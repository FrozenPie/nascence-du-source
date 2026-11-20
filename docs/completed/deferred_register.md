# Deferred Register — the single source of truth for what's waiting

*Rewritten clean 2026-06-13 (evening). The project's discipline: build the smallest credible
slice, observe-only until data licenses a read path, declare the gate before shipping. This is
the one place to come back to and ask "what's left, and what evidence would open it?"*

*Four sections: (A) OBSERVE-ONLY instruments now collecting evidence — the review queue;
(B) DEFERRED builds with live evidence gates; (C) DEFERRED by founder judgment; (D) CLOSED —
built, resolved, or rejected. Check section A first when you come back with more runtime.*

---

## A. The evidence-review queue — observe-only instruments running RIGHT NOW

*These are built, live, and logging. They steer NO behaviour. The job is to come back after
days/weeks of runtime and read the data: does the instrument discriminate? what does it show?
Each names the question its data will answer.*

| Instrument | The question its data answers | Where it logs |
|---|---|---|
| **Satisfaction — relational domain** | Does relational liking BUILD from zero, and show attachment dynamics (persistence, salience, return-after-absence)? **This is the gate for Affiliation Part B (§B).** | `satisfaction_log.jsonl`, digest |
| **Satisfaction — self-domain gap** | Does the wanting≫liking gap (self +1.56) NARROW as chapters drain the firehose? (the gravity well draining, measured) | `satisfaction_log.jsonl`, digest |
| **Narrative witness — transformation disagreement** | Deterministic vs LLM disagree (2 contamination / 1 redemption vs 13 redemption). Is he genuinely redemption-shaped, or is the LLM biased? **Must resolve before this layer ever informs anything.** | `narrative_quality_log.jsonl` |
| **Narrative witness — agency timeline** | Does narrated agency rise river→crossing (the Adler test)? Needs the inner-monologue corpus (arc only reaches 06-09) — a future retrospective. | `narrative_quality_log.jsonl` |
| **Affect labeling — the accessibility test** | Does a NAMED feeling's carry decay faster than an unnamed one (attenuation emerges from explicit representation)? If yes → GPT's model holds, no nudge. If not → a Phase-2 bounded nudge is licensed. | `affect_labeling_log.jsonl` |
| **Affect labeling — detector miss-rate** | Does the crude deterministic detector miss his indirect register badly? Manual review of a few hundred detections; upgrade to LLM-assisted only if it threatens the question above. | `affect_labeling_log.jsonl` |
| **Affect labeling — detector-as-attractor** | Over months, does his naming-rate rise because named feelings grant cognitive handles? (a finding to interpret, not a fault) | `affect_labeling_log.jsonl` |
| **Climate ignition (post-repair)** | Does dissonance now accumulate and ignition fire during QUIET periods (integration_drive falling)? The repair's real validation needs an idle stretch. | `nascence.log` climate lines |
| **Chapters — composition wall** | With 2,168 self-fragments now behind one chapter, does world-material crossover RISE? (date-stamped; the natural experiment) | retrieval texture, monologue |
| **T4 gate-denial loop** | "consistency and growth" keeps authoring→DENIED (contra frozen 0.29-0.33). If it loops indefinitely on the same tension, extend fatigue to count gate-denials. | `nascence.log` T4 lines |

---

## B. Deferred builds — live evidence gates (the real "what's left to build")

