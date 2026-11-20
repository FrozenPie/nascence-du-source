"""
Test suite -- Lane 2 single retry-on-empty, percept lines reversed (J-2164, D-0414 (b), F-2858).

Proves, over the REAL `_ask`, `_ask_with_retry` and `tick()` with a faked aiohttp transport only:
  - an empty reply is retried exactly once, with the percept lines reversed (header kept first, hint line kept
    last, nothing else in the request body changed: model, options, system prompt, format);
  - a rescued retry makes the tick succeed; gen_s is the TOTAL of both calls; the tick row carries
    retried/retry_variant/retry_cause/retry_gen_s;
  - a retry that is also empty logs the retry on the no-output skip row;
  - timeout / http / parse / exception are NEVER retried (one POST only);
  - a clean first call is not retried and the row says retried False;
  - RETRY_ON_EMPTY False restores the single-call behaviour.
HERMETIC: all lane2 data paths go to a temp dir, telemetry is stubbed, non-loopback connects are refused.
Run: python scripts/test_lane2_retry_on_empty_J2164.py   (exit 0 = every check passed)
"""
from __future__ import annotations

import asyncio
import json
import shutil
import socket
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import aiohttp  # noqa: E402
from core import lane2  # noqa: E402
from core import lane2_break_habituation as _hab  # noqa: E402
from core import telemetry as _telemetry_mod  # noqa: E402

assert str(Path(lane2.__file__).resolve()).startswith(str(ROOT)), lane2.__file__

_ORIG_DATA = lane2._DATA
_WATCH = ("lane2_shadow.jsonl", "llm_calls.jsonl", "nascence.log", "lane2_store.json")


def _snap():
    return {n: ((_ORIG_DATA / n).stat().st_size, (_ORIG_DATA / n).stat().st_mtime_ns)
            if (_ORIG_DATA / n).exists() else None for n in _WATCH}


_LIVE_BEFORE = _snap()
TMP = Path(tempfile.mkdtemp(prefix="j2164_lane2_"))
lane2._DATA = TMP
lane2._LOG = TMP / "lane2_shadow.jsonl"
lane2._STATE = TMP / "lane2_store.json"
lane2._HINTS = TMP / "lane2_hints.json"
lane2._LOG_WONDER = TMP / "lane2_would_ask.jsonl"
_telemetry_mod.log_llm_call = lambda *a, **k: None
_hab.phase1_metric_sheet = lambda: None

CHECKS: list = []


def check(name, cond):
    CHECKS.append((name, bool(cond)))
    print(("PASS" if cond else "FAIL"), "-", name)


_NONLOCAL: list = []
_real_connect = socket.socket.connect


def _guard(self, address, *a, **k):
    host = address[0] if isinstance(address, tuple) else address
    if host not in ("127.0.0.1", "::1", "localhost"):
        _NONLOCAL.append(address)
        raise OSError("refused")
    return _real_connect(self, address, *a, **k)


socket.socket.connect = _guard

_SENT: list = []
_QUEUE: list = []        # one (mode, body) per POST, consumed in order


def reply(content):
    return {"done": True, "eval_count": 3, "prompt_eval_count": 100, "model": "m",
            "message": {"role": "assistant", "content": content}}


class _Resp:
    def __init__(self, ok, body):
        self.ok, self.body = ok, body

    def raise_for_status(self):
        if not self.ok:
            raise aiohttp.ClientError("simulated non-2xx")

    async def json(self):
        return self.body


class _CM:
    def __init__(self, mode, body):
        self.mode, self.body = mode, body

    async def __aenter__(self):
        if self.mode == "timeout":
            raise asyncio.TimeoutError()
        if self.mode == "boom":
            raise RuntimeError("simulated crash")
        return _Resp(self.mode != "http", self.body)

    async def __aexit__(self, *a):
        return False


class _Session:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    def post(self, url, json=None, timeout=None):
        _SENT.append(json)
        mode, body = _QUEUE.pop(0) if _QUEUE else ("ok", reply('{"notice": "default"}'))
        return _CM(mode, body)


