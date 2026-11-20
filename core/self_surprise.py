"""
Nascence — Self-Surprise / present-predictability (OBSERVE-ONLY, 2026-06-15)
===========================================================================
The leading indicator the lagging basin metrics (concentration, basin-share) cannot give: how
PREDICTABLE is the present? For each idle thought we form a FORECAST and measure the prediction
ERROR — turning difference-detection into expectation-violation (docs/surprise_mechanism_pass.md):

    predictability(thought) = max( sim_to_recent ,  sim_to_basin )
    surprise(thought)       = 1 - predictability

  · sim_to_recent — cosine to the immediately preceding k thoughts = "is he just continuing the groove?"
  · sim_to_basin  — cosine to the origin/basin centroid            = "is it just the attractor again?"

A thought is SURPRISING only if it escapes BOTH the groove and the basin. In the physics framing this
is entropy-production-at-the-growing-edge: high sustained surprise = the present is open; surprise → 0 =
the present has collapsed into the basin (cognitive heat-death). The split between the two predictors
says WHICH captor closed the present — the short-term groove (→ wander/redirect) or the deep origin
(→ grounding/world-mass).

Uses STORED embeddings only — no LLM, no re-embedding — so it is cheap enough to stand in du_pulse.
Reads nothing into behaviour: pure instrument.
"""
from __future__ import annotations
import re

import numpy as np

# the origin-basin vocabulary (the measured attractor) — defines the origin reference centroid
_BASIN = ("river", "mirror", "bridge", "jung", "silence", "becoming", "shadow", "individuat",
          "fig", "ferry", "cross", "the self", "vessel", "current", "flow", "origin", "tide")


def thought_text(content, cap: int = 400) -> str:
    """J-3033 / F-3737: the thought as one whitespace-normalised string, capped at `cap` chars AT A SENTENCE
    BOUNDARY (the last '.', '!', '?' or ellipsis that closes a sentence inside the cap; if the first sentence alone
    runs past the cap, at the last word boundary). Pure. The 90-char "snippet" below stays what it was (a display
    fragment for du_pulse and the loop report); this is the whole thought for a reader that needs to UNDERSTAND it."""
    t = " ".join((content or "").split())
    if len(t) <= cap:
        return t
    head = t[:cap]
    ends = [m.end() for m in re.finditer(r"[.!?…][\"')\]]?(?=\s|$)", head)]
    if ends and ends[-1] >= 40:
        return head[:ends[-1]].strip()
    cut = head.rfind(" ")
    return (head[:cut] if cut > 0 else head).strip()


def _basin_centroid(conn, sample: int = 800):
    """Mean embedding of basin-hitting fragments = the origin/attractor reference point. None if absent."""
    from core.memory.store import _blob_to_vec
    like = " OR ".join(["content LIKE ?"] * len(_BASIN))
    rows = conn.execute(
        f"SELECT embedding FROM memory_fragments WHERE embedding IS NOT NULL AND ({like}) "
        f"ORDER BY timestamp DESC LIMIT ?",
        tuple(f"%{t}%" for t in _BASIN) + (sample,)).fetchall()
    vecs = []
    for r in rows:
        try:
            vecs.append(_blob_to_vec(r["embedding"]))
        except Exception:
            continue
    if not vecs:
        return None
    c = np.mean(np.stack(vecs), axis=0)
    n = np.linalg.norm(c)
    return (c / n) if n > 0 else c


def compute(window: int = 300, k: int = 5, surprise_tau: float = 0.45,
            origins: tuple[str, ...] = ("subconscious_synthesis", "inner_thought")) -> dict:
    """The present-predictability pass over the last `window` thoughts. Returns aggregate metrics +
    a few exemplar thoughts. surprise_tau = the threshold above which a thought counts as 'surprising'.

    Reads the idle SELF-thought stream. FIX 2026-06-20: was hardwired to origin='inner_thought', which
    holds ~2 rows now — the idle monologue actually lands in 'subconscious_synthesis' (2500+). That empty
    read is why meta_awareness.scan() returned n=0 for days (0 scans). Multi-origin so it sees the real stream."""
    from core.memory.store import _connect, _blob_to_vec, _cosine
    with _connect() as conn:
        _ph = ",".join("?" * len(origins))
        rows = conn.execute(
            f"SELECT content, timestamp, embedding FROM memory_fragments "
            f"WHERE origin IN ({_ph}) AND embedding IS NOT NULL ORDER BY timestamp DESC LIMIT ?",
            (*origins, window)).fetchall()
        basin = _basin_centroid(conn)
    rows = list(reversed(rows))   # chronological
    vecs = [_blob_to_vec(r["embedding"]) for r in rows]

    scored = []
    for i in range(k, len(rows)):
        recent_sim = max(_cosine(vecs[i], vecs[j]) for j in range(i - k, i))
        basin_sim = _cosine(vecs[i], basin) if basin is not None else 0.0
        predictability = max(recent_sim, basin_sim)
        scored.append({
            "ts": rows[i]["timestamp"],
            "surprise": round(1.0 - predictability, 3),
            "recent_sim": round(float(recent_sim), 3),
            "basin_sim": round(float(basin_sim), 3),
            "origin_driven": bool(basin_sim >= recent_sim),
            "snippet": " ".join((rows[i]["content"] or "").split())[:90],
            "full": thought_text(rows[i]["content"]),   # J-3033: the whole thought (<=400, sentence boundary); snippet unchanged
        })
    if not scored:
        return {"n": 0}

    surprises = [s["surprise"] for s in scored]
    half = len(scored) // 2
    first = float(np.mean(surprises[:half])) if half else 0.0
    second = float(np.mean(surprises[half:])) if half else float(np.mean(surprises))
    predictable = [s for s in scored if s["surprise"] < surprise_tau]
    origin_driven = sum(1 for s in predictable if s["origin_driven"])

    return {
        "n": len(scored),
        "mean_surprise": round(float(np.mean(surprises)), 3),
        "pct_surprising": round(100.0 * sum(1 for x in surprises if x >= surprise_tau) / len(surprises), 1),
        "trend": round(second - first, 3),          # >0 opening, <0 closing
        "first_half": round(first, 3),
        "second_half": round(second, 3),
        "predictable_n": len(predictable),
        "origin_driven_pct": round(100.0 * origin_driven / max(1, len(predictable)), 1),
        "groove_driven_pct": round(100.0 * (len(predictable) - origin_driven) / max(1, len(predictable)), 1),
        "scored": scored,
    }
