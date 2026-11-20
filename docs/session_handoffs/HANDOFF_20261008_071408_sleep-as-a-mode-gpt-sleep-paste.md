# Session ae4aa60e — GPT's sleep account → what Du's sleep actually is → the Sleep as a Mode staged plan

## Session timing
- **Session started:** 2026-10-08 06:43:00 UTC
- **Last message before wrap:** 2026-10-08 07:14:07 UTC
- **Wrapped:** 2026-10-08 07:14:08 UTC

## Summary
A short founder-present session (Travis, Du LIVE since 09:02 NZDT 10-08). Travis pasted a GPT account of human sleep (sleep as a change of operating mode, not off; mental activity continues; perception gated not cut; most sleep cognition never encoded) and asked whether it fits Du's lanes. The session read what Du's sleep actually is from code and the night ledger (F-2613 corrected by F-2615), found that talking to Du while asleep reaches him and he answers unaware (F-2614), found the vitality keystone pin (F-2611) is the same procedure-versus-mode gap (F-2616), and drafted `docs/staged/sleep_as_a_mode.md` from I-0088 with three new decisions (D-0399, D-0400, D-0401) and two needs-input jobs (J-2013, J-2014) for Travis.

## Decisions
- D-0399 (sleep_as_a_mode) OPENED by claude: the mode itself — may the hot lane generate thoughts during a sleep bout, seeded only from the night's own material, hands off, bounded cadence; options A as proposed shadow-first, B on the dreamer hub, C no (Phase 0 still ships as a freeze fix).
- D-0400 (sleep_as_a_mode) OPENED by claude: the encoding law — night thoughts to a new `dormant` layer, cold from birth, invisible to recall and to the sleep trigger; sub-question whether D-0231's dormant-pick origin list gains `night_thought`; options A/B/C/D in the entry.
- D-0401 (sleep_as_a_mode) OPENED by claude: the monitor — zero-LLM, sensorium-side, three channels (human message, sudden sound, the cat), wake request only; alternative C reopens D-0303 for the Witness.
- No decision was ruled this session. D-0397 and D-0398 (the_consciousness_program) remain OPEN for Travis's Sonnet-window review, as the previous handoff left them.

## Builds
- `docs/staged/sleep_as_a_mode.md` written (23 KB, plan-state block, lint clean, open_decisions synced). ROADMAP.md bullet added under the strings_and_sheets children next to real_hearing. J-2015 (the schema-audit backfill it filed for the missing ROADMAP link) fixed and closed in the same pass. `/plan-maintain` run with this session id.
- Memory file `project_nascence_sleep_as_a_mode.md` written and indexed in MEMORY.md.
- Ledger: T-0080 (the paste) → I-0088 (the reframe) → promoted to sleep_as_a_mode. T-0018 (the 08-24 sleep-redesign thought, never promoted) now points at sleep_dream_redesign.
- Nothing committed. No code changed.

