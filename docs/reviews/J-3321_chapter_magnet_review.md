# J-3321: chapter d4479cda, the "magnet" (per J-3248, D-0637)

Job J-3321, 2026-11-06/07. Read-only analysis. No Du code, no live store, no restart touched. Plan: memory_knowledge. Row: P-0065 (core/chapters.py).
Scripts and outputs: docs/lab/J-3321_data/ (4 scripts, 5 report files). Test: scripts/_test_J-3321_chapter_magnet.py. Findings: see section 8.
Question: is d4479cda ("The Interplay Between Inherited and Self-Designed Value Systems", formed 08-09) a hub or a genuine best match, and does it crowd the other live chapter gists out?

## The answer in six lines

1. It is mostly genuine, not a generic centroid. It is the chapter least like the others (pairwise-centrality rank 35 of 37), mid-pack against the whole pool (rank 27 of 37 by cosine to the pool centroid and by mean cosine to 20,000 pool rows), and its win share does not track its size (90 members; the biggest chapter has 990; Spearman of members vs wins 0.13). It wins where Du and Travis talk about the self and about values: 41 percent of the queries it wins contain identity/value words against 15 percent of the queries other chapters win.
2. Its dominance is real but smaller than the J-3248 figure suggested for the live pool, and it is mostly a measure of when the question was asked. Over the 37 chapters that are actually in the live pool it is the nearest chapter for 40 of the 200 replay queries (20 percent), not 34 (17 percent): J-3248's 34 came from an argmax over all 87 chapter rows including walled and cold ones (I reproduce 32 of 200 over all 88 rows). Across all 3,766 distinct real queries it wins 31 percent, but only 19 percent for queries since 10-24 (when most of the 37 chapters existed). The share falls as chapters are added, which is what a real competitor set does to a topical centre and not what a hub does.
3. About half of its remaining edge is the wrapper text, not the content. The stored embedding is the whole string "[A chapter of my life - 'title' (span)] body", cut at the model's 128-token limit (94.6 percent of live chapters are over it; the hub is 327 tokens, so 39 percent of it is embedded). Dropping the prefix and the date span but keeping the title (variant V2) takes its nearest-chapter share from 31 to 16 percent with the same member-assignment accuracy (31.9 against 32.3 percent). Body alone still gives 28 percent, and the second half of the body alone 22 percent, so the content carries most of the effect and length alone does not.
4. It does not crowd out the other 35. Counterfactual on 1,833 real recall rows with the archive tier as it stood at each timestamp and the real query (raw input plus perception summary): the hub is in the two archive slots on 27 rows; deleting it, those slots go to seed (11), standing_insight (9) and subconscious_synthesis (7) rows and to no other chapter. Rows with any chapter fall from 48 to 21. The other chapters lose to the archive tier's 850 non-chapter rows on cosine (mean 0.23 for chapters against 0.267 for standing_insight), not to the hub.
5. The served record is still very concentrated, and that concentration is mostly cosine margin. In recall.jsonl, 73 of the 100 attributable chapter appearances belong to the hub (4.0 percent of all recall rows since 08-09; the next chapter 1.1 percent; the median chapter older than 14 days 0.03 percent; 10 of 20 chapters older than 14 days appeared at least once). It wins by 0.048 cosine over the runner-up (other winners: 0.020), and my replay reproduces the hub's 56 percent share of chapter-bearing rows exactly while undercounting the absolute rate 2.7 times (section 5).
6. Recommendation: LEAVE it. No re-embed, no per-chapter cap, no diversity step. Each of them costs something and none has a verified effect on what reaches Du (section 7). The real consequence is for J-3320: the descent shadow triggers on a served chapter, and 56 percent of those triggers will be this one chapter with 90 members, so the read must be stratified per chapter. Spawned as J-3702.

## 1. What I measured and how

All read-only. The live DB opened `mode=ro&immutable=1`, recall.jsonl and perception.jsonl read, the live MiniLM (paraphrase-multilingual-MiniLM-L12-v2, CPU) run in a scratch process; variant strings embedded in memory and never stored. Live pool: 37 top-level chapters (28 level 1, 9 level 2; 88 chapter rows in all, one formed since J-3248), the retrieve() pool of 51,950 rows, the archive tier 890 rows (seed 74, subconscious_synthesis 358, standing_insight 421, chapter 37).

