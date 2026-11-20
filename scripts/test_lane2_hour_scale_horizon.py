"""
Test suite — Lane 2 stops relabelling hour-worded sun/tide/moon predictions as 'day' (J-1713, F-2336, 2026-10-03).

F-2336 (verified): core/lane2.py's `_correct_horizon` overrides a prediction to horizon 'day' (a 12 h clock)
whenever its text names a day-scale topic word (tide / tidal / sun / moon / moonlight / sunset / sunrise) and
carries no minute-scale word -- F-1984 / J-1376 exempted MINUTE wording only. Hour-worded claims ("I expect the
sun to rise in about an hour", "Within an hour, the sun will be at 180 degrees") therefore still hit the
override and were judged 12+ hours after a claim that named a one-hour window. Since the 2026-09-28 19:08
restart 12 of 12 day-labelled predictions were hour-worded (11 came through the override) and the one judged
break in about 49 live hours was one of them, scored 13.4 h after a one-hour claim.

What J-1713 adds (additive; nothing existing is renamed, removed or re-meant):
  1. `_correct_horizon` gains a fifth branch, 'skipped-hours': a day-scale topic IS named and the text itself
     names an hour-scale clock (a regex -- NOT the bare word "hour": multi-hour and day phrasing stays
     overridden) -> the generator's own horizon label is kept, exactly as 'skipped-minutes' keeps it. Minute
     wording is still checked first, so 'skipped-minutes' means exactly what it meant before.
  2. `status()` gains `horizon_override_skipped_hours` beside `horizon_override_skipped_minutes`.

HERMETIC, the way J-1709's check was (and this project's test-isolation rule demands): every data path in
core.lane2 is redirected to a fresh temp dir before anything runs, `core.telemetry.log_llm_call` is stubbed,
`core.coupling_rides` (which tick() publishes the Witness tuple to) is replaced by a recording stub,
`aiohttp.ClientSession` is replaced by a fake transport, and a guard on `socket.socket.connect` refuses any
non-loopback connect -- zero real network, zero real data/ I/O. The REAL `_correct_horizon`, `_ask`, `tick()`
and `status()` run.

Run: python scripts/test_lane2_hour_scale_horizon.py      (exit 0 = every check passed)
"""
from __future__ import annotations

import asyncio
import json
import shutil
import socket
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import aiohttp  # noqa: E402
import core as _core_pkg  # noqa: E402
from core import lane2  # noqa: E402
from core import lane2_break_habituation as _hab  # noqa: E402
from core import telemetry as _telemetry_mod  # noqa: E402

_ORIG_DATA = lane2._DATA
_WATCH = ("lane2_shadow.jsonl", "llm_calls.jsonl", "nascence.log", "lane2_store.json")


def _snap() -> dict:
    out = {}
    for n in _WATCH:
        p = _ORIG_DATA / n
        out[n] = (p.stat().st_size, p.stat().st_mtime_ns) if p.exists() else None
    return out


_LIVE_BEFORE = _snap()

TMP = Path(tempfile.mkdtemp(prefix="j1713_lane2_"))
lane2._DATA = TMP
lane2._LOG = TMP / "lane2_shadow.jsonl"
lane2._STATE = TMP / "lane2_store.json"
lane2._HINTS = TMP / "lane2_hints.json"
lane2._LOG_WONDER = TMP / "lane2_would_ask.jsonl"

_telemetry_mod.log_llm_call = lambda *a, **k: None      # never touch a real telemetry store
_hab.phase1_metric_sheet = lambda: None                 # status() would otherwise READ the live phase-1 stores

# tick() publishes the Witness tuple to core.coupling_rides after every logged row; a recording stub keeps that
# (and whatever store it writes) entirely out of the test.
_PUBLISHED: list = []
_cr_stub = types.ModuleType("core.coupling_rides")
_cr_stub.publish_witness = lambda rec, store: _PUBLISHED.append(rec.get("ts"))
sys.modules["core.coupling_rides"] = _cr_stub
_core_pkg.coupling_rides = _cr_stub

CHECKS: list[tuple[str, bool]] = []


def check(name: str, cond) -> None:
    CHECKS.append((name, bool(cond)))
    print(("PASS" if cond else "FAIL"), "-", name)


# ── no real network: a refused non-loopback connect, counted ────────────────────────────────────────
_NONLOCAL_CONNECTS: list = []
_real_connect = socket.socket.connect


def _guard_connect(self, address, *a, **k):
    host = address[0] if isinstance(address, tuple) else address
    if host not in ("127.0.0.1", "::1", "localhost"):
        _NONLOCAL_CONNECTS.append(address)
        raise OSError("test guard: real network connect refused")
    return _real_connect(self, address, *a, **k)


