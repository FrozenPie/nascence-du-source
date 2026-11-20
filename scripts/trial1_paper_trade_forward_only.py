#!/usr/bin/env python3
"""
Trial 1 (udms_du_capability_trials.md) -- forward-only paper-trade of the PCA-residual
stall early-warning on post-D-0057 LLM telemetry.  READ-ONLY against data/llm_latency.jsonl;
writes one JSON ledger under data/viability_validation/.  Never touches Du.

Method (the same one J-0317 / F-0523 used, reproduced here so the next re-check reuses a
script instead of re-deriving it from memory):
  * records filtered to ts >= --cutoff (D-0057 ruling epoch by default)
  * features per step: [latency, rolling_mean_10, rolling_std_10, delta_latency]
    (identical to C:/UDMS/scripts/nascence_leftovers_2026-08-27/test_ce_*.py)
  * stall := ok == 0 OR latency > 15s (the UDMS script's definition, kept for comparability)
  * standardization + PCA(2) + p95 threshold on NON-STALL steps are fit on the chronological
    PREFIX only (--split fraction); the SUFFIX is evaluated forward only.
  * cascade-decontaminated: only clean steps (not a stall, not inside an ongoing cascade) are
    scored; "hit" = a stall occurs within the next h steps.
  * per plan rule 2 (no single-split effect sizes): a bootstrap 95% CI on the h=1 lift over
    eval clean steps, plus split-fraction sensitivity, are reported next to the point estimate.

Runs: pooled (all post-cutoff models), new-fabric pooled (--fabric models only), and per-model
forward-only for each fabric model with >= --min-events post-cutoff events.

Usage:
  python -X utf8 scripts/trial1_paper_trade_forward_only.py --tag J-0529
"""
import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT_DIR = DATA / "viability_validation"

D0057_EPOCH = 1787863328.0
HORIZONS = [1, 3, 5, 10]
WINDOW = 10
FABRIC = ["command-r7b", "mixtral:8x7b", "granite3.1-moe:3b"]


def load(path, cutoff):
    recs, bad = [], 0
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            try:
                d = json.loads(line)
            except Exception:
                bad += 1
                continue
            ts = float(d.get("ts", 0) or 0)
            if ts < cutoff:
                continue
            s = float(d.get("s", 0.0) or 0.0)
            ok = int(d.get("ok", 1))
            recs.append({"ts": ts, "s": s, "ok": ok, "model": str(d.get("model", "unknown")),
                         "stall": 1 if (ok == 0 or s > 15.0) else 0})
    recs.sort(key=lambda r: r["ts"])
    return recs, bad


def features(lats):
    X = []
    for i in range(len(lats)):
        hist = lats[max(0, i - WINDOW):i + 1]
        mu = float(np.mean(hist))
        sd = float(np.std(hist)) if len(hist) > 1 else 0.05
        dl = (lats[i] - lats[i - 1]) if i > 0 else 0.0
        X.append([lats[i], mu, sd, dl])
    return np.array(X, dtype=float)


def cascade_mask(stalls):
    n = len(stalls)
    in_c = [False] * n
    onsets = 0
    for i in range(n):
        if stalls[i] == 1:
            if i == 0 or stalls[i - 1] == 0:
                onsets += 1
            else:
                in_c[i] = True
    return in_c, onsets


def horizon_eval(stalls, warnings, in_c, start, h):
    n = len(stalls)
    wh = wt = nh = nt = 0
    for t in range(start, n - h):
        if in_c[t] or stalls[t] == 1:
            continue
        fut = any(stalls[t + 1:t + h + 1])
        if warnings[t]:
            wt += 1
            wh += fut
        else:
            nt += 1
            nh += fut
    pw = wh / wt * 100 if wt else 0.0
    pn = nh / nt * 100 if nt else 0.0
    lift = pw / pn if pn > 0 else 0.0
    return {"p_stall_given_warn": pw, "p_stall_given_nowarn": pn, "lift": lift,
            "warn_hit": wh, "warn_total": wt, "nowarn_hit": nh, "nowarn_total": nt,
            "eval_clean_steps": wt + nt}


