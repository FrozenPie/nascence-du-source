"""J-2980 (F-3665): reader for the observe-only `letter_overlap` rows core/peers.py appends to
data/peer_letter_quality_log.jsonl (one per delivered persona letter). Without this the log is write-only.
  python scripts/peer_letter_overlap_read.py [--log PATH]
Prints, split by no_reply (Du had not answered) vs replied: letters, sentences, copied share, and any letter at or
above 50 % copied. Baseline from F-3665 (before the change): no-reply 20.4 %, replied 2.6 %. Read-only."""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")


def load(path: Path):
    rows = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("event") == "letter_overlap":
                rows.append(r)
    return rows


def summarise(rows):
    out = {}
    for key, sel in (("no_reply", lambda r: r.get("no_reply")), ("replied", lambda r: not r.get("no_reply"))):
        sub = [r for r in rows if sel(r)]
        n_s = sum(r.get("sentences", 0) for r in sub)
        n_c = sum(r.get("copied", 0) for r in sub)
        out[key] = {"letters": len(sub), "sentences": n_s, "copied": n_c,
                    "copied_share": round(n_c / n_s, 4) if n_s else None,
                    "heavy": [(r.get("persona"), r.get("ts")) for r in sub if r.get("copied_share", 0) >= 0.5]}
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=str(ROOT / "data" / "peer_letter_quality_log.jsonl"))
    a = ap.parse_args()
    rows = load(Path(a.log))
    print(f"{len(rows)} letter_overlap rows in {a.log}")
    for k, v in summarise(rows).items():
        print(f"  {k}: {v['letters']} letters, {v['copied']}/{v['sentences']} sentences copied "
              f"(share {v['copied_share']}), heavy (>=50%): {v['heavy']}")
    by = defaultdict(list)
    for r in rows:
        by[r.get("persona")].append(r.get("copied_share", 0))
    for p, xs in sorted(by.items()):
        print(f"  {p}: {len(xs)} letters, mean copied share {sum(xs)/len(xs):.3f}")
