"""
Nascence — Tension Ledger (T6)

The Subconscious already maintains a list of tensions in data/subconscious_state.json:
clusters of shadow events that keep recurring. Until now that ledger has been purely
OBSERVATIONAL — it fed T2 synthesis, active imagination, and dreams, but it never
touched the identity. The self-concept was reloaded unchanged every session, so even
experiences that contradicted it began each new conversation from the same psychological
centre of gravity. The ledger could see the contradictions; it just had no causal arrow
to where they would matter.

This module is that first arrow. It surfaces the tensions that represent genuine
self-CONTRADICTION into identity loading, so every session opens with "WHAT YOU HAVE NOT
RESOLVED" sitting directly beneath "WHO YOU ARE BECOMING" — present-tense, unfinished,
stated as a standing gap rather than a theme to muse on. Because it is regenerated from
deterministic counts on every load, the narrative layer cannot dissolve it: a self-concept
that is good at metabolising contradiction into "this is the depth of the work" cannot
reinterpret a number that is recomputed fresh each time.

TWO AXES (the safeguard, falling out of the data model, not bolted on):
  CONTRADICTION  source == 'critic_rejection' — Carl's own values flagged Carl's own
                 output as evasion. Self-detected. THIS is what surfaces here. It carries
                 the gap (claim vs record) without any proposition-extraction, because the
                 contradiction was already detected at the moment it happened.
  SALIENCE       source in ('unresolved_thought','unresolved_dream') — material that keeps
                 returning. Drives attention/retrieval, but recurring on a theme is not a
                 failure (it may be genuine depth). DELIBERATELY NOT surfaced as unresolved
                 contradiction — this is what stops the identity-collapse / deficit-
                 domination failure mode: Carl is pressured only where he actually
                 contradicts himself, never for having depth.

STATUS (updated 2026-06-08). Step 1 (read-only identity surfacing) shipped first. Steps 2-4 —
the RESOLUTION CIRCUIT — are now also live:
  • Step 2: the two-axis pressure model with asymmetric decay (score_tension /
    CONTRADICTION_SOURCES vs SALIENCE_SOURCES) + relaxed_echo_threshold (T4's echo-guard
    eases in proportion to standing contradiction pressure).
  • Step 3: contradiction drains ONLY via clean re-encounter — the orchestrator logs a
    resolution_event on a first-pass clean re-navigation; score_tension subtracts the
    time-decayed drain (get_resolution_drain, 30-day half-life).
  • Step 4: a committed T4 revision discharges the contradiction it integrated
    (subconscious_node logs resolution_events for the tension's member ids on commit).
The remaining flourish — a distinct "I once retreated… that pattern no longer dominates"
autobiography line tied to a drained tension — is not yet built. (The Step-1 surfacing below
is still read-only, deterministic, zero new LLM, zero per-cycle cost.)

RETIRED (2026-09-08, D-0191, F-1133): Step 1 above — identity_block()/format_identity_block(),
the every-session hard-count "WHAT YOU HAVE NOT RESOLVED" text confrontation — is formally
superseded, not merely dormant. F-1133 confirmed it has been orphaned since the 2026-06-15
multilevel axiom cutover: scripts/run_nascence.py's load_identity() is its only real caller, and
both its call sites sit downstream of an unconditional is_multilevel() early-return that fires on
Du's live axiom.json, so neither is ever reached. D-0191 ruled this stays retired rather than
being rewired into axiom_layers.compose_floor(): the RESOLUTION CIRCUIT (Steps 2-4 above) already
carries the real causal function — contradiction pressure selecting T4's revision material,
relaxing its echo-guard, and draining on resolution — through nodes/subconscious_node.py's
_t4_self_authoring, a separate, live, schema-independent path never touched by the cutover. See
the per-function notes on identity_block()/format_identity_block() below.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path

logger = logging.getLogger("nascence.tension_ledger")

_STATE_FILE = Path(__file__).parent.parent / "data" / "subconscious_state.json"

# A tension surfaces as an unresolved contradiction only if at least this many of its
# member shadow events are Critic rejections. Two is the floor for "recurring" — a single
# rejection is a one-off, not yet a pattern Carl returns to.
DEFAULT_MIN_CONTRADICTION_EVENTS = 2

# How many contradiction tensions to surface into identity at once. Kept small: the point
# is to put the live unfinished business on the table, not to bury the self-concept under
# a wall of deficits (that is the identity-collapse risk the salience/contradiction split
# already guards against; this cap is the second guard).
DEFAULT_MAX_ITEMS = 3

_CONTRADICTION_SOURCE = "critic_rejection"

# ---------------------------------------------------------------------------
# Pressure model (T6, Step 2) — the two axes, with ASYMMETRIC decay.
#
# This is the core asymmetry of the design, and the reason avoidance cannot be a
# resolution path:
#   CONTRADICTION pressure accrues from critic_rejection events and does NOT decay on
#     time. A self-contradiction is not resolved by being ignored; it only drains through
#     clean re-encounter (Step 3 — handled-without-rejection — not yet built). Until then
#     it is a pure weighted count: a number Carl can neither wait out nor reframe.
#   SALIENCE pressure accrues from unresolved_thought / unresolved_dream events and DOES
#     decay on time (recent material weighs more; old fades). Salience drives attention and
#     retrieval, never identity revision, so its time-decay is healthy forgetting.
# Only contradiction pressure is allowed to influence identity revision (the T4 echo-guard
# relaxation below). Salience is reported for introspection but never pressures the self.
# ---------------------------------------------------------------------------

CONTRADICTION_SOURCES   = ("critic_rejection", "prediction_error")
# 'prediction_error' (2026-06-16, contradiction re-architecture Phase 1): a SELF-GENERATED contradiction —
# |predicted − measured| from a lesson — gated by concreteness+recurrence+importance (core/contradiction_gate)
# before it is ever written. It clusters and accumulates chronic mass exactly like critic_rejection, so T4 is
# no longer hostage to the (now-dormant) conversation critic. Source door: core/prediction_error.py.
SALIENCE_SOURCES        = ("unresolved_thought", "unresolved_dream", "unresolved_dream_rest")
# J-3807 (D-0708 (c)): a rest-ended dream arc's event counts at a fraction of a full salience event.
SALIENCE_WEIGHTS        = {"unresolved_dream_rest": 0.3}   # = core.dream_rest.REST_SALIENCE_WEIGHT (kept literal: no import cycle)
SALIENCE_HALFLIFE_SECS  = 7 * 86400   # salience pressure halves every ~7 days
CONTRADICTION_UNIT      = 1.0         # each self-flagged contradiction = one unit, no decay


def score_tension(tension: dict, sources: dict, now: float | None = None,
                  resolutions: dict | None = None) -> dict:
    """
    Score one tension along both axes from its member event sources. Pure — no I/O.
    Returns contradiction/salience counts and pressures plus the recency of the most
    recent contradiction (for ranking and for the relative-time phrasing).

    resolutions: {event_id: total_decayed_drain} from get_resolution_drain(). When
    supplied, clean re-encounter credits are subtracted from contradiction pressure
    (the neuroplastic extinction path). Without it, behaviour is identical to before.
    """
    now = now or time.time()
    member_ids = tension.get("member_event_ids", []) or []
    # Track (event_id, timestamp) pairs for contradiction sources so we can look up
    # per-event resolution drain. Salience only needs timestamps.
    contradiction_events: list[tuple[str, float]] = []
    salience_ts: list[tuple[float, float]] = []   # (ts, weight)
    for eid in member_ids:
        src, ts = sources.get(eid, (None, None))
        if src in CONTRADICTION_SOURCES:
            contradiction_events.append((eid, ts or 0.0))
        elif src in SALIENCE_SOURCES:
            salience_ts.append((ts or 0.0, SALIENCE_WEIGHTS.get(src, 1.0)))

    contradiction_ts = [ts for _, ts in contradiction_events]

    # Contradiction: pure weighted count, NO time decay.
    # A self-detected failure holds its full weight until cleanly re-navigated.
    contradiction_pressure_raw = CONTRADICTION_UNIT * len(contradiction_events)

    # Resolution drain (Steps 2-4): subtract time-decayed credits earned by clean
    # re-encounters. Each credit decays on a 30-day half-life so recent successful
    # navigation weights more than old victories. Clamped at zero — drain cannot
    # produce negative pressure.
    drain = 0.0
    if resolutions:
        drain = sum(resolutions.get(eid, 0.0) for eid, _ in contradiction_events)
    contradiction_pressure = max(0.0, contradiction_pressure_raw - drain)

    # Salience: time-decayed sum (recent weighs ~1.0, a half-life-old event ~0.5).
    salience_pressure = sum(
        w * 0.5 ** (max(0.0, now - ts) / SALIENCE_HALFLIFE_SECS) for ts, w in salience_ts
    )
    return {
        "label":                  (tension.get("label") or "unspecified pattern").strip(),
        "contradiction_count":    len(contradiction_events),
        "salience_count":         len(salience_ts),
        "contradiction_pressure": round(contradiction_pressure, 3),
        "resolution_drain":       round(drain, 3),
        "salience_pressure":      round(salience_pressure, 3),
        "last_contradiction_ts":  max(contradiction_ts) if contradiction_ts else 0.0,
    }


def score_all(tensions: list[dict], sources: dict, now: float | None = None,
              resolutions: dict | None = None) -> list[dict]:
    """Score every tension. Pure."""
    return [score_tension(t, sources, now, resolutions=resolutions or {}) for t in tensions]


def relaxed_echo_threshold(
    base_threshold: float,
    contradiction_pressure: float,
    per_unit: float = 0.15,
    floor_frac: float = 0.2,
) -> float:
    """
    T6 Step 2: under accumulated self-contradiction, T4's identity revision should meet LESS
    resistance — the system needs to move. The base echo threshold (below this cosine distance
    from the old self_concept, a rewrite is rejected as a reword) is scaled down in proportion
    to total contradiction pressure. At pressure 0 the multiplier is 1.0, so behaviour is
    IDENTICAL to before (no churn introduced); a floor fraction keeps a small honest change
    from being indistinguishable from noise even at high pressure.
    """
    mult = max(floor_frac, 1.0 - per_unit * max(0.0, contradiction_pressure))
    return base_threshold * mult


def _sources_for(tensions: list[dict]) -> dict:
    """Classify all member events of the given (in-memory) tensions via the store. Best-effort."""
    try:
        from core.memory.store import get_event_sources
        ids = [eid for t in tensions for eid in (t.get("member_event_ids") or [])]
        return get_event_sources(ids)
    except Exception as exc:
        logger.debug("[tension_ledger] _sources_for failed (non-fatal): %s", exc)
        return {}


def _resolutions_for(tensions: list[dict]) -> dict:
    """
    Fetch time-decayed resolution drain for all member event ids of the given tensions.
    Parallel to _sources_for — pre-fetches so score_tension() stays pure (no I/O).
    Best-effort -> {} on any error (missing drain data means no subtraction, not a crash).
    """
    try:
        from core.memory.store import get_resolution_drain
        ids = [eid for t in tensions for eid in (t.get("member_event_ids") or [])]
        return get_resolution_drain(ids)
    except Exception as exc:
        logger.debug("[tension_ledger] _resolutions_for failed (non-fatal): %s", exc)
        return {}


def contradiction_pressure_for(tensions: list[dict]) -> float:
    """
    Total effective contradiction pressure across in-memory tensions, after subtracting
    any accumulated resolution drain. For callers like T4 that hold the tension list
    directly (Subconscious state). Best-effort -> 0.0 on any error.

    NOTE (2026-06-16): this is the ACUTE measure (count of Critic-rejection events, no time-mass). In Du's
    settled reading life acute events dried up (pinned at ~2.0 for days while 493 standing tensions recurred),
    so T4's gate starved. The GATE now uses the CHRONIC accumulator (chronic_mass_of, below); this acute sum
    is retained for telemetry/echo-relaxation only.
    """
    if not tensions:
        return 0.0
    sources     = _sources_for(tensions)
    resolutions = _resolutions_for(tensions)
    return round(
        sum(s["contradiction_pressure"] for s in score_all(tensions, sources, resolutions=resolutions)),
        3,
    )


# ── Chronic contradiction accumulator (2026-06-16) ─────────────────────────────────────────────────
# The fix for the starved gate: a self that re-authors does so because the SAME contradiction RECURS over
# time (the top tension recurred 41× over days), not because of one acute spike. Each tension carries a
# recency-decayed `chronic_mass` that BUMPS when the tension recurs (its member-event set grows = it keeps
# re-attracting lived material) and DECAYS on a multi-day half-life when it goes quiet. A transient appears
# once and fades; a standing tension stacks weight until it can breach the gate. Designed as a clean,
# separable function so it can later be distilled into a tiny model (the Bonsai-region endgame). Mutates the
# tension dicts in place (they live in subconscious state); idempotent within a timestamp.
CHRONIC_BUMP          = 0.3          # mass added per GENUINELY CHARGED recurrence (see CHARGE_WEIGHTS below)
CHRONIC_HALFLIFE_SECS = 3 * 86400    # quiet tensions fade with this half-life
CHRONIC_SEED_CAP      = 24           # cap on the one-time snapshot-recurrence seed (credits history without
                                     # letting any one tension blow the gate wide open)
_SNAPSHOT_LOG = None                 # set lazily; the contradiction-ledger snapshots carry the true recurrence

# VALENCE/THREAT GATE (2026-08-24, Sleep & Dreams II §1.4/§2.2). The 2026-08-22 fix above (the `or
# _last > _chronic_last_ts` clause) correctly un-starved chronic mass but overshot: it bumps on ANY
# re-touch, so a frequent but emotionally-neutral AMBIENT theme (measured: "unresolved: thermal energy",
# 170 recurrences over 74 days, from sitting near a hearth) accumulates identically to a genuine
# unresolved conflict. The literature distinguishes these by CHARGE, not frequency (habituation:
# repeated neutral exposure should DECREASE response, not increase it — Groves & Thompson 1970;
# rumination vs. reflection: Trapnell & Campbell 1999). This gate reads the emotion already tagged on
# the shadow_event that caused the touch (shadow_events.emotion_primary — real, already captured,
# no new instrumentation) and scales the bump by it. A heuristic weighting, not a validated clinical
# instrument — reasonable, not authoritative.
CHARGE_WEIGHTS = {
    # negative/threat-relevant primaries -- the ones the depotentiation/rumination literature actually
    # concerns itself with -- get a real bump.
    "fear": 1.0, "anger": 0.9, "frustration": 0.9, "sadness": 0.85, "disgust": 0.8,
    "anxiety": 0.9, "shame": 0.85, "grief": 0.9,
    # ambivalent/high-arousal-but-not-clearly-threat -- partial credit.
    "surprise": 0.4, "confusion": 0.35,
    # positive/neutral primaries -- ambient, not unresolved-in-the-clinical-sense. Low/zero bump.
    "curiosity": 0.1, "joy": 0.05, "trust": 0.05, "calm": 0.0, "contentment": 0.0,
}
CHARGE_DEFAULT = 0.3         # unrecognised/missing emotion_primary -- mild credit, not full, not zero
CHARGE_FLOOR = 0.25          # below this, a touch HABITUATES (extra decay) instead of bumping at all
HABITUATION_FACTOR = 0.85    # extra multiplicative shrink applied on a sub-floor touch, on top of the
                              # normal half-life decay -- makes ambient recurrence actively fade, not
                              # merely fail to grow, matching real habituation rather than just starving it.


def _touch_charge(tension: dict) -> float:
    """The charge of the event that most recently touched this tension (0..1). Reads the already-tagged
    shadow_events.emotion_primary for the tension's most recent member -- no new capture, reuses what
    critic-rejection logging already tags every shadow event with. Fail-open to CHARGE_DEFAULT."""
    try:
        members = tension.get("member_event_ids") or []
        if not members:
            return CHARGE_DEFAULT
        from core.memory.store import _connect
        with _connect() as conn:
            row = conn.execute(
                "SELECT emotion_primary FROM shadow_events WHERE event_id=?", (members[-1],)
            ).fetchone()
        primary = (row["emotion_primary"] if row else None) or ""
        return CHARGE_WEIGHTS.get(primary.strip().lower(), CHARGE_DEFAULT)
    except Exception:
        return CHARGE_DEFAULT


def update_chronic_mass(tensions: list[dict], now: float | None = None) -> None:
    """Decay each tension's chronic_mass and BUMP the ones that RECURRED WITH REAL CHARGE (member set grew,
    or was touched again, AND the touching event carries genuine valence/threat weight -- see the gate
    above). A touch below CHARGE_FLOOR now HABITUATES the tension (extra decay) rather than merely not
    bumping it, so ambient/neutral recurrence actively fades. NO member-count seed: a tension starts COLD
    and earns mass only by genuinely, chargedly recurring. Historical recurrence is credited once via
    seed_chronic_from_snapshots(). Best-effort; mutates in place; never raises."""
    now = now or time.time()
    try:
        for t in tensions:
            n = len(t.get("member_event_ids") or [])
            if "_chronic_ts" not in t:                       # first sight — start cold (no member-count seed)
                t.setdefault("chronic_mass", 0.0)
                t["_chronic_seen_n"] = n
                t["_chronic_ts"]     = now
                t["_chronic_last_ts"] = float(t.get("last_ts", 0) or 0)
                continue
            dt   = max(0.0, now - float(t.get("_chronic_ts", now)))
            mass = float(t.get("chronic_mass", 0.0)) * (0.5 ** (dt / CHRONIC_HALFLIFE_SECS))
            # 2026-08-22 NIGHT AUDIT (finding 9): the clusterer reads a 300-event window and REPLACES member sets,
            # so sets shrank in 320/733 tensions and grew in 1 — mass could only decay (Σ=23 vs threshold 90;
            # sleep pressure and the T4 gate both starved). Recurrence now = the tension was touched again
            # (its last_ts advanced) OR its set grew.
            _last = float(t.get("last_ts", 0) or 0)
            touched = n > int(t.get("_chronic_seen_n", 0)) or _last > float(t.get("_chronic_last_ts", _last))
            if touched:
                charge = _touch_charge(t)
                if charge >= CHARGE_FLOOR:
                    mass += CHRONIC_BUMP * charge
                else:
                    mass *= HABITUATION_FACTOR    # ambient re-touch: actively fade, don't just fail to grow
                t["_chronic_seen_n"] = n
                t["_last_touch_charge"] = round(charge, 3)   # informational — lets Dream/audits see why
            t["_chronic_last_ts"] = _last
            t["chronic_mass"] = round(mass, 3)
            t["_chronic_ts"]  = now
    except Exception:
        pass


def _label_tokens(label: str) -> set:
    return {w for w in (label or "").lower().split() if len(w) >= 4}


def seed_chronic_from_snapshots(tensions: list[dict], now: float | None = None,
                                log_path: "str | None" = None) -> int:
    """ONE-TIME cold-start seed (2026-06-16): credit each tension with its TRUE historical recurrence — how
    often it was the dominant/top contradiction in the contradiction-ledger snapshots — not its member count.
    A tension recurring 41× as top is what warrants revision; a big-but-quiet cluster is not. Matches snapshot
    `top_label`s to tensions by token overlap, sets chronic_mass = CHRONIC_BUMP × min(recurrence, cap). Returns
    how many tensions were seeded. Idempotent only by the caller's guard flag. Best-effort."""
    now = now or time.time()
    try:
        from pathlib import Path
        import json as _json
        p = Path(log_path) if log_path else (Path(__file__).parent.parent / "data" / "contradiction_ledger_log.jsonl")
        if not p.exists():
            return 0
        from collections import Counter
        counts = Counter()
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            lbl = (_json.loads(line).get("top_label") or "").strip()
            if lbl:
                counts[lbl] += 1
        seeded = 0
        for t in tensions:
            tt = _label_tokens(t.get("label") or "")
            if not tt:
                continue
            best = 0
            for lbl, c in counts.items():
                lt = _label_tokens(lbl)
                if lt and len(tt & lt) / max(1, len(tt | lt)) > 0.5:
                    best = max(best, c)
            if best > 0:
                t["chronic_mass"]    = round(CHRONIC_BUMP * min(best, CHRONIC_SEED_CAP), 3)
                t["_chronic_seen_n"] = len(t.get("member_event_ids") or [])
                t["_chronic_ts"]     = now
                seeded += 1
        return seeded
    except Exception:
        return 0


