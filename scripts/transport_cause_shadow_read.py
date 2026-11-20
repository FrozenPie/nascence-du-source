"""Reader for data/transport_cause_shadow.jsonl (J-4382, D-0854, strings Phase 2 / D-0375).
Usage: python scripts/transport_cause_shadow_read.py [--log PATH] [--json]
Metrics: would-fire counts cause vs per-place (pass: cause <= per-place); would_fired_share per scoring over ticks
(D-0375 defeater >90%); one-event identity for multi-place causes (pass: 100%); cause lines silent while
cross-sections fire (kill: cause never fires in the window while its places do)."""
import argparse, json, sys
from pathlib import Path

DEFAULT = Path(__file__).resolve().parent.parent / "data" / "transport_cause_shadow.jsonl"

def read(path):
    ticks = causes = cause_fire = place_fire = 0
    tick_cause_any = tick_place_any = 0
    multi = multi_ok = 0
    per = {}   # cause -> [cause_fires, place_fires]
    t0 = t1 = None
    if not Path(path).exists():
        return {"rows": 0, "verdict": "NO-DATA"}
    for line in open(path, encoding="utf-8"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        ts = r.get("ts"); t0 = ts if t0 is None else min(t0, ts or t0); t1 = ts if t1 is None else max(t1, ts or t1)
        if r.get("type") == "tick":
            ticks += 1; tick_cause_any += bool(r.get("cause_any")); tick_place_any += bool(r.get("place_any"))
        elif r.get("type") == "cause":
            causes += 1
            pf = sum(1 for p in r.get("places", []) if p.get("place_would_fire"))
            cf = 1 if r.get("cause_would_fire") else 0
            cause_fire += cf; place_fire += pf
            d = per.setdefault(r["cause_id"], [0, 0]); d[0] += cf; d[1] += pf
            if r.get("n_places", 0) > 1:
                multi += 1
                eids = {r.get("event_ids", [None])[0]} if r.get("event_ids") else set()
                if len(r.get("event_ids", [])) == 1 and all(p.get("line_id") for p in r.get("places", [])):
                    multi_ok += 1
    silent = sorted(c for c, (cf, pf) in per.items() if cf == 0 and pf > 0)
    span_days = ((t1 - t0) / 86400.0) if t0 is not None and t1 is not None else 0.0
    out = {"rows": ticks + causes, "ticks": ticks, "span_days": round(span_days, 2),
           "cause_fires": cause_fire, "place_fires": place_fire,
           "cause_le_place": cause_fire <= place_fire,
           "would_fired_share_cause": round(tick_cause_any / ticks, 3) if ticks else None,
           "would_fired_share_place": round(tick_place_any / ticks, 3) if ticks else None,
           "multi_place_rows": multi, "one_event_identity": round(multi_ok / multi, 3) if multi else None,
           "causes_silent_while_places_fire": silent[:20], "n_silent": len(silent)}
    flags = []
    if cause_fire > place_fire: flags.append("KILL: cause fires more than per-place")
    if (out["would_fired_share_cause"] or 0) > 0.9: flags.append("DEFEATER: would_fired_share cause > 90%")
    if multi and multi_ok != multi: flags.append("DEFEATER: one-event identity < 100%")
    if silent and span_days >= 7: flags.append("DEFEATER: cause line silent 7d while places fire")
    out["flags"] = flags
    out["verdict"] = "NO-DATA" if not ticks else ("FAIL" if flags else ("PASS" if span_days >= 7 else "PASS-SO-FAR (<7d)"))
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--log", default=str(DEFAULT)); ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    res = read(a.log)
    print(json.dumps(res, indent=None if a.json else 2))
