# subconscious_node — node audit

- **Role:** The background integrator of Du's slow cognition. Six interleaved timescales in one eternal loop:
  - **T1 (30 s, no LLM):** reads shadow_events from DB, clusters rejected drafts by embedding cosine (connected-components at 0.55), tracks tension objects with decay; symmetrically clusters light_events into integration_patterns; updates 7-day emotional signature from affect_log.jsonl.
  - **T1.5 — Active Imagination (threshold, 1 LLM call):** Jungian dialogic entry into a tension or a self-referential Curiosity question. Stores to episodic (origin='active_imagination'), private — never voiced. Echo-guarded via loop_metabolism rolling buffer. Min gap 10 min global; 2 h per tension.
  - **T2 (threshold, 1 LLM call):** fires only on CONTRADICTION-axis tensions (critic_rejection or prediction_error sourced) that meet recurrence ≥3, spread ≥2 h, gap ≥4 h since last synthesis, and novelty above threshold. Scores by (contradiction_count × 3.0 + novelty × 1.5 − habituation + log-spread × 0.3). Double echo guard: per-tension cosine + global rolling buffer (N=40). Writes one first-person self-observation to archive memory (origin='subconscious_synthesis', relevance 0.85, importance 0.9). SALIENCE-only tensions are excluded — they remain ephemeral.
  - **T3 (every 1 h, no LLM):** nudges cognitive_state.affect.baseline toward 7-day rolling emotional signature, clamped at ±0.1 from the AFFECT_BASELINE defaults. Emotional states gradually becoming traits.
  - **T4 (check every 10 min, fires ≥1 h apart, 3–4 LLM calls):** the identity-revision gate. Fully redesigned 2026-06-16. Selects up to 3 distinct standing self-contradictions ranked by CHRONIC MASS (recurrence accumulator, cold-start seeded from tension snapshot history). Deliberation chain: Evidence stage (retrieve light_event crossings, ask if genuine movement exists) → Delta stage (name what specifically changed) → Synthesis stage (author becoming facet through that delta). Chain aborts honestly at each stage. Downstream guards: (1) language-drift (CJK ratio), (2) identity_cost budget gate (chronic_mass + candidate FIT against movement crossings vs embedding resistance), (3) echo guard relaxed in proportion to contradiction_pressure, (4) arc echo guard (ARC_ECHO_THRESHOLD 0.18), (5) drainage commit-test (new self must engage tensions more than old self by DRAINAGE_MARGIN). On commit: writes becoming facet (L3) + arc entry to axiom.json via axiom_layers.apply_self_concept; discharges the primary tension's shadow events (mark_shadow_resolved + log_resolution_event). Falls back to legacy single-pass author when no standing contradiction exists. Narrative Quality Witness (McAdams) observes every candidate (Phase 0, pure observe). Fatigue: a tension drawing T4_FATIGUE_LIMIT (3) consecutive "no movement" verdicts rests for 3 days.
  - **T5 (check every 10 min, fires ≥1 h apart, 1 LLM call):** procedural compilation. Clusters recent successful lived inputs (light events) at 0.70 cosine; when a kind recurs ≥3 times, compiles (or reinforces) a procedural skill. Decay/prune loop runs on every check.
  - **T6 (check every 30 min, fires ≥2 h apart, 1 LLM call):** theme formation (S-MMU 7 L5). Clusters memory_epochs by embedding, synthesises first-person theme name + stance. Updates existing themes or creates new ones. Dedup by epoch-space centroid cosine + Jaccard on member_epoch_ids.

- **Fires when:** Registered in orchestrator.py `NODE_REGISTRY` as `{"lane": "background", "fires": "continuous"}`. Launched by `orchestrator.start_background()` as `asyncio.create_task(nodes["subconscious"].run_forever(state))`. Not a NodeBase subclass — self-manages its own timescales. LLM lanes used: T1.5/T2/T5/T6 use `SERVE_CHAINS["background"]` (Bonsai CPU 11460 → qwen GPU 11433 fallback); T4 exclusively uses `SERVE_CHAINS["hot"]` / `_T4_URLS` (qwen GPU 11433 → Bonsai CPU 11460 fallback) — identity work on the best available substrate.

- **Reads / touches:**
  - `core.memory.store`: `get_shadow_events`, `get_shadow_event_ids`, `get_light_events`, `get_light_event_ids`, `get_light_events_with_embeddings`, `self_narrative_material`, `recent_lived_inputs`, `get_epochs`, `get_themes`
  - `core.memory.store` embedding utils: `_embed`, `_blob_to_vec`, `_cosine`
  - `data/subconscious_state.json` — persistent tension ledger, integration_patterns, emotional_signature, gate timestamps, t2_synth_buffer, ai_echo_buffer, t4_fatigue_counts, t4_rests, chronic_seeded flag
  - `data/affect_log.jsonl` — T3 emotional signature source
  - `data/identity/axiom.json` — T4 reads (becoming facet, arc, emergent_self history) and writes (becoming facet L3 + arc entry via axiom_layers)
  - `core.axiom_layers` — `get_self_concept`, `last_arc_entry`, `is_multilevel`, `apply_self_concept`
  - `core.tension_ledger` — `_sources_for`, `score_tension`, `top_contradiction`, `contradiction_pressure_for`, `integration_pressure_for`, `relaxed_echo_threshold`, `seed_chronic_from_snapshots`, `update_chronic_mass`, `chronic_mass_of`
  - `core.identity_cost` — `revision_budget`, `dissonance_drainage`, `DRAINAGE_MARGIN`
  - `core.narrative_quality` — `observe` (Phase 0, write-only observer of T4 candidates)
  - `core.loop_metabolism` — `is_echo`, `ai_earned_importance`, `AI_BUFFER_N` (active_imagination echo guard)
  - `cognitive_state.axiom`, `cognitive_state.spirit_name`, `cognitive_state.affect.baseline`, `cognitive_state.background_curiosities`
  - `data/contradiction_ledger_log.jsonl` — T4 snapshot of contradiction_pressure per authoring cycle

