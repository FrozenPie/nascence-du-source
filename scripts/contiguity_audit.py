"""scripts/contiguity_audit.py -- J-2511 (F-3220 item 1, plan memory_as_a_service). READ-ONLY.

QUESTION. When Du recalls fragments together, were they also ENCODED in similar contexts, beyond what
temporal proximity (recency / gap) and content similarity predict? (Howard-Kahana retrieved-context
reinstatement -> the contiguity effect.) Plus the encoding-specificity twin: is a recalled fragment's
encoding context closer to Du's context AT RECALL TIME than a gap-matched random fragment's?

INPUTS (read only, zero LLM, zero embedder): data/co_recall_ledger.jsonl (memory_edges.log_co_recall),
data/memory/nascence.db opened file:...?mode=ro (fragment_context + the STORED 384-d float32 embeddings).
Writes nothing. Prints one JSON object.

DECLARED OVERLAP (fixed before looking at any result; never tuned):
  place    w=0.30  1 if equal
  sounds   w=0.25  Jaccard of the sounds lists
  affect   w=0.20  1 - |valence_a - valence_b| / 2
  tod      w=0.15  1 if circular |tod_a - tod_b| <= 1/12 (2 h band)
  season   w=0.10  1 if circular |season_a - season_b| <= 1/24 (~2 weeks)
  score = sum(w*component over fields present on BOTH rows) / sum(those w). Pairs with no shared field skipped.

PAIRS. Every unordered pair inside a served id set (ids capped at 8 by the logger), de-duplicated per
source (a pair the stream perseverates on counts once), both ends needing a fragment_context row and an
embedding. Capped at --max-pairs per source (seeded sample).

BASELINES, per co-recalled pair (a, b) with encoding gap g = |ts_a - ts_b| in log2 bin k:
  random       : a vs a uniformly random population fragment (no matching) -- reference only
  gap_matched  : a vs a random c with |ts_a - ts_c| in the same log2 bin k (recency/proximity controlled)
  cos_matched  : a vs c in the same gap bin AND |cos(a,c) - cos(a,b)| <= 0.03 (content controlled too)
Reported: mean overlap and the paired delta (co - baseline) with its standard error.

REINSTATEMENT (drift_delta): recall-time context = the fragment_context row nearest the ledger ts (within
900 s, not one of the recalled ids). For each recalled r: overlap(recall_ctx, ctx_r) vs a c whose gap to the
recall time sits in the same log2 bin as r's. drift = 1 - overlap.

COVERAGE caveat: fragment_context exists only for fragments stored after 2026-08-21 (layer law); tod/season
were backfilled (all rows carry them on 2026-10-30) but are only as good as their source tuple.
"""
import argparse, bisect, json, math, random, sqlite3, sys
from collections import defaultdict
from datetime import datetime
from itertools import combinations
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
W = {"place": 0.30, "sounds": 0.25, "affect": 0.20, "tod": 0.15, "season": 0.10}


def circ(a, b):
    d = abs(a - b) % 1.0
    return min(d, 1.0 - d)


def overlap(x, y, comp=None):
    num = den = 0.0
    parts = {}
    if x["place"] and y["place"]:
        parts["place"] = 1.0 if x["place"] == y["place"] else 0.0
    if x["sounds"] is not None and y["sounds"] is not None and (x["sounds"] or y["sounds"]):
        parts["sounds"] = len(x["sounds"] & y["sounds"]) / len(x["sounds"] | y["sounds"])
    if x["val"] is not None and y["val"] is not None:
        parts["affect"] = 1.0 - min(1.0, abs(x["val"] - y["val"]) / 2.0)
    if x["tod"] is not None and y["tod"] is not None:
        parts["tod"] = 1.0 if circ(x["tod"], y["tod"]) <= 1 / 12 else 0.0
    if x["season"] is not None and y["season"] is not None:
        parts["season"] = 1.0 if circ(x["season"], y["season"]) <= 1 / 24 else 0.0
    for k, v in parts.items():
        num += W[k] * v
        den += W[k]
        if comp is not None:
            comp[k].append(v)
    return num / den if den else None


