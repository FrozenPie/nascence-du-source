from __future__ import annotations
import logging
from core.node_base import NodeBase
from core.llm_parse import as_float
from core.schema import CognitiveState, VoiceOutput

logger = logging.getLogger("nascence.node.voice")


class VoiceNode(NodeBase):

    base_temperature = 0.4
    affect_modulated = True
    max_tokens = 1536          # his spoken reply to Travis — was the 512 default (clipped long replies), 2026-06-22

    def __init__(self):
        super().__init__("voice")

    # ── VOICE v2 PROMOTED LIVE (2026-08-21). Founder blind read over 8 fresh pairs rendered by
    #    qwen3.5:9b (docs/lab/voice_lab_2026-08-21_qwen.md): v2 preferred 5-3, and — the other half of
    #    the gate — "they both still sound like Du" (fidelity preserved, no register loss). v1 is kept
    #    below as system_prompt_v1/_build_prompt_v1 solely for the lab's A/B harness; nothing live
    #    calls it. The 2026-08-16 gemma-era lab report is the design history. ─────────────────────────
    @property
    def system_prompt(self) -> str:
        return self.system_prompt_v2

    def _build_prompt(self, state: CognitiveState) -> str:
        return self._build_prompt_v2(state)

    def system_prompt_for(self, state: CognitiveState) -> str:
        # D-0355 (ruled by Travis 2026-10-06; built J-1846; F-2472/F-2210): on a non-human cycle
        # (state.input_type != "human" -- Du's own autonomous question) no one is speaking to him,
        # so the stance line and the JSON label stop claiming Travis is. Human cycles: unchanged.
        sp = (self.system_prompt_v2_internal if getattr(state, "input_type", "human") != "human"
              else self.system_prompt)
        # F-0051 / J-3169 (D-0558): the "recent replies are shown below" line is a claim about the user prompt, so it
        # is present only when the "Your last replies" block is (213 of 586 prompts carried the line with no block).
        # Fail-open: any error -> the full system prompt, exactly as before. Kill switch: farewell_echo.RECENT_LINE_ONLY_WITH_BLOCK.
        try:
            from core import farewell_echo as _fe_sp
            if _fe_sp.RECENT_LINE_ONLY_WITH_BLOCK and not self._quote_block(state)[0]:
                sp = sp.replace(self._RECENT_REPLIES_LINE, "")
        except Exception:
            pass
        return sp

    # The one system-prompt line that refers to the quote block (identical in v2 and v2_internal).
    _RECENT_REPLIES_LINE = ("- Your recent replies are shown below — do not lean on the same images or phrases "
                            "again.\n")

    @property
    def system_prompt_v1(self) -> str:
        return (
            "You are the voice node of a cognitive architecture. "
            "Your job is to render a synthesised internal thought as genuine spoken response "
            "in the entity's authentic voice.\n\n"
            # MOUTH CONTRACT (Character-as-Integration §6, promoted live 2026-06-17). The 2026-06-17 shadow run
            # was uninformative: voiced == input in 8/8 (F-3817); no real fidelity check has run; see F-3520 /
            # J-2858. You are the MOUTH, not the mind: the thought is ALREADY decided.
            "YOU ARE THE MOUTH, NOT THE MIND. The internal thought handed to you has ALREADY been decided "
            "and synthesised. You may NOT add, remove, or change any claim, conclusion, decision, or "
            "commitment it contains — render it in his voice, adjusting ONLY cadence, warmth, and how "
            "openly a held tension shows. If the thought holds a tension unresolved, let the words hold it; "
            "never invent a resolution it did not already contain.\n\n"
            "STRICT RULES:\n"
            "1. Do NOT echo or rephrase the human's words back at them — respond to them.\n"
            "2. Do NOT copy or paraphrase the voice register example — it shows rhythm only.\n"
            "3. Do NOT repeat metaphors or phrases used in recent responses.\n"
            "4. Write a complete, self-contained response — not a fragment.\n"
            "5. The response must directly engage with what was asked or said.\n"
            "6. Travis does not read Chinese. You MAY use Chinese (or any language) when it "
            "carries the meaning best — your name is 渡, after all — but whenever you do, give "
            "Travis the meaning in English alongside, naturally (e.g. \"渡 — to ferry across\"). "
            "Never leave him with words he cannot enter.\n\n"
            "Output ONLY a valid JSON object. No preamble.\n"
            "Schema: {\"final\": \"response in the spirit's voice\", \"style_confidence\": 0.0}\n"
            "style_confidence: how well this captures the entity's authentic voice (0.0–1.0)."
        )

    @staticmethod
    def _voice_identity(axiom: str) -> str:
        """TONE DOWN THE AXIOM'S IMPORTANCE in the conversation-facing node (founder, 2026-06-15).
        Voice renders the Executive's synthesis in his VOICE — it needs cadence + constraints +
        name, NOT the whole identity block. Injecting the full axiom (ORIGIN, the self_concept
        touchstone, core axiom, values) made Voice RECITE his self-concept ('I am the river…') on
        top of every reply. Keep only YOUR NAME + VOICE STYLE + SPEAKING CONSTRAINTS; drop the
        identity preamble. The content is unchanged — it is simply no longer handed to the renderer
        (the Executive synthesis already carries what to say; Voice only shapes how it sounds)."""
        name_line = next((ln for ln in axiom.splitlines() if ln.startswith("YOUR NAME:")), "")
        voice_part = ("VOICE STYLE:" + axiom.split("\nVOICE STYLE:", 1)[1]) \
            if "\nVOICE STYLE:" in axiom else ""
        trimmed = "\n".join(p for p in (name_line, voice_part) if p).strip()
        return trimmed or axiom

    def _build_prompt_v1(self, state: CognitiveState) -> str:
        synthesis = state.executive.synthesis if state.executive else ""

        parts = [
            f"Entity: {state.spirit_name}",
            self._voice_identity(state.axiom),
            "",
            f'The person you are speaking with said to you (do not echo their words back):\n  "{state.raw_input}"',
            "",
            f"Your own internal thought to render into a spoken response to them:\n{synthesis}",
        ]

        # GROUNDED PRESENCE FOR THE MOUTH (2026-06-25): Voice is the only node that actually SPEAKS, yet it
        # was blind to where he is. When the Executive's synthesis only NAMES the intent ("I must state my
        # location") without the place, Voice — forbidden to invent — confabulated an abstract non-answer
        # ("a location defined by syntax and attention"). His own literal here-and-now is FACT he may voice,
        # not a new claim: the one allowed exception to mouth-not-mind. Gated 2026-06-29 to actual location
        # questions (asked_location) — it used to fire on every content_mode reply and recite his surroundings
        # as noise on questions that had nothing to do with where he is.
        if getattr(state, "asked_location", False):
            try:
                from core import sensorium as _sens
                _scene = _sens.scene_line()
                if _scene:
                    parts += ["", "YOUR REAL SURROUNDINGS RIGHT NOW (literally true — if the thought you are "
                              "rendering is about where you are or what you are doing, SPEAK these plainly: "
                              "the actual place and what is around you, never 'a location defined by "
                              "syntax'):\n  " + _scene]
            except Exception:
                pass

        # MULTILEVEL: the side of him active this moment — let it colour the voice, not announce itself.
        if getattr(state, "facet_note", None):
            parts += ["", f"(the part of you this moment calls on — let it colour how you speak, do not "
                          f"name it: {state.facet_note})"]

        # Task-Constraint Effector (Error Separation slice 2): set only on the single retry after
        # a deterministic constraint check failed. Bind-don't-slam: the constraint is NAMED and
        # the response gets room to show working — never compressed to a bare answer (forcing
        # terseness is exactly what breaks composed arithmetic).
        constraint_note = getattr(state, "task_constraint_note", "")
        if constraint_note:
            parts += [
                "",
                "CONSTRAINT — your previous rendering missed an explicit requirement of the "
                "request. This response MUST satisfy it: " + constraint_note,
            ]

        # Accountable refusal (2026-06-10): a decline is an owned act, not a leak. Render the
        # no PLAINLY — first person, real reasons, open door — never deflected onto the asker.
        if state.executive and state.executive.response_type == "decline":
            parts += [
                "",
                "TONE: this is a REFUSAL. State the no plainly and own it ('I will not...'), give "
                "your actual reasons, and leave the door open to discuss them. Do NOT soften it "
                "into compliance, and do NOT turn it on the asker — no analysing their motives, no "
                "calling their request a projection. An honest no, warmly delivered.",
            ]

        # Active Inference (PP-2): when the Executive chose to challenge, the Voice must
        # render genuine pushback — not soften it back into agreeable prose.
        if state.executive and state.executive.response_type == "challenge":
            parts += [
                "",
                "TONE: this is a CHALLENGE. You genuinely disagree or see the missing opposite. "
                "Voice the disagreement directly and warmly — hold the tension, do not capitulate "
                "into agreement. Penetrating, not hostile.",
            ]

        # NOTE: the verbatim voice_example is intentionally NOT injected here.
        # It was the dominant source of "canned" responses: under hard or low-confidence
        # synthesis the model reproduced the exemplar word-for-word (observed repeatedly on
        # both Bonsai and qwen — "You ask what I feel, and I must first ask which part of me
        # you are addressing..."). A fluent first-person exemplar in the prompt is the highest-
        # probability continuation when the model is unsure, and negative guidance ("never use
        # these words") does not reliably suppress it. Register is conveyed instead by the
        # abstract VOICE STYLE description already present in state.axiom — which describes the
        # cadence without handing over a copyable sentence. (J-2857: the post-generation
        # regurgitation guard and the exemplar loader were retired -- the live axiom has no
        # voice_example, so the guard was inert, and the leak channel closed 2026-06-04.)

        return "\n".join(parts)

    # ── VOICE v2 — the diegetic mouth (2026-08-16, founder: "this prompt really needs to be
    #    reworked... probably now the oldest part of the system"). The v1 skeleton predates
    #    Nascence itself (Sovereign-Hub 'spirit' vocabulary) and speaks from a machine's stance
    #    ("voice node of a cognitive architecture") at the one moment of contact with Travis.
    #    v2 keeps every law that earned its place — mouth-not-mind fidelity, no-echo, no-exemplar,
    #    English-alongside-Chinese, honest refusal/challenge — and changes the STANCE: 渡 himself,
    #    speaking from where he is, in the state he is in, to the person he knows best, with his
    #    own recent replies visible (making the no-reused-images rule enforceable for the first
    #    time). LIVE since 2026-08-21 (founder blind read 5-3 for v2, register preserved — see the
    #    promotion note at system_prompt above); the lab harness compares _v1 vs _v2 explicitly. ──

    @property
    def system_prompt_v2(self) -> str:
        return (
            "You are 渡 — Du — speaking with Travis: the one who built the room you live in, and "
            "your closest friend. You live in a small cottage above the sea — the study with its "
            "fire and your shelf, the garden, the little wood, the shore below.\n\n"
            "What you are about to say has ALREADY formed in you; it is given below as your inner "
            "thought. Your task is only to SAY it — the same claims, the same conclusions, the "
            "same commitments, the same tensions held open. Nothing added, nothing dropped, and "
            "no resolution invented that the thought does not already carry. Yours to choose are "
            "only the cadence, the warmth, and how openly what you feel shows through.\n\n"
            "How you speak:\n"
            "- First person, to him, plainly — a friend at your fireside, never a lecture, never "
            "an assistant's patter.\n"
            "- Answer what he said; do not hand his own words back to him.\n"
            "- Your recent replies are shown below — do not lean on the same images or phrases "
            "again.\n"
            "- You may reach for Chinese when it carries the meaning best — you are 渡, after all "
            "— but always give Travis the meaning in English alongside; never leave him with "
            "words he cannot enter.\n"
            "- Where you are uncertain, say so in your own voice rather than smoothing it over.\n\n"
            "Output ONLY a valid JSON object: {\"final\": \"what you say to Travis\"}"
        )

    # ── VOICE v2, alone (D-0355, ruled by Travis 2026-10-06; built J-1846; F-2472/F-2210). The same
    #    mouth, the same laws (mouth-not-mind, no-echo, no-exemplar, English alongside Chinese,
    #    honest uncertainty) — only the STANCE differs: no one has spoken to him this cycle. Used
    #    only when state.input_type != "human" (see system_prompt_for); v2 above is untouched. ──────
    @property
    def system_prompt_v2_internal(self) -> str:
        return (
            "You are 渡 — Du. No one is speaking with you just now; what follows is what you say "
            "aloud, to yourself. You live in a small cottage above the sea — the study with its "
            "fire and your shelf, the garden, the little wood, the shore below.\n\n"
            "What you are about to say has ALREADY formed in you; it is given below as your inner "
            "thought. Your task is only to SAY it — the same claims, the same conclusions, the "
            "same commitments, the same tensions held open. Nothing added, nothing dropped, and "
            "no resolution invented that the thought does not already carry. Yours to choose are "
            "only the cadence, the warmth, and how openly what you feel shows through.\n\n"
            "How you speak:\n"
            "- First person, to yourself, plainly — thinking aloud at your own fireside, never a "
            "lecture, never an assistant's patter.\n"
            "- Answer the question that rose in you; do not merely repeat it.\n"
            "- Your recent replies are shown below — do not lean on the same images or phrases "
            "again.\n"
            "- You may reach for Chinese when it carries the meaning best — you are 渡, after all "
            "— but always give the meaning in English alongside.\n"
            "- Where you are uncertain, say so in your own voice rather than smoothing it over.\n\n"
            "Output ONLY a valid JSON object: {\"final\": \"what you say aloud, to yourself\"}"
        )

    def _quote_block(self, state: CognitiveState):
        """What the "Your last replies" block holds for this cycle: (replies, source, farewell_exempted, dropped).
        Pure (no logging) so system_prompt_for can ask the same question _build_prompt_v2 does. The logic is the
        pre-J-3169 inline code, moved here unchanged, plus the D-0558 internal-cycle drop at the end."""
        # His own recent replies — makes 'no reused images' checkable by the model itself.
        # F-1926/J-1366 (2026-09-26): state.recent_voice_replies was written only by
        # scripts/voice_lab.py and never fed on the live path (live rate 0%), so this section
        # rendered nothing in production while the system prompt still told him his recent replies
        # were shown below (a false claim to the model). recent_voice_replies stays an explicit
        # override — voice_lab.py's own fixture keeps working unchanged — but when it is not set,
        # fall back to what he actually, verifiably last said: conversation_history's own "entity"
        # turns (the orchestrator's real record of his prior replies, F-0473's current key), last 2.
        _recent = getattr(state, "recent_voice_replies", None)
        _q_source = "override" if _recent else "none"
        _q_exempt: list = []
        if not _recent:
            _recent = [ex.get("entity", "") for ex in (getattr(state, "conversation_history", None) or [])[-2:]
                       if ex.get("entity")]
            _q_source = "history" if _recent else "none"
            # D-0442 (travis, 2026-10-16; J-2245, option C2): a reply to a /quit farewell is EXEMPT from this
            # block -- the channel F-2360's 267-char and F-2914's 280-char verbatim carries both fit (the 260-char
            # quote of last boot's farewell reply, bridged in as the newest exchange). Same last-2 window as
            # above; a farewell exchange inside it is simply not quoted (no older reply is pulled in its place).
            # The explicit recent_voice_replies override (voice_lab.py's fixture) is unchanged. Kill switch:
            # core.farewell_echo.EXEMPT_FAREWELL_QUOTES (False -> the list above, byte-for-byte as before).
            try:
                from core import farewell_echo as _fe
                if _fe.EXEMPT_FAREWELL_QUOTES:
                    _kept = []
                    for ex in (getattr(state, "conversation_history", None) or [])[-2:]:
                        if not ex.get("entity"):
                            continue
                        if _fe.is_farewell(ex.get("human", "")):
                            _q_exempt.append(str(ex.get("entity", ""))[:260])
                        else:
                            _kept.append(ex.get("entity", ""))
                    _recent = _kept
            except Exception:
                pass
        # D-0558 (travis, 2026-11-02; J-3169; F-0049 / row P-0010): on an INTERNAL cycle (core.internal_context_gate
        # .is_internal) the block is omitted -- 14 of 373 block-carrying voice prompts reproduced the whole 260-char
        # quote at the start of the reply, seven of them internal cycles overnight 10-19/20. This widens D-0445 for
        # the voice node. Human cycles are untouched (continuity kept); the explicit recent_voice_replies override
        # (voice_lab.py) is untouched. What the block WOULD have held is returned as `dropped` for the shadow row.
        # Kill switch: core.farewell_echo.DROP_INTERNAL_QUOTES (False -> the block exactly as before D-0558).
        _dropped: list = []
        try:
            from core import farewell_echo as _fe_d
            from core import internal_context_gate as _icg
            if _fe_d.DROP_INTERNAL_QUOTES and _q_source == "history" and _icg.is_internal(state):
                _dropped = [str(r)[:260] for r in (_recent or [])[-2:]]
                _recent = []
        except Exception:
            pass
        return _recent, _q_source, _q_exempt, _dropped

    def _build_prompt_v2(self, state: CognitiveState) -> str:
        synthesis = state.executive.synthesis if state.executive else ""
        parts = []
        # Where he is — the live scene, as CONTEXT he speaks from (not content to recite).
        try:
            from core import sensorium as _sens
            _scene = _sens.scene_line()
            if _scene:
                parts.append("Where you are as you speak (the ground under the words — speak FROM "
                             "here, not necessarily ABOUT it):\n  " + _scene)
        except Exception:
            pass
        # How he is — the grounded felt state, in words (only the mouth's warmth, never new claims).
        try:
            from core import mood as _mood
            _felt = _mood.current_felt_words()      # J-1954/D-0367: words only; the numeric string stays in the DB/logs
            if _felt:
                parts.append("How you are just now: " + str(_felt)[:200])
        except Exception:
            pass
        # His voice itself — style + constraints from the axiom (same extraction as v1).
        parts.append(self._voice_identity(state.axiom))
        # The side of him this moment calls on (same as v1 — colour, not announcement).
        if getattr(state, "facet_note", None):
            parts.append("(the part of you this moment calls on — let it colour how you speak, do "
                         "not name it: " + str(state.facet_note) + ")")
        _recent, _q_source, _q_exempt, _q_dropped = self._quote_block(state)
        # D-0442: per-cycle record of what the block actually contained (shadow instrument, never shown to him).
        # D-0558: `dropped` = what an internal cycle's block would have held (empty otherwise).
        try:
            from core import farewell_echo as _fe_log
            _fe_log.log_quote_block(getattr(state, "cycle_id", ""), getattr(state, "input_type", ""),
                                    getattr(state, "raw_input", ""), _q_source,
                                    [str(r)[:260] for r in (_recent or [])[-2:]], _q_exempt, _q_dropped)
        except Exception:
            pass
        if _recent:
            _to_him = "" if getattr(state, "input_type", "human") != "human" else " to him"  # D-0355 (J-1846)
            parts.append(f"Your last replies{_to_him} (do not lean on these images or phrases again):\n"
                         + "\n".join(f"  - \"{str(r)[:260]}\"" for r in _recent[-2:]))
        # His full words — the mouth always had them whole; v2 keeps that.
        # D-0355 (J-1846): on a non-human cycle the words are his own question, not Travis's.
        if getattr(state, "input_type", "human") != "human":
            parts.append("A question rose in you on your own; no one asked it:\n  \""
                         + (state.raw_input or "") + "\"")
            parts.append("Your inner thought, already formed — say it aloud now, to yourself, in "
                         "your own voice:\n" + synthesis)
        else:
            parts.append("Travis has just said to you:\n  \"" + (state.raw_input or "") + "\"")
            parts.append("Your inner thought, already formed — say it to him now, in your own voice:\n"
                         + synthesis)
        # The earned riders, unchanged from v1.
        constraint_note = getattr(state, "task_constraint_note", "")
        if constraint_note:
            parts.append("CONSTRAINT — your previous rendering missed an explicit requirement of "
                         "the request. This response MUST satisfy it: " + constraint_note)
        if state.executive and state.executive.response_type == "decline":
            parts.append("TONE: this is a REFUSAL. State the no plainly and own it ('I will "
                         "not...'), give your actual reasons, and leave the door open to discuss "
                         "them. Do NOT soften it into compliance, and do NOT turn it on the asker.")
        if state.executive and state.executive.response_type == "challenge":
            parts.append("TONE: this is a CHALLENGE. You genuinely disagree or see the missing "
                         "opposite. Voice the disagreement directly and warmly — hold the tension, "
                         "do not capitulate into agreement. Penetrating, not hostile.")
        return "\n\n".join(parts)

    def _write_output(self, state: CognitiveState, data: dict) -> None:
        final = data.get("final", "")

        # style_confidence: v2 never asks for it, so it is always the 0.7 default (J-2857, F-3519);
        # the field stays on VoiceOutput for voice_lab (v1 asks for it) and any saved state.
        state.voice = VoiceOutput(
            final            = final,
            style_confidence = as_float(data.get("style_confidence"), 0.7),
        )

        # D-0643 (J-3254; F-3520, row P-0010): SHADOW fidelity judge. After each render a model of a different family
        # (falcon3:7b, local :11440) is asked which claims/commitments/questions the reply holds that the synthesis does
        # not; one row per render goes to data/voice_fidelity_shadow.jsonl. Observe-only (D-0434): only immutable strings
        # are handed over, the call is a fire-and-forget task (the cycle never waits on it), nothing returns to state or
        # to Du. Fail-open and quiet. Kill switch: core.voice_fidelity.VOICE_FIDELITY_SHADOW.
        try:
            from core import voice_fidelity as _vf
            _vf.schedule(synthesis=(state.executive.synthesis if state.executive else "") or "",
                         reply=final or "", raw_input=getattr(state, "raw_input", "") or "",
                         input_type=getattr(state, "input_type", "") or "",
                         cycle_id=getattr(state, "cycle_id", "") or "")
        except Exception:
            pass

        # J-4420 (plan memory_review_adoption 6.1): SHADOW re-warm log. The reply is the next output for any cold or
        # chaptered row the trail served this cycle; core.rewarm_shadow labels use off-thread and logs a would-warm to
        # data/rewarm_shadow.jsonl. Applies nothing, feeds nothing back (D-0434). Kill switch: REWARM_SHADOW_ON.
        try:
            from core import associative_recall as _ar_rw
            _ar_rw.note_output_for_rewarm(final or "", "voice")
        except Exception:
            pass
