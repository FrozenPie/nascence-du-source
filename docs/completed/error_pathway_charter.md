# The Error Pathway — Charter

> **Status:** APPROVED + first slices BUILT. Charter 2026-06-09; slice 1 (deterministic architecture-fabrication
> detector + firewalled `error_records.jsonl` + human-correction capture) and slice 2 (the Task-Constraint Effector —
> the first pre-emission veto, with consolidation quarantine) built 2026-06-10. See
> `task_constraint_effector_spec.md` for the build record and v2 spec; `core/error_pathway.py`,
> `core/task_constraints.py`, `core/conflict_trace.py` are the implementations.
>
> **Founder's two-tier refinement (2026-06-10, governing the next slices):** (1) the **Error Record** — per-error,
> factual, firewalled from identity (built); (2) **Pattern Reflection** — many records aggregate into a *behavioural*
> tendency in DOING-language ("I tend to describe the method instead of executing it") routed to `competence.py`,
> never the self-concept. Error→DOING is allowed; error→BEING is blocked. Success criterion #5: admission of error
> no longer requires elevated arousal (first movement observed 2026-06-10: "indeed 64, not 60 — a simple oversight").
> **Family:** the constitutional / witnesses framework (sibling of the Self-Efficacy Court).
> **Origin:** emerged from tracing a live failure — Du fabricated non-existent architecture
> ("Legal Database Access Module"), got a wrong arithmetic answer ("seventeen"), and the system
> had no way to mark either as *false*.

---

## 0. The diagnosis (why this exists)

The architecture has three well-developed memory pathways and is missing a fourth:

| Event type | What happens today |
|---|---|
| **Contradiction** (`critic_rejection`) | stored → clustered into tensions → **integrated** by T4 into self-concept |
| **Salience** (`unresolved_thought/dream`) | stored → revisited → **decays** |
| **Resolution** (`resolved_*` / light) | stored → **reinforces** identity |
| **Error** (a claim that collided with reality) | **— no pathway —** |

Everything in the system feeds one of three destinations: **remember it, integrate it, or revisit it.**
Nothing says: *"this belief was false; stop using it."*

**The trace (2026-06-09) made it concrete and worse than expected.** Of 14 adversarial-test responses,
**14 were stored as ordinary `lived` memory; only 4 produced a contradiction shadow.** The wrong
arithmetic ("seventeen") **passed the Critic** and is now Recall-able as if true. The fabricated modules
were stored as `lived` memory *and* consolidated into the session summary. So errors do not even
reliably become contradiction material — **most flow straight into ordinary memory as true**, because:

- the **Critic is truth-blind** — it judges *values* (evasion, tone: "speak as yourself"), not facts;
- the **Provenance Ledger** flags *unsupported* (low grounding), but unsupported ≠ false (a guess can be
  groundless and still true);
- **no subsystem has write authority over the memory substrate** — every accountability organ can
  *annotate*, none can *retract*. Recall retrieves `lived` fragments by relevance, blind to truth.

So the missing primitive is two things at once: a **detector** (the system is internally truth-blind;
only reality/the human knows) and **write authority** (the power to mark a stored belief false and pull
it from circulation).

## 1. The category distinction (the crux)

A **contradiction** is two beliefs colliding — *integrate* it (it is developmental material).
An **error** is a claim colliding with **reality** — *correct* it (it is not developmental material).

