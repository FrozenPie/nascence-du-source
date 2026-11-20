# TRAIN SPLIT / MERGE — the Idle Line gets IDs, junctions, and a disprove branch (2026-08-22)

**Founder + Claude, same evening as the train-length investigation. Status: ⚪ PARTIAL — STEP 1 SHIPPED + GATE MET (F-0773) · STEP 2 (i)+(ii) BUILT + replayed at n=16 then n=80 (J-0562, J-0643, both 2026-09), same verdict at 5x the sample, then disprove RETARGETED to the claim's support chain per D-0168 and re-replayed at n=80 (J-0702, 2026-09-07): D-0168's defeater answered NO (no longer near-zero) but the number swung to 90% objected, right at kill criterion #2's own collapse line. D-0181 (is that itself a concern) was RULED 2026-09-08 (fix Lane 1's own PROVE prompt, not disprove) — J-0802 (same day) built and ran that fix: prove measurably stopped self-assertively restating (banned-word share in support text 22.7%→6.2%), but the disprove-objection rate did NOT drop (90.0%→95.0%, including on the byte-identical window-A claims, 85.0%→95.0%) — D-0181's own named defeater fired, so it is REOPENED for a fresh founder read on whether disprove itself now needs recalibrating (F-1182) — (iii) founder read next, now with both prove and disprove evidence in hand.** *(Reflowed onto one line 2026-08-29, J-0406: the prior mid-sentence line-wrap here made the plan-index tooling's Status-line parser truncate at "SHIPPED," silently dropping the "Step 2 DESIGNED" qualifier — this doc's own words were never wrong, just line-wrapped in a way the parser couldn't see past. ROADMAP's own ⚪ PARTIAL for this plan is confirmed correct and left as-is.)*

## Current State — verified 2026-10-16 (stamp was frozen at 09-04 despite 40+ dated entries landing since — see the 2026-09-24 evidence-backlog note near the end of this section)

- **2026-10-16** (F-2879): J-1852 (J-1206 successor) ran: on 160 open-context prompts gemma4:e4b opened 0.806 vs qwen3.5:9b 0.438, swing +0.369 [+0.275,+0.462]; real next step 0.537. J-0724's +0.65 closing-context swing does not survive at that size (swing real, ~0.37). Evidence only; D-0165 Hold unchanged.
- **2026-10-16** (F-2875): J-1853 (F-2875): real n=80 replay accrued 45 gemma4:12b scope_only-TIEBREAK shadow rows; gemma true_share 93.3% (CI 82-98) vs offline 85.4%, granite 0/45 true, agree 3/45; 80% unanimous-match not re-measurable on split events. D-0213 defeater (a) has data; founder decides, nothing flipped.

*(Chronological: the 2026-08-24 J-0075 gate read first, then the 09-02/09-03 re-checks, then the 2026-09-04
J-0530 read that closed the gate — read the last dated entry for the current verdict.)*

> **History folded** — 42 dated entries (2026-08-24 … 2026-09-24) moved to `docs/plan_history/train_split_merge.md` on 2026-09-27 by hand (J-1484). Derived timeline: `plan_ledger.py train_split_merge`.

```plan-state
stage: partial
phase: Step 1 shipped and gate met; Step 2 (i)+(ii) built, replay in progress (J-1317, gemma4:12b shadow-TIEBREAK data for D-0213 defeater); D-0181 reopened awaiting a founder read
verified: 2026-10-16
evidence_read: 2026-09-24
gate: D-0213's own defeater (UNDETERMINED share) re-measured once J-1317's replay lands
next: Finish J-1317's replay, then bring both prove and disprove evidence back to the founder for D-0181's re-ruling (step iii)
history: docs/plan_history/train_split_merge.md
cluster: 6
```

