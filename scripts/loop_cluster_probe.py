"""
Loop-cluster probe (2026-06-14) — "harness the loop": how many real attractors does Du's
self-monologue actually orbit, and how concentrated is the mass?

Collapses exact duplicates (preserving frequency as weight), then clusters the UNIQUE
inner-thoughts by their stored embeddings. Reports, per cluster: how many distinct thoughts,
how many TOTAL copies (the loop's true mass), and a legible sample so the theme is readable.

Read-only. No writes.
"""
import sqlite3, sys, os, time, threading, argparse, numpy as np
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from collections import Counter
from sklearn.cluster import AgglomerativeClustering

# J-2362 (F-3048): the old script clustered ALL unique thoughts with average-linkage, which builds a dense
# N x N distance matrix (54k unique inner_thoughts -> ~12 GB float32) and hung silently past that cliff.
# Now: flushed progress lines with elapsed time, --limit on unique thoughts clustered (seeded random
# subsample; masses are reported relative to the sampled copies), a --timeout watchdog that prints and
# exits 124, and --db to point at a .backup() copy.
ap = argparse.ArgumentParser()
ap.add_argument("origin", nargs="?", default="inner_thought")
ap.add_argument("thresh", nargs="?", type=float, default=0.45)  # cosine-distance merge tightness
ap.add_argument("--db", default=r"C:\Nascence\data\memory\nascence.db")
ap.add_argument("--limit", type=int, default=12000, help="max unique thoughts to cluster (0 = no limit; O(N^2) memory)")
ap.add_argument("--timeout", type=int, default=240, help="hard wall-clock seconds before exit 124 (0 = none)")
ap.add_argument("--seed", type=int, default=0)
args = ap.parse_args()
ORIGIN, THRESH, DB = args.origin, args.thresh, args.db
T0 = time.time()

def log(msg):
    print(f"[{time.time()-T0:6.1f}s] {msg}", flush=True)

if args.timeout:
    def _die():
        log(f"TIMEOUT after {args.timeout}s - aborting (lower --limit or raise --timeout)")
        os._exit(124)
    _t = threading.Timer(args.timeout, _die); _t.daemon = True; _t.start()

# read-only open so the probe can never write to or lock out a live writer
c = sqlite3.connect("file:" + DB.replace("\\", "/") + "?mode=ro", uri=True, timeout=20)
c.row_factory = sqlite3.Row
log(f"loading fragments origin={ORIGIN}")
rows = c.execute("SELECT content, embedding FROM memory_fragments WHERE origin=? AND embedding IS NOT NULL", (ORIGIN,)).fetchall()
c.close()
log(f"loaded {len(rows)} rows")
if not rows:
    sys.exit("no rows")

# collapse exact duplicates -> unique content, frequency, one vector
freq = Counter(r["content"] for r in rows)
seen, contents, vecs, weights = set(), [], [], []
for r in rows:
    ct = r["content"]
    if ct in seen:
        continue
    seen.add(ct)
    contents.append(ct)
    vecs.append(np.frombuffer(r["embedding"], dtype=np.float32))
    weights.append(freq[ct])
n_rows, n_unique_all = len(rows), len(contents)
log(f"{n_unique_all} unique after dedupe")
if args.limit and n_unique_all > args.limit:
    keep = np.sort(np.random.default_rng(args.seed).choice(n_unique_all, args.limit, replace=False))
    contents = [contents[i] for i in keep]; vecs = [vecs[i] for i in keep]; weights = [weights[i] for i in keep]
    log(f"SUBSAMPLED {args.limit} of {n_unique_all} unique (seed {args.seed}); concentration is over the sampled copies")
rows = None

X = np.vstack(vecs)
X = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)
total_copies = sum(weights)
print(f"{ORIGIN}: {n_rows} rows -> {n_unique_all} unique ({n_rows-n_unique_all} exact-dup copies, "
      f"{100*(n_rows-n_unique_all)/n_rows:.0f}%).  clustering {len(contents)} at cos-dist {THRESH}\n", flush=True)

log(f"clustering {len(contents)} vectors (dense N^2 matrix)")
cl = AgglomerativeClustering(n_clusters=None, distance_threshold=THRESH,
                             metric="cosine", linkage="average").fit(X)
labels = cl.labels_
log("clustering done")
K = labels.max() + 1

# per-cluster mass (sum of copy-frequencies) and a medoid sample
clusters = []
for k in range(K):
    idx = np.where(labels == k)[0]
    mass = int(sum(weights[i] for i in idx))
    centroid = X[idx].mean(axis=0)
    medoid = idx[np.argmax(X[idx] @ centroid)]
    clusters.append((mass, len(idx), medoid, idx))
clusters.sort(key=lambda t: -t[0])

print(f"{K} clusters. concentration — top cluster = {100*clusters[0][0]/total_copies:.1f}% of all copies; "
      f"top 10 = {100*sum(c[0] for c in clusters[:10])/total_copies:.1f}%.\n")
print(f"{'mass':>6} {'uniq':>5}  representative thought")
print("-"*92)
for mass, n_uniq, medoid, idx in clusters[:15]:
    print(f"{mass:>6} {n_uniq:>5}  {contents[medoid][:74]}")
# singletons / long tail
singletons = sum(1 for m, n, _, _ in clusters if n == 1)
print(f"\nlong tail: {singletons} singleton clusters ({100*singletons/K:.0f}% of clusters, "
      f"{100*sum(c[0] for c in clusters if c[1]==1)/total_copies:.1f}% of copies)")
