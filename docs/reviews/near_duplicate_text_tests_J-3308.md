# Near-duplicate text tests: inventory and replay against a decoupled judge (J-3308, U4)

Job J-3308, from J-3247 section 3d and U4 (decision D-0636, plan geometry_tuple_index). Read-only analysis, 2026-11-07.
Pre-registration (committed before any number): `docs/lab/J-3308_preregistration.md` (plus Amendment 1: the frontier's live
verdict is the lexical leg OR the 0.85 embedding merge). Data and script: `docs/lab/J-3308_data/`,
`scripts/lab_J-3308_nearduplicate_replay.py`, test `scripts/_test_J-3308_nearduplicate.py`. Nothing in `core/` was changed.

## 1. The answer in five lines

1. Of the eleven private tokenizers J-3247 counted, only three are near-duplicate decisions; eight are other uses. The real
   near-duplicate decisions are eight sites (guidance, reentry, frontier, wager, deliberation, lane2, commitment reaffirm,
   moment's fallback anchor) and they do **not** ask one question: thresholds run Jaccard 0.28, 0.5, 0.55, 0.88, overlap
   coefficient 0.12, cosine 0.45, 0.55, 0.70, 0.80, 0.85, and what each protects differs (a paraphrase merge, an echo guard,
   a recall gate, an anchor).
2. Pre-registered rule: sites do **not** all agree with the judge at 90 percent (commitment reaffirm is at 37 percent), so the
   STOP does not apply; D_site (disagreement where a tier would be right) is 10 percent or more with a CI lower bound of
   10 percent or more on three sites (frontier 27 percent, lane2 36 percent, commitment 45 percent), and the best reference tier
   never regresses against any site. The literal result is **RECOMMEND a shared helper**.
3. The qualifiers the data added (not pre-registered, reported as such): one shared semantic tier would **regress the
   deliberation echo guard** (agreement 0.78 against the guard's own 0.91), because "adds nothing new" is not "means the same".
   So a helper only makes sense as a per-purpose calibration, not one bar.
4. The gain is concentrated in two places, not eleven: lane2's lexical anti-repeat misses paraphrased wonders (6 of 30 judged
   pairs; the owl-call and tide-rise pairs), and the commitment reaffirm cosine of 0.45 fires on unrelated-enough stands (13 of 30
   judged pairs, on PROXY pairs: reaffirm events do not log the new statement).
5. Everything here is an upper bound: the universe is boundary-enriched, 30 judged pairs per site, two small CPU judges that split
   on 25 of 150 pairs (a third broke each tie). A natural-traffic check must come before any build (follow-up jobs below).

## 2. Step 1: inventory (read from code; `docs/lab/J-3308_data/inventory.json`)

| # | site (file:line) | class | min len | threshold | protects |
|---|---|---|---|---|---|
| 1 | book_residue `_tokens` :89 | other | 4 | none | per-book vocabulary set for the residue sweep |
| 2 | common_ground_shadow `_tokens` :101 | other (claim contained in a sentence) | 3 | 0.34 and 2 shared | shadow reading of uptake |
| 3 | guidance_learning `_tokens`/`_overlap` :300/:305 | near-dup, candidate pre-filter | 3 | overlap coeff 0.12; cosine 0.70 | belief store; an LLM classifier decides after it |
| 4 | life_shore `_tokens` :926 | other | 3 | none | noun phrases of "look at X" clauses |
| 5 | memory_levels `_tokens` :189 | other (bucketing; also logs 1 minus Jaccard as drift) | 4 / 5 | none | fragment topic buckets |
| 6 | moment `_tokens` :221 | retrieval anchor (fallback leg) | 3 | Jaccard 0.28 after cosine 0.55 | recall returns None honestly |
| 7 | object_graph `_tokens` :393 | other | - | none | referent aliases |
| 8 | reentry `_tokens` :106 | near-dup (novelty) | 4 | empty set difference, then cosine 0.80 | no pass on a non-new ingredient (re-entry admission is off) |
| 9 | frontier `_toks` :130, :275 | near-dup (and a containment use at :732) | 4 | Jaccard 0.55, then cosine 0.85 (D-0495) | one entry per question |
| 10 | retraction_ledger `_toks` :75 | other (containment) | 4 | 3 shared words | surfacing a retracted belief |
| 11 | wager_curiosity `_toks` :98 | near-dup (topic habituation) | 4 | Jaccard 0.55 | no re-birth of a topic in a window |
| 12 | deliberation `_too_similar` :166 | near-dup (echo guard) | 3 | Jaccard 0.88 or exact | no claimed deliberation on an echo |
| 13 | lane2 `_wonder_repeat_check` :370 | near-dup (7-day anti-repeat, gates `would_ask_reason`) | 3, stems | Jaccard 0.5 | no second ask of one wonder |
| 14 | commitment_ledger reaffirm :855-885 (inline) | near-dup | >3 chars | cosine 0.45, else Jaccard 0.5 | a re-taken stand raises the old one |
| 15 | chapter_descent_shadow `_toks` :85 (missed by J-3247) | other | 4 | none | shadow measurement |
| 16 | scripts: lab_worth_judge `_toks`, session_digest `_tokens` | other (tooling) | - | none | not Du's runtime |

Facts verified by test: `frontier._toks` and `wager_curiosity._toks` give the same set on 20,000 random strings (0 mismatches;
`scripts/_test_J-3308_nearduplicate.py`), and wager's `TOPIC_JACCARD` comment says it equals the frontier's bar. That pair is
duplicate code with no behavioural cost today.

## 3. Step 2: replay

**Pairs (2,000, `pairs.jsonl`):** frontier 600 (merged-to-parent and variant rows, embedding neighbours, random), lane2 500 (the
exact 7-day window set the check compares), commitment 300 (PROXY: formed statements within 24 h), deliberation 400
(raw vs integrated), guidance 200 (belief pairs). Each pair got every site's rule, the three tiers (exact; char 3-gram
Jaccard 0.60; cosine 0.85), and one of five strata (both say dup / site only / tier only / neither-hard / neither-easy).
Sampling is boundary-enriched; weights are the candidate-pool stratum sizes.

