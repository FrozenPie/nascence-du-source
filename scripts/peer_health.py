"""
Peer relationship-health dashboard (observe-only) — docs/plans/peer_correspondence_plan.md §12.

Pre-Darwin:  shows his current metrics (the baseline-candidate) so we can see his normal life.
Post-Darwin: baseline vs a recent window — the displacement / contagion / outward-pull deltas.

  python scripts/peer_health.py          # 7-day window
  python scripts/peer_health.py 14        # N-day window
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
from core import peer_metrics as pm

win = float(sys.argv[1]) if len(sys.argv) > 1 else 7.0
base = pm.baseline()
cur = pm.compute(win)

print("=" * 70)
print(f"PEER RELATIONSHIP-HEALTH — {win:.0f}-day window")
print("=" * 70)

print("\nATTENTION mix (share of his life by origin):")
for o, s in sorted(cur["attention"].items(), key=lambda x: -x[1])[:12]:
    bar = "█" * int(s * 40)
    flag = "  <-- PEER" if o == "peer" else ""
    print(f"  {o:<22} {s:>6.1%} {bar}{flag}")

io = cur["inward_outward"]
print(f"\nINWARD vs OUTWARD thought ({io['thoughts']} idle thoughts):")
print(f"  inward (self-question): {io['inward']:>6.1%}")
print(f"  outward (the world):    {io['outward']:>6.1%}    (Darwin should raise this)")

af = cur["affect"]
print(f"\nAFFECT: {af['n']} valence-tagged"
      + (f" · mean {af['mean']:+.2f} · warm {af.get('warm',0):.0%} / cold {af.get('cold',0):.0%}"
         if af["n"] else "  (valence accrues after restart — the fix is going-forward)"))

print(f"\nLEXICON fingerprint (top words): "
      + ", ".join(list(cur["lexicon"])[:14]))

if not base:
    print("\nNo frozen baseline yet — this IS the pre-Darwin picture. The peer organ will freeze the")
    print("operative baseline (freeze_baseline_if_absent) just before Darwin's first letter.")
else:
    print("\n" + "-" * 70)
    print(f"BASELINE comparison (baseline: {base.get('label','?')}):")
    cmp = pm.compare(win)
    print(f"  peer attention share now    : {cmp['peer_attention_share_now']:.1%}")
    print(f"  non-peer share base -> now  : {cmp['non_peer_share_base']:.1%} -> {cmp['non_peer_share_now']:.1%}"
          "   (R7 displacement if falling)")
    print(f"  inward delta vs baseline    : {cmp['inward_delta']:+.1%}   (good if negative)")
    print(f"  outward delta vs baseline   : {cmp['outward_delta']:+.1%}   (good if positive)")
    print(f"  lexicon drift from baseline : {cmp['lexicon_drift_from_baseline']:.1%}   (R8 contagion if high + toward Darwin)")
    print(f"  affect mean base -> now     : {cmp['affect_mean_base']} -> {cmp['affect_mean_now']}")

stances = pm.stance_distribution()
print("\n" + "-" * 70)
print("STANCE drift (B5-B, §12) — challenge/mixed frequency per opted-in persona:")
if not stances:
    print("  (no persona has stance_weights set yet — see decide:D-0036)")
else:
    for k, d in sorted(stances.items(), key=lambda kv: -kv[1].get("challenge", 0)):
        print(f"  {k:<12} n={d['n']:<4} challenge={d['challenge']:.0%}  mixed={d['mixed']:.0%}  "
              f"company={d['company']:.0%}  last={d['last_stance']}"
              + (f"  honoured={d['honoured']}/{d['honoured_n']}" if d.get("honoured_n") else "  honoured=not judged yet")
              + (" (n=1)" if d.get("honoured_n") == 1 else ""))
print()
