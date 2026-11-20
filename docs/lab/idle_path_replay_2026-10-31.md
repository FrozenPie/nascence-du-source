# idle_allocator: is there a would-choose path, and does it compound? (J-2625, 2026-10-31)

Plan: dosed_coupling. From F-3355 (J-2521 curiosity_habituation null) and F-3386 (J-2624 transport_habituation
path replay). Read-only on every live store, zero LLM, core imported from the job worktree inside
`lab_env.isolate` with the lab root under the scratchpad.

## 1. First question: is there a path channel at all?

Read from `core/idle_allocator.py` and the whole `data/logs/idle_shadow.jsonl` (72,558 rows, 2026-06-16 .. 2026-10-30,
streamed by `docs/lab/idle_path_replay_2026-10-31/survey_J-2625.py`; full output in `survey_J-2625_output.txt`).

| Question | Answer | Where |
|---|---|---|
| Does any state depend on the allocator's own pick? | Yes, exactly one thing: `streak`. The argmax winner's streak +1, every other channel 0; `s_final = p_norm * W * (1 - 0.15 * streak)`. | lines 407-411, 343 |
| Does `history` (the percentile base) depend on the pick? | No. Every candidate's raw is appended every tick. With inputs fixed, p_norm is path-independent. | lines 402-406 |
| Is the real idle action in the log? | No. `actual` is null in 72,558 / 72,558 rows; the only caller never passes it. The briefing's "real action path" control does not exist. | survey K4; `nodes/inner_monologue_node.py` ~2694 |
| Is the logged argmax already the self-fed path? | Yes. The streak recurrence on the logged argmax holds on 486,241 / 486,241 candidate checks across every consecutive row pair, gaps and restarts included; `s_final` recomputes on every row; argmax = first max `s_final` on every row (266 ties). | survey K1, K2, K3 |
| How far back does the path reach? | 1-2 ticks. The longest logged argmax run is 1-2 ticks on every one of the 91 logged days, and the max streak is 2. One win costs 15%, which nearly always hands the slot to the runner-up. | survey per-day lines |

So **the argmax read cannot hide a path effect**. It is already the closed-loop path, and replaying it forward only
reproduces the log (E1 below).

**But Phase 1 is meant to adopt softmax, not argmax.** `docs/shelf/idle_executive_plan.md` (lines 197-198, 252-254)
rules a softmax gateway at tau 0.35, "never a pure argmax". The logged `would_pick_softmax` is drawn on a streak grown
from the argmax pick. If softmax were adopted, the streak would grow from the softmax pick instead. That is the one
would-choose path the ensemble read could hide, so it is the one replayed here. This is the same shape as J-2624's
transport case, where the logged "would" grew its state on a different winner than the adopted policy would.

Side note (not used by the replay): rebuilding p_norm from a 500-deep history made of the log's own raws matches on
387,046 / 428,604 non-bypassed checks (90.3%). The rest probably come from the state's history not matching what the
log shows: the J-1921 balance-history drop, rows from before the log began, and any tick whose log write failed. The
replay holds p_norm at the logged value, so this does not affect it.

## 2. Replay (declared before results; header of `scripts/shadow_path_replay_idle.py`)

- Every tick runs through `core.idle_allocator.shadow_tick` itself, with these patches:
  - `_CHANNELS` returns the recorded (raw, key, kind) tuples.
  - `_percentile` returns the logged p_norm (the concern bypass is off for the replay, so concern goes through the same hook).
  - State is held in memory and `_LOG` points to os.devnull.
- **AL** is the module as-is, run with argmax. **SL** is the module as-is, reading the softmax pick (the logged policy), seeds 0..19.
- **SA** is softmax ADOPTED. It is the same as SL, except the streak is re-accounted on the softmax pick after each tick, using the same 4-line accounting.
- SA and SL use the same seeds, so their random draws pair up tick for tick. The only difference between them is the feedback.
- Weeks: primary 2026-10-10..16 (verdict) and replicate 2026-09-05..11. Verdict days are all 7, and a rule needs ≥ 4 days.
- Rule set A compares SA with SL; rule set B compares SA with the logged softmax.
  - A1: the modal channel differs.
  - A2: modal share differs by ≥ 0.10.
  - A3: distinct channels differ by ≥ 2.
  - A4: the longest run differs by ≥ 3.
