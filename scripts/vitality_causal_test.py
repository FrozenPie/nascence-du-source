"""
J-0239: causal-substrate vitality predictor vs naive persistence, walk-forward.

Predictor design (per F-0296 / job briefing):
  forecast P forward via naive persistence (last known real P value strictly before the
  forecast-making tick), then apply the KNOWN day/night threshold schedule analytically
  (world_clock.daylight(t) at the FUTURE tick's own timestamp -- deterministic, known in
  advance) to get predicted vitality = clip01(1 - P_hat / threshold_hat).

Baseline: naive persistence on the vitality scalar itself (predicted(i) = actual(i-1)),
matching exactly how core/homeostasis.py tick() computes naive_err.

Methodology: 6 expanding-window walk-forward folds over homeostasis_shadow.jsonl's rows
(ordered by ts). Both predictors are parameter-free / analytic (no fitting), so "training"
only matters for the causal predictor's own causality constraint (P_hat may only use P data
with ts <= the previous row's ts, never look ahead). Win = causal beats naive_err (lower mean
abs error) in a clear majority of folds.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import world_clock as wc  # noqa: E402

ROOT = Path(r"C:\Nascence")
SHADOW = ROOT / "data" / "homeostasis_shadow.jsonl"
SP_LOG = ROOT / "data" / "sleep_pressure_log.jsonl"

NIGHT_THRESHOLD = 10.0
DAY_THRESHOLD = 100.0


def clip01(x):
    return max(0.0, min(1.0, x))


def load_jsonl(path):
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", type=float, default=None,
                     help="only use shadow rows with ts >= this epoch (restrict to current-formula era)")
    args = ap.parse_args()

    shadow_raw = load_jsonl(SHADOW)
    shadow = [r for r in shadow_raw if "vitality" in (r.get("variables") or {})]
    shadow.sort(key=lambda r: r["ts"])
    if args.since:
        shadow = [r for r in shadow if r["ts"] >= args.since]
    print(f"homeostasis_shadow.jsonl: {len(shadow_raw)} rows total, {len(shadow)} with vitality"
          f"{' (restricted to ts>=%.0f)' % args.since if args.since else ''}, "
          f"span {shadow[0]['ts']:.0f} -> {shadow[-1]['ts']:.0f}")

    sp_rows = load_jsonl(SP_LOG)
    sp_rows = [r for r in sp_rows if "P" in r and "ts" in r]
    sp_rows.sort(key=lambda r: r["ts"])
    sp_ts = [r["ts"] for r in sp_rows]
    sp_P = [float(r["P"]) for r in sp_rows]
    print(f"sleep_pressure_log.jsonl: {len(sp_rows)} usable rows, span {sp_ts[0]:.0f} -> {sp_ts[-1]:.0f}")

    import bisect

    def p_hat_at_or_before(ts_cutoff):
        """Last known real P value with ts <= ts_cutoff (causal: forecast-making-time snapshot)."""
        idx = bisect.bisect_right(sp_ts, ts_cutoff) - 1
        if idx < 0:
            return None
        return sp_P[idx]

    # per-row: naive_err (vitality persistence) and causal_err (substrate predictor)
    results = []  # (ts, naive_err, causal_err)
    skipped_no_prior_p = 0
    for i in range(1, len(shadow)):
        prev = shadow[i - 1]
        cur = shadow[i]
        actual = float(cur["variables"]["vitality"])
        prev_actual = float(prev["variables"]["vitality"])
        naive_pred = prev_actual
        naive_err = abs(actual - naive_pred)

        # causal predictor: forecast made AT prev's ts, for the future time cur['ts']
        p_hat = p_hat_at_or_before(prev["ts"])
        if p_hat is None:
            skipped_no_prior_p += 1
            continue
        dark = wc.daylight(cur["ts"]) == "night"
        thr_hat = NIGHT_THRESHOLD if dark else DAY_THRESHOLD
        causal_pred = clip01(1.0 - p_hat / max(1.0, thr_hat))
        causal_err = abs(actual - causal_pred)

        results.append((cur["ts"], naive_err, causal_err))

    print(f"\nusable one-step-ahead vitality predictions: {len(results)} "
          f"(skipped {skipped_no_prior_p} with no prior P data)")

    # overall
    n = len(results)
    mean_naive = sum(r[1] for r in results) / n
    mean_causal = sum(r[2] for r in results) / n
    win_rows = sum(1 for r in results if r[2] < r[1])
    print(f"\n=== OVERALL (all {n} rows pooled) ===")
    print(f"naive_err  mean MAE: {mean_naive:.5f}")
    print(f"causal_err mean MAE: {mean_causal:.5f}")
    print(f"row-level win rate (causal_err < naive_err): {win_rows}/{n} = {win_rows/n:.3f}")
    print(f"causal beats naive on POOLED mean: {mean_causal < mean_naive}")

    # 6 expanding-window walk-forward folds
    NFOLDS = 6
    fold_bounds = [round(i * n / NFOLDS) for i in range(NFOLDS + 1)]
    print(f"\n=== 6 EXPANDING-WINDOW WALK-FORWARD FOLDS ===")
    print("(fold k test-window = rows[bounds[k]:bounds[k+1]]; both predictors are analytic/"
          "parameter-free so 'expanding train window' only gates causality, not fitting)")
    fold_wins = 0
    for k in range(NFOLDS):
        lo, hi = fold_bounds[k], fold_bounds[k + 1]
        test = results[lo:hi]
        if not test:
            continue
        m_naive = sum(r[1] for r in test) / len(test)
        m_causal = sum(r[2] for r in test) / len(test)
        win = m_causal < m_naive
        fold_wins += int(win)
        t0, t1 = test[0][0], test[-1][0]
        print(f"  fold {k+1}: n={len(test):4d}  naive={m_naive:.5f}  causal={m_causal:.5f}  "
              f"{'CAUSAL WINS' if win else 'naive wins'}   ts[{t0:.0f}..{t1:.0f}]")
    print(f"\nfold win count: {fold_wins}/{NFOLDS}")
    print(f"clear majority (>=4/6) win for causal predictor: {fold_wins >= 4}")


if __name__ == "__main__":
    main()
