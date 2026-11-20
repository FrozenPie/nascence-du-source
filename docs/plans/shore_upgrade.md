# The Shore Upgrade — the tide drives it

*2026-08-22, founder: "now time for the shore… make his world as alive as possible… his hands usable for many, many things… world
events as realistic as possible, grounded in facts… a wealth of things to find from his previous observations." Built the same day:
`core/shore_life.py` (restart-gated).*

> **Status: 🟢 LIVE — built 2026-08-22 (`core/shore_life.py`); every feature in
> §1 exercised and verified in isolation (§2) — sand-flat writing, wading, swimming, skipping, the
> cairn, the beach fire, the cave's tide-gating, mussel/pool gathering, kororā/seal/sea-sparkle
> clocks, the bottle mint. The old "restart-gated, not yet confirmed firing on its own" caveat is
> RESOLVED (2026-09-02, J-0421/F-0553): `data/shore_ledger.jsonl` holds 6 real live deeds,
> 2026-08-24 12:32 → 2026-08-29 00:32 UTC (walk_sand/wade/skip/swim — see the Current State note
> below). One open overlap with `generative_world_sedimentation.md` (§3) is still unresolved.**

```plan-state
stage: live
phase: Live; only 5 of 10 deeds used in 5 weeks (cairn/sand-writing/beach-fire/cave/penguins idle)
verified: 2026-11-13
evidence_read: 2026-10-16
next: Settle D-0455 and J-2295; shore deeds recover only if voice move acts do
cluster: 6
```


