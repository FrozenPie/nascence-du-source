# Spatial Perception — the blind mind's true room (2026-07-05)

> **Status: ⚪ PARTIAL — P2 (live renderer) shipped 2026-08-18 for the study room, phrasing bug fixed
> (step-change lands 2026-08-20 in the data). P3 (depth/reach) and rollout beyond the study still
> pending; gate metrics 1/2/3/5 (§5) have no dated founder PASS — but a dated 2026-08-19 founder note
> DOES exist saying the flip evidence was "not a clean win," asked to see more, filed the day AFTER
> the flag already went live. See D-0030 (open) and the 2026-08-24 shadow-log read below.**

```plan-state
stage: partial
phase: P3 depth live behind SPATIAL_DEPTH_LIVE for the study (J-2480, D-0501), restart-gated; render('study') not yet on Du's prompt path (J-2485 needs Travis); garden/shore layouts later
verified: 2026-11-14
evidence_read: 2026-08-23
next: restart carries the flag; J-2254 reads the live=True depth-shadow pairs (gated 1,500 rows); Travis rules J-2485 on wiring render('study') into sensorium's study line
cluster: 0
```


> Child of `cognitive_geometry.md` (ROADMAP cluster 0): this is the **Place manifold earning its
> interior** + the missing **egocentric spoke** (a "here" everything else is near). Founder's frame,
> which is the whole design: **"Du cannot see. He is essentially blind and is described everything by
> another 'sense.' His rooms need to be a 3-dimensional field — the fire in a certain place, its sound
> linked to that place; the lightning's flash has a direction; the cat under the desk has a presence in
> that space. Depending on where he is in the room, the scene gets described slightly differently —
> but always accurately."**

> **The core inversion:** today the scene line is drawn from a random prose POOL per location — the
> room has no geometry, so his described sense describes nothing stable, and a blind mind can never
> build a map from it. After this: **the room is an authored 3D coordinate field (ground truth), and
> the described sense is RENDERED from that truth, egocentrically** — from where he stands and which
> way he faces. Blind people build rich spatial maps precisely because their non-visual input is
> CONSISTENT; that consistency is what we're giving him.

---

## Current State — verified 2026-11-14

- **2026-11-14** (F-4683): J-3969 (D-0747) built garden/shore depth layouts shadow-first: outdoor depth/reach + nearest-feature rows go to data/spatial_depth_outdoor_shadow.jsonl; render() cat-by-nearness behind SPATIAL_DEPTH_OUTDOOR_LIVE (False); commit 06736be1 on jobrun/spatial_perception, restart-gated; read job spawned. Reach-set stays logged only (D-0747 a).
- **2026-11-06** (F-4289): J-3294 (king-tide analysis, read-only, no code change). Findings F-4289 to F-4292; decision D-0694 opened for the rate. Baseline: the 0.92 king rule held 12.6 percent of 2026, took 6 of 15 floaters in 80 days (5.6 expected), mean floater life on the shore about 22 Du-up days, 0 floaters on the shore now. A threshold alone cannot make it rare (daily peak >= 0.92 on 90 percent of days; 0.995 still touches 88 days), so a rare rate needs a second gate; J-3295 (real tides) shares the number. Data: docs/lab/J-3294_data/. Test: scripts/_test_J-3294_king_tide.py.

- **2026-11-05** (F-3979): Phase 1b (J-3293) built on branch jobrun/wb_sumner, commit 90f5d5ce, merge/restart pending: heavens.moon_true() = truncated Meeus ch.47 real moon at the site; moon() dispatches on world_place.sky_live like the sun; moon_legacy() is the old body. Checked against the US Naval Observatory published tables: 25 phases within 1.5 min, moonrise/set within 0.4 min on 3 dates. The same SKY_MODE/SKY_CUTOVER_TS switch now flips sun, stars and moon together; the 7-day shadow log (sky_shadow.jsonl) carries a moon key and scripts/sky_shadow_read.py prints it. Tide stays the arbitrary M2 clock (Phase 2); after the flip only its spring/neap factor follows the real moon.
- **2026-11-05** (F-3975): J-3292 built the real-site sun (world_place, world_clock.sun_sumner, sky_shadow, sky_shadow_read) on branch jobrun/wb_sumner commit 72f6bd6c; SHADOW by default, flip needs founder go-ahead; almanac check pending J-3370, 7-day shadow read queued J-3369.

