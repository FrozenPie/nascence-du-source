"""
J-2649 (I-0128 rule-induction drill, measurement_to_action; F-3384). Hermetic: runs INSIDE lab_env.isolate, no LLM, no hub.
Checks: flag-off default does nothing (ask never called, no file written); shadow mode (drill on, feed off) asks, grades
and logs but feeds nothing and returns nothing; live mode returns ONLY the bare first failing {input, output} pair (None
on a right answer), never a score/confidence/verdict; competence.record_drill_accuracy receives (conf, hit_all); the lab
generator/checker is reused not forked; the ladder climbs; the pre-registered read flags a constant; a before/after
sha256 canary on the live stores proves nothing outside the sandbox was written.
  python scripts/_test_induction_drill_j2649.py      # exit 0 = ALL OK
"""
import hashlib
import json
import random
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  BEFORE lab_env (F-2423)
from core import induction_drill as idr    # noqa: E402
from core import competence as comp        # noqa: E402
from core import prediction_error as pe    # noqa: E402
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
import lab_env                            # noqa: E402
from lab_env import isolate                # noqa: E402
import tempfile                            # noqa: E402
# the lab dir lives in a temp dir, never under the shared tree's data/_lab (job-run rule); it is outside data/ so
# profile.guard_path honours it as an upstream redirect
_LAB_TMP = Path(tempfile.mkdtemp(prefix="j2649_lab_"))
lab_env._LAB_ROOT = _LAB_TMP
lab_env._ISOLATE_OUTCOMES_LOG = _LAB_TMP / "_isolate_outcomes.jsonl"

LIVE_DATA = Path(r"C:\Nascence\data")
FAILS = 0


def check(c, label):
    global FAILS
    print(("  ok   " if c else "  FAIL ") + label)
    FAILS += 0 if c else 1


