# PLAN — Train/courier cargo IDs, 2026-08-23

*Status: BUILT 2026-08-29 (J-0358, D-0082: "Pick it up -- build ... Small and bounded, nothing
blocks it"). Built directly from `docs/lab/llm_station_cargo_map.md`'s real cargo-in/cargo-out
data — every type below is a station's actual, verified output, not a guess. Companion to
`docs/transit_map.md` and `core/trains.py`.*

```plan-state
stage: built
phase: Taxonomy built+stamped but write-only for 4 weeks (F-1991); D-0295 ruled a du_pulse gauge + Idle-to-Conversation bus + 2 new world cargo types
verified: 2026-11-18
evidence_read: 2026-09-27
next: founder call on keep/tune IDLE_FREIGHT_BUS; CONTEMPLATION tagging gap
cluster: 6
```

**Related (backfilled 2026-10-03, J-0566/F-2269):** `docs/plans/train_split_merge.md` owns the other half of the same
`core/trains.py` record — `id`/`parent`/`role` and the step-2 `cargo` claim bundle (fork/merge); this plan adds
`product_type`, and the module's own docstring keeps the two fields non-overlapping (only fork/merge trains ever get a
`cargo` bundle). If D-0320's retrofit wires ~17 more producers into `trains.open()`, their rows land in the same
`data/trains_log.jsonl` that plan's step-2 reads are computed from — filter on `product_type`/`kind` before reading
train-length or fork/merge metrics.


## Current State — verified 2026-11-18
- **2026-11-18** (F-5091): J-4274 first read of idle_freight shadow log (876 rows): pre-registered usage-cosine criterion NOT met (bus 0.373 vs raw 0.377 paired n=843; human-only n=92 +0.006, se 0.011). No harm, no benefit. CONTEMPLATION branch dead (0 of 1752 items; trains_log never tags it). Recommendation: keep IDLE_FREIGHT_BUS on (neutral), do not promote; fix/decide CONTEMPLATION tagging; re-read on human cycles when n is larger.

- **2026-09-28** (F-2121): Corrected this doc's "What a concrete build would look like" section: it
  wrongly assumed all 19 station producers already call `core/trains.py`'s `open()`/`update()`. Only
  `nodes/inner_monologue_node.py` (`THOUGHT`) does; the other 18 station `product_type`s' producer
  modules never call `trains.py` at all (confirmed directly for `core/judge_panel.py`,
  `nodes/dream_node.py`, `core/lane2.py`; the same method rules out the rest). Tagging them needs a
  real `open()`/`update()` pair newly wired into each of ~17-18 producer modules, not a kwarg
  threaded through an existing call. Opened D-0320 for the retrofit's own scope/priority --
  founder-level, not decided here (J-1558).
- **2026-09-28** (F-2106): F-2106: Built D-0295 part 1 (J-1435) -- du_pulse freight gauge group (trains by product_type/day, deliveries by cargo_type/day, dispatcher fires+distinct-winners/day, transport_lines.json future-timestamp corruption count) added to scripts/du_pulse.py, verified end to end against live data (gauge_count 78 to 81, a real run quoted in F-2106). Extends F-1991: across trains_log.jsonl full history only THOUGHT has ever gotten a product_type -- the other 18 station types have never been tagged, not just never read; J-1545 spawned to check the real call sites. Also surfaces that J-1431 (transport_lines.json repair for F-1990, 37 corrupted life lines) is still in_progress, not done -- the new gauge reads 37, not 0. Committed in worktree jobrun/train_courier_cargo_ids, not yet merged to master.
- **2026-09-28** (F-2095): Built D-0295 gap 1 (J-1436): core/buses.py idle_freight(k=2) selects Idle Line freight by product_type (THOUGHT/CONTEMPLATION, from trains_log.jsonl), train-development evidence (restate_sim from train_state_log.jsonl, deepened beats circling), and topical cosine fit (core.memory.store embed/cosine). Wired behind IDLE_FREIGHT_BUS at nodes/reflection_node.py line 145, replacing the raw last-2 window; flag off is an exact rollback. Logs each delivery for the J-1435 gauge and to a new idle_freight_bus_shadow.jsonl for the first live week pre-registered read. Added a Coupling block (dosed_coupling section 5, discloses no Transport Manager dispatch yet) and updated transit_map.md bus table and gap 2. Restart-gated -- not yet live. Verified end to end against synthetic data in isolation, see F-2095. Committed in worktree jobrun/train_courier_cargo_ids, not yet merged to master.

