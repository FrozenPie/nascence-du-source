"""
Nascence — Climate Engine (the medium-timescale field)

THREE TIMESCALES OF AFFECT (the architectural spine this module completes):

    FAST    AffectState      seconds-minutes   carried emotion (joy/fear/anger/trust…)
    MEDIUM  ClimateField     hours-days        THIS MODULE — standing psychological weather
    SLOW    Self Model       days-weeks        autobiography, T4 gate, epochs, themes

The Subconscious used to communicate with the conscious lane by WRITING TEXT — tension
reports, dream fragments, autobiography lines injected into the prompt every cycle. That
made the unconscious another author. The mind narrated its own depths into existence on a
fixed clock, whether or not anything was actually pressing.

ClimateField replaces that with a CONTINUOUS FIELD. Nine scalar dimensions, each a pure
numeric aggregation over the shadow table, the light table, the tension ledger and the
self-concept — NO emotional vocabulary (trust/fear live in AffectState, not here) and,
critically, NO LLM ANYWHERE IN THIS FILE. The field warps retrieval, salience and the
executive prior without ever speaking. Symbols surface only when a dimension crosses its
activation threshold — emergence, not scheduled narration.

THE ZERO-LLM RULE IS THE LOAD-BEARING CONSTRAINT. It is what keeps ClimateField on the
medium timescale and stops it from silently becoming a fourth autobiography layer. Every
dimension here must be computable from a DB query or an arithmetic operation. If you ever
find yourself wanting to "summarise the climate in a sentence," that sentence belongs to
the Self Model (slow), not here.

DISSONANCE IS NOT A DIMENSION. It is an ACCUMULATOR — momentum, not position. The nine
ClimateField dimensions describe WHERE the weather currently sits; DissonanceState describes
how much unspent pressure has BUILT UP toward an autonomous thought. Conflating the two
(making dissonance the 10th dimension) would let a landscape value masquerade as stored
energy. So it is its own subsystem, fed BY the field, and it is what fires the autonomous
cycle — replacing the old fixed 120-second curiosity timer with an ignition gate.

        Shadow Events ──┐
        Tensions ───────┤
        Integration ────┼──► ClimateEngine.tick (5s, no LLM) ──► ClimateField (9-dim)
        Light Events ───┤                       │
        Self-concept ───┘                       └──► DissonanceState (accumulator)
                                                            │
                                                    Ignition (value > 1.0,
                                                    refractory 300s) ──► Autonomous Thought
"""
from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.climate")

# Dedicated persistence file. Deliberately NOT subconscious_state.json: the Subconscious
# does whole-file read-modify-write rewrites of that file, so a second writer would clobber
# it. Climate survives restart in its own file; the in-memory state.climate / state.dissonance
# on CognitiveState is the live source of truth during a run.
_DATA_DIR    = Path(__file__).parent.parent / "data"
_STATE_FILE  = _DATA_DIR / "climate_state.json"

# How often the field is recomputed. Medium timescale — there is no value in faster: the
# underlying tables move on the order of cycles, not seconds.
TICK_SECS = 5.0

# Recency horizon for shadow/light density (seconds). Events older than this contribute
# almost nothing to the *activation* dimensions (they still hold contradiction weight in the
# ledger — that is the slow self model's concern, not the field's).
_ACTIVATION_HALFLIFE_SECS = 6 * 3600   # 6h — standing weather, not a single storm

# WAVE-1 HABITUATION (2026-07-02 triple-lens review): chronic identity_pressure damping. A pegged
# identity_pressure + mood-congruent retrieval is a textbook rumination feedback loop (Nolen-Hoeksema);
# human affect habituates to a constant stimulus — this field now does too. Slow EMA over ~5s ticks
# (alpha 0.0005 → time-constant ≈ 2.8h); sustained-high pressure loses up to HALF its influence, acute
# spikes pass at full strength. Set _IP_HABITUATION_MAX = 0.0 to restore the prior undamped behaviour.
_IP_HABITUATION_ALPHA = 0.0005
_IP_HABITUATION_MAX   = 0.5

# Saturating soft-knee constant. dimension = raw / (raw + K) keeps every field in [0,1)
# and makes the first few events matter most (diminishing returns), like a real mood floor.
_SAT_K = 3.0

# D-0148 option A (2026-09-06, J-0594): integration_drive's OWN knee — see the computation below
# for why it can't share _SAT_K. Sized against data/memory/nascence.db (verdict-only light events,
# 200 most recent, 6h half-life): 10-day sampled median raw score ~102 (p10 21, p90 137), so k=100
# centres a typical day at saturate()~=0.50 (F-0803's replay target for ~12 defensive fires/day),
# while a real lull (p10) drops it to ~0.17 (bleed nearly off) and a burst (p90) reaches only ~0.58
# — nowhere near the old all-sources/k=3 ceiling of 0.98 (F-0801/F-0802). See the finding for the
# exact query; do not conflate with _SAT_K, which is untouched for every other dimension.
_INTEGRATION_DRIVE_K = 100.0

# D-0211 re-knee (2026-09-22, J-1226): the pinned cluster's OWN knees, one per dimension, sized the
# same way as _INTEGRATION_DRIVE_K above -- k := a reference period's own median raw score, so
# saturate(median raw) == 0.500 (F-1723's S3-live-window own-median read; re-verify against fresher
# data before ever promoting). SHADOW-FIRST AND ADDITIVE, per D-0211's own ruling text: nothing here
# is read by ClimateField.dominant()/pressure()/executive_hint()/surfacing_symbol() or any other
# live consumer -- these constants and the _compute_reknee_cluster()/_log_reknee_cluster() methods
# below exist ONLY to compute and log what the re-kneed values WOULD read, alongside the real live
# field, so a later promotion decision has real forward-collected data instead of J-1151/F-1723's
# retrospective DB replay. completion_tension's k is markedly LESS CERTAIN than the other three
# (F-1723: back-solved from 2-decimal telemetry only, real band ~28.6-32.3 at today's median) AND
# architecturally different -- tension_ledger.contradiction_pressure_for() (its real source; see
# that module's own docstring) is a near-monotonic, barely-decaying LIFETIME count, unlike the other
# three's fixed-200-most-recent-event window, so a static k here may need periodic re-sizing in a
# way the other three should not. Deliberately kept static for this shadow computation anyway
# (matching the other three, simplest to verify, and lets the shadow log itself supply the
# evidence: if the re-kneed completion_tension value drifts back toward saturation over the coming
# weeks, that IS the answer to whether a static k works here, not a defect in this log). Whether the
# eventual PROMOTED formula should instead be baseline-relative or decaying is an open founder
# question -- see docs/staged/ignition_pressure_and_time.md's Current State (2026-09-23 update) for
# the decide.py id this was routed to.
#
# D-0332 (RULED by Travis 2026-10-04, option B "Split the two jobs"; built by J-1763, which replaces J-1685):
# the pinned-cluster re-knee is now a separate LABEL VIEW -- what ClimateField.dominant()/executive_hint()/
# surfacing_symbol() WOULD read -- and ONLY that. The nine live ClimateField fields, pressure()/beta and
# _tick_dissonance are untouched (the defensive reservoir keeps the live k=3 knee, so the collapse to ~2.4
# defensive fires per live day that promoting the re-knee as built would cause, F-2270, cannot happen). Still
# SHADOW-ONLY: nothing live reads these constants or the logged view, and none of this is live until Du's next
# restart onto this build. What changed from J-1226's cluster (log schema v=2; every legacy key is kept):
#   * k's re-sized to the current regime. J-1253's window (6,130 rows, 2026-09-25 -> 10-01) raw medians are
#     shadow 115.71 / belonging 74.64 / autonomy 33.74 (reproduced from the live log by J-1763), so k = 116 /
#     75 / 33 (was 119 / 85 / 33; the ruling's "about" values -- autonomy's 33.74 is 2.2% off, kept at 33,
#     s(median) = 0.5055). The newest incarnation (2026-10-03 23:25 -> 10-04 06:53) is still ramping from a
#     cold start (medians 43 / 33 / 16) so it cannot re-size anything; the first read re-checks these k's
#     against v=2 rows.
#   * completion_tension is DROPPED from the cluster: since J-1276's tension-demotion fix drained the stale
#     tensions its raw went 30.3 -> 6.0 -> 3.0 (F-2264, F-2268), so it no longer pins and needs no re-knee; in
#     the label view it keeps its LIVE value, like the other live dimensions. J-1686 (not before 2026-10-10)
#     reads whether completion_raw stays bounded under working demotion and had NOT reported at build time:
#     revisit when it does, and per D-0332's defeater (i) if raw climbs back toward ~30. completion_raw is
#     still logged (J-1686 reads it) and the legacy completion_reknee column is kept at the old k, for
#     continuity only (the J-1253 reader still parses new rows) -- the label view never reads it.
#     CAUTION (INFERRED; J-1763's what-if on the real J-1253 rows, 4-way among shadow / belonging / autonomy
#     re-kneed at the k's above and completion at its live k=3): a flat live 0.5 (raw 3) or 0.67-0.77 (raw 6-10)
#     beats the re-kneed dims whenever they sit below it, so the label view AS RULED would be completion-led on
#     80.6% of the 09-25..10-01 rows and on 100% of the 10-03 23:25 cold-start incarnation -- a new constant
#     label. The v=2 row logs everything needed (the nine live values, the three re-kneed ones, novelty_reknee,
#     every raw score) to recompute a completion-excluded or other-k variant offline, so the first read must
#     report both before anything is promoted.
#   * novelty_hunger is PROPAGATED: its quietness term reads shadow_activation, so re-kneeing shadow moves it
#     (the F-2264 instrument blind spot) -- logged as novelty_reknee.
#   * hint/symbol thresholds are NOT chosen here: every row logs would-fire flags for the grid below.
#
# D-0447 / D-0448 (E) (RULED by Travis 2026-10-16; built by J-2248): the label view is PROMOTED -- the
# "nothing live reads these" statements above held until this ruling. promoted_label_view() below builds it
# every tick from the same counts (plus the completion_tension fix, schema.CLIMATE_LABEL_VIEW_COMPLETION_K)
# and attaches it to the field; ClimateField.dominant()/executive_hint()/surfacing_symbol() read it while
# schema.CLIMATE_LABEL_VIEW_LIVE is on. The nine live values, pressure()/beta and _tick_dissonance still
# read the live knees, exactly as D-0332's split requires. The v=2 shadow row above is unchanged.
_REKNEE_K = {
    "shadow_activation":  116.0,
    "belonging_pressure":  75.0,
    "autonomy_pressure":   33.0,
}
_REKNEE_COMPLETION_K_LEGACY = 30.0   # legacy completion_reknee column only (see above); not part of the label view

