"""J-2800 test: Perception drops schema-token entities; internal event_type fix is flag-gated.
Stubs everything (no model call); writes nothing."""
import sys
from pathlib import Path

TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core  # noqa: E402,F401
try:
    import lab_env  # noqa: E402,F401
except Exception:
    pass
assert Path(core.__file__).resolve().is_relative_to(TREE), core.__file__
from nodes import perception_node as pn  # noqa: E402
from core.schema import CognitiveState  # noqa: E402
assert Path(pn.__file__).resolve().is_relative_to(TREE)

# 1. cleaner
assert pn._clean_entities(["the_entity", "gardening", "The Person", "string", "mixed", "Travis", "the-world", "", None, 3]) == ["gardening", "Travis"]
assert pn._clean_entities(["the_entity"]) == [] and pn._clean_entities(None) == [] and pn._clean_entities("x") == []
assert pn._clean_entities(["entity of the garden"]) == ["entity of the garden"]  # only exact tokens are dropped

node = pn.PerceptionNode()
base = {"event_type": "input", "context_type": "question", "entities": ["the_entity", "lamp", "the_world"],
        "summary": "s", "subject": "the_entity", "register": "task"}

def run(input_type):
    st = CognitiveState(spirit_name="t", axiom="a", raw_input="x")
    st.input_type = input_type
    node._write_output(st, dict(base))
    return st.perception

# 2. entities stripped on both paths
for it in ("human", "internal"):
    assert run(it).entities == ["lamp"], it
# 3. event_type untouched while the flag is OFF (default)
assert pn.PERCEPTION_INTERNAL_EVENT_TYPE_ON is False
assert run("internal").event_type == "input"
# 4. flag ON: internal 'input' -> 'internal'; human unchanged; other values unchanged
pn.PERCEPTION_INTERNAL_EVENT_TYPE_ON = True
assert run("internal").event_type == "internal"
assert run("human").event_type == "input"
base["event_type"] = "memory_surface"
assert run("internal").event_type == "memory_surface"
print("J-2800 perception tests OK")
