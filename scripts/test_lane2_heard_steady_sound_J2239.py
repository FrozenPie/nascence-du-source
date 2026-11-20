"""
Test suite -- Lane 2 heard-steady-sound predictions kept out of the prediction store (F-2932, J-2239, 2026-10-16).

Part A (pure): `_heard_steady_sound_flag` on REAL expect_next strings and REAL rendered sounds lines copied from a
snapshot of data/lane2_shadow.jsonl (10-09..10-16 window, F-2932), including the rows where 'clock' means the
horizon ('the clock of the thing is 6 minutes') -- those must NOT be flagged, even against a sounds line that
does name the clock tick.
Part B (real tick()): same hermetic scaffold as scripts/test_lane2_notice_check_tick.py, run inside
lab_env.isolate() -- a flagged tick logs heard_steady_sound=True and appends NOTHING to the prediction store; a
horizon-'clock' expectation and a tick prediction with no clock heard are both stored as before.
Part C (status()): trivial_prediction_rate is unchanged (gross), trivial_prediction_rate_net excludes flagged ticks.
Part D (optional replay): `--snapshot PATH` (a COPY of data/lane2_shadow.jsonl, read-only) recounts the flag over
every clock-hearing tick and reports gross vs net trivial rate over the copy.

Run: python scripts/test_lane2_heard_steady_sound_J2239.py [--snapshot PATH]   (exit 0 = every check passed)
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import socket
import sys
import types
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core as _core_pkg  # noqa: E402  BEFORE lab_env (F-2423): the tree under test must win on sys.path
assert Path(_core_pkg.__file__).resolve().is_relative_to(ROOT), (_core_pkg.__file__, ROOT)
import aiohttp  # noqa: E402
from core import lane2  # noqa: E402
from core import lane2_break_habituation as _hab  # noqa: E402
from core import telemetry as _telemetry_mod  # noqa: E402
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate  # noqa: E402

CHECKS: list[tuple[str, bool]] = []


def check(name: str, cond, detail: str = "") -> None:
    CHECKS.append((name, bool(cond)))
    print(("PASS" if cond else "FAIL"), "-", name, ("" if cond or not detail else f"  [{detail}]"))


# ── canary: the live data dir (and this checkout's) must be byte-identical before and after ─────────────
_WATCH = ("lane2_shadow.jsonl", "lane2_store.json", "lane2_hints.json", "lane2_would_ask.jsonl", "llm_calls.jsonl")
_DIRS = {Path(r"C:\Nascence\data"), ROOT / "data"}


def _snap() -> dict:
    out = {}
    for d in _DIRS:
        for n in _WATCH:
            p = d / n
            out[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
    return out


_LIVE_BEFORE = _snap()

# ── Part A: real strings (copied verbatim from a snapshot of data/lane2_shadow.jsonl) ─────────────────
STUDY_SOUNDS = "fire crackle, clock tick, rain on roof"           # rendered line shape, study 10-12..10-16
STUDY_SOUNDS_RAW = ["fire_crackle", "clock_tick"]                  # world['sounds'] identifier shape
GARDEN_SOUNDS = "waves on shingle, wind in trees, footsteps grass soil, woodpile settle, morepork (an owl) call"
SHORE_SOUNDS = ("waves on shingle, shingle drag, tide pool trickle, kingfisher call, oystercatcher call, gull cries, "
                "shag (a cormorant) wingbeats")

FLAG_WHEN_HEARD = [
    "In about 6 minutes, the clock will tick.",
    "In the next 6 minutes, the clock will tick.",
    "I expect the clock to tick next in about 6 minutes.",
    "In about 6 minutes, I will hear a tick.",
    "In about 6 minutes, I will hear a clock tick.",
    "In about two minutes, the clock will tick again.",
    "In about two minutes, the sound of clock ticking will continue.",
    "I expect to hear a tick within next 6 minutes.",
]
# F-2932's horizon-'clock' rows (real, 10-09..10-16): 'clock' names the horizon, not the sound.
HORIZON_CLOCK = [
    ("In about 6 minutes, I will hear a bird's call, as the horizon is 'next' and the clock of the thing is 6 minutes.",
     GARDEN_SOUNDS),
    ("In about 6 minutes, I expect to hear a gull cry or a shagging sound, as the horizon is 'next' and the clock is "
     "approximately 6 minutes from now.", SHORE_SOUNDS),
    ("In the next hour, I expect to see the sun rise, as the current daylight is night, and the clock suggests within "
     "the hour. I anticipate that the temperature will begin to warm as the sun rises, and the",
     "waves on shingle, woodpile settle, morepork (an owl) call"),
    ("In about 6 minutes, I will hear the sound of waves breaking on the shore. This is a checkable statement about "
     "the horizon 'next' within the clock of the sun's position at 59 degrees azimuth.", SHORE_SOUNDS),
    ("I see a clock on the wall. The time is approximately 3:15 PM. Expect to see the time change within the next hour.",
     GARDEN_SOUNDS),
]
NEVER_FLAG_OTHER = [
    "I expect to hear a tickling sensation in about 5 minutes.",     # 'tick' inside another word
    "I expect the clock to ring in about 6 minutes",                 # a different event, accepted miss
    "In about 6 minutes, the fire will crackle.",
    "",
]

for e in FLAG_WHEN_HEARD:
    check(f"A1 flagged when the clock tick is heard (rendered line): {e[:50]}",
          lane2._heard_steady_sound_flag(e, STUDY_SOUNDS) is True)
    check(f"A2 flagged when the clock tick is heard (raw identifiers): {e[:50]}",
          lane2._heard_steady_sound_flag(e, STUDY_SOUNDS_RAW) is True)
    check(f"A3 NOT flagged where no clock is heard (garden): {e[:50]}",
          lane2._heard_steady_sound_flag(e, GARDEN_SOUNDS) is False)
    check(f"A4 NOT flagged with no sounds at all: {e[:50]}",
          lane2._heard_steady_sound_flag(e, None) is False and lane2._heard_steady_sound_flag(e, []) is False)
for e, snd in HORIZON_CLOCK:
    check(f"A5 horizon-'clock' row not flagged at its own place: {e[:50]}", lane2._heard_steady_sound_flag(e, snd) is False)
    check(f"A6 horizon-'clock' row not flagged even if the clock tick WERE heard: {e[:50]}",
          lane2._heard_steady_sound_flag(e, STUDY_SOUNDS) is False)
for e in NEVER_FLAG_OTHER:
    check(f"A7 not flagged (other event / sub-word / empty): {e[:50]!r}", lane2._heard_steady_sound_flag(e, STUDY_SOUNDS) is False)
check("A8 _trivial_prediction_flag itself unchanged (still flags clock and horizon-'clock' alike)",
      lane2._trivial_prediction_flag(FLAG_WHEN_HEARD[0]) and lane2._trivial_prediction_flag(HORIZON_CLOCK[0][0]))
check("A9 vocabulary is the small explicit tuple (clock tick only)",
      [t for t, _ in lane2._HEARD_STEADY_SOUNDS] == ["clock tick"])

# ── Part B: real tick() inside lab_env.isolate() ──────────────────────────────────────────────────────
_telemetry_mod.log_llm_call = lambda *a, **k: None
_hab.phase1_metric_sheet = lambda: None
_cr_stub = types.ModuleType("core.coupling_rides")
_cr_stub.publish_witness = lambda rec, store: None
sys.modules["core.coupling_rides"] = _cr_stub
_core_pkg.coupling_rides = _cr_stub

_NONLOCAL: list = []
_real_connect = socket.socket.connect


def _guard_connect(self, address, *a, **k):
    host = address[0] if isinstance(address, tuple) else address
    if host not in ("127.0.0.1", "::1", "localhost"):
        _NONLOCAL.append(address)
        raise OSError("test guard: real network connect refused")
    return _real_connect(self, address, *a, **k)


socket.socket.connect = _guard_connect
_REPLY = {"body": None}


class _FakeResp:
    def __init__(self, body): self.body = body
    def raise_for_status(self): return None
    async def json(self): return self.body


class _FakePostCM:
    def __init__(self, body): self.body = body
    async def __aenter__(self): return _FakeResp(self.body)
    async def __aexit__(self, *a): return False


class _FakeSession:
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False
    def post(self, url, json=None, timeout=None): return _FakePostCM(_REPLY["body"])


_REAL_SESSION = aiohttp.ClientSession
aiohttp.ClientSession = lambda *a, **k: _FakeSession()


def _generator_says(expect_next: str) -> None:
    content = json.dumps({"notice": "The fire is low and the room is warm.", "uncertain": "how long the fire will last.",
                          "expect_next": expect_next, "horizon": "next"})
    _REPLY["body"] = {"created_at": "2026-10-16T00:00:00Z", "done": True, "eval_count": 60,
                      "message": {"role": "assistant", "content": content}, "model": "deepseek-r1:7b",
                      "prompt_eval_count": 700}


_PERC = {"sounds": ["fire_crackle", "clock_tick"]}


def _percepts() -> dict:
    return {"available": ["world"], "missing": [], "run": 2,
            "world": {"place": "study", "standpoint": "at_the_desk", "warmth": 0.81, "warmth_band": "warm",
                      "light_band": "dim", "sounds": list(_PERC["sounds"])},
            "standpoint": "at_the_desk",
            "world_fields": ["place", "standpoint", "warmth", "warmth_band", "light_band", "sounds"],
            "somatic": {"energy": 0.88, "fatigue": 0.15, "tension": 0.3}}


lane2.gather_percepts = _percepts
lane2.read_weather = lambda: {"valence": None, "arousal": None, "unresolved": None}


async def _coh(out, store, percepts=None): return {"verdict": "coherent", "how": None}
async def _met(out): return {"verdict": "not_sampled", "how": None}
async def _ntc(notice, percepts): return {"verdict": "not_sampled", "how": None}


lane2._coherence_check, lane2._judge_metaphor, lane2._judge_notice = _coh, _met, _ntc


def _preds() -> list:
    return [p.get("expect") for p in (lane2._load_store().get("prediction") or [])]


async def run(expect: str) -> dict:
    _generator_says(expect)
    return await lane2.tick()


_ORIG_DATA = lane2._DATA
try:
    with isolate(db="empty", also=[(lane2, ["_LOG", "_STATE", "_HINTS", "_LOG_WONDER"])]) as lab:
        lane2._DATA = Path(lab)
        # J-3160 / D-0548: trivial predictions (these clock texts are flagged trivial) are no longer stored by default.
        # This test pins the OTHER guard (heard steady sound), so it runs with the new one off; the new guard has its
        # own test, scripts/_test_J3160_lane2_cup_artefacts.py.
        lane2.TRIVIAL_PREDICTION_EXCLUDED = False
        check("B0 lane2 paths redirected into the lab dir",
              all(Path(p).resolve().is_relative_to(Path(lab).resolve())
                  for p in (lane2._LOG, lane2._STATE, lane2._HINTS, lane2._LOG_WONDER)))

        r1 = asyncio.run(run("In about 6 minutes, the clock will tick again."))
        check("B1 tick logged a row", isinstance(r1, dict) and r1.get("kind") == "tick", str(r1)[:200])
        check("B1 heard_steady_sound=True on the row", (r1 or {}).get("heard_steady_sound") is True)
        check("B1 trivial_prediction still computed exactly as before (True)", (r1 or {}).get("trivial_prediction") is True)
        check("B1 expect_is_plan untouched (False)", (r1 or {}).get("expect_is_plan") is False)
        check("B1 nothing appended to the prediction store", _preds() == [], str(_preds()))

        r2 = asyncio.run(run(HORIZON_CLOCK[0][0]))
        check("B2 horizon-'clock' expectation: heard_steady_sound=False", (r2 or {}).get("heard_steady_sound") is False)
        check("B2 ...and it IS stored as a prediction", _preds() == [HORIZON_CLOCK[0][0]], str(_preds()))

        _PERC["sounds"] = ["fire_crackle", "rain_on_roof"]          # clock not heard this tick
        r3 = asyncio.run(run("In about 6 minutes, the clock will tick."))
        check("B3 tick prediction with NO clock heard: heard_steady_sound=False", (r3 or {}).get("heard_steady_sound") is False)
        check("B3 ...and it IS stored (only heard sounds are dropped)", len(_preds()) == 2, str(_preds()))

        _PERC["sounds"] = ["fire_crackle", "clock_tick"]
        r4 = asyncio.run(run("In about 6 minutes, the fire will crackle."))
        check("B4 a non-clock prediction in the study is unaffected and stored",
              (r4 or {}).get("heard_steady_sound") is False and len(_preds()) == 3, str(_preds()))

        # ── Part C: status() ─────────────────────────────────────────────────────────────────────────
        st = lane2.status()
        ticks = [json.loads(l) for l in open(lane2._LOG, encoding="utf-8") if l.strip()]
        ticks = [t for t in ticks if t.get("kind") == "tick"]
        gross = round(sum(1 for t in ticks if t.get("trivial_prediction")) / len(ticks), 3)
        net_rows = [t for t in ticks if not t.get("heard_steady_sound")]
        net = round(sum(1 for t in net_rows if t.get("trivial_prediction")) / len(net_rows), 3)
        check("C1 status() saw the 4 ticks", st.get("ticks") == 4 == len(ticks), str(st.get("ticks")))
        check("C2 trivial_prediction_rate is the unchanged gross rate (3 of 4 trivial)",
              st.get("trivial_prediction_rate") == gross == 0.75, str(st.get("trivial_prediction_rate")))
        check("C3 trivial_prediction_rate_net excludes the flagged tick (2 of 3)",
              st.get("trivial_prediction_rate_net") == net == 0.667, str(st.get("trivial_prediction_rate_net")))
        check("C4 heard_steady_sound_n counts the flagged tick", st.get("heard_steady_sound_n") == 1)
finally:
    lane2._DATA = _ORIG_DATA
    aiohttp.ClientSession = _REAL_SESSION
    socket.socket.connect = _real_connect

check("Z1 no non-loopback socket connect attempted", not _NONLOCAL)
check("Z2 C:\\Nascence\\data and this checkout's data/ watch-list byte-identical before and after", _snap() == _LIVE_BEFORE)

# ── Part D: optional read-only replay over a snapshot COPY ───────────────────────────────────────────
if "--snapshot" in sys.argv:
    snap = Path(sys.argv[sys.argv.index("--snapshot") + 1])
    check("D0 snapshot is not the live log", snap.resolve() != Path(r"C:\Nascence\data\lane2_shadow.jsonl").resolve())
    rows = [json.loads(l) for l in open(snap, encoding="utf-8") if l.strip()]
    rows = [r for r in rows if r.get("kind") == "tick" and r.get("percept_lines")]

    def _sounds(r):
        for line in r["percept_lines"].split("\n"):
            if line.startswith("- sounds:"):
                return line[len("- sounds:"):].strip()
        return ""

    heard = [r for r in rows if "clock tick" in _sounds(r)]
    flagged = [r for r in rows if lane2._heard_steady_sound_flag(r.get("expect_next"), _sounds(r))]
    print(f"REPLAY ticks-with-percept_lines={len(rows)} clock-heard={len(heard)} flagged={len(flagged)} "
          f"(clock-word expects among heard={sum(1 for r in heard if 'clock' in (r.get('expect_next') or '').lower())})")
    check("D1 every flagged replay row actually heard the clock tick", all(r in heard for r in flagged))
    g = sum(1 for r in rows if r.get("trivial_prediction")) / len(rows)
    nr = [r for r in rows if r not in flagged]
    n = sum(1 for r in nr if r.get("trivial_prediction")) / len(nr)
    print(f"REPLAY trivial gross={g:.3f} net-of-flag={n:.3f} (n={len(rows)} / {len(nr)})")

n_fail = sum(1 for _, ok in CHECKS if not ok)
print()
print(f"{len(CHECKS) - n_fail}/{len(CHECKS)} checks passed")
sys.exit(1 if n_fail else 0)
