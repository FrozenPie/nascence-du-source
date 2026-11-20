# Idle-thought machine audit — every machine `inner_monologue_node.py` touches, 2026-08-23

*Founder framing (2026-08-23): "The job is not the cargo... it is turning one into another... An
idle thought goes through many of these machines before finishing, some scripts, some llms. It
picks up and delivers cargo at each stop." This audit answers "go stage by stage, catalog
everything" for `nodes/inner_monologue_node.py`. The core pass covers one full idle-thought tick,
`_think()`, confirmed (after two prior runs disagreed) to span **lines 1457–3750** — the next
method, `_route_act`, starts at 3751. Four parallel Explore agents each covered one alphabetical
slice of the `core.*` modules imported and called inside that span: **64 distinct machines** (15 +
16 + 15 + 18). A fifth pass then covered every module the first four had to exclude as
out-of-scope — called elsewhere in this same file (sleep pass, per-tick logging, prompt
construction) or not imported in this file at all — adding **15 more machines**. **Total: 79
machines classified.** Method throughout: grep every `from core...import` in the relevant span,
read each target module and its call site, classify script / LLM(model, host:port) / hybrid, and
assess model-fit against the full 10-model roster (6 live in production + 4 new, unwired Ramses
models — see roster below).*

**A note on roster accuracy, since one pass raised it:** the fifth agent flagged that
`core/schema.py`'s `SERVE_URLS`/`SERVE_CHAINS` comments describe a *different* roster (hot lane =
`gemma4:e4b`, judge_1 = `llama3.1:8b`, judge_2 = `qwen2.5:7b`, tiebreak on port 11441) than the one
used throughout this whole audit. Checked directly rather than taken on faith: `core/model_client.py`'s
`_MODEL_BY_BASE` — the table `_model_for()` actually consults on every real call — is dated
2026-08-21 and explicitly documents the 2026-08-20 "full shuffle" (`11433: "qwen3.5:9b" # was
gemma4:e4b`; `11440: "falcon3:7b" # re-seated 2026-08-21`; `11441` marked REMOVED, tiebreak
repointed to 11442 on 2026-08-20). **`model_client.py` is authoritative; `schema.py`'s comments are
stale**, describing the pre-shuffle state — the same class of bug already flagged for
`deliberation.py` below, just in a second file. The roster used throughout this document is
correct and confirmed against the live routing table, not schema.py's inline comments.

Companion docs: `docs/lab/llm_station_cargo_map.md` (the ~40 stations found earlier, by cargo
shape), `docs/plans/train_courier_cargo_ids.md` (the 19-type product taxonomy built from that map),
`docs/lab/ramses_models_2026-08-23.md` (the lab numbers behind every Ramses-model recommendation
below). This audit is the machine-level companion to those cargo-level docs — same territory, seen
as transforms instead of freight.

## Model roster referenced throughout