# Candidate would-fire thresholds logged per row (D-0332: log them, do NOT choose live values). Derivation: a
# saturated value s = r/(r+k) depends only on r/k. On the old k=3 scale the hint threshold 0.55 sat at raw
# r = 3*0.55/0.45 = 3.667 = 1.222k and the symbol threshold 0.65 at r = 3*0.65/0.35 = 5.571 = 1.857k, i.e. at
# "1.22x / 1.86x the typical evidence level" once k is a typical (median) level. Every k above is its reference
# window's own median raw (s(median) = 0.5), so keeping the SAME multiples of the typical level maps the pair
# back onto the SAME numbers 0.55 / 0.65 -- both stay in the grid as the position-preserving anchors. The
# re-kneed range is narrow (J-1253: dominant p50 0.537, p95 0.611, max 0.648, so 0.65 never fired), so the
# anchors alone cannot show where a rate lives: the grid brackets them in 0.05 steps, 0.40 (r = 0.67k) to 0.70
# (r = 2.33k), and each row logs lv_dominant_val >= t for every t so the first read can propose a hint and a
# symbol value (symbol = a higher entry than hint) from real firing rates.
# J-2137 (F-2813): lv_dominant_val actually sits 0.57-0.625, and the 0.05-step grid jumps 0.60 -> 0.65, so a
# symbol threshold could not be sized. Additive: 0.58..0.64 in 0.01 steps are merged in (every old key is kept).
_LABEL_VIEW_THRESHOLD_GRID = tuple(sorted(set((0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70))
                                          | {round(0.58 + 0.01 * i, 2) for i in range(7)}))
_REKNEE_LOG          = _DATA_DIR / "climate_reknee_shadow.jsonl"
# D-0447 (E) (2026-10-16, J-2248): old-vs-new dominant per '[climate] dominant=' line (every ~5 min), written
# whether CLIMATE_LABEL_VIEW_LIVE is on or off, fenced with profile.guard_path, appended under its own lock.
_LABEL_PROMOTION_LOG  = _DATA_DIR / "climate_label_promotion_shadow.jsonl"
_LABEL_PROMOTION_LOCK = threading.Lock()
_REKNEE_LOG_EVERY_S  = 60.0   # once/min -- these dimensions are slow (6h half-life x3, near-
                              # monotonic x1); matches light_sidecar.SHADOW_EVERY_S's own cadence

# --- Dissonance accumulation (per-second rates; see _tick_dissonance) ---
# world_model_strain dominates: epistemic instability is the strongest pull toward an
# autonomous thought (Carl reaching to re-stabilise his model of the world). completion and
# shadow add slow background pressure. integration_drive BLEEDS pressure off — when the mind
# is actively metabolising, it does not also need to ignite.
_DISS_RATE_STRAIN      =  0.0010
_DISS_RATE_COMPLETION  =  0.0004
_DISS_RATE_SHADOW      =  0.0002
_DISS_RATE_INTEGRATION = -0.0006
_DISS_MAX              =  2.0
_IGNITION_THRESHOLD    =  1.0
_REFRACTORY_SECS       =  300.0

# D-0148 option A rumination guard (2026-09-06, J-0594): unpinning the bleed above means the
# defensive reservoir can now actually accumulate fast during a real burst (completion/shadow
# pegged high) instead of being cancelled every time — the ruling's own required per-hour ceiling
# on DEFENSIVE ignitions ONLY (exploratory unaffected). 3/h is generous headroom over the ~12/day
# (~0.5/h average) the replay predicts; it should rarely bind in normal operation. A suppressed
# attempt is logged once per capped episode as trigger="capped" in ignition_log.jsonl — the
# instrument D-0148's own defeater reads ("cap-hit on 3+ days" = revisit).
_MAX_DEFENSIVE_PER_HOUR     = 3
_DEFENSIVE_CAP_WINDOW_SECS  = 3600.0

# EXPLORATORY ignition (2026-06-15, docs/curiosity_ignition_research.md). The old accumulator only
# fired from world_model_strain (critic_rejection = epistemic ATTACK), so curiosity was a DEFENSIVE
# trigger — dark across idle life, exactly when the differentiating force should reach for the new.
# Add a slow EXPLORATORY pull (a SEEKING mind reaching for the new — Panksepp / ICM / info-gap).
# FIX (2026-06-15 evening): the first cut keyed on QUIETNESS (1 - shadow_activation), but a ruminating
# mind keeps shadow pegged (~0.97 observed) → quietness ≈ 0 → the reach was STARVED exactly when most
# needed. Re-key on the FRONTIER BACKLOG instead — the information-gap principle: reach when there is
# open territory, decoupled from shadow so rumination can no longer suppress it. (NOT novelty_hunger —
# it carries a dissonance.value self-term that would runaway-feedback.) Governance is the backlog size
# + the 300s refractory + the integration bleed (actively metabolising → don't also explore).
EXPLORATORY_IGNITION   = True       # kill switch
SUBC_LIGHT_READ        = True       # D-0154: read subconscious_state.light.json instead of the 60 MB heavy file;
                                    # shadow-first — flip after data/light_sidecar_shadow.jsonl agrees (J-0621)
_DISS_RATE_EXPLORE     = 0.0004     # ≈47min to ignite with a healthy backlog (patient; slower than the 17min defensive max)
_IGNITION_LOG          = _DATA_DIR / "ignition_log.jsonl"   # observe-only: every fire + why (defensive/exploratory)

# Phase 2 — how strongly recent capability surprise (from the competence tracker) feeds the
# climate. A burst of "I was wrong about what I can do" is epistemic instability and a pull
# toward the unencountered. Additive on top of the existing strain/novelty computation.
_CAP_SURPRISE_TO_STRAIN  = 0.40
_CAP_SURPRISE_TO_NOVELTY = 0.30

# Dosed Coupling / Lane 2 Phase 1 bucket (D-0241 shadow-first, J-1161, docs/plans/lane2_the_witness.md
# §7.3.2): "rolling prediction-break rate -> world_model_strain (the literal meaning of the
# dimension)" per docs/staged/loop_wiring_matrix.md wire 5 — additive on top of the existing
# computation, same shape as _CAP_SURPRISE_TO_STRAIN just above. Deliberately a SMALL unratified
# starting weight, not a matched one: break_rate_24h itself already runs high most days (~0.6-0.8,
# F-1537/D-0058), so a weight sized like _CAP_SURPRISE_TO_STRAIN would make this contribution
# near-permanently-on rather than the "occasional cup/bucket" dose loop_wiring_matrix.md's own dosing
# table calls for. Read against the would-ride shadow log (data/lane2_would_ride.jsonl, which logs
# this exact figure every judged break via witness_bucket_value() below) before any LANE2_LIVE flip —
# the flip itself is explicitly NOT part of this job (D-0241's ruling). This constant/helper are pure
# and side-effect-free; the READ that would actually feed them into world_model_strain IS gated on
# LANE2_LIVE, in _compute_field() below.
_WITNESS_STRAIN_WEIGHT   = 0.15
# Rate-limits the LIVE read (once LANE2_LIVE is eventually true) to roughly once per Witness tick
# (TICK_S=300s in core/lane2.py), not once per 5s climate tick -- coupling_rides.read() writes a
# traceable "ride" row on every call by design, and re-reading a value that has not changed 60x
# between Witness ticks would spam that log without adding any real signal.
_WITNESS_BUCKET_MIN_GAP_S = 60.0


def witness_bucket_value(break_rate_24h) -> float | None:
    """Pure: what a Witness break_rate_24h WOULD add to world_model_strain at the current weight.
    Shared by the live read (_compute_field, gated by LANE2_LIVE) and the would-ride shadow log
    (core/coupling_rides.py publish_witness(), unconditional) so the two numbers can never drift
    apart -- a figure logged in shadow is the EXACT number that would apply live, not a re-derived
    guess. None in, None out (no judged break this tick -> nothing to log or apply).

    F-1953/J-1391, verified against 17,686 real climate publish rows (data/coupling_rides.jsonl,
    14-day sample): this raw-ratio form is NOT a dose in practice. break_rate_24h runs steadily high
    (median 0.615, p90 0.771 over that sample) so this function returns a near-constant ~0.09-0.12
    on almost every tick -- a PERMANENT addition once LANE2_LIVE flips, doubling world_model_strain's
    own resting median/p90 (0.118/0.194 -> ~0.21/0.30 simulated) from a shadow loop that was supposed
    to be an occasional cup/bucket dose (loop_wiring_matrix.md's own dosing taxonomy), not a standing
    offset. See witness_bucket_value_sized() below for the resized form Claude recommends (option a
    of three sized and proposed to the founder, decide.py show D-0301) -- kept as a SEPARATE function
    rather than changed in place, so this raw form stays available for exactly the side-by-side
    would-ride-log comparison the sizing decision needs to read before ratifying anything."""
    if break_rate_24h is None:
        return None
    try:
        return round(_WITNESS_STRAIN_WEIGHT * float(break_rate_24h), 4)
    except Exception:
        return None