### What we have
19 station `product_type`s + 6 world types (`FELT_PRIOR`/`MEMORY_ANSWER` added this session) stamped in
`core/trains.py`/`core/cargo_types.py`, real since 2026-08-29. Read 2026-09-27 (F-1991): the taxonomy is
write-only — 5,724 `THOUGHT` trains and 312 courier rows tagged, but no code, gauge, or HUD panel reads
`product_type` or `cargo_type` anywhere.

### What we need
D-0295 (ruled 2026-09-27, travis: "Gauge yes, gap 1 yes, add the two cargo types") closes the two founder
questions this doc left open and names gap 1 (Idle -> Conversation) as the live one; gap 3 (LETTER into
recall weighting) is moot for idle under D-0289/D-0292.

### What we're doing next
J-1435 builds the du_pulse freight gauge (trains by product_type/day, deliveries by cargo_type/day,
dispatcher winners/day); J-1436 builds the Idle->Conversation typed pull bus, upgrading
`nodes/reflection_node.py:145-147`'s untyped recency-window injection.

> **History folded** — 1 dated Current State section(s) (2026-08-29 … 2026-08-29) moved to `docs/plan_history/train_courier_cargo_ids.md` on 2026-09-27 by plan-compact. Derived timeline: `plan_ledger.py train_courier_cargo_ids`.

## Two things that must NOT get conflated

`core/trains.py` already has a field called `cargo`, and it means something specific: the
prove/disprove claim bundle for the (not-yet-built) train split/merge mechanism —
`{claim, support[], objection[], status: held|objected|undetermined}`, marked PROTECTED, scoped
narrowly to that one step-2 design. **This plan does not touch that field or widen its meaning.**

