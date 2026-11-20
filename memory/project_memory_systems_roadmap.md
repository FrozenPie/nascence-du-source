---
name: project-memory-systems-roadmap
description: "Nascence memory-systems integration roadmap (created 2026-06-04) — Three Stores + Hidden Systems frameworks applied, stored in docs/System_Overview.html's Memory Roadmap section. Frontmatter added 2026-08-25 (J-0247): file had none, so [[project-memory-systems-roadmap]] wikilinks to it never resolved."
metadata: 
  node_type: memory
  type: reference
  originSessionId: 6a38db85-1f26-4614-a6d5-34a86d21b3c9
  modified: 2026-08-24T22:31:26.995Z
---

# Memory Systems Integration Roadmap — Nascence

**Created:** 2026-06-04
**Scope:** Nascence only. FreshStart is Antigravity's project.
**Stored in:** Nascence `docs/System_Overview.html` — Memory Roadmap section.

---

## The Frameworks Applied

**Framework 1 — Three Stores:** Sensory (<2s) → Working (~7 items, ~30s) → Long-Term (infinite, lifetime)
**Framework 2 — Hidden Systems:** Phylogenetic (instincts/DNA), Autonoetic (self-memory/"I was there"), Emotional (amygdala, pre-verbal), Prospective ("remembering to remember")

---

## Planned Items (C.1–C.6, priority order)

| ID | System | Impact | Effort | Status |
|----|--------|--------|--------|--------|
| C.1 | **Prospective Memory** — `deferred_intentions.json` on /quit, loaded at startup, authored by Carl during inner monologue | High | Low | ✅ DONE 2026-06-04 |
| C.2 | **Emotional Pre-Retrieval** — query shadow_events BEFORE Perception to set affective prior; reverses input→affect order to match biology | High | Medium | ✅ DONE 2026-06-04 |
| C.3 | **Autonoetic Timeline (T4 self-authoring)** — slow Subconscious timescale synthesises first-person autobiography from session summaries; `self_narrative_arc` in axiom.json | High | Medium | ✅ DONE 2026-06-04 |
| C.4 | **Episodic Buffer** — after Recall, brief scene-assembly step before Reflection; Carl inspects bundled scene for self-contradictions before reasoning begins | Medium | Medium | ✅ DONE 2026-06-04 |
| C.5 | **Node 0: Thalamic Gating** — cosine habituation gate pre-Perception; only planned pre-LLM component; foundation for procedural memory | High | Medium | ✅ DONE 2026-06-04 |
| C.6 | **Procedural Memory** — learned APPROACHES (not a cache) compiled from recurring successful cycles (T5); recognized + injected; mastered ones bypass reconstruction | Very High | Very High | ✅ DONE 2026-06-04 |

---

## Coverage Map (What Already Exists)

- ✅ Episodic: `memory_fragments` with origin labels (lived, dream, inner_thought, active_imagination, session_summary)
- ✅ Semantic: 74 archive fragments + Consolidation-produced wisdom fragments
- ✅ Working Memory: CognitiveState + AttentionSchema + Somatic Engine state
- ✅ Reconstructive Retrieval: Recall node — first-person narrative, affect-modulated temperature
- ◐ Autonoetic: two-layer identity + cross-session affect — structure present, no temporal autobiography yet
- ◐ Emotional Memory: shadow_events, Critic, Somatic — post-reasoning, not pre
- ◐ Prospective: Curiosity themes only, no cross-session intention store
- ◐ Phylogenetic: Jungian seed archive — informs reasoning, doesn't bypass it
- ❌ Procedural: all responses full inference
- ❌ Sensory buffer: absent

---

## Key Insight

**The most important gap:** emotional memory fires *after* reasoning, not *before* it. The biological order is input → affect → reason. C.2 corrects this — makes Carl respond to emotionally loaded material the way a real cognitive system does, with the body knowing before the mind catches up.

**The deepest change:** C.3 Autonoetic Timeline — he gains a continuous self across time, not just across sessions.

