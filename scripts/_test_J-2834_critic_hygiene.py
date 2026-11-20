"""J-2834 (F-3502, P-0008): Critic prompt hygiene.
  [1] none of the three Critic system prompts (human / internal / seedless) asks for identity_consistent.
  [2] the human prompt has no 'four values' / '(1-4)' count (it defines five violations); the internal one says (1-5).
  [3] no dated change-log text ('2026-', 'SECOND EXCEPTION') left in any prompt.
  [4] _write_output: a reply without identity_consistent follows approved; an old-style reply that carries it is honoured.
  [5] CriticOutput.JSON_SCHEMA no longer requires identity_consistent.
Model calls: none. Touches no live data."""
import re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import core  # noqa: E402,F401  (core before lab_env)
from core import schema  # noqa: E402
from core.schema import CognitiveState, CriticOutput  # noqa: E402
import nodes.critic_node as cn  # noqa: E402

assert Path(cn.__file__).resolve().parent.parent == ROOT, "test must run against its own tree"
node = cn.CriticNode()
human = node.system_prompt
internal = cn.CriticNode._SYSTEM_INTERNAL
seedless = cn.CriticNode._SEEDLESS_PROMPT
for name, p in (("human", human), ("internal", internal), ("seedless", seedless)):
    assert "identity_consistent" not in p, name
    assert "2026-" not in p and "SECOND EXCEPTION" not in p, name
    assert '"approved": true, "confidence": 0.0' in p.replace('\\"', '"'), name
assert "four values" not in human and "(1-4)" not in human and "(1\u20134)" not in human
assert "(1\u20135)" in human and "(1\u20135)" in internal
assert len(re.findall(r"^\d\. [A-Z]", human, re.M)) >= 5      # five numbered violations in the human prompt
assert "ANOTHER EXCEPTION" in human

def run(data):
    st = CognitiveState.__new__(CognitiveState)
    node._write_output(st, data)
    return st.critic
c = run({"approved": True, "confidence": 0.9, "corrections": []});  assert c.identity_consistent is True
c = run({"approved": False, "confidence": 0.9, "corrections": ["x"]}); assert c.identity_consistent is False
c = run({"approved": False, "confidence": 0.9, "identity_consistent": True, "corrections": ["x"]}); assert c.identity_consistent is True
assert "identity_consistent" not in CriticOutput.JSON_SCHEMA["required"]
print("J-2834 critic hygiene: all checks passed")
