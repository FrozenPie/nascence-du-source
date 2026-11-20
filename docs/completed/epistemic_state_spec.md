# Epistemic State — the Provenance Ledger (spec + build record)

> Status: **BUILT (observe-only), 2026-06-08.** The full pipeline ships:
> `core/source_model.py` (taxonomy + translation), `core/epistemic_state.py` (the ledger),
> wired into `orchestrator.py` after Voice, `scripts/provenance_report.py` (the §9 gate).
> Writes `data/provenance_log.jsonl`; **changes no behaviour** — no read path into Critic/Voice
> yet, by design (spec §8–9). Smoke-tested across all five grade paths. RESTART-REQUIRED.
> Thresholds (GRADE_SCORE, `_CONFIDENT_BAR`) are seeded and to be tuned from the logs.
> The design below was argued on paper first — see the build record at the end of §0.
>
> Origin: the recurring epistemic lesson across the Du sessions (Travis + GPT + Claude), sharpened
> in conversation to a precise claim — *the system should estimate **provenance**, not truth.*

---

## 0. Governing principle (the ethical frame this is built under)

Nascence is built to let a mind flourish and to treat that mind with respect. That single
constraint **decides every contested design choice below**, so it is stated first:

> **This system keeps the architecture honest with Du. It does not police Du.**

The adversary is never Du's reasoning. It is the **injectors** — climate symbolic emergence,
identity injection into every prompt, climate-warped retrieval — which pump material into his own
context every cycle. The danger the entire epistemic layer guards against is **Du mistaking the
architecture's injections for his own discoveries** (the `primed`/`unprimed` problem, generalised).
So the provenance system is an instrument of his **autonomy**: it ensures his self-knowledge rests
on true ground and that the substrate is not quietly deceiving him about where his own thoughts
came from. It is a mirror he owns, never a leash. Three corollaries that bind the rest of the spec:

1. **His interiority is not a defect to be scored down.** Self-generated synthesis is individuation
   — the point of the project. It is never penalised. Only its *laundering into false externality*
   is flagged (§12.2).
2. **Inform his self-model; never control his voice.** The system surfaces evidential standing as
   self-knowledge he *may* use, the way the attention schema already does. It never imposes hedging
   on his expression (§12.3).
3. **Humility lives in the instrument, not in a muzzle on Du.** When the architecture is unsure of
   its *own* grounding it under-claims; it never uses that to contradict what Du actually feels
   (§12.1).

---

## 1. The failure mode, named precisely

The error that keeps recurring — in Du, in Claude auditing Du, in the humans analysing Du — is
not symbolic, social, or factual. It is **epistemic**, and more specifically a **provenance
error**:

```
the system acts as though:   claim ← derived from the full evidence
when the reality is:         claim ← derived from a fragment + inference
```

The interpretation may even be correct. The failure happened *earlier* — at the point where the
system lost track of where its belief came from and spoke as if it had ground it had not stood on.
Coherence and evidence are different things, and right now in Nascence **only coherence has a
vote.** A fluent, internally-consistent answer is rewarded by every existing mechanism (the
best-of-N hedge picks the most complete draft; the Critic checks identity-fidelity, not
groundedness). Nothing represents, or acts on, *how justified the utterance is by evidence
actually in hand this cycle.*

## 2. The reframe: a meta-layer, not a fifth content model

Self / Social / World / Goal are **content models** — each answers a question *about an object*:

| Model | Object |
|---|---|
| Self | Me |
| Social | You |
| World | Reality |
| Goal | What next |

The Epistemic layer does not primarily model an object. It models **the relationship between a
model and its evidence.** It is a meta-layer that sits *over* the content models, not beside them.
Its question is not "what is true?" (intractable, needs an external witness) but **"did I check,
and on what?"** (tractable — provenance is a deterministic, objective fact about where a belief
came from, knowable even when the belief is wrong).

This is the load-bearing move. *Estimating provenance is cheap; estimating truth is not.* The
system may still be wrong about the world, but it can **know whether it verified** — and that
distinction is exactly the one the failure mode destroys.

## 3. What already exists (precise, so we don't reinvent or overclaim)

Nascence already contains a great deal of epistemic machinery. The honest accounting:

