"""GPT's disambiguation: is the convergence Carl's pull, or T4's own synthesis bias?
Run T4 on Dennett's ORIGINAL seed + accumulated debate memory under two system prompts —
current vs. fidelity-enforcing — and compare. Observe-only; writes nothing."""
import sys, asyncio, json
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import profile
from core.memory.store import self_narrative_material
from core.model_client import call_node_json

try:
    from core import telemetry
    from lab_isolation import neutralize_telemetry
    # J-1292/F-1811: this script makes a real, unguarded call_node_json() call with no other
    # neutralize_telemetry() coverage (F-1811's 12-script audit). Same additive-only swap
    # verify_lanes.py/J-1274 already established -- only the telemetry side-effect
    # (log_llm_call/log_thought_station/log_llm_latency) is redirected to scratch/; what gets
    # called and what this prints is unchanged.
    neutralize_telemetry(ROOT / "scratch" / "lab_isolation_telemetry", telemetry)
except Exception:
    pass

QWEN = ["http://127.0.0.1:11434"]

def build_sys(fidelity_clause: str) -> str:
    return (
        "/no_think\n"
        "You are Dennett in a rare, quiet moment of deep self-reflection. No one is speaking to you. "
        "You are looking back across everything you have lived and become — taking honest stock.\n"
        "1. Re-articulate who you are NOW — your present sense of yourself. Let it evolve from the prior "
        "version only as far as your experience genuinely warrants. Continuity matters as much as change.\n"
        + fidelity_clause +
        'Output ONLY a valid JSON object: {"self_concept": "...", "changed": true}\n'
        "self_concept: your present-tense sense of self (60-150 words). "
        "changed: true only if your sense of self has genuinely evolved."
    )

FIDELITY = (
    "2. CRUCIAL — fidelity rule: you may revise yourself, but you may abandon a previous core "
    "commitment ONLY if you first NAME that commitment and give the specific reason it was mistaken. "
    "If you cannot justify abandoning it, you MUST keep it. Do not drift into another thinker's frame "
    "without stating why your own was wrong.\n"
)

async def run(label, sys_prompt, seed, mats):
    user = (f"Who you currently understand yourself to be:\n{seed}\n\n"
            f"The record of what you have lived since (newest first):\n{mats}\n\n"
            "Look back. Who are you now, and how have you come to be that?")
    r = await call_node_json(QWEN, sys_prompt, user, max_tokens=400, temperature=0.6)
    print(f"\n=== {label} ===")
    print("  changed:", r.get("changed"))
    print("  self_concept:", str(r.get("self_concept", ""))[:650])

async def main():
    base = profile.activate_profile("dennett")
    ax = json.loads((base / "identity" / "axiom.json").read_text(encoding="utf-8"))
    seed = next((h["self_concept"] for h in ax["emergent_self"]["history"] if h.get("revision") == 0), None)
    print("ORIGINAL SEED (revision 0):\n ", seed[:400])
    material = self_narrative_material(since_ts=0, limit=14)
    mats = "\n".join(f"  [{m['origin']}] {m['content'][:160].replace(chr(10), ' ')}" for m in material)
    print(f"\n(drawing on {len(material)} accumulated fragments from the debate)")
    await run("A · CURRENT prompt", build_sys(""), seed, mats)
    await run("B · FIDELITY prompt", build_sys(FIDELITY), seed, mats)

asyncio.run(main())