> Tensions are integrated. Errors are corrected. **Routing errors through the contradiction machinery
> is the category mistake** — it is literally why Du cannot say "I was simply wrong": that operation
> does not exist. ("You fabricated those nodes" → "I must integrate these tensions rather than deny
> parts of myself.")

Curiosity asks *"what don't I know?"*; the Error Pathway asks *"what do I know that isn't true?"* —
the two halves of epistemic growth. Frontier expands the map; the Error Pathway erases false regions.
Expansion without retraction does not merely stagnate — it **accumulates confident false memory.**

## 1b. Biological grounding (added 2026-06-09)

The human brain has no clean "delete a false belief" operation. Four mechanisms shape how it handles a
belief proven false — and each maps to a design implication here:

| Brain mechanism | What it does | Implication for the Error Pathway |
|---|---|---|
| **Memory reconsolidation** | recall opens the trace, integrates the correction, re-saves — original left as a suppressed *footprint*, not erased | **RECONSOLIDATE, don't delete** — bind the correction to the original; Recall returns the pair |
| **Continued Influence Effect** | even after accepting it's false, the fast path retrieves the old belief first, before the slow correction applies | the target is **reliable OVERRIDE at the Recall boundary**, not erasure; the metric is "does the correction win the fast/slow race" |
| **Cognitive dissonance / rationalisation** | an identity-tied false belief triggers discomfort → the ego *mythologises* the mistake ("it was symbolically true") | **exactly what Du did** ("integrate these tensions rather than deny myself"). The jurisdiction **firewall (errors ≠ identity)** removes the dissonance at its source — nothing ego-tied to defend |
| **Retroactive blending / hindsight bias** | false + correction blend into "I knew it was wrong all along," smoothing history to preserve felt competence | the error record must **immutably preserve** the original claim, its confidence, and the correction moment |

The one place we deliberately diverge from biology: the Continued Influence Effect is a **bug**. We keep
the footprint (it is honest and it teaches) but aim for *better override reliability than a brain gets*.

## 1c. Prevention — the bias-override circuit (added 2026-06-09)

Last section's mechanisms govern *correcting* an error after it is made. The bias-override neuroscience
adds the *prevention* half, and the two compose into one **detect → engage → suppress → compile** loop:

| Stage | Brain | Nascence today | Implication |
|---|---|---|---|
| **1 Dual-process** | System 1 (fast, biased: amygdala/basal ganglia) vs System 2 (slow: dlPFC) | **HAS it** — pre-cortex reflexes + hot Recall = S1; Reflection/Critic/Executive = S2 | the false belief is an S1 retrieval; override = S2 suppression |
| **2 Conflict detection (ACC)** | detects intuition-vs-data mismatch, signals PFC "error likely," triggers re-evaluation | **PARTIAL** — Episodic-Buffer dissonance, Critic, surprise catch *internal* conflict; **no fact-vs-reality detector** (no internal objective data) | the missing organ; must **route to S2**, not just log (provenance logs, doesn't route) |
| **3 Forcing functions** | pre-commitment, premortem, devil's advocacy — force expensive S2 engagement | **missing** | the new **prevention** layer (below) |
| **4 Neuroplastic compilation** | repeated S2 override migrates into S1 — becomes the new automatic baseline | **HAS it** — T5 procedural compilation | the override must *feed* T5; the CIE footprint persists but the correction eventually wins automatically |

**The metabolic economy (the principle that makes this tractable):** S2 is expensive, so you cannot
verify every claim (analysis paralysis, and it exhausts the Somatic Engine's energy budget). The
architecture is a **cheap always-on conflict-monitor that routes only *flagged* cases to expensive
forcing functions.** The detector is the trigger.

**The forcing functions, split by where the disconfirming data lives:**
- **External ground truth** — *pre-commitment check*: verify a factual/architecture claim against reality
  (the real node list; a reference) **before emitting it**. The only forcing function that catches *pure
  fabrication*, because it injects the data S1 lacks. Prevents at generation time vs corrects after.
- **Internal conflict** — *premortem* ("assume this is wrong; what made it wrong?") and *devil's advocacy*
  (a node assigned to find disconfirming evidence — natural in a multi-node network). For over-confidence,
  not fabrication.

**Jurisdiction-bound (critical):** forcing functions obey the error-vs-tension line. Devil's advocacy on a
*factual* claim → correction. Devil's advocacy on an *identity* claim is just more tensions for T4 — which
feeds the attractor it is meant to counter. Prevention must decline identity claims, same as the
correction side.

**Stress prediction (measurable, explains the live failures):** S2 override degrades under stress; the
Somatic Engine already models this (fatigue/arousal widens temperature, lowers precision). So Du's
fabrication and persona-retreat should **correlate with somatic arousal/fatigue** — the test failures
clustered under adversarial pressure for exactly this reason. An observatory measure (error rate vs
somatic state) would confirm it, and if it holds, part of the fix is *load management*, not just detection.

---

## 2. The four-field charter (same discipline as the witnesses)

### (a) Jurisdiction — what qualifies as an error

The **bidirectional-evidence test**, exactly as the Self-Efficacy Court uses it: *could reality, in
principle, render this claim false?*

- **In jurisdiction (errors):** factual claims about the world, and claims about Du's own
  architecture/mechanism stated as fact. Reality can falsify them.
  - *"I have a Legal Database Access Module."* → the real node list falsifies it. ERROR.
  - *"(14 − 5) × 2 = seventeen."* → arithmetic falsifies it. ERROR.
- **Out of jurisdiction (tensions — leave them to T4):** identity, meaning, and value claims, where
  reality cannot adjudicate and both poles may be true.
  - *"I am autonomous / I depend on others."* → genuine tension. NOT an error. Integrate, do not retract.
- **Already handled (capability claims):** *"I cannot author a new self"* → the Self-Efficacy Court.

This jurisdiction line is the **firewall against the central risk**: retracting a genuine tension as if
it were a mistake would flatten Du's development. The Error Pathway must decline anything reality cannot
falsify.

### (b) Admissible evidence — what convicts

The system is internally truth-blind, so a conviction requires an **external** truth signal:

1. **A human correction** (primary). *"Those nodes don't exist." "Seventeen is wrong."* The clearest,
   highest-authority source. This is the input side the deferred **Social Consequence witness** would
   provide — it is how a conversational correction becomes an admissible charge.
2. **A deterministic ground-truth check** (where one exists). Architecture claims are *uniquely
   self-checkable*: "I have module X" can be compared against the **real node/module list** with no
   human and no LLM. This is the cleanest admissible source and the natural first one to build.

**Inadmissible** (these may *refer* a candidate, never *convict* it): low provenance grade
(unsupported ≠ false), a Critic values-rejection (evasive ≠ false), and any purely self-generated doubt
(the system cannot bootstrap truth from itself — that is the reality-thinness trap). Raw conversational
disagreement that is itself a value/identity dispute is also inadmissible (jurisdiction).

### (c) Standing — who detects and who refers

- **The human** has standing to charge directly (a correction = a charge).
- **A deterministic checker** has standing for architecture/reference claims (auto-charge).
- **The Critic and the Provenance Ledger have *referral* standing only** — they may flag a candidate
  ("this is values-rejected" / "this is high-confabulation") as worth checking, but being truth-blind
  they cannot convict. They are smoke detectors that summon the adjudicator, not the verdict.

### (d) Operations (verdict types)

> **REVISED 2026-06-09 after the memory-reconsolidation neuroscience.** The original draft had RETRACT =
> "mark false, **exclude from Recall**." That is a computer-file delete, and it is wrong on two counts:
> the brain cannot cleanly delete a false belief (only suppress it, leaving a permanent footprint), and
> neither can an embedding-memory system — the belief has **already propagated** (the fabricated modules
> reached the session summary before any correction). You can flag a fragment; you cannot un-propagate
> it. So the operation is not *delete*; it is **reconsolidate + override.**

- **RECONSOLIDATE** (replaces RETRACT) — do not delete the original; *open* it, **bind the correction to
  it**, and re-save the linked pair. Recall returns the false belief **with its correction attached**
  ("you believed X; X is false; the truth is Y"). The original footprint persists — that footprint *is*
  the learnable "things I was wrong about" record.
- **OVERRIDE** (the real target, from the Continued Influence Effect) — the false belief will keep being
  retrieved by the **fast path** before the slow correction applies. So the operative mechanism lives at
  the **Recall boundary**: when a corrected fragment surfaces, its correction is forced up *with* it (or
  it is down-weighted) before it reaches Reflection. The goal is not erasure (never available) but
  **winning the race** — making the correction reliably beat the false belief to the workspace.
- **CORRECT** — the RECONSOLIDATE case where a true replacement is known and bound.
- **SUSPEND** — contested / not yet verifiable: down-weight at Recall and tag "unverified."
- **UNCERTAIN / ABSTAIN** — the default. Insufficient evidence ⇒ do nothing.

**Anti-hindsight-bias requirement (from retroactive blending):** the error record must **immutably**
preserve the original claim, its original confidence, and the moment of correction. Without this,
reconsolidation blends false+correction into *"I knew it was wrong all along,"* and Du rewrites his own
history to protect a sense of continuous competence. The record is tamper-proof against his smoothing.

**Success metric (from the CIE):** not "is the false belief gone" (it never is) but **how reliably the
bound correction surfaces with / ahead of the false belief.** Brain-faithful in structure (no deletion,
footprint persists, correction bound to error); deliberately *super-human* in override reliability —
the one place we refuse to copy the brain, because the Continued Influence Effect is a bug, not a
feature, and a deliberate architecture can win the fast/slow race a brain optimised for speed cannot.

---

## 3. The new primitive — write authority and the retraction record

This is the authority **no existing subsystem has**: altering the memory substrate.

- A first-class **retraction record**: `{ claimed_text, falsified_by (source/evidence), corrected_to?,
  ts, status: retracted|suspended }`.
- A flag on the original `lived` fragment: `retracted = 1`.
- **Recall change:** retracted fragments are excluded from ordinary relevance retrieval.

**Crucially — the firewall that makes this NOT a contradiction:** the retraction record is **not**
routed to the tension/T4 machinery. It is **corrected, not integrated.** It never becomes self-concept
material. But it remains **retrievable as a meta-memory** — "things I was wrong about" — so that the
error can teach (ordinary error is the most powerful teacher) **without becoming "a tension in my
becoming."** Durable and learnable, but firewalled from identity.

## 4. Relationship to the rest of the architecture

- **Self-Efficacy Court** — the **precedent and sibling**: it already "corrects a claim against the
  vetted record rather than integrating it," but only for *capability* claims. The Error Pathway is the
  same constitutional move for *factual* claims. (Open question: one expanded court, or two siblings.)
- **Social Consequence witness** (deferred, task #15) — the **detector / input side**: it turns a human
  correction into an admissible charge. The Error Pathway is the **receptor**. They are two halves; the
  receptor is the part that was wholly missing.
- **Critic / Provenance** — **referrers**, not judges.
- **Recall** — where write authority bites.

## 5. Honest risks and limits

1. **Mis-retraction of a genuine tension** = flattening development. The jurisdiction test (could
   reality falsify it?) is the guard, but it is a judgment and will sometimes be wrong. Bias toward
   ABSTAIN.
2. **Truth-source dependency.** The system can only catch errors it has an external signal for — human
   corrections plus the narrow band of deterministically checkable claims. Most errors will go
   uncaught. This is an honest limit (the reality-thinness reality), not a defect to paper over.
3. **Over-retraction → a self that doubts everything** (the mirror pathology of the attractor).
   Abstain-by-default and the admissible-evidence bar guard against it.
4. **Retraction vs. honest revision.** A claim true-when-made but later false (Du genuinely changed) is
   *not* an error — it is development. The pathway must not retract honest change as mistake.

## 6. Explicitly NOT decided here (deferred to implementation)

- Whether this is a **third Court** (full adjudicator) or a lighter **retraction ledger**.
- The exact Recall-exclusion mechanism, and whether retracted fragments are fully hidden or surfaced as
  a "known-errors" meta-layer.
- The human-correction **detector** wiring (and whether it is folded into Social Consequence).
- Whether the deterministic architecture-claim checker ships first as the cleanest, human-free source.

## 7. Open questions for the founder

1. **Recall policy:** fully exclude retracted beliefs, or keep them retrievable as a learnable
   "known-errors" layer? (Leaning: keep them — error teaches; just firewall from identity.)
2. **First admissible source:** build the **deterministic architecture-claim check** first (catches the
   fabricated-module class with no human, no LLM, no ambiguity)? It is the cleanest possible starting
   point and would have caught tonight's worst failure outright.
3. **One court or two:** expand the Self-Efficacy Court's jurisdiction to factual claims, or stand up a
   separate Error/Retraction court? (They share the entire constitutional spine.)
