"""J-3100 (F-3818, P-0109): Lane 2 `_judge_prior` re-asks ONCE when the panel timed out, instead of closing the
prediction as cannot_tell.

HERMETIC: core.lane2's data paths point at a temp dir, core.coupling_rides is a recording stub, the generator and the
three other judges are stubs, and core.judge_panel.rule_detail is a scripted stub (no hub is contacted; Ramses is not
touched).  A snapshot proves the live data/ files were not changed.  The REAL _judge_prior, tick() and status() run.

Run from the worktree: python scripts/_test_J3100_lane2_judge_retry.py   (exit 0 = every check passed)
"""
from __future__ import annotations

import asyncio
import json
import sys
import tempfile
import time
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core as _core_pkg  # noqa: E402  (core BEFORE anything that touches lab_env)
from core import judge_panel as jp  # noqa: E402
from core import lane2  # noqa: E402
from core import lane2_break_habituation as _hab  # noqa: E402
from core import night as _night  # noqa: E402
from core import telemetry as _telemetry_mod  # noqa: E402

assert str(Path(lane2.__file__).resolve()).startswith(str(ROOT)), lane2.__file__

_ORIG_DATA = lane2._DATA
_WATCH = ("lane2_shadow.jsonl", "lane2_store.json", "coupling_rides.jsonl", "nascence.log", "llm_calls.jsonl",
          "judge_panel_log.jsonl")


def _snap() -> dict:
    out = {}
    for n in _WATCH:
        p = _ORIG_DATA / n
        out[n] = (p.stat().st_size, p.stat().st_mtime_ns) if p.exists() else None
    return out


_LIVE_BEFORE = _snap()
TMP = Path(tempfile.mkdtemp(prefix="j3100_lane2_"))
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


# ── scripted panel: each call pops the next scripted reply for the key asked ───────────────────────────────
TIMEOUT = {"verdict": None, "how": "unavailable", "err1": "timeout", "err2": None, "why": None}
TIMEOUT2 = {"verdict": None, "how": "unavailable", "err1": None, "err2": "timeout", "why": None}
HTTPFAIL = {"verdict": None, "how": "unavailable", "err1": "http", "err2": None, "why": None}
NOERR = {"verdict": None, "how": "unavailable", "err1": None, "err2": None, "why": None}
HELD = {"verdict": True, "how": "agreed", "err1": None, "err2": None, "why": "stub held"}
CALLS: list = []
SCRIPT: list = []


async def _stub_rule_detail(system, user, key, context="", tiebreak_url=None, **kw):
    CALLS.append(key)
    return SCRIPT.pop(0)


jp.rule_detail = _stub_rule_detail
lane2.percept_lines = lambda p: "PERCEPTS - observed text"
PERCEPTS = {"world": {"place": "study"}}


def prior(script):
    CALLS.clear()
    SCRIPT[:] = list(script)
    return asyncio.run(lane2._judge_prior("the lamp stays on", PERCEPTS))


# ── PART A: _judge_prior alone ─────────────────────────────────────────────────────────────────────────────
check("A0 shipped default is OFF", lane2.JUDGE_RETRY_ON_TIMEOUT is False and lane2.JUDGE_RETRY_MAX == 1)

OLD_CANNOT = {"verdict": "cannot_tell", "how": "unavailable", "why": None,
              "contradicted_how": None, "contradicted_why": None}
r = prior([TIMEOUT])
check("A1 flag OFF + timeout -> cannot_tell, dict byte-identical to the pre-J-3100 return, one ask", r == OLD_CANNOT and CALLS == ["held"])

lane2.JUDGE_RETRY_ON_TIMEOUT = True
r = prior([TIMEOUT])
check("A2 flag ON + err1 timeout -> marker verdict 'retry' (one ask, no second ask)",
      r["verdict"] == "retry" and r["how"] == "unavailable" and r["err1"] == "timeout" and CALLS == ["held"])
r = prior([TIMEOUT2])
check("A3 flag ON + err2 timeout -> 'retry'", r["verdict"] == "retry" and r["err2"] == "timeout")
r = prior([HTTPFAIL])
check("A4 flag ON + unavailable for a non-timeout cause (http) -> cannot_tell exactly as today", r == OLD_CANNOT)
r = prior([NOERR])
check("A5 flag ON + unavailable with no error recorded -> cannot_tell as today", r == OLD_CANNOT)

