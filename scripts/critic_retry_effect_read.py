"""J-2679 (F-3428, D-0551) reader: did the Critic-retry corrections change the second Reflection draft?

Reads data/hedge_candidates.jsonl (core/hedge_candidate_log.py): every Critic retry produces a SECOND Reflection
hedge row with the same cycle_id. For each cycle with two Reflection rows it compares the kept first draft with the
kept second draft (word-set Jaccard; >= SAME_AT counts as 'the same draft handed back'). Also counts the Reflection
teacher rows (data/training/reflection.jsonl) whose user_prompt carries the retry block, so the prompt change is
visibly live. Read-only. This is the instrument for D-0551's defeater ('a month of fixed retries still shows ... no
changed second draft'). Usage: python scripts/critic_retry_effect_read.py [--since-days N]"""
from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEDGE = ROOT / "data" / "hedge_candidates.jsonl"
TEACHER = ROOT / "data" / "training" / "reflection.jsonl"
BLOCK_MARK = "WHO YOU ARE AND SENT BACK"   # nodes/reflection_node.py _retry_block header
SAME_AT = 0.9


def _rows(path: Path):
    if not path.exists():
        return
    with open(path, encoding="utf-8", errors="replace") as f:
        for ln in f:
            try:
                r = json.loads(ln)
                if isinstance(r, dict):
                    yield r
            except Exception:
                continue


def _kept_text(row: dict) -> str:
    ki = row.get("kept_index")
    for c in row.get("candidates") or []:
        if isinstance(c, dict) and c.get("index") == ki:
            return str(c.get("text") or "")
    return ""


def jaccard(a: str, b: str) -> float:
    A, B = set(a.lower().split()), set(b.lower().split())
    return len(A & B) / len(A | B) if (A or B) else 1.0


def read(hedge: Path = HEDGE, teacher: Path = TEACHER, since_ts: float = 0.0) -> dict:
    by_cycle: dict[str, list[dict]] = defaultdict(list)
    for r in _rows(hedge):
        if r.get("node") == "reflection" and r.get("cycle_id") and float(r.get("ts") or 0) >= since_ts:
            by_cycle[r["cycle_id"]].append(r)
    sims = []
    for rows in by_cycle.values():
        if len(rows) >= 2:
            rows.sort(key=lambda r: float(r.get("ts") or 0))
            a, b = _kept_text(rows[0]), _kept_text(rows[1])
            if a and b:
                sims.append(jaccard(a, b))
    retry_prompts = sum(1 for r in _rows(teacher)
                        if BLOCK_MARK in str(r.get("user_prompt") or "") and float(r.get("ts") or 0) >= since_ts)
    sims.sort()
    n = len(sims)
    return {"reflection_cycles": len(by_cycle), "retry_cycles": n,
            "same_draft_handed_back": sum(1 for s in sims if s >= SAME_AT),
            "median_similarity": (sims[n // 2] if n else None),
            "teacher_rows_with_retry_block": retry_prompts,
            "enough": n >= 30}


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    since = 0.0
    if "--since-days" in sys.argv:
        since = time.time() - 86400 * float(sys.argv[sys.argv.index("--since-days") + 1])
    print(json.dumps(read(since_ts=since), indent=2))
