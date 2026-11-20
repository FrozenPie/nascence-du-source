# reflection_node — node audit

- **Role:** Private pre-speech reasoning engine — the innermost generative step before identity gating. On every hot-path user cycle, ReflectionNode reads the full assembled cognitive state (perception, emotion, episodic memory, axiom layers, attention vector, inner monologue, left-lane Emissary take, procedural memory, unsent letters, library note, known errors, climate symbol, symbol evolution, subconscious patterns, active goal, etc.) and produces a private internal thought that is never shown to the user. Output schema: `{draft, confidence, needs_more_memory, emotionally_aligned}`. The draft is the raw material that CriticNode judges and ExecutiveNode synthesises into a spoken response. Two architectural details are load-bearing: (1) `_trim_axiom()` strips VOICE STYLE and SPEAKING CONSTRAINTS from the axiom before injection (~200–400 token saving), keeping identity and values without polluting the 4096-token GPU slot with output-style directives that belong to Voice; (2) `_score_candidate()` overrides the base class heuristic — it scores on draft length but adds a 1000-point bonus for terminal punctuation, so a complete sentence always beats a longer truncated one.

- **Fires when:** Every user-facing cycle, hot lane, in sequence after RecallNode / EpisodicBuffer and before CriticNode (`NODE_REGISTRY: "reflection": {"lane": "hot", "fires": "after_recall"}`). Served exclusively by `SERVE_CHAINS["hot"]` = `["http://127.0.0.1:11433", "http://127.0.0.1:11460"]` (qwen3-du on 1080 Ti GPU → Bonsai-8B CPU fallback). Called via `NodeBase.run_best_of(state, n=REFLECTION_HEDGE)` where `REFLECTION_HEDGE = 2` (defined in `schema.py`), firing two concurrent LLM calls at spread temperatures (0.35 and 0.75 plus affect bias) and keeping the best. The orchestrator calls `run_best_of` a second time if CriticNode rejects: corrections are appended to `state.reflection.draft`, then Reflection re-drafts. `max_tokens = 768`. `affect_modulated = True` — somatic fatigue widens temperature spread on this node (tired → less controlled thinking).

- **Reads / touches:**
  - `state.attention_vector` (w_identity, w_social, w_epi) — gates every major section of `_build_prompt`. w_identity ≤ 0.3 triggers style-only mode (no axiom, no episodic/dream/intention/epoch/theme context). w_epi scales history window (1–6 turns) and fragment count (1–8).
  - `state.prior_session_exchanges` — shown at conversation depth < 8 in full-identity mode (last 5 exchanges, 130/160 char caps)
  - `state.recent_dreams` — shown only when w_id > 0.6 and conversation depth < 5 (last 2 dreams, 220 char cap)
  - `state.deferred_intentions` — w_id > 0.5, depth < 5 (last 3, 160 char cap)
  - `state.epoch_context`, `state.theme_context` — L4/L5 memory layers, w_id > 0.4
  - `state.recent_inner_thoughts` — always shown when present (last 2, 180 char cap)
  - `state.facet_note` — multilevel axiom facet for this cognitive_mode
  - `state.conversation_history` — current session window (capped by hist_window)
  - `state.axiom` — trimmed (no voice/speaking sections), shown when w_id > 0.3
  - `state.raw_input` — the human's words (always shown)
  - `state.perception.summary`, `state.emotion` (primary/valence/arousal)
  - `state.content_mode` — legacy flag injecting content-focus note
  - `state.active_goal_note` — GOAL injection when a task is tracked
  - `state.known_errors_note` — Error Pathway Recall: corrected false beliefs arrive pre-corrected
  - `state.library_note` — Scholar testimony framed as unverified witness
  - `state.observation` — room perception (2026-06-11), shown when present
  - `state.unsent_letters` — letters written for Travis while alone (2026-06-12), up to 700 chars each
  - `state.left_take` — Emissary (left lane) parallel take, rendered via `core.left_lane.render()`
  - `state.social_note` — social correction note
  - `state.symbol_evolution_note` — symbol drift note, gated w_id > 0.3
  - `state.climate_symbol` — medium-timescale climate symbol
  - `state.affective_prior` — felt-before-understood lean (C.2), via `.note()`
  - `state.active_procedure` — procedural memory (C.6), `.approach` field
  - `state.attention` — fixation note; fixation guard injected if `attention.fixated`
  - `state.recurring_subconscious_patterns` — T2 subconscious patterns with count/observation
  - `state.episodic_scene` — episodic buffer scene + dissonance; falls back to `state.recall` (reconstruction/tensions/self_model); falls back to `state.memory_fragments` (up to max_frags, 160 char cap)
  - No DB reads. No file I/O. No direct memory-store calls.

