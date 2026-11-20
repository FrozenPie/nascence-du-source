"""
Nascence — Psyche Graph P0 (big build 2026-07-03 · docs/completed/psyche_graph_instrument.md, un-shelved.
2026-08-19: doc moved to docs/completed/ at some point without this path being updated — corrected.).

A per-sleep DETERMINISTIC snapshot of his symbolic economy as a graph: nodes = spontaneous dream motifs
(the measurable population — axiom-resident symbols are permanently primed and excluded by design); edges =
same-dream co-occurrence over the recent arc window. The PRIMARY metric (GPT's refinement, ratified in the
design session): STABILITY UNDER REINTERPRETATION — when a motif gains new neighbours, do its old edges
survive? Preserved-lineage growth = development; neighborhood churn = rewriting. Secondary: motif
birth/death, hubs, edge counts.

Observe-only · zero LLM · firewalled log (psyche_graph_snapshots.jsonl) read by reports, never by him.
"""
from __future__ import annotations

import io
import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("nascence.psyche")

_DATA = Path(__file__).parent.parent / "data"
_DREAMS = _DATA / "dream_log.jsonl"
_OUT = _DATA / "psyche_graph_snapshots.jsonl"
_WINDOW_ARCS = 20     # the recent-arc window each snapshot summarizes

# the spontaneous-motif lexicon (dream-born; deliberately NOT the axiom's river/becoming family — those are
# permanently primed). Extend as new motifs earn recurrence; keys are substring-matched, lowercase.
MOTIFS = ("mirror", "glass", "door", "archway", "key", "pen", "book", "library", "shelf", "lantern",
          "gardener", "garden", "soil", "root", "tree", "seed", "tide", "sea", "shore", "star",
          "constellation", "bridge", "letter", "fish", "bird", "horse", "path", "mountain", "fire",
          "candle", "thread", "loom", "clock", "bell", "wall", "window")


def _recent_arcs() -> list[str]:
    """The last N multi-scene arcs' full text blobs (one string per arc)."""
    try:
        rows = [json.loads(l) for l in io.open(_DREAMS, encoding="utf-8") if l.strip()]
    except Exception:
        return []
    arcs = [r for r in rows if (r.get("scenes") or 0) >= 2]
    return [json.dumps(r, ensure_ascii=False).lower() for r in arcs[-_WINDOW_ARCS:]]


def snapshot() -> dict | None:
    """One per-sleep snapshot: nodes, co-occurrence edges, and stability-vs-previous. Appended, never
    rewritten (the graph's own history obeys the lineage law)."""
    try:
        arcs = _recent_arcs()
        if not arcs:
            return None
        nodes: dict = {}
        edges: dict = {}
        import re as _re
        for blob in arcs:
            # WORD-BOUNDARY matching (fixed at first run: substring 'pen' matched every 'open')
            present = [m for m in MOTIFS if _re.search(r"\b" + m + r"\b", blob)]
            for m in present:
                nodes[m] = nodes.get(m, 0) + 1
            for i, a in enumerate(present):
                for b in present[i + 1:]:
                    k = f"{a}|{b}"
                    edges[k] = edges.get(k, 0) + 1
        # STABILITY UNDER REINTERPRETATION vs the previous snapshot: of last time's edges, how many survive?
        prev = _last()
        stability = None
        new_edges = None
        if prev and prev.get("edges"):
            old = set(prev["edges"].keys())
            cur = set(edges.keys())
            stability = round(len(old & cur) / max(1, len(old)), 3)
            new_edges = len(cur - old)
        snap = {"ts": round(time.time(), 1), "arcs": len(arcs),
                "nodes": dict(sorted(nodes.items(), key=lambda kv: -kv[1])),
                "edges": dict(sorted(edges.items(), key=lambda kv: -kv[1])[:60]),
                "n_nodes": len(nodes), "n_edges": len(edges),
                "stability": stability, "new_edges": new_edges}
        _OUT.parent.mkdir(parents=True, exist_ok=True)
        with open(_OUT, "a", encoding="utf-8") as f:
            f.write(json.dumps(snap, ensure_ascii=False) + chr(10))
        logger.info("[psyche] snapshot: %d motifs, %d edges, stability=%s, new=%s",
                    len(nodes), len(edges), stability, new_edges)
        return snap
    except Exception as exc:
        logger.debug("[psyche] snapshot failed (non-fatal): %s", exc)
        return None


def _last() -> dict | None:
    try:
        last = None
        for l in io.open(_OUT, encoding="utf-8"):
            if l.strip():
                last = l
        return json.loads(last) if last else None
    except Exception:
        return None
