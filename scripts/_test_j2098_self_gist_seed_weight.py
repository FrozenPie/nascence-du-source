"""J-2098 (D-0410 B / F-1981): kind=self gist seed damping in associative_recall.recall_trail.
Pure in-memory: injects a synthetic matrix into the module cache (no DB, no live data/ write; the shadow log
path is pointed at a tempdir). Run: python scripts/_test_j2098_self_gist_seed_weight.py"""
import os, sys, tempfile, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import core
import numpy as np
from core import associative_recall as ar
assert str(Path(core.__file__).resolve()).startswith(str(Path(__file__).resolve().parent.parent)), core.__file__
tmp = Path(tempfile.mkdtemp())
ar._SEED_SHARE_LOG = tmp / "seed.jsonl"
rng = np.random.default_rng(0)
N, D = 200, 16
base = rng.normal(size=D)
M = base + 0.6 * rng.normal(size=(N, D))            # all moderately similar to the query
M = (M / np.linalg.norm(M, axis=1, keepdims=True)).astype(np.float32)
sg = np.zeros(N, dtype=bool); sg[:60] = True        # 30% pool share
imp = np.where(sg, 0.85, 0.5).astype(np.float32)    # the leak: self gists at fixed 0.85
def load():
    ar._cache.update(ts=1e18, M=M, ids=[f"f{i}" for i in range(N)], imp=imp,
                     age=np.zeros(N, np.float32), walled=np.zeros(N, bool),
                     origin=["gist" if g else "lived" for g in sg], self_gist=sg)
def share(w, q, seeds_only=True):
    ar.SELF_GIST_SEED_WEIGHT = w; load()
    tr = ar.recall_trail(q)
    top = sorted(tr, key=lambda t: -t["activation"])[:ar.N_SEEDS]
    return sum(int(t["origin"] == "gist") for t in top) / max(1, len(top))
q = (base / np.linalg.norm(base)).astype(np.float32)
pool = 60 / N
def mean_share(w):
    vals = []
    for k in range(40):
        qq = q + 0.3 * rng.normal(size=D).astype(np.float32); qq /= np.linalg.norm(qq)
        vals.append(share(w, qq))
    return sum(vals) / len(vals)
off, on = mean_share(1.0), mean_share(0.75)
print(f"pool={pool:.2f} undamped_seed_share={off:.2f} damped={on:.2f}")
assert off > pool * 1.5, "premise: undamped leak should over-seed"
assert on <= pool * 1.5, f"damped share {on:.2f} exceeds 1.5x pool"
assert on < off
# self-knowledge query: a query aligned with ONE self gist still returns it
ar.SELF_GIST_SEED_WEIGHT = 0.75; load()
tr = ar.recall_trail(M[5])
assert any(t["fragment_id"] == "f5" for t in tr), "self gist unfindable"
rows = [json.loads(l) for l in open(ar._SEED_SHARE_LOG)]
assert rows and "undamped_self_seeds" in rows[0]
print("PASS", len(rows), "shadow rows")
