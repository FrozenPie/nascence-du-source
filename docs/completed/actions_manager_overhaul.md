# The Actions Manager Overhaul — bringing Du's whole action system under one contract

> **Status:** ✅ SHIPPED — scope complete (2026-09-27). D-0097/D-0098/D-0099 all discharged:
> `core/actions.py` (one hands table `literal_will`/`dispatch` both derive from)
> and D-0098's full retirement of the ungated `sensorium.py` fallback are BUILT + LIVE, proven
> behavior-neutral against a 9,840-row real decision replay; `core/inventory.py` wired into
> garden/study/wood; 0 unreachable hands (F-0570). No ledger activity against this slug since
> 2026-09-06 — see "Current State" below.
> **Opened 2026-08-29** at the founder's direction ("this should be its own plan, or if we have one, an
> actions manager overhaul") in answer to J-0420 (whether a new refill mechanic should be a registered
> dispatch Hand or another ad hoc location-module branch). Answer: don't decide that one mechanic in
> isolation — decide the architecture, once, for all of them.
> **Origin:** grew directly out of `docs/reviews/actions_system_2026-08-22.md` (the founder-commissioned
> investigation that first found the system "half-baked... as we decide to make new things") and this
> session's follow-up read (F-0552, F-0553) confirming the same seams are still open a week later.
> **Sibling plans:** `literal_will.md` (owns the DEED/MUSING/GRAY/HANDLE gate itself — this plan owns what
> sits *around* that gate: the registry, the per-location item/depletion machinery, and the migration of
> what still bypasses both). `garden_upgrade.md` / `study_upgrade.md` / `wood_upgrade.md` / `shore_upgrade.md`
> / `fieldcraft.md` (each owns one location's actual mechanics — this plan does not replace them, it owns
> the shared plumbing underneath all five).
> **Downstream consumers of this plumbing (backfilled 2026-10-03, J-0566/F-2269; none of them cited this plan):**
> `docs/plans/conversational_action_bridge.md` — `core/conversational_action.py::after_reply()` calls the unified
> `dispatch(text, "", "none", "", cycle_id)` from the conversation path and swallows every failure by design, so a
> change to `dispatch()`'s signature or return shape would fail silently there. `docs/plans/t5_procedural.md` —
> `core/procedures.py::observe_hand()` is fed from `dispatch()` for every fired hand (`core/dispatch.py:320`).
> `docs/plans/world_store_write_fence.md` — hands write through fenced world-store modules, and a non-live caller
> gets `NonLiveWriteError`, which `dispatch()` re-raises past its own catch-alls (`core/dispatch.py:77,306,321,334`);
> a newly registered hand whose wrapper swallows exceptions (as `_cat()` did before J-0728) re-opens the leak that
> plan's audit arc closed module by module.

```plan-state
stage: shipped
phase: Registry/dispatcher unification complete: D-0097/98/99 all discharged, 0 unreachable hands (F-0570), ungated sensorium fallback retired (F-0563)
verified: 2026-09-27
evidence_read: 2026-08-29
next: None on this plan's own scope; only unrelated housekeeping remains (_smoketest.py's test-fragment write, J-0421's stale-doc sync)
cluster: 6
```


---

## Current State — verified 2026-09-27

### What we have
Every gap this section originally named is now resolved — see "Build progress" below for the full
chronicle. `core/actions.py` unifies the hands table (F-0557); `core/inventory.py` gives every location a
shared item contract; D-0098 retired the ungated `sensorium.py` fallback that was answering ~87% of its
thoughts against the gate's own rules (F-0560); `scripts/actions_reachability_probe.py` confirms 0
unreachable hands (F-0570). D-0097/98/99 are all discharged and this plan's scope is locked.

