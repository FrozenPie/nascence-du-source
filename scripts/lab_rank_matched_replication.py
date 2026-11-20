"""
J-2663 -- powered replication of the J-2657 rank-matched control (place and weather arms; fire conditional).

Pre-registration sheet: docs/lab/rank_matched_replication_2026-10-31.md (committed before any judge call).
Reuses scripts/lab_rank_matched_control.py UNCHANGED (construct, arm_stats, boot_mean, verdict rule, N_CTRL=2),
only the query draw (new seed, J-2657 queries excluded, larger n), the per-arm runner and a random control (gate G1)
are new. Reads data/memory/nascence.db (?mode=ro) only. Writes ONLY --out and --cache (scratch).

Usage: python scripts/lab_rank_matched_replication.py --arm place|weather|fire --n 90 --out <json> --cache <jsonl>
       --lab-root <dir> [--stage items|all]
"""
from __future__ import annotations
import argparse, asyncio, hashlib, json, os, random, sqlite3, sys, time
from pathlib import Path
import numpy as np

WT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WT))
sys.path.insert(0, str(WT / "scripts"))
import lab_rank_matched_control as h                 # J-2657 harness, unchanged

SEED2 = 20261031 + 2663
OFF = {"place": 1, "weather": 2, "fire": 3}
N_RANDOM = 30                                        # first 30 drawn queries per arm also get one random-depth control (G1)
J57 = WT / "docs" / "lab" / "rank_matched_control_2026-10-31_results.json"


def used_ids():
    d = json.load(open(J57, encoding="utf-8"))
    return {a: [it["query_id"] for it in lst] for a, lst in d["arms"].items()}, d


def build_items(v1, C, con, arm, n, log):
    d = json.load(open(h.S_RESULTS, encoding="utf-8"))
    qids = [q for q in d["S_queries"] if q in C.id2i]
    texts = {}

    def txt(i):
        if i not in texts:
            r = con.execute("SELECT content FROM memory_fragments WHERE fragment_id=?", (C.ids[i],)).fetchone()
            texts[i] = (r[0] or "").strip() if r else ""
        return texts[i]

    used, _ = used_ids()
    excl = set(q for lst in used.values() for q in lst)
    cand = [C.id2i[q] for q in qids if q not in excl and C.id2i[q] >= 800 and C.code[arm][C.id2i[q]] >= 0
            and len(txt(C.id2i[q])) >= 40]
    log(f"{arm}: {len(qids)} S_queries, {len(excl)} J-2657 ids excluded, {len(cand)} eligible new queries")
    rng = np.random.default_rng(SEED2 + OFF[arm])
    order = list(rng.permutation(len(cand)))
    items, tried = [], 0
    for kx in order:
        if len(items) >= n:
            break
        tried += 1
        qi = cand[kx]
        it = h.construct(v1, C, con, txt, qi, arm)
        if it is None or not it["controls"]:
            continue
        it["query_id"], it["query_text"] = C.ids[qi], txt(qi)[:h.TXT_MAX]
        if len(items) < N_RANDOM:
            pool = np.arange(0, qi)[-600:]
            taken = {it["base_top1"]["id"], it["pert_top1"]["id"]} | {c["id"] for c in it["controls"]}
            rr = random.Random(SEED2 * 7 + OFF[arm] * 1000 + len(items))
            for _ in range(200):
                gi = int(pool[rr.randrange(len(pool))])
                t = txt(gi)
                if C.ids[gi] in taken or len(t) < 30:
                    continue
                it["random_ctrl"] = {"id": C.ids[gi], "origin": str(C.origin[gi]), "text": t[:h.TXT_MAX]}
                break
        items.append(it)
    log(f"{arm}: {len(items)}/{n} items built from {tried} candidates tried of {len(cand)} eligible; "
        f"{sum(1 for i in items if 'random_ctrl' in i)} with random control")
    return items


