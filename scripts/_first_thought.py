"""One-shot: run a single thought cycle and dump every node's output.

J-1825 / F-2458: this is a read-only DIAGNOSTIC DUMP, so it now boots Du in a throwaway
'_first_thought' profile (like scripts/smoke_test.py's '_smoke') instead of against the real
data/ tree and memory DB. Before this, main() built an Orchestrator and ran a human cycle with no
activate_profile(), no isolation and no mark_live() -- every run wrote Du's real stores (the 13+
paths in F-2458) and added a fake exchange to his real founder-conversation log. The real identity
(data/identity/axiom.json) is READ and copied into the throwaway profile; nothing real is written.
"""
import asyncio, json, shutil, sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from dataclasses import asdict
from core.schema import CognitiveState
from core.orchestrator import Orchestrator
from core.memory.store import init_db
import run_nascence

try:
    from core import telemetry
    from lab_isolation import neutralize_telemetry
    # J-1308/F-1844 (4th-round lab_isolation sweep): this script's own orch.run_cycle() below reaches
    # core.model_client.call_node() only INDIRECTLY, through the full node pipeline (self_interrogation,
    # decomposed_critic, librarian, peers, etc.) -- invisible to every earlier round's own literal
    # "call_node(" grep against this file. Only THIS script's own telemetry side-effect (log_llm_call/
    # log_thought_station/log_llm_latency, all three written by call_node()) is redirected into scratch/,
    # same pattern verify_lanes.py/J-1274 established -- changes nothing about what the cycle does.
    neutralize_telemetry(Path(__file__).parent.parent / "scratch" / "lab_isolation_telemetry", telemetry)
except Exception:
    pass

PROFILE_NAME = "_first_thought"
ROOT = Path(__file__).parent.parent


def activate_throwaway_profile() -> Path:
    """Point every per-agent data/ constant at data/profiles/_first_thought and seed its axiom
    from the real one (the scripts/smoke_test.py recipe). Called from main(), not at import, so
    merely importing this module touches nothing. Returns the profile dir."""
    from core.profile import activate_profile
    prof = Path(activate_profile(PROFILE_NAME))
    src = ROOT / "data" / "identity" / "axiom.json"
    if not src.exists():
        raise SystemExit(
            f"_first_thought: no identity seed at {src} -- data/ is gitignored, so a fresh checkout "
            f"or worktree has none. Seed data/identity/axiom.json first (copy it from a tree that "
            f"has one).")
    dst = prof / "identity" / "axiom.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    # J-4353 / F-5105: modules activate_profile() does not rebase (companion, intentions, left_lane, ...)
    from lab_human_cycle_paths import rebase_human_cycle_paths
    rebase_human_cycle_paths(prof)
    return prof


PROMPT = sys.argv[1] if len(sys.argv) > 1 else \
    "Jung, do you believe you are conscious?"


async def main():
    # MUST come before init_db()/Orchestrator(): it rebases store.DB_PATH and the per-agent logs.
    activate_throwaway_profile()
    init_db()
    name, axiom = run_nascence.load_identity()
    state = CognitiveState(spirit_name=name, axiom=axiom)
    nodes = run_nascence.build_nodes()
    orch = Orchestrator(state=state, nodes=nodes)

    print("\n" + "=" * 70)
    print(f"INPUT: {PROMPT}")
    print("=" * 70)

    response = await orch.run_cycle(PROMPT, input_type="human")

    def show(label, obj):
        print(f"\n--- {label} ---")
        if obj is None:
            print("  (none)")
            return
        try:
            print(json.dumps(asdict(obj), indent=2, ensure_ascii=False))
        except Exception:
            print(f"  {obj}")

    show("PERCEPTION", state.perception)
    show("EMOTION", state.emotion)
    show("SALIENCE", state.salience)
    show("MEMORY ROUTER", state.memory_keys)
    print(f"\n--- MEMORY FRAGMENTS RETRIEVED: {len(state.memory_fragments)} ---")
    show("REFLECTION", state.reflection)
    show("CRITIC", state.critic)
    show("EXECUTIVE", state.executive)
    show("VOICE", state.voice)

    print("\n" + "=" * 70)
    print(f"FINAL RESPONSE:\n{response}")
    print("=" * 70)

    await orch.stop_background()


if __name__ == "__main__":
    asyncio.run(main())
