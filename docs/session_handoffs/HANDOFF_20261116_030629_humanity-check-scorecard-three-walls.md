# Humanity check, a fixed scorecard, and founder rulings on the closure and confidence walls

## Session timing
- **Session started:** 2026-11-16 01:51:28 UTC
- **Last message before wrap:** 2026-11-16 03:06:28 UTC
- **Wrapped:** 2026-11-16 03:06:29 UTC

## Summary
The founder asked for another humanity check on Du and whether the level is rising over time (thought T-0140). The check found no comparable score across fifteen earlier assessments, so the trend was rebuilt from re-measurable numbers; a fixed scorecard script was then built, three standing walls were traced to their mechanisms, and the founder ruled on the closure and confidence walls in two questionnaires. Three log-only flags were turned on and nine jobs filed; nothing was committed and Du was not restarted.

## Decisions
All ruled by travis in chat through AskUserQuestion, recorded with `decide.py rule --by travis`.
- **D-0780**: option b. A small daily quota on the Follow Line's consequence re-boarding; Du's own asks and claims stay uncapped.
- **D-0779**: option b. The Follow Line is how a question gets worked, plus the Wikipedia and web lookup hand as his own act; retire the dead pursuit readers.
- **D-0786**: D-0743 supersedes D-0626 option c. Keep shadowing the pursuit close with the v3 prompt.
- **D-0784**: option B. Revert the inert `done_when` scan fragment and add a separate second post-formation call, shadow first.
- **D-0782**: NO for now on the A-B-A model swap, because the roughly 23-day freeze would block the builds ruled today. Defeater: revisit when those builds are live and read, or if two consecutive monthly scorecards show the confidence rows unmoved.
- Founder answers to needs_input jobs (not `/decide` entries): **J-3897** ruled c (fix the closure composer prompt and allow one retry); **J-3889** ruled "neither arm yet" after the read of the first ten would-be closures; **J-4078** ruled "self-claims read results, shadow first"; **J-3899** ruled "outcomes from a decoupled check against memory, plus a settle step".
- Founder go in chat to turn on the D-0775 B and D-0776 B shadow flags (F-4823).

## Builds
- **Humanity check review**: `docs/reviews/du_humanity_check_2026-11-16.md` (sections 1 to 6). Finding F-4820 holds the measured claim. F-4820 was recorded without `--session`, so it is missing from the rollup.
- **Humanity scorecard**: `scripts/humanity_scorecard.py`, version 1. Twenty frozen measures plus three context rows, recomputed per month and per ISO week from `data/` (read-only, no model call). `--write` appends a snapshot to `docs/humanity_scorecard.jsonl` and rewrites `docs/reviews/humanity_scorecard.md`. First snapshot written 2026-11-16; a second run showed no drift. Changing a definition means bumping `SCORECARD_VERSION`.
- **Flags turned on (all log-only, effective at the next Du restart)**: `MOOD_WORDS_NO_VITALITY_SHADOW = True` and `JOY_PUMP_VALENCE_SHADOW = True` in `core/schema.py` (F-4823; 8 tests pass); `V3_PROMPT = True` in `core/pursuit_close_shadow.py` (D-0786).
- **Jobs added**: J-4079 (scorecard re-run and closure read, gated on 40 rows in `data/logs/closure_gate.jsonl`, 2 so far); closure builds J-4081 (quota), J-4082 (composer prompt and retry), J-4083 (commitment judge says achieved to everything), J-4084 (retire dead pursuit readers), J-4085 (`done_when` second call); confidence builds J-4086 (self-claims shadow) and J-4087 (recall wager outcomes). Jobs done: J-3897, J-3889, J-4078, J-3899.
- **Skill suggestion** S-0326 for job-queue (see Warnings).

## Fixes
- `scripts/_test_J-4012_pursuit_close_v3.py` asserted `V3_PROMPT` default False and ran its v2 section under the default, so four checks failed after the flag flip. It now asserts True and sets the flag off for the v2 section; all checks pass.

