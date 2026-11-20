# prompt_manager P0: vocabulary-by-week re-run and change ledger (generated)

Generated 2026-11-14 14:45 by `scripts/prompt_manager_p0_baseline.py`. Source: `data/monologue_log.jsonl` (88,925 thoughts with text; weeks are 7-day bins from 2026-08-15). Read-only.

**Reconstruction caveat:** F-1927's original regex scripts were scratchpad-only and are lost. Families below are a reconstruction. Calibration against F-1927's published weeks 1-2 is in the last column; a large mismatch means the family definition differs, not that the underlying rate changed. Absolute levels are comparable *within this table*, not exactly to F-1927.

| week of | n | frustration/heaviness | circling/loop/dead-ground | restless | anchor | shadow/avoid | wrong/not-true | ctl tide | ctl cat | ctl book | ctl rain/wind | opener3 reuse | opener4 reuse |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-08-15 | 3,671 | 5.8 | 5.1 | 1.8 | 5.6 | 1.4 | 0.1 | 18.6 | 3.2 | 2.0 | 7.6 | 41% | 22% |
| 2026-08-22 | 2,276 | 17.2 | 18.4 | 5.6 | 17.8 | 4.7 | 0.3 | 7.8 | 12.0 | 11.3 | 28.7 | 43% | 23% |
| 2026-08-29 | 5,527 | 20.5 | 23.3 | 7.5 | 20.5 | 2.3 | 0.3 | 18.0 | 13.2 | 11.9 | 19.9 | 48% | 28% |
| 2026-09-05 | 7,452 | 27.3 | 26.7 | 8.6 | 24.1 | 2.3 | 0.2 | 21.5 | 9.7 | 14.3 | 15.0 | 52% | 30% |
| 2026-09-12 | 3,411 | 32.5 | 25.5 | 8.9 | 24.4 | 1.3 | 0.4 | 24.2 | 9.3 | 12.0 | 16.4 | 50% | 29% |
| 2026-09-19 | 4,135 | 27.8 | 23.0 | 8.8 | 23.5 | 1.6 | 0.3 | 18.3 | 10.6 | 14.2 | 15.4 | 45% | 24% |
| 2026-09-26 | 4,286 | 17.4 | 18.3 | 4.9 | 25.8 | 2.4 | 0.3 | 18.8 | 13.4 | 14.0 | 17.7 | 51% | 27% |
| 2026-10-03 | 3,351 | 17.5 | 1.0 | 1.7 | 30.1 | 3.4 | 0.1 | 13.2 | 17.0 | 13.2 | 20.8 | 45% | 24% |
| 2026-10-10 | 9,847 | 13.6 | 1.0 | 0.7 | 26.5 | 2.3 | 0.0 | 10.2 | 17.4 | 15.8 | 27.7 | 57% | 32% |
| 2026-10-17 | 3,711 | 12.9 | 1.2 | 1.2 | 24.9 | 2.0 | 0.1 | 12.5 | 17.2 | 12.2 | 31.7 | 58% | 34% |
| 2026-10-24 | 1,702 | 17.6 | 1.5 | 1.0 | 22.6 | 6.2 | 0.0 | 13.2 | 9.6 | 15.6 | 8.8 | 46% | 22% |
| 2026-10-31 | 6,990 | 17.1 | 1.7 | 1.3 | 26.9 | 9.3 | 0.1 | 18.7 | 15.3 | 20.7 | 12.6 | 50% | 26% |
| 2026-11-07 | 6,046 | 13.8 | 2.5 | 0.4 | 7.6 | 6.2 | 0.2 | 12.6 | 14.3 | 7.6 | 27.7 | 55% | 29% |
| 2026-11-14 | 896 | 13.7 | 3.7 | 0.9 | 4.7 | 7.3 | 0.2 | 12.9 | 15.8 | 14.2 | 18.0 | 54% | 27% |

**Calibration vs F-1927 (weeks 1-2):**
- frustration/heaviness: this run w1 5.8 / w2 17.2; F-1927 published 5.6 / 17.9
- circling/loop/dead-ground: this run w1 5.1 / w2 18.4; F-1927 published 6.1 / 20.9
- restless: this run w1 1.8 / w2 5.6; F-1927 published 1.8 / 5.7
- anchor: this run w1 5.6 / w2 17.8; F-1927 published 5.9 / 18.3
- shadow/avoid: this run w1 1.4 / w2 4.7; F-1927 published 2.2 / 4.9
- wrong/not-true: this run w1 0.1 / w2 0.3; F-1927 published 0.1 / 0.4
- ctl tide: this run w1 18.6 / w2 7.8; F-1927 published 19.0 / 8.0

D-0368 thresholds (per family, not blended): frustration and circling each under 15%; same-day opener reuse under 30%. A+E live since the 2026-10-09 08:36:57 boot (first `steer_edge_log.jsonl` row 2026-10-09 10:27).

## Change ledger (restarts and prompt/steer/lane commits since 2026-08-15)

### Restarts (a change merged to the tree is not live until the next one)

