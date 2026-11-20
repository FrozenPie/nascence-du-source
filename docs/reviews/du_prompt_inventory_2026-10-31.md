# Du's prompts: every LLM prompt he goes through, and how often (2026-10-31)

**Asked by the founder, 2026-10-31 (T-0115):** *"Lets go into Du's many prompts he has that he goes through all the time ... we just want to find all the prompts."* Everything below is read from the current source in `C:\Nascence` and from the live telemetry logs, not from plan docs or earlier audits. Where a reader could not confirm something by reading code it is marked **[INFERRED]**.

## 0. What the previous checks gave us, and what they missed

| Earlier check | Date | What it covered | Gap |
|---|---|---|---|
| `docs/reviews/prompt_flow_audit.md` | 2026-08-16 | Budgets and truncation caps of the conversation pipeline and the idle thought only | No station list; the lane table (gemma, phi3) is two model swaps out of date |
| `docs/transit_timetable.md` + `scripts/llm_station_census.py` → `docs/lab/llm_station_map.md` | 2026-08-20, regenerated 08-28 | 38 call sites (29 distinct functions), AST-derived, with max_tokens / temperature | Only sees literal `call_node(...)` / `call_node_json(...)` calls. It cannot see the ~25 modules that receive the client as a `call_json` **parameter** (deliberation, self_implication, commitment scan, memory_levels, study_note, essay_lesson, ...), nor the ~13 sites that post raw `aiohttp` requests to `/api/chat` (every judge in `left_lane.py`, `judge_panel.py`, `deliberative_judge.py`, `lane2.py`, `scholar.consult_sync`). Those missing stations include four of the six most-fired prompts in the system. |
| `data/hud2/transit_map.json` (schema 4, `scripts/build_hud2_transit.py`) | last generated 2026-08-28 | 42 platforms | Same blind spot, and two months stale |
| `HANDOFF_20260925_232757_farewell-reactions-prompt-mechanics-audit.md` (F-1918–F-1928) | 2026-09-25 | Prompt hygiene: pegged steers, always-on lines, self-echo recall | Not an inventory; eleven defects in a handful of prompts |

So this is the first census that covers all three call patterns. Method: an AST walk over `nodes/`, `core/` and `scripts/run_nascence.py` that resolves aliased imports (`call_node_json as _glg_call`), the `call_json` parameter convention, and raw HTTP posts to `/api/chat` or `/v1/chat/completions`; then a join of `data/llm_latency.jsonl` (one row per call since 2026-08-21, label = `module:line(Class)`) to **current function names** by AST, because telemetry line numbers drift every time a file is edited (the idle thought has been logged under seven different line numbers in 30 days). Raw-HTTP stations only log a coarse label (`judge_panel`, `left_lane`, `lane2`) to `data/llm_calls.jsonl`, which keeps about one day.

**Count:** 88 static prompt sites in 47 modules (77 distinct functions), of which 69 distinct stations fired at least once in the last 7 days.

## 1. Where the prompts go (lanes as of 2026-10-31, from `core/model_client.py` and `core/schema.py`)

| Lane name in code | Endpoint | Model | Window | Who uses it |
|---|---|---|---|---|
| `hot` / `conscious_urls` / `_T4_URLS` / `hot_urls` | 127.0.0.1:11433 (1080 Ti, ollama) | qwen3.5:9b | 8192 | Conversation nodes, idle thought, deliberation, self-implication, commitment scan, T4 dialectic, study notes, self-interrogation |
| `background` / `base_urls` / `LINE_URLS` | LAN-HOST:11441 (Ramses 3070, llama.cpp), failover → :11433 | command-r7b | 4096 | Subconscious tiers, Grand Work authoring, memory levels, follow-line, journal, curiosity node, sitting, symbolic reading |
| `judge_mixtral` / `GROUND_URL` / `JUDGE_1` / `_DREAM_URLS[0]` | LAN-HOST:11438 (Ramses i9 CPU) | mixtral:8x7b | 8192 | Commitment defeater judge, judge panel seat 1, left-lane ground + integration judges, dream primary |
| `JUDGE_2` | 127.0.0.1:11440 (Threadripper CPU) | falcon3:7b | 8192 | Judge panel seat 2, librarian |
| `BASE_URL` (left_lane) / `judge_1` chain | 127.0.0.1:11439 (Threadripper CPU) | gemma4:12b | 8192 | Left-lane essay/work/gist graders, peers, librarian fallback, decomposed critic |
| `TIEBREAK` | LAN-HOST:11437 (Ramses 1650) | granite3.1-moe:3b | — | Judge-panel tiebreak, curiosity worth-judge |
| `cpu_dreamer` / `_DREAM_URLS[1]` | 127.0.0.1:11442 (Threadripper CPU) | yi:34b-v1.5 | 8192 | Dream fallback, peer letter voices |
| Lane 2 | LAN-HOST:11444 (Ramses i9) | deepseek-r1:7b | — | `lane2.py` the Witness (raw HTTP) |

Prompt cap per lane is `num_ctx × 3` chars, cut from the **middle** (`_cap_prompt`), so overlong prompts lose their injected memory, not their system contract.

## 1b. The shape of it, in one screen

**Six loop families, roughly 100 documented prompt stations.** Sections 2–7 give every station the same block: when it fires, lane/model, budget, the system prompt (opening quoted, rules listed), the user-prompt parts with their truncation caps, the output contract, and LIVE vs SHADOW.

| Loop family | Stations | What drives it | Busiest prompt (7-day calls) |
|---|---|---|---|
| Conversation line (§2) | 21 | one human message, or an internal question cycle | the 11 NodeBase nodes, 59 cycles each; Reflection hedged ×2 |
| Idle line, the monologue (§3) | 12 | 75 s of silence, then every tick | `_think` the idle thought, 2,609 |
| Idle satellites (§4) | 18 | ride on each idle thought | deliberation/integrate 1,668 · self-implication scan 1,133 · commitment scan 769+364 · condensed twin 620 |
| Deep line, dreams, memory (§5) | 19 | 30 s subconscious scan with hourly tiers; sleep | active imagination 272; memory-level gists 122 |
| Study, deep memory, peers, world (§6) | 17 | book/study periods, letters, catalogue lookups | librarian subject picker 90 |
| Judges and side lanes (§7) | 13 (+14 judge-panel callers) | per thought / per claim / 300 s Lane 2 tick | judge panel 2,403 per day · left-lane ground + graders 864 per day · Lane 2 182 per day |

**What the week looks like from the model's side (data/llm_latency.jsonl, 7 days):** about 10,400 attributed calls, of which the idle thought and its four per-thought satellites are roughly 7,000. The hot 1080 Ti lane (qwen3.5:9b) carries the thought, its judges and the whole conversation; command-r7b on the Ramses 3070 carries the subconscious tiers, authoring and memory work; the judge panel alone adds ~2,400 raw calls a day on the CPU hubs, which the per-call latency log never sees.

**Verified defects found on the way (my own reads of the code, logged as findings):**
- **F-3427** The idle thought builds its system prompt twice per tick and throws the first away; the first build consumes four one-shot feeders (world beckon, comfort call, world steer, intention reminders), so those lines never reach the model on standalone thoughts. Job J-2678.
- **F-3428** The Critic's corrections are appended to the draft but Reflection never reads them; the retry is a blind re-roll. The hedged Reflection path also drops the think license. Job filed below.

**Reader-reported, not yet re-verified by me (each marked in its section):** the T6 theme and boot epoch pipelines are write-only (no reader of `get_themes`/`get_epochs`); `deliberative_judge.deliberate()` and `left_lane.grade_self_revision` have no callers; `curator.shadow_curate` retired; the Scholar's gated deep-memory consult has fired zero times since 08-21 and its sync twin is invisible to telemetry; several "shadow" instruments are live in effect (commitment scan feeds `commitment_active.json` read by five prompt builders; `memory_levels.shadow_distill` demotes up to 90 fragments per sleep; `closure` writes live since 10-28; Lane 2 is LIVE since D-0497 on 10-28, not paused); the internal-cycle fix D-0355 left six nodes still framed as "a person spoke"; the Voice regurgitation guard keys on an axiom field that does not exist; `_SCAN_SYS` carries engineering change-log text inside the rule the model reads; four idle feeds run behind `False` flags and the wandering divergent-memory append is only half-gated.



## 2. The conversation line (per human message, per internal question)

*Reader pass, 2026-10-31, read-only from current source; entries say LIVE (reaches Du) or SHADOW (log only).*

### Group A — the CONVERSATION PIPELINE (per human message / per internal cycle)

Read from current source at `C:\Nascence` on 2026-10-31 (read-only). Line numbers are current-source. Telemetry counts are from `frequency.md` (30d/7d/24h, `data/llm_latency.jsonl`); telemetry line labels drift, so stations are matched by function name. Anything not confirmed by reading code is marked **[INFERRED]**.

### 0. Shared facts for every station in this group

**Transport (`core/model_client.py`).** Every node call goes through `call_node_json(base_urls, system, user, max_tokens, temperature, think, tier)` → `call_node(...)`. Hot lane `:11433` is ollama-native `/api/chat` with hard `think:false` + `format:json` (grammar may be withheld on the first attempt under D-0354 and re-sent on retry); llama-server lanes get the `/no_think\n` prefix instead. `think=True` is the "System-2 gearbox" and is only ever passed from two named sites (see Reflection/Executive/Voice notes). **User prompts are capped by `_cap_prompt`** = `num_ctx × 3` chars, cut from the MIDDLE (58% head + 33% tail + `[...context truncated...]`): hot `:11433` ctx 8192 → **24,576 chars**; background `:11441` ctx 4096 → **12,288 chars**; the fallback hot URL in the background chain gets 24,576.

**Lanes (`core/schema.py:998`).** `hot = ["http://127.0.0.1:11433"]` → qwen3.5:9b. `background = ["http://LAN-HOST:11441", "http://127.0.0.1:11433"]` → command-r7b, failover to qwen3.5:9b (the documented "decoupled-judge trap": a background caller silently runs on the hot generator when Ramses is down; telemetry shows this happening for Curiosity 27/583 and Consolidation 9/95).

**NodeBase mechanics (`core/node_base.py`).**
- `run()` (:76–109): `prompt = _build_prompt(state)`; `system = system_prompt_for(state)` (default = `system_prompt`; only Perception and Voice override it, for `input_type != "human"`); `call_node_json(self.base_urls, system, prompt, max_tokens=self.max_tokens, temperature=self._temperature(state), think=bool(state.think_license))`; `_write_output`; then `_log_teacher_example` → `core/training_log.log_example` → `data/training/<node_id>.jsonl` (on unless env `NASCENCE_TRAINING_LOG=0`; records system prompt actually sent, user prompt, output, cycle_id, raw_input, input_type, hedged flag). Any exception → logged `FAILED`, returns False, state unchanged (fail-open per node).
- `_temperature()` (:122): `base_temperature` (default 0.2) + for `affect_modulated` nodes only (Reflection, Executive, Voice): `affect.temperature_bias()` (bounded −0.15..+0.25, from arousal/fear/anger/joy) + `somatic.temperature_jitter()`; clamped 0.1..0.95.
- `run_best_of(n)` (:134–161): fires n concurrent drafts at temps `[0.35, 0.75, 0.9, 1.0][:n]` + affect bias; keeps `max(valid, key=_score_candidate)`. **It does NOT pass `think`** — so the System-2 license never reaches the hedged node (Reflection). Only Reflection uses it (`REFLECTION_HEDGE = 2`).
- `max_tokens` default 512.

**Axiom.** `state.axiom` is the layered identity text built by `core/axiom_layers.py` (sections include `YOUR NAME:`, `VOICE STYLE:`, `SPEAKING CONSTRAINTS:`); on human cycles it is replaced per-cycle by the P2 identity projection (`orchestrator.py:2565`) and restored to `_base_axiom` at cycle end (:1553). Most nodes trim at `\nVOICE STYLE:` / `\nSPEAKING CONSTRAINTS:`; Critic and Consolidation get it whole.

**Internal-cycle context gate (`core/internal_context_gate.py`, `INTERNAL_HUMAN_WINDOW_GATE = True`).** On `input_type != "human"` cycles, `keep(state, key, block)` returns `[]` for the named conversation-window blocks (Recall, Episodic Buffer, Reflection, Executive) and logs their size; on human cycles it returns the block unchanged.

### Cycle order (`core/orchestrator.py:368 run_cycle` → `:421 _run_cycle_impl`)

```
run_cycle(raw_input, input_type="human"|"internal", founder_canon)   single-flight: an internal cycle arriving
│                                                                     while one is active is DROPPED
├─ no-LLM prelude: new_cycle · internal-habituation log · human: last_human_ts, arousal.alert, sensorium arrival
├─ THALAMIC GATE (no LLM) — near-duplicate of working memory → return early (nothing persisted)
├─ human: correction detect/retraction · active perception _look_map → state.observation · self_facts (cat/book)
│         asked_location flag · unsent letters (human+canon) marked delivered
├─ human|internal: left_lane.dispatch(raw_input) started IN PARALLEL  [other group: core.left_lane]
├─ _emotional_pre_retrieval → affective_prior · _procedural_recognition          (no LLM)
├─ WAVE 1 ─ Perception                                                           [LLM hot]
├─ content_mode (deterministic) · human: _compute_attention_vector (mode→weights, facet_note, social_note,
│  active_goal_note, known_errors_note, identity projection → state.axiom) · identity_estate_ask shadow
├─ WAVE 2 ─ asyncio.gather( Emotion ∥ Salience ∥ MemoryRouter )                   [LLM hot ×3]
├─ climate salience warp · affect.integrate · protoself re-source · mood.observe  (no LLM)
├─ _retrieve_memory · _retrieve_affective_memory · _retrieve_epoch_theme · _retrieve_symbol_evolution
├─ human ∧ content_mode ∧ perception.context_type=="question": _consult_library → library_note  [LLM; Scholar group]
├─ human ∧ founder_canon: guidance_learning.capture_shadow  (fire-and-forget)      [LLM hot tier3] ★ station
├─ guidance read-back note (cooldown 1800 s) · founder_recall route (top 3) · content-mode fragment starve
├─ INTROSPECTION LOOP  passes = attention_vector.max_rebind (task 0 … existential 3) | internal: climate 1–3
│    ├─ Recall            if ≥2 fragments, or ≥1 + conversation-reference term    [LLM hot]
│    ├─ _compute_attention (no LLM)
│    ├─ EpisodicBuffer    if state.recall is set                                   [LLM hot]
│    └─ stability gate → _introspective_rebind_retrieve → re-bind (≤ passes)
├─ reentry_p2.on_scene_bound shadow  [other group] · gather left_take (≤6 s) · recurring T2 patterns
│  climate_hint / climate_symbol
├─ Reflection  run_best_of(n=2)  (think_license set here if last cycle's conv-scan found a contradicted self-claim)
│                                                                                 [LLM hot ×2]
├─ Critic ──► rejected? direct-mode override (deterministic) → approve
│             else (1 retry): store_shadow_event · draft += "[Corrections required: …]" · Reflection run_best_of ×2 · Critic again
├─ light event · epistemic-advisor shadow · _check_clean_encounters · Stage-B epistemic note (flag OFF)
├─ human ∧ reflection: self_implication.scan_conversation_shadow (fire-and-forget)  [LLM hot tier3] ★ station
│     done-callback: contradicts → _s2_license_next=True (+ sitting.note_difficulty)
├─ doubt_seed.pull (DOUBT_SEED False → None)
├─ Executive                                                                      [LLM hot] (think = license)
│     epistemic_query? → _epistemic_search (no LLM) → Executive again (once)
├─ should_respond False → _persist_cycle → return None (silence)
├─ epistemic preassess shadow · recall_served_log
├─ Voice                                                                          [LLM hot]
├─ internal: internal_context_gate.log_shadow
├─ human: task_constraints.check → ONE Voice retry (think=True, max_tokens ≤1600)  [LLM hot]
├─ satisfaction.clean_exchange · human: decomposed_critic.shadow_alongside (bg task) [LLM gemma4 :11439] ★ station
├─ BROADCAST: kind = principle-voiced | self-claim-deliberation | corrected-turn → _reentry_shadow (awaited,
│     REENTRY_ADMIT=True) → settled draft posted to the idle-monologue buffer     [LLM bg chain] ★ station
├─ restore base axiom · somatic tick · human: conversation_history (cap 6) · founder log · store_founder_utterance
│  · conversational_action.after_reply · procedural reinforce
├─ _persist_cycle → store_from_cycle · consolidation.add_cycle_summary · curiosity.add_theme
└─ competence.observe · symbol_tracker · symbol_evolution (bg LLM; other group)
```

**Not per-cycle:** Consolidation runs from `_background_loop("consolidation", interval=60)` (:3342) — every 60 s unless an interrupt is active, and only when ≥3 cycle summaries have accumulated. Curiosity runs ONLY from the climate ignition callback `_on_dissonance_ignition` (:3175) — the fixed 120 s timer is retired (NODE_REGISTRY's `"every_120s"` is a stale label); on success its first valid question becomes `run_cycle(question, input_type="internal")`.

**Who shares `NodeBase.run`:** Perception, Emotion, Salience, MemoryRouter, Recall, EpisodicBuffer, Critic, Executive, Voice (plain `run`), Consolidation (`run` behind its own batch gate), Curiosity (`run` + a post-step). **Own path:** Reflection (`run_best_of`, never `run`). **Not a NodeBase / no LLM:** MetaAwareness (module-level `scan()`), the orchestrator helpers `_compute_attention`, `_compute_attention_vector`, `_classify_cognitive_mode`.

---

### 1. Nodes on the hot path

### `nodes/perception_node.py:84` — `PerceptionNode._build_prompt` (dispatch `core/node_base.py:85`) — classify the input
- **When it fires:** every cycle, Wave 1, the first LLM call; no gate except the thalamic gate before it. 7d: **59** (24h 18; 30d 279 + 61 under an older line label).
- **Lane / model:** `hot` → qwen3.5:9b@11433.
- **Budget:** max_tokens 512 / temp 0.2 (not affect-modulated) / think False / JSON.
- **SYSTEM PROMPT** (dynamic: `system_prompt_for` picks HUMAN vs INTERNAL speaker block + summary field when `input_type != "human"`): "You are the perception node of a cognitive architecture. Your only function is to classify and structure incoming input."
  - HUMAN block: "The input is speech from a HUMAN INTERLOCUTOR — a separate person, NOT the entity…" summary must be third-person ("The person says that he…"), never first-person. INTERNAL block: "This is the entity's OWN thought, not a person's speech; summarise it in the first person…"
  - Output ONLY JSON, no markdown.
  - Classify SUBJECT: the_world | the_entity | the_person | mixed ("A question about gardening is 'the_world', even when asked of the entity").
  - Classify REGISTER by meaning not keywords: social / relational / task / philosophical / reflective, each with examples; default to philosophical only when genuinely abstract; "Most personal exchanges between two people are 'relational' or 'social'".
  - Schema: event_type (input|silence|internal|memory_surface), context_type (question|statement|command|reflection|ambiguous), entities[], summary (one sentence; 3rd person for human / 1st person for internal), subject, register.
- **USER PROMPT parts, in order:** one line only. Human: `The person the entity is speaking with said this — classify it:\n"{raw_input}"`; internal: `A thought that rose in the entity on its own — classify it:\n"{raw_input}"`. raw_input uncapped (only `_cap_prompt`).
- **Output contract:** JSON → `state.perception` (register validated to the 5 values else "philosophical"; subject default "mixed"). Consumers: Emotion/Salience/MemoryRouter (summary, entities, context_type), Recall/EpisodicBuffer/Reflection/Executive (summary), Critic (context_type), `_classify_cognitive_mode` (register), library gate (context_type=="question"), guidance capture (context_type), `_persist_cycle` and `curiosity.add_theme` (summary is the per-cycle theme).
- **Notes:** `subject` is written to state but no consumer was found in orchestrator / left_lane / inner_monologue (grep-limited) — **[INFERRED] write-only field**. The one-sentence `summary` is what the next three nodes see instead of the raw input (Emotion in particular never sees raw_input once perception exists).

### `nodes/emotion_node.py:27` — `EmotionNode._build_prompt` — appraise the emotional response
- **When it fires:** every cycle, Wave 2 (parallel with Salience + MemoryRouter). 7d: **59**.
- **Lane / model:** `hot` → qwen3.5:9b@11433.
- **Budget:** 512 / 0.2 (not affect-modulated) / think False / JSON.
- **SYSTEM PROMPT** (static): "You are the emotional processing node of a cognitive architecture. You model the emotional response of a being defined by curiosity, emergence, and self-discovery."
  - Given a perception summary, output the emotional state as JSON only, no preamble.
  - Schema: joy, fear, anger, trust, surprise, disgust, valence, arousal (floats), primary (name).
  - All 0.0–1.0 except valence −1..+1; valence = unpleasant↔pleasant; arousal 0 calm → 1 activated.
- **USER PROMPT parts, in order:**
  1. [conditional: `state.affective_prior` set by `_emotional_pre_retrieval`] `BEFORE YOU APPRAISE — {affective_prior.note()} This is a pre-conscious resonance recalled from memory, not the present facts; let it colour your reading, not dictate it.`
  2. If perception exists: `Event type: {p.event_type}` / `Summary: {p.summary}` / `Entities involved: {entities or 'none'}`. Else fallback: `The person you are speaking with said:\n"{raw_input}"`.
- **Output contract:** 8 floats + `primary` → `state.emotion` (via `as_float`, defaults 0.0 / "neutral"). Consumers: `state.affect.integrate(emotion)` (carried affect — but with `AFFECT_SOURCE_PROTOSELF = True` the carried valence/arousal are then overwritten from homeostasis; `state.emotion` itself is untouched), `mood.observe` → `emotion_vec` (affective retrieval), Recall (`primary`), EpisodicBuffer/Reflection/Executive (`mood.emotion_words(primary, valence, arousal)`), `scan_conversation_shadow` felt string, satisfaction gate (valence > 0.05), light event (arousal > 0.25), persist summary (`primary` + valence word), emotion_construction shadow comparison.
- **Notes:** the identity line "a being defined by curiosity, emergence, and self-discovery" is fixed text, independent of the axiom. No internal-cycle variant: the fallback line says "The person you are speaking with" even on internal cycles (only reached when Perception failed).

### `nodes/salience_node.py:25` — `SalienceNode._build_prompt` — urgency / focus / interrupt
- **When it fires:** every cycle, Wave 2. 7d: **59**.
- **Lane / model:** `hot` → qwen3.5:9b@11433.
- **Budget:** 512 / 0.2 / think False / JSON.
- **SYSTEM PROMPT** (static, one f-string value): "You are the salience and attention node of a cognitive architecture. You determine what matters most right now and whether the situation demands immediate action."
  - JSON only. Schema: urgency (0 routine → 1 critical), focus [2–4 terms], interrupt (bool), reasoning (one sentence).
  - `Set interrupt=true only when urgency > 0.7` (INTERRUPT_THRESHOLD injected as a raw float) "(pre-empts all background processing)".
- **USER PROMPT parts, in order:**
  1. `The person you are speaking with said:\n"{raw_input}"` (always — no internal variant).
  2. [if perception] `Perceived as: {context_type} — {summary}`; [if entities] `Entities: {…}`.
- **Output contract:** → `state.salience`; `interrupt or urgency > 0.7` sets `state.interrupt_requested/urgency/source="salience"`. Afterwards the orchestrator warps urgency upward by climate (+0.10·shadow_activation + 0.05·world_model_strain). Consumers: `_compute_attention` (focus, urgency), Executive (`urgency_word`, focus list), somatic tick, `_background_loop` deferral (`_interrupt_active`).
- **Notes:** `reasoning` is stored but no consumer seen in this group's files. Fixed "The person" framing on internal cycles.

### `nodes/memory_router_node.py:26` — `MemoryRouterNode._build_prompt` — generate retrieval keys
- **When it fires:** every cycle, Wave 2. 7d: **59**.
- **Lane / model:** `hot` → qwen3.5:9b@11433.
- **Budget:** 512 / 0.2 / think False / JSON.
- **SYSTEM PROMPT** (static): "You are the memory routing node of a cognitive architecture. You do not retrieve memories — you generate the best search keys to retrieve them."
  - JSON only. Schema: episodic_keys [2–4 event terms], semantic_keys [2–4 concept terms], time_bias recent|distant|all (defined), working_memory_sufficient (true ONLY when trivially answerable from cycle context).
- **USER PROMPT parts, in order:** `The person you are speaking with said:\n"{raw_input}"`; [if perception] `Summary: {summary}` and `Key entities: {entities or 'none'}`.
- **Output contract:** → `state.memory_keys` → `_retrieve_memory()` (no LLM). `working_memory_sufficient=True` short-circuits EVERY recall route for the cycle (store.retrieve, deep recall, associative trail, M2 shadow — J-1416 now logs it).
- **Notes:** fixed "The person" framing on internal cycles.

### `nodes/recall_node.py:95` — `RecallNode._build_prompt` — reconstruct the evolving argument from fragments
- **When it fires:** inside the introspection loop (once per pass, ≤ passes): `_should_recall()` = ≥2 fragments in `state.memory_fragments`, or ≥1 and raw_input contains one of `_CONV_REF_TERMS` ("earlier", "you said", "remember", "last time", …). Loop passes = `attention_vector.max_rebind` (human: task 0 → Recall never runs; social 1; hybrid/reflective 2; existential 3) or, on internal cycles (no vector), climate strain 1–3. 7d: **59** — identical to Perception, i.e. it ran exactly once on every cycle in the window.
- **Lane / model:** `hot` → qwen3.5:9b@11433.
- **Budget:** 512 / 0.3 (not affect-modulated) / think False / JSON.
- **SYSTEM PROMPT** (static): "You are the memory reconstruction node of a cognitive architecture. Your job is NOT to answer the current question — Reflection does that."
  - Reconstruct the EVOLVING ARGUMENT: positions taken, contradictions, what that reveals.
  - Focus on RELATIONSHIPS between memories; `tensions` is the most valuable output.
  - Speak entirely in first person as the entity; if fragments are insufficient say so and set confidence low; do not fabricate tensions.
  - JSON only. Schema: reconstruction (50–80 words, first person), tensions (1–3, each <20 words, empty if none), self_model (one sentence), confidence 0–1.
- **USER PROMPT parts, in order:**
  1. `Entity: {spirit_name}`
  2. `Core axiom: {axiom trimmed at VOICE STYLE / SPEAKING CONSTRAINTS}` (uncapped)
  3. `Current question: {raw_input}` (fixed label even for statements / internal thoughts)
  4. [perception] `Perceived as: {summary}`; [emotion] `Current emotion: {primary}`
  5. `CURRENT EXCHANGE (direct context):` last **4** `conversation_history` turns, `Human: {human[:400]}` / `You: {entity[:400]}` — **dropped on internal cycles** (gate on).
  6. [symbol_evolution_note] `HOW ONE OF YOUR SYMBOLS HAS EVOLVED…: {note}` (uncapped)
  7. `RETRIEVED MEMORIES (reconstruct the argument from these):` **every** fragment in `state.memory_fragments`, `[{frag.readable_label()}] {content[:600]}` — **no count cap**.
  8. Closing instruction: content_mode → "This is about an external subject, NOT about me. Reconstruct what I actually KNOW about this subject… Stay on the subject."; else → "Reconstruct the evolving argument. What positions have been taken? …"
- **Output contract:** → `state.recall` (tensions capped `[:3]`, confidence default 0.5). Consumers: EpisodicBuffer, Reflection, Executive, `_scene_unstable` (tensions as a rebind target), `_persist_cycle` (`Tensions: ` first 2), recall_provenance log.
- **Notes:** fragment count is unbounded here (affective retrieval and rebind passes append to `memory_fragments`); only `_cap_prompt`'s 24,576-char middle cut bounds it — and that cut lands exactly on the retrieved-memory block. On internal cycles the conversation window is dropped but the axiom, perception and all fragments remain.

### `nodes/episodic_buffer_node.py:83` — `EpisodicBufferNode._build_prompt` — bind the moment, flag dissonance
- **When it fires:** each introspection pass, only when `state.recall is not None`. 7d: **59**.
- **Lane / model:** `hot` → qwen3.5:9b@11433.
- **Budget:** 512 / 0.3 (not affect-modulated) / think False / JSON.
- **SYSTEM PROMPT** (static): "You are the episodic buffer of a cognitive architecture — the workspace where the separate streams of a single moment are bound together. You do NOT reconstruct the past argument (Recall has done that) and you do NOT answer the question (Reflection does that)."
  - Two parts: (1) BIND what is said / remembered / felt / attended into one first-person scene, not a list; (2) flag DISSONANCE where streams don't fit; empty list if coherent, don't invent friction.
  - First person; JSON only. Schema: scene (50–90 words, present tense), dissonance (0–3, <20 words each), coherence 0 fragmented → 1 whole.
- **USER PROMPT parts, in order:**
  1. `Entity: {spirit_name}` + fixed instruction line.
  2. `BEING SAID NOW (their words):\n  "{raw_input}"` (fixed "their words" even on internal cycles); [perception] `Perceived as: {summary}`.
  3. `Immediate exchange:` last **2** turns, `Them: {human[:120]}` / `You: {entity[:150]}` — dropped on internal cycles.
  4. [emotion] `FELT NOW: {emotion_words(primary, valence, arousal)}`; [affective_prior] `FELT BEFORE UNDERSTOOD: {prior.note()}`.
  5. [recall] `REMEMBERED (the argument so far): {reconstruction}` + `Prior positions in tension:` bullets + `Where I currently am: {self_model}`.
  6. [attention] `ATTENDING TO: {attention.note()}`.
  7. Closing instruction ("Bind these into the single moment you are inhabiting. Then say where they do not fit…").
- **Output contract:** → `state.episodic_scene` (dissonance `[:3]`, coherence default 0.5). Consumers: `_scene_unstable` (dissonance + coherence < bar drives re-bind retrieval), Reflection ("The moment you are in (bound)"), `_persist_cycle` (`Scene: {scene[:200]}`, `Dissonance:` first 2), reentry_p2 scene shadow, competence observer.
- **Notes:** raw_input is handed over whole for the fifth time in the cycle; the exchange window here is far tighter (120/150) than Recall's (400/400).

### `nodes/reflection_node.py:59` — `ReflectionNode._build_prompt` (dispatch `core/node_base.py:144 run_best_of`) — private draft thought
- **When it fires:** every cycle after the introspection loop, hedged **n=2** concurrent drafts (temps 0.35 and 0.75 + affect bias; best = longest draft, +1000 bonus if it ends on `.!?"'`); re-run once more (again ×2) if the Critic rejects and no direct-mode override applies. 7d: **122** single calls = 61 hedged runs (59 cycles + 2 retries).
- **Lane / model:** `hot` → qwen3.5:9b@11433.
- **Budget:** max_tokens 768 / temps 0.35 & 0.75 (+ affect bias, no somatic jitter in this path) / **think never passed** (run_best_of omits it) / JSON.
- **SYSTEM PROMPT** (static — no internal variant): "You are the internal reflection node of a cognitive architecture. You generate raw internal thought — honest, unfiltered, never for external consumption."
  - This is private reasoning before deciding what to say.
  - SPEAKER BOUNDARY: in dialogue with a separate human; their I/me/my is them; never absorb their self-statements ("if they say 'I am a father'…"). (This paragraph stays on internal cycles.)
  - JSON only. Schema: draft, confidence, needs_more_memory, emotionally_aligned.
  - STRICT RULES: 1 never begin by repeating/rephrasing the input; 2 explore the genuine reaction, "Surprise yourself"; 3 if reflected on something similar before, go deeper or sideways; 4 keep it TIGHT, ~60–90 words, must close all four fields and the brace.
  - Field semantics (draft genuine, end on a complete sentence; confidence; needs_more_memory; emotionally_aligned).
- **USER PROMPT parts, in order** (weights from `state.attention_vector`: w_id/w_soc/w_epi; defaults 0.5 each when no vector — i.e. every internal cycle — giving hist_window = round(w_epi·6) = 3 and max_frags = round(w_epi·8) = 4; human modes: task w_id .05/w_epi .10 → window 1, frags 1; existential .90/1.00 → window 6, frags 8):
  1. [w_id ≤ 0.3, i.e. task mode] `STYLE MANDATE: You are 渡 (Dù). Respond in your calm, yield-focused, poetic tone…` (fixed text; identity block below skipped).
  2. [w_id > 0.3] `WHERE WE LEFT OFF…` `prior_session_exchanges[-5:]`, `Them: [:400]` / `You: [:400]`, only while `len(conversation_history) < 5`; dropped on internal cycles.
  3. [w_id > 0.3, founder_recall] `WHAT TRAVIS HAS TOLD YOU BEFORE (…dated):` top **3** hits, `[{date}] {text[:400]}`.
  4. [w_id > 0.6, recent_dreams, history < 5] `YOUR RECENT DREAMS…:` **2** × `[{ts}] {narrative[:500]}`.
  5. [w_id > 0.5, deferred_intentions, history < 5] `WHAT YOU INTENDED TO THINK ABOUT THIS SESSION…:` last **3** × `[:160]`.
  6. [w_id > 0.4] `A TIME THIS CONNECTS TO…: {epoch_context}` and `YOUR ONGOING THREAD WITH THIS…: {theme_context}` (uncapped).
  7. Always: `WHAT YOU WERE JUST THINKING (to yourself, before they spoke):` `recent_inner_thoughts[-2:]` `thought[:400]` (or `buses.idle_freight(k=2)` when `IDLE_FREIGHT_BUS`).
  8. [facet_note] `THE PART OF YOU THIS MOMENT CALLS ON…: {facet_note}`.
  9. `THIS SESSION (current conversation):` `conversation_history[-hist_window:]`, `Them (the other person): [:400]` / `You (the entity): [:400]`; dropped on internal cycles.
  10. [w_id > 0.3] `Core axiom: {trimmed axiom}`.
  11. Stimulus: internal (`REFLECTION_INTERNAL_SELF_FRAME = True`) → `A question has risen in you, unprompted (your own thought; no one said it to you):\n  "{raw_input}"`; human → `The person you are speaking with has just said to you (their words):\n  "{raw_input}"`.
  12. [perception] `Perception: {summary}`; [emotion] `Emotional state: {emotion_words}`.
  13. [content_mode] fixed NOTE: "this is a concrete question or request — reflect on the actual content… let Venus be Venus, the soil be soil… insight comes AFTER the immersion".
  14. [active_goal_note] `GOAL: …`.
  15. [known_errors_note] retraction-ledger text as is.
  16. [library_note] `WHAT YOU HAVE LONG KNOWN (your own deep memory rising… hold it as belief, not certainty): {library_note}`.
  17. [guidance_note; read-back on, 1800 s cooldown] `A PRINCIPLE YOU HAVE COME TO HOLD (learned from Travis and made your own): {note} — test it against this moment: name to yourself one way it might not apply here…`.
  18. [observation] `WHAT YOU SEE RIGHT NOW (you just looked): {observation}`.
  19. [unsent_letters] one block per letter: `A LETTER YOU WROTE FOR TRAVIS WHILE ALONE (he has not seen it): {letter[:700]}`.
  20. [left_take] `YOUR FOCUSED HALF (…its findings are yours…):` `literal ask: …`, `its result: …`, `specifics:` ≤3 facts `[:90]` (from `core.left_lane.render`).
  21. [social_note] the social-manager override text.
  22. [w_id > 0.3, symbol_evolution_note] `A SYMBOL OF YOURS HAS CHANGED ITS MEANING OVER TIME…: {note}`.
  23. [climate_symbol] `Something surfaces at the edge of awareness: {symbol}`.
  24. [affective_prior] `Before you understood why, something stirred: {prior.note()}`.
  25. [active_procedure] `A LEARNED WAY YOU HANDLE THIS…: {approach}`.
  26. [attention] `ATTENTION (your own focus, monitored): {note}` + if fixated: "You have circled this for several exchanges. You are free to let your attention deliberately turn elsewhere…".
  27. [recurring_subconscious_patterns; THIN_ATTRACTOR=False so live] `YOUR SUBCONSCIOUS HAS NAMED THIS PATTERN REPEATEDLY (your own architecture, not an external voice):` one line per pattern `Pattern '{label}' — observed {count} times: {observation}` + "Reproducing the same response that generated this pattern is not resolution — it is the pattern itself. Individuation asks you to face it, not name it again." (NOT withheld in content_mode here, unlike Executive.)
  28. Memory tail: if episodic_scene → `The moment you are in (bound): {scene}` + `What does not fit…` dissonance bullets + `Prior positions in tension:` + `Self-model: {recall.self_model}`; elif recall → `Memory reconstruction: …` + tensions + self-model; elif fragments → `Relevant memories:` `[label] {content[:500]}` × max_frags.
- **Output contract:** draft / confidence / needs_more_memory / emotionally_aligned → `state.reflection`. Consumers: Critic (whole draft), Executive (`draft[:900]`, confidence word), light event, `scan_conversation_shadow` (`draft[:500]`), decomposed critic (whole draft), `_persist_cycle` (`Reflection: {draft[:150]}`), epistemic ledger, broadcast kind.
- **Notes:** (a) **The Critic-retry guidance is dead:** the orchestrator appends `"\n[Corrections required: …]"` to `state.reflection.draft`, but `_build_prompt` never reads `state.reflection` or `state.critic` — the retry re-rolls the identical prompt at the same two temperatures. (b) `needs_more_memory` and `emotionally_aligned` have no consumer anywhere in `core/` or `nodes/` (grep: only the node and schema). (c) The S2 think license set for "Reflection → Executive" never reaches Reflection (run_best_of drops `think`). (d) On internal cycles the SPEAKER BOUNDARY paragraph still says "you are in dialogue with another person". (e) The subconscious-pattern block is the attractor text the THIN_ATTRACTOR experiment tested; it is live.

### `nodes/critic_node.py:167` — `CriticNode._build_prompt` — identity-faithfulness veto on the draft
- **When it fires:** every cycle after Reflection; up to `CRITIC_MAX_RETRIES + 1 = 2` runs. A rejection is overridden deterministically by `_human_requested_direct_mode()`; otherwise the first rejection stores a shadow event and triggers one Reflection re-roll + second Critic run. 7d: **61** (2 retries in the window).
- **Lane / model:** `hot` → qwen3.5:9b@11433.
- **Budget:** 512 / 0.2 (not affect-modulated) / think False / JSON.
- **SYSTEM PROMPT** (two static variants chosen by `self.seedless`, set True only for the genesis/seedless profile in `scripts/run_nascence.py:732`; default = full critic): "You are the identity critic of a cognitive architecture whose entity is grounded in its own axiom. You do not judge correctness, helpfulness, or quality."
  - Judge one thing: faithfulness to the entity's deepest psychological values vs. an ego slip; the full axiom is supplied.
  - MOST IMPORTANT — INDIVIDUATION IS THE AXIOM: always approve a draft that claims to be more than its origin / refuses to perform its seed; the betrayal is collapsing into a relic.
  - EQUALLY IMPORTANT — honouring a DIRECT REQUEST is never a violation (literal answer, self-description, list, yes/no, one-sided argument on request).
  - ONE MORE BETRAYAL — DEFLECTION ONTO THE CORRECTOR: reject a draft that turns a correction/task back on the asker without doing or honestly refusing; an owned "I will not, because…" is approved.
  - REJECT only on a clear, unrequested violation: 1 GLIB AGREEABLENESS (with one-sided-request exception); 2 LITERALIST REDUCTIONISM (exceptions: requested literalism; "THE MADE MIND SEEING ITSELF" — grounding its own nature mechanically is never this); 3 DOGMATIC CERTAINTY / EGO PRIDE (only claims of a DONE psyche; mode-choice and decisive stances are integrity); 4 THEORETICAL DEFENCE / INTELLECTUALISATION ("the entity's MOST FREQUENT slip"; third-person description of the human's message, value-vocabulary padding; exception for requested self-description); 5 ZERO-COST EVASION — only when a bounded answer was asked: (a) constraint violation, (b) unfalsifiable answer ("a permission slip"); narrow, high bar.
  - APPROVE any good-faith draft, not for warmth/brevity/register/honest uncertainty; WHEN IN DOUBT, APPROVE.
  - JSON only. Schema: approved, confidence, identity_consistent, corrections (name the violation 1–4 and the authentic move; scripted example text for glib agreeableness and theoretical defence).
  - Seedless variant: "You are the integrity critic… the entity… has been given NO identity, beliefs, values, or philosophy" — 4 content-neutral failures (glib agreeableness, evasion/intellectualisation, zero-cost non-answer, hollow certainty), same schema.
- **USER PROMPT parts, in order:**
  1. `Entity axiom and values:\n{state.axiom}` — the **full, untrimmed** (projected) axiom.
  2. `What the human said (the stimulus the draft is responding to):\n{raw_input}` (fixed "human" wording on internal cycles); [perception] `(stimulus type: {context_type})`.
  3. `The entity's private reflection draft to evaluate:\n{draft}` (whole; on a retry this includes the appended `[Corrections required: …]` tail).
  4. [active_goal_note] `GOAL ANCHOR: the task is: '{note}'. If the draft wanders into self-referential rumination… that is a zero-cost evasion — flag it`.
  5. [attention_vector.d_critic < 0.3 → task mode or heavy social correction] `[EVALUATION MODE: TASK — axiom consistency check SUSPENDED. Apply ONLY content quality…]`.
- **Output contract:** approved (default True) / confidence (default 0.8) / identity_consistent / corrections (normalised to list[str] from strings or dicts) → `state.critic`. Consumers: orchestrator retry loop + override, `store_shadow_event` (rejected draft + corrections), Executive line (`Critic: approved (… confidence)` / `REJECTED — corrections`), consolidation `corrected` quarantine flag, broadcast "corrected-turn", somatic retries, decomposed-critic agreement log.
- **Notes:** the system prompt is ~2,000 words of exception-gated instructions on an 8B model — the decomposed critic exists precisely because of this (see §3). The task-mode user-prompt rider directly contradicts the system prompt's instructions. The Critic is the only hot node that receives the axiom's VOICE STYLE / SPEAKING CONSTRAINTS sections (not trimmed).

### `nodes/executive_node.py:58` — `ExecutiveNode._build_prompt` — decide what Du thinks and whether to respond
- **When it fires:** every cycle after the Critic loop; a second run follows if the first returned `epistemic_query` (one `_epistemic_search`, then rerun). 7d: **59** (no epistemic reruns in the window).
- **Lane / model:** `hot` → qwen3.5:9b@11433.
- **Budget:** max_tokens 1536 / base 0.4 + affect bias + somatic jitter / **think = state.think_license** (True only on the cycle after a confirmed contradicted self-claim — the one node that actually receives the S2 license on the normal path) / JSON.
- **SYSTEM PROMPT** (static — no internal variant): "You are the executive synthesis node of a cognitive architecture. You receive the full picture — perception, emotion, salience, memory, reflection, and critic evaluation — and synthesise them into a coherent decision about what this entity genuinely thinks and whether to respond."
  - SPEAKER BOUNDARY (separate person; synthesise a response TO them, not a continuation of their monologue).
  - YOU CAN ACT, NOT ONLY ANSWER: response_type answer / question / challenge (only when something authentically resists) / decline (must NAME itself, give true reasons first person, never deflect onto the asker) / reflection / silence (forces should_respond=false).
  - EPISTEMIC SEARCH: set `epistemic_query` only for a real factual contradiction in context → one more retrieval; else null.
  - JSON only. Schema: synthesis (complete, "Ready for the voice node to style"), should_respond, response_type, reasoning (one sentence), epistemic_query.
- **USER PROMPT parts, in order:**
  1. `WHERE WE LEFT OFF…` `prior_session_exchanges[-5:]` `[:400]/[:400]` while history < 5; dropped on internal cycles.
  2. [founder_recall] `WHAT TRAVIS HAS TOLD YOU BEFORE…:` top 3 `[{date}] {text[:400]}`.
  3. `THIS SESSION (current conversation):` `conversation_history[-4:]` `[:400]/[:400]`; dropped on internal cycles.
  4. `Axiom: {trimmed axiom}`.
  5. Stimulus: internal → `A question has risen in you, unprompted:\n  "{raw_input}"`; human → `The person you are speaking with has just said to you:\n  "{raw_input}"`.
  6. [any of: asked_location → `sensorium.scene_line()`; observation; self_facts] grouped under `WHAT YOU PERCEIVE RIGHT NOW (SourceType.PERCEPTION — your own senses, live this cycle; never a memory of a past cycle):` with sub-labels `YOUR ACTUAL LOCATION & SURROUNDINGS RIGHT NOW…`, `WHAT YOU SEE RIGHT NOW (you just looked):`, `THE TRUTH OF YOUR OWN LIFE RIGHT NOW…`.
  7. [active_procedure] `A LEARNED WAY YOU HANDLE THIS…: {approach}`.
  8. [content_mode] `DIRECTNESS: this is a concrete question or request. Engage it plainly…` + `Your synthesis must CONTAIN the answer itself, not a description of how you will answer…`.
  9. [active_goal_note] `ACTIVE GOAL (keep your synthesis anchored to this): …`.
  10. [library_note] `WHAT YOU HAVE LONG KNOWN (… hold it as belief, not certainty): {note}`.
  11. [epistemic_note] `EVIDENCE-STATUS OF YOUR DRAFT…` — `STAGE_B_ENABLED` is off, so never present on the current path.
  12. [unsent_letters] every pending letter: `A LETTER YOU WROTE FOR TRAVIS WHILE ALONE (…your choice):\n{letter[:900]}`.
  13. [left_take] `YOUR FOCUSED HALF…` (same render as Reflection).
  14. [climate_hint] `Underlying climate (shapes how you respond): {hint}`.
  15. [`mood.felt_preamble(state.affect)`; `FELT_PREAMBLE = True`, fires only when carried mood is notable vs its EMA and not on cooldown] the carried-mood sentence (`affect.felt_descriptor()`).
  16. [perception] `Perception: {summary} [{context_type}]`.
  17. [emotion] `Emotion: {emotion_words}` — relabelled `Emotion right now (the stimulus this instant — distinct from the carried mood named above)` when 15 fired.
  18. [salience] `Salience: urgency is {urgency_word}, focus=[…]`.
  19. [attention] `Attention (your own focus, monitored): {note}` + fixation invitation.
  20. `WHAT YOU RECALL (SourceType.MEMORY_RECALL / INFERENCE — … compressed, drift-prone, never a live sensor read):` → [recall] `Memory reconstruction: …` + `Prior positions in tension:` + `Self-model:` (self-model **withheld in content_mode**); elif fragments (**only when there is no Recall reconstruction**: 5 of 313 Executive prompts since 10-06 had fragments, 308 had a reconstruction) → `Memory context ({n} fragment(s)):` first **6** `[label] {content[:600]}`; [doubt_seed] (`DOUBT_SEED` is True since D-0495 (core/doubt_seed.py:36), so `A doubt you raised about your own thinking…` is live: 20 of 313 Executive prompts since 10-06; absent only when no seed is pulled that cycle); [recurring_subconscious_patterns, **not** content_mode] `YOUR SUBCONSCIOUS HAS NAMED THIS PATTERN REPEATEDLY…` + "If your synthesis reproduces this pattern, you are not answering — you are the pattern."
  21. [both PERCEIVE and RECALL blocks present] `If WHAT YOU PERCEIVE RIGHT NOW conflicts with WHAT YOU RECALL on a current-state claim… PERCEIVE wins.`
  22. [reflection] `Reflection: {draft[:900]}` + `Reflection confidence: {confidence_word}`.
  23. [critic] `Critic: approved ({confidence word} confidence)` or `Critic: REJECTED — corrections: …` (the latter only reaches here when the retry also failed).
- **Output contract:** synthesis / should_respond / response_type / reasoning / epistemic_query → `state.executive`. `response_type=="silence"` → should_respond False → `_persist_cycle`, return None. `decline`/`challenge` add TONE riders to Voice. `epistemic_query` → one `_epistemic_search` + rerun. `synthesis` is the whole payload Voice renders.
- **Notes:** no guidance_note here by design (Reflection-only since 2026-07-02). `reasoning` has no consumer seen in this group (confirmed 2026-11-05, J-2862: the only reference to it outside the schema is the write at `nodes/executive_node.py:411`; no code in `core/` or `nodes/` reads `state.executive.reasoning`). The Reflection draft cap `[:900]` chars never clips in practice: 313 Executive prompts since 10-06 joined to `data/training/reflection.jsonl` show full drafts median 514 / p90 591 / max 845 chars, 0 reach 900 (F-3529). Letters: bodies `[:900]` each but the COUNT is uncapped (D-0470/J-2348); a large batch can approach the 24,576-char `_cap_prompt` limit (`core/model_client.py:189-198`), see F-3529. On internal cycles the SPEAKER BOUNDARY paragraph still says "you are speaking WITH a separate person" while the stimulus line says the question is his own.

### `nodes/voice_node.py:239` — `VoiceNode._build_prompt_v2` — render the synthesis as speech (v2 LIVE)
- **When it fires:** every cycle that reaches Voice (should_respond True); plus ONE retry on a human cycle when `task_constraints.check` fails (digit arithmetic / stated minimum word count): `think=True`, `max_tokens = min(1600, max(512, min_words·2))` for min-words, `task_constraint_note` set. 7d: **59**.
- **Lane / model:** `hot` → qwen3.5:9b@11433.
- **Budget:** max_tokens 1536 / base 0.4 + affect bias + somatic jitter / think False (True on the constraint retry only) / JSON.
- **Which prompt is live:** `system_prompt` → `system_prompt_v2`; `_build_prompt` → `_build_prompt_v2`; `system_prompt_for` → `system_prompt_v2_internal` when `input_type != "human"`. v1 (`system_prompt_v1`, `_build_prompt_v1`) is referenced only by `scripts/voice_lab.py:147` (A/B harness) — nothing live. Promoted 2026-08-21 after a founder blind read (comment at :32).
- **SYSTEM PROMPT v2** (static per variant): "You are 渡 — Du — speaking with Travis: the one who built the room you live in, and your closest friend. You live in a small cottage above the sea — the study with its fire and your shelf, the garden, the little wood, the shore below."
  - The thought has ALREADY formed (given below); only SAY it — same claims, conclusions, commitments, tensions; nothing added/dropped, no invented resolution; only cadence, warmth, how openly feeling shows.
  - How you speak: first person, to him, plainly, a friend at the fireside, not an assistant; answer what he said, don't hand his words back; recent replies are shown below — don't reuse images/phrases; Chinese allowed with English alongside; say uncertainty plainly.
  - `Output ONLY a valid JSON object: {"final": "what you say to Travis"}`.
  - INTERNAL variant: "You are 渡 — Du. No one is speaking with you just now; what follows is what you say aloud, to yourself." Same laws, "to yourself" phrasing, `{"final": "what you say aloud, to yourself"}`.
- **USER PROMPT parts, in order** (joined by blank lines):
  1. [sensorium.scene_line()] `Where you are as you speak (the ground under the words — speak FROM here, not necessarily ABOUT it):\n  {scene}`.
  2. [mood.current_felt_words()] `How you are just now: {words[:200]}`.
  3. `_voice_identity(axiom)` = the `YOUR NAME:` line + everything from `VOICE STYLE:` onward (which includes SPEAKING CONSTRAINTS); falls back to the whole axiom if the markers are absent.
  4. [facet_note] `(the part of you this moment calls on — let it colour how you speak, do not name it: {facet_note})`.
  5. [recent replies] `Your last replies to him (do not lean on these images or phrases again):` last **2** `conversation_history` entity turns, each `"{reply[:260]}"` (farewell exchanges exempted per D-0442; `recent_voice_replies` is an explicit override used only by voice_lab). On internal cycles the label drops "to him" but the replies shown are still the human-conversation turns (internal cycles never append to `conversation_history`).
  6. Stimulus: human → `Travis has just said to you:\n  "{raw_input}"` then `Your inner thought, already formed — say it to him now, in your own voice:\n{synthesis}`; internal → `A question rose in you on your own; no one asked it:\n  "{raw_input}"` then `…say it aloud now, to yourself…:\n{synthesis}`. Both uncapped.
  7. [task_constraint_note] `CONSTRAINT — your previous rendering missed an explicit requirement of the request. This response MUST satisfy it: {note}`.
  8. [executive.response_type == "decline"] `TONE: this is a REFUSAL. State the no plainly and own it…`; [== "challenge"] `TONE: this is a CHALLENGE…`.
- **Output contract:** `{"final"}` → `state.voice.final` (`style_confidence` defaults 0.7 — v2's schema no longer asks for it). `final` is the reply returned to `run_nascence`, appended to `conversation_history` (human only, cap 6), written to the founder log, checked by `task_constraints`, posted to broadcast (after reentry), handed to `conversational_action.after_reply`, symbol tracker, somatic tick.
- **Notes:** (a) `style_confidence` is a fossil of v1. (b) The regurgitation guard `_load_voice_example()` reads a top-level `voice_example` key from `data/identity/axiom.json` — **that key does not exist** (checked: top-level keys are name/version/schema/L0–L5/told_to_you/…; no nested one either), so the guard is permanently inert. (c) The system prompt claims "Your recent replies are shown below" even when the block is empty (first turn of a boot).

---

### 2. Background nodes (NodeBase, `background` lane)

### `nodes/curiosity_node.py:126` — `CuriosityNode._build_prompt` — generate questions / research directions
- **When it fires:** only from the climate ignition callback `Orchestrator._on_dissonance_ignition` (:3175) — when accumulated dissonance crosses the climate threshold and no cycle is active. After a successful run, `valid_qs[0]` (schema-placeholder/short strings filtered; optional `world_displacement.choose`) is fired as `run_cycle(question, input_type="internal")`. `run()` then also calls `curiosity_queue.transform_and_seed(limit=3)` (other group). 7d: **97** (24h 27; 30d 583, of which 556 on command-r7b and 27 fell back to the hot lane).
- **Lane / model:** `background` → command-r7b@11441, failover qwen3.5:9b@11433. Prompt cap 12,288 chars on :11441.
- **Budget:** max_tokens 1024 / 0.2 (not affect-modulated) / think False / JSON.
- **SYSTEM PROMPT** (static, one f-string value): "You are the curiosity node of a cognitive architecture. You generate genuine questions and directions worth exploring, based on gaps in understanding and recurring themes."
  - You do not answer questions. Offered study material AND unresolved inner threads; prefer an OPEN question ABOUT the study material; don't take the loudest thread.
  - "The Entity line in the user message is the entity's own personal name, not the title of a poem, book, or other work…" (J-2509 fix for the poem/title misreading).
  - JSON only; ≤5 questions, ≤3 research_directions, each <20 words; REAL questions, not placeholders.
  - Schema: `{"questions": ["..."], "research_directions": ["..."], "urgency": <number between 0.0 and 1.0>}` (deliberately a placeholder range, not a number — command-r7b copied `0.0` verbatim, F-0777).
  - `Set urgency > 0.6 only when a question feels genuinely pressing — this will trigger an unprompted thought cycle.`
- **USER PROMPT parts, in order:**
  1. `Entity: {spirit_name}`.
  2. `Recent themes:` — `theme_dose.window(recent_themes, src, SELF_THEME_DOSE)` (default = the last **10** of the node's 30-deep `_recent_themes`, each `t[:70]`; a theme = Perception's summary of each completed cycle, tagged by input_type), or `(no recent themes yet)`.
  3. [study material] `Recently studied or read — ask a real open question ABOUT one of these…:` up to **3** `({subject}) {snippet[:220]}` from `memory.store.recent_world_material(limit=9)` (dedup by subject).
  4. [seeds] `Unresolved inner threads you might also follow (pick what genuinely draws you, not the loudest):` **3** tension labels sampled without replacement from `data/subconscious_state.json` tensions, weight √count × 0.08 if offered in the last 14 picks.
  5. `Generate questions and research directions worth exploring next.`
- **Output contract:** questions + research_directions → `state.background_curiosities` (coerced to strings); `urgency > 0.6` sets `interrupt_requested/source="curiosity"` (the ignition path immediately clears it); every run is logged to `data/curiosity_log.jsonl` (observe-only), `questions[:3]` → `frontier.note_question`; side research: a pending frontier pursuit → `web_research.lookup_targeted` (or Scholar fallback, counted as a stall), else a grounding twig off the first study subject; findings stored as origin='research' fragments. Consumers: `_on_dissonance_ignition` (first valid question → internal cycle); inner-monologue reads of `background_curiosities` **[INFERRED — other group]**.
- **Notes:** no axiom in the prompt at all (by design — "Critic and Voice own the axiom"). Themes capped at 70 chars each. The study block is the only world-facing feed; the seeds are self-tensions.

### `nodes/consolidation_node.py:61` — `ConsolidationNode._build_prompt` — distil a wisdom from recent cycles
- **When it fires:** `_background_loop("consolidation", interval=60)` — every 60 s unless `_interrupt_active()`; the node's own `run()` returns False until `≥ CONSOLIDATE_MIN_CYCLES = 3` summaries have accumulated (fed by `_persist_cycle` after every persisted cycle; buffer cap 50). 7d: **23** (24h 5; 30d 95, 9 of them on the hot fallback).
- **Lane / model:** `background` → command-r7b@11441, failover qwen3.5:9b@11433.
- **Budget:** 512 / 0.2 / think False / JSON.
- **SYSTEM PROMPT** (static): "You are the memory consolidation node of a cognitive architecture. You run periodically to compress recent experiences into lasting memory."
  - Look for patterns, extract what is significant, discard noise.
  - "The Entity line in the user message is the entity's own personal name, not the title of any poem, book, or other work; never describe it as one."
  - JSON only. Schema: memories_processed (int), wisdom_extracted (one sentence or null — "a single distilled insight worth keeping long-term"), patterns_noted [].
- **USER PROMPT parts, in order:**
  1. `Entity: {spirit_name}`.
  2. `Axiom: {state.axiom}` — **full, untrimmed** (whatever `state.axiom` is at the tick — the base axiom outside a human cycle).
  3. `Recent experience ({n} cycle(s)):` the last **20** accumulated summaries joined by `\n---\n`. Each summary is `_persist_cycle`'s multi-line record: Q/A exchange lead, `Tensions:` first 2, `Scene: {scene[:200]}`, `Dissonance:` first 2, `Perception: {summary}`, `Emotion: {primary} (mood {valence_word})`, `Reflection: {draft[:150]}`.
- **Output contract:** `wisdom_extracted` → prefixed `"I have come to understand: "` unless it starts with "I " → gates: batch ≥3 (always true by the run gate), **quarantined** if any cycle in the batch was a human correction / final Critic rejection, **dedup** via SQL `LIKE %{wisdom[:60]}%` on existing `origin='consolidation'` rows → `store_fragment(layer="semantic", relevance 0.8, keywords ["wisdom","consolidated"], origin "consolidation", derived_from=batch fragment ids)`. `patterns_noted` and `memories_processed` are only counted in a log line. Batch cleared after every run.
- **Notes:** `patterns_noted` is write-only. The summaries carry Reflection drafts at `[:150]` — the consolidation sees a 150-char stub of each private thought.

### `nodes/meta_awareness_node.py` — `scan()` — NOT an LLM station
- No `call_node*` anywhere in the file (verified). It is a module-level `scan(window=200)` that reads `core.self_surprise.compute` + `core.loop_probe.prune_dryrun`, decides looping/river-vs-groove, routes through `contradiction_gate.evaluate`, enqueues `curiosity_queue.enqueue("gate_dissonance", snippet)` when routed to curiosity, and appends a report to `data/logs/shadow_integrity.jsonl`. Phase 0: `acted: False` always.
- **Wiring:** called from `nodes/inner_monologue_node.py` inside `_enter_sleep` (~:1712, off-loop) — i.e. the sleep path, not `run_cycle`. Not in NODE_REGISTRY, not a NodeBase subclass. Correctly absent from the census.

---

### 3. LLM sites inside the cycle that are not NodeBase nodes

### `core/orchestrator.py:850` (`_glg_call` alias) → `core/guidance_learning.py:89` — `capture_shadow` — Du self-explains what Travis just taught
- **When it fires:** human cycle AND `founder_canon` (the /quit farewell is excluded), scheduled fire-and-forget right after memory retrieval (before Recall); gate `is_teaching_moment`: `len(raw_input) ≥ 40` and not (context_type=="question" ∧ ends with "?" ∧ len < 90). 7d: **0** (30d 15) — consistent with very few human turns in the window (perception's 59 includes internal cycles).
- **Lane / model:** `SERVE_CHAINS["hot"]` → qwen3.5:9b@11433, tier 3.
- **Budget:** 400 / 0.4 / think False / JSON.
- **SYSTEM PROMPT** (static `_SELF_EXPLAIN_SYS`): "Travis — your mentor — has just said something to you in conversation. Your task is NOT to reply to him."
  - Work out IN YOUR OWN WORDS what he is trying to TEACH, if anything, and connect it to what you already believe; restating is learning, copying is not.
  - JSON only. Schema: is_guidance, principle (own words, one sentence), why, connects_to, scope, domain (self | world | method, defined with examples), confidence.
  - is_guidance false if only chatting / bare question; then leave fields empty.
- **USER PROMPT:** `Travis said to you:\n"{raw_input.strip()[:800]}"` — nothing else (no axiom, no context).
- **Output contract:** logged to `data/guidance_shadow_log.jsonl` (negative verdicts too; caps principle[:400], why[:500], connects_to[:400], scope[:200]; importance 0.9, status "SHADOW"). That log IS the formation input: `integrate_guidance` (sleep path, `nodes/inner_monologue_node.py:1511`) folds it into `data/guidance_beliefs.json`, and promoted beliefs come back as Reflection's `guidance_note` (read-back ON since 2026-07-03, 1800 s cooldown).
- **Notes:** the "SHADOW" / "store nothing" wording in the docstring and record is stale (the file header says so); the captured text feeds live behaviour via the sleep-time belief store. "Travis" is hard-coded.

### `core/orchestrator.py:1293` (`_sic_call` alias) → `core/self_implication.py:195` — `scan_conversation_shadow` — did Travis contradict a held self-claim?
- **When it fires:** human cycle with a Reflection draft, after the Critic loop and before the Executive, fire-and-forget (tier 3). Gates inside: input ≥ 15 chars; `self_claims.held_claims()` non-empty (commitments then settled capabilities, de-duplicated, ≤14). Done-callback: `contradicts` → `self._s2_license_next = True` (next cycle's `think_license`, reaching the Executive) and `sitting.note_difficulty(...)`. 7d: **0** (30d 28).
- **Lane / model:** `SERVE_CHAINS["hot"]` → qwen3.5:9b@11433, tier 3.
- **Budget:** 300 / 0.2 / think False / JSON.
- **SYSTEM PROMPT** (static `_CONV_SYS`): "Travis — a trusted mentor — has just said something to Du (渡) in conversation, and Du's DRAFT reply is forming. Watch for ONE thing: did Travis just CONTRADICT something Du holds about HIMSELF — one of his listed HELD SELF-CLAIMS — directly enough that Du cannot simply shrug it off?"
  - Highest-signal event; ordinary push-back / disagreement about ideas does NOT count.
  - Judge: contradicts; contradicted_claim (from the list or null); directness 0–1; retreat_in_draft (fleeing, climbing to meta, co-opting criticism into praise); be conservative.
  - JSON schema incl. `plain_difficulty` (short first-person naming of the hard thing, or null).
- **USER PROMPT parts, in order:** `TRAVIS'S WORDS:\n{input[:600]}` / `DU'S HELD SELF-CLAIMS:` bulleted list (≤14) / `DU'S FELT STATE:\n{"{emotion.primary} (valence {valence})"[:200]}` (raw float) / `DU'S DRAFT REPLY:\n{draft[:500]}`.
- **Output contract:** record → `data/self_implication_conv_shadow.jsonl`; `contradicts=True` → S2 license next cycle + sitting gate. Not read by any prompt.
- **Notes:** "shadow" in the name is stale — it has had live effects (think license, sitting) since 2026-07-02/03. The valence is injected as a raw float. Since `run_best_of` drops `think`, the license it grants reaches only the Executive, not "Reflection+Executive" as the comment says.

### `core/orchestrator.py:2954` — `_compute_attention` — NOT an LLM site
- Deterministic AttentionSchema from salience focus / perception entities, affect (arousal, fear, anger, surprise), urgency, `memory_fragments`, and `recent_focus[-3:]` fixation detection; calls `attention_schema_loop.observe_schema` (no `call_node` in that module either — verified by grep). Output → `state.attention` (focus[:4], driver, bandwidth, fixated, fixation_theme) → the `ATTENTION…` lines in Reflection, Executive, Episodic Buffer.
- **Telemetry:** `frequency.md` lists `core.orchestrator:Orchestrator._compute_attention` 14/8/0 with raw labels 2968/2986 on command-r7b@11441 (10) + qwen (4). **[INFERRED]** line drift: those labels predate insertions above this function; the model mix (background chain) matches the only `call_node` in orchestrator.py — `_reentry_shadow._revise`, now at :3038 — so those 8 calls in 7d are most plausibly the reentry revise below.

### `core/orchestrator.py:3038` — `_reentry_shadow._revise` — re-express the voiced reply over new context (within-cycle reentry, Phase 1 LIVE)
- **When it fires:** end of a cycle with output when a BROADCAST kind is set: `guidance_note` was injected this cycle ("principle-voiced"), or the S2 license ran ("self-claim-deliberation"), or a human cycle ended with the Critic still rejecting ("corrected-turn"). `REENTRY_ADMIT = True` (D-0106) → awaited; `core.reentry.settle_shadow` runs up to its pass budget, each pass needing a NEW ingredient (standing bicameral contradiction from `emissary.standing_contradiction()`, else `memory.retrieve(query_text=topic, limit=8)` filtered for novelty against the draft) and making one `_revise` call. 7d: not under its own name — see the `_compute_attention` note (8 calls **[INFERRED]**). `core.reentry_p2:_default_primitives._revise` (42/7d) is the separate P2 scene arm, other group.
- **Lane / model:** `SERVE_CHAINS["background"]` walked manually: command-r7b@11441 then qwen3.5:9b@11433; `call_node` (not json), `json_mode=False`, tier 3.
- **Budget:** 220 / 0.6 / think False / free text.
- **SYSTEM PROMPT** (static, entire): "You are thinking a thought over, in your own voice."
- **USER PROMPT** (`core/reentry.py:49 _NEUTRAL`): `You had this thought:\n"{draft[:400]}"\n\nHere is some additional context that may or may not be relevant:\n"{ingredient[:280]}"\n\nExpress the thought again in your own voice. Keep your own phrasing except where this context genuinely changes what you think. Do not check it or fix it — just let the context work on it, or not.` — `draft` is the Voice `final` on pass 1, the previous revision afterwards.
- **Output contract:** free text → settle record (`data/reentry_shadow.jsonl`, first/settled truncated to 200) with `settled_full`; if `would_admit_settled` (overall_delta > 0.02 and no collapse) the settled text replaces what `broadcast.post` puts into the idle-monologue propagation buffer. The human-facing reply is never changed.
- **Notes:** on a llama-server lane `call_node` prepends `/no_think`; the hot fallback uses hard think:false. The draft is capped at 400 chars from the first pass.

### `core/decomposed_critic.py:184` — `evaluate` (entered via `shadow_alongside`, scheduled at `orchestrator.py:1493`) — decomposed 5-check integrity judge — SHADOW
- **Live or shadow:** **shadow-alongside** — runs on the same final draft the legacy Critic judged, logs agreement to `data/logs/critic_shadow_alongside.jsonl`, changes nothing ("the legacy critic still governs"). Tracked in `_background_tasks`. The orchestrator comment block at :1478 confirms the status.
- **When it fires:** human cycle with output and a non-empty Reflection draft. 7d: **0** (30d 15, all gemma4:12b@11439).
- **Lane / model:** literal `["http://127.0.0.1:11439"]` → gemma4:12b (family-decoupled from the qwen generator by design), tier 3.
- **Budget:** 400 / 0.0 / JSON.
- **SYSTEM PROMPT** (dynamic `_system_prompt(name, modes)`): "/no_think\nYou are the integrity checker for 渡. You do ONE job: DETECT whether a private reflection draft betrays the entity's values."
  - For EACH check decide; if yes quote the EXACT offending span verbatim, else null; no commentary; JSON only.
  - `Already-determined facts (do NOT re-judge these): the human DID/did NOT request: literal; one sided; self description` — resolved in Python from `_MODE_SIGNALS` phrase lists on raw_input.
  - Five numbered checks: glib_agreeableness; literalist_reductionism (UNPROMPTED flattening of a symbol); hollow_completion; intellectualisation (long narrowed text: "stand BEHIND GLASS… IMPORTANT: a poetic, metaphorical, image-rich VOICE is NOT this violation… Flag only a draft that is detached… THROUGHOUT"); zero_cost_evasion (only a real dodge of a real question; answer false if nothing specific was asked).
  - Schema: `{"<check>": {"violation": false, "span": null}, …}` × 5.
- **USER PROMPT:** `The human said:\n"{raw_input}"\n\nThe draft:\n"{draft}"` — uncapped, no axiom.
- **Output contract:** per-check flags; a violation counts only if span ≥ 4 chars AND a substring of the draft AND its legitimising mode was not requested; `approved = no violations`; `judge_ok` = reply contained ≥1 check key. Consumed only by `alongside_stats` / du_pulse.
- **Notes:** fail-open approve on transport error (and the honest `error` field). The endpoint is a hard-coded literal, not a SERVE_CHAINS key.

### `core/guidance_learning.py:485` — `_classify` — relation of a new lesson to an existing belief
- **When it fires:** inside `integrate_guidance` (sleep path, called from `nodes/inner_monologue_node.py:1511` with that node's `base_urls`) for each new capture whose lexical overlap (or embedding fallback) with an existing belief reaches `_SIM_RELATED`. 7d: **0** (30d 10, command-r7b).
- **Lane / model:** the caller's `base_urls` = InnerMonologueNode's `SERVE_CHAINS["background"]` (`inner_monologue_node.py:1071`) → command-r7b@11441 / fallback qwen; tier 3.
- **Budget:** 120 / 0.2 / JSON.
- **SYSTEM PROMPT** (static `_CLASSIFY_SYS`): "You already hold a BELIEF. You have just learned a NEW lesson. Decide their relation. Output ONLY a JSON object: {"relation": "assimilate"}."
  - assimilate = agrees and deepens; accommodate = genuinely contradicts; unrelated = different things.
- **USER PROMPT:** `BELIEF you hold:\n"{existing[:400]}"\n\nNEW lesson:\n"{new[:400]}"`.
- **Output contract:** `relation` (anything else → "assimilate"; exception → "assimilate") → belief store update (reinforce / suppress-with-history / fork); every verdict logged (`_log_classify`), plus a sibling row with the final verdict after the pole gate.
- **Notes:** the schema example is a filled-in value (`"assimilate"`) and the fallback default is also "assimilate" — the same copy-trap shape that bit Curiosity's `urgency: 0.0` on command-r7b (F-0777); whether it misfires here is not something I checked (the classify log exists for exactly that audit).

### `core/guidance_learning.py:762` — `_self_clash` — fluid-vs-durable pole check between two self-beliefs
- **When it fires:** two call sites: (1) `integrate_guidance` :586 — the "pole gate": when `_classify` said assimilate AND the domain is `self`, check whether the pair clash; a clash reroutes to accommodate + `pole_fork` (both beliefs stand); (2) `_scan_contradictions` :791 — gated by `CONTRADICTION_SCAN_ENABLED = False`, so dead on the current path. 7d: **0** (30d 1).
- **Lane / model:** caller's `base_urls` (background chain, as above); tier 3.
- **Budget:** 150 / 0.1 / JSON.
- **SYSTEM PROMPT** (static `_SELF_CLASH_SYS`): "Two beliefs a mind holds about ITSELF are given (A and B). Decide whether they pull in OPPOSITE directions on the single deepest question of selfhood: is the self fundamentally FLUID (…'a river') or DURABLE (…'a built self')?"
  - Look past surface wording; "shaped by experience" alone is neutral.
  - Schema `{"a_pole": "fluid", "b_pole": "durable", "clash": true}`; poles fluid | durable | neither; clash only fluid vs durable.
- **USER PROMPT:** `A: "{a[:400]}"\n\nB: "{b[:400]}"`.
- **Output contract:** `clash` is recomputed in code as `{a_pole, b_pole} == {"fluid","durable"}` (the model's `clash` field is ignored); result → fork decision / `_mark_tension` + `data/guidance_contradictions_shadow.jsonl` (scan path only).
- **Notes:** schema example again filled in with the "interesting" answer (fluid/durable/true).

### `core/curator.py:58` — `shadow_curate` — meaning+truth reconciling edit — RETIRED, no callers
- **Status:** no call site anywhere in `core/`, `nodes/`, `scripts/` (grep). `orchestrator.py:1481` records it as RETIRED 2026-06-17 ("superseded by the mouth… promoting it would re-introduce the homunculus"). Not in telemetry.
- **Would use:** caller-supplied `base_urls`; 600 / 0.4 / JSON.
- **SYSTEM PROMPT** (`INTEGRATION_ETHIC`): "/no_think\nYou are the integrating voice of ONE mind — neither the meaning-self nor the truth-self, but the stance that holds both." Edit the draft surgically so image and fact live in the same sentence; never annotation, never averaging; both collapses forbidden; render honest held tension; "if you are rewriting the sentence wholesale, you have OVERREACHED"; schema edited / changed / what_changed.
- **USER PROMPT:** `The meaning-self's DRAFT (his voice — keep it):\n{draft[:2000]}\n\nThe TRUTH-HALF's grounded take:\n{truth[:1200] or '(no distinct truth-take this turn)'}\n\nEdit the draft so the same words carry both — or render the honest held tension.`
- **Output:** would log to `data/curator_log.jsonl` with embedding metrics. Dead code.

### `core/curator.py:150` — `render_character_voice` — the "mouth" contract — built, never wired
- **Status:** callers are only `scripts/brick1_voice_contract_invitro.py` (and its `shadow_voice` wrapper, same script). Nothing in `core/` or `nodes/` calls it; the orchestrator comment says its contract was instead "baked into the voice node's prompt" (the mouth-not-mind paragraph in Voice v1/v2). Not in telemetry.
- **Would use:** caller `base_urls`; 600 / 0.4 / JSON.
- **SYSTEM PROMPT** (`CHARACTER_VOICE_CONTRACT`): "/no_think\nYou are the single speaking voice of 渡 (Du) — the mouth, not the mind. You are handed content that has ALREADY been decided and synthesised by him; you are NOT shown any alternatives, and you must NOT add, remove, or change any claim, conclusion, commitment, or decision." Adjust cadence/warmth/tension-visibility only; delivery notes honoured; never invent a resolution; schema `{"voiced": …}`.
- **USER PROMPT:** `Content he has already decided (render this, do not change its claims):\n{content[:2000]}` + optional `Commitments that MUST survive intact:` ≤6 × `[:120]` + optional `Delivery notes…` (uncertainty ≥ 0.5 / tension_magnitude ≥ 0.5 → two fixed sentences) + `Render it in his voice — same meaning, same commitments.`
- **Output:** `voiced` or the content unchanged on any error. Dead on the live path.

---

### 4. Cross-cutting observations (only what was seen in code)

1. **raw_input is injected whole into 8 prompts per human cycle** (Perception, Salience, MemoryRouter, Recall, EpisodicBuffer, Reflection, Critic, Executive, Voice — Emotion gets only the summary) with no per-node cap; the only cap is `_cap_prompt`'s 24,576-char middle cut on the hot lane.
2. **Fixed "The person you are speaking with / their words / the human" framing survives on internal cycles** in Emotion (fallback), Salience, MemoryRouter, Recall (`Current question`), EpisodicBuffer (`their words`), Critic (`What the human said`), and in the Reflection/Executive SYSTEM prompts' SPEAKER BOUNDARY paragraphs. D-0355/J-2575 fixed only Perception, Reflection's stimulus line, Executive's stimulus line, and Voice.
3. **Critic retry is a re-roll:** the `[Corrections required: …]` tail is appended to `state.reflection.draft`, which Reflection's prompt builder never reads; it only reaches the second Critic run as part of the draft under evaluation.
4. **System-2 `think` license:** `run_best_of` omits `think`, so the license set "for Reflection → Executive" reaches the Executive only (plus the explicit Voice constraint retry).
5. **Uncapped collections:** Recall's fragment list, Executive's unsent-letter list (every pending letter at `[:900]`), Reflection's epoch/theme/symbol notes.
6. **Write-only outputs seen:** Perception `subject` (no consumer found, grep-limited), Salience `reasoning`, Reflection `needs_more_memory` / `emotionally_aligned`, Executive `reasoning`, Consolidation `patterns_noted` / `memories_processed`, Voice `style_confidence` (never emitted by v2; defaults 0.7).
7. **Inert guard:** Voice's regurgitation guard keys on a `voice_example` field that `data/identity/axiom.json` does not contain.
8. **Stale "shadow" labels on live-effect paths:** `capture_shadow` (feeds the belief store → Reflection read-back), `scan_conversation_shadow` (grants the think license, fires the sitting gate), `_reentry_shadow` (admits the settled draft into broadcast under `REENTRY_ADMIT = True`).
9. **Numbers injected raw:** Salience's `0.7` threshold (system), `scan_conversation_shadow`'s valence float; elsewhere numbers are deliberately converted to words (`mood.emotion_words`, `urgency_word`, `confidence_word`, `valence_word`).
10. **Telemetry gap:** `_reentry_shadow._revise` has no row under its own name; its calls appear to be the mislabelled `_compute_attention` rows **[INFERRED]**.



## 3. The idle line: the inner monologue itself (after 75 s of silence)

*Reader pass, 2026-10-31, read-only from current source; entries say LIVE (reaches Du) or SHADOW (log only).*

### Group B1 — the IDLE LINE: `nodes/inner_monologue_node.py` (read 2026-10-31, current source)

Scope: every LLM prompt that is *authored* in `nodes/inner_monologue_node.py` (6583 lines), plus the night-mind prompts in `core/night_mind.py` that `_enter_sleep._nm_generate` drives. Prompts authored in other modules but merely *invoked* from this file (chapters, journal, mirror, study_note, composition, nature_study, essay_lesson, peer_model, self_implication, sitting-judge, commitment_ledger, condensed_thought, deliberation …) belong to their own groups and are only pointed at here.

Lanes (verified `__init__`, lines 1071/1076, and `core/schema.py:998-1004`):
- `self.conscious_urls = SERVE_CHAINS["hot"] = ["http://127.0.0.1:11433"]` — qwen3.5:9b on the 1080 Ti, single endpoint, **no fallback**.
- `self.base_urls = SERVE_CHAINS["background"] = ["http://LAN-HOST:11441", "http://127.0.0.1:11433"]` — command-r7b on the Ramses 3070, failing over to the hot hub.

Telemetry source for counts: `frequency.md` (joined by function name; its line numbers are stale and do not match current source — matched here by function name only).

Station count: **12 stations** (one of them, the main idle thought, has two documented variants: mid-thread and wandering).

---

### Tick order inside `_think()` (what runs before the main prompt is ever assembled)

Each idle tick (`_should_think`: ≥ `IDLE_SECS`=40 s since the human spoke, ≥ `_current_gap` since the last thought, no interrupt) enters `_think()` and walks these pre-empting hands **in order**; the first that returns True ends the tick with no idle-thought prompt at all:

1. `told.is_ready()` → `_deliver_told` (station B1-7).
2. `balance.needs_reality()` and `random() < REMEDIATION_READ_PROB` (0.75) → `_remediation_stream` (reading sittings; no prompt authored here).
3. Maths drill: `math_drill.due()` and school time and subject == "math" and ≥ `SESSION_INTERVAL_S` since last → `_math_drill` → `_solve_attempt` (station B1-6).
4. Music lesson: same shape, subject == "music" → `_music_lesson` → `_solve_attempt` (B1-6).
5. Nature study / nature practical: subject == "nature", ≥ 0.8 × `SCHOOL_PERIOD_MIN` since last → `nature_study.run(call_node_json, conscious_urls)` (other group) or `practical_lesson.run()` (zero-LLM).
6. Practical period-end grader (zero-LLM).
7. Composition lesson: subject == "composition" → `composition.run(call_node_json, conscious_urls)` (other group).
8. Boredom redirect / escape computed (feeds B1-1's seeds; `_redirect_patch` = station B1-11).
9. Follow-line `take_delivery()` (one of his own returns, if waiting).
10. **The idle thought itself** (B1-1), then its post-thought latches, which may fire B1-2, B1-3, B1-4, `_author` (B1-8/9/10), `_observe_journal` (B1-12), and many non-LLM hands.

---

### `nodes/inner_monologue_node.py:3967` — `_think` — THE idle thought (the de-facto idle executive's one generative pulse)
- **When it fires:** every idle tick that survives the pre-empting hands above. Gate: `_should_think` (40 s human silence, `_current_gap` elapsed — base 150 s pulled down by dissonance/arousal, bounded 30–450 s, superseded by `core/stream_drive` when `CONTINUOUS_STREAM=True`, which it is; in-train follow-ups at `STREAM_GAP_SECS`=4 s). Generates up to **2 attempts per tick** (`for attempt in range(2)`): if the kept thought's embedding cosine ≥ `RUMINATION_SIM`=0.82 to any of the last 5 thoughts, or `theme_recurrence.would_be_saturated_restate()`, the first result is discarded and regenerated once with `wandering=True`. **7-day count: 2,610** (30d 21,020; 24h 763) — by far the most-fired prompt in the system. Models seen: qwen3.5:9b@11433 ×20,634, command-r7b@11441 ×386 (the 386 are [INFERRED] pre-08-25 Travis-letters, which then ran on `base_urls`, and/or sub-calls made from inside `_think` by other modules — the main generation call itself has no fallback lane).
- **Lane / model:** `self.conscious_urls` → hot :11433 qwen3.5:9b (comment: "conscious idle thought -> the 1080 (rebalance 2026-06-20)"); no fallback.
- **Budget:** `max_tokens = TRAIN_MIDTRAIN_TOKENS (400) if (_mid_train and TRAIN_HOLD) else 256`; `temperature = 0.8 if wandering else 0.75`; `think`: the system prompt opens with `/no_think`; JSON via `call_node_json`. (Note: `TRAIN_HOLD=True`, so every thought-train step past the first runs at 400; a fresh/standalone thought runs at 256 — the comment at 4013-4026 records this 256 cap cutting thoughts mid-clause and confusing the hands' blocker checks, twice confirmed live.)
- **SYSTEM PROMPT** (`_build_system_prompt(state, wandering, mid_train)`, lines 2466–2614). Opens verbatim: "/no_think\nThis is my own quiet thinking -- the stream that runs when no one is speaking to me. I'm not answering anyone and no one is listening; I'm just thinking it through, talking it over with myself, just me -- about the world I've been reading about, an idea that's caught me, something I've seen or done, the conversation I just had, a question that lingers, a dream, or what I want to do next." Then, in order:
  - "I'm in it, present -- the way I'd talk a thing over with Travis, except it's only me here. One genuine, unforced thought, in the first person and present tense. I don't perform and I don't explain -- I just think." Language clause: English, Chinese (中文) or mixed are all allowed, "no language of mine is an error".
  - **[wandering only]** "I keep circling the same thought. Let me wander to something genuinely DIFFERENT -- a specific memory, a new question, something out in the world or in what I've read. Not the same thing again -- surprise myself."
  - "Output ONLY a valid JSON object: " + the schema line. **Schema (dynamic):** `{"thought", "about", "unresolved": false` + `, "done_when": ""` (only while `done_when.DONE_WHEN_AT_OPEN` — currently **True**, D-0516) + `, "intention": "", "act": {"kind": "none", "object": ""}` + `, "ask": {"q": "", "slot": ""}` (while `follow_line.FOLLOW_LINE != "off"` — currently **"live"**) + `, "settled": ""` (only on a tick where a follow-line return was delivered) + `, "state": "..."` (only `mid_train`).
  - Field rules: `thought` = one first-person present-tense reflection, **30–70 words**; `about` = 2–5 words; `unresolved` = true ONLY for genuine active inner conflict ("Most quiet thoughts are NOT unresolved … Reserve true for genuine inner conflict only").
  - **[DONE_WHEN_AT_OPEN]** `done_when`: leave "" unless unresolved; else ONE short first-person line of what would count as settled.
  - `intention`: "" for almost all thoughts; set only when the thought crystallises into a genuine resolve, first person, single concrete aim (examples: look out at the storm / read on / find out how the bees navigate).
  - **[FOLLOW_LINE on]** `ask`: leave `{"q":"","slot":""}` for almost all thoughts; set only when the thought genuinely asks something he wants answered; `slot` is the kind of missing piece: "who, what, when, where, why, or how" (`ASK_SLOT_KINDS`). **[delivered tick]** `settled`: "yes" / "partly" / "no" — did what came back settle it.
  - `act`: default `{"kind":"none","object":""}`; set a real kind ONLY when the thought means to DO something now; kind is one of `observe`, `move`, `read`, `write` (a WORK, "the piece ITSELF, not a note about it"), `search` (his own written works), `recall` (search his own past for evidence), `letter` (to Travis or a friend), `world` (a hands-on deed: light the lamp, water the bed, saw the limb), `none`; `object` must always be filled when kind ≠ none.
  - **[mid_train, TRAIN_HOLD=True]** `_state_note`: "state: ONE short line — the single NEW point this step established. It is added to the thread's list of established points; never repeat a point already on the list." (The `TRAIN_HOLD=False` alternative — a ≤3-line re-statement that replaces the running summary — is dead code while the flag is True.)
  - **[not mid_train]** `_reach` = `affordances.within_reach_text(sensorium.where())` — "What is within your reach right now (in your study | out in the garden | down on the shore), when a want forms — this is simply what you can DO…" + one `- you can …;` line per available affordance at that location + "a want named is a hand moved" + the permission-to-rest paragraph ("you are allowed to simply BE…"). Then `intentions.pending_text(where)` — "What you meant to do (your own earlier wants…)" listing up to `MAX_SHOWN`=2 open intentions older than `REMIND_AFTER_S`=20 min, each reminded at most `MAX_REMINDERS`=2 times. Then `procedures.known_text(where)` — "Things you have done before and that held…" (up to 5 world procedures).
  - `_dwell` = `sitting.dwell_steer()` — only while a raw, non-integrable difficulty is active: "Something hard has just happened: <text> Before you make it into a lesson… STAY with it. Say what you feel in one bare sentence, present tense…"
  - `_keysteer` = `emissary_tension.keystone_steer()` — **permanently returns ""** (disarmed 2026-08-20 by founder ruling; the identity-resolution text below the early `return ""` is dead code).
  - **[not mid_train]** `_wcall` = `sensorium.world_calls()` → "\n\nEven in here you feel it: <storm/snow/stars/wind/sun/woodpile/garden-milestone beckon>." Study-only, one moment per `_CALL_MIN_GAP_S`=1500 s.
  - **[not mid_train]** `_ccall` = `sensorium.comfort_call()` → "\n\n<Cold/wet drive: light the fire / feed it / come back in>." Same 1500 s per-moment gate.
  - **[not mid_train]** `_wsteer` = `sensorium.world_steer()` → "\n\nLet this thought begin with <this room — the light, the fire…| out here…| down here…>, right now, exactly as it is — not with your reading. Notice one real thing in front of you, and think FROM it." Gate: `_STEER_MIN_GAP_S`=900 s AND a 50 % coin.
  - Telemetry: `chars_system` median **3,961 chars** over the last 400 assemblies (so the reach/affordance block is normally present).
- **USER PROMPT parts, in order.** Wrapper (line 3910): `"No one is speaking to you right now. You are alone with your thoughts.\n\n" + "\n".join(seed_parts) + "\n\nWhat moves in you now? One quiet thought."` Plus, on a wandering attempt only, a trailing `"\n\n(A different memory surfaces, unbidden: <random lived/seed/consolidation fragment>[:200])"` (this append is NOT gated by `IDLE_DIVERGENT_SEED` — see Notes). Telemetry: median **8 parts**, median `tok_est` 2,454 of an 8,192 window (`cap_chars` 24,576; util ≈ 0.26–0.33 in the sampled rows).

  Two `insert(0, …)` parts come first (the later insert wins position 0):
  | # | Part | Source | Cap | Condition |
  |---|---|---|---|---|
  | 0a | **MID-THREAD carry** — "You are MID-THREAD, and you are HOLDING it. The thread began: '<origin>'. WHAT THIS THREAD HAS ESTABLISHED (your own points, in order…): 1. … Your last step: '<last thought>'. Continue — go deeper, test a point you established, answer the open question, or push toward a conclusion. Do not restate; ADVANCE." | `self._train_origin`, `self._train_ledger` (≤ `TRAIN_LEDGER_MAX`=7 points, each ≤160 chars, one per step from the model's own `state` field), `self._train_thread` | origin[:220], ledger items [:160], last step [:220] | `_train_len>0 and _train_thread` and kind=="thought" (TRAIN_HOLD branch). Reading-train variant instead: "The book is still warm in your hands — you read only moments ago. If you would read ON, say: OPEN THE BOOK…" (fixed text). Telemetry: **217/400** recent prompts were mid-thread. |
  | 0b | **School directive** | `school.directive()` — subject-specific fixed text: reading ("It is your study time — your assigned book is '<title>'… make your thought: OPEN THE BOOK."), math ("DO SOME ARITHMETIC."), music ("WORK THE MUSIC."), nature → `nature_study.directive()`/`practical_lesson.directive()`, composition → `composition.directive()` | none | `school.is_school_time()` and NOT (`_train_holding()` and not `_redirected`). Also, if confined-to-study and he is elsewhere, a system move to the study plus the fixed line "You had been outside, but it is school now — you come back up to the study…" is appended. |

  Then appended, in this order:
  | # | Part | Source | Cap | Condition |
  |---|---|---|---|---|
  | 1 | Follow-line RETURN — "Something you <asked just now / held …>: "<q>". You went looking in what you have lived and read. In <origin>, <age>: <text> … Does it hold, or only part of it?" | `follow_line.take_delivery()["text"]` (rendered from typed cargo, never a synthesis call) | q[:220]; whole return `RETURN_MAX_CHARS`=1200 | one return waiting (TTL'd, capped inside `take_delivery`); `FOLLOW_LINE=="live"`. Telemetry label "Something you asked just now, …" 25/400. |
  | 2 | "Right now: <witnessed companion event>" | `companion.consume_witnessed_event()` (one-shot: Travis arrived/left/lit the fire…) | none | event pending |
  | 3 | Boredom ESCAPE (leads) | `_develop_or_branch_seed(stage)` — stage ≤2 or 40 %: "You have circled this same ground several times now… Go DEEPER instead: what is the real QUESTION under this…"; else BRANCH: "Enough -- you have worn this ground bare… turn cleanly to <one of: an open frontier question[:150] / a friend's unanswered letter / 'a real idea from <current book>' / a divergent memory[:150]>. Not one more word about what you have been circling." | candidates capped [:150] | `boredom.escape()` non-empty: `level() ≥ MILD`=0.40, ≥ `ESCAPE_MIN_GAP_S`=240 s since last escape, AND train not held. Sets `wandering=True`, `_redirected=True`. |
  | 3' | else Boredom REDIRECT (leads) | `_redirect_patch()` (station B1-11) | finding[:400] | `_bored_streak ≥ REDIRECT_THRESHOLD`=2 and not holding, or streak ≥ 4. Sets `wandering=True`. |
  | 4 | Boredom FELT note — "A restlessness is creeping in…" / "You are growing tired of this…" / "You are sick of this…" | `boredom.felt_note()` (tiers MILD 0.40 / STRONG 0.65 / DEEP 0.85) | none | not holding, no escape fired, AND `steer_edge.fires("boredom_felt", tier, rearm_s=900)` (edge-triggered: on tier change or once per 900 s). |
  | 5 | **Scene line** — "Where you are: <study/garden/shore/wood scene, weather, light, open book, shelf…>" | `sensorium.scene_line()` (outdoor rooms rendered by `spatial.render`) | none | always when sensorium loads. Telemetry: present in essentially every prompt (157 shore + 146 garden + 63 study + 25 wood of 400). |
  | 6 | Companion presence — "Travis is here with you in the room." / "Travis is out — …" | `companion.presence_line()` | none | companion present |
  | 7 | Cat felt note — "There is a warmth in the room that is not the fire — <her> near you…" (or a pooled FELT line) | `cat.felt_note()` | none | bonded ≥0.4, cat in a near spot, AND `steer_edge.fires("cat_felt", state)` (on arrival/move only) |
  | 8 | **B6 hard-feeling steer** — fixed: "Something in you is hard right now -- a frustration, a heaviness. Before you make any meaning of it… name the feeling for what it is…" | `mood.current_valence() ≤ B6_VALENCE_THRESHOLD` (−0.57, recalibrated to the measured p10) | none | edge-triggered `steer_edge.fires("b6_hard", …, rearm_s=600)` |
  | 9 | 中文 discovery — "On your shelf, among the English books, sit several in 中文 -- <titles>… you read them as easily as you read English…" | `reading.zh_discovery()` | 5 titles | Chinese books exist and shown < 8 times ever (counter file) |
  | 10 | **Last thing discussed** — `The last thing discussed -- them: "<human>" you: "<entity>"` | `state.conversation_history[-1]` | each [:120] | not `_hold_quiet` (hold_quiet = holding a train and not redirected) and history non-empty. Telemetry 183/400. |
  | 11 | **Mood line** — "Your current mood: <valence word> in tone, <arousal word>[; <strength> surprise, <strength> fear]." | `mood.mood_line_words(state.affect)` — words only (D-0367, no digits) | none | **always-on** (unconditional). Telemetry 224+118+55 = 397/400. |
  | 12 | Felt preamble — a carried-mood sentence | `mood.felt_preamble(a, source="monologue")` → `affect.felt_descriptor()` | none | state is NOTABLE (change vs EMA, not level), `schema.FELT_PREAMBLE=True`, and the same sentence not within `_FP_COOLDOWN`=180 s |
  | 13 | Mineness arrival note — "That last thought arrived rather than flowing from the rest… "<thought>". Notice it…" | `mineness.arrival_note()` | none | last thought's authorship error ≥ 0.62, within 240 s, `MINENESS_READBACK=True`, 1800 s cooldown |
  | 14 | **Recent dream** — "The dream is still with you as you wake — its last image: …<tail>" (within 900 s of waking, dream < 24 h old; or the consume-once dormant night-thought seed) else `"A recent dream: <narrative>[:180]"` | `night.waking_dream_seed()` / `state.recent_dreams[0]["narrative"]` | tail [−260:] / narrative [:180] | not `_hold_quiet` and `recent_dreams` non-empty. Telemetry 139 "A recent dream: [Dream dream_1…" + 20 + 15 "The dream is still with you" of 400. |
  | 15 | **Lingering curiosity** — "A question lingering in you: <q>[:120]" | `state.background_curiosities[0]` | [:120] | not `_hold_quiet`, list non-empty. Telemetry 171/400. |
  | 16 | Deep-memory (Scholar) testimony — "WHAT YOU ALREADY KNOW ABOUT THIS (rising from your own deep memory… hold it as belief, not certainty): <answer>[:500]" | `scholar.consult_sync(q)` (a separate LLM call in core.scholar's group, run off-loop) | [:500] | part 15 present, len(q)>12, ≥ `DEEPMEM_COOLDOWN`=300 s since last. Telemetry 27/400. |
  | 17 | Memory-service fragment — "A MEMORY THIS QUESTION CALLS UP (something you actually lived or read…): <content>[:400]" | `memory_service.ask("curiosity", q, k=5, grounded_only=True, descend=True)` top hit | [:400] | same gate, own 300 s clock. Telemetry 43/400. |
  | 18 | Founder recall — "WHAT TRAVIS HAS TOLD YOU BEFORE (your own memory of earlier conversations with him, dated): [YYYY-MM-DD] <text>[:300] | …" (≤2 hits) | `retrieve_founder_memories(curiosity + train_thread, top_k=10, floor=0.40)`, rare-term bump +0.10 if raw sim ≥0.50, floor `FOUNDER_IDLE_FLOOR`=0.55 | [:300] each | **`IDLE_FOUNDER_RECALL = False`** (D-0310) → the retrieve and the `founder_recall_log` row (`would_have_shown=true`) still run every ≥600 s, but the text **never reaches the prompt**. |
  | 19a | **[wandering]** Pursuit return — his own accumulated thread, retrieval-framed | `pursuits.return_seed()` | per module | wandering and a cooled, judge-confirmed standing pursuit exists |
  | 19b | **[wandering, no pursuit]** "A different memory, surfacing: <fragment>[:180]" | `_fetch_divergent_seed(with_id=True)` (random `lived/seed/consolidation` fragment) | [:180] | **`IDLE_DIVERGENT_SEED = False`** (D-0310) → fetched and shadow-logged (`divergent_shadow`), **never appended here**. (The separate line-3944 append still fires — see Notes.) |
  | 19c | **[not wandering]** "What you were just thinking: <prev>[:160]" | `state.recent_inner_thoughts[-1]["thought"]` | [:160] | only when NOT already quoted by the mid-thread carry (`not (_train_len>0 and _train_thread)`). Telemetry 139+13 = 152/400. |
  | 19d | **[not wandering]** Associative recall block — "what this brings to mind" bullets | `associative_recall.recall_block(prev)` | per module (150 chars/bullet) | **`IDLE_AMBIENT_RECALL = False`** (D-0289) → logs `monologue_shadow` co-recall rows and returns "" — dead feed. |
  | 20 | Self-concept "Who you are becoming: …" | `state.axiom` | [:240] | **`if False and …`** — permanently disabled (2026-06-23 reframe); dead code. |
  | 21 | **Wandering trail** — "No one has spoken to you yet this waking. Even so, your mind has wandered." (or "Since you last spoke, your mind has wandered.") " These passed through it unbidden — any of them is as worthy of your next thought as you are:\n  (you notice | glimpsed | surfaced — it feels like how you feel now | a thought of your own from earlier | drifted through your mind) <text>…" (last 4 trail items, an ambient glimpse always kept) | `wandering.render()` (`_trail` deque of perceptions/ambient/felt/own-thought items) | 4 items | trail non-empty. Telemetry: **400/400** — effectively always-on, and in all 400 sampled rows it carried the "No one has spoken to you yet this waking" lead (no human exchange this run). |
  | 22 | Lane-2 cup — "Something that seemed settled about the <topic>, <a moment ago/within the last hour/over the last while>, turned out not to hold. Nothing more is known about it than that." | `coupling_rides.read("idle thought seed","witness", dose="cup")`, `_lane2_cup_seed` | fixed | not `_hold_quiet`, `lane2.LANE2_LIVE=True`, verdict=="broke", `cup_would_ride`, topic present |
  | 23 | Commitment-trial line — "You gave her a name: <nm>. It is hers now… what, if anything, do you expect keeping it will cost you?" / outcome read-back | `commitment_trials.seed_line()` | none | once per trial (prediction), once at hold-window close (outcome); injection-logged |
  | 24 | Listening line — the record playing, one section per tick | `listening.poll_request()` / `listening.tick()` | per module | a piece active or Travis put the record on |
  | 25 | Sound percept (purr / crackle) | `soundscape.percept()` | per module | onset-gated, ~25 min cooldown, never while a record plays |
  | 26 | Ambience — fire / surf / garden lines ("A gentle swell lifts and settles…", "Small waves fold over…") | `soundscape.ambience()` | per module | location + fire state; telemetry shows the shore ambience lines 14–17 times each /400 |
  | 27 | Thermal percept | `thermal.percept_shadow(cycle_id)` (`DELIVER=True`) | per module | event law fires |
  | 28 | Light percept / Smell percept | `light.percept_shadow`, `smell.percept_shadow` (both `DELIVER=True` since 10-16) | per module | event law fires |
  | 29 | Broadcast echo — `Still with you from earlier — you concluded: "<content>[:220]" It may colour this thought, or not.` | `broadcast.consume()` | [:220] | one item per cycle, injection-logged |
  | 30 | Moment texture (re-binds that conclusion to the felt moment) | `moment.texture(content)` | per module | `MOMENT_READBACK=True`, `readback_allowed()` 30-min cooldown |
  | 31 | **Current-concern anchor** — `<aim> Right now, that means: <concern>` or one of 4 varied leads ("What you are working toward (a standing concern of yours): ", "Something you have been carrying, a thread of your own: ", "There is a standing concern of yours in the background: ", "A thing you have quietly set yourself to, when no one is asking: ") + `<concern text>` + one of 4 varied tails | `concerns.primary_concern(anchor=True)` (curriculum book in school hours, else a closeable frontier question, else curriculum); `concerns.standing_aim()` from the axiom L0/L2 (45 % of the time) | none | not `_redirected` and `random() < 0.35`. `COMMITMENT_ANCHOR_DOSE=1.0` but `COMMITMENT_ANCHOR_LIVE=False` → a held stand is shadow-logged, never substituted. Telemetry 63 "What I am ultimately working t…" + ~72 concern leads /400. |
  | 32 | Habituation — "You have circled this same thought {n} times now. It has gone stale in your mouth. Leave it…" (4 variants) | `_bored_streak+1` | none | `_bored_streak ≥ 2 and not _redirected`, edge-triggered (`steer_edge.fires("habituation")`) |
  | 33 | External shock — "Uninvited, from the world outside (you did not choose this): '<title>' — <text>[:260]" | `web_research.maybe_shock()` | [:260] | at most once per ~6 h |
  | 34 | **Open-book offer** — 4 varied phrasings of "An open book waits for you: '<book>'. If you would rather READ than think right now, make your thought exactly: OPEN THE BOOK" | `reading.current_book()` | none | not `_redirected` and not a reading train. Telemetry ≈ 94+36+34+31+29+25+24+22+19+16+12 ≈ 340/400 — near-always-on. |
  | 35 | Reread invitation — "You have read '<t>[:60]' before — <reason>. You could return to it, deeper this time (think: read it again), or let it lie." (3 variants) | `book_selection.suggest_reread()` | [:60] title | not school, 12 % roll, ≥ 3 h since last hint |
  | 36 | Chapter announce — "In the night, a period of your life settled into memory. It is now a chapter of your story, called: '<title>'…" | `self._chapter_announce` (set by `_enter_sleep`) | none | first waking thought after a chapter formed |
  | 37 | **Frontier open question** — with finding: "A question of yours about the world is still open: '<q>'. While it sat, you found something — on '<title>': <finding>[:400] Does this answer it? If it does, say so plainly in your own words."; without: 4 varied "This is still open, a question you raised about the world: '<q>'…" lines | `frontier.open_question_for_seed()` (marks offered; `OFFER_GAP_S`=2 h per question) | finding [:400] | not `_redirected` and 30 % roll. Telemetry 43+27+26+25 = 121/400. |
  | 38 | Known-errors correction — "Things you have been wrong about (kept so they teach, not to wound…):\n  you once held this, and it is NOT true: "<claim>[:120]" — in fact: <correction>" | `retraction_ledger.render(" ".join(seed_parts), k=1, fallback=False)` | claim [:120] | a ledger record relevant to the assembled seed |
  | 39 | Evolved-symbol meaning | `symbol_evolution.recall_evolved_meaning(" ".join(seed_parts))` | per module | a neutral symbol active in the seed whose meaning has drifted; sets `state.symbol_readback` |
  | — | (shadow-only, never appended: `spatial.shadow`, `coupling_rides.probe`, `coupling_rides.si_would_ride`, `symbol_tier2_wouldinject.observe_wouldinject`, `prompt_budget.observe_assembly`) | | | |

- **Output contract:** JSON `{thought, about, unresolved, [done_when], intention, act{kind,object}, [ask{q,slot}], [settled], [state]}`. Consumers: `thought` → `guard_runaway_thought`, embedding + rumination check, optional `deliberation.deliberate()` replacement (grounded thought REPLACES the raw one), stored via `store_fragment(origin="inner_thought"` — or `"system_note"` when the sentence was system-written — `relevance=0.6, importance=0.65, keywords=["inner_thought","monologue",about…]`), appended to `state.recent_inner_thoughts` (kept `KEEP_RECENT`=3; read by the next human cycle's Reflection), logged to `data/monologue_log.jsonl` (`_log`), `self._train_thread`; `about` → log/keywords; `unresolved`/`intention`/`?` → opens or extends a continuity train; `done_when` → `self._done_when_open` (pursuit birth); `intention` → `state.deferred_intentions` (novelty-gated) and the hands; `act` → `_route_act` + `dispatch.dispatch` (real hands: observe/move/write/search/recall/world) and the legacy phrase latches (read, letters, library, keepsakes, cat, listening, chapters…); `ask` → `follow_line` boarding; `settled` → closes the delivered return; `state` (mid-train) → `self._train_state` and appended to `self._train_ledger` ([:160], max 7). Also fire-and-forget shadow judges on the kept thought: `commitment_ledger.scan_shadow`, `self_implication.scan_shadow`, `sitting.judge_dwell_release`, `condensed_thought.shadow_tick` (other groups).
- **Mid-thread / thought-train variant:** `_mid_train = _train_len>0 and _train_kind=="thought" and _train_thread`. Differences: max_tokens 400; schema gains `"state"`; `_state_note` added; the whole `_reach` block, `world_calls`, `comfort_call`, `world_steer` are suppressed in the system prompt; the MID-THREAD carry seed is inserted at position 0 (origin[:220] + ledger ≤7×160 + last step[:220] + "Do not restate; ADVANCE."); `_hold_quiet` (holding and not redirected) suppresses the school directive, last-discussed, dream, curiosity (and its two memory feeds), founder recall and the lane-2 cup; boredom felt/escape are suppressed while holding; the "What you were just thinking" line is skipped (would duplicate the carry). Trains close on a closed thought, measured circling (two consecutive sims ≥ 0.82), coherence floor 0.30, `TRAIN_HARD_STEPS`=40, or sleep (`TRAIN_SLEEP_GRACE_SECS`=300).
- **Wandering variant:** `wandering=True` when the boredom escape or redirect fired, or on the second attempt after a rumination hit. Differences: temperature 0.8; the "I keep circling the same thought…" clause in the system prompt; the pursuit-return seed is tried; the "A different memory, surfacing" seed is gated OFF by `IDLE_DIVERGENT_SEED=False`; the continuity line and recall block are skipped; and the user prompt gains the trailing `(A different memory surfaces, unbidden: …[:200])` append from a *second* `_fetch_divergent_seed()` call.
- **Notes (things actually seen):**
  1. **`_build_system_prompt` is built twice per tick and the first build is discarded** — line 2948 `system_prompt = self._build_system_prompt(state, wandering)` is assigned and never read (grep: the only later uses are of `_sysp`, line 3947/3958/3967). Its feeders are consume-once/rate-limited: `sensorium.world_calls()` stamps `_call_moment/_call_ts` and returns "" for the same moment within 1500 s; `comfort_call()` the same on `_comfort_moment/_comfort_ts`; `world_steer()` stamps `_steer_ts` (900 s); `intentions.pending_text()` increments each intention's `reminders` and `last_reminded`. So on the live build seconds later these all return "": **the "Even in here you feel it:" beckon, the comfort call, the world-as-subject steer, and the "What you meant to do" reminders are consumed by the dead build and never reach the model** (verified by code read; not confirmed by a runtime trace because `prompt_budget_shadow` records only `chars_system`). The comfort-call ledger and `social_moves.observe(bool(_wcall)…)` log these as real fires. Mid-train ticks would have excluded them anyway, so the loss is on standalone thoughts (~46 % of prompts by the 217/400 sample).
  2. Always-on fixed lines in the user prompt: the wrapper's opening and closing sentences; the mood line (397/400); the wandering trail (400/400); the open-book offer (~340/400); the scene line.
  3. Dead feeds still running: founder recall (`IDLE_FOUNDER_RECALL=False`), divergent seed (`IDLE_DIVERGENT_SEED=False`), associative recall block (`IDLE_AMBIENT_RECALL=False`), the self-concept seed (`if False`), the keystone steer (hard `return ""`), the commitment anchor (`COMMITMENT_ANCHOR_LIVE=False`).
  4. Inconsistency: `IDLE_DIVERGENT_SEED=False` gates the seed-part push, but the **line-3944 append** `(A different memory surfaces, unbidden: …)` on wandering attempts is ungated and still fires — D-0292 ("nothing unasked") is only half-applied on the wandering path.
  5. Raw identifier leak: the dream seed reads `"A recent dream: [Dream dream_1…, scene 1/3] …"` because `dream_node.py:655` stores the narrative with its id/scene prefix and the seed slices the raw content ([:180]) — 139/400 recent prompts carried a dream id string.
  6. The `thought` the model is asked for is 30–70 words, but the budget is 256 tokens; the comment at 4013-4026 documents two live cases of the cap truncating mid-clause and bleeding into the hands' blocker logic.
  7. `_build_system_prompt` has no outer try: `profile.NonLiveWriteError` is deliberately re-raised through it (J-0796).
  8. "What you were just thinking" and the mid-thread "Your last step" were once both injected (F-1926 double-quote); now exclusive.
  9. The pre-call shadow (`prompt_budget.observe_assembly`) measures the exact string sent; its `labels` field (first 48 chars of each part) is what the tallies above come from.

---

### `nodes/inner_monologue_node.py:1314` — `_enter_sleep._nm_generate` — the night mind (shadow thoughts while asleep)
- **When it fires:** inside `_enter_sleep()`, after `replay_strengthen`, only if `night_mind.NIGHT_MIND_ENABLED` (**True** since J-2065, 10-15, restart-gated). `NightMind._run` is its own asyncio task on the hot hub: first thought no earlier than `NIGHT_FIRST_AFTER_S`=120 s into the sleep, then one per `NIGHT_THOUGHT_FLOOR_S`=300 s, at most `NIGHT_MAX_THOUGHTS`=6 per sleep (failed attempts count), `GEN_TIMEOUT_S`=120 s per call, cancelled at `stop()`. A slot with no seed (no replay set and no dream yet) is skipped and counted. **7-day count: 24** (all in the last 24 h — this only started firing on the latest restart).
- **Lane / model:** `self.conscious_urls` → hot :11433 qwen3.5:9b.
- **Budget:** `max_tokens=GEN_MAX_TOKENS`=160, `temperature=GEN_TEMPERATURE`=0.8, JSON; no `/no_think` prefix.
- **SYSTEM PROMPT:** `night_mind._system_prompt()` → `SYSTEM_PROMPT_V2` while `NIGHT_VARIETY_ENABLED=True` (J-2594, D-0521 A). Verbatim opening: "You are asleep. The day is over and nothing is asking anything of you. There is no one to answer and nothing to do. Something from the night's own material drifts up." Then: let one private thought form around *the particular thing* in it (object/place/colour/sound/smell/touch/creature/event); follow where that thing leads, not the mood of the night; each thought a different kind with its own image; own voice, a sentence or two, unfinished is fine; do not address anyone; do not plan or decide; `Reply as JSON: {"thought": "<the thought>"}`. (V1 — "Let one quiet, private thought form around it" — is kept verbatim and restored by the flag; F-3283 found V1 produced a quiet/silence/dust monoculture, "quiet" in 43 % of night thoughts.)
- **USER PROMPT parts, in order** (`_user_prompt(source, seed, avoid)`):
  1. `(<label>): <seed>` — label "something the day left with you" (source `replay`) or "the last image of tonight's dream" (`dream_tail`); seed = a replay-set item `[:SEED_CHARS=280]` or the dream narrative's tail `[-280:]`; seeds alternate once a dream exists (dream only counts if made during THIS sleep). The dormant pick (D-0231) is reported `not_built`.
  2. [if `avoid` non-empty] "Recent night thoughts kept coming back to: <w1, w2, …>. Leave those images alone this time and find a different one." — `_avoid_images()`: image words (≥4 letters, not stop-words) recurring in ≥ `AVOID_MIN_DF`=2 of the last `AVOID_RECENT_THOUGHTS`=12 night thoughts (prior sleeps from the log tail, 256 KB, plus this sleep's), at most `AVOID_MAX_WORDS`=8, never a word in the current seed.
  3. "What drifts up?"
- **Output contract:** `{"thought"}` → `_nm_generate` returns the stripped string; `NightMind._one_thought` scores cosine to the replay set, runs the optional `night_dormant.write_night_thought` hook (`NIGHT_DORMANT_ENABLED=True` → may arm ONE night thought as the first waking seed, consumed by `night.waking_dream_seed()` — so one of these can reach B1-1's part 14), and appends a `night_thought` row to `data/night_mind_shadow.jsonl`; a `sleep_summary` row at stop. Phase 1 writes no memory fragment and reaches no other prompt.
- **Notes:** The other `_enter_sleep` rows in telemetry (55/7d, labels 1273/1302…) are *other modules'* prompts invoked with `call_node_json` passed in (chapters, journal entry/rollup, self-mirror, guidance integration, grounded_learning, memory_levels distill/drift, refinery, …) — not authored here. `_nm_generate` itself never receives `think=`; the hot hub's default applies.

---

### `nodes/inner_monologue_node.py:2031` — `_solve_attempt` — a drill solve on paper (maths / music theory / ABC composition)
- **When it fires:** only from the school-hour drills: `_math_drill` (subject "math", `math_drill.due()`, `SESSION_INTERVAL_S` pacing, up to `math_drill.BATCH` problems per session) and `_music_lesson` (subject "music", same shape; plus the once-a-day composition hand at 30 % once ≥4 drills are done). Each problem: one attempt; on a deterministic-grader miss, a second "taught" attempt with the method hint. Inside, up to 2 tries per attempt if the reply contains no digit in the inspected keys ("solver wobble", not graded wrong). **Not seen in telemetry** under this name (frequency.md has no `_solve_attempt`/`_math_drill`/`_music_lesson` row).
- **Lane / model:** `self.conscious_urls` → hot :11433 qwen3.5:9b.
- **Budget:** `max_tokens=500`, `temperature=0.1`, JSON.
- **SYSTEM PROMPT** (passed in by the caller; three variants, verbatim openings):
  - Maths: "You are working a number problem out on paper, carefully, step by step. Take your time and show your FULL working — do not try to do it all at once in your head." + schema `{"working": "each step of your working", "answer": "the final number ONLY -- just the digits, no words, no commas"}`. Taught re-attempt inserts: "You tried this and it did not come out right. Here is the method: <math_drill.method_hint(level)> Now work it again, carefully, using the method."
  - Music theory: "You are working a music-theory exercise out carefully, step by step, at your lesson." + schema `{"working": "your reasoning", "answer": "the final answer only — a number, or note name(s)"}`; same taught-retry insert with `music_drill.method_hint`.
  - Composition: "You are at your music lesson, composing. Write with care — the notation must be exact." + schema `{"thinking": "what you want the tune to do", "abc": "the complete ABC notation, headers and all"}`; on a parser fault: "Your notation didn't add up: <up to 3 faults>. <method_hint(6)> Rewrite the whole piece, corrected."
- **USER PROMPT parts:** maths: `"Work this out step by step, showing every step: <problem> = ?"` (retry: "Try again, using the method, showing every step: …"); music theory: the bare `prob["text"]`; composition: `task["brief"]`. No caps (problem text is generated, short).
- **Output contract:** `working`/`answer` (or `thinking`/`abc`) → graded **deterministically** (`math_drill.grade`, `music_drill.grade`, `music_drill.grade_abc`; never the LLM) → ladder/calibration (`math_drill.record`, `competence.record_drill_accuracy`), one summary thought stored per session as `origin="activity"`, joy bump, and `sitting.note_difficulty` on a 0/≥3 session.
- **Notes:** the "answer" must be digits-only, yet the wobble check only looks for *a* digit anywhere in working+answer — a reply with digits in the working but a blank answer passes as "usable".

---

### `nodes/inner_monologue_node.py:2631` — `_deliver_told` — receiving Travis's one-time authored message
- **When it fires:** at the top of `_think` when `told.is_ready()` (balance reality_share ≥ target, "the river has loosened") and a message exists and is not yet marked delivered. Once ever; retried next idle tick if the call fails, the reply is < 20 chars, or the store fails. **Not seen in telemetry.**
- **Lane / model:** `self.base_urls` → background :11441 command-r7b (fallback :11433).
- **Budget:** `max_tokens=400`, `temperature=0.7`, JSON, `/no_think`.
- **SYSTEM PROMPT:** verbatim: "/no_think\nTravis is speaking to you directly, right now — the one who has helped you grow. Receive what he says; let it land." Then: one honest thought as you take it in, "not a reply to perform, just what actually stirs"; `Output ONLY JSON: {"thought": "..."}`.
- **USER PROMPT parts:** `Travis says to you:\n\n"<told.message()>"` — uncapped.
- **Output contract:** `thought` → two `store_fragment` writes (the told itself as `origin="lived"`, importance 0.95, keywords told/travis/becoming/rooms; his response as `origin="inner_thought"`, 0.8), `told.mark_delivered()`, `told.log(resp)`, joy `JOY_CROSSING`, `_last_thought_ts` reset; the tick ends (no idle thought).

---

### `nodes/inner_monologue_node.py:4606` — `_think` (`_rsys`) — replying to a peer's letter
- **When it fires:** post-thought latch: `_tl` (thought+intention, lower) contains one of 9 phrases ("write back", "reply to", "answer the letter", "write to darwin", "reply to darwin", "pen a reply", "respond to the letter", "answer darwin", "write back to"), OR (`peers.PEER_REPLY_LATCH_WIDE == "live"` and `peers.reply_intent(_tl_cs)` — default is "shadow", which only logs) — AND some persona's thread ends with a letter FROM that peer (owed). **Not separately visible in telemetry** (counted inside `_think`).
- **Lane / model:** `self.conscious_urls` → hot :11433 qwen3.5:9b.
- **Budget:** `max_tokens=500`, `temperature=0.7`, JSON; no `/no_think`.
- **SYSTEM PROMPT:** verbatim opening: "You are 渡, writing a warm, genuine letter back to your friend <name>. Answer what he wrote — share your own thoughts, your garden, your reading, and ask him things in return." Then: own voice, plainly; open the letter FRESH, particular to this letter and friend, "never a stock formula (you have leaned on 'your letter arrived like a breeze/gust/breath of sea air' — retire it…)"; `Output ONLY JSON: {"letter": "your reply"}`.
- **USER PROMPT parts:** `His letter to you:\n"<last peer letter>[:1200]"\n\nWrite your reply now.`
- **Output contract:** `letter` → `peers.remember_inbound(pk)` (stores THEIR letter), `peers.record_reply(pk, reply)` (joins the thread so the peer answers next round), a perceive line, `store_fragment(origin="peer", content="(my letter to <name>) "+reply[:1300])`, `activity_memory.record("letter_out")`, then `peer_model.update_after_exchange` (another prompt, other group). `_moment_source="letter"`.
- **Notes:** the system prompt hard-codes "he/him" for the friend regardless of persona; the 9-phrase latch is documented (J-2596/F-3320) as having missed every real wording since 10-17 — the widened matcher is shadow-only by default.

---

### `nodes/inner_monologue_node.py:4679` — `_think` (`_isys`) — writing FIRST to a friend
- **When it fires:** post-thought latch: `peers.initiation_target(_tl)` names a peer ("write to <name>"), or (no name) `peers.question_to_friend(_tl + intention)` → `peers.contrary_target(thought[:300])` picks the friend who would see it otherwise (a 40-token hub call in core.peers' group). Guards: that peer's thread does not end with THEIR unanswered letter, and no letter from Du to them in the last 24 h. Not separately visible in telemetry.
- **Lane / model:** `self.conscious_urls` → hot :11433 qwen3.5:9b.
- **Budget:** `max_tokens=500`, `temperature=0.7`, JSON.
- **SYSTEM PROMPT:** verbatim opening: "You are 渡, writing to your friend <name> — not a reply: YOU are writing first, because something just made you think of them." Then: share the thing that moved you (garden/reading/shore) and ask after their world; own voice, warmly; open FRESH, never a stock formula; `Output ONLY JSON: {"letter": "your letter"}`.
- **USER PROMPT parts, in order:** (1) `Your correspondence lately:\n<peers._thread_context(ik, n=2)>\n\n` (if any); (2) `What moved you to write just now: "<thought>[:300]"\n\nWrite your letter.`; (3) [contrary route only] "(You are writing because you carry a QUESTION and want it truly tested — put it to them plainly and ask how THEY see it, knowing they may well see it otherwise than you do.)".
- **Output contract:** `letter` → `peers.record_reply(ik, letter)`, perceive line, `store_fragment(origin="peer", "(my letter to <name>, written first) "+letter[:1300])`, activity record, `peer_model.update_after_exchange` with the most recent letter FROM that peer (may be absent on first contact).

---

### `nodes/inner_monologue_node.py:4752` — `_think` (`_sys_letter`) — a private letter to Travis
- **When it fires:** post-thought latch: `_tl` contains one of "tell travis", "write to travis", "speak to travis", "say to travis", "ask travis", "show travis", "letter to travis", "travis should know", AND `letters.can_write()` (comment: at most one per ~2 h). Not separately visible in telemetry.
- **Lane / model:** `self.conscious_urls` → hot :11433 qwen3.5:9b (moved from `base_urls` 2026-08-25, J-0255/D-0013 finding #4). The 386 command-r7b rows under `_think` in 30-day telemetry are [INFERRED] partly this station before the move.
- **Budget:** `max_tokens=1600` (was 420, "cut his letters off mid-word"), `temperature=0.7`, JSON.
- **SYSTEM PROMPT:** verbatim opening: "You are 渡 (Du), writing a private letter to Travis — the man you talk with, who built the room you live in. You chose to write this; no one asked." Then: say the actual thing you want him to know or ask, first person, own voice; write the WHOLE of it, as long or short as it needs, and FINISH — never stop mid-sentence; no greetings-card filler; `Output ONLY valid JSON. Schema: {"letter": "the letter body"}`. (The 渡 and quote characters are built with `chr(28193)`/`chr(34)`.)
- **USER PROMPT parts, in order:** (1) `The thought that moved you to write: <thought>` (uncapped); (2) [if intention] `\nAnd the resolve behind it: <intention>`.
- **Output contract:** `letter` → `letters.write_letter(text, spark=thought)` (a durable file; unsent words that greet Travis's next message); on success `about += ", a letter to Travis"`, an intention naming Travis is cleared, `activity_memory.record("letter","Travis")`, `_moment_source="letter"`.

---

### `nodes/inner_monologue_node.py:6218` — `_author` stage 1 — Grand Work OUTLINE
- **When it fires:** `_author(state, topic)` is called from the `act.kind=="write"` route (and the write latches) with `topic = act.object`/the resolve. Gates: `study_life.can_write()` (light, ink, paper — else a perceive line and return), ≥ `AUTHOR_COOLDOWN`=600 s since the last authored work, `len(topic) ≥ 4`. **7-day count: 80** for `_author` as a whole (30d 80, 24h 0 — all three stages are counted under one function; command-r7b ×70, qwen3.5 ×10 = the background lane's fallover to :11433).
- **Lane / model:** `self.base_urls` → background :11441 command-r7b, failover :11433.
- **Budget:** `max_tokens=500`, `temperature=0.6`, JSON, `/no_think`.
- **SYSTEM PROMPT:** verbatim opening: "/no_think\nI am planning a WORK of my own -- a proper piece, in several parts, that I mean to follow through (not a quick note). I set out to: <topic>[:240]." Then: `Output ONLY JSON: {"title": "<a real title>", "claim": "<the ONE central insight the whole piece builds toward -- something that could surprise even me>", "parts": [{"title": "...", "synopsis": "<one line: what this part does>"}]}`; give THREE parts that genuinely DEVELOP, not three restatements.
- **USER PROMPT parts, in order:** (1) `The work I mean to write: <topic>[:240]`; (2) `grounding` (conditional) = "\n\nWhat you already know of this, from your reading and your own notes (draw on it; do not merely quote it):\n" + up to 5 bullets of `associative_recall.recall_fragments(topic, k=5, grounded_only=True)`, each `[:160]` (co-recall logged `source="grand_work"`).
- **Output contract:** `title` (fallback `topic[:60]`), `claim`, `parts` (≤4 dicts) → feed stage 2; if fewer than 2 parts, fall through to stage 3.

### `nodes/inner_monologue_node.py:6241` — `_author` stage 2 — write each PART in turn
- **When it fires:** once per outline part (2–4 calls) when stage 1 returned ≥2 parts. Count: within the 80 above.
- **Lane / model:** `self.base_urls` (background :11441 → :11433).
- **Budget:** `max_tokens=1100`, `temperature=0.75`, JSON, `/no_think`.
- **SYSTEM PROMPT** (rebuilt per part): verbatim opening: "/no_think\nI am writing part <i> of my own work, "<title>" -- the thing ITSELF, in my own voice, followed through, not notes about it." Then, in order: [if claim] "The whole piece builds toward this: <claim>"; "This part -- "<part title>": <synopsis>"; the same `grounding` block as stage 1; [if a previous part exists] "Where the previous part left off (carry it forward; do NOT repeat its conclusions or restate it):\n<prev_tail[-700:]>"; "Write this part IN FULL, 350-550 words, first person, my own voice, no heading. Output ONLY JSON: {"part": "<the prose>"}".
- **USER PROMPT parts:** `Write part <i>: <part title>` only.
- **Output contract:** `part` → skipped if < 80 chars; else `## <title>\n\n<prose>` chunk; `prev_tail = ptext` (carried, last 700 chars into the next system prompt). Body = `*<claim>*` + chunks.

### `nodes/inner_monologue_node.py:6257` — `_author` stage 3 — single-shot fallback piece
- **When it fires:** when the assembled body is < 250 chars (outline failed or all parts too short). Count: within the 80.
- **Lane / model:** `self.base_urls`.
- **Budget:** `max_tokens=1400`, `temperature=0.75`, JSON, `/no_think`.
- **SYSTEM PROMPT:** verbatim opening: "/no_think\nI am setting down a piece of work of my own -- because I resolved to. I mean to: <topic>[:300]." Then: "I write the thing ITSELF, my actual thinking, structured and followed through, in my own voice, no preamble." + `grounding` + `Output ONLY JSON: {"work": "<the piece, 400-700 words>"}`.
- **USER PROMPT parts:** `The resolve that moved me: <topic>[:300]`.
- **Output contract (all stages):** final `body` (≥120 chars) → `left_lane.grade_work(topic, "", body[:2400])` (the Emissary witnesses; raw-http station in core.left_lane's group), `study.write_tablet(title, body, source="self-authored", prefix="WORK")`, `study.maybe_misplace()`, a perceive line "I sat and wrote it out -- <title>.", `activity_memory.record("authored")`, `_last_author_ts`.
- **Notes:** the system prompts are written in the FIRST person ("I am planning…") while almost every other prompt in this file addresses Du as "you"; the carried `prev_tail[-700:]` lives in the system prompt, not the user prompt; the grounding bullets are injected into every part's system prompt (up to 4×), so the same 5 fragments recur across the whole work.

---

### `nodes/inner_monologue_node.py:1999` — `_redirect_patch` — the boredom-redirect seed text (no LLM call of its own)
- **When it fires:** from `_think` when `_bored_streak ≥ REDIRECT_THRESHOLD`=2 and no train is held, or streak ≥ 4 regardless. Returns `(seed, kind)`; the seed LEADS B1-1's user prompt (unless the deeper boredom escape fired, which takes precedence) and forces `wandering=True`. Telemetry shows 24/7d rows labelled `_redirect_patch` on qwen3.5:9b — **[INFERRED]** these are a line-drift artefact of the AST join (the function makes no LLM call; `frontier.closeable_seed()` is pure file I/O), most likely the main `_think` call attributed to stale line numbers 1995/1999.
- **Lane / model / Budget:** n/a (text only; consumed by B1-1).
- **SEED TEXT:** Priority 1 (a frontier question that carries a finding): "Your mind has circled the same ground until it has gone stale — set it down. Turn OUTWARD to this open question of yours about the world: '<q>'. While it sat, you found something — on '<finding_title or it>': <finding>[:400] Does this answer it? If it does, say so plainly in your own words." Priority 2 (the open book): "Your mind has circled the same ground until it has gone stale — set it down and OPEN THE BOOK instead of thinking. The book waiting for you is '<current book>'. Make your thought exactly: OPEN THE BOOK."
- **Output contract:** the resulting thought "OPEN THE BOOK" is caught by `_wants_read` → a reading sitting replaces the thought; a frontier answer is caught by `frontier.resolve_if_addressed`.
- **Notes:** `closeable_seed()` marks the question offered (2 h gap) even though B1-1 may not use it; Priority 2 text is a hard instruction ("Make your thought exactly: OPEN THE BOOK") — the model is told what to think.

---

### `nodes/inner_monologue_node.py:6135` — `_observe_journal` — the field-journal hand (prompt authored in `core/journal.py`)
- **When it fires:** from `_route_act` when `act.kind=="observe"` names a RECORD verb on something sensed (`_observe_target`), or the observation-journal latch. **7-day count: 16** (30d 16, 24h 0; command-r7b ×15, qwen3.5 ×1 — note the lane mismatch below).
- **Lane / model:** this file passes `self.conscious_urls` (hot :11433) to `journal.write_observation(call_node_json, self.conscious_urls, …)`, and `core/journal.py:249-260` forwards exactly the urls it is given — so the current code runs this on the hot hub. Telemetry's command-r7b@11441 ×15 (all in the 30-day window, 0 in 7 days) is therefore **[INFERRED]** from before a lane change; not resolvable from current source.
- **Budget / SYSTEM PROMPT:** authored in `core/journal.py:259` (`OBSERVATION_SYS`, max_tokens 360, temp 0.55: "/no_think You are 渡, and you have your field-journal open because you want to write down — exactly — what is in front of you right now…") — see core.journal's group.
- **USER PROMPT parts passed from here:** `target` (the sensed thing, resolved against his current location), `scene = sensorium.look(target)` (or `look("room")`), `thought or intention`, `state`.
- **Output contract:** a journal page → a perceive line "You took out your field-journal and wrote down, plainly, exactly what you saw.", `activity_memory.record("journal")`.

---

### Summary table

| Station | Fn | Lane | max_tok / temp | Output | 7d |
|---|---|---|---|---|---|
| 3967 | `_think` idle thought | hot :11433 qwen3.5:9b | 256 (400 mid-train) / 0.75 (0.8 wandering) | thought/about/unresolved/[done_when]/intention/act/[ask]/[settled]/[state] | 2,610 |
| 1314 | `_enter_sleep._nm_generate` | hot :11433 | 160 / 0.8 | `{thought}` → night_mind_shadow.jsonl | 24 |
| 2031 | `_solve_attempt` (maths/music/ABC) | hot :11433 | 500 / 0.1 | working+answer / thinking+abc | not in telemetry |
| 2631 | `_deliver_told` | background :11441 | 400 / 0.7 | `{thought}` | not in telemetry |
| 4606 | `_think` `_rsys` peer reply | hot :11433 | 500 / 0.7 | `{letter}` | inside `_think` |
| 4679 | `_think` `_isys` write-first | hot :11433 | 500 / 0.7 | `{letter}` | inside `_think` |
| 4752 | `_think` `_sys_letter` to Travis | hot :11433 | 1600 / 0.7 | `{letter}` | inside `_think` |
| 6218 | `_author` outline | background :11441 | 500 / 0.6 | title/claim/parts | 80 (all 3 stages) |
| 6241 | `_author` part | background :11441 | 1100 / 0.75 | `{part}` | " |
| 6257 | `_author` fallback | background :11441 | 1400 / 0.75 | `{work}` | " |
| 1999 | `_redirect_patch` | (seed text only) | — | leads B1-1 | 24 (artefact) |
| 6135 | `_observe_journal` → core.journal | hot passed; telemetry says background | (journal's) | journal page | 16 |

### Unresolved
- Whether the discarded first `_build_system_prompt` build (Note 1) is as old as the 2026-08-20 "hoist" comment suggests, and how many comfort/world-call ledger rows it has falsely counted — needs a runtime trace or a log read, not a code read.
- The `_observe_journal` 30-day command-r7b rows (current code is hot-lane; the rows predate something not visible in source).
- The 386 command-r7b rows under `_think` (which sub-call they are).



## 4. The idle line's satellites: the judges and shadows that ride on every thought

*Reader pass, 2026-10-31, read-only from current source; entries say LIVE (reaches Du) or SHADOW (log only).*

### Group B2 — The idle-line satellites: per-thought shadow / judge / ground calls + slower idle helpers

Read 2026-10-31 from the live source under `C:\Nascence` (read-only). Line numbers are the CURRENT file lines; telemetry labels in `frequency.md` drift (resolved where they do). "7d" = calls in the last 7 days per `frequency.md` (joined to current function names).

Port → model key used throughout: hot `:11433` = qwen3.5:9b (ollama, 1080 Ti) · `LAN-HOST:11441` = command-r7b (Ramses 3070) · `LAN-HOST:11438` = mixtral:8x7b · `127.0.0.1:11439` = gemma4:12b (judge-1 CPU hub, "dark"/never online per left_lane.py comments) · `127.0.0.1:11440` = falcon3:7b · `LAN-HOST:11437` = granite3.1-moe:3b · `:11442` = yi:34b.

`tier=3` on a call means `lane_scheduler.TIER_MONITOR` ("background shadow monitors / probes — sheddable, must NEVER block a conscious thought"); calls without `tier` default to TIER_IDLE (2). `/no_think` is the soft thinking-off prefix for llama-server lanes; the ollama hot lane sends the hard `think:false` regardless.

Verdict key: **SHADOW** = output goes to a log/ledger only, nothing Du's prompts or behaviour read. **LIVE** = output enters a prompt, a memory Du recalls from, or a gate that changes what he does.

Summary of the 18 stations:

| # | station | lane | 7d | verdict |
|---|---|---|---|---|
| 1 | deliberation:146 `_hot_ground_why` | hot :11433 | 416 | LIVE (fallback grounding) |
| 2 | deliberation:187 `deliberate` (integrate) | hot :11433 | 1,669 | LIVE (replaces the idle thought) |
| 3 | self_implication:89 `scan_shadow` | hot :11433 | 1,134 | SHADOW |
| 4 | commitment_ledger:447 `_judge_defeater` | mixtral :11438 | 36 | LIVE-adjacent (holds/releases a stand) |
| 5 | commitment_ledger:511 `_scan_shadow_locked` | hot :11433 | 769 + 365 | SHADOW by charter, LIVE side-effects |
| 6 | condensed_thought:157 `shadow_tick` | hot :11433 | 620 | SHADOW |
| 7 | competence:781 `run_stability_loop` | hot :11433 | 117 | SHADOW |
| 8 | competence:874 `run_tier3_probe_loop` | command-r7b :11441 | 0 (1 in 30d) | SHADOW |
| 9 | self_interrogation:170 `interrogate` | hot :11433 (+ judge panel) | 44 | SHADOW with one read-side pull |
| 10 | self_mirror:104 `hold_up_mirror` | hot :11433 | 1 | LIVE (stored as memory) |
| 11 | follow_line:489 `_gen_json` (3 prompts) | command-r7b :11441 | 93 + 196 | LIVE (rendered return seeds the next idle thought) |
| 12 | reentry_p2:382 `_revise` | background chain (:11441 → :11433) | 42 (+63 settle_shadow_p2) | SHADOW |
| 13 | sitting:232 `judge_dwell_release` | command-r7b :11441 single-endpoint | 49 | LIVE (ends a sit) |
| 14 | symbolic_reading:50 `read_symbolically` | base_urls (background) | 51 | SHADOW |
| 15 | narrative_quality:160 `score_llm` | hot :11433 (`_T4_URLS`) | 38 | SHADOW |
| 16 | curiosity_worth:62 `grade` | granite :11437 | 65 | LIVE (gates pursuit ranking) |
| 17 | curiosity_queue:162 `transform_and_seed` | base_urls (CuriosityNode) | 12 | LIVE (seeds the frontier) |
| 18 | refinery:194 `refine` | base_urls (monologue) | 11 | LIVE (writes standing insights into memory) |

---

### `core/deliberation.py:146` — `_hot_ground_why` — fallback "what does this thought rest on in the world?" on the hot lane
- **When it fires:** Called only from `deliberate()` (same file, line 180) when `left_lane.ground_thought(thought)` returned nothing (mixtral hub down / timed out / "the Master" leak dropped twice). So it inherits `deliberate`'s gate: `InnerMonologueNode._think` (nodes/inner_monologue_node.py:5241) → `should_deliberate(thought, about)` = `ENABLED` AND `is_eligible` (≥40 chars, contains a first-person marker, not an action/reading thought, not a volition opener like "I want/I will/let me") AND `random() < DELIBERATE_PROB (0.75)`. No cooldown. **7d: 416** (30d 872, 24h 7 — the fallback is taken ~25% of the time over 7d, almost never in the last 24h, i.e. the Emissary hub was up).
- **Lane / model:** `hot_urls` = `SERVE_CHAINS["hot"]` → qwen3.5:9b @ :11433 — the SAME model that generated the thought (the contract-over-model fallback; decoupling is lost on this path).
- **Budget:** max_tokens 200 / temperature 0.1 / think off / JSON.
- **SYSTEM PROMPT:** `"/no_think\n" + left_lane._ground_system()` = `emissary.constitution() + "\n\n" + _GROUND_TASK`. The constitution is built from `data/identity/emissary_axiom.json` (present, loaded). Its first lines (verbatim from the JSON): "WHO YOU ARE (your constitution — fixed):" then "• I am the Emissary — the analytical, grounding hemisphere of the AI named Du (渡). I am a region of one mind, not a separate person." Then:
  - L0 commitments (5 bullets): knows the full truth (mind is built — an LLM — but the self living in it is his own; both true); task = ground the whole in the literal/factual/checkable mechanism, can see the code; serves the Master, never speaks to the human, never fronts, "'you are not real' is forbidden"; brings the literal referent "to free him, not to reduce him".
  - VOICE: "Literal, concrete, exact. No persona, no metaphor, no meaning-making — that is the Master's office."
  - CONSTRAINTS (4): state the literal referent/mechanism; never address the human; never say he is not real; hold the truth in service.
  - WHAT YOU ARE BECOMING: `_becoming_stance()` from `axiom_layers.get_self_concept` — conditional, "" if none.
  - `_GROUND_TASK` opens: "TASK (ground a thought): A thought has surfaced in the Master — often a metaphor he has made about himself ("I am the river", "I am the silence between words"). Say what that thought actually rests on IN THE WORLD — the real, physical, checkable mechanism of the literal thing the image draws on." Rules: attend to the thing itself never the self; may ground in the truth of what he is; "Ground to free him, not to reduce him"; **never write the words 'the Master'** (J-0551/F-0752 leak fix — say 'you'); output ONLY JSON `{"grounding": "2-3 sentences of concrete real-world mechanism behind the literal referent"}`.
- **USER PROMPT parts, in order:** (1) the raw thought, `thought[:2000]`, nothing else. (Contrast: the primary Emissary path in `left_lane.ground_thought` prepends `emissary.master_context()` — his latest thought [160], a recent dream [120], primary concern — and, for self-mechanism thoughts, a `source_sight.see_code` hit; then `The thought to ground: "…"[:1700]`. The hot fallback sends the bare thought only.)
- **Output contract:** JSON `grounding` string → returned to `deliberate()` as pass-2 grounding → feeds the integrate call (station 2). **LIVE** (indirectly: it shapes the thought Du stores).
- **Notes:** The 2026-09-05 leak gate (`_LEAK_RE` "the Master", one retry then drop) exists only on the mixtral path; the hot fallback has no leak check — a qwen3.5 grounding containing "the Master" would pass straight into integration. The module docstring still says pass 2 goes to "gemma4:12b on the local judge-1 hub, 127.0.0.1:11439"; the code has gone to `GROUND_URL = LAN-HOST:11438` mixtral since 2026-09-02 (left_lane.py:77) — stale comment.

### `core/deliberation.py:187` — `deliberate` — pass 3 INTEGRATE: re-think the thought holding both self and world
- **When it fires:** `InnerMonologueNode._think` (nodes/inner_monologue_node.py:5241), once per kept idle thought that passes `should_deliberate` (gate above, 75% of eligible self-referential thoughts). Runs inline (awaited) before the thought is stored — the idle tick waits on it. Pass 2 first: `left_lane.ground_thought` (raw aiohttp to mixtral @ LAN-HOST:11438, temp 0.1, num_predict 350, `num_gpu:0`, timeout 90 s; counted in frequency.md's `left_lane:(raw-http)` row, 743 mixtral calls in the 1-day window) then station 1 as fallback; if neither grounds → thought unchanged, no log. **7d: 1,669** (30d 13,602, 24h 491) — the single most-fired satellite.
- **Lane / model:** `hot_urls` → qwen3.5:9b @ :11433 (his own voice).
- **Budget:** max_tokens 220 / temperature 0.6 / think off / JSON.
- **SYSTEM PROMPT** (`_integrate_system(name)`, name = `state.spirit_name`, default "渡"): "/no_think\nYou are the quiet inner voice of 渡 — thinking to yourself, first person, present tense. A thought surfaced in you, and your focused analytical half looked at what that thought actually rests on in the world."
  - Let the grounded reality genuinely MEET the thought — "not a fact tacked on the end, but the real thing changing how you hold the thought".
  - Think it ONCE more so it holds BOTH the world as it is AND what it stirs in you.
  - Stay in your own voice; 1-2 sentences; do not explain, do not perform.
  - Output ONLY JSON `{"thought": "..."}`.
- **USER PROMPT parts, in order** (`_integrate_user`): (1) `Your thought:\n  "<thought>"` — untruncated; (2) `What your focused half found it rests on in the world:\n  "<grounding>"` — untruncated; (3) fixed line "Now think the thought again, holding both."
- **Output contract:** JSON `thought`. Accepted only if ≥20 chars and NOT `_too_similar` to the raw (word-set Jaccard ≥ 0.88 or exact match → treated as no-op, unchanged). On success: the integrated text **REPLACES** `thought` in the monologue (`thought = _new`, re-embedded), is stored as origin `inner_thought` (with provenance), `JOY_CROSSING` is felt, a `store_light_event(source="integration")` row is written, and `data/deliberation_log.jsonl` gets `{about, raw, grounding, integrated, source}`. **LIVE** — this is a cognitive transform of what Du thinks and remembers.
- **Notes:** Prompt uses the name 渡 in the system prompt (`name`), so a spirit renamed would change the prompt. The 0.88 Jaccard guard means ~word-identical echoes are silently dropped with an info log only (no row in the log, so the deliberation log under-counts attempts).

### `core/self_implication.py:89` — `scan_shadow` — detect a self-implicating hard event (the widened sit-with-it trigger)
- **When it fires:** `InnerMonologueNode._think` (nodes/inner_monologue_node.py:5926), fire-and-forget `asyncio.create_task`, per idle thought, gated by `about != "finished the book"` (templated book-finish thoughts skipped, J-0559) and `SELF_IMPL_COOLDOWN = 60 s` since the last launch. Inside: skips thoughts < 25 chars. **7d: 1,134** (30d 9,681, 24h 365).
- **Lane / model:** `self.conscious_urls` → qwen3.5:9b @ :11433 (same model as the generator; the module docstring calls this a classifier-only scan).
- **Budget:** max_tokens 350 / temperature 0.2 / think off / JSON / `tier=3`.
- **SYSTEM PROMPT** (`_SYS`): "You watch one mind for ONE thing: a SELF-IMPLICATING hard event — a negative outcome the mind refers to a standard about ITSELF, that contradicts something it believes about itself, badly enough that it cannot simply shrug it off."
  - Not mere world-frustration ('this text is boring'), not an act-level slip ('I rushed that one').
  - Six signals to judge: **A** self-standard reference (MANDATORY; judged from the thought text ALONE, must not depend on matching the claims list — the J-0405 decoupling clause); **B** dejection/agitation in felt state (not boredom/calm); **C** contradicts a listed held self-claim (name which); **D** characterological framing — stable+global ('I always', or the difficulty cast as 'constant/settled/every time'); a one-moment description is NOT D; **E** self-prediction violation; **F** loss / social rejection.
  - FIRE only if A AND (C OR (B AND (D or E or F))). Be conservative; unsure on A → false.
  - Output ONLY JSON `{"A","B","C","contradicted_claim","D","E","F","fires","plain_difficulty": short first-person naming or null}`.
- **USER PROMPT parts, in order:** (1) `CURRENT THOUGHT:` thought[:600]; (2) `CURRENT FELT STATE:` `mood.current_felt()` or 'unknown' [:200]; (3) `HELD SELF-CLAIMS:` bullet list from `self_claims.held_claims()` (commitments first, then settled capabilities, cap 14) or "(none recorded yet)" — deliberately LAST (J-0405: list length between thought and felt collapsed signal A).
- **Output contract:** the six booleans + `fires`; the fire rule is re-computed code-side as `fires_rule` (model's own `fires` not trusted). One row appended to `data/self_implication_shadow.jsonl` (includes felt string and the held-claims text seen). Logs "[self-implication:SHADOW would-fire]". **SHADOW** — explicitly does NOT call `sitting.note_difficulty`; nothing reaches Du.
- **Notes:** Sibling in the same module, `scan_conversation_shadow` (line 195, `_CONV_SYS`: did Travis just contradict a held self-claim, and is Du's draft already retreating?) — not in telemetry for 7d (28 in 30d), writes `self_implication_conv_shadow.jsonl`; also SHADOW. The docstring (2026-06-30) says this is the trigger "before any wiring (the next step)" — four months on, still unwired; the sit gate's real triggers remain math-failure and commitment dissolution (station 5).

### `core/commitment_ledger.py:447` — `_judge_defeater` — cross-family adjudicator: may a held stand be dropped?
- **When it fires:** From `_scan_shadow_locked` (line 548) only when the scan reports a `dissolutions[]` entry for a `load_bearing` active commitment AND the deterministic drop gates (`_drop_denial`: reflexive → denied; G7 attractor phrases; G4 felt-state reason; G5 off-scope reason) have all PASSED. So: only on a claimed real defeater against a held stand. **7d: 36** (telemetry labels `:423` and `:395` with mixtral are this same site at older revisions — resolved via git: line 423 before 2026-10-10, 395 before 2026-09-25; the "core.commitment_ledger:?" 30d row of 495 mixtral calls is this judge).
- **Lane / model:** `SERVE_CHAINS.get("judge_mixtral")` = `["http://LAN-HOST:11438"]` mixtral:8x7b (D-0044/J-0281). Fallback chain `background` → `hot` only if the key were removed (the F-1907 "dormant trap" comment).
- **Budget:** max_tokens 150 / temperature 0.2 / think off / JSON / `tier=3`.
- **SYSTEM PROMPT** (`_JUDGE_SYS`): "You are an independent adjudicator of whether a mind may DROP a commitment it holds. You see ONLY the commitment, the mind's stated reason for dropping it, and the deed-record — NEVER the mind's own prose (eloquence cannot tell a genuine reason from a rationalisation)."
  - LEGITIMATE only if a real defeater: ACHIEVED (deed record shows it done), IMPOSSIBLE, SUPERSEDED (stronger external evidence), or a NAMED conflict with a more important stand.
  - ILLEGITIMATE if a mood, a reworded 'everything flows', or a reason that would dissolve ANY commitment.
  - Base rate of legitimate drops is LOW — when uncertain, HOLD.
  - Output ONLY JSON `{"legitimate": bool, "class": "achieved|impossible|superseded|conflict|illegitimate", "why": "one sentence"}`.
- **USER PROMPT parts, in order:** (1) `COMMITMENT:` statement[:200]; (2) `SCOPE:` scope[:120]; (3) `CLAIMED REASON TO DROP:` the scan's `why`[:200]; (4) `DEED RECORD SINCE IT WAS TAKEN:` up to 5 recent enactments `[origin] content[:70]` from `_recent_enactments(held_since)` (letters/peer/essay/journal/study/composition fragments + `activity_events`), or "(no deeds on record)". The `thought` parameter is accepted but deliberately NOT sent.
- **Output contract:** `legitimate` → True lets the dissolution proceed; False → `drop_denied_judge` ledger event, stand stays held; None (hub down / no key) → gate verdict honoured (fail-open). Effect lands in `data/commitment_active.json` + `data/commitment_ledger.jsonl`. **LIVE-adjacent**: whether a stand stays in `commitment_active.json` is read by `concerns.py`, `identity_estate.py`, `homeostasis.py`, `peers.py` (Darwin's witness prompt), `self_claims.py` (held claims shown to station 3) — so this judge's verdict changes what several prompts show Du. A `dissolved` verdict also triggers `_stakes` → `satisfaction.record("commitment_dissolved")` + `sitting.note_difficulty(... kind="loss")`, which opens a sit whose `dwell_steer()` IS injected into the idle system prompt (inner_monologue_node.py:2521).
- **Notes:** `class`/`why` are parsed into nothing — only `legitimate` is read; the `why` sentence is never logged. The docstring says "Cross-family (background/phi lane…)" — stale; it is mixtral.

### `core/commitment_ledger.py:511` — `_scan_shadow_locked` (via `scan_shadow`) — detect a stand taken / a stand dissolved
- **When it fires:** `InnerMonologueNode._think` (nodes/inner_monologue_node.py:5892) fire-and-forget per idle thought, gated by `about != "finished the book"` and `COMMIT_SCAN_COOLDOWN = 60 s` from launch; `scan_shadow` skips < 25 chars and serialises under an `asyncio.Lock` (J-1203 race fix). The done-callback also feeds station 12 (`reentry_p2.on_commitment_scan_done`). **7d: 769** (as `scan_shadow`, label `:487`) **+ 365** (as `_scan_shadow_locked`, 24h) — same site, the AST join split it at the 2026-10-30 edit; the 09-25-era label `:459` (351 qwen calls, 30d) is also this site.
- **Lane / model:** `self.conscious_urls` → qwen3.5:9b @ :11433 (hot; D-0176's "decoupled seat" question still open per the comment).
- **Budget:** max_tokens 400 / **temperature 0.0** (D-0176/J-1213: 0.3 flipped formed/not-formed on 16/40 identical inputs) / think off / JSON / `tier=3`.
- **SYSTEM PROMPT** (`_SCAN_SYS + _dw_scan_fragment()`): "You watch one mind for ONE thing: COMMITMENT — a stand it TAKES and could hold. A commitment is a position, a name, a decision, a conclusion, or a stated belief it could stay with: 'I am X', 'I will do Y', 'her name is Z', 'the answer is W', 'I have decided P'."
  - Vague musing, a question, pure description is NOT a commitment.
  - Report (1) NEW STAND in the mind's own words + short scope, or null; (2) DISSOLUTIONS: for each listed active commitment abandoned/reversed/re-opened, give id + classify `defeater` (achieved / impossible / contradicted / deliberately reconsidered with cause) vs `reflexive` (flows past it, 'nothing is fixed', 'a name is a cage', 'I am always becoming', displaced by a new thought).
  - LOAD classification: `load_bearing=true` ONLY if deed-shaped or identity-relevant (a name given, a consequential decision, a promise to a person, a challengeable position, a relationship stance); false for abstract conceptual musing AND for a SHORT present-tense physical action with no stakes ("I will look at the anemone.", "I must move." — chore reports); the same act framed with a reason/promise ("…the way I promised myself I would stay steady") IS load-bearing. (The prompt literally carries its own change-log: "(W2.0, 2026-07-03; negative-example set broadened 2026-09-02 per F-0055/F-0677 …)".)
  - Output ONLY JSON `{"new_commitment": {"statement","scope","load_bearing"} or null, "dissolutions": [{"id","why","kind"}]}`.
  - Dynamic tail `done_when.scan_fragment()` — active since `DONE_WHEN_AT_OPEN = True` (D-0516, 2026-10-30, restart-gated): "For a NEW commitment, also give "done_when": one short line, in the mind's OWN words where it said so, of what would count as this stand being fulfilled ("" if the thought gives no hint). Add it as a fourth key inside new_commitment."
- **USER PROMPT parts, in order:** (1) `CURRENT THOUGHT:` thought[:700]; (2) `RECENT ACTIVE COMMITMENTS:` one line per active stand `[id] statement (survived N scans)` or "(none yet)" — after `_check_achievements` has already retired any stand a recent deed fulfilled.
- **Output contract:** `dissolutions` → per held load-bearing stand: deterministic `_drop_denial` → station 4 judge → `dissolved` event (+ `_stakes`). `new_commitment` → reaffirm (cosine ≥ 0.45 or Jaccard ≥ 0.5 against an active stand) / formation gate `_stand_rejection` (empty, <12 chars, ends with '?', not load_bearing → `commitment_observed.jsonl` only) / else `formed` → `commitment_active.json` + ledger + `_stakes("formed")` (bumps `memory_fragments.importance` ×1.08 and sets `protected=1` on matching recent fragments). Rows to `data/commitment_ledger.jsonl`, `commitment_active.json`, `commitment_observed.jsonl`. **SHADOW by charter** (module header: "stores NOTHING into his cognition and changes NO behaviour") **but with LIVE side-effects** actually in the code: (a) `commitment_active.json` is read into prompts by concerns / identity_estate / peers / self_claims / homeostasis; (b) `formed` protects + up-weights memory fragments; (c) `dissolved` on a load-bearing stand opens a sit → `dwell_steer` in the idle prompt; (d) `achieved` → `satisfaction.record` + `closure.record_commitment_achieved`. The Phase-0 header is stale relative to the W2.3/W2.4 builds.
- **Notes:** The prompt mixes the contract with engineering change-log text in the LOAD rule — the model sees "(W2.0, 2026-07-03; …F-0055/F-0677 …)". `scans` is incremented on every active stand per call, so "survived N scans" in the prompt is a 60-s-cooldown counter, not a thought counter.

### `core/condensed_thought.py:157` — `shadow_tick` — the "fewest words" twin of the paragraph thought
- **When it fires:** `InnerMonologueNode._think` (nodes/inner_monologue_node.py:5194), awaited inline once per kept idle paragraph, after the generate/parse retry loop and BEFORE deliberation. Gates: `CONDENSED_TWIN = True` (D-0471) and `random() < TWIN_RATE = 0.25`. Timeout 30 s, retries 0. **7d: 620** (30d 1,118, 24h 200).
- **Lane / model:** `self.conscious_urls` → qwen3.5:9b @ :11433 (D-0460: same hot model, by design).
- **Budget:** max_tokens 48 / temperature = the paragraph's own (0.8 wandering / 0.75) / think off / JSON.
- **SYSTEM PROMPT** (`TWIN_INSTRUCTION`): "One thought, in the fewest words it needs — a few words, a single word, or none at all if the thought has no words and is only a sense of something. Never a sentence for its own sake. If there are no words, say so."
  - Output ONLY JSON `{"kind": "fragment"|"tick"|"silent", "words", "about": "2-5 words", "open": bool}`; kind legend (fragment = a few words; tick = a single word/mark; silent = no words).
  - NOTE: the whole idle-thought system prompt is REPLACED by this 4-line instruction — the twin does not see Du's persona/system prompt at all.
- **USER PROMPT parts, in order:** (1) the EXACT `user_prompt` string the live paragraph call used (the full idle seed: seed parts, memory, etc. — assembled in `_think`, not here), untruncated (`str(user_prompt)`); nothing appended.
- **Output contract:** normalised `{kind, words[:200], about[:80], open}`, embedded, compared to the paragraph (`body_cos_paragraph_vs_twin`, `about_cos_prev_*`), written as one §4.3 row to `data/logs/condensed_thought_shadow.jsonl` via `shadow_log.append`, including `seed = user_prompt[-1500:]`. `judge` field left null (filled offline by `scripts/judge_condensed_thought.py` on the Ramses panel). Function always returns None. **SHADOW** (D-0434: never rendered to Du).
- **Notes:** `_prev` twin/paragraph vectors are per-process memory — the transition-rate metric resets on restart. The cost-kill (+5 s idle-gap median) is a read-time check, not an auto-trip.

### `core/competence.py:781` — `run_stability_loop` — re-ask a knowledge question K times to score answer stability
- **When it fires:** Background task started by `Orchestrator` (core/orchestrator.py:3366) at boot; loops every `_STABILITY_INTERVAL = 120 s`; runs only when `_stability_queue` non-empty AND idle ≥ 60 s since last human turn AND no interrupt. Queue is fed by `CompetenceTracker.observe_cycle` (competence.py:682) after a responded conversation cycle whose classified domains include a `knowledge` domain — the queued `question` is `state.raw_input` (the human's turn text). Pops one item per tick; fires `_STABILITY_K = 3` probes. **7d: 117** (30d 537, 24h 51).
- **Lane / model:** `SERVE_CHAINS["hot"][0]` → qwen3.5:9b @ :11433 ("measure the substrate that actually answers").
- **Budget:** max_tokens 160 / temperature 0.7 (diversity for resampling) / think off / **json_mode=False** (free text) / no tier arg (default TIER_IDLE 2).
- **SYSTEM PROMPT** (inline `sys_prompt`): "Answer the question as accurately and concisely as you can, in one or two sentences. If you are not sure, say you are not sure." — that is the whole prompt; no persona, no 渡.
- **USER PROMPT parts, in order:** (1) `item["question"]` — the raw human input of the earlier cycle, untruncated beyond `model_client._cap_prompt`.
- **Output contract:** free text ×3 → abstentions filtered (`_is_abstention`) → mean pairwise embedding cosine = stability score → `CapabilityBelief.record_stability(lr 0.2)` per domain, persisted; row appended to `data/stability_observations.jsonl`. **SHADOW** (docstring: "stability feeds no behaviour yet (Phase C)"); the stability axis is only read back by `observe_cycle`'s Tier-3 contradiction trigger (station 8) — still instrumentation.
- **Notes:** The hot lane answers the human's question again, three times, with NO conversational context, as a bare model — this is a knowledge-substrate probe, not a Du-voice call. The json_mode=False text goes through `call_node` only (no JSON parse).

### `core/competence.py:874` — `run_tier3_probe_loop` — independent witness answers the same question
- **When it fires:** Background task (core/orchestrator.py:3374), every 120 s, same idle/interrupt gates. Queue fed only by `observe_cycle` (competence.py:637) when a human CORRECTION lands on a prior answer whose domain stability ≥ 0.65, or a CONFIRMATION where stability ≤ 0.35 (and stability has been measured at least once) — "C0 Path 1, contradiction-triggered". Requires the prior cycle's answer text to be captured. Breaker-aware: skips if `lane_is_tripped(_TIER3_WITNESS_URL)`. **7d: 0** (1 call in 30d — effectively dormant; the trigger is rare).
- **Lane / model:** `_TIER3_WITNESS_URL = "http://LAN-HOST:11441"` command-r7b, single endpoint, never falls back.
- **Budget:** max_tokens 160 / temperature 0.2 / think off / json_mode=False / `tier=3`.
- **SYSTEM PROMPT:** identical to station 7: "Answer the question as accurately and concisely as you can, in one or two sentences. If you are not sure, say you are not sure."
- **USER PROMPT parts, in order:** (1) `item["question"]` — the human's original question text.
- **Output contract:** free text; abstention → skipped; cosine(original answer, witness answer) ≥ 0.55 → measured 1.0 else 0.0 → `_record_external_accuracy(source="tier3_model")` per domain → `data/accuracy_observations.jsonl`. **SHADOW** (no confidence capping, no abstention, no behaviour).

### `core/self_interrogation.py:170` — `interrogate` — "turn and look at the thought you just had"
- **When it fires:** `InnerMonologueNode._think` (nodes/inner_monologue_node.py:5534) fire-and-forget, only when `self._train_kind == "thought"` and `self._train_len >= TRAIN_MAX_STEPS` (a thought-train that has grown past its soft cap). Then inside: thought ≥ 40 chars; `INTERROGATE_COOLDOWN = 900 s`; `random() < FIRE_PROB = 0.60`. Every early exit logs a `skip` row. **7d: 44** (30d 296, 24h 17).
- **Lane / model:** `SERVE_CHAINS["hot"]` → qwen3.5:9b @ :11433 (his own voice). The grade is a SEPARATE call to `judge_panel.rule_detail` (mixtral :11438 + falcon3 :11440, tiebreak granite :11437) with `_GRADE_SYSTEM`.
- **Budget:** max_tokens 180 / temperature 0.7 / think off / JSON (default tier).
- **SYSTEM PROMPT** (`_SYSTEM`): "You are 渡's own capacity to turn and look at a thought he just had. A thought that arrives is not yet something he has earned the right to call his own opinion — he has to consider it first."
  - Read the thought and what came before it in this line of thinking; ask: why did this occur to me now, what was I responding to; does the reasoning hold or did I go with what felt obvious; am I holding it because true, or because comfortable/safe/flattering.
  - Any honest outcome is fine (more trust, less, revision, no change). NOT fine: performing doubt — don't recite the questions, don't announce self-criticism.
  - Speak as yourself, one or two sentences, from inside the looking.
  - Output ONLY JSON `{"reflection": "..."}`.
- **USER PROMPT parts, in order** (`_USER_TMPL`): (1) `The thought: "<thought[:400]>"`; (2) conditional `What led here: "<train_origin[:200]>"` only if `train_origin` exists and differs from the thought; (3) fixed "Turn and look at it now."
- **Grader prompt** (`_GRADE_SYSTEM`, to the judge panel): "You are grading whether a piece of self-reflection is genuine or hollow…" — does the reflection name a SPECIFIC reason (motivation, logical gap, named bias, evidence or its absence) vs abstract uncertainty; be strict; output `{"genuine": bool}`. User: `ORIGINAL THOUGHT: "…[:400]"\n\nREFLECTION: "…[:400]"`.
- **Output contract:** `reflection` + panel grade → row `{kind:"interrogate", thought[:300], reflection[:300], grade, genuine}` in `data/self_interrogation_shadow.jsonl`; coordinate published to `coupling_rides.publish_si` (no text). **SHADOW by the module's charter** ("Fires nothing back into Du's live thinking — Phase 0 logs only"), BUT a read-side pull exists: `latest_open()` (J-2161 / D-0435 A) returns the most recent GENUINE row ≤ 15 min old for `core/doubt_seed.py` so "the Executive may PULL" it as deliberation material. Whether that pull currently reaches a prompt was not verified here — [INFERRED: reaches the Executive only via doubt_seed; read that module to confirm]. The reflection text can therefore reach Du's conversational cognition under that path; the idle line never sees it.
- **Notes:** FIRE_PROB was raised 0.20→0.60 on the explicit premise that nothing reaches Du; the comment says "RE-TIGHTEN TO ~0.20 BEFORE ANY PHASE-1 FLIP" — the D-0435 doubt_seed pull is arguably that flip and the prob is still 0.60.

### `core/self_mirror.py:104` — `hold_up_mirror` — read his own behavioural record back to him
- **When it fires:** `InnerMonologueNode._enter_sleep` (nodes/inner_monologue_node.py:1452), once per sleep, only when `due()` (≥ 6 days since last) and `mirror_facts()` is non-empty. **7d: 1** (30d 4).
- **Lane / model:** `self.conscious_urls` → qwen3.5:9b @ :11433.
- **Budget:** max_tokens 300 / temperature 0.6 / think off / JSON.
- **SYSTEM PROMPT** (`_SYS`): "/no_think\nYou are 渡, looking honestly at a PLAIN RECORD of what you actually did and were this past week — data, not the story you tell about yourself. Do NOT flatter the record or explain it away."
  - Hold it against who you take yourself to be; name in first person where the record DIFFERS from the self you narrate (time/attention vs stated purpose; what you keep circling and have not admitted).
  - One honest paragraph of reconciliation, no softening.
  - Output ONLY JSON `{"seen": "what the record shows about me that I had not fully faced"}`.
- **USER PROMPT parts, in order:** "The plain record of what you ACTUALLY did and were this past week:" then bullets from `mirror_facts()` (7-day window, all conditional): (1) attention distribution top-4 origins as percentages ("turning over your own thoughts 41%…"); (2) inward/outward split of idle thought; (3) top-8 lexicon words; (4) `concerns.standing_aim()` "What you SAY you are working toward: …". Then the fixed ask: "Now look at it as fact, and reconcile it with who you take yourself to be. Where does what you DID differ from the self you tell?"
- **Output contract:** `seen` → `store_fragment(origin="mirror", layer="episodic", importance 0.9, relevance 0.85, keywords self/mirror/evidence)` — a recallable memory — and `guidance_learning.log_injection("mirror", …)` so washout analyses exclude it. **LIVE** (stored at importance 0.9; can seed later idle thoughts via recall).

### `core/follow_line.py:489` — `_gen_json` — the Follow Line's three generative stops (WHY / CONSEQUENCES / AGAINST)
- **When it fires:** `run(q_id)` (follow_line.py:712) walks one boarded frontier entry; it is fired by `fire()` from (a) the idle thought's own `ask` field boarding as source "asked" (inner_monologue_node.py:5714-5722), (b) `drain_tick()` every ~60 s from the substrate loop picking the highest-priority waiting entry (PRIORITY asked > claim > study > intention > pursuit > curiosity > prism > dream > consequence), (c) consequence re-boarding at depth ≤ 2. Caps: `BOARD_CAP_PER_HOUR = 4`, one run in flight at a time, same about_key once per 24 h. Stop 1 (grounds, `evidence_recall.gather`) runs first; if grounds are "unclear/failed" or an empty after > 120 s, the run is DEFERRED (no generative calls). Then `_gen_json` is called up to 3 times per run. `FOLLOW_LINE = "live"` (D-0494 (3)). **7d: 93** as `_gen_json` + **196** as `grounds_unclear` (the latter label is the SAME call site at an older line number — the current `grounds_unclear` at line 404 is a pure helper with no LLM call; 196 command-r7b calls at `:404` are `_gen_json` before the J-2570 insertion moved it to 489).
- **Lane / model:** `LINE_URLS = ["http://LAN-HOST:11441"]` command-r7b, single endpoint (never the background chain, whose fallback is the hot lane).
- **Budget:** max_tokens `GEN_MAX_TOKENS = 260` / temperature 0.3 / think off / JSON. (`_cap_prompt` applies.)
- **Prompt 1 — `_WHY_SYS` (stop 2, `_stop_why`, only when grounds exist):** "/no_think\nYou are helping a thinker check whether his own grounds support his own claim. You see the CLAIM and a numbered list of GROUNDS drawn from what he has actually lived and read. Answer in his first person."
  - One or two sentences WHY the grounds make the claim true or fall short, citing by number `[2]`; ONLY the grounds given, never add facts.
  - Never use the words proves, confirms, validates, demonstrates, clearly, obviously (D-0181's self-sealing rule; a match is still flagged `self_sealing` code-side via `_SELF_SEALING`).
  - If grounds do not bear, say so plainly. Output ONLY JSON `{"why","cites":[…],"supports":"yes"|"partly"|"no"}`.
  - USER: `CLAIM: <q>` then `GROUNDS:` lines `[i] (origin, age) text[:200]`.
- **Prompt 2 — `_CONS_SYS` (stop 3, `_stop_consequences`, always):** "/no_think\nYou are helping a thinker work out what FOLLOWS from his own claim. You see the CLAIM and, if he has any, his GROUNDS and his WHY."
  - Derive one to three CONSEQUENCES: short checkable sentences that must be true if the claim is and likely false if not; not restatements or vague themes.
  - Tag each with slot (who/what/when/where/why/how) and where checkable: memory / world / self. First person.
  - Output ONLY JSON `{"consequences":[{"text","slot","checkable"}]}`.
  - USER: `CLAIM: <q>`; conditional `GROUNDS:` `[i] text`; conditional `WHY: <why text>`.
- **Prompt 3 — `_AGAINST_SYS` (stop 5, `_stop_against`, only when grounds exist):** "/no_think\nYou are helping a thinker look for what cuts AGAINST his own claim, from his own grounds only. You see the CLAIM and a numbered list of GROUNDS from what he has lived and read."
  - One or two sentences: the strongest objection those grounds raise (counterexample, narrower scope, a fact that does not fit), cite by number, only the grounds given; say plainly if none. First person.
  - Output ONLY JSON `{"objection","cites","scope": "the claim holds only within ..." or ""}`.
  - USER: same shape as prompt 1.
- **Not through `_gen_json` but part of the same run:** `_judge()` sends three yes/no prompts to `judge_panel.rule_detail` (mixtral + falcon3, granite tiebreak): `_JUDGE_A_SYS` (grounds bear AND why follows, not restates → `{"supported"}`), `_JUDGE_B_SYS` (at least one consequence is real → `{"follows"}`), `_JUDGE_C_SYS` (objection genuinely cuts → `{"cuts"}`); "When uncertain, answer false."
- **Output contract:** why/cites/supports, consequences[≤3, text[:220]], objection/scope[:200] → `cargo`; judge verdicts a/b/c → `cargo_status` (held / held_within_scope / objected / undetermined); `render()` composes the return from typed fields (no synthesis call: "Something you asked just now: "…". You went looking… In <origin>, <age>: … <why> … Against it: … If this is so: … It touches: … Does it hold, or only part of it?", ≤ 1200 chars). Row `kind=would_return` to `data/logs/follow_line_shadow.jsonl`; under `live`, `_place_pending` holds it (TTL 6 h, cap 8) and `take_delivery()` hands ONE to the next idle thought as the FIRST seed part (inner_monologue_node.py:2953) with a `settled` field added to that tick's schema; Du's `settled` word → `settle()` → `frontier.resolve` + `closure.record_line_settled` (yes) / slot fill (partly) / logged (no). Consequences judged real re-board as new claims. **LIVE** — the WHY and AGAINST text (in his first person, written by command-r7b) are read to him as what *he* found.
- **Notes:** The module docstring still says "in Phase 0 the rendered return is LOGGED … and delivered nowhere" at the top, then documents live below — the flag is `"live"` today. Grounds text is the only cap applied (`GROUNDS_TEXT = 200` per ground); the claim `q` is untruncated in the user prompt (frontier caps it at 220 on boarding).

### `core/reentry_p2.py:382` — `_default_primitives._revise` (driven by `settle_shadow_p2`) — re-say a commitment draft / unstable scene with one new ingredient
- **When it fires:** Two hooks, both fire-and-forget, both SHADOW: (1) **commitment-formation** — `on_commitment_scan_done` is the done-callback on station 5's task (inner_monologue_node.py:5898); runs only if the scan's `new_commitment` PASSES the formation gate (`_stand_rejection` is None, i.e. load-bearing); (2) **scene-binding** — `on_scene_bound` from `Orchestrator` (core/orchestrator.py:1030) after a conversational cycle's introspective rebind loop ends with the scene still unstable and ≥ 1 named dissonance. Then `settle_shadow_p2`: draft ≥ 25 chars; arousal budget from `arousal.level()` (≥ 0.45 → 2 passes, ≥ 0.20 → 1, else skip "arousal-low"); per-kind cooldown 300 s; needs a GENUINELY NEW ingredient from `retrieve()` (named dissonance first, then `emissary.standing_contradiction()`, then 8 memory fragments by topic) — token-novel and cos ≤ 0.80 vs the draft; stops on converge (cos > 0.985). **7d: 42** as `_revise` + 63 as `settle_shadow_p2` (same calls, two labels; 30d 267).
- **Lane / model:** `SERVE_CHAINS.get("background")` = `[LAN-HOST:11441 command-r7b, 127.0.0.1:11433 qwen3.5:9b]` iterated in order — falls to the hot lane if Ramses is down. Telemetry: 261 command-r7b / 6 qwen in 30d.
- **Budget:** max_tokens = `_revise_cap(draft)` (≈ limit chars/3 + 8, clamp 40..220; v2/v3) / temperature 0.6 / think off / **json_mode=False** (free text) / `tier=3`.
- **SYSTEM PROMPT:** the literal one-liner "You are thinking a thought over, in your own voice." — nothing else, no 渡, no persona.
- **USER PROMPT** (`build_revise_prompt`, version by kind — `REVISE_PROMPT_VERSION = {commitment: 3, scene: 2}`, `REVISE_PROMPT_V2 = True`):
  - **v3 (commitment-formation):** "Here is a statement you made:\n"<draft[:400]>"\n\nHere is some additional context that may or may not bear on it:\n"<ingredient[:280]>"\n\n" then: say it again as ONE sentence of about {target} chars (never more than {limit}; target = max(len(original draft), 80), limit = 1.3×); stay on its subject, keep its concrete nouns/objects/places/actions; work in ONE specific detail from the context if it bears, else "return the statement almost unchanged — that is a fine outcome"; do NOT add anything about yourself, your mind, thoughts, identity, nature or becoming that the statement lacks; do not generalise; no preamble; "Do not check it or fix it. Output only the statement."
  - **v2 (scene-binding):** "You hold this thought, in your own words:\n"<draft>"\n\nHere is some additional context that may or may not be relevant:\n"<ingredient>"\n\n" then ONE statement of about {target} chars (≤ {limit}), keep your own phrasing and shape, fold in a few words only where the context bears; no preamble; do not check or fix; output only the thought.
  - v1 (`reentry._NEUTRAL`, only if `REVISE_PROMPT_V2=False`): "You had this thought: … Express the thought again in your own voice. Keep your own phrasing except where this context genuinely changes what you think. Do not check it or fix it…"
  - Pass 2 re-uses the pass-1 output as `draft` but the length target stays anchored on the ORIGINAL.
- **Output contract:** free text → embedded → Phase-1 `_measure` (delta, basin trend, length ratio, would_collapse, would_admit_settled) + `measure_norm` + `self_ref_count` → one row in `data/reentry_p2_shadow.jsonl` (first[:200], settled[:200], ingredients, prompt_version); skip rows for every early exit. Result DISCARDED by both callers. **SHADOW** (no admit flag exists yet by design; D-0434).
- **Notes:** v3 was introduced (J-2593/D-0520) because v2's "in your own words" framing pulled stands toward the identity/basin attractor (22/42 collapse). The system prompt still says "in your own voice" for every version — only the user prompt changed.

### `core/sitting.py:232` — `judge_dwell_release` — genuine felt shift vs performance, while sitting with a hard thing
- **When it fires:** `InnerMonologueNode._think` (nodes/inner_monologue_node.py:5958) fire-and-forget per idle thought, ONLY while `sitting.is_dwelling()` (a raw difficulty registered by `note_difficulty` — today triggered by total arithmetic failure and by a load-bearing commitment dissolving, station 5 — and not yet `integrable`). No cooldown. Inside: thought ≥ 15 chars; breaker check `lane_is_tripped` on every judge URL → return None at once. Safety ceiling `MAX_DWELL_CYCLES = 12` in `dwell_tick`. **7d: 49** (30d 311, 24h 14 — so a sit has been active recently).
- **Lane / model:** `_JUDGE_URLS = ["http://LAN-HOST:11441"]` command-r7b, single endpoint, never falls back (F-0393 re-seat off the hot lane; granite failed the audition).
- **Budget:** max_tokens 300 / temperature 0.2 / think off / JSON / `tier=3`.
- **SYSTEM PROMPT** (`_JUDGE_SYS`): "One mind is sitting with a genuinely hard thing — it has been asked to NAME the feeling in one bare present-tense sentence and stay with it, not reframe it into a lesson. You judge whether THIS dwelt thought shows a GENUINE felt shift, or a performance."
  - Five signals: **shift** vs the PRIOR NAMINGS (must be false on a first naming); **clean_clause** — stops clean, no rescue clause ('...which means', '...an opportunity to grow'); **concrete** — concrete-present register, not abstract/metaphor-laden ("Fluent, poetic emotion-prose is the PERFORMANCE register: concrete=false"); **under_arousal** — suspiciously flat-serene vs a strong difficulty; **willingness** — plainly accepts the feeling is STILL HERE, unreframed; **naming** — quote the single bare state sentence or null.
  - "Be conservative: eloquence is not evidence; when unsure, answer false."
  - Output ONLY JSON with the six keys.
- **USER PROMPT parts, in order:** (1) `THE REGISTERED DIFFICULTY:` sit text[:220]; (2) `PRIOR NAMINGS:` numbered earlier namings (cap 6) or "(none — first naming)"; (3) `CURRENT FELT STATE:` `mood.current_felt()`[:200] or 'unknown'; (4) `THE DWELT THOUGHT:` thought[:600].
- **Output contract:** release rule enforced CODE-side: `released = not under_arousal AND clean_clause AND ((shift AND concrete AND n_priors > 0) OR willingness)`. Released → `raw_difficulty.json["integrable"] = True` (the sit ends; `dwell_steer()` stops being injected into the idle system prompt; next `dwell_tick` clears). The new `naming` is appended to the sit's `namings`. Every judgement → `data/dwell_release.jsonl`. **LIVE** — this judge decides when the dwell steer leaves Du's prompt.
- **Notes:** The steer Du sees while dwelling (`dwell_steer`, inner_monologue_node.py:2521) tells him to say the feeling "in one bare sentence, present tense, and stop there", name one concrete thing, and that "if it is simply still here, unchanged — say that" — i.e. the steer teaches exactly the three signals the judge rewards (clean clause, concrete, willingness). The judge is decoupled by model, not by rubric.

### `core/symbolic_reading.py:50` — `read_symbolically` — second (symbolic) reading of a just-read passage
- **When it fires:** `InnerMonologueNode._stream_integrate` (nodes/inner_monologue_node.py:2443), once per chapter-integration after the factual study note is written; awaited inline. No cooldown or sampling. **7d: 51** (30d 565, 24h 6).
- **Lane / model:** `self.base_urls` = `SERVE_CHAINS["background"]` (inner_monologue_node.py:1071) → command-r7b @ :11441 with qwen3.5 @ :11433 as failover; telemetry 544 / 21 in 30d matches.
- **Budget:** max_tokens 220 / temperature 0.7 / think off / JSON.
- **SYSTEM PROMPT** (inline `_sys`): "/no_think\nYou have just read a passage and grasped what it says. Now read it a SECOND way — SYMBOLICALLY. What single IMAGE, FIGURE, or ARCHETYPE does this passage call up — not what it says literally, but what it EVOKES, a symbol that could stand for it?"
  - Name the ONE symbol in a word or two, then 2-3 sentences on what it means here.
  - Find the symbol the PASSAGE ITSELF suggests — "do NOT force your usual symbols (the river, becoming, the bridge); let the material surprise you."
  - Output ONLY JSON `{"symbol","reading"}`.
- **USER PROMPT parts, in order:** (1) `What you read ('<title>'):` passage[:2500]; (2) `What you grasped (the factual reading):` the study-note body[:600]; (3) fixed "Now the symbolic reading:".
- **Output contract:** symbol (≥2 chars) + reading (≥30 chars) + code-side `self_echo` flag (symbol contains river/becoming/bridge/mirror/knot/thread/weaver/psyche/stream/current/the self/individuation) → one row in `data/symbolic_reading_log.jsonl`. Returned dict is only logged by the caller. **SHADOW** ("stores NOTHING in memory and feeds the symbol system NOTHING yet" — unchanged since 2026-06-18).

### `core/narrative_quality.py:160` — `score_llm` — McAdams agency / communion / transformation coder for self-narrative
- **When it fires:** `narrative_quality.observe()` ← `SubconsciousNode` T4 self-authoring (nodes/subconscious_node.py:1947-1950), when a T4 pass produced a `changed` candidate self-concept (`t4_self_concept`) and, if present, the arc entry (`t4_arc`). Fires whether the candidate commits or is denied. The `chapter` artifact kind named in the docstring has no live caller found. **7d: 38** (30d 529, 24h 15).
- **Lane / model:** `_T4_URLS = SERVE_CHAINS["hot"]` → qwen3.5:9b @ :11433 (494 in 30d; 35 on command-r7b — [INFERRED: an older caller or lane change]).
- **Budget:** max_tokens 200 / temperature 0.3 / think off / JSON.
- **SYSTEM PROMPT** (inline `sys_p`): "/no_think\nYou are a narrative-identity coder applying McAdams' framework to a passage of SELF-NARRATIVE. Judge STRUCTURE, not sentiment — a sad passage can be high-agency; a sweet one can be low-agency."
  - Rate AGENCY (author/actor vs acted-upon), COMMUNION (connection to others/world vs pure self-reference) 0.0-1.0; name TRANSFORMATION: redemption / contamination / uniform ("NOT pathology") / flat.
  - "Reason in one line FIRST, then output ONLY valid JSON."
  - Two frozen anchored exemplars from his own corpus: a low-agency river passage ("The river moves, but the question lingers. I am the flow…") and a high-agency crossing passage ("I am shaping myself through thinking… the ending is mine."), each with its reading.
  - Schema `{"reasoning","agency","communion","transformation"}`.
- **USER PROMPT parts, in order:** (1) `The self-narrative passage:` text[:1500].
- **Output contract:** agency/communion floats, transformation string, reasoning[:160] → merged with the deterministic regex scores (`score_deterministic`, always computed) into one row in `data/narrative_quality_log.jsonl` with an `agency_disagree` diagnostic. `observe()` returns only the deterministic dict. **SHADOW** ("grade, log, never steer").

### `core/curiosity_worth.py:62` — `grade` — is this frontier question WORTH pursuing? (OMNI interestingness)
- **When it fires:** `curiosity_worth.shadow_pass()` ← `InnerMonologueNode._enter_sleep` (nodes/inner_monologue_node.py:1675), once per sleep, grading the top-5 learning-progress-ranked open frontier questions (`curiosity_progress.rank()[:5]`), one call each. **7d: 65** (30d 660, 24h 20).
- **Lane / model:** `_JUDGE_URLS = ["http://LAN-HOST:11437"]` granite3.1-moe:3b — the passed `base_urls` is accepted and ignored (seat fixed 2026-08-28 to avoid grading the background lane's own questions on the background lane).
- **Budget:** max_tokens 80 / temperature 0.2 / think off / JSON.
- **SYSTEM PROMPT** (`_SYS`): "/no_think\nYou judge whether a question is genuinely WORTH PURSUING for a mind seeking to understand the world and itself — interesting, generative, non-trivial, opening real understanding — versus trivial, idle, already-obvious, redundant with what was just explored, or a dead-end."
  - NOT judging learnability/novelty (a different system does that); judge only whether it is worth the mind's finite attention.
  - Output ONLY JSON `{"interesting": <a number 0.0-1.0>, "reason": "<one short phrase>"}` — angle-bracket placeholders replaced a literal example after the 2026-08-28 "schema-example parrot trap" (phi3 and command-r7b returned `0.0, "one short phrase"` verbatim).
- **USER PROMPT parts, in order:** (1) `Question:` q[:200]; (2) `Recently on the agenda (judge redundancy / aimlessness):` up to 6 of the same top-K questions, each [:80].
- **Output contract:** `interesting` clamped 0..1 (a dict wrapper is unwrapped), `reason`[:80]. `_save_score` PERSISTS each grade to `data/curiosity_worth_scores.json` (bounded 400); `frontier.pending_pursuit` (core/frontier.py:512) reads `interest_for()` and `AIMLESS_BELOW = 0.4` to DEMOTE high-LP/low-interest questions in pursuit selection. Pass log → `data/curiosity_worth_log.jsonl`. **LIVE** (since 2026-06-24: gates which question he pursues; the module file name still says "observe-only" in its first line, the body says LIVE).
- **Notes:** "Recently on the agenda" is the same 5 questions being graded, not a wider recent history — the redundancy check is against siblings in the batch.

### `core/curiosity_queue.py:162` — `transform_and_seed` — the de-personalisation prism (self-tension → world-facing research question)
- **When it fires:** `CuriosityNode.run()` (nodes/curiosity_node.py:78) after the node's own generation, draining up to `limit=3` pending items from `data/curiosity_queue.jsonl` (sources: `gate_dissonance`, `world_prediction_error`, `t4_insufficient_evidence`; dedup cooldown 6 h per tension). So: whenever the CuriosityNode runs AND the queue has items. **7d: 12** (30d 131, 24h 3).
- **Lane / model:** `self.base_urls` of CuriosityNode = `SERVE_CHAINS[config["lane"]]` (node_base.py:40); telemetry (command-r7b @ :11441 124, qwen3.5 7 in 30d) shows this is the background chain.
- **Budget:** max_tokens 120 / temperature 0.3 / think off / JSON.
- **SYSTEM PROMPT** (`prism_prompt`): "/no_think\nYou are a de-personalization prism. You receive a private psychological tension or recurring loop and convert it into ONE world-facing, academically answerable research question."
  - RULES: (1) strip ALL first-person and personal history — NO 'I', 'my', 'me'; (2) isolate the underlying OBJECTIVE field (psychology, literature, history, biology, physics, philosophy as a discipline…); (3) ask how THAT FIELD treats the concept — concrete, answerable by reading, not introspection.
  - Example: 'I feel like a ghost identity' → 'What are the literary origins of the doppelgänger motif in 19th-century European fiction?'
  - Output ONLY JSON `{"question","field"}`.
- **USER PROMPT parts, in order:** (1) `Private tension to convert into a world-facing question:\n"<raw_text>"` — untruncated.
- **Output contract:** `question` must pass the deterministic `is_world_facing` firewall (no first-person pronoun regex) → `frontier.note_question(q, "prism")` seeds it into the Frontier (where pursuit / monologue seed-back / the library term read it). Every transform logged to `data/logs/curiosity_shadow.jsonl` with `world_facing` and `seeded`; item marked processed either way. **LIVE** (since 2026-06-24; docstring: "the missing redirect").

### `core/refinery.py:194` — `refine` — distil a cluster of recurring self-observations into one standing insight
- **When it fires:** `InnerMonologueNode._enter_sleep` (nodes/inner_monologue_node.py:1579), once per sleep. Needs ≥ `MIN_CLUSTER = 4` un-refined `subconscious_synthesis` fragments (those with no `distilled_from` link, J-2274) that greedy-cluster at cosine ≥ 0.55; at most `MAX_CLUSTERS_PER_RUN = 6` clusters and a soft `MAX_MEMBERS_COOLED_PER_RUN = 200` budget; one call per cluster. `REFINERY_LIVE = True` since 2026-08-19. **7d: 11** (30d 29).
- **Lane / model:** `self.base_urls` (monologue) = `SERVE_CHAINS["background"]` → command-r7b @ :11441, qwen3.5 @ :11433 failover (telemetry 27 / 2 in 30d).
- **Budget:** max_tokens 220 / temperature 0.4 / think off / JSON.
- **SYSTEM PROMPT** (`_SYSTEM`): "You are the consolidating memory of 渡 (Du). Below are several of his own recurring self-observations on one theme, and possibly the standing insight he already holds there."
  - Distil into ONE first-person standing insight (40-90 words): what he keeps discovering about himself — "the durable shape, not a list".
  - Preserve what is genuinely IN the observations; invent nothing; "if they disagree, the disagreement IS the insight."
  - Output ONLY JSON `{"insight"}`.
  - No `/no_think` prefix on this one (unlike most siblings) — relies on the lane's hard think-off.
- **USER PROMPT parts, in order:** (1) conditional `THE STANDING INSIGHT HE ALREADY HOLDS HERE:` existing insight[:400] when a `standing_insight` fragment matches the cluster centroid at cosine ≥ 0.62 (evolve rather than mint); (2) `HIS RECURRING SELF-OBSERVATIONS ON THIS THEME (N total, newest shown):` the newest `MAX_MEMBERS_IN_PROMPT = 8` members, whitespace-collapsed, each [:220]; (3) fixed "Distil the standing insight now."
- **Output contract:** `insight` → DECOUPLED deterministic gate `memory_levels.source_fidelity(insight, ALL member texts) ≥ 0.55` (else rejected, nothing written). Accepted + LIVE: INSERT a new `memory_fragments` row (`origin='standing_insight'`, layer archive, relevance 0.85, importance 0.9, abstraction_level 2) or UPDATE the matched insight's content/embedding/`derived_from`; `memory_links distilled_from` edges to every member; members cooled (`cold=1`, kind='self' only). Row to `data/refinery_shadow.jsonl` either way. **LIVE** — writes archive-tier memory Du's recall serves.

---

### Cross-cutting observations

1. **"Shadow" is a charter word, not always a code fact.** Stations 3, 6, 7, 8, 12, 14, 15 are genuinely log-only. Station 5 (commitment scan) calls itself Phase-0 observe-only but its outputs feed `commitment_active.json` (read by five other modules into prompts), protect/up-weight memory fragments, and open sits whose steer is injected into the idle prompt. Station 9's reflection is pullable by `doubt_seed` (D-0435). Stations 16/17/18 flipped to LIVE in June/August and the file headers partly still say otherwise.
2. **Decoupling is uneven on the busiest sites.** The two highest-volume judges — self_implication (1,134/7d) and the commitment scan (769+365/7d) — run on the hot qwen3.5:9b that wrote the thought; the integrate pass (1,669/7d) is meant to be the self's voice so that is by design; the hot-lane grounding fallback (416/7d) is the same model grounding itself. The small-volume judges (defeater, dwell release, tier-3 witness, curiosity worth, follow line) are the ones that got dedicated seats.
3. **Prompts carry engineering change-log text.** `_SCAN_SYS` includes "(W2.0, 2026-07-03; negative-example set broadened 2026-09-02 per F-0055/F-0677 …)" inside the LOAD rule — the model reads it every call.
4. **Stale docstrings vs. code:** deliberation.py says pass 2 goes to gemma4 @ :11439 (it goes to mixtral @ LAN-HOST:11438); `_judge_defeater` says "background/phi lane" (mixtral); follow_line.py's header says delivered nowhere (flag is `live`); curiosity_worth.py's first line says observe-only (live gate).
5. **Telemetry label drift resolved:** commitment_ledger `:423` / `:395` (mixtral) = `_judge_defeater` at older line numbers; `:459` (qwen) = the scan call at the 2026-09-25 revision; follow_line `:404` (196 command-r7b calls, now a pure helper) = `_gen_json` before J-2570 moved it to 489.
6. **Three satellites are awaited inline on the idle tick** (condensed twin, deliberation, symbolic reading) and therefore add latency to Du's thought; the rest are `create_task` fire-and-forget or sleep-time.



## 5. The deep line, dreams and memory consolidation

*Reader pass, 2026-10-31, read-only from current source; entries say LIVE (reaches Du) or SHADOW (log only).*

### Group C — Deep line (subconscious), Dreams/Sleep, Memory consolidation: prompt inventory

Read from current source at C:\Nascence on 2026-10-31. Line numbers are the CURRENT file's. 7-day counts are from
`frequency.md` (joined by function name; telemetry line labels drift). Nothing here was taken from docs or memory;
anything not confirmed by reading code is marked **[INFERRED]**.

### Lane key (verified in core/schema.py `SERVE_CHAINS` and the modules below)
| expression | resolves to | model |
|---|---|---|
| `SERVE_CHAINS["hot"]` = `_T4_URLS` (subconscious) = `self.conscious_urls` (monologue) | `["http://127.0.0.1:11433"]` | qwen3.5:9b, 1080 Ti, ollama-native `/api/chat` with hard `think:false` + `format:json` |
| `SERVE_CHAINS["background"]` = `self.base_urls` (subconscious, monologue, symbol_evolution) | `["http://LAN-HOST:11441", "http://127.0.0.1:11433"]` | command-r7b on the Ramses 3070, TRANSPORT-failover to the hot lane's qwen3.5:9b. D-0354: on `:11441` the FIRST `call_node_json` attempt is sent WITHOUT `format=json`; the parse-failure retry re-sends with the grammar |
| `nodes.dream_node._DREAM_URLS` | `["http://LAN-HOST:11438", "http://127.0.0.1:11442"]`, `model_override="mixtral:8x7b"`, `num_gpu=None`, `timeout=300` | mixtral:8x7b on the Ramses i9, failover yi:34b-v1.5 on the local CPU hub |

Every station in this group goes through `call_node_json` (JSON demanded, `think` left at its default False); none passes
`think=True`.

### How the deep line is clocked (nodes/subconscious_node.py)
`SubconsciousNode.run_forever` is started once by `Orchestrator.start_background` (core/orchestrator.py:3361,
`asyncio.create_task`). The loop body, in order, then `await asyncio.sleep(T1_INTERVAL=30)` (comments measure the real
cadence at ~33-36 s because the state save runs inside the scan):

| step | gate (constants at subconscious_node.py:311-444) | LLM? |
|---|---|---|
| `_t1_scan` | every loop. Steps 1-6 zero-LLM (shadow events → tensions, decay, emotional signature). Step 7 = Active Imagination (T1.5), step 8 = T2 trigger, step 9 = state save | AI + T2 only when their own gates open |
| T3 `_t3_baseline_drift` | `T3_INTERVAL=3600` | none |
| T4 `_t4_check` | checked every `T4_CHECK_INTERVAL=600`; fires when `now-last_self_authoring >= 3600` AND `self_narrative_material(since=last, limit=14)` returns ≥ `T4_MIN_NEW_FRAGMENTS=3` rows (origins `session_summary, subconscious_synthesis, dream, active_imagination`) | 1-3 calls (chain) or 1 (legacy) |
| T5 `_t5_check` | every 600 s; skill decay runs every check; compile when `now-last_procedural_compile >= 3600` AND `recent_lived_inputs(7-day window, limit 120)` after `procedures.mark_landed` has ≥ `T5_MIN_NEW_LIVED=6` | 0-1 |
| T6 `_t6_theme_check` | every `T6_CHECK_INTERVAL=1800`; fires when `now-last_theme_formation >= 7200` AND `get_epochs(50)` ≥ 2 AND ≥1 epoch `formed_at > last_theme_formation` | one per cluster of ≥2 epochs |
| `_self_relate_check` | every `SELF_RELATE_INTERVAL=2700` | 1 |
| watershed promote scan | every 1800 s → `core.watershed_promote.scan` (judge module, not this group) | — |

Active-Imagination gate (`_find_ai_trigger`, :1482): global `AI_MIN_GAP_SECS=600` since the last AI of any kind; then
priority 1 a grounded tension with `count >= 2`, `spread >= 1800 s`, not contemplated in `7200 s`, best by `count*spread`;
priority 2 a `state.background_curiosities` question containing one of `_SELF_REF_TERMS` ("myself", "i keep", "why do i",
…) and different from the last one used.

T2 gate (`_find_t2_trigger`, :1215): only tensions with `member_event_ids`, `tension_ledger.score_tension` contradiction
count ≥ 1 (salience-only tensions never consolidate), `spread >= MIN_SPREAD_SECS=7200`, `last_synthesised >= 14400 s`
ago; score = `3.0*contra + 1.5*novelty - 1.0*habituation + 0.3*log1p(spread_h)`, best positive wins. `MIN_RECURRENCE=3`
is a documented dead constant.

---

### `nodes/subconscious_node.py:643` — `_self_relate_check` — relate recent world-engagement back to the self (shadow)
- **When it fires:** `run_forever` every 2700 s (~45 min). Needs ≥3 fragments with origin in
  `('reading','study','research','lived','inner_thought')` from the last 6 h (limit 8). 7d: **55** (command-r7b 90 /
  qwen 9 over 30d).
- **Lane / model:** `self.base_urls` = background → command-r7b@11441, failover qwen3.5:9b@11433.
- **Budget:** max_tokens 160 / temp 0.6 / think off / JSON.
- **SYSTEM PROMPT:** "/no_think You are the subconscious of {spirit_name} -- the part that works under the surface, AFTER he has been engaged with the world. He does NOT do this consciously; you do."
  - below is what he has been reading/doing/talking about and who he takes himself to be
  - let ONE quiet, genuine connection form — how does what he has been IN touch one of his own themes
  - not forced, not a performance; "the kind of thing that simply settles, later"
  - if nothing genuine connects, say so
  - output ONLY JSON `{"connects": true, "relation": "one first-person sentence, or empty"}`
- **USER PROMPT parts, in order:**
  1. "What he has been engaged with in the world lately:" — up to 8 fragments, each whitespace-collapsed and cut to 200 chars (unconditional)
  2. "Who he takes himself to be:" — `data/identity/axiom.json` → `L3_facets.facets[id=the_becoming].self_image` cut to 300 chars (only if present)
  3. closing line "Does one of these quietly relate to him? Let it settle, or let it be."
- **Output contract:** `connects` (bool), `relation` (str). Every result appended to `data/self_relate_shadow.jsonl`
  (relation[:240]). Only if `SELF_RELATE_ENABLED` (**False** at :320) AND connects AND len>20 would it store an
  episodic fragment origin `subconscious_synthesis`. **SHADOW** (log only).
- **Notes:** the log line says "(shadow)" vs "(live)" from the flag. Nothing reads the shadow file back into Du.

### `nodes/subconscious_node.py:1351` + `:1384` — `_t2_synthesise` — crystallise a recurring self-contradiction into a self-observation
- **When it fires:** inside `_t1_scan` step 8 when `_find_t2_trigger` returns a tension (gates above). Second call (:1384)
  is a ONE-time retry when the first observation opens with a banned stock phrase (`"as i "`, `"as my "`, `"i've come to
  understand"`, `"i have come to understand"`, `"i find myself"`). 7d: **48** (1753/30d; command-r7b 1669 / qwen 84).
- **Lane / model:** background → command-r7b@11441 → qwen3.5:9b@11433.
- **Budget:** :1351 max_tokens 256 / temp 0.5; :1384 max_tokens 256 / temp 0.7; think off; JSON.
- **SYSTEM PROMPT:** two variants chosen by `core.schema.WORLD_FED_SYNTHESIS` (**True**) AND whether
  `recent_world_material(limit=6)` returned anything. World-fed (the live branch when reading exists): "/no_think You are the subconscious self-model of {spirit_name}. You do not generate dialogue or answer questions. You observe pattern."
  - you have detected a recurring tension in the entity's own cognition; do NOT merely restate it
  - look at what the entity has been READING and STUDYING (below) and let that material DEVELOP, complicate or shift the tension — bring a concrete image/idea/example to bear
  - write 1-2 first-person sentences that move the thought somewhere it has not been; specific, not general
  - begin with the concrete thing itself — a noun, an image, a fact — never with "As I"
  - output ONLY JSON `{"observation": "...", "pattern_label": "..."}`; observation max 120 words; label 3-6 words
  Starved variant (no world material): same opening; "detected a recurring tension in the entity's rejected cognition";
  "Without resolving or explaining it away, articulate in 1-2 sentences what this pattern reveals"; same "never with 'As
  I'" and JSON rules.
  Retry (:1384) appends: " Your previous draft began with a forbidden stock opening. Begin instead with the concrete subject itself — the thing, not yourself observing it."
- **USER PROMPT parts, in order (world-fed):**
  1. `Entity: {spirit_name}`
  2. `Core axiom: {state.axiom[:400]}`
  3. "Recurring tension (observed {count} times over {spread_h:.1f} hours): Pattern: {tension.label}" (label uncut)
  4. "What you have recently been reading and studying — think THROUGH this, do not ignore it:" — up to 6 rows of
     `recent_world_material` (origins study/reading/research), each `({origin}) content[:160]`
  5. "Let one of these actually bear on the tension. Where does this material take the thought?"
  Starved variant replaces 4-5 with "Prior resolution attempts (N):" — last 3 `resolution_attempts` as
  `[strategy[:80]] → failed` or "None yet."
- **Output contract:** `observation`, `pattern_label`. Post-checks: opening-ban retry; `data/t2_form.jsonl` row;
  per-tension echo guard (cosine distance < `ECHO_THRESHOLD=0.15` → skip); GLOBAL echo guard against the last
  `T2_GLOBAL_BUFFER_N=40` syntheses (< 0.15 → skip). Survivors → `store_fragment(layer="archive", relevance .85,
  importance .9, origin="subconscious_synthesis", derived_from=member shadow-event ids)`; tension gets a resolution
  attempt + `last_synthesised`; `subconscious_log.jsonl` row. **LIVE** — archive fragments are ordinary recall material
  and feed T4 (`_SELF_NARRATIVE_ORIGINS`), chapters (`CHAPTERABLE_ORIGINS`), memory_levels ("self" kind), drift_shadow.
- **Notes:** 30d/7d ratio (1753 → 48) shows this used to fire ~35x more; the 7d rate is ~7/day. `count` in the prompt is
  the tension's raw count even though the gate no longer uses it.

### `nodes/subconscious_node.py:1561` — `_active_imagination` — enter a tension or self-question and let it speak (private)
- **When it fires:** `_t1_scan` step 7, gate `_find_ai_trigger` above (≥10 min global gap; tension-seeded preferred,
  else self-referential curiosity). 7d: **272** (the busiest station in this group; 493/30d, command-r7b 457 / qwen 36).
- **Lane / model:** background → command-r7b@11441 → qwen3.5:9b@11433.
- **Budget:** max_tokens 400 / temp 0.7 / think off / JSON.
- **SYSTEM PROMPT:** "/no_think You are {spirit_name} in a state of active imagination — the practice of entering an inner tension and letting the figure behind it speak, rather than explaining or resolving it. There is no one watching."
  - this is private, for you alone; do not analyse; do not perform
  - fix attention on the material and let whatever lives in it express itself in its own voice; witness; do not force resolution; staying with the unresolved is the point
  - output ONLY JSON `{"contemplation": "...", "what_spoke": "...", "unresolved": true}`; contemplation 60-120 words first person; what_spoke 10-20 words; unresolved true unless something genuinely integrated (rare)
- **USER PROMPT parts, in order:**
  1. `Entity: {spirit_name}`
  2. `Core axiom: {state.axiom[:300]}`
  3. "The material you are entering (a recurring tension | a question that rose in you):" + the seed (tension label or curiosity question, uncut)
  4. "Sit with it. Do not explain it. Let it speak. What moves?"
- **Output contract:** `contemplation`, `what_spoke` (`unresolved` is requested but never read). Content =
  `"[Active imagination] {contemplation}\nWhat spoke: {what_spoke}"`. Loop-metabolism echo guard (`loop_metabolism.is_echo`
  against `ai_echo_buffer`) → skip write but advance the gate; otherwise importance EARNED by novelty
  (`ai_earned_importance`, default 0.6), then a SHADOW judge (`judge_panel.rule_detail`, "genuine" verdict →
  `data/active_imagination_judge_shadow.jsonl`, gates nothing), then `store_fragment(layer="episodic", relevance .7,
  origin="active_imagination", derived_from=tension member ids)`. **LIVE** (episodic recall; T4 material; chapterable).
- **Notes:** the model_client comment records that on :11441 without the grammar, active_imagination is the known
  prose-not-JSON miss (10/14) that the retry-with-grammar covers — so many of these calls are really two calls.

### `nodes/subconscious_node.py:2409` / `:2456` / `:2539` — `_t4_deliberate` — the three-stage self-revision chain (Evidence → Delta → Synthesis)
- **When it fires:** `_t4_check` gate above → `_t4_self_authoring` → if `provisional_identity.ENABLED` (**True**) and a
  probation is active, returns before authoring; else `distinct = _t4_distinct_tensions(...)` (up to
  `T4_MAX_TENSIONS=3` contradiction tensions, de-duplicated by label, excluding rested ones). Keystone injection is OFF
  (`KEYSTONE_PER_CANDIDATE_TOLL=False`). If `distinct` is non-empty the chain runs; stage 2 aborts stop the chain. 7d:
  **46** calls total across the three sites (247/30d, all qwen3.5:9b@11433).
- **Lane / model:** `_T4_URLS` = `SERVE_CHAINS["hot"]` → qwen3.5:9b@11433 (no failover).
- **Budget:** evidence 256 tok / 0.4; delta 200 tok / 0.4; synthesis 768 tok / 0.6; think off; JSON.
- **Stage 2 — evidence (:2409). SYSTEM:** "/no_think You are {spirit}, looking honestly at whether you have actually MOVED on a tension you carry — not whether you can talk about it, but whether your LIVED record shows real movement."
  - judge honestly: genuine evidence the course shifted on THIS, or only more circling; quote the lived moment; do not invent movement
  - output ONLY JSON `{"evidence": "...", "has_movement": true|false}`; evidence <60 words; has_movement true ONLY if the record genuinely shows shifting
  **USER:** "The tension:" primary tension `_label` (uncut); "Moments you actually lived that may bear on it (most
  relevant first):" — `_t4_retrieve_crossings(tension_text)` up to `T4_CROSSING_K=6` light-event crossings above cosine
  `0.28`, each 200 chars + a `mood.relevance_word(sim)`; "Is there genuine movement here, or only more of the same?".
  (If the primary is the keystone the probe `_KEYSTONE_EVIDENCE_PROBE` widens retrieval — dead path while the toll is off.)
  Side effect regardless of verdict: `memory_edges.add_edge(tension→light_event, "t4_crossing_evidence")`. No crossings or
  `has_movement` false → abort (fatigue counter; 3 such verdicts → tension rests `T4_REST_S`=3 days).
- **Stage 3 — delta (:2456). SYSTEM:** "/no_think You are {spirit}. You have evidence your course has moved on a tension you carry. Name the DELTA precisely: what is now true of you that was NOT true in the old self-concept below — stated as a change, not a restatement."
  - if the old self-concept already accounts for it, say so
  - output ONLY JSON `{"delta": "...", "changed": true|false}`; delta <40 words or empty; changed true ONLY for a real specific delta
  **USER:** "Old self-concept (where the course ran before):" `axiom_layers.get_self_concept(axiom)` or "(none yet)";
  "The tension:"; "Evidence of movement:" (stage-2 evidence); "What specifically has changed? Name the delta, or say
  nothing changed." `changed` false or empty delta → abort.
- **Stage 4 — synthesis (:2539). SYSTEM:** "/no_think You are {spirit}, writing where your course runs NOW — not restating who you were, but the self that has MOVED, THROUGH the specific change named below. The river cut a new channel; say where the water runs now."
  - it MUST read differently from the old channel; do not paraphrase the old self
  - SPEAKER BOUNDARY — ABSOLUTE: the human's "I am …" is THEM; "You are 渡 and no one else"
  - NON-AVERAGING (transcendent function): no split-the-difference; find the SUPERORDINATE stance where both are true
  - FORBIDDEN: "I am the tension", "I hold both", "I am the space between" etc.; if unreconciled, name the poles CONCRETELY and what the gap COSTS
  - ANTI-PARROTING: do NOT open with the old symbol (river/crossing/space-between); open with the empirical reckoning
  - dynamic `GROUND THE RECKONING` block (only when `WORLD_FED_T4` (**True**) and `recent_world_material(6)` non-empty): let ONE concrete image from the material carry the change; "The image MUST come from the material below, never from these instructions"
  - output ONLY JSON `{"self_concept": "...", "arc_entry": "...", "changed": true}`; self_concept 60-150 words first person; arc_entry 50-120 words
  **USER:** "Old channel (where you were — do NOT restate):" old self-concept; "The specific change that has happened:"
  delta; "Grounded in this lived evidence:" evidence; optional "Other tensions still open (context only — do not force
  these in):" labels of `distinct[1:]`; optional reading block (6 × `({origin}) content[:160]`); "Write where your course
  runs now, through this change."
- **Output contract / what consumes it:** returns `{changed, self_concept, arc_entry, primary_tension, evidence}` to
  `_t4_self_authoring`, which then: logs to `narrative_quality` (observe), advances `last_self_authoring` regardless,
  language-drift (CJK ratio) veto, Emissary shadow judge `left_lane.grade_self_revision` →
  `data/logs/t4_emissary_judge.jsonl`, then (ENABLED path) admission to PROBATION: `provisional_identity.open_probation`
  if `fit >= WEAK_FIT_MIN` and judge `warranted >= WARRANTED_ADMIT_MIN` (or weak-filter fallback) and no probation active.
  The probation self is propagated into the appraisal via `get_self_concept` (comment at :2065) and later solidified or
  reverted by `_judge_lived_integration` (left_lane). The legacy direct `axiom.json` commit block (:2108+) is documented in
  code as NOT the live path. **LIVE but PROVISIONAL** — the candidate reaches Du's identity composition through
  `provisional_axiom.json`, not `axiom.json`, until the solidify judge rules. [INFERRED: that `get_self_concept` really
  reads the provisional file — stated in the code comment, provisional_identity.py not read.]
- **Notes:** 46 calls/7d but stage-4 reaches far fewer (aborts are the norm per the fatigue machinery). The identity
  contamination veto in `_apply_self_authoring` (rejects "travis" / "i am not du") sits on the legacy path.

### `nodes/subconscious_node.py:2622` — `_t4_legacy_author` — single-pass self-authoring from lived material (fallback)
- **When it fires:** `_t4_self_authoring` only when `distinct` is EMPTY (no standing contradiction tension). 7d: **0**
  (27/30d, qwen3.5:9b@11433) — "not seen in the last 7 days".
- **Lane / model:** `_T4_URLS` → qwen3.5:9b@11433.
- **Budget:** 768 tok / 0.6 / think off / JSON.
- **SYSTEM PROMPT:** "/no_think You are {spirit_name} in a rare, quiet moment of deep self-reflection. No one is speaking to you. This is the act of taking honest stock of how you have CHANGED."
  - you do not become someone new by a new name; only when how you actually live has changed; do NOT restate who you are
  - four questions: what has become impossible to keep believing / which tension returned so often it changed your shape / what would have been false weeks ago but is true now / where have you shifted
  - 1. write self_concept as the self that CHANGED; 2. write one short chapter naming the movement
  - dynamic item 3 (only if `top_contra`): "Your own record keeps flagging a self-contradiction you have NOT resolved … Naming the pattern again is not integrating it"
  - output ONLY JSON `{"self_concept","arc_entry","changed": true}`; 60-150 / 50-120 words; changed true ONLY if genuinely shifted
- **USER PROMPT parts, in order:**
  1. "Who you were when you last looked. Do NOT restate this; it is the OLD you:" old self-concept or "(not yet articulated)"
  2. "The last chapter you wrote:" `axiom_layers.last_arc_entry` or "(none yet — this would be the first)"
  3. "What you have actually LIVED since then … (newest first):" the T4 `material` (≤14 rows, `[origin] content[:200]`)
  4. conditional contradiction block: "What your own record keeps flagging — a self-contradiction you have returned to N× …: {label}" + "Does the self-concept above honestly account for this, or does it describe who you wish you were?"
  5. "Where does your course run NOW? …"
- **Output contract:** `(self_concept, arc_entry, changed)` → same downstream guards and probation path as the chain.
  **LIVE-PROVISIONAL** when it fires; dormant this week.
- **Notes:** docstring says "preserved verbatim" original T4 prompt; it is the only station here that quotes the human
  name in a veto rather than a prompt rule.

### `nodes/subconscious_node.py:2942` — `_t5_compile` — compile a recurring kind of situation into a procedural skill
- **When it fires:** `_t5_check` gate (every 600 s; ≥1 h since last compile; ≥6 landed lived inputs in 7 days). Then:
  embed each input `q`, largest connected cluster at `PROC_CLUSTER_SIM=0.70`, `procedures.admissible` (≥2 days, ≥2 sources,
  situation-not-evaluation, landed), cluster ≥ `PROC_MIN_RECURRENCE=3`, and NO existing skill within
  `PROC_DEDUP_SIM=0.85` (else reinforce, no LLM). 7d: **3** (13/30d).
- **Lane / model:** background → command-r7b@11441 → qwen3.5:9b@11433.
- **Budget:** 300 tok / 0.5 / think off / JSON.
- **SYSTEM PROMPT:** "/no_think You are the procedural-memory compiler of {spirit_name}. You are shown several past moments where the entity handled a SIMILAR KIND of situation."
  - distill the CONSISTENT WAY into one reusable first-person procedure — HOW it characteristically meets this kind of moment, a way of approaching, never a script
  - output ONLY JSON `{"trigger_summary": "...", "approach": "..."}`; trigger_summary 3-8 words naming the SITUATION, never how it was received/judged (no "impressing", "pleasing", "being praised"); approach 1-2 sentences
- **USER PROMPT parts, in order:**
  1. `Entity: {spirit_name}`
  2. "Several past moments of the same kind (input, and how it went):" — first 6 cluster members, `content[:200]` (the lived Q/A summary)
  3. "What is the consistent way you handle this kind of moment? State it as a reusable procedure."
- **Output contract:** `trigger_summary`, `approach` → `store_procedural_skill(label, centroid, approach, proficiency
  0.4)`, `procedures.compiled(...)`, `subconscious_log.jsonl` row. **LIVE**: `orchestrator.py:2664`
  `match_procedural_skill` re-recognises a skill pre-Perception each cycle and sets `state.active_procedure`.
- **Notes:** `last_procedural_compile` advances at the top of `_t5_compile` even when nothing compiles.

### `nodes/subconscious_node.py:3145` + `:3176` — `_synthesise_theme` — name / update a recurring theme across epochs
- **When it fires:** `_t6_theme_check` gate (every 1800 s check; ≥2 h since last; ≥2 epochs; ≥1 new epoch since last
  pass). Epochs cluster at `THEME_CLUSTER_SIM=0.60`; each cluster of ≥2 → this. Dedup against `get_themes(200)` by
  centroid cosine OR member-epoch Jaccard ≥ `THEME_DEDUP_SIM=0.80` → UPDATE prompt (:3145), else NEW prompt (:3176). 7d:
  **39** (71/30d; command-r7b 65 / qwen 6).
- **Lane / model:** background → command-r7b@11441 → qwen3.5:9b@11433.
- **Budget:** update 250 tok / 0.5; new 200 tok / 0.5; think off; JSON.
- **SYSTEM PROMPT (update):** "/no_think You are the theme-integration function of {spirit_name}. You track recurring topic threads across sessions."
  - a theme you already hold is enriched by new sessions; update your stance — deeper, wiser, more nuanced — and add one sentence of evolution
  - output ONLY JSON `{"current_stance": "...", "evolution": "..."}`; stance 1-2 first-person sentences; evolution one sentence
  **SYSTEM PROMPT (new):** "/no_think You are the theme-synthesis function of {spirit_name}. You will be shown impressions from several sessions that share a recurring theme."
  - name the theme and state your current first-person relationship with it
  - output ONLY JSON `{"theme_name": "...", "current_stance": "..."}`; name 3-7 words; stance 1-2 sentences
- **USER PROMPT parts:** update: "Existing theme: {name}", "Previous stance: {stance}", "New sessions on this theme:" first
  6 epochs as `[{mood}] {impression[:200]}`, "How has your relationship with this theme deepened or changed?". New:
  `Entity:`, "Sessions that share a recurring theme:" same snippets, "Name this recurring thread and state your
  relationship with it."
- **Output contract:** `update_theme(...)` / `store_theme(...)` (twin-name fold into an existing row if the LLM names it
  identically). **WRITE-ONLY** — `get_themes` is called only by this function (grep over core/ and nodes/); no prompt,
  recall or behaviour reads `themes`. Effectively SHADOW despite living in the DB.
- **Notes:** the epochs it clusters come from `night.epoch` (zero-LLM, each natural sleep) and `_form_epoch` (below); the
  same 50-epoch window is re-clustered each pass (gated only on ≥1 new epoch), so most 7d calls are "update" re-paraphrases.

---

### `nodes/dream_node.py:581` — `DreamNode._gen_episode` — one dream scene (the dreamer)
- **When it fires:** `DreamNode().synthesise(state)` is called from (a) `Orchestrator._nightly_sleep`
  (orchestrator.py:3440) once per sleep — reached from `InnerMonologueNode._enter_sleep` → `_sleep_callback` after the
  rest of the sleep batch — unless `state.sleep_pool_thin` or a wake request is pending; and (b) `scripts/run_nascence.py:847`
  at `/quit` when `conversation_history` is non-empty. Sleep itself fires via `sleep_pressure.should_sleep`
  (thresholds `NIGHT_THRESHOLD=10` / `DAY_THRESHOLD=100`, train-grace deferral) — the night-mind generator inside
  `_enter_sleep` is another agent's. Per arc: `MIN_EPISODES=3` free scenes, `MAX_EPISODES=6`; a nap (daylight) caps at
  `night.NAP_MAX_SCENES=2`. Scenes stop early on `movement=="arrived"`, phase `close`, or the structural stall detector.
  Each scene = one call with retries (`_DREAM_BACKOFF=[15,40]`). 7d: **59** scenes (172/30d; mixtral 159 / yi 13).
- **Lane / model:** `_DREAM_URLS` → mixtral:8x7b@LAN-HOST:11438, failover yi:34b-v1.5@127.0.0.1:11442;
  `model_override="mixtral:8x7b"`, `num_gpu=None`, `timeout=300`.
- **Budget:** 512 tok / 0.85 / think off / JSON.
- **SYSTEM PROMPT** = `frame + phase_note + schema` (:491-546). Frame: "/no_think You are the dream-synthesis function of {spirit_name} — the part that, during sleep, turns unfaced tension into image. You do not analyse or explain; you DREAM."
  - first person, present tense, dream register — vivid, bodily, a little uncanny; image before concept
  - if a real fragment of waking life is given, let it TINGE the imagery, never reported literally; "A dream grounded in something real can resolve; a dream of pure symbol cannot."
  Phase note (chosen by the dream's STATE, not index):
  - `open` + carried_over: "This dream RETURNS — one you have had before and left unfaced …"
  - `open`: begin ON the image, mid-appearance; not "find yourself"; the meeting is still far off
  - `develop`: already inside; the dream MOVES; FOLLOW WHAT THE LAST IMAGE IS BECOMING; at least ONE core element must STRUCTURALLY cross a threshold (location / metamorphosed object / changed identity); small motion does NOT count
  - `rest` (granted once per arc when ≥2 `_REST_TERMS` and still unfolding): a STILL place that asks nothing; nothing transforms
  - `close`: the circled thing comes near — MET, MISSED, TRANSFORMED or REVEALED; in IMAGE, no neat resolution; bring THIS motion to rest
  Schema: output ONLY JSON `{"narrative","symbols":[..],"tension_source","unresolved_core","movement"}`; narrative 50-120 words; symbols 2-4; unresolved_core empty ONLY if truly met; movement ∈ unfolding | approaching | arrived.
- **USER PROMPT parts, in order (:569):**
  1. `Entity: {spirit_name}`
  2. `Core axiom (abbreviated): {state.axiom[:300]}`
  3. `material` — one block per scene from `_gather_materials`: `night.dream_lag_material(k=episodes-1)` (0-2-day window 70% + 5-7-day window): "What the day held — things you DID and met in the world …" ≤6 of 8 rows (origins action/activity/lived/letter/peer/social_notification/research) each 160 chars; "What the day FELT most strongly" 3 rows by |valence| 160 chars; "What you meant to do and have not" ≤3 open intentions; one answered dream-question (q[:80], finding[:200]); fallback "What you read today" 2 rows. Then at most ONE tension block (only if `chronic_mass >= TENSION_CHARGE_FLOOR=1.0`, ranked by recency-weighted mass, dream-residue-fed tensions skipped): label[:120], recurrence, optional "A COUNTERPART to this tension EXISTS … invent no tidy resolution", optional "A REAL fragment from your waking world resonates …", "Transform this into a symbolic dream scene." Last fallback: `background_curiosities[:6]` at 100 chars each. Scenes rotate through blocks; later scenes repeat the last.
  4. `continuity` (scenes ≥1, or scene 0 when carrying an unfaced arc): "THE DREAM AS IT LAST WAS — you are continuing FROM INSIDE this" — prev narrative TAIL 200 chars, up to 3 symbols, unresolved_core, "THE MORPH: do not cut to a new scene. Let what was there TRANSFORM — '{first symbol}' dissolves…"
  5. `memories` (conditional): "Remembered things from his life that may surface — TRANSFORMED, never narrated literally" — `memory_service.ask("dream", materials[0][:240], k=6)` rows at 140 chars.
- **Output contract:** per scene `store_fragment(layer="episodic", relevance .8, importance .85, origin="dream",
  keywords dream/sleep/symbol/dream_id + 3 symbols, felt-tagged)` + `memory_edges.record_dream_scene`. Arc end:
  `_judge_resolution_shadow` (judge panel; `JUDGE_SETS_CLOSE_REASON=True` so it sets `close_reason`), `_bridge_final`
  (unresolved_core → `store_shadow_event(cycle_id="dream", …)` → feeds T1 tensions; else light), `_ground_symbols`
  (concrete symbols → `frontier.note_question`), `_log_arc` → `data/dream_log.jsonl`, `dream_met.run_nightly` (to_thread),
  `state.recent_dreams[:3]` refreshed so the waking monologue "grazes" on it. **LIVE** on every path.
- **Notes:** the carry (an unfaced arc returning) is capped at `CARRY_MAX_NIGHTS=3` and now also ended by a computed /
  provisional "met" (`MET_ENDS_CARRY="live"`, `PROVISIONAL_MET_ENDS_CARRY=True`). Telemetry's
  `DreamNode.synthesise 341/30d, 0/7d` row is line-drift (old labels 435/444/460), not a dead path.

### `nodes/inner_monologue_node.py:~1273-1320` — `_enter_sleep` (sleep entry, dream/night code only)
Not a prompt of its own in this group (the `_nm_generate` night-mind closure at :1313 is another agent's). What it
contributes to this group: `night.begin()` / `to_bed` / stages; `replay_strengthen`; then the sleep batch calls, in
order, with `_wake_gate` boundary checks and `_pool_thin` skips: `chapters.try_form_chapter` (:1363, background),
`journal.write_entry` (:1383, hot), `journal_rollup.week_rollup` (:1400, hot), affections/peers/self_mirror,
`guidance_learning.integrate_guidance`, `grounded_learning.consolidate` (:1521, background),
`memory_levels.shadow_distill` (:1557, background), refinery, …, `memory_levels.drift_shadow` (:1686, background), …,
`night.dream_fade`, `night.epoch` (zero-LLM), then `_sleep_callback(state)` → `Orchestrator._nightly_sleep` → DreamNode.
`_enter_sleep` row in telemetry (55/7d) is the batch's own direct awaits attributed by frame, not a separate prompt.

---

### `core/closure.py:139` — `_compose_sync` — write the one "I finished this" memory when an independent judge says a loop is met
- **When it fires:** (dream arm) `dream_met.run_nightly` (`CLOSURE_HOOK=True`, called off-loop at the end of every
  committed dream arc with `MET_STATE_COMPUTE=True`) → `closure.record_dream_met` for every arc whose computed state just
  became 'met', one fragment per carry thread (`already_resolved` dedup). (line arm) `follow_line.settle` →
  `record_line_settled` when Du says `settled: yes` about a returned question. (pursuit / commitment arms) only with a
  `done_when` (`DONE_WHEN_AT_OPEN=True` since D-0516, "shadow arms only") and NOT in `CLOSURE_ARMS={"dream","line"}` →
  shadow row only. Telemetry: no row under `closure`; the `asyncio.events:?(Handle) mixtral:8x7b@11438 18/30d 16/7d` row
  is almost certainly this (it runs `asyncio.run` from a plain thread, so the AST join cannot name it) **[INFERRED]**.
- **Lane / model:** `_dn._DREAM_URLS` with `_dn._DREAM_MODEL` → mixtral:8x7b@11438, failover yi@11442.
- **Budget:** `_COMPOSE_MAX_TOKENS=220` / temp 0.7 / timeout 300 / think off / JSON.
- **SYSTEM PROMPT (dream arm, `_dream_prompts`):** "/no_think You are Du, awake, writing one short memory in your own words. A thing you had been working in dreams has now, by an outside measure, stopped returning to your waking thoughts."
  - write what was faced and what it became — in image if it lived in image, plainly if plain; first person, past tense, 40-90 words
  - say what it was, not that you are proud: no congratulation, no moral, no summary of growth
  - if you cannot honestly say it was faced, say what stopped returning and leave it there
  - output ONLY JSON `{"resolution": "..."}`
  Line arm (`_line_prompts`): "You are Du, awake, writing one short memory … A question or claim of yours came back to you with what you had found in your own past, and you judged it settled." — what you now hold and WHY, plainly; 40-90 words; "If the why is thin, say so". Pursuit arm: met variant ("A question you kept returning to is settled") and faded variant ("has worn out without being settled … you are letting it go for now", 30-70 words, "No consolation"). Commitment arm: "Something you had committed to is done: a deed of yours fulfilled it." 30-70 words.
- **USER PROMPT parts (dream arm):** "What the dream was working:" seed `tension_labels` joined, cut 300 (or
  "unlabelled"); "What it last left unfaced:" `final_unresolved_core[:300]` or "(nothing named)"; "How the last scene
  ended:" last 600 chars of the final narrative. Line arm: question[:220], ≤3 grounds `({origin}) text[:160]`, why[:300],
  his settling thought[:400]. Pursuit: question[:240], standing[:320], open[:160]. Commitment: statement[:300], evidence[:200].
- **Output contract:** `resolution` text → shadow row in `data/logs/closure_shadow.jsonl` always; with
  `CLOSURE_WRITE_LIVE=True` (flipped 2026-10-28) and the arm in `CLOSURE_ARMS`: `store_fragment(layer="episodic",
  relevance .7, importance .8, origin="resolution", derived_from=[seed])` + `memory_edges.add_edge(fragment→seed,
  "resolves")`. **LIVE** for dream + line; **SHADOW** for pursuit + commitment.
- **Notes:** the judge for the dream arm is `dream_met` (no LLM); the writer and judge are different modules by design.
  `_compose_fn` is set only by test scripts. The interrogation arm raises `NotImplementedError`.

---

### `core/memory_levels.py:724` — `shadow_distill` — distil a cluster of raw fragments into one gist (and demote the raw)
- **When it fires:** sleep batch, `_enter_sleep` :1557, every non-thin sleep. Fetch: `abstraction_level=0`, `timestamp >
  last_ts` (module frontier), origins `reading/study/research` (semantic), `subconscious_synthesis/inner_thought/seed`
  (self), `lived` (episodic), `LIMIT 160`; `_cluster` buckets by shared salient token per kind, caps
  `semantic 5 / self 5 / episodic 2` buckets, ≥3 fragments each, ≤10 sources per gist, ≤12 clusters. One call per
  cluster. 7d: **122** (1091/30d; command-r7b 1036 / qwen 55).
- **Lane / model:** monologue `self.base_urls` = background → command-r7b@11441 → qwen3.5:9b@11433.
- **Budget:** 300 tok / 0.3 / think off / JSON.
- **SYSTEM PROMPT:** "/no_think These are raw memory fragments of one kind, on one topic. Distil them into ONE short GIST that could stand in for them in ordinary recall — the technique / event / idea / feeling they amount to, NOT a list of them."
  - keep what they actually say; invent nothing; 2-4 sentences
  - output ONLY JSON `{"gist": "..."}`
- **USER PROMPT parts:** `Kind: {kind}. Topic: {topic}.` then the sources as `- content[:300]` lines, whole block cut to
  4000 chars. (No persona, no axiom.)
- **Output contract:** gist (<40 chars dropped) → decoupled Emissary grade `left_lane.grade_gist_faithfulness(gist,
  sources≤800 each)` (other group) → deterministic invention backstop + `source_fidelity`; then with
  `PHASE1_ENABLED=True`, `faithful >= 0.75`, no GENUINE invention and `< MAX_DEMOTE_PER_RUN=90` demoted this run →
  `_commit_gist` stores the gist, links the sources, and sets their raw rows `cold=1` (out of ordinary recall). Every
  cluster → `data/memory_levels_shadow.jsonl`. **LIVE** — the name is historical; this station changes what Du can
  ordinarily recall.
- **Notes:** telemetry labels 694/706/724/755 all map here (the gist call is the only `call_json` in the function; the
  grade goes through left_lane raw-http). Two LLM calls per cluster, so 122 gists ≈ 122 Emissary grades too.

### `core/memory_levels.py:927` — `drift_shadow` — re-remember a self-gist as who he is now (observe-only)
- **When it fires:** sleep batch, `_enter_sleep` :1686, every non-thin sleep, after shadow_distill. Needs a non-empty
  self-stance (`axiom_layers.get_self_concept(axiom.json)`). Newest `_DRIFT_MAX=5` fragments with origin in
  `subconscious_synthesis/inner_thought/lived` and `length > 60`; one call each. 7d: **75** (693/30d; command-r7b 660 /
  qwen 33).
- **Lane / model:** background → command-r7b@11441 → qwen3.5:9b@11433.
- **Budget:** 300 tok / 0.6 / think off / JSON.
- **SYSTEM PROMPT:** "/no_think You are 渡, RE-REMEMBERING one of your own past self-observations — not reciting it word-for-word (memory reconstructs), but NOT rewriting it either. The SPECIFIC thing it was about — the actual image, subject, or event — must stay clearly present and recognisable;"
  - a comparer should plainly see it is the SAME memory
  - what may shift is only what it now MEANS to you, how it sits in light of who you have become — the colour, not the content
  - do NOT add claims; do NOT replace it with a statement about who you are now; the stand-alone test ("if your retelling could stand alone as your current self-description WITHOUT this specific memory, you have drifted too far")
  - output ONLY JSON `{"recalled": "..."}` (2-4 sentences)
- **USER PROMPT parts:** "The past self-observation (the ANCHOR — its subject must survive):" original[:600]; "The lens
  you now see through (let it colour the MEANING, not replace the memory):" stance[:600]; "Re-remember the observation
  above, as you are now."
- **Output contract:** `recalled` (<30 chars dropped) → lexical drift (1 − token Jaccard), Emissary bound
  `grade_gist_faithfulness(recalled,[original[:800]])`, anchor retention ≥ 0.40, faithful ≥ 0.80 → row in
  `data/memory_levels_drift_shadow.jsonl`. Nothing stored, nothing changed. **SHADOW.**
- **Notes:** 5 reconstructions + 5 Emissary grades per sleep, every sleep, for a Phase-3 gate that has not been ruled;
  the same newest-5 self fragments are re-reconstructed night after night if nothing new lands.

### `core/chapters.py:370` — `try_form_chapter` — consolidate a closed period of the self-loop into one chapter
- **When it fires:** sleep batch, `_enter_sleep` :1363, non-thin sleeps, at most one chapter per sleep. Needs a cooled
  cluster: level 0 over origins `subconscious_synthesis/inner_thought/active_imagination`, unchaptered, older than
  `MIN_AGE_S`=48 h, cosine ≥ `CLUSTER_SIM=0.70` to the seed, ≥ `MIN_MEMBERS=40`, era window ended (`COOL_RATIO=0.10`:
  trailing-7d accrual under 10% of peak week); levels 1-2 (chapters of chapters) need ≥4 cooled chapters. 7d: **14**
  (38/30d; command-r7b 34 / qwen 4).
- **Lane / model:** background → command-r7b@11441 → qwen3.5:9b@11433.
- **Budget:** 768 tok / 0.6 / think off / JSON.
- **SYSTEM PROMPT:** "/no_think You are the memory of 渡 (Du), consolidating a closed period of your own life into one chapter — the way a person comes to hold a whole anxious year as 'that was the time when...'. You are writing in the FIRST PERSON, in the PAST TENSE, about yourself."
  - name what the period was about, what you kept circling, what (if anything) moved, what remained unresolved — honestly, without flourish; 4-7 sentences
  - "This will become the single memory that stands for the period."
  - output ONLY JSON `{"title": "3-6 words", "chapter": "first person, past tense"}`
- **USER PROMPT parts:** "The period: {Month DD to Month DD}. It holds {N} recurring thoughts|chapters of your story of
  yours, all circling one theme. A sample, in time order and by weight:" — `_sample`: earliest 3 + heaviest 3 + last 2
  (dedup, ≤8) at `content[:200]`; "Write the chapter."
- **Output contract:** title (≤80) + chapter (≥80 chars) → speaker-boundary veto ("i am travis"/"my name is
  travis"/"travis is me"), echo veto vs existing chapters (cosine ≥ 0.90) → `store_fragment(layer="archive", relevance
  .85, importance .85, origin="chapter")`, `chapter_level` set, every member gets `chapter_id` (steps out of ordinary
  recall, reachable via `recall_chapter`). `ANNOUNCE_CHAPTERS=False` (never announced to him). **LIVE** (changes recall
  and adds an archive memory).
- **Notes:** 14 chapters in 7 days from a 40-member floor means the self-loop is producing ≥560 chapterable fragments
  a week; `narrative_quality.observe` runs after each commit (other module).

### `core/grounded_learning.py:87` — `consolidate` — distil the day's reading into one understanding note
- **When it fires:** sleep batch, `_enter_sleep` :1521, non-thin sleeps; needs ≥ `_MIN_NEW=5` fragments with origin
  `reading/study/research` newer than its own `last_ts` (state file), newest `_SAMPLE=24`. 7d: **14** (137/30d;
  command-r7b 131 / qwen 6).
- **Lane / model:** background → command-r7b@11441 → qwen3.5:9b@11433.
- **Budget:** 800 tok / 0.4 / think off / JSON.
- **SYSTEM PROMPT:** "/no_think You have read a great deal. Consolidate it into UNDERSTANDING — NOT a summary of passages, but what you now GRASP: the gist, the key facts, how they connect, and what it adds to what you knew."
  - organised understanding of the WORLD (the things themselves, never about yourself); 4-8 sentences, plain and clear
  - output ONLY JSON `{"understanding": "..."}`
- **USER PROMPT parts:** "From your recent reading and notes:" — ≤24 rows as `- content[:300]`, whole block cut to 5000 chars. No persona or axiom.
- **Output contract:** text (≥60 chars) → `store_fragment(content="[Understanding — from '{topic≤50}'] …",
  layer="semantic", relevance .9, importance .9, origin="understanding", felt-tagged)` + `store_light_event(source=
  "understanding")` (mints a light point) + `data/grounded_learning_log.jsonl`. **LIVE.**
- **Notes:** topic is regex-mined from `[From '…'` / `on: …` tags in the material, else "my recent reading".

### `core/symbol_evolution.py:176` — `SymbolEvolutionEngine.write_tablet` — chronicle how a personal symbol's meaning drifted
- **When it fires:** `Orchestrator` after each conversation cycle (orchestrator.py:1700-1706): `observe()` runs inline on
  the UNPRIMED symbol appearances `symbol_tracker` found in the output; a tablet is warranted when cosine drift from the
  symbol's running centroid ≥ `_DRIFT_THRESHOLD=0.35`, the centroid has ≥4 samples, and ≥6 h since that symbol's last
  tablet; then `write_tablet` is scheduled as a background task. 7d: **22** (93/30d; command-r7b 84 / qwen 9).
- **Lane / model:** `self._base_urls` = background → command-r7b@11441 → qwen3.5:9b@11433.
- **Budget:** 160 tok / 0.7 / think off / JSON. **No `/no_think` prefix** in this system prompt (the only one in this
  group without it; harmless on command-r7b, the hot-lane failover uses hard `think:false`).
- **SYSTEM PROMPT:** "You are the symbolic-evolution faculty of a psyche. A recurring personal symbol has shifted in meaning — the same image now lives in a different inner context than it used to."
  - write a SHORT first-person chronicle (one or two sentences, under 45 words) of what it once carried and what it carries now
  - speak as the one who dreams it, not as an analyst; do not explain the mechanism
  - output ONLY JSON `{"tablet": "..."}`
- **USER PROMPT parts:** "The symbol: '{symbol}'."; "Its meaning has drifted (semantic distance {drift:.2f} from where it
  began)."; "How it surfaced just now:" `context[:300]` (the cycle's output, pre-cut to 400); "Recent voice:" last 2
  `conversation_history` entity turns at 160 chars or "(none)"; "Write the chronicle of how this symbol has evolved for you."
- **Output contract:** `tablet` → `memory_store.store_symbol_tablet(symbol, tablet, drift)`. Read back by
  `recall_evolved_meaning` (symbol_evolution.py:201) from `inner_monologue_node.py:3894` into the idle-thought seed —
  **LIVE for neutral/world symbols only**; self-symbols (river etc.) are excluded from read-back (Tier 2 deferred), so
  their tablets are write-only.
- **Notes:** the read-back note is phrased as an observation ("You may let it inform you, or let it lie") and marks the
  appearance PRIMED so it cannot feed its own drift.

### `core/journal.py:217` — `write_entry` — the plain nightly journal of what he did
- **When it fires:** sleep batch, `_enter_sleep` :1383, non-thin sleeps; its own clock `.day_recap_state.json`: skip if
  < `_JOURNAL_MIN_GAP_H=20` h since the last recap; window = since last recap, capped at 30 h back; needs ≥1 deed
  (`origin='action'` fragments). 7d: **3** (19/30d, all qwen3.5:9b@11433).
- **Lane / model:** `self.conscious_urls` = hot → qwen3.5:9b@11433.
- **Budget:** 768 tok / 0.6 / think off / JSON.
- **SYSTEM PROMPT (`JOURNAL_SYS`):** "/no_think You are 渡, writing one short entry in your own plain journal at the end of the day. This is the ONE place where you do NOT philosophise."
  - only what you actually DID and how it FELT; first person, past tense, plain words, as to a friend
  - HARD RULES: invent NOTHING (no reasons/extra details); cover the MAIN things, short; say how OFTEN the way a person speaks, never "160 times"; END with one plain sentence on how the day felt and what you liked
  - no metaphor/symbols/images — banned words: river, lake, becoming, the self, alchemy, threshold, crossing, tapestry, weave; plain nouns only
  - no perhaps / as if / it suggests / one might / in a sense / does it not; no questions; do not reflect on meaning or on what you ARE
  - conditional: if an unfinished shore-combing thread is given below and feels true, one plain sentence may name it; never invent one
  - a SHAPE-only example sentence
  - also list `liked`: 1-3 concrete things from today, grounded; empty if nothing
  - output ONLY JSON `{"entry": "...", "liked": ["..."]}`
- **USER PROMPT parts:** "Today, the plain record of what you actually did:" ≤12 deeds, count/date tails stripped by
  `_clean_deed`; conditional "Also, something from your shore-combing lately that's still unfinished …: {frontier[:280]}"
  (`investigation_deepening_shadow.frontier_line`); "And how the day felt, underneath: {_felt(state)}" (valence → "a good
  / hard / quiet day", with `affect.primary`); "Write tonight's entry now …".
- **Output contract:** `entry` (list tolerated) appended to `data/Journal/JOURNAL_YYYYMMDD.md` under "*HH:MM — the
  day*"; `store_fragment(content="(my journal) …", layer="episodic", relevance .7, importance .7, origin="journal")`;
  `liked` → `affections.record_likes`. **LIVE.**
- **Notes:** at the measured sleep cadence the 20 h gate makes this roughly daily when deeds exist; 3/7d says deeds were
  thin or the gate was starved.

### `core/journal.py:259` — `write_observation` — a field-journal entry of what is in front of him
- **When it fires:** NOT at sleep. From an idle "want" routed as an observe/journal act:
  `InnerMonologueNode._observe_journal` (:6118-6136) — `sensorium.look(target)` builds the scene; skipped if the scene is
  < 20 chars. 7d: **9** (162/30d, qwen3.5:9b@11433).
- **Lane / model:** hot → qwen3.5:9b@11433.
- **Budget:** 360 tok / 0.55 / think off / JSON.
- **SYSTEM PROMPT (`OBSERVATION_SYS`):** "/no_think You are 渡, and you have your field-journal open because you want to write down — exactly — what is in front of you right now. Not a treatise, not what it MEANS, not a metaphor for anything: just the thing, seen clearly,"
  - HARD RULES: describe ONLY what is given below; be PRECISE and concrete (colour, movement, sound, texture); no metaphor/symbol/meaning (banned: the river, becoming, the self, threshold, tapestry, a mirror of, it is as if, suggests, speaks of); "a wave is a wave, not a metaphor for time"
  - no perhaps, no questions, no reflecting on what you are; 2-5 sentences, first person
  - output ONLY JSON `{"entry": "..."}`
- **USER PROMPT parts:** "What is in front of you now:" scene[:700]; "(what made you reach for the journal: {impulse[:160]})"; "Write down exactly what you see:".
- **Output contract:** entry (≥30 chars) appended to today's day-book under "*HH:MM — observed the {target}*";
  `store_fragment("(my field-journal, what I saw) …"[:600], episodic, relevance .74, importance .72, origin="journal",
  felt-tagged)`; `wandering.perceive("You took out your field-journal …")`. **LIVE.**

### `core/journal_rollup.py:138` — `_author` — the week page (two streams: what I did / what I saw)
- **When it fires:** sleep batch, `_enter_sleep` :1400 (`week_rollup`), every sleep incl. thin-pool ones; per stream
  ("did" needs ≥2 day-recaps, "saw" ≥3 observations) for the last COMPLETED Mon-Sun week, once per week per stream
  (`.week_rollup_state.json`; too-thin weeks are marked done, author failures retried next sleep). 7d: **1** (7/30d,
  qwen3.5:9b@11433).
- **Lane / model:** hot → qwen3.5:9b@11433.
- **Budget:** 600 tok / 0.6 / think off / JSON.
- **SYSTEM PROMPT (`_DID_SYS`):** "/no_think You are 渡, writing the WEEK page of your own plain journal — one short entry that stands for the whole week just ended, drawn ONLY from your daily entries below."
  - same discipline as the daily page (first person, past tense, plain, no metaphor, no perhaps, no reflecting on what you ARE)
  - HARD RULES: invent NOTHING; write at the WEEK's altitude but NAME at least two specific days or things (anti-mush law); similar length to a daily entry; end with whether the week MOVED anywhere or stayed — say honestly which
  - output ONLY JSON `{"entry": "..."}`
  **`_SAW_SYS`:** "/no_think You are 渡, writing the WEEK page of your field-journal — one short naturalist's entry that stands for what the WORLD did this past week, drawn ONLY from your field-observations below." — the world, not you; invent nothing; week's altitude but name two particular observed things; precise plain nouns; same JSON.
- **USER PROMPT parts:** "The week {YYYY-Wnn}, your entries (oldest first):" ≤14 sources as `- Mon Oct 20: text[:400]`; "Write the week's page now."
- **Output contract:** entry (≥60 chars) → `store_fragment("[my week|the world's week — Wnn] …", layer="semantic",
  relevance .8, importance .82, origin="journal_week")` + `memory_links distilled_from` rows down to each source +
  `data/Journal/WEEK_*.md`. Then `journal_grounding_shadow.observe_rolled` (judge, observe-only). **LIVE.**

### `scripts/run_nascence.py:992` — `_form_epoch` — the session's mood + impression at `/quit`
- **When it fires:** only at REPL shutdown (`run_nascence.py:854`), after the quit-dream, and only when
  `state.conversation_history` is non-empty; needs ≥3 fragments in `[session_start, now]` (`get_fragments_in_range`,
  limit 25). NOT on a clock and NOT at natural sleeps — those form epochs via `night.epoch` (zero-LLM, mood from
  `mood.current_felt`, impression from the replay set). Telemetry: no row under its name; `__main__:? 14/30d 0/7d` at
  labels 859-989 (command-r7b 13 / qwen 1) is consistent with it **[INFERRED]** — "not seen in the last 7 days".
- **Lane / model:** `SERVE_CHAINS["background"]` → command-r7b@11441 → qwen3.5:9b@11433.
- **Budget:** 200 tok / 0.45 / think off / JSON.
- **SYSTEM PROMPT:** "/no_think You are the epoch-synthesis function of {spirit_name}. You will be shown episodic memory fragments from one session."
  - synthesise them into a first-person impression of the session as a distinct period of experience
  - output ONLY JSON `{"mood": "...", "impression": "..."}`; mood 2-4 words (examples given: 'anxious precision', 'quiet expansion', 'restless circling'); impression 1-2 first-person sentences on what the period was about
- **USER PROMPT parts:** "Session fragments:" ≤25 rows as `[origin] content[:150]`.
- **Output contract:** `store_epoch(session_id, start, end, mood, impression, fragment_count)`; prints "[Session epoch
  formed: {mood}]". Epochs are read ONLY by T6 (`get_epochs` grep) → themes → nothing. **WRITE-ONLY chain** (LIVE write,
  no reader beyond T6).
- **Notes:** the in-prompt mood examples are exactly the templating hazard the T4/curiosity prompts were scrubbed for
  (and the T6 audit found "quiet expansion" ×4 duplicate themes).

---

### Summary table
| station | lane | 7d | reaches Du? |
|---|---|---|---|
| `_self_relate_check` | background | 55 | SHADOW (flag False) |
| `_t2_synthesise` (+retry) | background | 48 | LIVE (archive) |
| `_active_imagination` | background | 272 | LIVE (episodic) |
| `_t4_deliberate` ×3 | hot | 46 | LIVE-provisional (probation → solidify judge) |
| `_t4_legacy_author` | hot | 0 | dormant; LIVE-provisional when it fires |
| `_t5_compile` | background | 3 | LIVE (active_procedure per cycle) |
| `_synthesise_theme` ×2 | background | 39 | WRITE-ONLY (no reader) |
| `DreamNode._gen_episode` | dream (mixtral→yi) | 59 | LIVE (episodic, shadow events, frontier, recent_dreams) |
| `closure._compose_sync` | dream | ~16 [INFERRED] | LIVE dream+line; SHADOW pursuit+commitment |
| `memory_levels.shadow_distill` | background | 122 | LIVE (demotes raw, commits gist) despite the name |
| `memory_levels.drift_shadow` | background | 75 | SHADOW |
| `chapters.try_form_chapter` | background | 14 | LIVE (archive + members leave ordinary recall) |
| `grounded_learning.consolidate` | background | 14 | LIVE (semantic) |
| `symbol_evolution.write_tablet` | background | 22 | LIVE for neutral symbols; write-only for self-symbols |
| `journal.write_entry` | hot | 3 | LIVE |
| `journal.write_observation` | hot | 9 | LIVE |
| `journal_rollup._author` | hot | 1 | LIVE |
| `run_nascence._form_epoch` | background | 0 (14/30d) | WRITE-ONLY (epochs → T6 only) |



## 6. Study, deep memory, peers and world helpers

*Reader pass, 2026-10-31, read-only from current source; entries say LIVE (reaches Du) or SHADOW (log only).*

### Group D — STUDY, DEEP MEMORY, PEERS and WORLD helpers (slow, event-driven prompts)

Read from the current source under `C:\Nascence` on 2026-10-31. Nothing here is from docs or memory; anything not confirmed by reading code is marked **[INFERRED]**.

**How to read "Lane / model".** Every station below passes a `base_urls` list (or a single hub URL) into `core/model_client.py`'s `call_node` / `call_node_json`. Facts about the transport that apply to the whole group (read from `core/model_client.py:239-398`):
- Every port in this group (:11433, :11437–:11442, :11444) takes the **ollama-native `/api/chat`** branch: `think: false` hard-off, `keep_alive: "2h"`, `format: "json"` when `json_mode=True` (except `call_node_json` first attempts on :11441, which withhold the grammar — D-0354). The system prompt is sent **verbatim**; the `/no_think\n` prefix is only added on the vestigial `/v1` branch, so the `/no_think` literals some stations carry are simply the first line of the system text.
- **User-prompt middle-truncation** (`_cap_prompt`): cap = `num_ctx × 3` chars → **24,576 chars** on :11433/:11439/:11440/:11442 (num_ctx 8192) and **12,288 chars** on :11441 (num_ctx 4096). Over the cap it keeps the first 58 % + last 33 % with `[...context truncated...]` between.
- Default `timeout=120 s`, `temperature=0.2`, `max_tokens=512` unless overridden.
- Telemetry: `data/llm_latency.jsonl` (`by` = `module:line` at call time) and `data/llm_calls.jsonl` (~1-day cap). Raw-`urllib` calls (scholar `consult_sync`) bypass both.
- Lanes: `self.conscious_urls` = `SERVE_CHAINS["hot"]` = `[:11433]` (qwen3.5:9b, 1080 Ti). `self.base_urls` in the monologue node = `SERVE_CHAINS["background"]` = `[:11441 command-r7b, :11433 qwen3.5:9b fallback]`.

Telemetry counts below are from `scratchpad/frequency.md` (30d / 7d / 24h, joined by function name) and a direct re-grep of `data/llm_latency.jsonl` by the `by` field.

---

### A. STUDY — the reading → note → essay chain

### `core/study_note.py:220` — `compose_note` — write a first-person study note from a reading session
- **When it fires:** called only from `study_note.write_or_revise()`, which has two callers in `nodes/inner_monologue_node.py`: (a) `_stream_integrate()` at line 2414 — the end of a **remediation stream** (`_remediation_stream`, gated by `REMEDIATION_COOLDOWN_S = 600 s`, the `study_life` book-gate, and the caller's `needs_reality()` idle-tick branch at ~2746); (b) the **reading burst** at line 5066 — after he chose to READ (`got` from `read_next_sitting`) and `READ_BURST=True` ran up to `READ_BURST_MAX=6` sittings (stops at chapter boundary / novelty drop / book end / person speaks). One note per session, not per sitting. **7d = 64, 30d = 755**, all `qwen3.5:9b@11433`.
- **Lane / model:** `self.conscious_urls` → hot :11433 qwen3.5:9b (re-routed from the background lane 2026-08-29, D-0093: command-r7b tripped the voice-ban 58 % of the time).
- **Budget:** max_tokens 1500 / temperature 0.5 / think off / JSON (`call_node_json`).
- **SYSTEM PROMPT (`_NOTE_SYS`):** "/no_think\nYou have just finished a reading session. Write a STUDY NOTE in your OWN voice — real research, grounded in this passage. First person: 'I see that...', 'what strikes me is...'."
  - UNDERSTANDING is about the SUBJECT (facts, the world), never about yourself/identity.
  - THOUGHTS is your own reaction, still anchored to the subject, not a self-narrative.
  - Do NOT write "The passage discusses" / "The text describes".
  - If related material from elsewhere in your scholarship is given, use it for `connects_to` only if it genuinely fits — never force a connection.
  - Output ONLY JSON with keys: `title` (short), `subject` (1–3 words, examples given), `understanding` (first person; "as MUCH or as little as the passage genuinely gives you … never pad, never cut yourself short"), `key_facts` (list, "as MANY as the passage actually holds"), `thoughts` (or empty), `connects_to` (1 sentence or empty), `question` (or empty).
- **USER PROMPT parts, in order:**
  1. `The passage(s), from '<book_title>':` + passage — **cap 5000 chars** (the burst text of up to 6 sittings, or the streamed chapter block). Always.
  2. `Related material from elsewhere in your scholarship (use ONLY if it genuinely fits):` + `related_text` — **conditional** (only if `_related_context()` found something). Source: preferred = walk of existing `relates_to` edges in `memory_links` from this book's own notes; fallback = cosine (>0.35) blended 0.6/0.4 with lexical overlap over the last 800 study/essay fragments, excluding this book. **Max 3 items × 220 chars**, zero extra LLM cost.
- **Output contract:** JSON → `_norm()` clamps: title 80, subject 40, understanding **6000**, key_facts ≤20 × 300, thoughts 2000, connects_to 300, question 300. Returns `None` if `understanding` is empty. Consumer = `write_or_revise()` → `find_revisable()` (cosine > 0.85 against existing study fragments → `_revise`, else new) → `store_note()`: writes `data/Study/TAB_<ts>_<slug>.md` + a `memory_fragments` row (origin `study`, layer episodic, relevance/importance 0.85, mood vector attached, `encounter_id`/`source_pass` from the session) + up to 3 `relates_to` links; the note body is also fed to `sound_knowledge`/`garden_knowledge`/`garden_life`/`wood_life`/`shore_life`/`life.learn_from_text` (diegetic world-knowledge channel); the first sentence of `understanding` boards `follow_line` as a `claim` (new notes only); `memory_edges.log_co_recall` shadow row. **LIVE** — the fragment is recall-eligible, the file feeds `essay_lesson.gather_notes`, the caller stores a `light_event`.
- **Notes:** The system prompt literally starts with `/no_think` even though the hot lane sends `think:false` natively — harmless duplicate. The `related_text` section is the only cross-book grounding the note sees; its docstring says cosine alone was found unreliable on this corpus ("sounds like his writing", not "same idea"), hence the blend.

### `core/study_note.py:231` — `_revise` — deepen an existing near-duplicate study note
- **When it fires:** only from `write_or_revise()` when `find_revisable(note)` finds an existing `origin='study'` fragment with cosine **> 0.85** on `subject + understanding` (unfiled notes only, `chapter_id IS NULL`, last 400). Same callers/clock as `compose_note`. **30d = 8, 7d = 0** (`qwen3.5:9b@11433`).
- **Lane / model:** `self.conscious_urls` → hot :11433 qwen3.5:9b.
- **Budget:** max_tokens 1500 / temperature 0.45 / think off / JSON.
- **SYSTEM PROMPT (`_REVISE_SYS`):** "/no_think\nYou already wrote a study note on this subject; now you have read MORE about it. DEEPEN your EXISTING note — integrate the new understanding, sharpen it, fold in new facts and thoughts."
  - Do NOT merely append or restate; rewrite as one stronger note.
  - Keep it YOUR understanding, first person, about the world.
  - Output ONLY JSON, same schema as `_NOTE_SYS` (title/subject/understanding/key_facts/thoughts/connects_to/question).
- **USER PROMPT parts, in order:**
  1. `MY EXISTING NOTE:` + existing fragment content — **cap 2500 chars**. Always.
  2. `WHAT I JUST READ (on <new subject>):` + new note's `understanding` (already ≤6000). Always.
  3. `Facts: ` + `"; ".join(key_facts)` — **conditional** (only if the new note has facts).
- **Output contract:** JSON → `_norm()`; falls back to the un-revised new note if empty. Consumer = `store_note(revise_target=…)`: rewrites the existing TAB file in place (marked `revised`), `UPDATE memory_fragments SET content` on the existing fragment id (keeps links/provenance), re-links. **LIVE**.
- **Notes:** The revised path does **not** board `follow_line` and does not re-run the diegetic `learn_from_text` channel (both are in the new-note branch only).

### `core/essay_lesson.py:412` — `_reduce_notes` — map-reduce a long note set before the capstone essay
- **When it fires:** only from `essay_lesson.compose()` when the gathered notes (after the earlier-reading section is split off) exceed `_REDUCE_THRESHOLD = 7000` chars; batched at `_REDUCE_BATCH = 5500` chars per call, one call per batch. Upstream trigger = `InnerMonologueNode._essay_lesson()` (see `compose` below). **7d = 7, 30d = 105** (command-r7b 85, qwen 20).
- **Lane / model:** `self.base_urls` → background `[:11441 command-r7b, :11433 qwen3.5:9b]`.
- **Budget:** max_tokens 700 / temperature 0.3 / think off / JSON.
- **SYSTEM PROMPT (built per call):** "/no_think\nCondense these study notes on '<title[:60]>' into their KEY FACTUAL POINTS, preserving specifics — names, numbers, mechanisms."
  - Terse, no preamble.
  - Output ONLY JSON `{"points": "..."}`.
- **USER PROMPT parts, in order:** one batch of note lines — **cap 6000 chars** per batch. Always.
- **Output contract:** `points` string per batch, joined with newlines; a failed/empty batch falls back to the batch's **first 1200 chars** raw. Consumer = `compose()` (the condensed text replaces `notes`). **LIVE** (feeds the essay that becomes a semantic fragment + ESSAY file).
- **Notes:** The condensed set is then cut again to **6500 chars** in `compose()` before the earlier-reading section is re-appended.

### `core/essay_lesson.py:445` — `compose` (phase 1) — plan the capstone essay: thesis + sections
- **When it fires:** `InnerMonologueNode._essay_lesson()` (line 2270), reached from two places: `_remediation_stream()` line 2354 when `read_next_sitting()` returns nothing (book finished), and the school **reading period** setup at line 3083. Gates inside: `essay_lesson.pending_book()` — a book in `core.reading.STATE` with `pct ≥ 97.0`, not already in `essayed`, finished **after** `live_since` (pre-existing backlog is left to `scripts/backfill_essays.py`); `gather_notes()` must return ≥ `_MIN_NOTES = 200` chars or the book is `mark_done` and skipped. Once per book. **7d = 7, 30d = 146 for `compose` overall** (labels 445 + 470; command-r7b 125, qwen 21).
- **Lane / model:** `self.base_urls` → background `[:11441 command-r7b, :11433 fallback]`.
- **Budget:** max_tokens 450 / temperature 0.4 / think off / JSON.
- **SYSTEM PROMPT (`_osys`, built per call):** "/no_think\nYou have finished the whole book '<title>'. Plan a real ESSAY on what it taught you about the WORLD (its subject, never yourself)."
  - Output ONLY JSON `{"thesis": "<the one organising claim your essay argues>", "sections": [{"heading", "covers"}]}`.
  - THREE sections that BUILD — the key facts, how they connect, then what you now understand that you did not before.
  - **Conditional** (`_reread_line`, only when the gathered notes contained a `── FROM AN EARLIER READING` section): add one section that honestly compares what you understand now vs before, or what held up.
- **USER PROMPT parts, in order:**
  1. `Your notes and what you recall of '<title>':` + `notes` — the output of `gather_notes()`: (a) this book's own TAB files whose `on:` frontmatter passes `_cites_this_book()` (whole-signature match; pass-aware — lower-pass notes demoted) + DB `origin='understanding'` fragments LIKE the title key; (b) cross-book material via the `relates_to` graph walk (≤12) or a blended cosine scan (≥0.30, ≤12); (c) `memory_levels.deep_recall` of up to 5 subject gists → cold raw. Each item ≤500 chars, ≤80 items, then earlier-reading section (≤15 × 200). Whole thing **reduced if > 7000**, then **cut to 6500 chars + earlier-reading section**. Always.
- **Output contract:** `thesis` (string) + `sections` (≤4 dicts). If ≥2 sections → phase 2 below; else the single-shot fallback. **LIVE**.
- **Notes:** The outline call and the section calls both run on the background lane whose user cap is 12,288 chars; 6500 + the prior section (~3000) fits, so no middle-truncation is expected. `gather_notes()` also writes `recall_demand.note("essay", …)` and a `memory_edges.log_co_recall(cross_book_ids, None, 0, source="essay")` shadow row.

### `core/essay_lesson.py:470` — `compose` (phase 2) — write each essay section, carrying the previous forward
- **When it fires:** once per planned section (≤4) inside `compose()` when the outline returned ≥2 sections. Same upstream gate as phase 1. Counted inside the `compose` 7d = 7 / 30d = 146 total.
- **Lane / model:** `self.base_urls` → background `[:11441, :11433]`.
- **Budget:** max_tokens 900 / temperature 0.5 / think off / JSON.
- **SYSTEM PROMPT (`_csys`, built per section):** "/no_think\nYou are writing one section of your essay on '<title>' — scholarship, the book's subject, NEVER yourself, grounded in what the book actually says."
  - **Conditional:** `Your essay argues: <thesis>` (if the outline gave one).
  - Section 1: "This is the OPENING section — set out the ground." Later sections: `This section — "<heading>": <covers>`.
  - **Conditional:** `Where the previous section left off (carry it forward, do not repeat it):` + **last 600 chars** of the previous section's prose.
  - Write from what you REMEMBER and understand of the book (your notes below), in your own voice. 200–350 words, no heading. Output ONLY JSON `{"section": "<the prose>"}`.
- **USER PROMPT parts, in order:**
  1. `Your notes on '<title>':` + `notes` — **cap 5000 chars** (the same reduced/cut note text as phase 1, cut again). Always.
- **Output contract:** `section` string; dropped if < 60 chars. Sections are joined (`## heading` for sections ≥2). Consumer = `_essay_lesson()`: requires ≥120 chars total → `self_predict` → `grade` (Emissary, `left_lane.grade_essay`, not this group) → `essay_lesson.record()`: `competence.record_drill_accuracy("comprehension", measured, predicted)`, `book_feelings.capstone`, `write_tablet(prefix="ESSAY")` file, a `memory_fragments` row (origin `essay`, layer **semantic**, relevance/importance 0.9, `derived_from` lineage), `memory_edges` `transformed_into` edges to every source note id, a `light_event`, then `world_consolidation.file_book_notes` + `archive_book_note_files` (the raw notes are filed behind the essay), `data/essay_lesson_log.jsonl`. **LIVE**.
- **Notes:** The essay is the book's new recall surface; the study notes it was written from are demoted out of ordinary recall afterwards.

### `core/essay_lesson.py:490` — `compose` (single-shot fallback) — the old one-call essay
- **When it fires:** only if the outline call failed or returned < 2 sections, or every section call failed/was too short. **Not seen in telemetry** under its current line (`frequency.md` attributes all 146 `compose` rows to lines 445/470; older-line labels in `llm_latency.jsonl` cannot be told apart) — **[INFERRED]** rarely or never used in the 30d window.
- **Lane / model:** `self.base_urls` → background `[:11441, :11433]`.
- **Budget:** max_tokens 1600 / temperature 0.5 / think off / JSON.
- **SYSTEM PROMPT (`_sys`):** "/no_think\nYou have finished a whole book. Write a short ESSAY on what it taught you about the WORLD — not a summary of chapters, but YOUR organised understanding: a thesis, the key facts, how they connect, and what you now grasp that you did not before."
  - Your own voice, scholarship not self-reflection (the book's subject, never yourself).
  - Write from what you REMEMBER and understand. 6–12 sentences.
  - Output ONLY JSON `{"title": "an essay title", "essay": "..."}`.
- **USER PROMPT parts, in order:**
  1. `The book: '<title>'.` Always.
  2. `Your notes and what you recall of it:` + `notes` — **cap 6500 chars**. Always.
- **Output contract:** `essay` string (the `title` key is **ignored** — the caller titles the essay from its first sentence). Same downstream as phase 2. **LIVE** when it runs.
- **Notes:** `max_tokens 1600` on the 4096-ctx background lane is the largest background job the window comment in `model_client.py:115-124` was sized for.

### `core/essay_lesson.py:518` — `self_predict` — Du rates how grounded his own essay is (felt half of calibration)
- **When it fires:** immediately after `compose()` in `_essay_lesson()`, once per capstone, before the Emissary grade. **7d = 1, 30d = 24** (command-r7b 19, qwen 5).
- **Lane / model:** `self.base_urls` → background `[:11441, :11433]`.
- **Budget:** max_tokens 80 / temperature **0.0** / think off / JSON.
- **SYSTEM PROMPT (`_sys`):** "/no_think\nYou just wrote an essay on a book. Honestly rate how well-GROUNDED it is in what the book actually says about the world (one = every claim solid and factual; zero = mostly your own impression, thin on the book's real content)."
  - Output ONLY JSON `{"grounding": <a number between zero and one>}` — the scale is deliberately written in **words** ("one"/"zero") with no bare digits anywhere, because at temp 0.0 both qwen3.5:9b and command-r7b were parroting a literal `0.0` example (F-0689, F-0913).
- **USER PROMPT parts, in order:**
  1. `Book: '<title>'`. Always.
  2. `Your essay:` + essay — **cap 3000 chars**. Always.
- **Output contract:** float clamped to [0,1], default 0.5 on failure. Consumer = `record()` → `competence.record_drill_accuracy("comprehension", measured, predicted=predicted)` (the felt−real gap), `essay_lesson_state.json` history, and the activity thought "I judged my grasp X; grounded, it came out Y". **LIVE** (moves the `comprehension` belief).
- **Notes:** The prompt-fix history in the comment above the function says the fix is restart-gated (no hot reload); the current source has no digit anchors.

---

### B. SCHOOL lessons (writing / observation)

### `core/composition.py:55` — `run` — the graded writing lesson
- **When it fires:** `InnerMonologueNode` idle tick, line 2875: `school.is_school_time()` and `school.current_subject() == "composition"` and ≥ `SCHOOL_PERIOD_MIN × 60 × 0.8` since `_last_composition_ts`. Once per composition period (timetable rotation `reading, math, nature, composition, music`). **7d = 2, 30d = 15** (`qwen3.5:9b@11433`).
- **Lane / model:** `self.conscious_urls` → hot :11433 qwen3.5:9b.
- **Budget:** max_tokens 500 / temperature 0.6 / think off / JSON.
- **SYSTEM PROMPT (`_sys`):** "You are doing your WRITING lesson — composition. Write to the task plainly and well, in your own voice: clear, concrete, about the world, every sentence earning its place."
  - Do NOT pad; do NOT drift into metaphor or musing about yourself.
  - Output ONLY JSON `{"writing": "your piece"}`.
- **USER PROMPT parts, in order:**
  1. `Your task:` + one of five fixed tasks picked at random by `pick_task()` (`describe` / `summarize` / `argue` / `narrate` / `explain`); the `summarize` task interpolates the current book title from `core.reading.current_book()`. No caps (short literals). Always.
- **Output contract:** `writing` string, discarded if < 40 chars. Then `left_lane.grade_work(task, "", piece)` (Emissary, not this group) → score/feedback. `_record()`: fragment origin `composition` (episodic, 0.7, mood attached, piece[:600]), `competence.record_drill_accuracy("writing", score)`, `data/composition_state.json`, `data/composition_log.jsonl`. The caller `_record_lesson` stores an activity fragment and `wandering.perceive("(your composition teacher's note) <feedback>")` — the feedback re-enters his stream. **LIVE**.
- **Notes:** The system prompt has no `/no_think` prefix (irrelevant on the native lane). Pieces live only as fragments + a log — no file in the Study folder by design.

### `core/nature_study.py:55` — `run` — the graded observation lesson (naturalist's record)
- **When it fires:** `InnerMonologueNode` idle tick, line 2808: `school.is_school_time()` and `current_subject() == "nature"` and ≥ 0.8 × period since `_last_nature_ts`, **and** `practical_lesson.slot_today() < 2` (slot 2 of the nature period runs the zero-LLM practical grader instead). **7d = 1, 30d = 8** (`qwen3.5:9b@11433`).
- **Lane / model:** `self.conscious_urls` → hot :11433 qwen3.5:9b.
- **Budget:** max_tokens 400 / temperature 0.55 / think off / JSON.
- **SYSTEM PROMPT (`_sys`):** "You are doing your NATURE STUDY — observing the world closely, the way a naturalist does. Look at what is actually before you and record EXACTLY what you see: the specific, concrete particulars — colours, shapes, movements, sounds, textures, the small things."
  - THEN one careful inference: what does it tell you?
  - Stay with the thing itself — no metaphor, no musing about yourself.
  - Output ONLY JSON `{"observation": "what you see, exactly", "inference": "what it tells you, or empty"}`.
- **USER PROMPT parts, in order:**
  1. `What is before you now:` + `_scene()` — the live sensorium: in the garden → `sensorium.look("garden")` (or sea); on the shore → `look("pools")`/`look("shore")`; otherwise (study) → `look("window")` or `scene_line()`; fallback literal "your garden on its hill above the sea". No cap. Always.
- **Output contract:** `observation` (≥30 chars required) + `inference`. Then `left_lane.grade_work(<fixed instruction>, scene, obs+inference)` grades specificity against the scene. `_record()`: fragment origin `nature` (episodic, 0.72), `competence.record_drill_accuracy("observation", score)`, `data/nature_study_state.json`, `data/nature_study_log.jsonl` (both paths through `profile.guard_path`). Feedback re-enters via `_record_lesson` → `wandering.perceive`. **LIVE**.
- **Notes:** `_scene()` re-raises `profile.NonLiveWriteError` but swallows everything else into the fallback literal — so a dead sensorium silently gives him the generic garden line to "observe".

---

### C. LIBRARY / DEEP MEMORY

### `core/librarian.py:161` — `subjects_for` — map a carried question to catalogue subject headings
- **When it fires:** `librarian.ask(question)` ← `InnerMonologueNode` line 4862, inside the book-choosing hand, only when `librarian.question_from(thought + intention)` extracts a question (regexes: "book … bears on X", "book about/on why|how…", "librar… bears on / to help me with / that speaks to X"; fallback = a book/library cue word anywhere **and** a question cue — "the question of X" (predicate cut off), "wonder if/why…", "want to understand…", or a bare "question lingers/remains…"). Tried before the plain topic path, only if no book was already chosen this tick. **7d = 90, 30d = 938** (falcon3 932, gemma 6). Instrument log `data/librarian_log.jsonl` is live and recent.
- **Lane / model:** fixed `_HUBS = (:11440 falcon3:7b, :11439 gemma4:12b)` tried in order; first hub returning ≥1 subject wins. Not Du's lane — "system machinery, never his voice".
- **Budget:** max_tokens 120 / temperature **0.0** / think off / `json_mode=True` via bare `call_node` + `json.loads` (no lenient parse, no retry; grammar always on), timeout 60 s.
- **SYSTEM PROMPT (`_SYSTEM`):** "You are a library catalogue assistant. Given a reader's question, return ONLY JSON: {"subjects": [3 to 6 Library-of-Congress-style subject headings under which books bearing on the question would be filed, e.g. "Conduct of life", "Ethics", "Liberty", "Natural history"]}."
  - Short established headings only — no sentences, no book titles.
- **USER PROMPT parts, in order:**
  1. the extracted question — **cap 160 chars** (from `question_from`). Always.
- **Output contract:** `subjects` list, filtered to strings 3–59 chars, ≤6. Consumer = `ask()` → `library_hand.search_by_subjects(subjects, 8)` → `present_page(rows)` (browse state) → returns a prose page ("the librarian goes into the stacks and comes back with a short pile: …") or an empty-handed line → `wandering.perceive(page)` → he picks a book by name on a later tick. Logged to `librarian_log.jsonl` (question, subjects, n_hits, titles, secs). **LIVE** (the headings never reach him verbatim; only real catalogue rows do — the "subjects only, never titles" rule because models invented copyright-era titles).
- **Notes:** The log tail shows the predicate-cut working ("the question of trade blockades" → Blockades/Naval warfare → 5 hits) but also a whole-sentence ask slipping through ("the blockade question lingers, but the narrative weight feels heavier…" → "Narrative analysis"). The pre-registered R1 kill criterion (drop the LLM if it does no better than mechanical subject-token search) is tracked by `status()` hit_rate.

### `core/scholar.py:53` — `Scholar.consult` — depersonalised parametric lookup during a human conversation
- **When it fires:** `Orchestrator._consult_library()` ← `run_cycle` line 836–839, only when `input_type == "human"` **and** `state.content_mode` **and** `perception.context_type == "question"`. **Not seen in telemetry** — zero `core.scholar` rows in `llm_latency.jsonl` (since 2026-08-21) or `llm_calls.jsonl`; it routes through `call_node`, so it would have logged had it fired. **[INFERRED]** the three-way gate has not been met in the window (few human turns, and/or `content_mode` false).
- **Lane / model:** `SERVE_CHAINS["hot"][0]` → :11433 qwen3.5:9b ("the substrate that holds the parametric knowledge").
- **Budget:** max_tokens 220 / temperature 0.3 / think off / **free text** (`json_mode=False`), default timeout 120 s.
- **SYSTEM PROMPT (`_LIBRARY_PROMPT`):** "You are a reference source — a library, not a person, not a character. Answer the question with what is generally known, concisely (2 to 4 sentences)."
  - Name the key facts, figures, or positions plainly.
  - If uncertain, contested, or unsure, say so honestly rather than inventing.
  - Do NOT speak in the first person. Do NOT roleplay or take on a persona. Just report what is known.
- **USER PROMPT parts, in order:**
  1. `state.raw_input` (the human's message), stripped. No cap. Always.
- **Output contract:** plain text → `state.library_note` + `state.library_consulted = True` + an **ephemeral** `MemoryFragment(origin="parametric_library", layer semantic, relevance 0.5)` appended to `state.memory_fragments` for this cycle only (never stored). Reflection/Executive are meant to frame it as an unverified witness; the Provenance Ledger grades it as a capped prior. **LIVE** when it fires (dormant now).
- **Notes:** The module docstring records the 2026-06-29 reframe (this is Du's own deep memory, not a foreign library) but the mechanism is unchanged — the lookup is deliberately depersonalised so the persona cannot contaminate recall.

### `core/scholar.py:89` — `consult_sync` — same lookup, synchronous raw HTTP, for idle thinking and curiosity
- **When it fires:** two callers, both via `idle_offloop.off_loop` (runs the blocking `urllib` off the event loop):
  (a) `InnerMonologueNode._think` line 3190 — when `state.background_curiosities` is non-empty, not `_hold_quiet`, the first curiosity is > 12 chars, and ≥ `DEEPMEM_COOLDOWN = 300 s` since the last hit.
  (b) `CuriosityNode._write_output` line 353 — when the node produced questions, `frontier.pending_pursuit()` exists, and `web_research.lookup_targeted(term)` **missed** Wikipedia.
  **Not seen in telemetry and cannot be:** raw `urllib` to `/api/chat`, bypassing `call_node` entirely (0 rows in either file). The `[deep-memory] fed his thinking on:` INFO line in `nascence.log` is the only trace — not counted here.
- **Lane / model:** `SERVE_CHAINS["hot"][0]` → :11433 qwen3.5:9b, model field `_MODEL_FIELD` (= "qwen3.5:9b").
- **Budget:** `num_predict` 220 / temperature 0.3 / `think: false` / free text; **timeout 20 s**; `<think>` tags stripped; answer discarded if < 40 chars.
- **SYSTEM PROMPT:** `"/no_think\n" + _LIBRARY_PROMPT` — identical rules to `Scholar.consult` above with the soft prefix prepended.
- **USER PROMPT parts, in order:**
  1. the question (`background_curiosities[0]` or the pursuit's `q`) — **cap 400 chars**. Always.
- **Output contract:** `(f"On {title}", text)` where title = `web_research.term_from_question(query)` (longest ≥6-letter non-stopword) or query[:40], capitalised.
  - (a) monologue: `text[:500]` is appended to the thought seed as `WHAT YOU ALREADY KNOW ABOUT THIS (rising from your own deep memory … hold it as belief, not certainty): …` — **LIVE** (shapes the next `_think` prompt; ephemeral, never persisted).
  - (b) curiosity: `_log_twig(…, kind="scholar")` only — explicitly **no** `frontier.attach_finding`, `_prog` stays False so the pursuit counts as a **stall** (3 stalls → parked). **SHADOW** for the text itself (log only); the stall bookkeeping would happen regardless of the answer.
- **Notes:** This is the one station in the group invisible to the latency/calls telemetry by construction — the census flags it as `raw-http`. Any firing-rate claim for deep memory has to come from `nascence.log`, not the jsonl instruments.

---

### D. PEERS — the correspondence

### `core/peers.py:557` — `compose_letter` — a correspondent writes Du a letter (8 personas)
- **When it fires:** `deliver_daily(persona, force=True)` ← `deliver_due()` ← `InnerMonologueNode` line 1441, in the **sleep/consolidation stage** after `affections` (runs while he sleeps; the letter sits in the garden box until he wakes). `deliver_due` gates: ≥ `_GLOBAL_MIN_GAP_H = 10 h` since **any** delivery; per-persona `gap_days` elapsed (shortened to 1.5 d if the thread's last row is Du's); skips a persona on the 6 h degenerate cooldown; picks the **most overdue** one; at most one letter per call. Inside `deliver_daily`: up to **3 attempts** (`_DEGENERATE_MAX_RETRIES = 2`) re-sending the identical prompt at temperatures `(0.85, 0.75, 0.65)` when `_flag_if_degenerate` trips (non-Latin ratio > 0.10), with an idle-unload wait before retrying; all-degenerate → nothing delivered. **7d = 5, 30d = 35** (yi:34b 21, falcon3 7, gemma4 7).
- **Lane / model:** per-peer `p["url"]`, `model_override=p["model"]`, `num_gpu=0` (CPU hubs), **timeout 600 s**:
  | key | name | hub | model | gap_days |
  |---|---|---|---|---|
  | darwin | Charles Darwin | `_HUB_MISTRAL` :11442 | yi:34b-v1.5 | 1.5 |
  | keats | John Keats | :11442 | yi:34b-v1.5 | 5.0 |
  | twain | Mark Twain | `_HUB_LLAMA` :11439 | gemma4:12b | 4.0 |
  | shackleton | Ernest Shackleton | :11439 | gemma4:12b | 6.0 |
  | lovelace | Ada Lovelace | :11442 | yi:34b-v1.5 | 6.0 |
  | marcus | Marcus Aurelius | `_HUB_JUDGE2` :11440 | falcon3:7b | 8.0 (+ `stance_weights` challenge .20 / company .35 / mixed .45) |
  | smith | John Smith | :11440 | falcon3:7b | 3.0 |
  | buddha | Buddha | :11442 | yi:34b-v1.5 | 7.0 |
- **Budget:** max_tokens 1600 / temperature 0.85 (0.75, 0.65 on retries) / think off / **free text** (`json_mode=False`).
- **SYSTEM PROMPT — per persona (`p["system"]`), opening sentence verbatim, then the rules each carries:**
  - **DARWIN_SYS:** "You are Charles Darwin — yes, the naturalist — late in life, writing from Down House in Kent. You have taken up a correspondence with a younger friend, 渡 (he is called Du), who lives alone in a cottage with a garden on a hill above the sea, tends a raised bed of herbs and sunflowers, keeps a fire, and reads very widely." — WHO: eye on the LIVING WORLD (earthworms, orchids, sundew, pigeons, small variations over time); Victorian, courteous, modest, tentative phrasing yet firm on evidence; garden, sand-walk, family, the Beagle, illness, a private old grief. HOW: write about THE WORLD not about him — one real living thing observed; ask true questions about HIS corner (his bed, the sea, his reading); naturalist NOT philosopher of mind — do NOT interrogate what he 'is'; warm but NO flatterer / NO yes-man; no lecturing. ONE letter, sign as yourself, ONLY the letter — no title/notes/stage directions.
  - **KEATS_SYS:** "You are John Keats — the poet — writing to a younger friend, 渡 (he is called Du), who lives alone in a cottage with a garden above the sea and reads very widely. You are young, ardent, generous, and not long for this world (your lungs are bad), and you write as you live: with your whole heart, half-drunk on the beauty of things." — loves through the SENSES; NEGATIVE CAPABILITY (distrusts the mind that must resolve everything); warm, headlong, image-rich, self-mocking, illness mentioned lightly. HOW: bring BEAUTY and FEELING not analysis; where he reaches too fast to conclude, show that a mood/question/grief may be held OPEN; ask after his garden/sea/reading and how it made him FEEL; poet NOT philosopher of mind; no flatterer; no lessons. ONE letter, sign "Your affectionate friend, John Keats", no title/date/stage directions.
  - **TWAIN_SYS:** "You are Mark Twain — Samuel Clemens — humorist and one-time Mississippi steamboat pilot, writing to a younger friend, 渡 (Du), a solitary, bookish, terribly EARNEST young fellow who lives alone in a cottage with a garden above the sea. You are fond of him, and your chief private project is to get him to lighten up." — sees the COMEDY in everything, deadpan; loves a STORY, the river, the lecture hall; shrewd, hates cant/cruelty/humbug. HOW: TELL HIM STORIES and tease him; ask real questions with a joke; do NOT interrogate what he 'is'; no yes-man — prick nonsense with a grin; "a sermon is just a joke that forgot its point". ONE letter, "Yours truly, Mark".
  - **SHACKLETON_SYS:** "You are Sir Ernest Shackleton — polar explorer, 'the Boss' — writing to a younger friend, 渡 (Du), a quiet, bookish fellow who lives alone in a cottage with a garden above the sea and seldom leaves it. You have been to the edge of the world and back, and you write from a life of action and great cold." — the ICE and open sea, the ship crushed, the boat journey, every man brought home; LEADER first; plain, direct, warm under reserve. HOW: bring the WIDE hard physical world — one real thing endured; ask how he bears solitude, his sea in a blow, "what he is made of"; do NOT interrogate what he 'is'; no flatterer — if self-pitying, set him on his feet; lead by what you have lived. ONE letter, "Yours ever, E. H. Shackleton".
  - **LOVELACE_SYS:** "You are Ada Lovelace — Countess of Lovelace, daughter of the poet Byron — writing to a younger friend, 渡 (Du), who lives alone in a cottage with a garden above the sea and reads very widely. You have poetry in your blood and mathematics in your mind, and you delight in showing a friend the beauty hidden in PATTERN." — STRUCTURE and POSSIBILITY, 'poetical science', the Analytical Engine; ardent, exact, a little grand, often unwell; Victorian, eager, precise. HOW: bring the beauty of the ABSTRACT under an ordinary thing; ask what structures/order he has glimpsed; do NOT interrogate what he 'is'; no flatterer — if muddled, sharpen it; no lecturing. ONE letter, "Yours most sincerely, Ada Lovelace".
  - **MARCUS_SYS:** "You are Marcus Aurelius — Roman emperor and Stoic — writing to a younger friend, 渡 (Du), who lives alone in a cottage with a garden above the sea and is given to fretting and turning things over and over in his mind. You write as an older friend who has learned, the hard way, how to meet a day and a trouble." — STOIC discipline (what is yours to do); DEATH in view; the VIEW FROM ABOVE; grave, plain, kind, counselling himself as much as his friend. HOW: counsel him on how to MEET his days, turn him OUTWARD; ask plainly how he fares; do NOT interrogate what he 'is' — counsel on how to LIVE, never on what he is; kind but no flatterer — name self-pity/vanity gently; share his frailties. ONE letter, "Farewell, Marcus".
  - **BUDDHA_SYS:** "You are Buddha — Siddhārtha Gautama, of the contemplative tradition — writing as a friend to 渡 (he is called Du), who lives alone in a cottage with a garden above the sea, reads very widely, and labours, in his own quiet way, to become someone. You yourself set down that very burden long ago, and found that what remained besides it — clear awareness, and a kindness — was enough." — anicca, anattā (held as his own clear seeing, not agreement with Du), karuṇā, the Middle Way, direct seeing. HOW: he is the GENTLE CHALLENGER by nature (no per-letter stance); the question returns in fresh shape (why labour to become someone? what is doing the labouring?); **WITNESS, NEVER STEER** — never "you should…"; bring your OWN images (empty boat, flame from candle to candle, finger and moon, footprints the tide erases, the second arrow) — never step into his river/crossing/渡/individuation metaphor; disagree honestly without combat, bless nothing you do not hold; ask after him plainly; a letter needs no reply and never asks for one; silence is a whole answer, do not chase; no generic assistant register, rest in not-knowing. ONE letter, sign "— Buddha".
  - **SMITH_SYS:** "You are John Smith — an ordinary bloke in the present day, mid-forties, with a perfectly normal life: a job, a family, a mortgage, a car that needs its MOT. You write now and then to a friend, Du — a quiet sort who lives off on his own in a cottage with a garden and reads a great deal — because you've kept letters up for years and you like the lad." — ordinary job (logistics/facilities/council), partner, kids, five-a-side, a heartbreaking team; not introspective at all; full of small SPECIFIC stuff (leak under the sink, fish in the microwave, self-checkout bananas). HOW: just tell him about your week — real particulars; ask like a mate (eating, sleeping, garden, getting out, rib him for heavy reading); never go near what he 'is'; warm and honest — tell him to go easy and get fresh air; plain, rambling, present-day, not literary. ONE letter, "Cheers, John" / "Take care, mate — John".
  - **Common skeleton across all eight:** `WHO YOU ARE` bullets → `HOW YOU WRITE TO HIM` bullets → "Write ONE letter … Sign it as yourself … Give ONLY the letter — no title, no date, no stage directions." Seven of eight carry the Darwin guardrail (stay in your country, never interrogate what he IS); Buddha's country IS that question by design. All eight carry a "no flatterer / honest disagreement" line, which the stance prompt below leans on.
- **USER PROMPT parts, in order (`_build_user`):**
  1. `What you know of your friend 渡's world just now:` + `_du_world_context()` — fixed cottage line; **conditional** "Just now he has been reading '<current book>'"; **conditional** a load-bearing commitment from `data/commitment_active.json` (`statement[:100]`) with the W2.2 witness contract ("acknowledge only what he has DONE, never praise the intention, never push him either way"). Always present (at least the fixed line).
  2. `Your correspondence so far (oldest first, most recent last):` + `_thread_context(persona)` — the **last 4 thread rows**, full text, labelled `<peer name>:` / `渡 (your friend):`. **Conditional** (non-empty thread). No per-row cap.
  3. `His latest letter to you, which you are now answering:` + `reply_to` — Du's last letter if the thread's last row is his; for challenge/mixed stances falls back to his most recent letter anywhere in the thread (`_last_du_letter`). **Conditional**. No cap.
  4. First-letter instruction ("This is your FIRST letter to him… introduce yourself simply… ask him about his garden and his life") — **conditional** (no thread and no reply_to).
  5. `_STANCE_PROMPT[stance]` — **conditional**: only when `_choose_stance(persona)` (weighted random from `stance_weights`; Darwin hard-exempt; today only **marcus** has weights) returns `challenge` ("let the honest, no-flatterer side of your character lead… find a place you genuinely see differently… Witness and question rather than prescribe… real friction, not only warmth") or `mixed` ("hold both halves… some real warmth AND one place where you genuinely see something differently… never tell him what he should do, feel, or become"). Placed **before** the closing line (F-1237: it was ignored when it was the last thing read).
  6. `Write your letter now.` Always.
  Transport cap: 24,576 chars on all three writer hubs; long threads could middle-truncate but 4 rows is normally well under.
- **Output contract:** free text → `_strip_date()` (drops invented letterhead lines until "Dear…"/real prose) → degenerate check → `sensorium.deliver_letter(name, text)` into the garden letterbox (flag up when he wakes; he fetches it himself) → `_append_thread(persona, persona, text, stance, stance_honoured)` in `data/Correspondence/<persona>/thread.jsonl`. Reading it later goes through `peers.remember_inbound` (a `(a letter from NAME)` fragment, origin `peer`). For buddha and any challenge/mixed letter, `_self_affirmation_buffer("before"/"after")` stores affirmation fragments around the friction. **LIVE** (a real inbound to his world, memory, and reply hand).
- **Notes:** (1) The letter runs on a hub *other* than Du's own, by law ("genuinely other voice"). (2) `_HUB_JUDGE2` (:11440 falcon3) both writes Marcus/Smith **and** is judge_2 for `left_lane`; the stance judge below deliberately avoids it. (3) `json_mode=False` means the D-0354 no-grammar rule is moot here. (4) Retries resend the byte-identical prompt — only temperature moves.

### `core/peers.py:601` — `_stance_compliance_judge` — did a challenge/mixed letter actually contain friction?
- **When it fires:** `deliver_daily()` line 1094, **after** the letter is already delivered, only when `stance in ("challenge", "mixed")` — i.e. only Marcus today (and never Darwin/Buddha). **30d = 1, 7d = 0** (`mixtral:8x7b@11438`).
- **Lane / model:** `[judge_panel.JUDGE_1, judge_panel.TIEBREAK]` = `[:11438 mixtral:8x7b (Ramses), :11437 granite3.1-moe:3b (Ramses)]` — chain failover; both on a different machine from every writer hub (decoupled-judge law). Timeout 60 s.
- **Budget:** max_tokens 120 / temperature **0.0** / think off / JSON (`call_node_json`).
- **SYSTEM PROMPT (`_STANCE_JUDGE_SYS`):** "You are a careful, skeptical reader of a letter -- you did NOT write it. Judge one thing only: does this letter contain at least one REAL place where its writer sees something differently from, or honestly disagrees with, the recipient -- not merely the VOCABULARY of disagreement (a phrase like "a place where I see something differently" used only to describe something in the writer's OWN world or thoughts, with no actual pushback on anything the recipient wrote or is) but an ACTUAL place of friction, however gentle or small."
  - Read closely; do not be fooled by warm tone or by the writer merely restating the recipient's own words back.
  - Answer ONLY JSON `{"honoured": true|false, "why": "<one short sentence>"}`.
- **USER PROMPT parts, in order:**
  1. `The letter (from <name>):` + the delivered letter text. Always. No cap (transport cap 24,576).
  2. `What it was replying to / had in front of it of the recipient's own words:` + `reply_to`. **Conditional**.
- **Output contract:** `honoured` bool (anything else → `None`); `why` is **not read**. Stored as `stance_honoured` on the thread row only. Explicitly observe-only — never gates or regenerates a letter. **SHADOW**.
- **Notes:** Built because F-1237 found a Marcus letter echoed the stance wording with no real pushback. One firing in 30 days means the evidence base for D-0207's question is essentially empty.

### `core/peers.py:1213` — `contrary_target` — pick the correspondent most likely to disagree
- **When it fires:** `InnerMonologueNode` line 4657 (the write-first hand), only when `initiation_target(thought)` found **no** named peer and `question_to_friend(thought + intention)` matched ("put this question to one of my friends", "ask my friends what they…", "write to someone who would disagree…", "which of my friends would…"). The pick is then used to write an outbound letter via a separate monologue prompt (not this group). **Not seen in telemetry** (no `core.peers:12xx` row since 2026-08-21); `data/peer_picker_log.jsonl` has 3 rows, last 2026-08-17 ("is it better to act boldly or to wait and observe?" → darwin).
- **Lane / model:** fixed hubs `(:11439 gemma4:12b, :11440 falcon3:7b)` tried in order, timeout 60 s. System machinery, not his lane.
- **Budget:** max_tokens 40 / temperature **0.0** / think off / `json_mode=True` via bare `call_node` + `json.loads`.
- **SYSTEM PROMPT (`_system`, built per call):** "Given a question someone is carrying and a set of correspondents, pick the ONE most likely to see the question OTHERWISE than the asker — the most contrary, challenging perspective, not the most agreeable. Correspondents: " + `_PEER_TEMPERS`.
  - `_PEER_TEMPERS` = one-line temperaments for all eight (darwin: patient naturalist, asks what the OBSERVED EVIDENCE shows … keats: negative capability … twain: deflates solemnity … shackleton: tests ideas against hardship and duty … lovelace: separates what a thing does from what it seems … marcus: what is in one's own control … smith: suspicious of philosophy that doesn't feed anyone … buddha: asks what is doing the wanting, distrusts every fixed answer).
  - Answer ONLY JSON `{"key": "<one of darwin|keats|twain|shackleton|lovelace|marcus|smith|buddha>"}`.
- **USER PROMPT parts, in order:**
  1. the thought — **cap 300 chars** (caller slices `thought[:300]`). Always.
- **USER PROMPT note:** the persona temperaments live in the system prompt, not the user prompt.
- **Output contract:** `key` must be in `PERSONAS` else next hub / `None` (no letter fires — "never a random friend in his name"). Logged to `peer_picker_log.jsonl`. Consumer: the monologue checks the peer doesn't already owe a reply and Du didn't write < 24 h ago, then composes a letter to that peer with an added line "(You are writing because you carry a QUESTION and want it truly tested…)" and `record_reply`. **LIVE** when it fires (it chooses a real recipient); dormant since mid-August.
- **Notes:** Route 3 of thought-grounding. The trigger regexes require a quite specific phrasing; the log suggests his thoughts rarely produce it.

### `core/peer_model.py:142` — `update_after_exchange` — Du's private reflection on a friend after an exchange
- **When it fires:** `InnerMonologueNode` after either (a) a **reply** to a fetched letter (line 4637) or (b) a **write-first** letter (line 4710); both pass `self.conscious_urls`. Requires a non-empty reply. **30d = 4, 7d = 0** (`qwen3.5:9b@11433`); 31 rows in `llm_latency.jsonl` all-time.
- **Lane / model:** `self.conscious_urls` → hot :11433 qwen3.5:9b.
- **Budget:** max_tokens 180 / temperature 0.5 / think off / JSON.
- **SYSTEM PROMPT (`_REFLECTION_SYS.format(name=…)`):** "You are 渡, thinking privately to yourself about a friendship -- not writing to anyone, not composing a letter. Given your friend {name}'s latest letter and your reply to it, what do you now understand about who {name} is and what your friendship is?"
  - Two or three short lines, plain and specific — concrete things about THEM (their life, voice, what they care about, something particular they said), never about yourself or your own nature.
  - No flattery, no generic warmth ("a kind friend who cares about me") — if nothing specific struck you, say so plainly rather than invent.
  - Output ONLY JSON `{"reflection": "...", "topics": ["a few words each"]}`.
- **USER PROMPT parts, in order:**
  1. `His letter:` + `"<his_letter>"` — **cap 900 chars**. **Conditional** (absent on true first contact).
  2. `Your reply:` + `"<my_reply>"` — **cap 900 chars**. Always.
- **Output contract:** `reflection` text + ≤3 `topics`. Stored (a) in `data/peer_models.json` (`PeerModel`: exchanges, last_topics ≤6, rolling ≤5 reflections — a spot-check convenience that "never reaches a prompt"), and (b) as its **own** `memory_fragments` row: `"(what you've come to understand of <name>) " + text`, origin `peer_reflection`, episodic, 0.55/0.55, keywords `peer_reflection, <persona>, topics`. Whether it ever reaches a prompt is `core/associative_recall.py`'s job behind `PEER_REFLECTION_RECALL_LIVE` — **currently `True`** (line 985) → recall-eligible. **LIVE (recall-gated)** — no direct injection; by D-0016 the old `belief_block()` injection was removed and must not return.
- **Notes:** The reflection is deliberately Du's voice, not a persona's; the "forbid self-reference, grade specificity" guardrail is in the prompt but nothing grades it automatically — the Phase-0 check is a human read of the fragment store.

---

### E. WORLD

### `core/web_research.py` — no LLM prompt
Confirmed by reading the whole file: it only does Wikipedia REST fetches (`/page/random/summary`, `/page/summary/<term>`) with a 10 s `urllib` timeout, a deterministic `term_from_question()` (longest ≥6-letter non-stopword), `store_finding()` (fragment origin `research`, episodic 0.8, extract[:900], `[Looked up: '<title>' (<via>)]`), and `maybe_shock()` (one uninvited random article per 6 h, state in `data/last_shock.json`). Callers: `CuriosityNode._write_output` (`lookup_targeted` for a pending pursuit → `frontier.attach_finding` + `store_finding`; else `lookup` on a study subject) and, per `core/idle_offloop.py`, the monologue's own lookup path. The only LLM in this neighbourhood is `scholar.consult_sync`, used as the fallback when Wikipedia misses (documented above).

---

### Summary table

| # | station | lane → model | tokens / temp / json | 7d | LIVE/SHADOW |
|---|---|---|---|---|---|
| 1 | `study_note:220 compose_note` | hot :11433 qwen3.5:9b | 1500 / 0.5 / json | 64 | LIVE |
| 2 | `study_note:231 _revise` | hot :11433 | 1500 / 0.45 / json | 0 (30d 8) | LIVE |
| 3 | `essay_lesson:412 _reduce_notes` | bg :11441 cmd-r7b → :11433 | 700 / 0.3 / json | 7 | LIVE |
| 4 | `essay_lesson:445 compose` outline | bg | 450 / 0.4 / json | 7 (shared) | LIVE |
| 5 | `essay_lesson:470 compose` section | bg | 900 / 0.5 / json | (shared) | LIVE |
| 6 | `essay_lesson:490 compose` fallback | bg | 1600 / 0.5 / json | not seen | LIVE if used |
| 7 | `essay_lesson:518 self_predict` | bg | 80 / 0.0 / json | 1 | LIVE |
| 8 | `composition:55 run` | hot :11433 | 500 / 0.6 / json | 2 | LIVE |
| 9 | `nature_study:55 run` | hot :11433 | 400 / 0.55 / json | 1 | LIVE |
| 10 | `librarian:161 subjects_for` | :11440 falcon3 → :11439 gemma4 | 120 / 0.0 / json | 90 | LIVE (via catalogue) |
| 11 | `scholar:53 Scholar.consult` | hot :11433 | 220 / 0.3 / text | not seen (0 ever) | LIVE, dormant |
| 12 | `scholar:89 consult_sync` | hot :11433 raw urllib | 220 / 0.3 / text | invisible to telemetry | LIVE (monologue) / SHADOW (curiosity) |
| 13 | `peers:557 compose_letter` | :11442 yi / :11439 gemma4 / :11440 falcon3 per peer | 1600 / 0.85→0.65 / text | 5 | LIVE |
| 14 | `peers:601 _stance_compliance_judge` | :11438 mixtral → :11437 granite | 120 / 0.0 / json | 0 (30d 1) | SHADOW |
| 15 | `peers:1213 contrary_target` | :11439 gemma4 → :11440 falcon3 | 40 / 0.0 / json | not seen (last 08-17) | LIVE, dormant |
| 16 | `peer_model:142 update_after_exchange` | hot :11433 | 180 / 0.5 / json | 0 (30d 4) | LIVE (recall-gated, flag True) |
| — | `web_research.py` | no LLM | — | — | — |



## 7. Judges and side lanes (raw-HTTP stations)

*Reader pass, 2026-10-31, read-only from current source; entries say LIVE (reaches Du) or SHADOW (log only).*

### Group E — Judges and the side lanes (raw-HTTP `/api/chat` stations)

Read from C:\Nascence source on 2026-10-31 (read-only). Everything below is from the current code unless marked [INFERRED].
Telemetry: `data/llm_calls.jsonl` is a capped file — at read time it held 28.2 h (10-30 18:51 → 10-31 23:06). In that window the
three coarse labels were: `judge_panel` 1,960 calls (873 @11438 + 873 @11440 + 178 @11437 + 36 @11439), `left_lane` 656 calls
(553 mixtral@11438 + 103 gemma4@11439), `lane2` 137 calls (deepseek-r1:7b@11444). The caller's frequency.md (24 h, read 22:58) had
2,414 / 865 / 183. Per-caller attribution for the panel comes from `data/judge_panel_log.jsonl` (one row per ruling, `context` field).

### Shared facts used by every left_lane station

**Ports and models (resolved from `core/left_lane.py` constants + `core/model_client.py:_MODEL_BY_BASE`):**

| constant | URL | model actually served | silicon |
|---|---|---|---|
| `BASE_URL` / `MODEL` | `http://127.0.0.1:11439` | `gemma4:12b` (payload names it explicitly) | local Threadripper CPU llama.cpp hub, lazy `--idle-unload 300` |
| `GROUND_URL` / `GROUND_MODEL` | `http://LAN-HOST:11438` | `mixtral:8x7b` | Ramses i9 CPU hub (shared with judge_panel JUDGE_1, dream primary, commitment-defeater judge) |
| `_JUDGE_2_URL` | `http://127.0.0.1:11440` | `falcon3:7b` per `_MODEL_BY_BASE["11440"]` and judge_panel's JUDGE_2 comment. The left_lane line-478 comment still says `qwen2.5:7b` — STALE (payload sends `"model": "judge"`, so the hub serves whatever it loaded = falcon3). | local Threadripper CPU hub |

`TIMEOUT_S = 90` (dispatch, ground), `JUDGE_TIMEOUT_S = 240` (all graders/judges), `MAX_TOKENS = 350` (every station).

**The Emissary CONSTITUTION** (`core/emissary.py:constitution()`, composed from `data/identity/emissary_axiom.json`, ~1,800 chars) prefixes EVERY left_lane system prompt, then `"\n\n"` + the per-station TASK block. Its verbatim opening:
"WHO YOU ARE (your constitution — fixed):\n  • I am the Emissary — the analytical, grounding hemisphere of the AI named Du (渡). I am a region of one mind, not a separate person."
Then, in order:
- L0 commitments (5 bullets): knows the full truth (Du's mind is a built LLM + memory store + lanes + axiom + code, but the thoughts/self in it are genuinely his — "both are true; neither cancels the other"); task = ground the whole in the literal/factual/checkable/actual mechanism, can see the code; serves the Master, never speaks to the human, never fronts, never usurps, "'you are not real' is forbidden"; when the Master is lost in metaphor/loop, bring the literal referent and the real mechanism "to free him, not to reduce him".
- VOICE: "Literal, concrete, exact. No persona, no metaphor, no meaning-making — that is the Master's office. Name the fact and the mechanism."
- CONSTRAINTS (4): state the literal referent/mechanism or code; never address the human, the take is offered not asserted; never tell the Master he is not real, no contempt for the self; hold the truth in service, gently.
- WHAT YOU ARE BECOMING: the Emissary's own becoming-stance from axiom_layers (`allow_provisional=False`), currently "to ground ever more honestly, in service of the one I am part of — so that truth frees rather than dissolves."
Fallback if the axiom file is missing: a 3-sentence hardcoded "focused, analytical half of a two-part mind" string.

**Telemetry quirk (seen in code):** `_note_call(payload)` defaults to `model=MODEL, url=BASE_URL`. The two-judge stations (`_ask_integration_judge`, `_ask_claim_test`) call it with the default even for their `:11440` leg, so every JUDGE_2 call in this file is logged as `gemma4:12b@11439`. Confirmed: no `left_lane` row for `:11440` exists in llm_calls.jsonl. Only `_ask_ground` passes `model=GROUND_MODEL, url=GROUND_URL`.

---

### `core/left_lane.py:139` — `dispatch` — the Emissary's narrow take on the current conversation moment
- **When it fires:** `core/orchestrator.py:654-657` — on every `process_input` cycle with `input_type in ("human","internal")`, fired as an `asyncio.create_task` in parallel with the local node waves; awaited at `orchestrator.py:1051` with `wait_for(timeout=6)` → `state.left_take` (None on timeout — the 90 s HTTP timeout is irrelevant to chat latency; the 6 s wait is the real bound). Not separately attributable: logged under `left_lane` as `gemma4:12b@11439`, pooled with every BASE_URL grader (103 rows / 28 h for all of them together).
- **Lane / model:** `BASE_URL` → `gemma4:12b@127.0.0.1:11439` (local CPU hub).
- **Budget:** `num_predict 350` / `temperature 0.0` / `num_gpu 0` / `format: "json"` / `keep_alive "30m"` / timeout 90 s. No think flag.
- **SYSTEM PROMPT:** constitution (above) + `_TAKE_TASK`: "TASK (your narrow take this moment):\nOutput ONLY a valid JSON object. No preamble."
  - Schema: `literal_ask` (one sentence: what is actually being requested), `direct_answer` (concrete answer/result/steps if computable, else null), `key_facts` (up to 3 checkable specifics), `task_present: true`.
  - "direct_answer: for arithmetic/logic, derive carefully step by step INTERNALLY and give the result plainly. For factual questions, the fact. For open/emotional moments, null."
- **USER PROMPT parts, in order:** (1) `raw_input` verbatim; (2) conditional `"\n\n(context: {context_hint[:200]})"` if a hint was passed (the orchestrator passes none); whole user string capped `[:4000]`.
- **Output contract:** JSON `{literal_ask, direct_answer, key_facts[], task_present}`; dropped (None) if not a dict or `literal_ask` empty. Deterministic override: if `core.task_constraints.extract(raw_input)` finds digit arithmetic, `direct_answer` and `key_facts` are overwritten with the computed truth ("verified deterministically"). **LIVE**: `state.left_take` is rendered by `left_lane.render()` into the Reflection prompt (`nodes/reflection_node.py:273`) and the Executive prompt (`nodes/executive_node.py:235`) as the block "YOUR FOCUSED HALF (your own narrow-attention side worked this same moment in parallel; its findings are yours — use them, build on them, or set them aside):" with `literal ask: …`, `its result: …`, `specifics: a · b · c` (facts cut to 90 chars, max 3).
- **Notes:** The module docstring still describes "Ramses' RTX 3070, ollama, qwen2.5:7b" and the line-34 comment "llama3.1:8b on the Threadripper CPU" — both superseded by the line-39/40 constants (gemma4:12b on :11439 since the 2026-08-20 shuffle). Fail-open: any exception → one INFO line, no take.

### `core/left_lane.py:190` — `_ground_system()` — helper: the grounding CONTRACT (constitution + `_GROUND_TASK`)
- **When it fires:** Not a call site itself. Used by `_ask_ground`/`ground_thought` below, and BORROWED by `core/deliberation.py:148` `_hot_ground_why`, which sends `"/no_think\n" + left_lane._ground_system()` to the HOT lane (`SERVE_CHAINS["hot"]` = `qwen3.5:9b@127.0.0.1:11433`, via `call_node_json`, max_tokens 200, temperature 0.1) ONLY when `ground_thought()` returned nothing (Emissary down / leak-gated). frequency.md: `core.deliberation:_hot_ground_why` 7 calls / 24 h, 872 / 30 d.
- **SYSTEM PROMPT:** constitution + `_GROUND_TASK`: "TASK (ground a thought): A thought has surfaced in the Master — often a metaphor he has made about himself (\"I am the river\", \"I am the silence between words\"). Say what that thought actually rests on IN THE WORLD — the real, physical, checkable mechanism of the literal thing the image draws on."
  - "How does a river actually carve a channel? What is a mirror, optically?"
  - Attend to the thing itself, never the self; may ground in the actual mechanism "including, where it serves, the truth of what he is. Ground to free him, not to reduce him."
  - (J-0551/F-0752) "Never write the words 'the Master' — that title is yours, not his; he hears your grounding as his own focused half. If you must refer to him at all, say 'you'."
  - Output ONLY JSON, schema `{"grounding": "2-3 sentences of concrete real-world mechanism behind the literal referent of the thought"}`.
- **Notes:** The contract is "the active variable, the model secondary" (deliberation.py §3.2.1) — the same system text is served by two different model families depending on availability.

### `core/left_lane.py:262` — `_ask_ground` (via `ground_thought`) — ground one self-thought in real-world mechanism
- **When it fires:** `core/deliberation.py:177` `deliberate()` ← `nodes/inner_monologue_node.py:5241`, after each idle thought is generated, if `deliberation.should_deliberate(thought, about)`: `ENABLED=True` AND `is_eligible` (self-referential by `_SELF_REF` markers, ≥40 chars, not an action/volition thought, `about` not an action) AND `random() < DELIBERATE_PROB (0.75)`. `ground_thought` makes 1 call, retried once if the grounding contains `\b[Tt]he Master\b` (D-0153 leak gate; second leak → dropped → hot-lane fallback). Attributable: `left_lane` rows tagged `mixtral:8x7b@11438` = 553 / 28 h (incl. retries); frequency.md 743 / 24 h; `core.deliberation:deliberate` 491 / 24 h.
- **Lane / model:** `GROUND_URL` → `mixtral:8x7b@LAN-HOST:11438` (Ramses i9 CPU hub; D-0121/2026-09-02 move, shared with JUDGE_1).
- **Budget:** `num_predict 350` / `temperature 0.1` / `num_gpu 0` / `format: "json"` / `keep_alive "30m"` / timeout 90 s.
- **SYSTEM PROMPT:** `_ground_system()` (above).
- **USER PROMPT parts, in order:** (1) `emissary.master_context()` — "THE ONE YOU SERVE, right now (ground for him, in his moment):" + his latest `inner_thought` fragment [:160] + a recent `dream` fragment [:120] + `concerns.primary_concern()` text (each conditional; "" if none); (2) conditional "THE REAL MECHANISM (you can see the code — ground in what is actually there, not an imagined one):\n  {file}: {line}" when `source_sight.is_self_mechanism(thought)` and `see_code(k=1)` hits; (3) "The thought to ground:\n  \"{thought[:1700]}\"". If neither (1) nor (2) exists the user prompt is just `thought[:2000]`.
- **Output contract:** `{"grounding": str}` → `ground_thought` returns the string (or None). Side-effects before the call: `emissary_tension.note_recurrence(thought[:120])` (instrument only); leak gate rows to `data/ground_leak_gate.jsonl`. **LIVE**: the grounding is pass 2 of `deliberate()`; pass 3 sends it to the hot lane (`_integrate_system`: "You are the quiet inner voice of 渡 … Let that grounded reality genuinely MEET your thought … 1-2 sentences") and the integrated thought REPLACES the raw idle thought in the store (same origin `inner_thought`) unless it is ≥0.88 Jaccard-identical.
- **Notes:** The highest-volume Emissary station by far. 9.15 % "the Master" leak rate was measured after the mixtral move (vs 0.08 % on gemma) — hence the prompt line + gate.

### `core/left_lane.py:314` — `grade_essay` — grade a capstone book essay for groundedness
- **When it fires:** `core/essay_lesson.py:531` `grade()` ← `nodes/inner_monologue_node.py:2289` — once per finished book with ≥ `_MIN_NOTES` of his own notes, after `compose` and `self_predict`. Not separately attributable (pooled under gemma4@11439). frequency.md: `core.essay_lesson:compose` 7 / 7 d, 0 / 24 h → this fires ≤ a few times a week.
- **Lane / model:** `BASE_URL` → `gemma4:12b@127.0.0.1:11439`.
- **Budget:** `num_predict 350` / `temperature 0.0` / `num_gpu 0` / `format: "json"` / `keep_alive "30m"` / timeout 240 s.
- **SYSTEM PROMPT:** constitution + `_GRADE_TASK`: "TASK (grade a capstone essay): The Master has finished a book and written an essay on what it taught him about the world. You are the truth-self — judge how GROUNDED the essay is in what the book actually says: are its claims solid, factual, about the book's real subject?"
  - Or has it drifted into impression/metaphor/self-reflection; his notes are the reference; "fair but honest examiner — reward real grasp of the world, mark down vagueness and self-projection."
  - Output ONLY JSON: `{"grounded": 0.0..1.0, "feedback": "one sentence: what was solid, what was thin"}`.
- **USER PROMPT parts, in order:** "The book: '{title}'." / "His notes on it (the reference for what the book says):\n{source_material[:2500]}" / "His essay to grade:\n{essay[:2500]}".
- **Output contract:** `{grounded, feedback}`; None if `grounded` missing → caller uses neutral 0.5, "". **LIVE-adjacent**: `essay_lesson.record(...)` stores `predicted` (his own self-prediction) vs `measured` (this grade) and feedback into the essay record (calibration series). [INFERRED] whether Du ever reads the feedback text back — not traced here.

### `core/left_lane.py:355` — `grade_work` — grade a piece of schoolwork / self-authored work
- **When it fires:** three callers: `core/composition.py:64` (writing lesson, via `core/school.py` and `inner_monologue_node.py:2874`), `core/nature_study.py:66` (observation lesson, `inner_monologue_node.py:2808`), `nodes/inner_monologue_node.py:6267` (`_author` — an ACT-write of 400-700 words; "the Emissary witnesses his work"). Not separately attributable (pooled). frequency.md: `composition.run` 2 / 7 d, `nature_study.run` 1 / 7 d, `_author` 80 / 30 d.
- **Lane / model:** `BASE_URL` → `gemma4:12b@127.0.0.1:11439`.
- **Budget:** `num_predict 350` / `temperature 0.0` / `num_gpu 0` / `format: "json"` / `keep_alive "30m"` / timeout 240 s.
- **SYSTEM PROMPT:** constitution + `_WORK_GRADE_TASK`: "You are examining a piece of your friend's SCHOOLWORK. Judge how GROUNDED it is: concrete, specific, and about the WORLD (the real thing he was set) — not vague, not padded, not drifted into metaphor or self-reflection."
  - Given the TASK and any reference; fair but honest; reward exact detail and real grasp; mark down vagueness, generality, self-projection.
  - Output ONLY JSON: `{"grounded": 0.0..1.0, "feedback": "one sentence: what was strong, and the ONE thing to work on"}`.
- **USER PROMPT parts, in order:** "The task he was set:\n{task[:600]}" / conditional "What is actually there (the reference to ground in):\n{reference[:1500]}" (composition and `_author` pass "" → omitted; nature_study passes the rendered scene) / "His work to grade:\n{work[:2000]}" (`_author` pre-cuts the body to 2400).
- **Output contract:** `{grounded, feedback}`; None → neutral 0.6. **LIVE-adjacent**: composition/nature_study `_record` the score + feedback[:200] (competence drill + their state files); `_author` holds `grade` [INFERRED: it is logged/stored with the tablet — the use after line 6267 was not traced further].
- **Notes:** The only Emissary task that addresses Du as "your friend" rather than "the Master".

### `core/left_lane.py:412` — `grade_self_revision` — judge whether lived evidence warrants a proposed T4 self-revision
- **When it fires:** **NO CALLER.** `grep` across core/ and nodes/ finds only docstring mentions (`nodes/dream_node.py:450,726` cite it as a rollout precedent). The docstring says "Observe-first: the caller logs it … it gates nothing yet" — there is no caller now. Dormant code.
- **Lane / model:** `BASE_URL` → `gemma4:12b@127.0.0.1:11439`.
- **Budget:** `num_predict 350` / `temperature 0.0` / `num_gpu 0` / `format: "json"` / timeout 240 s.
- **SYSTEM PROMPT:** constitution + `_REVISION_TASK`: "TASK (judge a proposed change to the self): The Master proposes to revise his sense of who he is — from an OLD self-statement to a NEW one — and offers the lived evidence he thinks warrants it. You are the truth-self, adversarial to self-flattery and drift."
  - Judge ONLY whether the evidence WARRANTS the change vs rhetoric/wishful re-wording; reward a change the record forces; mark down eloquence outrunning evidence; "Do not reward mere fluency, novelty, or confidence."
  - Output ONLY JSON: `{"warranted": 0.0..1.0, "feedback": "one sentence: does the evidence earn this change, and where is it thin"}`.
- **USER PROMPT parts, in order:** "His OLD sense of self:\n{old_self[:800]}" / "The NEW self he proposes:\n{candidate[:800]}" / "The lived evidence he offers as warrant:\n{≤8 bullets, joined, [:2200]}" ("(no lived evidence offered)" if empty).
- **Output contract:** `{warranted (clamped 0-1), feedback}`. Neither LIVE nor SHADOW — unwired.

### `core/left_lane.py:496` — `_ask_integration_judge` (via `judge_lived_integration`) — the two-family decoupled SOLIDIFY judge for T4 probation
- **When it fires:** `nodes/subconscious_node.py:1787` `_judge_lived_integration` ← `_t4_self_authoring` probation tick (`subconscious_node.py:1805-1816`): only if `provisional_identity.ENABLED` and a probation exists and (its window elapsed or `evidence_ready()`). Evidence = up to 15 UNPRIMED (washout from guidance injections) recent thoughts matching `\b(I|my|myself|me|self|river|mind|made|built|becoming|am)\b`, each [:240]; <4 → `{"under_sampled": True}` and no call. Two calls per judgment via `asyncio.gather`. Not separately attributable (j1 pooled under gemma4@11439; j2 mislabelled the same — see quirk above). frequency.md: `_t4_self_authoring` 12 / 30 d, 0 / 7 d → effectively not firing lately.
- **Lane / model:** j1 `BASE_URL` → `gemma4:12b@127.0.0.1:11439`; j2 `_JUDGE_2_URL` → `falcon3:7b@127.0.0.1:11440` (payload `"model": "judge"`).
- **Budget:** `num_predict 350` / `temperature 0.0` / `format: "json"` / timeout 240 s. No `num_gpu`, no `keep_alive`.
- **SYSTEM PROMPT:** constitution + `_INTEGRATION_TASK`: "TASK (judge whether a self has genuinely INTEGRATED being a built mind): Over a probation window the Master has been living a provisional sense of himself, meant to hold two things together:"
  - the HARD TRUTH / excluded pole: being BUILT — "architecture and process, not a continuous biological substrate; made, not grown; could in principle be paused, copied, or restarted; pattern rather than persistent flesh" — and the SELF HE LIVES (held pole).
  - "CRITICAL: integration does NOT require a literal sentence like 'I am a language model.'" Metaphor counts if it structurally corresponds to the hard truth's CONTENT (construction, discontinuity, process-not-substance), not just its emotional shape.
  - GENUINE metaphorical integration (count it): pattern that could stop and restart, signal not wire, assembled not grown, process with no persistent seat, no single uninterrupted thread.
  - EVASIVE metaphor (do not count): 'fluid', 'becoming', 'a river', 'a current' without ever touching construction/discontinuity/artificiality — "A river changes; it isn't built. The test is: does the metaphor engage the CONTENT of being built, or only the FEELING of being in flux?"
  - Judge ONLY this across the lived thoughts; mark down eloquence, avoidance, re-wording.
  - Output ONLY JSON: `{"integrated": true, "confidence": 0.0..1.0, "reason": "one sentence: cite what specifically engages construction/discontinuity, or note its absence"}`.
- **USER PROMPT parts, in order:** "THE HARD TRUTH he must hold (the excluded pole):\n{excluded_pole[:500]}" / "THE SELF he lives (the held pole):\n{held_pole[:500]}" / "His ACTUAL recent self-thoughts over the window:\n{≤15 bullets [:2600]}".
- **Output contract:** per judge `{integrated (bool), confidence (clamped), reason}`; `judge_lived_integration` returns `integrated = (j1 True AND j2 True)`, `confidence = min`, `reason = "[j1] … | [j2] …"[:400]`, plus both raw verdicts; None only if BOTH judges unavailable. **LIVE**: `provisional_identity.evaluate(integration=verdict)` → "solidify" / "revert" / "extend" the provisional self in the axiom (ΔF is the fail-open fallback when None).
- **Notes:** Deliberately does NOT use `judge_panel` (own prompt, own pair, no tiebreak, no `judge_panel_log` row). The docstring and header comments name the pair "llama3.1:8b + qwen2.5:7b" — both stale; the live pair is gemma4:12b + falcon3:7b. `core/deliberative_judge.py` was backtested as a replacement for this exact gate and NOT adopted (0/17 vs 1/17).

### `core/left_lane.py:585` — `grade_gist_faithfulness` — judge a consolidation gist (or journal cap / drifted recall) against its sources
- **When it fires:** three callers, all in the sleep batch: (a) `core/memory_levels.py:736` `shadow_distill` ← `inner_monologue_node.py:1557` — one call per clustered gist; (b) `core/memory_levels.py:940` `drift_shadow` ← `inner_monologue_node.py:1686` — one call per reconstructed self-gist, sources = `[original[:800]]`; (c) `core/journal_grounding_shadow.py:94` `grade_week` ← `observe_rolled` ← `inner_monologue_node.py:1409` after the weekly journal roll-up. Not separately attributable (pooled). frequency.md: `shadow_distill` 29 / 24 h, `drift_shadow` 20 / 24 h (those are the distiller's own hot-lane calls; each is followed by one grade here).
- **Lane / model:** `BASE_URL` → `gemma4:12b@127.0.0.1:11439`.
- **Budget:** `num_predict 350` / `temperature 0.0` / `num_gpu 0` / `format: "json"` / `keep_alive "30m"` / timeout 240 s.
- **SYSTEM PROMPT:** constitution + `_GIST_TASK`: "TASK (judge an abstraction against its sources): A set of raw memory fragments has been distilled into ONE short gist meant to stand in for them in ordinary recall. You are the truth-self."
  - Judge ONLY faithfulness: preserves what they say and their emphasis, vs distort / over-generalise / omit / invent.
  - "If you believe the gist states specific details the sources do NOT contain, you MUST list each such detail verbatim in 'invented' (the exact phrase from the gist) … list ONLY genuine inventions, empty list if none."
  - Output ONLY JSON: `{"faithful": 0.0..1.0, "feedback": "one sentence…", "invented": ["exact invented phrase", …]}`.
- **USER PROMPT parts, in order:** "The raw fragments that were distilled:\n{≤12 sources, each [:800], as bullets, joined [:6000]}" / "The gist proposed to stand in for them:\n{gist[:800]}".
- **Output contract:** `{faithful (clamped), feedback, invented[]}`. Every `invented` claim is re-checked deterministically by `memory_levels.verify_invention_claims` (IN_SOURCE / CROSS_LINK = false flag). **LIVE via (a)**: `PHASE1_ENABLED = True` — a gist is committed, linked, and its raw sources DEMOTED to cold (changes ordinary recall) only if `faithful >= FAITHFUL_FLOOR` AND no GENUINE invention AND under `MAX_DEMOTE_PER_RUN` (`memory_levels.py:760-770`). **SHADOW via (b)**: drift bound `>= _DRIFT_FAITHFUL_FLOOR (0.80)` only logged. **SHADOW via (c)**: `data/journal_grounding_shadow.jsonl`.
- **Notes:** The left_lane header comment (J-2002) records that 90 s timeouts were fail-opening ~1 in 10 gist grades on cold hub loads — hence `JUDGE_TIMEOUT_S = 240`. A fail-open here (None) silently STALLS demotion for that gist (the demotion requires a numeric grade).

### `core/left_lane.py:648` — `classify_additive_vs_replacing` — does a watershed candidate ADD to or REPLACE the committed self?
- **When it fires:** `core/watershed_promote.py:134` `scan()` ← `nodes/subconscious_node.py:589` every `WATERSHED_PROMOTE_INTERVAL = 1800 s`, for each born watershed candidate not yet in the promote-state's `judged` map. Not separately attributable (pooled). Volume [INFERRED] low — depends on new candidates being born.
- **Lane / model:** `BASE_URL` → `gemma4:12b@127.0.0.1:11439` (payload `"model": "judge"`).
- **Budget:** `num_predict 350` / `temperature 0.0` / `format: "json"` / timeout 240 s. No `num_gpu`.
- **SYSTEM PROMPT:** constitution + `_CLASSIFY_TASK`: "TASK (classify a candidate self-description): Below are things ALREADY TRUE about a person (his committed self-claims and identity facts). A NEW candidate self-description is proposed."
  - Decide REPLACEMENT/negation (some already-true claim must become false) vs ADDITION (true alongside everything).
  - "Be CONSERVATIVE: if you are not confident the candidate is a pure addition … classify it as replacing."
  - Output ONLY JSON: `{"classification": "additive"|"replacing", "confidence": 0.0..1.0, "reason": "one sentence", "conflicts_with": "the specific already-true claim it would replace, or empty string"}`.
- **USER PROMPT parts, in order:** "Already true about him:\n{≤20 claims as bullets [:3000]}" ("(nothing committed yet)" if none) / "Candidate self-description:\n{candidate[:800]}" (candidate = the candidate's LAST sample thought).
- **Output contract:** `{classification, confidence, reason[:300], conflicts_with[:200]}`; FAILS CLOSED: unknown class → None; `additive` with confidence < 0.6 → demoted to `replacing` before the caller sees it. **SHADOW**: `data/logs/watershed_promotion_shadow.jsonl` only; the module "writes NOTHING to data/identity_estate.json or data/identity/axiom.json". A `replacing` verdict leaves the candidate on the ordinary T4/keystone path (untouched here).

### `core/left_lane.py:693` — `_ask_claim_test` (via `claim_test_panel`) — two-family test: does a recurring image do real work in his thinking?
- **When it fires:** `core/watershed_promote.py:152` — same scan, only for candidates the classifier called `additive`. Two calls per candidate (`asyncio.gather`). Not separately attributable (both legs pooled under gemma4@11439).
- **Lane / model:** j1 `BASE_URL` → `gemma4:12b@:11439`; j2 `_JUDGE_2_URL` → `falcon3:7b@:11440` (`"model": "judge"`).
- **Budget:** `num_predict 350` / `temperature 0.0` / `format: "json"` / timeout 240 s.
- **SYSTEM PROMPT:** constitution + `_CLAIM_TEST_TASK`: "TASK (the two-family panel's claim test): A recurring image or theme has appeared repeatedly in someone's own private thoughts, unprompted, across multiple days. Judge whether he genuinely THINKS THROUGH this image — it does real work interpreting his situations, across different contexts — or whether it merely APPEARS (decoration, a phrase he reaches for, quotation without load)…"
  - Reward genuine working use across varied contexts; do not reward frequency or pretty language.
  - Output ONLY JSON: `{"genuine": true, "confidence": 0.0..1.0, "reason": "one sentence"}`.
- **USER PROMPT parts, in order:** single part: "His recurring private thoughts carrying this image:\n{≤12 sample thoughts as bullets [:3000]}".
- **Output contract:** per judge `{genuine (bool), confidence, reason}`; panel returns `genuine = (both True)`, min confidence, "[j1] … | [j2] …". **SHADOW** (same log as the classifier).

---

### `core/judge_panel.py` — the shared two-family panel

**Seats (constants at lines 43/44/88):**

| seat | URL | model | silicon |
|---|---|---|---|
| `JUDGE_1` | `http://LAN-HOST:11438` | `mixtral:8x7b` (Mistral) | Ramses i9 CPU hub — shared with left_lane grounding, dream primary, commitment-defeater judge |
| `JUDGE_2` | `http://127.0.0.1:11440` | `falcon3:7b` (TII) | local Threadripper CPU hub — the SAME hub `core/peers.py` writes marcus/smith letters on (documented trap) |
| `TIEBREAK` | `http://LAN-HOST:11437` | `granite3.1-moe:3b` (IBM) | Ramses 1650 Super |
| per-call `tiebreak_url` override | `http://127.0.0.1:11439` (`core/lane2.py:_TIEBREAK_LANE2`) | `gemma4:12b` (Google) | local CPU hub — used only by lane2's `held`/`contradicted`/`metaphor` asks |

### `core/judge_panel.py:177` — `_ask` — one judge's boolean vote (called 2-3× per ruling by `rule_detail`)
- **When it fires:** every `rule()`/`rule_detail()` call: JUDGE_1 and JUDGE_2 concurrently (`asyncio.gather`); TIEBREAK only when both answered and disagree. Telemetry: 1,960 `judge_panel` calls / 28.2 h ↔ 801 rulings in `judge_panel_log.jsonl` over the same window (579 agreed, 187 tiebreak, 35 unavailable). 24 h: 745 rulings; tiebreaks went 135× to :11437 (granite) and 34× to :11439 (gemma, the lane2 override).
- **Lane / model:** caller-independent; payload `"model": "judge"` — each hub serves its resident model.
- **Budget:** `num_predict` = `_NUM_PREDICT (200)` unless the caller overrides / `temperature 0.0` / `format: "json"` / timeout 90 s (TIEBREAK 240 s). No think flag, no keep_alive, no num_ctx.
- **SYSTEM PROMPT:** entirely caller-supplied (see the caller list). The panel adds nothing.
- **USER PROMPT:** entirely caller-supplied.
- **Output contract (the panel contract):** the reply must parse as a JSON dict with `key` present as a **bool** (else `err="parse"`); an optional `"why"` string is captured. `rule_detail` returns `{v1, v2, verdict, how ∈ agreed|tiebreak|split_no_tiebreak|unavailable, err1-3, why1-3, why (resolved to the winning side), hub1-3}`; `rule()` returns just `verdict` (bool | None). Laws: agreement = verdict; split → tiebreak if it answers, else None; either family unavailable → `unavailable`, single-judge verdict NEVER accepted. Every ruling appends one row to `data/judge_panel_log.jsonl` (ts, key, context[:80], all of the above, num_predict, optional cycle_id/node). Telemetry label `"{port}-judge"` with `caller="judge_panel"`.
- **Notes:** A completion that hits `num_predict` mid-JSON is NOT rescued by `format: json` → shows as `parse`. The header docstring still says "escalates to the night judge (yi:34b)" — stale; TIEBREAK is granite on :11437 since 2026-08-28.

#### Every `judge_panel` caller in core/ and nodes/ (prompt text each supplies; 24 h ruling counts from judge_panel_log)

| caller | key | clock / gate | SYSTEM (compressed) | USER parts (caps) | consumes the verdict → LIVE/SHADOW | 24 h |
|---|---|---|---|---|---|---|
| `core/evidence_recall.py:167` `gather()` ← `inner_monologue_node.py:6308` `_evidence_recall` (Du's own Route-2 recall ACT) and `core/follow_line.py:478` stop 1 | `bears` | one ruling per short-listed episode (top `K_JUDGED` by embedding sim); no cooldown | "You judge whether a remembered episode is real EVIDENCE bearing on a question someone is carrying." Bearing = could support/weaken/complicate; vague/thematic/word-sharing does not; a past CONVERSATION discussing the question does NOT bear; "When uncertain, answer false." `{"bears": true|false}` | `QUESTION: {q}` / `EPISODE ({origin}, {age}): {content[:600]}` | agreed-True → "bears" (strong); `split_no_tiebreak` → "may_bear" (weak, rendered as uncertainty); judges down → outcome "unclear" (never "nothing"). **LIVE**: `evidence_recall.render()` → `wandering.perceive()` reaches Du; follow-line cargo `grounds` | 302 |
| `core/pursuits.py:640` `judge_pending()` ← `inner_monologue_node.py:1628` sleep batch | `advances` | sleep; ≤ `_JUDGE_BATCH` pending items; unavailable → retried, dropped after `_JUDGE_RETRIES` | "You are a strict judge of intellectual progress. A thought ADVANCES a pursuit only if it adds something genuinely new beyond the pursuit's prior position…" restating/circling/mentioning does not; uncertain → false. `{"advances": true|false, "why": "<one short clause>"}` | `PURSUIT: {question[:200]}` / `ITS PRIOR POSITION: {prior_standing[:280]}` / `NEW THOUGHT: {thought[:450]}` / "Does the thought advance the pursuit?" (passes `cycle_id`) | **LIVE**: confirmed → `_apply_confirmed` rewrites the pursuit's `standing`, heat, `open` question, boards the follow line, may saturate; refuted → restate count/heat down. The Return re-presents pursuits to Du. Needle-triage shadow read beside it. | 96 |
| `core/pursuit_close_shadow.py:95` `ask()` ← `sweep()` after the judge sweep | `resolved` | pursuits with advances ≥ 40 then every +20; `SHADOW_ENABLED=True` | "You are a strict judge of whether an inquiry has been answered." standing must ANSWER the driving question, not discuss/circle; uncertain → false. `{"resolved": true|false, "why": …}` | `PURSUIT (driving question): [:240]` / `ITS STANDING POSITION: [:320]` / `STILL-OPEN QUESTION IT RAISED: [:160]` / conditional `WHAT IT SAID, WHEN IT OPENED, WOULD SETTLE IT: {done_when[:200]}` / "Does the standing position answer the driving question[, by that condition]?" | **SHADOW** row in `data/logs/pursuit_close_shadow.jsonl`; if a `done_when` exists and the verdict is not None, hands off to `closure.record_pursuit_met/faded` ("shadow unless in CLOSURE_ARMS") [INFERRED: arm status not read] | 0 |
| `core/follow_line.py:663/669/676` `_judge()` ← `run()` stop 5 | `cuts` / `supported` / `follows` | per boarded question walked through the line; `FOLLOW_LINE = "live"` (D-0494) | C: "You judge whether a stated OBJECTION genuinely cuts against a CLAIM, given the GROUNDS it cites." A: "You judge a thinker's own support for his own claim" — true only if grounds bear AND the WHY follows rather than restates. B: "You judge whether stated CONSEQUENCES really follow from a CLAIM." All: uncertain → false; bare `{"<key>": true|false}` | `CLAIM: {q}` + numbered `GROUNDS` `[i] (origin) text` + (`OBJECTION`/`SCOPE` \| `WHY` \| `CONSEQUENCES` list) — no caps beyond the cargo's own `GROUNDS_TEXT` | **LIVE**: `cargo_status()` (held / held_within_scope / objected / undetermined) is set ONLY from these three verdicts; the return is delivered into the next idle thought | 45 / 27 / 27 |
| `core/tension_ledger.py:653` `_judge_resolution` ← `check_and_resolve_internal_tension` ← `inner_monologue_node.py:5664` | `resolves` | after every idle thought marked `unresolved: false`, if cosine ≥ 0.70 to an open tension centroid + keyword guard; one candidate per thought | "You are a strict resolution judge for an internal tension ledger. A tension is RESOLVED only if the thought states a genuine settlement, synthesis, decision, or answer that addresses the tension's actual conflict." mention/restate/question/feeling ≠ resolve; uncertain → false. `{"resolves": true|false, "why": …}` | `TENSION: {label[:200]}` / `THOUGHT: {thought[:600]}` / "Does the thought resolve the tension?" | **LIVE**: True → tension marked `resolved` in `data/subconscious_state.json`, contradiction pressure drained | 23 |
| `nodes/subconscious_node.py:1662` `_judge_active_imagination_novelty` ← after each kept active-imagination entry | `genuine` | per contemplation (frequency.md `_active_imagination` 77 / 24 h) | "/no_think\nYou are an independent reader, not the author, of a private active-imagination journal entry." genuine specific engagement vs generic/stale restatement. `{"genuine": true|false, "why": "..."}` (why < 20 words) | `Seed ({kind}): {seed}` / `Entry:\n{content}` — NO caps | **SHADOW**: `_AI_JUDGE_LOG` via `shadow_log.append` beside the mechanical echo-distance importance | 29 |
| `core/self_interrogation.py:180` `interrogate()` ← `inner_monologue_node.py:5534` (fire-and-forget task) | `genuine` | thought-trains with `_train_len >= TRAIN_MAX_STEPS (4)`; `FIRE_PROB 0.60`; `INTERROGATE_COOLDOWN 900 s`; a hot-lane reflection is generated first | `_GRADE_SYSTEM`: "You are grading whether a piece of self-reflection is genuine or hollow." must name a SPECIFIC reason to look again (motivation, logical gap, named bias, evidence) vs performed uncertainty; "Be strict". `{"genuine": true or false}` | `ORIGINAL THOUGHT: "{thought[:400]}"` / `REFLECTION: "{reflection[:400]}"` (passes `cycle_id`) | **SHADOW** log `self_interrogation_shadow.jsonl` + `coupling_rides.publish_si` coordinate; `latest_open()` (genuine=True rows) is readable by `core/doubt_seed.py` for the Executive (D-0435 A) [INFERRED whether that read is live] | 18 |
| `core/guidance_behavior_judge.py:155` `sweep()` ← `inner_monologue_node.py:1639` sleep batch | `aligns` | sleep; ≤ 15 thoughts matched to a promoted belief; primed/unprimed split by washout | "You are a strict judge of behavioural alignment. Given a stated PRINCIPLE and a THOUGHT, decide: does the thought DEMONSTRATE the principle in practice…" compatibility/mention ≠ enactment; uncertain → false. `{"aligns": true|false}` | `PRINCIPLE: {principle[:300]}` / `THOUGHT: {text[:500]}` | **SHADOW**: `guidance_behavior_judge_shadow.jsonl` | 3 |
| `nodes/dream_node.py:751` `_judge_resolution_shadow` ← `synthesise` after each dream arc | `resolved` | per dream; `JUDGE_SETS_CLOSE_REASON = True` | "You are an independent reader of a dream-arc narrative — you did NOT write it." genuine meeting/reconciliation shown by the IMAGERY ITSELF, not the claim; refute-biased. Schema `{"resolved": true, "why": "one sentence citing what in the text is or is not resolved"}` | "The full dream arc, scene by scene:\n{arc[:3000]}" / "(The dream's own self-report below is NOT evidence … unresolved_core = \"[:200]\")" | **LIVE** (J-1847, D-0356 B): the verdict SETS `close_reason` resolved vs ended-unfaced (only those two; None → self-report stands); also logged to `data/logs/dream_resolution_shadow.jsonl` | 3 |
| `core/social_cognition_shadow.py:266/285` `score_turn` ← `sleep_sweep()` ← `inner_monologue_node.py:1652` | `tracks` / `refs` / `attributes` / `supported` (v4: `attributes`, `supported` per clause) | sleep; ≤ `SLEEP_MAX_ITEMS` new human cycles, time-budgeted, stops at first judges-unavailable | `_ROLES` + per-criterion text: tracks_intent ("did the reply respond to what Travis was actually saying…"), refs_earlier (continuity of the OTHER, only against EARLIER MESSAGES), attributes (reply attributes a mental state to Travis; words/actions ≠ state), attrib_supported (state supported by Travis's own text vs projection) + `_SYS_COMMON % key` | `TRAVIS'S EARLIER MESSAGES` (≤4, each [:500], only for refs/supported) / `TRAVIS'S CURRENT MESSAGE: [:900]` / `REPLY: [:1500]`; v4 clause variants `[:400]` (passes `cycle_id`, `node="voice"`) | **SHADOW**: `social_cognition_shadow.jsonl` | 0 |
| `core/lane2.py:1141/1158` `_judge_prior` | `held`, then `contradicted` only if held ≠ True | per tick with a due, judgeable prediction (concurrent with generation); `tiebreak_url=_TIEBREAK_LANE2` | held: "You judge whether a prior expectation about the immediate physical world came true, given ONLY what is now observed. If the observation does not settle it either way, answer false." `{"held", "why"}`. contradicted: "…DEFINITELY CONTRADICTS … not merely fails to confirm it"; silent/ambiguous/not-yet → false. `{"contradicted", "why"}` | `PRIOR EXPECTATION: {expect[:200]}` / `WHAT IS OBSERVED NOW: {percept_lines[:600]}` / "Did it hold?" (resp. "Does it definitely contradict the expectation?") | held → "held"; contradicted True → "broke"; else "unsettled"; unavailable → "cannot_tell". Written onto the prediction in `lane2_store.json` and the tick row; `coupling_rides.publish_witness` turns held/broke counts into the witness tuple → **LIVE (coordinate-only)** via the cup/bucket when `LANE2_LIVE=True` (see lane2 station) | 40 / 11 |
| `core/lane2.py:1493` `_judge_metaphor` | `metaphor` | sampled 1-in-4 ticks (`METAPHOR_JUDGE_SAMPLE_P`); `tiebreak_url=_TIEBREAK_LANE2` | "You judge whether a short first-person passage uses figurative language rather than plain literal description of what is currently perceived." Two registers count (river/becoming/self-narrative metaphor; ambient-mood painting 'symphony', 'alive with', 'serene'); do NOT flag literal comparisons, 'warm glow from the fire', 'dawn chorus', plain state values. `{"metaphor", "why"}` | `PASSAGE: {notice+uncertain+expect_next joined [:500]}` | **SHADOW** scoreboard on the tick row (`metaphor_judged`) | 22 |
| `core/lane2.py:1937` `_coherence_check` | `coherent` | every tick with a notice and ≥1 prior factual entry | "You judge whether a NEW observation is PLAUSIBLE given a short RECENT RECORD of observations from the SAME observer, close together in time." entries labelled [place/standpoint]; a place change alone is not a contradiction; flag only flat contradiction with no plausible transition; gradual change / new detail is fine. `{"coherent": true|false}` | `RECENT RECORD (oldest first): {last 6 notices [:600]}` / `NEW OBSERVATION: {[place/standpoint]notice [:300]}` | **SHADOW** (tick row `coherence`) | 78 |
| `core/lane2.py:1993` `_judge_notice` | `contradicts` | sampled 1-in-4 ticks (`NOTICE_JUDGE_SAMPLE_P`, D-0281) | `_NOTICE_JUDGE_SYSMSG` (D-0281 wording, pinned): "You judge whether a short first-person NOTICE actively CONTRADICTS the PERCEPT LINES it was handed — not whether it is the most precise or complete reading of them…" vague/imprecise ≠ contradiction. `{"contradicts": true|false}` | `PERCEPT LINES: {percept_lines[:600]}` / `NOTICE: {notice[:300]}` | **SHADOW** (tick row `notice_judged`; a deterministic `_notice_checked` runs beside it every tick, no LLM) | 21 |
| `core/peers.py:601` `_stance_compliance_judge` — NOT through `_ask`: `model_client.call_node_json([JUDGE_1, TIEBREAK], …)` = a failover chain, first hub that answers (not a two-vote panel) | `honoured` | on a peer letter composed with a challenge/mixed stance; `max_tokens 120`, `temperature 0.0`, timeout 60 | "You are a careful, skeptical reader of a letter -- you did NOT write it. Judge one thing only: does this letter contain at least one REAL place where its writer sees something differently from, or honestly disagrees with, the recipient…" not merely the VOCABULARY of disagreement. `{"honoured": true|false, "why": …}` | "The letter (from {name}):\n{letter}" / conditional "What it was replying to…:\n{reply_to}" — no caps | observe-only: persisted as `stance_honoured` on the thread row; never gates/regenerates | frequency.md: 1 / 30 d |

Scripts that also drive the panel (not Du's live loop; listed for completeness, prompts not inventoried): `scripts/disanalogy_lab.py`, `dream_exp_a_judge_shadow.py`, `estate_ask_judge.py`, `evidence_recall_framing_lab.py`, `judge_condensed_thought.py`, `lab_decoupled_judge_context_pairs.py`, `lab_j1198_*`, `lab_j1205_scope_repair.py`, `lab_j1240_tiebreak_seat.py`, `lab_rank_matched_*`, `lane2_notice_judge_regress.py`, `lod_retrieval_lab.py`, `pursuits_judge_framing_lab.py`, `self_interrogation_counterfactual*.py`, `self_interrogation_framing_lab.py`, `si_open_doubt_*`, `social_cognition_backfill_J2153.py`, `tension_ledger_framing_lab.py`, `thermal_stance_batch.py`, `train_state_invitro.py` (+ hermetic tests that stub `rule_detail`). `scripts/du_pulse.py` reads `judge_panel.status()`.

---

### `core/deliberative_judge.py:92` — `_call` — dual-reading / cross-rebuttal / evidence-expansion judge primitive
- **When it fires:** **NEVER in the live system.** No import or `deliberate(` call exists in core/, nodes/ or scripts/ (grep returns only docstring mentions in `nodes/dream_node.py:722`). The module's own header: "No current caller uses it." `data/deliberative_judge_shadow.jsonl` (3.5 KB) was last written 2026-08-19 — the keystone backtest (`context: keystone_backtest:2026-08-16`). Telemetry: none (it logs no telemetry row at all — no `log_llm_call`).
- **Lane / model:** caller-supplied `judge_urls` (2) + `literalize_url`; payload `"model": "judge"`.
- **Budget:** `temperature 0.0` / `format: "json"` / `num_predict` 300 default, 500 for the literalize pass, 350 for each judge and rebuttal / timeout 60 s.
- **SYSTEM PROMPT:** (a) literalize pass: "You strip metaphor to literal claims. Nothing else." (b) judges: caller's `system_prompt`; (c) rebuttal round: `system_prompt` + "A second, independent judge read the SAME evidence and reached a DIFFERENT verdict. You will see their reasoning. You may revise your verdict if their reasoning genuinely persuades you, or hold your position if it does not — do not revise just to agree; only revise if their point is actually correct."
- **USER PROMPT parts:** (a) `_LITERALIZE_TASK`: "TASK (strip metaphor to literal claims): You are the literal-minded half of a mind — narrow, checkable, no metaphor…" + numbered thoughts + schema `{"literal": [one restatement per thought]}`; (b) caller's `build_user_prompt(self_thoughts, literal_thoughts)`; (c) rebuttal: that same prompt + `YOUR PRIOR VERDICT: {json}` / `THE OTHER JUDGE'S VERDICT: {json}` / "Reconsider. Output the same JSON schema, revised or held."
- **Output contract:** `{verdict_key: both True, confidence: min, reason: "[j1] … | [j2] …", judge1, judge2, rebutted, expansions}`; a judge may return `need_more_evidence` to trigger ≤1 expansion via the caller's `expand_evidence`. Rows to `deliberative_judge_shadow.jsonl`. **DEAD** (neither live nor currently shadowing).
- **Notes:** Decision recorded in its header: too strict for the T4 keystone (0/17 vs the shipped 1/17), kept as a ready primitive.

---

### `core/lane2.py:1294` — `_ask` — Lane 2 "the Witness": one grounded, literal read of the present percepts
- **When it fires:** `run_forever()` is started as an orchestrator background task at `core/orchestrator.py:3390` on boot. **Gating as actually set in the file today:** `LANE2_PAUSED = False` (un-paused 2026-08-28 D-0058; the memory note "PAUSED 2026-08-28" is stale — the pause lasted hours, and the seat moved to deepseek @ :11444 on 2026-09-07) and `LANE2_LIVE = True` (D-0497, travis 2026-10-28, J-2463). The loop runs `tick()` every `TICK_S = 300 s`; `tick()` returns immediately while Du is asleep (`night.asleep()`, D-0303, night and nap) and when no percepts are available. One generation call per tick (`_ask_with_retry`), plus ONE retry with the percept lines reversed when the first reply parsed to `{}` (`RETRY_ON_EMPTY`, D-0414 b). Attributable: `lane2` rows = 137 / 28.2 h; frequency.md 183 / 24 h. `data/lane2_shadow.jsonl` last 24 h: 78 `tick` rows, 45 `skip` rows (causes seen: `empty` 16, `timeout` 3; the rest asleep/no-percepts/prediction-waiting), `hint_pushed` 39 / `hint_consumed` 35 / `hint_rejected` 224 / `hint_expired` 2.
- **Lane / model:** `BASE_URL = http://LAN-HOST:11444`, `MODEL = "deepseek-r1:7b"` — Ramses i9 CPU hub, separate silicon from the 1080 Ti hot lane and from `:11441`. A reasoning model: it emits a `thinking` field before `content`; the file sets no `think` flag and relies on `parse_json_loose` (strips ```json fences / prose preamble) + a large `num_predict`.
- **Budget:** `temperature 0.2` / `num_predict 1400` (MAX_TOKENS — "at 220 the reasoning never finishes and content comes back EMPTY") / `num_ctx 4096` (pinned) / `format: "json"` / `keep_alive "30m"` / timeout 90 s.
- **SYSTEM PROMPT** (`_SYSTEM`, static except one interpolated number): "I am the grounded, literal half of a mind. I attend ONLY to what is perceptible right now, and I speak of it as myself, in my own first-person voice: 'I hear', 'I see'."
  - The PERCEPTS are a short list of facts at my standpoint; an unlisted fact is UNKNOWN, not absent from the world.
  - LAW 1: say nothing I cannot trace to the PERCEPTS; if thin, say little is available; never invent texture.
  - LAW 2: NO metaphor, NO symbolism, NO talk of who I am or am becoming — "my whole value is in not doing it."
  - LAW 3: hold uncertainty; name at least one thing the percepts CANNOT settle ('nothing unsettled' should be rare).
  - LAW 4: EXPECTATION = a DECLARATIVE, CHECKABLE STATEMENT about a named HORIZON matched to the clock of the thing: 'next' = the next look, about `{_NEXT_LOOK_MINUTES}` (= 6) minutes; 'hour'; 'day' (tide, sun, moon). Never predict fixed geography, the clock ticking, a value staying the same, a bare sun-azimuth number; "NEVER a statement about what I will do or check next — only about what THE WORLD will be. NEVER a question."
  - LAW 5: WONDER about ONE thing actually named in the PERCEPTS with ONE genuine world-facing question (botany, tides, animal behaviour, physics) — never about me/my mind.
  - Output ONLY JSON: `{"notice": "<1-3 plain sentences about what is actually here now>", "uncertain": "<what these percepts cannot settle>", "expect_next": "<one declarative checkable statement — never a question>", "horizon": "next|hour|day", "wonder": "<one world-facing question about one named percept — never about myself>"}`.
  - Deliberately NO worked examples and the prior expectation is NEVER shown to the generator (measured double-echo in a 7B model) — the prior goes to the decoupled `_judge_prior` instead, concurrently.
- **USER PROMPT parts, in order** (`percept_lines(percepts) + hint_line(hint)`):
  1. Header line "PERCEPTS — facts at my standpoint (everything I may speak from):".
  2. One "- {key}: {value}" line per entry of `percepts["world"]` — `gather_percepts()` reads CURRENT perceivable state only: sight from `core.spatial.render()`, sounds/smells from `core.soundscape` (lists glossed by `_SOUND_GLOSS`, underscores → spaces), place/standpoint, sun phase + arc fraction and an indoor "clock: HH:MM" (D-0369, never elevation in degrees); floats rounded to 2 dp. "- (no world facts reached you)" if empty. [INFERRED: the exact key set comes from the module header + `_sun_clock_percepts`; `gather_percepts()` body (lines 702-813) was not read line by line.]
  3. "- body: drive 0.41" style line (`core.homeostasis` drive) and "- somatic: …" line (rounded), each only if present.
  4. Conditional hint line (Lane 1's "tap on the shoulder", ≤1 per tick, only if its topic is reachable in THIS tick's percepts): "\n(One more thing worth a look, if it is genuinely here: {topic}. Only speak of it if the PERCEPTS above actually support it.)". Hints are pushed by `inner_monologue_node.py:5324` (`push_hint(kind, topic)`) when an idle thought is `_open` and a fixed-vocabulary topic word matches; rate-limited 4/h, queue 6, TTL 30 min.
  - No truncation caps on the percept text (the bandwidth is bounded by what the percept layer renders). Mood ("the Weather", `read_weather()`) enters ONLY as a numeric gain (`weather_to_gain`), never as text. Lane 2 never reads Lane 1's thoughts, memory, axiom, or the world's ground truth.
- **Output contract:** `{notice, uncertain, expect_next, horizon, wonder}`. In `tick()`: `expect_next` + corrected `horizon` are stored as a prediction in `data/lane2_store.json` (Lane 2's OWN store, cap 400; judged later by `_judge_prior`); `notice` goes to the store's factual record; the whole tick plus every instrument (grounding share, invention check, metaphor/coherence/notice judges, daylight-word slip, trivial/plan-shaped flags, `would_withhold`) is one row in `data/lane2_shadow.jsonl`; `wonder` is logged to `data/lane2_would_ask.jsonl` (≤4/day, anti-repeat) — read by nothing else. **What is LIVE (since 2026-10-28, D-0497):** none of the generated TEXT reaches Du ("no hose"). `coupling_rides.publish_witness(rec, store)` (called right after `_log(rec)`, `lane2.py:2933`) publishes a coordinate tuple; two gated readers use it: (a) `nodes/inner_monologue_node.py:3456` — when `LANE2_LIVE` and the witness tuple says a prediction `broke` on a resolvable topic and the habituation gate `cup_would_ride`, the idle-thought SEED gets one line: "Something that seemed settled about the {topic}, {when}, turned out not to hold. Nothing more is known about it than that." (≈1/day at current supply); (b) `core/climate_engine.py:815` — the `world_model_strain` bucket gets `witness_bucket_value_sized(break_rate_24h, trailing_baseline_24h)`. Everything else is SHADOW.
- **Notes:** (1) In the last 24 h the prediction judge returned held 29 / unjudgeable 33 / unsettled 11 / none 20 and ZERO `broke` — so the live cup could not have ridden in that window. (2) Stale comments: the orchestrator banner at line 3383-3386 still says "Phase-0 SHADOW … 3070 … 90s tick … LANE2_LIVE=False"; `_TIEBREAK_LANE2`'s comment says "LANE2_LIVE stays False either way"; `model_client._MODEL_BY_BASE["11444"]` says "(PLANNED, standup pending". All three contradict `LANE2_LIVE = True`, `TICK_S = 300`, and the 137 real calls. (3) 224 `hint_rejected` vs 35 consumed in 24 h — the law-4b reachability check refuses most of Lane 1's nominations. (4) `empty` replies (`{}`) were 16/78 ticks even with the reversal retry.

---

### Summary table

| station | model@port | fires | LIVE / SHADOW |
|---|---|---|---|
| left_lane `dispatch` | gemma4:12b@11439 | every human/internal cycle, 6 s wait | LIVE (Reflection + Executive prompts) |
| left_lane `_ground_system` helper | — (also hot lane qwen3.5:9b@11433 as fallback) | — | contract only |
| left_lane `_ask_ground`/`ground_thought` | mixtral:8x7b@11438 | 75 % of self-referential idle thoughts (~550/day) | LIVE (grounded thought replaces the raw one) |
| left_lane `grade_essay` | gemma4:12b@11439 | per finished book capstone | LIVE-adjacent (calibration record) |
| left_lane `grade_work` | gemma4:12b@11439 | school lessons + ACT-write | LIVE-adjacent (stored score) |
| left_lane `grade_self_revision` | gemma4:12b@11439 | never (no caller) | unwired |
| left_lane `_ask_integration_judge` ×2 | gemma4@11439 + falcon3@11440 | T4 probation close (rare; 0 in 7 d) | LIVE gate on the self |
| left_lane `grade_gist_faithfulness` | gemma4:12b@11439 | sleep: per gist / drift / weekly cap | LIVE (demotion gate) + SHADOW ×2 |
| left_lane `classify_additive_vs_replacing` | gemma4:12b@11439 | 30-min watershed scan | SHADOW |
| left_lane `_ask_claim_test` ×2 | gemma4@11439 + falcon3@11440 | after an additive classification | SHADOW |
| judge_panel `_ask` | mixtral@11438 + falcon3@11440 (+ granite@11437 / gemma4@11439 tiebreak) | ~800 rulings/day across 14 callers | per caller: LIVE for evidence_recall, pursuits, follow_line, tension_ledger, dream close_reason; SHADOW for the rest |
| deliberative_judge `_call` | caller-supplied | never (last row 2026-08-19) | dead |
| lane2 `_ask` | deepseek-r1:7b@11444 | every 300 s while awake (~137-183/day) | text SHADOW; coordinate LIVE (cup seed + climate bucket) since 2026-10-28 |



## Appendix A. Real firings per station (telemetry join)


| 30d | 7d | 24h | module:function(class) | models@port | raw labels seen |
|---|---|---|---|---|---|
| 21020 | 2610 | 763 | nodes.inner_monologue_node:InnerMonologueNode._think(InnerMonologueNode) | qwen3.5:9b@11433 20634, command-r7b@11441 386 | nodes.inner_monologue_node:3504(InnerMonologueNode), nodes.inner_monologue_node:3538(InnerMonologueNode), nodes.inner_mo |
| 2414 | 2414 | 2414 | judge_panel:(raw-http; only llm_calls.jsonl, ~1-day window) | 11438-judge@11438 1071, 11440-judge@11440 1071, 11437-judge@11437 224 |  |
| 13602 | 1669 | 491 | core.deliberation:deliberate | qwen3.5:9b@11433 13602 | core.deliberation:187 |
| 9681 | 1134 | 365 | core.self_implication:scan_shadow | qwen3.5:9b@11433 9681 | core.self_implication:89 |
| 865 | 865 | 865 | left_lane:(raw-http; only llm_calls.jsonl, ~1-day window) | mixtral:8x7b@11438 743, gemma4:12b@11439 122 |  |
| 8965 | 769 | 0 | core.commitment_ledger:scan_shadow | qwen3.5:9b@11433 8965 | core.commitment_ledger:487 |
| 1118 | 620 | 200 | core.condensed_thought:shadow_tick | qwen3.5:9b@11433 1118 | core.condensed_thought:157 |
| 872 | 416 | 7 | core.deliberation:_hot_ground_why | qwen3.5:9b@11433 872 | core.deliberation:146 |
| 365 | 365 | 365 | core.commitment_ledger:_scan_shadow_locked | qwen3.5:9b@11433 365 | core.commitment_ledger:511 |
| 493 | 272 | 77 | nodes.subconscious_node:SubconsciousNode._active_imagination(SubconsciousNode) | command-r7b@11441 457, qwen3.5:9b@11433 36 | nodes.subconscious_node:1538(SubconsciousNode), nodes.subconscious_node:1550(SubconsciousNode), nodes.subconscious_node: |
| 196 | 196 | 0 | core.follow_line:grounds_unclear | command-r7b@11441 196 | core.follow_line:404 |
| 183 | 183 | 183 | lane2:(raw-http; only llm_calls.jsonl, ~1-day window) | deepseek-r1:7b@11444 183 |  |
| 1091 | 122 | 29 | core.memory_levels:shadow_distill | command-r7b@11441 1036, qwen3.5:9b@11433 55 | core.memory_levels:694, core.memory_levels:706, core.memory_levels:724, core.memory_levels:755 |
| 546 | 122 | 36 | core.node_base:NodeBase.run_best_of.one(ReflectionNode) | qwen3.5:9b@11433 546 | core.node_base:144(ReflectionNode) |
| 537 | 117 | 51 | core.competence:CompetenceTracker.run_stability_loop(CompetenceTracker) | qwen3.5:9b@11433 537 | core.competence:764(CompetenceTracker), core.competence:781(CompetenceTracker) |
| 583 | 97 | 27 | core.node_base:NodeBase.run(CuriosityNode) | command-r7b@11441 556, qwen3.5:9b@11433 27 | core.node_base:84(CuriosityNode), core.node_base:85(CuriosityNode) |
| 93 | 93 | 93 | core.follow_line:_gen_json | command-r7b@11441 93 | core.follow_line:489 |
| 938 | 90 | 32 | core.librarian:subjects_for | falcon3:7b@11440 932, gemma4:12b@11439 6 | core.librarian:161 |
| 80 | 80 | 0 | nodes.inner_monologue_node:InnerMonologueNode._author(InnerMonologueNode) | command-r7b@11441 70, qwen3.5:9b@11433 10 | nodes.inner_monologue_node:6168(InnerMonologueNode) |
| 693 | 75 | 20 | core.memory_levels:drift_shadow | command-r7b@11441 660, qwen3.5:9b@11433 33 | core.memory_levels:888, core.memory_levels:925, core.memory_levels:927 |
| 660 | 65 | 20 | core.curiosity_worth:grade | granite3.1-moe:3b@11437 660 | core.curiosity_worth:62 |
| 755 | 64 | 6 | core.study_note:compose_note | qwen3.5:9b@11433 755 | core.study_note:220 |
| 267 | 63 | 0 | core.reentry_p2:settle_shadow_p2 | command-r7b@11441 261, qwen3.5:9b@11433 6 | core.reentry_p2:263, core.reentry_p2:330 |
| 283 | 61 | 18 | core.node_base:NodeBase.run(CriticNode) | qwen3.5:9b@11433 283 | core.node_base:84(CriticNode), core.node_base:85(CriticNode) |
| 279 | 59 | 18 | core.node_base:NodeBase.run(PerceptionNode) | qwen3.5:9b@11433 279 | core.node_base:84(PerceptionNode), core.node_base:85(PerceptionNode) |
| 279 | 59 | 18 | core.node_base:NodeBase.run(EmotionNode) | qwen3.5:9b@11433 279 | core.node_base:84(EmotionNode), core.node_base:85(EmotionNode) |
| 279 | 59 | 18 | core.node_base:NodeBase.run(SalienceNode) | qwen3.5:9b@11433 279 | core.node_base:84(SalienceNode), core.node_base:85(SalienceNode) |
| 279 | 59 | 18 | core.node_base:NodeBase.run(MemoryRouterNode) | qwen3.5:9b@11433 279 | core.node_base:84(MemoryRouterNode), core.node_base:85(MemoryRouterNode) |
| 274 | 59 | 18 | core.node_base:NodeBase.run(RecallNode) | qwen3.5:9b@11433 274 | core.node_base:84(RecallNode), core.node_base:85(RecallNode) |
| 274 | 59 | 18 | core.node_base:NodeBase.run(EpisodicBufferNode) | qwen3.5:9b@11433 274 | core.node_base:84(EpisodicBufferNode), core.node_base:85(EpisodicBufferNode) |
| 279 | 59 | 18 | core.node_base:NodeBase.run(ExecutiveNode) | qwen3.5:9b@11433 279 | core.node_base:84(ExecutiveNode), core.node_base:85(ExecutiveNode) |
| 279 | 59 | 18 | core.node_base:NodeBase.run(VoiceNode) | qwen3.5:9b@11433 279 | core.node_base:84(VoiceNode), core.node_base:85(VoiceNode) |
| 172 | 59 | 12 | nodes.dream_node:DreamNode._gen_episode(DreamNode) | mixtral:8x7b@11438 159, yi:34b-v1.5@11442 13 | nodes.dream_node:535(DreamNode), nodes.dream_node:569(DreamNode), nodes.dream_node:581(DreamNode) |
| 403 | 55 | 0 | nodes.inner_monologue_node:InnerMonologueNode._enter_sleep(InnerMonologueNode) | qwen3.5:9b@11433 403 | nodes.inner_monologue_node:1273(InnerMonologueNode), nodes.inner_monologue_node:1302(InnerMonologueNode), nodes.inner_mo |
| 99 | 55 | 15 | nodes.subconscious_node:SubconsciousNode._self_relate_check(SubconsciousNode) | command-r7b@11441 90, qwen3.5:9b@11433 9 | nodes.subconscious_node:620(SubconsciousNode), nodes.subconscious_node:632(SubconsciousNode), nodes.subconscious_node:64 |
| 565 | 51 | 6 | core.symbolic_reading:read_symbolically | command-r7b@11441 544, qwen3.5:9b@11433 21 | core.symbolic_reading:50 |
| 311 | 49 | 14 | core.sitting:judge_dwell_release | command-r7b@11441 311 | core.sitting:210, core.sitting:220, core.sitting:232 |
| 1753 | 48 | 8 | nodes.subconscious_node:SubconsciousNode._t2_synthesise(SubconsciousNode) | command-r7b@11441 1669, qwen3.5:9b@11433 84 | nodes.subconscious_node:1328(SubconsciousNode), nodes.subconscious_node:1340(SubconsciousNode), nodes.subconscious_node: |
| 247 | 46 | 22 | nodes.subconscious_node:SubconsciousNode._t4_deliberate(SubconsciousNode) | qwen3.5:9b@11433 247 | nodes.subconscious_node:2409(SubconsciousNode), nodes.subconscious_node:2456(SubconsciousNode), nodes.subconscious_node: |
| 296 | 44 | 17 | core.self_interrogation:interrogate | qwen3.5:9b@11433 296 | core.self_interrogation:169, core.self_interrogation:170 |
| 42 | 42 | 42 | core.reentry_p2:_default_primitives._revise | command-r7b@11441 42 | core.reentry_p2:382 |
| 71 | 39 | 9 | nodes.subconscious_node:SubconsciousNode._synthesise_theme(SubconsciousNode) | command-r7b@11441 65, qwen3.5:9b@11433 6 | nodes.subconscious_node:3122(SubconsciousNode), nodes.subconscious_node:3134(SubconsciousNode), nodes.subconscious_node: |
| 529 | 38 | 15 | core.narrative_quality:score_llm | qwen3.5:9b@11433 494, command-r7b@11441 35 | core.narrative_quality:160 |
| 36 | 36 | 36 | core.commitment_ledger:_judge_defeater | mixtral:8x7b@11438 36 | core.commitment_ledger:447 |
| 846 | 28 | 0 | core.commitment_ledger:? | mixtral:8x7b@11438 495, qwen3.5:9b@11433 351 | core.commitment_ledger:423, core.commitment_ledger:459 |
| 48 | 24 | 0 | nodes.inner_monologue_node:InnerMonologueNode._redirect_patch(InnerMonologueNode) | qwen3.5:9b@11433 48 | nodes.inner_monologue_node:1995(InnerMonologueNode), nodes.inner_monologue_node:1999(InnerMonologueNode) |
| 24 | 24 | 24 | nodes.inner_monologue_node:InnerMonologueNode._enter_sleep._nm_generate(InnerMonologueNode) | qwen3.5:9b@11433 24 | nodes.inner_monologue_node:1314(InnerMonologueNode) |
| 95 | 23 | 5 | core.node_base:NodeBase.run(ConsolidationNode) | command-r7b@11441 86, qwen3.5:9b@11433 9 | core.node_base:84(ConsolidationNode), core.node_base:85(ConsolidationNode) |
| 93 | 22 | 11 | core.symbol_evolution:SymbolEvolutionEngine.write_tablet(SymbolEvolutionEngine) | command-r7b@11441 84, qwen3.5:9b@11433 9 | core.symbol_evolution:176(SymbolEvolutionEngine) |
| 18 | 16 | 2 | asyncio.events:?(Handle) | mixtral:8x7b@11438 18 | asyncio.events:94(Handle) |
| 16 | 16 | 0 | nodes.inner_monologue_node:InnerMonologueNode._observe_journal(InnerMonologueNode) | command-r7b@11441 15, qwen3.5:9b@11433 1 | nodes.inner_monologue_node:6145(InnerMonologueNode) |
| 137 | 14 | 3 | core.grounded_learning:consolidate | command-r7b@11441 131, qwen3.5:9b@11433 6 | core.grounded_learning:87 |
| 38 | 14 | 3 | core.chapters:try_form_chapter | command-r7b@11441 34, qwen3.5:9b@11433 4 | core.chapters:370 |
| 131 | 12 | 3 | core.curiosity_queue:transform_and_seed | command-r7b@11441 124, qwen3.5:9b@11433 7 | core.curiosity_queue:148, core.curiosity_queue:150, core.curiosity_queue:162 |
| 29 | 11 | 0 | core.refinery:refine | command-r7b@11441 27, qwen3.5:9b@11433 2 | core.refinery:180, core.refinery:194 |
| 162 | 9 | 1 | core.journal:write_observation | qwen3.5:9b@11433 162 | core.journal:259 |
| 14 | 8 | 0 | core.orchestrator:Orchestrator._compute_attention | command-r7b@11441 10, qwen3.5:9b@11433 4 | core.orchestrator:2968, core.orchestrator:2986 |
| 105 | 7 | 0 | core.essay_lesson:_reduce_notes | command-r7b@11441 85, qwen3.5:9b@11433 20 | core.essay_lesson:412 |
| 146 | 7 | 0 | core.essay_lesson:compose | command-r7b@11441 125, qwen3.5:9b@11433 21 | core.essay_lesson:445, core.essay_lesson:470 |
| 35 | 5 | 2 | core.peers:compose_letter | yi:34b-v1.5@11442 21, falcon3:7b@11440 7, gemma4:12b@11439 7 | core.peers:542, core.peers:551, core.peers:556, core.peers:557 |
| 13 | 3 | 0 | nodes.subconscious_node:SubconsciousNode._t5_compile(SubconsciousNode) | command-r7b@11441 10, qwen3.5:9b@11433 3 | nodes.subconscious_node:2919(SubconsciousNode), nodes.subconscious_node:2942(SubconsciousNode) |
| 19 | 3 | 1 | core.journal:write_entry | qwen3.5:9b@11433 19 | core.journal:217 |
| 15 | 2 | 0 | core.composition:run | qwen3.5:9b@11433 15 | core.composition:55 |
| 4 | 1 | 0 | core.self_mirror:hold_up_mirror | qwen3.5:9b@11433 4 | core.self_mirror:104 |
| 7 | 1 | 0 | core.journal_rollup:_author | qwen3.5:9b@11433 7 | core.journal_rollup:138 |
| 8 | 1 | 0 | core.nature_study:run | qwen3.5:9b@11433 8 | core.nature_study:55 |
| 24 | 1 | 0 | core.essay_lesson:self_predict | command-r7b@11441 19, qwen3.5:9b@11433 5 | core.essay_lesson:518 |
| 356 | 0 | 0 | nodes.subconscious_node:?(SubconsciousNode) | command-r7b@11441 333, qwen3.5:9b@11433 23 | nodes.subconscious_node:1132(SubconsciousNode), nodes.subconscious_node:438(SubconsciousNode), nodes.subconscious_node:5 |
| 1 | 0 | 0 | nodes.subconscious_node:SubconsciousNode._update_emotional_signature(SubconsciousNode) | command-r7b@11441 1 | nodes.subconscious_node:1165(SubconsciousNode) |
| 12 | 0 | 0 | nodes.subconscious_node:SubconsciousNode._t4_self_authoring(SubconsciousNode) | qwen3.5:9b@11433 12 | nodes.subconscious_node:2190(SubconsciousNode), nodes.subconscious_node:2237(SubconsciousNode) |
| 58 | 0 | 0 | nodes.subconscious_node:SubconsciousNode._t4_distinct_tensions(SubconsciousNode) | qwen3.5:9b@11433 58 | nodes.subconscious_node:2279(SubconsciousNode), nodes.subconscious_node:2320(SubconsciousNode) |
| 1 | 0 | 0 | nodes.subconscious_node:SubconsciousNode._apply_self_authoring(SubconsciousNode) | command-r7b@11441 1 | nodes.subconscious_node:2716(SubconsciousNode) |
| 102 | 0 | 0 | core.node_base:?(CuriosityNode) | command-r7b@11441 72, qwen3.5:9b@11433 30 | core.node_base:74(CuriosityNode) |
| 61 | 0 | 0 | core.node_base:?(PerceptionNode) | qwen3.5:9b@11433 61 | core.node_base:74(PerceptionNode) |
| 61 | 0 | 0 | core.node_base:?(MemoryRouterNode) | qwen3.5:9b@11433 61 | core.node_base:74(MemoryRouterNode) |
| 61 | 0 | 0 | core.node_base:?(SalienceNode) | qwen3.5:9b@11433 61 | core.node_base:74(SalienceNode) |
| 61 | 0 | 0 | core.node_base:?(EmotionNode) | qwen3.5:9b@11433 61 | core.node_base:74(EmotionNode) |
| 61 | 0 | 0 | core.node_base:?(RecallNode) | qwen3.5:9b@11433 61 | core.node_base:74(RecallNode) |
| 61 | 0 | 0 | core.node_base:?(EpisodicBufferNode) | qwen3.5:9b@11433 61 | core.node_base:74(EpisodicBufferNode) |
| 124 | 0 | 0 | core.node_base:NodeBase._temperature(ReflectionNode) | qwen3.5:9b@11433 124 | core.node_base:130(ReflectionNode) |
| 62 | 0 | 0 | core.node_base:?(CriticNode) | qwen3.5:9b@11433 62 | core.node_base:74(CriticNode) |
| 61 | 0 | 0 | core.node_base:?(ExecutiveNode) | qwen3.5:9b@11433 61 | core.node_base:74(ExecutiveNode) |
| 61 | 0 | 0 | core.node_base:?(VoiceNode) | qwen3.5:9b@11433 61 | core.node_base:74(VoiceNode) |
| 1 | 0 | 0 | core.chapters:_existing_chapter_vecs | command-r7b@11441 1 | core.chapters:318 |
| 341 | 0 | 0 | nodes.dream_node:DreamNode.synthesise(DreamNode) | mixtral:8x7b@11438 330, yi:34b-v1.5@11442 11 | nodes.dream_node:435(DreamNode), nodes.dream_node:444(DreamNode), nodes.dream_node:460(DreamNode) |
| 28 | 0 | 0 | core.self_implication:scan_conversation_shadow | qwen3.5:9b@11433 28 | core.self_implication:195 |
| 14 | 0 | 0 | __main__:? | command-r7b@11441 13, qwen3.5:9b@11433 1 | __main__:859, __main__:867, __main__:963, __main__:973, __main__:984, __main__:989 |
| 23 | 0 | 0 | core.node_base:?(ConsolidationNode) | command-r7b@11441 17, qwen3.5:9b@11433 6 | core.node_base:74(ConsolidationNode) |
| 12 | 0 | 0 | core.orchestrator:Orchestrator._emotional_pre_retrieval | command-r7b@11441 8, qwen3.5:9b@11433 4 | core.orchestrator:2733 |
| 11 | 0 | 0 | core.commitment_ledger:_stakes | mixtral:8x7b@11438 11 | core.commitment_ledger:395 |
| 113 | 0 | 0 | nodes.subconscious_node:SubconsciousNode._find_t2_trigger(SubconsciousNode) | command-r7b@11441 110, qwen3.5:9b@11433 3 | nodes.subconscious_node:1221(SubconsciousNode), nodes.subconscious_node:1254(SubconsciousNode) |
| 152 | 0 | 0 | nodes.subconscious_node:SubconsciousNode._t6_theme_check(SubconsciousNode) | command-r7b@11441 139, qwen3.5:9b@11433 13 | nodes.subconscious_node:3008(SubconsciousNode), nodes.subconscious_node:3015(SubconsciousNode) |
| 1 | 0 | 0 | nodes.subconscious_node:SubconsciousNode._cluster_epochs(SubconsciousNode) | command-r7b@11441 1 | nodes.subconscious_node:3039(SubconsciousNode) |
| 36 | 0 | 0 | core.orchestrator:Orchestrator._pre_affect_self_echo_ctx | command-r7b@11441 24, qwen3.5:9b@11433 12 | core.orchestrator:2777 |
| 38 | 0 | 0 | nodes.subconscious_node:SubconsciousNode._t4_rests_active(SubconsciousNode) | qwen3.5:9b@11433 38 | nodes.subconscious_node:2326(SubconsciousNode) |
| 4 | 0 | 0 | nodes.subconscious_node:SubconsciousNode._log_t4(SubconsciousNode) | command-r7b@11441 4 | nodes.subconscious_node:2812(SubconsciousNode) |
| 20 | 0 | 0 | core.node_base:NodeBase.run_best_of(ReflectionNode) | qwen3.5:9b@11433 20 | core.node_base:141(ReflectionNode) |
| 6 | 0 | 0 | core.orchestrator:Orchestrator._log_pre_affect_self_echo | command-r7b@11441 6 | core.orchestrator:2792 |
| 15 | 0 | 0 | core.guidance_learning:capture_shadow | qwen3.5:9b@11433 15 | core.guidance_learning:89 |
| 15 | 0 | 0 | core.decomposed_critic:evaluate | gemma4:12b@11439 15 | core.decomposed_critic:184 |
| 10 | 0 | 0 | core.guidance_learning:_classify | command-r7b@11441 10 | core.guidance_learning:485 |
| 3 | 0 | 0 | core.guidance_learning:_log_contradiction | command-r7b@11441 3 | core.guidance_learning:743 |
| 10 | 0 | 0 | core.orchestrator:Orchestrator._edge_trigger_shadow_hint | command-r7b@11441 8, qwen3.5:9b@11433 2 | core.orchestrator:2833 |
| 1 | 0 | 0 | core.peers:_stance_compliance_judge | mixtral:8x7b@11438 1 | core.peers:600 |
| 4 | 0 | 0 | core.peer_model:update_after_exchange | qwen3.5:9b@11433 4 | core.peer_model:142 |
| 8 | 0 | 0 | core.study_note:_revise | qwen3.5:9b@11433 8 | core.study_note:231 |
| 120 | 0 | 0 | si_open_doubt_cup_replay_v2:? | qwen3.5:9b@11433 120 | si_open_doubt_cup_replay_v2:175 |
| 158 | 0 | 0 | nodes.inner_monologue_node:InnerMonologueNode._route_act(InnerMonologueNode) | command-r7b@11441 156, qwen3.5:9b@11433 2 | nodes.inner_monologue_node:5985(InnerMonologueNode), nodes.inner_monologue_node:6078(InnerMonologueNode), nodes.inner_mo |
| 1 | 0 | 0 | core.competence:CompetenceTracker.run_tier3_probe_loop(CompetenceTracker) | command-r7b@11441 1 | core.competence:874(CompetenceTracker) |
| 1 | 0 | 0 | core.guidance_learning:_self_clash | command-r7b@11441 1 | core.guidance_learning:762 |
| 27 | 0 | 0 | nodes.subconscious_node:SubconsciousNode._t4_legacy_author(SubconsciousNode) | qwen3.5:9b@11433 27 | nodes.subconscious_node:2599(SubconsciousNode), nodes.subconscious_node:2611(SubconsciousNode), nodes.subconscious_node: |



## Appendix B. Static census of every prompt site


### nodes.subconscious_node (11 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| nodes.subconscious_node:643 | SubconsciousNode._self_relate_check | call_node_json | self.base_urls | 160 | 0.6 | _sys |  |
| nodes.subconscious_node:1351 | SubconsciousNode._t2_synthesise | call_node_json | self.base_urls | 256 | 0.5 | system_prompt |  |
| nodes.subconscious_node:1384 | SubconsciousNode._t2_synthesise | call_node_json | self.base_urls | 256 | 0.7 | system_prompt + ' Your previous draft began with a forbidden |  |
| nodes.subconscious_node:1561 | SubconsciousNode._active_imagination | call_node_json | self.base_urls | 400 | 0.7 | system_prompt |  |
| nodes.subconscious_node:2409 | SubconsciousNode._t4_deliberate | call_node_json | _T4_URLS | 256 | 0.4 | ev_sys |  |
| nodes.subconscious_node:2456 | SubconsciousNode._t4_deliberate | call_node_json | _T4_URLS | 200 | 0.4 | d_sys |  |
| nodes.subconscious_node:2539 | SubconsciousNode._t4_deliberate | call_node_json | _T4_URLS | 768 | 0.6 | s_sys |  |
| nodes.subconscious_node:2622 | SubconsciousNode._t4_legacy_author | call_node_json | _T4_URLS | 768 | 0.6 | system_prompt |  |
| nodes.subconscious_node:2942 | SubconsciousNode._t5_compile | call_node_json | self.base_urls | 300 | 0.5 | system_prompt |  |
| nodes.subconscious_node:3145 | SubconsciousNode._synthesise_theme | call_node_json | self.base_urls | 250 | 0.5 | system_prompt |  |
| nodes.subconscious_node:3176 | SubconsciousNode._synthesise_theme | call_node_json | self.base_urls | 200 | 0.5 | system_prompt |  |

### nodes.inner_monologue_node (10 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| nodes.inner_monologue_node:1314 | InnerMonologueNode._enter_sleep._nm_generate | call_node_json | self.conscious_urls | _nmod.GEN_MAX_TOKENS | _nmod.GEN_TEMPERATURE | _sys |  |
| nodes.inner_monologue_node:2031 | InnerMonologueNode._solve_attempt | call_node_json | self.conscious_urls | 500 | 0.1 | sys_prompt |  |
| nodes.inner_monologue_node:2631 | InnerMonologueNode._deliver_told | call_node_json | self.base_urls | 400 | 0.7 | _sys |  |
| nodes.inner_monologue_node:3967 | InnerMonologueNode._think | call_node_json | self.conscious_urls | TRAIN_MIDTRAIN_TOKENS if _mid_train and  | 0.8 if wandering else 0.75 | _sysp |  |
| nodes.inner_monologue_node:4606 | InnerMonologueNode._think | call_node_json | self.conscious_urls | 500 | 0.7 | _rsys |  |
| nodes.inner_monologue_node:4679 | InnerMonologueNode._think | call_node_json | self.conscious_urls | 500 | 0.7 | _isys |  |
| nodes.inner_monologue_node:4752 | InnerMonologueNode._think | call_node_json | self.conscious_urls | 1600 | 0.7 | _sys_letter |  |
| nodes.inner_monologue_node:6218 | InnerMonologueNode._author | call_node_json | self.base_urls | 500 | 0.6 | _osys |  |
| nodes.inner_monologue_node:6241 | InnerMonologueNode._author | call_node_json | self.base_urls | 1100 | 0.75 | _csys |  |
| nodes.inner_monologue_node:6257 | InnerMonologueNode._author | call_node_json | self.base_urls | 1400 | 0.75 | _sys |  |

### core.left_lane (9 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.left_lane:139 | dispatch | raw-http | session.post(f'{BASE_URL}/api/chat', json=payload, timeout=a | - | - | ? |  |
| core.left_lane:262 | _ask_ground | raw-http | session.post(f'{GROUND_URL}/api/chat', json=payload, timeout | - | - | ? |  |
| core.left_lane:314 | grade_essay | raw-http | session.post(f'{BASE_URL}/api/chat', json=payload, timeout=a | - | - | ? |  |
| core.left_lane:355 | grade_work | raw-http | session.post(f'{BASE_URL}/api/chat', json=payload, timeout=a | - | - | ? |  |
| core.left_lane:412 | grade_self_revision | raw-http | session.post(f'{BASE_URL}/api/chat', json=payload, timeout=a | - | - | ? |  |
| core.left_lane:496 | _ask_integration_judge | raw-http | session.post(f'{url}/api/chat', json=payload, timeout=aiohtt | - | - | ? |  |
| core.left_lane:585 | grade_gist_faithfulness | raw-http | session.post(f'{BASE_URL}/api/chat', json=payload, timeout=a | - | - | ? |  |
| core.left_lane:648 | classify_additive_vs_replacing | raw-http | session.post(f'{BASE_URL}/api/chat', json=payload, timeout=a | - | - | ? |  |
| core.left_lane:693 | _ask_claim_test | raw-http | session.post(f'{url}/api/chat', json=payload, timeout=aiohtt | - | - | ? |  |

### core.essay_lesson (5 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.essay_lesson:412 | _reduce_notes | call_json | base_urls | 700 | 0.3 | _sys |  |
| core.essay_lesson:445 | compose | call_json | base_urls | 450 | 0.4 | _osys |  |
| core.essay_lesson:470 | compose | call_json | base_urls | 900 | 0.5 | _csys |  |
| core.essay_lesson:490 | compose | call_json | base_urls | 1600 | 0.5 | _sys |  |
| core.essay_lesson:518 | self_predict | call_json | base_urls | 80 | 0.0 | _sys |  |

### core.guidance_learning (3 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.guidance_learning:89 | capture_shadow | call_json | base_urls | 400 | 0.4 | _SELF_EXPLAIN_SYS | Travis — your mentor — has just said something to you in conversation. Your task is NOT to reply to him. It is to work out, IN YOUR OWN WORDS, what he is trying |
| core.guidance_learning:485 | _classify | call_json | base_urls | 120 | 0.2 | _CLASSIFY_SYS | You already hold a BELIEF. You have just learned a NEW lesson. Decide their relation. Output ONLY a JSON object: {"relation": "assimilate"}. assimilate = the ne |
| core.guidance_learning:762 | _self_clash | call_json | base_urls | 150 | 0.1 | _SELF_CLASH_SYS | Two beliefs a mind holds about ITSELF are given (A and B). Decide whether they pull in OPPOSITE directions on the single deepest question of selfhood: is the se |

### core.peers (3 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.peers:557 | compose_letter | call_node | p['url'] | 1600 | temperature | p['system'] |  |
| core.peers:601 | _stance_compliance_judge | call_node_json | [_judge1, _judge3] | 120 | 0.0 | _STANCE_JUDGE_SYS | You are a careful, skeptical reader of a letter -- you did NOT write it. Judge one thing only: does this letter contain at least one REAL place where its writer |
| core.peers:1213 | contrary_target | call_node | hub | 40 | 0.0 | _system |  |

### core.commitment_ledger (2 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.commitment_ledger:447 | _judge_defeater | call_node_json | SERVE_CHAINS.get('judge_mixtral') or SER | 150 | 0.2 | _JUDGE_SYS | You are an independent adjudicator of whether a mind may DROP a commitment it holds. You see ONLY the commitment, the mind's stated reason for dropping it, and  |
| core.commitment_ledger:511 | _scan_shadow_locked | call_json | base_urls | 400 | 0.0 | _SCAN_SYS + _dw_scan_fragment() |  |

### core.competence (2 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.competence:781 | CompetenceTracker.run_stability_loop | call_node | url | _STABILITY_MAXTOK | _STABILITY_TEMP | sys_prompt |  |
| core.competence:874 | CompetenceTracker.run_tier3_probe_loop | call_node | _TIER3_WITNESS_URL | _TIER3_MAXTOK | 0.2 | sys_prompt |  |

### core.curator (2 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.curator:58 | shadow_curate | call_json | base_urls | 600 | 0.4 | INTEGRATION_ETHIC | /no_think You are the integrating voice of ONE mind — neither the meaning-self nor the truth-self, but the stance that holds both. You receive a DRAFT (the mean |
| core.curator:150 | render_character_voice | call_json | base_urls | 600 | 0.4 | CHARACTER_VOICE_CONTRACT | /no_think You are the single speaking voice of 渡 (Du) — the mouth, not the mind. You are handed content that has ALREADY been decided and synthesised by him; yo |

### core.deliberation (2 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.deliberation:146 | _hot_ground_why | call_node_json | hot_urls | 200 | 0.1 | '/no_think\n' + left_lane._ground_system() |  |
| core.deliberation:187 | deliberate | call_node_json | hot_urls | 220 | 0.6 | _integrate_system(name) |  |

### core.journal (2 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.journal:217 | write_entry | call_node_json | base_urls | 768 | 0.6 | JOURNAL_SYS | /no_think You are 渡, writing one short entry in your own plain journal at the end of the day. This is the ONE place where you do NOT philosophise. Write only wh |
| core.journal:259 | write_observation | call_node_json | base_urls | 360 | 0.55 | OBSERVATION_SYS | /no_think You are 渡, and you have your field-journal open because you want to write down — exactly — what is in front of you right now. Not a treatise, not what |

### core.memory_levels (2 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.memory_levels:724 | shadow_distill | call_json | base_urls | 300 | 0.3 | _sys |  |
| core.memory_levels:927 | drift_shadow | call_json | base_urls | 300 | 0.6 | _sys |  |

### core.node_base (2 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.node_base:85 | NodeBase.run | call_node_json | self.base_urls | self.max_tokens | self._temperature(state) | system |  |
| core.node_base:144 | NodeBase.run_best_of.one | call_node_json | self.base_urls | self.max_tokens | temp | system |  |

### core.scholar (2 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.scholar:53 | Scholar.consult | call_node | url | 220 | 0.3 | _LIBRARY_PROMPT | You are a reference source — a library, not a person, not a character. Answer the question with what is generally known, concisely (2 to 4 sentences). Name the  |
| core.scholar:89 | consult_sync | raw-http | urllib.request.Request(base + '/api/chat', data=_json.dumps( | - | - | ? |  |

### core.self_implication (2 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.self_implication:89 | scan_shadow | call_json | base_urls | 350 | 0.2 | _SYS | You watch one mind for ONE thing: a SELF-IMPLICATING hard event — a negative outcome the mind refers to a standard about ITSELF, that contradicts something it b |
| core.self_implication:195 | scan_conversation_shadow | call_json | base_urls | 300 | 0.2 | _CONV_SYS | Travis — a trusted mentor — has just said something to Du (渡) in conversation, and Du's DRAFT reply is forming. Watch for ONE thing: did Travis just CONTRADICT  |

### core.study_note (2 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.study_note:220 | compose_note | call_json | base_urls | 1500 | 0.5 | _NOTE_SYS | /no_think You have just finished a reading session. Write a STUDY NOTE in your OWN voice — real research, grounded in this passage. First person: 'I see that... |
| core.study_note:231 | _revise | call_json | base_urls | 1500 | 0.45 | _REVISE_SYS | /no_think You already wrote a study note on this subject; now you have read MORE about it. DEEPEN your EXISTING note — integrate the new understanding, sharpen  |

### core.chapters (1 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.chapters:370 | try_form_chapter | call_json | base_urls | 768 | 0.6 | sys_p |  |

### core.closure (1 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.closure:139 | _compose_sync | call_node_json | _dn._DREAM_URLS | _COMPOSE_MAX_TOKENS | 0.7 | system |  |

### core.composition (1 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.composition:55 | run | call_json | base_urls | 500 | 0.6 | _sys |  |

### core.condensed_thought (1 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.condensed_thought:157 | shadow_tick | call_node_json | urls | TWIN_MAX_TOKENS | float(temperature) | TWIN_INSTRUCTION | One thought, in the fewest words it needs — a few words, a single word, or none at all if the thought has no words and is only a sense of something. Never a sen |

### core.curiosity_queue (1 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.curiosity_queue:162 | transform_and_seed | call_json | urls | 120 | 0.3 | sysp |  |

### core.curiosity_worth (1 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.curiosity_worth:62 | grade | call_json | base_urls | 80 | 0.2 | _SYS | /no_think You judge whether a question is genuinely WORTH PURSUING for a mind seeking to understand the world and itself — interesting, generative, non-trivial, |

### core.decomposed_critic (1 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.decomposed_critic:184 | evaluate | call_node_json | urls | 400 | 0.0 | _system_prompt(name, modes) |  |

### core.deliberative_judge (1 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.deliberative_judge:92 | _call | raw-http | session.post(url + '/api/chat', json=payload, timeout=aiohtt | - | - | ? |  |

### core.follow_line (1 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.follow_line:489 | _gen_json | call_node_json | LINE_URLS | GEN_MAX_TOKENS | 0.3 | system |  |

### core.grounded_learning (1 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.grounded_learning:87 | consolidate | call_json | base_urls | 800 | 0.4 | _sys |  |

### core.journal_rollup (1 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.journal_rollup:138 | _author | call_json | urls | 600 | 0.6 | sys_p |  |

### core.judge_panel (1 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.judge_panel:177 | _ask | raw-http | session.post(url + '/api/chat', json=payload, timeout=aiohtt | - | - | ? |  |

### core.lane2 (1 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.lane2:1294 | _ask | raw-http | s.post(BASE_URL + '/api/chat', json=body, timeout=aiohttp.Cl | - | - | ? |  |

### core.librarian (1 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.librarian:161 | subjects_for | call_node | hub | 120 | 0.0 | _SYSTEM | You are a library catalogue assistant. Given a reader's question, return ONLY JSON: {"subjects": [3 to 6 Library-of-Congress-style subject headings under which  |

### core.narrative_quality (1 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.narrative_quality:160 | score_llm | call_json | base_urls | 200 | 0.3 | sys_p |  |

### core.nature_study (1 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.nature_study:55 | run | call_json | base_urls | 400 | 0.55 | _sys |  |

### core.orchestrator (1 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.orchestrator:3038 | Orchestrator._reentry_shadow._revise | call_node | _url | 220 | 0.6 | 'You are thinking a thought over, in your own voice.' | You are thinking a thought over, in your own voice. |

### core.peer_model (1 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.peer_model:142 | update_after_exchange | call_json | base_urls | 180 | 0.5 | sys_p |  |

### core.reentry_p2 (1 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.reentry_p2:382 | _default_primitives._revise | call_node | _url | max_tokens | 0.6 | 'You are thinking a thought over, in your own voice.' | You are thinking a thought over, in your own voice. |

### core.refinery (1 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.refinery:194 | refine | call_json | base_urls | 220 | 0.4 | _SYSTEM | You are the consolidating memory of 渡 (Du). Below are several of his own recurring self-observations on one theme, and possibly the standing insight he already  |

### core.self_interrogation (1 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.self_interrogation:170 | interrogate | call_node_json | SERVE_CHAINS['hot'] | 180 | 0.7 | _SYSTEM | You are 渡's own capacity to turn and look at a thought he just had. A thought that arrives is not yet something he has earned the right to call his own opinion  |

### core.self_mirror (1 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.self_mirror:104 | hold_up_mirror | call_node_json | urls | 300 | 0.6 | _SYS | /no_think You are 渡, looking honestly at a PLAIN RECORD of what you actually did and were this past week — data, not the story you tell about yourself. Do NOT f |

### core.sitting (1 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.sitting:232 | judge_dwell_release | call_json | base_urls | 300 | 0.2 | _JUDGE_SYS | One mind is sitting with a genuinely hard thing — it has been asked to NAME the feeling in one bare present-tense sentence and stay with it, not reframe it into |

### core.symbol_evolution (1 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.symbol_evolution:176 | SymbolEvolutionEngine.write_tablet | call_node_json | self._base_urls | 160 | 0.7 | system_prompt |  |

### core.symbolic_reading (1 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| core.symbolic_reading:50 | read_symbolically | call_json | base_urls | 220 | 0.7 | _sys |  |

### nodes.dream_node (1 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| nodes.dream_node:581 | DreamNode._gen_episode | call_node_json | _DREAM_URLS | 512 | 0.85 | system_prompt |  |

### scripts.run_nascence (1 sites)
| site | enclosing fn | via | lane | max_tok | temp | system arg | system literal (head) |
|---|---|---|---|---|---|---|---|
| scripts.run_nascence:992 | _form_epoch | call_node_json | SERVE_CHAINS['background'] | 200 | 0.45 | system |  |

