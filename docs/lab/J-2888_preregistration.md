# J-2888 pre-registration (written before any grounder call was made)

Lab for F-3553 (P-0088 grounder). Read-only against Du's data; no code or prompt changed.

## Sample
100 emissary rows from data/deliberation_log.jsonl (last 30 days of the log, raw 60-1200 chars), seed 2888, strata by regex on the raw thought
(priority book_person > self_metaphor > plain_sensory): 40 plain_sensory, 30 self_metaphor, 30 book_person. The regexes are crude; strata are labels
of convenience, not ground truth. File: docs/lab/J-2888_data/sample.jsonl.

## Arms (all: constitution prefix, temperature 0.1, num_predict 350, num_gpu 0, format json, model mixtral:8x7b on :11438, one call per row per arm, no retry on leak)
- A0  "as logged before J-2883/J-2886/D-0573": live nullable task text + user prompt with `his latest thought` (the previous emissary row's raw, cut to 160) + the BROAD code hint (source_sight.is_self_mechanism / see_code).
- A   the live contract and live user prompt as ground_thought builds it today (J-2883: no latest thought; D-0573 narrow code hint; D-0570 nullable schema).
- B   A without the code hint (briefing's B: no `latest thought`, no hint; A already lacks the thought, so A vs B isolates the hint).
- C   B with schema {"grounding": ..., } or {"grounding": null, "reason": "no physical referent"} and a line forbidding symbolizes/represents/alludes.
- D   C plus: mechanism required only when the thought names a concrete physical thing, otherwise null; and name no object, place, person or number the thought does not contain.
Context approximation: the dream and concern lines come from the live store as it stands now (one fixed context for every row), not as it stood at each row's timestamp. The previous-thought line for A0 is the previous emissary row's raw.

## Metrics (per arm, counts over 100)
1. invented_detail: judge Q1 (core/ground_grade.py Q1_SYSTEM) answers true AND its quote is verified (in the grounding, not in the thought). Deterministic proxy: capitalised tokens or digits in the grounding that appear nowhere in the thought (reported separately).
2. mechanism_present: judge Q2 (ground_grade Q2_SYSTEM) true. Regex proxy: F-3553 causal regex.
3. symbol_reading: F-3553 regex (symbol/metaphor/allude/represent/evoke/figurative) hit, and the judge's own Q3 (does the grounding explain the thought as a symbol or meaning rather than as a physical thing); both reported, headline = regex OR judge.
4. schema_break: reply not JSON, not an object, `grounding` key missing, or grounding is neither string nor null; also dict-valued grounding.
5. null_rate: grounding null.
6. echo_risk (pass 3): judge Q4 reads grounding and raw only: would a writer using the grounding as a fact source copy a fact the thought lacks as if true? quote verified as in Q1. Headline = share of non-null groundings.
Denominators: counts over all 100 and over non-null groundings; null rows count as not-invented, not-mechanism, so arms with nulls are compared on both denominators.
Judge: falcon3:7b via judge_panel._ask on JUDGE_2 (:11440), blind to arm and to the grounder model. Positive control (an invented sentence appended) on 15 random groundings; judge sensitivity reported; judge base rates reported.
Kill criterion (briefing): if A0 and B differ by less than 3 points on invented-detail rate, context is not the driver and F-3549's fix is hygiene only. Same test also reported for A vs B.
"Best arm": lowest invented_detail + symbol_reading rate subject to mechanism_present on non-null groundings not falling more than 10 points below the best arm; stated with counts, not a verdict about shipping.
Noise: 100 rows per arm, one sample at temperature 0.1; a difference under about 10 points between arms is inside binomial noise (SE about 5 points at p=0.5) and will be reported as such.

## Amendment 1 (written after 3 grounder calls and before any analysis; reason: scale)
Measured cost: mixtral replies take 120-235 s each (output padded to num_predict by trailing whitespace; the live payload does the same) and the falcon3 judge 60-190 s per question on the shared CPU hub. 100 rows x 5 arms (about 22-28 h) is not achievable in one sitting.
Changes: (1) arm A is not run separately: its user prompt differs from B only by the narrow code hint, which fires on 1 of 100 sample rows; for the other rows A is B by construction, and the A-vs-B contrast is reported as "1 row, not testable". Arms run: A0, B, C, D. (2) Rows are processed in a stratified round-robin (sensory, self-metaphor, book/person), so any prefix is stratified; the run is a PILOT of however many rows finish in the budget (target 7 rows x 4 arms), reported with n. At this n the 3-point kill criterion cannot be resolved statistically; the report says so and gives counts only. (3) Judge question Q4 is dropped; echo risk = Q1-verified invented detail with no hedge word (likely, perhaps, possibly, may, might, could, such as, probably) in the grounding sentence containing it. Q1, Q2, Q3 stay.
