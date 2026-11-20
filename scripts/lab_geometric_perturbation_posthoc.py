"""
J-2535 -- POST-HOC diagnostics for the geometric perturbation sweep (NOT pre-registered; labelled as such in the report).
Imports scripts/lab_geometric_perturbation_sweep.py.  Read-only; writes only --out.

 (a) Part M re-run at lower context weights (the pre-registered primary wc=0.15 made lift negative for every dim,
     i.e. a noise term costing more than the signal paid; does any dim turn positive when the weight is small?)
 (b) pure-clock diagnostic: win-rate of |ts_item - ts_query| alone in the same matched design (unconditional and
     clock-controlled).  If season/tod standalone Wi ~ this, they are clocks.
 (c) pool homogeneity: how much of the shadow's own 600-fragment recent pool varies on each coordinate.
"""
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, r"C:\jr\wt_cg\scripts")
sys.path.insert(0, r"C:\jr\wt_cg")
import lab_geometric_perturbation_sweep as L


def clock_win(C, units):
    ws = []
    for u in units:
        d = np.abs(C.ts[u["items"]] - C.ts[u["q"]])
        ws.append(L.win_rate(d, u["pos_loc"], u["neg_loc"]))
    return float(np.mean(ws)), len(ws)


def pool_homogeneity(C, queries):
    out = {}
    for c in L.COORDS:
        vals = []
        for qi in queries:
            pool = np.arange(max(0, qi - 600), qi)
            if c in L.CAT:
                v = C.code[c][pool]
                _, cnt = np.unique(v, return_counts=True)
                vals.append(cnt.max() / cnt.sum())                  # modal-value share
            else:
                a = C.num[c][pool]
                a = a[~np.isnan(a)]
                vals.append(float(a.std() / C.sd[c]) if len(a) else np.nan)   # within-pool SD / cohort-wide kernel SD
        out[c] = float(np.nanmean(vals))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--nm", type=int, default=250)
    ap.add_argument("--reps", type=int, default=20)
    a = ap.parse_args()
    rng = np.random.default_rng(20261031 + 1)
    t0 = time.time()
    C = L.load_cohort()
    res = {"cohort_n": C.n}
    # (a) weights
    res["wc_sweep"] = {}
    for wc in (0.01, 0.03, 0.06):
        m = L.part_m(C, rng, a.nm, a.reps, None, False, wc=wc, log=print)
        res["wc_sweep"][str(wc)] = {"n_units": m["n_units"], "W6": m["W6"],
                                    "dims": {c: {k: d[k] for k in ("lift", "lift_z", "harm", "harm_z", "lift_ci")} for c, d in m["dims"].items()}}
        print("wc", wc, "done", round(time.time() - t0))
    # (b) clock diagnostic
    okq = L.query_ok(C)
    out_b = {}
    for clock in (False, True):
        units = []
        for grp in ("monologue", "wandering", "other"):
            cands = [i for i in range(C.n) if okq[i] and grp in C.partners.get(C.ids[i], {})]
            pick = rng.choice(cands, size=min(a.nm, len(cands)), replace=False)
            for qi in pick:
                u = L.build_unit(C, int(qi), grp, rng, None, clock)
                if u is not None:
                    units.append(u)
        w, n = clock_win(C, units)
        # also standalone Wi of tod/season/daylight/place in THESE units, for a like-for-like comparison
        wi = {}
        for c in ("tod", "season", "daylight", "place", "weather"):
            ws = []
            for u in units:
                m0 = L.match_vec(C, c, u["items"], L.query_value(C, u["q"], c))
                ws.append(L.win_rate(1.0 - m0, u["pos_loc"], u["neg_loc"]))
            wi[c] = float(np.mean(ws))
        out_b["clock_controlled" if clock else "age_bin_matched"] = {"n_units": n, "W_abs_dt_alone": w, "Wi_same_units": wi}
    res["clock_diagnostic"] = out_b
    # (c) pool homogeneity on a Part S style query set
    qs, _ = L.pick_part_s_queries(C, rng, 300)
    res["pool_homogeneity"] = pool_homogeneity(C, qs)
    # (d) TIGHT age matching (bin 0.02 instead of 0.15): removes most of the within-bin time gradient, so a pure clock
    #     (|dt| alone) should fall toward 0.5; then what is left of each coordinate is not merely temporal proximity.
    L.BIN_W = 0.02
    m = L.part_m(C, rng, a.nm, a.reps, None, False, log=print)
    units = []
    okq = L.query_ok(C)
    for grp in ("monologue", "wandering", "other"):
        cands = [i for i in range(C.n) if okq[i] and grp in C.partners.get(C.ids[i], {})]
        pick = rng.choice(cands, size=min(a.nm, len(cands)), replace=False)
        for qi in pick:
            u = L.build_unit(C, int(qi), grp, rng, None, False)
            if u is not None:
                units.append(u)
    w, n = clock_win(C, units)
    res["tight_match"] = {"bin_w": 0.02, "n_units": m["n_units"], "W_sem": m["W_sem"], "W6": m["W6"], "W_abs_dt_alone": w, "n_clock_units": n,
                          "dims": {c: {k: d[k] for k in ("Wi", "Wi_null_mean", "Wi_z", "Wi_minus_Wsem", "lift", "lift_z", "harm", "harm_z")} for c, d in m["dims"].items()}}
    res["runtime_s"] = time.time() - t0
    Path(a.out).write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    print("WROTE", a.out, round(time.time() - t0))


if __name__ == "__main__":
    import core
    sys.path.insert(0, r"C:\Users\USER\.claude\skills\job-queue")
    from lab_env import isolate
    with isolate(db="empty"):
        main()
