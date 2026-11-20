"""
J-3232 test: the guidance-classify replay lab is read-only and faithful to the live call.
Asserts its own tree (worktree), touches no live data, writes nothing outside a temp dir.
Run from the worktree: python scripts/_test_J-3232_classify_lab.py
"""
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789/J-3583: no write to the tree's data/
import asyncio
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import guidance_learning as gl          # core BEFORE the lab (and before any lab_env use)
assert Path(gl.__file__).resolve().is_relative_to(ROOT), f"core imported from the wrong tree: {gl.__file__}"


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


lab = load("lab_guidance_classify")
rep = load("lab_guidance_classify_report")
assert lab.ROOT == ROOT and lab.OUT == ROOT / "docs" / "lab" / "J-3232_data", "lab output must live under this worktree's docs/lab"

# 1. prompt A is the live constant verbatim; C differs from A ONLY by the example placeholder
A, B, C = lab.prompt_A(), lab.PROMPT_B, lab.prompt_C()
assert A == gl._CLASSIFY_SYS
assert A != C and '"assimilate"}' in A and '"assimilate"}' not in C and "<assimilate|accommodate|unrelated>" in C
assert C.replace("<assimilate|accommodate|unrelated>", "assimilate") == A, "C must differ from A only in the example"
# 2. B is 4-way, example unfilled, and keeps the live framing sentence
for tok in ("same_lesson", "compatible_different", "contradicts", "unrelated", "<same_lesson|compatible_different|contradicts|unrelated>"):
    assert tok in B, tok
assert B.startswith("You already hold a BELIEF. You have just learned a NEW lesson.")

# 3. the lab's user message is byte-identical to what the live _classify sends (live logger patched to a no-op: no live write)
seen = {}


async def fake_call_json(base_urls, system, user, **kw):
    seen["system"], seen["user"], seen["kw"] = system, user, kw
    return {"relation": "assimilate"}


orig_log = gl._log_classify
gl._log_classify = lambda rec: None
try:
    asyncio.run(gl._classify(fake_call_json, ["http://x"], "belief text", "new text", "self"))
finally:
    gl._log_classify = orig_log
assert seen["system"] == A and seen["user"] == lab.user_msg("belief text", "new text"), "lab user message drifted from the live one"
assert seen["kw"]["max_tokens"] == 120 and seen["kw"]["temperature"] == 0.2 and seen["kw"]["tier"] == 3

# 4. parsing and verdict mapping
assert lab.parse_json('noise {"relation": "same_lesson"} tail') == {"relation": "same_lesson"}
assert lab.parse_json("not json") == {}
assert rep.verdict("A", "accommodate") == ("accommodate", False)
assert rep.verdict("B", "contradicts") == ("accommodate", False)
assert rep.verdict("B", "same_lesson") == ("corroborate", False)
assert rep.verdict("B", "compatible_different") == ("compat", False)
assert rep.verdict("A", "") == ("corroborate", True), "invalid answers take the live default (assimilate)"
lo, hi = rep.wilson(0, 28)
assert lo == 0.0 and 0.10 < hi < 0.15

# 5. the pair sets are consistent with the hand labels (when the data dir has been built)
if (lab.OUT / "pairs.json").exists():
    pairs = json.load(open(lab.OUT / "pairs.json", encoding="utf-8"))
    hand = json.load(open(lab.OUT / "hand_labels.json", encoding="utf-8"))["labels"]
    ids = [p["id"] for p in pairs]
    assert len(ids) == len(set(ids)) and set(ids) == set(hand), "every pair needs exactly one hand label"
    assert all(hand[p["id"]] == "S" for p in pairs if p["set"] in ("S", "S2"))

# 6. scratch writes go only to a temp dir
with tempfile.TemporaryDirectory() as td:
    (Path(td) / "x.json").write_text("{}")
print("J-3232 classify lab test: OK")
