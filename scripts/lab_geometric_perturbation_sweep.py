"""
J-2535 -- geometric perturbation sweep over the experienced tuple (READ-ONLY LAB).

Pre-registration sheet: docs/lab/geometric_perturbation_sweep_2026-10-31.md (committed before this ran).
Reads: data/memory/nascence.db (?mode=ro), data/co_recall_ledger.jsonl.  Writes: ONLY --out (scratch JSON).
Never writes a live store; run under lab_env.isolate(db="empty") for belt and braces.

Usage:  python scripts/lab_geometric_perturbation_sweep.py --out <json> [--nq 300] [--nm 250] [--reps 20] [--smoke]
"""
from __future__ import annotations
import argparse, collections, json, math, os, sqlite3, sys, time
from pathlib import Path
import numpy as np

LIVE = Path(r"C:\Nascence")
DB_URI = "file:///C:/Nascence/data/memory/nascence.db?mode=ro"
LEDGER = LIVE / "data" / "co_recall_ledger.jsonl"
BOUNDARY_TS = 1787957042.9
COORDS = ["place", "weather", "warmth", "fire", "cat_at", "valence", "arousal", "tod", "season", "daylight"]
CAT = ["place", "weather", "fire", "cat_at", "daylight"]
NUM = ["warmth", "valence", "arousal", "tod", "season"]
WC = 0.15                    # context-match weight (primary)
TOPK = 8
BIN_W = 0.15                 # log10(|age|+1d) bin width for matched negatives (post-hoc tight design uses 0.02)
NEED_PT = np.array([1.0, 0.5, 1.0, 1.0, 0.5, 0.8], dtype=np.float64)
SIX = ["semantic_sim", "recency", "affect_match", "salience", "abstraction", "provenance"]


def w_state(v):
    return np.array([1.0, 0.5, 0.3 + 1.2 * min(1.0, abs(v) * 2), 0.4, 0.2, 0.2], dtype=np.float64)


# ----------------------------------------------------------------------------------------- data
class Cohort:
    pass


