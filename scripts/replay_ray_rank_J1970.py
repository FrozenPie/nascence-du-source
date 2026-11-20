"""
J-1970 / D-0364 (C): replay the Theta ray over the RECORDED triggers under several ranking rules, before/after the
tod/season backfill. READ-ONLY: opens the live DB with mode=ro, reads data/theta_shadow.jsonl, writes nothing but
stdout (and an optional --out JSON path you give it, e.g. in a scratchpad).

Pools (both honest, both reported):
  STORED  = fragment_context rows whose tod/season are non-NULL today (what the shipped ray can see).
  FULL    = every fragment_context row, phase derived from tuple_ts with core.theta_shadow.now_phase (what the
            ray would see after scripts/backfill_phase_J1970.py runs). Stored values are used where present.

Rules (rank key = d_tod + w * d_season, ties most-recent first):  w=1.0 is the pre-J-1970 rule.
Metrics per (pool, rule): p50/p90 age of the top-3 slots, share of slots older than 7 / 14 / 30 days, mean d_tod,
mean d_season, share of rows where top-3 differs from a recency-only top-3 (most recent eligible rows, no phase),
mean distinct ids / repeats, truncation count at the old 2000-row cap.

Run:  python scripts/replay_ray_rank_J1970.py [--max-ts 1791270000] [--out path.json]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
from core import theta_shadow as T  # noqa: E402  (std-lib only module; no side effects on import)

LIVE_DB = Path(r"C:\Nascence\data\memory\nascence.db")
LIVE_LOG = Path(r"C:\Nascence\data\theta_shadow.jsonl")
DAY = 86400.0


def load_pool():
    conn = sqlite3.connect(f"file:{LIVE_DB.as_posix()}?mode=ro", uri=True)
    rows = conn.execute("SELECT fragment_id, tuple_ts, tod, season FROM fragment_context "
                        "WHERE tuple_ts IS NOT NULL").fetchall()
    conn.close()
    ids = np.array([r[0] for r in rows], dtype=object)
    ts = np.array([r[1] for r in rows], dtype=np.float64)
    stored = np.array([r[2] is not None and r[3] is not None for r in rows])
    tod = np.empty(len(rows)); season = np.empty(len(rows))
    mism = 0
    for i, r in enumerate(rows):
        dt, ds = T.now_phase(r[1])
        if stored[i]:
            if r[2] != dt or r[3] != ds:
                mism += 1
            tod[i], season[i] = r[2], r[3]
        else:
            tod[i], season[i] = dt, ds
    return ids, ts, tod, season, stored, mism


def wdist(a, b):
    d = np.abs(a - b)
    return np.minimum(d, 1.0 - d)


def pct(x, q):
    return float(np.percentile(x, q)) if len(x) else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-ts", type=float, default=1791270000.0,
                    help="only replay log rows with ts <= this (default = the closed 3025-row sample, ~2026-10-06 07:28)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--weights", default="1.0,0.5,0.25,0.1,0.03,0.0")
    args = ap.parse_args()
    weights = [float(x) for x in args.weights.split(",")]

    ids, ts, tod, season, stored, mism = load_pool()
    print(f"pool: {len(ids)} rows, stored phase {int(stored.sum())}, derived!=stored on {mism} stored rows")
    trig = []
    for line in LIVE_LOG.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            if r["ts"] <= args.max_ts:
                trig.append(r)
    print(f"triggers: {len(trig)} (ts <= {args.max_ts})")

    order_recent = np.argsort(-ts, kind="stable")   # for the recency-only baseline

    results: dict = {}
    # faithfulness: old rule on STORED pool must reproduce the logged top3 set where the log had candidates
    faith = tot = 0
    for pool_name in ("STORED", "FULL"):
        for w in weights:
            results[(pool_name, w)] = dict(ages=[], dtod=[], dsea=[], differ_base=0, rows=0, trunc=0,
                                           ids=[], n_cand=[])
    for r in trig:
        now = r["ts"]
        t0, s0 = T.now_phase(now)
        elig = ts < now - T.MIN_AGE_S
        dt = wdist(tod, t0)
        ds = wdist(season, s0)
        in_win = elig & (dt <= T.TOD_TOLERANCE + 1e-12) & (ds <= T.SEASON_TOLERANCE + 1e-12)
        for pool_name in ("STORED", "FULL"):
            pool_mask = in_win & (stored if pool_name == "STORED" else True)
            idx = np.nonzero(pool_mask)[0]
            # recency-only baseline (no phase) over the pool's eligible rows
            base_elig = elig & (stored if pool_name == "STORED" else True)
            bidx = order_recent[base_elig[order_recent]][:3]
            bset = set(ids[bidx])
            for w in weights:
                R = results[(pool_name, w)]
                R["rows"] += 1
                R["n_cand"].append(len(idx))
                if len(idx) > 2000:
                    R["trunc"] += 1
                if len(idx) == 0:
                    continue
                key_d = dt[idx] + w * ds[idx]
                # sort by (key, -ts): lexsort uses last key as primary
                o = np.lexsort((-ts[idx], key_d))[:3]
                top = idx[o]
                R["ages"].extend((now - ts[top]) / DAY)
                R["dtod"].extend(dt[top])
                R["dsea"].extend(ds[top])
                R["ids"].extend(ids[top])
                if set(ids[top]) != bset:
                    R["differ_base"] += 1
                if pool_name == "STORED" and w == 1.0 and r["n_candidates"] >= 1:
                    tot += 1
                    if set(ids[top]) == set(r["top3_ids"]):
                        faith += 1
    print(f"faithfulness (old rule, stored pool vs logged top3 set, rows with logged candidates): {faith}/{tot}")

    summary = []
    print(f"\n{'pool':6} {'w':>5} {'rows':>5} {'win_med':>7} {'trunc>2000':>10} {'p50age':>7} {'p90age':>7} "
          f">7d >14d >30d  {'d_tod(min)':>10} {'d_sea(d)':>9} {'differ_vs_recency':>17} {'distinct/slots':>14}")
    for (pool_name, w), R in results.items():
        a = np.array(R["ages"])
        if not len(a):
            continue
        nrows_cand = sum(1 for n in R["n_cand"] if n > 0)
        row = dict(pool=pool_name, w=w, rows=R["rows"], rows_with_cand=nrows_cand,
                   win_median=float(np.median(R["n_cand"])), trunc=R["trunc"],
                   p50_age_d=pct(a, 50), p90_age_d=pct(a, 90),
                   gt7=float((a > 7).mean()), gt14=float((a > 14).mean()), gt30=float((a > 30).mean()),
                   mean_dtod_min=float(np.mean(R["dtod"]) * 1440), mean_dseason_days=float(np.mean(R["dsea"]) * 366),
                   differ_vs_recency=R["differ_base"] / max(nrows_cand, 1),
                   distinct_over_slots=len(set(R["ids"])) / len(R["ids"]), slots=len(a))
        summary.append(row)
        print(f"{pool_name:6} {w:5.2f} {R['rows']:5d} {row['win_median']:7.0f} {R['trunc']:10d} {row['p50_age_d']:7.2f} "
              f"{row['p90_age_d']:7.2f} {row['gt7']:.2f} {row['gt14']:.2f} {row['gt30']:.3f}  "
              f"{row['mean_dtod_min']:10.2f} {row['mean_dseason_days']:9.2f} {row['differ_vs_recency']:17.3f} "
              f"{row['distinct_over_slots']:14.3f}")
    if args.out:
        Path(args.out).write_text(json.dumps(summary, indent=1), encoding="utf-8")


if __name__ == "__main__":
    t = time.time()
    main()
    print(f"\n[{time.time()-t:.0f}s]")
