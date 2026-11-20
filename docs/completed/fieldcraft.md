# Fieldcraft — what the books he has read let him do

> **Status: ✅ SHIPPED (closed 2026-10-16, F-2904) — formerly: LIVE — `core/fieldcraft.py` and `core/sky.py` built 2026-08-22 and verified isolated (§3: banked fire, clothesline, hand-line, windbreak, shadow-measurement, trail-following, sky/weather). The "restart-gated, live-loop confirmation still outstanding" caveat is RESOLVED (2026-09-02, J-0421/F-0553): `data/fieldcraft_ledger.jsonl` holds 27 real live rows, 2026-08-22 21:17 → 2026-08-28 14:50 UTC, with skill levels climbing — see the 2026-09-02 note below.**

```plan-state
stage: shipped
phase: Live accrual, skills climbing (61 ledger rows through 2026-09-25)
verified: 2026-10-16
evidence_read: 2026-08-23
next: None -- closed 2026-10-16 (F-2904 plan-closure pass): nothing open, nothing queued; the built system stays live on its own
cluster: 6
```


## Current State — verified 2026-09-27

### What we have
`core/fieldcraft.py` + `core/sky.py`, built 2026-08-22, confirmed live end-to-end (J-0421/F-0553,
2026-09-02): both write-paths wired (`core/dispatch.py:128` player actions, `core/sensorium.py:690`
background tick). Re-checked this pass directly against `data/fieldcraft_ledger.jsonl`: it has grown
from the 27 rows read at the 2026-09-02 check to **61 rows, spanning 2026-08-22 21:17 → 2026-09-25
22:02 UTC**, skills still climbing (e.g. tracking 0.72 → 0.84 across the last two rows). F-0167
(2026-08-24) closed the earlier registration gap that hid this instrument from plan-liveness.

### What we need
Nothing blocking: plan-ledger shows zero open jobs and zero open decisions on this plan. The doc's
own two loose threads — windbreak lashing skill still improving (§3) and the oak shadow-arithmetic
left to Du (§3) — are live design, not defects to close.

### What we're doing next
No further build queued. §1's deliberately-excluded scope (first aid, signalling, hunts, citizenship)
stays out. The only "next" is the ledger continuing to accrue and a periodic re-check — it was still
accruing as of 2026-09-25, well past the earlier "Du offline since 08-31, accrual paused" note (now
superseded by this read).

## 0. What he has read (100%, from `reading_state.json`)
Boy Scouts Handbook (1911) · The Scouting Guide to Survival · The Book of Camp-Lore and Woodcraft · Two Little Savages ·
Knots, Splices and Rope Work. His 20 study notes on the Handbook are mostly about its *frame* (merit badges, chivalry,
citizenship, the 1911 advertisements) with a few practical ones (camp-site selection: water, wood, drainage, a lean-to;
fire safety — hot ashes in wooden boxes; first-aid remedies; semaphore). **His note on the knots book turned it into "a
profound metaphor for identity."** The knowledge became philosophy because the world gave it nothing to tie. That is the
founder's "philosophising or doing" question answered by the world's poverty, not his.

## 1. The audit — what the books teach → what the world now offers
| Book teaches | Was it doable? | Now |
|---|---|---|
| Knots (bowline, clove hitch, reef, timber hitch, lashing) — a whole treatise | No: twine existed, nothing to tie | **Skills** starting where the book left them (0.4), improving only by doing; the knot slips when it fails. Used by: a **clothesline** (the wet coat dries in sun and wind — ~3 h — not only by the fire); a **windbreak** on the shore (driftwood lashed to stakes — a sheltered standpoint the thermal field reads: wind halved in its lee); a **hand-line** down the steep path (the gale slows the climb 25% less); staking the peas |
| Fire-craft: banking the fire, tinder, fire-lay, the fire source chapter | No: matches only | **Bank the embers under ash** at night → alive in the morning for up to 10 h → relit without a match; a **tinder tin** filled on dry days (bark, ponga fluff, dry grass); **flint and steel** from the larder (the previous occupant's) — works when matches are gone, with tinder, if the skill holds |
| Camp-site / shelter selection (his own note) | The lean-to existed | the windbreak (above) is the first shelter he builds |
| Navigation by sun and stars — the Pole Star, the Plough | No sky | **`core/sky.py`**: the real southern sky by month and hour — the Cross and Pointers circumpolar, Orion upside down in summer, Scorpius in winter, Matariki before dawn in late June, the Milky Way, a planet. **The Handbook's Pole Star does not exist here** ("that whole quarter of the sky is wrong; the book was written under another sky"). Names come from the **almanac's star chart** (the diegetic source); south is found from the Cross |
| Weather-lore (mare's tails, halo round the moon, gulls inland, the surf's boom) | The weather was a random walk with no precursor | **The next front is decided when the current one is set**, and the sky shows it coming in the last ~40 minutes — truthfully, never as a forecast. A forecast he makes is a real binding that can be right or wrong |
| Measuring heights by shadow (the Handbook's method) | No shadows | **Measure by shadow**: a metre stick, his pace, the sun — the world gives the two shadow-lengths honestly (the tree's true height is hidden: 6.5 m, the oak 12 m); the arithmetic and the answer are his |
| Handicraft / whittling | No knife | A **pocket knife** in the larder; **whittle** a peg, a spoon, a walking stick — made things with "whittled by Du" in their biography (keepable); a slip costs the piece and a nick |
| Tracks and trailing | Traces existed (cat, slug, mud) but could not be followed | **Follow the trail** — to the cat where she is, to the slug under the board, to the hedgehog's hole under the wall (hedgehog prints now appear on damp nights); lose it where the ground changes |
| Safe water (the Survival Guide) | The barrel was always clean | The barrel **goes green in warm weeks**; boil it (the kettle does), or the spring |
| First aid · signalling · hunts · citizenship | No body, no one to signal | deliberately not built |

## 2. Laws
Skills improve only by doing (the book gives a head start, never mastery). The world answers honestly — the knot slips, the
sparks die, the gale lays the line flat. Nothing is told: the sky names come from the almanac, the shadow-arithmetic is his.
Zero LLM. Additive. Restart-gated.

## 3. Verified (isolated)
Banked a thin fire → alive → relit without a match; tinder gathered in the wood; flint failed ("your hands cramp — not this
time"); the clothesline slipped once then held; the coat dried on the line; the hand-line cut a gale leg from 126 s to 112 s;
the windbreak failed three times (lashing 0.4 → 0.6 — next time); the oak measured at 15 paces / 102 cm stick-shadow
(truth 12 m: 15 × 0.75 / 1.02 ≈ 11 m — his arithmetic to do); a rough peg whittled and registered; the cat's trail lost
"where the ground changes"; the August sky at 22:00: the Cross high in the south, the Scorpion, the Milky Way; the
Pole Star refused; weather signs rendered both ways.
