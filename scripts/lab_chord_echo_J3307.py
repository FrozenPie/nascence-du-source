"""J-3307 chord_echo replay (U1 stage 1). Read-only (mode=ro). See docs/lab/J-3307_chord_echo_prereg.md."""
import sqlite3, json, math, sys, random
import numpy as np
from scipy import sparse
DB = "C:/Nascence/data/memory/nascence.db"
OUT = "C:/Nascence/docs/lab/J-3307_chord_echo_results.json"
TB = ((0.66, "high"), (0.33, "mid"), (-1.0, "low")); WB = ((0.66, "warm"), (0.33, "mild"), (-1.0, "cold"))
def tags(r):
    t = set()
    if r["place"]: t.add("place:" + r["place"])
    if r["weather"]: t.add("wx:" + r["weather"])
    if r["standpoint"]: t.add("sp:" + r["standpoint"])
    if r["tide_level"] is not None: t.add("tide:" + next(b for th, b in TB if r["tide_level"] > th))
    if r["warmth"] is not None: t.add("warmth:" + next(b for th, b in WB if r["warmth"] > th))
    if r["cat_at"]: t.add("cat:" + r["cat_at"])
    try:
        for s in json.loads(r["sounds"] or "[]"): t.add("snd:" + s)
    except Exception: pass
    return t
c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True); c.row_factory = sqlite3.Row
rows = [dict(r) for r in c.execute("select fragment_id,tuple_ts,place,weather,sounds,standpoint,tide_level,warmth,cat_at,valence,arousal from fragment_context where source like 'experienced:%' and valence is not null")]
c.close()
rows.sort(key=lambda r: r["tuple_ts"])
N = len(rows); print("rows", N)
TG = [tags(r) for r in rows]
vocab = {}
for t in TG:
    for x in t: vocab.setdefault(x, len(vocab))
df = np.zeros(len(vocab))
ri, ci = [], []
for i, t in enumerate(TG):
    for x in t: ri.append(i); ci.append(vocab[x]); df[vocab[x]] += 1
w = 1.0 / np.log(2 + df)
ntag = np.array([len(t) for t in TG], float)
X = sparse.csr_matrix((np.ones(len(ri)), (ri, ci)), shape=(N, len(vocab)))
norm = 1.0 / (np.sqrt(ntag) + 0.001)
ts = np.array([r["tuple_ts"] for r in rows])
wx = np.array([r["weather"] or "" for r in rows])
snd = [[x for x in t if x.startswith("snd:")] for t in TG]
sndidx = {}
for i, s in enumerate(snd):
    for x in s: sndidx.setdefault(x, []).append(i)
K = 24

