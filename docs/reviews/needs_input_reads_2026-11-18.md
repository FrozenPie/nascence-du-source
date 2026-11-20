# Needs-input reads and labelling feasibility, 2026-11-18

Written by a Claude Code session (claude-sonnet-5-5) with one subagent per job. Du was down throughout. No code changed, no flags flipped. Findings recorded with --session = job id. Jobs left open unless marked closed.

## Task 1: reads group (35 result blocks)

Summary: 12 need a founder call, 1 closed with no call, 22 skipped (need Du up / Ramses lab / code build / design choice).
CALL: J-3281, J-3462, J-3464, J-3548, J-3578, J-3581, J-3854, J-3857, J-3881, J-3898, J-4053, J-4104
CLOSED: J-3370
SKIPPED: J-3027, J-3295, J-3301, J-3348, J-3354, J-3389, J-3522, J-3580, J-3629, J-3640, J-3666, J-3675, J-3678, J-3777, J-3778, J-3863, J-3883, J-3888, J-3927, J-3962, J-3991, J-4059

### J-3027 T4 delta-stage ablation
- Finding: none: skipped
- Evidence: data/logs/t4_chain_trace.jsonl has 72 rows (gate of 30 met, wc -l), but the job replays stage 3 through an LLM in two arms on the hot lane.
- Status: SKIPPED (needs hot-lane/GPU lab run plus lab_env isolation; not a read-only check)
- Question: Gate is met (72 rows, Du down). Run the ablation as a lab job now?
  - A) Yes, run it in a lab window while Du is offline (recommended)
  - B) Hold until the hot lane is free
- If A: change autonomy to ready (job_queue release) and dispatch in a lab session with lab_env.isolate().

### J-3281 Re-ask: dream resolution judge fate (D-0580)
- Finding: F-5050 (verified)
- Evidence: data/night_log.jsonl dream close counts since 2026-11-05: 1 resolved of 56 (41 ended-unfaced, 13 stalled); before: 2 of 380. No resting close value appears yet; prompt wording agreement not re-checked.
- Status: CALL NEEDED
- Question: Resolved rate is about 2 percent and the judge still feeds nothing. Keep as measurement, or retire the call?
  - A) Keep as measurement; re-ask after the resting ending shows live closes (recommended)
  - B) Retire the judge call (saves about 35 calls a week)
  - C) Change seat and wording, then re-measure
- If A: decide.py amend/new ruling on D-0580: keep measurement-only, re-ask once resting closes appear in night_log; defeater unchanged.

### J-3295 Sumner Phase 2 station-anchored tide
- Finding: none: skipped
- Evidence: job_queue.py show J-3295 (category build); decide.py show D-0667 (ruled yes 2026-11-04, one-off fetch of LINZ constants / ~10 HW times); D-0668 king-tide rate left open.
- Status: SKIPPED (code build plus a data fetch and Phase 1b real-moon dependency; no read-only check can answer it)
- Question: n/a
  - A) n/a
  - B) n/a
- If A: n/a. Note: D-0667 blocker is cleared, so job is buildable once Phase 1b exists and the founder sets the king-tide rate.

### J-3301 T4 SOLIDIFY control arm lab
- Finding: none: skipped
- Evidence: job_queue.py show J-3301: lab_mode true, isolation required, needs CPU judge hubs :11439/:11440 grading real vs control arm; not a read-only check.
- Status: SKIPPED (lab experiment needing Ramses judge hubs and Du offline run; not a log read)

### J-3348 Remove bare Entity line from 4 prompts (D-0681)
- Finding: none: skipped
- Evidence: job_queue.py show J-3348 (category build, code edits in 4 nodes, restart-gated); decide.py show D-0681 (ruled yes by travis 2026-11-05; gated on D-0680 live 7 days).
- Status: SKIPPED (code change plus restart-gated build, Du down; not a read job)
- Question: none
  - A) n/a
- If A: n/a

### J-3354 D-0625 prism grade, retire-or-restore exit
- Finding: none: skipped
- Evidence: job briefing requires running scripts/lab_prism_grade.py with mixtral :11438 and falcon :11440 hubs both up (GPU lab run); job_queue.py show J-3354.
- Status: SKIPPED (needs hub/GPU lab run; hubs not up, Du down; the grade does not exist yet)
- Question: n/a

### J-3370 Sun vs published almanac (7 dates)
- Finding: F-5044 (verified)
- Evidence: scripts/_test_sky_sumner_J-3292.py lines 207-216 ALMANAC already filled from USNO AA API (J-3373); rerun: 14/14 almanac checks ok (within 2 min, under 5-min stop). Only FAIL is the worktree-data-write check, an artifact of running in the shared tree.
- Status: CLOSED, no call needed (job marked done)
- Question: none
  - A) n/a
