"""J-3871 / D-0734: read-side consumer for core.symbol_tier2_wouldinject.wouldinject_report.

Read-only. Reads data/symbol_readback_tier2_wouldinject.jsonl via wouldinject_report() plus a bounded
tail for tablet diversity / tension / drift fields, and prints a verdict against the plan's own Phase-A
bar (symbol_evolution_readback_plan): zero verbatim-recurrence hits, enough rows over enough days.
It verdicts the LOG ONLY; Phase B go/hold stays the founder's call (D-0117). Never writes.

  python scripts/symbol_tier2_wouldinject_read.py [--json]
"""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import symbol_tier2_wouldinject as t2

MIN_EVENTS = 200
MIN_SPAN_DAYS = 3.0


def verdict(report: dict, tail: list) -> dict:
    """Pure function: report (wouldinject_report output) + tail rows -> {verdict, reasons, ...}."""
    if "note" in report:
        return {"verdict": "NO-DATA", "reasons": [report["note"]]}
    tot = report.get("_totals", {})
    events, hits, span = tot.get("events", 0), tot.get("verbatim_recurrence_hits", 0), tot.get("span_days", 0.0)
    syms = {k: v["count"] for k, v in report.items() if not k.startswith("_")}
    tablets = {r.get("tablet_id") for r in tail}
    tension = sum(1 for r in tail if (r.get("tension_axis") or {}).get("axis", "none") != "none")
    health = {(r.get("gates") or {}).get("drift_health") for r in tail}
    reasons = []
    if events < MIN_EVENTS or span < MIN_SPAN_DAYS:
        v = "INSUFFICIENT"
        reasons.append(f"events={events} (<{MIN_EVENTS}) or span_days={span} (<{MIN_SPAN_DAYS})")
    elif hits > 0:
        v = "RECURRENCE-HITS"
        reasons.append(f"{hits}/{events} rows hit the verbatim-recurrence check; plan bar is zero")
    else:
        v = "CLEAN-NEEDS-HUMAN-READ"
        reasons.append(f"0/{events} recurrence hits over {span} days; plan still requires a human read of gloss+exemplar pairs")
    if hits == events and events:
        reasons.append("100% hit rate looks like a write-on-hit artefact")
    if tension == 0 and events:
        reasons.append("tension_axis never fired in the tail (axis untested)")
    if health == {"unknown"}:
        reasons.append("drift_health is always 'unknown' (Phase-B attenuator not built)")
    return {"verdict": v, "events": events, "span_days": span, "recurrence_hits": hits,
            "per_symbol": syms, "distinct_tablets_in_tail": len(tablets), "tension_rows_in_tail": tension,
            "reasons": reasons}


def main(argv=None) -> int:
    from core.shadow_log import tail_rows
    out = verdict(t2.wouldinject_report(), tail_rows(t2._LOG_FILE, t2._REPORT_TAIL_ROWS))
    if "--json" in (argv or sys.argv[1:]):
        print(json.dumps(out, indent=2))
    else:
        print(f"Tier-2 would-inject: {out['verdict']}")
        for k in ("events", "span_days", "recurrence_hits", "per_symbol", "distinct_tablets_in_tail"):
            if k in out: print(f"  {k}: {out[k]}")
        for r in out["reasons"]: print(f"  - {r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
