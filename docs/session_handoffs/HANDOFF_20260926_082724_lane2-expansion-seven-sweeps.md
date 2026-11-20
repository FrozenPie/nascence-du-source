# Lane 2 expansion: three founder tracks, then seven issue sweeps of the Witness

## Session timing
- **Session started:** 2026-09-25 23:30:02 UTC
- **Last message before wrap:** 2026-09-26 08:27:24 UTC
- **Wrapped:** 2026-09-26 08:27:24 UTC

## Summary
The founder opened with "let's look at lane 2, we really need to expand on this" (T-0064). After a status read, the founder chose three expansion tracks (finish Phase 1 to the flip; promote the curiosity idea to a staged plan; work the senses-and-scope items), and then asked, repeatedly, to keep finding issues for new jobs while a Sonnet job-run worked in another window. The session produced 33 findings (F-1929 to F-1963, with gaps where the other window's findings landed), 23 jobs (J-1370 done, J-1371 and J-1375 to J-1399 open), 6 decisions opened (D-0280 to D-0285, three of which the founder ruled in the other window during the session), a staged plan (docs/staged/lane2_curiosity.md), one idea (I-0074), and nine commits.

## Decisions
- D-0280 (Lane 2 percept widening: light_band and smells, no climate self-pressure dims for the Witness) was opened by this session and ruled by Travis in the other window at 2026-09-26 07:05 UTC, option (a). The other window's job-run built it as J-1372 (F-1947) in its worktree; not merged to master at wrap time.
- D-0281 (sampled claim-correctness judge on the Witness's notice) and D-0282 (authorize the shadow-first build of lane2_curiosity's wonder field) were opened by this session and also ruled in the other window; J-1373 and J-1374 exist for them. This session did not see the rulings' text; read them with decide.py show before assuming options.
- D-0283 (does the body percept carry a feeling label; which voice the Witness speaks in), D-0284 (how to wire the never-wired Weather channel), D-0285 (build or retire the knowledge tier) are open, opened by this session, all on lane2_the_witness. All have defeaters and Claude recommendations in their text.
- D-0058 (the deepseek seat) was read, not touched; its defeater about hub reliability is now readable through F-1937 and F-1943.

## Builds
- J-1370 done and committed (db8d3c3): core/lane2.py _TOPIC_CANON extended additively with clock, bird and sea topics plus synonyms; topic resolution over deepseek-era breaks went from 62% to 96% (F-1929, F-1930). It re-keys 143 already-resolved breaks to more specific topics, so per-topic reads must not straddle that commit. Restart-gated: the live process still runs the old vocabulary until Du's next restart.
- Section 8 (Senses and scope) written into docs/plans/lane2_the_witness.md: hardware question closed by D-0058, claim-correctness instrument proposed (D-0281), audit cadence answered (weekly, inside the section 7.6 read), percept widening (D-0280), climate dims recommendation, pointer to the curiosity track.
- docs/staged/lane2_curiosity.md written and linked from docs/ROADMAP.md (commit 51c2c3f); I-0069 promoted to it; memory file project_nascence_lane2_curiosity.md written.
- Ledger snapshot committed as 50c798e at the founder's request.

## Fixes
- The only code change this session is the _TOPIC_CANON extension in core/lane2.py (J-1370). Every other defect was recorded and queued, not fixed, because the other window's job-run was editing the tree concurrently and the founder said this window was for looking and planning.

## Findings
The plan doc's Current State section carries a dated entry per sweep with every ID; this is the map of what matters, most important first.

- F-1958 / J-1396 (urgency 4): 58% of all "broke" verdicts are predictions judged after Du walked to a different standpoint. Same-place held rate 0.48, moved 0.16. The prediction store carries no place. This is the largest single scoreboard error and should be the primary judgeability rule.
- F-1949 / J-1386 (urgency 4): since the judge_panel tiebreak moved to granite3.1-moe on 2026-08-28, every split on the "held" key has resolved broke (0 held / 503 broke; August under yi was 183 / 180). The prediction judge's own prompt scores "unsettled" as false. Agreed-only broke share is 0.58, not 0.66. The same casting vote sits on 74% of incoherent verdicts and 39 of 45 metaphor verdicts.
- F-1934 / J-1376 (urgency 4): the 08-22 horizon override forces a third of deepseek's predictions to the day clock although 81% of them name minutes, so they are judged 12 hours later and 84 of 92 break. This is the inverted horizon curve. The prompt's clock ("about two minutes") is 3x short of the measured 361 s tick. F-1962 adds that "shingle" is a sound word and must leave the override list.
- F-1935 / J-1377 (urgency 4): break_rate_24h is a ratio (~0.7), not a daily count; the plan and D-0241 read it as "0.6 to 0.8 per day". Real judged breaks run 60 to 75 per day. Day one of the would-ride log: 12 of 12 breaks rode; the copied habituation constants need four breaks per topic before suppressing. J-1304's P1-1 read must compare rides to breaks per day, not to 0.7.
- F-1952 / J-1390 (urgency 4): the Phase 1 cup is a 6-minute window, not a consumable. coupling_rides.read() never clears; idle thoughts run every 78 s; one break would seed 4 to 5 consecutive idle thoughts with the same sentence. The Tap already has the right semantics (consume-once, 30 min TTL, 4 per hour cap).
- F-1953 / J-1391: the Phase 1 bucket adds a constant ~0.11 to world_model_strain (median 0.116). It would double the dimension permanently. Recommendation: contribute only the excess over the Witness's own baseline.
- F-1940 / J-1381 (urgency 4): the hint producer in nodes/inner_monologue_node.py matches topic keywords as substrings. "rain" inside "train" makes 88% of would-be "wet" nominations; "cat" fires on "oystercatcher", "wind" on "window". Junk pushes burn the rate cap.
- F-1943 / J-1382 (urgency 4): Lane 2 is 67% of all judge-panel calls (three per tick). The first judge family times out at 90 s in overnight bursts (245 of 585 calls on 09-26, 00:00 to 08:00 local). Du's own judged cognition loses verdicts in the same bursts. D-0281 adds a fourth call; read it against this.
- F-1941 / D-0284: the Weather channel has never been wired. weather_to_gain()'s outputs are logged and read by nothing. F-1959 (positive) shows the Tap, the other channel, does work: hinted topics get looked at (tide 0.86 vs 0.17) with no loss of grounding (F-1931).
- F-1942 / D-0285: the knowledge tier (section 2.8c) was never built; the store has factual and prediction only.
- F-1955 / J-1393: the somatic sense never arrives because gather_percepts() calls a somatic.status() that does not exist; percepts_available has been world and body on all 6,401 ticks. current_body() returns energy, fatigue and tension with no feeling label.
- F-1956 / J-1394: 18% of topic-naming predictions are judged on a tick where the named field was absent (held 0.05); 75 plan-shaped "I will check" predictions (held 0.05).
- F-1951 / J-1388: the metaphor judge scores 0 of 169 figurative-phrased notices ("warm glow", "alive with", "symphony") as metaphor; its 45 hits are literal tiebreak rows. Kill criterion #1 has never been tested against what deepseek writes.
- F-1950 / J-1387 (needs_input): the Witness has no clock and no sun height; it says the sun is setting at midday 82 times. Sun phase and arc fraction already exist in core/world_clock.py sun() and are dropped by experienced_tuple.
- F-1936 / J-1378: 84% of invention flags are the heard cat (purr in sounds) and the sun at dusk.
- F-1937 / J-1379: 19% of ticks produce no output on both post-qwen seats; cause never logged. Correction in F-1941: pending-cap skips lose only the prediction, not the notice.
- F-1939 / D-0283: the body percept's dominant feeling label reaches the Witness as text (vitality, relational warmth in 22 to 30% of notices) against section 2's "no affect text"; the voice is unsettled (you 28%, I 7%, third person 14%).
- F-1933 / J-1375: 14 of 22 hand-read incoherent verdicts are the coherence judge blind to place; "at_the_door" names both the study door (fire present, 1,905 ticks) and the garden door (400).
- F-1944 / J-1383 [INFERRED]: section 2.10 (sleep) is unbuilt; whether it matters (hints pushed during sleep) is unread. "at_the_bed" is the garden bed.
- F-1963 / J-1399: riroriro is garbled 83% of the time, morepork becomes pork or pig 14% ("the morepork will have finished cooking"). A four-word gloss per rare name fixes it.
- F-1938 / J-1380 and F-1960 / J-1397: hygiene bundles (templated uncertain field, snake_case sound ids, five-decimal body numbers, stale "90s" banner; no model field per tick, stale judge docstrings).
- F-1931: law 6's boundary audit ran for the first time; no divergence between hinted and self-found ticks.
- I-0074: the Witness cannot tell its own footsteps from the world's; tagging self-caused sounds is a law-5 percept change for a future decide.

Taken together, the Witness's honest same-place forecasting skill is roughly one in two; the two-thirds broke figure the plan carried since August was mostly instrument (tiebreak, override, moved-judging, unjudgeable).

## Open
1. The LANE2_LIVE flip. Blocked on: a clean P1-1 read with corrected units (J-1377, then J-1304), the cup made consumable (J-1390), the bucket resized (J-1391), D-0152's 2026-09-27 defeater clock, and D-0211. Next action: run J-1377 before J-1304, and open the flip decide only after J-1390 and J-1391 report.
2. J-1304 (in_progress, session J-1230): its restart gate is met (Du booted 2026-09-25 19:21 local after the J-1161 commit) and its calendar gate fell due at 19:21 local on 09-26. Its briefing carries the 0.6 to 0.8 per day units error; read F-1935 first.
3. Three jobs touch the same judging code and must land in one restart: J-1386, J-1394, J-1396. J-1376 (override and prompt) and J-1379 (_ask) also touch core/lane2.py, as do J-1371, J-1375, J-1378, J-1380, J-1393, J-1397, J-1399 and the other window's J-1372, J-1373, J-1385. A job-run should expect file overlap on core/lane2.py and merge, not run them blind in parallel.
4. Open founder decisions: D-0283, D-0284, D-0285. J-1387 is needs_input pending a ruling on sun phase and a clock as percepts (D-0280's ruling did not cover them).
5. The Weather channel: D-0284 decides whether to wire it; until then D-0172 is moot.
6. Two job briefings carry wrong IDs, corrected in the plan doc: J-1388 cites F-1945 for the tiebreak finding (correct: F-1949); J-1391 cites J-1389 for the cup job (correct: J-1390).
7. [OPEN] Whether Lane 1 pushes hints during sleep (J-1383 will read it). Nothing should be built for section 2.10 until that is known.

## Warnings
- The other window's job-run has been ruling and building against decisions this session opened (D-0280 to D-0282). Its builds live in job-run worktrees, not master, at wrap time. Do not assume core/lane2.py on master reflects them.
- core/lane2.py's live process is pre-J-1370 until Du's next restart. Tonight's J-1304 read is on the old vocabulary.
- Every broke-share figure in docs/plans/lane2_the_witness.md since 2026-08-28 is inflated by F-1949, F-1934, F-1956 and F-1958. Do not cite 0.66 as the Witness's error rate.
- Long shell heredocs failed twice this session on a quoting error and wrote nothing; the Write tool was used instead. Check that a file exists before referencing it.
- Never restart Du, the supervisor, or any hub from a Claude tool (CLAUDE.md).

## Pointers
- docs/plans/lane2_the_witness.md: Current State (dated entries for each sweep, newest last before section 0) and section 8.
- docs/staged/lane2_curiosity.md; docs/ROADMAP.md staged bullet.
- core/lane2.py (_TOPIC_CANON at line 740, _judge_prior at 581, _correct_horizon around 868, gather_percepts 413, tick 881); core/coupling_rides.py (publish_witness, read); core/lane2_break_habituation.py; core/climate_engine.py (_WITNESS_STRAIN_WEIGHT, witness_bucket_value); nodes/inner_monologue_node.py (_LANE2_HINT_KEYWORDS at 152, hint push at 4484, cup seed at 175 and 2716); core/judge_panel.py (TIEBREAK line 29).
- data/lane2_shadow.jsonl, data/lane2_would_ride.jsonl, data/lane2_break_habituation_state.json, data/lane2_store.json, data/lane2_hints.json, data/coupling_rides.jsonl, data/judge_panel_log.jsonl, data/llm_calls.jsonl (by=lane2).
- Memory: project_nascence_lane2_the_witness.md (dated note appended), project_nascence_lane2_curiosity.md, and this handoff's companion file.
- Commits this session: db8d3c3, 51c2c3f, a3ebe88, 5f1a2b4, 799b848, 33e8376, 4310782, 26647b0, 16775a2, 50c798e.
