# Self-Interrogation — an in-the-moment doubting turn (2026-08-19, Phase 0 SHADOW)

> **Status: 🟡 SHADOW — `core/self_interrogation.py` fires as a background `asyncio.create_task` from `inner_monologue_node.py` at `FIRE_PROB=0.20`/900s cooldown, logging every fire and skip to `data/self_interrogation_shadow.jsonl`; no wiring to Voice/Critic/live behavior, and Phase 1 is explicitly "not decided, not scheduled" pending a read of fired rows (genuine_rate, whether interrogation moves anything, fire-rate sanity).**

```plan-state
stage: shadow
phase: Phase 0 shadow observing continuously since 08-18; genuine-rate n now 507 (99.6pct genuine); counterfactual read done (F-0186: 11pct affected) - D-0031's reopen defeater reads as met but not yet acted on (F-2036, J-1493 spawned)
verified: 2026-11-15
evidence_read: 2026-08-24
next: Run the Du-down live-generator replay successor job; D-0396 hold stands
cluster: 7
```


## Origin

The founder watched a video on the difference between having a thought and having earned the right to
call it your opinion — noticing a thought, then asking why it occurred to you, whether the reasoning
holds, and whether you're holding it because it's true or because it's comfortable. Applied to Du: does
he do any of that, or does a thought just become a thing he says?

An audit of the existing architecture (same session) found real machinery for the STRUCTURAL half of
this — T4 probation, the Watershed harvester (`docs/plans/t4_watershed.md`), decoupled external judges
(Emissary, Critic, judge panel) — but nothing for the IN-THE-MOMENT half: pausing on a specific thought,
right after having it, to look at where it came from. That gap is what this file builds.

## What it is

