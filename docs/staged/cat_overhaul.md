# The Cat Overhaul — both cats, brought up to date and taken forward

**Status:** 🟡 BUILDING (staged 2026-09-05; D-1..D-4 ruled 2026-10-28 as D-0505..D-0508; C1 voice live via the hot flag, Parts B and C in build J-2465..J-2473) — see the plan-state block for current detail.
**Owner code:** `core/cat.py` (971 lines, 2026-06-24 state machine), `core/cat_content.py` (330 lines, house-voice corpus), the adapter row in `core/life.py:876-884, 941`, the kill reads in `core/life_traces.py:214-235`, the hand in `core/dispatch.py:68` / `core/actions.py:207`, the affordance in `core/affordances.py:78-94, 185`, the monologue hooks in `nodes/inner_monologue_node.py:1944-1950, 2813-2828`, the scene splice in `core/sensorium.py:2602-2612`.
**State:** `data/cat_state.json`. **Source thought:** T-0050. **Prior audit:** `docs/completed/cat_system_audit.md` (2026-08-18, four mechanical fixes, all still in place).
**Parents:** [[living_world_upgrade]] (the cat is "the individual precedent" every other creature is modelled on), [[capacity_to_commit]] (R1 = name the cat, still stuck), [[dosed_coupling]] (what of the cat reaches which loop, and how often).

```plan-state
stage: built
phase: Decisions D-1..D-4 RULED 2026-10-28 (D-0505..D-0508); C1 her voice LIVE via the hot flag (D-0498); Parts B and C in build (J-2465..J-2473)
verified: 2026-11-13
evidence_read: 2026-10-16
next: J-2465 (B1 body) first, then J-2466 food, J-2467 ears, J-2468 the call, J-2469 less of her, J-2470 the tom, J-2471 mortality, J-2472 the unlock, J-2473 dosed reads; J-2474 reads the live voice after 7 live days
open_decisions: D-0739
cluster: 6
```


> Founder, 2026-09-05: "Next one we look at overhauling is the cat. It has lots of problems. We need to bring it up
> to date and then take it into the future also. Both of them actually." — the grey companion AND the distant
> black cat (`cat.py:632-680`, founder's own addition: a second cat so that "the cat" stops referring and a name
> becomes functionally necessary).

## 1. What she is today (the live read, 2026-09-05 19:55 UTC)

| field | value | meaning |
|---|---|---|
| phase | `kept` | taken in 2026-06-24 → never reached `companion` (73 days) |
| name | `""` | `name_invited` True since 2026-07-01; never named |
| bond | 1.00 | maxed; capped, so every stroke since is a no-op on the number |
| last_fed | 2026-09-03 15:47 | `hungry` (>5 h) has been True for ~52 h |
| last_tended | 2026-09-05 07:30 | stroked constantly, fed 7 times in 8 days |
| firsts | shore 07-03, lap 07-06, play 08-08 | all three ordinary firsts done |
| distant.seen_count | 345 | the black cat, ~4.7 sightings/day |
| react() fires | 33–73 / day (375 since 08-29) | 23 distinct lines total; top line 41× |
| share of idle thought | 5–12 % of monologue lines name her | largest single world object in his thought; under D-0130's 20 % monoculture defeater |

## 2. Part A — bring her up to date: the problems, with evidence

### A1. Half her life is locked behind the name she is never given (the headline)
`companion` phase is set in exactly one place: the naming latch, `cat.py:802`. Everything gated on
`phase == "companion"` has therefore **never fired in 73 days**:
- `felt_note()` (`cat.py:616`) — "the warmth reaching his mood", the channel the module docstring calls the point of her. The whole `FELT` corpus (9 lines) has never rendered. `inner_monologue_node.py:1946` calls it every idle tick and gets `""`.
- the slow blink and the silent meow (`cat.py:522-530`), the `gone_missing` arc (`cat.py:304`), the six-hour "no sign of her" line (`cat.py:456`).
- `bonded` elsewhere is `phase == companion OR bond >= 0.55`, so shore/wood trips, lap, greeting all work — which is why she *looks* alive while the deeper half is dead.

