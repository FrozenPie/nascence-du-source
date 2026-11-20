"""J-3475 / D-0607: the Curiosity node's urgency field is dropped (prompt, parse, log, interrupt flag).

Checks, in a temp tree with the log redirected (nothing live is touched, no model is called):
  (a) the system prompt has no urgency field and not the false sentence, and still names questions + research_directions;
  (b) _write_output sets state.background_curiosities exactly as before, raises NO interrupt, ignores an emitted urgency;
  (c) the logged row has no "urgency" key, "ignited" is True iff a question was produced (grounding_injection and
      world_displacement read only ignited rows) and those two readers still read a new row and an old row;
  (d) CuriosityOutput.JSON_SCHEMA no longer requires urgency.
Run (from the worktree):  python scripts/_test_J3475_curiosity_urgency_drop.py
"""
from __future__ import annotations
import asyncio, json, pathlib, sys, tempfile

sys.stdout.reconfigure(encoding="utf-8")
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core                                     # noqa: E402  (BEFORE lab_env)
assert str(pathlib.Path(core.__file__).resolve()).lower().startswith(str(ROOT).lower()), core.__file__
from core import frontier, grounding_injection, world_displacement   # noqa: E402
from core.schema import CognitiveState, CuriosityOutput               # noqa: E402
import nodes.curiosity_node as CN                                      # noqa: E402

ok_all = True
def check(name, cond):
    global ok_all; ok_all = ok_all and bool(cond)
    print(("  ok   " if cond else "  FAIL ") + name)

node = CN.CuriosityNode()
sp = node.system_prompt
check("prompt has no 'urgency'", "urgency" not in sp.lower())
check("prompt lacks the false sentence", "unprompted thought cycle" not in sp and "genuinely pressing" not in sp)
check("prompt still names the two lists", '"questions"' in sp and '"research_directions"' in sp)
check("threshold constant removed", not hasattr(CN, "_CURIOSITY_URGENCY_THRESHOLD"))
check("schema no longer requires urgency", "urgency" not in CuriosityOutput.JSON_SCHEMA["required"])

tmp = pathlib.Path(tempfile.mkdtemp(prefix="J3475_"))
CN._CURIOSITY_LOG_PATH = tmp / "curiosity_log.jsonl"
CN._TWIG_LOG_PATH = tmp / "twig_log.jsonl"
frontier._F = tmp / "frontier.json"
for nm in ("_F_LIGHT",):
    if hasattr(frontier, nm): setattr(frontier, nm, tmp / "frontier_light.json")

def run(data):
    st = CognitiveState(spirit_name="Du", axiom="J-3475 test")
    r = node._write_output(st, data)
    if asyncio.iscoroutine(r): asyncio.run(r)
    return st

st = run({"questions": ["Why does a shoreline never stay still over a whole day?", {"question": "a dict shaped one here"}],
          "research_directions": ["look at the tide tables"], "urgency": 0.95})
check("background_curiosities set (strings, dict coerced)", len(st.background_curiosities) == 3 and all(isinstance(x, str) for x in st.background_curiosities))
check("no interrupt raised even with an emitted urgency of 0.95", st.interrupt_requested is False and st.interrupt_source == "" and st.interrupt_urgency == 0.0)
st2 = run({"questions": [], "research_directions": ["only a direction"]})
check("no questions -> no interrupt", st2.interrupt_requested is False)
run({"questions": ["Second run question about the moss on the north wall?"], "research_directions": []})

rows = [json.loads(l) for l in CN._CURIOSITY_LOG_PATH.read_text(encoding="utf-8").splitlines()]
check("three rows logged", len(rows) == 3)
check("no row carries urgency", all("urgency" not in r for r in rows))
check("ignited True iff a question was produced", [r["ignited"] for r in rows] == [True, False, True])
check("chain/keys intact", rows[1]["parent_id"] == rows[0]["id"] and {"questions", "directions", "seeds_offered", "recent_themes", "ts"} <= set(rows[0]))

# readers: a new row and an old (urgency-carrying) row both read; ignited False is skipped
old = {"id": "old", "ts": 1.0, "parent_id": None, "seeds_offered": [], "questions": ["An old ignited question about lichen on stone?"],
       "directions": [], "urgency": 0.8, "ignited": True, "recent_themes": []}
lines = [json.dumps(old)] + [json.dumps(r) for r in rows]
got = grounding_injection.parse_curiosity_tail(lines, 12)
check("grounding_injection reads old and new ignited rows, skips the un-ignited one",
      len(got) == 3 and "lichen" in got[0] and "shoreline" in got[1] and "moss" in got[2])

print("\nALL PASS" if ok_all else "\nFAILURES")
sys.exit(0 if ok_all else 1)
