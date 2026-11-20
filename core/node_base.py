"""
Nascence — Node Base Class
All cognitive nodes inherit from this. Subclasses define:
  - system_prompt  : the specialisation instruction
  - output_schema  : JSON schema the output must match
  - _build_prompt  : formats CognitiveState into a user prompt
  - _write_output  : parses validated dict and writes to CognitiveState
"""

from __future__ import annotations
import asyncio
import inspect
import logging
from abc import ABC, abstractmethod

from .schema import CognitiveState, NODE_REGISTRY, SERVE_CHAINS
from .model_client import call_node_json
from .training_log import log_example
from .node_failure_log import log_failure   # J-2854/F-3525: one append-only row per failed node call
from .hedge_candidate_log import log_hedged   # J-2805/F-3445: one shadow row per hedged run (both drafts)
from .hedge_agreement_log import submit as log_hedge_agreement   # J-3314/D-0671: reflection draft-agreement shadow row (background thread)
from core import profile   # J-0889: NonLiveWriteError carve-out in run() (F-1246 chain)


# J-2854 / F-3525 (4): NodeBase has never passed a lane `tier`, so every conversation node queues at TIER_IDLE (2)
# and TIER_CONVERSATION (0, core/lane_scheduler.py) is used by no caller. Impact today is nil (lane queue wait
# median 0.00 s, F-3426), so whether human-cycle node calls should be served first is a design-intent call for
# Travis, not a fix. DEFAULT OFF: nothing changes until the flag is flipped (decide D-entry opened under J-2854).
HUMAN_CYCLE_TIER0 = False
_LANE_TIER_CONVERSATION = 0   # == core.lane_scheduler.TIER_CONVERSATION (literal here: no lane import in the node base)