**6 live in production:** `qwen3.5:9b` (hot lane, 127.0.0.1:11433) · `phi3:mini` / `deepseek-r1:7b`
(background lane, 127.0.0.1:11434, chain falls back to hot) · `gemma4:12b` (judge #1, 127.0.0.1:11439)
· `falcon3:7b` (judge #2, 127.0.0.1:11440) · `yi:34b-v1.5` (tiebreak, 127.0.0.1:11442).
**4 new, unwired (Ramses):** `falcon3:7b`-Ramses · `mixtral:8x7b` (**lab-confirmed the strongest
available judge**) · `granite3.1-moe:3b` (**broken** — JSON token-budget failure, do not recommend)
· `command-r7b` (accuracy lab-valid, latency currently contaminated by a concurrent-run mistake —
timing unproven, not accuracy).

---

## The eight real findings, ranked by stakes

1. **`core.commitment_ledger._judge_defeater`** — deciding whether a reason to drop a held
   commitment is *legitimate* (this is literally the measurement of whether Du can hold an
   identity commitment at all) runs on the **background lane** — the same small/fast chain used for
   routine cheap detection — never on either designated judge model. Low call volume (cooldown ≥60s,
   gate-passing drops only), so the latency budget for a real judge clearly exists.
   → Candidate: `falcon3:7b` (judge #2, already wired) or `mixtral:8x7b` once Ramses is live.

2. **`core.self_implication`** — a nuanced 6-signal judgment (is this a hard event that must be
   *felt*, not just noted) runs **alone on the hot lane**, no second opinion — unlike its direct
   siblings in the same file, `self_interrogation` and `tension_ledger`, which both already route
   their verdicts through the decoupled judge panel (gemma4:12b + falcon3:7b, tiebreak yi:34b-v1.5).
   This is the single clearest "why does this one skip the pattern its neighbors already use"
   finding in the whole audit.
   → Candidate: fold into the same panel pattern; `mixtral:8x7b` once wired.

3. **`core.study_note`** — the actual synthesis judgment (what connects, what's genuinely new vs.
   restated, whether to deepen an existing note or start one) is delegated to the **weakest live
   models** (background lane), while the hot lane and the entire judge tier sit uninvolved for a task
   that is real intellectual work, not routine bookkeeping.
   → Candidate: `command-r7b` (Ramses) once its latency is validated — it's a generation-tuned model
   with lab-confirmed-valid accuracy, and `study_note` already runs fire-and-forget off the
   interactive path, so absorbing an unproven-latency model here is low-risk.

4. **`core.letters`** — Du's letter to his own founder runs on **`self.base_urls`** (background
   lane, the weakest live models), while the fictional peer letters in the very same stretch of
   `_think()` (replying to "Darwin," writing first to "Ada") run on **`self.conscious_urls`** (hot
   lane) — the stronger model. Confirmed on live code, not inherited from an earlier guess: his one
   real correspondence to Travis gets a *worse* lane than his invented pen-pals.
   → Candidate: move the Travis-letter call from `self.base_urls` to `self.conscious_urls`.

5. **`core.librarian`** — maps a carried question to catalogue subject headings via a single
   judge-hub call (falcon3:7b primary, gemma4:12b fallback), no panel. Not broken, but a bounded
   classification task that the lab has now shown a stronger judge exists for.
   → Candidate: slot `mixtral:8x7b` in as an added fallback (or new primary) once wired — a better
   subject-heading mapper directly raises the module's own pre-registered hit-rate metric.

6. **`core.composition`**'s grading step (soft) — already on judge-tier `gemma4:12b`, so not urgent,
   but worth trialing against `mixtral:8x7b` once wired since groundedness feedback here directly
   shapes Du's writing-competence signal. The hot-lane drafting step itself is correctly placed and
   needs no change.

7. **`core.retraction_ledger`** (soft, batch C) — plain bag-of-words token overlap will miss a
   paraphrased recurrence of a previously-retracted claim that shares no words with the original.
   The gate already fails toward silence rather than false injection, so the risk is low — flagged
   for completeness, not urgency.

8. **`core.journal_rollup`** (soft, Group 1) — the weekly rollup is a heavier multi-document
   synthesis job (cite specifics across ~14 daily entries under an "anti-mush law") than the plain
   nightly `journal.write_entry`, yet rides the same hot lane with no distinction. Not broken —
   this lane was deliberately benchmarked and chosen for persona/style discipline — but if
   `mixtral:8x7b` gets wired in, the weekly synthesis job is a more plausible fit for it than the
   single-day entry is. A "worth trying," not an active problem.

**Two stale-documentation findings — both FIXED 2026-08-23:**
- `core.deliberation`'s in-file docstring/comments described its grounding call as routing to "the
  Emissary, Ramses qwen2.5" — stale since `left_lane.py` was repointed to `gemma4:12b` on
  2026-08-20. Fixed: now names `gemma4:12b` on the local judge-1 hub (127.0.0.1:11439), and the
  hot-lane fallback/integrate comments now say `qwen3.5:9b` instead of the old `qwen3-du`.
- `core/schema.py`'s `SERVE_URLS`/`SERVE_CHAINS` comments described the *pre-shuffle* roster
  (`gemma4:e4b` hot, `llama3.1:8b` judge_1, `qwen2.5:7b` judge_2, tiebreak on 11441) — superseded by
  the 2026-08-20 "full shuffle" that `core/model_client.py`'s `_MODEL_BY_BASE` (the table actually
  consulted at call time) correctly reflects. Fixed: header block and both dict comments now match
  `_MODEL_BY_BASE`. The `"tiebreak": 11441` dict *value* was also dead (confirmed by grep: nothing
  in the codebase reads `SERVE_URLS["tiebreak"]`/`SERVE_CHAINS["tiebreak"]` — `judge_panel.py`
  hardcodes its own tiebreak constant) — left the dead port in place but added an explicit comment
  explaining why, rather than silently repointing a value nothing consults.

**Everything else — the other 71 of 79 machines — was read and confirmed fine-as-is.** The full
per-module breakdown below is the receipt for that claim, not just an assertion of it.

---

## Full catalog, part 1: inside `_think()` — by batch (alphabetical slices of the confirmed 1457–3750 span)

### Batch A — `activity_memory` → `concerns` (15 modules)

| Module | Type | Job | Assessment |
|---|---|---|---|
| `activity_memory` | script | upserts the one general-event record for an (action_type, target) pair, returns a rolling summary | fine as-is |
| `affect_labeling` | script (regex) | detects a first-person named negative feeling in the thought text | fine as-is — module's own docstring defers LLM upgrade until Phase-0 data show a real miss-rate problem |
| `arousal` | script | composes ambient state into one global activation float | fine as-is |
| `associative_recall` | script (embeddings, not chat models) | spreading-activation trail of associated memories for a query | fine as-is |
| `balance` | script (SQL) | reality/light share ratios + remediation-gate booleans | fine as-is |
| `book_selection` | script | explore-weighted new book pick or motivated reread | fine as-is |
| `boredom` | script | tracks "stuck in one region," returns escalating escape directives | fine as-is |
| `broadcast` | script | tiny ring-buffer of high-value conscious-cycle winners | fine as-is |
| `cat` | script | state machine + authored content for the cat's presence/reactions | fine as-is |
| `chapters` (in-scope call) | script | keyword-match recall of a named life-chapter's excerpts | fine as-is (its LLM-authoring path, `try_form_chapter`, lives in the sleep pass — out of `_think()`'s scope) |
| `commitment_ledger` | hybrid — LLM(qwen3.5:9b hot) detection scan + LLM(background lane) defeater judge | detects/logs new stands, dissolutions, drops on the held-commitment ledger | **candidate — see finding #1** |
| `commitment_trials` | script | prediction-elicitation seeds / +7-day outcome read-back | fine as-is — deterministic outcome probe is a deliberate decoupled-judge-clean design choice |
| `companion` | script | narration + shared-state mutation for presence/actions (fire, tea, etc.) | fine as-is |
| `composition` | hybrid — LLM(qwen3.5:9b hot) drafts, LLM(gemma4:12b judge-1) grades | self-generated writing task, graded for groundedness, feeds competence | **candidate (soft) — see finding #6** |
| `concerns` | script | reads existing stores, returns standing aim / concern list | fine as-is |

