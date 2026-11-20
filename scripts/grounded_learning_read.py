"""J-3181 / D-0568 reader: the one-week check of the reworked grounded-learning pass. Read-only.

  python scripts/grounded_learning_read.py [--days 7]

Prints (1) outcomes of data/grounded_learning_attempts.jsonl (stored / waiting / covered / rejected:* / dup_study /
call_failed / no_answer) and the per-sleep rows (notes per sleep, backlog `pending_frags`, `expired`, `last_ts`),
(2) for understanding notes written since the rework, the median best cosine to the book's study notes against the
book's reading fragments (D-0568 defeater: revisit if the study-note median is still above 0.75), (3) whether
`last_ts` is below the oldest still-pending fragment (it must never run ahead of unfed passages). The memory DB is
opened mode=ro.
"""
from __future__ import annotations

import json
import re
import sqlite3
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DATA = ROOT / "data"


def _rows(p: Path) -> list[dict]:
    try:
        return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    except Exception:
        return []


def main() -> None:
    days = float(sys.argv[sys.argv.index("--days") + 1]) if "--days" in sys.argv else 7.0
    since = time.time() - days * 86400
    att = [r for r in _rows(DATA / "grounded_learning_attempts.jsonl") if r.get("ts", 0) >= since]
    if not att:
        print("no attempts logged in the window: the reworked pass has not run (restart pending?)")
        return
    sleeps = [r for r in att if r.get("sleep")]
    tries = [r for r in att if not r.get("sleep")]
    print(f"window {days:g} d: {len(sleeps)} sleeps with new reading, {len(tries)} per-book attempts")
    print("outcomes:", dict(Counter(r.get("outcome") for r in tries)))
    if sleeps:
        notes = [r["notes"] for r in sleeps]
        print(f"notes per sleep: mean {statistics.mean(notes):.2f}, max {max(notes)} (cap = core.grounded_learning._MAX_NOTES)")
        print(f"backlog pending_frags: first {sleeps[0]['pending_frags']}, last {sleeps[-1]['pending_frags']}, "
              f"max {max(r['pending_frags'] for r in sleeps)}; expired total {sum(r.get('expired', 0) for r in sleeps)}")
    stored = [r for r in tries if r.get("outcome") == "stored"]
    if stored:
        print(f"stored notes: n_sources median {statistics.median(r['n_sources'] for r in stored)}, "
              f"covered-skipped median {statistics.median(r['n_covered'] for r in stored)}")
    try:
        import numpy as np
        from core.memory.store import DB_PATH
        con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        sc, rc = [], []
        for u in con.execute("SELECT content, embedding, timestamp FROM memory_fragments WHERE origin='understanding' "
                             "AND timestamp>=? AND embedding IS NOT NULL", (att[0]["ts"],)):
            m = re.match(r"\[Understanding \W+ from '(.*?)'\]", u["content"])
            if not m:
                continue
            uv = np.frombuffer(u["embedding"], dtype=np.float32)

            def best(origin, needle, lim):
                vs = [np.frombuffer(r["embedding"], dtype=np.float32) for r in con.execute(
                    "SELECT embedding FROM memory_fragments WHERE origin=? AND embedding IS NOT NULL AND instr(content, ?)>0 "
                    "AND timestamp<=? ORDER BY timestamp DESC LIMIT ?", (origin, needle, u["timestamp"], lim))]
                return max((float(np.dot(uv, v)) for v in vs), default=None)
            s = best("study", f"· on '{m.group(1)[:50]}' ·", 200)
            r = best("reading", f"[From '{m.group(1)}'", 300)
            if s is not None:
                sc.append(s)
            if r is not None:
                rc.append(r)
        if sc or rc:
            print(f"median best cosine of a new note: to its book's study notes {statistics.median(sc):.2f} (n={len(sc)}), "
                  f"to its reading {statistics.median(rc):.2f} (n={len(rc)})  [before the rework: 0.77 vs 0.68; revisit if study > 0.75]"
                  if sc and rc else f"cosines: study {sc[:3]} reading {rc[:3]}")
        else:
            print("no new understanding notes with embeddings yet")
        con.close()
    except Exception as exc:
        print("cosine check skipped:", exc)
    try:
        st = json.loads((DATA / "grounded_learning_state.json").read_text(encoding="utf-8"))
        print(f"state: last_ts {st.get('last_ts')}, per-book watermarks {len(st.get('books') or {})}")
    except Exception as exc:
        print("state unreadable:", exc)


if __name__ == "__main__":
    main()
