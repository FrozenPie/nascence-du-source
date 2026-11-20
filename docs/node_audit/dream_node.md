# dream_node — node audit

- **Role:** Generates a multi-scene (3-episode) progressive dream arc during Sleep State. Each scene is seeded by the prior scene's narrative, symbols, and `unresolved_core`, so imagery carries across a night. Material comes from the top-N tensions in `subconscious_state.json` (grounded against real reading/study fragments via cosine search), falling back to `state.background_curiosities` if no tensions exist. A prior night's unresolved arc is continued rather than restarted ("the recurring figure until met"). After the arc: unresolved final scenes feed `store_shadow_event(source='unresolved_dream')`, resolved finals feed `store_light_event(source='resolved_dream')`; concrete (non-abstract) symbols are handed to `frontier.note_question` as world-questions for the curiosity chain; the arc is appended to `data/dream_log.jsonl`; each scene is stored as an `origin='dream'` episodic fragment tagged with the current `mood.current_vec()` for affective retrieval. NOT a NodeBase subclass — a plain class instantiated fresh on each call.

- **Fires when:** Sleep State entry, triggered autonomously by `inner_monologue_node.py` after a threshold of idle thoughts. The monologue calls `self._sleep_callback(state)`, which is wired at orchestrator startup (`_nightly_sleep`) to `DreamNode().synthesise(state)`. Runs on the background lane: `SERVE_CHAINS["background"]` — Bonsai-8B-Q1_0 CPU llama-server on port 11460, with GPU qwen fallback on 11433.

- **Reads / touches:**
  - `data/subconscious_state.json` — tensions (sorted by count), integration_patterns (counterpart pointers)
  - `core/memory/store` — cosine search over `memory_fragments` for world-ground fragments (reading/study/research origin, last 400 rows); `_embed()` / `_cosine()` for counterpart matching
  - `state.background_curiosities` — fallback material when no tensions recorded
  - `state.spirit_name`, `state.axiom` — injected into every scene prompt
  - `data/dream_log.jsonl` — reads last line to detect an unresolved prior arc (recurring dream detection)
  - `core.mood.current_vec()` — live felt-vec for emotion tagging stored fragments
  - `core.frontier` — `is_world_question()` / `note_question()` for symbol grounding

- **Writes / feeds:**
  - `core/memory/store.store_fragment()` — each scene as L3 episodic fragment (`origin='dream'`, layer='episodic', relevance=0.8, importance=0.85, emotion_embedding=mood_vec)
  - `core/memory/store.store_shadow_event(source='unresolved_dream')` — final scene unresolved → tension accumulator (feeds T4 → becoming facet only)
  - `core/memory/store.store_light_event(source='resolved_dream')` — final scene resolved → light currency
  - `core.frontier.note_question()` — up to 2 concrete symbols per night as world-questions
  - `data/dream_log.jsonl` — full arc record (narrative, symbols, ended_unresolved, final scene detail for recurring-arc continuity)
  - `state.recent_dreams` — orchestrator inserts the full arc text (top-3 kept) so the waking monologue can graze on it

- **Built / last updated:** Built 2026-06-15 (dated comments in file; mtime 2026-06-15 15:19:43). The multi-scene progressive arc, night-to-night recurring figure, reality grounding (`_find_world_ground`), and symbol-to-frontier pipeline are all 2026-06-15 additions per inline founder notes. No evidence of earlier dated comments — this is a full build, not a refactor.

- **Fleshed-out vs stub:** Fully fleshed. 404 lines, 11 methods (2 async). Every method has real implementation: LLM call with structured JSON schema, cosine retrieval for grounding, counterpart resolution, recurring-arc detection, shadow/light bridging, frontier symbol feeding, per-scene memory storage with affective tagging, arc logging. No pass-stub or TODO-only methods. The `commit=False` path supports in-vitro testing. Only non-trivial gap: no direct REPL `_sleep_cycle` path (noted in docstring as a mirror; REPL path exists separately and is not audited here).

- **Flesh-out opportunities:**
  1. **Grounded-learning integration gap** — the docstring explicitly calls out that the sleep routine "does NOT currently do" consolidation of reading/study into chapters; the dream node and `grounded_learning.py` are architecturally adjacent but dream does not trigger or coordinate with the learning consolidation pass. A post-dream consolidation hook would close this.
  2. **Symbol grounding threshold is very loose (0.22 cosine)** — by design, but means a tangential reading fragment can tinge imagery for unrelated tensions. A per-tension cache or a slightly higher threshold for the first scene (then relax for subsequent) could improve coherence.
  3. **Recurring-arc detection reads only the last log line** — if the last dream was a sub-session test (commit=False) the file isn't written, but any other intervening waking session's log entry would break the night-to-night continuity. A `ended_unresolved` filter across the last N lines would be more robust.
  4. **`_find_counterpart` embeds each integration_pattern label per call** — no caching; if patterns list is large, this is N embed calls per scene. A lazy cache dict on the instance would fix it.
  5. **No grounded_learning distillation call inside `_nightly_sleep`** — `grounded_learning.py` exists and runs, but the orchestrator's `_nightly_sleep` does not call it; it is run separately. Wiring it here (or documenting the expected caller) would close the gap the docstring flags.
