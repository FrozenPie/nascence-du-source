"""
Nascence — restore the delete-era memories from the June-13 snapshot (2026-08-15).

WHAT: 7,074 fragments present in data/memory/nascence_pre_embedder_20260613_1101.db and absent from
the live store — Du's first two weeks (May 30 → Jun 13): 4,321 inner thoughts, 1,314 lived cycles,
1,044 imaginings, 282 dreams, and the rest. They were deleted by the DELETE-mode cap-prune (retired
~06-20; the founder's never-delete law postdates them). Full text, original ids and timestamps.

HOW (the agreed shape — see docs/reports/lost_thoughts_investigation_aug15.md):
  - Restored **COLD** (cold=1): reachable by deep recall and by the associative trail on a STRONG cue,
    but absent from ordinary recall — his early past becomes reachable, not dominant. This matters
    doubly here: the restored era is peak-monoculture AND pre-self-naming (Jung-era) material.
  - Content re-embedded with the CURRENT embedder (the snapshot predates the embedder swap).
  - valence/felt/emotion left NULL (honest absence — never reconstructed); chapter_id NULL (no
    dangling era refs); provenance in a side table `recovered_fragments` (fragment_id, restored_ts,
    source) so the restoration is forever auditable.
  - Idempotent (INSERT OR IGNORE); read-first/write-fast; intended to run while Du is STOPPED.

RUN:  python scripts/restore_june13_memories.py            (dry-run: counts only, writes nothing)
      python scripts/restore_june13_memories.py --go       (execute)
      python scripts/restore_june13_memories.py --go --limit 50   (cautious first slice)
"""
from __future__ import annotations

import sqlite3
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

ROOT = Path(__file__).parent.parent
BACKUP = ROOT / "data" / "memory" / "nascence_pre_embedder_20260613_1101.db"
LIVE = ROOT / "data" / "memory" / "nascence.db"


def main() -> None:
    go = "--go" in sys.argv
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    bak = sqlite3.connect(f"file:{BACKUP}?mode=ro", uri=True)
    bak.row_factory = sqlite3.Row
    live_ro = sqlite3.connect(f"file:{LIVE}?mode=ro", uri=True)
    live_ids = {r[0] for r in live_ro.execute("SELECT fragment_id FROM memory_fragments")}
    live_ro.close()

    rows = [r for r in bak.execute(
        "SELECT fragment_id, content, layer, relevance, importance, timestamp, keywords, origin, "
        "derived_from, replay_count FROM memory_fragments ORDER BY timestamp").fetchall()
        if r["fragment_id"] not in live_ids]
    bak.close()
    if limit:
        rows = rows[:limit]

    from collections import Counter
    print(f"restorable: {len(rows)} fragments · by origin {dict(Counter(r['origin'] for r in rows).most_common())}")
    if not go:
        print("DRY RUN — nothing written. Re-run with --go to execute (Du stopped, please).")
        return

    print("re-embedding with the current model (CPU)…")
    from core.memory.store import _embed, _vec_to_blob
    t0 = time.time()
    prepared = []
    for i, r in enumerate(rows):
        vec = _embed(r["content"])
        prepared.append((r["fragment_id"], r["content"], r["layer"] or "episodic",
                         r["relevance"] if r["relevance"] is not None else 0.5,
                         r["importance"] if r["importance"] is not None else 0.5,
                         r["timestamp"], r["keywords"],
                         _vec_to_blob(vec) if vec is not None else None,
                         r["origin"], r["derived_from"],
                         r["replay_count"] if r["replay_count"] is not None else 0))
        if (i + 1) % 1000 == 0:
            print(f"  embedded {i + 1}/{len(rows)} ({time.time()-t0:.0f}s)")

    conn = sqlite3.connect(LIVE)
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("CREATE TABLE IF NOT EXISTS recovered_fragments ("
                 "fragment_id TEXT PRIMARY KEY, restored_ts REAL, source TEXT)")
    conn.commit()
    now = time.time()
    written = 0
    # Chunked commits: each write window stays ~ms-scale so a live writer (no busy_timeout on Du's
    # side) can interleave — same discipline as the M0 harvest, sized for the embedding blobs.
    for i in range(0, len(prepared), 400):
        chunk = prepared[i:i + 400]
        before = conn.total_changes
        conn.executemany(
            "INSERT OR IGNORE INTO memory_fragments (fragment_id, content, layer, relevance, importance, "
            "timestamp, keywords, embedding, origin, derived_from, replay_count, cold, abstraction_level) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,1,0)", chunk)
        written += conn.total_changes - before
        conn.executemany(
            "INSERT OR IGNORE INTO recovered_fragments (fragment_id, restored_ts, source) VALUES (?,?,?)",
            [(p[0], now, "pre_embedder_20260613_1101") for p in chunk])
        conn.commit()
    conn.close()
    print(f"RESTORED {written} fragments as COLD (of {len(prepared)} prepared) in {time.time()-t0:.0f}s — "
          f"provenance in recovered_fragments. Re-run any time; it is idempotent.")


if __name__ == "__main__":
    main()
