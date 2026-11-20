"""
Test suite -- J-3117 (F-3837, P-0110): the Lane 2 metaphor judge's second (flag) arm.

Same hermetic scaffold as scripts/test_lane2_notice_check_tick.py (fake aiohttp transport, lane2 data paths redirected
to a temp dir, coupling_rides stubbed, non-loopback sockets refused, this checkout's data/ stat-checked before and
after).  Nothing here touches a live store or a hub.

Run: python scripts/_test_J3117_lane2_metaphor_flag_arm.py      (exit 0 = every check passed)
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

TMP = Path(tempfile.mkdtemp(prefix="j3117_lane2_"))
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



import random  # noqa: E402

_METAPHOR_CALLS: list = []
_METAPHOR_SEES: list = []
_VERDICT = {"v": "literal"}


async def _metaphor_stub(out):
    _METAPHOR_CALLS.append(1)
    _METAPHOR_SEES.append(sorted(out.keys()))
    return {"verdict": _VERDICT["v"], "how": "agreed", "why": "stub"}


async def _notice_stub(notice, percepts):
    return {"verdict": "not_sampled", "how": None}


lane2._coherence_check = _coherence_stub
lane2._judge_metaphor = _metaphor_stub
lane2._judge_notice = _notice_stub

_RANDOM_CALLS: list = []
_real_random = random.random
_FORCE = {"v": 0.99}      # 0.99 -> neither draw hits; 0.0 -> both hit; None -> the real seeded stream


def _counting_random():
    v = _FORCE["v"] if _FORCE["v"] is not None else _real_random()
    _RANDOM_CALLS.append(v)
    return v


FLAGGED = "The sounds around me are a symphony of nature."
PLAIN = "The air is warm and the light is dim."


async def run_tick(notice: str) -> dict:
    _generator_says(notice)
    return await lane2.tick()


async def main():
    random.random = _counting_random
    try:
        # A: unsampled + unflagged -> not judged, shape unchanged
        _FORCE["v"] = 0.99
        _METAPHOR_CALLS.clear()
        ra = await run_tick(PLAIN)
        check("A1 unsampled, unflagged tick: judge NOT called", _METAPHOR_CALLS == [])
        check("A2 its metaphor_judged is the old not_sampled shape (no arm key)",
              (ra or {}).get("metaphor_judged") == {"verdict": "not_sampled", "how": None}, str((ra or {}).get("metaphor_judged")))

        # B: unsampled + flagged -> judged on the flag arm, blind
        _METAPHOR_CALLS.clear(); _METAPHOR_SEES.clear()
        rb = await run_tick(FLAGGED)
        mjb = (rb or {}).get("metaphor_judged") or {}
        check("B1 unsampled, flagged tick: judge called exactly once", len(_METAPHOR_CALLS) == 1, str(_METAPHOR_CALLS))
        check("B2 its metaphor_judged carries arm == 'flag' and the verdict", mjb.get("arm") == "flag" and mjb.get("verdict") == "literal", str(mjb))
        check("B3 the judge stayed blind: it received only the output fields, never the flags",
              _METAPHOR_SEES and all("metaphor_flags" not in k and "figurative_flags" not in k for k in _METAPHOR_SEES), str(_METAPHOR_SEES))
        check("B4 the tick row still logs its own flags", (rb or {}).get("figurative_flags") == ["symphony"], str((rb or {}).get("figurative_flags")))

        # B5: a metaphor-flag (not figurative) tick is also caught
        _METAPHOR_CALLS.clear()
        rb2 = await run_tick("A calm before the journey ahead.")
        check("B5 a _metaphor_flags-only tick is judged on the flag arm too",
              len(_METAPHOR_CALLS) == 1 and ((rb2 or {}).get("metaphor_judged") or {}).get("arm") == "flag")

        # C: sampled -> random arm, judged once (flagged or not)
        _FORCE["v"] = 0.0
        for label, txt in (("flagged", FLAGGED), ("plain", PLAIN)):
            _METAPHOR_CALLS.clear()
            rc = await run_tick(txt)
            check(f"C1 sampled {label} tick: judged ONCE (no double judging), arm 'random'",
                  len(_METAPHOR_CALLS) == 1 and ((rc or {}).get("metaphor_judged") or {}).get("arm") == "random",
                  str((rc or {}).get("metaphor_judged")))

        # D: the random draws are identical to the pre-J-3117 order: same count, same values, flagged or not
        seqs = {}
        for label, txt in (("flagged", FLAGGED), ("plain", PLAIN)):
            _FORCE["v"] = None
            random.seed(20261106)
            _RANDOM_CALLS.clear()
            await run_tick(txt)
            seqs[label] = list(_RANDOM_CALLS)
        check("D1 flagged vs plain consume the same random numbers in the same order (flag arm draws nothing)",
              seqs["flagged"] == seqs["plain"] and len(seqs["plain"]) >= 2, str(seqs))
        random.seed(20261106)
        d0, d1 = _real_random(), _real_random()
        check("D2 the first two draws are exactly the seeded stream (notice then metaphor, nothing inserted before)",
              seqs["plain"][0] == d0 and seqs["plain"][1] == d1, f"{seqs['plain'][:2]} vs {[d0, d1]}")
    finally:
        random.random = _real_random
        _FORCE["v"] = 0.99

    # E: status() ignores the flag arm in every comparable rate, and reports its own counts
    ticks = []
    def _t(i, mj):
        ticks.append({"kind": "tick", "ts": 1.7e9 + i, "model": "deepseek-r1:7b", "notice": "x", "metaphor_judged": mj,
                      "metaphor_flags": [], "figurative_flags": []})
    _t(0, {"verdict": "literal", "how": "agreed", "arm": "random"})
    _t(1, {"verdict": "literal", "how": "agreed"})                       # legacy row: no arm key == random
    _t(2, {"verdict": "metaphor", "how": "tiebreak", "arm": "flag"})
    _t(3, {"verdict": "metaphor", "how": "agreed", "arm": "flag"})
    _t(4, {"verdict": "not_sampled", "how": None})
    _t(5, {"verdict": "not_sampled", "how": None})
    with open(lane2._LOG, "w", encoding="utf-8") as fh:
        for r in ticks:
            fh.write(json.dumps(r) + "\n")
    st = lane2.status()
    check("E1 metaphor_leak_rate_judged ignores the flag arm (0 metaphor of 2 random-arm verdicts)", st.get("metaphor_leak_rate_judged") == 0.0, str(st.get("metaphor_leak_rate_judged")))
    check("E2 metaphor_flag_arm_n == 2 and metaphor_flag_arm_metaphor == 2", st.get("metaphor_flag_arm_n") == 2 and st.get("metaphor_flag_arm_metaphor") == 2,
          f"{st.get('metaphor_flag_arm_n')} {st.get('metaphor_flag_arm_metaphor')}")
    check("E3 metaphor_judge_coverage counts the random arm only (2 of 6)", st.get("metaphor_judge_coverage") == round(2 / 6, 3), str(st.get("metaphor_judge_coverage")))
    check("E4 tiebreak rate ignores the flag arm's tiebreak (0 of 2 random-arm rows)", st.get("metaphor_tiebreak_rate") == 0.0, str(st.get("metaphor_tiebreak_rate")))
    print("STATUS FIELDS:", {k: st.get(k) for k in ("metaphor_leak_rate_judged", "metaphor_judge_coverage", "metaphor_tiebreak_rate",
                                                    "metaphor_flag_arm_n", "metaphor_flag_arm_metaphor")})

    # F: constants unchanged, live data untouched, no real network
    check("F1 METAPHOR_JUDGE_SAMPLE_P is still 0.25", lane2.METAPHOR_JUDGE_SAMPLE_P == 0.25)
    check("F2 no non-loopback connect attempted", _NONLOCAL_CONNECTS == [], str(_NONLOCAL_CONNECTS))
    check("F3 live data stores untouched", _snap() == _LIVE_BEFORE)


try:
    asyncio.run(main())
finally:
    aiohttp.ClientSession = _REAL_SESSION
    socket.socket.connect = _real_connect
    shutil.rmtree(TMP, ignore_errors=True)

bad = [n for n, ok in CHECKS if not ok]
print(f"\n{len(CHECKS) - len(bad)}/{len(CHECKS)} checks passed")
sys.exit(1 if bad else 0)
