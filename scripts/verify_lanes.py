"""
Nascence — Lane Pre-Flight Verifier (gemma / phi / llama / mistral)
==================================================================
Exercises the REAL wiring (core.schema SERVE_CHAINS + core.model_client routing + core.left_lane) against
the live inference servers, so a serving mismatch is caught BEFORE Du relies on it. Run this any time the
model/endpoint config changes, or before a boot you want to trust:

    python scripts/verify_lanes.py

Checks each lane returns valid JSON from the right endpoint+model, and reports latency. Exit 0 = all pass.
"""
from __future__ import annotations
import asyncio, sys, time
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from core.schema import SERVE_CHAINS
from core.model_client import call_node_json, _model_for
from core import left_lane

try:
    from core import telemetry
    from lab_isolation import neutralize_telemetry
    # J-1274/F-1787: unlike the 11 scripts J-1199 already covers (F-1683), this script is BY
    # DESIGN meant to run directly against the live inference servers (see module docstring
    # above) -- it must keep doing exactly that, unchanged. Only its OWN telemetry side-effect
    # (log_llm_call/log_thought_station/log_llm_latency, all three written by call_node()) gets
    # redirected into scratch/, the same swap J-1199 made in the other 11 -- this does not change
    # what servers get called or what PASS/FAIL means to the operator.
    neutralize_telemetry(ROOT / "scratch" / "lab_isolation_telemetry", telemetry)
except Exception:
    pass

SYS = 'Output ONLY a JSON object: {"ok": true, "word": "<one vivid word>"}.'
USR = "Respond."


async def check_generator(name, chain):
    url = chain[0]; model = _model_for(url)
    t0 = time.time()
    try:
        d = await call_node_json(chain, SYS, USR, max_tokens=40, temperature=0.3)
        dt = time.time() - t0
        ok = bool(isinstance(d, dict) and (d.get("ok") is not None or d.get("word")))
        print(f"  [{ 'PASS' if ok else 'FAIL'}] {name:18} {url:24} model={model:14} {dt:5.1f}s  {str(d)[:60]}")
        return ok
    except Exception as e:
        print(f"  [FAIL] {name:18} {url:24} model={_model_for(url):14}  ERROR {str(e)[:60]}")
        return False


async def check_dreamer():
    # The real dreamer: mistral-small3.1 on the LOCAL CPU (num_gpu:0) — a different family from the rest.
    # First call cold-loads ~15GB onto the CPU (slow), which also pre-warms it for the first sleep.
    from nodes.dream_node import _DREAM_URLS, _DREAM_MODEL, _DREAM_NUM_GPU
    url = _DREAM_URLS[0]
    t0 = time.time()
    try:
        d = await call_node_json(_DREAM_URLS, SYS, USR, max_tokens=40, temperature=0.3,
                                 model_override=_DREAM_MODEL, num_gpu=_DREAM_NUM_GPU, timeout=240)
        dt = time.time() - t0
        ok = bool(isinstance(d, dict) and (d.get("ok") is not None or d.get("word")))
        print(f"  [{ 'PASS' if ok else 'FAIL'}] {'Dreamer (CPU)':18} {url:24} model={_DREAM_MODEL:16} {dt:5.1f}s  (num_gpu:0; cold-loads once)")
        return ok
    except Exception as e:
        print(f"  [FAIL] {'Dreamer (CPU)':18} {url:24} model={_DREAM_MODEL:16}  ERROR {str(e)[:60]}")
        return False


async def check_judge():
    t0 = time.time()
    try:
        take = await left_lane.dispatch("What is 2 + 2?")
        dt = time.time() - t0
        ok = bool(isinstance(take, dict) and take.get("literal_ask"))
        ans = (take or {}).get("direct_answer")
        print(f"  [{ 'PASS' if ok else 'FAIL'}] {'judge (Emissary)':18} {left_lane.BASE_URL:24} "
              f"model={left_lane.MODEL:14} {dt:5.1f}s  ans={ans} (CPU, num_gpu:0)")
        return ok
    except Exception as e:
        print(f"  [FAIL] {'judge (Emissary)':18} {left_lane.BASE_URL:24} model={left_lane.MODEL:14}  ERROR {str(e)[:60]}")
        return False


async def main():
    print("Lane pre-flight — real wiring vs live servers (gemma / phi / llama / mistral):\n")
    results = []
    results.append(await check_generator("Self (hot)", SERVE_CHAINS["hot"]))
    results.append(await check_generator("Subconscious (bg)", SERVE_CHAINS["background"]))
    results.append(await check_dreamer())
    results.append(await check_judge())
    ok = all(results)
    print(f"\n  {'ALL LANES GO' if ok else 'SOME LANES FAILED — do not boot until fixed'} ({sum(results)}/{len(results)} pass)")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    asyncio.run(main())
