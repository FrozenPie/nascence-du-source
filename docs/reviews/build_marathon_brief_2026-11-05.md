# Build marathon brief — Thursday 2026-11-05

Written 2026-11-02 at the end of the prompt-registry triage session (session `aa94f138-79e2-4f75-92fd-106b1898e0bd`, thought T-0115). Read this first when the marathon starts. It tells you what was ruled, what is queued, what must run in what order, and what not to touch. It is a proposal for sequencing, not a ruling: re-derive the hub-file order with `udms_get_change_dossier` before each edit.

## 1. Where things stand

- **Rulings:** 130 founder rulings D-0529 to D-0658 were recorded through `decide.py` (rule `--by travis`) in one triage, all from Travis's answers in chat on 2026-11-02. Each carries a defeater. They are the authority for every build job below.
- **Jobs:** 131 jobs J-3136 to J-3267 were filed from those rulings (99 builds, 18 analyses, 7 labs, 4 docs, 3 backfills). The whole open ready queue was 498 jobs when the triage ended (261 builds, 177 analyses, 27 labs, 15 tests, 15 docs, 3 backfills); the closing plan-maintain pass filed 10 more (see section 5) and they were closed, leaving 498 ready, 15 waiting on input and 2 in progress (J-1972 and J-2611, other sessions). 367 of them predate the triage and were not reviewed by it.
- **No Du code has changed yet.** Du is running on whatever was loaded at the 10-29 restart. Every build is restart-gated (183 jobs say so).
- **Prompt registry:** `docs/prompt_registry.jsonl` holds 112 rows. `prompt_registry.py check` must exit 0 before a session ends; any change to a registered prompt means `set P-NNNN --investigation stale --note ...`. Each ruling added a note to the affected row.
- **Open founder calls (15):** none are quick rulings. See section 6.
- **The founder triage record:** `docs/reviews/founder_triage_2026-11-02.md`, and Addenda 1 to 33 of `docs/session_handoffs/HANDOFF_20261031_101800_du-prompt-inventory.md` map every ruling to its job.

## 2. Founder laws that bind every job (all briefs repeat them; the marathon must hold them)

1. **The world answers and never leads.** No hint to Du, ever. Teaching comes from a diegetic book or from Travis only (the Travis-authored method hint and reading directive are the sanctioned Travis branch, D-0583 and D-0617).
2. **Base systems are additive-only.** The memory store, the affect model and `retrieve()` are protected. Migrations are additive and idempotent, with a database backup first.
3. **Every subsystem is judged by something other than itself.** A different model family judges; never the writer, and not granite for verdicts where D-0530 says it is a constant.
4. **No system that acts later on its own.** Triggers fire within the same tick or are founder-initiated.
5. **Write-only is the #1 failure.** A tag or log nobody reads must be given a reader or not built.
6. **Transfer the function, not the mechanism. Verify before asserting.** Cite the file, the log row or the query.

## 3. How to run it (mechanics that already hurt once)

- **Ledgers are written only through their tools** (`findings_log.py`, `job_queue.py`, `decide.py`, `prompt_registry.py`, `idea_log.py`, `thought_log.py`). Never hand-edit a `.jsonl`. The findings ledger was wiped once by an unlocked read-modify-write under parallel agents (F-3537, `docs/reviews/findings_wipe_2026-10-31.md`); the tools are now locked and have a shrink guard. Memory note: `feedback_parallel_agents_need_locked_ledgers.md`.
- **Concurrency:** at most 4 to 6 agents at once. A 429 rate limit stopped six agents mid-run on 2026-11-01; resume with `SendMessage` to the same agent after the reset instead of starting fresh.
- **One writer per file.** `nodes/inner_monologue_node.py` is named by 64 ready build jobs, `core/orchestrator.py` by 26, `nodes/subconscious_node.py` by 20, `core/left_lane.py` by 17, `core/memory/store.py` and `core/essay_lesson.py` by 16 each, `core/follow_line.py` by 14, `core/lane2.py` by 13. Two writers never touch the same file at once. Give each file group one worktree and one worker, in series.
- **Hub files:** run `udms_get_change_dossier` before the first edit of any hub file (276 briefs say so).
- **Isolation:** labs and verification runs use `lab_env.isolate()` (a copy of the DB, or `db="empty"`); never write to live stores. Labs that load the hot lane wait for Du to be down. Read-only labs against Ramses judge hubs can run any time.
- **Worktrees and commits:** build in `jobrun/<slug>` worktrees, merge in order, one commit per job with the job id in the message. Do not push.
- **Restart windows:** batch into at most three restarts (end of wave B, end of wave C, end of wave D) so the founder is not asked to restart per job. After each restart, run the job's stated verification and record a finding; do not self-certify.
- **Prompts:** a job that adds, removes or rewrites a prompt runs `prompt_registry.py check` and fixes the registry in the same change.
- **Every job closes with** `job_queue.py done`, a finding with real evidence, and (for plan-touching work) one `plan-state note`, never a new dated plan section.