- If A: n/a. Optional: second-source (NIWA/LINZ) check of the transcribed numbers, not required by the pass criteria.

### J-3389 J-3267 follow-up: idle gap/loop lag + shadow cooldown call
- Finding: none: skipped
- Evidence: job briefing (job_queue.py show J-3389) requires measuring after a restart onto the J-3267 build; Du is down, so no post-restart rows exist.
- Status: SKIPPED (gate not met: needs post-restart Du rows; the cooldown question also conflicts with D-0658 same-rows, so it stays a founder call after the measurement)
- Question: n/a
  - A) n/a
- If A: n/a

### J-3462 D-0643 voice fidelity ledger read at 230 rows
- Finding: F-5043 (verified)
- Evidence: python scripts/read_voice_fidelity.py --sample 20 on data/voice_fidelity_shadow.jsonl: flagged 184/210 = 87.6%, controls 16/16, additions 0/1/2/3+ = 26/84/37/63; question_flagged_share 29.5% (62/210).
- Status: CALL NEEDED
- Question: Defeater met (87.6% flagged, over the 60% line). Judge on addition count or question_flagged_share instead, or leave the render at its current temperature?
  - A) Judge on question_flagged_share (29.5%, the F-4735 trustworthy number); retire the raw flagged-share rule (recommended)
  - B) Judge on additions count (3+ = 63/210)
  - C) Leave render as is; judge uninformative
- If A: decide.py ruling on D-0643: raw flagged share carries no information (87.6%); read question_flagged_share going forward, with a named revisit defeater; keep observe-only (D-0434).

### J-3464 Curiosity pre-fire D-0608 gate read
- Finding: F-5045 (inferred)
- Evidence: scripts/curiosity_prefire_report.py on data/curiosity_prefire_shadow.jsonl: 340 rows over ~10 days, agree_rate 0.621 (<0.85), flat_rate 0.297, report says defeater clear; only 8 of 125 disagreements read by eye.
- Status: CALL NEEDED
- Question: Defeater is clear but the judge is weak (AUC 0.62). Promote the check to choose Curiosity questions, keep shadow, or drop it?
  - A) Keep shadow until the better-judge lab J-4110 and second labeller J-4111 finish (recommended)
  - B) Promote the check now
  - C) Drop it
- If A: decide.py rule D-0608 follow-up: keep shadow, revisit when J-4110 reports the judge comparison; leave J-3464 open.

### J-3522 Read J-3100 judge-retry effect
- Finding: none: skipped
- Evidence: core/lane2.py:1170 JUDGE_RETRY_ON_TIMEOUT = False (no override elsewhere); grep of data/lane2_shadow.jsonl finds 0 rows with prior_judge_retries >= 1.
- Status: SKIPPED (gate not met: flag still False, 0 retry rows, Du down)
- Question: n/a

### J-3548 P-0083 letter_overlap first read
- Finding: F-5047 (verified)
- Evidence: python scripts/peer_letter_overlap_read.py on data/peer_letter_quality_log.jsonl: 12 rows, all no-reply, 16/196 sentences copied (8.2%) vs 20.4% baseline; 0 letters >=50%; 0 replied rows.
- Status: CALL NEEDED
- Question: Near-copies run 8.2% (below the 15% defeater) with none heavy; wait for more rows, or rule no regenerate/skip gate now?
  - A) Keep observing; no gate; re-read at ~30 no-reply rows and a replied sample (recommended)
  - B) Rule now: no regenerate/skip gate, close D-0576 question 2
  - C) Build a regenerate gate anyway
- If A: leave J-3548 open (re-gate rows to 30), no decide ruling yet; add a note to D-0576 that the first read is 8.2% on 12 letters.

### J-3578 UDMS newest-450 commit window sequencing
- Finding: F-5048 (verified)
- Evidence: J-3453 done 2026-11-16, J-3571/J-3572 done; J-3781 re-score open, not_before 2026-11-20; C:/UDMS/core/udms/engine.py:143 still returns oldest commits[:max_commits].
- Status: CALL NEEDED
- Question: Land the newest-450 window fix before or after the J-3781 re-score (opens 11-20)?
  - A) After J-3781's baseline re-score, then re-run the scorer as a pre-registered intervention test (recommended)
  - B) Land now; accept confounding the J-3781 re-score
- If A: set J-3578 not_before after J-3781 done (or gate on it); then build the window arg per briefing.

