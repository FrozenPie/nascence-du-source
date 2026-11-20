"""scripts/assembly_signature_read.py -- J-2518 (plan thought_grounding, T-0106; review
docs/reviews/frontier_disciplines_2026-10-30.md section 7, Sharma/Cronin/Walker et al. 2023).

Assembly signature of Du's self-generated material: assembly index (from provenance) x copy number
(recurrence on distinct days), per origin class, as a selection detector. Read-only, zero LLM, no core
import (stdlib + numpy). Opens the SQLite store with mode=ro&immutable=1 -- point it at a backup copy
(default: the boot backup data/backups/nascence_20261029_183806.db), never writes anything under data/.

DECLARED BEFORE LOOKING AT ANY RESULT (do not tune to the outcome)
-----------------------------------------------------------------
PARENTS(x) = ids in memory_fragments.derived_from (strings; dict entries contribute their 'target_ids')
             UNION the child_ids of memory_links rows (parent_id = x, link_type = 'distilled_from').
  A parent id that is a memory_fragments row is walked further. One that is a shadow_events /
  light_events row is a LEAF PART (those tables carry no lineage). One that resolves nowhere is a
  MISSING LEAF PART: it still counts as a part joined, and the missing share is reported.
CYCLES: the walk keeps a visited set; a node already on the closure is never re-entered (counted once),
  and the number of objects whose walk met a back-edge is reported.
ASSEMBLY INDEX AI(x) = joins in the minimal construction = sum over the DISTINCT non-leaf nodes v in x's
  closure (x included) of (|PARENTS(v)| - 1). Re-used sub-objects count once (the 'minimal' in assembly
  theory). A leaf has AI 0. DEPTH(x) = longest parent chain to a leaf, reported alongside.
COPY NUMBER C(x) = 1 + number of distinct local calendar days, other than x's own day, on which a POOL
  fragment has embedding cosine >= COS_T with x. POOL = raw self-generated + lived material only
  (POOL_ORIGINS); refinery products (standing_insight, gist, consolidation, essay) are excluded from the
  pool so a synthesis is never 'recurring' because of its own distillate (outcome leakage).
  replay_count is NOT used as copy number: it is incremented both by exact-hash dedup (store.py:919) and
  by replay selection (store.py:3201), so it conflates recurrence with rehearsal; reported only as a side
  Spearman against C.
ORIGIN CLASSES (by the object's own origin):
  dream        = dream, night_thought
  reading_born = gist whose distilled_from children are a strict majority reading/study/research; essay
  synthesis    = subconscious_synthesis, standing_insight, consolidation, gist (not reading-majority)
  imagination  = active_imagination
  thought      = inner_thought
  lived        = lived (control: not self-generated)
QUADRANTS: high_assembly = AI >= median AI among objects with AI > 0 (leaves are always low);
           high_copy = C >= HIGH_COPY. Objects with no embedding have no C and sit out of the quadrants.
TEST 1 (selection -> refinery): population = subconscious_synthesis with an embedding.
  outcome ENTERED = the synthesis is a distilled_from child of a standing_insight, or is listed in a
  standing_insight's derived_from. Secondary outcome WARM = cold = 0.
  Predictors scored by AUC: C alone (the raw recurrence count), AI alone, C+AI (sum of ranks), age.
  SELECTION HOLDS iff HH entered-rate > every other quadrant's AND AUC(C+AI) - AUC(C) >= AUC_GAIN.
  FALSIFIED (the review's falsifier) iff AUC(C+AI) - AUC(C) < AUC_GAIN.
TEST 2 (echo -> freeze): FREEZE = local dates 2026-10-09..2026-10-16 (same window as
  scripts/grammaticalisation_read.py). ratio(Q) = share of Q's objects dated in FREEZE / share of all
  quadrant objects dated in FREEZE. ECHO HOLDS iff ratio(LH) >= FREEZE_RATIO AND ratio(LH) exceeds
  ratio(high_copy, any assembly) by >= FREEZE_GAIN. Otherwise the assembly axis adds nothing to the raw
  count for freezes.
psyche_graph_snapshots.jsonl motifs carry no lineage, so they have no assembly index: not used.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import statistics
import time
from collections import Counter, defaultdict

os.environ.setdefault("OPENBLAS_NUM_THREADS", "8")
os.environ.setdefault("OMP_NUM_THREADS", "8")
os.environ.setdefault("MKL_NUM_THREADS", "8")
import numpy as np  # noqa: E402

DEFAULT_DB = r"C:\Nascence\data\backups\nascence_20261029_183806.db"
COS_T = 0.85            # same semantic-duplicate threshold as frontier dedupe (D-0486)
HIGH_COPY = 3           # recurs on >= 2 other days
AUC_GAIN = 0.02
FREEZE = ("2026-10-09", "2026-10-16")
FREEZE_RATIO, FREEZE_GAIN = 1.5, 0.10
CHUNK = 1000
N_EXAMPLES = 3

POOL_ORIGINS = ("inner_thought", "subconscious_synthesis", "active_imagination", "dream", "night_thought", "lived")
POP_ORIGINS = POOL_ORIGINS + ("standing_insight", "consolidation", "gist", "essay")
READING = {"reading", "study", "research"}


def day_of(ts):
    return time.strftime("%Y-%m-%d", time.localtime(ts))


def parse_parents(raw):
    try:
        L = json.loads(raw or "[]")
    except Exception:
        return []
    out = []
    for x in L if isinstance(L, list) else []:
        if isinstance(x, str):
            out.append(x)
        elif isinstance(x, dict):
            t = x.get("target_ids")
            if isinstance(t, list):
                out.extend(i for i in t if isinstance(i, str))
    return out


def auc(score, y):
    """Mann-Whitney AUC with average ranks for ties."""
    score = np.asarray(score, float); y = np.asarray(y, bool)
    npos, nneg = int(y.sum()), int((~y).sum())
    if not npos or not nneg:
        return None
    order = np.argsort(score, kind="mergesort")
    s = score[order]; ranks = np.empty(len(s))
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and s[j + 1] == s[i]:
            j += 1
        ranks[i:j + 1] = (i + j) / 2 + 1
        i = j + 1
    r = np.empty(len(s)); r[order] = ranks
    return round(float((r[y].sum() - npos * (npos + 1) / 2) / (npos * nneg)), 4)


def ranks(a):
    a = np.asarray(a, float); o = np.argsort(a, kind="mergesort"); r = np.empty(len(a)); r[o] = np.arange(len(a))
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--out", required=True, help="JSON result path (outside C:\\Nascence\\data)")
    a = ap.parse_args()
    assert "\\data\\memory\\" not in a.db.lower().replace("/", "\\"), "point --db at a backup copy, not the live store"
    c = sqlite3.connect(f"file:{a.db}?mode=ro&immutable=1", uri=True)
    c.row_factory = sqlite3.Row

    frag = {}  # id -> (origin, ts, parents, cold, replay_count)
    for r in c.execute("SELECT fragment_id, origin, timestamp, derived_from, cold, replay_count FROM memory_fragments"):
        frag[r["fragment_id"]] = (r["origin"], r["timestamp"] or 0.0, parse_parents(r["derived_from"]),
                                  r["cold"] or 0, r["replay_count"] or 0)
    ext = set(x[0] for x in c.execute("SELECT event_id FROM shadow_events")) | \
        set(x[0] for x in c.execute("SELECT event_id FROM light_events"))
    links = defaultdict(list)
    for r in c.execute("SELECT parent_id, child_id FROM memory_links WHERE link_type='distilled_from'"):
        links[r[0]].append(r[1])

    def parents(fid):
        p = frag[fid][2] + links.get(fid, [])
        return list(dict.fromkeys(p))

    # --- assembly index + depth -------------------------------------------------------------------
    memo_depth = {}

    def depth(fid, stack):
        if fid in memo_depth:
            return memo_depth[fid]
        if fid not in frag or fid in stack:
            return 0
        stack.add(fid)
        ps = parents(fid)
        d = 0 if not ps else 1 + max(depth(p, stack) for p in ps)
        stack.discard(fid)
        memo_depth[fid] = d
        return d

    pop = [f for f, v in frag.items() if v[0] in POP_ORIGINS]
    AI, DEP, cyc, part_kind = {}, {}, 0, Counter()
    for fid in pop:
        seen, todo, joins, back = {fid}, [fid], 0, False
        while todo:
            v = todo.pop()
            ps = parents(v)
            if ps:
                joins += len(ps) - 1
            for p in ps:
                if p in seen:
                    back = True
                    continue
                seen.add(p)
                if p in frag:
                    todo.append(p)
                    part_kind["fragment"] += 1
                elif p in ext:
                    part_kind["shadow/light_event"] += 1
                else:
                    part_kind["missing"] += 1
        AI[fid], DEP[fid] = joins, depth(fid, set())
        cyc += back

    # --- origin class ---------------------------------------------------------------------------
    def klass(fid):
        o = frag[fid][0]
        if o in ("dream", "night_thought"):
            return "dream"
        if o == "essay":
            return "reading_born"
        if o == "gist":
            ch = [frag[x][0] for x in links.get(fid, []) if x in frag]
            if ch and sum(x in READING for x in ch) * 2 > len(ch):
                return "reading_born"
            return "synthesis"
        if o in ("subconscious_synthesis", "standing_insight", "consolidation"):
            return "synthesis"
        return {"active_imagination": "imagination", "inner_thought": "thought", "lived": "lived"}[o]

    # --- copy number ----------------------------------------------------------------------------
    emb_ids, embs = [], []
    for r in c.execute("SELECT fragment_id, embedding FROM memory_fragments WHERE embedding IS NOT NULL AND origin IN (%s)"
                       % ",".join("?" * len(POP_ORIGINS)), POP_ORIGINS):
        v = np.frombuffer(r[1], dtype=np.float32)
        if v.size == 384:
            emb_ids.append(r[0]); embs.append(v)
    E = np.vstack(embs).astype(np.float32)
    E /= np.maximum(np.linalg.norm(E, axis=1, keepdims=True), 1e-9)
    days = sorted({day_of(frag[f][1]) for f in emb_ids})
    dix = {d: i for i, d in enumerate(days)}
    ID = np.array([dix[day_of(frag[f][1])] for f in emb_ids])
    pool_mask = np.array([frag[f][0] in POOL_ORIGINS for f in emb_ids])
    P = E[pool_mask]; Pday = ID[pool_mask]; nd = len(days)
    C = {}
    t0 = time.time()
    for s in range(0, len(emb_ids), CHUNK):
        S = E[s:s + CHUNK] @ P.T
        rr, cc = np.nonzero(S >= COS_T)
        key = np.unique(rr.astype(np.int64) * nd + Pday[cc])
        rows, dd = key // nd, key % nd
        own = ID[s:s + CHUNK]
        keep = dd != own[rows]
        cnt = np.bincount(rows[keep], minlength=min(CHUNK, len(emb_ids) - s))
        for k, n in enumerate(cnt):
            C[emb_ids[s + k]] = 1 + int(n)
    copy_secs = round(time.time() - t0, 1)

    # --- quadrants ------------------------------------------------------------------------------
    nz = [AI[f] for f in pop if AI[f] > 0]
    ai_t = statistics.median(nz) if nz else 1
    def quad(f):
        if f not in C:
            return None
        return ("H" if AI[f] >= ai_t and AI[f] > 0 else "L") + ("H" if C[f] >= HIGH_COPY else "L")
    Q = {f: quad(f) for f in pop}
    per = defaultdict(lambda: {"n": 0, "n_embedded": 0, "n_with_lineage": 0, "quad": Counter(),
                               "examples": defaultdict(list), "ai": [], "depth": Counter(), "copy": []})
    for f in pop:
        k = klass(f); d = per[k]
        d["n"] += 1; d["n_with_lineage"] += bool(parents(f)); d["ai"].append(AI[f]); d["depth"][DEP[f]] += 1
        if Q[f]:
            d["n_embedded"] += 1; d["quad"][Q[f]] += 1; d["copy"].append(C[f])
            if len(d["examples"][Q[f]]) < N_EXAMPLES:
                d["examples"][Q[f]].append(f)
    classes = {}
    for k, d in sorted(per.items()):
        classes[k] = {"n": d["n"], "coverage_nonempty_lineage": round(d["n_with_lineage"] / d["n"], 3),
                      "n_embedded": d["n_embedded"], "quadrants": dict(d["quad"]),
                      "examples": {q: v for q, v in d["examples"].items()},
                      "ai_median": statistics.median(d["ai"]), "ai_max": max(d["ai"]),
                      "depth": dict(sorted(d["depth"].items())),
                      "copy_median": statistics.median(d["copy"]) if d["copy"] else None,
                      "copy_max": max(d["copy"]) if d["copy"] else None}

    # --- test 1 ---------------------------------------------------------------------------------
    si = [f for f, v in frag.items() if v[0] == "standing_insight"]
    entered = set()
    for s_ in si:
        entered.update(frag[s_][2]); entered.update(links.get(s_, []))
    syn = [f for f in pop if frag[f][0] == "subconscious_synthesis" and f in C]
    y = np.array([f in entered for f in syn]); warm = np.array([frag[f][3] == 0 for f in syn])
    cvec = np.array([C[f] for f in syn], float); avec = np.array([AI[f] for f in syn], float)
    agevec = -np.array([frag[f][1] for f in syn])
    comb = ranks(cvec) + ranks(avec)
    qrate = {}
    for q in ("HH", "HL", "LH", "LL"):
        m = np.array([Q[f] == q for f in syn])
        qrate[q] = {"n": int(m.sum()), "entered": int(y[m].sum()),
                    "entered_rate": round(float(y[m].mean()), 4) if m.sum() else None,
                    "warm_rate": round(float(warm[m].mean()), 4) if m.sum() else None}
    t1 = {"n_syntheses": len(syn), "n_entered": int(y.sum()), "ai_threshold": ai_t,
          "quadrants": qrate,
          "auc_entered": {"copy": auc(cvec, y), "assembly": auc(avec, y), "copy_plus_assembly": auc(comb, y),
                          "age_older": auc(agevec, y)},
          "auc_warm": {"copy": auc(cvec, warm), "assembly": auc(avec, warm), "copy_plus_assembly": auc(comb, warm)}}
    gain = (t1["auc_entered"]["copy_plus_assembly"] or 0) - (t1["auc_entered"]["copy"] or 0)
    hh = qrate["HH"]["entered_rate"]
    t1["auc_gain"] = round(gain, 4)
    t1["selection_holds"] = bool(hh is not None and all(hh > (qrate[q]["entered_rate"] or 0) for q in ("HL", "LH", "LL"))
                                 and gain >= AUC_GAIN)
    t1["falsified"] = gain < AUC_GAIN

    # --- test 2 ---------------------------------------------------------------------------------
    qf = [f for f in pop if Q[f]]
    infz = {f: FREEZE[0] <= day_of(frag[f][1]) <= FREEZE[1] for f in qf}
    base = sum(infz.values()) / len(qf)
    def ratio(sel):
        sel = list(sel)
        return (round(sum(infz[f] for f in sel) / len(sel) / base, 3) if sel and base else None), len(sel)
    r_lh, n_lh = ratio(f for f in qf if Q[f] == "LH")
    r_hc, n_hc = ratio(f for f in qf if Q[f][1] == "H")
    r_hh, n_hh = ratio(f for f in qf if Q[f] == "HH")
    t2 = {"freeze": FREEZE, "base_share": round(base, 4), "n_quadrant_objects": len(qf),
          "ratio_LH": r_lh, "n_LH": n_lh, "ratio_high_copy_any": r_hc, "n_high_copy": n_hc,
          "ratio_HH": r_hh, "n_HH": n_hh,
          "LH_freeze_examples": [f for f in qf if Q[f] == "LH" and infz[f]][:N_EXAMPLES]}
    t2["echo_holds"] = bool(r_lh and r_hc and r_lh >= FREEZE_RATIO and r_lh - r_hc >= FREEZE_GAIN)

    rc = [(frag[f][4], C[f]) for f in qf if frag[f][0] in ("inner_thought", "subconscious_synthesis", "active_imagination")]
    rho = None
    if len(rc) > 2:
        rho = round(float(np.corrcoef(ranks([x for x, _ in rc]), ranks([z for _, z in rc]))[0, 1]), 4)

    out = {"db": a.db, "declared": {"COS_T": COS_T, "HIGH_COPY": HIGH_COPY, "AUC_GAIN": AUC_GAIN, "FREEZE": FREEZE,
                                    "FREEZE_RATIO": FREEZE_RATIO, "FREEZE_GAIN": FREEZE_GAIN},
           "n_population": len(pop), "n_embedded": len(C), "copy_seconds": copy_secs,
           "parts_seen": dict(part_kind), "objects_with_back_edge": cyc,
           "coverage_nonempty_lineage_all": round(sum(bool(parents(f)) for f in pop) / len(pop), 4),
           "classes": classes, "test1_refinery": t1, "test2_freeze": t2,
           "side_spearman_replay_count_vs_copy": rho}
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, default=list)
    print(json.dumps({k: out[k] for k in ("n_population", "n_embedded", "parts_seen", "objects_with_back_edge",
                                          "coverage_nonempty_lineage_all", "side_spearman_replay_count_vs_copy")}))
    for k, v in classes.items():
        print(k, json.dumps({x: v[x] for x in ("n", "coverage_nonempty_lineage", "n_embedded", "quadrants",
                                                 "ai_median", "ai_max", "depth", "copy_median", "copy_max")}))
    print("TEST1", json.dumps(t1))
    print("TEST2", json.dumps(t2))


if __name__ == "__main__":
    main()