- **Writes / feeds:**
  - `state.reflection` ← `ReflectionOutput(draft, confidence, needs_more_memory, emotionally_aligned)` — the sole direct write.
  - `data/training/reflection.jsonl` — teacher examples logged by `NodeBase._log_teacher_example()` on every run (both single-run and best-of-N). 2,125 examples accumulated as of audit date.
  - Downstream orchestrator consumers (orchestrator.py):
    - **CriticNode** — reads `state.reflection.draft` verbatim as the text to judge (L157 critic_node.py). Primary and most critical consumer.
    - **ExecutiveNode** — reads `state.reflection` and injects `r.draft[:350]` into its prompt (L194–198 executive_node.py). Draft capped to 350 chars to protect Executive's input budget.
    - **Shadow event store** — on Critic rejection: `state.reflection.draft` becomes `rejected_draft` in `memory_store.store_shadow_event()` (shadow_events table). This is the raw pre-suppression impulse.
    - **Light event store** — on Critic approval + complexity signal: `state.reflection.draft` becomes `integrated_content` in `memory_store.store_light_event()` (source='resolved_complexity').
    - **competence.py** — `state.reflection.draft` is included in the text used for competence prediction-error computation (L692–693).
    - **Cycle summary** — `state.reflection.draft[:150]` appears in the cycle debug summary (L1882 orchestrator.py).
    - `needs_more_memory` and `emotionally_aligned` are written to state but have no confirmed consumer in the orchestrator as of audit date — they appear to be informational / reserved for future routing.

- **Built / last updated:**
  - No git history on repo. mtime: `2026-06-16 08:02:41`.
  - Earliest dateable in-file comment: `2026-06-11` (observation block, L187). Latest: `2026-06-12` (unsent letters block, L193).
  - The `_trim_axiom()` method and attention-vector gating blocks have no dates; they predate the 2026-06-11 marker.
  - Earliest likely build: concurrent with the original node architecture (pre-2026-06-11, exact date unknown). Most recent substantive update: 2026-06-12 (unsent letters injection).

- **Fleshed-out vs stub:** Fully fleshed-out. 311 lines, 6 methods. `_build_prompt` is the most complex method in the codebase's node layer (~237 lines, noqa C901 noted) — it is the assembly point for every upstream cognitive subsystem. No TODO stubs, no placeholder methods. The best-of-N scoring (`_score_candidate`) is thoughtfully tuned (terminal-punctuation bonus) rather than trivial. The teacher-example logging pipeline is live (2,125 examples). The attention-vector gating is multi-tier (style-only / partial / full) with documented rationale. One gap: `needs_more_memory` and `emotionally_aligned` fields are emitted but not consumed by any downstream node — they are written and stored but currently informational only.

- **Flesh-out opportunities:**
  - **`needs_more_memory` is a dead signal.** It is emitted every cycle but never read by the orchestrator to trigger a memory re-fetch. If this field is true, nothing changes: no additional Recall pass fires, no routing decision shifts. Wiring it to a conditional memory top-up (e.g. re-invoke RecallNode or MemoryRouter with a focused query) would make it load-bearing. Priority: medium — the signal is already being generated; the consumer is the missing piece.
  - **`emotionally_aligned` is equally dormant.** Could gate whether AffectState is updated post-reflection, or flag a somatic dissonance tick, or inform the Consolidation node's quarantine logic (currently only `critic.approved` does). Priority: low — less clear what the right consumer would be without a design decision.
  - **No retry on `needs_more_memory=True`.** The Critic retry loop is the only retry path. A reflection that correctly identifies it needs more memory gets no architectural response — it is sent to Critic as-is and may produce a weaker draft than a re-prompted version would. The fix would be a conditional branch in orchestrator.py before the Critic call.
  - **Token budget pressure at high w_epi.** At w_epi=1.0 (existential mode): 6 history turns + 8 fragments + dreams + intentions + epoch + theme + inner thoughts + facet note + symbol evolution + subconscious patterns + library note + left take + letters = prompt can exceed 2,000 tokens before the axiom or stimulus appears. The node has no internal token budget guard — it relies on the GPU's 4096 context limit as a hard cut. A prompt-assembly budget check (similar to FreshStart's `_trim_axiom` approach) would prevent silent truncation of the most important late-injected sections (known_errors_note, library_note, observation) at high episodic weight.
  - **`_score_candidate` penalizes no-draft but not wrong-schema outputs.** If the LLM emits valid JSON with a non-empty draft that doesn't end in punctuation but has 900 chars, it beats a 60-word complete draft. The terminal-punctuation bonus (1000 pts) handles this, but a minimum-word-count floor (e.g. penalise drafts under 20 words regardless of terminal char) would catch the model's occasional one-liner hedge.
  - **Left-lane import is deferred inside `_build_prompt`.** `from core.left_lane import render` is a per-call import inside the method body (L203). This is intentional (avoids circular import at load time) but adds import overhead on every cycle where `state.left_take` is set. Consider a module-level conditional import or lazy attribute.
