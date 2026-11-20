"""
Nascence — GOLDEN SPIRAL RECALL, Phase 2: Theta (phase-angle) shadow log — 2026-09-28, J-1562.
docs/staged/golden_spiral_recall.md section 3, Phase 2 row (quoted): "a would-recall log: at each
felt-recall trigger and each idle seed, compute the ray (phase tolerance +/- 1/24 of day, +/- 1/12 of
year) and log {trigger, n_candidates_by_band, top3_ids, would_differ_from_current_recall} -- nothing
rides."

THE IDEA (plan section 2, Theta row). A recall triggered by a world change (felt recall) or by an
idle seed reads the current tod/season and casts a ray: candidate fragments whose phase is within a
tolerance of now's, across every age band. The ray is cheap (one indexed range query on two REAL
columns, plan's own words) and is compared against whatever the CALLER's own current recall already
found, purely to see whether phase would have surfaced something different. NOTHING RIDES: this
module never changes a caller's return value, control flow, or what reaches affect/a prompt. It only
reads fragment_context (read-only queries) and appends one row per call to a NEW file,
data/theta_shadow.jsonl -- it never writes to memory_fragments, fragment_context, or any existing
shadow log.

WHERE THE RAY GOES (plan section 2 + this job's own briefing): two REAL columns on fragment_context,
`tod` and `season` (both ALTER-added, additive, by core/memory/store.py's store_fragment(),
store.py:671-679/700-714) -- `daylight` (categorical) is deliberately NOT used here; the briefing
itself flags it as "not obviously a distance metric, decide how/whether to use it" and the plan's own
worked example only ever casts the ray on day + year phase. Two starting phases are "enough to start"
(plan section 2's own words) -- routine phase (weekday) is explicitly a later column, not built here.

GUARDS (plan section 5, kept): no new store, no schema rewrite -- one index added on the ALREADY
ALTER-added tod/season columns (this job's own briefing: "confirm an index exists or add one; this is
a new read path, not a new write"), no new column, no table. Nothing renders phase into a prompt from
this module. World answers, never leads: callers pass their OWN current-recall ids in so this module
can compare against them; this module never tells a caller what to recall.

Callers (both additive, both wrapped in try/except at the call site, per this module's own fail-open
contract below): core/felt_recall.py's _handle_edge() (trigger = "felt_recall:<dim>") and
core/associative_recall.py's recall_block() (trigger = "idle_seed").
"""
from __future__ import annotations

import json
import logging
import sqlite3
import time
from pathlib import Path

logger = logging.getLogger("nascence.theta_shadow")

_ROOT = Path(__file__).parent.parent
_DB = _ROOT / "data" / "memory" / "nascence.db"
_SHADOW_LOG = _ROOT / "data" / "theta_shadow.jsonl"

# Plan section 3, Phase 2 row, quoted exactly: "phase tolerance +/- 1/24 of day, +/- 1/12 of year".
# Starting values (shadow-first discipline) -- plan section 8 item 1 leaves the exact tolerance open
# for a founder call later; these are what the plan's own Phase 2 row already pre-registers to START
# the shadow with, not a value this job invented.
TOD_TOLERANCE = 1.0 / 24.0
SEASON_TOLERANCE = 1.0 / 12.0

# "A 'time' is not the last five minutes" -- reused verbatim from felt_recall.py's own MIN_AGE_S
# (plan section 3.2's lineage: golden_spiral_recall.md never overrides this floor, and the two shadow
# logs should not silently disagree on what counts as "the past").
MIN_AGE_S = 86400.0

# Age bands named by the plan's own section 2, R row, verbatim: "last hour, last day, last week, last
# month, last season, older". R itself (the per-band retrieval budget) is Phase 3, not this job -- but
# Phase 2's own briefing asks for `n_candidates_by_band` this session, so the ray buckets candidates by
# the SAME named bands the plan already uses elsewhere, rather than inventing a different partition.
# Seconds; upper bound exclusive; the last band is open-ended.
AGE_BANDS: tuple[tuple[str, float], ...] = (
    ("last_hour", 3600.0),
    ("last_day", 86400.0),
    ("last_week", 7 * 86400.0),
    ("last_month", 30 * 86400.0),
    ("last_season", 90 * 86400.0),
    ("older", float("inf")),
)

