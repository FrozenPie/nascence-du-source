"""
Nascence — Transport Dispatch Habituation Shadow (squishy-spring discount, dosed_coupling's own
Weight law applied to the dispatcher — J-0603, spawned from F-0828/J-0600, under
docs/staged/dosed_coupling.md Section 1.3/3).

SHADOW-ONLY. This module never changes what core/transport_manager.py's dispatch_tick() actually
returns. Alongside the real (undiscounted) winner selection, this module computes a WOULD-WIN
candidate using the same per-tick weights but with each line's weight additionally discounted by a
habituation term `b`, and logs `{real_winner, would_winner, differs}` so a founder read after a few
days can ask whether the discount would meaningfully cut the dispatcher's fired-share.

WHY THIS EXISTS (F-0828): dispatch_tick() has zero memory of a line having already won. A line whose
drought ratio crosses DISPATCH_THRESHOLD stays a "candidate" forever (since_hours only grows, gap_ema
is frozen without a fresh observe() call) and keeps winning every tick until it gets a new
occurrence. Real example: 'sound:clock_tick:study' won 337/337 (100%) of dispatch ticks over ~8h
post-restart, because nothing discounts a repeat winner. dosed_coupling.md already names this gap
("Transport Manager shadow, saturated 721/721") as one of the un-habituated readers of its own
Weight law (Section 1.3: "felt pull = earned weight minus an antagonist that grows with activation
and decays with quiet").

THE SHAPE (deliberately mirrors core/curiosity_habituation.py's `b`, not a new formalism): `b` per
line_id GROWS each tick that line is the REAL (undiscounted) winner — repeatedly winning for real is
the "genuine re-activation" signal here, the direct analog of curiosity's tension `count` bump — and
DECAYS exponentially with real elapsed time since that line's own last touch (win or candidacy). No
sign asymmetry here (unlike curiosity's aversive/positive/neutral split) — a dispatch win has no
independent valence signal to key off; a single symmetric law is used.

The discount is MULTIPLICATIVE and floored, never zeroing a line out (this project's "not deletion"
law, dosed_coupling.md Section 6): discounted_weight = raw_weight * max(DISCOUNT_FLOOR, 1 - b).
Novelty candidates are NEVER discounted (mirrors dispatch_tick()'s own DISPATCH_THRESHOLD exemption:
"maximal salience by definition; no baseline needed to judge it" — a birth event has nothing to
habituate against).

Growth is driven by the REAL winner history (not a counterfactual "would-have-won" chain) — this is
a deliberate simplification for a first shadow pass, same spirit as curiosity_habituation's own
documented proxy (real signal, not a fully self-consistent counterfactual simulation): it answers
"if this discount had been governing selection, given how dispatch ACTUALLY played out, who would
have ridden the bus instead" rather than the harder "who would have won under a fully counterfactual
world where the discount was live from the start." Good enough to read a differ_share from; not
claimed to be more than that.

State (`data/transport_habituation_state.json`) is keyed by line_id, persists {b, last_update_ts} —
decay is measured against real elapsed wall time between touches, not resampled fresh each tick.
Fail-open throughout: any error here must never affect the dispatcher's real behaviour — the caller
(transport_manager.dispatch_tick()) wraps this whole module in a bare try/except.
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Optional

from core import profile

_DATA = Path(__file__).parent.parent / "data"
_STATE = _DATA / "transport_habituation_state.json"
_LOG = _DATA / "transport_habituation_shadow.jsonl"

# ── tunables (Phase 0 shadow — cheap to retune from the log, nothing here is live) ──
# A ~60s-cadence dispatcher needs a discount that clears in HOURS, not curiosity's multi-day tau,
# or a stale winner (like clock_tick:study) would still dominate for days after this ships.
# CEILING/DISCOUNT_FLOOR picked from a real replay (J-0603, scratch), not guessed: against the
# actual post-restart clock_tick:study sequence (344 real ticks, raw weight climbing 15.17->18.59
# as its unresolved drought keeps growing), CEILING=0.92 only suppressed 50% of ticks -- the discount
# floor (1-0.92=0.08) was not quite low enough, so as the still-genuinely-growing raw weight climbed
# past ~1.5/0.08=18.75-ish over several hours it punched back through. CEILING=0.95 (discount floor
# 0.05) dropped the same real replay to 2.3% (8/344, all in the initial ramp-up before b reaches
# ceiling) -- comfortably under Phase 0's own pre-registered "<30% of ticks" target. This is a
# genuine trade-off, not free: a HIGHER ceiling suppresses a real, still-worsening drought for
# longer before it's allowed to punch back through DISCOUNT_FLOOR -- "not deletion" (dosed_coupling
# Sec 6) means it always CAN resurface, never that it resurfaces quickly. Retune from the shadow log
# once real multi-line data accrues, same as every other constant in this module.
GROWTH_STEP = 0.25           # b added per consecutive REAL win for that line
CEILING = 0.95                # asymptote for b (never fully suppressed — DISCOUNT_FLOOR handles that)
DECAY_TAU_S = 2 * 3600.0      # 2h half-decay-ish constant (b *= exp(-gap/TAU) between touches)
DISCOUNT_FLOOR = 0.03         # a habituated line is discounted, never zeroed (dosed_coupling Sec 6)


def _load_state() -> dict:
    try:
        return json.loads(_STATE.read_text(encoding="utf-8")) if _STATE.exists() else {}
    except Exception:
        return {}


def _save_state(d: dict) -> None:
    path = profile.guard_path(_STATE)   # J-1196/D-0250: real data/ only if this process is live;
    # raises before any I/O if not (D-0179, J-0932 precedent). Resolved OUTSIDE the fail-open try
    # below, so the refusal is never swallowed by the net meant for genuine disk errors.
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)
    except Exception:
        pass


def _log(rec: dict) -> None:
    path = profile.guard_path(_LOG)   # J-1196/D-0250: same fence as _save_state() above, resolved
    # independently since _LOG is a distinct path constant from _STATE.
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _decay(line_id: str, now: float, state: dict) -> float:
    """Return this line's currently-decayed b (does not mutate state)."""
    prior = state.get(line_id)
    if not prior:
        return 0.0
    gap = max(0.0, now - float(prior.get("last_update_ts", now)))
    return float(prior.get("b", 0.0)) * math.exp(-gap / DECAY_TAU_S)


