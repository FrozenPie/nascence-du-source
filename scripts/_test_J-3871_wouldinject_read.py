"""J-3871: verdict() on stubbed reports (pure; touches no data/ store)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import symbol_tier2_wouldinject as t2
assert Path(t2.__file__).resolve().is_relative_to(Path(__file__).resolve().parent.parent)
from scripts.symbol_tier2_wouldinject_read import verdict

assert verdict({"note": "x"}, [])["verdict"] == "NO-DATA"
def rep(n, h, s): return {"a": {"count": n}, "_totals": {"events": n, "verbatim_recurrence_hits": h, "span_days": s}}
assert verdict(rep(10, 0, 1.0), [])["verdict"] == "INSUFFICIENT"
assert verdict(rep(300, 5, 4.0), [])["verdict"] == "RECURRENCE-HITS"
r = verdict(rep(300, 0, 4.0), [{"tablet_id": "t", "gates": {"drift_health": "unknown"}, "tension_axis": {"axis": "none"}}])
assert r["verdict"] == "CLEAN-NEEDS-HUMAN-READ" and len(r["reasons"]) == 3, r
assert "write-on-hit" in " ".join(verdict(rep(300, 300, 4.0), [])["reasons"])
print("ok")