## Findings
- **No humanness score exists.** Fifteen assessments from 2026-07-02 to 2026-11-16 share no rubric (list in review section 5). The trend comes only from re-measurable numbers.
- **The 10-15 table re-measured over the last 7 days** (review section 2): improved are attention (modal-topic share 0.97 to 0.55), contradiction acted on (2 of 95 to 21 of 126), instruction integration (0 to 7 rows) and social cognition (now measurable; intent tracked 95 percent, attributions supported 72.5 percent). Unchanged are stated recall confidence (0.85 to 0.95), pursuits (0 of 93 resolved), dreams (0 of 40 by judge panel) and mood (about -0.3). Worse are the hold rate (0.215 to 0.128) and the all-domain prediction gap (0.21 to 0.295).
- **Monthly series** (review section 3): the only sustained rises are July to September (stick-test spokes, peer outward delta, ignitions per hour), flat since. No measure rises unprompted. Movement follows targeted builds.
- **Wall 2 is partly the ruler** (F-4822). The skill prediction is the stored `confidence` in `data/capability_beliefs.json`; a drill updates only `accuracy` (`core/competence.py:89-94`). Re-scored with a running accuracy as the prior, the November gap is 0.013 against 0.300. `core/self_claims.py:31-47` claims "I am capable at X" at confidence 0.70 or more, and every domain is 0.77 to 0.89, so he claims capability in science (measured 0.38), observation (0.19) and history_culture (0.20).
- **Wall 1** (F-4822): only frontier questions have a live closing path (closure gate, enforce since the 14:01 NZDT boot, 2 verdicts, one with the judge unavailable). Pursuits have no resolved state in `core/pursuits.py`. Dream and commitment arms are shadow only. The web lookup hand is loaded and has made zero calls. The wall 1 and wall 3 code readings beyond the spot checks named in F-4822 came from a read-only subagent and were not re-checked line by line.
- **Wall 3**: affect changes sampling temperature, storage and pacing but no action choice. Nothing identified carries mood into a decision. [INFERRED] the 0 of 14 on human cycles comes from the re-bind budget and the direct-request override in `core/orchestrator.py`.
- **J-3889 read**: of the first ten would-be closures, the eight commitment ones were all judged achieved and six credit a study note unrelated to the commitment; the two pursuit ones are honest set-downs.
- **What made the topic anti-relock work**: one identified carrier, one dose, turned on live, read against kill criteria fixed beforehand (D-0485, F-4567).
- F-4821 says that before J-4075 nothing routed an empty-evidence factual question to the lookup hand. [OPEN] what J-4075 changed and whether it is loaded; J-4084 step 3 covers it.

## Open
1. **Commit this session's work.** Not done; the founder did not ask. Files: `core/schema.py`, `core/pursuit_close_shadow.py`, `scripts/_test_J-4012_pursuit_close_v3.py`, `scripts/humanity_scorecard.py`, `docs/humanity_scorecard.jsonl`, `docs/reviews/humanity_scorecard.md`, `docs/reviews/du_humanity_check_2026-11-16.md`, this handoff, and the ledgers. Stage by path only.
2. **Restart Du** so the three shadow flags load. Blocked on the founder (Control Panel or `scripts/start_supervisor_detached.ps1`). After it, check that `data/mood_words_shadow.jsonl` and `data/joy_pump_shadow.jsonl` get rows, then J-4006 and J-3942.
3. **Seven ready builds**, J-4081 to J-4087. Suggested order: J-4082 and J-4081 first, since they decide whether the closure gate reaches 40 verdicts (J-4079).
4. **Still to discuss with the founder**: affect not steering (needs a design conversation; no carrier identified); the unused lookup hand (how he comes to know he has it without a hint from the world); three falling measures that may be instrument changes (world-query grounding deficit 0.16 to 0.54, thoughts with any act 0.54 to 0.24 with a step near 10-04, T4 warranted 0.67 to 0.18). Next action: a read of each instrument's change history before any fix.
5. **Dreams**: nothing aimed at dream resolution (about 1 percent under the judge since August). Left on purpose until question closing is read.
6. **Doubt uptake** (0 of 48, F-2670) was not re-measured; it needs judge models.
7. T-0140 is still open; promote or drop it. J-3989 (layered goals first read) is past its gate and unread.

## Warnings
- `core/schema.py` and `core/pursuit_close_shadow.py` carry uncommitted flag flips. Another window editing those files should expect them.
- Running `scripts/_test_J-4012_pursuit_close_v3.py` leaves a lab directory under `data/_lab/` each time (two from this session, `20261116_155140` and `20261116_155208`).
- `job_queue.py add` failed once with `PermissionError: [WinError 5]` on its atomic rename while another window was writing; a retry worked and the queue shows all of J-4081 to J-4085 (S-0326).
- The scorecard's "questions resolved" row will probably fall before it rises: 569 of the 751 resolved frontier entries are backfilled lexical closes that no longer count.
- The scorecard's whole-series verdicts start from June, which is a different regime (1,674 human turns against 381 internal cycles); read the "last step" column and the month cells, not the tally alone.
- The measurement scripts from the first two passes live only in the old scratchpad `C:\Users\USER\AppData\Local\Temp\claude\8e21a5667f6c8928\eeb55687-2194-40de-a807-6d34df0f0008\scratchpad\` (`series\series.py`, `rescore\m1.py` to `m3.py`) and may be cleaned up; the scorecard script holds the definitions that matter.
- `/plan-maintain` state: see the last line of this file's companion memory note; if it says not run, run it with `--session` before trusting the plan index.

## Pointers
- `docs/reviews/du_humanity_check_2026-11-16.md` (the check, the trend, the walls table)
- `scripts/humanity_scorecard.py`, `docs/reviews/humanity_scorecard.md`, `docs/humanity_scorecard.jsonl`
- Findings F-4820, F-4822, F-4823; earlier F-4707, F-4488, F-4506, F-4753, F-3413, F-4821
- `core/competence.py:89-94`, `core/self_claims.py:31-47`, `core/recall_wager.py:47`, `core/pursuit_close_shadow.py:48`, `core/schema.py` (search `MOOD_WORDS_NO_VITALITY_SHADOW`, `JOY_PUMP_VALENCE_SHADOW`)
- `docs/reviews/du_vs_human_2026-10-15.md` (the table that was re-scored), `docs/reviews/curiosity_end_to_end_J-3988_2026-11-14.md`, `docs/staged/closure_producer.md`
