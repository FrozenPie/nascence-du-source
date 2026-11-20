"""
J-2657 -- rank-matched control for the J-2639 decoupled-judge pilot (+ fire and weather arms).

Pre-registration sheet: docs/lab/rank_matched_control_2026-10-31.md (committed 574a0eeb before any judge call).
Reads: data/memory/nascence.db (?mode=ro) only. Writes ONLY --out and --cache (scratch). Judge calls go to the
decoupled panel hubs via core.judge_panel.rule_detail (log redirected into the lab dir).

Usage: python scripts/lab_rank_matched_control.py --out <json> --cache <jsonl> --lab-root <dir> [--stage items|all]
"""
from __future__ import annotations
import argparse, asyncio, json, os, random, sqlite3, sys, time
from pathlib import Path
import numpy as np

WT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WT))
sys.path.insert(0, str(WT / "scripts"))
LIVE_DB = Path(r"C:\Nascence\data\memory\nascence.db")
S_RESULTS = WT / "docs" / "lab" / "geometric_perturbation_sweep_2026-10-31_results.json"
J39 = WT / "docs" / "lab" / "decoupled_judge_context_pairs_2026-10-31_results.json"
SEED = 20261031 + 2657
TXT_MAX = 600
N_CTRL = 2
ARMS = {"place": None, "fire": 15, "weather": 15}      # place = the exact J-2639 queries


def construct(v1, C, con, txt, qi, dim):
    """Same per-query construction as J-2639 build_pairs for one perturbed dimension, plus rank-matched controls."""
    pool = np.arange(0, qi)[-600:]
    now = C.ts[qi]
    F = v1.six_features(C, qi, pool, now)
    w = v1.w_state(C.num["valence"][qi])
    base6 = v1.d6_terms(F, w).sum(axis=1)
    mb = {c: v1.match_vec(C, c, pool, v1.query_value(C, qi, c)) for c in v1.COORDS}
    cb = {c: v1.WC * (1.0 - mb[c]) ** 2 for c in v1.COORDS}
    cb_sum = sum(cb.values())
    o0, pos0 = v1.rank_positions(base6 + cb_sum)
    top0 = o0[: v1.TOPK]
    s0 = set(top0.tolist())
    best = None
    for pv in v1.perturbations(C, qi, dim):
        mp = v1.match_vec(C, dim, pool, pv)
        tot = base6 + cb_sum - cb[dim] + v1.WC * (1.0 - mp) ** 2
        o1, pos1 = v1.rank_positions(tot)
        top1 = o1[: v1.TOPK]
        s1 = set(top1.tolist())
        jac = len(s0 & s1) / len(s0 | s1)
        shift = float(np.mean(np.abs(pos1[top0] - pos0[top0])))
        new = [j for j in top1.tolist() if j not in s0]
        if not new:
            continue
        key = (jac, -shift)
        if best is None or key < best[0]:
            best = (key, pv, jac, shift, new, top1.tolist(), s1)
    if best is None:
        return None
    _, pv, jac, shift, new, top1l, s1 = best
    bi, pi = int(pool[o0[0]]), int(pool[new[0]])
    tb, tp = txt(bi), txt(pi)
    if len(tb) < 30 or len(tp) < 30 or tb == tp:
        return None
    k = int(pos0[new[0]]) + 1                                   # pert item's rank under the BASE ranker (>= 9)
    excl = s0 | s1 | {new[0]}
    cand_ranks = sorted((r for r in range(1, len(pool) + 1)), key=lambda r: (abs(r - k), r))
    ctrls = []
    for r in cand_ranks:
        loc = int(o0[r - 1])
        if loc in excl:
            continue
        gi = int(pool[loc])
        t = txt(gi)
        if len(t) < 30 or t == tp:
            continue
        ctrls.append({"id": C.ids[gi], "origin": str(C.origin[gi]), "base_rank": r, "text": t[:TXT_MAX]})
        if len(ctrls) >= N_CTRL:
            break
    return {"dim": dim, "perturbed_value": C.cat_vals[dim][pv], "query_value": C.cat_vals[dim][C.code[dim][qi]],
            "jac_top8": jac, "mean_rank_shift": shift, "k": k,
            "base_top1": {"id": C.ids[bi], "origin": str(C.origin[bi]), "base_rank": 1, "text": tb[:TXT_MAX]},
            "pert_top1": {"id": C.ids[pi], "origin": str(C.origin[pi]), "base_rank": k, "text": tp[:TXT_MAX]},
            "controls": ctrls}