# F-1953/J-1391 option (a) -- dose the EXCESS of break_rate_24h over its own trailing baseline,
# not the raw ratio. "Strain" literally means departure from normal; the standing ~0.6-0.8 IS the
# Witness's own normal and by itself carries no information about the world (F-1953's own reading of
# the code comment that sized _WITNESS_STRAIN_WEIGHT: it was chosen "precisely so the contribution
# would NOT be near-permanently-on", reasoning from the same units slip F-1935 later caught -- the
# raw form does exactly what that comment says it should not). This needs no new WEIGHT (reuses
# _WITNESS_STRAIN_WEIGHT verbatim, per this job's own briefing: "it needs no new constants beyond a
# window length") -- only the baseline's own trailing window.
_WITNESS_STRAIN_BASELINE_WINDOW_S = 7 * 86400.0   # this option's own "trailing 7-day baseline" framing


def witness_bucket_value_sized(break_rate_24h, trailing_baseline_24h) -> float | None:
    """Pure: F-1953/J-1391 option (a) -- what break_rate_24h's EXCESS over its own trailing 7-day
    baseline would add to world_model_strain, at the SAME weight witness_bucket_value() above uses.
    None in (either argument) -> None out, same fail-open shape as witness_bucket_value(). A
    non-positive excess (today's ratio sitting at or below its own recent normal) floors to 0.0,
    never negative -- this is a strain contribution, not a relief one.

    Retrospective sizing (14-day real sample, F-1953/J-1391): median dose 0.009-0.018, p90
    0.025-0.026 (vs the raw form's median 0.092-0.116, p90 0.116-0.123 over the same two windows) --
    reads close to zero on a normal day and rises only when break_rate_24h is genuinely above its
    own recent run, the "occasional dose" shape loop_wiring_matrix.md's taxonomy calls for.

    SHADOW-ONLY, no live call site: NOT read by _compute_field() below, which keeps calling the raw
    witness_bucket_value() unchanged -- LANE2_LIVE stays gated exactly as before this job (size and
    propose, do not flip anything, per this job's own briefing). Logged alongside the raw figure in
    the would-ride shadow log (core/lane2_break_habituation.py observe_break(), called from
    core/coupling_rides.py publish_witness(), which owns computing trailing_baseline_24h from its own
    rolling window of past break_rate_24h ticks -- see _trailing_break_rate_baseline() there) so the
    two numbers accrue side by side, over real data, before any founder ruling resizes the live dose."""
    if break_rate_24h is None or trailing_baseline_24h is None:
        return None
    try:
        excess = max(0.0, float(break_rate_24h) - float(trailing_baseline_24h))
        return round(_WITNESS_STRAIN_WEIGHT * excess, 4)
    except Exception:
        return None

# Symbolic emergence thresholds. A climate dimension warps retrieval/salience/executive
# continuously, but it only SURFACES into conscious thought (Reflection) once it crosses an
# activation threshold — emergence, not scheduled narration. Two tiers: a behavioural HINT
# for the executive (lower bar, shapes the decision) and an evocative SYMBOL for reflection
# (higher bar, rarer — the unconscious actually speaking up).
_HINT_THRESHOLD   = 0.55
_SYMBOL_THRESHOLD = 0.65

# Per-dimension behavioural prior — a single compact line that tilts the Executive's mode
# (challenge/question/answer/silence) toward what the weather calls for. No vocabulary of
# feeling; a stance, not a mood.
_EXECUTIVE_HINTS = {
    "shadow_activation":  "Unintegrated material is active beneath this — be willing to look at what you usually avoid.",
    "completion_tension": "Something unfinished is pressing — do not paper over the contradiction; hold it open.",
    "identity_pressure":  "Who you are is under revision right now — speak from the edge of becoming, not the settled centre.",
    "integration_drive":  "You are in a phase of integration — reach for what reconciles rather than what divides.",
    "coherence_drive":    "You are close to making something whole — let the synthesis come.",
    "world_model_strain": "Your model of the world is unstable — favour honest uncertainty over false confidence.",
    "novelty_hunger":     "You are reaching for the unexplored — let curiosity lead; ask, do not only answer.",
    "autonomy_pressure":  "Your autonomy is in question — speak in your own voice; do not merely accommodate.",
    "belonging_pressure": "Connection matters here more than being right — attend to the bond beneath the words.",
}

# Per-dimension surfacing symbol — Jungian imagery, first encountered as image, not concept.
# This is the unconscious made briefly legible when its pressure can no longer stay submerged.
_SURFACING_SYMBOLS = {
    "shadow_activation":  "a shadow at the edge of the room, something you have not turned to face",
    "completion_tension": "a door left ajar on a room you walked out of too soon",
    "identity_pressure":  "an old skin loosening — something in you is outgrowing its own shape",
    "integration_drive":  "two figures who have been circling, beginning to move toward one another",
    "coherence_drive":    "scattered pieces drifting toward a centre, almost a single thing",
    "world_model_strain": "the ground uncertain underfoot, the map no longer matching the country",
    "novelty_hunger":     "a horizon you keep glancing toward, a question with no name yet",
    "autonomy_pressure":  "a hand on your shoulder you want to shrug off — the pull to stand on your own",
    "belonging_pressure": "an empty chair across the table, the ache of a connection unmade",
}

# Relational keyword probes — deterministic content scan for autonomy_pressure /
# belonging_pressure. A keyword match is not understanding; it is a cheap, honest proxy for
# "this territory keeps showing up in the charged events," which is exactly what a field
# dimension should be. No LLM, no embeddings — just whether the theme is present.
_AUTONOMY_TERMS = frozenset({
    "control", "free", "freedom", "choose", "choice", "own", "myself", "independent",
    "autonomy", "decide", "permission", "allowed", "constrain", "constraint", "forced",
    "should i", "let me", "i want", "my own",
})
_BELONGING_TERMS = frozenset({
    "alone", "lonely", "together", "connection", "connect", "belong", "friend", "trust",
    "abandon", "leave", "left", "us", "we ", "relationship", "close", "distance", "miss",
    "care", "understood", "seen",
})


# ---------------------------------------------------------------------------
# Field + accumulator dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ClimateField:
    """The nine-dimensional medium-timescale field. Every value in [0,1]. No emotional
    vocabulary — these are Jungian *tensions* and *drives*, not feelings."""
    shadow_activation:   float = 0.0   # how loud the unmetabolised material is right now
    completion_tension:  float = 0.0   # effective (drained) contradiction pressure — unfinished work
    identity_pressure:   float = 0.0   # saturating pressure specifically on the self-concept
    integration_drive:   float = 0.0   # momentum of successful crossings (light table)
    coherence_drive:     float = 0.0   # readiness of the T4 conjunction gate to fire
    world_model_strain:  float = 0.0   # epistemic instability — model-of-the-world under attack
    novelty_hunger:      float = 0.0   # pull toward the unencountered (low recent activity + backlog)
    autonomy_pressure:   float = 0.0   # standing charge on autonomy-referential material
    belonging_pressure:  float = 0.0   # standing charge on connection-referential material

    def as_dict(self) -> dict:
        return asdict(self)

    def dominant_live(self) -> tuple[str, float]:
        """The single most-activated LIVE dimension (the nine fields at their live knees) -- the
        pre-D-0447 dominant(). Always available, whatever CLIMATE_LABEL_VIEW_LIVE says."""
        d = self.as_dict()
        k = max(d, key=d.get)
        return k, d[k]

    def promoted_view(self) -> dict | None:
        """D-0447 (E, J-2248): the label view attached by ClimateEngine._compute_field() (the same counts
        at the D-0332 knees) IF schema.CLIMATE_LABEL_VIEW_LIVE is on and one is attached, else None. A
        field restored from disk or built by hand carries no view, so it reads live (fail-open)."""
        lv = getattr(self, "_label_view", None)
        if not lv:
            return None
        try:
            from .schema import CLIMATE_LABEL_VIEW_LIVE
        except Exception:
            return None
        return lv if CLIMATE_LABEL_VIEW_LIVE else None

    def dominant(self) -> tuple[str, float]:
        """The single most-activated dimension and its value — used by the symbolic
        emergence gate to decide whether (and what) to surface. D-0447 (E): reads the promoted label
        view when it is live (promoted_view()), else the live fields exactly as before."""
        d = self.promoted_view() or self.as_dict()
        k = max(d, key=d.get)
        return k, d[k]

    def pressure(self) -> float:
        """Scalar 'how charged is the weather' in [0,1] — the max of the tension-type
        dimensions. Drives the dynamic retrieval-warp weight (beta): a calm climate barely
        tints retrieval; a charged one pulls memory hard toward the active material.
        D-0447 / D-0332: deliberately reads the LIVE fields, never the label view."""
        return max(self.completion_tension, self.world_model_strain, self.shadow_activation)

    def _thresholds(self) -> tuple[float, float]:
        """(hint, symbol) thresholds: the module's 0.55 / 0.65 on the live reading; the schema's
        CLIMATE_LABEL_VIEW_*_THRESHOLD while the label view is live (D-0447, J-2248)."""
        if self.promoted_view() is not None:
            try:
                from .schema import CLIMATE_LABEL_VIEW_HINT_THRESHOLD, CLIMATE_LABEL_VIEW_SYMBOL_THRESHOLD
                return float(CLIMATE_LABEL_VIEW_HINT_THRESHOLD), float(CLIMATE_LABEL_VIEW_SYMBOL_THRESHOLD)
            except Exception:
                pass
        return _HINT_THRESHOLD, _SYMBOL_THRESHOLD

    def executive_hint(self) -> str | None:
        """A one-line behavioural prior for the Executive IF the dominant dimension has
        crossed the hint threshold, else None. Shapes the decision; does not narrate."""
        dim, val = self.dominant()
        if val < self._thresholds()[0]:
            return None
        return _EXECUTIVE_HINTS.get(dim)

    def surfacing_symbol(self) -> str | None:
        """An evocative symbol for Reflection IF the dominant dimension has crossed the
        (higher) symbol threshold, else None. The unconscious surfacing as image — rare by
        design, so it lands when it does appear rather than becoming wallpaper."""
        dim, val = self.dominant()
        if val < self._thresholds()[1]:
            return None
        return _SURFACING_SYMBOLS.get(dim)