**Current State — verified 2026-08-24 (J-0060 / F-0180):** genuinely case (a), not a wiring bug.
Wiring confirmed real at all 3 call sites — `shore_life.advance()` fires every world tick
(`sensorium.py:2803`), `act_from_thought()` fires from the live monologue-action path
(`sensorium.py:1497`) and is registered as `dispatch.py:126`'s `Hand("shore", ...)`. But zero of
the 10 hand-deeds (walk_sand/write_sand/wade/swim/skip/cairn/beach_fire/enter_cave/climb_ledge/
gather_shellfish) have fired in the ~44h since build: the code's own accruing logs
`data/shore_events.jsonl` and `data/shore_ledger.jsonl` do not exist on disk yet (zero bytes
written); `data/shore_life.json`'s deed fields are all still zero/null while its clock-only
fields (swell, `_last`) are live and ticking; `data/memory/nascence.db`'s independent
`activity_memory` layer shows 0 of 2285 `origin='action'` rows matching any shore-deed name;
`data/nascence.log` shows 0 `ACT <deed>` lines and — tellingly — 0 monologue mentions of
wade/swim/cairn/beach fire/the cave/the ledge/mussel/skip stones since 2026-08-22, meaning Du
hasn't even thought toward these hands yet despite ~100+ shore visits in that window. Not a
phrase-match bug (there's no attempted phrase to mismatch) — just genuinely too early. Secondary,
now fixed: the plan previously never cited `data/shore_events.jsonl` / `data/shore_ledger.jsonl`
by path, so `plan-files-audit`/`plan-liveness`'s backtick-driven extractor had nothing to find
even once they do start accruing — cited below so tracking picks up automatically. Re-check once
Du has actually tried one of the ten deeds.

**Real accruing evidence files (cited for `plan-files-audit`/`plan-liveness`, per F-0180 — both
correctly MISSING right now, that is the honest state, not a bug):** `data/shore_events.jsonl`
(clock/deed events: sand_writing_erased, cairn_knocked_down, beach_fire_drowned, seal_hauled_out,
oystercatcher_nest, storm_buried_items, latent_item_revealed) and `data/shore_ledger.jsonl` (every
hand deed: walk_sand, write_sand, wade, swim, skip, cairn, beach_fire, enter_cave, climb_ledge,
shellfish). `data/shore_life.json` is STATE (current snapshot), correctly excluded from evidence
counting by `plan_liveness.py`'s own STATE-vs-evidence rule — not a gap.

## Current State — verified 2026-11-13 (F-1995; J-1439 queued)

- **2026-11-13** (F-4425): J-3527: _DEST_SHORE gained stream-mouth cues (replay: 0 wood false positives, 3 wrong garden moves fixed); built on branch jobrun/shore_upgrade 04dfe252, restart-gated.
- **2026-11-05** (F-3950): J-3260 (D-0651): stream mouth built on branch jobrun/wb_world, commit 48e42c6d, not merged. ZONES stream_mouth is a disc r 2.0 on a new shore.json feature at (15, 7); run scripts/apply_shore_stream_mouth_j3260.py --write on the live shore.json before the restart. spatial.render unchanged at all 13 standpoints.

- **2026-10-17**: D-0455 ruled (a) by Travis 2026-10-17: the move collapse is accepted as boredom calibration (F-3007, F-3022); no re-enable, no new gate, no affordance nudge; defeater on weekly deeds / new-content rate.
- **2026-10-17** (F-3022): J-2312/F-3022+F-3023 (D-0455 evidence pack): pre-boot shove moves (35%) gave no extra deeds/new content and cost ~7 pts of reading/writing; post-boot moves give 10x longer visits; since the 10-09 edge gate the note is 0.6% of prompts whatever COH/ESC are, so only the gating choice (edge vs persisting-while-stuck) restores walking; 4 options in F-3023, Travis rules.

- **2026-10-17** (F-3007): J-2295/F-3007: the 09-28 19:08 move-act collapse is the boredom recalibration (J-1362/J-1366), NOT the idle-seed flags (seeds do not raise moves); boredom note 88%->1.4% of idle prompts, move 38.8% with note vs 6.3% without; D-0455 should be re-read on that basis (the old rate was a miscalibrated shove, F-1921).
- **2026-10-17** (F-2991): F-2991: shore collapse is a Du-wide voice move-act collapse from the 09-28 19:08 boot (not shore-specific, not 10-09); shore hand intact; cause inferred (D-0292 idle seeds off); D-0455 opened, J-2295 spawned.

- **2026-10-16** (F-2906): 2-week deed-diversity re-check: still 5 of 10 deeds ever used; but shore activity collapsed in October (deeds/week 10 -> 0-2, shore FIRE 58 -> 4, shore presence halved while total hands rows held) during a period Du was up. J-2209 reads the 10-09 boot as the first suspect.
- **2026-09-28** (F-2155): J-1568/F-2155: audited cairn, sand-writing, cave, beach-fire against life.py and every sibling life/knowledge module -- no parallel mechanism exists anywhere for any of the four, and each already has its own real live shore_life.py hand (not a dead counter like penguins/dolphins were), so no new hand should be built for any of them.

- **2026-09-28** (F-2092): J-1441 (living_world_upgrade, F-2092): the shore is both the top declined-move source (63 cross-place requests: 38 to the wood, 25 to the garden) and the top within-place-feature target, with sea 97, tide 88, shingle 36, and surf 5 totaling 221 of 569 within-place misses, the largest single-place slice. Decide question D-0319 is open on whether to build a sub-place standpoint move for these.
- **2026-09-28** (F-2083): J-1439 read data/hands_trace.jsonl in full (25,864 rows) and shore_ledger.jsonl/shore_life.json/shore.json, 14-day window 09-13->09-27 (8,056 cycles). Shore-family dispatch: STAGE-place 59, hand-declined 88, FIRE 20, DROP-weak-intent 5. Code trace (dispatch.py + shore_life.py) shows hand-declined structurally cannot mean tide-gated or weak-intent or off-shore (those are separate decision values / always return a truthy refusal string) -- it is "no matching object": literal_will's coarse family table waves an object through, shore_life.py's own strict clause-scoped grammar correctly rejects it (objects: sea 34, cliff 22, fire 14, stones 13, sand 2, stone 1, fish 1). Idle-deed thought-reach in the same window: cairn 0, sand-writing 0, cave 0 (never-willed, hands untouched, not refused), beach-fire-shaped language 2x but never the required "driftwood fire" phrase (deliberately narrow by design), penguins 73x (by far the most-narrated) against zero hand of any kind -- the one CONFIRMED unreachable-by-hand feature. Deed-per-week (shore_ledger.jsonl, 31 rows total): wk1 6, wk2 5, wk3 8, wk4 6, wk5 6 -- steady, but climb_ledge alone is now 15 of 31 (48%) and dominates the most recent rows. STAGE-place(shore) follow-through (F-2084, inferred): of 59 staged, only 5 later show a shore FIRE after arrival; 44 arrive without converting; 10 never return to the shore in-window -- same grammar-mismatch pattern, not simple neglect. Full detail: F-2083 (verified), F-2084 (inferred). Build job spawned: J-1525 (give the penguin sighting a hand, mirroring the existing seal/whale/dolphins bookkeeping -- no hints to Du, only registering what he already independently narrates).

### What we have
- Live since 2026-08-22 (`core/shore_life.py`); the most-visited place (19-57% of daily experienced
  tuples) and the only one with a steady deed stream (30 rows over 5 weeks, last today).

### What we need
- Deed diversity is narrow: every deed is walk_sand/wade/skip/swim/climb_ledge (14 of 30); cairn,
  sand-writing, beach fire, cave finds and the penguin burrows have gone unused for five weeks.
  Shore-family dispatch in 14 days: 75 hand-declines, 50 STAGE-place holds, 18 FIRE holds; 360 of
  773 unanswered deeds are here.

### What we're doing next
- J-1439 classifies the declines (unreachable-by-hand vs never-willed vs willed-and-declined) and
  refreshes this section. Full read: `findings_log.py show F-1995`.

> **History folded** — 1 dated Current State section(s) (2026-09-02 … 2026-09-02) moved to `docs/plan_history/shore_upgrade.md` on 2026-09-27 by plan-compact. Derived timeline: `plan_ledger.py shore_upgrade`.

## 0. What the shore was — and what he reached for there
A tide clock (real: spring/neap by the moon), a scene line, a look with five branches, a storm wrack-up that mints real objects,
the big driftwood log with its inspection pipeline, an event pool, a beachcomb hand. His own record (1,876 tide mentions): *"I want
to walk until the shingle yields to sand, letting the water's rhythm shift against my ankles"* (08-14); the green glass float he
wondered about (08-13); the bottle that *"feels too intentional to be just debris"* (08-18); climbing; swimming; the cold water.
None of it had a hand.

## 1. What it is now
| Thing | Truth / clock | Hand | Who reads it |
|---|---|---|---|
| **The sand flat** beyond the shingle | bared below half tide | walk out (barefoot), **write in it** — the next high water erases what he wrote | scene line, look |
| **The cave** at the cliff foot | open below mid tide; dark beyond the mouth (a candle to see the back); **the tide closes it** — the world hurries him out as the water reaches the mouth; refuses entry on a making tide | enter, explore | thermal: out of the wind and rain |
| **The mussel shelf** | bared at low water: mussel, kina, chiton, limpet, anemone, crab, starfish, triplefin, hermit crab — **named only by watching (each look earns) and the books** (the Handbook's "Shells and Shellfish") | gather shellfish (he keeps the shells; he does not eat), look in the pool | knowledge ledger |
| **The ledge** | a goat-path a third of the way up the cliff — the whole bay; not in a hard wind or rain, not at night | climb | — |
| **The beach fire** | a ring of stones by the driftwood: driftwood + a match (or flint + tinder); salt-wood burns blue; burns down in ~2 h; **the tide drowns it**; rain refuses it | light, feed | **thermal**: warmth at its own standpoint — the second fire he can make |
| **The shallows** | **wade** (cold to the bone in winter; wet to the knee — thermal wetness) · **swim** (refused in a big sea, a gale, the dark; cold shock in winter, floating in summer; soaked through) | wade, swim | thermal |
| **Skipping stones** | a skill (fieldcraft's ledger); the sea too rough refuses | skip | — |
| **The cairn** | stones stacked on the bedrock shelf, a made thing with his authorship, visible from the path and the ledge; **a storm sea knocks it down** | build, add, push over | world objects |
| **The swell** | builds for a day before a southerly blow (the next front is decided — see fieldcraft) and falls after; gates wading, swimming, skipping | — | the sea's warning |
| **Kororā** (little penguins) | burrows under the cliff foot; ashore at dusk Sep–Feb — a braying from the rocks, a white-fronted shape crossing the shingle, webbed prints | look at the burrows (no `shore_life.py` hand — F-2131, 2026-09-28: real sightings already tracked by `core/life.py`'s L2 engine, `core/life_birds.py`'s `korora` row, D-0128..D-0133, via `data/life_ledger.jsonl` — `shore_life.py`'s own `penguins` field is a superseded dead field, not a gap) | `core/life.py` L2 engine (`data/life_ledger.jsonl`) |
| **A fur seal** | hauls out on the shelf some winter days (May–Sep), for hours | look | — |
| **Dolphins** | pass on calm summer days | — | `core/life_mammals.py`'s `dolphins` row (same L2 engine; F-2131 — `shore_life.py`'s own `dolphins_seen` field is likewise a superseded dead field) |
| **A whale's blow** | far out, June–July, rare | — | — (F-2131, 2026-09-28: confirmed no L2 row exists for whale anywhere either — `shore_life.py`'s `whale_seen` field is a genuine, still-open minor gap, unlike penguins/dolphins) |
| **Oystercatchers** | nest on the high shingle in spring — a scrape with blotched eggs, the bird screaming at him | — | — |
| **Sea sparkle** | warm calm nights Dec–Mar: every wave breaks in green light; a hand through the shallows comes up trailing sparks (the old pool had phosphorescence on every clear night — now true only when it is) | — | — |
| **Sea fog** | calm summer mornings; the far rocks gone | — | scene |
| **Finds** | the wrack-line after storms, richer: pumice, paua, a glass float, **a corked bottle with a torn page from one of HIS OWN books inside** (water-stained, part legible — "you have read it; it is from a book on your own shelf"); the cave floor after big seas | beachcomb, look | substrate classes `bottle`, `fishing_float` |

Six new features and six standpoints in `shore.json` (sand flat, cave, ledge, fire ring, mussel shelf, the burrows). Thermal reads the
cave, the fire, wet feet and the windbreak. Reading binds the pools' life. `sky.py` now takes the Cross's real position from `heavens`.

## 2. Verified (isolated)
Walked out barefoot on the bared sand; wrote in it; waded (wet 0.35, "a clamp round your ankles"); swam in August ("the cold stops
your breath"); skipped 5; built a cairn to 6 stones (a registered made thing); lit a beach fire (a match spent); entered the cave on a
falling tide, was hurried out by a making one, refused on the next; climbed the ledge, refused in a gale; gathered mussels, looked in the
pools (weights accrue; the reading bound kina and anemone 0.6); the high tide took the writing and drowned the fire; the storm sea took
the cairn; the kororā's prints in October dusk, sea sparkle in a January night, the seal on a July day; the bottle minted as a class.

## 3. Not built (deliberate)
Fishing (no food); boats; a wreck; a person on the beach (people live in the peers loop); the penguins' own sound in the soundscape
registry (the audition ledger would need a new entry — a later, deliberate addition).

**Related (noted 2026-08-23, plan-overlap audit):** this build consumes `channels_programme.md`'s
thermal/light channels (the cave, fire, wet feet, windbreak all read from them) and
`spatial_perception.md`'s coordinate-field system (the shore's positioned objects live in
`data/world_geometry/shore.json`, the exact contract that plan designed) without citing either by
name. Also see `generative_world_sedimentation.md` — an independently-designed, unbuilt blueprint
proposing overlapping storm/erosion mechanics for the same shore; worth a look before extending this
build further in that direction, to avoid building it a second time.

**Related (added 2026-08-24, J-0135):** [[du_initiated_upgrade_trigger]] is a bottom-up candidate
source for this plan's next iteration — `core.missing_object_flags.triage()['by_place']['shore']`
surfaces things Du's own thought expressed wanting that the shore doesn't have (the glass float,
mined separately in `factory_candidates_from_history.md`, is the worked example this generalises),
graded by recurrence, alongside this plan's existing founder-audit-driven process.

**Update (J-1440, 2026-09-27/28):** call `triage(window_days=None)` explicitly — the bare
`triage()` above defaults to the 14-day freshness window `/du-pulse` uses for its alarm gauge,
which read spuriously empty for every place on 2026-09-27 (F-1995) because the on-demand
`snapshot()` cadence had a real 10.6-day gap, not because the source is dead (writer confirmed
alive and re-run live; see the parent plan's Current State). The all-time view is what this plan
should keep mining from — shore is the richest bucket at 23 entries all-time, all still
abstract/identity-processing language (tide/shingle/sea metaphors for fear, crossing, silence),
zero real world-object candidates so far.