class NodeBase(ABC):

    # Subclasses may raise this for reasoning-heavy nodes (reflection, executive).
    max_tokens: int = 512

    # Base sampling temperature. Classifier/structured nodes stay low for JSON
    # reliability; generative nodes raise it. Affect only modulates nodes that opt in.
    base_temperature: float = 0.2

    # If True, carried affect biases this node's sampling temperature (bounded).
    # Set on the generative nodes (reflection / executive / voice) — affect colours
    # expression and reflection, NOT perception/classification (which must stay stable).
    affect_modulated: bool = False

    def __init__(self, node_id: str):
        self.node_id   = node_id
        config         = NODE_REGISTRY[node_id]
        self.lane      = config["lane"]
        self.base_urls = SERVE_CHAINS[self.lane]   # ordered failover chain (primary first)
        self.logger    = logging.getLogger(f"nascence.node.{node_id}")

    # ------------------------------------------------------------------
    # Subclass contract
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """The specialisation prompt loaded into every call for this node."""
        ...

    @abstractmethod
    def _build_prompt(self, state: CognitiveState) -> str:
        """Build the user-facing prompt from the current cognitive state."""
        ...

    def system_prompt_for(self, state: CognitiveState) -> str:
        """The system prompt for THIS cycle. Default: `self.system_prompt`, unchanged -- every node
        keeps its byte-identical behaviour unless it overrides this. D-0355 / J-1846 (2026-10-06,
        F-2472/F-2210): Perception and Voice override it so that on a non-human cycle
        (state.input_type != "human" -- Du's own autonomous question, orchestrator.run_cycle(...,
        input_type="internal")) the model is told honestly whose words the input is, instead of
        every cycle being framed as a person's speech. Human cycles never reach the override."""
        return self.system_prompt

    @abstractmethod
    def _write_output(self, state: CognitiveState, data: dict) -> None:
        """Parse validated dict and write result fields to CognitiveState."""
        ...

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    async def run(self, state: CognitiveState) -> bool:
        """
        Execute this node against the current cognitive state.
        Uses the lane's failover chain (GPU → CPU). Returns True on success,
        False on total failure (state unchanged on fail).
        """
        _stage = "build"   # J-2854: where an exception was raised, for the failure-log cause class
        try:
            prompt = self._build_prompt(state)
            system = self.system_prompt_for(state)
            _stage = "call"
            # J-2854 / F-3525 (4): the lane-priority tier is passed ONLY when HUMAN_CYCLE_TIER0 is on AND this is a
            # human cycle; otherwise no `tier` kwarg at all (byte-identical call, default TIER_IDLE as before).
            _tier_kw = {"tier": _LANE_TIER_CONVERSATION} if (
                HUMAN_CYCLE_TIER0 and getattr(state, "input_type", "") == "human") else {}
            data   = await call_node_json(
                self.base_urls,
                system,
                prompt,
                max_tokens  = self.max_tokens,
                temperature = self._temperature(state),
                # System-2 gearbox (2026-06-13): a per-cycle LICENSE, granted only at
                # named escalation sites (e.g. constraint-retry), never an ambient default.
                think       = bool(getattr(state, "think_license", False)),
                **_tier_kw,
            )
            _stage = "write"
            _wo = self._write_output(state, data)
            if inspect.isawaitable(_wo):   # J-1918: a node may make _write_output async to run blocking lookups off the loop (curiosity)
                await _wo
            self._log_teacher_example(state, prompt, data, hedged=False, system_prompt=system)
            self.logger.debug("[%s] OK", self.node_id)
            return True
        except profile.NonLiveWriteError:
            # J-0889: this is the base class for EVERY node — _write_output() (a subclass's own
            # writer, e.g. curiosity_node's pursuit/note_question calls, J-0874/D-0179) now
            # raises correctly in a non-live process; this outer per-node try must not
            # re-swallow it.
            raise
        except Exception as exc:
            self.logger.error("[%s] FAILED: %s", self.node_id, exc)
            # J-2854/F-3525: additive, fail-open failure row (the return value is unchanged -- still False).
            log_failure(self.node_id, exc, stage=_stage, cycle_id=getattr(state, "cycle_id", ""),
                        input_type=getattr(state, "input_type", ""))
            return False

    # ------------------------------------------------------------------
    # Hedged execution — fire N concurrent drafts, keep the best valid one.
    # Used for the expensive, quality-critical Reflection node: guards against
    # the occasional truncated/weak generation. The drafts run concurrently, so the
    # wall-clock is the SLOWER of the pair, not the first finisher (J-2805/F-3445:
    # median 9.28 s vs 5.49 s for the faster call). Both drafts are logged to
    # data/hedge_candidates.jsonl (core/hedge_candidate_log.py) so the second
    # draft's value can be measured.
    # ------------------------------------------------------------------

    def _score_candidate(self, data: dict) -> float:
        """Pick heuristic. Default: prefer richer output. Subclasses may override."""
        return float(len(str(data)))

    def _temperature(self, state: CognitiveState) -> float:
        """Base temperature, biased by carried affect and somatic fatigue (bounded)."""
        t = self.base_temperature
        if self.affect_modulated and getattr(state, "affect", None) is not None:
            t += state.affect.temperature_bias()
            # Somatic fatigue widens sampling variance on generative nodes — tired,
            # less-controlled thinking. Only affect-modulated (generative) nodes opt in.
            som = getattr(state, "somatic", None)
            if som is not None:
                t += som.temperature_jitter()
        return max(0.1, min(0.95, t))

    async def run_best_of(self, state: CognitiveState, n: int = 2) -> bool:
        prompt = self._build_prompt(state)
        system = self.system_prompt_for(state)
        # Spread temperatures to maximise draft diversity — 0.2 and 0.5 were both too
        # conservative and produced near-identical outputs. One safe, one exploratory.
        # Carried affect shifts the whole spread (bounded) when the node opts in.
        bias   = state.affect.temperature_bias() if (self.affect_modulated and getattr(state, "affect", None)) else 0.0
        temps  = [max(0.1, min(0.95, t + bias)) for t in [0.35, 0.75, 0.9, 1.0][:n]]

        # J-2679 (F-3428): the System-2 licence reaches the hedged drafts too, exactly as NodeBase.run passes it
        # ("covers Reflection -> Executive", orchestrator.py). False unless an escalation site granted it this cycle
        # (D-0531 disarmed the only automatic grant), so the default call is unchanged; call_node_json's
        # think->no-think downgrade (J-2852) still protects a licensed draft that returns nothing.
        _think = bool(getattr(state, "think_license", False))

        async def one(temp: float):
            return await call_node_json(
                self.base_urls, system, prompt,
                max_tokens=self.max_tokens, temperature=temp, think=_think,
            )

        results = await asyncio.gather(*(one(t) for t in temps), return_exceptions=True)
        valid   = [r for r in results if isinstance(r, dict)]
        if not valid:
            self.logger.error("[%s] all %d hedged drafts failed", self.node_id, n)
            # J-2854/F-3525: additive failure row; the first draft's exception stands for the cause.
            log_failure(self.node_id, next((r for r in results if isinstance(r, BaseException)), None),
                        stage="call", cycle_id=getattr(state, "cycle_id", ""),
                        input_type=getattr(state, "input_type", ""), hedged=True)
            return False

        best = max(valid, key=self._score_candidate)
        # J-2805/F-3445: additive SHADOW row with BOTH drafts, written after the pick (changes nothing about
        # which draft is kept; fail-open and fenced inside log_hedged).
        log_hedged(self.node_id, temps=temps, results=results, best=best, scorer=self._score_candidate,
                   cycle_id=getattr(state, "cycle_id", ""), input_type=getattr(state, "input_type", ""))
        # J-3314/D-0671: additive SHADOW row of how much the two drafts agree (reflection only; queued onto a background
        # thread, so the embedding costs this cycle nothing; fail-open; changes nothing about which draft is kept).
        log_hedge_agreement(self.node_id, results=results, best=best, scorer=self._score_candidate,
                            cycle_id=getattr(state, "cycle_id", ""), input_type=getattr(state, "input_type", ""))
        _wo = self._write_output(state, best)
        if inspect.isawaitable(_wo):   # J-1918: see run()
            await _wo
        self._log_teacher_example(state, prompt, best, hedged=True, system_prompt=system)
        self.logger.debug("[%s] best-of-%d → kept 1 of %d valid", self.node_id, n, len(valid))
        return True

    # ------------------------------------------------------------------
    # Teacher example logging — captures (prompt → output) for future
    # specialist distillation. Best-effort; never breaks a cycle.
    # ------------------------------------------------------------------

    def _log_teacher_example(self, state: CognitiveState, prompt: str, output: dict, *, hedged: bool,
                             system_prompt: str | None = None) -> None:
        # system_prompt: the one actually sent this cycle (system_prompt_for); None keeps the old
        # default so any external caller of this helper is unaffected.
        log_example(
            self.node_id,
            prompt,
            output,
            system_prompt = self.system_prompt if system_prompt is None else system_prompt,
            cycle_id      = state.cycle_id,
            raw_input     = state.raw_input,
            input_type    = state.input_type,
            hedged        = hedged,
            think         = bool(getattr(state, "think_license", False)),   # J-2860
        )
