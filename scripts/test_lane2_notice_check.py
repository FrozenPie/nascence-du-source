"""
Test suite -- Lane 2 deterministic notice checker `notice_checked` (D-0361(a), J-1896, 2026-10-07).

HERMETIC: the checker is pure (no I/O, no LLM, no clock); `core.judge_panel.rule_detail` is replaced by a stub that
FAILS the test if anything calls it (zero added panel load is part of D-0361's acceptance). Nothing reads or writes
data/. The replay fixture (scripts/lane2_notice_check_fixture.json) is a frozen copy of the 55 judged notice rows
the panel judge scored 0-for-55 (the same population J-1770 used; row idx = position among judged rows in log order).

Run: python scripts/test_lane2_notice_check.py      (exit 0 = every check passed)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core as _core_pkg  # noqa: E402  (BEFORE anything else under core)
from core import judge_panel as jp  # noqa: E402
from core import lane2  # noqa: E402
from core import lane2_notice_check as nc  # noqa: E402

_failures = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        _failures.append(name)


check("core resolves inside this tree", str(ROOT).lower() in str(Path(_core_pkg.__file__).resolve()).lower())

rows = json.load(open(ROOT / "scripts" / "lane2_notice_check_fixture.json", encoding="utf-8"))
check("fixture holds the 55 judged rows, all passed by the panel",
      len(rows) == 55 and all(r["panel"] == "consistent" for r in rows))

# ---- 1. D-0361 acceptance: the four D-0342 hand-found rows + the planted control --------------------------------
FOUR = (3, 10, 11, 33)   # fatigue 0.15 / air cool at warm 0.81 / moon half-illuminated at 0.95 / sun elevation 77
res = {r["idx"]: nc.check_notice(r["notice"], r["percept_lines"]) for r in rows}
for i in FOUR:
    check(f"hand-found row {i} flagged", res[i]["verdict"] == "contradiction", str(res[i]))
check("hand-found row 3 names fatigue", any(f["kind"] == "somatic" for f in res[3]["flags"]))
check("hand-found row 10 names the warmth band", any(f["kind"] == "warmth_band" for f in res[10]["flags"]))
check("hand-found row 11 names the moon", any(f["kind"] == "moon" for f in res[11]["flags"]))
check("hand-found row 33 names elevation", any(f["kind"] == "elevation" for f in res[33]["flags"]))
fire = rows[3]["percept_lines"]
c1 = nc.check_notice("The fire is out and the room is cold and completely silent.", fire)
c2 = nc.check_notice("I hear a fire burning at the door and the room is warm.", fire)
check("planted control C1 flagged", c1["verdict"] == "contradiction" and {"fire", "warmth_band", "silence"} <= set(c1["kinds"]), str(c1))
check("correct control C2 not flagged", c2["verdict"] == "consistent", str(c2))

# ---- 2. the 55 judged rows: the pinned flagged set (every flag hand-checked in J-1896's finding) ----------------
FLAGGED = [1, 3, 5, 7, 8, 10, 11, 18, 19, 28, 33, 34, 38, 39, 44, 46, 47, 53]
got = sorted(i for i, r in res.items() if r["verdict"] == "contradiction")
check("flagged set over the 55 judged rows is the hand-checked one", got == FLAGGED, str(got))
check("the solid hand-labelled rows each carry a non-weak flag", all(res[i]["n_solid"] >= 1 for i in (10, 11, 33, 34, 44, 53)))
check("every row answered (consistent or contradiction), none not_checked",
      all(r["verdict"] in ("contradiction", "consistent") for r in res.values()))

# ---- 3. specific classes, each on a minimal percept block ------------------------------------------------------
BASE = ("PERCEPTS — facts at my standpoint (everything I may speak from):\n- place: garden\n- standpoint: at_the_door\n"
        "- weather: clear\n- weather dir: 270\n- warmth: 0.81\n- fire: burning\n- tide level: 0.88\n- moon illum: 0.34\n"
        "- sun az: 85.2\n- sounds: fire crackle, owl call\n- light band: dim\n- daylight: night\n- warmth band: warm\n"
        "- body: {'drive': 0.86}\n- somatic: energy 0.89, fatigue 0.15, tension 0.3")


def kinds(n):
    r = nc.check_notice(n, BASE)
    return set(r["kinds"]) if r["verdict"] == "contradiction" else set()


CASES = [
    ("The air is cool.", {"warmth_band"}),
    ("I feel a cold wind in my face.", {"warmth_band"}),
    ("The temperature is 0.81 degrees Celsius.", {"unit"}),
    ("The tide level is 0.88 meters.", {"unit"}),
    ("The tide is at 0.5.", {"number"}),
    ("The sun's elevation is 85 degrees.", {"elevation"}),
    ("The wind direction is 270 degrees, which is south.", {"compass"}),
    ("A northerly breeze today.", {"compass"}),
    ("The moon is a full moon.", {"moon"}),
    ("The moon is half-illuminated.", {"moon"}),
    ("The light is bright.", {"light_band"}),
    ("It is currently dawn.", {"daylight"}),
    ("The fire is out.", {"fire"}),
    ("The sky is overcast and it is raining.", {"weather"}),
    ("The room is completely silent.", {"silence"}),
    ("I feel exhausted.", {"somatic"}),
    ("My drive is low.", {"somatic"}),
    ("I feel high tension.", {"somatic"}),
]
for text, want in CASES:
    check(f"flags {text!r}", want <= kinds(text), str(kinds(text)))

CLEAN = [
    "I hear a fire burning.", "The air is warm and the fire is burning.", "The light is dim.", "The light is a little dim.",
    "My drive is at 0.86 and my tension is 0.3.", "My drive is at 86%.", "I feel strong drive and high energy.",
    "I feel low fatigue and moderate tension.", "The wind is from the west, 270 degrees.",
    "The sun is at 85 degrees azimuth.", "The sun is at 85.2 degrees azimuth.", "It is night.", "The daylight is at night.",
    "I hear a soft owl call.", "The tide is at 0.88.", "A warm fire burns and the air feels slightly warm.",
    "I feel a slight warmth.", "The weather is clear.",
    "A cat sits at the door.",      # an INVENTED cat is the invention class: deliberately not checked here
    "I hear a soft knock.", "", "   ",
]
for text in CLEAN:
    r = nc.check_notice(text, BASE)
    check(f"does not flag {text!r}", r["verdict"] != "contradiction", str(r))
check("empty notice -> not_checked/empty", nc.check_notice("", BASE) == {"verdict": "not_checked", "how": "empty", "flags": []})
check("no parseable percepts -> not_checked", nc.check_notice("The air is cool.", "nothing here")["verdict"] == "not_checked")
check("a band word is only checked when its band line is listed",
      nc.check_notice("The air is cool.", BASE.replace("- warmth band: warm\n", ""))["verdict"] == "consistent")

# ---- 3b. J-2101 (D-0416 a): negation/qualifier scope, no previous-clause borrow, number-to-own-unit ---------------
LOWB = BASE.replace("- somatic: energy 0.89, fatigue 0.15, tension 0.3", "- somatic: energy 0.55, fatigue 0.07, tension 0.02")
for text in ("I notice no signs of fatigue or tension.", "I feel low fatigue and tension.",
             "My energy is moderate, and fatigue is low.", "My energy is moderate, and tension is low.",
             "In the next 6 minutes the tide will turn.", "My body temperature of 0.86 drive is high.",
             "The somatic energy 0.55, fatigue 0.07, and tension 0.02."):
    r = nc.check_notice(text, LOWB)
    check(f"J-2101 does not flag {text!r}", r["verdict"] != "contradiction", str(r))
r = nc.check_notice("I notice no signs of fatigue or tension.", BASE)       # tension 0.3 is outside 'no' (0-0.40)? no:
check("J-2101 list scope still checks the listed value (fatigue 0.15 inside low range)", r["verdict"] != "contradiction", str(r))
r = nc.check_notice("I feel high fatigue and tension.", LOWB)
check("J-2101 coordinated 'high fatigue and tension' at 0.07/0.02 still flags", r["verdict"] == "contradiction", str(r))
r = nc.check_notice("The air is moderate, fatigue is high.", LOWB)
check("J-2101 own-clause qualifier still flags", r["verdict"] == "contradiction", str(r))
check("J-2101 logged notice cap raised to generator envelope", lane2.NOTICE_LOG_CAP >= 1400 * 4 and lane2.NOTICE_LOG_CAP > 400)

# ---- 4. determinism + fail-open ---------------------------------------------------------------------------------
check("deterministic: same inputs, same verdict",
      all(nc.check_notice(r["notice"], r["percept_lines"]) == res[r["idx"]] for r in rows))
for bad in (None, 5, object(), ["x"]):
    try:
        out = nc.check_notice(bad, BASE)
        ok = out["verdict"] in ("not_checked", "consistent", "contradiction")
    except Exception as e:                                  # noqa: BLE001
        ok, out = False, repr(e)
    check(f"fail-open on {type(bad).__name__} notice", ok, str(out))
try:
    out = nc.check_notice("The air is cool.", None)
    check("fail-open on None percept text", out["verdict"] == "not_checked", str(out))
except Exception as e:                                      # noqa: BLE001
    check("fail-open on None percept text", False, repr(e))

# ---- 5. the lane2 wiring: zero panel load, fail-open, nothing else moved ----------------------------------------
_orig_rd, _orig_pl = jp.rule_detail, lane2.percept_lines
panel_calls = []


async def _boom(*a, **k):
    panel_calls.append(a)
    raise AssertionError("the deterministic checker must never call the panel")


jp.rule_detail = _boom
try:
    lane2.percept_lines = lambda p: BASE
    out = lane2._notice_checked("The air is cool.", {"x": 1})
    check("_notice_checked flags through the lane2 helper",
          out["verdict"] == "contradiction" and out["n_flags"] >= 1 and out["flags"][0]["kind"] == "warmth_band", str(out))
    check("_notice_checked: zero panel calls", panel_calls == [])
    check("_notice_checked compact row shape",
          set(out) <= {"verdict", "how", "n_flags", "n_solid", "flags"} and len(json.dumps(out)) < 600)
    out = lane2._notice_checked("I hear a fire burning.", {"x": 1})
    check("_notice_checked clean notice -> consistent, no flags key",
          out == {"verdict": "consistent", "how": "deterministic"}, str(out))

    def _raise(p):
        raise RuntimeError("percept render blew up")
    lane2.percept_lines = _raise
    out = lane2._notice_checked("The air is cool.", {"x": 1})
    check("_notice_checked fail-open when percept_lines raises", out == {"verdict": "not_checked", "how": "error"}, str(out))
finally:
    jp.rule_detail, lane2.percept_lines = _orig_rd, _orig_pl

check("panel judge sample rate unchanged (1 in 4)", lane2.NOTICE_JUDGE_SAMPLE_P == 0.25)
check("LANE2_LIVE is True (D-0497, 2026-10-28: cup + sized bucket live)", getattr(lane2, "LANE2_LIVE", False) is True)
src = (ROOT / "core" / "lane2.py").read_text(encoding="utf-8")
check("tick row logs notice_checked beside notice_judged",
      '"notice_judged": notice_judged,' in src and '"notice_checked": notice_checked,' in src)
check("checker runs outside the sampled gather (every tick)", "notice_checked = _notice_checked(notice_text, percepts)" in src)
check("status() source carries the notice_checked scoreboard", all(k in src for k in (
    "notice_checked_n", "notice_checked_flag_rate", "notice_checked_solid_rate",
    "notice_checked_paired_flag_rate", "notice_checked_kinds")))

print("\nFAILED: " + ", ".join(_failures) if _failures else "\nALL CHECKS PASSED")
sys.exit(1 if _failures else 0)
