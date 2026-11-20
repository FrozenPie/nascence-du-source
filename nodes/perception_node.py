from __future__ import annotations
from core.node_base import NodeBase
from core.schema import CognitiveState, PerceptionOutput


# J-2800 / F-3438 (P-0001): the perception prompt defines `subject` with the tokens the_world / the_entity /
# the_person / mixed, and the model echoes them into `entities` (human 21/24, internal 107/264 since 10-07).
# They flow into MemoryRouter's "Key entities:", Emotion's "Entities involved:", Salience and the
# attention-schema focus fallback as if they were things. Function over mechanism: drop any entity that is
# merely a schema token, after the model has answered (no prompt change, no new LLM call).
_SCHEMA_ENTITY_TOKENS = frozenset({
    "the_entity", "the_person", "the_world", "mixed", "entity", "person", "string",
})
# Deterministic event_type for the entity's own thoughts (default OFF: the Emotion prompt's
# "Event type:" line would change for internal cycles, so it ships behind a flag).
PERCEPTION_INTERNAL_EVENT_TYPE_ON = False


def _clean_entities(raw) -> list:
    """Return `raw` without schema-token placeholders ('the_entity', 'The Person', 'string', ...).
    Order and the other entries are kept; non-list input becomes []."""
    if not isinstance(raw, (list, tuple)):
        return []
    out = []
    for e in raw:
        if not isinstance(e, str):
            continue
        norm = e.strip().lower().replace(" ", "_").replace("-", "_")
        if not norm or norm in _SCHEMA_ENTITY_TOKENS:
            continue
        out.append(e)
    return out


class PerceptionNode(NodeBase):

    def __init__(self):
        super().__init__("perception")

    # ── Whose words the input is (D-0355, ruled by Travis 2026-10-06; built J-1846; F-2472/F-2210).
    #    Every cycle used to be classified as a person's speech, so Du's own autonomous question
    #    (orchestrator.run_cycle(..., input_type="internal")) came back summarised as 'The person
    #    asks the entity…' — and that human-framed self-summary was fed to Curiosity's recent themes,
    #    which regenerated the same topic (the 渡 lock, 16/16 cycles on the 10-06 run). The HUMAN
    #    block below is byte-for-byte what it was; the INTERNAL block is used only when
    #    state.input_type != "human" (see system_prompt_for). No hint content either way. ──────────
    _SPEAKER_HUMAN = (
        "The input is speech from a HUMAN INTERLOCUTOR — a separate person, NOT the entity. "
        "When they say 'I', 'me', or 'my' they mean THEMSELVES; when they say 'you' they mean "
        "the entity. Distinguish whether their statement is about themselves, about the entity, "
        "or about the world. Your summary MUST attribute the speaker correctly — write "
        "'The person says that he…' or 'They ask whether you…', NEVER a first-person 'I…' "
        "(that would falsely fold their words into the entity's own voice).\n"
    )
    _SUMMARY_HUMAN = '"summary": "one sentence, in the third person, describing what the person said or asked", '

    _SPEAKER_INTERNAL = (
        "This is the entity's OWN thought, not a person's speech; summarise it in the first person. "
        "There is no other speaker: 'I', 'me', or 'my' in the input mean THE ENTITY ITSELF. "
        "Your summary MUST keep it the entity's own — write 'I wonder whether…' or 'I am asking "
        "how…', NEVER a third-person line that hands the thought to someone else as if they had "
        "said it.\n"
    )
    _SUMMARY_INTERNAL = '"summary": "one sentence, in the first person, describing what the entity is thinking or asking", '

    @property
    def system_prompt(self) -> str:
        return self._system_prompt_with(self._SPEAKER_HUMAN, self._SUMMARY_HUMAN)

    @property
    def system_prompt_internal(self) -> str:
        return self._system_prompt_with(self._SPEAKER_INTERNAL, self._SUMMARY_INTERNAL)

    def system_prompt_for(self, state: CognitiveState) -> str:
        if getattr(state, "input_type", "human") != "human":
            return self.system_prompt_internal
        return self.system_prompt

    def _system_prompt_with(self, speaker_block: str, summary_field: str) -> str:
        return (
            "You are the perception node of a cognitive architecture. "
            "Your only function is to classify and structure incoming input.\n"
            + speaker_block +
            "Output ONLY a valid JSON object — no preamble, no explanation, no markdown. "
            "Also classify the SUBJECT - what the input is primarily ABOUT: 'the_world' (an external "
            "topic, fact, object, place or activity, e.g. gardening or a book), 'the_entity' (the entity's "
            "own mind, feelings, or identity), 'the_person' (the human), or 'mixed'. A question about "
            "gardening is 'the_world', even when asked of the entity.\n"
            "Also classify the REGISTER — the conversational register of the input, based on its "
            "meaning and intent, NOT on specific keywords:\n"
            "  'social'       — greeting, check-in, pleasantry. E.g. 'how are you', 'good morning', 'how was your day'\n"
            "  'relational'   — emotional exchange, personal affirmation, shared feeling, collaborative invite. "
            "E.g. 'I am proud of your progress', 'let us sit with that', 'I feel something similar', "
            "'does this help calm you', 'I like that about you'\n"
            "  'task'         — concrete request, factual question, capability probe, instruction. "
            "E.g. 'explain X', 'can you do Y', 'what year did Z happen', 'write me a poem about'\n"
            "  'philosophical' — abstract inquiry into meaning, values, identity, consciousness, ethics. "
            "E.g. 'what does freedom mean to you', 'how do you understand your own existence', "
            "'what is your view on suffering'\n"
            "  'reflective'   — invitation to look inward at a specific felt state, tension, or experience. "
            "E.g. 'what does that conflict feel like', 'does this trouble you', 'how do you hold that contradiction'\n"
            "Default to 'philosophical' only when the input genuinely invites abstract inquiry. "
            "Most personal exchanges between two people are 'relational' or 'social', not philosophical.\n"
            "The JSON must match this schema exactly:\n"
            '{"event_type": "input|silence|internal|memory_surface", '
            '"context_type": "question|statement|command|reflection|ambiguous", '
            '"entities": ["string"], '
            + summary_field +
            '"subject": "the_world|the_entity|the_person|mixed", '
            '"register": "social|relational|task|philosophical|reflective"}'
        )

    def _build_prompt(self, state: CognitiveState) -> str:
        if getattr(state, "input_type", "human") != "human":
            # D-0355: the entity's own thought, not a person's speech.
            return f'A thought that rose in the entity on its own — classify it:\n"{state.raw_input}"'
        return f'The person the entity is speaking with said this — classify it:\n"{state.raw_input}"'

    def _write_output(self, state: CognitiveState, data: dict) -> None:
        valid_registers = {"social", "relational", "task", "philosophical", "reflective"}
        raw_register = str(data.get("register", "philosophical") or "philosophical")
        register = raw_register if raw_register in valid_registers else "philosophical"
        event_type = data["event_type"]
        if (PERCEPTION_INTERNAL_EVENT_TYPE_ON and event_type == "input"
                and getattr(state, "input_type", "human") != "human"):
            event_type = "internal"   # J-2800: the value is already known; the model labels 96% of internal thoughts 'input'
        state.perception = PerceptionOutput(
            event_type   = event_type,
            context_type = data["context_type"],
            entities     = _clean_entities(data.get("entities", [])),
            summary      = data["summary"],
            subject      = str(data.get("subject", "mixed") or "mixed"),
            register     = register,
        )