### Batch B — `deliberation` → `math_drill` (16 modules)

| Module | Type | Job | Assessment |
|---|---|---|---|
| `deliberation` | hybrid — LLM(gemma4:12b via left_lane, judge-hub) grounds, LLM(qwen3.5:9b hot) re-integrates | grounds a self-referential thought in a real mechanism, then re-thinks it once | fine as-is (wiring); **docs are stale — see note above finding list** |
| `dispatch` | script (zero-LLM, fail-open) | classifies a willed act and fires at most one world-changing hand | fine as-is |
| `euclidean_recall` | script (numpy) | weighted-Euclidean nearest-neighbour memory recall + shadow comparison vs. semantic baseline | fine as-is |
| `frontier` | script | maintains/offers/resolves open "world questions" | fine as-is |
| `geometry_census` | script (observe-only) | logs one coordinate tuple (place/weather/objects/body/affect/...) per tick | fine as-is |
| `guidance_learning` (in-scope calls) | script | logs each moment a promoted-belief paraphrase is injected | fine as-is (its real LLM-graded formation logic lives in `_enter_sleep`, out of scope) |
| `hands` | script (zero-LLM) | opens/resets the fired-hands ledger, records the per-thought trace | fine as-is |
| `idle_allocator` | script (Phase-0 shadow) | logs what a would-be idle-executive would have picked, across 9 salience channels | fine as-is |
| `keepsakes` | script (deterministic) | detects a "keep/pocket/take home" verb, mints a durable mantel entry | fine as-is |
| `letters` | hybrid — script persists; LLM call inline in `_think` (background lane for Travis, hot lane for fictional peers) | composes and persists a letter body | **candidate CONFIRMED — see finding #4** |
| `librarian` | LLM(falcon3:7b judge-2, fallback gemma4:12b) | maps a carried question to catalogue subject headings | **candidate — see finding #5** |
| `library_hand` | script (CSV scan + fetch, zero-LLM) | switches/searches/fetches/shelves books from the SPGC catalogue | fine as-is |
| `light` | script (zero-LLM, trig) | illuminance field + shadow-logged brightening/darkening percepts | fine as-is |
| `listening` | script (deterministic, zero runtime DSP) | unfolds a chosen musical piece section by section | fine as-is |
| `literal_will` | script (Phase-0 shadow, hand-authored classifier) | DEED/MUSING/GRAY/HANDLE verdict per candidate intent | fine as-is currently — deliberately model-free by design; can't determine if a judge belongs here since that phase isn't built yet |
| `math_drill` | script (generator + deterministic grader) | arithmetic drill, grades without the LLM being tested | fine as-is — deliberately zero-LLM as a bias control |

