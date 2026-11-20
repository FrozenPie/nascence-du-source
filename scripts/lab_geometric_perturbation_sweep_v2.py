"""
J-2638 -- geometric perturbation sweep v2 (READ-ONLY LAB). Follow-up of J-2535.

Pre-registration sheet: docs/lab/geometric_perturbation_sweep_v2_2026-10-31.md (committed c25db4a3 before this ran).
Reuses the J-2535 harness (scripts/lab_geometric_perturbation_sweep.py, imported, unchanged) with:
  * matched negatives in age bins of width 0.02 (v1.BIN_W patched; J-2535 primary was 0.15),
  * a pure-clock pseudo-coordinate clk beside every dimension and lift computed over a ranker already containing clk,
  * test populations: per-source co-recall partners, and subset G = partners that arrived by a memory_links
    (lattice descend) walk rather than by embedding similarity.
Reads: data/memory/nascence.db (?mode=ro), data/co_recall_ledger.jsonl, data/felt_recall_shadow.jsonl.
Writes ONLY --out. Run under lab_env.isolate(db="empty") with the lab root patched to --lab-root.

Usage: python scripts/lab_geometric_perturbation_sweep_v2.py --out <json> --lab-root <dir> [--nm 250] [--reps 20] [--smoke]
"""
from __future__ import annotations
import argparse, collections, json, math, os, sqlite3, sys, time
from pathlib import Path
import numpy as np

WT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WT))
sys.path.insert(0, str(WT / "scripts"))

LIVE = Path(r"C:\Nascence")
DB_URI = "file:///C:/Nascence/data/memory/nascence.db?mode=ro"
LEDGER = LIVE / "data" / "co_recall_ledger.jsonl"
FELT = LIVE / "data" / "felt_recall_shadow.jsonl"
CANARY = [LIVE / "data" / "memory" / "nascence.db", LEDGER, FELT]
WC = 0.15
CLK_CAP_DAYS = 60.0
MIN_UNITS = 40
GSUB = ["G", "G_distilled_from", "G_relates_to", "G_duplicate_of"]
GROUPS = ["monologue", "wandering", "curiosity", "follow", "pursuits", "dream", "grand_work", "recall_act",
          "study_note", "essay"]


def src_group(src):
    if src in (None, "monologue"):
        return "monologue"
    return src if src in GROUPS else "other"


# ------------------------------------------------------------------------------ ledger / census
def read_ledger(C, v1):
    con = sqlite3.connect(DB_URI, uri=True)
    links = {}
    for p, c, t in con.execute("SELECT parent_id, child_id, link_type FROM memory_links"):
        links[(p, c)] = t
    con.close()
    linked = lambda a, b: (a, b) in links or (b, a) in links
    census = collections.defaultdict(lambda: collections.Counter())
    partners = collections.defaultdict(lambda: collections.defaultdict(set))
    rows_ts = []                                   # (ts, src, ids) for the felt join
    all_ids = set()
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
        ids = list(dict.fromkeys(x for x in (r.get("ids") or []) if x))
        all_ids.update(ids)
        if ids:
            rows_ts.append((float(r.get("ts") or 0.0), src, ids))
        if len(ids) < 2:
            continue
        g = src_group(src)
        cs = census[g]
        cs["rows"] += 1
        # descend-reached ids in this row: p is a memory_links child of another id r in the row
        walked = {p: [(q, links[(q, p)]) for q in ids if q != p and (q, p) in links] for p in ids}
        walked = {p: rs for p, rs in walked.items() if rs}
        cs["rows_with_walked_id"] += int(bool(walked))
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                cs["pairs"] += 1
                cs["pairs_linked"] += int(linked(a, b))
                if a in C.id2i and b in C.id2i:
                    cs["pairs_cohort"] += 1
        for a in ids:
            if a not in C.id2i:
                continue
            for b in ids:
                if b == a or b not in C.id2i:
                    continue
                partners[a][g].add(b)
                # subset G: b arrived by the walk from some r != a, and a/b are not themselves parent/child
                if b in walked and any(r != a for r, _ in walked[b]) and not linked(a, b):
                    partners[a]["G"].add(b)
                    cs["G_pairs_cohort"] += 1
                    # DEVIATION (declared after the smoke run, before the full run): split G by the link type
                    # that reached b -- distilled_from = lattice descend (no similarity in the pick),
                    # relates_to = study/essay walk over edges admitted at 0.55-0.85 cosine (indirectly embedding).
                    for lt in sorted({t for r, t in walked[b] if r != a}):
                        partners[a]["G_" + lt].add(b)
                        cs["G_pairs_cohort_" + lt] += 1
    return census, partners, rows_ts, all_ids


