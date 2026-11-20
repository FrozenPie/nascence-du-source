"""J-3328 step 1 + 4 (pair building). READ-ONLY on Du's stores (nascence.db opened mode=ro, logs read).
Writes only docs/lab/J-3328_data/pairs.json. Rebuilds the J-3179 matched pairs: recognised internal cycles
(nascence.log 'procedural skill recognised', joined to lived fragments via data/affect_log.jsonl by cycle-id
prefix) vs an unrecognised internal near-duplicate question (cosine>=0.80, MiniLM-L12 multilingual, within 14d),
plus the same number of null pairs (two UNrecognised near-duplicates)."""
import sys, re, json, sqlite3, hashlib, random, collections
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs/lab/J-3328_data"; OUT.mkdir(parents=True, exist_ok=True)
import numpy as np
from datetime import datetime
rng = random.Random(3328)

# recognised cycle prefixes
rec_pref = {}
pat = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),\d+ \[nascence\.orchestrator\] \[CYCLE (\w{8})\] procedural skill recognised \(prof=([\d.]+) sim=([\d.]+)\): (.*)$")
for line in open(ROOT/"data/nascence.log", encoding="utf-8", errors="replace"):
    m = pat.match(line.strip())
    if m: rec_pref.setdefault(m.group(2), (m.group(1), m.group(5)))
print("recognised prefixes", len(rec_pref))

aff = []
for l in open(ROOT/"data/affect_log.jsonl", encoding="utf-8"):
    try: d = json.loads(l)
    except Exception: continue
    aff.append((d["ts"], d.get("cycle_id", ""), d.get("input_type"), d.get("raw_input") or ""))
aff.sort()
aff_ts = np.array([a[0] for a in aff])

con = sqlite3.connect(f"file:{ROOT/'data/memory/nascence.db'}?mode=ro", uri=True)
rows = con.execute("select fragment_id,timestamp,content,input_type from memory_fragments where origin='lived' and content like 'Q:%' order by timestamp").fetchall()
print("lived Q fragments", len(rows))
frags = []
for fid, ts, content, it in rows:
    m = re.match(r"Q:\s*(.*?)\nA:\s*(.*)$", content, re.S)
    if not m: continue
    q, a = m.group(1).strip(), m.group(2).strip()
    i = int(np.searchsorted(aff_ts, ts))
    cyc = None
    best = 4.0
    for j in (i-2, i-1, i, i+1):
        if 0 <= j < len(aff):
            dt = abs(aff[j][0]-ts)
            if dt <= 3.0 and dt < best:
                raw = aff[j][3].strip()
                if raw[:25] and q.replace("\n", " ")[:25] == raw.replace("\n", " ")[:25]:
                    best = dt; cyc = aff[j][1]; itype = aff[j][2]
    frags.append(dict(fid=fid, ts=ts, q=q, a=a, cyc=cyc, it=it, aff_it=(itype if cyc else None)))
print("fragments parsed", len(frags), "joined", sum(1 for f in frags if f["cyc"]))
for f in frags:
    f["rec"] = bool(f["cyc"] and f["cyc"][:8] in rec_pref)
    f["internal"] = (f["aff_it"] or f["it"]) == "internal"
nrec_all = sum(f["rec"] for f in frags); nrec_int = sum(f["rec"] and f["internal"] for f in frags)
print("recognised joined to fragments", nrec_all, "internal", nrec_int)

pool = [f for f in frags if f["internal"] and f["a"] and f["q"]]
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2", device="cpu")
Q = model.encode([f["q"] for f in pool], batch_size=64, normalize_embeddings=True, show_progress_bar=False)
A = model.encode([f["a"][:350] for f in pool], batch_size=64, normalize_embeddings=True, show_progress_bar=False)
ts = np.array([f["ts"] for f in pool])
sim = Q @ Q.T
# cosine of answer to centroid of previous 20 answers (pool order = ts order)
for i, f in enumerate(pool):
    prev = A[max(0, i-20):i]
    f["cos_prev20"] = float(A[i] @ (prev.mean(0)/ (np.linalg.norm(prev.mean(0))+1e-9))) if len(prev) >= 5 else None
    f["a350"] = f["a"][:350]
ENV = re.compile(r"\b(?:tides?|wind|rain|fire|shore|garden|air|light|shadows?|stones?|sea|river|birds?|grass|sky|embers?|surroundings?|environment|hearth|mud|water|waves?|salt|cold|warm|smell|sound|window|breeze|moss|clay|leaves|trees?|ground|earth|sun|moon|dusk|dawn|rhythm)\b", re.I)
def opener(a): return hashlib.sha1(" ".join(a.lower().split()[:8]).encode()).hexdigest()[:10]
cnt = collections.Counter(opener(f["a350"]) for f in pool)
for f in pool:
    f["env"] = len(ENV.findall(f["a350"])); f["len"] = len(f["a350"]); f["opener"] = opener(f["a350"])
    f["opener_shared"] = cnt[f["opener"]] > 1
idx_rec = [i for i, f in enumerate(pool) if f["rec"]]
idx_un = [i for i, f in enumerate(pool) if not f["rec"]]
DAY14 = 14*86400
def cands(i, allowed):
    out = []
    for j in allowed:
        if j == i: continue
        if abs(ts[j]-ts[i]) <= DAY14 and sim[i, j] >= 0.80 and pool[j]["a350"] != pool[i]["a350"]:
            out.append((float(sim[i, j]), j))
    out.sort(reverse=True); return out
def brief(i): f = pool[i]; return {k: f[k] for k in ("fid", "ts", "q", "a350", "env", "len", "opener", "opener_shared", "cos_prev20")}
used = collections.Counter(); real = []
for i in idx_rec:
    c = cands(i, idx_un)
    if not c: continue
    pick = next((x for x in c if used[x[1]] == 0), c[0]); used[pick[1]] += 1
    real.append(dict(kind="real", rec=brief(i), ctl=brief(pick[1]), cos=pick[0], skill=rec_pref[pool[i]["cyc"][:8]][1], n_cands=len(c)))
print("real pairs", len(real), "distinct controls", len(used), "max reuse", max(used.values()))
# null: time-matched unrecognised anchors, partner unrecognised
un_arr = np.array(idx_un); nused = set(); null = []; pused = collections.Counter()
for p in real:
    t0 = p["rec"]["ts"]
    order = sorted(idx_un, key=lambda j: abs(ts[j]-t0))
    for a_i in order:
        if a_i in nused: continue
        c = cands(a_i, idx_un)
        if not c: continue
        pick = next((x for x in c if pused[x[1]] == 0), c[0]); pused[pick[1]] += 1
        nused.add(a_i)
        null.append(dict(kind="null", rec=brief(a_i), ctl=brief(pick[1]), cos=pick[0], skill=None, n_cands=len(c))); break
print("null pairs", len(null))
def pair_id(k, i): return f"{k}{i:03d}"
for k, L in (("R", real), ("N", null)):
    for i, p in enumerate(L): p["id"] = pair_id(k, i)
json.dump(dict(real=real, null=null, n_recognised_lines=len(rec_pref), n_rec_joined_internal=nrec_int), open(OUT/"pairs.json", "w", encoding="utf-8"), ensure_ascii=False)