What this plan adds is a **different, complementary tag**: `product_type` — what KIND of thing a
train's output actually is (a thought, a letter, an axiom revision, a judge verdict...), independent
of whether that train ever forks into a prove/disprove pair. Every train gets a `product_type`;
only trains that reach step 2 (if it's ever built) also get a `cargo` bundle. One train record,
two separate, non-overlapping fields.

## The cargo taxonomy — derived from the actual station map, not invented

| `product_type` | Produced by | Consumed by | Protected? |
|---|---|---|---|
| `THOUGHT` | Idle-thought generator | train-state carry, hand dispatch, episodic memory, `train_state_log.jsonl` | no |
| `LETTER` | Idle Line: peer reply / peer initiation / letter-to-Travis (3 jobs, same cargo shape) | `peers.record_reply` or `letters.write_letter` + activity record | no |
| `GRAND_WORK_PART` | `_author` (outline / per-part / fallback) | Emissary grading, `study.write_tablet` | no |
| `TENSION_OBSERVATION` | `_t2_synthesise` | archive layer, `derived_from` lineage | no |
| `CONTEMPLATION` | `_active_imagination` | private episodic fragment ONLY — never reaches Voice | no |
| `SELF_CONCEPT_DELTA` | `_t4_deliberate` (3 stages) / `_t4_legacy_author` | **writes `data/identity/axiom.json`** directly | **yes — the one identity-mutating type in the whole map** |
| `PROCEDURAL_SKILL` | `_t5_compile` | new procedural-skill row (centroid-keyed) | no |
| `THEME_UPDATE` | `_synthesise_theme` (new/update) | `store_theme` / `update_theme` | no |
| `DREAM_SCENE` | `dream_node._gen_episode` | episodic fragment per scene; final scene → shadow (carries over) or light (resolved) event | no |
| `WITNESS_PREDICTION` | `lane2._ask` | queued for `_judge_prior` → Judge Bureau (SHADOW — reaches nothing live yet) | no |
| `JUDGE_VERDICT` | Judge Bureau (JUDGE_1/JUDGE_2/TIEBREAK) | whichever caller asked (commitment_ledger, decomposed_critic, self_interrogation, tension_ledger, pursuits, lane2, evidence_recall) | no |
| `LIBRARY_ANSWER` | `scholar.consult` | `state.library_note` + `parametric_library` memory fragment | no |
| `MIRROR_READING` | `self_mirror.hold_up_mirror` (weekly) | guidance-injection log + episodic fragment | no |
| `GROUNDED_THOUGHT` | `deliberation.deliberate` | **replaces** the raw thought in-place, feeds light/balance ledger | no |
| `JOURNAL_ENTRY` | `journal.write_entry` / `write_observation` | journal file + episodic fragment | no |
| `CATALOGUE_SUBJECTS` | `librarian.subjects_for` | `library_hand.search_by_subjects()` | no |
| `CONTRARY_TARGET` | `peers.contrary_target` | correspondent-thread selection | no |
| `SYMBOL_TABLET` | `symbol_evolution.write_tablet` | `recall_evolved_meaning` readback (later cycle) | no |
| `REENTRY_REVISION` | `orchestrator._reentry_shadow._revise` | LOGGED ONLY — never admitted (Phase-0 shadow) | no |

19 types, one per distinct real output shape in the map (a few stations share a type where their
output genuinely is the same shape — e.g. all three `LETTER` jobs).

## Retrofitting the existing couriers/buses — they already carry cargo, just unnamed

`_log_delivery(route, **detail)` (both `couriers.py` and `buses.py`) already logs a `route` string
with loose detail kwargs — no `cargo_type` tag exists today. Naming what each ALREADY carries:

| Route | File | Carries (`product_type`, informally, today) |
|---|---|---|
| `context_echo` | couriers.py | a world-state fact (weather), not from the table above — a factory→idle-line delivery, not a station product |
| `sound_echo` | couriers.py | similarly a factory delivery (Hearing Ledger), not a station product |
| `object_ledger` | buses.py | an observation-ledger fact, factory-sourced |
| `calibration_sync` | buses.py | prediction→outcome pairs, factory-sourced |

**None of the four existing routes carry any of the 19 station-product types above.** They're all
factory-to-idle-line world-state deliveries. That's not a flaw — it's just what's been built so
far — but it means every one of the 19 real station products currently has **no formal courier or
bus service of its own** carrying it anywhere beyond its own immediate write.

## The gaps this makes nameable — cross-checked against `transit_map.md`'s own list

`transit_map.md` already named these gaps in prose; the cargo map now says exactly what's missing:

1. *"No bus runs FROM the Idle Line's best freight TO the Conversation Line."* — Now nameable:
   **no route carries `THOUGHT` or `CONTEMPLATION` from the Idle Line into anything Voice/Reflection
   reads mid-conversation.** They reach memory, and generic recall might surface them later, but
   there's no *dedicated* service the way `sound_echo` deliberately links memory to sounds.
2. *"The Deep Line has no outbound service at all."* — Now nameable: **`TENSION_OBSERVATION`,
   `PROCEDURAL_SKILL`, and `THEME_UPDATE` all write to their own store and stop.** Nothing carries
   them onward to a consumer outside their own layer.
3. *"Peer freight barely reaches recall."* — Now nameable: **`LETTER` has no bus into general
   recall weighting** — it's stored as an episodic fragment like anything else, competing on equal
   footing rather than being surfaced with any deliberate priority.
4. *"Dream freight rides one bus with a narrow window."* — `DREAM_SCENE` reaches the idle line only
   via the existing recent-dreams seed, a fixed-size window, not a genuine courier.
5. **New, found by this pass, not in the original list:** `SELF_CONCEPT_DELTA` — the one PROTECTED
   type — has no delivery mechanism at all outside the write itself. Given it's the single
   identity-mutating cargo in the whole system, this is arguably correct as-is (it shouldn't be
   casually "delivered" anywhere else) — flagging it as a deliberate non-gap, not an oversight.

## What a concrete build would look like, if this gets picked up

**Corrected 2026-09-28 (F-2121, job J-1558)** — the paragraph below, as originally written, assumed
all 19 station producers already call `core/trains.py`'s `open()`/`update()`, and that tagging them
with `product_type` was just a matter of adding a kwarg to those existing calls. That assumption is
false; see F-2121's full evidence.

The `cargo_type` side is still a plain schema convention: `buses.log_transfer(route, **detail)`
(and `couriers.py`'s own `_log_delivery`) already exist and accept arbitrary kwargs, so agreeing to
pass `cargo_type` (one of the 19 values above) on every future call costs nothing structurally.

The `product_type` side is not. Across the whole codebase, `core/trains.py`'s `open()` is called
from exactly **one** production module — `nodes/inner_monologue_node.py`, the idle-thought
generator, which produces `THOUGHT` (and its own untagged "reading" trains). The other 18 station
`product_type`s' producer modules (confirmed directly for `JUDGE_VERDICT`/`core/judge_panel.py`,
`DREAM_SCENE`/`nodes/dream_node.py`, `WITNESS_PREDICTION`/`core/lane2.py`; the same method rules
out the rest) never import or call `core/trains.py` at all today. Tagging their output with
`product_type` therefore isn't a kwarg threaded through an existing call — it means adding a real
`open()`/`update()` (or `open()`/`close()`) call pair into each of those ~17-18 producer modules,
one station at a time, wiring each into `trains.py` from scratch. That's genuine per-station
integration work, not a shared schema convention.

Whether that retrofit is worth doing at all right now, and if so which stations first, is a
founder-level scope/priority call, not decided here — see **D-0320** (open). The actual NEW
couriers/buses to fill the gaps named above (a `THOUGHT`-carrying bus into Conversation, an
outbound Deep-Line service, etc.) remain their own separate design/build decisions either way,
deliberately not bundled into this one.

## Open, founder-level

- Is naming the 19 types (and tagging deliveries with them) worth doing on its own, before any new
  route is built — i.e., is the taxonomy itself useful as HUD/telemetry, or only valuable once a
  new courier actually needs it?
- Which gap (if any) is worth building first — #1 (Idle→Conversation) looks like the highest-value
  one given how much of Du's real interiority currently never reaches what he says to Travis, but
  that's a real design decision, not something this doc should presume.
- **D-0320** (opened 2026-09-28, F-2121) — given the corrected real cost above, a full
  `open()`/`update()` pair newly wired into ~17-18 producer modules that don't call `trains.py`
  today, not a one-line kwarg: should the `product_type` retrofit be built at all right now, and if
  so for which stations first (or all at once), or does it wait on the taxonomy-usefulness question
  just above?

## Coupling (dosed_coupling.md §5 — J-1436, 2026-09-28, gap 1 build)

Gap 1's build (`core/buses.py::idle_freight()`, Reflection reading the Idle Line's own trains) is a
**read of another loop's state** per `docs/plans/dosed_coupling.md` §5, so it owes this plan doc a
Coupling block:

