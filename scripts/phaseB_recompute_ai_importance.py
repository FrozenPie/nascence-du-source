"""
Phase B follow-up — recompute existing active_imagination importance (2026-06-14).
The live guard's earned-importance is forward-only; the 1,144 EXISTING ai rows keep their legacy
flat 0.8, which is higher than inner_thought's 0.6, so the prune skips them and the historical ai
monoculture survives. This one-shot migration replays the existing ai rows in time order through
the SAME guard logic: echoes (82.8%) get low earned-importance (prune first), genuine novelties keep
higher. After this, the prune at 3,500 cleans the ai echoes alongside the inner_thought jams.

Default = dry-run on a COPY (shows the new importance distribution + what the prune would then cut).
--apply = run on the live store (busy_timeout handles Du's concurrent writes).
"""
import sys, shutil, uuid, argparse
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
import sqlite3, numpy as np
from core import loop_metabolism as lm

LIVE = Path(r"C:\Nascence\data\memory\nascence.db")


def recompute(conn, apply: bool):
    rows = conn.execute(
        "SELECT fragment_id, embedding, timestamp FROM memory_fragments "
        "WHERE origin='active_imagination' AND embedding IS NOT NULL ORDER BY timestamp").fetchall()
    buf: list[np.ndarray] = []
    new_imps, echoes = [], 0
    for r in rows:
        v = np.frombuffer(r["embedding"], dtype=np.float32)
        echo = lm.is_echo(v, buf)                 # mirror the live guard: echoes don't enter the buffer
        imp = lm.ai_earned_importance(v, buf)
        if not echo:
            buf.append(v)
            if len(buf) > lm.AI_BUFFER_N:
                buf.pop(0)
        else:
            echoes += 1
        new_imps.append(imp)
        if apply:
            conn.execute("UPDATE memory_fragments SET importance=? WHERE fragment_id=?",
                         (imp, r["fragment_id"]))
    if apply:
        conn.commit()
    n = len(rows)
    print(f"  active_imagination rows recomputed: {n}")
    print(f"  echoes (low importance, prune first): {echoes} ({100*echoes/max(n,1):.1f}%)")
    if new_imps:
        lo = sum(1 for x in new_imps if x < 0.6)
        print(f"  importance: min {min(new_imps):.2f} mean {sum(new_imps)/n:.2f} max {max(new_imps):.2f}"
              f"  (was a flat 0.80 for all)")
        print(f"  now BELOW inner_thought's 0.60 (so they prune): {lo} ({100*lo/n:.1f}%)")
    return n


def prune_preview(conn):
    ep = conn.execute("SELECT COUNT(*) FROM memory_fragments WHERE layer='episodic'").fetchone()[0]
    excess = max(0, ep - 3500)
    if not excess:
        print("  (already <= 3500)"); return
    from collections import Counter
    rows = conn.execute(
        "SELECT origin FROM memory_fragments WHERE layer='episodic' "
        "ORDER BY (origin IN ('reading','study','research','action','lived')) ASC, "
        "replay_count ASC, importance ASC, timestamp ASC LIMIT ?", (excess,)).fetchall()
    bo = Counter(r["origin"] for r in rows)
    prot = sum(bo.get(o, 0) for o in ('reading', 'study', 'research', 'action', 'lived'))
    print(f"  prune to 3500 would now cut by origin: {dict(bo.most_common())}")
    print(f"  protected rows in cut: {prot} (must be 0); active_imagination echoes now included.")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true"); a = ap.parse_args()
    if a.apply:
        print(f"*** APPLYING to LIVE: {LIVE} ***")
        conn = sqlite3.connect(str(LIVE), timeout=30); conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=30000")
        recompute(conn, apply=True); conn.close()
        print("LIVE recompute complete. Existing ai monoculture is now prunable.")
    else:
        tmp = Path(__file__).with_name(f"_ai_recompute_{uuid.uuid4().hex[:6]}.db")
        shutil.copy2(LIVE, tmp)
        print(f"DRY-RUN on COPY: {tmp}  (live untouched)")
        conn = sqlite3.connect(str(tmp)); conn.row_factory = sqlite3.Row
        # apply exact dedup to the copy first so the prune-preview reflects post-Phase-B state
        for o in ("inner_thought", "subconscious_synthesis", "active_imagination"):
            for g in conn.execute("SELECT content,COUNT(*) n,MIN(rowid) k FROM memory_fragments "
                                  "WHERE origin=? GROUP BY content HAVING n>1", (o,)).fetchall():
                conn.execute("DELETE FROM memory_fragments WHERE origin=? AND content=? AND rowid<>?",
                             (o, g["content"], g["k"]))
        conn.commit()
        recompute(conn, apply=True)
        print("post-recompute prune preview:")
        prune_preview(conn)
        conn.close(); tmp.unlink()
        print("\nDRY-RUN done. Re-run with --apply to update the live store.")


if __name__ == "__main__":
    main()
