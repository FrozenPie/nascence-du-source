"""
Nascence — Symbol recurrence report (the Meaningfulness check)

Per tracked symbol: primed vs UNPRIMED appearance counts over time. UNPRIMED recurrence — the
symbol surfacing when nothing fed it — is the evidence of autonomous persistence (the symbolic
equivalent of external verification). This declares nothing significant; it shows the tally so
significance can be EARNED by the data, weeks apart, rather than asserted today.

Run:  python scripts/symbol_report.py
"""
import sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from core.symbol_tracker import symbol_report

r = symbol_report()
print("\n=== Symbol recurrence (Meaningfulness axis) ===")
if r.get("note"):
    print(" ", r["note"]); sys.exit(0)
for sym, d in sorted(r.items(), key=lambda kv: -kv[1]["unprimed"]):
    span_days = (d["last_ts"] - d["first_ts"]) / 86400 if d.get("first_ts") else 0
    print(f"  {sym:16} unprimed={d['unprimed']:4}  primed={d['primed']:4}  (over {span_days:.1f} days)")
print("\n  Only UNPRIMED, recurring across weeks in unrelated contexts, counts as earned meaning.\n")