# Plan section 3.2's own bound ("keep the top N_MATCH") has a Theta analogue here: cap how many raw
# candidate rows one ray pulls back before ranking, so a densely-populated phase window (once the
# store has years of history) never turns one shadow row into an unbounded scan. Generous relative to
# felt_recall's own N_MATCH=24 because this is a read for COUNTING by band, not just top-3.
# J-1970 (D-0364 C), 2026-10-08: raised 2000 -> 20000. The query has no ORDER BY, so a LIMIT smaller than the
# window silently ranks an ARBITRARY subset (index-scan order). With the 7% populated store the window median
# was 209 (max 935) and 2000 never bit; once the tod/season backfill (scripts/backfill_phase_J1970.py) fills the
# other ~65,700 rows the window median is ~3,100 and 2000 WOULD truncate before ranking. A tolerance is untouched
# by this; it only stops the cap from deciding which rows get ranked.
_RAY_ROW_LIMIT = 20000

# J-1970 (D-0364 C): the ranking rule. Replaces the linear sum d_tod + d_season (season = 69.5% of the rank
# distance, one day of season = 3.9 minutes of clock, F-2528: a recency preference in disguise). The rule is
# named in every logged row (`rank_rule`) so a later read can tell which ranking produced a row. Chosen from
# scripts/replay_ray_rank_J1970.py -- see the finding recorded with this change for the replay numbers.
# rank key = d_tod + SEASON_RANK_WEIGHT * d_season, ties broken by recency (unchanged from before).
# CHOSEN RULE (named): "tod_first_season_window" = weight 0.0 -- rank by d_tod ALONE among the candidates that
# already passed the +/- SEASON_TOLERANCE season filter, most-recent first on exact ties. Replay over the 3025
# recorded triggers on the full backfilled pool (F-id in the J-1970 finding): weights 1.0/0.5/0.25/0.1/0.03 left the
# top-3 at p50 age 1-3 d (still a recency preference, the season term still outweighed or matched tod in the sort);
# only 0.0 moved it (p50 12.0 d, p90 25.0 d, 44% of slots older than 14 d, 73% distinct ids vs 31%). The season
# window still bounds how far the date can drift, so "same clock time from an unrelated season" cannot occur.
# The SEASON window itself (+/- SEASON_TOLERANCE filter) is untouched; only its weight inside the rank changed.
SEASON_RANK_WEIGHT = 0.0
RANK_RULE = "tod_first_season_window"

_index_ensured = False


def _ensure_index() -> None:
    """This job's own briefing, verbatim: "confirm an index exists or add one; this is a new read
    path, not a new write." Checked directly (2026-09-28): core/memory_edges.py's own _CTX_SCHEMA is
    the only CREATE TABLE for fragment_context in the repo, and it carries no index on tod or season.
    Adds one, additive, idempotent (IF NOT EXISTS) -- the same ALTER-adjacent convention the tod/season
    columns themselves were added under (store.py:706-712). Runs at most once per process (module-level
    flag); a short busy_timeout (2s, distinct from store.py's own 30s convention for real writes) so a
    lock held by a live writer at the exact moment of the FIRST call after process start can never
    stall the substrate tick or an idle thought waiting on this -- a failure here just means the next
    caller retries the same cheap DDL, never a correctness issue (the SELECT below works with or
    without the index, only its speed differs on a populated store)."""
    global _index_ensured
    if _index_ensured:
        return
    try:
        conn = sqlite3.connect(str(_DB))
        try:
            conn.execute("PRAGMA busy_timeout=2000;")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_fragctx_tod ON fragment_context(tod)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_fragctx_season ON fragment_context(season)")
            conn.commit()
        finally:
            conn.close()
        _index_ensured = True
    except Exception as exc:
        logger.debug("[theta_shadow] index ensure failed, will retry next call (non-fatal): %s", exc)


def now_phase(ts: float | None = None) -> tuple[float, float]:
    """The SAME formula core/memory/store.py's store_fragment() uses to stamp a fragment's own
    tod/season (store.py:675-676) -- reused verbatim, not re-derived, so a ray cast at moment `ts`
    measures itself against fragments stamped by the identical clock."""
    _lt = time.localtime(ts if ts is not None else time.time())
    tod = round((_lt.tm_hour * 3600 + _lt.tm_min * 60 + _lt.tm_sec) / 86400.0, 4)
    season = round((_lt.tm_yday - 1 + tod) / 366.0, 4)
    return tod, season


