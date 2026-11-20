"""J-2079 / F-2698 regression: evidence_recall's recall act stashes its returned fragment ids so
memory_service.note_usage("recall_act", vec) scores them. Isolated: shadow log redirected to a temp dir
and the embedding matrix stubbed; never touches live data/. Run: python scripts/test_recall_act_usage_stash.py
"""
import asyncio
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
from core import memory_service as ms  # noqa: E402  (import core BEFORE any lab_env)
from core import associative_recall  # noqa: E402

assert str(Path(ms.__file__).resolve()).startswith(str(ROOT)), ms.__file__

tmp = Path(tempfile.mkdtemp(prefix="j2079_"))
ms._DATA = tmp
ms._SHADOW_LOG = tmp / "memory_service_shadow.jsonl"
M = np.eye(3, dtype=np.float32)
associative_recall._matrix = lambda: {"M": M, "ids": ["f1", "f2", "f3"]}


def rows():
    if not ms._SHADOW_LOG.exists():
        return []
    return [json.loads(l) for l in ms._SHADOW_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]


# 1. stash then note_usage -> one service_usage row, source recall_act
ms.stash_usage("recall_act", ["f1", "f2", None, "f1"])
p = ms._pending_usage["recall_act"]
assert set(p) == {"ts", "n_slots_filled", "fragments"} and p["n_slots_filled"] == 1, p
assert [f["fragment_id"] for f in p["fragments"]] == ["f1", "f2"], p
ms.note_usage("recall_act", [1.0, 0.0, 0.0])
su = [r for r in rows() if r["kind"] == "service_usage"]
assert len(su) == 1 and su[0]["source"] == "recall_act", su
assert su[0]["usage"][0]["fragment_id"] == "f1" and su[0]["usage"][0]["cos_sim"] == 1.0
ride = [r for r in rows() if r["kind"] == "coupling_ride"]
assert len(ride) == 1 and ride[0]["line"] == "memory_ask:recall_act", ride

# 2. zero-fragment stash -> zero-fragment entry (ask()'s convention)
ms.stash_usage("recall_act", [])
assert ms._pending_usage["recall_act"]["fragments"] == []
ms.note_usage("recall_act", [1.0, 0.0, 0.0])
assert [r for r in rows() if r["kind"] == "service_usage"][-1]["usage"] == []

# 3. a stash failure never changes gather()'s return
from core import evidence_recall as er  # noqa: E402


def boom(*a, **k):
    raise RuntimeError("stash boom")


from core import judge_panel  # noqa: E402

er._LOG = tmp / "evidence_log.jsonl"
er._candidates = lambda q: [{"fragment_id": "f1", "origin": "x", "sim": 0.9, "timestamp": 0,
                             "content": "c"}]


async def _rd(*a, **k):
    return {"verdict": True, "v1": True, "v2": True, "how": "agreed"}


judge_panel.rule_detail = _rd


def run():
    return asyncio.run(er.gather("test question j2079"))


baseline = run()
assert [e["fragment_id"] for e in baseline["episodes"]] == ["f1"], baseline
assert [f["fragment_id"] for f in ms._pending_usage["recall_act"]["fragments"]] == ["f1"]
orig = ms.stash_usage
ms.stash_usage = boom
try:
    out = run()
finally:
    ms.stash_usage = orig
assert out == baseline, (out, baseline)
print("OK: recall_act stash/usage tests passed")
