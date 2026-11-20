"""
spring_ledger_reflective_ceiling_test_time_respecting.py -- D-0215's own defeater, path (b) (J-0948,
memory_multiway_linking.md). Read-only over already-accrued stores; writes nothing.

BACKGROUND (F-1316, D-0215): scripts/spring_ledger_reflective_ceiling_test.py (J-0936) found that a
reflective-mode new_id which ALSO carries real spring_ledger `w_gated` backing (>=0.3 to any partner) gets
used by the next thought (prong-2 usage-cosine) more than one with none -- backed mean 0.394 (n=7) vs
unbacked 0.274 (n=36), 95% CI [+0.025, +0.217]. That script's own docstring named a real caveat, not fixed
there: it looks up each fragment's `w_gated` from `data/spring_ledger_state.json`, which is TODAY's single
current snapshot -- the FINAL value after every reinforcement or decay tick that has happened since,
including any that happened AFTER the fragment was actually usage-scored. That is look-ahead bias: a
fragment could show as "backed" today only because of reinforcement that had not yet happened at the
moment its usage was measured, which would overstate the read.

This script closes that gap by REPLAYING core/spring_ledger.py's own append-only shadow log
(`data/spring_ledger_shadow.jsonl` -- ts, key, w_gated_prev, w_gated_after per activation; the exact
per-event record the state file is folded down from) to reconstruct, for each usage-scored fragment, its
real w_gated AS OF the moment `data/associative_recall_shadow.jsonl`'s matching `m2_usage` row says that
fragment was actually usage-scored -- that row's own `ts` (when `note_next_thought_for_m2_usage()` ran and
computed the cosine against the next thought), not `parent_ts` (the earlier retrieval/shadow_compare
moment) and not today. "As of T" means: the LAST logged activation for a pair with `ts <= T`, using that
row's raw `w_gated_after` exactly as recorded -- NOT further decayed forward to T itself. This is the same
convention the original script already used and named ("the raw stored w_gated as-is... not re-decayed to
any particular query time") -- kept identical on purpose so this script isolates ONLY the look-ahead fix,
not a second methodological change riding along with it.

SCOPE NOTE: this script only ever asks "what was fragment X's max real w_gated, as of some time T" for the
~30 distinct fragment ids that actually appear in the 43 reflective m2_usage entries -- so the shadow-log
replay is restricted (correctly, not approximately: any spring_ledger key that never touches one of these
fragment ids cannot affect its max-w_gated lookup at any T) to only the pair keys where one of those
fragments' truncated ids appears, rather than materialising a full point-in-time history for all ~29,660
tracked pairs.

PRE-REGISTRATION: unchanged from the original script -- same SPRING_THRESHOLD (0.3), MIN_GROUP_N (5),
PRIMARY_MIN_DIFF (0.05 abs), same bootstrap procedure (independent two-sample percentile, 10,000 resamples,
seed=42) and same H1/H0/WINDOW_INSUFFICIENT verdict rule. This is deliberately the SAME comparison as
before with ONE input corrected (today's snapshot w_gated -> time-respecting w_gated), not a fresh
pre-registration -- re-litigating the bars here would confound "did the correction change the answer" with
"did we also change what counts as an answer."

This is a first read for a founder to grade, not a self-issued ruling -- report back to D-0215 with the
new finding id per J-0948's own briefing; do not rule D-0215 from this script's result alone.
"""
from __future__ import annotations

import bisect
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

SPRING_THRESHOLD = 0.3   # unchanged from the original script -- F-1303 metric 3's "meaningfully reinforced" bar
MIN_GROUP_N = 5          # unchanged -- floor per group below which the primary verdict is declined
PRIMARY_MIN_DIFF = 0.05  # unchanged -- pre-registered "meaningfully higher" bar for mean(backed) - mean(unbacked)


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


def collect_reflective_usage_entries(shadow_log: Path) -> list[dict]:
    """Same population as the original script's collect_reflective_usage_entries -- every reflective-mode
    (fragment_id, cos_sim) entry ever scored by prong 2 -- but keeping the row's own `ts` (the usage-
    scoring moment) per entry, which the original script never needed since it only looked at today's
    snapshot."""
    rows = load_jsonl(shadow_log)
    out = []
    for r in rows:
        if r.get("kind") != "m2_usage":
            continue
        scored_ts = r.get("ts")
        for entry in ((r.get("usage_by_mode") or {}).get("reflective") or []):
            fid, cos = entry.get("fragment_id"), entry.get("cos_sim")
            if fid is None or cos is None:
                continue
            out.append({"fragment_id": fid, "cos_sim": float(cos), "scored_ts": scored_ts,
                        "parent_ts": r.get("parent_ts")})
    return out