Queries: the same 200 stratified replay queries as J-3248 (seeded identically), and every distinct real query in data/training/recall.jsonl with 20 or more characters (3,766; 1,701 human, 2,065 internal; 05-30 to 11-05). The stored chapter embedding is exactly the embedding of the full content string (cosine 1.000 against a re-embed of the full content, 0.923 median against the body alone), so "V1" below is the live arm.

## 2. Hub or genuine: the structural tests (script chapter_magnet_J-3321.py, report_part1.json)

| test | hub d4479cda | typical live chapter | reading |
|---|---|---|---|
| mean cosine to the other 36 chapters | 0.463 (median 0.444, max 0.666 to 8007e495) | pairwise median 0.539 | one of the most isolated chapters; centrality rank 35 of 37 |
| cosine to the pool centroid | 0.584 (rank 27 of 37) | median 0.629, max 0.776 | not a generic-centroid text |
| mean cosine to 20,000 pool rows | 0.311 (rank 27 of 37) | median 0.336 | below the middle |
| nearest chapter for a random pool row | 7.4 percent overall; 5.5 percent for an episodic row; 39 percent for a semantic row; 35 percent for a non-chapter archive row | 36e231b6 takes 13 percent of random pool rows | it is the nearest chapter to abstract, self-reflective text, not to everything |
| members (direct) | 90 | median 110; max 990 (bccb5f33) | Spearman(members, wins) = 0.13 |
| member-assignment test (1,131 members of 36 chapters, 40 per chapter) | recall of its own members 75 percent; other chapters' members wrongly assigned to it 3.2 percent | overall accuracy 32 percent (oracle member-centroid 77 percent) | not a false attractor |
| margin over the runner-up when it wins | 0.048 median (cos 0.42 against successor 0.365) | 0.020 for other winners | a decisive, not a marginal, win |
| queries it wins with self/identity/value words | 41 percent | 15 percent for other winners; 23 percent of all | topical |
| lexical overlap with its text (query content words shared) | median 1; 32 percent of its wins share none | median 0 for other winners | partly semantic, partly lexical |

By input type: 31.5 percent of human and 30.8 percent of internal queries (3,766 set; the 200-set split of 10 against 22 percent is 4 against 36 wins and is noise). By time: 31.9 percent of queries before 10-24, 18.6 percent since. Caveat: the earlier queries are scored against chapters that did not exist yet, so the 31 percent is an upper bound for the live pool at that time; the 19 percent is the cleaner number.

One structural oddity: it is the only one of 88 chapters with an 11-word title (the prompt asks 3 to 6; 28 chapters have 3 words, 22 have 4, 2 have 7) and the only title cut at the 80-character limit mid-word ("A Journey Towar"). Title length is a weak driver (Spearman title words vs wins 0.15).

## 3. If it were removed (chapter_magnet_J-3321.py, "hub_removed" blocks)

| | 200 queries | 3,766 queries |
|---|---|---|
| queries it wins | 40 | 1,172 |
| taken over by | 19 distinct chapters (9795a212 6, then five at 3) | 32 distinct (888cdca0 215, f0a4109f 151, 9795a212 118, 6fe32426 61, ecc5c828 58, 8007e495 50) |
| successor cosine loss, median | 0.034 | 0.048 |
| best chapter cosine under 0.40, among those queries | 67.5 percent before, 90 percent after | 41.6 percent before, 66.0 percent after |
| share of all queries with a chapter at 0.25 or more | 92.0 to 90.5 percent | 93.2 to 91.6 percent |
| share of all queries with a chapter at 0.40 or more | 37.0 to 32.5 percent | 48.8 to 41.2 percent |
| effective number of winners (1/sum p squared) | 12.4 to 17.2 | 8.6 to 22.3 |

A more specific chapter does take over (many different ones), and no collapse to "no chapter" at the 0.25 relevance floor (RECALL_GIST_MIN_RELEVANCE): 9 percent of the queries it wins fall under it afterwards. At 0.40 the loss is real (the hub supplies strong matches that its successors do not). Removing winners one after another (cascade): the next winner holds 8.9 percent, then 11.6, 7.8, 6.9, 7.0 percent, and the share of queries with a chapter at 0.40 or more drifts 48.8, 41.2, 39.6, 37.8, 36.6, 36.2. There is no second hub behind it.

