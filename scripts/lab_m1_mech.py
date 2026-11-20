"""M1 mechanism tests (J-3993). READ-ONLY, exploratory. Imports lab_m1_memory_reuse.
Run: python scripts/lab_m1_mech.py mech|cc|match 2026-11-01 2026-11-15
"""
import sys, json, re
import numpy as np
sys.path.insert(0, 'C:/Nascence/scripts')
import lab_m1_memory_reuse as m
from lab_m1_memory_reuse import (load, build, prep, fit_all, summarize, bootstrap, EDGES0, DAY, ts_of)

STD = {'understanding', 'understanding_from_guidance', 'gist', 'essay', 'standing_insight', 'resolution', 'seed', 'chapter', 'journal_week'}
BOOK = {'reading', 'study'}


def grp(org):
    return 'std' if org in STD else ('book' if org in BOOK else 'lived')


def emb(b):
    v = np.frombuffer(b, dtype=np.float32)
    return v / (np.linalg.norm(v) + 1e-9)


def mech(t0, t1):
    ev, rows, con = load(t0, t1)
    out = {}
    for name, orgs in (('std', STD), ('book', BOOK)):
        ages, M = build(ev, rows, only_origins=orgs)
        A, Mc, cen = prep(ages, M, True)
        ns = sum(len(x) for x in A)
        out['grp_' + name] = dict(n_served=ns, **summarize(fit_all(A, Mc, cen), ns))
    ages, M = build(ev, rows, exclude_origins=STD)
    A, Mc, cen = prep(ages, M, True)
    ns = sum(len(x) for x in A)
    out['grp_nonstd'] = dict(n_served=ns, **summarize(fit_all(A, Mc, cen), ns))
    out['grp_nonstd_boot'] = bootstrap(A, Mc, cen, 40)
    # first-serve-only hazard
    meta = {r[0]: r for r in rows}
    ages, M = build(ev, rows, exclude_origins=STD)
    seen = set()
    A2 = []
    M2 = M.copy()
    tsv = np.array([e[0] for e in ev])
    for j, (t, ids, _) in enumerate(ev):
        a = []
        for i in ids:
            r = meta.get(i)
            if r is None or r[2] in STD or i in seen:
                continue
            seen.add(i)
            a.append((t - r[1]) / DAY)
            if j + 1 < len(ev):
                ag = (tsv[j + 1:] - r[1]) / DAY
                b = np.searchsorted(EDGES0, ag) - 1
                ok = (b >= 0) & (b < M2.shape[1])
                M2[np.arange(j + 1, len(ev))[ok], b[ok]] -= 1
        A2.append(a)
    A2, Mc2, cen2 = prep(A2, M2, True)
    ns2 = sum(len(x) for x in A2)
    out['first_serve_only_nonstd'] = dict(n_served=ns2, **summarize(fit_all(A2, Mc2, cen2), ns2))
    out['fixed_effects'] = fixed_effects(ev, rows)
    return out


def fixed_effects(ev, rows):
    served = {}
    for t, ids, _ in ev:
        for i in ids:
            served.setdefault(i, []).append(t)
    bk = [r for r in rows if r[2] in BOOK and ((not r[3]) or r[0] in served)]
    ts = np.array([e[0] for e in ev])
    res = {}
    bgrid = [0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.5]
    for key, idx in (('none', None), ('source_id', 4), ('chapter_id', 5)):
        grpk = {}
        for r in bk:
            k = 'ALL' if idx is None else (r[idx] if r[idx] is not None else 'NA_' + r[2])
            grpk.setdefault(k, []).append(r)
        infos = {k: v for k, v in grpk.items() if any(x[0] in served for x in v)}
        prof = []
        for b in bgrid:
            L = 0.0
            for k, frs in infos.items():
                fts = np.sort(np.array([x[1] for x in frs]))
                E = 0.0
                for t in ts:
                    n_av = np.searchsorted(fts, t)
                    a = (t - fts[:n_av]) / DAY
                    E += (a[a >= 0.2] ** (-b)).sum()
                tsm = {x[0]: x[1] for x in frs}
                sa = np.array([(t - tsm[x[0]]) / DAY for x in frs if x[0] in served for t in served[x[0]]])
                sa = sa[sa >= 0.2]
                n = len(sa)
                if n == 0 or E <= 0:
                    continue
                L += n * np.log(n / E) - b * np.log(sa).sum() - n
            prof.append(round(float(L), 1))
        res[key] = dict(strata=len(infos), profile_logL=dict(zip(bgrid, prof)), best_b=bgrid[int(np.argmax(prof))])
    return res


