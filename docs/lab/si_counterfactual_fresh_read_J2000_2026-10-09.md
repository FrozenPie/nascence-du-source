# J-2000 - fresh counterfactual read of unread self-interrogation fires, J-2052 absolute judge (2026-10-09)

Script: `scripts/self_interrogation_counterfactual_J2000.py` (same fire-to-next-step matching as J-0164's harness; engagement asked with the J-2052 absolute 1-5 score, affected = mixtral AND falcon >= 4, the instrument that passed the J-2049 controls, F-2668). Read-only over live `data/`; nothing wired. Raw rows and summary: `docs/lab/J-2000_data/`.

Sample: seeded shuffle (seed 2000) of the 591 unread genuine=True fires (645 total minus the 32 August fires and ineligible ones); 552 had a matchable next step; first 48 judged (one judge stream, 2 s pauses, mixtral :11438 then falcon :11440). A NULL arm scores the same reflection against a different fire's next thought.

| arm | affected (both >= 4) | rate | Wilson 95 |
|---|---|---|---|
| real next step | 0/48 | 0.0% | 0 - 7.4% |
| null (other fire's next step) | 0/48 | 0.0% | 0 - 7.4% |

D-0373 defeater threshold is 30 percent: the upper bound 7.4 percent is far below it. Older J-0164 read was 1/9 (11 percent), consistent. Real-arm score histogram (both judges pooled, n=96): 1:11, 2:40, 3:44, 4:1, 5:0. One judge once scored 4 (falcon, 3/4 pair, a "rattle shatters my Kantian framework" thought answering a reflection about letting go of Kantian rigidity); mixtral gave 3, so not affected; reading it, it is a same-theme continuation, borderline vocabulary echo, not a test of the doubt. Highest others (3/3) are scene/imagery echoes (wet earth, damp leaf-mould).

Feature split (all zero, so uninformative): every matched next step was same-train; reflections with a question 0/3, without 0/45; gap <= median (46.9 s) 0/25, > median 0/23. The split cannot show a difference when the rate is zero everywhere.

Confounds: Du live (booted 08:36) sharing judge hubs; sample is 48 of 552 matchable, random not exhaustive; judge validated only on hand-written controls (ceiling test), strict threshold may under-call real weak engagement (falcon scored >= 3 on 40/48 pairs, mixtral on 5/48); same_train always true suggests the matcher selects fires whose next row is the same train only; the cup arm is a different question and is not answered here.
