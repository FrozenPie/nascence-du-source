"""
Satisfaction cold-start backfill (2026-06-13). Replays Du's real history through the same
deterministic detectors that Phase 0 uses live, so his starting wanting/liking accumulators
are EARNED from the actual record, not asserted (auditor ruling). Run with Du down.
Idempotent: rewrites satisfaction_state.json from history each run.

Historical sources:
  light_events    -> liking (light_event)          | shadow_events -> wanting (shadow_event)
  T4 commits      -> liking (t4_commit) [from log]  | frontier born/resolved [frontier.json]
  study tablets   -> liking (study_tablet)          | chapters [origin='chapter']
Applies the live decay, so distant history weighs less.
"""
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from core.satisfaction import (_LIKING_EVENTS, _WANTING_EVENTS, DOMAINS,
                               _LIKING_HALFLIFE_S, _WANTING_HALFLIFE_S, _STATE)

now = time.time()
liking = {d: 0.0 for d in DOMAINS}
wanting = {d: 0.0 for d in DOMAINS}
counts: dict = {}

def add(event, ts):
    if event in _LIKING_EVENTS:
        w, dom = _LIKING_EVENTS[event]
        liking[dom] += w * (0.5 ** ((now - ts) / _LIKING_HALFLIFE_S))
    elif event in _WANTING_EVENTS:
        w, dom = _WANTING_EVENTS[event]
        wanting[dom] += w * (0.5 ** ((now - ts) / _WANTING_HALFLIFE_S))
    counts[event] = counts.get(event, 0) + 1

conn = sqlite3.connect(r"C:\Nascence\data\memory\nascence.db")
conn.row_factory = sqlite3.Row
for r in conn.execute("SELECT timestamp, source FROM light_events"):
    add("light_event", float(r["timestamp"]))
for r in conn.execute("SELECT timestamp, source FROM shadow_events"):
    add("unresolved_thought" if r["source"] == "unresolved_thought" else "shadow_event",
        float(r["timestamp"]))
for r in conn.execute("SELECT timestamp FROM memory_fragments WHERE origin='chapter'"):
    add("chapter_formed", float(r["timestamp"]))
for r in conn.execute("SELECT timestamp FROM memory_fragments WHERE origin='study'"):
    add("study_tablet", float(r["timestamp"]))
conn.close()

log = Path(r"C:\Nascence\data\nascence.log")
if log.exists():
    for line in log.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "T4 DISCHARGE — metabolised" in line:
            m = re.match(r"(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)", line)
            if m:
                ts = time.mktime(time.strptime(m.group(1), "%Y-%m-%d %H:%M:%S"))
                add("t4_commit", ts)
                add("tension_discharged", ts)

fj = Path(r"C:\Nascence\data\frontier.json")
if fj.exists():
    try:
        for q in json.loads(fj.read_text(encoding="utf-8")).get("questions", []):
            add("frontier_born", float(q.get("born", now)))
            if q.get("status") == "resolved":
                add("frontier_resolved", float(q.get("resolved_ts", now)))
    except Exception:
        pass

liking = {d: round(min(5.0, v), 4) for d, v in liking.items()}
wanting = {d: round(min(5.0, v), 4) for d, v in wanting.items()}
_STATE.write_text(json.dumps({"liking": liking, "wanting": wanting, "last_ts": now}),
                  encoding="utf-8")

print("events backfilled:", dict(sorted(counts.items())))
print("\nEARNED starting state (decayed to now):")
for d in DOMAINS:
    g = round(wanting[d] - liking[d], 3)
    print(f"  {d:<10} liking={liking[d]:.3f}  wanting={wanting[d]:.3f}  gap={g:+.3f}")
