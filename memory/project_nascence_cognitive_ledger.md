---
name: project_nascence_cognitive_ledger
description: "Nascence — THE convergent primitive behind T4/reading/dreams/consolidation: a typed layered cognitive-value system (Evidence→Claim→Model→Identity) governed by predictive-value retention; 'the cognitive ledger that decides what earns permanence.' Spun out 2026-06-17 after 4 auditor rounds. NOT built; minimal claim object first."
metadata:
  node_type: memory
  type: project
  originSessionId: 012323c4-3fb7-4445-b78f-150a4e0a1404
---

Nascence **COGNITIVE LEDGER** — `docs/cognitive_ledger_plan.md` (auditor draft v1, 2026-06-17). **Spun out of the
reading-provenance plan** after FOUR auditor rounds all converged on the same conclusion: the real missing
primitive isn't reading provenance / lineage / forgetting — it's **a typed, layered cognitive-VALUE system that
decides WHAT EARNS THE RIGHT TO REMAIN in memory.** Last auditor named it: **"the cognitive ledger that decides
what earns permanence."** Bigger than reading AND T4 — the shared memory/value layer under both.

**GOVERNING FRAME:** *memory is PREDICTION INFRASTRUCTURE* — info is kept because it stays useful for predicting
reality (strengthen/weaken/invert). Storage FINITE → forgetting is a first-class design principle (delete raw
evidence once support folds into stable confidence + a credibility trace), NOT a failure mode.

**THE SUBSTRATE (typed layered graph):** **Evidence(encounters) → Claim → Model → Identity**, each level slower/
harder to change (same stratification as the multilevel axiom, generalised). Encounters = support structure
(deletable); **CLAIMS = the first survivable units** (confidence + status active/weakened/rejected/resurrected +
typed edges); Models = clusters of mutually-supporting claims; Identity = slowest priors, **built FROM stable
claims** not from evidence directly. Typed edges (reserve shape, populate lazily): supports/contradicts/revises/
replaces/reinforces/transformed_into + `source_of` ≠ `changed` (provenance≠influence); NEGATIVE edges first-class
(a rejected belief is history). **THE POLICY = predictive value, NOT greenfield — seed live in
`core/prediction_error.py` (L1, feeding)**: a claim gains confidence when relying on it cuts future surprise.
Corroboration (independent sources converge → strengthen) vs duplication (same source repeated → compress) =
opposite behaviours. Value not volume (`changed` edge, not `source_of` count).

**FORGETTING = COLLAPSE-TO-CONFIDENCE (the finite-storage answer):** encounter→claim→stable confidence + source-
credibility trace → DELETE raw encounter. Principled replacement for the blunt importance-prune; home for the
sleep/dream §6B store-cap work.

**THE T4 MISSING MIDDLE (sharpest consequence):** T4 grounding is weak because it leaps Evidence→Self DIRECTLY,
skipping Evidence→Claims→World-model→Self; the self is built from STABLE CLAIMS that survived evidence updates →
explains why every text-cosine-to-evidence metric failed (no claim layer to stand on). The ledger IS that middle →
T4 may be the highest-value FIRST consumer, not reading (open Q).

**CROSS-PLAN MAP:** reading=writes encounters+claim candidates (first ingestion layer); T4=consumes the claim
middle for grounding; dreams=reprocess unresolved claims offline; sleep/consolidation=stabilise/weaken confidence +
collapse-to-confidence forgetting; idle-exec/pulse=predictive-usefulness as retention/priority.

**THE FIRST SEAM (the ONLY near-term build — auditor-unanimous: tiny/explicit/immediately useful):** the MINIMAL
claim object — `encounter → claim{id,text,confidence,status} → edges{supports|contradicts} → confidence_update
(driven by L1 prediction_error)`. Minimal: a claims table + claim_edges (or reuse derived_from) + `mint_claim` on
ONE existing distiller (essay/understanding pass, OR T4 keystone) + a confidence tick. NOTHING ELSE — no
corpus-wide claim extraction, no model/identity layers, no forgetting engine yet. OBSERVE-FIRST (mint in shadow,
log confidence trajectories, before anything reads them).