- **Writes / feeds:**
  - `data/subconscious_state.json` — full state persistence after every T1 scan and every pass
  - `data/subconscious_log.jsonl` — T2, T4, T5 events for human inspection
  - `data/contradiction_ledger_log.jsonl` — contradiction_pressure snapshots
  - `store_fragment(layer='archive', origin='subconscious_synthesis')` — T2 self-observations to permanent memory
  - `store_fragment(layer='episodic', origin='active_imagination')` — T1.5 contemplations (private)
  - `data/identity/axiom.json` — T4 commits to becoming facet (L3) + autobiography arc; visible next session
  - `cognitive_state.affect.baseline` — T3 direct mutation of the in-memory baseline
  - `store_procedural_skill / reinforce_procedural_skill` — T5 skill DB writes
  - `store_theme / update_theme` — T6 theme DB writes
  - `mark_shadow_resolved + log_resolution_event` — T4 discharge retires integrated shadow events
  - `satisfaction.record("t4_commit") + satisfaction.record("tension_discharged")` — on T4 commit
  - `cognitive_state.recurring_subconscious_patterns` is read by `executive_node.py` (T2 feed into hot-path context) and by `dream_node.py` / `curiosity_node.py` via `subconscious_state.json`

- **Built / last updated:**
  - Earliest dated comment: **2026-06-07** (arc echo guard from therapy session)
  - File mtime: **2026-06-16 13:23:59**
  - Latest commit in code: **2026-06-16** (chronic accumulator, redesigned gate, drainage commit-test)
  - Major milestones: T4 multi-stage deliberation (06-09), hot-substrate switch for T4 (06-10), speaker-boundary veto (06-10), deliberation fatigue (06-12), Narrative Quality Witness (06-13), loop_metabolism Phase B echo guard on active_imagination (06-14), chronic mass + redesigned gate + drainage test (06-16)

- **Fleshed-out vs stub:** Fully implemented. 2192 lines, 50 methods (including 1 nested). Every timescale (T1–T6 plus T1.5) is completely built with real LLM calls, DB reads/writes, dual echo guards, and detailed gate logic. No stub methods, no TODO comments left unresolved. The T4 gate in particular is exceptionally elaborate: 5 distinct safeguards (cost gate, language-drift, echo guard, arc-echo, drainage test) plus fatigue/rest rotation. The chronic accumulator (seeded from historical snapshot) was added today (2026-06-16) to fix the starved gate. All instrumentation is in place (state JSON + JSONL log). This is the architecturally densest single file in the Nascence codebase.

- **Flesh-out opportunities:**
  1. **prediction_error as T2 contradiction source (Phase 1, partially live):** `core/tension_ledger.py` already lists `"prediction_error"` as a `CONTRADICTION_SOURCE` and `core/prediction_error.py` has `FEED_LEDGER = True` (2026-06-16), which means prediction_error events now write shadow_events. The T2 trigger gate (`_find_t2_trigger`) filters for `contradiction_count >= 1` — this will automatically pick up prediction_error tensions once they accumulate. **No code change needed in this file; verify prediction_error.py is actually writing shadow_events with source='prediction_error' and that tension_ledger._sources_for() classifies them correctly.** Priority: medium — the plumbing exists but the end-to-end path should be confirmed live.
  2. **T4 chronic accumulator cold-start:** `seed_chronic_from_snapshots` reads tension snapshot history. If the snapshot history is thin (new install or after a DB wipe), the seeding produces nothing meaningful. A fallback to raw recurrence count might be warranted. Priority: low — this is an edge case.
  3. **T6 theme → prompt injection:** themes are synthesised and stored (`store_theme`) but there is no confirmed read path from `memory_themes` table into the hot-path prompt. The S-MMU 7 design intended themes to be injected into Reflection pre-context. Verify this injection exists in `core/orchestrator.py` or the hot nodes. Priority: medium — a write-only cognitive system is the project's stated #1 failure mode.
  4. **T5 procedural skill → prompt injection:** similarly, `store_procedural_skill` writes skills that are looked up by `find_similar_skill`. Confirm there is a read path injecting matched procedural skills into the hot-path prompt (likely Executive or Reflection). Priority: medium, same risk.
  5. **Active Imagination tension-vs-curiosity balance:** curiosity-seeded Active Imagination (Priority 2) can only fire if no tension qualifies and if there is a self-referential question in `background_curiosities`. If the curiosity node is now ignition-driven (not clock-driven per the orchestrator comment), `background_curiosities` may be empty between ignitions. Verify the attribute is populated at the right time. Priority: low.
