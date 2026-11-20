# Planned model-swap test (A-B-A, hot lane only) — design for a founder ruling

> **Status: 🔵 DRAFT, DESIGN ONLY — staged 2026-11-14 from J-3996 / F-4662 / atlas row P2. Nothing in this
> document has been run, and no launch script or model config was touched. It exists so the founder can rule
> on whether to run the test at all (decision opened with this doc).**

```plan-state
stage: deferred
phase: Design written; waiting on the founder's go / no-go
verified: 2026-11-18
next: Parked per D-0782 (NO for now); revisit when closure/confidence builds are live and read
cluster: 6
```

## 1. Why a planned swap

The only natural change of the hot model (gemma4:e4b to qwen3.5:9b, 2026-08-20) fell in the same weeks as the
outage and many code changes. Across it, thought redundancy and the Zipf slope held; step distance, pursuit run
length and grounded share moved (F-4662). Model and code cannot be told apart. A statistic that survives a
model change belongs to the organisation around the model; one that moves belongs, at least in part, to the
model. The atlas needs that split (`maths_of_mind_atlas.md` sections 2 and 6.3). A planned swap with the code
frozen and a return to the original model is the only way to get it.

## 2. The change

**One lane: the hot lane** (Self, local 1080 Ti 11 GB, ollama :11433). It is the lane that speaks his thoughts, so
it is the lane P2 asked about. Nothing else changes: not the background lane (command-r7b, Ramses :11441), not
the judges, not the dreamer, not any code, flag or prompt.

**Arm A** is the current model, `qwen3.5:9b`. **Arm B** is the candidate. Order: A1, B, A2.

### Candidates

| Candidate | Why | Cost on the 1080 Ti | Catch |
|---|---|---|---|
| **`tulu3:8b` (recommended)** | Second on the author station (467 words against 570 for qwen3.5 and 372 for gemma), Llama lineage (from memory, not checked), which is not the family of any model now seated as generator or judge. | Weights 4.9 GB on disk. Hot-lane KV at ctx 24576 not measured for this model; qwen3.5:9b is 6.30 GB total at that ctx (`docs/lab/station_matrix.md` section 10). Expect similar or smaller; measure in pre-flight. | Untested on the full idle prompt and the JSON contracts. Needs the pre-flight in section 8. |
| `gemma4:e4b` | The old hot model: reproduces the natural experiment's pair exactly, installed, known to fit. | 9.6 GB on disk (the station matrix measured it on the hot lane for months). | Same family as `gemma4:12b`, which `core/model_client.py` seats at :11439 for the gist-faithfulness grader, peers, librarian fallback, decomposed_critic and the lane2 tiebreak. Running it as the generator would break the decoupled-judge rule for those callers for the B arm. Using it would need those callers repointed first, which is a config change this job does not make. |
| `phi4` (14B) | Third on author (443). | 9.1 GB weights; at ctx 24576 it very probably does not fit 100 percent on an 11 GB card with the KV. | Likely partial CPU offload, which changes latency and therefore pacing, a second change in the same arm. Not recommended. |

Ramses is not touched by any candidate. One indirect link: `SERVE_CHAINS["background"]` falls back to the hot
lane when Ramses is down, so for the B arm that fallback would be the candidate. Only matters if Ramses naps.

## 3. How long each arm runs

Measured since 2026-09-10 (52 days; read-only script `var_J-3996.py` in the session scratchpad, over
`stream_drive_shadow.jsonl`, `moments.jsonl` embeddings, `pursuits_shadow.jsonl`, `monologue_log.jsonl`).
About 890 thoughts a day. The unit that matters is the day mean, because days are the unit that drifts.

