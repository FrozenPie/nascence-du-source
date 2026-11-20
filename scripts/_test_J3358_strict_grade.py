"""J-3358 (D-0582): the maths grader is strict at every level incl. 10+ (answer field only, last number), the IMN
call site hands it the answer field alone, and the measurement script counts a loose pass. Writes only under a temp dir."""
import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import core  # noqa: E402,F401  BEFORE lab_env
from core import math_drill as md  # noqa: E402
import j3358_loose_grade_measure as meas  # noqa: E402

fails = []


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        fails.append(msg)


# 1. grader semantics at levels 10..17 (the grader has no level argument, so one rule for all levels)
for lv in range(10, md.MAX_LEVEL + 1):
    for _ in range(40):
        p = md._gen_hard(lv) if lv > md.HINT_AUTHORED_MAX_LEVEL else None
        if p is None:
            continue
        text, a = p
        check(md.grade(str(a), a), f"L{lv}: bare true answer passes ({text} = {a})") if _ == 0 else None
        if md.grade(str(a + 1), a):
            check(False, f"L{lv}: a+1 must fail")
        # right number in the WORKING, wrong declared answer: the caller now passes the field only
        if md.grade(f"{a + 3}", a):
            check(False, f"L{lv}: wrong field must fail")
check(md.grade("so 61*7 = 427 but the answer is 428", 427) is False, "right number mid-text, wrong last number -> miss")
check(md.grade("", 5) is False and md.grade("the final number", 5) is False, "blank / words-only field -> miss")

# 2. the IMN call site grades the answer field, never f"{working} {ans}"
src = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
check("math_drill.grade(ans, prob[\"answer\"])" in src, "IMN grades the answer field alone")
check("math_drill.grade(f\"{working}" not in src and "grade(f\"{_work" not in src, "IMN does not pass working+answer")

# 3. measurement script on a temp log
with tempfile.TemporaryDirectory() as td:
    lg = Path(td) / "log.jsonl"
    now = time.time()
    rows = [
        {"ts": now, "level": 12, "problem": "p", "his_answer": "7", "true": 7, "correct": True, "raw_answer": "7"},
        {"ts": now, "level": 12, "problem": "p", "his_answer": "the final number", "true": 7, "correct": True,
         "raw_answer": "the final number"},                      # old loose pass on a wrong declared answer
        {"ts": now, "level": 5, "problem": "p", "his_answer": "9", "true": 7, "correct": False},
    ]
    lg.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    out = Path(td) / "rep.txt"
    meas.main(lg, now - 10, out)
    txt = out.read_text(encoding="utf-8")
    check("levels >= 10: n=2, loose_pass_wrong=1" in txt, "measure counts exactly one loose pass at level >= 10")

print("FAILED" if fails else "ALL PASS")
sys.exit(1 if fails else 0)
