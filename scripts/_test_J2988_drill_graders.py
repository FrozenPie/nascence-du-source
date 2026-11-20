"""
J-2988 (F-3685): the drill graders grade the ANSWER field, a blank answer is a wobble, the article 'a' is not the note A,
and the raw answer + working head are logged. Hermetic: stubs the model call, points the drill _STATE/_LOG at a temp dir, and a
before/after hash canary on the live drill stores proves nothing outside it was written.
  python scripts/_test_J2988_drill_graders.py      # exit 0 = ALL OK
"""
import ast
import asyncio
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  BEFORE lab_env (F-2423)
from core import math_drill as md, music_drill as mu  # noqa: E402
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
import lab_env  # noqa: E402,F401

FAILS = 0


def check(c, label):
    global FAILS
    print(("  ok   " if c else "  FAIL ") + label)
    FAILS += 0 if c else 1


def h(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


LIVE = Path(r"C:\Nascence\data")
CANARY = [LIVE / n for n in ("music_drill_state.json", "music_drill_log.jsonl", "math_drill_state.json",
                             "math_drill_log.jsonl", "capability_beliefs.json")]
before = {p: h(p) for p in CANARY}
check(Path(core.__file__).resolve().parent.parent == ROOT, "core is the tree under test")
TMP = Path(tempfile.mkdtemp(prefix="j2988_"))
mu._STATE, mu._LOG = TMP / "mu_state.json", TMP / "mu_log.jsonl"
md._STATE, md._LOG = TMP / "md_state.json", TMP / "md_log.jsonl"

print("-- the four F-3685 probes now fail")
check(mu.grade("It is a minor key, so the answer is x", "A", "note") is False, "article 'a' is not the note A")
check(mu.grade("4/4 meter, measure 2 is short 2", "4", "number") is False, "meter fraction 4/4 does not supply the answer 4")
check(mu.grade("C major is C D E F G A B; answer C, Eb, G", "C E G", "notes3") is False, "scale + Eb is not the triad C E G")
check(md.grade("61*7=427 then adding 1 gives 428", 427) is False, "maths: 427 in the working, 428 final -> miss")

print("-- real answers still pass")
check(all([mu.grade("A", "A", "note"), mu.grade("A minor", "A", "note"), mu.grade("a", "A", "note"),
           mu.grade("F-sharp", "F#", "note"), mu.grade("F\u266f major", "F#", "note"), mu.grade("Bb", "Bb", "note"),
           mu.grade("E-flat", "Eb", "note")]), "note answers (A, A minor, a, F-sharp, F-sharp major, Bb, E-flat)")
check(all([mu.grade("2", "2", "number"), mu.grade("measure 4", "4", "number"), mu.grade("x = -3", "-3", "number"),
           mu.grade("4 beats", "4", "number")]), "number answers")
check(all([mu.grade("C E G", "C E G", "notes3"), mu.grade("A, C, E", "A C E", "notes3"),
           mu.grade("A minor: A C E", "A C E", "notes3"), mu.grade("C-sharp E G-sharp", "C# E G#", "notes3")]),
      "triad answers (any order / repeats fine)")
check(not mu.grade("C E", "C E G", "notes3") and not mu.grade("C E G B", "C E G", "notes3"), "a short or over-full triad is a miss")
check(all([md.grade("4300 + 172 = 4472", 4472), md.grade("3,572", 3572), md.grade("The final number is 8712.", 8712),
           md.grade("x = 427", 427)]), "maths: equation form, commas, sentence form pass on the last number")
check(not md.grade("", 5) and not md.grade("five", 5) and not mu.grade("", "2", "number") and not mu.grade("", "A", "note"),
      "blank / wordy fields never pass")
check(mu._norm_notes("A is the answer") == [] and mu._norm_notes("A, C and E") == ["a", "c", "e"]
      and mu._norm_notes("It is a good one") == [] and mu._norm_notes("a minor") == ["a"],
      "_norm_notes: article vs note A")

print("-- the log keeps the old keys and adds raw_answer + working_head")
mu.log("p" * 300, "x" * 100, "2", True, 6, "w" * 500, "r" * 500)
md.log("12 x 3", "36", 36, True, 4, "step " * 100, "36")
mrow = json.loads(mu._LOG.read_text(encoding="utf-8").splitlines()[0])
drow = json.loads(md._LOG.read_text(encoding="utf-8").splitlines()[0])
OLD = {"ts", "level", "problem", "his_answer", "true", "correct"}
check(OLD <= set(mrow) and OLD <= set(drow), "old keys all still present")
check(len(mrow["raw_answer"]) == 400 and len(mrow["working_head"]) == 200 and len(mrow["his_answer"]) == 60
      and len(mrow["problem"]) == 160, "music: raw_answer capped 400, working_head 200, old caps unchanged")
check(drow["raw_answer"] == "36" and len(drow["working_head"]) == 200 and drow["his_answer"] == "36", "maths row carries both")
mu.log("t", "A", "A", False, 5)
check(json.loads(mu._LOG.read_text(encoding="utf-8").splitlines()[-1])["raw_answer"] == "A", "old 5-arg call still works")

print("-- node wiring (real _solve_attempt, _music_lesson and _math_drill exec'd with a stubbed model)")
SRC = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
TREE = ast.parse(SRC)


def fn_code(name):
    n = next(n for n in ast.walk(TREE) if isinstance(n, ast.AsyncFunctionDef) and n.name == name)
    return textwrap.dedent(ast.get_source_segment(SRC, n))


class _Log:
    def info(self, *a, **k): pass
    def warning(self, *a, **k): pass


async def fake_call_node_json(urls, sys_prompt, user_prompt, max_tokens=500, temperature=0.1):
    return fake_call_node_json.queue.pop(0) if fake_call_node_json.queue else None


fake_call_node_json.queue = []
NS = {"asyncio": asyncio, "time": __import__("time"), "logger": _Log(), "store_fragment": lambda **k: None,
      "JOY_CROSSING": 0.0, "CognitiveState": object, "InnerMonologueNode": object,
      "call_node_json": fake_call_node_json}
for nm in ("_solve_attempt", "_math_drill", "_music_lesson"):
    exec(fn_code(nm), NS)


class Node:
    conscious_urls = ["stub"]
    _solve_attempt = NS["_solve_attempt"]
    _math_drill = NS["_math_drill"]
    _music_lesson = NS["_music_lesson"]

    def _feel_joy(self, *a, **k):
        pass

    async def _rate_drill_item(self, domain, prob):   # J-4052: J-3830 added this call; stub = rating step off
        return None


async def solve(queue, **kw):
    fake_call_node_json.queue = list(queue)
    return await Node()._solve_attempt("s", "u", **kw), len(fake_call_node_json.queue)


blank = {"working": "it is 42", "answer": ""}
good = {"working": "w", "answer": "42"}
r, left = asyncio.run(solve([blank, blank], require_answer=True))
check(r is None and left == 0, "require_answer: blank twice -> None (wobble), both tries used")
r, left = asyncio.run(solve([blank, good], require_answer=True))
check(r == good and left == 0, "require_answer: blank then answer -> the second reply")
r, _ = asyncio.run(solve([blank]))
check(r == blank, "default (composition hand etc.): behaviour unchanged, a digit anywhere is usable")
r, _ = asyncio.run(solve([{"thinking": "t", "abc": "C2"}], keys=("thinking", "abc")))
check(r is not None, "the composition hand's call shape is unchanged")


async def session(mod, name, prob, queue):
    saved = {k: getattr(mod, k) for k in ("due", "generate", "record", "log", "BATCH", "method_hint", "status", "_load")
             if hasattr(mod, k)}
    calls = {"n": 0}
    rec, logged = [], []

    def due():
        calls["n"] += 1
        return calls["n"] <= 1
    mod.due = due
    mod.generate = lambda: prob
    mod.record = lambda lvl, ok: rec.append((lvl, ok))
    mod.log = lambda *a, **k: logged.append(a)   # J-4052: J-3830 passes item_id=
    mod.BATCH = 1
    mod.method_hint = lambda lvl: "HINT"
    mod.status = lambda: {"today_done": 1}
    if hasattr(mod, "_load"):
        mod._load = lambda: {"today_done": 1, "level": 1, "window": [], "composed_today": 1}
    fake_call_node_json.queue = list(queue)
    NS["music_drill"], NS["math_drill"] = mu, md
    try:
        ran = await getattr(Node(), name)(None)
    finally:
        for k, v in saved.items():
            setattr(mod, k, v)
    return ran, rec, logged


# maths: working holds the true answer 42 but the answer field says 41 -> a MISS (the old grader credited it)
prob = {"text": "6*7", "answer": 42, "level": 9}
ran, rec, lg = asyncio.run(session(md, "_math_drill", prob,
                                   [{"working": "6*7 = 42, so I will say", "answer": "41"}, {"working": "w", "answer": "42"}]))
check(rec == [(9, False)], "maths: true answer only in the working -> independent attempt recorded as a miss")
check(bool(lg) and lg[0][5] == "6*7 = 42, so I will say" and lg[0][6] == "41" and lg[0][1] == "42",
      "maths: log gets the independent working + raw answer; his_answer is the taught one (old behaviour)")
ran, rec, lg = asyncio.run(session(md, "_math_drill", prob, [blank, blank]))
check(rec == [] and lg == [] and ran is False, "maths: blank answer twice -> skipped, never graded wrong")
ran, rec, lg = asyncio.run(session(md, "_math_drill", prob, [{"working": "x", "answer": "42"}]))
check(rec == [(9, True)], "maths: right answer field -> correct")
mprob = {"text": "which note", "answer": "A", "kind": "note", "level": 4}
ran, rec, lg = asyncio.run(session(mu, "_music_lesson", mprob,
                                   [{"working": "A is it 1", "answer": "It is a minor key, so x1"},
                                    {"working": "w1", "answer": "A"}]))
check(rec == [(4, False)], "music: article 'a' in the answer field no longer credits the note A")
ran, rec, lg = asyncio.run(session(mu, "_music_lesson", {"text": "measure?", "answer": "3", "kind": "number", "level": 6},
                                   [{"working": "the answer is 3 maybe", "answer": ""}, {"working": "3", "answer": ""}]))
check(rec == [] and lg == [], "music: blank answer field twice -> wobble, skipped, not graded from the working")

print("-- source checks")
grade_lines = [ln for ln in SRC.splitlines() if "_drill.grade(" in ln]
check(len(grade_lines) == 4 and not any(".get('working'" in ln or "working" in ln for ln in grade_lines),
      "the four drill grade() calls in the node pass the answer field only")
check("just the digits, or just the note names" in SRC and "a number, or note name(s)" not in SRC, "music schema line tightened")


def base_consts(path):
    t = subprocess.run(["git", "-C", str(ROOT), "show", "223c95c6:" + path], capture_output=True, text=True,
                       encoding="utf-8").stdout
    return {k: re.search(r"^" + k + r"\s*=\s*([^#\r\n]+)", t, re.M).group(1).strip()
            for k in ("DAILY_TARGET", "MAX_LEVEL", "ADVANCE_WINDOW", "ADVANCE_ACCURACY", "BATCH")}


for mod, rel in ((mu, "core/music_drill.py"), (md, "core/math_drill.py")):
    base = base_consts(rel)
    cur = {k: getattr(mod, k) for k in base}
    check(all(float(cur[k]) == float(base[k]) for k in base), f"{rel}: ladder constants untouched {base}")

after = {p: h(p) for p in CANARY}
check(before == after, "live drill stores + capability_beliefs byte-identical before/after (canary)")
print("\nALL OK" if FAILS == 0 else f"\n{FAILS} FAILED")
sys.exit(1 if FAILS else 0)