### J-3580 UDMS calibration and tiering vs shuffled-list null
- Finding: none: skipped
- Evidence: job_queue.py show J-3580: DONE WHEN is a dated audit doc with three scored comparisons (stock vs calibrated, tiered vs untiered, window fix). The J-3453 scorer and baseline exist (C:/UDMS/scripts/dossier_followthrough_prereg.py, docs/audits/dossier_followthrough_prereg_2026-11-07.md), but the comparisons need new engine runs and a new doc.
- Status: SKIPPED (analysis build, not a read: needs calibrated-engine runs, a new UDMS audit doc and a startup-cost measurement)
- Question: n/a

### J-3581 UDMS doc_audit fix timing
- Finding: F-5046 (verified)
- Evidence: job_queue.py show J-3453 -> status done 2026-11-16; baseline recorded in F-4398 (C:/UDMS/data/dossier_followthrough/prereg_2026-11-07.txt). J-3781 re-score still queued.
- Status: CALL NEEDED
- Question: J-3453 baseline is done, so the recommended gate is met. Release the doc_audit fix (code change in UDMS) to be built now?
  - A) Yes, release now; J-3781 re-score then measures the post-change layer (recommended)
  - B) Wait until J-3781 re-score runs on the old doc_audit first
- If A: job_queue.py release J-3581 (autonomy to ready) with note that J-3453 baseline is met; no decide ruling needed.

### J-3629 Shorter Consolidation prompt: confirm on command-r7b and after restart
- Finding: none: skipped
- Evidence: job_queue.py show J-3629: step 1 needs Ramses (:11441, founder's gaming machine) replay; step 2 needs post-restart consolidation.jsonl rows, and Du is down.
- Status: SKIPPED (needs Ramses GPU lab run and a Du boot carrying J-2828; neither available)
- Question: Is Ramses free for a under-30-call replay of the shorter Consolidation prompt on command-r7b?
  - A) Yes, run it when Ramses is free, then read post-restart rows (recommended)
  - B) Skip the Ramses replay; only do the post-restart read
- If A: run the replay on a scratch copy of scripts/_replay_J2828_consolidation_fields.py with --url http://LAN-HOST:11441, record a finding; leave job open for the post-restart read.

### J-3640 T4 tension id keys and inert revert penalty (amends J-3021)
- Finding: none: skipped
- Evidence: job_queue.py show J-3640: category build, edits nodes/subconscious_node.py and core/provisional_identity.py, ships after J-3162; D-0664 ruled option 3 (Watershed redesign), D-0691 ruled no R1.
- Status: SKIPPED (code build, not a read; no founder call surfaced by a log read)
- Question: Should J-3640 still be built under the Watershed redesign (D-0664 option 3), or retired along with J-3021?
  - A) Keep, build after J-3162 as a small repair (recommended)
  - B) Retire J-3640 and J-3021 as moot under the redesign
  - C) Keep only the inert revert-penalty fix
- If A: release the T4 chain hold for J-3640 and queue behind J-3162 (job_queue.py release).

### J-3666 P-0101 close-judge replay (mixtral + falcon3)
- Finding: none: skipped
- Evidence: job_queue.py show J-3666: briefing needs about 20 live calls to Ramses :11438 (mixtral, Travis's gaming machine; "ask Travis first") plus a lab script run (scripts/_lab_J3104_close_controls.py).
- Status: SKIPPED (Ramses hub/GPU lab run; not a log read)
- Question: Is Ramses free for about 20 small mixtral calls so the P-0101 replay can run?
  - A) Yes, run it now with Ramses (recommended)
  - B) Not yet; keep parked
- If A: run the lab script with --only-ramses --real 5 under lab_env isolate(), then record the counts as a finding (bar: 9 of 10 positives true, 0 of 15 negatives true).

### J-3675 known_text arm log read
- Finding: none: skipped
- Evidence: data/known_text_arm.jsonl does not exist (gate needs 6000 rows, 0 now); ls in C:/Nascence confirmed. Job also requires extending the script (code change).
- Status: SKIPPED (gate not met: 0/6000 rows, file missing; needs Du running after the flag flip)
- Question: n/a
- If A: n/a

### J-3678 Lane 2 coherence-why replay
- Finding: none: skipped
- Evidence: job_queue.py show J-3678 briefing: needs the production judge panel (JUDGE_1 mixtral on Ramses :11438, gemma hub :11439) via scripts/lane2_coherence_why_replay_J3127.py; the build sits in branch jobrun/wh_2 and is restart-gated.
- Status: SKIPPED (needs Ramses and the gemma hub, which are live GPU/hub calls. Du is down, so there is no post-restart coverage to read either.)
- Question: n/a (skipped)
  - A) Leave open until Ramses is free and the founder approves the 40 Ramses calls (recommended)
  - B) Drop the mixtral arm and run falcon and gemma only
