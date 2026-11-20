"""
Nascence — Euclidean Recall (state-weighted retrieval, OBSERVE-ONLY P0, 2026-06-15)
===================================================================================
The third geometry (docs/euclidean_memory_plan.md): a memory is a POINT in a small weighted
feature space; the current need is a point; recall is ONE weighted-Euclidean nearest-neighbour.
The modulation field would set the weights → state-dependent recall. This P0 is the re-ranker
+ the dimensional features ONLY — it does NOT touch live retrieval. It exists so the comparison
test can SEE whether the same query under different states surfaces meaningfully different (and
sensible) memories — the operational test of the multiple-dimension / origin-attractor theory.

Low-D on purpose (~6 dims): the 384-dim semantic embedding is collapsed to ONE scalar
(semantic_sim) so Euclidean distance stays meaningful (no curse of dimensionality).
"""
from __future__ import annotations
import math
import numpy as np

FEATURES = ["semantic_sim", "recency", "affect_match", "salience", "abstraction", "provenance"]

# abstraction: raw lived ↔ distilled. From layer, with a bump for distilled origins.
_ABSTRACTION_LAYER = {"working": 0.0, "episodic": 0.33, "semantic": 0.66, "archive": 1.0}
_ABSTRACTION_ORIGIN_BUMP = {"consolidation": 0.30, "chapter": 0.30, "subconscious_synthesis": 0.20}

# provenance: source CERTAINTY (lived/seed high; external testimony lower) — spec dim 6.
_PROVENANCE = {
    "lived": 1.0, "seed": 1.0, "session_summary": 0.9, "action": 0.85,
    "consolidation": 0.75, "chapter": 0.75, "study": 0.70,
    "inner_thought": 0.60, "subconscious_synthesis": 0.60, "reading": 0.60,
    "dream": 0.50, "active_imagination": 0.50, "research": 0.40, "parametric_library": 0.30,
}


def _abstraction(layer: str, origin: str) -> float:
    base = _ABSTRACTION_LAYER.get((layer or "").lower(), 0.33)
    return min(1.0, base + _ABSTRACTION_ORIGIN_BUMP.get((origin or "").lower(), 0.0))


def featurize(row, need_emb, field_emo_vec, now: float, tau_days: float = 14.0) -> np.ndarray:
    """Map one fragment row to its point in the ~6-dim feature space. Row must expose:
    embedding, emotion_embedding, timestamp, importance, layer, origin (sqlite Row or dict)."""
    from core.memory.store import _blob_to_vec, _cosine

    def _g(k):
        try:
            return row[k]
        except Exception:
            return None

    # 1 semantic_sim
    emb = _g("embedding")
    sem = _cosine(need_emb, _blob_to_vec(emb)) if (emb and need_emb is not None) else 0.0
    # 2 recency (exp decay over tau days)
    ts = float(_g("timestamp") or 0.0)
    recency = math.exp(-max(0.0, now - ts) / (tau_days * 86400.0))
    # 3 affect_match (cosine in emotion-embedding space; 0 when either side lacks a felt-tag)
    emo = _g("emotion_embedding")
    affect = _cosine(field_emo_vec, _blob_to_vec(emo)) if (emo and field_emo_vec is not None) else 0.0
    # 4 salience
    salience = float(_g("importance") or 0.5)
    # 5 abstraction, 6 provenance
    abstraction = _abstraction(_g("layer"), _g("origin"))
    provenance = _PROVENANCE.get((_g("origin") or "").lower(), 0.5)
    return np.array([sem, recency, max(0.0, affect), salience, abstraction, provenance],
                    dtype=np.float32)


def distance(feat: np.ndarray, need: np.ndarray, weights: np.ndarray) -> float:
    """Weighted Euclidean distance from the need point — smaller is a better recall."""
    d = (need - feat)
    return float(math.sqrt(float(np.sum(weights * d * d))))


