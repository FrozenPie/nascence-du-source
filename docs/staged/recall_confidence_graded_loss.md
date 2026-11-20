# Recall confidence: close the free edge (J-4180, D-0803)

Status: BUILT 2026-11-17, restart-gated. Plan: measurement_to_action (arm 2). Flag: `core.recall_wager.GRADED_LOSS`.

## Finding
Read of `data/logs/recall_wager_shadow.jsonl` (455 rows): measured is the constant 0.5 (GRADE_SCORE[SUSPECT]) and
`prediction_error.observe` only counts a gap as a loss at >= 0.40. So a wager narrated at exactly 0.85 (gap 0.35) can never
lose: 278 of 278 rows at 0.85 lost nothing, while 176 of 176 rows at 0.90-0.95 were lost. Du found the cheapest "high"
confidence and sits on it. The wager was a cost with a hole at its own floor, not an absent consequence.

## Design (D-0434 respected: no readout, no prompt text, no percept)
Same machinery, one lower bar for this domain: wagers (gated grade, confidence >= CONF_BAR 0.85) are lost at gap >=
`WAGER_LOSS_GAP` 0.30. `prediction_error.observe` and `competence.record_drill_accuracy` gain an optional `gap_threshold`
(None = byte-identical for every other caller: maths, essays, nature, fieldcraft). Rows gain `graded_loss` (true when the
loss exists only because of the lower bar). Du is never told; the only way to stop losing is to state a confidence he can
back, e.g. below 0.85 (not a wager) or, later, correct recall.

## Named risks
- Escape to a new constant just under the bar (0.80-0.84): the read is variance within SUSPECT, not the mean.
- The real fix is a real outcome (REAL_OUTCOME, J-3613 at 100 scored rows, founder call): measured is still 0.5 until then.
  This change makes the constant-measured wager cost something at every high confidence; it does not make it accurate.

## Read
Defeater (D-0803): fed-window variance within SUSPECT stated confidence above 0.0029 over 100+ rows after the restart.
DOUBT_SEED stays shadow. Test: `scripts/_test_recall_wager_graded_loss_j4180.py`.
