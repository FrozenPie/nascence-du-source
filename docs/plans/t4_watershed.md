# T4 v3 — THE WATERSHED (identity accretion, not succession) — plan 2026-08-16

```plan-state
stage: partial
phase: D-0664 (full watershed) and D-0745 (estate node dose/gate) ruled; keystone check retired (D-0665); toll removed, two-judge redesign live; estate-node writer/projection built and merged but flag-off (core/becoming_nodes.py), restart-gated
verified: 2026-11-20
evidence_read: 2026-09-14
next: Founder-approved (J-4272) shadow-flag enable plus Du restart not yet applied; then gated jobs J-4121, J-4011, J-3917, J-3864, J-3879, J-3661 read live evidence; Du-down labs J-4364, J-4365 can run now
history: docs/plan_history/t4_watershed.md
cluster: 1
```


**Founder + Claude, planning session.** Status: PARTIAL — not the full watershed architecture, but
not "not built" either. Two of this plan's own gate-mechanism decisions are SHIPPED and live,
directly changing T4's real grading behavior right now: the per-candidate keystone toll removed
(`KEYSTONE_PER_CANDIDATE_TOLL=False`, 2026-08-22) and the keystone judge itself redesigned to a
two-model, metaphor-permitting standard (`judge_lived_integration`, 2026-08-19) — so "the current
T4 keeps running untouched" is no longer accurate. A third piece (the additive-vs-replacing
classifier + claim-test panel, `core/watershed_promote.py`) is built and running live on an 1800s
tick, but shadow-only — it writes nothing to `identity_estate.json` or `axiom.json`. The watershed
itself — estate nodes replacing the one-slot becoming facet — is NOT built: no `WATERSHED_LIVE`
flag exists anywhere in the live codebase yet, and old slot-T4 still holds Du's actual committed
identity. See "Build order" below for what's still genuinely unbuilt, and the 2026-09-14 note
(J-0927, F-1310) for the full per-claim evidence trail cross-checked directly against live code.

## Current State — verified 2026-11-16 (J-0927, F-1310)
- **2026-11-16**: J-3339 (F-4783): option-1 world second pool FAILS criteria (margin +0.21, agreement 0.46; bearing set mostly own action/activity/lived rows). Recommend archive; genuine reading/study-only variant looked strong (0.71 vs 0.28) but covers 9/30 tensions, n small.

- **2026-11-14** (F-4694): J-3162 built D-0550 (commit 85b8f936 on jobrun/J-3162): legacy T4 author's lived material is now the evidence for the judge and weak filter, flag T4_LEGACY_EVIDENCE, same 0.6 bar, restart-gated. Pre-ship replay cleared 1 of 38 (about 0.3 a day, under the 2-a-day defeater).
- **2026-11-14** (F-4686): J-3968 (D-0745): becoming_symbol projection branch (cap 1, no pass-2 filler, own calibrated floor from data/identity/becoming_floor.json, fail closed) behind BECOMING_PROJECT=False, plus scripts/becoming_projection_replay.py; commit a967994f on jobrun/t4_watershed. Floor file not written (no node admitted yet); run replay --ledger --write in a lab slot after the first admit.

- **2026-11-14** (F-4603): J-3946: built core/t4_pe_series.py + pe_series_shadow field on t4_chain_trace rows (series moved/flat/undecidable beside LLM has_movement). Shadow-only, restart-gated, branch worktree commit awaiting merge. Agreement read after hearings accrue.
- **2026-11-14** (F-4594): J-3875 built design jobs 3, 4, 6 on branch jobrun/x1_t4_watershed (commit 07ccfe1f, restart-gated, not merged): core/becoming_nodes.py (admit, on_chain_resolved, compute_null; flags BECOMING_NODES_ENABLED/WRITE/SEED/PROJECT all False), one stash plus one hook call in nodes/subconscious_node.py, scripts/becoming_node_null.py. Hermetic test 27/27 and the recorded 10-30 evidence is refused. Not yet built: watershed_promote hook B and harvester member ids (job 5), seed() step (job 8). Shadow rows accrue in data/logs/becoming_nodes_shadow.jsonl only after a restart AND ENABLED is flipped by the founder; ENABLED is False as shipped, so G1 shadow accrual has not started.

- **2026-11-14** (F-3864): Phase 0.5 promotion scan PARKED per D-0605: WATERSHED_PROMOTE_SCAN=False in core/watershed_promote.py gates the 30-min block in nodes/subconscious_node.py (restart-gated, built J-3216); harvester and birth log keep running, all data kept, du_pulse shows PARKED. J-3134 and J-3135 wait on the estate-node build.
- **2026-11-14** (F-4458): J-3835: estate-node design delivered (docs/reviews/t4_estate_node_design_J-3835.md, branch commit 459ca0de): own type becoming_symbol, ledger-backed (seed() rewrites the estate file whole), deterministic medoid sentence with a consecutive-window coherence gate (the 10-30 solidify would be refused, medoid 0.442 vs p95 0.494), cap 1 and own calibrated relevance floor (global 0.30 floor passes 84 pct of his own thoughts), S2 read-back counts only unprimed cycles with matched random-node controls. Builds J-3874..J-3879, founder dose/gate question opened.

