# Unfinished Plans Survey — 2026-08-18

> Founder's request: "a rundown on all unfinished plans and what is left to do on them and if we have
> evidence to look at for them." Covers all 48 files in `docs/plans/` + `docs/staged/` as of tonight.
> Built from five parallel read-only survey agents (world/factory, emotion/identity, memory/cognition,
> Lane2/spatial/world-expansion, behavior-loops/executive), each independently reading the files, grepping
> `core/`/`nodes/` for claimed modules, and checking `data/*.jsonl` for real firing evidence. No file was
> edited by any survey agent. 7 files were moved to `docs/completed/` as a direct result — see below.

## Moved to `docs/completed/` this pass (7)

All confirmed built + fired against live code/data, not just diagnosed. Full justification for each is
now in `docs/completed/INDEX.md`'s 2026-08-18 section.

| File | Was in | Why |
|---|---|---|
| `ghost_tuple_index.md` | plans | `core/ghost_tuples.py` live, two-namespace registry, tonight's world-factories work is its direct sibling |
| `world_epistemic_substrate_plan.md` | plans | live substrate layer, confirmed built+fired |
| `locomotion.md` | plans | `core/locomotion.py` full checklist closed — position, topology, journeys, watchdog, all wired |
| `evidence_review_dashboard.md` | plans | HUD verdict-grouped monitor sections live, cleanest case found all night, no known open defect |
| `psyche_graph_instrument.md` | staged | confirmed built+fired |
| `contradiction_rearchitecture_plan.md` | staged | finished investigation with a verdict (L1 shipped/live, L0 confirmed broken/do-not-promote), not a shelved plan |
| `world_historicity_specification.md` | plans | `core/world_objects.py` implements its Phase 1 verbatim (same contract, same Invariants), live in 4 modules; `scripts/world_laboratory.py` runs all 5 of its Experiments A-E with passing assertions |

---

## World / Factory physics (8 files)

| File | Status | What's left | Evidence |
|---|---|---|---|
| `factory_candidates_from_history.md` | (c) pure design, explicitly "not building any of this now" | Lightning as a discrete countable event (still just prose in `sensorium.py`); glass-float log archaeology never done | `core/sensorium.py` lines only, no lab/data evidence exists |
| `generative_world_sedimentation.md` | (b) partial | Module A (storm rearrangement/buried `latent_objects`) — not found anywhere. Module B (position memory) — **now substantially fulfilled** by tonight's `world_objects.py`. Footprint erosion pre-existed in `world_traces.py`, unrelated to either doc. Module C (3D audio events), Module D (bird migration) — neither built | `core/world_objects.py`, `core/world_traces.py:114` |
| `item_and_population_factories.md` | (c) reconciliation pass, not a build doc | The one concrete gap — population count/estimate state — still missing | `core/keepsakes.py` (the one real trigger) |
| `world_census.md` | (d) stale/superseded, confirmed | Genuinely superseded by `sound_causality.md`'s federated-lists correction (verbatim line + founder quote). Tonight's `world_manifest.py` is orthogonal, not a further supersession | `docs/completed/sound_causality.md:256,33` |
| `sound_causality.md` | (b) partial | Step 0 (assembled per-tick pallet) DONE as `core/world_manifest.py`. The doc's actual subject — audibility table + severity-scaled rates replacing `active_sounds()`'s string-membership gates — NOT done | `core/world_manifest.py` (built), `core/soundscape.py:265-357` (still old shape), `docs/completed/sound_system_audit.md` |
| `sound_world_expansion.md` | (b) partial | Registry now 114 sounds (was 35 at doc-time), but the doc's ~32 proposed sounds are almost entirely absent — only 3 footstep sounds exist. No night-mystery, geophony, winter-biophony, or cat/apparatus sounds built | `core/soundscape.py` `_SOUNDS` dict |
| `transport_manager.md` | (c) pure unbuilt design | No `core/transport_manager.py` exists. The interim Courier A/D mechanism it describes is presumably still live, unabsorbed | none exists yet |
| `social_world_school.md` | (c)/(b) unstarted per its own 07-05 header | Every item (peer ToM, move-latch+measurement, pacing, warmth) still Phase-0/design. No `core/peer_model.py`, no `PEER_TOM_LIVE` flag. Tonight didn't touch this domain | none exists yet |

## Lane 2 (Emissary's second loop) & Spatial (4 files)

