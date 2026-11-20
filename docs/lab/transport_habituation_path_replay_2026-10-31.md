# Transport habituation: non-ergodic path replay (J-2624, 2026-10-31)

Plan: dosed_coupling. From F-3355 / J-2521. Script: `scripts/shadow_path_replay_transport.py` (method, weeks, rules
declared in its header before the first run). Result files: `docs/lab/transport_path_replay_2026-10-31/`
(`J-2624_primary.json` = verdict run, `J-2624_primary_anchorfirst.json` = post-hoc start sensitivity,
`J-2624_replicate.json`, `survey_J-2624.py` = the era survey below).

## Question

The J-0603 shadow logs a would_winner whose b grows on the REAL winner. Read per tick (an ensemble read) it said the
discount displaces the stale winner almost always (differs 285/292 on 2026-09-05, 935/940 on 09-06). If the discount
were ADOPTED, b grows on the discounted policy's OWN winner. Dispatch is argmax over ~124-147 candidates. Does the
adopted path (D) differ from the real policy (C) and from what the logged would-policy (W) predicts?

## Method (short; the script header is the full declaration)

- Pool and raw weights held fixed per tick. Check from the log: the winner's raw_weight drops on the next tick in
  15 of 5,543 consecutive pairs (primary) and 2 of 5,243 (replicate). So a win does not reset raw weight; the rare
  drops are fresh observe() events. Novelty consumption is modelled per path. No real tick was won by a novelty, so
  nothing needed restoring.
- C = argmax dispatch. D = module discount with b grown on D's own winner, through
  `core.transport_habituation.observe_and_log` itself (redirected to memory). b starts at 0 at each start tick.
  W = the logged would_winner.
- Both picks are deterministic argmax, so there are no RNG runs. Instead there are 12 start ticks, 2 h apart.
- Primary week 2026-09-05..09-11 (5,545 ticks, level-trigger era, clock_tick:study monoculture). The verdict is read
  on days 2..7. Replicate week 2026-09-16..09-23 (5,244 ticks, life:cat:study / wood_pigeon monoculture).

## Machinery checks (all pass)

| check | primary | replicate |
|---|---|---|
| E1 re-implemented pick vs REAL `transport_manager.dispatch_tick()` (synthetic state, C and D pools) | 11,090 / 11,090 | 10,488 / 10,488 |
| E2 D pick vs `observe_and_log`'s own would pick, all starts | 66,059 / 66,059 | 60,614 / 60,614 |
| E3 logged policy rebuilt from real winners: would identical / b max abs dev | 5,482 / 5,545, 1e-4 | 5,244 / 5,244, 1e-4 |
| E4 C reproduces logged real_winner, all starts | 66,059 / 66,059 | 60,614 / 60,614 |

Limit: the log's `weights` dict is keyed by line_id. Every tick, 1-14 candidates are collapsed: a line holding
novelty plus drought, or spike plus drought, keeps only its last candidate. C is unaffected (E4 100%). The 63
primary E3 misses (1.1%) are the upper bound of what the collapse can change in a discounted pick.

## Result

Both declared rule sets fire: **A (D vs C) DIVERGE** and **B (D vs W) DIVERGE**.

- Primary A: R2 6/6 days, R1 2/6, R3 2/6.
- Primary B: R1 5/6, R2 6/6, R3 5/6.
- Replicate A: R1 2, R2 6, R3 3. Replicate B: R1 5, R2 6, R3 3.

Primary week, per day (D = min/median/max over starts):

| day | C modal, share, changes | W (ensemble) modal, share | D modal, share, changes |
|---|---|---|---|
| 09-06 | clock_tick 1.00, 0 | blackbird_song 0.55 | clock_tick 0.73, 505-513 |
| 09-07 | clock_tick 1.00, 0 | bees_in_garden 0.57 | clock_tick 0.93, 132 |
| 09-08 | clock_tick 1.00, 0 | small_birds 0.46 | clock_tick 0.92, 90 |
| 09-09 | clock_tick 1.00, 0 | clock_tick 0.69 | clock_tick 0.97, 46 |
| 09-10 | moth_tap 0.47, 5 | clock_tick 0.39 | None (no dispatch) 0.60, 26 |
| 09-11 | penguin_bray 0.40, 4 | wind_in_trees 0.42 | None 0.93, 131 |

Over the whole primary week, start 0: D gives clock_tick 3,314 / 5,545 ticks (60%) and None 1,906 (34%), and never
picks a novelty.

The divergence runs the OPPOSITE way to the compounding hypothesis. Adopted, the discount does not displace the
monoculture. The ensemble read (W) says it does: on 3 of the 4 clock_tick days it puts a runner-up on top. In W the
real line keeps winning, so its b re-grows to the 0.95 ceiling every tick.

In D the discount is self-limiting. Once clock_tick (raw ~19) stops winning, its b decays (tau 2 h) below about 0.92
within ~230 s, which is 2-3 ticks. Then raw * (1 - b) clears 1.5 again. The adopted policy flickers: clock_tick, a
short runner-up or None, then clock_tick. That gives 46-513 winner changes a day against 0, the same modal line on
4/4 clock_tick days, and longest runs of 36-381 ticks against 543-940.

On lower-weight days, the discounted line sits in [1.0, 1.5), above every novelty at 1.0 but under the threshold, so
dispatch goes silent (None 60-93%).

Agreement with D by horizon (primary, pooled over starts):

| horizon (ticks) | C vs D | W vs D |
|---|---|---|
| [0,10) | 0.58 | 0.52 |
| [10,30) | 0.38 | 0.05 |
| [300,1000) | 0.70 | 0.04 |
| [1000,inf) | 0.60 | 0.34 |

Start sensitivity: the paths converge to one attractor. On days 3..7, D's metrics are identical or within ±2 changes
across all starts. Only 09-06 (day 2) varies: 88-513 changes in the post-hoc 12-distinct-start run. The declared
start rule collapsed 8 of 12 starts onto tick 0 because the log begins ~14 h after midnight. The post-hoc run
(anchor = first row) gives the same verdicts.

## Not replayed

From 2026-09-24 on, the candidate pool collapses to 1-40 per tick, and real dispatch fires on 0-3% of ticks from
09-29 (survey). Under EDGE_TRIGGER (D-0294) a win also disarms the winner, so the pool is path-dependent and cannot be
held fixed. The current regime is therefore not covered by this result.

## Isolation

- core was imported from the worktree (asserted).
- lab_env isolate(db=empty) ran with its lab root patched to the scratchpad. tm/thab state and log globals were
  redirected, and every writer was stubbed.
- Live data/ top-level canary (434 files, size+mtime): only hud.err.log and supervisor.log changed (HUD and
  supervisor processes, not this job).
- No LLM was used.
