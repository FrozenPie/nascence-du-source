#!/usr/bin/env python3
"""J-3744 -- follow-up to J-3472 (D-0102 defeater read), read-only on C:/Nascence/data.

Two questions J-3472 left open:
  (1) why did opponent_process.b_after detach from the valence family (hourly |r| 0.54-0.69 in August, 0.13-0.45 since)?
      Decomposes the hourly gauge (mean of b_after over the pair-activation rows in the hour) into what it is made of:
      first activations of a pair (b_after is then a pure function of the valence SIGN: the step table) vs repeat
      activations (b_after carries the pair's decaying state), the progress-signal mix, and the co-recall source mix
      (each opponent_process row is joined to its co_recall_ledger row by timestamp, because the shadow log
      hardcodes source="co_recall"). Reports hourly r(valence, gauge) per period and per component, plus an
      EVENT-time r (valence at the event, from the nearest earlier felt_preamble row, vs the row's b_after).
  (2) is ignition's lead over valence only the two sampling cadences? Cross-correlation at EVENT time: both series
      are put on a 60 s grid by last-observation-carried-forward (stale beyond 300 s = missing), detrended by a 3 h
      rolling mean, and C(tau) = corr(ign(t), val(t+tau)) is read at tau = +-1..30 min; A(tau) = sign(C0)*(C(+tau)-C(-tau))
      is positive when ignition leads. Null: circular shift of the valence grid by a random offset >= 6 h (500 draws,
      seed 42; same spirit as the F-4039 roll null). Also the per-row version: for each valence row the last ignition
      row before it vs the next after it, with the gaps reported.

Reads data/*.jsonl; writes ONLY to --out-dir. Run: python scripts/analyze_j3744_mood_cluster_followup.py
"""
from __future__ import annotations

import argparse
import bisect
import collections
import datetime as dt
import json
import math
import sys
from pathlib import Path

import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(r"C:/Nascence/data")
HOUR = 3600
UTC = dt.timezone.utc

# dated code/config changes that can move b_after (all read from git, times UTC)
KILL_SWITCH_TS = dt.datetime(2026, 9, 28, 7, 32, tzinfo=UTC).timestamp()    # first co_recall_ledger curiosity + monologue_shadow rows (the restart that picked up 7a167458 J-1587 D-0310 flags-off and the memory_service curiosity wiring)
PERIODS = [
    ("P1 08-19..09-28a (ambient recall ON, before 09-28 07:32Z)", dt.datetime(2026, 8, 19, tzinfo=UTC).timestamp(), KILL_SWITCH_TS),
    ("P1a 08-21..09-02 (F-0565 window)", dt.datetime(2026, 8, 21, tzinfo=UTC).timestamp(), dt.datetime(2026, 9, 3, tzinfo=UTC).timestamp()),
    ("P1b 09-04..09-28a", dt.datetime(2026, 9, 4, 10, 21, tzinfo=UTC).timestamp(), KILL_SWITCH_TS),
    ("P2 09-28b..10-06 (ambient OFF, shadow rows still tick)", KILL_SWITCH_TS, dt.datetime(2026, 10, 7, tzinfo=UTC).timestamp()),
    ("P3 10-07..end (ambient OFF)", dt.datetime(2026, 10, 7, tzinfo=UTC).timestamp(), 9e12),
    ("ALL", 0, 9e12),
]


