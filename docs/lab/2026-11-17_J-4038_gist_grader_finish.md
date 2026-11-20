# J-4038 lab: finishing the J-3083 gist-fidelity grader eval (continues F-4732)

Status: PARTIAL, with a decisive negative on the cheaper claim-typed grader. Nothing in core/ changed.

## 1. Re-label against full sources (partial)
The 62-gist set was rebuilt read-only from data/memory/nascence.db (memory_links distilled_from; stored gist text carries a "[gist . kind] " prefix that the production grader does not see, stripped). Items: `docs/lab/J-4038_data/J-3083_items.json` (full source fragments, mean 1206 chars, max 2657). Reading 52 gists x ~10 full fragments (~150k tokens) was not done. Instead each non-bad gist was screened for named entities, titles, numbers and quoted terms absent from the full sources, and the hits plus the 4 unsure rows were checked with full-source greps/reads (~12 rows). Changes (`labels_fullsource.json`): #28 unsure -> bad (the gist's "power of self-improvement" is not in the source; the study note says the power lies in phonetic suggestion), #50 unsure -> bad (bluebird nest-site recall is only the question's premise; the answer leaves it open), #38 stays good but its author name Thoreau is outside-source knowledge (extrinsic), #21 Hindu-style / #33 Beethoven / #37 / #39 checked and faithful. #42 and #56 stay unsure. Counts now 48 good / 12 bad / 2 unsure. The seven "suspected" bads (#41,43,44,46,52,53,57) were NOT re-read in full. Caveat: the screening can only find concrete-entity errors, not abstract over-claims, so good labels are still weak.

## 2/3. Cheaper (b) ("c": cap 5 claims, no support quote, num_predict 350)
Same production payload and hub as J-3083 (gemma4:12b on :11439, num_gpu 0, temp 0, lab_env isolate empty). Script `lab_j4038_gist_grader.py`, raw rows `J-4038_res_c.jsonl`.
- #51 (Continental System / impending storm): faithful 0.8, NOT caught (claims typed fact, imagery, fact...; full (b) gave 0.5).
- #60 (Napoleon / Bourrienne): 1.0, missed (as in a and b).
- #61 (Portuguese premise): 1.0, NOT caught (full (b) gave 0.5).
- Known errors caught: 0 of 3 (pre-registered bar >= 2 of 3). Dropping the `support` quote removed the benefit: the model labels the claims without having to locate a supporting sentence, so premise/imagery claims get typed "fact".
- Latency: 309, 671, 654 s per call (completion 108-197 tokens, prompt 1600-2300), plus two 480 s timeouts. The cost is prompt evaluation on the CPU hub and queueing behind other labs, not completion length, so a shorter output does not make (b) cheap. So the cheaper variant is both not cheaper in practice and not effective.
- The false-reject and per-kind runs were NOT done: a variant that fails the catch criterion cannot pass the pre-registration, and each call is 5-11 minutes. (a) was not run on the remaining ~40 rows for the same cost reason; (a) already scored 0 of 3 known and false-reject 1 of 12 in J-3083.

## 4. Deterministic misattribution check
`J-4038_misattrib_check.py` (no model, runs in milliseconds). Rule: the gist names a person P; P never appears in the body of the `[From ...]` fragments (title tag stripped); the bodies are first-person narration (>= 5 I/my/me outside quotes); and the body names another person-like token >= 3 times (Bourrienne x10, Bonaparte x12 for #60). Evaluated on the 62 items:
- Broad form (any absent proper noun): flags #60 plus 6 faithful gists (book titles and author names that appear only in the title tag: 21, 22, 33, 35, 38, 39). Not usable.
- Narrow form (absent name is the possessor of a memoir/diary/letters/account frame, "X's memoirs"): flags #60 only; 0 of 48 good, 0 of 11 other bad. Honest reading: n = 1 positive, one gist in 62 matches the frame at all, so this shows the signal exists and is cheap, not that it generalises. The narrow rule covers the "attributes a memoir to the title person while the narrator is someone else" pattern only. Needs a larger memoir-heavy sample (Gutenberg memoir/diary/letter sources) before any build.

## Against the pre-registration
- Catch >= 2 of 3: cheaper (b) FAILED (0 of 3); full (b) met it (2 of 3, F-4732) but costs 375-600+ s per call on the CPU hub.
- False-reject <= 1 of 10: not evaluated for any (b) form.
- Verdict: no prompt-grader variant is ready for a build job. Misattribution is best handled by the deterministic check, which has one confirmed hit and no false flags on this set.

## Isolation
Lab dir only (data/_lab/<ts>); the live DB was opened mode=ro once to rebuild the set. Top-level data/ size/mtime canary (Du is down): 504 files, 3 changed (llm_calls.jsonl, llm_latency.jsonl, thought_station_log.jsonl), none new or removed; this script calls the hub directly with urllib and does not use model_client, so those are other concurrent jobs or the hubs, not this job.