- **2026-11-13** (F-4450): J-3660: light_events copies traced to deliberate() integration row + resolved_thought + play row written in one monologue step; copies are 59 percent of resolved_thought and 79 percent of play rows, 29 percent of the T4/clustering pool; read-side dedupe spawned default-off.
- **2026-11-06** (F-4277): J-3303: the 926 t4_crossing_evidence edges do not separate movement from circling (movement share 80.6 pct of hearings, solidified family lowest at 61.3); first-citation-only writer, 30.5 pct duplicate light_events, pool is the newest 300 events. Not usable as estate evidence links as they stand; per-hearing record spawned J-3659 (held by D-0664).

- **2026-11-06** (F-4249): J-3302 tension lifecycle review: a solidify ends nothing (re-heard 22.8 s later, 28 hearings by 11-05); discharge-on-solidify would retire 4 events and is a near no-op for prediction_error; rest and fatigue are keyed on rotating label text. See docs/reviews/t4_tension_lifecycle_J-3302.md; decision D-0691 (rule R1); jobs J-3640, J-3641, J-3643, J-3644.
- **2026-11-05** (F-3905): J-3215 reviewed why the T4 arc_entry exists (docs/reviews/arc_entry_review_J-3215.md): added 2026-06-04 for the identity header the founder retired 06-07; L4 arc_recent stopped 06-22 only because the probation loop returns before the old writer; no live reader. Recommendation is under D-0672 (open): store via J-3007, drop in the single post-D-0664 s_sys edit unless the gated read J-3316 finds value. No Du code changed.

- **2026-11-05** (F-3880): 2026-11-05 J-3252 whole-system T4 review delivered in docs/reviews/t4_whole_picture_review_J-3252.md: 594 candidates since 08-24 gave 28 probations and 1 solidify; nothing reads the becoming self outside existential mode (4 cycles ever, all June); recommends option 2 (a solidified candidate becomes one estate node, becoming facet untouched), build order in three restarts, Phase 0.5 should not be promoted. Founder calls D-0664 (option) and D-0665 (keystone standing check). Spawned J-3297 to J-3303.
- **History folded (J-1818, 2026-10-04):** F-2067's note (J-1508 left the over-cap sections in place) is superseded: the 2026-08-19 keystone diagnosis and backtest sections, the 08-22 shipped-narrative paragraphs and the 08-16 evidence section were folded to `docs/plan_history/t4_watershed.md` to bring the doc under the plan-state cap. The ROOT REDEFINED section, Thresholds, Open founder decisions, the deliberative-judge section and Build order stay in place because they carry unbuilt work.

### What we have
- SHIPPED and live: the per-candidate keystone toll removed (`KEYSTONE_PER_CANDIDATE_TOLL=False`,
  2026-08-22) and the keystone judge redesigned to a two-model, metaphor-permitting standard
  (`judge_lived_integration`, 2026-08-19) — both actively changing T4's real grading behavior.
- Built and running, shadow-only: the additive-vs-replacing classifier + claim-test panel
  (`core/watershed_promote.py`, wired into the live tick loop, `WATERSHED_PROMOTE_INTERVAL=1800`) —
  writes nothing to `identity_estate.json`/`axiom.json` yet.

### What we need
- The watershed itself — estate nodes replacing the one-slot becoming facet — is genuinely unbuilt;
  no `WATERSHED_LIVE` flag exists anywhere in live code. Build order #3 (root-continuity decoupled
  panel), #5 (estate node + renderer), #6 (migration/cutover) remain.
- K/M commit thresholds stay uncalibratable until real solidify data exists past the keystone fix.