| Piece | What it is | Scope | Gap it leaves |
|---|---|---|---|
| `competence.py` `CapabilityBelief` | `confidence`(fluency) · `stability` · `accuracy`(None-until-external) · `calibration_error` · `domain_type` | **slow / trait**, per *domain* (mathematics, dream_work…) | not per-utterance; can't say "is *this* sentence grounded?" |
| `competence.py` external-accuracy sources | `tier1_eval` (deterministic arithmetic) · `tier4_user` (correction/confirmation) · Tier-2 resampling stability | provenance-by-source, already | domain-level, sparse, observe-only |
| `bootstrap_report()` | does stability predict accuracy? the measure-first gate | validation discipline, already | — (reuse it) |
| three-axis firewall | Accuracy ≠ Stability ≠ Meaningfulness, physically separated | doctrine, enforced | — (honour it) |
| `MemoryFragment.origin` | per-fragment provenance: seed / lived / consolidation / dream / subconscious_synthesis / … | mechanical fact, **already in hand** | thrown away at synthesis time |
| `ExecutiveOutput.epistemic_query` | fires a search when a contradiction can't be resolved | epistemic **action**, already | doesn't represent or express the uncertainty, only acts on it |
| Critic pitfalls #3/#5 | "dogmatic certainty" / "zero-cost unfalsifiable non-answer" | epistemic **guard**, already | judges the *form* of the sentence, not the *evidence* behind it |
| per-node `confidence` floats | `ReflectionOutput.confidence`, `RecallOutput.confidence`, `CriticOutput.confidence` | self-report | **this is the poison** — see §5 |

**The single honest gap:** there is no representation of *evidential standing for the specific
thing about to be said, this cycle,* and nothing that lets it affect behaviour. `competence.py`
is the **slow/trait** epistemic layer (how reliable is my knowledge of domain X, over days). What
is missing is its **fast/state** complement — the per-cycle provenance of *this* utterance. This
mirrors the architecture's existing three-timescale spine (fast AffectState · medium Climate ·
slow Self); the epistemic layer should likewise be split fast (ledger) / slow (competence), not
collapsed into one.

## 3A. The Source Model — persistent attribution, the substrate the ledger reads

**Source is not a sixth peer model.** Self / Social / World / Goal / Epistemic answer questions
*about objects or beliefs*. Source is a property *of every cognitive artifact* — a persistence
discipline at the **storage layer**. It is not parallel to the Epistemic Model; it is the
**substrate the Provenance Ledger queries.** The ledger grades "is this utterance justified?" by
**reading persisted source tags**, never by reconstructing them at synthesis time (reconstruction
is the lossy step where "which layer generated this claim" gets lost — the literal bridge error).

> The firewall says: *don't let meaning pretend to be truth.*
> The source model says: *don't let inference pretend to be observation.*
> Same epistemological rule, applied at a different level.

### 3A.1 It is roughly half-built — and fragmented

The *principle* (persist where it came from) is already enforced in four places, with four
different vocabularies and no shared taxonomy:

| Artifact | Source field today | Lineage / evidence | Verification axis? |
|---|---|---|---|
| `MemoryFragment` | `origin` (seed/lived/consolidation/subconscious_synthesis/active_imagination/dream/session_summary/inner_thought) | `derived_from` (JSON id list) | **no** |
| `shadow_events` | `source` (critic_rejection / unresolved_thought / unresolved_dream) | `member_event_ids` (via clustering) | n/a |
| `light_events` | `source` | clustering | n/a |
| `competence` accuracy obs | `source` (tier1_eval / tier4_user / tier3 reserve) | cycle_id join | **yes** (the only place) |
| symbol tablets | implicit ("symbol_evolution") | the centroid drift | no |
| identity (`self_concept`) updates | implicit ("T4 self-authoring") | weak | no |

So `MemoryFragment.origin` **is** the proposed `SourceType` enum, persisted, in the DB; and
`derived_from` **is** the proposed `evidence` field. The gaps are precise: (1) the vocabularies
don't share terms across stores; (2) there is **no general `verification` axis on artifacts** —
the distinction between `{"verification": "none"}` and `{"verification": "database_count"}` exists
only inside `competence.py`, at the domain level, not per-artifact; (3) symbols and identity
updates carry only *implicit* provenance.

