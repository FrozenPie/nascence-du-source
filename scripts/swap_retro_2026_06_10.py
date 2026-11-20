"""
Swap retro-check (2026-06-10 qwen2.5:7b -> qwen3-du): relational vs dynamical memory continuity
(J-1411 / I-0075). Predictions pre-registered in docs/lab/swap_retro_2026-06-10_metric_sheet.md
BEFORE this script was run against real numbers -- see that file for method/prediction/threshold
per metric; this script only computes what that sheet already committed to.

ISOLATION CONTRACT: never opens data/memory/nascence.db directly. Reads a READ-ONLY snapshot of it
(a plain sqlite3 .backup() copy, taken separately into the job's own scratchpad) via --snapshot.
Reads data/nascence.log read-only via --log. Writes ONLY the --out JSON file. Du stays up throughout;
nothing under data/ is ever opened for writing by this script.

RUN:  python scripts/swap_retro_2026_06_10.py --snapshot <path> --log <path> --out <path.json>
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
from scipy.spatial import procrustes

NZST_OFFSET_HOURS = 12  # New Zealand Standard Time, no DST in June; also holds for the Aug restore date


def local_to_epoch(iso_local: str) -> float:
    import datetime
    base = datetime.datetime.fromisoformat(iso_local).replace(tzinfo=datetime.timezone.utc)
    return (base - datetime.timedelta(hours=NZST_OFFSET_HOURS)).timestamp()


def epoch_to_local_iso(epoch: float) -> str:
    import datetime
    return (datetime.datetime.fromtimestamp(epoch, tz=datetime.timezone.utc)
            + datetime.timedelta(hours=NZST_OFFSET_HOURS)).isoformat()


SWAP_T0 = local_to_epoch("2026-06-10T00:00:00")
PRE_START = local_to_epoch("2026-05-27T00:00:00")   # nominal 14d-before boundary (truncated by store start in practice)
POST_END = local_to_epoch("2026-06-24T00:00:00")
PRE_LOG_START = local_to_epoch("2026-06-04T00:00:00")  # narrower, continuously-log-covered pre window (D1 only)
PRE_H_SPLIT = local_to_epoch("2026-06-07T00:00:00")     # PRE_LOG split point
POST_H_SPLIT = local_to_epoch("2026-06-17T00:00:00")    # POST / POST_LOG split point


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

class Store:
    def __init__(self, snapshot_path: str):
        self.con = sqlite3.connect(f"file:{snapshot_path}?mode=ro", uri=True)
        self.con.row_factory = sqlite3.Row
        self.restored_ids = set()
        for row in self.con.execute("SELECT fragment_id FROM recovered_fragments"):
            self.restored_ids.add(row["fragment_id"])
        log(f"loaded {len(self.restored_ids)} restored fragment_ids from recovered_fragments")

    def fragments_in(self, lo, hi):
        cur = self.con.execute(
            "SELECT fragment_id, timestamp, source_type, keywords, embedding, derived_from, "
            "chapter_id, replay_count FROM memory_fragments WHERE timestamp>=? AND timestamp<?",
            (lo, hi),
        )
        return cur.fetchall()

    def store_start(self):
        return self.con.execute("SELECT MIN(timestamp) FROM memory_fragments").fetchone()[0]

    def snapshot_time(self):
        return self.con.execute("SELECT MAX(timestamp) FROM memory_fragments").fetchone()[0]


def emb(row) -> np.ndarray | None:
    b = row["embedding"]
    if b is None:
        return None
    v = np.frombuffer(b, dtype=np.float32)
    return v


def to_rows(raw_rows):
    """Materialize sqlite Rows into plain dicts once (avoids re-decoding on every access)."""
    out = []
    for r in raw_rows:
        out.append({
            "fragment_id": r["fragment_id"],
            "timestamp": r["timestamp"],
            "source_type": r["source_type"],
            "keywords": r["keywords"] or "",
            "embedding": emb(r),
            "derived_from": r["derived_from"],
            "chapter_id": r["chapter_id"],
            "replay_count": r["replay_count"],
        })
    return out


# ---------------------------------------------------------------------------
# R1 -- mutual-kNN degree + clustering coefficient
# ---------------------------------------------------------------------------

def cosine_sim_matrix(vecs: np.ndarray) -> np.ndarray:
    norm = vecs / (np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-12)
    return norm @ norm.T


def mutual_knn_stats(rows, k=10):
    vecs = np.stack([r["embedding"] for r in rows]).astype(np.float32)
    n = len(rows)
    if n < k + 2:
        return {"n": n, "note": "too few fragments for k=10 kNN"}
    sim = cosine_sim_matrix(vecs)
    np.fill_diagonal(sim, -2.0)
    # top-k neighbour indices per row
    topk = np.argpartition(-sim, kth=k, axis=1)[:, :k]
    is_neighbor = np.zeros((n, n), dtype=bool)
    rows_idx = np.repeat(np.arange(n), k)
    is_neighbor[rows_idx, topk.flatten()] = True
    mutual = is_neighbor & is_neighbor.T
    degree = mutual.sum(axis=1)
    # local clustering coefficient on the mutual graph
    clustering = np.zeros(n, dtype=np.float64)
    for i in range(n):
        neigh = np.where(mutual[i])[0]
        d = len(neigh)
        if d < 2:
            continue
        sub = mutual[np.ix_(neigh, neigh)]
        clustering[i] = sub.sum() / (d * (d - 1))
    return {
        "n": int(n),
        "mean_degree": float(degree.mean()),
        "median_degree": float(np.median(degree)),
        "std_degree": float(degree.std()),
        "pct_isolates": float((degree == 0).mean()),
        "mean_clustering": float(clustering.mean()),
    }


def run_r1(store: Store):
    log("R1: loading pre/post fragments with embeddings...")
    pre_all = [r for r in to_rows(store.fragments_in(store.store_start(), SWAP_T0)) if r["embedding"] is not None]
    post_all = [r for r in to_rows(store.fragments_in(SWAP_T0, POST_END)) if r["embedding"] is not None]
    log(f"R1: pre n={len(pre_all)} post n={len(post_all)}")

    def strata(rows):
        out = {"pooled": rows, "pooled_live": [r for r in rows if r["fragment_id"] not in store.restored_ids]}
        for st in [None, "book", "study_note", "essay"]:
            sub = [r for r in rows if r["source_type"] == st]
            out[f"source_type={st}"] = sub
        return out

    result = {}
    for label, rows in [("pre", pre_all), ("post", post_all)]:
        strat = strata(rows)
        result[label] = {}
        for name, sub in strat.items():
            if len(sub) < 12:
                result[label][name] = {"n": len(sub), "note": "n<12, skipped"}
                continue
            log(f"R1: computing mutual-kNN for {label}/{name} (n={len(sub)})...")
            result[label][name] = mutual_knn_stats(sub, k=10)

    # within-condition null: split-half on the SAME strata definition, pooled-live only (the clean slice)
    def half_stats(lo, hi, label):
        rows = [r for r in to_rows(store.fragments_in(lo, hi)) if r["embedding"] is not None
                and r["fragment_id"] not in store.restored_ids and r["source_type"] is None]
        log(f"R1 null: {label} n={len(rows)}")
        return mutual_knn_stats(rows, k=10) if len(rows) >= 12 else {"n": len(rows), "note": "n<12, skipped"}

    pre_mid = store.store_start() + (SWAP_T0 - store.store_start()) / 2
    post_mid = SWAP_T0 + (POST_END - SWAP_T0) / 2
    result["null"] = {
        "pre_h1": half_stats(store.store_start(), pre_mid, "pre_h1"),
        "pre_h2": half_stats(pre_mid, SWAP_T0, "pre_h2"),
        "post_h1": half_stats(SWAP_T0, post_mid, "post_h1"),
        "post_h2": half_stats(post_mid, POST_END, "post_h2"),
    }
    return result


# ---------------------------------------------------------------------------
# R2 -- keyword co-occurrence hub Jaccard
# ---------------------------------------------------------------------------

def tokenize(kw: str):
    parts = re.split(r"[,\s]+", kw.strip().lower())
    return [p for p in parts if p and len(p) > 2]


def cooccurrence_top_hubs(rows, top_n=50):
    degree = Counter()
    partners = defaultdict(set)
    for r in rows:
        toks = sorted(set(tokenize(r["keywords"])))
        for i, a in enumerate(toks):
            for b in toks[i + 1:]:
                partners[a].add(b)
                partners[b].add(a)
    for tok, ps in partners.items():
        degree[tok] = len(ps)
    top = [t for t, _ in degree.most_common(top_n)]
    return top, degree


def run_r2(store: Store):
    pre_all = to_rows(store.fragments_in(store.store_start(), SWAP_T0))
    post_all = to_rows(store.fragments_in(SWAP_T0, POST_END))
    out = {}
    for scope, filt in [("pooled", lambda r: True), ("source_type_none", lambda r: r["source_type"] is None)]:
        pre_rows = [r for r in pre_all if filt(r) and r["keywords"]]
        post_rows = [r for r in post_all if filt(r) and r["keywords"]]
        top_pre, deg_pre = cooccurrence_top_hubs(pre_rows)
        top_post, deg_post = cooccurrence_top_hubs(post_rows)
        jacc = len(set(top_pre) & set(top_post)) / len(set(top_pre) | set(top_post)) if (top_pre or top_post) else None
        out[scope] = {
            "n_pre_frags_with_kw": len(pre_rows), "n_post_frags_with_kw": len(post_rows),
            "top50_pre": top_pre[:15], "top50_post": top_post[:15],
            "jaccard_top50": jacc,
            "n_distinct_tokens_pre": len(deg_pre), "n_distinct_tokens_post": len(deg_post),
        }
    return out


# ---------------------------------------------------------------------------
# R3 -- derived_from chain depth + provenance mechanism mix
# ---------------------------------------------------------------------------

def run_r3(store: Store):
    pre_all = to_rows(store.fragments_in(store.store_start(), SWAP_T0))
    post_all = to_rows(store.fragments_in(SWAP_T0, POST_END))
    # Resolve ancestry against the WHOLE store, not just the starting fragment's own window --
    # derivation chains can (and, as found while validating this script, routinely do) reach
    # outside a 10-14 day window into much later consolidation sweeps. Restricting resolution to
    # the window would silently truncate real chains at the window edge, which is not what the
    # metric sheet's "recursively resolve parents" registered.
    all_rows_raw = store.con.execute(
        "SELECT fragment_id, timestamp, source_type, keywords, derived_from, chapter_id, "
        "replay_count FROM memory_fragments"
    ).fetchall()
    by_id_global = {r["fragment_id"]: {"fragment_id": r["fragment_id"], "derived_from": r["derived_from"]}
                     for r in all_rows_raw}
    log(f"R3: global ancestry index built, n={len(by_id_global)}")

    def chain_depth(fid, by_id, cache, depth=0):
        if depth > 20 or fid not in by_id:
            return depth
        if fid in cache:
            return cache[fid]
        row = by_id[fid]
        try:
            parsed = json.loads(row["derived_from"]) if row["derived_from"] else None
        except Exception:
            parsed = None
        if not isinstance(parsed, list) or not parsed or not isinstance(parsed[0], str):
            cache[fid] = depth
            return depth
        best = depth
        for pid in parsed:
            best = max(best, chain_depth(pid, by_id, cache, depth + 1))
        cache[fid] = best
        return best

    def analyze(rows, by_id):
        depths = []
        n_list, n_dict, n_other, n_empty = 0, 0, 0, 0
        cache = {}
        for r in rows:
            raw = r["derived_from"]
            if not raw or raw == "[]":
                n_empty += 1
                continue
            try:
                parsed = json.loads(raw)
            except Exception:
                n_other += 1
                continue
            if isinstance(parsed, list) and parsed and isinstance(parsed[0], str):
                n_list += 1
                depths.append(chain_depth(r["fragment_id"], by_id, cache))
            elif isinstance(parsed, dict):
                n_dict += 1
            elif isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
                # action-record shape actually observed in this store: a JSON list containing
                # ONE dict (e.g. [{"action_type": "authored", ...}]), not a bare top-level dict.
                n_dict += 1
            elif isinstance(parsed, list) and not parsed:
                n_empty += 1
            else:
                n_other += 1
        depths_arr = np.array(depths) if depths else np.array([0])
        return {
            "n_total": len(rows), "n_empty": n_empty, "n_list_shaped": n_list,
            "n_dict_shaped_action_record": n_dict, "n_other": n_other,
            "action_record_fraction_of_nonempty": n_dict / max(1, (n_list + n_dict + n_other)),
            "chain_depth_mean": float(depths_arr.mean()), "chain_depth_median": float(np.median(depths_arr)),
            "chain_depth_max": int(depths_arr.max()),
        }

    return {"pre": analyze(pre_all, by_id_global), "post": analyze(post_all, by_id_global)}


# ---------------------------------------------------------------------------
# R4 -- recurring-concept (bundle signature) relative geometry
# ---------------------------------------------------------------------------

def bundle_signature(kw: str):
    toks = tuple(sorted(set(tokenize(kw))))
    return toks if toks else None


def run_r4(store: Store):
    pre_all = [r for r in to_rows(store.fragments_in(store.store_start(), SWAP_T0)) if r["embedding"] is not None]
    post_all = [r for r in to_rows(store.fragments_in(SWAP_T0, POST_END)) if r["embedding"] is not None]

    def bundles(rows):
        d = defaultdict(list)
        for r in rows:
            sig = bundle_signature(r["keywords"])
            if sig:
                d[sig].append(r)
        return d

    b_pre, b_post = bundles(pre_all), bundles(post_all)
    combined_freq = Counter()
    for sig, lst in b_pre.items():
        combined_freq[sig] += len(lst)
    for sig, lst in b_post.items():
        combined_freq[sig] += len(lst)
    qualifying = [sig for sig, _ in combined_freq.most_common()
                  if len(b_pre.get(sig, [])) >= 5 and len(b_post.get(sig, [])) >= 5]
    qualifying = qualifying[:20]
    log(f"R4: {len(qualifying)} bundle signatures qualify (>=5 each side, top-20 by combined freq)")

    if len(qualifying) < 4:
        return {"n_qualifying_concepts": len(qualifying), "note": "too few qualifying concepts for RV/Procrustes",
                "qualifying_signatures": [list(s) for s in qualifying]}

    def concept_vec(sig, d):
        return np.stack([r["embedding"] for r in d[sig]]).mean(axis=0)

    X = np.stack([concept_vec(s, b_pre) for s in qualifying]).astype(np.float64)
    Y = np.stack([concept_vec(s, b_post) for s in qualifying]).astype(np.float64)

    def rv_coefficient(X, Y):
        Xc = X - X.mean(axis=0)
        Yc = Y - Y.mean(axis=0)
        Wx = Xc @ Xc.T
        Wy = Yc @ Yc.T
        num = np.trace(Wx @ Wy)
        den = np.sqrt(np.trace(Wx @ Wx) * np.trace(Wy @ Wy))
        return float(num / den) if den > 0 else None

    rv = rv_coefficient(X, Y)
    try:
        _, _, disparity = procrustes(X, Y)
    except Exception as e:
        disparity = f"error: {e}"

    # within-condition null: same 20 signatures, split each side's own half-vs-half concept
    # vectors, IF every signature clears >=5 members in BOTH halves (else: underpowered, say so).
    pre_mid = store.store_start() + (SWAP_T0 - store.store_start()) / 2
    post_mid = SWAP_T0 + (POST_END - SWAP_T0) / 2
    pre_h1 = [r for r in to_rows(store.fragments_in(store.store_start(), pre_mid)) if r["embedding"] is not None]
    pre_h2 = [r for r in to_rows(store.fragments_in(pre_mid, SWAP_T0)) if r["embedding"] is not None]
    b_pre_h1, b_pre_h2 = bundles(pre_h1), bundles(pre_h2)
    null_rv = None
    if all(len(b_pre_h1.get(s, [])) >= 5 and len(b_pre_h2.get(s, [])) >= 5 for s in qualifying):
        X1 = np.stack([concept_vec(s, b_pre_h1) for s in qualifying]).astype(np.float64)
        X2 = np.stack([concept_vec(s, b_pre_h2) for s in qualifying]).astype(np.float64)
        null_rv = rv_coefficient(X1, X2)
        log(f"R4: within-condition null RV (pre_h1 vs pre_h2) = {null_rv}")
    else:
        log("R4: null RV underpowered -- not all 20 signatures have >=5 members in both pre-halves")

    return {
        "n_qualifying_concepts": len(qualifying),
        "qualifying_signatures": [list(s) for s in qualifying],
        "rv_coefficient": rv,
        "procrustes_disparity": disparity,
        "null_rv_pre_h1_vs_pre_h2": null_rv,
    }


# ---------------------------------------------------------------------------
# D1 -- log-based coarse-state transition statistics
# ---------------------------------------------------------------------------

LOGGER_RE = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ \[([\w.]+)\]")


def scan_log_buckets(log_path: str, windows: dict):
    """One full pass over the log, bucketing (state, is_model_client_error) into every named
    [lo_iso, hi_iso) window it falls into. `windows` = {name: (lo_iso, hi_iso)}.

    Deliberately NEVER breaks early: this file contains multi-line log messages (dialogue/content
    with literal embedded newlines), so a naive line-iterator sees phantom "lines" whose first 19
    chars are arbitrary text, not a timestamp -- an earlier version of this function broke on
    `d >= hi_iso` and such a phantom line (sorting lexicographically after any real date because
    it starts with a letter) caused a silent, badly-wrong early stop. The LOGGER_RE anchor (a real
    `YYYY-MM-DD HH:MM:SS,ddd [logger]` prefix) already rejects phantom lines before any date
    comparison happens, so a plain unconditional per-line range check (continue, never break) is
    both correct and the only thing checked against real timestamps.
    """
    out = {name: {"states": [], "mc_total": 0, "mc_err": 0} for name in windows}
    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            m = LOGGER_RE.match(line)
            if not m:
                continue  # phantom continuation line of a multi-line message -- not a real entry
            d, comp = m.group(1), m.group(2)
            is_mc = comp == "nascence.model_client"
            is_err = is_mc and ("JSON parse failed" in line or "salvaged truncated" in line
                                 or "transport error" in line)
            for name, (lo_iso, hi_iso) in windows.items():
                if lo_iso <= d < hi_iso:
                    out[name]["states"].append(comp)
                    if is_mc:
                        out[name]["mc_total"] += 1
                        if is_err:
                            out[name]["mc_err"] += 1
    return out


def transition_matrix(states):
    idx = {s: i for i, s in enumerate(sorted(set(states)))}
    n = len(idx)
    mat = np.zeros((n, n), dtype=np.float64)
    for a, b in zip(states[:-1], states[1:]):
        mat[idx[a], idx[b]] += 1
    row_sums = mat.sum(axis=1, keepdims=True)
    with np.errstate(invalid="ignore", divide="ignore"):
        probs = np.divide(mat, row_sums, out=np.zeros_like(mat), where=row_sums > 0)
    return idx, probs, mat


def mean_row_tvd(idx_a, probs_a, idx_b, probs_b):
    shared = sorted(set(idx_a) & set(idx_b))
    if not shared:
        return None
    tvds = []
    for s in shared:
        ia, ib = idx_a[s], idx_b[s]
        cols_shared = sorted(set(idx_a) & set(idx_b))
        pa = np.array([probs_a[ia, idx_a[c]] for c in cols_shared])
        pb = np.array([probs_b[ib, idx_b[c]] for c in cols_shared])
        tvds.append(0.5 * np.abs(pa - pb).sum())
    return float(np.mean(tvds))


def run_d1(log_path: str):
    def local_iso(epoch):
        return epoch_to_local_iso(epoch)[:19].replace("T", " ")

    pre_lo, pre_hi = local_iso(PRE_LOG_START), local_iso(SWAP_T0)
    post_lo, post_hi = local_iso(SWAP_T0), local_iso(POST_END)
    pre_h1_lo, pre_h1_hi = local_iso(PRE_LOG_START), local_iso(PRE_H_SPLIT)
    pre_h2_lo, pre_h2_hi = local_iso(PRE_H_SPLIT), local_iso(SWAP_T0)
    post_h1_lo, post_h1_hi = local_iso(SWAP_T0), local_iso(POST_H_SPLIT)
    post_h2_lo, post_h2_hi = local_iso(POST_H_SPLIT), local_iso(POST_END)

    windows = {
        "pre": (pre_lo, pre_hi), "post": (post_lo, post_hi),
        "pre_h1": (pre_h1_lo, pre_h1_hi), "pre_h2": (pre_h2_lo, pre_h2_hi),
        "post_h1": (post_h1_lo, post_h1_hi), "post_h2": (post_h2_lo, post_h2_hi),
    }
    log(f"D1: single-pass scanning log for windows: {windows}")
    buckets = scan_log_buckets(log_path, windows)
    for name, b in buckets.items():
        log(f"D1: {name}: n_lines={len(b['states'])} model_client_lines={b['mc_total']} errors={b['mc_err']}")

    idx_pre, probs_pre, _ = transition_matrix(buckets["pre"]["states"])
    idx_post, probs_post, _ = transition_matrix(buckets["post"]["states"])
    vocab_pre, vocab_post = set(idx_pre), set(idx_post)
    tvd = mean_row_tvd(idx_pre, probs_pre, idx_post, probs_post)

    i1, p1, _ = transition_matrix(buckets["pre_h1"]["states"])
    i2, p2, _ = transition_matrix(buckets["pre_h2"]["states"])
    i3, p3, _ = transition_matrix(buckets["post_h1"]["states"])
    i4, p4, _ = transition_matrix(buckets["post_h2"]["states"])

    def mc_rate(b):
        return {"model_client_lines": b["mc_total"], "error_lines": b["mc_err"],
                "error_rate": (b["mc_err"] / b["mc_total"]) if b["mc_total"] else None}

    return {
        "pre_log_window": [pre_lo, pre_hi], "post_log_window": [post_lo, post_hi],
        "n_pre_lines": len(buckets["pre"]["states"]), "n_post_lines": len(buckets["post"]["states"]),
        "vocab_pre_only": sorted(vocab_pre - vocab_post),
        "vocab_post_only": sorted(vocab_post - vocab_pre),
        "vocab_shared": sorted(vocab_pre & vocab_post),
        "mean_row_tvd_shared_states": tvd,
        "null_pre_h1_vs_h2_tvd": mean_row_tvd(i1, p1, i2, p2),
        "null_post_h1_vs_h2_tvd": mean_row_tvd(i3, p3, i4, p4),
        "model_client_error_rate_pre": mc_rate(buckets["pre"]),
        "model_client_error_rate_post": mc_rate(buckets["post"]),
    }


# ---------------------------------------------------------------------------
# D2 -- cue -> neighbourhood reconstruction overlap
# ---------------------------------------------------------------------------

def run_d2(store: Store, n_cues=30, k=10, seed=1411):
    pre_all = [r for r in to_rows(store.fragments_in(store.store_start(), SWAP_T0)) if r["embedding"] is not None]
    post_all = [r for r in to_rows(store.fragments_in(SWAP_T0, POST_END)) if r["embedding"] is not None]
    rng = np.random.default_rng(seed)
    cue_idx = rng.choice(len(pre_all), size=min(n_cues, len(pre_all)), replace=False)

    pre_vecs = np.stack([r["embedding"] for r in pre_all]).astype(np.float32)
    pre_vecs_n = pre_vecs / (np.linalg.norm(pre_vecs, axis=1, keepdims=True) + 1e-12)
    combo = pre_all + post_all
    combo_vecs = np.stack([r["embedding"] for r in combo]).astype(np.float32)
    combo_vecs_n = combo_vecs / (np.linalg.norm(combo_vecs, axis=1, keepdims=True) + 1e-12)

    overlaps = []
    cue_restored_flags = []
    for i in cue_idx:
        cue_vec = pre_vecs_n[i]
        sims_pre = pre_vecs_n @ cue_vec
        sims_pre[i] = -2.0
        top_pre = set(np.argsort(-sims_pre)[:k].tolist())

        sims_combo = combo_vecs_n @ cue_vec
        sims_combo[i] = -2.0  # same index i refers to same fragment since pre_all is a prefix of combo
        top_combo_idx = np.argsort(-sims_combo)[:k].tolist()
        top_combo_ids = {combo[j]["fragment_id"] for j in top_combo_idx}
        top_pre_ids = {pre_all[j]["fragment_id"] for j in top_pre}

        overlap = len(top_pre_ids & top_combo_ids) / k
        overlaps.append(overlap)
        cue_restored_flags.append(pre_all[i]["fragment_id"] in store.restored_ids)

    return {
        "n_cues": len(overlaps), "k": k,
        "mean_overlap": float(np.mean(overlaps)), "median_overlap": float(np.median(overlaps)),
        "min_overlap": float(np.min(overlaps)), "max_overlap": float(np.max(overlaps)),
        "n_cues_from_restored_cohort": int(sum(cue_restored_flags)),
    }


# ---------------------------------------------------------------------------
# D3 -- replay_count vs age
# ---------------------------------------------------------------------------

def run_d3(store: Store):
    snap_t = store.snapshot_time()
    pre_all = to_rows(store.fragments_in(store.store_start(), SWAP_T0))
    post_all = to_rows(store.fragments_in(SWAP_T0, POST_END))

    def analyze(rows, label):
        live = [r for r in rows if r["fragment_id"] not in store.restored_ids]
        restored = [r for r in rows if r["fragment_id"] in store.restored_ids]
        out = {"n_live": len(live), "n_restored": len(restored)}
        if live:
            rc = np.array([r["replay_count"] for r in live], dtype=np.float64)
            age_days = np.array([(snap_t - r["timestamp"]) / 86400 for r in live], dtype=np.float64)
            out["live_replay_mean"] = float(rc.mean())
            out["live_replay_median"] = float(np.median(rc))
            out["live_replay_max"] = float(rc.max())
            out["live_pct_replayed"] = float((rc > 0).mean())
            if rc.std() > 0 and age_days.std() > 0:
                out["live_replay_age_spearman"] = float(
                    np.corrcoef(np.argsort(np.argsort(rc)), np.argsort(np.argsort(age_days)))[0, 1]
                )
                slope = np.polyfit(age_days, rc, 1)[0]
                out["live_replay_age_slope"] = float(slope)
            else:
                out["live_replay_age_spearman"] = None
                out["live_replay_age_slope"] = None
        if restored:
            rc_r = np.array([r["replay_count"] for r in restored], dtype=np.float64)
            out["restored_replay_mean"] = float(rc_r.mean())
            out["restored_replay_median"] = float(np.median(rc_r))
            out["restored_pct_replayed"] = float((rc_r > 0).mean())
        return out

    return {"pre": analyze(pre_all, "pre"), "post": analyze(post_all, "post"),
            "snapshot_time_local": epoch_to_local_iso(snap_t)}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default=None, help="comma list of R1,R2,R3,R4,D1,D2,D3 to run (default all)")
    args = ap.parse_args()

    which = set(args.only.split(",")) if args.only else {"R1", "R2", "R3", "R4", "D1", "D2", "D3"}
    store = Store(args.snapshot)
    results = {
        "generated_at_local": epoch_to_local_iso(time.time()),
        "swap_t0_local": epoch_to_local_iso(SWAP_T0),
        "store_start_local": epoch_to_local_iso(store.store_start()),
        "snapshot_time_local": epoch_to_local_iso(store.snapshot_time()),
    }
    if "R1" in which:
        log("=== R1 ===")
        results["R1"] = run_r1(store)
    if "R2" in which:
        log("=== R2 ===")
        results["R2"] = run_r2(store)
    if "R3" in which:
        log("=== R3 ===")
        results["R3"] = run_r3(store)
    if "R4" in which:
        log("=== R4 ===")
        results["R4"] = run_r4(store)
    if "D1" in which:
        log("=== D1 ===")
        results["D1"] = run_d1(args.log)
    if "D2" in which:
        log("=== D2 ===")
        results["D2"] = run_d2(store)
    if "D3" in which:
        log("=== D3 ===")
        results["D3"] = run_d3(store)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    log(f"wrote {args.out}")


if __name__ == "__main__":
    main()
