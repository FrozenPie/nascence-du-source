"""M1 memory re-use analysis (J-3993, atlas maths_of_mind_atlas sec 6.1/6.3/10). READ-ONLY.
Reads data/ask_recency_shadow.jsonl and data/memory/nascence.db (mode=ro). Writes nothing to data/.
Usage: python scripts/lab_m1_memory_reuse.py base --t0 ISO --t1 ISO [--out FILE]   (pre-registered fit)
       python scripts/lab_m1_memory_reuse.py mech --t0 ISO --t1 ISO               (mechanism tests)
"""
import sys, json, sqlite3, argparse, datetime as dt
import numpy as np
from scipy.optimize import minimize
DAY = 86400.0
NB = 240
EDGES = np.logspace(np.log10(0.2/1.0), np.log10(400.0), NB + 1)  # age edges in days (0.2 d .. 400 d)
EDGES0 = np.concatenate([[1e-4], EDGES])  # bin 0 = 1e-4..0.2 d (young)

def ts_of(s): return dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc).timestamp()

def load(t0, t1, root='C:/Nascence'):
    ev = []
    for l in open(f'{root}/data/ask_recency_shadow.jsonl'):
        r = json.loads(l)
        if t0 <= r['ts'] < t1 and r.get('without_ids'):
            ev.append((r['ts'], r['without_ids'], r.get('with_ids', [])))
    ev.sort(key=lambda x: x[0])
    c = sqlite3.connect(f'file:{root}/data/memory/nascence.db?mode=ro', uri=True)
    rows = c.execute("select fragment_id,timestamp,origin,cold,source_id,chapter_id,source_type from memory_fragments").fetchall()
    return ev, rows, c

def exposure_counts(ev, fts_sorted, mask_sorted):
    """per event, available count per age bin (age bins EDGES0). mask applies to sorted ts array."""
    M = np.zeros((len(ev), len(EDGES0) - 1))
    for i, (t, _, _) in enumerate(ev):
        # fragment ts in (t - edge_hi, t - edge_lo]
        lo_ts = t - EDGES0[::-1] * DAY  # ascending timestamps
        idx = np.searchsorted(fts_sorted, lo_ts, side='right')
        cnt = np.diff(idx)[::-1]  # from youngest bin to oldest
        M[i] = cnt
    return M

def build(ev, rows, drop_young=True, only_origins=None, exclude_origins=None, need_source=None):
    """returns served ages (per event list), per-event exposure matrix, served meta"""
    served_ids = set(i for _, ids, _ in ev for i in ids)
    keep = []
    for fid, ts, org, cold, sid, ch, st in rows:
        if only_origins is not None and org not in only_origins: continue
        if exclude_origins is not None and org in exclude_origins: continue
        if cold and fid not in served_ids: continue
        keep.append((ts, fid))
    keep.sort()
    fts = np.array([k[0] for k in keep])
    M = exposure_counts(ev, fts, None)
    meta = {r[0]: r for r in rows}
    ages = []
    for t, ids, _ in ev:
        a = []
        for i in ids:
            r = meta.get(i)
            if r is None or (only_origins is not None and r[2] not in only_origins) or (exclude_origins is not None and r[2] in exclude_origins): continue
            a.append((t - r[1]) / DAY)
        ages.append(a)
    return ages, M

CEN = np.sqrt(EDGES0[:-1] * EDGES0[1:])

def prep(ages, M, drop_young):
    lo = 1 if drop_young else 0
    A = [np.array([x for x in a if (x >= EDGES0[1] if drop_young else x > 0)]) for a in ages]
    return A, M[:, lo:], CEN[lo:]