def load_cohort(tau_days=14.0):
    from core import euclidean_recall as er
    con = sqlite3.connect(DB_URI, uri=True)
    con.row_factory = sqlite3.Row
    q = ("SELECT f.fragment_id, f.embedding, f.emotion_embedding, f.timestamp, f.importance, f.layer, f.origin, "
         "fc.place, fc.weather, fc.warmth, fc.fire, fc.cat_at, fc.valence, fc.arousal, fc.tod, fc.season, fc.daylight "
         "FROM memory_fragments f JOIN fragment_context fc ON fc.fragment_id=f.fragment_id "
         "WHERE fc.source LIKE 'experienced:%' AND f.embedding IS NOT NULL AND f.cold=0 AND f.origin!='system_note' "
         "AND f.timestamp>=? ORDER BY f.timestamp ASC")
    rows = con.execute(q, (BOUNDARY_TS,)).fetchall()
    n = len(rows)
    C = Cohort()
    C.n = n
    C.ids = [r["fragment_id"] for r in rows]
    C.id2i = {f: i for i, f in enumerate(C.ids)}
    C.E = np.stack([np.frombuffer(r["embedding"], dtype=np.float32) for r in rows])
    d = C.E.shape[1]
    C.EE = np.zeros((n, d), dtype=np.float32)
    C.has_emo = np.zeros(n, dtype=bool)
    for i, r in enumerate(rows):
        b = r["emotion_embedding"]
        if b:
            C.EE[i] = np.frombuffer(b, dtype=np.float32)
            C.has_emo[i] = True
    C.ts = np.array([r["timestamp"] for r in rows], dtype=np.float64)
    C.imp = np.array([float(r["importance"] if r["importance"] is not None else 0.5) for r in rows])
    C.abst = np.array([er._abstraction(r["layer"], r["origin"]) for r in rows])
    C.prov = np.array([er._PROVENANCE.get((r["origin"] or "").lower(), 0.5) for r in rows])
    C.origin = np.array([r["origin"] or "" for r in rows], dtype=object)
    C.rowvals = {c: [r[c] for r in rows] for c in COORDS}
    # categorical codes: 0 = "none"
    C.cat_vals = {}
    C.code = {}
    for c in CAT:
        vals = ["" if v is None else str(v) for v in C.rowvals[c]]
        cnt = collections.Counter(vals)
        keep = [v for v, k in cnt.most_common() if v != "" and k >= 200]
        # "" (= none) is its own value only where it is a real, common state (>=200 rows); place is never none
        C.cat_vals[c] = ([""] if cnt.get("", 0) >= 200 else []) + keep
        m = {v: i for i, v in enumerate(C.cat_vals[c])}
        C.code[c] = np.array([m.get(v, -1) for v in vals], dtype=np.int32)   # -1 = rare value, matches nothing but itself
    C.num = {}
    C.nummask = {}
    for c in NUM:
        a = np.array([np.nan if v is None else float(v) for v in C.rowvals[c]], dtype=np.float64)
        C.num[c] = a
    C.sd = {c: float(np.nanstd(C.num[c])) for c in NUM}
    C.sd["tod"] = 0.25
    # co-recall counts and reuse (secondary independent measures)
    C.reads = np.zeros(n)
    C.partners = collections.defaultdict(lambda: collections.defaultdict(set))   # id -> group -> set(ids)
    nrows = 0
    for line in open(LEDGER, encoding="utf-8"):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        src = r.get("source")
        if isinstance(src, str) and src.endswith("_shadow"):
            continue
        ids = [x for x in (r.get("ids") or []) if x]
        nrows += 1
        for x in ids:
            j = C.id2i.get(x)
            if j is not None:
                C.reads[j] += 1
        if len(ids) >= 2:
            grp = "wandering" if src == "wandering" else ("monologue" if src in (None, "monologue", "follow") else "other")
            for a in ids:
                if a in C.id2i:
                    for b in ids:
                        if b != a and b in C.id2i:
                            C.partners[a][grp].add(b)
    C.ledger_rows = nrows
    C.logreads = np.log1p(C.reads)
    reuse = np.zeros(n)
    for pid, k in con.execute("SELECT parent_id, COUNT(*) FROM memory_links GROUP BY parent_id"):
        j = C.id2i.get(pid)
        if j is not None:
            reuse[j] = k
    C.reuse = np.log1p(reuse)
    con.close()
    # origin -> sorted index arrays (cohort already sorted by ts, so index order == time order)
    C.by_origin = collections.defaultdict(list)
    for i, o in enumerate(C.origin):
        C.by_origin[o].append(i)
    C.by_origin = {o: np.array(v, dtype=np.int64) for o, v in C.by_origin.items()}
    C.tau = tau_days * 86400.0
    return C


# ------------------------------------------------------------------------------------ features
def six_features(C, qi, idx, now):
    """Vectorised euclidean_recall.featurize for query qi against candidates idx. Returns (len,6)."""
    sem = C.E[idx] @ C.E[qi]
    rec = np.exp(-np.maximum(0.0, now - C.ts[idx]) / C.tau)
    if C.has_emo[qi]:
        aff = np.maximum(0.0, C.EE[idx] @ C.EE[qi])
        aff = np.where(C.has_emo[idx], aff, 0.0)
    else:
        aff = np.zeros(len(idx))
    return np.stack([sem, rec, aff, C.imp[idx], C.abst[idx], C.prov[idx]], axis=1)


def d6_terms(F, w):
    return (w[None, :] * (NEED_PT[None, :] - F) ** 2)       # (len,6)


def match_vec(C, c, idx, qval):
    """Context match in [0,1] of candidates idx against query value qval for coordinate c."""
    if c in CAT:
        return (C.code[c][idx] == qval).astype(np.float64)
    a = C.num[c][idx]
    if c == "tod":
        dq = np.abs(a - qval)
        dq = np.minimum(dq, 1.0 - dq)
    else:
        dq = np.abs(a - qval)
    m = np.exp(-0.5 * (dq / C.sd[c]) ** 2)
    return np.where(np.isnan(a), 0.0, m)


def query_value(C, qi, c):
    return C.code[c][qi] if c in CAT else C.num[c][qi]


