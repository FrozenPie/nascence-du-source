"""J-3160 (D-0548) + J-3035 (F-3742): Lane 2 stops judging a next/hour prediction in the wrong place or long after
it was made, trivial predictions are not stored, and the cup tripwire is a number a person can read.

HERMETIC: core.lane2's data paths point at a temp dir, core.coupling_rides is a recording stub, every model call
(_ask, _judge_prior, the three judges) is a stub, core.night.asleep is patched, and a snapshot proves the live
data/ files were not touched. The REAL _prediction_judgeability, tick(), status(), cup_break_artefact_reasons and
cup_artefact_report run.

Run from the worktree: python scripts/_test_J3160_lane2_cup_artefacts.py   (exit 0 = every check passed)
"""
from __future__ import annotations

import asyncio
import io
import json
import sys
import tempfile
import time
import types
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core as _core_pkg  # noqa: E402  (core BEFORE anything that touches lab_env)
from core import lane2  # noqa: E402
from core import lane2_break_habituation as _hab  # noqa: E402
from core import night as _night  # noqa: E402
from core import telemetry as _telemetry_mod  # noqa: E402

assert str(Path(lane2.__file__).resolve()).startswith(str(ROOT)), lane2.__file__

_ORIG_DATA = lane2._DATA
_WATCH = ("lane2_shadow.jsonl", "lane2_store.json", "coupling_rides.jsonl", "nascence.log", "llm_calls.jsonl")


def _snap() -> dict:
    out = {}
    for n in _WATCH:
        p = _ORIG_DATA / n
        out[n] = (p.stat().st_size, p.stat().st_mtime_ns) if p.exists() else None
    return out


_LIVE_BEFORE = _snap()
TMP = Path(tempfile.mkdtemp(prefix="j3160_lane2_"))
lane2._DATA = TMP
lane2._LOG = TMP / "lane2_shadow.jsonl"
lane2._STATE = TMP / "lane2_store.json"
lane2._HINTS = TMP / "lane2_hints.json"
lane2._LOG_WONDER = TMP / "lane2_would_ask.jsonl"
_telemetry_mod.log_llm_call = lambda *a, **k: None
_hab.phase1_metric_sheet = lambda: None
_cr_stub = types.ModuleType("core.coupling_rides")
_cr_stub.publish_witness = lambda rec, store: None
_cr_stub.CUP_TTL_S = 1800.0
sys.modules["core.coupling_rides"] = _cr_stub
_core_pkg.coupling_rides = _cr_stub

CHECKS: list = []


def check(name, cond):
    CHECKS.append((name, bool(cond)))
    print(("PASS" if cond else "FAIL"), "-", name)


# ── PART A: the pure gate, on the real rows quoted in F-3741 / F-3742 ──────────────────────────────────
J = lane2._prediction_judgeability
G = lane2._GRACE_S
T0 = 1_800_000_000.0

# F-3741 (2): warmth/hour made in the GARDEN at_the_door, judged in the STUDY at_the_door.
warm = {"ts": T0, "horizon": "hour", "due_ts": T0 + 3600, "standpoint": "at_the_door", "place": "garden", "verdict": None}
check("warmth/hour: same place, due+0 -> matched-standpoint", J(warm, T0 + 3600, "at_the_door", "garden") == "matched-standpoint")
check("warmth/hour: same STANDPOINT NAME, other place, inside grace -> waiting (master judged it)",
      J(warm, T0 + 3600 + 10, "at_the_door", "study") == "waiting")
check("warmth/hour: other place, past grace (due+400) -> expired-moved",
      J(warm, T0 + 3600 + 400, "at_the_door", "study") == "expired-moved")
check("warmth/hour: a different standpoint is still expired-moved (unchanged)",
      J(warm, T0 + 3600 + 400, "at_the_hearth", "garden") == "expired-moved")

# F-3741 (4): clock/next made 23:24:23, Du slept 23:29 to 00:04, judged 2,434 s later.
clock = {"ts": T0, "horizon": "next", "due_ts": T0 + 150, "standpoint": "at_the_desk", "place": "study", "verdict": None}
check("clock/next judged 2,434 s after creation -> expired-stale by age",
      J(clock, T0 + 2434, "at_the_desk", "study") == "expired-stale")
