# The Full Sound-World — expansion proposal (2026-08-15, for founder review)

> **Status: ⚪ PARTIAL, built and live (restart-gated builds merged 2026-10-29); read pending. D-0063 approved the full ~39-sound proposal 2026-08-28;
> D-0500 (2026-10-28) ruled sections 2-5 built now with no shadow. §1 self-sounds built J-0337 + J-0377; §2 night mysteries F-3181;
> §3 geophony fills F-3184; §4-§5 F-3192/F-3194; merged to master F-3209 (2026-10-29); D-0500 defeater read F-4492 (NOT TRIGGERED,
> 2026-11-14). Constructed sound-string sidecar holds 94 keys (J-2571 done 2026-11-18). Remaining: read the never-percepted keys
> after the next live window (J-4250), and the untested needle_crackle / runout_hiss (no listening session since the merge).**

```plan-state
stage: partial
phase: Sections 1-5 built and merged (D-0500, F-3209); 94-key sidecar in place (J-2571); never-percepted-key read pending
verified: 2026-11-20
evidence_read: 2026-11-14
next: J-4250 reads the never-percepted keys after the next live window
cluster: 6
```


> **Founder's ask:** "I want this sense world to be quite full as it is for a human." Current registry:
> 35 sounds. This proposes ~32 more across five categories, each world-honest (a real source in his
> authored world), each with its trigger, place, rarity, and **epistemic status** under the new
> audition system. Nothing here is built; this is the thinking, for the discussion when you're back.

## Current State — verified 2026-11-14

- **2026-11-14**: J-3978 built D-0760: look_binding bind_targets now whole-word (_binds_target), up/out/far dropped from 7 entries; commit on jobrun/sound_world_expansion; restart-gated.
- **2026-11-14** (F-4590): J-3891: F-4494 confirmed on full note bodies; four read-channel namings were false positives. Word-boundary + 160-char proximity matcher committed in worktree (restart-gated, merge pending); already-learned entries remain in the live ledger.

- **2026-11-14** (F-4492): J-2479 read after about 253 live hours on the merged sections 2-5 boot: D-0500 defeater (about 4 percepts per live day per new sound) NOT triggered, highest dolphin_blow and stream_over_stones at 1.99 per day. Eight keys never percepted (hail x2, rain_down_chimney, frost_crack, paradise_duck_flyover, kelp_fly_buzz, needle_crackle, runout_hiss); the last two await a listening session. Side findings F-4493 (unnamed-sound fragment keywords carry the cause) and F-4494 (read-channel naming by loose substring).
- **2026-10-30** (F-3302): J-2487 regenerated the constructed sound-string sidecar off-live for the 94-key registry: 24 keys added, 70 unchanged, realness 0.9894; dry-run script now takes sidecar and lab out paths; live data file not touched while Du runs

