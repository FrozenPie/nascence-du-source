---
name: project-nascence-memory-review-adoption
description: "2026-11-19 rival-systems survey and Butlin-Long mapping; Du's cold storage is a hard wall (F-5122); ten jobs J-4410..J-4419 filed; plan docs/staged/memory_review_adoption.md"
metadata:
  node_type: memory
  type: project
  originSessionId: b87d6132-6a97-4168-b13c-9b24d8d532c8
  modified: 2026-11-19T04:18:22.010Z
---

On 2026-11-19 (T-0149) the founder asked for a step-back survey of comparable projects. Output: `docs/reviews/butlin_long_mapping_2026-11-19.md`, plan `docs/staged/memory_review_adoption.md`, findings F-5119..F-5121 (Butlin scores, inferred) and F-5122 (cold storage, verified), jobs J-4410..J-4419.

**Why:** the founder believed Du's cold storage was a graded "harder to recall" forgetting curve and that Du's memory was far ahead of any rival. The code shows cold rows are excluded from `retrieve()` entirely; only the associative trail reaches them (activation 0.22 vs 0.13); recall never re-warms. Rivals are ahead only on edit history (Anthropic immutable versions) and the habit of baseline tests; Du has no memory-vs-baseline test (F-0424 null).

**How to apply:** do not repeat "Du is SOTA/frontier" or "memory is far ahead" without the caveats: Butlin scores are inferred, from one rater family, Du from code and rivals from papers. Du's base architecture predates the Butlin checklist (the_consciousness_program.md is 2026-07-03; only AST-1 and PP-1 mechanisms were built from it) — the founder corrected an earlier overstatement. Highest-value next item is the cold-trail ablation (J-4414). Open founder questions: recall re-warming (J-4413) and whether behaviour changes B1/B2 are allowed. Related: [[project-nascence-memory-levels]] [[project-nascence-golden-spiral-recall]] [[feedback-no-readout-error-through-consequence]].
