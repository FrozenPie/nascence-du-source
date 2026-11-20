"""
Test suite -- Lane 2 `notice_checked` through the REAL tick() and status() (D-0361(a), J-1896, 2026-10-07).

Same hermetic scaffold as scripts/test_lane2_hour_scale_horizon.py (fake aiohttp transport, lane2 data paths
redirected to a temp dir, coupling_rides stubbed, non-loopback sockets refused, this checkout's data/ stat-checked
before and after). Proves: a real tick() logs `notice_checked` beside `notice_judged`; the checker runs on every
tick (also the ones the panel judge does not sample); it draws no random numbers; it fails open; status() reports
the new scoreboard fields; and nothing else on the row moved.

Run: python scripts/test_lane2_notice_check_tick.py      (exit 0 = every check passed)
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


def check(name: str, cond, detail: str = "") -> None:
    CHECKS.append((name, bool(cond)))
    print(("PASS" if cond else "FAIL"), "-", name, ("" if cond or not detail else f"  [{detail}]"))


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


def _generator_says(notice: str, expect_next: str = "I expect the same light at the next look.", horizon: str = "next") -> None:
    """Queue the :11444 hub's envelope shape for one successful generation (F-2331's probe)."""
    content = json.dumps({"notice": notice, "uncertain": "how long the light has been low.",
                          "expect_next": expect_next, "horizon": horizon})
    _REPLY["body"] = {"created_at": "2026-10-03T00:00:00Z", "done": True, "eval_count": 60,
                      "message": {"role": "assistant", "content": content}, "model": "deepseek-r1:7b",
                      "prompt_eval_count": 700}


_PERCEPTS = {"available": ["world"], "missing": [], "run": 2,
             "world": {"place": "study", "standpoint": "at_the_desk", "warmth": 0.81, "warmth_band": "warm",
                       "light_band": "dim"},
             "standpoint": "at_the_desk", "world_fields": ["place", "standpoint", "warmth", "warmth_band", "light_band"],
             "somatic": {"energy": 0.88, "fatigue": 0.15, "tension": 0.3}}
lane2.gather_percepts = lambda: dict(_PERCEPTS)
lane2.read_weather = lambda: {"valence": None, "arousal": None, "unresolved": None}


async def _coherence_stub(out, store, percepts=None):
    return {"verdict": "coherent", "how": None}


async def _metaphor_stub(out):
    return {"verdict": "not_sampled", "how": None}


_PANEL = {"verdict": "not_sampled", "how": None}


async def _notice_stub(notice, percepts):
    return dict(_PANEL)


lane2._coherence_check = _coherence_stub
lane2._judge_metaphor = _metaphor_stub
lane2._judge_notice = _notice_stub
# D-0599 (1) (J-3209): the panel notice judge is retired by default (NOTICE_JUDGE_RETIRED=True). This suite is about the
# checker sitting BESIDE a sampled panel verdict, so it runs the REVERT path (flag False = the pre-D-0599 behaviour);
# the retired default is covered by scripts/_test_J3209_lane2_notice_coherence.py.
lane2.NOTICE_JUDGE_RETIRED = False


import random  # noqa: E402

from core import lane2_notice_check as _nc  # noqa: E402


def _rows() -> list[dict]:
    if not lane2._LOG.exists():
        return []
    return [json.loads(l) for l in open(lane2._LOG, encoding="utf-8") if l.strip()]


_RANDOM_CALLS = []
_real_random = random.random


_FORCE = {"v": 0.99}                    # default: no sampling draw hits (deterministic); T2 forces 0.0


def _counting_random():
    _RANDOM_CALLS.append(1)
    return _FORCE["v"] if _FORCE["v"] is not None else _real_random()


async def run_tick(notice: str) -> dict:
    _generator_says(notice)
    return await lane2.tick()


async def main():
    random.random = _counting_random
    try:
        # T1 - a wrong band word reaches the row, beside the panel verdict, on a tick the panel did NOT sample
        _PANEL.update(verdict="not_sampled", how=None)
        _RANDOM_CALLS.clear()
        r1 = await run_tick("The air is cool and I feel exhausted.")
        n_random_with_checker = len(_RANDOM_CALLS)
        check("T1 tick() logged a row", isinstance(r1, dict) and r1.get("kind") == "tick")
        nc1 = (r1 or {}).get("notice_checked") or {}
        check("T1 notice_checked is on the row and flags the wrong band word",
              nc1.get("verdict") == "contradiction" and any(f["kind"] == "warmth_band" for f in nc1.get("flags", [])), str(nc1))
        check("T1 it also flags the fatigue claim at 0.15", any(f["kind"] == "somatic" for f in nc1.get("flags", [])), str(nc1))
        check("T1 notice_judged sits beside it, untouched (not_sampled)", (r1 or {}).get("notice_judged") == {"verdict": "not_sampled", "how": None})
        check("T1 the checker ran on an UNSAMPLED tick (every tick, not 1-in-4)", nc1.get("how") == "deterministic")

        # T2 - a clean notice, and the panel verdict of a sampled tick stays exactly as the panel returned it
        _PANEL.update(verdict="consistent", how="agreed")
        _FORCE["v"] = 0.0                       # every sampling draw says "sampled": the panel stub answers
        r2 = await run_tick("The air is warm and the light is dim.")
        _FORCE["v"] = 0.99
        check("T2 clean notice -> consistent", ((r2 or {}).get("notice_checked") or {}).get("verdict") == "consistent", str((r2 or {}).get("notice_checked")))
        check("T2 panel verdict logged exactly as returned", (r2 or {}).get("notice_judged") == {"verdict": "consistent", "how": "agreed"})

        # T3 - fail-open: a checker that raises must not break the tick
        real_check = _nc.check_notice

        def _raise(*a, **k):
            raise RuntimeError("checker blew up")
        _nc.check_notice = _raise
        try:
            r3 = await run_tick("The air is cool.")
        finally:
            _nc.check_notice = real_check
        check("T3 tick survives a raising checker and logs not_checked/error",
              isinstance(r3, dict) and (r3.get("notice_checked") or {}) == {"verdict": "not_checked", "how": "error"}, str((r3 or {}).get("notice_checked")))

        # T4 - the checker draws no random numbers: the tick's own draws (sampling) are the same with it swapped for a stub
        real_helper = lane2._notice_checked
        lane2._notice_checked = lambda n, p: {"verdict": "consistent", "how": "deterministic"}
        _RANDOM_CALLS.clear()
        await run_tick("The air is cool and I feel exhausted.")
        n_random_stub = len(_RANDOM_CALLS)
        lane2._notice_checked = real_helper
        check("T4 same number of random draws with the real checker as with a stub", n_random_with_checker == n_random_stub,
              f"{n_random_with_checker} vs {n_random_stub}")
        check("T4 NOTICE_JUDGE_SAMPLE_P and METAPHOR_JUDGE_SAMPLE_P unchanged", lane2.NOTICE_JUDGE_SAMPLE_P == 0.25 and lane2.METAPHOR_JUDGE_SAMPLE_P == 0.25)
    finally:
        random.random = _real_random


try:
    asyncio.run(main())
    st = lane2.status()
    rows = [x for x in _rows() if x.get("kind") == "tick"]
    answered = [x for x in rows if (x.get("notice_checked") or {}).get("verdict") in ("contradiction", "consistent")]
    flagged = [x for x in answered if x["notice_checked"]["verdict"] == "contradiction"]
    check("S1 status() ran over the real tick rows", isinstance(st, dict) and st.get("ticks") == len(rows) == 4)
    check("S2 notice_checked_n counts the answered rows", st.get("notice_checked_n") == len(answered) == 3, str(st.get("notice_checked_n")))
    check("S3 flag rate = flagged / answered", st.get("notice_checked_flag_rate") == round(len(flagged) / len(answered), 3), str(st.get("notice_checked_flag_rate")))
    check("S4 solid rate present and <= flag rate", st.get("notice_checked_solid_rate") is not None and st["notice_checked_solid_rate"] <= st["notice_checked_flag_rate"])
    check("S5 paired n counts only ticks the panel also answered (T2 only, so 1)", st.get("notice_checked_paired_n") == 1 and st.get("notice_checked_paired_flag_rate") == 0.0, str(st.get("notice_checked_paired_n")))
    check("S6 kinds counter names the flagged classes", {"warmth_band", "somatic"} <= set((st.get("notice_checked_kinds") or {})), str(st.get("notice_checked_kinds")))
    check("S7 the panel scoreboard is untouched: notice_judged_n / notice_contradiction_rate keep their meaning",
          st.get("notice_judged_n") == 1 and st.get("notice_contradiction_rate") == 0.0, str((st.get("notice_judged_n"), st.get("notice_contradiction_rate"))))
finally:
    aiohttp.ClientSession = _REAL_SESSION
    socket.socket.connect = _real_connect

check("Z1 core.lane2 data paths were redirected to the temp dir for the whole run",
      str(lane2._LOG).startswith(str(TMP)) and str(lane2._STATE).startswith(str(TMP)))
check("Z2 no non-loopback socket connect was attempted", not _NONLOCAL_CONNECTS)
check("Z3 the fake transport saw every generation POST (4 ticks)", len(_SENT) == 4, str(len(_SENT)))
check("Z4 this checkout's own data/ watch-list is byte-identical before and after", _snap() == _LIVE_BEFORE)
shutil.rmtree(TMP, ignore_errors=True)

n_fail = sum(1 for _, ok in CHECKS if not ok)
print()
print(f"{len(CHECKS) - n_fail}/{len(CHECKS)} checks passed")
sys.exit(1 if n_fail else 0)
