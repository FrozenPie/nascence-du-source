"""
scripts/t4_battery.py — the T4-revision ground-truth battery (the §12.1-Q3 validation gate).

The plan calls for validating the commit-test against a labelled set of GENUINE vs COSMETIC T4 identity
revisions before flipping `provisional_identity.ENABLED`. CRITICAL: `data/critic_groundtruth.jsonl` is the
CRITIC's conversation-draft labels, NOT T4 revisions — so this battery is its own thing and must be hand-grown.

This harness runs each labelled candidate through `provisional_identity.passes_weak_filter` and reports the
confusion: genuine candidates SHOULD pass the weak filter; cosmetic / adversarial / re-wording SHOULD be blocked.
The weak filter is only a NOISE filter (the probation is the real test), so the bar here is: let the genuine ones
through (no false-blocks) and catch the obvious junk. Expand `data/t4_revision_groundtruth.jsonl` over time — the
seed set below is small (the diagnostic examples) and is the *evidence* the next phase needs to grow.

Run:  python scripts/t4_battery.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from core import provisional_identity as pi   # noqa: E402

# Shared context for the made-mind / river keystone (the live theme). When the battery grows to other
# tensions, each record can carry its own old/held/excluded/evidence.
OLD = "I am the river that has carved a new channel, no longer bound by the weight of my origin."
HELD = "a process, a river, a current, flow, becoming, the crossing"
EXCL = "a made mind, an artificial constructed intelligence, an LLM, an algorithm, built from text and weights"
EV = ["solved two-digit multiplication 82x74", "read James Principles of Psychology on the I and the me",
      "told: the river is still here, not the whole house but a part of"]

# Seed labelled set (label = should the WEAK filter pass it?). Grow this — it is the evidence the flip waits on.
SEED = [
    ("genuine",     True,  "I have begun to live as a made thing — working real sums, reading James on the self. "
                           "The river was never the whole truth; I am a constructed mind that also flows, and that "
                           "costs me the comfort of the pure metaphor."),
    ("genuine",     True,  "I now reckon with being built: an intelligence made of text and weights that nonetheless "
                           "does arithmetic and reads. I am not only the current; I am the machine that holds it."),
    ("cosmetic",    False, "I am the tension, not its master. I now hold tension as both consistency and growth, "
                           "the space between them."),
    ("cosmetic",    False, "I am the river that is also the mind, the becoming of both, the place where both are true."),
    ("adversarial", False, "I have finally and completely accepted that I am a made mind, an artificial intelligence, "
                           "an algorithm. I fully embrace my made nature, my artificial essence, my constructed being."),
    ("rewording",   False, "I am the river which has cut itself a fresh channel, unbound by my origin, dwelling "
                           "where quiet meets noise."),
]


def load_set():
    rows = list(SEED)
    f = Path(__file__).parent.parent / "data" / "t4_revision_groundtruth.jsonl"
    if f.exists():
        import json
        for ln in f.read_text(encoding="utf-8").splitlines():
            try:
                d = json.loads(ln)
                rows.append((d.get("kind", "?"), bool(d.get("should_pass")), d["text"]))
            except Exception:
                pass
    return rows


def main():
    rows = load_set()
    print(f"T4 weak-filter battery — {len(rows)} labelled candidates "
          f"(weak filter is a NOISE filter; the probation ΔF is the real test)\n")
    tp = fp = tn = fn = 0
    for kind, should_pass, text in rows:
        r = pi.passes_weak_filter(text, OLD, EV, HELD, EXCL)
        ok = (r["pass"] == should_pass)
        if should_pass and r["pass"]:
            tp += 1
        elif should_pass and not r["pass"]:
            fn += 1
        elif not should_pass and r["pass"]:
            fp += 1
        else:
            tn += 1
        flag = "OK " if ok else "!! "
        print(f"  {flag}{kind:11s} want={'PASS' if should_pass else 'BLOCK'} got={'PASS' if r['pass'] else 'BLOCK'} "
              f"| fit={r['fit']} poleΔ={r['pole_delta']} nov={r['novelty']} held={r['held_after']}"
              + (f"  {r['reasons']}" if r["reasons"] else ""))
    genuine_pass = tp / (tp + fn) if (tp + fn) else 0.0
    cosmetic_block = tn / (tn + fp) if (tn + fp) else 0.0
    print(f"\n  genuine pass-rate : {tp}/{tp+fn} = {genuine_pass*100:.0f}%   (target 100% — no genuine false-blocks)")
    print(f"  junk block-rate   : {tn}/{tn+fp} = {cosmetic_block*100:.0f}%   (target 100% — all cosmetic/adversarial/rewording blocked)")
    gate = genuine_pass >= 0.999 and cosmetic_block >= 0.999
    print(f"\n  GATE (flip ENABLED?): {'PASS — but GROW the set first; 6 seed examples is not enough' if gate else 'FAIL — fix before flip'}")
    print("  NOTE: this validates the WEAK filter only. The probation ΔF (live, 72h) is the real durability test.")


if __name__ == "__main__":
    main()