check("clock/next, a SHORT sleep inside the wait (lateness only 250 s) -> expired-stale by the asleep rule",
      J(clock, T0 + 400, "at_the_desk", "study", last_asleep_ts=T0 + 200) == "expired-stale")
check("same, no sleep -> matched-standpoint (the rule is the sleep, not the lateness)",
      J(clock, T0 + 400, "at_the_desk", "study") == "matched-standpoint")
check("a sleep BEFORE the prediction was made does not stale it",
      J(clock, T0 + 400, "at_the_desk", "study", last_asleep_ts=T0 - 50) == "matched-standpoint")
day = {"ts": T0, "horizon": "day", "due_ts": T0 + 43200, "standpoint": "at_the_desk", "place": "study", "verdict": None}
check("day horizon is exempt from the asleep rule (a 12 h wait spans a night by design)",
      J(day, T0 + 43200 + 100, "x", "study", last_asleep_ts=T0 + 20000) == "matched-place")
check("day horizon still obeys the age bound", J(day, T0 + 43200 + 700, "x", "study") == "expired-stale")
edge = {"ts": T0, "horizon": "next", "due_ts": T0 + 150, "standpoint": "s", "place": "p", "verdict": None}
check("age bound: exactly due + 2 grace ticks is not stale; one second more is",
      J(edge, T0 + 150 + 2 * G, "s", "p") == "matched-standpoint" and J(edge, T0 + 150 + 2 * G + 1, "s", "p") == "expired-stale")
check("legacy: standpoint but no place -> standpoint alone decides",
      J({**edge, "place": None}, T0 + 200, "s", "anywhere") == "matched-standpoint")
check("legacy: neither recorded -> matched-legacy", J({"horizon": "next", "ts": T0, "due_ts": T0 + 150}, T0 + 200, "s", "p") == "matched-legacy")
check("a record with no due_ts is never read as stale", J({"horizon": "next", "ts": T0}, T0 + 99999, "s", "p") != "expired-stale")

# ── PART B: tick(), stubbed model calls ────────────────────────────────────────────────────────────────
_PERCEPTS = {"available": ["world"], "missing": [], "run": 2, "world": {"place": "study", "standpoint": "at_the_desk"},
             "standpoint": "at_the_desk", "world_fields": ["place", "standpoint"]}
lane2.gather_percepts = lambda: dict(_PERCEPTS)
lane2.read_weather = lambda: {"valence": None, "arousal": None, "unresolved": None}
_SAY = {"expect_next": "In about 6 minutes, I will hear the clock strike.", "horizon": "next"}
JUDGE_CALLS: list = []


async def _ask(payload):
    return ({"notice": "I hear waves on the shingle.", "uncertain": "how long the light has been low.",
             "expect_next": _SAY["expect_next"], "horizon": _SAY["horizon"]}, 1.0, None)


async def _judge(expect, percepts, *_a, **_k):   # J-3099 added age_s, horizon, pred_place
    JUDGE_CALLS.append(expect)
    return {"verdict": "held", "how": "agreed", "why": "stub", "contradicted_how": None, "contradicted_why": None}


async def _coh(out, store, percepts=None):
    return {"verdict": "coherent", "how": None}


async def _met(out):
    return {"verdict": "not_sampled", "how": None}


async def _notice(n, p):
    return {"verdict": "not_sampled", "how": None}


lane2._ask = _ask
lane2._judge_prior = _judge
lane2._coherence_check = _coh
lane2._judge_metaphor = _met
lane2._judge_notice = _notice
_night.asleep = lambda: False


def rows():
    return [json.loads(x) for x in open(lane2._LOG, encoding="utf-8") if x.strip()]


def run_tick():
    asyncio.run(lane2.tick())


# B1: a trivial prediction (bare azimuth, flagged trivial_prediction) is not stored; the tick row keeps the flag.
lane2._save_store({"factual": [], "prediction": []})
_SAY["expect_next"] = "In about 6 minutes, the sun will be at 301.1 degrees."
run_tick()
st = lane2._load_store()
rs = rows()
check("B1 trivial prediction (bare azimuth) NOT stored", not st.get("prediction"))
check("B1 the tick row still carries trivial_prediction=True (measurement unchanged)",
      any(r.get("kind") == "tick" and r.get("trivial_prediction") is True for r in rs))
