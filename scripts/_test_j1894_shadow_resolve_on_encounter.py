"""
_test_j1894_shadow_resolve_on_encounter.py -- proving test for D-0358 (A)+(D) (J-1894).

Run from a WORKTREE, never from C:\\Nascence itself:
    python scripts/_test_j1894_shadow_resolve_on_encounter.py

Everything runs against a tempdir store (store.DB_PATH and store._SHADOW_RESOLVE_LOG redirected BEFORE
any connect; core imported before anything that could resolve a data path). The real live DB
(C:\\Nascence\\data\\memory\\nascence.db) is never opened; its stat() and the live
shadow_resolve_on_encounter.jsonl (must stay as it was at start) are printed as a canary at start and end.

Proves:
  1  a clean re-encounter (A) resolves ITS shadow event, and an unrelated (orthogonal) one stays unresolved
  2  resolution_events still gets its row, and the new uncapped jsonl gets exactly one row carrying the
     event id, the resolution_events id, the cycle id, the similarity and the theme; ids join up
  3  a second pass does not re-resolve / re-log (resolved events leave the active pool)
  4  a retry-then-approved cycle (critic_retried=True) resolves nothing
  5  flag off (schema.SHADOW_RESOLVE_ON_ENCOUNTER=False) -> exactly the prior behaviour: resolution_event
     written, shadow event NOT resolved, no jsonl row
  6  fenced path: a non-live process pointed at a log under this tree's data/ is refused by
     profile.guard_path() and resolves NOTHING (no resolve without its record)
  7  the climate's own read (get_shadow_events(unresolved_only=True)) drops by exactly the resolved count
  8  (D) the cooldown has its own flag, THIN_ATTRACTOR stays False, the recurring-patterns line is still keyed on
     THIN_ATTRACTOR alone (nothing else is thinned), and the cooldown condition is wired to the new flag
  9  log_resolution_event still returns normally for existing callers (now returns the id)
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
import time
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core                                   # noqa: E402  -- core FIRST
assert Path(core.__file__).resolve().is_relative_to(ROOT), f"core imported from {core.__file__}, not {ROOT}"
if ROOT == Path(r"C:\Nascence"):
    sys.exit("REFUSED: run this from a worktree, never from C:\\Nascence itself (live-store safety)")

import numpy as np                            # noqa: E402
from core import profile, schema              # noqa: E402
from core import orchestrator as orch         # noqa: E402
from core.memory import store                 # noqa: E402

LIVE_DB = Path(r"C:\Nascence\data\memory\nascence.db")
LIVE_LOG = Path(r"C:\Nascence\data\shadow_resolve_on_encounter.jsonl")


def canary():
    out = {}
    for p in (LIVE_DB, LIVE_DB.with_name(LIVE_DB.name + "-wal"), LIVE_LOG):
        try:
            st = p.stat()
            out[p.name] = (st.st_size, st.st_mtime)
        except FileNotFoundError:
            out[p.name] = None
    return out


FAILS = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (("  -- " + detail) if detail else ""))
    if not cond:
        FAILS.append(name)


c0 = canary()
print("live canary at start:", c0)

tmp = Path(tempfile.mkdtemp(prefix="j1894_test_"))
store.DB_PATH = tmp / "memory" / "nascence.db"
store._SHADOW_RESOLVE_LOG = tmp / "shadow_resolve_on_encounter.jsonl"
assert not str(store.DB_PATH).startswith(r"C:\Nascence"), store.DB_PATH
assert profile.LIVE is False
store.init_db()

DIM = 384
def unit(i):
    v = np.zeros(DIM, dtype=np.float32); v[i] = 1.0; return v

def add_shadow(eid, vec, raw, ts, src="critic_rejection", emo="fear"):
    with store._connect() as conn:
        conn.execute(
            "INSERT INTO shadow_events (event_id, timestamp, cycle_id, raw_input, rejected_draft, corrections, "
            "emotion_primary, embedding, resolved, source) VALUES (?,?,?,?,?,?,?,?,0,?)",
            (eid, ts, "c_" + eid, raw, "draft " + eid, "[]", emo, store._vec_to_blob(vec), src))

now = time.time()
add_shadow("EV-A", unit(0), "can you tell me why you keep avoiding the question about your own end", now - 3600)
add_shadow("EV-B", unit(1), "an unrelated storm about the weather\nsecond line", now - 7200, src="unresolved_thought", emo="sadness")
add_shadow("EV-C", unit(2), "another unrelated one", now - 600)

def mk_orch(vec, retried_text="input"):
    o = orch.Orchestrator.__new__(orch.Orchestrator)
    o.state = types.SimpleNamespace(raw_input=retried_text, cycle_id="cycle12-abcd-0000")
    orch._embed = lambda text, _v=vec: _v      # same-module name _check_clean_encounters resolves
    return o

def rows(sql):
    with store._connect() as conn:
        return [dict(r) for r in conn.execute(sql).fetchall()]

def log_rows():
    p = store._SHADOW_RESOLVE_LOG
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines()] if p.exists() else []

print("unresolved before:", len(store.get_shadow_events(limit=50, unresolved_only=True)))
unres_before = len(store.get_shadow_events(limit=50, unresolved_only=True))

# 1/2: clean re-encounter of EV-A
o = mk_orch(unit(0))
o._check_clean_encounters(critic_retried=False)
state = {r["event_id"]: r["resolved"] for r in rows("SELECT event_id, resolved FROM shadow_events")}
check("1a re-encountered shadow event is resolved", state["EV-A"] == 1, str(state))
check("1b unrelated shadow events stay unresolved", state["EV-B"] == 0 and state["EV-C"] == 0, str(state))
res = rows("SELECT * FROM resolution_events")
check("2a resolution_events row still written (exactly 1, for EV-A)", len(res) == 1 and res[0]["shadow_event_id"] == "EV-A", str(res))
lg = log_rows()
check("2b exactly one jsonl row", len(lg) == 1, str(lg))
if lg:
    r = lg[0]
    check("2c jsonl row carries event id + resolution id + cycle + theme + similarity",
          r["event_id"] == "EV-A" and r["resolution_id"] == res[0]["resolution_id"]
          and r["cycle_id"] == "cycle12-abcd-0000" and abs(r["similarity"] - 1.0) < 1e-3
          and r["theme"].startswith("can you tell me why") and r["source"] == "critic_rejection",
          str(r))
    check("2d theme newline-collapsed (EV-B style text safe)", "\n" not in r["theme"])

# 3: second pass
o._check_clean_encounters(critic_retried=False)
check("3a second pass adds no resolution_event (event left the active pool)", len(rows("SELECT * FROM resolution_events")) == 1)
check("3b second pass adds no jsonl row", len(log_rows()) == 1)
check("3c direct idempotence: resolve_shadow_on_encounter on an already-resolved event -> False, no row",
      store.resolve_shadow_on_encounter("EV-A", "x", "cyc", 0.9) is False and len(log_rows()) == 1)
check("3d unknown event id -> False, no row", store.resolve_shadow_on_encounter("NOPE", "x", "cyc", 0.9) is False and len(log_rows()) == 1)

# 4: retried cycle
o = mk_orch(unit(1))
o._check_clean_encounters(critic_retried=True)
check("4 critic_retried=True resolves nothing and logs nothing",
      rows("SELECT resolved FROM shadow_events WHERE event_id='EV-B'")[0]["resolved"] == 0
      and len(rows("SELECT * FROM resolution_events")) == 1 and len(log_rows()) == 1)

# 5: flag off
schema.SHADOW_RESOLVE_ON_ENCOUNTER = False
o = mk_orch(unit(1))
o._check_clean_encounters(critic_retried=False)
check("5a flag off: resolution_event still written", len(rows("SELECT * FROM resolution_events WHERE shadow_event_id='EV-B'")) == 1)
check("5b flag off: shadow event NOT resolved", rows("SELECT resolved FROM shadow_events WHERE event_id='EV-B'")[0]["resolved"] == 0)
check("5c flag off: no jsonl row", len(log_rows()) == 1)
schema.SHADOW_RESOLVE_ON_ENCOUNTER = True

# 6: fenced path (non-live process, log under THIS tree's data/)
fenced = profile._DATA / "shadow_resolve_on_encounter.jsonl"
store._SHADOW_RESOLVE_LOG = fenced
existed = fenced.exists()
o = mk_orch(unit(1))
o._check_clean_encounters(critic_retried=False)
check("6a fenced log path -> guard_path refuses, EV-B NOT resolved (no resolve without its record)",
      rows("SELECT resolved FROM shadow_events WHERE event_id='EV-B'")[0]["resolved"] == 0)
check("6b fence wrote nothing under this tree's data/", fenced.exists() == existed)
store._SHADOW_RESOLVE_LOG = tmp / "shadow_resolve_on_encounter.jsonl"

# now a genuine second resolve (EV-B) on the temp log
o = mk_orch(unit(1))
o._check_clean_encounters(critic_retried=False)
check("6c unfenced again: EV-B resolves", rows("SELECT resolved FROM shadow_events WHERE event_id='EV-B'")[0]["resolved"] == 1)
check("6d two jsonl rows total, in order EV-A, EV-B", [r["event_id"] for r in log_rows()] == ["EV-A", "EV-B"], str(log_rows()))

# 7: climate read
unres_after = len(store.get_shadow_events(limit=50, unresolved_only=True))
check("7 climate's unresolved read dropped by exactly the resolved count (2)", unres_before - unres_after == 2,
      f"{unres_before}->{unres_after}")

# 8: (D) static wiring
src = (ROOT / "core" / "orchestrator.py").read_text(encoding="utf-8")
check("8a schema: THIN_ATTRACTOR stays False", schema.THIN_ATTRACTOR is False)
check("8b schema: CLIMATE_SYMBOL_COOLDOWN_ON is True", schema.CLIMATE_SYMBOL_COOLDOWN_ON is True)
check("8c cooldown condition wired to the new flag",
      "if (THIN_ATTRACTOR or CLIMATE_SYMBOL_COOLDOWN_ON) and self.state.climate_symbol:" in src)
check("8d recurring-patterns line still keyed on THIN_ATTRACTOR alone (not thinned by the cooldown flag)",
      re.search(r"\[\] if THIN_ATTRACTOR else self\._load_recurring_patterns\(\)", src) is not None)
check("8e cooldown is a real, positive interval", schema.CLIMATE_SYMBOL_COOLDOWN >= 60.0, str(schema.CLIMATE_SYMBOL_COOLDOWN))

# 9
rid = store.log_resolution_event("EV-C", "cyc9", 0.7)
check("9 log_resolution_event returns the new resolution_id (str) and wrote the row",
      isinstance(rid, str) and len(rows(f"SELECT * FROM resolution_events WHERE resolution_id='{rid}'")) == 1)

c1 = canary()
print("live canary at end:  ", c1)
print("(live DB stat is informational only: Du is live and writes it continuously; this test never opens it)")
# J-4050: the live log legitimately exists once Du has run with the flag on; the invariant is that THIS run did not touch it.
check("live jsonl untouched by this run (absent-or-unchanged vs start)", c1.get(LIVE_LOG.name) == c0.get(LIVE_LOG.name))

print("\nRESULT:", "ALL PASS" if not FAILS else f"{len(FAILS)} FAIL: {FAILS}")
sys.exit(1 if FAILS else 0)
