# Plan progress audit of all 102 plans, three job-run waves, and a founder questionnaire over the needs-input jobs

## Session timing
- **Session started:** 2026-11-17 22:35:21 UTC
- **Last message before wrap:** 2026-11-18 01:14:15 UTC
- **Wrapped:** 2026-11-18 01:14:16 UTC

## Summary
The founder suspected many plans had stalled, so one read-only agent audited every plan doc (102: docs/plans + docs/staged), 70 jobs were created on 36 plans, and three job-run waves (30 jobs) were then run. The founder also went through about 40 needs-input jobs by questionnaire and ruled D-0839, D-0840 and D-0841. Two Du-down labs (J-2676, J-4058) were still running in the background at wrap time, and nothing is committed yet.

## HOW TO FIND THE QUESTIONS THAT ARE LEFT (new window: start here)
The founder will continue the questionnaire in a fresh window. About 59 open jobs with autonomy needs_input remain (counted at wrap). The live list is:
- `python C:/Users/USER/.claude/skills/job-queue/job_queue.py list --needs-input`
- A grouped snapshot is in `C:\Nascence\docs\reviews\founder_needs_input_2026-11-18.md` (regenerated at wrap; groups A hand-label 15, B decision/call 26, C needs Du/hubs/lab 11, D read/discuss 7; the file also lists every job already answered this session). The grouping is keyword-based, so some jobs are in the wrong group.
- Method used: for each job, read its briefing (`job_queue.py show <id>`), then ask with AskUserQuestion (max 4 per call, recommended option first, "(Recommended)" label, standalone questions because the founder may not remember the context). Log each answer straight away: spawn a ready follow-up job with `job_queue.py spawn --kind ... --from job:<id> --briefing-file ... --autonomy ready --session <id>`, then `job_queue.py done <id> --note "Founder <date>: ..."`. Jobs are autonomy needs_input and cannot be changed to ready, so the pattern is spawn-a-ready-copy then close the original. Write briefings to files (never a backtick in a double-quoted Bash arg).
- Not yet asked and worth doing first: J-4296 (prompt_manager P1 go/no-go; check D-0633 first. D-0633 is ruled "fix twin prompt, restart clock, judge post-fix rows", so first check whether the twin fix was executed and its bytes recorded), J-3113 (pasted reviews in the social bar, wire or retire v4, conditional on J-2599), J-3063 (object permanence, five open questions, a founder discussion), J-4302 (world_shelf_gap: shelve the Maori mythology book PG42218? clocks substitute; non-Gutenberg sources, downloads need founder approval per title), J-4303 (web hand discoverability: About You book line and study encyclopedia object, D-0661), J-4297/J-4298 (strings_and_sheets Phase 2/3), J-4236 (affect_drives C/D/E/G scope; part of it answered via J-4310), J-4059, J-4244, J-3991, J-3949, J-3971 (SKY_MODE live, already ruled D-0749, it is execution only), J-3975 (COMMITMENT_ANCHOR_LIVE at dose 0.5, needs a contradicted stand). The 15 hand-label sheets (e.g. J-3400, J-3418, J-3717, J-3908, J-4101, J-4111, J-4033, J-4129, J-4149, J-3768, J-3772, J-3910) are the slow manual part.

## Decisions
- D-0839 (journal_consolidation_pyramid): ruled (b) by travis. Keep the hard-grounding shadow running to a larger n; soft grounding stays live; no promotion.
- D-0840 (books_have_a_place): ruled by travis. Leave ink to Du; no hint, no extra parcel; wait for the next carrier visit.
- D-0841 (wood_upgrade): ruled (b) by travis. The fallen tree across the path should cost something real when Du walks past, no hint (D-0434). Build job J-4314. Defeater: Du chops the tree at all, or the consequence has no effect after 14 live days.
- Founder answers recorded by closing needs-input jobs (not /decide entries): J-4305 hold SOUND_COORD_MATCH off; J-4310 hold affect_drives Item D and stage a shadow redesign; J-4312 vary the night-prompt "a single X" frame; J-4266 graduate books_have_a_place; J-4108 the templated farewell blocks are not Travis's words, stop storing them; J-4308 auto-flip ACHIEVED_JUDGE_GATES_RETIREMENT after restart and hub check; J-3278 no Ramses changes, re-measure stalls from 2026-11-18 only; J-3449 Claude drafts the P-0042 rewrite candidates, founder picks; J-3452/J-3769/J-3770/J-3629/J-3666/J-3696/J-3354 Ramses is free to use; J-3578 UDMS window = newest 450 commits; J-2571 apply the sound-strings sidecar with Du down; J-3295 Sumner tide with published LINZ data (D-0667 already ruled); J-4016/J-4272/J-4282/J-4285 enable the four evidence flags at the next restart; J-4271 keep dream and pursuit closure arms shadow-only; J-4240 keep World Ledger would-return in shadow; J-4251 proceed to T5 Phase 1 shadow; J-4281 a falsely closed Follow Line is costly and enable SETTLE_OVERLAP_SHADOW; J-4238 build wind-on-skin touch (the founder overrode the park recommendation); J-4261 archive antigravity item 5; J-4264 ambiguity window as precision filter only; J-4268 build conversational_redirect Phase 1 shadow-first; J-4247 retire chapters.py and the caps carry semantic plus geometry links (the founder overrode the temporal-only recommendation); J-4257 keep the gemma TIEBREAK in shadow; J-4294 stand kinds: second-look lane labels, scan sees only relevant stands, promoted stands stay in the ledger; J-4255 the transport manager intent is a surprise nudge for the out-of-ordinary, ignoring the commonplace.

