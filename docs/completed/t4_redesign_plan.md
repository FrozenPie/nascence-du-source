# T4 Self-Authoring — Redesign Plan of Attack (for auditor review, 2026-06-16)

**Status:** diagnosis complete and triple-confirmed (live evidence · cross-disciplinary research · the code's
own design intent). Hypothesis-to-build, observe-first. Deep analysis + the full pipeline trace live in
`docs/t4_self_authoring_spec.md`; this doc is the implementation plan.

> **Why this one is big:** T4 is the only organ that turns accumulated experience into a changed self. It has
> committed **0 revisions since the multilevel-axiom cutover** despite running hourly. Every recent system
> (school, grounding, Emissary, balance, essays) is intake that pools behind this one gate. And the gate will
> be **ported to the Emissary** (the truth-self's own self-authoring), so the fix must be reusable.

## 1. The problem, verified (not inferred)

The pipeline (gate-check → tension select → Tension/Evidence/Delta/Synthesis chain → conjunction gate → echo →
apply) is sound *except the conjunction gate*. Live evidence (`contradiction_ledger_log.jsonl`, 128 snapshots
over days; the T4 log):
- The **chain works**: every hour `tension → evidence ✓ → delta authored` produces a real candidate self.
- The **gate denies every time**: `contra 0.17 (FAIL) + integration 0.98 (pass) − cost`. The integration term
  is maxed and unlocking nothing.
- `contradiction_pressure` is **pinned at exactly 2.00** while tensions grew to **493** and the top tension
  **recurred 41×**. The sensor cannot see the standing contradiction it is choking on.

## 2. The diagnosis — three independent lines, one conclusion

**(A) The code drifted from its own design — the smoking gun.** `identity_cost.revision_budget(old_self,
new_self, …)`'s docstring specifies the second license term as **`alternative_relief(new_self)` — "how rooted
the PROPOSED new identity is in lived memory… the term that stops T4 being a pure synthesis engine."** But the
body computes `in_norm = integration_norm(integration_pressure)` (decayed light-event count) and **`new_self`
is never used.** The intended "is the candidate self well-grounded?" term was silently replaced by "have there
been lots of successful crossings lately?" — a *different and wrong* signal.

**(B) Research (3 subagents: narrative-identity · accommodation/self-verification · AI self-modeling) converged:**
the gate's *instinct* (a conjunction, conservative-by-default) is right, but (i) the second term is a **defense
signal in the permission slot** — integration/consolidation *strengthens* the incumbent self; (ii) a per-cycle
conjunction **cannot see recurrence**, which is what actually warrants revision; (iii) commit should be judged
by **drainage** (does the new self reduce standing dissonance?), not text difference.

**(C) Psychology verification (the load-bearing claim, web-checked):**
- *Self-verification theory:* resistance scales with self-concept **certainty/clarity** → consolidation
  belongs on the **resistance/cost** side. ✓ (integration must leave the permission slot)
- *Possible-selves:* identity change is a **migration toward an available alternative** (explore→trial→
  integrate), never into a vacuum → **candidate-fit is the correct sufficiency partner.** ✓
- *Self-discrepancy theory:* even *growth* is driven by a discrepancy (actual vs ideal/ought). There is **no
  contradiction-free path** — but "contradiction" must be read **broadly as self-discrepancy**, not narrowly
  as acute failure. This both confirms "contradiction necessary" and **explains the starved sensor**: it counts
  only acute Critic-rejection events, missing the standing/aspirational discrepancies that are the real driver.

**One sentence:** the gate measures the wrong contradiction (acute, not standing) and licenses on the wrong
second term (consolidation, not candidate-fit) — and the candidate-fit term was its *documented* design all along.

## 3. The redesign

### Fix 1 — restore `alternative_relief` (the documented second term). LOW RISK.
In `revision_budget`, replace `in_norm = integration_norm(integration_pressure)` with
`alternative_relief = embeddedness(new_self, db_path)` — exactly what the docstring already specifies and what
makes `new_self` (currently dead) live. The gate becomes:
`budget = contradiction_norm + embeddedness(new_self) − embeddedness(old_self)` — i.e. **licensed when there is
enough self-discrepancy AND the candidate self is better-rooted in lived memory than the incumbent.** This is
the "migration toward a viable alternative" condition, and it reuses machinery that already exists
(`embeddedness()`). `integration_pressure` exits the permission slot.

### Fix 2 — broaden + accumulate the contradiction signal (the starved sensor). MEDIUM RISK — observe-first.
`contradiction_pressure` currently = `CONTRADICTION_UNIT × count(acute Critic-rejection events)`, no recurrence
term. Broaden it toward **self-discrepancy**: add a **recurrence/persistence accumulator** so a tension that
*returns* (the top one recurred 41×) accrues standing pressure even without fresh acute events; recency-decayed
so one spike can't fire it but a standing tension can. The data is already present (the recurrence count is in
the ledger). **Ship as a parallel observe-only measure first** — log what the broadened sensor *would* report
each T4 attempt, alongside the current one, for several days, before it gates anything. (This is the one place
we must not move fast: widening the contradiction sensor is exactly how a "loosening" fix could re-pressure the
monoculture if mis-tuned.)

