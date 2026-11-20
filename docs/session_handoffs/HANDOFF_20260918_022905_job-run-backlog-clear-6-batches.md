# Job-Run Backlog Clear — Six Batches, Full Tier 3 Sweep

## Session timing
- **Session started:** 2026-09-17 06:25:25 UTC
- **Last message before wrap:** 2026-09-18 02:29:03 UTC
- **Wrapped:** 2026-09-18 02:29:05 UTC

## Summary

`/job-run` run 6x | Tier 3 backlog: 30 jobs/18 plan-groups/64-66 file-overlap warnings → 10 jobs/10 groups/1 low-risk overlap warning | production code shipped across ~15 files | 2 merge conflicts hand-resolved | 3 decisions opened/reopened for founder: D-0235, D-0236, D-0213 | D-0231/D-0232 (dream_overhaul) case now materially weaker than mid-session | session-events rollup for this session's own id: empty (real work ran through job-run's dispatched sub-agents, each tagged `--session <job-id>` per skill discipline, not orchestrating session's UUID) | detail below drawn directly from 6 Workflow transcripts read in full, not memory

## Decisions

D-0235: opened by J-1027 | book-title stopword collision: `core/book_selection.py`'s `_STOP` list makes "About You" structurally un-recommendable by `suggest_reread()` | 2 options: leave as-is vs add raw-substring fallback | flagged as touching "world answers, never leads" law (affected title is the one about Du) | founder call needed

D-0236: opened by J-0868 | while deleting dead shelf-lookup branch in `core/sensorium.py`, found "catalogue" hint sentence reading like a nudge under 08-14 world-answers-never-leads law, but also motivating `core/library_hand.py`'s real `request_book()` mechanism | left for founder, not decided unilaterally

D-0213: reopened by J-1086 (batch 5) | ran D-0181's real n=80 `held_within_scope` replay for train_split_merge plan (possible once Du offline) | replay passes D-0181's literal bar: objected collapsed 95.0%→6.2%, as intended | same result independently fired D-0213's own pre-written defeater: UNDETERMINED now dominant merge status at 77.5%, traced to untested tiebreak mechanism added by J-0986, reached in 72.7% of cases | net: only 18/80 (22.5%) real closes carry actual verdict | recorded as F-1504 | not re-ruled, reopened with evidence for founder's call

