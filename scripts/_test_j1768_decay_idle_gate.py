"""Regression for J-1768 / D-0340 (2026-10-04, Travis-ruled option 2; evidence F-2334): the weekly decay
throttle in nodes/subconscious_node.py -- _apply_decay (tensions, D-0266/J-1283) and
_apply_pattern_decay (integration_patterns, D-0270/J-1290) -- halves a row's count only when the row has
been idle for more than PATTERN_DECAY_DAYS (7 d, from last_ts) AND was last halved more than that long ago
(last_decay_ts). Idleness is measured from max(last_decay_ts, last_ts), so touching a row (which only moves
last_ts) moves its effective anchor and a touched row never decays.

Extends the F-1810 (tensions) / F-1829 (patterns) isolated assertions -- their script was a scratch file,
never committed -- with the case they lacked: a recently touched row with an OLD last_decay_ts anchor must
NOT halve. Every case runs for BOTH functions; the F-1810 throttle cases (no collapse in minutes, once per
window, floor at 1, backfill from last_ts, missing last_ts) are kept and re-asserted under the new gate.

Hermetic: the node is built with SubconsciousNode.__new__ (no __init__, so no _STATE_FILE read or write)
around a synthetic in-memory state and nothing is persisted. Every row stays under the 30-day long-cold line
and is never resolved, so _apply_decay's demotion block (the only code in either function that writes to
disk, data/tensions_archive.jsonl) is never entered -- asserted in run(). core.memory.store.DB_PATH is
redirected into a temp dir before the node module is imported (never connected to).

    python scripts/_test_j1768_decay_idle_gate.py
    J1768_MODULE=<path to another subconscious_node.py> python scripts/_test_j1768_decay_idle_gate.py
        (same assertions against a different copy of the module -- e.g. HEAD's pre-J-1768 file -- to show
         the new-gate cases FAIL without the change)
"""
from __future__ import annotations
import importlib.util, logging, os, sys, tempfile, time
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FAILS = 0
def check(name, cond, detail=""):
    global FAILS
    FAILS += (not cond)
    print(f"  [{'ok ' if cond else 'FAIL'}] {name}" + (f"   ({detail})" if detail and not cond else ""))

TMP = Path(tempfile.mkdtemp(prefix="j1768_decay_gate_"))
_LIVE = [ROOT / "data" / "tensions_archive.jsonl"]
def _stat(f): return (f.stat().st_mtime_ns, f.stat().st_size) if f.exists() else None
_LIVE_BEFORE = [_stat(f) for f in _LIVE]

from core.memory import store as _store
_store.DB_PATH = TMP / "nascence.db"          # never connected to by this test; belt and braces

_alt = os.environ.get("J1768_MODULE")
if _alt:
    _spec = importlib.util.spec_from_file_location("nodes.subconscious_node", _alt)
    scn = importlib.util.module_from_spec(_spec)
    sys.modules["nodes.subconscious_node"] = scn
    _spec.loader.exec_module(scn)
else:
    from nodes import subconscious_node as scn
print("module under test:", scn.__file__)

DAY = 86400.0
NOW = time.time()           # the pass takes milliseconds, every margin below is hours-to-days
KINDS = {"tension": ("tensions", "_apply_decay"),
         "pattern": ("integration_patterns", "_apply_pattern_decay")}
assert scn.PATTERN_DECAY_DAYS == 7, "the cases below are written for a 7-day window"


def R(count, last_ts_ago_d, anchor_ago_d=None, rid="r"):
    """A row `last_ts_ago_d` days idle whose last halving was `anchor_ago_d` days ago (None = the
    field is absent, i.e. pre-J-1283 state, so the first pass backfills it from last_ts)."""
    r = {"id": rid, "count": count, "last_ts": NOW - last_ts_ago_d * DAY}
    if anchor_ago_d is not None:
        r["last_decay_ts"] = NOW - anchor_ago_d * DAY
    return r


def run(kind, rows, passes=1):
    key, fn = KINDS[kind]
    node = scn.SubconsciousNode.__new__(scn.SubconsciousNode)
    node._state = {"tensions": [], "integration_patterns": []}
    node._state[key] = [dict(r) for r in rows]
    for _ in range(passes):
        getattr(node, fn)()
    out = node._state[key]
    assert len(out) == len(rows), "demotion block entered -- test rows must stay under the 30-day line"
    return out


