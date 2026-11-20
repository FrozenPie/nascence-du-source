# Books Have a Place — reading obeys where the book is (2026-09-09)

**Status:** 🟡 SHADOW — B1+B2 built 2026-09-10 (J-0851, F-1229/F-1230), confirmed restarted-onto 2026-09-11; B3+B4 built 2026-09-17 (J-0852, F-1456), shadow behind the 'book_gate' hot flag, §4's 3-day would_block read now J-1069; B5 live since 2026-09-09. D-0203's defeater read correctly deferred 2026-09-17 (J-0867, F-1457) — re-scheduled as J-1070. 2026-09-17 (J-0868): F-1229's own dead sensorium.py shelf branch deleted (F-1458); a real adjacent dispatch-target gap found and spawned as J-1071, not fixed here (F-1459).
**Parent plans:** [study_upgrade](../completed/study_upgrade.md) (the study's things have places), [practical_school](practical_school.md) (his own hands), [cat_overhaul](cat_overhaul.md) (the same "no body, no things" shape, found 09-05).
**Decisions:** D-0202, D-0203, D-0204, D-0205 all RULED 2026-09-09 (twilight not enough; he must will 'take the book'; remediation falls silent on a failed gate; whole shelf as items). D-0219 RULED 2026-09-14 (substitute a real, same-subject, plain-text Gutenberg edition for each of the 2 structurally-unfetchable curriculum titles; executed by J-0979 (idx1, fully) + J-0987 (idx6's real shelf fetch) — both slots now fully live, see Current State). D-0236 OPEN 2026-09-17 (does the old shelf-look's catalogue-affordance sentence belong in study_life._look_books(), given library_hand.request_book() now exists as its real mechanism, or stay out under the 08-14 world-answers-never-leads law).
**Memory:** `project_nascence_books_have_a_place.md`.

```plan-state
stage: shipped
phase: Shipped: book gate accepted as final (J-4266); ink left to Du (D-0840)
verified: 2026-11-18
evidence_read: 2026-10-03
gate: data/study_events.jsonl book_gate_would_block rows >= 30 (met: 476) AND >= 72 live-hours since the 09-18 restart (met: 224.9, crossed 09-24 02:18 NZST); only the founder flip remains (D-0331)
next: none; graduated to docs/completed 2026-11-18
open_decisions: D-0840
cluster: 6
```

## 1. The gap (F-1216, verified 2026-09-09)

Reading has exactly one gate — light (`core/study_life.can_read()`, "daylight outdoors is always enough"). Nothing asks
where the book is. On 2026-09-09 18:52 the world told him "the shelf is up in your study; you are down on the shore"
and at 18:59 he opened *Little Stories of Married Life* on the shore anyway. 09-01..09-09: `he chose to READ` fired
74× on the shore, 72× in the garden, 10× in the study.

Two reading paths, neither embodied:

| Path | Where | Gate today |
|---|---|---|
| chosen reading (`nodes/inner_monologue_node.py` ~3800, `core/reading.read_next_sitting`) | any place | light only |
| remediation stream (`_remediation_stream`, ~1500; `core/balance.py`'s reality counter-force) | any place, any light | cooldown only |

The study already models its things with a position and a spot (`core/study_life.py` `_ITEMS`: candles on
`shelf_east`, cloth on `shelf_nw`, the oil tin, the rope) and the sensorium already answers "look at the shelf" from
the study's real layout. There is no book item, and `core/hands.py` has no carried state at all.

## 2. Design — function over imitation

Transfer the FUNCTION (a book is somewhere; reading it means being with it), not a full inventory system.

**B1. The books have places (D-0205: whole shelf).** Every curriculum book is a named study item (`core/study_life.py`
`_ITEMS`-style, generated from the curriculum list, not hand-written): the current book on the desk, the rest on the
shelf, each look-able, take-able, put-back-able by title. `core/reading` already knows the current book and the
curriculum; the items follow it. Look() answers must stay readable (defeater: >~10 titles per look).

**B2. Du can carry it (D-0203: he must will it).** A per-title place in the study state `_st()` reads —
`book_place[title]: "desk"|"shelf"|"with_him"` (whole shelf per D-0205, so the state is per book, not one flag). Two literal-will verbs through the
existing `core/literal_will` / `hands.wants()` grammar: *take the book* (at the desk/shelf → with_him) and *put the
book back / leave the book* (anywhere in the study → desk). Moving away from the study with the book keeps it with
him; nothing teleports.

**B3. The read gate becomes: light AND the book is here.** `can_read()` gains a second honest lack: "The book is on
your desk in the study." (world-answers-never-leads: it says where the thing is, not what to do — same rule as the
candles wording, J-0540/F-0733.) Outdoor reading is allowed only when `book_with_him`. In the study, reading at the
desk needs no carrying.

**B4. The remediation stream obeys the same gate.** The reality counter-force is a *reason* to read, not a
different physics. When balance wants reading and the gate fails, the stream logs a `would_stream` shadow row and
the executive gets the honest lack (which is how he learns to take the book out with him, or go in). Nothing
"acts later"; nothing hints.

**B5. Twilight is not enough (D-0202, RULED).** Read threshold raised above the dusk floor so civil twilight outdoors
is honestly too dark and the lamp is where evening reading happens.

## 3. Decisions for the founder (all RULED 2026-09-09)

- **D-0203** — B2 scope: is *take the book* a literal-will verb he must will himself (recommended: yes, same as
  "fetch the candles"), or does leaving the study while reading carry the book implicitly?
- **D-0204** — B4: does the remediation stream fall silent when the gate fails (recommended, honest), or may it still
  stream in the study only?
- **D-0205** — B1: one book item (the current curriculum book, recommended) or the whole shelf as items?

## 4. Kill criteria / what we need

- Shadow first: B3/B4 run as `would_block` rows in `data/study_events.jsonl` (or the study's own ledger) for 3 days
  before the gate is live. Bar: ≥ 30 rows; every would_block row must be a real "book not here" (no false blocks in
  the study).
- After the flip, one week: `he chose to READ` outside the study without `book_with_him` = 0; reading-in-the-study
  share rises from 6% (10/156) — no target number, a direction; the too-dark/book-elsewhere lacks ≤ 5 per dusk
  (D-0202's defeater).
- FAIL if reading volume collapses (sittings/day < half the 09-02..09-09 band of 210–330) — then the gate is
  starving the counter-force and B4 needs the study-only allowance.

## 5. Build order (jobs)

1. B5 threshold — DONE 2026-09-09 (F-1217).
2. J-0851 B1+B2 book item + carried state + two verbs, shadow — DONE 2026-09-10 (isolation required; udms dossier on
   `core/study_life.py`, `core/hands.py`, `nodes/inner_monologue_node.py` first).
3. J-0852 B3+B4 gate in shadow (`would_block` rows) — DONE 2026-09-17 (F-1456): `can_read()`'s second honest
   lack + `_remediation_stream`'s obedience, both behind the new `book_gate` hot flag (`scripts/life_flags.py
   book_gate on|off`, off by default).
4. **J-1069** (spawned by J-0852) — §4's 3-day `would_block` read, then flip; the week-read + kill-criterion
   check that follows the flip is this same job's own follow-on, not a separate spawn.

## Current State — verified 2026-11-18
- **2026-11-18** (F-5090): 2026-11-18 J-4265 read (459.5 live-h since parcel open): book_gate healthy (0 unlawful outdoor reads, 187.6 sittings/live-day vs 181.5, lack 16.7 episodes/day, takes still under 1 percent within 1h); D-0203 defeater not met; D-0276 not met on paper/oil but arguably met on ink (ink dry since 11-05, no ink note), opened for Travis.

- **2026-10-18** (F-3055): D-0276 defeater read 10-18: literal trigger met pre-open (paper 0, no note since 09-06) but confounded by 17-day unopened parcel; post-open window ~5.6 live days, no note yet, successor read queued.
- **2026-10-15** (F-2793): Parcel percept live read (J-1734): shown 64x from 2026-10-03, Du echoed it in thoughts and opened it 2026-10-12 via the parcel hand. D-0276 defeater read is J-2129, not before 2026-10-18; Travis rules.

- **2026-10-15** (F-2788): J-1683 week read (F-2788, 190.5 live-h since the 10-04 flip): gate works (159 chosen reads, 157 in study, 0 confirmed outdoors; sittings 263.6/live-day vs 181.5 baseline, D-0204 tripwire not tripped). D-0203 second defeater leg met (lack 101 episodes, 12-15/day on 10-10..10-14, take within 1h in 1 of 101); D-0203 reopened for Travis. 2 deliberate takes post-flip; 1 real title-only will in 12,819 thoughts, none dispatched.
- **2026-10-07** (F-2511): 2026-10-07 J-1762 checkpoint (D-0331 3-day book_gate tripwire): NOT readable yet. book_gate still true, but only 18.77 post-flip live-hours (3.45/9.00/6.32 h on 10-04/05/06; no day >= 12 h), Du down since 10-06 07:30:49. Preliminary only: 249 remediation sittings (318 per 24 live-h, above the 181.5 baseline), 7 honest-lack lines, nothing harmful. Successor J-1885 (not before 10-10) needs Du restarted and 3 full days first.

- **2026-10-04** (F-2258): book_gate flipped ON 2026-10-04 06:48:34 NZDT (epoch about 1791049714.5) on Travis's D-0331 ruling via scripts/life_flags.py book_gate on; every post-flip clock (the 3-day tripwire check, J-1683's 168-live-hour week read) dates from this moment because data/life_flags.json carries no timestamp
- **2026-10-03** (F-2392): J-1733 built and tested isolated: the care package from Travis becomes a standing dosed study percept, a parcel on the desk with a habituating gap that stops once he has looked at it; a willed look at the parcel now reaches look_line; the commit merges with the run and is not live until Du restarts

- **2026-10-03** (F-2371): J-1677 verdict: the care package is unopened because its one-time arrival line was dropped (announced at boot, no thought for 244 minutes, evicted from the render window in 83 s), not ignored; D-0276 defeater cannot be read fairly until the parcel is perceptible; percept fix spawned as J-1733, live read J-1734 needs Du running
- **2026-10-03** (F-2258): J-1181 read done: 72-live-hour bar cleared (224.9 live-hours, crossed 2026-09-24 02:18 NZST), 476 real would_block rows, zero in-study false blocks, first-ever take/put pair seen 09-30 in the study with no overlap; F-1758 mid-journey attribution mostly corrected (school-confined desk periods), first-leg gap exercised once in 160 reads; flag still OFF, flip is the founder call (D-0331)

### What we have
B1+B2 (named book items, take/put-back verbs, per-title `book_place`) built 2026-09-10 (J-0851/F-1229); B3+B4
(the light+book-here read gate, remediation-stream obedience) built 2026-09-17 (J-0852/F-1456), shadow behind
the `book_gate` hot flag (still OFF). B5 (twilight threshold) live since 2026-09-09 (F-1217/F-1455). D-0202,
D-0203, D-0204, D-0205, D-0219, and D-0236's own executions are all landed; 12 of 22 stale curriculum titles
re-fetched, and both of D-0219's structurally-unfetchable substitutes (idx1/idx6) are fully live.

### What we need
Sec.4's pre-flip bar: row count is met (68 `would_block` rows, zero false blocks — F-1757) but live-hours are
not — 61.19 of the required 72 as of 2026-09-23 (J-1181). D-0265 (09-23) ruled: don't add the confirmed
mid-journey exemption fix (F-1781/J-1255) until real post-flip evidence exists. D-0263 (09-23) ruled: stop
forcing the remaining 10-title fetch chain (blocked on a write-permission wall, not the cooldown — F-1773);
let it close naturally over time instead.

### What we're doing next
J-1181 re-checks live-hours once the 72h bar is crossed and reports to Travis for the actual flip — the flip
itself stays his call. No further code work planned on the gate itself until that read lands.