socket.socket.connect = _guard_connect

# ── the faked aiohttp transport (records every POST; nothing leaves the process) ────────────────────
_SENT: list[dict] = []
_REPLY = {"body": None}


class _FakeResp:
    def __init__(self, body):
        self.body = body

    def raise_for_status(self):
        return None

    async def json(self):
        return self.body


class _FakePostCM:
    def __init__(self, body):
        self.body = body

    async def __aenter__(self):
        return _FakeResp(self.body)

    async def __aexit__(self, *a):
        return False


class _FakeSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    def post(self, url, json=None, timeout=None):
        _SENT.append({"url": url, "json": json})
        return _FakePostCM(_REPLY["body"])


_REAL_SESSION = aiohttp.ClientSession
aiohttp.ClientSession = lambda *a, **k: _FakeSession()


def _generator_says(expect_next: str, horizon: str) -> None:
    """Queue the :11444 hub's envelope shape for one successful generation (F-2331's probe)."""
    content = json.dumps({"notice": "I hear waves on the shingle.", "uncertain": "how long the light has been low.",
                          "expect_next": expect_next, "horizon": horizon})
    _REPLY["body"] = {"created_at": "2026-10-03T00:00:00Z", "done": True, "eval_count": 60,
                      "message": {"role": "assistant", "content": content}, "model": "deepseek-r1:7b",
                      "prompt_eval_count": 700}


_PERCEPTS = {"available": ["world"], "missing": [], "run": 2,
             "world": {"place": "study", "standpoint": "at_the_desk"},
             "standpoint": "at_the_desk", "world_fields": ["place", "standpoint"]}
lane2.gather_percepts = lambda: dict(_PERCEPTS)
lane2.read_weather = lambda: {"valence": None, "arousal": None, "unresolved": None}


async def _coherence_stub(out, store, percepts=None):
    return {"verdict": "coherent", "how": None}


async def _metaphor_stub(out):
    return {"verdict": "not_sampled", "how": None}


async def _notice_stub(notice, percepts):
    return {"verdict": "not_sampled", "how": None}


lane2._coherence_check = _coherence_stub
lane2._judge_metaphor = _metaphor_stub
lane2._judge_notice = _notice_stub

DAY = ("day", True, "day-scale")

# ── PART A — the pure function ──────────────────────────────────────────────────────────────────────
# The 12 day-labelled predictions logged since the 2026-09-28 19:08 restart, verbatim from
# data/lane2_shadow.jsonl (F-2336): all hour-worded, 11 of them through the day-scale override.
POST_RESTART_DAY_LABELLED = [
    "I expect the sun to rise in about an hour.",
    "I expect the sun to rise in about an hour.",
    "I expect to see the sun in about an hour.",
    "I expect to see the sun in the sky within an hour.",
    "I expect to hear something within the next hour, as the sun's position will change significantly over the course of the day.",
    "Within an hour, the sun will be at 180 degrees.",
    "I expect to see the sun rise in about an hour.",
    "I expect the sun's position to be in the sky within the next hour.",
    "I expect the sun's position to change within the next hour.",
    "I expect the sun to rise in about an hour",
    "Within the next hour, the light will begin to brighten as the sun rises.",
    "In the next hour, the sun will reach its highest point.",
]

# other hour-scale phrasings (3 real ones from the pre-restart era log, the rest natural variants)
HOUR_SCALE_VARIANTS = [
    "The tide will rise within the hour.",                       # real
    "The tide will continue to rise over the next hour.",        # real
    "The sun's azimuth angle will change over the next hour.",   # real
    "The sun will set in 1 hour.", "The moon will clear the ridge in one hour.",
    "An hour from now the sun will be lower.", "The tide will turn in half an hour.",
    "The tide will turn in a half-hour.", "WITHIN AN HOUR the moon will rise.",
    "The tide will turn in the next half hour.",
]

# multi-hour / day phrasing and non-clock uses of the word: must STAY overridden to 'day'
STILL_DAY_SCALE = [
    "The sun will rise in about two hours.",                     # real
    "The sun will set in about 2 hours.",                        # real
    "The tide will rise by the hour.",                           # real (a rate, not a clock)
    "The sun will be at 333 degrees.",                           # real (names no clock at all)
    "The tide will turn in twelve hours.", "The sun will set in 12 hours.",
    "The moon will rise hours from now.", "The sun will set by evening.",
    "The tide will be high tomorrow.", "The moon will be up overnight.",
    "The tide will turn in a few hours.", "The tide will turn in several hours.",
    "The sun will set in an hour and a half.", "The tide will turn in the next hour or two.",
    "Within half a day the tide will turn.", "The moon will rise in 11 hours.",
    "The moon will rise in 21 hours.", "The tide will complete a twelve-hour cycle.",
]


