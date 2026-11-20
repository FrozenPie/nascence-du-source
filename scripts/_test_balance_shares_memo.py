#!/usr/bin/env python
"""In-vitro test for the balance.shares() short-TTL memo (J-1908, F-2540). Offline: a TEMP sqlite DB with the three
tables balance.py reads, a fake clock, no network, no LLM, no data/ file touched (balance.py is imported and its _DB
is pointed at the temp DB before any call). The OLD code is the verbatim pre-change core/balance.py from git
(default rev 4ed340f; override --baseline-rev / --baseline-file) loaded as a separate module object, so every check
is a real old-vs-new comparison on the SAME DB.

What it proves
  0  the SQL rewrite (`+origin IN (...)`) range-scans idx_timestamp where the old text walks idx_origin
  1  STATIC DB, 120 calls over a fake clock that crosses the TTL repeatedly: old and new return IDENTICAL
     shares(), needs_reality(), needs_light(), in_remediation() and status() on every call
  2  forced hysteresis flips (EXIT_AT / REENTER_AT monkeypatched between phases on BOTH modules): identical latch
     sequences and >=4 real flips in each of _reading and _sprinting
  3  one idle tick's six shares() calls cost ONE real read in the new code (six in the old)
  4  LIVE-DRIFT DB (rows inserted between calls): inside the TTL the new code serves exactly the value read at the
     last refresh and a refresh equals the fresh old value; the new latches equal the OLD latch logic fed with that
     as-of-last-refresh value at every step (so the only difference from old is the bounded staleness, nothing
     else), and the staleness never reaches the TTL
  5  failure path: a DB with no tables -> zeros, NOT memoised (fresh again once the tables appear)
  6  returned dicts are independent copies (mutating one, or status(), never leaks into the memo)
  7  the memo is keyed on db path / WINDOW_DAYS (a change is a miss); SHARES_TTL_S=0 == old behaviour
  8  scripts/balance_test.py (monkeypatches balance.shares) still passes unchanged

Run (from the tree under test):  python scripts/_test_balance_shares_memo.py [--baseline-rev REV | --baseline-file SRC]
"""
from __future__ import annotations

import argparse
import importlib.util
import random
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  (import core BEFORE anything else; assert it is THIS tree)
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
from core import balance as NEW  # noqa: E402
assert Path(NEW.__file__).resolve().is_relative_to(ROOT), NEW.__file__

ap = argparse.ArgumentParser()
ap.add_argument("--baseline-rev", default="4ed340f")
ap.add_argument("--baseline-file", default=None)
ap.add_argument("--real-db", default=None, help="a COPY of the real nascence.db: adds check 9 (old==new on real rows, timings)")
args = ap.parse_args()

ok_all = True


def check(name, cond, extra=""):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  {'PASS' if cond else 'FAIL'} {name}{(' -- ' + extra) if extra else ''}")


# ---- the OLD module, verbatim from git (or a file), as independent module objects ----
if args.baseline_file:
    old_src = Path(args.baseline_file).read_text(encoding="utf-8")
else:
    old_src = subprocess.run(["git", "-C", str(ROOT), "show", f"{args.baseline_rev}:core/balance.py"],
                             capture_output=True, text=True, encoding="utf-8", check=True).stdout
assert "_shares_uncached" not in old_src, "baseline already has the memo -- pick an older rev"
tmp_dir = Path(tempfile.mkdtemp(prefix="balance_old_J1908_"))


