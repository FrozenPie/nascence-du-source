"""
J-3195 (D-0582, F-3686): the maths ladder extended 9 -> 17. Hermetic: no LLM, no hub, no DB; the ladder state/log paths are
pointed at a temp dir and a before/after sha256 canary on the live stores proves nothing outside it was written.
Checks, per new level (10-17): every drawn problem's answer matches an INDEPENDENT re-solve parsed from the problem TEXT
(not the generator's own arithmetic); the answer is a whole number >= 3 that is not one of the numbers printed in the
problem; the level offers variety and the kind is the one the level claims; grade() accepts the true answer and rejects a
wrong one. Plus: levels 1-9 generate exactly as before (byte-identical to the pre-J-3195 baseline commit f9bd17c3, the parent of 4aafad72, for the same seed), method_hint() source is
untouched, the ladder climbs 9 -> 17 and stops at MAX_LEVEL, and the state a live Du is parked in (level 9, window of forty
correct) steps to 10 on its first result.
  python scripts/_test_math_drill_levels_j3195.py      # exit 0 = ALL OK
"""
import ast
import hashlib
import importlib.util
import json
import math
import random
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  BEFORE lab_env (F-2423)
from core import math_drill as md  # noqa: E402
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
import lab_env  # noqa: E402,F401

LIVE_DATA = Path(r"C:\Nascence\data")
# J-3707: baseline pinned to the parent of the J-3195 commit (4aafad72), NOT git HEAD (HEAD is post-J-3195).
BASELINE_COMMIT = "f9bd17c3533979d0772b26184c92140acd19077a"
FAILS = 0


def check(c, label):
    global FAILS
    print(("  ok   " if c else "  FAIL ") + label)
    FAILS += 0 if c else 1