def h(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def rows(p):
    p = Path(p)
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


check(Path(core.__file__).resolve().is_relative_to(ROOT), "core.__file__ is inside the tree under test")
CANARY = [LIVE_DATA / "capability_beliefs.json", LIVE_DATA / "prediction_error_log.jsonl",
          LIVE_DATA / "prediction_error_state.json", LIVE_DATA / "induction_drill_state.json",
          LIVE_DATA / "logs" / "induction_drill_shadow.jsonl", LIVE_DATA / "math_drill_state.json"]
before = {p: h(p) for p in CANARY}
live_listing_before = sorted(p.name for p in LIVE_DATA.glob("*induction*")) if LIVE_DATA.exists() else []


def reply(item, wrong_idx=(), conf=0.9):
    ans = [str(o) for _, o in item["held"]]
    for i in wrong_idx:
        ans[i] = "zzz-9999" if item["family"] in ("string", "ca_row") else "987654"
    return json.dumps({"answers": ans, "confidence": conf})


def gen(seed, family, tier):
    return idr.generate(random.Random(seed), family=family, tier=tier)


with isolate(db="empty", also=[(idr, ["_STATE", "_SHADOW"]), (comp, ["_BELIEFS_FILE"]),
                               (pe, ["_RAW", "_STATE", "_SHADOW"])]) as lab_dir:
    for mod, attr in [(idr, "_STATE"), (idr, "_SHADOW"), (comp, "_BELIEFS_FILE"), (pe, "_RAW")]:
        check(Path(getattr(mod, attr)).resolve().is_relative_to(lab_dir.resolve()), f"{mod.__name__}.{attr} redirected into the lab")

    print("[reuse] lab generator/checker is the lab module, not a fork")
    check(not hasattr(idr, "GEN") and idr._lab().__file__.endswith("rule_induction_calibration_lab.py"),
          "generator/parser/checker come from scripts/rule_induction_calibration_lab.py")

    print("[flags off] shipped default")
    check(idr.INDUCTION_DRILL is False and idr.INDUCTION_FEED is False, "both flags ship False")
    calls = []
    r = idr.run_item(lambda s, u: calls.append(1) or "{}")
    check(r is None and calls == [], "flag off: returns None and never calls ask")
    check(not Path(idr._STATE).exists() and not Path(idr._SHADOW).exists() and not Path(comp._BELIEFS_FILE).exists()
          and rows(pe._RAW) == [], "flag off: no state, shadow, belief or prediction_error file written")

    print("[prompt] elicits before any answer, leaks nothing")
    it = gen(7, "function", 2)
    system, user = idr.prompt(it)
    check("confidence" in user and "ALL THREE" in user, "prompt asks for 3 predictions and one confidence")
    tail = user.split("Predict the outputs for:")[-1]
    check(it["rule"] not in user and all(f"-> {o}" not in tail for _, o in it["held"]),
          "prompt carries neither the rule text nor the held answers")

    print("[shadow] drill on, feed off")
    idr.INDUCTION_DRILL = True
    it1 = gen(11, "sequence", 1)
    r = idr._finish(it1, reply(it1, wrong_idx=(1,), conf=0.93))
    check(r is None, "shadow: returns None (no counterexample leaves the module)")
    sh = rows(idr._SHADOW)
    check(len(sh) == 1 and sh[0]["would_feed"] is True and sh[0]["fed"] is False and sh[0]["predicted"] == 0.93
          and sh[0]["measured"] == 0.0, "shadow row records the would-be pair (0.93, 0.0), not fed")
    check(sh[0]["counterexample"] == {"input": it1["held"][1][0], "output": it1["held"][1][1]},
          "shadow row keeps the pair it would have returned")
    check(not Path(comp._BELIEFS_FILE).exists() and rows(pe._RAW) == [],
          "shadow: competence beliefs and prediction_error untouched")

    print("[live] drill on, feed on")
    idr.INDUCTION_FEED = True
    try:
        it2 = gen(12, "string", 1)
        ce = idr._finish(it2, reply(it2, wrong_idx=(0, 2), conf=0.88))
        check(ce == {"input": it2["held"][0][0], "output": it2["held"][0][1]}, "returns the FIRST failing pair")
        check(set(ce) == {"input", "output"}, "the return carries exactly input and output")
        blob = json.dumps(ce).lower() + idr.format_counterexample(it2, ce).lower()
        check(not any(w in blob for w in ("conf", "score", "gap", "right", "wrong", "correct", "hit", "0.88", "rule", "brier")),
              "no score/confidence/verdict word in anything returned")
        b = json.loads(Path(comp._BELIEFS_FILE).read_text(encoding="utf-8"))["induction"]
        check(b["calib_pairs"][-1] == [0.88, 0.0] and b["accuracy"] == 0.0 and b["accuracy_count"] == 1,
              "record_drill_accuracy('induction') got (predicted 0.88, measured 0.0)")
        check(len(rows(pe._RAW)) == 1 and rows(pe._RAW)[0]["domain"] == "induction",
              "prediction_error observed the pair (maths' own path)")
        check(rows(idr._SHADOW)[-1]["fed"] is True, "shadow row says fed")
        it3 = gen(13, "ca_row", 1)
        check(idr._finish(it3, reply(it3, conf=0.9)) is None, "all three right: returns None (silence, not 'right')")
        check(idr.counterexample(it3, [True, True, True]) is None, "counterexample() None when nothing failed")
        n_before = len(rows(idr._SHADOW))
        check(idr._finish(it3, "not json at all") is None and rows(idr._SHADOW)[-1]["scored"] is False
              and len(rows(idr._SHADOW)) == n_before + 1, "unparseable reply: logged unscored, nothing returned")
        b2 = json.loads(Path(comp._BELIEFS_FILE).read_text(encoding="utf-8"))["induction"]
        check(b2["accuracy_count"] == 2, "unparseable reply was not fed (count 2 = the wrong + the right item only)")
        check(idr.run_item(lambda s, u: None) is None, "ask returning None (solver wobble) is not graded")
        out = idr.run_item(lambda s, u: json.dumps({"answers": ["1", "1", "1"], "confidence": 0.99}), rng=random.Random(5))
        check(out is None or set(out) == {"input", "output"}, "run_item end to end returns None or a bare pair")

        print("[ladder] accuracy window climbs a tier")
        t0 = idr._load()["ladder"]["function"]["tier"]
        for k in range(idr.ADVANCE_WINDOW):
            itx = gen(100 + k, "function", t0)
            idr._finish(itx, reply(itx, conf=0.8))
        check(idr._load()["ladder"]["function"]["tier"] == t0 + 1, "12/12 hits at tier 1 -> tier 2")
    finally:
        idr.INDUCTION_FEED = False
        idr.INDUCTION_DRILL = False

    print("[read] pre-registered read")
    rr = idr.read([{"scored": True, "family": "sequence", "conf": 0.9, "hit_all": 0} for _ in range(60)])
    check(rr["ready"] and rr["constant_fail"] and rr["modal_share"] == 1.0 and rr["gap_overall"] == 0.9,
          "60 rows all at 0.9: ready, constant_fail, gap 0.9")
    mix = [{"scored": True, "family": "string", "conf": c, "hit_all": h_}
           for c, h_ in [(0.2, 0), (0.5, 1), (0.8, 0), (0.4, 0), (0.6, 1)] * 12]
    rm = idr.read(mix)
    check(not rm["constant_fail"] and rm["modal_share"] == 0.2, "spread confidences: no constant")
    check(idr.read([])["n_scored"] == 0 and idr.read([])["ready"] is False, "empty log reads as n=0, not ready")

after = {p: h(p) for p in CANARY}
check(before == after, "sha256 canary: live stores unchanged")
check(sorted(p.name for p in LIVE_DATA.glob("*induction*")) == live_listing_before,
      "no new induction file under C:\\Nascence\\data")
print("ALL OK" if FAILS == 0 else f"{FAILS} FAILED")
sys.exit(1 if FAILS else 0)
