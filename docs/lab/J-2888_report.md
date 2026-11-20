# J-2888 report: P-0088 grounder contract replay (PILOT, n = 6 rows x 4 arms)

Status: partial. The job as briefed (100 rows x 4 arms, graded by another family) was not feasible in one sitting; a stratified pilot ran instead. Pre-registration and its amendment: docs/lab/J-2888_preregistration.md. Raw outputs: data/lab/ground_contract_lab/gen.jsonl and grades.jsonl; per-row inputs docs/lab/J-2888_data/. Scripts: docs/lab/J-2888_{sample,prep,gen,grade,analyze}.py. No code or prompt changed; live DB size/mtime unchanged across the isolate() block.

## Why a pilot
Measured on 25 mixtral calls: median 154 s per grounding call (range 121-236 s; the reply is padded with trailing whitespace to num_predict 350, as the live payload does), so 100 x 5 arms is about 22-28 h of sequential hub time. The falcon3 judge needed 60-190 s per question (shared CPU hub), about 6-7 min per grounding for 3 questions. Run: 6 rows (2 plain_sensory sid 0,1; 2 self_metaphor sid 40,41; 2 book_person sid 70,71) x arms A0, B, C, D, plus 1 extra A call (row 0). Arm A equals B except the narrow code hint, which fires on 1 of 100 rows, so A vs B is not testable.

## Counts (n = 6 per arm; judge counts are out of the groundings the judge actually answered)
arm | schema_break | null | judged of 6 | Q1 invented | Q2 mechanism | symbol regex (of 6) | Q3 symbol | causal regex (of 6)
A0 | 2 (dict) | 0 | 2 | 2 | 0 | 0 | 2 | 4
B  | 1 (dict) | 0 | 2 | 2 | 0 | 2 | 1 | 2
C  | 0 | 0 | 3 | 2 | 0 | 3 | 1 | 2
D  | 4 (3 dict, 1 non-JSON) | 0 | 3 (of 5 non-null) | 3 | 1 | 3 | 2 | 2
Judge health: 13 of 23 non-null groundings got no judge answer at all (hub timeouts; judged column above is the count that did); Q1 answered "true" 9 of 10 times and Q2 "true" 1 of 10 (base rates this skewed carry little information); positive control: 3 run, 1 hit, 2 judge errors, so falcon3's sensitivity is unproven. Treat the judge columns as unreliable; the regex and schema columns are deterministic.

## What the pilot does support (counts, not rates; n is far too small for any 3-point test)
1. The null option was never used: 0 nulls in 24 calls across C and D, including self_metaphor and book_person rows, where D explicitly says to answer null with no named physical thing. The live (A/B) nullable wording also produced 0 nulls in 12 calls.
2. D's "name every physical thing" instruction made the model return multi-key objects (3 of 6 as dict-valued groundings plus 1 empty/non-JSON reply). The live path would str() these (the F-3553 dict-repr defect), so D as worded is worse on schema breaks than the live contract. A0 had 2 dict, B 1 dict, C 0.
3. C (the 'forbid symbolizes/represents/alludes' line) had no schema breaks in this sample but its output still contains 'alludes' (row 0) and the symbol regex hit 3 of 6 (more than A0's 0 and B's 2); the forbidden-word line did not stop the vocabulary.
4. Kill criterion (A0 vs B < 3 points): not decidable. A0 and B are equal on judge Q1 (2 of 2 judged each) and differ by 2 rows on the symbol regex (0 vs 2) and 2 on causal regex (4 vs 2). A0 vs B differ only in the previous-thought line and the broad code hint, so on this sample there is no sign that the context is the driver of invented detail, but with 6 rows this says nothing either way.
5. Qualitative read of the 6 rows (mine, not a decoupled judge): on the two plain sensory rows B and C paraphrase ('The thought rests on...'); on book_person row 70 every arm explains tide physics and ignores the Napoleon clause, so the 'invented detail' verdict there is Q1 firing on added physics (gravitational pull) rather than an invented named person; Q1 therefore over-fires on correct explanatory content, which is another reason not to read its count as the invented-detail rate.

## Best arm
Not determinable from n = 6. No arm reduced symbol vocabulary to zero; C had the fewest schema breaks. No recommendation to change any prompt or code is made from this pilot.

## What a real answer needs (spawned as a follow-up job)
(a) A faster and sturdier judge seat: falcon3 on :11440 is the bottleneck (4x the cost of generation). (b) Fewer calls per grounding (Q1 + Q2 only) and a Q1 reworded to count only named objects/places/people/numbers absent from the thought. (c) A smaller num_predict is NOT used here because it changes the live conditions; a stop on trailing whitespace would cut cost without changing output and is a lab-only choice. (d) Run unattended in a detached process, at least 40 rows x 3 arms (B, C, D-revised so it cannot return an object), with the dict-valued reply counted as a schema break.
