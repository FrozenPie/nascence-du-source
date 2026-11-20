"""J-4348 reader: side-by-side of the spread vs origin-stratified epoch impressions.

Usage: python scripts/epoch_stratify_shadow_read.py [path]   (default data/epoch_stratify_shadow.jsonl)
Prints, per logged /quit epoch, each arm's origin mix, mood and impression, and which arm was stored.
Read-only. Founder question it answers: does stratifying by origin make the impression cover more than the
dominant origin's voice (J-3587: 7ccacdb2 covered only inner_thought)? A human reads the pairs; no score is claimed."""
import json
import sys
from pathlib import Path

DEFAULT = Path(__file__).resolve().parent.parent / "data" / "epoch_stratify_shadow.jsonl"


def main(argv):
    p = Path(argv[1]) if len(argv) > 1 else DEFAULT
    if not p.exists():
        print(f"no shadow log at {p} (flag NASCENCE_EPOCH_STRATIFY_SHADOW has not fired yet)")
        return 0
    rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"{len(rows)} epoch pair(s) in {p}")
    for i, r in enumerate(rows, 1):
        print(f"\n#{i} session {r['session_start']:.0f}..{r['session_end']:.0f} stored={r['stored_arm']}")
        for name, a in r["arms"].items():
            mix = ", ".join(f"{k} {v}" for k, v in sorted(a["origins"].items(), key=lambda kv: -kv[1]))
            print(f"  [{name}] n={a['n']} origins: {mix}\n    mood: {a['mood']}\n    impression: {a['impression']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