def part_a():
    for label in ("next", "hour"):
        check(f"A1 all 12 post-restart day-labelled texts keep the generator's {label!r} label, branch skipped-hours",
              all(lane2._correct_horizon(label, t) == (label, False, "skipped-hours")
                  for t in POST_RESTART_DAY_LABELLED))
        check(f"A2 the other hour-scale phrasings keep the {label!r} label",
              all(lane2._correct_horizon(label, t) == (label, False, "skipped-hours") for t in HOUR_SCALE_VARIANTS))
        bad = [t for t in STILL_DAY_SCALE if lane2._correct_horizon(label, t) != DAY]
        check(f"A3 multi-hour / day phrasing and non-clock 'hour' still override {label!r} -> day", not bad)
        if bad:
            print("      still exempted:", bad)
    check("A4 the briefing's own two sentences are exempt",
          lane2._correct_horizon("hour", "I expect the sun to rise in about an hour")
          == ("hour", False, "skipped-hours")
          and lane2._correct_horizon("hour", "Within an hour, the sun will be at 180 degrees.")
          == ("hour", False, "skipped-hours"))
    # untouched branches
    check("A5 generator already said 'day': unchanged branch already-day",
          all(lane2._correct_horizon("day", t) == ("day", False, "already-day")
              for t in POST_RESTART_DAY_LABELLED))
    check("A6 minute wording still wins and still reads skipped-minutes (J-1376 sentence, and minute+hour text)",
          lane2._correct_horizon("next", "In about two minutes, the sun will be at 302.5 degrees.")
          == ("next", False, "skipped-minutes")
          and lane2._correct_horizon("next", "In about two minutes, the sun will reach the horizon, which is "
                                             "within the next hour.") == ("next", False, "skipped-minutes")
          and lane2._correct_horizon("hour", "The sun will rise in about an hour, so 60 minutes.")
          == ("hour", False, "skipped-minutes"))
    check("A7 no day-scale topic named: no-match even with hour wording (label untouched)",
          lane2._correct_horizon("next", "A bird will call within the hour.") == ("next", False, "no-match")
          and lane2._correct_horizon("hour", "The wind will drop in about an hour.") == ("hour", False, "no-match"))
    check("A8 empty / None text: no-match, never raises",
          lane2._correct_horizon("next", "") == ("next", False, "no-match")
          and lane2._correct_horizon("hour", None) == ("hour", False, "no-match"))
    check("A9 the original day-scale branch is intact: a topic with no sub-day clock is still relabelled",
          lane2._correct_horizon("next", "The tide will be high.") == DAY
          and lane2._correct_horizon("hour", "The sun's azimuth is 34.5 degrees.") == DAY)
    check("A10 return shape is still a (str, bool, str) 3-tuple",
          all(isinstance(x, tuple) and len(x) == 3 and isinstance(x[0], str) and isinstance(x[1], bool)
              and isinstance(x[2], str)
              for x in (lane2._correct_horizon("next", t) for t in POST_RESTART_DAY_LABELLED + STILL_DAY_SCALE)))


# ── PART B — the REAL tick() over the REAL _ask(), faked transport ──────────────────────────────────
def _rows() -> list[dict]:
    if not lane2._LOG.exists():
        return []
    return [json.loads(l) for l in open(lane2._LOG, encoding="utf-8") if l.strip()]


def _store_predictions() -> list[dict]:
    return json.load(open(lane2._STATE, encoding="utf-8")).get("prediction") or []


async def tick_case(expect_next: str, horizon: str):
    _generator_says(expect_next, horizon)
    n_pred = len(_store_predictions()) if lane2._STATE.exists() else 0
    rec = await lane2.tick()
    pred = _store_predictions()[n_pred:] if lane2._STATE.exists() else []
    return rec, (pred[0] if pred else None)