2026-08-15 11:39:56, 2026-08-15 18:56:14, 2026-08-15 19:43:09, 2026-08-15 20:25:06, 2026-08-16 09:15:11, 2026-08-17 00:13:29, 2026-08-18 00:15:09, 2026-08-18 22:43:51, 2026-08-19 09:40:50, 2026-08-19 19:58:01, 2026-08-20 09:58:27, 2026-08-20 10:25:50, 2026-08-20 15:32:07, 2026-08-20 19:21:00, 2026-08-20 20:01:48, 2026-08-20 20:49:48, 2026-08-21 08:34:16, 2026-08-21 11:17:32, 2026-08-21 13:37:21, 2026-08-21 21:46:00, 2026-08-22 11:25:03, 2026-08-22 13:57:19, 2026-08-22 15:55:51, 2026-08-22 17:26:52, 2026-08-22 22:54:49, 2026-08-23 08:07:33, 2026-08-23 11:03:48, 2026-08-24 02:07:00, 2026-08-24 21:41:54, 2026-08-24 22:16:09, 2026-08-25 08:43:48, 2026-08-25 11:53:17, 2026-08-25 19:39:37, 2026-08-27 20:34:59, 2026-08-28 09:23:15, 2026-08-28 10:11:54, 2026-08-28 17:54:07, 2026-08-29 10:42:58, 2026-08-29 17:25:06, 2026-08-30 01:14:46, 2026-08-30 09:14:12, 2026-08-30 17:15:01, 2026-09-02 08:48:54, 2026-09-02 15:44:16, 2026-09-03 08:19:18, 2026-09-03 09:07:49, 2026-09-03 18:39:13, 2026-09-03 20:03:46, 2026-09-04 11:37:21, 2026-09-04 12:53:50, 2026-09-04 23:10:16, 2026-09-04 23:34:47, 2026-09-05 11:37:26, 2026-09-05 14:39:58, 2026-09-05 18:14:35, 2026-09-05 19:15:24, 2026-09-08 16:41:59, 2026-09-09 13:25:14, 2026-09-09 15:22:15, 2026-09-09 19:01:08, 2026-09-11 13:50:42, 2026-09-16 07:53:01, 2026-09-18 23:14:19, 2026-09-18 23:37:27, 2026-09-21 09:29:45, 2026-09-22 16:11:04, 2026-09-25 19:21:50, 2026-09-28 19:08:44, 2026-09-28 22:01:25, 2026-09-29 12:36:49, 2026-09-30 20:28:49, 2026-10-03 06:55:10, 2026-10-03 23:25:34, 2026-10-04 20:40:29, 2026-10-06 01:11:50, 2026-10-07 12:33:26, 2026-10-08 09:03:08, 2026-10-09 08:36:57, 2026-10-16 22:37:20, 2026-10-18 19:06:22, 2026-10-18 19:37:09, 2026-10-19 08:50:11, 2026-10-19 10:05:17, 2026-10-19 22:09:40, 2026-10-29 18:38:21, 2026-10-31 11:43:18, 2026-10-31 21:56:58, 2026-11-02 13:17:25, 2026-11-07 20:33:40, 2026-11-08 10:51:28, 2026-11-12 22:29:00, 2026-11-13 23:21:32, 2026-11-14 14:15:26

### Commits touching the idle prompt, steers, prompt budget, condensed twin