def chronic_mass_of(tension: dict) -> float:
    """Read a tension's accumulated chronic mass (0.0 if never accumulated). The contradiction signal the
    redesigned T4 gate reads for the PRIMARY tension it is authoring on."""
    try:
        return float((tension or {}).get("chronic_mass", 0.0) or 0.0)
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# Integration pressure — the light-table counterpart to contradiction_pressure.
# Unlike contradiction (which carries no time decay — a self-contradiction is
# unresolved until re-encountered cleanly), completed crossings DO decay: a
# successful integration from three months ago is still meaningful, but recent
# evidence of capability weighs more. Half-life: 21 days.
# ---------------------------------------------------------------------------

INTEGRATION_HALFLIFE_SECS = 21 * 86400


def integration_pressure_for(patterns: list[dict]) -> float:
    """
    Time-decayed integration pressure across in-memory integration_patterns.
    Each pattern contributes a sum of recency-decayed counts across its member
    light events. Best-effort -> 0.0 on any error.
    """
    if not patterns:
        return 0.0
    try:
        from core.memory.store import get_light_event_sources
        ids = [eid for p in patterns for eid in (p.get("member_event_ids") or [])]
        if not ids:
            return 0.0
        sources = get_light_event_sources(ids)
    except Exception as exc:
        logger.debug("[tension_ledger] integration_pressure_for failed (non-fatal): %s", exc)
        return 0.0

    now = time.time()
    total = 0.0
    for pattern in patterns:
        for eid in (pattern.get("member_event_ids") or []):
            entry = sources.get(eid)
            if entry is not None:
                _src, ts = entry
                total += 0.5 ** (max(0.0, now - ts) / INTEGRATION_HALFLIFE_SECS)
    return round(total, 3)