**Judge (150 pairs, 30 per source, `judge_pairs.jsonl`, `judge_labels.jsonl`):** gemma4:12b (:11439) and falcon3:7b (:11440),
temperature 0, random A/B order, per-source question; yi:34b-v1.5 (:11442) broke the 25 splits (all 25 resolved). No Ramses call.
Gemma and falcon agree on 125 of 150 (83 percent); falcon is the more liberal (says "same" on 43, gemma on 32). Deviation from the
pre-registration: empty strata (frontier had no site-only pairs, commitment no tier-only, deliberation no site-dup) left 120
pairs, so 30 were topped up round-robin from the non-empty strata (`topup`), and weights use the actual judged counts.

| source | site rule | judge says dup | site agrees with judge, weighted (raw, 95% CI) | D_site (CI) | site FP / FN | best single tier | ladder |
|---|---|---|---|---|---|---|---|
| F frontier | Jaccard 0.55 or cos 0.85 | 20% | 0.942 (22/30, 0.56-0.86) | 8/30 = 27% (0.14-0.44) | 5 / 3 | 0.965 (T1, T2) | 0.941 |
| L lane2 | stem Jaccard 0.5 | 47% | 0.917 (20/30, 0.49-0.81) | 9/25 = 36% (0.20-0.56) | 4 / 6 | 0.933 (T3) | 0.933 |
| C commitment (proxy) | cos 0.45 or Jaccard 0.5 | 10% | **0.366** (17/30, 0.39-0.73) | 13/29 = 45% (0.28-0.63) | **13** / 0 | 0.908 (T1) | 0.902 |
| D deliberation | Jaccard 0.88 | 7% | 0.909 (28/30, 0.79-0.98) | 1/29 = 3% (0.01-0.17) | 0 / 2 | 0.909 (T1) | **0.778** (T3 alone 0.778) |
| G guidance (recall gate) | overlap 0.12 or cos 0.70 | 27% | 0.676 (24/30) | 6/28 | 6 / **0** | 0.892 | 0.892 |