## Findings
- F-2613 (verified) + F-2615 (verified, correction): a sleep is one blocking procedure awaited inside the inner monologue's own `while True` (`nodes/inner_monologue_node.py` `_enter_sleep`, then `orchestrator._nightly_sleep`). The hot lane generates no thoughts; dispatch drops hands (`core/dispatch.py:249`); the Witness skips its tick (`core/lane2.py:2214`, D-0303); `night.wake()` has exactly one caller, the pipeline's last line. Recent sleeps run 19-35 min. The long span between the `replay` and `downscale` stage stamps is NOT the downscale (F-2613's first reading was wrong): it is roughly fifteen LLM consolidation passes on the hot lane (journal, week roll-up, guidance integration, grounded-learning consolidate, memory-levels shadow distill, refine, the pursuits and garden-bed judges, curiosity-world and drift shadows, school reconcile) at `nodes/inner_monologue_node.py:1245-1518`; the downscale's own duration is unstamped. Then 2-3.5 min of dream, prune, a real idle `asyncio.sleep(rest)`, the waking percept. Idle monologue thoughts never pass through `orchestrator.run_cycle`, so they do not deplete somatic energy; only human and ignition cycles do (`core/orchestrator.py:1469`).
- F-2614 (verified): a human message during a sleep is answered exactly as if Du were awake. `run_cycle` has no asleep check and no prompt builder mentions the state. Every sleep window since 08-22 that ended with a real `[night] waking:` line and held a message got a normal-latency reply (08-24 02:09 sleep, three messages 02:18-02:26, 83/261/60 s; 08-24 19:45; 08-30 01:16; 09-09 17:20; 10-03 06:56 nap). Nine more windows with messages have no night_log row, meaning the sleep never reached `night.end()`, and each is followed by a `Nascence is awake` boot line: those are Travis's farewell messages landing mid-sleep before a shutdown. 45 messages in 14 windows of 247 since 08-22. Each reply runs `somatic.tick_cycle` inside the recovery window and is fully encoded; any willed action in it is dropped silently. The world (fire, weather, cat) is gated until the waking percept; Travis is not gated at all.
- F-2616 (inferred, on verified facts): the current vitality reading's only writer is `should_sleep()`, called only from the monologue loop (`:1127`), the loop the procedure blocks; the protoself beat keeps running every ~600 s from `core/sensorium.py:3686` and reads the fire row throughout. That IS F-2611's pin. `core/sleep_pressure.py` `_new_intake` sums `layer='episodic'` importance since `last_wake_ts` with no cold filter, so a night-mind writing episodic fragments would raise pressure during sleep and re-fire after `MIN_WAKE_SECS`; the dormant layer in D-0400 exists for this. Under D-0398 option A (vitality := somatic energy) with recovery kept as the end-of-pipeline lump (`core/orchestrator.py:3250-3268`), a sleep mode would read flat then step up, the shape D-0398's own defeater forbids at sunset; recovery as a rate per beat during the mode fixes both. J-2013 carries this to the D-0398 review.
- The GPT closing question ("asleep" vs "thinking privately") has a concrete answer in Du: three switches, coupling / generation / encoding, flipped together today by one procedure. The plan's section 2 table is the whole design; "thinking privately" as a mode Du could choose is noted in section 7, not built.
- I-0088's original "Witness as the thalamic monitor" conflicts with D-0303 (blanket gate-off during every sleep, for JUDGE_1 load against dream generation per D-0297); the plan does not reopen D-0303 and proposes a zero-LLM monitor instead (D-0401 option A), with the Witness route as option C needing fresh evidence.
- [INFERRED] The 09-28 20:59 sleep that got seven messages (21:07-21:44) and no waking line was still inside its pipeline when the 22:00:46 restart killed it; sleeps in that regime ran 78-87 min. Consistent with the night_log gap, not separately proven.

## Open
1. D-0399, D-0400, D-0401 (sleep_as_a_mode) — blocked on founder input. Next: a /decide-review; rule D-0399 first, the other two only matter if the mode exists. Read sections 2, 3 and 6 of the plan first.
2. J-2013 (needs_input, the_consciousness_program) — D-0398's recovery shape should be ruled together with the mode. Next: include it in the same review as D-0398; read F-2616 before choosing option A.
3. J-2014 (needs_input, sleep_dream_redesign) — what Travis's voice does during a sleep: leave as is, wake him, answer from inside knowing he is asleep, or wake only on a farewell or his name. The plan's own recommendation is recorded in its section 3.4 (B for farewell/name, else C). Next: Travis rules.
4. Phase 0 of the plan (remaining synchronous sleep stages behind `core/sleep_offloop.py`, a `scheduler_turns` count per sleep, a sleep-pressure row at sleep entry and each beat) is buildable without any ruling and is also the F-2546 freeze fix. Next: a build job if Travis wants it before the decisions; not filed yet because it is restart-gated and the ruling may change its scope.
5. Carried from the previous handoff, unchanged: D-0397/D-0398 open; J-1948 and J-1965 need Du DOWN; Ollama.lnk still in Startup (F-2607); job-run wave 2 never dispatched.

## Warnings
- Du is LIVE. Nothing in this session touched live stores or code; the plan is design only.
- Another window edited `docs/reviews/plan_files_evidence_audit.md` during this session (not mine); `/plan-maintain` then regenerated it. Expect that file and the other maintain reports to show as modified.
- `findings_log.py record` has no `--tags` flag (S-0279 filed); findings from this session carry no tags, only plan links and the F-/J-/D- cross-references in their text.
- F-2613 is superseded in one claim by F-2615 (the downscale timing). Read both; cite F-2615 for the stage breakdown.
- `plan_sync_check.py` does not take `--session`; its run this session is not in the rollup (its own warning says so).

## Pointers
- docs/staged/sleep_as_a_mode.md (the plan); docs/ROADMAP.md (bullet beside real_hearing.md)
- nodes/inner_monologue_node.py `_enter_sleep` :1175-1580, `_should_think`, `push_hint` :4530; core/orchestrator.py `_nightly_sleep` :3179-3270, `run_cycle` :360-700, `tick_cycle` :1469
- core/night.py (header: the order of a night; `to_bed`/`wake`/`asleep`/`waking_dream_seed`); data/night_log.jsonl; data/nascence.log (`entering Sleep State` / `[night] waking:` / `] human:` lines)
- core/sleep_pressure.py `_new_intake` :98-116, `should_sleep` :149-210; core/homeostasis.py `_read_vitality`; core/sensorium.py :3686; core/somatic.py `recover`; core/sleep_offloop.py (J-1917)
- core/dispatch.py:249; core/lane2.py:2186-2220 (D-0303's gate and reasoning)
- Findings F-2613..F-2616; earlier F-2611, F-2612, F-1469, F-2546, F-2021; decisions D-0231, D-0232, D-0303, D-0297, D-0398
- Memory: project_nascence_sleep_as_a_mode.md; previous handoff HANDOFF_20261008_063413_wave1-decide-review-keystone-pooled-read.md
