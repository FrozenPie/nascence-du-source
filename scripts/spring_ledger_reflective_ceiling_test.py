"""
spring_ledger_reflective_ceiling_test.py -- D-0051's own "real ceiling" comparison, run for the first
time (J-0936, memory_multiway_linking.md, per cognitive_geometry.md's top-of-file law: "every phase
ships with a PRE-REGISTERED metric sheet -- predictions written before the run"). Read-only over two
already-accrued stores; writes nothing.

BACKGROUND (F-1302, F-1303): D-0051 ruled that reflective mode's own named edge type
(`co_recalled_developing`, memory_multiway_linking.md §4) had never actually been built, so every
prior M2 gate-read (F-0604/F-0605/F-1302) compared reflective mode against task/relational while
reflective mode itself ran on secondary weights alone (transformed_into/dreamt_from/part_of) -- F-1302
found reflective is NOT measurably worse than task/relational despite this (7.5% vs 8.2%/7.0% prong-1
hit rate), which is ambiguous: either reflective doesn't need real edges, or its true ceiling was never
tested because the real edge type never existed to compare against. core/spring_ledger.py (built same
day, D-0051) is that real edge type's weight (`w_gated`, progress-gated Hebbian -- nudges only on the
co-recall ledger's own `developed==1` verdict, exactly what `co_recalled_developing` names). This script
asks the question D-0051 was built to make askable: does a reflective-mode new_id that ALSO carries real
`w_gated` spring backing get used by the next thought more than one that carries none?

DATA:
  - data/spring_ledger_state.json (core.spring_ledger's own state; 29,660 tracked pairs at the time this
    was written, already mature -- backfilled from the full 38,710-row data/co_recall_ledger.jsonl
    history, 2026-08-15 through today; live-forward accrual only just started this session, so the
    backfill supplies effectively all of the signal used here). Keyed `f"{a[:12]}|{b[:12]}"`
    (core/spring_ledger.py:115) -- a LOSSY 12-char truncation of each full fragment id, sorted. To ask
    "does fragment X carry real spring backing to ANYTHING", X is truncated the same way and the MAX
    `w_gated` is taken over every pair key where X's truncated form appears on either side (collision
    risk between two distinct fragment ids sharing a 12-char UUID prefix is astronomically low against
    this store's real fragment population -- ~2^44 name space per side -- and is not separately audited
    here). Using the raw stored `w_gated` as-is (last computed value for that pair, not re-decayed to
    any particular query time) since that IS what the state file represents and what the briefing names.
  - data/associative_recall_shadow.jsonl's `m2_usage` rows (`usage_by_mode.reflective`, a list of
    {fragment_id, cos_sim} per row) -- the exact same population scripts/shadow_eval.py's own
    `prong2_usage_verdict()` reads for its "reflective" line (F-1302: n=43, mean=0.294). Each entry is
    one reflective-mode new_id (a fragment the edge-aware trail surfaced beyond the plain-cosine greedy
    trail, per an earlier `m2_edge_aware` row) that got a real cosine-to-the-next-thought usage score.
    This script does not re-derive that population from `m2_edge_aware`'s own `new_ids` field -- the
    `m2_usage` rows already are that per-fragment scored join (by `parent_ts`), which is the piece
    scripts/shadow_eval.py's own docstring says was "the missing piece."

PRE-REGISTRATION (written before this script was ever run against real numbers -- the correlation below
had NOT been looked at when this paragraph was written):
  Grouping: for each of the n=43 (at pre-registration time) reflective usage-scored fragments, SPRING
    BACKED if its max real w_gated (over any pair it appears in) >= 0.3 -- F-1303's own "meaningfully
    reinforced" bar (metric 3: 418/9,208 nonzero gated pairs clear this). UNBACKED otherwise (covers
    both "never appears in spring_ledger at all" and "appears, but every pair is < 0.3").
  H1 ("the real spring meaningfully raises reflective mode's ceiling"): mean(cos_sim | BACKED) -
    mean(cos_sim | UNBACKED) >= +0.05 absolute (a moderate bar: roughly a fifth of the ~0.041-0.595
    overall observed range, F-1302) AND the 95% independent two-sample percentile bootstrap CI (10,000
    resamples, seed=42) on that difference excludes 0.
  H0 ("it doesn't matter" / the null D-0051's own ruling asked this script to be able to report
    honestly): point estimate < +0.05, or the CI includes 0.
  Pre-committed insufficient-window rule: given >=0.3 gated pairs are rare overall (418/29,660 tracked
    pairs, ~1.4%) against only 43 total scored fragments to split, if EITHER group ends up with fewer
    than 5 scored entries, the primary verdict is DECLINED (reported as WINDOW_INSUFFICIENT) rather than
    forced off too few points -- the same honesty convention scripts/shadow_eval.py already applies
    (MIN_ROWS_FOR_VERDICT / MIN_ROWS_FOR_USAGE_VERDICT), scaled down because this is a further, rarer
    join on top of an already-rare usage signal.
  Secondary / exploratory (reported regardless, never substitutes for the primary verdict): Pearson r
    between each entry's raw (unthresholded, includes 0 for no backing at all) max w_gated and its
    cos_sim, across all scored entries -- a continuous check that survives even if the binary 0.3-bar
    split above turns out underpowered.

This is a first read for a founder to grade, not a self-issued ruling -- same discipline as every other
gate-read in this plan (D-0088/D-0111/D-0119/D-0123/F-1303's own pattern).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")   # Windows console default (cp1252) can't print +/- etc.
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).parent.parent))

from core import spring_ledger as spring  # noqa: E402

_DATA = Path(__file__).parent.parent / "data"

SPRING_THRESHOLD = 0.3   # pre-registered, matches F-1303 metric 3's own "meaningfully reinforced" bar
MIN_GROUP_N = 5          # pre-registered floor per group below which the primary verdict is declined
PRIMARY_MIN_DIFF = 0.05  # pre-registered "meaningfully higher" bar for mean(backed) - mean(unbacked)


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows


def build_max_wgated_lookup() -> dict[str, float]:
    """Truncated-fragment-id -> max real w_gated over every spring_ledger pair it appears in (either
    side). See the module docstring's DATA section for the truncation/collision-risk note."""
    state = spring._load()
    lookup: dict[str, float] = {}
    for key, rec in state.items():
        w = float(rec.get("w_gated", 0.0))
        try:
            left, right = key.split("|", 1)
        except ValueError:
            continue
        for side in (left, right):
            if w > lookup.get(side, -1.0):
                lookup[side] = w
    return lookup