def build_items(v1, C, con, log):
    d = json.load(open(S_RESULTS, encoding="utf-8"))
    qids = [q for q in d["S_queries"] if q in C.id2i]
    texts = {}

    def txt(i):
        if i not in texts:
            r = con.execute("SELECT content FROM memory_fragments WHERE fragment_id=?", (C.ids[i],)).fetchone()
            texts[i] = (r[0] or "").strip() if r else ""
        return texts[i]

    arms = {}
    # place: the exact J-2639 queries, order preserved
    j39 = json.load(open(J39, encoding="utf-8"))
    arms["place"] = []
    mism = 0
    for i, pr in enumerate(j39["pairs"]):
        qi = C.id2i[pr["query_id"]]
        it = construct(v1, C, con, txt, qi, "place")
        if it is None:
            log(f"place {i}: construction failed")
            continue
        it["query_id"], it["query_text"], it["j39_index"] = pr["query_id"], txt(qi)[:TXT_MAX], i
        it["reproduces_j39_pert_id"] = (it["pert_top1"]["id"] == pr["pert_top1"]["id"])
        it["reproduces_j39_base_id"] = (it["base_top1"]["id"] == pr["base_top1"]["id"])
        mism += (not it["reproduces_j39_pert_id"])
        arms["place"].append(it)
    log(f"place arm: {len(arms['place'])} items, pert-id mismatches vs J-2639: {mism}")
    for off, dim in enumerate(("fire", "weather")):
        rng = np.random.default_rng(SEED + off + 1)
        cand = [C.id2i[q] for q in qids if C.id2i[q] >= 800 and C.code[dim][C.id2i[q]] >= 0 and len(txt(C.id2i[q])) >= 40]
        order = list(rng.permutation(len(cand)))
        arms[dim] = []
        for kx in order:
            if len(arms[dim]) >= ARMS[dim]:
                break
            qi = cand[kx]
            it = construct(v1, C, con, txt, qi, dim)
            if it is None or not it["controls"]:
                continue
            it["query_id"], it["query_text"] = C.ids[qi], txt(qi)[:TXT_MAX]
            arms[dim].append(it)
        log(f"{dim} arm: {len(arms[dim])}/{ARMS[dim]} items from {len(cand)} eligible queries")
    return arms