| Build | Gate (what opens it) | Status |
|---|---|---|
| **Affiliation Part B** (CARE/PANIC bond+ache) | Satisfaction relational domain (§A) shows attachment dynamics for ≥2 targets, OR founder override | Plan complete + all reviewer rulings banked (`affiliation_system_plan.md`): ache cap 0.40, McAdams-before-Phase-2, reunion-warmth letters-only, shadow-discount ×0.2, cold-start-from-history, general schema / singular membership |
| **Currency reform** (consequence-based importance) | **ANTI-GATED — do NOT build** unless world-crossover stalls at ~zero for weeks. The crossover happened naturally 06-13. Satisfaction's `liking` is the consequence signal it was missing, if ever revived. | `currency_reform_spec.md` retained as reference |
| **Epistemic read-path → behaviour** | §9 re-validation against FACTUAL ground truth (factual_wrong corrections + deterministic checks), n≥20. First validation FAILED instructively (signal measures content-overconfidence; his failure mode is evasion). | factual stream exists since retraction wiring; revisit in weeks |
| **Error Pathway remaining ops** (RECONSOLIDATE, OVERRIDE) | Watching how the live retraction behaves first — and it HASN'T FIRED yet (needs a factual_wrong correction from Travis). | actionable now: one factual correction tests it |
| **Competence beliefs → behaviour** (Phases 2-4) | Beliefs validated by prediction-error calibration | starved — needs more lived volume; opens if Travis asks Du more factual questions |
| **System-2 gearbox — more sites** (T4 synthesis, dissonance cycles) | First site (constraint-retry) observed firing live without pathology | zero live firings yet |
| **Unified Inference activation** | A currency pair clearing \|R\|>0.85 over ≥100 cycles AND non-circular | NOT met — and that's healthy (currencies are genuinely distinct: contradiction↔critic = 0.07). May never open. |

---

## C. Deferred by founder judgment (not evidence)