def fit_all(A, M, cen, w=None, which=('power', 'exp', 'mix', 'powfloor')):
    n = len(A)
    w = np.ones(n) if w is None else w
    sa = np.concatenate([a for a in A]) if n else np.array([])
    sw = np.concatenate([np.full(len(a), wi) for a, wi in zip(A, w)])
    Eb = (w[:, None] * M).sum(0)
    la = np.log(np.maximum(sa, 1e-9))
    out = {}
    def ll(lam_served, lam_bin): return float((sw * np.log(np.maximum(lam_served, 1e-300))).sum() - (Eb * lam_bin).sum())
    ncen = cen
    def f_power(p): return -ll(np.exp(p[0] - np.exp(p[1]) * 0 - p[1] * la), np.exp(p[0] - p[1] * np.log(ncen)))
    def f_exp(p): return -ll(np.exp(p[0] - sa / np.exp(p[1])), np.exp(p[0] - ncen / np.exp(p[1])))
    def lam_mix(p, a): return np.exp(p[0]) * np.exp(-a / np.exp(p[2])) + np.exp(p[1]) * np.exp(-a / np.exp(p[3]))
    def f_mix(p): return -ll(lam_mix(p, sa), lam_mix(p, ncen))
    def lam_pf(p, a): return np.exp(p[0]) * a ** (-p[1]) + np.exp(p[2])
    def f_pf(p): return -ll(lam_pf(p, sa), lam_pf(p, ncen))
    n0 = max(len(sa), 1) / max(Eb.sum(), 1)
    c0 = np.log(n0)
    r = minimize(f_power, [c0, 0.8], method='Nelder-Mead', options={'xatol': 1e-5, 'fatol': 1e-6, 'maxiter': 2000}); out['power'] = (-r.fun, r.x, 2)
    if 'exp' in which:
        best = None
        for t in (3, 30, 300):
            r = minimize(f_exp, [c0, np.log(t)], method='Nelder-Mead', options={'maxiter': 2000}); best = r if best is None or r.fun < best.fun else best
        out['exp'] = (-best.fun, best.x, 2)
    if 'mix' in which:
        best = None
        for t1, t2 in ((1, 20), (2, 60), (0.5, 10)):
            r = minimize(f_mix, [c0, c0 - 3, np.log(t1), np.log(t2)], method='Nelder-Mead', options={'maxiter': 6000, 'xatol': 1e-5, 'fatol': 1e-7}); best = r if best is None or r.fun < best.fun else best
        out['mix'] = (-best.fun, best.x, 4)
    if 'powfloor' in which:
        best = None
        for d in (-12, -9, -7):
            r = minimize(f_pf, [c0, 0.9, d], method='Nelder-Mead', options={'maxiter': 6000, 'xatol': 1e-5, 'fatol': 1e-7}); best = r if best is None or r.fun < best.fun else best
        out['powfloor'] = (-best.fun, best.x, 3)
    return out

def summarize(out, nserved):
    s = {}
    for k, (L, x, npar) in out.items():
        s[k] = dict(logL=round(L, 2), k=npar, AIC=round(2 * npar - 2 * L, 2), BIC=round(npar * np.log(max(nserved, 2)) - 2 * L, 2), par=[round(float(v), 4) for v in x])
    return s

def bootstrap(A, M, cen, B=200, seed=1, which=('power', 'exp', 'mix'), blocks=None):
    """blocks: optional per-event block id (e.g. ts//21600 for 6-hour blocks); resamples whole blocks."""
    rng = np.random.default_rng(seed)
    n = len(A); sl = []; dAIC_exp = []; dAIC_mix = []
    if blocks is not None:
        ub, inv = np.unique(blocks, return_inverse=True)
    for b in range(B):
        if blocks is None:
            w = np.bincount(rng.integers(0, n, n), minlength=n).astype(float)
        else:
            wb = np.bincount(rng.integers(0, len(ub), len(ub)), minlength=len(ub)).astype(float)
            w = wb[inv]
        o = fit_all(A, M, cen, w, which)
        sl.append(o['power'][1][1])
        ns = float(sum(w[i] * len(A[i]) for i in range(n)))
        a = {k: 2 * v[2] - 2 * v[0] for k, v in o.items()}
        dAIC_exp.append(a['exp'] - a['power']); 
        if 'mix' in a: dAIC_mix.append(a['mix'] - a['power'])
    q = lambda v: [round(float(x), 3) for x in np.percentile(v, [2.5, 50, 97.5])]
    return dict(slope_ci=q(sl), dAIC_exp_minus_power=q(dAIC_exp), dAIC_mix_minus_power=q(dAIC_mix) if dAIC_mix else None)