for kind in KINDS:
    print(f"-- {kind}: {KINDS[kind][1]}")

    # ---- D-0340: the case F-1810 / F-1829 never had ------------------------------------------------
    r = run(kind, [R(5, 2, 9)], passes=3)[0]
    check(f"{kind}: touched 2d ago with an OLD anchor (9d) does NOT halve (5 stays 5)", r["count"] == 5,
          f"count={r['count']}")
    check(f"{kind}: ...and its anchor is left alone (not re-stamped)",
          abs(r["last_decay_ts"] - (NOW - 9 * DAY)) < 1e-6)
    r = run(kind, [R(8, 1, 30)], passes=3)[0]
    check(f"{kind}: touched 1d ago with a 30d-old anchor does NOT halve", r["count"] == 8, f"count={r['count']}")
    r = run(kind, [R(8, 6.5, 20)], passes=2)[0]
    check(f"{kind}: idle 6.5d (under the 7d line) with a 20d anchor does NOT halve", r["count"] == 8,
          f"count={r['count']}")
    r = run(kind, [R(8, 7.5, 20)])[0]
    check(f"{kind}: idle 7.5d (over the line) with a 20d anchor halves once (8 -> 4) and is re-stamped to now",
          r["count"] == 4 and abs(r["last_decay_ts"] - NOW) < 60, f"count={r['count']}")
    r = run(kind, [R(8, 8, 9)])[0]
    check(f"{kind}: halved 9d ago, touched 8d ago, idle since: a touch only moves the clock, it halves again (8 -> 4)",
          r["count"] == 4, f"count={r['count']}")

    # ---- cold rows still decay once a week (the cliff fix's benefit is kept) -------------------------
    row = R(8, 10, 12)
    out = run(kind, [row])
    check(f"{kind}: idle 10d + 12d anchor halves once (8 -> 4) and is re-stamped to now",
          out[0]["count"] == 4 and abs(out[0]["last_decay_ts"] - NOW) < 60, f"count={out[0]['count']}")
    out6 = run(kind, [row], passes=6)
    check(f"{kind}: six immediate passes (the ~36 s scan cadence) still halve exactly once (4, not 1)",
          out6[0]["count"] == 4, f"count={out6[0]['count']}")
    rolled = dict(out6[0]); rolled["last_decay_ts"] -= 8 * DAY      # a real week later, still idle
    out2 = run(kind, [rolled])
    check(f"{kind}: a week later, still idle, it halves again (4 -> 2): a recurring gate, not a one-shot latch",
          out2[0]["count"] == 2, f"count={out2[0]['count']}")

    # ---- a freshly backfilled row does not collapse in minutes ---------------------------------------
    nb = R(200, 10)                                                   # pre-J-1283 row: no last_decay_ts
    out = run(kind, [nb])
    check(f"{kind}: no anchor, idle 10d: backfilled from last_ts then halves once (200 -> 100)",
          out[0]["count"] == 100 and abs(out[0]["last_decay_ts"] - NOW) < 60, f"count={out[0]['count']}")
    out = run(kind, [nb], passes=40)
    check(f"{kind}: 40 immediate scans on that backfilled cold row: still 100 (no collapse in minutes)",
          out[0]["count"] == 100, f"count={out[0]['count']}")
    out = run(kind, [R(7, 2)], passes=3)
    check(f"{kind}: no anchor, touched 2d ago: anchor backfilled from last_ts (not now), count untouched",
          out[0]["count"] == 7 and abs(out[0]["last_decay_ts"] - (NOW - 2 * DAY)) < 1e-6,
          f"count={out[0]['count']}")

    # ---- F-1810 / F-1829 assertions that must stay green ---------------------------------------------
    out = run(kind, [R(9, 20, 1)], passes=3)
    check(f"{kind}: 20d idle but halved 1d ago: throttled, no re-fire (the anchor still gates)",
          out[0]["count"] == 9, f"count={out[0]['count']}")
    out = run(kind, [R(1, 15, 15)], passes=2)
    check(f"{kind}: count 1 floor takes the fire branch without going below 1", out[0]["count"] == 1,
          f"count={out[0]['count']}")
    r0 = R(6, 0); del r0["last_ts"]
    out = run(kind, [r0], passes=2)
    check(f"{kind}: no last_ts and no anchor: anchor backfilled to ~now, no raise, no halve",
          out[0]["count"] == 6 and abs(out[0]["last_decay_ts"] - NOW) < 60)
    r1 = R(6, 0, 12); del r1["last_ts"]
    out = run(kind, [r1])
    check(f"{kind}: no last_ts but a 12d anchor: falls back to the anchor alone and halves (6 -> 3), no TypeError",
          out[0]["count"] == 3, f"count={out[0]['count']}")
    r2 = R(6, 0, 12); r2["last_ts"] = None
    # _apply_decay's separate, older demotion block (not touched by J-1768) already raises a caught,
    # logged-once TypeError for a present-but-None last_ts; keep that known warning out of this output.
    _lg = logging.getLogger("nascence.subconscious"); _lvl = _lg.level; _lg.setLevel(logging.CRITICAL)
    try: out = run(kind, [r2])
    finally: _lg.setLevel(_lvl)
    check(f"{kind}: last_ts None with a 12d anchor: same fallback, the decay loop does not raise",
          out[0]["count"] == 3, f"count={out[0]['count']}")

    # ---- production-shaped pool (F-1631 / F-2334): cold floor-1 rows + touched rows with old anchors --
    pool = [R(1, 8 + (i % 17), 8 + (i % 17) + (i % 5), rid=f"cold{i}") for i in range(300)]
    pool += [R(2 + (i % 19), (i % 6) + 0.2, 8 + (i % 13), rid=f"touched{i}") for i in range(130)]
    anchors0 = {p["id"]: p["last_decay_ts"] for p in pool}
    counts0 = {p["id"]: p["count"] for p in pool}
    out = run(kind, pool, passes=3)
    cold = [p for p in out if p["id"].startswith("cold")]
    touched = [p for p in out if p["id"].startswith("touched")]
    check(f"{kind}: pool: all 300 cold floor-1 rows stay at exactly 1", all(p["count"] == 1 for p in cold))
    check(f"{kind}: pool: all 130 touched-within-7d rows keep their count (0 halved) and their old anchor",
          all(p["count"] == counts0[p["id"]] and p["last_decay_ts"] == anchors0[p["id"]] for p in touched),
          f"halved={sum(p['count'] != counts0[p['id']] for p in touched)}")
    check(f"{kind}: pool: every cold row got re-stamped (fired once, throttled after)",
          all(abs(p["last_decay_ts"] - NOW) < 60 for p in cold))

_LIVE_AFTER = [_stat(f) for f in _LIVE]
check("no live store was written by this test (tensions_archive.jsonl mtime/size unchanged)",
      _LIVE_BEFORE == _LIVE_AFTER, "Du is live and may itself write this; rerun if it flaps")
print("temp dir:", TMP)
print("FAILS =", FAILS)
sys.exit(1 if FAILS else 0)
