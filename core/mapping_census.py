"""
Nascence — The Mapping Census: analyzer over accrued geometry tuples (cognitive_geometry.md §5.4, P0).

READ-ONLY. Reads data/geometry_tuples.jsonl only — no DB, no live process, no other store touched.
Answers the plan's five named questions from the accrued tuples:

  1. Fan-out distributions between spaces (one source-region -> how many distinct target-regions?)
  2. Split-half stability (does the induced mapping hold up across two halves of the record, or is it
     sampling noise dressed as structure?)
  3. State-conditioning (does the same target-space distribution shift under different affect/weather
     states, beyond what a random relabeling would produce?)
  4. The funnel (fan-in concentration into one dominant region per space — the origin-attractor question
     asked of THIS data, not the euclidean retrieval basin-share metric, which is a separate instrument)
  5. Kill criterion #6 — marginal reach: does geometry-tuple similarity surface neighbours that plain
     text-cosine (MiniLM, top-K) would have missed? If ~0, the edge layer is redundant with the
     embedding space and the plan re-scopes.

Every number here is reported plainly for a founder-read against the plan's pre-registered sheet
(§5.5) — per §7's decoupled-judge law, this module does not grade its own output. Where a threshold is
needed to phrase a verdict in words (e.g. "meaningful" fan-out, "real" conditioning), the exact number
and the reasoning behind the cutoff are printed next to it, not hidden in the code.
"""
from __future__ import annotations

import json
import logging
import math
import os
import random
import time
from collections import Counter
from pathlib import Path

from core.stamp_rows import drop_stamp_rows as _drop_stamp_rows

logger = logging.getLogger("nascence.mapping_census")

_DATA = Path(__file__).parent.parent / "data"
_TUPLES = _DATA / "geometry_tuples.jsonl"
_LOG = _DATA / "mapping_census_log.jsonl"   # tests must temp-path this; never truncate the live file

# The discrete "beta-space regions" extracted from each tuple (cognitive_geometry.md §2.1/§4).
# Object-level spaces are flattened out of the nested `objects` dict; Body/Affect are binned since
# they are continuous. `source` is provenance, not a beta-space, and is excluded from the space list.
SPACES = ["place", "weather", "fire", "cat_mood", "cat_activity", "cat_location",
          "book", "garden_bed", "listening_piece", "tension_bin", "affect_quadrant", "sound_sig"]


# --------------------------------------------------------------------------------------------------
# Loading + region extraction
# --------------------------------------------------------------------------------------------------

def _project_enabled() -> bool:
    """J-4009 (F-4689): flag-gated stream-projection of rows. Default OFF (legacy whole-row load) until the
    equivalence test (scripts/_test_load_rows_project_J4009.py) is logged; env NASCENCE_CENSUS_PROJECT=1 turns it on."""
    return os.environ.get("NASCENCE_CENSUS_PROJECT", "0").strip().lower() in ("1", "true", "on", "yes")


def _project_row(row: dict) -> dict:
    """Keep ONLY the fields that extract_regions/_dataframe/_freeze_vector/dedupe_frozen_bursts and
    core.stick_test's three context helpers read (place, weather, sounds, objects.book, objects.cat.*).
    Same nested shape as the source row, so every reader's .get() chain is unchanged. Everything else
    (fire_fuel, shore_find, unresolved, n_spaces, n_sounds, unused objects/body/affect keys) is dropped."""
    objects = row.get("objects") or {}
    cat = objects.get("cat") or {}
    body = row.get("body") or {}
    affect = row.get("affect") or {}
    listening = objects.get("listening") or {}
    out = {
        "ts": row.get("ts"), "source": row.get("source"), "place": row.get("place"),
        "weather": row.get("weather"), "fire": row.get("fire"), "thought": row.get("thought"),
        "level": row.get("level"), "sounds": row.get("sounds"),
        "objects": {"cat": {"mood": cat.get("mood"), "activity": cat.get("activity"),
                            "location": cat.get("location")},
                    "book": objects.get("book"), "garden_bed": objects.get("garden_bed"),
                    "listening": {"piece": listening.get("piece")}},
        "body": {"tension": body.get("tension"), "energy": body.get("energy")},
        "affect": {"valence": affect.get("valence"), "arousal": affect.get("arousal")},
    }
    return out