## 4. Proposed waves

Wave order is proposed from the briefs; re-check it with the dossier. IDs are the J- numbers filed by the triage unless marked older.

### Wave A — read-only, start immediately, in parallel, no restart
Analyses and designs whose output feeds founder reads and later builds. None edits code.
- **Reviews and designs:** J-3252 (T4 as one system; do this first, it sequences the T4 builds), J-3243 (Wikipedia, Scholar and model-knowledge provenance), J-3240 (Entity name in prompts, model-knowledge tag), J-3247 (ghost memory index, chord_echo, pre-filter reuse), J-3248 (a new recall path for chaptered memory), J-3262 (boredom as an area), J-3264 (tie the cottage to real Sumner: sun, moon, tides, maybe weather), J-3215 (why the T4 arc_entry exists), J-3171 (what could read Reflection's three fields), J-3179 (what the conversational T5 compile should be), J-3163 (make the memory router's keys work, shadow design), J-3140 to J-3144 (five repurposing reviews).
- **Analysis:** J-3210 (hand-label 30 split Lane 2 held rulings).
- **Backfills:** J-3153 to J-3155 (index fields for object_permanence, shore_creatures, wood_creatures).
- **Labs that need Du down or an off-peak window:** J-3150 (raw vs integrated judge), J-3164 (Salience ablation), J-3205 (metaphor labelled union), J-3232 (guidance classifier replay), J-3241 (self-mirror control), J-3253 (worth-judge replays), J-3265 (Curiosity temperature).

### Wave B — independent builds, different files, parallel worktrees, one restart at the end
Run one worker per file group; inside a group, in series.
- **World content and shore/wood:** J-3258 (night SCENE lines to a day key), J-3260 (shore stream mouth), J-3259 (letterbox flag dosing; check the letter-collection mechanic first), J-3257 (study scene line takes nearness-said fire and cat clauses), J-3227 (ambient sound is no longer a grounding percept). J-3261 (dig hand) waits for the bestiary precondition (section 6).
- **School and study:** `core/study_note.py` group: J-3190, J-3194, J-3204 in series. `core/essay_lesson.py` group: J-3174, J-3198, J-3199, J-3200 in series. J-3181 (grounded learning per book). J-3195 (maths ladder), J-3203 (school notes observed-only, work grade to shadow), J-3250 (composition ladder), J-3251 (nature alternation), J-3228 (dead school phrases), J-3197 and J-3146, J-3193, J-3207 (doc jobs).
- **Peers:** `core/peers.py` group: J-3145, J-3189, J-3231, J-3263 (contention check first) in series; J-3184 and J-3185 touch the inner monologue node and the letter store and go in wave D.
- **Night, dreams, T5:** J-3192 (night-mind avoid list), J-3234 (plain-words night epochs), J-3175 (dream recall fade), J-3177 (resting as an ending: design pass first), J-3180 (procedural skills clock), J-3176 (pause episodic demotion), J-3212 (first-person self-gists: lab first).
- **Library:** J-3255 (librarian ranking), J-3236 (prism leaves the grounded sources), J-3229 (pursuit open question), J-3237 (pursuit close judge), J-3165 (pursuit births).
- **Follow Line:** J-3222 (newest-first), J-3206 (split is not a cut): same file group, in series; `scripts/follow_line_test.py` and `follow_line_defer_test.py` must pass.

