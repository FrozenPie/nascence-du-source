"""J-3099 (F-3815, P-0109): Lane 2 `_judge_prior` tells the judges when the expectation was made.

HERMETIC: every judge call (core.judge_panel.rule_detail) is a recording stub, no hub is contacted, no data path is
touched (a snapshot of the live data files is compared before and after).  The REAL `_judge_prior`, `_made_line`,
`_fmt_span`, `_prediction_age_s` run.

Run from the worktree: python scripts/_test_J3099_judge_prior_made_line.py   (exit 0 = every check passed)
"""
from __future__ import annotations

import asyncio
import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core as _core_pkg  # noqa: E402  (core BEFORE anything that touches lab_env)
from core import judge_panel as jp  # noqa: E402
from core import lane2  # noqa: E402

assert str(Path(lane2.__file__).resolve()).startswith(str(ROOT)), lane2.__file__

_WATCH = [Path("C:/Nascence/data") / n for n in ("lane2_shadow.jsonl", "lane2_store.json", "judge_panel_log.jsonl")]


def _snap():
    out = {}
    for p in _WATCH:
        try:
            st = p.stat()
            out[str(p)] = (st.st_size, st.st_mtime)
        except OSError:
            out[str(p)] = None
    return out


FAILS = []


def check(name, cond, detail=""):
    print(("ok   " if cond else "FAIL ") + name + (f"  [{detail}]" if (detail and not cond) else ""))
    if not cond:
        FAILS.append(name)


PERCEPTS = {"world": {"place": "garden"}}
lane2.percept_lines = lambda p: "PERCEPTS - observed text"      # constant observation, no gather
EXPECT = "Within the next hour, the sun will reach its highest point."


def run_prior(**kw):
    """Calls the real _judge_prior with a recording stub panel: held -> False, contradicted -> True (so both asks fire)."""
    calls = []

    async def stub(system, user, key, context="", tiebreak_url=None, **k):
        calls.append({"system": system, "user": user, "key": key, "context": context})
        return {"verdict": (key == "contradicted"), "how": "agreed", "why": "stub"}

    real = jp.rule_detail
    jp.rule_detail = stub
    try:
        res = asyncio.run(lane2._judge_prior(EXPECT, PERCEPTS, **kw))
    finally:
        jp.rule_detail = real
    return res, calls


