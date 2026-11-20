#!/usr/bin/env python3
"""J-3472 -- D-0102 defeater read for the 6-gauge "mood cluster" (F-0565 / F-0585).

D-0102 (ruled by travis 2026-09-01): keep the six mood-cluster gauges measured separately. Its defeater: revisit if a
gauge-correlate pass over a substantially longer window still shows the same monoculture with ZERO divergence.
This script is that pass, on the live logs, read-only:

  gauges (hud/server.py MONITOR_REGISTRY id . field -> log):
    affect_divergence.carried_valence      affect_divergence_shadow.jsonl
    affect_drives.valence                  felt_preamble_log.jsonl
    continuous_stream.ignition             stream_drive_shadow.jsonl
    lane2_weather.commit_threshold         lane2_shadow.jsonl  (nested under "gain")
    opponent_process.b_after               opponent_process_shadow.jsonl
    thermal_relationship.felt_valence      thermal_relationship.jsonl
  sensitivity fields (the F-0565 second members): affect_divergence.proto_tonic, affect_drives.ema_valence.

Outputs, per window (FULL = whole pairwise overlap, LAST30 = the 30 days before the common end, plus the F-0565
REPLICATION window and consecutive 30-day slices):
  1. the 15 pairwise zero-lag Pearson r (hourly bins = F-0565's method; 900 s bins = the lead-lag bins), after
     differencing any series that is a cumulative counter (>= 85 % non-decreasing steps), and a connected-component
     check at the |r| >= 0.6 threshold F-0565 used;
  2. the lead-lag z for each pair on 900 s bins: the contiguous Levy area 0.5*(r(+1)-r(-1)) under the calibrated roll
     null (F-4039) and the sleep/wake-preserving within-bout linear-detrend null (F-4150). This REUSES lag_pair() from
     C:/UDMS/scripts/analyze_nascence_gauge_correlations.py (J-3406), imported read-only, so the nulls are the same code.
  3. the defeater verdict: DIVERGED (a gauge with no |r| >= 0.6 link, or a pair below the divergence floor) and
     DRIVER (one gauge leading its partners with a significant, sign-consistent detrended z).

Reads C:/Nascence/data/*.jsonl read-only; writes ONLY to --out-dir (default docs/lab/J-3472_data/ in this tree).

Usage (from the worktree root):
  python scripts/analyze_j3472_mood_cluster_defeater.py --data-dir C:/Nascence/data
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import math
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
UDMS_SCRIPT = Path(r"C:/UDMS/scripts/analyze_nascence_gauge_correlations.py")
DEFAULT_DATA = Path(r"C:/Nascence/data")

# the six gauges: name -> (log, prefix for series_from_rows, nested key or None, field)
GAUGES = {
    "affect_divergence.carried_valence": ("affect_divergence_shadow.jsonl", "affect_divergence", None, "carried_valence"),
    "affect_drives.valence": ("felt_preamble_log.jsonl", "affect_drives", None, "valence"),
    "continuous_stream.ignition": ("stream_drive_shadow.jsonl", "continuous_stream", None, "ignition"),
    "lane2_weather.commit_threshold": ("lane2_shadow.jsonl", "lane2_weather", "gain", "commit_threshold"),
    "opponent_process.b_after": ("opponent_process_shadow.jsonl", "opponent_process", None, "b_after"),
    "thermal_relationship.felt_valence": ("thermal_relationship.jsonl", "thermal_relationship", None, "felt_valence"),
}
SENSITIVITY = {
    "affect_divergence.proto_tonic": ("affect_divergence_shadow.jsonl", "affect_divergence", None, "proto_tonic"),
    "affect_drives.ema_valence": ("felt_preamble_log.jsonl", "affect_drives", None, "ema_valence"),
}
BOUT_LOG = "sleep_pressure_log.jsonl"

EDGE_R = 0.6            # F-0565's connected-component threshold
DIVERGE_R = 0.3         # a pair below this on the full window counts as a divergence
SIG_Z = 3.0             # F-4039's calibrated level
HOUR, QUARTER, DAY = 3600, 900, 86400
MONOTONIC_FRAC = 0.85   # gauge_correlate.py's cumulative-counter test
CODE_CHANGE_TS = dt.datetime(2026, 9, 4, 10, 21, tzinfo=dt.timezone.utc).timestamp()
REPLICATION = ("2026-08-21", "2026-09-02")   # the August window F-0565 measured: all six logs exist from 08-21, snapshot files end 09-02


def load_udms():
    if not UDMS_SCRIPT.exists():
        sys.exit(f"{UDMS_SCRIPT} not found (J-3406's lag pass is the null library this reuses)")
    spec = importlib.util.spec_from_file_location("udms_gauge_corr", str(UDMS_SCRIPT))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def epoch(day):
    return dt.datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp()


def iso(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%d %H:%MZ")


def load_raw(gc, base, end_ts=None):
    """{name: [(ts, v)]} for the six gauges + sensitivity fields + sleep.awake_min (the bout series)."""
    raw = {}
    for name, (log, prefix, nested, field) in list(GAUGES.items()) + list(SENSITIVITY.items()):
        part = gc.series_from_rows(gc.load_rows(log, base), prefix, nested=nested, fields={field})
        pts = part.get(f"{prefix}.{field}", [])
        raw[name] = [p for p in pts if end_ts is None or p[0] <= end_ts]
    sleep = gc.series_from_rows(gc.load_rows(BOUT_LOG, base), "sleep", fields={"awake_min"})
    raw["sleep.awake_min"] = [p for p in sleep.get("sleep.awake_min", []) if end_ts is None or p[0] <= end_ts]
    return raw


def bucket(raw, bucket_s):
    out = {}
    for name, pts in raw.items():
        b = {}
        for ts, v in pts:
            b.setdefault(int(ts // bucket_s), []).append(v)
        out[name] = {k: sum(vs) / len(vs) for k, vs in b.items()}
    return out


def non_decreasing_fraction(series):
    ks = sorted(series)
    if len(ks) < 3:
        return 0.0
    steps = [series[ks[i + 1]] - series[ks[i]] for i in range(len(ks) - 1)]
    return sum(1 for s in steps if s >= 0) / len(steps)


def difference(series):
    ks = sorted(series)
    return {ks[i + 1]: series[ks[i + 1]] - series[ks[i]] for i in range(len(ks) - 1)}


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sx = sum((x - mx) ** 2 for x in xs)
    sy = sum((y - my) ** 2 for y in ys)
    if sx == 0 or sy == 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(sx * sy)


def window_slice(b, lo_bin, hi_bin):
    return {k: v for k, v in b.items() if lo_bin <= k <= hi_bin}


def zero_lag_table(bucketed, names, lo_bin, hi_bin, min_overlap=24, first_diff=False):
    """{(a,b): {'r':, 'n':, 'diff': bool}} on the common bins inside [lo_bin, hi_bin]. A series that is a cumulative
    counter inside the window is differenced first (it never fires for these six, but the check is reported)."""
    sl = {n: window_slice(bucketed[n], lo_bin, hi_bin) for n in names}
    mono = {n: non_decreasing_fraction(sl[n]) for n in names}
    if first_diff:
        # first differences across ADJACENT bins only: strips the shared slow trend a one-episode window can carry
        sl = {n: {k: v - sl[n][k - 1] for k, v in sl[n].items() if (k - 1) in sl[n]} for n in names}
    else:
        for n in names:
            if mono[n] >= MONOTONIC_FRAC:
                sl[n] = difference(sl[n])
    res = {}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            common = sorted(set(sl[a]) & set(sl[b]))
            if len(common) < min_overlap:
                res[(a, b)] = {"r": None, "n": len(common), "diff": False}
                continue
            r = pearson([sl[a][c] for c in common], [sl[b][c] for c in common])
            res[(a, b)] = {"r": r, "n": len(common), "diff": mono[a] >= MONOTONIC_FRAC or mono[b] >= MONOTONIC_FRAC}
    return res, mono


def components(names, table, edge_r=EDGE_R):
    parent = {n: n for n in names}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for (a, b), d in table.items():
        if d["r"] is not None and abs(d["r"]) >= edge_r:
            parent[find(a)] = find(b)
    groups = {}
    for n in names:
        groups.setdefault(find(n), []).append(n)
    return sorted(groups.values(), key=lambda g: (-len(g), g))


def summarize_r(table):
    rs = [abs(d["r"]) for d in table.values() if d["r"] is not None]
    if not rs:
        return {"n_pairs": 0}
    rs.sort()
    return {"n_pairs": len(rs), "min": rs[0], "median": rs[len(rs) // 2], "max": rs[-1],
            "n_ge_edge": sum(1 for r in rs if r >= EDGE_R), "n_lt_diverge": sum(1 for r in rs if r < DIVERGE_R)}


def lag_table(gc, bucketed15, names, gaw, lo_bin, hi_bin, draws, seed, r0_sign):
    """lag_pair() per pair inside [lo_bin, hi_bin]. Direction: the Levy area is 0.5*(r(+1)-r(-1)) with
    r(+1)=mean a_t*b_{t+1} and r(-1)=mean a_{t+1}*b_t. For a positively coupled pair area > 0 means a leads b; for a
    NEGATIVELY coupled pair the larger-magnitude lagged term is the more negative one, so area > 0 means b leads a.
    So the leader is a iff sign(r0) * area > 0 (r0_sign = sign of the zero-lag r on the same window; J-3406's
    _lead_label reaches the same answer by comparing |r(+1)| with |r(-1)|)."""
    out = {}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            r = gc.lag_pair(window_slice(bucketed15[a], lo_bin, hi_bin), window_slice(bucketed15[b], lo_bin, hi_bin),
                            window_slice(gaw, lo_bin, hi_bin), draws=draws, seed=seed)
            r["a"], r["b"] = a, b
            area = r.get("det_area", r.get("raw_area"))
            sgn = r0_sign.get((a, b))
            if "det_z" in r:
                r["dir_basis"] = "detrended"
            elif "raw_z" in r:
                r["dir_basis"] = "raw only"
            if area is not None and sgn:
                r["coupling"] = "+" if sgn > 0 else "-"
                r["leader"], r["follower"] = (a, b) if sgn * area > 0 else (b, a)
            out[(a, b)] = r
    return out


def driver_read(names, lag, z_key="det_z"):
    """Per gauge: significant pairs where it leads / follows under z_key (|z| >= SIG_Z); a DRIVER leads at least 4 of
    its 5 pairs significantly and follows none."""
    tally = {n: {"leads": [], "follows": [], "scored": 0, "unscored": 0} for n in names}
    for (a, b), r in lag.items():
        for n in (a, b):
            if z_key in r:
                tally[n]["scored"] += 1
            else:
                tally[n]["unscored"] += 1
        if z_key in r and abs(r[z_key]) >= SIG_Z:
            tally[r["leader"]]["leads"].append(r["follower"])
            tally[r["follower"]]["follows"].append(r["leader"])
    drivers = [n for n in names if len(tally[n]["leads"]) >= 4 and not tally[n]["follows"]]
    return tally, drivers


def fmt(v, spec="+.3f"):
    return format(v, spec) if isinstance(v, (int, float)) else "-"


def short(n):
    return n.replace("affect_divergence.", "aff_div.").replace("affect_drives.", "aff_drv.") \
        .replace("continuous_stream.", "stream.").replace("lane2_weather.", "lane2.") \
        .replace("opponent_process.", "opp.").replace("thermal_relationship.", "therm.")


def run(args):
    gc = load_udms()
    base = Path(args.data_dir)
    names = list(GAUGES)
    # the common end: the logs' shared last timestamp (felt_preamble_log runs on after Du stopped, with 'warming up' rows)
    ends = {}
    full_raw = load_raw(gc, base)
    for n in names:
        if full_raw[n]:
            ends[n] = max(p[0] for p in full_raw[n])
    if args.end:
        common_end = epoch(args.end)
    else:
        common_end = max(ends[n] for n in names if n != "affect_drives.valence")
    raw = {k: [p for p in v if p[0] <= common_end] for k, v in full_raw.items()}
    spans = {n: (len(raw[n]), min(p[0] for p in raw[n]), max(p[0] for p in raw[n])) for n in raw if raw[n]}
    print(f"common end {iso(common_end)}  (per-series ends: " +
          ", ".join(f"{short(n)} {iso(e)}" for n, e in ends.items()) + ")")
    for n, (c, lo, hi) in spans.items():
        print(f"  {n:<38} rows={c:<7} {iso(lo)} .. {iso(hi)}")

    b3600 = bucket(raw, HOUR)
    b900 = bucket(raw, QUARTER)
    gaw = b900["sleep.awake_min"]
    t_hi = int(common_end // HOUR)
    q_hi = int(common_end // QUARTER)

    windows = {}
    windows["FULL"] = (None, None)
    windows["LAST30"] = (common_end - 30 * DAY, common_end)
    windows["REPLICATION"] = (epoch(REPLICATION[0]), epoch(REPLICATION[1]))
    # Nascence commit 444b60b8 (J-0580, 2026-09-04 22:21 +1200 = 10:21Z) connected stream_drive._ignition()'s climate
    # term, which had silently failed before (F-0807, nonexistent core.climate module): the split tests whether the
    # ignition gauge's detachment dates from that change. Zero-lag only.
    windows["PRE_0904"] = (epoch("2026-08-21"), CODE_CHANGE_TS)
    windows["POST_0904"] = (CODE_CHANGE_TS, common_end)
    # consecutive 30-day slices back from the common end, as far as all-six data goes
    all_six_start = max(spans[n][1] for n in names)
    slices = []
    hi = common_end - 30 * DAY          # LAST30 is the newest 30 days; the slices are the 30-day blocks before it
    while hi - 30 * DAY >= all_six_start - 1:
        slices.append((hi - 30 * DAY, hi))
        hi -= 30 * DAY
    slices.reverse()

    report = {"common_end": iso(common_end), "spans": {n: [c, iso(lo), iso(hi)] for n, (c, lo, hi) in spans.items()},
              "all_six_start": iso(all_six_start), "windows": {}}
    all_windows = dict(windows)
    for k, (lo, hi_) in enumerate(slices, 1):
        all_windows[f"SLICE{k}"] = (lo, hi_)

    for wname, (lo_t, hi_t) in all_windows.items():
        lo_h = int(lo_t // HOUR) if lo_t else 0
        hi_h = int(hi_t // HOUR) if hi_t else t_hi
        lo_q = int(lo_t // QUARTER) if lo_t else 0
        hi_q = int(hi_t // QUARTER) if hi_t else q_hi
        tbl_h, mono = zero_lag_table(b3600, names, lo_h, hi_h)
        tbl_q, _ = zero_lag_table(b900, names, lo_q, hi_q, min_overlap=96)
        comps_h = components(names, tbl_h)
        tbl_d, _ = zero_lag_table(b3600, names, lo_h, hi_h, min_overlap=24, first_diff=True)
        entry = {"hourly_diff": {f"{a} x {b}": d for (a, b), d in tbl_d.items()}, "hourly_diff_summary": summarize_r(tbl_d),
                 "window": [iso(lo_t) if lo_t else "start", iso(hi_t) if hi_t else iso(common_end)],
                 "monotonic_frac": {n: round(v, 3) for n, v in mono.items()},
                 "hourly": {f"{a} x {b}": d for (a, b), d in tbl_h.items()},
                 "quarter": {f"{a} x {b}": d for (a, b), d in tbl_q.items()},
                 "hourly_summary": summarize_r(tbl_h), "quarter_summary": summarize_r(tbl_q),
                 "components_hourly": comps_h}
        report["windows"][wname] = entry
        s = entry["hourly_summary"]
        print(f"\n[{wname}] {entry['window'][0]} .. {entry['window'][1]}  hourly |r|: min {fmt(s.get('min'), '.3f')} "
              f"median {fmt(s.get('median'), '.3f')} max {fmt(s.get('max'), '.3f')}; "
              f"{s.get('n_ge_edge')}/{s.get('n_pairs')} pairs >= {EDGE_R}, {s.get('n_lt_diverge')} < {DIVERGE_R}; "
              f"components at |r|>={EDGE_R}: {[[short(x) for x in g] for g in comps_h]}")

    # weekly trajectory: hourly zero-lag r per pair in consecutive 7-day windows from the all-six start
    weekly = []
    wlo = all_six_start
    while wlo < common_end - 3 * DAY:        # a final partial week is kept when it is at least 3 days long
        wt, _m = zero_lag_table(b3600, names, int(wlo // HOUR), int(min(wlo + 7 * DAY, common_end) // HOUR), min_overlap=48)
        rs = [abs(d["r"]) for d in wt.values() if d["r"] is not None]
        weekly.append({"start": iso(wlo)[:10], "n_pairs": len(rs),
                       "min_abs_r": min(rs) if rs else None,
                       "median_abs_r": sorted(rs)[len(rs) // 2] if rs else None,
                       "n_ge_edge": sum(1 for x in rs if x >= EDGE_R),
                       "r": {f"{a} x {b}": d["r"] for (a, b), d in wt.items()}})
        wlo += 7 * DAY
    report["weekly"] = weekly

    # lead-lag (FULL and LAST30 and each slice); 900 s bins, the J-3406 nulls
    lag_windows = {"FULL": (None, None), "LAST30": windows["LAST30"]}
    for k, sl in enumerate(slices, 1):
        lag_windows[f"SLICE{k}"] = sl
    for wname, (lo_t, hi_t) in lag_windows.items():
        lo_q = int(lo_t // QUARTER) if lo_t else 0
        hi_q = int(hi_t // QUARTER) if hi_t else q_hi
        tbl_q_w, _ = zero_lag_table(b900, names, lo_q, hi_q, min_overlap=96)
        r0_sign = {k: (1 if d["r"] > 0 else -1) for k, d in tbl_q_w.items() if d["r"] is not None}
        lag = lag_table(gc, b900, names, gaw, lo_q, hi_q, args.draws, args.seed, r0_sign)
        tally_det, drivers_det = driver_read(names, lag, "det_z")
        tally_raw, drivers_raw = driver_read(names, lag, "raw_z")
        report["windows"][wname]["lag"] = {
            f"{a} x {b}": {k: v for k, v in r.items() if k not in ("a", "b")} for (a, b), r in lag.items()}
        report["windows"][wname]["lag_driver_det"] = {"tally": tally_det, "drivers": drivers_det}
        report["windows"][wname]["lag_driver_raw"] = {"tally": tally_raw, "drivers": drivers_raw}
        sig_det = sum(1 for r in lag.values() if "det_z" in r and abs(r["det_z"]) >= SIG_Z)
        sig_raw = sum(1 for r in lag.values() if "raw_z" in r and abs(r["raw_z"]) >= SIG_Z)
        scored_det = sum(1 for r in lag.values() if "det_z" in r)
        print(f"[{wname}] lead-lag: {scored_det}/15 pairs scored under the detrended null, {sig_det} at |z|>={SIG_Z:.0f}; "
              f"roll null {sig_raw} at |z|>={SIG_Z:.0f}; drivers (det) {drivers_det}; drivers (raw) {drivers_raw}")

    # verdict on the defeater
    full = report["windows"]["FULL"]
    last = report["windows"]["LAST30"]
    verdict = verdict_for(names, full, last, report["windows"])
    report["verdict"] = verdict
    print("\nVERDICT:", json.dumps(verdict, indent=1))

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "mood_cluster_defeater_read.json").write_text(json.dumps(report, indent=1, default=str), encoding="utf-8")
    write_tsv(out_dir, names, report)
    write_md(Path(args.md), names, report, args)
    print(f"wrote {out_dir} and {args.md}")
    return report


def verdict_for(names, full, last, windows):
    v = {}
    # divergence: a gauge with no |r|>=EDGE_R partner on the window, or any pair < DIVERGE_R
    for wname in ("FULL", "LAST30"):
        w = windows[wname]
        h = w["hourly"]
        isolated = []
        for n in names:
            partners = [d["r"] for k, d in h.items() if n in k.split(" x ") and d["r"] is not None]
            if not any(abs(r) >= EDGE_R for r in partners):
                isolated.append(n)
        low = [k for k, d in h.items() if d["r"] is not None and abs(d["r"]) < DIVERGE_R]
        nones = [k for k, d in h.items() if d["r"] is None]
        v[wname] = {"isolated_gauges": isolated, "pairs_below_diverge_floor": low, "pairs_unmeasurable": nones,
                    "single_component": len(w["components_hourly"]) == 1,
                    "n_pairs_ge_edge": w["hourly_summary"].get("n_ge_edge"), "n_pairs": w["hourly_summary"].get("n_pairs")}
    v["drivers_full_det"] = full["lag_driver_det"]["drivers"]
    v["drivers_last30_det"] = last["lag_driver_det"]["drivers"]
    return v


def write_tsv(out_dir, names, report):
    rows = ["window\tpair\tn_hourly\tr_hourly\tn_quarter\tr_quarter\tdet_r0\tbins\tsteps\tbouts\tbout_steps\t"
            "raw_area\traw_z\tdet_area\tdet_z\tdet_z_inshift\tleader\tfollower\tnote"]
    for wname, w in report["windows"].items():
        for key in w["hourly"]:
            h, q = w["hourly"][key], w["quarter"][key]
            l = w.get("lag", {}).get(key, {})
            rows.append("\t".join([
                wname, key, str(h["n"]), fmt(h["r"], ".4f"), str(q["n"]), fmt(q["r"], ".4f"), fmt(l.get("det_r0"), ".4f"),
                str(l.get("bins", "")), str(l.get("steps", "")), str(l.get("bouts", "")), str(l.get("bout_steps", "")),
                fmt(l.get("raw_area"), ".5f"), fmt(l.get("raw_z"), ".2f"), fmt(l.get("det_area"), ".5f"),
                fmt(l.get("det_z"), ".2f"), fmt(l.get("det_z_inshift"), ".2f"), l.get("leader", ""), l.get("follower", ""),
                l.get("note", "")]))
    (out_dir / "mood_cluster_pairs.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    keys = list(report["weekly"][0]["r"]) if report.get("weekly") else []
    wrows = ["week_start\tn_pairs\tmin_abs_r\tmedian_abs_r\tn_pairs_ge_0.6\t" + "\t".join(keys)]
    for wk in report.get("weekly", []):
        wrows.append("\t".join([wk["start"], str(wk["n_pairs"]), fmt(wk["min_abs_r"], ".3f"), fmt(wk["median_abs_r"], ".3f"),
                                str(wk["n_ge_edge"])] + [fmt(wk["r"].get(k), ".3f") for k in keys]))
    (out_dir / "mood_cluster_weekly_r.tsv").write_text("\n".join(wrows) + "\n", encoding="utf-8")


def write_md(path, names, report, args):
    L = []
    w = L.append
    w("# D-0102 defeater read: the six mood-cluster gauges (J-3472)\n")
    w(f"Generated by `scripts/analyze_j3472_mood_cluster_defeater.py` on the live `C:/Nascence/data` logs, read-only, "
      f"common end {report['common_end']}; roll draws {args.draws}, seed {args.seed}. Lead-lag nulls are J-3406's "
      f"`lag_pair()` (F-4039 roll null; F-4150 within-wake-bout linear detrend).\n")
    w("## Series coverage\n")
    w("| series | rows | first | last |\n|---|---:|---|---|")
    for n, (c, lo, hi) in report["spans"].items():
        w(f"| {n} | {c} | {lo} | {hi} |")
    w(f"\nAll six overlap only from {report['all_six_start']}; three of the six logs (lane2_shadow, "
      f"opponent_process_shadow, thermal_relationship) start in the last third of the span, so a pair that includes one of them "
      f"spans fewer days than the 141-day headline.\n")
    for wname, wd in report["windows"].items():
        w(f"## Window {wname}: {wd['window'][0]} .. {wd['window'][1]}\n")
        s = wd["hourly_summary"]
        w(f"Hourly (F-0565's bins) |r|: min {fmt(s.get('min'), '.3f')}, median {fmt(s.get('median'), '.3f')}, max "
          f"{fmt(s.get('max'), '.3f')}; {s.get('n_ge_edge')}/{s.get('n_pairs')} pairs at |r| >= {EDGE_R}; "
          f"connected components at that threshold: {[[short(x) for x in g] for g in wd['components_hourly']]}.\n")
        sd = wd["hourly_diff_summary"]
        w(f"Same window on hourly FIRST DIFFERENCES (adjacent bins only; strips a shared slow trend): |r| min {fmt(sd.get('min'), '.3f')}, "
          f"median {fmt(sd.get('median'), '.3f')}, max {fmt(sd.get('max'), '.3f')}; {sd.get('n_ge_edge')}/{sd.get('n_pairs')} pairs at |r| >= {EDGE_R}.\n")
        has_lag = "lag" in wd
        hdr = "| pair | n (h) | r (1 h) | n (15 m) | r (15 m) | r (1 h, first diff) |"
        sep = "|---|---:|---:|---:|---:|---:|"
        if has_lag:
            hdr += " r0 detrended | steps | z roll | z detrended | leads (by coupling sign x area) |"
            sep += "---:|---:|---:|---:|---|"
        w(hdr)
        w(sep)
        for key in wd["hourly"]:
            h, q = wd["hourly"][key], wd["quarter"][key]
            line = f"| {short(key.split(' x ')[0])} x {short(key.split(' x ')[1])} | {h['n']} | {fmt(h['r'])} | {q['n']} | {fmt(q['r'])} | {fmt(wd['hourly_diff'][key]['r'])} |"
            if has_lag:
                l = wd["lag"][key]
                lead = f"{short(l['leader'])} -> {short(l['follower'])}" if "leader" in l else "-"
                if "det_z" not in l and "raw_z" in l:
                    lead += " (raw only)"
                line += (f" {fmt(l.get('det_r0'))} | {l.get('steps', '-')} | {fmt(l.get('raw_z'), '+.2f')} | "
                         f"{fmt(l.get('det_z'), '+.2f')} | {lead if ('raw_z' in l or 'det_z' in l) else l.get('note', '-')} |")
            w(line)
        if has_lag:
            tl = wd["lag_driver_det"]["tally"]
            w("\nLeads / follows among significant pairs (detrended null, |z| >= 3):\n")
            w("| gauge | leads | follows | pairs scored | pairs unscored |\n|---|---|---|---:|---:|")
            for n, t in tl.items():
                w(f"| {n} | {', '.join(short(x) for x in t['leads']) or '-'} | {', '.join(short(x) for x in t['follows']) or '-'} | {t['scored']} | {t['unscored']} |")
            w(f"\nDrivers (lead >= 4 of 5, follow none): detrended {wd['lag_driver_det']['drivers'] or 'none'}, "
              f"roll null {wd['lag_driver_raw']['drivers'] or 'none'}.\n")
    w("## Weekly trajectory (hourly zero-lag r, consecutive 7-day windows; every pair in mood_cluster_weekly_r.tsv)\n")
    w("| week start | pairs measured | min abs r | median abs r | pairs >= 0.6 | aff_drv x stream | aff_drv x opp | aff_drv x lane2 | aff_drv x therm |")
    w("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for wk in report.get("weekly", []):
        g = lambda k: fmt(wk["r"].get(k))
        w(f"| {wk['start']} | {wk['n_pairs']} | {fmt(wk['min_abs_r'], '.3f')} | {fmt(wk['median_abs_r'], '.3f')} | {wk['n_ge_edge']} | "
          f"{g('affect_drives.valence x continuous_stream.ignition')} | {g('affect_drives.valence x opponent_process.b_after')} | "
          f"{g('affect_drives.valence x lane2_weather.commit_threshold')} | {g('affect_drives.valence x thermal_relationship.felt_valence')} |")
    w("")
    w("## Verdict mechanics\n")
    w("```json\n" + json.dumps(report["verdict"], indent=1) + "\n```\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data-dir", type=Path, default=DEFAULT_DATA)
    ap.add_argument("--out-dir", type=Path, default=ROOT / "docs" / "lab" / "J-3472_data")
    ap.add_argument("--md", type=Path, default=ROOT / "docs" / "lab" / "J-3472_data" / "mood_cluster_tables.md",
                    help="the generated tables; the hand-written verdict is docs/audits/mood_cluster_defeater_read_2026-11-07.md")
    ap.add_argument("--draws", type=int, default=500)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--end", type=str, default=None, help="common end day YYYY-MM-DD (default: the logs' last timestamp)")
    args = ap.parse_args(argv)
    run(args)


if __name__ == "__main__":
    main()
