"""
AST-1 fixation/bandwidth predictor re-audit (D-0065, 2026-08-29).

Re-runs the same naive-persistence-baseline comparison the 2026-08-20 DEAD verdict used
(docs/reviews/audit_2026-08-20.md, Part 4, line 240), against the 2026-08-29 redesigned
bandwidth predictor (mean-reversion, core/attention_schema_loop.py _BW_WINDOW_K/_BW_REVERSION_GAMMA)
and against the unchanged fixation predictor (persistence).

Methodology: honest one-step walk-forward over the real accrued shadow log
(data/ast_loop_shadow.jsonl), 6 expanding-window folds (same convention as
D-0045/vitality_causal_test.py). The bandwidth predictor's hyperparameters (K=10, gamma=0.5) were
selected on the FIRST 40% of the log only, in a separate calibration pass, and never re-tuned
against this held-out/full-log report -- see core/attention_schema_loop.py module docstring's
2026-08-29 note for the calibration methodology.

Run: python scripts/ast1_reaudit.py
"""
from __future__ import annotations

import json
from pathlib import Path

_LOG = Path(__file__).parent.parent / "data" / "ast_loop_shadow.jsonl"

# must match core/attention_schema_loop.py's shipped constants exactly
K = 10
GAMMA = 0.5
FOLDS = 6
WARM = 5


def load_actuals():
    rows = []
    with open(_LOG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("kind") == "predict":
                rows.append(r)
    rows.sort(key=lambda r: r["ts"])
    return rows


def naive_bw(bw, i):
    return bw[i - 1]


def reversion_bw(bw, i, k=K, gamma=GAMMA):
    lo = max(0, i - k)
    window = bw[lo:i]
    rm = sum(window) / len(window)
    return max(0.1, min(1.0, bw[i - 1] + gamma * (rm - bw[i - 1])))


def naive_fx(fx, i):
    return fx[i - 1]


def informedness(fx, preds_fn, idxs):
    tp = fn = tn = fp = 0
    for i in idxs:
        p, a = preds_fn(fx, i), fx[i]
        if p and a:
            tp += 1
        elif not p and a:
            fn += 1
        elif not p and not a:
            tn += 1
        else:
            fp += 1
    sens = tp / (tp + fn) if (tp + fn) else None
    spec = tn / (tn + fp) if (tn + fp) else None
    inf = round(sens + spec - 1, 4) if sens is not None and spec is not None else None
    return inf, (tp, fn, tn, fp)


def main():
    rows = load_actuals()
    n = len(rows)
    bw = [r["actual"]["bandwidth"] for r in rows]
    fx = [bool(r["actual"]["fixated"]) for r in rows]
    usable = list(range(WARM, n))
    fold_size = len(usable) // FOLDS

    print(f"AST-1 re-audit -- {n} predict rows, {len(usable)} usable one-step predictions\n")

    print("--- BANDWIDTH: mean-reversion (shipped) vs naive persistence, 6-fold expanding-window ---")
    wins = 0
    for f in range(FOLDS):
        idxs = usable[f * fold_size:(f + 1) * fold_size] if f < FOLDS - 1 else usable[f * fold_size:]
        if not idxs:
            continue
        naive_mae = sum(abs(naive_bw(bw, i) - bw[i]) for i in idxs) / len(idxs)
        rev_mae = sum(abs(reversion_bw(bw, i) - bw[i]) for i in idxs) / len(idxs)
        win = rev_mae < naive_mae
        wins += win
        print(f"  fold {f + 1}: n={len(idxs):3d}  naive_MAE={naive_mae:.4f}  reversion_MAE={rev_mae:.4f}  "
              f"{'WIN' if win else 'loss'}")
    print(f"  reversion predictor wins {wins}/{FOLDS} folds\n")

    naive_mae_all = sum(abs(naive_bw(bw, i) - bw[i]) for i in usable) / len(usable)
    rev_mae_all = sum(abs(reversion_bw(bw, i) - bw[i]) for i in usable) / len(usable)
    win_rate_all = sum(1 for i in usable if abs(reversion_bw(bw, i) - bw[i]) < abs(naive_bw(bw, i) - bw[i])) / len(usable)
    print(f"  POOLED: naive_MAE={naive_mae_all:.4f}  reversion_MAE={rev_mae_all:.4f}  "
          f"win_rate={win_rate_all:.3f}  n={len(usable)}")

    print("\n--- FIXATION: persistence (unchanged), 6-fold expanding-window informedness ---")
    for f in range(FOLDS):
        idxs = usable[f * fold_size:(f + 1) * fold_size] if f < FOLDS - 1 else usable[f * fold_size:]
        if not idxs:
            continue
        inf, cm = informedness(fx, naive_fx, idxs)
        print(f"  fold {f + 1}: n={len(idxs):3d}  informedness={inf}  cm(tp,fn,tn,fp)={cm}")

    inf_all, cm_all = informedness(fx, naive_fx, usable)
    print(f"  POOLED: informedness={inf_all}  cm={cm_all}  n={len(usable)}")
    print("\n  Note: fixation predictor == naive persistence by construction (see D-0065 / 08-20 audit note);")
    print("  this number is naive's own score, not evidence of a self-model, and is reported as such.")


if __name__ == "__main__":
    main()