| committed | hash | subject |
|---|---|---|
| 2026-11-14 13:55 | 4cc4f980 | Layered goals Phase 5 detection (shadow), stalled flag, rest honoured on the seed path |
| 2026-11-14 13:47 | cd70eb9f | Layered goals Phase 6 (first part): optional set_down field and its judge |
| 2026-11-14 13:23 | 093a65c6 | ﻿Layered goals Phases 2 and 4: aim off the lead, goal offers at 25% of idle anchors |
| 2026-11-14 04:21 | ab34bc6d | J-3952: build idle-thought system prompt once before the retry loop so retries keep consume-once feeders |
| 2026-11-14 02:51 | 7d3e9dc1 | J-3335: Rail C shadow double_repeat trigger (bored_streak>=2), additive, restart-gated |
| 2026-11-14 02:47 | e54e9c3f | job-run worktree merge: x4__ungrouped_J-2801 (jobrun/x4__ungrouped_J-2801) |
| 2026-11-14 02:47 | 3178aeb2 | job-run worktree merge: x4__ungrouped_J-2678 (jobrun/x4__ungrouped_J-2678) |
| 2026-11-14 02:43 | 46130003 | J-3671: reply-hand prompt quotes the thought via peers.quote_thought, not thought[:300] (P-0026) |
| 2026-11-14 02:43 | dee36711 | J-2678: remove dead first _build_system_prompt call in _think (F-3427) |
| 2026-11-14 02:43 | 6049f746 | J-2801: correct stale gemma4/11439 docstrings and note station mislabel (F-3436) |
| 2026-11-14 02:36 | 00a2f43a | J-3656: stored letter fragment cap 1300 -> 3600 (F-3677) |
| 2026-11-14 02:29 | 94d5a5ef | J-3830: log-only per-item self-rated P(correct) before math/music drill items (D-0736); restart-gated |
| 2026-11-14 02:05 | 8c504c0c | job-run worktree merge: x0_symbol_evolution_readback_pl (jobrun/x0_symbol_evolution_readback_pl) |
| 2026-11-14 02:04 | 8f67ab61 | J-2662: Option E ignition promotion from the stream (shadow rows + dormant live path, restart-gated) |
| 2026-11-14 02:00 | 8ab2caeb | J-3861: pass note_fragment_id to symbolic lens read (restart-gated) |
| 2026-11-14 01:27 | cfe3d9d7 | job-run worktree merge: w15_social_world_school (jobrun/w15_social_world_school) |
| 2026-11-14 01:26 | f6f46957 | J-3817 / D-0720: PRACTICAL_FIRST flag (default False) swaps nature slots, wood branch in nature_study._scene() |
| 2026-11-14 01:25 | 43f6d8ea | J-3815 / D-0717: drop invented garden from write-first prompt and friends' world context |
| 2026-11-14 01:06 | 3c5c5101 | J-3507: lens usage proxy rows (kind lens_usage) for the three recall-lens shadow logs |
| 2026-11-14 00:56 | 3bdb35f3 | J-3685: word-safe _seed_cut on dream narrative, passage and thread-state seed lines (SEED_TEXT_HYGIENE_ON, res |
| 2026-11-14 00:40 | 106d8312 | J-2822: gate wandering divergent-memory user-prompt append behind IDLE_DIVERGENT_SEED; log divergent_shadow wh |
| 2026-11-14 00:17 | 343c6d74 | J-3077: essay sections get distinct note slices, persisted outline, word-boundary title, overlap check |
| 2026-11-13 23:44 | 5283a794 | J-3796: flag-gated known_text shown/withheld arm, default OFF (D-0693) |
| 2026-11-13 08:50 | 04dfe252 | Add stream-mouth cues to _DEST_SHORE (J-3527, F-4138) |
| 2026-11-13 08:39 | 8996575d | Fix stale hot-lane cap comment in prompt_budget.py (J-3515, F-3525 item 1) |
| 2026-11-07 13:13 | 936c493d | Merge jobrun/wg_8: Run I retry chain wg_8 (jobs that died on the usage limit in Runs G and H, redone) |
| 2026-11-07 09:14 | 6d96fd46 | J-2941 idle prompt sample: watch-list rows (Right now / Travis is here / cat / thermal / light / smell / liste |
| 2026-11-07 09:09 | 6a8eb8fe | J-2933 sampled full-text log of the idle thought's user prompt (F-3620, P-0030..P-0033) |
| 2026-11-07 09:01 | 9349b0cd | J-2960: an ungraded school lesson earns no grade-scaled joy (F-3652) |
| 2026-11-07 07:59 | d33460df | Merge jobrun/wh_2: Run H chain H2 - Lane 2 coherence why, companion presence, stale-patch repeat clause, evide |
| 2026-11-07 07:45 | c7d544a2 | Merge jobrun/wg_9: Run G chain G9 - store, refinery, journal, curiosity node (J-3071, J-3180, J-3443, J-3066,  |
| 2026-11-07 07:45 | 0ba8d43c | Merge jobrun/wg_5: Run G chain G5 - closure, commitment, sitting, self_implication, night (J-2964, J-2963, J-3 |
| 2026-11-07 07:45 | 89b8a212 | Merge jobrun/wg_3: Run G chain G3 - essay lesson chain (J-3086, J-3052, J-3053, J-3081, J-2992) |
| 2026-11-07 00:32 | 2b58d3da | J-2988: drill graders grade the answer field only, blank answer = wobble, article 'a' is not the note A, raw a |
| 2026-11-07 00:18 | 7785e84f | J-3336: stale-patch cue second trigger, repeat_record (shadow only; F-4314, F-4315, D-0677) |
| 2026-11-07 00:09 | ba977031 | J-2925: the search-my-own-works hand reaches WORK_/ESSAY_/TAB_ files; book-note folders are a second pass (F-3 |
| 2026-11-07 00:03 | 5c43f5b3 | J-2939: companion presence worded by place, one presence clock (F-3629, P-0031) |
| 2026-11-07 00:03 | 92614cb7 | J-2935: idle seed quoted lines (previous thought, broadcast echo, mid-thread carry, ledger point, last-thing h |
| 2026-11-07 00:00 | 39deb97e | J-2915: idle seed text is cut at a word boundary and no longer renders '?.' (F-3587, F-3579, F-3575, P-0033) |
| 2026-11-06 23:53 | 9bd8825e | J-3029: deep-memory feed logs every consult_sync attempt and memoises repeated questions (F-3733, F-4294, P-00 |
| 2026-11-06 23:44 | e4ca7c81 | J-3025: a named wish to write to a waiting friend is a reply; precise initiation matcher; route tag (F-3731, F |
| 2026-11-06 23:38 | 3573b5d0 | J-2973: nightly journal sees a spread of the day's deeds, not the first 12, and no thought-lines; SHAPE exampl |
| 2026-11-06 23:33 | 3650f29d | J-2985: reply prompt reads the whole friend letter, drops the named image, neutral gender, cleans salvage resi |
| 2026-11-06 23:25 | f61d0bb4 | J-2992: a fail-open grader result is ungraded (None), not a neutral 0.5/0.6 recorded as a measurement (F-3691) |
| 2026-11-06 23:20 | 55ed855f | J-2995 sitting dwell_release rows log thought_full (600, as the judge read), priors and felt_seen; stale sit c |
| 2026-11-06 23:16 | 183d7f8a | J-3081: capstone felt rating asks one lane, stores null when unrated, sees first+last 1,500 chars, logs the an |
| 2026-11-06 23:01 | a10bbc02 | J-2984: reply hand picks the friend the thought names and never replies to a question (F-3674, P-0026) |
| 2026-11-06 22:57 | e4483d8e | J-2930: curiosity memory.ask line no longer re-offers the same fragment for a question's whole life (F-3618 pa |
| 2026-11-06 22:15 | 223c95c6 | Merge jobrun/wf_10: Run F2 chain F10 - retire the weekly self-mirror and demote its 17 fragments offline (J-34 |
| 2026-11-06 12:31 | 57f18e5c | J-3478: retire the weekly self-mirror (flag) and offline-demote its 17 stored fragments (D-0630 + D-0434, foun |
| 2026-11-06 12:20 | 972d9377 | Merge jobrun/wf_10: Run F chain F10 - integrator question guard (J-3477), stream-mouth standpoint (J-3486), re |
| 2026-11-06 12:20 | 372eb752 | Merge jobrun/wf_8: Run F chain F8 - content_hash writers (J-3395), hidden-tier readers (J-3398), own moment_ts |
| 2026-11-06 10:57 | d2c6be71 | J-3289: stale-patch cue as a shadow-only renderer with a deterministic clause verifier (boredom design Stage 0 |
| 2026-11-06 10:54 | 79a56fcf | J-3479: own_moment_ts - give a fresh inner thought its own accurate moment stamp (F-4017 / J-3393, founder fix |
| 2026-11-06 10:51 | 7df1051c | J-3485: routed read act that completely names a different shelf book switches to it; hourly cap 4 -> 6 (D-0609 |
| 2026-11-06 10:50 | 73129bce | J-3001: curiosity worth-judge grades the pursuit-eligible questions, not the LP top-5 (F-3695, F-3702, D-0683) |
| 2026-11-06 08:48 | 6dcdca18 | Merge jobrun/we_5: Wave E chain E5 - symbol read-back pause + window metric (J-3226), deep-memory name gate (J |
| 2026-11-06 07:54 | 52c69c88 | J-3245: condensed-thought twin v2 (D-0633): live system text + twin ask, restart marker, post-fix-only judge a |
| 2026-11-06 07:32 | e35a58b4 | J-3244: Follow Line returns a hypothesis's own intervention_test; writer gate on at the restart (D-0632) |
| 2026-11-06 07:29 | 640aee18 | J-3139: D-0534 idle self-implication scan 12x less often + J-2827 prompt/felt fixes (shadow, restart-gated) |
| 2026-11-06 07:27 | 2da16464 | J-3230: exclude name questions from the deep-memory gate (D-0619) |
| 2026-11-05 18:39 | c7a3615d | J-3267: run the dead idle feeds off the event loop (D-0658) |
| 2026-11-05 18:13 | 332be328 | J-3182: when the Emissary cannot ground, deliberation is skipped and the raw thought is stored; no hot-lane fa |
| 2026-11-05 18:06 | 503d3f81 | J-3220: route act.kind=read to the existing read latch, gated and capped (D-0609, F-3467) |
| 2026-11-05 17:52 | fa36f5c9 | J-3184: friend replies report only what is true of his day (D-0571) |
| 2026-11-05 17:50 | e47b25e5 | J-3223: reword the current-concern anchor leads to state only what is true (D-0612) |
| 2026-11-05 17:45 | e3d87a4c | J-3221: correct the idle prompt's base-rate wording (D-0610) |
| 2026-11-05 17:43 | acd7b7d3 | J-3188: label the curiosity memory hit honestly when it is his own earlier answer (D-0575) |
| 2026-11-05 17:38 | 6fe3ebed | J-3187: drop the restored farewell line from the idle seed (D-0574) |
| 2026-11-05 17:36 | d68a1951 | J-3151: reword the B6 hard-feeling steer so he names the feeling himself (D-0542) |
| 2026-11-05 17:35 | afe3b3f8 | J-3156: remove the open-book offer seed line from the idle prompt (D-0543) |
| 2026-11-05 17:32 | 4636ec9d | J-3196: wire GRAND_WORK_PLAIN_PROSE into IMN _author part writer (D-0584), flag stays False |
| 2026-11-05 17:32 | 42fadf4d | J-3374: IMN half of D-0587 (job J-3200): _author grounding passes exclude_own_works=True |
| 2026-11-05 17:32 | b56f63d0 | J-3357: IMN half of D-0582 (job J-3195): skip the taught maths re-attempt above HINT_AUTHORED_MAX_LEVEL |
| 2026-11-05 17:29 | 3b2bd07a | J-3371: D-0535 IMN half: contrary route passes the whole thought, descriptive note replaces the system-voiced  |
| 2026-11-05 17:27 | ac7001fd | J-3227: ambience no longer tagged as a grounding percept (D-0616) |
| 2026-11-05 17:27 | 51baebab | J-3284: IMN half of the origin labels: shock seed names its source, memory-ask frame no longer calls a looked- |
| 2026-11-05 17:26 | a4e6d9ae | J-3203: _author files the work first, then records the Emissary's grade to the shadow log (D-0591 part 2) |
| 2026-11-05 07:18 | 15d83daa | J-2840: correct "shadow / changes NO behaviour" docs on the P-0038 commitment scan (comments/docstrings only) |
| 2026-10-30 17:57 | cfd4a36c | Widen peer reply latch in shadow; surface reply-hand failures (J-2596, F-3320, D-0517) |
| 2026-10-30 17:49 | 580bbef7 | job-run worktree merge: sleep_dream_redesign (jobrun/sleep_dream_redesign) |
| 2026-10-30 17:47 | ef1658f3 | Night stall sub-marks inside the replay and pre_dream_done stage bodies (J-2558, F-3260) |
| 2026-10-30 17:47 | 7a59045b | J-2582: tag-capture fifth replay stratum SHADOW (flag off) + replay harness (I-0107, F-3315) |
| 2026-10-30 17:33 | 78d015b9 | D-0514 (a) / J-2591: dosed commitment anchor at the idle anchor, SHADOW, default dose 0 |
| 2026-10-30 17:27 | 5d9ea0de | Night stall sub-marks inside peers delivery, after stick_test, and around each dream scene (J-2557, F-3258) |
| 2026-10-30 14:25 | 5ba4e4f8 | intervention_test field on object hypotheses, gated off by default (J-2524, I-0102) |
| 2026-10-30 13:41 | 642be603 | Closure arms 3: pursuit + commitment arms with done_when written at open time (J-2160) |
| 2026-10-28 09:23 | b8a9e6f4 | J-2463: LANE2_LIVE=True -- cup line coordinate-only, climate bucket in D-0301 sized form (D-0497 (2)+(4)) |
| 2026-10-28 08:29 | 1b780119 | J-2460: the Follow Line, Phase 1 -- delivery, settled, id-keyed close, closure arm=line, stop 5 against; FOLLO |
| 2026-10-28 07:49 | eb0f180b | J-2459: the Follow Line, Phase 0 shadow (FOLLOW_LINE=shadow, restart-gated, D-0494 unruled, NOT merged) |
| 2026-10-19 18:10 | 4dcfaf49 | J-2448: identity_estate re-seed: batch embeds + text-hash cache + off-loop sync (kill switch ESTATE_OFFLOAD);  |
| 2026-10-18 18:15 | 4af95fa6 | J-2404: world_consolidation.sweep runs in a spawned child (sleep_offloop.off_process), restart-gated |
| 2026-10-18 17:55 | be70c5e7 | J-2403: stick_test.snapshot runs in a spawned child (sleep_offloop.off_process), restart-gated |
| 2026-10-18 14:36 | 93579a8a | J-2384: book_residue.sweep in a spawned child interpreter (GIL convoy fix, F-3082) |
| 2026-10-18 12:59 | f61777a2 | J-2359: object_epistemic_loop Phase 1 provenance fix + O1 archive tool (dry-run default) |
| 2026-10-17 23:04 | 55381098 | condensed_thought: flip CONDENSED_TWIN=True for next boot (D-0471, J-2349); test the +5 s cost-kill read check |
| 2026-10-17 22:35 | 9c38066d | J-2330 / F-3019: exact night stall attribution (prev_sub, sub_set_offset_s, marks_during, sub_age_s) + sub-mar |
| 2026-10-17 22:22 | bd111042 | Practical School: issued rows, period-end grader, whip_rope_end co-location gate (J-2315, F-3009, restart-gate |
| 2026-10-17 22:14 | 372b8e66 | condensed_thought Phase 0: shadow twin + offline decoupled judge + read script (J-2281, restart-gated) |
| 2026-10-17 14:19 | b4dbaf48 | J-2202: wire social-cognition probe into the sleep batch (capped, time-budgeted, restart-gated) |
| 2026-10-16 20:27 | 87648cdb | job-run worktree merge: drowsiness_phase (jobrun/drowsiness_phase) |
| 2026-10-16 20:27 | 46edc627 | job-run worktree merge: emissary_lane2 (jobrun/emissary_lane2) |
| 2026-10-16 20:27 | ccc313f6 | job-run worktree merge: within_cycle_reentry (jobrun/within_cycle_reentry) |
| 2026-10-16 20:25 | 57b13903 | J-2217: World Ledger first consumer, shadow-only 'what do I know about X' (T-0089) |
| 2026-10-16 19:55 | 724f11dc | J-2244: drowsiness_phase section 2 shadow drowsy zone (D-0441) |
| 2026-10-16 19:54 | c8ecdde0 | J-2216: within_cycle_reentry Phase 2 SHADOW - commitment-formation + scene-binding re-entry with arousal-budge |
| 2026-10-16 19:45 | 133b023c | J-2214: continuous_stream Phase 2 (Rail C.2/C.3) grounding-injection + re-seed SHADOW |
| 2026-10-15 19:47 | 390f6fff | J-2141: stall-attribution sub-marks + night_stall_attribution.jsonl probe (F-2825) |
| 2026-10-15 12:17 | f4cea7d4 | sleep_as_a_mode J-2064 (D-0407 B, travis 2026-10-15): the founder's message wakes a sleeping Du; the answer fo |
| 2026-10-09 09:10 | a0bbd3fa | sleep_as_a_mode J-2026 (F-2626): meta_awareness.scan off the loop in _enter_sleep; curiosity_queue enqueue/mar |
| 2026-10-09 09:05 | de0ad7b2 | sleep_as_a_mode Phase 3 (J-2019, D-0401 B): zero-LLM human-message wake monitor, observe-only (WAKE_ON_HUMAN F |
| 2026-10-09 09:00 | a44fd364 | sleep_as_a_mode Phase 2 (J-2018, D-0400 B): dormant layer for night thoughts + fence canary + one waking seed, |
| 2026-10-09 08:52 | db13cc84 | sleep_as_a_mode Phase 1 (J-2017, D-0399 A): shadow night-mind task, NIGHT_MIND_ENABLED default False |
| 2026-10-09 00:47 | becabcb0 | job-run worktree merge: sleep_mode (jobrun/sleep_mode) |
| 2026-10-09 00:20 | 04d0c3e4 | J-2008 / D-0396: coordinate-only open-doubt cup, SHADOW publisher (restart-gated, observe-only) |
| 2026-10-08 21:11 | 00662369 | J-2011 (F-2611): post-wake sleep_pressure row so status()['last'] stops being the fire row |
| 2026-10-08 21:07 | 664e3037 | J-2016: sleep_as_a_mode Phase 0 - remaining sleep stages off the loop, scheduler_turns, in-sleep pressure rows |
| 2026-10-08 18:14 | fb452b96 | J-1992: guard runaway salvaged idle thought at leaked JSON key (F-2593) |
| 2026-10-08 16:01 | 12905f41 | job-run worktree merge: prompts_words (jobrun/prompts_words) |
| 2026-10-08 16:00 | cb12231a | J-1955 / D-0368 A+E: edge-triggered affective steers; system sentences stored as system_note |
| 2026-10-08 15:53 | 5b360ca9 | J-1954 / D-0367: gauges as words everywhere (shared renderer in core/mood.py) |
| 2026-10-08 15:53 | f63ce8c7 | Dosed Coupling Phase 2 shadow: residual gate beside spike gate, composed hub key (J-1957, D-0370/D-0371) |
| 2026-10-07 18:05 | de64ba49 | J-1918 / F-2547: run the idle-thought Scholar consult_sync and memory.ask(descend) (monologue _think) and curi |
| 2026-10-07 16:52 | 8fb75984 | J-1917 / F-2546: run the sleep-consolidation sweeps (stick_test.snapshot, peer_metrics.snapshot, holdrate_snap |
| 2026-10-07 12:40 | eec5a0ee | J-1893: pursuits light sidecar for status()/sample_series (shadow-first, flag off) + should_sleep off the even |
| 2026-10-07 07:50 | 597b97ba | J-1835 / D-0348: clause-first tin resolution in _observe_target (look verb's own clause reaching a tin/packet  |
| 2026-10-04 15:51 | f2fdcdcb | J-1764: D-0333 seed tin's own words on the look row + whole-word tin cue in _OBS_TARGETS |
| 2026-10-02 00:13 | ed34b4fd | J-1635: widen _move_dest() gate/bed/mailbox cues for an inserted modifier |
| 2026-09-28 17:57 | 6bfa519e | job-run worktree merge: memory_as_a_service (jobrun/memory_as_a_service) |
| 2026-09-28 17:37 | 349d7bec | J-1601: fix _OBS_TARGETS collapsing every herb cue to bed, add 25 missing species cues |
| 2026-09-28 17:35 | 76b29ac2 | J-1617: wire curiosity's note_usage() metric-sheet hook (memory_as_a_service.md sec4.3) |
| 2026-09-28 15:32 | c6f61857 | job-run worktree merge: memory_as_a_service (jobrun/memory_as_a_service) |
| 2026-09-28 15:30 | 22cf694a | job-run worktree merge: guidance_learning (jobrun/guidance_learning) |
| 2026-09-28 14:52 | d6e6091a | J-1588 (D-0312): give curiosity a real, additional memory.ask() fragment-store call |
| 2026-09-28 14:09 | 1800a196 | J-1586 (D-0309): gate the idle founder-recall tie-break bump on raw similarity |
| 2026-09-28 13:54 | 7a167458 | J-1587 (D-0310): flip memory_as_a_service's 3 kill-switches True -> False |
| 2026-09-28 10:11 | 9235ae96 | J-1516: recall-act accounting wrapper -- felt-coordinate join + log_co_recall (memory_as_a_service sec4.2/4.5) |
| 2026-09-27 23:55 | fdcba427 | J-1428: founder idle recall + divergent seed OFF as unasked pushes (D-0292) |
| 2026-09-27 18:50 | 0b8847c7 | Merge branch 'jobrun/lane2_the_witness' into master |
| 2026-09-27 16:21 | 421c2f48 | docs: move dated top-level one-offs into reviews/ + session_handoffs/, fix dangling doc paths, Monetisation.tx |
| 2026-09-27 11:52 | 24a51ad2 | J-1390: Lane 2 witness cup consume-once + TTL + rate cap, not a 6-min window (F-1952) |
| 2026-09-27 10:20 | 5c8a6978 | J-1381: Lane 1 hint producer whole-word topic match, train no longer nominates wet (F-1940) |
| 2026-09-26 22:02 | 057132fb | job-run worktree merge: cluster_a_prompt_social (jobrun/cluster_a_prompt_social) |
| 2026-09-26 21:30 | 4c1a9038 | J-1366: prompt hygiene batch -- wandering frame, hold/boredom clash, double quote, dead voice-replies, B6 + re |
| 2026-09-26 21:00 | e8afc746 | J-1401: restore J-0382's read_count_importance_shadow wiring lost in c95b205 (D-0084, F-1967) |
| 2026-09-25 09:53 | b7e6a863 | J-1346: dedup garden-fetch peer-letter storage via peers.remember_inbound() (F-1902) |
| 2026-09-24 09:06 | 30a11e63 | Fix false "I finished a book" on dark reads (F-1849, D-0275) |
| 2026-09-23 17:30 | a52495c1 | job-run actions_expansion: J-1182/J-1187 gate-unmet reports (F-1767/F-1768), J-1183's J-1180 fix read (F-1776, |
| 2026-09-22 20:00 | 690d0867 | J-1161 (D-0241 shadow-first): build Lane 2 Phase 1 read path -- cup, bucket, habituation gate, would-ride log  |
| 2026-09-21 18:39 | 781e8ac3 | J-1185: system-driven redirects (night.to_bed, school reel-back) are exempt from D-0224's first-leg gate (D-02 |
| 2026-09-18 18:09 | caed0a64 | J-1112: build D-0226's narrow "I just did X" grounding check (F-1527) |
| 2026-09-18 08:04 | 1621742a | J-1075: add explicit sensorium.tick() calls between night.py sleep-pipeline stages (F-1469 fix) |
| 2026-09-18 07:51 | 0665c3b1 | J-1071: F-1459 shelf/desk/book cues + double-perceive gate |
| 2026-09-17 20:18 | 512641a0 | J-1042: real candidate mechanisms found for substrate-tick sleep starvation (F-1469) |
| 2026-09-17 19:56 | c177d238 | J-0998: broaden the LISTEN latch's fixed 8-phrase tuple (F-1367) |
| 2026-09-17 19:12 | 32fe142c | J-0852: books_have_a_place B3+B4 -- read gate = light AND book here, shadow behind 'book_gate' (D-0204) |
| 2026-09-15 13:13 | f2e98a25 | J-0919: close climate_engine._ignite()/IMN._sleep_callback swallows (F-1416) |
| 2026-09-11 13:07 | dde59618 | job-run worktree merge: actions_wood (jobrun/actions_wood) |
| 2026-09-11 12:55 | dc2fffaf | J-0877: fence core/keepsakes.py (write-fence module #19) + close its 3 external swallows (F-1252) |
| 2026-09-11 12:48 | c136619a | J-0864: sensorium.move() accepts the bare 'wood' token (F-1249, D-0209 opened); woodpile is a garden cue |
| 2026-09-11 12:44 | 8747644b | J-0874: close the external swallows of core/frontier.py's NonLiveWriteError in curiosity_node/dream_node/inner |
| 2026-09-10 14:25 | 2a498036 | J-0833: _move_dest() resolves the place the move verb REACHES (F-1227); D-0193 re-ruled, raised bed widened |
| 2026-09-10 11:18 | 19f9159b | J-0831: smell.percept_shadow() + inner_monologue_node third try re-raise NonLiveWriteError (F-1226) |
| 2026-09-09 09:31 | 5633eb58 | J-0816: close inner_monologue_node.py's thermal/light percept_shadow() swallow (F-1194); spawn J-0831 for smel |
| 2026-09-09 09:11 | 548ff4d9 | J-0815: close 4 connecting-tissue swallows beyond J-0792 (F-1170, F-1193) |
| 2026-09-08 20:50 | f6c8d8f1 | J-0797: fence soundscape.py's ambience dispatch chain into inner_monologue_node.py (F-1145) |
| 2026-09-08 20:35 | dfbb5dc5 | J-0796: fence sensorium.py/garden_soil.py/study_life.py's connecting tissue one layer beyond garden_knowledge. |
| 2026-09-08 20:01 | 13b28a74 | J-0795: close inner_monologue_node.py's nature-practical run() grading swallow, D-0179's third practical_lesso |
| 2026-09-08 19:44 | abe4b55b | J-0798: fix note/_note NameError swallow in _stream_integrate() (F-1147/F-1172), plus a second bug on the same |
| 2026-09-08 15:41 | caaca02b | J-0785: close write_or_revise() connecting-tissue gap in inner_monologue_node.py (F-1123/J-0770) |
| 2026-09-08 14:27 | ac52dda9 | J-0782: close school.py + inner_monologue_node.py's own swallows so D-0179's raise reaches the live loop (F-11 |
| 2026-09-07 23:40 | 31dfecd5 | J-0752: let D-0179's hard-raise escape inner_monologue_node.py's own direct write-fence calls |
| 2026-09-07 12:49 | 4b039cad | J-0695: reject a location-mismatched observe target at the source (F-1000/F-1001) |
| 2026-09-06 18:02 | 92de5330 | J-0668: log CancelledError at both _essay_lesson call sites (D-0169 follow-up) |
| 2026-09-06 09:53 | a92320bd | living_world_upgrade: fix the _tl blocker-bleed exposure across 12 hands.wants() latches (J-0657, F-0958) |
| 2026-09-06 08:48 | 82ad7377 | living_world_upgrade: letter-fetch latch, phantom candle tin, resource-destroying sync bug, and sweep/fire mat |
| 2026-09-05 22:11 | c6b9cd37 | Practical School build 2/3: core/practical_lesson.py, school-directive nature-slot alternation, rung-1 hands w |
| 2026-09-05 17:06 | e129693d | Music composition hand fixed (F-0870, J-0625, D-0010); lesson targets set to what a period holds (F-0871) |
| 2026-09-05 15:26 | 6f6d7d0c | Dosed Coupling Phase 1: publish + ride log, observe-only (D-0152 GO, registry variant, J-0617) |
| 2026-09-05 10:56 | 55f450d2 | Gate PLAY light points on joy delta, not just absolute level (D-0151) |
| 2026-09-05 09:09 | ac12be87 | Add shadow-only stream-topic habituation, anchor-noun keyed (J-0602) |
| 2026-09-04 22:29 | f783ad4a | J-0581: fix stream_drive grounding-tag mismatch so Rail B's gate fires (F-0811b/F-0817) |
| 2026-09-04 17:12 | ec418c9b | job-run batch 2/2: J-0536, J-0539..J-0544 done (F-0777..F-0792; D-0147 opened; J-0564..J-0575 spawned) |
| 2026-09-04 07:18 | a37083cf | Idle founder-memory route: missing module-level 'import re' (D-0141 never fired for 11h after the 20:03 restar |
| 2026-09-03 19:25 | dea44fc9 | Librarian asks the real question (J-0547); Travis's words reach idle thought (D-0141); joy_start instrument (F |
| 2026-09-03 08:09 | d915eedf | Living World L4: traces, deaths and carcasses, interactions, graduation, HUD (J-0513, D-0130/D-0133) |
| 2026-09-02 15:27 | 9a188958 | Phase 0 (shadow) of the conversational-redirect plan (F-0675) |
| 2026-09-02 14:09 | 02862fe2 | Wire J-0476's Tier-2 symbol observe-only logging (lost to the same collision) |
| 2026-09-02 14:05 | 1a6c8561 | Full 5-variable homeostasis model, kind-aware pruning wired live, geometry co-evocation win |
| 2026-09-02 13:33 | c21ed1c1 | Fix _move_dest missing outside/in destination vocabulary (F-0634, J-0459) |
| 2026-09-02 13:03 | a433abc9 | Reentry Phase 1 live, geometry P1 index, thermal tuning, decide-review backlog clear |
| 2026-08-30 01:08 | ae5bb841 | Retire the ungated fallback (D-0098 discharged) |
| 2026-08-29 17:22 | e716c96c | J-0411/D-0093: route study_note.write_or_revise to qwen3.5:9b |
| 2026-08-29 15:36 | 29329e33 | J-0311: re-seat dwell-release judge off the hot lane (decoupled-judge) |
| 2026-08-29 13:00 | c95b205b | Redo (again): reflection_node.py WHERE WE LEFT OFF gate < 8 -> < 5 -- reverted a second time between edits, ca |
| 2026-08-29 12:59 | 13a50f52 | Reconstruct: Carl/Jung identity-key rename + WHERE WE LEFT OFF gate fix (redo) |
| 2026-08-29 12:56 | 3470b4d9 | Checkpoint: lock in post-reset agent work (J-0364, J-0383, J-0374, J-0230, J-0179, J-0149, J-0330, J-0283, J-0 |
| 2026-08-29 10:41 | f4f32389 | Decide-review pass + job-run execution: 23 rulings, 28+ built jobs (2026-08-29) |
| 2026-08-28 13:46 | a1ca090a | Fix cat location leak: react() had no visibility gate |
| 2026-08-27 19:36 | e828d9ba | Redistribution moves 1-3: commitment judge -> mixtral:11438, dreamer + tiebreak -> command-r7b:11441 (D-0044) |
| 2026-08-27 18:42 | 8eef0bb9 | Baseline: Nascence pre-git state, 2026-08-27 |

### Commits touching model lanes / client

| committed | hash | subject |
|---|---|---|
| 2026-11-14 02:38 | 4eb986a5 | J-3668: decomposed critic internal-cycle stimulus framing, flag-gated default OFF; shadow rows record input_ty |
| 2026-11-14 01:27 | e9130c42 | job-run worktree merge: w15__ungrouped_J-3836 (jobrun/w15__ungrouped_J-3836) |
| 2026-11-14 01:26 | 1a29128e | J-3760: additive fn (co_qualname) field beside by on llm_calls/thought_station/llm_latency/json_parse_fail row |
| 2026-11-14 01:26 | 42a66718 | J-3836 / D-0671: Reflection stops asking needs_more_memory and emotionally_aligned; Executive drops the Reflec |
| 2026-11-07 08:43 | 41682e85 | J-2834 Critic prompt hygiene: drop identity_consistent from the prompts, fix violation counts, strip change-lo |
| 2026-11-07 07:45 | c7d544a2 | Merge jobrun/wg_9: Run G chain G9 - store, refinery, journal, curiosity node (J-3071, J-3180, J-3443, J-3066,  |
| 2026-11-07 07:45 | 15be3e96 | Merge jobrun/wg_8: Run G chain G8 - consolidation, critic, librarian, prompt_budget (J-2826, J-2828 and others |
| 2026-11-07 00:06 | 099c6fd7 | J-2846: Curiosity prompt hygiene: word-boundary trims, seed labels reworded at the selector, stale text fixed  |
| 2026-11-06 23:30 | b3c6cee0 | J-2831 Critic: internal-cycle framing behind CRITIC_INTERNAL_FRAMING_ON (default OFF; F-3500, P-0008, D-0551) |
| 2026-11-06 23:17 | 0f621742 | J-2828 ConsolidationNode: stop requesting write-only patterns_noted / memories_processed (F-3471, P-0012) |
| 2026-11-06 22:57 | d841c4ab | J-2964 closure composer calls labelled in the latency log; stale SHADOW docstring fixed |
| 2026-11-06 12:21 | 9192a1cf | Merge jobrun/wf_6: Run F chain F6 - prefill counts, Reflection frame and hedge logs, node failure log, compose |
| 2026-11-06 12:20 | cf4a199d | Merge jobrun/wf_2: Run F chain F2 - think-license downgrade (J-2852), key shadow (J-3310), chapter-descent sha |
| 2026-11-06 11:07 | b7624434 | J-3475: drop urgency from the Curiosity node and fix the false prompt sentence (D-0607 re-ruled, F-4092, P-001 |
| 2026-11-06 11:02 | 95635fed | J-2857: Voice retires the inert regurgitation guard + exemplar loader; style_confidence becomes an optional fi |
| 2026-11-06 11:00 | d5fa1bb2 | J-3314: shadow log of hedge agreement between Reflection's two drafts (D-0671, J-3171 5.3 C1) |
| 2026-11-06 10:46 | 9a10729b | J-2852: think license that returns empty content downgrades to think=false; a failed Executive/Critic is named |
| 2026-11-06 10:43 | 0deba61e | J-3118: store the stance judge's why and answering hub on the thread row; stance_distribution gets an honoured |
| 2026-11-06 10:38 | 1fc4d84b | J-2849: Salience interrupt flag no longer outlives its cycle; one predicate (F-3521) |
| 2026-11-06 10:38 | 1f4d9a0a | J-2675: log ollama/hub prompt_eval + eval counts on llm_latency rows (prefill visibility, F-3426) |
| 2026-11-05 19:24 | 87611861 | J-3173: record input_type on persisted cycle fragments and label internal ones separately (D-0561) |
| 2026-11-05 18:37 | 4d923f7a | J-3166: phase 1 SHADOW of the 7th (curiosity) Emotion channel (D-0555) |
| 2026-11-05 18:33 | 7f477d65 | J-3167: gate the resolved_complexity light event on a calibrated carried arousal on internal cycles (D-0556) |
| 2026-11-05 18:25 | fd6479c2 | J-3172: Executive reasoning is optional in the prompt and defaulted in ExecutiveOutput (D-0560) |
| 2026-11-05 16:50 | b3f08b92 | trial merge wb_follow (grounded_learning: keep J-3181 rewrite) |
| 2026-11-05 16:12 | 76f2d938 | J-3196: prose cleaner also drops a chatty lead-in line ("Sure, here's part 1:", rule, bold title); lab reports |
| 2026-11-05 16:00 | bf8ba107 | J-3196: plain-prose part/section contract behind GRAND_WORK_PLAIN_PROSE (default False), same-input A/B lab (D |
| 2026-11-05 15:17 | 1344d9e3 | J-3284: origin labels tell the truth: shock page, system-fetched page, peer (D-0631 review J-3243) |
| 2026-11-05 07:22 | df3399f4 | J-2882: fix stale Ramses/qwen2.5 comments on the Emissary take lane (F-3554, F-3545); comments/docstrings and  |
| 2026-10-19 08:10 | 7a8ca876 | J-2416: fix stale judge comments in model_client.py; quarantine pointer in SESSION_HANDOFF.md |
| 2026-10-16 21:50 | 13b31305 | D-0451 follow-up: label-view hint 0.555 / symbol 0.58 (travis, 2026-10-16) |
| 2026-10-16 21:43 | 3ab448fb | J-2270: D-0451 option 3 -- label-view-only integration_drive knee k=148, view thresholds 0.60/0.62 |
| 2026-10-16 19:48 | e2dea8e5 | J-2248: D-0447/D-0448 (E) promote the D-0332 label view to the live climate reading + (F) judge-path shadow re |
| 2026-10-15 21:24 | f84fc93a | measurement_to_action J-2158 + J-2161 (D-0434/D-0435 A, travis 2026-10-15): recall-confidence wager + executiv |
| 2026-10-08 18:14 | fb452b96 | J-1992: guard runaway salvaged idle thought at leaked JSON key (F-2593) |
| 2026-10-08 17:51 | 744b44d4 | J-1971 / F-2573: shadow call-level timing log (hot-lane calls + human arrival) for speech-vs-thought collision |
| 2026-10-08 15:53 | 5b360ca9 | J-1954 / D-0367: gauges as words everywhere (shared renderer in core/mood.py) |
| 2026-10-08 15:22 | 7174cbdf | D-0363 (B): shadow_activation age-decay (3h half-life) + edge-triggered shadow Executive hint (J-1969), flags  |
| 2026-10-07 12:39 | cecf9940 | D-0358 build (J-1894): resolve shadow events on clean re-encounter + symbol cooldown on its own flag |
| 2026-10-07 10:45 | 698495c1 | J-1880: single-endpoint judge callers fast-fail while the Ramses lane breaker is open (F-2503) |
| 2026-10-07 08:26 | c2e29979 | model_client: per-lane circuit breaker in call_node_json (J-1832, F-2466) |
| 2026-10-07 07:59 | dc5c2bce | J-1840 / D-0354: no JSON grammar on the first call_node_json attempt for the :11441 background lane |
| 2026-10-05 08:53 | e49dfbad | J-1735 / F-2367: provenance labels for 9 raw-origin fragment types in readable_label() |
| 2026-10-02 00:06 | 170b8ec1 | J-1630: tag symbol_tracker.observe() rows with active belief_id (F-2127 cross-topic test) |
| 2026-09-28 08:36 | fb4cc3bb | J-1553 (F-2135): retense stale gemma4:e4b comment in model_client.py |
| 2026-09-25 09:36 | c1ee0c50 | J-1347: document the SERVE_CHAINS["background"] hot-lane-fallback trap at its source |
| 2026-09-24 11:45 | 10fa791b | J-1306: build regime-gated AFFECT_SOURCE_AROUSAL, SHADOW ONLY (D-0274) |
| 2026-09-15 16:37 | 0521bf82 | J-0939: build persistent per-thought station/model-attribution log (F-1308, D-0214) |
| 2026-09-15 16:09 | 0a9a0a1d | J-1045: fix core/schema.py's stale ActiveProcedure automaticity-bypass docstrings (F-1424/F-1430) |
| 2026-09-04 22:58 | fa783b64 | Fix /quit farewell contaminating founder memory (F-0796, J-0578) |
| 2026-09-03 09:07 | 7b205eae | Founder memory route (D-0134): canonical [Travis said to me] fragments, cold-exempt, own route, backfilled to  |
| 2026-09-02 14:54 | 74b9dff3 | Move Judge1 panel voting + left_lane grounding off the dark local hub (D-0121, D-0122) |
| 2026-09-02 13:03 | a433abc9 | Reentry Phase 1 live, geometry P1 index, thermal tuning, decide-review backlog clear |
| 2026-08-28 08:56 | 6c04a1ac | D-0056/D-0057 rewire: ollama off Ramses, command-r7b consolidation |
| 2026-08-27 19:36 | e828d9ba | Redistribution moves 1-3: commitment judge -> mixtral:11438, dreamer + tiebreak -> command-r7b:11441 (D-0044) |
| 2026-08-27 18:42 | 8eef0bb9 | Baseline: Nascence pre-git state, 2026-08-27 |