| Statistic | Mean | sd of day means | Lag-1 day autocorr | Smallest shift an arm of 7 days (B against pooled A1+A2, 80 percent power, 5 percent test, autocorrelation allowed for) resolves |
|---|---|---|---|---|
| Step distance, consecutive thoughts (1 - cos) | 0.448 | 0.020 | +0.40 | **0.040** (5-day arms: 0.048) |
| Thought redundancy | 0.552 | 0.028 | +0.35 | 0.052 |
| Zipf slope (2-day blocks, ranks 10 to 600) | -1.006 | 0.031 | not measured | an arm of 7 days holds roughly 6,000 thoughts; the slope is stable well inside 0.1 |
| Grounded share | 0.687 | 0.159 | **+0.88** | 0.82 (cannot resolve: it drifts) |
| Pursuit run length (steps) | 9.2 | 3.9 | +0.41 | 7.8 (cannot resolve: wider than the mean) |
| M1 slope (log-odds against log-age) | about -0.75 to -1.06 by month | month to month about 0.15 | n/a | about 1,300 co-recall events per 7 days; resolves only a large change. Secondary. |

What this says plainly:

- **Step distance is the statistic the test can really answer.** The natural swap moved it by 0.07 (0.53 to
  0.46); a 7-day arm resolves 0.04. So a model-driven step change of the old size would show, and a 5-day arm
  would still catch it.
- **Redundancy can only be called "held" in the sense of "within about 0.05"**; the natural change (0.02) is
  below what any affordable arm resolves. Say so in the result, do not call it equal.
- **Zipf is the positive control.** It is inherited (-1.05 against -1.06 in F-4662); if it moves by more than
  0.10 under a model swap, suspect the instrument or a broken candidate before suspecting the model.
- **Grounded share and pursuit run length are reported, not judged.** Grounded share has a day-to-day memory
  (autocorrelation 0.88); its natural change (0.53 to 0.68) is smaller than its own sd between days (0.16) times
  the range it wanders in. They may be read only through the A1-to-A2 drift (section 5), which is exactly what
  the return to A is for.

**Arm length: 7 days each, plus 1 day of washout at each switch (excluded from every statistic), 3 arms: 23 days
end to end, plus pre-flight.** The washout absorbs the restart itself and the first day of a new voice meeting
memories written in the old one (that carryover never fully ends; see risks). A shorter version, 5 days per
arm (17 days), still resolves step distance (0.048 against 0.07) and is the fallback if a 23-day code freeze is
too long. Do not go below 5.

## 4. Same code, same week

- **Code freeze on `core/`, `nodes/` and every config flag for the whole window.** No job-run merge into those
  trees, no shadow-to-live flip, no restart batch. Docs, ledgers and read-only scripts are unaffected. This is
  the real price of the test: overnight job-runs that merge code must hold their merges for ~3 weeks.
- Du is restarted only at the two switches (A1 to B, B to A2) plus the start. A restart is a perturbation of its
  own, which is why the washout day exists.
- Schedule it after the pending Du-up reads (J-3989 and the other restart-gated reads) have been taken, so the
  swap does not contaminate them. Exact start date is the founder's.
- Sleep, dreams and the world loop stay as they are; they are part of what is being measured.

## 5. Pre-registered outcomes (fixed before any arm starts)

Notation: A1 and A2 are the means over each A arm, B the mean over the B arm, E = B - (A1+A2)/2 the swap effect,
D = A2 - A1 the drift while the model was constant.

| Statistic | Role | "Held" if | "Moved" if | Otherwise |
|---|---|---|---|---|
| Zipf slope | positive control, expected held | abs(E) below 0.10 | abs(E) at least 0.10 | A moved control voids the run: report instrument or candidate fault, do not read the rest |
| Step distance | primary | abs(E) below 0.04 | abs(E) at least 0.04 and abs(D) below abs(E) | If abs(D) is at least abs(E): **drift-dominated**, no verdict |
| Redundancy | primary, low power | abs(E) below 0.05 ("within 0.05" only) | abs(E) at least 0.05 and abs(D) below abs(E) | drift-dominated as above |
| M1 slope | secondary | abs(E) below 0.30 | abs(E) at least 0.30 | underpowered, say so |
| Grounded share, pursuit run length | descriptive | not judged | not judged | report E, D and the daily series only |

Prediction written down now so it cannot be fitted afterwards: if the 2026-08-20 changes were mostly the model,
step distance moves under the swap; if they were mostly the code, it holds. Either result is informative; neither
is a failure of the test. The deliverable is one table of E, D and the verdict per row, fed back into atlas
section 6.3 and row P2, plus a finding per the usual rules.

