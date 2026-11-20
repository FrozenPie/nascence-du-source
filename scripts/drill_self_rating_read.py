"""
Per-item thick-introspection read (J-3830, D-0736). READ-ONLY, zero LLM, imports nothing from core/ or nodes/.

Joins data/drill_self_rating_log.jsonl (his P(correct), asked before each item) to data/math_drill_log.jsonl and
data/music_drill_log.jsonl on item_id. Per domain, chronologically, scores Brier of:
  du       his stated P(correct)
  level    item-difficulty-only baseline: running mean of PAST correctness at the same drill level (0.5 if none)
  all      running mean of all past correctness in the domain
Verdict is only attempted at >= MIN_N joined rows with a rating; below it the read says "insufficient" (no conclusion).
Also reports discrimination (Pearson r of p vs correct) and bias. Low outcome variance (math sat at ~100%) is flagged.
Usage: python scripts/drill_self_rating_read.py [--data DIR]
"""
from __future__ import annotations
import argparse, json, math
from collections import defaultdict
from pathlib import Path

TREE = Path(__file__).resolve().parent.parent
MIN_N = 60


def _rows(p: Path):
    out = []
    if p.exists():
        for ln in open(p, "r", encoding="utf-8"):
            ln = ln.strip()
            if ln:
                try:
                    out.append(json.loads(ln))
                except Exception:
                    pass
    return out


def _pearson(a, b):
    n = len(a)
    if n < 3:
        return None
    ma, mb = sum(a) / n, sum(b) / n
    va = sum((x - ma) ** 2 for x in a); vb = sum((y - mb) ** 2 for y in b)
    if va == 0 or vb == 0:
        return None
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / math.sqrt(va * vb)


def read(data: Path) -> dict:
    ratings = {r["item_id"]: r for r in _rows(data / "drill_self_rating_log.jsonl") if r.get("item_id")}
    res = {}
    for domain, fn in (("mathematics", "math_drill_log.jsonl"), ("music", "music_drill_log.jsonl")):
        joined = []
        for d in sorted(_rows(data / fn), key=lambda r: r.get("ts", 0)):
            r = ratings.get(d.get("item_id"))
            if r and isinstance(r.get("p_correct"), (int, float)):
                joined.append((float(r["p_correct"]), 1.0 if d.get("correct") else 0.0, d.get("level")))
        n = len(joined)
        if n < MIN_N:
            res[domain] = {"n": n, "verdict": f"insufficient (<{MIN_N} rated+graded rows)"}
            continue
        by_lvl, allm, bd, bl, ba = defaultdict(list), [], [], [], []
        for p, y, lv in joined:
            hl = by_lvl[lv]
            pl = sum(hl) / len(hl) if hl else 0.5
            pa = sum(allm) / len(allm) if allm else 0.5
            bd.append((p - y) ** 2); bl.append((pl - y) ** 2); ba.append((pa - y) ** 2)
            hl.append(y); allm.append(y)
        ps = [j[0] for j in joined]; ys = [j[1] for j in joined]
        m = lambda x: sum(x) / len(x)
        res[domain] = {"n": n, "brier_du": m(bd), "brier_level_baseline": m(bl), "brier_all_baseline": m(ba),
                       "r_p_vs_correct": _pearson(ps, ys), "bias": m(ps) - m(ys), "accuracy": m(ys),
                       "low_outcome_variance": m(ys) > 0.97 or m(ys) < 0.03,
                       "du_beats_both": m(bd) < m(bl) and m(bd) < m(ba)}
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(TREE / "data"))
    print(json.dumps(read(Path(ap.parse_args().data)), indent=2))