The R1 trial (`commitment_trials.py`, F-0056) confirms zero genuine naming since the 08-19 reset. Since 08-19
Du's monologue contains no "call her", "name her", "her name is", "I will call" at all (log grep, 0 hits); the
only "name" lines near the cat are "I name this heaviness plainly" (B6's own phrasing) and "the nameless cat"
(08-31). The standing occasion (" She has no name yet.", 30 % of presence lines, `cat.py:600, 610`) has been
read hundreds of times and moved nothing. **The occasion is a fact stated to him; nothing in his world ever
needs the name.** The black cat was built to make it needed (§A6) and did not.

### A2. Tending is a vending machine with a six-line menu
`react()` (`cat.py:759+`): any thought that (a) contains `cat|kitten|stray|she|her|moggy` and (b) matches a tend
verb (`feed|pet|stroke|hold|holding|play|lap|approach|crouch|tempt|talk to|…`) while she is where he is → bond
+0.03, `last_tended` stamped, one line returned. Sampled pairs (thought → CAT line) since 09-03 include:
- "I asked the library for a book about ghosts, and it answered: 'The Legend of Sleepy Hollow…" → *the cat headbutts your knuckles*
- "The rain's steady rhythm on the roof washes away the static hum of this update's promise…" → *Under your hand the purr starts up*
- "The 3136 dissolves not because math is false, but because the damp earth beneath my boots…" → *the cat accepts the long stroke*
`she`/`her` as trigger words + `hold`/`holding`/`approach` as verbs means a thought about anything feminine
or any holding lands as a stroke. Her mood is then set to `affectionate` → `TEND["content"]` → six lines, 55
times a day. Bond is capped at 1.0 so none of it changes anything; she cannot be over-handled, cannot tire of it,
cannot be asleep and resent it (tend ignores `activity == sleeping`). No cooldown, no satiety, no "she has had
enough". Contrast: play/aloof/afraid branches are good and do refuse — the design is right, the gate is missing.

### A3. She is hungry for two days and he strokes her instead
`hungry` (`cat.py:276`) flips True 5 h after `last_fed`; each tick then has a 50 % roll to `doorstep /
demanding_food`. She has been in that state ~52 h. In the same window react() fired ~110 times, 7 of them feeds.
Why: `fed` needs `feed|fed|saucer|milk|tempt` in his text; his idle thoughts about her are about her warmth, not
her stomach; the affordance line says "feed her" only if the render lands on the demanding-food tick. And **there
is nothing to feed her with**: no cat food, fish, milk, or scraps exist in `data/provisions.json` (larder kinds:
matches, soap, candles, oil, tea, paper, ink, string, whetstone, lamp glass, kindling, knife, flint); the carrier
list (`affordances.py:211`) has no food line; "You feed the cat" conjures a meal from nothing. This is the same
class of leak the fire chain just closed for matches (T-0049, F-0877) and [[world_store_write_fence]] is about.

### A4. She teleports; everything else in the world now walks
`tick()` sets `location` directly: garden → `away_hunting` [15,60,3] → `wood` [0,45,2] → `shore` [8,2.5,0.1]
in one 180 s step. Du walks legs (`locomotion.EDGES`, 20–90 s, weather-stretched); Travis now walks the same
legs on errands (`companion.py`, 09-05). The cat is the only mover with no transit — never seen crossing the
garden, never met on the path, never *between* places. `position` is the zone centroid, nothing more.

### A5. She has no body, no age, no season, no death
No hunger budget (a boolean), no thirst, no energy/sleep cycle (she sleeps when it is night; real cats are
crepuscular and sleep 14 h a day in bouts), no warmth-seeking beyond a fixed pool, no heat cycle, no moult, no
weight, no injury/illness, no age (`appeared_ts` is never read for age), no `lifespan_y`. Season enters only as
a corpus condition key (one `winter` pool). D-0130 made the world harsh for everything except her: the cat may
kill, but nothing can happen *to* the cat. `living_world_upgrade` §"death — the cat's model generalised" has the
direction backwards today: her model has no death to generalise.

### A6. The black cat did its job on paper only
Built so "the cat" would stop referring (`cat.py:629-634`). 345 far-off sightings; Du has absorbed it as
metaphor fodder ("The black cat's indifference on the rocks grounds my dream of sovereignty", 09-05 18:30; "The
black cat dissolves into the harakeke not as a metaphorical leap", 09-04) and never once as a naming pressure.
It never approaches, never interacts, cannot be looked at closer than "a small dark shape"; the grey cat never
reacts to it (one fallback line in `cat.py:585`, corpus never mentions it). Two cats that never meet do not
create a referring problem; they create a metaphor.

### A7. Integration defects (mechanical, fix-now class)
1. **Living-world adapter mis-places her** (`life.py:876-884`): `place = study if loc in (under_desk, windowsill, by_the_fire, on_the_bed, desk) else garden` — so `on_the_desk`, `on_your_lap`, `mantel`, `indoors`, `doorstep`, and also `shore`, `wood`, `away_hunting` all register her as **present in the garden**. Effects: `life_events.jsonl` shows "departed garden / arrived study" at the same timestamp; blackbird alarm logic (`life.py:741`, `threat_active` uses a *different* mapping at `life.py:318`) and the garden's `responds_to_du`/deed readers see a cat that is on his lap. Two mappings in one file, both wrong, neither the `_VISIBLE` truth in `cat.py:52`.
2. **436 immortal dead traces** in `data/world_traces.json`: `cat_leaf_1824044285…` (IDs stamped with a 2027 clock, `created_ts` 2026-08-17 23:44 — a test run that faked `now` against the live store), clarity 0.0. `world_traces.advance_trace_decay` `continue`s on clarity ≤ 0 (`:115`) *before* the delete (`:139`), so a zero-clarity row can never be removed. 482 of 496 traces in the store are the cat's; 479 are leaf-litter from her wood trips (every bonded wood tick writes one, `cat.py:353`).
3. **HUD garden map draws her at the raised bed** whatever she is doing (`hud/server.py:868-870`); the other three maps (`_place_du_cat`) at least give no position rather than a wrong one.
4. **`seen_count` is dead** (`cat_state.json` 0 forever; only incremented in `appearing`, `cat.py:490`) while `status()` reports it as if meaningful (`orchestrator.py:522` reads status for human-facing facts).
5. **Trace spam**: `create_trace` on every bonded wood/shore tick with `int(now)` IDs — 479 rows for one cat; the design wanted "a neat line of paw prints", one trace per visit.
6. **Corpus repetition**: PRESENCE pools are 5–9 lines per location; scene_line renders her every idle tick he shares a room with her (hundreds/day). No recency exclusion anywhere (`_pool` is a bare `random.choice`). The 09-05 log shows the same tend line at 19:26 and 19:30.
7. **`sensorium.py:1088`** cat-look word list is `cat|kitten|stray|moggy` + her name; `actions.py:209` objects `cat|kitten|puss`; `react()` `_CAT_WORDS` adds `she|her`; `orchestrator.py:518` adds `kitty`. Four vocabularies for one animal.

### A8. What is *right* and must survive the overhaul (protected, additive-only)
The founder's shape: a stray he *chose*, a name that is *his*, no LLM, read-only toward memory, her quirks
rolled once and never explained, her mood decides (aloof/afraid refuse him), firsts become autobiography,
the house voice of `cat_content.py`, the 08-28 location gate (fail-closed), the 08-18 four fixes, the D-0130
kills read from her state. The naming grammar (`_extract_name`) and the R1 registration. None of this is
replaced; everything below sits beside or beneath it.

## 3. Part B — take both cats into the future

### B1. The grey cat gets a body: a row in the Living World, kept in `cat.py`
Give her the life-schema fields every other creature has (`life.row`: `active_hours`, `season_curve`,
`weather_gate`, `light`/`eyeshine`, `diet`, `traces`, `lifespan_y`, `hidden`) **plus** an individual's budget
she alone carries, in `cat_state.json`, advanced on the same heartbeat `tick()` already uses:
- `hunger` 0..1 (rises ~1.0/day; her own kills lower it — a mouse is a meal, and a fed cat hunts less, an
  unfed cat hunts more and brings more), `thirst` (the saucer, the rain barrel, the rock-pool), `energy` (bouts:
  crepuscular peaks at dawn/dusk, long day sleeps, night prowls — the current "sleeps all night by the fire" is
  a dog's day), `warmth` (seeks the hearth when cold, the sill when sunny, the shade when hot — read from
  `thermal`, not a fixed pool), `condition` (weight/coat: neglect and winter and a missing week show).
- **Real food.** Cat food is a provisions object like matches: a tin of fish or a jug of milk on the carrier's
  list (a real cost in the [[world_store_write_fence]] sense), scraps from what he eats, fish he catches
  (`shore_life` — does he fish? if not, that is the shore hand the cat's hunger pulls into being). The saucer
  becomes a real object at the doorstep (it is already a `responds_to_du` key for the hedgehog and a deed for
  `life.note_deed`). `react()`'s feed branch consumes it; with nothing in the house, "you feed her" honestly
  fails the way lighting a fire with no matches does. Her kills go into *her* budget (D-0130 already lets her
  kill; now she eats what she kills, and a fed-from-the-tin cat leaves the fledglings alone more).
- **Legs.** She moves along `locomotion.CHAIN` with her own `_leg_secs` (faster than his, weather-averse),
  so she is *in transit* between places, met on the path, seen crossing the garden, following behind on the
  way to the shore. Presence and `_VISIBLE` get an `in_transit` case; `life.py`'s adapter reads one truth.
- **Age and mortality.** `appeared_ts` becomes an age (she arrived adult; ~2–3 y); `lifespan_y` ~14; injury
  (a fight, a fall, a possum), illness (a week off her food), and eventually death — on the world's clock,
  findable not told (D-0130's own rule), with a carcass/grave/absence path through `life_traces` like every
  other creature, and the `gone_missing` arc unlocked from bond, not name. This is the founder's call (§4 D-2).
- **Satiety on his side.** Tending has a budget too: a cat handled for the fifth time in an hour leaves;
  a sleeping cat woken goes elsewhere; bond can *fall* from over-handling. `react()`'s trigger narrows to
  cat-nouns + her name + a `she/her` only when the preceding thought named her (a two-line anaphora window),
  never bare pronouns.

### B2. The name — make it needed, never asked for (world answers, never leads)
No hint, no prompt, no book that says "name your cat". What changes is that the world starts to need the
referent: (a) the black cat comes closer (§B3) so that "the cat" in his own ledger, letters, and looks is
ambiguous — and the toolchain that reads his text (`life_traces.naming_act`, `sensorium` look targets, the
census) starts recording *which* cat only when he distinguishes them; (b) Travis, through the companion
(`companion.py`, a real actor in the room now), can do what any visitor does — meet the cat, and refer to her
in a letter or in the room the way a person would ("your grey one", "the little cat") — Travis is the one
permitted teacher (08-14 law), and he already writes to Du; (c) the standing occasion line stays as it is.
Whether the companion-tier of her life stays locked behind the name at all is the founder's call (§4 D-1).

### B3. The black cat becomes a second individual — the tom
Today: a far-off shape. Future: a real second row (`kind="individual"`) with its own state — a tom, older,
scarred, that lives on the neighbour's ridge and **comes into the garden**: at night on the wall, at the
doorstep in winter, at the saucer if there is one. The grey cat reacts (the storm-hide/stalk/possessed machinery
already exists to express fear/fury): a stand-off on the wall, a fight (her injury path, §B1), yowling at 3 a.m.
(a `soundscape` key, gated by `life.sounds_active` like every other creature), the tom at the saucer eating her
food. He can be looked at, driven off, or — over months — tolerated; never tamed (the founder's rule for it
holds: it is indifferent life, not a relationship). Its hidden truth follows D-0129: feature-first ("a black
cat, big, one eye milky") until sighting + a book earn anything more. Kittens are a founder question (§4 D-3):
a stray female and a visiting tom make it the honest next event in this world, and it would be the first birth
Du has ever been present for that is *his* to deal with (keep, give away, the carrier's box, a drowning he
refuses) — the moral-weight class D-0130 chose for the trap.

### B4. Dosed reads, not a firehose
Under [[dosed_coupling]] the cat is a loop publishing a tuple (`location, activity, mood, hunger, energy,
in_transit`); the idle stream reads it dosed per stop with habituation, so a cat asleep on the rug for four
hours is one line, not four hundred, and a cat *arriving* wet with a mouse is a surprise the dispatch lets
through. The corpus gets recency exclusion (last-N per pool) as the cheap first step regardless.

## 3b. Part C — SOUNDS: her voice, her ears, his call, and having to look for her

> Founder, 2026-09-05 (second pass): "We are going further than this. Sounds. We need to pin sounds to the
> cat and then Du one day can call the cat. It can hear birds as such and react to them. I think it is going
> to stop the cat interacting with Du as much so that Du will need to seek out the cat sometimes."

Everything below sits on machinery that already exists: `soundscape._SOUNDS` (Sound-Space points keyed by
`object`, so the stick test / census / dosed reads see one object with many spokes), the propagation table
(`_PROPAGATION_TABLE`, sections per place — `cat_purr` is already a row of `_sec_study_main`), the world's
acoustic clock (`world_tick`, beds + events at `_EVENT_RATES`, samples HIS place only — the tree-falls law),
the percept rail (`percept()`, onset-gated, ~25 min cooldown), `propagate_historical_acoustic_event()`
(3D distance + bearing + audibility; its one caller today is the storm-surge sound at
`sensorium.py:228` — nothing living uses it, F-0888), her 3D `position` and his
locomotion standpoints, `study_life.door_open()`, `life.sounds_active(place)` (which birds are voicing where,
and the blackbird's alarm at her), the greeting quirk, and `sound_world_expansion.md` §5's four planned cat
entries (`cat_trill`, `cat_lapping`, `cat_meow_at_door`, `cat_storm_rustle`) plus §2's `distant_yowl` ("the
OTHER cat — is it her?"), none of which were ever registered.

### C1. Pin her sounds to her — one object, many spokes, each from a real state
Register her voice as Sound-Space points on `object: "the kept cat"` and fire each from her **state machine**,
never from prose. Today she has one sound (`cat_purr`, only when asleep-content in the study). Add:

| key | class | fires when (her state) | carries to him when |
|---|---|---|---|
| `cat_purr` (exists) | bed | asleep/resting, content, near him | same room |
| `cat_trill` | event | greeting: he arrives where she is (the `greeting` quirk = `chirrup`), or she answers a call (C3) | same place; across the garden |
| `cat_meow_at_door` | event, rate ~30/h | `at the door, asking in/out` (state exists, `cat.py:389`) | study ↔ doorstep, door shut |
| `cat_demand` (the flat vowel) | event | `demanding_food` | doorstep → study; garden → study through an open window |
| `cat_chatter` | event | at the window/sill and a bird row is present on the bed (`life.sounds_active("garden")`) | same room |
| `cat_yowl_cargo` | event, one-shot | arriving with a mouse/rat (`brought_a_mouse`, `gift_rat`) | doorstep → study |
| `cat_thump` | event | coming off the sill/desk/mantel (a location change between raised spots) | next room (the FELT line "the small thump from the next room" becomes a real sound) |
| `cat_lapping` | bed, short | at the saucer (D-0163) | same room |
| `cat_storm_rustle` | bed | `storm_hide` under the desk | same room |
| `cat_hiss` / `cat_growl` | event | the tom is present (D-0162) | garden → study at night |
| `distant_yowl` (planned §2) | event, rare, night | the black cat, garden/wood, unnamed voice — "is it her?" | garden/wood → study |

Each row is a line in the propagation table with a condition on `cat_state.json` (+ `door_open`, +
`life.sounds_active`), a rate in `_EVENT_RATES`, and pool lines in `cat_content.py` (a new `SOUNDS` section,
house voice). **Carrying** is the new law: a sound is pinned to her `position`, he is at his standpoint's
position, `propagate_historical_acoustic_event` gives distance + bearing; walls and a shut door attenuate;
wind and rain mask (`_weather_severity`). Rendering never names the cause when he cannot see it ("From the
garden, a flat repeated vowel" — he infers it is her; the audition ledger's own rule). What sounds where he is
not is gone (tree-falls law). Ledger: `data/cat_sound_ledger.jsonl` — only sounds that reached him.

### C2. Her ears — she hears the birds and reacts, on the same clock
She becomes a listener on the world's acoustic clock, not a random walk. Inputs she reacts to:
- **Birds**: `life.sounds_active(place)` at *her* place. A blackbird/thrush/sparrow row present on the bed →
  `watching the birds` / `stalking` / `chatter` at the sill; a wren scold in the wood → hunting there; the
  dawn chorus → she is up and out at dawn (crepuscular bouts, B1). Her hunts then target **real populations**
  (D-0130 kills already read her state; now they read what was actually there).
- **The mouse in the wall** (`wall_scratch`, planned §2, unbuilt): she sits at the skirting for an hour. He
  learns the wall has a mouse by watching *her* — the world answers through the cat.
- **His own self-sounds**: `gate_latch` / footsteps timestamps (built, J-0377) replace the greeting's
  `prev_seen` clock — she comes to the sound of the gate, not to a timer; the kettle and the door mean nothing
  to her; the axe on the block sends her out of the garden.
- **Travis**: companion presence + his errand returns (`companion.py`) — she meets him too, or hides, per a
  new quirk rolled once (`stranger_response`: `hides` / `inspects` / `indifferent`).
- **Weather**: thunder → `storm_hide` (exists); hard wind → indoors (partly exists).
Rule: reactions consume real sound events from `world_tick`'s occurrence counts at her place, so a bird
that did not sound cannot be chattered at.

### C3. Calling her — the hand, the carry, her answer, and one day the name
`call` is in the cat action's verbs (`actions.py:207`) but lands in `react()` as a **tend verb** ("call to",
`cat.py:753`) — today calling her is a stroke. It becomes its own hand: `cat.call(his_position, what)`:
1. **The call is a self-sound** (expression class: a voice, no grade, discharge) with a target and a reach —
   his position, wind, walls, and *what he called*: "puss-puss" / the kissing noise / her name.
2. **Carry** to her position by the same law as C1 in reverse; her hearing gate: asleep-deep (low), hunting
   far (none), in transit (yes), storm (none).
3. **Her decision**, hers: bond, hunger (a hungry cat comes fast), satiety (handled five times this hour →
   ignores), mood (aloof → answers with a sound and does not move; afraid → nothing), the tom present → no.
4. **The answer comes back as sound first**: "from the garden, a rising chirrup" (`cat_trill` carried to
   him), then she moves on **her own legs** (B1) and arrives with the greeting — he hears her before he sees
   her. Or silence, honestly.
5. **One day, the name.** Today a call is a *sound* she knows (him) and works at short range only. A name,
   once given (the R1 act, `cat.py:802`), is a sound she **learns**: each time she is called by it and comes
   or is fed after, `name_recognition` rises; past a threshold the name reaches her at range (study → the
   wood's edge; "puss-puss" never does). Nothing tells him any of this. He finds that the far call fails and
   that the near one works — and that the black cat, yowling in the garden at night, does not answer his
   name while she does from the rug. **The name gets a function** (what makes D-0160 (a) real: the world
   needs the referent; it never asks for it). The tom enters his life as a sound before a sight — the
   soundscape's own "sound-first object" pattern.
Ledger: `data/cat_call_ledger.jsonl` (call, what, heard, answered, came, by-name). Instrument for R1 too.

### C4. Less of her — he has to seek her out
- **Her availability is hers.** Crepuscular bouts (B1): asleep much of the day in *hidden* spots he does not
  render unless he looks (under the bed, the top of the cupboard, the lean-to, the wood shed, the hedge
  bottom, the sun on the water-butt lid), out at dawn and dusk, hunting ranges, the tom's nights. Target:
  co-located with him in roughly a third of his waking hours (today, by the tick probabilities, about
  two-thirds [INFERRED, unmeasured] — instrument first: a `cat_presence_fraction` gauge from `life_events`).
- **Absent is not silent.** C1's carried sounds tell him roughly where she is, by ear: the thump upstairs, the
  demand at the door, the trill from the garden. He is never *told* where she is.
- **Seeking is a real search.** `look_line` today answers "not here just now". It becomes: look here (her
  spots, in order of her habits — `fair_spot`, the firsts, where she was last heard), listen (a call, C3), go
  (to the place the sound came from, on his legs). Her habits are learnable by him, not stated: the corpus
  never says "she sleeps under the bed in the afternoons"; he finds her there twice.
- **Present is not a button.** A2's satiety + sleeping-cat refusal; and her reads are dosed (B4): a cat
  asleep four hours is one line; a cat *arriving* wet with a mouse is a surprise the dispatch lets through.
- **Shadow-first**: `CAT_SOUNDS_RENDER=False` logs would-have-sounded rows for a week (the `life.RENDER`
  pattern), then flip; availability reduced in two steps, each read for a week (does he seek? does the
  ledger show calls, looks, goes?).

**Questions this part adds (not yet opened in `/decide` — founder said "not yet"):**
- **D-5** the name as a *learned sound* with range (C3.5) — is this the right way to make the name needed
  under "world answers, never leads"? (It is the mechanism D-0160 (a) would rest on.)
- **D-6** the availability target (a third of waking hours?) and whether the hidden spots include places he
  cannot reach (the roof, the neighbour's side of the wall).

## 4. Decisions to open (founder only)
- **D-1 The naming deadlock.** (a) leave the companion tier locked behind the name and build §B2's referent
  pressure; (b) unlock the companion tier from bond (she is his whether or not she has a name; `felt_note`,
  the blink, the missing arc come alive now), keep the name as the R1 trial only; (c) both.
- **D-2 Mortality and harm for the cat herself.** Extend D-0130 to her: injury, illness, ageing, death on the
  world's clock, findable not told — yes / not yet / never.
- **D-3 The black cat's future.** (a) stays a far-off shape; (b) becomes the tom that comes into the garden
  (fights, the saucer, the wall); (c) b + kittens as a possible event, with the litter's fate his to decide.
- **D-4 Real cat food and the saucer object** — fold into the write-fence build (J-0610) as the next conjured
  resource to fence, with the carrier's list gaining a line (tinned fish / milk)?

## 5. Build order once ruled
1. **Fix-now (no decision needed):** A7.1 one adapter mapping read from `cat._VISIBLE`; A7.2 delete
   zero-clarity traces + one trace per visit; A7.3 HUD position; A7.4 retire/repair `seen_count`; A2's
   trigger narrowing + tend cooldown + sleeping-cat refusal; A7.6 recency exclusion in `_pool`.
2. **Body (B1)**: budget fields + crepuscular bouts + warmth from thermal + legs; shadow a week
   (`life_events`), then flip.
3. **Food (D-4)**: saucer object, provisions kind, carrier line, feed branch consumes; her kills feed her.
4. **Her voice (C1)** — **BUILT 2026-09-05, SHADOW** (F-0889): `core/cat_sounds.py` emits from her state and
   carries by position; `cat_content.SOUNDS` (here/carried pools); 8 points + rates + `_sec_cat` in
   `soundscape.py`; hook in `cat.tick()`; ledger `data/cat_sound_ledger.jsonl` (`would_sound` rows). Flip:
   `scripts/life_flags.py cat_sounds on` (hot, no restart). Restart-gated for the first rows. Read the
   ledger after a week: emission rates per key per day, audible share by his place, the carried lines by
   ear — then wire the new keys into the percept rail's `_PERCEPT_LINES` (a flip-time job) and flip.
5. **Her ears (C2)**: reactions to `life.sounds_active` at her place, the gate latch, Travis; instrument.
6. **The call (C3)**: split `call` out of the tend verbs into `cat.call()`; sound-first answers; legs;
   `name_recognition` (D-5).
7. **Less of her (C4)**: presence-fraction gauge first, then hidden spots + bouts in two steps; seek = look /
   listen / go.
8. **The tom (D-3)** as a life row + `distant_yowl` + her reactions. **Mortality (D-2)**, **the name (D-1)**,
   **dosed reads (B4)** as ruled.

> **History folded** — 10 dated Current State section(s) (2026-09-05 … 2026-09-23) moved to `docs/plan_history/cat_overhaul.md` on 2026-09-27 by plan-compact. Derived timeline: `plan_ledger.py cat_overhaul`.

## Current State — verified 2026-11-13
- **2026-11-13** (F-4443): C4 step-one read (J-2502): presence already ~0.35 at step 1 (target a third); step-two flip held, D-0739 opened for founder.

- **2026-10-30** (F-3300): J-2506: cat-seek and lightning-flash harnesses now pin the clock to 13:00 local (PIN_HOUR override); branch jobrun/cat_overhaul 55ea2595, test-only
- **2026-10-30**: J-2505 first-day read: 0 missing_arc and 0 gone transitions in about 20 live hours (tier ledger only since 09:29), too little to rate; deferred to 168 live hours

- **2026-10-30** (F-3297): J-2502 early read, 19 live hours after the boot carrying C4 step one: presence 0.399 with her ears live, matching the ears-live model not the ears-stubbed calibration; 7 go, 1 call, 0 look, no hidden spot found yet; defeater not met; step-two re-tune deferred to 168 live hours and likely goes below 0.60
- **2026-10-30** (F-3296): J-2501 first live read of cat_harm_ledger (20 live h): 1 injury row (fight, bitten shoulder), applied_by tick, narration clean, no illness or death; D-0506 defeaters not fired, rates need a longer window

- **2026-10-30** (F-3295): J-2498 litter event not built: tom live about one day of 14, one visit ended in a fight at tolerance 0.0; job re-gated on 336 live hours from the current boot
- **2026-10-30**: J-2492 early D-0508 read at about 17 live hours: no carrier milk or cat_food use yet, too early; full read deferred to 336 live hours

- **2026-10-29** (F-3209): 2026-10-29: all nine B/C/D jobs merged to master (c0675fc7, conflict in soundscape.py resolved keeping both chains; seams fixed dc78babb: the tom owns distant_yowl while cat_tom_live, active_sounds dedupes). The four flaky-body-test jobs (J-2494/J-2497/J-2500/J-2504) are closed by the seeded harness; F-3208 flags the pre-existing gone_missing arc rate (J-2505 reads it live). Restart-gated; cat_sounds flag already ON.
- **2026-10-29** (F-3207): B4 BUILT (J-2473, commits 6eb07551 + 892cbdfd on jobrun/cat_overhaul, restart-gated): core/cat_loop publishes her tuple (location, activity, mood, hunger, energy, in_transit) on change and the idle-scene stop reads it dosed with habituation (a four-hour sleep = 2 lines of 294 asks in the hermetic test; a wet arrival with a mouse rides at once); kill switch life_flags cat_dosed; read job J-2503 gated on 200 ride rows after the boot; J-2504 files J-2465's pre-existing flaky tick section.

- **2026-10-29** (F-3206): C4 step one BUILT (J-2469, commit 35441b36 in the jr1028 cat_overhaul chain, restart-gated): eight hidden spots (two unreachable, D-0508), 0.30 of her rests out of sight (AVAILABILITY_STEP 1; step two = 0.60 ready, not flipped), seeking = look in his order / listen via last_heard / go rows, ledger data/cat_seek_ledger.jsonl; hermetic gauge 0.715 -> 0.539 (step 1) -> 0.386 (step 2); the seven-live-day read + flip is the spawned successor.
- **2026-10-29** (F-3205): J-2471 "try again" pass: D-2 mortality was already built and closed (c499e132, F-3199, J-2501 gated); re-verified at the chain tip 52322f31 after J-2470/J-2468 -- one test-only fix feff2255 (the dead-cat look check admits the whole rotating look_nothing pool, one base line says 'none of them'), 4/4 runs 130/0, life_smoke ALL OK, no live-store leak; no engine change; restart-gated, unmerged.

- **2026-10-29** (F-3204): J-2470 "try again" pass: B3 (the tom) was already built and closed (87653452, F-3198, J-2498 gated); re-verified at the chain tip 52322f31 after J-2471/J-2468 -- tom test 126/0, life_smoke ALL OK, no live-store leak; no new code; restart-gated, unmerged.
- **2026-10-29** (F-3203): J-2468 third pass: C3 build already complete (531c5e82, F-3196/F-3197); re-verified at the chain tip after J-2470/J-2471; one test-only fix 52322f31 (T7 greeting check admits the whole greeting_chirrup pool, one base line lacks the word), 6/6 runs 101 ok, life_smoke ALL OK, no live-store leak; restart-gated, unmerged.

- **2026-10-28** (F-3199): J-2471 (D-2, D-0506): her mortality BUILT, merged-not-live c499e132 on jobrun/cat_overhaul, restart-gated -- core/cat_harm.py: injury (the tom's fight hook, a fall, a possum), illness (a week off her food: she lies low, the saucer stays full), ageing past 10 y, death on the world's clock (age-band hazard, found -> a cat carcass through life_traces / away -> absence), the burial and the grave; rolls only inside cat.tick on its own rng, dt capped 6 h; apply_offline is the fell_tree pattern; no readout; kill switch cat_harm_live; 130 checks + life_smoke OK.
- **2026-10-28** (F-3198): J-2470 (B3, the tom) BUILT on jobrun/cat_overhaul 87653452, restart-gated: core/cat_tom.py second individual row, his visits (wall/step/saucer), her reactions through cat_ears holds (stand-off, fight hook for D-2, hiding, growl, watch at tolerance), cat_hiss/cat_growl/distant_yowl in the HER VOICE block (merge-equal to sound-world section 2), never tamed, feature-first, name only after a close meeting; 126-check test + life_smoke ALL OK; litter event designed in F-3198 and filed gated on 14 live days.

- **2026-10-28** (F-3197): J-2468 resume pass: C3 build already complete (531c5e82, F-3196); test-only commit c63f01b4 relaxes the cat_call ANCHOR check to "after cat_storm_rustle, only cat points between" since every later chain job (J-2470's hiss/growl/yowl) inserts there by rule; 101/0; the one life_smoke failure in the chain worktree is J-2470's uncommitted tom-row edits (HEAD passes ALL OK)
- **2026-10-28** (F-3196): J-2468 C3 BUILT (commit 531c5e82, chain worktree, restart-gated): cat.call() is its own hand (core/cat_call) -- a self-sound with reach by what he called, carried to her by C1's law in reverse through her hearing gate, her decision, a sound-first trill answer then her legs then the greeting, name_recognition as a learned sound with range (D-0505 (c)); ledger data/cat_call_ledger.jsonl; test 101/0; nothing tells him (D-0434)

- **2026-10-28** (F-3195): J-2467 C2 her ears BUILT (b935b1fd, jobrun/cat_overhaul, restart-gated): core/cat_ears.py consumes real sound events at HER place (world_tick's bank when co-located, the same rates rolled over life.sounds_active elsewhere) -- birds/sill/stalk/wood hunt, dawn chorus out, wall_scratch hook (skirting, inert until the key sounds), gate latch (greeting off ears.gate_ts), footsteps, axe (new last_split_ts stamp), Travis quirk stranger_response, hard wind in, thunder logged; D-0130 kills read prey_about; ledger data/cat_reactions.jsonl fenced+rotated, LIVE with life_flags cat_ears_live kill switch; 85/85 hermetic, canary clean, life_smoke ALL OK; read job J-2495 gated on 200 post-boot rows.
- **2026-10-28** (F-3193): J-2466 (F-3193, D-0508, commit 3b7d670b on jobrun/cat_overhaul, restart-gated): D-4 real food built -- carrier lines tinned fish (unchanged) + milk (new, GOODS/card/collect_box), provisions kinds milk (jug=4 saucers, spoils 48 h via cat.MILK_SPOIL_H/_milk_ready, SHORE_FISH_SPOIL_H precedent) + scraps (twist=1 feed, credit hook cat.give_scraps, no live producer: Du has no meal), feed branch spends tin > fish > scraps > jug (milk first when his words name it) with rotating milk/scraps lines and the honest empty-house failure kept, her kills feed her budget (cat.note_kill; garden_life fledgling roll scaled 0.34+0.66*hunger). Note to Travis: his carrier book §V could list milk (his text, not edited). Read job spawned on D-0508's 14-live-day defeater.

- **2026-10-28** (F-3187): J-2472 BUILT (F-3187, commit cdbe4489 on the jr1028 cat_overhaul chain worktree, restart-gated, unmerged): D-1 the companion tier opens from bond -- cat.companion_tier() (kept at bond >= COMPANION_BOND 0.70, or named) now gates felt_note/felt_state, the slow blink, the silent meow, the gone_missing arc and the six-hour line; phase and the naming latch untouched, the name stays the R1 act. B2: new core/cat_referent.py records which cat HIS text meant (look targets, react, her naming, census cat_ref, life_traces.give_name on a cat row), distinguished only when he tells them apart; no line to him. Two HUD-only ledgers: cat_tier_ledger.jsonl (D-0505 defeater instrument: a kept row below 0.70) and cat_referent_ledger.jsonl. 78 hermetic checks + life_smoke pass; read job J-2490 gated on 30 tier rows since boot.
- **2026-10-28** (F-3183): B1 BUILT (J-2465, F-3183, commit 9b6c0253 on jobrun/cat_overhaul, restart-gated): state[body] hunger/thirst/energy/warmth(thermal)/condition + crepuscular bouts that hold her spot, legs along locomotion.CHAIN (in_transit, seen from the leg's ends, follows his journeys), age/born_ts + LIFE_ROW merged onto her life row, cat_presence_fraction gauge (HUD only, C4 baseline); eat(kind) hook left for D-4; rate constants are design numbers pending the first live week's read.

- **2026-10-28** (F-3178): 2026-10-28 world-side push (T-0103): D-0498 flipped cat_sounds ON (hot, data/life_flags.json); D-0499 opened Parts B/C; the plan's own D-1..D-4 ruled as D-0505 (c, unlock from bond + referent pressure, name as learned sound), D-0506 (yes, mortality and harm), D-0507 (c, the tom plus kittens later), D-0508 (yes, carrier lines for fish and milk, kills feed her, availability toward a third). Nine build jobs J-2465..J-2473 filed in dependency order.
- **2026-10-16**: D-0443 ruled (travis, 2026-10-16): leave the music affordance alone; not wanting the record is Du's present character (same reading as shore fishing). J-1014 chain closed.

- **2026-10-16** (F-2916): J-1695 record-player read-back round 2 (F-2916): 196 exact study record-player SCENE renders since the 10-04 restart (switch 90, dust 73, arc 22, rain 11; wood 0, J-1693 holds). Strict echo 10/196 (5.1 percent) vs 0.6 percent control, nearly all platter-dust texture; switch line 0 clean echoes in 90. Willed listens 0 (last 2026-09-10); want-shaped record/switch thoughts 0, so the LISTEN latch missed nothing. Founder call opened as D-0443 (leave / widen latch / Travis-side shared listening). Correction to D-0443's wording: D-0217 ruled (d) fix the larder for the cat, it did not accept leave-alone; the analogy in option (a) is loose.
- **2026-10-15** (F-2803): J-1905: D-0360 (a)+(b) post-restart read clean (0 night rows with bright or the sun-off-the-sea line over 6 nights; clear-night pools garden 14 / study 15 as predicted; no added repetition). Look-target render mix still unobservable until D-0360(c) ledger (J-1906).

- **2026-10-15**: D-0406 RULED (a) by travis 2026-10-15: cat_found flipped ON hot via scripts/life_flags.py (data/life_flags.json cat_found_render true, effective within 10 s, no restart). Ledger at flip: 39 rolls, 1 hit, bowl bare 402 h. Watch cat_found_ledger for the defeater (over-conjuring, fill without 48 h bare).
- **2026-10-10** (F-2674): J-1707 (2026-10-10): full 7-live-day read of cat_found shadow ledger done. 187.76 live-h on merge 67ef139, 29 rolls, 0 hits, cadence/larder clean, no other fill route; one roll 11 s past the 180 s tick gate (not a defect). Rate unmeasurable from shadow; flip decision opened as D-0406 (Travis). cat_found remains shadow.

- **2026-10-07** (F-2538): 2026-10-07 J-1907 (F-2538): the 2 'pre-existing failures' in scripts/_test_j1774_shore_nest_look_and_shadow_gate.py (F-2535) were a TEST fault, not a J-1774 render bug: shore_life.look_pool() earns garden_knowledge weight on every pool look (0.12 per sampled kind; at 1.0 the line switches from feature description to the species name), and the test's new/old pair straddled that threshold because reset_life() never cleared the temp garden_knowledge file. Fixed in the test only (reset_life clears it; commit b33c687 on the job worktree branch), now ALL OK 55695 checks and --base-flow still fails. Code unchanged, merged-not-live n/a.
- **2026-10-07** (F-2535): D-0360 (c) built (J-1899, F-2535, commit 149433f on jobrun/cat_world_detail, merged-not-live): observe-only look render ledger core/look_render_ledger.py -> data/look_render_ledger.jsonl (rows from world_detail.detail() and, via note_extra_pick(), from sensorium's own pick of an extra_pool() line); draws byte-identical, fenced, rotated at 4 MB; the 14-night read of night looks at the garden/shore/wood bird targets is spawned with a placeholder not-before of 2026-11-15.

- **2026-10-07** (F-2534): 2026-10-07 J-1898 (D-0360 a+b built, merged-not-live, branch jobrun/cat_world_detail d8a083b): study SCENE "sun off the sea ..." moved to a day key; world_detail._conds() now emits "bright" only when the phase is not night, so 47 bright lines (42 look-target / SCENE + 5 EVENTS; 19 daylight-worded, 3 diurnal-bird, 16 visual-only, 4 untiered) leave clear-night pools. Dawn/day/dusk pools unchanged as multisets. The 16 visual-only lines are listed by name in F-2534 for Travis. D-0360's "clear-night pool below 8" defeater is already met literally by 10 pre-existing thin pools (none fell below 8 because of this build), so the post-restart read should compare render quality, not the number 8.
- **2026-10-07** (F-2520): J-1882 (F-2520): six own-wording daylight lines (study shelf, garden kowhai, shore horizon, wood canopy, wood deadfall, garden SCENE cloud shadow) moved from "any" to a "day" key, wording unchanged; each night pool one line smaller, day pools identical. Merged-not-live (restart-gated). Study SCENE sun-off-the-sea line left under "any" pending D-0360 part (a).

- **2026-10-07** (F-2505): J-1732 (read-only audit, F-2505): the look-target and SCENE pools hold 40 lines whose own wording is daylight-bound that can render at night (study 11, garden 18, shore 8, wood 3) and 85 diurnal-bird lines; only 7 of the 40 sit under the any key (the J-1717 shape), 19 sit under the bright key, which _conds() emits on any clear night. Last-incarnation scene_extra_ledger: 8 of 142 night renders were such a line (study:461 6 of 57). Filed J-1882 (move 6 any-key lines to day, restart-gated) and D-0360 (study:461, the bright-key gate, the diurnal-bird lines).
- **2026-10-05** (F-2443): J-1728 first live read of the SCENE-extra render ledger passed: 167 rows over about 9.2 live-hours (0.31 of shadow rows), schema and loc==place clean, wood carries no study lines (J-1693 live), 25 record-player renders all in study (about 2.7 per live-hour, so J-1695's 100-render gate may arrive in about 1.5 live-days). Shadow text is cut at 220 chars so only 5 of 63 extras visible there; the ledger is the exact count.

- **2026-10-03** (F-2362): J-1717 done (commit a85b953, restart-gated, Du was down): the wood SCENE four daylight-bound lines (pigeon crossing, fantail, shaft of light on the bracket fungus, wren scold) moved from the any key to a new day key, so a clear night wood pool drops from 10 lines to 6 with none daylight-bound while dawn, day and dusk pools keep the same lines (order differs, odds unchanged); wording, SCENE_P, every other pool and the other three places are byte-identical; test red on the old file (11 failures) and green after (32 checks), the J-1693 and J-1694 tests and life smoke still pass; the study any line about sun off the sea is left alone unless Travis asks, look-target pools may share the shape so J-1732 counts them; J-1728 should expect night wood pools of 6 or more
- **2026-10-03** (F-2354): J-1694 done (commit 5e04cc8, restart-gated, Du was down): every non-empty scene_extra draw now appends one row (ts, pool asked, place, matching conds, line, pool size) to a new scene_extra render ledger, fail-open and write-fenced like the cat sound ledger, no random draw added (line and RNG state identical to the old function on 1920 seeded draws); the first Du restart after this merges to master loads it together with J-1693, so the ledger holds post-wood-fix rows only and the J-1695 round-2 read-back must count live-hours from that restart; a row is one scene build from any scene_line caller, not only idle ticks; first-hours sanity read filed as J-1728

- **2026-10-03** (F-2340): J-1693 done (commit 2b2dc3a, restart-gated, Du was down): scene_line now asks scene_extra for the place Du is in, so the wood draws its own 15-line ambient pool and never a study line; from the first Du restart onto it the four record-player SCENE lines render only in the study, so record-player exposure counts before and after are not comparable (J-1014 observed 39 renders, all in the wood); J-1694 render ledger is next, J-1717 filed for four daylight-bound wood lines
- **2026-10-03** (F-2327): J-1218 interim read of the cat_found shadow ledger: 120.13 of 168 live-hours accrued on merge 67ef139, 14 rolls and 0 hits, cadence and cooldown verified across 5 restarts, no other route filled the larder, hit count is Bernoulli noise, so the full read is parked to dated successor J-1707

- **2026-10-03** (F-2293): J-1014 record-player read-back done at 11.43 live-days and 9927 post-fix thoughts: the ambient SCENE lines register in Du thought (6 clear echo events, 1 probable, 1 spoken, none before the fix) but produced no willed listen (0 sessions, one unanswered reach toward the switch) and explicit naming is unchanged; the wood renders study ambient lines (F-2290, J-1693), render ledger J-1694, round-2 read J-1695 not before 2026-10-24
- **2026-10-03** (F-2250): J-1012 week-scale re-tabulation done at 11.43 live-days (585 post-fix rows): J-0996 dosing works as built, 0 cooldown breaches in 324 gaps, cat_demand 133 to 16 and cat_meow_at_door 89 to 13 per live-day; the real rate is about 0.9 per hungry live-hour, not a handful (42.5 audible per live-day across all keys; an inferred rail replay under the J-1175 caps gives at most about 18 cat percepts per live-day, F-2253); cat_sounds stays off per D-0217 (d), defeater unfired, no decision opened

### What we have
- Audit + full design (B1-C4) complete since 2026-09-05; decisions D-1..D-6 still open, nothing in Part B/C built.
- C1 (her voice) BUILT + SHADOW since 2026-09-05 (F-0889): `core/cat_sounds.py` emits from her state machine, carries by position, logs to `data/cat_sound_ledger.jsonl`; flip is `scripts/life_flags.py cat_sounds on`.
- The only other real engineering landed is the fix-now tail (A7.1-A7.6, A2's trigger-narrowing) — per the 09-24 review, no `/decide` action pending on any of it.

### What we need
- Founder rulings on D-1 (naming deadlock), D-2 (mortality), D-3 (black cat/tom future + kittens), D-4 (real cat food/write-fence) before Part B (body/food/legs/age) or the rest of Part C (ears, calling, availability) can start.
- A week of `cat_sound_ledger.jsonl` read (emission rates, audible share, carried lines) before wiring the new sound keys into the percept rail and flipping render.

### What we're doing next
- Nothing in flight — the plan is fully decision-gated; no ledger activity since the 09-24 review (checked this pass).