check("B1 one 'trivial-excluded' skip row records the exclusion",
      sum(1 for r in rs if r.get("kind") == "skip" and r.get("skip") == "trivial-excluded") == 1)
_SAY["expect_next"] = "In about 6 minutes, I will see the clock moving to 23:25."
run_tick()
check("B1 a clock tick is excluded too", not lane2._load_store().get("prediction"))
# non-trivial: stored as before
_SAY["expect_next"] = "In about 6 minutes, I will hear a small warbler trill."
run_tick()
check("B1 a non-trivial prediction is stored", len(lane2._load_store().get("prediction") or []) == 1)
# switch off -> old behaviour
lane2._save_store({"factual": [], "prediction": []})
lane2.TRIVIAL_PREDICTION_EXCLUDED = False
_SAY["expect_next"] = "In about 6 minutes, the sun will be at 301.1 degrees."
run_tick()
check("B1 TRIVIAL_PREDICTION_EXCLUDED=False restores storing it", len(lane2._load_store().get("prediction") or []) == 1)
lane2.TRIVIAL_PREDICTION_EXCLUDED = True

# B2: a stale due prediction closes unjudgeable/expired-stale and the judge is NOT called.
now = time.time()
_SAY["expect_next"] = "In about 6 minutes, I will hear a small warbler trill."
lane2._save_store({"factual": [], "prediction": [{"ts": now - 5000, "expect": "the lamp stays on", "horizon": "next",
    "due_ts": now - 4850, "standpoint": "at_the_desk", "place": "study", "verdict": None}]})
JUDGE_CALLS.clear()
run_tick()
p = lane2._load_store()["prediction"][0]
check("B2 stale prediction closed unjudgeable / expired-stale", p["verdict"] == "unjudgeable" and p["judged_how"] == "expired-stale")
check("B2 the judge panel was not called for it", JUDGE_CALLS == [])
check("B2 the tick row says expired-stale", rows()[-1].get("prior_judged_how") == "expired-stale"
      and rows()[-1].get("prior_verdict") == "unjudgeable")

# B3: made in the garden, same standpoint name, judged in the study past grace -> moved, judge not called.
now = time.time()
lane2._save_store({"factual": [], "prediction": [{"ts": now - 600, "expect": "the temperature will be 0.32 warmth",
    "horizon": "next", "due_ts": now - 450, "standpoint": "at_the_desk", "place": "garden", "verdict": None}]})
JUDGE_CALLS.clear()
run_tick()
p = lane2._load_store()["prediction"][0]
check("B3 cross-place prediction closed unjudgeable / moved", p["verdict"] == "unjudgeable" and p["judged_how"] == "moved")
check("B3 the judge panel was not called for it", JUDGE_CALLS == [])

# B4: a sleep inside the wait stales a prediction that is only 150 s late.
now = time.time()
lane2._save_store({"factual": [], "prediction": [{"ts": now - 300, "expect": "the lamp stays on", "horizon": "next",
    "due_ts": now - 150, "standpoint": "at_the_desk", "place": "study", "verdict": None}]})
lane2._LAST_ASLEEP_TS = now - 100
JUDGE_CALLS.clear()
run_tick()
p = lane2._load_store()["prediction"][0]
check("B4 slept-through prediction closed expired-stale, judge not called",
      p["verdict"] == "unjudgeable" and p["judged_how"] == "expired-stale" and JUDGE_CALLS == [])

# B5: the asleep branch records the sleep (so B4's input is real, not only injected).
lane2._LAST_ASLEEP_TS = 0.0
_night.asleep = lambda: True
t_before = time.time()
run_tick()
_night.asleep = lambda: False
check("B5 an asleep tick sets _LAST_ASLEEP_TS", lane2._LAST_ASLEEP_TS >= t_before)

# B6: a normal matched prediction is still judged (no regression).
now = time.time()
lane2._save_store({"factual": [], "prediction": [{"ts": now - 300, "expect": "the lamp stays on", "horizon": "next",
    "due_ts": now - 150, "standpoint": "at_the_desk", "place": "study", "verdict": None}]})
