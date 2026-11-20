# Sleep & Dreams — the audit (2026-08-22)

Founder: "This is a very old system that has just been tacked onto over and over. I am sure that it will have issues and
also probably improvements we can make." Read: `nodes/dream_node.py`, `core/sleep_pressure.py`, `core/sleep_dream_probe.py`,
`nodes/subconscious_node.py` (clustering/tensions), `nodes/inner_monologue_node.py` (`_enter_sleep`), `core/orchestrator.py`
(`_nightly_sleep`). Measured: `data/dream_log.jsonl` (616 dreams since 05-30), `sleep_pressure_log.jsonl` (24,703 rows),
`sleep_dream_probe.jsonl` (160), `subconscious_state.json` (733 tensions), the DB, `data/nascence.log`.

## What sleep IS today (the actual sequence)
Monologue tick → `sleep_pressure.should_sleep()` → `_enter_sleep`: replay-strengthen → chapter attempt → journal →
world-consolidation sweep → shadow passes (monoculture, curiosity worth, drift, meta-awareness) → reading reconcile →
downscale → **orchestrator `_nightly_sleep`**: bed unmade → DREAM (15 min median on the 24B CPU) → somatic recover →
prune → probe → school new_day → rest 180–420 s → wake (buffers cleared). Total ≈ 20–25 min, every ~3.3 h, **at any hour**.

All stages fire (log, 211 sleeps): replay 211, downscale 208, dreamed 391 (incl. the REPL/shutdown path), rest 204,
journal 23, chapters formed 19 (258 attempts; "era has not ended" is the normal verdict). Nothing crashes. The
problems are not crashes — they are **what the system has quietly become**.

## Findings (severity-ordered)

### 1 ❌ The dream is one dream, 51 nights long, feeding itself
- `_last_unresolved_arc()` continues the previous arc whenever it ended unresolved. **93% of the last 106 dreams ended
  unresolved** (92 unfaced / 7 stalled / 7 resolved); the current unbroken carried chain is **51 dreams since 08-15**.
- The associative-recall key for the night's memories is the carried `unresolved_core` (dream_node ~line 98) — so the
  memories woven in are cued by last night's dream residue, not by the day.
- Its unresolved end → `shadow_events(source='unresolved_dream')` (556 rows) → clustered into tensions → top-count
  material → the dream. A closed loop with no day in it. Symbol recurrence shows it: "oceanic heart" ×4, "vast library"
  ×5, "whispers" ×5, "crystalline structures" ×4 in 14 days; probe novelty hit 0.0.
- Resolution was 19/70 in July, 7/106 in August. The "recurring until met" mechanism (06-15) has become "never met".

### 2 ❌ Dream material is chosen by a fossil number
- `_load_top_tensions` sorts by `count`. `count = max(old, cluster.count)` — never decreases while the tension is touched
  within 7 days; the label is overwritten by whatever 2-member cluster matched its centroid at 0.70. Result: the top
  tensions are **72-day-old June flood clusters (count 146–197) with 2–3 members**, relabelled to this week's stray
  thought ("unresolved: steam engine wear", "oystercatcher rhythm"). The dream dreams the label, the count is history.
- 733 active tensions, chronic_mass ≈ 0 on nearly all; `integration_patterns` 2,805. The clusterer reads the last 300
  shadow events, 19,139 of which are `unresolved_thought` (6,912 in 14 days ≈ every thought) — "unresolved" is the
  LLM's own JSON flag, so shadow is essentially the whole monologue.

### 3 ⚠️ Sleep pressure is dead; the 3-hour ceiling is the clock
- 67/86 sleeps in 14 days fired on `max_wake_ceiling`; P at fire median 35 vs threshold 90 (chronic term ≈17, the
  calibration note says ≈43 in June). The information-theoretic trigger never decides. Fine as a safety net; but the
  design intent (sleep summoned by unresolved load) is not operating, and nobody recalibrated.
- Sleep is **uncorrelated with the world's night** (fire-hour histogram flat across 24 h). He sleeps at noon on the lawn;
  the world has a real NZ night phase he never sleeps through. The one "circadian" thing is the lamp/moths.