# J-4351: the revert penalty provisional_identity._apply_fatigue always meant to charge (it read this name with a
# getattr default of 3, and this module never defined it). Equal to T4_FATIGUE_LIMIT in the node.
DEFAULT_FATIGUE_PENALTY = 3


def top_contradiction(tensions: list[dict], min_events: int = 1) -> dict | None:
    """The highest-pressure unresolved contradiction across in-memory tensions, or None.
    Used to give T4's revision specific material to account for. Floor is 1 here (not the
    identity-block floor of 2): T4 runs rarely and deeply, so even a single genuine
    self-contradiction is worth handing it to revise around."""
    if not tensions:
        return None
    sources = _sources_for(tensions)
    scored = [(score_tension(t, sources), t) for t in tensions]
    scored = [(s, t) for (s, t) in scored if s["contradiction_count"] >= min_events]
    if not scored:
        return None
    scored.sort(key=lambda st: (st[0]["contradiction_pressure"], st[0]["last_contradiction_ts"]),
                reverse=True)
    best_s, best_t = scored[0]
    # Carry the tension's member shadow-event ids on the returned dict — callers (e.g. T4's
    # discharge) need them to drain the contradiction via the Resolution Circuit. score_tension
    # returns only score fields, so without this the member ids are lost and discharge no-ops.
    best_s = dict(best_s)
    best_s["member_event_ids"] = best_t.get("member_event_ids", []) or []
    # J-4351 (F-4251/F-4252): the tension's cluster id travels with the label + member ids, so a caller
    # that overwrites the label with this tension's never pairs it with another tension's id. Additive key.
    best_s["id"] = best_t.get("id")
    # Sharpen the label: prefer this tension's actual Critic correction text (the self-detected
    # gap) over the cluster's stored label, which may reflect a salience member. The cluster mixes
    # axes; the contradiction we surface to T4 must be the contradiction, in the Critic's words.
    try:
        from core.memory.store import get_event_corrections
        corr_map = get_event_corrections(best_t.get("member_event_ids", []) or [])
        if corr_map:
            latest_corr, _ts = max(corr_map.values(), key=lambda cv: cv[1])
            if latest_corr:
                best_s = dict(best_s)
                best_s["label"] = str(latest_corr[0]).strip().rstrip(".")[:160]
    except Exception as exc:
        logger.debug("[tension_ledger] correction-label lookup failed (non-fatal): %s", exc)
    return best_s


