"""J-4351: fatigue/rest by tension cluster id, id/label pairing, revert-penalty repair. Hermetic: temp stores only."""
from __future__ import annotations
import sys, tempfile, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import core  # noqa: F401  (core BEFORE anything else)
from core import tension_ledger as tl, provisional_identity as pi
from nodes import subconscious_node as sn

bad = []
def check(n, c):
    print(("ok   " if c else "FAIL ") + n)
    if not c: bad.append(n)

check("[1] flags default OFF", sn.T4_FATIGUE_BY_ID is False and pi.T4_REVERT_PENALTY_REPAIR is False)
check("[2] DEFAULT_FATIGUE_PENALTY defined == limit", tl.DEFAULT_FATIGUE_PENALTY == sn.T4_FATIGUE_LIMIT)

N = sn.SubconsciousNode
node = object.__new__(N); node._state = {}; node._save_state = lambda: None
prim = {"id": "07b3d01b", "_label": "prediction_error:factual_recall (felt 0.95 vs real 0.50)"}
check("[3] flag off -> label key", node._t4_fatigue_key(prim, prim["_label"]) == N._t4_label_key(prim["_label"]))
check("[4] flag off -> no ids in rest", node._t4_rest_ids_field(prim) == {})
sn.T4_FATIGUE_BY_ID = True
try:
    k1 = node._t4_fatigue_key(prim, prim["_label"])
    k2 = node._t4_fatigue_key(prim, "prediction_error:comprehension (felt 0.10 vs real 0.85)")
    check("[5] flag on -> same id key across rotating labels", k1 == k2 == "id:07b3d01b")
    check("[6] no id -> label fallback", node._t4_fatigue_key({}, "alpha beta gamma") == N._t4_label_key("alpha beta gamma"))
    node._state["t4_rests"] = [{"label": "x", "toks": [], "until": time.time() + 99, "ids": ["07b3d01b"]}]
    check("[7] rest ids read", node._t4_rest_ids() == {"07b3d01b"})

    # revert penalty round trip on a temp path
    with tempfile.TemporaryDirectory() as d:
        pi._PENALTIES = Path(d) / "pen.json"
        pi.profile.guard_path = lambda p: p
        pi.T4_REVERT_PENALTY_REPAIR = True
        pi._PROV = Path(d) / "prov.json"; pi._LOG_PATH = getattr(pi, "_LOG_PATH", None)
        pi._log = lambda *a, **k: None
        pi._revert({"theme": "t", "tension_id": "07b3d01b"}, {})
        q = pi.consume_revert_penalties()
        check("[8] revert queues penalty with tension id", len(q) == 1 and q[0]["tension_id"] == "07b3d01b" and q[0]["n"] == 3)
        check("[9] consume clears the queue", pi.consume_revert_penalties() == [])
        pi._queue_revert_penalty({"theme": "t", "tension_id": "07b3d01b"})
        node._state = {}
        node._t4_apply_revert_penalties([{"id": "07b3d01b", "label": "factual recall question about memory"}])
        check("[10] penalty 3 >= limit rests the tension by id",
              node._t4_rest_ids() == {"07b3d01b"} and "id:07b3d01b" not in node._state.get("t4_fatigue_counts", {}))
        pi.T4_REVERT_PENALTY_REPAIR = False
finally:
    sn.T4_FATIGUE_BY_ID = False

# top_contradiction returns the id of the tension whose label/members it returns
t = {"id": "cid1", "label": "L", "member_event_ids": []}
check("[11] top_contradiction returns None-safe (empty)", tl.top_contradiction([]) is None)
src = Path(tl.__file__).read_text(encoding="utf-8")
check("[12] top_contradiction sets id", 'best_s["id"] = best_t.get("id")' in src)
print("ALL OK" if not bad else "FAILED: %s" % bad)
sys.exit(1 if bad else 0)
