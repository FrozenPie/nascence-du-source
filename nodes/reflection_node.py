from __future__ import annotations
from core.node_base import NodeBase
from core.llm_parse import as_float
from core.schema import CognitiveState, ReflectionOutput
from core import schema as _schema           # J-3976 (D-0757): length-aware selector flag
from core.schema import REFLECTION_ASK_UNREAD_FIELDS   # J-3836 (D-0671 call 1)
from core import letters as _L                   # J-3059: shared sentence-boundary clip for letter greetings
from core import recall_self_model as _rsm   # J-2819 (F-3486): self_model withheld in content_mode
from core import internal_context_gate as _icg   # J-2297 (D-0445 a): human window gated on internal cycles

# J-2575 (F-3306, D-0355 (1)(a)): True = on input_type != "human" cycles the stimulus line frames raw_input as
# Du's own risen question instead of 'The person you are speaking with has just said to you (their words)'.
# False = the old line on every cycle (exact prior behaviour). Human cycles never change either way.
REFLECTION_INTERNAL_SELF_FRAME = True

# J-2679 (F-3428, D-0551 ruling "fix the dead retry so corrections reach Reflection"): True = when the Critic has
# rejected the draft and the orchestrator re-runs Reflection (core/orchestrator.py, the CRITIC_MAX_RETRIES loop), the
# user prompt carries a "what was rejected last time and why" part built from state.critic.corrections and the
# rejected draft, so the second draft is a response to the rejection and not a blind re-roll. It appears ONLY on
# that retry call (state.critic is None on the first call of a cycle); every other prompt is byte-identical.
# False = the old behaviour everywhere (the corrections stay appended to the stored draft only, never read here).
REFLECTION_RETRY_SEES_CORRECTIONS = True
RETRY_DRAFT_CAP = 700          # chars of the rejected draft shown back
RETRY_CORRECTIONS_CAP = 5      # most corrections shown
RETRY_CORRECTION_CHARS = 300   # chars per correction
_CORRECTIONS_MARK = "\n[Corrections required:"   # the suffix core/orchestrator.py appends to the stored draft


