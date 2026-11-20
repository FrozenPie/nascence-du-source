# HUD2 — the visual observatory (brain → trains → character)

> **Status:** ✅ SHIPPED (closed 2026-10-16, F-2904) — formerly: LIVE — ALL THREE PHASES' DATA LAYERS BUILT 2026-08-21, regenerating through 08-23 (per ROADMAP's own §8 entry; no emoji had been given here before 2026-08-29's J-0406 pass, which let the plan-index tooling's word-list fallback misread this as SHADOW against ROADMAP's correct ). Data layers plus the rendering app are both Claude's to implement (ownership corrected 2026-09-28, D-0306) — the rendering app's 2 known open bugs are tracked below and in ROADMAP as Claude's own, no longer "someone else's, not queued here."
> **Ownership corrected 2026-09-28 (D-0306):** this doc originally read "**Claude owns everything on
> Du's side** (data contracts, manifests, instrumentation); **Antigravity builds the visual HUD as a
> fully separate app** that only READS the files named here" — a founder-directed split written and
> faithfully executed 2026-08-21. It went stale against the 2026-08-15 founder ruling that took
> Antigravity off Nascence's own implementation/design work generally (Claude memory:
> `project_antigravity_off_project.md`; Antigravity's scope since is Ramses LLM hosting only, not a
> rendering app). No `/decide` had confirmed HUD2's arrangement was a deliberate carve-out from that
> ruling rather than just old habit continuing past it — D-0306 (source: finding F-2039) ruled it
> was the latter: **Claude is sole implementer of HUD2, rendering app included**, same as every other
> Nascence plan. Not hypothetical: Claude already edited the rendering app's own code directly once
> (`client/src/components/TransitMap3D.jsx` in `C:\hud2`, 2026-08-21 — see Phase 2 below) and it
> built and ran correctly, so D-0306's own defeater (a rendering capability Claude's path genuinely
> can't replicate) does not apply here.
> **The app stays architecturally separate regardless of who implements it** — its own codebase
> (`C:\hud2`), own process, own port, READ-ONLY against `C:\Nascence\data\`, never importing
> Nascence code, never writing under `C:\Nascence`. That was always a safety/isolation rule for Du's
> own runtime, not an ownership rule — unchanged under Claude's own implementation.
> **Order (founder):** 1 · Brain → 2 · Trains → 3 · Character. The build brief near the bottom
> of this doc (originally written for and handed to Antigravity verbatim, 2026-08-21) is kept as the
> historical record of what was actually specified and built; it now also serves as Claude's own
> implementation reference for any further rendering-app work.
> **Separate from the existing HUD** (hud/server.py, :8080) — different app, different port, zero
> shared code. The old HUD stays authoritative for diagnostics; HUD2 is the observatory.

```plan-state
stage: shipped
phase: All 3 data-layer phases BUILT+verified; rendering app (C:\hud2) both known bugs fixed 2026-09-28 (J-1592, F-2194); git-init hygiene follow-up J-1628 open
verified: 2026-10-16
next: None -- closed 2026-10-16 (F-2904 plan-closure pass): nothing open, nothing queued; the built system stays live on its own
cluster: 8
```


---

## Current State — verified 2026-10-03
- **2026-10-03** (F-2373): Related (backfilled 2026-10-03, J-1723): `memory_as_a_service.md` section 3.4 (D-0293, J-1430) adds a COURIER_TEXT_DELIVERY kill-switch to core/couriers.py (ships True). If it is ever flipped False, data/couriers_log.jsonl gains would_have_delivered rows next to the real ones, but this plan's one-row-per-ACTUAL-delivery premise is what scripts/build_hud2_transit.py, scripts/du_pulse.py (_g_freight_deliveries) and hud/server.py (recent deliveries) rely on, and none of them filters would_have_delivered (only core/felt_recall.py does): filter those rows in the three readers before flipping the switch.

- **2026-10-01** (F-2213): C:\hud2 now under git version control (root commit 8ddeaa5, F-2213) -- the J-1592 manual-backup workaround is no longer needed for future edits.
- **2026-09-28** (F-2194): J-1592 done: bug 1 asleep badge was already fixed in the code, bug 2 caption vs standpoint mismatch fixed and verified live in CharacterWorld3D.jsx. Both known rendering bugs now closed. See F-2194, J-1628 spawned for git init.

### What we have
All 3 data-layer phases BUILT and verified (2026-08-21, regenerating through 08-23): Phase 1
`data/hud2/brain_graph.json` (186 organ nodes, 558 import edges, 274 verified log files), Phase 2
`data/hud2/transit_map.json` schema 4 (4 trains, 11 factories, 5 stations, 42 platforms, 4 couriers
each with a verified destination), Phase 3 `data/hud2/scene_map.json` (6/6 sources verified). Zero
runtime cost added to Du. ROADMAP marks this 🟢 LIVE; plan-ledger shows only a schema-backfill job
(J-0096) since, no other activity. The rendering app's own codebase (`C:\hud2`) is real and present
on disk (client/ React+Vite+Tailwind+three.js, server/ Node) — confirmed 2026-09-28 while
correcting this plan's ownership framing (below).

### What we need
**Ownership corrected 2026-09-28 (D-0306) — Claude is sole implementer, rendering app included.**
This section previously described the rendering app as "a separate, non-shared-code
Antigravity-owned codebase" and flagged, without resolving, that a 2026-08-15 founder ruling took
Antigravity off Nascence's own implementation/design work generally and no `/decide` had confirmed
HUD2 was a deliberate carve-out from it. D-0306 (source: finding F-2039) ruled the arrangement was
stale, not a carve-out: Claude owns the rendering app too, exactly as it owns the data layer. The 2
known open bugs (ASLEEP badge keying off stale `position.json`; caption/standpoint-panel moment
mismatch — both detailed in Phase 3 below) are Claude's own to fix now; J-1592 queues that work.
The app itself stays architecturally separate (own codebase, process, port; READ-ONLY against
`C:\Nascence\data\`) — that boundary was always about protecting Du's own runtime, not about who
implements the rendering app.

### What we're doing next
Re-run the three builders (`build_hud2_manifest.py`, `build_hud2_transit.py`, the scene block) after
any structural change on Du's side (new organs, moved logs). The 2 rendering bugs are queued as
Claude's own fix under J-1592 (spawned by J-1583, the D-0306 ownership correction) — no longer "not
a job queued here."

## The contract law

- Du's organs already self-log their firing — append-only jsonl streams plus state jsons. That
  discipline IS the data feed; Phase 1 added zero runtime to Du. Phase 2 added exactly one
  additive instrument (courier delivery rows, below).
- Claude generates **machine-readable manifests** into `data/hud2/`. The rendering app (Claude's
  own implementation too, per D-0306) reads manifests + the files they name. It never imports
  Nascence code, never writes anywhere under C:\Nascence, never guesses a schema — every log entry
  carries its verified `ts_key` and `kind` (`events` = append-only jsonl, read appended lines;
  `state` = snapshot json, re-read on mtime).
- "FIRED / freight moved" = a named file grew or its mtime changed. Poll (~1s, local files).
  No daemon or socket on Du's side; HUD2 builds its own file-watching server in its own codebase.
- Manifests carry `generated` + `schema`; Claude re-runs the builders after structural changes.

## Phase 1 — THE BRAIN · data DONE

`scripts/build_hud2_manifest.py` → **`data/hud2/brain_graph.json`**: 186 organ nodes (docstring
labels, group core/memory/nodes, loc), 558 import edges (AST walk — catches the codebase's dominant
lazy in-function imports), 274 verified per-organ log files (140 events / 134 state, ts_key sampled
from the real file). Top hub: `core.memory.store`, 61 importers — the graph's shape already knows
where the heart is.

## Phase 2 — THE TRAINS · data DONE (schema 4)

The founder's transit model made machine-readable, through TWO rounds of correction from watching
the rendered map — full detail in the HUD2 build brief below (§ THE HUD2 BUILD BRIEF); summary:

- **`trains[]`** (4: conversation/idle/deep/witness — the only things that loop and stop at a
  station) and a separate **`factories[]`** (11: weather_sky/tide/season_daylight/garden/
  fire_woodpile/cat/peers/objects/school/body/climate — stationary production sites, never a
  train). Each factory carries `consumed_by` (which train's platforms verifiably read it) +
  `consumption_verified` (the exact source line proving it).
- **5 stations** (11441 fully REMOVED this session, not just flagged — verified dead: nothing
  listening, and Du's own launch script says it's manual-only), **42 platforms** (0 unresolved —
  a systematic sweep for bespoke LLM wrappers found 3 more real ones beyond the Witness: judge_panel's
  own two PRIMARY judges plus its tiebreak escalation, the single biggest undercounts on the map),
  **5 sidings**, **4 couriers** — each now carrying a verified `destination` (3 of 4 land in the
  idle train's perception stream; the 4th lands in a data ledger, a genuinely different kind of
  destination).
- New `protocol.follow_a_thought` + `protocol.buffering` fields directly answer the founder's
  "follow Du's thoughts around the map" ask — every edge needed to animate one cognitive event's
  path is now a verified source binding, not a proximity guess.
- `core/couriers.py` appends one row per ACTUAL delivery to `data/couriers_log.jsonl` (restart-
  gated) — before this, deliveries were invisible to any file-growth watcher.

## Phase 3 — THE CHARACTER · data DONE

**`data/hud2/scene_map.json`** (6/6 sources verified): place+weather+fire (`room_state.json` — a
small finite state space, ideal for tableau-swapping), objects present (`world_substrate.json`,
including his own observation ledgers + inferences per object), the cat (`cat_state.json`), current
book+bookmark (`reading_state.json`), what he's doing right now (`train_state_log.jsonl` tail),
psychological climate (`climate_state.json`).

## Upkeep

Re-run all three builders after structural changes (new organs, moved logs, new lines):
`build_hud2_manifest.py` · `build_hud2_transit.py` · the scene block (in the transit session
notes). Cheap, deterministic, zero LLM. The courier delivery log activates at Du's next restart.

---

## THE HUD2 BUILD BRIEF (originally written for and handed to Antigravity verbatim, 2026-08-21;
kept below exactly as written — the historical record of what was actually specified and built. Per
D-0306, 2026-09-28, Claude is now this brief's own implementer too: read "you"/"your" below as
whoever is building or extending the rendering app, no longer a hand-off to a separate party.)

You are building **HUD2** — a live visual observatory for Nascence, a continuously-running
synthetic-psyche project at `C:\Nascence` (a single mind, "Du", living in a simulated coastal
cottage world: study, garden, shore, wood, a cat, weather, tides, letters). This is a NEW
standalone web app, built in THREE PHASES, in order. Ship each phase working before starting the
next. It must be visually striking — this is the flashy one; 3D encouraged (three.js or similar),
dark, alive, beautiful. Full aesthetic freedom within the hard rules.

**HARD RULES (all phases)**
1. READ-ONLY: you may read files under `C:\Nascence\data\` (and only there). Never write, create,
   delete, or lock anything under `C:\Nascence`. Your app, server, caches live in your own project
   folder, on your own port (NOT :8080 — that's the existing diagnostic HUD; don't touch or
   replicate it).
2. Do NOT import or execute any Nascence python code. The three manifest files are your entire
   interface: `data\hud2\brain_graph.json`, `data\hud2\transit_map.json`, `data\hud2\scene_map.json`.
3. The sim may be stopped; files may be absent or mid-write — tolerate every read failure silently
   and keep rendering. A missing file is quiet, never an error screen.
4. Local only (127.0.0.1), one user, Chrome, desktop.
5. **TRUTH RULES (the project's culture — non-negotiable):** never invent activity. No decorative
   pulses, no fake shimmer pretending to be data. If nothing fired, it's quiet — and a quiet mind
   should still look beautiful. Don't label anything "thinking" or "consciousness"; these are
   organs (scripts) firing and freight moving, and the honest framing is the impressive one.
   Where a manifest marks something `freight_visible: false`, show the line with visibly-unwatched
   freight — never simulate it.

**SHARED LIVE PROTOCOL** (also in each manifest's `protocol` block): every manifest names files
with `kind` and `ts_key`. Poll file sizes ~1s. Size grew on an `events` file ⇒ that thing just
fired — read only the appended bytes; each line is one JSON event, timestamp under `ts_key`.
mtime changed on a `state` file ⇒ re-read the (small) file. Manifests carry `generated` + `schema`
(brain/scene 1, transit 4); if schema exceeds what you built against, show "manifest updated — rebuild me"
rather than guessing.

### PHASE 1 — THE BRAIN (`brain_graph.json`)
A living 3D brain-graph of the 186 organs of Du's mind: `nodes[]` (id, human `label`, `group`:
core/memory/nodes, `loc`, `logs[]` — the files that prove the organ is alive) and `edges[]`
(import relationships — who feeds whom). Cluster by group, size by something honest (activity
rate or loc), edges as faint synaptic threads. When an organ fires, it LIGHTS — a pulse that can
travel its edges. Idle organs dim, never vanish. `core.memory.store` is the most-connected hub
(61 in-edges) — let the layout discover that naturally. Include: hover → label + recent raw event
lines; a time dial/trail replaying the last N minutes; a calm ambient mode and an inspect mode.
Frame rate over completeness — cull faint edges dynamically if 558 is heavy.

**Founder's request 2026-08-21, verified buildable:** *"I really want the brain layer to light up
and flash on nodes he is actively using."* Du is genuinely running as of this note (verified: a
fresh T2 synthesis + climate tick within the last minute) — the data already supports this
animation (every node's `logs[]` carries `kind`/`ts_key` for exactly this purpose); if the current
build looks static, this is a rendering/animation task still to wire, not a missing-data problem.

### PHASE 2 — THE TRAINS (`transit_map.json`, schema 4 — TWO rounds of founder corrections from watching the rendered map, 2026-08-21)
**SCHEMA 4, the founder's SECOND correction, read this first:** *"World layer should not be a
train, it is a factory that the stations use."* A train loops and stops at stations; a factory is
a stationary production site a train's platform reads from while stopped there. The manifest now
has **`trains[]`** (4: conversation, idle, deep, witness — the only things that actually loop and
carry an LLM platform) and a separate **`factories[]`** (11: weather_sky, tide, season_daylight,
garden, fire_woodpile, cat, peers, objects, school, body, climate — world-driven production sites,
none of which loop or stop anywhere). **Render factories as stationary nodes/depots, NOT as
tracks** — that was the schema-2/3 mistake.

Each factory carries **`consumed_by`**: the train id(s) whose platforms verifiably read it, plus a
`consumption_verified` field naming the exact source line proving it (e.g. weather_sky is read by
`nodes.inner_monologue_node:1246-1248` before every idle thought). **Draw a real connection from a
factory into its consuming train(s)** — this is the mechanism for "stations use factories." An
empty `consumed_by` means not yet traced, not "never used" — render those factories plainly,
without inventing a connection.

**Trains, stations, platforms, sidings** work as before: **6→5 stations** (11441 was fully removed
this session — see below), **38→42 platforms** (four more hand-verified bespoke-wrapper calls
found, see below), **5 sidings** (thought-train circling, deliberation passing loop, reentry
shunt, T2 retry lap, T4 branch) — draw as real track loops off a train, animated when their
evidence moves.

**Couriers now carry a real, verified `destination`** (founder: *"buses... should show on the map
rather than just being boxes that move around with no apparent pattern"*) — `destination_kind`:
`"train"` (3 of 4 routes ultimately land in the idle train's own perception stream — verified via
`wandering.perceive()` and the look-render path) or `"ledger"` (`calibration_sync`, which writes to
a data store the competence model reads, not a perceived stream — genuinely different, render it
differently). **Animate each courier traveling FROM wherever it's triggered TO its real
`destination`** — never an aimless wandering box.

**"Follow Du's thoughts around the map" — the founder's ask, and how the data now supports it:**
a single idle-train tick is a traceable path, not a guess: a factory's evidence changes → within
the same window one of the idle train's platforms fires (`train_state_log.jsonl` gains a row) →
a courier may deliver in the same window. Every one of those edges is now a VERIFIED source-code
binding (via `consumed_by`/`consumption_verified` and courier `destination`), not proximity
correlation — so animating factory → (courier) → idle-train platform → its train_state_log entry
as one traveling pulse is honest even when unrelated files happen to touch in the same second.
**If true real-time animation looks incoherent** (bursty/out-of-order touches — plausible since
several factories share one physical file), **a small server-side buffer (~10s, replay in strict
ts order) is a sound fix** — your own server's concern entirely; every file already carries a real
timestamp to order by. Full guidance lives in the manifest's `protocol.follow_a_thought` and
`protocol.buffering` fields — read those directly, they're written for exactly this feature.

**Everything found and fixed this session (read in order — each was a real bug, not a rendering
choice, all traced to the manifest or to Du's own routing table, never to your rendering):**
- `line: "service"` is NOT a train — non-revenue depot/utility track (shared infrastructure many
  trains pass through), never a mystery loop with no station.
- `tide`/`season_daylight` are honestly `freight_visible: false` — pure clock functions, no
  persisted file; don't invent one.
- `weather_sky`/`fire_woodpile`/`garden` share one physical file but each carries a `watch_key` —
  watch only that JSON key so they read as genuinely distinct, not retracing each other.
- `school` has no dedicated platform — its LLM work rides whichever idle-train platform invokes it
  (verified injected-callback pattern). Draw it as a factory with no station stop of its own.
- **The Witness DOES call an LLM** (hand-added — a bespoke wrapper the generic scan couldn't see),
  and targets a SECOND resident model (deepseek-r1:7b) on the same port the subconscious uses for
  phi3:mini — `stations[].also_hosts` names it.
- **`station_11441` was fully REMOVED** (not just flagged) — verified nothing was listening
  (`Test-NetConnection` false) and Du's own launch script says it's manual-only, "NOT started by
  default." Cleaned up in `core/model_client.py`. **Stations are now 5, not 6.**
  **UPDATE 2026-08-23 (plan-overlap audit):** this finding was accurate for its own session — the
  port is manual-only by design, not permanently dead. It has since been manually started for
  `epistemics_phase_c.md`'s Tier-3 work: re-verified live via `Test-NetConnection` (true) and a
  direct `/api/tags` query confirming `command-r7b` is actually being served. Not a contradiction
  of this finding, just a later manual start — don't read "fully REMOVED" above as still current
  without checking the port again first.
- **A systematic sweep for every bespoke LLM wrapper** (founder's direct ask) found THREE more real
  platforms invisible to the generic scan: `judge_panel.py`'s own TWO PRIMARY judges (JUDGE_1
  gemma4:12b, JUDGE_2 falcon3:7b — fire on EVERY panel ruling, hundreds/day, the single biggest
  undercounts on the whole map) plus its tiebreak escalation. All three hand-added with real
  evidence logs (`judge_panel_log.jsonl`, filterable by verdict field).
- Also found, not fixed (informational): `core/deliberative_judge.py` is fully built with ZERO live
  callers anywhere — a genuinely unwired module, not a miscounted platform.

**Visual note (founder feedback on the actual render):** the current schema-2/3 Transit Map scene
reads as an abstract structure (coiled tubes, floating towers, a legend overlay) rather than
anything recognizable as a metro/train system. That's a rendering-legibility call entirely yours,
but worth surfacing plainly since it was the founder's own reaction. Also seen: the on-screen
legend was static descriptive text written once (still describing "Station 11441 (Orphaned)"
after that station was fully removed from the live data) — **derive legend/callout text from the
manifest's live content each load**, never bake a finding in as fixed UI copy.

### PHASE 3 — THE CHARACTER (`scene_map.json`)
Du in his world, now — and this world has REAL AUTHORED GEOMETRY, so build the scene from truth,
not invention: `scene_map.json`'s `geometry` source names four hand-authored 3D coordinate fields
(`data/world_geometry/{study,garden,shore,wood}.json` — metric positions for every fixed feature:
fireplace, mantel, doors, desk, gate, tide-line; 24 named standpoints; cat spots; sound sources;
each file documents its own frame). `du_position` (`data/position.json`) gives Du's live
{place, standpoint} — his exact coordinates come from the geometry's standpoints; the `bindings`
block in the manifest spells out how Du, the cat, the fire, and movable objects resolve to
positions. `spatial_render` is the egocentric scene EXACTLY as Du himself perceives it (live since
08-18) — use it to caption what he sees. Beyond geometry, the scene is driven by six more verified
sources — location (study/garden/shore/wood) + weather + wind + fire state + woodpile
(`room_state.json`), the objects around him with his own observation notes (`world_substrate.json`),
the cat and where she is (`cat_state.json`), the book open on his desk with his actual bookmark
(`reading_state.json`), what he is doing/thinking right now (`train_state_log.jsonl` tail — you may
show the current thought as ambient text), and the psychological climate (`climate_state.json`) as
subtle atmosphere. The state space is small and discrete — build it as tableaux that swap and blend
on state change, not physics. When the sim is stopped, render the world still and true (the fire's
last known state, the weather's last front) with a quiet "asleep" treatment.

**Two real bugs found 2026-08-21, verified against live files (not a guess):**
- **The "ASLEEP" badge is showing when Du is genuinely awake.** Verified live: `room_state.json`
  had just been written (46s old) and a fresh T2 synthesis had fired, while `position.json` was
  ~28 minutes stale — Du can go 20–30+ minutes without physically moving while thinking hard, and
  if your liveness check keys off `position.json`'s mtime alone, a long still-thinking stretch
  misreads as sleep. **Recommend checking `room_state.json`'s mtime instead (or the freshest of
  several always-ticking files)** — it updates every sensorium tick regardless of whether Du
  moves.
- **The spatial caption and the standpoint panel can show two different MOMENTS at once.**
  Verified with real timestamps: `spatial_render`'s last logged caption said "the garden" (logged
  17:12) while `du_position`'s standpoint said shore (written 17:22) — Du had walked from the
  garden gate to the shore path in the ~10 minutes between those two writes, and the scene showed
  both snapshots together as if simultaneous. These two sources update on different cadences
  (`spatial_render` only logs on certain look/render events; `position.json` updates on every
  locomotion step) — **recommend deriving the caption fresh from the current standpoint/place when
  they disagree**, or clearly timestamping which moment the caption belongs to, rather than
  trusting the last logged prose line as always-current.

Architect the app so all three are scenes of one observatory with shared file-watching plumbing.

**Related (noted 2026-08-23, plan-overlap audit):** Phase 3's scene map (`scene_map.json`) is built
directly from `spatial_perception.md`'s `data/world_geometry/{study,garden,shore,wood}.json`
files — the exact deliverable that plan designed and built — without citing it by name. Functionally
correct (verified live 08-18 per that plan), just uncited.