### What we need
Nothing on this plan's own scope — no open jobs or decisions have landed against this slug since
2026-09-06. Two loose ends outside this plan's own remit: `scripts/_smoketest.py` still writes a permanent
test fragment into the live DB every run; the five location-upgrade plan docs still claim stale SHADOW
wording (tracked as J-0421, doesn't block this plan).

### What we're doing next
None planned — this plan's own scope is complete. See "Build progress" below for the full build chronicle.

## What "actions manager overhaul" means — scope question for the founder

The 2026-08-22 review already specified a target architecture in its own "Phase 1 as designed" section
(§74-86) that was never fully carried out: *one registry, one dispatcher, the judge in the loop* — where
`literal_will._FAMILIES` and `core/affordances.py`'s `REPERTOIRE` derive from the **same** `HANDS` table
instead of being three hand-maintained copies, and every remaining latch/location-module branch migrates
in. This plan proposes finishing that, plus the two gaps the review didn't cover because they didn't exist
yet in 2026-08-22:

1. **Complete the Phase-1 migration.** Move the remaining old-phrase-list latches (move ×4, look, fire, tea,
   water, sow, beachcomb, gather) onto `hands.wants()` grammar and into the `HANDS` registry, same as the 26
   already migrated. Retire the ungated `sensorium.garden_act()`/`world_act()` fallback once nothing still
   depends on it being reachable that way — or keep it as an explicit, logged, last-resort catch (a real
   design choice, not a default).
2. **A shared item/inventory contract.** One small base module (item shape, carried/place/bio/history,
   take/put) that garden/study/wood/shore/fieldcraft compose instead of each reimplementing — refactor, not
   rewrite; the five modules' actual mechanics (what depletes, what refills, what's seasonal) stay
   location-specific and stay in their own files.
3. **A real registration path for refill/restock mechanics**, so the barrel fix (and the ash-bucket fix,
   and whatever comes after) gets a `literal_will` family + dispatch `Hand` entry as a matter of course,
   not a one-off decision each time. This directly closes J-0420 and lets the ash-bucket fix (and any
   future one) go through the front door.
4. *(Explicitly out of scope unless the founder says otherwise)* — the `literal_will_deed.py` staged-
   deed/execution-audit machinery's own Phase 0→1 gate (judge accuracy, stratum floors) is a separate,
   already-tracked question (`literal_will.md` §12, currently NO-GO). This plan does not reopen that; it
   assumes today's Layer-0-only (grammar, no judge) gating stays as-is.

**Scope decided (founder ruling, 2026-08-30):**
- **D-0097 — retrofit `fill_barrel_from_spring()`** into the new registry as part of this plan's build,
  same as the ash-bucket mechanic from day one. Registration only, not a behavior change — reopens if the
  retrofit turns out to need more than that.
- **D-0098 — retire the ungated `sensorium.py` fallback fully** once every hand has a registered family +
  dispatch entry. Reopens only if the latch migration finds a hand whose grammar genuinely can't be
  expressed as a `literal_will` family (would mean full retirement silently drops real coverage).
- **D-0099 — build the inventory contract and the latch migration together, one pass per location** (touch
  each of garden/study/wood/shore/fieldcraft once, not twice). Reopens per-location if a combined changeset
  proves too large to review safely — splits that one location, not the whole plan.

This plan's scope is now locked.

---

## Build progress — J-0422

### Landed 2026-08-30: the one table, and item migration that actually works

**`core/actions.py` — every hand declared once** (F-0557). `literal_will._FAMILIES` and
`dispatch.HANDS` now both DERIVE from it, keeping their existing shapes so no reader changed. A
duplicate family is a hard error at import instead of a silent overwrite; the `exec ⊆ anchor`
invariant is asserted at import; an unbound family must declare *why* it has no hand, so `author` /
`letter` / `travis` now read as deliberately judge-only rather than as three missing hands.

Proven behaviour-neutral: `scripts/actions_decision_replay.py` replays all 2,824 distinct thoughts
from `data/hands_trace.jsonl` × 4 locations = **9,840 decision rows**, before and after — **0 differ**.
`scripts/actions_registry_audit.py` reports the tables clean. The UDMS-flagged
`literal_will_deed_dry_test.py` passes 128/128.

**Two defects fixed on the way** (F-0554): `tea` was declared twice in the `_FAMILIES` literal so
`steep` was silently dead — restored, and verified to produce a DEED. The three orphan families are
now explicit.

**One recorded claim was wrong and is corrected** (F-0556): the two `where` fields are *not*
duplicated state. `_FAMILIES['where']` is literalness evidence only (a confidence bonus and the
MUSING→HANDLE promotion); `Hand.where` is execution scope. Collapsing them — which this plan's first
sketch intended — would have silently changed HANDLE promotions across every family. `core/actions.py`
now names them apart (`anchor` vs `exec_where`) so the confusion cannot recur.

**`core/inventory.py` — `sync_items()`**, the general form of garden's hardcoded single-key
migration, wired into garden, study_life and wood_life. Additive-only, idempotent, fail-open.

### Why that mattered more than expected