if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'base':
    ap = argparse.ArgumentParser(); ap.add_argument('mode'); ap.add_argument('--t0'); ap.add_argument('--t1'); ap.add_argument('--keep_young', action='store_true'); ap.add_argument('--B', type=int, default=100)
    a = ap.parse_args()
    ev, rows, _ = load(ts_of(a.t0), ts_of(a.t1))
    ages, M = build(ev, rows)
    A, Mc, cen = prep(ages, M, not a.keep_young)
    ns = sum(len(x) for x in A)
    print('events', len(ev), 'served ages kept', ns)
    o = fit_all(A, Mc, cen)
    print(json.dumps(summarize(o, ns), indent=1))
    print(json.dumps(bootstrap(A, Mc, cen, a.B, blocks=np.array([int(e[0] // 21600) for e in ev]))))


def prereg(t0, t1, B=1000, excl_heavy=False, snapshot=None):
    """PRE-REGISTERED primary analysis (atlas section 6.4). nonstd origins, ages 0.2-48 d, 4 models, 6h block bootstrap."""
    from lab_m1_mech import STD
    ev, rows, _ = load(t0, t1)
    if snapshot:  # cold flag as of the window start; fragments absent from the snapshot (created later) keep today's flag
        import gzip, csv
        snap = {r['id']: int(r['cold']) for r in csv.DictReader(gzip.open(snapshot, 'rt'))}
        rows = [(r[0], r[1], r[2], snap.get(r[0], r[3]), r[4], r[5], r[6]) for r in rows]
    if excl_heavy:
        from collections import Counter
        cn = Counter(i for _, ids, _ in ev for i in ids); heavy = {i for i, k in cn.items() if k >= 20}
        ev = [(t, [i for i in ids if i not in heavy], w) for t, ids, w in ev]
    ages, M = build(ev, rows, exclude_origins=STD)
    A, Mc, cen = prep(ages, M, True)
    keep = cen <= 48.0
    Mc = Mc[:, keep]; cen = cen[keep]
    A = [a[a <= 48.0] for a in A]
    ns = sum(len(x) for x in A)
    o = fit_all(A, Mc, cen)
    res = dict(events=len(ev), n_served=ns, fits=summarize(o, ns))
    blocks = np.array([int(e[0] // 21600) for e in ev]); ub, inv = np.unique(blocks, return_inverse=True)
    rng = np.random.default_rng(11)
    rows_b = []
    for b in range(B):
        wb = np.bincount(rng.integers(0, len(ub), len(ub)), minlength=len(ub)).astype(float)
        ob = fit_all(A, Mc, cen, wb[inv])
        aic = {k: 2 * v[2] - 2 * v[0] for k, v in ob.items()}
        rows_b.append((ob['power'][1][1], aic['exp'] - aic['powfloor'], aic['mix'] - aic['powfloor'], aic['power'] - aic['powfloor'], ob['powfloor'][1][1]))
    R = np.array(rows_b)
    q = lambda v: [round(float(x), 3) for x in np.percentile(v, [2.5, 50, 97.5])]
    res['boot'] = dict(power_slope=q(R[:, 0]), powfloor_slope=q(R[:, 4]), dAIC_exp_minus_powfloor=q(R[:, 1]), dAIC_mix_minus_powfloor=q(R[:, 2]), dAIC_power_minus_powfloor=q(R[:, 3]), B=B)
    return res


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'prereg':
    sys.path.insert(0, 'C:/Nascence/scripts')
    print(json.dumps(prereg(ts_of(sys.argv[2]), ts_of(sys.argv[3]), B=int(sys.argv[4]) if len(sys.argv) > 4 else 1000, snapshot=(sys.argv[5] if len(sys.argv) > 5 else None), excl_heavy=(len(sys.argv) > 6 and sys.argv[6] == 'heavy')), indent=1))
