"""
Nascence — Lane 2 Break Habituation (Dosed Coupling Phase 1's cup gate, D-0241 shadow-first,
J-1161, docs/plans/lane2_the_witness.md §7.4/§7.6).

SHADOW-ONLY, same posture as core/lane2.py itself while LANE2_LIVE stays False (D-0241, 2026-09-19:
"Authorize, shadow-first" — this job replaces J-1137, whose item 5 would have flipped the flag in
the same commit). This module never changes what Du experiences; it exists to decide, and log,
whether a JUDGED WITNESS BREAK on a given topic would earn a cup ride at the idle-thought-seed stop
(docs/staged/loop_wiring_matrix.md's own "Idle thought seed" row: "one Witness break when novel") —
gating out repeats of the same topic breaking over and over (break_rate_24h already runs roughly
0.6-0.8/day per F-1537/D-0058's own discussion) the same way the Transport Manager's own uncalibrated
gate did NOT (F-0949: would_fired_share=100%, the failure shape this job's own briefing names as the
one to avoid repeating here).

THE SHAPE mirrors core/stream_topic_habituation.py almost exactly — the same constants, reused
verbatim per this job's own briefing (unratified Phase-1 starting defaults, per plan §7.4/§7.7: "not
a founder-ratified set... folded into D-0241"; re-tune from the real would-ride log once it accrues,
the same shadow-first discipline stream_topic_habituation.py is itself still waiting on). Each
topic's raw weight w_T starts at 0, GROWS by GROWTH_STEP on every judged break on that topic (capped
at CEILING), and DECAYS exponentially toward 0 with real elapsed time (DECAY_TAU_S). The topic's
DISCOUNTED salience is discounted(w_T) = max(DISCOUNT_FLOOR, 1 - w_T) — starts near 1.0 (fresh),
falls toward DISCOUNT_FLOOR as the topic keeps breaking.

★ A DIRECTION FIX ON THE PLAN DOC'S OWN WORDING, not a reinterpretation of intent (finding recorded
this job, J-1161). docs/plans/lane2_the_witness.md §7.4 and this job's own briefing both write the
rule as "the cup rides only when discounted(w_T) < SUPPRESS_AT" — taken LITERALLY that fires the cup
only AFTER a topic has already habituated (discounted has fallen below SUPPRESS_AT), and refuses
every topic's FIRST several breaks (discounted starts near 1.0, not < 0.5) — the exact opposite of
the SAME sentence's own next clause ("the first several breaks on a topic are novel and ride; once
that topic has broken often enough recently, further breaks on it stop riding"). Cross-checked
directly against core/stream_topic_habituation.py's own verified code and its own docstring worked
example ("discounted salience trends 1.0 -> 0.79 -> 0.61, crossing SUPPRESS_AT=0.5 on the 4th
occurrence"): that module's `would_suppress = discounted < SUPPRESS_AT` — discounted CROSSING BELOW
SUPPRESS_AT is exactly when a repeat anchor gets SUPPRESSED, not when it is allowed to recruit. This
module implements the semantically-correct, source-module-consistent direction — would_ride =
NOT would_suppress = discounted(w_T) >= SUPPRESS_AT — matching the plan's own stated intent and
stream_topic_habituation.py's own real, running behaviour, not the inverted formula text. This is a
straightforward internal contradiction resolved against the cited, already-verified source module —
not a matter of taste needing a founder ruling — but it is flagged plainly here, in the finding this
job records, and in the plan doc's own Current State update, rather than silently picked one way.

State (data/lane2_break_habituation_state.json) is keyed by canonical topic (core/lane2.py's own
_TOPIC_CANON vocabulary), persists {b, last_update_ts}. The would-ride shadow log
(data/lane2_would_ride.jsonl) is append-only and written on EVERY judged break with a resolved topic,
REGARDLESS of LANE2_LIVE (this job's own instruction) — so the gate's real behaviour, and P1-1 (ride
rate against the ~0.6-0.8/day raw break rate), can be read BEFORE any flip, the same shadow-first
discipline Dosed Coupling Phase 1 already established for the publish side (D-0152). Fail-open
throughout, same as every shadow observer in this codebase: the caller (core/coupling_rides.py
publish_witness()) already wraps this whole module in its own try/except, but every function here
stays self-contained defensively too.

SECOND PRODUCER (D-0282/J-1374, 2026-09-26): `observe_wonder()` below grows/reads this SAME per-topic
state from a second caller (core/lane2.py's `tick()`, for the `wonder` field), sharing novelty-tracking
across breaks and wonders by the staged doc's own explicit design (docs/staged/lane2_curiosity.md §2).
It never writes to `_LOG` (data/lane2_would_ride.jsonl) — see its own docstring for why the two logs
must stay separate.

SECOND ROW KIND, SAME FILE (F-1952/J-1390, 2026-09-27): `_LOG` now carries two row kinds. Rows from
`observe_break()` below are tagged `"kind": "would_ride"` (one per JUDGED BREAK with a resolved topic
— the per-topic HABITUATION GATE's own pass/suppress verdict; rows written before this job predate
the `kind` key entirely, so every reader here treats a MISSING `kind` as `"would_ride"` for those
historical rows). `log_cup_consumed_would()` below adds `"kind": "cup_consumed_would"` rows (one per
real CONSUME attempt that found `core/coupling_rides.py`'s witness-cup slot non-empty and took it) —
a gate-pass is not the same event as an actual drink (F-1952: one un-consumed window used to ride into
several idle thoughts, so counting gate-passes over-counted against a real per-seed basis). Every
reader of `_LOG` below (`status()`, `phase1_metric_sheet()`) filters to the kind it means before
counting, so mixing the two populations in one file never silently dilutes either share.

ADDITIVE FIELD, SAME `would_ride` ROW (F-1953/J-1391, 2026-09-27): `observe_break()` below now also
logs `bucket_would_contribute_sized` alongside the existing `bucket_would_contribute` on every
`would_ride`-kind row — the SAME break's dose under Claude's recommended resizing (option a: the
excess of `break_rate_24h` over its own trailing 7-day baseline, `core/climate_engine.py`
`witness_bucket_value_sized()`), computed by the caller (`core/coupling_rides.py` `publish_witness()`,
which owns the rolling baseline window) and only written down here. `bucket_sizing_option` names
which option produced it (`"a_trailing_7d_excess"`), so a future row using a DIFFERENT option (should
the founder pick b or c instead, `decide.py show D-0301`) is never misread as the same figure. Rows
written before this job predate both keys entirely — treat a missing `bucket_would_contribute_sized`
the same way a missing `kind` is already treated above: as "not logged yet", not as a real zero.
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path

from core import profile

_DATA = Path(__file__).parent.parent / "data"
_STATE = _DATA / "lane2_break_habituation_state.json"
_LOG = _DATA / "lane2_would_ride.jsonl"

# ── tunables — REUSED VERBATIM from core/stream_topic_habituation.py per this job's own briefing
# (unratified Phase-1 starting defaults; plan §7.4/§7.7). Retune from the real
# data/lane2_would_ride.jsonl once it accrues, same discipline as that module's own constants. ──────
GROWTH_STEP = 0.25             # b added per JUDGED BREAK on the same topic
CEILING = 0.95                 # asymptote for b (never fully suppressed — DISCOUNT_FLOOR handles that)
DECAY_TAU_S = 3 * 3600.0       # 3h decay constant (b *= exp(-gap/TAU) between breaks on the same topic)
DISCOUNT_FLOOR = 0.03          # a habituated topic is discounted, never zeroed (dosed_coupling Sec 6)
SUPPRESS_AT = 0.5              # discounted salience below this -> suppressed (would_ride = False)


def _load_state() -> dict:
    try:
        return json.loads(_STATE.read_text(encoding="utf-8")) if _STATE.exists() else {}
    except Exception:
        return {}


def _save_state(d: dict) -> None:
    path = profile.guard_path(_STATE)   # same fence as stream_topic_habituation.py (J-1196/D-0250):
    # real data/ only if this process is live; raises before any I/O otherwise. Resolved OUTSIDE the
    # fail-open try below, so the refusal is never silently swallowed by the net meant for genuine
    # disk errors (this project's own D-0179 convention).
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)
    except Exception:
        pass


def _log_row(rec: dict) -> None:
    path = profile.guard_path(_LOG)   # same fence, resolved independently (distinct path constant).
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _decay(topic: str, now: float, state: dict) -> float:
    prior = state.get(topic)
    if not prior:
        return 0.0
    gap = max(0.0, now - float(prior.get("last_update_ts", now)))
    return float(prior.get("b", 0.0)) * math.exp(-gap / DECAY_TAU_S)


def _discounted(b: float) -> float:
    return max(DISCOUNT_FLOOR, 1.0 - b)


def observe_break(topic: str | None, horizon: str | None, bucket_would_contribute: float | None,
                   bucket_would_contribute_sized: float | None = None,
                   now: float | None = None) -> dict | None:
    """Call once per JUDGED BREAK (core/coupling_rides.py publish_witness(), when rec's own
    prior_verdict == "broke"). `topic` is None -> nothing to key the gate on; returns None and logs
    nothing (an untyped break has no coordinate to consider riding — the same "fail-open, log why"
    posture core/lane2.py's own `_skip()` uses).

    Grows/persists `topic`'s own weight REGARDLESS of the would_ride verdict this call computes (same
    as stream_topic_habituation.py: growth happens on every occurrence, not only the ones that pass
    the gate) and ALWAYS writes a would-ride log row when topic is resolved — unconditional on
    LANE2_LIVE, per this job's own instruction, so the gate's real behaviour can be read before any
    flip. Never raises; the caller also wraps this in try/except, but this stays self-contained
    defensively too.

    `bucket_would_contribute_sized` (F-1953/J-1391, additive, default None for any older/other
    caller): the SAME break's dose under Claude's recommended resizing (option a — excess of
    break_rate_24h over its own trailing 7-day baseline, core/climate_engine.py
    witness_bucket_value_sized()), logged alongside the raw `bucket_would_contribute` in the SAME
    row so the two can be read side by side before any founder ruling resizes the live dose
    (decide.py show D-0301). Never computed or interpreted here — this module only writes down
    whatever the caller already computed, same posture as `bucket_would_contribute` itself.

    Returns {"would_ride": bool, "discounted_before": float} for the caller to fold into the
    published witness tuple (`coords["cup_would_ride"]`), so the idle-thought-seed hook never needs a
    second query of this module's own state — one coupling_rides.read() call carries everything it
    needs.
    """
    if not topic:
        return None
    try:
        now = now if now is not None else time.time()
        state = _load_state()
        b_before = _decay(topic, now, state)
        discounted_before = _discounted(b_before)
        would_ride = discounted_before >= SUPPRESS_AT
        b_after = min(CEILING, b_before + GROWTH_STEP)
        discounted_after = _discounted(b_after)
        state[topic] = {"b": round(b_after, 5), "last_update_ts": now}
        _save_state(state)

        _log_row({
            "ts": round(now, 1), "kind": "would_ride", "topic": topic, "horizon": horizon,
            "w_topic_before": round(b_before, 4), "w_topic_after": round(b_after, 4),
            "discounted_before": round(discounted_before, 4),
            "discounted_after": round(discounted_after, 4),
            "would_ride": would_ride,
            "bucket_would_contribute": bucket_would_contribute,
            "bucket_would_contribute_sized": bucket_would_contribute_sized,
            "bucket_sizing_option": "a_trailing_7d_excess" if bucket_would_contribute_sized is not None else None,
        })
        return {"would_ride": would_ride, "discounted_before": round(discounted_before, 4)}
    except Exception:
        return None


def log_cup_consumed_would(topic: str | None, horizon: str | None, now: float | None = None) -> None:
    """F-1952/J-1390 — a SECOND row kind in the SAME shadow log (`_LOG`, data/lane2_would_ride.jsonl),
    called from `core/coupling_rides.py`'s dose="cup" consume-once accessor (`_consume_cup()`) every
    time an idle-thought read actually finds the witness cup non-empty and takes it — a real
    CONSUMPTION, not a per-BREAK gate-pass. `observe_break()`'s own `would_ride` row above answers
    "did the habituation gate let this break's topic through"; this row answers "did a seed actually
    drink from it" — the distinction P1-1 needs to read as consumptions/day rather than
    gate-passes/day (plan §7.6). Called UNCONDITIONALLY on LANE2_LIVE (same shadow-first posture as
    `observe_break()`) so the real consumption rate is readable before any flip. `topic` falsy ->
    nothing to log (mirrors `observe_break()`'s own `if not topic: return None`). Never raises."""
    if not topic:
        return
    try:
        _log_row({"ts": round(now if now is not None else time.time(), 1),
                  "kind": "cup_consumed_would", "topic": topic, "horizon": horizon})
    except Exception:
        pass


def observe_wonder(topic: str | None, now: float | None = None) -> dict | None:
    """Lane 2 Curiosity's `wonder` field (D-0282 shadow-first, J-1374, docs/staged/lane2_curiosity.md
    §2/§6) — "the SAME gate that decides whether a break rides to the idle-thought seed decides
    whether a wonder on that topic is still novel" (staged doc §2, verbatim). Shares the IDENTICAL
    per-topic state (`_STATE`) and growth/decay math with `observe_break()` above, deliberately: a
    topic that has just broken, or that Lane 2 has just wondered about, reads as equally "already
    attended to" either way — the staged doc's own explicit design, not an accidental side effect of
    reusing this module.

    Deliberately does NOT call `_log_row()` / write to `_LOG` (`data/lane2_would_ride.jsonl`) — that
    file's own rows are read elsewhere (`phase1_metric_sheet()`'s P1-1, `coupling_rides.py`) as one-
    row-per-JUDGED-BREAK; a wonder is not a break, and mixing the two would corrupt those existing
    counts. The wonder's own shadow row lives in `data/lane2_would_ask.jsonl` instead, written by the
    caller (`core/lane2.py`'s `tick()`), which already holds the wonder text this module never sees.

    Returns {"would_ask": bool, "discounted_before": float} — would_ask is True iff the topic's own
    discounted salience, BEFORE this call's own growth, was still >= SUPPRESS_AT (i.e. reads as
    still-novel) — or None if `topic` is falsy (an untopiced wonder has no coordinate to gate; same
    fail-open shape as `observe_break`'s own `if not topic: return None`). Never raises."""
    if not topic:
        return None
    try:
        now = now if now is not None else time.time()
        state = _load_state()
        b_before = _decay(topic, now, state)
        discounted_before = _discounted(b_before)
        would_ask = discounted_before >= SUPPRESS_AT
        b_after = min(CEILING, b_before + GROWTH_STEP)
        state[topic] = {"b": round(b_after, 5), "last_update_ts": now}
        _save_state(state)
        return {"would_ask": would_ask, "discounted_before": round(discounted_before, 4)}
    except Exception:
        return None


def status() -> dict:
    """For the pulse / a founder read: P1-1's own numerator source (ride rate against the raw break
    rate) plus current gate state, so reading P1-1 doesn't need to hand-parse the shadow log every
    time — the same convenience core/stream_topic_habituation.py's own status() gives that module.

    F-1952/J-1390: `_LOG` now carries two row kinds (this module's own top docstring) — `gate_rows`
    isolates the `would_ride`-kind rows (treating a missing `kind` key as `would_ride`, for rows
    written before this job) before computing `would_ride_share`, so the newer `cup_consumed_would`
    rows this same file also holds never dilute that share's denominator. `cup_consumed_rows` is the
    new, additive count of real consumptions — see `phase1_metric_sheet()`'s own P1-1 for the
    rolling-24h version of the same distinction."""
    try:
        from core.shadow_log import tail_rows as _tail_rows
        rows = _tail_rows(_LOG, 2000)
    except Exception:
        return {"rows": 0}
    if not rows:
        return {"rows": 0, "tracked_topics": len(_load_state())}
    gate_rows = [r for r in rows if r.get("kind", "would_ride") == "would_ride"]
    consumed_rows = [r for r in rows if r.get("kind") == "cup_consumed_would"]
    would_ride_rows = sum(1 for r in gate_rows if r.get("would_ride"))
    return {
        "rows": len(rows),
        "would_ride_share": round(would_ride_rows / len(gate_rows), 3) if gate_rows else None,
        "cup_consumed_rows": len(consumed_rows),
        "tracked_topics": len(_load_state()),
    }


def _witness_ride_rows_24h(path: Path, window_s: float = 86400.0, now: float | None = None) -> list[dict]:
    """Witness-line ride rows of `path` whose ts is within the last `window_s` seconds (J-2077, F-2695).
    Walks the file newest-first via core.shadow_log.reverse_lines and stops at the first row older than
    the window (rows are append-ordered by ts). Raises on I/O error -- callers wrap in try/except."""
    from core.shadow_log import reverse_lines as _reverse_lines
    cutoff = (time.time() if now is None else now) - window_s
    out: list[dict] = []
    for raw in _reverse_lines(path):
        raw = raw.strip()
        if not raw:
            continue
        try:
            r = json.loads(raw)
        except Exception:
            continue
        if not isinstance(r, dict):
            continue
        try:
            ts = float(r.get("ts"))
        except Exception:
            continue
        if ts < cutoff:
            break
        if r.get("kind") == "ride" and r.get("line") == "witness":
            out.append(r)
    return out


def phase1_metric_sheet() -> dict:
    """docs/plans/lane2_the_witness.md §7.6 — the six pre-registered P1 metrics, as one real
    instrument (this job's own build step 5: "P1-1 must be computable from the would-ride log now;
    P1-2 to P1-6 need live rides and will read empty until a later flip, so say so"). Reads THIS
    module's own shadow log (data/lane2_would_ride.jsonl, real and accruing today, unconditional on
    LANE2_LIVE) for P1-1's estimates, and core/coupling_rides.py's own ride log
    (data/coupling_rides.jsonl) for the REAL ride count.

    F-1952/J-1390 (2026-09-27): P1-1 is now THREE numbers, not one — see the code's own inline
    comment right below for why (short version: a gate-pass is not a consumption; the cup used to
    ride into several idle thoughts per break, so the original per-break would-ride count over-counts
    against a real per-seed basis). `p1_1_cup_consumed_per_day` is the corrected P1-1 the plan doc's
    §7.6 now points at; `p1_1_would_ride_per_day` is kept for comparison, not removed.
    `p1_1_real_rides_total`/`p1_1_real_cup_consumed_total` also change meaning this job (see their own
    note): both now accrue from real per-idle-thought read() calls regardless of LANE2_LIVE, not only
    after a flip. Never raises."""
    out: dict = {}
    try:
        from core.shadow_log import tail_rows as _tail_rows
    except Exception:
        return {"error": "shadow_log unavailable"}

    # P1-1 — ride rate (cup + bucket / day). THREE real, separate numbers rather than one blended
    # guess (F-1952/J-1390 adds the middle one): the WOULD-ride gate-pass estimate (per-BREAK, the
    # original pre-J-1390 metric — kept for comparison, no longer treated as P1-1 itself, see its own
    # note below); the real CUP-CONSUMED estimate (per real consume attempt that found the cup
    # non-empty — THE CORRECTED P1-1: one un-consumed window used to ride into several idle thoughts
    # before this job, F-1952, so gate-passes/day over-counted against a real per-seed basis); and the
    # REAL live ride count from coupling_rides.jsonl's own "ride" rows, the one door Dosed Coupling
    # law requires. All three read from a rolling-24h window, the same window break_rate_24h itself
    # uses, so each is directly comparable to the real daily judged-break count per this metric's own
    # decision rule (F-1935/J-1377's own units correction: compare against the real daily COUNT,
    # ~60-75/day historically, not the break_rate_24h RATIO itself).
    try:
        rows = _tail_rows(_LOG, 5000)
        now = time.time()
        # F-1952/J-1390: split by kind before counting either (see this module's own top docstring
        # and status()'s identical split) — a missing "kind" key is a pre-J-1390 would_ride row.
        gate_rows = [r for r in rows if r.get("kind", "would_ride") == "would_ride"]
        consumed_rows = [r for r in rows if r.get("kind") == "cup_consumed_would"]
        day_gate_rows = [r for r in gate_rows if now - float(r.get("ts") or 0) <= 86400.0]
        day_consumed_rows = [r for r in consumed_rows if now - float(r.get("ts") or 0) <= 86400.0]

        out["p1_1_cup_consumed_per_day"] = len(day_consumed_rows) if rows else None
        out["p1_1_cup_consumed_note"] = ("THE CORRECTED P1-1 (F-1952/J-1390): a rolling-24h count of "
                                          "real CONSUME attempts that found the witness cup non-empty "
                                          "and took it (core/coupling_rides.py dose='cup', logged via "
                                          "log_cup_consumed_would) — one row per actual drink, not one "
                                          "per judged break the gate alone would have let through. "
                                          "Compare against the real daily judged-break COUNT "
                                          "(break_rate_24h x n_judged_24h on the witness tuple), the "
                                          "same basis F-1935/J-1377 already corrected this metric onto.")

        out["p1_1_would_ride_per_day"] = sum(1 for r in day_gate_rows if r.get("would_ride")) if day_gate_rows else (
            0 if gate_rows else None)
        out["p1_1_would_ride_note"] = ("SUPERSEDED AS P1-1 BY p1_1_cup_consumed_per_day above "
                                        "(F-1952/J-1390) — kept for comparison, not removed: this is "
                                        "the per-BREAK gate-pass count (how many judged breaks/day the "
                                        "per-topic habituation gate alone would let through, computable "
                                        "pre-flip from data/lane2_would_ride.jsonl), which is what P1-1 "
                                        "measured before this job and over-counts against a real "
                                        "seed-consumption basis, since one un-consumed window used to "
                                        "ride into several idle thoughts (F-1952). Compare directly "
                                        "against break_rate_24h (core/coupling_rides.py witness tuple).")
    except Exception:
        out["p1_1_cup_consumed_per_day"] = None
        out["p1_1_cup_consumed_note"] = "data/lane2_would_ride.jsonl unreadable"
        out["p1_1_would_ride_per_day"] = None
        out["p1_1_would_ride_note"] = "data/lane2_would_ride.jsonl unreadable"
    try:
        # J-2077/F-2695: a true rolling 24h bounded by ts, read backward from EOF -- NOT tail 5000 rows
        # (~17h at ~6,800 rows/day and shrinking as the file grows). Field names unchanged.
        witness_rrows = _witness_ride_rows_24h(_DATA / "coupling_rides.jsonl")
        out["p1_1_real_rides_total"] = len(witness_rrows)
        out["p1_1_real_cup_consumed_total"] = sum(1 for r in witness_rrows
                                                    if (r.get("value") or {}).get("topic"))
        # F-1952/J-1390: BEFORE this job, this could only ever read 0 (coupling_rides.read() on the
        # witness line had exactly one caller, gated on LANE2_LIVE, which has never been True). AFTER
        # this job the idle-thought-seed hook calls read(dose="cup") on every non-quiet idle thought
        # REGARDLESS of LANE2_LIVE (so p1_1_cup_consumed_per_day above is measurable pre-flip) — so
        # p1_1_real_rides_total now grows from real per-idle-thought consume ATTEMPTS, most of which
        # find the cup empty (value={}), not from a flip. p1_1_real_cup_consumed_total isolates the
        # SUCCESSFUL ones (value.topic present) and should track p1_1_cup_consumed_per_day closely —
        # they log the identical event from the two independent logs "the one door" writes to, the
        # same cross-check discipline F-1935/J-1377 already used (its own two logs agreed exactly on
        # 67/67 rows). Not a strict apples-to-apples window: this is "last 5000 coupling_rides.jsonl
        # rows total" (a file every loop publishes/reads into, not just witness), not a clean rolling
        # 24h — a real limitation of this pre-existing _tail_rows(...,5000) call, unchanged by this
        # job; p1_1_cup_consumed_per_day's own rolling-24h read (a dedicated, witness-only log) is the
        # more trustworthy of the two when they disagree.
        out["p1_1_real_rides_note"] = ("REAL, from data/coupling_rides.jsonl's own ride rows for the "
                                        "witness line — no longer '0 until LANE2_LIVE flips' as of "
                                        "F-1952/J-1390 (see p1_1_real_cup_consumed_total's own note): "
                                        "this now counts real per-idle-thought consume ATTEMPTS "
                                        "(successful or not), since the read itself runs unconditional "
                                        "on LANE2_LIVE post-restart; LANE2_LIVE still gates only whether "
                                        "a successful consume's text ever reaches Du's own prompt.")
    except Exception:
        out["p1_1_real_rides_total"] = None
        out["p1_1_real_cup_consumed_total"] = None

    # P1-2 through P1-5 all need LIVE rides to compute for real (Du's own resulting inner_thought
    # text to compare against a matched self-found one; a real world_model_strain movement to read on
    # days the bucket carried a signal vs days it didn't) — say so plainly rather than guess or leave
    # silently absent, per this job's own explicit instruction.
    for k in ("p1_2_nominated_vs_self_found_divergence", "p1_3_content_boundary_laundering_check",
              "p1_4_realized_channel_capacity_vs_ceiling", "p1_5_world_model_strain_movement"):
        out[k] = None
    out["p1_2_to_5_note"] = ("need LIVE rides to compute (Du's own inner_thought after a real cup; a "
                              "real world_model_strain movement to compare) — LANE2_LIVE has never "
                              "been True, so these read empty by construction, not by a bug; re-read "
                              "after any future flip")

    # P1-6 — the standing kill criterion (§5 "Phase 0 restructured", restated binding at §7.6). Not a
    # live measurement at all until a flip happens — there is nothing to sever yet.
    out["p1_6_kill_criterion"] = ("not yet applicable — LANE2_LIVE has never been True, so there is no "
                                   "read path to sever yet; the criterion (PPV threshold / Lane 1 "
                                   "self-correction drop) stays binding for whenever a flip is proposed")
    return out