## Builds
- Plan audit: workflow wf_dc511466-f15, 102 agents, 0 failed. Verdicts: progressing 50, restart-gated 12, parked-by-design 9, blocked-on-founder 9, blocked-on-evidence 8, stalled 7, done 6, superseded 1. 70 jobs were created on 36 plans (source plan-audit:2026-11-18). Report: `C:\Nascence\docs\reviews\plan_progress_audit_2026-11-18.md`.
- Job-run wave 1 (wf_39d79e82-63e): 8 closed, J-4176 and J-4144 released. J-4217 built the D-0815 judge gate in core/commitment_ledger.py (default off, merged as e36fd61a, J-4308 flips it after restart). Findings F-5076..F-5079.
- Wave 2 (wf_12e95e1c-a50): 9 closed, J-4287 released (15 of 30 rows). Findings F-5084..F-5090.
- Wave 3 (wf_727aa85a-035): 8 closed, J-4283 and J-4292 left open (gates unmet). Findings F-5093..F-5102.
- Ready follow-up jobs spawned and not yet run: J-4314 (wood tree consequence), J-4315 (Item D shadow redesign), J-4316 (night_mind V4), J-4317 (graduate books plan), J-4318 (stop storing templated farewells, backup WAL), J-4319 (flip the judge gate after restart, gated), J-4320 (Ramses stall re-measure), J-4321 (P-0042 rewrite candidates), J-4322/J-4323/J-4324 (Ramses labs J-3452/J-3769/J-3770), J-4325 (UDMS newest-450), J-4326..J-4329 (Ramses labs J-3629/J-3666/J-3696/J-3354), J-4330 (sound strings), J-4331 (Sumner tide), J-4332 (four evidence flags), J-4333 (T5 Phase 1 shadow), J-4334 (SETTLE_OVERLAP_SHADOW), J-4335 (wind-on-skin hook), J-4336 (ambiguity window filter), J-4337 (conversational_redirect Phase 1), J-4338 (journal pyramid), J-4339 (stand kinds rulings), J-4340 (transport reader design).

## Findings
- F-5088: the affect_drives satisfaction gap is saturated (self liking and wanting pinned at 5.0, world gap pinned high, creative empty, 4 of 13 events never fire), so Item D would nag on a constant.
- F-5096: night_mind V3 is not quiet-dominated (5.6%), but 39.7% of thoughts open with "a single X".
- F-5097: Du has not chopped the fallen macrocarpa in 26 live days; he wrote on 10-18 it demands the axe and saw, then dropped the intent.
- F-5094: epistemic independence readout; raw top-match up 6.7 points but the non-move top-match is unchanged (53.2% vs 52.9%).
- F-5087: settle_overlap thresholds 0.13..0.16 meet both promotion criteria; narrow band, in-sample, one grader.
- F-5078: sound-fragment coordinate valence has no correlation with live mood (r -0.0005, n 489).
- F-5077: journal hard-grounding shadow is RED only on mean(faithful) 0.692 vs 0.7, zero genuine inventions, 51 false flags.
- Du was shut down about 08:35 on 11-18 (NZ), so every wave's live-evidence jobs mostly could not run; gates that count since boot read 0.