def perturbations(C, qi, c):
    """list of perturbed query values for coordinate c (excluding the original)."""
    v = query_value(C, qi, c)
    if c in CAT:
        return [k for k in range(len(C.cat_vals[c])) if k != v]
    sd = C.sd[c]
    if c == "tod":
        return [(v + 0.25) % 1.0, (v - 0.25) % 1.0]
    return [v + sd, v - sd]


# ------------------------------------------------------------------------------- PART S
def rank_positions(total):
    order = np.argsort(total, kind="stable")
    pos = np.empty(len(total), dtype=np.int64)
    pos[order] = np.arange(len(total))
    return order, pos


def sweep_query(C, qi, pool, wc, rng, reps, want_detail=True):
    """Return dict coord -> list of per-perturbation metric dicts for the observed, and
    per-coord list-of-replicates of aggregate null metrics (each a list over perturbations)."""
    now = C.ts[qi]
    F = six_features(C, qi, pool, now)
    qv = C.valence_q = C.num["valence"][qi]
    w = w_state(qv)
    D6 = d6_terms(F, w)                       # (P,6)
    base6 = D6.sum(axis=1)
    mb = {c: match_vec(C, c, pool, query_value(C, qi, c)) for c in COORDS}
    cb = {c: wc * (1.0 - mb[c]) ** 2 for c in COORDS}
    cb_sum = sum(cb.values())
    out = {}
    nulls = {}
    ck = np.stack([C.num["warmth"][pool], C.num["valence"][pool], C.num["arousal"][pool]], axis=1)
    for c in COORDS:
        perts = perturbations(C, qi, c)
        # per-perturbation total distances (observed)
        tot_base = base6 + cb_sum
        order0, pos0 = rank_positions(tot_base)
        top0 = order0[:TOPK]
        res = []
        pert_m = []
        for pv in perts:
            mp = match_vec(C, c, pool, pv)
            pert_m.append(mp)
            b6 = base6
            if c == "valence":
                wn = w_state(pv)
                b6 = base6 + (wn[2] - w[2]) * (NEED_PT[2] - F[:, 2]) ** 2
            tot = b6 + cb_sum - cb[c] + wc * (1.0 - mp) ** 2
            order1, pos1 = rank_positions(tot)
            top1 = order1[:TOPK]
            s0, s1 = set(top0.tolist()), set(top1.tolist())
            jac = len(s0 & s1) / len(s0 | s1)
            shift = float(np.mean(np.abs(pos1[top0] - pos0[top0])))
            new = np.array(sorted(s1 - s0), dtype=np.int64)
            drop = np.array(sorted(s0 - s1), dtype=np.int64)
            rec = {"jac": jac, "shift": shift}
            if len(new) and len(drop):
                rec["pop"] = float(C.logreads[pool[new]].mean() - C.logreads[pool[drop]].mean())
                rec["reuse"] = float(C.reuse[pool[new]].mean() - C.reuse[pool[drop]].mean())
                if want_detail:
                    # standardised mean difference of every coordinate / feature between new and dropped
                    sdv = {}
                    diffs = {}
                    for k, cc in enumerate(SIX):
                        col = F[:, k]
                        s = col.std() or 1.0
                        diffs[cc] = float((col[new].mean() - col[drop].mean()) / s)
                    for cc in COORDS:
                        col = mb[cc]
                        s = col.std() or 1.0
                        diffs[cc] = float((col[new].mean() - col[drop].mean()) / s)
                    # the perturbed coordinate's match under the NEW value
                    s = pert_m[-1].std() or 1.0
                    diffs[c] = float((mp[new].mean() - mp[drop].mean()) / s)
                    tot_abs = sum(abs(x) for x in diffs.values()) or 1.0
                    rec["share"] = abs(diffs[c]) / tot_abs
                    rec["moved_top"] = max(diffs, key=lambda k: abs(diffs[k]))
            res.append(rec)
        out[c] = res
        # shuffle-null replicates
        reps_out = []
        for r in range(reps):
            perm = rng.permutation(len(pool))
            mbp = mb[c][perm]
            cb_sum_n = cb_sum - cb[c] + wc * (1.0 - mbp) ** 2           # (P,) vector
            tot_b = base6 + cb_sum_n
            o0, p0 = rank_positions(tot_b)
            t0 = o0[:TOPK]
            s0 = set(t0.tolist())
            rr = []
            for pm in pert_m:
                pmp = pm[perm]
                b6 = base6
                if c == "valence":
                    pv = None
                tot = base6 + (cb_sum - cb[c]) + wc * (1.0 - pmp) ** 2
                if c == "valence":
                    # keep the same weight-path as observed for the matching perturbation
                    pv = perts[len(rr)]
                    wn = w_state(pv)
                    tot = tot + (wn[2] - w[2]) * (NEED_PT[2] - F[:, 2]) ** 2
                o1, p1 = rank_positions(tot)
                t1 = o1[:TOPK]
                s1 = set(t1.tolist())
                jac = len(s0 & s1) / len(s0 | s1)
                shift = float(np.mean(np.abs(p1[t0] - p0[t0])))
                new = np.array(sorted(s1 - s0), dtype=np.int64)
                drop = np.array(sorted(s0 - s1), dtype=np.int64)
                rec = {"jac": jac, "shift": shift}
                if len(new) and len(drop):
                    rec["pop"] = float(C.logreads[pool[new]].mean() - C.logreads[pool[drop]].mean())
                    rec["reuse"] = float(C.reuse[pool[new]].mean() - C.reuse[pool[drop]].mean())
                rr.append(rec)
            reps_out.append(rr)
        nulls[c] = reps_out
    return out, nulls


