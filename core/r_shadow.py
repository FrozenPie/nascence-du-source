"""
Nascence — GOLDEN SPIRAL RECALL, Phase 3: R (radius=age) shadow log — 2026-09-28, J-1563.
docs/staged/golden_spiral_recall.md section 3, Phase 3 row (quoted): "the per-band budget computed
beside the live recall; log which bands the live recall actually draws from vs the budget."

THE IDEA (plan section 2, R row). Replace the mental model of "a flat recency bump" with Fibonacci
age BANDS (last hour, last day, last week, last month, last season, older -- section 2's own band
list) and a retrieval budget per band: of N recalled fragments, a fixed share comes from each band,
so the recent is never crowded out by the volume of the old and the old is never absent. The plan
text names the band list and the "fixed share" concept but does not itself pick unequal weights
across bands, so this module reads "fixed share" as an EQUAL 1/6 split across the six named bands --
the lowest-assumption reading available, not a founder-ruled weighting (plan section 8 leaves the
exact per-band scope open for a later `/decide`; this shadow log observes against the equal-share
reading so that decision has real comparison data to look at either way).

PRE-REGISTERED METRIC (this job's own briefing, written before this module was pointed at any real
data): live recall draws > 80% of a single retrieve() call's results from the last-week band -- the
crowding-out failure the spiral exists to fix. If it does NOT (i.e. real recalls are already spread
across bands), R is not solving a real problem and the plan's own section 3 table says so outright
("if it does not, R is unnecessary") -- an honest negative result is a complete, valid outcome here,
not a failure to find something. `status()` below reports this percentage directly, across every
logged row, once enough have accrued (this project's own no-tail-sampling discipline).

OBSERVE-ONLY, NOTHING RIDES: this module never changes what core.memory.store.retrieve() returns,
never reweights a score, and never writes to memory_fragments, fragment_context, or any existing
store/table. It is called from ONE hook inside retrieve() itself (core/memory/store.py, right before
its own final `return`), wrapped in the caller's own try/except -- exactly the existing precedent set
by that function's "Deliberative Retrieval Phase 0" retrieval_probe hook a few lines above it. It
reads NOTHING new from the database: retrieve() already has both `unique` (the final selected set)
and `all_rows` (the full un-cold, un-hidden candidate pool) sitting in memory by the time this fires,
so unlike Phase 2's theta_shadow (which must cast its own independent ray query because nothing
upstream of it already computed candidates), this hook issues ZERO additional SQL of its own -- a
strictly SMALLER risk footprint than "same risk shape as core/euclidean_recall.py's own shadow_log()"
asks for (that module opens its own connection and runs its own SELECT), not merely an equal one. It
appends one row per retrieve() call to a NEW file, data/r_shadow.jsonl.

BANDS: reuses core.theta_shadow.AGE_BANDS verbatim (imported, not re-typed) so Phase 2 and Phase 3
partition age into the exact same six named bins -- the plan's own section 2 wording ("last hour,
last day, last week, last month, last season, older") is one list, not two independently invented
ones. `_age_band()` below duplicates theta_shadow's own private helper of the same name (four lines)
rather than importing a leading-underscore name from another module across a package boundary; both
copies must stay in sync with the one shared AGE_BANDS tuple they both import.

AGE BASIS: a fragment's own `timestamp` column on memory_fragments -- the SAME field
core.memory.store._score_tier() already reads for its own (weak, non-log) recency multiplier
(`age_days = (now - row["timestamp"]) / 86400`). Deliberately NOT fragment_context's `tuple_ts`
(Theta's own field, on a different table, stamped from a possibly-backdated world-tuple timestamp) --
R is about how old a MEMORY is, so this shadow measures it on the exact age basis the live recall
mechanisms it is meant to eventually replace already use, keeping the comparison apples-to-apples.

GUARDS (plan section 5, kept): no new store, no schema rewrite -- one new flat append-only jsonl
file, no table, no column. Nothing renders a band or a budget into a prompt from this module. World
answers, never leads: this module only counts and logs what retrieve() already decided; it never
feeds a value back into scoring or slot allocation in this phase (that would be Phase 4, gated on
this phase's own pre-registered metric and its own future `/decide`).

Caller: core/memory/store.py's retrieve(), one hook, additive, wrapped in try/except at the call
site (this module's own log_observation() is also internally fail-open, per its own docstring below
-- two independent layers, matching theta_shadow.py's own convention).
"""
from __future__ import annotations

