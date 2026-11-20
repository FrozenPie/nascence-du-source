# J-3308 pre-registration: near-duplicate text tests (U4)

Written BEFORE any replay number was computed (the inventory in section 1 was read from code only). Commit order in
the branch shows this file first. Author: the J-3308 agent, 2026-11-07. Plan: geometry_tuple_index. Decision: D-0636.

## 1. Question

Du's code asks "are these two texts the same?" in many private ways. Do the sites that really are near-duplicate
tests agree with a decoupled judge? If they disagree on 10 percent or more of the pairs where one reference tier
would be right, recommend a shared helper (a separate job builds it). If every site agrees at 90 percent or more,
leave them and log the duplication as known and free.

## 2. Pair universe (designed, boundary-enriched; not the natural traffic)

Five pair sources, 2,000 pairs total, read read-only from C:/Nascence/data (live files opened for read only):

| code | source file | pair | n |
|---|---|---|---|
| F | data/frontier.json | (variant, canonical parent) for merged and variant rows; plus hard and easy non-merged pairs | 600 |
| L | data/lane2_would_ask.jsonl | (wonder, an earlier wonder inside 7 days), the exact set `_wonder_repeat_check` compares | 500 |
| C | data/commitment_ledger.jsonl | (formed statement, another formed statement within 24 h). PROXY: reaffirm rows do not log the new statement text, so the true pair is not recoverable | 300 |
| D | data/deliberation_log.jsonl | (raw thought, integrated thought) | 400 |
| G | data/guidance_beliefs.json | (principle+scope of belief A, of belief B) | 200 |

Sampling inside each source is stratified, seed 3308, into: pairs every reference tier calls duplicate, pairs only
some tier calls duplicate, and pairs no tier calls duplicate (half of these "hard": max of char-3gram Jaccard 0.30 or
embedding cosine 0.60 reached). Because it is enriched toward the decision boundary, any agreement rate measured here is
a LOWER bound on natural-traffic agreement: a stop (agreement 90 percent or more) on this universe is strong; a pass
(disagreement 10 percent or more) is an upper bound and needs a natural-traffic confirmation before any build.

## 3. The site rules (each applied unchanged to the pairs, code read 2026-11-07)

- R_frontier: Jaccard over `[a-z][a-z']+` tokens of length 4 or more, strictly greater than 0.55 (`core/frontier.py:130,275`).
  `core/wager_curiosity.py:98,154` is the same rule on topics (identical tokens, identical 0.55); one rule in the replay.
- R_lane2: Jaccard over content stems (letters, 3+ chars, stopwords dropped, one of ing/ed/s folded), at or above 0.5 (`core/lane2.py:345,370`).
- R_delib: Jaccard over `[a-z']{3,}` tokens, at or above 0.88, or exact text (`core/deliberation.py:166`).
- R_guid: overlap coefficient over `[a-z]{3,}` tokens minus stopwords, at or above 0.12 as a CANDIDATE pre-filter; or embedding cosine at or above 0.70 (`core/guidance_learning.py:231,327`). An LLM classifier decides after it, so R_guid is a recall gate, not a final verdict; it is scored as such (its false negatives count, its false positives are expected and not counted against it).
- R_commit: embedding cosine at or above 0.45, else Jaccard over whitespace tokens longer than 3 chars at or above 0.5 (`core/commitment_ledger.py:855-885`).
- R_moment: Jaccard over alnum tokens of 3+ chars minus a tiny stoplist, at or above 0.28 (`core/moment.py:209,221`), a recall anchor not a duplicate verdict; included for the cross-site matrix only.
- Each rule is also applied to every other source's pairs (cross-site matrix) to show how far the sites disagree with each other on the same text.

Embedding = `core.memory.store._embed_batch` (paraphrase-multilingual-MiniLM-L12-v2, the shared model). Cosines are on that model only.

## 4. The three-tier reference

- T1 exact: equal after lower-casing and collapsing non-alphanumerics.
- T2 fuzzy: Jaccard of character 3-gram shingles of the normalised text, at or above 0.60 (set now, not tuned).
- T3 semantic: embedding cosine at or above 0.85 (the frontier's validated bar, `core/frontier.py:158-169`).
- Reference verdict "duplicate" = T1 or T2 or T3. "One tier would be right" = at least one of T1/T2/T3 equals the judge label.

## 5. Judge panel (decoupled)

Hubs, local only: gemma4:12b (:11439, Google), falcon3:7b (:11440, TII), yi:34b-v1.5 (:11442, 01.ai). The texts were
written by Du's qwen3.5:9b hot lane (frontier questions and wonders possibly by earlier lane models; all earlier
models used were qwen/deepseek/phi family as far as the registry says). None of the three judges is of those families.
No Ramses call. Judge label = majority of gemma4 and falcon3; if they split, yi:34b breaks the tie; if a hub cannot
answer, the panel is whoever answered and the pair is flagged. Per-site judge question is fixed in the script
(same-question for F and L, same-stand for C, "adds nothing new" for D, same-lesson for G); temperature 0.
Sample: 150 pairs, 30 per source, stratified evenly over the four strata of section 2 (7 or 8 each). The judge sees no
site verdict and no tier verdict. Pair order inside a prompt is randomised (seeded) to cancel position bias.

If the hubs cannot do 150 x 2 calls in the job's time (a call over 120 s is logged as a finding), the sample is cut
to what was judged, the cut is reported, and the remaining pairs are staged in docs/lab/J-3308_data/judge_pairs.jsonl
for a lab job.

## 6. Decision rules (fixed now)

- Site agreement with judge A_site = share of judged pairs of that source where the site's verdict equals the judge label, stratum-weighted back to the universe.
- Disagreement-where-a-tier-is-right D_site = share of judged pairs (with at least one tier equal to the judge label) where the site's verdict differs from the judge label.
- RECOMMEND shared helper iff D_site >= 0.10 for at least 2 genuine near-duplicate sites (F, L, C, D; G and moment are recall gates) AND on every site the best single tier, or the T1-then-T2-then-T3 ladder, has agreement with the judge no lower than the site's own (no regression).
- STOP (leave them, log as known and free) iff A_site >= 0.90 for every near-duplicate site.
- Otherwise: PARTIAL, report which site disagrees and name the one-site fix, no helper.
- 30 judged pairs per site is a small sample: every rate gets a Wilson 95 percent interval, and a decision that flips inside the interval is reported as "not settled".

## 7. Not done on purpose

No helper is built. No live file is written. `reentry` (no-new-tokens plus cosine 0.80) and `wager_curiosity` pair texts are not
replayed (reentry logs 200-char truncations only; wager's tokenizer is byte-identical to frontier's, shown by test).

## 8. Amendment 1 (2026-11-07, before the replay was run)

Section 3 listed R_frontier as the lexical Jaccard leg alone. Since D-0495 the frontier's live verdict is that leg OR the
embedding merge at cosine 0.85 (`core/frontier.py:FRONTIER_SEMANTIC_MERGE = "enforce"`, `SEMANTIC_MERGE_THRESHOLD`). The
site rule scored for source F is therefore the live OR (lexical > 0.55 or cosine >= 0.85); the lexical leg alone is kept as
`frontier_lex` in the cross-site matrix. No other rule or threshold changes.