def collect_reflective_usage_entries(shadow_log: Path) -> list[dict]:
    """Every reflective-mode (fragment_id, cos_sim) entry ever scored by prong 2 -- the same population
    scripts/shadow_eval.py's prong2_usage_verdict() reads for its "reflective" line."""
    rows = load_jsonl(shadow_log)
    out = []
    for r in rows:
        if r.get("kind") != "m2_usage":
            continue
        for entry in ((r.get("usage_by_mode") or {}).get("reflective") or []):
            fid, cos = entry.get("fragment_id"), entry.get("cos_sim")
            if fid is None or cos is None:
                continue
            out.append({"fragment_id": fid, "cos_sim": float(cos), "parent_ts": r.get("parent_ts")})
    return out


def bootstrap_mean_diff(a: list[float], b: list[float], n_boot: int = 10000, seed: int = 42):
    """Independent (unpaired) two-sample percentile bootstrap CI for mean(a) - mean(b). numpy-only,
    same style as C:\\UDMS\\core\\udms\\eval_harness.py -- that module's own paired_bootstrap_diff
    requires two aligned same-length arrays (e.g. one row scored under two systems at once), which does
    not fit two independently-sized groups (spring-backed vs not), hence this small local sibling."""
    import numpy as np
    rng = np.random.default_rng(seed)
    arr_a, arr_b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    point = float(arr_a.mean() - arr_b.mean())
    diffs = np.empty(n_boot)
    for i in range(n_boot):
        ra = arr_a[rng.integers(0, len(arr_a), size=len(arr_a))]
        rb = arr_b[rng.integers(0, len(arr_b), size=len(arr_b))]
        diffs[i] = ra.mean() - rb.mean()
    diffs.sort()
    return point, float(diffs[int(0.025 * n_boot)]), float(diffs[int(0.975 * n_boot)])


def pearson_r(xs: list[float], ys: list[float]):
    import numpy as np
    if len(xs) < 3:
        return None
    x, y = np.asarray(xs, dtype=float), np.asarray(ys, dtype=float)
    if x.std() == 0 or y.std() == 0:
        return None
    return float(np.corrcoef(x, y)[0, 1])