def observe_and_log(candidates: list, real_winner, dispatch_threshold: float, now: float | None = None) -> None:
    """Given every Candidate evaluate() produced this tick (across all registered lines) and the
    REAL winner dispatch_tick() actually picked (a Candidate or None, using its own unmodified,
    undiscounted logic), compute the WOULD-WIN candidate under habituation-discounted weights and
    log both. Never raises — the caller wraps this in try/except, but this stays self-contained
    defensively too. Mutates no dispatcher state; only this module's own shadow state/log.

    EDGE_TRIGGER note (D-0294/J-1432, 2026-09-28): `candidates` is still literally "every Candidate
    evaluate() produced this tick" — unchanged in shape/contract — but under
    core.transport_manager.EDGE_TRIGGER=True, evaluate() itself now only PRODUCES a spike/drought
    Candidate for a line whose (line, kind) is currently armed (see transport_manager.py's own
    EDGE_TRIGGER comment). A line whose ratio is still over the bar but which already fired and
    hasn't re-armed yet emits NO Candidate at all under edge-trigger, so it never reaches this
    function — this module sees the edge-FILTERED pool, not the raw threshold-crossing pool it saw
    under level polling. This directly changes what this shadow instrument can observe: D-0177's
    finding (would_fired_share stuck at 100%, F-0949) was diagnosing level-trigger's stale-winner
    problem specifically; that problem is what edge-trigger targets, so would_fired_share should
    fall once real data accrues under EDGE_TRIGGER=True. Re-read this instrument's own shadow log
    after a live week under the edge trigger rather than assuming D-0177's number still applies."""
    try:
        if not candidates:
            return
        now = now if now is not None else time.time()
        state = _load_state()

        touched_ids = {c.line_id for c in candidates}
        b_decayed = {lid: _decay(lid, now, state) for lid in touched_ids}

        would_winner = None
        best_discounted = float("-inf")
        weights_detail: dict = {}
        for c in candidates:
            if c.kind == "novelty":
                discounted = c.weight   # novelty is exempt, mirrors dispatch_tick()'s own rule
            else:
                discounted = c.weight * max(DISCOUNT_FLOOR, 1.0 - b_decayed[c.line_id])
            weights_detail[c.line_id] = {"kind": c.kind, "raw_weight": round(c.weight, 4),
                                          "b": round(b_decayed[c.line_id], 4),
                                          "discounted_weight": round(discounted, 4)}
            if discounted > best_discounted:
                best_discounted = discounted
                would_winner = c
        if would_winner is not None and would_winner.kind != "novelty" and best_discounted < dispatch_threshold:
            would_winner = None

        real_line = real_winner.line_id if real_winner is not None else None
        for lid in touched_ids:
            grew = (real_line == lid and real_winner.kind != "novelty")
            b_after = min(CEILING, b_decayed[lid] + GROWTH_STEP) if grew else b_decayed[lid]
            state[lid] = {"b": round(b_after, 5), "last_update_ts": now}
        _save_state(state)

        _log({
            "ts": round(now, 1),
            "real_winner": real_winner.to_dict() if real_winner is not None else None,
            "would_winner": would_winner.to_dict() if would_winner is not None else None,
            "differs": (real_line or None) != (would_winner.line_id if would_winner is not None else None),
            "n_candidates": len(candidates),
            "weights": weights_detail,
        })
    except Exception:
        pass


def status() -> dict:
    """For the pulse: how much divergence the shadow has accrued so far — the pre-registered read."""
    try:
        from core.shadow_log import tail_rows as _tail_rows
        rows = _tail_rows(_LOG, 2000)
    except Exception:
        return {"rows": 0}
    if not rows:
        return {"rows": 0}
    differs = sum(1 for r in rows if r.get("differs"))
    would_fired = sum(1 for r in rows if r.get("would_winner") is not None)
    real_fired = sum(1 for r in rows if r.get("real_winner") is not None)
    return {
        "rows": len(rows),
        "differ_share": round(differs / len(rows), 3),
        "real_fired_share": round(real_fired / len(rows), 3),
        "would_fired_share": round(would_fired / len(rows), 3),
        "tracked_lines": len(_load_state()),
    }