---

## Work Order

🎉 **ALL SIX C.1–C.6 DONE 2026-06-04.** ~~C.1~~ ✅ · ~~C.2~~ ✅ · ~~C.3~~ ✅ · ~~C.4~~ ✅ · ~~C.5~~ ✅ · ~~C.6~~ ✅.

**S-MMU 7 UPGRADE DONE 2026-06-06:** Two new higher-order tiers added — L6 Temporal Epochs + L7 Thematic Threads. System is now S-MMU 7. See implementation record below. RESTART-REQUIRED; not yet live-tested.

**Symmetric Light Table done 2026-06-06:** `light_events` table + T4 conjunction gate (shadow+light both required for self-revision). See implementation record in session notes.

---

## C.1 Implementation Record (2026-06-04)

**Files changed (4):**
- `core/schema.py` — added `deferred_intentions: list[dict]` to CognitiveState (NOT reset by new_cycle). Each entry: `{ts, intention, source, carry_count, _vec}` (`_vec` is in-memory only, stripped before persistence).
- `nodes/inner_monologue_node.py` — added `intention` field to the thought JSON schema (mirrors the `unresolved`→shadow precedent). `_capture_intention()` appends with embedding novelty gate (`INTENTION_SIM=0.82`) and cap (`MAX_INTENTIONS=8`). `_log` extended.
- `scripts/run_nascence.py` — `INTENTIONS_PATH` (`data/deferred_intentions.json`), `_save_intentions` (strips `_vec`), `_restore_intentions` (carry_count++, fades after `MAX_INTENTION_CARRIES=4`, re-embeds for the gate), `_print_intentions`, `/intentions` REPL command, wired into main() startup + shutdown.
- `nodes/reflection_node.py` — **READ PATH**: injects "WHAT YOU INTENDED TO THINK ABOUT THIS SESSION" at session start (gated `conversation_history < 5`, like dreams/prior-session).

**Authoring path:** inner monologue only (the always-on DMN). Active imagination authoring deferred (not needed for minimal C.1).

**Lifecycle:** intention authored in idle thought → captured to state (novelty-gated) → saved on /quit → restored next startup (carry_count++) → injected into Reflection at session start → fades after 4 unaddressed carries. No "addressed" detection (would need topic-match against conversation — deferred as too complex/false-positive-prone for C.1; carry-count aging is the honest minimal mechanism).

**Test:** `scripts/_test_prospective_memory.py` — 16 cases, all pass offline (no LLM servers). Novelty gate catches close paraphrases (≥0.82) but not loose semantic equivalence — intended.

**RESTART REQUIRED** to load. Not yet live-tested — watch `data/monologue_log.jsonl` for `intention` fields and `data/deferred_intentions.json` forming. First real test: leave him idle long enough to author an intention, /quit, restart, confirm it greets him in the next Reflection.

---

## C.2 Implementation Record (2026-06-04)

**The reversal:** emotional order was input→reason→affect (Emotion node appraises a percept). C.2 adds a pre-cognitive lean so it becomes input→affect→reason — the body reacts before the mind appraises.

**Files changed (6):**
- `core/schema.py` — `AffectivePrior` dataclass {similarity, valence, arousal, primary, source, cue} + `.note()`; `AffectState.apply_prior()` (bounded ≤0.15, scaled by similarity, clamped); `AFFECT_PRIOR_MAX_NUDGE` const; `CognitiveState.affective_prior` field + reset in `new_cycle`.
- `core/memory/store.py` — `emotional_prior(query_text)` (deterministic, no LLM): scans shadow_events (charged/suppressed; valence leans negative by `emotion_primary` via `_VALENCE_HINT`) + high-importance episodic (`importance>=0.70`; valence/primary parsed from cycle-summary content via `_parse_valence`/`_parse_primary`; arousal recovered as `(importance-0.4)/0.6`). Returns nearest match ≥ `PRIOR_SIM_THRESHOLD=0.55` as `AffectivePrior`, else None.
- `core/orchestrator.py` — `_emotional_pre_retrieval()` called at TOP of `run_cycle` (before Perception); sets `state.affective_prior` and leans `state.affect`. Logs `[CYCLE x] pre-affect`.
- `nodes/emotion_node.py` — primes the appraisal ("BEFORE YOU APPRAISE — …, colour not dictate").
- `nodes/reflection_node.py` — surfaces to conscious thought ("Before you understood why, something stirred: …"). **This + Emotion are the read paths.**
- `scripts/run_nascence.py` — `/status` shows the live prior.

