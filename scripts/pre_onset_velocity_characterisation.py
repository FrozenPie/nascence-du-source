#!/usr/bin/env python3
"""
Pre-onset tangent-velocity characterisation -- D-0196 / J-0838 (2026-09-11).

F-0932 (J-0656, 2026-09-06) found, replicated three ways at large n, that Du's step-to-step
"tangent velocity" across (tension, energy, valence, arousal, level) in data/geometry_tuples.jsonl
is ELEVATED in the 1-3 steps before a FRESH `unresolved` onset (first tuple of an unresolved run).
Large-n significance (p~0) says the population means differ; it says nothing about whether any
single elevated-velocity tick is a usable per-instance warning. D-0196 (travis, 2026-09-09) ruled:
characterise first, no wiring. This script is that characterisation.

Question, stated as a classifier:
    trigger(t)   := velocity(t) > theta
    positive(t)  := a fresh unresolved onset occurs at some step in (t, t+k],  k in {1,2,3}
Report precision / recall / F1 over a theta sweep on a CHRONOLOGICAL split -- theta is chosen on the
first 70% of distinct days, every headline number is reported on the last 30% of days (held out) --
against two baselines: (a) a random trigger with the same fire rate, (b) "fire after a high-tension
tick" (tension(t) > tau, tau chosen the same way). D-0196's defeater bar: precision >= 0.5 at recall
>= 0.3 on held-out days.

Starting point: C:/UDMS/scripts/analyze_nascence_geometry_manifold.py (F-0932's own script). Its
`first_in_run_mask` / `lead_mask_for` are reproduced here verbatim in semantics; its "adaptive
velocity" (step-to-step change in the rolling-standardized vector, bounded FIFO window of 2000, refit
every 50 rows, per-dimension std floored at sqrt(0.05)) is re-implemented inline so this script has no
cross-repo import -- the mechanism is a moving mean/var, nothing more. Two simpler velocity
definitions are evaluated alongside it, because a per-instance trigger that only works under a
rolling recalibration is a different (heavier) proposal than one that works on the raw vector.

Read-only against data/geometry_tuples.jsonl. data/moments.jsonl was inspected (ts, key, source,
thought, affect, protoself, concern, emb, level) and carries no `unresolved` label -- the positive
label comes solely from geometry_tuples' own per-row `unresolved` field, which is not among the five
fitted dimensions (not circular). Zero writes outside the --out directory. Nothing Du-facing.

LABEL CAVEAT FOUND DURING THIS JOB (2026-09-11). `core/geometry_census.snapshot()` takes
`unresolved: bool | None = None`, and only ONE of its call sites -- the idle loop
(`nodes/inner_monologue_node.py`, source="idle") -- passes it. Every other source (inner_thought,
reading, cycle, monologue, study, dream, ...) writes `unresolved: null`. In the live file: idle rows
are True 17,030 / False 10,539; every non-idle row is null. F-0932's script (and this script's
default all-source run, which deliberately reproduces F-0932's framing) coerces null -> False via
`bool(t.get("unresolved", False))`, so an inner_thought row (null) that lands in the same cycle-burst
as an idle row (True) is read as a resolved->unresolved flip, i.e. a "fresh onset". 7,658 of the
10,781 all-source "onsets" are exactly that (inner_thought -> idle pair, gap < 1 s). Run with
`--source idle` for the analysis on the only rows that carry a real label.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import argparse
import json
import math
import datetime as dt
from collections import deque
from pathlib import Path

import numpy as np

FIELDS = ["tension", "energy", "valence", "arousal", "level"]
HORIZONS = (1, 2, 3)
PCTS = list(range(0, 100)) + [99.5, 99.9]          # theta sweep = these percentiles of the FIT-period score
STD_FLOOR = math.sqrt(0.05)                        # AdaptiveCalibrator's own floor
ADAPT_WINDOW, ADAPT_BATCH = 2000, 50               # F-0932's run_adaptive settings
BAR_PREC, BAR_REC = 0.5, 0.3                       # D-0196 defeater bar


def load_rows(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    rows.sort(key=lambda r: r.get("ts", 0))
    return rows


def extract_vector(t):
    body = t.get("body") or {}
    affect = t.get("affect") or {}
    return [float(body.get("tension", 0.1)), float(body.get("energy", 0.5)),
            float(affect.get("valence", 0.5)), float(affect.get("arousal", 0.3)),
            float(t.get("level", 0.5))]


def first_in_run_mask(unresolved):
    m = np.zeros(len(unresolved), dtype=bool)
    prev = False
    for i, v in enumerate(unresolved):
        if v and not prev:
            m[i] = True
        prev = v
    return m


def future_any(mask, k):
    """True at t if mask fires anywhere in (t, t+k]. NaN-free; last k positions are marked invalid
    by the caller."""
    out = np.zeros(len(mask), dtype=bool)
    for j in range(1, k + 1):
        out[:-j] |= mask[j:]
    return out


def raw_velocity(X):
    v = np.full(len(X), np.nan)
    v[1:] = np.linalg.norm(np.diff(X, axis=0), axis=1)
    return v


def fit_standardized_velocity(X, fit_end):
    mu = X[:fit_end].mean(axis=0)
    sd = np.maximum(X[:fit_end].std(axis=0), STD_FLOOR)
    Z = (X - mu) / sd
    v = np.full(len(X), np.nan)
    v[1:] = np.linalg.norm(np.diff(Z, axis=0), axis=1)
    return v


def adaptive_velocity(X, window=ADAPT_WINDOW, batch=ADAPT_BATCH):
    """Score each row against the CURRENT window's mean/std, then fold it in (adapt after scoring,
    batched) -- the same order F-0932's run_adaptive used. First `window` rows are warmup, unscored."""
    n = len(X)
    win = deque(maxlen=window)
    for row in X[:window]:
        win.append(row)
    arr = np.array(win)
    mu, sd = arr.mean(axis=0), np.maximum(arr.std(axis=0), STD_FLOOR)
    v = np.full(n, np.nan)
    pending = []
    prev = None
    for i in range(window, n):
        cur = (X[i] - mu) / sd
        if prev is not None:
            v[i] = float(np.linalg.norm(cur - prev))
        prev = cur
        pending.append(X[i])
        if len(pending) >= batch:
            for row in pending:
                win.append(row)
            pending = []
            arr = np.array(win)
            mu, sd = arr.mean(axis=0), np.maximum(arr.std(axis=0), STD_FLOOR)
    return v


