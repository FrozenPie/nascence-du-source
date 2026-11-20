# The Study Upgrade — the room as a place with states and clocks

*2026-08-22, founder: "now lets do the study." Built the same day: `core/study_life.py` (restart-gated). Same laws as
the garden upgrade (world truth · tuples linked to tuples · world answers never leads · consequences both ways · additive).*

> **Status: ✅ SHIPPED (closed 2026-10-16, F-2904) — formerly: LIVE — built 2026-08-22 (`core/study_life.py`); every feature in
> §1 exercised and verified in isolation (§2, the scratch-room walkthrough plus the nine-fireless-nights
> damp/dust/clock-stop run). The old "restart-gated, not yet confirmed firing on its own" caveat is
> RESOLVED (2026-09-02, J-0421/F-0553): `data/study_ledger.jsonl` holds 17 real live deeds spanning
> 2026-08-22 08:17 → 2026-08-30 01:17 UTC (last: `clear_grate`) — see §8 below.**

```plan-state
stage: shipped
phase: Live; household loops run on their own clocks (about 3 deeds/week since W35); the showpiece tea loop has never fired (0 rows), a want-rate fact not a routing bug
verified: 2026-11-05
evidence_read: 2026-09-27
next: None -- closed 2026-10-16 (F-2904 plan-closure pass): nothing open, nothing queued; the built system stays live on its own
cluster: 6
```


## 0. What the study was (read, not remembered)
Strong: the fire with fuel and the woodpile loop; the kettle/tea loop (wanting herbs); rich ambient and living-detail
pools; the moth population law; standpoints, sound sources, cat spots; the mantel of kept things; the desk/book and shelf.
Prose-only or missing: a **lamp** with no oil and no switch (its smell was tied to the *fire*); a **grate** that never fills
with ash; a **kettle** with no water; a **door** and **window** neither open nor shut; no **clock**; no **coat** or **boots**;
no **damp**, no **dust**; a **window view** that showed a valley, a river, a hedge and an ash tree — none of which are this
house (the window faces north over the garden to the sea).