def load(db):
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    ctx, ids, embs, ts = {}, [], [], []
    q = ("SELECT fc.fragment_id, fc.tuple_ts, fc.place, fc.sounds, fc.valence, fc.tod, fc.season, mf.embedding "
         "FROM fragment_context fc JOIN memory_fragments mf USING (fragment_id)")
    for fid, t, place, snd, val, tod, sea, emb in c.execute(q):
        try:
            s = set(json.loads(snd)) if snd else None
        except Exception:
            s = None
        ctx[fid] = {"ts": t, "place": place, "sounds": s, "val": val, "tod": tod, "season": sea, "i": None}
        if emb is not None and len(emb) == 1536 and t is not None:
            ctx[fid]["i"] = len(ids)
            ids.append(fid)
            embs.append(np.frombuffer(emb, dtype=np.float32))
            ts.append(t)
    c.close()
    E = np.vstack(embs).astype(np.float32)
    E /= np.linalg.norm(E, axis=1, keepdims=True) + 1e-9
    order = np.argsort(ts)
    return ctx, [ids[i] for i in order], E[order], np.asarray(ts)[order]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default=None, help="ISO local time; default = whole ledger")
    ap.add_argument("--db", default=str(ROOT / "data/memory/nascence.db"))
    ap.add_argument("--ledger", default=str(ROOT / "data/co_recall_ledger.jsonl"))
    ap.add_argument("--max-pairs", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    since = datetime.fromisoformat(a.since).timestamp() if a.since else 0.0

    ctx, pop_ids, E, T = load(a.db)
    for j, fid in enumerate(pop_ids):
        ctx[fid]["i"] = j
    n_pop = len(pop_ids)
    ctx_ts_sorted = sorted((v["ts"], k) for k, v in ctx.items() if v["ts"] is not None)
    ctx_t = [x[0] for x in ctx_ts_sorted]

    def in_bin(t0, k):
        lo, hi = 2.0 ** k, 2.0 ** (k + 1)
        spans = [(bisect.bisect_left(T, t0 + lo), bisect.bisect_left(T, t0 + hi)),
                 (bisect.bisect_right(T, t0 - hi), bisect.bisect_right(T, t0 - lo))]
        return [s for s in spans if s[1] > s[0]]

    def gbin(g):
        return int(math.floor(math.log2(max(g, 1.0))))

    pairs = defaultdict(set)
    events = defaultdict(list)
    n_rows = n_multi = 0
    for line in open(a.ledger, encoding="utf-8"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("ts", 0) < since:
            continue
        n_rows += 1
        src = r.get("source") or "legacy_none"
        ids = [i for i in (r.get("ids") or []) if isinstance(i, str)]
        if ids:
            events[src].append((r["ts"], ids))
        if len(ids) >= 2:
            n_multi += 1
            for x, y in combinations(sorted(set(ids)), 2):
                pairs[src].add((x, y))

    out = {"window_since": a.since or "all", "ledger_rows": n_rows, "multi_id_rows": n_multi,
           "population_with_ctx_and_emb": n_pop, "weights": W, "by_source": {}}
    allacc = defaultdict(list)
    for src in sorted(pairs):
        P = sorted(pairs[src])
        cov = [p for p in P if ctx.get(p[0], {}).get("i") is not None and ctx.get(p[1], {}).get("i") is not None]
        if len(cov) > a.max_pairs:
            cov = rng.sample(cov, a.max_pairs)
        acc = defaultdict(list)
        comp = defaultdict(list)
        for x, y in cov:
            cx, cy = ctx[x], ctx[y]
            o = overlap(cx, cy, comp)
            if o is None:
                continue
            k = gbin(abs(cx["ts"] - cy["ts"]))
            cos_ab = float(E[cx["i"]] @ E[cy["i"]])
            acc["co"].append(o)
            acc["gap_s"].append(abs(cx["ts"] - cy["ts"]))
            acc["cos"].append(cos_ab)
            # random (unmatched)
            o_r = overlap(cx, ctx[pop_ids[rng.randrange(n_pop)]])
            acc["d_random"].append(o - o_r if o_r is not None else None)
            spans = in_bin(cx["ts"], k)
            if not spans:
                continue
            cand = [j for s in spans for j in range(s[0], s[1]) if pop_ids[j] not in (x, y)]
            if not cand:
                continue
            c1 = pop_ids[rng.choice(cand)]
            o_g = overlap(cx, ctx[c1])
            if o_g is not None:
                acc["gap"].append(o_g)
                acc["d_gap"].append(o - o_g)
            samp = cand if len(cand) <= 600 else rng.sample(cand, 600)
            cs = E[samp] @ E[cx["i"]]
            ok = [samp[t] for t in np.nonzero(np.abs(cs - cos_ab) <= 0.03)[0]]
            if ok:
                o_c = overlap(cx, ctx[pop_ids[rng.choice(ok)]])
                if o_c is not None:
                    acc["cosm"].append(o_c)
                    acc["d_cos"].append(o - o_c)
        # reinstatement: recall-time context vs encoding context
        for t0, ids in events[src][-4000:]:
            j = bisect.bisect_left(ctx_t, t0)
            best = None
            for jj in (j - 2, j - 1, j, j + 1):
                if 0 <= jj < len(ctx_t) and abs(ctx_t[jj] - t0) <= 900 and ctx_ts_sorted[jj][1] not in ids:
                    if best is None or abs(ctx_t[jj] - t0) < abs(ctx_t[best] - t0):
                        best = jj
            if best is None:
                continue
            now = ctx[ctx_ts_sorted[best][1]]
            for rid in ids:
                cr = ctx.get(rid)
                if not cr or cr["i"] is None:
                    continue
                o = overlap(now, cr)
                spans = in_bin(t0, gbin(abs(t0 - cr["ts"])))
                cand = [jx for s in spans for jx in range(s[0], min(s[1], s[0] + 5000))]
                if o is None or not cand:
                    continue
                o_b = overlap(now, ctx[pop_ids[rng.choice(cand)]])
                if o_b is None:
                    continue
                acc["reinst"].append(o)
                acc["reinst_base"].append(o_b)
                acc["d_reinst"].append(o - o_b)

        def m(k):
            v = [z for z in acc[k] if z is not None]
            return (round(float(np.mean(v)), 4) if v else None), len(v)

        def d(k):
            v = [z for z in acc[k] if z is not None]
            if len(v) < 2:
                return None
            return {"mean": round(float(np.mean(v)), 4), "se": round(float(np.std(v, ddof=1) / math.sqrt(len(v))), 4), "n": len(v)}

        res = {"unique_pairs": len(P), "pairs_with_ctx": len([p for p in P if ctx.get(p[0], {}).get("i") is not None and ctx.get(p[1], {}).get("i") is not None]),
               "scored": m("co")[1], "co_overlap": m("co")[0], "random": m("d_random")[0] and round(m("co")[0] - m("d_random")[0], 4),
               "gap_matched": m("gap")[0], "cos_matched": m("cosm")[0],
               "delta_vs_random": d("d_random"), "delta_vs_gap": d("d_gap"), "delta_vs_cos": d("d_cos"),
               "median_gap_h": round(float(np.median(acc["gap_s"])) / 3600, 2) if acc["gap_s"] else None,
               "mean_cos": m("cos")[0],
               "components_co": {k: round(float(np.mean(v)), 3) for k, v in comp.items()},
               "reinstatement": {"recall_vs_encoding": m("reinst")[0], "gap_matched_base": m("reinst_base")[0],
                                 "delta": d("d_reinst"),
                                 "drift_delta_co": m("reinst")[0] is not None and round(1 - m("reinst")[0], 4)}}
        out["by_source"][src] = res
        if not src.endswith("_shadow") and src != "legacy_none":
            for k in ("d_gap", "d_cos", "d_reinst", "co", "gap", "cosm"):
                allacc[k].extend(z for z in acc[k] if z is not None)
    out["pooled_shown_sources"] = {k: {"mean": round(float(np.mean(v)), 4), "n": len(v),
                                       "se": round(float(np.std(v, ddof=1) / math.sqrt(len(v))), 4) if len(v) > 1 else None}
                                   for k, v in allacc.items() if v}
    json.dump(out, sys.stdout, indent=1)


if __name__ == "__main__":
    main()
