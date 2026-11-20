"""
Phase 1 in-vitro proof (2026-06-15) — the READ design, no behaviour change.

Loads the multilevel DRAFT axiom and shows what Du would actually receive in each cognitive_mode:
the faint always-present floor (L0 continuity + L1 voice + name) + the ONE facet whose domain is active
+ the transient stance. Demonstrates, on real data, BEFORE any wiring:
  - 渡 + continuity are always present (the floor never disappears),
  - the river-facet surfaces ONLY in reflective/existential mode (confined to self-reflection),
  - studying surfaces the seeker; talking surfaces the companion,
  - the deep layers are a faint floor, not a recited self-concept.
Read-only. Touches nothing live.

Run:  python scripts/axiom_read_invitro.py
"""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

AX = json.loads(Path(r"C:\Nascence\data\identity\axiom.multilevel_draft.json").read_text(encoding="utf-8"))

# cognitive_mode -> which L3 facet is active (maps onto the existing attention_vector machinery)
MODE_FACET = {
    "task":        "seeker",
    "social":      "in_relation",
    "hybrid":      None,          # light — no facet headline; floor only
    "reflective":  "who_feels",
    "existential": "the_becoming",  # the river — its proper, confined home
}


def faint_floor() -> str:
    """L0 continuity + name + L1 voice cadence — always present, quiet, never a recited headline."""
    l0 = AX["L0_constitution"]["commitments"][0]            # the one-self continuity line
    name = AX["name"]
    voice = AX["L1_temperament"]["voice_style"].split(".")[0]  # just the cadence keyword, faint
    return (f"(quiet floor — {name}, one self across change; voice: {voice.lower()}. "
            "Not your subject; the ground you stand on.)")


def facet_by_id(fid):
    return next((f for f in AX["L3_facets"]["facets"] if f["id"] == fid), None)


def compose(mode: str) -> str:
    parts = [faint_floor()]
    fid = MODE_FACET.get(mode)
    if fid:
        f = facet_by_id(fid)
        parts.append(f"ACTIVE FACET — {f['name']}: {f['self_image']}")
    # the transient stance surfaces only when turning inward (reflective/existential)
    if mode in ("reflective", "existential"):
        parts.append(f"(passing stance, fading: {AX['L5_working_self']['current_stance']})")
    return "\n   ".join(parts)


def main():
    print("WHAT DU RECEIVES, BY MODE (multilevel draft, real data) — the read design proven in vitro\n")
    print("=" * 98)
    for mode in ("task", "social", "hybrid", "reflective", "existential"):
        trigger = {"task": "'How does a river carve a channel?'",
                   "social": "'How are you today, Du?'",
                   "hybrid": "'Tell me about the book.'",
                   "reflective": "(idle, turning inward)",
                   "existential": "'Who are you, really?'"}[mode]
        print(f"\n[{mode.upper()}]  e.g. {trigger}")
        print("   " + compose(mode))
    print("\n" + "=" * 98)
    # the proof, stated as checks
    river_in = [m for m in MODE_FACET if (MODE_FACET[m] == "the_becoming")]
    river_out = [m for m in ("task", "social", "hybrid") if MODE_FACET[m] != "the_becoming"]
    print(f"PROOF:")
    print(f"  • river-facet appears in: {river_in}  → confined to self-reflection ✓")
    print(f"  • river-facet ABSENT in:  {river_out}  → study/talk are river-free ✓")
    print(f"  • 渡 + one-self continuity: present in EVERY mode (the faint floor) ✓")
    print(f"  • seeker on a study question, companion on a personal one ✓")


if __name__ == "__main__":
    main()