def h(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


check(Path(core.__file__).resolve().is_relative_to(ROOT), "core.__file__ is inside the tree under test")
check(Path(md.__file__).resolve().is_relative_to(ROOT), "math_drill is the worktree copy")
CANARY = [LIVE_DATA / "math_drill_state.json", LIVE_DATA / "math_drill_log.jsonl", LIVE_DATA / "capability_beliefs.json"]
before = {p: h(p) for p in CANARY}
_TMP = Path(tempfile.mkdtemp(prefix="j3195_math_"))
md._STATE = _TMP / "math_drill_state.json"
md._LOG = _TMP / "math_drill_log.jsonl"


def nums(t):
    return [int(x) for x in re.findall(r"\d+", t)]


def py_expr(t):
    """Text -> a python integer expression, by a different route from the generator."""
    return t.replace("×", "*").replace("÷", "//").replace("^", "**")


def solve_x(t):
    """Brute-force the unique positive integer x for 'x when <lhs> = <rhs>' by substitution."""
    eq = t.split("when", 1)[1]
    eq = re.sub(r"(\d)x", r"\1*x", eq)
    eq = re.sub(r"(\d)\(", r"\1*(", eq)
    lhs, rhs = eq.split("=")
    sols = [x for x in range(1, 200) if eval(lhs, {"x": x}) == eval(rhs, {"x": x})]
    return sols[0] if len(sols) == 1 else None


def resolve(level, t):
    if level in (10, 11):
        e = py_expr(t)
        # a ÷ must be exact: re-evaluate with true division and compare
        v_true = eval(e.replace("//", "/"))
        v_int = eval(e)
        return v_int if v_true == v_int else None
    if level == 12:
        m = re.match(r"the remainder when (.+) is divided by (\d+)$", t)
        return eval(py_expr(m.group(1))) % int(m.group(2))
    if level == 13:
        return solve_x(t)
    if level == 14:
        terms = [int(x) for x in t.replace("+ ... +", "+").split("+")]
        a, a1 = terms[0], terms[1]
        d = a1 - a
        last = terms[-1]
        if (last - a) % d or terms[:3] != [a, a + d, a + 2 * d]:
            return None
        return sum(range(a, last + 1, d))
    if level == 15:
        ks = re.findall(r"choose (\d+) things from (\d+)", t)
        tot = math.comb(int(ks[0][1]), int(ks[0][0]))
        m = re.search(r"choose 2 things from (\d+)", t)
        if m:
            tot -= int(m.group(1)) * (int(m.group(1)) - 1) // 2
        return tot
    if level == 16:
        m = re.match(r"(\d+) \(base (\d+)\) converted to base 10$", t)
        if m:
            return int(m.group(1), int(m.group(2)))
        m = re.match(r"(\d+) written in base 2 \(binary\)$", t)
        return int(format(int(m.group(1)), "b"))
    if level == 17:
        if t.startswith("x when"):
            return solve_x(t)
        m = re.match(r"the remainder when (.+) is divided by (\d+)$", t)
        return eval(py_expr(m.group(1))) % int(m.group(2))
    raise AssertionError(level)


KIND = {10: lambda t: "^" in t, 11: lambda t: t.count("(") >= 2, 12: lambda t: t.startswith("the remainder"),
        13: lambda t: t.startswith("x when"), 14: lambda t: "..." in t, 15: lambda t: "ways to choose" in t,
        16: lambda t: "base" in t, 17: lambda t: ("^3" in t) or ("(x -" in t)}

random.seed(3195)
N = 600
print("\n-- per-level draws (%d each) --" % N)
for lv in range(10, 18):
    bad_resolve = bad_range = bad_op = bad_kind = bad_grade = 0
    texts = set()
    forms = set()
    for _ in range(N):
        t, a = md._gen(lv)
        texts.add(t)
        r = resolve(lv, t)
        if r != a:
            bad_resolve += 1
        if not (isinstance(a, int) and a >= 3):
            bad_range += 1
        if a in nums(t):
            bad_op += 1
        if not KIND[lv](t):
            bad_kind += 1
        if not (md.grade(f"working {a}", a) and not md.grade(f"working {a + 1}", a)):
            bad_grade += 1
        forms.add(re.sub(r"\d+", "#", t))
    check(bad_resolve == 0, f"L{lv}: {N} answers match an independent re-solve from the text ({bad_resolve} bad)")
    check(bad_range == 0 and bad_op == 0, f"L{lv}: answers are whole numbers >= 3 and never a printed operand ({bad_range}/{bad_op} bad)")
    check(bad_kind == 0, f"L{lv}: every problem is the kind the level claims")
    check(bad_grade == 0, f"L{lv}: grade() accepts the true answer and rejects answer+1")
    check(len(texts) >= 150, f"L{lv}: variety ({len(texts)} distinct of {N}, {len(forms)} shapes)")

print("\n-- levels 1-9 unchanged, method_hint untouched --")
head = subprocess.run(["git", "show", f"{BASELINE_COMMIT}:core/math_drill.py"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8").stdout
check("MAX_LEVEL          = 9 " in head, "baseline copy is the pre-J-3195 module (MAX_LEVEL 9)")
spec = importlib.util.spec_from_loader("md_head", loader=None)
old = importlib.util.module_from_spec(spec)
old.__dict__["__file__"] = str(ROOT / "core" / "math_drill.py")
exec(compile(head, "md_head", "exec"), old.__dict__)
same = True
for lv in range(1, 10):
    for seed in range(40):
        random.seed(seed * 100 + lv)
        x = md._gen(lv)
        random.seed(seed * 100 + lv)
        y = old._gen(lv)
        same &= (x == y)
check(same, "levels 1-9: same seed gives the same problem as the pre-J-3195 baseline (360 draws)")


def fn_src(text, name):
    """sha256 of one function's source segment, cut from the module TEXT (HEAD copy vs worktree file)."""
    node = next(n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == name)
    return hashlib.sha256(ast.get_source_segment(text, node).encode()).hexdigest()


cur = (ROOT / "core" / "math_drill.py").read_text(encoding="utf-8")


check(fn_src(cur, "method_hint") == fn_src(head, "method_hint"), "method_hint() source is byte-identical to the pre-J-3195 baseline (Travis-authored, D-0583)")
check(fn_src(cur, "record") == fn_src(head, "record"), "record() untouched (grade() was deliberately changed by J-2988: last number of the answer field)")
check(md.method_hint(10) == md.method_hint(1) and md.HINT_AUTHORED_MAX_LEVEL == 9,
      "level 10+ has no authored hint (falls through to the generic text) and HINT_AUTHORED_MAX_LEVEL says so")

print("\n-- ladder mechanics (temp state) --")
check(md.MAX_LEVEL == 17, "MAX_LEVEL == 17")
md._STATE.write_text(json.dumps({"level": 9, "streak": 301, "window": [1] * 40, "today_done": 0,
                                 "day": __import__("datetime").date.today().isoformat()}), encoding="utf-8")
d = md.record(9, True)
check(d["level"] == 10 and d["window"] == [], "a parked Du (level 9, forty correct) steps to level 10 on its first result and the window clears")
lvl = 10
for lv in range(10, 18):
    for _ in range(md.ADVANCE_WINDOW):
        d = md.record(lv, True)
    lvl = d["level"]
check(lvl == 17, "climbing at 95%+ reaches 17 and stops there")
for _ in range(md.ADVANCE_WINDOW):
    d = md.record(17, True)
check(d["level"] == 17, "level 17 is the ceiling (no level 18)")
md._STATE.write_text(json.dumps({"level": 12, "window": [1] * 36 + [0] * 4, "day": __import__("datetime").date.today().isoformat()}), encoding="utf-8")
d = md.record(12, True)
check(d["level"] == 12, "90% over the window does not advance")
g = md.generate()
check(g["level"] == 12 and md.grade(f"x {g['answer']}", g["answer"]), "generate() serves the saved level")
md.log(g["text"], str(g["answer"]), g["answer"], True, g["level"])
check(md._LOG.exists() and md._LOG.parent == _TMP, "log goes to the temp dir")

print("\n-- sample, 3 per new level (seed 31950) --")
random.seed(31950)
for lv in range(10, 18):
    for _ in range(3):
        t, a = md._gen(lv)
        print(f"  L{lv}: {t} = {a}")

after = {p: h(p) for p in CANARY}
check(before == after, "live math_drill_state/log + capability_beliefs byte-identical before/after (canary)")
print("\nALL OK" if FAILS == 0 else f"\n{FAILS} FAILED")
sys.exit(1 if FAILS else 0)
