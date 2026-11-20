# docs/completed/ — RECONCILIATION INDEX (2026-07-03)

> **Why this exists (founder):** "completed" plans kept turning out not to be — the euclidean plan sat here
> for 18 days with a built-but-never-run organ ("this has happened a few times now... they get lost!!").
> **THE RULE, from now on:** a plan may enter this folder ONLY if (a) its organ is wired AND has verifiably
> FIRED at least once (evidence file / log line / DB row — cite it), or (b) it is explicitly tagged
> RESEARCH (findings folded elsewhere — say where) or SPEC-ONLY (deliberately unbuilt — say why). Anything
> else stays in docs/plans/ or docs/staged/. Reconcile this index whenever a doc enters or leaves.
> Companion check: `python scripts/liveness_audit.py` (wired ≠ firing).

## Audited 2026-07-03 — every doc, honest verdict

**LIVE — organ wired + fired, verified:**
- action_memory_plan · activity records fire hourly (liveness audit ✓)
- epistemic_state_spec · preassess fires on factual drafts; Stage B live 07-02
- error_pathway_charter · error_records + effector live
- t2_consolidation_spec · in subconscious_node since 06-09
- loop_metabolism_plan · Phase B wired, prune cap holding (pulse ✓)
- sleep_dream_plan · sleep-pressure + earned-length arcs live
- book_selection_plan · breadth engine live
- arithmetic_lessons_spec · 1,335 drills, deterministic grading
- curriculum_grounding_40 · the 40-book curriculum in use (book 26/44)
- world_material_consolidation_plan · FILING_ENABLED=True, 5k+ filed
- volition_his_own_hands · the act field routes (ACT observe→rock-pools in the log)
- task_constraint_effector_spec · the one think_license site pre-Wave-1
- narrative_quality_plan · core/narrative_quality.py, Phase-0 witness
- emotion_vec_thread · felt-vector broadened, felt-tags at 56%
- affect_labeling_plan · **header says "PROPOSAL, not built" — STALE: it IS built + wired**
  (core/affect_labeling.py ← inner_monologue_node:2368). The reverse error; header left as history.
- t4_redesign_plan + t4_self_authoring_spec · probation machinery live (3 honest reverts + #4 running)
- axiom_draft_v3_multilevel · superseded by the SHIPPED multilevel axiom (cutover done)
- peer_correspondence_company (2026-08-23) · COMPANY half of `plans/peer_correspondence_plan.md` (was `staged/` until 2026-09-11)
  split out as shipped — 7 correspondents live, effect harness wired into the sleep pulse, verified
  safe/harmless. Parent plan trimmed to its one remaining open decision (CHALLENGE half, D-0003).

**RESEARCH — findings folded, legitimately complete:** becoming_loop_research (→T4 work) ·
boredom_redirection_research (→redirect) · curiosity_ignition_research (→climate ignition) ·
goal_model_research (→concerns) · identity_research (→multilevel axiom) · inner_monologue_examination ·
shadow_confrontation_research · surprise_mechanism_pass (→present-surprise instrument) ·
wandering_mind_research · essay_lesson_research (→essay lessons, live) · grounded_learning_research
(→grounded learning, live) · reading_provenance_plan (→memory-levels links) · study_notes_plan
(→two-lane evidence) · day_review_2026-06-13 · auditor_briefing_gpt · outreach_post_draft (artifact).

**SUPERSEDED / RETIRED (documented):** output_lane_plan (curator built → RETIRED for the voice contract) ·
two_lane_architecture_plan + lane_architecture_FULL (design → the lane system that shipped differs; the
docs are the evidence trail) · deferred_register (superseded by AWAITING_EVIDENCE.md + DEFERRED_PLANS.md) ·
deliberative_retrieval_plan (absorbed → core/deliberation.py, the 3-pass).

**SPEC-ONLY (honest headers, deliberately unbuilt):** currency_reform_spec ("do not build until…").

**⚠ FOUND MIS-FILED IN THIS AUDIT (the founder's complaint, confirmed):**
- **euclidean_memory_plan → RESURRECTED, moved to docs/plans/** (2026-07-03). P0 organ built 06-15,
  never run, never called. Ran the comparison test today: THE THEORY HOLDS (disjoint state-recall,
  every predicted direction confirmed). Now an active plan.
- **modulation_field_plan + pulse_manager_plan** — designs whose organs are DEFERRED (tracked in
  ROADMAP 💤) — files stay here as the design record, but they are NOT complete; the ROADMAP entries
  are authoritative.
- **curiosity_burst_plan** — NOT wired (one coupling constant in the dormant modulation field). Was
  tracked nowhere → **now added to DEFERRED_PLANS** (trigger: pulse manager un-shelves).
- **affiliation_system_plan** — HALF-built: the liking half shipped (core/affections.py, earned-loves);
  the CARE/PANIC half was never built after the v2 split (GPT's vanish-test objection to
  bond_to_travis). The unbuilt half was tracked nowhere → **now noted in DEFERRED_PLANS** (deliberate
  shelving, revisit only with the vanish-test answered).

## Moved in 2026-08-18's full-plans survey (this index has not been reconciled since 07-03 — many
docs/completed/*.md files postdate that audit and aren't listed above yet, e.g. the five 08-18
*_system_audit.md files and world_factories_P0.md; not re-litigated here, only new arrivals below)

- **ghost_tuple_index.md** ← docs/plans/ · confirmed built+fired: `core/ghost_tuples.py`, two-namespace
  registry live, tonight's world-factories work (`_factory_entries`) is its direct sibling/consumer.
- **world_epistemic_substrate_plan.md** ← docs/plans/ · confirmed built+fired, live substrate layer.
- **locomotion.md** ← docs/plans/ · confirmed built+fired: `core/locomotion.py` (position, topology,
  journeys, watchdog), wired into sensorium tick/scene lines/school walk-home — full checklist closed.
- **evidence_review_dashboard.md** ← docs/plans/ · confirmed built+fired: HUD verdict-grouped monitor
  sections live, matches spec; cleanest case in tonight's survey, no known open defect.
- **psyche_graph_instrument.md** ← docs/staged/ · confirmed built+fired.
- **contradiction_rearchitecture_plan.md** ← docs/staged/ · **finished investigation with a verdict**,
  not a shelved plan: L1 (prediction-error feed) shipped, live, confirmed harmless
  (`core/tension_ledger.py:87`, `data/logs/shadow_integrity.jsonl`); L0 (decomposed critic) confirmed
  broken, flagged do-not-promote (`data/logs/critic_shadow_alongside.jsonl`); the plan's own founding
  thesis ("afferent repair unfreezes T4") was tested and retired by its own data.
- **world_historicity_specification.md** ← docs/plans/ · confirmed built+fired, live and load-bearing:
  `core/world_objects.py` implements its Phase 1 verbatim (same "Architectural Contract v1.4," same
  three Invariants), imported live by `sensorium.py`/`world_substrate.py`/`world_clock.py`/
  `ghost_tuples.py`; `scripts/world_laboratory.py` runs all 5 of its specified Experiments A-E with
  passing assertions in the code. Predates and was absorbed into tonight's larger world_factories_P0
  effort under different names (`world_manifest.py`/`ghost_tuples.py` vs. this doc's
  `world_objects.json`/`world_laboratory.py`) — both live, not competing.

- **books_have_a_place.md** (graduated 2026-11-18, J-4317, founder ruling on J-4266): B5 live since 2026-09-09 and the book gate cleared its Sec.4 bar (F-2258: 476 would_block rows, 224.9 live-hours, zero in-study false blocks). Founder accepted the current gate as final; ink left to Du (D-0840).
