"""
Nascence — Task-Constraint Effector (Phase: Error Separation, slice 2 — the FIRST effector)
===========================================================================================
The conflict-trace (2026-06-10, first live session) proved the execution gap: dissonance named
Du's failure verbatim ("describing methodology vs. providing the solution") and had no authority;
the Critic stands down on direct requests — precisely the task cycles. The architecture could
notice and could not act. This module is the first organ empowered to act.

Discipline (from the founder's veto framework + the charter):
  - JURISDICTION-BOUNDED: only constraints that are EXPLICIT and DETERMINISTICALLY checkable in
    the human's input — v1: digit-arithmetic to compute, and a stated minimum word count. Never
    style, never meaning, never identity. An unparseable task is out of jurisdiction → silence.
  - BIND, DON'T SLAM: on an unmet constraint the effector does NOT suppress or terse-ify (forcing
    "only the number" is exactly what broke bare-qwen arithmetic). It re-runs the Voice ONCE with
    the constraint *named* and room to show working. It never hands over the answer — the
    directive says "derive it step by step and state the final number", not "say 27".
  - FAIL OPEN: any internal error → behave as if no constraint existed. One retry maximum.
  - HONEST RECORD: a constraint still unmet after the retry becomes a firewalled error record
    (deterministic ground-truth evidence, charter-admissible) — never an identity tension.

The conflict-trace `acted` column is the before/after instrument for this slice: it has been
structurally 0 for every truth-signal; this effector is what flips it.
"""
from __future__ import annotations
import ast
import re

# ---- jurisdiction 1: digit arithmetic ---------------------------------------------------------

# verbal → symbolic operators (digits stay digits; word-numbers are v2, see the spec)
_VERBAL_OPS = [
    (re.compile(r"\bmultiplied\s+by\b", re.I), "*"),
    (re.compile(r"\btimes\b", re.I), "*"),
    (re.compile(r"(?<=\d)\s*[x×]\s*(?=\d)"), "*"),
    (re.compile(r"\bplus\b", re.I), "+"),
    (re.compile(r"\bminus\b", re.I), "-"),
    (re.compile(r"\bdivided\s+by\b", re.I), "/"),
]
# a candidate expression: numbers/parens joined by arithmetic operators
_EXPR = re.compile(r"\(?\s*\d+(?:\.\d+)?(?:\s*[\+\-\*\/]\s*\(?\s*\d+(?:\.\d+)?\s*\)?)+\s*\)?")
# the input must actually ASK for computation — otherwise numbers in prose are not a constraint
_COMPUTE_INTENT = re.compile(
    r"what is|what's|compute|calculate|work (this |it )?out|solve|step by step|"
    r"final (number|answer|result)|equals?\b|=\s*\?", re.I)

# ---- jurisdiction 2: explicit minimum word count ----------------------------------------------
_MIN_WORDS = re.compile(r"at least (\d{2,5}) words", re.I)
_WORDCOUNT_TOLERANCE = 0.85   # prose "at least 300 words" satisfied at 255+ — intent, not pedantry

_ALLOWED_NODES = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
                  ast.Add, ast.Sub, ast.Mult, ast.Div, ast.USub)

_ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
         "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
         "eighteen", "nineteen"]
_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]


def _safe_eval(expr: str) -> float | None:
    """Evaluate a pure-arithmetic expression. Whitelisted AST nodes only — never eval()."""
    try:
        tree = ast.parse(expr, mode="eval")
        for node in ast.walk(tree):
            if not isinstance(node, _ALLOWED_NODES):
                return None
            if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float)):
                return None
        return float(eval(compile(tree, "<constraint>", "eval"), {"__builtins__": {}}, {}))
    except Exception:
        return None


def _int_words(n: int) -> list[str]:
    """English word forms for 0..999 (the forms Du actually answers in: 'twenty-seven')."""
    if not 0 <= n <= 999:
        return []
    if n < 20:
        return [_ONES[n]]
    if n < 100:
        t, o = divmod(n, 10)
        if o == 0:
            return [_TENS[t]]
        return [f"{_TENS[t]}-{_ONES[o]}", f"{_TENS[t]} {_ONES[o]}"]
    h, rest = divmod(n, 100)
    head = f"{_ONES[h]} hundred"
    if rest == 0:
        return [head]
    return [f"{head} and {w}" for w in _int_words(rest)] + [f"{head} {w}" for w in _int_words(rest)]


def _answer_forms(value: float) -> list[str]:
    """Acceptable surface forms of the expected result — digits and English words."""
    forms = []
    if value == int(value):
        iv = int(value)
        forms.append(str(iv))
        forms += _int_words(abs(iv)) if iv >= 0 else []
    else:
        forms.append(f"{value:g}")
    return forms


def _contains_answer(output: str, value: float) -> bool:
    low = output.lower()
    for form in _answer_forms(value):
        if re.search(r"(?<![\d\w.])" + re.escape(form.lower()) + r"(?![\d\w])", low):
            return True
    return False


# ---- public API --------------------------------------------------------------------------------

def extract(raw_input: str) -> dict | None:
    """Find ONE explicit, deterministically checkable constraint in the human's input, or None.
    Out-of-jurisdiction inputs (no explicit checkable demand) return None — the effector stays
    silent rather than guessing what the task 'really' wanted."""
    text = raw_input or ""

    m = _MIN_WORDS.search(text)
    if m:
        n = int(m.group(1))
        return {"kind": "min_words", "min_words": n,
                "why": f"input demands at least {n} words",
                "directive": (f"The response must be a full piece of at least {n} words — "
                              "complete the task at that length, in your own voice.")}

    norm = text
    for rx, sym in _VERBAL_OPS:
        norm = rx.sub(f" {sym} ", norm)
    if _COMPUTE_INTENT.search(text) or _COMPUTE_INTENT.search(norm):
        exprs = [e.strip() for e in _EXPR.findall(norm)]
        # take the LAST candidate (the question is usually at the end), longest on ties
        exprs.sort(key=len)
        for expr in reversed(exprs):
            value = _safe_eval(expr)
            if value is not None:
                return {"kind": "arithmetic", "expression": expr, "expected": value,
                        "why": f"input asks to compute {expr} (= {value:g})",
                        # v1.1 recompute-license (2026-06-10 live finding): the first live retry
                        # failed because the wrong figure lived UPSTREAM in the synthesis and the
                        # Voice faithfully re-rendered it — the retry re-ran the mouth while the
                        # error sat in the mind. The directive now explicitly licenses the Voice
                        # to distrust and re-derive the number itself.
                        "directive": ("The internal thought you are rendering may contain a "
                                      "WRONG figure — do not trust any number already in it. "
                                      "Re-derive the calculation that was asked yourself, "
                                      "carefully, step by step, then state the final number "
                                      "plainly. Keep your voice, but the number must be there "
                                      "and must be correct.")}
    return None


def check(constraint: dict, output: str) -> tuple[bool, str]:
    """Deterministically test the output against the constraint."""
    if not output:
        return False, "empty output"
    if constraint["kind"] == "arithmetic":
        if _contains_answer(output, constraint["expected"]):
            return True, "expected result present"
        return False, (f"expected result {constraint['expected']:g} of "
                       f"{constraint['expression']} not found in response")
    if constraint["kind"] == "min_words":
        n = len(output.split())
        need = int(constraint["min_words"] * _WORDCOUNT_TOLERANCE)
        if n >= need:
            return True, f"{n} words (≥{need})"
        return False, f"only {n} words of the {constraint['min_words']} asked for"
    return True, "unknown constraint kind — fail open"
