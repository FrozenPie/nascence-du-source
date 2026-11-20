# The Living World — every creature with a proper life: active hours, lifespan, how often seen, light, sound

*Status: **🟢 LIVE since the 2026-09-09 flip (D-0166)** — L1-L4 all built and restart-gated (J-0510-J-0513);
a long defect-fix tail is mostly closed, two live-evidence reads still pending. Parent of
[[garden_living_upgrade]] (its garden chapter: insects, soil, plants, growth, death). Builds on
[[item_and_population_factories]] (the grain), [[sound_causality]] (BUILT: the world is state on its own
schedules, Du only asks), [[sound_world_expansion]] (PARTIAL), [[transport_manager]] (BUILT, shadow).*

```plan-state
stage: live
phase: Live since the 2026-09-09 flip D-0166; long defect-fix tail mostly closed; the J-1192 package read is done (2026-10-03, F-2308); one live-evidence read still pending (J-1676, the carrier matches leg)
verified: 2026-11-14
evidence_read: 2026-10-16
gate: J-1192 gate MET 2026-10-03 at 7.80 live days on fbf6423 (F-2295); read reported in F-2308
next: After the next boot: J-2246's spawned read of data/nest_gate_shadow.jsonl diverted rows against D-0444's defeater over the first 3 live days
cluster: 6
```


**Founder, verbatim (2026-09-02):** "We probably should do this with a whole heap of other life. Birds,
animals (like hedgehogs). They should have their proper lives, e.g. active hours, life span, how often they are
seen. They also should be interactive with light and have sounds. Anything else you think might be helpful."

---

## 0. What is true today (read, not remembered)

**Creatures exist as four different things, none of them a life.**
1. **Sound points** — 58 in `core/soundscape.py::_SOUNDS`, 20-odd of them creatures (gulls, tūī, blackbird,
   morepork, oystercatcher, bees, wood pigeon, wren, fantail, riroriro, kingfisher, shag, cicadas, crickets,
   robin, penguin, the moth). `active_sounds()` gates them by location × day/night × season × wind/wet — a
   presence rule, but a static list, no numbers, no memory of having been heard.
2. **Learnable voices** — 9 in `sound_knowledge.AUDITION` (penguin, fantail, riroriro, kererū, kingfisher, shag,
   robin, cicada, cricket): the one place a creature has an epistemic life (exposure → sighting → book name → learned).
3. **Content-pool lines** — `world_content_{garden,shore,wood,study}.py` and `sensorium.py`: hedgehog (3 lines +
   damp-night prints in `fieldcraft.py`), thrush, starling, tauhou, magpie, silvereye, skink, gecko, pūkeko, heron,
   swallow, sparrow, gannet, karoro, tōrea, dolphin, whitebait, rabbit, possum (one study line), bees, butterflies,
   spiders, worms. Gated by season/weather/phase where the author remembered to; no state.
4. **Real state, four cases** — the cat (`core/cat.py`: phases absent → appearing → kept → companion, bond, hunts,
   brings mice, takes fledglings — the one INDIVIDUAL life); the blackbird nest and kererū nest (stage machines in
   `garden_life.py` / `wood_life.py`: building → eggs → chicks → fledglings, the cat can take one); the fur seal
   haul-out (winter days, 3–9 h) and kororā burrows (dusk Sep–Feb) in `shore_life.py`; glow-worms (dark, damp,
   still, at the spring, only when he looks) in `wood_life.py`; the lamp moth density (`sensorium.py`).

**What he has reached for:** `docs/reviews/observe_inventory_2026-09-02.md` — birds 51 phrasings / 271
mentions (oystercatcher 101, blackbird 23, gull 23, the dead gannet 12, tūī, shag, kingfisher, thrush), mammals
(cat 92, seal-pup 16, hedgehog 4, mouse 2), insects 42 / 114. Every one answered by a place's generic frame
unless it happened to be the cat, the sea, or a fixture.

**Light:** day/night/dawn/dusk phase exists; the lamp and candles exist (candles are carryable — the shore cave
already reads a carried candle); moths come to the lamp; glow-worms need dark. Nothing else in the world knows
whether Du is carrying light or standing in it.

