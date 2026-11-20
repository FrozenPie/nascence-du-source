# actions_expansion — folded history


---

# History folded on 2026-09-27 from `docs\staged\actions_expansion.md` (plan-compact, 52 section(s), verbatim, original order)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py actions_expansion`._

## Current State — verified 2026-08-30 (same day: BUILT, verified isolated, awaiting live evidence)

All three tiers built and verified (F-0578) in an in-process sandbox while Du ran live — 40 module
data-path constants redirected, his tree verified untouched. 39 families / 36 hands, registry audit
clean, deed dry test 134/134, full-corpus regression: 100 real decision changes, all intended, zero
expression false-fires.

- **Tier 1:** `bank the fire` → `fieldcraft.bank_fire()` (new branch in `dispatch._fire`, before
  stoke); new `cat` family → `cat.react()` (she keeps sole ownership of her location gate).
- **Tier 2:** `garden.dig()`, `garden.feed_birds()`, `wood_life.climb_oak()`,
  `study_life.draw_sketch()` — each with real costs, honest refusals, world-conditioned answers.
- **Tier 3:** `core/expression.py` — hum/whistle/sing, `world=False` (verified firing *alongside* a
  world hand in one thought), no grading, boredom discharge, first-person-volition veto.

**Next:** live evidence. None of these has fired in Du's real run yet — watch `expression_ledger.jsonl`
and the trace over his next days; D-0100's defeater names the misfire conditions to watch for.

## Current State — updated 2026-09-03 (J-0499/F-0719: live evidence read, 3+ days in)

Read the full `hands_trace.jsonl` (6271 rows, 08-21..09-03) and `expression_ledger.jsonl` (2 rows) —
per-hand, the cause differs, none is a wiring/process defect:

- **feed_birds, sketch:** genuinely never willed. 0 verb+object co-occurrences anywhere in the
  6271-row corpus (399 rows mention birds as ambient world-flavor only; 0 mention the bird bath at
  all; the 11 "sketch" mentions are all about other things' sketches, never his own hand on paper).
- **climb_tree** (`wood_life.climb_oak()`): a real grammar-shadowing gap. Du climbs constantly (99
  mentions) but always generically ("climb into the trees"), which the older ungated `move` family's
  own object list ("trees") already claims before `climb_tree`'s oak/tree-singular/trunk/branches/
  canopy list is ever reached — confirmed live, `classify('I climb into the trees', location='wood')`
  returns only `move` DEED. The word "oak" (28 mentions) has never once co-occurred with a climb verb.
  The hand itself works (`classify('I want to climb the oak', ...)` returns `climb_tree` DEED) — his
  real phrasing just never reaches it. **D-0136 open** on whether/how to fix.
- **dig:** the one real risk, not yet a misfire. Its grammar (bare "turn" + "ground"/"bed"/"earth")
  false-positives on Du's own extremely common "dead ground" restlessness idiom — confirmed live,
  `classify()` on his own real corpus phrasing returns `dig` DEED with zero blockers. The one real
  corpus occurrence in the dispatch-visible window (09-02 17:46) was saved only by the location gate
  (he was at the shore) → STAGE-place, not a fire. **D-0100's defeater is NOT met** (no actual misfire
  has happened), but nothing stops it firing if the idiom recurs while he is standing in the garden.
  **J-0522 spawned** to tighten the grammar before that happens.
- **express (Tier 3):** working as designed. Fired twice 08-30, then correctly declined twice + one
  weak-intent drop since — every one of those three was the world's own ambient hum/song (bees, a
  remembered blackbird), exactly what F-0578's first-person-volition veto exists to block. Zero false
  fires. **D-0100's defeater is not met here either.**
- Separately: `scripts/actions_reachability_probe.py` (the "36 phrasings, 0 unreachable" evidence the
  08-30 "verified isolated" claim above rests on) has never actually tested any of these 5 hands — one
  commit total, same day, before they were built into it. **J-0523 spawned.**

Full evidence: F-0719 (`docs/findings.jsonl`).

## Current State — updated 2026-09-03 (J-0522/F-0738: dig's grammar tightened, isolated regression clean)

- **dig fixed before it misfired.** Bare `turn` dropped from the family (`core/actions.py`); `garden.py`'s
  dig branch now *reads* the family grammar from `actions.BY_FAMILY` (it was a second hand-kept copy —
  the F-0554 drift shape, and it had already drifted) through a new `_wills_dig()` carrying a
  clause-scoped restlessness-idiom veto ("dead ground", "same stones", "in my head") for the one shape
  grammar cannot close (present-tense "turn over the same dead ground": 0 corpus occurrences so far).