### Batch C — `mineness` → `school` (15 modules)

| Module | Type | Job | Assessment |
|---|---|---|---|
| `mineness` | script (shadow-first) | authorship-error score → rare "arrival note" + ownership assessment | fine as-is — docstring explicitly commits to no-LLM |
| `moment` | script | stores a "moment" record; re-textures a recalled fragment into a cue | fine as-is — docstring: "no LLM, deterministic, fail-open" |
| `mood` | script | live affect → embedding/valence/preamble tagging most other fragments | fine as-is |
| `music_drill` | hybrid — script (gen + parser-grading) + LLM(qwen3.5:9b hot) for composing/solving | solves theory problems or grades ABC-notation compositions | fine as-is — grading intentionally scripted, same pattern as math_drill |
| `nature_study` | hybrid — LLM(qwen3.5:9b hot) generates, LLM(gemma4:12b judge-1) grades | scene → graded naturalist observation + feedback | fine as-is — generation/judging split matches capability to task |
| `night` (in-scope call) | script | vivid recent dream → one-line waking-image seed | fine as-is / mostly N/A — night's heavier machinery runs outside `_think()` |
| `peers` | hybrid — script bookkeeping; LLM(qwen3.5:9b hot) writes replies; LLM(gemma4:12b→falcon3:7b) picks a contrary target | letter reply/initiation, or picks who'd see an unaddressed question | fine as-is — creative writing gets the bigger model, persona-pick gets the judge tier |
| `phrasing` | script | non-repeating phrased line from template variants | fine as-is |
| `prompt_budget` | script (shadow-only) | logs seed/prompt size and shape | fine as-is |
| `pulse_shadow` | script | logs idle-seconds as a pulse observation | fine as-is |
| `pursuits` (in-scope call) | script | tracks/returns an open pursuit thread on wandering | fine as-is — docstring: "no LLM, cooldown-gated"; its LLM judge, `judge_pending`, only runs from the sleep pass |
| `reading` | script | next reading chunk / session batch / "open the book" seed | fine as-is — the LLM work (study notes) lives in sibling modules |
| `retraction_ledger` | script (token-overlap matcher) | matches an about-to-be-thought seed against a logged retraction | **candidate (weak) — see finding #7** |
| `satisfaction` | script | logs a completed act as a satisfaction-event | fine as-is |
| `school` | script | timetable gating for lesson subjects/quotas | fine as-is — pure scheduler, actual grading lives in sibling subject modules |

### Batch D — `self_implication` → `wandering` (18 modules)