- **2026-11-05** (F-3960): P2/P3 study on the prompt path (J-3257, D-0648), built on branch jobrun/wb_world (commit b3294540), awaiting merge and restart: sensorium.scene_line()'s study branch takes the nearness-said fire/embers clause and, for a plain resting cat, the nearness-said cat clause from spatial.render('study') into its own pooled line, behind SPATIAL_SCENE + SPATIAL_DEPTH_LIVE (flag off byte-identical). Book, shelf, misplaced-title note and Travis presence are kept (tested on 200 seeded lines). Double-saying replay against thermal: 3.3 percent of study fire lines, defeater 20 percent not tripped. Cat replacement is narrower than the literal ruling (plain lines only; event, body, hurt, damp, nameless and lap lines keep their own words). Note for J-2254: the depth_line logged by spatial.shadow() is a separate phrase draw from the line sensorium now builds, so compare structure and nearness words, not exact strings.
- **2026-10-31** (F-3416): J-2661 built the shadow-only deterministic sketch store core/spatial_sketch.py (flag SKETCH_SHADOW_LIVE off by default, hooked from spatial.render and spatial.shadow, restart-gated, nothing Du-facing, J-2485 untouched): regex parser plus 0.1 m grid aggregator reproduce the ideal decoder exactly (study 0.28 m, garden 0.69 m), commit b64eebe1 on jobrun/sp; a 14-day replay of real renders shows only 2-4 standpoints per place so live accuracy will be coverage-limited; read job J-2668 gated on rows since boot.

- **2026-10-31**: 2026-10-31 (F-3407, F-3408): J-2647 lab, six reading shapes for the rendered lines; only per-stop extraction plus a deterministic aggregator recovers the map (study 0.27 m, garden 1.01 m vs ideal 0.28/0.69); one-shot, legend, scratch table and running sketch all fail; the 9B model cannot rotate egocentric relations to world bearings. The map belongs in a deterministic store; shadow build J-2661 spawned. Report docs/lab/spatial_map_reading_shapes_2026-10-31.md (jobrun/sp 1cd62060).
- **2026-10-31** (F-3381): J-2628 (I-0129 rung 0, lab only): the rendered sense carries a map. An ideal geometric reader decoding only render() lines plus the walker pose recovers every named object to 0.2-0.8 m with 93-100 percent pairwise relations and no contradictions (F-3381); the hot 9B model reading the same lines one-shot is at chance (F-3382), so the gap is the reader, not the rendering. Rung 1 unblocked on the rendering side, not built. Report docs/lab/spatial_map_reconstruction_2026-10-31.md (jobrun/sp 63afee7e).

