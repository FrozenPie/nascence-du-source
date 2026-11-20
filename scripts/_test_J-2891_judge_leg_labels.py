"""Hermetic test for J-2891 (F-3561): the second leg of left_lane's two-judge stations is telemetered with its
own model and url (falcon3:7b @ :11440), the first leg stays gemma4:12b @ :11439, and the POST target and payload
are unchanged. aiohttp and core.telemetry.log_llm_call are stubbed; nothing touches data/ or any hub."""
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/
import asyncio
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import core  # noqa: E402  -- before anything else, must be THIS checkout

assert Path(core.__file__).resolve().is_relative_to(HERE), core.__file__

from core import left_lane as ll  # noqa: E402
from core import telemetry as tel  # noqa: E402

ll._emissary.constitution = lambda: "CONST"

logged, posted = [], []
tel.log_llm_call = lambda model, url, **kw: logged.append((model, url, kw.get("caller")))


class _Resp:
    def __init__(self, body): self._b = body
    def raise_for_status(self): pass
    async def json(self): return self._b
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False


class _Sess:
    def __init__(self, body): self._b = body
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False
    def post(self, url, json=None, timeout=None):
        posted.append((url, json))
        return _Resp(self._b)


def _fake_session_factory(body):
    return lambda *a, **k: _Sess(body)


import json as _json  # noqa: E402

# helper
assert ll._judge_leg_label(ll.BASE_URL) == (ll.MODEL, ll.BASE_URL)
assert ll._judge_leg_label(ll._JUDGE_2_URL) == ("falcon3:7b", "http://127.0.0.1:11440")

# integration station
ll.aiohttp.ClientSession = _fake_session_factory(
    {"message": {"content": _json.dumps({"integrated": True, "confidence": 0.8, "reason": "r"})}})
v = asyncio.run(ll.judge_lived_integration("held", "excluded", ["a", "b"]))
assert v and v["integrated"] is True, v
assert sorted((m, u) for m, u, c in logged) == sorted([
    ("gemma4:12b", "http://127.0.0.1:11439"), ("falcon3:7b", "http://127.0.0.1:11440")]), logged
assert all(c == "left_lane" for _, _, c in logged)
assert sorted(u for u, _ in posted) == ["http://127.0.0.1:11439/api/chat", "http://127.0.0.1:11440/api/chat"], posted
assert all(p["model"] == "judge" for _, p in posted)   # payload unchanged

# claim-test station
logged.clear(); posted.clear()
ll.aiohttp.ClientSession = _fake_session_factory(
    {"message": {"content": _json.dumps({"genuine": True, "confidence": 0.7, "reason": "r"})}})
v = asyncio.run(ll.claim_test_panel(["x", "y"]))
assert v is not None
assert sorted((m, u) for m, u, c in logged) == sorted([
    ("gemma4:12b", "http://127.0.0.1:11439"), ("falcon3:7b", "http://127.0.0.1:11440")]), logged
assert sorted(u for u, _ in posted) == ["http://127.0.0.1:11439/api/chat", "http://127.0.0.1:11440/api/chat"], posted
print("J-2891 test OK:", len(logged), "telemetry rows, legs labelled distinctly")