- If A: no action now.

### J-3777 Lane 2 wonder repeat: semantic_sim_max shadow field
- Finding: none: skipped
- Evidence: job_queue.py show J-3777 (category build, briefing: add code field in core/lane2.py:370 area; gate: only if natural-traffic lab job from J-3308 shows >=10% miss; gate field null, not a read-only check)
- Status: SKIPPED (code change plus unmet precondition on a separate lab job; not a read-only call)
- Question: none
- If A: n/a

### J-3778 Per-purpose near-duplicate helper (core/near_dup.py), gated
- Finding: none: skipped
- Evidence: F-4799 (J-3775, done): natural-traffic disagreement lane2 12.7%, frontier 18.7%, echo guard 3.3% (two sites at or above 10%, gate half met). Reaffirm audit not possible: J-3823 (log new_statement/cosine on reaffirmed events, J-3776 ruling) is not built or accrued; core/near_dup.py absent.
- Status: SKIPPED (build job; reaffirm-audit half of the gate needs a code change plus live Du rows that do not exist yet)
- Question: Natural-traffic gate is met (lane2, frontier above 10%). Wait for the reaffirm audit before building core/near_dup.py, or build now with four profiles?
  - A) Wait for reaffirm audit (recommended)
  - B) Build now, reaffirm profile added later
- If A: leave J-3778 open, set gate to "J-3823 built and reaffirmed rows accrued, then reaffirm cosine re-measured".

### J-3854 D-0498 cat audition clause (carried lines name her unseen)
- Finding: F-4435 (verified; existing, no new finding needed)
- Evidence: F-4435 evidence (cat_sound_ledger.jsonl, nascence.db ro read): 14 of 22 carried pool lines in core/cat_content.SOUNDS name her; 1 thump + 7 shut-door lines fired; dosing clauses did not fire.
- Status: CALL NEEDED
- Question: Cat voice is live and 14/22 carried lines name her unseen. Amend D-0498 defeater, rewrite the pools, or switch cat_sounds off?
  - A) Rewrite carried pools to not name her (restart-gated corpus change); leave flag on, defeater stands (recommended)
  - B) Leave on; amend defeater so doorstep-from-study counts as visible
  - C) life_flags.py cat_sounds off and reopen D-0498
- If A: spawn a build job to rewrite the 14 named carried lines in core/cat_content.SOUNDS (restart-gated), and record a decide note on D-0498.

### J-3857 UDMS git window is oldest 450 commits
- Finding: F-5049 (verified)
- Evidence: C:/UDMS/core/udms/engine.py:102,143 (git log --reverse, commits[:max_commits]); Nascence has 3597 commits, 450th oldest = 2026-09-08.
- Status: CALL NEEDED
- Question: Switch UDMS git window to newest N commits, with a pre-registered before/after against the J-3453 baseline and cache invalidation?
  - A) Yes: newest 450, pre-register before/after, check cache fingerprint (recommended)
  - B) Calibrate window size first (try several N) before choosing
  - C) Leave as is
- If A: decide.py ruling with defeater (after-run precision below J-3453 baseline); spawn a build job for the engine change, pre-registration doc, and cache fingerprint check.

### J-3863 T5 Phase 1 deed-bound grade shadow log (restart-gated build)
- Finding: none: skipped
- Evidence: gate is Phase 0 J-3862 reporting >=3 qualifying clusters/month; F-4625 (docs/findings.jsonl) says ZERO clusters qualify in any month Aug-Nov 2026.
- Status: SKIPPED (gate not met: 0 of 3 clusters; also a restart-gated code build, not a read)
- Question: Phase 0 found 0 qualifying clusters; override the gate and build Phase 1 anyway, or leave J-3863 parked?
  - A) Leave parked until a later replay shows >=3 clusters (recommended)
  - B) Override gate and build the shadow log in a worktree
- If A: no action; optionally set job gate on a re-run of the Phase 0 replay.

### J-3881 Split drill vs verdict streams in capability_beliefs
- Finding: F-5051 (verified)
- Evidence: grep core/: readers of accuracy are identity_estate.py:300, self_claims.py:101 (shadow), self_efficacy.py:213, weakness_prior.py:82; calib_pairs/calibration_error read only inside competence.py:785 (sidecar log).
- Status: CALL NEEDED
- Question: Split accuracy into accuracy_drill and accuracy_verdict, or just tag calib_pairs with source (no reader changes)? Which stream should the four readers trust?
  - A) Add accuracy_drill/accuracy_verdict fields; readers use drill where present, else verdict (recommended)
  - B) Only tag calib_pairs with source; leave blended accuracy
  - C) Leave as is