| Module | Type | Job | Assessment |
|---|---|---|---|
| `self_implication` | LLM(qwen3.5:9b hot) | 6-signal breakdown + verdict on whether a thought is a genuinely self-implicating hard event | **candidate — see finding #2** |
| `self_interrogation` | hybrid — LLM(qwen3.5:9b hot) generates, LLM judge panel (gemma4:12b + falcon3:7b, tiebreak yi:34b-v1.5) grades | reflection on an earned thought-train, judged for genuine reconsideration vs. performed humility | fine as-is — already the decoupled pattern `self_implication` is missing |
| `sensorium` | script | renders causal room/world state into a one-line scene | fine as-is |
| `sitting` | script | dwell-cycle counter, gates meaning-making until minimum dwell passed | fine as-is |
| `smell` | script | odorant sources/intensity from world state (shadow-only, not yet delivered) | fine as-is |
| `soundscape` | script | live world state → delivered ambience/sound-percept line | fine as-is |
| `spatial` (in-scope call) | script | shadow-compares pooled scene vs. authored-geometry egocentric render | fine as-is |
| `study_life` | script | gates reading on the study's light-state | fine as-is |
| `study_note` | hybrid — script (retrieval/dedup/filing) + LLM(background lane) composes/revises | passage → structured study note, filed new or deepened | **candidate CONFIRMED — see finding #3** |
| `symbol_evolution` (in-scope call) | script | readback of an evolved neutral-symbol meaning into the seed | fine as-is — its LLM call (`write_tablet`) lives in `orchestrator.py`, outside `_think()` |
| `tension_ledger` | hybrid — script (candidate-matching) + LLM judge panel (gemma4:12b + falcon3:7b, tiebreak yi:34b-v1.5) | confirms genuine settlement of an open tension vs. mere restatement | fine as-is — same decoupled pattern as `self_interrogation` |
| `theme_recurrence` | script | time-decaying restate counts across long horizons, catches slow-loop rumination | fine as-is |
| `thermal` | script | felt-warmth/wetness fields (shadow-only, not yet delivered) | fine as-is |
| `thermal_relationship` | script | logs warmth/place/weather + temperature vocabulary + felt valence for offline analysis | fine as-is — module's own docs say any stance-rating is offline/cross-family, not live |
| `told` | script | gates delivery of Travis's one-time authored message on a reality-share threshold | fine as-is — the actual delivery LLM call lives in the sibling `_deliver_told` method |
| `train_metrics` | script | logs a closed train's length and why it ended | fine as-is |
| `trains` | script | registry minting/tracking/closing train ids and cargo records | fine as-is |
| `wandering` | script (embeddings, zero-LLM) | maintains/updates the associative wandering trail used as seed text | fine as-is |

---

## Full catalog, part 2: the other 15 machines — called elsewhere in this file, or not called from it at all

These were excluded from the four `_think()` batches above because their call site sits outside
lines 1457–3750 — inside the nightly sleep pass, per-tick logging, or prompt construction, all
still within `inner_monologue_node.py` — or because the module isn't imported in this file at all.
Same rigor, same format, with a **WHERE** column added since "inside `_think()`" no longer applies.

### Group 1 — called elsewhere in `inner_monologue_node.py`

| Module | Type | Job | Where | Assessment |
|---|---|---|---|---|
| `competence` | script (zero-LLM, delta-rule bookkeeping) | folds a drill result (correct/incorrect) into a domain's rolling accuracy belief | `_music_lesson` (959), `_math_drill` (1042) | fine as-is |
| `book_feelings` | script (deterministic EMA blend) | returns a joy-multiplier scaling reading-joy by how this book has felt so far | `_stream_integrate` (1238) | fine as-is |
| `book_residue` | script (observe-only, zero-LLM) | scans recent thought/dream text for resurfacing signatures from long-closed books | `_enter_sleep` (553), nightly sleep batch | fine as-is |
| `buses` | script (zero-LLM) | joins prediction→outcome episodes into the world-calibration ledger | `_enter_sleep` (606), nightly sleep batch | fine as-is |
| `affections` | script (zero-LLM, deterministic tally) | rebuilds the "loves ledger" from stated likes, stores a recallable affection past 2+ recurrences | `_enter_sleep` (461), nightly sleep batch | fine as-is — deliberately avoids embeddings/LLM per its own docstring (a prior design was abandoned as "write-only for valence") |
| `affordances` | script (template repertoire, zero-LLM) | builds the "what is within reach right now" context block | `_build_system_prompt` (1294), every cycle | fine as-is — prompt-construction plumbing, not a cognition step |
| `affect_divergence` | script (zero-LLM, fail-open logging) | logs carried-mood valence vs. grounded-protoself valence side by side | `_log` (4235), per-thought logging tail | fine as-is — deliberately model-free so it can't contaminate the signal it's auditing |
| `journal` | LLM(qwen3.5:9b, hot lane :11433) | turns the day's logged deeds + affect into one first-person nightly journal entry; also extracts stated likes for `affections` | `_enter_sleep` (437-442), nightly sleep pass | fine as-is — the hot lane here was deliberately benchmarked and chosen for persona/style discipline over the background lane ("where phi3 went dry and confabulated, 2026-06-21") |
| `journal_rollup` | LLM(qwen3.5:9b, hot lane :11433) | authors one weekly "what he did / what the world did" page synthesized from ~14 daily entries | `_enter_sleep` (~450), nightly, at most once/week | **candidate (soft) — see finding #8** |