def fetch(con, need):
    E, CT = {}, {}
    need = list(need)
    for k in range(0, len(need), 5000):
        ch = need[k:k + 5000]
        q = f"select fragment_id,embedding,substr(content,1,700) from memory_fragments where fragment_id in ({','.join('?' * len(ch))})"
        for fid, b, ctn in con.execute(q, ch):
            if b is not None:
                E[fid] = emb(b)
            CT[fid] = ctn or ''
    return E, CT


def case_control(t0, t1, ncontrol=40, seed=7, topic_window=10):
    from sklearn.linear_model import LogisticRegression
    ev, rows, con = load(t0, t1)
    rng = np.random.default_rng(seed)
    rows_s = sorted([r for r in rows if not r[3]], key=lambda r: r[1])
    ts_arr = np.array([r[1] for r in rows_s])
    ids_arr = np.array([r[0] for r in rows_s])
    meta = {r[0]: r for r in rows}
    need = set()
    plan = []
    for j, (t, ids, _) in enumerate(ev):
        need.update(ids)
        hi = np.searchsorted(ts_arr, t - 0.2 * DAY)
        if hi < 100:
            continue
        ctrl = list(ids_arr[rng.integers(0, hi, ncontrol)])
        cases = [i for i in ids if i in meta and (t - meta[i][1]) / DAY >= 0.2]
        plan.append((j, t, cases, ctrl))
        need.update(cases)
        need.update(ctrl)
    E, CT = fetch(con, need)
    pur = []
    for l in open('C:/Nascence/data/concerns_log.jsonl'):
        r = json.loads(l)
        if r['source'] == 'frontier' and r['text'].startswith('pursuing:'):
            pur.append((r['ts'], r['text'][9:]))
    pur.sort()
    pts = np.array([p[0] for p in pur])
    stop = set('the and that this with from have what how why not but are was for your about which their they them would could should into more some than then there these those does just like when where while whether'.split())
    tok = lambda s: set(w for w in re.findall(r"[a-z]{4,}", s.lower()) if w not in stop)
    topic = {}
    hist = []
    for j, (t, ids, _) in enumerate(ev):
        vs = [E[i] for h in hist[-topic_window:] for i in h if i in E]
        topic[j] = np.mean(vs, 0) if vs else None
        hist.append(ids)
    X, y = [], []
    for j, t, cases, ctrl in plan:
        tv = topic[j]
        if tv is None:
            continue
        tv = tv / (np.linalg.norm(tv) + 1e-9)
        pi = np.searchsorted(pts, t) - 1
        ptok = tok(pur[pi][1]) if pi >= 0 else set()
        for lab, lst in ((1, cases), (0, ctrl)):
            for i in lst:
                if i not in E:
                    continue
                r = meta[i]
                g = grp(r[2])
                ov = len(ptok & tok(CT.get(i, ''))) / max(len(ptok), 1)
                X.append([np.log((t - r[1]) / DAY), float(E[i] @ tv), ov, g == 'std', g == 'book'])
                y.append(lab)
    X = np.array(X, float)
    y = np.array(y)
    res = {'n_rows': int(len(y)), 'n_cases': int(y.sum()), 'controls_per_event': ncontrol}
    mu, sd = X.mean(0), X.std(0) + 1e-9

    def fit(cols):
        Z = (X[:, cols] - mu[cols]) / sd[cols]
        mdl = LogisticRegression(penalty=None, max_iter=1000).fit(Z, y)
        p = np.clip(mdl.predict_proba(Z)[:, 1], 1e-12, 1 - 1e-12)
        return float((y * np.log(p) + (1 - y) * np.log(1 - p)).sum()), (mdl.coef_[0] / sd[cols]).round(4).tolist()

    for name, cols in (('age only', [0]), ('sim only', [1]), ('age+group', [0, 3, 4]), ('age+group+sim', [0, 3, 4, 1]), ('age+group+sim+pursuit', [0, 3, 4, 1, 2])):
        ll, co = fit(cols)
        res[name] = dict(logL=round(ll, 1), coef_per_unit=co, order='logage,std,book,sim,pursuit'.split(',')[:0] or None)
    res['coef_order'] = 'columns in model order: logage, [std, book], [sim], [pursuit]'
    return res