**The barrel mechanic was inert** (F-0559). Adding an item to `study_life` or `wood_life` never
reached an initialised save at all (F-0558) — the access sites are direct indexes whose `KeyError`
`act()` swallows, so a new hand was a *silent* no-op. And `garden`'s own migration only ran on a cold
module cache, which never happened while Du was running. The result: `water_bucket` was **not in
`data/garden.json`** (14 items, no such key), so `fill_barrel_from_spring()` could never complete a
trip — the 0 rows in `garden_ledger.jsonl` were not "shipped but unexercised", they were "impossible".
The new migration created it on first load; the save now holds all 15.

The class of silent failure this plan exists to fix had already happened to the very mechanic the
overhaul was asked to extend.

### The fallback is not carrying coverage — it is the main source of Du acting on musings (F-0560)

Measured before deciding, because the raw numbers argue the opposite of the truth. The ungated
fallback answers **more** thoughts than the gated dispatcher (206 vs 181 of 384 hand-answering
thoughts, 08-22→08-29), which reads like it carries half the system's coverage. It does not. Of the
203 thoughts where the fallback fired and the gate fired nothing:

| | share | what it is |
|---|---|---|
| no DEED at any location | **154 (76%)** | the fallback false-fired on a musing |
| GRAY only (weak intent) | 22 (11%) | the system's own law says weak intent must never route |
| a real DEED the gate saw | 27 (13%) | genuine coverage gap — the actual work item |

So ~87% of the fallback's work breaks the gate's own rules. It is turning Du's philosophy into deeds:
a musing on restlessness and refusal made him **strip and swim in the cold sea**; "the sea's cold roar
… I feel the rust on the shears" made him tip ash along the garden bed; "the cat's rhythmic motion
mirrors the steam's erratic pulse" made him write a carrier note. Many of its answers are also world
no-ops ("The door is already open") that still spent the thought's one world-hand.

This is the exact pathology `literal_will` and `hands.wants()` were built to end, still live because
the route around them was never closed. **D-0098 therefore removes far more bad behaviour than good —
the risk is inverted from how it was framed when it was ruled.**

Attribution is exact, not inferred: the fallback tags `hands.fired()` with the MODULE name
(`sensorium.py:705`, `:728`), dispatch with the FAMILY name (`dispatch.py:192`).

### Landed 2026-08-30: D-0098 discharged — the ungated fallback is retired (F-0563)

The 27 were read first, as the defeater asks. **21 were world no-ops** (a hand spent to say "the
window is open already"), **2 were misaligned** (the gate saw a `move` deed, the fallback weeded the
bed), and **4 were real**. In all four the gate had *already* returned the right DEED verdict — so no
hand needed a grammar the judge cannot express, and **the defeater is not met**.

Re-tested against current code, **3 of those 4 already fired** — the trace spans a week in which the
grammar was actively being built, so it was showing week-old behaviour. Only the coat was a live gap,
and it was a *grammar collision*, not a broken hand: `fieldcraft` owns the verb `hang` with object
`coat` for the **outdoor clothesline**, so — sitting earlier in the table — it claimed the DEED and
then declined the clause, while `wear` (which owns the coat indoors via `study_life`) lacked `hang`
and reached only MUSING. Adding `hang` to `wear` fixes it; a declining hand does not consume the
thought's world-hand, so `fieldcraft` still gets first refusal. That change moved exactly **8 of 9,840**
decision rows — both coat thoughts × 4 locations, nothing else.