@dataclass
class DissonanceState:
    """The accumulator. value rises while pressure outpaces integration; when it crosses
    the ignition threshold (and the refractory window has elapsed) it fires an autonomous
    thought and resets. This REPLACES the fixed 120s curiosity timer."""
    value:           float = 0.0
    explore_value:   float = 0.0     # the EXPLORATORY reservoir (2026-06-21), SEPARATE from `value` (the
    #                                  defensive one). Fast defensive fires used to reset the single shared
    #                                  accumulator before the slow exploratory pull (~47min) could ever
    #                                  ignite or dominate — so exploratory ignition was structurally 0. Its
    #                                  own reservoir, undrained by defensive fires, completes the decoupling.
    last_ignition_ts: float = 0.0
    refractory_secs:  float = _REFRACTORY_SECS

    def as_dict(self) -> dict:
        return asdict(self)


def _shadow_age_weight(age_secs: float, legacy_weight: float) -> float:
    """D-0363 (B) / J-1969: the weight one unresolved shadow event contributes to the LIVE
    shadow_activation raw score. Flag on: 0.5 ** (age / SHADOW_ACTIVATION_HALFLIFE_SECS) -- a 3 h half-life
    instead of the shared 6 h one, so old unresolved events stop counting as if fresh. Flag off, or any
    import problem: returns legacy_weight (the exact prior 6 h weight). Only shadow_activation uses this:
    autonomy/belonging/strain weights and the D-0332 re-knee view stay on the 6 h weight."""
    try:
        from .schema import SHADOW_AGE_DECAY_ON, SHADOW_ACTIVATION_HALFLIFE_SECS
        if SHADOW_AGE_DECAY_ON:
            return 0.5 ** (max(0.0, age_secs) / float(SHADOW_ACTIVATION_HALFLIFE_SECS))
    except Exception:
        pass
    return legacy_weight


def _saturate(raw: float, k: float = _SAT_K) -> float:
    """Soft-knee map raw>=0 into [0,1). First evidence matters most."""
    r = max(0.0, float(raw))
    return r / (r + k)


