"""Retrieval-floor calibration measurement (2026-09-26, J-1366 / F-1926 items 6+8). READ-ONLY
against the live DB -- never writes anything.

core/memory/store.py's retrieve_epoch()/retrieve_theme()/retrieve_symbol_tablet() all gate on the
one shared _WEAK_RETRIEVAL_FLOOR=0.30 (set 2026-08-19 by analogy to evidence_recall.py's MIN_SIM,
explicitly "not per-corpus-calibrated"), and emotional_prior() gates separately on
PRIOR_SIM_THRESHOLD=0.55. Both are top_k=1 (argmax-over-N) selections, so the right null to compare
a floor against is not "cosine between two random vectors" but "the BEST cosine a real, typical
query gets against everything currently in that table" -- exactly the statistic F-1926's own manual
sweep computed by hand over 15 inputs ("best cosine >=0.30 for epochs 13/15, tablets 12/15,
themes 8/15"). This script reproduces that statistic at real scale, read-only, using genuine stored
embeddings on both sides (no embedder re-load, no synthetic text):

  - query side: recent origin='lived' fragment embeddings -- 'lived' is the per-human-cycle summary
    fragment (see store.py's _parse_valence/_parse_primary, which read exactly this origin's content),
    and both call sites that matter (orchestrator.py:_retrieve_epoch_theme/_retrieve_symbol_evolution
    and the emotional_prior(self.state.raw_input) call at orchestrator.py:2500) are keyed on
    state.raw_input from a HUMAN cycle -- 'lived' fragments are the closest real stand-in for "a
    typical human-cycle query" without needing to reload the sentence-embedder here.
  - table side: the real, current contents of memory_epochs / memory_themes / symbol_tablets (self-
    symbols excluded, same frozenset as core/symbol_tracker.SELF_SYMBOLS:71) for _WEAK_RETRIEVAL_FLOOR,
    and shadow_events UNION high-importance episodic (importance>=0.70) for PRIOR_SIM_THRESHOLD --
    the exact corpora retrieve_epoch/retrieve_theme/retrieve_symbol_tablet/emotional_prior each query.

Usage:
    python scripts/measure_retrieval_floor_calibration.py [n_queries]

Example:
    python scripts/measure_retrieval_floor_calibration.py 400
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

# Hardcoded to the one real live repo, same reasoning scripts/measure_boredom_calibration.py gives --
# a job-run worktree has no data/ dir of its own; this script's whole point is the LIVE store.
DB_PATH = Path(r"C:\Nascence\data\memory\nascence.db")

# current constants at time of writing (core/memory/store.py)
CURRENT_WEAK_FLOOR = 0.30
CURRENT_PRIOR_FLOOR = 0.55

# core/symbol_tracker.py:71 -- inlined rather than imported so this script has no dependency on
# `core` being importable from an arbitrary cwd (the same choice measure_boredom_calibration.py
# made by reimplementing record()'s math locally instead of importing core.boredom).
SELF_SYMBOLS = frozenset({"river_crossing", "avon", "du_glyph", "bridge", "mirror"})


def blob_to_vec(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def best_of_n(query_vecs: list[np.ndarray], table_vecs: list[np.ndarray],
              query_ids: list[str] | None = None, table_ids: list[str] | None = None) -> list[float]:
    """For each query vector, the best (max) cosine against every OTHER row currently in the table --
    the exact selection statistic retrieve_epoch/retrieve_theme/retrieve_symbol_tablet/
    emotional_prior each use (top_k=1 / best-of-N argmax). query_ids/table_ids (fragment_id), when
    given, exclude a row from a query's own best-of-N if it is literally the same fragment -- the
    affective-prior corpus is drawn from memory_fragments too, so a 'lived' query that also happens
    to be one of the high-importance episodic rows must not be allowed to match ITSELF at cosine=1.0
    (verified: 62/400 of the 'lived' proxy queries used below are also members of that corpus)."""
    if not table_vecs:
        return []
    tmat = np.stack(table_vecs)
    tnorm = np.linalg.norm(tmat, axis=1)
    tnorm[tnorm == 0.0] = 1.0
    tnorm_mat = tmat / tnorm[:, None]
    out = []
    for i, q in enumerate(query_vecs):
        qn = float(np.linalg.norm(q))
        if qn == 0.0:
            continue
        sims = tnorm_mat @ (q / qn)
        if query_ids is not None and table_ids is not None:
            qid = query_ids[i]
            self_mask = [j for j, tid in enumerate(table_ids) if tid == qid]
            if self_mask:
                sims = np.delete(sims, self_mask)
                if sims.size == 0:
                    continue
        out.append(float(sims.max()))
    return out


def report(name: str, arr: list[float], current_floor: float) -> None:
    if not arr:
        print(f"\n{name}: NO DATA (table empty or no query overlap)")
        return
    a = np.array(arr, dtype=np.float64)
    qs = [1, 5, 10, 25, 50, 75, 80, 90, 95, 99]
    print(f"\n{name}: n_queries={len(a)} mean={a.mean():.4f} std={a.std():.4f} "
          f"min={a.min():.4f} max={a.max():.4f}")
    for q in qs:
        print(f"  p{q:<3d} = {float(np.percentile(a, q)):.4f}")
    share = float((a >= current_floor).mean()) * 100.0
    print(f"  share of typical queries whose BEST match already clears current floor "
          f"({current_floor}): {share:.2f}%")


def main() -> None:
    n_queries = int(sys.argv[1]) if len(sys.argv) > 1 else 400

    uri = f"file:{DB_PATH.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row

    query_rows = conn.execute(
        "SELECT fragment_id, embedding FROM memory_fragments WHERE origin='lived' "
        "AND embedding IS NOT NULL ORDER BY timestamp DESC LIMIT ?", (n_queries,)
    ).fetchall()
    queries = [blob_to_vec(bytes(r["embedding"])) for r in query_rows]
    query_ids = [r["fragment_id"] for r in query_rows]
    print(f"DB={DB_PATH}  proxy queries (origin='lived', most recent)={len(queries)}")

    epoch_rows = conn.execute("SELECT embedding FROM memory_epochs WHERE embedding IS NOT NULL").fetchall()
    theme_rows = conn.execute("SELECT embedding FROM memory_themes WHERE embedding IS NOT NULL").fetchall()
    tablet_rows = conn.execute(
        "SELECT symbol, embedding FROM symbol_tablets WHERE embedding IS NOT NULL").fetchall()
    tablet_rows = [r for r in tablet_rows if r["symbol"] not in SELF_SYMBOLS]
    shadow_rows = conn.execute("SELECT event_id, embedding FROM shadow_events WHERE embedding IS NOT NULL").fetchall()
    episodic_rows = conn.execute(
        "SELECT fragment_id, embedding FROM memory_fragments WHERE layer='episodic' AND importance >= 0.70 "
        "AND embedding IS NOT NULL").fetchall()
    conn.close()

    epoch_vecs = [blob_to_vec(bytes(r["embedding"])) for r in epoch_rows]
    theme_vecs = [blob_to_vec(bytes(r["embedding"])) for r in theme_rows]
    tablet_vecs = [blob_to_vec(bytes(r["embedding"])) for r in tablet_rows]
    prior_vecs = ([blob_to_vec(bytes(r["embedding"])) for r in shadow_rows]
                  + [blob_to_vec(bytes(r["embedding"])) for r in episodic_rows])
    # shadow_events ids live in a disjoint id space from memory_fragments.fragment_id, so prefixing
    # them just needs to never accidentally collide with a real fragment_id -- it can't, they're
    # UUIDs from a different table -- only episodic_rows' real fragment_id needs to match query_ids.
    prior_ids = ([f"shadow:{r['event_id']}" for r in shadow_rows]
                 + [r["fragment_id"] for r in episodic_rows])
    print(f"table sizes: epochs={len(epoch_vecs)} themes={len(theme_vecs)} "
          f"tablets(non-self)={len(tablet_vecs)} affective-prior-corpus={len(prior_vecs)} "
          f"(shadow={len(shadow_rows)} + high-importance-episodic={len(episodic_rows)})")

    report("epoch best-of-N cosine (_WEAK_RETRIEVAL_FLOOR)", best_of_n(queries, epoch_vecs), CURRENT_WEAK_FLOOR)
    report("theme best-of-N cosine (_WEAK_RETRIEVAL_FLOOR)", best_of_n(queries, theme_vecs), CURRENT_WEAK_FLOOR)
    report("tablet best-of-N cosine (_WEAK_RETRIEVAL_FLOOR)", best_of_n(queries, tablet_vecs), CURRENT_WEAK_FLOOR)
    report("affective-prior best-of-N cosine (PRIOR_SIM_THRESHOLD)",
           best_of_n(queries, prior_vecs, query_ids, prior_ids), CURRENT_PRIOR_FLOOR)


if __name__ == "__main__":
    main()