def build_snapshot_lookup() -> dict[str, float]:
    """TODAY's snapshot lookup -- identical to the original script's build_max_wgated_lookup(). Kept here
    so this script can report the original (uncorrected) read side by side with the time-respecting one,
    making any divergence directly visible rather than asserted."""
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


def build_time_respecting_history(shadow_log: Path, target_truncs: set[str]) -> dict[str, list]:
    """One pass over core/spring_ledger.py's own activation log. Returns {key: [(ts, w_gated_after), ...]}
    sorted ascending by ts, restricted to keys where at least one side is in `target_truncs` (see the
    module docstring's SCOPE NOTE -- this restriction is exact, not an approximation)."""
    history: dict[str, list] = {}
    if not shadow_log.exists():
        return history
    with open(shadow_log, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if "skip" in r:  # same convention as core/spring_ledger.py's own status(): skip rows carry no w_gated
                continue
            key = r.get("key")
            if not key or "|" not in key:
                continue
            left, right = key.split("|", 1)
            if left not in target_truncs and right not in target_truncs:
                continue
            ts, w_after = r.get("ts"), r.get("w_gated_after")
            if ts is None or w_after is None:
                continue
            history.setdefault(key, []).append((ts, float(w_after)))
    for lst in history.values():
        lst.sort(key=lambda p: p[0])
    return history


def build_reverse_index(history: dict[str, list]) -> dict[str, list[str]]:
    rev: dict[str, list[str]] = {}
    for key in history:
        left, right = key.split("|", 1)
        rev.setdefault(left, []).append(key)
        rev.setdefault(right, []).append(key)
    return rev


def value_at_or_before(ts_val_pairs: list, T: float):
    """Last (ts, val) with ts <= T, or None if the pair had not yet been activated as of T."""
    ts_only = [p[0] for p in ts_val_pairs]
    idx = bisect.bisect_right(ts_only, T) - 1
    if idx < 0:
        return None
    return ts_val_pairs[idx][1]


def max_w_gated_as_of(trunc: str, T: float, history: dict[str, list], rev: dict[str, list[str]]) -> float:
    """Max real w_gated over every spring_ledger pair `trunc` appears in, AS OF time T -- the time-
    respecting analogue of the original script's lookup.get(trunc, 0.0). Defaults to 0.0 if `trunc` never
    appears in any pair, or every pair it appears in was not yet activated as of T."""
    best = 0.0
    for key in rev.get(trunc, []):
        v = value_at_or_before(history[key], T)
        if v is not None and v > best:
            best = v
    return best


def bootstrap_mean_diff(a: list[float], b: list[float], n_boot: int = 10000, seed: int = 42):
    """Independent (unpaired) two-sample percentile bootstrap CI for mean(a) - mean(b). Identical to the
    original script's own copy (see that script's docstring for why this is a small local sibling of
    C:\\UDMS\\core\\udms\\eval_harness.py's paired_bootstrap_diff rather than a reuse of it)."""
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


def _verdict(backed: list[float], unbacked: list[float]) -> dict:
    out = {"n_backed": len(backed), "n_unbacked": len(unbacked),
           "backed_summary": _summary(backed), "unbacked_summary": _summary(unbacked)}
    sufficient = len(backed) >= MIN_GROUP_N and len(unbacked) >= MIN_GROUP_N
    out["window_sufficient_for_primary_verdict"] = sufficient
    if sufficient:
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
    return out


def run() -> dict:
    entries = collect_reflective_usage_entries(_DATA / "associative_recall_shadow.jsonl")
    target_truncs = {str(e["fragment_id"])[:12] for e in entries}

    snapshot_lookup = build_snapshot_lookup()
    history = build_time_respecting_history(_DATA / "spring_ledger_shadow.jsonl", target_truncs)
    rev = build_reverse_index(history)

    for e in entries:
        trunc = str(e["fragment_id"])[:12]
        e["max_w_gated_snapshot"] = snapshot_lookup.get(trunc, 0.0)
        e["spring_backed_snapshot"] = e["max_w_gated_snapshot"] >= SPRING_THRESHOLD
        e["max_w_gated_time_respecting"] = max_w_gated_as_of(trunc, e["scored_ts"], history, rev)
        e["spring_backed_time_respecting"] = e["max_w_gated_time_respecting"] >= SPRING_THRESHOLD
        e["w_gated_value_changed_since_scoring"] = (
            abs(e["max_w_gated_snapshot"] - e["max_w_gated_time_respecting"]) > 1e-9)

    snap_backed = [e["cos_sim"] for e in entries if e["spring_backed_snapshot"]]
    snap_unbacked = [e["cos_sim"] for e in entries if not e["spring_backed_snapshot"]]
    tr_backed = [e["cos_sim"] for e in entries if e["spring_backed_time_respecting"]]
    tr_unbacked = [e["cos_sim"] for e in entries if not e["spring_backed_time_respecting"]]

    out = {
        "n_total_scored": len(entries),
        "n_distinct_fragment_ids": len(target_truncs),
        "n_relevant_spring_ledger_keys_replayed": len(history),
        "spring_threshold": SPRING_THRESHOLD,
        "min_group_n": MIN_GROUP_N,
        "primary_min_diff": PRIMARY_MIN_DIFF,
        "snapshot_read_today_uncorrected": _verdict(snap_backed, snap_unbacked),
        "time_respecting_read_corrected": _verdict(tr_backed, tr_unbacked),
    }

    # classification-level + value-level divergence, reported honestly regardless of which way it cuts
    flipped = [e["fragment_id"] for e in entries
               if e["spring_backed_snapshot"] != e["spring_backed_time_respecting"]]
    out["n_entries_where_backed_classification_flipped"] = len(flipped)
    out["n_entries_where_raw_w_gated_value_changed"] = sum(
        1 for e in entries if e["w_gated_value_changed_since_scoring"])

    all_w_snap = [e["max_w_gated_snapshot"] for e in entries]
    all_w_tr = [e["max_w_gated_time_respecting"] for e in entries]
    all_cos = [e["cos_sim"] for e in entries]
    out["secondary_pearson_r_snapshot"] = pearson_r(all_w_snap, all_cos)
    out["secondary_pearson_r_time_respecting"] = pearson_r(all_w_tr, all_cos)

    out["entries"] = entries
    return out


def _print_report(v: dict) -> None:
    print("spring_ledger_reflective_ceiling_test_time_respecting -- D-0215 defeater path (b) (J-0948)")
    print(f"  reflective-mode usage-scored fragments (n): {v['n_total_scored']}  "
          f"distinct fragment ids: {v['n_distinct_fragment_ids']}  "
          f"spring_ledger keys replayed: {v['n_relevant_spring_ledger_keys_replayed']}")
    print(f"  spring threshold (w_gated >=): {v['spring_threshold']}   min group n: {v['min_group_n']}   "
          f"primary min diff: {v['primary_min_diff']}")
    print()
    for label, key in (("SNAPSHOT (today, uncorrected -- F-1316's original read)", "snapshot_read_today_uncorrected"),
                        ("TIME-RESPECTING (as-of-scoring-moment -- this job's corrected read)", "time_respecting_read_corrected")):
        r = v[key]
        print(f"  {label}:")
        print(f"    backed   n={r['n_backed']:3d}  {r['backed_summary']}")
        print(f"    unbacked n={r['n_unbacked']:3d}  {r['unbacked_summary']}")
        if r["window_sufficient_for_primary_verdict"]:
            d = r["primary_mean_diff"]
            print(f"    mean diff (backed - unbacked): {d['point']:+.4f}  95% CI [{d['ci_low']:+.4f}, {d['ci_high']:+.4f}]")
        print(f"    PRIMARY VERDICT: {r['primary_verdict']}")
        print()
    print(f"  entries where backed/unbacked classification FLIPPED between snapshot and time-respecting: "
          f"{v['n_entries_where_backed_classification_flipped']} / {v['n_total_scored']}")
    print(f"  entries where the raw w_gated VALUE differs (even if same side of the 0.3 bar): "
          f"{v['n_entries_where_raw_w_gated_value_changed']} / {v['n_total_scored']}")
    print(f"  secondary Pearson r -- snapshot: {round(v['secondary_pearson_r_snapshot'], 4)}   "
          f"time-respecting: {round(v['secondary_pearson_r_time_respecting'], 4)}")
    print("  (bars unchanged from scripts/spring_ledger_reflective_ceiling_test.py's own pre-registration;")
    print("   interpreting this against D-0215's defeater is a founder read, same discipline as every")
    print("   prior gate-read in this plan.)")


if __name__ == "__main__":
    result = run()
    _print_report(result)
    print()
    print(json.dumps({k: v for k, v in result.items() if k != "entries"}, indent=2, ensure_ascii=False))