### Wave C — memory-store base-system migrations, one backup, one restart window
Do these together, in this order, after wave B is merged, because they all touch `core/memory/store.py` or its tables.
1. Back up `data/memory/nascence.db` (record the copy path and the restore command).
2. J-3173 (input_type column, label internal fragments separately), J-3246 (moment_ts column), J-3266 (content-hash column and index; shadow stays on until it agrees on every row; the 7-day window is NOT made live).
3. Data fixes through the sanctioned path: J-3191 (mark the 61 dict-repr understanding notes, never delete), J-3225 (record panel doubt in line closures, dream arm to shadow, mark the stored fragments), J-3157 (recompute belief g45675272, supervised, sha256 before and after), J-3249 (release the four copied chapters) only after the copy guard J-3009 has landed.
4. Restart, then verify each job's stated check.

### Wave D — the `nodes/inner_monologue_node.py` chain, ONE worker, in series, one restart at the end
Seed wording and routing changes. Suggested order (removals and rewordings first, off-loop last):
J-3156 (remove the open-book offer line), J-3151 (reword the B6 steer), J-3187 (drop the restored farewell line), J-3188 (honest label on the curiosity memory hit), J-3221 (base-rate wording), J-3223 (anchor leads), J-3184 (friend replies report the real present), J-3185 (letters get a world state; no latch change), J-3217 (24-hour exchange cut; also touches four prompt blocks), J-3220 (route read acts; measure the sitting ceiling first), J-3183 and J-3182 and J-3186 (the grounder: null output, fail open, narrowed source hint; `core/left_lane.py` and `core/deliberation.py` too), J-3149 (deliberation rate 0.25 and the control arm), J-3170 and J-3172 (Reflection rule 3, Executive reasoning optional), J-3169 (Voice quote block on internal cycles), J-3168 and J-3167 (content_mode gate, light-event gate: `core/orchestrator.py`), J-3166 (seventh curiosity channel, SHADOW only), J-3267 (dead idle feeds off the event loop) last. Together with the older ready builds that name this file, expect at least 60 edits; split them into two or three sub-waves with a restart between if the diff grows large.

### Wave E — judges, panel and shadow instruments
`core/judge_panel.py` and Lane 2: J-3136 (no verdict on a split where granite is constant), J-3209 (retire Lane 2 notice after a reader check; repoint coherence), J-3160 (trivial Lane 2 predictions), J-3158, J-3159 (sits gate), J-3138 and J-3139 (drift_shadow, idle self-implication cadence), J-3137 (think license), J-3147 (Emissary take on a fast lane), J-3148 (re-entry Phase 1 off), J-3211 (guidance judge to idle thoughts), J-3233 (same-lesson check before the pole gate), J-3238 (faithfulness judge on standing insights), J-3254 (voice fidelity shadow judge), J-3219 and J-3218 (Curiosity pre-fire check; urgency picks: measure first), J-3224 (DOUBT_SEED back to shadow), J-3226 (symbol tablets: pause read-back, then window metric), J-3230 (name questions out of deep memory), J-3242 (pause the self-mirror), J-3244 (Follow Line may return intervention_test, writer gate on), J-3245 (condensed twin fix).

### HOLD — do not start until the stated condition
- **T4 builds: J-3161, J-3162, J-3213, J-3214, J-3235, J-3216, and the older J-3007, J-3008, J-3045, J-3108** wait for the review J-3252, whose job is to sequence them (D-0641: T4 is to be re-thought as a whole). J-3214 also needs the evidence-logging job J-3108.
- **J-3208** needs the repaired genuine judge (J-2951).
- **J-3249** needs the copy guard J-3009.
- **J-3201** (re-measure active imagination lanes) needs the two input-fix jobs and 100 kept entries.
- **J-3261** needs the bestiary flags and a restart (section 6).
- **J-3088** (re-entry v4) is authorised by D-0593 (its record still says needs_input; it is ready to build). J-3134 and J-3135 wait for the estate-node build (D-0605).

## 5. Data traps the marathon must not trip on

