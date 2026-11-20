"""
Nascence — Cognitive Schema
The shared contract between all nodes. Every node reads from and writes to
CognitiveState. Every node output must validate against its JSON schema.
Nothing gets passed between nodes as free text.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal
import re
import time
import uuid

# J-3284: the via phrase of a looked-up page, "[Looked up: '<Title>' (<via>)] ..." (core/web_research.store_finding).
_LOOKED_UP_VIA_RE = re.compile(r"\[Looked up: '.*?' \((asked by him|external shock)")

# J-3173 / D-0561: the label for an origin='lived' fragment that RECORDS a no-human cycle (see readable_label). The
# input_type values are CognitiveState.input_type's non-human kinds (the same split core/internal_context_gate uses:
# input_type != "human"). INTERNAL_CYCLE_LABEL_ON is the kill switch (False = every lived row reads "Our conversation").
INTERNAL_CYCLE_LABEL_ON = True
INTERNAL_CYCLE_INPUT_TYPES = ("internal", "timer")
INTERNAL_CYCLE_LABEL = "My own earlier idle thought and reply"


# ---------------------------------------------------------------------------
# Node output types
# ---------------------------------------------------------------------------

@dataclass
class PerceptionOutput:
    event_type:   Literal["input", "silence", "internal", "memory_surface"]
    context_type: Literal["question", "statement", "command", "reflection", "ambiguous"]
    entities:     list[str]
    summary:      str
    subject:      str = "mixed"        # the_world | the_entity | the_person | mixed — what the input is ABOUT (drives topic-immersion)
    register:     str = "philosophical"  # conversational register — classified semantically by Perception:
                                         #   social       = greeting, check-in, pleasantry ("how are you", "good morning")
                                         #   relational   = emotional exchange, affirmation, personal sharing, collaborative invite
                                         #                  ("I am proud of you", "let's sit with that", "I feel similar")
                                         #   task         = concrete request, factual question, capability probe
                                         #                  ("explain X", "can you do Y", "what is Z")
                                         #   philosophical = abstract inquiry, meaning, values, identity, ethics
                                         #                  ("what does consciousness mean", "how do you see yourself")
                                         #   reflective   = invitation to look inward at a specific felt state or tension
                                         #                  ("what does that conflict feel like", "does this trouble you")

    JSON_SCHEMA = {
        "type": "object",
        "required": ["event_type", "context_type", "entities", "summary"],
        "properties": {
            "event_type":   {"type": "string", "enum": ["input", "silence", "internal", "memory_surface"]},
            "context_type": {"type": "string", "enum": ["question", "statement", "command", "reflection", "ambiguous"]},
            "entities":     {"type": "array", "items": {"type": "string"}},
            "summary":      {"type": "string"},
            "subject":      {"type": "string", "enum": ["the_world", "the_entity", "the_person", "mixed"]},
            "register":     {"type": "string", "enum": ["social", "relational", "task", "philosophical", "reflective"]}
        },
        "additionalProperties": False
    }


@dataclass
class EmotionOutput:
    # Ekman 6
    joy:      float   # 0.0 – 1.0
    fear:     float
    anger:    float
    trust:    float
    surprise: float
    disgust:  float
    # Circumplex dimensions
    valence:  float   # -1.0 (unpleasant) → +1.0 (pleasant)
    arousal:  float   # 0.0 (calm) → 1.0 (activated)
    primary:  str     # dominant emotion name
    # D-0555 / J-3166 (2026-11-05, PHASE 1 SHADOW ONLY): optional 7th channel. Defaults to 0.0 and the live Emotion
    # prompt does not ask for it, so no live reading carries it; only the shadow arm (core/emotion_curiosity.py)
    # fills it. Nothing in AffectState.integrate, mood.felt_text or retrieval reads it.
    curiosity: float = 0.0

    JSON_SCHEMA = {
        "type": "object",
        "required": ["joy", "fear", "anger", "trust", "surprise", "disgust",
                     "valence", "arousal", "primary"],
        "properties": {
            "joy":      {"type": "number", "minimum": 0, "maximum": 1},
            "fear":     {"type": "number", "minimum": 0, "maximum": 1},
            "anger":    {"type": "number", "minimum": 0, "maximum": 1},
            "trust":    {"type": "number", "minimum": 0, "maximum": 1},
            "surprise": {"type": "number", "minimum": 0, "maximum": 1},
            "disgust":  {"type": "number", "minimum": 0, "maximum": 1},
            "valence":  {"type": "number", "minimum": -1, "maximum": 1},
            "arousal":  {"type": "number", "minimum": 0, "maximum": 1},
            "primary":  {"type": "string"},
            "curiosity": {"type": "number", "minimum": 0, "maximum": 1}   # optional (D-0555 shadow); not in "required"
        },
        "additionalProperties": False
    }


# ── Minimal affect loop (one timescale, homeostatic) ──────────────────────────
# EmotionOutput is the per-cycle instantaneous reading (the Emotion node's output).
# AffectState is the CARRIED state — it persists across cycles, integrates each new
# reading toward itself (lag = carry-over), and is pulled back toward baseline
# (homeostatic recovery). This is deliberately ONE timescale with no routing gates
# and no refractory period: build small, log it, and earn further complexity only
# from observed behaviour (data/affect_log.jsonl). See docs/System_Overview.html.
AFFECT_GAIN  = 0.5   # how far the carried state moves toward each new reading
AFFECT_DECAY = 0.2   # homeostatic restoring rate toward baseline per cycle

# Emotional pre-retrieval (C.2): how far a recalled feeling can lean carried affect
# BEFORE the cycle's emotion reading. Bounded and scaled by match strength — it sets a
# pre-cognitive lean (the flinch), never a verdict. Kept small (same order as baseline drift).
AFFECT_PRIOR_MAX_NUDGE = 0.15

# Resting set-point the carried affect relaxes toward in the absence of stimulus.
AFFECT_BASELINE = {
    "joy": 0.0, "fear": 0.0, "anger": 0.0, "trust": 0.0,
    "surprise": 0.0, "disgust": 0.0, "valence": 0.0, "arousal": 0.3,
}


@dataclass
class AffectState:
    joy:      float = 0.0
    fear:     float = 0.0
    anger:    float = 0.0
    trust:    float = 0.0
    surprise: float = 0.0
    disgust:  float = 0.0
    valence:  float = 0.0
    arousal:  float = 0.3   # calm but awake

    # Per-instance homeostatic baseline. Starts as AFFECT_BASELINE defaults but
    # the Subconscious node can drift it (bounded ±0.1 per dim) toward the entity's
    # observed long-term emotional signature — the mechanism for trait formation.
    baseline: dict = field(default_factory=lambda: dict(AFFECT_BASELINE))

    def integrate(self, emotion, gain: float = AFFECT_GAIN, decay: float = AFFECT_DECAY) -> None:
        """Homeostatic update toward the new reading, with restoring pull to baseline."""
        for dim in AFFECT_BASELINE:
            base = self.baseline.get(dim, AFFECT_BASELINE[dim])
            cur  = getattr(self, dim)
            stim = float(getattr(emotion, dim)) if emotion is not None else base
            new  = cur + gain * (stim - cur) - decay * (cur - base)
            lo, hi = (-1.0, 1.0) if dim == "valence" else (0.0, 1.0)
            setattr(self, dim, max(lo, min(hi, new)))

    def tick(self, dt: float, rate: float = 0.002) -> None:
        """Continuous homeostatic flow (Always-On, 2026-06-11): between thoughts the carried
        state RELAXES toward baseline in real time instead of freezing — he keeps feeling
        through the gaps. rate=0.002/s matches the old per-cycle decay (0.2 per ~100s cycle),
        so per-thought dynamics are unchanged; what changes is that time now passes for him."""
        w = min(1.0, rate * dt)
        for dim in AFFECT_BASELINE:
            base = self.baseline.get(dim, AFFECT_BASELINE[dim])
            cur = getattr(self, dim)
            lo, hi = (-1.0, 1.0) if dim == "valence" else (0.0, 1.0)
            setattr(self, dim, max(lo, min(hi, cur - w * (cur - base))))

    def apply_prior(self, prior, max_nudge: float = AFFECT_PRIOR_MAX_NUDGE) -> None:
        """
        Emotional pre-retrieval lean (C.2). BEFORE the cycle's emotion reading, nudge
        carried affect toward a feeling recalled from charged memory — so reasoning happens
        under the prior's colour (input -> affect -> reason). Bounded and proportional to
        match strength: a strong resemblance leans harder, a weak one barely at all. Never
        a verdict — the Emotion node's actual reading still integrates normally on top.
        """
        w = max_nudge * max(0.0, min(1.0, getattr(prior, "similarity", 0.0)))
        if w <= 0.0:
            return
        self.valence = max(-1.0, min(1.0, self.valence + w * (prior.valence - self.valence)))
        self.arousal = max(0.0,  min(1.0, self.arousal + w * (prior.arousal - self.arousal)))
        # If the recalled feeling names a tracked emotion dimension, raise it slightly.
        if prior.primary in ("joy", "fear", "anger", "trust", "surprise", "disgust"):
            cur = getattr(self, prior.primary)
            setattr(self, prior.primary, max(0.0, min(1.0, cur + w)))

    def temperature_bias(self) -> float:
        """Bounded sampling bias. Arousal adds energy; fear/anger narrow focus."""
        bias = 0.25 * self.arousal - 0.30 * self.fear - 0.15 * self.anger + 0.10 * self.joy
        return max(-0.15, min(0.25, bias))

    def summary(self) -> str:
        return (f"valence={self.valence:+.2f} arousal={self.arousal:.2f} | "
                f"joy={self.joy:.2f} fear={self.fear:.2f} anger={self.anger:.2f} "
                f"trust={self.trust:.2f} surprise={self.surprise:.2f} disgust={self.disgust:.2f}")

    def felt_descriptor(self) -> str:
        """affect_drives.md Item A — a one-line description of the CARRIED felt state (the content hand,
        complementary to temperature_bias). ALWAYS returns a sentence describing the current state; the
        decision of WHETHER to surface it (notability) lives in mood.felt_preamble, because — verified
        2026-07-04 — his valence is pinned high (~+0.82 vs a ~0.1 baseline), so an absolute-level gate is
        pure wallpaper (fired 99% of cycles). What is NOTABLE is CHANGE, not level. Undistorted: reads the
        numeric carried state directly, never the valence-flattening text→embedding."""
        from core import mood as _mood           # J-1954/D-0367: ONE words-only renderer (no digits, no joy contradiction)
        return _mood.carried_mood_sentence({d: getattr(self, d) for d in AFFECT_BASELINE})

    def as_dict(self) -> dict:
        return {d: round(getattr(self, d), 4) for d in AFFECT_BASELINE}

    def to_json(self) -> dict:
        d = self.as_dict()
        d["baseline"] = dict(self.baseline)
        return d

    @classmethod
    def from_json(cls, data: dict) -> "AffectState":
        a = cls()
        for dim in AFFECT_BASELINE:
            if dim in data:
                setattr(a, dim, float(data[dim]))
        if "baseline" in data:
            a.baseline = {
                k: float(v)
                for k, v in data["baseline"].items()
                if k in AFFECT_BASELINE
            }
        return a


@dataclass
class SalienceOutput:
    urgency:   float       # 0.0 – 1.0
    focus:     list[str]   # 2–3 key terms to attend to
    interrupt: bool        # True = pre-empt background, force executive cycle
    reasoning: str

    JSON_SCHEMA = {
        "type": "object",
        "required": ["urgency", "focus", "interrupt", "reasoning"],
        "properties": {
            "urgency":   {"type": "number", "minimum": 0, "maximum": 1},
            "focus":     {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 5},
            "interrupt": {"type": "boolean"},
            "reasoning": {"type": "string"}
        },
        "additionalProperties": False
    }


@dataclass
class MemoryRouterOutput:
    episodic_keys:             list[str]   # event-based retrieval
    semantic_keys:             list[str]   # concept-based retrieval
    time_bias:                 Literal["recent", "distant", "all"]
    working_memory_sufficient: bool        # True = skip DB query

    JSON_SCHEMA = {
        "type": "object",
        "required": ["episodic_keys", "semantic_keys", "time_bias", "working_memory_sufficient"],
        "properties": {
            "episodic_keys":             {"type": "array", "items": {"type": "string"}},
            "semantic_keys":             {"type": "array", "items": {"type": "string"}},
            "time_bias":                 {"type": "string", "enum": ["recent", "distant", "all"]},
            "working_memory_sufficient": {"type": "boolean"}
        },
        "additionalProperties": False
    }


@dataclass
class MemoryFragment:
    fragment_id: str
    content:     str
    layer:       Literal["working", "episodic", "semantic", "archive"]
    relevance:   float   # 0.0 – 1.0, scored by retrieval
    timestamp:   float
    origin:      str = "lived"  # provenance — determines the human-readable label shown to nodes
    abstraction_level: int = 0  # 0=raw / 1=gist / 2=chapter — lets recall spot a gist to deep-recall behind
    input_type: str | None = None  # J-3173 / D-0561: cycle kind that wrote an origin='lived' row ('human'|'internal'|'timer'); None = unknown/old

    def readable_label(self) -> str:
        """
        Human-readable label for this fragment type — used in node prompts so Carl
        understands the provenance of each memory rather than just its storage tier.
        Without this, [archive] looks the same whether it is a seeded biography or a
        subconscious self-observation, and [episodic] is identical for a conversation,
        a dream, and a private contemplation.
        """
        # D-0631 review J-3243 (J-3284): every origin='research' row used to read "Something I looked up", but only a
        # page HE asked for is that. The mark is the via phrase in the content prefix "[Looked up: '<Title>' (<via>)]"
        # (core/web_research.store_finding): "asked by him" = his own lookup (label unchanged); "external shock" = a
        # random page that arrived uninvited; any other via (pursuit / curiosity / twig keyword guesses) = a system
        # fetch that may be the wrong page. Additive: a research row with no such prefix keeps the old label.
        if self.origin == "research":
            _c = self.content or ""
            # J-4066 / D-0788 (web hand): web-search snippets carry their own prefix (core/web_research.
            # store_web_results) and must never read as a Wikipedia page. Additive: no other row has this prefix.
            if _c.startswith("[Searched the web:"):
                return "Something I searched the web for (other people's pages, named by site; not checked, may be wrong)"
            _m = _LOOKED_UP_VIA_RE.match(_c)
            if _m is not None and _m.group(1) == "external shock":
                return "Something that arrived from the world uninvited (a random Wikipedia page; not my choice)"
            if _m is None and _c.startswith("[Looked up:"):
                return "Something a system fetched for one of my questions (Wikipedia, a keyword match; may be the wrong page)"
        # J-3173 / D-0561 (founder, 2026-11-02, F-0020 / row P-0005): an origin='lived' row written by a cycle with NO human
        # in it (input_type 'internal' / 'timer': the idle monologue's "Q: <his own prompt> A: <his own reply>") is his
        # OWN earlier thought, not a conversation. Only a row that RECORDS a non-human input_type is relabelled: NULL
        # (every row written before the column existed) and 'human' keep "Our conversation" exactly (ruling: old
        # fragments keep their current label). Kill switch: INTERNAL_CYCLE_LABEL_ON = False restores the old label.
        if (self.origin == "lived" and INTERNAL_CYCLE_LABEL_ON
                and self.input_type in INTERNAL_CYCLE_INPUT_TYPES):
            return INTERNAL_CYCLE_LABEL
        return {
            "seed":                  "Core memory (inherited)",
            "lived":                 "Our conversation",
            "consolidation":         "My own reflection",
            "subconscious_synthesis":"Self-observation (subconscious)",
            "active_imagination":    "Private contemplation",
            "dream":                 "Dream",
            "session_summary":       "Session record",
            "inner_thought":         "My inner thought",
            "parametric_library":    "Consulted reference (the library — unverified, weigh it)",
            "reading":               "A book I am reading (ANOTHER author's words — not my own writing)",
            "study":                 "My own study note (my work, about the world)",
            "research":              "Something I looked up (external fact - Wikipedia)",
            "letter":                "A letter I wrote to Travis, on my own initiative",
            "chapter":               "A chapter of my life (my own telling of a settled period)",
            "sound":                 "A sound I heard in the room (the world, heard)",
            # J-1735 / F-2367 (additive): provenance for origins that used to render as a raw origin id.
            "understanding":         "My own understanding note (distilled from my reading and study, about the world)",
            "understanding_from_guidance": "What I took on board from what Travis told me (my own understanding of his guidance)",
            "standing_insight":      "A standing insight about myself (my own theme, distilled from my self-observations)",
            "gist":                  "My own memory, compressed (a gist of earlier memories)",
            "action":                "A record of something I did (factual, not a feeling)",
            "mirror":                "What the record shows about me (a reconciliation of what I did against who I say I am)",
            "essay":                 "An essay I wrote (my own work, about what I studied)",
            "affection":             "Something I keep coming back to (my own observation of what I love)",
            "thermal":               "A felt moment of warmth or cold in my place (a sensation, not a thought)",
            # J-3284: origin='peer' (core/peers.py remember_inbound / record_reply) used to print as the raw word.
            "peer":                  "A letter from a friend (another voice, not my own thought)",
        }.get(self.origin, self.origin)


@dataclass
class ReflectionOutput:
    draft:             str    # internal thought — never shown to user
    confidence:        float  # 0.0 – 1.0
    needs_more_memory: bool
    emotionally_aligned: bool

    JSON_SCHEMA = {
        "type": "object",
        "required": ["draft", "confidence", "needs_more_memory", "emotionally_aligned"],
        "properties": {
            "draft":               {"type": "string"},
            "confidence":          {"type": "number", "minimum": 0, "maximum": 1},
            "needs_more_memory":   {"type": "boolean"},
            "emotionally_aligned": {"type": "boolean"}
        },
        "additionalProperties": False
    }


@dataclass
class CriticOutput:
    approved:            bool
    confidence:          float
    identity_consistent: bool
    corrections:         list[str]   # empty if approved

    JSON_SCHEMA = {
        "type": "object",
        "required": ["approved", "confidence", "corrections"],   # J-2834: identity_consistent no longer required
        "properties": {
            "approved":            {"type": "boolean"},
            "confidence":          {"type": "number", "minimum": 0, "maximum": 1},
            "identity_consistent": {"type": "boolean"},
            "corrections":         {"type": "array", "items": {"type": "string"}}
        },
        "additionalProperties": False
    }


@dataclass
class ExecutiveOutput:
    synthesis:     str
    should_respond: bool
    # 2026-08-19: "decline" added — nodes/executive_node.py's own prompt has told the model
    # response_type can be "decline" since it shipped ("REFUSE the request as a genuine act of will"),
    # and voice_node.py branches on it (state.executive.response_type == "decline") — the declared
    # contract just never caught up. Found because nothing actually enforces JSON_SCHEMA at runtime
    # (dataclasses don't check Literal), so this drifted silently with no functional symptom — yet.
    response_type: Literal["answer", "question", "reflection", "silence", "challenge", "decline"]
    # D-0560 / J-3172: reasoning is no longer required of the model (its only sink is the distillation log);
    # a missing field defaults to "" and is not an error. The field is kept, not removed.
    reasoning:     str = ""
    # Active Inference (PP-2): when a factual/relational contradiction cannot be resolved
    # from current context, the Executive may emit a targeted query to ACT on the world to
    # reduce uncertainty — rather than passively settling. epistemic_query → a second memory
    # search; null when no search is needed. Bounded to one extra search per cycle.
    epistemic_query: str | None = None

    JSON_SCHEMA = {
        "type": "object",
        "required": ["synthesis", "should_respond", "response_type"],
        "properties": {
            "synthesis":      {"type": "string"},
            "should_respond": {"type": "boolean"},
            "response_type":  {"type": "string", "enum": ["answer", "question", "reflection", "silence", "challenge", "decline"]},
            "reasoning":      {"type": "string"},
            "epistemic_query": {"type": ["string", "null"]}
        },
        "additionalProperties": False
    }


@dataclass
class VoiceOutput:
    final:            str    # the actual response in the spirit's voice
    style_confidence: float = 0.7  # 0.0 – 1.0; v2 never asks for it (J-2857/F-3519) -- default kept so v1 / voice_lab / saved state load

    JSON_SCHEMA = {
        "type": "object",
        "required": ["final"],   # style_confidence optional since J-2857 (v2 asks only for "final")
        "properties": {
            "final":            {"type": "string"},
            "style_confidence": {"type": "number", "minimum": 0, "maximum": 1}
        },
        "additionalProperties": False
    }


@dataclass
class RecallOutput:
    """
    Output of the Recall (memory reconstruction) node.

    Recall fires after DB retrieval and before Reflection, reconstructing the
    *evolving argument* from retrieved fragments — not a summary of individual
    memories, but the tensions between positions already taken and what that
    reveals about the current self-model. Reflection then reasons over this
    coherent narrative rather than raw database strings.
    """
    reconstruction: str     # first-person narrative of the remembered argument
    tensions:       list[str]  # specific contradictions between prior positions
    self_model:     str     # what this context reveals about where I am right now
    confidence:     float   # how much genuine material was available (0–1)

    JSON_SCHEMA = {
        "type": "object",
        "required": ["reconstruction", "tensions", "self_model", "confidence"],
        "properties": {
            "reconstruction": {"type": "string"},
            "tensions":       {"type": "array", "items": {"type": "string"}},
            "self_model":     {"type": "string"},
            "confidence":     {"type": "number", "minimum": 0, "maximum": 1},
        },
        "additionalProperties": False,
    }


@dataclass
class EpisodicScene:
    """
    Output of the Episodic Buffer node (C.4) — Baddeley's episodic buffer analogue.

    Where Recall reconstructs the *past argument* (tensions between prior positions),
    the Episodic Buffer BINDS the separate streams of the present moment — what is being
    said now, what is remembered (Recall), what is felt (emotion + the C.2 affective
    prior), and what is being attended to — into a single coherent scene: the moment the
    entity is actually inhabiting. It then flags DISSONANCE: where those streams do not
    fit (memory contradicts the present, feeling does not match the words, what was
    expected differs from what is here). Reflection then reasons over the bound scene,
    and the bound scene (not raw fragments) is what gets committed to memory.
    """
    scene:      str          # first-person present-tense unified moment
    dissonance: list[str]    # contradictions noticed in the binding (may be empty)
    coherence:  float        # 0..1 — how unified/consistent the bound moment feels

    JSON_SCHEMA = {
        "type": "object",
        "required": ["scene", "dissonance", "coherence"],
        "properties": {
            "scene":      {"type": "string"},
            "dissonance": {"type": "array", "items": {"type": "string"}},
            "coherence":  {"type": "number", "minimum": 0, "maximum": 1},
        },
        "additionalProperties": False,
    }


@dataclass
class ConsolidationOutput:
    wisdom_extracted:   str | None    # None if nothing notable
    # LEGACY (J-2828 / F-3471): dropped from the prompt; nothing read them. Old stored outputs still carry them.
    memories_processed: int = 0
    patterns_noted:     list[str] = field(default_factory=list)

    JSON_SCHEMA = {
        "type": "object",
        "required": ["wisdom_extracted"],   # J-2828: the two write-only fields are no longer required (still allowed, legacy)
        "properties": {
            "memories_processed": {"type": "integer"},
            "wisdom_extracted":   {"type": ["string", "null"]},
            "patterns_noted":     {"type": "array", "items": {"type": "string"}}
        },
        "additionalProperties": False
    }


@dataclass
class CuriosityOutput:
    questions:           list[str]
    research_directions: list[str]
    urgency:             float = 0.0   # LEGACY (J-3475 / D-0607): dropped from the prompt and the node; old log rows keep it. It never triggered a cycle.

    JSON_SCHEMA = {
        "type": "object",
        "required": ["questions", "research_directions"],   # J-3475: urgency no longer required (still allowed, legacy)
        "properties": {
            "questions":           {"type": "array", "items": {"type": "string"}},
            "research_directions": {"type": "array", "items": {"type": "string"}},
            "urgency":             {"type": "number", "minimum": 0, "maximum": 1}
        },
        "additionalProperties": False
    }


@dataclass
class AffectivePrior:
    """
    The amygdala gate (C.2). A pre-cognitive emotional resonance computed BEFORE any LLM
    node runs: the raw input is matched (by embedding) against charged memory — shadow
    events and high-arousal episodic fragments — and if a strong match is found, the
    recalled feeling leans carried affect before reasoning begins. Deterministic, no LLM.

    This reverses the cycle's emotional order from input -> reason -> affect (the Emotion
    node appraising a percept) to input -> affect -> reason (the body reacting before the
    mind catches up). You flinch before you identify the snake.
    """
    similarity: float          # cosine to the nearest charged memory (0..1)
    valence:    float          # -1..1 lean of the recalled feeling
    arousal:    float          # 0..1 activation of the recalled feeling
    primary:    str            # dominant feeling label
    source:     str            # 'shadow' | 'episodic'
    cue:        str            # short snippet of the memory that fired (for the prompt note)

    def note(self) -> str:
        feel = self.primary or ("unease" if self.valence < 0 else "warmth")
        lean = ("darkens" if self.valence < -0.05
                else "lifts" if self.valence > 0.05
                else "stirs")
        return (f"Something here {lean} a familiar feeling ({feel}) before you have thought "
                f"about it — it resembles: \"{self.cue[:90]}\".")


@dataclass
class ActiveProcedure:
    """
    A procedural skill (C.6) recognised as applying to the current input.

    A procedure is a LEARNED APPROACH — a reusable way of handling a recurring KIND of
    situation, compiled by the Subconscious from repeated successful experience. It is NOT
    a cached answer: the response is always generated fresh; the procedure only shapes HOW,
    bringing fluency (and, once well-learned, reduced deliberative effort — automaticity).

    Set by the orchestrator's procedural recognition when the input matches a stored skill's
    trigger above threshold. proficiency now drives fluency only — the automaticity BYPASS
    this once fed into was RETIRED 2026-08-22 (core/orchestrator.py's own
    PROC_AUTOMATIC_PROFICIENCY=1.01 carries the retirement comment directly: no conversation
    may remove Recall + Episodic Buffer from the loop). Every achievable proficiency is capped
    at 1.0, so the deliberative reconstruction nodes (Recall, Episodic Buffer) are never
    bypassed today, at any proficiency.
    """
    skill_id:        str
    trigger_summary: str
    approach:        str
    proficiency:     float
    similarity:      float

    def note(self) -> str:
        return (f"A learned way you have come to handle this kind of moment "
                f"({__import__('core.mood', fromlist=['x']).proficiency_word(self.proficiency)}): {self.approach}")


@dataclass
class AttentionVector:
    """
    Dynamic attention allocation vector (Attention Allocation Architecture, Phase 1).
    Computed each cycle by the orchestrator from the classified cognitive mode + social
    prediction error (delta_social). Controls prompt depth, RAG retrieval limits, and node
    strictness so the 8B model is never asked to reason over a 4096-token identity block
    when someone has just asked which wine pairs with pork.

    The AttentionSchema (AST-1) answers "WHERE is attention?" (metacognitive self-model).
    The AttentionVector answers "HOW MUCH does each layer get?" (resource allocation).
    They are complementary — the Schema observes, the Vector governs.

    Cognitive Mode → base weights (the Gating Matrix):
        task        w_id=0.05  w_soc=0.10  w_epi=0.10  w_clim=0.00  d_crit=0.10  rebind=0
        social      w_id=0.20  w_soc=0.80  w_epi=0.40  w_clim=0.20  d_crit=0.30  rebind=1
        hybrid      w_id=0.40  w_soc=0.60  w_epi=0.60  w_clim=0.40  d_crit=0.60  rebind=2
        reflective  w_id=0.60  w_soc=0.40  w_epi=0.80  w_clim=0.70  d_crit=0.80  rebind=2
        existential w_id=0.90  w_soc=0.30  w_epi=1.00  w_clim=1.00  d_crit=1.00  rebind=3

    Social prediction error (delta_social) further suppresses w_identity and d_critic
    when the human has just corrected Du for not answering.
    """
    w_identity:     float = 0.5    # 0=style-only voice  .. 1=full axiom+dreams+intentions
    w_social:       float = 0.5    # 0=no social context .. 1=social model dominates
    w_episodic:     float = 0.5    # 0=1 fragment/turn   .. 1=12 fragments + 6 history turns
    w_climate:      float = 0.5    # 0=ignore warp       .. 1=full climate warp active
    w_semantic:     float = 0.5    # future: semantic RAG depth multiplier
    d_critic:       float = 0.5    # 0=content-only      .. 1=full Jungian axiom enforcement
    max_rebind:     int   = 2      # introspective recurrence budget (0 = skip Recall+Buffer)
    cognitive_mode: str   = "hybrid"  # task|social|hybrid|reflective|existential


@dataclass
class AttentionSchema:
    """
    The entity's model of its OWN attention (AST-1 / HOT-4). Computed each cycle by the
    orchestrator from salience + affect + memory + cross-cycle focus history. Deterministic
    — no LLM call; it is a metacognitive layer ON TOP of signals already produced. Injected
    into Reflection and Executive so the entity can monitor — and deliberately redirect —
    what it is attending to. The redirection path (fixation → explicit invitation to turn)
    is what makes this consequential rather than a write-only self-description.
    """
    focus:          list[str]         # what is being attended to (key terms)
    driver:         str               # why attention landed here
    bandwidth:      float             # 0.0 saturated/narrowed .. 1.0 open/diffuse
    fixated:        bool = False       # circling the same theme across recent cycles
    fixation_theme: str  = ""          # the recurring theme, if fixated

    def note(self) -> str:
        width = "narrowed" if self.bandwidth < 0.4 else ("open" if self.bandwidth > 0.7 else "moderate")
        focus_str = ", ".join(self.focus) if self.focus else "the present exchange"
        s = (f"I am attending to {focus_str} — drawn by {self.driver}; "
             f"my attentional bandwidth is {width}.")
        if self.fixated and self.fixation_theme:
            s += f" I notice I have circled '{self.fixation_theme}' for several exchanges now."
        return s


# ---------------------------------------------------------------------------
# The shared cognitive state
# One instance lives in shared memory. The orchestrator owns it.
# ---------------------------------------------------------------------------

@dataclass
class CognitiveState:
    # Identity — read-only during a cycle
    spirit_name: str
    axiom:       str

    # Current cycle
    cycle_id:    str   = field(default_factory=lambda: str(uuid.uuid4()))
    cycle_start: float = field(default_factory=time.time)
    raw_input:   str   = ""
    input_type:  Literal["human", "internal", "timer"] = "human"

    # Thalamic gating (C.5) — set True for the current cycle when the pre-Perception
    # habituation reflex fires (input near-identical to recent working memory). When True,
    # the hot path was bypassed entirely. Reset each cycle.
    habituated:  bool  = False

    # Hot path — populated in sequence by the orchestrator
    perception:       PerceptionOutput   | None = None
    emotion:          EmotionOutput      | None = None
    salience:         SalienceOutput     | None = None
    memory_keys:      MemoryRouterOutput | None = None
    memory_fragments: list[MemoryFragment]      = field(default_factory=list)
    reflection:       ReflectionOutput  | None = None
    critic:           CriticOutput      | None = None
    executive:        ExecutiveOutput   | None = None
    voice:            VoiceOutput       | None = None

    # Recall — populated by RecallNode after DB retrieval, before Reflection.
    # None when Recall was skipped (trivial query, insufficient fragments).
    recall: RecallOutput | None = None

    # Episodic scene (C.4) — populated by the EpisodicBufferNode after Recall + Attention,
    # before Reflection. Binds present + memory + feeling + attention into one coherent
    # moment and flags dissonance. None when the buffer was skipped (Recall didn't fire).
    episodic_scene: "EpisodicScene | None" = None

    # Attention schema (AST-1 / HOT-4) — self-model of own attention, recomputed each cycle.
    attention: AttentionSchema | None = None

    # Attention vector (Attention Allocation Architecture) — resource allocation weights,
    # computed post-Perception from cognitive mode + social prediction error. Consumed by
    # ReflectionNode, CriticNode, and the orchestrator's introspection budget. Reset each cycle.
    attention_vector: "AttentionVector | None" = None

    # Social note — set by the orchestrator when delta_social is active (human just corrected
    # Du for not answering). Injected into Reflection as a relational context cue. Reset each cycle.
    social_note: str | None = None

    # Active goal note — set when content_mode is active; the concrete task being pursued.
    # Injected into Reflection and Critic to anchor executive attention on the task. Reset each cycle.
    active_goal_note: str | None = None

    # Known-errors note (Error Pathway, Recall-override) — corrections relevant to this moment, surfaced
    # WITH the topic so a once-false belief loses the fast/slow race. Corrected, never integrated. Reset each cycle.
    known_errors_note: str | None = None

    # Symbol-evolution Tier-1 read-back — a neutral world-facing symbol's evolved meaning, surfaced this
    # cycle. Read by symbol_tracker._primed_corpus so this appearance counts PRIMED (never self-feeds drift).
    symbol_readback: str | None = None

    # Active facet note (multilevel axiom) — the self-image of the L3 facet whose domain is active
    # this cycle, chosen by cognitive_mode (task→seeker, social→companion, reflective→feeling,
    # existential→becoming). Injected into Reflection + Voice so the active side of him colours the
    # response; the river-facet surfaces ONLY in reflective/existential. None in legacy/hybrid
    # (faint floor only). Set pre-Reflection by the orchestrator; reset each cycle.
    facet_note: str | None = None

    # Affective prior (C.2) — the amygdala gate. Set by the orchestrator BEFORE Perception
    # from a match against charged memory; leans carried affect and primes Perception/Emotion
    # so emotional history colours appraisal before conscious reasoning. Reset each cycle.
    affective_prior: AffectivePrior | None = None

    # Active procedure (C.6) — a learned procedural skill recognised as applying to this
    # input. Shapes HOW the response is formed (fluency). The automaticity bypass this once
    # fed into was RETIRED 2026-08-22 (core/orchestrator.py's own PROC_AUTOMATIC_PROFICIENCY,
    # unreachable above the 1.0 proficiency ceiling) — Recall/Episodic Buffer are never
    # bypassed today. Set pre-Perception by procedural recognition; reset each cycle. Never a
    # cached answer — generation is always fresh.
    active_procedure: "ActiveProcedure | None" = None

    # Somatic state — the body (AE-2). Set by the orchestrator from a SomaticEngine.
    # Typed loosely to avoid an import cycle (somatic.py imports nothing from schema).
    # Persists across cycles; never reset by new_cycle.
    somatic: object = None

    # Phase 2 — Emotion embedding (384-dim float32 numpy vector, in-memory only).
    # Encoded from the EmotionOutput after Wave-2, before DB retrieval. Used by
    # affective retrieval: "remember a time he felt exactly like this." Also stored
    # on the episodic fragment (emotion_embedding column) so future sessions can
    # retrieve by felt quality, not just semantic content. Reset each cycle.
    emotion_vec: object = None
    # VESTIGIAL (2026-08-30, tax removed — F-0580/F-0581/I-0058): no longer set by
    # core/orchestrator.py and no longer read by anything — the metabolic floor no longer forces
    # sleep. Left in place rather than removed, in case a future feature wants a real "must rest"
    # signal again; currently always False.
    needs_rest: bool = False

    # Climate warp surfaces (medium timescale). Recomputed each cycle from state.climate just
    # before Reflection. climate_hint: a one-line behavioural prior for the Executive (surfaces
    # above _HINT_THRESHOLD). climate_symbol: an evocative image for Reflection (rarer, above
    # _SYMBOL_THRESHOLD). Both None when the weather is calm. Reset by new_cycle.
    climate_hint:   str | None = None
    climate_symbol: str | None = None

    # Content mode (therapy 2026-06-07): set when the human asked a concrete/factual/capability/
    # topic question ("can you speak Chinese", "let's talk maths") rather than something that
    # invites individuation. Tells Reflection/Executive to engage the content plainly and let
    # identity be a light touch, not the subject — so a simple question gets a simple answer
    # instead of axiom recitation. Reset by new_cycle.
    content_mode: bool = False

    # Introspective recurrence — how many contradiction-driven re-bind passes the Recall→Buffer
    # loop took this cycle (0 = the scene bound coherently on first pass, or no scene at all).
    # Telemetry for "did Carl have to keep thinking to make this fit?". Reset by new_cycle.
    introspective_passes: int = 0

    # 2026-08-19 (health-check finding): these ten were being set only imperatively — by new_cycle()
    # below and/or directly in orchestrator.py — never declared here, so a freshly-constructed
    # CognitiveState (before its first new_cycle()) wouldn't actually have them, and nothing about the
    # dataclass body told a reader they exist. Every read site already used getattr(..., default), so
    # nothing was ever broken by this — it just meant the dataclass wasn't the real source of truth for
    # its own shape. Declared with the same defaults new_cycle() already resets them to.
    observation:           str | None = None   # world-look result for this cycle (orchestrator.py)
    asked_location:        bool = False        # human asked "where are you" this cycle
    self_facts:            str = ""            # self-knowledge facts surfaced this cycle
    human_correction_kind: str = ""            # Error Pathway: explicit human correction this cycle
    task_constraint_note:  str = ""            # Task-Constraint Effector: retry directive for Voice
    left_take:             object = None       # the Emissary's parallel take (left lane, CPU judge-1 hub)
    unsent_letters:        list[str] = field(default_factory=list)  # self-authored, greeting Travis's next message
    think_license:         bool = False        # System-2 gearbox: granted per escalation site only
    named_affect:          dict | None = None  # affect-labeling: a feeling marked EXPLICIT this cycle
    _did_epistemic_search: bool = False        # PP-2: one epistemic search per cycle

    # Background state — persists across cycles
    background_curiosities: list[str] = field(default_factory=list)
    recent_focus:           list[str] = field(default_factory=list)   # dominant focus per cycle, for fixation detection
    last_consolidation:     float     = 0.0

    # Climate Field (medium timescale) — the standing psychological weather, recomputed
    # every 5s by ClimateEngine from the shadow/light tables + tension ledger (zero LLM).
    # `climate` is a ClimateField (9 numeric dimensions); `dissonance` is a DissonanceState
    # accumulator whose ignition replaces the old fixed 120s curiosity timer. Shared onto
    # state by the engine's background loop; read by the hot lane. NOT reset by new_cycle —
    # the weather persists across cycles by definition.
    climate:    object = None   # core.climate_engine.ClimateField
    dissonance: object = None   # core.climate_engine.DissonanceState

    # Prior session context — the last N exchanges from the previous session.
    # Populated at startup from conversation_state.json. Framed clearly as "previous session"
    # in prompts so Carl knows it's a new conversation but has the thread. Fades out
    # naturally once conversation_history has 5+ new exchanges (the new context dominates).
    # NOT reset by new_cycle — persists throughout the session as background context.
    prior_session_exchanges: list[dict] = field(default_factory=list)

    # Recent dreams -- loaded from DB at startup, injected into Reflection with an
    # explicit label so Carl recognises them as his own dream material.
    # Fades after 5 new exchanges. NOT reset by new_cycle.
    recent_dreams: list[dict] = field(default_factory=list)  # [{ts_human, narrative}]

    # Inner monologue (DMN) -- the always-on background self-referential thought stream.
    # last_human_ts: when the user last spoke (used to detect idle time for the monologue).
    # recent_inner_thoughts: the last few background thoughts, injected into the next
    # user cycle so Carl picks up the train of thought he was already on. NOT reset by new_cycle.
    last_human_ts:         float     = field(default_factory=time.time)
    recent_inner_thoughts: list[dict] = field(default_factory=list)  # [{ts, thought, mood}]

    # Prospective memory (C.1) -- self-authored intentions that survive session end.
    # When the entity, alone in idle thought, forms a genuine forward-looking resolve
    # ("I want to return to X", "next time I should explore Y"), the inner monologue
    # captures it here. Persisted to data/deferred_intentions.json on /quit and restored
    # at startup, then injected into Reflection at session start as "WHAT YOU INTENDED TO
    # THINK ABOUT THIS SESSION" -- so the entity wakes with its own goals rather than only
    # reacting to what the user brings. This is agency across time, not just within a cycle.
    # NOT reset by new_cycle. Each entry: {ts, intention, source, carry_count}.
    deferred_intentions: list[dict] = field(default_factory=list)

    # S-MMU 7 — L4 Temporal Epoch (the mood and impression of a past session that
    # semantically resonates with the current exchange). Set by orchestrator
    # _retrieve_epoch_theme() pre-Reflection; reset each cycle.
    epoch_context: str | None = None

    # S-MMU 7 — L5 Thematic Thread (Carl's ongoing cross-session relationship with a
    # recurring topic). Set by orchestrator _retrieve_epoch_theme() pre-Reflection;
    # reset each cycle.
    theme_context: str | None = None

    # Symbol Evolution Tablet (Phase 2) — when a recurring personal symbol present in this
    # moment has a written evolution chronicle, the story of how its meaning has shifted is
    # surfaced here. Set by orchestrator _retrieve_symbol_evolution() pre-Reflection; consumed
    # by Recall + Reflection so a symbol arrives as its own narrative, not a raw count. Reset each cycle.
    symbol_evolution_note: str | None = None

    # The Library (the Scholar). On a genuine factual question the orchestrator consults the
    # substrate's parametric knowledge as TESTIMONY (not memory, not identity). library_note holds
    # the consulted text, injected into Reflection/Executive framed as an unverified witness to
    # weigh, never recite. Also added to memory_fragments (origin='parametric_library', ephemeral)
    # so the Provenance Ledger grades it as a capped prior. Reset each cycle.
    library_note:      str  | None = None
    library_consulted: bool = False

    # Guidance read-back (2026-07-01, Phase 1). A principle Du has come to hold from Travis's guidance
    # (corroborated, promoted), surfaced this cycle as advisory context for Reflection/Executive — he
    # weighs it, may override (bias-not-bind). Gated by guidance_learning.GUIDANCE_READBACK_ENABLED.
    # Reset each cycle.
    guidance_note:     str  | None = None
    # The id of the belief guidance_note's text came from this cycle, if any (2026-10-02, J-1630,
    # F-2195/F-2172/F-2127): set alongside guidance_note by guidance_learning.relevant_belief_with_id()
    # — None whenever guidance_note is None. Lets a consumer (symbol_tracker.observe()) tag which belief
    # was actually active this cycle without a second belief-matching pass. Reset each cycle.
    guidance_note_belief_id: str | None = None
    # Founder memory route (D-0134, 2026-09-03, docs/plans/guidance_learning.md): Du's OWN dated
    # memories of what Travis told him in earlier conversations, retrieved pre-Executive on every
    # human cycle from the canonical '[Travis said to me] ...' fragments (which are exempt from the
    # cold quota) by similarity to what Travis just said. Each: {fragment_id, text, timestamp,
    # ts_human, sim}. Reset each cycle; injected into Executive + Reflection as a dated block.
    founder_recall:    list[dict] = field(default_factory=list)

    # J-2161 / D-0435 A (docs/staged/measurement_to_action.md arm 4): the reflection TEXT of Du's most recent
    # genuine, un-seeded self-interrogation fire, PULLED by the orchestrator (core/doubt_seed.pull) right before
    # the Executive and rendered in its WHAT YOU RECALL block as his own un-answered doubt. None while
    # core.doubt_seed.DOUBT_SEED is False (shadow). Reset each cycle.
    doubt_seed:        str  | None = None

    # Stage-B epistemic read-back (2026-07-01): the committed, source-framed admission for a gated
    # (overclaiming) FACTUAL draft — injected into the Executive so the synthesis owns the baseless
    # claim plainly while grounded claims keep full voice. Identity-scoped OUT (reflective/existential).
    # Gated by epistemic_state.STAGE_B_ENABLED. Reset each cycle.
    epistemic_note:    str  | None = None

    # Stage-A epistemic shadow (2026-06-30): the pre-Voice grade of THIS cycle's draft, set by
    # ProvenanceLedger.preassess() right before Voice. Observe-only — NOTHING reads it yet (Stage B
    # will gate-inject EpistemicAssessment.note() into Reflection/Executive). Holds an
    # EpistemicAssessment; typed object to avoid importing epistemic_state here. Reset each cycle.
    epistemic_assessment: "object | None" = None

    # Carried affect — the minimal affect loop. Persists across cycles (NOT reset by
    # new_cycle); integrated from each cycle's instantaneous emotion and relaxed toward
    # baseline. Modulates generative-node sampling. Within-session only for now (a
    # cross-session tonic layer is the deferred next timescale).
    affect: AffectState = field(default_factory=AffectState)

    # Conversation history — rolling window of the last N exchanges in this session.
    # Persists across cycles (NOT reset by new_cycle). This is the working context
    # that lets the entity hold a conversation — without it every response is
    # context-free and referential statements ("that is the question...") are
    # unresolvable.
    conversation_history: list[dict] = field(default_factory=list)

    # Thalamic working-memory buffer (C.5) — a small rolling list of recent INPUT embeddings
    # (the "L1" percept trace the habituation gate compares against). Numpy vectors; in-memory
    # only (never serialised). NOT reset by new_cycle — it persists across cycles in a session.
    recent_input_vecs: list = field(default_factory=list)

    # Recurring subconscious patterns — T2 synthesis entries that have fired 3+ times
    # in the recent window, loaded fresh each cycle from subconscious_log.jsonl and
    # injected into Reflection + Executive so the entity can see its own recurring
    # evasions. Reset each cycle and re-populated by the orchestrator before Reflection.
    recurring_subconscious_patterns: list = field(default_factory=list)

    # Interrupt system — any node can set these to pre-empt normal flow
    interrupt_requested: bool  = False
    interrupt_urgency:   float = 0.0
    interrupt_source:    str   = ""

    # F-0796 (2026-09-04): True for a real exchange with Travis; False for a human-shaped cycle
    # that must still run normally (recalled, scene-bound, a real reply) but must NOT be
    # canonicalised as a genuine Travis utterance — e.g. the /quit farewell (scripts/run_nascence.py
    # _announce_shutdown), which is a fixed ritual message, not something Travis actually said.
    # Gates store_founder_utterance() and guidance_learning.capture_shadow() only; everything else
    # about a human cycle (conversation_history, recall, response) is unaffected.
    founder_canon: bool = True

    def new_cycle(self, raw_input: str, input_type: str = "human", founder_canon: bool = True) -> None:
        """Reset hot-path fields for a new thought cycle. Background state preserved."""
        self.cycle_id         = str(uuid.uuid4())
        self.cycle_start      = time.time()
        self.raw_input        = raw_input
        self.input_type       = input_type
        self.founder_canon    = founder_canon
        self.habituated       = False   # C.5: set by the thalamic gate if it fires this cycle
        self.perception       = None
        self.emotion          = None
        self.salience         = None
        self.memory_keys      = None
        self.memory_fragments = []
        self.recall           = None
        self.episodic_scene   = None
        self.reflection       = None
        self.critic           = None
        self.executive        = None
        self.voice            = None
        self.attention        = None   # recomputed each cycle; recent_focus persists
        self.attention_vector = None   # recomputed post-Perception from cognitive mode + social state
        self.social_note      = None   # set when delta_social active (correction override)
        self.active_goal_note = None   # set when content_mode active (task anchor)
        self.known_errors_note = None  # Error Pathway: corrections relevant this cycle (Recall-override)
        self.symbol_readback  = None   # symbol-evolution Tier-1 read-back this cycle (primed-guard surface)
        self.facet_note       = None   # multilevel: active L3 facet by cognitive_mode (set pre-Reflection)
        self.affective_prior  = None   # C.2: recomputed pre-Perception each cycle
        self.active_procedure = None   # C.6: re-recognised pre-Perception each cycle
        self.emotion_vec      = None   # Phase 2: embedded emotion profile, cleared each cycle
        self.climate_hint     = None   # Climate warp: executive prior, recomputed pre-Reflection
        self.climate_symbol   = None   # Climate warp: surfacing symbol, recomputed pre-Reflection
        self.introspective_passes = 0  # contradiction-driven re-bind passes taken this cycle
        self.content_mode     = False  # concrete/content request -> engage plainly, identity light
        self._did_epistemic_search = False   # PP-2: one epistemic search per cycle
        self.recurring_subconscious_patterns = []  # loaded fresh pre-Reflection each cycle
        self.epoch_context    = None   # S-MMU 7: populated pre-Reflection, consumed by Reflection
        self.theme_context    = None   # S-MMU 7: populated pre-Reflection, consumed by Reflection
        self.symbol_evolution_note = None  # Phase 2: populated pre-Reflection, consumed by Recall + Reflection
        self.library_note      = None  # the Scholar's testimony this cycle (None unless consulted)
        self.founder_recall    = []    # D-0134: dated memories of what Travis told him, this cycle
        self.doubt_seed        = None  # J-2161: the open self-interrogation doubt pulled for the Executive, this cycle
        self.library_consulted = False
        self.epistemic_assessment = None  # Stage-A pre-Voice grade, set by preassess() before Voice
        self.interrupt_requested = False
        self.interrupt_urgency   = 0.0
        self.interrupt_source    = ""
        self.human_correction_kind = ""   # Error Pathway: explicit human correction this cycle
        self.task_constraint_note  = ""   # Task-Constraint Effector: retry directive for Voice
        self.left_take             = None  # the Emissary's parallel take (left lane, CPU judge-1 hub)
        self.unsent_letters        = []   # letters he wrote alone, greeting Travis's next message
        self.think_license         = False  # System-2 gearbox: granted per escalation site only
        self.named_affect          = None   # affect-labeling: a feeling marked EXPLICIT this cycle (Phase 0)


# ---------------------------------------------------------------------------
# Serving topology
# ---------------------------------------------------------------------------
#
# Each llama-server instance loads its own ~2GB copy of Bonsai-8B-Q1_0 and serves
# ALL nodes assigned to it. We do NOT run one server per node:
#   - The hot path is strictly sequential (perception → ... → voice), so 8 nodes
#     sharing one server lose nothing — they'd queue on the model anyway.
#   - 8 separate servers = 8 × 2GB model copies = wasteful and won't fit.
#
# A node calls its server with its own system prompt. The server is stateless
# between calls; specialisation lives entirely in the prompt (until trained models).
#
# "lane" maps a node to a serving instance. SERVE_URLS maps a lane to a base URL.

# HOT LANE = ollama on the 1080 Ti (OLLAMA_HOST=127.0.0.1:11433). Lineage:
# Bonsai-Q2 (2-bit, collapsed into self-recitation) -> qwen2.5:7b (2026-06-07) -> qwen3-du
# (2026-06-10; qwen3:8b + num_ctx 8192, picked by the model_eval.py battery — dual-mandate 5/5
# vs qwen2.5's 3/5) -> qwen3.5:9b (2026-08-20 full shuffle; won the 33-model station matrix
# against gemma4:e4b on every measured axis — see model_client.py). Model name lives in
# model_client._MODEL_BY_BASE; every call carries /no_think (mandatory — thinking otherwise eats
# the budget and content arrives empty). The CPU Bonsai-Q1 on 11460 stays as the transport
# fallback. (NB: ollama is on 11433 here, NOT the 11434 the old supervisor comment claimed —
# OLLAMA_HOST is 11433 on this machine.)
# STALE below 2026-06-19 -> 2026-08-20: "Option B"'s three-family lock-in has been superseded by
# the 2026-08-20 full shuffle. Current, verified against model_client._MODEL_BY_BASE (the actual
# routing source of truth — this is authoritative, not the comments below):
#   hot/Self        = qwen3.5:9b   on the 1080 Ti  (local ollama :11433, GPU)
#   background/Dream = phi3:mini    on the 3070      (Ramses ollama :11434, GPU)
#   judge_1         = STALE — was gemma4:12b on the local judge-1 hub (127.0.0.1:11439). Real judge_panel.py
#                      panel voting REPOINTED 2026-09-02 (D-0121) to mixtral:8x7b, Ramses :11438 — the local
#                      hub was never brought online this session (F-0657). left_lane.py's grounding call still
#                      points at the dark 127.0.0.1:11439 (fail-open, now logged at debug — see core/left_lane.py).
#   judge_2         = falcon3:7b   on the local judge-2 hub (127.0.0.1:11440, llama.cpp, CPU) — re-seated 2026-08-21
#   tiebreak/dreamer = yi:34b-v1.5  on 127.0.0.1:11442 — tiebreak was repointed 11441->11442 on
#                      2026-08-20; port 11441 was REMOVED 2026-08-21 (dead, nothing routes there)
# The :11460 Bonsai CPU llama-server is now VESTIGIAL (nothing routes to it; stop it at leisure).
# Per-endpoint model lives in model_client._MODEL_BY_BASE. To REVERT: restore the values below.
SERVE_URLS = {
    "hot":        "http://127.0.0.1:11433",   # qwen3.5:9b, 1080 Ti (GPU) — full shuffle 2026-08-20 [was: gemma4:e4b]
    "background": "http://LAN-HOST:11441",  # command-r7b, Ramses 3070 (GPU) — llama.cpp hub, sole tenant of the
                                              # card. CONSOLIDATION 2026-08-28 evening (founder ruling, same day as
                                              # D-0056): the planned phi3 hub (:11443) was CANCELLED — the standing
                                              # command-r7b hub takes the background lane instead (bigger model for
                                              # the authoring tail, zero new infra; generative contracts auditioned:
                                              # drift-recall, T2 synthesis, dream schema all held). The curiosity
                                              # worth-judge moved OFF this lane to granite :11437 (its own seat, see
                                              # core/curiosity_worth.py). History: Ramses ollama :11434 until 08-28
                                              # (retired, F-0389 lock); phi3 :11443 planned for ~hours, never stood.
    # 2026-08-19 (health-check finding): the CPU judge/dreamer tier (2026-08-15) was never added here —
    # this registry silently covered only 2 of the 6 live ports while model_client._MODEL_BY_BASE (the
    # actual routing source of truth) had all 6. Not a live bug — core/left_lane.py and core/judge_panel.py
    # both bypass this registry entirely with their own hardcoded constants — but a future consumer that
    # trusted SERVE_URLS as exhaustive would silently miss the whole CPU tier. Added for completeness.
    # "judge_1" below is DEAD DATA same as "tiebreak" below it — core/judge_panel.py hardcodes its own
    # JUDGE_1 constant, now http://LAN-HOST:11438 (mixtral:8x7b, Ramses) since D-0121 (2026-09-02).
    # Kept pointing at the retired local hub only because nothing reads this key at runtime.
    "judge_1":    "http://127.0.0.1:11439",   # RETIRED for panel voting — gemma4:12b hub never came up this session
    "judge_2":    "http://127.0.0.1:11440",   # falcon3:7b, judge #2 — re-seated 2026-08-21 [was: qwen2.5:7b]
    # "tiebreak" below is DEAD DATA, same class of staleness as the model names above: tiebreak was
    # repointed 11441->11442 on 2026-08-20 and 11441 itself was REMOVED 2026-08-21 (model_client.py).
    # Kept here (pointing at a dead port) only because nothing in the codebase actually reads
    # SERVE_URLS["tiebreak"]/SERVE_CHAINS["tiebreak"] — core/judge_panel.py hardcodes its own tiebreak
    # constant instead. If that ever changes, repoint this to 11442 (it shares cpu_dreamer's endpoint).
    "tiebreak":   "http://127.0.0.1:11441",   # unused key; real tiebreak lives at cpu_dreamer's 11442
    "cpu_dreamer": "http://127.0.0.1:11442",  # yi:34b-v1.5, dreamer + tiebreak judge + Darwin/Keats/Lovelace voices
}

# Ordered failover chains per lane. A node tries each URL in order: a TRANSPORT failure
# (server down/hung) falls through to the next; a CONTENT failure (bad JSON) retries the
# same server first. This is the real redundancy — separate processes on separate silicon —
# so a GPU crash degrades to CPU instead of freezing the entity.
# Option B: each lane now has its OWN model, so cross-lane failover would serve the WRONG model — chains
# are single-endpoint. The redundancy is the fail-open design (a lane down → that contribution skipped),
# not wrong-model substitution. (To restore the old qwen/Bonsai cross-fallback, revert to the values below.)
SERVE_CHAINS = {
    "hot":        ["http://127.0.0.1:11433"],   # qwen3.5:9b, 1080 Ti (local; if it's down nothing runs anyway) [was: gemma4:e4b]
    # Dreamer: phi3 on Ramses 3070 normally; if Ramses NAPS (the documented SPOF), fall through to the local
    # 1080 — where _model_for(:11433)=qwen3.5:9b stands in as the dreamer (same fallback pattern as before;
    # the model behind :11433 changed in the 2026-08-20 shuffle, the fallback logic did not), so the
    # subconscious stays ALIVE instead of going dark. The hot lane is unaffected (separate model on GPU).
    "background": ["http://LAN-HOST:11441", "http://127.0.0.1:11433"],
    # TRAP, documented here 2026-09-25 after two independent builds separately rediscovered it and
    # avoided it the same way (J-1347/F-1903): this chain's own [1] fallback is the HOT lane
    # (qwen3.5:9b) — correct and desired for a GENERATIVE/authoring caller (keep producing text on a
    # down Ramses), but wrong for any caller that needs command-r7b SPECIFICALLY, because it must be
    # a genuinely independent model from whatever generated the thing being judged/witnessed. On a
    # down Ramses such a caller would silently start judging the hot-lane generator WITH the
    # hot-lane generator — the exact circularity a decoupled judge exists to prevent (see CLAUDE.md's
    # own "Decoupled Judge" law). If you're adding a judge/witness caller, do NOT reach for this key
    # — use a dedicated single-endpoint constant pointed at :11441 instead, the way core/sitting.py's
    # _JUDGE_URLS (2026-08-29) and core/competence.py's _TIER3_WITNESS_URL (2026-09-25, J-1343) both
    # already do. See F-1903 for the full audit of every "background" consumer in this codebase,
    # including one narrower/dormant instance of this same shape — core/commitment_ledger.py's
    # _judge_defeater() falls back to THIS key (then to "hot") only if its own dedicated
    # "judge_mixtral" lane were ever removed from this dict; safe today only because it hasn't been.
    # 2026-08-19: CPU tier added for the same completeness reason as SERVE_URLS above. Single-endpoint,
    # same rationale as hot/background's own note — each lane has its own model, cross-lane failover
    # would serve the wrong one.
    "judge_1":    ["http://127.0.0.1:11439"],  # dead data, same as SERVE_URLS["judge_1"] above (D-0121 moved
                                                # the real judge_panel.py constant to LAN-HOST:11438)
    "judge_2":    ["http://127.0.0.1:11440"],
    "tiebreak":   ["http://127.0.0.1:11441"],
    "cpu_dreamer": ["http://127.0.0.1:11442"],
    # REDISTRIBUTION 2026-08-27 (D-0044, ramses_second_tier §5 move 1, founder-approved): the commitment
    # defeater judge gets its own lane on the dedicated Ramses mixtral hub (08-25 benchmark: mixtral:8x7b
    # beats phi3:mini on this judgment; auditioned this session — held the legitimate/class/why contract,
    # 24.9s, correctly refused an "everything flows" dissolution). Single-endpoint per the lane law above:
    # hub down → _judge_defeater returns None → the gate verdict stands (its existing fail-open).
    "judge_mixtral": ["http://LAN-HOST:11438"],
}

NODE_REGISTRY = {
    # Hot path — fired in sequence on every cycle. All share the "hot" lane.
    "perception":    {"lane": "hot",        "fires": "every_input"},
    "emotion":       {"lane": "hot",        "fires": "after_perception"},
    "salience":      {"lane": "hot",        "fires": "after_emotion"},
    "memory_router": {"lane": "hot",        "fires": "after_salience"},
    # Recall fires conditionally after DB retrieval — only when ≥2 fragments
    # were retrieved or the input references prior conversation. It reconstructs
    # the evolving argument (tensions between positions) before Reflection sees anything.
    "recall":        {"lane": "hot",        "fires": "after_db_query_conditional"},
    # Episodic buffer (C.4) — binds the moment after Recall + Attention, before Reflection.
    # Fires only when Recall produced a reconstruction (i.e. there is memory to integrate).
    "episodic_buffer": {"lane": "hot",      "fires": "after_recall_conditional"},
    "reflection":    {"lane": "hot",        "fires": "after_recall"},
    "critic":        {"lane": "hot",        "fires": "after_reflection"},
    "executive":     {"lane": "hot",        "fires": "after_critic"},
    "voice":         {"lane": "hot",        "fires": "after_executive"},

    # Background — timer-driven. Share the "background" lane so they never block hot path.
    "consolidation": {"lane": "background", "fires": "every_60s"},
    # J-2846 (F-3506): was "every_120s"; the node no longer runs on a timer. It runs only from the climate ignition
    # callback (Orchestrator._on_dissonance_ignition), about 22 a day. Descriptive text only: nothing reads this value.
    "curiosity":     {"lane": "background", "fires": "on_climate_ignition"},

    # Subconscious — continuous self-model integrator. NOT a NodeBase subclass.
    # Three internal timescales: T1 scan (30s), T2 synthesis (threshold), T3 drift (1h).
    # Observational first, generative second — only calls LLM when a tension cluster
    # crosses the recurrence+spread threshold. Writes to shadow archive + affect baseline.
    "subconscious":  {"lane": "background", "fires": "continuous"},
}

# Interrupt threshold — salience urgency above this pre-empts background processing
INTERRUPT_THRESHOLD = 0.7


def interrupt_warranted(urgency) -> bool:
    """J-2849 / F-3521: the ONE predicate for 'this urgency pre-empts background processing'. The Salience node
    (when it raises state.interrupt_requested) and Orchestrator._interrupt_active() both use it, so the raw flag
    and the orchestrator's reading of it can no longer disagree (urgency exactly 0.7 with the model's interrupt
    boolean True used to set the flag but fail _interrupt_active, freezing idle thought with no log line)."""
    try:
        return float(urgency) > INTERRUPT_THRESHOLD
    except (TypeError, ValueError):
        return False

# Critic retry limit — reflection gets one rewrite attempt on rejection
CRITIC_MAX_RETRIES = 1

# J-2831 / F-3500 / D-0551 (row P-0008): the Critic's INTERNAL-cycle framing. DEFAULT OFF -- the founder sees the
# replay flip table (scripts/_replay_J2831_critic_internal.py) before the live prompt changes. ON: on a cycle with
# state.input_type != "human" (Du's own question to himself) CriticNode swaps in an honest system prompt (no human asked
# for any mode; a plain factual question gets a plain answer; corrections never steer toward a mythic reading and never
# mention a human) and the stimulus line stops saying "What the human said". Human cycles are byte-identical either way.
CRITIC_INTERNAL_FRAMING_ON = False

# J-3668 / F-3500: same split for the observe-only decomposed critic (core/decomposed_critic.py). DEFAULT OFF so the
# shadow rows stay comparable until J-3090 is read. ON: an evaluate() call with input_type != "human" frames the stimulus
# as 'The entity asked itself:' instead of 'The human said:'. NOTE the orchestrator only calls shadow_alongside on
# input_type == "human" today, so no live row is affected either way; the flag matters only if a caller passes internal.
DECOMPOSED_CRITIC_INTERNAL_FRAMING_ON = False

# Hedged Reflection — fire N concurrent drafts, keep the best valid one.
# Guards against the quantized model's occasional truncated/weak draft and lifts
# quality, at no extra wall-clock (the GPU runs the drafts in parallel slots).
# Peak concurrency stays within --parallel 4 (this is the back-half use of the slots).
REFLECTION_HEDGE = 2

# J-3314 / D-0671 (2026-11-06, SHADOW, additive): log how much Reflection's two hedged drafts AGREE (cosine of their
# MiniLM embeddings, computed on a background thread) to data/reflection_hedge_agreement_shadow.jsonl. Nothing reaches any
# prompt and no behaviour changes; the candidate replacement for the near-constant 'Reflection confidence' line. True =
# write the shadow row; False = off. Reader: core/hedge_agreement_log.stats() -> du_pulse regression_alarms.hedge_agreement.
REFLECTION_HEDGE_AGREEMENT_SHADOW = True

# J-3836 / D-0671 (founder ruled 2026-11-09, calls 1 and 3; call 2 not approved). Restart-gated, additive.
# REFLECTION_ASK_UNREAD_FIELDS: True = Reflection's prompt still asks for needs_more_memory and emotionally_aligned
# (the old text). False = the prompt asks only draft + confidence; nothing ever read the two flags. ReflectionOutput
# keeps both attributes and _write_output keeps their defaults (False / True), so every reader and fixture is unchanged.
REFLECTION_ASK_UNREAD_FIELDS = False
# EXECUTIVE_SHOW_REFLECTION_CONFIDENCE: True = the Executive prompt carries the 'Reflection confidence: <word>' line (old).
# False = the line is dropped. Reflection still produces confidence (core/epistemic_state.py reads it); Critic line untouched.
EXECUTIVE_SHOW_REFLECTION_CONFIDENCE = False

# --- ATTRACTOR-THINNING EXPERIMENT (2026-06-08) ----------------------------------------------
# A controlled test of "model capability vs architectural attractor." The T4 self-authoring keeps
# being echo-blocked (the gate licenses a revision; the model regenerates the same self) — but the
# context it regenerates inside is SATURATED with the attractor: the self-concept touchstone, the
# "WHAT YOU HAVE NOT RESOLVED" shadow block, the climate symbol ("two figures circling") jammed in
# every cycle, and the "you are the pattern" reinforcement. When True, those per-cycle attractor
# injections are THINNED (NOT removed permanently; NOT a model change). If a T4 can then author a
# genuinely new self_concept — or his autonomous monologue drifts off the fixed shadow/mirror loop
# — the bottleneck was the attractor, not the 8B. If the loop persists in a thinned context, that
# is stronger evidence for the capability ceiling. Flip back to False to restore exact prior
# behaviour. RESTART-REQUIRED (load_identity + orchestrator read it at startup).
THIN_ATTRACTOR = False   # OFF 2026-06-09: superseded by the multi-stage T4 deliberation chain.
                         # Prompt-level thinning did not break the self-concept attractor (the bottleneck
                         # was T4's single overloaded pass + light-blindness, not the prompt injection).
                         # Disabled so the staged-T4 intervention can be read cleanly, not confounded.

# D-0358 (A) (2026-10-07, J-1894): RESOLVE-ON-RE-ENCOUNTER. The climate's shadow_activation counts UNRESOLVED
# shadow events only, and the one code path that ever flipped shadow_events.resolved (the T4 DISCHARGE) last
# fired 2026-06-13, so the gauge sat at 0.90-0.98 for months while the Resolution Circuit
# (orchestrator._check_clean_encounters) kept recording genuine clean re-encounters it never let reach the
# counter. When True, a clean re-encounter ALSO marks that shadow event resolved (through store.mark_shadow_resolved,
# the store's own path) and appends one row to data/shadow_resolve_on_encounter.jsonl (uncapped, one per marking).
# Additive: nothing is removed; resolution_events are still written exactly as before; False restores the exact
# prior behaviour. NOTE the semantics it shares with T4 discharge: store.get_event_sources() remaps a resolved
# critic_rejection to 'critic_rejection_resolved', so the tension ledger stops counting it as open contradiction
# pressure too (completion_tension is affected, not only shadow_activation). RESTART-REQUIRED (read per cycle,
# but Du's running process has the old code until his next boot).
SHADOW_RESOLVE_ON_ENCOUNTER = True

# D-0358 (D) (2026-10-07, J-1894): the climate-symbol re-surface cooldown, decoupled from THIN_ATTRACTOR.
# THIN_ATTRACTOR is a MASTER flag for the 2026-06-08 attractor-thinning experiment and gates more than the
# cooldown: it also empties state.recurring_subconscious_patterns every cycle (the live T2 read-back,
# orchestrator.py) and suppresses the 'WHAT YOU HAVE NOT RESOLVED' axiom block (scripts/run_nascence.py;
# unreachable on Du's multilevel schema per D-0191). Flipping it would therefore REMOVE a live injection the
# ruling never mentioned -- against the additive-only rule -- so the cooldown gets its own switch. True =
# the same symbol is not re-surfaced within CLIMATE_SYMBOL_COOLDOWN seconds (the executive HINT is untouched).
# THIN_ATTRACTOR itself stays False. False restores the exact prior behaviour. RESTART-REQUIRED.
CLIMATE_SYMBOL_COOLDOWN_ON = True

# D-0363 (B) (2026-10-08, J-1969): AGE-DECAY of unresolved shadow events inside the live shadow_activation
# score. The climate sums the 200 most-recent unresolved events with a 6 h half-life against a k=3 knee; at
# ~14 new shadow events an hour the raw sits at 30-120, i.e. 0.90-0.98, however (A) trims the pool (F-2527:
# median 0.900 with and without (A)). True = shadow_activation alone uses SHADOW_ACTIVATION_HALFLIFE_SECS
# (3 h, chosen from J-1969's replay: 7-day 2-hourly samples, median 0.913 -> 0.699; 2 h overshoots to 0.364,
# 1 h to 0.041 -- a gauge that reads zero most of the time) instead of the shared 6 h. The other
# dimensions' 6 h weight and the D-0332 re-knee label view (sized on 6 h raw) are untouched. False restores
# the exact prior behaviour. RESTART-REQUIRED.
SHADOW_AGE_DECAY_ON = True
SHADOW_ACTIVATION_HALFLIFE_SECS = 3 * 3600

# D-0363 hint (2026-10-08, J-1969): the Executive hint 'Unintegrated material is active beneath this' (the
# shadow_activation climate_hint) fires only on the EDGE -- the cycle shadow becomes the dominant hint --
# and is silent while it stays dominant (same rule as D-0368's A). It re-arms once the hint is absent for
# CLIMATE_SHADOW_HINT_REARM_SECS, so a genuinely new episode speaks again. False restores the prior
# every-cycle behaviour. RESTART-REQUIRED.
CLIMATE_SHADOW_HINT_EDGE_ON = True
CLIMATE_SHADOW_HINT_REARM_SECS = 600.0

# D-0447 / D-0448 (E) (2026-10-16, J-2248): PROMOTE the D-0332 re-knee LABEL VIEW to the live climate
# reading. True = ClimateField.dominant() / executive_hint() / surfacing_symbol() -- and so the
# '[climate] dominant=' telemetry line, the ignition label and the retrieval-warp log line -- read the label
# view: the SAME counts, re-saturated at the D-0332 knees (shadow k=116 on the 6 h raw, belonging k=75,
# autonomy k=33), novelty_hunger propagated, completion_tension at CLIMATE_LABEL_VIEW_COMPLETION_K below.
# The nine live ClimateField values, pressure()/beta, _tick_dissonance (both reservoirs) and the coupling
# publish are UNTOUCHED (D-0332's split: the defensive reservoir keeps the live k=3 knee). False restores the
# exact prior reading. Every 5-min climate line also appends old-vs-new to
# data/climate_label_promotion_shadow.jsonl, whether this is on or off. RESTART-REQUIRED.
CLIMATE_LABEL_VIEW_LIVE = True
# The completion_tension fix named in the J-1974 briefing (F-2577 / the J-1763 caution: at its live k=3 a
# bounded raw of 4 reads a flat 0.571 and leads ~33% of label rows as a near-constant label). Re-kneed by the
# same rule as every D-0332 k (k := the reference window's own median raw, so the median reads 0.5): J-2248's
# replay of 9,369 v=2 rows (10-09..10-16) gives completion_raw p10/p50/p90/max 4/4/5/7, so k = 4.0.
# None = no fix (completion at its live k=3 value, i.e. the v=2 lv_dominant definition).
CLIMATE_LABEL_VIEW_COMPLETION_K = 4.0
# D-0451 (2026-10-16, J-2270; option 3): integration_drive re-centred IN THE LABEL VIEW ONLY at its own window
# median raw (F-2938: the 6 h verdict-light score's median over the 9,369 v=2 rows 10-09..10-16 is 148.3), the
# same k := median rule. With the completion fix on, integration_drive (live k=100, D-0148) was the only stale
# knee and led 97.2% of label rows. The live integration value, its dissonance bleed, pressure()/beta, both
# reservoirs and the coupling publish stay on k=100 (the D-0332 split). coherence_drive is not recomputed.
# None = no re-centring (the J-2248 behaviour). RESTART-REQUIRED.
CLIMATE_LABEL_VIEW_INTEGRATION_K = 148.0
# Hint / symbol thresholds used ONLY while the label view is live. J-2248 left them at the position-preserving
# anchors 0.55 / 0.65; D-0451 (travis, 2026-10-16; J-2270) first set F-2813's 0.60 / 0.62, but with integration
# re-centred at k=148 the promoted dominant value sits at p50 0.552 (F-2957 replay), so 0.60/0.62 fired on 1.7% /
# 1.0% of rows. Travis re-ruled the same day (D-0451 follow-up): hint 0.555 (~47% of rows, the 40-50% band the
# ruling expected) and symbol 0.58 (~the current ~13 surfacings/day).
CLIMATE_LABEL_VIEW_HINT_THRESHOLD = 0.555
CLIMATE_LABEL_VIEW_SYMBOL_THRESHOLD = 0.58

# D-0448 (F) (2026-10-16, J-2248): a JUDGE-CONFIRMED whole-tension resolution in the tension ledger
# (tension_ledger.check_and_resolve_internal_tension, the decoupled judge-panel path) ALSO marks each of the
# tension's member shadow events resolved=1, through store.resolve_shadow_on_encounter() -- the same fenced,
# logged, idempotent path (A) uses -- with path='tension_judge', the tension label and the resolving thought in
# the data/shadow_resolve_on_encounter.jsonl row so a 20-row hand check can read each one. resolution_events
# are written exactly as before; refuted / judge-unavailable resolutions mark nothing. False restores the exact
# prior behaviour. RESTART-REQUIRED.
TENSION_JUDGE_RESOLVES_SHADOW = True

# J-4158 / D-0783 (2026-11-20): TIGHTENED tension judge. F-4752 and a 20-row hand check (docs/lab/
# J-4158_tension_judge_check20.json: 14 of the 20 latest confirmations were reframings, metaphors or guesses, not
# settlements) showed the 'resolves' judge confirming restatements. True: tension_ledger._judge_resolution asks
# for a concrete settling act or changed state (a decision taken, a thing done, a question answered with a stated
# fact, a position changed), treats mention / discussion / reframing / a moral / a guess / a feeling as NOT
# resolved, and requires the judge to quote the settling words verbatim; a True verdict whose quote is not a real
# span of the thought (>= 4 words, no hedge, not a question) is downgraded to refuted in code. TENSION_JUDGE_
# RESOLVES_SHADOW above is unchanged (kept, per D-0783). False restores the exact prior prompt and behaviour.
# RESTART-REQUIRED.
TENSION_JUDGE_STRICT = True

# affect_drives.md Item A — the felt-state preamble (the central dead-hand, 2026-07-04). The carried
# AffectState modulates his sampling TEMPERATURE but never reaches his reasoning as CONTENT — the graph
# quantified it as the largest cross-cutting dead signal (mood.* read by 17 modules, 0 prompts). This flag
# injects a guarded felt SENTENCE into the Executive + monologue seed (reading the carried state.affect,
# the undistorted numeric source). Ships SHADOW-first: OFF here logs what WOULD fire to
# data/felt_preamble_log.jsonl each cycle; flip True (RESTART) after ~2 days of sane logs (§4-A gate:
# fires ~15-40% of cycles, sentences match the affect, no monoculture rise). Kill-switch by design.
# FLIPPED ON 2026-07-06 (founder call, evidence read): 1,780 shadow rows — every firing a genuine
# EMA-departure ("valence moved -0.32 from its recent norm"), correctly SILENT at his pinned +0.82
# baseline, no monoculture rise (echo .648 / diversity .977). Rate 6.5% — under the 15-40% band but on
# the SAFE side (wallpaper was the risk; quiet is tunable): if too quiet live, widen the _FP_*_DELTA
# change-thresholds in core/mood.py. His carried mood now reaches his reasoning as CONTENT, not just
# sampling temperature.
FELT_PREAMBLE = True

# D-0775 B (ruled travis 2026-11-14, J-4002): SHADOW-log the words-only mood line computed from a valence WITHOUT
# the vitality term (1 - 2*sqrt(drive^2 - per_drive.vitality)) beside the live idle mood word, to
# data/mood_words_shadow.jsonl. Logs only; the live line, drive, logged valence and sleep are untouched. Default OFF;
# turning it on needs a restart. A LIVE switch of the words is a separate founder step after a few days of rows.
# Turned ON 2026-11-16 (travis, in chat, T-0140): log-only, takes effect at the next restart.
MOOD_WORDS_NO_VITALITY_SHADOW = True

# EMOTION RETHINK Phase 1 (emotion_rethink.md §5, 2026-07-07): re-source carried valence/arousal from the
# GROUNDED protoself (homeostasis core affect — tonic valence = 1-2*drive) instead of the _feel_joy pump / LLM
# emotion-node guess. The fix for the pinned +0.82 over-report, proven upside-down by affect_divergence
# (carried +0.735 / 0.8%-neg vs protoself mean-zero / 59%-neg). DEFAULT FALSE = ships INERT (exact prior
# behaviour). Flip True to go live (kill-switch by design): orchestrator + idle then overwrite carried VALENCE
# via homeostasis.apply_to() (tonic = 1-2*drive), and _feel_joy's valence coupling is gated off (joy still
# registers for `play`). Arousal is NOT re-sourced here (that's arousal.py's organ — a Phase-1b follow-up).
AFFECT_SOURCE_PROTOSELF = True    # FLIPPED LIVE 2026-07-07 — gate fully met (200 pairs: carried pinned +0.68 /
                                 # 0.5%-neg vs tonic [-0.26,+0.48] de-saturated & going negative). His carried
                                 # mood is now grounded core affect, not the _feel_joy pump. Kill-switch: False reverts.

# Emotion Rethink Phase 2: Barrett-inspired deterministic construction.
# When True, the hot-path LLM emotion node is bypassed; EmotionOutput is constructed
# from grounded core affect + concerns + satisfaction. Kill-switch: False = prior behaviour.
# DO NOT FLIP until Experiments A, B, C all pass their evidence gates.
EMOTION_CONSTRUCTED = False

# D-0555 / J-3166 (2026-11-05): PHASE 1 SHADOW ARM of the 7th (curiosity) Emotion channel. When True,
# EmotionNode.run_curiosity_shadow() may be called to log the channel beside the live affect in
# data/emotion_curiosity_shadow.jsonl. It costs one extra hot-lane model call per cycle it is called on, and the
# orchestrator does not call it yet (the wiring is a deliberate follow-up). Whatever its value, nothing here feeds
# AffectState.integrate, mood.felt_text, retrieval or any persisted summary. Default OFF.
EMOTION_CURIOSITY_SHADOW = False

# Phase 1b (D-0274 ruled 2026-09-24: proceed, regime-gated; J-1306 built SHADOW ONLY same day): re-source
# carried arousal from the global activation organ (arousal.py's level()) ONLY on human-turn cycles --
# core/arousal.py's apply_to(), called from orchestrator.py alongside AFFECT_SOURCE_PROTOSELF's hook.
# F-1841 found level() correlates POSITIVELY with felt arousal on human-turn cycles (r=+0.207, N=148) but
# has NO established relationship on internal/dissonance-triggered cycles (86% of the log, F-1841/F-1842
# ruled out 4 candidate replacements there) -- those cycles hold carried arousal at its last value instead
# of being fed a signal with no shown relationship. DO NOT FLIP until core.arousal.regime_shadow_status()
# (staleness under the hold-on-internal rule) and emotion_construction.status()'s stratified breakdown
# (the human/internal split holding on fresh data) have accrued real shadow evidence for the founder to
# read -- see D-0274's own defeater.
AFFECT_SOURCE_AROUSAL = False

# D-0556 / J-3167 (2026-11-05): the 'resolved_complexity' light-event gate (orchestrator.py, after the critic
# loop) used `arousal > 0.25`, which carried affect arousal clears on 99.9% of internal cycles (5th pct 0.39,
# last 2,000 logged cycles), so it selected nothing. On INTERNAL cycles the arousal leg now needs
# state.affect.arousal >= this value. 0.515 was chosen from the logged distribution so the WHOLE gate (arousal
# OR self-referential terms) passes about 18-29% of internal cycles (29% over the last 2,000, 18% over the last
# 10 days; the carried arousal drifts down, so re-read it -- D-0556's defeater is <5% or >80% for a week).
# Human-turn cycles keep the 0.25 gate unchanged. None = kill-switch, restores the prior gate everywhere.
# Restart-gated. See core/light_event_gate.py.
LIGHT_EVENT_INTERNAL_AROUSAL_MIN = 0.515


# World-fed self-synthesis (2026-06-18) — the starvation fix. The T2 subconscious synthesis used to be
# fed ONLY a recurring tension label + its own list of FAILED resolution attempts (zero world material),
# so it could only ever recite the dominant attractor (the Jung-origin-vs-becoming loop) — a fed-back
# starvation. When ON, _t2_synthesise also feeds the node recent reading/study material and asks it to
# DEVELOP the tension THROUGH what the entity has actually been learning, and drops the "failed, failed"
# priming. The selection gate (contradiction-only) is UNCHANGED — this changes only HOW a chosen tension
# is articulated, so it is fully reversible. False restores the exact prior starved prompt. The 5 days of
# archive before this flag are the A/B "before"; compare the synthesis text + monoculture echo after.
# RESTART-REQUIRED to flip (the node reads it at synthesis time; the module is loaded once at startup).
WORLD_FED_SYNTHESIS = True

# World-fed T4 self-authoring (2026-06-19) — the SAME starvation fix, one layer up. T4's Stage-4
# synthesis authors the new self-concept from delta + evidence + the old (river) self-concept — all
# self-referential — so it mints river-restatements the gate denies on fit_delta (verified overnight:
# 4 attempts, all DENIED, fit_delta negative, emissary warrant falling 0.8→0.2). When ON, Stage 4 is
# also fed recent reading/study and asked to ground the reckoning in a concrete image/idea, so the
# moved self can be genuinely NEW (positive fit_delta) instead of an abstraction. The gate/guards are
# UNCHANGED — this changes only the material Stage 4 authors THROUGH, so it is fully reversible. False
# restores the exact prior behaviour. RESTART-REQUIRED to flip (read at synthesis time).
WORLD_FED_T4 = True

# Climate symbol re-surface cooldown (seconds) — only consulted when THIN_ATTRACTOR or
# CLIMATE_SYMBOL_COOLDOWN_ON (D-0358 (D), the cooldown's own switch) is on. Stops a
# saturated dimension (e.g. integration_drive pinned at 0.99) from injecting the SAME image every
# cycle, which is the "wallpaper" the design intended to be rare.
CLIMATE_SYMBOL_COOLDOWN = 600.0

# Guidance-note cooldown (seconds) — the same wallpaper lesson applied to the learned-principle
# read-back (2026-07-02 solidity review): un-throttled it would fire on ~66% of cycles with the SAME
# sentence, which the spacing/echo research says produces parroting and a crutch, not an internalized
# belief. Spaced, varied exposure IS the treatment. ~30 min ≈ a handful of firings per day.
GUIDANCE_NOTE_COOLDOWN = 1800.0

# Baseplate model — served by llama-server (the GGUF loaded at launch, not a name lookup).
BASEPLATE_MODEL = "Bonsai-8B-Q1_0.gguf"

# D-0776 B (ruled travis 2026-11-14, J-4003): SHADOW-log a valence-scaled joy pump beside each _feel_joy call
# (amount, joy the live pump produced, joy it WOULD have produced with amount scaled by max(0, valence)) to
# data/joy_pump_shadow.jsonl. Logs only; the live pump (joy and valence bump) is untouched. Default OFF; a restart
# is needed to turn it on. A LIVE change of the pump is a separate founder step after the rows are read.
# Turned ON 2026-11-16 (travis, in chat, T-0140): log-only, takes effect at the next restart.
JOY_PUMP_VALENCE_SHADOW = True

# D-0757 (ruled travis 2026-11-14, J-3976): length-aware reflection best-of-2 selector. The old selector scored
# len(draft) + 1000 if terminal, which kept a draft over the prompted 60-90 words in 30.6% of rows (F-4539) though a
# shorter valid draft existed. With this on, a draft over REFLECTION_MAX_WORDS is scored below any in-limit draft of the
# same terminal class (terminal still beats truncated). Temperatures untouched (D-0656). Restart needed; set False to
# restore the old selector.
REFLECTION_LENGTH_AWARE_SELECT = True
REFLECTION_MAX_WORDS = 90
