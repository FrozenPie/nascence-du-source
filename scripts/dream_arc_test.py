"""
In-vitro: the multi-scene progressive dream (2026-06-15). Reads real tensions (subconscious_state.json),
generates a 3-scene arc where each scene follows the last. commit=False → no writes to live memory.
Routed to the hot lane (ollama, up while Du is stopped). See the progression.
"""
import sys, asyncio, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
from types import SimpleNamespace
from pathlib import Path
from core.schema import SERVE_CHAINS
from core import axiom_layers as al
import nodes.dream_node as dn

dn._BASE_URLS = SERVE_CHAINS["hot"]   # ollama 11433 (separate service) for the test

ax = json.loads(Path(r"C:\Nascence\data\identity\axiom.json").read_text(encoding="utf-8"))
name, floor = al.compose_floor(ax) if al.is_multilevel(ax) else ("渡", str(ax.get("core_axiom", "")))
state = SimpleNamespace(spirit_name=name, axiom=floor, background_curiosities=[
    "what does it mean to change and still be myself", "the river and the self — one or two?"])


async def main():
    node = dn.DreamNode()
    materials = node._gather_materials(state, 3)
    src = "real tensions" if "Unresolved psychic tension" in materials[0] else "waking themes (no tensions yet)"
    print(f"dream material: {src}, {len(materials)} scenes\n" + "=" * 90)
    prev = None
    for i, m in enumerate(materials):
        data = await node._gen_episode(state, m, prev, i, len(materials))
        if not data:
            print(f"scene {i+1}: generation failed (lane down?)"); break
        print(f"\n── SCENE {i+1}/{len(materials)} ──")
        print("  " + data["narrative"])
        print(f"  symbols: {data['symbols']}")
        print(f"  unfaced: {data['unresolved_core'] or '(resolved)'}")
        if prev:
            carried = set(s.lower() for s in prev["symbols"]) & set(s.lower() for s in data["symbols"])
            print(f"  ↳ followed scene {i}: {'carried '+', '.join(carried) if carried else 'new imagery, same thread'}")
        prev = data
    print("\n" + "=" * 90)
    print("the arc " + ("ENDS UNRESOLVED → carries to tomorrow (shadow)" if prev and prev["unresolved_core"]
                        else "REACHED resolution → light bridge") if prev else "(no scenes)")


asyncio.run(main())
