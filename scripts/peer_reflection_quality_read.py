"""
J-3031 (F-3739): the READER for data/peer_reflection_quality_log.jsonl (written by core/peer_model.py, one row per
stored peer reflection, observe-only). Read-only: opens the log, prints counts, writes nothing.

Why it exists: a log with no reader is the #1 failure of this codebase (write-only). Run it after a fortnight of live
reflections (about 14 rows at 1 a day) and compare with the F-3739 baseline over the 32 reflections stored under the
old prompt (first person 10/32, second person 5/32, "nothing struck me" 0/32).

Usage: python scripts/peer_reflection_quality_read.py [path-to-log]      (default: <tree>/data/peer_reflection_quality_log.jsonl)
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT = ROOT / "data" / "peer_reflection_quality_log.jsonl"
HIGH_OVERLAP = 0.5   # share of a reflection's 3-word shingles already present in the same peer's previous one


def read(path: Path) -> dict:
    rows = []
    if path.exists():
        for ln in path.read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(ln))
            except Exception:
                pass
    n = len(rows)
    out = {"n": n}
    if not n:
        return out

    def share(pred, pool=None):
        pool = rows if pool is None else pool
        return (sum(1 for r in pool if pred(r)), len(pool))

    ov = [r for r in rows if r.get("overlap_contain") is not None]
    out.update({
        "starts_with_you": share(lambda r: r.get("starts_with_you")),
        "has_you": share(lambda r: r.get("has_you")),
        "first_person": share(lambda r: (r.get("first_person_n") or 0) > 0),
        "nothing_new": share(lambda r: r.get("nothing_new")),
        "topics_leak": share(lambda r: r.get("topics_leak")),
        "letter_capped": share(lambda r: r.get("letter_capped")),
        "high_overlap_with_prev": share(lambda r: r["overlap_contain"] >= HIGH_OVERLAP, ov),
        "median_len_ratio": round(statistics.median([r["len_ratio"] for r in rows if r.get("len_ratio") is not None]), 4)
        if any(r.get("len_ratio") is not None for r in rows) else None,
        "by_peer": {},
    })
    for r in rows:
        out["by_peer"][r.get("persona", "?")] = out["by_peer"].get(r.get("persona", "?"), 0) + 1
    return out


def main(argv) -> int:
    path = Path(argv[1]) if len(argv) > 1 else DEFAULT
    o = read(path)
    print(f"peer reflection quality log: {path}")
    if not o["n"]:
        print("  no rows yet (nothing has been logged; the log only fills when Du runs from a tree with J-3031 merged)")
        return 0
    print(f"  rows: {o['n']}   by peer: {o['by_peer']}")
    for k in ("starts_with_you", "has_you", "first_person", "nothing_new", "topics_leak", "letter_capped",
              "high_overlap_with_prev"):
        a, b = o[k]
        print(f"  {k:24s} {a}/{b}")
    print(f"  median reflection/letter length ratio: {o['median_len_ratio']}")
    print("  baseline over the 32 old-prompt reflections (F-3739): first person 10/32, second person 5/32, nothing-new 0/32")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