### Group 2 — not imported in `inner_monologue_node.py` at all (call sites found elsewhere in the codebase)

| Module | Type | Job | Where | Assessment |
|---|---|---|---|---|
| `attention_schema_loop` | script (zero-LLM, EMA/persistence predictor) | predicts next-cycle attention bandwidth, scores prediction error, optionally reweights attention (currently flag-off) | `core/orchestrator.py` (`observe_schema`/`control`, every conversational cycle), `hud/server.py` status hook | fine as-is — deliberately content-blind by design; shadow-only, doesn't steer anything live yet |
| `audio_features` | script (zero-LLM, DSP via ffmpeg+numpy) | extracts tempo/key/energy/section features from decoded audio, derives a plain-English descriptor + a bounded felt-vector nudge | `core/listening.py`'s `tick()` (reached transitively from `_think` via the LISTEN latch) | fine as-is — explicitly "a translator, not an author" |
| `axiom_layers` | script (zero-LLM, schema/dict helpers) | the single shared reader/writer for the layered L0-L5 axiom JSON | `core/orchestrator.py`, `nodes/subconscious_node.py` (T4 self-authoring), `core/emissary.py`, `core/provisional_identity.py`, `core/self_efficacy.py`, `core/memory_levels.py` | fine as-is — **not dead code**, one of the most load-bearing identity-system utilities in the codebase |
| `book_splitter` | script (zero-LLM, regex chapter detection) | splits raw book text into chapter/section spans so reading can stop at boundaries | `core/reading.py`'s `chapter_end_offset()` | fine as-is |
| `cat_content` | script (static authored line pools) | supplies pre-written "house voice" lines for the cat's presence/reactions | `core/cat.py`'s `_content()` (itself reached from `_think` via `cat`/`affordances`) | fine as-is — a content corpus, not a generation step |
| `climate_engine` | script (zero-LLM by explicit architectural law) | recomputes the 9-dimension "standing psychological weather" every 5s, ticks the dissonance accumulator that triggers autonomous thought | `core/orchestrator.py.__init__` (shared onto `CognitiveState.climate`/`.dissonance`, reaching `_think` as shared state, not a direct import) | fine as-is — the module's own docstring treats "summarise the climate in a sentence" as a design smell to resist |

**All 15 resolved to real, confirmed call sites — none were dead code**, including the six that
looked orphaned from `inner_monologue_node.py` alone. Only two of the fifteen are LLM machines
(`journal`, `journal_rollup`); the other thirteen are zero-LLM by explicit design, several with
docstrings stating "zero LLM" as a load-bearing architectural constraint rather than an oversight.

---

## What this confirms and what it doesn't

**Confirms:** the founder's instinct that "some scripts, some LLMs, some need to be smarter than
others" was correct in specific, nameable places — 8 real candidates out of 79, concentrated
exactly where you'd predict: judgment tasks quietly inheriting a cheap/fast lane instead of the
judge tier, and one real writing task (a letter to Travis) getting worse treatment than its
fictional counterpart. The overwhelming majority (71/79) were already correctly matched — most of
the non-LLM "script" modules are *deliberately* zero-LLM by explicit design (bias controls like
`math_drill`, shadow-first instruments like `mineness`/`geometry_census`, fail-open safety modules
like `dispatch`/`hands`, or architectural laws like `climate_engine`'s) rather than under-resourced.

**Doesn't show:** whether any of the 7 candidates actually improve outcomes if reassigned — none of
this has been lab-tested the way the Ramses model comparisons were. This is an architectural map of
where a stronger model *could* be slotted in, not a verdict that it *should* be, yet. Per this
session's established discipline, none of these seven should be built without a further explicit
decision — this doc is the punch list for that decision, not an implementation.