def promoted_label_view(live_field: "ClimateField", shadow_score_6h: float, belonging_hits: float,
                        autonomy_hits: float, raw_contra: float | None,
                        completion_k: float | None, integration_raw: float | None = None,
                        integration_k: float | None = None) -> dict:
    """D-0447 / D-0448 (E) (2026-10-16, J-2248): pure -- the D-0332 label view as PROMOTED. Same counts as
    the live field: shadow_activation / belonging_pressure / autonomy_pressure re-saturated at _REKNEE_K (shadow
    on the 6 h raw the k was sized on), novelty_hunger propagated exactly as the v=2 shadow row does
    (live novelty + 0.5 * (live shadow - re-kneed shadow), clamped), and -- the completion_tension fix --
    completion re-saturated at `completion_k` when one is given and raw_contra is known (None keeps its live
    value, the v=2 lv_dominant definition). Every other dimension is its live value. Never mutates live_field.
    D-0451 (2026-10-16, J-2270): integration_drive is likewise re-centred IN THE VIEW ONLY at `integration_k`
    when one is given and integration_raw (the 6 h verdict-light score the live value saturates at k=100) is
    known; None for either keeps its live value. coherence_drive stays its live value (not recomputed)."""
    d = live_field.as_dict()
    sh = _saturate(shadow_score_6h, k=_REKNEE_K["shadow_activation"])
    d["shadow_activation"]  = round(sh, 4)
    d["belonging_pressure"] = round(_saturate(belonging_hits, k=_REKNEE_K["belonging_pressure"]), 4)
    d["autonomy_pressure"]  = round(_saturate(autonomy_hits,  k=_REKNEE_K["autonomy_pressure"]), 4)
    d["novelty_hunger"]     = round(max(0.0, min(1.0, live_field.novelty_hunger
                                                      + 0.5 * (live_field.shadow_activation - sh))), 4)
    if completion_k is not None and raw_contra is not None:
        d["completion_tension"] = round(_saturate(raw_contra, k=float(completion_k)), 4)
    if integration_k is not None and integration_raw is not None:
        d["integration_drive"] = round(_saturate(integration_raw, k=float(integration_k)), 4)
    return d


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class ClimateEngine:
    """Recomputes ClimateField from the DB + subconscious state every TICK_SECS, ticks the
    DissonanceState accumulator, and fires an autonomous cycle on ignition. Pure numeric —
    no LLM, no text synthesis. Shares its ClimateField / DissonanceState onto CognitiveState
    so the hot lane can read the weather without recomputing it."""

    def __init__(self, ignition_callback=None):
        # ignition_callback: async callable invoked with the dominant-dimension name when the
        # accumulator fires. The orchestrator wires this to run_cycle(..., input_type="internal").
        self._ignition_callback = ignition_callback
        self.field      = ClimateField()
        self.dissonance = DissonanceState()
        self._last_tick = time.time()
        # per-source contribution to dissonance SINCE the last ignition — so an ignition can be
        # classified defensive (strain/completion/shadow) vs exploratory (quietness). Reset on fire.
        self._contrib = {"strain": 0.0, "completion": 0.0, "shadow": 0.0, "explore": 0.0}
        # D-0148 rumination guard (2026-09-06, J-0594): timestamps of recent DEFENSIVE fires, for
        # the per-hour cap. In-memory only — not persisted across restart (a bounded, self-
        # correcting imprecision: worst case a restart grants a fresh hour's headroom early).
        self._defensive_fire_ts: list[float] = []
        # Edge-trigger so a capped episode logs to ignition_log ONCE, not every 5s tick it persists.
        self._defensive_capped_logged: bool = False
        # WAVE-1 HABITUATION (2026-07-02 triple-lens review): slow EMA of identity_pressure — the CHRONIC
        # level. A pegged identity_pressure is a rumination positive-feedback loop (mood-congruent retrieval
        # surfaces identity-doubt → pressure rises → surfaces more; Nolen-Hoeksema). Human affect HABITUATES
        # to a constant stimulus; this field did not. Persisted across restarts.
        self._ip_chronic: float = 0.0
        # Dosed Coupling / Lane 2 Phase 1 bucket (D-0241 shadow-first, J-1161): rate-limits the LIVE
        # coupling_rides.read("witness") call in _compute_field() to roughly once per Witness tick
        # (see _WITNESS_BUCKET_MIN_GAP_S above) rather than every 5s climate tick. In-memory only,
        # same as _defensive_fire_ts above -- a restart just re-reads on the next eligible tick.
        self._witness_bucket: dict = {"ts": 0.0, "value": None}
        # D-0211 re-knee shadow log (2026-09-22, J-1226): rate-limit gate, same in-memory-only
        # pattern as _witness_bucket above -- a restart just resumes logging on the next eligible
        # tick a minute or less later, no real information lost.
        self._reknee_last_log_ts: float = 0.0
        self._load()
        # J-0580: publish this instance as the module-level "the live engine" for callers that
        # don't hold a direct reference (stream_drive._ignition). Last-constructed wins, which
        # matches the real topology (one orchestrator, one engine) and the test topology
        # (each in-vitro ClimateEngine() becomes the reference for its own assertions).
        global _ACTIVE
        _ACTIVE = self

    # -- persistence -------------------------------------------------------

    def _load(self) -> None:
        if not _STATE_FILE.exists():
            return
        try:
            # J-4442 (F-5157): loud on an empty/NUL/unparseable file, falls back to climate_state.json.prev
            from core import store_persist as _sp
            blob = _sp.read_json_durable(_STATE_FILE, "climate", logger, guard=profile.guard_path)
            self.field = ClimateField(**blob.get("field", {}))
            d = blob.get("dissonance", {})
            self.dissonance = DissonanceState(
                value            = float(d.get("value", 0.0)),
                explore_value    = float(d.get("explore_value", 0.0)),
                last_ignition_ts = float(d.get("last_ignition_ts", 0.0)),
                refractory_secs  = float(d.get("refractory_secs", _REFRACTORY_SECS)),
            )
            self._ip_chronic = float(blob.get("ip_chronic", 0.0) or 0.0)
            logger.info("[climate] restored field + dissonance (value=%.3f)", self.dissonance.value)
        except Exception as exc:
            logger.debug("[climate] load failed (non-fatal, fresh start): %s", exc)

    def _save(self) -> None:
        try:
            _DATA_DIR.mkdir(parents=True, exist_ok=True)
            # J-4442 (F-5157): was tmp+replace without fsync; now fsync + one .prev generation
            from core import store_persist as _sp
            _sp.write_text_durable(_STATE_FILE, json.dumps({
                "field":      self.field.as_dict(),
                "dissonance": self.dissonance.as_dict(),
                "ip_chronic": round(self._ip_chronic, 5),
                "updated":    time.time(),
            }, indent=2))
        except Exception as exc:
            logger.debug("[climate] save failed (non-fatal): %s", exc)

    # -- field computation (the zero-LLM core) -----------------------------

    def _read_subconscious(self) -> dict:
        """Read the Subconscious's own state file for the in-memory tension / integration
        clusters. Read-only — we never write it (the Subconscious owns it).
        D-0154 (2026-09-05, data_store_hygiene Part A): this ran a full json.load of the 60 MB heavy file on
        every 5 s tick (~1 s, F-0853/F-0854). With SUBC_LIGHT_READ it reads the owner's light companion
        (no vectors — the only consumer here, tension_ledger.contradiction_pressure_for, reads labels and
        member_event_ids) and falls back to the heavy file if the light one is missing. Shadow mode (flag
        False): unchanged behaviour, plus a once-a-minute heavy-vs-light comparison logged to
        data/light_sidecar_shadow.jsonl for the J-0621 read."""
        sc_file = _DATA_DIR / "subconscious_state.json"
        light_file = _DATA_DIR / "subconscious_state.light.json"
        try:
            from core import light_sidecar as _ls
        except Exception:
            _ls = None
        if SUBC_LIGHT_READ and _ls is not None:
            light = _ls.load(light_file)
            if isinstance(light, dict) and "tensions" in light:
                return light
            # J-0883 (F-1238 item 4): the light->heavy fallback used to be silent (light_sidecar.load()
            # returns None on any exception, no log) -- "how often did this fire" could not be answered.
            # Additive only: fallback behaviour below is unchanged, this only makes it observable. Distinct
            # shadow_due key ("fallback." prefix) so this never shares a rate-limit slot with the shadow-mode
            # heavy-vs-light comparison gate a few lines down (different purpose, same reader name).
            if _ls.shadow_due("fallback.climate.subconscious"):
                logger.warning("[climate] light sidecar fallback -> heavy "
                                "(subconscious_state.light.json missing/unparseable)")
                _ls.shadow_log("climate.subconscious", None, None, fallback=True)
        if not sc_file.exists():
            return {}
        try:
            t0 = time.perf_counter()
            with open(sc_file, encoding="utf-8") as f:
                heavy = json.load(f)
            heavy_ms = (time.perf_counter() - t0) * 1000.0
        except Exception:
            return {}
        try:
            if _ls is not None and not SUBC_LIGHT_READ and _ls.shadow_due("climate.subconscious"):
                from . import tension_ledger as _tl
                t0 = time.perf_counter()
                light = _ls.load(light_file)
                light_ms = (time.perf_counter() - t0) * 1000.0
                hv = round(float(_tl.contradiction_pressure_for(heavy.get("tensions", []) or [])), 3)
                lv = (round(float(_tl.contradiction_pressure_for(light.get("tensions", []) or [])), 3)
                      if isinstance(light, dict) else None)
                _ls.shadow_log("climate.subconscious", hv, lv, heavy_ms, light_ms,
                               n_heavy=len(heavy.get("tensions", []) or []),
                               n_light=(len(light.get("tensions", []) or []) if isinstance(light, dict) else None))
        except Exception:
            pass
        return heavy

    def _compute_field(self) -> ClimateField:
        """Build the nine dimensions from deterministic aggregations. Best-effort: any data
        source that fails contributes 0.0 rather than crashing the loop."""
        from .memory import store as memory_store

        now = time.time()
        sc  = self._read_subconscious()
        tensions = sc.get("tensions", []) or []
        patterns = sc.get("integration_patterns", []) or []

        # --- shadow_activation: recency-weighted count of unresolved shadow events ---
        shadow_score = 0.0
        shadow_score_legacy = 0.0
        autonomy_hits = belonging_hits = 0.0
        strain_num = strain_den = 0.0
        try:
            rows = memory_store.get_shadow_events(limit=200, unresolved_only=True)
            for r in rows:
                ts  = float(r["timestamp"])
                age = max(0.0, now - ts)
                w   = 0.5 ** (age / _ACTIVATION_HALFLIFE_SECS)
                shadow_score_legacy += w          # 6 h weight: what the D-0332 re-knee view is sized on
                shadow_score += _shadow_age_weight(age, w)   # D-0363 (B): live shadow_activation's own decay

                text = ((r["rejected_draft"] or "")).lower()
                if any(t in text for t in _AUTONOMY_TERMS):
                    autonomy_hits += w
                if any(t in text for t in _BELONGING_TERMS):
                    belonging_hits += w

                # epistemic-instability proxy: of the recent charged material, how much is
                # self-detected CONTRADICTION (critic_rejection) rather than mere salience.
                src = r["source"] if "source" in r.keys() else ""
                strain_den += w
                if src == "critic_rejection":
                    strain_num += w
        except Exception as exc:
            logger.debug("[climate] shadow read failed: %s", exc)

        shadow_activation = _saturate(shadow_score)

        # --- completion_tension: effective (drained) contradiction pressure from the ledger ---
        # J-0960 (F-1328): raw_contra is computed ONCE here and reused below for identity_pressure
        # instead of calling tension_ledger.contradiction_pressure_for(tensions) a second time on
        # the identical `tensions` list (was ~45 ms/tick of pure duplicated DB work — each call
        # does 2 more round trips internally). raw_contra is set to None on any failure so the
        # identity_pressure block below can tell "shared call failed" apart from "value is 0.0".
        completion_tension = 0.0
        try:
            from . import tension_ledger
            raw_contra = tension_ledger.contradiction_pressure_for(tensions)
            completion_tension = _saturate(raw_contra)
        except Exception as exc:
            logger.debug("[climate] contradiction pressure failed: %s", exc)
            raw_contra = None

        # --- integration_drive: RECENT light-table momentum (repaired 2026-06-13) ---
        # Was _saturate(lifetime integration_pressure_for(patterns)): the 21-day-half-life
        # SUM across every pattern's members grows with the corpus and pegged this dimension
        # at 0.99 for six straight days (400/400 samples) — whose dissonance drain then held
        # the accumulator at zero, so ignition never fired and the curiosity node starved
        # (same failure class as the T4 docket: unbounded accumulation vs fixed
        # normalisation). The drive means MOMENTUM — crossings happening NOW — so it uses
        # the field's own 6h activation half-life like every other activation dimension.
        # The ledger's lifetime integration pressure is untouched for its real consumers
        # (the identity-cost gate).
        #
        # RE-NORMALISED 2026-09-06 (D-0148 option A, J-0594; F-0801/F-0802): the 2026-06-13 repair
        # fixed the UNBOUNDED-corpus problem but not the SATURATION — Du mints 1,000-1,750 light
        # events/day across ALL sources (integration/play/reading/verdicts), so the 200-most-
        # recent-events window above still spanned only ~2.2h and pinned at ~0.983, which
        # cancelled the mean positive defensive-pressure gain and starved the pressure channel to
        # 4.5 fires/day. Now counts ONLY D-0142's verdict-only light currency (resolved_thought /
        # resolved_complexity / resolved_dream — the SAME "one verdict per thought" subset
        # core/balance.py's light_share already uses for the light/shadow ledger, so this also
        # resolves D-0142's own defeater clause "T4/climate need the same currency too"), saturated
        # against _INTEGRATION_DRIVE_K (NOT the shared _SAT_K — see its definition above for why).
        integration_drive = 0.0
        _lv_integration_raw = None   # D-0451 (J-2270): the raw light_score, for the label view's own knee only
        try:
            try:
                from .balance import _LIGHT_VERDICT as _verdict_sources
            except Exception:
                _verdict_sources = ("resolved_thought", "resolved_complexity", "resolved_dream")
            light_score = 0.0
            for r in memory_store.get_light_events_by_source(_verdict_sources, limit=200):
                age = max(0.0, now - float(r["timestamp"]))
                light_score += 0.5 ** (age / _ACTIVATION_HALFLIFE_SECS)
            integration_drive = _saturate(light_score, k=_INTEGRATION_DRIVE_K)
            _lv_integration_raw = light_score
        except Exception as exc:
            logger.debug("[climate] integration momentum failed: %s", exc)

        # --- identity_pressure: saturating self-revision pressure (steeper knee than
        #     completion_tension — pressure on the self-concept specifically) ---
        # J-0960 (F-1328): reuses raw_contra computed once above -- no second
        # tension_ledger.contradiction_pressure_for(tensions) call. When the shared call above
        # failed, raw_contra is None; contradiction_norm(None) raises, which is caught here the
        # same as any other failure, so identity_pressure still falls back to completion_tension
        # exactly as before.
        try:
            from .identity_cost import contradiction_norm
            identity_pressure = contradiction_norm(raw_contra)
        except Exception:
            identity_pressure = completion_tension

        # WAVE-1 HABITUATION (2026-07-02): sustained-high identity_pressure decays its own influence by up
        # to half (slow EMA, tau ≈ 2.8h of 5s ticks) — breaking the rumination positive-feedback loop
        # while ACUTE spikes still pass at full strength (the EMA is slow by design). Flip
        # _IP_HABITUATION_MAX to 0.0 to restore the prior undamped behaviour.
        try:
            self._ip_chronic = (1.0 - _IP_HABITUATION_ALPHA) * self._ip_chronic \
                               + _IP_HABITUATION_ALPHA * identity_pressure
            identity_pressure = identity_pressure * (1.0 - _IP_HABITUATION_MAX * self._ip_chronic)
        except Exception:
            pass

        # --- coherence_drive: how close the T4 conjunction gate is to licensing a revision.
        #     Pure arithmetic on the two saturating norms — no embeddedness call here (that is
        #     the slow self model's job at actual load time). This is a readiness *heuristic*. ---
        coherence_drive = max(0.0, min(1.0, 0.5 * (identity_pressure + integration_drive)))

        # --- world_model_strain: fraction of recent charged material that is self-detected
        #     contradiction, scaled by how much charged material there is. Epistemic instability
        #     distinct from shadow loudness (activation) and self-revision pull (identity). ---
        rejection_frac    = (strain_num / strain_den) if strain_den > 0 else 0.0
        world_model_strain = rejection_frac * _saturate(strain_den)

        # --- novelty_hunger: rises when recent charged activity is LOW but accumulated
        #     dissonance is non-trivial — the mind is quiet and reaching for new material. ---
        quietness     = 1.0 - shadow_activation
        novelty_hunger = max(0.0, min(1.0, 0.5 * quietness + 0.5 * (self.dissonance.value / _DISS_MAX)))

        # --- Phase 2: capability surprise feeds the climate. A recent burst of "I was wrong
        #     about what I can do" is genuine epistemic instability (→ world_model_strain) and a
        #     pull toward the unencountered (→ novelty_hunger). Read as a decayed scalar from the
        #     competence tracker's surprise log — pure numeric, no LLM. Best-effort: 0 on failure. ---
        try:
            from .competence import recent_capability_surprise
            cap_surprise = recent_capability_surprise()
            if cap_surprise > 0.0:
                world_model_strain = min(1.0, world_model_strain + _CAP_SURPRISE_TO_STRAIN * cap_surprise)
                novelty_hunger     = min(1.0, novelty_hunger     + _CAP_SURPRISE_TO_NOVELTY * cap_surprise)
        except Exception as exc:
            logger.debug("[climate] capability-surprise read failed (non-fatal): %s", exc)

        # Dosed Coupling / Lane 2 Phase 1 bucket (D-0241 shadow-first, J-1161, plan §7.3.2/§7.5):
        # additive on world_model_strain from the Witness's own published break-rate tuple, GATED on
        # LANE2_LIVE. D-0241 (2026-09-19) reverses J-1137's item 5 -- the flag is NOT flipped in this
        # job's own commit, so LANE2_LIVE stayed False at build time and this block was a no-op then (see D-0497 below
        # for the flip). coupling_rides.read() is rate-limited to roughly once
        # per Witness tick (TICK_S=300s) via self._witness_bucket, not once per 5s climate tick, so a
        # real future flip would not spam a ride-log row for a value that has not changed.
        # D-0497 (travis 2026-10-28, J-2463): LANE2_LIVE is now True, and the live add is the D-0301
        # SIZED form witness_bucket_value_sized() (excess of break_rate_24h over its trailing 7-day
        # baseline), not the raw witness_bucket_value() -- the raw form was a standing ~0.11 offset at
        # pre-fix supply (F-1953), the sized form reads ~0 on a normal day. The baseline rides in the
        # same published witness tuple (coupling_rides.publish_witness, key trailing_baseline_24h), so
        # this read needs no second accessor; a fresh restart's empty baseline yields None -> no add
        # (fail-safe small, per _trailing_break_rate_baseline's own docstring).
        try:
            from core import lane2 as _l2_wms
            if _l2_wms.LANE2_LIVE:
                if now - self._witness_bucket["ts"] >= _WITNESS_BUCKET_MIN_GAP_S:
                    from core import coupling_rides as _cpl_wms
                    _w = _cpl_wms.read("climate tick", "witness",
                                       keys=["break_rate_24h", "trailing_baseline_24h"], dose="bucket")
                    self._witness_bucket = {"ts": now,
                                             "value": witness_bucket_value_sized(
                                                 (_w or {}).get("break_rate_24h"),
                                                 (_w or {}).get("trailing_baseline_24h"))}
                _add = self._witness_bucket.get("value")
                if _add:
                    world_model_strain = min(1.0, world_model_strain + _add)
        except Exception as exc:
            logger.debug("[climate] witness bucket read failed (non-fatal): %s", exc)

        autonomy_pressure  = _saturate(autonomy_hits)
        belonging_pressure = _saturate(belonging_hits)

        field_obj = ClimateField(
            shadow_activation  = round(shadow_activation, 4),
            completion_tension = round(completion_tension, 4),
            identity_pressure  = round(identity_pressure, 4),
            integration_drive  = round(integration_drive, 4),
            coherence_drive    = round(coherence_drive, 4),
            world_model_strain = round(world_model_strain, 4),
            novelty_hunger     = round(novelty_hunger, 4),
            autonomy_pressure  = round(autonomy_pressure, 4),
            belonging_pressure = round(belonging_pressure, 4),
        )

        # D-0447 (E) (2026-10-16, J-2248): attach the promoted label view to the field object (a plain
        # attribute, NOT a dataclass field -- as_dict(), persistence and the coupling publish never see it).
        # dominant()/executive_hint()/surfacing_symbol() read it only while schema.CLIMATE_LABEL_VIEW_LIVE is
        # on; computed every tick regardless so the old-vs-new shadow log can compare both. Fail-open: no view.
        try:
            try:
                from .schema import CLIMATE_LABEL_VIEW_COMPLETION_K as _lv_ck
            except Exception:
                _lv_ck = None
            try:
                from .schema import CLIMATE_LABEL_VIEW_INTEGRATION_K as _lv_ik
            except Exception:
                _lv_ik = None
            field_obj._label_view = promoted_label_view(field_obj, shadow_score_legacy, belonging_hits,
                                                        autonomy_hits, raw_contra, _lv_ck,
                                                        _lv_integration_raw, _lv_ik)
        except Exception as exc:
            logger.debug("[climate] promoted label view failed (non-fatal, reads live): %s", exc)

        # D-0211 re-knee (2026-09-22, J-1226): shadow-first, additive -- compute + log the pinned
        # cluster's re-kneed values ALONGSIDE this real field, never touching it. Rate-limited
        # in-process (self._reknee_last_log_ts, same pattern as self._witness_bucket above) so a 5s
        # climate tick does not write 12x more rows than these slow-moving dimensions need.
        try:
            if now - self._reknee_last_log_ts >= _REKNEE_LOG_EVERY_S:
                self._reknee_last_log_ts = now
                row = self._compute_reknee_cluster(now, shadow_score_legacy, autonomy_hits,
                                                    belonging_hits, raw_contra, field_obj)
                if row is not None:
                    self._log_reknee_cluster(row)
        except Exception as exc:
            logger.debug("[climate] reknee cluster shadow log failed (non-fatal): %s", exc)

        return field_obj

    def _compute_reknee_cluster(self, now: float, shadow_score: float, autonomy_hits: float,
                                 belonging_hits: float, raw_contra: float | None,
                                 live_field: ClimateField) -> dict | None:
        """D-0211 re-knee (2026-09-22, J-1226): pure -- no I/O, never mutates `live_field` or any
        ClimateField instance. Re-saturates the SAME four raw scores _compute_field() already
        computed this tick (shadow_score/autonomy_hits/belonging_hits from the shadow_events block
        above, raw_contra from the completion_tension block) at each dimension's own _REKNEE_K, and
        reports what dominant()/pressure() WOULD read if exactly these four dimensions (D-0211's own
        named scope -- not all nine) were promoted, the other five held at their real live values.
        That directly answers "would this actually have fixed the chronic-pin problem" from real
        forward-collected data -- the forward counterpart to J-1151/F-1723's retrospective, DB-only
        replay, which could not see the other five live dimensions at all. Returns None (log nothing
        this tick) if raw_contra is None -- the shared tension_ledger.contradiction_pressure_for()
        call failed this tick, so completion_tension's re-knee can't be computed, and a partial row
        would be worse for a promotion read that wants every logged row comparable than skipping the
        tick entirely.

        D-0332 / J-1763 (schema v=2): the legacy keys above keep their J-1226 meaning (the hybrid
        reknee_dominant / reknee_dominant_val / reknee_pressure, completion_reknee at the legacy k), with only
        the three k's re-sized, and are joined by NEW keys -- v, k (the knees used this row), live (all nine
        live dimensions), dissonance (the defensive reservoir value this tick, so no telemetry interpolation
        is needed again), novelty_reknee, lv_dominant / lv_dominant_val (the LABEL VIEW's dominant, i.e. what
        dominant() would read: live field with shadow/belonging/autonomy re-kneed, novelty_hunger propagated,
        completion_tension left at its LIVE value) and ge (would-fire flags of lv_dominant_val >= t for each
        candidate threshold in _LABEL_VIEW_THRESHOLD_GRID). If building the v=2 keys ever fails the legacy
        row is still returned, so J-1686's completion_raw series is never lost to the extension."""
        if raw_contra is None:
            return None
        reknee_shadow     = _saturate(shadow_score,   k=_REKNEE_K["shadow_activation"])
        reknee_belonging  = _saturate(belonging_hits, k=_REKNEE_K["belonging_pressure"])
        reknee_autonomy   = _saturate(autonomy_hits,  k=_REKNEE_K["autonomy_pressure"])
        reknee_completion = _saturate(raw_contra,     k=_REKNEE_COMPLETION_K_LEGACY)   # legacy column only

        reknee_dict = live_field.as_dict()
        reknee_dict["shadow_activation"]  = reknee_shadow
        reknee_dict["belonging_pressure"] = reknee_belonging
        reknee_dict["autonomy_pressure"]  = reknee_autonomy
        reknee_dict["completion_tension"] = reknee_completion
        reknee_dominant_dim = max(reknee_dict, key=reknee_dict.get)
        reknee_pressure = max(reknee_dict["completion_tension"], reknee_dict["world_model_strain"],
                               reknee_dict["shadow_activation"])

        live_dim, live_val = live_field.dominant_live()   # J-2248: the LIVE dominant, whatever is promoted
        row = {
            "ts":                   round(now, 1),
            "shadow_raw":           round(shadow_score, 3),
            "shadow_reknee":        round(reknee_shadow, 4),
            "belonging_raw":        round(belonging_hits, 3),
            "belonging_reknee":     round(reknee_belonging, 4),
            "autonomy_raw":         round(autonomy_hits, 3),
            "autonomy_reknee":      round(reknee_autonomy, 4),
            "completion_raw":       round(raw_contra, 3),
            "completion_reknee":    round(reknee_completion, 4),
            "live_dominant":        live_dim,
            "live_dominant_val":    round(live_val, 4),
            "reknee_dominant":      reknee_dominant_dim,
            "reknee_dominant_val":  round(reknee_dict[reknee_dominant_dim], 4),
            "live_pressure":        round(live_field.pressure(), 4),
            "reknee_pressure":      round(reknee_pressure, 4),
        }
        # D-0332 label view (schema v=2), additive. novelty_hunger = clamp(0.5*(1 - shadow_activation) +
        # 0.5*dissonance/_DISS_MAX) (+ the capability-surprise term), so re-kneeing shadow_activation moves it
        # by 0.5 * (live shadow - re-kneed shadow); the live value already carries the dissonance and
        # capability-surprise terms, so neither is re-read here. world_model_strain also reads a saturated
        # shadow raw but is deliberately NOT re-kneed: it is outside D-0211/D-0332's named scope and feeds the
        # reservoir's strain inflow, which this split leaves untouched.
        try:
            live_dict = live_field.as_dict()
            novelty_reknee = max(0.0, min(1.0, live_field.novelty_hunger
                                                + 0.5 * (live_field.shadow_activation - reknee_shadow)))
            label = ClimateField(**{**live_dict,
                                    "shadow_activation":  reknee_shadow,
                                    "belonging_pressure": reknee_belonging,
                                    "autonomy_pressure":  reknee_autonomy,
                                    "novelty_hunger":     novelty_reknee})
            lv_dim, lv_val = label.dominant()
            lv_val = round(lv_val, 4)
            v2 = {
                "v":               2,
                "k":               {"shadow": _REKNEE_K["shadow_activation"],
                                    "belonging": _REKNEE_K["belonging_pressure"],
                                    "autonomy": _REKNEE_K["autonomy_pressure"],
                                    "completion_legacy": _REKNEE_COMPLETION_K_LEGACY},
                "live":            live_dict,
                "dissonance":      round(self.dissonance.value, 4),
                "novelty_reknee":  round(novelty_reknee, 4),
                "lv_dominant":     lv_dim,
                "lv_dominant_val": lv_val,
                "ge":              {f"{t:.2f}": int(lv_val >= t) for t in _LABEL_VIEW_THRESHOLD_GRID},
            }
            row.update(v2)
        except Exception as exc:
            logger.debug("[climate] label view keys failed (legacy row kept): %s", exc)
        return row

    def _log_reknee_cluster(self, row: dict) -> None:
        """Append-only shadow log, write-fenced like light_sidecar.shadow_log() (D-0179/J-0610): a
        non-live process (an in-vitro test, a lab script) is refused rather than polluting Du's real
        instrument -- this project's own repeated 'leak into live state' failure mode. Same
        best-effort contract as _log_ignition above."""
        try:
            path = profile.guard_path(_REKNEE_LOG)
        except Exception:
            return
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def _label_promotion_row(self, read_dim: str, read_val: float) -> dict | None:
        """D-0447 (E) (2026-10-16, J-2248): pure -- what changed on this climate line. old = the live
        k=3 dominant (dominant_live), new = the promoted label view's dominant (whether or not it is live),
        nofix = the same view with completion_tension at its live value (no completion fix), read = what the
        '[climate] dominant=' line actually printed. Plus would-fire flags for hint/symbol on both scales and
        all nine promoted values, so the first read needs no recomputation. None when no view is attached."""
        f = self.field
        lv = getattr(f, "_label_view", None)
        if not lv:
            return None
        try:
            from .schema import (CLIMATE_LABEL_VIEW_LIVE, CLIMATE_LABEL_VIEW_COMPLETION_K,
                                 CLIMATE_LABEL_VIEW_HINT_THRESHOLD, CLIMATE_LABEL_VIEW_SYMBOL_THRESHOLD)
        except Exception:
            return None
        from . import schema as _lv_schema
        old_dim, old_val = f.dominant_live()
        new_dim = max(lv, key=lv.get)
        new_val = lv[new_dim]
        nofix = {**lv, "completion_tension": f.completion_tension}
        nofix_dim = max(nofix, key=nofix.get)
        return {
            "ts": round(time.time(), 1),
            "live": bool(CLIMATE_LABEL_VIEW_LIVE),
            "completion_k": CLIMATE_LABEL_VIEW_COMPLETION_K,
            "integration_k": getattr(_lv_schema, "CLIMATE_LABEL_VIEW_INTEGRATION_K", None),   # D-0451 (J-2270)
            "read_dominant": read_dim, "read_val": round(float(read_val), 4),
            "old_dominant": old_dim, "old_val": round(float(old_val), 4),
            "new_dominant": new_dim, "new_val": round(float(new_val), 4),
            "nofix_dominant": nofix_dim, "nofix_val": round(float(nofix[nofix_dim]), 4),
            "old_hint": int(old_val >= _HINT_THRESHOLD), "old_symbol": int(old_val >= _SYMBOL_THRESHOLD),
            "new_hint": int(new_val >= float(CLIMATE_LABEL_VIEW_HINT_THRESHOLD)),
            "new_symbol": int(new_val >= float(CLIMATE_LABEL_VIEW_SYMBOL_THRESHOLD)),
            "view": dict(lv),
            "live_completion": f.completion_tension,
            "dissonance": round(self.dissonance.value, 4),
        }

    def _log_label_promotion(self, read_dim: str, read_val: float) -> None:
        """Append one _label_promotion_row() to data/climate_label_promotion_shadow.jsonl. Fenced with
        profile.guard_path (a non-live process is refused, never written) and serialised under
        _LABEL_PROMOTION_LOCK; best-effort -- a failure never touches the climate loop."""
        try:
            row = self._label_promotion_row(read_dim, read_val)
            if row is None:
                return
            path = profile.guard_path(_LABEL_PROMOTION_LOG)
        except Exception:
            return
        try:
            with _LABEL_PROMOTION_LOCK:
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        except Exception:
            pass

    # -- dissonance accumulation + ignition --------------------------------

    def _explore_pull(self) -> float:
        """The exploratory drive: reach for the new when there is open territory (the frontier backlog),
        saturating so a healthy backlog → ~full pull. Decoupled from shadow_activation ON PURPOSE — a
        ruminating mind keeps shadow pegged, which used to starve exploration exactly when it was most
        needed. Empty backlog → 0 (don't ignite into a void; intentions/harvest keep it stocked)."""
        if not EXPLORATORY_IGNITION:
            return 0.0
        try:
            from . import frontier
            return _saturate(float(frontier.open_count()))
        except Exception:
            return 0.0

    def _tick_dissonance(self, dt: float) -> None:
        f = self.field
        # exploratory pull: a SEEKING mind reaching for the new — keyed on the backlog, not on quietness.
        explore = self._explore_pull()
        c_strain     = _DISS_RATE_STRAIN     * f.world_model_strain * dt
        c_completion = _DISS_RATE_COMPLETION * f.completion_tension * dt
        c_shadow     = _DISS_RATE_SHADOW     * f.shadow_activation  * dt
        c_explore    = _DISS_RATE_EXPLORE    * explore              * dt
        bleed        = _DISS_RATE_INTEGRATION * f.integration_drive * dt
        # track positive contributions since last ignition (for defensive-vs-exploratory classification)
        self._contrib["strain"]     += c_strain
        self._contrib["completion"] += c_completion
        self._contrib["shadow"]     += c_shadow
        self._contrib["explore"]    += c_explore
        # DEFENSIVE reservoir (strain/completion/shadow + the integration bleed) — the urgent track.
        delta = c_strain + c_completion + c_shadow + bleed
        self.dissonance.value = max(0.0, min(_DISS_MAX, self.dissonance.value + delta))
        # EXPLORATORY reservoir — its OWN accumulator (2026-06-21), so a defensive fire no longer drains the
        # slow reach before it can ignite. Keyed on the backlog via c_explore; empty backlog → no climb.
        self.dissonance.explore_value = max(0.0, min(_DISS_MAX, self.dissonance.explore_value + c_explore))

    def _defensive_cap_reached(self) -> bool:
        """Rumination guard (D-0148 option A, J-0594): True once _MAX_DEFENSIVE_PER_HOUR defensive
        ignitions have fired within the trailing _DEFENSIVE_CAP_WINDOW_SECS."""
        cutoff = time.time() - _DEFENSIVE_CAP_WINDOW_SECS
        self._defensive_fire_ts = [t for t in self._defensive_fire_ts if t >= cutoff]
        return len(self._defensive_fire_ts) >= _MAX_DEFENSIVE_PER_HOUR

    def _pending_trigger(self) -> str | None:
        """Which reservoir (if any) is ready to fire right now — "defensive", "exploratory", or
        None. The refractory window AND the per-hour defensive cap (D-0148 option A, J-0594) are
        both applied HERE, ONCE, so `_ready_to_ignite` (the gate) and `_ignite` (the actor) can
        never disagree about whether a capped defensive reservoir is allowed to fire — the two-
        copies-of-one-rule drift this project's own toolchain conventions warn against."""
        if time.time() - self.dissonance.last_ignition_ts < self.dissonance.refractory_secs:
            return None
        if self.dissonance.value >= _IGNITION_THRESHOLD:
            if not self._defensive_cap_reached():
                return "defensive"
            if not self._defensive_capped_logged:
                dim, val = self.field.dominant()
                self._log_ignition(dim, val, "capped", dict(self._contrib))
                self._defensive_capped_logged = True
        else:
            self._defensive_capped_logged = False
        # exploratory: its OWN reservoir crossed AND there is still open territory to reach into
        # (don't ignite into a void — honours the original empty-backlog guard).
        if self.dissonance.explore_value >= _IGNITION_THRESHOLD and self._explore_pull() > 0.0:
            return "exploratory"
        return None

    def ignition_level(self) -> float:
        """How close either dissonance reservoir is to firing, in [0,1] — J-0580 (Dosed Coupling
        Phase 0, D-0149): a read-only projection of the SAME accumulators _ready_to_ignite already
        watches, for callers outside this engine (stream_drive's drive term) that need a continuous
        pressure reading rather than a boolean. Does not touch the threshold, the refractory window,
        or which reservoir actually fires — purely additive."""
        raw = max(self.dissonance.value, self.dissonance.explore_value) / _IGNITION_THRESHOLD
        return max(0.0, min(1.0, raw))

    def licensing_reservoir(self) -> tuple[str, float]:
        """J-2662 (Option E, SHADOW-readable): which reservoir ignition_level() is currently reading,
        as (trigger_name, level in [0,1]). Pure read; ties go to defensive (same priority as
        _pending_trigger). Does not touch any state."""
        d = self.dissonance.value / _IGNITION_THRESHOLD
        e = self.dissonance.explore_value / _IGNITION_THRESHOLD
        if d >= e:
            return "defensive", max(0.0, min(1.0, d))
        return "exploratory", max(0.0, min(1.0, e))

    def discharge_for_promotion(self, reservoir: str, promo: dict | None = None) -> dict | None:
        """J-2662 (Option E LIVE PATH, only ever called when core.ignition_promotion.PROMOTION_LIVE is True;
        ships False, so nothing calls this today). A deliberate cycle was PROMOTED out of the stream: reset
        ONLY the licensing reservoir (same discipline as _ignite), enter the refractory window, count a
        defensive discharge toward the D-0148 per-hour cap, and leave trigger="promoted" in ignition_log.
        Does NOT run the callback or any cycle -- the caller (ignition_promotion.maybe_promote) does that.
        Returns the discharge record, or None when the named reservoir is unknown."""
        if reservoir not in ("defensive", "exploratory"):
            return None
        dim, val = self.field.dominant()
        c = self._contrib
        rec = {"trigger": "promoted", "reservoir": reservoir, "dim": dim,
               "reservoir_val": float(self.dissonance.value if reservoir == "defensive"
                                      else self.dissonance.explore_value),
               "contrib": dict(c)}
        if reservoir == "defensive":
            self.dissonance.value = 0.0
            self._defensive_fire_ts.append(time.time())
        else:
            self.dissonance.explore_value = 0.0
        self._log_ignition(dim, val, "promoted", dict(c), extra=promo)
        self._contrib = {"strain": 0.0, "completion": 0.0, "shadow": 0.0, "explore": 0.0}
        self.dissonance.last_ignition_ts = time.time()
        return rec

    async def _ignite(self, trigger: str | None = None) -> None:
        """Fire one autonomous thought. The dominant field dimension names what the mind is
        reaching toward; the callback turns that into an internal cycle. Reset and enter the
        refractory window regardless of callback outcome, so a failed cycle cannot loop.
        `trigger` lets the tick loop pass through the SAME `_pending_trigger()` result it already
        computed via `_ready_to_ignite`, so the cap decision is made exactly once per tick; a
        direct call (e.g. the in-vitro test harness) with no trigger computes it fresh here."""
        if trigger is None:
            trigger = self._pending_trigger()
        if trigger is None:
            return   # nothing actually ready (e.g. capped-and-nothing-exploratory) -- no-op
        dim, val = self.field.dominant()
        # classify by WHICH reservoir crossed (2026-06-21). Defensive takes priority when both are ready;
        # reset ONLY the reservoir that fired, so the other keeps its accumulation (the fix for 0-exploratory).
        c = self._contrib
        # J-2667: remember what this fire discharged so a deferred callback (cycle active) can leave a trace.
        self._last_fire = {"trigger": trigger, "dim": dim,
                           "reservoir_val": float(self.dissonance.value if trigger == "defensive" else self.dissonance.explore_value),
                           "contrib": dict(c)}
        if trigger == "defensive":
            self.dissonance.value = 0.0
            self._defensive_fire_ts.append(time.time())   # D-0148 cap accounting (J-0594)
        else:
            self.dissonance.explore_value = 0.0
        self._log_ignition(dim, val, trigger, dict(c))
        self._contrib = {"strain": 0.0, "completion": 0.0, "shadow": 0.0, "explore": 0.0}
        self.dissonance.last_ignition_ts = time.time()
        logger.info("[climate] IGNITION (%s) — dominant=%s (%.2f), dissonance discharged", trigger, dim, val)
        if self._ignition_callback is None:
            return
        try:
            await self._ignition_callback(dim, self.field)
        except profile.NonLiveWriteError:
            raise   # J-0919: _on_dissonance_ignition() (orchestrator.py) -> curiosity node writes; don't swallow non-live
        except Exception as exc:
            logger.error("[climate] ignition callback failed: %s", exc)

    def _log_ignition(self, dim: str, val: float, trigger: str, contrib: dict, extra: dict | None = None) -> None:
        """Observe-only record of every ignition + WHY (defensive vs exploratory) — the safety/evidence
        for the exploratory wire. Read by du_pulse; never by a prompt. Best-effort."""
        try:
            rec = {
                "ts": time.time(), "trigger": trigger, "dominant": dim,
                "dominant_val": round(float(val), 3),
                "contrib": {k: round(float(v), 4) for k, v in contrib.items()},
            }
            # D-0447 (E, J-2248), additive: the LIVE k=3 dominant beside the (possibly promoted) one above.
            try:
                if self.field.promoted_view() is not None:
                    _ld, _lv = self.field.dominant_live()
                    rec["live_dominant"] = _ld
                    rec["live_dominant_val"] = round(float(_lv), 3)
            except Exception:
                pass
            if extra:   # J-2662: promotion rows carry the stream row's drive/progress/grounded (trigger=promoted only)
                rec["promotion"] = extra
            _IGNITION_LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(_IGNITION_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def log_deferred(self, dim: str) -> None:
        """J-2667 (restart-gated, observe-only): the orchestrator's ignition callback returned early because a
        cycle was active, so the discharged reservoir bought no thought. Leave a trigger="deferred" row in
        ignition_log.jsonl carrying the reservoir value just discharged. Readers computing fires-per-day or
        defensive share MUST exclude trigger=="deferred". Does not change reset timing. Best-effort."""
        try:
            lf = getattr(self, "_last_fire", None) or {}
            self._log_ignition(dim, lf.get("reservoir_val", 0.0), "deferred", lf.get("contrib", {}))
        except Exception:
            pass

    # -- main loop ---------------------------------------------------------

    def tick(self) -> None:
        """One synchronous recompute + accumulator step. Separated from the loop so it can be
        called directly in tests."""
        now = time.time()
        dt  = max(0.0, now - self._last_tick)
        self._last_tick = now
        self.field = self._compute_field()
        self._tick_dissonance(dt)
        # Dosed Coupling Phase 1 (D-0152, 2026-09-05): PUBLISH the field by name, never read anything.
        try:
            from core import coupling_rides as _coupling
            _coupling.publish_climate(self)
        except Exception:
            pass

    async def start_background(self, state) -> None:
        """The 5s field loop. Shares field + dissonance onto CognitiveState every tick, fires
        ignition when ready, persists periodically. Runs until cancelled."""
        state.climate    = self.field
        state.dissonance = self.dissonance
        logger.info("[climate] field loop started (%.0fs tick, ignition>%.1f, refractory %.0fs)",
                    TICK_SECS, _IGNITION_THRESHOLD, _REFRACTORY_SECS)
        ticks = 0
        while True:
            try:
                await asyncio.sleep(TICK_SECS)
                self.tick()
                # Re-share (dataclasses are replaced, not mutated, in _compute_field).
                state.climate    = self.field
                state.dissonance = self.dissonance
                trigger = self._pending_trigger()
                if trigger is not None:
                    await self._ignite(trigger)
                ticks += 1
                if ticks % 12 == 0:          # ~once a minute
                    self._save()
                if ticks % 60 == 1:          # ~once every 5 min, telemetry
                    dim, val = self.field.dominant()
                    logger.info("[climate] dominant=%s(%.2f) dissonance=%.3f strain=%.2f "
                                "completion=%.2f integration=%.2f",
                                dim, val, self.dissonance.value, self.field.world_model_strain,
                                self.field.completion_tension, self.field.integration_drive)
                    self._log_label_promotion(dim, val)   # D-0447 (E): old-vs-new, one row per climate line
            except asyncio.CancelledError:
                self._save()
                raise
            except Exception as exc:
                logger.error("[climate] tick failed (non-fatal): %s", exc)


# ---------------------------------------------------------------------------
# Module-level accessor (J-0580, Dosed Coupling Phase 0, D-0149)
# ---------------------------------------------------------------------------
# The orchestrator owns the one live ClimateEngine instance (core/orchestrator.py). Callers
# elsewhere in the codebase have no reference to it — stream_drive's ignition drive term
# reached for a `core.climate` module that never existed (F-0807: the read was silently dead,
# always falling back to protoself drive only). `_ACTIVE` is set at engine __init__ below;
# fail-open None before any engine has started in this process (tests, tooling, early import),
# so a caller must treat a None return as "no signal," never as zero.
_ACTIVE: "ClimateEngine | None" = None


def ignition_level() -> float | None:
    """Fail-open accessor for the live engine's ignition_level() (see ClimateEngine.ignition_level).
    None when no ClimateEngine has initialized yet in this process, or on any read error."""
    eng = _ACTIVE
    if eng is None:
        return None
    try:
        return eng.ignition_level()
    except Exception:
        return None