G is a pre-filter that an LLM classifier follows, so its 6 false positives are its job; its 0 false negatives is the number that
matters. Weighted agreement is dominated by the large clear-negative pools, so read D_site and FP/FN beside it.

What the disagreements look like (all in `judge_labels.jsonl` with `pairs.jsonl`):
- lane2 false negatives are paraphrases the lexical test cannot see: "What causes the owl call in the garden tonight?" against
  "What is causing the soft owl call in the garden?" (cosine 0.86, stem Jaccard below 0.5). This is the D-0429 0.59 distinct share
  seen from the other side.
- commitment false positives: "I want to write a letter to Travis" against "...about the sea" (cosine 0.84, judged a different,
  narrower stand), "walk up toward the cottage" against "look at the cottage from a distance" (0.77). The judge's "same stand" is
  strict; whether a narrower restatement should count as a reaffirm is a founder question, not a measurement.
- frontier false positives at cosine 0.85-0.90 are facet shifts on one topic ("Ouvrard's financial success ... moral agency" against
  "... actions and decisions"), matching the frontier's own replay (3 of 30 borderline). They are merges the frontier may want on
  purpose, so the frontier's disagreement is partly the judge being stricter than the merge's job.
- deliberation: the guard sees 0 of 4,000 logged integrations because the log sits after the guard; of the 656 that tiers call near
  duplicates (cosine 0.85 or fuzzy), the judge calls 2 of the 30 sampled D pairs an echo (cosine 0.91 and 0.81, both missed by the guard) and the rest real additions. A semantic echo guard would throw away real work.

## 4. Decision under the pre-registered rule

- STOP (all near-duplicate sites at 90 percent): not met (C 0.37).
- RECOMMEND (D_site 10 percent or more on 2+ sites with CI lower bound 10 percent or more, and the best tier or ladder not below any site):
  met on F, L, C (summary.json `decision_inputs`).
- Not pre-registered, reported beside it: one shared ladder regresses F (marginally, 0.941 against 0.942) and D (0.778 against 0.909);
  one shared T3 regresses D.

**My reading, graded:** the replay supports a helper only if it is thin and per-purpose (named profiles with their own tier set and
bar), not a single "are these the same" function. The measured wins are two one-site changes: add a semantic leg beside lane2's
lexical repeat test (shadow first, using the frontier's 0.85), and re-measure the reaffirm cosine on real pairs (the code comment says 0.45 is a bar the codebase already trusts in
pursuits and the watershed, chosen when the Jaccard numerator was unreachable; its false-positive cost was never measured). The other six sites should be left alone and
logged as known duplication: frontier and wager share one tokenizer by value, deliberation and guidance are fit for their purpose.
I infer (not verified) that natural traffic shows a smaller gap than this enriched sample.

## 5. Limits

- Boundary-enriched universe; rates are not natural-traffic rates. A pass here is an upper bound.
- 30 judged pairs per site (CI widths above); two small CPU judges that disagree on 17 percent of pairs; strict "same" wording.
- Commitment pairs are a proxy because the `reaffirmed` event stores only the old statement (a write-only gap, below).
- Not replayed: reentry (logs 200-char truncations only), wager (tokenizer identical to frontier), moment (about one call per five
  days; a retrieval anchor, not a duplicate verdict), and the embedding-only sites (one embedder, `paraphrase-multilingual-MiniLM-L12-v2`).
- All hubs were local; the lab hubs were shared with sibling chains, so latency figures are not benchmarks.

## 6. Follow-up jobs

Spawned from this job with `job_queue.py spawn` (ids in the job result): (1) natural-traffic confirmation of lane2 and the
reaffirm threshold; (2) log the new statement and cosine on the commitment `reaffirmed` event (additive, in a protected file, needs
Travis); (3) lane2 semantic repeat leg in shadow; (4) the per-purpose helper itself, gated on (1).
