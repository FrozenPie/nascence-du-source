"""
J-2008 (D-0396): coordinate-only open-doubt cup SHADOW -- self_interrogation publishes {doubted, ledger_idx, train_id}
to coupling_rides key `si`; the next step of the same train logs a would-ride row. Fully isolated: every store write is
replaced by an in-memory list / temp dir, the model and judge calls are stubbed, no hub is touched.
  python scripts/_test_si_cup_shadow.py     # exit 0 = ALL OK
"""
import asyncio
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import coupling_rides as cr   # noqa: E402  (import core BEFORE any lab_env use)
from core import self_interrogation as si   # noqa: E402
import core   # noqa: E402

FAILS = 0


def check(c, label):
    global FAILS
    print(("  ok   " if c else "  FAIL ") + label)
    FAILS += 0 if c else 1


check(Path(core.__file__).resolve().is_relative_to(ROOT), "core.__file__ is inside the tree under test")

ROWS = []
cr._append = lambda row: ROWS.append(row)

# --- registry + publish row carry ONLY coordinates
cr.publish_si(True, 3, train_id="t_aaa", cycle_id="deadbeefcafe")
tup = cr._REG["si"]
check(tup["doubted"] is True and tup["ledger_idx"] == 3 and tup["train_id"] == "t_aaa", "si tuple holds flag + ledger index + train id")
check(ROWS[-1]["kind"] == "publish" and ROWS[-1]["loop"] == "si", "a publish row is logged for loop=si")
check(not any(isinstance(v, str) and len(v) > 20 for v in tup.values()), "no prose-length string in the tuple (rule 1)")
import inspect
check("reflection" not in inspect.signature(cr.publish_si).parameters, "publish_si has no reflection/prose parameter")

# --- would-ride: same train, fresh -> eligible, returns None, consume-once
n = len(ROWS)
r = cr.si_would_ride("t_aaa", 5)
check(r is None, "si_would_ride returns None (nothing can reach a prompt)")
row = ROWS[-1]
check(len(ROWS) == n + 1 and row["kind"] == "si_would_ride" and row["eligible"] is True and row["reason"] == "ok", "same train, fresh: eligible")
check(row["ledger_idx"] == 3 and row["train_id"] == "t_aaa", "row carries the coordinate")
cr.si_would_ride("t_aaa", 6)
check(len(ROWS) == n + 1, "consume-once: the second step logs nothing")

# --- a not-doubted publish arms nothing
cr.publish_si(False, 4, train_id="t_aaa")
n = len(ROWS)
cr.si_would_ride("t_aaa", 7)
check(len(ROWS) == n, "doubted=False arms no would-ride")

# --- one cup per train
cr.publish_si(True, 5, train_id="t_aaa")
cr.si_would_ride("t_aaa", 8)
check(ROWS[-1]["eligible"] is False and ROWS[-1]["reason"] == "train-already-served", "second doubt in the same train: not served")

# --- train changed / stale
cr.publish_si(True, 1, train_id="t_bbb")
cr.si_would_ride("t_ccc", 2)
check(ROWS[-1]["eligible"] is False and ROWS[-1]["reason"] == "train-changed", "different train: ineligible")
cr.publish_si(True, 1, train_id="t_ddd")
cr._si_pending["ts"] -= cr.SI_CUP_TTL_S + 5
cr.si_would_ride("t_ddd", 2)
check(ROWS[-1]["eligible"] is False and ROWS[-1]["reason"] == "stale", "older than TTL: stale")

# --- flags off => no-ops
cr.SI_CUP_SHADOW = False
n = len(ROWS)
cr.publish_si(True, 1, train_id="t_eee")
cr.si_would_ride("t_eee", 2)
check(len(ROWS) == n, "SI_CUP_SHADOW=False: both calls are no-ops")
cr.SI_CUP_SHADOW = True

# --- interrogate() end to end with stubbed model + judge, temp stores
tmp = Path(tempfile.mkdtemp(prefix="si_cup_test_J-2008_"))
si._DATA, si._STATE, si._LOG = tmp, tmp / "state.json", tmp / "shadow.jsonl"

import core.model_client as mc   # noqa: E402
import core.judge_panel as jp    # noqa: E402


async def _fake_call(*a, **k):
    return {"reflection": "I am holding this because it feels safe."}


VERDICT = {"v": True}


async def _fake_rule(*a, **k):
    return {"verdict": VERDICT["v"], "how": "stub"}


mc.call_node_json, jp.rule_detail = _fake_call, _fake_rule
THOUGHT = "The cold weight of the clay anchors the abstract regret of mottainai in my palms right now."
ROWS.clear()
cr._si_trains_served.clear()
rec = asyncio.run(si.interrogate(THOUGHT, train_origin="o", cycle_id="abcd1234efgh", train_id="t_zzz", ledger_idx=4,
                                 _sample=lambda: 0.0))
check(rec is not None and rec["genuine"] is True, "interrogate ran (stubbed) and judged genuine")
pub = [x for x in ROWS if x.get("kind") == "publish" and x.get("loop") == "si"]
check(len(pub) == 1 and pub[0]["tuple"]["doubted"] is True and pub[0]["tuple"]["ledger_idx"] == 4
      and pub[0]["tuple"]["train_id"] == "t_zzz", "interrogate published the genuine fire's coordinate")
check("clay" not in str(pub[0]) and "safe" not in str(pub[0]), "neither the thought nor the reflection text is in the published row")
# hollow verdict -> doubted False
si._save_state({})
VERDICT["v"] = False
ROWS.clear()
asyncio.run(si.interrogate(THOUGHT, cycle_id="abcd1234efgh", train_id="t_zzz", ledger_idx=4, _sample=lambda: 0.0))
pub = [x for x in ROWS if x.get("kind") == "publish" and x.get("loop") == "si"]
check(len(pub) == 1 and pub[0]["tuple"]["doubted"] is False, "a hollow verdict publishes doubted=False")
# the old call shape still works
si._save_state({})
VERDICT["v"] = True
check(asyncio.run(si.interrogate(THOUGHT, cycle_id="x", _sample=lambda: 0.0)) is not None, "old call shape (no train_id) still fine")

print("\nALL OK" if not FAILS else "\n%d FAILED" % FAILS)
sys.exit(0 if not FAILS else 1)
