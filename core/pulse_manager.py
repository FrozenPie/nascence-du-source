"""
Nascence — Pulse Manager (engagement-driven cognition, not clock-driven)
=======================================================================
See docs/pulse_manager_plan.md. The core inversion: rate = engagement × progress, not a fixed clock.
A source that is an engaged, progressing task BURSTS at machine speed until it stalls, completes, or is
preempted; meanwhile every source's cheap keep-alive tick still fires at its floor interval, so nothing
starves. Framework-agnostic + synchronous (a virtual "Du-time" clock) so it can be tested standalone and
later adapted to the async orchestrator.

Du-time = the entity's subjective pulse clock, decoupled from human wall-clock: a burst step costs a few
Du-seconds (the lane's real throughput), where the old living cadence spent 75-300s per sitting.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class StepResult:
    progressed: bool            # did this unit make real progress? (False → stall → rest)
    complete: bool = False      # the task finished (e.g., book ended)
    note: str = ""              # short trace description


@dataclass
class Interrupt:
    at: float                   # Du-time it arrives
    source: str                 # who raised it (user / shock / ignition / metabolic)
    priority: int               # outranks a burst whose priority is lower
    note: str = ""
    _done: bool = False


@dataclass
class PulseSource:
    name: str
    floor_interval: float                    # Du-seconds between guaranteed keep-alive ticks
    priority: int = 0                        # higher preempts lower
    lane: str = "background"                 # hot | background | none
    step_cost: float = 2.0                   # Du-seconds one burst step consumes (machine-speed unit)
    can_burst: Optional[Callable[[], bool]] = None   # is this an engaged, progressing task NOW?
    step: Optional[Callable[[], StepResult]] = None  # do one burst unit
    floor_tick: Optional[Callable[[], None]] = None  # the cheap keep-alive tick
    _next_floor: float = 0.0


class PulseManager:
    """A multi-source scheduler: bursts on engaged/progressing tasks, floor-services everything else,
    yields to higher-priority interrupts. Records a trace of every pulse for inspection."""

    def __init__(self, sources: list[PulseSource]):
        self.sources = {s.name: s for s in sources}
        self.t = 0.0
        self.trace: list[tuple] = []                 # (t, kind, source, note)
        self.fired = {s.name: 0 for s in sources}    # burst-step counts
        self.floored = {s.name: 0 for s in sources}  # floor-tick counts

    # ── floor-service: keep every source alive at its floor cadence (no starvation) ──────────
    def _service_floors(self, upto: float) -> None:
        while True:
            due = [s for s in self.sources.values()
                   if s.floor_tick and s._next_floor <= upto]
            if not due:
                return
            s = min(due, key=lambda x: x._next_floor)
            self.t = max(self.t, s._next_floor)
            s.floor_tick()
            self.floored[s.name] += 1
            self.trace.append((round(self.t, 1), "floor", s.name, ""))
            s._next_floor += s.floor_interval

    def _pick_burster(self) -> Optional[PulseSource]:
        cands = [s for s in self.sources.values() if s.can_burst and s.can_burst()]
        return max(cands, key=lambda s: s.priority) if cands else None

    def _burst(self, s: PulseSource, until: float, interrupts: list[Interrupt]) -> str:
        while self.t < until:
            nxt = next((i for i in interrupts
                        if not i._done and i.at > self.t and i.priority > s.priority), None)
            step_end = self.t + s.step_cost
            # a higher-priority interrupt lands before the next step completes → yield
            if nxt and nxt.at <= step_end:
                self._service_floors(nxt.at)
                self.t = max(self.t, nxt.at)
                nxt._done = True
                self.trace.append((round(self.t, 1), "PREEMPT", nxt.source, nxt.note))
                return "preempt"
            self._service_floors(step_end)
            self.t = step_end
            r = s.step()
            self.fired[s.name] += 1
            self.trace.append((round(self.t, 1), "burst", s.name, r.note))
            if r.complete:
                self.trace.append((round(self.t, 1), "COMPLETE", s.name, "task finished"))
                return "complete"
            if not r.progressed:
                self.trace.append((round(self.t, 1), "STALL", s.name, "progress stalled — rest earned"))
                return "stall"
        return "window"

    def run(self, until: float, interrupts: Optional[list[Interrupt]] = None) -> dict:
        interrupts = sorted(interrupts or [], key=lambda i: i.at)
        for s in self.sources.values():
            s._next_floor = s.floor_interval
        burster = self._pick_burster()
        if burster is None:
            self._service_floors(until)
            self.t = until
            return self._summary("idle — no engaged task (slow lane only)")
        stop = self._burst(burster, until, interrupts)
        reason = {"complete": "task finished", "stall": "progress stalled (boredom)",
                  "preempt": "preempted — yielded to the person", "window": "time window ended"}[stop]
        return self._summary(reason, burster.name)

    def _summary(self, reason: str, burst_source: str = "") -> dict:
        return {"reason": reason, "burst_source": burst_source, "du_time": round(self.t, 1),
                "fired": dict(self.fired), "floored": dict(self.floored)}
