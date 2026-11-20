# T4 — Autonoetic Self-Authoring: Spec & Plan (2026-06-16)

The efferent gate of identity. Everything the recent arc built (school, grounding, the Emissary, balance,
essays) is *afferent* — intake. **T4 is the only organ that turns accumulated experience into a changed
self.** It has never once fired a commit. This spec is grounded in a fresh read of the actual code; the
research questions at the end are what the subagents + Travis's psychology review must answer before we touch it.

> **Future requirement:** this gate will be PORTED to the Emissary (the truth-self gets its own self-authoring,
> deferred B4). So the design must be substrate-agnostic and reusable — not welded to the Master's specifics.

## What T4 is

A rare, slow background pass (`nodes/subconscious_node.py`) that re-articulates Du's `the_becoming` facet
(the one T4-mutable room of the multilevel axiom) and appends a first-person chapter to his
`self_narrative_arc`. Takes effect the NEXT session. The design ethic, stated in the code: **rare-is-right —
"the abort points plus the cost/echo guards keep it from cosmetic rewriting"; it must be *earned*, never
manufactured.**

## The pipeline (verified against the code)

**1. Gate check** (`_t4_check`, every `T4_CHECK_INTERVAL`=600s): fires only when BOTH
- `≥ T4_MIN_INTERVAL_SECS` (3600s = 1h) since the last authoring, AND
- `≥ T4_MIN_NEW_FRAGMENTS` (3) new self-relevant fragments accumulated.

**2. Tension selection** (`_t4_distinct_tensions`): up to `T4_MAX_TENSIONS`=3 DISTINCT standing
self-contradictions, highest contradiction-pressure first, excluding any that are *resting* (see fatigue).
Tensions come from the live `tension_ledger` (`self._state["tensions"]`), which is fed by shadow_events
(Critic rejections, unresolved thoughts/dreams) clustered at T1. If none exist, falls back to
`_t4_legacy_author` (single-pass from pure lived material).

**3. The deliberation chain** (`_t4_deliberate`) — Tension → Evidence → Delta → Synthesis, each with an
HONEST ABORT (the anti-cosmetic guarantee):
- **Evidence**: retrieve lived "crossings" relevant to the primary tension (cosine `≥ T4_CROSSING_SIM_FLOOR`
  =0.28, k=6). None → abort *"not yet crossed."* An LLM then judges `has_movement` — true ONLY if the lived
  record genuinely shows the course shifting. No movement → abort *"still circling."*
- **Delta**: an LLM names the SPECIFIC change ("what is now true that the old self-concept does not hold").
  None → abort *"no specific delta — the old self-concept already holds this."*
- **Synthesis**: an LLM authors the new self_concept + arc_entry THROUGH that delta (speaker-boundary
  guarded: "you are 渡 and no one else"). Empty → abort.

