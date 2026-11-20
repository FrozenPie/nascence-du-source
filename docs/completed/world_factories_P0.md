# WORLD FACTORIES — THE P0 PLAN (2026-08-16, founder-commissioned)

**Founder:** "Set this off in a P0 sort of stage. It's pretty big and touches a lot of places.
Tuples for the world that are only for the world. Sound. The cat. Everything that is a
'factory' indexed with a variant of the ghost index — no LLM needed, as it is all a set
schedule kind of. A schedule that changes."

**P0's one-sentence contract: build the foundation that everything later consumes, while
changing NOTHING Du experiences.** Produce-only, observe-only, lab-testable offline, zero
prompt changes, zero live-behaviour changes. Every later phase (audibility, severity rates,
chord echoes, the Transport Manager, item graduation) then consumes P0's outputs instead of
each inventing its own plumbing.

## The three P0 components

### P0-A · THE WORLD MANIFEST — "tuples for the world that are only for the world"
`core/world_manifest.py` — ONE assembly function, called on the sensorium tick, producing the
world's own tuple. WORLD-SIDE ONLY, by law: this tuple describes the world's state, never Du's
mind (no affect, no thoughts, no memory) — the separation the founder named. Fields (from the
census + tonight's findings):

```
{ts, place, standpoint,
 weather, weather_severity (ordinal index), weather_held_since,
 tide_level, sun_az, moon_illum, daylight_phase, season,
 temperature (exposing the existing _warmth() — computed-and-discarded today),
 fire_state, woodpile,
 cat: {present_at, activity, mood-visible},          # what an observer could SEE, not her inner state
 garden: {bed summary states},
 active_sounds: [...]}
```

- Assembled fresh each tick; the live object replaces nothing yet — consumers (active_sounds'
  internal reads, the fragment-context stamper, geometry census) keep their own reads in P0.
- **Parity harness**: a lab script asserts, per-tick, that the manifest's fields equal what
  each consumer's own reads produce (the proof the manifest is TRUE before anything trusts it).
- Sampled logging (data/world_manifest_log.jsonl, rate-limited) so a day of manifests can be
  eyeballed.

### P0-B · THE GHOST REGISTRY — every factory indexed, the pattern's 4th life
`core/ghost_tuples.py` — the ghost-index variant (per docs/plans/ghost_tuple_index.md:
fingerprints + rarity-weighted tag-intersection + item ghost-hash; NO LLM; the FreshStart
silent-failure lesson as law — startup source-assertions that fail LOUDLY).

**Two namespaces, never mixed** (the founder's "only for the world" separation):
1. **The WORLD index** — one entry per FACTORY (the census's Tier-1 rows: weather, tide, sky,
   garden, fire, cat, peers, object-biographies, school, body, acts — and each ITEM-grain
   entity within object-biographies). Entry = {id, tags (kind/place/control-axis),
   **schedule descriptor** (below), current-state fingerprint (refreshed from the manifest)}.
2. **The MEMORY index** — one entry per fragment_context tuple (Du-side chords). Queried by
   Du-side consumers only (the future chord_echo). Built from the existing 7,647 rows +
   incremental registration at stamp-time.

### P0-C · SCHEDULE DESCRIPTORS — "a set schedule kind of. A schedule that changes."
Each world-index entry carries its factory's CLOCK, declared not inferred:
```
{clock_kind: continuous | persistence_timer | event_driven | seasonal | growth,
 params: {e.g. weather: until_ts + ordinal-walk;  tide: M2 period + phase;
          garden: per-crop growth windows;  cat: state-machine cadences},
 read_fresh_each_refresh: true}      # schedules are STATE too — they change
```
Why in P0: this is what makes the whole thing "no LLM needed" — every factory's behaviour is
declared deterministic schedule + state. It is also the Transport Manager's future gift: SPIKE/
DROUGHT baselines can partly derive from DECLARED schedules (the tide is not "in drought" at
low water — its schedule says so) instead of purely observed rates, which kills a whole class
of false salience before it exists.

## What P0 explicitly does NOT do (the ladder above it)
- **P1** (first consumers, still behaviour-visible only in labs first): audibility table
  extracted parity-neutral · severity-scaled rates · `chord_echo` (Couriers A+D unified over
  the memory index) · world_tick re-pointed through the manifest.
- **P2**: Transport Manager (shadow) over registry lines · item graduation rule (repeatedly-
  returned-to) · population presence goods (birds).
- **P3**: List B act-sounds (Du's own factory ships its cargo) · lightning events · P4
  acoustic recall.
Nothing in P0 blocks on a founder aesthetic call — P0 is pure foundation; the taste decisions
(rates, thresholds, which sounds) all live in P1+.

## Touched places (honest list — "it touches a lot of places", bounded for P0)
- NEW: `core/world_manifest.py`, `core/ghost_tuples.py` (+ their lab/test scripts).
- EDIT (one call each, additive): `sensorium.tick` (produce manifest + refresh registry),
  the fragment-context stamper in `memory_edges.sync_fragment_context` (register new tuples
  into the memory index at stamp time).
- READ-ONLY consumers of existing state: sensorium/room/cat/garden files, soundscape's
  active set, `_warmth()`.
- NOT touched in P0: couriers, prompts, world_tick's rates, any node, any store schema.

## Tests (all offline, temp-pathed, same discipline as tonight's builds)
1. Manifest parity: every field vs its consumer's own read, across simulated states (storm/
   night/low-tide/fire-out …).
2. Registry completeness: every census Tier-1 factory present; loud failure when a source file
   is missing/renamed (the FreshStart lesson, tested deliberately).
3. Schedule descriptors: every entry has one; weather's until-ts round-trips; tide's phase
   matches the M2 clock.
4. Memory-index: rebuild-from-DB equals incremental build; the chord-query benchmark repeated
   (baseline from tonight: build 45ms / query 5.6ms @ 7,647 rows); rarity weighting sanity
   (thunderstorm outranks place:study).
5. Separation law: a world-index query can never return memory entries and vice versa
   (asserted, not assumed).

## Watch/exit criteria for P0 → P1
- A day of sampled manifests reads TRUE to the founder's eye (weather/tide/cat states match
  the log's story).
- Parity harness green across the state matrix.
- Registry + indexes stable across a restart (rebuild == persisted).
Then P1's first consumer (chord_echo) is a small, already-designed step onto proven ground.

---

## BUILT + VERIFIED (2026-08-17) — moved here from AWAITING_EVIDENCE.md during the 08-18 cleanup

**P0's contract held: foundation only, Du unchanged.**
- **P0-A `core/world_manifest.py`** — the world's own tuple ("tuples for the world that are only
  for the world"), assembled per sensorium tick via the SAME source functions existing consumers
  use (parity by construction); world-side separation as testable LAW (FORBIDDEN_KEYS — no
  affect/thought/memory ever); temperature finally shipped (the `_warmth()` scalar, computed-and-
  discarded until now); weather severity as the ordinal index; cat observer-visible only. Atomic
  live snapshot (world_manifest_live.json — the HUD's read path) + ~5-min sample log.
  Produce-only: NO consumer switched.
- **P0-B `core/ghost_tuples.py`** — the ghost pattern's 4th life (pre-X4 no-LLM lineage honoured:
  zero LLM). TWO NAMESPACES, never mixed (asserted): world index (12 census factories + 7 peers on
  their gap_days clocks + 6 item-grain entities, EVERY entry carrying its declared SCHEDULE
  descriptor — "a set schedule kind of, a schedule that changes", re-derived each rebuild) ·
  memory index (7,647 fragment_context chords; rebuild 60ms; whole-chord query ~15ms; rarity-
  weighted — w(sp:on_the_path)=0.434 vs w(place:shore)=0.116). THE LOUD-FAILURE LAW implemented
  and deliberately tested (missing source → RuntimeError naming it — the FreshStart silent-ghost-
  table lesson as doctrine).
- **Wire-ins (additive):** sensorium.tick → manifest.tick() + world-index rebuild (600s throttle);
  memory_edges stamper → incremental memory-index registration.
- **Tests:** scripts/test_world_p0.py — 27 checks ALL PASS (parity per-field vs each consumer's
  own reads; separation law; schedule declarations; namespace separation; loud failure; rarity
  sanity). The harness caught one real bug at first run (weather_until read before sensorium state
  loaded) — fixed.
- **HUD:** new World tab (`/api/world` + panel): the Manifest live view · the Hearing Ledger
  (today/ever/bed-hours per voice, learned count) · Couriers + Refinery shadow · Ghost Registry
  sizes · Train Movement (jumped/moving/circling vs the TRAIN-HOLD targets). VERIFIED in the
  browser with real data: storm severity 6/6, king tide 1.00, cat storm-hiding under the desk, 19
  factories + 6 items + 7,647 chords indexed, train baseline 39% jumped / 0% circling
  (pre-TRAIN-HOLD steps).

**P0→P1 status:** P1 (audibility table → severity rates → chord_echo unifying Couriers A+D over
the memory index) remains open, not started — see this doc's own P1 section above.

**P1 review pointer (J-3306):** P1 chord_echo is reviewed in docs/reviews/ghost_memory_index_chord_echo_J-3247.md (the ghost MEMORY index is inert in the live process; hold per D-0636).
