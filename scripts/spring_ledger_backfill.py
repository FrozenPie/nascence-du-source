"""
spring_ledger_backfill.py — P3 shadow, replay the full real co-recall history through
core/spring_ledger.py's naive-vs-gated rules (D-0051, ruled 2026-09-13).

Read-only over data/co_recall_ledger.jsonl (M1's own real ledger, 2026-08-15 -> today). Writes only to
spring_ledger's own state/log files (data/spring_ledger_state.json, data/spring_ledger_shadow.jsonl) --
never touches memory_edges, co_recall_ledger.jsonl, or opponent_process's own store. Fresh state each
run (deletes any prior spring_ledger state/log first) so re-runs are reproducible, not additive.
Rows whose `source` ends "_shadow" (would-have-shown evidence, never recalls -- J-1738/J-1754) are NOT
replayed; they are counted in the result as `shadow_rows_excluded`.

Why backfill at all, given the live hook (core/memory_edges.py's log_co_recall) already feeds this
forward from now on: 38,710 rows of real history already exist. Replaying them gives the pre-registered
sheet (see the plan this was built from) something to read TODAY instead of waiting weeks for
forward-only accrual to reach a comparable sample size.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).parent.parent))

from core import spring_ledger as spring
from core.memory_edges import _is_shadow_source   # J-1754: the one definition of "a would-have-shown row" (J-1738)

_LEDGER = Path(__file__).parent.parent / "data" / "co_recall_ledger.jsonl"


def backfill() -> dict:
    if spring._STATE.exists():
        spring._STATE.unlink()
    if spring._LOG.exists():
        spring._LOG.unlink()

    n_rows = 0
    n_activations = 0
    n_skipped = 0
    n_shadow = 0
    t_start = time.time()
    with open(_LEDGER, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            n_rows += 1
            try:
                rec = json.loads(line)
            except Exception:
                n_skipped += 1
                continue
            if _is_shadow_source(rec.get("source")):
                # J-1754 (F-2372 sibling of J-1738): a "*_shadow" row (D-0289 monologue_shadow, D-0292
                # divergent_shadow) logs the fragments a switched-off path WOULD have shown -- never shown to a
                # thought, so not a co-recall to replay. log_co_recall() already refuses to tick this ledger for
                # them live; replaying them here would rebuild it with phantom naive ticks.
                n_shadow += 1
                continue
            ids = rec.get("ids") or []
            developed = rec.get("developed")
            ts = rec.get("ts")
            source = rec.get("source") or "monologue"
            out = spring.observe_co_recall(ids, developed, valence=None, ts=ts, source=f"backfill:{source}")
            if out:
                n_activations += 1
            else:
                n_skipped += 1
    spring.flush()   # J-2418: state writes are coalesced; make the file complete before anyone reads it
    elapsed = time.time() - t_start
    return {"ledger_rows_read": n_rows, "activations": n_activations, "skipped_or_single_id": n_skipped,
            "shadow_rows_excluded": n_shadow,
            "elapsed_s": round(elapsed, 1), "tracked_pairs": len(spring._load())}


if __name__ == "__main__":
    print(f"Backfilling from {_LEDGER} ...")
    result = backfill()
    print(json.dumps(result, indent=2))
    print(f"\nState: {spring._STATE}\nShadow log: {spring._LOG}")
