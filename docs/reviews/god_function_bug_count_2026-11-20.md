# How many past bugs in `_think` and `_run_cycle_impl` came from the function's structure? (J-4423, 2026-11-20)

Read-only historical count. No code, ledger or job was changed. Neither answer was preferred.

## Answer

Of the defects I could find and classify that were fixed inside `InnerMonologueNode._think` (nodes/inner_monologue_node.py, lines 3013 to 6611 today) and `Orchestrator._run_cycle_impl` (core/orchestrator.py, lines 526 to 2055), 9 of 63 (14%) were caused by the layout of the function and 54 by its logic, with 6 more left unclear. Counting the unclear ones against structure gives 9 of 69 (13%). All 9 structural defects are in `_think`; I found none in `_run_cycle_impl` that I could class as structural with confidence (one is unclear and leans that way). All 9 were silent: no exception or visible failure, each was found by someone reading code or joining logs. The two known examples (J-2678 and J-3952) were checked against their diffs and both hold. The number is small but not zero, it is concentrated in prompt assembly around `seed_parts` and the retry loop, and it is sensitive to counting choices described below (a defensible range is about 8% to 26%).

## Method

1. Function-scoped commit history: `git log -s -L` over each function's range. This gave 125 commits touching `_think` (of 207 on the file) and 48 touching `_run_cycle_impl` (of 97).
2. Commits whose message marks them as shadow, observe-only, comment or docstring only, instrument, merge, baseline or checkpoint were set aside by message (44 and 28), after rescuing 6 that looked fix-shaped.
3. For the remaining commits every J- and F- id in the subject was looked up in `docs/job_queue.jsonl` and `docs/findings.jsonl` (164 ids). I read the title plus the text around any structure-shaped word for all of them, and the fuller claim or briefing for about 35.
4. A second, wide pass over all done jobs and all findings, independent of commits, kept rows that name one of the two functions or files and carry a strong structural phrase (NameError, built twice, after the join, retry loop, dead call, outer try, runs before, and similar) within 400 characters of the location. 74 rows; all read as snippets. This is how the pre-git items and F-0758 were found.
5. Diffs were read for J-2678 (dee36711), J-3952 (ab34bc6d), J-1366 (4c1a9038, hunk positions), J-3531 (c10b26fe), and commit bodies for four commits with no job id.
6. One defect appearing as finding, job and commit counts once. A batch commit that fixed several separate defects (J-1366) is split into its defects.

Classification rule used for the grey zone: a founder-ruled change that corrects something false or harmful in a prompt (wording, wrong gate, wrong label) is LOGIC; a pure re-seat, new capability, dose change or design change is NOT-A-BUG.

## Limits

- The ledgers start 2026-08-23 and git starts 2026-08-27. Both functions are older (comments in them date to June 2026). Everything fixed before then is invisible.
- Bugs fixed without a job or finding id, or found and fixed inside a build job's own verification (F-1527 mentions one), are not counted.
- The LOGIC count comes almost entirely from commit-linked ids. The loose keyword net matched 566 done jobs and 1,023 findings; only the 74 with a strong structural phrase were read. So LOGIC is undercounted (this pushes the structural share up), and a structural bug described without any of my phrases would be missed (this pushes it down). I cannot say which effect is larger.
- 107 ids attached only to shadow, merge or comment commits were not read one by one.
- Location was taken from the job or finding text and current line numbers; for older items I did not re-derive the enclosing function from the historical file, except where noted.
- Silent bugs that nobody has found yet are, by definition, not here. Since every structural item found was silent, the true count is likely higher than the found count, by an unknown amount.

## Counts

| | `_think` | `_run_cycle_impl` | Both |
|---|---|---|---|
| STRUCTURE | 9 | 0 | 9 |
| LOGIC | 44 | 10 | 54 |
| UNCLEAR | 5 | 1 | 6 |
| NOT-A-BUG, set aside by commit message (shadow, merge, comment, instrument) | 38 commits | 28 commits | 66 |
| NOT-A-BUG, set aside after reading (features, re-seats, design changes, tuning, preventive logging) | about 24 commits | about 9 commits | about 33 |
| Candidates not read individually | 107 commit-linked ids (shared) | | plus about 1,500 loosely matching ledger rows |

