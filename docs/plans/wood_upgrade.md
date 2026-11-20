# The Wood Upgrade — the little wood as a living place

*2026-08-22, founder: "then, lets do the wood." Built the same day: `core/wood_life.py` (restart-gated). Same laws as the
garden and the study.*

> **Status: 🟢 LIVE (deeds) — built 2026-08-22 (`core/wood_life.py`); every feature in
> §1 exercised and verified in isolation (§2, the Sep→Mar simulated walkthrough — oak's year, kererū
> nesting, deadfall gales, fungi, saw/split/sharpen, the glow-worms). The old "restart-gated, not yet
> confirmed firing on its own" caveat is RESOLVED for the deed half (2026-09-02, J-0421/F-0553):
> `data/wood_ledger.jsonl` holds 4 real live deeds, 2026-08-25 12:35 → 2026-08-28 14:31 UTC
> (gather/split — see §6). The world-events half (`data/wood_events.jsonl`) is still legitimately
> 0 rows — see §5 (F-0599) for why that is season/offline-gating, not a bug.**

```plan-state
stage: live
phase: Live since 08-22; deadfall depleted, 0 deeds since 09-09 (F-1996); D-0296 ruled a felled tree as new content
verified: 2026-11-18
evidence_read: 2026-09-27
next: Founder rules D-0841 (leave, across-path consequence, or world-answer naming the chop object, or wait 14 more live days); then re-read wood_ledger.jsonl for chop rows.
cluster: 6
```


## 0. What the wood was
A scene line; a look with three branches (floor / trees / sea); an ambient pool (good prose, weather-gated); a gather hand
that minted 3–4 loads of firewood from nothing, every time; a "deadfall" feature that never ran out; nine sounds, well
gated; no state but `last_event`. Today it gained a spring.

## 1. What it is now
| Thing | Truth / clock | Earned? | Hands |
|---|---|---|---|
| **The old oak** (named, grandfathered) | bare Jun–Sep → buds and catkins Sep–Oct → leaf Oct → acorns Mar–May → leaf-fall Apr–Jun; acorns on the ground in autumn (a keepable thing — "fill a pocket"); its fall deepens the leaf-mould | — | gather acorns |
| **The kānuka grove** (hidden) | white flower Nov–Jan, bees, the fantails in it; bark in strips | the flower seen + the book read | — |
| **The tōtara** (hidden) | red berries Mar–May, the pigeons at them; bark in fibrous ropes | the berries seen + the book | — |
| **The ponga** (hidden) | silver beneath; new fronds uncurling Sep–Nov | the uncurling seen + the book | — |
| **Deadfall** | a STOCK: gales bring it down (limbs under the oak); gathering depletes it ("picked clean — it wants a gale"); the substrate still mints the odd limb as a thing | — | gather (now honest) |
| **The spring → the stream** | runs down the gully to the shore; loud after rain, a thread in a dry spell | — | fill the pail |
| **The glow-worms** | on the dark wet bank by the spring — only on dark, damp, still nights, only when he stands there and looks; they go out if he brings the lamp near | a witnessed first | look |
| **Fungi** | after autumn rain (Mar–Jun); hidden kinds described by feature; rot in a week | no names (he knows better than to taste) | look |
| **Moss, leaf-mould** | moss with rain on the north sides; leaf-mould with the oak's fall | — | look |
| **The kererū** | nests in the oak in spring: building (a clatter) → sitting (white breast) → chick → fledged | — | look up |
| **The wētā** | under the bark of a fallen limb, at night, if he looks | — | look |
| **The work** | the **axe** and the **bow-saw** (the previous occupant's, in the new **lean-to** by the cottage with a chopping block), both blunting with use; the **whetstone** sharpens them; the **wheelbarrow** brings a whole limb home; saw → green logs → the lean-to's green stack → DRY over weeks (faster in summer) → split on the block → the woodpile (the chips to the kindling box) | — | saw · split · sharpen · barrow · take the tools |
| **The fallen tree** (D-0296, code shipped J-1443, restart-gated) | a whole tree comes down ONCE, offline, while Du is away (`fell_tree()`, called by J-1444's own lab-mode script — nothing in `advance()` ever calls it); kind/name are DATA (`FALLEN_TREE_DEFAULT`), not a hardcoded branch — builder's default a windthrown macrocarpa unless the founder names one; NOT one of the four TREES above (oak keeps the nest; kānuka/tōtara/ponga keep their earned-name state) | felled once, then found only by walking in and looking (no hint) — `seen` flips True on first look, keying milestone()'s one-shot reveal | **chop** (limbs first into `d['limbs']`, blunts 0.08 per swing; then bucks the bare trunk into a new `d['rounds']` the existing **split** already draws on, blunting more; a dull axe < 0.2 glances; a wet night refuses like climb_oak) |

Wet wood (the shore, rain) burns short and smoky; green logs only smoke; a dull axe bounces — all honest refusals or consequences.
Reading binds the trees (seen-then-read names; read-alone earns a little). Three trees + three tools registered as world
objects with positions and biographies.

## 2. Verified (isolated, Sep→Mar simulated)
Oak bud (day 7) → leaf (60) → acorns in March; ponga uncurling; kānuka flowering in Nov; a kererū built (21), sat, a chick (57);
two gales brought deadfall down; fungi came up after March rain; gather drew the stock down honestly; saw 4+3 green logs;
split 3 dry logs to the woodpile (+chips); a dull axe refused; the whetstone fixed it; the glow-worms appeared at the spring
on a calm clear night. Kānuka: read 0.3 → seen flowering 0.5 → 0.8, still unnamed — one more look or book names it.

## 3. Not built
The stream's own sound (a registered sound needs the soundscape + epistemic audition registry); bird nesting in the kānuka;
the wood as a place the cat hunts; possums (a real NZ night presence — a later, deliberate addition).

**D-0296's felling itself (J-1444, part 2 of 2) is not built** — J-1443 (this pass) shipped only the CODE
(fallen-tree state, its render in look()/ambient()/milestone(), `fell_tree()`, and the `chop` deed with
grammar/edge-blunting/ledger rows — all isolated-tested in `scripts/_test_wood_life_grammar_derivation.py`'s
part 3, 20 checks, ALL OK across repeated runs). The tree is not yet down in the live world; that is J-1444's
own job, once this code is on master and Du is confirmed stopped. Also not isolated-tested here (a real,
if minor, gap): `chop()`'s wet-night refusal (item (c) of J-1443's briefing) — the code path exists and
mirrors climb_oak's own refusal shape, but forcing a deterministic night in the isolated test would need
monkeypatching `core.world_clock.daylight()`, which the 5 test bullets J-1443 actually named did not ask
for; a follow-up job covers closing that gap (see job-queue).

**Related (noted 2026-08-23, plan-overlap audit):** this build consumes `channels_programme.md`'s
thermal/light channels and `spatial_perception.md`'s coordinate-field system (the wood's positioned
objects live in `data/world_geometry/wood.json`, the exact contract that plan designed) without
citing either by name.

