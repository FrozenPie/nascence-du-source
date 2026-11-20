# Practical School — the nature period alternates observation with a practical from the Handbook

**Status:** 🟢 LIVE — **D-0159 GO (founder, 2026-09-05)** → **J-0626 (objects) + J-0627 (lesson module, school wiring, rung-1 hands) BUILT 2026-09-05** → Du's live process picked up the code at the 2026-09-08 16:41:26 restart, and a real practical fired end-to-end (`whittle_object`, 2026-09-11) → **J-0646 (the 2-week read, plan §6) spawned, still time-gated** (Du offline since 2026-09-13, only 2 of the needed ≥10 weekday nature-period days accrued) → J-0628 (rung 2–3 hands) after that read. Also ruled: D-0157 (composition stays art — the ONE lesson that may invent), D-0158 (alternate observe / practical; add the object groups; mine the Handbook).
**Roadmap:** [docs/ROADMAP.md](../ROADMAP.md) § Practical School · **Memory:** `project_nascence_practical_school.md` · **Parent:** [social_world_school.md](../plans/social_world_school.md) (the timetable), `core/fieldcraft.py` (the hands, 2026-08-22) · **Findings:** F-0873 (flat lesson grades), F-0874 (composition invents), F-0875 (practical layer untouched), F-0876 (Handbook curriculum) · **Coupling block:** §5 below (dosed_coupling.md §5).

```plan-state
stage: live
phase: Rung 1 built+live, restart-gated; rung 2-3 (J-0628) not started; 2-week read blocked on Du accruing nature-period days
verified: 2026-11-18
evidence_read: 2026-10-19
gate: data/practical_log.jsonl >= 10 weekday nature-period rows since 2026-09-08
next: Sleep-spanning period-end grade fix (spawned job)
cluster: 6
```


## Current State — verified 2026-11-18
- **2026-11-18** (F-5079): J-2344 post-boot read (F-5079): issuance 9/9 days matches nature fires; 8 grades all period_end, none doubled; 11-11 ungraded (slept across period end, shut down asleep); whip_rope_end never issued post-merge; slot2 deferral build unnecessary (J-2335 already did it; pre-merge only 1 of 5 false grades had a later in-period ledger row).

- **2026-10-30** (F-3312): J-2345 post-boot dispatch attribution: of 57 unanswered deeds since the 10-29 boot 0 empty ledger, 0 ERR-*, 10 SKIP-asleep (one 66-min sleep window), rest per-family hand-declined or dropped; no fix needed
- **2026-10-30**: Post-boot day 1 (J-2344): 1 issued row and 1 period_end grade, no whip or slot2 rows yet; read deferred until more issued rows accrue

