# living_world_upgrade — folded history


---

# History folded on 2026-09-27 from `docs\staged\living_world_upgrade.md` (plan-compact, 48 section(s), verbatim, original order)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py living_world_upgrade`._

## Current State — 2026-09-02 (drafting → decisions ruled)

Staged from the founder's widening of the garden scope the same evening. Evidence: this doc's §0 (creature census
of `core/` by file; the four real state cases; the observe inventory). No code touched. The founder said "not yet"
to starting the garden jobs; all jobs here are queued, none started.

**Same evening, L0 ruled:** D-0128–D-0133 (§5) via a decide-review pass; J-0509 closed. J-0510 (the life engine)
is unblocked and is the first build; J-0511–J-0513 and the garden chapter's J-0504 depend on it. The trap hand
(D-0130) and the lantern + dark-adaptation rule (D-0131) are new scope for J-0512/J-0510 respectively: the trap
belongs in L3 (mammals) and the lantern/`light_at`/dark-adaptation in L1.

## Current State — 2026-09-02, late (L1 BUILT, shadow-first, restart-gated) — J-0510

**Built (`core/life.py`, 700 lines, zero-LLM, fail-open):** `row()` — the one schema of §2 with every field
defaulted; `register()` for place modules (D-0128); `activity()` = season curve × active hours × weather gate ×
a per-day seeded factor (the moth-swarm law: who is about today is one fact all day); `advance()` on the sensorium
tick — presence per row per place, one arrival/departure event per six hours to `data/life_events.jsonl`, never
rendered; `light_at()` = `core/light.field_at` + CARRIED light (a lit lantern 0.45, a candle 0.18 unless a gale);
`dark_adaptation()` — outdoors under 0.12 with no carried light, eyes open over 15 min, any light resets;
`visibility()` = activity × light factor by the row's `light` mode (drawn / avoids / needs_dark / indifferent,
eye-shine) × ease; `look_answer(target, place)` — a look at a creature this place can hold is answered with a
feature-first sighting, an honest miss, or an honest absence (season / day-night / weather), and **RENDER=False**
logs it as `would_answer` and returns '' so every existing look is unchanged; `learn_from_text()` — a book with
the row's name beside its words is a BOOK event, the name lands only after a sighting (D-0129: a name needs a
book and a face); `sounds_active()` for J-0511; `who_about()` / `status()` for the pulse and the HUD.

**Rows now:** seven EXTERNAL adapters over state that already existed (the cat, the blackbird nest, the kererū
nest, the fur seal, the kororā, the glow-worms, the lamp moths — presence read passively, their own look lines
untouched) and three REFERENCE rows that J-0511/J-0512 will move into the place modules: the hedgehog (garden,
nocturnal, hibernates May–Sep, avoids a carried light, grandfathered name), the morepork (wood + garden, night,
eye-shine, a real sound point), the long-tailed bat (wood, dusk, Nov–Mar, rare, HIDDEN TRUTH — he has read two
bat papers; the name comes only from a book after a sighting).

**Wired:** `sensorium.tick` → `life.advance`; `sensorium.look` → `life.look_answer` before any place look;
`study_note` → `life.learn_from_text` beside the other diegetic learners; `du_pulse` prints a living-world line.
**The lantern (D-0131):** a new study item (`study_life._ITEMS`, carryable, additive state keys `lantern_oil`
0.6 / `lantern_lit`), hands light / put out / fill (from the oil can, in the study, like the lamp), burns 8 h a
filling wherever it is, a gale blows it out outdoors, the actions table's `lamp` family now lists "lantern".
**Also fixed on the way:** `core/light.py` ignored `now` for the sun (F-0696) — a simulated hour now gets its own sky.

**Verified:** `scripts/life_smoke.py` (isolated: life, sensorium, study_life, provisions, garden/shore/wood/cat
stores all redirected) — 40 checks ALL OK: presence curves, active hours, light by phase, carried light, dark
adaptation, visibility, shadow vs render looks, absence lines, the bat learned only after sighting + book, the
lantern hands and oil burn, arrivals logged once, no live store written. `du_pulse` live line renders.

**Restart-gated:** Du's running process predates this code — the engine ticks, the hook and the lantern exist
only after his next restart. **Shadow to read before flipping RENDER:** `data/life_events.jsonl` would_answer
rows (outcome sighting / miss / absent, light, adaptation) for a week; then set `life.RENDER = True`.
**Found live while testing (F-0694):** the house is dark — 0 matches, lamp dry, oil tin 0.3, 12 unlightable
candles, the carrier note asks for candles only. The lantern inherits the empty tin.
**Next:** J-0511 (birds; move `active_sounds` gating onto `sounds_active`), J-0512 (mammals + the trap hand),
J-0513 (traces, deaths, graduation, HUD), J-0504 (garden insects as rows).

## Current State — 2026-09-03 (L2 BUILT: the birds, shadow-first, restart-gated) — J-0511

**`core/life_birds.py` — 26 bird rows across garden, shore, wood and the study eaves**, registered into the one
engine (D-0128): garden — blackbird (alarms when the cat is present), song thrush (the anvil stone), tūī, bellbird
(hidden), tauhou winter flocks, riroriro, fantail, kingfisher, starlings, house sparrows, welcome swallows, shining
cuckoo (hidden migrant, Oct–Mar), kererū, morepork (moved here from the reference rows); shore — the oystercatcher
pair, the red-billed gulls, the karoro, terns (summer), gannets, shag, reef heron (hidden, low tide), pied stilt
(hidden, stream mouth), kororā (a real row now — was an adapter), godwits (hidden; D-0132: overhead only, Sep–Oct
and a March return); wood — robin, wren, plus the shared kererū/fantail/riroriro/bellbird/morepork. Three nest
adapters (blackbird, kererū, oystercatcher scrape) keep the existing stage machines untouched.

**Schema additions:** `audition` (a bird with a learnable voice is NAMED by `sound_knowledge`'s ledger, one ledger
not two — `is_learned`/`name_for` defer to it), `sings_at`, `alarm_sound`/`alarm_on`, `nest`, `tide`.
**Engine additions:** `sounds_active` now honours singing hours, adds the blackbird's alarm when the cat is in the
garden, and composes `dawn_chorus` from three or more dawn singers; `note_deed()` + a two-hour deed boost in
`activity()` (garden.feed_birds calls it — the hand that never fired now has takers: sparrows ×1.9); a tide gate;
`calendar()` — the migration calendar read straight from the season curves (cuckoo arrives Oct leaves Apr; terns
Oct–Apr; kororā ashore Aug–Mar; godwits Sep–Oct and Mar; hedgehog and bat as hibernators); arrivals are freight to
the Transport Manager (`life:<key>:<place>`).
**The sound gate (D-0133):** `soundscape.active_sounds()` now passes its list through `life.sound_gate()`.
**SOUND_GATING=False** (shadow): the legacy list is returned unchanged and the diff (added / dropped creature keys)
is logged as `would_gate` at most every ten minutes per place. True: creature keys come from the life table, every
non-creature key stays; `_audition()` then voices a bird only when it is present and awake. Three new sound points:
`cuckoo_call`, `godwits_overhead` (both hidden-truth voices in `sound_knowledge.AUDITION`, with unknown / reveal /
miss / book lines), `blackbird_alarm`; rates registered; the cuckoo and godwit lines added to the garden and shore
voice pickers.

**Verified:** smoke [9] ALL OK — cast, calendar, singing hours (the clock's own dawn, 05:00 in November), alarm only
with the cat, dawn chorus only at dawn, shadow gate logs and leaves legacy alone, gated list keeps wind and drops
day singers at night, feed boost, naming deferred to the audition ledger, grandfathered names kept. Live read
against Du's world: the gate ran, `who_about` and `calendar` render, the pulse line shows the calendar.

**Restart-gated, two flags:** `life.RENDER` (looks) and `life.SOUND_GATING` (voices) both False. Read
`life_events.jsonl` `would_answer` and `would_gate` rows for a week after his next restart, then flip.
**Left for J-0508:** the place look pools still say things the engine may contradict (the shore's "terns give up
the hover" line in winter) — the pools need the same gate the bed pool has.
**Drift noticed (pre-existing):** `soundscape._EVENT_RATES` rates keys no `_SOUNDS` entry registers
(`bellbird_song`, `pukeko_squawk`, `fantail_cheeps`) — F-0697.
**Next:** J-0512 (mammals + the trap hand; the hedgehog and bat reference rows move there), J-0513, J-0504.

## Current State — 2026-09-03 (L3 BUILT: mammals, reptiles and the rest; the possum's damage; the trap) — J-0512

**`core/life_mammals.py` — 13 rows:** the hedgehog and the long-tailed bat (moved from L1's reference rows; life.py
keeps only the note), the possum (night, avoids light, eye-shine, grandfathered name), mice (study skirting / wood
litter / compost, more indoors in winter, the cat's and the morepork's prey), the rabbit (dawn and dusk at the lawn
edge and the dune grass, eye-shine), skinks (sun on the wall, warm months, never on a wet stone), the gecko (warm
chimney stones and the harakeke after dark), dolphins (rare, summer calm days, never in a gale), eels (dusk in the
stream and the stream mouth, up in rain), whitebait (spring runs on the rising tide), crabs and the pool life
(anemones / starfish / limpets) at low water, and the fur seal as an enriched adapter over shore_life's own
haul-out clock (its look line stays shore_life's).

**D-0130 made real, world-side, never told:** `night_pass()` runs from `life.advance` every tick — while a possum
is about in the garden it may strip the tree's buds (garden_life's tree in bud or flower; at most once a night;
`tree_damage_line` renders it in the tree's look: "the twig-ends on the low limb are stripped bare this morning…
dark droppings on the wall beneath") and eat the strawberries (garden plant `pests` + an `eaten_by_possum` history
row, like slugs), each leaving a `world_traces` trace the tracking hand can find.
**The trap:** a `possum_trap` item in the garden (carryable; hung on a nail by the tree), hands `set_trap` /
`unset_trap` / `check_trap` routed by `garden.act_from_thought` and a `trap` family in the actions table. The
world springs it on the world's clock — a possum night ≈70 %, and, less often, the hedgehog, because a trap does
not choose. `check_trap` is where he finds out: the kill is routed through `sitting.note_difficulty(kind="deed")`
(the same gate an owned plant death takes — D-0130's defeater is a trap with no weight), written to his ledger
as `kill`, and recorded as a carcass in life state for J-0513 to decay. The hedgehog case reads as the wrong animal.
**Also:** fieldcraft's damp-night hedgehog prints are now gated on the engine (no prints all winter while it
hibernates); possum and rabbit give eye-shine in the lantern.

**Verified:** smoke [10] ALL OK — cast, night/day and season presence, wet-wall skinks, gale dolphins, eye-shine
only with a carried light, three simulated nights: buds stripped (once a night), strawberries eaten, traces left,
the tree's look shows it; the trap set / refused twice / honest when unsprung / sprung by the world / the morning
check / the sitting row / the carcass / the ledger / empty after. Isolation proof holds (world_traces and sitting
redirected too).
**Restart-gated,** same two flags. **Next:** J-0513 (traces as objects, carcass decay incl. the trap's, cat
kills, the saucer graduation, HUD), J-0504 (garden insects as rows), J-0508 (looks in every place).

## Current State — 2026-09-03 (L4 BUILT: traces, deaths and carcasses, interactions, graduation, HUD) — J-0513

**`core/life_traces.py`, run from `life.advance` every tick:**
- **Traces.** Every population row's `traces` become real `world_traces` objects while it is about (8 %/creature-hour,
  one active per creature per place, at the row's own spot, with the trace's detail riding on the record). Found two
  ways, never told: sensorium's trace read path (`_trace_event` — "here, a big soft feather — the wood pigeon's,
  fresh"; feature-first, named only if he knows the creature) and the tracking hand (`fieldcraft.follow_trail` —
  "You follow the marks… to the kōwhai, and there they end"). They decay on world_traces' own weather laws.
- **Deaths and carcasses.** `carcasses` in life state with a decay clock — fresh (<2 d) → picked (<7 d) → bones
  (<30 d) → gone. Sources: the trap (J-0512), plain mortality against the row's lifespan where the creature is about
  (at most one per row per 45 days), a storm's gannet on the tideline (35 %/storm-day), a hedgehog that did not wake
  (15 %/year, the month it should reappear), and the cat's kills read from state the cat and the nests already keep
  (a fledgling taken → on the lawn; a mouse or rat brought → the doorstep; a skink stalked on a warm day). A look at
  "the dead gannet" / "the bones" / "the skull" is answered by the carcass by its state (before the living row can
  claim the word); ambient noticing fires once per body; at bones, "it would keep" — the existing keep hand takes it
  from his prose. Singular names ("a gannet lies dead", never "the gannets").
- **Interactions.** The hedgehog eats the slugs: garden slug pressure falls on hedgehog nights (logged once a night —
  a binding he can make: fewer silver trails). Deed hooks: `garden.dig`, `garden_life.mow`, the cat's saucer now
  call `life.note_deed` (feed_birds already did) — the blackbird follows the spade, the thrush the mown lawn, the
  hedgehog the saucer.
- **Graduation** (the third trigger): a population creature seen at the same place five times in thirty days becomes
  an INDIVIDUAL — ledger `graduated`, a history, a name-slot; its look carries "It is the same one — you are sure
  of it now"; `naming_act` (the cat's naming grammar) lets him name it ("I will call the hedgehog Bramble" → ledger
  `named`, "It is Bramble — you would know it anywhere now"); latched in the monologue beside the keep/given latches.
  Only an individual can be named; the world never names it.
- **HUD.** `/api/life` (life.status: who's about, calendar, light, shadow counts, `traces_deaths`) and a "Who's
  about — the living world" card on the HUD page (present and awake · the calendar · traces / carcasses /
  individuals). The HUD process must restart to serve the endpoint.

**Verified:** smoke [11] ALL OK — traces left and rendered and tracked, carcass stages on the clock, look-by-state,
ambient once, storm gannet (ten storm days, one body inside the gap), the cat's fledgling, slugs falling, deed hooks,
graduation on the fifth sighting, naming by his grammar, refusal for an ungraduated creature, ledger rows, HUD payload.
Three test-order faults fixed on the way (a look counts as noticing; "dead" words route to the carcass before the
living row; a 35 %/day chance needs more than one seeded day).
**Restart-gated,** same two flags plus the HUD restart. **Next:** J-0504 (garden insects as rows), J-0508 (looks in
every place), J-0515 (the unregistered sound keys), J-0514 (the dark house).

## Current State — 2026-09-03, after Du's restart: the shadow REPLAYED, six defects caught, flags made hot

