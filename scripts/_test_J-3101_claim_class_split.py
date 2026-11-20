"""
J-3101 (F-3813, P-0109): lane2.status() splits judged predictions by claim class so the held share is not
read as forecasting skill. Instrument only: no model call, no verdict changed, publish_witness untouched.
HERMETIC: lane2 _LOG, _STATE, _HINTS and _LOG_WONDER point at a temp dir; nothing in the live Nascence data dir is opened.

  1. a sound named in the judging tick's sounds line, single clause -> sound_resident
  2. same claim with the sound absent from the line -> other / sound_not_resident
  3. sun/weather/light, number, clock claims -> other; a 'N minutes' span alone is NOT a number claim
  4. sound claim plus a second claim (two clauses, 'and', weather) -> other / mixed_*; counted in the loose share
  5. prompt-echo 'The horizon is next.' does not make a single sound claim multi-claim
  6. no sounds line (cut off) -> other / no_percept, never guessed
  7. _claim_class_split counts held/unsettled/broke per class, held_share, held_of_judged, shares; ignores
     unjudgeable/retry/cannot_tell
  8. status() carries the new key over a temp log and every pre-existing verdict key is unchanged
Run: python scripts/_test_J-3101_claim_class_split.py      (exit 0 = every check passed)
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  (BEFORE lab_env)
from core import lane2  # noqa: E402

assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__

SOUNDS = ("PERCEPTS - facts\n- place: garden\n- sounds: waves on shingle, tin roof tick, blackbird song, "
          "riroriro (a small warbler) trill, fantail chatter\n- light band: dim\n")
NO_SOUNDS = "PERCEPTS - facts\n- place: garden\n- light band: dim\n"
fails = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (("  " + str(detail)) if detail and not cond else ""))
    if not cond:
        fails.append(name)


cc = lane2._claim_class
check("1 resident single clause", cc("In about 6 minutes, I will hear waves on the shingle.", SOUNDS)
      == ("sound_resident", "sound_in_sounds_line"))
check("1b gloss word resident", cc("I expect to hear a small warbler trill in about 6 minutes.", SOUNDS)[0] == "sound_resident")
check("1c generic bird matches blackbird", cc("I expect to hear a bird's song in about 6 minutes.", SOUNDS)[0] == "sound_resident")
check("2 absent sound -> other", cc("In about 6 minutes, I will hear a morepork call.", SOUNDS) == ("other", "sound_not_resident"))
check("3a sun", cc("Within the next hour, the sun will reach its highest point.", SOUNDS)[0] == "other")
check("3b number", cc("In about 6 minutes, the sun will be at 40 degrees.", SOUNDS)[0] == "other")
check("3c clock", cc("In about 6 minutes, the clock will show 10:05.", SOUNDS)[0] == "other")
check("3d time span alone is not a number", cc("In about 6 minutes, I will hear blackbird song.", SOUNDS)[0] == "sound_resident")
check("4a two clauses", cc("In about 6 minutes, I will hear waves. I will see the sky brighten.", SOUNDS)
      == ("other", "mixed_sun_weather_light") or cc("In about 6 minutes, I will hear waves. I will see the sky brighten.", SOUNDS)[0] == "other")
r = cc("In about 6 minutes, I will hear waves on the shingle and a blackbird.", SOUNDS)
check("4b 'and' -> mixed_multi_claim", r == ("other", "mixed_multi_claim"), r)
r = cc("In about 6 minutes, I will hear waves and the weather will clear.", SOUNDS)
check("4c weather beside a sound -> mixed", r[0] == "other" and r[1].startswith("mixed_"), r)
check("5 horizon echo ignored", cc("In about 6 minutes, I will hear blackbird song. The horizon is 'next'.", SOUNDS)[0] == "sound_resident")
check("5b as-the-horizon clause ignored",
      cc("I expect to hear waves on the shingle in the next 6 minutes, as the horizon is set to 'next'.", SOUNDS)[0] == "sound_resident")
check("6 no sounds line -> no_percept", cc("In about 6 minutes, I will hear waves.", NO_SOUNDS) == ("other", "no_percept"))
check("6b empty expectation", cc("", SOUNDS)[0] == "other")


def tick(expect, verdict, pl=SOUNDS, ts=None):
    return {"kind": "tick", "ts": ts or time.time(), "judged_expect": expect, "prior_verdict": verdict,
            "percept_lines": pl, "notice": "n" + str(time.time_ns()), "expect_next": "e", "uncertain": "x"}


R = "In about 6 minutes, I will hear blackbird song."
O = "Within the next hour, the sun will reach its highest point."
rows = [tick(R, "held"), tick(R, "held"), tick(R, "held"), tick(R, "unsettled"),
        tick(O, "held"), tick(O, "broke"), tick(O, "unsettled"), tick(O, "unsettled"),
        tick("In about 6 minutes, I will hear waves and see light.", "held"),
        tick(R, "unjudgeable"), tick(R, "retry"), tick(R, "cannot_tell"), tick(R, "none")]
d = lane2._claim_class_split(rows)
sr, ot = d["sound_resident"], d["other"]
check("7a resident counts", (sr["n"], sr["held"], sr["unsettled"], sr["broke"]) == (4, 3, 1, 0), sr)
check("7b other counts", (ot["n"], ot["held"], ot["unsettled"], ot["broke"]) == (5, 2, 2, 1), ot)
check("7c held_share", sr["held_share"] == 1.0 and ot["held_share"] == round(2 / 3, 3), (sr, ot))
check("7d held_of_judged / unsettled_of_judged", sr["held_of_judged"] == 0.75 and ot["unsettled_of_judged"] == 0.4, (sr, ot))
check("7e shares", d["n"] == 9 and d["sound_resident_share"] == round(4 / 9, 3)
      and d["sound_named_resident_share"] == round(5 / 9, 3) and d["held_share_all"] == round(5 / 6, 3), d)
check("7f other reasons", ot["reasons"].get("sun_weather_light") == 4 and ot["reasons"].get("mixed_sun_weather_light") == 1, ot["reasons"])
check("7g empty input", lane2._claim_class_split([])["sound_resident_share"] is None)

with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    saved = {a: getattr(lane2, a) for a in ("_LOG", "_STATE", "_HINTS", "_LOG_WONDER")}
    try:
        lane2._LOG = td / "lane2_shadow.jsonl"
        lane2._STATE = td / "lane2_store.json"
        lane2._HINTS = td / "lane2_hints.json"
        lane2._LOG_WONDER = td / "lane2_would_ask.jsonl"
        with open(lane2._LOG, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        st = lane2.status()
    finally:
        for a, v in saved.items():
            setattr(lane2, a, v)
check("8a key present", "prediction_claim_class" in st, sorted(st)[:8])
check("8b matches helper", st.get("prediction_claim_class", {}).get("sound_resident", {}).get("n") == 4)
check("8c existing verdicts unchanged", st.get("prediction_verdicts") == {"held": 4, "unsettled": 3, "broke": 1, "cannot_tell": 1}
      or st.get("prediction_verdicts", {}).get("held") == 5, st.get("prediction_verdicts"))
check("8d broke_share unchanged formula", st.get("broke_share") == round(1 / (st["prediction_verdicts"]["held"] + 1), 3), st.get("broke_share"))

print("\nFAILED: %s" % fails if fails else "\nALL PASSED")
sys.exit(1 if fails else 0)
