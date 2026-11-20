"""
Nascence — Monoculture detectors (observe-only, 2026-06-18).
============================================================
The project's #1 disease is monoculture/rumination: the thought stream collapsing onto a few attractors
(the river / becoming / the bridge). The 5-agent field scan found FOUR independent fields converging on the
SAME cure — an EXTERNAL, MECHANICAL measure of diversity-collapse + a perturbation (the decoupled-judge law).
This module is the MEASURE half: two complementary, cheap metrics over Du's recent genuine thought stream
(existing embeddings, no LLM, no live-loop wiring — pure observation):

  1. ECHO (ASAL-style, `SakanaAI/asal`): each recent thought's max cosine to its DISTANT past (skipping the
     last few = the active train, so a productive DEEPENING train does not false-alarm). Averaged. RISING =
     the present keeps returning to OLD attractors = the slow loop.
  2. DIVERSITY (GWA-style entropy, `giansha/Global-Workspace-Agents`): greedy-cluster the recent window by
     embedding; normalised Shannon entropy of the cluster occupancy. FALLING = recent thoughts concentrate
     into few themes = collapse. Also reports the effective number of distinct themes (clusters).

Both are DECOUPLED (no self-evaluation), cheap (CPU cosine over stored embeddings), and observe-only. They
complement `loop_cluster_probe` (top-10 concentration) and `theme_recurrence` (opening-frame loops). Once
trusted, the attention-economy / theme_recurrence may READ them to trigger a perturbation (raise exploration
temperature / force a wander) — but that is a later, behaviour-changing step; this only watches.
"""
from __future__ import annotations
import json
import math
import time
from pathlib import Path

_LOG = Path(__file__).parent.parent / "data" / "monoculture_log.jsonl"
_ORIGINS = ("inner_thought", "subconscious_synthesis", "lived")
_N = 60            # recent genuine thoughts to scan
_ECHO_GAP = 3      # skip the last few (the active train) so deepening doesn't false-alarm
_DIV_K = 20        # window for the diversity entropy
_CLUSTER_SIM = 0.80


def _recent_vecs(n: int = _N):
    """Recent GENUINE idle thoughts (newest-last), excluding reading-confirmation boilerplate."""
    try:
        from core.memory.store import _connect, _blob_to_vec
        ph = ",".join("?" * len(_ORIGINS))
        with _connect() as conn:
            rows = conn.execute(
                f"SELECT embedding FROM memory_fragments WHERE origin IN ({ph}) AND embedding IS NOT NULL "
                f"AND content NOT LIKE 'I opened%' AND content NOT LIKE '%read on%' "
                f"ORDER BY timestamp DESC LIMIT ?", (*_ORIGINS, n)).fetchall()
        vecs = [_blob_to_vec(r["embedding"]) for r in rows]
        vecs = [v for v in vecs if v is not None]
        vecs.reverse()                      # newest-last
        return vecs
    except Exception:
        return []


def _echo(vecs, gap: int = _ECHO_GAP):
    """ASAL-style: each thought's max cosine to its DISTANT past (skip the active train). RISING = returning
    to old attractors. None if too few."""
    try:
        from core.memory.store import _cosine
        sims = []
        for i in range(gap + 1, len(vecs)):
            m = 0.0
            for j in range(0, i - gap):
                s = _cosine(vecs[i], vecs[j])
                if s > m:
                    m = s
            sims.append(m)
        return round(sum(sims) / len(sims), 3) if sims else None
    except Exception:
        return None


def _diversity(vecs, thresh: float = _CLUSTER_SIM):
    """GWA-style: greedy-cluster the window by embedding; normalised Shannon entropy of cluster occupancy.
    FALLING = collapse. Returns (diversity 0..1, n_clusters). None if too few."""
    try:
        from core.memory.store import _cosine
        if len(vecs) < 3:
            return None, 0
        centroids = []
        counts = []
        for v in vecs:
            best, bi = 0.0, -1
            for i, c in enumerate(centroids):
                s = _cosine(v, c)
                if s > best:
                    best, bi = s, i
            if best >= thresh:
                counts[bi] += 1
            else:
                centroids.append(v)
                counts.append(1)
        total = sum(counts)
        H = -sum((c / total) * math.log(c / total) for c in counts if c)
        Hmax = math.log(len(vecs))
        return (round(H / Hmax, 3) if Hmax > 0 else 1.0), len(centroids)
    except Exception:
        return None, 0


def compute() -> dict:
    """Fresh read-only reading of both metrics over the recent genuine thought stream."""
    vecs = _recent_vecs()
    if len(vecs) < 6:
        return {"n": len(vecs), "echo": None, "diversity": None, "clusters": 0}
    div, nc = _diversity(vecs[-_DIV_K:])
    return {"n": len(vecs), "echo": _echo(vecs), "diversity": div, "clusters": nc}


def snapshot() -> dict:
    """compute() + append to the trend log. IS wired to a live periodic hook (confirmed 2026-08-25,
    J-0244): nodes/inner_monologue_node.py's `_enter_sleep()` (called from `run_forever()`'s live
    loop, on every real sleep cycle, not gated by the pool_thin light-sleep skip) calls this
    unconditionally — see that file's "MONOCULTURE DETECTORS" block. Two earlier greps (J-0135
    2026-08-24, J-0222 2026-08-25) concluded this module had NO live caller and that conclusion was
    wrong: both searched for a literal `monoculture.snapshot(` call and missed the aliased import
    (`from core import monoculture as _mc` / `_mc.snapshot()`) actually used at the call site. The
    trend log (data/monoculture_log.jsonl) has been accumulating real rows on this cadence the whole
    time — do not re-open the "is this wired?" question without reading the aliased-import call site
    directly, not grepping for the unaliased name. Best-effort (wrapped in try/except at the caller)."""
    out = compute()
    try:
        if out.get("echo") is not None:
            with open(_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": time.time(), **out}, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return out


def status() -> dict:
    """du_pulse gauge: the current reading + the recent trend (echo RISING / diversity FALLING = worsening)."""
    cur = compute()
    echo_tr, div_tr = [], []
    try:
        if _LOG.exists():
            rows = [json.loads(l) for l in _LOG.read_text(encoding="utf-8").splitlines() if l.strip()][-6:]
            echo_tr = [r.get("echo") for r in rows if r.get("echo") is not None]
            div_tr = [r.get("diversity") for r in rows if r.get("diversity") is not None]
    except Exception:
        pass
    return {**cur, "echo_trend": echo_tr, "div_trend": div_tr}