def _circular_window(centre: float, tolerance: float) -> list[tuple[float, float]]:
    """tod and season are both circular fractions in [0, 1) (midnight/New Year wrap) -- a plain
    BETWEEN(centre-tol, centre+tol) would miss real neighbours across the wrap (tod=0.995 vs tod=0.01
    are 0.015 apart, not 0.985 apart). Returns 1 or 2 (lo, hi) ranges (each within [0, 1]) whose union
    is the correct wrapped window -- 2 only when the window itself straddles the wrap point."""
    lo, hi = centre - tolerance, centre + tolerance
    if lo < 0.0 and hi > 1.0:
        return [(0.0, 1.0)]   # tolerance >= 0.5 -- window covers the whole circle
    if lo < 0.0:
        return [(0.0, hi), (1.0 + lo, 1.0)]
    if hi > 1.0:
        return [(lo, 1.0), (0.0, hi - 1.0)]
    return [(lo, hi)]


def _phase_distance(a: float, b: float) -> float:
    """Wrapped distance between two [0, 1) phase fractions (e.g. tod 0.01 and 0.995 are 0.015 apart,
    not 0.985)."""
    d = abs(a - b)
    return min(d, 1.0 - d)


def _age_band(age_s: float) -> str:
    for name, upper in AGE_BANDS:
        if age_s < upper:
            return name
    return "older"   # unreachable (AGE_BANDS's last upper bound is inf) -- kept as an honest fallback


def rank_candidates(rows, tod: float, season: float, season_weight: float | None = None) -> list:
    """Order phase-window candidates (rows with ["tod"], ["season"], ["tuple_ts"]) closest-first.
    key = d_tod + season_weight * d_season, ties broken most-recent-first. season_weight=1.0 reproduces the
    pre-J-1970 rule exactly (kept reachable for the replay harness; nothing live passes it)."""
    w = SEASON_RANK_WEIGHT if season_weight is None else season_weight

    def _sort_key(r) -> tuple[float, float]:
        d = _phase_distance(r["tod"], tod) + w * _phase_distance(r["season"], season)
        return (d, -r["tuple_ts"])

    return sorted(rows, key=_sort_key)


