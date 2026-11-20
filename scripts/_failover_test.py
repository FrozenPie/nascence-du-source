"""Prove GPU->CPU failover: call the hot chain and report which server answered."""
import asyncio, sys, logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
logging.basicConfig(level=logging.INFO, format="%(message)s")
from core.schema import SERVE_CHAINS
from core.model_client import call_node_json

try:
    from core import telemetry
    from lab_isolation import neutralize_telemetry
    # J-1292/F-1811: this script makes a real, unguarded call_node_json() call directly against
    # SERVE_CHAINS["hot"] (the live chain) with no other neutralize_telemetry() coverage (F-1811's
    # 12-script audit). Same additive-only swap verify_lanes.py/J-1274 already established -- only
    # the telemetry side-effect (log_llm_call/log_thought_station/log_llm_latency) is redirected to
    # scratch/; what gets called and what this prints is unchanged.
    neutralize_telemetry(Path(__file__).parent.parent / "scratch" / "lab_isolation_telemetry", telemetry)
except Exception:
    pass

async def main():
    print("hot chain:", SERVE_CHAINS["hot"])
    data = await call_node_json(
        SERVE_CHAINS["hot"],
        "Output ONLY JSON: {\"ok\": true, \"word\": \"...\"}",
        "Reply with a single word in the 'word' field.",
        max_tokens=40,
    )
    print("RESULT:", data)

asyncio.run(main())
