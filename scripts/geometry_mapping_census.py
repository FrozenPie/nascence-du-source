"""
Nascence — THE MAPPING CENSUS (CLI): analyzer over accrued geometry tuples. Thin wrapper over
core.mapping_census. See cognitive_geometry.md §5.4 and core/mapping_census.py's module docstring.

READ-ONLY: reads data/geometry_tuples.jsonl only. Appends one summary row to
data/mapping_census_log.jsonl (the longitudinal record, mirroring stick_test.py's pattern) unless
--no-log is passed. Safe to run any time, live sim running or not.

Usage:
    python scripts/geometry_mapping_census.py                  # full census incl. marginal reach
    python scripts/geometry_mapping_census.py --fast            # skip marginal reach (no MiniLM load)
    python scripts/geometry_mapping_census.py --sample-n 400    # smaller marginal-reach sample
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from core import mapping_census as mc   # noqa: E402


def _print_fanout(fanout: dict) -> None:
    print("\n=== 1. FAN-OUT (source-space -> target-space, effective #targets per source value) ===")
    ranked = sorted(fanout.items(), key=lambda kv: -kv[1]["mean_effective_fanout"])
    for pair, d in ranked[:15]:
        print(f"  {pair:34} tested={d['tested_values']:3}  mean_effective_fanout={d['mean_effective_fanout']}")
    if len(ranked) > 15:
        print(f"  ... {len(ranked) - 15} more pairs (see JSON dump for full table)")


def _print_split_half(sh: dict) -> None:
    s = sh["summary"]
    print("\n=== 2. SPLIT-HALF STABILITY (TVD of P(target|source) across chronological halves; 0=stable, 1=noise) ===")
    print(f"  pairs tested: {s['pairs_tested']}  ·  source-values tested: {s['n_a_values_tested']}  ·  "
          f"overall mean TVD: {s['overall_mean_tvd']}")
    worst = sorted(sh["by_pair"].items(), key=lambda kv: -kv[1]["mean_tvd"])[:5]
    best = sorted(sh["by_pair"].items(), key=lambda kv: kv[1]["mean_tvd"])[:5]
    print("  most stable pairs:")
    for pair, d in best:
        print(f"    {pair:24} mean_tvd={d['mean_tvd']}  (n_values={d['tested_values']})")
    print("  least stable pairs:")
    for pair, d in worst:
        print(f"    {pair:24} mean_tvd={d['mean_tvd']}  (n_values={d['tested_values']})")


def _print_state_conditioning(sc: dict) -> None:
    print("\n=== 3. STATE-CONDITIONING (observed vs permutation-null TVD; z >~2 = likely real, not noise) ===")
    for k, d in sc.items():
        if d.get("insufficient_data"):
            print(f"  {k:26} insufficient data (n={d['n']})")
            continue
        flag = "  <-- likely real" if (d["z"] or 0) >= 2 else ""
        print(f"  {k:26} n={d['n']:5}  observed={d['observed_tvd']}  null={d['null_mean_tvd']}"
              f"±{d['null_std_tvd']}  z={d['z']}{flag}")


def _print_funnel(fn: dict) -> None:
    print("\n=== 4. THE FUNNEL (fan-in concentration; top_value_share ~1.0 = everything collapses to one region) ===")
    for space, d in sorted(fn.items(), key=lambda kv: -kv[1]["top_value_share"]):
        print(f"  {space:18} top='{d['top_value']}'  share={d['top_value_share']}  "
              f"herfindahl={d['herfindahl']}  distinct={d['distinct_values']}  n={d['n']}")


def _print_marginal_reach(mr: dict) -> None:
    print("\n=== 5. KILL CRITERION #6 — MARGINAL REACH (geometry neighbours a widened text-cosine search misses) ===")
    if "error" in mr:
        print(f"  FAILED: {mr['error']}")
        return
    print(f"  sample_n={mr['sample_n']}  k={mr['k']}  wide_k={mr['wide_k']}")
    print(f"  mean_overlap_at_k (geometry vs text top-K): {mr['mean_overlap_at_k']}")
    print(f"  mean_marginal_reach_fraction: {mr['mean_marginal_reach_fraction']}")
    print(f"  {mr['note']}")
    print(f"\n  CAVEAT: {mr['caveat']}")
    print("\n  founder-read examples (query thought -> its top geometry neighbour vs its top text-cosine neighbour):")
    for ex in mr.get("examples", []):
        print(f"    Q:     {ex['query_thought']!r}")
        print(f"    GEOM ({','.join(ex['matched_on']) or 'no shared fields'}): {ex['top_geometry_neighbour_thought']!r}")
        print(f"    TEXT:  {ex['top_text_cosine_neighbour_thought']!r}")
        print()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true", help="skip marginal reach (kill criterion #6) — no MiniLM load")
    ap.add_argument("--sample-n", type=int, default=700, help="tuples sampled for marginal reach")
    ap.add_argument("--no-log", action="store_true", help="don't append to data/mapping_census_log.jsonl")
    ap.add_argument("--json", action="store_true", help="dump full result as JSON instead of the printed report")
    ap.add_argument("--dedupe", action="store_true",
                     help="NEW comparison lens (F-1259/J-0898): collapse contiguous frozen same-source "
                          "bursts (byte-identical tension/energy/valence/arousal/level vs the immediately "
                          "preceding row) into one representative row each before computing fan-out/"
                          "stability/state-conditioning/funnel. Omit for the original, unchanged, "
                          "un-deduplicated codepath (the default).")
    args = ap.parse_args()

    res = mc.census(sample_n=args.sample_n, run_marginal_reach=not args.fast, dedupe=args.dedupe)
    if not res.get("rows"):
        print("mapping census: no data (data/geometry_tuples.jsonl unreadable or empty?)")
        sys.exit(0)

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2, default=str))
    else:
        header = f"MAPPING CENSUS — {res['rows']} tuples over {res['span_days']} days (cognitive_geometry.md §5.4)"
        if res.get("dedupe"):
            header += f"  [DE-DUPED from {res.get('raw_rows')} raw rows -- frozen-burst lens, F-1259/J-0898]"
        print(header)
        _print_fanout(res["fanout"])
        _print_split_half(res["split_half_stability"])
        _print_state_conditioning(res["state_conditioning"])
        _print_funnel(res["funnel"])
        if "marginal_reach" in res:
            _print_marginal_reach(res["marginal_reach"])
        print("\nPRE-REGISTERED PREDICTION (plan §5.5 #6, kill criterion): cross-space/tuple retrieval "
              "reaches meaningfully beyond cosine top-K. If ~0 -> the edge layer is redundant, RE-SCOPE.")

    if not args.no_log:
        row = mc.snapshot(res)
        if row is not None:
            print(f"\n[census row appended to {mc._LOG.name} — the longitudinal record]")
        else:
            print("\n[log append failed]")


if __name__ == "__main__":
    main()
