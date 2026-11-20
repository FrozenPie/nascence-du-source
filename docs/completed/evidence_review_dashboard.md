# The Evidence-Review Dashboard — a plan of plans (2026-07-05)

> A multi-step plan whose *subject* is the other plans. Born from the 12-plan evidence review (2026-07-05):
> instead of a static verdict table that rots, make the review a LIVING instrument on the HUD — every plan's
> primary monitor visible, grouped by its **evidence verdict**, so "is it working?" is answerable at a glance
> and re-answerable every day. The review's own lesson made concrete: *we build mechanisms and don't watch
> them* — so this plan's deliverable is watching.

## 0. THE VERDICT TABLE (the review's result — the source of truth for the groups)
| Plan | Verdict | Group | Primary monitor |
|---|---|---|---|
| euclidean_memory | FAILED gate — state-recall ties baseline (49/51); blocked on emotion-rethink | **failing** | `euclidean_shadow.jsonl` |
| contradiction_rearch | FAILED gate — decomposed critic 0% precision; thesis retired | **failing** | `contradiction_ledger_log.jsonl` |
| symbol_evolution | Structurally unreachable — parked for replan | **failing** | `symbol_recurrence.jsonl` |
| memory_knowledge · Stage B | Mis-targeted → off-until-observable (enacted) | **failing** | `epistemic_stageb_shadow.jsonl` |
| friction_self_evidence | Healthy — advance B1 (detector precise 2/2) | **ready** | `self_implication_conv_shadow.jsonl` |
| curiosity_goals_dreams | Healthy — build Item 4 (dream re-pin, worsening regression) | **ready** | `curiosity_worth_log.jsonl` |
| guidance_learning | Healthy — promotes "commit to a direction" to belief #1; build the judge | **ready** | `guidance_integration_log.jsonl` |
| capacity_to_commit | Disease measured (549/546); FIRST cure-signal (hold-rate 0→17%) | **ready** | `commitment_ledger.jsonl` |
| peer_correspondence | Un-archived — company half done, CHALLENGE half (B5) unbuilt; effect tiny | **ready** | *(needs `compare()` → log — Step 3)* |
| idle_executive | Passes gate but holstered (present-being); payload `actual` never captured | **hold** | `logs/idle_shadow.jsonl` |
| pulse_manager | Correct hold — no contention; canary improving (t4-block 91%→26%→~0) | **hold** | `sleep_pressure_log.jsonl` |
| cognitive_loop_actuation | Absorbed diagnostic — resolved; prediction-error 98% math + dark | **hold** | `prediction_error_log.jsonl` |
| social_world_school | Healthy domain, plan unstarted; Item 2 counter unbuilt | **hold** | *(needs the heeded/ignored counter — Step 4)* |
| memory_levels (Improvement) | Phase-1 LIVE, healthy | active | `memory_levels_shadow.jsonl` |

*Un-reviewed / current build wave (stay in `active`/`staged`):* cognitive_geometry, spatial_*, emotions_*,
consciousness_program, affect_drives, continuous_stream, within_cycle_reentry, music_learning, psyche_graph.

## 1. THE HUD REORGANISATION (the build)
Add three verdict-groups to the HUD's Plan Monitors, each its own section with its own graphs, alongside
the existing `active`/`staged`:
- **★ Ready to Progress** — the healthy plans with a named next step (friction·curiosity·guidance·capacity·peer).
- **⚠ Failing their Gate** — evidence-negative; graphs KEPT so the failure stays visible, not hidden
  (euclidean·contradiction·symbol_evolution·epistemic Stage B).
- **⏸ Correct Holds** — parked-correctly / resolved (idle_executive·pulse_manager·cognitive_loop·social).

## 2. STEPS
- **S1 — server: dynamic grouping + regroup (DONE 2026-07-05).** `load_monitors_index` → `setdefault(group)`
  so any group name works; MONITOR_REGISTRY entries re-tagged to ready/failing/hold; `epistemic_stageb` card
  added → `epistemic_stageb_shadow.jsonl`.