# ------------------------------------------------------------------------------ metrics
def clk_vec(C, qi, idx):
    d = np.abs(C.ts[idx] - C.ts[qi]) / 86400.0
    return np.minimum(1.0, np.log10(d + 1.0) / math.log10(CLK_CAP_DAYS + 1.0))


def unit_metrics_v2(v1, C, u, wc, rng, reps, dims):
    qi, idx = u["q"], u["items"]
    F = v1.six_features(C, qi, idx, C.ts[qi])
    w = v1.w_state(C.num["valence"][qi])
    D6 = v1.d6_terms(F, w).sum(axis=1)
    clk = clk_vec(C, qi, idx)
    Dc = D6 + wc * clk ** 2
    pl, nl = u["pos_loc"], u["neg_loc"]
    wr = v1.win_rate
    W6, W6c, Wclk = wr(np.sqrt(D6), pl, nl), wr(np.sqrt(Dc), pl, nl), wr(clk, pl, nl)
    out = {"W_sem": wr(1.0 - F[:, 0], pl, nl), "W6": W6, "W6c": W6c, "Wclk": Wclk, "npos": len(pl), "dims": {}}

    def stats(m, perts_m):
        ci = wc * (1 - m) ** 2
        W6ci = wr(np.sqrt(Dc + ci), pl, nl)
        Wp = []
        for pv, mp in perts_m:
            Dp = Dc
            if c == "valence":
                wn = v1.w_state(pv)
                Dp = Dc + (wn[2] - w[2]) * (v1.NEED_PT[2] - F[:, 2]) ** 2
            Wp.append(wr(np.sqrt(Dp + wc * (1 - mp) ** 2), pl, nl))
        return {"Wi": wr(1.0 - m, pl, nl),
                "lift": W6ci - W6c,
                "lift_raw": wr(np.sqrt(D6 + ci), pl, nl) - W6,
                "lift_clk": wr(np.sqrt(wc * clk ** 2 + ci), pl, nl) - Wclk,
                "harm": W6ci - float(np.mean(Wp))}

    for c in dims:
        m0 = v1.match_vec(C, c, idx, v1.query_value(C, qi, c))
        perts = v1.perturbations(C, qi, c)
        pm = [(pv, v1.match_vec(C, c, idx, pv)) for pv in perts]
        rec = stats(m0, pm)
        nulls = collections.defaultdict(list)
        for _ in range(reps):
            perm = rng.permutation(len(idx))
            s = stats(m0[perm], [(pv, mp[perm]) for pv, mp in pm])
            for k, v in s.items():
                nulls[k].append(v)
        for k, v in nulls.items():
            rec["null_" + k] = v
        out["dims"][c] = rec
    return out


KEYS = ("Wi", "lift", "lift_raw", "lift_clk", "harm")


