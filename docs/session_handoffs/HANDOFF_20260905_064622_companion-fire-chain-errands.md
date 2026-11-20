# Companion fire chain: Travis lights the fire through Du's own mechanisms, with errands

## Session timing
- **Session started:** 2026-09-05 05:50:59 UTC
- **Last message before wrap:** 2026-09-05 06:46:17 UTC
- **Wrapped:** 2026-09-05 06:46:22 UTC

## Summary
Founder ask (T-0049): composer "Light the fire" button must work with house at 0 matches, Travis carries own box + leaves it | escalated to "go all the way": no kindling: he fetches some; no wood: he fetches it; all via the same mechanisms Du would use | core/companion.py rewritten around errand system, Travis walks Du's own legs to Du's own stocks | verified by isolated 8-scenario test (F-0877, F-0878) | Du down whole session (nothing listening on composer port 8765); change lands on next start [INFERRED] | nothing committed.

## Builds
- Travis's match box (F-0877): study.matches 0: core/companion.py `_travis_leaves_matches()` adds ONE full box (50) via provisions.add, origin "travis", own biography line | moves it cupboard position→mantel [0.45, 2.0, 1.4] beside tin | logs left_by_travis event in provisions_log.jsonl | sets study.matches from shelf | strike consumed from that box by provisions.sync() on next study read, same path as Du's strikes | only Travis does this; study_life untouched, Du's hands still find tin empty until Travis leaves one | all 6 larder boxes in data/provisions.json already empty 2026-09-05; fires on very next empty-tin fire [INFERRED].
- Whole fire chain (F-0878): `_light_fire()` in core/companion.py mirrors sensorium.act('light') lines 2871-2905 step by step | banked embers alive (fieldcraft.banked_alive): uncovered w/ handful of kindling, no match, fuel 0.8 | no kindling: tied bundle from cupboard (kindling +0.5, mirrors provisions.open_kindling_bundle, history "untied and used by Travis"), else twigs+bark with deadfall from wood (+0.35) | no wood: dry logs split on block at lean-to if logs_dry >= 1 AND axe at garden AND axe_edge >= 0.15 (up to 3 logs, edge reduced 0.08, chips add +0.15 kindling, mirrors wood_life.split lines 430-458); else deadfall from wood (3 loads, 4 when gusty, taken from wood_life.json finite deadfall stock, gale replenishes; wet +0.4 in rain; wood_snap_ts stamped); else driftwood off shore (2 loads, 3 when gusty, wet +0.4) | choked grate (ash > 0.85): cleared into bucket first if ash_bucket + hearth_brush to hand in study, else fire smoulders out, match + kindling spent, same as Du's | wet_wood > 0.5: fuel 0.7 + sullen-smoke narration | hand_lit set True, fire dies only of own fuel like Du's hand-lit fires (before: Travis's fire died at daylight, hand_lit never set).
- Errands: any shortfall needing Travis's body elsewhere = errand persisted in data/companion_state.json under "errand" (stages w/ absolute timestamps, haul, need, notes, then) | legs via locomotion._leg_secs w/ current weather + wind, 1.3x longer when loaded, along study-garden-wood-shore chain | `_advance()` runs due stages, called from every entry point (perform_action, set_present, presence_line, consume_witnessed_event, status); errand completes on whichever of Du's ticks / Travis's buttons reaches it first | shore fallback decided on arrival in wood if deadfall < 1.0 | haul lands on woodpile only on home stage (wood_haul_ts stamped; kindling + wet carried into study box), then carried-through intent runs: `_light_fire(allow_errand=False)`, honest failure if need still unmet | while out: other buttons refuse w/ ETA; "I'm away" refuses; presence_line tells Du where Travis is heading; witnessed events queue in list, joined on consume | measured ETAs, calm weather: wood trip ~259 s, shore fallback ~481 s, lean-to split ~45 s; wind+rain wood trip 363 s (longer than calm 259 s).
- fetch_wood button: no longer conjures 4 loads; runs same errand (refuses if woodpile >= 3).
- scripts/run_nascence.py composer bridge: new `{"type": "status"}` message answered w/ companion.status() (present, errand, eta_s, errand_line, last_narration, pending_event) | scripts/du_composer.py polls every 10 s while errand out, shows "back in about N min", then return narration | docstring updated.

## Fixes
- 2 defects caught by test, fixed before writing | (1) out-phrase read Travis's starting room ("on his way in") not destination; now derived from next non-arrive stage | (2) ETA counted outward legs only; now `_project_return()` adds loaded return legs, recomputed on shore fallback.

## Findings
- Du's own hands (sensorium._gather_wood, wood_life.split, provisions.open_kindling_bundle, fieldcraft.uncover_fire) read Du's location, narrate in Du's voice; wood_life._log "deed" key cross-links into core/activity_memory | calling them for Travis would make Travis's gathering something Du remembers doing [INFERRED] | companion.py re-states each mechanism at primitive-store level, source line cited at each site; writes wood_ledger.jsonl rows as gather_by_travis / driftwood_by_travis / split_by_travis, no "deed" key | verified in test: every wood ledger row lacked "deed".
- Study counts = views over provisions objects; provisions.sync() runs on every study_life._st() call; bare count bump (matches, kindling from bundle) erased on next read; object must exist | reason match box + bundle both go through provisions.json.
- Single shore haul adds wet_wood 0.4, below Du's 0.5 wet threshold; one driftwood trip still a clean fire; two would smoke [INFERRED] | mirrors Du exactly.
- Live state at wrap: woodpile 37 | kindling 1.0 | matches 0 | wet_wood 0.998 | deadfall 0.0 (picked clean) | logs_dry 0 | limbs 2 | banked embers ok from 2026-09-04 | ash 0.178, bucket already full | first empty-tin fire uses Travis's box, no trip [INFERRED] | wood errand today would fall through to shore [INFERRED].
- findings_log.py record warns AFTER writing when --session missing, says re-run; re-run creates duplicate F-id | hit on F-0877 (logged w/o --session; absent from this session's rollup, as is S-0041) | suggested S-0041 against findings-log: refuse before writing, or add tag-session subcommand.

## Open
1. [OPEN] Live run of chain not observed; Du down all session | next: start Du, mark present in composer, press "Light the fire" w/ tin empty, confirm box on mantel in data/provisions.json (origin travis) + narration reaches Du's idle tick as "Right now:" seed; then force woodpile low, watch errand complete across ticks.
2. [OPEN] Nothing committed: core/companion.py, scripts/run_nascence.py, scripts/du_composer.py, docs/plans/world_store_write_fence.md + ledgers uncommitted in shared tree | next: founder or a session asked to commit stages those 4 paths explicitly.
3. [OPEN] T-0049 still OPEN in thoughts.jsonl; built directly, no plan doc | next: drop w/ --why "built, F-0877/F-0878", or promote to plan slug if Companion plan doc gets written.
4. Write-fence success condition (docs/plans/world_store_write_fence.md, Current State) amended: Travis's companion rows named legitimate movers of study.matches, woodpile, wood_life.json deadfall/logs_dry/axe_edge, provisions kindling bundles, fieldcraft banked, study kindling/wet_wood/ash | [OPEN] J-0610 build should honour companion.py as live-process writer (runs in-process in run_nascence.py).

## Warnings
- core/companion.py fully rewritten this session; any concurrent session editing it will conflict [INFERRED] | perform_action signature + presence/witness read channels unchanged | consume_witnessed_event now returns all queued events joined w/ spaces (was single string).
- companion_state.json gained "errand" + "last_narration" keys | errand persists across Du restart, completes on first `_advance()` after start (stale timestamps simply due).
- Scratchpad test scripts redirect every store path + stub provisions._register | do not run against live data w/o those redirects (world_substrate + world_objects = live stores _register writes).
- plan-maintain ran at wrap (--session tagged): 55 open jobs, 47 ready, 8 needs-input, 18 plans still without Current State (pre-existing punch list, not from this session).

## Pointers
- core/companion.py
- scripts/du_composer.py
- scripts/run_nascence.py (composer bridge, status branch)
- core/sensorium.py:1746-1905 (Du's wood loop), :2871-2905 (Du's light act)
- core/wood_life.py:392-458 (deadfall stock, saw, split)
- core/provisions.py (larder objects, sync, open_kindling_bundle)
- core/fieldcraft.py:200-247 (bank / banked_alive / uncover)
- core/locomotion.py:39-50, :183-200 (legs + weather stretch)
- docs/plans/world_store_write_fence.md
- data/companion_state.json, data/companion_actions_log.jsonl
- scratchpad test scripts: test_travis_matches.py, test_errands.py (session 1c211fa9-02f4-4827-87fd-ba12105726d2 scratchpad)