def matched(t0, t1, nchunks=6, nbins_sim=10, seed=3, B=200):
    ev, rows, con = load(t0, t1)
    tmid = ev[len(ev) // 2][0]
    early = [e for e in ev if e[0] < tmid]
    late = [e for e in ev if e[0] >= tmid]
    meta = {r[0]: r for r in rows}
    served_early = {}
    for t, ids, _ in early:
        for i in ids:
            served_early[i] = served_early.get(i, 0) + 1
    served_late = {}
    for t, ids, _ in late:
        for i in ids:
            served_late[i] = served_late.get(i, 0) + 1
    pool = [r for r in rows if r[1] < tmid - 0.2 * DAY and (not r[3] or r[0] in served_early)]
    pool = [r for r in pool if r[2] not in STD]
    q = "select fragment_id,embedding from memory_fragments where embedding is not null and timestamp < ? and cold = 0 and origin not in (%s)" % ','.join('?' * len(STD))
    emap = {}
    for fid, b in con.execute(q, [tmid - 0.2 * DAY] + list(STD)):
        emap[fid] = emb(b)
    ids_all = [r[0] for r in pool if r[0] in emap]
    need = [i for i in served_early if i not in emap and i in meta and meta[i][2] not in STD]
    E2, _ = fetch(con, need)
    emap.update(E2)
    ids_all = [r[0] for r in pool if r[0] in emap]
    Mx = np.stack([emap[i] for i in ids_all])
    # topic vectors per chunk of the early window (mean embedding of what was served in the chunk)
    ch = np.array_split(np.arange(len(early)), nchunks)
    tv = []
    for c in ch:
        vs = [emap[i] for k in c for i in early[k][1] if i in emap]
        v = np.mean(vs, 0)
        tv.append(v / np.linalg.norm(v))
    S = Mx @ np.stack(tv).T
    simmax = S.max(1)
    age0 = np.array([(tmid - meta[i][1]) / DAY for i in ids_all])
    g = np.array([1 if meta[i][2] in BOOK else 0 for i in ids_all])
    se = np.array([served_early.get(i, 0) > 0 for i in ids_all])
    sl = np.array([served_late.get(i, 0) > 0 for i in ids_all])
    agebin = np.digitize(np.log(age0), np.linspace(np.log(0.2), np.log(400), 13))
    simbin = np.digitize(simmax, np.quantile(simmax, np.linspace(0, 1, nbins_sim + 1)[1:-1]))
    key = agebin * 1000 + simbin * 10 + g
    # stratified comparison (Mantel-Haenszel style): within stratum, P(late | early served) vs P(late | not)
    from collections import defaultdict
    st = defaultdict(lambda: [0, 0, 0, 0])  # n_se, k_se, n_ns, k_ns
    for k_, a, b in zip(key, se, sl):
        s = st[k_]
        if a:
            s[0] += 1; s[1] += int(b)
        else:
            s[2] += 1; s[3] += int(b)

    def mh(stt):
        num = den = 0.0
        d_w = d_num = 0.0
        for n1, k1, n0, k0 in stt:
            if n1 == 0 or n0 == 0:
                continue
            n = n1 + n0
            num += k1 * n0 / n
            den += k0 * n1 / n
            w = n1 * n0 / n
            d_num += w * (k1 / n1 - k0 / n0)
            d_w += w
        return (num / den if den else float('nan')), (d_num / d_w if d_w else float('nan'))

    rr, dd = mh(st.values())
    # bootstrap over fragments within strata is heavy; bootstrap strata-cells by resampling fragments
    rng = np.random.default_rng(seed)
    idx_by = defaultdict(list)
    for n_, k_ in enumerate(key):
        idx_by[k_].append(n_)
    rrs, dds = [], []
    for b in range(B):
        stb = []
        for k_, ii in idx_by.items():
            ii = np.array(ii)
            jj = ii[rng.integers(0, len(ii), len(ii))]
            a, c = se[jj], sl[jj]
            stb.append([int(a.sum()), int((a & c).sum()), int((~a).sum()), int((~a & c).sum())])
        r_, d_ = mh(stb)
        rrs.append(r_); dds.append(d_)
    return dict(tmid=tmid, early_events=len(early), late_events=len(late), pool=len(ids_all), early_served=int(se.sum()),
                raw_late_rate_served_early=float(sl[se].mean()), raw_late_rate_not=float(sl[~se].mean()),
                MH_rate_ratio=round(rr, 3), MH_rate_diff=round(dd, 5),
                rr_ci=[round(float(x), 3) for x in np.nanpercentile(rrs, [2.5, 97.5])],
                diff_ci=[round(float(x), 5) for x in np.nanpercentile(dds, [2.5, 97.5])],
                strata=len(st))


if __name__ == '__main__':
    which, a, b = sys.argv[1], sys.argv[2], sys.argv[3]
    f = {'mech': mech, 'cc': case_control, 'match': matched}[which]
    print(json.dumps(f(ts_of(a), ts_of(b)), indent=1, default=float))