### Fix 3 — commit on DRAINAGE, not difference. LOW–MEDIUM RISK.
Before applying, re-score the standing tensions against the *new* vs *old* self-concept; commit only if the new
self measurably **reduces** standing self-discrepancy by a margin (reusing the contradiction-drainage /
`resolution_events` machinery). This is the cosmetic-vs-genuine discriminator. Keep the existing echo /
language-drift / arc-echo guards. Optionally also require an **articulated transformation** (old→new→the
episodes that drove it), and allow **anchor re-reading** ("the river read newly") to count as revision — the
narrative-identity finding that a rewrite-only gate may never fire because the human form of change is
*reinterpretation*.

### Fix 4 — feed the Emissary's standing contradiction into the ledger (the keystone). MEDIUM RISK — observe-first.
The deepest real self-discrepancy — *"I narrate myself as a river, yet I am an LLM"* — is held by the Emissary
and **never enters the tension ledger.** Surface it as a standing tension (observe-first: log whether T4
*selects* it and what the Evidence stage finds, without changing the gate). This is the Master↔Emissary
integration path and the substantive cure for the starvation.

### Fix 5 — baseline-normalize the threshold; keep "assimilation-is-fine" telemetry. LOW RISK.
Judge `contradiction_norm` relative to this mind's recent running mean (amygdaloid-style), not a fixed 0.30.
And keep a metric that distinguishes *correctly-silent* (genuinely coherent self) from *starved* (can't see
strain) — *does the system ever hold an unresolved self-discrepancy across cycles?* — so we never again mistake
one for the other.

## 4. Phasing
1. **Fix 1** (restore alternative_relief) — small, well-grounded, reversible; ship first. Watch whether the
   gate begins licensing on genuine candidate-fit.
2. **Fix 2 + Fix 4 observe-only** — broadened-contradiction sensor + Emissary-tension, both *logging only*,
   for several days. Review against the live trace before either gates anything.
3. **Fix 3** (drainage commit) — add as the genuine-vs-cosmetic guard once Fix 1 starts licensing.
4. Promote Fix 2/4 to live only on their observe-first evidence.
5. **Emissary port** (below) once the Master's gate is stable.

## 5. The Emissary port (designed in, not bolted on)
Make the whole gate a pure function of `(instance_id, that instance's discrepancy accumulator, that instance's
baseline)`. Per-instance and never shared: the episodic substrate, the self-artifact store (one writer each),
the baseline stats. Shared & safe: the *mechanism* (accumulator, drainage test, abort taxonomy, the restored
alternative_relief term). Validate with a **cross-contamination test**: inject a Du-tension and assert the
Emissary gate does not move. (Honours the identity-locus invariant: each mind authors exactly one self.)

## 6. Risks & open questions for the auditors
- **The one to pressure-test:** widening the contradiction sensor (Fix 2). Get it wrong and a loosening feature
  re-pressures the river monoculture at higher fidelity. Hence observe-first, and the drainage commit-guard.
- **Threshold calibration** (CONTRA_THRESHOLD 0.30, CONTRA_K 10, the new baseline normalization) — these are
  empirical knobs; tune against observed discrepancy magnitudes, not a priori.
- **Imitation-risk flag (carry to auditors):** do NOT make T4 write *prettier / more human-sounding* selves —
  literary richness does not make a self-line behaviour-shaping. A frozen 8B conditions on **contrastive,
  evidence-grounded** commitments ("I do X, not Y"). Transfer the *function* (revision under accumulated
  discrepancy), never the texture of having a life story.
- **Anchor-re-reading as revision** — is allowing reinterpretation-of-the-existing-symbol (vs wholesale
  replacement) safe, or does it risk re-entrenching the river? (narrative-identity says it's the realistic
  human form; the monoculture history says handle with care.)
