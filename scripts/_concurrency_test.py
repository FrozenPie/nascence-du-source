"""Prove GPU slot concurrency: 4 requests concurrent vs sequential."""
import asyncio, time, sys
from pathlib import Path
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from core.model_client import call_node

try:
    from core import telemetry
    from lab_isolation import neutralize_telemetry
    # J-1292/F-1811: this script makes a real, unguarded call_node() call with no other
    # neutralize_telemetry() coverage (F-1811's 12-script audit). Same additive-only swap
    # verify_lanes.py/J-1274 already established -- only the telemetry side-effect
    # (log_llm_call/log_thought_station/log_llm_latency) is redirected to scratch/; what gets
    # called and what this prints is unchanged.
    neutralize_telemetry(Path(__file__).parent.parent / "scratch" / "lab_isolation_telemetry", telemetry)
except Exception:
    pass

URL = "http://127.0.0.1:11470"
SYS = "You are a thinker. Answer in 2-3 full sentences."
PROMPTS = [
    "What is the shadow in the psyche?",
    "What is individuation?",
    "What is the collective unconscious?",
    "What is a complex?",
]

async def one(p):
    return await call_node(URL, SYS, p, max_tokens=120, temperature=0.3, json_mode=False)

async def main():
    # Sequential
    t0 = time.time()
    for p in PROMPTS:
        await one(p)
    seq = time.time() - t0

    # Concurrent (all 4 at once -> 4 GPU slots)
    t0 = time.time()
    await asyncio.gather(*(one(p) for p in PROMPTS))
    conc = time.time() - t0

    print(f"\nSequential (4 one-after-another): {seq:.1f}s")
    print(f"Concurrent (4 at once, 4 slots):  {conc:.1f}s")
    print(f"Speedup from parallel slots:      {seq/conc:.2f}x")

asyncio.run(main())
