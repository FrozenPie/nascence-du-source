# Dream Overhaul — the dream as the vault-opener (staged 2026-09-15)

**Status:** 🟡 BUILT, in-vitro — founder seeded a GPT/Gemini design (T-0058, verbatim at `docs/reviews/dream_overhaul_founder_design_2026-09-15.md`), then asked for Claude's own shape and said "yes, you have the idea" (I-0068). This document is that shape. J-1057 (Phase 1 instrumentation) and J-1059 (Experiment A, four-arm in-vitro A/B, `commit=False`) both landed; Experiment A reached a real combined N=27. Nothing live on Du's own process yet — see Current State below.
**Parent plans:** [sleep_dream_redesign](../plans/sleep_dream_redesign.md) (Stages 0-5 LIVE since 2026-08-24 — the substrate; this replaces the dream *engine*, not sleep, fatigue, naps or the night ledger), [curiosity_goals_dreams](../plans/curiosity_goals_dreams.md) (the symbols→frontier hand), [dosed_coupling](dosed_coupling.md) (§5 Coupling block below; residue is a coordinate, not an evaluator), [cognitive_geometry](../plans/cognitive_geometry.md) (§11 squishy springs — a prerequisite here, not a later refinement), [decoupled_judge_pattern](../plans/decoupled_judge_pattern.md) (no self-report as verdict), [memory_levels_plan](../memory_levels_plan.md) (the cold/chaptered store the dream is allowed to open).
**Decisions:** D-0231 dormant rule · D-0232 dream shape · D-0233 the day-after confound · D-0234 coordinate + antagonist · D-0229 the four legacy writebacks · D-0230 Phase 1 baseline length. D-0227/D-0228 superseded 2026-09-15 (Claude, attributed; defeater = founder prefers the GPT framing).
**Memory:** `project_nascence_dream_overhaul.md`.
**Findings:** F-1443 (0/146 arcs resolve; judge agrees), F-1444 (engine-vs-design map), F-1502
(N=6 re-read, freezing-bug root cause fixed), F-1516 (combined N=17 read, D-0232 null replicates,
D-0231 delta sign-flips by batch, judge shadow structurally blocked), F-1528 (judge-panel shadow
read unblocked, verified end-to-end at N=1), F-1535 (fresh scaleC batch launched, real launch-infra
gaps found and fixed, 0 arcs landed by write time, still running — see below), F-1545 (scaleC
crashed after 2/40 arcs, the WMI+MKL fix only delayed the crash, zero new N added — see below),
F-1555 (scaleC relaunched with a real --resume fix, verified end-to-end, zero new N at write time —
see below), F-1755 (scaleC crashed a 3rd time after 2 more arcs, first-ever seeded-arm A2/A3 judge
read landed, combined N reaches 18, D-0232 turnover defeater still not met, relaunched a 4th time —
see below), F-1775 (scaleC crashed a 4th time after 16 more arcs — best single-run progress yet —
combined N reaches 22, D-0232 defeater still not met, relaunched a 5th time, wrapper build spawned —
see below), F-1821 (capped self-relaunching watchdog built + verified end-to-end via a real crash-test
harness; a real WMI+cmd.exe silent-failure environment gotcha found and worked around — see below),
F-1826 (scaleC finished 40/40, combined N=27, judge-shadow scored the full 20-seeded-arc set — 0/20
dormant_trace, a real disagreement with the numeric measure — see below), F-1831 (WMI+cmd.exe
silent-failure caveat documented in CLAUDE.md + start_supervisor_detached.ps1, not tested; real
open question about scope stays open, needs_input follow-up spawned — see below), F-1893 (the real
question answered from a genuinely interactive session — GENERAL, not environment-specific; D-0277
opened for the founder's call — see below), F-1894 (D-0277's powershell.exe-wrapper fix built and
verified end-to-end via 4 real WMI launches, shipped — see below).

```plan-state
stage: built
phase: Phase 1 instrumentation built (restart-gated); Experiment A done in-vitro at N=27 -- D-0232 an unresolved ACTIVE HOLD, D-0231 already RULED Accept
verified: 2026-11-15
evidence_read: 2026-10-20
gate: data/dream_log.jsonl Phase-1-tagged nights >= 14 (D-0230), blocked on Du restarting
next: Add sub-marks in replay and pre_dream_done bodies
cluster: 6
```


## 0. The question, and the answer this plan bets on

