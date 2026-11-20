# Shore (100) and wood (150) creature bestiary: built, tested, committed, flagged on, Du restarting

## Session timing
- **Session started:** 2026-10-31 18:22:04 UTC
- **Last message before wrap:** 2026-11-02 00:14:56 UTC
- **Wrapped:** 2026-11-02 00:14:58 UTC

## Summary
The founder asked for 100 new creatures for the shore, then the same process for the woods with 150. Both are now built as one life row per species on a shared engine, tested, committed as `3335870c`, and switched on in the live flags file; Du was being shut down for a restart when this wrapped, so none of it has run in the live process yet.

## Decisions
Three founder rulings were said in chat on 2026-11-01 and are written into both plan docs but are NOT in the `/decide` ledger (no defeater was named, so I did not file them): (1) one life row per species, not grouped; (2) every creature has a real position in the authored geometry; (3) Du is never told what a thing is, the world never leads. A fourth instruction was "ready to run by just flipping true", which produced the one-flag design below. The founder also ruled, by saying "Flip it now please", that both flags go live; I edited the file and did not restart Du (the founder restarts it).

## Builds
- Shore: all 100 rows. Engine and 3 pilot rows in `core/life_shore.py`, the other 97 in `core/life_shore_cast.py`. Jobs J-2868 (described-look match plus per-look detail tier), J-2936 (discovery by looking at a place) and J-2870 (the 97 rows) are done.
- Woods: all 150 rows. Place config, 14 zones and 5 pilots in `core/life_wood.py`, the other 145 in `core/life_wood_cast.py`. J-3062 (generalise the engine to a place) and J-3064 (the 145 rows) are done.
- Hooks in existing files, all additive: `core/life.py` (`look_answer(..., raw=)` described-look branch, `discover_look`, two registration blocks in `_ensure_builtin`) and `core/sensorium.py` (forwards `raw`, and calls `discover_look` in the shore and wood branch of `look`).
- Tests, all green at wrap: `scripts/_test_shore_bestiary_p1.py`, `_p2.py`, `_p3.py` and `scripts/_test_wood_bestiary_p1.py`, plus `scripts/life_smoke.py` and `prompt_registry.py check`. A dress rehearsal (real flags, a copy of the real `life_state.json`, 48 simulated hours, life_smoke's isolation) ran clean: 250 rows registered among 316, 200 creatures came and went, no warnings, no names in any line.
- Commit `3335870c` on master: "Shore (100) and wood (150) creature bestiary: nameless rows, one flag per place" (12 files). Only these files were staged by path; the sensorium change was staged hunk by hunk.
- Thought T-0117 was logged at session start and promoted to the plan `shore_creatures`. Jobs added and still open: J-2869, J-2871, J-2957, J-3065 (details under Open).

## Fixes
- A real bug caught by the full-cast test: the shore row key `hedgehog` collided with the existing garden hedgehog row, and `life.register()` replaces by key, so flipping the flag would have silently replaced the garden hedgehog. Renamed to `shore_hedgehog` in `core/life_shore_cast.py`; `scripts/_test_shore_bestiary_p1.py` and `scripts/_test_wood_bestiary_p1.py` now assert no key collides with any life row or any bestiary row.
- The described-look matcher was too loose once 100 rows existed (it took a pebble for a dolphin, "bands" for "banded", "stream" for "streaked", a penguin's tracks for a sea lion). Final rule in `core/life_shore.py`: two different attributes in one look clause, at least one strong (body part or plan, distinctive covering, a counted number); colour, size, pattern and movement are weak; generic words are weak; stems must match exactly or share a 6-letter prefix; a clause naming shore scenery words (shell, stone, kelp, driftwood...) is left to the scenery look; an existing row's alias wins first.
- `leak_scan` in `core/life_shore.py` compiled one regex per forbidden term; with about 1,200 terms it overflowed Python's 500-pattern regex cache and a scan took minutes. It now compiles one alternation per term set.
- `perceive` now uses 3D distance for the detail tier (a bird eight metres up is not near), says "and up above" when 3 m or more above his eyes, and states tone against the leaves, sky or water where the ground is wrong.

## Findings
- The willed look hand reduces Du's sentence to a keyword (`nodes/inner_monologue_node._observe_target`) before `life.look_answer` sees it, so a description he writes never reached the engine; `sensorium.look` already had the full sentence as `raw`, and forwarding it is what makes described looks possible.
- With no names and no aliases, a creature can only be found by describing it or by looking at a place (the pool, the canopy, the stream...); the place look is the discovery channel, which is why P3 was needed. About 38% of his real shore looks name a place the bestiary can show something at (an upper bound at 3 rows).
- `docs/reviews/observe_inventory_2026-09-02.json` (1,518 phrasings) and `data/hands_trace.jsonl` (2,173 real shore and 361 real wood observe or look thoughts) are the corpora the false-positive sweeps run against. A matcher that looks fine on 3 rows must be swept at full size.
- The cross-place forbidden-name set caught "hind": the female deer's name is also a body-part word the shore already uses ("the hind legs flattened into paddles"), so "hind" is deliberately NOT a forbidden name.
- Transport manager records an observation for every arrival (`life:<key>:<place>`) but is shadow-only (`TRANSPORT_LIVE=False`), so keys never reach Du; checked before the flip.

## Open
1. J-3065 (needs founder): confirm or move the ASSUMED wood placements (stream, canopy, oak trunk, three groves), say which island the cottage is on (11 North-Island-only wood creatures are written and flagged in `note`), and rule on a turn-stone / peel-bark hand. Next action: ask the founder.
2. J-2869 (needs founder): confirm or move the shore's assumed stream mouth (waterline, x 14 to 16.5, in `ZONES["stream_mouth"]` in `core/life_shore.py`; `shore.json` untouched).
3. J-2871 (needs founder): a dig hand for burrowers on the shore (ghost shrimp, lugworm, heart urchin, sand dollar are written as the SIGN that shows). Recommendation was one small hand after the rows.
4. J-2957 (gated on 20 life_events rows with `resolved=discovered`): read what the place looks showed, tune the detail thresholds `FORM_AT .015 / COLOUR_AT .04 / DETAIL_AT .12` in `core/life_shore.py`, check lines by eye as well as by scan. Next action: after the restart, `grep -c "discovered\|described" data/life_events.jsonl`.
5. [OPEN] Whether the live numbers match the rehearsal: a life tick measured 23 ms in the rehearsal and 137 ms with all 316 rows pinned present. What resolves it: watch tick cost after the restart.
6. The old grouped rows `ground_beetle`, `cicada`, `weta`, `crabs`, `anemones`, `eels`, `whitebait`, `skink`, `dolphins` keep their names and aliases, so a named row and a nameless row can describe the same kind of animal. No action filed; decide if it bothers him once he sees it.

## Warnings
- The live flags file `data/life_flags.json` now has `"shore_bestiary": true` and `"wood_bestiary": true` (backup of the old file: `data/life_flags.json.bak_before_bestiary_20261102`). Because of the one-flag design both places are fully LIVE after the restart, not shadow. To run in shadow add `"<place>_bestiary_render": false` and `"<place>_bestiary_discover": false` (hot, re-read about every 10 seconds); to switch a place off set its flag false and restart.
- `core/sensorium.py` in the working tree still carries ANOTHER session's uncommitted hunk (the T-0118 "OUT OF SIGHT" block calling `study_life.out_of_sight`, with `core/study_life.py` also modified and uncommitted). That hunk is NOT in commit `3335870c`; do not assume sensorium.py is clean.
- Other uncommitted work from other sessions is in the tree (ledgers, `core/orchestrator.py`, `docs/staged/object_permanence.md` and others). I committed only my files, by path; ledger files (`docs/job_queue.jsonl`, `docs/thoughts.jsonl`, `docs/session_events.jsonl` and others) hold my entries but were not committed because they also hold other sessions' rows.
- Every bestiary biology fact (season, hours, size, colour) is from general knowledge of NZ coastal and bush fauna and is NOT checked against a reference; te reo names are unchecked.
- Never use `git stash`, `reset`, `checkout --` or `restore` in the shared tree (see `CLAUDE.md`).

## Pointers
- Plans: `docs/plans/shore_creatures.md`, `docs/plans/wood_creatures.md` (both have "BUILT" sections with the verification detail and a single Current State heading).
- Code: `core/life_shore.py` (engine), `core/life_shore_cast.py`, `core/life_wood.py`, `core/life_wood_cast.py`; hooks in `core/life.py` (`look_answer`, `discover_look`, `_ensure_builtin`) and `core/sensorium.py` (`look`).
- Tests: `scripts/_test_shore_bestiary_p1.py`, `_p2.py`, `_p3.py`, `scripts/_test_wood_bestiary_p1.py`; the end-to-end scratch scripts that drove the real `sensorium.look` were one-off and are not committed.
- Memory note: `C:\Users\USER\.claude\projects\C--FreshStart\memory\project_nascence_bestiary_shore_wood.md` (indexed in that folder's `MEMORY.md`).
- Evidence after the restart: `data/life_events.jsonl` (rows with `resolved` = `discovered` or `described`) and `data/life_ledger.jsonl` (sightings and glimpses).