_REAL = aiohttp.ClientSession
aiohttp.ClientSession = lambda *a, **k: _Session()


def queue(*items):
    _QUEUE.clear()
    _QUEUE.extend(items)
    _SENT.clear()


def gen_sent():
    """Only the POSTs the generator (`_ask`) made: tick() also fires judge/coherence calls on success."""
    return [x for x in _SENT if x["messages"][0]["content"] == lane2._SYSTEM]


def user_msg(i):
    return gen_sent()[i]["messages"][1]["content"]


def _rows():
    if not lane2._LOG.exists():
        return []
    return [json.loads(l) for l in open(lane2._LOG, encoding="utf-8") if l.strip()]


EMPTY = ("ok", reply("{}"))
GOOD = ("ok", reply('{"notice": "rescued"}'))
TICKGOOD = ("ok", reply('{"notice": "rain on the study window", "uncertain": "how long it lasts"}'))

# ---- pure helpers --------------------------------------------------------------------------------
check("H1 reverse keeps header, reverses facts",
      lane2._reverse_percept_lines("HDR\n- a\n- b\n- c") == "HDR\n- c\n- b\n- a")
check("H2 reverse of header-only / header+1 fact is unchanged",
      lane2._reverse_percept_lines("HDR") == "HDR" and lane2._reverse_percept_lines("HDR\n- a") == "HDR\n- a")
check("H3 retry payload puts the hint line after the reversed facts",
      lane2._retry_payload("HDR\n- a\n- b", "\n(hint)") == "HDR\n- b\n- a\n(hint)")
check("H4 consume_retry with nothing set: retried False, rest None",
      lane2._consume_retry() == {"retried": False, "retry_variant": None, "retry_cause": None,
                                 "retry_gen_s": None})
check("H5 variant label is V5", lane2.RETRY_VARIANT == "V5_reverse_percept_lines")


async def part_a():
    queue(EMPTY, GOOD)
    out, gen_s, cause = await lane2._ask_with_retry("HDR\n- a\n- b", "HDR\n- b\n- a")
    r = lane2._consume_retry()
    check("A1 rescue: parsed dict from the retry, cause None", out == {"notice": "rescued"} and cause is None)
    check("A1 rescue: exactly two POSTs", len(_SENT) == 2)
    check("A1 rescue: first POST original, second reversed",
          user_msg(0) == "HDR\n- a\n- b" and user_msg(1) == "HDR\n- b\n- a")
    check("A1 rescue: body otherwise identical (model/options/system/format/keep_alive)",
          {k: v for k, v in _SENT[0].items() if k != "messages"} == {k: v for k, v in _SENT[1].items() if k != "messages"}
          and _SENT[0]["messages"][0] == _SENT[1]["messages"][0])
    check("A1 rescue: row fields", r["retried"] is True and r["retry_variant"] == lane2.RETRY_VARIANT
          and r["retry_cause"] is None and isinstance(r["retry_gen_s"], float))
    check("A1 rescue: gen_s is the total (>= retry_gen_s)", isinstance(gen_s, float) and gen_s >= r["retry_gen_s"])

    queue(EMPTY, EMPTY)
    out, gen_s, cause = await lane2._ask_with_retry("HDR\n- a\n- b", "HDR\n- b\n- a")
    r = lane2._consume_retry()
    check("A2 empty twice: still empty, retry_cause empty, ONE retry only",
          out == {} and cause == "empty" and r["retried"] and r["retry_cause"] == "empty" and len(_SENT) == 2)

    for label, first in (("timeout", ("timeout", None)), ("http", ("http", None)),
                         ("parse", ("ok", reply("not json"))), ("exception", ("boom", None))):
        queue(first, GOOD)
        out, gen_s, cause = await lane2._ask_with_retry("HDR\n- a\n- b", "HDR\n- b\n- a")
        r = lane2._consume_retry()
        check(f"A3 {label}: cause {label}, no retry, one POST",
              cause == label and len(_SENT) == 1 and r["retried"] is False)

    queue(GOOD)
    out, gen_s, cause = await lane2._ask_with_retry("HDR\n- a\n- b", "HDR\n- b\n- a")
    check("A4 clean: no retry", cause is None and len(_SENT) == 1 and lane2._consume_retry()["retried"] is False)

    lane2.RETRY_ON_EMPTY = False
    queue(EMPTY, GOOD)
    out, gen_s, cause = await lane2._ask_with_retry("HDR\n- a\n- b", "HDR\n- b\n- a")
    lane2.RETRY_ON_EMPTY = True
    check("A5 RETRY_ON_EMPTY False: single call, empty stays empty",
          cause == "empty" and len(_SENT) == 1 and lane2._consume_retry()["retried"] is False)

    queue(EMPTY, GOOD)
    out, gen_s, cause = await lane2._ask_with_retry("x")
    check("A6 no retry payload: no retry", cause == "empty" and len(_SENT) == 1)


