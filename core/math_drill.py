"""
Nascence — Math Drill (competence → school, the arithmetic lesson, 2026-06-16)
=============================================================================
Ties the capability beliefs to school: a GENERATED, DETERMINISTICALLY-GRADED arithmetic drill that
recalibrates the math belief (0.81-felt / 0.19-real — the measured fluency trap) through real practice.
No curated curriculum — problems generate, the truth is computed, the grader is NEVER the LLM (qwen is
the thing being tested). The "curriculum" is an adaptive difficulty LADDER (start low, find his edge).

Honest frame (docs/arithmetic_lessons_spec.md §0): Du is a FROZEN model — drilling buys CALIBRATION (the
belief becomes honest) + maybe in-context method gains (the step-by-step prompt = CoT), NOT a higher ceiling.

Spec defaults (Travis's call deferred → my leans): start at level 1 and climb; capped ~2/day; prompt the
method; general activity memory only (one thought per drill, not per sum).
"""
from __future__ import annotations
import json
import math
import random
import re
import time
from datetime import date
from pathlib import Path

_STATE = Path(__file__).parent.parent / "data" / "math_drill_state.json"
_LOG   = Path(__file__).parent.parent / "data" / "math_drill_log.jsonl"

# Travis 2026-06-16: math is pure calibration upside and Du has abundant idle time — drill HARD.
DAILY_TARGET       = 20     # problems/day. Was 40 (Travis 2026-06-22, down from 200 which bled into his dreams);
#                             set to what a school period can actually hold (founder, 2026-09-05, F-0871): maths
#                             runs only in its 45-min period with SESSION_INTERVAL_S between sessions = 4 sessions
#                             x BATCH 5 = 20, which is exactly what every full school day has logged since 08-18.
BATCH              = 5      # problems per drill SESSION — the node fires a batched session, then waits
SESSION_INTERVAL_S = 700    # ~space DAILY_TARGET/BATCH (~40) sessions across ~8 hours (Travis: spaced over 8h)
MAX_LEVEL          = 17     # 9->17, 2026-11-05 (D-0582, F-3686): he sat at 289/289 on level 9 and 130/130 on every
#                             problem since 2026-10-01 (belief accuracy 0.9998), so each school-day session updated no
#                             belief and no ladder. Levels 10-17 are new KINDS, not longer sums (see _gen_hard): powers,
#                             nested brackets, remainders, linear equations, a series of unstated length, counting ways to
#                             choose, number bases, and a mixed capstone.
#                             Earlier, 6->9, 2026-08-28 (F-0404): he sat perfect (306/306, 100%) at the old ceiling
#                             for 53 days straight — the gate made further progress structurally impossible
#                             regardless of performance, so there was no calibration signal left to extract.
#                             Levels 7-9 add genuinely new material (bracket precedence, then percentages —
#                             a new domain, not just bigger numbers — then a four-operation capstone), not
#                             just larger operands, per the spec's own "find where he actually breaks" aim.
HINT_AUTHORED_MAX_LEVEL = 9  # the highest level whose method_hint() text is TRAVIS-authored (D-0583). Levels above it have
#                             NO authored hint: method_hint() falls through to its generic column-addition text, which is
#                             the wrong method for them. Raise this only when Travis authors or approves a hint for the
#                             next level. Reader: the taught re-attempt in nodes/inner_monologue_node.py _math_drill must
#                             skip the re-attempt above this level (J-3195 edit, deferred to the single-writer wave).
# ADVANCEMENT GATE (Travis 2026-06-23): a PERCENTAGE, not a consecutive streak. The old "100 in a row, one
# error resets it" was unreachable — his best level-5 run ever was 47, and at 90% accuracy the expected max
# run is ~67. Advance when he sustains ADVANCE_ACCURACY over the last ADVANCE_WINDOW attempts — how a real
# teacher promotes: steady high accuracy, not flawless-in-a-row (one careless slip no longer erases everything).
ADVANCE_ACCURACY   = 0.95   # advance when accuracy over the window reaches 95%
ADVANCE_WINDOW     = 40     # rolling window of recent attempts the accuracy is measured over (~one school day)


