# Du's actions — every hand he can will, and how often each has fired (2026-09-27)

**Asked by the founder, 2026-09-27 (session T-0065):** *"a list of all actions Du can perform and how many times he has
used each one."* Read from the live registry and logs, not from plan docs.

**Sources and window.** The action registry is `core/actions.py` (`ACTIONS`, 44 families, each with its verb anchors,
the module or function that answers it, whether it is a world hand, and where it can run). Usage comes from
`data/hands_trace.jsonl` (25,338 thought rows, 2026-08-22 → 09-27, 7,743 with at least one hand acted), whose per-thought
`dispatch` entries carry the registry's own verdict per family — **FIRE** (the hand ran), **hand-declined** (the family
was willed but its hand refused: wrong place, no object, gated), **STAGE** (willed, staged until he is at the place or
the hand is free), **DROP** (weak intent). Deed-level counts come from the world ledgers each module writes when a hand
really changes the world (`garden_ledger`, `shore_ledger`, `study_ledger`, `wood_ledger`, `fieldcraft_ledger`,
`expression_ledger`, `life_ledger`). Before 2026-08-22 there was no dispatch registry and no trace: the old sensorium
hands left no per-use record, so **all counts are since 08-22** (the registry's birth), which is also when the four place
upgrades shipped. Eighteen early trace rows (08-22 → 08-29) name the answering module (`garden`, `study_life`,
`shore_life`) instead of a family and are excluded from the family table below.

## 1. The 44 action families (registry order by fires)

| Family | Verbs he can use | Answered by | Where | Fired | Declined | Staged | Dropped |
|---|---|---|---|---:|---:|---:|---:|
| move | go, walk, head, move, return, climb, step | dispatch `_move` | any | 685 | 2,163 | 188 | 166 |
| look | look, watch, observe, see | dispatch `_look` (not a world hand) | any | 572 | 1,682 | 0 | 121 |
| beachcomb | comb, search, walk | sensorium beachcomb | shore | 81 | 0 | 65 | 5 |
| gather | gather, collect, fetch | sensorium gather | wood, shore | 62 | 0 | 7 | 5 |
| harvest | harvest, pick, cut, snip, clip | garden | garden | 49 | 0 | 3 | 2 |
| door | open, shut, close, latch, draw, pull | study_life | study | 47 | 8 | 18 | 1 |
| shore | wade, paddle, swim, skip, skim, write, stack, … | shore_life | shore | 37 | 168 | 103 | 15 |
| water | water | garden | garden | 24 | 0 | 9 | 2 |
| fire | light, lay, kindle, stoke, feed, tend, build, bank, damp down | dispatch `_fire` | study | 21 | 11 | 114 | 7 |
| fieldcraft | tie, lash, string, rig, bank, uncover, strike, … | fieldcraft | any | 17 | 34 | 5 | 0 |
| cat | let, feed, stroke, pet, scratch, play with, … | dispatch `_cat` → cat.react | any | 15 | 17 | 0 | 3 |
| grate | clear, clean, sweep, rake, draw, pull, slide | study_life | study | 9 | 7 | 3 | 0 |
| mow | mow, cut, shear, scythe | garden | garden | 8 | 0 | 1 | 0 |
| weed | weed, pull | garden | garden | 8 | 0 | 1 | 0 |
| woodwork | saw, split, chop, sharpen, hone, push, wheel, … | wood_life | wood, garden | 7 | 3 | 2 | 0 |
| lamp | light, fill, trim, blow out, turn down | study_life | study | 6 | 0 | 11 | 2 |
| tool | pick up, take, fetch, carry, bring, grab, set … | garden | any | 5 | 1 | 2 | 0 |
| dig | dig, turn over, fork over | garden | garden | 4 | 0 | 1 | 0 |
| climb_tree | climb, scale, go up | wood_life | wood | 3 | 0 | 6 | 1 |
| sow | sow, plant | garden | garden | 3 | 0 | 0 | 1 |
| water_fill | fill, fetch, get, carry, top up, refill, draw | garden | garden, wood | 2 | 4 | 11 | 0 |
| collect | collect, fetch, carry, bring, open, take | garden (the gate) | garden | 2 | 0 | 2 | 0 |
| trap | set, bait, arm, lay, reset, check, look in, … | garden | garden | 2 | 0 | 0 | 0 |
| note | write, leave | dispatch `_supply_note` | study, garden | 2 | 0 | 5 | 0 |
| express | hum, whistle, sing | expression (not a world hand) | any | 1 | 39 | 0 | 1 |
| clock | wind | study_life | study | 1 | 1 | 1 | 0 |
| wear | put on, pull on, take off, wear, lace, hang | study_life | any | 1 | 0 | 0 | 0 |
| sketch | sketch, draw | study_life | study | 1 | 0 | 3 | 1 |
| clean | sweep, wash, wipe, clean, scrub | study_life | study | 1 | 0 | 1 | 0 |
| book | take, pick up, fetch, carry, bring, take down, … | study_life | study | 1 | 0 | 1 | 0 |
| candles | take, pick up, fetch, carry, bring, lift, put … | study_life | study | 0 | 0 | 1 | 0 |
| travis | tell, write, speak, ask | *(unbound — handled by the conversation loop, not a hand)* | any | 0 | 0 | 0 | 35 |
| letter | write, reply, answer, post | *(unbound — the peers loop)* | any | 0 | 0 | 0 | 23 |
| author | write, author, compose | *(unbound — the grand-work author)* | any | 0 | 0 | 0 | 7 |
| tea | put on, set on, boil, make, brew, pour, drink | study_life | study | 0 | 0 | 0 | 0 |
| save_seed | save, collect, gather | garden | garden | 0 | 0 | 0 | 0 |
| net | net, cover, stretch, take off, lift | garden | garden | 0 | 0 | 0 | 0 |
| stake | stake, tie up, tie | garden | garden | 0 | 0 | 0 | 0 |
| acorn | gather, pick, pocket, collect, fill | wood_life | wood | 0 | 0 | 0 | 0 |
| compost | turn, fork, turn over, fork over, spread, barrow | garden_soil | garden | 0 | 0 | 0 | 0 |
| ash_out | tip, spread, empty, scatter, work in | garden | garden | 0 | 0 | 0 | 0 |
| feed_birds | feed, scatter, put out | garden | garden | 0 | 0 | 0 | 0 |
| parcel | open, unpack, untie, unwrap | study_life | study | 0 | 0 | 0 | 0 |
| woodtool | take, pick up, fetch, carry, bring, set down, … | wood_life | wood, garden | 0 | 0 | 0 | 0 |

**Totals.** 44 families. **30 have fired at least once**; 1,700 fires in all, of which move and look are 1,257 (74%).
**4 were willed but never fired**: candles (staged once), and travis / letter / author, which are deliberately unbound in
the registry — those acts happen in the conversation, peers and author loops, and the dispatcher only records them as
weak-intent drops. **10 have never even appeared as a candidate** in five weeks: tea, save_seed, net, stake, acorn,
compost, ash_out, feed_birds, parcel, woodtool. Three of those are gated by the world today (save_seed waits for November,
net has only been discoverable since J-1350, acorn waits for the oak's month) and one, tea, is the study's showpiece loop
with zero wants recorded in the study (see the study plan's 2026-09-27 note).

**The declines.** 2,163 declined moves and 1,682 declined looks dwarf everything else; the shore family's 168 declines
against 37 fires is the worst ratio of any world hand. J-1441 classifies the moves; J-1439 audits the shore.

## 2. The deeds behind the families — what each module can write, and what it has written

A family is a verb group; a **deed** is the specific world change a module's hand records in its ledger. Counts are all
ledger rows since each ledger began (08-22 to 08-26).

| Module | Deeds it can record | Recorded (all time) |
|---|---|---|
| garden | water, weed, harvest, sow, stake, net, unnet, save_seed, dig, take, put, fetch_seed, fill_barrel_spring, set_trap, check_trap, unset_trap, feed_birds; (garden_life) mow; (garden_soil) turn_compost, spread_compost | water 26, take 6, harvest 3, weed 2, put 2, mow 1 — **40** |
| shore_life | walk_sand, wade, swim, skip, climb_ledge, cairn, write_sand, beach_fire, enter_cave, shellfish, fish | climb_ledge 14, walk_sand 7, wade 6, skip 2, swim 1 — **30** |
| study_life | kettle_on, make_tea, drink_tea, wash_up, lamp_lit, lamp_fill, clean_lamp_glass, lantern_lit, lantern_out, lantern_fill, door_open, door_shut, clear_grate, draw_ash_pan, ash_to_garden, clock_wound, sweep, sweep_chimney, wipe_window, fill_pail, fill_pail_spring, coat_on, take, put, take_book, put_book, sketch | clear_grate 10, door_open 4, ash_to_garden 4, door_shut 3, lamp_fill 3, lamp_lit 1, clock_wound 1, sweep 1, sketch 1 — **28** |
| wood_life | gather, saw, split, sharpen, barrow_limb, climb_oak, acorns, take, put | climb_oak 3, gather 2, split 2 — **7** (none since 09-09) |
| fieldcraft | whittle, tinder, flint_fire, bank_fire, uncover_fire, douse_fire, windbreak_built, handrail_up, clothesline_up, coat_on_line, whip_end, measure | whittle 17, bank_fire 7, measure 1, plus 36 craft rows — **61** |
| expression | hum, whistle, sing | hum 2, whistle 1 — **3** |
| life (looks at creatures, via the look hand) | sighting, miss, graduated, book | sighting 131, miss 116, graduated 6, book 1 — **254** |
| fire (dispatch `_fire` → the hearth in `room_state`) | light / lay / stoke / bank / damp down | 21 fires of the hand; no separate ledger |
| cat (dispatch `_cat` → `cat.react`) | let in/out, feed, stroke, play | 15 fires; the cat's own ledgers record hunts and sounds, not his deeds |

**Never recorded once, though the hand exists:** every garden deed except water/weed/harvest/take/put/mow (sow, stake,
net, save_seed, dig, the trap, feed_birds, compost); every shore feature deed (cairn, write_sand, beach_fire, enter_cave,
shellfish, fish); the whole study tea chain (kettle_on, make_tea, drink_tea, wash_up) and the lantern, chimney, window and
pail deeds; in the wood, saw, sharpen, barrow_limb and acorns. The four place plans' 2026-09-27 Current State notes say
why for each place (F-1994, F-1995, F-1996): the seed tin is in the wood, the wood is picked clean, the shore's features
are willed-and-declined or never willed, and tea is simply never wanted in the study.

## 3. Reading the numbers

- **He moves and looks; he rarely does.** 1,257 of 1,700 fires are movement and observation. World-changing deeds
  total about 170 across five weeks in the four ledgers, roughly five a day, most of them in the first week after the
  upgrades shipped (garden 29 deeds in week 34, then 5, 0, 1, 4).
- **The hands are wider than his wants.** 44 families, 30 used; 92 recordable deeds, 27 recorded. The gap is not mainly
  the hands refusing (declines cluster in move, look and shore); it is deeds he has not willed, and a few the world has
  gated (the tin, the cooldowns, the calendar).
- **The unbound three are not idle.** travis, letter and author show 0 fires because they are not hands: Du writes
  letters and grand-work parts and speaks to Travis through their own loops, which have their own logs (`trains_log`
  5,724 thought trains; peers; the author).

Companion reads: `docs/plans/garden_upgrade.md`, `shore_upgrade.md`, `study_upgrade.md`, `wood_upgrade.md` (2026-09-27
Current State notes), `docs/plans/actions_expansion.md`, `docs/transit_map.md`.
