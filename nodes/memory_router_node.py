from __future__ import annotations
from core.node_base import NodeBase
from core.schema import CognitiveState, MemoryRouterOutput


class MemoryRouterNode(NodeBase):

    def __init__(self):
        super().__init__("memory_router")

    # -- Whose words the input is (J-2836, row P-0004, F-3496; same pattern as Perception / Voice, D-0355).
    #    1991 of 1991 logged non-human prompts said 'The person you are speaking with said:' while
    #    Perception's summary on the same cycle was first person. The HUMAN prompt is byte-for-byte what it
    #    was; the INTERNAL lines are used only when state.input_type != "human". No hint about WHAT to
    #    remember either way (the world answers, never leads). Restart-gated. --------------------------------
    _INTERNAL_SYSTEM_LINE = (
        "The input is the entity's OWN thought, not a person's speech; there is no other speaker. "
    )

    # -- Placeholder / pronoun tokens Perception writes into `entities` (P-0001, F-3438: 62.7 percent of
    #    logged router calls carried only these). They name no memory, so they are not written to the prompt.
    _JUNK_ENTITY_TOKENS = frozenset({
        "the entity", "the person", "the world", "the entity's interlocutor", "the interlocutor",
        "the person the entity is speaking with", "entity", "person", "interlocutor",
        "you", "your", "yours", "i", "me", "my", "mine", "we", "us", "he", "she", "they", "them", "it",
        "string", "none", "null", "n/a", "unknown",
    })

    @classmethod
    def _real_entities(cls, entities) -> list:
        out = []
        for e in entities or []:
            key = " ".join(str(e).replace("_", " ").lower().split()).strip(" .\"'")
            if key and key not in cls._JUNK_ENTITY_TOKENS:
                out.append(e)
        return out

    @property
    def system_prompt(self) -> str:
        return self._system_prompt_with("")

    @property
    def system_prompt_internal(self) -> str:
        return self._system_prompt_with(self._INTERNAL_SYSTEM_LINE)

    def system_prompt_for(self, state: CognitiveState) -> str:
        if getattr(state, "input_type", "human") != "human":
            return self.system_prompt_internal
        return self.system_prompt

    def _system_prompt_with(self, input_line: str) -> str:
        return (
            "You are the memory routing node of a cognitive architecture. "
            + input_line +
            "You do not retrieve memories — you generate the best search keys to retrieve them. "
            "Output ONLY a valid JSON object. No preamble. No explanation.\n"
            "Schema: {\"episodic_keys\": [\"event term\"], \"semantic_keys\": [\"concept term\"], "
            "\"time_bias\": \"recent|distant|all\", \"working_memory_sufficient\": false}\n"
            "episodic_keys: 2–4 terms for finding specific past events.\n"
            "semantic_keys: 2–4 terms for finding general concepts and knowledge.\n"
            "time_bias: 'recent' for current-context queries, 'distant' for deep history, 'all' for broad search.\n"
            "Set working_memory_sufficient=true ONLY when the input is trivially answerable "
            "from the current cycle context alone with no memory needed."
        )

    def _build_prompt(self, state: CognitiveState) -> str:
        # Runs in Wave 2 (parallel with Salience), so it reads Perception only —
        # Salience focus is not yet available. Perception's entities + summary are
        # enough to generate good retrieval keys.
        if getattr(state, "input_type", "human") != "human":
            lines = [f'The entity\'s own thought:\n"{state.raw_input}"']
        else:
            lines = [f'The person you are speaking with said:\n"{state.raw_input}"']
        if state.perception:
            lines.append(f"Summary: {state.perception.summary}")
            ents = self._real_entities(state.perception.entities)
            if ents:
                lines.append(f"Key entities: {', '.join(ents)}")
        return "\n".join(lines)

    def _write_output(self, state: CognitiveState, data: dict) -> None:
        state.memory_keys = MemoryRouterOutput(
            episodic_keys             = data.get("episodic_keys", []),
            semantic_keys             = data.get("semantic_keys", []),
            time_bias                 = data.get("time_bias", "recent"),
            working_memory_sufficient = bool(data.get("working_memory_sufficient", False)),
        )