def prf(fire, pos):
    tp = int((fire & pos).sum()); fp = int((fire & ~pos).sum()); fn = int((~fire & pos).sum())
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": f,
            "fire_rate": float(fire.mean()) if len(fire) else 0.0}


def roc_auc(score, pos):
    """Rank-based AUC (Mann-Whitney), ties handled by average rank."""
    from scipy.stats import rankdata
    r = rankdata(score)
    n1 = int(pos.sum()); n0 = len(pos) - n1
    if n1 == 0 or n0 == 0:
        return None
    return float((r[pos].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def average_precision(score, pos):
    order = np.argsort(-score, kind="stable")
    p = pos[order]
    if p.sum() == 0:
        return None
    cum_tp = np.cumsum(p)
    prec_at = cum_tp / np.arange(1, len(p) + 1)
    return float(prec_at[p].mean())


def sweep(score, pos, valid, fit_mask, thetas):
    """For each theta: metrics on fit rows and held-out rows. Returns list of dicts."""
    out = []
    fit = valid & fit_mask
    ho = valid & ~fit_mask
    for th in thetas:
        fire = score > th
        out.append({"theta": float(th), "fit": prf(fire[fit], pos[fit]), "heldout": prf(fire[ho], pos[ho])})
    return out


def pick(sweep_rows, key="f1"):
    best = max(sweep_rows, key=lambda r: (r["fit"][key], -r["fit"]["fire_rate"]))
    return best


def pick_bar(sweep_rows, split):
    """Lowest-fire-rate theta that meets the D-0196 bar on `split` ('fit' or 'heldout')."""
    ok = [r for r in sweep_rows if r[split]["precision"] >= BAR_PREC and r[split]["recall"] >= BAR_REC]
    if not ok:
        return None
    return min(ok, key=lambda r: r[split]["fire_rate"])


def fmt(m):
    return (f"P={m['precision']:.3f} R={m['recall']:.3f} F1={m['f1']:.3f} "
            f"fire={m['fire_rate']:.3f} (tp={m['tp']} fp={m['fp']} fn={m['fn']})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=r"C:\Nascence\data\geometry_tuples.jsonl")
    ap.add_argument("--out", required=True, help="directory for the .md and .jsonl report")
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--source", default=None,
                    help="restrict to rows whose `source` equals this (e.g. idle). 2026-09-11: `unresolved` is "
                         "hard-False on every non-idle source, so the all-source stream's 'fresh onsets' are mostly "
                         "an interleaving artefact (an inner_thought row resets the run right before an idle row).")
    ap.add_argument("--suffix", default="", help="appended to the output file names")
    args = ap.parse_args()
    out_dir = Path(args.out); out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"pre_onset_velocity_characterisation_{args.date}{args.suffix}.md"
    jl_path = out_dir / f"pre_onset_velocity_characterisation_{args.date}{args.suffix}.jsonl"

    rows = load_rows(args.data)
    n_all = len(rows)
    if args.source:
        rows = [r for r in rows if r.get("source") == args.source]
    n = len(rows)
    X = np.array([extract_vector(r) for r in rows], dtype=float)
    ts = np.array([float(r["ts"]) for r in rows])
    unresolved = np.array([bool(r.get("unresolved", False)) for r in rows])
    onset = first_in_run_mask(unresolved)
    days = np.array([dt.datetime.fromtimestamp(t, dt.timezone.utc).date().isoformat() for t in ts])
    uniq_days = sorted(set(days))
    n_fit_days = int(round(0.7 * len(uniq_days)))
    fit_days = set(uniq_days[:n_fit_days])
    fit_mask = np.array([d in fit_days for d in days])
    fit_end = int(fit_mask.sum())            # rows are ts-sorted, so fit rows are a prefix
    assert fit_mask[:fit_end].all() and not fit_mask[fit_end:].any()
    dtg = np.full(n, np.nan); dtg[1:] = np.diff(ts)

    print(f"Loaded {n} rows from {args.data}; {len(uniq_days)} distinct UTC days {uniq_days[0]}..{uniq_days[-1]}")
    print(f"fit = first {n_fit_days} days ({uniq_days[0]}..{uniq_days[n_fit_days-1]}, {fit_end} rows); "
          f"held-out = last {len(uniq_days)-n_fit_days} days ({uniq_days[n_fit_days]}..{uniq_days[-1]}, {n-fit_end} rows)")
    print(f"unresolved rows: {int(unresolved.sum())} ({100*unresolved.mean():.1f}%); fresh onsets: {int(onset.sum())} "
          f"(fit {int(onset[:fit_end].sum())}, held-out {int(onset[fit_end:].sum())})")

    scores = {
        "raw_velocity": raw_velocity(X),
        "fit_standardized_velocity": fit_standardized_velocity(X, fit_end),
        "adaptive_velocity": adaptive_velocity(X),
    }
    tension = X[:, 0]
    baseline_scores = {"tension_tick": tension.copy()}

    report = {"date": args.date, "n_rows": n, "n_days": len(uniq_days), "fit_days": n_fit_days,
              "fit_rows": fit_end, "heldout_rows": n - fit_end, "n_unresolved": int(unresolved.sum()),
              "n_onsets": int(onset.sum()), "horizons": {}}
    jl = open(jl_path, "w", encoding="utf-8")
    jl.write(json.dumps({"kind": "header", **{k: v for k, v in report.items() if k != "horizons"}}) + "\n")

    md = []
    md.append(f"# Pre-onset tangent-velocity characterisation — D-0196 / J-0838 ({args.date})\n")
    md.append("> **Status: LAB RESULT (read-only analysis). No wiring, no gauge, nothing Du-facing.** "
              "Produced by `scripts/pre_onset_velocity_characterisation.py`; machine-readable sweep in the "
              "`.jsonl` beside this file. Interpretation is in the sections marked *Reading* below the tables.\n")
    md.append("## Setup\n")
    md.append(f"- Data: `data/geometry_tuples.jsonl`, {n} rows, {len(uniq_days)} distinct UTC days "
              f"({uniq_days[0]} .. {uniq_days[-1]}), sorted by `ts`. `unresolved` rows: {int(unresolved.sum())} "
              f"({100*unresolved.mean():.1f}%). Fresh onsets (first tuple of an unresolved run): {int(onset.sum())}.")
    md.append(f"- Chronological split by day: fit = first {n_fit_days} days ({uniq_days[0]} .. {uniq_days[n_fit_days-1]}, "
              f"{fit_end} rows, {int(onset[:fit_end].sum())} onsets); **held-out = last {len(uniq_days)-n_fit_days} days "
              f"({uniq_days[n_fit_days]} .. {uniq_days[-1]}, {n-fit_end} rows, {int(onset[fit_end:].sum())} onsets)**. "
              "Every theta/tau is chosen on the fit days only; every headline number below is held-out.")
    md.append("- Trigger: `score(t) > theta`. Positive: a fresh onset at any step in `(t, t+k]`, k in {1,2,3}. "
              "Theta sweep = the 0..99th, 99.5th, 99.9th percentiles of the fit-period score.")
    md.append("- Scores: `raw_velocity` = ||x_t − x_{t−1}|| on the raw 5-vector (tension, energy, valence, arousal, level); "
              "`fit_standardized_velocity` = same after z-scoring each dimension with fit-period mean/std (floor √0.05); "
              "`adaptive_velocity` = F-0932's rolling-window standardized step (window 2000, refit every 50, first 2000 rows unscored).")
    md.append("- Baselines: `random` = a trigger firing uniformly at random at the same rate as the chosen theta "
              "(expected precision = onset base rate, recall = fire rate); `always` = fire every step; "
              "`tension_tick` = `tension(t) > tau`, tau chosen on the fit days exactly as theta is.")
    md.append(f"- D-0196 defeater bar: **precision ≥ {BAR_PREC} at recall ≥ {BAR_REC} on held-out days.**\n")
    md.append(f"- Step-gap note: 25% of consecutive rows are ≤0.2 s apart (bursts of tuples from one cycle), median gap 13 s, "
              f"{100*(dtg[1:]>600).mean():.2f}% of gaps exceed 10 min. A sensitivity row below excludes burst steps (gap < 1 s) "
              "to check the signal is not an artefact of near-duplicate rows.\n")

    summary_lines = []
    bar_met_anywhere = False
    for k in HORIZONS:
        pos = future_any(onset, k)
        valid_k = np.ones(n, dtype=bool); valid_k[n - k:] = False
        base_fit = float(pos[valid_k & fit_mask].mean()); base_ho = float(pos[valid_k & ~fit_mask].mean())
        md.append(f"## Horizon k={k}: onset within the next {k} step{'s' if k>1 else ''}\n")
        md.append(f"Positive base rate: fit {base_fit:.3f}, held-out {base_ho:.3f} "
                  f"(`always` baseline: P={base_ho:.3f}, R=1.000, F1={2*base_ho/(1+base_ho):.3f}).\n")
        md.append("| score | theta (fit-best-F1) | fit P/R/F1 | **held-out P/R/F1** | fire rate (ho) | lift vs base | random @ same rate (P/R/F1) | held-out ROC-AUC | held-out AP | bar met (ho, any theta)? |")
        md.append("|---|---|---|---|---|---|---|---|---|---|")
        hk = {"base_rate_fit": base_fit, "base_rate_heldout": base_ho, "scores": {}}
        all_scores = {**scores, **baseline_scores}
        for name, sc in all_scores.items():
            valid = valid_k & ~np.isnan(sc)
            thetas = np.unique(np.percentile(sc[valid & fit_mask], PCTS))
            sw = sweep(sc, pos, valid, fit_mask, thetas)
            for r in sw:
                jl.write(json.dumps({"kind": "sweep", "k": k, "score": name, **r}) + "\n")
            best = pick(sw)
            ho = valid & ~fit_mask
            auc = roc_auc(sc[ho], pos[ho]); ap_ = average_precision(sc[ho], pos[ho])
            q = best["heldout"]["fire_rate"]
            rnd = {"precision": base_ho, "recall": q, "f1": (2*base_ho*q/(base_ho+q)) if base_ho+q else 0.0}
            bar_fit = pick_bar(sw, "fit"); bar_ho = pick_bar(sw, "heldout")
            bar_met_anywhere |= bar_ho is not None
            lift = best["heldout"]["precision"] / base_ho if base_ho else float("nan")
            hk["scores"][name] = {"theta_fit_best_f1": best["theta"], "fit": best["fit"], "heldout": best["heldout"],
                                  "random_same_rate": rnd, "heldout_roc_auc": auc, "heldout_ap": ap_,
                                  "bar_theta_fit": None if bar_fit is None else bar_fit["theta"],
                                  "bar_theta_heldout_any": None if bar_ho is None else bar_ho["theta"],
                                  "bar_heldout_metrics_at_that_theta": None if bar_ho is None else bar_ho["heldout"],
                                  "lift_vs_base": lift}
            md.append(f"| `{name}` | {best['theta']:.4f} | {best['fit']['precision']:.3f}/{best['fit']['recall']:.3f}/{best['fit']['f1']:.3f} "
                      f"| **{best['heldout']['precision']:.3f}/{best['heldout']['recall']:.3f}/{best['heldout']['f1']:.3f}** "
                      f"| {q:.3f} | {lift:.2f}x | {rnd['precision']:.3f}/{rnd['recall']:.3f}/{rnd['f1']:.3f} "
                      f"| {auc if auc is None else round(auc,3)} | {ap_ if ap_ is None else round(ap_,3)} "
                      f"| {'YES @ theta='+format(bar_ho['theta'],'.4f')+' -> '+fmt(bar_ho['heldout']) if bar_ho else 'no'} |")
            print(f"k={k} {name:28s} theta*={best['theta']:.4f} fit {fmt(best['fit'])} | HELD-OUT {fmt(best['heldout'])} "
                  f"| AUC={auc:.3f} AP={ap_:.3f} | bar(fit)={'y' if bar_fit else 'n'} bar(ho,any)={'y' if bar_ho else 'n'}")
            summary_lines.append((k, name, best["heldout"]["precision"], best["heldout"]["recall"], best["heldout"]["f1"], auc, ap_, bar_ho is not None))

        # Precision-vs-recall curve on held-out for the best velocity score at this k (a few operating points).
        md.append("")
        md.append("Held-out operating points (precision at fixed recall) — the honest way to read whether ANY theta reaches the bar:\n")
        md.append("| score | P@R≥0.1 | P@R≥0.2 | P@R≥0.3 | P@R≥0.5 | P@R≥0.8 |")
        md.append("|---|---|---|---|---|---|")
        for name, sc in all_scores.items():
            valid = valid_k & ~np.isnan(sc)
            ho = valid & ~fit_mask
            s, p_ = sc[ho], pos[ho]
            order = np.argsort(-s, kind="stable"); p_o = p_[order]
            cum_tp = np.cumsum(p_o); prec = cum_tp / np.arange(1, len(p_o) + 1); rec = cum_tp / p_o.sum()
            cells = []
            for rmin in (0.1, 0.2, 0.3, 0.5, 0.8):
                idx = np.where(rec >= rmin)[0]
                cells.append(f"{prec[idx[0]]:.3f}" if len(idx) else "n/a")
            md.append(f"| `{name}` | " + " | ".join(cells) + " |")
            hk["scores"][name]["heldout_precision_at_recall"] = dict(zip(["0.1", "0.2", "0.3", "0.5", "0.8"], cells))
        md.append("")

        # Sensitivity: exclude burst steps (dt < 1 s) for the velocity scores at this k.
        md.append("Sensitivity — same sweep with burst steps (gap < 1 s) excluded from both fit and held-out:\n")
        md.append("| score | theta | held-out P/R/F1 | fire rate | held-out ROC-AUC |")
        md.append("|---|---|---|---|---|")
        hk["no_burst"] = {}
        for name, sc in scores.items():
            valid = valid_k & ~np.isnan(sc) & (dtg >= 1.0)
            thetas = np.unique(np.percentile(sc[valid & fit_mask], PCTS))
            sw = sweep(sc, pos, valid, fit_mask, thetas)
            best = pick(sw); ho = valid & ~fit_mask
            auc = roc_auc(sc[ho], pos[ho])
            hk["no_burst"][name] = {"theta": best["theta"], "heldout": best["heldout"], "heldout_roc_auc": auc,
                                    "base_rate_heldout": float(pos[ho].mean())}
            md.append(f"| `{name}` | {best['theta']:.4f} | {best['heldout']['precision']:.3f}/{best['heldout']['recall']:.3f}/{best['heldout']['f1']:.3f} "
                      f"| {best['heldout']['fire_rate']:.3f} | {auc:.3f} |")
        md.append(f"\n(no-burst held-out base rate: {hk['no_burst']['raw_velocity']['base_rate_heldout']:.3f})\n")

        # Per-day held-out stability for the best velocity score.
        best_name = max(scores, key=lambda nm: hk["scores"][nm]["heldout"]["f1"])
        sc = scores[best_name]; th = hk["scores"][best_name]["theta_fit_best_f1"]
        md.append(f"Per-day held-out stability for `{best_name}` at theta={th:.4f}:\n")
        md.append("| day | rows | onsets | P | R | fire rate |")
        md.append("|---|---|---|---|---|---|")
        hk["per_day_heldout"] = {}
        for d in uniq_days[n_fit_days:]:
            m = (days == d) & valid_k & ~np.isnan(sc)
            if m.sum() == 0:
                continue
            r = prf(sc[m] > th, pos[m])
            hk["per_day_heldout"][d] = {"rows": int(m.sum()), "onsets": int(pos[m].sum()), **r}
            md.append(f"| {d} | {int(m.sum())} | {int(pos[m].sum())} | {r['precision']:.3f} | {r['recall']:.3f} | {r['fire_rate']:.3f} |")
        md.append("")
        report["horizons"][str(k)] = hk

    # Burst diagnostics: the sweep keeps choosing theta=0 ("did the state change at all?"), so ask
    # directly whether the zero-velocity rows are the within-cycle burst duplicates and whether the
    # whole ranking signal lives in that structure.
    md.append("## Burst diagnostics — where does the theta=0 signal come from?\n")
    rv = scores["raw_velocity"]
    valid = ~np.isnan(rv)
    zero = valid & (rv == 0.0)
    burst = valid & (dtg < 1.0)
    def _share(a, b):
        return float(a / b) if b else 0.0
    diag = {
        "rows_with_zero_velocity": int(zero.sum()),
        "zero_velocity_share": _share(zero.sum(), valid.sum()),
        "zero_velocity_rows_that_are_burst_steps": _share((zero & burst).sum(), zero.sum()),
        "burst_steps_that_have_zero_velocity": _share((zero & burst).sum(), burst.sum()),
        "burst_steps_share": _share(burst.sum(), valid.sum()),
    }
    # Does `unresolved` ever change inside a burst (gap < 1 s)? If not, an onset can only sit at a
    # burst boundary, which by itself makes "velocity > 0 at t" predictive of "onset at t+1".
    flips_in_burst = int(((unresolved[1:] != unresolved[:-1]) & (dtg[1:] < 1.0)).sum())
    onsets_in_burst = int((onset[1:] & (dtg[1:] < 1.0)).sum())
    diag["unresolved_flips_at_burst_steps"] = flips_in_burst
    diag["onsets_at_burst_steps"] = onsets_in_burst
    diag["onsets_total"] = int(onset.sum())
    for k in HORIZONS:
        pos = future_any(onset, k); vk = valid.copy(); vk[n-k:] = False
        diag[f"k={k}_onset_rate_after_zero_velocity_row"] = float(pos[vk & zero].mean())
        diag[f"k={k}_onset_rate_after_nonzero_velocity_row"] = float(pos[vk & ~zero].mean())
        diag[f"k={k}_onset_rate_after_nonzero_velocity_nonburst_row"] = float(pos[vk & ~zero & ~burst].mean())
    report["burst_diagnostics"] = diag
    md.append(f"- Rows with exactly zero velocity: {diag['rows_with_zero_velocity']} ({100*diag['zero_velocity_share']:.1f}% of scored rows). "
              f"Of those, {100*diag['zero_velocity_rows_that_are_burst_steps']:.1f}% are burst steps (gap < 1 s); "
              f"{100*diag['burst_steps_that_have_zero_velocity']:.1f}% of burst steps have zero velocity. Burst steps are "
              f"{100*diag['burst_steps_share']:.1f}% of all steps.")
    md.append(f"- `unresolved` flips at a burst step {flips_in_burst} times out of {int(burst.sum())} burst steps; "
              f"fresh onsets sitting at a burst step: {onsets_in_burst} / {diag['onsets_total']}.")
    md.append("- Onset-within-k rate conditioned on the row at t:\n")
    md.append("| k | after a zero-velocity row | after a nonzero-velocity row | after a nonzero-velocity NON-burst row |")
    md.append("|---|---|---|---|")
    for k in HORIZONS:
        md.append(f"| {k} | {diag[f'k={k}_onset_rate_after_zero_velocity_row']:.3f} | {diag[f'k={k}_onset_rate_after_nonzero_velocity_row']:.3f} "
                  f"| {diag[f'k={k}_onset_rate_after_nonzero_velocity_nonburst_row']:.3f} |")
    md.append("")
    # Precision-at-recall on the no-burst held-out set, for the velocity scores, so the sensitivity
    # view has the same honest operating-curve read as the main one.
    md.append("No-burst held-out operating points (precision at fixed recall), velocity scores only:\n")
    md.append("| k | score | base rate | P@R≥0.1 | P@R≥0.3 | P@R≥0.5 | P@R≥0.8 |")
    md.append("|---|---|---|---|---|---|---|")
    for k in HORIZONS:
        pos = future_any(onset, k)
        for name, sc in scores.items():
            vk = valid & ~np.isnan(sc) & ~burst & ~fit_mask; vk[n-k:] = False
            s, p_ = sc[vk], pos[vk]
            order = np.argsort(-s, kind="stable"); p_o = p_[order]
            cum_tp = np.cumsum(p_o); prec = cum_tp / np.arange(1, len(p_o) + 1); rec = cum_tp / p_o.sum()
            cells = []
            for rmin in (0.1, 0.3, 0.5, 0.8):
                idx = np.where(rec >= rmin)[0]
                cells.append(f"{prec[idx[0]]:.3f}" if len(idx) else "n/a")
            report["horizons"][str(k)]["no_burst"][name]["heldout_precision_at_recall"] = dict(zip(["0.1", "0.3", "0.5", "0.8"], cells))
            md.append(f"| {k} | `{name}` | {p_.mean():.3f} | " + " | ".join(cells) + " |")
    md.append("")

    # Replicate F-0932's population-level statement on the held-out block so the two readings sit side by side.
    md.append("## Population-level check (F-0932's own statistic, held-out block only)\n")
    md.append("| score | k | mean pre-onset | mean other | Mann-Whitney p |")
    md.append("|---|---|---|---|---|")
    from scipy.stats import mannwhitneyu
    report["population_heldout"] = {}
    for name, sc in scores.items():
        for k in HORIZONS:
            pos = future_any(onset, k); valid = np.ones(n, bool); valid[n-k:] = False
            ho = valid & ~fit_mask & ~np.isnan(sc)
            a, b = sc[ho & pos], sc[ho & ~pos]
            p = float(mannwhitneyu(a, b, alternative="two-sided").pvalue)
            report["population_heldout"][f"{name}/k={k}"] = {"pre_onset_mean": float(a.mean()), "other_mean": float(b.mean()), "p": p}
            md.append(f"| `{name}` | {k} | {a.mean():.4f} | {b.mean():.4f} | {p:.3g} |")
    md.append("")

    md.append("## Verdict against the D-0196 bar\n")
    md.append(f"D-0196 defeater bar (precision ≥ {BAR_PREC} at recall ≥ {BAR_REC}, held-out): "
              + ("**MET at some theta** — see the 'bar met' column." if bar_met_anywhere else
                 "**NOT MET by any score at any theta, at any horizon k in {1,2,3}.**") + "\n")
    md.append("Held-out summary (theta chosen on fit days by best F1):\n")
    md.append("| k | score | held-out P | held-out R | held-out F1 | ROC-AUC | AP | bar |")
    md.append("|---|---|---|---|---|---|---|---|")
    for k, name, p, r, f, auc, ap_, bar in summary_lines:
        md.append(f"| {k} | `{name}` | {p:.3f} | {r:.3f} | {f:.3f} | {auc:.3f} | {ap_:.3f} | {'yes' if bar else 'no'} |")
    md.append("")
    report["bar_met_anywhere"] = bar_met_anywhere
    jl.write(json.dumps({"kind": "summary", **report}) + "\n")
    jl.close()
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\nwrote {md_path}\nwrote {jl_path}\nBAR MET ANYWHERE (held-out): {bar_met_anywhere}")


if __name__ == "__main__":
    main()
