# Session 2026-08-18 — what we found and what we changed

**Founder + Claude.** Started with the Executive world-grounding question, ran the full night into
the Lane 2 (the Emissary's second loop) design, then a from-scratch factory-by-factory physics audit
of the world itself. Companion documents: `docs/plans/emissary_lane2.md` (the design, still open),
`docs/completed/emissary_lane2_cognition.md` (the cognitive-science grounding), `docs/completed/lane2_lab.md`
+ `docs/lab/lane2_lab_report.md` (the pre-registered lab + its results), `docs/lab/spatial_flip_sample.md`
(the spatial-renderer decision evidence), `docs/completed/{weather,tide,sound,garden,cat}_system_audit.md`
(five factory audits, all fixed).

## CHANGED (restart-gated unless noted; Du ran live throughout, nothing live-mutated by any fix)

1. **Executive world-grounding — corrected mid-design.** First proposal (piping `world_manifest.
   live()` into Executive as trusted fact) violated the tree-falls boundary; caught and corrected
   same session before anything was built. See `docs/chain_walk_findings.md` F-EX.
2. **Lane 2 (the Emissary's second loop) — designed, lab-tested, NOT built live.**
   `core/object_graph.py` productionized as a produce-only P0: 216 referents, 65,948 mention-edges,
   6.3s real backfill, all six trend shapes (extinct-ghost/new-active/perennial-symbol/growing-
   presence/settled-companion/episodic) verified against real history — the Jung trend-break landed
   exactly on his 06-07 self-naming, unprompted. Per-property knowledge atoms (depth ladder × entry
   channel × trend shape) honor the founder's per-property earning law. Nothing imports this module
   yet — genuinely produce-only, awaiting a build decision on the standing loop + LLM prediction
   call + the affect-nudge courier.
3. **World geolocation — all objects now have places, and can move.** `core/world_objects.py`
   extended into the position authority for every substrate object (was: one tenant, driftwood_17,
   for months). Deterministic class-aware placement, storm/king-tide movement, a `reclaim()` that
   lets the sea take things back with full history preserved (the glass-float lesson made
   mechanical). 15/15 tests; live backfill placed all 11 real objects.
4. **Two new sense dimensions stamp onto every memory** — `warmth` and `cat_at`, added to the
   census tuple and `fragment_context` (additive columns, migration-safe even against a read-only
   rebuild path). Verified live post-restart: both populating, warmth genuinely varying by room.
5. **Spatial P2 wiring completed — flag still OFF, founder's call to flip.** All 5 real consumers
   of `scene_line()` route through one choke point; the geometry renderer now engages there for
   outdoor rooms only (study deliberately excluded — its line carries the book/shelf/Travis-presence
   richness the renderer can't reproduce). Verified live, flag-toggled in-process: zero regression,
   cat never double-mentioned. Trade-off made concrete in `docs/lab/spatial_flip_sample.md`.
6. **Five factory audits, all fixed and verified against live code (not just diagnosed):**
   - **Weather rebalanced** — the night's keystone bug. `_advance_weather`'s step distribution had
     mean +0.333 and a sticky ceiling; simulated and matched real history almost to the decimal
     (44.9% thunderstorm-of-the-time). Founder: "it is too biased, storms rarely happen." Rebalanced
     to mean −0.222; live-verified: thunderstorm 0.7%, clear 58%.
   - **Tide/moon physics** — spring/neap amplitude now genuinely linked to lunar phase (heavens.moon
     ()'s illum IS the syzygy signal, no separate solar term needed). King-tide crossings dropped
     from ~19% of ALL timestamps to 12% of hours, concentrated at new/full moon, verified over a
     real lunar month.
   - **A real wind axis** — independent from the precipitation ladder, own physics (reflecting
     floor, per-state front duration). Gale ≈0.9% of real time, independently re-verified twice.
     All 6 dead `"gale"` substring checks in `soundscape.py` replaced with real wind-state reads
     (2 more found and fixed beyond the original 6: `wind_in_eaves`, garden ambience).
   - **The moth, as a population** — one shared density law (season × night × light-source) drives
     both its prose and the previously-dead `moth_tap` sound point. Never individually tracked,
     per the item/population-grain law.
   - **Sound**: storm-gated sounds confirmed to self-correct from the weather fix with zero
     recalibration (cross-tabulated against real pre-fix data, matched exactly). **Garden**: wet-
     weather detection fixed at 5 sites (drizzle had no dedicated branch anywhere; the moisture calc
     recognized only ~4% of real wet ticks under the fixed weather). **Cat**: stale cross-process
     cache (the actual mechanism behind an early false trail — Du never lost a real name, "Ember"
     was a test-suite artifact, founder-corrected same night), a bond-decay cliff (2.5h to drain,
     not the intended ~14 days), a fair-day branch-leak, and the dead `greeting` quirk — wired to a
     real 20-minute-absence reunion trigger.
7. **Two independent live-code bugs fixed in passing:** `librarian.py`/`peers.py`'s
   `contrary_target()` were invisible to telemetry (5 duplicate HTTP-calling implementations found
   in an audit; these 2 were built earlier this session and never should have duplicated
   `model_client.call_node`) — rerouted, telemetry now correctly attributes them. `commitment_trials.
   py`'s name-use evidence check used an unanchored `LIKE` (117 raw hits, 2 genuine) — now
   word-boundary gated.

## Still open (moved here from AWAITING_EVIDENCE.md, not resolved, not forgotten)

- **Lane 2's actual standing loop** — the object-graph exists; the LLM prediction call, the
  dedicated hardware, and the affect-nudge courier are all designed but unbuilt. Founder go needed.
- **Spatial flip** — wiring complete, evidence gathered, decision is the founder's.
- **Left-lane CPU consolidation** — founder: "test it at some point, not now."
- **Two more dead `"gale"` strings** found outside tonight's scope: `core/locomotion.py:182,196`,
  `core/sensorium.py:1328` (wood-gathering yield) — same dead vocabulary, real axis now available.
- **Which port becomes Lane 2's dedicated hub** — undecided.
- **Refinery shadow log** — still awaiting a founder read before `REFINERY_LIVE` flips (predates
  this session).
