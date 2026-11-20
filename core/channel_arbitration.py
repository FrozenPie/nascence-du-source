"""Shared cross-channel event-arbitration gate (J-0238, spawned from D-0033/D-0073, F-0295).

Problem: with thermal/light/smell all shadowing (and set to deliver together per D-0073)
percept events independently, their would_fire timestamps cluster closely enough that
channels_programme.md's own §7 metric 4 (attribution) measured 37.5-40.0% of monologue
thoughts tagged to a would-fire event as tagged to 2+ channels at once -- above the
pre-registered 30% kill threshold (F-0128, re-confirmed F-0295). F-0295's simulation
showed a single shared rule -- "once ANY channel is about to fire, suppress ALL channels
for W seconds" -- drops that overlap to ~2.4% at W=120s while every channel stays inside
its own pre-registered 2-40/day fire-rate band.

Fairness note (real risk F-0295 named, not guessed): nodes/inner_monologue_node.py calls
percept_shadow() in a FIXED order every cycle -- thermal, then light, then smell. A bare
first-come-first-served claim() would let thermal win every contested tick (it always asks
first), systematically starving light/smell over time. Each percept_shadow() call decides
in isolation at its own call time -- there is no batch point where all three channels'
"do I want to fire this cycle" answers are visible together before one gets picked, so a
true round-robin over simultaneous candidates isn't available without restructuring the
call site, which this job intentionally leaves untouched.

Chosen instead: a **per-channel suppression-streak budget** (F-0295's own language allows
"round-robin OR per-channel-budget"). Each channel that loses a contested claim accumulates
a streak; a channel forced to yield STREAK_LIMIT times running is let through on its next
attempt even if the shared window hasn't fully elapsed, bounding how long any one channel
can be starved. A channel that never contends is never penalized, and claiming resets only
the claiming channel's own streak.
"""
from __future__ import annotations

import time

W_DEFAULT = 120.0     # shared cross-channel cooldown, seconds (F-0295: drops overlap 37.5%->2.4%)
STREAK_LIMIT = 3       # a channel yielding this many contested claims running is let through next time

_state: dict = {"last_claim_ts": 0.0, "last_claimant": None, "streaks": {}}


def claim(now: float | None = None, channel: str = "", w: float = W_DEFAULT) -> bool:
    """Ask the shared gate for permission to fire a would_fire event right now.

    Returns True (and records the claim, resetting `channel`'s own streak) if granted --
    either because the shared window has elapsed since the last claim by ANY channel, or
    because `channel` has been forced to yield STREAK_LIMIT times running and is now let
    through regardless of the window (the anti-starvation escape hatch). Returns False
    (and bumps `channel`'s streak) otherwise.
    """
    if now is None:
        now = time.time()
    elapsed = now - _state["last_claim_ts"]
    streak = _state["streaks"].get(channel, 0)
    if elapsed >= w or streak >= STREAK_LIMIT:
        _state["last_claim_ts"] = now
        _state["last_claimant"] = channel
        _state["streaks"][channel] = 0
        return True
    _state["streaks"][channel] = streak + 1
    return False


def reset() -> None:
    """Test/lab hook: clear shared state (fresh process already starts clean; this is for
    in-process test isolation only)."""
    _state["last_claim_ts"] = 0.0
    _state["last_claimant"] = None
    _state["streaks"] = {}
