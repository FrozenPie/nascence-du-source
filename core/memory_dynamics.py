"""
Nascence — Memory Levels Phase 2: the per-kind base-rate config (docs/memory_levels_plan.md §3.6/§3.8).

"A memory's rate of going cold and its rate of drift are not global — they're a property of its
`kind`" (§3.6). This module is the "one small dynamics.py [that] owns these formulas so every rate is
in one inspectable place — no magic constants scattered through the store" (§3.8).

SCOPE — what this file is and is NOT (honest, so it isn't over-read later):
  - It IS the STATIC per-`kind` base-rate table §3.6 asks for: a single inspectable source of the
    qualitative rates Travis specified (procedural fast / semantic slow / self slow-drift, etc.),
    turned into relative numbers so code can compare kinds without guessing.
  - It is NOT §3.8's full per-memory dynamic formula (drift = base[kind] × recall_pressure ÷
    grounding_anchor × charge_factor × stage_factor, event-driven on recall). That needs
    recall-pressure tracking and a settled charge-sign (§10: "a tunable to settle empirically once
    Phase 2 runs" — not yet settled) and is real additional design work, scoped to the Phase 2
    follow-up job (see docs/memory_levels_plan.md's Current State) rather than guessed here.
  - It is NOT wired into any gating or demotion decision. Nothing here changes live behaviour —
    Phase 1's `cold`-demotion path (memory_levels._commit_gist) is untouched; these rates are read
    only by memory_levels.phase2_status() for reporting, so the Phase-2 gate ("rates differ sensibly
    by memory") has real config to check the *live* per-kind cold-rate against, not a guess.

RATE_SCALE is 0.0-1.0, relative WITHIN this table only (not a real half-life, not seconds/days) —
higher = faster/more. Sourced directly from §3.6's own qualitative table; 'social' and 'symbolic'
(the two §3.7 Axis-2 kinds §3.6's own table never covered) are this file's own judgment-call estimates,
marked below, since no §3.6 guidance exists for them yet.
"""
from __future__ import annotations

