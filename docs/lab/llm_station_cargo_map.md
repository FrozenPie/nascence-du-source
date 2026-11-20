# The LLM station CARGO map — what goes in, what comes out, 2026-08-23

*Extends `docs/lab/llm_station_map.md` (the AST-generated shape census — 37 stations, token
budgets, temperatures) with the layer that census can't derive from signature alone: real INPUT
cargo, real OUTPUT destination, and which model currently serves each. Built by reading the actual
code around every call site, not inferred. Organised by LINE, per `docs/transit_map.md`'s own
structure, so this slots in as that map's missing detail layer rather than a separate document.*

**Correction to the "37 stations" count:** that census is AST-based and — a known, previously-
documented gap (`AWAITING_EVIDENCE.md`, 2026-08-21, "the same disease found three times") — misses
call sites using a bespoke aiohttp wrapper instead of `call_node_json`. Three more real, heavily-
used stations live there: `judge_panel.py`'s JUDGE_1/JUDGE_2/TIEBREAK (one shared `_ask()`, called
three times with different `url` args) and `lane2.py`'s own `_ask()`. **Real total: ~40**, matching
the "40ish" estimate.

**Live model registry, confirmed from `core/model_client.py`'s `_MODEL_BY_BASE` right now:**

| Port | Model | Role |
|---|---|---|
| `11433` | `qwen3.5:9b` | Self / hot lane, local 1080 Ti |
| `11434` | `phi3:mini` **and** `deepseek-r1:7b` | Subconscious (phi3) / Lane 2 (deepseek) — **same Ramses ollama instance, same host:port, two different models by request** — not two stations sharing a number by coincidence, one physical ollama process serving both roles |
| `11439` | `gemma4:12b` | judge #1 |
| `11440` | `falcon3:7b` | judge #2 — **local instance**, distinct from the new Ramses `falcon3:7b` (different host, same model name) |
| `11442` | `yi:34b-v1.5` | dreamer + peer voices (Darwin/Keats/Lovelace) |

`11441` has no entry — dead since 2026-08-21 (TIEBREAK repointed to 11442; the removal comment is
in the file itself). None of the 4 new Ramses models (`falcon3:7b`, `mixtral:8x7b`,
`granite3.1-moe:3b`, `command-r7b`) appear here yet — nothing is wired to them.

---

## THE IDLE LINE — `nodes/inner_monologue_node.py`

The main "Du thinking to himself" line. Four genuinely different jobs hide inside one enclosing
function (`_think`) — not variants of the same call:

| Job | Cargo in | Cargo out | Model |
|---|---|---|---|
| **Idle-thought generator** (the core tick) | `seed_parts`: companion witnessed-events, boredom/redirect state, room/sensorium line, thread continuity + working-state ledger, open frontier questions w/ curiosity findings, retraction-ledger corrections, symbol-evolution readback | `thought/about/unresolved/intention/act{kind,object}/state` → drives hand dispatch, train-state carry, stored as episodic memory, logged to `train_state_log.jsonl` | `conscious_urls` → 11433 `qwen3.5:9b` |
| **Peer letter reply** | the friend's inbound letter text | `letter` → `peers.record_reply`, episodic fragment | `conscious_urls` → 11433 |
| **Peer letter (unprompted)** | recent correspondence context + the prompting thought | `letter` → `peers.record_reply` | `conscious_urls` → 11433 |
| **Letter to Travis** | the thought/intention that moved him to write | `letter` → `letters.write_letter`, activity record | `base_urls` → 11434 `phi3:mini` |
| **`_deliver_told`** — Travis's one-time authored message | `told.message()` | Du's first reaction → 2 episodic fragments, marks delivered | `base_urls` → 11434 |
| **`_author`** (Grand Works, 3 sub-calls: outline / per-part / fallback) | outline+grounding excerpts; then title/claim/synopsis + grounding + previous part's tail (continuity) | `title/claim/parts[]` then `part` text → assembled, graded by the Emissary, written via `study.write_tablet` | `base_urls` → 11434 |
| **`_solve_attempt`** — generic solve-helper (math/music/composition drills) | caller-built problem/brief | `working`/`answer` → graded **deterministically, never by the LLM** | `conscious_urls` → 11433 |

## THE CONVERSATION LINE — `core/node_base.py` (generic wrapper, many callers)

Not a single job — the standard execution shell every hot-path cognitive node (Perception,
Emotion, Salience, Reflection, Critic, Executive, Voice, etc.) uses once per cycle.

