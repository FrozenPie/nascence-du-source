# recall_node — node audit

- **Role:** Hippocampal/mPFC analogue. After DB retrieval but before Reflection, it takes the raw memory fragments from the current cycle and reconstructs the *evolving argument* Du has been building — not a summary of individual memories but the tensions (contradictions) between prior positions and a one-sentence current self-model. Its output replaces raw database strings with a coherent narrative, so Reflection only needs to reason rather than also reconstruct. It is explicitly designated pure reconstruction: no DB writes, no affect modulation. It separates reconstruction from reasoning — the named motivation in its docstring.

- **Fires when:** Hot user-cycle and internal cycles only (never background). Fires conditionally inside the orchestrator's Recall→Episodic-Buffer loop in `_run_cycle_impl`, gated by `_should_recall()`. Two trigger conditions:
  1. `len(state.memory_fragments) >= 2` — enough fragments to tension-map.
  2. `len(state.memory_fragments) >= 1` AND the raw input contains explicit conversation-reference terms (e.g., "you said", "earlier", "remember") from `_CONV_REF_TERMS`.
  Skipped entirely if a mastered procedural skill is active (`_procedure_automatic()` returns True).
  Lives on the **"hot" lane** (NODE_REGISTRY entry: `"recall": {"lane": "hot", "fires": "after_db_query_conditional"}`). Served by `SERVE_CHAINS["hot"]` = `["http://127.0.0.1:11433", "http://127.0.0.1:11460"]` (qwen3-du GPU → Bonsai CPU fallback). Explicitly `affect_modulated = False` (reconstruction must be accurate, not mood-coloured).

- **Reads / touches:**
  - `state.spirit_name`, `state.axiom` (trimmed to identity+values only, dropping VOICE STYLE and SPEAKING CONSTRAINTS via `_trim_axiom`)
  - `state.raw_input`
  - `state.perception.summary` (if present)
  - `state.emotion.primary` (if present)
  - `state.conversation_history[-4:]` — last 4 live exchanges for in-session argument thread
  - `state.symbol_evolution_note` (Phase 2 — symbol meaning shift story, if present)
  - `state.memory_fragments[]` — the DB-retrieved fragments (each up to 300 chars, labelled by `frag.layer`)
  - No DB tables accessed directly; all memory is pre-populated by the orchestrator's `_retrieve_memory()` before this node runs.

- **Writes / feeds:**
  - Writes `state.recall` (a `RecallOutput` dataclass): `reconstruction` (50–80 word first-person narrative), `tensions` (list of up to 3 contradiction strings, capped in `_write_output`), `self_model` (single sentence), `confidence` (0.0–1.0).
  - `state.recall` is then consumed by:
    - **EpisodicBufferNode** (`_should_buffer()` gate requires `state.recall is not None`; `episodic_buffer_node.py` reads `recall.reconstruction`, `recall.tensions`, `recall.self_model` into the scene binding prompt)
    - **ReflectionNode** — injects `recall.tensions`, `recall.self_model`, and `recall.reconstruction` into the reflection prompt (two code paths: with episodic scene and without)
    - **ExecutiveNode** — substitutes raw fragments with `recall.reconstruction`, `recall.tensions`, `recall.self_model` when `state.recall` is not None
    - **Orchestrator** — uses `state.recall.tensions` as one of two query sources for contradiction-driven `_introspective_rebind_retrieve()`; appends tensions to the persisted memory fragment in `_persist_cycle()` so future Recall nodes can access what the live friction was
    - **`recall_provenance.observe()`** — observe-only, fires on first pass; logs `recall.confidence` and `len(recall.tensions)` to `data/recall_provenance_log.jsonl`
    - **`scripts/debate_harness.py`** — reads `state.recall.tensions` for telemetry JSON (not a runtime consumer)

- **Built / last updated:** File mtime: **2026-06-08 17:33:30**. No inline date comments found. No earlier history traceable from the file alone. Given the mtime and cross-references (symbol_evolution_note read path is tagged "Phase 2", episodic_buffer noted as "C.4"), the node was built and last modified on 2026-06-08.

- **Fleshed-out vs stub:** **Genuinely fleshed out.** 153 lines, 4 methods (`system_prompt`, `_trim_axiom`, `_build_prompt`, `_write_output`). The system prompt is carefully designed — it specifies the reasoning task (tensions, not summaries), output format, token budget for each field, and a grounding constraint (no fabricated tensions). `_build_prompt` assembles all relevant state layers in a deliberate order. `_write_output` validates the tensions list and caps it at 3. It is wired end-to-end: the orchestrator gate, the schema type (`RecallOutput`), and at least 4 downstream consumers are all confirmed present and active. This is not a stub.

- **Flesh-out opportunities:**
  1. **Affective retrieval integration** — Recall currently builds the argument from semantic/episodic fragments only. The `state.emotion_vec` (affective retrieval; `_retrieve_affective_memory()`) populates additional fragments after the main retrieval but before Recall runs. Recall's prompt does not distinguish affect-congruent fragments from semantic ones — it treats all fragments identically. A simple `frag.origin == "affective"` label in the prompt, similar to how `frag.layer` is already used, would let Recall weight the felt-memory differently (the `readable_label()` mechanism exists for this purpose).
  2. **Epoch/theme context** — `state.epoch_context` (L4) and `state.theme_context` (L5) are populated before Recall runs but are not included in `_build_prompt`. Reflection consumes them but Recall, which is upstream, cannot use them to contextualise the argument in a longer-arc frame. Low implementation cost (two lines).
  3. **Confidence signal to gate depth** — `state.recall.confidence` is logged but no downstream node adjusts its behaviour based on it. A low-confidence recall (< 0.3) could plausibly signal that the episodic buffer should lower its own coherence expectations, or that Reflection should treat the reconstruction as provisional. Currently the gate is binary (fired / not fired).
  4. **Teacher-example quality** — Recall logs teacher examples via `NodeBase._log_teacher_example`. But because it is `affect_modulated = False` and has a narrow token budget (512), the examples are short. The quality signal for future distillation depends on whether the model actually generates non-trivial tensions. There is no validation or quality filter on logged examples beyond JSON schema compliance.