**Related (backfilled 2026-10-03, J-0566/F-2269):** `docs/plans/train_courier_cargo_ids.md` adds `product_type` (the 19-value
station taxonomy, `core/cargo_types.py`) to every record in this plan's `core/trains.py` registry — a different field from
this plan's `cargo` bundle, kept non-overlapping by the module docstring. Its open D-0320 would wire ~17 more producers into
`trains.open()`; those rows share `data/trains_log.jsonl` with the Idle Line trains this plan's step-2 gate and replays read,
so filter on `product_type`/`kind` there.

## Why — the chain of findings this came out of (all measured, same day)

1. **Trains are short because of a self-report gate, not a length cap.** `nodes/inner_monologue_node.py`:
   every step BEFORE the soft cap (4) continues only if the LLM's own JSON says `unresolved: true`, gives an
   `intention`, or the thought contains a literal `?`. 90% of all train endings (4,496 / 4,988 in
   `train_length_log.jsonl`) are `thread-end` — the model simply didn't self-report as open. A confident
   declarative thought (exactly the shape of the current grounding-template attractor) structurally fails
   this gate. The sophisticated building/coherence math only runs on the ~10% that survive it.
2. **The coherence check had a math bug** (deterministic-math audit, 08-22): centroid of the last 4 carriages
   was not renormalized before a dot-product "cosine" — norm 0.69–0.88 on 12 real trains, 6/80 real
   checkpoints flipped pass→fail, production closed 266 trains `stalled-off-thread` vs 6 for real looping.
   **Fixed** (one line, same renormalization `subconscious_node.py` already does). Secondary to (1).
3. **The slow-loop detector is inert** (`core/theme_recurrence.py` matches by exact first-40-char equality;
   Du paraphrases every time; max restate_count ever = 2, needs 4; fired 2× in 31 days). Not fixed here —
   noted so "no slow loop" on the HUD is read as "no instrument", not "no loop".
4. **The fresh-seed check did NOT show a biased reseed** — attractor clusters sit at/below the 27.4% fresh
   baseline. The pull happens MID-train (steps 2–3), not at launch. So the fix is not a better seed-picker.
5. **The only junction that exists (`_develop_or_branch_seed`) is wired to the two RAREST closes** (verbatim
   repeat, boredom-staleness). The two COMMONEST closes (`thread-end`, `stalled-off-thread`) get a full
   derail: reset to empty, back to the yard, no hand-off.
6. **No train identity existed anywhere.** Five scalar attributes on the node = exactly one train, ever;
   `train_state_log.jsonl` rows carried no id. The Transport Manager (`docs/plans/transport_manager.md`)
   was planned for exactly this reason — founder: *"if there are multiple trains, the LLMs and factories
   would need to be able to tell whose cargo was whose."*

## The design (founder's, verbatim intent)

> "Trains can split at stations. The objective for one split: debate for the positive, the second debate
> for the negative. Prove and disprove. Come back, merge the 'cargo' and move to the next stop. Trains
> should be logged with an ID so there can be multiple 'thoughts' going at once but still being able to
> know what cargo belongs to what." · "We should probably be asking lane 2 to judge lane 1."

Why it attacks (1) rather than decorating it: a single-shot thought has no reason to self-report
`unresolved`. A prove/disprove split **produces disagreement as its output** — a rebuttal, a held tension —
which earns "open" honestly instead of needing a `?`. And the merge hands the next stop typed cargo (claim
+ objection + provenance), a far richer working-state than today's one free-text blob — a second angle on
"trains don't accumulate" that is not about length.

