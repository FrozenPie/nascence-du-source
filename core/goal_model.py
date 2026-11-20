"""
Nascence — Goal Model (Executive Goal Persistence, Phase 1)

Prevents the self-model from capturing attention and substituting self-reflection for task
completion. When a concrete task is active, the Goal Model records it and injects a completion
criterion into Reflection + Critic so goal drift is caught before it becomes a 29-second pork
pairing tangent.

Phase 1 is simple: a stack of string goals derived from content_mode detection, no LLM. Phase 2
(planned) will infer more nuanced goals from Executive synthesis. The Cognitive Model Quartet:

    Self Model  — Who am I?           (axiom, cadence, tensions)
    Social Model — Who are you?       (user expectations, trust, correction signal)
    World Model  — What is true?      (semantic + episodic memory)
    Goal Model   — What are we doing? (active task objective) ← this file
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger("nascence.goal")


@dataclass
class GoalState:
    active_goal:          str | None  = None
    goal_stack:           list[str]   = field(default_factory=list)
    completion_criteria:  str | None  = None
    goal_relevance:       float       = 0.0   # 0..1 — how task-focused this cycle is

    def push(self, goal: str, criteria: str, relevance: float = 1.0) -> None:
        if self.active_goal:
            self.goal_stack.append(self.active_goal)
        self.active_goal = goal
        self.completion_criteria = criteria
        self.goal_relevance = relevance
        if len(self.goal_stack) > 5:
            self.goal_stack = self.goal_stack[-5:]

    def pop(self) -> str | None:
        popped = self.active_goal
        self.active_goal = self.goal_stack.pop() if self.goal_stack else None
        self.completion_criteria = None
        self.goal_relevance = 0.0
        return popped

    def clear(self) -> None:
        self.active_goal = None
        self.goal_stack.clear()
        self.completion_criteria = None
        self.goal_relevance = 0.0

    def note(self) -> str | None:
        if not self.active_goal:
            return None
        s = f"Active task: {self.active_goal}"
        if self.completion_criteria:
            s += f" — done when: {self.completion_criteria}"
        return s

class GoalManager:
    """
    Derives and tracks the active GoalState from content_mode + Perception.
    Lives on the Orchestrator; updates state.active_goal_note each cycle.
    """

    def __init__(self):
        self.state = GoalState()
        self._cycles_on_task = 0

    def update(self, raw_input: str, content_mode: bool) -> None:
        """
        Called once per cycle post-Perception. Pushes a new goal when content_mode
        turns on; pops it when content_mode is off and we were tracking a task.
        """
        if content_mode:
            # Push a fresh goal from the current input
            goal = raw_input[:120].strip()
            criteria = "answer the question or complete the task directly"
            self.state.push(goal, criteria, relevance=1.0)
            self._cycles_on_task += 1
        else:
            # Not a task cycle — the conversation has moved to an open/abstract turn, so the old concrete
            # goal is ABANDONED, not paused. CLEAR it (and the stack). Was pop(), which RESURRECTED a stale
            # goal from the stack: on an abstract turn the Critic was then handed an OLD concrete question
            # from many turns ago (the cat-name, the location) and rejected the CURRENT draft for "evading"
            # it — firing well after that question was handled, and dragging the dead question back into the
            # conversation. The Critic must anchor to the current turn, not a resurrected one. (2026-06-30)
            if self.state.active_goal:
                self.state.clear()
                self._cycles_on_task = 0
