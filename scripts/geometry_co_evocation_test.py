"""
J-0463 (D-0111): the third, differently-shaped realness test for cognitive_geometry's cross-space
edge layer — the "co-evocation" instrument.

WHY THIS IS A GENUINELY DIFFERENT SHAPE, NOT A THIRD RE-READ (see docs/plans/cognitive_geometry.md
Current State, D-0111's own ruling):
  - F-0501 (marginal reach, kill criterion #6): SET-OVERLAP question — does a geometry top-K neighbour
    set reach outside a widened text-cosine top-K set? Data: data/geometry_tuples.jsonl (per-THOUGHT
    idle-cycle snapshots). Comparator: text beats/loses a coverage race.
  - F-0635 (sec5.3 felt-response/co-recall realness test): PREDICTIVE-ACCURACY question — does
    geometry-distance kNN out-predict text-distance kNN on restate_sim / developed? Same data source,
    same kNN-vs-text horse-race shape, different outcome variables.
  - THIS TEST asks a third, disjoint question from sec5.3's own wording ("co-evocation, co-recall,
    felt response" -- co-evocation is the one neither prior test operationalised): when Du's REAL
    production cognition recalls multiple memory fragments TOGETHER in one step (data/co_recall_
    ledger.jsonl, n_ids>=2 -- real behaviour that already happened, not a constructed kNN benchmark),
    do the co-recalled fragments share MORE geometric context with each other than chance would
    predict? This is a COHESION/PERMUTATION-NULL test on REAL recall groups, not a distance-predicts-
    outcome regression, and it does not pit geometry against text at all as its primary comparator --
    text is run as a PARALLEL, not competing, control arm. Data source is also new: `fragment_context`
    (a per-FRAGMENT-at-creation-time context row keyed to fragment_id, joined via SQL to memory_
    fragments.embedding) rather than geometry_tuples.jsonl's per-THOUGHT-event log.

READ-ONLY: reads data/co_recall_ledger.jsonl and, via a read-only ("mode=ro") SQLite connection,
memory_fragments.embedding and fragment_context.* from data/memory/nascence.db. Writes nothing to the
DB or any live store; only this script's own report file under docs/lab/.

PRE-REGISTERED DESIGN (written before results were read):

Fields compared per fragment ("context spaces", from fragment_context, chosen for real coverage --
see docs/lab/ for the coverage audit run before writing this): place, weather, fire, light_band,
standpoint, cat_at, held (JSON list -> frozenset), sounds (JSON list -> frozenset), affect_quadrant
(binned from valence/arousal at 0.5, same convention as core/mapping_census.extract_regions).

coherence(a, b) = (# shared-populated fields where a and b AGREE) / (# shared-populated fields), over
fields where BOTH fragments have a non-null value. Undefined (None) if fewer than 2 fields are shared-
populated for that pair.

For each real co-recall event (ids all present in fragment_context, n_ids>=2): event_score = mean
coherence(a,b) over all C(n,2) fragment pairs with a defined coherence (skip undefined pairs).
observed_geom = mean(event_score) over all qualifying events (unweighted by group size).
observed_text = the same statistic using cosine(embedding_a, embedding_b) in place of coherence()
(embeddings are the system's own precomputed MiniLM vectors, memory_fragments.embedding -- no re-
encoding needed, no risk of a different model introducing spurious differences from F-0501/F-0428/
F-0635's MiniLM baseline).

NULL (permutation, mirroring core.mapping_census.state_conditioning's existing permutation-null
methodology -- the same bar for "differs beyond chance" this project already accepts): for each of
N_PERM iterations, for every real event of size m, draw m distinct fragment ids UNIFORMLY AT RANDOM
from the full eligible pool (all fragment_ids with both fragment_context and an embedding) and compute
the same event_score; aggregate the per-permutation mean over all events -> one null sample. z-score
and one-sided permutation p-value (fraction of null samples >= observed) computed for both geom and
text arms.

ROBUSTNESS SPLIT (pre-registered, guards the exact "book/time" confound cognitive_geometry.md already
flagged for a different pair): the same test is re-run on two disjoint event subsets by the time-span
of the group's own fragments (max(tuple_ts) - min(tuple_ts)): NEAR-TERM (< 1 day) and LONG-RANGE
(>= 1 day). If coherence is real only in the near-term subset, that is the same "tracks slow time, not
real coupling" read this plan already gave `book` -- weak evidence. If coherence survives on the
LONG-RANGE subset (fragments recalled together despite being formed in genuinely different life
periods), that is a materially stronger, non-trivial signal.

PRE-REGISTERED VERDICT RULE (stated before running):
  PASS (real co-evocation signal, reopens P1/P2 for founder consideration) iff geom z >= 2.0
    (permutation p < 0.05) on the FULL sample AND on the LONG-RANGE (>=1 day) subset specifically --
    i.e. not explained away by same-session recency alone.
  MIXED iff geom is significant on the full sample but NOT on the long-range subset (the recency-
    confound read).
  FAIL iff geom is not significant (z < 2.0) on the full sample at all.
  The text arm is reported for context (do co-recalled fragments ALSO cohere in text, as expected
  since retrieval is itself text/embedding-driven) but does not gate the verdict -- this test's
  question is whether GEOMETRIC coherence is present in real recall groups at all, not whether it
  out-competes text (that horse race is what F-0635 already ran and settled negatively).

Usage: python scripts/geometry_co_evocation_test.py [--n_perm 200] [--seed 42]
"""
from __future__ import annotations