**Related (added 2026-08-24, J-0135):** [[du_initiated_upgrade_trigger]] is a bottom-up candidate
source for this plan's next iteration — `core.missing_object_flags.triage()['by_place']['wood']`
surfaces things Du's own thought expressed wanting that the wood doesn't have, graded by
recurrence, alongside this plan's existing founder-audit-driven process.

**Update (J-1440, 2026-09-27/28):** call `triage(window_days=None)` explicitly — the bare
`triage()` above defaults to the 14-day freshness window `/du-pulse` uses for its alarm gauge,
which read spuriously empty for every place on 2026-09-27 (F-1995) because the on-demand
`snapshot()` cadence had a real 10.6-day gap, not because the source is dead (writer confirmed
alive and re-run live; see the parent plan's Current State). The all-time view is what this plan
should keep mining from — wood currently holds only 1 entry (`frame of reference`, new/singleton,
abstract), the thinnest of the four places and still zero real world-object candidates.

## Current State — verified 2026-11-18

- **2026-11-18**: J-4314 (D-0841 b): across_path had no consequence code (F-5097 confirmed; only look() prose). Built core/locomotion.py FALLEN_TREE_CONSEQUENCE (default False, restart-gated): Du garden<->wood legs +50% seconds plus a plain physical clause while fallen_tree.across_path and trunk_rounds_left>0; self-clears when trunk chopped; cat/companion untouched; no hint or readout. Test scripts/_test_J-4314_fallen_tree_consequence.py.
- **2026-11-18** (F-5097): J-4256 (D-0296 third read, 2026-11-18): Du has not chopped the fallen macrocarpa in 26 live days since 10-15; zero chop rows, no chop attempted or refused. He named the need on 10-18 and dropped it. Founder call opened as D-0841.

- **2026-10-28** (F-3179): J-2481 BUILT (a09d953d, restart-gated): the plain look in the wood now ends with one rotating clause naming what carryable rests there -- today 'a dented tin' (garden.json seed_tin, place=wood); the axe/saw/barrow are named only when they actually lie in the wood; by-name looks and refusals byte-identical to HEAD (F-3179, D-0502).
- **2026-10-15** (F-2811): D-0296 5-day read attempt 2 (J-1652): gate met; fallen macrocarpa seen=true (revealed by place path, not look dispatch), never chopped (18 rounds/12 limbs left, no chop row). No defeater triggered.

- **2026-10-02**: J-1641 closed done (its own scope -- read, finding, plan-state note -- was complete); the actual deferred re-check now lives on freshly spawned J-1652 (not_before 2026-10-08), not on J-1641 itself, because an in_progress job is invisible to job_queue next/job-run regardless of not_before.
- **2026-10-02** (F-2223): J-1641: felling applied correctly offline (F-2223); 5-live-day read gate NOT yet met as of 2026-10-02 (about 2.0 cumulative live days so far); job deferred to 2026-10-08, D-0296 not reopened (no defeater condition triggerable yet).

- **2026-09-28** (F-2209): J-1444 (D-0296 part 2): a macrocarpa tree came down while Du was stopped, offline, no hint. Fallen, unseen, across the path, 18 trunk rounds/12 limbs. J-1641 spawned to read whether he finds/chops it after his next start + 5 live days.
- **2026-09-28** (F-2098): J-1444 attempted 2026-09-28: both hard preconditions for the offline felling are unmet -- Du is currently live (data/nascence.log continues past the 09-25 restart with active ticks through 2026-09-28 01:13), and PART 1's fell_tree()/chop code (J-1443, commit cd8b758) is only on branch jobrun/wood_upgrade, not yet on master. No felling applied; wood_life.json/wood_events.jsonl confirmed unchanged. See F-2098. Job left in_progress -- retry once Du has stopped and the branch reaches master.

- **2026-09-28** (F-2094): J-1443 shipped (restart-gated): fallen-tree state (fell_tree(), FALLEN_TREE_DEFAULT), its render in look()/ambient()/milestone() (one-shot reveal keyed on first look), and the chop deed (limbs first into d[limbs], then bucks the bare trunk into a new d[rounds] that split() now also draws on); woodwork grammar widened (hew/fell/limb verbs, trunk/fallen tree/limbs/round/rounds objects); hands.py gained a fell past-tense guard mirroring the existing saw guard. F-2094 (verified): isolated test scripts/_test_wood_life_grammar_derivation.py part 3 (20 checks) passes 4x with the live store untouched; 6 sibling grammar tests re-run, no regression. Not isolated-tested: chop's wet-night refusal (follow-up job spawned). Next: J-1444 applies fell_tree() to the live world once this code reaches master and Du is confirmed stopped.
- **2026-09-28** (F-2092): J-1441 (living_world_upgrade, F-2092): the wood is the top cross-place-miss source (69 requests: 38 to the shore, 7 to the garden, 6 to the study), explained by the already-ruled D-0224 journey-redirect protection, not a wood-specific bug. Trees, or into the trees, at 52 requests is the within-place-feature target most attributable to the wood; see decide question D-0319.

### What we have
The wood is visited daily and answers nothing: 7 deeds ever, none since 09-09, 0 in the last 14 days; 4 world
events in five weeks. Deadfall (the only working material) went 6.0 -> 0.0 with the two September gathers;
zero-in-five-weeks is the design's expected rate (a gale x a ~1.7e-4 per-tick draw), not a fault (F-1996).

### What we need
D-0296 (ruled 2026-09-27, travis: "I want a full tree to fall for him next ti[me]") calls for new content
rather than tuning the existing drought: a fallen tree, not just more deadfall trickle.

### What we're doing next
J-1443 builds the fallen-tree state, rendering, `fell_tree()`, and the CHOP hand (restart-gated); J-1444
fells it once offline while Du is down, then spawns the 5-day read on whether the wood answers again.

> **History folded** — 2 dated Current State section(s) (2026-09-02 … 2026-09-27) moved to `docs/plan_history/wood_upgrade.md` on 2026-09-27 by plan-compact. Derived timeline: `plan_ledger.py wood_upgrade`.

## 4. Current State (2026-08-24, J-0058 — instrument discovery)

**The real shadow instruments exist and are genuinely wired, not dead code — but plan-liveness
can't see them and neither can currently be read (both/(a)+(b), not (c); F-0172, findings-log).**
`core/wood_life.py` defines `_EVENTS` = `data/wood_events.jsonl` (the world's clock: tree stage
changes, deadfall gales, fungi, kererū nest stages, logs drying) and `_LEDGER` =
`data/wood_ledger.jsonl` (his deeds: gather/saw/split/sharpen/barrow/acorns) — same shape as the
garden's pair. `_log()` is called from real live call sites (6 in `advance()`, 6 across the deed
functions), and `wood_life` is imported live from `dispatch.py` (the `woodwork` Hand), `sensorium.py`
(5 sites), `garden.py` (3), `soundscape.py`, `study_note.py`, `experienced_tuple.py` — not an
orphaned module.

