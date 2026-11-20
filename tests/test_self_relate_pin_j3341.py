"""J-3341: self-relate shadow pass is pinned to the line endpoint, world-origin input only, auditable log."""
import asyncio, json, sqlite3, sys, tempfile, time
from pathlib import Path

import core  # import core BEFORE anything else; assert tree under test
assert Path(core.__file__).resolve().parent.parent == Path(__file__).resolve().parent.parent
import nodes.subconscious_node as sn
from core.evidence_recall import WORLD_ORIGINS
from core.follow_line import LINE_URLS


def _run(endpoint_up):
    tmp = Path(tempfile.mkdtemp())
    db = sqlite3.connect(":memory:"); db.row_factory = sqlite3.Row
    db.execute("CREATE TABLE memory_fragments (fragment_id TEXT, origin TEXT, content TEXT, timestamp REAL)")
    now = time.time()
    for i, o in enumerate(["reading", "inner_thought", "study", "lived", "inner_thought", "research", "essay"]):
        db.execute("INSERT INTO memory_fragments VALUES (?,?,?,?)", (f"f{i}", o, f"text {i}", now - i))

    class _C:
        def __enter__(s): return db
        def __exit__(s, *a): return False
    import core.memory.store as store
    calls = []

    async def fake_call(urls, *a, **k):
        calls.append(list(urls)); return {"connects": False, "relation": ""}

    async def fake_up(urls, timeout=3.0): return endpoint_up

    saved = (store._connect, sn.call_node_json, sn._SELF_RELATE_LOG, sn.SubconsciousNode._self_relate_endpoint_up)
    store._connect = lambda: _C(); sn.call_node_json = fake_call
    sn._SELF_RELATE_LOG = tmp / "log.jsonl"; sn.SubconsciousNode._self_relate_endpoint_up = staticmethod(fake_up)
    try:
        node = sn.SubconsciousNode.__new__(sn.SubconsciousNode)
        node.base_urls = ["http://hot:11433"]
        class CS: spirit_name = "Du"
        asyncio.run(node._self_relate_check(CS()))
    finally:
        store._connect, sn.call_node_json, sn._SELF_RELATE_LOG, sn.SubconsciousNode._self_relate_endpoint_up = saved
    rows = [json.loads(l) for l in (tmp / "log.jsonl").read_text().splitlines()] if (tmp / "log.jsonl").exists() else []
    return calls, rows


def test_pinned_world_only_and_audit_fields():
    calls, rows = _run(True)
    assert calls == [LINE_URLS]
    r = rows[0]
    assert "inner_thought" not in r["origins"] and all(o in WORLD_ORIGINS for o in r["origins"])
    assert r["n_world_items"] == len(r["fragment_ids"]) == 5
    assert "self_image_sha1" in r and r["endpoint"] == LINE_URLS[0]


def test_endpoint_down_skips():
    calls, rows = _run(False)
    assert calls == [] and rows == []
