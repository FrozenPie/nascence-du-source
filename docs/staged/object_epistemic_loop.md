# Object Epistemic Loop — clean hypotheses, read-back, real tests, shadow-only evaluation

**Status:** 🟠 STAGED — drafted 2026-10-17 from Argon's plan (pasted into session 03e3d80b), corrected against the code and the live store. Not ruled, not built. **Parent thought:** T-0094. **Related:** [investigative_action_loop_plan](../plans/investigative_action_loop_plan.md) (D-0326 closed Phase 2 / live advisory), [world_store_write_fence](../plans/world_store_write_fence.md), `feedback_no_readout_error_through_consequence` (D-0434).

```plan-state
stage: designed
phase: staged draft; nothing built; Phase 1 is the only phase safe to start without a founder ruling
verified: 2026-11-14
evidence_read: 2026-10-18
next: Next boot carries the switch; J-2387 reads the D-0464 defeater after 7 live days
open_decisions: D-0751
cluster: 7
```

## Current State — verified 2026-11-14
- **2026-11-14**: J-3844 (D-0738): core/world_knowledge.py and core/induction_drill.py (plus its only importer test scripts/_test_induction_drill_j2649.py) archived by git mv to scripts/archive/, history kept; commits b24a564a and 45ed1fdc on branch jobrun/x4_object_epistemic_loop, merge is restart-gated. I-0128 rule-induction drill is archived, not scheduled; restore by git mv back to core/ if revived.

- **2026-11-14** (F-4490): J-2387 post-boot read: switch on since 2026-10-18 boot; 1 objtest FIRE in 18,097 thoughts, rate not above baseline, but that FIRE was a metaphorical weigh (D-0478 defeater clause 2). Decision opened for Travis; recommendation keep ON plus figurative-object guard.
- **2026-11-07** (F-4309): J-3440 built (restart-gated, branch jobrun/wh_7): deontic-frame exclusion in extract() and intervention_test(), default on with kill switches; 15 of 195 replayed hits were intentions; opened D-0695; follow-ups J-3692, J-3693.

- **2026-10-30** (F-3290): J-2524 built intervention_test field on object hypotheses: deterministic do/withhold/observe candidates from hand families, gated off (NASCENCE_INTERVENTION_TEST), no consumer, restart-gated; store too small to judge coverage (3 of 3, n=3)
- **2026-10-18** (F-3114): J-2411: Layer-1 form-key fallback removed, get_generative_state reads physical_state only (jobrun/object_epistemic_loop f351b29a, restart-gated); migrated-store copy prose 3228/3228 byte-identical, injected Layer-1 keys reach nothing (538/538 gen state, 3228/3228 prose)