async def run_judges(arms, cache_path, log):
    from core import judge_panel as jp
    import lab_decoupled_judge_context_pairs as j9
    cache = {}
    if Path(cache_path).exists():
        for line in open(cache_path, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                cache[r["k"]] = r
    items = []
    for arm, lst in arms.items():
        for i, it in enumerate(lst):
            roles = [("pert", it["pert_top1"]["text"])]
            if arm != "place":
                roles.append(("base", it["base_top1"]["text"]))
            roles += [(f"c{j+1}", c["text"]) for j, c in enumerate(it["controls"])]
            for role, text in roles:
                items.append((f"R|{arm}|{i}|{role}", "appropriate", j9.SYS_APPROP,
                              f"CURRENT TEXT:\n{it['query_text']}\n\nMEMORY PASSAGE:\n{text}"))
    random.Random(SEED).shuffle(items)
    log(f"{len(items)} panel items to rule ({sum(1 for k, *_ in items if k in cache and cache[k].get('verdict') is not None)} cached)")
    t0 = time.time()
    with open(cache_path, "a", encoding="utf-8") as fh:
        for n, (k, key, sysm, user) in enumerate(items):
            if k in cache and cache[k].get("verdict") is not None:
                continue
            res = None
            for attempt in range(2):
                res = await jp.rule_detail(sysm, user, key, context=k)
                if res["how"] in ("agreed", "tiebreak"):
                    break
            rec = {"k": k, **{x: res[x] for x in ("v1", "v2", "verdict", "how", "why1", "why2", "why3",
                                                  "err1", "err2", "err3", "hub1", "hub2", "hub3")}}
            cache[k] = rec
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            if (n + 1) % 10 == 0:
                log(f"  judged {n+1}/{len(items)} {time.time()-t0:.0f}s last how={res['how']}")
    return cache


def boot_mean(vals, rng, n=2000):
    a = np.array(vals, dtype=float)
    m = [rng.choice(a, size=len(a), replace=True).mean() for _ in range(n)]
    return [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]


def arm_stats(arm, lst, cache, j39v, rng):
    ver = lambda k: (cache.get(k) or {}).get("verdict")
    rows = []
    for i, it in enumerate(lst):
        p = ver(f"R|{arm}|{i}|pert")
        cs = [ver(f"R|{arm}|{i}|c{j+1}") for j in range(len(it["controls"]))]
        rated = [(c, it["controls"][j]["base_rank"]) for j, c in enumerate(cs) if c is not None]
        row = {"i": i, "query_id": it["query_id"], "k": it["k"], "p": p,
               "c": [c for c, _ in rated], "c_ranks": [r for _, r in rated],
               "c_mean": (float(np.mean([bool(c) for c, _ in rated])) if rated else None),
               "b": ver(f"R|{arm}|{i}|base") if arm != "place" else (j39v.get(f"A|{it['j39_index']}|base") or {}).get("verdict"),
               "p_j39": (j39v.get(f"A|{it['j39_index']}|pert") or {}).get("verdict") if arm == "place" else None}
        rows.append(row)
    S = {"n_items": len(lst), "rows": rows}
    use = [r for r in rows if r["p"] is not None and r["c_mean"] is not None]
    S["n_used"] = len(use)
    S["share_with_rated_control"] = float(np.mean([r["c_mean"] is not None for r in rows])) if rows else 0.0
    dr = [abs(rk - r["k"]) for r in rows for rk in r["c_ranks"]]
    S["median_abs_rank_gap"] = float(np.median(dr)) if dr else None
    S["median_k"] = float(np.median([r["k"] for r in rows])) if rows else None
    S["GM_pass"] = bool(S["share_with_rated_control"] >= 0.8 and dr and S["median_abs_rank_gap"] <= 2)
    D = [float(bool(r["p"])) - r["c_mean"] for r in use]
    S["rate_pert"] = float(np.mean([bool(r["p"]) for r in use])) if use else None
    S["rate_ctrl_rankmatched"] = float(np.mean([r["c_mean"] for r in use])) if use else None
    bs = [bool(r["b"]) for r in use if r["b"] is not None]
    S["rate_base_top1"] = float(np.mean(bs)) if bs else None
    S["n_base_rated"] = len(bs)
    if D:
        m = float(np.mean(D))
        ci = boot_mean(D, rng)
        a = np.array(D)
        nul = np.array([float((a * np.where(rng.random(len(a)) < 0.5, -1.0, 1.0)).mean()) for _ in range(5000)])
        pval = float(np.mean(np.abs(nul) >= abs(m) - 1e-12))
        S.update({"mean_D": m, "D_ci": ci, "D_p_labelswap": pval,
                  "D_null_band95": [float(np.percentile(nul, 2.5)), float(np.percentile(nul, 97.5))]})
        lo, hi = ci
        if not S["GM_pass"]:
            S["verdict"] = "MATCH FAILED"
        elif lo > 0 and pval < 0.05:
            S["verdict"] = "BEYOND DEPTH"
        elif hi < 0 and pval < 0.05:
            S["verdict"] = "BELOW DEPTH"
        elif lo >= -0.25 and hi <= 0.25 and abs(m) <= 0.10:
            S["verdict"] = "DEPTH ONLY"
        else:
            S["verdict"] = "INCONCLUSIVE"
        if arm != "place":
            S["verdict"] += " (n=15, underpowered)"
        # discordance counts p vs rounded control
        S["pert_yes_ctrl_all_no"] = sum(1 for r in use if r["p"] and r["c_mean"] == 0.0)
        S["pert_no_ctrl_all_yes"] = sum(1 for r in use if (not r["p"]) and r["c_mean"] == 1.0)
        if S["rate_base_top1"] is not None and S["n_base_rated"] == len(use):
            S["depth_cost_base_minus_R"] = S["rate_base_top1"] - S["rate_ctrl_rankmatched"]
            S["placement_effect_pert_minus_R"] = S["rate_pert"] - S["rate_ctrl_rankmatched"]
            gap = S["rate_base_top1"] - S["rate_pert"]
            S["j39_style_gap_base_minus_pert"] = gap
            S["share_of_gap_explained_by_depth"] = (S["depth_cost_base_minus_R"] / gap) if gap >= 0.05 else None
            sc = [1.0 if (r["b"] and not r["p"]) else (0.0 if (r["p"] and not r["b"]) else 0.5) for r in use]
            S["P_base_win_descriptive"] = float(np.mean(sc))
            S["P_base_win_ci"] = boot_mean(sc, rng)
    if arm == "place":
        both = [r for r in rows if r["p"] is not None and r["p_j39"] is not None]
        S["retest_agreement_pert_vs_j39"] = float(np.mean([bool(r["p"]) == bool(r["p_j39"]) for r in both])) if both else None
        S["retest_n"] = len(both)
        sens = [float(bool(r["p_j39"])) - r["c_mean"] for r in rows if r["p_j39"] is not None and r["c_mean"] is not None]
        if sens:
            S["sensitivity_meanD_with_j39_pert_verdicts"] = {"mean": float(np.mean(sens)), "ci": boot_mean(sens, rng), "n": len(sens)}
    return S


def stats(arms, cache):
    j39v = json.load(open(J39, encoding="utf-8"))["verdicts"]
    S = {"arms": {}}
    for off, (arm, lst) in enumerate(arms.items()):
        S["arms"][arm] = arm_stats(arm, lst, cache, j39v, np.random.default_rng(SEED + 100 + off))
    R = [r for k, r in cache.items() if k.startswith("R|")]
    bf = [r for r in R if r["v1"] is not None and r["v2"] is not None]
    S["agreement"] = {"n_rulings": len(R), "n_both_families": len(bf),
                      "v1_eq_v2": float(np.mean([r["v1"] == r["v2"] for r in bf])) if bf else None,
                      "tiebreak_fired": sum(1 for r in R if r["how"] == "tiebreak"),
                      "split_no_tiebreak": sum(1 for r in R if r["how"] == "split_no_tiebreak"),
                      "unavailable": sum(1 for r in R if r["how"] == "unavailable"),
                      "yes_rate_v1": float(np.mean([bool(r["v1"]) for r in bf])) if bf else None,
                      "yes_rate_v2": float(np.mean([bool(r["v2"]) for r in bf])) if bf else None}
    if bf:
        a = np.array([bool(r["v1"]) for r in bf])
        b = np.array([bool(r["v2"]) for r in bf])
        po = float((a == b).mean())
        pe = float(a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean()))
        S["agreement"]["cohen_kappa"] = (po - pe) / (1 - pe) if pe < 1 else None
    hubs = {}
    for r in R:
        hubs[f"{r.get('hub1')}/{r.get('hub2')}"] = hubs.get(f"{r.get('hub1')}/{r.get('hub2')}", 0) + 1
    S["hubs_used"] = hubs
    return S


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--stage", default="all")
    a = ap.parse_args()
    log = lambda s: print(s, flush=True)
    import lab_geometric_perturbation_sweep as v1
    from core import judge_panel as jp
    lab = Path(os.environ["J2657_LAB_DIR"])
    jp._LOG = lab / "judge_panel_log.jsonl"
    jp._DATA = lab
    canary = {str(LIVE_DB): (os.path.getsize(LIVE_DB), os.path.getmtime(LIVE_DB))}
    t0 = time.time()
    C = v1.load_cohort()
    log(f"cohort n={C.n} load {time.time()-t0:.0f}s")
    con = sqlite3.connect(v1.DB_URI, uri=True)
    arms = build_items(v1, C, con, log)
    con.close()
    out = {"seed": SEED, "cohort_n": C.n, "arms": arms}
    Path(a.out).write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    if a.stage == "items":
        return
    cache = asyncio.run(run_judges(arms, a.cache, log))
    out["verdicts"] = cache
    out["stats"] = stats(arms, cache)
    out["canary"] = {p: {"before": list(v), "after": [os.path.getsize(p), os.path.getmtime(p)]}
                     for p, v in canary.items()}
    out["runtime_s"] = time.time() - t0
    Path(a.out).write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    log("WROTE " + a.out + " verdicts=" + json.dumps({k: v.get("verdict") for k, v in out["stats"]["arms"].items()}))


if __name__ == "__main__":
    import core                                            # import core BEFORE lab_env (job-run live-store rule)
    assert str(Path(core.__file__).resolve()).lower().startswith(str(WT).lower()), core.__file__
    lab_root = None
    for i, x in enumerate(sys.argv):
        if x == "--lab-root":
            lab_root = Path(sys.argv[i + 1])
            del sys.argv[i:i + 2]
            break
    assert lab_root is not None, "--lab-root <dir under your scratchpad> is required (S-0315)"
    sys.path.insert(0, r"C:\Users\USER\.claude\skills\job-queue")
    import lab_env
    lab_env._LAB_ROOT = lab_root
    lab_env._ISOLATE_OUTCOMES_LOG = lab_root / "_isolate_outcomes.jsonl"
    with lab_env.isolate(db="empty") as _lab:
        assert str(Path(_lab).resolve()).lower().startswith(str(lab_root.resolve()).lower()), _lab
        os.environ["J2657_LAB_DIR"] = str(_lab)
        main()