- Any rule meeting the day threshold means DIVERGE. The pre-registered falsifier is that the paths converge.

## 3. Results

| | primary 10-10..16 (10,202 ticks) | replicate 09-05..11 (7,733 ticks) |
|---|---|---|
| E1: the module's argmax replay vs the log (pick, streak, s_final) | 10,202 / 10,202 | 7,733 / 7,733 |
| A: SA vs SL | **CONVERGE** (A1 0, A2 0, A3 0, A4 0 days) | CONVERGE (A1 2, others 0) |
| B: SA vs logged softmax | **CONVERGE** (A4 1, others 0) | CONVERGE (A1 3, others 0) |
| Sanity: SL vs logged softmax | CONVERGE (0 / 0 / 0 / 0) | CONVERGE (A1 1) |
| Paired same pick SA = SL | 0.876 | 0.880 |
| Per-day TVD between SA and SL pick distributions | 0.011 - 0.023 | 0.011 - 0.022 |
| Median longest run, SA vs SL | 4 vs 5-6 | 4-4.5 vs 5-7 |
| Change share (G3 "rotates"), SA vs SL vs logged argmax | 0.84-0.85 vs 0.79-0.81 vs 0.97-1.00 | 0.81-0.86 vs 0.76-0.82 |
| Pooled self share (G2 gate < 0.35), SA / SL / logged softmax | 0.130 / 0.137 / 0.132 | 0.149 / 0.156 / 0.160 |
| SA max streak reached (20 seeds) | 4-6 | 4-8 |

The replicate's A1 hits all fall on days where the seeds split their vote between two channels, such as concern 11 vs
curiosity 9 on 09-07, or balance_world 15 vs concern 5 on 09-08. Those are near-ties in plurality, not displacements.

## 4. Reading

- **There is no hidden path effect.** Adopting the softmax gateway would put the streak on the sampled channel, and that
  moves the daily pick distribution by at most 2.3% TVD.
- The adopted path is slightly **more** rotating than the logged softmax read, not less. Its longest runs are about 2
  ticks shorter and its change share is about 0.04 higher.
- The direction is self-limiting, the same as F-3386. Habituation lands on whatever was just picked, so a lucky repeat
  is punished rather than compounded.
- With a memory of 1-2 ticks and a 15% step, this channel cannot build up a monoculture. It is the opposite of the
  transport case, where a 2 h decay let the state build a long attractor.
- The logged softmax read is therefore a faithful predictor of the adopted gateway's day-level behaviour, and the G2/G3
  numbers in the idle_executive plan carry over.

**Scope.**
- Channel inputs are held fixed. If adopted, the allocator would change what Du does and therefore its own future
  inputs (contradiction mass, curiosity LP, boredom streak). That loop is outside the shadow and cannot be replayed from
  this log.
- The concern-bypass era and the current percentile switches are those in force during the replayed weeks. The p_norm
  values are as logged.

Artifacts: `scripts/shadow_path_replay_idle.py`; `docs/lab/idle_path_replay_2026-10-31/` (survey script and its output,
`J-2625_primary.json`, `J-2625_replicate.json`). Each replay took 175 s and 165 s for 41 paths.
Isolation: core was imported from the worktree (asserted), and `lab_env.isolate(db="empty")` ran with the lab root
under the scratchpad. A canary of `C:\Nascence\data` (4,011 files to depth 2, size and mtime) was taken before and
after. Three things changed during the window: `hud.err.log` grew (the HUD process), and `memory/nascence.db-shm` and
`memory/nascence.db-wal` were removed, which SQLite does when another process's last connection closes. This process
cannot write there: its `_DATA` resolves to the worktree, and its DB is redirected by lab_env.