def _summary(vals: list[float]) -> dict:
    if not vals:
        return {"n": 0}
    s = sorted(vals)
    n = len(s)
    return {"n": n, "mean": round(sum(vals) / n, 4), "median": round(s[n // 2], 4),
            "min": round(s[0], 4), "max": round(s[-1], 4)}


def run() -> dict:
    lookup = build_max_wgated_lookup()
    entries = collect_reflective_usage_entries(_DATA / "associative_recall_shadow.jsonl")

    for e in entries:
        trunc = str(e["fragment_id"])[:12]
        e["max_w_gated"] = lookup.get(trunc, 0.0)
        e["spring_backed"] = e["max_w_gated"] >= SPRING_THRESHOLD

    backed = [e["cos_sim"] for e in entries if e["spring_backed"]]
    unbacked = [e["cos_sim"] for e in entries if not e["spring_backed"]]

    out = {
        "n_tracked_pairs_in_spring_ledger": len(spring._load()),
        "n_total_scored": len(entries),
        "spring_threshold": SPRING_THRESHOLD,
        "min_group_n": MIN_GROUP_N,
        "primary_min_diff": PRIMARY_MIN_DIFF,
        "n_backed": len(backed),
        "n_unbacked": len(unbacked),
        "backed_summary": _summary(backed),
        "unbacked_summary": _summary(unbacked),
    }

    window_sufficient = len(backed) >= MIN_GROUP_N and len(unbacked) >= MIN_GROUP_N
    out["window_sufficient_for_primary_verdict"] = window_sufficient
    if window_sufficient:
        point, lo, hi = bootstrap_mean_diff(backed, unbacked)
        out["primary_mean_diff"] = {"point": round(point, 4), "ci_low": round(lo, 4), "ci_high": round(hi, 4)}
        if lo > 0 and point >= PRIMARY_MIN_DIFF:
            out["primary_verdict"] = "REAL_POSITIVE"
        elif lo > 0:
            out["primary_verdict"] = "CI_EXCLUDES_ZERO_BUT_BELOW_PREREGISTERED_BAR"
        else:
            out["primary_verdict"] = "NO_DETECTABLE_DIFFERENCE"
    else:
        out["primary_verdict"] = "WINDOW_INSUFFICIENT"

    # secondary / exploratory -- see docstring; never substitutes for the primary verdict above.
    all_w = [e["max_w_gated"] for e in entries]
    all_cos = [e["cos_sim"] for e in entries]
    out["secondary_pearson_r_all_entries"] = pearson_r(all_w, all_cos)
    out["secondary_n_any_spring_at_all"] = sum(1 for w in all_w if w > 0)

    out["entries"] = entries
    return out


def _print_report(v: dict) -> None:
    print("spring_ledger_reflective_ceiling_test -- D-0051's real-ceiling comparison (J-0936)")
    print(f"  spring_ledger tracked pairs: {v['n_tracked_pairs_in_spring_ledger']}")
    print(f"  reflective-mode usage-scored fragments (n): {v['n_total_scored']}")
    print(f"  spring threshold (w_gated >=): {v['spring_threshold']}   min group n for verdict: {v['min_group_n']}")
    print(f"  backed   n={v['n_backed']:3d}  {v['backed_summary']}")
    print(f"  unbacked n={v['n_unbacked']:3d}  {v['unbacked_summary']}")
    if v["window_sufficient_for_primary_verdict"]:
        d = v["primary_mean_diff"]
        print(f"  mean diff (backed - unbacked): {d['point']:+.4f}  95% CI [{d['ci_low']:+.4f}, {d['ci_high']:+.4f}]")
    print(f"  PRIMARY VERDICT: {v['primary_verdict']}")
    r = v["secondary_pearson_r_all_entries"]
    print(f"  secondary Pearson r (raw w_gated vs cos_sim, all {v['n_total_scored']} entries): "
          f"{r if r is None else round(r, 4)}")
    print(f"  secondary: entries with ANY real spring weight at all (w_gated>0): "
          f"{v['secondary_n_any_spring_at_all']}/{v['n_total_scored']}")
    print("  (no pre-registered verdict rule anywhere else settles the 0.3/0.05 bars used here -- they")
    print("   are this script's own, stated in its docstring before it was ever run; interpreting the")
    print("   result against D-0051's defeater is a founder read, same discipline as every prior gate-read.)")


if __name__ == "__main__":
    result = run()
    _print_report(result)
    print()
    print(json.dumps({k: v for k, v in result.items() if k != "entries"}, indent=2, ensure_ascii=False))
