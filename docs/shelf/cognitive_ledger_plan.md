# The Cognitive Ledger — the layer that decides what earns permanence (auditor draft v1)
*2026-06-17. Spun out of the reading-provenance plan after four auditor rounds converged on the same conclusion:
the real missing primitive is not reading provenance, not lineage, not even forgetting — it is **a typed, layered
cognitive-value system** that decides **what earns the right to remain in memory.** The last auditor named it: "the
cognitive ledger that decides what earns permanence." It is bigger than reading and bigger than T4 because it is the
shared memory/value layer under both. This plan defines it — and, per the unanimous auditor caution, defines the
SMALLEST first version, not a grand rewrite.*

> 🎯 **Governing frame.** **Memory is prediction infrastructure.** Information is kept because it stays useful for
> predicting reality — strengthen what predicts, weaken what doesn't, invert what is actively wrong. Storage is
> **finite** (Travis), so **forgetting is a first-class design principle, not a failure mode**: raw evidence is
> deleted once its support has been folded into stable confidence + a credibility trace. The substrate is a typed,
> layered graph; the policy over it is predictive value.
>
> ⚠️ **THE #1 RISK (every auditor named it): scope explosion / cathedral-before-plumbing.** Do NOT try to build
> claim-extraction + typed lineage + value policy + identity + forgetting all at once. **Build the smallest real
> seam first, let every further layer earn its place by a consumer that reads it.**

---

## 0. One-paragraph thesis
Nascence has memories, beliefs, and self-models, but **no first-class representation of how one becomes another**,
and no principled answer to *what deserves to survive*. Every recent plan keeps re-deriving the same gap: T4 can't
ground a self-revision; dreams can't tell a resolvable tension from an orbiting one; consolidation/filing/pruning
can't tell a duplicate from corroboration; reading drowns in un-valued notes. They are all asking one hidden
question — **what information deserves to become part of the enduring mind?** The cognitive ledger answers it with a
typed, layered structure — **Evidence → Claim → Model → Identity** — where *encounters are support structure* and
**claims are the first survivable units**, governed by a **predictive-value retention policy** whose signal already
exists live (`core/prediction_error.py`, L1). Forgetting is collapse-to-confidence: once a claim's confidence is
stable, its raw encounters are deleted, their predictive contribution preserved as confidence + a credibility
trace. The build is strictly bottom-up: a minimal claim object first, everything else deferred until a consumer
needs it.