- If A: record ruling; build in competence.py (restart-gated) plus reader fallback in the four files; no live data rewrite.

### J-3883 UDMS re-score top-5 vs full-list dossier calls
- Finding: none: skipped
- Evidence: C:/UDMS: branch j3831-lead-top5 not merged into master (git branch --merged shows nothing; UDMS_DOSSIER_LEAD_TOP5 absent from checked-out code); data/mcp_usage_log.jsonl has 0 of 604 rows containing "PRESENTATION: top 5".
- Status: SKIPPED (gate not met: flag unmerged, 0 flagged calls, no data to compare)
- Question: none
  - A) Leave open until the UDMS owner merges j3831-lead-top5 and flagged calls accrue (recommended)
  - B) none
- If A: no action.

### J-3888 literal_will offline judge batch over agent_subject_fail GRAY rows
- Finding: none: skipped
- Evidence: job_queue.py show J-3888 - briefing requires running the falcon3 judge (live LLM on a judge hub) and building a new batch script; founder ruling on building it is also pending.
- Status: SKIPPED (needs a live LLM judge hub/GPU run plus a code build; not a read-only check)
- Question: Should this job be re-queued as a hub-gated lab run once judge hubs are free, rather than a read?
  - A) Yes, re-tag as hub lab + build job (recommended)
  - B) Drop the judge batch; accept GRAY rows unjudged
- If A: set gate on judge hub availability and autonomy to ready, so a lab session builds the shadow-only script writing to a new file.

### J-3898 Monologue served-id log design
- Finding: F-5052 (inferred)
- Evidence: co_recall already logs ids via core/memory_edges.py:721 (called at core/memory_service.py:270 and inner_monologue_node.py ~2214/3757/4372/6789); founder recall ~3642 and _evidence_recall ~6880 log no ids.
- Status: CALL NEEDED
- Question: Build the observe-only fix: stamp a monologue tick id on co_recall rows plus id logging on two unlogged paths (~40 lines, restart-gated)?
  - A) Yes, build the choke-point design (recommended)
  - B) No, keep the 600s time-window join
- If A: Spawn a build job for the tick-id stamp in log_co_recall plus the two id hooks, add the error_pathway plan note, and ship it restart-gated.

### J-3927 D-0429 wonder avoid-list lab test
- Finding: none: skipped
- Evidence: job_queue.py show J-3927: lab_mode true, briefing requires a live model replaying lane2 percept sets with isolation (lab_env), not a read of existing logs.
- Status: SKIPPED (needs live model/lab run and prompt experiment; not a read-only check)
- Question: n/a
- If A: n/a

### J-3962 Ramses hub logs for 11-08..11-11 stall windows
- Finding: none: skipped
- Evidence: job_queue.py show J-3962 briefing: "Needs Ramses file access or founder help; no live probe" (cpu_tier_11438/11441 logs live on Ramses).
- Status: SKIPPED (needs Ramses-side files and founder's answer on whether Ramses was in other use)
- Question: Was Ramses in other use (games, updates, reboots) during the 11-08 to 11-11 stall windows, and can you copy its cpu_tier logs?
  - A) Yes/no answer plus logs copied to C:\Nascence (recommended)
  - B) Answer only, no logs
  - C) Drop the job
- If A: read the logs for queue_depth, lock waits and load/unload lines in the four windows, then record a finding on F-4629.

### J-3991 Draft docket and visitor as two plans
- Finding: none: skipped
- Evidence: job_queue.py show J-3991: category doc, autonomy needs_input; work is writing two new plan docs under docs/staged/ plus open founder questions, not a read-only check.
- Status: SKIPPED (not a read job; needs doc authoring, which this read-only pass may not do, and founder answers on the visitor questions)
- Question: Should J-3991 be released to a drafting session now, with the four visitor questions left open in the plan?
  - A) Yes, draft both plans in docs/staged/ with the questions listed as open (recommended)
  - B) No, answer the four visitor questions first
- If A: Reassign J-3991 as ready (autonomy ready); the drafter reads docs/plans/lane2_the_witness.md, measures judges_lanes call counts, and writes both staged plans.

