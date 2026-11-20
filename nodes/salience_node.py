from __future__ import annotations
from core.node_base import NodeBase
from core.llm_parse import as_float
from core.schema import CognitiveState, SalienceOutput, interrupt_warranted


class SalienceNode(NodeBase):

    def __init__(self):
        super().__init__("salience")

    # J-2850 / F-3462, F-3463 (P-0003): internal cycles used to be framed as "The person you are speaking
    # with said:" and the system prompt carried the raw 0.7 threshold. Human block keeps its wording;
    # the INTERNAL block (input_type != "human") never mentions a user. The numeric threshold now lives only
    # in code (INTERRUPT_THRESHOLD / interrupt_warranted); the prompt says it in words. No hint content.
    _ROLE = (
        "You are the salience and attention node of a cognitive architecture. "
        "You determine what matters most right now and whether the situation demands immediate action. "
    )
    _ROLE_INTERNAL = (
        "You are the salience and attention node of a cognitive architecture. "
        "You determine what matters most to the entity right now and whether its own thought demands "
        "immediate action. There is no other speaker. "
    )

    def _prompt_with(self, role: str) -> str:
        return (
            role
            + "Output ONLY a valid JSON object. No preamble. No explanation.\n"
            "Schema: {\"urgency\": 0.0, \"focus\": [\"term1\", \"term2\"], "
            "\"interrupt\": false, \"reasoning\": \"one sentence\"}\n"
            "urgency: 0.0 = routine, 1.0 = critical. "
            "Set interrupt=true only when the matter is critical (pre-empts all background processing); "
            "most cycles are not. "
            "focus: 2–4 key terms that should receive the most attention this cycle."
        )

    @property
    def system_prompt(self) -> str:
        return self._prompt_with(self._ROLE)

    @property
    def system_prompt_internal(self) -> str:
        return self._prompt_with(self._ROLE_INTERNAL)

    def system_prompt_for(self, state: CognitiveState) -> str:
        if getattr(state, "input_type", "human") != "human":
            return self.system_prompt_internal
        return self.system_prompt

    def _build_prompt(self, state: CognitiveState) -> str:
        # Runs in Wave 2 (parallel with Emotion), so it reads Perception only —
        # Emotion is not yet available. Emotional modulation still reaches the
        # downstream Reflection/Executive nodes where it matters most.
        p = state.perception
        if getattr(state, "input_type", "human") != "human":
            lines = [f'This rose in you on its own; no one said it:\n"{state.raw_input}"']
        else:
            lines = [f'The person you are speaking with said:\n"{state.raw_input}"']
        if p:
            lines.append(f"Perceived as: {p.context_type} — {p.summary}")
            if p.entities:
                lines.append(f"Entities: {', '.join(p.entities)}")
        return "\n".join(lines)

    def _write_output(self, state: CognitiveState, data: dict) -> None:
        urgency   = as_float(data.get("urgency"), 0.0)
        interrupt = bool(data.get("interrupt", False))

        state.salience = SalienceOutput(
            urgency   = urgency,
            focus     = data.get("focus", []),
            interrupt = interrupt,
            reasoning = data.get("reasoning", ""),
        )

        # J-2849 / F-3521: one predicate with Orchestrator._interrupt_active() (urgency > INTERRUPT_THRESHOLD). The model's
        # own interrupt boolean alone no longer raises the flag: its prompt already says to set it only above the threshold,
        # and a flag the orchestrator does not recognise only froze idle thought silently. The model's value is still
        # recorded in state.salience.interrupt above.
        if interrupt_warranted(urgency):
            state.interrupt_requested = True
            state.interrupt_urgency   = urgency
            state.interrupt_source    = "salience"
