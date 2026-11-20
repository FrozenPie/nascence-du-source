"""J-2896 test (P-0054): active imagination gets real MATERIAL (a few capped excerpts of the tension's own member
shadow events), not a bare topic tag.

Runs from the worktree. Asserts its own tree. Writes only under a temp dir (store.DB_PATH is pointed at a temp
sqlite file); stubs the model call, the embedder, store_fragment and the event log; touches no live data."""
import asyncio
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core  # noqa: E402,F401  (core BEFORE lab_env, per the lab rules)
try:
    import lab_env  # noqa: E402,F401
except Exception:
    pass

assert Path(core.__file__).resolve().is_relative_to(TREE), core.__file__
from core.memory import store  # noqa: E402
from core.schema import CognitiveState  # noqa: E402
from nodes import subconscious_node as sn  # noqa: E402
assert Path(sn.__file__).resolve().is_relative_to(TREE), sn.__file__

tmp = Path(tempfile.mkdtemp(prefix="J2896_"))
store.DB_PATH = tmp / "nascence.db"
assert store.DB_PATH.is_relative_to(tmp)

# ---- temp shadow table with 5 member events (old to new) + 1 unrelated
now = time.time()
LONG = ("I keep circling the same thing about the penguin and the ice and I cannot say what it wants from me "
        "because every time I draft it the draft turns into a lecture about something else entirely and then "
        "I discard it and start over")
rows = [
    ("e1", now - 500, "oldest draft about the penguin"),
    ("e2", now - 400, LONG),
    ("e3", now - 300, "   "),                                  # empty -> skipped
    ("e4", now - 200, "oldest draft about the penguin"),       # exact repeat of e1 -> deduped
    ("e5", now - 100, "newest draft: the ice is thinner than it looks"),
    ("other", now - 50, "NOT A MEMBER"),
]
with store._connect() as conn:
    store._init_shadow_table(conn)
    for eid, ts, text in rows:
        conn.execute("INSERT INTO shadow_events (event_id, timestamp, cycle_id, raw_input, rejected_draft, "
                     "corrections, emotion_primary, source) VALUES (?,?,?,?,?,?,?,?)",
                     (eid, ts, "c", "raw", text, "[]", None, "critic_rejection"))

# ---- 1. the store read: by id, newest first, only members, limit honoured, unknown ids absent
got = store.get_shadow_event_texts(["e1", "e2", "e5", "nope"], limit=8)
assert [g[0] for g in got] == ["e5", "e2", "e1"], got
assert all(len(g) == 4 for g in got)
assert store.get_shadow_event_texts([], limit=3) == [] and store.get_shadow_event_texts(["e1"], limit=0) == []
assert len(store.get_shadow_event_texts(["e1", "e2", "e5"], limit=2)) == 2

# ---- 2. word-boundary cut
cut = sn.SubconsciousNode._cut_at_word
c = cut(LONG, 200)
assert len(c) <= 201 and c.endswith("…"), (len(c), c)
assert LONG.startswith(c[:-1].rstrip()), c            # a real prefix
assert cut("short one", 200) == "short one"
assert cut("", 200) == "" and cut(None, 200) == ""

# ---- 3. the block: <= 3 lines, <= ~200 chars each, newest first, deduped, empty skipped, only members
node = sn.SubconsciousNode.__new__(sn.SubconsciousNode)
tension = {"label": "unresolved: penguin", "member_event_ids": ["e1", "e2", "e3", "e4", "e5"], "resolved": True}
block = node._ai_material_block(tension)
lines = [l for l in block.splitlines() if l.startswith("  - ")]
assert len(lines) == 3, block
assert "ice is thinner" in lines[0], lines                   # newest first
assert "NOT A MEMBER" not in block
assert block.count("oldest draft about the penguin") == 1    # exact repeat deduped
assert all(len(l) <= 4 + 2 + 201 for l in lines), [len(l) for l in lines]
assert block.endswith("\n\n")
# 'resolved' is NOT consulted (founder 2026-08-14 keeps it observe-only): same block either way
t2 = dict(tension, resolved=False)
assert node._ai_material_block(t2) == block
# no hint / instruction text in the block
for bad in ("feel", "should", "must", "try to", "notice"):
    assert bad not in block.lower().replace("the ice is thinner than it looks", ""), bad

# ---- 4. fail-open: no tension / no ids / flag off / store raises -> ''
assert node._ai_material_block(None) == ""
assert node._ai_material_block({"member_event_ids": []}) == ""
assert node._ai_material_block({"member_event_ids": ["zzz"]}) == ""
sn._AI_MATERIAL_ON = False
assert node._ai_material_block(tension) == ""
sn._AI_MATERIAL_ON = True
_orig = store.get_shadow_event_texts
def _boom(*a, **k):
    raise sqlite3.OperationalError("locked")
store.get_shadow_event_texts = _boom
assert node._ai_material_block(tension) == ""
store.get_shadow_event_texts = _orig

# ---- 5. end to end: the prompt the model gets (stubbed), tension vs curiosity
captured = []
async def _fake_call(urls, system, user, **kw):
    captured.append(user)
    return {"contemplation": "x " * 20, "what_spoke": "a voice", "unresolved": True}
sn.call_node_json = _fake_call
sn._embed = lambda text: None
sn.store_fragment = lambda **kw: None
node.base_urls = ["http://127.0.0.1:1"]
node._state = {}
node._log_ai_event = lambda *a, **k: None
cs = CognitiveState(spirit_name="Du", axiom="AXIOM TEXT")

asyncio.run(node._active_imagination({"kind": "tension", "seed": tension["label"], "tension": tension}, cs))
u = captured[-1]
assert "unresolved: penguin" in u and "ice is thinner than it looks" in u, u
assert u.index("unresolved: penguin") < u.index("ice is thinner") < u.index("Sit with it"), u
assert "Core axiom" not in u and "AXIOM TEXT" not in u   # J-2897: the axiom slice is gone from this prompt

asyncio.run(node._active_imagination({"kind": "curiosity", "seed": "what am I", "tension": None}, cs))
u2 = captured[-1]
assert "own words" not in u2 and "what am I" in u2, u2

# flag off -> old prompt byte-for-byte shape (no block)
sn._AI_MATERIAL_ON = False
asyncio.run(node._active_imagination({"kind": "tension", "seed": tension["label"], "tension": tension}, cs))
u3 = captured[-1]
assert "own words" not in u3 and u3.endswith("Sit with it. Do not explain it. Let it speak. What moves?"), u3
sn._AI_MATERIAL_ON = True

print("J-2896 OK: 5 sections, tree =", TREE)