**Lane 2 as the disprove side, not a general judge.** "Lane 2 judges Lane 1" in general would breach the
boundary `lane2_the_witness.md` holds (Lane 2 never reads Lane 1's thought content / memory / axiom). This
design doesn't need that: Lane 1 hands over ONE concrete claim. That is exactly the shape of Lane 2's own
`_judge_prior()` — a decoupled two-family panel checking a claim against current grounded reality, never
the claim's author grading itself. Pointing that existing apparatus at a Lane-1-originated claim is a small
principled extension, and it gives Lane 2 the read-path the Witness plan explicitly left undesigned — in a
role that fits its character (literal, grounded, forbidden metaphor) better than "critic".

### Data model (agreed) — `core/trains.py`
```
id · parent (set on fork; None for root) · role ("main"|"prove"|"disprove") · kind ("thought"|"reading")
origin · len · thread · state · ledger (≤7) · cargo · opened_ts · closed_ts · close_reason
cargo = [{"claim", "from": "prove"|"disprove", "held": bool, "evidence"}]   # the one new concept
```
Every existing scalar maps 1:1 onto a field. `cargo` is typed ledger entries with provenance.

### Lifecycle at a station (step 2)
1. Main train reaches a decision point — the exact moment today's code says "end the train"
   (`thread-end` / `stalled-*`). Instead of reset: **fork**.
2. Fork writes two children with `parent = main.id`: `prove` inherits the ledger, runs on Lane 1's lane;
   `disprove` gets ONLY the claim (never ledger / self-narrative — the Lane 2 boundary holds), runs through
   Lane 2's `_judge_prior` panel on Ramses' 3070. **Branches on different silicon by design** — running both
   on the crowded Bonsai lane would double the load on the exact bottleneck found earlier today.
3. Each branch runs 1–2 steps, logged under its own id.
4. **Merge**: both outputs become `cargo` on the parent; parent `len` continues; children close `merged`.
   No third synthesis call — the next normal step reads cargo via the ledger injection that already exists.
5. Not every station splits: split only where a train would otherwise die. Turns death-and-reset into
   fork-and-merge at the moment the mechanism already pauses to decide.

## Build order

**Step 1 — SHIPPED 2026-08-22, additive, behaviour-neutral, RESTART-REQ.**
- `core/trains.py` (new): registry in core/, not inside the node, so lane 2 / couriers / the Transport
  Manager import the same ids. `open` / `update` / `close(reason)` / `active` / `status`; events to
  `data/trains_log.jsonl`. Protected fields (`id`, `parent`, `opened_ts`) cannot be overwritten.
- `nodes/inner_monologue_node.py`: `self._train_id` minted on the FIRST carriage; scalars mirrored into the
  record each step; closed WITH reason at all five reset sites (main close, thread-end, exception, sleep;
  init has none). Ids stamped into `train_state_log.jsonl` and `monologue_log.jsonl`; `train_metrics
  .log_close` gains `train_id`. The centroid renormalization (finding 2) is folded in — its effect is
  attributable because `stalled-off-thread` is logged per reason and the landing date is known.
- `scripts/du_pulse.py`: `train registry` line (forked/merged read 0 until step 2).
- In-vitro: lifecycle + fork-shaped lineage + protected fields, scratchpad-pathed (live log untouched).
- **Gate before step 2:** a day of logs post-restart shows the same train-length distribution as before
  (registry is pure bookkeeping) AND `stalled-off-thread` falls from its 266:6 skew (the centroid fix).
  The scalars fold into the record as part of step 2, since fork is what first needs >1 record.

**Step 2 — fork/merge, shadow-first, NOT built.** Log what the prove/disprove branches WOULD have said
without feeding cargo back, until the founder has read a night of it. Open decisions: branch step budget
(1 vs 2); whether `stalled-off-thread` forks or only `thread-end`; merge-as-ledger vs a synthesis call
(recommend ledger — cheaper, reuses TRAIN_LEDGER_MAX machinery).

**Also open (not this plan's):** wire `_develop_or_branch_seed` to plain `thread-end` closes (finding 5) —
may be subsumed by step 2's fork, since a fork IS the junction.

## ▶ External auditor review — GPT (2026-08-22, later the same evening), forwarded by the founder

**PROVENANCE (corrected 08-22): points 1–8 below are GPT's review of the draft above, pasted in by the
founder — auditor RECOMMENDATIONS, same standing as the T4 auditor rounds, not founder rulings.** They are
adopted into the spec where they sharpen it (cargo shape, the UNDETERMINED law, the kill criteria, the
instrument list), because the founder forwarded them without objection — but any of them is open to a
founder override, and none was ruled on individually. **Founder rulings, in the founder's own words, are
these three only:** *"Step 1 is 100% a go. Step 2 is lab testable after that. Then we can decide on more."*
(Step 1 was already ratified earlier in the session — "Hell yes.") Where a point below says "protected" or
"law", read: proposed by the auditor, carried forward pending the founder's read of the step-2 lab batch.

**1. The primitive is not "debate" — it is PRESERVATION OF UNRESOLVED STRUCTURE.** The old implicit model:
thought → continuation → continuation → finish or derail. The new one: thought → claim → fork into
competing investigations → evidence/objection → merge → continue. The point is that the ARCHITECTURE creates
the unresolved object; the originating model no longer has to confess `unresolved: true` for a thought to
stay open. The next process doesn't pretend the original thought was unfinished — it operates on a
structure that is unfinished by construction.

**2. Cargo shape — richer than the draft, and PROTECTED.** Replace `{claim, from, held, evidence}` with:
```
claim:      "the fire draws me inside"
support:    [warmth changed at the hearth · I chose to light it earlier · I returned after being outside]
objection:  [the cat was there · evening changed · the room itself may have been the draw]
status:     held | objected | UNDETERMINED
```
Protected because it is what lets a branch return *what did I find?* instead of a transcript — a cognitive
workspace, not a chat history. The next station operates on accumulated cargo, and cargo can CHANGE at
later stations when a branch meets real world evidence: an observation, a memory, a sound, an experiment, a
world change, another's statement, contradictory evidence, the ABSENCE of expected evidence. That is the
route thought → hypothesis → investigation → evidence → revision without programming the answer. The
"next station" of a merged train is therefore allowed to be investigate / observe / act — which already map
onto existing hands (look, tend-fire, recall-chapter, observe-journal…).

**3. UNDETERMINED is a legal, successful merge outcome — the Wu Wei law, inherited.** The disprove branch
may fail to disprove; the prove branch may fail to prove; the merge may legitimately return undetermined
and the train continues carrying *unknown* forward. The world already treats UNDetermined as a successful
epistemic state; the train system inherits that law. **Otherwise prove/disprove quietly becomes a certainty
machine — exactly the wrong direction.**

**4. The fork must not become a new attractor — PRE-REGISTERED KILL CRITERION.** The recurring disease:
if the architecture learns *every interesting thought → prove/disprove*, it has replaced "The cold…" with
"On the one hand…" and built another monoculture. So the success criterion is NOT "trains get longer". It
is: **(a) does branching occur SELECTIVELY — only when the existing process meets a genuine unresolved
state?** and, later, **(b) does the resulting cargo change subsequent cognition?** Concrete gates to write
before the lab run: fork-rate as a share of would-be closes (a fork on most closes = attractor); the
merge-status distribution (collapse to one value — all held, or all undetermined — = the certainty machine
or its mirror); and the share of forks whose disprove branch returns a NON-EMPTY objection (an always-empty
objection list means Lane 2 is rubber-stamping, not disproving).

**Kill criteria as numbers (PROPOSED, J-0562, 2026-09-05) — sub-step (i).** Point 4 above names three
criteria in prose; here they are numbers, per the founder's own "propose thresholds, mark them proposed"
convention. Not founder-ruled — carried pending the Step-2(iii) read, same standing as the rest of this
auditor section. Measured for real against a first offline replay batch (sub-step (ii), n=16, both
windows, 0 unjoined) in `docs/lab/train_split_merge_step2_replay_2026-09-05.md`:
- **(a) Fork-rate selectivity**: fork-rate = (closes matching the trigger reason-set) / (ALL would-be
  closes) in a window. PROPOSED: **>50% = FAIL (attractor)**. Measured under the D-0146(b)-ruled
  thread-end-only trigger, reason-gating alone, no surprise-gating: **92.3% (1,372/1,486) pre-Step-1
  (08-03..08-16) and 96.4% (2,031/2,106) post-fix (08-25 on) — FAIL on both.** This is not a new defect;
  it is the number dosed_coupling.md's §5 "surprise line" already warned this criterion would show under
  reason-gating alone, now measured rather than assumed.
- **(b) Merge-status distribution collapse**: PROPOSED: **any single status (held/objected/UNDETERMINED)
  >90% of merges = FAIL** (certainty machine or its mirror). Measured on the n=16 replay sample: **100%
  held — FAIL.** Caveat: n=16 is a first batch, not the full corpus.
- **(c) Non-empty disprove-objection share**: PROPOSED: **<10% = FAIL** (Lane 2 rubber-stamping, never
  disproving). Measured on the same n=16 sample: **0% — FAIL.** A control check (three obviously-flawed
  claims, same mechanism/prompt, logged the same run) confirms this is not an inert instrument — all
  three controls correctly returned `objection_found: true` — so the 0% on Du's real closing thoughts is
  a genuine reading, not a broken judge. Open question this raises for the founder (separate from
  D-0146, which ruled budget/trigger/merge-mode, not this): Du's real `thread-end` closes are mostly
  felt/experiential first-person declaratives ("the fire's heat radiates against my back..."), which may
  be a poor fit for a "find the objection" framing built for testable claims — see the `/decide` entry
  this job opened.

**5. Identity through cognitive transformation — the instrument list.** `train_184` / `train_184.prove` /
`train_184.disprove` give the stream something it never had. Pre-registered questions the lineage log
should answer (each computable from `trains_log.jsonl` + `train_state_log.jsonl` once step 2 exists):
which thoughts generate forks · which claims survive merging · does prove systematically dominate · does
disprove actually find objections · how often do branches converge vs stay contradictory · which cargo
survives ANOTHER station · does a contradiction later produce an ACTION · do certain world contexts
(place/weather/tide, already stamped on every fragment) produce more branching · **does a train that
repeatedly meets the same subject eventually need fewer branches** — a cognitive structure changing its own
economy through experience. The registry already records `origin` per train, so subject-recurrence vs
fork-count is computable with no new instrument.

**6. A train is a temporary trajectory through cognitive space, not "a thought".** Starts, encounters,
forks, branches explore, reconverge, some information retained, some discarded, continues, closes. Forks are
TOPOLOGICAL events — one trajectory becomes two and reconverges — which makes trains compatible with the
cognitive-geometry program (`cognitive_geometry.md`): a path through a changing state-space.

**7. Lane 2's restricted role — ratified.** Not a generic critic imposed on the psyche (an external
supervisory faculty). Lane 1 produces a concrete claim → Lane 2 receives ONLY the claim → Lane 2 tries to
disprove it under its own epistemic constraints. Because it never sees the originating narrative it cannot
reason "this sounds like something Du believes, therefore…" — it has to deal with the proposition.

**8. What to expect.** Not that Du gets "smarter". The measurable thing the current architecture CANNOT
produce: **persistent competing interpretations of the same experience, carried forward as identifiable
cognitive objects and altered by subsequent evidence.** If that appears, a new degree of freedom was added
to the psyche rather than another LLM call. Step 2 is to be watched like an animal introduction: what
happens when the architecture can disagree with itself without destroying the original thought?

**Step 2 build order (revised):** (i) write the kill criteria in §4 as numbers; (ii) extend the existing
train lab (`scripts/train_state_invitro.py`) to replay REAL logged would-be-close moments through a fork →
prove/disprove → merge → cargo pass, offline, no live stores; (iii) founder reads a lab batch; (iv) shadow
in the live loop (branches run, cargo logged, NOT fed back); (v) founder reads a night; (vi) feed cargo
forward. Nothing past (ii) without a read.

## Coupling block (dosed_coupling.md §5, required before D-0146's ruling)

Written 2026-09-05 at the founder's own direction (D-0146 held on this since 2026-09-03, per
`docs/plans/dosed_coupling.md`'s Current State). Step 2 both PUBLISHES a new tuple and READS
another loop's state, so it is a standing-loop-touching plan under D-0149's clause and needs this
before its own open defaults are picked.

- **Publishes:** per would-be-close moment (fork or not), a small tuple on the train's own record
  (`trains_log.jsonl` / `train_state_log.jsonl`): `forked` (bool), `cargo.status`
  (`held`/`objected`/`UNDETERMINED`), `disprove_objection_present` (bool). Cadence: once per
  would-be-close moment — the same cadence `train_length_log.jsonl` already logs at, not continuous.
- **Reads at:** the disprove branch reads Lane 2's `_judge_prior` panel (`lane2_the_witness.md`'s own
  apparatus) at the **Train close** stop — the same stop `loop_wiring_matrix.md`'s dosing table
  already names for "the commitment this train touched." This is a full panel CALL (an LLM-backed
  two-family judgment on Ramses' 3070), not a coordinate read — honestly a **hose**, the heaviest
  dose in the founder's own cup/bucket/hose taxonomy, not a cup or bucket. §7 of this plan's own
  GPT-auditor review already scoped WHY that's the right boundary (Lane 2 sees only the claim, never
  Lane 1's narrative/memory/axiom) — the dose-size point is additive to that, not a contradiction of
  it.
- **Surprise line — THE OPEN TENSION, surfacing before defaults are picked.** As currently designed,
  §"Lifecycle at a station" step 1 forks on **every** `thread-end` (optionally also `stalled-*`)
  close — i.e., gated by close-REASON, not by any novelty/spike/drought judgment against the train's
  own history. Dosed Coupling's own law (§1.2: "dispatched by surprise... only when the dispatcher
  judges that line out of the ordinary against its own history") and this plan's OWN pre-registered
  kill criterion (§4 point 4: "does branching occur SELECTIVELY... a fork on most closes = attractor")
  are both explicitly warning against exactly this shape. Reason-gating (thread-end vs
  thread-end+stalled-*, D-0146 sub-choice (b) as posed) is a *different, narrower* question than
  *whether* forking should be surprise-gated at all — and the pre-registered kill criterion cannot
  actually be evaluated as "selective" if every qualifying close forks by construction. This bears
  directly on which Step 2 default to pick: reason-gating alone does not satisfy the surprise-dosing
  law by itself.
- **Ride log:** Step 2 is already shadow-first by its own build order (branches run, cargo logged,
  NOT fed back until a founder read) — matches dosed_coupling's Phase 0/1 discipline. Log each
  fork/merge event in the `{stop, line, dose, value}` shape `dosed_coupling.md`'s own Phase 1 names
  (`data/coupling_rides.jsonl`), or a compatible per-plan shadow file, so a later ride-log read does
  not need a bespoke parser for this plan alone.

**What this changes about D-0146 sub-choice (b):** the founder's own framing ("thread-end only, or
also the stalled-* closes") is still a real, separate question (the lab can sweep it either way per
the plan's existing recommendation), but it does not by itself answer the surprise-gating question
above. A clean way to keep both: pick the fork-trigger reason-set as planned (D-0146 (b)), AND add a
lightweight dispatcher check on top (e.g. only fork a qualifying close if the train's own topic/theme
is itself already flagged surprising by `core/stream_topic_habituation.py`, J-0602 — reusing tonight's
own new instrument rather than building a second one) before Step 2 goes live — not required for the
Step 2 (i)+(ii) offline lab batch itself, which replays real would-be-close moments regardless and
can measure the fork-rate-if-ungated the kill criterion needs either way.