def agg(mets, dims):
    res = {"n_units": len(mets), "dims": {}}
    if not mets:
        return res
    n = len(mets)
    bs_rng = np.random.default_rng(7)
    for k in ("W_sem", "W6", "W6c", "Wclk"):
        v = np.array([m[k] for m in mets])
        res[k] = float(v.mean())
        bs = [float(v[bs_rng.integers(0, n, n)].mean()) for _ in range(500)]
        res[k + "_ci"] = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
    for c in dims:
        d = {}
        for key in KEYS:
            v = np.array([m["dims"][c][key] for m in mets])
            d[key] = float(v.mean())
            bs = [float(v[bs_rng.integers(0, n, n)].mean()) for _ in range(500)]
            d[key + "_ci"] = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
            nm = np.array([m["dims"][c]["null_" + key] for m in mets])
            if nm.ndim == 2 and nm.shape[1] > 1:
                nrep = nm.mean(axis=0)
                mu, sd = float(nrep.mean()), float(nrep.std(ddof=1))
                d[key + "_null_mean"], d[key + "_null_sd"] = mu, sd
                d[key + "_z"] = (d[key] - mu) / sd if sd > 0 else None
        diff = np.array([m["dims"][c]["Wi"] - m["W_sem"] for m in mets])
        bs = [float(diff[bs_rng.integers(0, n, n)].mean()) for _ in range(500)]
        d["Wi_minus_Wsem"] = float(diff.mean())
        d["Wi_minus_Wsem_ci"] = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
        lz, hz = d.get("lift_z"), d.get("harm_z")
        d["bar"] = ("pass" if (d["lift"] > 0 and d["harm"] > 0 and lz is not None and hz is not None and lz >= 3 and hz >= 3)
                    else "fail")
        res["dims"][c] = d
    return res


def build_units(v1, C, grp, rng, nm, cond):
    okq = v1.query_ok(C)
    cands = [i for i in range(C.n) if okq[i] and C.partners.get(C.ids[i], {}).get(grp)]
    if not cands:
        return [], 0
    pick = rng.choice(cands, size=min(nm, len(cands)), replace=False)
    units = []
    for qi in pick:
        u = v1.build_unit(C, int(qi), grp, rng, cond, False)
        if u is not None:
            units.append(u)
    return units, len(cands)


def run_m(v1, C, grp, rng, nm, reps, cond, log):
    dims = [c for c in v1.COORDS if not (cond == "place" and c == "place") and not (cond == "tod" and c == "tod")]
    units, ncand = build_units(v1, C, grp, rng, nm, cond)
    log(f"  [M2 grp={grp} cond={cond}] candidates={ncand} units={len(units)}")
    if len(units) < MIN_UNITS:
        return {"n_units": len(units), "n_candidates": ncand, "skipped": f"< {MIN_UNITS} units"}
    mets = [unit_metrics_v2(v1, C, u, WC, rng, reps, dims) for u in units]
    r = agg(mets, dims)
    r["n_candidates"], r["cond"] = ncand, cond
    return r


def wsem_census(v1, C, rng, nm, log):
    out = {}
    for grp in GROUPS + GSUB:
        units, ncand = build_units(v1, C, grp, rng, nm, None)
        if not units:
            out[grp] = {"n_candidates": ncand, "n_units": 0}
            continue
        mets = [unit_metrics_v2(v1, C, u, WC, rng, 0, []) for u in units]
        r = agg(mets, [])
        r["n_candidates"] = ncand
        out[grp] = r
        log(f"  [census {grp}] cand={ncand} units={len(units)} Wsem={r['W_sem']:.3f} Wclk={r['Wclk']:.3f}")
    return out