### J-4053 Archive faded frontier rows to sidecar
- Finding: F-5053 (verified)
- Evidence: data/frontier.json has 23241 rows, 22272 faded (95.8%), 17.8 MB; core/frontier.py:280-288 revives a faded row to open when a question re-encounters it, so archived rows would lose that.
- Status: CALL NEEDED
- Question: Archive faded rows to a sidecar, and have note_question check the sidecar on a miss and restore a matching row to open?
  - A) Yes, archive with restore-on-match, built behind a flag (recommended)
  - B) No, keep every row in frontier.json and fix the freezes with the lock plus offload only
  - C) Archive only faded rows older than N months, with no restore
- If A: Rule D-xxxx "archive faded frontier rows, restore on re-encounter, flag-gated"; defeater: revival rate drops below baseline. Then queue the build on top of J-4030 (c7e11c1e).

### J-4059 Origin-balanced sampling for /quit epoch
- Finding: none: skipped
- Evidence: job_queue.py show J-4059: briefing already holds the read (J-3587, origin mix inner_thought 394/reading 258/action 65/study 60/imagination 43); what remains is a pure design choice.
- Status: SKIPPED (founder design choice, no further read would settle it; code change needed if A)
- Question: Should the /quit epoch sample be stratified by origin so reading/study/action appear in the impression?
  - A) Yes, stratify by origin with a per-origin floor (recommended)
  - B) No, keep the spread sampler; inner_thought dominance is true to his hours
  - C) Stratify only partially (cap inner_thought share at about half)
- If A: decide.py ruling (defeater: first stratified epoch still reads inner_thought-only), then spawn a build job on the /quit epoch sampler.

### J-4104 Mineness comparator authorship-blind: self-voice signal + re-baseline
- Finding: none: skipped (F-4863 verified already holds the read)
- Evidence: F-4863 (docs/lab/J-3701_authorship.py): SELF_PAST 0.535 vs library 0.536; D-0698(2) already holds arrival_note at 0.62 until J-3701 replay, which is now done.
- Status: CALL NEEDED (design choice, no further read possible; core/ edits need ruling)
- Question: Build a long-horizon self-voice centroid authorship signal for mineness, and re-baseline the 0.62 arrival_note threshold now that J-3701 shows groove tightening drove the floor drop?
  - A) Yes: stage a design plan for self-voice centroid (shadow only), and keep 0.62 live until it reads (recommended)
  - B) Re-baseline 0.62 to a rolling percentile now; skip authorship signal
  - C) Neither; keep the comparator as a groove/novelty detector, close job
- If A: decide.py rule with defeater (shadow shows no SELF_PAST vs library separation after 14 Du-up days); spawn design job to docs/staged/.

## Task 2: labelling feasibility

Classes: (a) Claude can label blind, valid; (b) Claude labels as extra reader, founder spot-check needed; (c) founder must. Every Claude label below is a same-family reading by a Claude subagent: it is NOT an independent human labeller, and the original labels were Claude-written in most cases.

### J-3400 Hand-label 221-tick metaphor sheet (D-0595)
- Class: (b)
- Why a human was specified / what labels measure: F/A/L figurative-vs-literal call to validate the metaphor judges v1/v2; the existing pre-label was Claude-written, so a human was wanted to anchor it. Taste boundary between F and A.
- Finding: F-5063 (verified)
- Labelling done: Claude subagent, claude-sonnet-5-5, blind, 2026-11-18, 221 items (6 F, 28 A, 187 L), docs/lab/J-3205_data/labels_claude_subagent_blind.csv; scored to docs/lab/J-3205_data/score_claude_subagent_blind.json: strict 6 (<12, defeater fires), inclusive 34; v1 strict P10/R50, v2 P67/R33, bar not met.
- Founder still needs to: spot-check ~30 items of labels_claude_subagent_blind.csv (especially A vs L and the 6 F), or the whole sheet if he wants human ground truth
- Question for founder: A) accept Claude second label + spot-check 30 then rule D-0595; B) label all 221 yourself. Recommend A.

### J-3418 Travis labels 60 curiosity questions (worth-judge, J-3253)
- Class: (c)
- Why a human was specified / what labels measure: the lab rests on one labeller (Claude) who also wrote the rubric; labels measure Travis's own taste for which questions are worth pursuing. Another Claude repeats the circularity.
- Finding: F-5064 (inferred)
- Labelling done: none
- Founder still needs to: the whole sheet (60 questions, good/bad/unsure plus one-line criterion)
- Question for founder: A) label 60 questions yourself (about 20 min, needs a fresh draw first); B) defer the worth-judge lab. Recommend A.