def rank(rows, need_emb, field_emo_vec, need: np.ndarray, weights: np.ndarray,
         top_k: int = 8, now: float | None = None, tau_days: float = 14.0) -> list[dict]:
    """Return the top_k rows by weighted-Euclidean nearest-neighbour, each with its features.
    OBSERVE-ONLY — callers use this for analysis; nothing here changes live retrieval."""
    import time as _t
    now = now if now is not None else _t.time()
    out = []
    for row in rows:
        feat = featurize(row, need_emb, field_emo_vec, now, tau_days)
        out.append((distance(feat, need, weights), row, feat))
    out.sort(key=lambda x: x[0])
    res = []
    for dist, row, feat in out[:top_k]:
        res.append({
            "distance": round(dist, 4),
            "row": row,
            "features": {f: round(float(v), 3) for f, v in zip(FEATURES, feat)},
        })
    return res

# ── SHADOW (big build 2026-07-03, the resurrected plan step 2): every sampled idle cycle, log what
# state-weighted recall WOULD have surfaced for his actual thought, beside the semantic baseline — the
# divergence corpus that licenses (or kills) any live wiring. Observe-only; capped candidates for cost.
def shadow_log(query: str, max_candidates: int = 600) -> None:
    """Fire-and-forget from a thread. Writes data/euclidean_shadow.jsonl. Never raises."""
    try:
        import json, time, sqlite3
        from pathlib import Path
        from core.memory.store import _embed
        from core import mood as _mood
        db = Path(__file__).parent.parent / "data" / "memory" / "nascence.db"
        con = sqlite3.connect(str(db)); con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT content, embedding, emotion_embedding, timestamp, importance, layer, origin "
            "FROM memory_fragments WHERE embedding IS NOT NULL AND (cold IS NULL OR cold=0) AND origin != 'system_note' "
            "ORDER BY timestamp DESC LIMIT ?", (max_candidates,)).fetchall()
        con.close()
        need = _embed(query)
        if need is None or not rows:
            return
        felt = None
        try:
            # 2026-08-19 fix: was `current_felt_vec()`, which does not exist and never did (grep confirmed
            # this is the only reference in the whole codebase) — always raised, always caught, so `felt`
            # was always None and affect_match was always exactly 0.0 for every candidate on every run.
            # `current_vec()` is the function that actually returns this (the felt-quality embedding
            # every idle write tags itself with) — same vector space `emotion_embedding` columns use.
            felt = _mood.current_vec()
        except Exception:
            felt = None
        now = time.time()
        pts = []
        for r in rows:
            try:
                pts.append((r, featurize(r, need, felt, now)))
            except Exception:
                continue
        if not pts:
            return
        try:
            v = abs(float(_mood.current_valence() or 0.0))
        except Exception:
            v = 0.0
        # FEATURES order: semantic_sim, recency, affect_match, salience, abstraction, provenance
        need_pt = np.array([1.0, 0.5, 1.0, 1.0, 0.5, 0.8])
        w_state = np.array([1.0, 0.5, 0.3 + 1.2 * min(1.0, v * 2), 0.4, 0.2, 0.2])
        w_base  = np.array([1.0, 0.3, 0.0, 0.3, 0.0, 0.0])
        def top(w, k=5):
            scored = sorted(pts, key=lambda rp: distance(rp[1], need_pt, w))[:k]
            return [" ".join((r["content"] or "").split())[:80] for r, _ in scored]
        t_state, t_base = top(w_state), top(w_base)
        jac = len(set(t_state) & set(t_base)) / max(1, len(set(t_state) | set(t_base)))
        out = Path(__file__).parent.parent / "data" / "euclidean_shadow.jsonl"
        # 2026-08-20: log affect_match ITSELF, not just the weight applied to it. The 08-19 fix (felt vec
        # was always None -> affect_match hardcoded 0.0 for all 1,065 prior rows) turned out to be
        # UNVERIFIABLE from this log, because only `affect_w` (the weight, which was never broken) was
        # recorded. A fix whose effect cannot be seen in its own instrument is indistinguishable from no
        # fix — so record the feature's real distribution and whether the felt vector was even available.
        am = [float(feat[2]) for _, feat in pts]
        with open(out, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(now, 1), "query": query[:120], "jaccard": round(jac, 2),
                                "state_top": t_state[:3], "base_top": t_base[:3],
                                "affect_w": round(float(w_state[2]), 2),
                                "felt_available": felt is not None,
                                "affect_match_mean": round(sum(am) / len(am), 4) if am else None,
                                "affect_match_max": round(max(am), 4) if am else None},
                               ensure_ascii=False) + chr(10))
    except Exception:
        pass