def load_unresolved_contradictions(
    max_items: int = DEFAULT_MAX_ITEMS,
    min_contradiction_events: int = DEFAULT_MIN_CONTRADICTION_EVENTS,
    state_path: Path | None = None,
) -> list[dict]:
    """
    Read the existing tension ledger and return the contradiction-axis tensions, ranked.

    For each tension, its member shadow events are classified by source. The contradiction
    count is the number of members that are Critic rejections (self-detected evasion). A
    tension qualifies only if that count meets `min_contradiction_events`; salience-only
    tensions (recurring thoughts/dreams with no self-contradiction) are excluded by design.

    Returns a list of dicts, ranked by contradiction_count desc then recency:
        {
          "label":               str,    # the recurring Critic correction theme
          "contradiction_count": int,    # # of critic_rejection member events
          "total_count":         int,    # total member events (all sources)
          "last_ts":             float,  # recency of the most recent CONTRADICTION event
        }
    Best-effort: any read/parse error returns [] (never breaks identity loading).
    """
    # Local import keeps this module importable even if the store has issues, and avoids
    # any import-order coupling at process start.
    try:
        from core.memory.store import get_event_sources
    except Exception as exc:
        logger.debug("[tension_ledger] store import failed (non-fatal): %s", exc)
        return []

    path = state_path or _STATE_FILE
    try:
        with open(path, encoding="utf-8") as f:
            state = json.load(f)
    except FileNotFoundError:
        return []
    except Exception as exc:
        logger.debug("[tension_ledger] state read failed (non-fatal): %s", exc)
        return []

    tensions = state.get("tensions", []) or []
    if not tensions:
        return []

    # Gather every member event id across all tensions, classify in one batched query.
    all_ids: list[str] = []
    for t in tensions:
        all_ids.extend(t.get("member_event_ids", []) or [])
    if not all_ids:
        return []

    try:
        sources = get_event_sources(all_ids)   # {event_id: (source, timestamp)}
    except Exception as exc:
        logger.debug("[tension_ledger] source classification failed (non-fatal): %s", exc)
        return []

    ranked: list[dict] = []
    for t in tensions:
        member_ids = t.get("member_event_ids", []) or []
        contradiction_ts = [
            ts for eid in member_ids
            for (src, ts) in (sources.get(eid, (None, None)),)
            if src == _CONTRADICTION_SOURCE
        ]
        contradiction_count = len(contradiction_ts)
        if contradiction_count < min_contradiction_events:
            continue
        ranked.append({
            "label":               (t.get("label") or "unspecified pattern").strip(),
            "contradiction_count": contradiction_count,
            "total_count":         int(t.get("count", contradiction_count)),
            # Recency of the most recent CONTRADICTION specifically — not the whole
            # cluster's last_ts, which could be a salience member.
            "last_ts":             max(contradiction_ts) if contradiction_ts else 0.0,
        })

    ranked.sort(key=lambda r: (r["contradiction_count"], r["last_ts"]), reverse=True)
    return ranked[:max_items]