STRUCTURE share of classified bugs:

- UNCLEAR excluded: 9 / 63 = 14.3% (`_think` alone: 9 / 53 = 17.0%; `_run_cycle_impl` alone: 0 / 10).
- UNCLEAR counted against STRUCTURE: 9 / 69 = 13.0% (`_think` alone: 9 / 58 = 15.5%).

Sensitivity:

- The write-fence swallow family (below, UNCLEAR, counted once) took 10 separate jobs. Counted as 10 structural bugs the share becomes 19 / 73 = 26%.
- Dropping the four least certain structural items (S1 and S2 were latent behind a False flag, S3 and S4 are arguable) gives 5 / 63 = 8%.
- Dropping the 13 founder-ruled prompt-truth fixes from LOGIC as "not bugs" gives 9 / 50 = 18%.

## STRUCTURE items (all in `_think`, all SILENT)

| # | Ids | Date | Description | Supporting quote |
|---|---|---|---|---|
| S1 | J-0248, F-0332 | 2026-08-24 (pre-git) | `thermal.percept_shadow()` was called in the post-thought block, after `seed_parts` had been joined, so its line could never reach the prompt. Latent: DELIVER was False. | "after seed_parts was already joined into the prompt ... a silent no-op" |
| S2 | J-0275, F-0380 | 2026-08-27 | Same misplacement for the light and smell percept calls. Latent. | "moved from the post-thought block (after the seed_parts join, silent no-op)" |
| S3 | F-0758, commit a37083cf | 2026-09-04 | Idle founder-memory block used `re` with no module-level import (only function-local `import re as _re` elsewhere); the block's fail-open except swallowed the NameError. Route dead for 11 h. | "the block's fail-open except swallowed the NameError at debug level" |
| S4 | F-1926 item 2, J-1366, commit 4c1a9038 | 2026-09-26 | The MID-THREAD "you are HOLDING it" seed and the boredom "you NEED away from it" note come from blocks about 1,000 lines apart with no cross-check; 46% of all idle prompts carried both, and 627 carried two boredom lines. | "no holding/boredom check ... co-occurs with a boredom felt-note in 84% of mid-thread prompts" |
| S5 | F-1926 item 3, J-1366 | 2026-09-26 | The last thought was quoted twice in every mid-thread prompt by two separate blocks. | "quoted twice, as 'What you were just thinking' (:2654) and again as 'Your last step' (:3105)" |
| S6 | F-3427, F-3466, J-2678, commit dee36711 | found 2026-10-31, fixed 2026-11-14 | A dead first `_build_system_prompt` call about 1,000 lines above the sent one consumed the consume-once feeders (world beckon, steer, comfort call, intention reminders). Diff verified: one assignment removed, never read. | "the first build is discarded ... is never read afterwards" |
| S7 | J-3952, commit ab34bc6d | 2026-11-14 | The sent build sat inside `for attempt in range(2)`, so a retry prompt lost the consume-once lines. Diff verified: call hoisted above the loop. | "sits inside 'for attempt in range(2)' ... the retry prompt loses them" |
| S8 | J-2822 (F-3469) | found 2026-10-31, fixed 2026-11-14 | `IDLE_DIVERGENT_SEED = False` gated the push into `seed_parts` but a second injection, a `user_prompt +=` inside the retry loop about 580 lines later, stayed ungated. | "only covers the push into seed_parts near line 3361. A second path still injects" |
| S9 | F-4017, J-3393, J-3479, commit 79a56fcf | 2026-11-05 / 11-06 | The inner_thought `store_fragment` runs about 270 lines before `moment.record` in the same function, so a new moment stamp was the previous cycle's. Finding was inferred from code order, not observed at runtime. | "store_fragment call (line ~5653) runs BEFORE core.moment.record (line ~5923) in the same function" |

