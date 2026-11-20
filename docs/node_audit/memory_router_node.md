# memory_router_node — node audit

- **Role:** Key-generation intermediary that sits between raw perception and the memory DB. It does NOT retrieve memories; it generates structured retrieval keys (`episodic_keys`, `semantic_keys`, `time_bias`, `working_memory_sufficient`) that drive the subsequent `memory_store.retrieve()` call. In the cognitive pipeline, this is the "query planner" — the LLM decides which terms to search for and whether to skip DB lookup entirely.

- **Fires when:** Hot user-cycle only (never idle/background). Fires in Wave 2 — concurrently with `emotion` and `salience` nodes — via `asyncio.gather()` in `orchestrator.py:529`. This means it only has `state.perception` available (not `state.salience`), which the `_build_prompt` docstring explicitly notes. Lane: `"hot"` → `SERVE_CHAINS["hot"]` = qwen3-du on 127.0.0.1:11433, falling back to Bonsai CPU on 11460 on transport failure. Does NOT fire on idle, background timer, or consolidation cycles.

- **Reads / touches:**
  - `state.raw_input` — the raw user utterance
  - `state.perception.summary` and `state.perception.entities` — from PerceptionOutput (Wave 1 output)
  - `MemoryRouterOutput` schema from `core/schema.py`
  - No DB reads, no file reads, no external state

- **Writes / feeds:**
  - `state.memory_keys` → `MemoryRouterOutput` dataclass (episodic_keys, semantic_keys, time_bias, working_memory_sufficient)
  - This field is the SOLE input to `orchestrator._retrieve_memory()` (line 1075–1105). If `working_memory_sufficient=True`, the orchestrator skips DB retrieval entirely. If False, `episodic_keys`, `semantic_keys`, and `time_bias` are passed directly to `memory_store.retrieve()`, which uses them for keyword overlap scoring and recency weighting.
  - `time_bias` also propagates into `store._score_tier()`, affecting the recency multiplier on every retrieved fragment.
  - No DB writes. No file writes. Pure state transformation.

- **Built / last updated:** mtime `2026-05-30 20:48:10` — no dated inline comments; file has no revision history markers. This is the only timestamp available. Node was part of the initial Nascence architecture (schema.py defines `MemoryRouterOutput` alongside the founding node types); no evidence of post-launch edits.

- **Fleshed-out vs stub:** Fleshed out but minimal by design. 43 lines total. 4 methods (1 constructor, 1 property, 2 abstract implementations). The system prompt is detailed and well-specified (7 directive lines, explicit schema, clear field semantics). `_build_prompt` reads only Perception-available fields with a correct Wave-2 comment. `_write_output` maps all 4 fields with safe defaults. No JSON schema defined as a class attribute (uses NodeBase's `call_node_json` which validates against the LLM output only, not a stored schema — contrast with nodes that carry `JSON_SCHEMA` on the output dataclass). This is not a stub: all three subclass obligations are fully implemented. It is intentionally thin because key-generation is genuinely a one-shot LLM call with no internal branching.

- **Flesh-out opportunities:**
  1. **Schema validation missing.** `MemoryRouterOutput` defines a `JSON_SCHEMA` in `schema.py` but `_write_output` does not validate against it before writing to state. Bad LLM output (e.g. `time_bias="all_time"`) silently passes defaults. Adding a validation call (matching the pattern used by nodes that call `call_node_json` with schema) would catch this.
  2. **Salience focus ignored.** The node fires in parallel with `salience`, so it cannot use `state.salience.focus`. A post-salience routing pass (or a second Wave-3 routing refinement that merges salience focus terms into the keys) would tighten retrieval precision — currently the router is working blind to urgency and attended topics.
  3. **`working_memory_sufficient` is unobserved.** The flag gates the entire DB retrieval but nothing logs or counts when it fires. Adding a debug log line would make it visible whether this shortcut is actually being used, or whether it's dead in practice.
  4. **`time_bias` effect is weak.** The `"distant"` bias gives only a +10% recency multiplier for old fragments (vs recent's +20%), and only for fragments older than 7 days. For deep-history queries this is nearly no-op. The router could also pass an explicit `age_floor` hint that the store could use to filter more aggressively.
  5. **No teacher-example differentiation.** All nodes log training examples via `_log_teacher_example` in `NodeBase.run()`, but the memory router's examples are particularly valuable for distillation since key-generation is the most trainable sub-task (deterministic mapping from perception to search terms). No special logging or annotation to flag these for priority distillation.
