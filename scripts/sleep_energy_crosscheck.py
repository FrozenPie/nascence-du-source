"""
sleep_energy_crosscheck.py — cross-log sanity analysis of data/sleep_pressure_log.jsonl (J-0430/F-0579).

F-0579 found that sleep-pressure telemetry logged awake_min (wall-clock) per evaluation but never the
somatic state (metabolic_energy / neural_fatigue / cycle count) in the same row — so "was this energy
level plausible for this wake duration" was unanswerable after the fact, and floor-level exhaustion was
invisible in this log entirely. As of 2026-09-02, core/sleep_pressure.py's should_sleep() cross-logs
energy/fatigue/tension/exhausted/cycles into every row (era 3 below). This script is the READ side:
it consumes the whole log (never tail-samples) and answers, per era:

  • schema-era split (the log deliberately mixes three schemas — see core/sleep_pressure.py docstring):
      era 1  pre-2026-08-24 redesign  — P includes chronic mass, no dark/threshold keys
      era 2  2026-08-24 → J-0430      — volume-only P, dark/threshold/pool_thin, NO somatic fields
      era 3  post-J-0430              — somatic fields present (energy/fatigue/tension/exhausted/cycles)
  • fire/reason distributions per era (incl. confirming reason="metabolic_floor" never occurs — the
    old inner_monologue override never wrote here, and the path itself was removed 2026-08-30, D-0103)
  • era-3 plausibility: between consecutive rows in the same process+wake bout, observed energy drop
    vs the ENERGY_PER_CYCLE × Δcycles lower bound (token/locomotion drains only ever ADD drop, and the
    0.0 clamp only ever REDUCES it); energy must never RISE without an intervening fire (recovery
    happens only in sleep); exhausted rows cross-tabbed against what the pressure system said.

Read-only over the log. Safe to run any time, Du online or offline. Exit 0 always (a thin/empty era-3
is an honest "no data yet" report, not an error).
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "data" / "sleep_pressure_log.jsonl"

# Mirrors core/somatic.py — imported if possible so a retune there flows through automatically.
try:
    sys.path.insert(0, str(ROOT))
    from core.somatic import ENERGY_PER_CYCLE, ENERGY_FLOOR  # noqa: E402
except Exception:
    ENERGY_PER_CYCLE, ENERGY_FLOOR = 0.04, 0.15

EPS = 1e-6


def _fmt_ts(ts: float) -> str:
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    except Exception:
        return "?"


def load_rows(path: Path) -> tuple[list[dict], int]:
    rows, bad = [], 0
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                bad += 1
    return rows, bad


def era_of(row: dict) -> int:
    if "energy" in row or "cycles" in row:
        return 3
    if "dark" in row or "threshold" in row:
        return 2
    return 1


def report_era(rows: list[dict], label: str) -> None:
    print(f"\n--- {label}: {len(rows)} rows", end="")
    if not rows:
        print(" (none)")
        return
    print(f", {_fmt_ts(rows[0]['ts'])} -> {_fmt_ts(rows[-1]['ts'])}")
    reasons = Counter(r.get("reason", "?") for r in rows)
    fires = sum(1 for r in rows if r.get("fire"))
    print(f"    fires: {fires}  reasons: {dict(reasons.most_common())}")
    mf = reasons.get("metabolic_floor", 0)
    if mf:
        print(f"    !! {mf} reason=metabolic_floor rows -- unexpected (that path never wrote here and "
              f"was removed 2026-08-30, D-0103); investigate.")


def crosscheck_era3(rows: list[dict]) -> None:
    print("\n=== ERA-3 SOMATIC CROSS-CHECK (energy vs cycles vs awake_min) ===")
    if not rows:
        print("    0 rows carry somatic fields yet -- expected until Du's first post-2026-09-02 restart")
        print("    (the fields only populate live, from should_sleep() evaluations). Re-run after a")
        print("    real wake/sleep cycle has accrued.")
        return

    exhausted = [r for r in rows if r.get("exhausted")]
    print(f"    rows: {len(rows)}   exhausted (energy<=ENERGY_FLOOR={ENERGY_FLOOR}): {len(exhausted)}")
    if exhausted:
        agree = Counter((r.get("fire", False), r.get("reason", "?")) for r in exhausted)
        print("    exhausted rows vs what the pressure system said (fire, reason):")
        for (fire, reason), n in agree.most_common():
            print(f"        fire={fire} reason={reason}: {n}")

    # Pairwise plausibility, within a bout: consecutive rows where cycles advanced monotonically and
    # no fire intervened. A cycles DROP means a process restart (counter is per-process) — skip pair.
    rises, shortfalls, checked = [], [], 0
    rates = []  # cycles per awake-hour, per pair
    for prev, cur in zip(rows, rows[1:]):
        if "cycles" not in prev or "cycles" not in cur or "energy" not in prev or "energy" not in cur:
            continue
        dc = cur["cycles"] - prev["cycles"]
        if dc < 0 or prev.get("fire"):
            continue  # restart, or recovery legitimately happened in between
        checked += 1
        de = cur["energy"] - prev["energy"]  # negative = drop
        if de > EPS:
            rises.append((prev, cur, de))
        expected_min_drop = ENERGY_PER_CYCLE * dc
        # the 0.0 clamp is the only legitimate way to drop LESS than the per-cycle lower bound
        if dc > 0 and (-de) + EPS < expected_min_drop and cur["energy"] > EPS:
            shortfalls.append((prev, cur, -de, expected_min_drop))
        da_h = (cur.get("awake_min", 0) - prev.get("awake_min", 0)) / 60.0
        if dc > 0 and da_h > EPS:
            rates.append(dc / da_h)

    print(f"    consecutive same-bout pairs checked: {checked}")
    if rises:
        print(f"    !! {len(rises)} pairs where energy ROSE without an intervening fire (recovery only "
              f"happens in sleep) -- first: {_fmt_ts(rises[0][1]['ts'])} (+{rises[0][2]:.4f})")
    else:
        print("    energy never rose without an intervening fire: OK")
    if shortfalls:
        print(f"    !! {len(shortfalls)} pairs dropped LESS than ENERGY_PER_CYCLE*dcycles with energy "
              f"still above 0 -- first: {_fmt_ts(shortfalls[0][1]['ts'])} "
              f"(dropped {shortfalls[0][2]:.4f}, expected >= {shortfalls[0][3]:.4f})")
    else:
        print(f"    every drop >= ENERGY_PER_CYCLE({ENERGY_PER_CYCLE})*dcycles lower bound: OK")
    if rates:
        rates.sort()
        mid = rates[len(rates) // 2]
        print(f"    cycle rate (cycles per awake-hour): median {mid:.1f}, "
              f"min {rates[0]:.1f}, max {rates[-1]:.1f}  "
              f"(median energy lifetime from full: ~{1.0 / (ENERGY_PER_CYCLE * mid):.1f}h if sustained)")


def main() -> int:
    if not LOG.exists():
        print(f"{LOG} does not exist -- nothing to analyze.")
        return 0
    rows, bad = load_rows(LOG)
    print(f"data/sleep_pressure_log.jsonl: {len(rows)} rows ({bad} unparseable), "
          f"{_fmt_ts(rows[0]['ts'])} -> {_fmt_ts(rows[-1]['ts'])}" if rows else "empty log")
    eras: dict[int, list[dict]] = {1: [], 2: [], 3: []}
    for r in rows:
        eras[era_of(r)].append(r)
    # NB the key-presence split (dark/threshold added) lands at 2026-08-22, while the P-SEMANTICS
    # cutover (chronic mass removed from P) was 2026-08-24 -- two different boundaries. Era 2 rows
    # from 08-22..08-24 still have chronic in P; filter by ts against the 08-24 cutover if analyzing
    # P values across that window (see docs/plans/sleep_dream_redesign.md §7 "not done, listed honestly").
    report_era(eras[1], "ERA 1 (no dark/threshold keys; pre-2026-08-22)")
    report_era(eras[2], "ERA 2 (dark/threshold present, no somatic fields; 08-22 -> J-0430)")
    report_era(eras[3], "ERA 3 (post-J-0430: somatic fields cross-logged)")
    crosscheck_era3(eras[3])
    return 0


if __name__ == "__main__":
    sys.exit(main())