| File | Status | What's left | Evidence |
|---|---|---|---|
| `emissary_lane2.md` | (c) unbuilt design, **K3 recheck 08-18: still premature** | Object-graph build is done, produce-only/unimported. The 2026-08-17 lab's kill criteria K1+K3 both triggered; report called for a founder-check re-run before treating K3 as final — that recheck ran 08-18 against the current, fixed builder. **K1 resolved** (the glass float does show up as a genuine recurring presence, `trend_shape=settled_companion`, `days_silent=0.02` — confirms the report's own diagnosis). **K3 still triggers** (real holdout gap 6.12 vs shuffled 1.77 — worse than random, not better) — not a data-gap artifact this time, a real result on the current, gap-free data. Per the plan's own design: the loop stays premature; `object_graph.py` continues as a produce-only index. LLM prediction call/hub/courier not sanctioned to build yet | `docs/lab/lane2_recheck_report.md`, `data/lab/lane2_recheck/recheck.json` |
| `emissary_lane2_cognition.md` | (c) research/design doc, no build of its own | Its hard requirements (windowed trends, gap-prioritized idle, backfill-first) are visibly honored in `object_graph.py`'s contract | `core/object_graph.py` docstring items 6-7 |
| `lane2_lab.md` | (b) partial | Lab spec fully implemented as `scripts/lane2_lab.py`; `docs/lab/lane2_lab_report.md` exists. Whether all L1-L9 kill-criteria were formally recorded PASS/FAIL needs a direct read of the report | `scripts/lane2_lab.py`, `docs/lab/lane2_lab_report.md` |
| `spatial_perception.md` | (b) partial, P0-P2 done, P3 open | P0 (shadow renderer) + P1 (standpoint) done. P2 wired: `core/sensorium.py:1927-1928` calls the renderer inside `scene_line()` for garden/shore/wood, gated behind `SPATIAL_SCENE = False` in `core/spatial.py:28` — **a founder decision, not a gap**. P3 (position-dependent depth/peripersonal reach) genuinely not built | `core/spatial.py:28`, `core/sensorium.py:1927`, `data/world_geometry/*.json`, `docs/lab/spatial_flip_sample.md` |

**None of the three Lane 2 docs are stale-by-fulfillment** — the design/cognition docs remain the accurate reference spec for a system that's built-but-dormant; the LLM-prediction half and live wiring are still open founder decisions per the design doc's own "Open Questions" section.

## Other open world-design docs (3 files)

