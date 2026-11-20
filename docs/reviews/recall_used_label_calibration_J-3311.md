# P-0004 keys: used-label calibration on recall_served_log (J-3311, D-0552)

Status: ANALYSIS ONLY. Read-only on live data; nothing in Du changed. Written 2026-11-06 by job J-3311 (worktree wh_6).
Plan: memory_knowledge. Design this validates: `docs/reviews/memory_router_keys_shadow_design_J-3163.md` section 4.3.
Pre-registration (thresholds fixed before any rate was computed): `docs/lab/J-3311_data/PREREG_J-3311.md`, commit 151d3699.
Script: `scripts/analyze_J3311_used_label.py` (labels, judge, judge-batch, report); post-hoc diagnostic `scripts/_diag_J3311_u4_content.py`;
test `scripts/_test_J3311_used_label.py`. Data and results: `docs/lab/J-3311_data/` (labels.jsonl, labels_meta.json, results.json,
u4_content_diag.json, judge_scores_*.jsonl).

## 1. Bottom line

1. The J-3163 use proxy (10.0 percent) reproduces exactly (9.95 percent, 363 of 3,647 fragments, 200 cycles) but **more than half of it is
   function-word coincidence**: 206 of the 363 positives share only 4-grams of short or function words or bare apostrophe tokens. With a content
   test the plain 4-gram rate is 4.3 percent (F-4280).
2. The better label (embedding similarity of output sentences to fragment sentences, threshold = 99th percentile of a cross-cycle null, fixed in
   advance) gives **6.1 percent** (223 of 3,647); 3.6 percent if verbatim 4-gram echoes are removed. The two labels agree poorly (kappa about 0.26).
   The honest range for "served and used" is **about 4 to 10 percent**, up to 23 percent at a looser threshold. There is no ground truth, so the
   label is a calibration instrument and nothing more (F-4273).
3. **Use lives in one origin.** Lived fragments are used at 22.9 percent (4-gram) or 13.4 percent (embedding); every other origin with n of 30 or
   more is at most about 6 percent, and standing_insight (81 served) and action (92) are never used under either label (F-4274, F-4275).
4. **A 2-slot change cannot be expected to move what Du uses.** Du uses 1.1 (embedding) to 1.8 (4-gram) of about 18 served fragments per cycle;
   a 2-slot swap bounds at 0.27 to 0.46 used fragments per cycle, and the origin movement the J-3163 pilot measured for arm A implies about
   minus 0.02 to minus 0.035 (F-4276). The shadow bar must stand on judged relevance, as the design already says.
5. **Judge-vs-use AUC: not established.** The stage-0 replay judge (J-3309) is not built, and the local hubs were saturated by sibling chains, so
   only a small interim sample was scored (section 5). A lab job carries the rest.

## 2. Method (as pre-registered)

- Unit: one served fragment (cycle_id, fragment_id) from `data/recall_served_log.jsonl`, all 203 rows (200 distinct cycle_ids; 3 human cycles are
  logged twice about 30 s apart with identical fragment lists, the later row is kept). Output text = `voice.jsonl` `output.final` (all 200 joined).
  Fragment text = `memory_fragments.content` (nascence.db opened mode=ro immutable; WAL was 0 bytes). Log spans 2026-10-31 to 2026-11-05.
- U4 (baseline): at least one shared word 4-gram. SE: max cosine over (output sentence, fragment sentence) pairs, embedder
  paraphrase-multilingual-MiniLM-L12-v2. UE = SE at or above T = 0.7038, the 99th percentile of 18,235 null pairs (each served fragment against the
  outputs of 5 other cycles of the same input type). Sensitivity: p95 = 0.614 (23.5 percent used), p99.9 = 0.99999988 (degenerate, see 6).
- Null B: 1,500 random unserved fragments of the same origin mix against random cycles: 0 of 1,500 above T (mean SE 0.388 versus served 0.526). So
  UE is rare for a random fragment, but served fragments are topical by construction, so UE cannot separate "used" from "relevant and on topic".
- Judge arm: interim, pointwise or listwise, falcon3:7b (TII), never shown the output, only the cycle input and the fragment(s).

## 3. Use rate (all rows, Wilson 95 percent intervals in results.json)

| group | n | U4 (J-3163) | U4 content-checked | UE (primary) | UE without 4-gram echo |
|---|---|---|---|---|---|
| all | 3,647 | 9.95% | 4.3% | 6.11% [5.4, 6.9] | 3.59% |
| input_type human | 551 | 7.6% | n/a | 2.9% | 1.1% |
| input_type internal | 3,096 | 10.4% | n/a | 6.7% | 4.0% |
| origin lived | 1,356 | 22.9% | 10.8% | 13.4% [11.6, 15.3] | 6.9% |
| origin study | 458 | 3.5% | 0.9% | 2.0% | 1.7% |
| origin understanding | 407 | 1.2% | 0.5% | 1.0% | 1.0% |
| origin inner_thought | 307 | 2.9% | 1.0% | 3.3% | 2.9% |
| origin reading | 231 | 4.3% | 0.0% | 3.0% | 2.2% |
| origin gist | 181 | 0.6% | n/a | 2.8% | 2.8% |
| origin consolidation | 119 | 3.4% | 1.7% | 5.9% | 5.0% |
| origin research | 144 | 0.7% | n/a | 0.0% | 0.0% |
| origin standing_insight | 81 | 0.0% | 0.0% | 0.0% | 0.0% |