- **S2 — client: the three new sections (DONE 2026-07-05).** `index.html` grids `monitors-ready/failing/hold`
  + headers; `app.js` iterates the new groups.
- **S3 — peer monitor (DONE 2026-07-05).** `peer_metrics.snapshot()` appends the compare() deltas to
  `peer_effect.jsonl` once per sleep (wired in the sleep hook); HUD card `peer_correspondence` → **ready**.
  Closes "the judge built 06-21, never run/logged." Verified: outward +0.28 / inward −0.38 / peer-share 0.5%.
- **S4 — social heeded/ignored counter (DONE 2026-07-05).** `core/social_moves.py` — observe-only tracker
  wired at the world-call consumer (`inner_monologue:1036`): a call fires inside → pending; goes outdoors
  within 25min = HEEDED, window passes still inside = IGNORED → `social_moves.jsonl`. HUD card
  `social_world_school` (heeded 1/0 line) → **hold**. Verified state-machine (heeded/ignored/rate).
- **S5 — the hold-rate monitor (DONE 2026-07-05).** `commitment_ledger.holdrate_snapshot()` computes
  reaffirmed/(formed+reaffirmed) over the recent window → `commitment_holdrate.jsonl` once per sleep; HUD
  card `capacity_holdrate` → **ready** (the north-star as a first-class line). Verified: currently **0.22**
  over the last 400 events (up from the 0→17% half-split — climbing).
- **S6 — MAINTENANCE RULE.** When a plan's verdict changes (a failing plan's gate flips green; a ready plan
  ships; a hold's trigger fires), move its registry entry to the new group AND update §0. This file is the
  index; the HUD is its live face. Re-run the review's grading passes (`euclidean_grade.py`, `critic_grade.py`)
  to move a plan OUT of `failing`.

## 3. THE BUILD QUEUE (surfaced by the review — the actual work, none urgent)
Ranked for the NEXT session (2026-07-05, founder calls + leverage):
1. **★ PEN-PAL CHALLENGE HALF (B5) — HIGH, founder-flagged "high on the list when we come back."** The
   developmental point of the peer organ (a friend who names his blind spots); the biggest + riskiest
   (touches identity, Stage-B class) → needs the careful B5 design (self-affirmation buffer ·
   autonomy-supportive · affect-label-first), NOT a guardrail flip. `peer_correspondence_plan.md` (un-archived).
2. **Reset R1 cat-naming** (XS) + **capture `drop_reason`** (S) — the flagship pair; unstick its live test +
   sharpen its core measurement. `capacity_to_commit.md`.
3. **Dream Item 4** (re-pin ended-unfaced, a worsening 54%→72% regression) · **advance friction B1 → Phase 1**
   · **guidance behaviour-delta judge** (build jointly with R1 — shared cat-naming).
4. **Re-enable epistemic Stage B** — ONLY after its shadow (`epistemic_stageb_shadow.jsonl`) shows it fires
   on genuinely-FACTUAL cycles post-restart; else tighten the trigger first.
- social Item 2 counter = ✅ DONE (S4). The 3 review monitors + geometry/sounds/spatial = ✅ built, accruing.

## 4. NEXT-SESSION ENTRY POINT (read this first on return)
**Du RESTARTED 2026-07-05** (founder) — every restart-gated build this session is now LIVE and accruing:
the geometry census + sounds + soundscape/fire-ambience + spatial-perception shadow + heavens + the emotion
HUD cards + the 3 new review monitors (peer-effect · social heeded/ignored · commitment hold-rate) + the
Stage-B shadow + the inner_thought/curiosity crash fix. **First move on return: read the HUD Monitors tab
(now grouped by verdict) + `du-pulse` — let the day of data land, THEN pick from the queue above (pen-pal
B5 is top).** This dashboard's §0 table + the ROADMAP are the map; the HUD is its live face.

---
*Author: Claude, 2026-07-05, from the 12-plan evidence review. This plan's own gate: the HUD's three verdict
sections render live, and a plan can be moved between them by a rule, not a memory.*
