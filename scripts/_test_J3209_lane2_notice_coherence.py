"""
Test suite -- J-3209 / D-0599: (1) the Lane 2 panel NOTICE judge is retired with its random draw order untouched;
(2) lane2:coherence's tiebreak is the lane2 gemma seat (_TIEBREAK_LANE2), not the shared granite TIEBREAK.

Same hermetic scaffold as scripts/test_lane2_notice_check_tick.py (fake aiohttp transport, lane2 data paths redirected
to a temp dir, coupling_rides stubbed, non-loopback sockets refused, this checkout's data/ stat-checked before and
after).  Nothing here touches a live store or a hub.

Run: python scripts/_test_J3209_lane2_notice_coherence.py      (exit 0 = every check passed)
"""
from __future__ import annotations
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/

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
assert str(Path(_core_pkg.__file__).resolve()).lower().startswith(str(ROOT).lower()), _core_pkg.__file__
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

TMP = Path(tempfile.mkdtemp(prefix="j3209_lane2_"))
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
_REPLY_BY_PORT: dict = {}     # port -> response body (judge hubs); the generator hub falls back to _REPLY["body"]


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
        return _FakePostCM(_REPLY_BY_PORT.get(url.rsplit(":", 1)[-1].split("/")[0], _REPLY["body"]))


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


_REAL_COHERENCE = lane2._coherence_check
lane2._coherence_check = _coherence_stub
lane2._judge_metaphor = _metaphor_stub
lane2._judge_notice = _notice_stub


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



import random  # noqa: E402

from core import judge_panel as _jp  # noqa: E402

_RANDOM_CALLS = []
_real_random = random.random
_FORCE = {"v": 0.99}
_NOTICE_CALLS: list = []


def _counting_random():
    v = _FORCE["v"] if _FORCE["v"] is not None else _real_random()
    _RANDOM_CALLS.append(v)
    return v


async def _recording_notice_stub(notice, percepts):
    _NOTICE_CALLS.append(notice)
    return {"verdict": "consistent", "how": "agreed"}


lane2._judge_notice = _recording_notice_stub


def _judge_body(key: str, value: bool) -> dict:
    return {"done": True, "message": {"role": "assistant", "content": json.dumps({key: value})}}


async def run_tick(notice: str) -> dict:
    _generator_says(notice)
    return await lane2.tick()