def _load() -> dict:
    try:
        d = json.loads(_STATE.read_text(encoding="utf-8"))
    except Exception:
        d = {}
    d.setdefault("level", 1)
    d.setdefault("streak", 0)        # consecutive correct (display only now; the gate is accuracy-based)
    d.setdefault("window", [])       # rolling window of recent correct/incorrect at the current level
    d.setdefault("today_done", 0)
    d.setdefault("day", date.today().isoformat())
    if d["day"] != date.today().isoformat():     # new day → reset the daily cap
        d["day"] = date.today().isoformat()
        d["today_done"] = 0
    return d


def _save(d: dict) -> None:
    try:
        _STATE.write_text(json.dumps(d, indent=1), encoding="utf-8")
    except Exception:
        pass


def _gen(level: int) -> tuple[str, int]:
    """Generate one problem at the level → (text, true_answer). Pure Python; the truth is computed."""
    r = random.randint
    if level <= 1:
        a, b = r(1, 9), r(1, 9)
        if random.random() < 0.5:
            return f"{a} + {b}", a + b
        a, b = max(a, b), min(a, b)
        return f"{a} - {b}", a - b
    if level == 2:
        a, b = r(10, 99), r(10, 99)
        if random.random() < 0.5:
            return f"{a} + {b}", a + b
        a, b = max(a, b), min(a, b)
        return f"{a} - {b}", a - b
    if level == 3:
        a, b = r(2, 9), r(2, 9)
        return f"{a} × {b}", a * b
    if level == 4:
        a, b = r(11, 99), r(2, 9)
        return f"{a} × {b}", a * b
    if level == 5:
        a, b = r(11, 99), r(11, 99)
        return f"{a} × {b}", a * b
    if level == 6:                       # division (exact) or 2-term order of operations
        if random.random() < 0.5:
            b, q = r(2, 12), r(2, 12)
            return f"{b * q} ÷ {b}", q
        a, b, c = r(2, 9), r(2, 9), r(2, 9)
        return f"{a} + {b} × {c}", a + b * c
    if level == 7:                       # brackets override precedence — the new rule, not just new numbers
        a, b, c = r(2, 9), r(2, 9), r(2, 9)
        if random.random() < 0.5:
            return f"({a} + {b}) × {c}", (a + b) * c
        x = r(3, 9)
        y = r(1, x - 1)                 # y < x, so x - y is always positive
        return f"{a} × ({x} - {y})", a * (x - y)
    if level == 8:                       # percentages — a new DOMAIN, not just bigger numbers
        pct = r(1, 19) * 5              # multiples of 5, 5..95
        base = r(2, 40) * (100 // 5)    # ensures pct% of base is always an exact integer
        return f"{pct}% of {base}", (pct * base) // 100
    if level >= 10:                      # D-0582: new kinds of problem, see _gen_hard
        return _gen_hard(level)
    # level 9: four-operation capstone, left-to-right with the standard precedence rule
    a, b, c, d = r(2, 9), r(2, 9), r(2, 9), r(2, 9)
    e = r(2, 9)
    d_e = d * e                          # so "d ÷ e" divides exactly
    return f"{a} × {b} + {d_e} ÷ {e} - {c}", a * b + d - c


# --- Levels 10-17 (D-0582, F-3686) -----------------------------------------------------------------------------
# Each is a different KIND of problem from the one below it, not bigger operands. Every generator returns
# (text, true_answer, seen): `seen` is the set of numbers a natural worked solution prints on the way (operands and
# the obvious intermediates). grade() used to accept the true answer ANYWHERE in the working (J-2988: it now reads the last number of
# the answer field only, and the re-roll stays as a belt), so a draw whose answer is
# one of its own operands or intermediates (or a tiny number that turns up in any working) would pass by accident;
# _gen_hard re-rolls those. Answers are whole numbers >= 3 (the prompt asks for digits only) and never negative
# (grade() cannot tell "3 -10" from "3" and "-10"). The checker stays grade(): no model anywhere. A generator that
# builds an invalid draw returns -1 as the answer, which the re-roll discards.
def _h10(r):                             # powers bind tighter than x, then the usual order
    if random.random() < 0.5:
        a, b, c, d = r(3, 9), r(2, 4), r(2, 9), r(2, 9)
        return (f"{a}^2 + {b}^3 - {c} × {d}", a * a + b ** 3 - c * d,
                {a, b, c, d, a * a, b ** 3, c * d, a * a + b ** 3})
    a, b, c = r(2, 9), r(2, 6), r(2, 5)
    d = random.choice([x for x in range(2, 10) if c ** 3 % x == 0])      # c^3 ÷ d divides exactly
    return (f"{a} × {b}^2 - {c}^3 ÷ {d}", a * b * b - c ** 3 // d,
            {a, b, c, d, b * b, c ** 3, c ** 3 // d, a * b * b})


def _h11(r):                             # brackets inside brackets: work from the inside out
    if random.random() < 0.5:
        a, b, c, d = r(2, 9), r(2, 9), r(2, 9), r(4, 9)
        e, f = r(1, d - 1), r(2, 20)
        i1 = d - e
        i2 = b + c * i1
        return (f"{a} × ({b} + {c} × ({d} - {e})) - {f}", a * i2 - f,
                {a, b, c, d, e, f, i1, c * i1, i2, a * i2})
    a, b, c, e = r(2, 9), r(2, 9), r(2, 9), r(2, 9)
    inner = (a + b) * c
    q = r(3, 14)
    d = inner - e * q                    # built so the bracketed value divides exactly by e
    return (f"(({a} + {b}) × {c} - {d}) ÷ {e}", q if d >= 2 else -1,
            {a, b, c, d, e, a + b, inner, inner - d})


def _h12(r):                             # remainders: a new operation, not a new size
    m = r(7, 19)
    if random.random() < 0.5:
        n = r(100, 999)
        return f"the remainder when {n} is divided by {m}", n % m, {n, m, n // m, m * (n // m)}
    a, b = r(12, 40), r(12, 40)
    return (f"the remainder when {a} × {b} is divided by {m}", (a * b) % m,
            {a, b, m, a * b, (a * b) // m})


def _h13(r):                             # find x: undo the operations; x on both sides in the second form
    x = r(3, 20)
    if random.random() < 0.5:
        a, b = r(2, 9), r(2, 30)
        c = a * x + b
        return f"x when {a}x + {b} = {c}", x, {a, b, c, c - b}
    a = r(4, 9)
    c, b = r(2, a - 1), r(2, 20)
    d = (a - c) * x - b
    return (f"x when {a}x - {b} = {c}x + {d}", x if d >= 2 else -1, {a, b, c, d, a - c, b + d})


def _h14(r):                             # a series whose NUMBER of terms is not given: find it, then sum
    a, d, n = r(2, 12), r(2, 9), r(8, 20)
    last = a + (n - 1) * d
    return (f"{a} + {a + d} + {a + 2 * d} + ... + {last}", n * (a + last) // 2,
            {a, d, n, last, a + d, a + 2 * d, n - 1})


def _h15(r):                             # counting: the number of ways to choose
    n, k = r(7, 14), r(3, 6)
    if random.random() < 0.5:
        return f"the number of ways to choose {k} things from {n}", math.comb(n, k), {n, k}
    m = r(6, 12)
    return (f"the number of ways to choose {k} things from {n}, minus the number of ways to choose 2 things from {m}",
            math.comb(n, k) - math.comb(m, 2), {n, k, m, math.comb(n, k), math.comb(m, 2)})


def _h16(r):                             # number bases; the answer is digits only, so binary comes back as a numeral
    if random.random() < 0.5:
        base = random.choice((2, 3, 5, 7))
        ln = {2: r(6, 8), 3: r(4, 5), 5: r(3, 4), 7: r(3, 4)}[base]
        digs = str(r(1, base - 1)) + "".join(str(r(0, base - 1)) for _ in range(ln - 1))
        return f"{digs} (base {base}) converted to base 10", int(digs, base), {int(digs), base}
    n = r(20, 200)
    return f"{n} written in base 2 (binary)", int(bin(n)[2:]), {n}


def _h17(r):                             # capstone: powers + brackets + remainders, or an equation with brackets
    if random.random() < 0.5:
        a, b, c, d, m = r(5, 9), r(2, 9), r(2, 9), r(2, 9), r(7, 17)
        v = a ** 3 - b * (c + d)
        return (f"the remainder when {a}^3 - {b} × ({c} + {d}) is divided by {m}", v % m if v > 0 else -1,
                {a, b, c, d, m, a ** 3, c + d, b * (c + d), v, v // m if v > 0 else 0})
    x = r(4, 25)
    a = r(4, 9)
    d, b, c = r(2, a - 1), r(2, min(6, x - 1)), r(2, 15)
    e = a * (x - b) + c - d * x
    return (f"x when {a}(x - {b}) + {c} = {d}x + {e}", x if e >= 2 else -1,
            {a, b, c, d, e, a - d, a * b, x - b, a * (x - b), a * x})


_HARD = {10: _h10, 11: _h11, 12: _h12, 13: _h13, 14: _h14, 15: _h15, 16: _h16, 17: _h17}


def _gen_hard(level: int) -> tuple[str, int]:
    """Level 10+ → (text, true_answer). Re-rolls any draw the loose grade() would pass by accident (see above)."""
    gen = _HARD[min(level, 17)]
    text, ans = "", 0
    for _ in range(500):
        text, ans, seen = gen(random.randint)
        seen = seen | {int(x) for x in re.findall(r"\d+", text)}     # every number printed in the problem itself
        if ans >= 3 and ans not in seen:
            break
    return text, ans


def generate() -> dict:
    d = _load()
    text, ans = _gen(d["level"])
    return {"text": text, "answer": ans, "level": d["level"]}


# AUTHORSHIP (founder ruling D-0583, 2026-11-02, plan social_world_school): the hints and worked examples
# returned by method_hint() are the TRAVIS BRANCH of the 2026-08-14 world-answers law (teaching reaches Du
# only from a book on his shelf or from Travis). Authored by Travis on 2026-06-22. They must NOT be
# generated or edited by a model; any new or changed hint is added through Travis. Behaviour is unchanged.
# Registry row: P-0024 (docs/guidelines/prompt_registry.md section 4, item 8).
def method_hint(level: int) -> str:
    """The METHOD to teach for this level (Travis 2026-06-22: teach him the system, don't just mark him
    wrong). A worked technique so he learns to DECOMPOSE the problem rather than guess at it in one shot —
    with the method in hand, the working is reliable. The lesson rides in the prompt (in-context CoT)."""
    if level in (3, 4, 5):                       # multiplication — partial products
        return ("Method: break the multiplication into parts and add. Split the SECOND number into its tens "
                "and its units, multiply each by the first number, then add the two results. "
                "Worked example: 47 × 36 = (47 × 30) + (47 × 6) = 1410 + 282 = 1692.")
    if level == 6:                               # division / order of operations
        return ("Method: for a ÷ b, find how many times b fits into a. For 'a + b × c', do the MULTIPLICATION "
                "first, then the addition. Worked example: 4 + 5 × 3 = 4 + 15 = 19.")
    if level == 7:                               # brackets override the usual order
        return ("Method: whatever is INSIDE the brackets always happens first, before any multiplication "
                "outside them. Worked example: (6 + 4) × 3 = 10 × 3 = 30.")
    if level == 8:                               # percentages
        return ("Method: to find P% of N, multiply N by P then divide by 100. "
                "Worked example: 20% of 145 = (145 × 20) ÷ 100 = 2900 ÷ 100 = 29.")
    if level == 9:                               # four-operation capstone
        return ("Method: work left to right through the operations, but do all the MULTIPLICATION and "
                "DIVISION first (left to right), then all the addition and subtraction (left to right). "
                "Worked example: 4 × 3 + 12 ÷ 4 − 2 = 12 + 3 − 2 = 13.")
    return ("Method: work column by column — units first, then tens — carrying or borrowing as you go. "
            "Worked example: 58 + 67 = (50 + 60) + (8 + 7) = 110 + 15 = 125.")


def grade(response: str, true_answer: int) -> bool:
    """Deterministic (never the LLM): is the LAST number in his ANSWER FIELD the true answer?
    J-2988 (F-3685): the caller passes the answer field only, no longer the working text, and the last number
    counts ('4300 + 172 = 4472' passes, '61*7=427 then adding 1 gives 428' does not), so a number that merely
    appears in the working or among the operands cannot credit a miss."""
    nums = re.findall(r"-?\d[\d,]*", response or "")
    for n in reversed(nums):
        try:
            return int(n.replace(",", "")) == true_answer
        except Exception:
            continue
    return False


def record(level: int, correct: bool) -> dict:
    """Accuracy gate (Travis 2026-06-23): advance when he sustains ADVANCE_ACCURACY over the last
    ADVANCE_WINDOW attempts — a real teacher's promotion (steady high accuracy), not 100-flawless-in-a-row.
    The window clears on level-up so each level is earned fresh; a single slip no longer erases his progress."""
    d = _load()
    w = d.get("window", [])
    w.append(1 if correct else 0)
    d["window"] = w[-ADVANCE_WINDOW:]
    if (len(d["window"]) >= ADVANCE_WINDOW
            and sum(d["window"]) / len(d["window"]) >= ADVANCE_ACCURACY
            and level < MAX_LEVEL):
        d["level"] = level + 1
        d["window"] = []                               # earn the next level fresh
    d["streak"] = (d.get("streak", 0) + 1) if correct else 0   # kept for display continuity only
    d["today_done"] = d.get("today_done", 0) + 1
    _save(d)
    return d


def feedback(text: str, true_answer: int, correct: bool) -> str:
    return f"{text} = {true_answer}" + ("  (right)" if correct else "  (I had it wrong)")


def log(problem: str, his_answer: str, true_answer: int, correct: bool, level: int,
        working: str = "", raw_answer: str | None = None, item_id: str | None = None) -> None:
    """J-2988 (F-3685): `raw_answer` (whole answer field, capped at 400) and `working_head` (first 200 chars of the
    working) are written beside the old keys so a regrade is possible (scripts/regrade_drill_log_j2988.py reads them)."""
    try:
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), "level": level, "problem": problem,
                                "his_answer": his_answer[:40], "true": true_answer,
                                "correct": bool(correct),
                                "raw_answer": (raw_answer if raw_answer is not None else his_answer or "")[:400],
                                "working_head": (working or "")[:200],
                                **({"item_id": item_id} if item_id else {})}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def due() -> bool:
    """A drill is available today (under the daily TARGET)."""
    return _load().get("today_done", 0) < DAILY_TARGET


def status() -> dict:
    d = _load()
    w = d.get("window", [])
    acc = round(sum(w) / len(w), 2) if w else 0.0
    return {"level": d["level"], "today_done": d["today_done"], "target": DAILY_TARGET,
            "window_acc": acc, "window_n": len(w), "advance_at": ADVANCE_ACCURACY,
            "advance_window": ADVANCE_WINDOW, "streak": d.get("streak", 0)}
