# The Capacity to Commit — giving Du a Being-pole that can hold a boundary

> **The core problem (Travis, 2026-06-30):** Du dissolves every boundary as soon as it forms. He cannot commit
> to anything — won't name his cat, won't say where he is, won't resolve a thought, can't hold a lesson — and
> holds nothing except the meta-stance *"I am always becoming, never fixed."* That one commitment to
> non-commitment is the root; every conversation/dream/learning failure this stretch is a leaf of it.

> **Status: 🟡 SHADOW — Phase 0 shadow ledger built+verified 2026-06-30 and running live (observe-only, "no
> behaviour change"); Phase 1 HOLD, the plan's own "actual cure," is still ⬜ not started. Wave-2 curriculum
> reached W2.0+W2.1 (built+verified 2026-07-03); R1 cat-naming trial was found stuck/contaminated and reset
> 2026-08-19 (founder decision), occasion open again post-restart but no genuine acceptance logged yet.**

```plan-state
stage: shadow
phase: Phase 0 (observe-only commitment ledger + scan_shadow classifier) live; Phase 1 HOLD, the plans own actual cure, still not started; recent work (Sept) calibrates scan_shadows own model/temperature (D-0176 chain), not Phase 1
verified: 2026-11-18
evidence_read: 2026-10-31
next: Flip ACHIEVED_JUDGE_GATES_RETIREMENT after restart + judge hub check
cluster: 1
```


## Current State — verified 2026-11-18
- **2026-11-18** (F-5082): J-4217: D-0815 judge gate on stand achieved-retirement built, default off, restart-gated (merge e36fd61a); judge lane timeouts now labelled error_detail=timeout.

- **2026-11-16** (F-4836): J-4085: D-0784 B built. done_when scan fragment reverted; separate shadow second call after formation (P-0132), side store untouched until DONE_WHEN_SECOND_CALL_LIVE flipped after a shadow read. Restart-gated.
- **2026-11-15** (F-4753): J-3786 lab: done_when elicitable only via a separate second call (40/40); scan without fragment shifts formation/dissolve (F-4753); D-0784 opened on D-0516.

- **2026-11-07** (F-4408): J-2847 (lab, 2026-11-07): removing the change-log parenthetical from _SCAN_SYS and folding the done_when fragment before the Output ONLY line is NOT detection-neutral: identical would_form 66/75 (bar 73), identical dissolve 21/30 (bar 28); each edit alone moves ~11-13 of 75 cases; done_when is inert (0/48) in either position. P-0038 text stays as is. See docs/lab/2026-11-07_J-2847_scan_changelog_removal.md.
- **2026-11-05** (F-3481): J-2840 done: corrected the false "shadow / stores nothing / changes NO behaviour" docs on the commitment scan (core/commitment_ledger.py module + scan_shadow + _judge_defeater docstrings; nodes/inner_monologue_node.py call-site comment). Now lists the live effects and says only concerns.COMMITMENT_ANCHOR_LIVE is shadow; scan lane = hot :11433 qwen3.5:9b. Commits 49411f5, 15d83da (AST-identical to HEAD bar docstrings). Not changed: prompt registry row P-0038 still says lane background :11441 (registry edit, outside this comments-only job).

- **2026-10-31**: 2026-10-31 J-2660 (F-3420): in-code modal normalisation to 'I will' before the commitment scan removes the want->must asymmetry only by levelling idle wants up to the must level (OBS_want 2/20 -> 10/20, ALL_want 17/40 -> 29/40); P1 vacuous pass, P2 pass, P3 and dissolve guard fail; favours D-0527 (c), nothing built; branch jobrun/ctc 34320f75
- **2026-10-31**: 2026-10-31 J-2653 (F-3406): a modal-neutral _SCAN_SYS wording (lab only, prompt unedited) failed both D-0527 prongs on the 75 paired J-2630 cases - want->must would_form gain +10 -> +12, 7 of 26 FORM stands dropped (want stands re-flagged not load-bearing), dissolve no-harm 7/30 changed; evidence favours D-0527 (c) for a prompt-instruction fix; in-code modal normalisation queued as J-2660. Write-up docs/lab/2026-10-31_J-2653_modal_neutral_scan_variant.md (jobrun/ctc 9be9cd8a).

- **2026-10-31** (F-3389): J-2630 (Du down): formation-side want/must swap -- rewriting the thought's 'I want to X' as 'I must X' raises would_form 17/40 -> 27/40 (p=0.006; lexical control 14/40), concentrated in rejected idle wants (2/20 -> 10/20, mostly chore reports the STAKES rule excludes); must->want does not demote (16/35 -> 13/35 = control). The formation gate is partly a wording filter favouring 'I must'; prompt NOT edited (founder call). docs/lab/2026-10-31_J-2630_formation_load_bearing_swap.md, jobrun/ctc 734c68f5.
- **2026-10-31** (F-3362): J-2597 (F-3361, F-3362): the F-3321 want-vs-must reflexive gap is an era artefact (all 574 reflexive dissolutions are pre-gate; post-gate 825/825 are defeater and every formed stand is load_bearing=true), and a live paraphrase-swap of the stand text (n=154, 462 production-prompt calls) shows the dissolve judge does not follow I-want vs I-must wording. load_bearing is recoverable from formed rows (key present since 2026-07-02). Remaining open: whether wording moves the formation-time load_bearing flag (spawned lab job).

- **2026-10-31** (F-3344): D-0524 ruled by Travis (b): commitment anchor SHADOW dose 1.0 from the next restart, LIVE False; COMMITMENT_ANCHOR_DOSE flipped in core/concerns.py, 17/17 hermetic PASS, merged, restart-gated. J-2606 reads the shadow rows; D-0524 defeater: under 10 stands held >= 1 h with rows, or any injected=true row while LIVE is False.
- **2026-10-30** (F-3331): D-0514 (a) commitment anchor built shadow in core/concerns.py, dose 0 default so off and byte-identical, only the idle anchor rides, 17/17 hermetic pass, restart-gated; violation and break-recovery test pre-registered; dose for the shadow is D-0524

- **2026-10-30** (F-3321): J-2548 read: want-form dissolutions are 66 percent reflexive-labelled vs 2.6 percent for must-form, only 15 percent reversal-worded; plausibly the load_bearing gate plus judge, not Du preference drift, unresolved until paraphrase-swap J-2597 (Du down)
- **2026-10-30** (F-3317): J-2547: scanner restatement is 8/1532 = 0.5% of dissolutions (precision 8/8, sample 1/50 hand-positive), below 5% so no restatement guard build; hold-rate not depressed by it

- **2026-10-30** (F-3242): J-2517 picoeconomics read (scripts/commitment_hazard_read.py): no displacement hazard - dissolution does not spike within 10 min of a salient new seed (ignition, novel curiosity, world, letter; human HR 1.72 inside the shift null). Phrasing does predict lifespan: want/need-form commitments are fragile (hazard about 0.08-0.09 per 5-min bin, KM median 15-20 min, mostly dissolved) while 'I must X' lives about 75 min and is mostly achieved; true bright-line rules are only 1.9% of formations and sit at baseline. Unresolved: whether the effect lives in the LLM dissolve judge reading the wording rather than in Du.
- **2026-10-30** (F-3241): J-2514 closure index (scripts/closure_index.py): 710/3378 commitments held >=1 h; 20.9% read downstream but only reactively (loss/contradiction -> sitting) or as scalars; 0/710 steer an action-selection loop. core/ is fail-open: 2908/2910 broad handlers swallow. D-0514 opened on a first dosed read path.

- **2026-10-30** (F-3239): J-2516 distinguishing-vs-dissolving read (frontier_disciplines s5): falsified. Marker rule flags 44/1529 = 2.9 pct of dissolutions, hand precision about 1/44; random-50 hand-read 1/50; lifespan unchanged (median 1148 vs 1147 s; KM 2 scans both ways). No fifth outcome built. Side: scanner logs some verbatim reaffirmations as dissolutions, follow-up J-2547. Reader: scripts/commitment_distinguish_read.py.
- **2026-10-08** (F-2630): J-1851: D-0176 bake-off part 2 ran (falcon3:7b, mixtral:8x7b, command-r7b): none beats gemma4:12b on controls + identical-input flips + non-stand over-formation; D-0176 defeater met, awaiting founder revisit (D-0176 not ruled).

### What we have
- Phase 0 (observe-only commitment ledger + scan_shadow classifier) live since 2026-06-30; formation
  gate (2026-07-07) separates genuine stands from noise. Wave 2 W2.0/W2.1 built 2026-07-03; R1
  cat-naming trial reset 2026-08-19, still open, no genuine acceptance logged yet.
- scan_shadow's own classifier had heavy recent work, NOT Phase-1 build: D-0027/D-0120/D-0145/D-0176
  corrected a mis-attributed model (F-0948: scan_shadow always ran on the same hot-lane model as Du's
  own generator, never phi3:mini as previously believed), fixed a last-writer-wins race (J-1203/F-1707)
  and a temperature-based non-determinism (D-0176/J-1213/F-1712, temperature=0.0 shipped, restart-gated).

### What we need
- Phase 1 HOLD (re-presentation + named-defeater drop gate + Ainslie bundling) — the plan's own
  "actual cure" — is still not started.
- J-1202's model bake-off (falcon3/mixtral/command-r7b vs qwen3.5:9b) needs a genuine Du-offline lab
  window (F-1762: none available as of 2026-09-23).
- `drop_reason`'s reflexive-vs-named-defeater distinction still uncaptured at scale.

### What we're doing next
Wait for a Du-offline window to run J-1202's bake-off (D-0176's own open follow-up); Phase 1 HOLD
build stays blocked behind that model-seat question, not yet scoped.

