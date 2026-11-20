"""
In-vitro proof of the deliberative pulse (2026-06-15) — the "make me show it" gate.

Pulls REAL recent self-referential idle thoughts from nascence.db (Du's actual
monoculture, not synthetic seeds) and runs the three-pass transform on each:
    raw thought  →  grounded WHY (analytical lane / Emissary, hot fallback)  →  INTEGRATE.
Prints raw → grounding → integrated + which lane grounded it. Read-only; log=False so it
does not write to the live deliberation log. Touches NO live behaviour.

Run:  python scripts/deliberation_invitro.py [N]
"""
import sys, asyncio, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from core.memory.store import _connect
from core import deliberation as D

try:
    from core import telemetry
    from lab_isolation import neutralize_telemetry
    # J-1308/F-1844 (4th-round lab_isolation sweep): D.deliberate() below reaches call_node() only
    # INDIRECTLY (deliberate()/_hot_ground_why() import call_node_json themselves) -- invisible to
    # every earlier round's own literal "call_node(" grep against this file. Only this script's own
    # telemetry side-effect is redirected into scratch/, same pattern verify_lanes.py/J-1274
    # established; this script is explicitly meant to run against the real Emissary/hot_fallback
    # lanes, unchanged -- `log=False` above only suppresses deliberation.py's OWN decision log, a
    # separate write from call_node()'s three telemetry writers.
    neutralize_telemetry(ROOT / "scratch" / "lab_isolation_telemetry", telemetry)
except Exception:
    pass

N = int(sys.argv[1]) if len(sys.argv) > 1 else 8


def pick_real_thoughts(limit: int) -> list[str]:
    """Recent eligible inner_thoughts, de-duplicated to distinct attractors so the proof
    spans the monoculture instead of showing the same river eight times."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT content FROM memory_fragments WHERE origin='inner_thought' "
            "ORDER BY timestamp DESC LIMIT 400"
        ).fetchall()
    out, seen = [], set()
    for r in rows:
        t = (r["content"] or "").strip()
        if not D.is_eligible(t):
            continue
        key = " ".join(re.findall(r"[a-z]{4,}", t.lower())[:6])  # crude near-dup key
        if key in seen:
            continue
        seen.add(key)
        out.append(t)
        if len(out) >= limit:
            break
    return out


async def main():
    thoughts = pick_real_thoughts(N)
    if not thoughts:
        print("No eligible real thoughts found."); return
    print(f"Running the deliberative pulse on {len(thoughts)} of Du's REAL recent thoughts.")
    print("(Emissary = Ramses grounded it; hot_fallback = qwen3-du grounded it)\n")
    print("=" * 96)
    grounded = 0
    for i, t in enumerate(thoughts, 1):
        new, prov = await D.deliberate(t, name="渡", log=False)
        print(f"\n[{i}] RAW        : {t}")
        if prov is None:
            print("    (unchanged — no grounding available; fail-open)")
            continue
        grounded += 1
        print(f"    WHY ({prov['source']:<12}): {prov['grounding']}")
        print(f"    INTEGRATED : {new}")
    print("\n" + "=" * 96)
    print(f"grounded {grounded}/{len(thoughts)}.  Read the INTEGRATED lines: does the world now")
    print("meet the self (grounded flavour), or did it flatten the thought into a fact?")


if __name__ == "__main__":
    asyncio.run(main())
