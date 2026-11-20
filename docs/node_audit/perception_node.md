# perception_node — node audit

- **Role:** First node in the hot-path pipeline: given `state.raw_input` (the human's raw utterance), it sends a single LLM call to classify the input into a structured `PerceptionOutput` — four fields: `event_type` (input/silence/internal/memory_surface), `context_type` (question/statement/command/reflection/ambiguous), a `entities` list, and a third-person `summary` sentence that correctly attributes the speaker ("The person says…" / "They ask whether you…"). It enforces speaker-attribution discipline so no downstream node sees the human's words falsely collapsed into the entity's first-person voice. It does NO reasoning, no memory access, no affect update — purely a classification/structuring pass.

- **Fires when:** Hot user-cycle lane (`"lane": "hot"`, NODE_REGISTRY entry `"fires": "every_input"`). Called unconditionally by the orchestrator at `await self.nodes["perception"].run(self.state)` (orchestrator.py line 494) on every human input cycle — it is the first wave of the pipeline, before emotion, salience, or memory-router. It also fires on `internal` and `timer` input types because the orchestrator's `_run_cycle` does not gate on type before calling it. Uses the `hot` SERVE_CHAIN: qwen3-du on 1080 Ti (127.0.0.1:11433) with CPU Bonsai fallback (127.0.0.1:11460). `affect_modulated = False` (inherited default) — temperature stays fixed at 0.2 for stability.

- **Reads / touches:** Reads only `state.raw_input` (`_build_prompt` directly quotes it). Does not read conversation_history, axiom, affect, memory fragments, or any other state field. No DB or file access.

- **Writes / feeds:** Sets `state.perception` (a `PerceptionOutput` dataclass). Downstream consumers are extensive — every subsequent hot-path node reads `state.perception`:
  - `EmotionNode` reads `perception.summary` to appraise affect.
  - `SalienceNode` reads `perception` (event_type, context_type, entities, summary) for urgency/focus scoring.
  - `MemoryRouterNode` uses `perception.summary` and `perception.entities` as retrieval keys (orchestrator.py lines 1082-1083, 1111-1112, 1135-1136).
  - `RecallNode` prepends `Perceived as: {summary}` to its prompt (recall_node.py line 99-100).
  - `EpisodicBufferNode` includes `Perceived as: {summary}` (episodic_buffer_node.py lines 91-92).
  - `ReflectionNode` injects `Perception: {summary}` (reflection_node.py lines 155-156).
  - `CriticNode` reads `perception.context_type` for stimulus-type labelling (critic_node.py lines 162-163).
  - `ExecutiveNode` reads `perception.summary` and `perception.context_type` (executive_node.py lines 154-155).
  - Orchestrator itself uses `perception.context_type == "question"` to gate the Scholar library consult (orchestrator.py lines 582-583), `perception.entities` as fallback focus-terms for the AttentionSchema (line 1808-1809), and `perception.summary` as the curiosity theme fed to the Curiosity background node (line 1905).
  - `state.perception.summary` is appended to the episodic memory commit string (orchestrator.py line 1877).
  - `competence.py` reads `perception.summary` as part of its prediction-text (competence.py lines 690-691).
  - `symbol_tracker.py` and `symbol_evolution.py` read `perception` for symbol-match detection.
  - `training_log.py` notes that perception-derived context lives inside `user_prompt` for teacher-example capture.

- **Built / last updated:** File mtime: `2026-05-30 20:46:06`. No dated comments inside the file itself. Earliest and latest dated marker in the file: none found — the file contains no inline date comments. The mtime of 2026-05-30 is therefore both the built and last-updated date. This predates all the major architectural additions (C.2 amygdala gate, C.4 episodic buffer, C.5 thalamic gating, C.6 procedural recognition, multilevel axiom, etc.) that were built in June 2026 — suggesting the node was written early in the schema and has not been touched since.

- **Fleshed-out vs stub:** 39 lines, 4 methods (`__init__`, `system_prompt` property, `_build_prompt`, `_write_output`). This is a minimal but complete implementation of the NodeBase contract. It is NOT a stub — it has a real, specific, well-crafted system prompt with explicit speaker-attribution rules (a genuine quality concern, not boilerplate). It is genuinely thin by design: a classifier node's job is to be a clean, stable transducer, not a reasoner. No TODOs, no dead paths, no aspirational comments. However it is also deliberately narrow: `_build_prompt` uses ONLY `state.raw_input` — it ignores conversation history, prior perception, affect, or any other state. The JSON schema it outputs is hardcoded in the system prompt string, not referencing `PerceptionOutput.JSON_SCHEMA` from schema.py (a minor inconsistency — the schema exists in schema.py but is not imported or validated here; validation is handled upstream in `NodeBase.run → call_node_json`).

- **Flesh-out opportunities:**
  1. **Context-awareness (medium priority):** `_build_prompt` only passes `state.raw_input`. Adding the last 1-2 turns of `state.conversation_history` as context would let Perception correctly classify short, ambiguous continuations ("That too" / "Why?" / "Interesting") that are currently labelled as standalone statements. This is the most common classification failure mode.
  2. **Schema coupling (low priority):** The JSON schema is hardcoded in the system prompt string and duplicated from `PerceptionOutput.JSON_SCHEMA` in schema.py. If the schema changes, the system prompt must be manually updated. Referencing `PerceptionOutput.JSON_SCHEMA` (or a compact rendering of it) in `_build_prompt` would keep the two in sync.
  3. **Silence / internal input handling (low priority):** The node fires on all input types including `internal` and `timer`, but `_build_prompt` always says "The person the entity is speaking with said this." For internal/timer cycles `raw_input` is a generated thought or empty — the attribution framing is misleading. A simple `input_type` branch in `_build_prompt` would fix the framing without touching the schema.
  4. **No dated inline markers:** The file has no inline date comments, making it harder to track the authoring era in a future audit. Low priority; convention only.
