# The cat overhaul: audit of both cats, staged plan, her voice built in shadow

## Session timing
- **Session started:** 2026-09-05 07:51:54 UTC
- **Last message before wrap:** 2026-09-05 08:26:04 UTC
- **Wrapped:** 2026-09-05 08:26:05 UTC

## Summary
Founder ask T-0050: "Next one we look at overhauling is the cat. It has lots of problems. Bring it up to date and then take it into the future. Both of them" | read as grey companion cat (core/cat.py) + founder's distant black cat (cat.py:629-680) | audited core/cat.py against code, live state, 8 days of nascence.log | wrote docs/staged/cat_overhaul.md (Part A up-to-date, B future, C sounds) | opened 4 founder decisions | queued 4 fix-now jobs | founder second direction: "Sounds. Pin sounds to the cat, then Du one day can call the cat; it can hear birds and react; stop the cat interacting as much so Du must seek her out" | designed Part C, built C1 (her voice) in SHADOW | all committed 76a976f at founder request | other jobs stay on the board.

## Decisions
4 opened, 0 ruled | D-0160 naming deadlock (keep companion tier locked behind the name + build referent pressure / unlock from bond / both) | D-0161 mortality + harm for her (extend D-0130 to her: yes / not yet / never) | D-0162 black cat future (far-off shape / real tom that comes into the garden / plus kittens) | D-0163 real cat food + saucer object, folded into write-fence build J-0610 | D-5 (name as learned sound with range) + D-6 (availability target) held in plan doc, NOT opened — founder said "not yet" | [OPEN] "not yet" read as "keep designing, don't rule"; could instead be an answer to D-0161's not-yet option.

## Builds
Part C1 "her voice" BUILT, SHADOW (F-0889) | core/cat_sounds.py (new) emits 8 sounds from her state: cat_trill on greeting stamp | cat_meow_at_door 30/h while "at the door, asking in/out" | cat_demand 20/h while demanding_food | cat_chatter 12/h at windowsill, only when life.sounds_active("garden") has a bird voicing | cat_yowl_cargo + cat_thump once per state transition | cat_lapping for 120 s after a feed | cat_storm_rustle while storm_hide | each carried to his position by reach × wall × weather (door open 0.7, window open 0.6, shut 0.3; rain 0.8, wind 0.75, hard wind 0.5, thunder 0.4) + distance/bearing from soundscape.propagate_historical_acoustic_event | every emission logged to data/cat_sound_ledger.jsonl as kind="would_sound" with exact line from new cat_content.SOUNDS corpus (here/carried pools) | nothing reaches active_sounds / census / percept rail / his prompt until data/life_flags.json cat_sounds_render is true | flip: `python scripts/life_flags.py cat_sounds on` (hot, no restart) | core/soundscape.py: +8 Sound-Space points on "the kept cat", rates in _EVENT_RATES, 2 beds, last-row _sec_cat returns [] in shadow | core/cat.py: +1 fail-open call to cat_sounds.tick before its 180 s gate | scripts/life_smoke.py redirects the new ledger | verified: isolated 33-check test (scratchpad test_cat_sounds.py, every store redirected, every world read stubbed) + scripts/life_smoke.py ALL OK | live ledger file absent after both runs | restart-gated: Du awake since 19:15 local throughout | [INFERRED] first would_sound rows appear at his next restart | commit 76a976f: core/cat_sounds.py new, core/cat.py +9, core/cat_content.py +91, core/soundscape.py +48, scripts/life_flags.py +11, scripts/life_smoke.py +1, docs/staged/cat_overhaul.md new, the ledgers.

