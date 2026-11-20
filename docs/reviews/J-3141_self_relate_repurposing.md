# J-3141: Repurposing review of the T1 self-relate check (SubconsciousNode._self_relate_check, row P-0052)

Read-only design review, 2026-11-05. No Du code, store or log was edited; Du kept running. Founder ask (triage 2026-11-02, thought T-0115): "do NOT retire this. Look at how it could be used in our systems." Evidence: findings F-3930, F-3931, F-3932 (this job) on top of F-3834, F-3835, F-3836 (J-2732, the prompt sweep). Confidence is tagged [verified] (I read the file or ran the query), [inferred] or [guess].

## 0. The answer in six lines

1. The pass writes a sentence nobody reads, authored by command-r7b about Du, from input that is 78 percent his own idle thoughts. Flipping its flag (the planned "change D") would store a model-authored first-person "realization" as his memory, judged by nothing. Do not do that. [verified, F-3836, F-3930]
2. Of the four consumers you named, none can take the **sentence**. T2 wants tension events; the climate field forbids any LLM; the Follow Line takes only his own words. T4's evidence stage is the one real gap, and it needs **retrieval**, not a sentence. [verified, F-3931]
3. The function (relate what he has engaged with in the world to who he takes himself to be) transfers to two places that already have the machinery and a decoupled judge: **T4's evidence stage** (a world-contact pool, option 1) and **the Follow Line as a self-claim intake** (his own first-person claims tested against his own past, option 2).
4. Recommendation: **repair in shadow**, in two moves. Now: a small restart-gated repair (J-3341) that stops the hot-lane leak and makes the log auditable. And two read-only labs (J-3339, J-3340) that decide whether either option earns a build. Archive trigger and revive note in section 6; a dated read job (J-3342, not before 2026-12-05) so nothing waits on memory.
5. One founder call: **D-0678**, may his own self-claim board the Follow Line (shadow first, delivery capped at one a day)? It sits across your 06-23 reframe. Not blocking.
6. Honest limit: under either option the sentence generator itself is replaced. What survives is the slot, the cadence idea and the finding that his world-engagement input is crowded out by his own thoughts.

## 1. The function it was built to serve, in one sentence

To move the "how does this relate to me" work out of the conscious stream and under the surface, so that what he engages with in the world is quietly related back to who he takes himself to be and can later surface as a realization (module comment `nodes/subconscious_node.py` ~317 and `docs/archive/conscious_subconscious_reframe_spec.md` section 3B and 3D).

The reframe's words, as the spec records them: "the inner monologue is the cause, it is too focused on the self"; the subconscious "should be the one that owns 'who am I, how does this relate to me.'" And the line it was built on: "by not thinking about myself for a while and just being, it sometimes bears fruit." The spec itself says A (strip conscious self-musing) "must ship with B+D, not alone." B (this pass) shipped in shadow; D (surfacing) was never built; no plan or decision owns it (F-3834).

## 2. What the evidence says it can and cannot do today

**Can** (verified, F-3930, re-measured today with Du running): fire about 25 to 32 times a day at a median 1.85 s; 196 calls and 26 minutes of model time in 7 days; write a sentence per tick to `data/self_relate_shadow.jsonl` (2127 rows since 2026-06-23). The output has moved with Du's world: in the last 2 days 0 of 64 sentences name the river (9 of 116 before) and 15 of 64 name the sea, tide or oystercatcher.

