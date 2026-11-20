# Review of Argon's object epistemic loop plan, corrected into a staged plan

## Session timing
- **Session started:** 2026-10-17 08:29:05 UTC
- **Last message before wrap:** 2026-10-17 08:39:21 UTC
- **Wrapped:** 2026-10-17 08:39:22 UTC

## Summary
Travis pasted a plan drafted with Argon for closing Du's object-level hypothesis/belief-revision loop and asked for a review. I checked it against the code and live store, found it right on diagnosis but wrong on several specifics, and wrote a corrected staged plan, `docs/staged/object_epistemic_loop.md`, plus four open decisions.

## Decisions
Opened, not ruled (all on plan `object_epistemic_loop`): D-0462 (archive vs delete the 1459 provenance-empty inferences; recommend archive), D-0463 (show Du his own standing hypothesis plus senses-used on re-encounter, no verdict; recommend yes), D-0464 (do generic-noun routings to scrape/heft/smell/float count as a D-0326 hint), D-0465 (may shadow evaluator outcomes ever feed the action log or frontier; recommend founder-only until validated).

## Findings
- `data/world_substrate.json` (read with utf-8): 534 objects, 1459 inferences, all 1459 with empty `supporting_observations`, all IDs unique; 998 observations, all `look`.
- Contamination is mostly in the garden, not on the shore: `garden_plant_thyme` 427, `garden_item_twine` 175, `garden_item_rain_barrel` 87, `shore_stone_682963` 67, `driftwood_17` 64. Sampled hypotheses are whole-thought dumps about mottainai, Plato, the cat, dreams.
- Mechanism: `nodes/inner_monologue_node.py` `_wants_record_inference` (~L865) and call site (~L5766-5782): bare " it "/" its " relevance latch, 30-minute `last_looked_object()` window, `[], []` provenance, first 280 chars stored.
- `superseded_by` is never set; `buses.object_ledger_line` (L131) never reads inferences.
- Argon's plan used invented feature names (heft, scrape_resistance, porosity_visible, odor, buoyancy "floats_high"). Real keys are in `core/observation.py` (e.g. relative_weight, hardness_impression, floats_or_sinks, buoyancy high/low, scent). Several non-look branches are wood-specific.
- Argon's Phase 4 wrote SUPPORTED/CONTRADICTED verdicts into Du's percept and mutated his InferenceRecord confidence; that conflicts with D-0434 and the decoupled-judge rule. The staged plan makes it a shadow-only evaluator that writes nothing Du sees.
- [INFERRED] The 5-minute look window Argon proposed may suppress most legitimate recording; the staged plan says to measure first.

## Open
1. Rule D-0462 to D-0465 (founder). Next: `/decide-review` or rule them in chat.
2. Phase 1 build (clause-scoped extractor, provenance, dedup/supersession, look-window measurement). It does not depend on the rulings. Next: build in a throwaway worktree, restart-gated.
3. Data hygiene archive of the 1459 inferences, after D-0462 and a dry-run report.

## Warnings
- Phase 1 touches a live store and Du is live; use the write fence, a throwaway worktree, and a store hash canary.
- Do not carry Argon's claim table or Phase 5 tests over verbatim; they use nonexistent feature keys.
- `docs/staged/object_epistemic_loop.md` overlaps `docs/plans/investigative_action_loop_plan.md` (D-0326 closed live advisory); check that plan's trail before touching `close_real_episode` or `frontier`.

## Pointers
- `docs/staged/object_epistemic_loop.md` (the plan), thought T-0094 (promoted to it)
- `core/world_substrate.py`, `core/observation.py`, `core/buses.py`, `nodes/inner_monologue_node.py`, `core/sensorium.py`