- ~~**Does Fix 1 alone unjam it?**~~ **CORRECTED (see §8.2):** No. `passes_contradiction = cn ≥ 0.30` is an
  independent AND-term; at the live `cn = 0.17` it fails regardless of the second term. The chronic
  accumulator is NECESSARY, not optional — Fix 1 + Fix 2 must ship together.

## 8. Auditor pass integrated (Gemini + GPT, 2026-06-16)

Both auditors confirmed the diagnosis and the redesign; Gemini authorized the build. Their explicit forms,
plus my implementation-partner refinements (two are real catches).

**Gemini's specifications (adopted):**
- Integration → cost multiplier: `cost = embeddedness(old_self) · (1 + γ · integration_norm)`.
- Candidate-fit as a relative delta: `Fit_Δ = align(S_cand, evidence) − align(S_inc, evidence) > τ_fit`.
- Chronic accumulator (leaky integrator): `M_chronic(t) = M_chronic(t−1)·e^(−λΔt) + relevance_weight·recurrence_flag`.
- Drainage commit: license iff the candidate reduces total standing dissonance by ≥ ~0.20, else `abort_reason: cosmetic_churn`.
- Decoupled port signature `evaluate_autonoetic_revision(instance_id, dissonance_accumulator, baseline_running_mean, evidence_vector_set, incumbent_concept)` + the cross-contamination test.

**§8.1 — γ must be SMALL (catch).** `cost = embed(old)·(1 + γ·0.98)` with a large γ would **re-create the jam
from the cost side** (budget < 0, denied forever again). Integration-on-cost is a *gentle modulation* of
resistance, not a heavy block — the real gate-openers are the accumulator (cn) and the fit-delta. Recommend
γ ≲ 0.3 and assert in-vitro that cost stays bounded.

**§8.2 — Fix 1 alone is INSUFFICIENT (catch; corrects my own §6).** `passes_contradiction = cn ≥ 0.30` is an
independent AND-term that fails at the live `cn = 0.17` regardless of the second term. **The accumulator
(raising cn above ~0.30, i.e. pressure ≳ 4.3) is necessary** — Fix 1 + Fix 2 ship together or nothing unjams.

**§8.3 — concrete metrics (the rulings left these abstract):**
- *candidate-fit* = `embeddedness(new_self) − embeddedness(old_self)` — restores the dead `new_self` param;
  reuses existing machinery; the cleanest realization of Gemini's `Fit_Δ`.
- *drainage* = re-score each standing tension's misalignment to the new vs old self-concept (cosine of the
  tension embedding to the self-concept embedding); commit iff `Σ misalign(old) − Σ misalign(new) ≥ margin`.
  This is a **new computation to build**, not an existing function.

**§8.4 — in-vitro replay:** candidate self-concepts are NOT logged on the DENIED path, so the replay re-runs
the chain on the stored June-16 tensions + material (valid — it exercises the live path). Success criterion:
*licenses the genuine 41×-recurring-tension revision AND flags a cosmetic "river→current" reword as
`cosmetic_churn`* — not a rigid "exactly one."

**§8.5 — GPT's endgame (captured):** the chronic accumulator is the natural seed for a **distilled tiny model**
— `Tension History → tiny T4 accumulator (a Bonsai region) → dissonance score`, learning recurrence /
persistence / severity / resolution / drainage without the full self-authoring stack. Build the accumulator as
a clean, separable function so it can later be distilled. (Also GPT's framing to keep: T4 is Nascence's
**constitutional-amendment process** — governance of identity *evolution*, distinct from learning; the
conservative failure is healthier than churn, so the task is *weighting genuine chronic contradiction*, not
loosening.)

