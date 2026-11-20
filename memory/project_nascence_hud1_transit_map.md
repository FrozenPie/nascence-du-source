---
name: project-nascence-hud1-transit-map
description: "Nascence — HUD1's transit-pulse visualization (2D, honest, not decorative), ported from HUD2's concept. BUILT + BROWSER-VERIFIED 2026-08-23: station tagging, /api/transit_pulse, and the World-tab map card all live. Needs Du's next restart before real (non-'?') station data flows."
metadata: 
  node_type: memory
  type: project
  originSessionId: 24362f92-5fed-41bf-ab7f-837372cb4473
  modified: 2026-08-22T19:11:37.239Z
---

**Origin:** founder wants to see, in HUD1 (not HUD2's 3D), Du's actual thoughts moving through the
real processing pipeline — "trains travelling between stations" — grounded in real logged events,
explicitly NOT decorative (HUD2's own first transit map was constant-speed looping with zero tie to
real activity; it got rebuilt for exactly that reason — do not repeat it here).

**The mental model, arrived at over several rounds (all confirmed against real code, not invented):**
- A single thought rides a real ~8-9 step PIPELINE per tick: generate (LLM) → embed → deliberate/
  ground (LLM, the Emissary, only some ticks) → continuity check (script) → affect label (script) →
  shadow/light classify (script) → act routing (script) → store (DB write) → loop back to 1, or the
  train ends. "Cargo" = what each station actually attaches (embedding, grounding verdict, shadow/
  light tag, act decision) — already exists scattered, never assembled as one trail.
- Two fates worth showing separately: the TRAIN ends (no more continuation) vs. the FRAGMENT's own
  life (goes cold/pruned much later — different clock, don't conflate).
- **FACTORIES** (weather/tide/garden/etc, stationary, own clock) feed thoughts/other factories via:
  **COURIERS** (urgent, real-time — must be current to matter) vs **BUSES** (not time-sensitive,
  including confirmed-real factory→factory, e.g. weather→garden with zero delivery mechanism).
- Open, NOT yet decided: does the visualization scope to just the idle-line pipeline first, or
  include deep-line/T4 hand-offs too; new HUD1 tab vs. fold into System Health; how the fragment's
  longer post-tick life (couriers picking it up days later, T4 pulling it as evidence) relates to
  the per-tick pipeline view (different timescale, probably a separate view, not decided).

**SHIPPED 2026-08-22 (the prerequisite, not the visualization itself):** the courier/bus rename.
`core/couriers.py`'s own docstring had called itself "the busses" since 2026-08-16 — founder: "couriers.py
was probably an attempt at this... go with the new way of naming it." Split: `core/couriers.py` keeps
only genuinely urgent routes (`context_echo`, `sound_echo` — gate on CURRENT world state). New
`core/buses.py`: `object_ledger_line` + `sync_investigation_calibration` (never actually time-sensitive),
moved unchanged in behaviour, own `buses_state.json`/`buses_log.jsonl` (real synced-id migrated, not
lost). `buses.log_transfer()` is a ready hook for factory→factory (weather→garden confirmed real,
not yet instrumented). HUD World tab card split into labeled sections; `scripts/build_hud2_transit.py`
(the separate HUD2 data builder, which Claude also owns per its own convention) updated so its next
run reflects the split correctly (was pointing all 4 routes at one shared log).

**Also found along the way, not yet acted on:** `scripts/build_hud2_transit.py`'s own protocol notes
already contain a `follow_a_thought` design for animating one real cognitive event across a map
(factory changes → platform fires → courier delivers, tied to real log growth) — written for HUD2,
worth reading before designing HUD1's version so the two don't diverge on the same idea. Also: the
AST-based station scan misses hand-built aiohttp wrappers (left_lane/Emissary at 11439 doesn't
appear in `transit_map.json` at all) — same disease found twice before (judge_panel, lane2); a third
instance, not fixed.

**BUILT 2026-08-23 (browser-verified):** station-level instrumentation + the actual pulse map.
`core/trains.py::station_for_url()` gives a canonical `station_{port}` id. `InnerMonologueNode.__init__`
computes `self._main_station` once (hot chain has no fallback, so no per-step recompute needed);
`self._step_visited` resets every step and gets `station_11439`/`station_11433` appended only when
`core/deliberation.py`'s own already-computed `provenance["source"]` says the Emissary was really hit —
no new detection logic invented, reused an existing return value. `_log_train_step()` writes both into
`train_state_log.jsonl`. `hud/server.py::load_transit_pulse()` (new `/api/transit_pulse`) deliberately
does NOT re-derive station/factory/courier ground truth — it reuses `data/hud2/transit_map.json` (already
AST-verified by `scripts/build_hud2_transit.py`) for that, and only adds the live overlay a static file
can't have: open trains (reconstructed from `trains_log.jsonl` open/close pairs, since the HUD is a
separate process and can't see `core.trains`'s in-memory registry), the last 40 station-tagged steps, and
recent courier/bus deliveries. Frontend (new World-tab card in `index.html`/`style.css`/`app.js`) draws a
deterministic ring layout and only ever animates a pulse/hop at a station a real step just named — no
invented motion, confirmed by browser check (5 station nodes rendered; pre-restart log rows correctly
show "?", not fabricated values). Full detail: `docs/AWAITING_EVIDENCE.md` "Built, awaiting evidence" →
Transit Pulse entry; `docs/ROADMAP.md` "★★ THE TRAINS" section.
**Not yet true:** Du hasn't restarted with this code, so every existing `train_state_log.jsonl` row still
reads `station: "?"` — that's correct/honest, not a bug. Next: restart Du, confirm new rows carry a real
station and that a deliberation hop shows up in `visited`.
[[project_nascence_train_registry]]