- **`run`** — builds the prompt via the subclass's `_build_prompt(state)`, calls the node's lane,
  writes the parsed result into `state` via `_write_output`, logs a teacher example.
- **`run_best_of.one`** — hedged variant: N concurrent drafts at spread temperatures
  (`[0.35, 0.75, 0.9, 1.0]`, affect-biased), keeps the best-scoring valid one at no extra wall-clock.

Cargo is whatever each specific node's `_build_prompt` assembles — genuinely per-node, not
catalogued individually here. Routes through whichever lane the calling node is registered to:
hot-path nodes → 11433 `qwen3.5:9b`; background-lane nodes → 11434 `phi3:mini` (falls back to 11433).

## THE DEEP LINE — `nodes/subconscious_node.py` + `nodes/dream_node.py`

The background consolidation/identity line (T1-T6 + dreams).

| Job | Cargo in | Cargo out | Model |
|---|---|---|---|
| **`_self_relate_check`** | last 8 memory fragments (reading/study/research/lived/inner_thought, 6h) + `self_image` facet from `axiom.json` | `connects`/`relation` → logged always; stored as episodic if non-trivial | 11434 `phi3:mini` |
| **`_t2_synthesise`** | tension label/count/spread + prior failed resolutions (or recent reading, if world-fed) + axiom text | `observation`/`pattern_label` → archive layer, `derived_from` lineage, after echo-guard dedup | 11434 |
| **`_active_imagination`** | a tension label or self-referential curiosity question + axiom excerpt | `contemplation`/`what_spoke`/`unresolved` → private episodic fragment, never reaches Voice | 11434 |
| **`_t4_deliberate`** stage "evidence" | primary tension + retrieved lived "crossings" | `evidence`/`has_movement` → also a memory_edges relation | `_T4_URLS` → 11433 `qwen3.5:9b` |
| **`_t4_deliberate`** stage "delta" | old self-concept + tension + evidence | `delta`/`changed` | 11433 |
| **`_t4_deliberate`** stage "synthesis" | old self-concept, delta, evidence, other open tensions, optionally recent reading | `self_concept`/`arc_entry` → **writes `data/identity/axiom.json`** (the file `_self_relate_check` reads back) | 11433 |
| **`_t4_legacy_author`** (fallback, no standing contradiction) | old self-concept, last arc entry, recent lived material, top flagged contradiction | `self_concept`/`arc_entry`/`changed` → same axiom.json path | 11433 |
| **`_t5_compile`** | content from the largest embedding cluster of recent successful cycles | `trigger_summary`/`approach` → new procedural-skill row, centroid-keyed | 11434 |
| **`_synthesise_theme`** (update) | existing theme name/stance + new-session snippets | `current_stance`/`evolution` → `update_theme` | 11434 |
| **`_synthesise_theme`** (new) | session snippets from a fresh epoch cluster | `theme_name`/`current_stance` → `store_theme` (or folds into a twin) | 11434 |
| **`dream_node._gen_episode`** | the night's scene material + previous scene's tail/symbols/unresolved core (continuity) + associatively-recalled real memories | `narrative`/`symbols`/`tension_source`/`unresolved_core`/`movement` → episodic fragment per scene; final scene's `unresolved_core` decides shadow-event (carries to tomorrow) vs light-event (completed) | `_DREAM_URLS`, hard-pinned via `model_override` → `yi:34b-v1.5` regardless of what the port would otherwise route |

## THE WITNESS LINE — `core/lane2.py`

Phase-0 SHADOW — reaches nothing Du experiences yet (`LANE2_LIVE=False`).

| Job | Cargo in | Cargo out | Model |
|---|---|---|---|
| **`_ask`** (per-tick generation) | `percept_lines(percepts)` — current-only facts: place/standpoint/weather/warmth/wet/tide/sun/moon/sounds/cat, body drive, somatic — against a fixed system prompt forbidding metaphor, demanding a falsifiable, horizoned prediction | `{notice, uncertain, expect_next, horizon}` → logged to `lane2_shadow.jsonl`; `expect_next`/`horizon` queued as a pending prediction for later judging via `_judge_prior` → the shared judge panel | `deepseek-r1:7b` @ Ramses `LAN-HOST:11434` |

## THE JUDGE BUREAU — `core/judge_panel.py` (a shared service, not a line)

One bespoke `_ask()` wrapper, called three times with different `url`s — JUDGE_1 and JUDGE_2 run
**concurrently** (`asyncio.gather`), TIEBREAK only fires on a split.