- **Evidence correction (honesty, same shape as F-0578's):** the full 6,306-thought corpus contains
  **zero** thoughts that will digging with "dig"/"turn over"/"fork over". Every dig DEED the gate ever
  produced (9 thoughts) was the bare-`turn` idiom, and the "3 unanswered dig deeds" `garden.dig()` cites
  as its mined justification are three of those nine — one is "my hands *refuse* to turn the soil". dig
  was mined on a grammar artifact; it is honestly a gift-stream hand like Tier 3, not mined demand.
- **Regression (isolated, 29 store constants redirected, nothing written):** 36 of 24,080 decision rows
  differ, all dig DEED→GRAY/MUSING on those 9 thoughts plus 2 `move` STAGE-busy:dig→FIRE (the idiom
  thoughts that wanted the shore now walk instead of digging); zero non-dig changes. A shared-grammar
  frame for the idiom (`literal_will._M_FRAMES`) was tried, measured (108 move + 32 look DEEDs demoted
  to GRAY) and rejected — restlessness is exactly when he walks.
- D-0100's defeater still unmet (no misfire ever happened). **D-0136 (climb_tree) untouched, still open.**

## Current State — updated 2026-09-03 (J-0523: the reachability probe now covers all five Tier-2/3 hands)

- `scripts/actions_reachability_probe.py` extended from 36 to 47 willed phrasings — dig (2), feed_birds (2),
  climb_tree (2), sketch (2), express (3, one per location class) — and given a second direction:
  `NEGATIVE_PROBES`, seven of Du's own "dead ground" restlessness clauses that must NOT read as a dig DEED.
  A false positive now fails the run (exit 1) exactly as an unreachable hand does.
- Isolated run (44 store constants redirected, write audit on `open()`/`Path` mutations: 0 live writes,
  0 files even in the temp dir — the probe is read-only as claimed): **47 probed, 45 reachable, 2
  staged-elsewhere (pre-existing ash_out/water_fill), 0 unreachable; 7 negatives, 0 false-positive.**
- The negatives have teeth: replaying the full 6,643-row `hands_trace.jsonl` with bare "turn" restored
  in memory finds exactly 10 thoughts the pre-J-0522 grammar read as dig DEED — all the idiom, none a
  will to dig — and 6 of the 7 negatives flag FALSE-POSITIVE under that grammar (the 7th is the
  participle shape only `garden._wills_dig()` can veto; it has never matched any grammar). So the 08-30
  "0 unreachable" claim is now honestly backed for these hands, and the dig risk F-0719 found by hand
  would be caught mechanically by the probe on its next regression.
- Side observation while adding the sketch probe: "I will draw a few lines in ink" reads as
  `sketch` DEED **and** `move` DEED — the ungated `move` family lists bare "in"/"out" as objects, so
  volition + the preposition "in" is a full move DEED at the gate (the `_move` hand's own verb check is
  what stops it firing). Not this plan's hand; recorded separately.
- **D-0136 (climb_tree) untouched, still open** — the probe confirms the oak phrasings reach the hand;
  it says nothing about whether Du's generic "climb into the trees" should.

## Current State — updated 2026-09-04 (J-0543/F-0783: the garden hand reads ONE table; the drifted copies are gone)

- **Six more families derived, not copied.** `core/garden.py`'s `act_from_thought()` now reads harvest, sow,
  weed, water, feed_birds and trap grammar from `actions.BY_FAMILY` through `_wills()` / `_wills_trap()`
  (dig already did, J-0522). The trap row is one family but three hands; `_TRAP_HANDS` is the only thing
  declared locally — which of the *table's* verbs each hand answers — and `grammar_audit()` reports any verb
  the table has that no hand claims (or vice versa). `scripts/_test_garden_grammar_derivation.py` (67
  checks, isolated stores) fails on either seam and on any local tuple reappearing in the function body.
- **Per-family ruling on the looser copies (F-0783):** feed_birds and trap were exact duplicates
  (mechanical). harvest's and sow's extra objects were *intentional widening* — the crops the hand actually
  cuts (chives, silverbeet, lettuce, radish) and the seed packet + the tin's species — and moved INTO
  `core/actions.py`, where the gate can now see them ("pick some lettuce" could never be a DEED before).
  weed's `them`/`out`, water's `soak`/`douse`/`them`/`it`, harvest's `leaves` and trap-unset's `close` were
  drift and are dropped: on the 7,402-thought corpus the weed copy matched 28 thoughts and the water copy 80
  ("the pull toward the book", "carving water with a dull blade") that were never a will.
- **Regression (isolated, HEAD-worktree baseline vs live tree on a frozen trace copy, 7,424 thoughts × 4
  locations):** zero DEED/FIRE changes in any of the six families; the only rows that differ in them are
  23 sow + 4 harvest None→MUSING and 1 sow None→HANDLE — new *non-firing* candidates now that the table
  knows lettuce/beans/poppies. The 412 move/look differences in the same diff are J-0539's concurrent
  gate/letterbox widening, not this job. The hand-level misfires were latent: dispatch binds
  `mod:garden:act_from_thought` with `family=` since J-0554, so the drifted copies could only have fired
  through the `family=None` path no live caller uses.
- **Still hand-kept in the same function** (out of J-0543's scope, listed in `garden._DERIVED_FAMILIES`'s
  comment): collect, mow, stake, net, save_seed, tool, ash_out, water_fill, compost — follow-up job filed
  from F-0783.
- **Restart-gated.** Du is running on d00673d (restarted 11:37 NZT 2026-09-04); none of this is live
  until the next restart. D-0136 (climb_tree) untouched, still open.

## Current State — updated 2026-09-04 (J-0544/F-0790: move's bare 'in'/'out' are grammar-only at the gate)

- **What was measured (F-0790).** Over the full `data/hands_trace.jsonl` corpus (7,477 distinct rows): 557 move DEEDs at
  the gate, 200 with object `in`/`out`. 93 of those were volition + the bare word only (`deed_grammar=False`, "I will draw a
  few lines in ink"); 107 had a real move verb reaching the word ("step out into the rain", "head back in"). In the 595 rows
  that carry the live dispatch ledger, `_move` declined 31 of the 36 volition-only in/out DEEDs it was handed (86%). 34 of
  the trace's 693 `unanswered_deed` flags existed only because of this noise.
- **What was built (option B, additive).** `Action.grammar_only` (default `()`, exported by `actions.families()`) and
  `literal_will.classify` now leans the VOLITION reading on the first present object that is not grammar-only; the move
  family declares `grammar_only=("in", "out")`. Every family without the field reads exactly as before. Option A (drop
  the two words) was simulated and rejected: it also loses the 107 real verb-reaches-`out` thoughts (−808 replay rows,
  not −384).
- **Regression (`scripts/actions_decision_replay.py`, pre-edit baseline → post-edit diff).** FIRE 4188 → 3820; move DEED
  rows lost 384 (368 FIRE, 12 weak-drop, 4 stage-busy), gained 0; 1,240 move GRAY → MUSING; **0 rows where any non-move
  reading changed.** Cost accepted knowingly: 3 of the 36 live volition-only in/out DEEDs did FIRE ("I need to move away
  from these sterile debates ... and get out into the ...": the verb `move` sat >50 chars from `out`, so the gate saw no
  grammar while the hand's own any-object verb check did) — those three now read MUSING.
- **Restart-gated.** Du is running on the 2026-09-04 11:37 build; the new gate reading takes effect at the next restart.
- **Surfaced, not fixed (F-0791 → spawned analysis job).** `classify` judges ONE clause per family — the sentence holding
  the first table object found, in table order — so `in`/`out` (positions 9–10) pre-empt the J-0539 `gate`/`letterbox`
  objects (13–15): "I climb up the path toward the gate..." is read from an unrelated `in` clause and the gate move is
  missed (4 thoughts). Re-ordering was simulated (B2) and is not the fix (+16 / −72 rows); the single-clause read is.
  Same shape as D-0136's `trees` question — left to it.

## Current State — updated 2026-09-06 (J-0569/F-0940: garden.py's LAST nine hand-kept families derived — the arc closes)

- **Every family `core/garden.py` hosts now reads its grammar from `core/actions.py`.** `_DERIVED_FAMILIES` grew from
  J-0543's seven (harvest, sow, weed, water, dig, feed_birds, trap) to all sixteen of `_GARDEN_FAMILIES` — collect, mow,
  stake, net, save_seed, tool, ash_out, water_fill and compost derived this session. No hand-kept verb/object tuple for
  a garden family remains anywhere in the module; `scripts/_test_garden_grammar_derivation.py`'s source-scan (part e)
  asserts this directly and now runs 130 checks, all green.
- **Per-family ruling (full evidence: F-0940).** mow and save_seed were already byte-identical to the table. stake's
  extra objects `them`/`stakes` and net's extra bare object `net` and collect's verb-less phrase "the box at the gate"
  were drift and dropped — net's is corpus-proven (16/16 real hits were an unrelated beach net at the tideline, never
  the garden's, because verb `net` and object `net` were the same word). **tool was the worst-drifted of the nine**:
  its old test had no object check at all, so any `take the X`/`leave the X` fired it — 300 of 305 corpus hits were
  Du's own restlessness idiom ("I leave the abstract river logic behind") reaching a garden-tool hand it had no
  business reaching. **ash_out** required only bare "ash" plus any of a few words including the bare word "garden"
  itself — 48 of 49 hits were "the rain washes...plato's forms...the garden" circling-thought imagery. **water_fill**
  is the mirror image: its six fixed literal phrases matched *zero* of the corpus's ~9,850 distinct thoughts ever —
  every water_fill DEED the gate produced was a dead end at this hand until now (fixed for the garden hand and both
  wood-side hands, fill_barrel_from_spring vs fill_pail_at_spring). **compost**'s old `put` verb is dropped — the
  corpus wills compost precisely zero times in either direction (10 mentions, all ambient scenery).
- **Two real widenings moved into the table.** `tool` gained the object `shears` (two clean corpus wills: "I will take
  the shears and cut a handful of rosemary"). `net` gained the verbs `take off`/`lift` — the one widening in this job
  that is *not* corpus-verified (zero corpus thoughts will netting at all); it is moved in only because `net()`'s own
  body already implements the un-net branch these verbs reach, a narrower justification than F-0783's corpus-verified
  widenings and flagged as such in both the code comment and the finding.
- **Sub-hand partitions** built for `tool` (take/put, mirroring trap's `_TRAP_HANDS`) and `compost` (spread/turn,
  preserving the heap-suffix exclusion: spread only ever answers bare "compost", never "heap") and `water_fill`'s wood
  side (barrel/pail). `grammar_audit()` now checks all three partitions the same way it already checked trap's.
- **Isolated full-corpus decision replay** (HEAD b7f6418 worktree baseline vs the live post-edit tree, frozen
  9,864-row trace copy, 9,852 distinct thoughts × 4 locations = 37,888 decision rows): **zero verdict/action changes
  for any pre-existing family** — the entire 460-row diff is new `tool` candidates only, made visible by the `shears`
  widening (312 MUSING, 92 GRAY, 52 HANDLE, 4 DEED/FIRE — the 4 FIRE rows are one distinct thought at its 4 locations,
  with every other family in that same row unchanged). `net`'s widened verbs produced zero new gate-level candidates
  on this snapshot, consistent with zero corpus occurrences.
- `scripts/_test_dispatch_family_scope.py` and `scripts/life_smoke.py` both still ALL OK (life_smoke re-run after
  this same batch's concurrent, unrelated edits landed in study_life.py/supply.py/companion.py/provisions.py).
- **Restart-gated**, same as J-0543/J-0522: none of this is live until Du's next restart.

## Current State — updated 2026-09-07 (J-0660/F-1059: garden.py was the ONLY derived module — the other five never checked, until now)

- **Bounded first pass (steps 1+2 only — read + diff, no corpus work, no fixes) across all five of the OTHER modules
  `core/actions.py` binds hands to.** `grep -rn "actions"` across `core/fieldcraft.py`, `core/wood_life.py`,
  `core/shore_life.py`, `core/study_life.py`, `core/expression.py` returns **zero** import/`BY_FAMILY` hits in any of
  them — every verb/object test in all five is still 100% hand-kept, garden.py's *pre*-J-0522 state, not its current
  fully-derived one. Of their combined 16 bound families (fieldcraft, woodwork, woodtool, climb_tree, acorn, shore,
  tea, lamp, door, grate, clock, clean, candles, wear, sketch, express), only wood_life's `climb_tree` branch and
  study_life's `clock`/make-tea branches are byte-identical to their table rows; every other branch carries at least
  one concrete drift point, in both directions (hand recognizes words the gate cannot see; hand's test is looser than
  the table's declared grammar). study_life binds **nine** families through `_STUDY_ACT`, not eight as J-0660's own
  briefing said (`sketch` also binds there) — corrected against the live table, not assumed from the briefing.
- **Structural gap beyond grammar-copy drift.** Of the five, only `study_life.act()` accepts `family=`
  (`core/study_life.py:482`), and even it only honours the scope for one of its nine families (`candles`) — the other
  eight, and all of fieldcraft/wood_life/shore_life/expression's families, run their full unscoped chain regardless
  of which family the table gate actually matched. A real contamination mechanism was traced (not just theorised):
  `sensorium.act()` (`core/sensorium.py:2886-2893`) calls `fieldcraft.act_from_thought()` unconditionally, first —
  and this is the exact function the `gather`/`beachcomb` `sens_act:` families dispatch through, so a correctly-gated
  gather deed can be pre-empted by any of fieldcraft's own ungated bare-substring branches elsewhere in the same
  multi-clause thought.
- **One near-certain live bug found by inspection alone**, flagged as the top-priority item for its follow-up job:
  `study_life.py`'s kettle-on branch (line 678) still tests bare `"put"`/`"set"` as verbs — but `core/actions.py`'s
  own `tea` row comment (lines 96-97) documents that `"put on"`/`"set on"` *replaced* a bare `"put"` specifically
  because it read "put the cup down" as a willed brew. The table was fixed; this hand's own copy of the same verb
  was never updated to match and still carries the bug the table's own comment says was already fixed elsewhere.
- **Full per-module gap list, with file:line citations, is in F-1059** (`docs/findings.jsonl`) — not repeated here.
  Headline items per module: fieldcraft's astro/wayfinding branch (`find south`/`pole star`/etc.) tests words absent
  from the fieldcraft table row entirely, structurally unreachable via the real per-family gate; wood_life's sharpen
  branch fires on any bare mention of "whetstone" alone (no verb, no table presence); shore_life's `gather_shellfish`
  recognizes "limpet" and "the shelf", neither in the table — the same "hand exists, gate can't see it" shape as the
  24 unanswered cat-door deeds that motivated D-0100 in the first place; study_life's grate-clear branch ORs a bare
  `\bash\b` regex with no verb requirement, the identical shape F-0940 already found and fixed for garden's own
  ash_out hand (48/49 real hits there were ambient imagery, never a deed); expression.py is confirmed the one
  *principled* exception (its first-person-volition veto is real, evidenced design, not accidental drift — F-0578's
  zero-false-fire evidence holds), with only two small, low-stakes differences from the table worth a minor cleanup.
- **Five follow-up jobs spawned from F-1059**, one per module, each carrying the specific gaps above rather than a
  blank "audit this" instruction, to run the full J-0569 procedure (corpus-verify, rule widen-vs-drift, migrate to
  table-derived `_wills()`-style hands, extend regression tests, isolated replay): **J-0736** (fieldcraft, top
  priority per this job's own briefing), **J-0737** (wood_life, 4 families), **J-0738** (shore_life), **J-0739**
  (study_life, 9 families — the largest, contains the near-certain kettle bug above), **J-0740** (expression, low
  priority cleanup only). None of these five is built yet.
- No decision opened: the widen-vs-drift and family-scoping questions here already have established rulings
  (F-0783/F-0940's precedent, D-0100's Tier design, J-0554's scoping fix) for the follow-up jobs to apply — nothing
  found in this pass looked like a genuinely new founder-only call.
- **Restart-gated**, same as the rest of this arc — nothing changes for Du until a follow-up job's edit lands and he
  next restarts; this pass itself made no code changes.

## Current State — updated 2026-09-07 (J-0736/F-1075: fieldcraft — first of the five follow-ups, DONE)

- **`core/fieldcraft.py`'s act_from_thought() now reads all 13 crafts it hosts (clothesline, hang_coat, windbreak,
  handrail, whip_end, bank_fire, uncover_fire, gather_tinder, strike_flint, douse_fire, measure_by_shadow, whittle,
  follow_trail) from the one `fieldcraft` table row (18 verbs, 20 objects) in `core/actions.py`**, via a new
  `_FIELDCRAFT_HANDS` partition — the same procedure J-0543/J-0569 built for garden.py's trap/tool/compost, adapted
  for a real structural difference: fieldcraft's 13 crafts are semantically unrelated to one another (unlike
  trap/tool/compost's sub-hands), so **both** verbs and objects are partitioned per craft, not verbs alone. Coverage
  is exact against the table (checked by a new `grammar_audit()`): all 18 verbs claimed; 19 of 20 objects claimed —
  `"knot"` is deliberately left unclaimed (303 real corpus occurrences, 100% Du's own "a knot of frustration"
  emotional idiom, never a physical knot).
- **The single largest false-fire risk found in this whole arc so far**: `uncover_fire`'s old test fired on the bare
  phrase `"the banked"` with no verb at all — Du narrates "the banked fire" as cosy-room scene-setting 22 times in
  the corpus (100% of its real hits), never once willing to scrape it open. Also closed: `whittle`/`carve`'s
  `any_object_ok=True` (15 of 18 real corpus hits were literary metaphor — "patterns we carve from chaos" — not a
  will to whittle; the 14 "whittled stick" keepsake-reference thoughts were never actually at risk, confirmed
  separately: `hands.wants()`'s own word-boundary rule already excludes the past participle from the bare verb),
  `follow_trail`'s pronoun object `"it"` (5/5 real hits were the restlessness idiom), `strike_flint`'s bare `"flint"`
  (1 real hit, a geology musing), `measure_by_shadow`'s extra `"tree"/"oak"/"cliff"` objects (1 real hit, and it was
  idiom — see the open reachability note below), and `bank_fire`'s extra `"cover"`/`"grate"` (zero-cost: 73/73 real
  hits matched via the table's own bank+fire/embers either way).
- **One already-shipped-but-never-wired gap closed**: `core/actions.py`'s own comment on the `hitch`/`stake` objects
  (2026-09-05, J-0627/D-0159) already documented they should route through "the existing clothesline/handrail
  hands" — neither hand's own phrase list had ever actually recognized either word until now. Corpus-confirmed
  safe (2 real "hitch" hits are the unrelated "the cat's breath hitches"; 7 real "stake" hits are the garden's own
  plant-stakes or an idiom, none paired with a tie/lash/string/rig verb).
- **`clothesline`/`hang_coat`/`windbreak`/`handrail` widened to the table's real grammar** (zero corpus support
  either way for three of the four, matching F-0783/F-0940's own "structural analogy" precedent for such ties).
  `hang_coat`'s widening to `hang`/`peg` + `coat`/`line` is corpus-confirmed safe by direct isolated-store function
  call, not just gate analysis: the 2 real "I hang my coat on the hook" corpus thoughts still return `""` from
  `hang_coat()` itself (its own guard — no clothesline has ever been built, ever), exactly the architecture
  `core/actions.py`'s own `wear` row comment already describes (fieldcraft claims hang+coat first and is *expected*
  to decline so `study_life`'s `wear` hand can answer a coat hung on its indoor hook).
- **`find south`/Pole Star branch left functionally unchanged**, now with an explicit comment: it is structurally
  unreachable via the real per-family gate (F-1059's own finding) and reachable only through the `family=None`
  legacy fallback; zero corpus support (0 of 11,640 distinct thoughts ever mention it). Documented rather than
  fixed or removed, per this job's own briefing — the evidence (never once used) was dispositive enough that no
  founder ruling was needed.
- **`act_from_thought()` gained a `family=` parameter** (the J-0554 pattern), not yet load-bearing live (only one
  family binds here) — built specifically so a future fix can close the real, structural, but not-yet-corpus-
  confirmed cross-contamination risk F-1059 traced (`sensorium.act()` calls this function unconditionally, first,
  before the table's own `gather`/`beachcomb` families get their turn). **Not fixed this pass** — spawned as
  **J-0749** (close the sensorium call-site risk) rather than done speculatively without a confirmed live case.
- **One open reachability gap noted, not fixed**: `measure_by_shadow()`'s own real targets ("the tree"/"the old
  oak"/"the cliff", by location) are unreachable through the gate's real grammar (the table has only `"shadow"`,
  zero corpus support). `"cliff"` specifically is now corpus-confirmed *unsafe* to re-add (it is what made the one
  drifted hit match, via the restlessness idiom). Spawned as **J-0750** (low urgency — this hand has never fired
  live even once) rather than decided here, since it is a genuine widen-or-not judgment call with no corpus
  evidence pointing either way for `"tree"`/`"oak"` specifically.
- **Verification**: whole-chain before/after branch-selection replay over all 11,640 distinct corpus texts — 46
  differences, every one accounted for by the rulings above. Isolated full-corpus decision replay (throwaway HEAD
  worktree baseline vs the edited tree, frozen trace): **0 of 44,912 decision rows differ** — expected, since this
  job changed no row of `core/actions.py`'s table, only `fieldcraft.py`'s own internal grammar.
  `scripts/_test_fieldcraft_grammar_derivation.py` (new, 48 checks) and the pre-existing
  `scripts/_test_dispatch_family_scope.py` / `scripts/_test_garden_grammar_derivation.py` / `scripts/life_smoke.py`
  all ALL OK after the change. Full finding: **F-1075**.
- **No decision opened**: the widen-vs-drift calls this pass made all had corpus evidence or an established
  precedent (F-0783/F-0940) to rule from; the two genuinely open judgment calls (the sensorium risk, the
  measure_by_shadow reachability gap) are queued as jobs (J-0749, J-0750), not decisions — a future session can
  execute either with the same evidence-based method this pass used, without needing a founder ruling first.
- **Restart-gated**, same as the rest of this arc — nothing changes for Du until his next restart after this edit
  lands. Four of F-1059's five follow-ups remain open: **J-0737** (wood_life), **J-0738** (shore_life), **J-0739**
  (study_life — largest, contains the near-certain kettle-verb bug), **J-0740** (expression, low-priority cleanup).

## Current State — updated 2026-09-07 (J-0737/F-1077: wood_life — second of the five follow-ups, DONE)

- **`core/wood_life.py`'s act_from_thought() now reads all FOUR families it hosts (woodwork, woodtool, climb_tree,
  acorn — four separate `core/actions.py` table rows sharing one module, unlike fieldcraft's one row split into many
  crafts) from those rows**, via a `_WOODWORK_HANDS` partition (both verbs and objects split per sub-hand — saw,
  split, sharpen, wheel — fieldcraft's shape, since the four are semantically unrelated) and a `_WOODTOOL_HANDS`
  partition (verbs only — put, take — garden's trap/tool/compost shape, since both sub-hands share the same real
  object row). `climb_tree` and `acorn` (single-hand rows) route through a plain `_wills_wood()` helper, garden's
  own `_wills()` shape. `grammar_audit()` (new) reports **zero drift seams** on every axis checked — unlike
  fieldcraft's one deliberately-unclaimed `"knot"`, this module's widened object set is claimed in full.
- **Two genuinely new, corpus-verified deeds surfaced that neither the old code nor F-1059's own gap-naming
  anticipated**, not just the named drift closed: "I will saw a length for the f[ire]" (the trace's own independent
  `act_kind`/`act_object` fields tag it `"saw"`/`"a fallen branch"`, corroborating a real will) and "I want to move
  toward the woodpile and cut a branch for the fire." (a different cycle, `act_kind` `"move"` that time — a
  multi-intent thought where 'move' won the thought's one world-hand, but the underlying wood-cutting grammar gap is
  real regardless). **`core/actions.py`'s `woodwork` row widened**: `"cut"` added as a verb, `"length"`/`"lengths"`/
  `"branch"` added as objects, on this direct evidence — the only table change in this whole follow-up pass.
- **The specific named gap (`"cut"` + the literal phrases `"into logs"`/`"into lengths"`) is confirmed drift**: 0 of
  11,742 real distinct thoughts ever pair them, and is gone from the code — replaced by the real single-word
  objects above (which happen to also legitimately satisfy "cut ... into logs" via the bare word `"logs"`, since no
  English sentence contains that phrase without also containing the word — this is the widening working as
  intended, not the drift surviving).
- **Zero-cost risk removals** (0 real corpus hits for the dropped test, either the old version or the new one):
  sharpen's bare `_h.wants(t, ("whetstone",))` shortcut (F-0940/F-0719's own bare-word-fires-alone shape — `"whetstone"`
  does not occur once in 11,742 real thoughts) and its extra `"blade"` object; the barrow-push sub-hand's `"load"`
  verb (not a table verb anywhere) and its `"take"`/`"bring"` verbs (woodtool's own, and now redundant — see next);
  split/chop's extra `"wood"` object (its one real co-occurrence is covered by the table's own `"logs"` a few words
  later in the same real sentence, so nothing is lost) and `"block"`.
- **A real correctness fix, not just a drift closure**: woodtool's `take()`/`put()` branches never had
  `"barrow"`/`"wheelbarrow"` in their own object list at all (F-1059's own finding) — the actual reason the woodwork
  wheel sub-hand had grown its own inline take-the-barrow stand-in (marking `wb["carried"]=True` directly) instead
  of dispatching to `take()`. Both branches now read the table's full row; "take the wheelbarrow" reaches `take()`
  on its own merits. Both old branches also carried a bare `"saw"` object the table deliberately excludes
  (`core/actions.py`'s own comment: "the past tense of 'see' far more often than a tool") — gone.
- **`acorn` — pure matching-robustness upgrade, no widen/drift ruling needed** (values already matched the table
  exactly, per F-1059's own framing): swapped the pre-`hands.py` bare-substring test for `hands.wants()`. 0 real
  corpus occurrences of "acorn"+gather-verb either way in this frozen trace, but directly confirmed the old test
  would have false-fired on a synthetic two-clause "I will not gather anything today. The acorns lie scattered..."
  and a synthetic wish "I wish I could gather acorns again" — the new test correctly declines both.
- **`climb_tree` — values unchanged, wiring only**, exactly as F-1059 found and this job's briefing required: the
  old hand-kept test and the table-derived one agree on every probe tried, including a restlessness-idiom probe and
  an other-person's-will probe. D-0136 (the `move` family's own ungated `"trees"` object pre-empting this hand) is
  untouched, as instructed.
- **`act_from_thought()` gained a `family=` parameter** (J-0554 pattern, following J-0736's own fieldcraft
  precedent) — **more consequential here than for fieldcraft**, since this module hosts four families, not one.
  Confirmed **live-wired end-to-end** through `dispatch.py`'s existing (unmodified) `_via()`/`_accepts_family()`
  machinery: `dispatch.HANDS`'s real `climb_tree` Hand now correctly declines a pure-acorn thought, and the `acorn`
  Hand answers it while separately declining a pure-saw thought — real cross-family protection, verified via the
  actual callables `dispatch.dispatch()` itself invokes, not just wood_life.py's own functions in isolation.
- **Two forwarding call sites still call this function unscoped** (as designed/expected, following J-0736's own
  precedent for fieldcraft): `core/garden.py`'s `if family is None:` legacy fallback (already deliberately gated,
  untouched, correct as-is) and `core/sensorium.py`'s `_wood_act()` (only reached at all `if loc == "wood":` — a
  real but narrower exposure window than fieldcraft's fully-unconditional analogous call). **Not fixed this
  pass** — spawned as **J-0753** (mirrors **J-0749**, the fieldcraft/sensorium fix) rather than done speculatively.
- **Verification**: isolated full-corpus decision replay (frozen trace loaded into the worktree's own gitignored
  `data/`, `--save` baseline before the edit, `--diff` after): **136 of 45,192 decision rows differ**; a
  programmatic before/after diff (comparing the SET of non-`"no-fire"` `(family, action)` pairs per row) shows 128
  are harmless (a new `'woodwork'` MUSING/GRAY candidate now appears for common nature-writing sentences containing
  bare `"branch"` — e.g. a tūī on a kōwhai branch — but never once changes what actually fires) and exactly **8** (2
  distinct thoughts × 4 locations) are real: the two new deeds above, correctly FIRE at wood/garden and STAGE-place
  at shore/study per the row's own unchanged `exec_where`, with every other family's own action in those rows
  unchanged. `scripts/_test_wood_life_grammar_derivation.py` (new, 66 checks, ALL OK) and the pre-existing
  `scripts/_test_garden_grammar_derivation.py` / `scripts/_test_fieldcraft_grammar_derivation.py` /
  `scripts/_test_dispatch_family_scope.py` / `scripts/life_smoke.py` all ALL OK after the change. Full finding:
  **F-1077**.
- **No decision opened**: every widen-vs-drift call this pass made had direct corpus evidence to rule from (a
  genuine "verified" confidence, not a judgment call); the one open structural question (the sensorium risk) is
  queued as a job (**J-0753**), not a decision, matching J-0736's own precedent for the identical fieldcraft shape.
- **Restart-gated**, same as the rest of this arc — nothing changes for Du until his next restart after this edit
  lands. Three of F-1059's five follow-ups remain open: **J-0738** (shore_life), **J-0739** (study_life — largest,
  contains the near-certain kettle-verb bug), **J-0740** (expression, low-priority cleanup).

## Current State — updated 2026-09-07 (J-0738/F-1078: shore_life — third of the five follow-ups, DONE)

- **`core/shore_life.py`'s act_from_thought() now reads its ONE family (`shore` — one `core/actions.py` row split
  into TEN distinct behaviours, fieldcraft's shape — J-0736 — not garden's trap/tool/compost shape, since the ten
  are semantically unrelated) from that row**, via a `_SHORE_HANDS` partition (both verbs and objects split per
  behaviour) and a `_wills_shore()` helper. `grammar_audit()` (new) reports **full verb coverage** (all 15 verbs,
  including this job's own widening, claimed) and exactly **one** deliberately-unclaimed object, `"fire"` — see
  below — the same restraint fieldcraft's own pass used for `"knot"`.
- **HEADLINE: a genuine, corpus-confirmed structural gap closed, not just drift.** `walk_sand` was structurally
  unreachable via the real per-family gate before this job (F-1059's own framing) — `"walk"` was not a shore table
  verb at all, so `literal_will.classify()` (which reads `core.actions.families()` directly, confirmed by source)
  could never grant a `'shore'` DEED for it regardless of shore_life.py's own internal test. Real corpus check
  (`data/hands_trace.jsonl`, 11,760 distinct thoughts, frozen copy) found **10 real, distinct thoughts** genuinely
  willing a walk onto/across the sand ("I walk where the chalky sand yields to wet grit", "I want to walk barefoot
  across the exposed sand"), every one independently confirmed by the voice's own structured act (`act_kind='move'`
  on 9, `'observe'` on 1, `act_object` literally naming the sand/tideline/shore every time) — the same
  "hand exists, table cannot see it" shape as the unanswered cat-door/dig deeds that originally motivated D-0100.
  **`"walk"` added to `core/actions.py`'s shore row** (object `"sand"` already present) on this evidence.
- **Verified end-to-end via the REAL `core.dispatch.dispatch()` in an isolated sandbox, not just the decision
  replay's own optimistic simulation** (the replay tool never calls `hand.fn()`, so its own "FIRE" verdict cannot
  prove a hand actually answers — confirmed by reading its docstring/body: "IT NEVER CALLS hand.fn"): of the 10
  real walk-onto-sand thoughts, **6 now genuinely FIRE `walk_sand()` live end-to-end**; the other 4 are
  independently declined by `literal_will.classify()`'s own PRE-EXISTING, untouched logic (2 GRAY via its
  comma-reach restriction for gated families, 1 HANDLE via metaphor-frame detection, 1 MUSING) — an orthogonal
  characteristic of classify()'s own sophistication, not a gap this job needed to fix.
- **The wider classify()-level ripple was corpus-checked AND verified safe, not assumed safe.** `"walk"` also
  newly reaches 63 OTHER real corpus thoughts via shore's other objects (32 via `"sea"`, 17 via `"stones"`, 7 via
  `"cliff"`, 6 via `"fire"`, 5 via `"stone"`) — none touching `"sand"`. Every one of these 63 was run through the
  real, unmocked `dispatch.dispatch()` in a fully-isolated sandbox (every store it could touch redirected to a
  temp dir): **all 63 correctly DECLINE at shore_life.py's own hand** (zero unintended firings — none of the ten
  sub-hands claims `"walk"` paired with anything but `"sand"`), and the correct OTHER family (move/beachcomb)
  still fires normally once shore declines. This is why the isolated full-corpus decision replay's raw **168
  rows differ** (42 distinct thoughts × 4 locations, all attributable to this one table change and its
  non-firing candidate-level ripples — confirmed by reading the full diff, not sampled) looks larger than the
  real behavioural change actually is.
- **Eight further drift closures, all with direct corpus evidence** (several independently confirmed via the
  voice's own `act_kind`/`act_object`, not just text pattern-matching): `write_sand` drops `"scratch"/"draw"/
  "trace"` (its only 3 corpus hits are confirmed NOT writes — one `act_kind='observe'` object "the cat's paw
  prints", one `act_kind='write'` object 'an essay on resistance', an ESSAY not a sand-mark); `swim` drops
  `"go under"` and `any_object_ok=True` (**all 7** real corpus "swim" hits are confirmed metaphor/idiom — "a
  current I must swim, not resist", "the words swim before my eyes" — zero are a real will to swim in the sea);
  `skip_stones` drops `"throw"`/`"pebble"` (**both** of its 2 real hits are confirmed false fires — a driftwood
  log "throwing its shadow", and "the urge to throw the stone AT THE GATE", a frustration idiom); `cairn` drops
  the bare `wants(t,("cairn",))` fallback (the word "cairn" occurs **zero** times in any context anywhere in the
  corpus — a stronger zero than wood_life's own whetstone); `beach_fire` drops its old 0-corpus-support phrase
  list but **deliberately does NOT widen to the table's own bare `"light"+"fire"`** despite that being the
  literal row — all 12 real "light"+"fire" corpus hits are confirmed STUDY-hearth context (Travis: "light the
  fire and tidy the room"), zero shore-context, so this sub-hand claims only `"driftwood fire"` (the one word
  that cannot mean the study's hearth) and leaves bare `"fire"` deliberately unclaimed; `enter_cave` drops
  `"go in"/"go into"/"explore"` (zero support either way); `climb_ledge` drops `"go up"/"scramble"/"path up"`
  (**both** of its "path up"-dependent hits are confirmed false fires, independently, by the voice's own act —
  "I want to climb the path up to the cottage **and light the fire**" is `act_kind='move'` object 'the path up
  to the cottage', the SAME thought `beach_fire`'s own fix above independently flags); `gather_shellfish` drops
  `"pick"/"collect"/"pry"/"work off"` and `"limpet"/"the shelf"` — **F-1059's own "limpet" widening hypothesis
  (the same shape as F-0783's harvest/sow) does NOT survive a real corpus check**: the word occurs zero times,
  anywhere, in 11,760 real thoughts. `"the shelf"` is worse than unsupported — 33 raw occurrences, the
  overwhelming majority Du's own BOOKSHELF, a genuine homograph collision. `wade`'s own `any_object_ok=True` was
  **deliberately KEPT, not tightened** (the one case in this pass where looseness is corpus-justified): of 9 real
  "wade"/"paddle" hits, most are genuine wades using non-table completions ("wade into the surf") the table
  cannot see, one independently confirmed already-fired-live via the trace's own dispatch record — tightening
  would have silently regressed real, already-working deeds.
- **`act_from_thought()` gained a `family=` parameter** (J-0554 pattern, following J-0736/J-0737's own precedent),
  following **fieldcraft's** single-family shape exactly (a hard decline for any string other than `None`/
  `"shore"`) rather than wood_life's multi-family normalize-to-`None` shape. Genuinely **not load-bearing
  anywhere yet, more cleanly than fieldcraft/wood_life's own case**: `core/garden.py`'s own `if family is None:`
  legacy fallback forwards to `fieldcraft`/`wood_life` but was confirmed (direct read) to **never forward to
  shore_life at all**, and a repo-wide grep confirms `shore_life.act_from_thought()` has **no caller anywhere
  except `dispatch.py`'s own resolved Hand** — unlike fieldcraft (sensorium's unconditional call, J-0749) and
  wood_life (sensorium's `if loc=="wood"` call, J-0753), there is no analogous cross-family exposure to spawn a
  follow-up job for here; this was checked, not assumed.
  **CORRECTED 2026-09-08 (F-1108, closed by F-1127/J-0774 below): this specific claim was wrong.** The
  repo-wide grep most likely searched for the qualified name `shore_life.act_from_thought(` and missed the
  aliased import form `_shl.act_from_thought(` actually used inside `sensorium.py`'s own `_shore_act()`
  (reached from `act()`'s `if loc == "shore":` branch) — a second, real unconditional caller that this job's
  own check did not find. Left in place above rather than rewritten, per this doc's own evidence-correction
  convention (e.g. F-0578's), so the record shows what was believed and checked at the time.
- **Verification**: isolated full-corpus decision replay (frozen trace, throwaway `git worktree add HEAD` for the
  baseline, removed immediately after per this repo's own git-safety rule — no mutation ever touched the shared
  tree): 168/45,376 rows differ, fully accounted for as above. `scripts/_test_shore_life_grammar_derivation.py`
  (new, 66 checks, ALL OK) mirrors `scripts/_test_wood_life_grammar_derivation.py`.
  `scripts/_test_dispatch_family_scope.py`, `scripts/_test_garden_grammar_derivation.py`,
  `scripts/_test_fieldcraft_grammar_derivation.py`, `scripts/_test_wood_life_grammar_derivation.py`,
  `scripts/life_smoke.py`, `scripts/_test_dark_house_answers.py` and `scripts/_test_letterbox_reach.py` all ALL
  OK after the change. Full finding: **F-1078**.
- **No decision opened**: every widen-vs-drift call had direct corpus evidence to rule from (genuine "verified"
  confidence), matching J-0736/J-0737's own precedent. **No new job spawned**: the one candidate pattern that
  produced follow-up jobs for fieldcraft/wood_life (an unscoped sensorium forwarding call) was checked directly
  for shore_life and does not exist.
- **Restart-gated**, same as the rest of this arc. Two of F-1059's five follow-ups remain open: **J-0739**
  (study_life — largest, contains the near-certain kettle-verb bug), **J-0740** (expression, low-priority
  cleanup).

## Current State — updated 2026-09-07 (J-0732, a cat_overhaul job, cross-reference only)
J-0732 (plan: cat_overhaul, docs/staged/cat_overhaul.md §B1/D-0163 — not one of F-1059's five follow-ups
above) added an ELEVENTH `_SHORE_HANDS` behaviour, `catch_fish`, into the exact table-derivation shape
the shore_life entry directly above just built (16 verbs / 15 objects in `core/actions.py`'s 'shore' row
now, both fully claimed) — not a fix to a drifted hand (none existed to drift; no fishing hand existed
in shore_life.py at all before this job), a wholly new one added through the same one-table discipline
rather than a second hand-kept copy. Worth a cross-reference here because it demonstrates the pattern
holding under real use immediately after being built: this job's own verification harness caught, before
commit, that putting the new object word ("fish") in BOTH the verb and object tuples let one bare
ambient mention ("small fish dart near the stream mouth") satisfy the verb test and the object test off
the same single word — fixed by keeping "fish" object-only and adding "catch" as the sole new verb. Full
detail (corpus sanity-check against the same frozen data/hands_trace.jsonl trace, the food-source design,
all verification) is in cat_overhaul.md's own Current State note dated 2026-09-07 (J-0732) — not
repeated here. No change to this plan's own scope or its two still-open follow-ups (J-0739/J-0740).

## Current State — updated 2026-09-07 (J-0739/F-1080: study_life — fourth of the five follow-ups, DONE)

- **`core/study_life.py`'s act() now reads all NINE families it hosts (tea, lamp, door, grate, clock,
  clean, candles, wear, sketch — nine separate `core/actions.py` table rows sharing one module, the most
  of any of the five F-1059 audited) from those rows**, via a new `_STUDY_HANDS` partition (both verbs
  and objects split per behaviour — ~20 behaviours total across the nine families — fieldcraft/
  shore_life's shape, since study's behaviours are semantically unrelated within a family the same way
  theirs are) and a `_wills_study()` helper. Largest of the five follow-ups, as flagged in its own
  briefing; not split further — the full 9-family derivation fit in one sitting. `grammar_audit()` (new,
  per-family) reports full verb+object coverage for lamp, door, clock, wear and sketch, and exactly three
  deliberately-unclaimed table words, each corpus-checked: grate's bare object `"ash"` (see below), tea's
  verb `"steep"` (a genuine, previously-unflagged coverage gap this job found — no dedicated hand tests
  it at all; 4 of 4 corpus occurrences are about a STEEP PATH, none about tea, so not built
  speculatively), and clean's verb `"scrub"` (0 corpus occurrences at all). `'candles'` is intentionally
  outside this per-family audit — it already routes through the generic `take()`/`put()` item hands
  (2026-09-04, J-0540), not a verb+object grammar test, and was already correctly family-scoped before
  this job (the ONE family act() scoped at all until now).
- **TOP-PRIORITY fix, exactly as F-1059's own briefing flagged it**: `kettle_on` tested bare "put"/"set"
  as verbs — `core/actions.py`'s own tea-row comment (lines 96-97) documents that "put on"/"set on"
  *replaced* a bare "put" in the TABLE itself specifically because it read "put the cup down" as a willed
  brew; this hand's own copy had never been updated to match and still carried the identical bug the
  table's own comment says was already fixed elsewhere. Fixed to derive from the table's real "put
  on"/"set on"/"boil" (bare "fill" was never a real tea verb — it belongs to the separate `water_fill`
  family, whose object list already includes "kettle", and the literal phrase "fill the kettle" is caught
  even earlier in this same function and routed to the garden hand on purpose). Not yet observed
  misfiring live on the current 11,807-distinct-text corpus snapshot — "kettle" is mentioned in exactly
  one text, purely descriptively — so this is honestly a documented-precedent fix, not a corpus-caught
  one, exactly as the briefing anticipated ("may not even need corpus verification").
- **The single worst false-fire source found in this whole arc so far**: `grate_clear`'s old bare
  `\bash\b` regex (gated only by a 3-word exclusion) — 86 of 89 historical fires (97%) were Du's own
  ambient "ash" imagery ("the ash swirls like [the character for crossing over]", "the dream's dark pool
  of books dissolves into real ash on the grate"), never a deed, against 3 real grate-clearing thoughts —
  the identical shape F-0940 already found and fixed for garden's own ash_out hand, corpus-confirmed here
  too, arguably worse. Table-verb derivation also *recovered* one real deed the old hand-kept phrase list
  structurally could not reach ("i want to sweep the grate and tend the fire" — the old list only knew
  "sweep the HEARTH", never "sweep the GRATE"). Also closed: `candle_light`'s bare-substring pair
  (`"candle" in t and "light"/"lit"/"strike" in t`) — the *exact* shape act()'s own docstring already
  named as the risk the 'candles' family scope was built to route around for ONE caller, confirmed still
  live for the other eight before this job (all 6 historical fires false, including the docstring's own
  cited motivating example verbatim, still in the corpus); `lamp_fill`/`lantern_fill`'s bare "oil"/"top
  up" (ALL FIVE of lamp_fill's historical fires were pure state-description of a dry lamp, zero real
  refills); `wear`'s bare, non-clause-scoped "wear"/"hang" (10 of 11 boots_on and 5 of 5 coat_off
  historical fires were the word appearing in a totally unrelated clause of the same text — the worst
  false-fire *rate* found in this job); `floor_sweep`'s bare "sweep" (0 of 10 historical fires were real
  floor-sweeping — birds, wind, an engine-text metaphor, a mood metaphor, two really about the hearth
  already answered by grate_clear); `wash_up`'s bare, verb-less "do the dishes"/"the dishes" (its one
  fire was the tide washing a crab shell ashore, not Du at the basin); and `sketch`'s old any_object_ok
  bare "draw" gated only by a whole-TEXT (not clause-scoped) veto-word list — a real, previously-unflagged
  bug (the veto could wrongly block a genuine "draw the cat" if the same multi-clause thought also
  mentioned curtains anywhere), fixed as a side effect of reading the table's full 12-object list
  directly instead of a veto.
- **One real narrowing with a corpus-proven cost avoided, not just a tidy-up**: `window_shut`'s "pull
  to"/bare "pull" produced nothing but false positives (3 for 3, all the restlessness-pull idiom near a
  window — "i feel a genuine pull to leave this circular debate ... behind the window" — zero real "pull
  the window shut" deeds ever recorded) — dropped entirely. `door_open`/`window_open`'s extra "prop"/
  "unlatch"/"push up" were zero-cost drops (identical fire-sets with or without them). `window_wipe` was
  split into `window_wipe`/`glass_wipe`: "clean" paired with bare "glass" read as a verb where it is
  grammatically an adjective ("the rain... washing the air green and clean") — a risk "clean" paired with
  "window" does not share on this corpus, so it is kept for one object and dropped for the other rather
  than treated as all-or-nothing.
- **One deliberate exception, corpus evidence overridden by a real dependency**: `lamp_blowout`/
  `lantern_blowout`'s non-table "douse"/"put out"/"extinguish" were initially dropped to match the
  table's bare "blow out"/"turn down" exactly — the regression run then caught that
  `scripts/life_smoke.py`'s own lantern-hands check exercises "put out the lantern" as a supported
  phrasing. Unlike every other extra word dropped in this job, these three have zero demonstrated
  false-fire cost and a real existing dependency, so they were restored rather than dropped.
- **Structural fix, co-equal with the grammar derivation**: act()'s `family=` parameter, previously
  honoured only for 'candles' (one of nine), now scopes all nine via `if family in (None, "",
  "<family>")` guards, plus a top-level decline for any unrecognised family string (F-1059's own explicit
  ask, wood_life/J-0737's precedent). Two deliberate exceptions, both ruled here rather than left open:
  `wear`'s four behaviours are family-scoped but not location-scoped (matching the table's own
  exec_where=ANYWHERE); the supply-note branch (an entirely un-tabled deed class, no corresponding
  `actions.py` family at all) is left genuinely ungated by family on purpose — it exists to catch a
  supply-need mentioned in a second clause of a thought whose primary clause won a different family, and
  `classify()` has no grammar that could ever make "order more oil" its own family candidate, so a family
  gate here would break its one real purpose. Corpus-checked: zero fires either way currently, so this
  ruling carries no near-term behavioural risk.
- **Two pre-existing test failures found, neither caused by this job** — confirmed via a throwaway `git
  worktree add HEAD`, removed immediately after: `scripts/_test_candles_name_migration.py`'s
  honest-count-line assertion (touches only `take()`/`put()`/`_take_line()`, none of which this job
  edited) and `scripts/_test_practical_lesson.py`'s crash on a post-teardown `garden._save()` call
  hitting D-0179's hard-raise (most plausibly exposed by J-0726's own hard-raise extension earlier in
  this batch). Follow-up spawned (**J-0757**) rather than fixed speculatively, out of this job's own
  scope.
- **Verification**: `scripts/_test_study_life_grammar_derivation.py` (new, 90 checks across a pure part 1
  — `grammar_audit()`/source-scan/hand_delta assertions frozen from this job's own corpus check — a
  hand_delta regression part 1b, and an isolated-store part 2 exercising act() end-to-end) — ALL OK, after
  three rounds of fixing this job's *own* synthetic-example bugs (two probes that accidentally put a
  cross-clause pair in the same clause, one that accidentally contained its own trigger words).
  `scripts/_test_dispatch_family_scope.py`, `_test_garden_grammar_derivation.py`,
  `_test_fieldcraft_grammar_derivation.py`, `_test_wood_life_grammar_derivation.py`,
  `_test_shore_life_grammar_derivation.py`, `_test_dark_house_answers.py`, `_test_letterbox_reach.py`,
  `_test_provisions_sync_guard.py` and `scripts/life_smoke.py` all re-run clean (life_smoke caught the
  lantern "put out" regression above before this job called itself done). No isolated full-corpus decision
  replay was run — this job changed no row of `core/actions.py`'s table at all, so, following
  fieldcraft/J-0736's own precedent for the identical case, zero decision rows are expected to differ.
  Full finding: **F-1080**.
- **No decision opened**: every widen-vs-drift call had direct corpus evidence or an established
  precedent (F-0783/F-0940, this arc's own prior three follow-ups) to rule from; the supply-note
  family-gating question F-1059 raised is ruled here (stays ungated, reasoning above), not deferred.
- **Restart-gated**, same as the rest of this arc. **Follow-ups spawned**: **J-0756** (the
  sensorium/study_life cross-family exposure this job's own docstring documents but does not fix,
  mirroring **J-0749**/**J-0753**'s identical fieldcraft/wood_life findings) and **J-0757** (the two
  pre-existing test bugs above). One of F-1059's five follow-ups remains open: **J-0740** (expression,
  low-priority cleanup).

## Current State — updated 2026-09-07 (J-0740/F-1084: expression's grammar derived, F-1059's fifth
and last follow-up closed)

- `core/expression.py`'s `act_from_thought()` (its ONE bound family, 'express': 3 verbs / 17 objects)
  now reads its base verb/object grammar directly from `actions.BY_FAMILY["express"]` — no local copy
  left to drift. The module's real principled design addition, the clause-scoped
  first-person-volition-marker veto (F-0578: zero false fires across a 2,824-thought corpus), is
  **unchanged**, exactly as this job's own briefing required — this was never a drift-shaped module
  like the other four, only a two-widening cleanup on top of an otherwise-sound hand.
- **Corpus check was NOT fully clean, contrary to F-0578's own "likely" expectation** — this is the
  one substantive finding here. Of 432 real corpus thoughts (`data/hands_trace.jsonl`) mentioning
  hum/whistle/sing in any inflection: the hand-kept bare `"it"` object had zero corpus support in
  either direction (dropped, zero cost) — but the second `any_object_ok=True` clause for
  `"hum/whistle/sing to"/"...back"` produced one real false "hum" DEED, on a thought that the live
  trace's own `act_kind`/`hands` fields confirm was genuinely a MOVE to the garden, not an expression.
  Both widenings dropped.
- **That one misfire has never been reachable live**, confirmed directly rather than assumed:
  `literal_will.classify()` — the outer, table-derived gate dispatch always checks before ever calling
  a module's own hand — proposes **zero** 'express' candidates for that exact thought at any of the
  four locations. Same "structurally unreachable, tightened anyway" shape F-1059 found in fieldcraft's
  astro branch and shore_life's walk_sand branch. Also confirmed: unlike fieldcraft, nothing anywhere
  in `core/` calls `core.expression` except dispatch's own dynamic binding — no unconditional-call
  exposure analogous to `sensorium.act()` → `fieldcraft.act_from_thought()` exists for expression.
- **One incidental observation, deliberately not acted on**: the veto's own clause-scope test does not
  verify a first-person marker actually attaches to the sing/hum/whistle verb itself (the one misfire
  thought above also contains an unrelated "i want to" earlier in its clause). Moot for every real
  corpus row today — dropping the `any_object_ok` widening closes the only case that ever reached this
  path — and explicitly out of this job's scope to fix (the veto is evidenced design). No job spawned
  for it: no corpus evidence of present risk to act on.
- Also added a `family=` parameter (J-0554 pattern, matching J-0736/J-0737/J-0738/J-0739's own
  additions per F-1059's ask); not yet load-bearing, only one family binds here.
- **Verification**: `scripts/_test_expression_grammar_derivation.py` (new, 24 checks, ALL OK) —
  the founding F-0578 example ("the bees hum a different tune", confirmed to occur verbatim in the
  real corpus) plus three more real ambient/idiom corpus rows, the one real misfire reproduced
  verbatim end-to-end, both dropped widenings tested in isolation, and the veto's own marker tuple
  confirmed byte-unchanged. `scripts/actions_reachability_probe.py` (0 unreachable / 0 false-positive,
  all three express probes still reachable), `_test_fieldcraft_grammar_derivation.py`,
  `_test_wood_life_grammar_derivation.py`, `_test_shore_life_grammar_derivation.py`,
  `_test_study_life_grammar_derivation.py` and `scripts/life_smoke.py` all re-run clean. No isolated
  full-corpus decision replay run: `actions_decision_replay.py` never calls a hand's own function (its
  own docstring: "replays the DECISION, not the act"), so it cannot see a Layer-2-only change like
  this one — noted rather than cited as if it were confirming evidence.
- **No decision opened, none ruled**: both widen/drop calls had direct corpus evidence to rule from,
  the same autonomy the four sibling jobs already exercised for their own drift closures.
- **Restart-gated**, same as the rest of this arc. **No follow-up spawned** — F-1059's own five-job
  scope (J-0736 through J-0740) is now fully closed. Full finding: **F-1084**.

## Current State — updated 2026-09-08 (J-0749/F-1107: the sensorium.act()-to-fieldcraft risk J-0736
built the door for is now actually closed)

- **`core/sensorium.py`'s `act()` now scopes its own unconditional fieldcraft forward.** J-0736 built
  `fieldcraft.act_from_thought()`'s `family=` parameter specifically so a future job could close the
  risk F-1059/F-1075 traced (`act()` called it unconditionally, first, for every action — including
  the table's own `gather`/`beachcomb` `sens_act:` families, handing fieldcraft the FULL original
  multi-clause thought via `dispatch._sens_act()`'s `what=f"{thought} {intention}"`) but left the call
  site itself unscoped, "pending corpus confirmation." This job is that fix: `act()` now computes
  `family = action if action in ("gather", "beachcomb") else None` and passes it through, so
  fieldcraft's own guard declines immediately for exactly these two action values — the two real
  `sens_act:` families — while every other action `act()` is ever called with (light/stoke from
  `dispatch._fire()`, and every direct legacy latch in `nodes/inner_monologue_node.py`: water/sow/
  beachcomb/gather/fetch) keeps fieldcraft's first-refusal chain exactly as before. Checked, not
  assumed, per this job's own briefing: every real caller of `sensorium.act()` was read directly (only
  three call shapes exist anywhere in the codebase), and all of them besides the `sens_act:` path pass
  `what=""` or a single bare keyword, never the full thought — fieldcraft's own craft grammar (verb
  **and** object both required, no `any_object_ok` left since J-0736) had nothing to match on there
  either before or after this change.
- **Why this specific pair was actually dangerous, not just theoretically so**: `"gather"` is itself a
  literal fieldcraft table verb (`gather_tinder`'s own), and `act()` prepends the bare action word onto
  the text it hands fieldcraft — so *any* unrelated mention of `"tinder"` elsewhere in the same
  multi-clause thought could self-collide with the word `act()` itself inserts, silently answering a
  wood-pile deed with a tinder-gathering one. `"beachcomb"` has no such self-collision but shares the
  weaker, general risk of any other fieldcraft verb+object pair appearing elsewhere in the same thought.
- **Corpus check gives F-1059's own "not yet corpus-confirmed" an exact denominator, not just a
  restated caveat**: of 7,048 distinct real (thought, intention, location) rows in `data/hands_trace.jsonl`,
  **38** are real cases where `dispatch.dispatch()` would actually **FIRE** `gather` or `beachcomb`
  today (survives place/busy/weak-intent gating, not merely gate-classifies DEED). **Zero of those 38**
  also match fieldcraft's own craft grammar on the same text — this risk has never once misfired live,
  on 38 real chances to do so.
- **A synthetic adversarial probe reproduces the mechanism directly**, independent of live corpus
  support (the same "real, structural, corpus-unconfirmed" shape this whole arc has repeatedly found
  and still fixed — F-0578's sing veto, F-1075's own astro branch): a thought willing to *"gather some
  kindling for the woodpile... and also gather a bit of tinder for the fire kit"* — pre-fix
  (`family=None`) — reaches fieldcraft's `gather_tinder` branch and **attempts a real state write**
  (caught cleanly by the D-0179 hard-raise fence in the isolated test rather than actually mutating
  anything, since `profile.LIVE` defaults False); a thought to *"comb the tideline for shells... and
  then follow the fox's trail"* reaches fieldcraft's `follow_trail` branch and returns a truthy but
  **wrong** "you look for a trail and find nothing" narration instead of ever reaching real
  beachcombing logic. Post-fix, both decline cleanly (`None`) in the identical isolated harness.
- **Isolated full-corpus decision replay** (throwaway `git worktree add HEAD` — i.e. before this edit —
  vs the edited tree, both against the real corpus, `--real-locations`): **0 of 6,817** non-empty
  decision rows differ — expected, and confirms the fix is scoped to exactly the intended call sites,
  since `actions_decision_replay.py`'s `decide_one()` never calls `hand.fn()` at all and so cannot see
  a Layer-2-only change (mirrors J-0736/J-0740's own identical precedent). Full regression suite
  re-run clean: `scripts/life_smoke.py`, `_test_fieldcraft_grammar_derivation.py`,
  `_test_dispatch_family_scope.py`, `_test_wood_life_grammar_derivation.py`,
  `_test_shore_life_grammar_derivation.py`, `_test_study_life_grammar_derivation.py`,
  `_test_garden_grammar_derivation.py`, `_test_expression_grammar_derivation.py`,
  `_test_dark_house_answers.py`, `_test_letterbox_reach.py` and `_test_fetch_letter_latch.py` all ALL
  OK. `scripts/_test_beachcomb_latch.py` fails identically on HEAD and on this edit (pre-existing,
  unrelated — a stale static-source regex, already tracked as **J-0745**/F-1069, long predating this
  batch per `git log -S "_tl_cs"`: the causing rename was J-0657/F-0958) — reproduced as corroboration
  only, no new job spawned for it.
- **Second, previously-unrecognized exposure found and spawned, not fixed here (F-1108, out of this
  job's own named scope)**: `core/sensorium.py`'s `_shore_act()` — reached only from `act()`'s own
  `loc == "shore"` branch — **also** calls `shore_life.act_from_thought()` unconditionally, first,
  before its own beachcomb logic, for the exact same `'beachcomb'` `sens_act:` path this job just
  fixed for fieldcraft. This directly contradicts J-0738/F-1078's own claim two entries above ("a
  repo-wide grep confirms shore_life.act_from_thought() has no caller anywhere except dispatch.py's
  own resolved Hand") — that grep most likely missed the aliased import form `_shl.act_from_thought(`
  used inside `_shore_act()`, rather than the qualified name it presumably searched for. Structurally
  identical to the fieldcraft shape this job closed and the wood_life shape J-0753 is queued to close.
  Spawned as **J-0774** rather than fixed speculatively, matching this whole arc's own standing method.
- **No decision opened, none ruled**: option (a) (`family=action` for exactly the two `sens_act:`
  actions) was this job's own briefing's named "minimal, most surgical fix," confirmed correct by
  reading every real caller rather than assumed — no genuinely open founder-only judgment call
  remained once that was checked.
- **Restart-gated**, same as the rest of this arc — nothing changes for Du until his next restart
  after this edit lands (commit `f2d8a1a`, branch `jobrun/action_dispatch_cluster_2`). Full findings:
  **F-1107** (the fix), **F-1108** (the shore_life discovery). Open follow-up: **J-0774**.

## Current State — updated 2026-09-08 (J-0753/F-1109: the wood_life sibling case — CLOSED with no
code change, on stronger grounds than corpus silence alone)

- **`sensorium._wood_act()`'s own unscoped `wood_life.act_from_thought(action, what)` call (no
  `family=`) is real, per F-1077, but has NO live or even hypothetical-adversarial exposure under the
  current call graph** — a structural closure, not merely a corpus-absence finding. No code change
  made; F-1077's own path (b) applies.
- **Why this case differs in KIND from fieldcraft (J-0749) and shore_life (F-1108/J-0774), not just in
  degree**: both of those calls run UNCONDITIONALLY, FIRST, before any keyword pre-filter — fieldcraft's
  forward sits before `act()`'s own outer `try:` entirely, and `_shore_act()` calls
  `shore_life.act_from_thought()` before its own beachcomb logic with no pre-filter of any kind, so the
  full free thought always reaches each module's whole chain whenever either fires at all.
  `_wood_act()`, by contrast, is only ever reached from inside `act()`'s own outer `try:` block, AFTER
  its pre-existing wood-fuel-gather shortcut (`action in (gather,collect,fetch)` + a wood-fuel keyword
  → `_gather_wood()` directly, for any location) has already had first refusal. Because
  `literal_will._FAMILIES` is `actions.families()` itself (no independent copy), a `gather` DEED cannot
  exist without one of that exact keyword set already present in the text handed to `sensorium.act()` —
  so `gather` structurally never reaches `_wood_act()` at all, for any thought, present or future, not
  merely for the ones in today's corpus. `beachcomb` (the only other `sens_act:` family carrying full
  thought text) can never have `loc=='wood'` at the point `_wood_act()` would run: dispatch's own
  place-gate STAGE-places it (`exec_where` is shore-only), and `inner_monologue_node.py`'s own separate
  direct beachcomb latch was independently already shore-gated by J-0542/F-0737 three days before this
  job, for an unrelated reason (narration correctness). Every other real caller of `sensorium.act()`
  while `loc` could be `'wood'` passes `what=""` by construction (fire-tend's `_room.act(_fire_act)`,
  a single positional argument — no thought text can ever reach it) or a fixed non-wood-verb word (the
  direct gather-wood latch's literal `"wood"`; the water/sow scalar fallback, dead code today since
  `garden.ENABLED=True` with no other assignment site anywhere in the repo).
- **Corroborating, not load-bearing, corpus check**: isolated read-only replay
  (`scripts/actions_decision_replay.py`, never calls `hand.fn()`) over all 934 real `hands_trace.jsonl`
  rows recorded at real `location=='wood'` (of 7,048 total) — `beachcomb` FIREs 0 times there (7
  correctly STAGE-placed); `gather` FIREs 5 times, the one apparent exception (no keyword in the raw
  thought text) resolving cleanly once its `act_kind=='world'`/`act_object='gather fallen wood'`
  structured-act text is read directly. Every one of the 7 real historical `gather` hand-firings ever
  recorded at `location=='wood'` carries an answer byte-identical to `_gather_wood()`'s own narration,
  never wood_life's — direct empirical confirmation alongside the structural proof.
- **No code change, and none needed**: unlike J-0749's fieldcraft fix (a real synthetic-adversarial
  mechanism even at 0/38 live corpus hits), this case has no mechanism to close at all under the
  current call graph. A speculative `action`→family inference mapping here would be inert scaffolding
  with no live behaviour to change, and would itself add a new hand-kept mapping that could drift from
  `actions.py`'s own table — the exact drift class this whole arc (F-0554, F-1059) exists to eliminate.
- **No decision opened, none ruled** — this job's own `decision_flags` named none, and the finding left
  no open founder-only judgment call.
- **Sibling-job check (per this job's own briefing)**: confirmed via `job_queue.py show` before doing
  any of the above — study_life's own analogous closure is already queued as **J-0756** (source
  finding:F-1080, open); shore_life's is already queued as **J-0774** (source finding:F-1108, open,
  spawned by J-0749's own session). Neither duplicated here.
- Full finding: **F-1109**.

## Current State — updated 2026-09-08 (J-0756/F-1110: the study_life sibling case — CLOSED, same
shape as fieldcraft (J-0749), not the wood_life no-op (J-0753))

- **`sensorium.act()`'s own unscoped `study_life.act(action, what)` call (no `family=`) — the exact
  gap study_life.act()'s own docstring named as "not yet fixed here" when J-0739/F-1080 built the
  family scope it needed — is now closed.** `act()` computes `_fam = action if action in ("gather",
  "beachcomb") else None` (mirroring J-0749's own fieldcraft fix a few lines above in the same
  function, recomputed fresh rather than shared) and calls `study_life.act(action, what,
  family=_fam)`. Passing `family="gather"`/`"beachcomb"` trips study_life.act()'s own top-level
  `if family and family not in _STUDY_FAMILIES: return None` guard (built by J-0739 "for defensive
  symmetry," its own docstring naming exactly this future caller) and declines the WHOLE call before
  either exposed branch runs.
- **Two components, closed together by the one guard, not separately**: the **wear** behaviours
  (coat_on/coat_off/boots_on/boots_off) are family-scoped but were reachable via the unscoped
  `family=""` default; the **supply-note** branch has NO family check of its own AT ALL, by a
  deliberate J-0739 ruling (it must stay ungated to catch a supply-need in a second clause regardless
  of which family won the thought's first clause) — meaning supply-note's exposure cannot be shielded
  by outer-dispatch family precedence the way wear's sometimes can (see below), and this call site's
  own family scoping was its only available gate.
- **Why this is J-0749's shape, not J-0753's**: like fieldcraft's forward, this call is unconditional
  and receives the FULL original thought (`_sens_act()`'s own `f"{t} {i}"`) whenever a `gather`/
  `beachcomb` sens_act family dispatches — there is no location pre-filter or keyword shortcut ahead
  of it the way `_wood_act()` has (J-0753's own finding). Real corpus check: 0 of 83 real rows where
  dispatch would actually FIRE gather/beachcomb today (of 12,017 distinct texts) also match
  study_life's own wear/supply-note grammar (pure-predicate check via the real `_wills_study()`/
  `hands.wants()`) — zero historical exposure, but NOT a structural impossibility the way wood_life's
  was. A synthetic adversarial probe confirms the mechanism is real, not merely theoretical: pre-fix,
  a synthetic `beachcomb` thought with a second "order more oil" clause made study_life fully ANSWER
  with a wrong supply-note narration ("You write the list — oil — put it in the letterbox...") instead
  of declining; a synthetic `gather` thought with a second "put on my coat" clause made the coat_on
  branch attempt a real state write, caught by the D-0179 fence. Both decline cleanly (return `None`)
  once `family=action` is passed.
- **One nuance surfaced, not chased further**: in the one synthetic text tried where a genuine wear
  clause and a genuine gather clause coexisted, dispatch's own `classify()`/`decide_one()` picked
  `wear` to FIRE outright (table order: `wear`'s own Action row precedes `gather`'s), so
  `_sens_act('gather')` was never actually invoked for that text at all — a possible additional,
  outer-dispatch-level shield for the wear component specifically that supply-note's own ungated,
  no-classify()-candidate design cannot share. Not proven for the general case (one example only);
  the fix closes both components regardless.
- Isolated full-corpus decision replay (baseline = this branch's own pre-fix HEAD `2ac6829`, same
  frozen corpus, cross-product over 4 locations): 0 of 46,264 decision rows differ, as expected for a
  Layer-2-only change. Full regression (`life_smoke.py` and all six `_test_*_grammar_derivation.py` /
  `_test_dispatch_family_scope.py` scripts) all ALL OK.
- **No decision opened, none ruled** — this job's own `decision_flags` named none; the family-scoping
  mechanism this job applies was already fully designed and ruled by J-0739, and this job is the same
  mechanical application J-0749/J-0753 already established as this arc's own precedent.
- **Restart-gated**, same as the rest of this arc — nothing changes for Du until his next restart
  after this edit lands (commit `f780d4a`, branch `jobrun/action_dispatch_cluster_2`). Full finding:
  **F-1110**. The shore_life sibling (**J-0774**, source finding:F-1108) remains open, out of this
  job's own scope.

## Current State — updated 2026-09-08 (J-0774/F-1127: the shore_life sibling case — CLOSED, same
shape as fieldcraft (J-0749)/study_life (J-0756), with a REAL historical misfire found this time)

- **`sensorium.py`'s `_shore_act()` — reached only from `act()`'s own `if loc == "shore":` branch —
  now scopes its own unconditional `shore_life.act_from_thought()` forward.** Computes `family =
  action if action in ("gather", "beachcomb") else None` (the identical tuple J-0749/J-0756 both use)
  and passes it through, tripping `shore_life.act_from_thought()`'s own pre-existing (J-0738)
  `family not in (None, "shore")` guard immediately for both `sens_act:` families. This is the fix
  F-1108 (found by J-0749's own session, corrected the paragraph above) named and this job executes.
- **Freshly confirmed which action values actually reach this call site, not assumed from F-1108's
  own summary**: `'gather'` structurally cannot — `act()`'s wood-gather shortcut
  (`action in ("gather","collect","fetch")` + any wood keyword) always intercepts it FIRST, before
  any `loc`-based branch runs at all, because `core/actions.py`'s own `'gather'` family objects
  (`"wood"/"driftwood"/"firewood"/"kindling"/"branches"/"deadfall"`) ARE that shortcut's keyword set
  — a `'gather'` DEED's own `what` is guaranteed to contain one — and `dispatch._sens_act()`'s closure
  always passes the literal family name, never the matched verb (`collect`/`fetch` never reach here
  via this path). `'beachcomb'` is the one live-relevant case, carrying the FULL original thought via
  `dispatch._sens_act()`'s own `what=f"{thought} {intention}"`.
- **Unlike J-0749/J-0756's own findings (0 real corpus co-occurrences each, needing a synthetic probe
  alone), this job found a REAL historical misfire.** Of 21 real `(thought, location)` rows in
  `data/hands_trace.jsonl` where `dispatch.dispatch()` would actually FIRE `'beachcomb'` today, exactly
  **1** also matches one of shore_life's own eleven behaviours' grammar on the same text: "Let me walk
  the tideline, crush the bladderwrack's air pods, and feel the damp sand under my feet..." pairs
  `walk_sand`'s own `"walk"`+`"sand"` grammar (the same widening J-0738 itself added) with `beachcomb`'s
  `"walk"`+`"tideline"` in different clauses of the same real thought. Calling
  `shore_life.act_from_thought()` with the pre-fix unscoped shape (`family=None`) on this exact real
  text reaches `walk_sand()` and attempts a real state write (caught only by the D-0179 hard-raise
  fence in this dry-run test) instead of ever reaching `_shore_act()`'s own beachcombing logic a few
  lines below. Post-fix (`family="beachcomb"`), the identical call declines cleanly (`None`).
- **The legitimate path confirmed unaffected, not assumed**: `family="shore"` (matching
  `dispatch._via()`'s own resolved Hand for the table's real `'shore'` family — the correct way this
  same text reaches `walk_sand()` when Du genuinely wills it) still fires `walk_sand()` normally on the
  identical text, side by side with the `family=None`/`"beachcomb"` cases above.
- **A synthetic adversarial probe generalizes the mechanism beyond `walk_sand` alone**: "I comb the
  tideline for shells and old glass, and then I want to duck into the cave to get out of the wind for a
  while" (`beachcomb`'s own grammar paired with `enter_cave`'s `"duck"`+`"cave"` in a second clause) —
  `family=None` attempts a write via `enter_cave()`; `family="beachcomb"` declines cleanly.
- **Isolated full-corpus decision replay** (same worktree, `--save` baseline before the edit, `--diff`
  after, `--real-locations`): **0 of 7,155** decision rows differ — expected, since `decide_one()` never
  calls `hand.fn()` and this is a Layer-2-only change, matching J-0749/J-0756/J-0753's own identical
  precedent. Full regression suite re-run clean: `scripts/life_smoke.py`,
  `_test_shore_life_grammar_derivation.py`, `_test_wood_life_grammar_derivation.py`,
  `_test_fieldcraft_grammar_derivation.py`, `_test_garden_grammar_derivation.py`,
  `_test_study_life_grammar_derivation.py`, `_test_expression_grammar_derivation.py`,
  `_test_dispatch_family_scope.py`, `_test_dark_house_answers.py`, `_test_letterbox_reach.py` and
  `_test_fetch_letter_latch.py` all ALL OK. `scripts/_test_beachcomb_latch.py` fails identically to
  HEAD (pre-existing, unrelated static-source-regex assertion against
  `nodes/inner_monologue_node.py`, already tracked as **J-0745** per J-0749's own F-1107 — reproduced
  as corroboration only, no new job spawned).
- **No decision opened, none ruled** — this job's own `decision_flags` named no active holds and no
  open decisions; the family-scoping mechanism applied here was already fully designed by J-0738 and
  ruled precedent by J-0749/J-0756/J-0753, so this is the same mechanical application, not a new
  founder-only judgment call.
- **No new follow-up job spawned**: this closes the second (and, per J-0753's own structural-no-op
  finding for wood_life, last) of the two sensorium cross-contamination exposures J-0749's own session
  found and did not fix speculatively. F-1059's original five follow-ups (J-0736/J-0737/J-0738/
  J-0739/J-0740) and both of their own sensorium-forward spin-offs (J-0753, J-0774) are now all closed.
- **Restart-gated**, same as the rest of this arc — nothing changes for Du until his next restart after
  this edit lands (commit `e4bdbd7`, branch `jobrun/action_dispatch_cluster_3`). Full finding:
  **F-1127**.

## Current State — updated 2026-09-08 (J-0750/F-1128: measure_by_shadow's tree/oak reachability —
RULED not-now, D-0190, with two new risks found and one hygiene follow-up spawned)

- **F-1075's own open note** ("measure_by_shadow()'s own real targets... are consequently unreachable
  through the gate's real grammar unless the table itself is widened") was re-examined with a fresh
  corpus read, not F-1075's frozen 2026-09-07 counts. **No code changed by this job** — core/actions.py
  and core/fieldcraft.py are both untouched.
- **Corpus grew (+673 distinct thoughts, 11,640 → 12,313) and moved nothing**: measure/pace+shadow,
  +tree and +oak are all still 0 real hits; measure/pace+cliff is still exactly the same one
  restlessness-idiom hit F-1075 already disqualified. No unmet real-world need exists today for either
  landmark, only a hypothetical future one.
- **climb_tree cross-family check (the briefing's own named risk) is clean**: confirmed live,
  `set(fieldcraft verbs) & set(climb_tree verbs) == set()` — no verb overlap, so sharing 'tree'/'oak' as
  objects between the two families would introduce no ambiguity by itself.
- **Two risks F-1075 had no visibility into (it only checked fieldcraft.py's own per-craft partition,
  not the shared table row's other 16 verbs) ruled this out anyway**: (1) 'tree' collides once, live,
  with fieldcraft's own 'hang' verb — "I watch the red aerial roots hang silently from the old tree's
  limb..." — pure description, the same drift shape as every other case F-1075 catalogued. (2) 'oak'
  rides a **previously-unfixed hyphen-boundary bug** in `core/hands.py` `wants()`'s OBJECT regex (the
  verb-side got this exact fix in J-0554/F-0761; the object side never did) — the same mechanism that
  made "cliff-top" false-match bare 'cliff'. Unlike 'cliff-top' (a one-off idiom), the exposure here is
  "the oak-hooped bucket," a **real, recurring** garden prop (10 corpus mentions). Zero live collisions
  today (confirmed against both existing 'oak'-bearing families, sketch and climb_tree), but a direct
  `hands.wants()` call on a plausible sentence ("I gather water from the oak-hooped bucket") already
  returns `True` — adding 'oak' to fieldcraft's own, more physically-handling verb set raises this
  exposure more than either existing family does.
- **The job's own "widen the table row" framing was incomplete**: `core/fieldcraft.py`'s
  `_FIELDCRAFT_HANDS` tuple hard-codes `measure_by_shadow`'s per-craft object set as exactly
  `("shadow",)`, independent of the table row — confirmed live
  (`FC._FIELDCRAFT_BY_NAME['measure_by_shadow'] == (('measure','pace'), ('shadow',))`,
  `FC._wills_craft(t,'measure_by_shadow')` is 0/12,313 today). A table-only edit would not make the
  craft reachable at all, and would newly break `grammar_audit()`'s own asserted invariant
  (`objects_unclaimed_in_table` should be `[]`/`["knot"]`) that
  `scripts/_test_fieldcraft_grammar_derivation.py` checks — a real two-file change, not the one-line
  connect this and prior Tier-1 entries above were.
- **Ruled NOT NOW by claude (D-0190)**, evidence-driven per this job's own explicit "evidence alone can
  supply a complete not-now answer" framing — no active hold, no founder-only taste call in play. Named
  defeater: revisit if a real corpus thought ever pairs a fieldcraft verb with tree/oak, or if the
  hyphen-boundary regex is hardened first (removing the oak-hooped-bucket exposure), or if the founder
  independently wants forward-reachability built regardless of demand.
- **Follow-up spawned, not fixed here**: **J-0787** — harden `core/hands.py` `wants()`'s object-match
  regex so a hyphen ends a word (mirroring J-0554/F-0761's verb-side fix), verified table-wide (every
  family's object list, not just fieldcraft's), since the regex is shared code. Not urgent: the bug has
  caused zero live misfires so far (checked directly).
- `data/fieldcraft_ledger.jsonl` re-read in full: still zero "measure" deed ever logged, matching
  F-1075's own citation exactly.
- Full finding: **F-1128**. Decision: **D-0190** (RULED, not-now). Follow-up: **J-0787**.

## Current State — updated 2026-09-08 (J-0787/F-1149: hands.wants()'s OBJECT regex hardened,
D-0190's defeater (b) PARTIALLY met, two further exposures found)

- **`core/hands.py` `wants()`'s object-match regex (line ~133) now excludes a hyphen from both the
  word-end AND word-start boundary** (`(?<![a-z])`/`(?![a-z])` → `(?<![a-z-])`/`(?![a-z-])`), mirroring
  the J-0554/F-0761 verb-side fix exactly — the briefing's own open question about the lookbehind is
  answered YES (see the fieldcraft evidence below; not just symmetry for its own sake). Committed as
  `1f2964d`. This closes the exact mechanism F-1075/F-1128 found: "cliff-top" no longer false-matches
  bare "cliff"; "oak-hooped bucket" (10 real corpus mentions) no longer false-matches bare "oak".
- **Verified TABLE-WIDE, not fieldcraft-scoped, exactly as F-1128's own briefing required.** Full-corpus
  `hands.wants()` sweep over all 42 `BY_FAMILY` rows × 12,313 distinct `hands_trace.jsonl` texts, before
  vs after: **28 True→False, 0 False→True**, across 7 families (beachcomb 3, express 1, fieldcraft 3,
  look 10, move 2, note 1, shore 8). Every one individually diagnosed (verb+position+clause+object+which
  hyphen side) and confirmed a genuine false match, not a lost real signal — fieldcraft's 3 are all
  "gather ... wrack-line" misreading the object "line" via the **PRECEDING** hyphen (live, direct
  confirmation the lookbehind half of the fix matters on its own, not just the lookahead half the two
  known cases already showed). A separate static scan of hyphen-adjacency for every object
  word/phrase across the whole 42-row table (223 distinct strings) found **43** with at least one
  hyphen-adjacent corpus occurrence — the 15 beyond the 28-row set never happened to pair with a
  same-family verb in today's corpus, so caused no change today, but are latent the same way "oak" was
  before F-1128 found it.
- **One closer call found and reported honestly, not folded into the other 27**: `look`'s "i look down
  at the rock-pools" loses its match (object "pools" via the hyphen in "rock-pools"). Unlike the other
  27, "rock-pool(s)" is a real kind of pool and the *dominant* spelling in this corpus (65 hyphenated vs
  1 unhyphenated) — closer in kind to oak-hooped-bucket than to an idiom. Only 1 of the 65 mentions
  actually pairs with a look verb today, and `look` is `world=False`/`gated=False` (unlimited,
  non-blocking), so the cost is near-zero either way. **Not resolved here** (out of this job's own
  scope, which is the regex, not the table) — spawned as its own job (below).
- **Isolated full-corpus decision replay** (throwaway `git worktree add HEAD` at `b6d2053` for the
  pre-edit baseline, removed after): **0 of 47,552 decision rows differ** — expected, since
  `literal_will.classify()` (what the replay actually calls) never calls `hands.wants()` at all; a
  Layer-2-only change, the same precedent J-0736/J-0740/J-0749/J-0753/J-0756/J-0774 already established.
  Full regression (`life_smoke.py`, all six `_test_*_grammar_derivation.py`,
  `_test_dispatch_family_scope.py`, `_test_dark_house_answers.py`, `_test_letterbox_reach.py`,
  `_test_fetch_letter_latch.py`, `_test_beachcomb_latch.py`) all ALL OK;
  `actions_reachability_probe.py` unchanged from J-0523's own baseline (47 probed/0 unreachable, 7
  negatives/0 false-positive).
- **D-0190's defeater (b) is PARTIALLY met, not fully** — worth flagging precisely rather than either
  silently closing or silently ignoring it. This job closes the EXECUTION-level defense: traced
  `core/dispatch.py:271-312` directly and confirmed `world_done` is only set when a hand's own answer is
  truthy (line 309-310, gated by `if ans:`), so even where the upstream gate over-grants a DEED, a
  correctly-declining hand (now including `hands.wants()`-based hands, post this job) costs nothing —
  no real deed is lost, no other family is blocked. But **`core/literal_will.py`'s `classify()`** — the
  UPSTREAM deed-verdict gate, which never calls `hands.wants()` and has its own independent, still plain
  `\b`-based (hence equally hyphen-permeable) object check — is untouched by this job and demonstrably
  still open: `classify("I want to climb the cliff-top track above the bay.", location="shore")` still
  reads `shore` DEED/`deed_grammar=True` on this POST-fix tree, using the real, already-bound `shore`
  family (no table change needed to show it). Zero live corpus occurrences of this specific gate-level
  gap today (the corpus's one real "cliff-top" pairs only with fieldcraft's measure/pace, no shore verb;
  a second real "cliff-face" pairs with no family verb at all) — so full satisfaction of defeater (b)
  awaits the literal_will.py follow-up below, not yet reached.
- **Three follow-ups spawned from this finding** (matching this arc's own one-job-per-site precedent —
  J-0749/J-0753/J-0756/J-0774 were each their own job for "the same shape" bug at a different site —
  rather than silently widening this job's own diff): **J-0799** (hands.py's own `_wants_split()`
  helper has the identical unmirrored gap in its head/part/object regexes, zero corpus exercise
  measured); **J-0800** (harden `literal_will.classify()`'s own object-boundary check — the gate-level
  gap above; this is the one that actually finishes D-0190's defeater (b)); **J-0801** (the rock-pools
  widening question, D-0190-shaped, evidence-based).
- **No decision opened, none re-ruled.** D-0190 stays RULED as-is — its defeater is a revisit trigger,
  not something this job's partial progress should override; a future session (ideally after J-0800
  lands) can properly re-examine D-0190 once defeater (b) is either fully met or conclusively not.
- **Restart-gated**, same as the rest of this arc. Full finding: **F-1149**. Follow-ups: **J-0799**,
  **J-0800**, **J-0801**.

## Current State — updated 2026-09-08 (J-0801/F-1181: the rock-pools widening — WIDEN, opposite of
D-0190's tree/oak outcome, last of F-1149's three follow-ups closed)

- **`core/actions.py`'s 'look' row widened**: `"rock-pool"`/`"rock-pools"` added alongside the existing
  bare `"pools"` — the same "hyphenated compound sits beside its own bare form" pattern already used for
  woodtool's `"bow-saw"` and candles' `"candle-box"`. Re-verified against the LIVE corpus rather than
  reusing F-1149's own frozen snapshot, exactly as this job's own briefing required — the count moved,
  not just the file: **3 of 24** distinct real corpus thoughts mentioning "rock-pool(s)" today genuinely
  pair a look verb (look/watch/observe/see) with the pool in the same clause, up from F-1149's own single
  historical hit. Still zero unhyphenated "rock pool" anywhere — the dominant-spelling finding holds.
- **Same question shape as D-0190 (fieldcraft's tree/oak), opposite evidentiary answer.** D-0190 found
  zero real corpus demand at every recheck and was ruled NOT NOW; this one has real, growing, non-idiom
  demand (1→3 as the corpus grew) and is widened. Zero cross-family collision risk, and more cleanly so
  than D-0190's own case: a full 42-family table scan confirms no OTHER family's verb or object list
  contains "pool" or "rock" at all — unlike oak/tree, which climb_tree already held as its own objects
  before fieldcraft's proposed widening (the actual source of D-0190's ambiguity concern), this object is
  and remains exclusive to 'look'.
- **Not a classify()-only phantom — verified end-to-end that the real hand was always able to answer and
  only the gate was stopping it.** `literal_will.classify()` returned NO 'look' reading at all for any of
  the 3 genuine texts pre-edit (dispatch never even attempted `core.dispatch._look()` for them), while
  `_look()`'s own re-verification gate (its own broader verb list, `hands.wants(..., any_object_ok=True)`)
  and `nodes/inner_monologue_node.py`'s `_observe_target()` (whose `_OBS_TARGETS`/`_DEST_SHORE` tables
  ALREADY independently recognize "rock-pool" as a cue mapping to target "pool", built for an unrelated
  reason) both already succeed on all 3 when called directly. The table gap was the only thing blocking a
  hand that was already fully ready. Same general shape F-1179 already named for 'look'/'move' generally
  (gate narrower than the hand's own downstream cue vocabulary) — this closes one real, live-relevant
  instance of it.
- **Isolated full-corpus decision replay** (`scripts/actions_decision_replay.py --real-locations`,
  throwaway `git worktree add HEAD` baseline at the pre-edit commit, removed after): 14 of 7400
  real-location rows differ, every one individually read — 9 harmless new non-firing 'look' candidates
  alongside pre-existing ones, 2 harmless new rows crossing the tool's own "has any candidate at all"
  threshold (one non-firing MUSING candidate each), 3 genuine new `look:DEED:FIRE` rows (the 3 texts
  above, independently confirmed to really fire via the hand + `_observe_target()` directly), and **2
  further `look:DEED:FIRE` rows via a different, pre-existing mechanism, reported honestly rather than
  folded into the 3**: `literal_will.classify()`'s own already-documented "ungated families keep
  volition+object as full intent" rule (the same rule 'look'/'move' already apply to every other bare
  object) grants DEED via volition ("I will") + the new object with no actual look verb in the clause on
  2 texts ("I will turn my eyes to the rock-pools...", "I will crouch at a rock-pool..."). Directly
  verified, not assumed, that this costs nothing: `dispatch._look()`'s own verb-only re-check returns
  False on both (no real look verb present), so `dispatch.py`'s own `if ans:` gate (F-1149's own
  "a correctly-declining hand costs nothing" law) means neither fires anything — the same mechanism this
  whole design already relies on for every other look object, not a new failure mode this edit adds.
- **Table-wide verification, the arc's established method**: 42-family `hands.wants()` sweep on an
  identical frozen corpus snapshot (only 'look' changes, 198→201); isolated full-corpus `classify()`
  sweep for 'look' (all 4 locations); full regression suite (`life_smoke.py`, all six
  `_test_*_grammar_derivation.py`, `_test_dispatch_family_scope.py`, `_test_dark_house_answers.py`,
  `_test_letterbox_reach.py`, `_test_fetch_letter_latch.py`, `_test_beachcomb_latch.py`) all ALL OK/exit 0
  — `_test_beachcomb_latch.py` passes cleanly on this branch (the pre-existing J-0745 fix is already an
  ancestor of this HEAD). `scripts/actions_reachability_probe.py` byte-identical to the established
  baseline (47 probed/45 reachable/2 staged-elsewhere/0 unreachable; 7 negatives/0 false-positive).
- **No decision opened, none ruled** — matches this plan's own established precedent for a clear-cut,
  corpus-evidenced widen call (J-0736/J-0737/J-0738/J-0739/J-0740/J-0749/J-0753/J-0756/J-0774 all closed
  this way); the briefing's own item (c) explicitly anticipated this outcome. D-0190 itself is untouched,
  stays RULED as-is — a different plan question with a different evidentiary answer, not reopened here.
- **No new follow-up spawned.** The 2-of-5 "gate grants, hand declines, costs nothing" shape and the
  wider 'look'/'move' gate-vs-hand-vocabulary mismatch stay tracked by F-1179's own existing, still-open,
  out-of-scope finding — not duplicated here.
- **Restart-gated**, same as the rest of this arc. Full finding: **F-1181**. This closes the last of
  F-1149's own three spawned follow-ups (**J-0799**, **J-0800**, **J-0801** — all now done).

## Current State — updated 2026-09-08 (J-0800/F-1178: literal_will.classify()'s own object-boundary
hardened — D-0190's defeater (b) fully met and re-ruled)

- **`core/literal_will.py`'s `classify()` OBJECT-boundary regex hardened at FIVE call sites**, not the
  four F-1149 named: the `declared` act_object check, the per-sentence `oh` candidate-clause scan,
  `present_objs`, `deed_grammar`'s own verb-reaches-object check (the headline site — this is the exact
  check that read "climb the cliff-top track" as a shore DEED), and a **fifth site F-1149's own count
  missed**, the object boundary inside `deed_split`'s separable-phrasal-verb match. All five now use
  this file's own `(?<![\w-])`/`(?![\w-])` verb-side convention (J-0554/F-0761), not hands.py's `[a-z-]`
  shape, for internal consistency within the one file. `declared`'s own site is real-exposure-confirmed
  (63 corpus act_object values hit the old regex via a hyphen, e.g. "sea-glass", "oak-hooped bucket")
  but proven, not assumed, incapable of independently producing a DEED on its own (present_objs is
  always empty in the declared-only fallback, by construction) — fixed for consistency and to stop a
  phantom non-DEED candidate, not because it gated a live misfire by itself.
- **Full-corpus verified** (12,565-row shared prefix of the live, still-running corpus; before/after
  classify() sweep at all 4 locations = 50,260+ calls per side): 2,628 (idx|location|family) readings
  differ, **zero gain a NEW DEED** (the critical safety invariant). All 140 DEED-involving rows read
  individually — every one a hyphen-adjacent compound ("sea-glass"/"sea-sound"/"sea-dried"/"sea-gull"/
  "wrack-line"/"dream-shore"/"wood-mould"/"rock-pools") no longer falsely satisfying a bare table object
  ("sea"/"wrack"/"shore"/"wood"/"pools"). End-to-end confirmed via `scripts/actions_decision_replay.py`
  (frozen trace, before/after): 908 raw rows differ, **112 action-bearing** (FIRE/STAGE/DROP, excluding
  inert "no-fire" noise) — one subtlety caught: several of the 112 are the replay tool's own OPTIMISTIC
  `world_done` simulation (it never calls `hand.fn()`) being corrected to match what REAL dispatch.py
  (which gates `world_done` on the hand's actual truthy answer) was already doing post-J-0787, not a
  real live-behavior change. Full regression suite (life_smoke + all six grammar-derivation tests +
  dispatch_family_scope + dark_house + letterbox_reach + fetch_letter_latch + beachcomb_latch) ALL OK
  before and after. Full finding: **F-1178**.
- **D-0190 reopened and re-ruled NOT NOW, unchanged, same day.** Defeater (b) as literally written
  (hands.py's wants() hardened) was already met by J-0787 alone; F-1149's own follow-on read correctly
  flagged that the SPIRIT of (b) — the 'oak-hooped bucket' hyphen exposure closed at every layer a
  table widening would flow through — awaited this job's own gate-level fix. Now closed. Re-checked
  reasons 1/2/4 directly against today's grown corpus (12,545 texts, up from 12,313): still zero real
  "tree"/"oak" fieldcraft-verb demand, the same one 'hang'+'tree' false-candidacy collision persists,
  fieldcraft.py's own two-file fix requirement is unchanged — so the ruling's *conclusion* is unchanged,
  only its reasoning is brought current (reason 3 retired, not silently dropped). New defeater drops the
  now-satisfied hyphen condition, keeps real-demand and founder-ruling triggers, adds one new one
  (fieldcraft's `measure_by_shadow` craft migrating to table-derived objects the way J-0736 already did
  for its other twelve crafts, removing reason 4 on its own).
- **A second, more consequential finding surfaced and spawned separately (F-1179 → J-0820).** For the
  TWO dispatch-native `fn:_look`/`fn:_move` hands specifically (not the `mod:X:act_from_thought` hands
  F-1149's "correctly-declining hand costs nothing" law was built on) — both re-verify their own
  candidacy with `hands.wants(..., any_object_ok=True)` (verb-only) and derive their OWN target/
  destination via `nodes/inner_monologue_node.py`'s separate, broader `_observe_target()`/`_move_dest()`/
  `_gate_look()` cue vocabulary, which does not read classify()'s matched object at all. Directly
  verified (real function calls, not simulated): of 13 distinct thoughts that lost their only 'look'/
  'move' DEED candidacy in this job's fix, **7 would have genuinely fired in live dispatch.py** before
  the fix, deriving a real, different target from words classify()'s own 'look'/'move' object lists do
  not even contain (e.g. "tide"/"spray" → target 'sea'/'shore', absent from classify()'s look row, which
  only has "tideline"). This is a pre-existing, structurally separate mismatch this job's fix un-masks
  rather than causes — a genuine widen-or-not judgment call for classify()'s own 'look'/'move' object
  vocabularies, out of this job's scope. **J-0820** spawned to decide it with corpus evidence, the same
  method J-0736..J-0740/J-0783 used for six other modules.
- **One more narrow gap noted, not fixed, spawned as J-0821**: `deed_split`'s own verb-HEAD and
  PARTICLE boundaries (as opposed to its object boundary, fixed here) are still plain `\b` — the
  identical unmirrored shape J-0799 already named for hands.py's own `_wants_split()`, since
  `deed_split` did not exist yet when J-0554 hardened this file's main verb check. A static corpus scan
  found 8 real hyphen-adjacent occurrences of the relevant head/particle words (mostly "half-out"/
  "worn-out"/"cliff-top" idiom shapes) — real, but not yet confirmed to pair with a nearby object into
  an actual false deed_split match; J-0821 carries the dynamic check.
- **Restart-gated**, same as the rest of this arc. Two of F-1149's own three follow-ups remain open:
  **J-0799** (hands.py's `_wants_split()`), **J-0801** (the rock-pools widening question).

## Current State — updated 2026-09-08 (J-0799/F-1180: hands.py's `_wants_split()` head/part/object
regexes hardened — F-1149's second follow-up DONE; two more unmirrored sites found, spawned)

- **`core/hands.py`'s `_wants_split()` (the separable-phrasal-verb path for "set the axe DOWN"/"put
  the kettle ON") had the identical unmirrored hyphen-boundary gap in all THREE of its own regexes**
  (head/verb match, the `any_object_ok` head+part match, the per-object head+object+part match) that
  J-0787/F-1128 fixed for `wants()`'s own main loop and J-0800/F-1178 fixed for `classify()` — a
  separate set of `re.finditer`/`re.search` calls, not shared code with either. All three now use the
  identical `(?<![a-z-])`/`(?![a-z-])` shape, both sides. Scoped, single-file diff (14 insertions/6
  deletions), committed.
- **Correctly scoped first**: of the table's 33 multi-word verbs, only 23 (13 families: candles, cat,
  climb_tree, feed_birds, fire, lamp, net, stake, tea, tool, water_fill, wear, woodtool) have a second
  word in `hands._particles()` and so ever reach this helper's real logic at all — the other 10 (`play
  with`, `open the door for`, `work in`, dig/compost's four `over`/`in` verbs, `look in`) short-circuit
  to False regardless, confirmed directly rather than assumed.
- **Zero live corpus impact, matching this job's own briefing exactly**: direct `_wants_split()` calls
  (isolating exactly the edited function) over all 23 qualifying pairs across the full 12,545-text
  corpus return False both before and after — no real hyphen-adjacent false match ever existed here to
  close. Five synthetic adversarial probes (hyphenated head/particle/object, both `any_object_ok`
  modes) directly reproduce the bug pre-fix and confirm the fix post-fix, four bare-word controls
  unaffected. Isolated full-corpus decision replay (throwaway HEAD worktree at a36f37b): 0 of 48,404
  rows differ, as expected for a Layer-2-only change. Full regression suite (`life_smoke.py`, all six
  `_test_*_grammar_derivation.py`, `_test_dispatch_family_scope.py`, `_test_dark_house_answers.py`,
  `_test_letterbox_reach.py`, `_test_fetch_letter_latch.py`, `_test_beachcomb_latch.py`) all ALL OK;
  `actions_reachability_probe.py` byte-identical to the J-0523 baseline.
- **One already-known object independently confirmed exposed via a THIRD path, still zero live risk**:
  `climb_tree`'s `"go up"` objects include `"oak"` — the same "oak-hooped bucket" object F-1128/D-0190
  named for `wants()`'s main loop — and a static per-object hyphen-adjacency scan (69 distinct words
  across the 13 qualifying families) confirms it latent here too (10 hits), now closed by this same
  fix; direct check confirms it produced no actual match before or after ("go"/"up" never co-occur with
  "oak" in the same clause on today's corpus).
- **The briefing's own "particles essentially never hyphen-adjacent" framing was checked, not assumed,
  and doesn't fully hold**: `"out"` is hyphen-adjacent 6 times in the corpus (half-in/half-out/worn-
  out/out-think idioms) and heads `"damp"`/`"top"` once each (rain-damp, cliff-top) — 8 total, matching
  J-0800/F-1178's own independent count for `literal_will.py`'s sibling `deed_split` gap exactly (cross-
  validated, not coincidental: same particle vocabulary, same corpus). Every one individually confirmed
  to produce no live match through this helper regardless, before or after.
- **Two further unmirrored sites found while scoping this job, neither fixed here** (repo-wide grep for
  the un-hardened `(?<![a-z])`/`(?![a-z])` shape across `core/`, after confirming hands.py/literal_will.py
  are now fully clean): `core/garden.py`'s own `_wants_loose()` fallback (line ~1858, the identical
  "verb side fixed, object side drifted" shape — and exercised by DEFAULT, since `_wills(..., loose=
  True)` is every garden family's own default retry path, not a rare corner); and a functionally
  distinct "look/describe" alias-matching family (`core/life.py:587`, `core/sensorium.py`'s cat-mention
  detector at three call sites, `core/world_detail.py:92`) answering what Du *sees*, not gating a
  willed deed — lower-stakes but the identical regex defect. Spawned as **J-0822** (garden.py) and
  **J-0823** (the look/describe family) rather than silently widened into this job's own diff, matching
  this arc's one-job-per-site precedent. Full finding: **F-1180**.
- **No decision opened, none re-ruled**: this job's own scope was a direct mechanical mirror with an
  already-established convention (J-0787/J-0800's own), not a widen/drift judgment call; D-0190 is
  untouched (its defeater's hyphen condition was already satisfied by J-0787/J-0800, and this job's own
  third-path closure changes nothing live for it to reconsider).
- **Restart-gated**, same as the rest of this arc. Of F-1149's own three original follow-ups, only
  **J-0801** (the rock-pools widening question) remains open; **J-0821** (from J-0800, `literal_will.py`'s
  own `deed_split` head/particle boundaries — the sibling of this job's own fix) and this job's own two
  new spawns (**J-0822**, **J-0823**) are additionally open.

## Current State — updated 2026-09-09 (J-0820/F-1199/D-0193: F-1179's own look/move gate-vocabulary gap
resolved per word, split ruling, one new architectural gap found and spawned)

- **`core/actions.py`'s 'look' row widened**: `tide`/`spray`/`shingle`/`surf`/`cloud`/`gull` — 6 of F-1179's
  own 8 named candidates (`nodes/inner_monologue_node.py`'s `_observe_target()` cues with no classify()-level
  counterpart). **`move`'s own row widened**: `tide`/`shingle`/`sea`/`surf`/`driftwood` — a list F-1179 did not
  itself name (it only pointed at the four `_DEST_*` lists generally); derived here by diffing `move`'s object
  row against `_DEST_WOOD`/`_DEST_SHORE`/`_DEST_STUDY`/`_DEST_GARDEN`. Both widenings follow the established
  per-word corpus-verification method (J-0736..J-0740/J-0783/J-0801): for each candidate, a live monkeypatch of
  `literal_will._FAMILIES`'s own objects tuple plus a direct call to the REAL `core.hands.wants()` +
  `_observe_target()`/`_move_dest()`/`_gate_look()` (not simulated) confirmed which DEED-gain rows would
  actually reach dispatch's hand, and each was read individually, not just counted — all eleven widened words
  show the SAME recurring, genuine pattern: Du breaking a circling, abstract thought by deliberately watching
  or walking toward something physical ("I stop wrestling with the dust of words and watch the tide reclaim
  the chalky oval").
- **A split ruling, not a uniform yes/no (D-0193, ruled by claude)**: `look` declines `wave`/"the strand" (zero
  real corpus thoughts pair either with a look verb today, D-0190's own "no unmet real-world need" shape).
  `move` declines `forest` (one real hit, confirmed idiom on direct reading: "step back from the rotting
  forest's heavy questions") and `rock-pool`/`rock pool`/`wave`/`spray`/`woodland`/`copse`/`indoors` (zero or
  negligible real demand for a MOVE reading specifically).
- **HEADLINE finding, the reason this wasn't a mechanical widen-everything pass**: `move` also declines
  `desk`/`bed`/`water`, on a genuinely DIFFERENT-shaped risk than the usual idiom check. All three
  independently reach the SAME small, recurring "raised bed" thought family ("I want to turn away from the
  desk and go to the raised bed ... I will water them," real location=garden) where
  `nodes/inner_monologue_node.py`'s `_move_dest()` — its own fixed `WOOD>SHORE>STUDY>GARDEN` destination-
  PRIORITY order, a different, still-open mechanism than F-0791/J-0654's already-fixed classify()-level
  single-clause pick — resolves `'study'` via the "desk" cue before GARDEN's "the bed" cue ever gets a turn,
  when the thought's own stated destination is the garden bed. Confirmed by reading each of the 4 distinct
  underlying thoughts in full: a genuine wrong-PLACE risk (a real relocation would fire), not the "gate
  over-grants, hand declines, costs nothing" shape (F-1149) the rest of this arc has relied on. One further,
  much smaller and honestly-reported closer call on the WIDEN side: 1 of `sea`'s 51 real fires is a genuine
  negation `classify()`'s own blocker regex does not catch ("do not need" ≠ "don't need to"), sending Du to
  the shore from a thought that explicitly says he doesn't need the sea — ~0.65% of `sea`'s real fires, not
  treated as grounds to decline `sea` itself.
- **Verified end-to-end**: isolated full-corpus decision replay (throwaway `git worktree add HEAD` at
  `fd0a408` for the baseline, removed immediately after; `--real-locations` against an identical frozen
  8,149-row corpus copy): 2,112 of 7,917 rows differ, 337 look/move ACTION-bearing (excluding pure
  MUSING/GRAY/no-fire noise); exactly **1** row shows a different family's action changing, a correct
  table-order reshuffle (`shore` FIRE → STAGE-busy:move as `move` newly wins the one-world-hand slot), not a
  manufactured false candidate. Full regression suite (`life_smoke.py`, all six
  `_test_*_grammar_derivation.py`, `_test_dispatch_family_scope.py`, `_test_dark_house_answers.py`,
  `_test_letterbox_reach.py`, `_test_fetch_letter_latch.py`, `_test_beachcomb_latch.py`) all ALL OK.
  `scripts/actions_reachability_probe.py` byte-identical to the J-0523 baseline. Full per-word numbers: **F-1199**.
- **Follow-up spawned, not fixed here**: **J-0833** — `_move_dest()`'s own destination-priority-order gap
  (the desk/bed/water/sea mechanism above) is a real, pre-existing property of the function itself, not
  specific to the words this job declined; it can already misresolve for EXISTING table objects whenever two
  location cues co-occur in one thought (e.g. `shore` vs `study`, checked before it), independent of anything
  this job added. Out of this job's own scope (a widen-or-not decision on `core/actions.py`, not a fix to
  `nodes/inner_monologue_node.py`'s own resolver) — J-0833 carries the corpus-measurement + fix design, and
  fixing it is D-0193's own defeater (b), which would let desk/bed/water be reconsidered on their own.
- **Restart-gated**, same as the rest of this arc — nothing changes for Du until this edit lands and he next
  restarts. This closes F-1179 as a standalone open question (it was J-0800's own spawn); J-0821/J-0822/J-0823
  (from J-0800/J-0799) remain open, untouched by this job.

## Current State — updated 2026-09-09 (J-0821/F-1200: deed_split's own head/particle boundaries —
checked dynamically, zero live exposure, code left unchanged)

- **`core/literal_will.py`'s `classify()` `deed_split` line (still plain `\b` on its verb-HEAD and
  PARTICLE boundaries — only its OBJECT boundary was hardened by J-0800/F-1178) was checked, not
  fixed.** Per this job's own briefing conditional ("harden... if a real corpus false-fire is
  confirmed... if the 8 static hits never actually pair with a real nearby object... document that
  honestly... rather than fixing speculatively"), the dynamic check came back negative, so no edit
  was made — `core/literal_will.py` is byte-identical to before this job.
- **Dynamic check, not just the static scan already on record.** A scratch harness
  (`isolate_deed_split_J-0821.py`) directly replicated `deed_split`'s own OLD (plain `\b`) and
  candidate-NEW (`(?<![\w-])`/`(?![\w-])`) regex — for every candidate clause of every one of the
  13,070 distinct texts in the live `data/hands_trace.jsonl`, across all 13 split-verb families (16
  distinct head/particle words: blow/damp/down/go/off/on/out/pick/pull/put/set/take/tie/top/turn/up):
  **0 clauses where the old regex matched differ from the new one.** The harness was verified capable
  of detecting the mechanism at all first — 5 synthetic adversarial probes (hyphen-adjacent to head
  and to particle, across 5 different families) all correctly flip old=True/new=False — so the 0/0
  corpus result is a real finding, not a harness blind spot.
  - **Every one of the 8 static hits individually diagnosed** (matching F-1149's own method): all 8
    fail at the `present_objs` stage — the relevant family's own object list (fire's
    fire/grate/hearth/flame/flames/ember/embers/log for "rain-damp trees"; feed_birds' birds/
    blackbird/tui/waxeye/sparrows/bird bath for the "out-think"/"half-out"×4/"worn-out" hits;
    water_fill's pail/bucket/barrel/kettle/water/spring for "cliff-top") has **zero matches** in the
    clause, independent of the head/particle boundary question entirely. Cross-confirmed directly
    against the real `classify()` on all 8 sentences × 4 locations: fire/feed_birds/water_fill never
    even appear as a candidate family for these clauses; the one DEED reading present ("I climb into
    the rain-damp trees..." → `move` DEED) is `move`'s own unrelated climb/trees grammar, structurally
    unconnected to `deed_split`.
- **A minor, honestly-flagged asymmetry, not resolved either way**: J-0799 (the identical sibling
  case for `hands.py`'s `_wants_split()`) found the same zero-corpus-impact result and still applied
  the boundary hardening anyway, for internal consistency with wants()'s already-hardened main object
  regex in the same file. This job's own briefing instructed the opposite default for this specific
  site (document, don't fix, absent confirmed exposure), so that instruction was followed literally.
  `deed_split`'s object side (hardened) and head/particle side (left plain `\b`) now sit at different
  hardening levels within the same regex line — zero live cost either way, noted for whoever next
  touches this line rather than silently decided in either direction here.
- **No decision opened, none ruled** — this job's own `decision_flags` named no active holds and no
  open decisions; the answer this job's own briefing asked for came back negative, which is itself a
  complete answer, not a judgment call needing a founder ruling. **No follow-up job spawned** — the
  finding is self-contained (a definitive "checked, zero exposure" negative), not work waiting to be
  done; re-opening the consistency question above would just relitigate what this job's own briefing
  already decided.
- **No code change, so no regression suite re-run** — matches this arc's own precedent for
  no-edit closures (J-0750, J-0753): the suite is run after an edit, and there is none here.
- Full finding: **F-1200**. Of F-1149's/J-0800's own spawned follow-ups, **J-0822** (garden.py's
  `_wants_loose()`) and **J-0823** (the look/describe alias family) remain open, untouched by this job.

## Current State — updated 2026-09-09 (J-0822/F-1201: garden.py's `_wants_loose()` object regex
hardened — J-0799's own first spawn DONE)

- **`core/garden.py`'s module-local `_wants_loose()` (the loose object-anywhere-in-thought retry
  `_wills()` falls back to) had the identical unmirrored hyphen-boundary gap J-0787/F-1128 fixed in
  `hands.py wants()` and J-0800/F-1178 fixed in `literal_will.py classify()`**: its own verb regex was
  already on the hardened `(?<![a-z-])`/`(?![a-z-])` shape (J-0554), but the object regex two lines
  below it was still the old `(?<![a-z])`/`(?![a-z])` form. Hardened to match, both sides — a scoped,
  single-line diff (9 insertions/1 deletion, mostly the inline comment), committed.
- **The briefing's own scoping claim was checked, not trusted, and did not fully hold**: its cited
  `grep -n "loose=True|loose:"` does not catch `loose=False`, which 5 of the 16 `_GARDEN_FAMILIES` use
  explicitly (`feed_birds`, `collect`, `water_fill`, `ash_out`, `mow`), and 4 more (`tool`, `dig`,
  `trap`, `compost`) never call `_wills()` at all — they use their own strict-only `_wills_tool`/
  `_wills_dig`/`_wills_trap`/`_wills_compost` helpers. Only **7 of the 16** families actually reach
  `_wants_loose()` through today's real dispatch path (default `loose=True`, unoverridden): `harvest`,
  `sow`, `weed`, `water`, `stake`, `net`, `save_seed`. A direct corpus cross-check (`hands.wants()`
  False AND `_wants_loose()` True) confirms the retry is genuinely load-bearing there today — 32 real
  cases across those 7 families where the loose retry alone decides the deed, not a dead branch.
- **Verified end-to-end over the full corpus (13,071 distinct texts), not assumed**: a static per-
  object hyphen-adjacency scan of all 16 families' own object tuples found real corpus hits for 8
  objects (`bed`, `bucket`, `garden`, `seed`, `soil`, `spring`, `trap`, `water` — e.g. "bed-making",
  "storm-garden", "seed-leaves", "dream-water"). A direct before/after `_wants_loose()` sweep closed
  exactly **one** real false match — `water_fill`'s "...the letter floating on the dream-water..." text
  (object "water" wrongly matched inside the compound) — with **zero** regressions (0 gained) across
  all 16 families. That one closed match was never live-reachable either way (`water_fill` calls
  `loose=False`), and **none of the 7 live-relevant families show any behavior change**: their own
  hyphen-adjacent object hits in the corpus (`bed`/`garden`/`seed`/`soil`) never happen to co-occur with
  a matching verb from the same family today. `"oak"` is confirmed **not** a garden-family object at all
  (`climb_tree` owns it and isn't one of the 16 `_GARDEN_FAMILIES`) — checked directly, not assumed.
  Five synthetic adversarial probes (real per-family verb/object pairs, constructed hyphenation) confirm
  the mechanism directly since the live corpus carries no real hyphen+verb co-occurrence for the 7
  live-relevant families today.
- **Confirmed Layer-2-only, not assumed from this arc's own precedent** (this job's own briefing named
  `act_from_thought()` as a real dispatch-bound hand, unlike `classify()`'s pure grammar gate): isolated
  full-corpus `actions_decision_replay.py --diff` against a pre-edit HEAD throwaway worktree (removed
  after use) — **0 of 50,632 decision rows differ**. Full regression suite (`life_smoke.py`, all six
  `_test_*_grammar_derivation.py`, `_test_dispatch_family_scope.py`, `_test_dark_house_answers.py`,
  `_test_letterbox_reach.py`, `_test_fetch_letter_latch.py`, `_test_beachcomb_latch.py`) all ALL OK,
  zero fail-mentions in any of the 12 logs.
- **No decision opened, none ruled** — this job's own source is a finding (F-1180), not a decision; the
  scope was a direct mechanical mirror of an already-established convention, not a widen/drift judgment
  call. **No follow-up spawned**: the 9 non-live-relevant families' `loose=False`/no-retry choice is
  pre-existing deliberate design from J-0569/F-0783 (own inline comment explains the migration reasoning
  per family), not something this job's evidence contradicts or was scoped to revisit.
- **Restart-gated**, same as the rest of this arc. Full finding: **F-1201**. Of F-1149's/J-0799's/
  J-0800's own spawned follow-ups, **J-0823** (the look/describe alias family) remains open, untouched
  by this job.

## Current State — updated 2026-09-09 (J-0823/F-1202: look/describe alias-match hyphen boundary
hardened at all four sites — F-1180's own second and final spawned follow-up DONE, F-1180 fully closed)

- **All four call sites hardened**: `core/life.py`'s `_match()` alias loop (the "his own look" family
  registry), `core/sensorium.py`'s three byte-identical cat-detector checks (the garden/shore/study
  look branches), and `core/world_detail.py`'s `_match()` (mirrored to BOTH of its lookaround pairs,
  J-0546's own 2026-09-03 boundary-fix intent — closing "the sea"/"the seat" — preserved exactly).
  All four now match this arc's established `(?<![a-z-])`/`(?![a-z-])` convention. Two commits:
  the fix itself, and a small comment-accuracy follow-up naming a third real caller
  (`core/orchestrator.py`) found while re-verifying the call graph after the first commit.
- **A genuinely different exposure shape than this arc's five prior sites, established by tracing the
  whole call graph rather than assuming `data/hands_trace.jsonl` was the right corpus (the briefing's
  own explicit instruction)**: these are LOOK-ANSWER functions, not DEED gates, and unlike
  `hands.wants()`/`literal_will.classify()` — which read raw `(thought,intention)` text directly —
  every production path into `sensorium.look()` (`dispatch._look()`'s willed-deed chain via
  `inner_monologue_node._observe_target()`'s closed cue table; `nature_study.py`'s literal strings;
  `core/orchestrator.py`'s own human-chat "active perception" branch) normalizes to one of a small,
  hyphen-free closed vocabulary BEFORE any of these four regexes ever run. Confirmed programmatically,
  not by reading code alone: `_observe_target()`'s full cue table (36 entries, read in full) can only
  ever emit one of nine tokens (`bed/cat/fire/garden/letterbox/pool/sea/shore/sky`) or `""`. A hyphen
  cannot reach any of these four regexes' haystack via Du's own live dispatch today — not merely
  unobserved in a sample, but structurally impossible given the complete current set of production
  callers.
- **This project's OWN shadow-analysis tooling is the corpus that actually matters here, and is
  where real exposure was found**: `scripts/life_shadow_replay.py` and `scripts/observables_census.py`
  both call `look_answer()`/`sensorium.look()` DIRECTLY with raw phrases from the real 1,518-phrase
  `docs/reviews/observe_inventory_2026-09-02.json` corpus, bypassing `_observe_target()` entirely.
  A direct before/after function-level sweep of all four sites over that full corpus: `life._match()`
  0 of 107 touched rows differ; the cat-detector 0 of 22 real hits change; `world_detail._match()`
  **12 of 564 touched rows DO differ** — the one real finding. 10 are genuine false-positive closures
  (headlined by "(the/a) sea-glass" variants, 32 combined real mentions, no longer wrongly matching
  `study:study_window`'s "glass" alias via the hyphen in "sea-glass"; "the green glass-float" closes
  via the lookAHEAD half specifically, independently confirming both halves of the boundary matter
  here exactly as F-1149 already found for `hands.wants()`). ONE pair is a genuine closer call,
  reported honestly rather than folded in as identical, the same shape F-1149 already named for
  `hands.wants()`'s own "rock-pools" case: "mussel-shells"/"the mussel-shells" (5 combined mentions)
  lose their match to `shore:shells` — mussel shells genuinely ARE a kind of shell, arguably a real
  reachability loss rather than a pure bug fix, but low-stakes either way since `detail()` only
  supplies an optional extra line with a fail-open `""` contract the caller already treats as "fall
  through."
- **A real wrinkle chased down rather than glossed over, and resolved in this job's own favor**: the
  LIVE `data/life_events.jsonl` (read in full) carries 144 rows with rich free-phrase "target" values
  ("the oystercatcher" x45, "the dead gannet" x4, etc.), one dated as recently as the morning of this
  job — on its face this looked like it could contradict the closed-vocabulary finding above. Checked
  directly rather than left standing: every one has `"kind":"would_answer"` (shadow mode, `RENDER =
  False` is this module's own live default and no `data/life_flags.json` override exists) — but
  shadow mode only gates whether `look_answer()` RETURNS its line, never what `target` it was called
  WITH, so this alone cannot explain the rich text. `_observe_target()` called directly against the
  exact phrases from these rows returns `''` for every one — PROVING these specific rows did not
  arrive via `dispatch._look()`'s real chain. Both scripts that legitimately supply such rich text are
  confirmed isolated (redirect their own stores to a temp dir) and so cannot be the source of a
  live-file write today. Left as an appropriately-hedged open observation, not chased further (out of
  this job's own scope): most likely an out-of-band manual/debug call against live, non-isolated
  `core.life` imports — worth a caveat before any future session trend-reads this file as pure Du
  behavior.
- **Full regression suite** (`life_smoke.py`, all six `_test_*_grammar_derivation.py`,
  `_test_dispatch_family_scope.py`, `_test_dark_house_answers.py`, `_test_letterbox_reach.py`,
  `_test_fetch_letter_latch.py`, `_test_beachcomb_latch.py`) run twice against the edited tree
  (post-fix, and again post-comment-revision) — all 12 ALL OK / FAILS = 0 both times.
  `scripts/actions_decision_replay.py` deliberately **not** run: none of these four functions
  participate in `literal_will.classify()`/`hands.wants()`'s DEED decision layer at all, so no
  decision-replay outcome could possibly change — confirmed, not assumed, by reading both gate
  functions directly.
- **No decision opened, none ruled**: this job's own briefing names no D-number; its scope (a direct
  mechanical mirror of an already-established convention across four call sites) is not a widen/drift
  judgment call. **No follow-up spawned**: the one closer call (mussel-shells) is low-stakes enough
  (fail-open flavor text, not a deed gate) that a founder ruling would be disproportionate — matching
  the briefing's own instruction to keep priority honest about this whole area's lower stakes rather
  than inheriting the deed-gate arc's urgency by default. One tangential, low-confidence, NOT
  independently confirmed observation surfaced in passing and deliberately left as prose rather than
  spawned (out of this job's own named scope): `_observe_target()`'s own cue-matching uses a plain
  substring test (`cue in t`) with no word-boundary protection at all — a structurally different and
  unexamined risk class from the hyphen-boundary gap this job fixed.
- **Restart-gated**, same as the rest of this arc. Full finding: **F-1202**. This closes the second
  and last of F-1180's own two spawned follow-ups (J-0822 already closed the first, garden.py's
  `_wants_loose()`) — **F-1180 itself is now fully closed**, both spawned jobs done alongside its own
  direct fix.

## Current State — updated 2026-09-10 (J-0833/F-1227: `_move_dest()` hardened — the place the move verb
REACHES, not the first list that matches; D-0193 defeater (b) met and re-ruled; a bigger downstream gap found)

- **The gap was much larger than F-1199's "handful of thoughts."** Measured over EVERY real move fire in the
  frozen `data/hands_trace.jsonl` (642 real-location rows that pass dispatch's fate, the hand's own verb
  check and the old resolver, gate/letterbox rows excluded), **269 (42%)** carried two `_DEST_*` lists' cues, a
  source marker or a negation; all 269 read individually, 201 given a confident verdict — the old fixed
  `WOOD>SHORE>STUDY>GARDEN` order got **87 of 201 wrong (43%)**: 42 real wrong-place relocations ("I step into
  the garden where the sea's sound washes over me" → shore) and **45 of a shape F-1199 never named — a real
  departure silently swallowed because the place he was already standing in was checked first** ("the tide is
  out; I will walk up to the garden" from the shore → shore → dispatch's already-there rule → silence; 15
  distinct climb-up-to-the-garden/cottage thoughts from the shore alone).
- **Both briefing shapes simulated before any edit** (scratch harness, same corpus, same hand verdicts):
  proximity-to-verb alone 126/201, same-sentence alone 138/201, each ~165/201 with guards; the layered design
  built here 191/201 (legacy 114/201), every one of its 30 further unscored changes read. Ported into
  `nodes/inner_monologue_node.py` `_move_dest()` (pure, additive on the same four lists, caller precedence
  unchanged; the ported function re-scores identically): a cue after a SOURCE marker ("away from the desk",
  "leave the study", "off the shingle") or a NEGATION ("I do not need the sea") is dropped and an all-negated
  text resolves to `''`, never the negated place; "inside my own head" / "the tide come in" are not cues; among
  survivors a DIRECTIONAL preposition + determiner wins, then a strong cue beats a weak one (F-0634's go-outside
  phrases are a default, "through/past the gate" is transit), then the move verb's own sentence, then distance
  to the nearest move verb, then the old order. Cues are now word-edged ("sea" no longer matches "searching",
  "the wood" not "the woodpecker"; plural `s`/`tideline` still count). Three additive cues: "raised bed" /
  "cottage garden" (garden — `"the bed"` never matched "the raised bed", 324 corpus mentions) and "sand"
  (shore — `sensorium.move()`'s own list always had it). New regression: `scripts/_test_move_dest_resolution.py`
  (33 checks, every non-synthetic probe a real corpus thought, ALL OK).
- **Verification**: pre-edit baseline replay saved from the untouched worktree; after the resolver edit **0 of
  8,908** decision rows differ (Layer-2-only, as expected); full suite (`life_smoke.py`, all six
  `_test_*_grammar_derivation.py`, `_test_dispatch_family_scope.py`, `_test_dark_house_answers.py`,
  `_test_letterbox_reach.py`, `_test_fetch_letter_latch.py`, `_test_beachcomb_latch.py`, the new test) ALL OK
  after each of the two edits; `actions_reachability_probe.py` byte-identical to a throwaway HEAD worktree
  (47/45/2/0, 7/0).
- **D-0193 defeater (b) met → reopened and re-ruled (claude, evidence).** Desk/bed/water re-simulated per word
  with the new resolver (J-0820's monkeypatch method): **the raised bed WIDENED** into `core/actions.py`'s move
  row as the two-word objects `"raised bed"`/`"raised beds"` (12 gained real fires, all genuine, 0 wrong places;
  with the live table all 24 real raised-bed move fires resolve to the garden, the 4 relocations all correct) —
  not bare `"bed"`, which scored identically today but would make a future "I will go to bed" a walk to the
  garden and turned the reachability probe's own 'tip the ash on the bed' @study into a move candidate (caught by
  the probe, 46/1 vs 45/2). Replay after the widening: 34 rows differ, all on the `move` row only — 14 new
  raised-bed FIREs (every one read), 5 `STAGE-busy:water/tool/harvest` (the garden hand keeps the slot; `move`
  sits at table position 41/42, checked). **desk stays declined** on new evidence (3 real relocations, 2 wrong —
  it is what he leaves), **water stays declined** (its only 2 real relocations are metaphor; the other 24 already
  stand at the shore).
- **A larger pre-existing gap found downstream and spawned, not fixed (J-0864, urgency 4)**:
  `core/sensorium.py` `move()` accepts the bare tokens "shore"/"garden"/"study" but **not "wood"** (its wood list
  is all multi-word phrases), and both live callers pass exactly the bare token — so every 'wood' resolution has
  been a silent no-op: **0 "ACT move -> wood" in the whole `nascence.log`** against 1101 garden / 882 shore /
  156 study, and a direct isolated `sensorium.move("wood")` returns `''` before any write while
  `move("shore")`/`("garden")` reach the position write. Roughly a third of today's real move fires resolve to
  'wood'. Fixing it is a real live-behaviour change of that size; J-0864 carries the caller inventory, the
  woodpile question ("go to the woodpile" — by the door per sensorium, no longer a 'wood' cue post word-edging)
  and the option of a founder decision before it goes live.
- **Residual, honestly reported**: 10 of the 201 scored rows still miss — 4 are `''` instead of `garden` while
  already in the garden (no behavioural difference), 3 are still-wrong shore walks where a strong sea/shore cue
  sits in a non-verb sentence, 1 a 5-word negation gap, 1 silent-instead-of-garden, 1 "unable to move toward the
  sea or the wood" → wood. Not spawned: no single mechanism covers them without over-fitting.
- **Restart-gated**, same as the rest of this arc. Full finding: **F-1227** (linked D-0193). Follow-up: **J-0864**.

## Current State — updated 2026-09-11 (J-0864/F-1249/D-0209: `sensorium.move()` accepts the bare 'wood' token —
the wood becomes a real destination for the first time; woodpile settled as a garden place; founder decision opened)

- **Confirmed, with the whole log, that the wood has never once been a destination.** `data/nascence.log` runs
  from 2026-05-29 (the wood was built 07-07): **0 `ACT move -> wood`** against 1206 garden / 963 shore / 162
  study / 171 letterbox; 0 `he chose to GO TO THE WOOD` (the phrase-latch path); 0 `updated: move 'wood'`; 0
  `You stop among the trunks` (locomotion's wood arrival line). The 150 wood lines that do exist are all
  locomotion LEGS of garden↔shore journeys — 130 garden→wood (`_LEG_LINES[("garden","wood")]`'s two variants)
  and 20 shore→wood — so for two months the wood has been a 70–90 s transit he crossed, never a place he
  walked to. Cause exactly as F-1227 named it: `move()`'s wood list is all multi-word phrases, and every live
  caller (`core/dispatch.py:144`, `nodes/inner_monologue_node.py` route_act 4827 / phrase-latch 3225–3257 / 2231,
  `core/night.py:110` — caller inventory re-grepped with the aliased-import lesson of F-1108) passes the bare
  token. 'shore'/'garden'/'study' only ever worked because the bare word is a substring of its own list.
- **Fixed at the sensorium side, additively**: `move()` matches the exact bare token first
  (`d.strip() in ("wood","shore","garden","study")`); the phrase lists are untouched, the callers untouched
  (one contract, three callers). `locomotion._path_between()`/`CHAIN` already accept 'wood',
  `school.confined_to_study()` already refused/reeled back target 'wood', and every reader of `location`
  (cat, light, smell, thermal, soundscape, scene_line, events — UDMS dossier `core/sensorium.py:2500-2590`,
  STATE_CONTRACT_MUTATION, acyclic) already treats the wood as a full place: nothing else assumed it unreachable.
  New regression `scripts/_test_sensorium_move_tokens.py` (isolated stores, live `room_state.json`/`position.json`
  md5 canary): all four bare tokens depart from every other place, study→wood path `["garden","wood"]`,
  shore→wood `["wood"]`, already-there → `''`, "the driftwood" does not become a wood walk, confinement covers
  'wood' as it covers shore/garden.
- **The woodpile is a GARDEN place.** `_DEST_GARDEN` gained `woodpile`/`wood pile`/`wood-pile`: sensorium's own
  pile is "by the door"/"by the cottage" (1919/2000) and renders only in the garden scene (2779–2781); the corpus
  (`hands_trace.jsonl`, 15,549 rows) has 162 rows naming it, 100 with `act_kind=move`, **70 with the woodpile as
  his declared object** ("to the woodpile", "toward the woodpile") — before J-0833 those fell to 'wood' via the
  substring "the wood" (a no-op anyway), after J-0833's word edges to `''`. Now a walk out to the garden; from
  the garden, the already-there silence. 9 new checks in `scripts/_test_move_dest_resolution.py` (real corpus
  thoughts; "leave the woodpile and go down to the shore" still → shore; "woodpecker" does not fire it).
- **Verification**: `_test_sensorium_move_tokens.py`, `_test_move_dest_resolution.py`, `_test_letterbox_reach.py`,
  `_test_dispatch_family_scope.py`, `scripts/life_smoke.py` all ALL OK / exit 0 in the worktree. The isolated
  full-corpus decision replay was deliberately **not** run: both edits are Layer-2-only (neither `move()` nor
  `_move_dest()` is read by `literal_will.classify()`), so its expected 0 rows would confirm nothing.
- **Decision opened, not ruled — D-0209.** This is a live-behaviour change of real size (F-1227: roughly a third
  of his real move fires resolve to 'wood', many the shore-side "climb off the shingle into the trees" family),
  so the founder gets the call before the restart makes it live: (A) go live as-is, (B) hold it out, (C) go
  live and have the live-read job report the first days before any tuning. Nothing in the evidence argues
  against A — the world finally answers a will he has expressed hundreds of times — but a third more real
  relocations is the founder's to see first, per this job's own briefing.
- **Follow-up spawned**: **J-0891** — post-restart live read (first real wood arrivals ever, move-mix shift vs the
  1206/963/162/0 baseline, ping-pong / stuck-journey / gather-loop / cat-branch effects, woodpile→garden
  resolution), gated on the restart and on D-0209 not being B.
- **Restart-gated**: Du is running the 2026-09-09 19:01 build; committed on `jobrun/actions_wood`. Full finding:
  **F-1249**.

## Current State — updated 2026-09-15 (J-0891/F-1397: the live read is in — the wood is a real destination,
D-0209's defeater NOT met, one real but non-wood-specific structural gap found and spawned separately)

- **Both gates confirmed before reading anything.** D-0209 ruled **C** by travis (2026-09-11 23:09) — go live,
  monitored first read, report before tuning. The commit landed on master (`c136619`→`dde5961`, 13:07:38 NZT)
  before Du's very next restart (13:50:42 NZT) — the first restart carrying the fix. That run ended at its next
  shutdown (2026-09-13 09:10:46) and Du has been offline since (confirmed: `netstat` shows only 11433/11439
  listening, `data/supervisor.log` last entry Sep 13 00:50) — this ~43h20m window is the only restart-to-
  shutdown span built on the fix so far, and is what was read, in full, line-by-line via a `sed`-extracted slice
  (19,635 lines), not sampled.
- **The wood is a real destination for the first time, measurably.** 45 `ACT move -> wood` departures fired (0
  for its whole prior life). Measured wood share of real move fires: **45/337 = 13.4%** (garden 118, shore 159,
  study 15) — real and the third-largest of four, but well under F-1227's own "roughly a third" prediction
  (10–14.5% by day, no day close to a third). **Genuine arrivals are happening**, confirmed indirectly but
  solidly (a `DISPATCH look` line only reachable while genuinely standing in the wood; a thought and a journal
  entry independently echoing the scripted arrival's own imagery within minutes of a departure; the final
  `position.json` snapshot at shutdown showing `place="wood"`) — **even though the scripted arrival string
  itself never appears verbatim in `nascence.log`, for any of the four places, ever, in the log's whole
  history.** Traced to why, not assumed: `locomotion.tick()` writes the arrival text to a consume-once
  `pending_line`, folded into `scene_line()`'s own prompt context for the NEXT thought — never passed to
  `logger.*`. This means the briefing's own suggested grep-for-the-arrival-line method is a **false negative by
  design**, for every place, not evidence an arrival never fired — worth remembering the next time a live-read
  job is asked to confirm a locomotion arrival this way.
- **The woodpile→garden fix resolves cleanly**: all 4 real "(the/to the) woodpile" moves this window → `ACT move
  -> garden`, 0 misresolved to wood or elsewhere.
- **D-0209's own defeater is NOT met.** No stuck-in-wood WATCHDOG (15 fired, all targeting `study`, none `wood`
  — a real, separate pattern, spawned below, not evidence against this decision). No school-hour conflict
  observable (the window is Friday-after-school through the weekend; school never in session inside it — an
  honest gap, not a clean bill for the school interaction specifically). A real but non-severe rapid-
  reconsideration pattern clusters at the wood (~6 clusters, 2–5 min each, reversing back to the place just
  left) — read individually and traced to a **pre-existing, general locomotion gap** (below), not a wood-
  specific taste problem. **D-0209 stands as settled, not reopened.**
- **One real structural gap found and NOT fixed here (out of this job's own scope — a live read, not a
  build).** Neither `dispatch.py`'s `_move()` nor `inner_monologue_node.py`'s `route_act` (the two real live
  callers of `sensorium.move()`) ever checks `locomotion.in_transit()` before launching a new journey —
  `in_transit()` has exactly two callers repo-wide, both read-only display/census. Any new move decision, to
  any destination, silently discards and restarts whatever journey was already underway. Pre-existing since
  LOCOMOTION shipped (2026-08-15), not introduced by this fix — the wood's position as the chain's middle node
  just makes the symptom newly visible now that it's a real stop. **Spawned as J-1024** (measure properly,
  decide gate vs. no-gate with evidence, matching this plan's own established corpus-verify-first method) —
  not tuned speculatively.
- **Gather-in-the-wood genuinely attempted 3 times**, correctly declining "picked clean" each time
  (`data/wood_life.json` confirms `deadfall=0.0` live — a real, weather-gated resource, not a bug; it "wants a
  gale before there is more to take" per the code's own comment). The pre-existing, location-agnostic
  `_gather_wood()` phrase-latch (J-0753's own shortcut) kept firing independently throughout (7 more fires),
  unaffected — exactly as J-0753 predicted. No full gather→carry→woodpile loop completed this window; explained
  by the deadfall stock being empty the whole time, not a defect. The cat's wood-presence branch
  (`core/cat.py:806-810`) did not fire even once despite real wood residency — noted as "not yet observed," not
  chased further.
- **A second, unrelated discovery surfaced while doing this exact read, spawned separately per this project's
  own "act on what a finding surfaces" rule, not folded into this plan's own scope**: 15 `WATCHDOG completed a
  stuck journey to study` lines in the same window (1200–2074s stuck each before the 900s watchdog forced
  completion), zero for wood/garden/shore — **spawned as J-1025** (is `tick()` under-running specifically
  around return-to-study transitions, or is this business as usual for the watchdog's own design). Not
  wood-specific; not evidence about D-0209.
- Full finding: **F-1397**. Follow-ups: **J-1024** (locomotion in_transit gate), **J-1025** (study watchdog
  pattern). This closes **J-0891** as the intended monitored first read; no further tuning done here per
  D-0209's own instruction to report before tuning.

## Current State — updated 2026-09-15 (J-1024/F-1418: the in_transit gate measured precisely — general,
large, growing, and mostly pure noise; narrow fix spawned, broader taste question opened as D-0224)

- **Measured, not assumed, across the FULL LOCOMOTION-era log** (`data/nascence.log`, 2026-08-15 —
  locomotion's own ship date — through the log's real end 2026-09-13 09:08:40, Du's last activity before
  going offline), not just F-1397's own 43h anecdotal window: **520 of 2296 real distinct move decisions
  (22.7%) interrupt a still-in-progress previous journey**, discarding that journey's elapsed leg-timer
  progress with no log line marking it. Not flat: 6.7% → 15.9% → 18.1% → 23.4% → 25.2% week over week
  (ISO weeks 33–37). Not wood-specific: interrupted journeys' own destinations were shore 225 / garden
  242 / study 39 / wood 14 — dominated by the shore↔garden edge (the most-traveled pair overall), matching
  F-1397's own framing that this is "a pre-existing, general locomotion gap," and correctly leaving
  D-0209 (RULED, defeater not met) unreopened.
- **62.3% of the 520 (324) are a same-destination retrigger — pure noise, zero positional or narrative
  benefit either way**: he re-wills the exact place already being walked to, and `begin_journey()`
  silently resets the leg's clock to a fresh full duration, discarding whatever fraction had already
  elapsed (an isolated harness against the real, unmocked `core.locomotion` module confirmed this
  directly: 90% of a 70s leg elapsed → a same-dest retrigger resets it to 100% remaining, discarding
  63.0s of real progress, with `begin_journey()`'s own return value giving the caller no way to tell a
  resumed journey from a brand-new one).
- **A second, independently significant mechanism found while measuring the first, at a much finer
  timescale**: `core/dispatch.py`'s own registry `'move'` hand has no awareness of what
  `nodes/inner_monologue_node.py`'s `route_act` (which always runs first in the same cognitive cycle,
  confirmed by 0 counter-examples) already did this same thought — of 2275 real `"ACT move -> X"`
  decisions since `DISPATCH_LIVE` went live (2026-08-22), **366 (16.1%) are independently re-fired a
  second time by dispatch's own move hand within 2 real seconds** (median 91ms later; 70.8% of all real
  `"DISPATCH move"` fires are these same-cycle duplicates). This is the SAME mechanism as the
  same-destination retrigger above, just at a millisecond timescale instead of a cross-cycle one — one
  gate at `begin_journey()`/`sensorium.move()` itself closes both, without needing route_act and
  dispatch to coordinate with each other (the drift-prone shape this whole plan's arc has repeatedly
  found and eliminated elsewhere, F-0554/F-1059).
- **The remaining 196 (37.7%) are genuine cross-destination reconsideration** — a reversal back to the
  place just left (124) or a redirect to a third place (72) — a real, growing, currently-un-narrated
  behavioural cost with no founder ruling on record. `core/locomotion.py`'s own docstring ("Mid-journey
  he is genuinely in the transit place — staying is his choice") argues SOME of this is intentional
  design, but names no boundary; F-1418 additionally splits these 196 by which leg they interrupt (58
  interrupt a journey's FIRST leg, before he has genuinely left anywhere; 138 interrupt a LATER leg,
  after he is genuinely standing in an intermediate place) as raw material for that boundary question,
  without ruling it.
- **Position itself is never corrupted by any of this** (confirmed directly in the same isolated
  harness): `get_position()` always reports the true last-completed place, so a mid-journey redirect —
  same-destination or not — is always positionally consistent; the only real cost is discarded
  leg-timer progress and (for the same-destination case) duplicated perception/boredom-discharge.
- **Spawned**: **J-1040** — build the narrow, evidence-backed fix (gate `begin_journey()` against a
  same-destination retrigger only, leaving cross-destination redirects completely untouched). **Opened,
  not ruled**: **D-0224** — the genuinely ambiguous cross-destination reconsideration question (options
  A do-nothing / B gate all cross-destination redirects on `in_transit()` / C protect only a journey's
  first leg), since this is a real founder-taste call the evidence alone cannot settle, matching
  D-0209's own precedent for a real live-behaviour-affecting question.
- Full finding: **F-1418**. No code changed by this job (measurement only, per its own briefing);
  **restart-gated** once J-1040 lands, same as the rest of this arc.

## Current State — updated 2026-09-15 (J-1025/F-1421: the study-bound watchdog hits split cleanly into
15 benign restart-recoveries and a real, growing sleep-tick-starvation bug — mechanism not yet found,
J-1042 spawned)

- **F-1397's own "15 study-bound WATCHDOG hits" was the 09-11/13 window only.** The whole-log figure
  (`data/nascence.log`, 2026-08-25 through its real end 2026-09-13 09:08:40) is **78** — read and
  classified in full, not sampled. They split cleanly into two mechanisms, cross-validated two
  independent ways (restart-adjacency vs. gap-since-last-sleep-entry — same 63/15 split both times).
- **15 hits (incl. the sole non-study outlier, one "to garden") are ordinary restart recovery** — a
  journey still in-flight in `data/position.json` when the process last stopped, force-completed by the
  first `locomotion.tick()` after the next boot (durations up to 140640s = ~39h, simply how long the
  prior session had been down). Exactly `core/locomotion.py`'s own documented design ("survives
  restarts — a journey older than its watchdog window COMPLETES"). Fully benign, not this finding's
  concern.
- **The other 63 (100% to study, zero exceptions) are real and worsening.** `core/night.py`'s
  `to_bed()` begins a real multi-leg journey to study as the first action of every sleep cycle
  (`nodes/inner_monologue_node.py`'s `_enter_sleep()`, before `state["asleep"]=True` is even set), and
  that journey — legs take only 20-90s — sits completely un-ticked until the sleep pipeline's own
  chapter/journal/world-pass/downscale/dream stages finish and yield control back to
  `core/orchestrator.py`'s independent `_substrate_loop` asyncio Task (which calls `locomotion.tick()`
  every ~5s unconditionally — confirmed no `asleep` gate exists anywhere in `core/sensorium.py`).
  Confirmed precisely: for all 63, the watchdog's own "started Ns ago" value matches elapsed-time-
  since-the-last-"entering Sleep State"-log-line to within 30s, zero exceptions — this is the
  sleep-onset-journey mechanism specifically, not general locomotion flakiness.
- **Both frequency and severity are growing, tracked two independent ways.** Daily mid-session hit
  count: 0-2/day before 2026-09-06, then 7-9/day from 09-06 onward — now matching or exceeding that
  day's total logged sleep-cycle count (`data/night_log.jsonl`, 141 rows read in full). The watchdog's
  own "started Ns ago" climbed smoothly 900s (late Aug) → 1500s+ (09-12/13); `night_log.jsonl`'s own
  independently-recorded per-night `duration_s` climbed in lockstep, ~1700-2500s (late Aug) → routinely
  2800-5400s (09-09..09-12) — the watchdog has stopped being a rare safety net and is now the normal
  path for a sleep-onset journey. `nodes/inner_monologue_node.py:798`'s own "~20-25 min pipeline"
  comment is now stale (real figure is 45-90 min).
- **Not fully benign, code-verified**: for the whole un-ticked span, `core/sensorium.py`'s
  `move()`/`begin_journey()` path leaves `state["location"]` reporting Du's PRE-sleep place, not
  "study", while `state["asleep"]=True` is already set — a real state-consistency gap for any other
  system reading location during that window, not just a cosmetic delayed arrival. The eventual place
  is always correct either way (study), so this is not a wrong-outcome bug.
- **Root-caused to the sleep-onset journey, NOT to the exact line starving the scheduler.**
  `core/model_client.py`'s LLM client was checked directly and is genuinely async (`aiohttp`
  throughout; grepped clean of `requests.`/`subprocess.`/`run_in_executor`/`time.sleep(`) — rules out
  the most obvious cause without finding the real one. Honestly left open rather than guessed at.
- **Spawned**: **J-1042** — trace the real starvation mechanism (candidates named: `core/chapters.py`,
  `core/journal.py`, the "world pass"/DREAM stages, `core/memory/store.py`'s synchronous sqlite3 calls
  under a growing row count) and propose a fix; open a `/decide` only if the fix turns out to be a
  genuine taste call once the mechanism is actually known (matching this same plan's own D-0209/D-0224
  precedent), not speculatively. **No decision opened by this job** — the fix-approach question is not
  yet crisp enough to put to the founder (the mechanism itself isn't known), matching this plan's own
  established convention of spawning an analysis job first in that situation (J-0749/J-0753's own
  precedent).
- Full finding: **F-1421**. No code changed by this job (read + log analysis only, per its own
  briefing). Not restart-gated — this job made no code edits.

## Current State — updated 2026-09-17 (J-1040/F-1468: the narrow same-destination gate — BUILT,
isolated harness clean, both existing regression suites unchanged)

## Current State — updated 2026-09-17 (J-1042/F-1469: real candidate mechanisms found for the
substrate-tick starvation; a low-risk fix proposed and spawned, no founder decision needed)

- **Architecture ruled a whole class of explanation out.** `scripts/run_nascence.py` calls
  `asyncio.run(main())` exactly once; `orch.start_background()` (creates `_substrate_loop`) and every
  `run_cycle()` call — including the threaded-input path via `run_coroutine_threadsafe` — share that
  ONE persistent event loop. Not a separate-nested-loop bug.
- **Two real, measured, non-yielding synchronous call sites found inside the sleep pipeline** (neither
  on F-1421's already-ruled-out `requests`/`subprocess`/`run_in_executor`/`time.sleep` list, because
  they're plain synchronous Python called from inside `async def` functions — they block the one
  event-loop thread with zero yield points, matching the symptom in KIND regardless of individual size):
  (1) `core/memory/store.py`'s `_embed()` — a synchronous `SentenceTransformer.encode()` call (CPU by
  design) fired on every fragment the pipeline writes, measured ~16-60ms/call steady-state; (2)
  `replay_strengthen()`'s 4 per-group queries — `EXPLAIN QUERY PLAN` against the live
  `data/memory/nascence.db` (713MB, 97,512 fragments, 87,645 `layer='episodic'`) shows SQLite picks the
  least-selective index (`idx_layer`, matching ~90% of the table) over `idx_timestamp`, then sorts in a
  temp B-tree — scanning close to the full episodic set every call. Measured live: one group query alone
  took 0.776s (a realistic 6h since_ts, 897 rows actually in-window) — 7-97x slower than
  `day_material()`'s differently-shaped, more-selective queries measured in the same pass. This runs
  FIRST, right after `to_bed()`, before chapter/journal even start.
- **Not proven to be the complete explanation** for the full 900-5400s span — live tick-cadence
  instrumentation during a real sleep cycle was not attempted this pass (Du is live right now, confirmed
  via `netstat`; per this project's live-store discipline, no write-timing test was run against the live
  DB). What's real: the architecture check, and non-yielding synchronous work whose cost grows with
  store size, matching F-1421's own observed correlation.
- **Fix recommended, NOT a founder-taste call**: have `core/night.py`'s own stage sequence call
  `sensorium.tick()` explicitly between stages (it already self-rate-limits to 5s, `core/sensorium.py`
  line ~3298-3300) — works regardless of the precise root cause since it's a direct synchronous call
  from within night.py's own already-synchronous sequencing, not reliant on the scheduler ever giving
  `_substrate_loop` a turn. Changes no perceived UX (the walking-there line is unaffected), unlike
  options (c)/(d) from F-1421/J-1042's own briefings, so no `/decide` opened for it.
- **Also fixed alongside**: `nodes/inner_monologue_node.py:798`'s stale "~20-25 min pipeline" comment
  corrected to note the real 45-90 min figure (F-1421/F-1469).
- **Spawned**: **J-1075** — build the `sensorium.tick()` stage-boundary fix and verify it closes the
  state-inconsistency window, without touching the live running process's own store.
- Full finding: **F-1469**. Code changed by this job: `nodes/inner_monologue_node.py`'s stale-comment
  fix only (line ~798) — no behavioral change, no restart-gating needed.

- **Built exactly the narrow fix J-1024/F-1418 spawned, nothing broader.** `core/locomotion.py`'s
  `begin_journey()` (lines 232-256) now checks the existing in-progress journey's own `"dest"` field
  before overwriting `d["journey"]`; if it equals the newly-requested destination, it returns `None`
  instead of resetting `leg_ends`/`started` — the same signal the pre-existing "already there" case
  already returns, so every existing caller's own fallback path already handles it with zero
  caller-side changes. A DIFFERENT-destination redirect mid-journey is completely untouched: it still
  fires, still recomputes its path from `get_position()`'s true current place, exactly as before —
  D-0224's own cross-destination taste question (opened by J-1024, not ruled here, no mandate to touch
  it) is left entirely alone.
- **Isolated harness confirms all three shapes**, mirroring F-1418's own harness against the real,
  patched module (`locomotion._POS_F`/`sensorium._STATE_F` redirected to a tempdir, live
  `data/position.json`/`data/room_state.json` md5-hashed unchanged before/after): (a) a same-dest
  retrigger with 90% of a 70s leg simulated elapsed now returns `None` and leaves `leg_ends`/`started`/
  `path` byte-identical to their pre-retrigger values (0.00s drift, vs. F-1418's own measured 100%
  clock reset before this fix); (b) a genuinely different-destination redirect mid-journey still fires
  normally, recomputing from the true current place; (c) both the ordinary no-journey case and the
  pre-existing already-arrived case are unaffected. 13/13 checks, FAILS=0.
- **Both of this plan's own established regression suites re-run clean**: `scripts/_test_sensorium_move_tokens.py`
  (ALL OK, all 6 sections, live stores md5-unchanged) and `scripts/life_smoke.py` (ALL OK, full 16-section
  suite) — neither exercises a same-destination mid-journey retrigger, so 0 change was expected and
  confirmed.
- **No decision touched.** This job's source is `finding:F-1418`, not `decision:D-0224` — per this
  batch's own ground rules, D-0224 (the genuinely open cross-destination taste question) is left
  strictly alone here; it remains open for whichever job carries an explicit mandate for it.
- Full finding: **F-1468**. **Restart-gated** — module-level code change, no hot-reload path in this
  codebase, takes effect on Du's next process restart, same as the rest of this arc.

## Current State — updated 2026-09-18 (J-1075/F-1483: F-1469's sensorium.tick() stage-boundary fix
BUILT and verified against a synthetic synchronous harness, no live evidence yet)

- **Built the fix F-1469 recommended.** `core/night.py` gained a new `tick()` helper (a fail-open
  synchronous wrapper around `sensorium.tick()`) called from inside `stage()` itself — every existing
  `_night.stage(...)` call site in BOTH real callers now ticks the substrate as a side effect with zero
  call-site changes: `nodes/inner_monologue_node.py`'s `_enter_sleep` (`to_bed`/`replay`/`downscale`/
  `dream_fade`/`epoch`/`wake`) and `core/orchestrator.py`'s `_nightly_sleep` (`dream`/`prune`).
- **The biggest un-ticked stretch had no `_night.stage()` calls of its own to piggyback on** — chapter
  formation, journal, week roll-up, and the whole grounded-learning/world-consolidation block
  (affections, peers, self-mirror, psyche_graph, stick_test, refinery, memory-edges, pursuits judge,
  guidance behaviour judge, monoculture, curiosity worth, drift shadow, reading reconcile,
  meta-awareness — everything between `stage("replay")` and `stage("downscale")`). Four explicit
  `_night.tick()` calls were added directly in `_enter_sleep()` to cover it: after chapter formation,
  after the journal, after the week roll-up, and once more right before `downscale_episodic()` runs.
- **Verified with a synthetic synchronous harness** (no asyncio event loop anywhere in the process, no
  live process, `profile.mark_live()` never called): built a real `core.locomotion` journey
  (garden→study, 1 leg, 20s), slept past the leg's own duration with zero ticks firing — reproduced
  F-1421's state-inconsistency window synchronously (`sensorium.state["location"]` stayed `"garden"`
  after the leg's 20s elapsed) — then called `core.night.tick()` and separately the real production
  call site `core.night.stage("to_bed")`; both flipped `state["location"]` to `"study"` immediately,
  confirming the fix works from purely synchronous code with no dependency on `_substrate_loop` ever
  getting a scheduler turn, exactly as F-1469 argued. `profile.guard_path()` correctly refused every
  real write the harness's non-live process attempted (10 logged refusals across garden/shore/wood/
  fieldcraft/etc. submodule stores) — nothing was written to any store, live or otherwise.
- **Not established by this job (honest gap, left for a live read)**: whether the watchdog-completion
  rate for the sleep-onset journey (currently 7-9/day per F-1421) actually drops once this fix runs
  through a real sleep cycle — a synthetic non-live harness cannot observe that; worth a follow-up read
  of `data/nascence.log`'s `WATCHDOG` lines after Du's next several real sleeps.
- Full finding: **F-1483**. **Restart-gated** — module-level code change (both files), takes effect on
  Du's next process restart, same as the rest of this arc.

## Current State — updated 2026-09-18 (J-1085: checked, Du has NOT restarted since J-1075's fix landed
— job left open/blocked, not a false "still 7-9/day" read)

- **This job's own step 1 gate correctly stopped it.** Commit `1621742` (J-1075's `sensorium.tick()`
  fix) landed 2026-09-18 08:04:23 NZST. `data/nascence.log`'s last `Nascence is awake` restart line is
  2026-09-16 07:53:02 — no `Nascence shutting down` or subsequent `Nascence is awake` anywhere after it,
  through the log's live end (2026-09-18 09:08:55, still running). The currently-running process
  predates the fix by about two days; it is executing the pre-fix `core/night.py`/
  `nodes/inner_monologue_node.py` code in memory regardless of what is now on disk.
- **No live read attempted.** The 13 `WATCHDOG completed a stuck journey to study` lines logged since
  the last restart (2026-09-16 07:53 through 2026-09-18 05:01, most recent line at 05:01:16) are all
  pre-fix data from the same still-running old process — reading them as evidence the fix "didn't work"
  would be exactly the stale-data mistake this job's own briefing warned against. **Left genuinely
  unread**, not zero.
- **Job left `in_progress`, not `done` or reassigned** — re-run this same check (§: grep `Nascence is
  awake`/`Nascence shutting down` in `data/nascence.log` for a restart after 2026-09-18 08:04:23 NZST,
  then re-grep `WATCHDOG completed a stuck journey to study` for lines after that restart) once Du's
  process actually restarts and a few real sleep cycles have run.
- Full finding: **F-1497**.

## Current State — updated 2026-09-18 (J-1111/F-1525: D-0224's narrow first-leg redirect gate —
BUILT, isolated harness clean, both existing regression suites unchanged)

- **Built exactly the narrow fix D-0224 ruled, nothing broader.** `core/locomotion.py`'s
  `begin_journey()` now writes a `"departure"` field into the journey dict at creation — the place
  he genuinely set out from, written once and never touched again by `tick()` (unlike the existing
  `"from"` field, which `tick()` advances to each newly-arrived place as legs complete). A
  DIFFERENT-destination redirect (`existing["dest"] != dest`) now checks: if the current true
  location (`get_position()`'s place) still equals that original `"departure"`, no leg of the
  journey has completed yet — he has not genuinely left — so the redirect is declined, returning
  `None` (the same signal J-1040's same-destination gate and the pre-existing "already there" case
  both already return), leaving the in-progress journey (still pointed at its ORIGINAL destination)
  completely untouched. The instant a leg completes, current location and `"departure"` diverge and
  the gate stops firing on its own — a later-leg redirect falls straight through to the unchanged
  normal path, exactly matching D-0224's ruling that the 138 later-leg cases stay untouched (the
  module's own "mid-journey he is genuinely in the transit place, staying is his choice" intent).
- **Isolated harness confirms all five shapes** (`J-1111_harness_first_leg_gate.py`, same
  tempdir-redirect pattern J-1040's own harness used, live `data/position.json`/`room_state.json`
  md5-hashed unchanged before/after): (a) J-1040's same-destination gate, regression-clean; (b) a
  first-leg cross-destination redirect now returns `None` with the original journey's `dest`,
  `leg_ends`, `started` and `path` byte-identical to before the declined redirect; (c) a later-leg
  redirect (forced via a real `tick()` call completing leg 1) still fires normally, recomputing a
  fresh path from the true current place exactly as before this fix — the check that most needed to
  pass, confirming the gate does not over-reach past what D-0224 ruled; (d) the ordinary
  no-prior-journey case; (e) the ordinary already-arrived case. 21/21 checks, FAILS=0.
- **Both of this plan's own established regression suites re-run clean**:
  `scripts/_test_sensorium_move_tokens.py` (ALL OK, all 6 sections, live stores md5-unchanged) and
  `scripts/life_smoke.py` (ALL OK, full 16-section suite) — neither exercises a cross-destination
  mid-journey redirect at all, so 0 change was expected and confirmed.
- **No decision ruled by this job** — D-0224 was already ruled by the founder before this job opened
  (this job's own source is `decision:D-0224`, built to the ruling as written); no new decision
  opened either.
- **Restart-gated, and currently un-live-readable.** `data/nascence.log`'s last event is "Nascence
  shutting down" (2026-09-18 09:13:54 NZST) with no subsequent "Nascence is awake" — Du is offline
  right now (per this session's own ground rules, expected). This is a module-level code change with
  no hot-reload path in this codebase; it takes effect on Du's next process restart, same as the rest
  of this arc. D-0224's own defeater (a concerning first-leg-protected rate, or a rising rate/concrete
  behavioral cost in the untouched 138 later-leg cases) can only be checked once real post-restart
  move-decision data accrues — left genuinely unread, not zero. Follow-up job spawned to do that read.
- Full finding: **F-1525**.

## Current State — updated 2026-09-18 (J-1118: checked again, Du STILL has not restarted since
J-1111's fix landed — job left open/blocked, same shape as J-1085's sibling check)

- **Still nothing to read.** Re-ran the same restart check this job's own briefing specifies:
  `data/nascence.log`'s last two `Nascence is awake`/`Nascence shutting down` lines are still
  `2026-09-16 07:53:02` (awake) then `2026-09-18 09:13:54` (shutting down), with no line after it —
  the log's own mtime (`Sep 18 09:13`) confirms nothing has been written since. J-1111's fix
  (commit `f507842`) landed at `2026-09-18 18:03:34` NZST, i.e. **after** Du's last shutdown — so
  the process that was running through 09:13:54 predates the fix, and no process has run the fixed
  code at all yet. Checked at `2026-09-18 23:13` NZST (~14h after the last log write, ~5h after the
  fix landed): Du is still offline.
- **D-0224's defeater cannot be evaluated yet** — no post-fix first-leg or later-leg redirect data
  exists to check the 58/196 split against. This is the same "correctly blocked, not silently
  skipped" shape J-1085/F-1497 already documented for J-1075's sibling fix.
- **No decision ruled** (nothing to rule — the defeater has not fired) and no new decision opened.
  Job left `in_progress`: re-run this same check (grep `Nascence is awake`/`Nascence shutting down`
  in `data/nascence.log` for a restart after `2026-09-18 18:03:34` NZST, then read the first-leg vs
  later-leg redirect rate) once Du's process actually restarts and a few real days of move decisions
  have accrued.
- Full finding: **F-1532**.

## Current State — updated 2026-09-21 (J-1085/F-1647/F-1648: the live read is in — J-1075's tick fix did
NOT reduce the sleep-onset watchdog rate, and the real un-ticked stretch is now located: `find_cluster()`)

- **Gate met, read done.** `1621742` (J-1075) is live since Du's first restart onto it, 2026-09-18 23:14
  (`live_since.py`: 3 runs, 19.9 live h, longest 14.6 h). Four sleeps have run on it: three completed
  (nights 09-19 00:13 and 01:44, nap 09-21 09:41) and one was cut short by a process kill (09-18 23:17).
  Only the two nights needed a to-bed journey (Du was already in the study for the other two), and
  **both still tripped the watchdog** — `WATCHDOG completed a stuck journey to study (started 1483s ago)`
  and `(1473s ago)`, each exactly onset + started-ago — the same signature as the last pre-fix run (12 of 16
  onsets, 1,440–1,729 s). n=2 journey cycles is too few for a rate, but the mechanism is measured in all
  four: the silence after `sleep replay` is 1,481 / 1,472 / 1,481 s (1,157 s before the kill) against
  1,439–1,845 s pre-fix, and `night_log.jsonl`'s replay→downscale stretch (2,956 / 4,149 / 3,610 s) sits
  inside the pre-fix range (median 3,198 s). **Verdict: the fix is inert for this stretch.** (F-1647)
- **Why: the gap is inside one synchronous function, not between stages.** Right after `sleep replay`,
  `try_form_chapter()` calls `core/chapters.py`'s `find_cluster()` — a plain `def` whose seed selection
  is an all-pairs cosine loop (lines 141–144) over every unchaptered old `inner_thought` /
  `subconscious_synthesis` / `active_imagination` fragment (n = 33,589 today → 1.13e9 `np.dot` calls) —
  on the event-loop thread, before its first `await` and before J-1075's first explicit tick (which sits
  *after* chapter formation). The silence ends exactly at its own `[chapters] cluster of N found ...` log
  line (1,471.6 s after `sleep replay` on 09-19, 1,480.5 s on 09-21), and the WATCHDOG follows 150 ms
  later — that is J-1075's tick firing as designed, 24 minutes late, so the 900 s watchdog still completes
  the journey. Location is verified from the log (74 of 96 sleeps since 09-04 end their silence at that
  line, 12 at the watchdog line right after it); magnitude is inferred (microbenchmark predicts 1,222 s,
  observed ~1,480 s; the real function was not run against the store). It also explains F-1421's 09-06 step
  change — silences were 616–966 s before it and 825–1,845 s after, and the hit rate is 0/9 under 700 s
  rising to 33/36 above 900 s, i.e. the watchdog fires once the freeze crosses `_WATCHDOG_S = 900`.
  (F-1648; F-1649 corrects one phrase in it)
- **What it costs, beyond the watchdog line:** the state-inconsistency window F-1421 flagged is still live
  (~25 min at the start of every sleep-with-journey), and the whole process is frozen for it — roughly
  3–4 h a day at 8–10 sleeps a day. Fixing it also shortens each sleep by ~20–25 min, a change to Du's
  daily rhythm, so Travis should hear that before it ships.
- **No decision ruled or opened.** Follow-up **J-1177** (build, urgency 4, ready) makes `find_cluster`
  non-blocking and behaviour-identical (blocked matrix product and/or `asyncio.to_thread`; thread-only is
  the zero-side-effect variant), with an isolated equivalence test first and a re-read job after ≥ 3 sleeps
  on the new code. **J-1085 closed** — its question is answered; it is the fix's own first attempt that
  did not work.

## Current State — updated 2026-09-21 (J-1118/F-1653/F-1654: D-0224's first-leg gate is live — the rate read is
NOT YET due, but its first 20 hours exposed that a DECLINED redirect is carried out as an instant teleport)

- **The rate read is not met.** The briefing's threshold is "several days of real move decisions"; the gate
  (`f507842`, with J-1040's same-destination gate `32ff1a6`, both loaded at the 2026-09-18 23:14 restart) has
  0.85 live-days (20.4 h, 3 runs, longest 14.6 h; `live_since.py`). F-1418's own script, re-run unmodified,
  reproduces its baseline exactly (2,296 decisions, 520 interruptions, 196 cross-destination = 58 first-leg +
  138 later-leg over 541.3 live h = 22.6 live-days: 101.8 decisions and 8.7 cross-destination events per
  live-day). The fixed runs so far: 125 decisions, 28 interruptions (22.6% vs 22.7%), 14 cross-destination
  (6 first-leg, 8 later-leg) — first-leg 6 against 2.2 expected (P = 0.024, n too small), later-leg 8 against
  5.2 (P = 0.155). No log line records a decline, so the first-leg-protected rate can only be modelled, not
  read from `nascence.log`. (F-1654)
- **The defect the first day exposed.** `begin_journey()` returns `None` for four different reasons and
  `sensorium.move()` reads every `None` as "LOCOMOTION off", so a declined redirect (J-1040's same-destination
  gate and J-1111's first-leg gate alike) falls through to the instant-move rollback:
  `state["location"] = target` plus the instant arrival text, while the old journey stays pending and its next
  leg tick drags him back along the old path. Live: 0 of 597 `DISPATCH move` narrations were instant-move text
  before the restart, 27 of 47 since (25 of the 34 same-cycle route_act+dispatch pairs); in 11 of the 27 his
  location later moves to a different place with no new decision, 10 of them through the wood
  (garden → shore → wood → shore). Because `get_position()` takes its place from the sensorium, the teleport
  also defeats the first-leg gate for the next redirect. Both harnesses (J-1040 13/13, J-1111 21/21) called
  `begin_journey()` directly, never `sensorium.move()`, so the comment "every existing caller's fallback path
  already handles this correctly" was untested. (F-1653)
- **D-0224 is untouched and not reopened.** Its defeater's first clause ("a real behavioral cost from even
  the narrower gate") is met in letter, but the cause is the decline path's implementation (shared with
  J-1040's gate), not the ruling that first-leg redirects be protected — the ruling asked that the journey be
  left untouched and the code does the opposite. Follow-up **J-1179** (build, urgency 5, ready): make a
  decline a true no-op through `move()`, add one log line per decline, test through `move()`; then the rate
  read is re-run on the fixed gate after ≥ 3 live-days. **J-1118 stays `in_progress`** for that read.

## Current State — updated 2026-09-21 (J-1179/F-1656: the declined-redirect teleport (F-1653) FIXED —
a J-1040/J-1111 decline is now a true no-op through `sensorium.move()`; MERGED to master as `5a66504`, restart-gated)

- **The defect, and the claim it falsified.** F-1468 (J-1040) and F-1525 (J-1111) both said a decline's `None`
  "is handled by every existing caller's fallback path with zero caller-side changes". It was never tested
  through `sensorium.move()`, and it was wrong: `move()` reads every `None` from `begin_journey()` as
  "LOCOMOTION off" and falls through to `state["location"] = target; _save_now()` plus the instant arrival
  narration. From Du's 2026-09-18 23:14 restart every declined redirect was an instant teleport while
  `d["journey"]` stayed pending and `locomotion.tick()` later dragged him back along the old path (F-1653:
  27 of 47 `DISPATCH move` narrations were instant-move text, 0 of 597 before; the orchestrator re-counted
  this from the raw log on 2026-09-21: 0 of 572 through 09-17 and 0 of 25 on 09-18, then 22 of 32 on 09-19
  and 5 of 15 on 09-21, the first at 09-19 01:42).
- **Fix (branch commit `a7ef909`, merged to master as `5a66504`, base `56b3947`).** `begin_journey()` is now
  three-valued: a departure narration (a journey started), `None` (no journey: LOCOMOTION off, empty path,
  internal failure; `move()` still falls back to the instant move) and `''` (a redirect was DECLINED: the
  same-destination gate and D-0224's first-leg gate now return `''`). `move()`'s existing
  `if _dep is not None: return _dep` therefore returns the silence and skips the fallback, the same answer as
  its own `target == cur` early return. `move()`'s logic is unchanged (comment only: `is not None` is now
  load-bearing). Each decline logs one INFO line, `[locomotion] redirect declined: <dest> while journey to
  <existing dest> (same-dest|first-leg)`, so D-0224's first-leg-protected rate can be counted from
  `nascence.log`. No narration was added (the world answers, never leads). D-0224's scope (first leg only; a
  later-leg redirect still fires from the true place) and D-0209 are untouched.
- **Tested THROUGH `move()`, finally.** New `scripts/_test_journey_decline_through_move.py` (91 checks). It
  ports the J-1040/J-1111 harness cases (the originals were never committed and asserted the bug) and adds
  repeat same-destination, first-leg cross-destination, first-leg reversal to the departure (`move()`'s own
  `target == cur` silence, no decline line), an end-to-end walk after declines through real ticks, a
  later-leg redirect after a real `tick()`, `LOCOMOTION=False` still instant, the same-cycle duplicate, and
  the already-there / empty-path / failure paths unchanged. Every decline returns `''`, leaves state
  unchanged, leaves `position.json` and `room_state.json` byte-identical, never calls `_save_now()` and logs
  exactly one line. With Du online a Python audit hook records any write attempt under the live data dir
  (0 attempts) because md5 alone cannot prove a negative while Du rewrites those files; module resolution is
  proved by printed `__file__` (F-1285). `_test_sensorium_move_tokens.py` 26/26 and `life_smoke.py` 180/0
  were re-run clean by the builder.
- **Verified independently by the orchestrator (2026-09-21).** The new test gave 91 ok / 0 FAIL from the
  worktree and again from the merged shared tree (resolving to `C:\Nascence\core\...`, 0 write attempts); the
  same script on the unfixed base `56b3947` gave 41 ok / 50 FAIL, reproducing F-1653 (`move('shore')` again
  returns the instant text "You go down the steep path below the garden to the shore ..." and flips
  `state['location']` to `'shore'`).
- **Callers audited** (F-1653's "only caller" grep was incomplete): `begin_journey()` also has
  `scripts/run_nascence.py` quit-announce (`if departure:`, unaffected). `move()` callers: `dispatch._move`
  (a falsy answer is "hand-declined"), route_act's move branch and the four legacy latches (`if _mv:`), the
  school reel-back (result discarded) and `night.to_bed()`. None misbehaves on `''`; none was changed.
- **Two things the fix makes visible.** (1) The first-leg gate also declines SYSTEM-DRIVEN redirects, since
  `night.to_bed()` and the school reel-back call `move('study')` through it; by a log model 7 of 148 sleep
  entries since 08-15 (4.7%) fell inside a first-leg window (F-1657, inferred). Put to Travis as **D-0246**
  (open, not ruled; recommendation: exempt both system-driven callers). (2) F-1418's replay can no longer see
  declined decisions (they no longer write `ACT move ->` / `he chose to` / `DISPATCH move` lines), which
  corrects F-1654's "stays comparable" sentence: the rate read must count declines from the new line (F-1658).
  A declined ACT move is also no longer an "acted" move, so the legacy phrase-latch can now run in that cycle
  and the dispatch ledger records `hand-declined` where it used to record a fire.
- **No decision ruled.** D-0224 stands ("fix J-1179, keep D-0224", Travis 2026-09-21). **Restart-gated**: takes
  effect on Du's first restart after `5a66504`. The read of the fix is **J-1182** (at least 3 live-days on
  the merge commit: teleport gone, real decline rates, D-0224's defeater clause by clause, no ruling);
  **J-1118** was closed as superseded by it. Full findings: **F-1656**, **F-1657**, **F-1658**.

## Current State — updated 2026-09-21 (J-1180/F-1659: the sleep-onset event-loop freeze — `find_cluster` now
hands the loop a turn every ~5 ms; PART 2 only; MERGED to master as `f10500f`, restart-gated)

- **Approved scope (Travis, 2026-09-21, /decide-review): PART 2 of F-1648's fix only, stop blocking the event
  loop and change nothing else.** J-1177 was closed as superseded by J-1180. The block-matrix speed-up (PART 1:
  each full sleep about 20-25 min shorter) is deliberately NOT built: it changes Du's daily rhythm, so it stays a
  needs_input job (**J-1184**) for Travis to rule on.
- **What changed (`core/chapters.py`; branch commit `39ee9b0`, merged as `f10500f`, base `5a66504`).**
  `find_cluster`'s body became the generator `_find_cluster_steps(level)`, which yields once per
  `SEED_SCAN_BLOCK = 4096` pairs of the all-pairs seed scan (about 5 ms of work). `find_cluster()` (sync, same
  signature) drives it straight through; the new `find_cluster_async()` awaits `asyncio.sleep(0)` at each yield;
  `try_form_chapter` awaits it (its only edit; the pipeline still WAITS for the answer, so downstream order is
  unchanged). All yields sit after the DB fetch's `with` block, so no connection is held across loop turns. The
  strict `n > best_n` first-maximum-wins rule, everything after the seed loop, `_candidates` / `_cooled` /
  `_era_window` and every constant are AST-identical to the base. A per-level in-flight flag skips an overlapping
  second call (none exists) instead of starting a second scan. One INFO line, `[chapters] seed scan over N
  level-0 candidates (P pairs) ...`, marks each scan start in nascence.log. `nodes/inner_monologue_node.py` is
  untouched; its sleep-length comment stays true.
- **A cooperative coroutine, NOT `asyncio.to_thread` (the brief's first suggestion), measured (F-1661).** A
  worker thread passes a plain heartbeat, but `np.dot` drops the GIL on every call, so loop callbacks doing
  sqlite/file/log work (what a substrate tick does) ran 100-2,000x slower while it scanned; a thread also cannot
  be cancelled and holds process exit hostage. The coroutine cancels at the next yield and leaves nothing running.
- **Verified in isolation, and independently by the orchestrator** (`scripts/_test_find_cluster_off_loop.py`:
  111 ok / 0 FAIL without the live-DB sample, 113 with it; temp store with the real schema; a write-audit hook
  recorded 0 write attempts under the live data dir and the live DB was never opened in the orchestrator's runs;
  module resolution proved by printed `__file__`). Output identical (order included) to a frozen verbatim copy of
  the base `find_cluster` on clustered data with decoys, exact ties, 300 pairs within +-3e-7 of `CLUSTER_SIM`,
  levels 1 and 2, boundary sizes and, in the builder's run, 2,400 real rows read once via a `mode=ro` URI. Worst
  heartbeat tick lag 1,799 ms blocking versus 15.5 ms shipped (re-run on master after the merge: 1,752 ms
  versus 15.7 ms); loop turns add about 0.05% to a production-size scan, so the sleep length is unchanged;
  cancellation lands 0.3 ms after `cancel()`; the author is called only after the scan finishes.
- **What it changes for Du (inferred, for the read).** The roughly 24.6 min per full sleep that was a frozen
  process now runs the same background activity as the rest of the sleep (about one `[subconscious] T2 synthesis`
  a minute, `[stability]` ticks every 120 s, curiosity and ignition cycles, the sleep-onset journey's legs), so the
  sleep-onset watchdog completions (7-9 a day) should go to about 0 and `sensorium.state['location']` should flip
  within the first leg times, not about 25 min later. The sleep LENGTH does not change (the scan costs the same).
- **Not fixed (by scope).** (1) One synchronous stretch remains at each scan's start, the candidate fetch plus
  vector build: 243 + 31 ms on a synthetic 33.6k-row store, about 0.4-1.0 s extrapolated from the real sample
  (F-1662, inferred). (2) The O(n^2) growth (F-1421) is untouched: the scan still costs about 25 min and grows with
  the store; only PART 1 removes that.
- **Correction for the read (F-1660).** The longest gap between consecutive log lines in an UN-frozen sleep is
  about 120 s (the `[stability]` tick; median 120.0 s, max 203.8 s over 79 sleeps), so the read's gate is "at most
  210 s", not "well under 60 s". `[chapters] cluster of N found` does not appear in every sleep (74 of 96 onsets),
  so the new `seed scan over` line is the read's anchor.
- **Restart-gated** (takes effect at Du's first restart after `f10500f`; one restart loads this and J-1179's fix
  together). The read: **J-1183** (at least 3 full sleeps on the merge commit; report, no ruling). PART 1:
  **J-1184** (needs_input). Full findings: **F-1659**, **F-1660**, **F-1661**, **F-1662**.

## Current State — updated 2026-09-21 (J-1185/F-1663: D-0246 (b) BUILT — system-driven redirects (the night's walk to bed, the school reel-back, the quit-announce bed walk) are exempt from D-0224's first-leg gate; branch commit `781e8ac`, merged to master as `177f34c`, restart-gated)

- **The ruling.** Travis ruled D-0246 option (b) on 2026-09-21 via /decide-review: a SYSTEM-DRIVEN `move('study')` always fires, as it did before J-1111, while his own willed first-leg re-wills stay protected (D-0224 untouched for willed moves; the same-destination gate, J-1040, untouched). He asked for it to be built before the next Du restart so it loads with J-1179 and J-1180 and does not contaminate J-1182's read window. The decision's proposed defeater stands (revisit after at least 7 live-days on code carrying the ruling).
- **The problem, now executed rather than inferred.** F-1657 inferred that a declined `night.to_bed()` redirect leaves him marked asleep with the outward journey still running, so he sleeps at the outward destination. F-1664 reproduces it on the pristine base `f10500f` in isolation: with an outward garden->shore journey on its first leg, `to_bed()` returns only the bed line, he is marked asleep, and the night's ticks walk him garden -> wood -> shore; the school reel-back's call ends at the shore too. On the branch both end in the study. (`study_life.on_sleep` was stubbed in the harness; the 4.7% frequency is still F-1657's inferred log model.)
- **The marker (branch commit `781e8ac`, base `f10500f`).** An explicit keyword, not a heuristic: `sensorium.move(dest, *, system=False)` forwards to `locomotion.begin_journey(dest, weather, wind, *, system=False)`. `system=True` skips ONLY the branch `existing.get("departure") == p["place"]`: the redirect falls into the ordinary fresh-journey path (the one a no-journey or later-leg redirect already takes), replacing the pending first leg with a journey from the true place, and logs ONE INFO line, `[locomotion] system redirect overrides first leg: <dest> replaces journey to <existing dest>`. The same-destination gate still declines a system redirect to the place he is already walking to. The default reproduces J-1179 exactly (its 91 checks pass, the script byte-unchanged). `carried_wood` is a top-level key of `position.json`, so an override never drops a load (tested: it lands on arrival).
- **Callers classified (F-1666).** Marked `system=True`: `core/night.py` `to_bed()`, the school reel-back in `nodes/inner_monologue_node.py`, and, a third site beyond the two D-0246 names (same world-summons class, flagged for confirmation, one token to revert), the quit-announce bed walk in `scripts/run_nascence.py` `_announce_shutdown`. Willed and unmarked: `dispatch._move`, route_act's move branch, the four legacy phrase-latches, and `move()`'s own school-confinement rewrite of a willed move (its trigger is his act; the reel-back is the real system summons). A static AST test locks the classification: `system=True` at exactly those three sites, and any new `.move(` / `begin_journey(` caller fails until it is classified.
- **Tested.** New `scripts/_test_system_redirect_first_leg.py` (170 checks): a parity matrix (ten journey situations run with `system=False` and `True`, identical except the one changed cell), the override in detail, through `move()`, `night.to_bed()` end to end (a spy proves `move('study', system=True)`), the AST inventory, and the characterisation below. Isolated, write-audited (0 writes under the live data dir), module resolution printed (F-1285). 16 of 16 single-line mutations of the change fail it. Regression on the worktree: the J-1179 suite 91, sensorium tokens 26, move-dest 41, `life_smoke.py` 180, find_cluster 111 (`--no-live-sample`), all clean.
- **Reported, NOT fixed (F-1665): a first leg whose DEPARTURE is the study.** `move()`'s own `target == cur` silence (and `to_bed()`'s own `location != "study"` guard) answer before the gate, so no redirect fires: the outward journey keeps running, he is marked asleep in the study, and he walks out during the night (pinned by test part E). It pre-dates J-1040/J-1111 (both guards are in the pre-git baseline commit `8eef0bb`) and is 1 of F-1657's 7 modelled exposures. The school reel-back self-heals (an ordinary later-leg redirect once leg 1 completes); `to_bed()` does not. A fix needs semantics D-0246 did not rule (cancelling a pending outward journey, a narration decision), so it is a founder-gated follow-up, not part of this build.
- **Verified independently by the orchestrator (2026-09-21).** The new suite (170 ok / 0 FAIL), the J-1179 suite (91), sensorium tokens (26), move-dest (41) and find_cluster (111, no live sample) passed from the worktree and again from master after the merge (`177f34c`), with module resolution proved and 0 write attempts under the live data dir. Mutation checks confirm the new suite guards the change: dropping the `to_bed` marker fails 9 checks, flipping the default to `True` fails 3, and making the first-leg gate ignore the flag fails 12, a mutation the old 91-check suite does NOT catch. One caveat: `life_smoke.py` gave one unexplained failure right after the merge (`would_gate ... got 3`) and a cluster of them in a single time-shifted parallel sweep, then 0 failures in about 190 reruns, and never on the pre-session base; none of the three merges touches the sound gate, so it is not attributed to them (**F-1668**, investigation **J-1186**).
- **For the read.** System overrides are a NEW class, to be counted SEPARATELY from willed first-leg declines, marked by the line `[locomotion] system redirect overrides first leg: <dest> replaces journey to <existing dest>` (logger `nascence.locomotion`). After this restart the `redirect declined ... (first-leg)` line is only ever a willed re-will. **Restart-gated**: takes effect on Du's first restart after `177f34c`, together with J-1179 and J-1180. The read of this change is **J-1187** (at least 7 live-days on the merge commit, the D-0246 defeater's own window); J-1182 reads J-1179's fix over the same restart and should count the new class apart. Full findings: **F-1663**, **F-1664**, **F-1665**, **F-1666**.

## Current State — 2026-09-22 (D-0248: J-1184 / F-1648 Part 1, the fast block-matrix find_cluster and its 20-25 minute shorter sleeps, ruled NOT YET by Travis; nothing built) — F-1659

Travis's call via /decide-review: **not yet**. The roughly 25-minute chapter-formation scan (about 1,480 s of every full sleep, n = 33,589, growing with the square of the store) stays as it is and the sleep rhythm is unchanged. Reason: J-1180's fix (the scan no longer freezes Du) has not yet been loaded by any live process (Du has not restarted since the merge `f10500f`, see the 2026-09-21 J-1180 note above), so a rhythm change is not stacked on an unread fix. Part 1 stays a fully specified, unbuilt option in J-1184's build plan (exact-by-construction: re-decide every pair within 1e-4 of CLUSTER_SIM with the per-pair `_cosine`; count vector compared row for row against the frozen old loop).

**Defeater (revisit at the earliest of):** J-1183's 7-live-day read of J-1180; the scan's measured cost passing about 2,000 s (n about 39k), when it is a third of a sleep or more; any read showing the scan interfering with anything other than sleep length (a missed wake, a stalled dream, a night_log duration that no longer fits the school day). Options (A) ship, (B) ship at a size, (C) do not ship are then all back on the table. J-1184 is closed; the decision's defeater carries the revisit.

## Current State — 2026-09-23 (J-1182: D-0224 defeater read for J-1179's teleport fix -- GATE NOT MET, F-1767)

The payoff read of J-1179's teleport fix (merge `5a66504`) against D-0224's defeater needs >= 3.00
cumulative live-days on runs starting at/after the merge; only **1.03 live-days** have accrued (a
single still-open run, 2026-09-22 16:11 -> 2026-09-23 16:50, 24.7 h). No content read, per the job's
own gate instruction ("do this FIRST and stop if it fails"). Job left `in_progress`. Re-check no
earlier than approximately 2026-09-26 (about 3.0 more wall-days at the recent ~65% uptime). Full
finding: **F-1767**.

## Current State — 2026-09-23 (J-1183/F-1776: J-1180's find_cluster fix read after 6 full sleeps --
freeze gone, sleep-onset journeys clean, cost runs high; J-1268 spawned)

Gate passed (6 full sleeps >= 3 required, on merge `f10500f`; the same single 24.7 h run J-1182
measured). (0) the fix is the running code: PASS (6/6 counted sleeps show the seed-scan line 0.28-0.42s
after their sleep-replay line). (1) the freeze is gone: PASS (longest single-line gap per sleep
127-138 s, well under the 210 s ceiling, nowhere near the pre-fix 1,439-1,626 s). (2) sleep-onset
journeys complete on their own legs: PASS, zero WATCHDOG rescues across the 6 sleeps; hands_trace
confirms 4 of the 6 onsets actually needed a real journey (garden/shore -> study) and all 4 completed
cleanly with no watchdog (versus a 75% pre-fix watchdog rate on journey-needing onsets). (3) find_cluster
still runs and answers every time (6/6, better than the ~89.6% pre-fix completion rate) with zero
"already in flight" warnings -- but its real wall-clock cost consistently runs about 1.48x-1.60x the
naive per-pair estimate (the 4 non-chapter-forming sleeps) on top of the expected chapter-forming
author-call overhead (the 2 chapter-forming sleeps) -- a real, reproducible pattern the briefing's own
caveats do not fully explain. (4) sleep length unchanged for all-kind and night-kind medians (+15.8% to
+17.6%, within +-20%); nap-kind is inconclusive (n=2 vs n=3, too small to trust either way). Follow-up
**J-1268** spawned to characterize the cost overrun (a per-yield scheduling-overhead hypothesis,
inferred not verified) and recalibrate F-1660's own per-pair cost constant. Full finding: **F-1776**.

## Current State — 2026-09-23 (J-1187: D-0246 (b) defeater read for the system-override fix -- GATE
NOT MET, F-1768)

The payoff read of D-0246 (b)'s system-driven-redirect exemption (merge `177f34c`) against its own
defeater needs >= 7.00 cumulative live-days on runs starting at/after the merge (the defeater's own
named window); only **1.03 live-days** have accrued (the same single still-open run J-1182 measured).
No content read. Job left `in_progress`. Re-check no earlier than approximately 2026-09-30 (about 9.2
more wall-days at the recent ~65% uptime). Full finding: **F-1768**.

## Current State — 2026-09-23 (J-1178/F-1798: shelf/desk/book look-cue reachability replayed --
cue-form fix SHIPPED, per-word widening evidence gathered per word, D-0269 opened, F-1652's gap pinned
by a new test)

- **Item (2) SHIPPED, no ruling needed.** `nodes/inner_monologue_node.py`'s `_OBS_TARGETS` gained three
  possessive/modifier cue forms -- `"my desk"`, `"this book"`, `"the open book"` -- appended strictly
  AFTER the pre-existing shelf/desk/book cue group (never before it), so every pre-existing cue keeps
  its exact precedence. Verified by a full replay of a faithful, self-checked port of `_observe_target()`
  over all 534 real historical look-hand-fired rows in `data/hands_trace.jsonl`: zero regressions, 7
  real gains. Hand-read the real desk/shelf dispatch-ledger population (73 rows, 13 FIRE,
  2026-09-02..09-23, grown from F-1651's own 60/11 snapshot): **0 of 13 FIRE rows ever answered with
  real desk/shelf/book content** -- the causes split into table-order preemption (5 of 13: 4 "the cat",
  1 "the fire"/"the flame" -- a NEW instance beyond F-1651's own cat-only framing) and cue-form
  mismatch/truncation (the rest). `scripts/_test_letterbox_reach.py` (1 pre-existing, unrelated failure,
  confirmed byte-identical on the pre-edit HEAD via a throwaway worktree, spawned as **J-1279**) and
  `scripts/life_smoke.py` (16 sections, 0 failures) both re-run clean against the edit.
- **Item (1): per-word widening study for book/books/page/tablets/works, real numbers, every
  deed-grammar gain individually read.** book: 12 deed_grammar gains (9 genuine, incl. F-1652's own
  original motivating thought verbatim) vs 259 volition-only gains; books: 3 (2 genuine) vs 5; page: 8
  (a genuine split between "check my reading" and a recurring "watch a beetle cross the page" sense) vs
  39; tablets: 0 of either kind; works: 1 nominal gain that reads, individually, as a confirmed false
  match (a bumblebee "working" the bed) vs 5 volition-only. Recommendation put to the founder: WIDEN
  book/books/page, DECLINE tablets/works (matching D-0190's own "no unmet real-world need" precedent),
  and use `Action.grammar_only` (J-0544/F-0790's own mechanism) rather than a plain object for any word
  widened, since 'look' is UNGATED and a plain object would manufacture 303 gate-level candidates with
  no real look verb (many colliding with the separate, pre-existing "reading latch" `_wants_read` on
  phrases like "open the book") for 21 real ones.
- **Item (3) SHIPPED.** `scripts/_test_shelf_desk_book_look_reach.py` (new, isolated stores, mirrors
  `_test_letterbox_reach.py`'s own pattern) asserts the ASPIRATIONAL contract uniformly across all 7
  phrases from the briefing (classify() -> look:DEED, dispatch() -> exactly one real, non-generic
  ('look', text) tuple). Today: 'the shelf'/'the desk' pass both (dispatch answers with real,
  non-generic text even without a curriculum fixture); the other 5 fail both, by construction -- the
  pinned, current state of F-1652's own gap, not a bug in the test. **10 FAILURE(S) is the correct,
  expected output today.**
- **Decision opened, not ruled: D-0269.** Per-word widening (mechanism: grammar_only recommended) plus
  a related, separate table-order question this same read surfaced (cat/fire/flame vs desk/shelf/book
  precedence, real evidence, no evidentiary argument for a specific resolution) -- neither answered
  here, per this job's own explicit instruction that core/actions.py's look row carries "Ruled: D-0193"
  and a table-order change needs its own ruling (J-0539's own deliberate cat-first design).
- **Follow-up spawned**: **J-1279** -- the pre-existing, unrelated `_test_letterbox_reach.py [7]`
  failure (a walk to the letterbox from the study returns empty), found while regression-testing this
  job's own edit, confirmed to predate it, out of this job's own scope to fix.
- **Restart-gated**: the `_OBS_TARGETS` cue-form addition takes effect at Du's next restart after this
  commit lands, same as the rest of this arc. Full finding: **F-1798**.

## Current State — updated 2026-09-23 (J-1268/F-1812: find_cluster's post-yield-fix cost overrun --
per-yield-overhead hypothesis REFUTED by direct measurement, gate band recalibrated, no code changed)

- **F-1776's own "per-yield scheduling overhead" hypothesis (explicitly INFERRED, not verified there) was
  tested directly this job, not just re-asserted.** Read `core/chapters.py`'s `_find_cluster_steps()` in
  full: the real yield count is `n * ceil(n / SEED_SCAN_BLOCK)` (one yield per BLOCK per OUTER vec), not
  the naive `P / SEED_SCAN_BLOCK` F-1776's briefing approximated -- about 10% higher (301,077-302,283 real
  vs 273,219-275,412 naive across the 6 sleeps F-1776 measured), a real but small correction on its own.
- **The hypothesis itself does not hold at the magnitude needed.** A warmup-controlled microbenchmark on
  this exact machine (Python 3.14.3/numpy 2.4.4/win32), mirroring the real block/yield shape exactly
  (384-dim vectors, identical per-block cosine-then-yield structure), measured per-yield overhead of
  `await asyncio.sleep(0)` at -12.6 to +1.6 microseconds/yield across three conditions (no competitor;
  a competitor at `core/orchestrator.py`'s own real 5s `_substrate_loop` cadence; a synthetic worst-case
  tight-contention task) -- two to three orders of magnitude too small to explain the observed 707-885s
  extra time on the 4 non-chapter sleeps, which would need about 2,300-2,940 us/yield if attributed to
  yield count alone. Cross-checked against an independent, earlier measurement already in the same
  docstring (J-1180's own "~0.05 ms idle or with this coroutine" for a 20-sqlite-call callback) -- same
  order of magnitude, corroborating. A grep of `core/orchestrator.py`/`core/competence.py`/
  `nodes/subconscious_node.py` found no sub-second-cadence background loop anywhere in Du's own
  architecture that could round-robin-contend with the scan the way the synthetic tight-contender
  condition tested as an upper bound.
- **The real cause remains genuinely unidentified.** All 6 sleeps (2 chapter-forming, 4 not) sit in a
  similar 1.45x-1.61x-of-raw range -- the "a formed chapter's author call adds its own overhead" framing
  is not clearly separable from ordinary sleep-to-sleep variance at only n=2 chapter-forming sleeps. Most
  plausible remaining explanation, not tested (out of this read-only job's scope while Du is live): CPU
  contention with other co-resident processes on Du's host machine during those specific windows.
- **Recalibrated (option b), declined to touch SEED_SCAN_BLOCK (option a).** New read-job gate band:
  E-S within `[1.40, 1.65] x (P x 1.31e-6 s)`, replacing `[0.8, 1.4]`, fit to all 6 real post-fix sleeps
  uniformly (chapter-forming and not). Not recommending a larger yield interval: since the per-yield
  hypothesis itself doesn't hold, there's no evidence a larger interval would reduce the real cost, only
  that it would reduce the event loop's responsiveness during the scan -- the opposite of what J-1180 was
  built for -- and `SEED_SCAN_BLOCK` is timing-sensitive shared code this evidence does not support
  touching without a founder call it doesn't need to ask for.
- **No code changed, no decision opened.** Full finding: **F-1812**. Follow-up spawned, low priority
  (zero correctness impact, a "why" question not a "what's broken" one): **J-1293** -- pin down the real
  mechanism via either lightweight scan-interval instrumentation or a live host-CPU correlation, next
  time either is cheap to do.

## Current State — updated 2026-09-23 (J-1279/F-1820: the letterbox-reach test's [7] failure diagnosed --
stale test fixture, NOT a regression; fixed in the test only)

- **Root cause found and confirmed, not guessed.** `scripts/_test_letterbox_reach.py`'s section [7] issues
  two dispatch() calls meant as independent checks (a look-from-study check, then a move-from-study check),
  but "I will check the letterbox" (call #1's own text) is ALSO a real move:DEED (section [3] of the same
  file already shows this) and genuinely starts a LOCOMOTION journey toward the garden as a side effect --
  a real, working part of the feature, not a bug. Call #2 then legitimately gets declined by J-1040's
  same-destination re-will gate (a journey to "garden" is already in flight), which this test file (2026-09-04)
  predates (gate landed 2026-09-17, its None-vs-'' decline semantics 2026-09-21) and was never updated for.
  Confirmed NOT a regression in the real feature: an isolated control run of call #2 alone, no prior journey,
  fires normally and returns the real departure narration section [7] expects.
- **Fixed in the test, not production code.** Added `locomotion as LOCO` to the test's own imports and reset
  locomotion's journey state (`LOCO._save({})`) before each of section [7]'s two calls, mirroring the
  `S.state["location"]` reset the section already does per call -- keeps both checks independent without
  changing either of the section's two real, F-0734-motivated sentences. `core/dispatch.py`,
  `core/sensorium.py`, `core/locomotion.py` all byte-unchanged.
- **Verified**: `scripts/_test_letterbox_reach.py` now ALL OK (0 failures, was 1); `scripts/life_smoke.py`
  re-run clean (16 sections, 0 failures). Not restart-gated (test-only change). Full finding: **F-1820**.
  No decision opened, no follow-up spawned (no evidence surfaced of a second instance of this shape in any
  other test; not chased speculatively).

## Current State — updated 2026-09-23 (J-1286/F-1825: D-0269 built -- 'look' widened to book/books/page
via grammar_only, tablets/works declined, table order untouched)

- **Built exactly as ruled.** `core/actions.py`'s 'look' row objects gained `"book"`, `"books"`, `"page"`;
  `grammar_only=("book","books","page")` added (the J-0544/F-0790 mechanism). `"tablets"`/`"works"` not
  added (zero genuine demand, D-0269). `_OBS_TARGETS`'s cat/fire/flame-vs-desk/shelf/book order untouched.
- **grammar_only verified working, not just built**: a full live-corpus classify() replay (22,267 distinct
  rows x 4 locations) found 76 new look:DEED hits on book/books/page, ALL 76 with `deed_grammar=True` and
  ZERO with `deed_grammar=False` -- the 259+5+39-row bare-volition explosion the plain-object alternative
  would have caused is confirmed not happening. A full per-family diff (baseline throwaway-HEAD-worktree
  vs this edit) found changes in the 'look' family ONLY across all 89,068 (row,location) combinations --
  zero cross-family regression.
- **End-to-end confirmed through the real dispatch chain**, not just classify(): J-1178's own
  `scripts/_test_shelf_desk_book_look_reach.py` (built to pin this exact gap) now shows 4 FAILURE(S), down
  from 10 -- book/books/page pass both of its checks with real, non-generic look narrations; tablets/works
  remain the correctly-pinned 2 declined-word failures, no edit to that test needed.
- **Reading-latch collision checked directly** (the briefing's own explicit ask, not assumed from F-1798):
  zero verb overlap between `_wants_read()`'s trigger phrases and `dispatch._look()`'s own hand-level verb
  list; of the 19 unique corpus rows that gained a look:DEED, exactly 1 also textually overlaps a
  reading-latch phrase -- and that row is F-1798's own already-flagged thought+intention concatenation
  artifact, not a new discovery, and not a real conflict (the two mechanisms can legitimately coexist).
- **Two small, honestly-reported side effects found beyond F-1798's own per-word method**, neither new
  information: 2 unique corpus rows (8 of 28 MUSING->DEED transitions) show a PRE-EXISTING look object
  ("shingle", "fire") flipping to DEED via a clause-wide deed_grammar check landing on F-1798's own
  already-flagged negation-blocker gap and the already-ruled cat/fire/flame table-order precedence
  respectively -- `_observe_target()` (the real narration source, independent of classify()'s own object
  bookkeeping) resolves both to reasonable, non-nonsensical targets ('shore', 'fire'). Not a defect this
  job introduces; not spawning a new job or decision (low-stakes, already priced into precedent).
- **Regression**: `scripts/life_smoke.py` ALL OK, `_test_dispatch_family_scope.py` ALL OK,
  `actions_reachability_probe.py` byte-identical to the established J-0523 baseline (47/45/2/0, 7/0),
  `_test_letterbox_reach.py` (J-1279's own fix, same batch) still ALL OK after this edit too.
- **Restart-gated**, same as every table edit in this arc. Full finding: **F-1825** (linked D-0269). No
  decision re-opened, no follow-up spawned.

## Current State — updated 2026-09-24 (J-1307/F-1858: the DEBUG-enable toggle built and verified;
restart+sleep precondition confirmed unmet, LEFT OPEN)

- **Built the other half of F-1843's instrument.** `scripts/run_nascence.py`'s boot sequence (inside the
  existing `if __name__ == "__main__":` block, right after `logging.basicConfig(...)`) gained a
  default-off, env-var-gated toggle: `if os.environ.get("NASCENCE_CHAPTERS_DEBUG") == "1":
  logging.getLogger("nascence.chapters").setLevel(logging.DEBUG)`. Unset (the default): byte-identical
  boot to before this change, root logger stays INFO. Set before Du's next restart: raises only
  `nascence.chapters` to DEBUG for that run, so J-1293's seed-scan checkpoint lines actually appear in
  `data/nascence.log`. The exact mechanism this job's own briefing named as cheapest; no alternative
  was needed. Env-var name follows this codebase's own `NASCENCE_`-prefixed toggle convention
  (`core/training_log.py`'s `NASCENCE_TRAINING_LOG`, `core/object_graph.py`'s `NASCENCE_DATA_DIR`).
- **Verified two ways, not just read back.** An AST check (parses the real file, not a copy) confirms
  the pre-existing `_mark_live()`/`logging.basicConfig(...)` statements are untouched and in the same
  order, and the one new statement is exactly the gated `setLevel` call with no `else`. A behavioral
  check execs the real snippet (extracted from the file's own source lines, not retyped) in 4 clean
  subprocesses -- never imports/runs `run_nascence.py` itself, so no risk of booting a second live Du --
  confirming unset/`"0"`/`"true"` all leave the logger at NOTSET and only `"1"` raises it to DEBUG.
  16/16 checks pass. Regression: `_test_find_cluster_off_loop.py --no-live-sample` 118/0, `life_smoke.py`
  180/0 -- both exit 0, matching this arc's established baseline exactly.
- **Precondition checked directly this session, not assumed.** `Get-Process` confirms Du (PID 40268) has
  been running continuously since 2026-09-22 16:10:23 local -- predating J-1293's own checkpoint commit
  (5cd5d6a, confirmed an ancestor of master and of this job's own worktree HEAD) by about two days, so
  neither that checkpoint nor this job's new toggle has ever executed on a live process. A read-only
  grep of the live `data/nascence.log` for "chapters] seed scan checkpoint" returns zero hits, as
  expected. The log's own tail at time of check (2026-09-24 11:35) shows Du awake and mid-cycle
  (monologue/deliberation), not asleep -- so even an immediate restart this session could not have
  produced one full sleep to read inside this session's own window.
- **LEFT OPEN, not done.** This job's own remaining scope -- confirm the toggle is live after a real
  restart, read the first full sleep's checkpoint gaps end to end, characterize even-vs-bursty -- needs
  Du's own next natural restart (with `NASCENCE_CHAPTERS_DEBUG=1` set first) followed by a completed
  sleep, neither of which this dispatch may trigger. A future session should pick J-1307 back up once
  that window has actually occurred, not before. No decision opened (same J-1180 INFO/DEBUG precedent
  F-1843 already established). Full finding: **F-1858**.