- **2026-10-29** (F-3209): 2026-10-29: sections 2-5 merged to master (dd5f87af) and reconciled with the cat chain in dc78babb (section 2's distant_yowl draw stands down while the tom is live; the dry-run archetype tables know cat_hiss/cat_growl/cat_call). All four harnesses pass from a throwaway worktree of merged HEAD; restart-gated.
- **2026-10-28** (F-3194): J-2478 (D-0500, F-3194): §5 THE APPARATUS built in the chain worktree, commit eac726f4 after J-2475/J-2476/J-2477 -- needle_crackle + runout_hiss bookend a listening session from core/listening.py's started_ts and a new ended_ts that outlives the clear (session_marks(), RUNOUT_S 20 min; the needle-drop and ending lines untouched, D-0443), letterbox_flag_clank gated on room_state's garden.letterbox.flag + the real wind axis at the garden (near) and the study (far pools), all three GRANDFATHERED, one row _sec_apparatus LAST, rates LAST, pools LAST, rail keys LAST with an 8 h floor; registry 88 -> 91; the plan's four §5 cat entries were already cat_overhaul C1's. One real limit: the rail yields to the record while a piece is on, so needle_crackle is heard as listening.start()'s own line and lives on the census/ledger, never as a rail percept. Tests 118/118 + the three earlier chain tests + life_smoke ALL OK, live data/ untouched; restart-gated, nothing live until the next boot carries the merged chain. §2-§5 are now all built: 19 of the plan's unbuilt sounds -> 21 keys registered across the four jobs (bellbird_chime skipped as a duplicate of bellbird_song).

- **2026-10-28** (F-3192): J-2477 (D-0500): §4 seasonal biophony BUILT in the chain worktree, commit 2d0bbbd8 -- silvereye_flock (bound to the tauhou life row, arrives unnamed, easy hedge sighting), paradise_duck_flyover (no life row: a seeded per-day draw of minutes-long passes over the open sky, unnamed, caught only by a look UP inside a new per-entry bind_window_s=300), kelp_fly_buzz (shore summer bed, grandfathered); one row appended LAST, 8 h rail floor; bellbird_chime NOT built (duplicates bellbird_song); 124/124 + regressions 117/117, 150/150 + life_smoke ALL OK; registry 88; restart-gated. §5 (J-2478) next in the same worktree.
- **2026-10-28** (F-3184): J-2476 (D-0500): §3 geophony fills BUILT in the chain worktree, commit e7acc468 -- ten keys (hail roof/leaves, drizzle_hiss, downpour_drum, rain_down_chimney, tin_roof_tick, stream_over_stones, undertow_rumble, frost_crack, calm_sea_hush) on the real clocks, one row appended LAST, 8 h rail floor; tin_roof_tick + frost_crack arrive unnamed; rain grades agree with the severity curve (D-0063 defeater clear); stream_over_stones is its own point, not a grade of stream_run; 150/150 + life_smoke ALL OK; registry 85; restart-gated. §4 next in the same worktree.

- **2026-10-28** (F-3181): 2026-10-28 J-2475 (D-0500): section 2 NIGHT MYSTERIES BUILT, restart-gated -- possum_rasp, wall_scratch, distant_yowl, hedgehog_snuffle, dolphin_blow (registry 70 -> 75; penguin_bray was already the sixth): points, rates, one propagation row appended last, rotating named pools, AUDITION entries with rotating unnamed per-place pools; the four creature voices bound to their life rows (new additive row fields sound_at / sound_days in core/life.py), the yowl a deterministic rare nightly bout with no row yet (known kind, unknown individual). Commit 6fbe9bd3 on jobrun/sound_world_expansion, unmerged; tests 117/117 + life_smoke ALL OK; the §2 table above should now read BUILT for all six rows. Sections 3-5 follow serially in the same worktree.
- **2026-10-28**: 2026-10-28 (T-0103): D-0500 ruled by Travis: build all four remaining sections now, no shadow (19 sounds; bellbird_chime dropped as a duplicate of bellbird_song, penguin_bray already exists). Jobs J-2475 (section 2), J-2476 (3), J-2477 (4), J-2478 (5), read J-2479.

### What we have
- All five sections are built and merged (D-0500, F-3181/F-3184/F-3192/F-3194, merge F-3209, 2026-10-29): §1 self-sounds (19),
  §2 night mysteries, §3 geophony fills, §4 winter biophony, §5 cat/apparatus. Registry 94 sounds; sidecar `data/sound_strings_constructed.json` holds 94 keys.
- D-0063 (2026-08-28) approved the full ~39-sound proposal; D-0014 merged this doc's §1 with `sound_causality.md`'s self-sound list.
- F-4492 (2026-11-14, ~253 live hours): no new sound exceeded D-0500's ~4 percepts per live day; defeater not triggered.

### What we need
- A read of the never-percepted keys (hail_on_roof, hail_on_leaves, rain_down_chimney, frost_crack, paradise_duck_flyover, kelp_fly_buzz,
  needle_crackle, runout_hiss, cat_call) after the next live window; needle_crackle and runout_hiss need a listening session first.

### What we're doing next
- J-4250: the unpercepted-key read. Nothing further to build under D-0500.

## 0. What makes a human sound-world *full* — the shape of the gap

Soundscape ecology divides a natural soundscape into **geophony** (wind, water, weather), **biophony**
(living voices), and **anthrophony** (made sounds). Du now has decent geophony and growing biophony.
But a human's sound-world has two more layers that his world lacks almost entirely:

1. **The sounds of one's own acts.** A human hears themselves constantly — footsteps, pages, the door,
   the pen. This is not decoration: self-generated sound is the classic case of **sensorimotor
   contingency** (the brain predicts the sound of its own act and hears the *match*). It is agency
   feedback — arguably the most identity-relevant audio there is, and Du's acts are currently silent.
   This is also a gift to the consciousness program: the mineness comparator's cleanest possible
   signal is "the sound I predicted because I did it."
2. **Silence and distance as experiences.** A full sound-world is not wall-to-wall sound; it includes
   the held breath after the morepork, the glass-calm night sea, the far-off versus the near. Some of
   this exists in prose; none of it is structural.

## 1. SELF-SOUNDS — the single owned content+trigger table (merged per D-0014/F-0061, 2026-08-25)

> **This table is now the one place self-sounds are listed and specced.** `sound_causality.md`
> no longer keeps a second content list for these — see its own Current State note. Self-sounds
> are deterministic act-triggers, not continuous causal rates, so `sound_causality.md`'s
> rate-function/audibility-table machinery never applied to them; this table is the correct home.

All **known instantly** (no epistemics — a mind knows the sound of its own act; that immediacy IS the
point). Triggered deterministically by his real acts. These make his agency audible.

**Status column:** BUILT = registered in `core/soundscape.py` today; PROPOSED = not built, unbuilt in
both source docs prior to this merge.

| Sound | Trigger | Note | Status |
|---|---|---|---|
| footsteps_shingle | moving at the shore | crunch-and-slide; the shore announces him | BUILT |
| footsteps_leafmould | moving in the wood | soft, held prints; near-silence as texture | BUILT |
| footsteps_floorboards | moving in the study | the one that creaks in the same place every time | BUILT |
| footsteps_grass_soil | moving in the garden | the terrain gap identified in F-0061 — shingle/leafmould/floorboards exist, garden/grass does not. **Built 2026-08-29 (J-0337): locomotion.GROUND already mapped garden→"grass"; soundscape.py's footsteps block just never read it — one `elif` closed the gap.** | BUILT |
| page_turn | a reading sitting | the sound of his own attention, hours of it. **Built 2026-08-29 (J-0377): off `reading.py`'s existing `last_read_ts` (written every sitting) — only the read is new.** | BUILT |
| pen_scratch | writing (letters, notes) | the letter to Travis had a sound; now it will again. **Built 2026-08-29 (J-0377): a new persisted `last_write_ts` in `letters.py`'s `write_letter()` (the old cooldown clock was in-memory only).** | BUILT |
| wood_snap | gathering (snapping deadfall) | effortful, resonant, his. **Built 2026-08-29 (J-0377): `state["wood_snap_ts"]` at `sensorium._gather_wood()`'s wood-branch, the literal "snapped to length" moment.** | BUILT |
| log_on_fire | feeding the grate | thud, spark-burst, the fire's answering lift. **Built 2026-08-29 (J-0377): `state["stoke_ts"]` at `sensorium.act()`'s `"stoke"` branch.** | BUILT |
| gate_latch | passing the garden gate | the boundary of home, marked in sound. **Built 2026-08-29 (J-0377): `gate_ts` in `locomotion.tick()`, the same "really passes the gate" condition the letterbox-flag glimpse already used.** | BUILT |
| ~~kettle_rising~~ → kettle_fill / kettle_pour | make_tea (fire lit) | **Correction (F-0061): dropped as proposed — `kettle_sing` already exists** (`core/soundscape.py:176`, wired 394-395 as a state-condition check on `kettle_on_ts`/`kettle_boiled`, not an act-site hook). Repurposed to the still-missing fill/pour sub-events instead of duplicating the boil. **Built 2026-08-29 (J-0337): both wired as brief (<20s) recency-window sounds off real act-site timestamps — `kettle_fill` off the existing `kettle_on_ts` (fires right after the kettle is filled and set on the hob, before the boil), `kettle_pour` off a new `pot['pour_ts']` field added at the `make_tea` act site in `study_life.py` (fires when the boiled water goes onto the leaves).** | BUILT |
| woodpile_settle | ambient, night, after wood is stocked | the stocked pile shifting once — his labour audible after dark. **Distinct from `wood_haul_clatter` below** (F-0061: same noun as sound_causality's woodpile gap, different mechanism — one is ambient, one is an act). **Built 2026-08-29 (J-0377): no timestamp needed — reads the already-real `sensorium.state["woodpile"]` count, ambient at night in the garden.** | BUILT |
| wood_haul_clatter | hauling wood to the pile | the haul itself, not the settle — added per F-0061's His-Own-Acts gap; kept separate from `woodpile_settle` on purpose. **Built 2026-08-29 (J-0377): `state["wood_haul_ts"]` in `locomotion.tick()`'s arrival branch, the literal "tip the armful onto the woodpile" moment.** | BUILT |
| bed_watering | watering the garden bed | the can's spatter on soil and leaves — added per F-0061's His-Own-Acts gap. **Built 2026-08-29 (J-0377): `last_water_ts` added to `garden.py`'s own state dict inside `water()`.** | BUILT |
| herb_cut | cutting/harvesting herbs | the snip — added per F-0061's His-Own-Acts gap. **Built 2026-08-29 (J-0377): `last_harvest_ts` added inside `garden.py`'s `harvest()`.** | BUILT |
| sow_dig | sowing/digging in the garden | added per F-0061's His-Own-Acts gap. **Built 2026-08-29 (J-0377): `last_sow_ts` added inside `garden.py`'s `sow()`.** | BUILT |
| door_sound | the cottage door (open/close) | added per F-0061's His-Own-Acts gap. **Built 2026-08-29 (J-0377): `door_ts` added at both of `study_life.py`'s door open/close branches; also required a `sensorium.act()` save-throttle fix — see the entry below.** | BUILT |
| chair_desk_scrape | sitting/rising at the desk | added per F-0061's His-Own-Acts gap. **Built 2026-08-29 (J-0377): `desk_ts` in `locomotion.goto()` whenever the standpoint becomes `"at_the_desk"` (already the crossing point for lamp-lighting/letter-writing).** | BUILT |

**Corrections applied to this table (2026-08-25, executing D-0014/F-0061):**
1. `kettle_rising` dropped as a duplicate of the already-built `kettle_sing`; repurposed to the
   still-missing fill/pour sub-events.
2. Six His-Own-Acts items from `sound_causality.md` List B that this doc never proposed are now
   added: `bed_watering`, `herb_cut`, `sow_dig`, `door_sound`, `chair_desk_scrape`, and the
   `footsteps_grass_soil` terrain gap.
3. `woodpile_settle` is kept (it is an ambient night sound) and a new, separate `wood_haul_clatter`
   is added for the act itself — these are not duplicates despite sharing the word "woodpile."
4. Cat entries completed in §5 below (`cat_meow_at_door`, `cat_storm_rustle` added alongside the
   existing `cat_trill`/`cat_lapping`).

## 2. NIGHT MYSTERIES — the epistemic stars (~6 sounds, ALL arrive unnamed)

The audition system's best material: real NZ night voices that are genuinely alarming or strange when
unknown. The night becomes a place of learnable mysteries. Identification difficulty is honest
natural history.

| Sound | Truth | Where/when | Difficulty |
|---|---|---|---|
| possum_rasp | brushtail possum | wood/garden night | harsh coughing rasp — frightening unnamed; visible by looking with resolve (eyes in the dark) — medium |
| penguin_bray | little blue penguin | shore rocks, night | a donkey-bray from the dark rocks — bizarre unnamed; hard to sight; book-learnable |
| wall_scratch | mouse in the cottage wall | study, night, winter | tiny, intimate, unfindable — the classic house mystery; near-impossible to sight (a trap is not authored); may stay a mystery |
| distant_yowl | the OTHER cat (the black one) | garden/wood night, rare | he KNOWS cats — but is it her? Ambiguity between known-kind and unknown-individual; binds if he ever sees the black cat cry |
| hedgehog_snuffle | hedgehog | garden night | busy snuffling along the beds; sightable by lamplight? (no lamp authored — moonlight nights only, low prob) |
| dolphin_blow | dolphin/small whale | shore, any hour, RARE | the authored line already exists ("something out on the water blows a breath"); register it as a sound; sightable only if he looks at the water fast, by day — mostly stays a wonder |

## 3. GEOPHONY FILLS — weather/water completeness (~8 sounds)

Mostly grandfathered-known (he has lived with rain and sea for months; new *grades* of a known thing
are not new identities). Trigger-tied to the real clocks.

- **hail_on_roof / hail_on_leaves** — winter storm variant; sharp, unmistakable, rare.
- **drizzle_hiss vs downpour_drum** — rain gains grades (currently one rain sound); intensity from the
  weather state. Known.
- **rain_down_chimney** — rain reaching the lit fire: sizzle and spit. Known (fire + rain co-state).
- **tin_roof_tick** — the corrugated roof creaking as sun heats/cools it: THE New Zealand cottage
  sound; morning/evening of clear days. Enters unnamed (a genuinely mysterious tick until placed —
  sightable by looking at the ceiling? Better: book/inference; a good slow mystery).
- **stream_over_stones** — the shore's stream mouth (already authored in prose); constant near it.
- **undertow_rumble** — big-sea backwash rolling the shingle: felt-in-the-feet bass. Known (it's the sea).
- **frost_crack** — hard-frost nights, a single sharp report from timber or ground. Unnamed at first
  (a bang in the night!); inference/book.
- **calm_sea_hush** — the *near-silence* state: glass night sea, registered as its own point so the
  census records quiet as a state, not an absence.

## 4. WINTER/SEASONAL BIOPHONY (~4 sounds)

- **silvereye_flock** — tauhou working the trees in loose winter flocks, soft contact cheeps; the
  definitive NZ winter-garden sound. Unnamed → easily sighted (they swarm visibly).
- **bellbird_chime** — korimako in the wood, the bell-note dawn voice. Unnamed; medium sighting.
- **paradise_duck_flyover** — pairs passing high, honking her-then-him; needs no habitat (flyover).
  Unnamed; sightable by looking up at the right moment.
- **kelp_fly_buzz** — summer wrack-line flies (pairs with the substrate's kelp). Known-ish; trivial.

## 5. THE CAT'S WIDER VOICE + APPARATUS (~7 sounds, cat entries completed per F-0061)

Relationship sounds and the dwelling's machinery — all known (lived-with):
- **cat_trill** — her greeting chirrup when he arrives; bonds have sounds.
- **cat_lapping** — small, domestic, alive.
- **cat_meow_at_door** — added per F-0061: the meow at the door, missing from the original 2 cat
  entries.
- **cat_storm_rustle** — added per F-0061: the under-desk rustle during storms (her `storm_response`
  quirk already exists state-side; this gives it a sound).
- **needle_crackle / runout_hiss** — the record player's apparatus voice at start/end (the needle-drop
  line already exists in listening.py; register the sounds so music sessions have acoustic bookends).
- **letterbox_flag_clank** — wind working the raised flag: the sound of unread mail.

`woodpile_settle` moved to §1 (self-sounds) alongside its new sibling `wood_haul_clatter` — see the
correction note there; it is listed once now, not duplicated across sections.

## 6. Explicitly NOT proposed, and why

- **A clock** — no clock is authored, and mechanical time would quietly re-introduce the clock-time
  sense the cadence work deliberately removed. Founder call if ever.
- **Traffic/aircraft/voices** — no humans are authored within earshot; the solitude is load-bearing.
- **A distant boat engine** — tempting (the glass fishing-float implies fishing boats exist somewhere),
  and it would be the world's first hint of other people. That is a WORLD-DESIGN decision, not a sound
  decision — parked for the founder.
- **Frogs** — no pond. **Skylark** — no open farmland. **Kea/kaka** — wrong habitat. World honesty wins.

## 7. Structural notes (for the build, when approved)

- **Self-sounds** hook the ACT sites (move/read/write/gather/feed/tea), not ambience — they are
  consequences, and their reliability is the point. Consider logging predicted-vs-heard for the
  mineness comparator later (efference copy, shadow-only).
- **Distance/attenuation**: sounds already carry direction; add a near/far word from the geometry where
  sources have positions (the same honesty as the spatial renderer).
- **Chords**: with ~65 sounds the census chords get genuinely rich; the auditory-recall channel
  (geometry-P4, still unbuilt) is where fullness pays off — more acoustic neighbourhoods to associate
  through.
- Rarity discipline throughout: mysteries are RARE (a possum some nights, not every night); the
  anti-wallpaper law holds. Fullness = variety × state-honesty, never volume.

**Net (superseded by the 2026-08-25 merge below — kept as the original estimate for history):
~32 new sounds → registry ~67, five categories, 12 entering unnamed through the audition system,
9 making his own agency audible for the first time.**

**Corrected net, post D-0014/F-0061 merge (2026-08-25):** §1 self-sounds now 17 entries (3 already
built: `footsteps_shingle/leafmould/floorboards`; `kettle_sing` also already built but lives under
its own name, not this list; 14 proposed and unbuilt after adding the 6 His-Own-Acts items + the
grass/soil terrain gap + `wood_haul_clatter`, and dropping `kettle_rising`). §5 cat/apparatus now 7
entries (2 completed). §2/§3/§4 unchanged in count. Total proposed-and-unbuilt across all five
categories: ~39, not ~32 — the original estimate undercounted His-Own-Acts before F-0061 mapped it
against `sound_causality.md`'s List B. This table is now the single owned content+trigger source for
self-sounds; do not re-propose these items in `sound_causality.md`.

**Net after D-0063 execution begins (2026-08-29, J-0337):** §1 self-sounds: 3 of its 15 unbuilt-sound
slots now built (`footsteps_grass_soil`, `kettle_fill`, `kettle_pour`) — 12 remain, scoped to J-0377.
§2/§3/§4/§5 unchanged (still fully unbuilt, ~24 sounds). Registry: 43→46. Total proposed-and-unbuilt
across all five categories: ~36, down from ~39.

**Net after §1 completion (2026-08-29, J-0377):** all 15 of §1's unbuilt-sound slots are now built —
the remaining 12 (`page_turn`, `pen_scratch`, `wood_snap`, `log_on_fire`, `gate_latch`,
`woodpile_settle`, `wood_haul_clatter`, `bed_watering`, `herb_cut`, `sow_dig`, `door_sound`,
`chair_desk_scrape`) each got a real act-site hook — see the dated entry above for the full
per-sound source-file/mechanism breakdown and the live verification. §1 SELF-SOUNDS IS COMPLETE.
Registry: 46→58. §2/§3/§4/§5 unchanged (still fully unbuilt, ~24 sounds) — §2 (night mysteries) is
next in priority order per D-0063.

**2026-09-03 — J-0515 (F-0697 → F-0722): the three rated-but-unregistered §4 sound keys resolved.**
The Living World bird build (J-0511) had rated `bellbird_song`, `fantail_cheeps` and `pukeko_squawk`
in `soundscape._EVENT_RATES` with no matching `_SOUNDS` point, so all three were dead (never in the
active set, never counted, never heard) — `set(_EVENT_RATES) - set(_SOUNDS)` was non-empty. Resolved
per-key, not as a block:
- **`bellbird_song` REGISTERED** — this doc's own §4 already proposed `bellbird_chime` as unbuilt
  winter/seasonal biophony, and `core/life_birds.py`'s bellbird row (HIDDEN TRUTH, `ease=0.35`) had
  been carrying the sound as a documented gap since J-0511 (`note="...bellbird_song is rated but not
  registered"`). Added a real Sound Space point (`core/soundscape.py`, bright/pure/periodic — a clear
  bell-note, distinct from the blackbird's rougher, less periodic phrasing), a `sound_knowledge.
  AUDITION` entry (unnamed-until-seen-or-read, reveal/miss text matched to the row's own
  `hidden.reveal`/`hidden.miss` so the sound and sight paths agree), `audition="bellbird_song"` +
  `sound=("bellbird_song",)` on the row itself, and a garden + wood voice line in `_GARDEN_NEW_VOICES`/
  `_WOOD_NEW_VOICES` (the same picker pools `fantail_chatter`/`riroriro_trill` use). §4's proposed
  `bellbird_chime` is now effectively built under the name `bellbird_song` — §4's own count should be
  read as 3 remaining, not 4, next time it's picked up.
- **`fantail_cheeps` DROPPED** — confirmed a stale twin: `fantail_chatter` (this doc's §1, already
  BUILT) is the real, fully-wired fantail voice (life_birds.py row, AUDITION entry, both garden and
  wood pickers); nothing else in `core/` ever referenced `fantail_cheeps`.
- **`pukeko_squawk` DROPPED** — on evidence that contradicts F-0697/this job's own premise: a grep
  across `core/` found ZERO mentions of pukeko anywhere outside the one dead rate — not in
  `world_content_garden.py`, not in `life_birds.py`, nowhere. No pukeko row exists or is planned, so
  there was nothing to condition the register-vs-drop call on; dropped.

`set(_EVENT_RATES) <= set(_SOUNDS)` now holds (verified live). Registry: 58→62 (also reflects J-0511's
`cuckoo_call`/`godwits_overhead`/`blackbird_alarm` additions, not just this job). `scripts/
life_smoke.py` section [9] (THE BIRDS) passes with `bellbird_song` now in the garden-dawn active set;
the one remaining smoke-test FAIL (`one active trace per creature per place`, section [11]) is in the
unrelated J-0513 traces/carcasses subsystem. Full detail: F-0722.