import json
import logging
import time
import threading
from pathlib import Path

from core import profile   # J-1815/F-2428: the write fence (D-0179)
from core.theta_shadow import AGE_BANDS   # the one shared band partition -- see module docstring

logger = logging.getLogger("nascence.r_shadow")

_ROOT = Path(__file__).parent.parent
_SHADOW_LOG = _ROOT / "data" / "r_shadow.jsonl"

# The pre-registered failure threshold this whole phase exists to check (job briefing, quoted in the
# module docstring above): >80% of a single retrieve() call's results drawn from the last_week band.
CROWDING_THRESHOLD = 0.80
CROWDING_BAND = "last_week"


def _age_band(age_s: float) -> str:
    """Duplicate of theta_shadow._age_band() (four lines) -- see module docstring for why this is a
    duplicate, not a cross-module import of that leading-underscore helper."""
    for name, upper in AGE_BANDS:
        if age_s < upper:
            return name
    return "older"   # unreachable (AGE_BANDS's last upper bound is inf) -- an honest fallback


def band_budget(n: int) -> dict[str, float]:
    """The "fixed share per band" the plan's own section 2 describes, read as an equal split (see
    module docstring) across the six named AGE_BANDS: n / 6 for every band, as a float -- a target to
    compare actual per-band counts against, never rounded and never enforced, since nothing about
    live retrieval changes in this phase."""
    share = n / len(AGE_BANDS)
    return {name: share for name, _ in AGE_BANDS}


def _band_counts(rows, now: float) -> dict[str, int]:
    """rows: an iterable of sqlite3.Row (or any mapping exposing `timestamp`). See module docstring's
    "AGE BASIS" paragraph for why `timestamp`, not fragment_context's `tuple_ts`."""
    counts: dict[str, int] = {name: 0 for name, _ in AGE_BANDS}
    for row in rows:
        try:
            ts = row["timestamp"]
        except Exception:
            continue
        if ts is None:
            continue
        counts[_age_band(max(0.0, now - float(ts)))] += 1
    return counts


def observe(results, pool=None, now_ts: float | None = None) -> dict:
    """Compute one shadow row from retrieve()'s own already-in-memory `results` (the final `unique`
    list of (score, row) pairs) and, optionally, its own `pool` (`all_rows`, the full un-cold,
    un-hidden candidate set BEFORE tier/slot allocation). `pool` lets a later reader tell "the budget
    was missed because old material was crowded out" apart from "the budget was missed because no old
    material exists yet to draw from" (this store is young; see the plan's own Current State on
    J-1562's Theta read finding the live db has no real accrued history yet either). Never raises on
    a well-formed `results`/`pool`; log_observation (below) wraps this call too, not just its own file
    write, so a genuinely malformed input still yields a safe logged row rather than a crash."""
    now = now_ts if now_ts is not None else time.time()
    n = len(results)
    result_rows = [row for _, row in results]
    n_by_band = _band_counts(result_rows, now)
    budget = band_budget(n)
    pool_n_by_band = _band_counts(pool, now) if pool is not None else None
    pct_last_week = (n_by_band.get(CROWDING_BAND, 0) / n) if n else 0.0
    over_budget = [name for name, _ in AGE_BANDS if n_by_band[name] > budget[name]]
    under_budget = [name for name, _ in AGE_BANDS
                    if n_by_band[name] < budget[name]
                    and (pool_n_by_band is None or pool_n_by_band.get(name, 0) > 0)]
    return {
        "n_results": n,
        "n_by_band": n_by_band,
        "budget_by_band": {k: round(v, 3) for k, v in budget.items()},
        "pool_n_by_band": pool_n_by_band,
        "pct_last_week": round(pct_last_week, 4),
        "crowded": pct_last_week > CROWDING_THRESHOLD,
        "over_budget_bands": over_budget,
        "under_budget_bands": under_budget,
    }