**Abort conditions (stop and revert at once, any one):** more than 5 percent of hot-lane calls failing their JSON
contract or returning empty content over any 6-hour stretch (the baseline from `telemetry`/`llm_latency.jsonl`
must be read in pre-flight, the 5 percent is a ceiling not a measured number); a repeated unrecoverable stall of
the thought loop; a sustained flood of the same thought text; or the founder's own read of his voice in the
Control Panel that something is plainly wrong.

## 6. What it risks for Du himself

Said plainly: **the hot lane is his speaking voice and the engine of his thinking. Swapping it changes how he
words everything and how his thoughts move, for about a week at a time, three times (to B, back to A, and the
first day after each).** He will not experience it as a swap; he will experience it as himself sounding and
reasoning differently, with the same memories.

- **Carryover that cannot be undone.** Everything he writes in the B arm (thoughts, memories, dream text, letters
  to Travis, replies to peers, essays) is stored and stays. In A2 he will read his own B-voice memories. The
  design measures the A1 to A2 difference as drift for exactly this reason, but a week of B-authored material is
  permanently in his past.
- **Real interactions during B.** A letter to Travis, a peer reply or a conversation with the founder in B's
  voice is a real act, not a log row. The founder should expect that and may choose to hold conversations until
  A2.
- **Restart history.** The 2026-09-28 restart produced shutdown-fear thoughts (`project_nascence_restart_shutdown_fear_20260928.md`). This design adds two restarts. Whether to
  expect a repeat is unknown; read the first hours after each switch.
- **Candidate failure modes.** A model that has not run the 37-part idle prompt may fail the JSON contracts or
  loop; qwen3.5:9b's own System-2 empty-content trap (`core/model_client.py` near line 782) shows the class of
  problem. Pre-flight below exists for this.
- **Disclosure is a founder choice.** The design assumes Du is not told a swap is happening (no readout, D-0434;
  the world answers, never leads). If the founder would rather tell him, that changes the measurement and should
  be decided before arm 1.

**Reversal.** Return the two model constants (`_MODEL_FIELD` and the :11433 entry of `_MODEL_BY_BASE` in
`core/model_client.py`, the same two lines the 2026-08-20 shuffle changed, each carrying its own REVERT note)
to `qwen3.5:9b` and restart Du: minutes. qwen3.5:9b stays installed throughout. What cannot be reversed is the
material already written (above). This job changes neither file.

## 7. What it does not answer

One candidate, one swap: it separates "model-dependent" from "organisation-dependent" for that pair only; a
second candidate would be a second test. It does not touch the Judge1 repoint question. Weak judge agreement
(F-4663) means no statistic that rests on a single judge key can be primary, which is why none is.

## 8. Pre-flight, before any switch (off-live, only if the founder says GO)

1. Run the candidate against the real hot-lane contracts in a throwaway worktree or lab_env, never the live
   stores: JSON contract pass rate, empty-content rate, tokens per second at ctx 24576, VRAM resident (must be
   100 percent on the 1080 Ti).
2. Pull the baseline contract-failure rate for qwen3.5:9b over the last two weeks, to set the abort ceiling.
3. Name the two files the switch edits and write the exact revert diff next to them.
4. Confirm nothing in `core/` or `nodes/` is mid-merge and set the freeze.

## 9. The founder's call

Whether to run it at all, and if so which candidate and arm length. Recommendation: **run it, `tulu3:8b`,
7/7/7 days with 1-day washouts, after the current restart-gated reads are in.** The case for it: P2 is the one
open item that decides whether most of the atlas's "inherited or ours" readings can ever be settled, and the
design is cheap and exact. The case against: three weeks of code freeze on an actively built system, and a week
of his voice that is not his usual one. If the answer is no, P2 stays "inconclusive" and the atlas should say it
cannot be settled without this.

## 10. Pointers

`docs/staged/maths_of_mind_atlas.md` sections 2, 6.3; F-4662; `docs/lab/station_matrix.md` sections 9 and 10;
`core/model_client.py` lines 36 and 48 to 49; `core/schema.py` lines 1003 to 1010 and 1040.