def rows_of(path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                yield json.loads(line)
            except Exception:
                pass


def pearson(x, y):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    if len(x) < 8 or x.std() == 0 or y.std() == 0:
        return None
    return float(np.corrcoef(x, y)[0, 1])


def f3(v, spec="+.3f"):
    return format(v, spec) if isinstance(v, (int, float)) else "-"


# --------------------------------------------------------------------------------------------- part 1
def part1(data, out):
    opp = [r for r in rows_of(data / "opponent_process_shadow.jsonl") if "skip" not in r]
    ledger = [(r["ts"], r.get("source")) for r in rows_of(data / "co_recall_ledger.jsonl") if r.get("n_ids", 0) >= 2]
    ledger.sort()
    lts = [x[0] for x in ledger]
    fp = [(r["ts"], r["valence"]) for r in rows_of(data / "felt_preamble_log.jsonl") if isinstance(r.get("valence"), (int, float))]
    fp.sort()
    fts = [x[0] for x in fp]

    # join each opp row to the ledger row whose ts is the closest earlier-or-equal within 2 s (opp stamps time.time() a few ms later)
    for r in opp:
        i = bisect.bisect_right(lts, r["ts"] + 0.05) - 1
        r["lsrc"] = ledger[i][1] if i >= 0 and r["ts"] - lts[i] <= 2.0 else "?unjoined"
        j = bisect.bisect_right(fts, r["ts"]) - 1
        r["val"] = fp[j][1] if j >= 0 and r["ts"] - fts[j] <= 120 else None
    res = {"n_rows": len(opp)}

    # daily source mix (so the kill-switch and the J-1738 effective date are visible)
    day = collections.defaultdict(lambda: collections.Counter())
    for r in opp:
        day[dt.datetime.fromtimestamp(r["ts"], UTC).strftime("%m-%d")][r["lsrc"]] += 1
    res["daily_source"] = {k: dict(v.most_common(5)) for k, v in sorted(day.items())}

    # per-period composition
    comp = {}
    for name, lo, hi in PERIODS:
        rs = [r for r in opp if lo <= r["ts"] < hi]
        if not rs:
            continue
        n = len(rs)
        c = collections.Counter(r["sign"] for r in rs)
        first = [r for r in rs if r["activation_n"] == 1]
        rep = [r for r in rs if r["activation_n"] > 1]
        comp[name] = {
            "n": n, "mean_b_after": sum(r["b_after"] for r in rs) / n,
            "mean_b_after_first": sum(r["b_after"] for r in first) / len(first) if first else None,
            "mean_b_after_repeat": sum(r["b_after"] for r in rep) / len(rep) if rep else None,
            "first_share": len(first) / n, "progress_signal_share": sum(r["has_progress_signal"] for r in rs) / n,
            "pos": c["positive"] / n, "aver": c["aversive"] / n, "neut": c["neutral"] / n,
            "mean_b_prev": sum(r["b_prev"] for r in rs) / n,
            "src": {k: round(v / n, 3) for k, v in collections.Counter(r["lsrc"] for r in rs).most_common(5)},
        }
    res["composition"] = comp

    # hourly gauge and its parts vs hourly mean valence
    hv = collections.defaultdict(list)
    for t, v in fp:
        hv[int(t // HOUR)].append(v)
    hv = {k: sum(x) / len(x) for k, x in hv.items()}

    def hourly(rs, key):
        d = collections.defaultdict(list)
        for r in rs:
            d[int(r["ts"] // HOUR)].append(r[key])
        return {k: sum(x) / len(x) for k, x in d.items()}

    def r_vs_val(series, first_diff=False, min_n=24):
        ks = sorted(set(series) & set(hv))
        if first_diff:
            ks = [k for k in ks if (k - 1) in series and (k - 1) in hv]
            xs = [series[k] - series[k - 1] for k in ks]
            ys = [hv[k] - hv[k - 1] for k in ks]
        else:
            xs = [series[k] for k in ks]
            ys = [hv[k] for k in ks]
        return (pearson(xs, ys), len(ks)) if len(ks) >= min_n else (None, len(ks))

    hourly_tab = {}
    for name, lo, hi in PERIODS:
        rs = [r for r in opp if lo <= r["ts"] < hi]
        e = {}
        for label, sel in (("gauge (all rows)", rs),
                           ("first activations only", [r for r in rs if r["activation_n"] == 1]),
                           ("repeat activations only", [r for r in rs if r["activation_n"] > 1]),
                           ("rows with a progress signal", [r for r in rs if r["has_progress_signal"]]),
                           ("rows without", [r for r in rs if not r["has_progress_signal"]])):
            s = hourly(sel, "b_after")
            e[label] = {"r": r_vs_val(s), "r_diff": r_vs_val(s, True)}
        # the sign-share explanation: hourly share of aversive rows (the thresholded valence at the event) vs hourly valence
        sh = collections.defaultdict(list)
        for r in rs:
            sh[int(r["ts"] // HOUR)].append(1.0 if r["sign"] == "aversive" else 0.0)
        s_av = {k: sum(x) / len(x) for k, x in sh.items()}
        e["aversive share of rows"] = {"r": r_vs_val(s_av), "r_diff": r_vs_val(s_av, True)}
        e["mean b_prev (state)"] = {"r": r_vs_val(hourly(rs, "b_prev")), "r_diff": r_vs_val(hourly(rs, "b_prev"), True)}
        hourly_tab[name] = e
    res["hourly_r_vs_valence"] = hourly_tab

    # per-source view and source-excluded counterfactual gauges (which feeder carries the repeat-activation accumulation?)
    first_seen = {}
    for t, src in ledger:
        first_seen.setdefault(src, t)
    res["ledger_source_first_seen"] = {str(k): dt.datetime.fromtimestamp(v, UTC).strftime("%Y-%m-%d %H:%MZ") for k, v in first_seen.items()}
    src_tab = {}
    for name, lo, hi in PERIODS:
        if name not in ("P1 08-19..09-28a (ambient recall ON, before 09-28 07:32Z)", "P3 10-07..end (ambient OFF)"):
            continue
        rs = [r for r in opp if lo <= r["ts"] < hi]
        e = {}
        for src in sorted({r["lsrc"] for r in rs}, key=lambda x: str(x)):
            sel = [r for r in rs if r["lsrc"] == src]
            if len(sel) < 500:
                continue
            fr = [r for r in sel if r["activation_n"] == 1]
            rp = [r for r in sel if r["activation_n"] > 1]
            e[str(src)] = {"n": len(sel), "share": len(sel) / len(rs), "first_share": len(fr) / len(sel),
                           "mean_b_after": sum(r["b_after"] for r in sel) / len(sel),
                           "mean_b_after_repeat": sum(r["b_after"] for r in rp) / len(rp) if rp else None,
                           "mean_b_prev": sum(r["b_prev"] for r in sel) / len(sel),
                           "hourly_r_vs_valence": r_vs_val(hourly(sel, "b_after"), min_n=48)}
        # counterfactual: the same gauge with one feeder removed (its rows are still in the STATE that later rows decay from)
        cf = {}
        for drop in ("curiosity", "monologue_shadow", "wandering", "monologue"):
            sel = [r for r in rs if r["lsrc"] != drop]
            if sel and len(sel) < len(rs):
                cf["without " + drop] = {"n": len(sel), "hourly_r_vs_valence": r_vs_val(hourly(sel, "b_after"))}
        e["_counterfactual_gauge"] = cf
        src_tab[name] = e
    res["per_source"] = src_tab

    # event time: valence at the event (nearest earlier fp row) vs b_after, overall and within activation class
    ev = {}
    for name, lo, hi in PERIODS:
        rs = [r for r in opp if lo <= r["ts"] < hi and r["val"] is not None]
        e = {"n": len(rs)}
        for label, sel in (("all", rs), ("first", [r for r in rs if r["activation_n"] == 1]),
                           ("repeat", [r for r in rs if r["activation_n"] > 1])):
            e[label] = pearson([r["val"] for r in sel], [r["b_after"] for r in sel])
        ev[name] = e
    res["event_time_r_valence_vs_b_after"] = ev

    # does the sign itself still follow valence at the event? (it should by construction: sign = threshold of mood.current_valence())
    agree = collections.Counter()
    for r in opp:
        if r["val"] is None:
            continue
        s = "aversive" if r["val"] <= -0.05 else ("positive" if r["val"] >= 0.05 else "neutral")
        agree[s == r["sign"]] += 1
    res["sign_matches_nearest_fp_valence"] = {"match": agree[True], "mismatch": agree[False]}
    return res


# --------------------------------------------------------------------------------------------- part 2
def locf_grid(ts, vs, g0, n, step=60, max_age=300):
    """last-observation-carried-forward onto a step-second grid; NaN where the last observation is older than max_age."""
    t = np.asarray(ts, float)
    v = np.asarray(vs, float)
    grid = g0 + step * np.arange(n)
    idx = np.searchsorted(t, grid, side="right") - 1
    ok = idx >= 0
    out = np.full(n, np.nan)
    age = np.where(ok, grid - t[np.clip(idx, 0, None)], np.inf)
    good = ok & (age <= max_age)
    out[good] = v[idx[good]]
    return out


def rolling_detrend(x, win):
    """x minus its centred rolling mean over `win` points, NaN-aware."""
    m = np.isfinite(x)
    xs = np.where(m, x, 0.0)
    c = np.concatenate([[0.0], np.cumsum(xs)])
    cn = np.concatenate([[0], np.cumsum(m.astype(int))])
    n = len(x)
    lo = np.clip(np.arange(n) - win // 2, 0, n)
    hi = np.clip(np.arange(n) + win // 2 + 1, 0, n)
    cnt = cn[hi] - cn[lo]
    with np.errstate(invalid="ignore", divide="ignore"):
        mean = (c[hi] - c[lo]) / cnt
    out = x - mean
    out[cnt < win // 4] = np.nan
    return out


def xc(a, b, lag):
    """corr(a(t), b(t+lag)) on grid points where both are finite."""
    if lag > 0:
        x, y = a[:-lag], b[lag:]
    elif lag < 0:
        x, y = a[-lag:], b[:lag]
    else:
        x, y = a, b
    m = np.isfinite(x) & np.isfinite(y)
    k = int(m.sum())
    if k < 500:
        return float("nan")
    x, y = x[m], y[m]
    sx, sy = x.std(), y.std()
    if sx == 0 or sy == 0:
        return float("nan")
    return float(((x - x.mean()) * (y - y.mean())).mean() / (sx * sy))


def part2(data, draws, seed, out):
    ig = [(r["ts"], r["ignition"]) for r in rows_of(data / "stream_drive_shadow.jsonl") if isinstance(r.get("ignition"), (int, float))]
    fp = [(r["ts"], r["valence"]) for r in rows_of(data / "felt_preamble_log.jsonl") if isinstance(r.get("valence"), (int, float))]
    ig.sort()
    fp.sort()
    res = {"n_ignition_rows": len(ig), "n_valence_rows": len(fp)}

    # per-row view: last ignition before / first after each valence row
    its = np.array([x[0] for x in ig])
    ivs = np.array([x[1] for x in ig])
    fts = np.array([x[0] for x in fp])
    fvs = np.array([x[1] for x in fp])
    i = np.searchsorted(its, fts, side="left")
    ok = (i > 0) & (i < len(its))
    gp = fts[ok] - its[i[ok] - 1]
    gn = its[i[ok]] - fts[ok]
    res["gap_prev_pctl"] = [float(np.percentile(gp, q)) for q in (5, 25, 50, 75, 95)]
    res["gap_next_pctl"] = [float(np.percentile(gn, q)) for q in (5, 25, 50, 75, 95)]
    vv, ip, inx = fvs[ok], ivs[i[ok] - 1], ivs[i[ok]]
    # restrict to rows where both neighbours are within 120 s (inside one wake stretch)
    near = (gp <= 120) & (gn <= 120)
    res["per_row"] = {}
    for label, sel in (("all with both neighbours <=120 s", near),
                       ("gap-matched (next/prev gap ratio in 0.8..1.25)", near & (gn / np.maximum(gp, 1e-9) >= 0.8) & (gn / np.maximum(gp, 1e-9) <= 1.25)),
                       ("next closer than prev", near & (gn < gp)), ("prev closer than next", near & (gp < gn))):
        r_prev = pearson(vv[sel], ip[sel])
        r_next = pearson(vv[sel], inx[sel])
        r_pn = pearson(ip[sel], inx[sel])
        part_prev = part_next = None
        if None not in (r_prev, r_next, r_pn):
            d1 = math.sqrt(max(1e-12, (1 - r_next ** 2) * (1 - r_pn ** 2)))
            part_prev = (r_prev - r_next * r_pn) / d1                  # corr(val, ign_prev | ign_next)
            part_next = (r_next - r_prev * r_pn) / d1                  # corr(val, ign_next | ign_prev)
        res["per_row"][label] = {"n": int(sel.sum()), "r_val_ign_prev": r_prev, "r_val_ign_next": r_next,
                                 "r_prev_next": r_pn, "partial_val_prev_given_next": part_prev,
                                 "partial_val_next_given_prev": part_next,
                                 "median_gap_prev": float(np.median(gp[sel])) if sel.any() else None,
                                 "median_gap_next": float(np.median(gn[sel])) if sel.any() else None}

    # grid cross-correlation
    g0 = math.floor(max(its[0], fts[0]) / 60) * 60
    g1 = min(its[-1], fts[-1])
    n = int((g1 - g0) // 60)
    gi = locf_grid(its, ivs, g0, n)
    gv = locf_grid(fts, fvs, g0, n)
    win = 180
    di, dv = rolling_detrend(gi, win), rolling_detrend(gv, win)
    lags = [1, 2, 5, 10, 15, 20, 30]
    rng = np.random.default_rng(seed)
    windows = {
        "FULL": (0, n),
        "PRE 09-04 10:21Z": (0, int((dt.datetime(2026, 9, 4, 10, 21, tzinfo=UTC).timestamp() - g0) // 60)),
        "POST 09-04 10:21Z": (int((dt.datetime(2026, 9, 4, 10, 21, tzinfo=UTC).timestamp() - g0) // 60), n),
        "LAST 30 d": (max(0, n - 30 * 1440), n),
    }
    res["grid"] = {"grid_points": n, "start": dt.datetime.fromtimestamp(g0, UTC).isoformat(), "end": dt.datetime.fromtimestamp(g1, UTC).isoformat(),
                   "finite_ign": int(np.isfinite(di).sum()), "finite_val": int(np.isfinite(dv).sum()), "lags_min": lags, "windows": {}}
    for wname, (a, b) in windows.items():
        wi, wv = di[a:b], dv[a:b]
        if np.isfinite(wi).sum() < 2000 or np.isfinite(wv).sum() < 2000:
            continue
        c0 = xc(wi, wv, 0)
        sgn = 1.0 if c0 >= 0 else -1.0
        curve = {lag: (xc(wi, wv, lag), xc(wi, wv, -lag)) for lag in lags}
        asym = {lag: sgn * (p - m) for lag, (p, m) in curve.items()}
        # roll null: shift the valence grid by a random offset >= 6 h
        null = {lag: [] for lag in lags}
        span = len(wv)
        for _ in range(draws):
            sh = int(rng.integers(360, max(361, span - 360)))
            wv2 = np.roll(wv, sh)
            for lag in lags:
                p, m = xc(wi, wv2, lag), xc(wi, wv2, -lag)
                null[lag].append(sgn * (p - m))
        z = {}
        for lag in lags:
            arr = np.array([x for x in null[lag] if np.isfinite(x)])
            z[lag] = float((asym[lag] - arr.mean()) / arr.std()) if len(arr) > 20 and arr.std() > 0 else None
        res["grid"]["windows"][wname] = {"C0": c0, "curve": {str(k): {"C(+tau)": v[0], "C(-tau)": v[1]} for k, v in curve.items()},
                                         "A": {str(k): v for k, v in asym.items()}, "z_vs_roll_null": {str(k): v for k, v in z.items()},
                                         "n_pairs0": int((np.isfinite(wi) & np.isfinite(wv)).sum())}
    # peak lag of C over the full range, finer
    wi, wv = di, dv
    fine = list(range(-60, 61, 2))
    cc = [xc(wi, wv, k) for k in fine]
    j = int(np.nanargmax(np.abs(cc)))
    res["grid"]["fine_peak_lag_min_FULL"] = fine[j]
    res["grid"]["fine_curve_FULL"] = {str(k): c for k, c in zip(fine, cc)}
    return res


def write_md(path, r1, r2):
    L = []
    w = L.append
    w("# J-3744 generated tables (mood cluster follow-up)\n")
    w("## Part 1: opponent_process.b_after composition per period\n")
    w("| period | rows | mean b_after | mean (first act.) | mean (repeat) | first share | progress-signal share | pos/aver/neut | mean b_prev | ledger source mix |")
    w("|---|---:|---:|---:|---:|---:|---:|---|---:|---|")
    for k, c in r1["composition"].items():
        w(f"| {k} | {c['n']} | {f3(c['mean_b_after'], '.3f')} | {f3(c['mean_b_after_first'], '.3f')} | {f3(c['mean_b_after_repeat'], '.3f')} | "
          f"{c['first_share']:.2f} | {c['progress_signal_share']:.2f} | {c['pos']:.2f}/{c['aver']:.2f}/{c['neut']:.2f} | {c['mean_b_prev']:.3f} | {c['src']} |")
    w("\n## Part 1: hourly r(component, hourly mean valence) per period  (r, n_hours | first-difference r)\n")
    for k, e in r1["hourly_r_vs_valence"].items():
        w(f"**{k}**\n")
        w("| component | r (hourly) | n | r (first diff) | n |\n|---|---:|---:|---:|---:|")
        for label, d in e.items():
            (r, n), (rd, nd) = d["r"], d["r_diff"]
            w(f"| {label} | {f3(r)} | {n} | {f3(rd)} | {nd} |")
        w("")
    w("## Part 1: per feeder (ledger source), hourly r(b_after of that feeder's rows, valence)\n")
    w(f"first seen in co_recall_ledger (n_ids>=2): {r1['ledger_source_first_seen']}\n")
    for k, e in r1["per_source"].items():
        w(f"**{k}**\n")
        w("| feeder | rows | share | first-act. share | mean b_after | mean b_after (repeat) | mean b_prev | hourly r vs valence (n) |")
        w("|---|---:|---:|---:|---:|---:|---:|---|")
        for src, d in e.items():
            if src.startswith("_"):
                continue
            rr, nn = d["hourly_r_vs_valence"]
            w(f"| {src} | {d['n']} | {d['share']:.2f} | {d['first_share']:.2f} | {d['mean_b_after']:.3f} | {f3(d['mean_b_after_repeat'], '.3f')} | {d['mean_b_prev']:.3f} | {f3(rr)} ({nn}) |")
        for lab, d in e["_counterfactual_gauge"].items():
            rr, nn = d["hourly_r_vs_valence"]
            w(f"\n- gauge {lab}: hourly r vs valence {f3(rr)} (n {nn} hours)")
        w("")
    w("## Part 1: event-time r(valence at event, b_after)\n")
    w("| period | n | all | first activations | repeat activations |\n|---|---:|---:|---:|---:|")
    for k, e in r1["event_time_r_valence_vs_b_after"].items():
        w(f"| {k} | {e['n']} | {f3(e['all'])} | {f3(e['first'])} | {f3(e['repeat'])} |")
    w(f"\nSign vs nearest-earlier felt_preamble valence: {r1['sign_matches_nearest_fp_valence']}\n")
    w("## Part 1: daily ledger-source mix of the opponent_process rows (top 5)\n")
    for k, v in r1["daily_source"].items():
        if "09-20" <= k <= "10-20":
            w(f"- {k}: {v}")
    w("\n## Part 2: per-row view (last ignition row before each valence row vs first after)\n")
    w(f"valence rows {r2['n_valence_rows']}, ignition rows {r2['n_ignition_rows']}; gap to previous ignition row pctl (5/25/50/75/95 s) {[round(x, 1) for x in r2['gap_prev_pctl']]}; "
      f"gap to next {[round(x, 1) for x in r2['gap_next_pctl']]}\n")
    w("| subset | n | r(val, ign_prev) | r(val, ign_next) | r(prev, next) | partial val~prev given next | partial val~next given prev | median gap prev | median gap next |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for k, d in r2["per_row"].items():
        w(f"| {k} | {d['n']} | {f3(d['r_val_ign_prev'])} | {f3(d['r_val_ign_next'])} | {f3(d['r_prev_next'])} | {f3(d['partial_val_prev_given_next'])} | "
          f"{f3(d['partial_val_next_given_prev'])} | {f3(d['median_gap_prev'], '.1f')} | {f3(d['median_gap_next'], '.1f')} |")
    w("\n## Part 2: grid cross-correlation (60 s LOCF grid, 3 h rolling-mean detrend); A(tau) > 0 means ignition leads valence\n")
    g = r2["grid"]
    w(f"grid {g['start']} .. {g['end']}, {g['grid_points']} points; finite ign {g['finite_ign']}, val {g['finite_val']}; fine peak |C| lag (FULL) {g['fine_peak_lag_min_FULL']} min\n")
    for wn, d in g["windows"].items():
        w(f"**{wn}**  C(0) = {f3(d['C0'])}, paired points {d['n_pairs0']}\n")
        w("| tau (min) | C(+tau) | C(-tau) | A(tau) | z vs roll null |\n|---:|---:|---:|---:|---:|")
        for lag in g["lags_min"]:
            c = d["curve"][str(lag)]
            w(f"| {lag} | {f3(c['C(+tau)'])} | {f3(c['C(-tau)'])} | {f3(d['A'][str(lag)])} | {f3(d['z_vs_roll_null'][str(lag)], '+.2f')} |")
        w("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, default=DATA)
    ap.add_argument("--out-dir", type=Path, default=ROOT / "docs" / "lab" / "J-3744_data")
    ap.add_argument("--draws", type=int, default=500)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args(argv)
    r1 = part1(args.data_dir, args.out_dir)
    print("part 1 done", r1["n_rows"])
    r2 = part2(args.data_dir, args.draws, args.seed, args.out_dir)
    print("part 2 done")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "mood_cluster_followup.json").write_text(json.dumps({"part1": r1, "part2": r2}, indent=1, default=str), encoding="utf-8")
    write_md(args.out_dir / "mood_cluster_followup_tables.md", r1, r2)
    print("wrote", args.out_dir)


if __name__ == "__main__":
    main()
