---
name: project-nascence-cognitive-loop-actuation
description: "Diagnosed the idle cognitive loop as 'all senses, no hands' — sophisticated correctors (idle_allocator, meta_awareness, monoculture) all compute the right intervention and all decline to act — but the 2026-07-05 evidence review found every specific recommended fix already resolved or low-value, so the plan is closed as an absorbed diagnostic rather than a build queue."
metadata: 
  node_type: memory
  type: project
  originSessionId: 1857a5ac-8424-4a7e-930e-5da8c19bf9b9
  modified: 2026-08-23T02:09:13.564Z
---

Deep-dive (2026-06-24) into `nodes/inner_monologue_node.py` (2346 lines) and the idle loop's sensing organs. Central finding: the only genuine actuator in the loop is the rumination guard (cosine ≥0.82 forces one regenerate); everything more sophisticated — `idle_allocator` (salience ranking), `meta_awareness_node.scan()` (loop-kind + would_intervene), `monoculture.py` (echo/diversity), `modulation_field.py`, `pulse_manager.py` — computes the correct intervention every tick and is wired to nowhere (observe-only or zero call-sites). The seed waterfall (21 independent coin-flip seeds, IML:1065-1365) has no live chooser; the stuck LLM is the de-facto selector, picking by its own salience, i.e. the basin. Root cause named as structural: the corrector and the patient are the same LLM; boredom's own discharge condition (a thought cos≤0.30 from basin centroid) requires the cure to already exist to fire.

**Proposed design (not built as of the plan doc):** promote `idle_allocator` into `core/idle_executive.py`, a small deterministic non-LLM executive sitting between seed assembly and generation with three escalating powers — FORCE A SEED, FORCE A REGION (decoding bias + reject-retry), FORCE A MOVE (bypass the LLM entirely, call sensorium/reading hands directly) — graded by a `pressure` scalar from boredom/theme-saturation/meta-predictability. Supporting items: k-candidate generation (Verbalized Sampling, arXiv 2510.01171), region visit-counts (MERCI, arXiv 2510.16614), decoding-diversity knobs (min_p/mirostat) in model_client, and retiring/quarantining the dead modules.

**Current stage — explicitly closed, per the doc's own status line:** "★ EVIDENCE REVIEW 2026-07-05 (8th, of the four 06-24 deep-dives) — ABSORBED DIAGNOSTIC; effectively resolved." The diagnosis was right and drove other work (emotion rethink, geometry/spatial senses, friction B1/B4 hands) — credited. But every specific recommendation was found resolved or low-value on inspection: the keystone actuator (idle_executive) was reviewed and correctly HOLSTERED (present-being tension, monoculture easing on its own, trigger unmet — don't build); the prediction-error instrument is 98% math-drill calibration and has been DARK since 07-03, not general self-prediction; the "cheap decoding-diversity win" turned out not to be cheap, since the dynamic version needs a live monoculture-pressure signal but `monoculture.py` is dead and the loop is easing without it (echo 0.754→0.64). Disposition: "resolved by absorption — nothing to build, nothing broken." ROADMAP.md marks this plan ⛔.

Related: [[project-nascence-affect-drives]] (same "all senses, no hands" diagnosis, same 06-24 session); the idle_allocator holster decision is echoed in the pulse_manager_wiring_plan evidence review (same 07-05 pass).