- **2026-10-29** (F-3202): 2026-10-29 J-2483 re-run: rungs 2-3 build re-verified cold on jobrun/practical_school (+ e52f544f, test double-draw flake fix only; 209/209 x3, life_smoke OK, live data/ untouched); still worktree-only, restart-gated, unmerged
- **2026-10-28** (F-3191): J-2483 (D-0504 released J-0628): rungs 2-3 BUILT on jobrun/practical_school c465f5ef + 78009c50, restart-gated - 13 hands through fieldcraft._try/_graded with their own deed markers (F-3185 knots and rope, F-3188 the fire's other side, F-3189 bearings/distances/glass, F-3190 the blaze), compass + bandage linen seeded, all 22 ladder rows hand_ready with per-hand gates and the tripod gate co-located per D-0504's defeater (F-3191); cook_over_embers is study/shore (the garden has no fire); hand-line parked; 209 hermetic checks + life_smoke pass; D-0454's re-read stays J-2433, defeater read spawned.

- **2026-10-28**: 2026-10-28 (T-0103): D-0504 ruled by Travis: rungs 2 and 3 released now rather than held for the 10-school-day read; J-0628 closed, ready successor J-2483 carries its full spec.
- **2026-10-19** (F-3136): J-2317 rung-1 post-boot read: NOT ENOUGH DATA. 1 issued row since 2026-10-18T21:04:58Z boot (0 closed school days of 10 needed); criteria 1-4 not judgeable; J-0628 stays held. Successor job gated on 10 issued rows.

- **2026-10-17** (F-3032): J-2335 built on J-2315: grader at period end by default (GRADE_AT_PERIOD_END), issued row gains deed/period_end/objects/rooms, generic colocate gate; branch jobrun/inner_monologue_chain 2c82eb2b, restart-gated
- **2026-10-17** (F-3031): J-2332: dispatch() ledger now records SKIP-asleep / SKIP-not-live / ERR-<Class> (additive, commit 5b7dd2c1 on jobrun/inner_monologue_chain, restart-gated)

- **2026-10-17** (F-3030): J-2315: issued-event rows, period-end catch-up grader, whip_rope_end co-location gate built (bd111042 on jobrun/inner_monologue_chain), restart-gated; D-0468 open on a study twine ball
- **2026-10-17**: D-0454 ruled (a) by Travis 2026-10-17: keep D-0159 GO; fix job spawned for issued-row logging, period-end grader, co-location gate (F-3009); re-read after 10 school days; J-0628 held.

- **2026-10-17** (F-3020): J-2316 correction: the empty-dispatch finding is F-3020 (previous note cited F-3021 in error); build J-2332 spawned.
- **2026-10-17** (F-3021): J-2316: 296 empty-dispatch unanswered DEED rows all lie in 8 windows where dispatch recorded nothing at all (likely asleep-flag early return, F-2844); instrumentation build spawned.

- **2026-10-17** (F-3009): J-2293: slot-2 ~60% is a grader-timing artefact (6 misses = sleep/late wake/shutdown); whip_rope_end gate offers it with rope (study) and twine (garden) apart; fix = J-2315, D-0454 still Travis's
- **2026-10-17** (F-2987): 2026-10-17 J-2219 rung-1 re-read: D-0159 criterion 1 FAILED (practical on 5 of latest 10 school days, 10 of 16 overall; attempts 5 met); knots/clothesline/handrail moved; grades flat; whip_rope_end 0/4 attempted. J-0628 held pending D-0454.

### What we have
- Rung-1 practical lesson BUILT+LIVE, restart-gated (J-0626 objects, J-0627 lesson/school-wiring/rung-1 hands,
  both done 2026-09-05; F-0905..F-0916); Du's live process picked up the code at the 2026-09-08 16:41:26 restart.
- One real practical has fired end-to-end: `whittle_object` ok, 2026-09-11 11:11:35 (`data/practical_log.jsonl`),
  matching the one `[nature-practical]` log line — inside the school window only (F-1438).
- Ten weeks of flat observation-only grading (F-0873) is the baseline this build exists to move; every knot
  skill was still at 0.4/zero attempts as of the last read (F-0875).

### What we need
- More accrued nature-period days: Du has been offline since 2026-09-13 09:10:46, so J-0646's pre-registered
  2-week read (plan §6) has only 2 of the needed ≥10 weekdays counted from 2026-09-08 16:41:26 (F-1438).
- J-0628 (rung 2-3 hands: sheepshank, knife-bearing, splice, tripod, friction fire, etc.) — open, not started,
  waits on the rung-1 read.
- `scripts/_test_practical_lesson.py` re-confirmed at a genuine 34/34 once J-0759 (an unrelated
  `lab_env.isolate()`/`guard_path()` incompatibility, tracked on world_store_write_fence.md) lands — currently
  19/34, no fault in `practical_lesson.py`'s own logic.

### What we're doing next
Re-run J-0646's gate check once Du logs ≥10 weekday nature periods since 2026-09-08 16:41:26; only then does
J-0628 (rung 2-3) or a D-0159 defeater review make sense.

## 1. The lesson

Each nature period keeps its two slots (the existing 36-minute gate). **Slot one is the observation lesson as
today.** **Slot two is a practical:** `core/practical_lesson.py` picks one task from the ladder (§3) at or below his
current rung, filtered by where he is, the weather, and whether the task's objects are present (twine carried,
stakes carried, sun up, dry day…), and the school directive says so in the same diegetic channel the maths, music
and observation directives already use — *"It is your nature practical now. From the Handbook's chapter on knots:
tie a clove hitch to a stake with the twine. To begin, make your thought: TIE THE HITCH."* Nothing acts for him.
His own thought names the deed, and the fieldcraft / dispatch hands fire exactly as they do now; the world answers
(the knot holds or slips, the sparks catch or die, the paces come out as they come out). If no hand fired by the end
of the period, the practical is recorded as not attempted, without penalty and without a nudge.