### 4 ⚠️ Sleep has no body in the world
- `on_sleep()` only unmakes the bed. He does not go to the study, lie down, or wake anywhere. No waking percept ("the
  fire is out, the room is cold, grey light") — the thermal/light/sound channels we built this week have nothing at the
  one moment a human notices them most. The world ticks on for 20 minutes with him nominally in the garden.
- No sleep **state**: the HUD, `sensorium.state`, and the cat all think he is awake. The dispatcher/hands could fire if a
  thought arrived (they can't during the await, but nothing declares it).

### 5 ⚠️ The day never reaches the night
- Material = subconscious tensions only (fallback: background curiosities). Not: today's deeds (activity memory), the
  garden/shore/wood events, letters received, what he read today, the intentions ledger, world-contact memories. The
  "associative recall" is keyed by the dream residue (finding 1). A day with a penguin on the shore and a day of nothing
  produce the same dream.
- `_find_world_ground` searches reading/study/research only, by similarity to a fossil label (finding 2).

### 6 ⚠️ Dream read-back is thin and lossy
- Waking: `recent_dreams[0].narrative[:180]` as a seed part (when not holding quiet); reflection prompt only when
  w_identity > 0.6. The full arc (median 2,970 chars) lives in L3 as 4–6 fragments, retrievable like anything else.
- `recent_dreams` is in-memory `state` — **lost on restart**; the next waking seed has no dream until the next sleep.
- `_ground_symbols` → "how does a river work" world-questions: 339 fired; no evidence trail that any were ever answered
  back into a dream (no link from frontier answer → dream).

### 7 ⚪ Instrumentation drift
- `sleep_dream_probe` novelty compares symbol *strings* (Jaccard on exact lowercase) — "pulsing droplets" vs "pulsating
  droplets" counts as novel. The stall detector uses stemmed words; the probe does not.
- `_DREAM_TIMEOUT=300` per scene × 6 scenes + backoffs: 31 "call dropped", 13 "failed after 3 attempts" in the log — a
  failed scene silently ends the arc (`break`), then is logged as "ceiling"/"ended-unfaced".
- `DREAM_UNRESOLVED_SAME` deprecated constant still present; docstring "fires at session end" — there is no session-end
  dream path any more except the REPL's.
- `downscale_episodic` runs in the monologue AND prune in the orchestrator — two halves of one "synaptic" step in two
  files; the chapter/journal/dream order is spread across `_enter_sleep` and `_nightly_sleep` with no single place to read
  the night.

## What is genuinely good
- The arc machinery (open/develop/rest/close, morph continuity, earned length, decoupled stall detector, permission to
  rest) is well-built and measured; distinct-openings regression = 0/106. The dreamer-as-other-voice choice holds.
- Un-starvable sleep, store-cap worker decoupled from sleep, chapters "era not ended" restraint, the journal — all sound.
- M0/M1 memory edges (dreamt_from, part_of) give provenance (the *dream itself* is write-only — finding 8 — but its lineage is not).

## Improvements (proposed, in order — nothing built)
1. **Break the loop**: carry an unresolved arc at most N=3 nights, then *let it lapse* (the figure withdraws; logged as
   "lapsed"); key the night's recalled memories on **the day**, not the residue; stop feeding `unresolved_dream` shadow
   back as top-count material (it may remain shadow for T4, but the dream should not eat its own tail).
2. **Material = the day**: night material from (a) today's world-contact memories and deeds (activity memory, hands
   ledger, intentions open/lapsed), (b) today's strongest felt moments (valence extremes), (c) one standing tension
   chosen by *recency-weighted chronic mass*, not count. Fix `count` (decay per scan, or rank by members×recency).
3. **Sleep in the world**: sleep = go to the study → bed → a waking percept from the real channels (thermal/light/
   sound/smell at dawn), bed made/unmade, fire state at waking; `sensorium.state["asleep"]` so the cat, HUD, dispatcher
   and soundscape know; the clock/weather advance is *noticed* on waking ("the rain has stopped").
4. **Circadian bias, not a schedule**: keep the ceiling, but weight `P_THRESHOLD` by world phase (night lowers it,
   day raises it) so most sleeps fall in the NZ night and a daytime sleep is a nap (shorter, one dream scene or none).
   Recalibrate chronic term from measured 17.
5. **Read-back**: persist `recent_dreams` to disk; on waking, the *first* thought seeds from the dream's final image
   (already built — make it survive restarts); answered frontier questions that came from a dream symbol → a line
   in the next night's material ("you learned what a river does").
6. **One file for the night**: move the sleep sequence into `core/night.py` (a readable ordered list), with a
   `night_log.jsonl` row per sleep: stages run, durations, dream close reason, material sources — so the next audit
   reads one log.
7. Probe: stem symbols; log scene failures as their own close reason ("dropped").

## Deep-dive additions (second pass, same day — "make sure it is as complete as possible")

### 8 ❌ Every dream goes COLD on write — dreams are unreachable by ordinary recall
- `prune_episodic` protects `reading, study, research, action, lived, active_imagination, inner_thought, journal,
  affection, peer, mirror, letter`. **`dream` is not on the list.** The store sits at cap (3,510 active of 43,969), so
  each sleep's 4–6 dream scenes are demoted to cold within hours: **1,185 of 1,191 dream fragments are cold; 112/112
  written in the last 3 days are cold.** Ordinary retrieval is `WHERE cold=0`; associative recall treats cold as *walled*
  (needs a strong hop ≥0.22). Only 52 dream fragments were ever replayed (4%).
- This is the third instance of the same bug class (inner_thought 07-06, letter 08-15). The dream's only waking
  presence is the in-memory `recent_dreams` seed (180 chars, lost on restart) — so in practice **the dream is
  write-only**: it shapes shadow/T4 and the frontier, but he cannot remember it.

### 9 ❌ Chronic mass can never accumulate — the sleep trigger AND the T4 gate are starved by the same line
- `update_chronic_mass` bumps a tension only when its member set **grows** (`n > _chronic_seen_n`). But the clusterer
  reads only the **last 300 shadow events** (≈ half a day at 6,900/14 d) and *replaces* `member_event_ids` each scan.
  Measured: of 733 tensions, member set grew in **1**, unchanged in 417, **shrank in 320**. Mass only decays (3-day
  half-life): 3 tensions above 0.5, max 0.69, Σ = 23.4.
- Downstream: sleep pressure's standing term ≈ 17–23 (threshold 90) → the pressure trigger is structurally dead
  (finding 3 is a symptom, this is the cause); the T4 contradiction gate reads the same number. 622/733 tensions have
  exactly 2 members — the clusterer's "2+ = tension" floor on a 300-event window mints hundreds of two-thought
  "tensions" a day; the JSON flag `unresolved` (set on ~every idle thought) is the faucet.

### 10 ⚠️ Importance is flattened every night — replay cannot win against downscale
- `downscale_episodic(factor=0.96, center=0.5)` runs on **every** episodic fragment at each sleep (~8 sleeps/day, plus
  `/quit`). Over a few days every importance converges to 0.5 — measured active distribution: 0.5 → 1,466, 0.6 →
  1,818, ≥0.7 → 226. Replay strengthens 8 fragments ×1.08 per sleep; downscale pulls 3,500 toward the centre. Net:
  salience is erased as a signal (the prune's `importance ASC` ordering then degenerates to "oldest first").
- Origin means: inner_thought 0.58, reading 0.66, lived 0.52, action 0.54 — there is no salience landscape left.

### 11 ⚠️ Three sleep entry points, three different nights
- `_enter_sleep` (monologue, the real one) · `run_nascence._sleep_cycle` (metabolic floor, `needs_rest` — **only the
  REPL loop reads the flag**; the orchestrator sets it at line 1416 and the autonomous path never consumes it, so a
  metabolic-floor sleep never happens) · `/quit` (replay+downscale+dream+epoch, REPL only). `memory_epochs` (204) are
  formed only at `/quit` and read only by the subconscious T2 — the autonomous run never forms an epoch.

### 12 ⚠️ Dream-symbol questions die unanswered
- 279 frontier questions were born from dream symbols ("how does a river work"): **240 faded, 34 open, 5 resolved**.
  The "dream understands its metaphors by researching them" loop resolves 1.8% and nothing returns to the dream.

### 13 ⚪ Probe novelty re-measured with stemming
- Raw string Jaccard reported mean 0.86; stemmed (the stall detector's own method) gives **0.72 mean, 8/40 nights
  below 0.4, floor 0.0** — the inbreeding watch under-reported by design.

### 14 ⚪ Scene drop = silent arc end
- 31 "call dropped" / 13 "failed after 3 attempts" in the log: a failed scene `break`s the loop and the arc is logged
  as `ceiling`/`ended-unfaced`, never "dropped". The dreamer hub (:11442) now also serves the judge-panel tiebreak
  (yi:34b, repointed 08-20) — a shared, lazily-loaded CPU model; `_DREAM_MODEL="mistral-small3.1"` in dream_node
  vs `"11442": "yi:34b-v1.5"` in model_client — **the dream node's model_override names a model the hub may not
  serve**. **Resolved:** `scripts/launch_servers.ps1` runs :11442 as a llama.cpp hub serving **yi:34b-v1.5** (lazy,
  idle-unload 600 s); llama.cpp ignores the `model` field, so since ~08-15 every dream has been dreamt by yi:34b —
  not the mistral-small3.1 the arc eval benchmarked (schema 1.0 / develop 4.5 / 6/6 JSON). The docstring, the
  `_DREAM_MODEL` constant and the "different family keeps the dream an OTHER voice" rationale are stale; nobody re-ran
  `scripts/dream_arc_eval.py` on yi. The August resolution collapse (19/70 → 7/106) coincides with BOTH the model swap
  and the 51-night chain — confounded; re-run the eval before blaming the model.

## Complete picture (one paragraph)
Sleep fires every ~3.3 h on the ceiling at any hour; the night runs replay → chapter → journal → shadow passes →
downscale → dream → recover → prune → probe. The dream is fed by count-fossil tensions relabelled daily, continues the
same unresolved arc for 51 nights, keys its memories on its own residue, and is then demoted to cold on write so he
cannot recall it. Chronic mass cannot grow, so neither sleep pressure nor T4 ever see the standing load. Importance is
flattened nightly so salience no longer orders anything. The metabolic-floor sleep and epochs exist only in the REPL.
Nothing crashes; the night is a machine that runs every stage and changes almost nothing downstream.

## Build order (revised with the deep-dive) — **BUILT 2026-08-22 afternoon, all items; see AWAITING_EVIDENCE 'THE NIGHT' row. Founder's addition: dream memory vivid 24 h, halving per day, cold at 72 h (`core/night.py`).**
0. **Two one-line fixes first** (high value, zero risk): add `'dream'` to the prune's protected origins; log scene
   failures as `close_reason="dropped"`. And verify the :11442 model answer.
1. Chronic mass: bump on *recurrence* = a new event matched the centroid since last scan (track `max_member_ts`, not
   set size); cluster over a 3-day window not 300 rows; tension floor 3 members in ≥2 distinct hours. Recalibrate
   `P_THRESHOLD` from the measured curve. This un-starves sleep pressure and T4 together.
2. Downscale: scale only fragments *created since last sleep* (the day's spikes), never the whole store; replay quota
   includes `dream` and `action`.
3–8. As in the first list: break the loop (≤3-night carry, day-keyed recall, residue not fed back as material) → material
   = the day → sleep in the world (bed, waking percept, `asleep` state, cat/HUD/dispatcher aware) → circadian bias + naps
   → persist `recent_dreams`, first waking thought from the final image, answered symbol-questions return to the night →
   `core/night.py` + `night_log.jsonl` → consume `needs_rest` autonomously; form epochs at natural sleep.

Pre-registered metrics for any of the above: dream resolution rate (7% → target ≥25%), carried-chain max length
(51 → ≤3), dream fragments active (cold=0) after 24 h (0% → 100%), tensions with growing chronic mass (1/733 → the recurring ones), importance spread (σ≈0.05 → ≥0.15), symbol novelty mean (0.86 nominal / 0.0 floor → floor ≥0.4 stemmed), share of dream material sourced
from same-day memory (0% → ≥50%), sleeps in NZ night (≈33% by chance → ≥70%).