- **2026-10-18** (F-3105): J-2405: D-0480 A_strict built restart-gated (jobrun/object_epistemic_loop 7d10726c): branch/root form tests read the structure head word; 3228-cell store check changes only ec5091 inspect_end section irregular->round + 2 feature sets; D-0479 read must name it as expected
- **2026-10-18**: D-0480 (A_strict head-word match, build before next boot) and D-0482 (study/wood ledger line waits for J-2382's read) ruled by travis 2026-10-18 (decide-review).

- **2026-10-18** (F-3100): J-2396: NASCENCE_GENERIC_OBJECT_TESTS default ON (code default, env 0 forces off; commit 989bf1a4 on jobrun/object_epistemic_loop), restart-gated; post-boot read J-2387.
- **2026-10-18** (F-3099): J-2394: shore + garden generic looks now carry object_ledger_line (jobrun/object_epistemic_loop 2bc15efd; NASCENCE_GENERIC_OBJECT_LEDGER default on per D-0475, off byte-identical; rows gain branch/would_ledger/base_chars); ledger median 245 chars on a 143-char look; study shelf holds most re-looked objects, scope question D-0482

- **2026-10-18** (F-3096): J-2390: driftwood structure mismatch (F-3092) has reached no percept yet (1012/1012 observations are looks); head-word fix changes 1 unseen inspect_end line on ec5091 (probe 865e4428); D-0480 open (fix known objects before next boot vs new spawns only)
- **2026-10-18**: D-0475, D-0478, D-0479 ruled by travis 2026-10-18 (decide-review): generic looks also append object_ledger_line (J-2394 build); NASCENCE_GENERIC_OBJECT_TESTS goes ON at the next boot (J-2396); the wood form-key migration applies in the same founder-chosen Du-down window as J-2373's archive (J-2389).

- **2026-10-18** (F-3091): J-2388: wood form keys made Layer-2 (jobrun/object_epistemic_loop 7f78a100; get_generative_state reads physical_state, Layer-1 fallback until applied); migrate_wood_form_keys.py dry-run 8 keys on 4 objects, prose 3228/3228 byte-identical on a copy; apply held in D-0479 (J-2389); F-3092 priors vocabulary mismatch -> J-2390
- **2026-10-18** (F-3085): J-2376: Phase 3 built restart-gated (jobrun/object_epistemic_loop f03dbe02; NASCENCE_GENERIC_OBJECT_TESTS default off, off byte-identical; float only shore + garden barrel with water; Layer-1 counterfactual 45/45); replay baseline 2 willed tests in 44196 thoughts (F-3086)

- **2026-10-18** (F-3079): J-2375: Phase 2 read-back built restart-gated (branch jobrun/object_epistemic_loop 9c9ff7c2+b94f5432; switch NASCENCE_LEDGER_HYPOTHESIS_READBACK default off, would_readback shadow field); 0 of 1476 live inferences eligible, only driftwood_17 look calls the ledger (F-3080, D-0475)
- **2026-10-18** (F-3073): J-2359: Phase 1 built restart-gated (branch jobrun/object_epistemic_loop f61777a2; clause gate, provenance, dedup/supersession; 0 of 43777 logged thoughts pass); O1 archive tool shipped, dry-run 1476/1476 provenance-empty, real apply held in J-2373

Checked directly against code and `data/world_substrate.json` (read with `encoding="utf-8"`):

- **534 objects, 1459 inferences, 1459 with `supporting_observations == []`** (100%). All 1459 inference IDs are unique.
- **998 observations, all `action == "look"`.** No scrape / pick_up / inspect_end / smell / float_test has ever been recorded by the generic path.
- **The contamination is mostly NOT on the shore.** Top holders: `garden_plant_thyme` 427, `garden_item_twine` 175, `garden_item_rain_barrel` 87, `shore_stone_682963` 67, `driftwood_17` 64. Sampled hypotheses are whole-thought dumps (first 280 chars) about mottainai, dreams, Plato, regret, the cat — not claims about the object. Argon's examples were all shore stones; the fix must cover garden objects.
- Mechanism confirmed: `nodes/inner_monologue_node.py` `_wants_record_inference` (~L865) matches any cue word in the whole `thought + intention`; call site (~L5766-5782) uses `last_looked_object()` with the default 30-min window, a relevance gate that accepts a bare `" it "`/`" its "`, and passes `[], []` as provenance. The stored text is `hyp[0][:280]`, the whole thought, not the claim.
- `superseded_by` exists on `InferenceRecord` but nothing ever sets it; `record_du_inference` / `record_inference` only append.
- `buses.object_ledger_line` (~L131) reads observations only; it never reads inferences. Standing hypotheses are write-only.
- `core/world_knowledge.py` has a `_KNOWLEDGE_BASE` of `DiagnosticEntry` rows across several domains, but nothing in the live path calls it.

## What Argon's plan got wrong (do not carry these over)

1. **Invented feature vocabulary.** `heft`, `scrape_resistance`, `particle_shed`, `porosity_visible`, `odor`, `buoyancy: "floats_high"` etc. do not exist. Real keys in `core/observation.py`: look → `colour, shape, bark_presence, grain_visibility, surface_damage, size, overall_condition`; pick_up → `relative_weight, balance_point, surface_texture, moisture_impression, structural_flexibility`; inspect_end → `cross_sectional_geometry, annual_ring_visibility, fiber_structure, break_pattern`; scrape → `internal_grain_color, hardness_impression, fiber_structure, resin_presence`; float_test → `floats_or_sinks, orientation, water_absorption_rate, buoyancy` (`high`/`low`); smell → `scent`; plus `_CLASS_EXTRAS` (hardness, hollowness, porosity, chambering, …) only when present in `physical_state`. Several of these branches are wood-specific (stone `inspect_end` would say "annual ring visibility"), so "all 9 classes support all 6 actions" is only true in the sense that the call does not crash.
2. **Phase 4 is a readout.** Writing `SUPPORTED/CONTRADICTED` and "testing showed otherwise" into Du's percept, and adjusting his own `InferenceRecord.confidence` from a table we wrote, violates D-0434 (error through consequence only, no readout) and the decoupled-judge rule (every subsystem judged by something other than itself — here a grader we author would be mutating the thing it grades).
3. **Phase 3 adds verbs without a D-0326 ruling.** Keyword-routing "float / scrape / heft / smell" in every place is the world answering if he asks — consistent in spirit with the 08-14 comment in `sensorium._shore_act` — but the plan never checks affordance text in garden/study, and `float_test` has no prose or caller anywhere and needs a real water-source check.
4. **Small:** `describe_and_observe` returns `str`, not `Optional[str]`, and already records features for any action (only the *prose* is look-field-shaped); inference IDs use `int(time.time())` (collision-prone within one second); quoted line numbers are off; the archive step touches a live store and must respect the write fence; a 5-minute look window may suppress most legitimate recording (see Phase 1 measurement).
5. **Overlap.** `epistemic_affordance_advisor.py` / `investigative_action_loop_plan.md` already own the investigation loop under D-0326. Rewiring `close_real_episode` and `frontier.attach_finding` belongs in that plan's decision trail, not a patch list.

## Guardrails (all phases)

- Layer 1 (`causal_state`, `causal_history`) is never read by anything that produces text Du sees or that scores his hypotheses. Evaluators read only Layer 2 via `observation.py`'s existing output, or Layer 3.
- No imperatives, no "next test", no verdict language in anything Du perceives (D-0326, D-0434).
- Every new write goes through the write fence (`profile.guard_path`); new hooks re-raise `profile.NonLiveWriteError`, swallow everything else.
- Each behavior behind an env kill-switch, default off until its phase is ruled: `NASCENCE_STRICT_INFERENCE_GATE`, `NASCENCE_LEDGER_HYPOTHESIS_READBACK`, `NASCENCE_GENERIC_OBJECT_TESTS`, `NASCENCE_EPISTEMIC_EVAL_SHADOW`.
- Build and test in a throwaway worktree with the lab_env isolation; never touch the shared tree with git state commands; restart-gated (Du is live).

## Phase 1 — Valid, provenance-bearing, supersedable hypotheses (build first, alone)

Goal: stop recording philosophy as object hypotheses; record real ones with provenance.

1. **Clause-scoped extractor** replacing `_wants_record_inference`'s whole-text match. Split `thought + intention` into clauses (reuse the pattern in `core/garden_knowledge.py::_clauses`, J-1524). A hypothesis needs, in one clause or an adjacent pair: (a) an object anchor taken from the target object's own class/name tokens — **no bare pronouns**; (b) an epistemic cue (the existing `_INFER_HIGH/LOW` lists); (c) a claim about kind, origin, material or physical property, not a feeling or metaphor. Store only the matched 1-2 clauses (≤240 chars), not the thought prefix. Anchors must be derived per object class so garden objects (thyme, twine, rain barrel) work — not a shore-only noun list.
2. **Target resolution:** keep `last_looked_object()` but make the window a tunable constant. **Measure first** (replay the existing thought log against look timestamps) to pick a value; do not hard-code 300 s.
3. **Provenance:** pass the object's last N observation IDs as `supporting_observations` (and `[]` knowledge for now).
4. **Dedup + supersession in `record_du_inference`:** if the latest active inference has near-identical text (Jaccard ≥ 0.75), refresh it instead of appending; if the new one differs and the prior is still active, set `prev.superseded_by = new.inference_id`. Make inference IDs collision-safe (suffix a counter).
5. **Data hygiene (separate job, after the gate is verified):** back up `data/world_substrate.json`, archive the inferences failing the new gate to `data/archive/contaminated_inferences_pre_fix.jsonl`, via the write fence. Dry-run report first (count by object, what survives).

Verification: negative cases built from sampled live rows (mottainai/Plato/cat thoughts attached to thyme, stone) record nothing; positive cases ("this pale stone might be pumice") record one inference with provenance; replay over the stored thought history gives a before/after counts table.

## Phase 2 — Read-back of his own hypothesis on re-encounter (no verdicts)

In `buses.object_ledger_line`, after the observation summary, append his latest non-superseded hypothesis in his own words plus **which senses he has used so far** (from `observation.action` values), e.g. "Earlier you wondered about this: \"…\"; so far you have only looked." No status field, no "held up / contradicted", no suggestion. Raw later observations are already shown by the existing feature list, so he can see for himself whether they bear on it. Same for `world_ledger_ask`. This is memory read-back (cf. `garden_knowledge.recall_for_place`, J-1524), not a hint. Gate: ruling O2.

## Phase 3 — Generic physical tests (only after a D-0326 ruling)

- Extend `describe_and_observe(object_id, action)` with short prose for the real keys of each action (reading `relative_weight`, `hardness_impression`, `scent`, `floats_or_sinks`, …); keep existing recording behavior. First extend `observation.py` so non-wood classes return class-appropriate keys for `inspect_end` / `scrape` rather than wood anatomy.
- Replace the `driftwood_17`-only branch in `sensorium._shore_act` (~L1895-1984) with a helper that resolves the object (`find_object_at`, then a generic-noun fallback via `last_looked_object`) and routes through `describe_and_observe`, for the places that have a plausible object and, for `float_test`, a real water source. `driftwood_17` becomes just one object, keeping its authored prose for scrape/inspect/smell/pick_up.
- No new affordance text anywhere. Gate: ruling O3.

## Phase 4 — Shadow-only evaluator (never reaches Du)

- New `core/epistemic_eval_shadow.py`: given an inference and the object's Layer-3 observations, emit `{inference_id, object_id, outcome: CONSISTENT | INCONSISTENT | INCONCLUSIVE, matched_features, matched_knowledge_ids}` to `data/epistemic_eval_shadow.jsonl`. Claim table built **only from real `observation.py` keys and values** and cross-checked against the `_KNOWLEDGE_BASE` entries; start with a small set of unambiguous claims (floats/sinks, hollow/solid, resin/no resin, soft/hard) rather than species/rock names.
- **Writes nothing** to `InferenceRecord` (no confidence changes, no `epistemic_state`), nothing to `object_ledger_line`, nothing to `frontier`. It is an instrument for the founder and the doctor rounds, per the decoupled-judge rule.
- Reads: a `plan-shadow-read` spec once rows accrue (how often do real tests exist at all; agreement with hand labels on a sample).
- Deferred, each needs its own ruling: feeding outcomes to `close_real_episode` (fixes the INCONCLUSIVE-heavy action log) and to `frontier.attach_finding`.

## Phase 5 — Tests (hermetic, `core.lab_env.isolate()`, import core before lab_env)

- **Layer-1 counterfactual:** two objects with identical Layer 2, different Layer 1 → byte-identical prose for every action, identical ledger lines and identical shadow evaluator outcomes; then change only Layer 2 on one and assert only the Layer-2-dependent actions diverge. (Argon's idea, kept.)
- **Contamination suite** from sampled live rows (shore and garden), and the positive/negative gate cases from Phase 1.
- **Read-back** test asserts the ledger line contains his words and the senses-used summary and contains none of: "supported", "contradicted", "test", "try", imperative verbs.
- **Live-store canary:** hash `data/world_substrate.json` before and after (see the 10-04 live-store-leak lesson).

## Open questions for the founder

- **O1.** Archive vs delete the 1459 provenance-empty inferences (recommend archive, dry-run report first).
- **O2.** Is showing Du his own standing hypothesis plus senses-used on re-encounter acceptable under D-0326/D-0434? (Recommend yes: it is his own words and raw sensory history.)
- **O3.** Does letting generic nouns ("the stone", "the shell") route to scrape/heft/smell/float in every place count as a hint under D-0326? Which places have a water source for `float_test`?
- **O4.** Should shadow evaluator outcomes ever be allowed to touch the action log / frontier, or stay a founder-only instrument?

## Suggested sequence

Phase 1 (+ measurement of the look window) → hygiene dry-run → rulings O1-O4 → Phase 2 → Phase 3 → Phase 4 shadow → read the shadow → only then discuss anything beyond it. Phase 5 tests grow alongside each phase.