## Findings
F-0879: half her life never fired in 73 days | phase "companion" set only by the naming latch (cat.py:802) | unnamed since 2026-06-24 (name_invited since 07-01) | never run: felt_note()/FELT corpus, slow blink, silent meow, gone_missing arc, 6h-absence line | 0 naming attempts in log since the 08-19 R1 reset
F-0880: tending is a vending machine | react() fires on bare she/her + hold/approach while co-located | 375 fires since 08-29 (33-73/day) on 23 distinct lines | sampled triggers include a library request about ghosts | bond capped 1.0, no cooldown, sleeping cat not refused
F-0881: "hungry" ~52 h while tended ~110 times, only 7 feeds (far fewer) | no cat food in provisions.json, carrier list has no food line — "You feed the cat" conjures a meal | same leak class as matches before F-0877
F-0882: life.py _cat_presence (life.py:876-884) maps lap/desk/mantel/indoors/doorstep/shore/wood/away_hunting all to "garden" | threat_active uses a second, different mapping | life_events.jsonl shows departed-garden + arrived-study at identical timestamps
F-0883: 436 dead cat traces with 2027-clock IDs (created 2026-08-17 by a test against the live store) immortal in world_traces.json — advance_trace_decay continues on clarity<=0 before the delete | 482 of 496 traces are hers
F-0884: black cat 345 sightings, 0 naming pressure | Du uses it as metaphor
F-0885: she teleports (no legs) | no hunger/energy/warmth budget, no age, no death | D-0130 harshness applies to everything but her
F-0886: HUD garden map pins her at the raised bed | seen_count 0 forever yet reported by status()
F-0887: calling her is currently a stroke ("call to" in _TEND_VERBS, cat.py:753)
F-0888 CORRECTS F-0887 second half: propagate_historical_acoustic_event has 1 caller (storm-surge sound, sensorium.py:228), not 0 as F-0887 said
F-0890 [INFERRED]: cat._ZONE_POSITIONS is a per-place frame (shore 8 m from study, wood 45 m), not a world frame — so cat_sounds keeps its own chain frame
Live read 2026-09-05: phase kept | bond 1.0 | last_fed 09-03 15:47 UTC | last_tended 09-05 07:30 UTC | distant.seen_count 345 | cat named in 5-12% of daily monologue lines (under D-0130's 20% monoculture line)
Toolchain gap: findings_log has no amend/retract subcommand | S-0042 filed

## Open
1. D-0160..D-0163 wait on founder | D-5/D-6 in plan doc not opened (founder: "not yet") | next: founder rules, or /decide-review.
2. Fix-now jobs, no ruling needed, ready: J-0629 (one cat-to-place mapping in life.py from cat._VISIBLE) | J-0630 (purge the 436 immortal traces + one trace per visit + find the test that faked now) | J-0631 (narrow react() triggers, tend cooldown/satiety, sleeping-cat refusal, recency exclusion in _pool) | J-0632 (HUD position, seen_count) | founder chose to leave them on the board | next: nurse round or job-run.
3. J-0633: after Du's next restart read a week of data/cat_sound_ledger.jsonl (per-key rates, audible share by his place + by why, 30 carried lines by ear) | wire new keys into soundscape._PERCEPT_LINES/_PERCEPT_SOUNDS via cat_sounds.line_for | then flip | [OPEN] seed takes the ledger line directly vs the percept rail — decide at flip time.
4. [OPEN] [INFERRED] expected: while she stays unfed (F-0881) cat_demand dominates the shadow ledger until D-0163 gives him food — instrument reporting truthfully, not a bug.
5. Plan-maintain at wrap filed J-0634 (ROADMAP link backfill for cat_overhaul) — done at wrap, see Warnings | 19 plans still without Current State (pre-existing punch list).
6. Designed in docs/staged/cat_overhaul.md, not built: Part B (her body, legs, food, mortality) | C2 (her ears) | C3 (the call, name as learned sound) | C4 (less of her / seeking) | the tom | build order in its §5.

## Warnings
Changed this session, committed 76a976f: core/cat.py, core/soundscape.py, core/cat_content.py, scripts/life_smoke.py | sessions with older in-memory copies: re-read before editing | cat_sounds.tick keeps process-local transition memory (_mem) — a restart forgets one thump, never invents one | cat_sounds.py _POS/_HIS chain frame is its own; do not "fix" it to match cat._ZONE_POSITIONS (F-0890) | scratchpad test_cat_sounds.py redirects every store + stubs every world read; never run cat_sounds against live data without those | module itself writes only its own ledger, but locomotion.get_position would write position.json — module uses peek() for that reason | 60 s sample + 90 s audible window are module constants (_SAMPLE_S, _AUDIBLE_WINDOW_S) | never git stash/reset in the shared tree (CLAUDE.md rule) | ROADMAP.md gained one bullet for staged/cat_overhaul.md at wrap (J-0634).

## Pointers
- docs/staged/cat_overhaul.md (Parts A/B/C | §4 decisions | §5 build order | Current State)
- core/cat_sounds.py | core/cat_content.py (SOUNDS) | core/soundscape.py (_sec_cat, the 8 points) | core/cat.py (tick hook)
- scripts/life_flags.py (cat_sounds on|off) | data/life_flags.json | data/cat_sound_ledger.jsonl (after next restart)
- scratchpad test: C:\Users\USER\AppData\Local\Temp\claude\C--Nascence\649d6850-8558-4e13-8930-38ac5b6da170\scratchpad\test_cat_sounds.py
- docs/completed/cat_system_audit.md (2026-08-18 prior audit) | docs/plans/capacity_to_commit.md (R1) | docs/plans/living_world_upgrade.md | docs/plans/sound_world_expansion.md §2/§5 (cat entries, distant_yowl)
- memory: C:\Users\USER\.claude\projects\C--Nascence\memory\project_nascence_cat_overhaul.md