import argparse
import json
import random
import sqlite3
import sys
import time
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.memory_edges import _is_shadow_source   # J-1754: the one definition of "a would-have-shown row" (J-1738)

_ROOT = Path(__file__).parent.parent
_DATA = _ROOT / "data"
_DB = _DATA / "memory" / "nascence.db"
_LEDGER = _DATA / "co_recall_ledger.jsonl"

FIELDS = ["place", "weather", "fire", "light_band", "standpoint", "cat_at", "held_set",
          "sounds_set", "affect_quadrant"]


def _load_ledger() -> list[dict]:
    rows = []
    with open(_LEDGER, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            # J-1754 (F-2372 sibling of J-1738): a "*_shadow" row (D-0289 monologue_shadow, D-0292
            # divergent_shadow) is the fragments a switched-off path WOULD have shown -- never recalled together
            # in a thought, so not a "real recall group" for this test's question. Every real source still counts.
            if r.get("n_ids", 0) >= 2 and r.get("ids") and not _is_shadow_source(r.get("source")):
                rows.append(r)
    return rows


def _affect_quadrant(valence, arousal):
    if valence is None or arousal is None:
        return None
    return ("V+" if valence >= 0.5 else "V-") + ("A+" if arousal >= 0.5 else "A-")


def _load_fragment_data(conn: sqlite3.Connection) -> tuple[dict, dict]:
    """Returns (regions, embeddings) both keyed by fragment_id, restricted to fragments that have
    BOTH a fragment_context row and a stored embedding (the eligible pool)."""
    cur = conn.cursor()
    cur.execute("""SELECT fragment_id, tuple_ts, place, weather, fire, light_band, standpoint,
                          cat_at, held, sounds, valence, arousal
                   FROM fragment_context""")
    regions: dict[str, dict] = {}
    ts_by_id: dict[str, float] = {}
    for row in cur.fetchall():
        (fid, tuple_ts, place, weather, fire, light_band, standpoint, cat_at, held, sounds,
         valence, arousal) = row
        held_set = frozenset(json.loads(held)) if held else None
        sounds_set = frozenset(json.loads(sounds)) if sounds else None
        regions[fid] = {
            "place": place, "weather": weather, "fire": fire, "light_band": light_band,
            "standpoint": standpoint, "cat_at": cat_at, "held_set": held_set,
            "sounds_set": sounds_set, "affect_quadrant": _affect_quadrant(valence, arousal),
        }
        if tuple_ts is not None:
            ts_by_id[fid] = tuple_ts

    cur.execute("SELECT fragment_id, embedding FROM memory_fragments WHERE embedding IS NOT NULL")
    import numpy as np
    embeddings: dict[str, "np.ndarray"] = {}
    for fid, blob in cur.fetchall():
        if fid in regions:
            embeddings[fid] = np.frombuffer(blob, dtype="float32")

    # restrict regions to the fragments that also have an embedding (the true eligible pool)
    regions = {fid: r for fid, r in regions.items() if fid in embeddings}
    for fid, ts in ts_by_id.items():
        if fid in regions:
            regions[fid]["_tuple_ts"] = ts
    return regions, embeddings


def _coherence(a: dict, b: dict) -> float | None:
    shared = [f for f in FIELDS if a.get(f) is not None and b.get(f) is not None]
    if len(shared) < 2:
        return None
    agree = sum(1 for f in shared if a[f] == b[f])
    return agree / len(shared)


def _text_sim(emb_a, emb_b) -> float:
    import numpy as np
    return float(np.dot(emb_a, emb_b) / (np.linalg.norm(emb_a) * np.linalg.norm(emb_b) + 1e-9))


def _event_score(ids: list[str], regions: dict, embeddings: dict) -> tuple[float | None, float | None]:
    geom_vals, text_vals = [], []
    for a_id, b_id in combinations(ids, 2):
        c = _coherence(regions[a_id], regions[b_id])
        if c is not None:
            geom_vals.append(c)
        text_vals.append(_text_sim(embeddings[a_id], embeddings[b_id]))
    geom_score = sum(geom_vals) / len(geom_vals) if geom_vals else None
    text_score = sum(text_vals) / len(text_vals) if text_vals else None
    return geom_score, text_score


def _span_days(ids: list[str], regions: dict) -> float | None:
    tss = [regions[i]["_tuple_ts"] for i in ids if regions[i].get("_tuple_ts") is not None]
    if len(tss) < 2:
        return None
    return (max(tss) - min(tss)) / 86400.0


def _aggregate(events: list[dict], regions: dict, embeddings: dict) -> dict:
    geom_scores, text_scores = [], []
    for ev in events:
        g, t = _event_score(ev["ids"], regions, embeddings)
        if g is not None:
            geom_scores.append(g)
        if t is not None:
            text_scores.append(t)
    return {
        "n_events": len(events),
        "n_geom_scoreable": len(geom_scores),
        "mean_geom_coherence": sum(geom_scores) / len(geom_scores) if geom_scores else None,
        "mean_text_sim": sum(text_scores) / len(text_scores) if text_scores else None,
    }


def _permutation_null(events: list[dict], regions: dict, embeddings: dict, pool: list[str],
                       n_perm: int, rng: random.Random) -> dict:
    sizes = [len(ev["ids"]) for ev in events]
    null_geom, null_text = [], []
    for _ in range(n_perm):
        perm_geom_scores, perm_text_scores = [], []
        for m in sizes:
            draw = rng.sample(pool, m)
            g, t = _event_score(draw, regions, embeddings)
            if g is not None:
                perm_geom_scores.append(g)
            if t is not None:
                perm_text_scores.append(t)
        if perm_geom_scores:
            null_geom.append(sum(perm_geom_scores) / len(perm_geom_scores))
        if perm_text_scores:
            null_text.append(sum(perm_text_scores) / len(perm_text_scores))
    return {"null_geom": null_geom, "null_text": null_text}


def _z_and_p(observed: float, null_samples: list[float]) -> dict:
    n = len(null_samples)
    mean_null = sum(null_samples) / n
    var_null = sum((x - mean_null) ** 2 for x in null_samples) / n
    std_null = var_null ** 0.5
    z = (observed - mean_null) / std_null if std_null > 1e-9 else None
    p_one_sided = sum(1 for x in null_samples if x >= observed) / n
    return {
        "observed": round(observed, 4),
        "null_mean": round(mean_null, 4),
        "null_std": round(std_null, 4),
        "z": round(z, 2) if z is not None else None,
        "perm_p_one_sided": round(p_one_sided, 4),
    }


def _binom_two_sided_p(k_successes: int, n_trials: int, p: float = 0.5) -> float:
    """Two-sided binomial sign-test p-value, p=0.5 null (coin flip). Exact for small n_trials
    (matches scripts/geometry_realness_test.py's own helper -- same statistical convention this
    project already uses for paired comparisons); falls back to a normal approximation with
    continuity correction for large n_trials, where math.comb(n, n/2) overflows a float."""
    if n_trials == 0:
        return 1.0
    import math

    if n_trials <= 2000:
        def pmf(k, n, p):
            return math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k))

        obs_pmf = pmf(k_successes, n_trials, p)
        total = 0.0
        for k in range(n_trials + 1):
            pk = pmf(k, n_trials, p)
            if pk <= obs_pmf * (1 + 1e-9):
                total += pk
        return min(1.0, total)

    # normal approximation to the binomial sign test, continuity-corrected
    mean = n_trials * p
    std = math.sqrt(n_trials * p * (1 - p))
    z = (abs(k_successes - mean) - 0.5) / std
    # two-sided p from the standard normal survival function via erf
    p_val = math.erfc(z / math.sqrt(2))
    return min(1.0, p_val)


