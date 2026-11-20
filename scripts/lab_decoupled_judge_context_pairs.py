"""
J-2639 -- decoupled-judge pass on 30 context-divergent memory pairs (J-2535 optional step 3).

Pre-registration sheet: docs/lab/decoupled_judge_context_pairs_2026-10-31.md (committed 72e6b320 before this ran).
Reads: data/memory/nascence.db (?mode=ro) only. Writes ONLY --out and --cache (scratch). Judge calls go to the
decoupled panel hubs via core.judge_panel.rule_detail (log redirected into the lab dir).

Usage: python scripts/lab_decoupled_judge_context_pairs.py --out <json> --cache <jsonl> --lab-root <dir> [--stage pairs|all]
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
SEED = 20261031 + 2639
TXT_MAX = 600

SYS_APPROP = ("You judge whether a remembered passage fits a current piece of text. You are given CURRENT TEXT and a "
              "MEMORY PASSAGE. Decide whether surfacing the memory passage while a mind is thinking the current text would "
              "be a sensible, relevant association: same topic, theme, question, or a clear connection a thoughtful person "
              "would draw. Answer false if it is unrelated, off-topic, or only superficially similar. "
              'Reply with JSON only: {"appropriate": true or false, "why": "one short sentence"}')
SYS_PAIR = ("You judge which of two remembered passages is the more appropriate one to surface while a mind is thinking a "
            "given piece of text. You are given CURRENT TEXT, MEMORY FIRST and MEMORY SECOND. Prefer the passage that is the "
            "more relevant and sensible association for the current text. "
            'Reply with JSON only: {"first_better": true or false, "why": "one short sentence"}')


def build_pairs(v1, C, con, log):
    rng = np.random.default_rng(SEED)
    d = json.load(open(S_RESULTS, encoding="utf-8"))
    qids = [q for q in d["S_queries"] if q in C.id2i]
    pc = C.code["place"]
    places = [v for v in C.cat_vals["place"] if v != ""]
    texts = {}

    def txt(i):
        if i not in texts:
            r = con.execute("SELECT content FROM memory_fragments WHERE fragment_id=?", (C.ids[i],)).fetchone()
            texts[i] = (r[0] or "").strip() if r else ""
        return texts[i]

    cand_by_place = {p: [] for p in places}
    for q in qids:
        qi = C.id2i[q]
        pl = C.cat_vals["place"][pc[qi]]
        if pl not in cand_by_place or qi < 800:
            continue
        cand_by_place[pl].append(qi)
    quota = {p: n for p, n in zip(places, [8, 8, 7, 7])}
    pairs = []
    for p in places:
        order = list(rng.permutation(len(cand_by_place[p])))
        got = 0
        for k in order:
            if got >= quota[p]:
                break
            qi = cand_by_place[p][k]
            if len(txt(qi)) < 40:
                continue
            pool = np.arange(0, qi)[-600:]
            now = C.ts[qi]
            F = v1.six_features(C, qi, pool, now)
            w = v1.w_state(C.num["valence"][qi])
            D6 = v1.d6_terms(F, w)
            base6 = D6.sum(axis=1)
            mb = {c: v1.match_vec(C, c, pool, v1.query_value(C, qi, c)) for c in v1.COORDS}
            cb = {c: v1.WC * (1.0 - mb[c]) ** 2 for c in v1.COORDS}
            cb_sum = sum(cb.values())
            tot0 = base6 + cb_sum
            o0, pos0 = v1.rank_positions(tot0)
            top0 = o0[: v1.TOPK]
            s0 = set(top0.tolist())
            best = None
            for pv in v1.perturbations(C, qi, "place"):
                mp = v1.match_vec(C, "place", pool, pv)
                tot = base6 + cb_sum - cb["place"] + v1.WC * (1.0 - mp) ** 2
                o1, pos1 = v1.rank_positions(tot)
                top1 = o1[: v1.TOPK]
                s1 = set(top1.tolist())
                jac = len(s0 & s1) / len(s0 | s1)
                shift = float(np.mean(np.abs(pos1[top0] - pos0[top0])))
                new = [j for j in top1.tolist() if j not in s0]       # in perturbed rank order
                if not new:
                    continue
                key = (jac, -shift)
                if best is None or key < best[0]:
                    best = (key, pv, jac, shift, new, top1.tolist())
            if best is None:
                continue
            _, pv, jac, shift, new, top1l = best
            bi, pi = int(pool[o0[0]]), int(pool[new[0]])
            tb, tp = txt(bi), txt(pi)
            if len(tb) < 30 or len(tp) < 30 or tb == tp:
                continue
            cos = float(C.E[bi] @ C.E[pi])
            top1set = set(int(pool[x]) for x in top1l)
            pairs.append({
                "query_id": C.ids[qi], "query_place": p, "query_text": txt(qi)[:TXT_MAX],
                "perturbed_place": C.cat_vals["place"][pv], "jac_top8": jac, "mean_rank_shift": shift,
                "base_top1": {"id": C.ids[bi], "origin": str(C.origin[bi]), "base_rank": 1, "text": tb[:TXT_MAX]},
                "pert_top1": {"id": C.ids[pi], "origin": str(C.origin[pi]), "pert_rank_in_top8": top1l.index(new[0]) + 1,
                              "base_rank": int(pos0[new[0]]) + 1, "text": tp[:TXT_MAX]},
                "cosine_base_vs_pert": cos,
                "base_top1_in_pert_top8": bool(bi in top1set),
                "_pool_rest": [int(pool[j]) for j in range(len(pool)) if j not in s0 and int(pool[j]) not in top1set],
            })
            got += 1
        log(f"place {p}: {got}/{quota[p]} pairs")
    # controls for 15 of the pairs
    ctrl_idx = set(int(i) for i in rng.choice(len(pairs), size=min(15, len(pairs)), replace=False))
    for k, pr in enumerate(pairs):
        rest = pr.pop("_pool_rest")
        if k in ctrl_idx:
            for _ in range(20):
                ci = int(rng.choice(rest))
                t = txt(ci)
                if len(t) >= 30:
                    pr["control"] = {"id": C.ids[ci], "origin": str(C.origin[ci]), "text": t[:TXT_MAX]}
                    break
    return pairs


async def run_judges(pairs, cache_path, log):
    from core import judge_panel as jp
    cache = {}
    if Path(cache_path).exists():
        for line in open(cache_path, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                cache[r["k"]] = r
    items = []
    rnd = random.Random(SEED)
    for i, pr in enumerate(pairs):
        for arm in ("base", "pert", "control"):
            frag = pr.get({"base": "base_top1", "pert": "pert_top1", "control": "control"}[arm])
            if frag:
                items.append((f"A|{i}|{arm}", "appropriate", SYS_APPROP,
                              f"CURRENT TEXT:\n{pr['query_text']}\n\nMEMORY PASSAGE:\n{frag['text']}"))
        order = rnd.random() < 0.5            # True: base shown first in order 0
        for o in (0, 1):
            first_base = order if o == 0 else (not order)
            a, b = ((pr["base_top1"]["text"], pr["pert_top1"]["text"]) if first_base
                    else (pr["pert_top1"]["text"], pr["base_top1"]["text"]))
            items.append((f"B|{i}|{o}|{int(first_base)}", "first_better", SYS_PAIR,
                          f"CURRENT TEXT:\n{pr['query_text']}\n\nMEMORY FIRST:\n{a}\n\nMEMORY SECOND:\n{b}"))
    rnd.shuffle(items)
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


def boot(vals, rng, n=2000):
    a = np.array(vals, dtype=float)
    m = [rng.choice(a, size=len(a), replace=True).mean() for _ in range(n)]
    return [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]


def stats(pairs, cache):
    rng = np.random.default_rng(SEED + 1)
    S = {}
    ver = lambda k: (cache.get(k) or {}).get("verdict")
    rows = []
    for i, pr in enumerate(pairs):
        b, p, c = ver(f"A|{i}|base"), ver(f"A|{i}|pert"), ver(f"A|{i}|control")
        pref = []
        for o in (0, 1):
            for k, r in cache.items():
                if k.startswith(f"B|{i}|{o}|"):
                    fb = int(k.split("|")[3])
                    v = r.get("verdict")
                    pref.append(None if v is None else ("base" if (v == bool(fb)) else "pert"))
        if len(pref) == 2 and None not in pref:
            ps = 1.0 if pref == ["base", "base"] else (0.0 if pref == ["pert", "pert"] else 0.5)
            consistent = pref[0] == pref[1]
        else:
            ps, consistent = None, None
        rows.append({"i": i, "place": pr["query_place"], "b": b, "p": p, "c": c, "pair_pref": pref,
                     "pair_score": ps, "consistent": consistent})
    S["rows"] = rows
    both = [r for r in rows if r["b"] is not None and r["p"] is not None]
    S["n_pairs"] = len(rows)
    S["n_both_judged"] = len(both)
    sc = [1.0 if (r["b"] and not r["p"]) else (0.0 if (r["p"] and not r["b"]) else 0.5) for r in both]
    S["P"] = float(np.mean(sc)) if sc else None
    S["P_ci"] = boot(sc, rng) if sc else None
    nul = [float(np.mean([s if rng.random() < 0.5 else 1 - s for s in sc])) for _ in range(2000)] if sc else []
    S["P_null"] = ({"mean": float(np.mean(nul)), "sd": float(np.std(nul)),
                    "band95": [float(np.percentile(nul, 2.5)), float(np.percentile(nul, 97.5))]} if nul else None)
    S["counts"] = {"base_only": sum(1 for r in both if r["b"] and not r["p"]),
                   "pert_only": sum(1 for r in both if r["p"] and not r["b"]),
                   "both_yes": sum(1 for r in both if r["b"] and r["p"]),
                   "both_no": sum(1 for r in both if not r["b"] and not r["p"])}
    S["rate_base"] = float(np.mean([bool(r["b"]) for r in both])) if both else None
    S["rate_pert"] = float(np.mean([bool(r["p"]) for r in both])) if both else None
    ctrl = [r["c"] for r in rows if r["c"] is not None]
    S["n_control"] = len(ctrl)
    S["rate_control"] = float(np.mean([bool(x) for x in ctrl])) if ctrl else None
    pcs = [r for r in both if r["c"] is not None]
    if pcs:
        diff = [float(bool(r["p"])) - float(bool(r["c"])) for r in pcs]
        S["pert_minus_control_on_ctrl_pairs"] = {"mean": float(np.mean(diff)), "ci": boot(diff, rng), "n": len(diff)}
        S["pert_rate_on_ctrl_pairs"] = float(np.mean([bool(r["p"]) for r in pcs]))
        S["base_rate_on_ctrl_pairs"] = float(np.mean([bool(r["b"]) for r in pcs]))
    fc = [r["pair_score"] for r in rows if r["pair_score"] is not None]
    S["P_pair"] = float(np.mean(fc)) if fc else None
    S["P_pair_ci"] = boot(fc, rng) if fc else None
    S["P_pair_n"] = len(fc)
    S["pair_order_consistent"] = sum(1 for r in rows if r["consistent"])
    nulp = [float(np.mean([s if rng.random() < 0.5 else 1 - s for s in fc])) for _ in range(2000)] if fc else []
    S["P_pair_null_band95"] = [float(np.percentile(nulp, 2.5)), float(np.percentile(nulp, 97.5))] if nulp else None
    by = {}
    for r in both:
        s = 1.0 if (r["b"] and not r["p"]) else (0.0 if (r["p"] and not r["b"]) else 0.5)
        by.setdefault(r["place"], []).append((s, bool(r["b"]), bool(r["p"])))
    S["by_place"] = {p: {"n": len(v), "P": float(np.mean([x[0] for x in v])),
                         "rate_base": float(np.mean([x[1] for x in v])),
                         "rate_pert": float(np.mean([x[2] for x in v]))} for p, v in by.items()}
    A = [r for k, r in cache.items() if k.startswith("A|")]
    both_fam = [r for r in A if r["v1"] is not None and r["v2"] is not None]
    S["agreement"] = {"n_A_items": len(A), "n_both_families_answered": len(both_fam),
                      "v1_eq_v2": float(np.mean([r["v1"] == r["v2"] for r in both_fam])) if both_fam else None,
                      "tiebreak_fired": sum(1 for r in A if r["how"] == "tiebreak"),
                      "split_no_tiebreak": sum(1 for r in A if r["how"] == "split_no_tiebreak"),
                      "unavailable": sum(1 for r in A if r["how"] == "unavailable"),
                      "yes_rate_v1": float(np.mean([bool(r["v1"]) for r in both_fam])) if both_fam else None,
                      "yes_rate_v2": float(np.mean([bool(r["v2"]) for r in both_fam])) if both_fam else None}
    if both_fam:
        a = np.array([bool(r["v1"]) for r in both_fam])
        b = np.array([bool(r["v2"]) for r in both_fam])
        po = float((a == b).mean())
        pe = float(a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean()))
        S["agreement"]["cohen_kappa"] = (po - pe) / (1 - pe) if pe < 1 else None
    Bi = [r for k, r in cache.items() if k.startswith("B|")]
    bf = [r for r in Bi if r["v1"] is not None and r["v2"] is not None]
    S["agreement_pairwise"] = {"n_B_items": len(Bi),
                               "v1_eq_v2": float(np.mean([r["v1"] == r["v2"] for r in bf])) if bf else None,
                               "tiebreak_fired": sum(1 for r in Bi if r["how"] == "tiebreak"),
                               "unavailable_or_split": sum(1 for r in Bi if r["how"] in ("unavailable", "split_no_tiebreak"))}
    cos = [pr["cosine_base_vs_pert"] for pr in pairs]
    S["difference"] = {"median_cosine": float(np.median(cos)), "share_cos_lt_0.8": float(np.mean([c < 0.8 for c in cos])),
                       "base_top1_stays_in_pert_top8": sum(1 for pr in pairs if pr["base_top1_in_pert_top8"])}
    g1 = (S["rate_control"] is not None and S["rate_control"] < 0.5 and S["n_both_judged"] >= 24)
    S["G1_instrument_valid"] = bool(g1)
    if not g1:
        S["verdict"] = "INSTRUMENT INVALID"
    else:
        lo, hi = S["P_ci"]
        if lo > 0.5 and lo > S["P_null"]["band95"][1]:
            S["verdict"] = "perturbed set judged LESS appropriate"
        elif hi < 0.5:
            S["verdict"] = "perturbed set judged MORE appropriate"
        else:
            pm = S.get("pert_minus_control_on_ctrl_pairs")
            ok = bool(S["rate_pert"] >= 0.5 and pm and pm["ci"][0] > 0 and (S["rate_base"] - S["rate_pert"]) <= 0.15)
            S["verdict"] = ("not distinguishable; different AND also appropriate" if ok
                            else "not distinguishable; inconclusive")
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
    lab = Path(os.environ["J2639_LAB_DIR"])
    jp._LOG = lab / "judge_panel_log.jsonl"
    jp._DATA = lab
    canary = {str(LIVE_DB): (os.path.getsize(LIVE_DB), os.path.getmtime(LIVE_DB))}
    t0 = time.time()
    C = v1.load_cohort()
    log(f"cohort n={C.n} load {time.time()-t0:.0f}s")
    con = sqlite3.connect(v1.DB_URI, uri=True)
    pairs = build_pairs(v1, C, con, log)
    con.close()
    out = {"seed": SEED, "n_pairs": len(pairs), "pairs": pairs, "cohort_n": C.n}
    Path(a.out).write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    log(f"pairs built: {len(pairs)}")
    if a.stage == "pairs":
        return
    cache = asyncio.run(run_judges(pairs, a.cache, log))
    out["verdicts"] = cache
    out["stats"] = stats(pairs, cache)
    out["canary"] = {p: {"before": list(v), "after": [os.path.getsize(p), os.path.getmtime(p)]}
                     for p, v in canary.items()}
    out["runtime_s"] = time.time() - t0
    Path(a.out).write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    log(f"WROTE {a.out} verdict={out['stats']['verdict']}")


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
        os.environ["J2639_LAB_DIR"] = str(_lab)
        main()
