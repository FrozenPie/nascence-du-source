"""Fire T4 self-authoring for both debate agents on the contradiction pressure the 300-turn
debate loaded. Forces the rewrite onto qwen (11434), bypasses the interval gate, reports
before/after self_concept. This is the trigger the debate harness left cocked (it ran T1/T2
only, never T4)."""
import sys, asyncio, json
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import profile, tension_ledger
from core.schema import CognitiveState
from core.memory.store import self_narrative_material
from nodes.subconscious_node import SubconsciousNode
import run_nascence as rn

QWEN = ["http://127.0.0.1:11434"]   # force the capable model for the identity rewrite


async def fire(name: str):
    base = profile.activate_profile(name)
    rn.AXIOM_PATH = base / "identity" / "axiom.json"
    axp = base / "identity" / "axiom.json"

    before = json.loads(axp.read_text(encoding="utf-8"))["emergent_self"]
    spirit_name, axiom = rn.load_identity()
    state = CognitiveState(spirit_name=spirit_name, axiom=axiom)

    node = SubconsciousNode()           # loads this profile's subconscious_state.json (debate tensions)
    node.base_urls = QWEN
    node._state["last_self_authoring"] = 0   # bypass the 1h interval gate — force the attempt

    cp = tension_ledger.contradiction_pressure_for(node._state.get("tensions", []))
    material = self_narrative_material(since_ts=0, limit=14)
    print(f"\n=== {name} ===")
    print(f"  contradiction_pressure: {cp}   self-narrative fragments: {len(material)}")
    print(f"  revision_count (before): {before.get('revision_count')}")
    if len(material) < 1:
        print("  no material — skip"); return

    await node._t4_self_authoring(state, material)

    after = json.loads(axp.read_text(encoding="utf-8"))["emergent_self"]
    changed = (after.get("revision_count") != before.get("revision_count")
               or after.get("self_concept") != before.get("self_concept"))
    print(f"  revision_count (after):  {after.get('revision_count')}   CHANGED: {changed}")
    if changed:
        print(f"  NEW self_concept:\n    {after.get('self_concept','')[:600]}")
        arc = after.get("self_narrative_arc", [])
        if arc:
            print(f"  NEW arc entry:\n    {arc[-1].get('arc_entry','')[:400]}")
    else:
        print("  unchanged — echo guard held or the model regenerated the same self.")


async def main():
    rn.prewarm()
    for nm in ("carl", "dennett"):
        try:
            await fire(nm)
        except Exception as e:
            import traceback
            print(f"  ERROR firing {nm}: {e}\n{traceback.format_exc()[:1500]}")

asyncio.run(main())
