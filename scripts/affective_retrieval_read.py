"""J-3872 / D-0734: read-side consumer for core.emotion_construction.affective_retrieval_status.

Read-only. Reads data/emotion_construction_affective_retrieval_shadow.jsonl (Experiment C part 2: top-5
recall ranked with the LLM mood vector vs the constructed one, same weights) via affective_retrieval_status()
and prints a verdict. emotion_rethink sets no numeric bar for Experiment C, so the thresholds below are this
reader's own, labelled as such. It verdicts the LOG ONLY; no flag flip (EMOTION_CONSTRUCTED) is implied and
that stays the founder's call (all three experiments must land). Never writes.

  python scripts/affective_retrieval_read.py [--json]
"""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import emotion_construction as ec

MIN_PAIRED = 100        # reader-chosen, not a plan bar
HIGH_JACCARD = 0.90     # reader-chosen
LOW_JACCARD = 0.60      # reader-chosen


def verdict(status: dict) -> dict:
    """Pure function: affective_retrieval_status() output -> {verdict, reasons, ...}."""
    rows, paired = status.get("rows", 0), status.get("paired", 0)
    if not rows:
        return {"verdict": "NO-DATA", "reasons": ["no shadow rows"]}
    jac, gap = status.get("mean_jaccard_top5"), status.get("mean_affect_match_gap")
    reasons = []
    if paired < MIN_PAIRED or jac is None:
        v = "INSUFFICIENT"
        reasons.append(f"paired={paired} (<{MIN_PAIRED}) or no Jaccard")
    elif jac >= HIGH_JACCARD:
        v = "CONSTRUCTED-MATCHES-LLM"
        reasons.append(f"top-5 overlap {jac} >= {HIGH_JACCARD}: swapping the mood vector barely changes recall")
        reasons.append("high overlap can also mean affect_match is too weak to matter in the ranking; "
                       "it does not by itself show the constructed vector is good")
    elif jac < LOW_JACCARD:
        v = "CONSTRUCTED-DIVERGES"
        reasons.append(f"top-5 overlap {jac} < {LOW_JACCARD}: recall would change materially")
    else:
        v = "MIXED"
        reasons.append(f"top-5 overlap {jac} between {LOW_JACCARD} and {HIGH_JACCARD}")
    return {"verdict": v, "rows": rows, "paired": paired, "mean_jaccard_top5": jac,
            "mean_affect_match_gap": gap, "reasons": reasons}


def main(argv=None) -> int:
    out = verdict(ec.affective_retrieval_status())
    if "--json" in (argv or sys.argv[1:]):
        print(json.dumps(out, indent=2))
    else:
        print(f"Affective retrieval: {out['verdict']}")
        for k in ("rows", "paired", "mean_jaccard_top5", "mean_affect_match_gap"):
            if k in out: print(f"  {k}: {out[k]}")
        for r in out["reasons"]: print(f"  - {r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