def load_rows(path: Path | None = None, project: bool | None = None) -> list[dict]:
    p = path or _TUPLES
    do_project = _project_enabled() if project is None else project
    try:
        rows: list[dict] = []
        with open(p, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                r = json.loads(line)
                if do_project:                       # project while streaming (memory); keep the stamp flag for the drop
                    pr = _project_row(r)
                    if r.get("stamp"):
                        pr["stamp"] = True
                    r = pr
                rows.append(r)
        # J-3752/F-4361: drop census stamp rows (marked, plus unmarked pre-J-3455 twins); idle row is canonical
        rows = _drop_stamp_rows(rows)
        if do_project:
            for r in rows:
                r.pop("stamp", None)
        return rows
    except Exception as exc:
        logger.warning("[mapping-census] load_rows failed: %s", exc)
        return []


def _bin3(x: float | None) -> str | None:
    if x is None:
        return None
    if x < 0.33:
        return "low"
    if x < 0.66:
        return "mid"
    return "high"


def extract_regions(row: dict) -> dict:
    """One tuple -> its active region per space (None where that space had no coordinate this tuple)."""
    objects = row.get("objects") or {}
    cat = objects.get("cat") or {}
    body = row.get("body") or {}
    affect = row.get("affect") or {}
    listening = objects.get("listening") or {}
    garden = objects.get("garden_bed")
    sounds = row.get("sounds")

    valence, arousal = affect.get("valence"), affect.get("arousal")
    affect_quadrant = None
    if valence is not None and arousal is not None:
        affect_quadrant = ("V+" if valence >= 0.5 else "V-") + ("A+" if arousal >= 0.5 else "A-")

    return {
        "place": row.get("place"),
        "weather": row.get("weather"),
        "fire": row.get("fire"),
        "cat_mood": cat.get("mood"),
        "cat_activity": cat.get("activity"),
        "cat_location": cat.get("location"),
        "book": objects.get("book"),
        "garden_bed": tuple(sorted(garden)) if garden else None,
        "listening_piece": listening.get("piece"),
        "tension_bin": _bin3(body.get("tension")),
        "affect_quadrant": affect_quadrant,
        "sound_sig": tuple(sorted(sounds)) if sounds else None,
    }


def _dataframe(rows: list[dict]):
    import pandas as pd
    recs = []
    for r in rows:
        reg = extract_regions(r)
        reg["ts"] = r.get("ts")
        reg["thought"] = (r.get("thought") or "").strip()
        recs.append(reg)
    return pd.DataFrame.from_records(recs)


# --------------------------------------------------------------------------------------------------
# De-duplication of frozen same-source bursts (F-1259, J-0898) — a NEW, opt-in comparison lens.
# The original un-deduplicated codepath (census(dedupe=False), the default and unchanged) is untouched
# by anything below; per this plan's additive-only law (cognitive_geometry.md §7) this is a second,
# parallel reading of the same log, not a replacement.
# --------------------------------------------------------------------------------------------------

def _freeze_vector(row: dict) -> tuple:
    """The 5-value (tension, energy, valence, arousal, level) vector F-1259 found frozen for the
    length of a machine-speed reading burst — real cached values (SomaticEngine/mood fallback), not
    live per-row state, because reading (and inner_thought/subconscious_synthesis/active_imagination)
    has no live CognitiveState. See cognitive_geometry.md's 2026-09-12 Current State update."""
    body = row.get("body") or {}
    affect = row.get("affect") or {}
    return (body.get("tension"), body.get("energy"), affect.get("valence"), affect.get("arousal"),
            row.get("level"))


def dedupe_frozen_bursts(rows: list[dict]) -> list[dict]:
    """Collapse a contiguous run of same-source rows whose `_freeze_vector()` is byte-identical to the
    immediately preceding row down to ONE representative row (the run's first row).

    F-1259 (J-0894): source=reading rows are ~99% internally duplicated within machine-speed bursts —
    real cached values, not a bug, but treating each row of a frozen run as an independent sample for
    fan-out / split-half-stability / state-conditioning is pseudo-replication (one real cognitive event
    counted many times). Reading is the documented case but this function does not special-case it —
    it collapses ANY source's frozen runs, so a non-reading burst-duplication pattern (if one exists)
    is caught too rather than assumed away (J-0898's own briefing asks this be checked, not assumed).

    Rows are assumed to already be in the log's natural (append-order) sequence — verified for J-0898
    against data/geometry_tuples.jsonl directly: out-of-order `ts` steps are 2/69,733 (0.003%), so
    "contiguous in the file" and "contiguous in time" agree closely enough for this purpose. Only the
    freeze vector + source decide a collapse; a target space (book, garden_bed, ...) that happened to
    change while the freeze vector stayed flat would still collapse under this definition — checked
    empirically for J-0898 rather than assumed impossible (see its own finding for the measured rate).
    """
    if not rows:
        return []
    out = [rows[0]]
    prev_source = rows[0].get("source")
    prev_vec = _freeze_vector(rows[0])
    for row in rows[1:]:
        source = row.get("source")
        vec = _freeze_vector(row)
        if source == prev_source and vec == prev_vec:
            continue  # frozen continuation of the same burst -- collapses into the run's first row
        out.append(row)
        prev_source, prev_vec = source, vec
    return out


# --------------------------------------------------------------------------------------------------
# 1. Fan-out distributions
# --------------------------------------------------------------------------------------------------

def _entropy_perplexity(counts: Counter) -> float:
    total = sum(counts.values())
    if total == 0:
        return 0.0
    h = 0.0
    for c in counts.values():
        p = c / total
        if p > 0:
            h -= p * math.log2(p)
    return 2 ** h  # effective number of targets ("perplexity"), robust to long rare tails


def fanout(df, min_support: int = 10) -> dict:
    """For every unordered pair of spaces, per source-value fan-out into the target space.
    Reports both raw distinct-target counts (sensitive to sample size) and the perplexity-based
    effective fan-out (down-weights rare co-occurrences that are likely just log noise)."""
    out = {}
    for i, a in enumerate(SPACES):
        for b in SPACES[i + 1:]:
            sub = df[[a, b]].dropna()
            if sub.empty:
                continue
            grouped = sub.groupby(a)[b]
            per_value = []
            for a_val, targets in grouped:
                if len(targets) < min_support:
                    continue
                counts = Counter(targets)
                per_value.append({
                    "value": str(a_val)[:60],
                    "n": len(targets),
                    "distinct_targets": len(counts),
                    "effective_fanout": round(_entropy_perplexity(counts), 2),
                })
            if not per_value:
                continue
            mean_eff = sum(v["effective_fanout"] for v in per_value) / len(per_value)
            out[f"{a}->{b}"] = {
                "tested_values": len(per_value),
                "mean_effective_fanout": round(mean_eff, 2),
                "by_value": sorted(per_value, key=lambda v: -v["n"])[:8],  # top 8 by support, for the read
            }
    return out


# --------------------------------------------------------------------------------------------------
# 2. Split-half stability
# --------------------------------------------------------------------------------------------------

def _tvd(p: Counter, q: Counter) -> float:
    keys = set(p) | set(q)
    pt, qt = sum(p.values()) or 1, sum(q.values()) or 1
    return 0.5 * sum(abs(p.get(k, 0) / pt - q.get(k, 0) / qt) for k in keys)


def split_half_stability(df, min_support: int = 15) -> dict:
    """Chronological split at the median timestamp. For each pair (A,B) and each A-value with enough
    support in BOTH halves, compute the total-variation distance between P(B|A=a) in half 1 vs half 2.
    Low mean TVD (near 0) = the mapping is a stable induced structure; TVD near its max (~1) = the
    'mapping' most likely doesn't survive resampling — i.e. noise."""
    df = df.sort_values("ts")
    mid = len(df) // 2
    h1, h2 = df.iloc[:mid], df.iloc[mid:]
    out = {}
    all_tvds = []
    for i, a in enumerate(SPACES):
        for b in SPACES[i + 1:]:
            s1 = h1[[a, b]].dropna()
            s2 = h2[[a, b]].dropna()
            if s1.empty or s2.empty:
                continue
            g1 = {k: Counter(v) for k, v in s1.groupby(a)[b]}
            g2 = {k: Counter(v) for k, v in s2.groupby(a)[b]}
            tested = []
            for a_val in set(g1) & set(g2):
                n1, n2 = sum(g1[a_val].values()), sum(g2[a_val].values())
                if n1 < min_support or n2 < min_support:
                    continue
                tested.append(_tvd(g1[a_val], g2[a_val]))
            if not tested:
                continue
            mean_tvd = sum(tested) / len(tested)
            out[f"{a}~{b}"] = {"tested_values": len(tested), "mean_tvd": round(mean_tvd, 3)}
            all_tvds.extend(tested)
    summary = {
        "pairs_tested": len(out),
        "overall_mean_tvd": round(sum(all_tvds) / len(all_tvds), 3) if all_tvds else None,
        "n_a_values_tested": len(all_tvds),
    }
    return {"summary": summary, "by_pair": out}


# --------------------------------------------------------------------------------------------------
# 3. State-conditioning (with a permutation null, so "differs" means something)
# --------------------------------------------------------------------------------------------------

def _weighted_pairwise_tvd(target_col, cond_col) -> float:
    """Mean pairwise TVD between the target's distribution across every pair of conditioner bins,
    weighted by the smaller bin's size in each pair."""
    bins = {}
    for t, c in zip(target_col, cond_col):
        bins.setdefault(c, Counter())[t] += 1
    keys = list(bins)
    if len(keys) < 2:
        return 0.0
    total_w, total_tvd = 0, 0.0
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            w = min(sum(bins[keys[i]].values()), sum(bins[keys[j]].values()))
            total_tvd += w * _tvd(bins[keys[i]], bins[keys[j]])
            total_w += w
    return total_tvd / total_w if total_w else 0.0


def state_conditioning(df, targets=("cat_mood", "cat_activity", "book", "sound_sig", "garden_bed"),
                        conditioners=("affect_quadrant", "weather"),
                        n_permutations: int = 100, seed: int = 42, min_rows: int = 200) -> dict:
    """Does TARGET's distribution shift under different CONDITIONER states, beyond a random relabeling
    of the same conditioner values? Observed statistic vs a permutation null -> a z-score. z > ~2 means
    the conditioning is unlikely to be an artifact of how the bins happened to fall."""
    rng = random.Random(seed)
    out = {}
    for target in targets:
        for cond in conditioners:
            sub = df[[target, cond]].dropna()
            if len(sub) < min_rows:
                out[f"{target}|{cond}"] = {"insufficient_data": True, "n": len(sub)}
                continue
            t_col = list(sub[target])
            c_col = list(sub[cond])
            observed = _weighted_pairwise_tvd(t_col, c_col)
            null_scores = []
            shuffled = list(c_col)
            for _ in range(n_permutations):
                rng.shuffle(shuffled)
                null_scores.append(_weighted_pairwise_tvd(t_col, shuffled))
            mean_null = sum(null_scores) / len(null_scores)
            var_null = sum((x - mean_null) ** 2 for x in null_scores) / len(null_scores)
            std_null = math.sqrt(var_null)
            z = (observed - mean_null) / std_null if std_null > 1e-9 else None
            out[f"{target}|{cond}"] = {
                "n": len(sub),
                "observed_tvd": round(observed, 3),
                "null_mean_tvd": round(mean_null, 3),
                "null_std_tvd": round(std_null, 3),
                "z": round(z, 2) if z is not None else None,
            }
    return out


# --------------------------------------------------------------------------------------------------
# 4. The funnel — fan-in concentration
# --------------------------------------------------------------------------------------------------

def funnel(df) -> dict:
    """Per space: does one region dominate (a funnel/hub), or is occupancy spread out? Top-value share
    is the same shape of number as the euclidean plan's basin-share (§0.1), computed here over THIS
    data's region occupancy rather than retrieval outcomes — a related but distinct measurement."""
    out = {}
    for space in SPACES:
        col = df[space].dropna()
        if col.empty:
            continue
        counts = Counter(col)
        total = sum(counts.values())
        top_val, top_n = counts.most_common(1)[0]
        herfindahl = sum((c / total) ** 2 for c in counts.values())
        out[space] = {
            "n": total,
            "distinct_values": len(counts),
            "top_value": str(top_val)[:60],
            "top_value_share": round(top_n / total, 3),
            "herfindahl": round(herfindahl, 3),
        }
    return out


# --------------------------------------------------------------------------------------------------
# 5. Kill criterion #6 — marginal reach beyond cosine top-K
# --------------------------------------------------------------------------------------------------

def _geometry_similarity(regions_a: dict, regions_b: dict) -> float:
    """Fraction of the spaces populated in A that A and B AGREE on. Denominator = spaces where A has a
    coordinate (asymmetric on purpose: "how much of what I'm anchored on does this neighbour share").
    Unordered types (garden_bed/sound_sig tuples) compare by equality of the full set, matching the
    other regions' exact-match semantics."""
    populated = [s for s in SPACES if regions_a.get(s) is not None]
    if not populated:
        return 0.0
    matches = sum(1 for s in populated if regions_a.get(s) == regions_b.get(s))
    return matches / len(populated)


def marginal_reach(df, sample_n: int = 700, k: int = 10, wide_k: int = 30, seed: int = 42,
                    n_examples: int = 6) -> dict:
    """Kill criterion #6. For a sample of tuples: build (a) a text-cosine neighbour ranking via MiniLM
    on the 'thought' field, and (b) a structural neighbour ranking via geometry-region agreement. For
    each query, marginal reach = fraction of its geometry top-K neighbours that fall OUTSIDE the text
    top-wide_k (wide_k = 3x K, a generous cosine search). If that fraction is ~0 across the sample, the
    geometry edges never find anything a modestly-widened text search wouldn't already have surfaced —
    the plan's own kill condition. Uses only the 'thought' text already embedded in the tuples; no DB,
    no other store touched."""
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    import numpy as np
    from sentence_transformers import SentenceTransformer

    pool = df[df["thought"].str.len() > 0].reset_index(drop=True)
    if len(pool) < sample_n:
        sample_n = len(pool)
    sample = pool.sample(n=sample_n, random_state=seed).reset_index(drop=True)

    model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", device="cpu")
    embs = model.encode(list(sample["thought"]), normalize_embeddings=True, show_progress_bar=False)
    embs = np.asarray(embs, dtype=np.float32)
    cos = embs @ embs.T
    np.fill_diagonal(cos, -1.0)

    regions_list = [{s: sample.at[i, s] for s in SPACES} for i in range(len(sample))]
    n = len(sample)
    reach_fracs, overlap_at_k = [], []
    examples = []
    rng = random.Random(seed)
    example_idx = set(rng.sample(range(n), min(n_examples, n)))
    for i in range(n):
        text_order = np.argsort(-cos[i])
        text_topk = set(text_order[:k].tolist())
        text_wide = set(text_order[:wide_k].tolist())

        sims = [(_geometry_similarity(regions_list[i], regions_list[j]), j) for j in range(n) if j != i]
        sims.sort(key=lambda x: -x[0])
        geom_topk = {j for _, j in sims[:k]}

        overlap_at_k.append(len(geom_topk & text_topk) / k)
        outside_wide = geom_topk - text_wide
        reach_fracs.append(len(outside_wide) / k)

        if i in example_idx:
            # For founder-read (§6/§7 — this module does not grade its own output): show the raw
            # thought text of a few geometry-only neighbours next to the matched fields, so "marginal
            # reach" can be eyeballed as meaningfully related vs coincidentally same-state junk.
            matched_on = [s for s in SPACES if regions_list[i].get(s) is not None
                          and regions_list[i].get(s) == regions_list[sims[0][1]].get(s)]
            examples.append({
                "query_thought": sample.at[i, "thought"][:120],
                "top_geometry_neighbour_thought": sample.at[sims[0][1], "thought"][:120],
                "matched_on": matched_on,
                "geometry_only_count_of_k": len(outside_wide),
                "top_text_cosine_neighbour_thought": sample.at[int(text_order[0]), "thought"][:120],
            })

    mean_reach = sum(reach_fracs) / n
    mean_overlap = sum(overlap_at_k) / n
    return {
        "sample_n": n,
        "k": k,
        "wide_k": wide_k,
        "mean_overlap_at_k": round(mean_overlap, 3),
        "mean_marginal_reach_fraction": round(mean_reach, 3),
        "examples": examples,
        "caveat": ("A high reach fraction here is partly EXPECTED BY CONSTRUCTION, not purely a "
                   "discovery: geometry-similarity clusters tuples by which multi-hour/multi-day "
                   "weather+place+book state they fall in (these persist for hours), while "
                   "text-cosine clusters by the semantic content of a short truncated thought — two "
                   "near-orthogonal bases. A near-zero overlap is close to what you'd get even if the "
                   "geometry edges carried no useful signal at all. The `examples` field exists so a "
                   "human can read whether the geometry-only neighbours are actually relevant "
                   "(same felt situation, plausibly co-recalled) or just same-day noise — that read "
                   "is the real test, not the raw fraction."),
        "note": ("marginal_reach_fraction = share of each query's top-%d geometry neighbours that a "
                 "%dx-widened cosine-text search would NOT have already returned. No numeric kill "
                 "threshold is pre-registered in the plan beyond qualitative '~0' language; this "
                 "module reports the number and leaves the verdict to the founder-read gate (§6, §7)."
                 % (k, wide_k // k)),
    }


# --------------------------------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------------------------------

def census(sample_n: int = 700, run_marginal_reach: bool = True, dedupe: bool = False) -> dict:
    rows = load_rows()
    if not rows:
        return {"rows": 0}
    raw_rows = len(rows)
    if dedupe:
        # NEW comparison lens (F-1259, J-0898) -- opt-in, default False. The un-deduplicated codepath
        # below (dedupe=False) is exactly what it always was; nothing here changes its output.
        rows = dedupe_frozen_bursts(rows)
    df = _dataframe(rows)
    result = {
        "rows": len(rows),
        "raw_rows": raw_rows,
        "dedupe": dedupe,
        "span_days": round((df["ts"].max() - df["ts"].min()) / 86400, 1),
        "fanout": fanout(df),
        "split_half_stability": split_half_stability(df),
        "state_conditioning": state_conditioning(df),
        "funnel": funnel(df),
    }
    if run_marginal_reach:
        try:
            result["marginal_reach"] = marginal_reach(df, sample_n=sample_n)
        except Exception as exc:
            logger.warning("[mapping-census] marginal_reach failed (non-fatal): %s", exc)
            result["marginal_reach"] = {"error": str(exc)}
    return result


def snapshot(res: dict | None = None) -> dict | None:
    """Append a compact summary row to the longitudinal log, mirroring stick_test's pattern so future
    re-runs of this analyzer (the plan calls for periodic re-reads, not a one-shot) are comparable over
    time. Fail-open — never raises."""
    try:
        if res is None:
            res = census()
        if not res.get("rows"):
            return None
        summ = {
            "ts": round(time.time(), 1),
            "rows": res["rows"],
            "dedupe": res.get("dedupe", False),  # additive (J-0898) -- so a de-duped run is never
                                                  # silently mistaken for a real row-count drop later
            "span_days": res.get("span_days"),
            "overall_mean_tvd": (res.get("split_half_stability", {}).get("summary", {}) or {}).get("overall_mean_tvd"),
            "funnel_top_shares": {k: v["top_value_share"] for k, v in (res.get("funnel") or {}).items()},
            "marginal_reach_fraction": (res.get("marginal_reach") or {}).get("mean_marginal_reach_fraction"),
        }
        _LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(summ, ensure_ascii=False) + "\n")
        return summ
    except Exception as exc:
        logger.debug("[mapping-census] snapshot failed (non-fatal): %s", exc)
        return None