async def main():
    # ---- (1) retirement ----------------------------------------------------------------------------------
    check("A1 NOTICE_JUDGE_RETIRED defaults to True", lane2.NOTICE_JUDGE_RETIRED is True)
    check("A2 the sample rate constants are unchanged (the draw is kept)",
          lane2.NOTICE_JUDGE_SAMPLE_P == 0.25 and lane2.METAPHOR_JUDGE_SAMPLE_P == 0.25)

    random.random = _counting_random
    try:
        # B: every draw says "sampled" -> pre-D-0599 this would have called the panel notice judge
        _FORCE["v"] = 0.0
        _RANDOM_CALLS.clear()
        _NOTICE_CALLS.clear()
        r_ret = await run_tick("The air is warm and the light is dim.")
        draws_retired = list(_RANDOM_CALLS)
        check("B1 retired: the notice judge was NOT called on an always-sampled draw", _NOTICE_CALLS == [], str(_NOTICE_CALLS))
        check("B2 retired: notice_judged is the same shape, marked retired",
              (r_ret or {}).get("notice_judged") == {"verdict": "not_sampled", "how": "retired"}, str((r_ret or {}).get("notice_judged")))
        check("B3 the deterministic checker still ran", ((r_ret or {}).get("notice_checked") or {}).get("how") == "deterministic")

        # C: the revert switch restores the call, and the SAME random draws are consumed either way
        lane2.NOTICE_JUDGE_RETIRED = False
        try:
            _RANDOM_CALLS.clear()
            _NOTICE_CALLS.clear()
            r_live = await run_tick("The air is warm and the light is dim.")
            draws_live = list(_RANDOM_CALLS)
        finally:
            lane2.NOTICE_JUDGE_RETIRED = True
        check("C1 revert switch False: the notice judge is called again", len(_NOTICE_CALLS) == 1, str(_NOTICE_CALLS))
        check("C2 revert switch False: its verdict is logged", (r_live or {}).get("notice_judged") == {"verdict": "consistent", "how": "agreed"})
        check("C3 the random draws are identical (count and values) retired vs live: the draw order is untouched",
              draws_retired == draws_live and len(draws_retired) >= 2, f"{draws_retired} vs {draws_live}")

        # D: a seeded real stream: the same draw sequence in both modes
        seq = {}
        for mode in (True, False):
            lane2.NOTICE_JUDGE_RETIRED = mode
            _FORCE["v"] = None
            random.seed(20261106)
            _RANDOM_CALLS.clear()
            await run_tick("The light is dim.")
            seq[mode] = list(_RANDOM_CALLS)
        lane2.NOTICE_JUDGE_RETIRED = True
        check("D1 a seeded stream gives the same draw sequence retired vs live", seq[True] == seq[False] and len(seq[True]) >= 2, str(seq))
    finally:
        random.random = _real_random
        _FORCE["v"] = 0.99

    # ---- (2) coherence tiebreak seat ---------------------------------------------------------------------
    check("E0 judge_panel's shared TIEBREAK is untouched (granite :11437)", _jp.TIEBREAK == "http://LAN-HOST:11437")
    check("E0b _TIEBREAK_LANE2 is the gemma seat", lane2._TIEBREAK_LANE2 == "http://127.0.0.1:11439")

    seen = {}
    real_rd = _jp.rule_detail

    async def _rd(system, user, key, context="", **kw):
        seen["context"], seen["key"], seen["kw"] = context, key, dict(kw)
        return {"verdict": True, "how": "agreed"}
    _jp.rule_detail = _rd
    store = {"factual": [{"notice": "I hear a fire.", "standpoint": "at_the_door", "place": "study"}]}
    pcp = {"world": {"place": "study"}, "standpoint": "at_the_desk"}
    try:
        res = await _REAL_COHERENCE({"notice": "The fire is warm."}, store, pcp)
    finally:
        _jp.rule_detail = real_rd
    check("E1 _coherence_check passes tiebreak_url=_TIEBREAK_LANE2 to rule_detail",
          seen.get("kw", {}).get("tiebreak_url") == lane2._TIEBREAK_LANE2 and seen.get("context") == "lane2:coherence", str(seen))
    check("E2 verdict mapping unchanged (True -> coherent)", {k: res.get(k) for k in ("verdict", "how")} == {"verdict": "coherent", "how": "agreed"}, str(res))

    # E3: through the REAL panel path on the fake transport: v1 true (:11438), v2 false (:11440) -> the split goes to
    # :11439 (gemma), never :11437 (granite)
    _REPLY_BY_PORT.clear()
    _REPLY_BY_PORT.update({"11438": _judge_body("coherent", True), "11440": _judge_body("coherent", False),
                           "11439": _judge_body("coherent", False), "11437": _judge_body("coherent", True)})
    sent_before = len(_SENT)
    _jp._LOG = TMP / "judge_panel_log.jsonl"
    res3 = await _REAL_COHERENCE({"notice": "The fire is warm."}, store, pcp)
    urls = [x["url"] for x in _SENT[sent_before:]]
    ports = sorted(u.rsplit(":", 1)[-1].split("/")[0] for u in urls)
    check("E3 a v1/v2 split on coherence is asked of :11439 (gemma) and never :11437 (granite)",
          ports == ["11438", "11439", "11440"], str(urls))
    check("E4 the gemma seat's answer decides (false -> incoherent), not granite's (true)",
          {k: res3.get(k) for k in ("verdict", "how")} == {"verdict": "incoherent", "how": "tiebreak"}, str(res3))
    logged = [json.loads(l) for l in open(_jp._LOG, encoding="utf-8") if l.strip()]
    check("E5 the ruling row names the physical hub that cast the tiebreak (hub3 == 11439)",
          logged and logged[-1].get("hub3") == "11439" and logged[-1].get("context") == "lane2:coherence", str(logged[-1:]))

    # E6: an agreed pair makes no tiebreak call at all
    _REPLY_BY_PORT.update({"11440": _judge_body("coherent", True)})
    sent_before = len(_SENT)
    res6 = await _REAL_COHERENCE({"notice": "The fire is warm."}, store, pcp)
    ports6 = sorted(x["url"].rsplit(":", 1)[-1].split("/")[0] for x in _SENT[sent_before:])
    check("E6 an agreed pair asks no tiebreak (only :11438 and :11440)", ports6 == ["11438", "11440"] and res6["verdict"] == "coherent", str(ports6))

    # F: status() carries the retirement marker
    st = lane2.status()
    check("F1 status() reports notice_judge_retired True", st.get("notice_judge_retired") is True, str(st.get("notice_judge_retired")))


try:
    asyncio.run(main())
finally:
    aiohttp.ClientSession = _REAL_SESSION
    socket.socket.connect = _real_connect

check("Z1 core.lane2 data paths were redirected to the temp dir for the whole run",
      str(lane2._LOG).startswith(str(TMP)) and str(lane2._STATE).startswith(str(TMP)))
check("Z2 no non-loopback socket connect was attempted", not _NONLOCAL_CONNECTS)
check("Z4 this checkout's own data/ watch-list is byte-identical before and after", _snap() == _LIVE_BEFORE)
shutil.rmtree(TMP, ignore_errors=True)

n_fail = sum(1 for _, ok in CHECKS if not ok)
print()
print(f"{len(CHECKS) - n_fail}/{len(CHECKS)} checks passed")
sys.exit(1 if n_fail else 0)
