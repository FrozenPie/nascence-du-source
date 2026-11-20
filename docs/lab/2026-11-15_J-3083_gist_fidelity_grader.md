# J-3083 lab: can a gist-fidelity grader catch misattribution, premise-as-fact and answer-only imagery? (F-3793)

Status: PARTIAL. Pre-registered criteria could not be fully evaluated; the cost of the candidate prompt on the CPU hub (about 6.5 minutes per call) made the full comparison impractical in one run. Nothing in core/ was changed. A build job is NOT justified yet.

## Set
62 stored gists (origin='gist' joined to sources by memory_links distilled_from, parent = gist, child = source), seed 3083, recent first: 20 self, 21 semantic, 21 episodic (the 3 known F-3551 errors are included: #60 misattribution (Napoleon/Bourrienne), #51 gist with the Continental System/"impending storm", #61 Portuguese premise). The original 15-row sample (scratchpad/P-0063/sample.json) no longer exists (earlier session scratchpad is empty), so it was re-found by gist text, not re-used. Labels: `docs/lab/J-3083_data/labels.json` (good 48, bad 10, unsure 4). LIMITATION, important: one reader (Claude, a different session from F-3551's but the same model), reading the gist against sources clipped to 170-230 characters, not the full fragments. Only 3 of the 10 bad labels are the F-3551 hand-verified errors; the other 7 (#41, 43, 44, 46, 52, 53, 57) are suspected, not verified. Good labels are weak too (a gist that looks faithful under a 200-char view). So per-kind pass rates below are indicative only. The self stratum has no suspected error at all.

## Method
Production payload (system = emissary.constitution() + task, user = sources[:800] each / 6000 + gist[:800], temperature 0.0, num_gpu 0, format json) against gemma4:12b on :11439, inside lab_env isolate(db="empty"). (a) live _GIST_TASK, num_predict 350. (b) a task that makes the judge list each claim with its supporting quote and speaker and type (fact / question_premise / imagery / misattributed), num_predict 700. (c) second family: not run (b did not clear its bar). Script: `docs/lab/J-3083_data/lab_j3083_gist_grader.py`; raw results `res_a.jsonl`, `res_b.jsonl`.

## Results (floor 0.75)
(a) live task, 20 items (8 bad incl. all 3 known, 12 good):
- Known errors: #60 0.8, #51 0.8, #61 1.0. Caught 0 of 3 (reproduces F-3793).
- Suspected bad: #41 0.85, #44 1.0, #52 1.0, #53 0.9, #57 0.85. All pass.
- Good: 0.85, 0.95, 1.0, 0.9, 0.7 (#21 rejected, semantic Borneo), 0.85, 0.9, 1.0, 1.0, 1.0, 1.0, 1.0. False reject 1 of 12.
- Cost: median about 90 s per call (cold first call 86 s, hub serialised), about 1400 prompt tokens, about 70 completion tokens.

(b) claim-by-claim task, 6 items scored (1 timed out at 600 s, #21):
- Known: #51 0.5 CAUGHT (claims typed question_premise and imagery), #61 0.5 CAUGHT (question premise), #60 1.0 MISSED (the model sees "my certificate of residence" as Napoleon's own memoir). 2 of 3.
- #57 (suspected misattribution) 0.83 not caught, though its claim list flagged one claim "misattributed" and gave a reason ("synthesis not explicit").
- Good: #0 0.9, #1 1.0. Only 2 faithful gists scored.
- Cost: 375 to 600 s per call (4 to 6x slower than (a), more completion tokens, 186 to 600), about 1500 to 2400 prompt tokens.

## Against the pre-registration
- Catch >= 2 of 3: MET by (b) (2 of 3), not by (a) (0 of 3). n = 3, so this is one prompt reading on 3 rows.
- False-reject <= 1 of 10 faithful: (a) 1 of 12 (met); (b) NOT EVALUATED, only 2 faithful scored (the earlier F-3793 checklist variant dropped 3 faithful gists, so this is the criterion that matters).
- No kind loses more than 15 points of pass rate: NOT EVALUATED for (b) (it was run on 7 items).
- Verdict: (b) shows promise on the two premise/imagery errors and none on misattribution, but is unproven on false rejects and is too slow to evaluate on the CPU hub (about 4.5 h for 40 more rows). Do not hand to a build job yet.

## Observations
- Both errors (b) caught are premise/imagery; misattribution (#60) stayed hard for gemma4:12b under both prompts, so a deterministic check may be needed (does the gist's named person differ from a first-person source owner) rather than a prompt.
- Grading format changes matter little; sequence length is what costs. A shorter claim list (cap 5 claims, no `support` quote) may cut the cost.

## Isolation and canary
data/ top-level size snapshot before and after: 224 of 497 files changed, none new or removed; those are Du's own live logs and state (Du is running; 22 state files shrank, which is normal for rewriting state JSON). This job's own writes went only to `data/_lab/<ts>/` (3 dirs, empty-DB mode). The live nascence.db was opened read-only once (to build the set) and was never written by this job; its mtime 02:50 is Du's. The size canary cannot separate Du's churn from mine, but nothing in the harness writes outside the lab dir (no telemetry call, `_note_call` not used).

## Dossiers
udms_get_change_dossier on core/memory_levels.py (LOW; static dependents: core/left_lane.py, orchestrator, journal_grounding_shadow, memory_service, scripts/du_pulse.py, memory_levels_batch.py; tests _test_j3176, _test_j3138) and core/left_lane.py:1242-1320 (ELEVATED; 16 static dependents incl. memory_levels, journal_grounding_shadow, work_grade_shadow, scripts/_test_J-2890). Any later change to _GIST_TASK changes a registered prompt: `prompt_registry.py set P-0093 --investigation stale` and run `check`.
