"""
J-3253 test: the worth-judge lab is read-only, faithful to the live prompt, and its maths is right.
Asserts its own tree (worktree); writes only under a temp dir; touches no live data and makes no network call.
Run from the worktree: python scripts/_test_J-3253_worth_judge_lab.py
"""
import asyncio
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import curiosity_worth as cw            # core BEFORE the lab (and before any lab_env use)
assert Path(cw.__file__).resolve().is_relative_to(ROOT), f"core imported from the wrong tree: {cw.__file__}"

spec = importlib.util.spec_from_file_location("lab_worth_judge", ROOT / "scripts" / "lab_worth_judge.py")
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)
assert lab.ROOT == ROOT and lab.OUT == ROOT / "docs" / "lab" / "J-3253_data", "lab output must live in this worktree's docs/lab"

# 1. the lab's prompt IS the live constant, and the user message is byte-identical to what grade() sends
seen = {}


async def fake_call_json(base_urls, system, user, **kw):
    seen["system"], seen["user"], seen["urls"] = system, user, base_urls
    return {"interesting": 0.5, "reason": "x"}


val, _ = asyncio.run(cw.grade("Why did Brune go to Bremen?", ["a", "b", "c"], fake_call_json, ["http://unused"]))
assert seen["system"] == lab._cw._SYS == cw._SYS
assert seen["user"] == lab.user_msg("Why did Brune go to Bremen?", ["a", "b", "c"]), "lab user message drifted from the live one"
assert "LAN-HOST:11437" in seen["urls"][0]

# 2. parsing
assert lab.parse_json('noise {"interesting": 0.7, "reason": "r"} tail')["interesting"] == 0.7
assert lab.parse_json("<think>x</think>{\"better\": \"A\"}") == {"better": "A"}
assert lab.parse_json("not json") == {}
assert lab.grade_value({"interesting": 1.7}) == 1.0 and lab.grade_value({"interesting": {"a": 0.3}}) == 0.3
assert lab.grade_value({}) is None and lab.grade_value({"interesting": "abc"}) is None

assert [lab.parse_better(v) for v in ("A", "Question A", "option b", "neither", None, "Both")] == ["A", "A", "B", None, None, None]

# 3. AUC maths
assert lab.auc([1, 1], [0, 0]) == 1.0 and lab.auc([0, 0], [1, 1]) == 0.0 and lab.auc([0.5], [0.5]) == 0.5
assert abs(lab.auc([0.9, 0.8, 0.5], [0.8, 0.1]) - 4.5 / 6) < 1e-9
lo, hi = lab.boot_ci([0.9, 0.8, 0.9, 0.95], [0.1, 0.2, 0.15, 0.3])
assert lo == hi == 1.0

# 4. pairwise design: every item meets exactly 2K opponents, no self pairs
ids = [f"i{n}" for n in range(54)]
pairs = lab.pair_design(ids, 5)
assert len(pairs) == 54 * 5 and all(a != b for a, b in pairs)
from collections import Counter
c = Counter(x for p in pairs for x in p)
assert set(c.values()) == {10}, c

# 5. agenda builder: time-matched, excludes the question itself, distinct, newest first
fq = [{"q": f"Q{i}", "source": "curiosity", "last_offered": 100.0 + i} for i in range(20)]
fq += [{"q": "me", "source": "asked", "last_offered": 119.5}, {"q": "dup", "source": "asked", "last_offered": 119.6},
       {"q": "DUP", "source": "asked", "last_offered": 118.9}, {"q": "never", "source": "asked", "last_offered": 0},
       {"q": "wrong", "source": "consequence", "last_offered": 119.7}]
ag = lab.build_agenda("Me", 119.8, fq)
assert ag[0] == "dup" and "me" not in [x.lower() for x in ag] and "wrong" not in ag and "never" not in ag
assert len(ag) == 5 and len({x.lower() for x in ag}) == 5

# 6. the committed dataset is consistent with the pre-registration counts and has no label drift
data = json.loads((lab.OUT / "labelled.json").read_text(encoding="utf-8"))["items"]
cnt = Counter(i["label"] for i in data)
assert cnt["good"] == 16 and cnt["bad"] == 25 and cnt["borderline"] == 9, cnt
assert len({i["id"] for i in data}) == len(data) == 50
assert [k for k, _ in lab.CONTROLS] == ["K_hello", "K_2plus2", "K_book", "K_bluebird"]
assert lab.PREREG == {"auc_min": 0.80, "control_abs_max": 0.40, "control_pair_max": 0.35}

# 7. analysis end-to-end on synthetic runs in a temp dir (no live file touched)
tmp = Path(tempfile.mkdtemp(prefix="J3253_test_"))
lab.OUT = tmp
items = [{"id": f"g{i}", "q": f"g{i}", "label": "good"} for i in range(5)] + \
        [{"id": f"b{i}", "q": f"b{i}", "label": "bad"} for i in range(5)] + \
        [{"id": "K1", "q": "hello", "label": "control"}]
with open(tmp / "runs_granite.jsonl", "w", encoding="utf-8") as f:
    for it in items:
        v = 0.9 if it["label"] == "good" else 0.1
        f.write(json.dumps({"key": f"a|{it['id']}|0", "arm": "a", "id": it["id"], "rep": 0, "value": v}) + "\n")
r = lab.analyze_arm("granite", "a", items)
assert r["auc"] == 1.0 and r["controls_low"] and r["PASS"] and r["share_raw_grades_in_0.8_0.9"] == round(5 / 11, 3)
assert lab.analyze_arm("mixtral", "a", items) is None
assert lab.OUT == tmp and ROOT not in tmp.parents

print("J-3253 lab tests passed")
