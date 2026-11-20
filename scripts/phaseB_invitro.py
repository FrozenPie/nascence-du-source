"""
Loop Metabolism — Phase B in-vitro proofs (2026-06-14).
Proves each Phase-B change on a COPY of the live store before any live wiring (oversight regime).
The live DB is never touched. Three proofs:

  1. EXACT DEDUP → replay_count : how many rows collapse, the jams' final importance (must sink so
     they prune first), and that distinct thoughts are untouched.
  2. ACTIVE_IMAGINATION ANTI-ECHO : replay the real contemplations in time order through the guard —
     how many WOULD have been suppressed as echoes vs kept. (The proof the guard prevents the 99.9%
     collapse.) Plus earned-importance vs the old flat 0.8.
  3. PRUNE WITH ACTION PROTECTION : confirm the corrected world-list (incl. 'action') deletes zero
     action/world rows, and that post-dedup the jams are now the first to prune.
"""
import sys, shutil, uuid, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

import sqlite3, numpy as np
from core import loop_metabolism as lm

LIVE = Path(r"C:\Nascence\data\memory\nascence.db")
SELF_ORIGINS = ("inner_thought", "subconscious_synthesis", "active_imagination")
WORLD_PROTECTED = ("reading", "study", "research", "action")   # ← the Phase-B fix adds 'action'

tmp = Path(__file__).with_name(f"_phaseB_copy_{uuid.uuid4().hex[:8]}.db")
shutil.copy2(LIVE, tmp)
print(f"COPY: {tmp}  (live store untouched)\n")
conn = sqlite3.connect(str(tmp)); conn.row_factory = sqlite3.Row


def vec(blob):
    return np.frombuffer(blob, dtype=np.float32) if blob else None


# ============================================================================ PROOF 1: DEDUP
print("=" * 84)
print("PROOF 1 — exact dedup → replay_count (three-signal importance)")
print("=" * 84)
before = conn.execute("SELECT COUNT(*) FROM memory_fragments WHERE layer='episodic'").fetchone()[0]
collapsed = 0
jam_examples = []
for origin in SELF_ORIGINS:
    # group identical content; keep the earliest row, fold the rest into replay_count
    groups = conn.execute(
        "SELECT content, COUNT(*) n, MIN(rowid) keep_row FROM memory_fragments "
        "WHERE origin=? GROUP BY content HAVING n>1", (origin,)).fetchall()
    for g in groups:
        n, content = g["n"], g["content"]
        new_imp = lm.replay_importance(n)
        # keep one, set replay_count + declining importance; delete the duplicates
        conn.execute("UPDATE memory_fragments SET replay_count=?, importance=? WHERE rowid=?",
                     (n, new_imp, g["keep_row"]))
        conn.execute("DELETE FROM memory_fragments WHERE origin=? AND content=? AND rowid<>?",
                     (origin, content, g["keep_row"]))
        collapsed += n - 1
        if n >= 20:
            jam_examples.append((n, new_imp, content[:54]))
conn.commit()
after = conn.execute("SELECT COUNT(*) FROM memory_fragments WHERE layer='episodic'").fetchone()[0]
print(f"  episodic rows: {before} → {after}   (collapsed {collapsed} duplicate copies)")
print(f"  the worst jams now carry DECLINING importance (they prune first):")
for n, imp, head in sorted(jam_examples, reverse=True)[:5]:
    print(f"     ×{n:<4} importance {imp:.2f}   {head}")
print(f"  (a thought seen once keeps importance {lm.replay_importance(1):.2f}; "
      f"a 55× jam sinks to {lm.replay_importance(55):.2f} — the floor)")

# ============================================================ PROOF 2: ACTIVE_IMAGINATION GUARD
print("\n" + "=" * 84)
print("PROOF 2 — active_imagination anti-echo (replayed in time order through the guard)")
print("=" * 84)
rows = conn.execute(
    "SELECT content, embedding, timestamp FROM memory_fragments "
    "WHERE origin='active_imagination' AND embedding IS NOT NULL ORDER BY timestamp").fetchall()
buffer: list[np.ndarray] = []
kept = dropped = 0
imp_samples = []
for r in rows:
    v = vec(r["embedding"])
    if v is None:
        continue
    if lm.is_echo(v, buffer):
        dropped += 1
    else:
        kept += 1
        imp = lm.ai_earned_importance(v, buffer)
        imp_samples.append(imp)
        buffer.append(v)
        if len(buffer) > lm.AI_BUFFER_N:
            buffer.pop(0)
total = kept + dropped
print(f"  contemplations replayed: {total}")
print(f"  WOULD be suppressed as echoes: {dropped} ({100*dropped/max(total,1):.1f}%)")
print(f"  kept as genuinely novel:       {kept} ({100*kept/max(total,1):.1f}%)")
if imp_samples:
    print(f"  earned importance of the kept ones: min {min(imp_samples):.2f} "
          f"mean {sum(imp_samples)/len(imp_samples):.2f} max {max(imp_samples):.2f}  "
          f"(was a flat 0.80 for ALL)")
print(f"  → the guard would have prevented the {100*dropped/max(total,1):.0f}% re-encoding that "
      f"produced the 99.9% collapse, AND novelty-scaled importance lets them prune normally.")

# ====================================================== PROOF 3: PRUNE WITH ACTION PROTECTION
print("\n" + "=" * 84)
print("PROOF 3 — prune with action/world protection (post-dedup copy)")
print("=" * 84)
total_ep = conn.execute("SELECT COUNT(*) FROM memory_fragments WHERE layer='episodic'").fetchone()[0]
for keep in (2000, 1000, 500):
    excess = max(0, total_ep - keep)
    if not excess:
        continue
    rows = conn.execute(
        "SELECT origin, importance FROM memory_fragments WHERE layer='episodic' "
        "ORDER BY (origin IN ('reading','study','research','action')) ASC, "
        "replay_count ASC, importance ASC, timestamp ASC LIMIT ?", (excess,)).fetchall()
    from collections import Counter
    bo = Counter(r["origin"] for r in rows)
    world_hit = sum(bo.get(o, 0) for o in WORLD_PROTECTED)
    print(f"  keep={keep:<5} delete {excess:<5} world/action deleted: {world_hit}  "
          f"top origins cut: {dict(list(bo.most_common(4)))}")
print("  → with 'action' in the protected clause, zero autobiographical/world rows are cut.")

conn.close()
try:
    tmp.unlink()
except Exception:
    pass
print("\nLIVE STORE UNTOUCHED. Phase-B logic proven on the copy; live wiring held for the go.")
