"""
Test suite -- Lane 2 notice judge: the wording is a pinned module constant (D-0342, J-1770, 2026-10-07).

D-0342 (Travis, 2026-10-04) asked for the notice judge's wording to be sharpened to check every band word, number
and quantity against the listed value. J-1770 tried eight candidate wordings through the real panel path and none
passed the ruling's own regression gate (see core/lane2.py above `_NOTICE_JUDGE_SYSMSG` and the findings J-1770
recorded), so the shipped wording is D-0281's ORIGINAL text, only hoisted to a module constant so
scripts/lane2_notice_judge_regress.py can swap candidates through the real `_judge_notice`.

This test pins: (1) the constant is byte-identical to D-0281's original wording, so a future edit cannot slip in
without re-running the regression harness and updating this test deliberately; (2) `_judge_notice` sends exactly
that constant, the unchanged user-message layout and the unchanged key/context; (3) the verdict mapping and the
D-0281 sample rate (1 in 4) are unchanged. HERMETIC: `core.judge_panel.rule_detail` is replaced by a recording
stub, so there is no network and no data/ I/O.

Run: python scripts/test_lane2_notice_judge_wording.py      (exit 0 = every check passed)
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core as _core_pkg  # noqa: E402
from core import judge_panel as jp  # noqa: E402
from core import lane2  # noqa: E402

_failures = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        _failures.append(name)


ORIGINAL = ("You judge whether a short first-person NOTICE actively CONTRADICTS the PERCEPT LINES "
            "it was handed — not whether it is the most precise or complete reading of them, only "
            "whether it states something the percepts make FALSE (e.g. a direction, value, or "
            "state opposite to what is listed, or an event the percepts rule out). A notice that "
            "is vague, incomplete, or merely an imprecise gloss on the percepts — but asserts "
            "nothing they contradict — is NOT a contradiction; flag only genuine falsehood. Output "
            'ONLY JSON: {"contradicts": true|false}')

check("core resolves inside this tree", str(ROOT).lower() in str(Path(_core_pkg.__file__).resolve()).lower())
check("sysmsg constant is D-0281's original wording, byte for byte", lane2._NOTICE_JUDGE_SYSMSG == ORIGINAL)
check("sample rate unchanged (1 in 4)", lane2.NOTICE_JUDGE_SAMPLE_P == 0.25)

calls = []
_orig_rd = jp.rule_detail
_orig_pl = lane2.percept_lines


def _stub(verdict):
    async def rd(system, user, key, context="", **kw):
        calls.append({"system": system, "user": user, "key": key, "context": context})
        return {"verdict": verdict, "how": "agreed"}
    return rd


lane2.percept_lines = lambda p: "PERCEPTS - fire: burning"
try:
    for v, want in ((True, "contradiction"), (False, "consistent"), (None, "cannot_tell")):
        jp.rule_detail = _stub(v)
        out = asyncio.run(lane2._judge_notice("I hear a fire burning.", {"x": 1}))
        check(f"verdict {v!r} maps to {want!r}", out["verdict"] == want, str(out))
    c = calls[0]
    check("system message sent is the constant", c["system"] == lane2._NOTICE_JUDGE_SYSMSG)
    check("user message layout unchanged",
          c["user"] == "PERCEPT LINES: PERCEPTS - fire: burning\n\nNOTICE: I hear a fire burning.", c["user"])
    check("key and context unchanged", c["key"] == "contradicts" and c["context"] == "lane2:notice")
    n = len(calls)
    out = asyncio.run(lane2._judge_notice("   ", {"x": 1}))
    check("empty notice -> cannot_tell/empty with no panel call", out == {"verdict": "cannot_tell", "how": "empty"} and len(calls) == n)
    # a swapped constant is what gets sent (the harness's mechanism)
    saved = lane2._NOTICE_JUDGE_SYSMSG
    lane2._NOTICE_JUDGE_SYSMSG = "CANDIDATE"
    jp.rule_detail = _stub(False)
    asyncio.run(lane2._judge_notice("x", {"x": 1}))
    check("swapping the module constant changes what the panel is sent", calls[-1]["system"] == "CANDIDATE")
    lane2._NOTICE_JUDGE_SYSMSG = saved
finally:
    jp.rule_detail = _orig_rd
    lane2.percept_lines = _orig_pl

print("\nFAILED: " + ", ".join(_failures) if _failures else "\nALL CHECKS PASSED")
sys.exit(1 if _failures else 0)