HELD_OUT = {"verdict": "held", "how": "agreed", "why": "stub held", "contradicted_how": None, "contradicted_why": None}
r_on = prior([HELD])
calls_on = list(CALLS)
lane2.JUDGE_RETRY_ON_TIMEOUT = False
r_off = prior([HELD])
check("A6 held-true path is byte-identical flag on vs off (same dict, same single ask)",
      json.dumps(r_on, sort_keys=True) == json.dumps(r_off, sort_keys=True) == json.dumps(HELD_OUT, sort_keys=True)
      and calls_on == CALLS == ["held"])
lane2.JUDGE_RETRY_ON_TIMEOUT = True
SPLIT = {"verdict": None, "how": "split_no_tiebreak", "err1": None, "err2": None, "why": None}
CONTRA_F = {"verdict": False, "how": "agreed", "err1": None, "err2": None, "why": "x"}
r = prior([SPLIT, CONTRA_F])
check("A7 a split_no_tiebreak still takes the second ask and closes 'unsettled' (not retried)",
      r["verdict"] == "unsettled" and CALLS == ["held", "contradicted"])
r = prior([{"verdict": False, "how": "agreed", "err1": None, "err2": None, "why": "n"}, TIMEOUT])
check("A8 timeout on the SECOND ask is untouched (closes unsettled as today)", r["verdict"] == "unsettled")

# ── PART B: tick() through the real store ──────────────────────────────────────────────────────────────────
_PERCEPTS = {"available": ["world"], "missing": [], "run": 2, "world": {"place": "study", "standpoint": "at_the_desk"},
             "standpoint": "at_the_desk", "world_fields": ["place", "standpoint"]}
lane2.gather_percepts = lambda: dict(_PERCEPTS)
lane2.read_weather = lambda: {"valence": None, "arousal": None, "unresolved": None}
_ASK = {"mode": "ok"}


async def _ask(payload):
    if _ASK["mode"] == "empty":
        return ({}, 1.0, "empty")
    return ({"notice": "I hear waves on the shingle.", "uncertain": "how long the light has been low.",
             "expect_next": "In about 6 minutes, I will hear a small warbler trill.", "horizon": "next"}, 1.0, None)


async def _coh(out, store, percepts=None):
    return {"verdict": "coherent", "how": None}


async def _met(out):
    return {"verdict": "not_sampled", "how": None}


async def _notice(n, p):
    return {"verdict": "not_sampled", "how": None}


lane2._ask = _ask
lane2._coherence_check = _coh
lane2._judge_metaphor = _met
lane2._judge_notice = _notice
_night.asleep = lambda: False


def rows():
    return [json.loads(x) for x in open(lane2._LOG, encoding="utf-8") if x.strip()]


def run_tick(script):
    CALLS.clear()
    SCRIPT[:] = list(script)
    asyncio.run(lane2.tick())


def seed():
    now = time.time()
    lane2._save_store({"factual": [], "prediction": [{
        "ts": now - 300, "expect": "the lamp stays on", "horizon": "next", "due_ts": now - 150,
        "standpoint": "at_the_desk", "place": "study", "verdict": None}]})


def due_rec():
    return next(p for p in lane2._load_store()["prediction"] if p["expect"] == "the lamp stays on")


lane2.JUDGE_RETRY_ON_TIMEOUT = True

# B1 timeout then a verdict: exactly one re-ask, then the real verdict
seed()
run_tick([TIMEOUT])
p = due_rec()
tr = [r for r in rows() if r.get("kind") == "tick"][-1]
check("B1a first timeout leaves the prediction OPEN (verdict None) with judge_retries == 1",
      p["verdict"] is None and p.get("judge_retries") == 1 and "judged_ts" not in p and "judged_how" not in p)
check("B1b the tick row logs prior_verdict 'retry' with prior_judge_retries 1 and the err",
      tr["prior_verdict"] == "retry" and tr.get("prior_judge_retries") == 1 and tr.get("prior_judge_err1") == "timeout")