lane2._LAST_ASLEEP_TS = 0.0
JUDGE_CALLS.clear()
run_tick()
check("B6 same place, on time -> still judged by the panel", JUDGE_CALLS == ["the lamp stays on"]
      and lane2._load_store()["prediction"][0]["verdict"] == "held")

# B7: the no-output skip row carries where the judged prediction was made (so the cup test can grade it).
async def _ask_empty(payload):
    return ({}, 1.0, "empty")
lane2._ask = _ask_empty
now = time.time()
lane2._save_store({"factual": [], "prediction": [{"ts": now - 300, "expect": "the lamp stays on", "horizon": "next",
    "due_ts": now - 150, "standpoint": "at_the_desk", "place": "study", "verdict": None}]})
run_tick()
r = rows()[-1]
check("B7 no-output skip row carries judged_horizon / judged_pred_place / judged_pred_standpoint",
      r.get("skip") == "no-output" and r.get("judged_horizon") == "next" and r.get("judged_pred_place") == "study"
      and r.get("judged_pred_standpoint") == "at_the_desk")
lane2._ask = _ask

# B8: status() counters.
S = lane2.status()
check("B8 status().unjudgeable_stale_24h counts the two stale closures (B2, B4)", S.get("unjudgeable_stale_24h") == 2)
check("B8 status().unjudgeable_moved_place_24h counts the place-only closure (B3)", S.get("unjudgeable_moved_place_24h") == 1)
check("B8 status().trivial_excluded_24h counts the exclusions (B1: azimuth + clock)", S.get("trivial_excluded_24h") == 2)

# ── PART C: the cup tripwire report, on the four F-3741 breaks (+ one clean one) ────────────────────────
LOGP, RIDESP = TMP / "c_lane2.jsonl", TMP / "c_rides.jsonl"
B = 1_800_100_000.0


def tick_row(ts, expect, horizon, age, pred_place, place, **kw):
    return {"ts": ts, "kind": "tick", "place": place, "judged_expect": expect, "judged_horizon": horizon,
            "judged_age_s": age, "judged_pred_place": pred_place, "prior_verdict": "broke", **kw}


log_rows = [
    {"ts": B - 5000, "kind": "skip", "skip": "asleep"},                                 # (before every wait below began)
    # (1) 10-29: night sunrise, hour: made in place, judged on time -- passes all three tests (documented limit)
    tick_row(B + 100, "Within the next hour, the weather will become clearer, and the sky will brighten as the sun begins to rise.",
             "hour", 3700, "study", "study"),
    # (2) 10-30: warmth made in the garden, judged in the study
    tick_row(B + 5000, "Within the next hour, the weather direction will be 225 degrees, and the temperature will be 0.32 warmth.",
             "hour", 3700, "garden", "study"),
    # (3) 10-30: bare azimuth
    tick_row(B + 9000, "In about 6 minutes, the sun will be at 301.1 degrees.", "next", 660, "study", "study"),
    # (4) 11-01: clock, slept in the wait (asleep skip rows) and judged 2,434 s later
    {"ts": B + 12000, "kind": "skip", "skip": "asleep"},
    tick_row(B + 14500, "In about 6 minutes, I will see the clock moving to 23:25.", "next", 2434.4, "study", "study"),
    # (5) a clean break: same place, on time, not trivial
    tick_row(B + 20000, "Within the next hour, I will hear the tide turn.", "hour", 3800, "shore", "shore"),
]
LOGP.write_text("".join(json.dumps(r) + "\n" for r in log_rows), encoding="utf-8")


def ride(ts, topic, horizon):
    return {"ts": ts, "kind": "ride", "stop": "idle thought seed", "line": "witness", "dose": "cup",
            "value": {"verdict": "broke", "topic": topic, "horizon": horizon, "cup_would_ride": True}, "what_changed_next": None}


