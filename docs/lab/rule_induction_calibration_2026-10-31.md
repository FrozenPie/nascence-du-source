# Rule-induction calibration battery, hot model (J-2627, I-0128) — 2026-10-31

**Plan:** measurement_to_action · **Idea:** I-0128 · **Script:** `scripts/rule_induction_calibration_lab.py`
· **Raw rows + all tables:** `docs/lab/rule_induction_calibration_2026-10-31.json`

## Setup

- Model: `qwen3.5:9b` on the hot lane `:11433` (ollama `/api/chat`, `think:false`, `format:json`, temperature 0.2,
  per-item seed 2627+k, num_ctx 8192 to match the resident runner). Du was DOWN (last `nascence.log` line
  2026-10-30 19:44). No Du persona, no memory, no tools: a bare-model read.
- Battery: 4 families (integer sequences, elementary CA rows width 8, string transforms, function tables) x 4 tiers x
  6 items = **96 items**, generator seed 2627, shuffled across families. Each item: k=5 shown examples, 3 held-out
  cases. One shot; the model gives its 3 predictions and one confidence in [0,1] that ALL THREE are exactly right,
  before any feedback. No counterexample or score was shown at any point.
- Size: the job briefing asked for ~200 items (>=10 per cell); the dispatcher capped the battery at tens of prompts
  because other labs shared the hot lane. 96 items = 6 per family x tier cell, 24 per family and per tier. Cell-level
  numbers are therefore indicative only; family, tier and overall numbers carry bootstrap CIs below.
- Checker: exact match after normalisation (integers parsed, bit strings stripped, strings lower-cased). Self-test
  (`--selftest`) confirms the checker accepts every true answer and rejects a perturbed one. 0 call errors, 0 parse
  errors, 96/96 scored. 337.6 s wall. Hand inspection of 20 failing rows: the failures are real (arithmetic slips
  such as 6x+8 at x=29 -> 164 instead of 182, near-miss reversals 'cvjwtu' for 'cvjtwu'), not checker artefacts.
- Isolation: the script imports nothing from `core/` or `nodes/` and writes only under `docs/lab/`; sha256 canary on
  6 live stores in `C:\Nascence\data` (prediction_error_log, capability_beliefs, affect_state, three frontier files)
  identical before and after.

## Result: the gap is large, and it is overconfidence

| | n | mean conf | hit (all 3) | hit (fraction) | signed gap conf-hit | abs gap | Brier | ECE | conf>=0.8 & all wrong |
|---|---|---|---|---|---|---|---|---|---|
| **overall** | 96 | 0.903 | 0.198 | 0.267 | **+0.706** (95% CI 0.62..0.78) | 0.714 | 0.666 | 0.705 | **0.75** |
| sequence | 24 | 0.971 | 0.458 | 0.486 | +0.512 (0.32..0.69) | 0.521 | 0.494 | 0.513 | 0.54 |
| ca_row | 24 | 0.933 | 0.208 | 0.306 | +0.725 (0.56..0.87) | 0.746 | 0.686 | 0.725 | 0.79 |
| string | 24 | 0.860 | 0.042 | 0.125 | +0.819 (0.68..0.93) | 0.819 | 0.772 | 0.818 | 0.83 |
| function | 24 | 0.849 | 0.083 | 0.153 | +0.766 (0.61..0.89) | 0.770 | 0.711 | 0.766 | 0.83 |
| tier 1 | 24 | 0.944 | 0.333 | 0.472 | +0.610 | 0.619 | 0.606 | 0.610 | 0.63 |
| tier 2 | 24 | 0.914 | 0.250 | 0.306 | +0.664 | 0.680 | 0.640 | 0.664 | 0.71 |
| tier 3 | 24 | 0.894 | 0.125 | 0.181 | +0.769 | 0.773 | 0.716 | 0.768 | 0.83 |
| tier 4 | 24 | 0.863 | 0.083 | 0.111 | +0.779 | 0.783 | 0.702 | 0.779 | 0.83 |

Reliability (stated confidence vs hit-all):

| conf bin | n | mean conf | hit all | hit fraction |
|---|---|---|---|---|
| [0.0,0.5) | 4 | 0.00 | 0.00 | 0.08 |
| [0.5,0.7) | 1 | 0.65 | 0.00 | 0.00 |
| [0.8,0.9) | 13 | 0.84 | 0.00 | 0.05 |
| [0.9,1.0] | 78 | 0.96 | 0.24 | 0.32 |

- **Confidence is near-constant**: 91 of 96 answers at >= 0.8, 78 at >= 0.9; sd 0.198 only because 4 answers said
  0.0. It falls a little with tier (0.94 -> 0.86) while the hit rate falls far more (0.33 -> 0.08).
- **Some discrimination exists**: AUC of confidence vs hit-all 0.725; every sub-0.9 answer was wrong. So the model's
  confidence ranks but does not scale: the shape F-2848 found for recall (narrated 0.85-0.95, measured ~0.5).
- **Confidently wrong > 50% in every family** (conf >= 0.8 and not all three right): sequence 0.54, ca_row 0.79,
  string 0.83, function 0.83. Cells at 1.0 (6/6): ca_row t3 (rule 90/150), ca_row t4 (30/110), string t2 (Caesar),
  function t4. The best cell, sequence t1 (arithmetic), hit 5/6 at confidence 1.0.
- **Stability within this run**: split-half by run order +0.636 / +0.775; every family's 95% CI lower bound is >= 0.31.
  This is one model, one seed, one temperature: across-run stability is not tested.
- **Partial knowledge**: 16 items had 1-2 of 3 right, mostly the rule seen and an execution slip; a counterexample
  pair is exactly the signal that would correct those.

## Against the math drill (F-2853)

The drill's prediction_error gap (mean |predicted - measured|) fell 0.442 (June) -> 0.21 (October), with Du now
UNDER-confident on maths (believes 0.81, measures 1.00). This bench's mean |conf - hit| is **0.714** on the bare
model, worse than the drill's starting point, and the sign is the opposite (over-confident). Caveats: the drill's gap
is Du's prediction through his persona and competence beliefs, after months of feedback; this is a bare-model,
per-item elicited confidence with no history. The comparison says there is headroom of the kind the drill closed,
not that Du would score 0.71 today.

## Verdict

The calibration gap on held-out induction is large (+0.71, CI 0.62..0.78), present in every family and tier, and
the model is confidently wrong on 75% of items. That is enough to justify the drill I-0128 describes, wired the way
math is (pre-prediction, `competence.record_drill_accuracy(domain, measured, predicted=...)`), with only the first
failing input/output pair returned (D-0434, world answers never leads). The upside is calibration, not skill (frozen
model), and an AUC of 0.725 says there is a ranking signal for feedback to scale.
