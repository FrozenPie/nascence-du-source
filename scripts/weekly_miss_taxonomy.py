"""
weekly_miss_taxonomy.py — Trial 2 of docs/staged/udms_du_capability_trials.md (J-0318)
========================================================================================
F-0402's first pass reproduced test_l's aggregate split (91.5/5.1/3.4 near-miss/environmental/
blindspot) and killed its naive "surprise" reading (state delta is SMALLER on a miss than a hit).
Open question this trial answers: is that split STABLE week to week, or does it move around --
and do blindspot misses actually differ from near-misses on graph distance (the affinity score),
which would argue self_surprise SHOULD scale by miss kind?

Reuses test_l's exact classification thresholds and SpectralDiffusionEngine (imported, not
reimplemented) — only the aggregation changes: real calendar weeks instead of one 70/30 split.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(r"C:\UDMS")))
from core.math.spectral_diffusion import SpectralDiffusionEngine  # noqa: E402

DATA = Path(__file__).parent.parent / "data" / "geometry_tuples.jsonl"
TRAIN_FRAC = 0.30   # build the graph from an early prefix, classify the whole remaining span by week
NEAR_MISS_AFFINITY_THR = 0.04
ENV_SHIFT_DELTA_THR = 0.40


def extract(t: dict) -> tuple[dict, list[str], dict]:
    body = t.get("body") or {}
    affect = t.get("affect") or {}
    state = {"uncertainty": 1.0 - affect.get("valence", 0.5), "tension": body.get("tension", 0.1),
             "contradiction": 0.8 if t.get("unresolved") else 0.1, "incoherence": 1.0 - t.get("level", 0.5),
             "energy": body.get("energy", 0.5), "arousal": affect.get("arousal", 0.3)}
    concepts = []
    place, weather = t.get("place", ""), t.get("weather", "")
    if place: concepts.append(place)
    if weather: concepts.append(weather)
    if t.get("fire"): concepts.append(f"fire_{t['fire']}")
    sounds = t.get("sounds", [])
    if isinstance(sounds, list): concepts.extend(sounds)
    objects = t.get("objects", {})
    if isinstance(objects, dict):
        cat = objects.get("cat", {})
        if isinstance(cat, dict) and cat.get("location"):
            concepts.append(f"cat_{cat['location']}")
    meta = {"ts": t.get("ts", 0.0), "place": place, "weather": weather}
    return state, concepts, meta


def load_sorted() -> list[dict]:
    rows = []
    with open(DATA, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    rows.sort(key=lambda t: t.get("ts", 0.0))
    return rows


def week_key(ts: float) -> str:
    d = datetime.fromtimestamp(ts, tz=timezone.utc)
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def main() -> None:
    rows = load_sorted()
    n = len(rows)
    parsed = [extract(t) for t in rows]
    states, concepts, metas = [p[0] for p in parsed], [p[1] for p in parsed], [p[2] for p in parsed]

    split_idx = int(n * TRAIN_FRAC)
    train_concepts = concepts[:split_idx]
    print(f"loaded {n} tuples; training graph on first {split_idx} ({TRAIN_FRAC*100:.0f}%), "
          f"classifying the remaining {n - split_idx} by real calendar week")

    cooc = defaultdict(lambda: defaultdict(float))
    for cs in train_concepts:
        for i in range(len(cs)):
            for j in range(i + 1, len(cs)):
                cooc[cs[i]][cs[j]] += 1.0
                cooc[cs[j]][cs[i]] += 1.0
    seen, edge_list = set(), []
    for u, nbrs in cooc.items():
        for v, w in nbrs.items():
            key = tuple(sorted([u, v]))
            if key not in seen:
                seen.add(key)
                edge_list.append((u, v, w))
    engine = SpectralDiffusionEngine()
    engine.build_graph_from_edges(edge_list)
    print(f"graph: {engine.n_nodes} nodes, {len(edge_list)} edges")

    by_week = defaultdict(lambda: {"near_miss": 0, "env_shift": 0, "blindspot": 0, "hits": 0,
                                    "affinity_blindspot": [], "affinity_near_miss": []})

    for i in range(split_idx, n - 1):
        cur_c, next_c = concepts[i], concepts[i + 1]
        known = [c for c in cur_c if c in engine.node_to_idx]
        if not known or not next_c:
            continue
        anchor = known[0]
        recs = engine.diffuse([anchor], t=1.5, top_k=2)
        pred = recs[1][0] if (len(recs) > 1 and recs[0][0] == anchor) else (recs[0][0] if recs else anchor)
        wk = week_key(metas[i]["ts"])

        if pred in next_c:
            by_week[wk]["hits"] += 1
            continue

        s_cur, s_next = np.array(list(states[i].values())), np.array(list(states[i + 1].values()))
        s_delta = float(np.linalg.norm(s_next - s_cur))
        affinity = 0.0
        if pred in engine.node_to_idx:
            diff = dict(engine.diffuse([pred], t=1.5, top_k=10))
            for target in next_c:
                if target in diff:
                    affinity = max(affinity, diff[target])
        weather_changed = metas[i]["weather"] != metas[i + 1]["weather"]
        place_changed = metas[i]["place"] != metas[i + 1]["place"]
        is_env = weather_changed or place_changed or (s_delta > ENV_SHIFT_DELTA_THR)

        if affinity > NEAR_MISS_AFFINITY_THR:
            by_week[wk]["near_miss"] += 1
            by_week[wk]["affinity_near_miss"].append(affinity)
        elif is_env:
            by_week[wk]["env_shift"] += 1
        else:
            by_week[wk]["blindspot"] += 1
            by_week[wk]["affinity_blindspot"].append(affinity)

    weeks = sorted(by_week.keys())
    print(f"\n{len(weeks)} weeks with data\n")
    print(f"{'week':10s} {'n_miss':>7s} {'near%':>7s} {'env%':>6s} {'blind%':>7s}")
    near_pcts, blind_pcts = [], []
    for wk in weeks:
        d = by_week[wk]
        n_miss = d["near_miss"] + d["env_shift"] + d["blindspot"]
        if n_miss == 0:
            continue
        near_pct = d["near_miss"] / n_miss * 100
        env_pct = d["env_shift"] / n_miss * 100
        blind_pct = d["blindspot"] / n_miss * 100
        near_pcts.append(near_pct)
        blind_pcts.append(blind_pct)
        print(f"{wk:10s} {n_miss:7d} {near_pct:6.1f}% {env_pct:5.1f}% {blind_pct:6.1f}%")

    print(f"\nnear-miss %% across weeks: min={min(near_pcts):.1f} max={max(near_pcts):.1f} "
          f"mean={np.mean(near_pcts):.1f} std={np.std(near_pcts):.1f}")
    print(f"blindspot %% across weeks: min={min(blind_pcts):.1f} max={max(blind_pcts):.1f} "
          f"mean={np.mean(blind_pcts):.1f} std={np.std(blind_pcts):.1f}")

    all_near_aff = [a for d in by_week.values() for a in d["affinity_near_miss"]]
    all_blind_aff = [a for d in by_week.values() for a in d["affinity_blindspot"]]
    print(f"\naffinity (graph distance proxy) near-miss: mean={np.mean(all_near_aff):.4f} "
          f"(n={len(all_near_aff)})")
    print(f"affinity blindspot:                        mean={np.mean(all_blind_aff):.4f} "
          f"(n={len(all_blind_aff)}, threshold={NEAR_MISS_AFFINITY_THR})")

    stable = (max(near_pcts) - min(near_pcts)) < 24   # matches the plan's own 85-97% band width
    print(f"\n-> {'STABLE' if stable else 'UNSTABLE'}: near-miss share range is "
          f"{max(near_pcts) - min(near_pcts):.1f}pp across weeks (bar: <24pp, the 85-97% band width)")


if __name__ == "__main__":
    main()