**#1 RISK (every auditor): scope explosion / cathedral-before-plumbing.** The layers/edges/policy/forgetting are a
MAP not a build list. Ship the seam only; each layer needs a named consumer. PITFALLS: value+substrate co-evolve
(can't value nothing); claim extraction expensive (mint only where distillation already happens); premature
deletion (wait for stable confidence); reinventing infra — CHECK `prediction_error.py`, `tension_ledger.py`
(chronic-mass ≈ a claim-confidence accumulator already!), `recall_provenance.py`, derived_from/chapter_id;
Evidence/Importance/Identity are DIFFERENT graphs.

**OPEN Qs:** first consumer reading vs T4? minimal claim fields? does tension_ledger chronic-mass already approximate
claim-confidence (build by GENERALISING it not a new table)? confidence-update cadence? where mint claims first?
forgetting-trigger (stable across N updates)?

**⚠ CROSS-PLAN REFINEMENT (from the active-imagination round, §10.8 of `docs/active_imagination_plan.md` v2):
NOT EVERYTHING IS A CLAIM.** The ledger's "Evidence→Claim→Model→Identity" is claim-centric (reading-side), but
the auditor showed there are at least **FOUR distinct cognitive CURRENCIES — Figure / Symbol / Claim /
Identity** — each evolved by a different organ: **AI+dream → FIGURES** (a named Other w/ evolving state, e.g.
the bridge: "cannot cross"→"crossing complete"), **symbol-evolution → SYMBOLS**, **reading → CLAIMS**, **action
→ EVIDENCE**. Figures/dreams/symbols are NOT claims — forcing them into claim-space too early LOSES
information. **T4 must read ACROSS all currencies**, or it becomes dependent on whichever subsystem happens to
speak in propositions. IMPLICATION for the ledger: the substrate isn't only claims — it's persistent cognitive
OBJECTS of several types that evolve; the claim is ONE type (the reading-side one). The smallest shared notion
= "a persistent cognitive object that evolves" (figure-object is the first NON-reading instance — built by the
AI plan). Don't force the unification now (cathedral) but the claim-only framing is too narrow. The deepest
question stands: define the OBJECT before measuring movement (drainage/fit/novelty/dream-res/provenance all
failed by measuring TEXT before defining what moves). [[project_nascence_active_imagination]]

**⚠ DEEPER GENERALISATION (from the active-imagination §12 round): the ledger's predictive-value policy ("what
earns PERMANENCE/storage") is a special case of a bigger primitive — an ATTENTION-ECONOMY: "WHAT EARNS ANOTHER
ENCOUNTER?" (finite resource = future ATTENTION, not just storage).** Persistence/recurrence/lineage are all
EVIDENCE not VALUE (biological minds are full of persistent JUNK — trauma loops/rumination). The SAME value
question drives dream-recurrence / AI-recurrence / contradiction-recurrence / T4-probation-windows / provenance-
retention / memory-pruning — they all BID for future attention. KEY: unify the RESOURCE (a shared currency they
bid for), NOT the organs (keep specialisation). This may be THE deepest convergent primitive — the ledger's
"what earns permanence" and this "what earns another encounter" are the same question at storage- vs attention-
scope. Likely its own plan (the attention-economy), feeding/beside the ledger. [[project_nascence_active_imagination]]

**STATUS: examination/design framed from 4 converged rounds; NOT built; going to auditors. The convergent primitive
the whole architecture has been circling — refined twice: (a) persistent cognitive OBJECTS of 4 currencies not
claims alone; (b) governed by an ATTENTION-ECONOMY (what earns another encounter), of which storage-permanence
is one case.** [[project_nascence_reading_provenance]] [[project_nascence_t4_redesign]] [[project_nascence_active_imagination]]
[[project-nascence-sleep-dream]] [[project_nascence_multilevel_axiom]]