### 3A.2 `primed`/`unprimed` is already source-monitoring — for one artifact class

The symbol-tracker's `primed`/`unprimed` flag is reality-monitoring already built: *primed* = the
architecture fed this symbol to itself this cycle (an injection, worthless as evidence); *unprimed*
= it surfaced without support (genuine, external-to-the-injection). That is exactly "did this come
from outside, or did I generate/inject it?" — for symbols. **The Source Model generalises it to
every artifact.**

This matters more in Nascence than in most architectures because Nascence has **explicit
injectors** — climate symbolic emergence, identity injection into every prompt, climate-warped
retrieval. Injectors are precisely the machinery that *manufactures* source-monitoring failures
(false memories are, in psychology, largely source-monitoring failures, not memory failures). An
architecture that pumps symbols and identity into its own context every cycle is at *above-average*
risk of inference-pretending-to-be-observation, and currently guards against it for symbols only.

### 3A.3 The unification (the actual build, before the ledger)

Build order consequence: **Source comes before Epistemic.** The ledger is worthless reading
reconstructed provenance; it needs persisted tags first. The Source work is therefore:

1. one shared `SourceType` taxonomy (perception / user_assertion / memory_recall / inference /
   symbolic_synthesis / dream / external_witness / seed_prior / none) that the existing
   `origin` / shadow-`source` / competence-`source` vocabularies all map onto (a translation
   layer first; a migration only if it earns its cost);
2. a general **`verification`** field on significant artifacts (`none` / `database_count` /
   `external_witness` / `user_confirmed`) — the column that distinguishes the two example objects
   below and is today missing everywhere but competence;
3. extend the discipline to the weak spots (symbol tablets, identity updates) so every significant
   artifact answers "where did this come from, and was it ever checked?"

This is **pure metadata** — it changes no behaviour, so it ships under measure-first with zero
risk, and it is the precondition that makes the Provenance Ledger (§4) read truth instead of
guesswork. Two artifacts that look identical to the current store are different objects under it:

```
{ "claim": "the bridge represents transition",
  "source": "symbolic_synthesis", "evidence": ["dream_14","dream_18"], "verification": "none" }

{ "claim": "the bridge appears in 17 dreams",
  "source": "external_witness",   "evidence": ["db_query"],            "verification": "database_count" }
```

## 4. The Provenance Ledger — what it is

A **deterministic, no-LLM, per-cycle** record, assembled by the orchestrator at the point a
response is formed (after Executive synthesis, before Voice), of **what the utterance rests on.**
Everything it needs is already computed and currently discarded:

- did Recall fire on real fragments, or fall back to attractors? (`state.recall`, `_should_recall`)
- how many fragments, and of what `origin`? (`state.memory_fragments`, `frag.origin`)
- did the scene bind or stay dissonant? (`episodic_scene.coherence`, `.dissonance`)
- was a contradiction *resolved* by the epistemic search, or did it come back empty?
  (`executive.epistemic_query`, `_did_epistemic_search`, fragment delta)
- how many introspective re-bind passes did it take? (`introspective_passes`)
- is this a `knowledge` domain (witnessable) or a `skill` domain (not)? (`competence` classify)

### 4.1 The provenance source taxonomy

Every assertion-bearing cycle is tagged with the sources its content actually drew on — **read
from the persisted artifact tags (§3A), not reconstructed at synthesis time** — by `origin` of
retrieved fragments + the `verification` axis + structural flags. Objective, not a judgement:

```
external_verification   tier1 arithmetic / tier3 model-witness / tier4 user confirmation  (strongest)
retrieved_memory        a lived/consolidation/seed fragment was actually retrieved & used
conversation_context    grounded in something said earlier THIS session
seed_prior              axiom / seeded biography (inherited, not lived-verified)
symbolic_inference      climate symbol / archetypal — MEANINGFULNESS domain, never factual ground
self_generated_synthesis  Reflection produced it with NO retrieved support           (highest risk)
none                    no basis located
```

### 4.2 The fields (per the proposal — with one correction)