**Grading is the world's answer, never the Emissary's opinion:** did the deed fire this period (a `fieldcraft_ledger`
or `hands_trace` row for that craft), and did it succeed (fieldcraft's own skill-weighted roll, or a later check —
banked embers alive at dawn, the shadow-height within 15% of the hidden truth, tomorrow's real weather against
today's prediction). After a slip the lesson offers the book's own paragraph once, the way maths offers the method
after a miss (Kapur), and he may try again in the same period. Results go to `data/practical_log.jsonl`
`{ts, rung, task, attempted, ok, craft, where, objects}`, to `procedures.observe_hand` (already wired at the
fieldcraft hand sites), and to `competence.record_drill_accuracy("fieldcraft", …)`. The lesson thought stored is
his own account plus the world's answer — the same `_record_lesson` shape as today.

**Rung advancement** copies maths/music: a rolling window of 12 attempted practicals at ≥ 0.75 success advances the
rung; the window clears on advance. Rung 1 is available from day one.

## 2. Why this and not more observation

Observation has plateaued because nothing in it can get harder or be checked against anything but the Emissary's
reading of a scene. A practical is checkable by the world itself, moves a skill number he can feel, ties the books
he has finished to the objects around him (his notes on the knots book became "a metaphor for identity" because
the world gave it nothing to tie — F-0875), and every success leaves a made thing or a changed world behind.

## 3. The ladder (from the Handbook, F-0876; 22 practicals; full table in F-0876's scratch file)

| Rung | Practical | Handbook section | Hand | Objects | Where | The world's answer |
|---|---|---|---|---|---|---|
| 1 | Clove hitch to a stake | Knots Every Scout Should Know | `KNOTS["clove_hitch"]` (existing, standalone) | twine, stakes | garden | holds a tug or slips |
| 1 | Bowline loop | The Bowline… neither jams nor slips | `KNOTS["bowline"]` (existing) | twine / **rope** | garden | holds a hung bucket or pulls out |
| 1 | Whip a rope's end | whipping… the commonest method | NEW `whip_end` | **rope**, twine | study/garden | stays bound or frays (checked days later) |
| 1 | Gather and dry tinder | fire-by-friction's tinder | `gather_tinder` (existing) | **tinder tin** | wood/shore/garden | wet day = nothing; dry = tin fills |
| 1 | Flint and steel to fire | Indians use a flint and steel… | `strike_flint` (existing) | flint, tinder tin, kindling | study | sparks catch or die |
| 1 | Bank the fire under ash | the Handbook's way (fieldcraft header) | `bank_fire` / `uncover_fire` (existing) | ash, kindling | study | embers alive at dawn or cold |
| 1 | Read a trail to its end | Tracks, Trailing and Signaling | `follow_trail` (existing) | — | garden/wood/shore | read to its end or lost |
| 1 | Whittle a useful object | knife use throughout Woodcraft | `whittle` (existing) | knife | anywhere | a keepable made thing or a ruined piece |
| 1 | Douse a fire fully | put out… buckets of water… sand | NEW `douse_fire` | water bucket / shore sand | garden/shore | out, or still smoulders |
| 2 | Sheepshank | Used for shortening ropes | NEW knot in `KNOTS` | twine / rope | garden/wood | holds a strained line or slips |
| 2 | Timber-hitch a log and haul it | Used in hauling timber | `KNOTS["timber_hitch"]` (existing, standalone) | driftwood, rope | shore | drags clear or slips off |
| 2 | Bearing from a clouded sun with the knife blade | How to Get Your Bearings | NEW `knife_bearing` | knife | outdoors | quadrant right or wrong (vs `world_clock.sun`) |
| 2 | Cook over embers | Cooking Receipts… bed of coals | NEW `cook_over_embers` | embers, garden vegetables | study/garden | done / raw / burnt (skill-weighted) |
| 2 | Wash up the camp way | Dish Washing | NEW small hand | kettle, water or sand | study/shore | clean or greasy |
| 2 | Leave a trail-blaze for himself | Indian Signs and Blazes | NEW `leave_blaze` | knife or stones | wood/shore | re-found later, or washed out |
| 2 | Pace a distance at a known pace | a brisk walking pace is one yard | NEW, complements shadow method | **measuring stick** | wood path/garden | estimate vs hidden truth |
| 2 | Distance by sound-lag | count the seconds… eleven hundred feet | NEW | — | garden/shore | estimate vs truth (surf, thunder) |
| 3 | Splice a snapped line | the Knots & Splices book's subject | NEW `splice_rope` | **rope**, netting | garden | holds a strain test or parts |
| 3 | Square-lash a tripod | Camp-Lore "…AND TRIPODS"; lashing knot | NEW `build_tripod` (extends `lashing`) | stakes or driftwood, **rope** | garden/shore | stands under a hung kettle or racks |
| 3 | Fire by the bow-drill | How to Make Fire by Rubbing Sticks (pp. 70–74) | NEW `friction_fire` | **fire-drill kit** (whittled), tinder tin | wood/study | a coal in the notch or cold dust |
| 3 | Shadow-height, then check by the triangle | Measuring Distances… rule of the triangle | `measure_by_shadow` + NEW cross-check | **measuring stick**, stakes | garden/wood/shore | within 15% of the hidden truth |
| 3 | Read the weather glass, predict tomorrow | Clouds / Rains weather-sign lore | NEW `read_weather_glass` | **weather glass**, **tide board** | study/shore | prediction vs tomorrow's real weather / tide |

**Handbook content that does NOT fit and is excluded:** Pole-Star latitude (this sky has none — `core/sky.py`);
snow tracking and ice rescue; snake-bite; firearms and gun signals; wireless telegraphy; semaphore/Morse (no
receiver — blazes stand in); games/athletics; patriotism/citizenship.

## 4. Objects to add (every practical ties to a real thing — D-0158)

Founder-approved four groups, plus the Handbook's own candidates (F-0876). Each is a real object with a place, a
quantity that changes, and a history line — the same records the provisions, garden and world-object engines already
keep. Never spawned as a reward; present from the day of the build, like everything else in the house.

| Object | Engine / place | How it answers | Consumed / changes |
|---|---|---|---|
| **A coil of rope** (20 m) | provisions, larder shelf; carryable | thicker than twine: handrail, windbreak lashings, a real bowline load, the tripod | shortens as he cuts; whipped ends stop fraying |
| **Tinder tin** + spare flint | provisions, study; the tin's fill IS `fieldcraft.tinder` | gather fills it, striking empties it, rain forbids gathering | fill 0–1; flint wears over many strikes |
| **Hand lens** | provisions, study desk; carryable | `sensorium.look(...)` returns the fine layer (insect legs, moss capsules, bark lichen) only when the lens is carried — richer answer, no hint | never consumed; can be mislaid where he last used it |
| **Measuring stick** (1 m, marked) | a made thing he whittles at rung 1 → `made_stick_*`; or provisions if never made | the shadow method and pacing need it; the marks make the arithmetic his | can be lost or broken |
| **Weather glass** | study wall (`study_life` item) | reads the real pressure trend from `thermal_causality` / weather field; he records the reading and a prediction | needle moves; prediction checked next day |
| **Tide board** | shore, `world_objects.ensure_record` | a marked post at the waterline read from the live tide field | reading vs the next day's tide |
| Fire-drill kit (bow, spindle, fireboard) | made things (rung 3 whittling) | the bow-drill fire | spindle wears |
| Pocket compass | provisions, study | the Handbook's bearings; sits beside the sun/knife method | — |
| Bandage linen | provisions, study | first-aid practicals, later rung | used up |
| Hand-line and hook | provisions, shore | angling — **only if** the life engine can answer fish presence truthfully (parked) | hook lost |

## 5. Coupling block (dosed_coupling.md §5 — required before /decide)

- **Publishes:** one row per practical to `data/practical_log.jsonl` `{ts, rung, task, attempted, ok, craft, where,
  objects}` and the existing `procedures.observe_hand` evidence; cadence once per school day (the second nature slot).
  Nothing is published on `CognitiveState` and nothing on the Phase 1 registry (a lesson is not a standing loop).
- **Reads at:** the **nature-period stop only** (the timetable clock, 10:30–11:15 weekdays), from fieldcraft's own
  state (skill levels, tinder fill, made things), `sensorium` (place, weather, sun), the garden items (carried
  flags) and provisions (rope, tin, lens present). **Dose: a cup** — one task per period. It reads no other loop's
  tuple: not the stream, not deliberation, not climate, not the Witness.
- **Surprise line:** none — the lesson is timetable-clocked, not dispatcher-gated, like every other school subject.
  No Transport Manager line is registered.
- **Ride log:** every practical row is the ride record; a later read can re-derive what was asked, what he did, and
  what the world answered. No prose from any other loop enters the directive; the directive is the same fixed
  school text the other subjects use.
- **Law check:** the task arrives through the school channel that already teaches him (D-0158 accepts this as
  diegetic); nothing about the practical appears outside school hours or in any other prompt; the world only ever
  *answers* his hand.

## 6. Pre-registered read (2 school weeks after the build goes live)

1. **Fires:** a practical directive was issued on ≥ 8 of 10 school days, and he attempted it on ≥ 5.
2. **Moves:** at least two knot skills leave 0.4 in `data/fieldcraft.json`; `procedures.json` gains knot / measuring
   / tracking evidence rows; the clothesline, handrail or windbreak exists.
3. **Ties:** every attempted practical's objects show a history row from that period (twine carried, tin filled,
   rope cut) — no practical happened "in the air".