def _text_matched_control(events: list[dict], regions: dict, embeddings: dict, pool: list[str],
                           n_candidates: int, rng: random.Random) -> dict:
    """THE CONFOUND GUARD (added before the real run, per the plan's own honesty precedent -- see
    cognitive_geometry.md's 'book' time-confound flag): the permutation-null test above shows real
    co-recalled pairs are more geometrically coherent than a FULLY RANDOM pair. But if Du's recall
    mechanism is itself text/embedding-driven, and topic (text) happens to correlate with place/
    weather (thoughts about the shore tend to occur AT the shore), that alone could produce the
    observed effect with geometry adding nothing beyond what text already carries -- exactly the
    'text wearing a costume' concern sec5.3 names.

    For every real co-recalled pair (a,b), replace b with b* = the fragment (drawn from a random
    n_candidates-sized subsample of the pool, for tractability over the full ~14k-fragment pool)
    whose TEXT similarity to a is closest to the real pair's own text_sim(a,b) -- i.e. a same-text-
    similarity-level substitute. Compare geom coherence(a,b) [real] vs geom coherence(a,b*)
    [text-matched substitute] pairwise. If real pairs are STILL more geometrically coherent than
    their text-similarity-matched substitutes, that is coherence text similarity does not explain --
    real incremental signal. If the gap collapses, the co-evocation effect above is substantially a
    text-similarity artifact, not new information from the cross-space edges."""
    import numpy as np

    real_vals, matched_vals = [], []
    for ev in events:
        ids = ev["ids"]
        for a_id, b_id in combinations(ids, 2):
            real_c = _coherence(regions[a_id], regions[b_id])
            if real_c is None:
                continue
            target_sim = _text_sim(embeddings[a_id], embeddings[b_id])
            candidates = [c for c in rng.sample(pool, min(n_candidates, len(pool)))
                          if c != a_id and c != b_id]
            if not candidates:
                continue
            cand_sims = np.array([_text_sim(embeddings[a_id], embeddings[c]) for c in candidates])
            best_idx = int(np.argmin(np.abs(cand_sims - target_sim)))
            b_star = candidates[best_idx]
            matched_c = _coherence(regions[a_id], regions[b_star])
            if matched_c is None:
                continue
            real_vals.append(real_c)
            matched_vals.append(matched_c)

    n = len(real_vals)
    if n < 20:
        return {"n_pairs": n, "note": "insufficient text-matchable pairs for a paired test"}
    real_arr, matched_arr = zip(*[(r, m) for r, m in zip(real_vals, matched_vals)])
    mean_real = sum(real_arr) / n
    mean_matched = sum(matched_arr) / n
    n_real_higher = sum(1 for r, m in zip(real_arr, matched_arr) if r > m + 1e-9)
    n_matched_higher = sum(1 for r, m in zip(real_arr, matched_arr) if m > r + 1e-9)
    p_sign = _binom_two_sided_p(n_real_higher, n_real_higher + n_matched_higher)
    return {
        "n_pairs": n,
        "mean_real_pair_coherence": round(mean_real, 4),
        "mean_text_matched_substitute_coherence": round(mean_matched, 4),
        "n_real_higher": n_real_higher, "n_matched_higher": n_matched_higher,
        "sign_test_p": round(p_sign, 5),
        "geom_adds_beyond_text": bool(mean_real > mean_matched and n_real_higher > n_matched_higher
                                       and p_sign < 0.05),
    }