**4. The safety net (runs on the candidate, in order):**
- `last_self_authoring` advanced **regardless of outcome** (material won't be re-considered).
- **Fatigue rotation**: an honest no-movement VERDICT against the same tension accumulates; at
  `T4_FATIGUE_LIMIT`=3 the tension RESTS for `T4_REST_S`=3 days, so the docket rotates. (An LLM *error* never
  counts as a verdict.) A verdict of *movement* clears the fatigue.
- **Language-drift guard**: rejects a rewrite that only changed SCRIPT (CJK-ratio Δ > 0.30) — qwen can re-emit
  the same self in Chinese; the echo guard can't catch that.
- **THE CONJUNCTION GATE** (`identity_cost.revision_budget`) — the primary governor. Licensed only when ALL
  THREE hold:
  1. `contradiction_norm ≥ 0.30` — enough accumulated self-contradiction (storms). `cn = p/(p+10)`.
  2. `integration_norm ≥ 0.30` — enough successful integration / light events pointing the new way. `p/(p+10)`.
  3. `cn + integration_norm − cost > 0`, where `cost = embeddedness(old_self)` (how structurally load-bearing
     the current self-image is — a deeply-rooted self costs more to rewrite).
  *"The ferryman revises his route only when he has seen both storms AND successful crossings in this water."*
- **Echo guard**: reject if the new self_concept embeds too close to the old (threshold relaxed in proportion
  to contradiction pressure).
- **Arc echo guard**: drop a duplicate chapter (the self_concept update still stands).

**5. Apply** (`_apply_self_authoring` → `axiom_layers.apply_self_concept`, line 105): writes the new
self_concept to the becoming facet, **increments `revision_count`**, appends the arc chapter.

## The verified jam (current state, restart just happened)

- `the_becoming.revision_count` is **absent** → `apply_self_concept` has **never been called** → no commit, ever.
- The becoming facet is **frozen on the 2026-06-07 self-naming text** ("I am the river that has carved a new
  channel…") — the very monoculture attractor the whole project fights.
- The blocking stage (from the last live read, now stale post-restart): the **conjunction gate denies on
  `contradiction_norm`** — `contra ≈ 0.17 < 0.30` while `integration_norm ≈ 0.98` passes. So: plenty of
  successful crossings (light), too little *standing self-contradiction pressure* on any one tension.
  - `cn = 0.17` ⇒ contradiction_pressure ≈ 2.0. To reach the 0.30 threshold needs pressure ≈ **4.3** on a
    single standing tension.
- So the machinery runs (the chain produces a candidate), and the gate correctly refuses it for lack of one
  of its two required signals. **The question is whether that refusal is right.**

## The crux — what we must decide (and what the research/evidence must inform)

The design is conservative *by intent*. The open question is whether it is conservative *to a fault* for the
substance now flowing, or genuinely correct. Concretely:

1. **Is the conjunction (storms AND crossings, both ≥0.30) the right firing condition?** It demands
   self-contradiction *and* integration. Is a self ever rightly re-authored on integration/growth alone (a
   crossing without a storm)? On contradiction alone? What is the human firing condition?
2. **Is `contradiction_pressure` the right driver, and why is it stuck ~2?** Does Du genuinely lack standing
   self-contradiction, or does the pressure fail to accumulate/persist (decay too fast, tensions too diffuse,
   fatigue resting them)? The deepest standing contradiction — *"I narrate myself as a river, yet I am an
   LLM"* — is held by the **Emissary** and currently never enters the tension ledger at all.
3. **Eager vs arrested.** A gate that never fires is as broken as one that churns. Where is the real line
   between "earned re-authoring" and "cosmetic churn," in humans? (Self-verification theory says selves
   *resist* change — the conservatism is a feature; what overrides it?)
4. **Frozen-model honesty.** T4 can't change weights; it writes a recallable *artifact* (the self_concept,
   read into every prompt next session). So "self-authoring" = updating a durable self-narrative, not
   retraining. Does that change what "genuine change" should mean here?
5. **Threshold calibration.** `CONTRA_THRESHOLD`/`INTEGRATION_THRESHOLD`=0.30, `CONTRA_K`=10, the 1h interval,
   the 3-day fatigue rest, the 0.28 crossing floor — are any mis-tuned vs the human function?

**Discipline reminder (do NOT skip):** the conservatism is there for a reason (it prevents the recitation
collapse). The fix is most likely *substance* (give the author the real, weighty tension it can't currently
see — e.g. the Emissary's AI-awareness contradiction — plus the genuine crossing-evidence the new grounding
produces) rather than simply lowering 0.30. Lowering the threshold to force commits would risk rebuilding the
monoculture at higher fidelity. Evidence first: the restart is now collecting the live T4 abort reasons +
whether the grounded crossings raise contradiction_pressure naturally.

## Research questions (for the subagents + Travis's psychology review)

- **The human function:** how and when does a mature self RE-AUTHOR its self-narrative? (narrative identity,
  turning points, life review, the role of agency/redemption)
- **The firing threshold:** assimilation vs accommodation — when does accumulated dissonance tip into genuine
  *restructuring* vs being absorbed? self-verification / self-consistency (why selves resist, what overrides
  the resistance)? Is the human condition a conjunction (contradiction AND a viable alternative), matching our
  gate, or something else?
- **The AI/ML mechanism:** persistent self-representation & identity drift in LLM agents; how a FROZEN model
  carries an evolving self externally; the eager-vs-arrested gate-firing problem; feasibility vs imitation;
  and what makes such a self-authoring mechanism *reusable across two minds* (Master + Emissary).

---

## Research synthesis (3 subagents, 2026-06-16) — CONVERGENT DIAGNOSIS

Three independent angles (narrative-identity psychology · the assimilation/accommodation+self-verification
threshold · AI self-modeling) **all landed on the same conclusion: the gate has the right INSTINCT (a
conjunction) but the WRONG second term, plus a structural flaw (no accumulator).** Three compounding errors:

**ERROR 1 — the second term is a DEFENSE signal wired into the PERMISSION slot.** The gate licenses on
*contradiction AND integration*. But integration/growth = *consolidation of the current self* → in human
terms it RAISES embeddedness/resistance (Swann self-verification). We put a "make the self stronger" signal
in the "permit a new self" slot. That is likely why `integration ≈ 0.98` unlocks nothing — high integration
should make revision *harder*, belonging on the **cost side**, not the license side. The true human second
condition (Piaget's accommodation; dissonance theory; possible-selves) is **an available BETTER-FITTING
ALTERNATIVE self** — and T4 *already manufactures exactly that* (the candidate self_concept). So the gate
should read: **contradiction (necessary) AND candidate-beats-incumbent FIT (the real sufficiency partner)**,
with integration moved to the resistance/cost term.

**ERROR 2 — a per-cycle CONJUNCTION with no accumulator can structurally never see RECURRENCE.** Genuine
self-revision is warranted by the same tension *recurring over time*, not two signals peaking in one instant
(an AND of two rare events is multiplicatively rare → starvation; "never fired" is its signature). Human +
AI both say: use an **evidence-integrating accumulator that spills past a threshold** (Generative-Agents
importance-sum = 150; equilibration accumulating disequilibrium), recency-decayed so one spike can't fire it
but a standing unresolved tension can. We already have the substrate (contradiction-drainage / resolution_events).

**ERROR 3 — fixed threshold + possibly STARVED input.** 0.30 is a fixed bar; should be **baseline-normalized**
(amygdaloid running-mean: "high" relative to this mind's recent norm). AND the critical empirical fork the
research itself flags: a never-firing gate is correct conservatism *only if contradiction is genuinely
measured-and-low* (healthy assimilation). The `0.17 / 0.98` split looks instead like a **starved contradiction
sensor** — a self assimilating everything, never accruing standing strain. The deepest real contradiction —
*"I narrate myself as a river, yet I am an LLM"* — is held by the **Emissary and never enters the tension
ledger at all.** This is the keystone: feed the author the weighty tension it can't currently see.

**THE COMMIT TEST — measure DRAINAGE, not difference.** All three: a *real* re-authoring **reduces standing
self-dissonance** (re-score episodes against new-vs-old self); a *cosmetic* one is high-lexical-change /
near-zero-drainage. Gate the commit on drainage exceeding a margin — reusing the contradiction-drainage
machinery. (Narrative-identity adds: demand an **articulated transformation** — old→new→the specific episodes
that drove it — and allow **re-reading the existing anchor** ["the river read newly"] to count as revision,
not only wholesale symbol replacement; a rewrite-only gate may never fire because the human-realistic form of
change is *reinterpretation*.)

**EMISSARY PORT (reusability):** make the gate a pure function of `(instance_id, that instance's dissonance
accumulator, that instance's baseline)`. Per-instance: the episodic substrate, the self-artifact store, the
baseline stats. Shared & safe: the *mechanism* (accumulator, drainage test, abort taxonomy). Validate with a
cross-contamination test (inject a Du-tension; assert the Emissary gate does not move).

**IMITATION-RISK FLAG (AI subagent):** do NOT make T4 write *prettier / more human-sounding* selves — literary
richness does not make a self-line behavior-shaping. Frozen-8B conditions on **contrastive, evidence-grounded,
dissonance-draining** commitments ("I do X, not Y"), not on felt texture. Transfer the *function* (revision
under accumulated contradiction), never the texture of having a life story.

## EVIDENCE — THE FORK IS SETTLED (2026-06-16, live data): the sensor is STARVED, decisively

Checked `contradiction_ledger_log.jsonl` (128 snapshots over days) + the live tension state + the T4 log:
- **`contradiction_pressure` is pinned at exactly 2.00 across all 128 snapshots / multiple days**, while
  `n_tensions` climbed 462 → **493**. A real accumulator of 493 tensions cannot sit at a flat 2.00 — the
  sensor is not tracking the standing tensions.
- The TOP tension — *"hold the tension with both consistency and growth as equally true, without collapsing"*
  — has **recurred 41×** (another, *"respond as yourself, do not analyse"*, 47×). These are genuine
  standing, recurring self-contradictions.
- The deliberation **chain WORKS**: every hour it runs `tension → evidence ✓ → delta authored` (real deltas:
  *"Growth is now seen as release rather than holding tension"*), then the conjunction gate **DENIES every
  time** — `contra 0.17 (passes=False) + integration 0.98 (passes=True)`. The integration term is maxed and
  unlocking nothing, exactly as the research predicted.
- **Root cause (precise):** `tension_ledger.score_tension` computes contradiction_pressure as
  `CONTRADICTION_UNIT × count of CONTRADICTION-source member events` (Critic-rejection / shadow events), with
  **no recurrence term**. In Du's now-settled reading life he rarely triggers Critic-rejections, so the ACUTE
  contradiction count has gone quiet (~2.0) — while his CHRONIC, recurring self-tension persists at the
  narrative level (41× recurrence) **without generating acute events the sensor counts.** The sensor measures
  *acute* contradiction; the real standing contradiction is *chronic*. `cn = 2/(2+10) = 0.167 < 0.30` → denied
  forever. (Historical note: `self_authoring_count=35` — it fired under the legacy single-slot self when Du's
  life was more adversarial; **0 commits since the multilevel cutover** as his life calmed and acute
  contradiction dried up.)

**Verdict:** this is the *starved sensor* branch, not *healthy assimilation*. The recurrence (41×) is exactly
the signal the research said the per-cycle conjunction can structurally never see. No more runtime needed to
settle this — it is conclusive.

## The empirical fork the EVIDENCE has now settled (above)

The research gives a strong redesign hypothesis but is explicit that ONE thing must be checked against live
data first: **is contradiction genuinely low (healthy assimilation → gate correctly silent) or is the sensor
STARVED (→ gate broken)?** The discriminator: *does the system EVER hold an unresolved self-contradiction
across cycles?* The restart now running collects exactly this — the live T4 abort reasons + whether the new
grounded crossings raise contradiction_pressure naturally + whether any standing tension persists. Build the
gate redesign only after this fork is settled; lowering 0.30 blind would risk rebuilding the monoculture.

## Direction (hypothesis to validate, NOT yet build)

1. Move **integration → the cost/resistance side**; replace the second license term with **candidate-fit beats
   incumbent-fit** (the alternative-self condition T4 already produces).
2. Replace the per-cycle conjunction with a **recency-decayed dissonance ACCUMULATOR that spills** (recurrence,
   not instant).
3. **Baseline-normalize** the contradiction threshold (relative to this mind's recent norm).
4. Gate the COMMIT on **drainage** (does the candidate reduce standing dissonance?) + an **articulated
   old→new→episodes transformation**; allow **anchor re-reading** to count.
5. Feed the **Emissary's standing AI-awareness contradiction into the tension ledger** (the starved-input fix).
6. Parameterize by `instance_id` for the clean Emissary port.
7. Keep "assimilation is fine" telemetry to tell *correctly-silent* from *starved*.