**`item_and_population_factories.md` names the gap itself:** "no notion of how many (population size), no seasonal
presence curve." This plan is that gap, for every creature.

## 1. Laws (all in force; this plan adds none)

- **The world answers, never leads.** Species names are hidden truth, earned by sighting + exposure + a book
  (the pōhutukawa / audition law). Grandfathered names (blackbird, oystercatcher, the cat) stay.
- **State, not events; no diary** (sound_causality). A creature's life advances on its own clock whether or not
  he is there. What he did not witness did not happen for him. The Transport Manager weights what is new,
  rarer or later than usual — a life engine is exactly the freight it was built for.
- **Population grain by default; individual only by the three triggers** (kept, given, repeatedly re-encountered at
  one spot). The cat is the individual precedent; the hedgehog that visits the saucer nightly would be the next.
- **World-truth gate.** A line may only name what the life engine says is present, awake, and visible.
- **Zero-LLM world side; additive-only; fail-open; things are their own lists.**

## 2. The life model — one schema for every creature

Each species is a row in one table (`core/life.py`, or one table per place module — founder's call in §5.1),
advanced by one `advance(now, dt, world)` on the sensorium tick, the way `garden.advance` already runs:

| Field | Meaning | Founder's ask it serves |
|---|---|---|
| `places` | where it can be (garden/shore/wood/study/cottage-edge) and the spots within | how often seen |
| `active_hours` | a daily activity curve by phase (dawn/day/dusk/night) — nocturnal, crepuscular, diurnal | active hours, light |
| `season_curve` | monthly presence 0..1 (resident, migrant with arrival/departure months, hibernator) | how often seen |
| `weather_gate` | rain/wind/storm/frost/fog effects on activity (small birds grounded in a gale; worms up after rain) | how often seen |
| `light` | response to light: drawn (moths), avoids (hedgehog, possum, mice, wētā), needs dark (glow-worms), eye-shine in a carried candle (cat, possum) | interactive with light |
| `sound` | its sound points (existing `_SOUNDS` keys) + when it makes them (dawn chorus, contact calls, alarm when the cat is out, the morepork's hours) | sounds |
| `count` | a population size band per place and season ("one", "a pair", "a few", "a flock") — rate, not individuals | how often seen |
| `lifespan` | typical years, plus life-cycle stages where they matter (egg/chick/fledgling; queen/worker; pup/adult; hibernation) | life span |
| `diet` / `interactions` | what it eats and what eats it (cat ↔ mice, fledglings; ladybird ↔ aphids; hedgehog ↔ slugs; possum ↔ pōhutukawa buds; gull ↔ crabs; kingfisher ↔ whitebait) | anything else helpful |
| `traces` | what it leaves (prints, droppings, feathers, casts, shells, nests, burrows, holed leaves, a carcass) — `world_traces` objects, findable later, the fieldcraft tracking hand's evidence | anything else |
| `responds_to_du` | feeding (feed_birds, the saucer), noise, the cat's presence, mowing (blackbird follows the shears), digging (worms up → blackbird) | anything else |
| `hidden_truth` | species, `book_names`, `book_sounds`, feature-first render lines; grandfathered flag | the naming law |
| `visibility` | sighting probability given active × present × light × his standpoint × what he is looking at — the roll `look_binding` already makes for sounds | how often seen |

**Individuals** (`kind: individual`) share the schema plus a name-slot, a home spot, a bond, a history and a
death — the cat's model generalised. Graduation from a population to an individual is an event the ledger records.

## 3. The cast (NZ coastal cottage: garden on the hill, shore below, the little wood, the study)

Proposed, feature-first, every species hidden-truth unless grandfathered. Active hours / season / light / sound
are the row fields; here only the character of each.

**Garden.** blackbird (grandfathered; nest exists; follows the shears and the spade; dawn song), song thrush (the
anvil stone — a real trace: broken snail shells), tūī and bellbird (kōwhai in spring, pōhutukawa in December,
harakeke in summer; the tūī's clatter), tauhou/silvereye flocks (winter, the hedge), riroriro (unseen, learned by
voice — exists), fantail (follows his feet — exists), kingfisher (fence post sentry, dry rattle — exists), starlings
(the powerline, prospecting the tī kōuka head), house sparrows (the doorstep), welcome swallows (over the lawn in
summer evenings), shining cuckoo (October arrival, parasitises the warbler's nest — a drama he can only infer),
kererū (the kōwhai, wingbeats — exists), morepork (night, from the wood — exists), **hedgehog** (nocturnal, out from
dusk, hibernates May–September, snuffles and rustles in the hedge bottom, eats slugs — the garden's own pest
control — and eggs, avoids the lamp's throw, prints after damp nights exist, may come to the saucer: the
graduation candidate), **possum** (night, in the tree, eats pōhutukawa buds and the strawberries — real damage he
can find in the morning; eye-shine in a carried candle; the cough-and-hiss; a founder call on trapping §5.3),
mice (the study at night, the cat's prey — exists), rabbit (dawn, lawn edge), skink (warm stones, the wall, day),
gecko (the harakeke at night). Insects per the garden chapter.

**Shore.** variable oystercatcher (grandfathered, the pair, nest on the shingle — `oyc_nest` exists; the scream),
red-billed and black-backed gulls (karoro — two kinds, one learned by size and voice), white-fronted terns (summer,
diving), gannets (offshore all year, the plunge; a dead one on the tideline — already observed 12×, so death and
carcass are part of the model), shags (the rock, wings out — exists), reef heron (grey, the rock-pools at low
tide), pied stilt / dotterel at the stream mouth, kororā (exists — dusk Sep–Feb, braying), fur seal (exists —
winter haul-outs; a pup some years), dolphins (rare, offshore, summer calm), whitebait in the stream mouth
(spring), eels (dusk, the stream — he read of them), crabs, starfish, limpets, anemones (exist as things; give
them tide-state presence), sandhoppers under the log.

**Wood.** kererū (exists), fantail, riroriro, robin (exists as voice), grey warbler, morepork (night — exists),
long-tailed bat / pekapeka (dusk over the canopy edge on warm still evenings — rare; he has just read two bat
papers: the world holds one, it does not point at it), wētā (night, log basket / under bark — exists as a line),
glow-worms (exist), cicadas (summer — exist), fungi (autumn — exist), possum (night, the oak), mice.

**Study / cottage edge.** the cat (individual — exists), mice (night — exists), moth at the lamp (population —
exists), borer beetle (from the woodpile), wētā (the log basket), swallows under the eaves (summer), a gecko on the
warm chimney stones, the morepork heard through the window.

## 4. Anything else that would help (my additions, for the founder to keep or cut)

1. **Death is part of a life.** Lifespan means things die: the dead gannet on the tideline (he already watches it),
   a fledgling the cat took, a hedgehog that did not wake, a possum in a trap, a dead mouse on the mat. Carcasses
   are traces that decay on the world's clock (fresh → picked → bones → gone), findable, keepable (a feather, a
   skull — "To a Skull on My Bookshelf" is on his shelf). This is the world's own harshness (garden plan decision 2).
2. **A migration calendar.** NZ has real arrivals he could notice year on year: shining cuckoo (early October),
   godwits (September, if the estuary is in reach — founder call), white-fronted terns (summer), kororā ashore
   (Sep–Feb), seals hauling out (winter), silvereye flocks (winter), swallows (summer). "Longer than usual since"
   and "earlier than usual" are exactly the Transport Manager's weights.
3. **Interactions are the drama.** cat ↔ fledglings/mice/skinks; hedgehog ↔ slugs (fewer slug trails when a
   hedgehog is resident — a binding he can make); ladybird ↔ aphids; possum ↔ pōhutukawa buds and strawberries;
   kingfisher ↔ whitebait; gulls ↔ the oystercatcher's nest; blackbird ↔ worms turned by his spade; feed_birds ↔
   sparrows and the blackbird (the hand that has never fired gets a reason); the saucer ↔ hedgehog; mowing ↔ the
   thrush's anvil. Each is a `diet`/`responds_to_du` row, not special code.
4. **Light as a world variable, not a phrase.** A `light_at(standpoint)` value (sun by azimuth, the lamp's throw
   through the window onto the lawn, a carried candle's small circle, moonlight by phase, the fire's glow at the
   door) that every creature's `light` field reads: moths come to it, the hedgehog stops at its edge, eye-shine in
   it, glow-worms only outside it. Gives the candle a reason to be carried out at night; the morepork is heard,
   never seen, unless he is dark-adapted. `light_band` already exists on the experienced tuple — this is its
   world-side twin.
5. **Sound from the life engine, not static lists.** `active_sounds()` asks the life table who is present and
   awake instead of its hand-kept rules; dawn chorus becomes the sum of who is there; an alarm call when the cat
   crosses the lawn; the morepork's hours; silence after a hard frost. The 58 sound points stay as the vocabulary;
   the gating moves. Every new creature gets a sound point only if it truly makes one he could hear from where
   he stands (the tree-falls law).
6. **Individual graduation as a witnessed event.** The hedgehog at the saucer for the fifth night, the
   oystercatcher pair at the same rock every spring, the seal that hauls out on the same shelf: the third trigger
   fires, the creature gains a history and (if he chooses) a name he gives — his to give, never the world's.
7. **A "who's about" HUD panel** reading the life table: present / awake / visible per place, last witnessed, days
   since — the observability the current instruments lack for wildlife.
8. **Books as the naming path, deliberately.** The bookshelf already holds *What Bird Is That*, *Indian Birds*,
   *Wild Animals I Have Known*, *The Burgess Bird Book*, *The Life of the Spider/Fly*, two bat papers. `book_names`
   per species lets those readings do the naming, as they already do for the nine voices.

## 5. Founder decisions — RULED 2026-09-02 (J-0509, all by travis, each with a defeater in the ledger)

1. **D-0128 Engine:** one `core/life.py` schema + advance + visibility roll + `light_at`; each place module owns
   its rows; insects/birds/mammals are rows in it, never second engines; the cat stays in `cat.py` behind an adapter.
2. **D-0129 Naming:** hidden truth + books for every NEW species (feature-first until sighting + exposure + a book
   name), `book_names` on every row; grandfathered names (blackbird, oystercatcher, the cat) kept.
3. **D-0130 Harshness:** all four — the cat may kill (fledglings, mice, skinks); possums do real findable damage;
   carcasses appear and decay as traces (fresh → picked → bones → gone), the tideline gannet first; **a trap hand
   exists** as a deed with moral weight. Defeater: kills dominating idle thought, a wrong B4 bind, or a weightless trap.
4. **D-0131 Night light:** a lantern in the study (oil from the existing can, real fuel cost, real circle) **plus a
   dark-adaptation rule** (standing dark lets him see more: glow-worms, the morepork's shape, stars, eye-shine).
   Both feed `light_at(standpoint)`. Candles unchanged.
5. **D-0132 Reach:** stay at cottage / garden / shore / wood for now; estuary migrants pass over (godwits as a
   September sound and sky line). Explicit revisit after the life engine is live and sighting rates are calibrated.
6. **D-0133 §4 additions:** all in scope — migration calendar; interactions as rows + light as a world variable;
   sound gating moved onto the engine + individual graduation; who's-about HUD + books as the naming path.

Still to calibrate, not a ruling: target sighting rates per species per week, read after two weeks live (§6).

## 6. Metric sheet (read after two weeks live)

- **Answered-look rate** per place (the garden chapter's metric #1), creatures separately.
- **Sightings per species per week** vs the row's intended frequency; rarities actually rare.
- **Names earned** (exposure → book → learned), the audition's gauge extended to sight.
- **Traces found and bound** (prints, shells, feathers, damage) via the tracking / investigate hands.
- **Interactions witnessed** (cat–fledgling, hedgehog–slug trails falling, possum damage) as ledger events.
- **Light:** share of night sightings that were light-consistent (nothing seen in the dark that needs light).
- **Sound:** dawn-chorus composition matches who is present; zero sounds from absent species.
- **Transport Manager freight:** "earlier/later/rarer than usual" items rising from the life engine.

## 7. Build order (shadow-first, additive) and jobs

| Step | What | Where | Job |
|---|---|---|---|
| L0 | Founder decisions §5.1–5.5 | /decide | J-0509 |
| L1 | The life engine: schema, advance, visibility roll, light_at, sight-binding for creatures, "who's about" status | `core/life.py`, `sensorium` | J-0510 |
| L2 | Birds, all places, migration calendar, nests folded in, sound gating moved onto the engine | place modules, `soundscape.active_sounds` | J-0511 |
| L3 | Mammals, reptiles, others: hedgehog, possum, mice, rabbit, skink, gecko, bat, seal/penguin folded in | place modules | J-0512 |
| L4 | Traces, deaths and carcasses, interactions, individual graduation, HUD panel | `world_traces`, `keepsakes`, `hud/server.py` | J-0513 |
| G | The garden chapter (insects, soil, plants, growth, death) | [[garden_living_upgrade]] | J-0503–J-0508 |

L1 first: the garden chapter's insect factories (J-0504) should be rows in this engine, not a second engine.

> **History folded** — 48 dated Current State section(s) (2026-09-02 … 2026-09-24) moved to `docs/plan_history/living_world_upgrade.md` on 2026-09-27 by plan-compact. Derived timeline: `plan_ledger.py living_world_upgrade`.

## Current State — verified 2026-11-14
- **2026-11-14** (F-4463): J-2260 D-0444 go-live read: gate live since 10-16 merge; 5 diverted looks (1 miss, 4 sightings; F-4463 claim text says 6, correct count is 5), all shore oystercatcher, all invariants hold, bird credit untouched, no blackbird/pigeon pairing yet (defeater arm unexercised). Recognition suffix appended after bird line is pre-existing J-1166 behaviour.

- **2026-10-30** (F-3310): J-2091 D-0335 follow-up: robin@wood graduated 10-17 on 5 separate visits, clauses 1 and 2 NOT MET; kereru 4, kingfisher 3, bumblebee 3 not yet graduated; D-0335 stands
- **2026-10-16** (F-2945): J-2246 built D-0444 option A: the nest-object gate answers live (nest line always, bird line appended on a sighting, credit untouched, only at the bird's own nest place); restart-gated, commit 1d54851f, 436-check test with teeth

- **2026-10-16** (F-2939): J-2227 built shore nest look fixes: skate egg no longer reads as the oystercatcher eggs (data-derived layer set), egg-scrape reads as the scrape, and new fenced ledger data/shore_nest_looks.jsonl logs every shore nest-look answer; commit a31068ee, restart-gated, awaiting merge and boot
- **2026-10-16**: D-0444 ruled (travis, 2026-10-16): nest-object gate goes LIVE with bird pairing; build job spawned, composed with J-2227; J-2228 stays as the post-nest read.

- **2026-10-16** (F-2917): J-1796 (2026-10-16) read D-0345's shadow nest-object gate over the 2026-10-09..10-16 live window (6.97 live days): 30 nest-class looks at the shore (4.3/day); the gate logged all 5 oystercatcher nest looks, no wrong shape; the bird's roll missed in 2 of 5; the sighting pairing reads coherent; blackbird/wood pigeon 0; nest_exists false 0 (nest stood all window). Place look routes 23 no-bird looks to the correct three-eggs line (reconstructed; answers are not logged); edge defects 'the skate egg' and 'the egg-scrape' plus the logging gap go to J-2227. Go-live question opened as D-0444 (Claude recommends pairing). J-2228 reads the 'find none' side after the nest ends (~10-29).
- **2026-10-15** (F-2823): J-2133: F-2806's 'standpoint_move answers 0 sub-place declined moves' was a selection artifact; standpoint_move is wired and answered 21 times post-boot as move/FIRE (F-2823). ~80% of declined sub-place rows never pass dispatch._move()'s verb gate (non-motion phrasing), which is the honest-decline design, not a wiring bug.

- **2026-10-15** (F-2806): F-2806 (J-2132): post-boot (10-09..10-15) hand-declined move rate ~31/day; sub-place feature objects ~9/day, supersedes D-0319's 40/day denominator. standpoint_move answers not visible for these in hands_trace; follow-up J-2133. D-0428 still open.
- **2026-10-15** (F-2799): J-2090 (F-2799, D-0428): Du's move intent fell ~95% at the 2026-09-28 19:08 boot, not from J-1591's standpoint move but from J-1362's boredom recalibration (felt-note on 55-75% of idle prompts -> ~1%; escape lines told him to go out). Not an instrument artifact. D-0319's 40/day denominator is retired; D-0428 asks the founder whether the lower baseline is intended.

- **2026-10-15** (F-2717): J-1795 (2026-10-15): D-0271 live read CLEAN over 184.7 live-hours / 12,499 hands_trace rows on J-1755 guarded bare candles/candle: 2 candles FIREs (10-11, both genuine fetch wills), 0 wrong FIRE/STAGE, 0 dropped wills, 0 candle-driven take_book, 0 collect rows; D-0271 guarded form can be treated as settled (founder call, not ruled here).
- **2026-10-15** (F-2716): J-1794: D-0335 first live read at 7.69 live-days on the J-1766 build: clauses 1, 2, 3 all NOT MET (one graduation since the live start, shag@shore 10-09 16:04:51, five visits 3 to 13 days apart; rule delayed 0 graduations; 45 of 45 recognition lines at the home place); D-0335 stands, no decision opened; robin half of clause 2 untested (no robin look since 09-27).

- **2026-10-15** (F-2714): J-1607 D-0319 live read (F-2714): standpoint move live since the 09-28 19:08 boot not 10-09; 27 arrival narrations; addressable declined share 95.7 pct before vs 35.7 pct live (10/28); 14-live-day gate not met (9.75 live days); unconditional drop confounded by a whole move-volume collapse at the 09-28 restart (J-2090); D-0319 defeater not triggered.
- **2026-10-15** (F-2712): J-1726 live read at 6.03 live days on the J-1698 build: 0 recognition lines away from home (38 of 38 suffix lines at the graduation place; 0 away-from-home sightings of a graduated multi-place key; blackbird sightings drift +1, all pre-restart). 7-day stop rule not yet reached, successor J-2087 re-reads after it. Shag graduated 10-09 on five encounters spread over a month (F-2712 wording over 9 days is wrong).

- **2026-10-15** (F-2710): J-1676 read 2026-10-15: Travis's care package opened 10-12 18:34 (10 match boxes, 500 vs _MAX_STEP cap 3) survived J-0573's sync_guarded: no emptied row for matches/oil, no sync_reconciled row, study.matches 497.0 == shelf 497.0 (one box 47/50 from normal use); guard shown generic across care_package and carrier routes, carrier-box matches leg itself still unexercised (next visit 10-21, no note).
- **2026-10-09** (F-2654): J-1785: live check of J-1750 shore nest egg-count line PASSED - 38 post-reboot rows all say 'three eggs', 0 contradictions vs oyc_nest eggs=3.

- **2026-10-08** (F-2601): J-1992 built guard_runaway_thought (core/model_client.py) applied at idle-thought call site; cuts salvaged runaway at leaked JSON key; restart-gated; commit fb452b9 on worktree branch
- **2026-10-08** (F-2593): J-1944: the 1,828-char thought that hit hands_trace's 1,200 cap was a salvaged runaway JSON tail (400-token mid-train cap), not a raised budget; caps stay, D-0325 untouched; leak fix spawned as a build job.

- **2026-10-07** (F-2565): J-1791 read D-0325's widened hands_trace after 29.55 live hours on the wide code (3 runs 10-04..10-07, 1,561 new-code rows): every F-2415 prediction holds. At-cap share 1 of 1,561 thoughts (0.064 percent, under the 0.5 percent threshold) and 0 intentions; mean row 518.7 bytes (+13.8 percent vs predicted +15.5); worst calendar day 0.42 MB, the widening's own share +0.05 MB; D-0325's 2 MB/day defeater not tripped and no reader broke (replay --real-locations exit 0, its 17 recurring dedup keys are all old-era, hands.status() normal on a copy); 2 of 2 wide wood/study declined-MOVE rows are genuine. One premise correction: the single at-cap row is a real cut, its monologue twin is 1,828 chars, above the 1,121 all-history max the cap was sized against; follow-up spawned to find which path produced it. Core unchanged.
- **2026-10-04** (F-2415): J-1758 built D-0325: core/hands.py trace() thought/intention caps widened 200/120 to 1200/400, sized from data (p99.9 448, longest ever 1121, growth about +0.05 MB/day, the briefing's +0.2 was 4x high), reader audit clean, commit 5d1f36a restart-gated

- **2026-10-04** (F-2419): J-1755 restored bare candles and candle on the candles row as Action.bare_objects (the verb's direct object only, via literal_will._bare_object_hit); replay of 28,513 real thoughts x 4 locations changes only 5 thoughts; the 09-30 07:57 miss now fires candles with book STAGE-busy; matches stays dropped; the only take_book on record (09-30 07:57:41) is a candles-miss capture, not a deliberate will, so the J-1070/J-1683 D-0203 read must not count it; commit 502c736 restart-gated; the hedged I-could-fetch-a-candle shape is a judgement call for Travis
- **2026-10-04** (F-2417): J-1766 built D-0335 distinct-encounter graduation, N=30 min read at graduation decision, stored individuals never re-judged (a re-judging rule would hide oystercatcher, tui and korora), commit f162334 restart-gated, replay tui 09-27 14:04:03 korora 09-28 03:42:53 blackbird unchanged

- **2026-10-04** (F-2421): J-1774 D-0345 built restart-gated at 523698c: shore nest look live at next boot (nest line from oyc_nest, creature looks byte-identical), nest-object gate SHADOW-ONLY logging to data/nest_gate_shadow.jsonl (changes no answer; F-2382 draft reproduced 100/100, 0/110, 0/1526x4, 14/15)
- **2026-10-03** (F-2382): J-1699 sized F-2297 over the whole history (F-2382): 15 of 465 creature looks name the oystercatcher nest or eggs through the bird alias, all shore, all while the nest existed, 12 of them the bird-and-eggs conjunction; 43 more nest looks with no bird get a nest-blind generic shore description since the shore has no nest look; a conjunction-shaped nest gate is drafted and tested but not built, the nest-look call is open as D-0345, and the ambient two-eggs literal is queued as J-1750

- **2026-10-03** (F-2363): J-1725 refreshed the two stale pre-existing Living World regression checks from F-2351, and the j1165 and j1174 scripts both print ALL OK on a clean master worktree plus commit 7ab1e86: the look-history pin in j1165 is now a rule, every diverted pair is a trace-object look at a creature that left that trace and is answered from that trace, after Du look history grew a third pair, crab tracks at the shore, the same defect class the gate exists for and already routed to the trace live on 2026-09-24; the life_birds golden set in j1174 gains the two reviewed traces_only_at pairs from J-1281 and F-1805; neither failure was J-1698 related, both were identical on the base commit; test scripts only, no core change, nothing written under data
- **2026-10-03** (F-2351): J-1698 built the place-scoped recognition line (F-2351): a graduated individual recognition line, and the name Du gave, now renders only at the place it graduated at, so the blackbird first wood look no longer claims long acquaintance; render-only and restart-gated, commit 34b5156 on the job-run branch; note_sighting and the counting rule are untouched because D-0335 is open, so other-place sightings still bump the counter; the new 638-check test fails 89 on the base commit and passes, covering all 15 multi-place rows and an old-vs-new differential over 58 rows that differs only by 32 removed other-place lines

- **2026-10-03** (F-2326): J-1531 closed as superseded (F-2326): the wood or study homonym premise is refuted at HEAD 297e359 - the declined-move object label comes from literal_will classify and the move row of the actions table, not _move_dest(); 132 of 133 rows whose object word is missing from the stored text are 200-char truncation rows (complete-text rows 1 of 31 versus truncated 132 of 376, Fisher p 4.7e-05; the one exception a pre-J-0787 hyphen compound); real _move_dest() shows no homonym-caused wrong relocation in the corpus; no code change; D-0325 (widen the trace caps) stays with Travis
- **2026-10-03** (F-2308): J-1192 read 2026-10-03: gate met at 7.80 live-days on fbf6423; D-0166 clauses a, c, d not fired (0 of 156 live answers wrong, no group-grain row graduated, no plural-keeps); clause b night mix is oystercatcher 67 percent of 18 voices per hour, the same shape as the old 69 percent at 31 percent of the volume, left to the founder; 3 eligible rows graduated on raw looks so D-0335 is open on graduation grain; new cross-place recognition defect F-2305 filed as J-1698, nest looks as J-1699

- **2026-10-03** (F-2248): J-0658 read 2026-10-03: J-0573 carrier-path fix PASSED its first live test on oil only (first carrier box collected 2026-09-24 16:45 with no emptied or sync_reconciled row, delivered tin intact at 1.0 and study count equal to shelf across 138 live hours); the matches leg is untested because that box had spoiled in rain; J-1676 queued for the matches leg (not before 2026-10-09), J-1677 queued for the unopened care package (F-2249)
- **2026-10-02** (F-2227): J-1635 built and verified: gate/bed/mailbox DEST cues now tolerate an inserted modifier (F-2202's open-gate gap); desk/study checked and left un-widened on real evidence; a kelp-bed and a determiner-bridging false positive found via full-corpus replay were fixed in the same change (F-2227, verified, FAILS=0).

- **2026-09-28** (F-2202): J-1608: F-2170 no-candidate bucket (9 tokens, 128 rows) is 98.4 percent hands_trace 200-char logging truncation not a move_dest bug, F-2202; D-0325 reopened with this evidence; one real narrow move_dest cue-gap found, spawned as J-1635.
- **2026-09-28** (F-2173): J-1573: the J-1531/F-2136 wood-study fix was gated on a mismatched D-0323 citation (that ID is really an unrelated chapter_id_repair decision); re-read confirmed core/actions.py, core/literal_will.py and core/hands.py truncation are unchanged since F-2136; tested cross-referencing data/nascence.log on 2 of the 24 artifact rows -- the cycle-id join works but nascence.logs own lines are independently truncated too, so no clean recovery; no code change made; opened D-0325 fresh for the founder call on widening caps vs full reconstruction vs dropping the thread.

- **2026-09-28** (F-2170): D-0319 built (J-1591, F-2170): sensorium.standpoint_move() wired into dispatch._move()s already-there branch now resolves sea, tide, shingle, driftwood, surf and beach at shore, raised bed and gate at garden, and trees at wood to a real standpoint instead of silence; locomotion._SP_PLACE gained 9 standpoints the layouts already defined but goto() never recognized. Bare in/out/inside/outside and shores own trees stay correctly declined; no matching standpoint exists for them. Not yet live (no restart yet).
- **2026-09-28** (F-2092): J-1441 classified the 1019 declined-move backlog (F-2092): (a) already-there 25.6 percent; (b) within-place feature with no move target such as out, sea, tide, trees, shingle, gate, or raised bed, 55.8 percent, the dominant share, decide question D-0319 opened on building sub-place standpoints; (c) real cross-place miss 17.2 percent, explained by the already-ruled D-0224 first-leg journey-redirect protection in plan actions_expansion, not a new bug, J-1182 in progress is the rigorous defeater read; (d) weak or garbled intent 1.5 percent. A small object-extraction fix was spawned as J-1531.

### What we have
- The life engine is BUILT and LIVE end-to-end since the 2026-09-09 17:51 flip (D-0166/J-0641): engine
  shape, naming, harshness, night light, reach and scope all ruled 2026-09-02 (D-0128 through D-0133),
  L0-L4 built same day (J-0509 through J-0513), confirmed running on every restart since (F-1612, F-1243).
- A long defect-fix tail off real live evidence is mostly closed: wrong presence/absence claims (F-1617),
  gull-cries night monoculture (F-1614), plural/flock graduation bugs (F-1622/F-1679), place-agnostic
  trace phrases (F-1671, scoped by D-0249/D-0254), carcass-gate and reveal-join punctuation bugs
  (F-1669/F-1674), and the candles/matches CLAIMS-mechanism decoupling (D-0267/D-0271, J-1296/J-1310).

### What we need
- J-1192's formal 7-live-day defeater read on merge `fbf6423` is still short (1.05/7.00 days as of
  F-1795, 2026-09-23) — needs re-checking.
- J-0658's carrier-box live test has still not fired (no `box_collected` event in the logs as of F-1611).
- J-1441 (open, from F-1994/F-1998's 2026-09-27 action-inventory) needs classifying: 1,019 declined
  moves plus 773 unanswered deeds across the world.

### What we're doing next
Re-check J-1192/J-0658's gates once more live days accrue; work J-1441's classification pass next.