check("B1c one panel ask so far", CALLS == ["held"])
run_tick([HELD])
p = due_rec()
tr = [r for r in rows() if r.get("kind") == "tick"][-1]
check("B1d the next tick re-asks (one more ask) and the prediction closes held", p["verdict"] == "held" and CALLS == ["held"])
check("B1e the closing row carries prior_verdict held and prior_judge_retries 1",
      tr["prior_verdict"] == "held" and tr.get("prior_judge_retries") == 1)
run_tick([])      # nothing due now: the panel is not asked again
check("B1f no third ask once closed", CALLS == [])

# B2 two timeouts: closes cannot_tell, never a third ask
seed()
run_tick([TIMEOUT])
run_tick([TIMEOUT2])
p = due_rec()
tr = [r for r in rows() if r.get("kind") == "tick"][-1]
check("B2a a second timeout closes cannot_tell (exactly as before J-3100)",
      p["verdict"] == "cannot_tell" and p["judged_how"] == "unavailable" and tr["prior_verdict"] == "cannot_tell")
check("B2b that row still carries prior_judge_retries 1 (so the lost ruling is countable)", tr.get("prior_judge_retries") == 1)
run_tick([])
check("B2c never a third ask", CALLS == [])

# B3 no-output tick: the retry is saved and mirrored on the skip row
seed()
_ASK["mode"] = "empty"
run_tick([TIMEOUT])
p = due_rec()
sk = [r for r in rows() if r.get("skip") == "no-output"][-1]
check("B3a no-output tick: store saved with judge_retries 1 and verdict None", p["verdict"] is None and p.get("judge_retries") == 1)
check("B3b skip row mirrors prior_verdict 'retry' + prior_judged_how + prior_judge_retries",
      sk.get("prior_verdict") == "retry" and sk.get("prior_judged_how") == "unavailable" and sk.get("prior_judge_retries") == 1
      and sk.get("judged_expect") == "the lamp stays on")
run_tick([HELD])
sk = [r for r in rows() if r.get("skip") == "no-output"][-1]
check("B3c the re-ask on a no-output tick closes held; skip row prior_verdict held, retries 1",
      due_rec()["verdict"] == "held" and sk.get("prior_verdict") == "held" and sk.get("prior_judge_retries") == 1)
_ASK["mode"] = "ok"

# B4 flag OFF: tick closes cannot_tell on the FIRST timeout, no judge_retries key anywhere
lane2.JUDGE_RETRY_ON_TIMEOUT = False
n_before = len(rows())
seed()
run_tick([TIMEOUT])
p = due_rec()
tr = [r for r in rows()[n_before:] if r.get("kind") == "tick"][-1]
check("B4a flag OFF: closes cannot_tell on the first timeout (today's behaviour)", p["verdict"] == "cannot_tell")
check("B4b flag OFF: no judge_retries on the record and no prior_judge_retries on the row",
      "judge_retries" not in p and "prior_judge_retries" not in tr and tr["prior_verdict"] == "cannot_tell")
lane2.JUDGE_RETRY_ON_TIMEOUT = True

# ── PART C: status() ───────────────────────────────────────────────────────────────────────────────────────
S = lane2.status()
pv = S.get("prediction_verdicts") or {}
check("C1 'retry' is in no verdict share (prediction_verdicts has no 'retry' key)", "retry" not in pv)
check("C2 predictions_judged counts only tick-row closures (as before): B1d held + B2 cannot_tell + B4 cannot_tell = 3; "
      "B3c closed on a skip row, which `verdicts` never read",
      S.get("predictions_judged") == 3 and sum(pv.values()) == 3)
check("C3 judge_retry_24h counts the three retry rows (B1a tick, B2 first tick, B3a skip)", S.get("judge_retry_24h") == 3)
check("C4 judge_retry_resolved_24h counts retried predictions that closed with a real ruling (B1d tick row, B3c skip row)",
      S.get("judge_retry_resolved_24h") == 2)
check("C5 judge_retry_lost_24h counts the second-timeout closure (B2)", S.get("judge_retry_lost_24h") == 1)

# ── the live files were not touched ────────────────────────────────────────────────────────────────────────
check("Z live data files untouched", _snap() == _LIVE_BEFORE)

bad = [n for n, ok in CHECKS if not ok]
print(f"\n{len(CHECKS) - len(bad)}/{len(CHECKS)} checks passed")
sys.exit(1 if bad else 0)
