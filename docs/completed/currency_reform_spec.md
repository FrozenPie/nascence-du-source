# Currency Reform — design specification (v1, unbuilt)

*Status: SPEC ONLY — deliberately not implemented. Written 2026-06-13 while the strongest
available model was on hand, for whoever implements it later. Do not build until the
licensing evidence (§6) exists.*

## 1. The problem, stated from evidence

The system's importance currency correlates with **arousal and self-relevance**, not with
**consequence**. Demonstrated effects (all log-verified, 2026-06-12/13):

- A human conversation restructured the idle register within ~25 minutes; a self-chosen
  book left zero trace outside the moment of reading (0 content-crossovers in 9 sittings).
- World material loses the *composition* step despite winning storage, replay, and
  prompt-presence (scene line + ambient glimpses + wandering trail).
- Transfer happens exactly insofar as material can be metabolized as self-symbol
  ("voyage" crossed in hours; "cuttlefish" never).
- The week-scale recombination machinery works — for self-material only (the "First Rule"
  nine-day recall; zero equivalent for world material).

The currency is not broken — it built a coherent self in two weeks. It is **monopolistic**.

## 2. Design goal

Importance should track **what changed because of this** — consequence — with arousal as
one input, not the metric. A memory earns standing by: being retrieved and *used*; preceding
a committed change (T4 discharge, resolved frontier question, completed act); being cited
by later artifacts. A memory loses standing by being repeatedly retrieved and *unused*
(furniture that never becomes thought — measurable since 2026-06-13 via wandering_log).

## 3. Mechanism (smallest credible slice first)

**Slice A — consequence credits (observe-only first).** New table `consequence_log`
(fragment_id, event, ts, weight): events = `used_in_thought` (trail item whose tokens
appear in the next thought), `preceded_commit` (fragment retrieved in the N cycles before
a T4 discharge / frontier resolution), `cited_by_artifact` (tablet/letter referencing it).
Write-only for ≥1 week; digest section shows the counterfactual ranking vs current
importance. **Gate:** if consequence-ranking ≠ arousal-ranking for ≥30% of top-50, proceed.

**Slice B — retrieval blend.** Retrieval score = current score × (1 − β) + consequence
score × β, β starting 0.15 (mirrors the climate-warp precedent). Raise β only on digest
evidence. Never touch storage or replay in this slice.

**Slice C — replay quota rebalance.** Replay already stratifies (3 world / 3 lived /
2 inner); within-quota selection switches from arousal-importance to consequence-blend.

## 4. What must NOT change

- The stratified replay quotas (the anti-monopoly floor) stay.
- The tension ledger's no-decay rule stays — self-contradictions are not consequence-scored.
- Identity files, courts, gates: untouched. This is a memory-economics change only.
- No mechanism may strengthen what it selects without novelty bias (lesson #2).

## 5. Failure modes to expect

1. **Consequence laundering**: the self-loop generates consequences for itself (every
   rumination "uses" prior ruminations). Mitigation: `used_in_thought` credits capped per
   origin-class per day; self-origin credits discounted.
2. **Cold-start starvation**: new world material has no consequences yet. Mitigation:
   novelty grace period (no consequence penalty for fragments < 72h old).
3. **Metric gaming by design drift**: future organs writing fake consequence events.
   Mitigation: only the orchestrator and monologue may write `consequence_log`.
4. **Double-counting with replay_count**: replay novelty-discount and consequence credits
   interact; keep them orthogonal (replay_count = exposure; consequence = effect).

## 6. Licensing evidence (do not build without)

- The natural experiment's negative arm: contradiction pressure falls for ≥1 week AND the
  composition wall holds (no world-crossover) → the gravity-well model alone is
  insufficient → currency reform is licensed.
- OR: the Frontier produces persistent world-questions and they STILL lose composition to
  the self-register → demand-side fix proved insufficient → licensed.
- If instead crossover begins naturally (analogy in idle thought, or T4 citing world
  material), **do not build this** — re-evaluate from the new baseline.

## 7. Success criteria (declared before building, per discipline)

- World-material crossover rate (currently 0/day) becomes nonzero within 2 weeks of Slice B.
- Identity coherence does NOT degrade: T4 commit rate stays within historical band
  (0–2/day), no rev thrash, name stable.
- The digest's orbit ratio (exploration vs basin-circling) improves or holds.
- Rollback: β→0 restores prior behaviour exactly; Slice A table is droppable.