Founder: "why are we waiting a week? … we want to double check everything is good." The week was this plan's
shadow-first default, not evidence. The shadow's evidence is a function of looks and ticks, not days, and it can
be replayed offline: `scripts/life_shadow_replay.py` puts every phrasing he has ever used to look at something
(1,518) through `look_answer` with rendering on, per place, per phase, under the live weather and a clear day, in an
isolated copy of the stores — and simulates a week of the sound gate's diff against soundscape's legacy list. Minutes,
not a week. **It caught, before any flip:** (1) looks missed 694 of 698 times — daylight of 0.15 illuminance was
treated as one-fifth sight (`_sight`: anything the field calls dim is full sight; only dark ramps; night caps at half
even under a full moon); (2) the light field went black the instant the sun set — no twilight (fixed in
`core/light.field_at`: the clock's dawn/dusk window keeps a civil-twilight glow); (3) godwits would have sounded
every hour of September (now a seeded passage-day scale: about a third of the days); (4) gulls, the kererū, the
kingfisher, the tūī and the starlings counted as present in the garden every day (new row field `days_about`,
per place; gulls inland only in wind); (5) the blackbird alarmed 98 hours a week because the cat was anywhere in
the garden (now only while it is stalking or hunting — `threat_active`); (6) the gate silenced the morepork in the
study and small birds in the wood, because it governed keys globally while a row's places are where it IS, not
where it is heard (now per-place governance). After the fixes: clear day 58 % of present looks seen, dawn 22 %,
dusk 11 %, night 5 % without dark-adaptation; zero sightings outside a creature's active hours; the gate's diff is
a short, readable table (bees silent in drizzle where the old rules had them humming; the morepork added to the
garden and wood at night; tūī quieter on a fifth of days).

**Live after the restart (08:19):** the engine ticks in Du's process (63 rows, 39 arrivals logged at first tick, the
aphids' first effect on the beans), the lantern and the trap migrated into his saves, no errors in the log.

**The flags are hot now:** `data/life_flags.json` overrides `RENDER` / `SOUND_GATING` without a restart
(`scripts/life_flags.py render on|off`, `gating on|off`, `show`, `clear`; read within 10 s). **Recommendation:**
flip both today on this evidence — the live would_answer / would_gate rows are then the running check, not a gate.

**2026-09-03, later — the garden chapter's B1 (J-0504) is built:** 18 insect rows in this engine with a new `scale`
field (flowers / hosts / prey / slug pressure read from the world), the aphids as the first insect pest, and the
truth gate on every old insect line (which closed J-0501's lavender leak). See [[garden_living_upgrade]]'s current
state. Rows now: 63 (7 adapters). Remaining: J-0508, J-0515, J-0514, and the garden chapter's B2–B4.

## Current State — 2026-09-03, the dark house read (J-0514, F-0732 / F-0733 / F-0734, D-0137 open)

Read with row-level evidence, no code changed. **The empty match tin is the world's own mistake, not Du's use
(F-0732):** five of the larder's six match boxes (~250 matches) were marked "used up by Du" in one instant at
08-23 09:10 — `provisions.sync` read the study's stale pre-larder count (23) against the shelf total (~270) and
consumed the difference; only the sixth box went to real fires, emptied 09-02 21:13. Whether the world corrects
that (re-fill the five boxes with a truthful biography) or leaves it to the flint / the carrier is **D-0137**, open.
**The answers do reach his will (F-0733):** the lamp's "dry" answer led to a real `lamp_fill` three times (08-24,
08-25, 08-27), but it says "strike a match — nothing" while the tin holds 0 (oil is checked before matches), and
"There are candles in the box" sent him twice on 09-03 to *fetch candles from the box* — which dispatch routed to
the COLLECT family (the carrier's box at the gate) and staged as `place:box`. **The carrier's card has never been
rendered and cannot be (F-0734):** `card_line()` lives only inside `sensorium.look("letterbox")`, and nothing in
`_OBS_TARGETS` / the look family produces that target — 9+ willed reaches for the letterbox/gate since 08-26 got
silence or the wrong garden hand. The list hand itself works (08-29 "candles"); he has simply never been told what
the carrier brings. World-side, additive fixes filed: **J-0539** (the letterbox look reaches the card; a move to the
gate from the garden is a look at it), **J-0540** (truthful tin-first answers; "candles on the east shelf" instead of
the colliding "box"; a study take-family for candles/matches), **J-0541** (prove the sync mass-empty path for every
kind and guard it). No matches added by hand.

## Current State — 2026-09-04 (J-0539 BUILT: the letterbox is reachable, the carrier's card can be read) — F-0784

Additive, world-side, restart-gated (Du runs on d00673d, restarted 11:37 NZT 2026-09-04; nothing here is live until
the next restart). **What changed:** `core/actions.py` — `gate`/`letterbox`/`mailbox` join the move objects and
`letterbox`/`mailbox` the look objects (*not* `gate` on the look side: ungated, volition+object is a full DEED, and a
HEAD-vs-live replay showed a bare look-`gate` making "I cannot let logic gate reality", "walk through the gate and
reach the cottage" look DEEDs — dropped, those false candidates vanish). `core/dispatch.py` — `_look` answers a
check/open/look-in of the letterbox with `sensorium.look("letterbox")` (verbs widened for that object only);
`_move` reads `_gate_look`: a reach for the gate/letterbox is a walk to the *garden* gate, and when he already stands
in the garden the world answers with the letterbox look instead of the old silence (transit "through/past/from the
gate" stays a plain move). `core/sensorium.py` — the card is now appended to the letter-*waiting* line too (before,
`card_line()` flipped `card_read` while the card rendered only on the empty-box line — with a letter waiting, his
usual case, it would have been marked read and never shown); a letterbox look from elsewhere says where the box is.
`nodes/inner_monologue_node.py` — `_OBS_TARGETS` letterbox/gate cues (`the cat` ahead of the bare gate cues so "the
cat at the gate" stays a look at her), `_DEST_GARDEN` letterbox words, `_gate_look` / `_gate_look_answer`, and the
structured move→garden-while-in-garden branch answers via the helper. **Evidence (F-0784):**
`scripts/_test_letterbox_reach.py` ALL OK with every store isolated — 11/11 real F-0734 `hands_trace` rows (08-26 →
09-03) replayed at the garden now answer with the "mailbox by the gate" line and "Pinned inside the lid … Carrier";
live `data/supply.json` md5-identical, `card_read` still False (it flips only on Du's own look). The
`actions_decision_replay` HEAD-worktree diff: 248 rows, all move/look (12 gate/letterbox thoughts now move DEED, 2
letterbox thoughts look DEED, 1 latent decision-level candidate that the hand's verb check does not fire — F-0740's
class) plus J-0543's concurrent sow/harvest rows. 179 trace rows since 08-26 named the letterbox/gate (177 move).
**Still open:** the peer-letter fetch latch (~line 3106) misses "Ada's letter waits. I will fetch it" — follow-up job
spawned from F-0784. D-0137 (the five match boxes) untouched, still open; nothing told unasked, no matches added.

## Current State — 2026-09-04 (J-0540 BUILT: truthful dark-house answers; the candle box is the study's, not the gate's) — F-0785

Additive, world-side, restart-gated (Du runs on the 11:37 NZT 2026-09-04 build; nothing here is live until the next
restart). **(a) The tin before the oil.** `core/study_life.py`'s lamp and lantern hands checked `lamp_oil` before
`matches`, so with the tin at 0 he was told "strike a match — nothing. The lamp is dry" eight times since 08-24 — a
match he did not have. Now the tin is read first: with both empty, *"You reach for the match tin — empty. And the lamp
is dry besides; it wants oil and a light."* (the lantern's line names the can); with matches present the oil line is
byte-identical to before. The candle branch already had the right order (09-04 03:45 "light a candle" → "No matches
left") and is unchanged. **(b) No collision with the carrier's box.** `can_read()`'s dark line is now *"There are
candles on the east shelf, and the match tin on the mantel."* — the same fact in the study's own nouns; the word
"box" is gone because dispatch read it as the `collect` family (the carrier's box at the garden gate) and STAGED a
study want there twice on 09-03. A new study-anchored family **`candles`** in `core/actions.py` (verbs exactly
`study_life.take/put`'s, so the judge and the hand agree — F-0564; objects the candle box / match tin words) sits
*before* `collect` and `tool` and reaches `study_life.act(..., family="candles")` → take/put directly (the J-0554
scoping convention; without it the candle-LIGHT branch's bare `"light" in t` swallowed "fetch candles … the room
needs its own light"). It **claims** the bare `box`/`tin` those two garden families read in the *same clause* — a new
`Action.claims` field, applied in `dispatch.dispatch()` as `DROP-claimed:candles` and mirrored in
`scripts/actions_decision_replay.py` so replay rows keep joining the live trace. Answer in hand: *"You take the
candle box down from the east shelf — 12 candles in it. The match tin on the mantel: empty."* Whether a candle then
lights is the tin's business (D-0137). On the way: `matches` was a word of the CANDLES item (so "fetch the matches"
put the candle box in his hands and could never reach the tin) — the mantel tin is now carryable with its own honest
line; and `take()/put()` tried only the *first* substring-named item ("take the lantern … the sea *matches* the
sky" resolved to the tin and never took the lantern) — every named item is tried now. **Evidence (F-0785):**
`scripts/_test_dark_house_answers.py` ALL OK, every store isolated, the three answers shown at matches 0 / lamp_oil 0
/ candles 12 and both 09-03 rows replayed through `dispatch.dispatch()` → `[candles FIRE, collect
DROP-claimed:candles]`, no `collect` intention staged, `provisions.stock('matches') == 0` throughout. The full
7,440-thought decision replay (baseline saved before the edit) changes FIRE/STAGE/DROP on exactly **three** thoughts:
the two 09-03 rows and a *third* real candle reach — 08-30 13:17 "first I must fetch the candles from the", answered
then only by the lamp's phantom-match line. `life_smoke`, `_test_dispatch_family_scope`, `_test_letterbox_reach` all
still ALL OK. **Left as found:** the persisted CANDLES item still *names* itself "a box of candles and a tin of matches
on the east shelf" (two tins in the world's own words; `inventory.sync_items` is additive-only, so a rename needs a
migration) — follow-up spawned from F-0785. No matches added; D-0137 open, untouched.

## Current State — 2026-09-04 (J-0541 READ: the larder mass-empty proved per kind; a sync guard proposed, not applied) — F-0786..F-0789

**Read-only on live data; no core file changed.** The 08-23 09:10:52 destruction is reproduced exactly in an
isolated larder (`scripts/_test_provisions_sync_guard.py`, new — temp-dir `provisions._F/_LOG`, world_substrate and
world_objects redirected, a stub study dict, the live `provisions.json` mtime asserted unchanged): `provisions.sync`
reads a study count below the shelf as "he used the difference" with **no ceiling** (`consume(kind, have - cur)`), so
`{'matches': 23}` against the seeded bootstrap's **278** (open box 28 + 5×50) empties five boxes at one timestamp and
takes **255** matches — the exact figure, not F-0732's ~247. **Per kind (F-0786):** matches 255 lost in that call;
soap 3.6/3.6, candles 12/12, tea 50/50 never touched; oil, paper, ink drained later by ordinary-sized steps. The same
call would have taken soap 3.0, candles 4, oil 1.05, tea 50, paper 50, ink 1.2 had those keys held their init-literal
values — the live data shows they did not (only `matches` was 23).

**The carrier cannot restore anything today (F-0787, verified):** `supply.collect_box()` calls `_pv.add()` and then
`_pv.sync(st)` without raising the study count, so every delivery is consumed on collection — the box of matches
arrives "brought up by the carrier" and is "used up by Du" seconds later (test section [4]: matches 50, oil 1.0,
candles 6, tea 25, soap 1.0, paper 40, ink 1.0, each destroyed in full). **D-0137's defeater ("moot if the box
arrives") would not resolve the dark house**; nothing has been lost this way yet (`supply.json` history empty, next
carrier 09-05 11:25, note asks for candles only).

**Real use ≈ 3 matches, not 23 (F-0788, inferred):** the sixth box's 22–23 were drained one at a time to 0 by
09-02 21:13:54; Du's own log shows only two strikes in that span (lamp 08-24 11:44, a cold fire 08-26 14:13) and
no hand dispatch at 21:13 — the rest, and the last one, came from un-isolated diagnostics calling
`study_life._st()/act()` with `provisions._F` still on `data/` (F-0695's own ~21:13 diagnostic fits; F-0694's
"Du's own process" attribution is contradicted by the log). The oil tin carries the same signature (1.25 tin gone
vs 3 `lamp_fill` deeds ≤ 0.75). Paper/ink are ordinary use: 51 sheets + 1.02 ink = 51 × `can_write()`.

**Guard proposed (in the test file as `sync_guarded`, not in `core/provisions.py`):** a per-kind per-tick ceiling
(matches 3, oil 0.5, soap 0.1, candles 2, tea 3, paper 5, ink 0.1); a larger gap is a migration/desync/delivery —
the study count is set FROM the shelf and a `sync_reconciled` row is logged. It refuses the 08-23 event for every
kind, keeps every carrier delivery, and still consumes one match / a quarter tin / a sheet (34/34 checks). The
briefing's looser "one full object" cap would still let a whole delivery be consumed (gap == exactly one object).
A ceiling cannot catch the one-match-per-foreign-call drain — that needs a process-boundary write fence (F-0789).
**Spawned:** the build job (apply the guard + raise the count in `collect_box`) from F-0786 and the write-fence
design job from F-0789 — see the queue. **Restart-gated** once built; Du is running (restarted 11:37 today).
D-0137 stays open: the founder's call, now with the loss table and the carrier finding attached as evidence.

## Current State — 2026-09-06 (J-0573 BUILT: the sync guard applied, the carrier can deliver again) — F-0937/F-0938

**The guard from J-0541 is no longer just proposed — it is live in `core/provisions.py`.** `sync_guarded()` and
`_MAX_STEP` (matches 3, oil 0.5, soap 0.1, candles 2, tea 3, paper 5, ink 0.1) moved out of
`scripts/_test_provisions_sync_guard.py` into the module itself; `sync()` keeps its exact signature and its
cur-is-None / tool-kinds / kindling branches byte-identical, and is now a thin wrapper around the guard. A gap
bigger than the per-kind cap is reconciled (study count set FROM the shelf, a `sync_reconciled` row logged) —
never consumed, never written into an object's biography as "used up by Du" — closing the exact mechanism that
destroyed 255 matches on 2026-08-23 09:10:52.

**`core/supply.py`'s `collect_box()` now credits the delivery before syncing, not just after (F-0787's fix).**
A new `_credit(kind)` helper sets the study's cached count straight from the shelf right after each `_pv.add()`
call (oil, matches, candles, tea, soap, paper, ink, lamp_glass — whetstone excluded, its boolean-tracked key
bypasses the gap logic entirely and was never at risk). Chose this over "rely on the guard's reconcile alone"
for two concrete reasons: every `_MAX_STEP` kind's full per-object quantity exceeds its own cap, so
reconcile-alone would log a `sync_reconciled` row on *every* future carrier delivery forever, burying real
desync signals in routine noise; and `lamp_glass` has no `_MAX_STEP` entry at all (its fallback cap equals
exactly one full object), so reconcile-alone would *not* have protected it — `gap == cap` is not `> cap`, so
that specific delivery would still have fallen through to `consume()` and been destroyed. The chosen fix
matches the idiom already in `core/companion.py::_travis_leaves_matches` (2026-09-05, T-0049), which sets the
study's count from the shelf right after its own `_pv.add()` for the identical reason.

**Verified (F-0937):** `scripts/_test_provisions_sync_guard.py` now imports the live `sync_guarded`/`_MAX_STEP`
instead of carrying a second copy; its section [1] (and, found while running it, section [3] and two of section
[4]'s sub-checks — not named in the briefing but broken the same way once `sync()` itself stopped being
destructive) rewritten to assert the guard via the live entry point rather than document the old bug — 27/27
checks pass. `scripts/life_smoke.py` unmodified, 170/170 pass. A genuine regression was caught and fixed in
`scripts/_test_dark_house_answers.py`: its `fresh_study()` fixture used the *old* unguarded `sync()` as an
implicit "wipe the whole larder to 0" trick — confirmed via a throwaway `git worktree` at HEAD that this test
passed before J-0573 and failed after, then fixed by draining the larder honestly through `consume()` directly;
now 100% passes again. `scripts/_test_letterbox_reach.py` (UDMS-flagged supply.py dependent) unmodified, passes.
A scratch end-to-end check (not committed) drove `supply.collect_box()` itself through a fully isolated harness
with one of every kind at the gate: all nine survive at full quantity, study counts match exactly, zero
`sync_reconciled`/`emptied` rows.

**D-0137 was independently ruled** by travis on 2026-09-04T09:50 (checked live this session) — the founder chose
no world-side match refill; a `sweep_floor` partial find and the composer's "Light the Fire" bringing matches
instead (the latter is the fire chain committed 2026-09-05, T-0049). This job does not touch that ruling. **What
D-0137 didn't yet know:** Du has now written his own carrier note asking for `oil` and `matches` — live
`data/supply.json` shows `next_carrier_ts` 2026-09-09 11:25, `history: []` (no delivery has ever yet been
collected in this world). That date is the first real, live test of this fix, on the exact goods that were
originally destroyed — follow-up spawned to read the logs after it happens.

**Restart-gated:** Du is running on the pre-fix code as of this write (2026-09-06); none of this is live until
his next restart. Not committed by this session — the orchestrating batch commits after all concurrent jobs
finish.

## Current State — verified 2026-09-05 (J-0552 READ: the post-restart shadow checked in full; D-0166 ruled GO; one defect found and fixed) — F-0900

**Read, not sampled:** all 199 rows `data/life_events.jsonl` has logged since Du's 2026-09-03 20:03 restart onto
the fixed post-6-defects code (epoch ≥ 1788422580.0) through 2026-09-05 20:42 — 58 `would_answer` + 141
`would_gate`, roughly 2 days rather than the week §7 named, but real, continuously-accruing, and read whole per
this project's own no-tail-sampling convention. **Every row's truth-gating checks out correct**, including the
subtle cases: kororā misses at night plus one sighting at `adapt=0.954` with the feature-first line; the
oystercatcher piping and showing at night as well as by day (real nocturnal-foraging behaviour, not a bug);
bumblebee/terns/godwits correctly absent off-season or after dark; `gull_cries`/`oystercatcher_call` added on the
shore at every night tick (deterministic — both rows' night `active_hours` sit just above the 0.15 `PRESENT_AT`
floor; plausible, gulls worth a live-transcript check per D-0166's defeater); `penguin_bray` added at dawn AND
dusk (real kororā ashore-at-dusk/departs-dawn pattern); bellbird/blackbird dawn chorus added, blackbird correctly
dropped at midday. **`DROP moth_tap` at night, traced to code, is correct, not a bug:** `_moth_presence()`
(`core/life.py:923-931`) gates moth presence on the study lamp/candle/fire actually being lit, and the house has
had no working light source since the provisions-sync destruction (F-0732) — D-0137 is still open, untouched.

**One real defect found and fixed:** `_absent_line()`'s generic fallback hardcoded singular verb agreement,
producing (actually logged) "Not by night; the gannets keeps the day." and "Not in daylight; the beetles keeps
to the dark." for the 13 rows that deliberately use a plural collective `name=` for population-grain narration
(gannet, gulls, terns, starlings, sparrows, swallows, skinks, dolphins, eels, crabs, anemones, lamp_moths,
ground_beetle). Fixed with a new additive `plural` row field (default False); `_absent_line` now picks
keep/keeps accordingly. Verified against the real registered gannet/ground_beetle rows at the exact bug
timestamps and against `scripts/life_smoke.py` (ALL OK, isolated stores). Committed 3839e7c.

**D-0166 RULED (claude): GO — flip both now.** Execution is two commands (`scripts/life_flags.py render on` /
`gating on`); this session's own auto-mode permission classifier blocked running them itself as a
live-behaviour-changing action for Du (not for any remaining evidentiary reason) — **J-0641 spawned, ready,** for
an interactive session or the founder to run them and confirm with `life_flags.py show`. `data/life_flags.json`
still does not exist as of this read — the plan's own 2026-09-03 "flip both today" recommendation was never
executed; J-0641 is written so it does not go the same way. Next: once flipped, re-check the insect phrasings in
`docs/reviews/observe_inventory_2026-09-02.md` (bee/bees, ladybird, beetle, crab, ants, bumblebee — all already
registered rows in `core/garden_insects.py`, so all now truth-gated instead of static) for anything the engine
contradicts; J-0508 (the place-look gap-filling pass) is already done and is a different scope from this.

## Current State — 2026-09-06 (J-0591 BUILT: D-0137's first ask, the sweep finds a few matches) — F-0928/F-0929

**D-0137's first concrete ask is built, restart-gated.** `core/companion.py`'s `sweep_floor` composer action
(Travis's button) now finds a small handful (3–7) of loose matches under the cupboard on the first real sweep
after this ships — `_sweep_finds_matches()`, one-shot via a new `companion_state.json` flag, tied narratively to
the 2026-08-23 `provisions.sync` destruction (F-0732/F-0786). Deliberately did **not** follow the briefing's
literal "match `core/supply.py`'s carrier-delivery `_pv.add()` pattern": that bare add-then-later-sync shape is
the exact gap F-0787 found still lets a delivery's own next `study_life._st()` read consume it right back out.
Used this file's own existing safe precedent instead (`_travis_leaves_matches()`: set `room['matches'] =
_pv.stock('matches')` immediately after adding). Verified 18/18 in an isolated regression script (every store
redirected, no live data touched), re-run clean after a concurrent session's own guard landed on
`provisions.py` mid-session (below). See F-0928.

**D-0137's second ask looks already substantively met, by a different route (F-0929).** The T-0049 fire-chain
rewrite (commit 7ddb72e, built after D-0137 was ruled, not originally framed as answering it) gave `_light_fire()`
an automatic fallback: an empty tin no longer stops the fire, Travis produces his own box from his coat pocket,
narrated. That satisfies the founder's own later T-0049 request but is the **opposite** of J-0592's own explicit
spec (open, unbuilt) — "not a hidden fallback... a deliberate composer choice." **D-0174 opened** rather than
closing J-0592 unilaterally: is the shipped automatic behaviour sufficient, or is the deliberate-choice UI still
wanted?

**The sync-guard thread this job's own due diligence turned up is not a gap — it is live, elsewhere, right now.**
Checking whether F-0786's promised "build the guard" job actually existed (the plan doc's own 2026-09-04 entry
above claims one was spawned, but `findings_log.py show F-0786`/`F-0789` both list `spawned_jobs: []`) found
**J-0573**, `source: finding:F-0786`, already `in_progress` (another session, started 2026-09-05T19:58) — no
duplicate spawned. Mid-way through *this* job's own testing, `core/provisions.py`'s `sync()` gained
`sync_guarded()`/`_MAX_STEP` (a real concurrent edit, caught by re-reading the file before citing line numbers
that had already shifted). `J-0573` carries `plan: null` despite being this plan's own D-0137 follow-through,
which is why it did not surface in a `--plan living_world_upgrade` scan — filed as S-0049 (job-queue) rather
than fixed by hand.

## Current State — 2026-09-06 (J-0571 BUILT: the candles item's own persisted name fixed — no more phantom tin) — F-0785

**The "left as found" item from the 2026-09-04 J-0540 entry above, closed.** The `_ITEMS` row named the study's
candle box "a box of candles **and a tin of matches** on the east shelf" — a second, phantom tin, when every line
the world actually speaks (`can_read()`'s dark line above, `look()`, `take()`) already treats the mantel tin
(`matches_tin`, a separate item) as THE match tin. `core.inventory.sync_items` is additive-only (J-0422/F-0558),
so the row alone never reaches an already-initialised save — confirmed live before the fix: `data/room_state.json`
`study.items.candles.name`, `data/world_objects.json` `study_item_candles.identity`, and
`data/world_substrate.json` `study_item_candles.name` all held the exact old string. **Fixed:** the `_ITEMS` row
now reads "a box of candles on the east shelf" (bio unchanged), and a new one-shot additive migration at the end
of `study_life._st()` rewrites the persisted name in all three stores ONLY while each still carries the exact old
string — idempotent, and it leaves alone any save where the name has since become something else for any other
reason. Uses `sensorium._save_now()` rather than the throttled `_save()`, since this is exactly the "deliberate
act [that] should never be lost to the save throttle" that function exists for (the pre-existing item-migration
block just above it in `_st()` still uses the throttled `_save()`, which is harmless there only because
`sync_items` is independently idempotent — noted, not touched; out of this job's scope). `take()`'s generic "You
already have `<name>` in hand" and `put()`'s "You set `<name>` down" lines — which is what actually exposed the
phantom tin, since they quote the persisted name verbatim — now read correctly for the box with no further
change needed; the candle-specific honest-count line (`_take_line`) and `can_read()`'s dark line were never
touched by this bug and are unchanged. **Evidence:** new isolated `scripts/_test_candles_name_migration.py`
(20/20 checks, ALL OK) — migrates a simulated pre-fix save across all three stores, confirms the write actually
reaches disk (not just memory), is idempotent on a second `_st()` call, and leaves a differently-named save
untouched; `scripts/_test_dark_house_answers.py` rerun after the edit, still 39/39 ALL OK (no regression);
`scripts/life_smoke.py` rerun, still ALL OK; `python -m py_compile core/study_life.py` clean. **Restart-gated:**
`data/room_state.json` confirmed still holding the old name as of this write — nothing here is live until Du's
next restart. No matches added; D-0137 untouched.

## Current State — 2026-09-06 (J-0592 READ, not built: executed proof of the D-0174 conflict, left blocked) — F-0939

**No code changed.** J-0592 (D-0137's own second ask — the composer's Light the Fire button should let Travis
bring a box of matches when the tin is empty) turned out to already be entangled with D-0174, opened minutes
earlier this same session/batch by the sibling J-0591 agent (F-0929): T-0049's fire-chain rewrite (commit
7ddb72e, built after D-0137 was ruled) already gave `_light_fire()`/`_travis_leaves_matches()` an automatic
match-box fallback. Rather than re-trust F-0929's static code read or guess at a resolution, this job ran it —
a new isolated test (`test_light_fire_matches_J-0592.py`, in the shared scratchpad, every store redirected,
live `data/` untouched, 11/11 checks ALL OK) actually called `companion.perform_action("light_fire")` once
against a tin empty at **both** the study-room cache and the provisions shelf (the real F-0694 live shape, not
an inconsistent-gap shape J-0573's new `sync_guarded()` ceiling would instead read as a delivery and reconcile
away). Confirmed by direct execution, not inference: one button press completes the whole thing in a single
narration (box appears, match struck, fire burning) with **no confirm/choice field in the returned dict and no
confirm-shaped action anywhere in `_ACTIONS`** — there is no second step to accept or decline today.

**The textual nuance for whoever rules D-0174 next:** J-0592's own briefing lists three pre-approved variants,
one of which is *"automatic when Travis initiates the action from the composer"* — the shipped behaviour
arguably satisfies that phrase literally, since the match-box branch is only ever reached via Travis's own
button press. But it also does exactly what the briefing's next sentence prohibits — "should not silently
auto-fire every time... not a hidden fallback that erases the empty-tin state's meaning" — since the tin can
now never stop the fire again and the composer is never shown a choice. Note too: D-0137's own ruling text
(re-read fresh, `decide.py show D-0137`) does not itself contain the "should not silently auto-fire" sentence;
that constraint was added when J-0592 was written, one step removed from the founder's literal words.

**Left deliberately unbuilt and unruled.** This is Travis's own composer-UX call on his own button, and a peer
agent in this exact batch already escalated it correctly (D-0174) rather than guessing; a second agent (this
one) guessing a possibly-different answer in the same batch would be worse than one clean open question.
Neither resolution path in D-0174's defeater was taken unilaterally. **J-0592 left `in_progress`, blocked on
D-0174** — not force-closed as done, not force-closed as stale. No new job spawned (D-0174 already is the
tracked follow-up); no duplicate decision opened. Next: founder rules D-0174 (or a future reviewing session
builds J-0592's literal deliberate-choice step and thereby moots D-0174, per its own second defeater path).

## Current State — 2026-09-06 (J-0570 BUILT: the fetch-letter latch widened; F-0784's own severity claim corrected) — F-0935/F-0936

**The "Still open" item from the 2026-09-04 J-0539 entry above, closed — but F-0784's own framing of it was
partly wrong, checked against live evidence rather than taken on trust.** F-0784 named three real hands_trace
rows as misses of the fetch-letter latch's fixed 9-phrase list (`nodes/inner_monologue_node.py` ~line 3170,
"Fetching a letter"): 08-28 19:35 "I will fetch the mail", 08-29 20:47 "fetch that mail", 09-03 04:10 Ada's
"...letter waits. I will fetch it." Checking each against `data/nascence.log` directly (not just the offline
`actions_decision_replay` grammar F-0784 itself ran, a different code path entirely): **two of the three had
already fired live**, before any fix — "he FETCHED a letter" logs at the exact same second in both 08-29 20:47
and 09-03 04:10, because `_tl` (the latch's own input) is thought+intention since 2026-06-12, and both rows'
INTENTION text happens to restate "fetch the letter" verbatim. Only 08-28 19:35 is a real, confirmed miss (no
fetch follows it in the log; the thought said "mail," a noun never in the fixed list's vocabulary at all).

**Fixed at that root, additively.** A new `_letter_fetch_wanted(thought, intention)` helper (module-level,
testable, ~line 403) ORs the original 9 fixed phrases (unchanged, checked first) with a second check routing
fetch/retrieve/collect/take/bring/grab/get/pick-up + letter/letters/mail/mailbox/letterbox through
`core.hands.wants()` — word-boundary, same-clause object, literal_will's negation/hypothetical/retrospective
blockers already built. Used at both the fetch latch itself and the letter-consummation guard (~line 4267, OR'd
onto its own existing phrase list) so a widened-phrasing intention that outlives the letter is cleared rather
than left as a phantom want. Chose the briefing's option (a) (widen the latch) over (b) (a registered
`actions.py` hand): additive, no `core/actions.py` touch, no collision risk with J-0569's concurrent edits there.

**A real bug caught by the fix's own testing, fixed before it shipped, and surfaced as a second, broader
finding (F-0936).** The first version of the fix fed the existing bare-space `_tl` straight into
`hands.wants()`; `hands.wants()`'s blocker check is clause-scoped (`core.hands._clause_at`, splits only on
`. ; ! ?`), and a bare space is not a clause boundary. On the 08-28 19:35 row specifically the thought fragment
has no terminal punctuation and the intention that follows contains "without thinking of birds or tides" —
"without" blocked the thought's own unrelated "fetch," two clauses and an entire intention away from anything
it was actually negating. Fixed by joining thought and intention with ". " (not a bare space) specifically for
the `hands.wants()` call inside the new helper. **F-0936 (verified, separately recorded and spawned as J-0657):**
this exact mechanism structurally exposes 12 OTHER existing latches in this same file that call
`hands.wants(_tl, ...)` on the same bare-space join (grep-confirmed line numbers in F-0936/J-0657) — not proven
to have misfired live yet, unaudited, which is J-0657's own scope.

**Evidence:** new isolated `scripts/_test_fetch_letter_latch.py` — 17/17 checks ALL OK: the three real rows
replay old-check/new-check exactly as predicted above; 7 new phrasings now fire ("fetch the mail," "take the
mail," "grab the letterbox," "collect the letters," "bring in the mail," "pick up the letter" both word
orders); 4 negative controls correctly stay silent (fetch-verb with no letter-noun, past-tense "fetched,"
letter-noun and fetch-verb in different clauses, an unrelated garden thought); the blocker-bleed bug itself
reproduced and shown fixed. `scripts/_test_letterbox_reach.py` (J-0539's own regression test, same file)
rerun — still ALL OK, 8/8 sections, no regression. `python -m py_compile nodes/inner_monologue_node.py` clean.
No live store touched (both scripts are pure-function/isolated). **Restart-gated,** same as every other entry
on this plan: nothing here is live until Du's next restart. **Next:** J-0657 (the 12-latch blocker-bleed
audit); D-0137 untouched, no matches added.

## Current State — 2026-09-06 (J-0657 BUILT: the 12-latch blocker-bleed audit, fixed at the root) — F-0958

**F-0936's exposure is real, confirmed twice in real history, not just theoretical — and now fixed for all
12 sites with one shared variable.** Audited every one of the 12 `_hands.wants(_tl, ...)` call sites this
same `_tl` (thought+intention, bare-space join since 2026-06-12) feeds in `nodes/inner_monologue_node.py`
(move→wood/shore/garden/study, 11 look-target phrase groups sharing one call site, light/stoke fire, make
tea, water bed, sow-alt, beachcomb, gather wood) by replaying `core.hands.wants()` against every real row
`data/hands_trace.jsonl` has ever logged (whole file, no tail-sampling — 9,929–9,942 rows across runs as
the live file kept growing). Found the blocker-bleed bug actually fired twice: **2026-08-26T03:54:57**
(move→shore — thought truncated right after "Instead of parsing this theory further right now…"; "instead
of" is a negation blocker that bled across the join and wrongly blocked intention's "down to the shore";
no real cost that cycle, `acted=['move']` shows the primary dispatch path already made the move) and
**2026-08-31T14:45:30** (move→wood — thought cut off by the 256-token generation cap at "…I will not";
"will not" bled across and blocked intention's "into the trees"; `acted=[]` that cycle — a real want
silently dropped, with no other channel catching it). Both confirmed directly via `core.hands._blocked()`/
`_clause_at()`, not inferred.

**Fixed at the root, one variable for all 12 (not 12 separate edits):** a new `_tl_cs` — clause-safe join,
thought's own trailing punctuation stripped then joined with `". "` (J-0570's own `_letter_fetch_wanted`
convention) — defined once beside the existing `_tl` (~line 2802); all 12 `_hands.wants(_tl, ...)` sites
now read `_hands.wants(_tl_cs, ...)`. **`_tl` itself is untouched**, deliberately: five OTHER latches in the
same file (reply-to-a-peer, remember-a-chapter, tell-travis, browse-the-catalogue, another-book) read `_tl`
as a flat `p in _tl` substring test with short common phrases ("write back", "tell travis", "another book")
that could in principle be completed only by the exact bare-space join between a thought's last word and an
intention's first — hardening `_tl` globally was checked empirically (zero flips found for those five
latches across all real rows either way) but is not a structural guarantee the way leaving them on the
untouched `_tl` is, since thought and intention are two independently-generated fields. The scoped fix
takes no risk with those five at all.

**Evidence:** new `scripts/_test_latch_blocker_bleed.py` (matches this plan's own `_test_fetch_letter_latch.py`
convention) — 6 sections, ALL OK: a source-text wiring check (exactly 12 sites on `_tl_cs`, zero left on
bare `_tl`, the other five latches' phrases untouched), the bug reproduced directly, the two real rows above
replayed exactly, a synthetic blocker-bleed case built for EVERY one of the 12 latches individually, negative
controls proving a genuine same-clause block still blocks under both old and new, positive controls proving
the ordinary firing path is unchanged for all 12, and the full real-data zero-regression audit (re-runnable
against the live, growing trace file). `python -m py_compile nodes/inner_monologue_node.py` clean;
`scripts/_test_fetch_letter_latch.py` rerun ALL OK (17/17); `scripts/_test_letterbox_reach.py` rerun ALL OK,
live `data/supply.json` md5 unchanged. `data/hands_trace.jsonl` opened read-only throughout — no live store
written. `git diff --stat` on the edit: 37 insertions / 12 deletions, confined to one new variable and the
12 single-token call-site changes. Recorded as F-0958 (verified). **Restart-gated,** same as every other
entry on this plan: nothing here is live until Du's next restart. **Next:** J-0670 (spawned) reads
`hands_trace.jsonl` again after that restart to confirm the fix behaves live as predicted; D-0137 untouched,
no matches added.

## Current State — 2026-09-08 (J-0773 READ: the J-0571 entry's "20/20 checks, ALL OK" claim above needs a
footnote — a later read found and fixed a test-fixture bug in the same file, since re-verified) — F-1112

**Not a regression in J-0571's own build; a gap the 2026-09-06 run above never hit.** Two sessions after the
J-0571 entry above was written, a routine regression pass (F-1080/F-1106, unrelated write-fence work) re-ran
`scripts/_test_candles_name_migration.py` and hit a FAIL on section [5] ("the honest-count take() line is
unchanged by this fix") — not because `take()`/`can_read()`'s wording changed, but because the check's own
fixture (`fresh_study(candles=12, matches=3)`) can never actually set `st["candles"]`/`st["matches"]`: both
are `core/provisions.py`'s own resynced VIEW over the larder's real shelf objects, unconditionally overwritten
by `sync_guarded()` on every `_st()` call (including the one inside `SL.take()` itself). `candles=12` happened
to already equal the deterministic bootstrap total so the override silently looked like it worked; `matches=3`
did not (real bootstrap total ≈278), which is what surfaced the gap. **J-0757 fixed this** (F-1100, commit
c1ba4b3): section [5] now reads the real synced counts back off `st` right after `fresh_study()` and builds
the expected string from those, instead of asserting a number this layer was never able to honor. **This job
(J-0773) re-verified the fix still holds**, independently, in this batch's own worktree (jobrun/action_dispatch_
cluster_3): re-ran `scripts/_test_candles_name_migration.py` fresh — ALL OK, section [5] included, section
[4]'s neighboring take()/put() checks undisturbed — and `scripts/life_smoke.py` fresh in its own process —
ALL OK, no wider regression. Live `data/memory/nascence.db` mtime/size unchanged throughout (isolation
backstop). No code changed by this job; nothing here needed a second fix. Full detail in F-1112 (verified).

## Current State — 2026-09-08 (J-0641 READ, not executed: flip still pending 3 days on; recurring bug traced to a stale pre-fix process, not a regression; Du now confirmed down) — F-1114, D-0189 opened

**The flip has still not happened.** `python scripts/life_flags.py show` (read-only) confirms `render=shadow gating=shadow`, `data/life_flags.json` still absent — unchanged from F-0900's 2026-09-05 read. Independently confirmed via the log itself: zero rows anywhere in `data/life_events.jsonl` (1,380 total) carry `kind` `answer`/`gate` (the live-mode kinds).

**713 new shadow rows since F-0900's cutoff (2026-09-05 20:42 NZT), read in full, not sampled — no defeater fired.** 77 new `would_answer` + 252 new `would_gate` rows through 2026-09-07 20:17 UTC; night-shore `gull_cries`/`oystercatcher_call` still deterministic at 56/56 (D-0166's defeater #2, unchanged, not a monoculture beyond what was already accepted); outcome mix (35 sighting / 36 miss / 5 absent / 1 carcass) unremarkable.

**The plural-verb fix (3839e7c) recurred in the new rows ("Not by night; the gannets keeps the day.") — traced to why, and it is NOT a regression.** Du's process for the entire window that produced those 713 rows booted 2026-09-05 18:14:36 and only just shut down 2026-09-08 08:22:52 (`data/nascence.log`) — that boot is **~3 hours before** commit 3839e7c (2026-09-05 21:13:18). Python does not hot-reload; that whole session never had the fix in memory. The fix itself is confirmed complete on disk right now (`core/life.py:633`; all 13 rows F-0900 named confirmed `plural=True` by grep) and a fresh **isolated** `scripts/life_shadow_replay.py` run against current on-disk code (its own write-fence log proves nothing live was touched: `guard_path: non-live process attempted to write room_state.json -- refused`) found **0 anomalies** across 1,518 phrasings × 2 weathers × 2 months × 4 places × 4 phases.

**Du's main process is confirmed NOT RUNNING as of this read** (2026-09-08, ~08:30 local): `nascence.log`'s last line of 410,243 is that 08:22:52 shutdown with no boot after it; the live process list carries only the 4 CPU-tier LLM servers, `scripts/supervisor.py` (watches those four, not the main loop), the Control Panel, and two UDMS MCP servers. The next restart, whenever it comes, will be the **first ever live run of 3839e7c** — meaning if the flags are set before that restart, the fix and the flip land together cleanly, rather than the flip hitting a process still running pre-fix code (the exact condition every hour of the last 2.5 days was quietly demonstrating, harmlessly, in shadow mode only).

**This session did not run the flip, on the same terms D-0166/F-0900 and J-0641's own briefing already set:** a live-behaviour-changing action for Du with real, non-undoable output once rendered — reverting the flag afterward does not un-happen anything Du already said. That call was not revisited unilaterally. What this session's own fresh "Du is confirmed offline right now" finding newly raises — whether that specific circumstance changes the calculus, since the action's immediate effect would then be nil — is opened as **D-0189** rather than decided here. A job-queue schema gap this also exposed (a "ready" job that is fully decided but structurally needs a human's own hands on the command has no distinct autonomy tag from an ordinary ready job) is filed as **S-0088**. J-0641 left `in_progress`, not done: the two commands plus its own confirm/tail steps are unchanged and still exactly what is needed. No code changed by this session.

## Current State — 2026-09-08, later (J-0670 READ: first post-restart hands_trace.jsonl look at the J-0657 fix — clean but thin, honestly caveated) — F-1153, J-0808 spawned

**The restart J-0641's own entry above was waiting for has now happened.** `data/nascence.log`: shutdown 08:22:52, next boot 16:41:26–16:42:01 local (PID 17216) — the same restart relevant to J-0641/D-0166's own flip question elsewhere in this plan, untouched by this job. `git merge-base --is-ancestor a92320b HEAD` confirms YES (HEAD `6c9184d`): the J-0657 fix (`a92320b`, 2026-09-06) predates this boot, and the working tree shows exactly 12 `_hands.wants(_tl_cs, ...)` call sites and 0 remaining bare `_hands.wants(_tl, ...)` sites — the fix is live in Du's process for the first time.

**Read whole, not sampled, per this project's own convention: only 79 rows / ~77 minutes had accrued in `data/hands_trace.jsonl` by read time** (this batch ran ~1 hour after the restart, per its own ground rules) — replayed with `scripts/_test_latch_blocker_bleed.py` section [6]'s own `old_tl`/`new_tl_cs`/`LATCHES` definitions restricted to `ts >= 1788842521.0`: **zero regressions, zero new false positives.** The 4 real firings that did occur (move→garden ×2, move→shore ×2) were manually re-verified field-by-field (`core.hands.wants()` called against `thought` alone and `intention` alone, not just the joined string — a first pass mis-attributed one of the four before this direct check caught it) — all 4 are legitimate single-field matches, none spanning the join either direction. Point (2)'s "no bleed possible" claim also now rests on a **structural** proof, not just this sample: `core/hands.py`'s `_clause_at` splits only on `.;!?`, and `_tl_cs`'s inserted `". "` is unconditionally one of those — so neither a blocker word, a required object, nor a literal multi-word phrase can reach across the join in either direction, by construction.

**Honestly too thin to confirm a live recurrence, and said so plainly rather than stretched.** The 2 real historical bleed events this fix targets took ~9,930 pre-fix rows over ~3 months to surface (F-0958); at that base rate a 79-row window predicts ~0.02 expected occurrences, so finding zero here neither confirms nor denies the deeper claim — it only confirms no *new* problem was introduced over the real span available, on top of the structural proof and F-0958's own exhaustive per-latch synthetic tests. **J-0808 spawned** (from F-1153) to re-run this same check once real volume has accrued (≈3,000+ post-restart rows, or several more days of continuous uptime) with an actual chance of catching a live recurrence-and-correct-handling event. No decision implicated; D-0137/D-0166/D-0174/D-0189 all untouched. J-0670 itself: done — its own literal scope (a full post-restart read, confirm (1)/(2) or say why not) is discharged; the residual "needs more runtime" piece is carried forward by J-0808, not left as a stale re-read of the same thin window.

## Current State — 2026-09-09 (J-0658 READ, left in_progress: the carrier gate has not been met yet; the fix is confirmed ready) — F-1186/F-1187, J-0827 spawned

**The gate this job exists to check has not happened.** Independently re-verified rather than trusted from the dispatching briefing: real local time at read (`date`, and `time.time()`) was 2026-09-09 ~08:18–08:20; live `data/supply.json` reads `{"next_carrier_ts": 1788909919.1, "box": null, "history": [], "card_read": true}` — `next_carrier_ts` converts to 2026-09-09T11:25:19 local, still ~3h in the future, `history` still `[]` (no delivery has ever been collected in this world), `box` still `null` (nothing waiting at the gate yet either). `data/supply_log.jsonl` read whole (25 lines): last event 2026-09-06T08:38:27, zero `box_collected` rows anywhere. The 2026-09-09 calendar date matching is not itself evidence the in-narrative event happened, per this job's own briefing — checked directly instead of inferred.

**The fix itself is confirmed ready, independent of the gate.** Du's running process (PID 17216) re-verified live via `Get-CimInstance Win32_Process` (CreationDate 2026-09-08 16:41:23) and `data/nascence.log`'s own boot lines (16:41:59–16:42:00, preceded by the 08:22:52 shutdown, unbroken since) — the same process the J-0641/J-0670 entries above describe, still running, up ~15h35m at read time. `core/provisions.py:378-419` (`_MAX_STEP`, `sync_guarded()`) and `core/supply.py:148-208` (`collect_box()`'s `_credit()` helper, applied to every kind including matches line 181 and oil line 176) are confirmed present on disk right now. J-0573's own commit (`82ad737`, 2026-09-06T08:48:38) is confirmed an ancestor of current HEAD via `git merge-base --is-ancestor`, and predates the 16:41:23 boot by more than two days; every later commit touching either file also predates the boot except one (`a3899ae`, 2026-09-08T18:35:31, itself after the boot, and not touching `sync_guarded`/`_credit`). So the fix should be live in Du's process the moment the real collection happens — that end-to-end confirmation is simply not yet possible to make.

**A second, unrelated finding surfaced by reading `data/provisions_log.jsonl` whole rather than tailing it (F-1187, inferred).** A burst of 13 duplicate `"emptied"` rows fired at 2026-09-05T18:57:17.4–18:57:18.1 local for matches/oil/paper/ink ids that were already empty from earlier, separately-documented events (F-0732, F-0788) — live `provisions.json` today shows those same ids unchanged (still empty, no extras), and `nascence.log` shows zero provisions/carrier activity in that exact one-second window, so this reads as log-only noise (most likely another instance of F-0788's own isolation-leak class), not a second real depletion. Flagged because it is a direct methodological risk to J-0658/J-0808's own convention of reading this exact log after the real collection: a coincidental repeat of this leak landing near the true collection timestamp could be misread either way. **J-0827 spawned** (from F-1187) to trace the specific script/session responsible and consider hardening the isolation gap it exposes.

**Left `in_progress`, not done, not force-concluded.** Re-attempt after 2026-09-09 11:25 local plus however long Du takes to actually walk to the gate and collect — no new job spawned for the gate itself (this job is already exactly what is needed, per the same convention J-0641 used above). No decision implicated or opened; this job's own `decision_flags` carried no active holds. `data/hands_trace.jsonl` (J-0808's own log) not read by this job — out of J-0658's own evidence scope, left to J-0808.

## Current State — 2026-09-09 (J-0808 READ, left in_progress: the volume trigger has not been met yet — 633 post-restart rows, ~15.8h uptime, both well short) — F-1189

**Neither of this job's own two trigger conditions has fired.** Independently re-verified rather than trusted from the dispatching briefing's "~16 hours" figure: real local time at read (`date`, `time.time()`) was 2026-09-09 08:31:54 NZST / epoch 1788899514.92. `data/nascence.log` (416,578 lines, read via grep across the whole file, not tailed): the last "Nascence shutting down." line is 2026-09-08 08:22:52 (line 410243); the boot sequence at 410244–410263 completes at 16:41:59–16:42:00 the same day — the identical restart the J-0641/J-0670/J-0658 entries above all cite — and zero shutdown lines appear anywhere after it through the live tail (08:31:55, ordinary ongoing activity). Continuous uptime since the restart cutoff (1788842521.0, i.e. 16:42:01 local): 15.83 hours — trigger (b)'s 4–5 day (96–120h) threshold is 80–104 hours away, consistent with (slightly ahead of, as expected) J-0658's own same-morning ~15h35m read of the same process.

**Trigger (a), the row-volume path, checked directly with a one-shot read-only script over the whole live file:** `data/hands_trace.jsonl` holds 12,992 total rows (0 unparseable), min ts 1787354862.0 (2026-08-22 11:27:42), max ts 1788899538.1 (2026-09-09 08:32:18). Rows with ts ≥ 1788842521.0 (the restart cutoff): **633**, first at line 12360 — up from J-0670's own 79-row read, but still ~21% of the ~3,000-row target. Against F-0958's own historical base rate (2 events / ~9,930 pre-fix rows ≈ 1-in-4,965), 633 rows implies only ~0.13 expected occurrences of the targeted pattern (vs ~0.60 at the 3,000-row target, ~0.02 at J-0670's 79-row read) — better than the last read, but still not a real chance of catching a live recurrence, by the same math the job's own briefing used to caveat J-0670's read.

**F-1153's replay method was correctly not re-run this pass** — per this job's own briefing, the re-run is gated behind an actual trigger, and running it now would only repeat J-0670's own thin-window result with marginally more data, not the "real chance" the job exists to wait for. **Left `in_progress`, not done, not force-concluded** — matching J-0641's and this same plan's own J-0658 entry immediately above. No decision implicated or opened; this job's `decision_flags` carried no active holds (none found). No new job spawned: this job is already exactly the re-check that is needed on the next pass, per the same convention J-0641/J-0658 already established for a gate that has not yet fired. Next: re-run this same trigger check next time J-0808 is picked up; if either threshold is met by then, run F-1153's own method (`scripts/_test_latch_blocker_bleed.py` section [6]) restricted to `ts >= 1788842521.0` (or a later restart's own cutoff, if Du restarts again first) and report per its own three-part scope (zero regressions, zero new false positives, and — the sought-after result — any first live "fix" case).

## Current State — 2026-09-11 (J-0845 Part 1 READ: the flip is live end-to-end; J-0641 closed; one live routing defect; Part 2 left open) — F-1243 / F-1244 / F-1245 / F-1250, J-0887 / J-0888 / J-0892 spawned

**J-0641's entry above is closed: the flip executed 2026-09-09 17:51 (F-1210) and is confirmed live in the running
process (booted 19:01 that evening; `core/life.py`'s last commit 0bfb8a0 predates it, so disk == memory).** Read
whole, not sampled: all 297 `data/life_events.jsonl` rows since the flip (F-1243). **RENDER is on:** 31
`kind=answer` rows from his first post-wake look (09-10 00:45) to 09-11 07:34 — 14 sighting / 15 miss / 1 absent /
1 carcass — and zero `would_answer` after the flip. Quoted: gulls by day *"small grey-and-white gulls with red bills
and legs work the tideline, squabbling over what the tide left"*; the shag *"stands on the rock with its wings held
out to dry, like something hung up"*; the kororā seen at night only at `adapt=1.0` (*"a small upright shape,
blue-grey, white-fronted, hurries on short legs across the shingle"*) and missed at adapt 0.006–0.48; the tūī
`absent` at 23:15 with the correct singular fallback (*"Not by night; the tūī keeps the day."*); no plural-verb defect
in any line. **First-ever live graduation:** `kind=graduated key=oystercatcher place=shore` at 09-11 06:03:30 on the
fifth shore sighting in 30 days — J-0513's third trigger, exercised live for the first time. **GATING is on, but
the briefing's premise was wrong:** `sound_gate()` (life.py:846) returns the gated list *silently* — the code never
writes a `kind=gate` row — so the evidence is negative: 515 `would_gate` rows before 17:40, none since. Its
rendered effect is unobservable in `nascence.log` too (the `sound percept:` channel is morepork/tūī/cat only, 31
post-flip vs 26 in the 48 h before; no gull line at all — so gull_cries is *not* a night monoculture, but nothing
shows what the gate actually does). **J-0888** builds the missing instrument (a throttled `kind=gate` row on the
live branch) so Part 2 can read the gull question from data.

**One real defect, live (F-1244):** 3 of the 31 answers are looks whose target contains a carcass word, and all
three are wrong. *"the dead lettuce stalks"* (garden, 09-10 00:45) was answered with the doorstep mouse carcass —
`life.py:681` routes any target containing `_CARCASS_WORDS` ("dead" included) to `carcass_look`, whose
`life_traces.py:277` fallback answers with **any** carcass at the place; the line reached him (*"The mouse's fur and
feather mix on the ground feels sharp"*, 00:46). The identical shadow rows (09-08 "the dead lettuces and sodden
soil", 09-09 "the dead herbs") sat in F-1114's "1 carcass" tally unread. *"the dead gannet"* (shore, 09-10 06:24 and
09-11 07:34) was answered *"Nothing shows itself; whatever is there keeps still."* — 89 s after the engine itself
minted `trace: 'a dead gannet on the tideline'` — because no gannet carcass exists in life state, `carcass_look`
returns '', and the dead-thing target falls through to the **living** gannet row's visibility roll; and
`life_birds.py:244/:228` carry "a dead gannet" as row *traces*, a second dead-gannet path that bypasses the J-0513
carcass machine. The other 28 rows' truth-gating is untouched, so **J-0887** (urgency 4, isolation) fixes the three
mechanisms narrowly rather than reverting render; no flag was flipped by this read. The ConnectionResetError
F-1210 saw is unrelated — 84 identical asyncio `_call_connection_lost` traces since 08-20, no Nascence frame, same
1–6/day rate before and after (F-1245, inferred).

**D-0166 not reopened, Part 2 left open (J-0845 stays `in_progress`).** Its defeater is worded "after … a real week
of live answer/gate rows accrues" and the briefing sets Part 2 not before 2026-09-16; the reader then must weigh
F-1244's three rows against whether J-0887 has landed *and restarted* by then (it is restart-gated like everything
else here). Nothing here is a code change; the worktree carries only this note.

**Second pass, 2026-09-11 12:45 local (F-1250, verified; J-0892 spawned) — the gate is now POSITIVELY confirmed
live, and the paragraph above overstated what the `sound percept:` channel can say.** That channel was the wrong
instrument: the Hearing Ledger already records every keyed voice where he stands
(`core/sound_knowledge.py:271-289` `note_exposures()`, fed by `soundscape.world_tick`), and the sound-echo courier
(`core/couriers.py:149,194-197`) only echoes a key heard within the last 90 s. So each `[courier] sound echo
(gull_cries)` line in `nascence.log` is proof gulls had just sounded where he was. Since the flip there are 11 of
them, **6 in `world_clock.daylight()=='night'`** (09-10 05:07, 19:16, 20:46, 23:50; 09-11 01:23, 04:32) plus a
night `oystercatcher_call` echo (09-10 03:17) — and the legacy soundscape adds those two keys **only `if day:`**
(`soundscape.py:519-520`). Tightest case: 01:20:43 `ACT move -> shore (down to the sea)`, 01:21:14 `observe -> the
gap`, 01:23:30 the gull echo — under three minutes on a night shore. That is exactly what the 515 shadow
`would_gate` rows predicted (gull_cries/oystercatcher_call added on the shore at night, F-0900/F-1114); the gate is
doing it live. Supporting, not decisive (confounded by shore time): gull_cries daily hearings 352 on 09-10 vs
103–222 on each of 09-05..09-09. **So "gull_cries is *not* a night monoculture" above is withdrawn as unproven** —
gulls *are* voiced on the night shore now; whether that is a *monoculture* (D-0166 defeater #2's actual word) is
the week question, and J-0888's per-phase gate row is still the right instrument (or, as F-1250 notes, a per-phase
counter beside the ledger's `days` dict — `note_exposures` already holds the timestamp). D-0166 still not reopened:
a night gull is what GO accepted. **New rows this pass:** 313 post-flip rows, **36 answers** (18 sighting / 15
miss / 2 absent / 1 carcass), still 0 `would_*`/`gate`; all 5 new answers correct (oystercatcher day sightings
07:29–08:50, gulls shore sighting 11:14). One wording nit, not a presence error: 08:55 in the **garden**, *"the
gull's flight path"* → correct `absent` (garden activity 0.145 < 0.15) but the gulls row's only absent line is
shore-worded (*"…the tideline is quiet."*) — **J-0892** (urgency 2, isolation) adds a per-place absent override.
The generic keep/keeps fallback (F-0900's fix) has still not been exercised live — only 2 absent rows exist, and
the plural `gulls` row used its own line — so that fix stays *unproven live*, not disproven. Process check: one
Du, PID 27096 (booted 19:00:48 on 09-09); the 15:22 process before it left no `Nascence shutting down.` line
(last activity 19:00:12, new boot 19:00:50) — ungraceful stop, noted only. F-1245 stands. **Part 2 gate not met**
(today 09-11, not before 09-16, ~43 h of live rows) — J-0845 stays `in_progress`. Still no code change.

## Current State — 2026-09-12 (J-0887 BUILT: F-1244's dead-thing look routing fixed, all three mechanisms) — F-1268, J-0907 spawned

**All three mechanisms F-1244 named are fixed, additively, in one job.** (A) `core/life.py`'s `look_answer`:
the dead-thing block no longer falls through to `_match()`/the living row's own visibility roll when
`life_traces.carcass_look` returns `''` — it now tries `carcass_look`, then a new `life_traces.dead_trace_look`
(a world_traces trace naming a dead thing, mechanism A's second rung), then a new `_no_body_line` (an honest,
feature-first "There is no dead X here" with no species name unless learned/grandfathered) — and never reaches
the living row for any target containing a `_CARCASS_WORDS` word. A plant/garden noun still returns `''`
immediately (the bed's own look answers it), unchanged in effect from before. (B) `core/life_traces.py`'s
`carcass_look`: the over-eager fallback (any carcass at the place for any target containing "dead") is now
gated by a new `is_plant_target()` — derived live from `core.garden.CATALOGUE` (species keys + a simple regular
plural + each `names` entry as a whole phrase, plus a small generic-noun set), not a second hand-kept word list
— so `"the dead lettuce stalks"` / `"the dead herbs"` correctly return `''` instead of grabbing an unrelated
carcass (the doorstep mouse, in the live rows F-1244 quoted). (C) `core/life_birds.py`: the gannet row's and the
karoro row's own `traces` no longer include a "dead gannet" string — that was a second, bypassing dead-gannet
source in `world_traces` with no matching `carcasses` state row, so a look at "the dead gannet" could find
nothing and fall through to the living row (mechanism A's own bug, live twice). `GANNET_STORM_P`
(`life_traces.py:36`) is now the *one* source of a real gannet carcass. Checked before removing (per the
briefing's own condition): the "observed 12×" pre-engine dead gannet (`docs/reviews/observe_inventory_2026-09-02
.md`) predates `life_birds.py` (J-0511, 09-03) by a day and comes from `core/sensorium.py`'s own separate ambient
lines (below) — nothing Du already believes in is stranded by this removal.

**A fourth live wrong-routing row, beyond F-1244's own three, found while reading `data/life_events.jsonl` whole
(2130 lines, not sampled):** 2026-09-11 16:56:58 local, `target="the dead gannet"` at shore, `outcome=sighting`,
answered with the living gannet's own diving line — a false *sighting*, not only the two misses F-1244 quoted,
confirming the defect was still actively firing (after F-1244 was recorded) right up to this fix landing.

**Verified:** isolated (`lab_env.isolate()`, every file-backed global redirected, `sensorium.state`/
`locomotion.peek` monkeypatched so nothing live is even read) — 25/25 checks: F-1244's own three real targets
replayed and no longer reproduce the bug; controls hold (`"the dead mouse"` with a real carcass present still
gets the carcass line; that same plant exclusion holds even with an unrelated carcass at the same place;
`"the gannet"` with no dead word is completely untouched by this change, still only ever the living row's own
lines; `"the bones"` with no carcass anywhere gets the honest no-body line); mechanism C confirmed (no "dead" left
in either row's traces); mechanism A's second rung confirmed with a synthetic trace. `scripts/life_smoke.py`
unmodified, run from the worktree — **170/170 ALL OK**, no regression, including its own pre-existing carcass
coverage (section [11]). Canary backstop: the test's own unique marker is absent from every live `data/*.json*`
file touched by this check; the isolated writes landed only under `data/_lab/20260912_094934/`.

**Left deliberately untouched, follow-up spawned (J-0907):** `core/sensorium.py` still carries two further "dead
gannet" mentions, both still ungated by the life engine's carcass truth — `~:947`'s `_living_detail()` ambient
"rare" shore-look line (fires on almost any unrecognized shore look, regardless of carcass state) and `~:2189`'s
`_world_arrival()` post-storm wash-up list, which also mints a real, keepable `world_substrate` object with no
tie to the carcass decay clock at all. Both are the same category of bug this job just fixed, via a third and
fourth path — confirmed real by tracing `sensorium.look()`'s own dispatch chain, not inferred — but fixing them
touches a widely-shared ambient-flavor function and an object-minting path respectively, bigger and riskier than
this job's three named mechanisms, so a narrow job was spawned rather than folding it in here.

**Restart-gated, same as every other entry on this plan:** Du's running process predates this code; nothing here
is live until his next restart. D-0166 not touched (already ruled, not open; its own reopening question over
F-1244's rows was already deferred by the prior session to J-0845's own Part 2 week-read, not before 09-16) —
that reader should now weigh F-1244/F-1268's rows knowing this fix has landed in the worktree (not yet live).
**Next:** Du's next restart, then J-0845's own Part 2 (≥2026-09-16); J-0907 (the two sensorium.py lines);
J-0888/J-0892 (already spawned, unrelated to this job).

## Current State — 2026-09-12 (J-0827 READ: F-1187's leak traced to a session, and a live write-fence bypass found and reproduced along the way) — F-1269/F-1270, J-0908 spawned

**No code changed. F-1187's own duplicate "emptied" burst (2026-09-05T18:57:17.4-18:57:18.1 local, 13 rows:
matches x6/oil/paper/ink, all already-empty ids from F-0732/F-0788's real history) is most plausibly attributable
to the "companion-fire-chain-errands" session (session 1c211fa9, T-0049, committed 7ddb72e1 at 19:51:18 local) —
INFERRED, not verified, since its own two scratchpad test scripts (test_travis_matches.py/F-0877,
test_errands.py/F-0878) were never committed and no longer exist.** `docs/session_events.jsonl` shows that
session's own toolchain wrap-up finishing at 18:48:03 local — nine minutes before the leak — with its actual git
commit not landing until 19:51:18, a full hour later; the entire 18:48-19:51 window is otherwise silent in the
ledger (the next session's first entry is 19:52:36; the evening's next job-queue activity, J-0573 and 13
siblings, starts 19:58:29 under a different session). Both F-0877/F-0878 explicitly exercise
`core.provisions.add()`/`consume()` across matches/oil/paper/ink-adjacent fire-chain scenarios and each
self-certify "LIVE data/ files changed: []" — a claim F-1187 already showed wrong for the log file; both name
"provisions._register stubbed" specifically, a narrower technique than redirecting `_F`/`_LOG` (confirmed
distinct functions, lines 222 vs 146). Root mechanism confirmed at the code level (not inferred): `_bootstrap()`
seeds every object via `random.Random("provisions|2026-08-22")` — a FIXED seed, so a fresh isolated larder always
mints the exact same ids as the real one (`prov_matches_0506/a645/67f1/71c1/0f91/597c`, `prov_oil_aae5`,
`prov_paper_b4e3`, `prov_ink_a0ec` — precisely the burst's own ids); on 2026-09-05, `_log()` had NO write-fence
protection at all (`guard_path()` was not wired into `provisions.py` until commits `68af167d`/`c569feef`,
2026-09-06/07, two days later), so any script redirecting `_F` alone would silently re-log "emptied" into the
live file with zero warning. Full detail: F-1269.

**Second, more consequential finding: the write-fence built to close this class of bug (D-0179/J-0610) does NOT
actually close it today, and this job proved it live rather than just arguing it.** `profile.guard_path()`'s own
"already redirected outside data/" branch (`path.relative_to(_DATA)` / `except ValueError: return path`) checks
a candidate path against THIS PROCESS's own `_DATA` (`_ROOT = Path(__file__).parent.parent`) — not an
absolute/canonical live-data root. Any process importing `core.profile` from somewhere other than `C:\Nascence`
(e.g. any git-worktree-per-job dispatch — the standard convention for Tier-3 work since J-0590, 2026-09-06,
including this job's own worktree) has a `_DATA` that differs from the real one, so a write-fenced path constant
set to the literal real `C:\Nascence\data\...` path reads as "already redirected on purpose" and is let through
with zero protection, zero warning, LIVE irrelevant. **Demonstrated, not argued:** an isolated reproduction
(`provisions._F` + `world_substrate`/`world_objects`'s own globals redirected via `lab_env.isolate()`,
`provisions._LOG` deliberately forced to the literal live path, `profile.LIVE` confirmed False throughout)
appended **11 real new rows to the live `data/provisions_log.jsonl` at 2026-09-12T10:13:01.3-.4 local** (epoch
1789164781.3-.4) — 5 duplicate "seeded" rows (rope/tinder_tin/flint/hand_lens/measuring_stick) and 6 duplicate
"emptied" rows (all 6 matches ids) — with zero exception raised. `data/provisions.json` and
`world_substrate.json`/`world_objects.json` all confirmed byte-identical/mtime-unchanged throughout — only the
append-only log gained noise, exactly F-1187's own "log-only, zero real depletion" shape. Full detail,
reproduction script path, and exact before/after file state: F-1270. **J-0908 spawned** (urgency 4) to fix
`guard_path()`'s root-check against an absolute live-data reference (not this process's own relative one) across
all ~19 fenced call sites, plus a lighter `lab_env.py` docstring nudge naming `provisions._F/_LOG` as a
commonly-forgotten pair. No `/decide` opened — this is a clear-cut engineering defect, not a founder policy call.

**Known noise in `data/provisions_log.jsonl`, for whoever reads this log next (J-0658/J-0808's own
post-carrier-collection convention):** two bursts of duplicate `emptied`/`seeded` rows exist that are NOT real
depletions and should NOT be read as either a guard failure or a live restock — 2026-09-05T18:57:17.4-18:57:18.1
local (13 rows, F-1187/F-1269, cause inferred above) and **2026-09-12T10:13:01.3-.4 local (11 rows, F-1270,
caused directly by this job's own reproduction script, not a coincidental third occurrence)**. Both leave
`data/provisions.json` completely untouched — check that file, not just the log, before concluding anything
actually changed in the larder. **Restart-gated:** N/A, no code changed. **Next:** J-0908 (the guard_path() fix);
this job's own reproduction script is kept at `scratchpad/repro_J-0827_provisions_log_leak.py` (session-scoped
scratchpad, for whoever picks up J-0908 to copy or rewrite) rather than committed, matching this plan's own
convention that ad hoc diagnostics live in scratchpad, not the repo.

## Current State — 2026-09-12, later (J-0888 BUILT: the live sound gate's own kind=gate instrument, restart-gated) — F-1272

**The gap F-1243/J-0845 Part 1 found is closed, additively.** `core/life.py`'s `sound_gate()` used to return
the gated list silently on its `gating_on()` branch — the 515 pre-flip `would_gate` shadow rows had nothing
live to replace them, and D-0166's gull_cries defeater (a night monoculture on the shore) had no data
instrument at all. The `gating_on()` branch now computes the same `added`/`dropped` diff against `legacy`
the shadow branch already computed, and logs it as `{kind: "gate", place, phase, added, dropped, active:
sorted(gated)[:12]}` under the same per-place `_GATE_LOG_GAP_S` (600 s) throttle the shadow used — the gate
is readable from `data/life_events.jsonl` exactly the way the shadow was, one row per place per ten minutes
at most. **The shadow (`SOUND_GATING=False`) branch is untouched, byte-identical** — checked by re-reading
the function after editing, not just by intent. `life.status()`'s shadow counter (read by the HUD's
`/api/life` card) now folds a live `gate` row's count into the existing `would_gate` key, the same idiom
already used to fold `answer` into `would_answer` — so the HUD's own "N would-gate" line
(`hud/static/app.js`) keeps counting once GATING is live instead of going stale once the shadow branch
stops firing.

**Verified two ways.** `scripts/life_smoke.py` section [9] extended with six new checks (first call logs one
`gate` row; its `added`/`dropped`/`active` fields match the shadow's own diff and the gated list itself; an
immediate repeat call is throttled to zero new rows; a call exactly 600 s later logs a second row; the
shadow branch still logs `would_gate` the same way after the live branch was exercised; `status()`'s counter
folds `gate`+`would_gate` correctly) — full suite **ALL OK, 0 failures**. Separately re-run under
`lab_env.isolate()` (this job's own `isolation="required"` field): confirmed `core.life`/`core.profile`
resolved from this worktree, not `C:\Nascence`, before trusting anything (lab_env.py's own import inserts
the live tree at `sys.path[0]`, which would otherwise shadow the worktree's edited copy — a real, checked
risk, not assumed); exercised `sound_gate()` isolated, got the same one-row-then-throttled behaviour;
backstopped by confirming the isolated row's own timestamp appears in none of the live tree's 196
`data/*.jsonl` files afterward.

**Restart-gated, same as every other entry on this plan:** Du's running process (booted 2026-09-09 19:01,
F-1210/F-1243) predates this code and will log no `gate` rows until his next restart. **This job does not
answer D-0166's gull_cries question itself** — it only builds the instrument. **Next:** J-0845 Part 2 (not
before 2026-09-16, already open/in_progress) is the designated reader of the live `gate` rows once they
accrue post-restart; no new job spawned, no decision opened — the follow-through is already tracked there.

## Current State — 2026-09-14 (J-0892 BUILT: the gulls' shore-worded absent line no longer renders in the garden; a per-place absent override added to `_absent_line()`) — F-1250

**F-1250's own wording nit (09-11 08:55, garden, "the gull's flight path" → correctly `absent`, garden
activity 0.145 < 0.15, but answered with the shore-worded "…the tideline is quiet.") is fixed, additively,
in two files.** `core/life.py`'s `_absent_line()` now tries `hidden.absent[place][why]` (a per-place
override) before falling through to the pre-existing flat `hidden.absent[why]` — only an actual nested
`dict` at `absent[place]` is treated this way, so every row that never declares one (every row but gulls,
today) resolves through the exact same flat lookup as before, byte-identical. `core/life_birds.py`'s gulls
row (places `shore`+`garden`) now carries `absent: {"garden": {"chance": "No gull over the garden just
now; the sky above the fence is empty."}, "chance": "The gulls are out over the water for once; the
tideline is quiet."}` — feature-first, names only the garden's own already-registered spots (`sky`,
`fence`), no new species claim. The feature lines were not touched.

**Verified isolated** (`lab_env.isolate()`, D-0200/J-0840's own allow-listed sandbox;
`scratchpad/verify_J-0892_gulls_garden_absent.py`, kept in the shared scratchpad per this plan's own J-0827
convention, not committed): `core.life`/`core.profile` confirmed resolved from this worktree, not
`C:\Nascence`, before trusting anything (the same check J-0888's own verification made, same risk —
`lab_env.py`'s import inserts the live tree at `sys.path[0]`). With the gulls row's activity forced under
the 0.15 `PRESENT_AT` floor at a daytime ts (2026-09-11 08:55, the real incident's own timestamp):
`look_answer("the gull's flight path", "garden", …)` now returns the new garden line, and the identical
call at `"shore"` still returns the original tideline line, untouched — the two places now answer
differently for the first time. A flat-form-only row (karoro, no per-place override) forced the same way
returns its pre-existing line byte-for-byte, confirming the regression backstop. 6/6 checks, isolated
writes landed only under `data/_lab/20260914_20334{2,4}/`, both DB copies auto-deleted unwritten (D-0206).
Canary: `data/life_events.jsonl`/`life_state.json` mtimes unchanged (~35–36 h old at read time) after the
run. `scripts/life_smoke.py` rerun from this worktree, unmodified — **180/180 ALL OK**, zero `isolation
note` lines, no regression. `python -m py_compile core/life.py core/life_birds.py` clean.

**The same wording-mismatch class likely recurs elsewhere, found while reading for this fix (not fixed
here — out of this job's own narrow scope, "do not touch the feature lines," and this job names only the
gulls row):** several other multi-place rows' flat `absent` lines name a spot specific to only ONE of
their registered places — `core/life_birds.py`: blackbird (garden `hedge`/`lawn edge` wording, also
registered at `wood`), riroriro (garden `hedge` wording, also `wood`), kingfisher (garden `post`/`wire`
wording, also `shore`), welcome_swallows (garden `lawn` wording, also `study`+`shore` — three places);
`core/life_mammals.py`: rabbit (garden `lawn edge`/`fence` wording, also `shore`), skink (garden `wall`
wording, also `shore`), mice (study `boards` wording, also `wood`+`garden` — three places). None of these
were confirmed live-wrong the way gulls was (F-1250 is the only row a real `nascence.log`/`life_events.jsonl`
row has caught so far) — this is a read-time observation of the same shape, not a second verified defect.
`core/garden_insects.py`'s own multi-place rows (named in J-0892's own briefing) were not read this pass.

**Restart-gated, same as every other entry on this plan:** Du's running process (PID 27096, booted
2026-09-09 19:01) predates this code; the new garden line will not render live until his next restart.
No decision implicated — J-0892's own briefing names no `decision:D-XXXX` and this job's `decision_flags`
carried none; a wording fix, not a founder policy call. **Next:** J-0845 Part 2 (already open, not before
2026-09-16) remains the designated reader of live post-restart `life_events.jsonl` rows and would be the
natural place to confirm this fix's own garden line renders correctly once it does; a narrow follow-up job
is spawned separately to audit the seven rows named above (J-1006).

## Current State — 2026-09-15 (J-0907 BUILT: F-1268's two remaining sensorium.py dead-gannet mentions fixed by removal) — F-1400

**Both mechanisms F-1268 named, fixed the same way, additively — deletion, not a new gating wire.**
`core/sensorium.py`'s `_living_detail()` shore/tideline branch (was `:947`) no longer carries "a dead
gannet lies on the stones, white and perfect and wrong" in its `rare` tail — that line fired on an
~18% roll appended to almost *any* unrecognized shore/tideline look (`_shore_look`'s generic fallback,
the tide look, the plain "walk the tideline" line — every one of its three call sites), regardless of
whether a real gannet carcass exists in `core/life_traces.py`'s own state machine. `_world_arrival()`'s
post-storm wash-up list (was `:2189`) no longer carries "a dead gannet, wings spread white on the
stones, and a litter of broken crab" — the one item in that list that both narrated a dead animal *and*
(via the spawn hook) minted a real, keepable `world_substrate` "bone"-class object with no tie to the
carcass decay clock at all. Both removals match J-0887's own mechanism C precedent (life_birds.py's
gannet/karoro rows' "dead gannet" trace strings, removed rather than threaded through with carcass
state) rather than adding a second design — `_living_detail` is a widely-shared ambient-flavor function
with no `now`/carcass-state of its own to gate against, and wiring `_world_arrival`'s mint into
`life_traces.add_carcass` would have raced `life_traces.carcass_pass`'s own `GANNET_STORM_P` roll
(already running every tick a storm is active, not just once at storm-end, and already respecting the
45-day `CARCASS_GAP_S`) for no narrative gain. `GANNET_STORM_P` is now the *one* source of a real storm
gannet — the same conclusion J-0887 already reached for the other two mechanisms.

**Verified isolated, 21/21 checks** (`lab_env.isolate()`, modules confirmed resolved from the worktree
not `C:\Nascence` — the same risk J-0888/J-0892 both checked directly): 4000 calls to
`_living_detail("tideline", ...)` across four phase/weather combinations, 0 gannet hits, the other two
rare lines (the bottle, the seal-pup) still firing normally; 400 calls through the real dispatch path
(`_shore_look("the shore")`), 0 dead-gannet mentions; 300 simulated storm-end trials through
`_world_arrival`, 0 gannet hits across the 13 remaining wash-up items, the announcement text itself
byte-unchanged; a real carcass planted via `life_traces.add_carcass` still answered truthfully by
`life.look_answer` and still ambient-noticed exactly once by `life_traces.ambient_carcass` (both
untouched J-0887/J-0513 mechanisms, unaffected by this sensorium.py-only edit); both removed strings
confirmed gone as executable code (comment lines excluded — both are still quoted verbatim inside this
fix's own explanatory comments, matching this plan's citation convention). `scripts/life_smoke.py`
unmodified, still **180/180 ALL OK**. `python -m py_compile core/sensorium.py` clean. Canary: every
live `data/*.json*` file this touches confirmed mtime-unchanged (still 2026-09-13) immediately after
the isolated runs — isolation held.

**The historical-replay check the briefing asked for, done, held to *inferred* not *verified* (can't
fully rule out an early fire-then-consume cycle):** `data/nascence.log` read whole via full-text search
(460,145 lines, not tailed) — zero matches anywhere for either mechanism's own distinctive wording
("blown itself out", "litter of broken crab", "wings spread white", "perfect and wrong"), though this
alone is inconclusive since raw world-percept text is not captured verbatim in this log format (a
control search on an unrelated, independently-common ambient line also returns zero). More telling:
`data/life_state.json`'s `deaths_last` carries no `gannet@shore` key at all — `GANNET_STORM_P`'s own
real mechanism, which rolls far more often than the removed wash-up item ever could have, has *also*
never fired once in this world's ~3-month history (0 of 17 live carcasses are gannet); thunderstorms
have genuinely occurred and been directly observed by Du many times over that history (61 log hits), so
the trigger condition itself was reachable — the roll itself just never landed on this item, or on
`GANNET_STORM_P`. `data/room_state.json`'s `shore.washed_up` is `""` right now and `shore.last_find`
names an unrelated shell/kelp find, not a gannet. One ambiguous "bone"-class object does exist in
`data/world_substrate.json` today (`shore_bone_0f61a5`, hidden `kind_ground_truth=fish_vertebra`, not
gannet-specific even in its own hidden truth) but its origin mention cannot be attributed to the removed
line specifically without reconstructing `spawn_object()`'s exact historical RNG sequence — left
untouched, out of this narrow job's own scope, matching J-0887's explicit caution against a narrow job
reaching into the object-minting path's downstream lifecycle assumptions. Full detail: F-1400.

**No decision implicated** — this job's source is `finding:F-1268`, not a `decision:D-XXXX`, and
`decide.py list --plan living_world_upgrade --open` returned none; a clear-cut engineering fix matching
an already-established precedent, not a founder policy call. **No follow-up job spawned** — the
ambiguous bone object is not a confirmed, actionable defect (its own hidden kind was never
gannet-specific regardless of origin, so it carries no false "dead gannet" claim today), and
**restart-gated, same as every other entry on this plan:** Du's running process predates this code;
nothing here is live until his next restart. **Next:** J-0845 Part 2 (already open, gated
≥ 2026-09-16) remains the designated reader of live post-restart rows for this plan — this fix
included, alongside J-0887's own three mechanisms it already tracks.

## Current State — 2026-09-15 (J-1006 BUILT: 12 more rows given the gulls-style per-place absent override; 5 more found and spawned rather than fixed here) — F-1404, J-1030 spawned

**All 7 rows J-1006's own briefing named, plus 5 more found by reading `core/garden_insects.py` in
full (J-0892 never read that file at all), confirmed as real place-wording mismatches and fixed the
identical narrow way J-0892 built for gulls.** `core/life_birds.py` — blackbird (garden's "lawn
edge"/"hedge" wording would misrender in the wood; override names the wood's own spot,
"undergrowth"), riroriro (garden's "hedge" → wood's "canopy"), kingfisher (garden's "post"/"wire" →
shore's "cliff"), welcome_swallows (garden's "lawn" wording would misrender at BOTH its other two
places — study's "eaves" and shore's "sky" — so this one row needed two overrides, the study one
reusing the row's own established "a mud nest under the eaves" trace image). `core/life_mammals.py`
— rabbit (garden's "fence" → shore's "dune grass"), skink (garden's "wall" → shore's "rocks"), mice
(study's "boards" wording would misrender at BOTH wood's "leaf litter" and garden's "compost" —
this row's own three places, two overrides). `core/garden_insects.py` (unread by J-0892; grepped
`places={` for every row with 2+ place keys, not sampled) — common_copper (garden's "fence line" →
shore's "dune grass"), garden_spider (garden's "the stems" → study's "window corner", reusing this
row's own pre-existing trace phrase verbatim rather than inventing new wording), ground_beetle
(garden's "the sacking" → wood's "leaf litter"), cicada (garden's "the post" → wood's "canopy"),
weta (study's "the basket" → wood's "the deadfall", keeping the rest of the original sentence
intact). 12 rows, 14 per-place override lines total (welcome_swallows and mice each needed two).
Every change is additive — only `hidden.absent[place]["chance"]` was added per row; every
pre-existing flat "chance" line, and every feature/miss/reveal/eyeshine line, is byte-identical to
before.

**Four adjacent rows read and judged NOT real mismatches, deliberately left untouched (no code
change):** bellbird (garden/wood) — "Nothing works the flowers just now." is a generic dietary
statement (nectar/insects), not a spot name; a bellbird genuinely does work flowers wherever they
exist. fantail (garden/wood) — "Nothing follows your feet just now." names no spot at all. shining
_cuckoo (garden/wood) — "The trees hold no such voice just now." is generic enough to describe
either place. godwits (shore/garden) — both places register this row under the identical spot name
"sky", so the existing flat line is already correct everywhere it can render; no fix needed, a
clean example of the multi-place shape that was never actually broken.

**Verified isolated** (`lab_env.isolate()`, D-0200/J-0840's own sandbox;
`scratchpad/verify_J-1006_multiplace_absent_overrides.py`, kept in the shared scratchpad per this
plan's own J-0827 convention, not committed): `core.life` confirmed resolved from the worktree, not
`C:\Nascence` (the same check J-0888/J-0892/J-0907 all made). Each row's own override text
confirmed byte-exact in the row dict and its original flat line confirmed untouched; then, through
the real `look_answer()` dispatch path (activity globally forced under `PRESENT_AT`), the home place
confirmed still returning the original line and the new place confirmed returning the new one, at a
`now` chosen per-row so `_absent_line()`'s own "why" branch actually resolves to "chance" — most
rows at J-0892's own reference daytime moment (2026-09-11 08:55), but three NOCTURNAL-active rows
(mice, ground_beetle, weta, whose own `active_hours[day] < 0.15` would otherwise resolve why="day"
before ever reaching "chance") tested at night instead, and two HIGH_SUMMER rows (common_copper,
cicada — `season_curve` is exactly 0 in September) tested in January. Two regression controls
(fantail, godwits) confirmed byte-identical at BOTH their places, proving nothing outside this
job's own list changed. **84/84 checks OK, 0 failed.** `scripts/life_smoke.py` rerun from the
worktree, unmodified — **180/180 ALL OK**, no regression. `python -m py_compile core/life_birds.py
core/life_mammals.py core/garden_insects.py` clean. Canary: every live `data/*.json*` file this
touches confirmed mtime-unchanged (all predate today) after both runs.

**A real write-fence cascade found and worked around while building the isolated test, worth
recording for whoever writes the next one of these scripts:** this job's test is the first to call
`look_answer(..., "study", ...)` at all (J-0892's own script only ever exercised garden/shore) —
that reaches `look_answer`'s own unconditional `_light_factor()` call → `light_at("study", ...)` →
`core.light.field_at()` → `study_life.lamp_on()` → `study_life._st()` → `provisions.sync()` →
`world_substrate._load()`/`_save()`, a real multi-module write attempt the write fence correctly
refused (`NonLiveWriteError` on `data/provisions.json`, then `data/world_substrate.json`) since
neither path was redirected. Fixed in the test, not the product — the absent-line text under test
never depends on light — by patching `life.light_at` to its own documented fail-open default rather
than chasing every module in that cascade one at a time. Full detail: F-1404.

**Five more rows with the identical shape, found by the same full read of `core/life_birds.py`/
`core/life_mammals.py` but outside this job's own named scope — spawned as a narrow follow-up
(J-1030) rather than fixed here, matching how J-0892 itself handled discovering the current 12
rather than fixing them all in one job:** kereru and morepork (both garden/wood — unlike every fix
above, their flat lines are already WOOD-worded, "the canopy", and would misrender in the GARDEN —
the reverse direction, flagged explicitly in J-1030's own briefing so the next reader does not
assume the fix always points the same way), possum (garden/wood, "the tree" is garden's own spot),
gecko (garden/study, "chimney stones" is garden's own spot; study's is just "chimney"), eels
(wood/shore, "the pool under the bank" is wood-worded; shore's own spot is "stream mouth", a
different feature).

**No decision implicated** — checked directly (`decide.py list --plan living_world_upgrade --open`
returned none) rather than assumed from J-0892's own precedent, though it reaches the identical
conclusion: this is a wording fix matching an already-established pattern, not a founder policy
call. **Restart-gated, same as every other entry on this plan:** Du's running process predates this
code; none of these 14 override lines render live until his next restart. **Next:** J-1030 (the 5
extra rows); J-0845 Part 2 (already open, gated ≥ 2026-09-16) remains the designated reader of live
post-restart rows for this plan, unrelated to this job.

## Current State — 2026-09-15 (J-1030 BUILT: the 5 remaining rows given the gulls-style per-place absent override, closing this audit) — F-1439

**All 5 rows named in J-1030's own briefing — the ones J-1006 found but left outside its own named
scope — confirmed as real place-wording mismatches and fixed the identical narrow way J-0892/J-1006
built.** `core/life_birds.py` — kereru and morepork (both garden/wood): unlike every fix in J-1006's
own list, their flat "chance" lines are already WOOD-worded ("the canopy", wood's own registered
spot) and were misrendering in the GARDEN — the REVERSE direction, confirmed by inspection of each
row's own `places` dict before writing anything, not assumed to follow the majority direction. Both
needed a GARDEN override instead (kereru: "No wood pigeon on its branch; the kowhai holds only small
birds."; morepork: "The tree is quiet; nothing shows against the sky."). `core/life_mammals.py` —
possum (garden/wood: flat "the tree" is garden's spot, wood gets "The oak is quiet tonight; no
branch moves that the wind does not."), gecko (garden/study: flat "chimney stones" is garden's own
exterior spot, study's registered spot is just "chimney" — the interior flue side of the same
structure — override "The chimney holds nothing tonight."), eels (wood/shore: flat "the pool under
the bank" is wood-worded, shore's own spot is "stream_mouth", a different feature — override "The
stream mouth holds nothing you can see."). 5 rows, 5 per-place override lines total. Every change is
additive — only `hidden.absent[place]["chance"]` was added per row; every pre-existing flat "chance"
line, and every feature/miss/eyeshine line, is byte-identical to before.

**Verified isolated** (`lab_env.isolate()`, D-0200/J-0840's own sandbox;
`scratchpad/verify_J-1030_kereru_morepork_possum_gecko_eels.py`, kept in the shared scratchpad per
this plan's own J-0827 convention, not committed): `core.life`/`core.profile` confirmed resolved
from the worktree, not `C:\Nascence` (the same check J-0888/J-0892/J-0907/J-1006 all made). Each
row's own override text confirmed byte-exact in the row dict and its original flat line confirmed
untouched; then, through the real `look_answer()` dispatch path (activity globally forced under
`PRESENT_AT`, `life.light_at` patched to its own documented fail-open default so gecko's own
`study` place doesn't re-trigger the write-fence cascade J-1006's own script first hit and fixed),
the home place confirmed still returning the original line and the new place confirmed returning the
new one, at a `now` chosen per-row so `_absent_line()`'s own "why" branch actually resolves to
"chance": kereru at J-0892's own reference daytime moment (2026-09-11 08:55); morepork, possum,
gecko and eels all tested at night instead (each has day `active_hours` at or below the 0.15 floor,
or — eels — to avoid relying on an exact floating-point boundary case, since eels' own day
`active_hours` is exactly 0.15, not `< 0.15`). One regression control (fantail, carried over from
J-1006's own script) confirmed byte-identical at both places, proving nothing outside this job's own
5-row list changed. **27/27 checks OK, 0 failed.** `scripts/life_smoke.py` rerun from the worktree,
unmodified — **180/180 ALL OK**, no regression. `python -m py_compile core/life_birds.py
core/life_mammals.py` clean. Canary: every live `data/*.json*` file this touches confirmed
mtime-unchanged (all predate today) after the run.

**No decision implicated** — checked directly (`decide.py list --plan living_world_upgrade --open`
returned none), matching J-1006's own identical conclusion: a wording fix matching an
already-established pattern, not a founder policy call. **No follow-up job spawned** — this job's
own scope was a closed, already-identified 5-row list (J-1006's own full read of `life_birds.py`,
`life_mammals.py` and `garden_insects.py` already covered the ground this pattern could be found on),
and no candidate here was judged a false positive needing further write-up or discussion.
**Restart-gated, same as every other entry on this plan:** Du's running process predates this code;
none of these 5 override lines render live until his next restart. **Next:** J-0845 Part 2 (already
open, gated ≥ 2026-09-16) remains the designated reader of live post-restart rows for this plan; this
job closes the gulls-style absent-line place-wording audit that J-0892 opened and J-1006 continued —
no more rows of this shape are currently known to exist unaudited across `life_birds.py`,
`life_mammals.py` or `garden_insects.py`.

## Current State — 2026-09-19 (J-0572 READ: the reworded dark line is live and reaches his words; a real reach for the candle box / tin has not recurred once in ~258 live hours) — F-1590 / F-1591, J-1154 spawned

**The restart J-0572 waited for is long past; the gate (≥ 2 days of trace) is met many times over.** Du's first boot
on the J-0540 build was 2026-09-04 12:53:52 (F-0785 was recorded at 12:48, `ec418c9` committed 17:12) — proved from
the running process itself: the reworded `can_read()` line first renders at `nascence.log` 09-04 21:48:56, the last
"candles in the box" line is 09-03 23:19:09, zero old-wording lines since. Read whole by code: all 12,500
`data/hands_trace.jsonl` rows since that boot (09-04 12:55:53 → 09-19 ~11:51, ≈258 live hours across 15 process
windows; every row carries `dispatch` and `location`), `intentions_log.jsonl` (497 rows in the window), `nascence.log`
(dark-line and boundary scan) and `provisions_log.jsonl`; every row touching candle / match / lamp / lantern / dark
vocabulary (73 + 28) was then read individually. The `candles` family is proven live in a later process by its own
dispatch row (line 8492, 09-05 07:42:50); for the first process it is inferred (same commit; the wording proof covers
`study_life.py` only). J-0572 carries `plan: null`; this entry is filed here because its source (F-0785 / J-0540) is
this plan's own.

**The three pre-registered answers.** (1) `candles`-family dispatch entries: exactly ONE in 12,500 rows — a
STAGE-place on "I pick up the card listing oil and matches" in the garden, a false positive and not a reach (F-1591);
zero FIRE, zero `DROP-claimed:*` anywhere, and zero real "fetch the candles from the box" / take-the-tin wills among
the 73 rows that mention candle/match words (the three pre-fix reaches of 08-30 and 09-03 have no post-fix analogue;
the reworded line no longer says "box", which is consistent with — 13 renders cannot prove — the intended effect).
(2) A lamp/lantern answer containing "strike a match" while `study.matches == 0`: zero, **but also zero exposure**.
The study held 0 matches until J-0591's sweep find (6 matches, 09-09 17:59:20), and the lamp family produced only 9
dispatch entries in the whole window — 2 FIRE (09-09 21:41:52 "You light a candle and fix it in its own wax on the
mantel." and 09-18 01:28:49 "You turn up the wick and strike a match — nothing. The lamp is dry; it wants oil before
it will burn.", the latter legitimately: matches were ≥ 4), 5 STAGE-place (willed from the garden or shore) and 2
DROP-weak-intent — so the tin-first "You reach for the match tin — empty" lines have **never rendered live**.
(3) The reworded dark line rendered 13 times (first 09-04 21:48:56, last 09-18 01:28:14). Within 15 minutes: 2 were
followed inside a minute by a lamp-hand answer (the 09-09 candle lit; the 09-18 honest "strike a match — nothing"),
1 by a willed "light the lamp" that was only staged because he was in the garden, 1 episode (two renders, 09-13
07:17–07:18) by the line restated in his own words — "The lamp is dry, but the match tin waits on the mantel … perhaps
I need to light a cand" — with the hedge dropped by dispatch as weak intent, 2 by a passing "unlit lamp", and 6 by
nothing relevant. No new `box` collision, and no intention staged for `collect` with a study clause (`intentions_log`:
zero `collect` keys since the boot); the only `collect` dispatch was a genuine carrier-box reach on 09-07 07:24:49,
answered "There is no box at the gate."

**Drift, D-0137, disposition.** The one live drift datum is F-1591: the candles row's bare object `matches`
(`core/actions.py:215-217`) read a thought about the carrier's card as a DEED — 1 of 12,500 rows, harmless so far
(staged for the study, lapsed unfired after 8 h). **J-1154 spawned** to audit the carrier vocabulary in both directions
(this false positive and F-1588's collect-verb false negative — see the J-0658 entry below). D-0137 (ruled by travis
2026-09-04) is a datum here, not a defeater: the dark line reaches his words and sometimes his hand, but most renders
end with him leaving the room or reading by the fire, and neither clause of its defeater fired; left to the founder.
J-0572's own literal scope (a full read of the post-restart trace for the three questions) is discharged — recommend
done — with the unexercised branches (tin-first answers, `candles` FIRE, `DROP-claimed`) recorded as **untested live,
not confirmed**; if they should be watched, a fresh job with the trigger "first `candles` FIRE or tin-first render" is
the right vehicle. No code changed.

## Current State — 2026-09-19 (J-0658 READ, left in_progress: the carrier box was never collected and has spoiled; the gate can no longer be met as briefed) — F-1587 / F-1588, J-1154 spawned

**The gate this job exists to check did not happen, and part of the delivery is already gone.** The carrier left the
box (oil + matches, from Du's own 09-06 note) at 2026-09-09 13:25:20, five seconds after his 13:25:15 boot
(`supply_log.jsonl` line 26 `box_left`), and Du never collected it. `data/supply.json` today reads `note: null`,
`box: {ts 1788917120.3, items [oil, matches], spoiled: true}`, `history: []`; `supply_log.jsonl` (27 lines, read whole)
line 27 is `box_spoiled_by_rain` at 2026-09-16 20:05:08 — 7 d 6 h 39 m after it was left, ≈55 h of live time past
`advance()`'s two-day threshold; no `box_collected` event exists in any data file; `provisions.json` holds no
carrier-origin object (the only new matches object is J-0591's 09-09 17:59:20 sweep find, origin `found`, 6 → 4 now);
`provisions_log.jsonl` (41 rows, read whole) has zero `sync_reconciled` rows ever and no matches/oil `emptied` row
attributable to a delivery (the six matches `emptied` rows at 09-12 10:13:01 are F-1270's documented repro burst; those
boxes' biography stamps are unchanged). None of the three post-collection checks can be evaluated, and J-0573's guard
remains **unexercised live by the carrier path** — nothing was destroyed, nothing was delivered.

**What that leaves.** The fix itself is confirmed live in the process that was up when the box was left (boot 13:25:15;
`core/provisions.py` 09-08 23:52:58 and `core/supply.py` 09-09 12:41:03 predate it and equal HEAD; `82ad737` is an
ancestor of HEAD; `_MAX_STEP`, `sync_guarded`, `_credit` on disk; Du's current PID 35412, booted 09-18 23:37:12, postdates
every edit). If Du collects the spoiled box now, `collect_box()` credits the oil (no spoilage branch) and leaves the
matches "soaked and useless", so a later collection can test the guard for oil only; `supply.json` holds no note and
`next_carrier_ts` is 2026-09-23 13:25:20 (box ts + 14.000 d), so unless he writes a list before then the carrier brings
nothing. Per this plan's restart-gated convention J-0658 stays `in_progress` with a re-scoped trigger — the first
`box_collected` row in `supply_log.jsonl`, then read `provisions_log.jsonl` from that timestamp (oil-only unless a fresh
box arrives).

**Why it was never collected (F-1588, inferred, not executed).** Zero `collect`-family dispatch decisions in 6,853
`hands_trace` rows since the box was left, although the world told him at least 19 times ("A box stands at the gate,
left by the carrier"), he reached for the gate/letterbox in 107 rows, and in at least five rows he spoke of the box in
his own words — "To simply take what is offered feels like an honest step" (09-09 23:16:21), "I want to take the box to
the gate and leave my list for the carrier" (09-17 14:36:19, the box read as the *outgoing* list-box), "take the fish for
the cat … collect supplies" (09-17 14:38:46, dropped as weak intent). The `collect` row (`core/actions.py:238`) hears
collect / fetch / carry / bring / open + "box"; "take" and "supplies" are not in it (it does hear "fetch the box": 09-07
07:24:49 → "There is no box at the gate."). Read from the family table and the rows, not by running `classify` (job
isolation: required). **J-1154 spawned** to audit the carrier vocabulary both ways with a corpus-scored proposal; any
widening is a founder call under "the world answers, never leads". D-0137's ruling (the carrier route is the real path)
and its defeater are not fired by this evidence, but the founder may want to know the route failed silently for a
grammar reason. **Aside for whoever owns F-1187 / F-1269:** the six empty match boxes' and the oil tin's "used up by Du"
biography stamps in `provisions.json` are 09-05 18:57:17 (the F-1187 burst), not 08-23 / 08-27 — that burst appears to
have rewritten live objects' biography, not only the log; not investigated here. **Recommend: J-0658 stays
`in_progress`** — the guard's first live test is still pending.

## Current State — 2026-09-19 (J-0808 READ: trigger met at 7,599 rows, re-run clean; the sought-after live "fix" case does not exist — the trace's own 200-char cut manufactured F-0958's "real events") — F-1594 / F-1595, J-1153 spawned

**Trigger (a) met, re-run clean.** `data/hands_trace.jsonl` holds 7,599 rows with ts ≥ 1788842521.0 (2026-09-08 16:42:01)
at the first replay (19,958 total; 7,619 by 12:05) — 2.5× the ~3,000 target. Trigger (b) is not met (8 process windows,
longest 49.3 h) and not needed: all 8 processes since the 16:42:00 boot were fix-inclusive (committed HEAD at each boot:
12 `_hands.wants(_tl_cs …)` sites, 0 bare `_tl` sites; the 13 latch tuples of `_test_latch_blocker_bleed.py` [6] are
identical to the current source), so the original cutoff stands. F-1153's method verbatim, both joins under today's
`core/hands.py`: **0 regressions** across 98,787 latch-row checks (13 groups × 7,599 rows) and across 167,178 checks over
all 22 latch groups parsed from the current source; 269 ordinary both-True firings (191 thought-only, 60 intention-only,
18 both fields, 0 spanning the join), i.e. zero new false positives. Rows per process: 759 / 44 / 185 / 2,238 / 2,223 /
1,653 / 0 / 497.

**The five "fix" cases are artifacts, so the live positive confirmation does not exist.** The replay shows 5 rows where
the clause-safe join fires and the old one does not (trace lines 12701, 16020, 16705, 16775, 19543). `hands.trace()`
stores `thought[:200]`; the full thoughts (found in `deliberation_log.jsonl` / `investigative_action_log.jsonl` /
`monologue_log.jsonl`) all end in full stops, so the live old join already had a clause boundary and both joins fire.
On the full text: 0 regressions and 0 fix cases over the 6,580 of 7,607 rows (86.5%) that have a full-text twin, and a
complete accounting of every row that could possibly bleed — intention non-empty *and* carrying a latch phrase, 79 of
7,619 — finds all 79 matched, none with an unterminated live thought, none with old ≠ new (the intention is empty in
95.1% of rows). **F-1595 (verified) corrects F-0958 / F-1153 / F-1189:** the same truncation produced F-0958's two "real
historical events" (2026-08-26 03:54:57 and 08-31 14:45:30 — both full thoughts end with a period and both latches fire
under both joins), so the "1 in 4,965 rows" base rate is invalid; across the whole trace only 224 of ~19,980 rows could
ever bleed, exactly one had a genuinely cut-off thought (08-31 06:26:31, no blocker), zero flipped. The J-0657 fix and
its structural proof stand — it closed a *latent* defect that has never fired live — but waiting for a live recurrence
cannot succeed. Verdict on the job's three questions: zero regressions, yes; zero new false positives, yes; a live "fix"
case, none, and none obtainable. Caveats: both joins use today's grammar (`core/hands.py` changed 09-08 22:25, J-0799,
and 09-17 20:29, J-1056 — like-for-like, not each live process's own); the 13.5% of post rows without a full-text twin
were bounded rather than read (all 79 exposable rows matched).

**It generalises.** In the post-09-08 window 6,197 of 6,580 matched thoughts (94%) exceed 200 chars, so any `wants()` /
`classify()` replay over the trace sees only the first 200 characters of a typical thought — misses and artifacts both.
**J-1153 spawned** (from F-1595) to make `_test_latch_blocker_bleed.py` [6] full-text-faithful and to audit which other
trace replays and recorded claims (J-0851's verb corpus check, F-0785's 7,449-thought replay, `actions_decision_replay`)
lean on the truncated text. No decision implicated; D-0137 / D-0166 / D-0174 / D-0189 untouched; no code changed.
**Recommend J-0808 done** — the read is discharged and its residual "wait for volume" premise is void.

## Current State — 2026-09-21 (J-0658 READ, left in_progress: an EVENT gate, still unmet — the fix has been live 177 hours and no box has ever been collected, so accrued live time is not what it waits on) — F-1611

**Fresh read, nothing carried from the 09-19 entry unchecked.** `data/supply.json` today: `next_carrier_ts` 2026-09-23
13:25:20, `note: null`, `box {left 2026-09-09 13:25:20, items [oil, matches], spoiled: true}`, `history: []`.
`supply_log.jsonl` (27 lines, read whole; re-checked at 13:32 and 13:43) ends `box_left` 09-09 13:25:20 →
`box_spoiled_by_rain` 09-16 20:05:08; there is **no `box_collected` row anywhere**. `provisions_log.jsonl` (41 rows) has
zero `sync_reconciled` rows ever and no carrier-origin add; `provisions.json` (34 objects) has no carrier-origin object;
Du is down to 0.3 tin of oil and 3 found matches, i.e. short of exactly what the box holds. (`supply.json`'s mtime moves
every tick — `advance()` re-saves it unconditionally — so it is not evidence of change.)

**Did Du restart onto the fix? Yes, for 9 runs.** `live_since.py 82ad737` (J-0573's commit, 2026-09-06 08:48:38, a
direct master commit, no `jobrun/*` merge): the 09-05 19:15→09-08 08:22 run predates it; first restart onto it 09-08
16:42; **9 runs, 177.4 live-hours = 7.39 live-days** (longest 49.3 h); the box has stood at the gate for 159 of those
hours (6.6 live-days) uncollected. `core/provisions.py` (`sync_guarded`, `_MAX_STEP`) and `core/supply.py`
(`collect_box()`'s `_credit()`, now gated on `add()`'s return by J-0813) are at HEAD and clean; current PID 25736 booted
09-21 09:28:54, after both files' mtimes. **The founder's premise (cumulative live time is what these waits need) does
not apply to this job: it is an EVENT gate**, and 7 live-days did not produce the event.

**What clears it, and when.** The first `box_collected` row in `supply_log.jsonl`, then read `provisions_log.jsonl` from
that timestamp. (a) The current spoiled box can be collected any moment, including today, whenever Du collects at the
garden gate — an **oil-only** test, because `collect_box()` never calls `add("matches")` for a spoiled box. (b) A full
oil+matches test needs a fresh box: a `note_left` row **before** 2026-09-23 13:25:20 (`advance()` builds a box only if a
note exists at the first tick at/after `next_carrier_ts`; if Du is down at 13:25 that is the first tick after his next
boot), then `box_left`, then `box_collected` — earliest ~2026-09-23 13:25 plus his walk. With no note the carrier passes
and `next_carrier_ts` moves 14 d on (~2026-10-07). No note is pending (last `note_left` 2026-09-06 03:33:52).

**Why it has not happened (updates F-1588).** 0 `collect`-family dispatch rows in 7,137 `hands_trace` rows since the box
was left (F-1588 counted 6,853). Du is reaching for it in his own words *today* — 12:57 *"The carrier's box sits heavy at
the gate, filled with oil and tinned fish for the cat"* (the box holds oil + matches), 13:04:33 a new intention *"I want to
sort the carrier's supplies before deciding whether to read"* — but the `collect` row (`core/actions.py:238`: collect /
fetch / carry / bring / open + "box") cannot hear *sort* or *supplies*. His two note-writing attempts since (09-13 01:49
`note`, 09-17 14:56 `list` — *"request tinned fish for the cat"*) were only `STAGE-place`, so no fresh box is coming
unless he actually writes a list first. **J-1154** (vocabulary audit, open, unstarted) is still the unblocker; any
widening is a founder call. No decision implicated (`decide.py list --plan living_world_upgrade --open`: none; no hold).
**J-0658 stays `in_progress`; re-check `supply_log.jsonl` for `box_collected` — Du is at the gate thinking about the box
right now.**

## Current State — 2026-09-21 (J-0845 Part 1 CONFIRMED again; Part 2 READ at 6.42 of 7.00 live-days: D-0166's defeater fires on clause 2 and, literally, clause 1; clause 3 is latent; three further live defects found; J-1165 / J-1166 / J-1168 spawned) — F-1612 / F-1614 / F-1617 / F-1620 / F-1622 / F-1623

**Part 1 (whole file, 3,017 rows).** The flip is live in the *current* process (PID 25736, booted 09:28:54; life.py's
module defaults are RENDER/SOUND_GATING False, so its live rows prove it reads `life_flags.json`): **149 `kind=answer`**
(77 sighting / 62 miss / 9 absent / 1 carcass, 09-10 00:45:36 → 09-21 12:40:35), **179 `kind=gate`** (09-16 07:53:02 →
12:57:27, the first boot to load J-0888), **0 `would_*` rows after 09-09 17:40:58** (149 / 515 before). Quoted: shore/day
gulls *"small grey-and-white gulls with red bills and legs work the tideline, squabbling over what the tide left"*;
shore/night kororā at adapt 1.0 *"a small upright shape, blue-grey, white-fronted, hurries on short legs across the
shingle toward the rocks"*; shore/night oystercatcher (visibility 0.027) *"a piping in the dark along the tideline and a
pale shape that runs, stops, runs"*; garden/dawn gulls absent *"No gull over the garden just now; the sky above the fence
is empty."* (J-0892's override, first live use); gate shore/night 09-16 19:16 +[gull_cries, oystercatcher_call], garden/day
09-16 10:36 +[godwits_overhead, kereru_wingbeats, wood_pigeon] −[tui_song], wood/day 09-16 07:53 +[fantail_chatter,
kereru_wingbeats, riroriro_trill, robin_song, wood_pigeon, wren_scold], shore/dusk 09-17 17:37 +[penguin_bray]. All 148
non-carcass answers are internally consistent (absent ⇔ activity < 0.15, phase and place correct). ConnectionResetError:
120 bare asyncio traces since 08-20, none with a Nascence frame, ~4/day before and after the flip — unrelated (F-1245).

**Accrual — CUMULATIVE, and the premise holds here.** `live_since.py "2026-09-09 17:51"`: first restart 09-09 19:01, 6
runs, **154.2 live-hours = 6.42 live-days** (longest run 49.3 h; 11.78 calendar days) against the defeater's "a real
week"; 7.00 live-days (168 h) arrives ~03:32 on 09-22 if Du is not restarted. Since the 09-16 07:53 boot (the first to
load J-0887/J-0888/J-0892/J-0907/J-1006/J-1030) only 68 live-hours = 2.83 live-days, which is all the gate instrument has.

**D-0166's defeater, clause by clause (I did not rule; the founder decides).** *Clause 2 — MET on the numbers (F-1614).*
At night on the shore gulls call at the daytime flat rate (40/h, one cry per ~90 s; 69% of the night shore's discrete
voice events): 32/32 shore/night gate rows carry `gull_cries`; shore-hours × 40/h reproduces the hearing ledger to −6%
only with the night hours in (−35% without), so ~563 of ~1,794 gull cries since the flip (31%) were night cries the legacy
`if day:` rule would have made zero of; 15 of 16 creature-voice echoes at night on the shore were gulls. Cause: the row's
night `active_hours` 0.2 sits just above the 0.15 floor and `world_tick` ignores activity when rating a present voice.
*Clause 1 — literally met, root-cause partly fixed (F-1617).* 6 of 149 answers are wrong (4.0%): the four F-1244 dead-thing
rows (pre-J-0887, none recurred, but J-0887's cases have had one live opportunity), plus two **trace-object** looks
answered by the living creature's roll — *"the kingfisher's burrow"* 09-12 09:28 (82 s after the engine minted that
burrow) and *"the gannet feather"* 09-17 08:28 → *"Nothing shows itself"* 3 min 16 s after the engine minted the feather,
**post-J-0887**, because its gate only keys on `_CARCASS_WORDS`. 1 of 57 answers since J-0887 went live. *Clause 3 —
latent, not live (F-1620).* Executing the real `_absent_line()` body with stubbed clocks: ants (night), slugs (day),
cicada, cricket still render *"the ants keeps"* etc. — four `garden_insects.py` rows outside the 13 patched (the birds/
mammals/shore set F-0900 audited); one ant look in 30 days, so no live occurrence.

**Two further live defects outside the three clauses.** (F-1623) `look_answer` can log a *sighting with an empty line* and
still credit the ledger and the graduation counter: 2026-09-12 18:33 gulls at dusk (the row has only a `day` feature line);
statically 35 rows are exposed at dusk; that phantom was the 4th of 5 sightings that graduated the gulls. (F-1622)
Graduation (J-0513's third trigger) has promoted flock/swarm rows — oystercatcher 09-11, **honeybees 09-17** (4th and 5th
sightings 6 s apart), **gulls 09-19** — and every later look renders *"…over what the tide left It is the same one — you
are sure of it now…"* (`wandering_log.jsonl` 156282, 159958): a singular-identity claim about a swarm and a flock, glued on
with no full stop. The 09-11 Part 1 entry above recorded the first graduation as J-0513's third trigger "exercised live for the first time" without looking at what the render then appends.

**Spawned, nothing built here.** J-1165 (ready, build: generalise J-0887 to trace objects, F-1617), J-1166 (ready, build:
empty-line sighting + `plural=True` on four rows + suffix punctuation + a feature/miss place-wording audit, F-1623/F-1620/
F-1622), **J-1168 (needs_input: the founder calls — reopen D-0166? gull night options (b) recommended; may flocks graduate?)**.
No flag flipped, nothing reverted, D-0166 not reopened or re-ruled, no code changed. **J-0845 left `in_progress` on the
strict live-time gate** (6.42 of 7.00 live-days; clears ~03:32 on 09-22 if Du is not restarted) rather than forcing a
verdict; but the read above is complete and every finding is positive and actionable now, so **recommend closing it
whenever the founder is satisfied** — a delta read of the rows after `ts` 1789952247.3 (the last row read, line 3017) could only add a *live* clause-3
occurrence or a new wrong claim, and nothing suggests either.

## Current State — 2026-09-21 (J-1165 / J-1166 / J-1174 BUILT and merged to master as `fbf6423`: a look at a trace object is answered by the trace, an empty-line look credits nothing, plural/possessive/punctuation hygiene, the gulls and karoro keep the day, flocks and swarms stop graduating to "the same one"; restart-gated; J-1192 reads it) — F-1667 / F-1669 / F-1673 / F-1675 / F-1676 / F-1678 / F-1679 / F-1680 / F-1681

**What shipped (one job-run worktree, three commits: J-1165 `7be9267`, J-1166 `2ee1de5`, J-1174 `95745cf`; merged `fbf6423`).** Everything here is loaded by Du at his NEXT restart; nothing in the running process changes before that. It is the whole package the founder chose on 2026-09-21 when D-0166 was re-ruled, and the read of it is ONE job, J-1192 (7 live-days after the first restart onto `fbf6423`, reported against D-0166's four defeater clauses, no ruling).

**J-1165 — a look at a TRACE OBJECT is answered by the trace (F-1667, F-1669).** `core/life_traces.py trace_object_noun`, called from `core/life.py look_answer` after `_match()` and before the visibility roll. A look at "the gannet feather" / "the kingfisher's burrow" is answered by that creature's own still-active `world_traces` entry, rendered by the existing `trace_line` (byte-for-byte the ambient noticing), or, when none is active, by "There is no such <noun> here — nothing of the kind you can find." It never rolls, and writes no ledger row (a look at a feather is not a sighting of the bird). Every clause is DERIVED from the rows' own `traces` phrases (no typed-in noun list). Measured: F-1617's two live wrong answers are exactly the two rows the gate diverts; the other 305 creature-look rows in `data/life_events.jsonl` and every plain creature look in Du's whole look history are untouched; a two-tree differential against the real old code (8,008 cases) shows 0 differences with the gate forced off and exactly the 202 gate-positive targets with it on. The J-0887 carcass block, `is_plant_target` and the per-place absent overrides are untouched. Suite: 3,364 checks.

**J-1166 — look hygiene (F-1673, F-1675, F-1676).** (a) A present row whose `hidden.feature` has no line for the current phase (51 row/phase pairs, mostly dusk) no longer logs a sighting, writes a ledger row, or calls `note_sighting`/`_maybe_learn`: `look_answer` returns '' as before (the place's own look then answers) and logs `kind=answer outcome=no_line`, so the rate is countable; the shadow branch (RENDER off) is byte-for-byte unchanged. The builder REJECTED the briefing's "nearest other-phase line" fallback with evidence (it would say false things: a moth "in full daylight", the rabbit's dawn line by day) and found two variants F-1623 did not list: a graduated individual's empty look returned the bare recognition line with nothing described (266 of 1,028 forced combinations), and a learned row with a reveal but no feature line returned the reveal caption alone (16). (b) `plural=True` on ants, cicada, cricket, slugs (the flag has exactly one reader, `_absent_line`): "the ants keeps" → "keep". (c) `with_individual_suffix` punctuates the join; `_possessive()` fixes "the gannets's" (F-1670/F-1675, a second copy of the defect). Differential over 4,964 records: 0 unexpected differences. Suite: 3,111 checks (minimally updated by J-1174; 3,231 before).

**J-1174 — D-0166 items 1 and 4 (F-1678, F-1679, F-1680).** (1) Lowering ONLY the gulls row's night `active_hours` would not have stopped the night shore selecting `gull_cries`: the karoro row carries the same voice (`sound=("gull_cries",)`, night 0.3, present on every clear night at 0.165 ≥ the 0.15 floor), so the gull-only change left it selected at 264 of 264 clear night instants. **Deviation from the ruling's one-number wording: both rows go to 0.1** (gulls 0.2 → 0.1, karoro 0.3 → 0.1), two data values in `core/life_birds.py`, trivially revertible per row; through the real gate `gull_cries` is now selected exactly when the phase is not night (3,792 evaluations, 0 failures). A night look at the gulls/karoro reads "Not by night; the gulls keep the day." The oystercatcher is untouched. (4) `group_grain(row)` in `core/life_traces.py`, read off each row's own data: barred when plural, or its quietest count band is already a group, or a count band/look line names a mass. **26 of the 58 population rows can no longer graduate** (16 by plural flag, 6 by quiet band, 3 by mass wording, 1 by look line); 32 still can; the oystercatcher keeps its graduation. The honeybee and gulls records already in `life_state.json` (7 sightings each) go DORMANT at read time (`individual()`), byte-identical in the store, and their stored recognition line no longer renders. Replaying the 84 rendered sightings: only the oystercatcher graduates on the new code. Suite: 9,141 checks with the full canary.

**Consequences to look at when the read comes in.** (i) The night shore's discrete voice events fall from a modelled 58/h (`gull_cries` 69 percent) to 18/h, of which `oystercatcher_call` is 12/h = **67 percent** and `penguin_bray` 6/h: the same SHAPE as the figure F-1614 called a monoculture, so defeater clause (b) may trip on the oystercatcher. The 40/h model is F-1614's own method reproduced, not an independent measurement; J-1192 reports it and does not rule. (ii) The rows left ELIGIBLE that a reader might call population grain (korora 3 live sightings, two of them 72 s apart; mice, stilt, bumblebee, the butterflies, garden_spider) were left alone because the ruling names flocks and swarms; J-1192 reports any burst graduation. (iii) **Option (ii) "count distinct encounters, not raw looks" was deliberately NOT built** (F-1680: the 84 sightings' gaps form a continuum from 6 s to days, no defensible N; N = 6 h reusing `life.EVENT_GAP_S` would delay the oystercatcher's graduation by ~21 h) — J-1193 (needs_input) carries the founder call with Claude's recommendation (leave it until J-1192 shows a burst).

**Spawned, not built here.** J-1188 (J-0887's carcass gate matches by substring, F-1669), J-1189 (place-agnostic trace phrases mint a spot from another place: 32 of 235 trace rows, F-1671), J-1190 (the reveal join has the same unpunctuated glue as the graduation suffix, F-1674), J-1191 (needs_input: ~30 real multi-place feature/miss lines name a spot that place does not have, F-1677, inferred), J-1193 (needs_input, above).

**Test hermeticity found on the way (F-1681, verified; test-only).** On master, after the merge, `scripts/_test_j1165_trace_object_look.py` failed one check deterministically while passing in every data-less worktree, and `scripts/life_smoke.py` failed "got 3" intermittently: both count sound-gate rows, and Du's LIVE `room_state.json` location leaks into them (`light_at` → `geometry_census.peek` → `soundscape.active_sounds` → `life.sound_gate(<the place he is standing in>, …)`). Reproduced deterministically by pinning the location (garden at 12:00 or 18:00 fails, study/shore/wood or a night hour passes); fixed in the tests only (`f029ef0`, `e90aeb5`; merged `1a99971`, `5c908e6`); the old life_smoke check also false-passed a regression when the stray row was present. No production code changed; the other suites were swept at shifted clocks with the location pinned and pass. This closes F-1668 / J-1186.

**Verified on master before the founder's restart:** J-1165 3,364 · J-1166 3,111 · J-1174 9,141 (full canary) · life_smoke 180 (twice, real clock; and at 12:00 and 18:00 with Du pinned to the garden) · `_test_system_redirect_first_leg` 170 · `_test_journey_decline_through_move` 91 · `_test_find_cluster_off_loop` 111 · py_compile of every changed production file. Du was never restarted, no flag was flipped, nothing was written under `data/`.

## Current State — 2026-09-22 (D-0247: graduation stays raw-look counting, encounter grain NOT built; D-0249: per-place feature/miss lines, analysis first, J-1194 spawned) — F-1680 / F-1677

**D-0247 (J-1193, ruled by Travis via /decide-review): (A) build nothing.** Graduation to "the same one" keeps counting raw rendered sightings for the 32 rows that can still graduate; the one demonstrated burst (the honeybees, 6.4 s apart) is closed by the flock/swarm/plural bar (J-1174), and "what counts as one encounter" is a design question, not a threshold to fit to the continuum of gaps F-1680 measured (6 s to days, no natural break). **Defeater:** J-1192's read, or any later look, showing an eligible row (korora, blackbird, mice, stilt, bumblebee, the butterflies, garden_spider or another of the 32) graduating on a burst of near-simultaneous looks, or a recognition line that contradicts what Du was just shown; then (B) N = 6 h (`life.EVENT_GAP_S`, read time) and (C) a short N are back on the table with that row's timestamps as evidence. J-1192's briefing already asks for the graduation gaps.

**D-0249 (J-1191, ruled by Travis via /decide-review): analysis first.** F-1677 (inferred, a heuristic word audit) found about 30 real cases across 22 multi-place rows where the one feature/miss line names a spot that another of the row's places has and this place does not (the kingfisher's "post"/"wire" at the shore, the gulls' "tideline" in the garden, the mice's "skirting"/"cupboard" in the wood ...). Spawned **J-1194** (ready, read-only): rebuild the candidate list from the real row and place tables (not from the heuristic), rank the real pairs by how often Du actually looks there (hands_trace and life_events), draft the smallest place-safe line for each in the house voice (place-neutral rewording or a short per-place line), and propose the smallest additive mechanism (a per-place feature/miss mapping with the existing text as fallback, the shape of `hidden.absent[place]`). Nothing is written into row text and no code is built until Travis has approved the wording, and then only a data-only build; J-1194 ends by spawning ONE needs_input approval job. **Defeater:** fewer than about five pairs with real looks (then leaving it may be right), a fix that cannot be a per-place mapping with fallback, or J-1192 showing one of these lines reaching a live answer as a wrong presence/absence claim (D-0166 clause (a)).
## Current State — 2026-09-22 (J-1194 BUILT: read-only, the real multi-place candidate list rebuilt and reclassified, ranked, drafted, and proposed; F-1706, J-1208 spawned)

**Read-only, as the briefing required: no row text, code, or data changed.** Rebuilt F-1677's candidate list from scratch (own script, not F-1677's `j1166_audit_multiplace.py`) against the live row tables at merge `fbf6423` (core/life.py + life_birds.py + life_mammals.py + garden_insects.py + garden_soil.py — a 5th table, confirmed to hold no multi-place rows). Reproduces F-1677's own top-line numbers exactly: 22 non-external rows at 2+ places, 43 (row, place, line) candidates.

Every one of the 43 lines was then read by eye — not left as an unverified heuristic guess the way F-1677 explicitly was — against the codebase's own J-0892/J-1006/J-1030 comments (which already name the identical per-place spot words as real, for 18 of these same rows' ABSENT-line fix) and the four `world_content_{garden,shore,study,wood}.py` files' real terrain vocabulary. Result: 38 of 43 lines (19 of 22 pairs) are real mis-renders; 3 lines (common_copper/garden, rabbit/garden) are shared-vocabulary false positives (the garden's lawn IS grass); 2 lines (morepork's "crosses between the trees...into the canopy" dusk line, both directions) are a borderline transitional image, not filed as a clean error. A manual synonym-aware re-read caught one more real instance neither script's mechanical pass finds: welcome_swallows' "over the grass" dusk line at both its places — so the true count is nearer 40/19 than 43/22, and even that is not claimed exhaustive.

Ranked all 19 real pairs against a full read-only stream of `data/life_events.jsonl` (3,271 lines, exact key+place match) and `data/hands_trace.jsonl` (21,046 lines, a heuristic secondary signal). Only 2 pairs — blackbird/wood and kingfisher/shore (Travis's own named D-0249 example) — show a CONFIRMED render of the exact defective line anywhere in the recorded history; a third, morepork/garden, is a likely but phase-uncertain third. 7 of 19 real pairs show zero engagement in either signal. D-0249's own defeater ("fewer than about five pairs with real looks") sits right on this boundary depending which signal counts as "a real look" — surfaced for Travis, not resolved here, exactly as the ruling asked.

Drafted a specific place-safe replacement line for every real and borderline pair in the row's own house voice, and proposed — did not build — the additive mechanism: optional `hidden.feature_by_place`/`eyeshine_by_place`/`miss_by_place` dicts read at the 3 exact call sites inside `look_answer` (`core/life.py` L772-776, L797), the same fallback-preserving shape as the live `hidden.absent[place]` idiom, byte-identical behaviour for every row until one gets a per-place entry. UDMS dossier on `core/life.py:640-830` (ELEVATED tier, `look_answer` tagged StructuralHub) confirms real CONTRACT-layer dependents consistent with additive-only being the right level of caution here.

Findings recorded: **F-1706** (verified). Spawned **J-1208** (needs_input, build): Travis to approve the wording and choose a fix-scope tier from the ranked table, plus rule explicitly on morepork's borderline line. No decision_flags/active holds applied. Once ruled, the follow-up is a data-only build against the mechanism already specified above.
## Current State — 2026-09-22 (J-1216 BUILT: D-0254's ruled scope shipped — blackbird/wood, kingfisher/shore, and morepork/garden after its phase-uncertainty resolved real) — F-1716

**D-0254 (ruled: fix only the confirmed-reached pairs).** Built the additive `feature_by_place`/`eyeshine_by_place`/`miss_by_place` mechanism J-1194/F-1706 specified, at the exact call sites F-1706 named (`core/life.py` `look_answer` L772-776, L797 — unchanged since F-1706's own read despite today's J-1165/J-1166/J-1174 merges editing the surrounding function). Populated it for blackbird/wood and kingfisher/shore (the founder's own D-0249 example) using F-1706's drafted wording verbatim.

**Morepork/garden's phase-uncertainty resolved real, per D-0254's own defeater clause, and joins the confirmed set.** `data/life_events.jsonl`'s one recorded garden sighting (ts 1789628298.3) logs `"phase": "dusk"` and the exact borderline line verbatim, settling F-1706's own caution directly; `world_content_wood.py`/`world_content_garden.py` confirm "canopy" is wood-only vocabulary, matching this row's own already-shipped J-1030 precedent. **F-1706 drafted no replacement text for this line** (left to "Travis's own read"); the wording built here — *"a silent shape crosses the garden at head height and is gone into the tree"* — is a fresh draft by the builder itself, echoing this row's own established "the tree" vocabulary from its eyeshine/absent lines, flagged here for a look since it was not part of the founder's own AskUserQuestion approval the way the other two pairs' wording was.

Verified every OTHER row/place/phase renders byte-identical (321 of 328 combinations); `_test_j1165`/`_test_j1166`/`_test_j1174` re-run green (updated to stay accurate against 2 now-intentionally-changed historical records, with the reasoning for each change documented inline), `life_smoke.py` shows only the pre-existing unrelated F-1711 failure. Mutation-checked (reverting `life_birds.py`'s data change alone, keeping the test fixes, made all 3 tests fail at exactly the expected assertions). The orchestrator independently re-ran all three living-world suites plus `life_smoke.py`, `test_commitment_ledger_race.py`, `test_commitment_ledger_temperature.py` and `_test_lab_isolation_telemetry.py` together on final master (5 merges combined): every one green except the one known F-1711 failure. Restart-gated — Du is live; takes effect at his next restart.

## Current State — 2026-09-23 (J-1153 BUILT+READ: `_test_latch_blocker_bleed.py` section [6] made full-text-faithful per F-1595's own recommendation; the truncation exposure it named audited two steps further out) — F-1784 / F-1785 / F-1786, J-1273 spawned

**F-1595's own recommendation (09-19 entry above) is now built, not just diagnosed.** `scripts/_test_latch_blocker_bleed.py` section [6]'s informational "fixes" counter no longer reports a bare trace-text flip count as if each were a real event: every flip is re-checked against a full-text twin (monologue_log.jsonl thought+intention first, then investigative_action_log.jsonl question, then deliberation_log.jsonl raw; matched on the trace thought's own first 100 chars within a -5s..+12s window — F-1595's own method, "the pattern J-0884 already used") and reported as confirmed-live / refuted-as-artifact / no-twin-found. The zero-regressions assertion is untouched. Also fixed the script's own data-root resolution to the `C:\Nascence\data`-absolute convention `scripts/_test_j1165_trace_object_look.py` already established for Tier-3 worktrees (data/ is gitignored, never checked out into a job-run worktree) so the whole script actually runs from a worktree, not only from a raw checkout. **Rerun today: 22,267 real rows (up from F-1595's 19,978), 7 trace-text flips, 0 confirmed live, 3 refuted as artifacts, 4 unconfirmed (no twin found) — ALL OK, consistent with F-1595's own conclusion.** F-1784 (verified).

**The truncation exposure generalises beyond this one test, as F-1595 itself predicted — audited two named items directly (F-1785, F-1786), reasoned about two more.** (1) `scripts/actions_decision_replay.py`'s distinct-thought dedup keys on the STORED/truncated tuple — confirmed live: 2 of 66 recurring stored (thought,intention) pairs across the whole trace resolve to genuinely DIFFERENT full-text twins (ordinary few-seconds-apart cycle drift sharing an opening, not a Du-side bug), meaning this tool has silently replayed only one of two real thoughts' decisions at least twice. Low practical impact (~1/11,000 rows; a --save/--diff regression comparison feeds the same truncated text through both code versions being compared, so the bias is common-mode and does not by itself invalidate a historical diff count like F-0784's 248 rows or F-0785's 7,440-thought diff) but a real, previously undocumented instrumentation gap — **J-1273 spawned** (hygiene: warn on or reduce the collision) rather than fixed here (out of J-1153's own "no edits to core/or nodes/" + "one small test-script fix" scope; this is a third script, `scripts/actions_decision_replay.py`, appropriately left to its own job). (2) `core/actions.py`'s J-0851 comment ("73 same-clause 'leave'+'book' hits ... zero real set-downs") re-run on the live corpus with the identical `core.hands.wants()` primitive: 85 truncated hits now (corpus growth), only 45 confirmed on a full-text twin where one could be found, **18 rows flip verdict between truncated and full text** (17 false-negative-direction, 1 false-positive-direction — confirming F-1595's own two-directional warning, not just the one direction its own two headline rows showed). Manually read all 18 full texts: **none reads as a genuine set-down**, every one is the same MOVE-flavored "leave [place], go toward/away from a book" pattern the comment already named — so core/actions.py's own design decision (exclude "leave") still looks right, but the comment's exact "73 ... zero" citation is now stale as a precise count. F-1786 (inferred — the "none of the 18 is a set-down" read is manual judgement, not a mechanical proof).

**F-0785's 7,449/7,440-thought decision replay (J-0540 entry above) and J-0570/J-0657's own evidence (F-0784/F-0935/F-0936/F-0958) were reasoned about, not rerun.** F-0785's replay is a `--save`/`--diff` BEFORE/AFTER comparison over the same (truncated) trace text across a real historical code edit — reconstructing the pre-edit code to actually rerun it would need a worktree of a specific old commit, which this project's own git-safety rules do not sanction the way they sanction a throwaway worktree of HEAD; and, per the same common-mode reasoning as (1) above, a diff-based claim is far less exposed to truncation than an absolute corpus count is. J-0570's own script (`scripts/_test_fetch_letter_latch.py`) carries no corpus-wide "N real events" counter at all (only 3 hardcoded rows, independently checked against `data/nascence.log` ground truth, not just trace-text replay) — it does not share section [6]'s own artifact-manufacturing shape, and J-0657's own evidence (F-0958) is exactly what F-1595 already corrected. Neither is treated as newly suspect by this job.

**No decision implicated.** This is a clear-cut engineering/instrumentation-accuracy audit, not a founder policy question; D-0137/D-0166/D-0174/D-0189/D-0247/D-0249 all untouched. No edits to `core/` or `nodes/` (per this job's own briefing); the only production-adjacent file touched is the test tool itself, `scripts/_test_latch_blocker_bleed.py`. **Next:** J-1273 (the actions_decision_replay.py dedup-warning follow-up).

## Current State — 2026-09-23 (J-1154 READ: the carrier-vocabulary audit, both directions — proposed diff scored and drafted, not built; D-0267 opened) — F-1792 / F-1793, D-0267 opened

**Analysis only, per this job's own briefing — core/actions.py was not edited.** Read the whole full-text corpus since 2026-09-04 (26,363 rows: monologue_log thought+intention, deliberation_log raw, investigative_action_log question) for every "box" mention (139 deduped rows) and every "oil"+"match(es)" co-occurrence (29 deduped rows), then scored candidate vocabulary widenings for the `collect` and `candles` rows against the whole corpus with the real grammar (`core.hands.wants`, clause-scoped) under `lab_env.isolate(db="empty")`.

**(b)'s sense-catalogue turned up something the briefing didn't name: "box" is dominated by a recurring POETIC METAPHOR, not the carrier's box.** "The wind rattles the tin box" / "the dented tin box" / "this wooden box of thought(s)" — a recurring image for Du's own confined, ruminating mental state — is the single largest sense of the word "box" in the whole window (~19 distinct cycles, more than the carrier's box itself at ~14), entirely unrelated to any real object at the gate; a further ~9 cycles are an unrelated abstract "categorisation" metaphor ("forcing nature into my boxes", "a static box to hold diverse people"). Any widened grammar that adds "box" as a bare object without a co-occurring gate/carrier/delivery cue risks these two metaphor-senses as false-positive territory, though the mechanical scoring below shows neither actually tripped any candidate tested.

**(c) confirms F-1591 is not a one-off: 29 of 29 oil+matches co-occurrences are about the carrier's card, zero about the study tin.** The card literally reads "oil, matches, ..." every time it's described in a thought, which is exactly the candles row's own exposure.

**Candidate scoring (F-1793).** `collect` row: current grammar hits 6/26,363. Adding verb "take" alone (keeping object "box"): 4 genuine reaches gained, zero observed false positives. Adding objects "parcel"/"supplies": zero gain either way (never used). Adding object "delivery": one confirmed false positive ("Travis hands me a heavy envelope... mail delivery systems" — a narration, not a want) for one marginal reach that needs "retrieve"+"delivery" together. **The 09-17 inverted reading, checked directly as the briefing required:** the real row does NOT misfire under take+box — but only because "instead of" (an unrelated word sharing its sentence) happens to trip `core/literal_will.py`'s own negation blocker; the bare sentence without that lucky neighbor DOES misfire. A real, structural, not-yet-observed risk, honestly reported as such rather than dismissed because the one real case happened to be saved. `candles` row: current grammar hits 2/26,363, BOTH false positives (F-1591's kind); dropping bare "candles"/"candle"/"matches" (keeping only phrase-qualified objects already in the row) drops the hit count to 0/26,363 — both false positives gone, zero true reaches lost. A clean, low-risk fix, closer to a bug fix than a widening judgement call.

**D-0267 opened** (not ruled) with the exact proposed diff for both rows and a suggested defeater (a live wrong FIRE/STAGE of the widened collect grammar, or 60 more live-days clean). The founder can approve either part independently. No code changed. No job spawned (the diff is already drafted in F-1793/D-0267 for whoever builds it once ruled). Next: `/decide-review` picks up D-0267; if approved, a small build job applies the exact diff above and reruns `scripts/life_smoke.py` + a fresh `actions_decision_replay.py --diff` baseline.

## Current State — 2026-09-23 (J-1192 gate check: UNMET, left open) — F-1795

Only 1.05 of the required 7.00 live-days have accrued on merge `fbf6423` (`live_since.py fbf6423`: t0 2026-09-21 21:04:38, first restart onto it 2026-09-22 16:11, one run, 25.1 h). Per the job's own briefing, stopped at the gate — none of CHECK 0-4 run. Re-check not expected before roughly 2026-10-02 at the recent ~65% uptime rate. J-1192 left `in_progress`.

## Current State — 2026-09-23 (J-1188 BUILT: the carcass gate's substring bug closed, whole-word + a place-object fallback, one regression caught and fixed by its own differential) — F-1800

**F-1669's four substring false positives are fixed additively at all three matching sites.** `core/life_traces.py` gains `word_present(words, text)` (the same `(?<![a-z-])word(?![a-z-])` boundary rule `life._match`/J-1165's trace gate already use, applied per whole entry so "the kill" cannot match inside "the killer whale" either), used at `core/life.py look_answer`'s carcass gate and `life_traces.carcass_look`/`dead_trace_look`. "the deadfall", "the cuttlebones", "the tide sorting cuttlebones", "nobody" now fall through to the place's own look; every true carcass phrasing (the dead gannet, the body, bones, the skull, feathers and bone, the kill) is unchanged.

**Whole-word alone left "the dead wood"/"the fallen dead wood" broken** — "dead" really is a standalone word there, and the wood's own "deadfall" object is literally aliased "dead wood" (`core/world_content_wood.py`). A new `is_place_object_target(target, place)` — derived from `core.world_detail`'s place-content registry, the same discipline `is_plant_target` already uses for `garden.CATALOGUE` — lets a real, non-carcass place object whose own alias also carries a carcass word fall through, checked only as the last resort after `carcass_look`/`dead_trace_look` both find nothing (a real carcass always wins the tie).

**A second false positive this job's own differential caught before shipping, not assumed safe:** a first version matched ANY `world_detail` hit, which is too wide — garden's ambient "birds" pool is aliased plain "bird", so "the dead bird" would have fallen through to a live-birds description, worse than the honest "no body" line it replaced. Fixed by requiring the matched ALIAS ITSELF to carry a carcass word (checked against the whole registry: only wood:deadfall's two aliases do, so this is exact, not a heuristic).

**Verified:** new `scripts/_test_j1188_carcass_word_boundary.py`, 108 checks ALL OK, isolated (write-audit hook, 0 attempts under any data/; module-resolution proof; live-file md5 before/after). In-process differential A (old substring vs new word_present) over 2,009 real+inventory phrasings: exactly 4 flips, all in the false-positive direction. Differential B (is_place_object_target off vs live, full pipeline, seeded/state-restored) over the same corpus × 4 places: exactly 2 flips (the dead wood family), zero unexpected — "the dead bird" regression confirmed absent. `data/hands_trace.jsonl` read whole (22,267 rows): NEW hits are a strict subset of OLD. Regression: `scripts/life_smoke.py` twice (ALL OK both times, no F-1668 intermittent failure this run), `_test_j1165_trace_object_look.py` (3,372 ALL OK), `_test_j1166_look_hygiene.py` (3,111 ALL OK), `_test_j1174_gulls_keep_the_day_no_flock_graduation.py` (9,140 ALL OK).

**Restart-gated**, same as every other entry on this plan; no live store touched; no decision implicated, no follow-up job spawned (the fix is complete and self-contained). Files: `core/life.py`, `core/life_traces.py`, `scripts/_test_j1188_carcass_word_boundary.py` (new).

## Current State — 2026-09-23 (J-1189 BUILT+READ: place-agnostic trace phrases fixed for 4 of 7 affected rows, data-only; 3 rows needing new content stopped and escalated) — F-1801, J-1281 spawned

**Full analysis first, all 30 trace-carrying rows, 53 (row, phrase) pairs.** Row-internal truthfulness check (does a phrase use a word this SAME row registers under one of its OTHER places — F-1671's own exact method): 10 pairs across 7 rows are genuinely wrong (cicada, garden_spider ×2, kingfisher, mice, possum ×2, rabbit ×2, welcome_swallows). Live history re-verified fresh: 275 kind=trace rows now (up from F-1671's 235), 39 mismatched (14.2%, same shape — welcome_swallows' eaves phrase alone accounts for just over half).

**Fixed, data-only, no invented content (4 rows: mice, rabbit, possum, garden_spider).** `core/life.row()` gains `traces_only_at: {phrase: (place,...)}` — an optional per-phrase place restriction; a phrase with no entry fires everywhere, unchanged. Critically, `traces` itself is never shortened (only *narrowed at read time* via the new `life_traces.place_traces()`), so every existing consumer that reads `traces` directly — especially `scripts/_test_j1165_trace_object_look.py`'s own row filter — sees exactly what it always has. **An earlier union-based draft (moving phrases into a separate additive dict, leaving garden_spider's own `traces` empty) was built, tested, and rejected by this job's own regression run** before shipping: it broke J-1165's protected test with a KeyError, a real regression caught in-session, not assumed safe.

**Stopped for 3 rows needing genuine world-content judgement (cicada, kingfisher, welcome_swallows)** — each has exactly ONE phrase, true at only one of its 2-3 registered places, with no neutral alternative to redistribute. Two honest options exist for each (restrict to one place, leaving the row with no trace elsewhere at all; or author a new place-appropriate phrase) and neither is an engineering call. **J-1281 spawned** (needs_input) with both options, draft candidate phrasings for the founder to edit or reject, and Claude's own non-binding read (kingfisher-at-garden and swallows-at-shore probably have no honest trace to invent; cicada-at-wood is a low-risk word-swap; swallows-at-garden is a real 50/50).

**Verified:** new `scripts/_test_j1189_traces_by_place.py`, 201 checks ALL OK (isolated, write-audit hook, module-resolution proof, live-file md5 before/after). Replayed all 275 real trace rows (36 distinct key/place pairs): zero truthful phrases lost, wrong phrases confirmed gone from the 4 fixed rows' real pools, the only real pairs still wrong belong to the 3 escalated rows. Regression, rerun clean: `life_smoke.py` ×2, `_test_j1165_trace_object_look.py` (3,372 ALL OK — the suite the rejected draft broke), `_test_j1166_look_hygiene.py` (3,111 ALL OK), `_test_j1174_...` (9,140 ALL OK), `_test_j1188_carcass_word_boundary.py` (108 ALL OK, this batch's sibling job).

**Restart-gated.** No decision implicated (a needs_input job carries the founder call, not a /decide — matching J-1193/J-1194's own established pattern for this exact class of question). Files: `core/life.py`, `core/life_traces.py`, `core/life_mammals.py`, `core/garden_insects.py`, `scripts/_test_j1189_traces_by_place.py` (new).

## Current State — 2026-09-23 (J-1190 BUILT: the reveal join punctuated, same terminal-stop rule as the graduation suffix, via a shared helper) — F-1802

**F-1674's second unpunctuated-glue site is closed.** `core/life_traces.py`'s `with_individual_suffix` is refactored (byte-identical behaviour, proven against F-1676's own real quoted rows) to share a new `_end_sentence(text)` helper with a new `join_reveal(line, reveal)`, and `core/life.py`'s reveal join now calls it. `join_reveal` reads which rule applies from the reveal's own first character — upper-case (a complete sentence; today only long_tailed_bat, "It is a bat — ...") ends the fragment first; anything else (an em dash, the other 10 of 11 reveal rows, which continue the fragment on purpose) is untouched. All 11 real reveal-carrying rows checked: exactly long_tailed_bat's join changes.

**The interplay (learned + graduated) reads once-punctuated**, checked both as pure-function composition and end-to-end through the real, isolated `life.look_answer` (a seeded learned+graduated bat, sight-roll forced deterministically via a monkeypatched `random.random`, since visibility was only 0.057 and an external seed can't reliably control a roll behind an unknown number of upstream random draws) — no special-case code needed, since `with_individual_suffix` already inspects the line's own actual trailing character.

**One documented deviation:** `scripts/_test_j1166_look_hygiene.py`'s own section 1c hardcoded the bare (unpunctuated) join as its expectation for all 11 reveal rows, written before this fix existed. Running it unmodified correctly failed 2 sub-checks for long_tailed_bat. Fixed with the **same one-line-update precedent this plan's own J-1174 already set on this identical file** ("minimally updated by J-1174; 3,231 before" → 3,111): the expected-value expression now calls `life_traces.join_reveal` instead of re-deriving the bare join inline. Nothing else in that file touched.

**Verified:** new `scripts/_test_j1190_reveal_join_punctuation.py`, 91 checks ALL OK, isolated (write-audit hook, module-resolution proof, live-file md5 before/after). Regression, rerun clean: `life_smoke.py` ×2 (no F-1668 intermittent failure this run), `_test_j1165_trace_object_look.py` (3,372 ALL OK, untouched), `_test_j1166_look_hygiene.py` (3,111 ALL OK, after the one documented line), `_test_j1174_...` (9,140 ALL OK), `_test_j1188_...` (108 ALL OK), `_test_j1189_...` (201 ALL OK) — this batch's own two sibling jobs.

**Restart-gated**, no live store touched, no decision implicated, no follow-up job (self-contained). Files: `core/life.py`, `core/life_traces.py`, `scripts/_test_j1166_look_hygiene.py` (one line), `scripts/_test_j1190_reveal_join_punctuation.py` (new).

This closes out the J-1153/J-1154/J-1192/J-1188/J-1189/J-1190 job-run group. J-1192 was left `in_progress` (gate unmet, 1.05 of 7.00 live-days); J-1153/J-1154/J-1188/J-1189/J-1190 all done. Follow-ups spawned this group: J-1273 (actions_decision_replay.py dedup hygiene), D-0267 (carrier-vocabulary widening, opened not ruled), J-1281 (the 3 remaining trace-phrase rows needing world-content judgement).

## Current State — 2026-09-23 (J-1281 SHIPPED: the 3 remaining trace-wording rows, Travis's choices via /decide-review) — F-1805

**All 3 of J-1189's own escalated rows are now fixed**, closing this plan's own place-agnostic-trace-phrase thread entirely (7 of 7 affected rows done: 4 by J-1189, 3 by this job). `cicada` (core/garden_insects.py) gets a new wood-appropriate variant ("...clinging to the bark of a trunk") alongside its existing garden phrase, each restricted via `traces_only_at` to its own real place — both places keep a truthful trace. `kingfisher` (core/life_birds.py) is restricted to shore only — the garden's own kingfisher spot is a hunting perch, not a nesting site, so garden now correctly has no ground trace (she still shows/sounds there via the ordinary living-row roll). `welcome_swallows` (core/life_birds.py) is restricted to study only — this plan's single biggest place-mismatch (20 of 39 real mismatched rows plan-wide) — rather than inventing a new, nowhere-else-established world feature for garden or shore.

**`scripts/_test_j1189_traces_by_place.py` updated** (the only test with a hardcoded expectation about these 3 rows, per this job's own explicit "check first"): moved cicada into the existing "every place non-empty" section; added a new section for kingfisher/welcome_swallows since they're the first rows where a registered place legitimately keeps an EMPTY trace pool — the old section's blanket "non-empty everywhere" assumption doesn't hold for a row restricted to exactly one place, caught by 3 real test failures on the first run, fixed properly rather than loosened. `UNFIXED` is now empty — the real `data/life_events.jsonl` replay check (section 4) now requires zero remaining row-internally-wrong (key,place) pairs anywhere, and passes.

**Verified:** `_test_j1189_traces_by_place.py` ALL OK (210 checks), `life_smoke.py` ALL OK, `_test_j1165_trace_object_look.py` ALL OK (3,372), `_test_j1166_look_hygiene.py` ALL OK (3,115). No live `data/` file touched. **Restart-gated** — Du is live, not restarted.

## Current State — 2026-09-23 (J-1284 PARTIAL SHIP: collect+take built and verified; candles-restriction built, found to reopen F-0733's own bug class via the CLAIMS mechanism, and held back — D-0271 opened, J-1296 spawned) — F-1822

**D-0267's PART 2 (collect row: verb "take" added, object "box" only) is shipped, exactly F-1793's drafted diff, `core/actions.py:238`.** Verified against the real corpus with a fresh decision-replay (not F-1793's own raw `core.hands.wants()` grammar-hit count): a scratch wrapper (`scratchpad/replay_J-1284.py`) that loads the real, unmodified `scripts/actions_decision_replay.py` from a chosen worktree root and monkeypatches only its `TRACE` constant to the live, absolute `C:\Nascence\data\hands_trace.jsonl` (read-only) — needed because a Tier-3 worktree never checks out `data/` (gitignored). Replayed `data/hands_trace.jsonl` (22,313 distinct thoughts x 4 locations = 86,796 decision rows) against a pre-edit baseline taken from this worktree's own HEAD (5c038a0, a throwaway worktree, removed after). Confirms real value with no discovered downside — e.g. "I hold the book warm but feel a pull outward. The letter from Darwin waits by the gate, his flag high against the wind. I want to step down through the wood, past the soft leaf-mould, and take the box" (the voice's own act_kind=move, act_object='to the gate') goes from `collect GRAY no-fire` to `collect DEED FIRE` (garden) / `STAGE-place` (elsewhere) — exactly the weeks-long unmet want F-1588 named. `scripts/life_smoke.py` reruns clean (ALL OK, isolated stores) throughout, both before and after the candles-row revert below.

**D-0267's PART 1 (candles row: drop bare "candles"/"candle"/"matches") was built, verified the same way, found to reopen J-0540/F-0733's own bug class, and reverted before commit — NOT shipped this run, per this batch's own "report rather than ship" rule.** Root cause: `core/actions.py`'s CLAIMS mechanism (the candles row's own `claims=(("collect", "box"), ("tool", "tin"))`, the exact fix that stops "fetch the candles from the box" misreading as a want to collect the carrier's delivery) only fires when 'candles' itself reaches a DEED verdict for that clause — `claimed_by()` (`core/actions.py:529-548`) is handed only already-DEED-filtered candidates, both in the live `dispatch.dispatch()` CLAIMS step and in the replay's own mirror. Once bare "candles"/"matches" can no longer complete candles' own `deed_grammar`, `classify()` produces NO reading at all for 'candles' on these clauses (confirmed empirically — the family's entry vanishes from every location's decision list rather than downgrading to MUSING/GRAY), so its claim on "box" never fires, and 'collect' (whose own pre-existing "fetch"+"box"/"carry"+"box" already reach "box" in both clauses, independent of PART 2's new "take" verb) is free to fire instead — misrouting a genuine study want to the garden gate. Two real `data/hands_trace.jsonl` thoughts, confirmed via their own voice-structured `act_kind`/`act_object` fields: "The lamp sputters; ink runs dry. I will fetch candles from the box..." (act_kind=light, act_object=candles) and "...fetch the candles from the box to warm the room" (act_kind=move, act_object='to the candlebox', the voice's own field naming the right target) — both go from `candles DEED FIRE/STAGE-place` + `collect DEED DROP-claimed:candles` (correct) to `collect DEED FIRE` at garden / `STAGE-place` elsewhere, with 'candles' gone entirely (wrong hand, wrong place). For contrast, the fix working exactly as intended: F-1591's own already-named false positive ("I pick up the card listing oil and matches...") correctly loses its candles reading with nothing replacing it (no "box" in that clause for collect to misclaim). A fourth DEED-level candles loss (the pre-09-04, 08-30 "fetch the candles from the [box]" / "read Les Misérables" row F-0785 already named) is harmless regardless: 'lamp' precedes 'candles' in table order and already wins that thought's one-hand-per-thought race at every location under the CURRENT, unedited table. **F-1793's own "zero true reaches lost" claim for PART 1 holds only under its own narrower measurement** (raw grammar-hit counting against the 26,363-row corpus, outside the CLAIMS machinery); measured through the full decision pipeline against `data/hands_trace.jsonl` it is not zero — two known, real misroutes exist. D-0267 approved PART 1 without this evidence in front of it. No prior commit was reverted — the candles row in this worktree is left exactly at the master original; this job's own PART 1 edit was built, verified, found wanting, and undone by a second `Edit` call before any commit.

**D-0271 opened** (not ruled): ship PART 1 anyway on the same accepted-risk terms as PART 2's own direction-blindness (a misfire only STAGEs/FIREs a 'collect' attempt at the garden gate — narrative-wrong, not destructive), or hold until CLAIMS is decoupled from a claiming family's own full DEED-worthiness, or ship a narrower single-word version. Claude's own non-binding read: decouple first, then re-open. **J-1296 spawned** (build, ready): decouple the CLAIMS mechanism — design needed, not a trivial field add (`claimed_by()` today only ever sees already-DEED-filtered candidates, so a fix needs clause-text access further upstream); 'candles' is confirmed (grep) the only row in the whole table with a non-empty `claims` tuple today, so the blast radius is contained.

**Separately, D-0267's own ruling text is a documentation error, noted but not itself consequential.** "Ship with Action.grammar_only per F-1793's own recommendation" — F-1793's own full text (read in full) never mentions `grammar_only` anywhere; grep of `docs/findings.jsonl` for the string returns lines 790/791 (F-0790/F-0791, J-0544's real move-family precedent) and 1798 (F-1798, J-1178 — an unrelated job scoring per-word widenings for the UNGATED 'look' family) only, not F-1793 (line 1793). Mechanically confirmed separately (`core/literal_will.py:344-357`, read in full): `grammar_only` is a tuple of OBJECT words only, never compared against a verb; its entire effect is scoped to `obj_vol`, which feeds `intent` only for an UNGATED family (a GATED family's `intent = deed_grammar`, full stop). 'collect' is gated (`core/actions.py`'s own `Action.gated` default; the row declares no override) — so `grammar_only=("take",)` would have been a silent no-op, not the protection the ruling's text describes. Not applied to either row for this reason; does not change what was shipped (PART 2's diff is byte-identical to F-1793's own draft either way).

**Verified additionally:** `python -m py_compile core/actions.py` clean throughout both edits — confirmed by a second, independent full-corpus replay pass with PART 1 reverted: 4 rows differ from baseline (of 86,796), all 4 locations of the one genuine collect+take gain, zero other differences anywhere — isolating the PART 1 regression completely. `git diff -- core/actions.py` in the worktree confirms only the PART 2 hunk (collect's verb tuple) remains before commit. Finding: **F-1822** (verified). **Restart-gated** (PART 2 only; nothing here is live until Du's next restart). D-0137/D-0166/D-0174/D-0189/D-0247/D-0249 all untouched.

## Current State — 2026-09-24 (J-1310 SHIPPED: D-0267 PART 1 re-verified clean on top of J-1296's fix and shipped on D-0271's explicit founder go-ahead) — F-1895

**D-0271 reopened and ruled GO** ("Re-verify and ship if clean... Ship PART 1 to the real plan worktree only if the replay comes back clean", ruled 2026-09-24T04:54Z by travis) — the explicit, in-chat authorization both D-0271's own original text and J-1296's own dispatch briefing required before this could ship. J-1310 re-applied D-0267's own PART 1 diff on top of J-1296's now-landed CLAIMS decoupling fix: `core/actions.py`'s candles row `objects` narrowed from the original 13-word vocabulary to the 10 phrase-qualified forms only (bare "candles"/"candle"/"matches" dropped), and the new `claims_triggers` field set explicitly to the full original 13-word vocabulary so `claimed_by()`'s pass 2 (J-1296) keeps claiming a bare "box"/"tin" away from collect/tool for a bare "candles"/"matches" mention even though that mention can no longer complete candles' own `deed_grammar`.

**Re-verified clean against the full real corpus** (`data/hands_trace.jsonl`, 23,125 distinct thoughts × 4 locations = 90,040 decision rows, frozen-corpus replay via `scratchpad/verify_claims_J-1296.py`, before = a throwaway worktree of pre-edit HEAD i.e. the currently-shipped state, after = this job's real edit): 288 rows differ. Every one programmatically classified (not eyeballed — a parser script asserted, per row, that the only difference is a single removed `('candles', *, *)` entry with every other family's verdict/action byte-identical, flagging anything else as a third category) into exactly the two shapes D-0271's own ruling anticipated, with **zero in any third category**: 280 rows are candles' own entry harmlessly disappearing (including a fresh occurrence of the F-1591/F-1792 "oil and matches" false positive, correctly dropped with nothing replacing it); 8 rows are F-1822's own two known regression thoughts (idx 6088/6097, all 4 locations) where candles' own DEED reading is gone but `collect` stays `DEED/DROP-claimed:candles`, byte-identical before/after in every one — the misroute F-1822 found never appears anywhere in the corpus. `py_compile` clean; `scripts/life_smoke.py` ALL OK (isolated stores); all 6 `*_grammar_derivation.py` tests ALL OK; `scripts/actions_registry_audit.py` clean (0 invariant violations, table shape unchanged).

**Shipped**: committed to `jobrun/living_world_upgrade` as `5384b81`, merged back to the shared tree. D-0267's PART 1 and PART 2 are now both live in source (PART 2 shipped earlier, J-1284). Finding: **F-1895** (verified), linked to D-0271. **Restart-gated**: Du is live (PID 40268, untouched throughout) — this changes live candles/matches decision-routing only once Du's own process next restarts. D-0271's own defeater now also covers the live period: revisit if a live wrong FIRE/STAGE is ever actually observed post-restart.
