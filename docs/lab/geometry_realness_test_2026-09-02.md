# §5.3 realness test — cross-space edge layer vs MiniLM text-distance (J-0416, D-0088)

**Script:** `scripts/geometry_realness_test.py` (read-only; reads `data/geometry_tuples.jsonl`,
`data/train_state_log.jsonl`, `data/co_recall_ledger.jsonl`; no DB touched, no lab_env isolation
needed). **Raw output:** `docs/lab/geometry_realness_test_1788309006.json`.
**Command run:** `python scripts/geometry_realness_test.py --sample_n 700 --k 10 --seed 42
--co_recall_dedicated_cap 1043` (2026-09-02).

## Why this instrument (D-0088's ruling)

D-0088 held P1/P2 pending §5.3's felt-response/co-recall realness test rather than a third
marginal-reach re-read: "A space is real iff its internal distances predict something (co-evocation,
co-recall, felt response) BETTER than MiniLM text-distance on the same items." That's a predictive
test against a real outcome, not the coverage/overlap question kill-criterion #6 already answered
(and answered ambiguously, 50/50, at scale — F-0501).

## The join

`geometry_census.snapshot(source="idle")` (called from `InnerMonologueNode._log()`) and
`_log_train_step()` (writes `train_state_log.jsonl` + triggers `memory_edges.log_co_recall()`) run
in the same `_think()` invocation on the same thought text. Matching on `thought[:100]` + nearest
timestamp recovered **11,290 clean joins** (median ts delta 0.18s, p90 1.24s) out of 18,015 `idle`-
source geometry tuples — the same cognitive event, not a coincidental collision.

## Two real, independent outcome variables

- **Felt response** = `restate_sim` (train_state_log): cosine of this thought's embedding to the
  immediately PRIOR thought's — how much felt/semantic content moved. Independent of the pair under
  test (compares to a different, earlier item).
- **Co-recall** = `developed` (co_recall_ledger, M1 ledger): 1 iff the fragments recalled into this
  step led to a DEEPENED train (0.40 ≤ restate_sim < 0.82). The plan's own "co-recall" concept.

## Pre-registered rule

kNN (k=10) regression/classification: predict each item's outcome from its k nearest neighbours
under (a) `core.mapping_census._geometry_similarity` (the same structural metric marginal_reach
already uses) and (b) MiniLM text-cosine, on the same sampled items (same seed=42, same MiniLM model
as F-0501/F-0428's marginal_reach, for direct methodological parity). Geometry wins a given outcome
only if it beats text on both point-estimate AND a paired significance test (sign test / McNemar).

## Results

**Felt response** (n=700): geom_mae=0.1213 vs **text_mae=0.1137** (text lower); geom
corr-to-truth=0.121 vs **text corr-to-truth=0.349** (text ~3x stronger); text wins on more items
(361 vs 339, sign-test p=0.43, not itself significant, but every point estimate favors text).
`geom_beats_text = False`.

**Co-recall**, dedicated pass over the FULL labelled pool (n=1043, not just whatever a 700-sample
happened to catch — the general-sample subset was n=69, too small; base rate developed=1 is 85.4%):
- majority-class baseline accuracy = 0.8543
- **geom_acc = 0.8399 (below the majority baseline)**
- **text_acc = 0.8830 (above the majority baseline)**
- paired: geometry right/text wrong on 8 items, geometry wrong/text right on 53 items —
  **McNemar p < 0.0001**. Reproduced with an independent seed (seed=7): 8 vs 49, same p<0.0001.

`geom_beats_text = False` on both outcomes. Text-distance predicts real co-recall development
significantly better than the cross-space edge layer's own structural similarity does — geometry
does not even clear the naive majority-class floor that plain text-cosine clears comfortably.

## Verdict

**Clear result, not mixed: the cross-space edge layer FAILS §5.3's realness test.** Neither outcome
(felt response, co-recall) shows geometry-distance out-predicting MiniLM text-distance; the co-recall
result is decisive and reproduced across seeds. Per §5.3's own wording — "Candidate fails → it's
text wearing a costume; do not admit it to the roster" — this space does not earn admission on this
evidence. Per D-0088's defeater ("a clear result either way … settles the P1/P2 investment question"),
this is the "coincidence" branch: **P1/P2 architectural investment does not clear the bar on this
evidence.** The defeater's retire-gate escalation was written for a "genuinely mixed" outcome; this
result is not mixed — it is a clean fail on the plan's own admission criterion, at least as strong a
signal for retire-gate consideration as the mixed case the defeater named, which is why a new founder
decision has been opened rather than assuming the answer either way (D-0088 is an active hold; this
session records evidence and defers the ruling per CLAUDE.md's discipline).

Consistent with what the rest of the plan's beta-space findings already show and are unaffected by:
state-conditioning (z=6-255) and funnel/hub concentration read as real per F-0428/D-0083 and are not
retested here — this verdict is specific to the cross-space EDGE layer (marginal reach / geometry-
distance as a retrieval-augmenting signal over text), not to the beta-space coordinates themselves.