def run(outc, gap_days, seed=20261116, nnull=20):
    y_all = np.array([np.nan if r[outc] is None else r[outc] for r in rows], float)
    ok = ~np.isnan(y_all)
    rng = np.random.default_rng(seed)
    qpool = np.where(ok)[0]
    q = np.sort(rng.choice(qpool, size=min(3000, len(qpool)), replace=False))
    gap = gap_days * 86400.0
    perms = [rng.permutation(N) for _ in range(nnull)]
    A1, A2, B, C, E_, NUL = [], [], [], [], [], np.zeros((nnull, len(q)))
    corr = {"b": [], "c": [], "truth": []}
    nt = 0; nw = 0
    pred_b = []
    for k, qi in enumerate(q):
        elig = ok & (np.abs(ts - ts[qi]) >= gap)
        ei = np.where(elig)[0]
        truth = y_all[qi]
        g = y_all[ei].mean()
        E_.append(abs(g - truth))
        # a1 weather
        pool = ei[wx[ei] == wx[qi]] if wx[qi] else ei[:0]
        if wx[qi]: nw += 1
        a1 = y_all[rng.choice(pool, K, replace=len(pool) < K)].mean() if len(pool) else g
        A1.append(abs(a1 - truth))
        # a2 sound
        if snd[qi]:
            key = snd[qi][rng.integers(len(snd[qi]))]
            idx = np.array(sndidx[key]); idx = idx[elig[idx]]
            a2 = y_all[rng.choice(idx, K, replace=len(idx) < K)].mean() if len(idx) else g
        else: a2 = g
        A2.append(abs(a2 - truth))
        # c nearest in time
        near = ei[np.argsort(np.abs(ts[ei] - ts[qi]))[:K]]
        cp = y_all[near].mean(); C.append(abs(cp - truth))
        # b chord
        if TG[qi]:
            nt += 1
            qv = np.zeros(len(vocab))
            for x in TG[qi]: qv[vocab[x]] = w[vocab[x]]
            s = (X @ qv) * norm
            def top(sv):
                sv = np.where(elig, sv, -1.0)
                if (sv > 0).sum() == 0: return None
                m = min(K, int((sv > 0).sum()))
                return np.argpartition(-sv, m - 1)[:m]
            t = top(s)
            bp = y_all[t].mean() if t is not None else g
            for r_i, p in enumerate(perms):
                tn = top(s[p])   # tags permuted across rows: row i carries tags of p[i]
                NUL[r_i, k] = abs((y_all[tn].mean() if tn is not None else g) - truth)
        else:
            bp = g
            NUL[:, k] = abs(g - truth)
        B.append(abs(bp - truth)); pred_b.append(bp)
        corr["b"].append(bp); corr["c"].append(cp); corr["truth"].append(truth)
        if k % 500 == 0: print(outc, gap_days, k, flush=True)
    A1, A2, B, C, E_ = map(np.array, (A1, A2, B, C, E_))
    bs = np.random.default_rng(1)
    def ci(d):
        m = [d[bs.integers(0, len(d), len(d))].mean() for _ in range(2000)]
        return [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]
    nm = NUL.mean(axis=1)
    z = float((nm.mean() - B.mean()) / (nm.std(ddof=1) + 1e-12))
    t = np.array(corr["truth"])
    res = dict(outcome=outc, gap_days=gap_days, n=len(q), cov_tags=nt / len(q), cov_weather=nw / len(q),
        mae=dict(global_mean=float(E_.mean()), single_weather=float(A1.mean()), single_sound=float(A2.mean()), chord=float(B.mean()), nearest_time=float(C.mean()), null_mean=float(nm.mean()), null_sd=float(nm.std(ddof=1))),
        d_a1_minus_b=float((A1 - B).mean()), ci_a1=ci(A1 - B), d_a2_minus_b=float((A2 - B).mean()), ci_a2=ci(A2 - B),
        d_c_minus_b=float((C - B).mean()), z_null=z,
        corr_chord=float(np.corrcoef(corr["b"], t)[0, 1]), corr_nearest=float(np.corrcoef(corr["c"], t)[0, 1]))
    res["pass"] = bool((A1 - B).mean() >= 0.02 and res["ci_a1"][0] > 0 and (A2 - B).mean() >= 0.02 and res["ci_a2"][0] > 0 and B.mean() < C.mean() and z >= 3)
    pl = np.array([rows[i]["place"] or "" for i in q]); wc = np.array([rows[i]["weather"] or "" for i in q])
    strat = {}
    for nm_, lab in (("place", pl), ("weather", wc)):
        strat[nm_] = {l: dict(n=int((lab == l).sum()), chord=float(B[lab == l].mean()), single_weather=float(A1[lab == l].mean()), global_mean=float(E_[lab == l].mean())) for l in sorted(set(lab)) if (lab == l).sum() >= 30}
    res["strata"] = strat
    return res

out = []
for gap in (7, 1):
    for o in ("valence", "arousal"):
        r = run(o, gap); out.append(r)
        print(json.dumps({k: v for k, v in r.items() if k != "strata"}), flush=True)
        json.dump(out, open(OUT, "w"), indent=1)
