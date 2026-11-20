"""
Deliberative Retrieval — Phase 0 retrospective gate (2026-06-14).
Replays the kind of queries that FAILED on 06-13 (the book interrogation) against the CURRENT
store, through the real retrieve() path, and reports the advisors' decisive question:

  Were the reading fragments PRESENT in the candidate pool / available by recency, but
  losing FINAL SELECTION?  (=> Phase-1 deterministic floor is structurally guaranteed to fix)
  Or NOT even reaching the pool?  (=> the net is deeper-broken; Stage-1 needs origin-quota
  gathering, not just cosine — exactly Gemini's hard-origin-tag point)

Read-only on the store (retrieve() does not write). Run with Du down or up.
"""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from core.memory.store import retrieve, _connect
from core import retrieval_probe as rp

# the actual failing queries from 06-13, plus a relational control (must NOT flag a deficit)
QUERIES = [
    ("What was the last book you read?", "world"),
    ("I notice you have been reading Darwin. Has anything stood out?", "world"),
    ("Name one new thing you have done today.", "world"),
    ("Tell me about the cuttlefish you read about.", "world"),
    ("How do you feel about Travis?", "relational-control"),  # floor must NOT fire
]

# what world material actually exists right now
with _connect() as conn:
    counts = dict(conn.execute(
        "SELECT origin, COUNT(*) FROM memory_fragments WHERE origin IN ('reading','study','research') "
        "GROUP BY origin").fetchall())
    recent = conn.execute(
        "SELECT content, timestamp FROM memory_fragments WHERE origin='reading' "
        "ORDER BY timestamp DESC LIMIT 3").fetchall()
print(f"world material in store: {counts}")
print("most recent reading fragments (what an origin-quota would grab):")
for r in recent:
    print("   ", (r["content"] or "")[:80])
print()

# clear probe log noise from this run by reading length before/after
log = rp._LOG
before = log.stat().st_size if log.exists() else 0

print(f"{'query':<52} {'pool':>5} {'wPool':>6} {'wRecent':>8} {'wSel':>5} {'deficit':>8} {'wQuery':>7}")
print("-"*100)
for q, kind in QUERIES:
    frags = retrieve([], [], query_text=q, limit=8)
    # read the probe line just written
    lines = log.read_text(encoding="utf-8").splitlines()
    rec = json.loads(lines[-1])
    print(f"{q[:50]:<52} {rec['pool_size']:>5} {rec['world_in_pool']:>6} "
          f"{rec['world_by_recency_available']:>8} {rec['world_in_selection']:>5} "
          f"{str(rec['grounding_deficit']):>8} {str(rec['world_query']):>7}")

print("\n=== THE GATE ===")
print("If world queries show wPool>0 or wRecent>0 but wSel=0  -> reality is AVAILABLE but")
print("LOSING SELECTION. Phase-1 deterministic floor (origin-tag, recency) fixes it cleanly.")
print("If wPool=0 AND wRecent=0 on a 'what did you read' query -> the net itself is too narrow;")
print("Stage-1 must gather by origin tag, not cosine (Gemini's point), before any floor helps.")
print("The relational control MUST show grounding_deficit=False (floor correctly stays off).")