**Cannot** (verified unless marked):
- **Nothing reads it.** Only the HUD gauge `n_world` does, and `n_world` is 8 in 2118 of 2127 rows (F-3834, F-3930).
- **Its input is not "world engagement".** 78 percent of the input slots over the last 7 days are his own `inner_thought` (1127 of 1440); only 72 of 180 ticks had any reading, study or research fragment, while the store held 4308 reading fragments in the same week. The recency-ordered `LIMIT 8` lets his own thoughts crowd the world out (F-3930). The repo also has three different definitions of "world origin" (F-3931).
- **Its verdict never says no.** `connects` is True in 1927 of 2127 rows; the only False rows since 2026-10-01 are 2026-10-18 and 2026-11-04 01:34 (F-3835, F-3930). No judge ever grades whether a connection is genuine.
- **It restates what it is fed.** In the last 2 days the cat clause from the self_image line appears in 34 of 64 sentences (57 of 116 before): weaker than the 46 of 91 in F-3835, not gone. 66 of 180 recent sentences have no first-person word ("the speaker", "the narrator"); 94 of 180 hit the 240-character log cap.
- **It cannot be audited.** The log keeps 240 characters of the output and nothing about the input (no fragment ids, no origins).
- **It leaks onto Travis's lane.** 27 of 180 successful calls (15 percent) landed on the hot conversation lane qwen3.5:9b :11433 via the background chain's fallback; another 16 failed outright (F-3930).
- **Enabling it as built would write into retrieval.** `core/euclidean_recall.py` gives `subconscious_synthesis` provenance 0.60 and an abstraction bump 0.20; `core/chapters.py` lists it as chapterable; `core/book_residue.py` counts it as a self origin (F-3836).

Founder-law check today: no breach, because Du never sees the output. The danger is any path that puts it in front of him.

## 3. Repurposing options

### Option 1: a world-contact evidence pool for T4's evidence stage (RECOMMENDED, lab first)

**The gap.** T4's evidence stage retrieves the 6 nearest of the 300 newest `light_events` to the tension (`_t4_retrieve_crossings`), 97 percent his own idle thoughts per J-3252, then rules whether he has moved (`has_movement` true 81 percent). Stage 4 (synthesis) already gets `recent_world_material(limit=6)` under `WORLD_FED_T4`; the stage that decides movement does not. Evidence for "have I moved on this?" is thus mostly his own musing about it, the exact "monoculture in a lab coat" that `core/evidence_recall.py` was built to avoid.

**The transfer (function, not mechanism).** The self-relate pass's idea is "pair what he engaged with in the world with who he takes himself to be". The function needed here is "find world-contact episodes that bear on a standing tension", which `core/evidence_recall.gather` already does (world origins only, a two-family panel, refute-biased). The sentence is not needed at all.

