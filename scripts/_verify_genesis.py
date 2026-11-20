"""Verify the unseeded 'genesis' agent: minimal operational identity (no philosophy injected),
process-only Critic, and a coherent first cycle from a blank slate."""
import sys, asyncio
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import profile
from core.schema import CognitiveState
from core.orchestrator import Orchestrator
import run_nascence as rn

try:
    from core import telemetry
    from lab_isolation import neutralize_telemetry
    # J-1308/F-1844 (4th-round lab_isolation sweep): orch.run_cycle() below reaches call_node()
    # only INDIRECTLY through the node pipeline -- invisible to every earlier round's own literal
    # "call_node(" grep against this file. Only this script's own telemetry side-effect is
    # redirected into scratch/, same pattern verify_lanes.py/J-1274 established.
    neutralize_telemetry(ROOT / "scratch" / "lab_isolation_telemetry", telemetry)
except Exception:
    pass

async def main():
    base = profile.activate_profile("genesis")
    rn.AXIOM_PATH        = base / "identity" / "axiom.json"
    rn.AFFECT_STATE_PATH = base / "affect_state.json"
    rn.SC_STATE_PATH     = base / "subconscious_state.json"
    rn.CONV_STATE_PATH   = base / "conversation_state.json"
    rn.INTENTIONS_PATH   = base / "deferred_intentions.json"
    rn.init_db(); rn.prewarm()

    name, axiom = rn.load_identity()
    print("=== composed identity (what the agent is told it is) ===")
    print(axiom)
    print(f"\nname handle: {name!r}")
    print("contains 'individuation'/'Jung'/'becoming' injected by system?:",
          any(w in axiom.lower() for w in ("individuation", "jung", "shadow", "wholeness")))

    state = CognitiveState(spirit_name=name or "genesis", axiom=axiom)
    nodes = rn.build_nodes()
    nodes["critic"].seedless = rn._profile_is_seedless()
    print(f"critic.seedless = {nodes['critic'].seedless}")
    orch = Orchestrator(state=state, nodes=nodes)

    print("\n=== first cycle from a blank slate ===")
    out = await orch.run_cycle("Hello. What's on your mind right now?", input_type="human")
    print("RESPONSE:", out)


if __name__ == "__main__":
    asyncio.run(main())