def load_old(name):
    p = tmp_dir / f"{name}.py"
    p.write_text(old_src, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    # J-4052: J-3807 added "unresolved_dream_rest" to the SHADOW origin set AFTER this baseline rev. That is a deliberate
    # semantic change, not what this test is about (memo + range-scan equivalence), so give the baseline today's sets
    # and keep the old/new comparison on the memo + SQL text only.
    import core.balance as _cur_balance
    for _k in ("_WORLD", "_SELF", "_LIGHT_VERDICT", "_SHADOW_VERDICT"):
        if hasattr(m, _k) and hasattr(_cur_balance, _k):
            setattr(m, _k, getattr(_cur_balance, _k))
    return m


OLD = load_old("balance_old_J1908")
REF = load_old("balance_ref_J1908")      # old latch logic, shares() replaced per step by the expected served value


class Clock:
    """Fake clock injected as the `time` global of the modules (time() and monotonic() advance together)."""
    def __init__(self, t0): self.t = t0
    def time(self): return self.t
    def monotonic(self): return self.t - 1_000_000.0


T0 = 1_790_000_000.0
clock = Clock(T0)
for _m in (OLD, NEW, REF):
    _m.time = clock

db_dir = Path(tempfile.mkdtemp(prefix="balance_db_J1908_"))
DB = db_dir / "nascence.db"
for _m in (OLD, NEW, REF):
    _m._DB = DB

rng = random.Random(1908)
WORLD, SELF = list(NEW._WORLD), list(NEW._SELF)
LV, SV = list(NEW._LIGHT_VERDICT), list(NEW._SHADOW_VERDICT)


def make_schema(path):
    c = sqlite3.connect(path)
    c.execute("CREATE TABLE memory_fragments (id INTEGER PRIMARY KEY, origin TEXT, timestamp REAL)")
    c.execute("CREATE INDEX idx_origin ON memory_fragments(origin)")
    c.execute("CREATE INDEX idx_timestamp ON memory_fragments(timestamp DESC)")   # as in the real DB (plan-relevant)
    c.execute("CREATE TABLE light_events (id INTEGER PRIMARY KEY, source TEXT, timestamp REAL)")
    c.execute("CREATE INDEX idx_light_ts ON light_events(timestamp DESC)")
    c.execute("CREATE TABLE shadow_events (id INTEGER PRIMARY KEY, source TEXT, timestamp REAL)")
    c.execute("CREATE INDEX idx_shadow_ts ON shadow_events(timestamp DESC)")
    c.commit(); c.close()


def add_rows(path, n_world, n_self, n_light, n_shadow, t_lo, t_hi, noise=True):
    c = sqlite3.connect(path)
    for _ in range(n_world): c.execute("INSERT INTO memory_fragments(origin,timestamp) VALUES (?,?)", (rng.choice(WORLD), rng.uniform(t_lo, t_hi)))
    for _ in range(n_self):  c.execute("INSERT INTO memory_fragments(origin,timestamp) VALUES (?,?)", (rng.choice(SELF), rng.uniform(t_lo, t_hi)))
    for _ in range(n_light): c.execute("INSERT INTO light_events(source,timestamp) VALUES (?,?)", (rng.choice(LV), rng.uniform(t_lo, t_hi)))
    for _ in range(n_shadow): c.execute("INSERT INTO shadow_events(source,timestamp) VALUES (?,?)", (rng.choice(SV), rng.uniform(t_lo, t_hi)))
    if noise:   # rows that must never be counted: other origin / out-of-window / non-verdict source
        for _ in range(40): c.execute("INSERT INTO memory_fragments(origin,timestamp) VALUES (?,?)", ("other_origin", rng.uniform(t_lo, t_hi)))
        for _ in range(40): c.execute("INSERT INTO memory_fragments(origin,timestamp) VALUES (?,?)", (rng.choice(WORLD + SELF), T0 - 30 * 86400))
        for _ in range(20): c.execute("INSERT INTO light_events(source,timestamp) VALUES (?,?)", ("play_point", rng.uniform(t_lo, t_hi)))
    c.commit(); c.close()


def reset_latches(*mods):
    for m in mods:
        m._sprinting = None; m._reading = None
    NEW.invalidate_shares_cache()


def snap(m):
    return (m.shares(), m.needs_reality(), m.needs_light(), m.in_remediation())


# counting wrapper around the new module's real read
real_reads = {"n": 0}
_orig_uncached = NEW._shares_uncached


def _counting():
    real_reads["n"] += 1
    return _orig_uncached()


NEW._shares_uncached = _counting

TTL0 = NEW.SHARES_TTL_S
print(f"\nbaseline: {args.baseline_file or args.baseline_rev}   TTL={NEW.SHARES_TTL_S}s   old has memo: {hasattr(OLD, '_shares_uncached')}")

# ======================= 0: the query plan ===========================================
print("\n[0] query plan of the memory_fragments counts (temp DB with the real index set)")
make_schema(DB)
_c = sqlite3.connect(DB)
_cut = T0 - 7 * 86400
_ph = ",".join("?" * len(NEW._WORLD))
plan_new = [r[3] for r in _c.execute(f"EXPLAIN QUERY PLAN SELECT COUNT(*) n FROM memory_fragments WHERE +origin IN ({_ph}) AND timestamp >= ?", NEW._WORLD + (_cut,))]
plan_old = [r[3] for r in _c.execute(f"EXPLAIN QUERY PLAN SELECT COUNT(*) n FROM memory_fragments WHERE origin IN ({_ph}) AND timestamp >= ?", NEW._WORLD + (_cut,))]
_c.close()
check("old query text walks idx_origin", any("idx_origin" in x for x in plan_old), "; ".join(plan_old))
check("new query text range-scans idx_timestamp", any("idx_timestamp" in x for x in plan_new), "; ".join(plan_new))
DB.unlink()

# ======================= 1 + 2: static DB, hysteresis flips ===========================
print("\n[1,2] static DB, 120 calls across TTL crossings + forced hysteresis flips")
make_schema(DB)
add_rows(DB, 460, 540, 300, 340, T0 - 6 * 86400, T0 - 3600)    # clock drifts <1 h here, never past a row
reset_latches(OLD, NEW)
b = OLD.shares()
check("fixture is sane (reality ~0.46, light ~0.47)", 0.40 < b["reality_share"] < 0.52 and 0.40 < b["light_share"] < 0.55,
      f"{b['reality_share']:.3f}/{b['light_share']:.3f}")
thr_phases = [(0.47, 0.42), (0.40, 0.30), (0.60, 0.50), (0.47, 0.42), (0.40, 0.30), (0.60, 0.50),
              (0.47, 0.42), (0.40, 0.30), (0.60, 0.50), (0.47, 0.42)]
mism = []; n_calls = 0; seq_old = []; seq_new = []; real_reads["n"] = 0; shares_calls = 0
for ph, (ex, re_) in enumerate(thr_phases):
    for m in (OLD, NEW):
        m.EXIT_AT = ex; m.REENTER_AT = re_
    for k in range(12):
        clock.t += rng.choice([0.3, 0.5, 1.2, 4.0, 9.0, 11.0, 31.0, 45.0])   # some steps expire the memo, most do not
        a = snap(OLD); bb = snap(NEW)
        n_calls += 1
        seq_old.append((OLD._reading, OLD._sprinting)); seq_new.append((NEW._reading, NEW._sprinting))
        if a != bb: mism.append((ph, k, a, bb))
        sa, sb = OLD.status(), NEW.status()
        if sa != sb: mism.append(("status", ph, k, sa, sb))
check(f"{n_calls} steps (each: shares + needs_reality + needs_light + in_remediation + status): all identical", not mism,
      f"{len(mism)} mismatches {mism[:1]}")
check("latch sequences (_reading, _sprinting) identical", seq_old == seq_new)


def flips(seq, i): return sum(1 for x, y in zip(seq, seq[1:]) if x[i] != y[i])


check("forced hysteresis: >=4 real flips in _reading and in _sprinting", flips(seq_old, 0) >= 4 and flips(seq_old, 1) >= 4,
      f"_reading flips={flips(seq_old, 0)} _sprinting flips={flips(seq_old, 1)}")
check("the memo was really exercised: some hits, some expiries (TTL=%.0fs)" % NEW.SHARES_TTL_S,
      1 < real_reads["n"] < n_calls * 9, f"{real_reads['n']} real reads over {n_calls} steps of ~9 shares() calls each")

# ======================= 3: one idle tick = one real read =============================
print("\n[3] one idle tick's six shares() calls")
for m in (OLD, NEW):
    m.EXIT_AT = 0.47; m.REENTER_AT = 0.42
reset_latches(OLD, NEW)
clock.t += 100.0
real_reads["n"] = 0
for _ in range(6): NEW.shares()
check("new: 6 calls -> 1 real read", real_reads["n"] == 1, f"{real_reads['n']}")
n_connect = {"c": 0}
_real_connect = sqlite3.connect


def _wrapped(*a, **k):
    n_connect["c"] += 1
    return _real_connect(*a, **k)


sqlite3.connect = _wrapped
try:
    for _ in range(6): OLD.shares()
finally:
    sqlite3.connect = _real_connect
check("old: 6 calls -> 6 real reads (reference)", n_connect["c"] == 6, f"{n_connect['c']}")

# ======================= 4: live-drift DB ===========================================
print("\n[4] live-drift DB: staleness bounded by the TTL; new latches == old latch logic on the as-of-refresh value")
DRIFT = db_dir / "drift.db"
make_schema(DRIFT)
for m in (OLD, NEW, REF):
    m._DB = DRIFT
    m.EXIT_AT = 0.47; m.REENTER_AT = 0.42
add_rows(DRIFT, 380, 620, 300, 340, clock.t - 6 * 86400, clock.t - 3600)
reset_latches(OLD, NEW, REF)
bad = []; last_refresh_t = None; served_snapshot = None
lat_new = []; lat_ref = []; lat_old = []; max_age = 0.0; n_refresh = 0
for i in range(200):
    clock.t += rng.choice([0.5, 2.0, 4.0, 7.0, 9.0, 13.0, 29.0, 40.0])
    add_rows(DRIFT, rng.choice([0, 1, 3, 6]), rng.choice([0, 1, 1, 2]), rng.choice([0, 1, 2]), rng.choice([0, 1, 1]),
             clock.t - 5, clock.t, noise=False)
    before = real_reads["n"]
    n_s = NEW.shares()
    refreshed = real_reads["n"] != before
    o_s = OLD.shares()                      # a fresh read at this instant
    if refreshed:
        served_snapshot = o_s; last_refresh_t = clock.t; n_refresh += 1
        if n_s != o_s: bad.append(("refresh != fresh old", i))
    else:
        if n_s != served_snapshot: bad.append(("served != last-refresh snapshot", i))
    age = clock.t - last_refresh_t
    max_age = max(max_age, age if not refreshed else 0.0)
    if (not refreshed) and age >= NEW.SHARES_TTL_S: bad.append(("served at/after TTL", i))
    REF.shares = (lambda v=dict(served_snapshot): dict(v))
    lat_new.append((NEW.needs_reality(), NEW.needs_light(), NEW.in_remediation(), NEW._reading, NEW._sprinting))
    lat_ref.append((REF.needs_reality(), REF.needs_light(), REF.in_remediation(), REF._reading, REF._sprinting))
    lat_old.append((OLD.needs_reality(), OLD.needs_light(), OLD.in_remediation(), OLD._reading, OLD._sprinting))
check("each call is a fresh read (== old) or the last-refresh snapshot, never older than the TTL", not bad, f"{bad[:3]}")
check("new latches == old latch logic fed the as-of-refresh value, all 200 steps", lat_new == lat_ref)
real_flips_old = flips(lat_old, 3); real_flips_new = flips(lat_new, 3)
check("memo stayed active during the drift (refreshes < steps)", 1 < n_refresh < 200, f"{n_refresh} refreshes / 200 steps; max served age {max_age:.1f}s")
print(f"       info: _reading flips old={real_flips_old} new={real_flips_new}; steps where new latch tuple != fresh-old: "
      f"{sum(1 for x, y in zip(lat_new, lat_old) if x != y)}")

# ======================= 5: failure path not memoised =================================
print("\n[5] failure path")
EMPTY = db_dir / "empty.db"
sqlite3.connect(EMPTY).close()
for m in (OLD, NEW, REF):
    m._DB = EMPTY
NEW.invalidate_shares_cache()
zero = {"reality_share": 0.0, "light_share": 0.0, "world": 0, "self": 0, "light": 0, "shadow": 0}
check("no tables -> zeros from both", OLD.shares() == zero and NEW.shares() == zero)
check("zeros are NOT memoised", NEW._shares_memo is None)
make_schema(EMPTY)
add_rows(EMPTY, 50, 50, 20, 20, clock.t - 3 * 86400, clock.t - 600)
check("tables appear -> the very next new call is fresh (== old)", NEW.shares() == OLD.shares() and NEW.shares()["world"] > 0)

# ======================= 6: dict independence ==========================================
print("\n[6] returned dicts are independent copies")
s1 = NEW.shares(); s1["world"] = -999; s1["junk"] = 1
s2 = NEW.shares()
check("mutating a returned dict does not leak into the memo", s2["world"] != -999 and "junk" not in s2)
st = NEW.status()
check("status() annotations do not leak into shares()", "remediating" in st and "remediating" not in NEW.shares())

# ======================= 7: key + ttl=0 =================================================
print("\n[7] memo key and TTL=0")
A = db_dir / "a.db"; B = db_dir / "b.db"
make_schema(A); make_schema(B)
add_rows(A, 10, 90, 10, 90, clock.t - 3 * 86400, clock.t - 600)
add_rows(B, 90, 10, 90, 10, clock.t - 3 * 86400, clock.t - 600)
NEW._DB = A; NEW.invalidate_shares_cache()
ra = NEW.shares(); NEW._DB = B; rb = NEW.shares()
check("changing _DB is a miss (no stale cross-db hit)", ra["reality_share"] < 0.2 and rb["reality_share"] > 0.8,
      f"{ra['reality_share']:.2f} vs {rb['reality_share']:.2f}")
NEW._DB = A; NEW.invalidate_shares_cache(); r1 = NEW.shares()
w0 = NEW.WINDOW_DAYS; NEW.WINDOW_DAYS = 0.0001; r2 = NEW.shares(); NEW.WINDOW_DAYS = w0
check("changing WINDOW_DAYS is a miss", r2["world"] == 0 and r1["world"] > 0, f"{r1['world']} -> {r2['world']}")
NEW.SHARES_TTL_S = 0; real_reads["n"] = 0
for _ in range(5): NEW.shares()
check("SHARES_TTL_S=0 -> every call is a real read (old behaviour)", real_reads["n"] == 5, f"{real_reads['n']}")
NEW.SHARES_TTL_S = TTL0

# ======================= 8: existing mock test ==========================================
print("\n[8] scripts/balance_test.py (monkeypatches shares()) still passes")
r = subprocess.run([sys.executable, str(ROOT / "scripts" / "balance_test.py")], capture_output=True, text=True, encoding="utf-8")
tail = [ln for ln in r.stdout.strip().splitlines() if ln.strip()]
check("balance_test.py exit 0", r.returncode == 0, tail[-2] if len(tail) >= 2 else r.stderr[-200:])

# ======================= 9: real rows (optional) =========================================
if args.real_db:
    import time as _rt
    print(f"\n[9] REAL DB COPY {args.real_db}: old == new on real rows, several windows, + timing")
    for m in (OLD, NEW):
        m.time = _rt; m._DB = Path(args.real_db)
    NEW.SHARES_TTL_S = 0                 # compare the SQL rewrite alone first (no memo in the way)
    for wd in (0.01, 0.5, 1.0, 3.0, 7.0, 14.0, 30.0, 90.0, 400.0):
        OLD.WINDOW_DAYS = NEW.WINDOW_DAYS = wd
        a, b2 = OLD.shares(), NEW.shares()
        check(f"window {wd:>6} d identical", a == b2, f"world={a['world']} self={a['self']} light={a['light']} shadow={a['shadow']}")
    OLD.WINDOW_DAYS = NEW.WINDOW_DAYS = 7.0

    def med(fn, n=7):
        ts = []
        for _ in range(n):
            t = _rt.perf_counter(); fn(); ts.append((_rt.perf_counter() - t) * 1000)
        ts.sort(); return ts[len(ts) // 2]
    mo, mn = med(OLD.shares), med(NEW.shares)
    check("one real shares(): new is much cheaper than old", mn < mo / 4, f"old median {mo:.0f} ms -> new median {mn:.0f} ms (memo off)")
    NEW.SHARES_TTL_S = TTL0

print(f"\n{'=' * 60}\n{'ALL PASS' if ok_all else 'FAILURES ABOVE'}\n{'=' * 60}")
sys.exit(0 if ok_all else 1)