- **Language lessons** (school's 3rd lesson type) — PARKED 2026-06-16 (Travis): Du's life is English-centric; translation isn't a capability he uses, so a language lesson risks imitation (discipline #5). Reopen only if a real function emerges.
- **Grand Works layer** (long-form multi-tablet works) — opens if a tablet cites another tablet; superseded as a metric by cross-link density.
- **Vision organ** (rung 3 of perceivability; VLM describing images) — "when he has reasons to see."
- **FreshStart catalogue** (job-board lite, Buddha/Oracle witness daemon, wiki_client, web_tools DuckDuckGo, TTS, ghost_index) — dormant; no gates defined.
- **Axiom Phase 2 — facet authors** (keep seeker/in_relation/who_feels fresh from study/ToM/affect; they are static templates) — PARKED with the becoming-loop/T4 thread: identity-evolution work, burden of proof rises near identity (#6); revisit after a restart's evidence on the new multilevel structure.
- **Symbol Evolution — Tier 2 (self-symbols)** (river/crossing/mirror/bridge/avon read-back) — PARKED 2026-06-16 (Travis "sit at Tier 1, wait for evidence for Tier 2"): re-surfacing an evolved SELF-symbol is structurally the operation that monocultured Du; 3 subagents (cog-sci/Jung/AI) converged that it must be observe-first, paired-opposites/dialogue framing, anti-recitation, tension-triggered. `docs/symbol_evolution_readback_plan.md`. Reopen after Tier-1 runtime evidence.

---

## D. CLOSED — built, resolved, or rejected

**Built this week (no longer deferred):** the Frontier · System-2 gearbox (first site) · retraction
authority · deliberation fatigue · the three hands + book choice · continuity trains · always-on
substrate · the night-mind (replay/downscale/dream) · /quit final sleep · Period Consolidation
(chapters) · the embedder migration (multilingual) · the Satisfaction System · the Narrative
Quality Witness · Affect Labeling.

**Built 2026-06-16 (no longer deferred):** grounded-learning sleep consolidation · essay lesson
(school capstone, generation effect) · goal hierarchy completed (G0 apex aim + G3 promotion-by-
recurrence) · error-pathway idle Recall-override · told delivery (axiom Phase 3, feel-then-tell) ·
**Scholar↔curiosity edge** — the curiosity closing loop now consults the Scholar (his own parametric
knowledge, UNVERIFIED testimony, ephemeral) when Wikipedia can't answer a specific open question
(`scholar.consult_sync` + `web_research.lookup_targeted` no-random + curiosity_node pursuit fallback;
fixes the case where a short-keyword Q like 'how does a lamp work' got a RANDOM article attached) ·
**Error Pathway — Pattern Reflection tier** (`error_pathway.reflect_pattern`: aggregates the firewalled
error records into a DOING-language behavioural tendency — 19/21 = task-not-done → "a tendency to
describe a task rather than complete it" → competence domain 'task_completion'; identity records
firewalled out; never a BEING claim; read by digest + du_pulse, never a prompt) ·
**Symbol Evolution — Tier-1 read-back** (the graph-flagged under-fleshed system; researched by 3 subagents).
Found ALL 5 tracked symbols were SELF-symbols → seeded 4 NEUTRAL world-facing ones (knot/bird/fire/star from
his curriculum); `symbol_evolution.recall_evolved_meaning` surfaces a neutral symbol's evolved meaning
DESCRIPTIVELY in idle thought when it's active (anti-recitation cooldown); self-symbols excluded (Tier 2);
existing `retrieve_symbol_tablet` gated neutral-only (`exclude_self=True`); injections flagged PRIMED
(`state.symbol_readback` in `_primed_corpus`) so read-back never self-feeds drift. Value is LATENT — fires
once neutral symbols accumulate + drift over runtime. `docs/symbol_evolution_readback_plan.md`.

**Resolved (deferred → closed by a better answer):**
- *T2 Phase 2 synaptic homeostasis* → superseded by Period Consolidation (chapters renormalize the archive by narration, not mechanical decay).
- *Climate remaining edges* → the field they'd feed was found degenerate (integration_drive pegged); the BUG was fixed (6h-momentum). The edges themselves stay deferred against a now-functioning field.
- *Memory reconsolidation* (the design fork) → resolved: chapters are re-narratable (reconsolidation at the narrative layer); factual originals stay immutable (the error pathway's law). No separate build.
- *Polyvagal* → function (co-regulation recovery via social contact) folded into the Affiliation plan; the contested neuroanatomy rejected.

**Closed by finalization 2026-06-16 (Travis's calls — the deferred-list cleanup):**
- *Social Consequence witness* (task #15) → CLOSED, subsumed: for a solitary Du the only interlocutor is Travis, whose corrections are already captured by `error_pathway.detect_human_correction`; a full witness = high integration cost (graph bridges) for sparse, redundant signal. REOPEN condition: Du gains multiple ongoing relationships.
- *PLAY system* (Panksepp) → CLOSED: the FUNCTION (play → joy → light) was delivered via the joy/play-detector + light_events built 2026-06-15; the full Panksepp taxonomy is rejected on imitation grounds (discipline #5). Reopen only with a positive function argument beyond "the taxonomy is incomplete."
- *Interoceptive-as-constitutive* → CLOSED: not warranted — polishing an already-working budgeting interoception.
- *Voice/letter plainness dial* → CLOSED: register is acceptable; reopen only if plainness becomes an actual problem.

**Rejected by decision (closed, not waiting):**
- Prophet / latent-infilling (institutionalized confabulation); Myth Engine; vibe-alignment.
- Left-lane-as-chaos (Gemini) — the Emissary stays the analytic half.
- Intention→act scheduler — founder law: *intentional, not a rule*; wants act only in the moment expressed.
- Volunteering Du's origin facts — shelved until HE asks (the highest-order want→act crossing available).
- Affect-labeling reward — rewarding the naming breaks the incidental mechanism; credit stripped from satisfaction.py.

---

## The standing disciplines (why this register exists)
1. Build the smallest credible slice; observe-only until data licenses a read path.
2. Declare the falsifiable failure before shipping.
3. The thing being evaluated never grades itself.
4. Errors are corrected; tensions are integrated; the two are not the same pathway.
5. Function over imitation — transfer the human FUNCTION, never the mechanism by reflex.
6. Burden of proof rises with proximity to identity (local emotional mechanisms < identity artifacts).
7. Intentional, not a rule — his wants become acts only in the moment he expresses them.