def cast_ray(now_ts: float | None = None) -> dict:
    """The ray itself (plan section 3.2's shape: "one indexed range query on two REAL columns" --
    two range queries here, tod and season, ANDed; the circular wrap above is Python-side because a
    raw SQL BETWEEN cannot express a wrapped range without the same branching this function already
    does explicitly). Read-only against a fresh URI connection (mode=ro) -- never opens a writable
    handle except inside `_ensure_index()`, and never mutates fragment_context or any fragment.

    Returns {tod, season, n_candidates, n_candidates_by_band, top3_ids, candidate_ids} --
    `candidate_ids` (every matched id, not just the top 3) is kept so a caller COULD diff against more
    than 3 of its own if it ever wanted to; the logged shadow row (log_ray, below) only ever carries
    top3_ids, per the plan's own exact field list.

    Ranking for top3 (J-1970 / D-0364 C, tod-first): wrapped d_tod + SEASON_RANK_WEIGHT * d_season,
    smallest = most phase-alike, so the clock time decides and the date only breaks near-ties; the season
    FILTER window is unchanged. Ties broken by recency (most-recent tuple_ts first) -- the same tie-break
    convention felt_recall._build_prior already uses. Before J-1970 the key was d_tod + d_season (weight 1).
    """
    _ensure_index()
    tod, season = now_phase(now_ts)
    tod_ranges = _circular_window(tod, TOD_TOLERANCE)
    season_ranges = _circular_window(season, SEASON_TOLERANCE)
    tod_sql = " OR ".join(["(tod >= ? AND tod <= ?)"] * len(tod_ranges))
    season_sql = " OR ".join(["(season >= ? AND season <= ?)"] * len(season_ranges))
    params: list[float] = []
    for lo, hi in tod_ranges:
        params.extend([lo, hi])
    for lo, hi in season_ranges:
        params.extend([lo, hi])
    now = now_ts if now_ts is not None else time.time()

    sql = (
        "SELECT fragment_id, tuple_ts, tod, season FROM fragment_context "
        "WHERE tod IS NOT NULL AND season IS NOT NULL AND tuple_ts < ? "
        f"AND ({tod_sql}) AND ({season_sql}) LIMIT ?"
    )
    conn = sqlite3.connect(f"file:{_DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(sql, (now - MIN_AGE_S, *params, _RAY_ROW_LIMIT)).fetchall()
    finally:
        conn.close()

    by_band: dict[str, int] = {name: 0 for name, _ in AGE_BANDS}
    for r in rows:
        by_band[_age_band(now - r["tuple_ts"])] += 1

    ranked = rank_candidates(rows, tod, season)
    candidate_ids = [r["fragment_id"] for r in ranked]
    return {
        "tod": tod, "season": season, "rank_rule": RANK_RULE,
        "n_candidates": len(rows),
        "n_candidates_by_band": by_band,
        "top3_ids": candidate_ids[:3],
        "candidate_ids": candidate_ids,
    }


def would_differ(ray_top3: list[str], current_recall_ids: list[str] | None) -> bool:
    """Plan's own field: does the ray's top-3 differ from the current recall's top-3? Order-blind set
    comparison. `current_recall_ids` is whatever the CALLER already considers its own current top-3
    (felt_recall's own N_MATCH-kept ranking, or associative_recall's own k-sliced trail) -- this
    function never re-derives or re-slices it, so it never silently guesses what "current recall"
    means for a caller it was not told about (world-answers-never-leads applied to this module's own
    callers, not just to Du)."""
    return set(ray_top3) != set(current_recall_ids or [])


def log_ray(trigger: str, current_recall_ids: list[str] | None, now_ts: float | None = None) -> dict:
    """The one entry point felt_recall.py and associative_recall.py call. Computes the ray, compares
    it to the caller's own current-recall ids, appends ONE row to data/theta_shadow.jsonl, and returns
    the row. Fail-open: never raises -- any failure anywhere in this function still produces and logs
    an honest, structurally-complete row (candidate fields at their empty/zero default) rather than
    silently doing nothing, so a caller's own try/except is a second line of defense, not the only one.
    Every caller ignores the return value (nothing rides on it); it exists only so a caller COULD read
    it back for its own diagnostics if ever useful.
    """
    now = now_ts if now_ts is not None else time.time()
    row: dict = {
        "ts": round(now, 1), "trigger": trigger,
        "tod": None, "season": None, "rank_rule": RANK_RULE, "n_candidates": 0,
        "n_candidates_by_band": {name: 0 for name, _ in AGE_BANDS},
        "top3_ids": [], "would_differ_from_current_recall": False,
        "current_recall_ids": list(current_recall_ids or []),
    }
    try:
        ray = cast_ray(now)
        row["tod"] = ray["tod"]
        row["season"] = ray["season"]
        row["n_candidates"] = ray["n_candidates"]
        row["n_candidates_by_band"] = ray["n_candidates_by_band"]
        row["top3_ids"] = ray["top3_ids"]
        row["would_differ_from_current_recall"] = would_differ(ray["top3_ids"], current_recall_ids)
    except Exception as exc:
        logger.debug("[theta_shadow] cast_ray failed for trigger=%s (non-fatal): %s", trigger, exc)
    try:
        _SHADOW_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_SHADOW_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[theta_shadow] log write failed (non-fatal): %s", exc)
    return row


def status() -> dict:
    """For the >=enough-rows read (this project's own no-tail-sampling discipline: read every row, not
    a sample) once this has accrued data -- straight off the shadow log, read-only. Mirrors
    felt_recall.status()'s own shape (rows / span / per-key breakdown) so a HUD or pulse reader already
    familiar with that convention needs no new mental model for this one."""
    try:
        rows = [json.loads(l) for l in _SHADOW_LOG.read_text(encoding="utf-8").splitlines() if l.strip()] \
            if _SHADOW_LOG.exists() else []
    except Exception:
        rows = []
    if not rows:
        return {"rows": 0}
    n_with_candidate = sum(1 for r in rows if r.get("n_candidates", 0) >= 1)
    n_differ = sum(1 for r in rows if r.get("would_differ_from_current_recall"))
    by_trigger: dict = {}
    for r in rows:
        t = r.get("trigger", "?")
        d = by_trigger.setdefault(t, {"n": 0, "with_candidate": 0, "differ": 0})
        d["n"] += 1
        if r.get("n_candidates", 0) >= 1:
            d["with_candidate"] += 1
        if r.get("would_differ_from_current_recall"):
            d["differ"] += 1
    span_hr = round((rows[-1]["ts"] - rows[0]["ts"]) / 3600, 2) if len(rows) > 1 else 0.0
    return {
        "rows": len(rows), "span_hr": span_hr,
        "pct_with_candidate": round(100 * n_with_candidate / len(rows), 1),
        "pct_would_differ": round(100 * n_differ / len(rows), 1),
        "by_trigger": by_trigger,
    }