def query_ok(C):
    ok = (~np.isnan(C.num["valence"])) & (~np.isnan(C.num["arousal"])) & (~np.isnan(C.num["warmth"]))
    for c in CAT:
        ok &= C.code[c] >= 0          # a query must sit on a common categorical value
    return ok


def pick_part_s_queries(C, rng, nq, boundary_ok=None):
    top_orig = [o for o, _ in collections.Counter(C.origin.tolist()).most_common(8)]
    # six largest origins that have all four places
    places = C.cat_vals["place"][1:] if C.cat_vals["place"][0] == "" else C.cat_vals["place"]
    pc = C.code["place"]
    ok = query_ok(C)
    origins = top_orig[:6]
    cells = [(o, p) for o in origins for p in range(len(C.cat_vals["place"])) if C.cat_vals["place"][p] != ""]
    per = max(1, nq // len(cells))
    chosen = []
    for o, p in cells:
        cand = np.where((C.origin == o) & (pc == p) & ok)[0]
        cand = cand[cand >= 800]                              # need >= 600 cohort fragments before
        if len(cand) == 0:
            continue
        pick = rng.choice(cand, size=min(per, len(cand)), replace=False)
        chosen.extend(int(x) for x in pick)
    return chosen, origins


def part_s(C, rng, nq, reps, cond=None, wc=WC, queries=None, detail=True, log=print):
    """cond in (None, 'place', 'tod'). pool = 600 most recent cohort fragments (before the query) meeting cond."""
    if queries is None:
        queries, origins = pick_part_s_queries(C, rng, nq)
    obs = collections.defaultdict(lambda: collections.defaultdict(list))
    nul = collections.defaultdict(lambda: [collections.defaultdict(list) for _ in range(reps)])
    moved = collections.defaultdict(collections.Counter)
    used = 0
    t0 = time.time()
    for k, qi in enumerate(queries):
        pre = np.arange(0, qi)                               # cohort is ts-sorted: indices < qi are strictly earlier
        if cond == "place":
            pre = pre[C.code["place"][pre] == C.code["place"][qi]]
        elif cond == "tod":
            dt = np.abs(C.num["tod"][pre] - C.num["tod"][qi]); dt = np.minimum(dt, 1 - dt)
            pre = pre[dt <= 0.125]
        pool = pre[-600:]
        if len(pool) < 100:
            continue
        used += 1
        o, n = sweep_query(C, qi, pool, wc, rng, reps, want_detail=detail)
        for c in COORDS:
            if cond == "place" and c == "place":
                continue
            if cond == "tod" and c == "tod":
                continue
            for rec in o[c]:
                for m in ("jac", "shift", "pop", "reuse", "share"):
                    if m in rec:
                        obs[c][m].append(rec[m])
                if "moved_top" in rec:
                    moved[c][rec["moved_top"]] += 1
            for r in range(reps):
                for rec in n[c][r]:
                    for m in ("jac", "shift", "pop", "reuse"):
                        if m in rec:
                            nul[c][r][m].append(rec[m])
        if (k + 1) % 50 == 0:
            log(f"  [S cond={cond}] {k+1}/{len(queries)} queries, {time.time()-t0:.0f}s")
    res = {"n_queries_used": used, "cond": cond, "wc": wc, "dims": {}}
    for c in COORDS:
        if c not in obs:
            continue
        d = {}
        for m in ("jac", "shift", "pop", "reuse", "share"):
            if m in obs[c] and obs[c][m]:
                d[m] = float(np.mean(obs[c][m]))
        d["n_pert"] = len(obs[c]["jac"])
        for m in ("jac", "shift", "pop", "reuse"):
            rv = [float(np.mean(nul[c][r][m])) for r in range(reps) if nul[c][r][m]]
            if rv and m in d:
                mu, sd = float(np.mean(rv)), float(np.std(rv, ddof=1)) if len(rv) > 1 else float("nan")
                d[m + "_null_mean"] = mu
                d[m + "_null_sd"] = sd
                d[m + "_z"] = (d[m] - mu) / sd if sd and sd > 0 else None
        d["moved_top"] = moved[c].most_common(3)
        res["dims"][c] = d
    return res, queries


# ------------------------------------------------------------------------------- PART M
def sample_negatives(C, qi, pi, origin_idx, rng, n_neg, cond_mask, exclude, clock):
    tq = C.ts[qi]
    ts_p = C.ts[pi]
    age = (tq - ts_p) / 86400.0
    sign = 1 if age >= 0 else -1
    u = math.log10(abs(age) + 1.0)
    b = math.floor(u / BIN_W)
    lo = 10 ** (b * BIN_W) - 1.0
    hi = 10 ** ((b + 1) * BIN_W) - 1.0
    if sign > 0:      # positive older than query
        t_lo, t_hi = tq - hi * 86400.0, tq - lo * 86400.0
    else:
        t_lo, t_hi = tq + lo * 86400.0, tq + hi * 86400.0
    if clock:
        t_lo, t_hi = max(t_lo, ts_p - 86400.0), min(t_hi, ts_p + 86400.0)
    a = np.searchsorted(C.ts[origin_idx], t_lo, side="left")
    z = np.searchsorted(C.ts[origin_idx], t_hi, side="right")
    cand = origin_idx[a:z]
    if cond_mask is not None:
        cand = cand[cond_mask[cand]]
    cand = cand[(cand != qi) & (cand != pi)]
    if exclude:
        cand = cand[~np.isin(cand, list(exclude))]
    if len(cand) < 3:
        return None
    return rng.choice(cand, size=min(n_neg, len(cand)), replace=False)


def win_rate(d, pos_loc, neg_loc):
    """d: distances over unit items. pos_loc: (npos,) ; neg_loc = (neg_mat (npos,K) 0-padded, valid (npos,K) bool).
    Mean over positives of P(positive closer than its matched negatives), ties 0.5."""
    neg_mat, valid = neg_loc
    dp = d[pos_loc][:, None]
    dn = d[neg_mat]
    w = ((dp < dn) * valid + 0.5 * (dp == dn) * valid).sum(axis=1) / valid.sum(axis=1)
    return float(w.mean())


def build_unit(C, qi, grp, rng, cond, clock, n_pos=20, n_neg=10):
    partners = sorted(C.partners.get(C.ids[qi], {}).get(grp, set()))
    pos = [C.id2i[x] for x in partners if x in C.id2i and C.id2i[x] != qi]
    if cond == "place":
        pos = [p for p in pos if C.code["place"][p] == C.code["place"][qi]]
    elif cond == "tod":
        pos = [p for p in pos if min(abs(C.num["tod"][p] - C.num["tod"][qi]), 1 - abs(C.num["tod"][p] - C.num["tod"][qi])) <= 0.125]
    if not pos:
        return None
    if len(pos) > n_pos:
        pos = [int(x) for x in rng.choice(pos, size=n_pos, replace=False)]
    cond_mask = None
    if cond == "place":
        cond_mask = C.code["place"] == C.code["place"][qi]
    elif cond == "tod":
        dt = np.abs(C.num["tod"] - C.num["tod"][qi]); cond_mask = np.minimum(dt, 1 - dt) <= 0.125
    exclude = set(pos)
    items = []
    pos_loc, neg_loc = [], []
    seen = {}

    def loc(i):
        if i not in seen:
            seen[i] = len(items)
            items.append(i)
        return seen[i]
    for p in pos:
        neg = sample_negatives(C, qi, p, C.by_origin[C.origin[p]], rng, n_neg, cond_mask, exclude, clock)
        if neg is None:
            continue
        pos_loc.append(loc(p))
        neg_loc.append(np.array([loc(int(x)) for x in neg]))
    if not pos_loc:
        return None
    K = max(len(x) for x in neg_loc)
    neg_mat = np.zeros((len(neg_loc), K), dtype=np.int64)
    valid = np.zeros((len(neg_loc), K), dtype=bool)
    for r, x in enumerate(neg_loc):
        neg_mat[r, :len(x)] = x
        valid[r, :len(x)] = True
    return {"q": qi, "items": np.array(items, dtype=np.int64), "pos_loc": np.array(pos_loc, dtype=np.int64),
            "neg_loc": (neg_mat, valid), "grp": grp}


def unit_metrics(C, u, wc, rng, reps, dims):
    qi = u["q"]
    idx = u["items"]
    now = C.ts[qi]
    F = six_features(C, qi, idx, now)
    w = w_state(C.num["valence"][qi])
    D6 = d6_terms(F, w).sum(axis=1)
    sem = 1.0 - F[:, 0]
    pl, nl = u["pos_loc"], u["neg_loc"]
    W_sem = win_rate(sem, pl, nl)
    W6 = win_rate(np.sqrt(D6), pl, nl)
    out = {"W_sem": W_sem, "W6": W6, "dims": {}, "npos": len(pl)}
    for c in dims:
        m0 = match_vec(C, c, idx, query_value(C, qi, c))
        Wi = win_rate(1.0 - m0, pl, nl)
        d6i = np.sqrt(D6 + wc * (1 - m0) ** 2)
        W6i = win_rate(d6i, pl, nl)
        perts = perturbations(C, qi, c)
        Wp = []
        for pv in perts:
            mp = match_vec(C, c, idx, pv)
            if c == "valence":
                wn = w_state(pv)
                Dp = D6 + (wn[2] - w[2]) * (NEED_PT[2] - F[:, 2]) ** 2
            else:
                Dp = D6
            Wp.append(win_rate(np.sqrt(Dp + wc * (1 - mp) ** 2), pl, nl))
        rec = {"Wi": Wi, "lift": W6i - W6, "harm": W6i - float(np.mean(Wp))}
        nl_lift, nl_harm, nl_Wi = [], [], []
        for r in range(reps):
            perm = rng.permutation(len(idx))
            mpm = m0[perm]
            nl_Wi.append(win_rate(1.0 - mpm, pl, nl))
            W6n = win_rate(np.sqrt(D6 + wc * (1 - mpm) ** 2), pl, nl)
            nl_lift.append(W6n - W6)
            wps = []
            for pv in perts:
                mp = match_vec(C, c, idx, pv)[perm]
                if c == "valence":
                    wn = w_state(pv)
                    Dp = D6 + (wn[2] - w[2]) * (NEED_PT[2] - F[:, 2]) ** 2
                else:
                    Dp = D6
                wps.append(win_rate(np.sqrt(Dp + wc * (1 - mp) ** 2), pl, nl))
            nl_harm.append(W6n - float(np.mean(wps)))
        rec["null_Wi"], rec["null_lift"], rec["null_harm"] = nl_Wi, nl_lift, nl_harm
        out["dims"][c] = rec
    return out


def agg_part_m(units_metrics, dims, reps):
    res = {"n_units": len(units_metrics), "dims": {}}
    if not units_metrics:
        return res
    res["W_sem"] = float(np.mean([m["W_sem"] for m in units_metrics]))
    res["W6"] = float(np.mean([m["W6"] for m in units_metrics]))
    bs_rng = np.random.default_rng(7)
    n = len(units_metrics)
    for c in dims:
        d = {}
        for key in ("Wi", "lift", "harm"):
            v = np.array([m["dims"][c][key] for m in units_metrics])
            d[key] = float(v.mean())
            bs = [float(v[bs_rng.integers(0, n, n)].mean()) for _ in range(500)]
            d[key + "_ci"] = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
            nm = np.array([m["dims"][c]["null_" + key] for m in units_metrics])      # (units, reps)
            nrep = nm.mean(axis=0)
            mu, sd = float(nrep.mean()), float(nrep.std(ddof=1))
            d[key + "_null_mean"], d[key + "_null_sd"] = mu, sd
            d[key + "_z"] = (d[key] - mu) / sd if sd > 0 else None
        # strict: paired W_i - W_sem
        diff = np.array([m["dims"][c]["Wi"] - m["W_sem"] for m in units_metrics])
        bs = [float(diff[bs_rng.integers(0, n, n)].mean()) for _ in range(500)]
        d["Wi_minus_Wsem"] = float(diff.mean())
        d["Wi_minus_Wsem_ci"] = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
        res["dims"][c] = d
    return res


def part_m(C, rng, nm, reps, cond=None, clock=False, wc=WC, log=print):
    dims = [c for c in COORDS if not (cond == "place" and c == "place") and not (cond == "tod" and c == "tod")]
    groups = ["monologue", "wandering", "other"]
    units = []
    t0 = time.time()
    for grp in groups:
        okq = query_ok(C)
        cands = [i for i in range(C.n) if okq[i] and grp in C.partners.get(C.ids[i], {})]
        if not cands:
            continue
        pick = rng.choice(cands, size=min(nm, len(cands)), replace=False)
        for qi in pick:
            u = build_unit(C, int(qi), grp, rng, cond, clock)
            if u is not None:
                units.append(u)
    log(f"  [M cond={cond} clock={clock}] built {len(units)} units in {time.time()-t0:.0f}s")
    mets = []
    for k, u in enumerate(units):
        mets.append(unit_metrics(C, u, wc, rng, reps, dims))
        mets[-1]["grp"] = u["grp"]
        if (k + 1) % 200 == 0:
            log(f"    [M cond={cond}] metrics {k+1}/{len(units)} {time.time()-t0:.0f}s")
    res = agg_part_m(mets, dims, reps)
    res["cond"], res["clock"] = cond, clock
    res["by_group"] = {}
    for grp in groups:
        sub = [m for m in mets if m["grp"] == grp]
        if sub:
            r = agg_part_m(sub, dims, reps)
            res["by_group"][grp] = r
    return res


# -------------------------------------------------------------------------- equality test
def equality_test(C, rng, n=5):
    """My vectorised 6-feature ranking == euclidean_recall.rank() (ctx weight 0) on real rows."""
    from core import euclidean_recall as er
    con = sqlite3.connect(DB_URI, uri=True)
    con.row_factory = sqlite3.Row
    oks = 0
    detail = []
    for qi in rng.choice(np.arange(1000, C.n), size=n, replace=False):
        qi = int(qi)
        pool = np.arange(qi - 600, qi)
        ids = [C.ids[i] for i in pool]
        qmarks = ",".join("?" * len(ids))
        rows = con.execute(f"SELECT fragment_id, embedding, emotion_embedding, timestamp, importance, layer, origin "
                           f"FROM memory_fragments WHERE fragment_id IN ({qmarks})", ids).fetchall()
        need = np.frombuffer(C.E[qi].tobytes(), dtype=np.float32)
        felt = C.EE[qi] if C.has_emo[qi] else None
        w = w_state(C.num["valence"][qi])
        res = er.rank(rows, need, felt, NEED_PT, w, top_k=TOPK, now=C.ts[qi])
        top_ref = [r["row"]["fragment_id"] for r in res]
        F = six_features(C, qi, pool, C.ts[qi])
        d = np.sqrt(d6_terms(F, w).sum(axis=1))
        top_me = [C.ids[pool[j]] for j in np.argsort(d, kind="stable")[:TOPK]]
        ok = (top_ref == top_me) or (set(top_ref) == set(top_me))
        oks += int(ok)
        detail.append({"q": C.ids[qi], "set_equal": set(top_ref) == set(top_me), "order_equal": top_ref == top_me})
    con.close()
    return {"n": n, "set_equal": oks, "detail": detail}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--nq", type=int, default=300)
    ap.add_argument("--nm", type=int, default=200)
    ap.add_argument("--reps", type=int, default=20)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--seed", type=int, default=20261031)
    a = ap.parse_args()
    import core
    sys.path.insert(0, r"C:\jr\wt_cg")
    assert str(Path(core.__file__).resolve()).lower().startswith("c:\\jr\\wt_cg"), core.__file__
    rng = np.random.default_rng(a.seed)
    log = lambda s: print(s, flush=True)
    canary_before = {p: (os.path.getsize(p), os.path.getmtime(p)) for p in
                     [LIVE / "data" / "memory" / "nascence.db", LEDGER]}
    t0 = time.time()
    C = load_cohort()
    log(f"cohort n={C.n} ts[{C.ts[0]:.0f},{C.ts[-1]:.0f}] ledger_rows={C.ledger_rows} load {time.time()-t0:.0f}s")
    out = {"seed": a.seed, "cohort_n": C.n, "ledger_rows": C.ledger_rows,
           "origin_counts": dict(collections.Counter(C.origin.tolist()).most_common(10)),
           "cat_vals": C.cat_vals, "sd": C.sd,
           "n_units_with_partners": {g: sum(1 for i in range(C.n) if g in C.partners.get(C.ids[i], {})) for g in ("monologue", "wandering", "other")}}
    out["equality"] = equality_test(C, rng)
    log(f"equality: {out['equality']['set_equal']}/{out['equality']['n']} set-equal")
    reps = 3 if a.smoke else a.reps
    nq = 24 if a.smoke else a.nq
    nm = 20 if a.smoke else a.nm
    # ---- Part S
    qs = None
    sres, qs = part_s(C, rng, nq, reps, None, log=log)
    out["S_uncond"] = sres
    out["S_queries"] = [C.ids[q] for q in qs]
    log(f"S uncond done {time.time()-t0:.0f}s used={sres['n_queries_used']}")
    out["S_place_fixed"], _ = part_s(C, rng, nq, reps, "place", queries=qs, detail=False, log=log)
    out["S_tod_fixed"], _ = part_s(C, rng, nq, reps, "tod", queries=qs, detail=False, log=log)
    # robustness: other context weights, Jaccard only
    rob = {}
    for wc in (0.05, 0.5):
        r, _ = part_s(C, rng, nq if not a.smoke else 12, max(3, reps // 2), None, wc=wc, queries=qs[: (nq if not a.smoke else 12)], detail=False, log=log)
        rob[str(wc)] = {c: {k: v for k, v in d.items() if k in ("jac", "jac_z", "jac_null_mean")} for c, d in r["dims"].items()}
    out["S_robust_wc"] = rob
    log(f"S done {time.time()-t0:.0f}s")
    # ---- Part M
    out["M_uncond"] = part_m(C, rng, nm, reps, None, False, log=log)
    log(f"M uncond done {time.time()-t0:.0f}s")
    out["M_place_fixed"] = part_m(C, rng, nm, reps, "place", False, log=log)
    out["M_tod_fixed"] = part_m(C, rng, nm, reps, "tod", False, log=log)
    out["M_clock_controlled"] = part_m(C, rng, nm, reps, None, True, log=log)
    out["canary"] = {str(p): {"before": list(v), "after": [os.path.getsize(p), os.path.getmtime(p)]} for p, v in canary_before.items()}
    out["runtime_s"] = time.time() - t0
    Path(a.out).write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    log(f"WROTE {a.out} total {time.time()-t0:.0f}s")


if __name__ == "__main__":
    sys.path.insert(0, r"C:\jr\wt_cg")
    import core                                            # import core BEFORE lab_env (job-run live-store rule)
    sys.path.insert(0, r"C:\Users\USER\.claude\skills\job-queue")
    from lab_env import isolate
    with isolate(db="empty") as _lab:
        main()