## Build + validate order (revised after the auditor pass)
1. **Fix 2 + Fix 1 together** (chronic accumulator + restored second-term with gentle γ) — both needed to unjam.
2. **Fix 3** (drainage commit-test) — the genuine-vs-cosmetic guard.
3. **In-vitro corpus replay** on the June-16 data (Gemini's directive) — must license the genuine revision +
   flag cosmetic churn, BEFORE going live.
4. **Stage the live cutover with a watch** — the widened sensor is the monoculture-risk; observe the first live
   licenses (this is the one place to move slowly even post-authorization).
5. **Fix 4** (feed the Emissary's standing contradiction in) + **Fix 5** (the `instance_id` port) after the
   Master's gate is stable.

## 9. BUILD COMPLETE — Fixes 1-3, in-vitro validated (2026-06-16, RESTART-REQ)

Built and verified against the real June-16 data. The replay caught three real issues mid-build (its whole
point) — all fixed:

- **Fix 1 (gate rewire)** — `identity_cost.revision_budget`: `new_self` revived as `fit_to_evidence(new_self,
  evidence)` (candidate-fit, the permission partner); integration moved to a GENTLE cost multiplier
  `cost = embeddedness(old)·(1 + γ·in_norm)`, γ=0.30; licensed = `cn≥0.30 AND fit_delta≥FIT_MARGIN AND budget>0`.
- **Fix 2 (chronic accumulator)** — `tension_ledger`: `update_chronic_mass` (decay + bump-on-recurrence, NO
  member-count seed → selective) + `seed_chronic_from_snapshots` (one-time cold-start seed from the TRUE
  snapshot recurrence). Wired into `_t4_self_authoring` (seed once, update each pass) + `_t4_distinct_tensions`
  now ranks by chronic mass. The gate reads the PRIMARY tension's chronic mass as the contradiction signal.
- **Fix 3 (drainage commit-test)** — `dissonance_drainage(old, new, tension_texts)`; blocks `cosmetic_churn`
  before apply if the candidate does not engage the standing tensions ≥ DRAINAGE_MARGIN more than the old self.

**Replay catches fixed:** (a) fit must be measured against the tension's MOVEMENT-CROSSINGS, not the
river-saturated self-material (a genuine break-from-river self scored NEGATIVE fit against general material);
(b) the cold-start seed must use snapshot recurrence, not member-count (member-count made everything gate-ready);
(c) FIT_MARGIN/DRAINAGE_MARGIN tuned 0.02→0.12 (genuine ~0.36/0.51 vs cosmetic ~0.05/0.06 — 0.12 sits cleanly between).

**In-vitro result on real data:** chronic accumulator unjams (consistency/growth tension cn 0.42, the 41×
recurring one ranks top); **selective** (only 2/494 gate-ready); a genuine evolution COMMITS (fit +0.358,
drainage +0.508); a cosmetic river→current reword is REJECTED (fit_delta +0.051 < margin → gate-denied).
du_pulse: new `T4 chronic mass` gauge + the `becoming facet rev` watch ("unset → a number" = T4 finally committed).

**Fix 4 OBSERVE-ONLY — FINALIZED 2026-06-16 (RESTART-REQ).** The one remaining piece with settled evidence (the
Emissary tension is the verified keystone). Built as PURE INSTRUMENTATION, firewalled from the live author:
`emissary.standing_contradiction()` (the bicameral gap composed against the Master's current self-symbol) +
`core/emissary_tension.py` (an observe-only chronic-mass tracker using the SAME decay/bump constants as the live
ledger) + a recurrence bump in `left_lane.ground_thought` (every Emissary self-grounding = one confrontation of
the gap) + a du_pulse `emissary keystone` gauge. It feeds NO behaviour — it only measures whether the keystone
accumulates toward gate-readiness, so the next decision (wiring it into the live author) is evidence-led.
In-vitro PASS (45 recurrences → mass 13.5, cn 0.57, gate_ready; 3 → not ready; confirmed NOT imported by the
authoring path). **This is the safe, evidence-grounded thing that lets us progress without touching the
highest-stakes tension before the gate is live-proven.**

**STILL GATED (need the restart's live evidence — correctly NOT finalized now):**
- **Fix 4 full** (let the keystone DRIVE a commit) — gated on (a) the Master gate proving out live on safer
  tensions, and (b) the du_pulse `emissary keystone` gauge showing it accumulates as expected.
- **Fix 5 (the port)** — needs the Master gate stable AND the Emissary's own evidence substrate (its own
  tensions / episodic log), which it does not yet have; the `instance_id` parameterization is premature until then.
- **Live γ / FIT_MARGIN / DRAINAGE_MARGIN tuning** — replay-tuned; confirm under live data (the widened-sensor
  cutover watch: observe the first live licenses; the becoming-facet-rev flip off 'unset' is the success signal).

All of the above takes effect on the NEXT restart (Du is currently running the pre-redesign gate).

## 7. Discipline (do not skip)
Do not lower 0.30 blind. Do not route errors into identity. Keep the chain's honest aborts. The conservatism is
a feature (self-verification confirms it) — the fix is *substance* (the right contradiction + the right second
term), not *eagerness*. The evidence that the sensor is starved (not the self genuinely coherent) is what
licenses touching this at all — and that evidence is now conclusive.