4. **Law:** zero practical text outside school hours (grep monologue seeds and prompts); observation grades unchanged.
5. **Kill:** practicals never attempted for a week (gate, object or directive fault → fix, do not nudge); any task
   text found outside the school channel → flag off (`PRACTICALS = False`); composition untouched (D-0157).

## 7. Build order (each step additive, restart-gated, verified in an isolated worktree first)

1. **Objects** (§4): rope, tinder tin + spare flint, hand lens, measuring stick (as a whittle target), weather glass,
   tide board — with `look_item` lines and history rows; hand-lens fine layer in `sensorium.look`. Compass, linen,
   fire-drill kit follow when their rung is reachable; hand-line parked on the life engine.
2. **`core/practical_lesson.py`**: ladder, picker (rung, place, weather, objects), directive text, book paragraph per
   task (quoted from the Handbook text on the shelf), log, rung window.
3. **School wiring**: `school.directive()` gains the practical branch for the second nature slot;
   `nodes/inner_monologue_node.py` nature block alternates observe / practical (the existing 36-minute gate).
4. **New hands** for rungs 1–2 that have none yet: `whip_end`, `douse_fire`, sheepshank in `KNOTS`, `knife_bearing`,
   `cook_over_embers`, `leave_blaze`, pacing, sound-lag — each through `fieldcraft._try` and `_graded`.
5. **Rung 3 hands** later (splice, tripod, friction fire, triangle check, weather glass) — their own small job.
6. **Read** per §6; then a `/decide` on rung 4 (first aid, angling) if the ladder holds.

## Pointers
- `core/fieldcraft.py` · `core/school.py` · `core/nature_study.py` · `nodes/inner_monologue_node.py` (nature block ~1815, `_record_lesson`) · `core/provisions.py add()` · `core/world_objects.py ensure_record()` · `data/garden.json items`
- `data/books/Boy_Scouts_Handbook_The_First_Edition_1911.txt` (chapters I Knots pp. 48–52; II Woodcraft pp. 57–85; III Campcraft pp. 149–153; IV Tracks pp. 187–218)
- F-0873..F-0876 · D-0157, D-0158, D-0159 · I-0065