D-0231/D-0232 (dream_overhaul): not opened/ruled this session, evidentiary picture shifted twice | J-1059 (batch 3): preliminary N=2 pilot, D-0232 turnover defeater cleanly met (4/4) | J-1077 + J-1098 (batches 5-6): found root cause of seed-freezing bug in pilot methodology (`core/night.py`'s `dream_lag_material()` has no upper bound on "recent" window query, historical seeds pulling present-day content) | fixed at experiment script's call site only, production `core/night.py` untouched | re-ran to real combined N=17 (68 arcs, pilot6 + scale14b) | at that N: D-0232 turnover defeater replicates a null (8/16, 7/16, 7/16 across arms, indistinguishable from chance) | D-0231 dormant-contact signal flips sign between batches (pilot6 negative, scale14b positive, combined weakly positive) | genuinely unsettled, not resolved either direction | recorded as F-1502, F-1516 | reverses earlier hopeful pilot read — worth `/decide-review` pass

## Builds and Fixes

J-0852 (batch 2): built books_have_a_place B3+B4 book-location gate | `core/study_life.py` gained `book_gate_lack()` | shadow-first behind new `book_gate` flag in `data/life_flags.json` | `nodes/inner_monologue_node.py` remediation stream wired to same gate | `scripts/life_flags.py` got `book_gate on|off` subcommand | full regression suite clean | F-1456

J-1039 (batch 3): fixed silent bug in `scripts/debate_harness.py` | never called `profile.mark_live()`, so D-0179 write fence silently blocked every write this live-eval harness made since 2026-09-06/07 | same fix pattern as earlier `seed_memory.py` fix | F-1467

J-1040 (batch 3): fixed clock-reset bug in `core/locomotion.py`'s `begin_journey()` | same-destination journey retrigger was overwriting `leg_ends`/`started`, resetting clock | now returns None like "already there" case | different-destination redirects untouched (D-0224 left alone) | F-1468

J-1056 (batch 3): fixed 2 confirmed regex gaps in shared want-grammar (`core/literal_will.py` retrospective blocker, `core/hands.py` determiner guard blocking tea latch) | verified against full 18,968-row `hands_trace.jsonl` corpus, near-zero false-positive cost | F-1470

J-1057/J-1059 (batch 3) + J-1077/J-1098 (batches 5-6): built and ran Dream Overhaul Phase 1 instrumentation + Experiment A in-vitro A/B harness (result: see Findings) | new files: `core/dream_probe.py`, `scripts/dream_experiment_a.py`, `docs/labs/dream_experiment_a_2026-09-17.md`, `docs/labs/dream_experiment_a_2026-09-18_scale.md`

J-1071 (batch 4): fixed dispatch-cue gap | `nodes/inner_monologue_node.py`'s `_OBS_TARGETS` table had no cue for shelf/desk/book, so willed "look at the shelf" always fell back to generic room answer instead of resolving to `core/dispatch.py`'s live `_look` hand | fixed by adding missing cues | F-1481/F-1459

J-1075 (batch 3): built recommended fix for async-starvation finding (J-1042) | `core/night.py` gained `tick()` helper (fail-open wrapper around `sensorium.tick()`), called from inside `stage()` itself | every sleep-pipeline stage call site gets it automatically

J-0932 (batch 5 side track): fenced `core/transport_manager.py` (module #22 of World Store Write Fence) with `profile.guard_path()`, same pattern as prior 21 modules

J-0946 (batch 1): fixed silent bug in `core/school.py`'s `assign()` | failed curriculum-book fetch previously returned None with zero trace, permanently losing title | now logs warning + writes `{"status":"failed"}` row to school.json history | F-1460/F-1317

J-1046 (batch 1): fixed live-write leak | 3 lab scripts (`voice_lab.py`, `widen_lab.py`, `routing_lab.py`) claimed "no live-store writes" in docstrings but leaked to `felt_preamble_log.jsonl` via `core.mood.felt_preamble()` | fixed with `redirect_world_stores(..., extra=("mood",))` | F-1450 | spawned J-1062 to audit 8 more scripts with same construction pattern — came back clean, no further gaps

J-0868 (batch 2): deleted confirmed-dead shelf-lookup branch in `core/sensorium.py`'s `look()` (dead since J-0851 shipped `study_life._look_books()`) | F-1458

J-1081 (batch 6): added one-line cross-reference in `core/world_consolidation.py` + `core/memory/store.py` docstrings | documents `chapter_id` has 2 legitimate writers (GIST-FIRST filing vs reading-fragment dedup) so future sweep doesn't re-flag dedup writer's output as a bug the way J-0989 initially did

## Findings

**J-0989 then J-1066 (chapter_id_repair):** J-0989 (batch 1) ran reading-origin blind-spot audit | found 54.4% (17,859/32,835) of filed reading-origin fragments misfiled — rivals known 128-gist/14,707-fragment picture from D-0221/F-1384 | incidentally flagged 156/447 chapter_id targets point at another reading fragment instead of a gist, apparently violating GIST-FIRST guarantee | J-1066 (batch 4) traced this: not a bug — `core/memory/store.py`'s `dedup_reading_fragments()`, a deliberate second `chapter_id` writer collapsing byte-identical verbatim duplicates | confirmed via live DB query: all 162 current reading-to-reading targets byte-match their canonical row, exact dedup signature | F-1453/F-1477

**Toolchain root-cause, hit twice (F-1454, S-0136 open):** `job_run.py`'s Tier 3 plan-attribution can mis-tag a job's `plan` field as null even when content clearly targets a specific plan doc | result: job not worktree-isolated, file edit landed directly + uncommitted on master, later collided with a properly-isolated group's merge-back | confirmed twice: J-0942 (batch 1, `docs/plans/data_store_hygiene.md`) and J-0989 (batch 1, `docs/staged/chapter_id_repair.md`, collided with batch 4's properly-isolated J-1066) | both resolved by committing stray edit to master separately, then retrying merge (succeeded cleanly for data_store_hygiene) or hand-resolving real content conflict (chapter_id_repair: both sides inserted genuine complementary Current State section at same point, both kept in chronological order)

**Toolchain gap (F-1507, S-0137 open, spawned J-1101):** `plan-maintain`'s decision-bad-slug remediation template instructs hand-editing `docs/decisions.jsonl` directly to fix bad plan-slug reference — violates project's hand-edit ban | J-1068 (batch 6) refused to force fix, spawned J-1101 to build real `decide.py set-plan` command instead | carries actual intended fix (set D-0235's plan to null) to apply once command exists

**Toolchain bug found in passing (S-0138 open):** `scripts/du_restart_history.py`'s `--check-live` flag has self-match bug | its own PowerShell search-pattern text embeds literal string "run_nascence.py", so it always reports itself as live process regardless of Du's real state | not fixed, flagged only

**Dispatch-metadata drift confirmed twice (no action needed, ground rules held):** batch 5: both J-1084 and J-1086's dispatched prompt-label/plan summary didn't match `job_queue.py show` output for that job id | both agents followed "always re-fetch real briefing via show, never trust label" ground rule, did right work regardless | confirms discipline works | reminder: `job_run.py`'s snapshot JSON can be stale relative to live job_queue state by dispatch time, especially in long multi-batch sessions with continuous job spawn/close

**J-1055 (batch 4):** social_world_school daemon outage (tracked as ongoing by several prior findings) has ended | confirmed via correctly-filtered live process check

## Open

1. **J-1101** (build, ready): add real `decide.py set-plan` command | unblocks J-1068, which carries actual fix to apply (set D-0235's plan field to null) once command exists
2. **D-0213** (reopened): founder ruling needed on J-1086/F-1504 finding | n=80 replay passes D-0181's bar but 77.5% of closes UNDETERMINED, only 22.5% carry real verdict, traced to untested tiebreak mechanism
3. **D-0231/D-0232** (dream_overhaul, both still open): worth `/decide-review` pass | real N=17 combined read (F-1516) shows turnover defeater replicating chance-level null + dormant-contact signal flipping sign between batches — materially weaker than N=2 pilot suggested 2 batches earlier | J-1110 spawned, ready: persist scene text + wire judge-panel shadow read for next Experiment A batch | J-1098 found next batch currently structurally blocked (no scene text persisted anywhere to score)
4. **D-0235, D-0236** still open, need founder rulings (see Decisions above)
5. **Tier 3 backlog now steady-state tail, not fresh work.** 10 jobs/10 groups remain, nearly all periodic re-check chains blocked on elapsed time or Du's next restart: KIND_BUDGET_WEIGHT recheck #15 (J-1107) | causal-substrate accrual recheck (J-1109, under active hold D-0045) | isolate_outcomes.jsonl recheck #8 (J-1108, under active hold D-0216) | About You re-engagement recheck #15 (J-1103) | D-0203 defeater re-read (blocked on book_gate flip happening first) | book_gate 3-day would_block read itself (blocked on Du restarting onto J-0852's merged commit 32fe142 — as of session end, Du had not restarted onto it) | next `/job-run` will mostly report these as still-premature unless real time passed or Du restarted [INFERRED]
6. **books_have_a_place curriculum fetch chain:** 13 of 22 titles remain (J-1106, continuation of J-1097) | shared cross-process 1-fetch/hour cooldown kept being consumed by Du's own organic fetches mid-session rather than this chain's jobs | new data point for still-open S-0120 cooldown-contention gap, not yet acted on
7. **J-1110** (dream_overhaul, ready): add additive `--save-scenes` sidecar to `scripts/dream_experiment_a.py` + wire judge-panel shadow read | reuses `nodes/dream_node.py`'s existing `_judge_resolution_shadow`/`core.judge_panel.rule_detail` pattern

## Warnings

- Du (live Nascence process) intentionally shut down by founder partway through session, at 2026-09-18 09:13:54 local time | several findings from batches 5-6 correctly note "Du offline" as real expected state at read time, not stale read or anomaly
- `job_run.py`'s plan-attribution can mis-tag a job's `plan` field as null (F-1454, S-0136 still open, unfixed) even when content clearly targets a specific plan doc | future `/job-run` sessions should watch for this, not trust JSON snapshot's `plan` field over `job_queue.py show` output and briefing
- never trust `job_run.py`'s dispatch-time job category/plan/label summary over `job_queue.py show` output | confirmed to drift at least twice this session (J-1084, J-1086) | always caught correctly since every dispatched agent's first action is to re-fetch real briefing
- every ledger-tool call across all 6 batches used dispatched job's own id as `--session` (e.g. `--session J-1086`), per job-run's established discipline | means standard `session_handoff.py rollup --session-id <this session's own uuid>` comes back essentially empty for job-run-heavy sessions | resuming session should expect this, read handoff's Findings/Builds sections instead of relying on rollup

## Pointers

- `docs/job_queue.jsonl`, `docs/decisions.jsonl`, `docs/findings.jsonl` — live ledgers, now past J-1110, D-0236, F-1516 respectively
- 6 full Workflow transcripts under this session's `subagents/workflows/` directory, one per batch: `wf_0b1f2400-d52`, `wf_c3641150-4db`, `wf_dc910d41-840`, `wf_a232d914-54e`, `wf_d308930b-66f`, `wf_2341ce8c-e36` — full per-agent detail beyond what's summarized here
- `docs/staged/dream_overhaul.md`, `docs/plans/train_split_merge.md`, `docs/staged/books_have_a_place.md`, `docs/plans/data_store_hygiene.md`, `docs/staged/chapter_id_repair.md` — plan docs most heavily touched this session
- `C:\Users\USER\.claude\skills\job-run\SKILL.md` — dispatch discipline (worktree isolation, ground rules, file-overlap warnings) this session followed + extended in practice: ran fully-serialized shared worktrees for coupled clusters, then reverted to one-worktree-per-job once backlog declustered