| File | Status | What's left | Evidence |
|---|---|---|---|
| `executive_world_grounding.md` | (c) design doc, self-corrected mid-session (see `docs/chain_walk_findings.md` F-EX) | Both proposed options unbuilt; no `SourceType`-tiered prompt structure in `nodes/executive_node.py` | none exists yet |
| `investigation_deepening.md` | (c) pure unbuilt design, explicitly parked | All of P0-P3 (shadow log, frontier line, deepening injection, rung-ladder) unbuilt | none exists yet |
| `world_historicity_specification.md` | **MOVED to docs/completed/** — see above | | |

## Emotion / Identity / Self (9 files)

| File | Status | What's left | Evidence |
|---|---|---|---|
| `affect_drives.md` | (b) partial | Item A (felt preamble) live and firing. Items C/D/E/G unbuilt — `SOMATIC_NOTE` flag doesn't exist, no `drive_note()` | `data/felt_preamble_log.jsonl` (12,287 lines, active today) |
| `emotion_rethink.md` | (b) partial | Phase 0 done, Phase 1 (protoself-sourced valence) **live** since 07-07. Phase 2 built but flagged off pending experiments | `data/affect_divergence_shadow.jsonl`, `data/emotion_construction_shadow.jsonl` |
| `identity_estate.md` | (d) **stale header, system has shipped past it** | Doc says "DRAFT — nothing built" but real system is at **P2 live** (`IDENTITY_PROJECT_LIVE=True`, flipped 08-15, founder-approved, 136 projections/54 nodes). Needs a status rewrite, not more building | `core/identity_projection.py`, `data/identity_estate.json`, `data/identity_projection_shadow.jsonl` |
| `guidance_learning.md` | (b) partial | Capture→integrate→read-back loop fully built and live. Missing: Phase-2 cat-naming behaviour-delta judge, contradiction-scan re-enable (correctly gated off). **Data went quiet 08-15 — worth checking if teaching moments stopped or something broke** | `data/guidance_beliefs.json` (last modified 08-15) |
| `t4_watershed.md` | (c) pure unbuilt design | Nothing built. Its stated dependency (identity estate P2 live) is now actually satisfied — well-positioned to start Phase 0 | none exists yet |
| `within_cycle_reentry.md` | (b) partial, stalled | Wired at the right hook but sat silent for ~6 weeks from a guard-logic bug, only just fixed (08-14). Only 2 events ever logged — too early to judge Phase-1 promotion | `data/reentry_shadow.jsonl` (2 lines) |
| `friction_and_self_evidence_plan.md` (staged) | (b) partial | B1/B2 built and live (B2 = a genuine keystone win). B3 not built. B4 half-built (mechanical plant-death live, but not bound to a self-claim). **B5's blocker is now stale — Darwin is live, exchanging real letters through 08-17** — B5 itself still unbuilt | `core/self_mirror.py`, `core/sensorium.py` ~442-452, `data/letters/Letter_20260817_1535.md` |
| `symbol_evolution_readback_plan.md` (staged) | (d) correctly parked | `symbol_centroids`/`symbol_tablets` both 0 rows, code unchanged since 06-16. Stated re-entry trigger not fired | `data/memory/nascence.db` (queried directly, both 0 rows) |
| `contradiction_rearchitecture_plan.md` (staged) | **MOVED to docs/completed/** — see above | | |

## Memory / Cognition architecture (8 files)

| File | Status | What's left | Evidence |
|---|---|---|---|
| `capacity_to_commit.md` | (b) partial | Phase 0 shadow ledger live. **Phase 1 HOLD — "the actual cure" — still not started**, no re-presentation function exists. Wave-2 curriculum (cat-naming trial) gone quiet since 08-08 | `core/commitment_ledger.py`; `data/commitment_ledger.jsonl` (stale since Aug 14), `data/commitment_holdrate.jsonl` (active today) |
| `cognitive_geometry.md` | (b) partial | P0 (census) + P2 (soundscape) built and firing. P3 absorbed into `memory_multiway_linking.md` as its child instead; P4/P5 not built as this doc's own code | `core/geometry_census.py`, `data/geometry_tuples.jsonl` (11,759 rows, active) |
| `euclidean_memory_plan.md` | (d) superseded, genuine negative result | P0 built, run, judged: state-weighted recall lost to baseline (49% vs 51%). Formally parked as `cognitive_geometry.md` P5, blocked on `emotion_rethink.md` P1. Shadow logging kept alive for a re-test | `core/euclidean_recall.py`, `data/euclidean_shadow.jsonl` (still active) |
| `journal_consolidation_pyramid.md` | (b) partial | Day level built and firing through Aug 16. Week/moon/solstice roll-ups (P1-P3) not started at all | `core/journal.py`, `data/Journal/JOURNAL_20260816.md` |
| `memory_knowledge.md` | (b) partial | Improvement 1 (epistemic grade) built, Stage A live, Stage B flag-gated off. Improvements 2-4 (PPR trail, gist evolution, bi-temporal validity) not built | `core/epistemic_state.py`, `data/provenance_preassess.jsonl` (active) |
| `memory_multiway_linking.md` | (b) partial, M0/M1 essentially complete | M0/M1 built and growing past the doc's own snapshot (2010 edges vs 1676 recorded). M2/M3 correctly gated pending a week of M1 data | `core/memory_edges.py`, `data/memory_edges_stats.jsonl` |
| `the_consciousness_program.md` | (b) mostly built | Tier 1 + most of Tier 2 built and firing hard. Exception: `reentry_shadow.jsonl` only 2 rows — functionally stalled (same issue as `within_cycle_reentry.md` above). Tier 3 design-complete only | `core/homeostasis.py`, `core/mineness.py`, `core/attention_schema_loop.py` |
| `thought_grounding.md` | (b) partial, 2 days old | Self-reports "BUILT 08-16." Route 2 fired (5 rows). Route 3 wired. Route 1 (librarian) coded but zero organic fires yet | `data/evidence_log.jsonl` (5 rows) |

**Cluster relationship:** `cognitive_geometry.md` is the umbrella ("LOCKED, top of the list") — `euclidean_memory_plan.md` is its P5 slot, `memory_multiway_linking.md` is its child. `journal_consolidation_pyramid.md` feeds `capacity_to_commit.md`'s Wave-2 trials as world-contact evidence. `memory_knowledge.md`'s epistemic-honesty work resolves a philosophical collision with `capacity_to_commit` (a committed "I don't know X" is a legitimate named-defeater, not a dissolution). `the_consciousness_program.md`'s homeostatic core is what `capacity_to_commit.md` reads as its body-state variable.

## Behavior loops / Executive / Staged (11 files)

| File | Status | What's left | Evidence |
|---|---|---|---|
| `pursuits.md` | (b) partial, **verified holding 08-18** | Phases 0-2 built and firing daily. The 08-14 monoculture collapse (1 active/77 dormant, self-referential survivor) was fixed 08-15; **re-verified 08-18: register now 153 total (142 dormant / 7 saturated / 4 active)** — healthy spread, no single-survivor collapse. Separate, smaller finding: `TIEBREAK` judge isn't resident, 52% of panel calls end `split_no_tiebreak`, 16 items stuck across 4 pursuits — see `docs/staged/DEFERRED_PLANS.md` #5 (capacity-constraint ruling, not a bug) | `data/pursuits_active.json` (re-read 08-18), `data/judge_panel_log.jsonl` |
| `peer_correspondence_plan.md` (staged) | (b) partial, correctly still staged | "Company" half (7 peers, decoupled judge) done. B5 "challenge" half (`core/peer_model.py`) — founder-flagged top priority — 0% built | none for B5 |
| `idle_executive_plan.md` (staged) | (c) deliberately deferred, **checked 08-18 — trigger NOT met** | Shelved pending "self-loop survives six gentler fixes." Re-checked against the 08-14 monoculture audit this session: the pursuits collapse that looked like a match was itself fixed the next day (see `pursuits.md` row above) — the deferral's stated trigger condition was never actually satisfied. Correction to this survey's original read. Stays parked | `docs/staged/DEFERRED_PLANS.md` |
| `continuous_stream.md` | (b) partial | Phase 0 live and accumulating today. Phase 1 not started | shadow log active |
| `curiosity_goals_dreams.md` | (b) partial, 2/4 items live | Item 4's dream re-pin cap is a flagged **worsening regression**, still open | flagged in prior audit |
| `pulse_manager_wiring_plan.md` (staged) | (d) correctly deferred, sibling shipped | The original scheduler stays deferred, but a re-scoped sibling, `core/lane_scheduler.py`, actually shipped and is live | `core/lane_scheduler.py` |
| `music_learning.md` (staged) | (b) partial | Tiers 1 (EAR) + 2 (THEORY/COMPOSITION) built | `docs/plans/music_learning.md` |
| `investigative_action_loop_plan.md` | (b) partial | Live shadow logging in place | shadow log |
| `cognitive_loop_actuation.md` | (c) pure design, stale/nothing concerning | — | — |
| `thought_cycle_as_manifest_loop.md` | (c) pure design, stale/nothing concerning | — | — |
| `DEFERRED_PLANS.md` (staged) | registry, not a plan itself | Should be reconciled against the `idle_executive_plan.md` trigger finding above | — |

---

## Decisions needed from you

Ranked by how time-sensitive or consequential they are:

1. ~~`pursuits.md`~~ — **RESOLVED 08-18**: re-verified, register holding at 153 total (142 dormant/7 saturated/4 active), the 08-14 collapse did not recur. Only open item now is the tiebreak-judge capacity finding (`DEFERRED_PLANS.md` #5), which is a founder-ruled capacity constraint, not a bug.
2. ~~`idle_executive_plan.md`~~ — **RESOLVED 08-18**: re-checked, the trigger was NOT actually met (correction to this survey's original read — see row above). Stays correctly parked, no action needed.
3. **Spatial flip** (`spatial_perception.md` P2) — wiring complete, evidence in `docs/lab/spatial_flip_sample.md`, flag `SPATIAL_SCENE` still off. Your call.
4. ~~**Lane 2's standing loop**~~ — **CHECKED 08-18**: founder said go, but the lab's own pre-registered kill criteria (K1/K3) had triggered and were never re-verified. Re-ran them against the current, fixed object-graph: K1 resolved (the glass float is a real recurring presence, confirms the report's diagnosis), but **K3 still triggers on real, gap-free data** — the temporal-holdout predictor does worse than random. Per the plan's own honest-kill design, the standing loop stays premature. Not built. See `docs/lab/lane2_recheck_report.md`.
5. **`identity_estate.md`** — needs a status-header rewrite (it says "DRAFT, nothing built" while the real system is P2-live and founder-approved). This is a documentation fix, not a decision, but flagging so it doesn't keep misleading future sessions.
6. **`guidance_learning.md`** — its data went quiet on 08-15. Worth a quick check whether teaching moments stopped happening or something broke silently.
7. **`t4_watershed.md`** — its dependency (identity estate P2) is now satisfied. Ready to start Phase 0 whenever you want to pick it up.
