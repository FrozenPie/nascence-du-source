"""J-2590 / F-3316 regression: memory_service.ask()'s ride rows carry `cue_hash` (ghost_hash of the
slot's own value, never the text) and `slots_filled`, additively, on every line shape -- single-what,
multi-slot, where, and the recall_act stash path (slots_filled only). Isolated: shadow log redirected to
a temp dir, every slot engine stubbed; never touches live data/. Run: python scripts/test_ride_log_cue_hash.py
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import memory_service as ms  # noqa: E402  (import core BEFORE any lab_env)
from core.ghost_tuples import ghost_hash  # noqa: E402

assert str(Path(ms.__file__).resolve()).startswith(str(ROOT)), ms.__file__

tmp = Path(tempfile.mkdtemp(prefix="j2590_"))
ms._DATA = tmp
ms._SHADOW_LOG = tmp / "memory_service_shadow.jsonl"

# Stub every engine ask() fans out to, so no live store is read or written.
from core import associative_recall  # noqa: E402
associative_recall.recall = lambda *a, **k: []
ms._fanout_who = lambda *a, **k: []
ms._fanout_when = lambda *a, **k: []
ms._fanout_why = lambda *a, **k: []
ms._lookup_fragments = lambda ids: []
ms._fetch_context = lambda ids: {}
ms._descend_from = lambda *a, **k: []
import core.memory_edges as me  # noqa: E402
me.log_co_recall = lambda *a, **k: None


def rides():
    if not ms._SHADOW_LOG.exists():
        return []
    return [json.loads(l) for l in ms._SHADOW_LOG.read_text(encoding="utf-8").splitlines()
            if l.strip() and json.loads(l)["kind"] == "coupling_ride"]


# 1. single-what ask: one row, old keys intact, cue_hash = ghost_hash(cue), slots_filled == ["what"]
ms.ask("curiosity", "Thunder, again ", k=4)
r = rides()
assert len(r) == 1 and r[0]["line"] == "memory_ask:curiosity", r
v = r[0]["value"]
assert {"n_returned", "n_grounded", "n_descended"} <= set(v), v
assert v["cue_hash"] == ghost_hash("thunder, again") and len(v["cue_hash"]) == 16, v
assert v["slots_filled"] == ["what"], v
assert "Thunder" not in json.dumps(r[0]), "cue text leaked into the ride log"

# 2. multi-slot ask with where: one row per filled slot + where, each with its own value's hash
ms.ask("dream", what="the garden gate", who="travis", when={"epoch": "autumn"}, where="garden", k_per_slot=2)
r = rides()[1:]
lines = sorted(x["line"] for x in r)
assert lines == sorted(["memory_ask:dream:who", "memory_ask:dream:what", "memory_ask:dream:when",
                        "memory_ask:dream:where"]), lines
by = {x["line"].rsplit(":", 1)[1]: x["value"] for x in r}
assert by["what"]["cue_hash"] == ghost_hash("the garden gate")
assert by["who"]["cue_hash"] == ghost_hash("travis")
assert by["when"]["cue_hash"] == ghost_hash(json.dumps({"epoch": "autumn"}, sort_keys=True))
assert by["where"]["cue_hash"] == ghost_hash("garden")
for s, val in by.items():
    assert val["slots_filled"] == ["who", "what", "when", "where"], (s, val)
assert "n_grounded" in by["what"] and "n_grounded" not in by["who"]

# 3. recall_act stash path: slots_filled only, no cue_hash (no cue reaches it)
ms.stash_usage("recall_act", ["f1"])
v = rides()[-1]["value"]
assert v["slots_filled"] == ["what"] and "cue_hash" not in v, v

# 4. the helper itself
assert ms._cue_hash(None) is None
assert ms._cue_hash("  Thunder ") == ghost_hash("thunder")
assert ms._cue_hash(object()) is not None   # default=str rendering, never raises

print("test_ride_log_cue_hash: OK", tmp)