**(a) Too early, honestly:** neither file exists on disk yet (0 rows). `advance()` gates tree-stage
transitions on a minimum 7 days in the current stage, and gales/fungi on weather-conditioned random
draws — `data/wood_life.json`'s own `_last` timestamp shows only ~1.7 elapsed days since the
2026-08-22 build, under that floor, so 0 world-events is the expected outcome. `data/nascence.log`
shows Du walked into the wood once (2026-08-23 07:04:37) then immediately came back inside without
performing any woodwork deed — so 0 ledger rows too, and (unlike the garden's F-0143/F-0145 routing
bug, which showed *repeated* real actions producing *no* log rows) there is no repeated-action-with-
no-log pattern here to diagnose a bug from. This is a real absence of data, not a broken pipe —
revisit once Du has spent real wall-clock days in the wood and performed a woodwork deed at least
once.

**(b) Real registration gap, worth fixing regardless:** this plan doc never once cites
`wood_events.jsonl` / `wood_ledger.jsonl` by path, so `plan-liveness`'s `extract_refs()` (a path
regex over the plan's own text, per `plan_files_audit.py:48–66`) cannot find them even after they do
accrue rows. `garden_upgrade.md:190` shows the citation convention this plan is missing: `` `data/garden_ledger.jsonl` (his deeds) · `data/garden_events.jsonl` (the world's) ``.
Citing both paths in this Current State section (this edit) is the fix — a future triage pass will
now find them here regardless of whether §1's table above is ever touched to add them too: **wood's
ledger is `data/wood_ledger.jsonl`, wood's events are `data/wood_events.jsonl`.**

## 5. Current State (2026-09-02, J-0438/F-0599 — 7-day gate re-checked, still 0 rows, real cause found)

`wood_events.jsonl` still does not exist on disk (11 calendar days after build) even though the
7-day min-stage gate §4(a) named has long since passed (satisfied 2026-08-29). Re-checked whether
this is now a real "never fires" bug — it is not: `_EVENTS` is confirmed the correct, live write
target (6 `_log(_EVENTS,...)` calls inside `advance()`, wired live via
`sensorium.tick() → core/sensorium.py:2839–2843 → _wl.advance(now, _dt_world)`), so this is not the
social_world_school-class filename mismatch. The real cause: **Du has been offline since
2026-08-31 17:47:17** (`data/nascence.log`'s last line, no restart marker since — confirmed by
dozens of unrelated `data/*.json(l)` files all sharing that same mtime cluster), which was *before*
the 2026-09-01 month boundary that would have fired the oak's deterministic `bare→bud` transition
(gate already satisfied by 08-29; `data/wood_life.json` still shows `oak.stage="bare"`,
`stage_ts`=bootstrap 2026-08-22, i.e. zero transitions ever recorded). Real live-tick coverage was
only ~9.3 days (08-22 11:25 → 08-31 17:47), not the 11 calendar days the gate assumed. The other
event types (gale-deadfall, fungi [months 3–6 only, currently month 9], kererū nest [months 9–11,
random per-day draw], log-drying [needs green logs — currently 0]) are each legitimately
weather/season/action-gated and simply have not coincided in that window — same conclusion §4(a)
already reached, just now re-verified past the gate rather than excused as "too early." Full
evidence trail: F-0599 (findings-log). Follow-up: J-0441, to re-check once Du has a live session
spanning a real month boundary (or a qualifying weather event) — only if it *still* shows 0 rows
after a confirmed live month-boundary tick would that be real evidence of a bug.

**J-0441 CLOSED 2026-09-02 (F-0622, verified) — confirms the diagnosis, no bug.** Du restarted
2026-09-02 20:48 UTC. On the first tick past the (already-satisfied since 08-29) gate,
`wood_events.jsonl` wrote its first-ever 2 rows: `oak_bud` and `ponga_uncurling`, both at the
restart timestamp — the deterministic transition that had been pending the whole offline stretch
fired exactly once, correctly, the moment a live tick reached it. No repeat/duplicate firing since.
Mechanism confirmed sound.