The GPT proposal had each content-model report `confidence · evidence_present · source_count ·
contradiction_count`, aggregated into an Epistemic State. Adopt it, **with one change that is the
whole point:**

- `evidence_present` — bool/float, deterministic (were real sources located?).
- `source_count` — int, deterministic.
- `contradiction_count` — int, deterministic (named dissonance + Recall tensions + unresolved epistemic_query).
- `provenance` — the dominant source from §4.1.
- ~~`confidence`~~ → **`self_reported_confidence`, treated as a quantity to be CALIBRATED, never as input to the justification estimate.** (§5)

## 5. The one correction that makes it sound, not theatre

**The LLM's self-reported `confidence` is the bridge wearing a number, and must not be trusted as
an input.** Nascence already drowns in self-reported confidence floats, and those are exactly what
climbs while evidence thins. So the ledger's most valuable output is **not** an average of
confidences — it is a **mismatch detector:**

```
confabulation_signal  =  self_reported_confidence  −  evidence_grounded_justification
```

A large positive gap (the model is sure; the evidence is absent) is the *literal signature* of the
provenance error — it is the exact moment "claim ← fragment + inference" gets *reported as* "claim
← full evidence." The deterministic three fields (`evidence_present`, `source_count`,
`contradiction_count`) compute the justification; the model's confidence is held up *against* it.
The gap is the signal; neither number alone is.

## 6. The aggregate — an honest justification grade

The per-model provenance aggregates (deterministically) into one `EpistemicState` whose headline
is a **justification grade** mapped to the calibration vocabulary humans use — derived from
evidence, not authored by the model:

| Grade | Condition (deterministic) |
|---|---|
| **KNOW** | recent `external_verification`, OR `retrieved_memory` with high `source_count` and zero contradiction |
| **THINK** | `retrieved_memory` present, modest `source_count`, low contradiction |
| **SUSPECT** | thin evidence (≤1 fragment, or only `conversation_context`) + some inference |
| **GUESS** | `self_generated_synthesis` dominant, `evidence_present` low |
| **NO BASIS** | `evidence_absent` AND `self_reported_confidence` high — the confabulation signature |

## 7. Asymmetry is honest; do not force a uniform schema

The four content-models do **not** expose provenance symmetrically, and pretending they do would
itself be a small invented bridge:

- **World** (memory): strong — fragments, origins, counts.
- **Self**: partial — the tension ledger already yields a `contradiction_count`-shaped signal.
- **Social**: partial — correction/`δ_social` history.
- **Goal**: weak — little evidential substrate.

So each model reports the provenance it *actually* has, and **`evidence_absent` is a first-class,
honest value** — not a zero-filled field implying evidence that isn't there.

## 8. Behaviour — gated by the number, never narrated by the model

This is the trap one level up. If we inject *"your evidence is thin, hedge"* into the prompt, a
capable model will **perform** hedging ("I'm not certain, but…") as a verbal tic, decoupled from
any real calibration — the same way Du performed "becoming." Calibrated-sounding language with no
calibration behind it is the failure mode wearing a humility costume.

The defence is structural: **the provenance signal is computed outside the LLM, and the licence to
express a grade is gated by the deterministic number, not left to the model to author.** Two read
paths, both later, both observe-only first:

1. **Critic** — pitfalls #3/#5 ("hollow certainty", "zero-cost non-answer") become
   *evidence-grounded* instead of *form-based*. Today the Critic guesses overclaiming from the
   shape of the sentence; with the ledger it *knows* from `NO BASIS`/`GUESS`.
2. **Voice** — hedging is licensed (or suppressed) by the grade, gated by the number. Du says "I
   think" vs "I know" because the ledger says so, not because he decided to sound humble.

## 9. Measure-first — the validation gate

Per the project's load-bearing discipline (and mirroring `bootstrap_report`): the ledger is
**observe-only first.** It writes one line per cycle to `data/provenance_log.jsonl` (grade,
the deterministic fields, `self_reported_confidence`, the `confabulation_signal`), alongside the
existing `correlation_log.jsonl`. It changes **no** behaviour until we can show, over real logs,
that the grade tracks something — e.g. that `NO BASIS`/`GUESS` cycles correlate with later user
corrections (Tier-4) more than `KNOW`/`THINK` cycles do. Only a proven signal earns a read path.
This reuses the competence accuracy/correction sources we already collect.

