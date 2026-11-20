"""
scripts/compare_homeostasis_forecast_J-0677.py — J-0677, D-0148 defeater check #3 tooling.

D-0148's ruling (option A: unpin the integration_drive bleed) carries a one-week post-restart
defeater; check #3 of that defeater reads: "homeostasis_causal forecasts diverge from live
dissonance by more than 0.2" (decide.py show D-0148, re-verified this job — see F-0967/F-0967's
own quote of the same text). This script measures that divergence as a real distribution
(max/p90/median), not a single number, per this job's own briefing.

WHAT IT ACTUALLY COMPARES AND WHY (read core/homeostasis_causal.py in full before changing this):
  `predict_coherence()` / `predict_novelty()` (core/homeostasis_causal.py) each load the CURRENT
  climate_state.json snapshot and project `_simulate_reservoirs()` forward by
  `DEFAULT_FORECAST_DT_SECS` (600s nominal — imported below, never hand-copied) to forecast what
  the live reader will see later. There is no historical log of climate_state.json's own raw
  dissonance.value between ticks to replay (a single snapshot, overwritten every ~5s tick, never
  logged per-row — see homeostasis_causal.py's own module docstring) — so a fresh live poll would
  need to sit and wait ~600s per sample to build any distribution at all.

  core/homeostasis.py's tick() already sidesteps that: it is called every ~600s (core/sensorium.py's
  cooldown gate — DELIBERATELY the same cadence as DEFAULT_FORECAST_DT_SECS, see that gate's own
  comment) and logs BOTH the forecast made THIS tick (`predicted_causal.coherence` /
  `.novelty` — the real, unmodified output of calling predict_coherence()/predict_novelty(), not a
  reimplementation) and the live actual reading THIS tick (`variables.coherence` / `.novelty`, via
  _read_coherence()/_read_novelty()) into data/homeostasis_shadow.jsonl. Because the tick cadence
  equals the forecast horizon BY DESIGN, consecutive rows already ARE real one-step-ahead
  forecast/actual pairs — pairing row i's forecast against the closest later row's actual reading
  (nearest-match within a tolerance, not a blind `i+1`, since ~64 days of real operation has ~85
  gaps over 2x the horizon — Du offline/restarted periods — that must be rejected, not matched
  across) reconstructs the exact comparison D-0148 asks for, using the real system's own real
  historical calls to predict_coherence()/predict_novelty() — not a hand re-derivation of their math.

  This means re-running this exact script UNCHANGED, once J-0671's restart gate is met (Du actually
  restarted onto the J-0594 build AND a week has accrued — see docs/staged/
  ignition_pressure_and_time.md's Current State section and F-0967; NOT met as of 2026-09-06, this
  job's own fresh re-check confirmed the same PID/creation-time F-0967 found, zero restarts since),
  IS the real D-0148 defeater-#3 read against post-fix data. Today it can only run against pre-fix
  data — a smoke test proving the tool works, per this job's own briefing, not a verdict.

SCALE NOTE: coherence-forecast divergence is IDENTICAL (same abs value, not just "related") to a
live-dissonance.value divergence, because core/homeostasis.py's _read_coherence() computes exactly
`1 - dissonance.value` and predict_coherence() returns exactly `1 - projected_value` — the two 1-x
transforms cancel in the abs difference. novelty is a related but DISTINCT scale (predict_novelty()
blends in shadow_activation too — see its own docstring), so it is reported as its own series, plus
a per-sample max() of the two as the single most-conservative reading of D-0148's defeater text,
which names both predict_coherence() and predict_novelty() against "the live dissonance" in one
clause.

Usage:
    python scripts/compare_homeostasis_forecast_J-0677.py [--log PATH] [--tolerance-secs N] [--threshold X]

Read-only: opens data/homeostasis_shadow.jsonl for reading only, writes nothing anywhere.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.homeostasis_causal import DEFAULT_FORECAST_DT_SECS  # the real horizon, not a hand-copy

DEFAULT_LOG = ROOT / "data" / "homeostasis_shadow.jsonl"
# D-0148's defeater #3 threshold, verified via a fresh `decide.py show D-0148` this job (matches F-0967's
# own quote of the same ruling text) — not a guess, not hand-copied from a paraphrase.
D0148_DIVERGENCE_THRESHOLD = 0.2


def load_rows(path: Path) -> tuple[list[dict], int]:
    """Full parse, no tail sampling (project convention) — every line, count bad ones rather than
    silently skipping them."""
    rows: list[dict] = []
    bad = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                bad += 1
    rows.sort(key=lambda r: r.get("ts", 0.0))
    return rows, bad


def find_target_row(rows: list[dict], start_idx: int, target_ts: float, tolerance_secs: float):
    """Nearest row after `start_idx` whose ts is closest to `target_ts`, among rows within
    `tolerance_secs` of it. Rows are ts-sorted, so once a candidate is more than `tolerance_secs`
    PAST the target nothing later can be closer — safe to stop scanning. Returns (index, |dt|) or
    (None, None) if nothing in range (a real gap in the log — Du offline/restarted — not a bug)."""
    best_idx = None
    best_dist = None
    for j in range(start_idx + 1, len(rows)):
        ts_j = rows[j].get("ts")
        if ts_j is None:
            continue
        if ts_j > target_ts + tolerance_secs:
            break
        dist = abs(ts_j - target_ts)
        if ts_j >= target_ts - tolerance_secs and (best_dist is None or dist < best_dist):
            best_idx, best_dist = j, dist
    return best_idx, best_dist


def dist_report(name: str, xs: list[float], threshold: float) -> None:
    if not xs:
        print(f"  {name}: NO SAMPLES")
        return
    xs_sorted = sorted(xs)
    n = len(xs_sorted)
    p90 = xs_sorted[min(n - 1, int(0.9 * n))]
    med = statistics.median(xs_sorted)
    over = sum(1 for x in xs if x > threshold)
    print(f"  {name}:")
    print(f"    n={n}  median={med:.4f}  p90={p90:.4f}  max={max(xs_sorted):.4f}  "
          f"over {threshold} threshold: {over}/{n} ({100.0 * over / n:.1f}%)")


def main() -> int:
    ap = argparse.ArgumentParser(description="Compare homeostasis_causal's forecasts against later live readings.")
    ap.add_argument("--log", default=str(DEFAULT_LOG), help="path to homeostasis_shadow.jsonl")
    ap.add_argument("--tolerance-secs", type=float, default=DEFAULT_FORECAST_DT_SECS,
                     help="max |actual_match_ts - (sample_ts+horizon)| accepted as a match "
                          "(default: one horizon width, i.e. accept elapsed real time in "
                          "[0, 2x horizon] around the nominal target)")
    ap.add_argument("--threshold", type=float, default=D0148_DIVERGENCE_THRESHOLD,
                     help="divergence threshold to report an over/under count against (default: D-0148's 0.2)")
    args = ap.parse_args()

    log_path = Path(args.log)
    if not log_path.exists():
        print(f"NO DATA: {log_path} does not exist. Nothing accrued yet -- cannot compare.")
        return 1

    rows, bad_lines = load_rows(log_path)
    print(f"Parsed {len(rows)} rows from {log_path} ({bad_lines} bad lines skipped).")
    if not rows:
        print("NO DATA: log is empty.")
        return 1

    horizon = DEFAULT_FORECAST_DT_SECS
    print(f"Forecast horizon (core.homeostasis_causal.DEFAULT_FORECAST_DT_SECS): {horizon:.0f}s")
    print(f"Match tolerance: +/-{args.tolerance_secs:.0f}s around each sample's ts+horizon target")
    print(f"D-0148 defeater #3 divergence threshold: {args.threshold}")
    print()

    coh_divs: list[float] = []
    nov_divs: list[float] = []
    combined_divs: list[float] = []
    match_dt_errs: list[float] = []
    n_no_predicted_causal = 0
    n_no_match = 0
    n_fallback_coh = 0   # predicted_causal.coherence == THIS tick's own live coherence (fail-open or genuine no-change; not distinguished)
    n_fallback_nov = 0
    first_sample_ts = None
    last_sample_ts = None

    for i, row in enumerate(rows):
        pc = row.get("predicted_causal")
        if not pc or "coherence" not in pc or "novelty" not in pc:
            n_no_predicted_causal += 1
            continue
        ts_i = row.get("ts")
        variables_i = row.get("variables") or {}
        if ts_i is None:
            continue

        target_ts = ts_i + horizon
        j, dist = find_target_row(rows, i, target_ts, args.tolerance_secs)
        if j is None:
            n_no_match += 1
            continue
        actual = rows[j].get("variables") or {}
        if "coherence" not in actual or "novelty" not in actual:
            n_no_match += 1
            continue

        if "coherence" in variables_i and abs(pc["coherence"] - variables_i["coherence"]) < 1e-9:
            n_fallback_coh += 1
        if "novelty" in variables_i and abs(pc["novelty"] - variables_i["novelty"]) < 1e-9:
            n_fallback_nov += 1

        d_coh = abs(pc["coherence"] - actual["coherence"])
        d_nov = abs(pc["novelty"] - actual["novelty"])
        coh_divs.append(d_coh)
        nov_divs.append(d_nov)
        combined_divs.append(max(d_coh, d_nov))
        match_dt_errs.append(dist)
        first_sample_ts = ts_i if first_sample_ts is None else min(first_sample_ts, ts_i)
        last_sample_ts = ts_i if last_sample_ts is None else max(last_sample_ts, ts_i)

    print(f"Rows skipped -- no predicted_causal.coherence/novelty yet (pre-dates the causal build): {n_no_predicted_causal}")
    print(f"Rows skipped -- no later row within tolerance to match against (a real gap: Du offline/restarted): {n_no_match}")
    print(f"Samples where predicted_causal.coherence == that SAME tick's own live coherence "
          f"(possible predict_coherence() fail-open fallback OR a genuine near-zero-change forecast, not distinguished here): "
          f"{n_fallback_coh}")
    print(f"Same check for novelty: {n_fallback_nov}")
    if match_dt_errs:
        print(f"Match quality: median |actual_match_ts - target_ts| = {statistics.median(match_dt_errs):.1f}s "
              f"(0s would mean a perfect hit on the nominal {horizon:.0f}s horizon)")
    if first_sample_ts is not None:
        import datetime
        print(f"Usable sample window: {datetime.datetime.fromtimestamp(first_sample_ts)} .. "
              f"{datetime.datetime.fromtimestamp(last_sample_ts)}")
    print()
    print("Divergence distributions (D-0148 defeater #3: \"homeostasis_causal forecasts diverge from live dissonance by more than 0.2\"):")
    dist_report("coherence forecast vs later live coherence (== live dissonance.value divergence, exactly, see SCALE NOTE)", coh_divs, args.threshold)
    dist_report("novelty forecast vs later live novelty_hunger (related, NOT identical, scale -- see SCALE NOTE)", nov_divs, args.threshold)
    dist_report("combined: max(coherence_div, novelty_div) per sample -- most conservative single reading of the defeater text", combined_divs, args.threshold)
    print()
    print(f"Total usable samples: {len(coh_divs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