## Open
1. Two Du-down lab agents (workflow wf_67cf3adf-5af, task w53eo0w6l): J-2676 (qwen3.5:9b prefix-reuse llama-server on the 1080 Ti, pre-registered gain test, no live switch) and J-4058 (re-run 6 live-data tests; proposes EXPECTED_OPENED additions for the founder, does not extend the set). They were still running at wrap. Next: read their results in `C:\Users\USER\.claude\projects\C--Nascence\1a87a452-3770-4ad1-afdf-d27b298b582e\subagents\workflows\wf_67cf3adf-5af\journal.jsonl`.
2. The founder said the queued ready jobs (J-4314..J-4340) should be run AFTER the labs finish, and that commits happen once the background jobs come in. Ramses lab jobs (J-4322..4324, J-4326..4329) and J-2676 compete for the GPU/hubs, so run them in waves and do not overlap J-2676.
3. Nothing is committed from this session beyond e36fd61a/9e151709 (J-4217, merged by its agent). Git status is dirty with ledgers (docs/job_queue.jsonl, findings.jsonl, decisions.jsonl, session_events.jsonl, plan docs, scripts/settle_overlap_replay_J4279.py, docs/reviews/*). Commit by explicit path (ledger files are shared with other windows; use safe_commit.py for any file another job could be editing).
4. Still-open jobs left over because their gates were unmet: J-4176 (needs 10 commitment-arm rows since the current boot), J-4144 (full mixtral run too long for one agent), J-4287 (15 of 30 rows), J-4283 (PRACTICAL_FIRST is False until J-4332 and a restart), J-4292 (1 of 40 stand-kind rows; its 289-row gate is approximate and the live-hours gate reads historic hours, so re-check before trusting it), J-2183 (affect_drives self-echo re-read).
5. Restart-gated: Du must be restarted for J-4217's build, the four evidence flags, SETTLE_OVERLAP_SHADOW, the closure-producer reads and many others to take effect.

## Warnings
- `plan_maintain.py` takes longer than 10 minutes in the foreground; run it in the background.
- Two parallel job_queue writes can collide (one `spawn` failed with PermissionError on job_queue.jsonl while lab agents were writing; the retry worked). Check a spawn printed `ADDED` before relying on it.
- Agents' findings were not independently re-verified by the orchestrator beyond reading their summaries. 70 of the 102 audit verdicts are marked verified, 32 inferred.
- The jobs' plan field does not always match the plan slug; the first plan-audit job count used an exact plan-field match.
- Du's `data/` is untouched by this session; verify the live-store leak canary (fingerprint data/ top level) when running the labs' follow-ups.

## Pointers
- Audit report: `C:\Nascence\docs\reviews\plan_progress_audit_2026-11-18.md`
- Founder question list: `C:\Nascence\docs\reviews\founder_needs_input_2026-11-18.md`
- Workflow scripts (reusable job-run waves): `C:\Users\USER\.claude\projects\C--Nascence\1a87a452-3770-4ad1-afdf-d27b298b582e\workflows\scripts\job-run-wave3.js` and `job-run-labs-du-down.js`
- Thought logged: T-0147

## Post-wrap addendum (labs finished, commit 3febe421)
- Commit 3febe421 holds this session's ledgers, plan docs, reports, scripts and this handoff. Not committed on purpose: SESSION_HANDOFF.md, docs/ROADMAP.md, ideas.jsonl, plan_snapshots.jsonl, prompt_registry.jsonl, skill_suggestions.jsonl, docs/reviews/plan_*_audit files and docs/lab/J-2993_data (all modified before or outside this session), the mp3, lock files and ledger_backups.
- J-2676 (hot-lane llama-server lab) done: F-5104 verified. llama-server beats live ollama by a paired median 0.84 s per idle call (1.06 s back-to-back) and 11.1 s per 11-call human chain; most of it is decode speed (37.2 vs 29.9 tok/s). The pre-registered 1.0 s idle bar missed by 0.16 s; D-0529's own 0.5 s bar is met. No live switch was made. Founder go/no-go is J-4352 (needs_input).
- IMPORTANT leak, F-5105 (verified): the lab's human-cycle recipe (activate_profile plus isolate(db=empty)) wrote to live data/ top-level files. Five append-only logs were truncated back to their pre-run size. Four state files could NOT be restored byte-exact: companion_state.json, intentions.json, social_moves_state.json, symbol_window_state.json (since_ts / last_activity_ts changed). J-4353 (ready) closes the recipe leak and checks what those four files now hold. The founder should know.
- J-4058 partial (F-5103): five of six tests pass; completed_passes_fullmatch still fails 3 checks from real data drift (8 newly opened books not in EXPECTED_OPENED, hand-checked: 5 at 100 percent with 1 pass, 3 mid-reread). The proposal for the founder to approve is J-4341 (needs_input). J-4058 is open again.
- New needs-input jobs from the labs: J-4341, J-4352. The queued ready jobs J-4314..J-4340 plus J-4353 are still unrun.