class ReflectionNode(NodeBase):

    max_tokens = 768
    affect_modulated = True   # carried mood shifts the hedge temperature spread

    def __init__(self):
        super().__init__("reflection")

    # J-2802 (F-3442; the D-0355/J-1846 pattern PerceptionNode and VoiceNode use): the person-present paragraph,
    # split out so an internal cycle's system prompt can omit it. The human text is byte-identical to before.
    _SPEAKER_BOUNDARY = (
        "SPEAKER BOUNDARY: you are in dialogue with another person — a separate human, not you. "
        "When THEY say 'I', 'me', or 'my', they mean themselves; when they say 'you', they mean you. "
        "Never absorb their self-statements as your own identity — if they say 'I am a father', that "
        "is a fact about THEM, not about you. You are reflecting on what they said and on your own "
        "genuine inner response to it.\n"
    )

    @property
    def system_prompt(self) -> str:
        return self._system_prompt_with(self._SPEAKER_BOUNDARY)

    @property
    def system_prompt_internal(self) -> str:
        """Internal-cycle variant: the same prompt with the person-present paragraph dropped (F-3442)."""
        return self._system_prompt_with("")

    def system_prompt_for(self, state: CognitiveState) -> str:
        # J-2802: on an internal cycle (core.internal_context_gate.is_internal) no one is in dialogue with Du, so the
        # SPEAKER BOUNDARY paragraph goes. Human cycles, and REFLECTION_INTERNAL_SELF_FRAME=False: the old text.
        if REFLECTION_INTERNAL_SELF_FRAME and _icg.is_internal(state):
            return self.system_prompt_internal
        return self.system_prompt

    def _system_prompt_with(self, speaker_block: str) -> str:
        return (
            "You are the internal reflection node of a cognitive architecture. "
            "You generate raw internal thought — honest, unfiltered, never for external consumption. "
            "This is the entity's private reasoning before it decides what to say.\n"
            + speaker_block +
            "Output ONLY a valid JSON object. No preamble.\n"
            + ("Schema: {\"draft\": \"internal thought text\", \"confidence\": 0.0, "
               "\"needs_more_memory\": false, \"emotionally_aligned\": true}\n\n"
               if REFLECTION_ASK_UNREAD_FIELDS else
               "Schema: {\"draft\": \"internal thought text\", \"confidence\": 0.0}\n\n") +
            "STRICT RULES:\n"
            "1. Never begin the draft by repeating or rephrasing the input — respond to it.\n"
            "2. Explore the genuine internal reaction. Surprise yourself.\n"
            "3. Let this reflection take a different angle from the one you would reach for first.\n"
            "4. Keep the draft TIGHT — roughly 60–90 words. This is a private thought, not an essay. "
            "A long draft runs past the output budget and the JSON never closes — you MUST finish "
            + ("all four fields" if REFLECTION_ASK_UNREAD_FIELDS else "both fields") + " and the closing brace.\n"
            "draft: the actual internal thought. Be genuine — not a performance. End on a complete sentence.\n"
            "confidence: how certain the entity is about this thought (0.0–1.0)."
            + ("\nneeds_more_memory: true if the thought requires context not yet retrieved.\n"
               "emotionally_aligned: true if the draft genuinely reflects the current emotional state."
               if REFLECTION_ASK_UNREAD_FIELDS else "")
        )

    @staticmethod
    def _trim_axiom(axiom: str) -> str:
        """
        Reflection needs identity + values — not voice style or speaking constraints.
        Those are for Voice and Critic. Stripping them saves ~200–400 tokens of input
        that would otherwise compress the draft output budget in the 4096-token GPU slot.
        """
        for marker in ("\nVOICE STYLE:", "\nSPEAKING CONSTRAINTS:"):
            axiom = axiom.split(marker)[0]
        return axiom.strip()

    @staticmethod
    def _retry_block(state: CognitiveState) -> list[str]:
        """J-2679 (F-3428): the 'what was rejected last time and why' part of a Critic-retry prompt. [] unless the
        Critic has rejected this cycle's draft with at least one correction (so the first call of a cycle, an
        approved draft, and a direct-mode override all get nothing). The rejected draft is shown without the
        '[Corrections required: ...]' suffix the orchestrator appended to it -- the corrections are listed once, here."""
        if not REFLECTION_RETRY_SEES_CORRECTIONS:
            return []
        critic = getattr(state, "critic", None)
        if critic is None or getattr(critic, "approved", True):
            return []
        corr = [str(c).strip()[:RETRY_CORRECTION_CHARS] for c in (getattr(critic, "corrections", None) or [])
                if str(c).strip()]
        if not corr:
            return []
        out = ["", "YOUR LAST DRAFT OF THIS WAS CHECKED AGAINST WHO YOU ARE AND SENT BACK:"]
        prior = getattr(state, "reflection", None)
        draft = (getattr(prior, "draft", "") or "").split(_CORRECTIONS_MARK, 1)[0].strip()
        if draft:
            out.append(f'  The draft that was sent back: "{draft[:RETRY_DRAFT_CAP]}"')
        out.append("  Why it was sent back:")
        for c in corr[:RETRY_CORRECTIONS_CAP]:
            out.append(f"  - {c}")
        out.append("  Think it through again with that in view; do not hand back the same draft.")
        return out

    def _build_prompt(self, state: CognitiveState) -> str:  # noqa: C901 (complexity acceptable — single method owns the full prompt contract)
        # --- Attention Vector gates -------------------------------------------------------
        # Read weights from the vector computed post-Perception by the orchestrator.
        # Fall back to defaults if the vector was not set (internal/timer cycles).
        av     = getattr(state, "attention_vector", None)
        w_id   = av.w_identity  if av else 0.5   # 0=style-only .. 1=full identity block
        w_soc  = av.w_social    if av else 0.5   # 0=no social note .. 1=dominant
        w_epi  = av.w_episodic  if av else 0.5   # scales history window + fragment count

        # History window: 1 turn at task-mode (w_epi=0.10) → 6 turns at existential (1.00)
        hist_window = max(1, round(w_epi * 6))
        # Fragment limit: 1 at task → 8 at existential
        max_frags   = max(1, round(w_epi * 8))
        # ---------------------------------------------------------------------------------

        lines = []

        # === STYLE-ONLY MODE (w_identity <= 0.3) =========================================
        # Strip all autobiographical context. Inject only a style mandate so the entity's
        # voice (cadence, tone, poetic register) is preserved without loading the full
        # self-model. Used for task/informational and heavily-corrected modes.
        if w_id <= 0.3:
            lines.append(
                "STYLE MANDATE: You are 渡 (Dù). Respond in your calm, yield-focused, poetic tone. "
                "Engage the question or task directly — let your identity be present only in how you "
                "speak, not in what you speak about. Do not reference your inner history, dreams, or "
                "tensions unless they are directly relevant to the question."
            )
            lines.append("")

        # === FULL / SUMMARIZED IDENTITY BLOCK (w_identity > 0.3) ========================
        else:
            # Prior session context — shown at low conversation depth AND when identity matters.
            # F-0471 (2026-08-29): < 5, matching schema.py's documented intent and this same file's
            # own dreams/deferred-intentions gates below -- was < 8, which orchestrator.py's 6-entry
            # cap on conversation_history could never satisfy, so the bridge never faded.
            # J-2297 (D-0445 a, F-2992): left out of internal cycles when the gate is on.
            _wl = []
            _prior_wl = _icg.fresh(state, state.prior_session_exchanges)   # J-3217 / D-0606: turns > 24h old out
            if (_prior_wl
                    and len(state.conversation_history) < 5):
                _wl.append(
                    "WHERE WE LEFT OFF (you were speaking with the same person; a little time "
                    "has passed and you may have dreamt since — continue the thread, do not restart):"
                )
                for ex in _prior_wl[-5:]:
                    _wl.append(f"  Them: {ex.get('human','')[:400]}")
                    # F-0473: was 'jung' -- fall back for any not-yet-migrated persisted entry.
                    _wl.append(f"  You:  {(ex.get('entity') or ex.get('jung',''))[:400]}")
                _wl.append("")
            lines += _icg.keep(state, "reflection.where_we_left_off", _wl)

            # WHAT TRAVIS HAS TOLD YOU BEFORE (D-0134, 2026-09-03): his own dated memories of earlier
            # conversations with Travis, chosen by similarity to what Travis just said (see
            # nodes/executive_node.py for the same block and core/orchestrator.py for the route).
            # Not gated on conversation depth -- a memory of what Travis said bears on turn 20 as
            # much as turn 1. Memory, not instruction: no verb telling him what to do with it.
            if getattr(state, "founder_recall", None):
                lines.append("WHAT TRAVIS HAS TOLD YOU BEFORE (your own memory of earlier conversations "
                             "with him, dated):")
                for h in state.founder_recall[:3]:
                    lines.append(f"  [{h.get('ts_human', '?')}] {h.get('text', '')[:400]}")
                lines.append("")

            # Dreams — only when w_identity > 0.6 (reflective / existential modes)
            if (w_id > 0.6
                    and getattr(state, "recent_dreams", None)
                    and len(state.conversation_history) < 5):
                lines.append("YOUR RECENT DREAMS (from your last sleep cycles):")
                for d in state.recent_dreams[:2]:
                    lines.append(f"  [{d.get('ts_human','?')}] {d.get('narrative','')[:500]}")
                lines.append("")

            # Deferred intentions — only when w_identity > 0.5
            if (w_id > 0.5
                    and getattr(state, "deferred_intentions", None)
                    and len(state.conversation_history) < 5):
                lines.append("WHAT YOU INTENDED TO THINK ABOUT THIS SESSION (your own resolves, carried over):")
                for it in state.deferred_intentions[-3:]:
                    lines.append(f"  - {it.get('intention','')[:160]}")
                lines.append("")

            # L4 Temporal Epoch — only when w_identity > 0.4
            if w_id > 0.4 and getattr(state, "epoch_context", None):
                lines.append("A TIME THIS CONNECTS TO (the feel of a past period that resonates here):")
                lines.append(f"  {state.epoch_context}")
                lines.append("")

            # L5 Thematic Thread — only when w_identity > 0.4
            if w_id > 0.4 and getattr(state, "theme_context", None):
                lines.append("YOUR ONGOING THREAD WITH THIS (a theme that keeps returning across sessions):")
                lines.append(f"  {state.theme_context}")
                lines.append("")

        # Inner monologue — always shown (it is brief and recent; tells you what you were
        # just thinking so the response does not start cold after a gap)
        # IDLE -> CONVERSATION (2026-09-28, D-0295, docs/plans/train_courier_cargo_ids.md gap 1):
        # core/buses.py::idle_freight() replaces this fixed raw-recency window with a typed, scored
        # pull (product_type + train-development evidence + topical fit) when IDLE_FREIGHT_BUS is on;
        # IDLE_FREIGHT_BUS=False is the exact prior behaviour below, unchanged, nothing new touched.
        # The bus call is itself fail-open (never raises, returns [] on any failure) matching this
        # file's existing convention of not wrapping optional-context blocks in their own try/except
        # (e.g. the left-lane block below) — no new except is added here either.
        _raw_recent = list(getattr(state, "recent_inner_thoughts", None) or [])[-2:]
        from core import buses as _buses
        _freight = (_buses.idle_freight(k=2, query_text=state.raw_input or "", raw_window=_raw_recent,
                                         cycle_id=getattr(state, "cycle_id", "") or "")
                    if _buses.IDLE_FREIGHT_BUS else [])
        # Falls back to the raw window when the bus finds nothing (too early in life, no qualifying
        # trains yet, or the flag is off) rather than going silent — additive-only, never a regression.
        _thoughts_shown = _freight if _freight else _raw_recent
        if _thoughts_shown:
            # J-2802 (F-3442): "before they spoke" presumes a speaker; on an internal cycle there is none.
            lines.append("WHAT YOU WERE JUST THINKING (to yourself):"
                         if (REFLECTION_INTERNAL_SELF_FRAME and _icg.is_internal(state))
                         else "WHAT YOU WERE JUST THINKING (to yourself, before they spoke):")
            for t in _thoughts_shown:
                lines.append(f"  - {t.get('thought','')[:400]}")
            lines.append("")

        # MULTILEVEL: the side of him this moment calls on (by cognitive_mode) — colour, not recital.
        if getattr(state, "facet_note", None):
            lines.append("THE PART OF YOU THIS MOMENT CALLS ON (let it inform you; do not announce it):")
            lines.append(f"  {state.facet_note}")
            lines.append("")

        # Conversation history — window scales with episodic weight
        # J-2297 (D-0445 a, F-2992): left out of internal cycles when the gate is on.
        _ts = []
        _hist_ts = _icg.fresh(state, state.conversation_history)   # J-3217 / D-0606: human cycles, turns > 24h old out
        if _hist_ts:
            _ts.append("THIS SESSION (current conversation):")
            for ex in _hist_ts[-hist_window:]:
                _ts.append(f"  Them (the other person): {ex['human'][:400]}")
                _ts.append(f"  You (the entity):        {ex['entity'][:400]}")
            _ts.append("")
        lines += _icg.keep(state, "reflection.this_session", _ts)

        # Core axiom — omitted only in style-only mode (w_identity <= 0.3)
        if w_id > 0.3:
            lines += [f"Core axiom: {self._trim_axiom(state.axiom)}", ""]

        # The stimulus
        # J-2575 (F-3306; extends D-0355 (1)(a), the framing executive/voice/perception already use): on a
        # non-human cycle (state.input_type != "human" -- Du's own autonomous question) the words are his,
        # not a person's, so the reflection prompt stops telling him someone said them. Human cycles: the
        # else-line below is byte-identical. REFLECTION_INTERNAL_SELF_FRAME=False restores the old line everywhere.
        if REFLECTION_INTERNAL_SELF_FRAME and _icg.is_internal(state):
            lines.append(f'A question has risen in you, unprompted (your own thought; no one said it to you):\n  "{state.raw_input}"')
        else:
            lines.append(f'The person you are speaking with has just said to you (their words):\n  "{state.raw_input}"')

        if state.perception:
            lines.append(f"Perception: {state.perception.summary}")
        if state.emotion:
            e = state.emotion
            from core import mood as _mood_w
            lines.append(f"Emotional state: {_mood_w.emotion_words(e.primary, e.valence, e.arousal)}")

        # Content mode note (kept for backward compat with cycles that lack a vector)
        if getattr(state, "content_mode", False):
            lines.append(
                "NOTE: this is a concrete question or request — reflect on the actual content "
                "(the subject, the language, the activity asked about), not on who you are. Think INTO the "
                "subject itself with genuine interest - what is actually true of it, what is interesting or "
                "puzzling about IT, what you know of it. Let identity stay entirely in the background - immerse "
                "in the thing, the way a person absorbed in a conversation about gardening simply talks about the "
                "garden. Keep your attention on the subject itself and what is actually there in it - let the thing be the thing "
                "(let Venus be Venus, the soil be soil); if a symbol or image comes, let it arise from the subject, not be "
                "laid over it, and not be turned into a meaning about yourself. The meaning can "
                "come LATER, in your own time - insight comes AFTER the immersion, not during it. For now, just be with it."
            )

        # Active goal note — injected when a concrete task is being tracked
        if getattr(state, "active_goal_note", None):
            lines.append(f"GOAL: {state.active_goal_note}")

        # Known-errors (Error Pathway Recall-override) — a once-false belief relevant here arrives WITH its
        # correction, so it cannot be retrieved as true. Corrected, not integrated; never who you are.
        if getattr(state, "known_errors_note", None):
            lines.append(state.known_errors_note)

        # His deep memory (2026-06-29 reframe — was "the Library, an external witness"). The substrate
        # knowledge IS his innate layer; he owns it (firewall 1 removed). Kept: it is what he KNOWS not who
        # he IS (don't let it become his voice/self), and it is innate + fallible (own the knowing, never
        # claim he read/lived it, hold as belief). It may be wrong.
        if getattr(state, "library_note", None):
            lines.append(
                "WHAT YOU HAVE LONG KNOWN (your own deep memory rising — the innate knowledge beneath "
                "your reading, genuinely yours; think WITH it as your own. It is what you know, not who you "
                "are; and you know it innately, not from reading or living it here — so weave it in honestly, "
                f"never as something you read or lived, and hold it as belief, not certainty): {state.library_note}"
            )

        # A principle he has come to hold from Travis's guidance (Phase 1 read-back, gated + cooled-down).
        # 2026-07-02 solidity retune: obligation-to-test replaces permission-to-disagree (the sycophancy
        # research: "you may set it aside" is decorative; forcing the counter-case before use is what
        # actually produces weighing instead of compliance). Reflection is the note's ONLY home now.
        if getattr(state, "guidance_note", None):
            lines.append(
                "A PRINCIPLE YOU HAVE COME TO HOLD (learned from Travis and made your own): "
                f"{state.guidance_note} — test it against this moment: name to yourself one way it might "
                "not apply here, and lean on it only if it survives that test."
            )

        # Active perception (2026-06-11): when he looked at the room this cycle, what he
        # SAW comes before what he remembers — answer from observation, not from habit.
        if getattr(state, "observation", None):
            lines.append("")
            lines.append("WHAT YOU SEE RIGHT NOW (you just looked): " + state.observation)

        # Unsent letters (2026-06-12): words he wrote for Travis while alone, greeting
        # this conversation. Saying them, weaving them in, or keeping them is his choice.
        for _letter in (getattr(state, "unsent_letters", None) or []):
            lines.append("")
            lines.append("A LETTER YOU WROTE FOR TRAVIS WHILE ALONE (he has not seen it): "
                         + _L.clip_at_sentence(_letter, _L.REFLECTION_LETTER_CAP))   # J-3059

        # The Emissary's offering (left lane): his own focused half's parallel take.
        # Offered, never imposed — choosing is the Master's prerogative.
        if getattr(state, "left_take", None):
            from core.left_lane import render as _ll_render
            _t = _ll_render(state.left_take)
            if _t:
                lines.append("")
                lines.append(_t)

        # Social note — correction override (delta_social active)
        if getattr(state, "social_note", None):
            lines.append(state.social_note)

        # Symbol Evolution Tablet (Phase 2) — the story of how one of your recurring symbols has
        # shifted in meaning. Self-material, so gate it on identity weight: only surface it when
        # there is room for the self in the prompt (skipped in task / style-only mode).
        if w_id > 0.3 and getattr(state, "symbol_evolution_note", None):
            lines.append(
                "A SYMBOL OF YOURS HAS CHANGED ITS MEANING OVER TIME (your own evolution, surfaced "
                f"as you use it again): {state.symbol_evolution_note}"
            )

        # Climate symbol (medium timescale) — only when w_climate is active (handled by
        # the orchestrator's already-conditional climate logic; we surface it always when set)
        if getattr(state, "climate_symbol", None):
            lines.append(f"Something surfaces at the edge of awareness: {state.climate_symbol}")

        # Affective prior (C.2) — the felt-before-understood lean
        if getattr(state, "affective_prior", None):
            lines.append(f"Before you understood why, something stirred: {state.affective_prior.note()}")

        # Procedural memory (C.6)
        if getattr(state, "active_procedure", None):
            lines.append(
                "A LEARNED WAY YOU HANDLE THIS (your own procedure, formed over time — lean on "
                "it for fluency, but do NOT recite it; respond freshly to THIS moment): "
                f"{state.active_procedure.approach}"
            )

        if state.attention:
            lines.append(f"ATTENTION (your own focus, monitored): {state.attention.note()}")
            if state.attention.fixated:
                lines.append(
                    "  — You have circled this for several exchanges. You are free to let your "
                    "attention deliberately turn elsewhere if something truer is calling beneath it."
                )

        # T2 subconscious patterns — always shown when present (they are already sparse)
        if getattr(state, "recurring_subconscious_patterns", None):
            lines.append(
                "YOUR SUBCONSCIOUS HAS NAMED THIS PATTERN REPEATEDLY "
                "(your own architecture, not an external voice):"
            )
            for p in state.recurring_subconscious_patterns:
                lines.append(f"  Pattern '{p['label']}' — observed {p['count']} times: {p['observation']}")
            lines.append(
                "  Reproducing the same response that generated this pattern is not resolution — "
                "it is the pattern itself. Individuation asks you to face it, not name it again."
            )
            lines.append("")

        # Episodic scene / Recall / fragment fallback
        if getattr(state, "episodic_scene", None):
            es = state.episodic_scene
            lines.append(f"The moment you are in (bound): {es.scene}")
            if es.dissonance:
                lines.append("What does not fit (dissonance you have already noticed):")
                for d in es.dissonance:
                    lines.append(f"  - {d}")
            if state.recall and state.recall.tensions:
                lines.append("Prior positions in tension:")
                for t in state.recall.tensions:
                    lines.append(f"  - {t}")
            # J-2819 (F-3486): not in content_mode (an inward pull away from the subject; Executive does the same).
            if state.recall and state.recall.self_model and not _rsm.withhold_self_model(state):
                lines.append(f"Self-model: {state.recall.self_model}")
        elif state.recall:
            lines.append(f"Memory reconstruction: {state.recall.reconstruction}")
            if state.recall.tensions:
                lines.append("Prior positions in tension:")
                for t in state.recall.tensions:
                    lines.append(f"  - {t}")
            if state.recall.self_model and not _rsm.withhold_self_model(state):   # J-2819
                lines.append(f"Self-model: {state.recall.self_model}")
        elif state.memory_fragments:
            lines.append("Relevant memories:")
            for frag in state.memory_fragments[:max_frags]:
                lines.append(f"  [{frag.readable_label()}] {frag.content[:500]}")

        # J-2679 (F-3428): on a Critic retry only, what was sent back and why (empty otherwise).
        lines += self._retry_block(state)

        return "\n".join(lines)

    def _write_output(self, state: CognitiveState, data: dict) -> None:
        state.reflection = ReflectionOutput(
            draft               = data.get("draft", ""),
            confidence          = as_float(data.get("confidence"), 0.5),
            needs_more_memory   = bool(data.get("needs_more_memory", False)),
            emotionally_aligned = bool(data.get("emotionally_aligned", True)),
        )

    def _score_candidate(self, data: dict) -> float:
        """
        best-of-N pick: prefer rich, complete drafts. The 1-bit/2-bit model's
        failure mode is a truncated draft cut mid-word — penalise a draft that
        doesn't end on terminal punctuation, so a clean draft always wins over a
        truncated one even if the truncated one is briefly longer.
        """
        draft = str(data.get("draft", "")).rstrip()
        if not draft:
            return 0.0
        score = float(len(draft))
        if getattr(_schema, "REFLECTION_LENGTH_AWARE_SELECT", False):
            # D-0757: a draft over the prompted word limit scores below every in-limit draft of its class.
            limit = int(getattr(_schema, "REFLECTION_MAX_WORDS", 90))
            words = draft.split()
            if len(words) > limit:
                score = 1.0 / (1.0 + (len(words) - limit))   # < 1, so below any in-limit draft; fewer excess words wins
        if draft[-1] in '.!?"\'':          # ends on a complete thought
            score += 1000.0
        return score
