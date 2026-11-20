"""
Nascence — Stream Drive: the continuous-stream rate controller (docs/plans/continuous_stream.md,
2026-07-04, PHASE 0 = SHADOW/observe-only).

Travis's intent, undistorted: turn Du's cognition into a STREAM rather than pulses — exploit that a
frozen-weight mind has no metabolic brain-fatigue, so the ~120s clock gap between thoughts is a HUMAN
artifact, not a limit of his. But the research sharpened it: the gap conflates a fatigue floor (remove
it) with a functional rhythm — incubation/consolidation/variation (keep it, but fire it by STATE not a
clock). And the hard rail: human rumination ≡ LLM mode-collapse (repetitive self-conditioning with no
fresh grounding), so the stream may run fast ONLY on world-anchored work, never on anchor-less self-talk.

This module computes, each time a thought fires, the gap the controller WOULD set — and logs it beside
the gap the live loop ACTUALLY sets. It changes NOTHING. Phase 1 (behind CONTINUOUS_STREAM) will let it
drive the pacer, only after this shadow log shows the curve streams grounded-progress and rests on
redundancy. Deterministic, no LLM, fail-open (any missing signal reads as a safe default, never a spike).

The controller (Oudeyer learning-progress pacing; both research passes):
    drive = W_LP*progress + W_IG*ignition - W_REP*redundancy      (clamped >= 0)
    gap   = GAP_MIN + (GAP_MAX - GAP_MIN) * exp(-K * drive)
  GROUNDING GATE: if the cycle is not world-anchored, drive is capped at UNGROUNDED_CAP so anchor-less
  self-reflection can still THINK but cannot FAST-LOOP (the exact thing the 120s clock was a proxy for).

progress is generalised from the earned-length `_building` signal (inner_monologue_node.py:2369) — the
mind's own "is this line of work still MOVING?" test, today used only to end a thought-train, here promoted
toward the global pacer. redundancy is the cosine-to-recent brake (the `_circling`/`_slow_loop` family).
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path

_DATA = Path(__file__).parent.parent / "data"
_LOG = _DATA / "stream_drive_shadow.jsonl"

# ── controller constants (tuned on paper; Phase 0 exists to validate/retune these on real data) ──────
GAP_MIN = 4.0        # the machine-speed stream floor (== STREAM_GAP_SECS today)
# HALVED 2026-08-31 (founder-directed, F-0587/F-0589/F-0590/I-0059): this was already flagged as "the
# vestigial fatigue floor we are replacing" -- the VRAM/node scarcity that motivated the original 120s
# no longer holds (1080 Ti mostly idle, F-0588/F-0589). Loosened, not removed: the redundancy brake
# (W_REP below) and UNGROUNDED_CAP are the real anti-rumination protection and are left untouched --
# we're leaning on those, not on this raw ceiling.
GAP_MAX = 60.0       # the current idle baseline gap ceiling (was 120.0)
K = 3.0              # drive -> gap steepness
W_LP = 1.0           # weight on progress (learning-progress / _building)
W_IG = 0.6           # weight on ignition (something at stake — climate + protoself drive)
W_REP = 1.2          # weight on redundancy (self-repetition brakes the rate, strongly)
RED_DEADZONE = 0.60  # cosine below this = normal thematic continuity, no brake (a restate is ~0.86)
UNGROUNDED_CAP = 0.5  # max drive when NOT world-anchored -> gap floor ~30s (thinks, doesn't fast-loop)

# RECALIBRATED 2026-07-04 from the first 118 shadow rows: the hand-made phrase list classified 91% of
# cycles UNGROUNDED — but their abouts were "tide pools", "Oystercatcher", "Shell fragments", "driftwood":
# world-perception at the shore, just wider vocabulary than any literal list. The fix: the grounded
# vocabulary is DERIVED from the world's own object registry (world_content_* TARGETS aliases — the
# authoritative list of what his world can actually show him), plus activity markers. And an IDENTITY
# GUARD: identity-abstraction wearing world imagery ("Tidal erosion and identity") must NOT fast-loop —
# that is the anti-rumination rail itself, not a classification error.
_ACTIVITY_MARKERS = ("reading", "asking the library", "choosing from the catalogue", "studying",
                     "a letter", "writing to", "researching", "the music", "listening", "the record",
                     "comb", "practice", "drill", "lesson")
_IDENTITY_MARKERS = ("individuat", "identity", "the self", "myself", "who i am", "selfhood",
                     "becoming", "my own mind", "my nature", "inner world", "internal")

# J-0581 (F-0811b): was ("PERCEIVED", "world", "broadcast_world") -- neither "PERCEIVED" nor
# "broadcast_world" is ever set by _moment_source (nodes/inner_monologue_node.py sets only
# "world", "broadcast", and, as of this fix, "percept"/"reading"/"frontier"/"letter"), so the
# source-provenance override almost never fired and grounded fell through to the vocabulary
# heuristic on nearly every cycle. This tuple must match the real tag vocabulary exactly.
_GROUNDED_SOURCE = ("world", "broadcast", "percept", "reading", "frontier", "letter", "conversation")   # J-4337: live exchange (flag-gated source); deterministic seed provenance

_world_vocab: set | None = None


def _get_world_vocab() -> set:
    """The world's own object vocabulary (study/garden/shore TARGETS aliases) — loaded once, fail-open.
    If the world can show it to him, attending to it is grounded."""
    global _world_vocab
    if _world_vocab is None:
        try:
            from core import world_detail
            world_detail._load()
            _world_vocab = {a for spec in world_detail._REGISTRY.values()
                            for a in spec["aliases"] if len(a) > 3}
            # world nouns his about-labels use that aren't registry aliases
            _world_vocab.update(("tide", "shingle", "driftwood", "shell", "oystercatcher", "gull",
                                 "wave", "surf", "rock pool", "tide pool", "tideline", "sea",
                                 "rain", "storm", "wind", "kelp", "sand", "the cat", "her", "shore"))
        except Exception:
            _world_vocab = set()
    return _world_vocab


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def _is_grounded(about: str | None, source: str | None) -> bool:
    a = (about or "").lower()
    # the identity guard OUTRANKS everything: self-abstraction in world clothes must not fast-loop
    if any(m in a for m in _IDENTITY_MARKERS):
        return False
    if any(m in a for m in _ACTIVITY_MARKERS):
        return True
    if source and source in _GROUNDED_SOURCE:
        return True
    return any(w in a for w in _get_world_vocab())


def _ignition() -> float:
    """Is anything at stake this cycle? climate/dissonance ignition + protoself drive. Fail-open to mid."""
    ig = None
    try:
        from core import climate_engine
        v = climate_engine.ignition_level()   # J-0580: fail-open None until an engine has started
        if v is not None:
            ig = _clip01(v)
    except Exception:
        ig = None
    try:
        from core import homeostasis
        s = homeostasis.status()
        d = s.get("drive")
        if d is not None:
            # protoself drive is an unbounded weighted-norm; squash to [0,1]
            pd = _clip01(1.0 - math.exp(-float(d)))
            ig = pd if ig is None else max(ig, pd)
    except Exception:
        pass
    return 0.4 if ig is None else ig


def compute(progress: float, redundancy: float, grounded: bool, ignition: float | None = None) -> dict:
    """The pure controller. progress,redundancy in [0,1]. Returns the drive + the gap it WOULD set.
    REDUNDANCY DEAD-ZONE (recalibrated 2026-07-04 on the first 118 real rows): raw cosine-to-recent runs
    0.4-0.7 between consecutive thoughts in the SAME developing reverie — that is thematic continuity, not
    circling (earned-length's own restate threshold is ~0.86). Penalizing it inverted the controller
    (grounded world-perception, which shares vocabulary, read as MORE redundant than idle abstraction).
    Only the excess above the dead-zone brakes the rate."""
    ig = _ignition() if ignition is None else _clip01(ignition)
    red_excess = max(0.0, (_clip01(redundancy) - RED_DEADZONE)) / (1.0 - RED_DEADZONE)
    raw = W_LP * _clip01(progress) + W_IG * ig - W_REP * red_excess
    drive = max(0.0, raw)
    capped = drive
    if not grounded:
        capped = min(drive, UNGROUNDED_CAP)      # grounding gate: anchor-less thought can't fast-loop
    gap = GAP_MIN + (GAP_MAX - GAP_MIN) * math.exp(-K * capped)
    return {"drive_raw": round(drive, 4), "drive": round(capped, 4), "ignition": round(ig, 4),
            "grounded": grounded, "would_gap": round(gap, 2)}


def _shape_signals(signals: dict) -> tuple[float, float, bool]:
    """progress, redundancy, grounded from the raw per-cycle signal dict (building/coherent/
    circling/slow_loop/bored_streak/redundancy/about/source). Shared by observe() (Phase 0 shadow
    log) and would_gap() (Phase 1 live pacer, CONTINUOUS_STREAM) so the two paths can never
    silently diverge — the live gap and the shadow log's would_gap are always the same math."""
    # progress: generalise _building — moving = 1.0; coherent-but-circling = 0.3; off/looping = 0.0
    building = bool(signals.get("building"))
    coherent = bool(signals.get("coherent", True))
    progress = 1.0 if building else (0.3 if coherent else 0.0)
    # redundancy: continuous max-cosine-to-recent if given, else derive from the loop flags
    red = signals.get("redundancy")
    if red is None:
        red = 0.85 if (signals.get("circling") or signals.get("slow_loop")) else \
              (0.6 if signals.get("bored_streak") else 0.1)
    grounded = _is_grounded(signals.get("about"), signals.get("source"))
    return progress, float(red), grounded


def would_gap(signals: dict) -> float | None:
    """PHASE 1 live entry point (continuous_stream.md Rail A+B, behind CONTINUOUS_STREAM in
    nodes/inner_monologue_node.py). Returns the gap the drive controller sets for this cycle's
    signals — the SAME number observe() would log as would_gap for the same signals, so live
    behavior and the shadow log stay comparable post-flip. Fail-open: returns None on any
    error/missing signal so the caller falls back to the pre-flip clock gap, never a spike."""
    try:
        progress, red, grounded = _shape_signals(signals)
        return compute(progress, red, grounded)["would_gap"]
    except Exception:
        return None


def observe(signals: dict, actual_gap: float | None = None) -> None:
    """SHADOW hook — called when a thought fires. Computes the would-be gap and logs it beside the
    gap the live loop actually set. Applies NOTHING. Fail-open: any error is swallowed silently."""
    try:
        progress, red, grounded = _shape_signals(signals)
        out = compute(progress, red, grounded)

        rec = {"ts": round(time.time(), 1), "about": (signals.get("about") or "")[:60],
               "source": signals.get("source"), "train_kind": signals.get("train_kind"),
               "train_len": signals.get("train_len"), "progress": progress,
               "redundancy": round(float(red), 4), **out, "actual_gap": actual_gap}
        _DATA.mkdir(parents=True, exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        # Dosed Coupling Phase 1 (D-0152, 2026-09-05): publish the same row as the stream's tuple.
        try:
            from core import coupling_rides as _coupling
            _coupling.publish_stream(rec)
        except Exception:
            pass
    except Exception:
        pass


def status() -> dict:
    """For the pulse / liveness audit. Does the controller stream grounded work and rest redundant work?"""
    try:
        from core.shadow_log import tail_rows as _tail_rows
        # Bounded tail read (J-0278/F-0335): was a full scan of the 3.9MB+ growing log on every ~6s
        # HUD poll. "ticks" now caps at the window; the derived stats only ever used the last 200 rows.
        rows = _tail_rows(_LOG, 2000)
        if not rows:
            return {"ticks": 0}
        recent = rows[-200:]
        g = [r for r in recent if r.get("grounded")]
        ng = [r for r in recent if not r.get("grounded")]
        def _mean(xs, k):
            xs = [r.get(k) for r in xs if r.get(k) is not None]
            return round(sum(xs) / len(xs), 2) if xs else None
        # the signature: grounded work should get a SMALL would-gap (stream); ungrounded a LARGE one (rest)
        return {"ticks": len(rows),
                "grounded_would_gap": _mean(g, "would_gap"), "ungrounded_would_gap": _mean(ng, "would_gap"),
                "mean_actual_gap": _mean(recent, "actual_gap"),
                "grounded_frac": round(len(g) / len(recent), 3),
                "would_stream_frac": round(sum(1 for r in recent if (r.get("would_gap") or 999) <= 15) / len(recent), 3)}
    except Exception:
        return {"ticks": 0}