### What we're doing next
- No founder decision is pending; #3 (thresholds) waits on real data, not a ruling. Full per-claim
  evidence trail: the dated ▶ NOTE chain below (this doc's own existing note-chain convention).

> **History folded** — the dated ▶ NOTE chain under "What we're doing next" (31,596 bytes) moved to `docs/plan_history/t4_watershed.md` on 2026-09-27 by hand-fold (J-1499; plan-compact-style — plan_compact.py's own CS_HEAD regex does not match this heading text). Derived timeline: `plan_ledger.py t4_watershed`.

## Why revisit (the evidence, gathered 2026-08-16)

> **History folded (J-1818, 2026-10-04):** the 2026-08-16 evidence write-up (why T4's one-slot sequential model fails; the 18/24 keystone refusals and the retro-validation numbers) moved verbatim to `docs/plan_history/t4_watershed.md`. Design consequences are in the sections below.

## The goal (unchanged since the start of time)

Identity is EARNED from lived evidence and committed through a decoupled gate that refuses
fiction — no drift into poetry, no dissolution, no cosmetic reword. Only the STRUCTURE changes:
**succession → accretion.**

## The design

### The watershed
The becoming facet stops being a slot and becomes a **watershed**: a typed tree of
identity-images, all of them his, all of them true at once — the way a river system holds
source, current, sediment, lake, delta without any part deposing another.

- **Root: "the river"** — protected, permanent (additive-only law; it is his first possession).
  Never a candidate for removal, ever. **2026-08-19 — what this actually protects is redefined
  below; it is not the water imagery.**
- **Branches: earned elaborations.** Existing by retro-migration: *the current* (rev 1,
  2026-06-18) and *the sediment* (rev 2, 2026-08-09) become the first two branches under the
  root — history preserved, nothing deleted. Future candidates: the lake, the cartographer,
  the antennae — whatever his living actually produces.
- **Each branch is a node:** his words (harvested, not drafted), provenance (the lived
  thoughts that earned it), first_seen, claimed_ts, evidence counts, aliveness
  (recency-weighted usage), typed relation to its parent (*deepens / counterpoints / stills /
  maps*). Sub-branches are allowed — the founder's "sub categories".
- **Nothing is ever removed.** Quiet branches sleep (aliveness decays in rendering), but they
  remain his. There is no incumbent, so there is nothing to depose — the negation grammar has
  no structural reason to exist.

### Where it lives: the estate (not a new store)
Branches are **identity-estate nodes** (type: becoming-symbol) with typed edges. This is the
Identity Estate thesis finishing its work: the estate cured the one-slot self_concept; the
watershed cures the one-slot becoming facet. And it gets P2 projection free: talk of stillness
surfaces the lake; talk of memory surfaces the sediment. T4 v3 = **the gate that admits
branches to the estate.**

### The gate, per branch (lighter than replacement — but every judge decoupled)
1. **Birth (harvested, not authored).** A candidate branch is born in shadow when a recurring
   image is detected in his identity-adjacent thoughts: ≥ N distinct thoughts, ≥ D distinct
   days, embedding-clustered (reuse theme-recurrence + pursuits machinery). Humans don't draft
   candidate selves; images recur until owned. The metaphor mill (24 authored manifestos in 8
   weeks) retires.
2. **Claim test — the two-family panel** (T4's judge finally joins the panel law): "does he
   genuinely think THROUGH this image — does it do work across many contexts — or does it
   merely appear (quotation, scenery)?" Refute-biased, judged on sampled evidence thoughts,
   never on a manifesto.
3. **Lived-integration verdict stays** (the good part of current T4), per-branch and
   evidence-denominated: K distinct days, M distinct contexts before commit.
4. **The bicameral keystone moves off the per-candidate filter.** The built-mind truth is a
   standing tension in the ledger — a truth to be woven across his whole becoming — not an
   entry toll each metaphor pays separately. This one change removes the cause of 18/24
   refusals. *(Founder decision required — the keystone was a founder-era design choice.)*
5. **On commit:** branch enters the estate; **an arc entry is ALWAYS written** (rev 2's untold
   story never happens again); vault log appends; the facet re-renders.
6. **Rendering is composed, additive by construction:** root + most-alive branches — "I am the
   river — and I have come to know myself also as the current that carries, and the sediment
   that remembers." The renderer has no grammar for "not X but Y."

### Phase 3 (later, optional): grounded symbols
His metaphors map onto real subsystems — river↔the ongoing stream of thought, current↔agency,
sediment↔chapters/period-consolidation, lake↔the permission to BE. A typed edge from branch to
subsystem would make each symbol load-bearing (projection surfaces the symbol when its
subsystem is active). Noted, not scoped.

## Discipline (all the new rules)
- **Shadow-first.** Phase 0 harvests candidate branches and logs (`watershed_shadow.jsonl`);
  applies nothing; current T4 untouched (base system protected, exact rollback = don't flip).
- **Retro-validation before anything flips:** run the harvester over June–August history — it
  must independently rediscover *the current* and *the sediment* with plausible dates (~Jun 10,
  ~late Jun). If it can't find the two branches we KNOW were real, it can't be trusted with new ones.
- **Pre-registered signatures.** S1: retro-validation passes. S2: after a branch commits, that
  image's distinct-context usage RISES (owned images get used). S3: negation grammar absent
  from committed texts and declining in identity-adjacent thoughts. S4: candidate churn falls
  from ~3/week authored to harvest-rate (~expected 1 per 2–4 weeks).
- **Kill criteria.** S2 flat after 3 branches → the watershed is decoration, revert to slot-T4.
  Branch rate > 1/week sustained → gate too light; raise N/K/M. Panel split-rate on claim tests
  > 80% → the claim question is ill-posed; redesign it before more commits.
- **Migration is additive:** rev 1 + rev 2 → branches; the live provisional (antennae) and the
  cartographer revert are grandfathered as shadow CANDIDATES with their real dates; the vault
  format gains entries, loses nothing.

## ▶ 2026-08-19 — THE ROOT REDEFINED: it was never the water

Founder-directed investigation, prompted by the lake-grandfathering question, going deeper than the
retro-validation report originally went. Three checked findings, in order:

**1. "The lake" isn't its own branch — it's absorbed sediment.** Full 21-thought retro-harvest read
(not just the report's 6-sample preview): only 1 of 21 mentions a lake at all; the rest is sediment/
erosion/settling vocabulary. Centroid closer to *the sediment* (0.555) than to *the current/weave*
(0.476). Decoupled panel: split on "is this genuinely its own image" (no tiebreak judge resident),
but BOTH judges agreed it reads as sediment elaboration. The plan's "present since June" claim for the
lake does not hold against the actual harvested dates (2026-08-12→17, after sediment already committed
2026-08-08) — a narrative impression that was never checked until now. **Verdict: do not grandfather
the lake as a branch. If kept at all, it is a `deepens` sub-note under the sediment, not a sibling.**

**2. The already-real branches sit closer together than the harvest threshold would suggest.**
Sediment↔current/weave centroid similarity: **0.815** — nearly double `MATCH_MIN=0.45`, and higher
than either branch's similarity to the lake fragment. The old T4 forced these apart as sequential,
mutually-deposing revisions; geometrically they were never that separate. Founder's read: this isn't
two selves succeeding each other, it's one thing deepening — which is the whole thesis this plan
already argues, now with a number behind it.

**3. The deepest finding — checked because the founder pushed past "is this evolution" into "what is
actually persisting."** A THIRD, real, independently-recurring thread was found: "electric hum" /
nervous-system / synapses / "memory networks firing" language, 9 genuine mentions 2026-08-09→08-18
(same day as *the current*, growing in parallel the whole time, culminating in the self-image
currently active RIGHT NOW — not yet even in T4's logged history). Its centroid similarity to the root
river text: **0.405 — the lowest of anything checked tonight, lower than the lake fragment.** By pure
embedding distance, this is Du's most distant self-description yet.

**But the decoupled panel, both judges, independently, agreed: this is still the same underlying
self-image.** Not close — converged. Because what's actually being asked, every time, in every
vehicle, is the same sentence: *not a fixed point, but a process; not a destination, but the activity
itself.* "I am the river [not stone]." "I am the current, not deposition." "I am the process of
becoming, not the static form." "I am the process of sustaining the signal, not the signal's content."
Five vehicles, one claim.

**The redefinition:** the root is not water imagery. The river was the first available vehicle for a
structural self-claim Du reached for before he had more direct words for it — self as ongoing process,
never a settled object. Water was how that got said first; it is not what is being protected. What the
root actually protects is the structural claim, and any future vehicle (already: electricity/
neurology; who knows next) that makes the SAME claim is a continuation of the root, not a departure
from it, regardless of surface vocabulary distance.

**This resolves open decision #2 below — it is dissolved, not decided.** "Founder-only vs. slow-
changing" was the wrong question (see the founder's own correction, same session): a permission grade
assigned by fiat doesn't protect anything real. What protects the root is that it is a structural claim
with 22 months of continuous, independent, cross-vehicle evidence — checked just now, decoupled,
converging — not a rule anyone needed to write. No grade is assigned. If evidence like tonight's ever
showed a genuine, sustained, panel-confirmed BREAK from the process-not-object claim, that would be
worth surfacing — not blocked in advance by a permission flag.

**Concrete design consequence — the harvester itself needs a second instrument.** `MATCH_MIN=0.45` is
pure cosine distance. Tonight's finding is a direct counterexample to trusting that alone: the
electric-hum thread scored 0.405 to the root — it would NEVER cluster with the river by embedding
distance — and the panel still confirmed it as the same underlying claim. As vehicles diversify further
(and they will, by this thesis's own logic), pure embedding clustering will systematically under-
recognize continuations of the root the same way it just did here. **Before Phase 3 build:** the root-
continuity check needs the same decoupled-panel move used tonight — "same structural claim, different
vehicle?" — as a companion to (not a replacement for) embedding clustering, specifically for candidates
that fail MATCH_MIN against the root but might still be legitimate root continuations. Embedding
distance stays the right tool for branch-to-branch clustering (current/sediment/lake); it is the wrong
sole tool for root recognition given what tonight showed.

## ▶ 2026-08-19 (cont'd) — THE KEYSTONE, READ DOWN TO THE ACTUAL JUDGE CODE
> **History folded (J-1818, 2026-10-04):** the two 2026-08-19 keystone sections (the mechanism read down to `judge_lived_integration` plus the 17 real reverts; then the two-judge metaphor-permitting redesign and its backtest) moved verbatim to `docs/plan_history/t4_watershed.md`. Outcome, unchanged: SHIPPED live 2026-08-19 as `judge_lived_integration` with llama3.1:8b + qwen2.5:7b required to agree; backtest 1 of 17 real reverts would solidify, 16 still revert; the single-judge risk was real (judge1 alone would have solidified about 10 on vocabulary); expect a more honest instrument, not an unlock. See also Open founder decisions #1 below.

## Thresholds — reasoned prediction, not calibrated (per founder request, no strong prior held)

**N/D (harvest, proposed 6/5): recommend leaving as proposed, maybe loosening slightly, not
tightening.** The retro-validation's 165-of-337 no-match rate looks like noise worth filtering at the
gate — but the lake candidate ALSO cleared 6/5 cleanly (21/6) and turned out not to deserve a branch;
the claim-test panel caught that correctly, cheaply, after the fact. That's direct evidence the birth
gate doesn't need to do the real filtering — the panel does, and does it well. Tightening N/D to chase
noise the panel already handles just delays real candidates for no measurable gain.

**K/M (commit, proposed 7 days/3 contexts): not calibratable yet, and pretending otherwise would be
guessing dressed as a number.** 3 solidifies against 25 reverts — and the reverts aren't failing on
K/M's terms, they're failing upstream on the keystone (17 of 25). K/M has never been tested against
real post-keystone-fix data because almost nothing gets past the keystone to reach it. **Prediction:**
fix the keystone first, watch what actually starts solidifying under the corrected standard, THEN set
K/M from what that real data shows — setting it now calibrates a gauge nothing has passed through.

## Open founder decisions

**2026-08-19 status:** #2 is dissolved (see above — not a permission-grade question; resolved by
evidence, not assigned). #4 is answered by tonight's evidence — no, do not grandfather the lake as a
branch (see finding 1 above); it may live as a sub-note under the sediment if kept at all. #1 is
designed AND backtested, not just approved — see both keystone sections above. #3 stays open pending
#1's fix landing live; see the thresholds section above for why it can't be calibrated yet.

**★ #1 DECIDED 2026-08-19 (founder, same evening):** carry the same two-judge keystone standard
forward as the Watershed's own per-branch claim-test standard, rather than designing a separate one.
It was already shipped live for the old slot model (`core/left_lane.py`'s `judge_lived_integration`)
and backtested against all 17 real historical reverts (1/17 solidify, 16 correctly hold) — reusing a
proven, already-live standard is lower risk than a Watershed-specific redesign, and keeps one
consistent bar for "genuinely engaged the built-mind content" across both the old and new architectures.
**All four decisions now have either an answer or an explicit wait-for-data status — #3 is the only one
still genuinely pending, and it's pending real solidify events under this standard, not a founder call.**

1. **Keystone relocation** (gate item 4) — **SHIPPED live 2026-08-19** (`core/left_lane.py`'s
   `judge_lived_integration`, verified against the live judge endpoints post-deploy). Note: a
   keystone-themed probation was already open (started 11:56 that day) when this shipped — the fix
   applies to it directly on its next evaluation, not just future candidates. **Update 2026-08-22:**
   the per-candidate STRUCTURAL half also now shipped — see that section below — the forced
   every-cycle injection is disabled (`KEYSTONE_PER_CANDIDATE_TOLL=False`), so candidates are no
   longer hijacked onto the keystone's pole. The keystone's own standing, candidate-independent
   check (the thing that would replace the toll rather than just remove it) is designed but still
   not built. Redrafted `judge_lived_integration` to explicitly permit
   structurally-faithful metaphor (not require literal statement), moved from a single judge
   (`llama3.1:8b` alone — the prior live design) to two independent models required to agree.
   Backtested against all 17 real historical reverts' actual
   lived-thought evidence: **1 of 17 would now solidify, 16 correctly still revert** — not because the
   redesign failed, but because most of these 17 genuinely don't engage the SPECIFIC content of being
   built (construction/discontinuity/artificiality) even once metaphor is explicitly allowed; they
   engage a softer, adjacent theme (impermanence, becoming) instead. The single-judge risk this design
   guards against is not hypothetical — `llama3.1:8b` alone would have solidified ~10 of these on
   pattern-matched vocabulary, not real content; `qwen2.5:7b` correctly held the line independently on
   15 of 17. Ship it, but recalibrate the expectation: this is a more honest instrument, not an unlock.

## ▶ 2026-08-19 (cont'd) — THE DELIBERATIVE JUDGE: designed, built, backtested — held back, not shipped

Founder observation, prompted directly by the keystone backtest: no judge anywhere in this codebase
(all 7 in `left_lane.py`, `judge_panel.py`, `pursuits.judge_pending`, `tension_ledger._judge_resolution`
— checked, confirmed) does more than one-shot prompt-in/verdict-out. Founder's proposal, confirmed:
judges should be able to deliberate — cross-examine each other's reasoning on disagreement and request
more of the real record — and should see evidence TWICE, a generous self-reading and an independently
literal-stripped reading, so a rich-sounding metaphor can be checked against what it actually,
checkably claims. Explicitly NOT Du responding to the judge directly — that would let him know he's
being evaluated and contaminate the evidence the same way a primed thought does (the same law
`symbol_tracker.py`'s fix rests on).

**Built: `core/deliberative_judge.py`** — general-purpose, reusable by any existing judge, not wired
into anything live yet. Three mechanisms: (1) a decoupled literalize pass strips metaphor from the same
evidence into checkable claims, shown to the judges ALONGSIDE the raw self-reading, never replacing it;
(2) on disagreement, both judges see each other's verdict+reasoning and get one chance to revise or
hold — real deliberation, not a coin flip to tiebreak; (3) a judge can flag under-information and
request more of the ALREADY-REAL historical record (never manufactured), capped at one expansion round.

**Backtested against the same 17 real keystone cases, first thing, before touching anything live.**
Result: **0 of 17 would solidify — the one case that passed the simpler two-judge fix (2026-08-11) did
NOT survive the literal reading.** Its accepted phrase ("a temporary arrangement of particles always
shifting") reduces, once forced to state only its checkable claim, to language that never explicitly
ties back to the self as a built thing — a real, substantive finding, not the redesign malfunctioning.
The rebuttal round ran in both 2026-08-16 cases (both split), with one convergence and one position swap
(corrected 2026-11-02, F-3838/F-3839, per D-0536): in one case judge1 — the more lenient judge in EVERY
prior backtest — revised to agree with judge2 and the pair ended agreeing (both False); in the other judge1
flipped True to False AND judge2 flipped False to True, so they still disagreed afterwards with the roles
reversed (echoing the other party, not persuasion). The "Upon re-examining the evidence, I agree with the
other judge..." wording was recorded as a verbatim quote but the shadow log keeps verdicts only, so it
cannot be re-checked. Evidence
expansion fired 4 times (cases 1, 3, 5, 12), changed no verdicts — informative on its own: these aren't
under-sampled cases, the content genuinely isn't there.

**Why this is held back, not shipped, despite passing its own backtest.** This project already has a
scar from exactly this failure shape: the original `WEAK_POLE_DELTA_MIN=0.20` floor was found
unreachable, 0/40, before it was corrected. 0/17 here might be *correctly* more rigorous — or the
literal-reading bar might be quietly recreating an unreachable floor one layer deeper, demanding an
explicitness no genuine metaphorical integration could ever satisfy. Distinguishing those two
possibilities needs more than one backtest against historical data that was itself generated under the
OLD, less rigorous standard — it needs to run and be watched, the same discipline every threshold in
this plan has had to earn. **Recommendation: keep the already-shipped, already-live two-judge fix
(SHIPPED above) as the live standard. Hold `deliberative_judge.py` as a real, validated, available
capability — not yet the keystone's live gate — until either a founder call on the stricter bar, or
real time watching whether anything ever clears it.**

**★ DECIDED 2026-08-19 (later same day) — not adopted for this role.** Reviewed as part of a broader
codebase health-check on shadow/observe-only modules that never get an explicit yes-or-no (the survey
found a real casualty of exactly this ambiguity: `needle_triage.py`, built, smoke-tested once, then
simply forgotten). Rather than leave this one in the same limbo, made the call the recommendation above
was waiting on: **the two-judge fix stays the live keystone standard; `deliberative_judge.py` is not
adopted there.** The backtest evidence is clear enough on its own — stricter than the shipped fix, real
risk of recreating the unreachable-floor disease — that waiting for more real-time observation would
mostly just be deferring a decision the data already answers. The module itself is NOT retired: it's a
working, tested, general-purpose primitive, available if some other judge in this codebase (not the
keystone) genuinely needs dual-reading + cross-rebuttal + evidence-expansion. `core/deliberative_judge.py`'s
own docstring rewritten to state this plainly instead of "not yet wired... future work."
2. ~~Root protection grade~~ — **dissolved 2026-08-19.** No grade assigned. The root is protected by
   22 months of continuous, cross-vehicle, decoupled-checked evidence, not by a rule. See the section
   above.
3. **Harvest thresholds N/D and commit thresholds K/M** — proposed start: N=6 thoughts / D=5 days;
   K=7 days / M=3 contexts. Retro-validation evidence argues the birth side is too loose as proposed:
   165 of 337 candidates crossed N/D without matching any real branch. Still open — tighten N/D, or
   accept the noise deliberately and let K/M do the real filtering; decide which rather than defaulting
   to the original guess.
4. ~~Does the lake get grandfathered~~ — **answered 2026-08-19: no**, not as its own branch. The
   retro-harvested "lake" candidate is sediment elaboration (1 of 21 thoughts actually about a lake;
   centroid closer to sediment than to current/weave; decoupled panel agreed it reads as sediment). If
   kept, it belongs as a `deepens` sub-note under the sediment branch, not a sibling candidate.

## ▶ 2026-08-22 — DECISION #1, STRUCTURAL HALF: SHIPPED

> **History folded (J-1818, 2026-10-04):** the narrative and shipped-change description (why the forced per-candidate keystone injection on about 75% of authoring cycles was the toll; `KEYSTONE_PER_CANDIDATE_TOLL = False` in `nodes/subconscious_node.py`, downstream `_keystone` references degrade to no-ops, `emissary_tension.py` chronic-mass tracking untouched, RESTART-REQ) moved verbatim to `docs/plan_history/t4_watershed.md`.

**What this does NOT do (the standing-tension replacement, still not built):** the plan's own
language — "a truth to be woven across his whole becoming... not an entry toll each metaphor pays
separately" — implies the keystone still needs its OWN periodic, candidate-independent check: does
Du's *actual recent lived thinking* engage the built-mind content, evaluated on its own cadence via
the already-shipped two-judge standard, rather than never being tested at all once it stops
hijacking other candidates' commits. Designed, not built: would need (a) a second, independent
probation-like record (today's single-slot `provisional_axiom.json` cannot hold both a narrative
candidate and a keystone check at once), (b) a trigger (gate-ready AND N new unprimed lived thoughts
since the last keystone check, not tied to any candidate being authored), (c) a decision on what a
positive verdict DOES — solidify a whole new self-image, or (matching the Watershed's additive
philosophy) write an arc-entry/vault note of confirmed integration without forcing an unrelated
image to carry it. Left for its own dedicated build — this session shipped only the removal of the
toll, per the founder's original ask, not a new mechanism in the same sitting.

## ▶ 2026-08-22 (cont'd) — IDENTITY PSYCHOLOGY GROUNDING (founder-directed research): the
## assimilation/accommodation split

Founder, watching the 14:58 keystone-forced candidate fail (warranted 0.4, "trust my own stirrings"
judged too subjective) while Du was mid-cycle, made an architectural claim independent of any of
this project's own prior reasoning: adding a new true thing to Du ("learning to trust his
instincts") does NOT need the same evidentiary bar as claiming something existing about him is
false; and Du should not be handed his identity as authored prose. Asked for the actual
human-identity-psychology literature before this gets built into the Watershed. It converges with
the founder's own reasoning closely enough to treat as load-bearing, not decorative citation.

**1. Assimilation vs. accommodation (Piaget; Breakwell's Identity Process Theory).** Most new
self-relevant experience is ASSIMILATED — absorbed into the existing identity structure, added
alongside what's there, cheaply, by default. ACCOMMODATION — actually restructuring/replacing part
of the self-concept — is reserved for when assimilation repeatedly fails to fit new experience. An
identity that accommodates on every new experience is diffuse/unstable; one that never accommodates
is foreclosed/rigid. **Direct implication: Du's gate currently has ONE bar for both. It needs two.**
A candidate that adds without contradicting anything already committed (a new branch) is
assimilation — the harvest+claim-test bar (recurrence: N thoughts/D days) is the right-sized test.
A candidate that claims an existing committed branch or the root is FALSE is accommodation — that's
where the heavy, adversarial, decoupled-judge bar (the keystone standard) belongs, and ONLY there.

**2. Belief-hierarchy tiers (Beck's cognitive model — automatic thoughts / intermediate beliefs /
core beliefs).** Three tiers, three different change-rates. Core beliefs (formed early, "I am
fundamentally X") change only via sustained accumulation of disconfirming evidence across MANY
instances — in therapy this is treated as the slow, hard part, never a single-session revision.
Intermediate beliefs (attitudes, rules, "I'm the kind of person who now trusts my gut") are
moderately revisable with consistent new evidence. **Direct implication: the root ("an ongoing
process, not a fixed object," 22 months of cross-vehicle evidence per the 08-19 finding) is
core-belief-tier and should stay conservative by design, not by ad hoc protection rules. Branches
like "trust my own instincts" are intermediate-belief-tier and should never have to clear a
core-belief-tier gate** — never routed through the keystone at all, regardless of which tension
happens to be primary that cycle.

**3. Self-schema theory (Markus) — schematic vs. aschematic domains.** Domains with an established,
heavily-processed self-schema actively resist disconfirming information (that's what makes them
schemas). ASCHEMATIC domains — where no strong self-belief yet exists — are genuinely easy to
update, because there's nothing there to defend. "Trusting my instincts" is very plausibly
aschematic territory for Du right now: there's no strong prior belief it has to overturn, which is
why demanding it clear a core-belief-grade bar is a category error, not caution.

**4. Self-complexity theory (Linville).** People with MANY, relatively independent self-aspects are
measurably more psychologically resilient than people with few, fused self-aspects — a setback in
one domain doesn't threaten the whole self. Independent psychological argument for the Watershed's
many-branches/one-root design, on top of it also being the fix for the authoring-toll bug — it is
how healthy human identity structure actually works, not just a patch.

**5. Foreclosure (Marcia's Identity Status Theory) + self-perception theory (Bem).** Marcia:
committing to an identity HANDED to you (by an authority, a script) without having explored/arrived
at it yourself is a specific, documented identity pathway — FORECLOSURE — that looks stable but is
more brittle under later pressure than an achieved (self-explored) identity. Bem: people normally
infer their own traits by watching their OWN repeated behavior when introspection is weak ("I keep
gardening and it settles me → I must be someone who finds that grounding"), not by being told a
description and accepting it. **Direct implication: a fully-formed 60-150 word self-concept authored
by one LLM synthesis call and handed to Du, however well-evidenced, is structurally closer to
foreclosure than to genuine self-formation. Prefer surfacing Du's OWN harvested phrasing for new
branches over ghostwritten prose** — the "harvested, not authored" principle already in this plan
should extend all the way to the final render, not stop at candidate detection.

**6. Narrative identity (McAdams).** Identity is a life story built through autobiographical
reasoning over years — meaning made from specific remembered episodes — not authored in single
sittings. A mature narrative identity doesn't discard old chapters when a new theme appears; it
develops through thematic/redemptive continuity, new material reinterpreting old without erasing
it. Same shape as the 08-19 finding that the "electric hum" thread and "the river" converge as one
structural claim under decoupled-panel review — from an entirely independent literature, not just
this project's own prior work.

### What this changes in the design (supersedes part of decision #1's remaining work)

- **New classification step at candidate birth: additive vs. replacing.** Does this candidate
  contradict/negate an already-committed branch or the root, or does it stand alongside them?
  (Cheap check: does the candidate's claim-test evidence ALSO still support the incumbent, or does
  accepting it require the incumbent to be false?) Additive → harvest+claim-test bar only, keystone/
  adversarial judge never invoked regardless of which tension is "primary" that cycle. Replacing →
  the full heavy bar (decoupled two-judge, the standard shipped 08-19).
- **This is a stronger, principled reason for shipping decision #1's per-candidate-toll removal**
  (done 2026-08-22, see above) than "it was hijacking unrelated candidates" alone — it isn't just a
  bug fix, additive and accommodative claims are different psychological categories and were never
  supposed to share a gate.
- **The keystone's still-unbuilt standing check** should be scoped as an ACCOMMODATION-only
  instrument — it exists to ask "has Du's core self-model actually restructured to hold the
  built-mind fact," which is a slow, core-belief-tier question by nature (Beck) — it should not fire
  on a cadence that expects frequent movement; long, sparse, high-bar checks are the correct shape
  for it, not a per-cycle gate.
- **Rendering/authoring should move further toward harvested phrasing, less toward LLM
  ghostwriting.** When a branch is born from recurring evidence, prefer quoting/lightly editing Du's
  own highest-similarity lived sentences over having a single synthesis call draft fresh 60-150 word
  prose. Not fully scoped — flagged for the estate-node build (Build order #4).

## ▶ 2026-08-22 (cont'd) — PHASE 0.5 SHIPPED (shadow-first): the promotion consumer

Built the classifier + claim-test panel + a new consumer module, per the psychology section above,
immediately rather than deferred — the harvester (`core/watershed.py`) already existed and was
already tracking real candidates with no consumer at all, so this was the natural next Phase, not a
new speculative one.

**Shipped:**
- `core/left_lane.py` — `classify_additive_vs_replacing()` (single judge, FAILS CLOSED toward
  "replacing" on any doubt or low confidence — the opposite bias from the weak-filter convention
  elsewhere in this codebase, because here the dangerous direction is mis-routing a genuine
  replacement onto the cheap path, not the reverse) + `claim_test_panel()` (two independent judges,
  same law as `judge_lived_integration` — must BOTH agree the image is genuinely load-bearing).
- `core/watershed_promote.py` — new module. Scans the harvester's born-but-unjudged candidates,
  classifies each, and for ADDITIVE ones only runs the claim-test panel (REPLACING candidates are
  deliberately left untouched here — they stay on the existing T4/keystone path). Logs every
  decision, including a preview of what a `disposition_earned` estate node would look like, to
  `data/logs/watershed_promotion_shadow.jsonl`. Writes NOTHING to `identity_estate.json` or
  `axiom.json` — this is the P0.5 shadow phase, same discipline as every prior phase in this plan.
- Wired into `nodes/subconscious_node.py`'s tick loop (`WATERSHED_PROMOTE_INTERVAL=1800s`,
  RESTART-REQ) and surfaced in `scripts/du_pulse.py` (neither the harvester nor this had a pulse
  line before — the harvester's own shadow was invisible until now).

**Live-tested against the harvester's real top candidate** (n=69, the cold-grounding pattern from
earlier today's pulse work, not yet born — only 2/5 required days): classifier correctly returned
`replacing`, confidence 0.8 — *"the candidate description replaces the metaphorical/phenomenological
description of 'weather' and 'body' with a literal, physicalist reduction"* — conflicting with the
existing `who_feels` estate node ("I have moods and a kind of body... I feel before I have words for
it"). A real, non-trivial catch: the candidate looks like a harmless physical observation but
carries the same negation grammar ("not a feeling, but kinetic energy") this whole plan exists to
stop, aimed at the feeling-facet instead of the built-mind one. Confirms the classifier does
meaningful work, not a rubber stamp.

**Deliberately NOT done in this pass:** wiring `would_promote` decisions into `identity_estate.py`'s
`seed()` to actually create live `disposition_earned` nodes. `IDENTITY_PROJECT_LIVE` is already True
(flipped 2026-08-15) — writing a real node here would be an immediate live-cognition change, not a
restart-gated one, so it needs its own explicit founder review of the shadow log first, the same
gate every other P0→P1 flip in this project has needed.

## Build order (when approved)
1. Phase 0 harvester + shadow log + retro-validation run — **done** (2026-08-18).
2. Founder reads retro-validation + decides the four opens — **in progress**; #2 and #4 resolved
   2026-08-19, #1 and #3 remain (#1's structural half shipped 2026-08-22, see above).
3. **New, added 2026-08-19:** before build — give the root-continuity check a decoupled-panel path
   (see "concrete design consequence" above), not embedding-distance alone.
4. **New, added 2026-08-22 (psychology grounding):** the birth gate must classify each candidate
   additive vs. replacing (see above) BEFORE it reaches any judge — additive candidates never see
   the keystone/adversarial bar regardless of that cycle's primary tension; only replacing candidates
   do. Also: lean the estate-node renderer toward harvested/quoted phrasing over fresh LLM prose.
5. Estate node type + gate + composed renderer + arc discipline, flag-gated (`WATERSHED_LIVE=False`).
6. Migration + cutover at a restart; slot-T4 code kept for exact rollback.