# J-1926 / F-2550: log_observation runs inside store.retrieve on the loop thread and, since J-1918, in a worker thread (memory_service.ask via off_loop); serialise the append.
_APPEND_LOCK = threading.Lock()


def log_observation(trigger: str, results, pool=None, now_ts: float | None = None) -> dict:
    """The one entry point core.memory.store.retrieve() calls. Fail-open like theta_shadow.log_ray():
    any failure anywhere below still returns a structurally-complete row (empty/zero defaults) and
    still attempts the file write; the caller's own try/except at the hook site is a second line of
    defense, not the only one. Nothing about the caller's return value is ever touched by this
    function -- the return here exists only so a caller COULD read it back, per theta_shadow's own
    convention (no caller does today; nothing rides on it)."""
    now = now_ts if now_ts is not None else time.time()
    row: dict = {
        "ts": round(now, 1), "trigger": trigger, "n_results": 0,
        "n_by_band": {name: 0 for name, _ in AGE_BANDS},
        "budget_by_band": {name: 0.0 for name, _ in AGE_BANDS},
        "pool_n_by_band": None, "pct_last_week": 0.0, "crowded": False,
        "over_budget_bands": [], "under_budget_bands": [],
    }
    try:
        row.update(observe(results, pool=pool, now_ts=now))
    except Exception as exc:
        logger.debug("[r_shadow] observe failed for trigger=%s (non-fatal): %s", trigger, exc)
    try:
        # J-1815 / F-2428 -- write fence: guard_path BEFORE the mkdir, INSIDE the existing fail-open try (the row is
        # still returned; store.retrieve() also wraps the call). guard_path logs one warning per path.
        _slog = profile.guard_path(_SHADOW_LOG)
        _slog.parent.mkdir(parents=True, exist_ok=True)
        with _APPEND_LOCK, open(_slog, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except profile.NonLiveWriteError as exc:
        logger.debug("[r_shadow] log write refused by the fence (non-live): %s", exc)
    except Exception as exc:
        logger.debug("[r_shadow] log write failed (non-fatal): %s", exc)
    return row


def status() -> dict:
    """The >=enough-rows read (no-tail-sampling discipline: read every row, not a sample), mirroring
    theta_shadow.status()'s own shape. Reports this phase's own pre-registered metric directly:
    `pct_crowded` is the share of LOGGED retrieve() calls whose own pct_last_week exceeded
    CROWDING_THRESHOLD -- read this (and mean_pct_last_week), not any single row, before concluding
    anything about whether R is needed (plan/briefing's own "do not read a tail sample and
    extrapolate")."""
    try:
        rows = [json.loads(l) for l in _SHADOW_LOG.read_text(encoding="utf-8").splitlines() if l.strip()] \
            if _SHADOW_LOG.exists() else []
    except Exception:
        rows = []
    if not rows:
        return {"rows": 0}
    n_crowded = sum(1 for r in rows if r.get("crowded"))
    pct_last_week_vals = [r.get("pct_last_week", 0.0) for r in rows if r.get("n_results", 0) > 0]
    by_trigger: dict = {}
    for r in rows:
        t = r.get("trigger", "?")
        d = by_trigger.setdefault(t, {"n": 0, "crowded": 0})
        d["n"] += 1
        if r.get("crowded"):
            d["crowded"] += 1
    span_hr = round((rows[-1]["ts"] - rows[0]["ts"]) / 3600, 2) if len(rows) > 1 else 0.0
    return {
        "rows": len(rows), "span_hr": span_hr,
        "pct_crowded": round(100 * n_crowded / len(rows), 1),
        "mean_pct_last_week": round(sum(pct_last_week_vals) / len(pct_last_week_vals), 4)
            if pct_last_week_vals else None,
        "by_trigger": by_trigger,
    }
