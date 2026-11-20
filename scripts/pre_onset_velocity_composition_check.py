#!/usr/bin/env python3
"""
J-0838 / D-0196: per-instance characterisation of the pre-onset tangent-velocity signal (F-0932).

Read-only over C:/Nascence/data/geometry_tuples.jsonl (+ a schema check of moments.jsonl).
Writes ONLY to the paths given on the command line (worktree docs/lab/...).

Question: is "velocity > theta at step t" a usable per-instance trigger for "a FRESH unresolved
onset occurs within the next k steps" (k in 1..3)?  Precision / recall / F1 across a theta sweep,
theta fitted on the first 70% of DAYS, reported on the last 30% of DAYS, against baselines.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import json
import datetime as _dt
from pathlib import Path
from collections import Counter

import numpy as np

sys.path.insert(0, r"C:\UDMS")
from core.math.udms_engine import UDMSEngine  # the honest PCA primitive F-0932 used

DATA = Path(r"C:\Nascence\data")
FIELDS = ["tension", "energy", "valence", "arousal", "level"]
DEFAULTS = [0.1, 0.5, 0.5, 0.3, 0.5]      # exactly analyze_nascence_geometry_manifold.extract_vector's fills
SEGMENT_GAP_S = 3600.0                     # a >1h gap breaks the step sequence (velocity undefined across it)
NULL_FIX_TS = _dt.datetime(2026, 8, 29, tzinfo=_dt.timezone.utc).timestamp()  # J-0331/J-0380 null-fill fix date
ADAPT_WINDOW = 2000
KS = (1, 2, 3)
OUT_MD = Path(sys.argv[1])
OUT_JSONL = Path(sys.argv[2])

# ----------------------------------------------------------------------------------------------- load
rows = []
with open(DATA / "geometry_tuples.jsonl", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
rows.sort(key=lambda r: r.get("ts", 0))
n = len(rows)
ts = np.array([r["ts"] for r in rows], float)
src = np.array([r.get("source", "") for r in rows])
unres = np.array([bool(r.get("unresolved", False)) for r in rows])
body_null = np.array([(r.get("body") is None) for r in rows])
aff_null = np.array([(r.get("affect") is None) for r in rows])


def vec(r):
    b = r.get("body") or {}
    a = r.get("affect") or {}
    return [float(b.get("tension", DEFAULTS[0])), float(b.get("energy", DEFAULTS[1])),
            float(a.get("valence", DEFAULTS[2])), float(a.get("arousal", DEFAULTS[3])),
            float(r.get("level", DEFAULTS[4]))]


X = np.array([vec(r) for r in rows], float)
tension = X[:, 0]

# moments.jsonl: schema check only -- does it carry any 'unresolved'-like label?
m_keys = Counter()
m_n = 0
with open(DATA / "moments.jsonl", encoding="utf-8") as f:
    for line in f:
        try:
            r = json.loads(line)
        except Exception:
            continue
        m_n += 1
        m_keys.update(r.keys())

# ----------------------------------------------------------------------------------------------- labels
onset = np.zeros(n, bool)
prev = False
for i, v in enumerate(unres):
    if v and not prev:
        onset[i] = True
    prev = v
dt = np.diff(ts, prepend=ts[0])
seg_start = dt > SEGMENT_GAP_S
seg_id = np.cumsum(seg_start)


def lead_label(target, k):
    """True at t if target fires anywhere in (t, t+k] within the same gap-free segment."""
    m = np.zeros(n, bool)
    for j in range(1, k + 1):
        same = np.zeros(n, bool)
        same[:-j] = seg_id[j:] == seg_id[:-j]
        hit = np.zeros(n, bool)
        hit[:-j] = target[j:]
        m |= same & hit
    return m


Y = {k: lead_label(onset, k) for k in KS}

# ----------------------------------------------------------------------------------------------- split by DAY
day = np.array([_dt.datetime.fromtimestamp(t, _dt.timezone.utc).date().isoformat() for t in ts])
days = sorted(set(day))
n_train_days = int(round(0.7 * len(days)))
train_days = set(days[:n_train_days])
train = np.array([d in train_days for d in day])
test = ~train

# ----------------------------------------------------------------------------------------------- velocities
def step_valid():
    v = np.ones(n, bool)
    v[0] = False
    v[seg_start] = False          # first row after a gap has no within-segment predecessor
    return v


valid = step_valid()

# (1) raw-unit velocity
V_raw = np.full(n, np.nan)
V_raw[1:] = np.linalg.norm(X[1:] - X[:-1], axis=1)
V_raw[~valid] = np.nan

# (2) PCA tangent velocity: UDMSEngine fit on the TRAIN days only, ingested in order over the whole stream
eng = UDMSEngine(tangent_dim=2, normal_dim=3, history_window=30)
eng.fit(X[train])
pca_abstain = bool(eng.is_abstaining)
V_pca = np.full(n, np.nan)
if not pca_abstain:
    Xn = (X - eng.mean) / eng.std
    Z = Xn @ eng.basis[:, :2]
    V_pca[1:] = np.linalg.norm(Z[1:] - Z[:-1], axis=1)
    V_pca[~valid] = np.nan
    _, S, _ = np.linalg.svd((X[train] - eng.mean) / eng.std, full_matrices=False)
    evr = (S ** 2) / (S ** 2).sum()
else:
    evr = None

# (3) adaptive velocity: step difference of the vector standardised by the PREVIOUS `ADAPT_WINDOW` rows'
#     mean/std (std floored at sqrt(0.05), as AdaptiveCalibrator / the F-0932 script do); first window is warm-up only.
V_adapt = np.full(n, np.nan)
cs = np.cumsum(X, axis=0)
cs2 = np.cumsum(X * X, axis=0)
for i in range(ADAPT_WINDOW, n):
    lo = i - ADAPT_WINDOW
    mu = (cs[i - 1] - (cs[lo - 1] if lo > 0 else 0)) / ADAPT_WINDOW
    var = (cs2[i - 1] - (cs2[lo - 1] if lo > 0 else 0)) / ADAPT_WINDOW - mu ** 2
    sd = np.maximum(np.sqrt(np.maximum(var, 0)), np.sqrt(0.05))
    V_adapt[i] = np.linalg.norm((X[i] - mu) / sd - (X[i - 1] - mu) / sd)
V_adapt[~valid] = np.nan

VELS = {"raw": V_raw, "pca_tangent": V_pca, "adaptive": V_adapt}

# ----------------------------------------------------------------------------------------------- metrics
def prf(pred, y, mask):
    p = pred & mask
    tp = int((p & y).sum())
    fp = int((p & ~y).sum())
    fn = int((~p & y & mask).sum())
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": prec, "recall": rec, "f1": f1,
            "fire_rate": float(p.sum() / max(mask.sum(), 1))}


def average_precision(score, y, mask):
    m = mask & ~np.isnan(score)
    s, yy = score[m], y[m]
    if yy.sum() == 0:
        return float("nan")
    o = np.argsort(-s, kind="stable")
    yy = yy[o]
    tp = np.cumsum(yy)
    prec = tp / np.arange(1, len(yy) + 1)
    return float((prec * yy).sum() / yy.sum())


def sweep(score, y, fit_mask, eval_mask, name, direction=">"):
    """Fit theta on fit_mask (max F1, and max precision s.t. recall>=0.3), report on eval_mask."""
    m_fit = fit_mask & ~np.isnan(score)
    m_eval = eval_mask & ~np.isnan(score)
    qs = np.concatenate([np.arange(0, 95, 2.5), np.arange(95, 100, 0.5)])
    thetas = np.unique(np.percentile(score[m_fit], qs))
    table = []
    for th in thetas:
        pred = (score > th) if direction == ">" else (score < th)
        r_fit = prf(pred, y, m_fit)
        r_ev = prf(pred, y, m_eval)
        table.append({"theta": float(th), "train": r_fit, "test": r_ev})
    best_f1 = max(table, key=lambda r: r["train"]["f1"])
    cands = [r for r in table if r["train"]["recall"] >= 0.3]
    best_p = max(cands, key=lambda r: r["train"]["precision"]) if cands else None
    # also the best the TEST set could ever give (oracle theta) -- an upper bound, not an operating point
    oracle = max(table, key=lambda r: r["test"]["f1"])
    return {"name": name, "n_train": int(m_fit.sum()), "n_test": int(m_eval.sum()),
            "base_rate_train": float(y[m_fit].mean()), "base_rate_test": float(y[m_eval].mean()),
            "ap_train": average_precision(score, y, m_fit), "ap_test": average_precision(score, y, m_eval),
            "theta_maxF1_train": best_f1, "theta_maxP_at_R30_train": best_p, "oracle_test_theta": oracle,
            "table": table}


def bool_trigger(pred, y, fit_mask, eval_mask, name):
    return {"name": name, "n_train": int(fit_mask.sum()), "n_test": int(eval_mask.sum()),
            "base_rate_train": float(y[fit_mask].mean()), "base_rate_test": float(y[eval_mask].mean()),
            "train": prf(pred, y, fit_mask), "test": prf(pred, y, eval_mask)}


results = {"n_rows": n, "n_days": len(days), "train_days": [days[0], days[n_train_days - 1]],
           "test_days": [days[n_train_days], days[-1]], "n_train_rows": int(train.sum()),
           "n_test_rows": int(test.sum()), "n_segments": int(seg_id.max() + 1),
           "n_onsets": int(onset.sum()), "n_unresolved": int(unres.sum()),
           "pca_abstain": pca_abstain, "pca_evr": None if evr is None else [round(float(e), 4) for e in evr],
           "moments_rows": m_n, "moments_keys": dict(m_keys),
           "unresolved_by_source": {s: [int((src == s).sum()), float(unres[src == s].mean())]
                                     for s in Counter(src).keys()},
           "body_null_rate_pre_fix": float(body_null[ts < NULL_FIX_TS].mean()),
           "body_null_rate_post_fix": float(body_null[ts >= NULL_FIX_TS].mean()),
           "affect_null_rate_pre_fix": float(aff_null[ts < NULL_FIX_TS].mean()),
           "affect_null_rate_post_fix": float(aff_null[ts >= NULL_FIX_TS].mean()),
           "runs": {}}

# ----------------------------------------------------------------------------------------------- run configurations
idle = src == "idle"
post_fix = ts >= NULL_FIX_TS
switch = np.zeros(n, bool)
switch[1:] = src[1:] != src[:-1]

# velocity at source switches vs within-source (artifact check)
for vn, V in VELS.items():
    ok = ~np.isnan(V)
    results[f"vel_{vn}_at_switch_mean"] = float(V[ok & switch].mean())
    results[f"vel_{vn}_within_source_mean"] = float(V[ok & ~switch].mean())
    results[f"vel_{vn}_prefix_at_switch_mean"] = float(V[ok & switch & ~post_fix].mean())
    results[f"vel_{vn}_postfix_at_switch_mean"] = float(V[ok & switch & post_fix].mean())

configs = {
    "all_rows": np.ones(n, bool),
    "post_null_fix_only": post_fix,
}
# idle-only SUBSEQUENCE: recompute steps/labels over idle rows alone (unresolved exists only there)
idle_idx = np.where(idle)[0]
Xi = X[idle_idx]
tsi = ts[idle_idx]
oni = onset[idle_idx]  # onset as defined on the full stream (first unresolved after any non-unresolved row)
# an idle-only onset: first unresolved idle row after a non-unresolved idle row
uni = unres[idle_idx]
oni2 = np.zeros(len(uni), bool)
pv = False
for i, v in enumerate(uni):
    if v and not pv:
        oni2[i] = True
    pv = v
dti = np.diff(tsi, prepend=tsi[0])
segi = np.cumsum(dti > SEGMENT_GAP_S)
vi = np.ones(len(uni), bool)
vi[0] = False
vi[dti > SEGMENT_GAP_S] = False
Vi_raw = np.full(len(uni), np.nan)
Vi_raw[1:] = np.linalg.norm(Xi[1:] - Xi[:-1], axis=1)
Vi_raw[~vi] = np.nan
Vi_pca = np.full(len(uni), np.nan)
if not pca_abstain:
    Zi = ((Xi - eng.mean) / eng.std) @ eng.basis[:, :2]
    Vi_pca[1:] = np.linalg.norm(Zi[1:] - Zi[:-1], axis=1)
    Vi_pca[~vi] = np.nan


def lead_label_i(target, k):
    m = np.zeros(len(target), bool)
    for j in range(1, k + 1):
        same = np.zeros(len(target), bool)
        same[:-j] = segi[j:] == segi[:-j]
        hit = np.zeros(len(target), bool)
        hit[:-j] = target[j:]
        m |= same & hit
    return m


train_i = train[idle_idx]
test_i = test[idle_idx]

for cname, cmask in configs.items():
    runs = {}
    for k in KS:
        y = Y[k]
        fit = train & cmask
        ev = test & cmask
        entry = {"base_rate_train": float(y[fit].mean()), "base_rate_test": float(y[ev].mean())}
        for vn, V in VELS.items():
            entry[f"vel_{vn}"] = sweep(V, y, fit, ev, f"velocity_{vn}")
        entry["baseline_high_tension"] = sweep(tension, y, fit, ev, "high_tension_tick")
        entry["baseline_always_fire"] = bool_trigger(np.ones(n, bool), y, fit, ev, "always_fire")
        entry["baseline_not_unresolved_now"] = bool_trigger(~unres, y, fit, ev, "not_unresolved_now")
        entry["baseline_prev_row_nonidle"] = bool_trigger(~idle, y, fit, ev, "row_t_is_non_idle")
        entry["baseline_idle_and_not_unresolved"] = bool_trigger(idle & ~unres, y, fit, ev, "idle_and_not_unresolved_now")
        # velocity restricted to rows where an onset is even possible next (not unresolved now)
        entry["vel_raw_given_not_unresolved"] = sweep(V_raw, y, fit & ~unres, ev & ~unres, "velocity_raw | not_unresolved_now")
        entry["vel_adaptive_given_not_unresolved"] = sweep(V_adapt, y, fit & ~unres, ev & ~unres, "velocity_adaptive | not_unresolved_now")
        # random-rate baseline at the velocity_raw maxF1 fire rate: precision == base rate, recall == fire rate
        fr = entry["vel_raw"]["theta_maxF1_train"]["test"]["fire_rate"]
        entry["baseline_random_at_matched_rate"] = {"fire_rate": fr, "precision": entry["base_rate_test"],
                                                    "recall": fr, "f1": (2 * entry["base_rate_test"] * fr /
                                                                         (entry["base_rate_test"] + fr)) if fr else 0.0}
        runs[f"k={k}"] = entry
    results["runs"][cname] = runs

# idle-only subsequence
runs = {}
for k in KS:
    y = lead_label_i(oni2, k)
    entry = {"n_idle_rows": int(len(uni)), "base_rate_train": float(y[train_i].mean()),
             "base_rate_test": float(y[test_i].mean())}
    entry["vel_raw"] = sweep(Vi_raw, y, train_i, test_i, "velocity_raw (idle-only subsequence)")
    if not pca_abstain:
        entry["vel_pca_tangent"] = sweep(Vi_pca, y, train_i, test_i, "velocity_pca (idle-only subsequence)")
    entry["baseline_high_tension"] = sweep(Xi[:, 0], y, train_i, test_i, "high_tension_tick (idle-only)")
    entry["baseline_always_fire"] = bool_trigger(np.ones(len(uni), bool), y, train_i, test_i, "always_fire")
    entry["baseline_not_unresolved_now"] = bool_trigger(~uni, y, train_i, test_i, "not_unresolved_now")
    entry["vel_raw_given_not_unresolved"] = sweep(Vi_raw, y, train_i & ~uni, test_i & ~uni, "velocity_raw | not_unresolved (idle-only)")
    runs[f"k={k}"] = entry
results["runs"]["idle_only_subsequence"] = runs

# mean-difference replication (the F-0932 statistic itself, on this split) for reference
from scipy.stats import mannwhitneyu
rep = {}
for vn, V in VELS.items():
    ok = ~np.isnan(V) & test
    a, b = V[ok & Y[3]], V[ok & ~Y[3]]
    rep[vn] = {"pre_onset_mean_test": float(a.mean()), "other_mean_test": float(b.mean()),
               "p": float(mannwhitneyu(a, b, alternative="two-sided").pvalue), "n_pre": int(len(a))}
results["f0932_mean_diff_replication_on_test_k3"] = rep

# ----------------------------------------------------------------------------------------------- write
OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_JSONL, "w", encoding="utf-8") as f:
    hdr = {k: v for k, v in results.items() if k != "runs"}
    f.write(json.dumps({"record": "header", **hdr}) + "\n")
    for cname, runs in results["runs"].items():
        for kk, entry in runs.items():
            for key, val in entry.items():
                if isinstance(val, dict) and "table" in val:
                    for row in val["table"]:
                        f.write(json.dumps({"record": "sweep", "config": cname, "k": kk, "trigger": val["name"],
                                            **row}) + "\n")
                    f.write(json.dumps({"record": "summary", "config": cname, "k": kk, "trigger": val["name"],
                                        "ap_train": val["ap_train"], "ap_test": val["ap_test"],
                                        "base_rate_test": val["base_rate_test"],
                                        "theta_maxF1_train": val["theta_maxF1_train"],
                                        "theta_maxP_at_R30_train": val["theta_maxP_at_R30_train"],
                                        "oracle_test_theta": val["oracle_test_theta"]}) + "\n")
                elif isinstance(val, dict):
                    f.write(json.dumps({"record": "baseline", "config": cname, "k": kk, "trigger": key, **val}) + "\n")
    f.write(json.dumps({"record": "f0932_replication", **rep}) + "\n")


def fmt(r):
    return f"P={r['precision']:.3f} R={r['recall']:.3f} F1={r['f1']:.3f} fire={r['fire_rate']:.3f}"


L = []
L.append("# Pre-onset tangent-velocity characterisation (J-0838 / D-0196 / F-0932)")
L.append("")
L.append(f"Run {_dt.datetime.now(_dt.timezone.utc).isoformat(timespec='seconds')} by "
         f"`scripts/pre_onset_velocity_composition_check.py`. Read-only over `data/geometry_tuples.jsonl` "
         f"({n} rows, {len(days)} UTC days, {results['n_segments']} gap-free segments at a {SEGMENT_GAP_S:.0f}s break) "
         f"and a schema check of `data/moments.jsonl` ({m_n} rows). Companion data: `{OUT_JSONL.name}`.")
L.append("")
L.append("## Setup")
L.append(f"- Vector: {FIELDS} (unresolved held out as the label), null body/affect filled with {DEFAULTS} exactly as "
         "`C:/UDMS/scripts/analyze_nascence_geometry_manifold.py::extract_vector` does.")
L.append("- Positive at step t: a FRESH unresolved onset (`first_in_run_mask`) at any of t+1..t+k, k in 1..3, not crossing a >1h gap.")
L.append("- Trigger: velocity > theta at t. Three velocity definitions (the three F-0932 methodologies): "
         "`raw` = ||x_t - x_{t-1}|| in raw units; `pca_tangent` = UDMSEngine 2-D tangent step (PCA fit on train days only"
         + (f", EVR {results['pca_evr']}" if evr is not None else ", ABSTAINED") + "); "
         f"`adaptive` = step of the vector standardised by the previous {ADAPT_WINDOW} rows (std floor sqrt(0.05)).")
L.append(f"- Chronological split by DAY: fit theta on the first {n_train_days} days ({days[0]} .. {days[n_train_days-1]}, "
         f"{int(train.sum())} rows), report on the last {len(days)-n_train_days} days ({days[n_train_days]} .. {days[-1]}, {int(test.sum())} rows).")
L.append("- Theta chosen on train two ways: max F1, and max precision subject to recall >= 0.3 (D-0196's defeater bar is "
         "precision >= 0.5 at recall >= 0.3 on held-out days). An 'oracle' theta (best F1 on TEST) is shown only as an upper bound.")
L.append("- Baselines: always-fire / random-at-matched-rate (precision = base rate), high-tension tick (tension_t > tau, tau swept the same way), "
         "and label-adjacent triggers that use only what is known at t: `not_unresolved_now`, `row_t_is_non_idle`, `idle_and_not_unresolved_now`.")
L.append("")
L.append("## Data facts that shape the answer")
L.append(f"- `unresolved` is True ONLY on `source=idle` rows: " +
         ", ".join(f"{s}: {c}/{cnt}" for s, (cnt, c) in
                   sorted(((s, (cnt, round(rate, 3))) for s, (cnt, rate) in results['unresolved_by_source'].items()),
                          key=lambda x: -x[1][0])[:8]) +
         f" (rate per source). {int(onset.sum())} fresh onsets / {int(unres.sum())} unresolved rows.")
L.append(f"- `moments.jsonl` keys: {sorted(m_keys)} -- it carries NO `unresolved` (or any resolution) label, so the positive class "
         "can only be defined on geometry_tuples.jsonl; moments.jsonl contributes nothing to this question and is not used further.")
L.append(f"- Null body/affect (filled with defaults): pre-2026-08-29 body null {results['body_null_rate_pre_fix']:.3f}, affect null "
         f"{results['affect_null_rate_pre_fix']:.3f}; post-fix body null {results['body_null_rate_post_fix']:.3f}, affect null "
         f"{results['affect_null_rate_post_fix']:.3f}.")
for vn in VELS:
    L.append(f"- Mean `{vn}` velocity at a source switch vs within-source: {results[f'vel_{vn}_at_switch_mean']:.4f} vs "
             f"{results[f'vel_{vn}_within_source_mean']:.4f} (switch rows pre-fix {results[f'vel_{vn}_prefix_at_switch_mean']:.4f}, "
             f"post-fix {results[f'vel_{vn}_postfix_at_switch_mean']:.4f}).")
L.append("")
L.append("## F-0932's own statistic, on the held-out days (k=3, pre-onset mean vs other)")
for vn, r in rep.items():
    L.append(f"- `{vn}`: pre-onset {r['pre_onset_mean_test']:.4f} vs other {r['other_mean_test']:.4f}, n_pre={r['n_pre']}, MWU p={r['p']:.3g}")
L.append("")


def section(cname, runs, vel_keys):
    L.append(f"## Config `{cname}`")
    for kk, e in runs.items():
        L.append(f"### {kk}  (base rate train {e['base_rate_train']:.3f}, test {e['base_rate_test']:.3f})")
        L.append("| trigger | theta (train maxF1) | TEST at that theta | theta (train maxP, R>=0.3) | TEST at that theta | AP test | AP train | oracle-test F1 |")
        L.append("|---|---|---|---|---|---|---|---|")
        for key in vel_keys + ["baseline_high_tension"]:
            if key not in e:
                continue
            s = e[key]
            b1 = s["theta_maxF1_train"]
            b2 = s["theta_maxP_at_R30_train"]
            L.append(f"| {s['name']} | {b1['theta']:.4f} | {fmt(b1['test'])} | "
                     + (f"{b2['theta']:.4f} | {fmt(b2['test'])}" if b2 else "none reaches R>=0.3 | -")
                     + f" | {s['ap_test']:.3f} | {s['ap_train']:.3f} | {s['oracle_test_theta']['test']['f1']:.3f} |")
        for key in ["baseline_always_fire", "baseline_not_unresolved_now", "baseline_prev_row_nonidle",
                    "baseline_idle_and_not_unresolved"]:
            if key in e:
                L.append(f"| {e[key]['name']} | - | {fmt(e[key]['test'])} | - | - | - | - | - |")
        if "baseline_random_at_matched_rate" in e:
            r = e["baseline_random_at_matched_rate"]
            L.append(f"| random at velocity_raw's fire rate | - | P={r['precision']:.3f} R={r['recall']:.3f} F1={r['f1']:.3f} fire={r['fire_rate']:.3f} | - | - | - | - | - |")
        L.append("")


section("all_rows", results["runs"]["all_rows"],
        ["vel_raw", "vel_pca_tangent", "vel_adaptive", "vel_raw_given_not_unresolved", "vel_adaptive_given_not_unresolved"])
section("post_null_fix_only (rows from 2026-08-29 on; train/test split unchanged)", results["runs"]["post_null_fix_only"],
        ["vel_raw", "vel_pca_tangent", "vel_adaptive", "vel_raw_given_not_unresolved", "vel_adaptive_given_not_unresolved"])
section("idle_only_subsequence (steps and onsets recomputed over idle rows alone)", results["runs"]["idle_only_subsequence"],
        ["vel_raw", "vel_pca_tangent", "vel_raw_given_not_unresolved"])

OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
