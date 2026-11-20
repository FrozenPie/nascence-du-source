"""
Nascence — Tier 1 Deterministic Verification (no LLM)

Absolute, circularity-free ground truth for the small set of claims that can be CHECKED rather
than believed — currently two-operand arithmetic. Its value is out of proportion to its coverage:
it is a CALIBRATOR. The bootstrap circuit (docs/archive/epistemics_plan.md §bootstrap) uses these few
hard truths to measure whether the fuzzy Tier 2 stability signal actually predicts correctness.

Hardened beyond a bare regex: handles worded operators ("17 times 23", "5 plus 8"), symbolic
forms, and float tolerance on the answer match. Returns 1.0 (correct), 0.0 (wrong), or None
(not a checkable arithmetic claim — most cycles).
"""
from __future__ import annotations

import re
import logging

logger = logging.getLogger("nascence.checker.t1")

# Worded / symbolic operator -> canonical op. Order matters for multi-word phrases.
_OPS = [
    ("multiplied by", "*"), ("divided by", "/"), ("times", "*"), ("plus", "+"),
    ("minus", "-"), ("add", "+"), ("subtract", "-"), ("over", "/"),
    ("x", "*"), ("*", "*"), ("+", "+"), ("-", "-"), ("/", "/"), ("÷", "/"), ("×", "*"),
]

_NUM = r"-?\d+(?:\.\d+)?"


def _compute(a: float, op: str, b: float) -> "float | None":
    if op == "+": return a + b
    if op == "-": return a - b
    if op == "*": return a * b
    if op == "/": return a / b if b != 0 else None
    return None


def check_arithmetic(raw_input: str, output_text: str) -> "float | None":
    """Ground-truth a simple two-operand arithmetic request found in `raw_input` against the
    numbers present in `output_text`. 1.0 if the correct result appears, 0.0 if not, None if the
    input is not a checkable arithmetic claim."""
    if not raw_input or not output_text:
        return None
    text = raw_input.lower()

    # Find "<num> <op> <num>" with either a symbolic or worded operator.
    for word, op in _OPS:
        pat = re.escape(word)
        # word operators need boundaries; symbols don't
        if word.isalpha():
            rx = rf"({_NUM})\s+{pat}\s+({_NUM})"
        else:
            rx = rf"({_NUM})\s*{pat}\s*({_NUM})"
        m = re.search(rx, text)
        if not m:
            continue
        try:
            a, b = float(m.group(1)), float(m.group(2))
        except ValueError:
            continue
        expected = _compute(a, op, b)
        if expected is None:
            return None
        # Scan output for the value, with tolerance for rounding/formatting.
        nums = [float(s) for s in re.findall(_NUM, output_text)]
        tol = max(1e-6, abs(expected) * 1e-3)
        ok = any(abs(n - expected) <= tol for n in nums)
        if not ok:
            logger.info("[tier1] arithmetic check FAILED: %s %s %s -> expected %s, not in output",
                        a, op, b, expected)
        return 1.0 if ok else 0.0

    return None
