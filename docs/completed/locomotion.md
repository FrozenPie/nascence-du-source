# Locomotion — Du gets a body in space (Option C, full; 2026-08-15)

> **Founder decision (this session): full within-place locomotion, not the halfway version.** "B is
> just a halfway attempt… knowing me, I will forget there was an option C until way down the track.
> We are pretty good at half implementing things." So this plan is written against half-implementation:
> §6 is a DONE checklist, and there is no deferred core. One flag (`LOCOMOTION`) exists for rollback
> only, never as a staging state.

## 1. Why — the standing dishonesty, and what it costs

Du **teleports**: `sensorium.move()` sets `state["location"]` instantly (~15 jumps/day). Meanwhile the
world narrates walking everywhere — "you walk the tideline", "you carry an armful up to the woodpile",
and the gate-glimpse code literally reasons about "what any walker would see in passing" for a walk
that does not exist. Found this session: **the wood's near-zero visits are caused by teleportation** —
it is authored as *on the path* between garden and shore, and he jumps over it. Costs of the missing
body: no distance-as-cost (place-switching is free → part of the 71% shore-share), no journey
event-boundaries in memory, no weather-en-route, no honest self-sounds (footsteps were about to be
built for feet he doesn't have — caught by the founder).

## 2. What already exists (audited 2026-08-15 — the geometry was BUILT for this)

- **4 authored places, one compass, real metres**: study 4.2×5.2 (a true room) · garden 10.5×12.5 ·
  wood 24×20 · shore 30×20.
- **24 named standpoints** with pos + facing + purpose-notes:
  study `in_the_chair · at_the_hearth · at_the_desk · at_the_window · at_the_door · by_the_shelf ·
  on_the_bed · mid_room` · garden `at_the_door · at_the_bed · by_the_fence · at_the_gate ·
  under_the_tree · mid_garden` · wood `on_the_path · by_the_oak · gathering · at_the_gap` ·
  shore `at_the_path_foot · on_the_shingle · at_the_tideline · at_the_pools · on_the_rocks ·
  by_the_driftwood`.
- **`spatial.render(room, standpoint=None)` already takes the standpoint and falls back to a default —
  nobody supplies the real one.** C's core is filling that argument with truth.
- Somatic energy/fatigue vars exist; footstep sounds are specified (sound_world_expansion §1);
  the topology is already stated in code ("every path between the cottage and the sea passes the
  garden gate; only shore↔wood skirts it").

## 3. The model

**Position = (place, standpoint).** Standpoint-resolution, not continuous xy — that is the geometry's
own granularity (coarse metres; nothing renders finer). Continuous xy is *rejected for now with
reason*, not deferred-by-vagueness: it would add state no renderer, memory, or percept consumes.

**3.1 Within a place — instant resolution, honest position.** The study is a room; crossing it takes
seconds — under any tick. So within-place movement resolves inside the act that needs it: "write a
letter" moves him `at_the_desk`, narrated in the act's own prose ("you cross to the desk"), position
state updated, a footstep sound fired, a somatic micro-cost added. **Acts carry their own movement —
that is not fabricated agency** (humans do not will each step); the act was his, the walking is its
physics. `look()` and the scene line render **from his actual standpoint** — the spatial renderer's
accuracy law finally gets a true origin, and the founder's original purpose ("things always in the
same place, from memory") completes: what he sees from the chair differs from what he sees at the
window, consistently, forever.

**3.2 Between places — journeys, leg by leg, in real time.** Topology (authored doors/gates/paths):

    study ─(the door)─ garden ─(the gate, down the path)─ wood ─(the path's foot)─ shore

A move to a non-adjacent place is a **journey**: legs complete on wall-clock (~60–120s each,
weather-scaled — a storm makes the shore genuinely far). During a leg `state["location"]` IS the
transit place — every existing reader stays honest, the census records the visit, transit thoughts
happen *in the wood*, `fragment_context` stamps memories laid down en route. Exits and entries use the
real standpoints: he leaves the garden **by the gate** (where the flag-glimpse now happens
geometrically), enters the wood at the path-top gap, comes off the path at the shore's path-foot.
Arrival is narrated as an experience ("the trees open and the sea stands up in front of you").

**3.3 Agency law.** The destination is always his (the ACT move latches are untouched — only
resolution changes). Mid-journey he is *genuinely* in the transit place: if something catches him
there — the fantail, a fallen limb across the path, a thought — staying is his choice, not an
interruption of the system's plan. The world supplies physics, never itinerary. School's reel-back
becomes a walk home (even being marched to the desk takes the path). No teleport remains anywhere.

**3.4 What rides on top (same wave, not later):**
- **Footstep self-sounds** per ground (shingle/leaf-mould/floorboards) fire on legs and crossings.
- **Somatic coupling**: per-leg energy cost (uphill legs cost more — shore→garden is the climb);
  gathered loads slow the uphill leg a touch (his labour has weight).
- **Weather exposure**: rain en route dampens him (the somatic/mood systems already read such state).
- **Transit percepts** in house voice per leg+direction+weather (a small authored pool, wood-heavy).

## 4. Touch points — the honest full list (anti-half-implementation)

| Surface | Change |
|---|---|
| `core/locomotion.py` (NEW) | position state (`data/position.json`), topology, journey state machine, leg advancer, narrations, costs, footstep/sound hooks |
| `sensorium.move()` | initiates a journey instead of setting location; instant only for same-place |
| sensorium tick | advances pending journey legs by wall-clock; journey watchdog (a stuck journey COMPLETES and logs why — instruments must say why they're silent) |
| `spatial.render` / scene lines / `look()` | fed the live standpoint |
| Act sites (desk/fire/bed/shelf/letterbox/bed-tending/gather/tea/keep) | resolve within-place position + narration + footsteps |
| school reel-back | a walk home through real legs |
| gate-glimpse | fires at the gate standpoint (now geometrically true) |
| geometry census tuple | gains `standpoint` field |
| `fragment_context` | gains standpoint via the tuple (schema already carries what tuples carry) |
| HUD | 'where he is' card gains standpoint texture (optional line, same file) |
| soundscape | footstep sounds registered (known-instantly class); ambience unchanged |

## 5. Risks & edges

- **Sleep/dream mid-journey**: sleep is a process, not a place — he sleeps where he is; if pressure
  crests mid-walk he finishes the leg first (legs are ≤2 min; no special case needed beyond that).
- **Journey stuck** (process restart mid-walk): position/journey state persists; on load, any journey
  older than its max duration completes immediately with a log line naming it.
- **Latch compatibility**: move-cue parsing unchanged; only what happens after.
- **Cadence**: ~15 moves/day × ≤2 legs ≈ 20–30 min/day in transit — human-proportionate; the wood gets
  ~8–12 brief daily presences (watch item).
- **Rollback**: `LOCOMOTION=False` restores instant moves exactly. Rollback flag, never staging flag.

## 6. DEFINITION OF DONE (the founder's guard against ourselves)

☑ No code path sets `location` without passing through locomotion — grep-verified 2026-08-15: the
  only setters are locomotion.tick (sanctioned) and sensorium's LOCOMOTION=False rollback branch
  (documented exception). (cat.py sets the CAT's own location — hers, not his.)
☑ Act sites resolve position: fire light/stoke → hearth · tea → hearth · water_bed → bed ·
  letterbox fetch → gate · gather → gathering/tideline (+ wood now CARRIED, deposited on arrival
  home) · driftwood haul → by_the_driftwood · letter-writing → desk. NOTE (honest): `on_the_bed`,
  `by_the_shelf`, `keep` have NO act functions that imply movement today (looks don't move); nothing
  was skipped — there is nothing to wire until such acts exist.
☑ Scene/look render from live standpoint (spatial.render defaults to locomotion's truth; the
  parameter that waited since 07-05 is filled). Transit narration leads the scene line, consume-once.
☑ Journeys traverse the full chain with transit presence, weather-scaled legs, somatic cost
  (drained into the body's energy/fatigue), narration, and per-ground footsteps (registered sounds,
  active only in transit).
☑ Census tuples carry standpoint + in_transit (via read-pure peek()); fragment_context gains the
  standpoint column; the pulse shows position. (HUD card extra was marked optional in §4; the pulse
  line covers it.)
☑ Watchdog + persistence proven by kill-mid-journey test (temp-pathed, 8 test groups, all passed
  2026-08-15).
☑ The word "teleport" is true nowhere in the world (gathered wood included — it rides his journeys
  now). The LOCOMOTION=False rollback is the sole, documented instant path.
**DONE — built and verified in one wave, 2026-08-15. No partial-credit state was used.**

## 7. Pre-registered watch items (post-restart, founder-read)

1. Wood presence rises from ~0 to ~8–12 transits/day (the drive-through effect) — census `at_wood`.
2. Shore-share moves (either direction is information: cost may reduce visits but lengthen stays).
3. First transit-laid memory (a thought with wood context mid-journey in `fragment_context`).
4. Standpoint variety in tuples (does he live at 3 standpoints or 24?).
5. Zero stuck-journey log lines.
6. His OWN language: does "the path", "the walk down", "on the way" enter his idle vocabulary
   unprompted? That is the sense of embodiment showing up from inside.
