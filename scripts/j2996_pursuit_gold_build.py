"""J-2996 step 1: build the gold set for the pursuits 'advances' judge (F-3692, P-0100).  READ-ONLY toward Du.

WHAT IT BUILDS (docs/lab/J-2996_data/):
  gold_pairs.jsonl   one row per pair, with ALL metadata (source, pursuit id, panel context). NOT shown to the labeler.
  blind_sheet.txt    what the labeler reads: id, PURSUIT, PRIOR, NEW only. Shuffled, no source, no verdict.
  (labels are written by the labeler into gold_labels.json BEFORE any replay is run; the replay refuses to run without it)

TWO SOURCES (both exactly what the live judge sees, up to the truncations noted):
  A  'confirmed'  consecutive (thoughts[i-1] -> thoughts[i]) from data/pursuits_active.json, i >= 1. Each of these WAS
     judged an advance by the panel (thoughts is appended only in _apply_confirmed), so source A can say nothing about
     the judge's false-negatives; it measures how many panel-confirmed advances are not progress.
     FIDELITY GAP (stated, not hidden): the stored thought is thought[:200] (pursuits._apply_confirmed) whereas the live
     judge saw thought[:400] as NEW and standing[:300] as PRIOR. A-pairs are therefore the 200-char heads of the
     judged text. Both arms of every comparison see the same heads, but absolute agreement with the live verdicts
     is not comparable to the live rate.
  B  'pending'  every item still queued in 'pending' (not yet judged; thought[:400], prior_standing[:300] = the live
     input verbatim). There is no surviving store of judge-REFUTED pairs' text (refuted items are removed from
     'pending' and only the pursuit's question[:100] is logged), so B is the only place a non-advance can be found
     that the panel has not already passed.

Usage (from the worktree):  python scripts/j2996_pursuit_gold_build.py [--n-confirmed 60] [--seed 2996]
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

LIVE_PURSUITS = Path(r"C:\Nascence\data\pursuits_active.json")      # opened read-only
OUT = ROOT / "docs" / "lab" / "J-2996_data"


def load_pursuits(path: Path = LIVE_PURSUITS) -> list:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def confirmed_pairs(items: list) -> list:
    """Every consecutive (prior confirmed -> next confirmed) pair, with the pursuit's own last-3 positions."""
    rows = []
    for p in items:
        th = p.get("thoughts") or []
        for i in range(1, len(th)):
            rows.append({
                "source": "confirmed", "pursuit": p["id"], "status": p.get("status"),
                "question": (p.get("question") or "")[:200],
                "prior": th[i - 1], "new": th[i],
                "recent3": th[max(0, i - 3):i],            # the last <=3 confirmed thoughts BEFORE the new one, oldest first
                "idx": i, "n_thoughts": len(th),
            })
    return rows


def pending_pairs(items: list) -> list:
    rows = []
    for p in items:
        th = p.get("thoughts") or []
        for k, it in enumerate(p.get("pending") or []):
            rows.append({
                "source": "pending", "pursuit": p["id"], "status": p.get("status"),
                "question": (p.get("question") or "")[:200],
                "prior": (it.get("prior_standing") or "")[:280], "new": (it.get("thought") or "")[:450],
                "recent3": th[-3:], "idx": k, "n_thoughts": len(th),
                "restate_sim": it.get("restate_sim"), "coherent": it.get("coherent"),
                "cycle_id": it.get("cycle_id"),
            })
    return rows


def sample_confirmed(rows: list, n: int, seed: int, per_pursuit: int = 3) -> list:
    """Stratified: shuffle pursuits (seeded), take up to per_pursuit random pairs from each until n reached, so the
    set spans as many pursuits as possible (the brief: 20+)."""
    rng = random.Random(seed)
    by = {}
    for r in rows:
        by.setdefault(r["pursuit"], []).append(r)
    pids = sorted(by)
    rng.shuffle(pids)
    out = []
    for pid in pids:
        pool = by[pid][:]
        rng.shuffle(pool)
        out.extend(pool[:per_pursuit])
        if len(out) >= n:
            break
    return out[:n]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-confirmed", type=int, default=60)
    ap.add_argument("--seed", type=int, default=2996)
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    items = load_pursuits()
    A = sample_confirmed(confirmed_pairs(items), a.n_confirmed, a.seed)
    B = pending_pairs(items)
    allr = A + B
    rng = random.Random(a.seed + 1)
    rng.shuffle(allr)                                   # the labeler sees one shuffled list
    for k, r in enumerate(allr, 1):
        r["gid"] = f"G{k:03d}"
    with open(out / "gold_pairs.jsonl", "w", encoding="utf-8") as f:
        for r in allr:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(out / "blind_sheet.txt", "w", encoding="utf-8") as f:
        for r in allr:
            f.write(f"=== {r['gid']} ===\nPURSUIT: {r['question']}\nPRIOR POSITION: {r['prior']}\nNEW THOUGHT: {r['new']}\n\n")
    pids = {r["pursuit"] for r in A}
    print(f"confirmed pairs {len(A)} across {len(pids)} pursuits; pending pairs {len(B)} "
          f"across {len({r['pursuit'] for r in B})} pursuits; total {len(allr)}")
    print("wrote", out / "gold_pairs.jsonl", "and", out / "blind_sheet.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
