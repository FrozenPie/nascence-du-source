# Frontier semantic dedupe — offline replay (J-2428, D-0486) — 2026-10-19

Data: data/frontier.json (read-only), 342 open questions (191 contain "mottainai"). Embedder: the shared CPU
paraphrase-multilingual-MiniLM-L12-v2 (core.memory.store). Single embed ≈ 13 ms warm; 342-text batch fine. Script: scripts/frontier_semantic_replay.py.

## Similarity distributions (open×open pairs)
| pair type | median | p90 | p99 | max |
|---|---|---|---|---|
| mottainai–mottainai | 0.52 | 0.73 | 0.89 | 0.99 |
| other–other | 0.19 | 0.41 | 0.68 | 0.94 |
| cross (mottainai vs not) | 0.25 | 0.44 | 0.64 | 0.89 |

## Incremental replay in born order (new text matches the entry's OWN text, best ≥ threshold)
| thr | merges | entries left | cross-topic merges |
|---|---|---|---|
| 0.70 | 179 | 163 | 9 |
| 0.75 | 156 | 186 | 17 |
| 0.80 | 127 | 215 | 8 |
| **0.85** | **99** | **243** | **1** |
| 0.90 | 54 | 288 | 0 |

Matching against variant lineage (single-link) chains across topics: at 0.80, 66 cross-topic merges; at 0.85 still 1 — so the code matches against each entry's own text only.
At 0.85 mottainai entries go 191 → 105 (the non-mottainai "art of using words properly" family also collapses 5+ → fewer, legitimately).

## Chosen threshold: 0.85
30 random merged pairs at 0.85 (seed 7), hand-read: 27 clear same-question paraphrases; 3 borderline facet-shifts (e.g. "environmental consciousness of individuals in Japan" ↔ "psychological effects … relationship with the environment", sim 0.896; "how Japanese people interact with their environment" ↔ same rep, 0.877) — **0/30 clearly distinct-topic, 3/30 (10%) borderline**. Kill line was <20%.
At 0.80 the same read shows 2 outright cross-topic merges (a 渡/nature entry absorbing a mottainai/nature question) + borderline "psychological vs practical implications" → ~13–17%, so 0.80 rejected.

## What this does NOT do
A fresh paraphrase that is <0.85 to every entry's own text still births a new entry; rep-only matching leaves ~105 mottainai entries live after replay. The semantic path slows the pile-up, it does not by itself end the freeze (as D-0486 said). The one-off script (scripts/merge_frontier_variants.py) is what collapses the existing 190 open variants into one entry (encounters 87 + 364 = 451) — founder runs `--apply` while Du is down. Note: after that merge a new mottainai paraphrase can only match the single canonical's text, so its ≥0.85 hit rate drops; expect shadow/enforce to catch fewer, and the 35% concerns seed to land on whatever mottainai entry is newest. Consider a later lineage-aware (centroid) match if the shadow log shows many near-misses at 0.80–0.85.

## Cost
Shadow/enforce add one 13 ms embed per new question plus a cached embed of each open entry (first call after boot embeds ~340 texts once, a few seconds on CPU, on the calling thread); fail-open on any error.