async def run_judges(arm, items, cache_path, log):
    from core import judge_panel as jp
    import lab_decoupled_judge_context_pairs as j9
    cache = {}
    if Path(cache_path).exists():
        for line in open(cache_path, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                cache[r["k"]] = r
    todo = []
    for i, it in enumerate(items):
        roles = [("pert", it["pert_top1"]["text"])] + [(f"c{j+1}", c["text"]) for j, c in enumerate(it["controls"])]
        if "random_ctrl" in it:
            roles.append(("rand", it["random_ctrl"]["text"]))
        for role, text in roles:
            todo.append((f"R|{arm}2|{i}|{role}", "appropriate", j9.SYS_APPROP,
                         f"CURRENT TEXT:\n{it['query_text']}\n\nMEMORY PASSAGE:\n{text}"))
    random.Random(SEED2 + OFF[arm]).shuffle(todo)
    log(f"{len(todo)} panel items to rule ({sum(1 for k, *_ in todo if k in cache and cache[k].get('verdict') is not None)} cached)")
    t0 = time.time()
    streak = 0
    with open(cache_path, "a", encoding="utf-8") as fh:
        for n, (k, key, sysm, user) in enumerate(todo):
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
            streak = 0 if res["how"] in ("agreed", "tiebreak") else streak + 1
            if streak >= 4:                      # circuit breaker: shared hubs (Du may be live); stop, resume later from the cache
                log(f"ABORT: {streak} consecutive unavailable/split rulings at item {n}; cache checkpointed, rerun to resume")
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                fh.flush()
                raise SystemExit(3)
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            if (n + 1) % 10 == 0:
                log(f"  judged {n+1}/{len(todo)} {time.time()-t0:.0f}s last how={res['how']}")
    return cache


def pooled(arm, S, rng):
    """Descriptive only: pilot rows (J-2657) + new rows."""
    _, d = used_ids()
    pil = [r for r in d["stats"]["arms"][arm]["rows"] if r["p"] is not None and r["c_mean"] is not None]
    Dp = [float(bool(r["p"])) - r["c_mean"] for r in pil]
    Dn = [float(bool(r["p"])) - r["c_mean"] for r in S["rows"] if r["p"] is not None and r["c_mean"] is not None]
    D = Dp + Dn
    a = np.array(D)
    m = float(a.mean())
    nul = np.array([float((a * np.where(rng.random(len(a)) < 0.5, -1.0, 1.0)).mean()) for _ in range(5000)])
    return {"n_pilot": len(Dp), "n_new": len(Dn), "n": len(D), "mean_D": m, "ci": h.boot_mean(D, rng),
            "p_labelswap": float(np.mean(np.abs(nul) >= abs(m) - 1e-12)), "mean_D_pilot": float(np.mean(Dp)),
            "mean_D_new": float(np.mean(Dn)) if Dn else None, "sd_D_new": float(np.std(Dn, ddof=1)) if len(Dn) > 1 else None}


def stats(arm, items, cache):
    rng = np.random.default_rng(SEED2 + 100 + OFF[arm])
    L = arm + "2"                                        # label != "place": avoids the J-2639-cache branches in arm_stats
    S = h.arm_stats(L, items, cache, {}, rng)
    S["verdict"] = S.get("verdict", "NA").replace(" (n=15, underpowered)", "")
    S["pooled_with_pilot_descriptive"] = pooled(arm, S, np.random.default_rng(SEED2 + 200 + OFF[arm]))
    rows = [r for r in S["rows"] if r["p"] is not None and r["c_mean"] is not None]
    if rows:
        kmed = float(np.median([r["k"] for r in rows]))
        for nm, sel in (("k_le_median", lambda r: r["k"] <= kmed), ("k_gt_median", lambda r: r["k"] > kmed)):
            D = [float(bool(r["p"])) - r["c_mean"] for r in rows if sel(r)]
            S.setdefault("depth_split_descriptive", {})[nm] = {"n": len(D), "mean_D": float(np.mean(D)) if D else None,
                                                              "median_k_split": kmed}
    # G1 random control
    rn = [(cache.get(f"R|{L}|{i}|rand") or {}).get("verdict") for i, it in enumerate(items) if "random_ctrl" in it]
    rn = [v for v in rn if v is not None]
    S["random_ctrl_rate"] = float(np.mean([bool(v) for v in rn])) if rn else None
    S["random_ctrl_n"] = len(rn)
    R = [r for k, r in cache.items() if k.startswith(f"R|{L}|")]
    bf = [r for r in R if r["v1"] is not None and r["v2"] is not None]
    S["agreement"] = {"n_rulings": len(R), "v1_eq_v2": float(np.mean([r["v1"] == r["v2"] for r in bf])) if bf else None,
                      "tiebreak_fired": sum(1 for r in R if r["how"] == "tiebreak"),
                      "split_no_tiebreak": sum(1 for r in R if r["how"] == "split_no_tiebreak"),
                      "unavailable": sum(1 for r in R if r["how"] == "unavailable")}
    if bf:
        a = np.array([bool(r["v1"]) for r in bf]); b = np.array([bool(r["v2"]) for r in bf])
        po = float((a == b).mean()); pe = float(a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean()))
        S["agreement"]["cohen_kappa"] = (po - pe) / (1 - pe) if pe < 1 else None
    hubs = {}
    for r in R:
        k = f"{r.get('hub1')}/{r.get('hub2')}"
        hubs[k] = hubs.get(k, 0) + 1
    S["hubs_used"] = hubs
    return S


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=list(OFF))
    ap.add_argument("--n", type=int, default=90)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--stage", default="all")
    a = ap.parse_args()
    log = lambda s: print(s, flush=True)
    import lab_geometric_perturbation_sweep as v1
    from core import judge_panel as jp
    lab = Path(os.environ["J2663_LAB_DIR"])
    jp._LOG = lab / "judge_panel_log.jsonl"
    jp._DATA = lab
    canary = {str(h.LIVE_DB): (os.path.getsize(h.LIVE_DB), os.path.getmtime(h.LIVE_DB))}
    t0 = time.time()
    C = v1.load_cohort()
    log(f"cohort n={C.n} load {time.time()-t0:.0f}s")
    con = sqlite3.connect(v1.DB_URI, uri=True)
    items = build_items(v1, C, con, a.arm, a.n, log)
    con.close()
    out = {"seed": SEED2, "arm": a.arm, "n_target": a.n, "cohort_n": C.n, "items": items,
           "items_sha256": hashlib.sha256(json.dumps([(i["query_id"], i["pert_top1"]["id"], [c["id"] for c in i["controls"]])
                                                      for i in items]).encode()).hexdigest()}
    Path(a.out).write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    log("items_sha256 " + out["items_sha256"])
    if a.stage == "items":
        return
    cache = asyncio.run(run_judges(a.arm, items, a.cache, log))
    out["verdicts"] = cache
    out["stats"] = stats(a.arm, items, cache)
    out["canary"] = {p: {"before": list(v), "after": [os.path.getsize(p), os.path.getmtime(p)]} for p, v in canary.items()}
    out["runtime_s"] = time.time() - t0
    Path(a.out).write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    log("WROTE " + a.out + " verdict=" + str(out["stats"].get("verdict")))


if __name__ == "__main__":
    import core                                            # import core BEFORE lab_env (job-run live-store rule)
    assert str(Path(core.__file__).resolve()).lower().startswith(str(WT).lower()), core.__file__
    lab_root = None
    for i, x in enumerate(sys.argv):
        if x == "--lab-root":
            lab_root = Path(sys.argv[i + 1])
            del sys.argv[i:i + 2]
            break
    assert lab_root is not None, "--lab-root <dir under your scratchpad> is required"
    sys.path.insert(0, r"C:\Users\USER\.claude\skills\job-queue")
    import lab_env
    lab_env._LAB_ROOT = lab_root
    lab_env._ISOLATE_OUTCOMES_LOG = lab_root / "_isolate_outcomes.jsonl"
    with lab_env.isolate(db="empty") as _lab:
        assert str(Path(_lab).resolve()).lower().startswith(str(lab_root.resolve()).lower()), _lab
        os.environ["J2663_LAB_DIR"] = str(_lab)
        main()
