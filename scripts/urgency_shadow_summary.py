"""
urgency_shadow_summary.py -- the READER for data/training/urgency_shadow.jsonl (J-3402, D-0682).

Compares, per consumer, what the DETERMINISTIC urgency (internal=low, human=moderate, time-pressure words or a human
correction=high, both=pressing) would have produced against what the Salience node's MODEL urgency actually produced,
and checks D-0682's defeater: does the deterministic urgency move attention bandwidth, somatic tension or the climate
warp OUTSIDE the range the model produced (model range 0.0-0.4 for the bandwidth urgency term, human mean 0.084)?

    python scripts/urgency_shadow_summary.py [--log PATH] [--json]

Read-only; writes nothing.  Verdict is the arithmetic, not a decision: D-0682's flip stays Travis's call.
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

TREE = Path(__file__).resolve().parent.parent
DEFAULT_LOG = TREE / "data" / "training" / "urgency_shadow.jsonl"


def load(path: Path) -> list[dict]:
    rows = []
    try:
        with open(path, encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if ln:
                    try:
                        rows.append(json.loads(ln))
                    except Exception:
                        pass
    except FileNotFoundError:
        pass
    return rows


def _rng(xs):
    xs = [x for x in xs if isinstance(x, (int, float))]
    if not xs:
        return None
    return {"n": len(xs), "min": round(min(xs), 4), "max": round(max(xs), 4), "mean": round(statistics.mean(xs), 4)}


def summarize(rows: list[dict]) -> dict:
    out: dict = {"rows": len(rows), "complete": sum(1 for r in rows if r.get("complete")), "by_type": {}}
    for it in ("human", "internal", "timer"):
        rs = [r for r in rows if r.get("input_type") == it]
        if not rs:
            continue
        bw = [r["bandwidth"] for r in rs if r.get("bandwidth")]
        so = [r["somatic"] for r in rs if r.get("somatic")]
        cl = [r["climate"] for r in rs if r.get("climate", {}).get("applies")]
        d: dict = {"n": len(rs),
                   "det_words": {w: sum(1 for r in rs if r["det"]["word"] == w) for w in ("low", "moderate", "high", "pressing")},
                   "model_urgency_raw": _rng([r["model"]["urgency_raw"] for r in rs]),
                   "bandwidth_urgency_term": {"model": _rng([b["model_urgency_term"] for b in bw]),
                                              "det": _rng([b["det_urgency_term"] for b in bw])},
                   "bandwidth": {"model": _rng([b["model"] for b in bw]), "det": _rng([b["det"] for b in bw]),
                                 "delta": _rng([b["delta"] for b in bw])},
                   "somatic_target": {"model": _rng([s["model_target"] for s in so]), "det": _rng([s["det_target"] for s in so]),
                                      "delta": _rng([s["delta_target"] for s in so])},
                   "climate_warped": {"model": _rng([c["model_warped"] for c in cl]), "det": _rng([c["det_warped"] for c in cl])}}
        # D-0682 defeater arithmetic: any det value outside [min, max] of the model's own values for that consumer
        def outside(det_key_vals, model_vals):
            m = [x for x in model_vals if isinstance(x, (int, float))]
            dv = [x for x in det_key_vals if isinstance(x, (int, float))]
            if not m or not dv:
                return None
            lo, hi = min(m), max(m)
            return sum(1 for x in dv if x < lo - 1e-9 or x > hi + 1e-9)
        d["det_outside_model_range"] = {
            "bandwidth_urgency_term": outside([b["det_urgency_term"] for b in bw], [b["model_urgency_term"] for b in bw]),
            "bandwidth": outside([b["det"] for b in bw], [b["model"] for b in bw]),
            "somatic_target": outside([s["det_target"] for s in so], [s["model_target"] for s in so]),
            "climate_warped": outside([c["det_warped"] for c in cl], [c["model_warped"] for c in cl]),
        }
        out["by_type"][it] = d
    return out


def main(argv: list[str]) -> int:
    path = DEFAULT_LOG
    if "--log" in argv:
        path = Path(argv[argv.index("--log") + 1])
    s = summarize(load(path))
    if "--json" in argv:
        print(json.dumps(s, indent=2))
    else:
        print(f"urgency shadow: {s['rows']} rows ({s['complete']} complete) from {path}")
        for it, d in s["by_type"].items():
            print(f"\n[{it}] n={d['n']}  det words {d['det_words']}  model urgency {d['model_urgency_raw']}")
            for k in ("bandwidth_urgency_term", "bandwidth", "somatic_target", "climate_warped"):
                print(f"  {k}: {d[k]}")
            print(f"  det values outside the model's own range: {d['det_outside_model_range']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