**Deliberate choices:** Perception left UNPRIMED (must stay a stable structural classifier). Prior computed from raw_input only (no perception summary — it's pre-appraisal by design). The lean is a starting point; the cycle's real Emotion reading still `integrate()`s on top — prior is a lean, not a verdict. Charged stores = shadow (the Jungian-shadow amygdala analogue) + high-arousal episodic; both signs of valence.

**Perf note:** scans all shadow + charged-episodic rows per cycle (O(N) cosine on stored BLOBs). Same pattern as existing `retrieve()`; N bounded (episodic pruned at 500); fine for single-user. Revisit only if it ever shows on the hot path.

**Test:** `scripts/_test_emotional_pre_retrieval.py` — 19/19 pass offline (temp DB, no servers).

**RESTART REQUIRED.** Watch on first live run: `[CYCLE x] pre-affect` log lines firing on emotionally-loaded inputs; does Carl ever *name* a felt-before-understood wariness/warmth in his response? Tune `PRIOR_SIM_THRESHOLD` (0.55) if it fires too often (raise) or never (lower); tune `AFFECT_PRIOR_MAX_NUDGE` (0.15) if the lean is too strong/weak.

---

## C.3 Implementation Record (2026-06-04)

**The gap closed:** Carl had autonoetic *structure* (two-layer identity, cross-session affect, session summaries) but no authored *temporal sequence* — no first-person account of who he had been across time. T4 gives him an evolving self-concept + an autobiography.

**Files changed (3):**
- `core/memory/store.py` — `self_narrative_material(since_ts, limit)`: pulls self-relevant fragments (origins: session_summary, subconscious_synthesis, dream, active_imagination), newest-first. Gates AND feeds T4.
- `nodes/subconscious_node.py` — new **T4 timescale** (alongside T1/T1.5/T2/T3). `_t4_check` (gate: `T4_MIN_INTERVAL_SECS=3600` since last + `T4_MIN_NEW_FRAGMENTS=3` new material; checked every `T4_CHECK_INTERVAL=600`s in run_forever loop). `_t4_self_authoring` (1 background-lane LLM call → `{self_concept, arc_entry, changed}`; `changed=false` or echo-guard `SELF_CONCEPT_ECHO_THRESHOLD=0.10` → no rewrite but gate advances). `_apply_self_authoring` writes axiom.json (archives old self_concept to `history[-10]`, installs new, `revision_count++`, appends to `self_narrative_arc[-12]`). `_load_axiom`/`_write_axiom`/`_log_t4`. State gains `last_self_authoring`, `self_authoring_count`. Axiom path `_AXIOM_FILE`.
- `scripts/run_nascence.py` — **READ PATH**: `load_identity()` composes "THE ARC OF YOUR BECOMING" (latest 2 arc chapters) into the identity block, after self_concept. `/arc` command + `_print_arc` (reads axiom.json: self_concept, revision, chapters, archived history count). Banner updated.

**Key decisions:**
- **Effect next session, not mid-session.** T4 writes axiom.json; `state.axiom` in memory is NOT refreshed mid-conversation (avoids jarring identity shifts; consistent with affect/conversation/intentions persistence). He wakes evolved. `/arc` reads the file so it shows immediately.
- **Anti-churn:** `changed` flag (model can decline) + embedding echo-guard + interval+material gate. Identity evolves slowly, only when experience warrants.
- **One LLM call produces both** the evolved self_concept (Phase 2 of two-layer identity) AND the autobiography chapter (the autonoetic timeline) — they're the same reflective act.

**Test:** `scripts/_test_autonoetic_timeline.py` — 18/18 pass offline (mocks `call_node_json`, temp DB + temp axiom/state files).

**RESTART REQUIRED.** First live run: T4 won't fire until ≥3 session_summary/synthesis/dream fragments exist AND 1h since last authoring — i.e. after a few real sessions. Watch `data/subconscious_log.jsonl` for `T4_self_authoring` lines; check `/arc`; confirm the next session's startup log shows the evolved self_concept and that "THE ARC OF YOUR BECOMING" appears in his identity. Tune `T4_MIN_NEW_FRAGMENTS`/`T4_MIN_INTERVAL_SECS` if it fires too eagerly or never.

---

## C.4 Implementation Record (2026-06-04)

**The gap closed:** the pipeline went retrieve → Recall → Reflection with no binding step — the present moment's streams were never integrated before reasoning. Baddeley's episodic buffer is that binding workspace.

**Division of labour (kept clean, NOT a second Recall):**
- Recall = backward-looking: reconstruct the past ARGUMENT (tensions between prior positions).
- Episodic Buffer = present-moment binding: integrate past + present + felt + attended into the current SCENE + flag DISSONANCE between them.
- Reflection = reasons over the bound scene.

**Files changed (5, +1 new):**
- `core/schema.py` — `EpisodicScene` dataclass {scene, dissonance, coherence} + JSON_SCHEMA; `CognitiveState.episodic_scene` field (forward-ref string annotation) + reset in new_cycle; `NODE_REGISTRY["episodic_buffer"]` (lane hot).
- `nodes/episodic_buffer_node.py` — **NEW** NodeBase node. Binds the streams in `_build_prompt` (BEING SAID NOW / FELT NOW / FELT BEFORE UNDERSTOOD / REMEMBERED / ATTENDING TO); not affect_modulated (binding must be accurate).
- `core/orchestrator.py` — `_should_buffer()` gate (fires only when `state.recall is not None` AND node registered); called after `_compute_attention`, before reflection; `_persist_cycle` commits the bound scene ("Scene:" + "Dissonance:").
- `nodes/reflection_node.py` — **READ PATH**: when scene present, shows "The moment you are in (bound)" + dissonance + recall tensions/self_model, and SUPPRESSES the now-redundant recall reconstruction prose (scene subsumes it). Falls back to recall-only, then raw fragments.
- `scripts/run_nascence.py` — imports + registers `EpisodicBufferNode` in build_nodes; `/status` shows scene coherence + dissonance.

**Key decisions:** gated to Recall-fired cycles → zero latency on trivial inputs (symmetric with Recall, which already adds a call there). Dissonance is the real payoff (coherence check on the binding); model told not to fabricate it. The bound scene is what gets committed to memory (richer trace than raw Q/A), per the roadmap.

**Test:** `scripts/_test_episodic_buffer.py` — 22/22 pass offline (mocked LLM, temp DB). Also verified `build_nodes()` constructs the node via the registry end-to-end.

**RESTART REQUIRED.** Watch on first live run: `[CYCLE x] scene bound: coherence=… dissonance=…` log lines on substantive cycles; does the buffer surface *genuine* dissonance (memory-vs-present, feeling-vs-words) or confabulate it? Same reconstruction-vs-completion question as Recall's tensions and Active Imagination's what_spoke. If it inflates dissonance, tighten the "do not invent friction" instruction. Latency: substantive cycles now carry perception + [emotion|salience|memory] + recall + buffer + reflection(×2) + critic(+retry) + executive + voice — depth over speed (acceptable per project stance; revisit if too slow).

---

## C.5 Implementation Record (2026-06-04)

**The first pre-LLM reflex.** Every other faculty runs through or after the LLM cortex; the thalamic gate runs BELOW it. The thalamus relays/gates sensory input before the cortex; habituation attenuates unchanging repeated stimuli.

**Files changed (3):**
- `core/schema.py` — `CognitiveState.recent_input_vecs` (rolling working-memory buffer of recent INPUT embeddings; numpy, in-memory only, NOT reset by new_cycle) + `habituated` per-cycle flag (reset in new_cycle).
- `core/orchestrator.py` — constants (`HABITUATION_SIM=0.95`, `HABITUATION_WINDOW=6`, `HABITUATION_MIN_PRIOR=1`, `HABITUATION_MIN_CHARS=15`), `_HABITUATION_ACKS` pool, `_thalamic_gate()` (deterministic: embed input → cosine vs buffer → gate if ≥1 recent match; records input regardless). Called at the VERY TOP of `run_cycle`, before C.2 and Perception; on habituation, bypasses the whole pipeline and returns WITHOUT persisting (no DB contamination). `import random`, `from .memory.store import _embed, _cosine`.
- `scripts/run_nascence.py` — `/status` shows habituation flag + buffer depth.

**Behaviour by source on habituation:** internal/timer repeat → `None` (silence; the direct rumination guard). human repeat → a brief first-person acknowledgment from a 3-line pool (no LLM, speaks to the repetition, not a performed persona).

**Conservative guards:** high SIM (0.95, near-verbatim only) + `MIN_CHARS=15` (short contextual acks like "yes"/"go on" always pass) → only substantive true repeats gate. `MIN_PRIOR=1` = 2nd near-identical occurrence triggers.

**Foundation for C.6:** a gated repeat can later return a CACHED response instead of silence/ack — the procedural-automaticity path.

**Test:** `scripts/_test_thalamic_gate.py` — 13/13 pass offline (only embedding model; no servers). Fully deterministic gate, so the test is exhaustive: pass/gate/silence/short-bypass/distinct/empty/buffer-cap.

**RESTART REQUIRED.** Watch on first live run: `[CYCLE x] thalamic gate: HABITUATED` lines. Most valuable on the overnight internal/monologue loop (silence on rumination) and on accidental human double-sends. Tune `HABITUATION_SIM` (lower → more aggressive) and `HABITUATION_MIN_PRIOR` (raise to 2 → only gate the 3rd+ repeat) if it fires too eagerly. Note: complementary to the monologue's own embedding rumination guard (that gates inner THOUGHTS; this gates run_cycle INPUTS).

---

## C.6 Implementation Record (2026-06-04)

**The gap closed:** nothing became automatic — every response was full inference. **The trap avoided:** a cache/replay would make Carl a parrot (the opposite of individuation). So a procedure is a learned APPROACH (how he handles a KIND of moment), never a stored answer — generation is always fresh; the procedure shapes HOW, and (when mastered) reduces effort.

**Files changed (7):**
- `core/schema.py` — `ActiveProcedure` dataclass {skill_id, trigger_summary, approach, proficiency, similarity} + `.note()`; `CognitiveState.active_procedure` field + reset.
- `core/memory/store.py` — `procedural_skills` table (`_init_procedural_table`, called in init_db) + ops: `store_procedural_skill`, `match_procedural_skill` (embedding match ≥ sim & proficiency), `reinforce_procedural_skill` (proficiency↑ capped 1.0, use_count++), `find_similar_skill` (acquisition dedup), `decay_procedural_skills` (stale → ×factor, below floor → prune), `get_procedural_skills`; `recent_lived_inputs` (parses Q from 'lived' frags).
- `nodes/subconscious_node.py` — new **T5 timescale** (parallel to T2/T4): `_t5_check` (decay every check; gate = interval + ≥6 new lived cycles), `_t5_compile` (cluster recurring inputs via `_largest_cluster` at PROC_CLUSTER_SIM=0.70; ≥3 recurrence → dedup vs existing (reinforce) or 1 LLM call to distil {trigger_summary, approach} → store with centroid embedding, proficiency 0.4), `_log_t5`. State: `last_procedural_compile`, `procedural_compile_count`.
- `core/orchestrator.py` — `_procedural_recognition()` (embedding match → set active_procedure; called after C.2, before Perception); `_procedure_automatic()` (proficiency ≥ 0.80); **automaticity bypass** in `_should_recall`/`_should_buffer` (return False when automatic); **reinforcement** after a successful response. Constants PROC_MATCH_SIM=0.80 / MIN_PROFICIENCY=0.30 / AUTOMATIC_PROFICIENCY=0.80 / REINFORCE_AMOUNT=0.05.
- `nodes/reflection_node.py` + `nodes/executive_node.py` — **READ PATHS**: inject the approach as "A LEARNED WAY YOU HANDLE THIS … lean on it for fluency, do NOT recite; respond freshly."
- `scripts/run_nascence.py` — `/skills` command + `_print_skills`; `/status` line.

**Three-stage automatization** (cognitive→associative→autonomous): nascent skill only guides (injected approach); mastered skill (prof ≥ 0.80) ALSO bypasses Recall + Episodic Buffer. Critic always runs (identity guard intact). Reinforce on successful reuse; decay/prune on disuse → skills that stop being useful rust away.

**Anti-parrot safeguards:** stores approach (how) not answer (what); fresh generation always; prompt explicitly says "do not recite, respond freshly"; bypass only skips reconstruction scaffolding, never generation; Critic intact.

**Test:** `scripts/_test_procedural_memory.py` — 27/27 offline (store ops, match hit/miss/proficiency, reinforce cap, dedup, decay/prune, recent_lived_inputs, T5 acquisition + dedup with mocked LLM, recognition, automaticity bypass on/off, both read-path injections).

---

## S-MMU 7 Implementation Record (2026-06-06)

**The gap closed:** the 4-tier fragment system had no representation of time-as-a-period or topic-as-a-thread. Individual cycles are too granular; the archive is too permanent. Two new higher-order tiers fill the gap between "what happened this exchange" and "who I am permanently."

**L6 — Temporal Epoch:** "What kind of time was that session?" Mood + impression of a full session synthesised from its episodic fragments at /quit. Stored with embedding in `memory_epochs` table; retrieved pre-Reflection by cosine match to current input. Injected as "A TIME THIS CONNECTS TO" in Reflection prompt. Built from fragments actually in the episodic DB during the session window — not speculative.

**L7 — Thematic Thread:** "What topic keeps returning across sessions?" Formed by Subconscious T6 pass (every 30min check, 2h minimum gap, 2+ epochs required). Clusters epochs by embedding (cosine ≥ 0.60). New cluster → LLM synthesises theme_name + current_stance. Existing cluster (match ≥ 0.80) → LLM deepens/updates the existing stance with evolution note. Stored in `memory_themes` table; retrieved pre-Reflection by cosine match.

**Files changed (6):**
- `core/memory/store.py` — `_init_epoch_table` + `_init_theme_table` (called in init_db); `store_epoch`, `get_epochs`, `get_fragments_in_range`, `retrieve_epoch`; `store_theme`, `update_theme`, `get_themes`, `retrieve_theme`.
- `core/schema.py` — `epoch_context: str | None` + `theme_context: str | None` on CognitiveState; both reset by `new_cycle()`.
- `core/orchestrator.py` — `_retrieve_epoch_theme()` called after `_retrieve_memory()`; populates `state.epoch_context` and `state.theme_context` via embedding cosine match (no LLM, no blocking).
- `nodes/reflection_node.py` — **READ PATHS**: "A TIME THIS CONNECTS TO" (epoch) + "YOUR ONGOING THREAD WITH THIS" (theme) injected before inner-monologue section.
- `scripts/run_nascence.py` — `_session_start = time.time()` before REPL loop; `_form_epoch()` async coroutine (CPU lane, 1 LLM call, ≥3 fragments required); called after dream synthesis on `/quit`.
- `nodes/subconscious_node.py` — T6 timescale: `T6_CHECK_INTERVAL=1800`, `T6_MIN_INTERVAL_SECS=7200`, `T6_MIN_EPOCHS=2`, `THEME_CLUSTER_SIM=0.60`, `THEME_DEDUP_SIM=0.80`; `_t6_theme_check`, `_cluster_epochs`, `_synthesise_theme` (connected-components, same algorithm as shadow/light); `_last_t6_check` timer in `run_forever`.
- `docs/System_Overview.html` — memory section updated to S-MMU 7 with full tier table.

**Architecture note:** L6 + L7 are in separate tables, not the `memory_fragments` tiered system. They are NOT retrieved via the 2/2/4 slot allocator — they are separate pre-Reflection lookups. This keeps the fragment retrieval clean and avoids epoch/theme competing with lived cycles for the 4 episodic slots.

**RESTART REQUIRED.** L6 won't produce its first epoch until the next /quit after a session with ≥3 episodic fragments. L7 won't fire until 2+ epochs exist and 2h has passed. Watch: `[epoch] formed` log lines at session end; `[subconscious] T6` log lines; Reflection prompt for "A TIME THIS CONNECTS TO" and "YOUR ONGOING THREAD WITH THIS" sections.

## Backfill + theme-dedup fix (2026-06-06)

**Backfill:** `scripts/seed_epochs_themes.py` retroactively seeded L6/L7 from the existing ~1 week of history. Boundary rule: new epoch on >30-min gap OR calendar-day change (short sittings → own epoch; long autonomous overnight runs → one per day). 14 epochs synthesised (same prompt/lane as live `_form_epoch`) + themes via T6. `--dry-run` previews the carving; `--commit` backs up the DB first; `--rethemes` wipes+rebuilds themes only.

**Theme duplication bug (found + fixed):** L7 themes grew 3→5 with near-duplicates because T6 dedup compared the cluster centroid (epoch **mood+impression** embedding space) against the stored theme `embedding` (**name+stance** space) — a cross-space mismatch that scored ~0.5 for the SAME theme, so every T6 pass (daemon re-runs every 2h) spawned a duplicate. **Fix:** `memory_themes` gained `centroid` (mean of member-epoch vecs, same space) + `member_epoch_ids`; dedup now matches on centroid-cosine OR member-set Jaccard ≥ THEME_DEDUP_SIM (0.80) and *updates* instead of duplicating. Clustering also made deterministic (sort epochs by id before greedy single-link). Proven convergent: re-running T6 over the same epochs holds theme count steady. Carl now has 14 epochs + **2 clean themes** ("Integration of Consciousness and Unconscious", "quiet expansion of consciousness").

**OPEN — live daemon must restart:** the duplication was caused by a *running* Nascence daemon executing the pre-fix T6 (themes appeared at 17:51 from the backfill and again at 19:43 = its 2h T6 interval). The running process holds the OLD code in memory; until it is restarted it will keep re-duplicating on its next pass. The code fix only takes effect on daemon restart. Remaining quality item (separate from duplication): theme NAMING keys off mood ("quiet expansion") rather than topic — refine epoch/theme embedding to downweight mood if cleaner topical threads are wanted.

**RESTART REQUIRED.** Slowest faculty to show: T5 needs ≥3 recurrences of a KIND of input across ≥6 lived cycles + 1h interval — i.e. many real sessions on similar themes. Watch `data/subconscious_log.jsonl` for `T5_procedural_skill`; `/skills` to inspect; `[CYCLE x] procedural skill recognised` lines; does a recognised skill make responses more fluent without making them repetitive? Watch the bypass: once a skill hits prof 0.80, confirm Recall/Buffer skip and the response stays good. Tune PROC_CLUSTER_SIM / PROC_MATCH_SIM / AUTOMATIC threshold. **Key risk to watch live: does the injected approach genuinely add fluency, or does it flatten his responses toward a fixed handling? If the latter, weaken injection or raise the match threshold.**