("Content-checked" per-origin figures are strict positives over all served in that origin, from u4_content_diag.json: lived 146, study 4,
inner_thought 3, understanding 2, consolidation 2, reading 0.) Per cycle: 18.2 served, 1.8 used (U4) or 1.1 used (UE); 31 percent of cycles use none
by U4, 49 percent by UE; human cycles 0.59 used (UE) against 1.20 for internal. Use rate by position in the served list peaks in the middle
quartiles (6.6, 14.3, 11.7, 7.5 percent), so the served list is not in a simple rank order; by logged relevance bin it rises from 1.4 percent
(relevance 0) to 9.7 percent (relevance 0.5 or more) under UE.

## 4. What this means for the key-blend read

- **The use label cannot be a pass/fail metric** and was never meant to be. The design's rule stands: success is judged relevance, with the
  shuffled-keys control.
- **The "judge score must predict use, AUC at least 0.6" sanity check (design 4.3, 5) is weak as written.** Reasons verified here: (a) the
  label is shaky (4 to 10 percent depending on definition, kappa 0.26 between two reasonable definitions); (b) it is dominated by one origin, so a
  judge that merely likes lived Q-and-A rows would pass; the logged retrieval relevance field itself reaches AUC 0.73 but falls to 0.57 to 0.60
  within lived and 0.54 to 0.58 within non-lived (intervals include 0.5 for non-lived) -- so AUC must be reported within origin strata, not
  pooled; (c) only about 220 to 360 positives exist, so a stratified AUC has wide intervals until the log doubles (job J-3663).
  Recommend the design's other two judge checks (shuffled-keys control at least 65 percent; hand calibration of 20 items) carry the validity,
  and the used-label AUC is reported within lived and non-lived, as supporting evidence only.
- **Ceiling and direction.** If the blend (arm A) moves slots away from lived toward standing_insight and understanding, as the pilot origin counts
  show, the expected change in used-per-cycle is slightly negative, which is not a reason to reject it (the label rewards echo). It is a reason
  not to read "Du used more/less" as evidence either way.

## 5. Judge arm (interim)

See section 7 for the numbers actually obtained. Constraints met on 2026-11-06: J-3309 (the stage-0 replay judge harness) is open and unbuilt, so
no shared judge existed; falcon3:7b on :11440 took 40 to 75 s for a one-token pointwise call and 126 to 235 s for a 15-fragment listwise call
(a trivial 2+3 prompt took 55 s) because sibling chains share the hub; gemma4:12b on :11439 took 40 to 233 s; the hot lane :11433 answered
/api/tags but its /api/chat timed out at 60 s for phi4 and tulu3:8b (not distinguished: cold load or the reported wedge). Ramses was not called.
Job J-3662 carries the full judge run.

## 6. Data-quality notes found on the way

- recall_served_log writes two rows for a re-voiced cycle (3 human cycles, 203 rows against 200 cycle_ids). Counting rows would double-count
  those; the script keeps one row per cycle_id. Whether this matters at larger n is in J-3663.
- The top 0.1 percent of cross-cycle (fragment, other-cycle output) sentence pairs are identical sentences (cosine 0.99999988): the outputs
  and the fragments repeat whole sentences across cycles. This makes the p99.9 sensitivity point meaningless and is consistent with the
  self-echo that lived "Q: ... A: ..." rows (Du's own earlier self-interrogation) invite.
- The pre-registered word regex counts apostrophes as word characters, so quotation marks around a name make 4-grams; that, with stop-word
  runs, is the 57 percent function-word share. Kept as written for the baseline so the reproduction stands; the content test is a labelled
  post-hoc diagnostic.

## 7. Judge numbers

The bar (AUC of judge score against the primary use label at least 0.6) is **not decided**. What exists, honestly labelled interim and
underpowered (F-4295):

| arm | rows scored | cycles | UE positives | AUC vs UE | cluster CI |
|---|---|---|---|---|---|
| falcon3:7b pointwise | 15 | 1 | 1 | 0.71 | none (1 positive) |
| falcon3:7b listwise | 47 valid (45 error rows) | 3 | 6 | 0.62 | 0.37 to 0.89 |

The listwise arm is unusable as a judge (wrong digit counts on 2 of 5 cycles, scores almost all 0 or 5). Neither number should be read as the judge
tracking or failing to track use. J-3662 (lab) runs the full judge-vs-use read on a quiet hub or on J-3309's harness; the pipeline is ready
(`labels`, then `judge` or `judge-batch` with a --tag, then `report`), resumable, and reports AUC against every label with a cycle-clustered
bootstrap. J-3663 re-runs the labels when the log has doubled. Ramses was not called.
