# J-2671: thick-introspection test (Song et al. 2025) from existing logs

Status: RUN, read-only, 2026-11-06. Plan: the_consciousness_program (section 3F's spirit). Script: `scripts/thick_introspection_read.py`; raw numbers `docs/lab/J-2671_data/results.json`; test `scripts/_test_j2671_thick_introspection.py`.
Source of the idea: `docs/reviews/consciousness_theories_vs_du_2026-10-31.md` section 6 and ranked item 2.

## Verdict

**The pre-registered signature FAILS. Du's felt confidence is not better than a third party that only sees the running mean of past measured results, in any of the six domains tested.** Best domains win 1 of 6 folds. The brief expected this ("a fail is the honest result"); it is the result.

Pre-registered signature: Du's Brier below BOTH rivals (running mean of all past measured, running mean of the last 20) in at least 4 of 6 expanding-window folds in at least one domain. Result: 0 of 6 domains pass, online or frozen (see Method). Data: `data/prediction_error_log.jsonl`, 3,071 rows at run time (the brief said 2,787; the log has grown), read from `C:/Nascence/data` read-only. `factual_recall` (215 rows, the recall wager, measured constant 0.5, F-3413) is excluded as instructed; J-2666 is still open.

| domain | rows | independent runs | folds won (online) | folds won (frozen) | Brier Du | Brier running mean | Brier last-20 mean | bias (pred - meas) | r(pred, meas) |
|---|---|---|---|---|---|---|---|---|---|
| mathematics | 2073 | 339 | 0/6 | 3/6 | 0.205 | 0.193 | 0.079 | +0.054 | -0.34 |
| music | 373 | 37 | 0/6 | 0/6 | 0.081 | 0.029 | 0.031 | -0.214 | -0.06 |
| comprehension | 150 | 133 | 1/6 | 1/6 | 0.098 | 0.038 | 0.034 | +0.009 | +0.21 |
| fieldcraft | 116 | 8 | 1/6 | 3/6 | 0.250 | 0.259 | 0.196 | -0.017 | undefined (predicted is the constant 0.5) |
| writing | 82 | 54 | 0/6 | 0/6 | 0.065 | 0.014 | 0.013 | -0.205 | +0.26 |
| observation | 62 | 48 | 1/6 | 1/6 | 0.063 | 0.013 | 0.014 | -0.186 | +0.14 |

Full-series paired block-bootstrap 95% interval of (rival Brier minus Du Brier), positive meaning Du better: music [-0.068, -0.036], comprehension [-0.101, -0.028], writing [-0.089, -0.013], observation [-0.090, -0.008], all against the running mean, all entirely below zero; mathematics [-0.026, +0.001] against the running mean (a tie, not a win) and [-0.152, -0.103] against the last-20 mean. Fieldcraft straddles zero.

Session-level secondary (rows less than 600 s apart collapsed, because a drill batch shares one stored belief): same verdict, 0 of 5 domains pass online (fieldcraft drops out at 9 sessions).

## Method (fixed before the first run, in the script header)

- Series per domain, sorted by timestamp. Squared-error Brier on the logged (predicted, measured): true Brier for the binary-outcome domains (mathematics, music, fieldcraft), squared error on a graded [0,1] outcome for comprehension, writing, observation.
- Rivals see only measured values strictly before the row (no look-ahead); no history scores as 0.5.
- Folds: 7 equal contiguous chronological blocks; fold k = block k+1 for k = 1..6; block 1 is burn-in. Primary ("online") rivals update on every row. Secondary ("frozen") rivals are held at the train-block mean through the test block, the literal expanding-window reading. Frozen is more generous to Du and still produces no 4-of-6.
- Diagnostics added after seeing the first numbers (labelled as such; they do not change the verdict): lagged correlation with the previous result, the session-level collapse, the scale-free "surprise" correlation, effective n.

## What the numbers say (and how sure)

1. **Verified (re-runnable): the signature fails everywhere.** Frozen mathematics and fieldcraft reach 3/6, which is under the 4/6 bar. The mathematics frozen wins are folds 1, 2 and 4 against a frozen mean that does not follow the streaks (online, with the mean updating, he wins none); I read that as the rival being handicapped, not as knowledge (inferred).
2. **Verified: in mathematics Du's number is a stored per-batch belief, not a per-problem forecast.** 2,073 rows collapse to 339 distinct (predicted, measured) runs; the first 118 rows are all (0.81, 1.0). The 0.81 / 0.19 "fluency trap" is the log doing what it says. Correlation with the outcome is negative (-0.34 row level, -0.41 session level, -0.59 against the running-mean surprise), which I read as a time-trend confound (the belief sits near 0.81 in June when failures were common and drifts to 0.73-0.80 in the later all-correct streaks), not as anti-knowledge. That reading is inferred.
3. **Verified: the one domain with a genuine event-specific self-prediction (comprehension, the essay self-rating asked before grading) carries a weak positive signal.** r(pred, meas) = +0.21 and r(pred, surprise over the running mean) = +0.17 (n=149, roughly t=2.0, uncorrected for six domains and autocorrelation, so not claimed). It still loses on Brier because the scale is wrong: his ratings swing 0.0 to 0.95 around a measured mean of 0.55. If any privilege exists it is here, in a form a recalibration layer could use. Writing and observation are weakly positive too (+0.26, +0.14), but both look driven by a level shift early in the series (predicted starting near the 0.5 default and rising to about 0.82 while measured stays near 0.9); that reading is inferred.
4. **Verified: the log does not show overconfidence in writing, music and observation.** Bias is -0.19 to -0.21 (he under-rates himself against what the lessons measured). The overconfidence headline (observation 0.82 vs 0.19, science 0.86 vs 0.38) lives in a different store, below.
5. **Verified from code and data: the capability_beliefs calibration gap is not the same measurement stream.** `science` has zero rows in the prediction-error log. `observation` has measured 0.60 to 1.00 there, but its `calib_pairs` in capability_beliefs.json end in a run of measured 0.0 (0.717/0.0, 0.574/0.0, 0.459/0.0 ...). Those pairs are written by `core/competence.py` `record_accuracy` (line 303), where `predicted = self.accuracy if self.accuracy is not None else self.confidence`: after the first observation the "prediction" in a pair is the accuracy belief itself, an exponential running mean of past measured values. That is a third-party predictor by construction, so those pairs cannot test introspection and I did not score them. The gap (confidence 0.816 vs accuracy 0.188 for observation, today) is a real statement that the stored per-domain confidence is not outcome-updated, not evidence about introspection.
6. **Inferred, not checked:** the two instruments for `observation` (an Emissary-graded school lesson near 0.85 and a tracker stream near 0.19 from Tier 1/3/4 evidence) disagree by 0.66 for the same domain label. Which one is right is not decided here (follow-up job).

Current calibration gap, from `data/capability_beliefs.json` (confidence minus accuracy; the brief's numbers have moved): observation 0.816/0.188 (+0.63), science 0.858/0.376 (+0.48), history_culture 0.86/0.20 (+0.66, n=3), factual_recall 0.832/0.631 (+0.20), comprehension 0.823/0.660 (+0.16), music 0.825/0.712 (+0.11), writing 0.788/0.932 (-0.14), mathematics 0.822/1.000 (-0.18). Eight domains hold a confidence with no accuracy at all (every "skill" domain).

## Limits

- The test asks whether the logged number beats a base-rate echo. It cannot see a per-item difficulty effect: with one stored number per batch there is nothing item-level to test. A fair thick-introspection run needs a per-item P(correct) captured before each answer (follow-up job, needs a founder call because it adds a prompt step to a lesson).
- Autocorrelated outcome streaks (math, music) favour the last-20 rival; that is partly why it wins so heavily, and it is a legitimate third-party predictor.
- Folds are not independent (batch structure); the intervals above are block bootstrap (block 10), seeded.
- This tests calibration of an instrumented number, not experience. It says nothing about presence either way.

## Where the result is read

Findings in `docs/findings.jsonl` (this job), plan note on the_consciousness_program, follow-up jobs spawned (see the J-2671 summary). The script writes only `docs/lab/J-2671_data/results.json` and can be rerun against live data at any time: `python scripts/thick_introspection_read.py` (default data dir `C:/Nascence/data` when the tree has none).