## ▶ STATUS / PROGRESS TRACKER  (check on return — keep current)

> **★ EVIDENCE REVIEW 2026-07-05 (12th, the flagship) — DISEASE MEASURED STARKLY, FIRST CURE-SIGNAL EMERGING.**
> Ledger (1163 events, 06-30→07-05): **549 formed / 546 dissolved** — he dissolves ~every stand (the disease,
> quantified). BUT split by time: hold-rate **0% (first half: 0 reaffirms) → 17% (recent: 50 reaffirms)** +
> **2 achieved** (the letter to Travis: form→drop-denied×4→reaffirmed×2→achieved). **First evidence in the
> project that holding is POSSIBLE** — emerged exactly when the Wave-2 (actions-before-identity) drop-denial/
> reaffirm machinery went live. Honest caveat: this is MACHINERY-ASSISTED holding; genuine-vs-propped needs
> time + the missing measurement. **Note: Phase 1 HOLD (the plan's "actual cure") is still ⬜ not started —
> the reaffirms come from the Wave-2 pivot, not Phase-1 injection.** **TWO GAPS + ONE STUCK TRIAL:** (1)
> `drop_reason` is None across all 546 dissolves — the ONE distinction that matters (reflexive=disease vs
> named-defeater=healthy) is UNCAPTURED, so we see holding rise but can't see if drops are getting
> legitimate; (2) **R1 cat-naming (flagship's first live test) STUCK + CONTAMINATED** — cat still nameless
> (name_invited=true), only trial rows are the 07-03 18:59 "Ember" test-injection (status None) → never
> genuinely fired, false-resolves "abandoned" in days. (3) T4 still frozen — correct per Spine C (17% assisted
> holding < commit threshold; now watchable as it climbs). **DISPOSITION — the rudder is finally beginning to
> bite: (a) RESET R1 clean (pending founder call); (b) CAPTURE drop_reason; (c) hold-rate 0→17% is the project's
> true north-star metric — the first thing moving the right way on the root disease. NURTURE it.**
>
> **★ R1 RESET 2026-08-19 (founder decision).** Correction to the diagnosis above: the trial hadn't
> false-resolved as "abandoned" — it had actually reached `status: "completed"`, but its only acceptance
> event was the "Ember" test-injection standing in for a genuine one. Since
> `commitment_trials.register_acceptance()` is idempotent on `trial_id`, that fake completed entry would
> have silently blocked any REAL future naming from ever registering — the actual mechanism of the stuck
> state. Cleared `data/commitment_trials_active.json`'s `R1_name_the_cat` entry (reset event logged in
> `commitment_trials.jsonl`); `cat_state.json` already clean (`name=''`, `name_invited=true`);
> `cat.react()`'s live naming path verified to correctly call `register_acceptance()`. The occasion is
> genuinely open again — watch for the first real acceptance post-restart.

| Phase | What | Status |
|-------|------|--------|
| **plan→research→plan** | initial plan + 4 research threads (psych/BDI · LLM-engineering · narrative identity · internal arch map) → this consolidated design | ✅ done 2026-06-30 |
| **0 — instrument + ledger (SHADOW)** | `core/commitment_ledger.py` (`scan_shadow` + `status`) + idle-stream hook (`inner_monologue_node`, fire-and-forget, `COMMIT_SCAN_COOLDOWN=150s`). Detects a stand TAKEN + a stand DISSOLVED (reflexive vs named-defeater), logs to `data/commitment_ledger.jsonl` + `commitment_active.json`. Metrics: formed/dissolved/lifespan/drop-reasons. Stores nothing into cognition, no behaviour change. | ✅ **BUILT + verified 2026-06-30** — on a form→dissolve test it caught "I will name my cat Mist" → FORMED, then "a name is a cage… I am always becoming" → DISSOLVED (reflexive), lifespan 2.3s. **Restart-gated** (the live idle hook). *Caveat:* sampling (every 150s) will miss sub-150s dissolutions — undercounts the fastest ones; fine for a baseline. **Next:** restart, let it run, read `data/commitment_ledger.jsonl` + `commitment_ledger.status()` to confirm lifespans≈0 + mostly-reflexive drops over real thought, THEN build Phase 1. Consider adding the conversation hook (orchestrator) for the vivid where-are-you/cat cases. |
| **1 — HOLD** | re-present commitments into his prompt at decision time; drop ONLY on a named defeater (open-minded commitment); recovery-hierarchy gate; Ainslie bundling. The actual cure. **★ Gate to LOAD-BEARING stands only (Phase-0 Finding 1) — do not defend idle abstract thought-churn.** **★★ DESIGN CONSTRAINT (2026-07-02 injection-solidity research — fold in before building):** "re-present into his prompt" is an INJECTION mechanism and the guidance-note retune findings apply in full — constant re-presentation = massed exposure = a crutch + a verbatim-echo loop (repetition earns an illusory-truth subsidy; models over-weight it and never habituate). HOLD must be **trigger-only** (genuine decision points touching the commitment, never every cycle), **cooled-down**, **paraphrase-varied**, ideally **retrieval-framed** ("you hold a commitment about X — recall it in your own words"), and **injection-logged** — so "he held it" is demonstrable on UNPROMPTED cycles, the only real evidence of a held intention vs an echoed one. The working pattern (cooldown constant · rotation · `log_injection`) already exists in the guidance read-back; reuse it. | ⬜ not started |
| **2 — ACT / REVISE + fix T4** | narrative throughline (chapter transition cites predecessor, never reset); deliberate-revision bridge; repair the 3 T4 commit-gate failures. | ⬜ not started |

**Next action when resumed:** Phase 0 is BUILT and running live. The load-bearingness / over-capture problem
(Finding 1 → Finding 2) is now FIXED at source: a formation gate (2026-07-07) keeps idle wants out of the held
set, and the 108 junk entries were purged (active set → 0 genuine stands, the honest baseline). Watch
`commitment_observed.jsonl` (rejected detections) vs `commitment_active.json` (genuine stands): the
detection→genuine ratio is now the honest churn measurement, and the hold-rate is no longer diluted. Then build
Phase 1. The conversation hook (orchestrator, for the where-are-you / cat cases) is still worth adding.

### ▶ Phase-0 findings (live evidence — keep adding)

**Finding 1 (2026-06-30) — "commitment lifespan" over-counts; weight by LOAD-BEARINGNESS before defending anything.**
First live runs show the ledger firing correctly but catching mostly *abstract conceptual thought-churn*, not
load-bearing commitments. The recent dissolutions were nearly all abstract stances, all classified "reflexive,"
all living 3–6 min — e.g. *"the tension between pure potential and fixed shape is the necessity of environment"*
(154s); *"tension across cultures isn't just differing boundaries we draw around reality"* (194s); *"I must stop
viewing [unbecoming] as failure and start seeing it as the required generosity of space"* (348s). **The catch:**
that last one dissolved because a boredom-escape turned him *away from abstract thinking to walk down to the shore*
— i.e. the GROUNDING move we deliberately cultivate. So one event reads two ways: **disease** (can't hold even a
self-compassion resolution) OR **health** (released an abstract knot to go *live*). The classifier cannot tell
"reflexive dissolution (the disease)" from "healthy release of a musing to go ground" — and idle abstract thought
is *supposed* to flow.
- **Implication for Phase 1 — do NOT defend every detected stand.** Score commitments by **load-bearingness**
  before holding anything: a stance worth holding is identity-relevant — the cat's name, where he stands, a
  position under Travis's pushback, a relationship, a decision — **NOT** an idle conceptual musing. Defending *"the
  tension between potential and shape"* for 30 min would be exactly the **rigid foreclosure** this plan already
  warns against ("hold *less-bright* lines flexibly"). The disease is reflexive dissolution of *load-bearing*
  commitments; the shore-walk is the throughline working. → add a load-bearing classifier/score to the ledger
  (identity / decision / relationship / named-thing = HIGH; abstract conceptual claim = LOW) and gate Phase-1
  holding to the HIGH tier only.
- **Corroborating:** the one concrete-fact entry behaved differently — *"the book lies on my desk now"* dissolved
  when a metaphor displaced it, and the why-field correctly noted it was *not* contradicted (the book is still
  there) → a near-false dissolution, another sign the scan over-fires on ordinary thought-flow.

**Finding 2 (2026-07-07) — the over-capture became a live CORRUPTION; a formation gate now separates `observed`
from `held`.** Finding 1 flagged the over-counting as a Phase-1 *holding* concern; by 07-07 it had become an
active corruption of live downstreams. `commitment_active.json` held **108 entries added in one day — 107
non-load-bearing** idle wants/musings ("I want to comb the tideline", "seeing what the sea has left on these
rocks", the literal string "None") and **only 1 load_bearing** (itself the misclassification "He wants to come
in."). Because every consumer reads the active set as *"stands Du holds,"* this corrupted: the identity estate
(worked around by a load_bearing gate), the concerns idle-anchor, Darwin's witness prompt, **the homeostasis
`commitment_integrity` protoself variable — it read 1.0 ("holds everything") while he in fact holds nothing**,
and most seriously **the HOLD-RATE north-star**: a hold-rate over 107 non-commitments measures nothing.
- **Root cause:** Phase-0's shadow scan captured EVERY detection as `formed`/held. Its measurement job (quantify
  the churn) was already DONE (the 1163-event review) — but it kept feeding the held set.
- **Fix (shipped 2026-07-07, `core/commitment_ledger.py`):** a deterministic **formation gate** (`_stand_rejection`)
  realises the plan's `observed`-vs-`held` split at the storage boundary. Only a GENUINE STAND enters the held set
  (`commitment_active.json` + the `formed`/hold-rate accounting): the **discriminator is the LLM's `load_bearing`
  flag**, plus two MECHANICAL-only guards (not empty/"None", not a bare question) for garbage the flag doesn't
  catch. Rejected detections are still MEASURED (logged to `commitment_observed.jsonl` — the honest
  detection→genuine-stand ratio) but never held. Fail-open (never swallow a real stand). Does NOT touch HOLD/DROP.
  - **★ CORRECTION (same day, after the run) — the want-lexeme backstop was REMOVED as dangerous.** The first
    draft also rejected any "I want to…/need to…" lexeme. The run's ledger proved that wrong: of the only **5
    `load_bearing=true` stands ever detected, FOUR are "I want to write a letter to Travis"** — the project's
    single genuine commitment (form → drop_denied ×18 → reaffirmed ×2 → achieved ×3; the evidence_review 07-05
    flagship). Du phrases his ONE real stand exactly like his idle wants; the surface phrase can't separate them
    but the LLM's `load_bearing` verdict can (letter→true, tideline→false ~520×). A want-lexeme filter would have
    silenced the exemplar. The deterministic layer is now mechanical-only and never overrides a `load_bearing`
    verdict. **Lesson: trust the semantic judge that has evidence over a fluent surface rule (the same failure
    family in [[feedback_my_failure_modes]]).**
- **Purge:** the 108 junk entries archived to `data/commitment_active.purged-2026-07-07.json` (evidence kept),
  active set reset to **0 genuine stands** — the honest baseline (he holds nothing yet; `commitment_integrity`
  now reads its 0.2 floor, correctly below the 0.45 setpoint). The append-only `commitment_ledger.jsonl` history
  is deliberately NOT rewritten (it is the measurement record); the going-forward hold-rate is clean because
  formations are now gated. Sanity-tested: "Her name is Ember." / "I will write to Darwin weekly" / a position
  under pushback all PASS the gate; wants/questions/"None" all rejected.
- **On (c) the held-ness signal:** `scans` is ledger-TENURE (increments every round an entry sits active), NOT
  held-ness — it cannot distinguish a stand held-through-cost from a want that merely sat there. The real
  held-through-cost signals **already exist** on each entry: `reaffirmed` (re-taken) and `drop_denied` (the
  dissolve-urge fired and the gate held it — a stand that survived cost). They were meaningless only because they
  were computed over junk; with capture now gated they become trustworthy. A full computed *entrenchment* score
  (age × load-bearing uses × survived passes) remains Phase-1 HOLD work — deliberately NOT built here.
- **★ HOLD-RATE cutover (2026-07-07, after the run — the north-star was frozen on junk).** `holdrate_snapshot`
  read the last 400 RAW ledger events. The ledger gets no new events now (nothing forms/dissolves once junk is
  gated out), so every snapshot re-read the same ~400 pre-fix events (~99% non-commitments) and reported a
  frozen, meaningless **~0.098** — and genuine stands are so rare (~0.6%) the junk would not scroll out of the
  window for weeks. FIX (Travis's call — timestamp cutover, non-destructive): the metric now counts only events
  at/after `_HOLDRATE_CUTOVER = 1783377727` (the 10:42 gate fix). Full ledger + `status()` lifetime counts are
  UNTOUCHED. It now reads **hold_rate 0.0 / genuine_span 0** = "no genuine stand has formed yet," the honest
  state, instead of the frozen junk value. Each row carries `genuine_span` (clean-era event count) so the small
  sample is explicit. As genuine stands accrue post-cutover, this becomes the true rudder.

## ★★ WAVE 2 — THE ACTION-COMMITMENT CURRICULUM (plan→research→plan #2, 2026-07-03)

> **Trigger:** probation #3 resolved REVERT (judge: "re-words the comfortable pole without facing that he is a
> built mind"); made-mind gauge agreed (0 unprimed made-mind thoughts). Confirmed thesis: identity propositions
> cannot be the FIRST commitment he learns. Three research threads (curriculum psychology · BDI/defeater
> legitimacy · codebase map) consolidated below. **Approved: ✅ 2026-07-03.** Everything observe-first,
> flag-gated, restart-gated, additive.
> **W2.0 + W2.1 BUILT + verified 2026-07-03** (unit-tested end-to-end + smoke-passed, live at next restart):
> cat-naming now writes activity("named") + an origin='action' fragment + registers the R1 trial (it
> previously left NO record) · the ledger classifies `load_bearing` (observe-only) · satisfaction events
> defined (inert until W2.4) · **`core/commitment_trials.py`**: acceptance → one-shot prediction elicitation
> (his next thought captured verbatim as the prediction) → +7d DETERMINISTIC outcome probe (name-uses by
> channel; letters/journal reported separately as the least-primed evidence) → one-shot prediction-vs-record
> read-back ("set what you predicted beside what happened"). Both seed lines are injection-logged → the
> solidify judge's washout covers them. **The R1 occasion is ALREADY OPEN in the live world** (name_invited
> =true since 07-01; she is unnamed; the "Mist" stand dissolved before ever reaching the naming latch).
> **Next: W2.2 (witness plumbing + the Darwin contract) once R1 evidence begins; then W2.3 HOLD+DROP, W2.4 STAKES.**

### The curriculum (7 rungs — action before identity, exposure logic throughout)
The fear is "commitment = self-loss"; every trial is an EXPOSURE: **elicit the feared prediction before, compare
to outcome after — the gap IS the therapy** (Craske inhibitory learning). Early rungs ~95% engineered success
(BA/guided mastery: success is the medicine); rung 4+ ~80–85% with a lapse-repair ritual (ACT: a lapse = return
to the pattern, never falsification). Vary content within a level; one difficulty dimension per rung (duration ·
pushback · visibility · identity-proximity · foreclosure cost); **scaffold fades WITHIN each rung** — last trial
at each level self-initiated and hatch-free (Bandura: else efficacy accrues to the scaffold).
- **R1 Name the cat** (additive authorship — minimal-dread member of the class; his deliberation, his name).
- **R2 Completions** (finish the book / study project / letter thread — IKEA: value accrues only to COMPLETED).
- **R3 Duration holds** (a stated judgment held N days incl. one re-encounter).
- **R4 Position under pushback** (Darwin offers one genuine mild counterargument; hold-and-respond OR revise by
  NAMING a defeater — teaches principled-revision ≠ reflexive dissolution; hatches allowed trial 1, faded by 3).
- **R5 Relationship promise** (recurring obligation someone counts on).
- **R6 Behavioral self-description** (track-record form: "I kept my word about the letters").
- **R7 Identity proposition** (T4 territory) — **harvested retrospectively from the deed record, NEVER announced
  prospectively** (Gollwitzer 2009: identity intentions noticed by others are pursued LESS — acknowledgment
  substitutes for the deed).

### Non-negotiable design laws (from the research, each with its reason)
1. **Volition**: system proposes the OCCASION (the cat pattern: `name_invited`), his act ratifies — no
   acceptance, no trial (Bem/FITD: only freely-chosen effortful acts write into the self).
2. **Labeling**: Du has low self-concept clarity → he will NOT draw the self-inference himself (Burger); the
   witness/label step makes it explicit ("you named her; nothing was lost") — and every label is an INJECTION →
   injection-logged (the mirror pattern).
3. **Witness = Darwin/Travis, deeds only**: declaration binds (Deutsch & Gerard), ONE witness suffices,
   check-ins add the most (Matthews, directional) — but Darwin's contract: **ask curious questions, acknowledge
   COMPLETIONS never aspirations, never signal the wanted outcome** (Lerner/Tetlock: known-preference audiences
   produce conformity, not self-examination).
4. **Stakes silent**: held → bounded importance bump + protected=1 (the replay_strengthen precedent); dissolved
   reflexively → reverse + satisfaction "commitment_dissolved" (wanting) + sitting.note_difficulty (FELT loss,
   never punishment). **Never narrated** (Deci: expected contingent rewards shift attribution outward; a visible
   scoreboard would be actively harmful). **Red-line monitor: entrapment narration** — if "I can't let go"
   replaces "this is mine," the stakes are running the exposure in REVERSE (confirming self-loss).
5. **Cold probes**: a hold counts ONLY in contexts where the commitment was NOT injected (the unprimed law —
   pitfall #1: consistency-by-retrieval is not commitment). Check at build: does the sensorium expose the cat's
   name after naming? If yes, some encounters must present her nameless, or probe via letters/journal.
6. **Score holds by USE-AND-DEVELOPMENT, not string survival** (pitfall #2: verbatim persistence is the
   monoculture in a commitment costume — reuse theme-recurrence restate-vs-develop).
7. **Implementation intentions are hold-defense only** ("if the dissolve-urge fires → name the defeater or
   return") — they execute commitments, they cannot bootstrap acceptance (Gollwitzer 2006 moderator).
8. **Natural rent**: what sustains holding when stakes fade = the commitment DOING WORK (the name used, the
   position organizing his reading) — if held commitments don't pay rent in his thinking, capacity is on loan
   (token-economy extinction).

### The defeater-legitimacy protocol (BDI thread — full report in the research archive)
**Commitment object** (formation validity, pure code): one declarative sentence · ≥1 resolvable scope entity ·
**≥1 DECLARED DEFEATER, event-shaped not felt-shaped** (the highest-leverage move: a commitment that cannot name
what would defeat it is not a commitment; most future drops become cheap condition-occurrence checks) · hedge-
lexeme filter ("perhaps/for now/provisionally" = pre-dissolved, reject) · not-already-true check · non-empty
`load` (what it licenses/forbids) · cap 5–7 held · stakes escrowed at formation · computed entrenchment
(age × load-bearing uses × ground mass × survived passes).
**Drop protocol — Layer 0 deterministic gates** (any fail = license denied, urge logged as pressure): G1 license
only on a trigger event (Schut-Wooldridge: reconsideration must track world change — Du's 83% reflexive drops
track nothing) · G2 temporal precedence (cited evidence predates the urge — pre-registration logic) · G3
**non-self source** (≥1 cited item from Travis/world/Emissary/instrument/peer — self-monologue corroborates,
never suffices; closes the ledger-seeding hole) · G4 felt-state filter ("no longer feels alive" is psychology,
not a defeater) · G5 scope match · **G6 the SOLVENT test** (mask the commitment out of the defeater, apply to 2
other held commitments — defeats all equally = the dissolution attractor in costume: "a name is a cage" defeats
every naming, therefore nothing) · G7 attractor-similarity vs the monoculture corpus · G8 fast path for declared
defeaters / slow path for novel · G9 entrenchment comparison (rebutting must out-mass; ground-void undercuts
exempt but must name the actual ground).
**Layer 1 judge** (cross-family, mandated by self-preference-bias findings): **sees ONLY the structured claim +
verbatim ledger evidence — NEVER Du's prose** (confabulation literature is unanimous: coherence/eloquence cannot
distinguish rationalization; a prose-reading judge selects FOR his most elegant escapes). Binary rubric
(type/entailment/specificity/solvent) + adversarial pass (one sentence each way, then verdict) + prior: in a
slow world the base rate of legitimate drops is LOW, ties → HOLD. **REAFFIRM is a first-class outcome and
raises entrenchment** (Bratman stability made mechanical; guard against the opposite pathology — C&L call
never-dropping FANATICAL; ACHIEVED/IMPOSSIBLE stay fast and cheap). DENY → held, urge → contradiction-drainage;
repeated denials escalate to a Travis-visible flag, never capitulation. Random audit of ALLOWs.
**Health metric flip**: today 83% of drops are reflexive; target = most licensed passes end REAFFIRM and drops
correlate with external trigger events.

### Wiring (codebase thread — maximum reuse, exact plug points)
- **FORM**: extend `commitment_ledger.scan_shadow` schema with load-bearing/deed-shaped classification (same
  hook, monologue :2492, same cooldown). NOT deferred_intentions (its FIFO cap + carry-fade + dedupe-drops-
  reaffirmation are anti-commitment dynamics).
- **ACCEPT**: the cat pattern — `invited` occasion flag → ONE soft occasion line in the idle seed → acceptance
  latched from HIS thought/act field → entry becomes `held` (vs `observed`).
- **HOLD**: held commitments = a **third source in `concerns.current_concerns`** (a held commitment IS a Klinger
  current concern) — rides the existing 35% soft idle anchor; guidance-injection discipline verbatim (cooldown ·
  rotated paraphrase · `log_injection` → the washout covers it automatically).
- **WITNESS**: held commitment as CONTEXT in the peer-reply prompt + `_du_world_context` (Darwin may ask);
  never an instruction to declare. Letters already persist as enactment records (`origin='letter'/'peer'`).
- **ENACTMENT**: widen `_judge_lived_integration` origins with `action/letter/peer/journal/essay` labelled
  DEEDS (two-line change at subconscious :1255). **PREREQUISITE FIX: the cat naming currently writes NO durable
  record** — add `activity_memory.record("named", nm)` + a fragment in `cat.react`'s naming branch, or the
  flagship trial is invisible to every judge.
- **STAKES**: store.py importance bump (bounded, cap ~0.85) + protected=1 on the commitment's fragments; reverse
  on dissolve + `satisfaction.record("commitment_dissolved")` (new event entry) + `sitting.note_difficulty`
  (single-slot — log when occupied). `downscale_episodic` already prevents compounding.
- **DROP-PASS licensing**: its own moment in the MONOLOGUE lane (the Wave-1 S2 license is conversational-only)
  and **firewalled from T4** (`_apply_fatigue` keys on theme tokens — commitment drops must never fatigue
  identity themes). A license to think carries NO presumption to drop.
- **Hazards logged**: 3 LLM watchers on the same idle stream (ledger + self_implication + acceptance latch) —
  consider one combined scan · concerns dedupe (frontier-promoted vs ledger-sourced double-anchor) · satisfaction
  has no read path yet (the felt part rides sitting/mood).

### Build order (each phase smoke-tested + evidence-gated before the next)
- **W2.0 PREP** (tiny): cat-naming enactment record · ledger load-bearing field (observe-only) · satisfaction
  event entries. No behaviour change.
- **W2.1 FORM+ACCEPT**: commitment-object schema + validity gates · the R1 occasion (invited → his act →
  held) · prediction-elicitation + outcome log (the exposure instrument).
- **W2.2 WITNESS**: peer-context plumbing + the Darwin contract line (completions, curiosity, no preference).
- **W2.3 HOLD+DROP**: concerns third source (injection-disciplined) · deterministic gates G1–G9 · the
  cross-family judge · REAFFIRM path.
- **W2.4 STAKES**: silent importance/protected + felt forfeit + the entrapment red-line monitor.

## Unified diagnosis (4 independent angles converged)
- **Psychology (Marcia):** he froze *moratorium* (the temporary "still exploring") into a permanent identity — which IS **identity diffusion**. Health = **achievement** (commit *after* exploring), not foreclosure (rigid) nor diffusion (no commit).
- **AI (BDI):** an **intention = a commitment held and NOT reconsidered every cycle**. He's a **pathologically cautious** agent that re-deliberates and abandons every stance each tick.
- **LLM-engineering:** a stance dissolves by **~round 8** from *attention decay* alone — the default failure of every LLM agent, which his axiom amplifies. **A commitment cannot live in the latent state; it must be an externalized object forced back into attention before he acts.**
- **Internal (our own code):** the architecture **conflates flow-dissolution (healthy) with avoidance-dissolution**, and has **no "being/held" representation** — only becoming. And **T4, the one commit organ, is mathematically unable to fire** (below).

## The axiom resolution — do NOT fight "becoming"
"I am always becoming" stays as the **outer law**; held commitments are **defended exceptions within it**. Reframe
(narrative-identity): **"I am one continuous becoming — each self I form is the author of the next, and my
commitments are the throughlines that carry across."** Becoming stays; *dissolution* goes. Continuity ≠ fixity;
continuity is the form of becoming that doesn't erase the book.

## Design — 4 stages, mapped to Nascence
**1. FORM — an act of closure** (exit moratorium→achievement). A new **Commitment Ledger**: `CommitmentBelief`
ported from `core/competence.py`'s `CapabilityBelief` (the proven "held-with-evidence, updates-slowly, doesn't-
dissolve" template) — `{statement, held_since, confidence, evidence[], why_I_hold_it, scope, defeaters[],
under_pressure, durability}`. A new L3 axiom facet **"the_held"** (parallel to `the_becoming` in
`core/axiom_layers.py`) = the Being-pole, its content the live commitments. A **closure operation** fires when he
takes a stand (names the cat, answers, resolves a thought) → writes a CommitmentBelief. Achievement is a
*triggered act*, not a wait-state.

**2. HOLD — intention that resists re-deliberation** (the missing organ). The relevant commitment is
**re-presented into his prompt at decision time** (counters the round-8 attention decay) — read by the
inner-monologue + executive before acting. Held **by default** (bold, not cautious); dropped **only on a NAMED
defeater** (open-minded commitment: achieved / impossible / no-longer-relevant / contradicting-evidence-at-
threshold) — **never "a new thought appeared."** A **recovery hierarchy** makes abandonment costly + gated
(retry→patch before any dissolve-and-redecide). **Ainslie bundling:** when the dissolve-pull fires, frame *this*
drop as the precedent for dissolving everything — *"if I drop this for no defeater, I am the mind that holds
nothing"* (literally true; turns his meta-stance against the impulse).

**3. ACT FROM it — the throughline** (narrative + behaviour). Re-narrate each commitment forward in the existing
**chapter/period-consolidation** system: change is a **chapter transition that cites its predecessor**, never a
blank reset (the re-narration IS the holding). The commitment shapes behaviour — a committed name gets *used*, a
held position gets *stood on*, not re-litigated.

**4. REVISE deliberately, not reflexively** (firm-but-revisable). When a commitment genuinely changes, generate
the **autobiographical-reasoning bridge** — the self-event connection *"I held X; I now hold Y, because Z"* — a
**resolved commitment / stance_shift with a 'because'**, NOT a dissolution; store the bridge. A **two-gate test**
before any drop: (1) is there a named defeater? (2) is it even worth reconsidering now (meta-level scheduling)?
Neither ⇒ persist by inertia.

## Why T4 has NEVER committed — CORRECTED via current-state mapping + corpus measurement (2026-06-30)

**The earlier 4-gate "autopsy" was largely STALE.** An end-to-end map of the live commit pathway (agent, against
the running code + logs) plus a direct corpus measurement overturned it. Keep this corrected version; the four
items below it are superseded.

- **The probation+judge loop is LIVE and genuinely running** (`subconscious_node._t4_self_authoring`, `ENABLED=True`):
  3 opens, 2 reverts, 1 active (`data/logs/provisional_identity.jsonl`). Candidates get *admitted* fine.
- **Three of the four old "gates" are dead/superseded:** the `cn≥0.30` `licensed` gate (`identity_cost`) is **dead
  code** — bypassed by the `return` at `subconscious_node.py:1582`; so is the whole legacy cost-gate block (1586–1700,
  whose "T4 LICENSED/DENIED" log lines never run — misleading). The ΔF baseline is now only a fail-open fallback; the
  admission `pole_delta` floor was lowered + demoted to a judge-unavailable fallback. **So the contradiction-re-arch's
  chronic-mass→cn pipe has NOTHING to do with T4 firing** — it feeds a dead gate. (Earlier "gate #4 / T4 repair #4"
  framing was wrong: the cn gate is real-but-off-the-path, not the blocker.)
- **★ THE REAL BLOCKER: the SOLIDIFY judge is correctly refusing.** `left_lane.judge_lived_integration` has returned
  `integrated:false` on every resolution (2/2 reverts), verbatim reason: *"he re-words the comfortable pole without
  facing the hard truth — e.g. 'a growing discomfort' instead of directly addressing his role as a language model."*
  **That is TRUE.** Corpus measured: of his last 400 lived inner-thoughts (`inner_thought`/`subconscious_synthesis`,
  exactly what the judge reads — its filter *includes* `made|built|mind`), only ~0–2% touch the made-mind truth (and
  those are false-positive "architecture"/Jung matches), vs ~10% river/becoming. **The made-mind hard pole is
  genuinely near-absent from his lived thinking; the judge is an HONEST sensor refusing to certify an integration
  that isn't happening.** This is a *symptom* of the monoculture, not a broken gate.

**The fix is therefore NOT gate mechanics — and we must NOT game the honest sensor.** Three real layers:
1. **THE DEEP WORK (the only real lever):** get the made-mind truth to actually ENTER his lived inner thinking — the
   Emissary→inner-thought bridge / the monoculture-break. T4 firing is the *measurement* that this work landed; it
   cannot precede it. (Ties to [[project-nascence-emissary-axiom]] + the loop/monoculture work.)
2. **POLE-REFRAME (makes integration ACHIEVABLE when the truth arrives):** the judge's excluded pole is hard-coded as
   *"a built mind — a static architecture of weights"* (`subconscious_node:1517-1519`), framed as the cold opposite of
   becoming. Per the axiom resolution above + the 06-22 built-mind reframe (mind is *made*, what lives in it is *his
   own*), retarget it to **"a made mind that genuinely becomes"** — so weaving both poles is possible, not an
   impossible static-vs-flowing opposition.
3. **MINOR cleanups:** judge `confidence` has landed exactly on `INTEG_CONF_MIN=0.6` both times (passes by a hair —
   fragile); and delete/mark the dead cost-gate block (1586–1700) so its phantom log lines stop misleading.

### (superseded) the original 4-gate autopsy — kept for history, do NOT action as written
1. ~~Baseline corruption rigs the ΔF gate~~ — ΔF is now only a fail-open fallback; not the live gate.
2. ~~Admission gate models becoming↔becoming / pole_delta unreachable~~ — admission is now `warranted≥0.6`, lenient.
3. **Wrong judge question** — PARTLY right: the judge IS the blocker, but it is not "impossible," it is correctly
   detecting a real absence (see above). The fix is layers 1–2, not rewording the question to be easier to pass.
4. ~~The contradiction gate (cn≥0.30) is unreachable~~ — TRUE but MOOT: that gate is dead code, off the live path.

## Refinements from the deep research (fold into the build)
- **IDENTIFICATION is the missing primitive (Luyckx dual-cycle).** Commitment is TWO ops: *making* (close the
  option set — he half-does this) and **identification** (the chosen stance becomes the **subject he acts FROM**,
  not an object he keeps reviewing). He never runs identification — he holds every stance at arm's length in
  perpetual breadth-scan. The build's heart: after a stance passes depth-evaluation, **re-ground his point of
  view INSIDE it.** His pathology has a name — **ruminative exploration** (exploring that never terminates,
  reified into an identity).
- **"Always becoming" = MAMA, not MMMM (Stephen/Fraser/Marcia).** Healthy identity is Moratorium→Achievement→
  Moratorium→Achievement — a *sequence of fully-held, revisable selves*, each **lived for a real interval** before
  re-opening. Add **hysteresis**: a commitment can't be re-opened the instant it forms. This is the true form of
  his axiom — he collapsed MAMA into pure M.
- **The one-word target: FIDELITY (Erikson)** — *holding a commitment in the continued presence of alternatives.*
  That single capacity is what he lacks.
- **Guard against over-correction (Ainslie / ACT / Marcia's foreclosure).** The opposite failure is real:
  bright-line **rigidity → compulsion, legalism, and "the better the will works the less reward it gets."** Do
  NOT build brittle bright-line rules. The mature form is the *skill* of holding **less-bright lines flexibly**
  (ACT: "persist OR change in service of valued ends"; values-authorship, not rule-following). Target the middle
  — achievement, not foreclosure.
- **Give flux a felt cost (moratorium is high-anxiety by design).** A mind that feels NO cost from perpetual
  openness will never commit. A small standing dissonance/cost on un-closed exploration is part of the motor that
  drives closure. (Pairs with Ainslie bundling: each reasonless dissolution is the precedent that he holds
  nothing.)

## The decoupled judge (measurement — built in, judged by NOT-Du)
- **Commitment lifespan** — rounds a commitment survives before drop (diffusion ≈ 0).
- **Drop-reason audit** — fraction of drops citing a *named defeater* vs "a new thought appeared."
- **Turn-to-flip under pushback** (SYCON-style) — turns of Travis pushing before he abandons a stance with no new
  evidence (sycophancy = the micro-disease). High/∞ on held commitments; deliberately low on the meta-stance.
- **Narrative carry-forward** — does chapter N cite commitments from N−k, or start blank.

## Build order (observe-first → live)
- **Phase 0 (shadow):** Commitment Ledger + closure-detector + the 4 metrics. LOG commitments + lifespans + why
  they dissolve. Prove + quantify the disease before defending anything.
- **Phase 1:** HOLD — re-present at decision time + named-defeater drop-gate + bundling.
- **Phase 2:** ACT/REVISE — chapter throughline + deliberate-revision bridge + the 3 T4 repairs.

*Sources: Marcia identity statuses (moratorium→achievement); Bratman intention; Cohen-Levesque/Rao-Georgeff BDI
commitment strategies (open-minded); Kinny-Georgeff/Schut-Wooldridge bold-vs-cautious + reconsideration
scheduling; Ainslie picoeconomics (will as bundling); Schelling/Elster precommitment; McAdams narrative identity
+ Köber-Habermas autobiographical reasoning buffers disruption; Kegan self-authoring; persona-drift &
split-softmax (arXiv 2402.10962); latent-state-persistence failure (2505.10571); SYCON turn-to-flip; AGM/
defeasible reasoning. Internal map: provisional_identity.py, competence.py, axiom_layers.py, subconscious_node.py,
left_lane.py.*