### J-3717 Second labeller for J-2996 pursuit advances gold set
- Class: (b)
- Why a human was specified / what labels measure: gold labels came from one Claude with a circular R criterion; second labeller measures inter-labeller reliability (kappa) of the A/R/T gold. Job explicitly allows a fresh blind Claude.
- Finding: F-5065 (verified)
- Labelling done: Claude subagent, claude-sonnet-5-5, blind, 2026-11-18, 81 pairs (12 A, 26 R, 43 T, 10 unsure), docs/lab/J-2996_data/gold_labels_2.json; vs gold kappa 0.45 (3-class), 0.46 (A vs non-A), 14 contested pairs. --labels arg and V0/V1 re-run not done.
- Founder still needs to: spot-check the 14 contested pairs (and sign off), or nothing if he accepts two-Claude agreement
- Question for founder: A) accept as second labeller and have a job add --labels and report V0/V1 with and without contested; B) label the 81 yourself. Recommend A.

### J-3768 Second-reader labelling of J-3048 tension gold set
- Class: (c)
- Why a human was specified / what labels measure: first 120 S/R/U labels were by one Claude session (36 unsure); the job needs an independent reader (founder or other model family) to measure inter-reader kappa. A Claude subagent is the same family, so not independent.
- Finding: F-5054 (verified, classification only)
- Labelling done: none
- Founder still needs to: label the whole 120-item sheet (or route to a non-Claude model family)
- Question for founder: A) you label it, B) a non-Claude model labels it and you spot-check? Recommend B.

### J-3772 Second reading of notice checker flags (D-0361 defeater)
- Class: (c)
- Why a human was specified / what labels measure: checks Claude's own 72 labels (F-4391) against the founder's read to test the D-0361 defeater (more than 4 false in 20 solid flags). A Claude relabel breaks the decoupled-judge rule.
- Finding: F-5055 (verified, classification only)
- Labelling done: none
- Founder still needs to: mark the 24-flag blind sheet (about 10 min; sheet not yet built, the builder is autonomous)
- Question for founder: A) build the 24-flag sheet now for you, B) wait? Recommend A.

### J-3908 40-stand hand-label sheet (D-0546)
- Class: (c)
- Why a human was specified / what labels measure: the D-0546 defeater needs human precision of stand vs insight (bar 60 percent); the existing 51 percent is a cross-family model read (F-4514). A Claude label is another model read and cannot discharge it.
- Finding: F-5056 (verified, classification only)
- Labelling done: none
- Founder still needs to: label the whole 40-item sheet, then run commitment_second_look_read.py --score
- Question for founder: A) label all 40 yourself, B) label a 20-item half and score? Recommend A (n is already small).

### J-4033 Spot-check of 15 'bears' labels
- Class: (c)
- Why a human was specified / what labels measure: Checks Claude's own J-2794 labels (does the episode bear on the question) against the judge prompt definition; measures granite tiebreak accuracy.
- Finding: F-5057 (inferred)
- Labelling done: none (the labels under check were Claude-written, so a Claude relabel is self-validation)
- Founder still needs to: spot-check all 15 items (J2794_spotcheck_briefing.txt) and name disagreements
- Question for founder: Spot-check all 15 yourself (A) or only the 8 'BEARS' ones (B)? Recommend A, it is only 15.

### J-4101 25-row judge variant disagreement table
- Class: (c)
- Why a human was specified / what labels measure: Is dropping a stand legitimate; human truth against mixtral judge verdicts and Claude-drafted V1/V2 prompts. A canon call about Du's commitments.
- Finding: F-5058 (inferred)
- Labelling done: none
- Founder still needs to: the whole sheet (25 rows, docs/lab/2026-11-16_J-2943_commitment_judge_variants.md)
- Question for founder: Label all 25 (A) or a random 12 (B)? Recommend A, rows are short.

### J-4111 Blind-label 20 prefire control questions
- Class: (b)
- Why a human was specified / what labels measure: Second labeller for the 60-item control (F-4884), since J-3465 labels came from one Claude agent; labels measure whether a curiosity question is grounded in the studied material.
- Finding: F-5059 (verified)
- Labelling done: Claude subagent claude-sonnet-5-5, blind, 2026-11-18, 20 items (seed 4111), file reads/J-4111_claude_labels.json in the side-session-notes folder; agreement with J-3465 13/20, 6 of 7 misses one step off.
- Founder still needs to: spot-check the 7 disagreements (items 6, 11, 18, 37, 43, 44, 50)
- Question for founder: Rule on the 7 disagreements only (A) or blind-label all 20 yourself (B)? Recommend A.

