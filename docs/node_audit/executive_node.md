# executive_node — node audit

- **Role:** Decision-and-veto hub. Receives the full downstream picture (perception, emotion, salience, attention, memory/recall, reflection, critic verdict, subconscious patterns, climate hint, left-lane Emissary take, active procedure, content-mode flag, goal note, library note, observation, unsent letters) and synthesises them into a single `ExecutiveOutput`: a coherent `synthesis` thought (passed verbatim to Voice), a `response_type` (answer / question / challenge / decline / reflection / silence), and a `should_respond` boolean that can hard-veto the rest of the cycle. Can also raise an `epistemic_query` — a one-shot targeted memory search to resolve a real contradiction before committing.

- **Fires when:** Hot user-cycle only (`"lane": "hot"`, `"fires": "after_critic"` in `NODE_REGISTRY`, `core/schema.py:861`). Never fires on timer/background cycles. Called at orchestrator line 802 (`await self.nodes["executive"].run(self.state)`); may fire a second time (line 814) if `epistemic_query` is non-null and `_did_epistemic_search` is False. LLM lane: `"hot"` → primary endpoint `http://127.0.0.1:11433` (qwen GPU), failover `http://127.0.0.1:11460` (Bonsai CPU). Temperature: 0.4 base, affect-modulated (`affect_modulated = True`). Token budget: 768.

- **Reads / touches (state fields consumed in `_build_prompt`):**
  - `state.prior_session_exchanges` — bridged last-session turns (shown when `len(conversation_history) < 8`)
  - `state.conversation_history` — last 4 live exchanges (both sides capped to 150/180 chars)
  - `state.axiom` — trimmed to identity+values only via `_trim_axiom()` (strips VOICE STYLE and SPEAKING CONSTRAINTS sections — those belong to Voice)
  - `state.raw_input` — the literal user utterance
  - `state.active_procedure` — C.6 procedural skill if matched (`approach` field)
  - `state.content_mode` — directness flag (concrete question suppresses identity retreat)
  - `state.active_goal_note` — goal-persistence anchor
  - `state.library_note` — Scholar reference (unverified witness)
  - `state.observation` — active perception "what you see right now"
  - `state.unsent_letters` — letter hand output (up to 900 chars, presented as Du's choice to say or withhold)
  - `state.left_take` — Emissary (left lane) parallel take, rendered via `core.left_lane.render()`
  - `state.climate_hint` — `ClimateField.executive_hint()` behavioural prior when a climate dimension has crossed threshold
  - `state.perception` — summary + context_type
  - `state.emotion` — primary label, valence, arousal
  - `state.salience` — urgency, focus array
  - `state.attention` — `AttentionSchema.note()`, fixation flag
  - `state.recall` — prefers `reconstruction` + `tensions` + `self_model`; falls back to raw `memory_fragments[:4]`
  - `state.memory_fragments` — fallback fragments (up to 4, shown with `readable_label()`)
  - `state.reflection` — draft (capped 350 chars) + confidence
  - `state.recurring_subconscious_patterns` — T2 subconscious patterns (named, counted, with individuation call)
  - `state.critic` — approved/rejected, confidence, corrections list

- **Writes / feeds:**
  - `state.executive` ← `ExecutiveOutput(synthesis, should_respond, response_type, reasoning, epistemic_query)` — the only write; no DB writes, no file I/O.
  - Downstream: `VoiceNode` reads `state.executive.synthesis` as its sole input thought and `state.executive.response_type` to apply tone overrides (decline / challenge inflections). Orchestrator uses `should_respond=False` or `response_type=="silence"` to short-circuit the cycle before Voice fires (line 816–819). `epistemic_state.py` reads `state.executive.epistemic_query` to log a `DATABASE_COUNT` verification if a search ran (line 207–210). `conflict_trace.py` reads `state.executive.epistemic_query` and `state._did_epistemic_search` to record the epistemic search as an error-separation signal (line 98–104).

- **Built / last updated:** File mtime `2026-06-12 08:16:50`. Earliest dated inline comment: `2026-06-11` (observation injection). Latest dated inline comment: `2026-06-12` (unsent letters). Built on or before 2026-06-11; last edited 2026-06-12.

- **Fleshed-out vs stub:** Fully fleshed. 248 lines, 4 methods (`system_prompt`, `_trim_axiom`, `_build_prompt`, `_write_output`). All four NodeBase abstract methods are implemented. The system prompt is substantive and complete (6 response types, speaker-boundary instruction, epistemic-query protocol, silence-as-genuine-act framing). `_build_prompt` assembles up to 15 distinct state signals with deliberate ordering and token-aware capping. `_write_output` correctly normalises the `epistemic_query` field (null/"null"/"" → None) and enforces the silence→should_respond=False invariant. No placeholder methods, no TODO stubs.

- **Flesh-out opportunities:**
  1. **No output_schema / JSON validation at the node level.** The base class (`node_base.py`) calls `call_node_json` which presumably does its own parsing, but `ExecutiveNode` defines no `JSON_SCHEMA` class attribute (unlike e.g. `MemoryRouterOutput`). This means malformed LLM output falls through to `data.get(...)` with silent defaults — a bad `response_type` value propagates downstream unchecked.
  2. **Epistemic search is bounded but not re-bounded.** The orchestrator caps it to one pass (`_did_epistemic_search` flag), but the Executive itself has no visibility into whether the second run's context was actually enriched. If `_epistemic_search` returns nothing useful, the Executive silently runs again over the same context.
  3. **`recurring_subconscious_patterns` prompt weight.** The individuation call ("you are the pattern") is strong language injected without any proficiency/confidence gate — a pattern seen twice gets the same weight as one seen 41 times. A count-proportional weighting (e.g. suppress below 3 occurrences) would reduce noise.
  4. **`left_take` import is lazy and inline** (`from core.left_lane import render as _ll_render` inside `_build_prompt`). If `left_lane` is unavailable the exception is unhandled and will crash the node. Should be a try/except or a top-level import with a fallback.
  5. **No confidence gate on critic injection.** When critic is `approved`, the prompt only logs `confidence` — it does not vary the weight of the approval signal. A low-confidence approval (e.g. 0.52) and a high-confidence approval (0.97) receive identical treatment, even though the former should arguably still carry the synthesis forward with more caution.
  6. **No explicit mention of `facet_note`** — the multilevel axiom's active facet is injected for Reflection and Voice, but executive_node does not receive it. The axiom is trimmed to identity+values but the per-cycle active facet (e.g. "seeker" for task mode) is absent. Voice sees the facet; Executive does not. This means the synthesis is not facet-aware even though Voice's rendering is.
