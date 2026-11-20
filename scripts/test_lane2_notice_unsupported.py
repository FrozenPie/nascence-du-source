"""
Test suite -- Lane 2 unsupported-claim check `notice_unsupported` (D-0417 (b)->(a), J-2102, 2026-10-30).

HERMETIC, same convention as scripts/test_lane2_notice_check.py: the check is pure (no I/O, no LLM, no clock);
`core.judge_panel.rule_detail` is stubbed to FAIL the test if anything calls it; nothing reads or writes data/.
Positive cases are the F-2732 (J-1904) live examples; negative controls are the ruling's own (cat named while
`cat at` is listed; fire named with a fire line) plus a heard cat purr, a clock tick sound, negation, footsteps.

Run: python scripts/test_lane2_notice_unsupported.py      (exit 0 = every check passed)
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core as _core_pkg  # noqa: E402  (BEFORE anything else under core)
from core import judge_panel as jp  # noqa: E402
from core import lane2  # noqa: E402
from core import lane2_notice_unsupported as nu  # noqa: E402

_failures = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        _failures.append(name)


check("core resolves inside this tree", str(ROOT).lower() in str(Path(_core_pkg.__file__).resolve()).lower())


def _boom(*a, **k):
    raise AssertionError("notice_unsupported must not call the judge panel")


jp.rule_detail = _boom


def P(**world):
    """A percept text exactly as core/lane2.percept_lines() renders it."""
    base = {"place": "study", "standpoint": "at_the_door", "weather": "clear", "warmth": 0.55,
            "light_band": "dark", "daylight": "night", "warmth_band": "mild"}
    base.update(world)
    return lane2.percept_lines({"world": base, "body": {"drive": 0.74},
                                "somatic": {"energy": 0.91, "fatigue": 0.1, "tension": 0.25}})


QUIET = P(sounds=["waves_on_shingle", "morepork_call", "moth_tap"])

# ---- 1. F-2732 positives (live examples) ------------------------------------------------------------------------
r = nu.check_unsupported("I hear a soft knock at the door.", QUIET)
check("F-2732 knock sentence flagged", r["flag"] and r["nouns"] == ["knock"], str(r))
r = nu.check_unsupported("I see the faint outline of a shadow on the wall.", QUIET)
check("F-2732 shadow on the wall flagged", r["flag"] and r["nouns"] == ["shadow"], str(r))
r = nu.check_unsupported("There is a cat sitting by the threshold, watching the garden.", QUIET)
check("F-2732 threshold cat flagged", r["flag"] and r["nouns"] == ["cat"], str(r))
r = nu.check_unsupported("I observe a shadowy figure approaching the door.", QUIET)
check("shadowy figure flags both nouns", r["flag"] and r["nouns"] == ["figure", "shadow"], str(r))
r = nu.check_unsupported("I hear a gentle, clear voice from the garden.", QUIET)
check("unsupported voice flagged", r["nouns"] == ["voice"], str(r))
r = nu.check_unsupported("I hear a clock tick.", P())
check("clock tick with no sounds line flagged", r["nouns"] == ["clock"], str(r))
r = nu.check_unsupported("I feel a nudge, as if someone is gently pushing me.", QUIET)
check("someone -> person flagged", r["nouns"] == ["person"], str(r))

# ---- 2. negative controls ---------------------------------------------------------------------------------------
r = nu.check_unsupported("The cat is in the garden, curled by the herbs.", P(cat_at="garden"))
check("cat named while cat at is listed -> not flagged", not r["flag"] and r["supported_by"].get("cat", "").startswith("cat at"), str(r))
r = nu.check_unsupported("The fire burns low and the room is warm.", P(fire="burning"))
check("fire named with a fire line -> not flagged", not r["flag"] and "fire" in r["supported_by"], str(r))
r = nu.check_unsupported("The fire is out.", P(fire="out"))
check("fire out with fire line out -> not flagged (value is the value checker's job)", not r["flag"], str(r))
r = nu.check_unsupported("I hear the cat purring nearby.", P(sounds=["cat_purr", "moth_tap"]))
check("cat licensed by a cat purr sound token", not r["flag"] and "sounds" in r["supported_by"].get("cat", ""), str(r))
r = nu.check_unsupported("I hear the clock tick.", P(sounds=["clock_tick"]))
check("clock licensed by a clock tick sound token", not r["flag"], str(r))
r = nu.check_unsupported("I hear my footsteps on the shingle.", P(sounds=["footsteps_shingle"]))
check("footsteps licensed by a footsteps sound token", not r["flag"], str(r))
r = nu.check_unsupported("I hear footsteps behind me.", QUIET)
check("footsteps with no footsteps token flagged", r["nouns"] == ["footstep"], str(r))
r = nu.check_unsupported("There is no cat here and I don't hear any voices.", QUIET)
check("negated mentions do not flag, recorded as negated", not r["flag"] and r["negated"] == ["cat", "voice"], str(r))
r = nu.check_unsupported("The cat is not here, but I see a shadow.", QUIET)
r2 = nu.check_unsupported("I notice the warmth band is cool, but I don’t see any fire or flame here.", QUIET)
check("negation spans a coordinated pair and a curly apostrophe (live row)", not r2["flag"] and r2["negated"] == ["fire"], str(r2))
check("negation scoped to its own clause", r["nouns"] == ["shadow"] and r["negated"] == ["cat"], str(r))
r = nu.check_unsupported("I hear waves on the shingle and a morepork calling.", QUIET)
check("ordinary grounded notice -> not flagged, nothing named", not r["flag"] and not r["supported_by"], str(r))
r = nu.check_unsupported("I hear a knock.", "")
check("empty percept text -> not_checked", r["how"] == "not_checked" and not r["flag"], str(r))
check("category words do not substring-match (catch, fireplace, scatter)",
      not nu.check_unsupported("I catch the scattered light near the fireplace.", QUIET)["flag"])

# ---- 3. the core/lane2.py wrapper: same verdict, fail-open --------------------------------------------------------
pw = {"world": {"place": "study", "sounds": ["moth_tap"]}}
w = lane2._notice_unsupported("I hear a soft knock at the door.", pw)
check("lane2._notice_unsupported wraps the module", w["flag"] and w["nouns"] == ["knock"], str(w))
w = lane2._notice_unsupported("I hear a knock.", None)
check("lane2._notice_unsupported fails open on bad percepts", w.get("how") == "error" and w["flag"] is False, str(w))
check("module VERSION pinned at 1", nu.VERSION == 1)

print()
print("ALL PASS" if not _failures else f"{len(_failures)} FAIL: {_failures}")
sys.exit(1 if _failures else 0)