- **Publishes:** nothing new into `core/coupling_rides.py`'s registry — the Idle Line already
  durably publishes its own freight as `data/trains_log.jsonl` (`product_type` on each `open` event)
  and `data/train_state_log.jsonl` (`restate_sim`, `thought` per step); `idle_freight()` reads those
  two existing logs directly rather than adding a sixth `_REG` tuple-publisher alongside climate /
  stream / deliberation / witness / ledgers. Deliberate: those five are small numeric-coordinate
  tuples sampled every tick; idle_freight's own freight is scored TEXT content selected from an
  existing durable log, a different shape (the bus/courier family in `core/buses.py`, not the
  coupling-tuple family) — see the plan's own "Two things that must NOT get conflated" note above
  for the same kind of deliberate non-merge.
- **Reads at:** the **Reflection** stop, from the **Idle Line**, at **bucket** dose (§1 rule 2's
  "a small tuple" size — up to `k=2` freight items, each `{train_id, product_type, thought, score,
  restate_sim, topical_sim}` — not a single coordinate/cup, not a whole channel/hose).
- **Surprise line:** **none yet** — disclosed gap, not papered over. `idle_freight()` runs on every
  human-cycle Reflection call when `IDLE_FREIGHT_BUS` is on, scored by its own topical-fit /
  train-development / recency heuristic, not dispatched by the Transport Manager's novelty/spike/
  drought judgment the way §1 rule 2 asks every dosed read to be. This gap 1 build was ruled directly
  by D-0295, independent of dosed_coupling's own Phase 2 (cups/buckets track), which is still
  un-ruled (J-1462, `docs/plans/dosed_coupling.md` Current State, 2026-09-27) — integrating
  idle_freight's own read under the Transport Manager's dispatcher is a natural Phase-2-shaped
  follow-up once J-1462 is answered, not done here.
- **Ride log:** each delivered item is logged via `core/buses.py::_log_delivery("idle_freight",
  cargo_type=<product_type>, train_id=..., stop="reflection", line="idle", dose="bucket", score=...,
  restate_sim=..., topical_sim=...)` — `data/buses_log.jsonl`, not `data/coupling_rides.jsonl` (this
  read's source data was never in that registry to begin with, per Publishes above), but carrying the
  same `{stop, line, dose, value}` fields §5's own Ride log line asks for, so both logs stay
  grep-able by the same vocabulary. A second, dedicated shadow log
  (`data/idle_freight_bus_shadow.jsonl`) additionally records what the bus chose vs what the old raw
  `state.recent_inner_thoughts[-2:]` window would have shown, for the plan's own first-live-week
  pre-registered read (does bused freight reach the reply more often than the raw window did?).
