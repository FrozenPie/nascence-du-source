"""
hodge_rumination_groundtruth_validate.py — J-0330, part 2 of Trial 5 (F-0418 lineage)
=======================================================================================
Ground-truth source: the 25 post-restart-epoch pursuit_return guidance injections already
hand-classified by F-0468 (data/guidance_injection_log.jsonl, notes matching the
pursuit_return template; ts > 1787604229). wandering_log.jsonl's 'via' field was already
ruled out (core/wandering.py:95-120 explicitly excludes near-duplicate/echo hops).

Label operationalization (real, not invented): F-0468 found the SAME source anchor quoted
verbatim across multiple pursuit_return injections -- the pursuit-selection layer re-picking
an unresolved thread it already picked before. That is a genuine, independently-observed
rumination signal (looping at the pursuit-tracker level), distinct from a fresh/novel anchor
being introduced. So:
  REPEAT  = this injection's OPEN anchor text (first ~90 chars) has already appeared earlier
            in this same post-restart list  -> rumination-shaped
  NOVEL   = first appearance of this anchor in the post-restart list -> exploratory-shaped
(NOVEL is a weak label -- it just means "not yet observed to loop", not "definitely
exploratory" -- flagged honestly in the writeup, not hidden.)

For each of the 25 events: take the 5 geometry_tuples.jsonl entries with ts nearest at-or-
after the injection ts (same window_size=5 the Trial-5 threshold search uses), extract the
SAME 7-dim state vector (body energy/fatigue/tension, affect valence/arousal, fire_fuel,
level) test_c/hodge_threshold_search already use, and run the real unbroken
DiscreteHodgeGovernor.evaluate_thought_trajectory over it to get curl_ratio (threshold-
independent -- confirmed by reading hodge_governor.py directly, curl_ratio is computed before
the threshold comparison).

Compares mean curl_ratio(REPEAT) vs mean curl_ratio(NOVEL) with an unpaired bootstrap CI on
the difference (2000 resamples, using the same np-only bootstrap approach as UDMS's own
eval_harness.bootstrap_ci, since paired_bootstrap_diff there assumes equal-length aligned
arrays which REPEAT/NOVEL are not).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(r"C:\UDMS")))
from core.math.hodge_governor import DiscreteHodgeGovernor  # noqa: E402

GEOM = Path(__file__).parent.parent / "data" / "geometry_tuples.jsonl"
INJ = Path(__file__).parent.parent / "data" / "guidance_injection_log.jsonl"
RESTART_EPOCH = 1787604229


def extract_state_vector(t: dict) -> np.ndarray:
    body = t.get("body") or {}
    affect = t.get("affect") or {}
    return np.array([
        body.get("energy", 0.5),
        body.get("fatigue", 0.0),
        body.get("tension", 0.0),
        affect.get("valence", 0.5),
        affect.get("arousal", 0.5),
        t.get("fire_fuel", 0.0),
        t.get("level", 0.5),
    ])


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def main() -> None:
    inj = load_jsonl(INJ)
    pursuit = [
        r for r in inj
        if ("thread of yours" in r.get("note", "") or "open question" in r.get("note", "")
            or "working something through" in r.get("note", ""))
    ]
    post = sorted([r for r in pursuit if r["ts"] > RESTART_EPOCH], key=lambda r: r["ts"])
    print(f"post-restart pursuit_return events: {len(post)}")

    seen_anchors = set()
    labels = []
    for r in post:
        anchor = r["note"][:90]
        label = "REPEAT" if anchor in seen_anchors else "NOVEL"
        seen_anchors.add(anchor)
        labels.append(label)
    n_repeat = labels.count("REPEAT")
    n_novel = labels.count("NOVEL")
    print(f"REPEAT (rumination-shaped, anchor seen before): {n_repeat}")
    print(f"NOVEL  (first appearance of anchor):             {n_novel}")

    geom = load_jsonl(GEOM)
    geom.sort(key=lambda t: t.get("ts", 0.0))
    geom_ts = np.array([t.get("ts", 0.0) for t in geom])

    gov = DiscreteHodgeGovernor()
    curl_repeat, curl_novel = [], []
    matched = 0
    for r, label in zip(post, labels):
        ts = r["ts"]
        idx = int(np.searchsorted(geom_ts, ts))
        if idx >= len(geom) - 4:
            continue
        window = [extract_state_vector(geom[idx + i]) for i in range(5)]
        res = gov.evaluate_thought_trajectory(window)
        matched += 1
        if label == "REPEAT":
            curl_repeat.append(res["curl_ratio"])
        else:
            curl_novel.append(res["curl_ratio"])

    print(f"\nmatched to geometry_tuples windows: {matched}/{len(post)}")
    print(f"curl_ratio REPEAT (n={len(curl_repeat)}): {curl_repeat}")
    print(f"curl_ratio NOVEL  (n={len(curl_novel)}): {curl_novel}")

    if not curl_repeat or not curl_novel:
        print("\nINSUFFICIENT: one group empty, cannot compare.")
        return

    mean_r = float(np.mean(curl_repeat))
    mean_n = float(np.mean(curl_novel))
    print(f"\nmean curl_ratio REPEAT = {mean_r:.4f}")
    print(f"mean curl_ratio NOVEL  = {mean_n:.4f}")
    print(f"observed separation (REPEAT - NOVEL) = {mean_r - mean_n:.4f}")

    rng = np.random.default_rng(42)
    cr = np.array(curl_repeat)
    cn = np.array(curl_novel)
    n_boot = 2000
    diffs = np.empty(n_boot)
    for i in range(n_boot):
        br = cr[rng.integers(0, len(cr), size=len(cr))]
        bn = cn[rng.integers(0, len(cn), size=len(cn))]
        diffs[i] = br.mean() - bn.mean()
    ci_lo, ci_hi = np.percentile(diffs, [2.5, 97.5])
    print(f"bootstrap 95% CI on (REPEAT - NOVEL) mean diff: ({ci_lo:.4f}, {ci_hi:.4f})")
    separates = not (ci_lo <= 0 <= ci_hi)
    print(f"\n{'SEPARATES (CI excludes 0)' if separates else 'DOES NOT SEPARATE (CI includes 0)'}")


if __name__ == "__main__":
    main()
