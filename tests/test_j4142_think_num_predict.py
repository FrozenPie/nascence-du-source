"""J-4142 (F-4964): think=true calls on the ollama-native lanes get num_predict >= 4096.

Offline: no model server, no network, no data/ writes (telemetry modules are stubbed, aiohttp is faked).
Run from the tree under test:  python tests/test_j4142_think_num_predict.py
"""
import asyncio
import os
import sys
import types

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

# Stub the telemetry writers BEFORE core.model_client imports them lazily (no data/ writes).
_tel = types.ModuleType("core.telemetry")
_tel.log_llm_call = lambda *a, **k: None
_tel.log_thought_station = lambda *a, **k: None
_tel.log_llm_latency = lambda *a, **k: None
_sts = types.ModuleType("core.speech_timing_shadow")
_sts.log_call = lambda *a, **k: None

import core  # noqa: E402
assert os.path.abspath(core.__file__).startswith(HERE), core.__file__
sys.modules["core.telemetry"] = _tel
sys.modules["core.speech_timing_shadow"] = _sts
core.telemetry = _tel
core.speech_timing_shadow = _sts

from core import model_client as mc  # noqa: E402

HOT = "http://localhost:11433"

# --- the helper ---------------------------------------------------------------------------------
assert mc._think_num_predict(512, HOT, 0) == 6000                     # short prompt: full target
assert mc._think_num_predict(512, HOT, 3000) == 6000                  # ~1000 tok prompt still fits 6000
n = mc._think_num_predict(512, HOT, 6000)                             # ~2000 tok prompt: clamped to window
assert n == 8192 - 2000 - 256, n
assert mc._think_num_predict(512, HOT, 30000) == 4096                 # huge prompt: never below the floor
assert mc._think_num_predict(7000, "http://x:9999", 0) == 8192 - 256  # big caller budget: clamped to window
assert mc._think_num_predict("bad", HOT, 0) == 4096                   # fail-open to the floor
assert mc._think_num_predict(512, HOT, 0) >= mc._THINK_NUM_PREDICT_FLOOR


# --- call_node payload, via a fake aiohttp -----------------------------------------------------
captured = []


class _Resp:
    def raise_for_status(self): pass
    async def json(self): return {"message": {"content": "{\"ok\": 1}"}, "eval_count": 5}
    async def __aenter__(self): return self
    async def __aexit__(self, *e): return False


class _Session:
    def __init__(self, *a, **k): pass
    def post(self, url, json=None, timeout=None):
        captured.append((url, json, timeout))
        return _Resp()
    async def __aenter__(self): return self
    async def __aexit__(self, *e): return False


mc.aiohttp.ClientSession = _Session


async def _run():
    await mc.call_node(HOT, "sys", "user prompt", max_tokens=512, think=True)
    await mc.call_node(HOT, "sys", "user prompt", max_tokens=512, think=False)

asyncio.run(_run())
(u1, p1, t1), (u2, p2, t2) = captured
assert u1.endswith("/api/chat")
assert p1["think"] is True and p1["options"]["num_predict"] == 6000, p1["options"]
assert t1.total >= 240
assert p2["think"] is False and p2["options"]["num_predict"] == 512, p2["options"]
print("J-4142 think num_predict: all checks passed (think=6000, no-think=512 unchanged)")