# ------------------------------------------------------------------------------ felt_recall join
def felt_join(C, rows_ts, all_ids, rng):
    from core.memory.store import _blob_to_vec
    n = fired = with_id = 0
    courier = []
    for line in open(FELT, encoding="utf-8"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        n += 1
        fired += int(bool(r.get("fired")))
        fid = r.get("courier_fragment_id")
        if fid:
            with_id += 1
            courier.append((float(r.get("ts") or 0), fid))
    res = {"rows": n, "fired": fired, "with_courier_id": with_id, "distinct_courier_ids": len({f for _, f in courier})}
    if not courier:
        return res
    con = sqlite3.connect(DB_URI, uri=True)
    vec_cache = {}

    def vec(fid):
        if fid in C.id2i:
            return C.E[C.id2i[fid]]
        if fid not in vec_cache:
            row = con.execute("SELECT embedding FROM memory_fragments WHERE fragment_id=?", (fid,)).fetchone()
            vec_cache[fid] = _blob_to_vec(row[0]) if row and row[0] else None
        return vec_cache[fid]
    ts_arr = np.array([t for t, _, _ in rows_ts])
    order = np.argsort(ts_arr)
    ts_sorted = ts_arr[order]
    ever = sum(1 for _, f in courier if f in all_ids)
    near_cos, rand_cos, n_near = [], [], 0
    for t, fid in courier:
        v = vec(fid)
        if v is None:
            continue
        a, b = np.searchsorted(ts_sorted, t - 600), np.searchsorted(ts_sorted, t + 600)
        near = [x for k in order[a:b] for x in rows_ts[k][2] if x != fid]
        cs = [float(np.dot(v, w)) for w in (vec(x) for x in near[:40]) if w is not None]
        if cs:
            n_near += 1
            near_cos.append(float(np.mean(cs)))
            ri = rng.choice(C.n, size=20, replace=False)
            rand_cos.append(float(np.mean(C.E[ri] @ v)))
    con.close()
    res.update({"courier_ever_co_recalled": ever, "courier_with_window_partners": n_near})
    if near_cos:
        dlt = np.array(near_cos) - np.array(rand_cos)
        res.update({"mean_cos_to_window_ids": float(np.mean(near_cos)), "mean_cos_to_random": float(np.mean(rand_cos)),
                    "mean_diff": float(dlt.mean()), "share_window_closer": float(np.mean(dlt > 0))})
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--nm", type=int, default=250)
    ap.add_argument("--reps", type=int, default=20)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--seed", type=int, default=20261031)
    a = ap.parse_args()
    import lab_geometric_perturbation_sweep as v1
    v1.BIN_W = 0.02
    log = lambda s: print(s, flush=True)
    rng = np.random.default_rng(a.seed)
    canary_before = {str(p): (os.path.getsize(p), os.path.getmtime(p)) for p in CANARY}
    t0 = time.time()
    C = v1.load_cohort()
    census, partners, rows_ts, all_ids = read_ledger(C, v1)
    C.partners = partners
    log(f"cohort n={C.n}; ledger read {time.time()-t0:.0f}s")
    nm = 30 if a.smoke else a.nm
    reps = 3 if a.smoke else a.reps
    out = {"seed": a.seed, "cohort_n": C.n, "bin_w": v1.BIN_W, "wc": WC, "clk_cap_days": CLK_CAP_DAYS,
           "census": {g: dict(c) for g, c in census.items()},
           "partner_queries": {g: sum(1 for x in partners.values() if x.get(g)) for g in GROUPS + GSUB}}
    out["wsem_census"] = wsem_census(v1, C, rng, nm, log)
    targets = ["G", "G_distilled_from", "G_relates_to"] + [g for g, r in out["wsem_census"].items()
                       if g in GROUPS and r.get("n_units", 0) >= MIN_UNITS and r.get("W_sem", 1.0) <= 0.75]
    out["targets"] = targets
    out["M2"] = {}
    for g in targets:
        out["M2"][g] = {cond or "uncond": run_m(v1, C, g, rng, nm, reps, cond, log) for cond in (None, "place", "tod")}
    out["felt_join"] = felt_join(C, rows_ts, all_ids, rng)
    out["canary"] = {p: {"before": list(v), "after": [os.path.getsize(p), os.path.getmtime(p)]}
                     for p, v in canary_before.items()}
    out["runtime_s"] = time.time() - t0
    Path(a.out).write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    log(f"WROTE {a.out} total {time.time()-t0:.0f}s")


if __name__ == "__main__":
    import core                                            # import core BEFORE lab_env (job-run live-store rule)
    assert str(Path(core.__file__).resolve()).lower().startswith(str(WT).lower()), core.__file__
    lab_root = None
    for i, x in enumerate(sys.argv):
        if x == "--lab-root":
            lab_root = Path(sys.argv[i + 1]); del sys.argv[i:i + 2]; break
    assert lab_root is not None, "--lab-root <dir under your scratchpad> is required (S-0315)"
    sys.path.insert(0, r"C:\Users\USER\.claude\skills\job-queue")
    import lab_env
    lab_env._LAB_ROOT = lab_root
    lab_env._ISOLATE_OUTCOMES_LOG = lab_root / "_isolate_outcomes.jsonl"
    with lab_env.isolate(db="empty") as _lab:
        assert str(Path(_lab).resolve()).lower().startswith(str(lab_root.resolve()).lower()), _lab
        main()
