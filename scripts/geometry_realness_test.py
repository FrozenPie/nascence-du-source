"""
J-0416 (D-0088): sec5.3's felt-response/co-recall realness test for the cross-space edge layer.

WHY THIS INSTRUMENT, NOT ANOTHER MARGINAL-REACH RE-READ (D-0088's own ruling, 2026-08-29): J-0381/
F-0501's 40-example hand-graded read of kill criterion #6 (marginal reach, core/mapping_census.py)
came back a genuinely mixed 20/40 (50%) resonant vs coincidence at scale -- weaker than F-0428's
small-sample 67%. Marginal reach only asks "does geometry surface neighbours plain text-cosine
search would have missed" -- a coverage question. cognitive_geometry.md's own §5.3 asks a DIFFERENT,
harder question that a 50/50 hand-grade of the SAME metric can't settle: "A space is real iff its
internal distances predict something (co-evocation, co-recall, felt response) BETTER than MiniLM
text-distance on the same items." That is a PREDICTIVE test against a real, independent outcome
variable, not a set-overlap test -- a genuinely different instrument, as D-0088 ruled.

THE TWO REAL, INDEPENDENT OUTCOME VARIABLES (both already computed live by Nascence, neither derived
from the candidate geometry-tuple regions):
  (a) FELT RESPONSE = restate_sim from data/train_state_log.jsonl -- cosine(this thought's embedding,
      the IMMEDIATELY PRIOR thought's embedding), i.e. how much the felt/semantic content moved from
      one thought to the next (high = restated/circling, mid = deepened, low = jumped away). This is
      an independent target: it compares THIS item to a DIFFERENT item (its predecessor in the train),
      never the pair of items whose distance is under test.
  (b) CO-RECALL = developed from data/co_recall_ledger.jsonl (the M1 ledger, memory_edges.log_co_recall)
      -- 1 iff the fragments recalled INTO this thought step led to a DEEPENED train (0.40 <= restate_sim
      < 0.82), 0 otherwise (circled or jumped). Literally the plan's own "co-recall" concept: did
      recalling these memories together produce real development. Independent of both the candidate
      geometry regions and of MiniLM text-distance between OTHER items.

THE JOIN (verified empirically before building the test, see docs/lab/ for the join-quality check):
geometry_census.snapshot(source="idle") is called from InnerMonologueNode._log(), which runs in the
same _think() invocation as _log_train_step() (source of train_state_log.jsonl + the co_recall_ledger
row via memory_edges.log_co_recall), on the SAME thought text. Matching on the first 100 chars of
`thought` + nearest ts recovers >11,000 exact matches with ts deltas of a fraction of a second
(median 0.18s) -- unambiguously the same cognitive event, not a coincidental collision.

PRE-REGISTERED VERDICT RULE (stated before reading results):
  For each outcome, predict item i's value from the mean (regression) / majority (classification) of
  its k=10 nearest neighbours under (1) geometry-similarity (core.mapping_census._geometry_similarity,
  the SAME structural metric marginal_reach already uses) and (2) MiniLM text-cosine on the same
  sampled item set -- symmetric methodology to marginal_reach (same k, same seed=42, same MiniLM
  model), but the prediction target is now a REAL held-out outcome, not neighbour-set overlap.
    - GEOMETRY WINS (space is REAL per §5.3) iff geometry's prediction is closer to ground truth than
      text's on both metrics (lower MAE + a paired sign-test favoring geometry at p<0.05, i.e. genuinely
      more often right, not tied noise) for the felt-response test, AND/OR geometry's classification
      accuracy beats text's with a McNemar-style paired advantage for co-recall.
    - TEXT WINS OR TIES (candidate FAILS -- "text wearing a costume") iff geometry does not clear that
      bar on a given outcome.
    - Both outcomes are reported; the plan's own §5.3 language ("co-evocation, co-recall, felt
      response") is disjunctive (predicts ANY of these), so a clear win on either outcome is a clear
      pass for the space; a clear loss on both is a clear fail.

READ-ONLY: reads data/geometry_tuples.jsonl, data/train_state_log.jsonl, data/co_recall_ledger.jsonl.
No DB touched, no store_fragment call, nothing written except this script's own report file --
mirrors core/mapping_census.py's read-only P0 pattern, so no lab_env isolation is needed (nothing
shared-state is written).

Usage: python scripts/geometry_realness_test.py [--sample_n 700] [--k 10] [--seed 42]
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

_DATA = Path(__file__).parent.parent / "data"


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def build_joined_dataset() -> list[dict]:
    """Join geometry_tuples (source=idle) -> train_state_log (restate_sim) -> co_recall_ledger
    (developed, source=monologue), by thought-text prefix + nearest timestamp. Returns one dict per
    successfully-joined event: regions (candidate space coords), thought text, restate_sim (felt
    response), developed (co-recall outcome, None if this step had <2 recalled ids)."""
    from core.mapping_census import extract_regions

    geo_rows = [r for r in _load_jsonl(_DATA / "geometry_tuples.jsonl") if r.get("source") == "idle"]
    train_rows = _load_jsonl(_DATA / "train_state_log.jsonl")
    co_rows = [r for r in _load_jsonl(_DATA / "co_recall_ledger.jsonl") if r.get("source") == "monologue"]

    # index train_state_log by thought[:100] -> list of rows (usually 1, occasionally a few if the
    # same opening 100 chars recurs)
    tidx: dict[str, list[dict]] = defaultdict(list)
    for r in train_rows:
        tidx[(r.get("thought") or "")[:100]].append(r)

    # index co_recall_ledger (monologue source) by rounded ts -> row, for a ts-nearest join to the
    # matched train_state_log row (both written back-to-back in the same _log_train_step() call)
    co_by_round_ts: dict[int, list[dict]] = defaultdict(list)
    for r in co_rows:
        co_by_round_ts[round(r["ts"])].append(r)

    joined = []
    for g in geo_rows:
        key = (g.get("thought") or "")[:100]
        cands = tidx.get(key)
        if not cands:
            continue
        best_train = min(cands, key=lambda r: abs(r["ts"] - g["ts"]))
        if abs(best_train["ts"] - g["ts"]) > 2.0:
            continue  # not the same cognitive event
        restate_sim = best_train.get("restate_sim")
        if restate_sim is None:
            continue

        # find the co_recall_ledger row for the SAME step (written within the same call as
        # best_train, so ts should match within a fraction of a second)
        developed = None
        n_ids = 0
        t = round(best_train["ts"])
        best_co = None
        best_co_diff = None
        for cand_ts in (t - 1, t, t + 1):
            for r in co_by_round_ts.get(cand_ts, []):
                d = abs(r["ts"] - best_train["ts"])
                if best_co_diff is None or d < best_co_diff:
                    best_co, best_co_diff = r, d
        if best_co is not None and best_co_diff is not None and best_co_diff < 1.0:
            developed = best_co.get("developed")
            n_ids = best_co.get("n_ids", 0)

        regions = extract_regions(g)
        joined.append({
            "ts": g["ts"], "thought": g.get("thought") or "", "regions": regions,
            "restate_sim": float(restate_sim), "developed": developed, "n_ids": n_ids,
        })
    return joined


def _knn_indices(sim_matrix, i: int, k: int) -> list[int]:
    import numpy as np
    row = sim_matrix[i].copy()
    row[i] = -1e9
    order = np.argsort(-row)
    return order[:k].tolist()


def run(sample_n: int = 700, k: int = 10, seed: int = 42) -> dict:
    import numpy as np
    from core.mapping_census import _geometry_similarity, SPACES

    joined = build_joined_dataset()
    n_available = len(joined)
    if n_available == 0:
        return {"error": "no joined rows -- join failed"}

    rng = random.Random(seed)
    if n_available > sample_n:
        sample = rng.sample(joined, sample_n)
    else:
        sample = list(joined)
    n = len(sample)

    # ---- embeddings + similarity matrices ----------------------------------------------------
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", device="cpu")
    thoughts = [r["thought"] for r in sample]
    embs = model.encode(thoughts, normalize_embeddings=True, show_progress_bar=False)
    embs = np.asarray(embs, dtype=np.float32)
    text_cos = embs @ embs.T

    regions = [r["regions"] for r in sample]
    geom_sim = np.zeros((n, n), dtype=np.float32)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            geom_sim[i, j] = _geometry_similarity(regions[i], regions[j])

    # ---- outcome 1: felt response (restate_sim, continuous) ----------------------------------
    y_felt = np.array([r["restate_sim"] for r in sample], dtype=np.float32)
    geom_pred, text_pred = np.zeros(n), np.zeros(n)
    for i in range(n):
        g_nb = _knn_indices(geom_sim, i, k)
        t_nb = _knn_indices(text_cos, i, k)
        geom_pred[i] = float(np.mean(y_felt[g_nb]))
        text_pred[i] = float(np.mean(y_felt[t_nb]))

    geom_err = np.abs(geom_pred - y_felt)
    text_err = np.abs(text_pred - y_felt)
    geom_mae, text_mae = float(geom_err.mean()), float(text_err.mean())
    geom_corr = float(np.corrcoef(geom_pred, y_felt)[0, 1])
    text_corr = float(np.corrcoef(text_pred, y_felt)[0, 1])

    # paired sign test: on how many items is geometry strictly closer than text (ties excluded)?
    strictly_better_geom = int(np.sum(geom_err < text_err - 1e-9))
    strictly_better_text = int(np.sum(text_err < geom_err - 1e-9))
    ties = n - strictly_better_geom - strictly_better_text
    p_sign_felt = _binom_two_sided_p(strictly_better_geom, strictly_better_geom + strictly_better_text)

    felt_result = {
        "n": n, "k": k,
        "geom_mae": round(geom_mae, 4), "text_mae": round(text_mae, 4),
        "geom_corr_to_truth": round(geom_corr, 4), "text_corr_to_truth": round(text_corr, 4),
        "n_geom_wins": strictly_better_geom, "n_text_wins": strictly_better_text, "n_ties": ties,
        "sign_test_p": round(p_sign_felt, 5),
        "geom_beats_text": bool(geom_mae < text_mae and geom_corr > text_corr
                                 and strictly_better_geom > strictly_better_text and p_sign_felt < 0.05),
    }

    # ---- outcome 2: co-recall (developed, binary, subset with n_ids>=2 and known label) -------
    co_mask = np.array([(r["developed"] is not None and r["n_ids"] >= 2) for r in sample])
    co_idx = np.where(co_mask)[0]
    co_result: dict = {"n": int(len(co_idx))}
    if len(co_idx) >= 20:
        y_dev = np.array([sample[i]["developed"] for i in co_idx], dtype=np.int32)
        geom_hat, text_hat = np.zeros(len(co_idx), dtype=np.int32), np.zeros(len(co_idx), dtype=np.int32)
        for pos, i in enumerate(co_idx):
            g_nb = _knn_indices(geom_sim, i, k)
            t_nb = _knn_indices(text_cos, i, k)
            # majority vote of ALL n sample items' developed value is undefined for non-labelled
            # neighbours; fall back to the neighbour's own restate_sim-derived label proxy only
            # among neighbours that themselves have a real 'developed' label. Neighbours without a
            # label are skipped (kNN restricted to labelled pool for the vote), matching standard
            # semi-supervised kNN practice.
            g_labels = [y_felt_to_dev(sample[j]) for j in g_nb if sample[j]["developed"] is not None]
            t_labels = [y_felt_to_dev(sample[j]) for j in t_nb if sample[j]["developed"] is not None]
            geom_hat[pos] = _majority(g_labels)
            text_hat[pos] = _majority(t_labels)

        geom_correct = (geom_hat == y_dev)
        text_correct = (text_hat == y_dev)
        geom_acc = float(geom_correct.mean())
        text_acc = float(text_correct.mean())
        # McNemar-style paired counts: geometry-right/text-wrong vs geometry-wrong/text-right
        b = int(np.sum(geom_correct & ~text_correct))   # geom right, text wrong
        c = int(np.sum(~geom_correct & text_correct))   # geom wrong, text right
        p_mcnemar = _binom_two_sided_p(b, b + c)
        co_result.update({
            "k": k, "geom_acc": round(geom_acc, 4), "text_acc": round(text_acc, 4),
            "geom_right_text_wrong": b, "geom_wrong_text_right": c,
            "mcnemar_p": round(p_mcnemar, 5),
            "geom_beats_text": bool(geom_acc > text_acc and b > c and p_mcnemar < 0.05),
        })
    else:
        co_result["note"] = "fewer than 20 labelled co-recall items in sample -- insufficient for a paired test"

    return {
        "n_joined_available": n_available, "sample_n": n, "k": k, "seed": seed,
        "felt_response_test": felt_result,
        "co_recall_test": co_result,
    }


def y_felt_to_dev(row: dict) -> int:
    return int(row["developed"])


def _majority(labels: list[int]) -> int:
    if not labels:
        return 0
    return 1 if sum(labels) * 2 > len(labels) else 0


def _binom_two_sided_p(k_successes: int, n_trials: int, p: float = 0.5) -> float:
    """Exact two-sided binomial test p-value (no scipy dependency), p=0.5 null (coin flip)."""
    if n_trials == 0:
        return 1.0
    import math

    def pmf(k, n, p):
        return math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k))

    center = n_trials * p
    obs_pmf = pmf(k_successes, n_trials, p)
    total = 0.0
    for k in range(n_trials + 1):
        pk = pmf(k, n_trials, p)
        if pk <= obs_pmf * (1 + 1e-9):
            total += pk
    return min(1.0, total)


def run_co_recall_dedicated(cap: int = 1200, k: int = 10, seed: int = 42) -> dict:
    """The co_recall_test embedded in run() draws its labelled subset from whatever a general
    sample_n=700 random draw happens to include (n=69 in the pre-registered run) -- underpowered,
    and 891/1043 (85.4%) of ALL labelled co-recall rows are developed=1, so a lucky majority-class
    guess alone scores ~0.85. This dedicated pass samples DIRECTLY from the full labelled pool (all
    rows with a real 'developed' verdict and n_ids>=2, capped at `cap` for runtime) for a properly
    powered paired comparison, and reports the majority-class baseline explicitly so accuracy numbers
    are read against a real floor, not an implicit one."""
    import numpy as np
    from core.mapping_census import _geometry_similarity

    joined = build_joined_dataset()
    labeled = [r for r in joined if r["developed"] is not None and r["n_ids"] >= 2]
    rng = random.Random(seed)
    sample = rng.sample(labeled, min(cap, len(labeled)))
    n = len(sample)

    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", device="cpu")
    thoughts = [r["thought"] for r in sample]
    embs = model.encode(thoughts, normalize_embeddings=True, show_progress_bar=False)
    embs = np.asarray(embs, dtype=np.float32)
    text_cos = embs @ embs.T

    regions = [r["regions"] for r in sample]
    geom_sim = np.zeros((n, n), dtype=np.float32)
    for i in range(n):
        for j in range(n):
            if i != j:
                geom_sim[i, j] = _geometry_similarity(regions[i], regions[j])

    y_dev = np.array([r["developed"] for r in sample], dtype=np.int32)
    base_rate = float(y_dev.mean())
    majority_baseline_acc = max(base_rate, 1 - base_rate)

    geom_hat, text_hat = np.zeros(n, dtype=np.int32), np.zeros(n, dtype=np.int32)
    for i in range(n):
        g_nb = _knn_indices(geom_sim, i, k)
        t_nb = _knn_indices(text_cos, i, k)
        geom_hat[i] = _majority([int(y_dev[j]) for j in g_nb])
        text_hat[i] = _majority([int(y_dev[j]) for j in t_nb])

    geom_correct = (geom_hat == y_dev)
    text_correct = (text_hat == y_dev)
    b = int(np.sum(geom_correct & ~text_correct))
    c = int(np.sum(~geom_correct & text_correct))
    p_mcnemar = _binom_two_sided_p(b, b + c)
    return {
        "n": n, "k": k, "base_rate_developed": round(base_rate, 4),
        "majority_class_baseline_acc": round(majority_baseline_acc, 4),
        "geom_acc": round(float(geom_correct.mean()), 4), "text_acc": round(float(text_correct.mean()), 4),
        "geom_right_text_wrong": b, "geom_wrong_text_right": c, "ties": n - b - c,
        "mcnemar_p": round(p_mcnemar, 5),
        "geom_beats_text": bool(float(geom_correct.mean()) > float(text_correct.mean()) and b > c and p_mcnemar < 0.05),
        "geom_beats_baseline": bool(float(geom_correct.mean()) > majority_baseline_acc + 0.02),
        "text_beats_baseline": bool(float(text_correct.mean()) > majority_baseline_acc + 0.02),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample_n", type=int, default=700)
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=str, default=None)
    ap.add_argument("--co_recall_dedicated_cap", type=int, default=1200)
    args = ap.parse_args()

    t0 = time.time()
    result = run(sample_n=args.sample_n, k=args.k, seed=args.seed)
    result["co_recall_test_dedicated"] = run_co_recall_dedicated(
        cap=args.co_recall_dedicated_cap, k=args.k, seed=args.seed)
    result["elapsed_s"] = round(time.time() - t0, 1)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    out_path = Path(args.out) if args.out else (
        Path(__file__).parent.parent / "docs" / "lab" / f"geometry_realness_test_{int(time.time())}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n[written] {out_path}")


if __name__ == "__main__":
    main()