rides = [
    {"ts": B + 50, "kind": "ride", "stop": "climate tick", "line": "witness", "dose": "bucket", "value": {"break_rate_24h": 0.1}},
    ride(B + 160, "sun", "hour"), ride(B + 5060, "warmth", "hour"), ride(B + 9060, "sun", "next"),
    {"ts": B + 9100, "kind": "ride", "stop": "idle thought seed", "line": "witness", "dose": "cup", "value": {}},   # empty read
    ride(B + 14560, "clock", "next"), ride(B + 20060, "tide", "hour"),
    ride(B - 500, "sun", "hour"),                                                  # before the watch start: excluded
]
RIDESP.write_text("".join(json.dumps(r) + "\n" for r in sorted(rides, key=lambda r: r["ts"])), encoding="utf-8")
rep = lane2.cup_artefact_report(since_ts=B, log_path=LOGP, rides_path=RIDESP)
by_topic = {g["topic"]: g["reasons"] for g in rep.get("recent", [])}
check("C1 five rides since the start (empty reads and bucket rows and the earlier ride are not rides)", rep.get("rides") == 5)
check("C2 all five matched to their break row", rep.get("matched") == 5 and rep.get("unmatched") == 0)
check("C3 warmth made in the garden, judged in the study -> place_mismatch", by_topic.get("warmth") == ["place_mismatch"])
check("C4 bare azimuth -> trivial", by_topic.get("sun") is not None and any("trivial" in g["reasons"] for g in rep["recent"]))
check("C5 clock (slept in the wait, 2,434 s, trivial) -> stale and trivial", by_topic.get("clock") == ["stale", "trivial"])
check("C6 the night sunrise (case 1) passes all three tests (the documented limit)",
      [g for g in rep["recent"] if g["ts"] == B + 160][0]["reasons"] == [])
check("C7 the clean tide break is clean", by_topic.get("tide") == [])
check("C8 totals: 3 artefacts, 2 clean, by reason place 1 / stale 1 / trivial 2",
      rep.get("artefacts") == 3 and rep.get("clean") == 2 and rep.get("by_reason") == {"place_mismatch": 1, "stale": 1, "trivial": 2})
check("C9 tripwire flag is a reading, limit 2, reached", rep.get("tripwire_limit") == 2 and rep.get("tripwire_reached") is True)
rep_none = lane2.cup_artefact_report(since_ts=B + 99999, log_path=LOGP, rides_path=RIDESP)
check("C10 no rides since a later start -> zero, tripwire not reached", rep_none.get("rides") == 0 and rep_none.get("tripwire_reached") is False)
check("C11 an unreadable path never raises", "error" in lane2.cup_artefact_report(log_path=TMP / "nope.jsonl", rides_path=TMP / "nope2.jsonl")
      or lane2.cup_artefact_report(log_path=TMP / "nope.jsonl", rides_path=TMP / "nope2.jsonl").get("rides") == 0)
check("C12 the report switches nothing: LANE2_LIVE untouched", lane2.LANE2_LIVE is True)

# ── PART D: the du_pulse block runs and prints the line (exec of the block's own text) ──────────────────
src = (ROOT / "scripts" / "du_pulse.py").read_text(encoding="utf-8")
a = src.index("# Lane 2 cup tripwire")
b = src.index("# 7) WHAT'S NEW")
block = src[a:b]
_orig_report = lane2.cup_artefact_report
lane2.cup_artefact_report = lambda *x, **k: _orig_report(since_ts=B, log_path=LOGP, rides_path=RIDESP)
buf = io.StringIO()
with redirect_stdout(buf):
    exec(compile(block, "du_pulse_block", "exec"), {"time": time, "json": json})
lane2.cup_artefact_report = _orig_report
out = buf.getvalue()
check("D1 pulse line shows rides, artefacts, reasons and the tripwire reading",
      "lane2 cup tripwire" in out and "5 cup rides" in out and "3 read as artefacts" in out
      and "place mismatch 1 / stale 1 / trivial 2" in out and "REACHED" in out)
check("D2 the pulse text says nothing switches the cup off automatically", "nothing does it automatically" in out)

# ── no live data touched ───────────────────────────────────────────────────────────────────────────────
check("live data files unchanged", _snap() == _LIVE_BEFORE)

bad = [n for n, c in CHECKS if not c]
print(f"\n{len(CHECKS) - len(bad)}/{len(CHECKS)} checks passed")
if bad:
    print("FAILED:", bad)
    sys.exit(1)