def main():
    before = _snap()
    saved_flag = lane2.JUDGE_MADE_LINE

    # 0. the shipped default is OFF (replay unread)
    check("default JUDGE_MADE_LINE is False", saved_flag is False)

    # 1. pure helpers
    check("fmt 350 s -> 6 minutes", lane2._fmt_span(349.8) == "6 minutes", lane2._fmt_span(349.8))
    check("fmt 30 s -> 1 minute", lane2._fmt_span(30) == "1 minute")
    check("fmt 3866 s -> 64 minutes", lane2._fmt_span(3866.6) == "64 minutes", lane2._fmt_span(3866.6))
    check("fmt 60318 s -> 16.8 hours", lane2._fmt_span(60317.6) == "16.8 hours", lane2._fmt_span(60317.6))
    check("fmt 12 h -> 12 hours", lane2._fmt_span(12 * 3600) == "12 hours", lane2._fmt_span(12 * 3600))
    check("made_line empty when nothing known", lane2._made_line(None, None, None) == "")
    ml = lane2._made_line(349.8, "next", "garden")
    check("made_line full shape", ml == "MADE: about 6 minutes ago, in the garden, stated horizon 'next' "
                                        "(due after about 2 minutes)", ml)
    check("made_line partial (age only)", lane2._made_line(120, None, None) == "MADE: about 2 minutes ago")
    check("made_line never raises on junk", lane2._made_line("x", "hour", None) == "")
    check("age_s from store rec", lane2._prediction_age_s({"ts": 100.0}, 449.8) == 349.8)
    check("age_s None without ts", lane2._prediction_age_s({}, 5.0) is None)

    # 2. OLD strings captured with the flag off (and keywords passed: flag off ignores them)
    lane2.JUDGE_MADE_LINE = False
    res_off, c_off = run_prior(age_s=349.8, horizon="next", pred_place="garden")
    res_plain, c_plain = run_prior()
    check("flag off: both asks fired", len(c_off) == 2 and [c["key"] for c in c_off] == ["held", "contradicted"])
    check("flag off + keywords == no keywords (byte-identical, all 4 strings)",
          [(c["system"], c["user"]) for c in c_off] == [(c["system"], c["user"]) for c in c_plain])
    golden_usr = f"PRIOR EXPECTATION: {EXPECT[:200]}\n\nWHAT IS OBSERVED NOW: PERCEPTS - observed text\n\nDid it hold?"
    golden_usr2 = (f"PRIOR EXPECTATION: {EXPECT[:200]}\n\nWHAT IS OBSERVED NOW: PERCEPTS - observed text\n\n"
                   "Does it definitely contradict the expectation?")
    check("flag off: held user prompt is the pre-J-3099 string", c_off[0]["user"] == golden_usr, repr(c_off[0]["user"]))
    check("flag off: contradicted user prompt is the pre-J-3099 string", c_off[1]["user"] == golden_usr2)
    golden_sys2 = ("You judge whether what is now observed DEFINITELY CONTRADICTS a prior "
                   "expectation about the immediate physical world \u2014 not merely fails to confirm "
                   "it. If the observation is silent on the point, ambiguous, or simply consistent "
                   "with the expectation not having happened YET, answer false: only answer true "
                   "if the observation rules the expectation out. Output ONLY JSON: "
                   "{\"contradicted\": true|false, \"why\": \"<one short clause>\"}")
    check("flag off: contradicted system message is the pre-J-3099 string", c_off[1]["system"] == golden_sys2)
    check("flag off: verdict shape unchanged", res_off["verdict"] == "broke" and res_off["why"] == "stub")

    # 3. flag ON, keywords present
    lane2.JUDGE_MADE_LINE = True
    res_on, c_on = run_prior(age_s=3866.6, horizon="hour", pred_place="garden")
    mline = "MADE: about 64 minutes ago, in the garden, stated horizon 'hour' (due after about 60 minutes)"
    check("flag on: MADE line in held user prompt", mline in c_on[0]["user"], c_on[0]["user"])
    check("flag on: MADE line in contradicted user prompt", mline in c_on[1]["user"], c_on[1]["user"])
    check("flag on: MADE sits between expectation and observation",
          c_on[0]["user"].index("PRIOR EXPECTATION") < c_on[0]["user"].index("MADE:")
          < c_on[0]["user"].index("WHAT IS OBSERVED NOW"))
    check("flag on: user prompt is the old one plus exactly the MADE block",
          c_on[0]["user"] == golden_usr.replace("WHAT IS OBSERVED NOW", mline + "\n\nWHAT IS OBSERVED NOW", 1))
    check("flag on: tolerance sentence in the contradicted system message only",
          lane2._MADE_TOLERANCE_SENTENCE in c_on[1]["system"] and lane2._MADE_TOLERANCE_SENTENCE not in c_on[0]["system"])
    check("flag on: held system message unchanged", c_on[0]["system"] == c_off[0]["system"])
    check("flag on: tolerance sentence names 1 degree of azimuth and 2 minutes of clock",
          "1 degree of azimuth" in c_on[1]["system"] and "2 minutes of clock" in c_on[1]["system"])
    check("flag on: contradicted system keeps the old text around the new sentence",
          c_on[1]["system"] == golden_sys2.replace("Output ONLY JSON: ",
                                                   lane2._MADE_TOLERANCE_SENTENCE + "Output ONLY JSON: ", 1))
    check("flag on: no Lane 1 text in the new line (only age, place, horizon)",
          "weather" not in mline and "standpoint" not in mline)
    check("flag on: verdict plumbing unchanged", res_on["verdict"] == "broke")

    # 4. flag ON but no keywords -> byte-identical to old
    res_nokw, c_nokw = run_prior()
    check("flag on, no keywords: byte-identical to old", [(c["system"], c["user"]) for c in c_nokw]
          == [(c["system"], c["user"]) for c in c_plain])

    # 5. call site: tick() passes the three fields from the store record (source check, no live tick)
    src = inspect.getsource(lane2.tick)
    check("tick() passes age_s/horizon/pred_place to _judge_prior",
          "_judge_prior(due_judgeable[\"expect\"], percepts" in src and "age_s=_prediction_age_s(due_judgeable, now)" in src
          and "pred_place=due_judgeable.get(\"place\")" in src and "horizon=due_judgeable.get(\"horizon\")" in src)

    lane2.JUDGE_MADE_LINE = saved_flag
    check("live data files untouched", _snap() == before)
    print("\nFAILED: " + ", ".join(FAILS) if FAILS else "\nALL CHECKS PASSED")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
