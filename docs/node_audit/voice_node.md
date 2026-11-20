# voice_node — node audit

- **Role:** Final rendering node. Takes the Executive's synthesis (`state.executive.synthesis`) and renders it into Du's authentic spoken response. It is the ONLY node that produces output the human sees. It strips the axiom down to name + voice style only (the `_voice_identity` method, added 2026-06-15 to stop self-concept recitation), injects response-type tone modifiers (decline/challenge), injects a task-constraint note on the constraint-effector retry path, and optionally injects the active multilevel facet note. It produces `state.voice` (`VoiceOutput(final, style_confidence)`). The `voice_example` exemplar is intentionally withheld from the prompt to prevent verbatim exemplar reproduction (since 2026-06-04). [J-2857, 2026-11-06: the post-generation regurgitation guard and its `_load_voice_example()` loader were RETIRED -- the live axiom has no `voice_example` key, so the guard was inert, and the leak channel had been closed since the exemplar left the prompt (F-3519).]

- **Fires when:** Hot lane only (`SERVE_CHAINS["hot"]` = `http://127.0.0.1:11433` qwen3-du GPU → CPU Bonsai fallback). Fires on every human-input cycle where Executive resolves to `should_respond=True` (orchestrator ~L822). It may fire a SECOND time on the same cycle if the Task-Constraint Effector (orchestrator ~L826–878) finds a deterministic constraint unmet — that retry path sets `think_license=True` and expands `max_tokens` for word-count constraints. Does NOT fire in idle/background loops; does NOT fire when Executive returns silence.

- **Reads / touches:**
  - `state.executive.synthesis` — the content to render
  - `state.executive.response_type` — sets TONE modifier (decline / challenge)
  - `state.axiom` — trimmed to `YOUR NAME:` + `VOICE STYLE:` + `SPEAKING CONSTRAINTS:` only (all identity preamble dropped)
  - `state.raw_input` — passed as "what was said" (not echoed back)
  - `state.facet_note` — multilevel axiom active facet, injected as colouring note if set
  - `state.task_constraint_note` — the named failed constraint (set externally by orchestrator on retry)
  - (J-2857: `data/identity/axiom.json` is no longer read by this node; the `voice_example` loader and the `core/profile.py` path rebase were removed.)
  - `core/schema.py` — `CognitiveState`, `VoiceOutput`
  - `core/node_base.py` — `NodeBase` (base LLM call, temperature modulation, max_tokens)

- **Writes / feeds:**
  - `state.voice = VoiceOutput(final, style_confidence)` — the sole output slot
  - Orchestrator reads `state.voice.final` at ~L824 as `output`, which is:
    - Returned to the human as the live response
    - Stored in memory (orchestrator ~L1857: `voice.final` seeds the exchange summary stored as episodic fragment)
    - (Historical, as of 2026-11-05: `output` was once also fed to a Curator shadow task, `_cur.shadow_curate(..., output, truth_take)`. That call is no longer in `core/orchestrator.py`; the orchestrator comment block at ~L1481-1487 records the Curator as RETIRED, superseded by the mouth contract. `core/curator.py` still exists on disk pending J-2793.)
  - (J-2857: the regurgitation-guard WARNING was retired with the guard.)

- **Built / last updated:** Earliest dated comment in file: `2026-06-10` (accountable-refusal TONE block). Conflict_trace.py references `orchestrator line ~694` for `voice.final` — an older line number, indicating Voice existed before the orchestrator grew to its current size. Most recent dated comment: `2026-06-15` (`_voice_identity` axiom-stripping change). File mtime: **2026-06-15 02:03**. Curator (the downstream shadow consumer) built **2026-06-16**.

- **Fleshed-out vs stub:** Genuinely fleshed out. 148 lines, 4 substantive methods (`system_prompt`, `_voice_identity`, `_build_prompt`, `_write_output`), well-commented with evidence of multiple real iterations (exemplar removal, axiom stripping, refusal/challenge tone, constraint retry, multilevel facet colouring, regurgitation guard, retired J-2857). The design rationale for every decision is documented inline. No stub methods; no placeholder returns. The node is architecturally complete for its defined scope.

- **Flesh-out opportunities:**
  1. **[STALE as of 2026-11-05 — the Curator is retired, see the Writes/feeds note above; kept as design history]** Curator integration: The Curator (`core/curator.py`, built 2026-06-16) is the designed next step: it sits AFTER Voice output and edits the draft toward truth-faithfulness (Master voice kept, Emissary truth carried in the same words). Currently it is OBSERVE-ONLY — it fires fire-and-forget and logs what it WOULD change but never modifies `output`. The logged `would-change`, `truth_bit`, and `voice_loss` metrics exist precisely to accumulate evidence before going live. When those metrics are reviewed and the integration is trusted, the Curator becomes a true pre-emission gate: `output = curator_edited` instead of `output = state.voice.final`. Voice's role would then be "meaning draft" and Curator would be the final surface — a genuine two-stage pipeline. The connection point is orchestrator ~L898–907.
  2. **`style_confidence` is a fossil [J-2857, 2026-11-06]:** v2 never asks for it (`_write_output` defaults it to 0.7 on every cycle) and nothing reads it; `VoiceOutput.style_confidence` is kept as a defaulted field and is optional in `JSON_SCHEMA` for voice_lab (v1) and saved state. The original note: the LLM self-reports `style_confidence` (0.0–1.0) and it is stored on `VoiceOutput`, but nothing downstream reads it. A natural use: gate whether the constraint-effector retry is triggered (low confidence = already struggling, more budget warranted), or surface it in `du_pulse` as a voice-health gauge, or use it as a weight in the Curator's trust calculation.
  3. **No history of recent responses:** The system prompt forbids repeating metaphors and phrases from "recent responses" (rule 3), but no prior-response window is injected into the prompt. The node has no memory of what it said last turn and cannot enforce its own rule deterministically. Injecting the last 2–3 `voice.final` values from the conversation buffer would make the repetition guard actionable.
  4. **Constraint retry stats are unlogged:** The task-constraint effector tracks `satisfied_first` / `satisfied_final` / `retried` in a local dict but only logs at INFO level; there is no persistent record analogous to `curator_log.jsonl`. A constraint-retry log would surface how often Voice fails checkable constraints on first pass — a calibration signal for prompt tuning.