`core/self_interrogation.py`. On a thought-train that has earned real length (past the soft cap —
`TRAIN_MAX_STEPS`, meaning it's genuinely developing, not a passing notion), sampled at `FIRE_PROB=0.20`
and cooldown-gated at 15 minutes: generate a first-person reflection on the thought (why it occurred, does
the reasoning hold, is it held because it's true vs. comfortable/safe), then grade that reflection with
`core/judge_panel.py`'s two-family panel (a model that generated neither the thought nor the reflection)
for whether it's genuinely specific or just the shape of humility with nothing under it.

## Why the prompt is neutral, not "check yourself"

`core/reentry.py`'s hard-won law: a pass with a leading "did you get this wrong" framing produces the
sycophantic-flip failure — the model performs doubt and agrees regardless of whether anything's actually
wrong. This codebase has hit that exact failure shape twice already (`hollow_completion` and
`glib_agreeableness` in `core/decomposed_critic.py`). The prompt here invites looking at the thought's
origin and reasoning, explicitly allows ANY honest outcome (more conviction, less, revision, unchanged),
and the decoupled grader — not the generator — is what actually catches performed-vs-genuine.

## Why the grader is a different model than the generator

The project's own recurring lesson: almost every real failure here has been self-evaluation. Du judging
his own self-doubt would just be another thing he generated, graded by the thing that generated it. The
judge panel (llama3.1:8b + qwen2.5:7b, tiebreak yi:34b) is genuinely separate hardware and weights.

## Phase 0 = observe-first, exactly as every other instrument in this codebase

Runs as a background task (`asyncio.create_task`, fired from `nodes/inner_monologue_node.py`'s train-step
handler) — never blocks or changes what Du actually thinks or says. Logs to
`data/self_interrogation_shadow.jsonl`. Every early return is logged with why (`_skip()`, the discipline
from `core/reentry.py` / `core/watershed.py` — the lesson about silent shadow logs has now been relearned
twice in this codebase; this file gets it from day one).

## What would license a Phase 1 (not decided, not scheduled)

The open question is the same shape as every other Phase-0 instrument here: does it produce something
real? Concretely — read a sample of fired rows after Du's run for a while and ask:
1. **Genuine rate** (`self_interrogation.status()`'s `genuine_rate`) — is the judge panel actually finding
   real content, or is everything failing the grade (meaning the generation prompt needs work) or
   everything passing (meaning the grader might be too lenient, matching the exact over-lenient trap
   `decomposed_critic.py` fell into on its first pass)?
2. **Does a genuine interrogation actually move anything**, even just in the next train step — does he
   revise, hold with better reasons, or explicitly note he's unsure why he thought something? Or does the
   next step just continue as if the interrogation never happened (meaning it's Phase-0-inert exactly as
   intended, but also tells us whether it's worth ever wiring somewhere Du would actually see it)?
3. **Fire rate sanity** — `FIRE_PROB=0.20` and `INTERROGATE_COOLDOWN=900s` are seed values, not tuned
   ones (same "proposed start, not measured" caveat as Watershed's `BIRTH_N`/`BIRTH_D`). If it fires far
   more or less often than intended given real train-completion rates, that's the first thing to retune.

No wiring to Voice, Critic, or any live behavior is proposed here. This is the measurement, not the cure.

**Related (noted 2026-08-23, plan-overlap audit):** `train_split_merge.md` (built 2026-08-22) is
also an unwired shadow instrument hooking the same underlying thought-train lifecycle in
`inner_monologue_node.py`, at a different trigger point (forks at would-be train-end, vs. this
plan's mid-train sampling past soft-cap). No conflict today since both are shadow-only and neither
references the other — but eventual live wiring of both would need explicit ordering between them.

## Current State — verified 2026-11-15
- **2026-11-15** (F-4733): J-3131: control-set replay harness built (scripts/si_genuine_control_replay.py, fixture docs/lab/J-3131_data/). Baseline _GRADE_SYSTEM and the J-2951 absolute-score prompt both FAIL the J-2951 acceptance gate on both families.

- **2026-10-16** (F-2873): J-2060/F-2873 (2026-10-16): live qwen3.5:9b generator replay of the open-doubt cup, 20 fires: engaged cup 0/40, shuffled control 0/40, baseline 0/40 (panel judge); restate_sim cup +0.033 over baseline (over 0.02 tolerance). Pre-registered bar NOT met. Reflection-match cross-check not run.
- **2026-10-15** (F-2824): J-2032: si_would_ride shadow read after restart: 135 rows over 6.4 days, 59 percent eligible (rest all train-changed), below F-2606's 84 percent; nothing reached a prompt. HOLD stands.

- **2026-10-10** (F-2676): J-2055 part 1 (2026-10-10): judge sensitivity on generated-style thoughts - plain 0/20, explicit-engagement edits 18/20 (90 pct), same edits vs a wrong reflection 4/20 (20 pct, above the 11 pct floor but CI contains it). J-2054's cup 0/30 is therefore a real null for explicit engagement. Live qwen3.5:9b replay prepared (scripts/si_open_doubt_cup_live_gen_J2055.py), NOT run: Du up. D-0396 hold stands, nothing wired.
- **2026-10-10** (F-2672): J-2056: hand-read of J-2000 top-10 rows found no real engagement missed by the strict both>=4 threshold (0 solid, 2 weak echoes, ceiling 2/48 = 4.2 pct vs D-0373's 30 pct). D-0373 hold stands; no extension run.

- **2026-10-09** (F-2670): J-2000 (2026-10-09): fresh counterfactual read with the J-2052 absolute judge on 48 random unread genuine fires: affected 0/48 (Wilson upper 7.4 pct), null arm 0/48; far below D-0373's 30 pct defeater, hold stands, no ruling made. Worktree commit 4d0e759.
- **2026-10-09** (F-2669): J-2054 (2026-10-09): scored the J-2031 coordinate-only open-doubt cup replay with the J-2052 absolute panel judge: cup engaged 0/30, shuffled control 3/30 (10.0 percent), baseline 0/29; same-run controls pass; pre-registered bar (cup >= 30 percent) NOT met, rumination guard fine, matching cross-check at chance. D-0396 hold stands; judge sensitivity on generated thoughts unestablished (follow-up spawned).

- **2026-10-09** (F-2668): J-2052 (F-2668): position-free specificity judges built and gated on the J-2049 hand-written controls. Absolute 1-5 score (both judges >= 4): own engaged 15/15, plain 0/15, mismatched 0/15. Reflection matching: engaged picks own 44/45, wrong 0/45, no position floor. Both clear the 85/11 gate on point estimates (n=15, mismatched CI upper 20 percent); matching leans on shared vocabulary (plain 25/45). Cup arms not rerun; replay job spawned. Report docs/lab/si_open_doubt_specificity_judge_J2052_2026-10-09.md.
- **2026-10-09** (F-2665): J-2000 deferred (not run): J-2049/F-2664 showed the engagement judge fails its negative control, so the 600+ fire counterfactual read would be uninterpretable. Resume J-2000 after J-2052 (position-free judge) passes both controls; D-0373 defeater and D-0396 hold unchanged.

- **2026-10-09** (F-2664): J-2049 (2026-10-09): positive control of the J-2031 pairwise open-doubt judge. Engaged beats plain 97-100 percent on all 3 rubrics (current/quote/masked) but mismatched negative control fails (33-40 percent vs gate 11): position-bias floor on near-tie pairs (mismatched wins only as A). No instrument passed both; cup replay not rerun, cup question still unanswered. Report docs/lab/si_open_doubt_pos_control_J2049_2026-10-09.md.
- **2026-10-09** (F-2660): 2026-10-09 J-2031 (F-2660): discriminating cup replay v2 (pairwise judge, mismatched-thought negative control, live-like seed with real recall, 2 samples/arm, 15 fires, generator gemma4:12b) -- the pairwise judge FAILED its negative control (mismatched thought beat own next thought 38.5 pct vs 11 pct gate), so the coordinate-only open-doubt cup (D-0396 hold stands) is neither shown to carry the concern nor refuted; cup vs control 43 pct, cup vs base 46 pct, all noise; rumination guard clean. Next: J-2049 positive-control the judge first. Report docs/lab/si_open_doubt_cup_replay_v2_2026-10-09.md, commit 1322722 on jobrun/lab_si.

- **2026-10-09** (F-2634): J-2008 (D-0396): coordinate-only open-doubt cup SHADOW publisher built (restart-gated, commits a9eeea3/7ec61c3/04d0c3e); 40-fire lab replay: baseline/cup/control all 97.5% affected, judge negative control 30%, bar FAILS uninformatively; D-0403 opened, J-2031 (better harness), J-2032 (post-restart read).
- **2026-10-08** (F-2605): J-1959 (D-0373): no measurable feature separates the 1 affected case from 15 unaffected; reflections are closed diagnoses never handed to the next step (98 pct no question, ready in 15 s median); one mechanism proposed (open-doubt cup, shadow-first) as D-0396; fresh n>=30 counterfactual read J-2000, build gated J-2001.

### What we have
- Phase 0 shadow-observing continuously since 2026-08-18 (`core/self_interrogation.py`,
  `data/self_interrogation_shadow.jsonl`, now 1,986 rows). Genuine-rate n has grown to 507 resolved
  fires (505 genuine, 2 hollow) = 99.6% genuine — far past the earlier 17/19=89.5% read this section
  used to cite.
- The counterfactual harness D-0031 was waiting on was actually built and run to completion the same
  day it was spawned (J-0164→J-0192, F-0164/F-0186), not left pending as this section previously said:
  genuine=True bucket, 9/17 decisive verdicts, only 1 affected (11%) — a genuine self-interrogation
  essentially does not move Du's next real thought.
- **New finding (F-2036):** D-0031's own reopen defeater (genuine-rate n past ~30-50 AND J-0164's read
  landing) reads as met, and has been for weeks, but nobody had acted on it — this section was never
  updated past 2026-08-24 to reflect J-0164/J-0192 landing that same day. J-1493 spawned to re-verify
  and open a `/decide` on reopening D-0031.

### What we need
A founder ruling on whether the low (11%) affected-rate itself argues for holding, independent of
whether the data-volume gate is met (J-1493's own question).

### What we're doing next
J-1493 (needs_input): re-verify the shadow-log counts fresh, then open a `/decide` on reopening D-0031.

> **History folded** — 2 dated Current State section(s) (2026-08-24 … 2026-08-24) moved to `docs/plan_history/self_interrogation.md` on 2026-09-27 by plan-compact. Derived timeline: `plan_ledger.py self_interrogation`.