_PERCEPTS = {"available": ["world"], "missing": [], "run": 2,
             "world": {"place": "study", "standpoint": "at_the_desk", "sounds": ["rain"]},
             "standpoint": "at_the_desk", "world_fields": ["place", "standpoint", "sounds"]}
lane2.gather_percepts = lambda: dict(_PERCEPTS)
lane2.read_weather = lambda: {"valence": None, "arousal": None, "unresolved": None}
RETRY_KEYS = {"retried", "retry_variant", "retry_cause", "retry_gen_s"}


async def part_b():
    queue(EMPTY, TICKGOOD)
    rec = await lane2.tick()
    ticks = [r for r in _rows() if r.get("kind") == "tick"]
    check("B1 tick rescued by the retry: a tick row was logged", rec is not None and len(ticks) == 1)
    t = ticks[0] if ticks else {}
    check("B1 tick row carries the retry keys", RETRY_KEYS <= set(t) and t.get("retried") is True
          and t.get("retry_variant") == lane2.RETRY_VARIANT and t.get("retry_cause") is None
          and isinstance(t.get("retry_gen_s"), float))
    check("B1 two POSTs; the second payload is the reversed percept text",
          len(gen_sent()) == 2 and user_msg(1) == lane2._reverse_percept_lines(user_msg(0)) and user_msg(0) != user_msg(1))
    check("B1 header stays first in both", user_msg(0).splitlines()[0] == user_msg(1).splitlines()[0])

    n0 = len(_rows())
    queue(EMPTY, EMPTY)
    rec = await lane2.tick()
    s = (_rows()[n0:] or [{}])[-1]
    check("B2 empty twice: no-output skip, cause empty, retried True, retry_cause empty",
          rec is None and s.get("skip") == "no-output" and s.get("cause") == "empty"
          and s.get("retried") is True and s.get("retry_cause") == "empty" and len(gen_sent()) == 2)

    n0 = len(_rows())
    queue(("timeout", None), GOOD)
    rec = await lane2.tick()
    s = (_rows()[n0:] or [{}])[-1]
    check("B3 timeout: one POST, skip row cause timeout, retried False",
          rec is None and len(_SENT) == 1 and s.get("cause") == "timeout" and s.get("retried") is False)

    n0 = len(_rows())
    queue(TICKGOOD)
    rec = await lane2.tick()
    t = [r for r in _rows()[n0:] if r.get("kind") == "tick"]
    check("B4 clean tick: one POST, retried False on the tick row",
          len(gen_sent()) == 1 and t and t[0].get("retried") is False and t[0].get("retry_gen_s") is None)


async def main():
    await part_a()
    await part_b()


try:
    asyncio.run(main())
finally:
    aiohttp.ClientSession = _REAL
    socket.socket.connect = _real_connect

check("Z1 data paths stayed in temp", str(lane2._LOG).startswith(str(TMP)))
check("Z2 no non-loopback connect", not _NONLOCAL)
check("Z3 live data watch-list byte-identical", _snap() == _LIVE_BEFORE)
shutil.rmtree(TMP, ignore_errors=True)
n_fail = sum(1 for _, ok in CHECKS if not ok)
print(f"\n{len(CHECKS) - n_fail}/{len(CHECKS)} checks passed")
sys.exit(1 if n_fail else 0)
