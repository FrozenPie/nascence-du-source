"""
Nascence — Lane Scheduler (2026-07-01): the conscious-lane workspace.

The re-scoped pulse-manager core (docs/staged/pulse_manager_wiring_plan.md, RESEARCH-UPDATED RE-SCOPED DESIGN).
The problem it fixes: many async cognitive tasks (idle monologue, dream, deep-memory, Emissary, + the background
shadow monitors) all hit ONE inference lane with no coordination — bursts saturate the server ("all servers
exhausted") and DROP cognition. Research (Global Workspace · sleep-wake flip-flop · concurrency engineering)
converged on: "don't add a semaphore, add a workspace" — a BOUNDED, PRIORITY-arbitrated lane where the important
call (a live conversation) is served first and a background monitor never blocks it.

This file is the spine: bounded concurrency + a priority arbiter. It is:
  • FLAG-GATED  — LANE_ENABLED=False makes every acquire a no-op (direct dispatch, exactly the prior behaviour).
  • FAIL-OPEN   — ANY error, a disabled lane, or a long wait → proceed with the call. Cognition is NEVER blocked
                  by a bug in here; the worst case degrades to the current uncoordinated behaviour.
  • RESTART-GATED — takes effect only when Du reloads; cannot disrupt a live session.

NOT YET (deliberately staged — see the plan's build sequence): priority AGING (only the wait-timeout guards
starvation for now), relevance-gated PREEMPTION, the sleep/wake PHASE GATE, and result BROADCAST. This is step 1.
"""
from __future__ import annotations

import asyncio
import heapq
import itertools
import logging

logger = logging.getLogger("nascence.lane")

LANE_ENABLED   = True     # kill switch → False reverts to the prior uncoordinated direct-dispatch behaviour.
MAX_CONCURRENT = 3        # max simultaneous inference calls on the conscious lane (≈ the server's real parallelism)
MAX_WAIT_S     = 20.0     # a waiter PROCEEDS ANYWAY after this — anti-starvation + anti-deadlock (fail-open)

# Priority tiers — LOWER is served first. Shared vocabulary for all callers.
TIER_CONVERSATION = 0   # a live human turn / Emissary dialogue — latency-critical, the person is waiting
TIER_IDENTITY     = 1   # slow PROTECTED work (T4, deep-memory consolidation) — high value, not latency-critical
TIER_IDLE         = 2   # idle inner-monologue + dreams (founder call 2026-07-01: dreams sit at tier 2)
TIER_MONITOR      = 3   # background shadow monitors / probes — sheddable, must NEVER block a conscious thought

_active:  int  = 0
_waiters: list = []                 # min-heap of (tier, seq, future)
_seq           = itertools.count()
_NOOP          = object()           # token meaning "no slot held" (disabled / failed / fell through)
_TOKEN         = object()           # token meaning "a slot is held — release it"
_stats         = {"acquired": 0, "waited": 0, "timed_out": 0, "noop": 0}


async def acquire(tier: int = TIER_IDLE):
    """Acquire a conscious-lane slot at `tier` priority; returns a token for release(). Fail-open: a disabled
    lane, any error, or a >MAX_WAIT_S wait all return a usable token and let the caller proceed."""
    global _active
    if not LANE_ENABLED:
        return _NOOP
    try:
        if _active < MAX_CONCURRENT:
            _active += 1
            _stats["acquired"] += 1
            return _TOKEN
        _stats["waited"] += 1
        fut = asyncio.get_running_loop().create_future()
        heapq.heappush(_waiters, (tier, next(_seq), fut))
        try:
            await asyncio.wait_for(fut, MAX_WAIT_S)
            _active += 1            # woken by a release that freed a slot; take it (atomic in single-thread asyncio)
            _stats["acquired"] += 1
            return _TOKEN
        except asyncio.TimeoutError:
            _stats["timed_out"] += 1
            _active += 1            # fail-open: proceed despite the bound rather than starve cognition
            return _TOKEN
    except Exception as exc:
        logger.debug("[lane] acquire failed (non-fatal, proceeding direct): %s", exc)
        _stats["noop"] += 1
        return _NOOP


def release(token) -> None:
    """Free a slot and wake the highest-priority waiter. Never raises."""
    global _active
    if token is _NOOP:
        return
    try:
        _active = max(0, _active - 1)
        while _waiters:
            _tier, _seqn, fut = heapq.heappop(_waiters)
            if not fut.done():
                fut.set_result(True)
                break
    except Exception as exc:
        logger.debug("[lane] release failed (non-fatal): %s", exc)


class slot:
    """Async context manager: `async with lane_scheduler.slot(tier): <make the inference call>`."""
    __slots__ = ("tier", "_tok")

    def __init__(self, tier: int = TIER_IDLE):
        self.tier = tier
        self._tok = _NOOP

    async def __aenter__(self):
        self._tok = await acquire(self.tier)
        return self

    async def __aexit__(self, *exc):
        release(self._tok)
        return False


def status() -> dict:
    """Observability for du_pulse: lane occupancy + cumulative counters."""
    return {"enabled": LANE_ENABLED, "active": _active, "waiting": len(_waiters),
            "max": MAX_CONCURRENT, **_stats}