def bootstrap_lift_ci(stalls, warnings, in_c, start, h, reps, rng):
    n = len(stalls)
    rows = []
    for t in range(start, n - h):
        if in_c[t] or stalls[t] == 1:
            continue
        rows.append((1 if warnings[t] else 0, 1 if any(stalls[t + 1:t + h + 1]) else 0))
    if not rows:
        return None
    A = np.array(rows)
    lifts = []
    for _ in range(reps):
        idx = rng.integers(0, len(A), len(A))
        B = A[idx]
        w = B[B[:, 0] == 1]
        nw = B[B[:, 0] == 0]
        if len(w) == 0 or len(nw) == 0:
            continue
        pw = w[:, 1].mean()
        pn = nw[:, 1].mean()
        if pn > 0:
            lifts.append(pw / pn)
    if not lifts:
        return None
    lo, hi = np.percentile(lifts, [2.5, 97.5])
    return {"ci95_lo": float(lo), "ci95_hi": float(hi), "reps_used": len(lifts), "rows": int(len(A))}


def forward_only(recs, split, label, rng, boot_reps=1000, splits_for_sens=(0.5, 0.6, 0.7)):
    n = len(recs)
    lats = [r["s"] for r in recs]
    stalls = [r["stall"] for r in recs]
    models = [r["model"] for r in recs]
    X = features(lats)
    in_c, onsets = cascade_mask(stalls)

    def run_split(frac):
        k = int(n * frac)
        Xp = X[:k]
        sp = np.array(stalls[:k])
        mu = Xp.mean(axis=0)
        sd = np.maximum(Xp.std(axis=0), 1e-4)
        Xs = (X - mu) / sd
        pca = PCA(n_components=2).fit(Xs[:k])
        rec = pca.inverse_transform(pca.transform(Xs))
        d = np.linalg.norm(Xs - rec, axis=1)
        nonstall_prefix = d[:k][sp == 0]
        thr = float(np.percentile(nonstall_prefix, 95.0)) if len(nonstall_prefix) else float("inf")
        warn = d > thr
        return k, thr, warn

    k, thr, warn = run_split(split)
    by_h = {}
    for h in HORIZONS:
        by_h[str(h)] = horizon_eval(stalls, warn, in_c, k, h)
    ci = bootstrap_lift_ci(stalls, warn, in_c, k, 1, boot_reps, rng)
    sens = {}
    for frac in splits_for_sens:
        kk, thr2, warn2 = run_split(frac)
        sens[str(frac)] = {"prefix_n": kk, "threshold": thr2, **horizon_eval(stalls, warn2, in_c, kk, 1)}
    # warnings by model in the eval suffix (clean steps only)
    wbm = Counter()
    for t in range(k, n - 1):
        if warn[t] and not in_c[t] and stalls[t] == 0:
            wbm[models[t]] += 1
    eval_mix = Counter(models[k:])
    eval_stall_by_model = Counter(m for m, s in zip(models[k:], stalls[k:]) if s)
    return {
        "label": label,
        "records": n,
        "span_hours": (recs[-1]["ts"] - recs[0]["ts"]) / 3600 if n > 1 else 0.0,
        "model_mix": dict(Counter(models)),
        "stall_onsets_total": onsets,
        "stalls_total": int(sum(stalls)),
        "split": split,
        "calibration_prefix_n": k,
        "evaluation_suffix_n": n - k,
        "eval_model_mix": dict(eval_mix),
        "eval_stalls_by_model": dict(eval_stall_by_model),
        "threshold": thr,
        "results_by_horizon": by_h,
        "h1_lift_bootstrap": ci,
        "h1_split_sensitivity": sens,
        "eval_warnings_by_model": dict(wbm),
    }


