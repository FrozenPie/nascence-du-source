"""
Embedder migration: all-MiniLM-L6-v2 -> paraphrase-multilingual-MiniLM-L12-v2 (2026-06-13).
Re-embeds every stored vector from its original source text, using the exact original
recipes. Run ONLY with Du shut down, AFTER backing up nascence.db.
  - memory_fragments.embedding        <- content
  - memory_fragments.emotion_embedding -> NULL (source text not stored; mixed-space
                                          comparison would be silently wrong; re-accumulates)
  - shadow_events.embedding           <- rejected_draft
  - light_events.embedding            <- integrated_content
  - procedural_skills.embedding       <- trigger_summary
  - memory_epochs.embedding           <- f"{mood}. {impression}"
  - memory_themes.embedding           <- f"{theme_name}. {current_stance}"
  - memory_themes.centroid            <- mean of re-embedded member-epoch vectors
"""
import json
import sqlite3
import sys
import time
import numpy as np

from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

DB = r"C:\Nascence\data\memory\nascence.db"
BATCH = 256

from sentence_transformers import SentenceTransformer
print("loading multilingual model...")
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                            device="cpu")

def blob(v):
    return np.asarray(v, dtype=np.float32).tobytes()

def reembed(conn, table, idcol, textfn, embcol="embedding"):
    rows = conn.execute(f"SELECT * FROM {table}").fetchall()
    items = [(r[idcol], textfn(r)) for r in rows if (textfn(r) or "").strip()]
    t0 = time.time()
    done = 0
    for i in range(0, len(items), BATCH):
        chunk = items[i:i + BATCH]
        # normalize_embeddings=True is MANDATORY: the store's _cosine is a raw dot and
        # assumes unit vectors (bug caught by post-migration verification 2026-06-13;
        # fixed in place by an L2 pass that run).
        vecs = model.encode([t for _, t in chunk], show_progress_bar=False,
                            convert_to_numpy=True, batch_size=64,
                            normalize_embeddings=True)
        conn.executemany(f"UPDATE {table} SET {embcol}=? WHERE {idcol}=?",
                         [(blob(v), _id) for (_id, _), v in zip(chunk, vecs)])
        done += len(chunk)
        print(f"  {table}: {done}/{len(items)}", end="\r")
    conn.commit()
    print(f"  {table}.{embcol}: {done} re-embedded in {time.time()-t0:.0f}s     ")
    return done

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

total = 0
total += reembed(conn, "memory_fragments", "fragment_id", lambda r: r["content"])
n = conn.execute("UPDATE memory_fragments SET emotion_embedding=NULL "
                 "WHERE emotion_embedding IS NOT NULL").rowcount
conn.commit()
print(f"  memory_fragments.emotion_embedding: {n} nulled (re-accumulates in new space)")
total += reembed(conn, "shadow_events", "event_id", lambda r: r["rejected_draft"])
total += reembed(conn, "light_events", "event_id", lambda r: r["integrated_content"])
total += reembed(conn, "procedural_skills", "skill_id", lambda r: r["trigger_summary"])
total += reembed(conn, "memory_epochs", "epoch_id",
                 lambda r: f"{r['mood']}. {r['impression']}")
total += reembed(conn, "memory_themes", "theme_id",
                 lambda r: f"{r['theme_name']}. {r['current_stance']}")

# theme centroids: mean of re-embedded member-epoch vectors
epoch_vecs = {}
for r in conn.execute("SELECT epoch_id, embedding FROM memory_epochs "
                      "WHERE embedding IS NOT NULL").fetchall():
    epoch_vecs[r["epoch_id"]] = np.frombuffer(r["embedding"], dtype=np.float32)
nc = 0
for r in conn.execute("SELECT theme_id, member_epoch_ids FROM memory_themes").fetchall():
    try:
        ids = json.loads(r["member_epoch_ids"] or "[]")
    except Exception:
        ids = []
    members = [epoch_vecs[i] for i in ids if i in epoch_vecs]
    if members:
        cen = np.mean(np.stack(members), axis=0)
        conn.execute("UPDATE memory_themes SET centroid=? WHERE theme_id=?",
                     (blob(cen), r["theme_id"]))
        nc += 1
conn.commit()
print(f"  memory_themes.centroid: {nc} recomputed from member epochs")
conn.close()
print(f"\nMIGRATION COMPLETE: {total} vectors re-embedded.")
