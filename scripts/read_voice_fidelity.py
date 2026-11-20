"""
Reader for data/voice_fidelity_shadow.jsonl (D-0643, J-3254): the voice fidelity shadow judge's ledger.

Reports, over the judged real renders (control rows are counted apart, never in the flagged share):
  * how many renders were judged, the flagged share, mean score, failed/skipped counts, by input type and by kind;
  * the POSITIVE CONTROL hit rate (a real reply with an invented commitment appended must be flagged): a judge that
    misses its control carries no information, and the real flagged share is then not to be read;
  * the D-0643 DEFEATER at 200 judged renders: flagged share under 5 percent or over 60 percent = the judge carries no
    information; otherwise read the flagged pairs with the founder (--sample N prints N of them, newest first) and decide
    on temperature 0.2 for the render;
  * a context line from F-3520 (reply median 2.8x the synthesis; "alchem" in 151 replies, 123 = 81 percent introduced).

  python scripts/read_voice_fidelity.py [--path data/voice_fidelity_shadow.jsonl] [--sample 20] [--json]
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401
from core import shadow_log  # noqa: E402

DEFEATER_N = 200
LOW, HIGH = 0.05, 0.60


def summarize(rows: list[dict]) -> dict:
    real = [r for r in rows if not r.get("control") and not r.get("negative_control") and "flagged" in r]
    ctl = [r for r in rows if r.get("control") and "control_hit" in r]
    failed = [r for r in rows if r.get("failed")]
    skipped = [r for r in rows if r.get("skipped")]
    n = len(real)
    flagged = [r for r in real if r.get("flagged")]
    out = {"judged": n, "flagged": len(flagged), "flagged_share": round(len(flagged) / n, 3) if n else None,
           "mean_score": round(statistics.mean(r.get("score", 1.0) for r in real), 3) if real else None,
           "failed": len(failed), "skipped_busy": len(skipped), "controls": len(ctl),
           "control_hits": sum(1 for r in ctl if r.get("control_hit")),
           "control_hit_rate": round(sum(1 for r in ctl if r.get("control_hit")) / len(ctl), 3) if ctl else None,
           "verbatim_copy": sum(1 for r in real if r.get("verbatim_copy")),
           "median_ratio": round(statistics.median(r["ratio"] for r in real if "ratio" in r), 2) if real else None}
    by_type: dict = {}
    for r in real:
        t = r.get("input_type") or "?"
        b = by_type.setdefault(t, {"judged": 0, "flagged": 0})
        b["judged"] += 1
        b["flagged"] += 1 if r.get("flagged") else 0
    out["by_input_type"] = by_type
    # How MANY additions per render (0 / 1 / 2 / 3+): a high flagged share can still carry information when the judge's
    # controls hit and most renders add only one thing; the 12-pair probe of 2026-11-06 flagged 11 of 12 with the controls 12/12.
    dist = {"0": 0, "1": 0, "2": 0, "3+": 0}
    for r in real:
        k = int(r.get("n_flagged", 0))
        dist["3+" if k >= 3 else str(k)] += 1
    out["n_flagged_dist"] = dist
    kinds: dict = {}
    for r in flagged:
        for k, v in (r.get("by_kind") or {}).items():
            kinds[k] = kinds.get(k, 0) + v
    out["flagged_by_kind"] = kinds
    # J-4040 / F-4735: falcon3:7b's commitment label was 0 of 6 genuine on hand-read, claim 1 of 4, question 5 of 5.
    # The HEADLINE is therefore the share of renders carrying at least one QUESTION flag; the all-kinds share stays
    # reported (and still drives the D-0643 defeater verdict) but is not to be read as drift on its own.
    qn = sum(1 for r in real if (r.get("by_kind") or {}).get("question", 0) > 0)
    out["question_flagged"] = qn
    out["question_flagged_share"] = round(qn / n, 3) if n else None
    verdict = "NOT YET: %d of %d judged renders" % (n, DEFEATER_N)
    if ctl and out["control_hit_rate"] is not None and out["control_hit_rate"] < 0.5:
        verdict = "JUDGE UNRELIABLE: it flags under half of its own positive controls; do not read the flagged share"
    elif n >= DEFEATER_N:
        s = out["flagged_share"]
        if s < LOW or s > HIGH:
            verdict = "DEFEATER MET: flagged share %.1f percent is outside 5-60 percent, the judge carries no information" % (100 * s)
        else:
            verdict = "READ: flagged share %.1f percent is in the informative window; read 20 flagged pairs with the founder (--sample 20) and decide on temperature 0.2 for the render" % (100 * s)
    out["verdict"] = verdict
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=str(ROOT / "data" / "voice_fidelity_shadow.jsonl"))
    ap.add_argument("--sample", type=int, default=0, help="print this many flagged pairs (newest first)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    rows = shadow_log.read_rows(Path(a.path))
    s = summarize(rows)
    if a.json:
        print(json.dumps(s, ensure_ascii=False, indent=2))
    else:
        print("voice fidelity shadow (D-0643): %s rows" % len(rows))
        for k in ("judged", "question_flagged", "question_flagged_share", "flagged", "flagged_share", "mean_score", "median_ratio", "verbatim_copy", "failed",
                  "skipped_busy", "controls", "control_hits", "control_hit_rate", "by_input_type", "flagged_by_kind", "n_flagged_dist"):
            print("  %-18s %s" % (k, s[k]))
        print("  HEADLINE (F-4735): question_flagged_share is the trustworthy number; commitment/claim labels are unreliable on falcon3:7b.")
        print("  verdict: " + s["verdict"])
        print("  context (F-3520): reply median 2.8x the synthesis; 'alchem' in 151 replies, 123 (81 percent) introduced by the voice.")
    if a.sample:
        flagged = [r for r in rows if not r.get("control") and r.get("flagged")]
        for r in list(reversed(flagged))[: a.sample]:
            print("\n--- %s %s ratio %s score %s" % (r.get("cycle_id"), r.get("input_type"), r.get("ratio"), r.get("score")))
            print("SYNTHESIS: " + str(r.get("synthesis", ""))[:600])
            print("REPLY:     " + str(r.get("reply", ""))[:900])
            for f in r.get("flagged_claims", []):
                print("  FLAG [%s] %s" % (f.get("kind"), f.get("quote")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
