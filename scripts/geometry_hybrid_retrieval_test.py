"""
J-0488 (D-0119): the hybrid-retrieval incremental-value test for the cross-space edge layer.

WHY THIS INSTRUMENT, NOT A FOURTH RE-READ OF THE SAME QUESTION (design note written before running,
J-0488's own briefing): F-0501 (marginal reach), F-0635 (realness test), and F-0651 (co-evocation) all
asked variants of "does geometry-distance ALONE do something text-distance ALONE doesn't" -- a
horse-race framing. All three read as: the underlying geometric coherence is real (F-0651 PASS) but a
standalone geometry-distance signal does not out-predict text-distance on real outcomes (F-0635 clean
FAIL) or reach much beyond a widened text search (F-0501, 50/50 mixed). No prior instrument asked the
one question a horse race structurally cannot answer: does geometry carry ANY information text does
not already carry, such that COMBINING the two beats text ALONE? Two signals can each individually be
weaker than a third and still be worth combining if their errors are not perfectly correlated -- this
is the actual "genuine architectural angle" the founder's D-0119 ruling asked this job to look for
before concluding no such angle exists. It corresponds to a real, standard architectural pattern
(hybrid/re-ranked retrieval: combine a dense semantic score with an auxiliary structural score) rather
than the "replace text search with geometry search" framing every prior instrument tested.

A DIAGNOSTIC HINT THIS IS WORTH TESTING, NOT A GUESS: re-reading F-0635's own raw JSON
(docs/lab/geometry_realness_test_1788309006.json) before writing this script: on the FELT-RESPONSE
outcome, geometry and text kNN predictions disagree on which is closer to truth in a near-coin-flip
way (339 geom-wins / 361 text-wins / sign-test p=0.427 -- NOT significant, i.e. genuinely
undifferentiated at the item level) even though geometry's raw correlation-to-truth is much weaker
(0.121 vs 0.349). That specific pattern -- weak alone, but not one-sidedly wrong the way co-recall's
53-vs-8 pattern is -- is exactly the signature an ensemble COULD exploit if geometry's errors are
even partly orthogonal to text's. On CO-RECALL, by contrast, the dedicated pass's own disagreement
pattern (geom_right_text_wrong=8 vs geom_wrong_text_right=53, mcnemar p=0.0 -- geometry is wrong far
more than it's uniquely right) argues the opposite: this looks like real inferiority, not
complementarity. Both readings come from data already collected; no new instrumentation was needed to
notice this.

PRE-REGISTERED DESIGN (written before this script's own results are read):
  - Same joined dataset (build_joined_dataset from scripts/geometry_realness_test.py), same sample_n,
    seed, k=10, same MiniLM model and _geometry_similarity metric as F-0635 -- only the combination
    step is new, so any effect found is attributable to hybridization, not a re-tuned instrument.
  - PRIMARY test: felt response (restate_sim) only. Co-recall is run as a DIAGNOSTIC-ONLY secondary
    check (does not gate the verdict) given the disagreement-pattern argument above -- pre-registered
    NOT to gate on it, so a negative co-recall result cannot be used post-hoc to claim the whole
    angle is dead, and a positive one cannot be used post-hoc to claim it beyond what felt-response
    alone earns.
  - Hybrid similarity: sim(i,j) = text_cos(i,j) + lambda * geom_sim(i,j), lambda in the pre-registered
    grid {0, 0.1, 0.25, 0.5, 1.0, 2.0, 4.0}. lambda=0 IS the text-only baseline (identical to F-0635's
    text arm, structurally, up to random-split noise) -- not a separate control run.
  - Nested train(70%)/val(15%)/test(15%) split, seeded. For every item in val/test, its k=10 nearest
    neighbours are drawn from TRAIN ONLY (never from val or test) -- avoids the leakage a same-pool kNN
    horse race doesn't have to worry about but a genuine held-out generalization claim does.
  - lambda* is selected on VAL ONLY (argmax correlation-to-truth, ties broken by lower MAE), then
    lambda* and lambda=0 are BOTH evaluated on the untouched TEST split and reported side by side.
  - VERDICT RULE (fixed before reading results): PASS ("a genuine architectural angle exists") iff
    lambda* != 0 on the validation selection AND, on the held-out test split, lambda*'s correlation-to-
    truth beats lambda=0's by >= 0.02 AND lambda*'s MAE is not worse. FAIL otherwise -- including the
    case lambda*==0 (validation itself found no benefit to hybridizing) or the test-set gain washes out
    below the pre-registered margin. A FAIL here, on the one outcome variable and the one disagreement
    pattern that gave this angle its best prior, is real evidence closing the door, not another
    horse-race re-read of the same question.

READ-ONLY: reads data/geometry_tuples.jsonl, data/train_state_log.jsonl, data/co_recall_ledger.jsonl
via scripts/geometry_realness_test.build_joined_dataset(). No store written except this script's own
report file.

Usage: python scripts/geometry_hybrid_retrieval_test.py [--sample_n 700] [--k 10] [--seed 42]
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.geometry_realness_test import build_joined_dataset, _binom_two_sided_p, _majority

LAMBDA_GRID = [0.0, 0.1, 0.25, 0.5, 1.0, 2.0, 4.0]


def _knn_from_pool(sim_row_subset, pool_idx: list[int], k: int) -> list[int]:
    """sim_row_subset: dict mapping pool index -> similarity. Returns the k pool indices with highest
    similarity (pool_idx already excludes the query itself by construction)."""
    ordered = sorted(pool_idx, key=lambda j: -sim_row_subset[j])
    return ordered[:k]


def run(sample_n: int = 700, k: int = 10, seed: int = 42) -> dict:
    import numpy as np
    from core.mapping_census import _geometry_similarity

    joined = build_joined_dataset()
    n_available = len(joined)
    if n_available == 0:
        return {"error": "no joined rows -- join failed"}

    rng = random.Random(seed)
    sample = rng.sample(joined, sample_n) if n_available > sample_n else list(joined)
    n = len(sample)

    # ---- embeddings + similarity matrices (identical methodology to F-0635) -------------------
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

    y_felt = np.array([r["restate_sim"] for r in sample], dtype=np.float32)

    # ---- nested train/val/test split (70/15/15, seeded) ----------------------------------------
    idx = list(range(n))
    rng2 = random.Random(seed + 1)
    rng2.shuffle(idx)
    n_train = int(round(n * 0.70))
    n_val = int(round(n * 0.15))
    train_idx = idx[:n_train]
    val_idx = idx[n_train:n_train + n_val]
    test_idx = idx[n_train + n_val:]

    def eval_lambda(lam: float, query_idx: list[int]) -> dict:
        preds, truths = [], []
        for i in query_idx:
            hybrid = {j: float(text_cos[i, j] + lam * geom_sim[i, j]) for j in train_idx}
            nb = _knn_from_pool(hybrid, train_idx, k)
            preds.append(float(np.mean(y_felt[nb])))
            truths.append(float(y_felt[i]))
        preds = np.array(preds)
        truths = np.array(truths)
        mae = float(np.mean(np.abs(preds - truths)))
        corr = float(np.corrcoef(preds, truths)[0, 1]) if len(set(preds.tolist())) > 1 else 0.0
        return {"mae": round(mae, 4), "corr": round(corr, 4), "n": len(query_idx)}

    # ---- select lambda* on VAL only --------------------------------------------------------
    val_scores = {lam: eval_lambda(lam, val_idx) for lam in LAMBDA_GRID}
    lam_star = max(LAMBDA_GRID, key=lambda lam: (val_scores[lam]["corr"], -val_scores[lam]["mae"]))

    # ---- evaluate lambda=0 (text-only baseline) and lambda* on the untouched TEST split -------
    test_baseline = eval_lambda(0.0, test_idx)
    test_star = eval_lambda(lam_star, test_idx)

    corr_gain = round(test_star["corr"] - test_baseline["corr"], 4)
    mae_delta = round(test_star["mae"] - test_baseline["mae"], 4)  # negative = improvement
    verdict_pass = bool(lam_star != 0.0 and corr_gain >= 0.02 and mae_delta <= 0.0)

    primary = {
        "n_total": n, "k": k, "seed": seed,
        "split": {"train": len(train_idx), "val": len(val_idx), "test": len(test_idx)},
        "lambda_grid": LAMBDA_GRID,
        "val_scores_by_lambda": {str(lam): val_scores[lam] for lam in LAMBDA_GRID},
        "lambda_star": lam_star,
        "test_lambda0_baseline": test_baseline,
        "test_lambda_star": test_star,
        "corr_gain_test": corr_gain,
        "mae_delta_test": mae_delta,
        "verdict_pass": verdict_pass,
    }

    # ---- diagnostic-only secondary check: co-recall, dedicated labelled pool -------------------
    diagnostic = run_co_recall_diagnostic(joined, k=k, seed=seed)

    return {
        "n_joined_available": n_available,
        "primary_felt_response_hybrid_test": primary,
        "diagnostic_co_recall_hybrid_test": diagnostic,
        "verdict_pass_primary": verdict_pass,
    }


def run_co_recall_diagnostic(joined: list[dict], k: int = 10, seed: int = 42, cap: int = 1200) -> dict:
    """Diagnostic-only (does not gate the verdict, per this script's own pre-registration above).
    Mirrors F-0635's run_co_recall_dedicated but with the same hybrid-similarity + held-out-neighbour-
    pool design as the primary test, on the dedicated labelled co-recall pool."""
    import numpy as np
    from core.mapping_census import _geometry_similarity

    labeled = [r for r in joined if r["developed"] is not None and r["n_ids"] >= 2]
    rng = random.Random(seed)
    sample = rng.sample(labeled, min(cap, len(labeled)))
    n = len(sample)
    if n < 40:
        return {"note": "fewer than 40 labelled co-recall items -- insufficient for a held-out split", "n": n}

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

    idx = list(range(n))
    rng2 = random.Random(seed + 1)
    rng2.shuffle(idx)
    n_train = int(round(n * 0.70))
    n_val = int(round(n * 0.15))
    train_idx = idx[:n_train]
    val_idx = idx[n_train:n_train + n_val]
    test_idx = idx[n_train + n_val:]

    def eval_lambda_clf(lam: float, query_idx: list[int]) -> dict:
        correct = 0
        for i in query_idx:
            hybrid = {j: float(text_cos[i, j] + lam * geom_sim[i, j]) for j in train_idx}
            nb = _knn_from_pool(hybrid, train_idx, k)
            hat = _majority([int(y_dev[j]) for j in nb])
            correct += int(hat == y_dev[i])
        return {"acc": round(correct / len(query_idx), 4), "n": len(query_idx)}

    val_scores = {lam: eval_lambda_clf(lam, val_idx) for lam in LAMBDA_GRID}
    lam_star = max(LAMBDA_GRID, key=lambda lam: val_scores[lam]["acc"])
    test_baseline = eval_lambda_clf(0.0, test_idx)
    test_star = eval_lambda_clf(lam_star, test_idx)

    return {
        "n": n, "k": k, "base_rate_developed": round(base_rate, 4),
        "majority_class_baseline_acc": round(majority_baseline_acc, 4),
        "split": {"train": len(train_idx), "val": len(val_idx), "test": len(test_idx)},
        "val_scores_by_lambda": {str(lam): val_scores[lam] for lam in LAMBDA_GRID},
        "lambda_star": lam_star,
        "test_lambda0_baseline": test_baseline,
        "test_lambda_star": test_star,
        "acc_gain_test": round(test_star["acc"] - test_baseline["acc"], 4),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample_n", type=int, default=700)
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=str, default=None)
    args = ap.parse_args()

    t0 = time.time()
    result = run(sample_n=args.sample_n, k=args.k, seed=args.seed)
    result["elapsed_s"] = round(time.time() - t0, 1)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    out_path = Path(args.out) if args.out else (
        Path(__file__).parent.parent / "docs" / "lab" / f"geometry_hybrid_retrieval_test_{int(time.time())}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n[written] {out_path}")


if __name__ == "__main__":
    main()
