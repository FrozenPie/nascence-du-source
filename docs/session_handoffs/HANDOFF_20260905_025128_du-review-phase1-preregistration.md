# Du review → Phase 1 built → the-Master gate → data hygiene → retention → farewell + purge → health check → lessons (full day, 2026-09-05)

## Session timing
- **Session started:** 2026-09-05 00:36:15 UTC
- **Last message before wrap:** 2026-09-05 05:41:23 UTC
- **Wrapped:** 2026-09-05 05:41:23 UTC

## Summary

Full session 00:36–05:41 UTC in eight stretches (first wrap at 02:51, then Addenda 1–7 below): review → D-0152 GO + Phase 1 BUILT (6f6d7d0) → D-0153 the-Master gate (7b8943f) → data_store_hygiene D-0154/D-0155 light sidecars (02d32ac) → retention rule D-0156 built (30a6b5c) + first apply (0adc1e1) → /quit farewell de-fired (87864f6) + J-0538 purge done with Du down → day health check (F-0866..F-0869) → lessons: music composition hand fixed (e129693, D-0010), targets 20/16, Practical School designed + D-0157/D-0158/D-0159 ruled (0124b69, 9cfb52e) | 10 founder rulings D-0152..D-0159 + D-0010 re-ruled, 0 open | F-0843..F-0876 | J-0612..J-0628 | Du is DOWN at wrap; everything code-side is restart-gated.
Founder review ask: Du status | plans w/ evidence waiting | loop-wiring plan progress | anything overdue.
Ran: session-resume | plan-liveness | plan-index | decide list | job queue.
Found Du + whole local CPU tier down at review time (J-0613 later showed this was the founder's own deliberate /quit at 11:53 NZST, F-0850, not an accident) | delivered review.
Founder restarted Du 14:39:58 NZST, build carrying J-0602/J-0603/J-0555/D-0151/J-0576.
Dispatched 4 sonnet agents on now-unblocked read-only jobs: J-0556, J-0599, J-0572, J-0613.
Pre-registered Dosed Coupling Phase 1 myself (`docs/plans/dosed_coupling.md` section 4a, D-0152 opened, J-0615 build gated on it).
Backfilled world-store write-fence plan's index fields (J-0611, J-0616) | refreshed 2 memory files | ran plan-maintain at end.
No code changed this session.

## Decisions

D-0152 opened (GO/NO-GO Dosed Coupling Phase 1, publish + ride log, observe-only), not ruled | session start: 0 open decisions (151 ruled), nothing waiting on founder.

## Builds

No code changed.
`docs/plans/dosed_coupling.md` gained "Current State — verified 2026-09-05" section (Phase 0 first-read table) + new section 4a "Phase 1 pre-registration", containing:
- publishers table — climate: 9 ClimateField dims by name + dissonance, explore_value, ignition_level | stream: drive, ignition, grounded, progress, redundancy, train_kind, train_len, unresolved_share_10 | deliberation: recall_confidence, tensions_carried, coherence, dissonance_count, think_license, critic_verdict, cycles_since_human | witness: break_rate_24h, grounded_share, distinct_share, hint_consumed_24h | ledgers: commitments_active, commitments_load_bearing, escalations_1h, tension_top3, frontier_open, pursuits_active, pursuits_heat_max
- ride-log row schema for `data/coupling_rides.jsonl`
- landing sites: optional loop_tuples dict field on CognitiveState at `core/schema.py` line 609 | new module `core/coupling_rides.py` | COUPLING_PUBLISH flag default False | one publish call at each existing write site
- pre-registered 7-day metrics: each loop's publish rows ≥95% of its own ticks | idle-thought gap median, cycles/day, commitments formed/day, Witness break rate all inside prior-week band | <5MB/day
- kill/revert rule
Section 4 build-order table now points at 4a.
UDMS dossier on `core/schema.py` listed 20 CONTRACT-layer consumers | named `scripts/_test_episodic_buffer.py` as test target.
`docs/staged/loop_wiring_matrix.md` got dated 2026-09-05 addendum to Current State.
`docs/ROADMAP.md`: dosed coupling entry updated w/ first reads + D-0152 | new section "WORLD STORE WRITE FENCE" added.
`docs/plans/world_store_write_fence.md` got Roadmap/Memory/Build-job pointer line + real Current State section.
Memory files: `project_nascence_world_store_write_fence.md` created + indexed in MEMORY.md | `project_nascence_dosed_coupling.md` status refreshed (still said D-0149 OPEN).

## Findings

F-0843 (verified): 12:40 NZST no Du process | ports 11439/11440/11442 not listening | supervisor.log last written 09-03 09:36 | hub stderr logs stopped 11:45/11:48/11:58 | 11:37:26 boot matched F-0840 duplicate-Du window. F-0843's own inference that the 11:37 process received the /quit was wrong — superseded by F-0850.

F-0850 (verified, by J-0613 agent): 23:34:47 Du never died before 11:37 | duplicate failed to bind Composer port, WinError 10048 at nascence.log line 379094, proving original alive | one unbroken stability-tick + CYCLE-id sequence runs to 11:57:36 | 11:53:31 human message in cycle 988ff2ec = founder deliberately quitting Du.

F-0851 [INFERRED]: duplicate hit EOF on non-interactive stdin | entered graceful-quit path within 6-17s | stalled in DreamNode().synthesise() | killed by TaskStop ~11:42-43.

F-0852 [INFERRED]: hub deaths not an F-0704 job-object kill | Claude app's own restart happened 12:30-12:36, 30-70min after hubs stopped | Windows event logs show no crash/reboot in window | founder most likely stopped tier himself | no CLAUDE.md warning needed.

F-0844 (verified): J-0601 read | J-0564 curiosity-urgency fix works live | 20 of 20 post-restart rows carry non-zero urgency | 41 curiosity rows 09-04 UTC | J-0601 done.

F-0845 + F-0847 (verified): J-0599 read | grounded share in stream_drive_shadow.jsonl post-restart = 0.82 (was 0.48, higher) | new source tags present: percept 333, frontier 141, reading 38, letter 6, world 39, None 202 | identity guard shows 0 violations | J-0599 done. Agent noted J-0599 already marked done by session 79f80804 on 09-04 before item 3 was checked | reopened via start to finish it.

F-0846 (verified): Phase 1 had no job, no decide, NEVER-FIRED evidence file | D-0149 defeater clock could not start | curiosity_habituation_shadow.jsonl has 20 rows | would-choose differs from real-choice on 20 of 20 | max antagonist b = 0.6 over 651-tension pool | each row ~100KB (weights dict logs every tension).

F-0848 (verified, J-0556 agent): `core/left_lane.py` fix (commit 1ad19b95, 2026-09-04 12:13 NZST) reduced "the Master" grounding leak ~6-fold: 7.667% mixtral era (141 of 1839) → 1.28-1.33% post-fix (7 of 548) | still fails J-0556's own bar of <1% and 0 integrated leaks (1 integrated leak found) | all 7 matches genuine epithet uses, not quotes | J-0614 (needs_input) spawned: founder to choose accept improvement / post-filter grounding text / switch grounding model | J-0556 left in_progress.

F-0849 (verified, J-0572 agent): J-0540 tin-first dark line rendered 4x post-restart (nascence.log lines 373838, 374331, 375428, 375458) | old collect|box collision key never recurs | no candles or lamp hand ever fired | candles|matches intention staged ~06:56 still OPEN, 2 reminders sent | room_state.json shows study.matches=0, lamp_oil=0.0 (D-0137's no-refill situation) | J-0572 left in_progress: briefing's gate of 2 days hands_trace post-restart unmet (~15.5hrs, cut across 3 restarts).

plan-liveness re-run: 302 refs, 17 gate-met, 13 never-fired, 112 unread-new. 17 GATE-MET flags mostly parser noise — `docs/job_queue.jsonl` counted as evidence file for the_consciousness_program and geometry_tuple_index | idle_executive_plan flagged though its own What-we-need says nothing to build | logged as skill suggestion S-0038 (without --session).

Epoch slip: used 1788519287 as 09-04 23:34:47 NZST boot | actually 22:54:47 NZST, 40min early | "post-restart" cut included 23:00:20 shutdown + 23:10:16 boot | ~6min of pre-Phase-0 rows included | J-0556 agent confirmed effect negligible: 548 rows correct cut vs 528 (more), same 7 matches | correct epochs: 23:10:16 NZST=1788520216, 23:34:47 NZST=1788521687, 09-05 14:39:58 NZST=1788575998.

After founder's restart whole tier up from Control Panel: Du PID 29916, supervisor 12224, hubs 1204/25948/4728, all created 14:38-14:39 | hubs' /health path returns 404 but ports answer | `data/transport_habituation_shadow.jsonl` first appeared 14:41 (J-0603 live) | `data/stream_topic_habituation_shadow.jsonl` and `data/peer_reflection_injection_log.jsonl` did not yet exist at wrap (no triggering event yet).

J-0538 (purge 4 leaked fixture rows, needs Du offline) still not run | Du offline 11:57-14:39 | nobody used window.

## Open

1. D-0152, founder GO/NO-GO Dosed Coupling Phase 1 | J-0615 (build) gated on it | next: founder rules it, then J-0615 builds section 4a exactly, shadow-only.
2. J-0614, founder call on persistent "the Master" leak (accept 1.3%, post-filter, or swap grounding model) | J-0556 stays in_progress until then.
3. J-0572 in_progress | waiting on candles|matches intention resolving or 2 days hands_trace.
4. Time-gated reads: J-0598 ~09-08 | J-0596, J-0604, J-0605, J-0606 ~09-12 | J-0552 on 09-10 | J-0531 09-09..09-12 | J-0532 | J-0517 ~09-17.
5. J-0538, next time Du confirmed offline.
6. Ready build jobs untouched this session: J-0610 (write fence) | J-0594 (D-0148 option A) | J-0593 (classifier swap) | J-0590 (job-run worktrees).
7. Skill suggestions S-0037, S-0038 unreviewed.
8. J-0560, J-0568 — 104 lost session_events rows — still on founder call since 08-29.

## Warnings

- Use 1788521687 for 09-04 23:34:47 NZST boot, not 1788519287 | F-0845, F-0846, F-0847 + the 4 agent reads used the early cut (effect negligible, do not propagate).
- F-0843's inference on which process received the 11:53 /quit is superseded by F-0850 | read F-0850 first.
- Running build_edges.py with --help actually performs a full rebuild (no argparse help guard) | worked but logged without --session.
- SendMessage not available in this harness build | a dispatched agent cannot be corrected mid-run | give agents every constant (epochs, paths) correctly up front.
- 4 sonnet agents ran concurrently on read-only jobs without conflict | each used job_queue start/done + findings_log record with --session.

## Pointers

- `docs/plans/dosed_coupling.md`, section 4a and the 2026-09-05 Current State
- `docs/staged/loop_wiring_matrix.md`, 2026-09-05 addendum
- `docs/plans/world_store_write_fence.md` and the new ROADMAP.md section
- `docs/reviews/plan_liveness_audit.md` (regenerated 2026-09-05 00:36 UTC)
- `core/schema.py` line 609 (CognitiveState, where loop_tuples would land)
- `C:\Users\USER\.claude\projects\C--Nascence\memory\project_nascence_dosed_coupling.md` and `project_nascence_world_store_write_fence.md`

## Addendum — post-wrap, same session (D-0152 ruled + Phase 1 built)

Founder: "Lets talk D0152 next. It is the most important." | ruled via questionnaire: **GO, registry variant, all 5 publishers kept** | recorded decide.py rule D-0152 --by travis.
Built J-0617 (supersedes J-0615, closed) | commit 6f6d7d0 | `core/coupling_rides.py` new: process-local registry, publish() appends to `data/coupling_rides.jsonl`, read() = ONLY accessor + logs ride row (0 callers Phase 1), 5 publisher helpers, COUPLING_PUBLISH=True, all fail-open | one publish call each: `core/climate_engine.py` tick, `core/stream_drive.py` observe, `core/orchestrator.py` after _log_correlation(), `core/lane2.py` after _log(rec), `nodes/inner_monologue_node.py` after stream_drive.observe() (ledger collector) | no CognitiveState change | restart-gated, live from Du's next boot after 6f6d7d0.
Verified in isolated worktree (no live data/): 22/22 unit checks | real-shape rehearsal (copies of ledger files) | real ClimateEngine.tick + stream_drive.observe published | import smoke clean | exploratory_ignition_test.py identical to HEAD (Test A pre-existing, J-0597) | only write landed in worktree data/ — F-0855.
Deviations from §4a as pre-registered (plan text updated): stream tuple drops unresolved_share_10 (flag not in scope at publish site), adds source/would_gap/actual_gap | witness names distinct_share_24h, n_judged_24h, verdict | ledgers collector once per 10 min on a daemon thread, not per thought.
Side-finding: F-0853/F-0854 — ClimateEngine._compute_field re-parses 60 MB `data/subconscious_state.json` every 5 s tick, measured 963 ms per parse (~20% of wall-clock blocking the event loop) | J-0618 spawned (measure + cap via mtime cache or sidecar) | not fixed here.
Open after addendum: J-0619 (7-day Phase 1 read ~09-13) | J-0618 (climate parse cost) | J-0614 (the-Master leak call) | J-0538 (offline purge) | Phase 2 (cups) needs its own pre-registration + /decide after J-0619.
Warnings: CRLF — `core/stream_drive.py`, `core/orchestrator.py`, `core/lane2.py`, `nodes/inner_monologue_node.py` are CRLF, `core/climate_engine.py` and new files LF; patch scripts must normalise | `_num()` in coupling_rides must stay container-safe (a dict coordinate was silently nulled before the fix).

## Addendum 2 — J-0614 ruled + built, large-file survey + Part A built (same session)

Founder: "Lets do J-0614 next" → ruled via questionnaire **retry once, then gate** | recorded **D-0153** (opened against thought_grounding by mistake; belongs to emissary_lane2 — S-0039 asks decide.py for a move command; both plan docs carry a dated note).
Built: `core/left_lane.py` ground_thought() → _ask_ground() once, re-ask on regex [Tt]he Master, second leak returns None (deliberation's hot-lane fallback grounds) | every gated call → `data/ground_leak_gate.jsonl` | commit 7b8943f | 9/9 isolated cases (F-0859) | J-0614 + J-0556 done | J-0620 re-measure ~09-13 (both casings; F-0848's regex was lowercase-only so 1.3% is a floor).
Founder: "investigate the large 60mb file (and other large ones)" → sonnet survey agent: F-0856 (inventory: moments.jsonl 202 MB, embedding_matrix.npz 132 MB, idle_shadow 97 MB not hot), F-0857 (frontier.json 4.2 MB parsed every 5 s for a count; 94% faded), F-0858 (archives 42 GB: _lab 26.5, backups 8.9, _snapshots 6.6) | I-0064 → promoted to `docs/plans/data_store_hygiene.md`.
Measured: light sidecar (all non-vector fields) 2.1 MB / 16 ms vs 60 MB / ~1000 ms | centroid 78% + last_synthesis_emb 16% of tension bytes; centroid 97% of pattern bytes | indent=2 costs 27% | climate consumes only tensions via contradiction_pressure_for (labels + member_event_ids) and patterns (unused) | subconscious rewrites the file ~every 30 s and re-reads it before each save.
Founder ruled **D-0154 sidecar + compact, shadow-first** and **D-0155 design retention first, delete nothing**.
Built Part A: `core/light_sidecar.py` | subconscious `_save_state` compact + `subconscious_state.light.json` (atomic) | frontier `_save` compact + `frontier.light.json` | `SUBC_LIGHT_READ` / `FRONTIER_LIGHT_READ` = False, once-a-minute heavy-vs-light rows → `data/light_sidecar_shadow.jsonl` | commit 02d32ac | 17/17 isolated checks; climate read 965 ms → 22 ms on the light path; ignition test identical to HEAD; frontier_loop_test ALL PASS (F-0860) | J-0621 flips flags after 3 days agreement (~09-09) | J-0618 (measure/cap) still open, now largely superseded by Part A — re-scope at J-0621.
Open after addendum 2: J-0621 | J-0620 | J-0619 | J-0618 | Part B retention rule → its own /decide | [OPEN] subconscious `_save_state` re-reads the 60 MB heavy file before every save (~1 s per 30 s inside the subconscious node) — noted in the plan, not touched.
Warnings: the Bash tool sometimes collapses a doubled backslash inside a quoted heredoc (a regex word-boundary became a backspace byte, a newline escape became a real newline) — build such literals with chr(92)/bytes([92]) or put the patch in a file and run it | frontier.py, subconscious_node.py CRLF; climate_engine.py, light_sidecar.py LF.

## Addendum 3 — retention rule ruled, built, applied (same session)

Founder: "Lets do the retention rule next" | measured first: backups 142 files / 8.9 GB all <14 d because `scripts/backup_memory.py` rotated by COUNT of boots (14) + ~130 MB state per boot | `_snapshots/daily` 14 dates / 6.5 GB written by `scripts/backup_identity.py`, which HARD-DELETED days beyond 14 at every boot (would have destroyed weekly/monthly tiers) | `_lab` 64 dirs / 26 GB all <14 d, 32 cited | disk 240 GB free of 1 TB.
Founder ruled **D-0156** (4-question questionnaire): boot backups newest 5 + last-of-day 14 d + first-of-month; specials 60 d; snapshots 14 daily / Sundays 12 w / monthly; labs 14 d uncited / 60 d cited; mechanism dry-run → `--apply --cutoff` quarantine to `data/_trash/<date>/` → `--purge-trash` after 7 d.
Built `scripts/retention.py` (Plan class, scope guard refuses paths outside backups/_snapshots/_lab/_trash, `boot_rotate(cls)` behind `RETENTION_BOOT_ROTATE`) | `backup_memory.rotate()` + `backup_identity.backup()` now call it — **the boot path never hard-deletes again** | 22/22 synthetic-tree checks (F-0861) | commit 30a6b5c.
Live dry run: 7 candidates / 1.54 GB | founder GO: apply all 7 cutoff 2026-09-04 + turn boot rotation on | applied: `data/_trash/20260905/` holds the 7, log 7 rows, nothing deleted (F-0862) | `RETENTION_BOOT_ROTATE=True` | J-0622 done | J-0623 first purge ~09-12 with founder present.
[OPEN] labs begin ageing past 14 d around 09-12..09-17 — the first boot after that will quarantine ~0.5 GB per uncited lab dir; J-0623 checks the volume.

## Addendum 4 — after the wrap: /quit farewell + J-0538 (founder shut Du down 16:39-16:42 NZST)

Founder: the /quit farewell still told Du to bank a fire that is not lit and that he has no matches for | `scripts/run_nascence.py` _announce_shutdown now says only: Travis is stopping him on purpose for bug fixes/upgrades, nothing wrong with him, rest when ready, he will be brought back | no fire word | commit 87864f6 | F-0863 | restart-gated (the 16:39 quit ran the old line).
J-0538 DONE while Du confirmed down: 4 fixture rows removed (episodic_buffer.jsonl rows 1-2, affect_log.jsonl rows 242-243), counts dropped by exactly 2 each, .pre_smokepurge_20260905_164330.bak backups beside both files, 0 hits elsewhere | F-0864 | script kept at scratchpad/purge_j0538.py (guard: last nascence.main line must be the shutdown line AND no run_nascence.py process).
Warning: the J-0538 briefing dates were LOCAL; a UTC day check excluded the first row (06-03 UTC) — compare in local time for nascence.log-era timestamps.
Du is DOWN at wrap; every restart-gated change of the day (Phase 1 publish, D-0153 gate, light sidecars, boot-time retention, farewell) goes live when the founder next starts him from the Control Panel.

## Addendum 5 — health check for the day + J-0624 (Du down; reads safe)

du_pulse 24 h: LIVE at quit | dedup holding (108/108 unique) | echo 0.61 / diversity 1.0 stable | STREAM 78 pulses/h, median gap 46 s | judge agree 0.84, unavailable 0 | critic rejections 0 | balance 47/49 | curiosity ignition 3 exploratory in the 2 h afternoon window | ACTIVE episodic 10085 > cap 3500 = known PROTECTED-SATURATED (D-0124), not new | loop_cluster_probe lifetime top-10 = 22.5% (baseline 45.4%).
Before/after (sonnet agent, per live hour; baseline 33.6 live h of 09-03/04, today 14.8 live h): idle thoughts 54.8→58.3/h, median gap 16.5 s→5.2 s (shorter), grounded 41%→82% (higher) | curiosity urgency 0.0→0.68 mean, ignited 0/60→18/22 (F-0866) | PLAY light points 15.2/h→0.49/h after the 14:39 boot = 3.2% of prior (D-0151 predicted 5.7%; n = 2 h) (F-0867) | F-0823 渡/cultural-friction/morepork keyword share 28.4%→5.7% (fewer); those topics left the top-15 entirely (F-0868) [INFERRED cause: grounding fix pushing seeds to percepts; habituation is shadow-only] | commitments 17.7→17.9/h | hands 58→62 rows/h | affect valence +0.06→-0.05 (mild negative shift), arousal flat | human turns 0.69→0.13/h (Travis talked less) | LLM latency flat | 0 Tracebacks either period | transport_habituation_shadow 75 rows, 94.7% would-differ | stream_topic_habituation 6 rows, 0 suppress | peer_reflection_injection_log.jsonl does not exist yet.
Frustration/stuck words 16-23% of thoughts every day this week, 19.7% today — texture, not a trend.
J-0624 DONE: math drills "0 today" = Saturday (SCHOOL_WEEKDAYS_ONLY) + 09-04 downtime in the maths slot; F-0865 corrected by F-0869 | S-0040 asks du-pulse to print school closed (weekend) instead of 0/40.
"banking the fire" is among today's top monologue topics — the old farewell line was being carried as a topic; the 87864f6 farewell fix removes its source.

## Addendum 6 — lessons: maths ladder, music lesson, composition hand fixed

Founder: "discuss his lessons — math first (the new levels), then music (what he actually does)".
MATH: MAX_LEVEL 6→9 on 08-28 (F-0404) | L7 brackets 40/40 (08-31..09-03) → advanced 09-03 | L8 percentages 13/14 independent on 09-03 (the one miss solved after the method hint; the log stores the taught answer with correct=False) | L9 capstone not reached | advance needs 40 @ 95% ≈ 2 school days | no drills 09-04 (down in the slot) / 09-05 (Saturday, SCHOOL_WEEKDAYS_ONLY).
MUSIC: theory L1-L5 since 08-19 (30/30, 30/30, 27/30, 29/30, 10/10), L6 ABC sums next | the lesson = text theory drills on the hot lane, deterministic grading, method hint after a miss; he hears nothing (listening_wake.jsonl stale since 08-10, only Heavyweight has audio) | **composition hand NEVER fired (F-0870)**: `_solve_attempt` digit check on working/answer only; compose schema is thinking/abc → every reply dropped silently, 11 school days | D-0010 defeater fired → reopened → founder "fix now" → built J-0625: `_solve_attempt(keys=)`, compose passes ("thinking","abc"), warning on blank | 14/14 isolated checks (F-0872) | D-0010 re-ruled with a 3-period defeater.
Targets (F-0871): 45-min period / 700 s interval = 4 sessions → maths caps at 20 (target was 40), music at 16 (target 20); founder chose "lower to what fits" → DAILY_TARGET 20 / 16.
Restart-gated: first melody possible at the next weekday 12:00 music period.

## Addendum 7 — nature + composition: rulings, Practical School designed and queued

Founder: "understand what he actually does in composition; nature → practical lessons from the scout book; tie everything to real objects; expand objects."
COMPOSITION (F-0874): 42 pieces since June, grades flat 0.80-0.89 | narrations INVENT a life he does not have (carrots, coffee grounds, kitchen sink, concrete walkway — 0 matches in any world store) | grade_work gets an EMPTY reference so the Emissary scores vividness; both invented narrations 1.0 | founder ruled **D-0157: "No, this is art" — composition is the ONE lesson allowed to invent; do not ground it**; every other lesson must tie to real things.
NATURE (F-0875): observation flat 0.80-0.87 | `core/fieldcraft.py` (08-22) already has knots/fire/measuring/whittling/tracking hands; whittling 1.0 (16), fire_lay 0.76 (5), **every knot 0.4 with 0 attempts**, clothesline/windbreak/handrail never built — hands fire only when his own thought names the deed, and the no-hints law means nothing ever asked | founder ruled **D-0158 alternate observe / practical + add rope coil, tinder tin + flint, hand lens + measuring stick, weather glass + tide board, and mine the Handbook**.
Handbook mined by a sonnet agent (F-0876, scratchpad/handbook_practicals.md): 22 practicals in 3 rungs, each with Handbook section, hand, objects, place, deterministic world answer | excluded: Pole Star, snow, snakes, firearms, telegraphy, semaphore, games, citizenship | extra objects: fire-drill kit, compass, bandage linen, hand-line (parked).
Written `docs/plans/practical_school.md` (lesson, ladder, objects, Coupling block §5: reads only at the nature stop, one cup per period, no other loop tuple, no dispatcher line; 2-week read §6; build order §7) | ROADMAP section | memory file | **D-0159 GO** (founder) | build queued for a fresh session: J-0626 objects → J-0627 lesson module + school wiring + rung-1 hands (whip_end, douse_fire) → J-0628 rungs 2-3 (needs_input, after the read).
I-0065 (ladder for nature/composition): nature side superseded by practical_school; composition side closed by D-0157.