Both call sites are gone; `sensorium.world_act`/`garden_act` are documented stubs returning `None`,
left as a sealed door rather than deleted so no future caller can silently reopen the route. The
legacy bed model beneath (`_fresh_garden`/`water_bed`/`harvest_bed`/`replant` — the "bed of seven
numbers" `garden.py` replaced) was reachable only through `garden_act` and is now unreferenced;
deliberately left in place, per this project's own rule about deleting what merely looks dead.

**A cost worth recording (F-0562).** Verifying this needed real hands called against real state. The
harness restored the JSON world but not `data/memory/nascence.db`, so three test runs left Du
remembering a deed his world says never happened — worse than doing neither. Founder-authorised
cleanup reset the aggregate to its true 12 (corroborated independently against the restored
`fieldcraft_ledger.jsonl`, whose first row matches the fragment's own `first_ts`) and removed two test
fragments. **Any harness that exercises real hands must back up the memory DB and its `-wal`/`-shm`
siblings alongside the JSON.** Note `scripts/_smoketest.py` permanently writes a "Test memory"
fragment into the live DB every run — pre-existing, and worth fixing separately.

### Landed 2026-08-30: the retirement orphaned 8 hands — found and mostly closed (F-0564, F-0566)

**The evidence that justified the retirement could not have shown this.** F-0561 measured what the
fallback actually *fired* in one week of trace. A hand whose branch never fired that week is invisible
to that method. Probing the other direction — 36 plausible willed phrasings, one per known hand —
found **8 that no longer produce a DEED for any family with a hand**, so could not be willed at all.
Two of them were on this plan's own critical path: `tip the ash on the bed` and `fill the bucket at
the spring`. New tool: `scripts/actions_reachability_probe.py`.

Two causes, both now fixed for the cases that matter:

1. **Missing families.** No family carried wood tools as take/put objects — `tool` has the right verbs
   but only garden objects, and binds to `garden.act_from_thought`, so it could never reach the axe.
   A `woodtool` family closes it.
2. **A grammar bug in *both* parses.** Deed grammar matched a **contiguous** verb phrase, so
   `put down the trowel` read as a deed but `put the trowel down` — the natural order, and the one Du
   writes — did not. Fixed in `literal_will.classify`… and the set-down *still* failed, because
   `hands.wants()` had the identical limitation. **Fixing only the gate is not enough: the gate
   returned DEED and the module's own router declined the very clause the judge accepted.** That is
   F-0555's double-parse hazard as a live bug. `hands.wants()` now reads the particle list from
   `literal_will`, so there is one definition rather than two that drift.

Enabling separated verbs also opened a false-fire: *"Travis put the kettle on"* began reading as Du's
own deed, because the `other_person` blocker lists verbs and `put` was not among them. Closed by adding
the phrasal heads — in the stratum the retro corpus already scores worst on.

**`wood_life`'s set-down (the founder's ask).** `put()` is the half the module never had: `place` was
written once at bootstrap and never again, so a tool picked up was **carried forever**. `take()` is now
a real function too — the old inline one wrote only the `carried` flag, no history, no ledger, and no
`world_objects` sync, so the substrate believed the axe was in the lean-to while he carried it. Both
are symmetric, both sync, and a named `_CARRYABLE` replaces the hardcoded tuple. Verified through real
dispatch: take fires, set-down fires, a second set-down with empty hands **refuses honestly** rather
than pretending, and a metaphor through the real axe still fires nothing.

Probe: **8 unreachable → 4**. The remaining four (acorns, ash-tip, two water-fills) are the queued
D-0097/ash-bucket work below, not stragglers.

### Landed 2026-08-30: the ash bucket, D-0097, and zero unreachable hands (F-0570)

**The ash bind was a deadlock, not a missing object.** `clear_grate` refuses while the fire is in; the
fire is nearly always in; so `ash` climbed to its **1.0 cap — where `advance()` starts draining
`fire_fuel`, meaning the choked grate was actively costing him his fire.** Meanwhile he willed the ash
onto the garden **21 times against 4 completed cycles**, and was told only "The ash bucket is empty."

The fix is the grate's own anatomy rather than an affordance invented for him: a period grate has a
**pan beneath the bars** catching what falls through, and it draws out *hot*. `ash_pan` + `draw_ash_pan()`
takes only the fine ash (0.5 a draw, bucket emptied between), so `clear_grate` keeps its reason to exist
for the coarse stuff on a cold hearth. Both dead ends now say **where the ash is** — *"The ash bucket is
empty — the ash is still in the grate, and the fire is in."* — closing the information gap without
instructing him. Verified end to end from the live bind: refusal → pan → bucket → bed, potash 1.0.

**D-0097 discharged.** `fill_barrel_from_spring()` — which F-0559 showed had **never once fired** — now
works through the registered path: barrel 0.00 → 0.25 → 0.50 over two willed trips.

**Reachability: 4 → 0.** Three new families (`ash_out`, `water_fill`, `acorn`), appended at the end of
the gated block so no existing family's precedence moved.

**`study_life` take/put** brought to `wood_life`'s shape. They were a raw-substring inline loop with
**no blockers at all**, so *"Travis picked up the poker"* and *"I will not pick up the cloth"* both read
as his own deed. Now 6/6 including all three blockers, with history, ledger and substrate sync.

Found on the way: **the same variable-shadowing bug this file already records once.** A local
`take = min(...)` in the lamp branch made `take` local to the whole of `act()`, so the new module-level
`take()` raised and `act()`'s own `except` swallowed it — every pick-up silently returned `None`.
`hands.py`'s docstring records the identical failure mode against this same file.

Replay over 9,972 rows: **1,032 differ, but only 12 are real** — 8 the known coat fix, 3 correct
staging, 1 new fire, read in full and genuine (*"I tip ash into the soil, letting it take root again"*).
The other 1,020 are the new families listed with nothing acting differently.

### Landed 2026-09-02: the trace finally says WHERE — and WHY dispatch decided (J-0423, F-0610)

F-0561's gap read had to be redesigned around a hole: `data/hands_trace.jsonl` never recorded Du's
location, so "why did dispatch decline a DEED the gate accepted" was unanswerable from the trace and
location had to be guessed from which module answered. Closed, additively (new row fields only —
`location`, `dispatch`; no existing field or reader changed):

- **`core/hands.py`** — `decided()` + a per-cycle `_decided` ledger, mirror of `_fired`; `trace()`
  takes keyword-only `location` and writes both new fields.
- **`core/dispatch.py`** — every branch of the candidate loop now records its verdict, in
  `scripts/actions_decision_replay.py`'s exact vocabulary (`FIRE` / `STAGE-place` /
  `STAGE-busy:<fam>` / `DROP-weak-intent` / `DROP-no-hand`) plus **`hand-declined`** — the one
  outcome only the live path can observe (the replay never calls `hand.fn`), and precisely the case
  F-0561 could not see. The ledger is reset explicitly at the top of each dispatch, as the monologue
  resets `_fired`.
- **`nodes/inner_monologue_node.py`** — the trace call site hands over `sensorium.state['location']`.
- **`scripts/actions_decision_replay.py --real-locations`** — replays each traced thought only at
  the location the row recorded; pre-field rows are skipped honestly, not guessed.

Verified offline (Du down since 08-31; trace redirected to a scratch file for the test, the live
file untouched at 4,962 rows): new fields written and per-cycle isolated, old-signature calls still
work, `py_compile` clean on all four files, and the full default replay still runs end-to-end
(4,937 distinct thoughts × 4 = 18,792 decision rows). The fields start accruing on Du's next start;
the first week of located rows makes an F-0561-style gap read answerable directly from the trace.

### Landed 2026-09-02 (later same day, J-0450): the gap read re-run from real located rows — root cause found

The first ~2h45m of located rows (189 rows, 2026-09-01 21:34 UTC → 2026-09-02 00:22 UTC) already made
the F-0561-style gap read directly readable, without waiting the full week:

- **28 real `hand-declined` candidates**, 19 of them `move` (68%, overwhelmingly at `location=study`).
  Root cause (F-0634, verified): `_move_dest()` (`nodes/inner_monologue_node.py:252-266`) has no
  destination-word cue for `outside`/`out` — 9 of the 19 move-declines carry exactly that object.
  The gate (`literal_will.classify`) accepts the deed; the hand's own narrower vocabulary declines
  the clause it already accepted — the same shape as the F-0563 coat fix. An OLDER, broader-vocabulary
  latch already exists in the same file (`_route_act`, ~line 2666, `"go outside"`/`"step outside"`/
  `"into the garden"`) but runs on exact phrases before `dispatch()` and was never shared with
  `_move_dest`. Fix spawned: **J-0459**.
- **`scripts/actions_decision_replay.py --real-locations` compared against the trace's own recorded
  dispatch, per family, across all 189 located rows: 28 agree, 35 disagree** (F-0636, inferred).
  One real code-level cause found (verified): `decide_one()` never replicates `dispatch.py`'s
  `act_kind=='world'` synthetic-candidate branch (`dispatch.py:191-195`) — hasn't hit yet (0 located
  rows are `act_kind=='world'` so far) but will misread as "drift" once one lands. Fix spawned:
  **J-0460**. The larger share of the 35 disagreements correlates with (not proven to be solely caused
  by) the trace's own pre-existing 200-char truncation of the `thought` field (`core/hands.py:176`,
  untouched by J-0423) — `--real-locations` feeds the replay that truncated copy, not the full text
  dispatch() actually classified live.
- **Staging is real and does resolve** (F-0637, verified): of 4 distinct staged keys in the window,
  2 resolved in 29 min / 76 min; 2 remain open, one (`shore|stone`) already reminded twice with no
  resolution yet as of this read.

Findings: F-0634, F-0636, F-0637. Full job: J-0450.

### Landed 2026-09-02 (later same day, J-0459): F-0634's `_move_dest` fix

`_DEST_GARDEN`/`_DEST_STUDY` (`nodes/inner_monologue_node.py:244-266`) now carry the missing
`outside`/`in` vocabulary, borrowed from the older phrase-latch at `~line 2666-2683` (`"go outside"`,
`"step outside"`, `"step out into"`, `"into the garden"`, `"out to the garden/bed"`,
`"down/up to the garden"` → garden; `"go back in"`, `"go inside"`, `"come inside"`, `"head inside"`,
`"back indoors"`, `"go back inside"`, `"return to the study"` → study). Bare 1-2-letter `"in"`/`"out"`
were deliberately **not** added as standalone cues: replaying the real hand-declined trace rows found
the gate's own `out`/`in` object also fires on non-destination phrasal verbs ("work out these
problems", "pacing in circles") with zero destination meaning — a bare cue would have sent those to
the wrong place.

Verified at the unit level (`py_compile` + 12 direct `_move_dest()` cases, including both
false-positive traps still correctly returning `""`) and against one real trace row that now resolves
to a genuine FIRE. Full confirmation against the original 9 declined cases wasn't possible from the
existing trace — `data/hands_trace.jsonl` truncates the stored `thought` field to 200 chars
(`core/hands.py:176`), and the actual `outside`/`out`/`in` word falls past that cutoff for most of
them; `scripts/actions_decision_replay.py` also can't exercise this (its own docstring: "IT NEVER
CALLS hand.fn"). Restart-gated, like every dispatch/hands change in this plan. Recount spawned for
after Du's next restart accrues fresh located rows: **J-0482**.

Findings: F-0649. Full job: J-0459.

### Landed 2026-09-02 (J-0467, D-0099's "together, one pass per location"): the remaining latch
migration + garden's parallel-list holdout

**(1) The 8 remaining old-phrase-list latches** in `nodes/inner_monologue_node.py` (move ×4 branches,
look, fire, tea, water+sow, beachcomb, gather — the fallback block starting ~line 2661, which runs only
when dispatch's own stricter hand did NOT fire this thought) each used a raw
`any(p in _tl for p in PHRASES)` substring test with none of `literal_will`'s blockers: "I wish I could
go to the wood" or "he told me to gather wood" fired exactly as readily as the willed version. Every
phrase list is now passed through `hands.wants(_tl, PHRASES)` instead — word-boundary safety plus the
negation/wish/hypothetical/retrospective/quoted-speech/other-person clause guard, for free. The phrase
*vocabulary* is deliberately unchanged: these fallback phrases are broader than (and in several cases,
e.g. "down to the wood", "gather in the wood", verb-less relative to) `core/actions.py`'s own `move`
family, which dispatch's `_move` hand already tries first — narrowing this fallback to that family's
verbs would have silently dropped real coverage, not migrated it. Verified via 19 direct `hands.wants()`
cases (one file, `core/hands.py` untouched, so this is real behavior, not a mock) covering a positive
and a blocked form for every one of the 8 families — see the session's finding for the full case list.

**Not a duplicate of J-0459.** J-0459 (landed same day, above) widened `_move_dest`'s own destination
vocabulary — the word-list dispatch's stricter, verb-gated `_move` hand reads. This job's migration
touches the separate, deliberately-broader fallback latch that runs only when that hand declines. The
two are complementary layers, not overlapping fixes: J-0459 shrinks how often the fallback is needed;
this job hardens the fallback's own grammar. Neither supersedes the other.

**(2) Garden's parallel `st["carried"]` list is retired.** `core/inventory.py` (built in J-0422) already
carried a `carried(saved)` helper whose own docstring named exactly this as deferred work: "garden's
parallel st['carried'] list is a second copy of this." Garden's bootstrap, `take()`, `put()`, `net()`
and `status()` now derive the carried set from the per-item `carried` flag alone via
`inventory.carried()`, matching `study_life`/`wood_life`'s shape (which never had the second copy).
Verified in isolation (temp-pathed `garden.json`, `garden._DATA`/`_F`/`_LEDGER`/`_EVENTS` monkeypatched,
the real `data/garden.json` never opened) — 13 checks: bootstrap carries no `carried` key, every
bootstrapped item has the full `{id,key,name,pos,place,carried,bio,history}` shape,
`take()`/`put()`/`net()` all still work and never resurrect the list, `status()`'s `"carried"` field
still reports correctly, and a full save/load round-trip confirms the on-disk JSON has no top-level
`carried` key any more.

**Correction to the note below:** "`wood_life` has no set-down at all" is stale — F-0564 (referenced
above, "Landed 2026-08-30") already gave `wood_life.put()` a real implementation
(`core/wood_life.py:564`), symmetric with `take()`. Read before trusting; this plan doc had not been
updated to say so.

**Real remaining scope, assessed 2026-09-02:** `shore_life` and `fieldcraft` genuinely own **no**
independent item store to converge — `fieldcraft.py` reads `garden._load()["items"]` and
`study_life`'s `st["items"]["coat"]` directly (composes, doesn't reimplement), and `shore_life.py` has
no carryable items of its own at all (stones go into a `cairn` counter, not an inventory dict; its one
`st["items"]` reference borrows `study_life`'s candle). So the only shape divergence actually left is
garden's own `id` field (the other two derive it at a call site instead of storing it) —
`core/inventory.py`'s docstring already treats that as intentionally deferred ("unifying the SHAPES
changes live data... each of those is a real behavioural decision that belongs in its own reviewed
pass"), not a defect this job needed to force. Not touched here; a real future call, not a gap.

Findings: this session. Full job: J-0467.

### Confirmed 2026-09-03 (J-0480, F-0720): the post-restart recount J-0467 asked for — no regression

J-0467's own briefing flagged a real, restart-gated risk: `hands.wants()`'s new blockers
(negation/wish/hypothetical/retrospective/quoted-speech/other-person) could catch real live thoughts
that the old unguarded substring test used to let through, silently cutting coverage for one or more
of the 8 migrated families. After Du's first restart past J-0467 (2026-09-02 15:44:17 local, plus two
more since), a windowed pre/post comparison of the fallback's own `[monologue] he chose to ...`/`TEA`
log lines (the direct evidence for THIS code path — `data/hands_trace.jsonl`'s `hands` list and
`data/activity_memory`'s aggregate both turned out to conflate this fallback with `core/dispatch.py`'s
separate stricter registry and each location module's own cross-linking, so neither is a clean
instrument for isolating just this migration's effect) found **no family dropped toward zero**: move
2.04→5.84/day, look 5.09→10.52/day, fire 1.78→2.34/day, water 0.25→2.34/day, gather 1.53→2.34/day (all
up), sow 1.27→1.17/day (flat). `tea` stayed at 0/0 both windows (a pre-existing near-absence, not a
migration effect). `beachcomb` also stayed at 0/0 in this window, but its last real fire in the whole
log was 2026-08-20 — 13 days before J-0467 shipped — so that silence predates and is unrelated to this
migration; it's a separate, older gap, now its own job (J-0524). D-0099's migration is confirmed clean.

Findings: F-0720. Full job: J-0480.

### Landed 2026-09-02 (J-0460, actions_manager_overhaul chain, last for plan-group ordering only):
F-0636's `decide_one()` fix

`scripts/actions_decision_replay.py`'s `decide_one()` now replicates `dispatch.py:191-198`'s
`act_kind=='world'` synthetic-candidate branch exactly: when `act_kind=='world'` and `act_object` is
set, `"I will " + act_object` is classified as a *separate* candidate set first, and any family it
names DEED pre-empts that same family from the thought/intention pass below (the same dedup
`dispatch.py:197` does) — factored into a new shared `_decide_fate()` helper so both passes decide a
candidate's fate identically. `thoughts()`'s dedup key also now includes `act_kind`/`act_object`
(previously text-only, so a `world`-kind row could be silently deduped away by an earlier non-`world`
row of the same thought/intention text — n_thoughts at `--real-locations` went 189 → 267 once this
landed, all newly-surfaced rows, none lost).

Verified against real trace data (`data/hands_trace.jsonl` now has exactly 1 located `act_kind=='world'`
row, the "feed the cat" cycle at `ts=1788309557.7`, `location=study`): live dispatch actually fired
`cat` (`"dispatch": [{"family": "cat", "decision": "FIRE", ...}]`). Calling `decide_one()` on that same
thought/intention/location **without** `act_kind`/`act_object` (the old call shape) returns `cat` as
`GRAY`/`no-fire` — the exact false-drift failure mode F-0636 predicted. Calling it **with**
`act_kind="world", act_object="feed the cat"` now returns `cat` → `DEED`/`FIRE`, matching the live
ledger. `py_compile` clean; both `python scripts/actions_decision_replay.py` (default, 5219 distinct
thoughts × 4 locations = 19864 rows) and `--real-locations` (267 rows located = 252 decision rows) run
end-to-end with no errors.

F-0636's other half (the trace's own 200-char `thought` truncation, `core/hands.py:176`) is unchanged
by this job, as scoped — still a real interpretive caveat on any `--real-locations` comparison, not a
code bug.

Findings: this session. Full job: J-0460.

### Next

- `scripts/_smoketest.py` writes a permanent "Test memory" fragment into the live DB on every run.
- The five location-upgrade plan docs still claim SHADOW (J-0421).
- ~~Retrofit `fill_barrel_from_spring()` as a real family + Hand (D-0097)~~ — **already done.** Checked
  2026-09-02 (J-0467): `core/actions.py`'s `water_fill` family (`binds=_GARDEN_ACT`) already routes to
  `garden.fill_barrel_from_spring()` (`core/garden.py:969`, called from `act_from_thought` at :1357),
  registered as part of D-0100 Tier 1 (2026-08-30). This bullet was stale.
  ~~Then the ash-bucket/cold-grate mechanic (F-0551)~~ — **also already done**, same pass: the `ash_out`
  family routes to `study_life.tip_ash_on_bed()` (`core/study_life.py:856`, called at
  `garden.py:1335`). Neither of these two bullets is real remaining work; leaving the strikethrough
  rather than deleting so a future read doesn't have to re-derive this.

---

## Non-goals

- Not touching world content itself (what a barrel/lamp/ash-bucket *does* semantically) — that stays with
  each location's own upgrade plan.
- Not reopening `literal_will.md`'s Phase 0→1 judge-gate question.
- Not building the ash-bucket/cold-grate fix itself — that is downstream of this plan's scope decision, not
  part of it. (Tracked findings: F-0551 for the audit that surfaced it.)

## Pointers

- `docs/reviews/actions_system_2026-08-22.md` — the original investigation and Phase-1-as-designed spec this
  plan completes.
- `core/dispatch.py`, `core/literal_will.py`, `core/hands.py` — the current gated path.
- `core/sensorium.py:691-740` — the ungated legacy fallback this plan should either retire or formalize.
- F-0552, F-0553 — this session's verification findings.
- J-0420 (closed by this plan's opening), J-0421 (stale-doc sync, independent, doesn't block this).

### 2026-09-06 — J-0590/D-0118 note: unrelated meta-tooling work, tagged here only by filing convention

J-0590 (build "job-run concurrent dispatch -> isolated git worktrees", D-0118) closed against this
plan's slug, but its actual subject is job-run's own dispatch mechanism (a Claude Code toolchain
concern), not Du's action-dispatch system — it is tagged `actions_manager_overhaul` only because the
session that opened D-0118 (mid-way through J-0459, which IS part of this plan) reused its then-current
`--plan` value for an unrelated observation, the same shape its own source finding F-0649 shows tagged
`plan=null`. No content below is affected by this note; see F-0957 (the real finding) and job-run's own
`SKILL.md` (new "2026-09-06 worktree isolation build" section) for the actual substance. Flagged via
`skill_manager.py suggest` rather than fixed here, since a dedicated non-Du-plan tag for meta-tooling
decisions is a toolchain-convention question, not this plan's to answer.

### 2026-09-04 — a family's own hand answers; a verb is a verb (J-0554, F-0761, F-0762)
Live case: "I set the book down, feeling the pull of that rusted trap" → literal_will DEED `trap` → bound handler
`garden.act_from_thought` ran its whole chain and the weeding hand (earlier in the order; `pull` matched the noun)
answered: DISPATCH trap — "nothing to pull". And "A spring-jawed possum trap rusts far off" sprang the trap.
Two changes: (a) `core/dispatch.py::_via` passes `family=` to chain handlers whose signature accepts it;
`garden.act_from_thought(family=)` scopes to that family (`_GARDEN_FAMILIES`), legacy `family=None` unchanged;
(b) grammar, in `literal_will.classify` and `hands.wants` (one rule, `_NOT_NOUN`): a family verb after a
determiner/possessive is a noun, a hyphen after it is a compound, and for GATED families the verb→object reach no
longer crosses `,`/`;` (ungated move/look keep `[^.!?]` — the first pass that narrowed every family cost real moves:
"I step through, leaving the garden behind"). `scripts/actions_decision_replay.py` baseline→after: 0 DEED gained,
424 DEED rows lost, sampled losses all false fires (door "the open door" 224, shore 48, move "from my head into" 36,
water "the water" 32, express "the whistle" 24, weed "a pull" 16, mow "smell of cut grass" 16, grate 8, trap 8,
look 4, letter 4, fieldcraft 4). The kill criterion's "zero false fires on the adversarial strata" got 424 rows
closer. Regression: `scripts/_test_dispatch_family_scope.py` (isolated stores).