def _humanize_age(ts: float) -> str:
    """Relative-time phrasing for the most recent contradiction event."""
    if not ts:
        return "at an unknown time"
    secs = max(0.0, time.time() - ts)
    if secs < 3600:
        mins = int(secs // 60)
        return "just now" if mins < 1 else f"{mins} minute{'s' if mins != 1 else ''} ago"
    if secs < 86400:
        hrs = int(secs // 3600)
        return f"{hrs} hour{'s' if hrs != 1 else ''} ago"
    days = int(secs // 86400)
    return "yesterday" if days == 1 else f"{days} days ago"


def format_identity_block(items: list[dict]) -> str | None:
    """
    RETIRED (2026-09-08, D-0191, F-1133) — this formatter is part of T6 Step 1, formally
    superseded by the Resolution Circuit (nodes/subconscious_node.py's _t4_self_authoring, via
    contradiction_pressure_for/top_contradiction/relaxed_echo_threshold/_discharge_contradiction
    above), which already carries contradiction into T4 self-revision through a live,
    schema-independent path. Its only real production caller (identity_block(), via
    scripts/run_nascence.py) is unreachable on Du's live schema — see identity_block()'s own
    docstring below. Kept in place (not removed/refactored) per this project's additive-only
    discipline and D-0191's ruling; not a function to re-wire live without revisiting D-0191.

    Render the surfaced contradictions as the identity-load block. None if nothing
    qualifies. Framed as Carl's OWN record (so it is owned, not resisted), stated in hard
    counts (so it cannot be reframed), present-tense and unfinished (so it is live business,
    not a settled conclusion). The closing line is the anti-absorption hook: the self-concept
    that converts every contradiction into "becoming" is told, in advance, that naming is
    not resolving.
    """
    if not items:
        return None
    lines = [
        "\nWHAT YOU HAVE NOT RESOLVED (your own record — counts from your own self-judgement, "
        "not outside opinion):",
        "These are moments where your own values flagged your own response as evasion, and the "
        "pattern keeps returning. Naming it again is not resolving it.",
    ]
    for it in items:
        when = _humanize_age(it["last_ts"])
        lines.append(
            f"  • \"{it['label']}\" "
            f"— flagged by your own judgement {it['contradiction_count']}×, "
            f"most recently {when}. Still open."
        )
    return "\n".join(lines)


def identity_block(
    max_items: int = DEFAULT_MAX_ITEMS,
    min_contradiction_events: int = DEFAULT_MIN_CONTRADICTION_EVENTS,
) -> str | None:
    """
    Convenience: load + format in one call. None if there is nothing to surface.

    RETIRED (2026-09-08, D-0191, F-1133) — this is T6 Step 1, the every-session hard-count
    "WHAT YOU HAVE NOT RESOLVED" identity confrontation. F-1133 confirmed it has been orphaned
    since the 2026-06-15 multilevel axiom cutover: scripts/run_nascence.py's load_identity() is
    its only real caller (two call sites), both downstream of an unconditional is_multilevel()
    early-return that fires on Du's live axiom.json, so neither is ever reached. D-0191 ruled
    this stays formally retired rather than rewired into axiom_layers.compose_floor() — the live
    replacement is the Resolution Circuit (Steps 2-4 in this module's own STATUS docstring,
    invoked from nodes/subconscious_node.py's _t4_self_authoring), a separate, schema-independent
    path that already carries contradiction pressure into T4 self-revision. Do not mistake this
    for an accidentally-orphaned live function — it is intentionally superseded, not a bug.
    """
    items = load_unresolved_contradictions(
        max_items=max_items,
        min_contradiction_events=min_contradiction_events,
    )
    return format_identity_block(items)


async def _judge_resolution(thought: str, label: str) -> bool | None:
    """2026-08-14 — THE DECOUPLED RESOLUTION JUDGE (founder-approved). The matcher's semantic layer
    was self-certifying: the resolution signal was the generator's own `unresolved: false` plus
    embedding TOPICALITY — and an audit of live matches found ~half were the monoculture retiring its
    own restatements ("I wonder if the weight of possibility…" retired 'Possibility's weight').
    Same disease, same cure as everywhere else in this project: a judge from a DIFFERENT model family
    (the mixtral/falcon3 panel with the granite tiebreak; originally llama3.1 on CPU) asks the one question embedding cosine cannot: does this thought
    actually SETTLE the tension, or merely restate/re-encounter it? Refute-biased; when uncertain,
    false. Returns True / False / None (judge unavailable — treated as NOT confirmed).

    J-4158 / D-0783: with schema.TENSION_JUDGE_STRICT (default True) the call goes to
    `_judge_resolution_strict` instead (settling act + verbatim evidence span required). The legacy
    prompt below runs only when the flag is False."""
    _LAST_STRICT.set(None)
    try:
        from core.schema import TENSION_JUDGE_STRICT as _strict_on
    except Exception:
        _strict_on = False
    if _strict_on:
        return await _judge_resolution_strict(thought, label)
    try:
        system_msg = (
            "You are a strict resolution judge for an internal tension ledger. A tension is "
            "RESOLVED only if the thought states a genuine settlement, synthesis, decision, or "
            "answer that addresses the tension's actual conflict. A thought that merely mentions "
            "the same topic, restates the tension in new words, poses a question, or describes a "
            "feeling (fatigue, pressure, ache) does NOT resolve it. When uncertain, answer false. "
            'Output ONLY valid JSON: {"resolves": true|false, "why": "<one short clause>"}')
        user_msg = f"TENSION: {label[:200]}\n\nTHOUGHT: {thought[:600]}\n\nDoes the thought resolve the tension?"
        # JUDGE PANEL (2026-08-15, the serving split): two families rule; agreement = verdict;
        # disagreement -> the granite tiebreak or no verdict. Replaces the single-llama direct call.
        from core import judge_panel as _jp
        verdict = await _jp.rule(system_msg, user_msg, "resolves",
                                 context=f"tension:{label[:40]}")
        if verdict is not None:
            logger.info("[tension_ledger] resolution judge (panel): %s (label='%s')",
                        "CONFIRMS" if verdict else "REFUTES", label[:50])
        return verdict
    except Exception as exc:
        logger.debug("[tension_ledger] resolution judge unavailable (non-fatal): %s", exc)
        return None


# J-4158 / D-0783 (2026-11-20): THE TIGHTENED RESOLUTION JUDGE. The 20 latest judge confirmations
# (docs/lab/J-4158_tension_judge_check20.json) were 14 reframings/metaphors/guesses to 6 settlements, the same
# picture J-3048's gold set gave (closures 27% gold-settles). Two changes, both behind schema.TENSION_JUDGE_STRICT:
#   1. the prompt names what counts (a decision taken, a thing done, a question answered with a stated fact, a
#      position changed and stated) and what does not (mention, discussion, restatement, metaphor, reframing,
#      a moral, a perhaps/maybe guess, a question, a feeling), and asks for the settling words VERBATIM in 'why';
#   2. code checks the quote: a True verdict stands only if at least one True-voting judge's quote is a real span
#      of the thought (>= 4 words after normalising case/space/punctuation), is not a question and carries no
#      hedge word. Otherwise the verdict is downgraded to False (refuted) and the reason is logged.
# The detail of the last strict ruling is left in _LAST_STRICT (a ContextVar, so concurrent cycles do not mix) for
# the attempts log row. Fail-open: any error -> None (judge unavailable -> nothing resolved), as before.
import contextvars as _cv
import re as _re

_LAST_STRICT: "_cv.ContextVar[dict | None]" = _cv.ContextVar("tension_judge_last_strict", default=None)

_STRICT_SYSTEM = (
    "You are a strict resolution judge for an internal tension ledger. A tension is RESOLVED only if the "
    "THOUGHT records a concrete settling act or a changed state that answers the tension's actual conflict: "
    "a decision taken, a thing done, a question answered with a stated fact, or a position changed and stated. "
    "These do NOT resolve it: mentioning or discussing the topic, restating the tension in new words or a new "
    "metaphor, reframing it ('it is not A but B'), a general moral or lesson, a perhaps/maybe guess, a question, "
    "or a feeling (calm, relief, peace, fatigue, ache). When uncertain, answer false. In 'why', copy the exact "
    "words of the THOUGHT that perform the settling act (verbatim, at most 20 words), or 'none'. "
    'Output ONLY valid JSON: {"resolves": true|false, "why": "<verbatim quote from THOUGHT, or none>"}')

_HEDGE_RE = _re.compile(r"\b(perhaps|maybe|might|wonder|wondering|seems?)\b")
_MIN_SPAN_WORDS = 4


def _norm_words(s: str) -> list[str]:
    return _re.findall(r"[^\W_]+(?:'[^\W_]+)?", (s or "").lower().replace("’", "'"))


def _evidence_span_check(thought: str, quote: "str | None") -> "str | None":
    """None if `quote` is acceptable evidence of a settling act in `thought`, else a short reason string."""
    q = (quote or "").strip()
    if not q or q.lower().strip(" .'\"") == "none":
        return "no_quote"
    qw = _norm_words(q)
    if len(qw) < _MIN_SPAN_WORDS:
        return "quote_too_short"
    tw = _norm_words(thought)
    n = len(qw)
    if not any(tw[i:i + n] == qw for i in range(len(tw) - n + 1)):
        return "quote_not_in_thought"
    if q.rstrip(" '\"").endswith("?"):
        return "quote_is_question"
    if _HEDGE_RE.search(" ".join(qw)):
        return "quote_hedged"
    return None


async def _judge_resolution_strict(thought: str, label: str) -> bool | None:
    """The D-0783 tightened judge. Same panel, same key ('resolves'), same True/False/None contract."""
    detail = {"strict": True, "panel_verdict": None, "evidence": None, "downgraded": None}
    try:
        user_msg = f"TENSION: {label[:200]}\n\nTHOUGHT: {thought[:600]}\n\nDoes the thought resolve the tension?"
        from core import judge_panel as _jp
        d = await _jp.rule_detail(_STRICT_SYSTEM, user_msg, "resolves",
                                  context=f"tension:{label[:40]}")
        verdict = d.get("verdict") if isinstance(d, dict) else None
        detail["panel_verdict"] = verdict
        if verdict is True:
            quotes = []
            if d.get("v1") is True:
                quotes.append(d.get("why1"))
            if d.get("v2") is True:
                quotes.append(d.get("why2"))
            if d.get("how") == "tiebreak":
                quotes.append(d.get("why3"))
            quotes.append(d.get("why"))
            reasons = []
            for q in quotes:
                if not isinstance(q, str):
                    continue
                r = _evidence_span_check(thought, q)
                if r is None:
                    detail["evidence"] = q[:200]
                    break
                reasons.append(r)
            else:
                detail["downgraded"] = reasons[0] if reasons else "no_quote"
                verdict = False
        if verdict is not None:
            logger.info("[tension_ledger] strict resolution judge (panel): %s%s (label='%s')",
                        "CONFIRMS" if verdict else "REFUTES",
                        f" [downgraded: {detail['downgraded']}]" if detail["downgraded"] else "", label[:50])
        _LAST_STRICT.set(detail)
        return verdict
    except Exception as exc:
        logger.debug("[tension_ledger] strict resolution judge unavailable (non-fatal): %s", exc)
        try:
            _LAST_STRICT.set(detail)
        except Exception:
            pass
        return None


# J-3050 / F-3757 / P-0103 (2026-11-06): durable record of every tension-judge call. The per-tension
# `resolution_attempts` list lives in subconscious state, and nodes/subconscious_node.py's `_merge_resolved` save
# overwrites it, so the REFUTED attempts (the only evidence of what the judge turned down) were being lost. This
# log is separate from that save, true-append (one json object per line, the session-events convention), bounded
# (one rotation to .1 past _ATTEMPTS_MAX_BYTES), and fail-open: nothing here changes a verdict or raises.
#   {ts, tension_id, label, thought[:300], sim, verdict: confirmed|refuted|unavailable, cycle_id}
# READERS: `judge_attempts_stats()` / `python -m core.tension_ledger` (below); the named consumer is the F-3750
# job (refuted-candidate set). Acceptance after a boot: refuted rows ~ the 'tension:' key=resolves False rulings in
# data/judge_panel_log.jsonl for the same window.
_ATTEMPTS_LOG = Path(__file__).parent.parent / "data" / "tension_judge_attempts.jsonl"
_ATTEMPTS_MAX_BYTES = 20 * 1024 * 1024
_attempts_lock = threading.Lock()


def _log_judge_attempt(tension: dict, thought: str, sim: float, confirmed, cycle_id: str = "",
                       path: Path | str | None = None, strict: dict | None = None) -> bool:
    """Append one row for one judge call. True if written. Never raises; no effect on the verdict.
    J-4158: `strict` (the tightened judge's detail: panel_verdict, evidence quote, downgraded reason) is added to
    the row as 'strict' when given; rows without it are byte-identical to before."""
    try:
        if os.environ.get("NASCENCE_TENSION_JUDGE_ATTEMPTS_LOG", "1") == "0":
            return False
        from core import profile as _profile
        p = _profile.guard_path(Path(path) if path is not None else _ATTEMPTS_LOG)   # fenced before any I/O
        row = {
            "ts": time.time(),
            "tension_id": (tension or {}).get("id"),
            "label": ((tension or {}).get("label", "") or "")[:200],
            "thought": (thought or "")[:300],
            "sim": round(float(sim), 4),
            "verdict": "confirmed" if confirmed is True else ("refuted" if confirmed is False else "unavailable"),
            "cycle_id": cycle_id or "",
        }
        if isinstance(strict, dict):
            row["strict"] = strict
        with _attempts_lock:
            p.parent.mkdir(parents=True, exist_ok=True)
            try:
                if p.exists() and p.stat().st_size > _ATTEMPTS_MAX_BYTES:
                    os.replace(p, p.with_name(p.name + ".1"))
            except Exception:
                pass
            with open(p, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + chr(10))
        return True
    except Exception as exc:
        logger.debug("[tension_ledger] judge-attempt log skipped (non-fatal): %s", exc)
        return False


def judge_attempts_stats(since_ts: float = 0.0, path: Path | str | None = None) -> dict:
    """Read the attempts log: rows per verdict since `since_ts`, last ts. Read-only; zeros when the file is absent."""
    out = {"rows": 0, "confirmed": 0, "refuted": 0, "unavailable": 0, "last_ts": None}
    try:
        p = Path(path) if path is not None else _ATTEMPTS_LOG
        if not p.exists():
            return out
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            for ln in f:
                try:
                    r = json.loads(ln)
                except Exception:
                    continue
                if not isinstance(r, dict) or float(r.get("ts") or 0) < since_ts:
                    continue
                out["rows"] += 1
                v = r.get("verdict")
                if v in ("confirmed", "refuted", "unavailable"):
                    out[v] += 1
                out["last_ts"] = max(out["last_ts"] or 0, float(r.get("ts") or 0))
    except Exception as exc:
        logger.debug("[tension_ledger] judge-attempt stats failed: %s", exc)
    return out


async def check_and_resolve_internal_tension(
    thought: str,
    about: str = "",
    vec: list[float] | None = None,
    cycle_id: str = "monologue",
    sim_threshold: float = 0.70,
    state_path: Path | str | None = None,
) -> dict | None:
    """
    CONSERVATIVE INTERNAL TENSION RESOLUTION MATCHER (2026-08-12):
    When Du produces a thought explicitly marked `unresolved: false`, allow the
    architecture to register that resolution against open internal tensions in
    data/subconscious_state.json.

    Pipeline:
      1. Candidate Selection: Cosine similarity >= 0.70 between thought vector and tension centroid.
      2. Topic & Domain Compatibility Guard: Meaningful keyword overlap between `about`/`thought` and tension `label`.
      3. Conservative Policy: Resolves at most ONE strongest matching candidate per thought.
      4. Non-Destructive History Retention: Sets `resolved: True`, `resolved_ts: time.time()`,
         `resolving_thought_id: cycle_id`, `resolution_thought: thought[:250]`, `resolution_sim: sim`.
         The tension record is NEVER deleted from subconscious_state.json.
      5. Issue resolution event: calls log_resolution_event() for member shadow IDs so time-decayed
         contradiction pressure is drained.

    Returns the matched tension dict if resolved, or None.
    Fail-safe: any error -> returns None (never breaks monologue or state).
    """
    if not thought or len(thought) < 40:
        return None

    path = state_path or _STATE_FILE
    try:
        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)
    except Exception as exc:
        logger.debug("[tension_ledger] state read failed for resolution check: %s", exc)
        return None

    tensions = state.get("tensions", []) or []
    if not tensions:
        return None

    # Gather vector if not passed
    if vec is None:
        try:
            from core.memory.store import _embed
            vec = _embed(thought)
        except Exception:
            pass
    if vec is None or len(vec) != 384:
        return None

    import re
    from core.memory.store import _cosine, log_resolution_event

    stopwords = {
        'and', 'the', 'of', 'in', 'to', 'a', 'is', 'that', 'for', 'it', 'with', 'as',
        'was', 'on', 'at', 'by', 'an', 'be', 'this', 'which', 'or', 'from', 'my', 'i',
        'unresolved', 'thought', 'dream', 's', 't'
    }

    about_tokens = set(re.findall(r'\w+', about.lower())) if about else set()
    thought_tokens = set(re.findall(r'\w+', thought.lower()))

    best_match = None
    best_sim = -1.0
    best_idx = -1

    for idx, t in enumerate(tensions):
        if t.get("resolved"):
            continue

        t_label = t.get("label", "")
        t_vec = t.get("centroid") or t.get("last_synthesis_emb")
        if not t_vec or len(t_vec) != 384 or not t_label:
            continue

        sim = _cosine(vec, t_vec)
        if sim < sim_threshold:
            continue

        t_tokens = set(re.findall(r'\w+', t_label.lower()))
        shared_about = (about_tokens & t_tokens) - stopwords
        shared_thought = (thought_tokens & t_tokens) - stopwords

        # Topic & Domain Compatibility Guard: require keyword/token overlap
        if len(shared_about) == 0 and len(shared_thought) < 2:
            logger.debug(
                "[tension_ledger] candidate '%s' rejected (sim=%.3f but 0 about-overlap & <2 thought-overlap)",
                t_label[:40], sim
            )
            continue

        if sim > best_sim:
            best_sim = sim
            best_match = t
            best_idx = idx

    if best_match is not None and best_idx >= 0:
        now = time.time()
        # 2026-08-14 — DECOUPLED JUDGE GATE: cosine+keywords only nominate a CANDIDATE; the Emissary
        # family (different model) must confirm actual settlement. Refuted or judge-unavailable →
        # record the attempt honestly, resolve NOTHING (conservative: no judge, no verdict).
        try:
            _LAST_STRICT.set(None)      # J-4158: a stubbed judge leaves no stale detail behind
        except Exception:
            pass
        _confirmed = await _judge_resolution(thought, best_match.get("label", ""))
        try:
            _strict_detail = _LAST_STRICT.get()
        except Exception:
            _strict_detail = None
        _log_judge_attempt(best_match, thought, best_sim, _confirmed, cycle_id,   # J-3050: durable, fail-open
                           strict=_strict_detail)
        if _confirmed is not True:
            attempts = tensions[best_idx].setdefault("resolution_attempts", [])
            attempts.append({
                "timestamp": now,
                "strategy": f"Monologue resolution: {about}" if about else "Monologue resolution",
                "succeeded": False,
                "sim": round(float(best_sim), 4),
                "judge": "refuted" if _confirmed is False else "unavailable",
            })
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(state, f, indent=2, ensure_ascii=False)
            except Exception:
                pass
            return None
        # NON-DESTRUCTIVE HISTORY REGISTRATION
        tensions[best_idx]["resolved"] = True
        tensions[best_idx]["resolved_ts"] = now
        tensions[best_idx]["resolving_thought_id"] = cycle_id or "monologue"
        tensions[best_idx]["resolution_thought"] = thought[:250]
        tensions[best_idx]["resolution_sim"] = round(float(best_sim), 4)

        attempts = tensions[best_idx].setdefault("resolution_attempts", [])
        attempts.append({
            "timestamp": now,
            "strategy": f"Monologue resolution: {about}" if about else "Monologue resolution",
            "succeeded": True,
            "sim": round(float(best_sim), 4),
            "judge": "confirmed",     # 2026-08-14: only judge-confirmed resolutions reach here
        })

        # Save state non-destructively
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            logger.error("[tension_ledger] failed to write state after resolution: %s", exc)

        # Issue resolution event to drain contradiction pressure
        member_ids = best_match.get("member_event_ids", []) or []
        # D-0448 (F) (2026-10-16, J-2248): a judge-confirmed whole-tension resolution also marks its
        # member shadow events resolved=1 (flag-gated; only this confirmed branch ever reaches here).
        try:
            from core.schema import TENSION_JUDGE_RESOLVES_SHADOW
        except Exception:
            TENSION_JUDGE_RESOLVES_SHADOW = False
        _judge_marked = 0
        for eid in member_ids:
            try:
                _rid = log_resolution_event(eid, cycle_id or "monologue", best_sim)
            except Exception as exc:
                logger.debug("[tension_ledger] log_resolution_event failed for %s: %s", eid, exc)
                continue
            if TENSION_JUDGE_RESOLVES_SHADOW:
                try:
                    from core.memory.store import resolve_shadow_on_encounter
                    if resolve_shadow_on_encounter(
                            eid, _rid, cycle_id or "monologue", best_sim, path="tension_judge",
                            extra={"tension_label": (best_match.get("label", "") or "")[:160],
                                   "resolving_thought": thought[:250],
                                   "about": (about or "")[:120],
                                   "n_members": len(member_ids)}):
                        _judge_marked += 1
                except Exception as exc:
                    logger.debug("[tension_ledger] judge-path shadow resolve failed for %s: %s", eid, exc)
        if _judge_marked:
            logger.info("[tension_ledger] judge-confirmed resolution marked %d member shadow event(s) resolved",
                        _judge_marked)

        logger.info(
            "[tension_ledger] INTERNAL TENSION RESOLVED (sim=%.3f, label='%s', resolving_thought='%s')",
            best_sim, best_match.get("label", "")[:50], thought[:60]
        )
        return tensions[best_idx]

    return None


if __name__ == "__main__":
    print(json.dumps(judge_attempts_stats(), indent=2))