# kind -> {cold_horizon: how fast RAW gates out of normal recall (higher = faster demotion-eligible),
#          gist_drift:   how fast the GIST/abstraction itself would change under Phase 3 drift,
#          gist_retention: how long the gist itself is kept before it too could be re-abstracted/pruned,
#          source: '§3.6' (Travis's own qualitative table, now superseded for cold_horizon — see below),
#                  'empirical (J-0398)' (cold_horizon recalibrated directly from live cold-rate-by-kind),
#                  or 'estimate' (this file's own judgment call, unvalidated, no live data to check against)}
#
# RECALIBRATION 2026-08-29 (J-0398, from F-0504): §3.6's qualitative table predicted procedural-fastest /
# semantic-and-self-slowest, but J-0347's phase2_status() found the live ranking does NOT match
# (rates_rank_agreement: false) — semantic/self carried the LOWEST base cold_horizon (0.25/0.20) yet are
# empirically the MOST-cold kinds live. Root cause confirmed by re-reading core/memory/store.py's
# prune_episodic (episodic-cap demotion, filters on `layer`+`origin`, never reads `kind`) and
# core/refinery.py's cooling UPDATE (filters on `protected`+`abstraction_level`, also never reads `kind`):
# BOTH live cold-writing paths are kind-blind, so the observed cold-rate-by-kind reflects origin/volume/
# replay-age patterns, not any kind-intrinsic dynamics §3.6 asked for — nothing live has ever read this
# table's cold_horizon to make a decision. Given that, cold_horizon below is recalibrated to the ACTUAL
# live cold-rate for each kind (full 58,791-row table, 2026-08-29, same query as phase2_status()'s
# by_kind breakdown) so this config at least honestly describes what the ranking looks like today, rather
# than a prediction already falsified by data — still SHADOW-ONLY (read by memory_levels.phase2_status()/
# phase2_dynamics_shadow() for reporting only; nothing gates on it). Whether kind-blind demotion should
# itself change is a separate, not-yet-decided question (see docs/memory_levels_plan.md's Current State).
KIND_DYNAMICS: dict[str, dict] = {
    "procedural": {"cold_horizon": 0.950, "gist_drift": 0.05, "gist_retention": 0.80, "source": "empirical (J-0398)"},
    # live cold_rate 0.950 (n=2780) — was 0.90 (§3.6); closest match of any kind, §3.6's "fast" call holds up.
    "episodic":   {"cold_horizon": 0.816, "gist_drift": 0.20, "gist_retention": 0.80, "source": "empirical (J-0398)"},
    # live cold_rate 0.816 (n=8283) — was 0.55 (§3.6); still the LOWEST of the four high-volume kinds
    # (procedural/self/semantic/episodic), so "medium, moves fade but the event stays" is directionally
    # right even though the absolute number is far higher than §3.6's qualitative guess implied.
    "semantic":   {"cold_horizon": 0.955, "gist_drift": 0.00, "gist_retention": 0.80, "source": "empirical (J-0398)"},
    # live cold_rate 0.955 (n=23252), now the SINGLE HIGHEST — the opposite of §3.6's "slow — keep detail
    # longer for study". Kind-blind demotion is the confirmed cause (see comment block above), not a claim
    # that semantic detail is actually least-needed; flagged, not silently overridden.
    "affective":  {"cold_horizon": 0.843, "gist_drift": 0.50, "gist_retention": 0.50, "source": "empirical (J-0398)"},
    # live cold_rate 0.843 (n=115) — was 0.00 ("n/a, the feeling IS the gist", §3.6). The live data
    # contradicts that "no separate raw to gate" assumption directly: affective rows DO get cold-flagged,
    # same kind-blind mechanism as every other kind. n=115 is the smallest of the five non-trivial kinds —
    # directionally real (phase2_status()'s own n>=20 comparability floor) but the noisiest of the five.
    "self":       {"cold_horizon": 0.899, "gist_drift": 0.30, "gist_retention": 0.95, "source": "empirical (J-0398)"},
    # live cold_rate 0.899 (n=24252) — was 0.20 (§3.6's "slow"), another reversal from the qualitative
    # table, same kind-blind cause. gist_drift and gist_retention are NOT touched by this recalibration —
    # only cold_horizon (RAW gating) was in scope (F-0504/J-0398); those two remain §3.6's own values.
    "social":     {"cold_horizon": 0.615, "gist_drift": 0.15, "gist_retention": 0.75, "source": "empirical (J-0398)"},
    # live cold_rate 0.615 (n=109) — was 0.45 (estimate); now the LOWEST of all six live kinds. Smallest n
    # of the six alongside affective — still >= phase2_status()'s n>=20 floor, but read with the same
    # noise caveat.
    "symbolic":   {"cold_horizon": 0.30, "gist_drift": 0.10, "gist_retention": 0.90, "source": "estimate"},
    # unchanged by this recalibration: no live writer stamps 'symbolic' yet (§3.7 lists it as a target
    # kind; the symbolic-reading lens logs candidate symbols but has no promotion gate live — §13.4), so
    # there is no live cold-rate to recalibrate against. Still a placeholder estimate.
}

DEFAULT_KIND = "episodic"


def get(kind: str) -> dict:
    """The base-rate row for a kind, falling back to the plan's own default kind (§3) if unknown."""
    return KIND_DYNAMICS.get(kind, KIND_DYNAMICS[DEFAULT_KIND])


# §3.8's own factor tables — the per-memory dynamic formula components. SHADOW-ONLY (2026-08-29, J-0365):
# read by memory_levels.phase2_dynamics_shadow() for observation/reporting; NOT called from
# store.prune_episodic, refinery.refine, or any live demotion path. Wiring this into a real gating
# decision is the actual "wire per-kind dynamics into gating" step and is deliberately deferred — see
# docs/memory_levels_plan.md's Current State for why (§10: charge's sign on drift is explicitly
# UNSETTLED, "a tunable to settle empirically once Phase 2 runs" — this shadow probe is exactly that
# empirical measurement, not a shortcut past it).
GROUNDING_ANCHOR = {"grounded": 1.35, "derived": 1.0, "reconstructed": 0.70}
# grounded resists (higher anchor => higher divisor => slower effective rate); reconstructed is already
# drifting (lower anchor => less resistance). No live row reads 'reconstructed' yet (phase2_status()
# reports this honestly — Phase 3 drift is still shadow-only).