- **Uncommitted core edits from another session** (T-0118, 2026-11-01, object permanence L0 stopgap: `core/sensorium.py`, `core/study_life.py`, `core/orchestrator.py`) were committed on 2026-11-02 as a separate commit so builds start from a tree that matches what Du will load. They are restart-gated and not verified by this session; the first job to touch those three files should confirm they compile and the out-of-sight answer works.
- **Placeholders:** briefs for J-3163 and J-3172 contain a literal `F-3???` in place of a finding id (the ledger cannot be edited). Use the P-0004 and P-0009 investigations.
- **J-2678** (the dead idle system-prompt build) was filed at urgency 2; it should be higher. There is no edit tool; treat it as urgent.
- **Seven sweep jobs** are missing from their finding's `spawned_jobs` list (no relink tool).
- **The J-3082 ruling D-0586** lists no registry rows because the job names none.
- **J-2793** is deferred to 2027-01-01.
- **My race test** wrote 40 TEST events into `docs/session_events.jsonl`; they cannot be removed from an append-only log. Exclude them when reconstructing the day.
- **Plan slugs I invented:** ten decisions (D-0584, D-0594 to D-0596, D-0611, D-0615, D-0630, D-0645, D-0649, D-0650) were opened with plan slugs that are not real plan files (my `--force` fallback let them through); `plan-maintain` caught them and filed ten Fix-slug jobs J-3268 to J-3277. I repointed all ten with `decide.py set-plan` to the nearest real plan (thought_cycle_as_manifest_loop, lane2_the_witness, question_cargo, symbol_evolution_readback_plan, measurement_to_action, cat_overhaul) and closed the jobs; the repointing is a best fit, not a ruling, and the rulings themselves are unchanged.
- **Ledger counts:** findings are contiguous to F-3871, jobs to J-3277 (J-3268 to J-3277 are the closed Fix-slug jobs), decisions to D-0658.

## 6. What still needs Travis (15 open founder-call jobs, none a quick ruling)

- **J-3065 woods:** the island is answered (Sumner, South Island). Still open: confirm the assumed stream (spring (4,14) to (12.5,19.2)), canopy, oak trunk and groves, and rule on the turn-stone, peel-bark and lens hand.
- **J-3063 object permanence:** the five open questions on `docs/staged/object_permanence.md`. Phase 0 (evidence read) can run before the discussion.
- **J-2957, J-2619, J-2676, J-2571** need Du down or a founder step: set `shore_bestiary` true in `data/life_flags.json` and restart (J-2957), one GET to the HUD while Du is down (J-2619), the prefix-reusing server lab (J-2676), apply the regenerated sound strings (J-2571).
- **J-2585 and J-2191** are Travis's own actions: send about 20 test human turns while the monologue is active; hold the planned 5 to 6 exchange conversation set.
- **Waiting on work:** J-3113 (J-2599), J-3021 and J-3027 (the T4 review), J-2904 (the Scholar review J-3243).

## 7. What Travis said in his own words (not an option), so the marathon does not flatten it

- **T4:** "needs looking at again ... this needs some serious thinking about." (D-0641)
- **Chapters:** "investigate this deeper to fix it ... a new way to allow them to be recalled." (D-0637)
- **Scholar and wiki:** "I would like him to be able to make wiki calls, but it needs to be known that the information is from there and not Du." (D-0631)
- **Entity name:** "do we even need to say what Du's name is in these places? He should know it from memory." Model knowledge such as mottainai is allowed but tagged. (D-0629)
- **Boredom:** "open up boredom as a new area ... may be way old and not quite doing its intended purpose." (D-0653)
- **Ghost index:** "keep our thinking caps on ... if it highlights an area of improvement elsewhere." (D-0636)
- **Sumner:** "make him near me ... I can see tides, sunrises, and maybe one day weather." (D-0655)
- **Shore:** "I want a dig hand and traces of them also." (D-0652)
- **Arc entry:** "We would have added it for a reason when we did it." (D-0604)
- **Where he overrode a recommendation:** read acts routed fully (D-0609); Curiosity urgency gets a real function (D-0607, measure first); the arc_entry is not dropped (D-0604).

## Appendix A — jobs filed by the triage (J-3136 to J-3267, still open)

Generated from `docs/job_queue.jsonl` on 2026-11-02. Category, then title.