async def part_b():
    # B1 — the F-2336 case: an hour-worded sun claim the generator labelled 'hour'
    rec, pred = await tick_case("Within an hour, the sun will be at 180 degrees.", "hour")
    check("B1 tick() returned a row", isinstance(rec, dict))
    r = rec or {}
    check("B1 hour-worded sun claim keeps the generator's 'hour' label (was relabelled 'day' before J-1713)",
          r.get("horizon") == "hour" and r.get("horizon_overridden") is False
          and r.get("horizon_override_branch") == "skipped-hours")
    check("B1 the stored prediction is due in ONE hour, not twelve",
          pred is not None and pred.get("horizon") == "hour"
          and abs((pred["due_ts"] - pred["ts"]) - lane2.HORIZONS["hour"]) < 0.5)

    # B2 — the generator's own 'next' label is kept too, exactly as skipped-minutes keeps it
    rec, pred = await tick_case("I expect the sun to rise in about an hour.", "next")
    r = rec or {}
    check("B2 'next'-labelled hour-worded claim keeps 'next' (the branch never invents a label)",
          r.get("horizon") == "next" and r.get("horizon_overridden") is False
          and r.get("horizon_override_branch") == "skipped-hours"
          and pred is not None and abs((pred["due_ts"] - pred["ts"]) - lane2.HORIZONS["next"]) < 0.5)

    # B3 — control: multi-hour wording is still relabelled day (12 h clock), flagged overridden
    rec, pred = await tick_case("The sun will rise in about two hours.", "hour")
    r = rec or {}
    check("B3 'about two hours' is NOT exempt: still relabelled 'day', overridden, branch day-scale",
          r.get("horizon") == "day" and r.get("horizon_overridden") is True
          and r.get("horizon_override_branch") == "day-scale"
          and pred is not None and abs((pred["due_ts"] - pred["ts"]) - lane2.HORIZONS["day"]) < 0.5)

    # B4 — control: the J-1376 minute exemption is unchanged
    rec, pred = await tick_case("In about two minutes, the sun will be at 302.5 degrees.", "next")
    r = rec or {}
    check("B4 minute-worded sun claim: still skipped-minutes, label kept",
          r.get("horizon") == "next" and r.get("horizon_overridden") is False
          and r.get("horizon_override_branch") == "skipped-minutes")

    # B5 — a no-topic claim is untouched
    rec, pred = await tick_case("A bird will call within the hour.", "hour")
    r = rec or {}
    check("B5 no day-scale topic: branch no-match, label kept",
          r.get("horizon") == "hour" and r.get("horizon_overridden") is False
          and r.get("horizon_override_branch") == "no-match")

    # B6 — every pre-existing horizon key is still on the row (additive only)
    check("B6 the row still carries horizon / horizon_overridden / horizon_override_branch / judged_horizon",
          all(k in r for k in ("horizon", "horizon_overridden", "horizon_override_branch", "judged_horizon")))


# ── PART C — status(): the new counter sits beside the existing one ────────────────────────────────
def part_c():
    rows = [x for x in _rows() if x.get("kind") == "tick"]
    want_hours = sum(1 for x in rows if x.get("horizon_override_branch") == "skipped-hours")
    want_minutes = sum(1 for x in rows if x.get("horizon_override_branch") == "skipped-minutes")
    want_rate = round(sum(1 for x in rows if x.get("horizon_overridden")) / len(rows), 3)
    st = lane2.status()
    check("C1 status() runs clean over the real tick rows", isinstance(st, dict) and st.get("ticks") == len(rows))
    check("C2 horizon_override_skipped_hours counts exactly the skipped-hours rows (2 of 5 here)",
          st.get("horizon_override_skipped_hours") == want_hours == 2)
    check("C3 horizon_override_skipped_minutes is unchanged in meaning (1 of 5 here)",
          st.get("horizon_override_skipped_minutes") == want_minutes == 1)
    check("C4 horizon_overridden_rate is unchanged in meaning (only the day-scale branch: 1 of 5)",
          st.get("horizon_overridden_rate") == want_rate == 0.2)
    check("C5 horizon_chosen reflects the kept labels: hour 2, next 2, day 1",
          st.get("horizon_chosen") == {"next": 2, "hour": 2, "day": 1})


async def main():
    await part_b()


try:
    part_a()
    asyncio.run(main())
    part_c()
finally:
    aiohttp.ClientSession = _REAL_SESSION
    socket.socket.connect = _real_connect

# ── the hermetic-ness proof ─────────────────────────────────────────────────────────────────────────
check("Z1 core.lane2 data paths were redirected to the temp dir for the whole run",
      str(lane2._LOG).startswith(str(TMP)) and str(lane2._STATE).startswith(str(TMP)))
check("Z2 no non-loopback socket connect was attempted", not _NONLOCAL_CONNECTS)
check("Z3 the fake transport saw every generation POST (5 ticks)", len(_SENT) == 5)
check("Z4 the coupling_rides stub, not the real module, received the Witness rows", len(_PUBLISHED) == 5)
check("Z5 this checkout's own data/ watch-list is byte-identical before and after", _snap() == _LIVE_BEFORE)
shutil.rmtree(TMP, ignore_errors=True)

n_fail = sum(1 for _, ok in CHECKS if not ok)
print(f"\n{len(CHECKS) - n_fail}/{len(CHECKS)} checks passed")
sys.exit(1 if n_fail else 0)