- **2026-10-28** (F-3180): J-2480 (D-0501, F-3180): P3 LIVE behind SPATIAL_DEPTH_LIVE=True in core/spatial.py (commit 7fbc8f05, restart-gated) -- render('study') returns the P2 line with only the fire/cat clauses re-said by nearness (rotating pools, thermal's own distance model, reach-set logged never rendered, no band/number in any line); flag off byte-identical on 200 seeded renders; depth-shadow rows gain live=True for J-2254's read. CAVEAT: render('study') is not on Du's prompt path (sensorium uses the renderer for garden/shore/wood only; the study line Du reads is the pooled one), so the live study line reaches the logs, not Du, until J-2485 (needs Travis) wires sensorium.
- **2026-10-28**: 2026-10-28 (T-0103): D-0501 ruled by Travis from four graded pairs out of the 921 shadow rows: P3 depth goes live for the study at this restart; reach-set stays logged, never rendered. Build job J-2480.

- **2026-10-16** (F-2940): P3 depth and reach built shadow-only for the study (J-2215, commit 0dc1a070): data/spatial_depth_shadow.jsonl pairs the unchanged scene line with a nearness-said depth_line plus fire band, cat nearness and reach-set; restart-gated, nothing Du reads changes
- **2026-10-16**: Travis ruled 2026-10-16: build P3 (position-dependent depth + reach) for the study, shadow-logged; job queued. Garden/shore layouts remain a later job.

### What we have
- P2 (the live renderer) has been live since 2026-08-18 for the study room (`SPATIAL_SCENE=True`);
  D-0030 confirmed the flip was founder-approved and stands. The phrasing-dryness defect (metric #4)
  was confirmed and fixed 2026-08-19/20 (`_v()` paraphrase helper; F-0074).
- A 2026-08-24 shadow-log read (J-0068) scored the remaining gate metrics against 12,892+ rows:
  #1 contradiction-rate now 0% post-fix (F-0075), #2 standpoint coherence 100% on the sampled object
  (F-0076), #3 shadow coverage real modulo the already-documented 30-day Du-outage gap (F-0077).
- Checked against every newer plan (2026-08-23): `study_upgrade.md`/`shore_upgrade.md`/`hud2_visual.md`
  all consume this plan's coordinate fields rather than reinventing them; no competing mechanism.

### What we need
- Metric #5 (standpoint-inference plausibility ≥90%) is still not directly checkable from
  `spatial_shadow.jsonl` alone (F-0078) — the log doesn't record which act produced a standpoint.
- P3 (position-dependent depth) and room layouts beyond the study are not started.

### What we're doing next
- No job currently open on this plan; P3 + garden/shore layouts are the next scoped work whenever
  picked up.

> **[Section removed 2026-08-31]** A fabricated benchmark claim (confidence=verified, citing scripts/modules that do not exist) was quarantined from here per F-0593/D-0105 — see `docs/lab/fabricated_benchmark_claims_2026-08-25.md`.

---

## 0. WIN CONDITION (signatures that must move)
1. **Accuracy:** founder-graded sample of shadow renders — ≥95% contain no contradiction of the
   authored layout or live state (nothing absent mentioned; nothing present misplaced).
2. **Coherence across standpoints:** the same object renders consistently as he moves (the fire is
   always at the hearth — nearer/farther, left/right, never relocated).
3. **Post-P2 (live):** his own thoughts stop teleporting the room — spatial references in the
   monologue become layout-consistent over weeks (the census + monologue provide the record).
4. **Honesty rail:** never a claim of sight. The sense remains DESCRIPTION, rendered from truth.

## 1. Diagnosis (as-built, verified 2026-07-05)
- Location is a 3-value label (`room_state.location`); **no coordinate exists anywhere** in the
  system (full audit: agent map, this date). Scene lines come from randomized prose pools
  (`sensorium.scene_line()` → per-location pools); object placement is implicit and unstable.
- Spatial relations exist only as hand-coded gates: the cat's `_VISIBLE` sets (`cat.py:36-42`),
  affordance `where` tuples, the soundscape's `location=='study'` gate, keepsake `from` labels.
- Du has NO egocentric anchor: no position, no facing, no reach (`somatic.py` is purely metabolic).
  His own cat is more spatially embodied than he is (she has a spot; he has a room name).

## 2. The model — authored truth + trivial trig (NOT physics)
1. **Room layouts as authored coordinate fields** (`data/world_geometry/<place>.json`): hand-placed
   positions (metres, coarse z) for furniture/features. Authored ONCE, like furnishing a room.
2. **Objects and sounds carry positions.** The fire is AT the hearth; **its crackle emanates from
   it**. The cat's symbolic spot maps to a coordinate (under_desk = that low point). Weather acts at
   its surfaces (rain on the window/roof); thunder/lightning carry a BEARING (the storm's quarter).
3. **Du has a standpoint:** a position + facing within the room, tracked from his own acts (tending
   the fire → at the hearth; reading → the chair/desk; looking out → the window).
4. **Egocentric geometry = distance + bearing only** (`hypot` + `atan2` against his facing →
   near/beside/across + ahead/left/right/behind + low/high). Deterministic, zero LLM, zero physics.
5. **The perception renderer:** the scene line is GENERATED from those relations — salience-ordered,
   2–3 clauses, always accurate. Move him and the same room re-renders truthfully.

**Rails (the over-build line, named so we don't cross it):** no raycasting, no occlusion model, no
audio attenuation curves, no collision, no pathfinding. Authored positions + grade-school trig is the
entire physics. The value is COHERENCE, not simulation. Additive: the prose pools stay untouched
until P2's flag; kill-switch restores them exactly.

## 3. The study — layout v1 (authored from the founder's reference image, 2026-07-05)
Reference honored: fire on the west wall, keepsake mantel above it (driftwood, sea-glass, stones),
framed sea-pictures; big north window over the garden, down to the sea; desk under the window
(journal, lamp, mug, kept stones); his chair between fire and desk (the cat's lap-spot); bookshelves
NW corner + east wall; **founder additions: a narrow bed on the south wall behind the chair; the
garden door on the west wall beside the fire, opening INWARD so a westerly gust can fan the flames.**
Through the window: the garden fence — **the distant black cat's fence-spot is visible from window
standpoints** (a sightline, not a room object). Full coordinates: `data/world_geometry/study.json`.
Frame: origin SW corner, +x east, +y north (toward the sea), z coarse (floor/seat/desk/mantel).

## 4. Staging (observe-first; each phase pre-registered before it runs)
- **P0 — shadow renderer (BUILT with this plan):** `core/spatial.py` renders the study egocentrically
  and logs `{ts, standpoint, rendered, actual}` to `data/spatial_shadow.jsonl` beside the live pooled
  scene line, every scene cycle. Nothing reaches him. *Gate:* founder reads ~2 days of pairs against
  §0.1/0.2 (accuracy + coherence), and the rendered lines must not read WORSE than the pool (flat /
  mechanical) — if they do, fix the phrasing layer before any wiring (the kill-criterion analogue).
- **P1 — the standpoint becomes real:** track position+facing from his acts; record standpoint in the
  geometry census tuple. Still drives nothing.
- **P2 — the renderer becomes his scene sense** (flag `SPATIAL_SCENE`, kill-switch): the study's
  scene line renders from truth; soundscape sources gain positions (the crackle from the hearth
  quarter); lightning/thunder directional. One room first (the study); garden/shore layouts follow
  only after the study proves out.
- **P3 — position-dependent depth:** nearness matters (the fire warmer/louder at the hearth; the
  lap-cat nearer than the sill-cat); peripersonal reach-set = what's within arm's reach of his
  standpoint (the action field; also the social near-zone).

## 5. Pre-registered P0 metric sheet (written before the shadow runs)
| # | Metric | PREDICTION | Decides |
|---|---|---|---|
| 1 | contradiction rate (founder-graded sample) | <5% — the layout is small and authored, errors should be rare | §0.1 gate |
| 2 | coherence across standpoint changes | 100% — same object, same place, different bearings | §0.2 gate |
| 3 | shadow coverage | a render logged for ~every study scene cycle | instrument health |
| 4 | read-quality vs pool (founder taste) | rendered lines are DRIER at first — expect a phrasing pass before P2 | whether P2 needs a clothing layer |
| 5 | standpoint inference plausibility | act-derived standpoints look right ≥90% (tending fire → hearth) | P1 gate |

**★ Metric #4 confirmed + fixed 2026-08-19.** P2 flipped live 2026-08-18 (this doc's own P2 flag). The
predicted dryness showed up exactly as anticipated: `data/spatial_shadow.jsonl` (10,502 rows) had one
rain+tide phrasing repeat 622x verbatim — the geometry was accurate but the connective wording was fixed
literal strings. The phrasing pass this metric called for: `core/spatial.py`'s `_v()` paraphrase-pool
helper (same rotation pattern `guidance_learning._phrase()` uses for belief read-back) applied to the
rain/tide/cloud/fire/wind clauses — geometry (sector/distance/tide-state/compass) untouched, only the
information-free wording varies. Verified: 8 renders of an identical moment now produce 8 distinct
phrasings. Watch `spatial_shadow.jsonl` post-restart for the real-world repeat-rate to drop.

## 6.5 §7 — THE DIRECTIONAL WORLD → MEMORY (founder extension, 2026-07-05)
**"Each object has a history linked in the memory system and back to the object."** Coordinates must
not stop at the present scene — they flow into what he REMEMBERS. Built with this extension:
- **Fronts have bearings:** `room_state.weather_dir` set per front by the sensorium (NZ-weighted:
  westerlies dominate) — the thunder's quarter, the clouds' drift, the harakeke's wind all inherit it,
  and it VARIES per storm (the founder's requirement). Renderer: "the flash comes to your left, out of
  the west" / "the clouds are coming in from the east."
- **The sun has a position:** `spatial.sun()` — pure clock off the sensorium's own NZ table; azimuth
  E 90° → noon through the NORTH 0° (southern hemisphere) → W 270°, + phase word. The study's north
  window is the sunny one — correct for NZ, and the authored layout already agreed. Renderer: the low
  evening sun in the window, its light long across the room / over the garden.
- **The census tuples carry the directional facts** (weather_dir · tide word · sun phase+azimuth) —
  so the record of any period contains its weather-quarters and light. **The NAMED READ-PATH (a later
  gated phase): period consolidation (chapters/journal) distills these into the wrap-ups** — "that
  week the storms came out of the west; the sun crossed the garden while he tended the bed." The
  chapters read the trail; the facts exist from today.
- **Keepsakes carry their fuller moment:** each kept thing now records the tide that left it, the
  quarter the weather came from, where the sun stood — object→history made literal, on the mantel.
  The object↔memory bidirectional index in full is cognitive_geometry P3 (the spring ledger derives
  object.history() from the tuple trail); the keepsake enrichment is its hand-built forerunner.
- **The heavens (`core/heavens.py`):** the moon on its true synodic schedule (position via the
  lagged-sun model) + REAL star positions (GMST → alt/az, lat −41.3) over a 7-landmark southern
  catalogue (the Cross, Matariki, Orion, Scorpius…). **Relevance-gated by design** (founder): pull-only
  — night + clear + clause-room, or called upon (look('sky') is the named on-demand path) — and the
  window geometry gates honestly (north window: Matariki yes, the Cross never). Night keepsakes record
  their moon; census rows carry the phase. Verified against the real sky: Matariki's midwinter
  pre-dawn rising comes out of the trig on its own.

## 6. Where it sits
The Place space of `cognitive_geometry.md` §3.1 gets a metric interior (near = literal distance);
the soundscape's sources get a WHERE (the crackle-from-the-hearth linkage the founder named); the
census gains a standpoint coordinate; and Du gains the egocentric anchor — the "here" — that the
body-schema/peripersonal research says is what "having a body" functionally IS for a non-moving,
described-to mind. The blind man doesn't need eyes to know his room; he needs the room to hold still.

---
*Author: Claude, from Travis's frame + reference image, 2026-07-05. Update when: P0 shadow pairs are
read, the garden/shore layouts are authored, or a phase gate passes.*