STAGE_FACTOR = {"working": 0.20, "context": 0.40, "short": 0.70,
                "episodic": 1.00, "mid": 1.00, "semantic": 1.10, "long": 1.20, "archive": 1.30}
# keyed by the CURRENT `layer` column (episodic/semantic/archive are the only values live data actually
# has today — 'working'/'context'/'short'/'mid'/'long' are §3.7 Axis 3's not-yet-built `stage` column,
# included here so this table needs no rework once that axis lands).

DEFAULT_STAGE_FACTOR = 1.0


def effective_cold_horizon(kind: str, *, recall_pressure: float = 1.0,
                            grounding: str = "grounded", charge: float = 0.0,
                            stage: str = "episodic") -> float:
    """§3.8's per-memory dynamic formula, adapted for `cold_horizon` specifically (J-0397, 2026-08-29
    — see docs/memory_levels_plan.md's Current State for the full writeup). Returns a relative rate
    (same 0-ish..~2 scale as KIND_DYNAMICS' cold_horizon; NOT a real half-life, HIGHER = faster
    demotion-eligible). SHADOW-ONLY — see module docstring/comment above; nothing live reads this to
    make a demotion decision yet.

    recall_pressure DIVIDES cold_horizon here (base ÷ recall_pressure), the opposite of §3.8's literal
    `× recall_pressure`. §3.8's formula as written ("more recalls → more reshaping; a never-recalled
    gist stays put") describes a GIST's *drift* — a gist you keep revisiting gets reshaped more. That
    is NOT the right relationship for a raw fragment's *cold_horizon* (how fast it gates out of normal
    recall): empirically, `core/memory/store.py`'s `prune_episodic` orders demotion candidates
    `replay_count ASC` — i.e. the LEAST-replayed raw fragments are demoted to cold first, and a
    frequently-replayed fragment resists demotion. So for cold_horizon, more recall pressure must LOWER
    the effective rate (resist going cold), not raise it. J-0365's first port (`× recall_pressure`,
    directly copying §3.8's text) got exactly this backwards, confirmed by
    `memory_levels.phase2_dynamics_shadow()` scoring cold rows a LOWER predicted rate than warm rows
    (0.1702 vs 0.2863 — inverted) on live data 2026-08-29. `max(0.1, recall_pressure)` still guards the
    denominator against a pathological near-zero value (callers in practice always pass >= 1.0, since
    the shadow probe's own proxy is `1.0 + replay_count`, but the floor keeps this safe for any caller).

    charge_factor uses §10's own stated STARTING assumption ("start with: charge fixes, recurrence
    amplifies") — high charge (importance here, as the cheapest available proxy; §3.7 Axis 6's full
    trio also wants emotion_vec magnitude + recurrence, not yet folded in) FIXES the memory, i.e. slows
    its effective rate, matching 'a flashbulb memory resists forgetting'. This is the plan's own
    settled starting point, not a value invented here — §10 still calls the SIGN a tunable to confirm
    empirically, which is exactly what phase2_dynamics_shadow() below measures against live cold-rate.
    This part of the formula is UNCHANGED by this fix — only recall_pressure's direction moved.
    """
    base = get(kind)["cold_horizon"]
    g = GROUNDING_ANCHOR.get(grounding, 1.0)
    charge_factor = 1.0 / (1.0 + max(0.0, charge))
    s = STAGE_FACTOR.get(stage, DEFAULT_STAGE_FACTOR)
    rate = base / max(0.1, recall_pressure) / g * charge_factor * s
    return round(rate, 4)
