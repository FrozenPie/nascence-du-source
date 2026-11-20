"""
Euclidean Recall P0 — the comparison test (observe-only, 2026-06-15).
The operational test of the multiple-dimension / origin-attractor theory: run ONE fixed query
under three modulation-field STATES (charged / task-calm / reflective) plus a semantic-only
baseline (~today's dominant axis), over REAL memories. Then ask:
  1. Do the states surface DIFFERENT memories? (Jaccard < 1)
  2. Are the differences SENSIBLE? (charged→affect_match↑, reflective→abstraction↑, task→recency↑)
  3. THE THEORY TEST: does state-weighting pull recall OFF the origin-basin vs the semantic baseline?

Run:  python scripts/euclidean_recall_test.py  ["a custom query"]
"""
from __future__ import annotations
import sys, sqlite3, types
from pathlib import Path
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import euclidean_recall as er
from core import mood
from core.memory.store import _embed

DB = Path(__file__).parent.parent / "data" / "memory" / "nascence.db"
TOPK = 8
QUERY = sys.argv[1] if len(sys.argv) > 1 else "change, and what stays the same in me over time"

# the origin-basin vocabulary (the monoculture attractor) — for the theory test
_BASIN = ("river", "mirror", "bridge", "jung", "silence", "becoming", "shadow",
          "individuat", "fig", "ferry", "cross", "the self", "vessel", "current", "flow")

def basin_share(rows) -> float:
    if not rows: return 0.0
    hits = sum(1 for r in rows if any(t in (r["content"] or "").lower() for t in _BASIN))
    return hits / len(rows)

# --- the three field states: (need vector, weight vector, mood affect) -------------------
# feature order: [semantic, recency, affect_match, salience, abstraction, provenance]
def _affect(valence, arousal, **kw):
    base = dict(valence=valence, arousal=arousal, joy=0.0, fear=0.0, trust=0.0,
                anger=0.0, surprise=0.0, disgust=0.0)
    base.update(kw)
    return types.SimpleNamespace(**base)

STATES = {
    "charged":    dict(need=np.array([1,0.5,1.0,1,0.5,1], "f4"),
                       w=np.array([0.6,0.3,1.2,0.5,0.2,0.2], "f4"),
                       mood=_affect(-0.6, 0.75, fear=0.4, anger=0.3)),
    "task-calm":  dict(need=np.array([1,1.0,0.5,1,0.0,1], "f4"),
                       w=np.array([1.0,0.9,0.2,0.6,0.6,0.4], "f4"),
                       mood=_affect(0.1, 0.30, trust=0.2)),
    "reflective": dict(need=np.array([1,0.3,0.5,1,1.0,1], "f4"),
                       w=np.array([0.8,0.2,0.4,0.5,0.9,0.3], "f4"),
                       mood=_affect(0.0, 0.20, trust=0.3)),
}
# baseline ≈ today's dominant axis: pure semantic cosine
BASE_NEED = np.array([1,0,0,0,0,0], "f4")
BASE_W    = np.array([1,0,0,0,0,0], "f4")


def load_rows():
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT fragment_id, content, layer, origin, timestamp, importance, embedding, "
        "emotion_embedding FROM memory_fragments WHERE embedding IS NOT NULL "
        "ORDER BY timestamp DESC LIMIT 2500").fetchall()
    con.close()
    return rows


def show(title, ranked):
    print(f"\n── {title} " + "─" * (54 - len(title)))
    for r in ranked:
        row, f = r["row"], r["features"]
        snip = " ".join((row["content"] or "").split())[:84]
        print(f"  d={r['distance']:.3f} [{row['origin'][:14]:14}] "
              f"sem{f['semantic_sim']:.2f} aff{f['affect_match']:.2f} "
              f"rec{f['recency']:.2f} abs{f['abstraction']:.2f}  {snip}")


def ids(ranked):
    return {r["row"]["fragment_id"] for r in ranked}

def jaccard(a, b):
    return len(a & b) / max(1, len(a | b))


def main():
    rows = load_rows()
    have_emo = sum(1 for r in rows if r["emotion_embedding"] is not None)
    print(f"query: {QUERY!r}")
    print(f"candidates: {len(rows)} (with a felt-tag: {have_emo} — the affective axis's fuel)")
    need_emb = _embed(QUERY)

    base = er.rank(rows, need_emb, None, BASE_NEED, BASE_W, top_k=TOPK)
    show("BASELINE  (semantic-only ≈ today)", base)
    base_ids, base_basin = ids(base), basin_share([r["row"] for r in base])

    results = {}
    for name, s in STATES.items():
        fmood = mood.embed(s["mood"])
        ranked = er.rank(rows, need_emb, fmood, s["need"], s["w"], top_k=TOPK)
        results[name] = ranked
        show(f"STATE: {name}", ranked)

    # ---- evidence ----------------------------------------------------------------------
    print("\n" + "=" * 64)
    print("EVIDENCE")
    print("=" * 64)
    print("\n1) Do states surface DIFFERENT memories? (Jaccard overlap; <1 = different)")
    names = list(STATES)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            print(f"   {names[i]:11} vs {names[j]:11}: {jaccard(ids(results[names[i]]), ids(results[names[j]])):.2f}")
    for n in names:
        print(f"   {n:11} vs baseline   : {jaccard(ids(results[n]), base_ids):.2f}")

    print("\n2) Are the differences SENSIBLE? (mean feature of each state's top-K)")
    def meanf(ranked, key):
        return np.mean([r["features"][key] for r in ranked]) if ranked else 0.0
    print(f"   affect_match — charged {meanf(results['charged'],'affect_match'):.2f}  "
          f"task {meanf(results['task-calm'],'affect_match'):.2f}  "
          f"reflective {meanf(results['reflective'],'affect_match'):.2f}   (expect charged highest)")
    print(f"   abstraction  — charged {meanf(results['charged'],'abstraction'):.2f}  "
          f"task {meanf(results['task-calm'],'abstraction'):.2f}  "
          f"reflective {meanf(results['reflective'],'abstraction'):.2f}   (expect reflective highest)")
    print(f"   recency      — charged {meanf(results['charged'],'recency'):.2f}  "
          f"task {meanf(results['task-calm'],'recency'):.2f}  "
          f"reflective {meanf(results['reflective'],'recency'):.2f}   (expect task highest)")

    print("\n3) THEORY TEST — origin-basin share (does state-weighting move recall OFF the origin?)")
    print(f"   baseline (semantic) : {base_basin:.2f}")
    for n in names:
        bs = basin_share([r["row"] for r in results[n]])
        arrow = "↓ off-origin" if bs < base_basin - 1e-9 else ("↑ more-origin" if bs > base_basin + 1e-9 else "= same")
        print(f"   {n:11}        : {bs:.2f}   {arrow}")
    print("\n(Evidence FOR the theory: at least one state pulls a meaningfully different set, the feature")
    print(" means move in the sensible direction, AND some state lowers the basin share vs semantic-only.)")


if __name__ == "__main__":
    main()