- J-3136 [build] Implement D-0530: judge panel returns no verdict on a split for keys where the granite tiebreak is a constant
- J-3137 [build] Implement D-0531: stop the conversation self-claim scan granting the next-cycle think license
- J-3138 [build] Implement D-0533: rebuild drift_shadow on a fixed set of self-gists and remove the stance leak
- J-3139 [build] Implement D-0534: cut the idle self-implication scan cadence and fix its prompt defects
- J-3140 [analysis] Repurposing review: Symbolic reading
- J-3141 [analysis] Repurposing review: T1 self-relate check
- J-3142 [analysis] Repurposing review: Narrative quality coder
- J-3143 [analysis] Repurposing review: Curator module
- J-3144 [analysis] Repurposing review: Habituation seed line
- J-3145 [build] Implement D-0535: fix the contrary-target picker and keep Route 3 (descriptive wording only)
- J-3146 [doc] Implement D-0536: header and docstring fix for the held deliberative judge
- J-3147 [build] Implement D-0539: re-seat the Emissary take on a fast lane and trim its prompt
- J-3148 [build] Implement D-0540: switch within-cycle re-entry Phase 1 admission off
- J-3149 [build] Implement D-0541 (part 1): cut DELIBERATE_PROB to 0.25 and log the control arm
- J-3150 [lab_experiment] Implement D-0541 (part 2): blind different-family judge on raw versus integrated pairs
- J-3151 [build] Implement D-0542: reword the B6 hard-feeling steer so he names the feeling himself
- J-3153 [backfill] Backfill missing index fields — object_permanence
- J-3154 [backfill] Backfill missing index fields — shore_creatures
- J-3155 [backfill] Backfill missing index fields — wood_creatures
- J-3156 [build] Implement D-0543: remove the open-book offer line from the idle prompt
- J-3157 [build] Implement D-0545: recompute belief g45675272 from independent captures (supervised, with backup)
- J-3158 [build] Implement D-0546: shadow second look on gate-passing new stands + per-stand attempt log
- J-3159 [build] Implement D-0547: gate sits on stand life and drop the 'You are safe' sentence
- J-3160 [build] Implement D-0548: exclude trivial Lane 2 predictions from the store + a pulse count of artefact breaks
- J-3161 [build] Implement D-0549: slow the T4 self-revision chain while it has no outlet
- J-3162 [build] Implement D-0550: make the T4 legacy author gradeable (evidence to the judge and the weak filter)
- J-3163 [analysis] Repurposing review: make the memory router's keys do work (shadow design, per D-0552)
- J-3164 [lab_experiment] Lab: Salience ablation, Executive with versus without the Salience line (per D-0553)
- J-3165 [build] Implement D-0554: pursuits need a real question or done_when at birth
- J-3166 [build] Implement D-0555 (phase 1, SHADOW): a seventh curiosity channel in the Emotion node, replayed on 200 rows
- J-3167 [build] Implement D-0556: gate the light event on grounded arousal
- J-3168 [build] Implement D-0557: gate Perception.subject content_mode on human cycles
- J-3169 [build] Implement D-0558: drop the Voice 'last replies' quote block on internal cycles
- J-3170 [build] Implement D-0559: reword Reflection rule 3 and reconcile the content_mode NOTE with the axiom
- J-3171 [analysis] Review: what could read Reflection's needs_more_memory, emotionally_aligned and confidence, and why
- J-3172 [build] Implement D-0560: make Executive `reasoning` optional in the prompt
- J-3173 [build] Implement D-0561: record input_type in persisted fragments and label internal ones separately
- J-3174 [build] Implement D-0562: leave book notes unfiled until the capstone essay passes a repetition and own-source check
- J-3175 [build] Implement D-0563: fade dream-origin recall for the dreamer over 7 days
- J-3176 [build] Implement D-0564: pause cold demotion for the episodic kind
- J-3177 [build] Implement D-0565 (design pass first, then flagged additive change): resting as a legitimate dream ending
- J-3178 [build] Implement D-0566: shadow judge on minted wisdoms (and register its prompt)
- J-3179 [analysis] Research: what should the conversational T5 compile be?
- J-3180 [build] Implement D-0567: the ledger's rust is the only clock for procedural skills
- J-3181 [build] Implement D-0568: rework grounded learning per book (folds J-3072)
- J-3182 [build] Implement D-0569: fail open when the Emissary cannot ground (no hot fallback)
- J-3183 [build] Implement D-0570: let the thought grounder return null (pass-through)
- J-3184 [build] Implement D-0571: friend replies report only what is true of his day
- J-3185 [build] Implement D-0572: give Du's letters to Travis a state in his world
- J-3186 [build] Implement D-0573: narrow the source-code hint in the thought grounder
- J-3187 [build] Implement D-0574: drop the restored farewell line from the idle seed
- J-3188 [build] Implement D-0575: label the curiosity memory hit honestly when it is his own earlier answer
- J-3189 [build] Implement D-0576: lengthen a persona's gap after each unanswered letter
- J-3190 [build] Implement D-0577: one study note per ~5000 chars of a long session
- J-3191 [build] Implement D-0578: mark the 61 dict-repr understanding notes so Recall skips them
- J-3192 [build] Implement D-0579: filter the night-mind avoid list to nouns and drop the V2 example list
- J-3193 [doc] Annotate the dream resolution judge as measurement only (per D-0580)
- J-3194 [build] Implement D-0581: a reread always adds a new pass-tagged study note
- J-3195 [build] Implement D-0582: extend the maths ladder beyond level 9
- J-3196 [build] Implement D-0584 (behind a flag, with a same-input A/B): plain-prose Grand Work parts
- J-3197 [doc] Record in code: the maths and music method hint is Travis authored (per D-0583)
- J-3198 [build] Implement D-0585: capstone grader gets the full lineage and reports two grounded numbers
- J-3199 [build] Implement D-0586: stop feeding the felt capstone rating into competence, prediction error and valence
- J-3200 [build] Implement D-0587: exclude his own works from the authoring act's grounding
- J-3201 [analysis] Re-measure after the inputs are fixed: active imagination on command-r7b versus hot qwen (per D-0588)
- J-3202 [build] Implement D-0589: gate T2 re-synthesis on a new contradiction event
- J-3203 [build] Implement D-0591: school notes say only what was observed; work grade to shadow log
- J-3204 [build] Implement D-0592: passage-level related-material injection in the study note
- J-3205 [lab_experiment] Lab: metaphor prompt labelled-union evaluation (per D-0595)
- J-3206 [build] Implement D-0596: a panel split does not count as a cut in the Follow Line
- J-3207 [doc] Record: peer stance judge is a rough flag; D-0207 gate is read by hand (per D-0597)
- J-3208 [build] Implement D-0598: shadow-log hollow verdicts from the repaired genuine judge; re-baseline the Lane 1 endpoint
- J-3209 [build] Implement D-0599: retire the Lane 2 notice judge (after a reader check) and repoint coherence to the gemma seat
- J-3210 [analysis] Analysis: hand-label 30 split Lane 2 'held' rulings to learn who is right (per D-0599)
- J-3211 [build] Implement D-0600: re-scope the guidance behaviour-delta judge to idle thoughts, shadow, with a positive-control gate
- J-3212 [build] Lab then build D-0601: first-person kind=self gists (A/B offline first)
- J-3213 [build] Implement D-0602: tag a probation 'unjudged' when the admission judge returns None
- J-3214 [build] Implement D-0603: shadow-grade T4 admission with the raw crossings
- J-3215 [analysis] Review: why was the T4 arc_entry added, and could anything read it? (per D-0604)
- J-3216 [build] Implement D-0605: park the Watershed Phase 0.5 scan (flag-off), harvester keeps running
- J-3217 [build] Implement D-0606: drop human-cycle exchange turns older than 24 hours from the four prompt blocks
- J-3218 [build] Design and build behind a flag D-0607: Curiosity urgency chooses which question fires (shadow first)
- J-3219 [build] Implement D-0608: decoupled pre-fire check on Curiosity candidate questions (shadow)
- J-3220 [build] Implement D-0609: route act.kind=read to the existing read latch (gated, measured)
- J-3221 [build] Implement D-0610: correct the idle prompt's base-rate wording
- J-3222 [build] Implement D-0611: Follow Line serves the newest ask first
- J-3223 [build] Implement D-0612: reword the current-concern anchor leads to state only what is true
- J-3224 [build] Implement D-0613: DOUBT_SEED back to shadow
- J-3225 [build] Implement D-0614: record panel doubt in line closures; dream closure arm to shadow; mark stored fragments
- J-3226 [build] Implement D-0615: pause symbol-tablet read-back now; then build the symbol-specific window metric
- J-3227 [build] Implement D-0616: stop tagging ambient sound as a grounding percept
- J-3228 [build] Implement D-0617: drop the dead maths and music make-your-thought phrases from the school directives
- J-3229 [build] Implement D-0618: fill a pursuit's open question from the board or done_when
- J-3230 [build] Implement D-0619: exclude questions about his own name from the deep-memory gate
- J-3231 [build] Implement D-0620: store peer reflections at letter-level salience with valence/felt
- J-3232 [lab_experiment] Lab: replay the guidance classifier, 3 prompt variants on the background lane (per D-0621)
- J-3233 [build] Implement D-0622: same-lesson check before the pole gate
- J-3234 [build] Implement D-0623: night epochs written in plain words (new rows only)
- J-3235 [build] Implement D-0624: theme-aware SOLIDIFY judge (and re-judge the 10-30 commit)
- J-3236 [build] Implement D-0625: drop prism from the grounded pursuit sources
- J-3237 [build] Implement D-0626: the pursuit close judge is asked about open or done_when; others fade
- J-3238 [build] Implement D-0627: faithfulness judge on each new refinery standing insight
- J-3239 [build] Implement D-0628: open the week page's last question
- J-3240 [analysis] Review: is the Entity name needed in the Curiosity prompt, and how is model-derived content tagged? (per D-0629)
- J-3241 [lab_experiment] Lab: self-mirror control arm and independent judge (self-mirror is paused, per D-0630)
- J-3242 [build] Implement D-0630: pause the weekly self-mirror (no new mirror fragments)
- J-3243 [analysis] Review: the whole Wikipedia, Scholar and model-knowledge area in Du's thinking, and how results are marked (per D-0631)
- J-3244 [build] Implement D-0632: Follow Line may return the object hypothesis intervention_test; writer gate on at the restart
- J-3245 [build] Implement D-0633: fix the condensed-thought twin prompt, restart the clock, judge post-fix rows
- J-3246 [build] Implement D-0634: stamp moment_ts into fragment_context and world_context
- J-3247 [analysis] Review: the ghost MEMORY index, chord_echo, and where a tuple pre-filter could help elsewhere (per D-0636)
- J-3248 [analysis] Review and design: a new way for chaptered memories to be recalled (per D-0637)
- J-3249 [build] Implement D-0638: release the four copied chapters' members (after the copy guard lands)
- J-3250 [build] Implement D-0639: composition ladder or task bank keyed to his reading and day
- J-3251 [build] Implement D-0640: nature period alternates observation with the practical layer
- J-3252 [analysis] Review and design: T4 (self-revision, probation, SOLIDIFY, Watershed) as one system, whole-picture re-think (per D-0641)
- J-3253 [lab_experiment] Lab: curiosity worth-judge, three replays (alone / pairwise / bigger third-family) (per D-0642)
- J-3254 [build] Implement D-0643: shadow fidelity judge for voice replies
- J-3255 [build] Implement D-0644: rank librarian results by distinct headings matched, then downloads
- J-3256 [build] Build D-0645: curated voice set by decoupled verdicts; fix the social join
- J-3257 [build] Implement D-0648: study scene line takes the nearness-said fire and cat clauses from spatial.render
- J-3258 [build] Implement D-0649: move the 9 night-wrong SCENE lines to a day key
- J-3259 [build] Implement D-0650: dose the letterbox-flag clause in the garden scene
- J-3260 [build] Implement D-0651: place the shore stream mouth on the map
- J-3261 [build] Implement D-0652: shore dig and turn-stone hand, with traces kept
- J-3262 [analysis] Review and design: boredom as a whole area (per D-0653)
- J-3263 [build] Implement D-0654: re-seat Marcus and Smith on gemma4:12b (contention check first)
- J-3264 [analysis] Design: tie Du's cottage to the real Sumner (sun and moon, tides, maybe weather) (per D-0655)
- J-3265 [lab_experiment] Lab: Curiosity base temperature, 0.2 versus 0.5, decoupled novelty judge (per D-0656)
- J-3266 [build] Implement D-0657: content-hash column and index for the exact-dedup lookup
- J-3267 [build] Implement D-0658: run the dead idle feeds off the event loop