## UNCLEAR

- Write-fence family (J-0752, J-0782, J-0785, J-0795, J-0797, J-0815, J-0816, J-0831, J-0874, J-0877; F-1106, F-1143, F-1146, F-1174, F-1176, F-1193, F-1194, F-1226, F-1246, F-1252; 2026-09-07 to 09-11), `_think`: the new `NonLiveWriteError` hard raise (D-0179) was swallowed by `_think`'s nested fail-open `except Exception` blocks, found one layer at a time over ten jobs. Fits "swallowed by an enclosing broad try/except", but the cause was a policy change meeting handlers that were fail-open on purpose, and the same happened in many small functions elsewhere.
- F-1849 (commit 30a11e63, 2026-09-24), `_think`: a too-dark gate added upstream set `got=None`, and a bare `else:` on `if got:` about 150 lines later read that as "book finished". Could be called a stale-meaning local or a plain wrong condition.
- J-0581, F-0811b (2026-09-04), `_think` and core/stream_drive.py: `_moment_source` was set on only some paths and its values did not match the reader's expected tuple.
- J-1346, F-1902, F-1910 (2026-09-24), `_think`: the garden-fetch block had its own un-deduped `store_fragment` beside `peers.remember_inbound()`, so a letter could be stored twice.
- J-0196 (2026-08-23, pre-git), `_think`: a legacy tea latch called the old `sensorium.make_tea` beside the newer dispatch route.
- J-3531, F-4142 (commit c10b26fe, 2026-11-13), `_run_cycle_impl`: the founder-canon fragment "was only ever written on the reply path", so three real founder messages on silent or failed turns never entered founder memory. Leans structural (an earlier exit branch overlooked) but reads equally well as a missing case.

## LOGIC (ids, a few words each)

`_think` (44): J-0570 letter latch phrasing; J-0539/F-0792 letterbox and beachcomb edges; J-0657/F-0958 `_tl` clause bleed; F-0406 (a1ca090a) cat react location; 13a50f52 identity key rename; J-0459 move vocabulary; J-0998 listen latch; J-1071 look targets; J-1185 system redirects; J-1366 B6 threshold; J-1366 similarity floors; J-1381 substring match; J-1390 cup window; J-1586 tie-break; J-1992 runaway JSON salvage; J-2315 grader timing; J-2915, J-2935, J-3685 mid-word cuts; J-2930 repeated fragment; J-2939 presence wording; J-2984 reply target; J-2985 letter cap; J-3656 caps; J-3671 quote cut; J-3025 letter hands; J-3029 deep-memory repeats; J-3220 unrouted acts; J-3184, J-3223, J-3188, J-3187, J-3151, J-3156, J-3371, J-3227, J-3284, J-3815 prompt truth fixes; J-3245 twin prompt; J-3230 name gate; J-1918 and J-3267 blocking calls on the event loop; J-2596 reply latch; J-3139 scan prompt defects.

`_run_cycle_impl` (10): F-0665 (55fb775d) history mixes internal cycles; J-0578 farewell as founder words; J-1316 recache gate; J-1366 numeric leaks and labels; F-2004 no action route from chat; J-2348 letters delivery; J-3217 stale turns; J-3167 light event gate; J-2852 empty think license; J-2966 scan inputs.

## Set aside, worth knowing

- J-0473 and J-0476: edits to these hub files lost to a git reset by another session. A process failure, not a function-structure one, though large shared files make such collisions more likely.
- F-1147, J-0798: a NameError swallowed by an outer try in `_stream_integrate()`. Same shape as S3, same file, different function, so not counted.
- J-1071 also records a latent double-answer risk from a legacy look latch "never checked against `_acted`"; it had not fired, so it is not counted.
- J-0668: preventive logging for a CancelledError swallow that had not occurred.