def run(n_perm: int = 200, seed: int = 42) -> dict:
    conn = sqlite3.connect(f"file:{_DB.as_posix()}?mode=ro", uri=True)
    try:
        regions, embeddings = _load_fragment_data(conn)
    finally:
        conn.close()

    ledger_rows = _load_ledger()
    all_events = []
    for r in ledger_rows:
        ids = r["ids"]
        if all(i in regions for i in ids) and len(ids) >= 2:
            all_events.append({"ids": ids, "ts": r["ts"]})

    pool = list(regions.keys())
    rng = random.Random(seed)

    full = _aggregate(all_events, regions, embeddings)
    full_null = _permutation_null(all_events, regions, embeddings, pool, n_perm, rng)
    full_stats = {
        "geom": _z_and_p(full["mean_geom_coherence"], full_null["null_geom"]),
        "text": _z_and_p(full["mean_text_sim"], full_null["null_text"]),
    }

    near_term, long_range = [], []
    span_by_event = {}
    for ev in all_events:
        span = _span_days(ev["ids"], regions)
        span_by_event[id(ev)] = span
        if span is None:
            continue
        (near_term if span < 1.0 else long_range).append(ev)

    near_agg = _aggregate(near_term, regions, embeddings)
    near_null = _permutation_null(near_term, regions, embeddings, pool, n_perm, rng)
    near_stats = {
        "geom": _z_and_p(near_agg["mean_geom_coherence"], near_null["null_geom"]),
        "text": _z_and_p(near_agg["mean_text_sim"], near_null["null_text"]),
    } if near_agg["mean_geom_coherence"] is not None else {"note": "insufficient scoreable events"}

    long_agg = _aggregate(long_range, regions, embeddings)
    long_null = _permutation_null(long_range, regions, embeddings, pool, n_perm, rng)
    long_stats = {
        "geom": _z_and_p(long_agg["mean_geom_coherence"], long_null["null_geom"]),
        "text": _z_and_p(long_agg["mean_text_sim"], long_null["null_text"]),
    } if long_agg["mean_geom_coherence"] is not None else {"note": "insufficient scoreable events"}

    spans = [s for s in (_span_days(ev["ids"], regions) for ev in all_events) if s is not None]
    spans.sort()

    geom_pass_full = full_stats["geom"]["z"] is not None and full_stats["geom"]["z"] >= 2.0 \
        and full_stats["geom"]["perm_p_one_sided"] < 0.05
    geom_pass_long = long_stats.get("geom", {}).get("z") is not None and \
        long_stats["geom"]["z"] >= 2.0 and long_stats["geom"]["perm_p_one_sided"] < 0.05

    if geom_pass_full and geom_pass_long:
        verdict = "PASS"
    elif geom_pass_full and not geom_pass_long:
        verdict = "MIXED (recency-explainable)"
    else:
        verdict = "FAIL"

    # Confound guard: does the coherence effect survive controlling for text similarity? Run on the
    # full sample and, separately, the long-range subset (the harder case). Not gating on the
    # pre-registered PASS/MIXED/FAIL rule above (that rule was fixed before results were read) --
    # reported as an additional diagnostic for the founder-read, per the decoupled-judge law (§7).
    text_control_full = _text_matched_control(all_events, regions, embeddings, pool,
                                               n_candidates=50, rng=rng)
    text_control_long = _text_matched_control(long_range, regions, embeddings, pool,
                                               n_candidates=50, rng=rng)

    return {
        "n_perm": n_perm, "seed": seed,
        "eligible_pool_size": len(pool),
        "n_ledger_rows_n_ids_ge2": len(ledger_rows),
        "n_events_all_ids_covered": len(all_events),
        "full_sample": {"aggregate": full, "stats": full_stats},
        "near_term_lt_1day": {"n_events": len(near_term), "aggregate": near_agg, "stats": near_stats},
        "long_range_ge_1day": {"n_events": len(long_range), "aggregate": long_agg, "stats": long_stats},
        "span_days_distribution": {
            "median": round(spans[len(spans) // 2], 3) if spans else None,
            "p90": round(spans[int(len(spans) * 0.9)], 3) if spans else None,
            "n_with_span": len(spans),
        },
        "text_matched_confound_control": {
            "full_sample": text_control_full,
            "long_range_ge_1day": text_control_long,
        },
        "verdict": verdict,
        "verdict_rule": ("PASS iff geom z>=2.0 & perm_p<0.05 on BOTH the full sample AND the "
                          "long-range (>=1 day) subset; MIXED iff full passes but long-range doesn't "
                          "(recency-explainable); FAIL iff full sample itself is not significant. "
                          "The text-matched confound control is diagnostic context, not part of the "
                          "gating rule (pre-registered before results were read)."),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n_perm", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=str, default=None)
    args = ap.parse_args()

    t0 = time.time()
    result = run(n_perm=args.n_perm, seed=args.seed)
    result["elapsed_s"] = round(time.time() - t0, 1)
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

    out_path = Path(args.out) if args.out else (
        _ROOT / "docs" / "lab" / f"geometry_co_evocation_test_{int(time.time())}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n[written] {out_path}")


if __name__ == "__main__":
    main()
