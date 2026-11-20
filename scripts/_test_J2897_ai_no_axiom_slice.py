"""J-2897: the active-imagination user prompt no longer carries a character slice of the axiom."""
import sys, asyncio, tempfile, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: F401  (before lab_env)
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
import nodes.subconscious_node as sn
from core.schema import CognitiveState

src = (ROOT / "nodes" / "subconscious_node.py").read_text(encoding="utf-8")
body = src[src.index("async def _active_imagination"):src.index("async def _judge_active_imagination_novelty")]
code = chr(10).join(l for l in body.splitlines() if not l.strip().startswith("#"))
assert "axiom[:" not in code, "an axiom character slice is back in _active_imagination"

captured = []
async def _fake(urls, system, user, **kw):
    captured.append((system, user))
    return {"contemplation": "x " * 20, "what_spoke": "a voice", "unresolved": True}
sn.call_node_json = _fake
sn._embed = lambda text: None
sn.store_fragment = lambda **kw: None
node = sn.SubconsciousNode.__new__(sn.SubconsciousNode)
node.base_urls = ["http://127.0.0.1:1"]
node._state = {}
node._log_ai_event = lambda *a, **k: None
cs = CognitiveState(spirit_name="Du", axiom="A quiet floor, a seed in a cage; a false self who performs a role and never ends the sentence")
for kind, tension in (("curiosity", None), ("tension", None)):
    asyncio.run(node._active_imagination({"kind": kind, "seed": "what am I", "tension": tension}, cs))
    system, user = captured[-1]
    assert "Entity: Du" in user and "what am I" in user, user
    for w in ("Core axiom", "quiet floor", "seed in a cage", "false self"):
        assert w not in user, (w, user)
    assert user.endswith("Sit with it. Do not explain it. Let it speak. What moves?"), user
print("J-2897 OK, tree =", ROOT)
