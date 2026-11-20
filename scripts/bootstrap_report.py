"""
Nascence — Bootstrap report (the Phase C gate)

Reads the Phase A accuracy observations + Phase B stability observations, joins them by cycle_id,
and reports whether stability predicts accuracy on the items where we have BOTH. The gap between
"stable & correct" and "stable & wrong" is the systematic-error blind spot, quantified.

Run any time:  python scripts/bootstrap_report.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from core.competence import bootstrap_report

r = bootstrap_report()
print("\n=== Nascence epistemics bootstrap ===")
print(f"  accuracy observations : {r['n_accuracy_obs']}")
print(f"  {r['n_tier4_excluded']} tier4_user excluded (old substring detector, pre-J-3106 restart)")
print(f"  stability observations: {r['n_stability_obs']}")
print(f"  paired (both, by cycle): {r['n_pairs']}")
if r["n_pairs"]:
    print(f"  mean stability when CORRECT  : {r.get('mean_stability_when_correct')}")
    print(f"  mean stability when INCORRECT: {r.get('mean_stability_when_incorrect')}")
    print(f"  correct − incorrect stability: {r.get('correct_minus_incorrect_stability')}")
    print(f"  pearson(stability, accuracy) : {r.get('pearson_stability_vs_accuracy')}")
print(f"\n  VERDICT: {r['verdict']}\n")
