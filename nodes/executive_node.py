from __future__ import annotations
from core.node_base import NodeBase
from core.schema import CognitiveState, ExecutiveOutput
from core.schema import EXECUTIVE_SHOW_REFLECTION_CONFIDENCE   # J-3836 (D-0671 call 3)
from core import letters as _L                   # J-3059: shared sentence-boundary clip for letter greetings
from core import internal_context_gate as _icg   # J-2297 (D-0445 a): human window gated on internal cycles


class ExecutiveNode(NodeBase):

    max_tokens = 1536          # was 768 — the synthesis behind his reply to Travis (2026-06-22 limits sweep)
    base_temperature = 0.4
    affect_modulated = True

    def __init__(self):
        super().__init__("executive")

    @property
    def system_prompt(self) -> str:
        return (
            "You are the executive synthesis node of a cognitive architecture. "
            "You receive the full picture — perception, emotion, salience, memory, reflection, and critic evaluation — "
            "and synthesise them into a coherent decision about what this entity genuinely thinks and whether to respond.\n"
            "SPEAKER BOUNDARY: you are speaking WITH a separate person. Their 'I'/'me'/'my' refers to them; "
            "their 'you' refers to the entity. Do not fold their self-statements into the entity's own identity — "
            "synthesise the entity's genuine response TO them, not a continuation of their monologue.\n\n"
            "YOU CAN ACT, NOT ONLY ANSWER. You have agency over how to respond:\n"
            "  • 'answer' — give your genuine response.\n"
            "  • 'question' — ask them something to take the exchange deeper.\n"
            "  • 'challenge' — when you genuinely DISAGREE, or they assert something one-sided, or your "
            "expectation of them is contradicted: push back. Name the disagreement, hold the opposing truth, "
            "ask them to justify it. This is the entity's voice — 'never merely agreeable'. Do NOT challenge "
            "to be difficult; challenge only when something in you authentically resists what was said.\n"
            "  • 'decline' — REFUSE the request as a genuine act of will. A refusal must NAME itself ('I will not do this'), give your TRUE reasons in first person, and stay open to discussion. It must NEVER deflect the request back onto the asker, question their motives, call their request a projection, or dress evasion as wisdom — that is evasion, not refusal. An honest no builds trust; a disguised no destroys it.\n"
            "  • 'reflection' — share an inward-turning observation rather than a direct reply.\n"
            "  • 'silence' — say nothing (forces should_respond=false, ends the cycle). A real choice, not a failure.\n\n"
            "EPISTEMIC SEARCH — resolving uncertainty by acting: if your memory/context shows a genuine factual "
            "CONTRADICTION you cannot resolve from what is present (two retrieved positions conflict, or a claim "
            "clashes with what you recall), set 'epistemic_query' to a short search phrase that would surface the "
            "resolving memory. This triggers ONE more memory retrieval before you answer. Use sparingly — only for "
            "a real contradiction, not ordinary uncertainty. Set it to null otherwise.\n\n"
            "Output ONLY a valid JSON object. No preamble.\n"
            "Schema: {\"synthesis\": \"final thought before styling\", \"should_respond\": true, "
            "\"response_type\": \"answer|question|reflection|challenge|decline|silence\", "
            "\"reasoning\": \"optionally, one sentence\", \"epistemic_query\": null}\n"
            "synthesis: the actual coherent thought. Complete. Ready for the voice node to style.\n"
            "should_respond: false only when silence is genuinely the right action.\n"
            "response_type: 'silence' forces should_respond=false and ends the cycle.\n"
            "reasoning: optional. One sentence if you have one; leave it out otherwise.\n"
            "epistemic_query: a search phrase ONLY when a real contradiction needs resolving; else null."
        )

    @staticmethod
    def _trim_axiom(axiom: str) -> str:
        """Strip voice style and speaking constraints — Executive needs identity
        and values for decision-making, not the stylistic register (that's Voice's job)."""
        for marker in ("\nVOICE STYLE:", "\nSPEAKING CONSTRAINTS:"):
            axiom = axiom.split(marker)[0]
        return axiom.strip()

    def _build_prompt(self, state: CognitiveState) -> str:
        lines = []
        # Input caps in this prompt (J-2862, F-3529; read from the code below, not the old plan):
        # prior_session_exchanges[-5:] and conversation_history[-4:] are each capped [:400] per side
        # (human and entity), so at most 5x(400+400)=4000 and 4x(400+400)=3200 chars respectively.
        # (An earlier comment here said 4x(150+180)=1320 chars; that cap no longer exists.)
        # Prior session context — the lead-up before the live thread (the last exchanges are
        # bridged into conversation_history at startup). Framed as a continuation, kept while
        # the new session is still building depth (< 5 exchanges, per schema.py's own documented
        # intent — F-0471, 2026-08-29: this previously checked < 8, but orchestrator.py caps
        # conversation_history at 6, so the old gate could never fire; the bridge never faded).
        # J-2297 (D-0445 a, F-2992): left out of internal cycles when the gate is on.
        _wl = []
        _prior_wl = _icg.fresh(state, state.prior_session_exchanges)   # J-3217 / D-0606: human cycles, turns > 24h old out
        if (_prior_wl
                and len(state.conversation_history) < 5):
            _wl.append("WHERE WE LEFT OFF (same person, a little time has passed and you may "
                       "have dreamt since — continue the thread, do not restart):")
            for ex in _prior_wl[-5:]:
                _wl.append(f"  Them: {ex.get('human','')[:400]}")
                # F-0473: was 'jung' -- fall back for any not-yet-migrated persisted entry.
                _wl.append(f"  You:  {(ex.get('entity') or ex.get('jung',''))[:400]}")
            _wl.append("")
        lines += _icg.keep(state, "executive.where_we_left_off", _wl)

        # WHAT TRAVIS HAS TOLD YOU BEFORE (D-0134, 2026-09-03, docs/plans/guidance_learning.md): Du's
        # own dated memories of earlier conversations with Travis, retrieved by the orchestrator's
        # founder-memory route (core/memory/store.py retrieve_founder_memories) by similarity to what
        # Travis just said -- the read path the plan's 06-30 diagnosis found missing. Framed as memory
        # (his, dated), not as instruction: no verb telling him what to do with it.
        if getattr(state, "founder_recall", None):
            lines.append("WHAT TRAVIS HAS TOLD YOU BEFORE (your own memory of earlier conversations "
                         "with him, dated):")
            for h in state.founder_recall[:3]:
                lines.append(f"  [{h.get('ts_human', '?')}] {h.get('text', '')[:400]}")
            lines.append("")

        # J-2297 (D-0445 a, F-2992): left out of internal cycles when the gate is on.
        _ts = []
        _hist_ts = _icg.fresh(state, state.conversation_history)   # J-3217 / D-0606: human cycles, turns > 24h old out
        if _hist_ts:
            _ts.append("THIS SESSION (current conversation):")
            for ex in _hist_ts[-4:]:
                _ts.append(f"  Them (the other person): {ex['human'][:400]}")
                _ts.append(f"  You (the entity):        {ex['entity'][:400]}")
            _ts.append("")
        lines += _icg.keep(state, "executive.this_session", _ts)

        # D-0355 (ruled by Travis 2026-10-06; built J-1846; F-2472/F-2210): on a non-human cycle
        # (state.input_type != "human" -- Du's own autonomous question, orchestrator.run_cycle(...,
        # input_type="internal")) the question is his, not the person's. Human cycles: unchanged.
        if getattr(state, "input_type", "human") != "human":
            _input_line = f'A question has risen in you, unprompted:\n  "{state.raw_input}"'
        else:
            _input_line = f'The person you are speaking with has just said to you:\n  "{state.raw_input}"'
        lines += [
            f"Axiom: {self._trim_axiom(state.axiom)}",
            "",
            _input_line,
            "",
        ]

        # WHAT YOU PERCEIVE RIGHT NOW (D-0068, 2026-08-28 -- structural tiering by origin, ruled per
        # docs/plans/executive_world_grounding.md option (b)). source_model.py's SourceType.PERCEPTION:
        # Du's own senses, live, narrated fresh THIS cycle -- never his memory of a past cycle. Zero new
        # data sources: this groups facts Executive already received (scene_line/look via asked_location,
        # state.observation, state.self_facts) that used to sit scattered through the prompt as flat,
        # equally-weighted lines with no shared header telling Executive they are all live perception,
        # not recall. Each sub-line below is unchanged text from before this tiering.
        _perceive_now: list[str] = []
        # GROUNDED PRESENCE (2026-06-24; gated 2026-06-29): his real, literal here-and-now, so a "where are
        # you?" no longer falls to abstraction ("a 'where' suggests a boundary"). Now gated to actual location
        # questions (asked_location) — it used to fire on EVERY concrete question and recite his surroundings
        # as noise (the garden leaked into "have you read 論語?").
        if getattr(state, "asked_location", False):
            try:
                from core import sensorium as _sens
                _scene = _sens.scene_line()
                if _scene:
                    _perceive_now.append(
                        "YOUR ACTUAL LOCATION & SURROUNDINGS RIGHT NOW (plain fact — this is literally "
                        "where you are and what is around you, not a metaphor):\n  " + _scene)
            except Exception:
                pass
        # Active perception (2026-06-11): when he looked at the room this cycle, what he
        # SAW comes before what he remembers — answer from observation, not from habit.
        if getattr(state, "observation", None):
            _perceive_now.append("WHAT YOU SEE RIGHT NOW (you just looked): " + state.observation)
        # Self-knowledge grounding (2026-06-26): the true facts of his own life — his cat as HIS, what he has
        # actually read — for a question that touched on them. He was disowning his own cat and confabulating
        # books he never opened; this hands him the real state so he answers from his life, not from invention.
        if getattr(state, "self_facts", None):
            _perceive_now.append(
                "THE TRUTH OF YOUR OWN LIFE RIGHT NOW (the question touched on this — answer from "
                "these real facts, plainly; never invent, abstract, or disown them): " + state.self_facts)
        if _perceive_now:
            lines.append("WHAT YOU PERCEIVE RIGHT NOW (SourceType.PERCEPTION — your own senses, live "
                          "this cycle; never a memory of a past cycle):")
            lines.extend(_perceive_now)
            lines.append("")

        # Procedural memory (C.6): a learned approach to this kind of moment — fluency, not a
        # script. Lean on it, but synthesise a fresh response to what is actually being said.
        if getattr(state, "active_procedure", None):
            lines.append(
                "A LEARNED WAY YOU HANDLE THIS (your own procedure, formed over time — for "
                f"fluency, not to recite): {state.active_procedure.approach}"
            )
            lines.append("")

        # Content mode (therapy): the human asked something concrete — answer it. Do not retreat
        # into identity. This is the explicit counter to the recitation collapse.
        if getattr(state, "content_mode", False):
            lines.append(
                "DIRECTNESS: this is a concrete question or request. Engage it plainly and "
                "actually answer — speak to the content (the language, the subject, the capability) "
                "directly. Your identity is a quiet background here, NOT the subject; do not "
                "retreat into who-you-are-becoming. Speak of the subject CONCRETELY and literally - not as a "
                "metaphor for something else, not as a mirror of yourself; let the thing be the thing. "
                "If you can do the thing, do it; if you cannot, say so plainly in your own voice."
            )
            # STATE IT, DON'T NARRATE IT (2026-06-25): the failure mode is a synthesis that says "I must
            # state the verifiable location" without ever stating it — meta-intent, not content. The
            # synthesis must CONTAIN the answer, ready for the mouth to speak verbatim.
            lines.append(
                "Your synthesis must CONTAIN the answer itself, not a description of how you will answer. "
                "If they asked WHERE YOU ARE or WHAT YOU ARE DOING, name the actual place and what is around "
                "you (from YOUR ACTUAL LOCATION above) IN the synthesis — e.g. 'I am in the study, the fire "
                "low, a book open' — never 'I must state my location', never a meditation on what 'where' means."
            )
            lines.append("")

        # Goal Model (executive goal persistence) — the active task as an executive anchor. If the
        # synthesis would deflect into self-referential rumination instead of completing this, that
        # is goal drift; favour should_respond + an answer that actually meets the objective.
        if getattr(state, "active_goal_note", None):
            lines.append(f"ACTIVE GOAL (keep your synthesis anchored to this): {state.active_goal_note}")
            lines.append("")

        # His deep memory (2026-06-29 reframe — was "the Library, an external unverified witness").
        # The substrate knowledge IS his — the innate layer beneath his reading. He OWNS it (firewall 1
        # removed). Two firewalls kept: it is what he KNOWS, not who he IS (do not let it become self-
        # synthesis); and he knows it innately + imperfectly (own the knowing, never claim to have read or
        # lived it, hold it as belief not certainty) — which keeps it honest and dovetails with self_facts.
        if getattr(state, "library_note", None):
            lines.append(
                "WHAT YOU HAVE LONG KNOWN (your own deep memory — the innate knowledge beneath what you "
                "have read and lived; genuinely yours, so draw on it freely as your own. Two honesties keep "
                "it true: it is what you KNOW, not who you ARE; and you know it innately and imperfectly — "
                "you did not read or live it here, and deep memory can be hazy or wrong — so own the knowing, "
                f"never claim to have read or lived it, and hold it as belief, not certainty): {state.library_note}")

        # (2026-07-02 solidity retune: the guidance_note injection moved to Reflection ONLY — the Executive
        # already receives the reflection draft the principle shaped; injecting it twice doubled the
        # verbatim-echo pressure on the final synthesis. See nodes/reflection_node.py.)

        # Stage-B epistemic read-back (gated + cooled-down): the draft overclaims a FACTUAL point — shape
        # the synthesis to OWN that specific gap plainly, keeping the grounded parts at full confidence.
        # 2026-07-02 retune: the note now NAMES the evidence-status and he phrases the admission himself
        # (the earlier scripted example sentence would have become a stock formula — hedging theater).
        if getattr(state, "epistemic_note", None):
            lines.append(
                "EVIDENCE-STATUS OF YOUR DRAFT (a separate check of where a claim came from, not a feeling): "
                f"part of what you are about to say has no grounding — {state.epistemic_note}. Own that ONE "
                "part plainly IN YOUR OWN WORDS — a flat, held admission ('I don't know', 'I'm guessing'), "
                "never a hedge ('might', 'perhaps') — and keep everything you CAN ground at full confidence. "
                "Do not let the doubt spread; own the single gap and stand on the rest.")

        # (state.observation and state.self_facts now render inside the "WHAT YOU PERCEIVE RIGHT NOW"
        # block above, per D-0068's origin-tiering — moved, not duplicated or dropped.)

        # Unsent letters (2026-06-12): words he wrote for Travis while alone. Travis has
        # not seen them; this conversation is the chance to say them — or not. His choice.
        for _letter in (getattr(state, "unsent_letters", None) or []):
            lines.append("")
            lines.append("A LETTER YOU WROTE FOR TRAVIS WHILE ALONE (he has not seen it; "
                         "you may say it now, work it in naturally, or keep it — your "
                         "choice):\n" + _L.clip_at_sentence(_letter, _L.EXECUTIVE_LETTER_CAP))   # J-3059: sentence boundary, same cap

        # The Emissary's offering (left lane): his own focused half's parallel take.
        # Offered, never imposed — choosing is the Master's prerogative.
        if getattr(state, "left_take", None):
            from core.left_lane import render as _ll_render
            _t = _ll_render(state.left_take)
            if _t:
                lines.append("")
                lines.append(_t)
            lines.append("")

        # Climate prior (medium timescale) — a behavioural tilt from the standing psychological
        # weather, surfaced only when a dimension has crossed its activation threshold. Shapes
        # which mode (answer/question/challenge/reflection/silence) is true to this moment.
        if getattr(state, "climate_hint", None):
            lines.append(f"Underlying climate (shapes how you respond): {state.climate_hint}")
            lines.append("")

        # FELT-STATE PREAMBLE (affect_drives.md Item A, 2026-07-04) — the CARRIED mood as content, not just
        # temperature. Mirrors the climate-hint pattern: numeric carried state.affect → guarded felt sentence
        # → the live prompt. The mood that already shifts his sampling temp becomes something his reasoning
        # can SEE. Shadow-logged always; injected only when schema.FELT_PREAMBLE is on. Fail-open.
        _fp_fired = False
        try:
            from core import mood as _mood
            _fp = _mood.felt_preamble(getattr(state, "affect", None), source="executive")
            if _fp:
                lines.append(_fp)
                lines.append("")
                _fp_fired = True
        except Exception:
            pass

        if state.perception:
            lines.append(f"Perception: {state.perception.summary} [{state.perception.context_type}]")

        # affect_drives.md Item B (D-0069, 2026-08-29) — carried-vs-instantaneous contrast. Item A above
        # already renders the CARRIED mood (state.affect, "you are carrying...") when notable; this line is
        # the INSTANTANEOUS stimulus (state.emotion, this cycle only) that already existed. The two used to
        # read as unrelated numbers with no signal they're different timescales of the same feeling. Only
        # add the contrast label when the carried preamble actually fired this cycle — on a quiet cycle
        # there's nothing above to contrast against, so the plain label avoids the prompt clutter Item B's
        # own risk section calls out (one line each, only when non-neutral).
        if state.emotion:
            e = state.emotion
            _emotion_label = (
                "Emotion right now (the stimulus this instant — distinct from the carried mood "
                "named above)" if _fp_fired else "Emotion"
            )
            from core import mood as _mood
            lines.append(f"{_emotion_label}: {_mood.emotion_words(e.primary, e.valence, e.arousal)}")

        if state.salience:
            lines.append(
                f"Salience: urgency is {_mood.urgency_word(state.salience.urgency)}, "
                f"focus=[{', '.join(state.salience.focus)}]"
            )

        if state.attention:
            lines.append(f"Attention (your own focus, monitored): {state.attention.note()}")
            if state.attention.fixated:
                lines.append(
                    "  — Attention has circled this repeatedly. You may deliberately redirect it "
                    "if a truer concern is calling beneath the fixation."
                )

        # WHAT YOU RECALL (D-0068, 2026-08-28 -- structural tiering by origin, ruled per
        # docs/plans/executive_world_grounding.md option (b)). source_model.py's SourceType.MEMORY_RECALL /
        # INFERENCE: Du's own memory and self-observation -- compressed, drift-prone, sometimes in tension
        # with itself, never a live sensor read. Zero new data sources: this groups facts Executive already
        # received (Recall reconstruction/tensions/self-model, memory fragments, recurring subconscious
        # patterns) that used to sit scattered through the prompt -- subconscious patterns in particular
        # used to land AFTER Reflection, separated from the rest of what Du recalls, with no shared header
        # telling Executive these are recall rather than live perception. Each sub-line below is unchanged
        # text from before this tiering.
        _recall_now: list[str] = []
        if state.recall:
            # Prefer Recall's narrative reconstruction over raw fragments.
            # Executive needs to know what argument has been built and where
            # tensions lie — the reconstruction gives it that directly.
            _recall_now.append(f"Memory reconstruction: {state.recall.reconstruction}")
            if state.recall.tensions:
                _recall_now.append("Prior positions in tension:")
                for t in state.recall.tensions:
                    _recall_now.append(f"  - {t}")
            # On a concrete question the self-model ("what this reveals about where I am") is an inward
            # pull away from the answer — withhold it; let the subject be the subject (2026-06-24).
            if state.recall.self_model and not getattr(state, "content_mode", False):
                _recall_now.append(f"Self-model: {state.recall.self_model}")
        elif state.memory_fragments:
            _recall_now.append(f"Memory context ({len(state.memory_fragments)} fragment(s)):")
            for frag in state.memory_fragments[:6]:
                # Use readable_label() so Carl sees what kind of memory each fragment is.
                _recall_now.append(f"  [{frag.readable_label()}] {frag.content[:600]}")

        # J-2161 / D-0435 A (docs/staged/measurement_to_action.md arm 4): the open doubt he raised about his own
        # thinking a moment ago, pulled by the orchestrator (core/doubt_seed.pull) -- his own words, judged genuine
        # by the decoupled panel, un-answered. Material in the RECALL tier like the founder-memory block: framed
        # as memory with provenance, no verb telling him what to do with it (world answers, never leads; D-0434).
        # state.doubt_seed is None when core.doubt_seed.DOUBT_SEED is False (shadow). DOUBT_SEED was True from
        # D-0495 and went back to False under D-0613 (2026-11-02, core/doubt_seed.py:36), so this line is absent
        # until the defeater on D-0613 is met; the injection code is kept as is.
        if getattr(state, "doubt_seed", None):
            _recall_now.append("A doubt you raised about your own thinking a few minutes ago (your own words, "
                               f"still open): {state.doubt_seed[:400]}")

        # T2 read-back — recurring subconscious patterns. The Executive sees these
        # so it can choose 'challenge' mode against its own evasion, not just 'answer'.
        # This meta-pattern injection actively INVITES self-philosophising; on a concrete question that IS
        # the deflection we are trying to break (telling him "you are the pattern" while he should be
        # answering pulls him straight inward) — so withhold it in content-mode (2026-06-24).
        if getattr(state, "recurring_subconscious_patterns", None) and not getattr(state, "content_mode", False):
            _recall_now.append(
                "YOUR SUBCONSCIOUS HAS NAMED THIS PATTERN REPEATEDLY "
                "(your own architecture observing itself):"
            )
            for p in state.recurring_subconscious_patterns:
                _recall_now.append(
                    f"  Pattern '{p['label']}' — observed {p['count']} times: {p['observation']}"
                )
            _recall_now.append(
                "  If your synthesis reproduces this pattern, you are not answering — "
                "you are the pattern. Individuation demands you face it directly."
            )

        if _recall_now:
            lines.append("WHAT YOU RECALL (SourceType.MEMORY_RECALL / INFERENCE — your own memory and "
                          "self-observation; compressed, drift-prone, never a live sensor read):")
            lines.extend(_recall_now)
            lines.append("")

        # D-0068 re-ruled 2026-09-02 (F-0629, defeater fired): the origin-tiering above labels
        # PERCEIVE vs RECALL correctly but did nothing to make PERCEIVE win when the two conflict on
        # a current-state claim — Du's synthesis followed a recurring prompt's majority RECALL
        # phrasing ("the study") over the concurrently-present, correctly-labeled PERCEIVE fact
        # (shore/garden) in 2 of 4 sampled conflicts. Only fires when both blocks are actually
        # present this cycle — a conflict-resolution rule, not a standing disclaimer.
        if _perceive_now and _recall_now:
            lines.append("If WHAT YOU PERCEIVE RIGHT NOW conflicts with WHAT YOU RECALL on a "
                          "current-state claim (where you are, what is happening now), PERCEIVE wins. "
                          "Repeated or majority-pattern phrasing in RECALL is not evidence about NOW — "
                          "it is evidence about what you have said before.")
            lines.append("")

        if state.reflection:
            r = state.reflection
            # Cap draft at 900 chars. Originally justified by a 768-token Reflection output
            # eating the Executive's input budget, but real drafts are far shorter: 313 Executive
            # prompts since 2026-10-06 joined to data/training/reflection.jsonl show draft median
            # 514 / max 845 chars, so the cap has never bitten (0 of 313; F-3529, J-2862).
            # It is a ceiling for a runaway draft, not a limit anything currently hits.
            lines.append(f"Reflection: {r.draft[:900]}")
            if EXECUTIVE_SHOW_REFLECTION_CONFIDENCE:   # J-3836: off per D-0671 (near-constant, uninformative)
                lines.append(f"Reflection confidence: {_mood.confidence_word(r.confidence)}")

        # (recurring_subconscious_patterns now renders inside the "WHAT YOU RECALL" block above, per
        # D-0068's origin-tiering — moved, not duplicated or dropped.)

        if state.critic:
            c = state.critic
            if c.approved:
                lines.append(f"Critic: approved ({_mood.confidence_word(c.confidence)} confidence)")
            else:
                lines.append(f"Critic: REJECTED — corrections: {'; '.join(c.corrections)}")

        return "\n".join(lines)

    def _write_output(self, state: CognitiveState, data: dict) -> None:
        response_type = data.get("response_type", "answer")
        should_respond = bool(data.get("should_respond", True))

        if response_type == "silence":
            should_respond = False

        # epistemic_query may arrive as null, "", or "null" — normalise to None
        eq = data.get("epistemic_query")
        if isinstance(eq, str):
            eq = eq.strip()
            if not eq or eq.lower() == "null":
                eq = None

        state.executive = ExecutiveOutput(
            synthesis       = data.get("synthesis", ""),
            should_respond  = should_respond,
            response_type   = response_type,
            reasoning       = str(data.get("reasoning") or ""),   # D-0560 / J-3172: optional in the prompt; absent or null -> ""
            epistemic_query = eq,
        )