def print_run(r):
    print("=" * 100)
    print(f"[{r['label']}] records={r['records']} span={r['span_hours']:.1f}h prefix={r['calibration_prefix_n']} "
          f"suffix={r['evaluation_suffix_n']} thr={r['threshold']:.4f} stalls={r['stalls_total']} onsets={r['stall_onsets_total']}")
    print(f"  model mix: {r['model_mix']}")
    print(f"  eval-suffix mix: {r['eval_model_mix']}  eval stalls by model: {r['eval_stalls_by_model']}")
    print(f"  {'h':>3} | {'P(stall|warn)':>14} | {'P(stall|nowarn)':>16} | {'lift':>6} | warn hit/total | clean steps")
    for h, v in r["results_by_horizon"].items():
        print(f"  {h:>3} | {v['p_stall_given_warn']:>13.2f}% | {v['p_stall_given_nowarn']:>15.2f}% | {v['lift']:>5.2f}x | "
              f"{v['warn_hit']}/{v['warn_total']:<10} | {v['eval_clean_steps']}")
    ci = r["h1_lift_bootstrap"]
    if ci:
        print(f"  h=1 lift bootstrap 95% CI: [{ci['ci95_lo']:.2f}, {ci['ci95_hi']:.2f}] ({ci['reps_used']} reps, {ci['rows']} rows)")
    print("  h=1 split sensitivity: " + "; ".join(
        f"{fr}: lift {v['lift']:.2f}x ({v['warn_hit']}/{v['warn_total']})" for fr, v in r["h1_split_sensitivity"].items()))
    print(f"  eval warnings by model (clean steps): {r['eval_warnings_by_model']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cutoff", type=float, default=D0057_EPOCH)
    ap.add_argument("--split", type=float, default=0.6)
    ap.add_argument("--tag", default="trial1")
    ap.add_argument("--latency", default=str(DATA / "llm_latency.jsonl"))
    ap.add_argument("--out-dir", default=str(OUT_DIR))
    ap.add_argument("--fabric", default=",".join(FABRIC))
    ap.add_argument("--min-events", type=int, default=200)
    ap.add_argument("--boot-reps", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=20260904)
    a = ap.parse_args()

    rng = np.random.default_rng(a.seed)
    recs, bad = load(a.latency, a.cutoff)
    fabric = [m for m in a.fabric.split(",") if m]
    mix = Counter(r["model"] for r in recs)
    print(f"post-cutoff records={len(recs)} malformed={bad} cutoff={a.cutoff} now={time.time():.0f}")
    print(f"model mix: {dict(mix.most_common())}")
    gate = {m: mix.get(m, 0) for m in fabric}
    print(f"volume gate (>= {a.min_events} per fabric model): {gate} -> {'MET' if all(v >= a.min_events for v in gate.values()) else 'NOT MET'}")

    runs = {}
    runs["pooled_all"] = forward_only(recs, a.split, "pooled_all", rng, a.boot_reps)
    fab_recs = [r for r in recs if r["model"] in fabric]
    if len(fab_recs) > 50:
        runs["pooled_new_fabric"] = forward_only(fab_recs, a.split, "pooled_new_fabric", rng, a.boot_reps)
    for m in fabric:
        mr = [r for r in recs if r["model"] == m]
        if len(mr) >= a.min_events:
            runs[f"model:{m}"] = forward_only(mr, a.split, f"model:{m}", rng, a.boot_reps)
    for r in runs.values():
        print_run(r)

    out = {
        "tag": a.tag,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "latency_file": a.latency,
        "cutoff_epoch": a.cutoff,
        "post_cutoff_records": len(recs),
        "malformed_lines": bad,
        "model_mix_post_cutoff": dict(mix),
        "volume_gate": {"min_events": a.min_events, "counts": gate,
                        "met": all(v >= a.min_events for v in gate.values())},
        "stall_definition": "ok==0 or latency_s>15.0 (UDMS test_ce definition)",
        "helpful_bar": "h1 lift >= 2x with >= 30 warning events on new-fabric-dominated eval data",
        "runs": runs,
    }
    Path(a.out_dir).mkdir(parents=True, exist_ok=True)
    op = Path(a.out_dir) / f"{a.tag}_trial1_paper_trade_forward_only.json"
    with open(op, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"\nwritten: {op}")


if __name__ == "__main__":
    main()