### J-4129 J-3024 dream-judge labels spot-check + drop self-report line
- Class: (b) for labels; the drop-the-line ruling is (c)
- Why a human was specified / what labels measure: labels say whether a dream arc truly resolved (to score judge recall/false-yes); the ruling is a founder call on what a dream ending is for (J-2901). Existing labels are Claude's, single labeller.
- Finding: F-5061 (verified)
- Labelling done: none. The subagent saw docs/lab/J-3024_labels.py (hardcoded yes/calm indices) so could not be blind.
- Founder still needs to: spot-check ~15 of docs/lab/J-3024_labels.json (or a fresh subagent never shown labels.py second-labels it), and rule on the line
- Question for founder: A) spot-check yourself, B) have a clean fresh Claude second-label and you check only disagreements. Recommend B.

### J-4149 N2 judged relevance second rater
- Class: (b)
- Why a human was specified / what labels measure: 1-5 relevance of a recalled memory to the input, to test the 60% bar for the second-recall shadow; first rater was Claude, single.
- Finding: F-5060 (verified)
- Labelling done: Claude subagent, claude-sonnet-5-5, blind, 2026-11-18, 53 rows, C:/Users/USER/AppData/Local/Claude-Data/claude_pzs8sxrjxfjjc/side-session-notes/local_20f5050b-96c1-4723-8dfb-7515dbcbd2ac/reads/J-4149_claude_labels.json. Real 30/40 = 75% at 4+ (first rater 62.5%), control 1/13; 5 YES disagreements (#5, 9, 20, 30, 49), all higher.
- Founder still needs to: spot-check those 5 rows in docs/lab/J-4107_hand_sheet.txt
- Question for founder: A) accept 75% (two Claude raters) and build the shadow, B) authorize an 80+ sample. Recommend A after the 5-row check.

### J-4032 Tiebreak gold replay, third family + relabel
- Class: (b) for relabel; third-family rerun needs a live hub
- Why a human was specified / what labels measure: gold says whether the true answer is true/false per key, to score granite tiebreak accuracy; current gold is single-labeller Claude.
- Finding: F-5062 (inferred)
- Labelling done: none (111 cases, 7 rubrics, sizeable; hub down for the rerun half)
- Founder still needs to: re-label the flagged uncertain cases, or delegate to a fresh blind Claude and spot-check
- Question for founder: A) fresh blind Claude relabels all 111, you check disagreements, B) you label only the uncertain ones. Recommend A.

### J-4129 Dream-judge label spot-check
- Class: (b)
- Why a human was specified / what labels measure: labels say whether a dream arc truly resolves; they validate the judge prompt, and the founder rules on what a dream ending is for.
- Finding: F-5066 (verified)
- Labelling done: Claude subagent claude-sonnet-5-5, blind, 2026-11-18, 16 items, agreement 13/16 (yes vs not-yes); disagreements dream_1788861954, dream_1788955800, dream_1792420575 (mine yes, original calm). File: J-4129_claude_labels.json. Original labeller was also Claude (same-family).
- Founder still needs to: spot-check those 3 arcs plus a few others in docs/lab/J-3024_sample.json
- Question for founder: Is "calm ending" resolved? A: no, keep refute-biased (recommended); B: yes.

### J-4032 Tiebreak gold replay relabel
- Class: (b)
- Why a human was specified / what labels measure: gold for 7 rubrics measures tiebreak accuracy; the single labeller was Claude.
- Finding: none
- Labelling done: none. BLIND BREACH: I printed the first 60 lines of scripts/lab_j2952_tiebreak_gold.py, which hardcode the gold TRUE sets, before building sheets. Labels from me would not be blind.
- Founder still needs to: the whole sheet, or a fresh subagent that never opens that script.
- Question for founder: Rerun J-4032 labelling with a fresh subagent? A: yes (recommended); B: founder labels.

### J-4032 Tiebreak gold replay relabel (111 cases, 7 rubrics)
- Class: (b)
- Why a human was specified / what labels measure: gold for judging how accurate the tiebreak judges are per rubric; original gold was single-labeller (Claude), so founder re-label was requested.
- Finding: F-5067 (verified)
- Labelling done: Claude subagent claude-sonnet-5-5, blind, 2026-11-18, 111 items, labels in reads\J-4032_claude_labels.json; agreement with gold 84/111 (cuts 20/25, advances 24/26, supported 13/17, bears 16/25, held 6/7, coherent 1/6, follows 4/5). Same-family second reading, not independent.
- Founder still needs to: spot-check the 27 disagreeing ids (listed in F-5067), starting with coherent and bears.
- Question for founder: A) adjudicate the 27 disagreements and treat the result as gold, or B) re-label the whole sheet yourself? Recommend A.