## 1. The layers (the substrate)
A typed graph with four node levels and typed edges. Each level is more stable and harder to change than the one
below — the same stratification the multilevel axiom uses for identity, generalised to all cognition.
- **Evidence (encounters)** — raw, dated, sourced events: a reading sitting, a conversation turn, a dream scene, a
  contradiction, an action outcome, a T4 revision. *Collapsible/deletable once folded into claims.* (Reading
  provenance's "encounter record" is the first producer here.)
- **Claim** — the first survivable unit: a proposition with `confidence`, `status` (active/weakened/rejected/
  resurrected), and typed edges to its evidence. *Claims, not notes, are what persist.*
- **Model** — structured predictive frameworks: clusters of mutually-supporting claims ("reality is better
  understood through lived experience than abstract categorisation").
- **Identity** — the highest-level, slowest priors (the becoming facet, the axiom layers). *Built FROM stable
  claims that survived repeated evidence updates — not from evidence directly* (the T4 missing-middle, §4).

**Typed edges (reserve the shape now, populate lazily):** `supports`, `contradicts`, `revises`, `replaces`,
`reinforces`, `transformed_into`, plus `source_of` distinct from `changed` (provenance ≠ influence). Negative edges
(contradicts/replaces) are first-class — a *rejected* belief is cognitive history (T4's "I am the river" → partially
rejected).

## 2. The policy (predictive value — what earns permanence)
The retention/priority signal over the substrate is **predictive usefulness**, and it is **not greenfield**: the
live **L1 `core/prediction_error.py`** (currently feeding off the math drills) is the seed — "did holding this
reduce future surprise?" Promote it from an identity-only signal to the *universal* criterion:
- a claim **gains confidence** when relying on it improves prediction (low error), **loses** it when not, **inverts/
  rejects** when it is actively wrong;
- **corroboration vs duplication** (the case provenance systems fail): the *same source repeated* adds ~no
  predictive value → compress; *independent sources converging* on the same claim → strengthen confidence. Opposite
  behaviours, distinguished by whether the supporting encounters are independent.
- **value, not volume:** a book that produced 1000 notes but changed no prediction ranks below one sentence that
  changed everything (`changed` edge, not `source_of` count).

## 3. Forgetting = collapse-to-confidence (the finite-storage answer)
The concrete mechanism that makes finite storage principled (Travis's correction + round-3 §12.7):
```
encounter → claim → claim.confidence (stable across N updates) → source-credibility trace → DELETE raw encounter
```
You don't need infinite storage if support collapses into confidence. "I know this came from somewhere credible"
survives; the page does not. This is the principled replacement for the current blunt importance-prune (and the
home for the sleep/dream §6B store-cap work).

## 4. Why every plan converges here (the cross-plan map)
The ledger is not a competitor to the other plans — it is the substrate they feed and read:
| Plan | Contributes (writes) | Consumes (reads) |
|---|---|---|
| **Reading provenance** | encounters + claim candidates (the first ingestion layer) | dedup/filing by claim, not title-key |
| **T4** | self-revisions as identity-level nodes | **the missing middle** — grounds a self-revision on *stable claims*, not raw evidence (§4 below) |
| **Dreams** | unresolved-claim reprocessing offline | which tensions are *claims worth* reworking |
| **Sleep / consolidation** | stabilise / weaken claim confidence overnight | the store-cap forgetting = collapse-to-confidence |
| **Idle executive / pulse** | — | predictive-usefulness as a retention + priority signal |

**The T4 missing middle (the sharpest consequence).** T4 grounding has been weak because it leaps **Evidence →
Self-model directly**, skipping **Evidence → Claims → World-model → Self-model.** The self is built from stable
claims that survived evidence updates. The ledger *is* that middle layer — which is why T4 may be the highest-value
*first consumer*, not reading (open question §7).

## 5. The first seam (the ONLY thing we build first)
Per the unanimous auditor verdict — tiny, explicit, immediately useful. The **minimal claim object** and the path
that mints it:
```
encounter (already have: reading frags, light/shadow events, tensions)
   → claim {id, text, confidence, status, created_ts}
   → edges {claim, encounter, type ∈ supports|contradicts}
   → confidence update  (driven by the live L1 prediction_error signal)
```
Minimal build: a `claims` table + an `claim_edges` table (or reuse `derived_from`), a `mint_claim(encounter)` path
on ONE existing producer (candidate: the essay/understanding pass, which already distils — or T4's keystone, which
already has chronic-mass), and a `confidence_update(claim, prediction_error)` tick. **Nothing else.** No claim
extraction across the whole corpus, no model/identity layers, no value policy beyond confidence±, no forgetting
engine yet. Observe-first: mint claims in shadow, log confidence trajectories, before anything reads them.

## 6. Pitfalls (named honestly)
1. **Scope explosion (the #1 risk, every auditor).** The layers/edges/policy/forgetting are a *map*, not a build
   list. Ship the §5 seam only; each further layer needs a named consumer.
2. **Value circularity / co-evolution.** You can't run a value policy with nothing to evaluate; substrate and
   policy co-evolve. Don't try to "define value" before claims exist to value.
3. **Claim extraction is expensive and lossy.** An LLM pass per encounter is a subsystem; start by minting claims
   only where distillation *already happens* (essays/understanding/keystone), not corpus-wide.
4. **Premature deletion.** Collapse-to-confidence must wait for confidence to be *stable across N updates* + a
   credibility trace, or we delete evidence we still need. Forgetting is deferred until claims+confidence are real.
5. **Reinventing existing infra.** Check before building: `core/prediction_error.py` (the value seed),
   `core/tension_ledger.py` (chronic-mass = a claim-confidence-like accumulator already), `core/recall_provenance.py`
   (exists — examine), the `derived_from`/`chapter_id` columns. The ledger should *promote and unify* these, not
   duplicate them.
6. **Identity ≠ evidence graph.** Evidence / Importance / Identity are different graphs (2+2=4 is grounded but never
   identity). Don't collapse them into one when the identity layer arrives.

## 7. Open questions for the auditors
1. **First consumer: reading or T4?** Reading is the natural producer (most traceable material), but the round-3
   diagnosis says the claim layer is *T4's* missing middle — the higher-value consumer. Build the seam to serve
   which first?
2. **Minimal claim object fields** — is `{text, confidence, status}` + `supports/contradicts` edges the right
   smallest version, or is `status` already premature?
3. **Does `tension_ledger` chronic-mass already approximate claim-confidence?** Should the ledger be built by
   *generalising* the tension ledger rather than as a new table?
4. **Confidence update rule** — can the live L1 `prediction_error` drive it directly from day one, and on what
   cadence (per-encounter / per-sleep / per-prediction-outcome)?
5. **Where do claims get minted first** — the essay/understanding distillation (already summarising), the T4
   keystone, or a tiny dedicated pass? (Tie to Q1.)
6. **Forgetting trigger** — what makes a claim's confidence "stable enough" to delete its raw encounters, and what
   minimal credibility trace makes that deletion lossless *for prediction*?

---

*Status: examination + design framed from four converged auditor rounds; NOT built; this IS the spun-out convergent
primitive. The build discipline is non-negotiable: the §5 minimal claim object first, everything else deferred to a
named consumer. Ingestion layers / consumers: [reading provenance](reading_provenance_plan.md),
[[t4_commit_test_redesign]] (the missing claim-middle), the sleep/dream §6B forgetting layer. Value seed already
live: `core/prediction_error.py`.*


```plan-state
stage: deferred
phase: Design only, never built, no ledger activity; smallest-first seam (section 5) not started
verified: 2026-09-27
next: Needs a named consumer (T4 or reading-provenance) before the section-5 seam gets built
```

## Current State — verified 2026-09-27

### What we have
- A design only (no ledger records — findings/jobs/decisions — cite this plan at all): four converged
  auditor rounds proposing a typed Evidence -> Claim -> Model -> Identity graph with a predictive-value
  retention policy (`core/prediction_error.py` as the value seed).
- Explicitly NOT built, including its own recommended smallest-first seam (§5's minimal claim object).

### What we need
A named consumer to build the §5 seam for, per the plan's own discipline (T4's missing claim-middle, or
reading-provenance's dedup, are its two candidate first consumers, §7 Q1) — nothing has picked this up.

### What we're doing next
Nothing planned; this stays a design record until a concrete plan (T4 redesign, reading provenance, or a
successor idea) actually needs the claim layer and builds the §5 seam first, per its own anti-cathedral rule.