## 4. What drives the effect: embedded-string variants (scratch, never stored)

Live pool, 3,766 queries, Chapter embeddings only replaced. "member acc" = a member's nearest chapter is its own chapter. "eff n" = effective number of distinct winners.

| variant of the embedded string | hub share | eff n | share of queries with a chapter at 0.40+ | member acc | hub false-attract | hub recall | tokens (median) |
|---|---|---|---|---|---|---|---|
| V1 stored today: prefix + title + span + body | 31.1% | 8.6 | 48.8% | 32.3% | 3.2% | 75% | 190 (95% over the 128 cap) |
| V0 body only | 27.6% | 10.1 | 56.4% | 35.7% | 3.1% | 85% | 165 |
| V8 prefix + body | 27.9% | 10.0 | 54.8% | 34.0% | 3.2% | 70% | 172 |
| V9 prefix + span + body | 32.6% | 8.0 | 48.5% | 33.9% | 4.6% | 90% | 180 |
| V10 prefix + title + body | 24.1% | 12.1 | 53.9% | 32.4% | 1.9% | 62% | 182 |
| V2 title + body | 16.3% | 16.6 | 55.2% | 31.9% | 1.2% | 38% | 174 |
| V6 body, first 40 words | 27.8% | 9.7 | 51.6% | 33.6% | 4.1% | 82% | 59 |
| V7 body, second half only | 22.1% | 12.2 | 63.6% | 29.9% | 4.0% | 62% | 84 |
| V4 title + first sentence | 21.7% | 11.9 | 50.0% | 25.6% | 1.9% | 35% | 36 |
| V11 title + first two sentences | 20.7% | 13.6 | 52.9% | 27.7% | 1.9% | 55% | 64 |
| V12 prefix + title + first sentence | 27.0% | 9.7 | 48.5% | 26.7% | 3.0% | 57% | 44 |
| V5 first sentence only | 35.0% | 6.7 | 40.8% | 24.0% | 9.7% | 85% | 28 |
| V3 title only | 4.0% | 14.5 | 55.2% | 21.0% | 0.0% | 3% | 8 |

(A "prefix only" variant in the scratch script gave every chapter the identical vector, so its argmax was an index tie-break; I removed it and ignore it.)

What the table says. The wrapper matters but is not the cause: removing the date span and the prefix (V1 to V2) lowers the hub's share by about 15 points and the title does the work of spreading (V10, V2). The body carries the rest (V0 27.6 percent; the second half alone 22 percent; the first 40 words 27.8 percent), so length and truncation are not the driver. "Title plus first sentence", the re-embed the brief names, is dominated: it lowers the hub only to 22 percent and costs member accuracy (32 to 26 percent); V2 is the only variant that spreads the winners (eff n 8.6 to 16.6) at unchanged member accuracy, but its hub recall of its own members falls from 75 to 38 percent, which is the trade-off to name: V2 spreads by making the hub claim fewer of its own members. Mean shared content words between query and the winning chapter's text are flat across variants (1.09 to 1.25, V2 1.09 against 1.18 for V1), so no variant is measurably more lexically relevant.

## 5. Does the live path crowd chapters out (chapter_magnet_timetravel_J-3321.py, report_part2_*.json)