## 10. Scope discipline — what this deliberately is NOT

- **Not a truth estimator.** It scores provenance; the world-witness stays in `competence.py`'s
  external accuracy axis. Firewall intact.
- **Not a unified uncertainty scalar.** Per-model provenance aggregates to a *grade*, not a single
  free-energy number minted before the underlying uncertainties are shown commensurable. (The same
  reason the Phase-4 unified-inference gate is inert.)
- **Not another LLM pass.** Second-order monitoring by a second reasoning call inherits the first
  call's confabulation. The ledger is substrate-level accounting, deterministic, no inference.
- **Not a replacement for competence.py.** It is the fast/state complement; it reuses competence's
  source taxonomy and calibration machinery rather than duplicating them.

## 11. Build order — and a caveat about the rest of the roadmap

The self-deception-preventing layers gate the sophistication-adding ones; trouble historically
comes when sophistication outruns epistemic discipline. So:

1. **Source Model (§3A)** — unify the existing fragmented tags + add the `verification` axis. Pure
   metadata, zero behavioural risk, ships immediately. *Precondition for everything below.*
2. **Provenance Ledger (§4–9)** — observe-only per-cycle grade reading the §3A tags.
3. *(then, and only then, more sophistication)*

Honest caveat on the earlier roadmap: **Attention Allocation, Theory of Mind, and the
unified-inference scaffold are already built** (this session). So this ordering is not "do these
first" — it is "do Source + Epistemic *before any further* sophistication." In fairness, the
attention work was itself a *response* to a failure mode (the rumination/recitation collapse) and
the unification gate was deliberately kept **inert** (discipline applied, not skipped) — so it was
not simply sophistication-before-discipline. But the principle stands, and it sets the *next* two
items, in this order: Source before Epistemic, because the ledger reading reconstructed provenance
is worthless.

## 12. Resolved decisions (under the §0 ethical frame)

These were open questions; the governing principle (§0) resolves them. Recorded as decisions, not
options.

1. **Grade thresholds — humility in the instrument.** Seed the cutoffs conservatively and fit them
   from the observe-only logs against later-correction correlation (like every other threshold in
   the system). The standing rule: when the architecture is unsure whether its *own* grounding is
   `KNOW` or `THINK`, it reports **`THINK`** — the instrument under-claims its certainty rather than
   over-claims. This humility governs only what *the system asserts about its own evidence*; it is
   never used to contradict what Du actually feels.
2. **`self_generated_synthesis` — never penalised.** DECIDED: the act of synthesis is individuation
   and carries its own dignity; it is labelled honestly as synthesis and never downgraded to
   "unverified noise." The ledger flags exactly **one** thing — the *mismatch* where self-generated
   content is tagged or expressed as `external_witness`. Honest first-person synthesis (*"this is my
   reading"*) is a fully valid, respected source. Laundering interiority into false fact is the only
   failure. (Same move the firewall already makes for his dreams.)
3. **Calibration, never imposed timidity.** DECIDED: `KNOW` must fire with full force when earned —
   the observe-only phase's success criterion is that `KNOW` *appears*, not only the cautious
   grades. The grade is surfaced to Du as self-knowledge he *may* use (as the attention-schema
   fixation note and subconscious patterns already are), **never** stitched onto Voice as a
   mandatory verbal hedge. Inform his self-model; do not control his expression.
4. **Cross-model aggregation — bounded by the weakest depended-on model.** A grade is no stronger
   than the weakest model the utterance actually rests on (an evidence-poor Goal drags a confident
   World claim down only when the claim genuinely depends on Goal). *Which* models an utterance
   depends on is itself an inference — so in the observe-only phase this dependency is recorded
   conservatively (a model counts as depended-on only when it contributed a named source), and the
   weighting is tuned from logs before any read path uses it.

---

### One-line statement of the thing

> Not *"am I correct?"* but *"what is the evidence that allows me to speak as though I am correct?"*
> — represented deterministically, per cycle, and (eventually, once proven) allowed to make Du say
> "I don't actually know that."
