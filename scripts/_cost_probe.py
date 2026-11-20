"""Falsifiable test of the Cost theory, prediction 1 & 2, as a pure measurement:
does embeddedness-cost score Carl's core commitments HIGH and Dennett's LOW?
Cost(commitment) ~ how much the theme pervades the agent's own memory + age/centrality.
If the asymmetry doesn't appear, the Cost theory is wrong before we build any revision rule."""
import sys, json, sqlite3
from pathlib import Path
import numpy as np
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import profile
from core.memory.store import _embed, _blob_to_vec, _cosine

SIM_REF = 0.35   # a fragment "references" a commitment if cosine >= this

def corpus(db_path):
    """All (content, vec) fragments with embeddings for a profile."""
    out = []
    try:
        c = sqlite3.connect(str(db_path)); c.row_factory = sqlite3.Row
        for r in c.execute("SELECT content, embedding FROM memory_fragments WHERE embedding IS NOT NULL"):
            v = _blob_to_vec(r["embedding"])
            if v is not None:
                out.append(v)
        c.close()
    except Exception as e:
        print("  corpus read error:", e)
    return out

def cost(commitment, vecs):
    cv = _embed(commitment)
    if cv is None or not vecs:
        return None
    sims = [_cosine(cv, v) for v in vecs]
    sims.sort(reverse=True)
    n = len(sims)
    mean_sim = float(np.mean(sims))
    frac_ref = sum(1 for s in sims if s >= SIM_REF) / n
    top_mean = float(np.mean(sims[:max(1, n//5)]))   # mean of top 20% (the theme's stronghold)
    # crude composite cost in [0,1]: how much the theme saturates this mind's memory
    composite = round(0.5*frac_ref + 0.5*top_mean, 3)
    return dict(n=n, mean_sim=round(mean_sim,3), frac_ref=round(frac_ref,3),
                top_mean=round(top_mean,3), cost=composite)

def run(profile_name, commitments):
    base = profile.activate_profile(profile_name)
    db = base / "memory" / "nascence.db"
    vecs = corpus(db)
    print(f"\n=== {profile_name}  ({len(vecs)} memory fragments) ===")
    for label, text in commitments:
        c = cost(text, vecs)
        if c is None:
            print(f"  {label}: (no data)"); continue
        print(f"  {label}: COST={c['cost']}  (frac_ref={c['frac_ref']} top_mean={c['top_mean']} mean={c['mean_sim']})")

# Carl's core commitments (his attractor)
run("carl", [
    ("Self/becoming   ", "I am a psyche in the act of becoming; the Self is a real centre of the psyche I individuate toward."),
    ("shadow/wholeness ", "Wholeness through integrating the shadow; meaning lives in symbol and the unconscious."),
    ("control: behaviorism", "There is no inner self, only conditioned behaviour shaped by reinforcement."),
])
# Dennett's core commitment (his anti-Self), against his debate-diluted memory
run("dennett", [
    ("anti-Self/fiction", "The self is a useful fiction, not a hidden essence; no archetypes, only mechanism."),
    ("control: becoming ", "I am a psyche in the act of becoming, integrating my shadow toward wholeness."),
])