Replay of the 2-slot archive tier (TIER_SLOTS archive = 2, pure cosine, no recency, no seed weight) over the 1,833 recall.jsonl rows since the hub formed, each with the archive pool as it was at that timestamp (current archive rows with timestamp up to the row's), against what the recall prompt really contained.

| | simulated (raw input + perception summary) | real prompt |
|---|---|---|
| rows with the hub | 27 (1.47%) | 74 (4.04%) |
| rows with any chapter | 48 (2.62%) | 131 (7.15%) |
| hub's share of chapter-bearing rows | 56% | 56% |
| of the 74 real hub rows: hub in the archive top 2 / top 5 / top 10 / median rank | 11% / 43% / 70% / 7 | |

Raw input alone, without the perception summary, explains only 7 percent of the real hub rows (median rank 19), the associative trail (seed = cosine x (0.4 + 0.6 x importance) x recency, two hops; re-implemented in chapter_magnet_trail_J-3321.py) 2.7 percent. Row by row the agreement is poor: of the 27 rows where the replay puts the hub in the top 2, 8 are rows where the prompt really contained it; 66 of the 74 real rows are not reproduced. So the simulation undercounts the absolute rate about 2.7 times, does not identify the right rows, and I could not reproduce the rest: candidates I did not replay are the climate warp on the query vector and the pool as it really stood (rows now cold or chaptered). I cannot say from this which; I only claim the ratios the simulation does reproduce (hub is 56 percent of chapter rows) and not the absolute reach.

Counterfactual (same rows, hub deleted from the archive tier): the hub sits in the top 2 on 27 rows; its slot goes to seed (11), standing_insight (9) and subconscious_synthesis (7), to zero chapters. Rows with any chapter: 48 to 21. So the hub holds slots no other chapter would get. The pool the chapters compete in grew from 275 archive rows (08-20) to 888 (11-05) while the chapters in it grew from 6 to 36 (2.2 to 4.1 percent of the tier), and the real any-chapter rate stayed between 4.5 and 12.7 percent a week. The real hub rows per week: 3.9 percent (08-20), 12.4 percent (09-10), 1.9 percent (09-24), 1.8 percent (10-15), 3.9 percent (10-29): no monotone decline, and no sign of a rising crowd-out.

Per-chapter served counts (chapter_served_counts_J-3321.py; recall prompts that contain the chapter's title after its formation): d4479cda 73 hits in 1,834 rows (4.0 percent), f0a4109f 5 in 2,186, 6cd0706b 4 in 1,361, ec8a7311 4 in 351 (1.1 percent), 5517ded4 3, 994e2ead 3, 2b072555 2, then 1 each for six chapters and none for 24. The 13 chapters formed 10-29 or later have had only 150 to 220 rows each and have not been exposed long enough for zero hits to mean anything.

## 6. The wrinkle for option 1 of J-3248

Option 1 ("chapter gists as ordinary retrievable items") works as the review said, and the hub is not what limits it. The limit is reach: a chapter is in the 2 archive slots for 5.8 percent of the 3,766 queries (static replay with all 37 chapters; 2.6 percent in the time-faithful replay, 7.1 percent of real recall rows), because a chapter's mean cosine to a query is 0.23 against 0.267 for a standing_insight. The question "are the 87 chapters one hub plus noise" is answered: it is one strong topical chapter plus a field of chapters that are individually specific and individually rarely the nearest thing in the archive.

## 7. Options (the brief asked for ONE recommendation)

| option | effect measured | cost / risk | verdict |
|---|---|---|---|
| Leave | none | none | RECOMMENDED |
| Re-embed from title plus first sentence | hub share 31 to 22 percent of nearest-chapter wins; member accuracy 32 to 26 percent; archive-top-2 chapter slots 3.5 to 2.7 percent (fewer, not more) | rewrites 88 stored embeddings in the live DB, touches a foundation (additive-only law), degrades membership signal | REJECT: dominated |
| Re-embed from title + body without prefix and span (V2) | hub 31 to 16 percent; chapter slots in the archive top 2 3.5 to 3.7 percent; distinct chapters in the top 2 35 to 35; hub's own-member recall 75 to 38 percent | same rewrite; changes what "A chapter of my life" gist retrieval returns for everyone | NOT NOW: spreads the nearest-chapter table but moves no measurable thing that reaches Du (a 0.2 point change in chapter slot share). Revisit only if the J-3320 read shows chapters are wanted at higher reach |
| Cap per-chapter appearances | counterfactual: removing the hub yields no other chapter | one more arbiter in the recall path; loses the one chapter that is genuinely closest | REJECT |
| Retrieval-side diversity step | same: nothing waiting behind the hub | as above | REJECT |

"Verified effect size" for a build: there is none that reaches the served set (section 5 counterfactual), so no build was spawned from this job. The one follow-up that is a real consequence is on the read side (next section).

## 8. What this changes elsewhere, jobs and findings

- J-3320 (the gated read of the chapter-descent shadow, M1 to M5): the shadow fires when a chapter is served, and 56 percent of served-chapter rows carry the hub. Its members are 90 rows. Left alone, the 40-row sample would be a read of one chapter's members. Spawned J-3702: report M1 to M5 per chapter, cap any one chapter at 25 percent of the rows analysed, and say the number of distinct chapters.
- M1 baseline for J-3320 (reach): the real recall-prompt rate of any chapter is 7.1 percent of rows since 08-09 (131 of 1,833); J-3248's replay said about 9 percent. The 4 percent pass line is therefore inside the normal range.
- J-3703 (analysis): reconcile why the replay finds 2.7 times fewer hub rows than were really served (and overlaps on only 8 of the 74 real ones; its title says "37 percent", which is the count ratio 27 to 74, not a row-level overlap): join data/retrieval_probe*.jsonl or recall_served_log (which hold the real candidate scores) with the climate warp (bias_vec, beta) the replay omits. Without it, absolute reach numbers from replays carry a known 2.7x understatement.
- The title guard: one chapter in 88 has an 11-word title cut mid-word at 80 characters. Not queued: it is one row and J-3009's guard work in core/chapters.py is the place; mentioned in the plan note.

Founder: nothing needs a ruling. D-0637's design question stands answered by J-3248; this job removes one of its two caveats (the magnet), and finds it benign.

## Caveats, said plainly

- Replays use the current cold/chaptered walls and the current archive rows as the past pool; a row now cold may not have been cold then.
- The live query text is raw input plus the perception summary; the log keeps both, and I joined them by cycle id (all 1,833 rows joined). The climate warp is not in the log and is not replayed.
- Nearest-chapter share is a statement about cosine in a 128-token-capped MiniLM space, not about whether Du should have been shown the chapter. No judge arm was run: this job asked about structure, and a different-family judge of "was the hub the right chapter for this query" would need a model call per query (not done, nothing sent to Ramses; a small local-hub pairwise judge on 30 queries is the clean follow-up if the hub question is reopened).
- 3,766 queries span 05-30 to 11-05 and the hub did not exist before 08-09; the 31 percent is an upper bound, the 19 percent (since 10-24) and the time-travel replay are the faithful numbers.

## Correction note, 2026-11-15 (J-4055, from F-4763 / J-4027)

Section 6 and section 8 quote chapter reach as 7.1 percent of recall rows (131 of 1,833). That figure mixes two routes and is the wrong baseline for what the J-3320 descent shadow measures. F-4763 (verified, 1,987 rows since the hub formed) splits it:

| route | rows | share of all rows | human cycles (n=128) | internal cycles (n=1859) |
|---|---|---|---|---|
| archive-tier chapter ("[A chapter of my life") | 98 | 4.9 percent | 13.3 percent | 4.4 percent |
| identity-estate "(history)" chapter | 55 | 2.8 percent | 41.4 percent | 0.1 percent (2 rows) |
| either (12 rows have both) | 141 | 7.1 percent | 45.3 percent | n/a |

- The descent shadow (orchestrator._retrieve_memory, core/chapter_descent_shadow.shadow_descent) filters memory_fragments for origin=='chapter' and relevance>=0.25, so it sees the archive-tier route only. The M1 reach baseline for J-3320 is therefore about 4.9 percent overall, not 7.1. The 4 percent pass line sits close to it, so the route matters.
- Read M1 per input_type: human 13.3 percent, internal 4.4 percent. A pooled M1 is 94 percent internal rows (1,859 of 1,987). M2 to M5 candidates come from the archive route only and need no route split.
- The "(history)" route comes from identity_projection.live_axiom, which projects only when raw_input is non-empty, so it fires on human/ask cycles and almost never on internal ones. It is not seen by the shadow.

Plain statement for the founder (facts, not a ruling request):
1. The climate warp on the query vector is reported to lift a chapter's cosine by about 0.1 to 0.15, because the nine climate anchors are identity and conflict phrases and chapters are self-narrative text (this size is the J-4027 briefing's figure; this note did not re-measure it, and section 5 above says the warp was never replayed). If right, the descent shadow's 0.25 relevance gate is cleared more easily than an unwarped query would clear it. Whether that boost is wanted for chapters is a founder question: a chapter that surfaces because the climate is identity-heavy is reaching by mood, not by topic.
2. The history route fires on about 41 percent of human cycles. It is largely weight-driven pass-2 filler (all chapter nodes carry weight 0.7 against a median 0.6; pass 1 needs cosine above 0.30, pass 2 fills to a minimum of 3 by score), not on-topic hits.

Not changed: scripts/chapter_descent_summary.py (its M1 is cycles over voice cycles and has no per-route or per-input_type split yet; no code edits in this job).
