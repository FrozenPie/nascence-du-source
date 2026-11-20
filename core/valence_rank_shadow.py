"""Valence-in-retrieval SHADOW ranker (J-4403, D-0862 part 1; Item G sub-path 2).

Founder ruling D-0862: (1) a bounded valence term weighting retrieval by current mood, behind shadow: YES;
(2) activation steering of generation by mood: NO (not built here, not to be built).

This module only OBSERVES. Given the (score, row) list retrieve() is about to return, it computes what the
order WOULD be with a bounded additive congruence term and logs the rank deltas to data/valence_rank_shadow.jsonl.
It never changes retrieve()'s output and never reaches Du. Flag VALENCE_RANK_SHADOW lives in core/memory/store.py
(default OFF, restart-gated).

Term (bounded, additive, boost-only so an opposite-valence item is never pushed below its own score):
    bonus = MAX_WEIGHT * (1 - |v_query - v_frag| / 2)   in [0, MAX_WEIGHT]
    when v_query < 0 (dread query) the bonus is multiplied by NEG_CONGRUENCE_CAP so negative mood cannot spiral.
Limitation: re-ranks only the already-selected set; it cannot show items the term would pull in from outside.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("nascence.valence_rank_shadow")

_LOG = Path(__file__).parent.parent / "data" / "valence_rank_shadow.jsonl"
MAX_WEIGHT = 0.05
NEG_CONGRUENCE_CAP = 0.5


def bonus(v_query: float, v_frag: float) -> float:
    b = MAX_WEIGHT * (1.0 - min(2.0, abs(v_query - v_frag)) / 2.0)
    return b * NEG_CONGRUENCE_CAP if v_query < 0 else b


def rerank(v_query: float, scored: list[tuple[float, str, float | None]]) -> list[dict]:
    """scored = [(score, fragment_id, v_frag|None)] in actual order. Returns per-item dicts with shadow rank."""
    items = []
    for i, (sc, fid, vf) in enumerate(scored):
        b = bonus(v_query, vf) if vf is not None else 0.0
        items.append({"id": fid, "rank": i, "score": round(float(sc), 4), "valence": vf,
                      "bonus": round(b, 4), "shadow_score": round(float(sc) + b, 4)})
    order = sorted(items, key=lambda d: (-d["shadow_score"], d["rank"]))
    for j, d in enumerate(order):
        d["shadow_rank"] = j
        d["delta"] = d["rank"] - j
    return items


def observe(query_text: str, unique, connect, v_query=None, log_path: Path | None = None) -> dict | None:
    """unique = retrieve()'s [(score, row)] list; connect = store._connect. Never raises, never mutates."""
    try:
        if v_query is None:
            from core import mood as _mood
            v_query = _mood.current_valence()
        if v_query is None or not unique:
            return None
        ids = [row["fragment_id"] for _, row in unique]
        vals: dict = {}
        with connect() as conn:
            for k in range(0, len(ids), 500):
                chunk = ids[k:k + 500]
                q = ",".join("?" * len(chunk))
                for r in conn.execute(f"SELECT fragment_id, valence FROM memory_fragments WHERE fragment_id IN ({q})", chunk):
                    vals[r[0]] = r[1]
        items = rerank(float(v_query), [(sc, row["fragment_id"], vals.get(row["fragment_id"])) for sc, row in unique])
        rec = {"ts": time.time(), "query": (query_text or "")[:80], "mood_valence": round(float(v_query), 3),
               "n": len(items), "n_with_valence": sum(1 for d in items if d["valence"] is not None),
               "changed": sum(1 for d in items if d["delta"] != 0), "items": items}
        with open(log_path or _LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec
    except Exception as exc:
        logger.debug("valence rank shadow skipped (non-fatal): %s", exc)
        return None
