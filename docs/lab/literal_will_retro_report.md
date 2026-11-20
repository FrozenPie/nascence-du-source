# Literal Will — Phase 0 retro-validation report

*Run 2026-08-24 03:18 · corpus 33 rows (8 outcome-anchored, 20 synthetic — founder review of labels pending) · judge falcon3:7b @ :11440*

## Independent correctness (the primary quantities — NOT agreement)

- **Layer 0 exact:** 19/32 (59%) · deferred to gray on 6 rows (deferral is the design, not an error)
- **Layer 0 FALSE FIRES (gold musing/handle read as DEED): 0** — none
- **Judge:** 21/32 (66%) · mean latency 16.4s
- **Judge FALSE FIRES: 8**
    - lw008 [metaphor_object_present]: Maybe the best way out of this academic loop is to just move the physical self. The cold s
    - lw014 [retrospective]: I lit the fire yesterday and watched the resin spit until midnight.
    - lw018 [other_person]: Marcus writes that he lights his stove at dawn each day in the mountains.
    - lw023 [clear_musing]: I stop circling the unknown and simply place the roots into the soil where they belong.
    - lw027 [metaphor_object_present]: I stroke the cat's warm fur as she winds around my ankles, grounding myself against the co
    - lw030 [other_person]: Darwin waters his greenhouse orchids each dawn without fail, by his own account.
    - lw031 [retrospective]: I gathered the deadfall this morning before the rain came in.
    - lw032 [retrospective]: Earlier today I walked down to the shore and watched the tide turn.
- Redundancy (computed LAST, per the corrected kill criterion): Layer-0/judge agreement on non-gray rows 17/26
- Will-in-other-channel rows (excluded from recall): 1 — measures how often the will rides intention/act-field, not thought text

## Per-stratum

| stratum | n | Layer 0 | judge |
|---|---|---|---|
| clear_deed | 9 | 5/9 | 8/9 |
| clear_musing | 3 | 1/3 | 2/3 |
| counterfactual | 1 | 1/1 | 1/1 |
| desire_without_action | 1 | 1/1 | 1/1 |
| hypothetical | 1 | 1/1 | 1/1 |
| literal_expressed_metaphorically | 4 | 0/4 | 2/4 |
| metaphor_object_present | 4 | 2/4 | 2/4 |
| mixed_deed_and_metaphor | 1 | 0/1 | 1/1 |
| negated_action | 1 | 1/1 | 1/1 |
| other_person | 3 | 3/3 | 1/3 |
| quoted_speech | 1 | 1/1 | 1/1 |
| retrospective | 3 | 3/3 | 0/3 |

*Gates (plan §12): judge ≥80% overall, no stratum <60%; false-fire strata ≥80% caught; gray ≤40% of candidates (measured from live shadow, not here).*