- (a) **Consumer.** `nodes/subconscious_node.py` `_t4_deliberate` stage 2, as a **second, additive pool** beside the existing one (flag off, logged first). What changes for Du: nothing in prompts or replies; T4's has_movement ruling would see lived and read episodes as well as his own thoughts. No new outlet, so D-0549 ("add no new outlet") is not touched; the live use stays behind D-0664 and the Restart A merged logging build.
- (b) **Input.** The primary tension label (already computed), world-origin fragments of the preceding 7 days (`evidence_recall.WORLD_ORIGINS`), embeddings the store already holds. Supply is not the constraint: 4308 reading, 959 action, 323 study, 245 lived and 159 research fragments in 7 days.
- (c) **Decoupled check.** The two-family panel on the Ramses hubs (falcon3, granite), never the T4 author (qwen3.5:9b) and never the T4 admission judge (gemma4:12b); plus two control arms (random world fragments, and fragments retrieved for a different candidate's tension), because the Watershed claim-test said yes to 12 of 12 control sets (F-3867, F-3868 via J-3252 C8).
- (d) **Success.** At least 40 percent of tensions have a panel-agreed bearing world crossing; real yes-rate at least 0.30 above the better control with agreement at least 0.7; at least half the bearing crossings are not already in the own-thought top 6.
- (e) **Stop.** Any criterion fails: archive this option. Job **J-3339** (lab, read-only, `lab_env.isolate()`).
- Law check: the world answers (his own lived and read episodes, nothing authored); additive (current pool untouched); judged by a different family; nothing acts later on its own.

### Option 2: a self-claim intake for the Follow Line (shadow first; founder call D-0678)

**The gap.** The founder's own diagnosis of the Follow Line: "what they never seem to do is to follow a claim. They never back up what they believe with why or facts" and "He should reason on all questions no matter where they come up" (`docs/staged/question_cargo.md`). His claims about himself are the least tested claims he makes ("I am the resistance carved by abstract leverage..."). Meanwhile the line's own docstring limits cargo to "his own `ask` field, his own frontier births, his own study-note claims and his own pursuit questions board", so a command-r7b sentence can never board, but a first-person claim **of his** can, as source `claim`.

**The transfer.** The function "relate what I have taken in to who I think I am" becomes "test what I say I am against what I have lived and read", with his own words as the cargo, by the line that already grounds, argues against and judges.

- (a) **Consumer.** `core/follow_line.board()` with a new source `selfclaim` fed by a deterministic first-person-claim selector over his idle thoughts; the graded return is delivered to the next idle thought exactly as any line return is, he answers `settled` yes, partly or no. What changes for Du: now and then a claim of his own comes back with grounds and an against line, as a question of his, never as a statement to him and never saying what to do. Cap: one self-claim return a day, inside the line's existing 4 boardings an hour.
- (b) **Input.** His first-person sentences. Supply is about 25 a day by a crude regex (178 sentences in 7916 idle thoughts, all distinct, F-3932), but in 8 random rows most are present-moment states ("I am steady here ...", "I am alone with the cold grate") rather than claims. The testable fraction is unmeasured [inferred].
- (c) **Decoupled check.** The line's existing `core.judge_panel` on the claim alone, plus the lab's own blind labelling by two different-family judges and a hand read.
- (d) **Success.** At least 20 percent of sampled first-person sentences are claims (judge agreement 0.7), at least half of those get a panel-agreed bearing ground, at most half are restatements of the river/becoming stock.
- (e) **Stop.** Any criterion fails, or a 14-day shadow shows the graded returns are mostly the monoculture re-circled: archive. Job **J-3340** (pre-test, isolated).
- **The tension, stated plainly.** On 2026-06-23 you moved self-examination out of the conscious stream. A delivered self-claim return puts a "who am I" item back in front of the idle thought, though as a tested question and capped. This is why delivery is D-0678 and not a build; the shadow log and the pre-test do not need the answer.
- Law check: only his own words board; the world answers; function not mechanism; a different-family judge; delivery is a founder call, nothing acts later on its own. The risk is the reframe's own: more foreground self. The cap and the shadow-first rule are the guard.

### Considered and rejected

- **T2 intake.** T2 fires on recurring shadow-event tension clusters (header, `nodes/subconscious_node.py`) and is already world-fed; a model-authored sentence is not a tension event, and putting one into T2's evidence would feed a command-r7b sentence into the first-person self-observation T2 writes, a loop of authorship.
- **Climate field.** `core/climate_engine.py`: "NO LLM ANYWHERE IN THIS FILE", the load-bearing constraint that keeps the medium timescale from becoming a fourth autobiography layer. A deterministic world-versus-self share already exists (`core/balance.py` `reality_share`, no LLM), and `identity_pressure` already measures pressure on the self-concept. No gain.
- **Flip `SELF_RELATE_ENABLED` and build the surfacing hook (change D as designed).** Stores a model-authored realization as his own memory with provenance 0.60, judged by nothing, restating his self_image (F-3836). Breaches "every subsystem judged by something other than itself" and "world answers, never leads".
- **A T4 evidence input that is the sentence** (relation text as a crossing): puts an authored paragraph into the stage whose point is lived evidence. Same trap.

## 4. Recommendation: repair in shadow, gated by two labs

- **Wire it:** no. Nothing it produces can be wired as built (section 2), and any wiring is a plan-level decision the labs have not yet earned.
- **Archive now:** not yet. You said do not retire it; it costs 26 minutes of model time a week; and the two options in section 3 are cheap to test offline. Archive is the default if both labs fail.
- **Repair in shadow:** yes, minimally, in two parts.
  1. **J-3341** (build, restart-gated, `subconscious_node.py` group): pin the call to the single Ramses endpoint the Follow Line uses (`http://LAN-HOST:11441`, skip when down) so it stops using Travis's lane; take the input origins from `evidence_recall.WORLD_ORIGINS` rather than a fourth definition; log fragment ids, origins and a self_image hash; replace the pegged `n_world` gauge field. Prompt wording unchanged, so the registry text is unchanged. Its honest value is the lane leak and an auditable record, not a better sentence.
  2. **J-3339 and J-3340** (labs, read-only): the two options above. If either passes, its build replaces the pass's sentence output. If both pass, option 1 first (it fixes a stage that decides T4 verdicts, and needs no founder call).
- **Plan home on success:** option 1 belongs in `t4_watershed` (evidence intake; sequence after Restart A of J-3252 section 5 so the `_t4_deliberate` hunks do not collide); option 2 belongs in `question_cargo` (a new Follow Line source, in the `core/follow_line.py` group of the marathon brief).

## 5. What needs a founder call

- **D-0678** (opened, plan `question_cargo`): may a self-claim of his own board the Follow Line, shadow first, delivery capped at one a day? Recommendation: yes for shadow logging and the pre-test now; decide delivery after J-3340 shows the testable share. Not blocking; J-3340 runs either way.
- No other call. "Repair in shadow" and the two labs are inside your own do-not-retire ruling.

## 6. Archive-and-revive note (the stop condition)

**Trigger (a dated read, not an automatic switch):** J-3342, not before 2026-12-05. If both labs failed their stop criteria, move `_self_relate_check`, its call block in `run_forever` and the `SELF_RELATE_*` constants to `docs/staged/` (restart-gated, `subconscious_node.py` group), keep `data/self_relate_shadow.jsonl` as the record, and retire P-0052 in the registry. If one lab passed, J-3342 closes as superseded by that lab's build.

**Revive only if** Du, unprompted, brings a self-theme from his own world-engagement and asks what in his reading or living bears on it; then the index is his question and this pass's slot (a background-lane, once-in-45-minutes world-to-self read) is the place to hang it. Do not revive it as a generator of first-person sentences.

## 7. Method and limits

- Read in full: the module docstring and the pass (`nodes/subconscious_node.py` 1-60, 300-335, 560-690, 2335-2400, 2462-2500), `core/follow_line.py` docstring and `board()`, `core/climate_engine.py` docstring and the field, `core/evidence_recall.py` docstring and `gather`, `core/balance.py` head, the reframe spec in full, J-3252 sections 0 to 9, J-3140 as a format sibling, F-3834 to F-3836, D-0664 and D-0549 as quoted by J-3252. I did **not** read `hud/server.py:701` again (I rely on F-3834 for the gauge and re-measured `n_world` from the log), and I did not re-measure J-3252's 97 percent own-thought figure.
- Measurements: all log rows streamed (`sr_stats_J-3141.py`, `sr_stats2_J-3141.py`), the tick-by-tick input reconstruction (`sr_inputmix_J-3141.py`, sqlite `mode=ro`, re-running the module's own query at each of the 180 logged ticks), latency rows (inline, `data/llm_latency.jsonl`), the self-claim regex (`sr_selfclaim_J-3141.py`).
- **Corrects F-3834's volume:** 91 rows and 102 calls in 7 days was a window with Du partly down; with Du up it is about 180 and 196. The inference is unchanged.
- The self-claim count is a crude regex and my read is of 8 rows (F-3932, inferred). Option 2's viability rests on a number the pre-test measures.
- I did not run any model: the options are untested designs. Nothing here was verified live beyond the log and store reads above.

## 8. Index

- Findings: F-3930 (current state, input mix, cost, lane leak), F-3931 (consumer fit; three world-origin definitions), F-3932 (self-claim supply, inferred). Earlier: F-3834, F-3835, F-3836.
- Decision opened: D-0678 (plan `question_cargo`).
- Jobs spawned: J-3339 (lab, T4 world-contact evidence), J-3340 (pre-test, self-claim intake), J-3341 (build, shadow repair, restart-gated), J-3342 (archive-or-keep read, not before 2026-12-05).
- Registry: P-0052 note updated.