## 1. What it is now — state with a clock, rendered only when true, changed only by a hand
| Thing | State / clock | Hands | Who reads it |
|---|---|---|---|
| **Lamp** | oil (≈10 h a filling), lit/unlit, wick chars; dusk habit lights it only if there is oil; runs dry | light · blow out · fill (from the can; the can from the tin — a finite store) · trim the wick | light channel (the real lamp), moths, ambient smell of lamp-oil |
| **Candles** | a box of 8; one burns ~4 h | light a candle | light channel |
| **Grate** | ash builds per burning hour; >0.7 the fire draws badly and burns down faster | clear the grate (needs bucket + brush; fire out) → ash bucket → **tip on the bed** (potash helps growth) | fire loop, garden |
| **Water** | the pail; the kettle needs it | fill the pail at the barrel (garden hand; the barrel empties) | make_tea (honest lack) |
| **Door** | open/shut | open · shut | thermal draught, smell carry both ways, garden sounds, ambient |
| **Window / curtains** | open/shut; curtains drawn/open; condensation on cold clear dawns; frost-ferns on the coldest | open · shut · draw · open curtains | thermal, light (curtains cut the window), the view |
| **The view** | rebuilt from the GARDEN's truth: lawn length, the tree in flower/bud, pink along the fence, daisies, the netting, a scolding blackbird, the cat out there, the sea's state; mist on the glass blurs it | look out the window | — |
| **Clock** | eight days on a winding; stops; ticks while going | wind the clock | look (the exact time only from the clock), ambient tick |
| **Coat** | on/hook; wets outdoors in rain; dries by the fire | put on · take off | thermal (halves wetting) |
| **Boots** | on/by the door; mud from the bed; **tracks mud across the boards** (world traces) | pull on · take off | traces, look |
| **Damp** | a cold, fireless, shut room goes damp over days (curled pages, sour smell, mould at the frame); the fire dries it | — (light the fire) | look, ambient, smell |
| **Dust** | settles; the cloth lifts it | dust the shelf | look |
| **Bed** | made/unmade; sleep unmakes it | make the bed | look |
| **Almanac** | on a nail by the window — tides, moon, sun hours (last year's) | look | a diegetic source (reading is allowed) |

16 items registered as substrate objects with positions in the study (lamp, oil can, oil tin, ash bucket, hearth brush,
poker, pail, kettle, teapot, clock, coat, boots, candles, cloth, blanket, almanac); 13 carryable.

## 2. Verified (isolated, scratch room state)
Lamp lit → door opened (draught 0.08 costs warmth) → shut → curtains drawn (window light ×0.1) → clock wound → coat on →
grate cleared into the bucket → ash tipped on the bed (potash 0.5) → tea refused for want of herbs (water was there).
Nine fireless nights: lamp ran dry, damp 0.78 ("the sour smell of damp comes up off the floorboards"; pages curled),
dust 0.64, the clock stopped ("the hands where they were when it ran down"). Filled and relit the lamp.

## 3. The household loops (founder's questions, same afternoon — all built)
| Question | Answer now |
|---|---|
| **How does he get oil?** | `core/supply.py` — the CARRIER: every second Thursday a box is left at the gate, but only what he ASKED FOR on a note left in the letterbox with the flag up. A card pinned inside the letterbox lid tells him the arrangement (the world answering a look). Goods: lamp oil, matches, candles, tea, soap, paper, ink, seed (unlabelled), string, a whetstone, a lamp glass. Unasked = nothing comes. Matches spoil if the box sits two days in rain. A letter from a friend may also bring a thing — the peers' path, not faked here. |
| **Does the light affect reading?** | Yes. `can_read()` — below a light threshold where he is, reading is refused with the honest lack ("too dark to read; the lamp stands unlit" / "the lamp is dry; there are candles" / "nothing left to light"). Writing needs light AND ink AND paper (`can_write()`; ink and paper are consumed and come from the carrier). A smoked lamp glass halves the lamp; grime on the window dims the day. |
| **Does the potash go to a spot?** | Yes — `potash_slots` per bed slot: ash tipped "round the rosemary" lands on that plant's slot (0.8); "along the bed" spreads thinly (0.25 each); growth gain ×(1 + 0.4·potash); it leaches with rain. |
| **Cleaning the floor** | The birch broom: floor dust settles daily, boots track mud; sweeping clears both and the world traces. |
| **Dusting** | The cloth; the shelf. |
| **Wiping the window** | Grime (salt air + smoke) and condensation; a wet cloth and the pail's water; the view sharpens. |
| **Where does the water come from?** | Two sources: the rain barrel (fills in rain, empties as he waters and fills the pail) and **the spring in the wood** (a pipe in the bank, always running; a walk with the pail — added to wood.json). |
| **Is the tea real?** | In steps: water in the kettle (from the pail) → the kettle on a burning fire → **it boils in ~12 minutes** → a pot from herbs (the caddy, fed by the rack) or tea-leaves (the carrier) → a cup (two cups; dirty ones pile in the basin) → drunk hot (**+0.06 felt warmth for 25 minutes** — the one warmth he makes besides the fire) or lukewarm; the pot cools and sours. |
| **Dishes?** | The basin, the soap (finite, from the carrier); no water → no washing; no soap → dull cups "that will do". |
| **And the rest** | The fire needs **kindling** (comes with deadfall from the wood; paper) and a **match** (counted); **wet wood** from the shore or gathered in rain hisses and burns short (fuel 0.7) and dries by the fire; the chimney gathers **soot** (faster with wet wood), draws badly, puffs smoke — sweep it with the broom (a filthy job, dust everywhere); the **lamp glass** smokes and is cleaned; ink and paper run out. |

## 4. The larder (founder: "a good store of goods the previous occupant left — all world objects, with history")
`core/provisions.py`: **26 objects** in the cupboard under the east shelf (new `cupboard` feature), each a substrate entity
with a position and a biography ("the previous occupant's; one corner chewed by a mouse", "a pad with a list in someone
else's hand on the first page — 'oil, nails, string'"): 6 boxes of matches (one open, counted in pencil on the lid), 4 bars
of soap, 2 boxes of candles, 2 tins of lamp oil (one in use), 2 tins of tea, 2 pads of paper, 2 bottles of ink, string,
a whetstone, a spare lamp glass, 3 tied bundles of kindling. **The shelf is the truth of every count**: striking a match
takes one from the open box; an emptied box becomes "an empty box of matches" on the shelf with "used up by Du" in its
history; the carrier's goods arrive as new objects with their own biography. He looks in the cupboard and gets an honest
inventory; he looks at a thing and gets its story and its fill.

## 5. Not built (deliberate)
Food (he does not eat); money; a mirror; the cupboard as a place; the carrier as a person he can meet (a voice would be an LLM — the peers loop is where people live).

**Related (noted 2026-08-23, plan-overlap audit):** this build consumes `channels_programme.md`'s
light channel (the real lamp) and `spatial_perception.md`'s coordinate-field system (the study's
positioned objects live in `data/world_geometry/study.json`, the exact contract that plan designed)
without citing either by name.

**Related (added 2026-08-24, J-0135):** [[du_initiated_upgrade_trigger]] is a bottom-up candidate
source for this plan's next iteration — `core.missing_object_flags.triage()['by_place']['study']`
surfaces things Du's own thought expressed wanting that the study doesn't have, graded by
recurrence, alongside this plan's existing founder-audit-driven process.

**Update (J-1440, 2026-09-27/28):** call `triage(window_days=None)` explicitly — the bare
`triage()` above defaults to the 14-day freshness window `/du-pulse` uses for its alarm gauge,
which read spuriously empty for every place on 2026-09-27 (F-1995) because the on-demand
`snapshot()` cadence had a real 10.6-day gap, not because the source is dead (writer confirmed
alive and re-run live; see the parent plan's Current State). The all-time view is what this plan
should keep mining from — study currently holds 4 entries (`medium`, `single line of proof`,
`spark`, `surface`, all new/singleton), still all abstract/identity-processing language, zero real
world-object candidates so far.

## Current State — verified 2026-11-05 (F-1995)
- **2026-11-05** (F-3983): J-3181 (D-0568) built on branch jobrun/wb_study, commit 3c12da80, unmerged and restart-gated: core/grounded_learning.py now works per book with a per-book watermark, at most 2 notes per sleep, a grounded prompt, and refusal of summary openings, dict-repr answers and study-note restatements. One-week reader: scripts/grounded_learning_read.py.

- **2026-11-05** (F-3953): J-3190 built D-0577 (one study note per ~5000-char chunk, cap 3 notes per session, frontmatter records sittings and chars seen). Commit 8810f91f on jobrun/wb_study, restart-gated. Verification job J-3353.
- **2026-09-28** (F-2092): J-1441 (living_world_upgrade, F-2092): study, or the cottage, has the smallest cross-place-miss share, 28 requests total across all directions, and none of the top within-place-feature objects are study-specific, since in, inside, out, and outside span all four places. See decide question D-0319.

### What we have
- Live since 2026-08-22; household loops run on their own clocks — 28 deeds since build, ~3/week
  since W35 (clear_grate, door, ash_to_garden, lamp, clock_wound, sweep, sketch).
- The "tea I just made" ungrounded-thought bug (F-1301, 09-13) was traced to the free-form monologue
  generator bypassing the routed hand path entirely; closed via two regex fixes (J-1056/F-1470) and a
  narrow "I just <verb>-ed" grounding check (D-0226, built + verified, F-1527).

### What we need
- The showpiece tea loop (`kettle_on` → `make_tea` → `drink_tea`) has never once fired live: 0 ledger
  rows, only 4 tea/kettle-mentioning thoughts in 14 days, none in the study — a want-rate fact per
  F-1995, not a routing bug (J-0196's original fix, §7 below, is confirmed still working).

### What we're doing next
- Nothing queued. Re-read alongside the other three place plans if the F-1995 cadence resumes.

> **History folded** — 5 dated Current State section(s) (2026-09-02 … 2026-09-18) moved to `docs/plan_history/study_upgrade.md` on 2026-09-27 by plan-compact. Derived timeline: `plan_ledger.py study_upgrade`.