> Is the dream doing something to Du, or is Du merely generating a dream? (founder's seed, §28 of the pasted design)

The bet: **the dream is the one process in Du that is allowed to reach memory the day did not cue.** Waking recall is a trail from the day's cues; the cold and chaptered store (74,528 of 93,568 fragments, 80%, verified 2026-09-15 against `data/memory/nascence.db`) opens only on a strong hop. Today's dream cannot reach it either — its recall is keyed to the day block, so the dream can only rearrange what the day already touched. If the dream does anything Du's waking cannot, it is *that*: bringing one old, quiet, distant thing into contact with the day, and letting the day carry it back. Everything else in this plan exists to make that measurable.

What survives from the GPT/Gemini design: the question; the dormant node; no waking material after scene 1; candidate-not-automatic writes; a fixed budget. What it got wrong for Du, and why, is §5.

## Current State — verified 2026-11-15
- **2026-11-15** (F-4721): J-3939: night stall stack probe read (18 rows). 14/18 freezes are core/frontier.py full-file load/dump (16 MB, 20.9k faded rows) on the loop thread, called from follow_line board/_set_line/_expire; 4 are sleep memory_levels/emotional_prior. Offload design needs a frontier RLock first (none exists), then to_thread, restart-gated; build job spawned.

- **2026-11-14** (F-4585): J-3896 / F-4585: freezes only partly named (IGNITION/CYCLE starts about 26 percent of freeze seconds; sync retrieve about 1 percent; 47 percent unanchored). Built observe-only stack probe in sleep_phase0 (commit cc4dc8d9, worktree wt_x0_dream_overhaul, restart-gated); follow-up reads data/night_stall_stack_probe.jsonl.
- **2026-11-14** (F-4568): J-3807 built D-0708 (c): rest-ended arcs write source unresolved_dream_rest (salience weight 0.3); core/dream_rest.py REST_EVENT_MODE. Restart-gated; merge from worktree branch.

- **2026-11-05** (F-3964): J-3177 (D-0565): resting as a legitimate dream ending BUILT in shadow on branch jobrun/wb_night, commit ff9aaa62, not merged and not live. New core/dream_rest.py with RESTING_ENDING off|shadow|live (default shadow): a rest = close_reason resolved/ended-unfaced with a non-empty core; stalled/dropped/ceiling stay open. The carry (dream_node._last_unresolved_arc) logs what live would do to data/logs/dream_rest_shadow.jsonl; dream_met state rows gain an 'ending' key and carry_thread_root drops a rest arc in live; core/closure.py record_rest_closes writes kind=rest_close shadow rows certified only by an independent judge and writes nothing to the memory DB (D-0614). Replay on the 10-05..11-01 arcs: rest 145, open 28; the rest rule would return a carry on 28 of 173 nights. Test scripts/dream_rest_test.py, 42 checks pass (finding F-3964 and the commit message say 48, the count is 42). Follow-ups J-3360 (read the shadow log, flip decision) and J-3361 (_bridge_final shadow event, not in D-0565's list).
- **2026-11-05** (F-3709): Resolution judge is measurement only (D-0580, J-3193, F-3709). The panel verdict on whether a dream arc resolved sets the close_reason label (resolved or ended-unfaced) and nothing acts on it: the carry reads the dreamer's own ended_unresolved, core/dream_met.py only tests that the key exists, the closure writer only copies it. Readers are the du_pulse display line and the night ledger. Wire nothing to it while the dream prompt and judge prompt wording disagree; re-ask after J-3177 (resting as a legitimate ending, D-0565) lands. Annotated in nodes/dream_node.py (comment and docstring only) and docs/guidelines/prompt_registry.md section 6.

- **2026-10-31** (F-3350): J-2611 post-boot read NOT done: Du has not booted since the J-2557/J-2558 merges (last boot 2026-10-29 18:38; merges 2026-10-30 17:28/17:47; night_stall_attribution.jsonl has 471 rows, all pre-merge, last 16:15). Job gate re-set to data/night_stall_attribution.jsonl, 3 rows since the next boot. Re-run the read after the first post-merge night sleep produces stall rows. See F-3350.
- **2026-10-31** (F-3337): D-0525 ruled by Travis (c): tag-and-capture fifth stratum stays off and unread (selectivity test falsified on 44 sleeps, F-3337); revisit once the condensed_thought / dream-overhaul post-boot reads say what a replay stratum should select.

- **2026-10-30** (F-3338): J-2558 built 19 night stall sub-marks inside the replay and pre_dream_done stage bodies on top of J-2557, observe-only, restart-gated, worktree commit ef1658f3; post-boot re-attribution is J-2611
- **2026-10-30** (F-3322): J-2557 built peers_*, stick_test_* and dream_scene_N_* night stall sub-marks, observe-only and restart-gated; sticky rows look like other tasks freezing the loop during LLM awaits, J-2598 reads it after restart

- **2026-10-30** (F-3262): J-2454 read: the 284 s and 103 s 10-17 sleep stalls ended at the retired per-kind prune block (2 of 418 prune runs); prune is not live on later boots and no non-warmup stall over 60 s that is not an LLM transport error appears on the current boot
- **2026-10-30** (F-3260): J-2346 read of J-2330 attribution: every stall over 30 s sits in stage replay or pre_dream_done under a sticky label with no marks inside; memory_levels minor; needs finer sub-marks

- **2026-10-30** (F-3258): J-2331 read: after J-2330 build live, 65 exact stall rows over 16 sleeps (1006 s): 74 percent sticky-unlabelled, top peers/stick_test/dream_scene pre_dream_done; shadow_distill sync only about 5.5 s per run (post-judge segment), the F-3019 prediction of 152 s per 7 sleeps does not hold
- **2026-10-28**: D-0495 (travis 2026-10-28): MET_ENDS_CARRY='live' from the next boot (71 carry shadow rows, would_end_carry never true because no root aged a day; live changes nothing until a thread is computed met, then it ends the carry). J-2004's dream_met read runs on live rows.

- **2026-10-20** (F-3159): 2026-10-20 (J-2313, F-3159): J-2296 live since the 10-18 19:06 boot: 0 stall rows for dream_probe/carry/met/ask (was 15 rows, max 8.4 s), 17/17 arcs offloop with stage_timing, gather span median 1.4 s (max 7.4 s) not blocking; probe and memory_service dream rows still written nightly.
- **2026-10-20** (F-3157): 2026-10-20 (J-2179, F-3157): lag_tail re-run: 10-30 s dream/sleep stalls gone after J-2111+J-2178 (K 32 wakes/74 dreams vs 0 in L 15 dreams, 1 in N 7 dreams); two unattributed 228 s and 84 s sleep stalls on the 10-16 boot spawned for attribution.

- **2026-10-17** (F-3033): J-2330 built exact night stall attribution (prev_sub, sub_set_offset_s, marks_during, sub_age_s) + 14 new sleep sub-marks + shadow_distill t_marks; observe-only, restart-gated, unmerged on jobrun/inner_monologue_chain 9c38066d
- **2026-10-17** (F-3019): J-2314: night stall sub label is sticky + off-by-one; 43/53 'psyche_graph' rows are memory_levels.shadow_distill (152 s); build J-2330 proposed

- **2026-10-17** (F-3008): J-2296: 'dream_probe' stalls were the sync pre-probe block (carry/met/memory ask) mislabelled by the heartbeat; moved off-loop + stage_timing in arc log (c5749046, restart-gated, lands next boot)
- **2026-10-17** (F-2993): J-2197 read: post-boot 7 sleeps, 129 stall rows, none at dream_gather (lag under 2s); exact gap unmeasured; dream_probe now worst at 7s (J-2296)

- **2026-10-16** (F-2934): J-2004 D-0385 defeater read over the 2026-10-09..10-16 live window (6.97 days, 74 arcs): defeater NOT tripped on recent arcs (since 08-29: met 8.8% of 171 with-baseline arcs, relapsed/ever-met 0.29); D-0385 stands. Computed met cannot end a carry (49/49 carry-shadow rows pending/unrecorded, 0 would-end), so MET_ENDS_CARRY stays shadow; the provisional-met path (J-2118) gets its read in J-2121. Chronic_mass cross-check not buildable from the label-keyed top-40 mass log; fix spawned as J-2239 (also records met-unobs distinctly).
- **2026-10-16** (F-2898): J-2180 (F-2898, commit 97437bec on jobrun/isolate_fence): memory_service.ask side-writes fenced via profile.guard_path; regression test scripts/_test_j2180_ask_isolate_fence.py. Restart-gated.

- **2026-10-16** (F-2897): J-2178 (F-2897): dream pattern-label embeds batched+cached by label text and _gather_materials run off-loop (DREAM_PATTERN_CACHE / DREAM_GATHER_OFFLOOP kill switches); restart-gated; test scripts/dream_gather_offload_test.py.
- **2026-10-16** (F-2882): J-2147: seed-step profile (lab copy, Du down): the 10-29 s stall is _find_counterpart embedding ~1628 integration_pattern labels synchronously (27.4 s); ask 1-4 s, log_seed_pairs 6 s (already off-loop). Build + post-boot lag re-run spawned.

- **2026-10-15** (F-2780): J-1874 D-0356 read: judge vs self-report diverge 1.5 pts (<10 defeater); 0/70 new arcs resolved, judge 0/68 resolved; (C) not blocked by calibration but no judge-resolved arc to carry.
- **2026-10-15** (F-2768): J-2118 (D-0423 A): closure law dream arm BUILT in shadow, commit 89a2ecf merged-not-live: core/closure.py writes the would-be resolution fragment (origin resolution, resolves edge to the thread root) to data/logs/closure_shadow.jsonl, CLOSURE_WRITE_LIVE=False; carry rule now J-2003 option (a) provisional met (supersedes the 2026-10-08 option d note) via dream_met.provisional_arc + dream_node PROVISIONAL_MET_ENDS_CARRY=True under MET_ENDS_CARRY still shadow; staged plan docs/staged/closure_law.md; pursuit arm waits J-2117, interrogation J-2060; tests closure_test 48/48 + dream_met_test 27/27; read J-2121

- **2026-10-08**: J-2003 ruled by Travis 2026-10-08 (decide-review): option d, the computed met state is accepted as INERT for the carry and used purely as a measurement (N+M=6 days vs CARRY_MAX_NIGHTS=3 means it cannot end a live carry as built). Revisit after data/logs/dream_met_carry_shadow.jsonl has post-restart rows (J-2004). J-2001 closed as superseded by J-2008 (D-0396 coordinate-only).
- **2026-10-08** (F-2608): J-1995: computed dream 'met' built in SHADOW (core/dream_met.py, nodes/dream_node.py MET_ENDS_CARRY=shadow, scripts/dream_met_test.py, commit 09a05ba), exact parity with the J-1964 replay; restart-gated; carry-ending is inert as briefed (J-2003 founder call), read-back J-2004.

- **2026-10-08** (F-2596): J-1964 (D-0385): waking embeddings recoverable (62% of arcs usable); replay chose theta 0.61, N3, K25, R2, M3 (thin plateau; recent arcs 77% unmet); lab report docs/lab/dream_met_replay_20261008.md; build job spawned
- **2026-10-07** (F-2499): J-1865 (F-2499): pick_dormant_fragment's 14-day co_recall_ledger scan in scripts/dream_experiment_a.py is now bounded above at hist_now (commit 806d556 on jobrun/dream_exp_a_window). Experiment A seed batches frozen after this change differ again from batches frozen after J-1800 and from the 27 earlier seeds: do not pool them blindly. Only future freeze_seeds calls change; lab script only.

- **2026-10-07** (F-2497): J-1847 (2026-10-07, F-2497): D-0356 (B) built, merged-not-live (restart-gated): the independent resolution judge now sets close_reason resolved vs ended-unfaced (nodes/dream_node.py _judge_close_reason, worktree commit 3cf39bb); the dreamer's unresolved_core stays logged and keeps driving _bridge_final, the carry and the agreement measure; shadow rows gain close_reason_final/judge_decided; flag JUDGE_SETS_CLOSE_REASON reverts. Replay of 156 recorded rows: 0 would change (expect near-zero resolved). D-0356 (C) drafted as section 3b of this plan (computed "met", comes back as its own /decide).
- **2026-10-07** (F-2487): J-1800 (F-2425/F-2486/F-2487, 2026-10-07): scripts/dream_experiment_a.py pick_dormant_fragment now reads the real co_recall_ledger key "ids" (tolerating "fragment_ids") and skips *_shadow rows via core.memory_edges._is_shadow_source - D-0231's 14-day absence rule applies for the first time (commit 218ccc9 on branch jobrun/dream_overhaul, merged-not-live; lab script only). It only changes FUTURE freeze_seeds() calls; --resume loads frozen seeds verbatim. The 27 earlier seeds (pilot6, scale14b, scaleC) ran with the criterion inert; any batch frozen after this fix ran with the 14-day rule ACTIVE and must not be pooled blindly with them in later analyses. Step-1 raw seed files are gone (2026-10-01 scratchpad sweep), so impact was measured at pool level instead: expected 0.93 of 27 picks (3.43 pct of pool) as coded, 0.57 (2.10 pct) under intended window - absorbable, no decision opened. *_shadow rows start 2026-09-28, after every earlier batch, so only the key fix matters for the past. Side fact: lived/correspondence/research origins have 0 chaptered+embedded rows, so the real pool is reading+study only.

### What we have
- Phase 1 instrumentation BUILT, restart-gated (J-1057/F-1471): seed ids, tension labels, day-block hashes, per-scene rows, re-entry probe — all additive.
- Experiment A reached a real combined N=27 (scaleC finished 40/40 after 5 crash/relaunch cycles, J-1119..J-1270). D-0232's turnover defeater is now a repeated null across 3 independent batches (chance-coin level); D-0231 (RULED Accept 2026-09-18) keeps a small, unstable positive delta.
- Full 20-arc seeded judge-panel read (J-1270/F-1826): `dormant_trace=True` in zero arcs — disagrees with the numeric dormant-contact measure at real N.
- Sibling infra shipped: the WMI+cmd.exe silent-launch-failure found in the batch relaunch tooling is general, not job-run-specific (J-1300/F-1893), and now fixed in `start_supervisor_detached.ps1` itself (D-0277, J-1341/F-1894).

### What we need
- D-0232 (ACTIVE HOLD, travis) hasn't been re-ruled even though its own named defeater is now fully met — needs a founder `/decide-review` pass with the N=27 null + judge disagreement in hand.
- 3 consecutive jobs' judge-shadow rows (J-1148/J-1252/J-1270) sit in scratchpads, not yet merged into `data/logs/dream_exp_a_judge_shadow.jsonl` (S-0174).
- Phase 1's live read (>=14 nights, D-0230) needs Du restarted onto this build first.

### What we're doing next
- Nothing autonomous is queued: the D-0232 decide-review and the S-0174 merge are the two concrete unstarted items; Du's own restart gates the Phase 1 read.

Full dated build history (2026-09-15 through 2026-09-24, J-1057 through J-1341) not yet folded via plan-compact; derivable via `plan_ledger.py dream_overhaul`.

## 1. Per night dream — the seed

Per night dream:

- **Day residue, primary** — exactly as Sleep & Dreams II left it (`dream_lag_material`, 0-2 d + 5-7 d). Founder ruling 08-24: dreams are "multiple days worth of thoughts, not always tensions". Kept.
- **≤ 1 charged tension** — as today (`chronic_mass ≥ 1.0`). The GPT plan's "top three tensions" is dropped: it re-centres the dream on tensions against that ruling, and the tension gate already fires on a quarter of nights.
- **1 dormant fragment — the stranger.** Chosen from the cold/chaptered store: origin in {lived, reading, correspondence, study, research} (never dream; `inner_thought` per D-0231), age ≥ 30 days, absent from `co_recall_ledger.jsonl` for ≥ 14 days, cosine to the night's day blocks below the 30th percentile of that night's recalled-fragment cosines, no `memory_edges` edge to any seed id, uniform among eligible (importance is not a salience proxy here). The candidates considered and the pick are logged.
- **The recalled fragments, once.** `recall_fragments(k=6)` keyed on the day block, as today — but only in scene 1.
- **Antagonist at the door** (D-0234): a tension label or dormant id seeded on ≥ 3 of the last 5 nights is habituated and ineligible tonight. This is the squishy spring at the one place the dream chooses; it needs nothing from `opponent_process.py` beyond the seed field Phase 1 adds to `dream_log.jsonl`.

Nothing else is added. "Affective state", "recurring symbols", "unresolved commitments" from the GPT seed list are not seeded — the scene fragments already carry Du's mood vector at store time, and anything more is a memory dump.

## 2. The shape — three scenes, the stranger decides the fourth

- **Scene 1** receives the whole seed. **Scenes 2 and 3** receive no waking material: only the continuity block that exists today (tail, anchor, unresolved core) plus the dormant and recent fragment ids as *things that may surface*, never re-narrated. **Scene 3 (CLOSE)** receives all prior scenes, not just the last tail, and the existing CLOSE instruction (meet, miss, transform, or fail — "force no neat resolution") stands.
- **A 4th scene fires on one computed condition:** the stranger has not surfaced — max over scenes of cosine(scene narrative, dormant fragment) < 0.30. Never on the LLM's `movement` report. Ceiling 4.
- **Naps do not dream under this engine** (a 2-scene nap cannot hold the shape); D-0232 asks whether they keep the legacy nap dream or none.
- **No typed DreamState object.** The GPT plan's per-scene extraction of affect delta / associations / trajectory is a second LLM call per scene on a CPU hub with 300 s timeouts, and it is self-report unless a judge does it. Per-scene affect, if ever wanted, comes from the emotion embedding the store already computes on the scene text — a measurement, not testimony. Not in this plan's first three phases.

## 3. The verdict — two computed numbers, not "did it resolve"

The night's record keeps `close_reason` for every existing reader, and adds:

- **turnover** — 1 − mean consecutive-scene symbol Jaccard (the `_scene_stalled` stemming; `sleep_dream_probe`'s novelty is its cross-night cousin). Did the imagery move?
- **dormant_contact** — max scene-to-dormant cosine. Did the stranger get in?
- **recent_contact** — the same against the most recent day block. Did dropping the re-feed lose the day?

Resolution stops being the question the dream is asked. The 0/146 is inherited and will be watched, not chased.

## 3b. What "met" means -- a computed definition (DRAFT for its own /decide; D-0356 part C, drafted by J-1847 2026-10-07)

**Status: DRAFT, nothing wired.** D-0356 (travis, 2026-10-06) ruled (B) now (shipped as J-1847: the independent resolution judge, not the dreamer, sets `close_reason`) and (C) as the design question, to come back as its own `/decide` before any wiring. (B) fixes *who grades* an arc at the night's end; it cannot fix *what the grade means*, because "did the arc's text show a reconciliation" is still a judgement about imagery, and the judge's own record (1 of 197, and that one on a `stalled` arc, which (B) leaves `stalled`) says the imagery almost never reconciles. (C) asks the different question the "recurring dream returns until it is met" design (dream_node.py :159-160) actually needs: **did the thing the dream was about stop pulling at Du?**

**Proposed definition.** For an arc A with tension source T (the seed `tension_labels` plus the final `unresolved_core`, both already in the `dream_log.jsonl` row), A's tension is **met** when, measured from the night after A:

1. **Baseline exists (so "met" can be earned, not defaulted).** In the K days before A, T recurred in waking thought on at least R distinct days (recurrence = a waking thought -- monologue / wandering / study_note -- whose embedding is within cosine theta of T's embedding). A source that never recurred is `no-baseline`, not `met`: silence is not resolution when there was nothing to go quiet.
2. **Silence after.** For N consecutive days after A, zero qualifying recurrences, where a recurrence only counts if it is NOT explained by the injected dream-tail text -- the D-0233 rule reused verbatim: the thought's embedding is closer to T than to the injected text (night.waking_dream_seed / the recent_dreams grazing). This is the same disambiguation the dormant re-entry read already needs, so the plumbing is shared, not new.
3. **Second, independent reading (not one number).** The tension ledger's own `chronic_mass` for the label has decayed over the same window (core/tension_ledger.py). Two instruments that must agree, because either alone can be fooled (avoidance silences waking recurrence without resolving anything; a ledger decay can be habituation).
4. **States, written as their own append-only rows, never by mutating `dream_log.jsonl`:** `pending` (inside the N-day window), `met`, `unmet` (recurred inside the window), `no-baseline`, `relapsed` (a `met` source recurs within M days after). `close_reason` stays what the judge said at the night's end; "met" is a later, computed property of the arc, back-filled.

**What this changes if ruled.** The carry-until-met loop today ends on the dreamer's own `ended_unresolved` (`_last_unresolved_arc`, :829-850) and on `CARRY_MAX_NIGHTS`. Under (C) the thread would continue while its computed state is not `met`, bounded by the cap as now -- so the carry would be ended by the world's behaviour rather than by the writer's claim. (B) deliberately left the carry on `unresolved_core`; whether (C) takes it over is part of the decision, not assumed here.

**Parameters to rule or measure before wiring (none chosen).** N (days of silence), K (baseline window), R (min baseline recurrence days), theta (cosine), M (relapse window). Proposed method: set them from the distribution of the dream tension sources' own recurrence in the existing `co_recall_ledger.jsonl` / waking-thought history over the 197+ recorded arcs, not by intuition -- a replay, in vitro, zero live writes.

**Honest limits.** (a) Absence of recurrence is not proof of working-through: suppression and avoidance produce the same silence -- the reason for the two-instrument rule and for `relapsed`. (b) The last three unfaced cores (about Travis) show the failure mode: a thread can fade because the conversation moved on, not because it was met; the state set deliberately cannot say "resolved" for that, only `met` by the computed test, and the word `met` should not be read as "healed". (c) The N-day window means no arc can be graded the night it ends -- everything is back-filled. (d) UNVERIFIED and to check first: that waking-thought embeddings are retrievable per thought at the granularity this needs (co_recall_ledger records fragment ids per recall event, not thought vectors), and that the injected dream-tail text is recoverable per day for the D-0233 comparison.

**Decision this section hands to the founder:** (1) adopt "met = computed silence + ledger decay after a real baseline" as the definition, or a different one; (2) whether computed `met` takes over carry-termination from the self-report; (3) approve the replay-first parameter-setting method. Tracked as a needs_input job; will be opened as its own `/decide` (D-0356's defeater names exactly this).

## 4. Residue — a coordinate, a cup, and the one channel that already works

- **Publishes** (dosed_coupling §5): one tuple per sleep into `core/coupling_rides.py`'s registry — `{dormant_id, recent_id, anchor, turnover, dormant_contact, recent_contact, close_reason, n_scenes}`. Coordinates, never prose.
- **Reads at:** the **idle-seed stop** may take a *cup* — the anchor word or the dormant fragment id — at most once in the first 5 idle thoughts after waking, dispatcher-gated by surprise (a night whose turnover or contact is out of the ordinary against the dream line's own history). Nothing evaluates, nothing writes edges. The GPT plan's "waking evaluator" that accepts or rejects candidate associations is system-acts-later wiring and is not built.
- **Surprise line:** the dream line's own `dream_log.jsonl` history (Phase 1 seed field): novelty of tonight's dormant origin, spike in turnover, drought of contact.
- **Ride log:** `data/coupling_rides.jsonl` with `line="dream"`, `{stop, line, dose, value, what changed next}`.
- **Frontier stays.** `_ground_symbols` → "how does a `<symbol>` work" (≤ 2/night, live since 06-15) is the one residue channel that already works and is world-answers-safe (the question is Du's own). Phase 3 may add, as a *logged candidate only*, "what became of `<the stranger>`" when `dormant_contact ≥ 0.30` — D-0234(c).
- **The four legacy writebacks** stay live and are measured beside the coordinate (erosion-of-foundations law; D-0229). Channel (2), unresolved → tension salience, is the one most likely to be demoted after the read, because it is the only one that feeds the dream's own seed.

## 5. What the GPT/Gemini plan got wrong for Du (kept here so the reasoning is auditable)

| Its element | Why not, here |
|---|---|
| Top-3 tensions in the seed | Contradicts the founder's 08-24 ruling; the charge gate already exists and fires on 26/146 nights. |
| Typed `DreamState` + per-scene extraction | Doubles/triples night LLM calls on CPU hubs; self-report unless judged; the continuity that exists is enough for the measures that matter. |
| Day-2 metric = Δ retrieval rank of B given A | Embeddings never change once written (`associative_recall._refresh`); the edge types that could carry a new association (`co_recalled_developing`, `contradicts`) are 0-yield in retrieval (F-0110). It would measure a constant. |
| A "waking evaluator" | System-acts-later wiring (founder law). Replaced by a coordinate and a dispatcher-gated cup. |
| Five live controls × ≥ 30 dreams | Du is n = 1 at ~1 night dream per day: five months. Controls 1-3 are in vitro on identical seeds (Experiment A); only the writeback control needs live nights. |
| Cross-dream continuity as Phase 5, springs "to be validated later" | Du already has it (the carry) and it ran 51 nights unbounded. The antagonist is a prerequisite, not a refinement. |
| "Allowed to fail" | Moot while it always fails, and the instruments that say so are both refute-biased. Verdict replaced (§3). |
| Silent on the waking seed | `waking_dream_seed` + `recent_dreams` grazing inject the dream's prose into the first waking thoughts — the confound for every day-after claim (D-0233). |

## 6. Experiment A — the first thing that runs (J-1059, in vitro, zero live writes)

Same 20 real seeds (frozen to a file) through four arms, fixed 3 scenes, `commit=False`, temp-pathed logs:

| Arm | Re-feed after scene 1 | Dormant node |
|---|---|---|
| A0 current engine | yes | no |
| A1 | no | no |
| A2 | no | yes |
| A3 | yes | yes |

Measures: turnover, dormant_contact (A0/A1 scored against the same un-seeded fragment = the floor), recent_contact, the shadow judge if the judge hubs are up, LLM calls and wall-seconds per arc.

**Pre-registered thresholds (written before the run):** dormant_contact ≥ 0.30 in ≥ 1/3 of A2/A3 arcs (else the *selection rule* is wrong — D-0231's defeater); A1/A2 turnover above A0 on the same seeds (else the re-feed is not what holds the dream still — D-0232's defeater). Cost: 240 dream calls on a CPU hub; run in the background.

## 7. Phases, metrics, kill conditions

| Phase | What | Metric (computable here) | Kill |
|---|---|---|---|
| **1 instrument** (J-1057) | seed ids + tension labels + day-block hashes in `dream_log.jsonl`; per-scene rows; `data/logs/dream_state.jsonl` per transition; the re-entry probe (`core/dream_probe.py`: for a fragment id, its waking recall events in a window from `co_recall_ledger.jsonl`). Additive; every existing key untouched. | ≥ 14 nights (D-0230) with complete rows; **re-entry noise floor**: for cold fragments never dreamt, matched on age and origin, the 48 h waking re-entry rate. | Seed / generated / after cannot be separated from the logs → fix observability first. |
| **A experiment** (J-1059) | §6 | §6 thresholds | Neither threshold met → the dormant idea and the re-feed idea are both out; report plainly. |
| **2 shadow the winner** | the winning arm behind `DREAM_ENGINE=vault` (default off), live nights, all four legacy writebacks untouched; publish the coordinate, nothing reads it yet. | on ≥ 30 nights: turnover and dormant_contact vs the Phase-1 legacy baseline; the stranger's **re-entry** within 48 h vs the noise floor — counted per D-0233's option (B first: a waking thought counts only if its embedding is closer to the dormant fragment than to the injected dream tail). | Re-entry not above the noise floor on ≥ 30 nights → the dream reaches the vault but the day does not carry it back; stop before any read path. |
| **3 the cup** | idle-seed stop reads the coordinate as a cup, dispatcher-gated; the candidate "what became of …" frontier question logged, not written. | two weeks of ride log: share of cups followed by a train that touches the stranger; frontier candidates that would have been world-questions. | No cup can be shown to precede such a train → drop the channel (D-0149's defeater shape). |
| **4 cross-dream, with the antagonist already on** | residue N may enter seed N+1 only through the seed interface and only past the 3-of-5 antagonist. | prior-night residue predicts tonight's contact beyond seed variance; no id seeded > 3/5 nights. | Any recurrence past the cap, or no predictive signal → no more cross-dream machinery. |

Each phase after A gets its own `/decide` before it runs and a founder read of its log before the next (dosed_coupling §4's law). No phase touches the frozen weights, the axiom, or the memory store schema.

## 8. What this is NOT
- Not a rewrite of sleep, fatigue, naps, or the night ledger. Not a story generator upgrade — prose quality is not a metric anywhere above.
- Not deletion of the four live writebacks; not a new automatic write of any kind. The dream proposes a coordinate; the day decides, by whether it goes there.
- Not a claim about consciousness. Not a fix for the resolution rate.

## Pointers
- GPT/Gemini design of record: `docs/reviews/dream_overhaul_founder_design_2026-09-15.md`; the counter-read: I-0068.
- Engine: `nodes/dream_node.py` (`synthesise` L133-297, `_gen_episode` L302-425, `_gather_materials` L538-572, `_load_top_tensions` L574-632, `_bridge_final` L447-474, `_ground_symbols` L763-794, `_log_arc` L796-819); `core/night.py` (`dream_lag_material` L332, `dream_fade` L199, `waking_dream_seed` L243); call site `core/orchestrator.py:2976`.
- Stores: `data/dream_log.jsonl`, `data/logs/dream_resolution_shadow.jsonl`, `data/sleep_dream_probe.jsonl`, `data/co_recall_ledger.jsonl`, `data/memory/nascence.db` (`memory_fragments`, `memory_edges`).
- **Phase 1 (J-1057, 2026-09-17, F-1471):** `data/logs/dream_state.jsonl` (per-transition sidecar), `data/logs/dream_assoc_probe.jsonl` (before/after delta-association pairs) — new logs; `core/dream_probe.py` (`probe_pair`, `log_seed_pairs`); `scripts/dream_assoc_after.py` (by-hand re-probe); `scripts/dream_phase1_test.py` (in-vitro smoke test, no LLM/live writes).
- **Experiment A (J-1059, 2026-09-17, F-1472):** `scripts/dream_experiment_a.py` (the four-arm runner); `docs/lab/dream_experiment_a_2026-09-17.md` (the N=2 preliminary read, method, and limitations).
- **Experiment A, N=6 re-read + freezing-bug root cause (J-1077, 2026-09-18, F-1502):** `docs/lab/dream_experiment_a_2026-09-18_scale.md`; `_bounded_day_residue()` fix in `scripts/dream_experiment_a.py`.
- **Experiment A, combined N=17 read (J-1098, 2026-09-18, F-1516):** pilot6+scale14b combined; D-0232 null replicates at N=17, D-0231 delta sign-flips by batch; judge-panel shadow read found structurally blocked (no scene text persisted) — follow-up **J-1110** spawned to add `--save-scenes` + wire the judge shadow read for the next batch.
- **Judge-panel shadow read unblocked + verified end-to-end (J-1110, 2026-09-18, F-1528):** `--save-scenes` flag + `scripts/dream_exp_a_judge_shadow.py`, real 1-seed test batch scored.
- **Fresh scaleC batch launched, launch-infra gaps found+fixed (J-1119, 2026-09-18, F-1535):** 10 new distinct seeds frozen (`--start-offset-days 2.0`), 0 arcs landed at write time, running in background via WMI past the session; Du-live/lab-experiment hub contention found. `<scratchpad>\dream_exp_a_seeds_J1119_scaleC.json`, `dream_exp_a_run_J1119_scaleC.log`, `analyze_combined_J1119.py`.
- **scaleC crashed after 2/40 arcs, WMI+MKL fix only partial, judge-shadow scored what landed (J-1125, 2026-09-19, F-1545):** same `forrtl: error (200)` crash recurred ~18 min into the fixed run; `dream_exp_a_judge_shadow.py` run on the 2 completed arcs (both `transformed=True`, `dormant_trace` unavailable — JUDGE_1/LAN-HOST:11438 timeout); zero new N. `run_J1125_judge_shadow.py` (isolate() wrapper template). Follow-up **J-1139**; skill suggestion **S-0141**.
- **scaleC relaunched with a real `--resume` fix, verified end-to-end (J-1139, 2026-09-19, F-1555):** `scripts/dream_experiment_a.py` gained an additive `--resume` flag (commit `0c9f2ff`, `jobrun/dream_overhaul`) — loads existing seeds verbatim, skips/appends instead of overwriting; Windows Event Viewer has no record of the crash (root cause still unknown). Relaunched via WMI (PID 19780, 2026-09-19 10:21:20); zero new N at write time. `test_J-1139_resume_helpers.py` (resume-logic verification, session 313cd8c9's scratchpad); `J-1139_backup_{seeds,results,scenes,run}_J1119_scaleC.*` (pre-relaunch safety copies, same scratchpad). Follow-up **J-1148**.
- **scaleC crashed a 3rd time after 2 more arcs; first-ever seeded-arm judge read; combined N=18; relaunched a 4th time (J-1148, 2026-09-23, F-1755):** seed 0's A2/A3 completed (dormant_contact 0.1287/0.2712) before the same `forrtl: error (200)` recurred at seed 1 arm A0. `dream_exp_a_judge_shadow.py` run (job-id-qualified wrapper) on just the 2 new arcs: both `transformed=True`/agreed, `dormant_trace=False`/agreed — the first real seeded-arm verdicts this experiment has produced, agreeing with the numeric cosine measure at this n=1. `analyze_combined_J1119.py` re-run: 18 seed-batches complete (was 17), D-0232 turnover defeater still not met (8/17, 7/17, 7/17), D-0231 delta now +0.0173/+0.1389 (was +0.0122/+0.147), direction unchanged. Relaunched via WMI from this job's own worktree (PID 26984/34460, 2026-09-23 15:34:20) toward the remaining 36 pairs. Gap: the 2 new judge-shadow rows live only in `run_J-1148_judge_shadow.py`'s own scratchpad output, not yet merged into the canonical `data/logs/dream_exp_a_judge_shadow.jsonl` (this job's own ground rules forbade any write under `C:\Nascence\data`). Follow-up **J-1252**.
- **scaleC crashed a 4th time after 16 more arcs, best single-run progress yet; combined N=22; relaunched a 5th time; wrapper build spawned (J-1252, 2026-09-23, F-1775):** seeds 1-4 completed in full (16 new rows, zero errors) before the same `forrtl: error (200)` recurred at seed 5 arm A0 — `FOR_DISABLE_CONSOLE_CTRL_HANDLER=1` confirmed NOT to prevent the crash outright, only (at best) delay it. `analyze_combined_J1119.py` re-run: 22 seed-batches complete (was 18), D-0232 turnover defeater still not met (10/21, 8/21, 9/21), D-0231 delta now +0.0246/+0.1818 (was +0.0173/+0.1389), direction unchanged, defeater's own 1/3 threshold not triggered. Relaunched via WMI (PID 29640/20952, 2026-09-23 16:54:40) toward the remaining 20 pairs. Bookkeeping gap (J-1148's 2 orphaned judge-shadow rows) still open, 2nd consecutive job under the same ground-rule restriction — skill suggestion S-0174 (filed by J-1148) covers the ambiguity, not re-filed. Follow-ups: **J-1267** (build a capped self-relaunching wrapper — the exact WMI command is now proven 5 times, captured verbatim in F-1775), **J-1270** (check the 5th relaunch, told to defer to J-1267 if it is mid-test against the same live process, re-combine N again).
- **Capped self-relaunching watchdog built + verified end-to-end; WMI+cmd.exe environment gotcha found
  (J-1267, 2026-09-23, F-1821):** `scripts/dream_exp_a_relaunch_watchdog.py` +
  `dream_exp_a_wmi_liveness.ps1` / `dream_exp_a_wmi_relaunch.ps1` / `dream_exp_a_target_launcher.ps1` /
  `dream_exp_a_watchdog_launcher.ps1` / `dream_exp_a_watchdog_start.ps1` (all WMI `Win32_Process.Create`,
  powershell.exe-wrapped not cmd.exe-wrapped — see the dated note above for why). Start with
  `dream_exp_a_watchdog_start.ps1 -JobId <id> -Tag <tag> -NSeeds <n>` against a live batch. Follow-up
  **J-1295** on whether the cmd.exe silent-failure is environment-specific.
- **scaleC FINISHED (40/40); combined N=27; judge-shadow scored the full 20-seeded-arc set, a real
  judge-vs-cosine disagreement found (J-1270, 2026-09-23, F-1826):** `analyze_combined_J1119.py` re-run
  (27 seed-batches, D-0232 defeater still not met at 14/26·11/26·13/26, D-0231 delta +0.0223/+0.1481,
  direction unchanged). `dream_exp_a_judge_shadow.py` run on the 36 not-yet-scored pairs (0 skipped, 0
  errors) — full A2/A3 set now 0/20 `dormant_trace=True`, disagreeing with dormant_contact's own
  57.4%-clears-threshold reading at real N. Bookkeeping gap open a 3rd consecutive job (S-0174).
- **WMI+cmd.exe silent-failure caveat documented, not tested — real open question stays open
  (J-1295, 2026-09-24, F-1831):** additive caveat added to `CLAUDE.md`'s "Never launch Du's servers..."
  section and a comment-only block above the `$cmd` line in `scripts/start_supervisor_detached.ps1`
  (launch mechanism itself unchanged — verified via `git diff` showing only inserted comment lines, plus
  a clean PowerShell AST parse). Option (a) of J-1267's own briefing (test from an interactive session)
  is not practical from any automated job-run dispatch, this job included; follow-up **J-1300** spawned
  `needs_input` (not autonomous) so it reaches a real interactive session instead of looping back through
  another automated agent.
- Thought T-0058 → idea I-0068 → this plan. Session 2dde3aac-5216-458e-ac8c-94fc2164b91f.
