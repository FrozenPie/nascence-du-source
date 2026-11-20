"""
Hermetic test for J-2923 (P-0072, F-3604): the study-note system prompt carries no sample opener, makes the
optional fields optional (once, plainly), has no duplicate /no_think, and the _norm contract is unchanged.
No LLM, no embedder, no live data; call_json is a stub.

  [1] _NOTE_SYS has none of the copied example frames ("I see that", "what strikes me", "The passage discusses",
      "The text describes") and no "/no_think" prefix
  [2] the schema keys are exactly the _norm keys, and "optional" is said once for thoughts/connects_to/question
  [3] the A-arm prompt kept for the A/B (docs/lab/J-2923_data/prompt_A.txt) still HAS the copied frames (the control
      is really the old prompt)
  [4] _norm contract: empty thoughts / connects_to / question stay empty strings; an empty understanding is
      rejected by compose_note (returns None); clamps unchanged
  [5] compose_note sends the system prompt unchanged and the passage cap (5000) unchanged
  [6] the hot lane really sends think:false and does not need the prefix (core/model_client.py source check)

Run:  python scripts/_test_J-2923_study_note_prompt.py   (from the tree under test)
"""
from __future__ import annotations
import asyncio, json, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # BEFORE lab_env: the tree under test must win on sys.path
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
from core import study_note as sn

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(("PASS " if cond else "FAIL ") + name)

S = sn._NOTE_SYS
low = S.lower()

# [1]
for frame in ("i see that", "what strikes me", "strikes me is", "i now grasp", "first person: '"):
    check(f"[1] no copied frame {frame!r}", frame not in low)
# the two QUOTED negations are kept on purpose: the A/B showed that without them 25 percent of notes opened
# "The passage <verb>" (third person, and that sentence boards the follow line as the claim); with them 0 to 2 of 10
check("[1] the anti-'The passage discusses' negation is kept (A/B evidence, see docs/lab/J-2923_data/summary.json)",
      "Do NOT write 'The passage discusses' or 'The text describes'" in S)
check("[1] no /no_think prefix", "no_think" not in low)

# [2]
m = re.search(r"Output ONLY JSON: (\{.*\})\s*$", S, re.S)
schema_keys = re.findall(r'"(\w+)":', m.group(1)) if m else []
norm_keys = list(sn._norm({}).keys())
check("[2] schema keys == _norm keys", schema_keys == norm_keys)
check("[2] 'optional' said exactly once", low.count("optional") == 1)
check("[2] the optional sentence names all three fields",
      all(k in S.split("optional")[0][-60:] + S.split("optional")[1][:120] for k in ("thoughts", "connects_to", "question")))
check("[2] no 'or empty' tail left in the schema descriptions", "or empty" not in low and "empty if" not in low)

# [3]
A = (ROOT / "docs" / "lab" / "J-2923_data" / "prompt_A.txt").read_text(encoding="utf-8")
check("[3] A arm is the old prompt", "I see that" in A and "what strikes me is" in A and A.startswith("/no_think"))

# [4]
n = sn._norm({"title": "t", "subject": "s", "understanding": "u", "key_facts": ["a", " "], "thoughts": "", "connects_to": None})
check("[4] empty optional fields stay empty strings", n["thoughts"] == "" and n["connects_to"] == "" and n["question"] == "")
check("[4] key_facts drops blanks", n["key_facts"] == ["a"])
check("[4] clamps unchanged", len(sn._norm({"understanding": "x" * 7000})["understanding"]) == 6000
      and len(sn._norm({"thoughts": "x" * 3000})["thoughts"]) == 2000)

# [5]
seen = {}
async def stub(urls, sysmsg, user, **kw):
    seen["sys"], seen["user"], seen["kw"] = sysmsg, user, kw
    return {"title": "T", "subject": "knots", "understanding": "A knot is a hitch.", "key_facts": [], "thoughts": ""}
note = asyncio.run(sn.compose_note(stub, ["http://x"], "Some Book", "p" * 6000))
check("[5] compose_note passes _NOTE_SYS unchanged", seen["sys"] == S)
check("[5] passage still capped at 5000", seen["user"].count("p") - "Some Book".count("p") <= 5000 + 20 and "p" * 5001 not in seen["user"])
check("[5] budget unchanged (1500 / 0.5)", seen["kw"].get("max_tokens") == 1500 and seen["kw"].get("temperature") == 0.5)
check("[5] empty thoughts survive compose_note", note and note["thoughts"] == "")
async def stub_empty(urls, sysmsg, user, **kw):
    return {"title": "T", "understanding": "  "}
check("[5] empty understanding -> None", asyncio.run(sn.compose_note(stub_empty, ["http://x"], "B", "p")) is None)

# [6]
mc = (ROOT / "core" / "model_client.py").read_text(encoding="utf-8")
check("[6] hot lane sends hard think", '"think": bool(think)' in mc)
check("[6] llama-server branch prepends _NO_THINK itself", '"content": _NO_THINK + system_prompt' in mc)
check("[6] write_or_revise callers pass call_node_json",
      (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8").count("_sn.write_or_revise(call_node_json") == 2)

print("ALL PASS" if ok_all else "SOME FAILED")
sys.exit(0 if ok_all else 1)