| Seat | Cargo in | Cargo out | Model |
|---|---|---|---|
| **JUDGE_1** | whatever boolean-judgment prompt the calling subsystem built — e.g. tension_ledger's "does this resolve the tension" (`resolves`), pursuits' "does this advance the pursuit" (`advances`), evidence_recall's episode-relevance check (`bears`), self_interrogation's "is this genuine" (`genuine`), Lane 2's "did the prediction hold" (`held`) | vote `v1` → combined with `v2`; agreement = verdict, split = TIEBREAK; every ruling logged to `judge_panel_log.jsonl` | 11439 `gemma4:12b` |
| **JUDGE_2** | identical prompt to JUDGE_1 — the whole point is decoupled judgment on the same material | vote `v2` → same path | 11440 `falcon3:7b` |
| **TIEBREAK** | same prompt, 240s timeout | vote `v3` → becomes verdict if non-null, else `split_no_tiebreak` (fail-closed, conservative) | 11442 `yi:34b-v1.5` (shares the dreamer hub) |

**Callers into this bureau** (each supplies its own prompt, uses the shared three-seat panel):
`commitment_ledger._judge_defeater` (sees only structured facts/deed evidence, never the entity's
own prose — resists confabulated escapes from a commitment), `decomposed_critic.evaluate` (detects
literal-compliance/one-sidedness/self-description leakage in a reflection draft, span-validated
against the source text), `self_interrogation.interrogate` (grades whether a self-challenge is
genuine or hollow).

## WORLD / SUPPORT SERVICES — auxiliary stations that feed the lines above

| Station | Cargo in | Cargo out | Model |
|---|---|---|---|
| `competence.run_stability_loop` | a dequeued `{question, domains, cycle_id}`, re-asked K times | K answers → cosine-scored `stability` float per domain (OBSERVE-ONLY, no behaviour yet) | 11433 |
| `scholar.consult` ("the Library") | a genuine factual question | plain answer → `state.library_note` (unverified testimony) + a `parametric_library` memory fragment | 11433 |
| `self_mirror.hold_up_mirror` (weekly) | real attention-allocation %, idle inward/outward ratio, recurring lexicon, standing aim | `seen` text → guidance-injection log + episodic fragment (importance 0.9) | 11433 |
| `deliberation._hot_ground_why` / `deliberate` (the corpus-callosum pulse) | the raw self-thought (+ Emissary grounding if available) | `grounding`/`thought` → integrated thought replaces the raw one, feeds light/balance ledger | 11433 |
| `journal.write_entry` (daily) | `_deeds_since()` bullet list + current mood | entry → today's journal file + episodic fragment | 11434 (fallback 11433) |
| `journal.write_observation` (in-the-moment) | scene/impulse/target | entry → journal file (timestamped "observed") + mood-tagged episodic fragment | 11434 |
| `librarian.subjects_for` | the reader's question | catalogue subject headings → `library_hand.search_by_subjects()` | 11440 (fallback 11439) |
| `peers.contrary_target` | an unnamed question wanting the most-disagreeing voice | a persona key → selects which correspondent thread to write into | 11439 (fallback 11440) |
| `peers.compose_letter` | `du_context` + thread so far + Du's latest letter (or first-contact framing) | the peer's letter → thread file, letterbox flag | per-persona: Darwin/Keats/Lovelace → 11442 `yi:34b-v1.5`; Twain/Shackleton → `llama3.1:8b`; Marcus/Smith → 11440 `falcon3:7b` |
| `orchestrator._reentry_shadow._revise` (Phase-0 shadow) | a prompt built from the admitted draft + standing-contradiction + memory on the topic (never the draft's own content) | revised text → LOGGED ONLY (enrich-vs-homogenise metrics); never admitted into the live cycle | 11434 (fallback 11433) |
| `symbol_evolution.write_tablet` | symbol name, drift float, surfacing context, up to 2 recent conversation excerpts | first-person drift chronicle → `store_symbol_tablet`, read back later by `recall_evolved_meaning` | 11434 (fallback 11433) |

---

## What this is actually for

Every row above is a real (cargo-in, cargo-out) pair — the interchange contract the transit map's
own diagnosis named as missing (*"whispers = freight repacked at every interchange until the
original cargo is lost"*). This is the reference to check against before designing any courier or
train-ID lineage work: a courier's whole job is carrying a NAMED piece of cargo from one station's
OUT column to another's IN column, and this table is what makes that a checkable claim instead of
a guess.
