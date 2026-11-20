# J-3048: does the tension-resolution judge need more than a 4-word label? (from F-3750, P-0103)

Status: measured on local single judges (falcon3:7b complete, gemma4:12b partial), NOT on the live Mixtral + Falcon + Granite panel. Read-only toward Du; core/tension_ledger.py and core/judge_panel.py unchanged.
Data: docs/lab/J-3048_data/ (gold_pairs.jsonl, blind_sheet.txt, gold_labels.json, replay_falcon.jsonl, replay_gemma.jsonl). Scripts: scripts/j3048_tension_gold_build.py, _replay.py, _report.py. Test: scripts/_test_J3048_tension_gold.py. Re-print every table below with `python scripts/j3048_tension_gold_report.py`.

## What was built
1. Gold set, 120 pairs, blind-labelled before any replay (labels file written first; the sheet shows label, thought and the tension's 3 most recent member shadow events, no source, no panel verdict, no sim):
   - 60 CLOSURES, random from the 229 tensions the live matcher closed (220 archived + 9 live in subconscious_state.json; the briefing said 219).
   - 60 REFUTED candidates: thoughts the panel actually refused (verdict False), capped at 2 per tension (47 distinct tensions).
2. Refuted candidates are a reconstruction, stated plainly: data/tension_judge_attempts.jsonl (J-3050) does not exist yet (Du has been down) and the text of a refused thought was never stored. Each key=resolves row of data/judge_panel_log.jsonl (1869) was joined to the monologue's own resolved_thought light event stored 8-30 s earlier (median gap 11.9 s) and to the tension of that label whose stored centroid passes the matcher's gate (cosine >= 0.62 recomputed against final centroids, live floor 0.70; plus the shared-token guard). Result: 433 of 1869 rulings joined (67 True, 331 False, 35 no-verdict); 1262 were dropped because the tension record is in neither the archive nor the state (so the sample is survivor-biased toward tensions that were kept), 72 had no event in the window. 534 of the 535 candidates with a surviving label pass the token guard, which is the evidence the join found the right thought.
3. Gold labels by one reader (this session, Claude; not the author of F-3750's n=15 sample): S settles / R restates or re-encounters / U unrelated. 120 items: 38 S, 54 R, 28 U; 36 flagged unsure. Closures: 16 S, 20 R, 24 U. Refuted: 22 S, 34 R, 4 U.
4. Replay of every pair through the exact live 'resolves' prompt (system text and user template asserted byte-identical to core/tension_ledger._judge_resolution by the test), 4 user-block variants: V0 live; V1 strip the 'unresolved:' prefix; V2 add the 3 most recent member events (200 chars each) under 'WHAT FORMED THE TENSION'; V3 both. Judges: falcon3:7b :11440 (live JUDGE_2 seat) and gemma4:12b :11439 (stand-in for the Mixtral seat; Ramses not called), each through judge_panel._ask. The panel verdict is composed offline exactly as rule_detail does for this key (D-0530: resolves is in GRANITE_CONSTANT_TIEBREAK_KEYS, so both True -> True, both False -> False, split -> None with no tiebreak call; the test pins this with a stubbed rule_detail).

## Results
Base facts first. 68% of the gold is non-settling, so a judge that always refuses agrees with the gold 68% [60-76]. The LIVE panel's own verdicts (closure = confirmed, refuted = refused) agree with the gold on 45% [36-54], kappa -0.10: of the 60 closures 16 are gold-S (27% [17-39]); of the 60 refusals 22 are gold-S (37% [26-49]). On the 84 items the reader marked sure the confirmations are gold-S 3/42 (7% [2-19]) against 8/42 (19%) of the refusals. Refusals decided by an agreed False/False are gold-S 11/35 (31%); those decided by the granite tiebreak 11/25 (44%), consistent with F-3639 (the granite is a near-constant on this key).

Single judge falcon3:7b, all 120 pairs per variant (k/n, Wilson 95%):
| variant | agree w/ gold | kappa | pass rate | false-keep | false-reject | of 60 closures still passed | of 60 refuted passed |
|---|---|---|---|---|---|---|---|
| V0 live | 62% (75/120) [54-71] | 0.26 | 52% | 43% (35/82) | 26% (10/38) | 65% | 40% |
| V1 no-prefix | 61% (73/120) [52-69] | 0.24 | 54% | 45% (37/82) | 26% (10/38) | 65% | 43% |
| V2 +events | 67% (80/120) [58-74] | 0.34 | 52% | 39% (32/82) | 21% (8/38) | 58% | 45% |
| V3 both | not run | | | | | | |

Paired against V0: V1 flips 6 rulings (2 pass->fail, 1 of them right; 4 fail->pass, 1 right); V2 flips 25 (13 pass->fail, 10 right; 12 fail->pass, 5 right): 15 flips toward the gold and 10 away, net +5 of 120, not distinguishable from noise (McNemar two-sided p about 0.4).

gemma4:12b: V0 on all 120 = 62% agree, kappa 0.22, pass 44%, closures passed 62%, refuted passed 27%. V2 on 76 of 120 pairs (stopped when the box was shared) = 55% agree, kappa 0.13, false-keep 49%: worse than its V0, paired flips 4 pass->fail (2 right) and 11 fail->pass (2 right). V1 and V3 not run on gemma.

Composed panel (gemma + falcon, no tiebreak): V0 agree 67% (59/88) with 32 of 120 splits returning no verdict, kappa 0.33; V2 67% (32/48), 28 splits, on the pairs both hubs finished. A panel that abstains on a quarter to a third of items and still sits at the 68% always-refuse line is not adding signal.

Cost: the system prompt is fixed; the user block grows from about 214 to about 369 prompt tokens with V2 (+72%) and does not change with V1. Wall clock per ruling on falcon was 12.9 to 20 s with the hubs shared, so the difference is lost in contention noise; gemma 38 s (V0) to 49 s (V2). At the live rate of at most a few rulings per cycle the extra tokens are negligible; the real price of V2 is a schema dependency (member_event_ids must resolve to shadow rows at judge time, and for 1262 of 1869 historic rulings the tension record no longer exists).

## Reading
1. The prefix is irrelevant. Removing 'unresolved:' moves nothing (61% vs 62%, kappa 0.24 vs 0.26). F-3750's suspicion that the fossil prefix harms the judge is not supported; it only wastes tokens.
2. Showing the actual conflict (V2) gives falcon a small, non-significant lift (62% to 67%, kappa 0.26 to 0.34) and hurts gemma on the part that ran. No variant beats the 68% always-refuse baseline. The judge is not failing for lack of input alone.
3. The closures are worse than F-3750's first read: 27% of a random 60 settle by this reader (3 of 42 on sure items), 73% restate or are unrelated. Half of all 229 closing thoughts (115) match the ad hoc regex mottainai|thyme|rain|rusted trap (a one-off count, not in the scripts); of the 60 sampled, 33 do and only 9 of those settle anything. 13 of the 229 closures are reading-event or library-event tensions ('reading X', 'finished the book', 'asking the library') where the closing thought is the same event restated; the exception is 'finished the book', which is closed correctly by actually reaching for a new book.
4. The 'refuted' side is not clean either: 37% of the panel's refusals read as settlements. The live panel's refusals and confirmations are nearly uncorrelated with a blind reader on this sample (kappa -0.10). Two local judges re-ruling the same refuted thoughts pass 27% (gemma) to 40% (falcon) of them, so the panel verdict on these tensions is close to a coin that leans on which family happens to answer.

## Caveats (read before acting on any number)
1. One labeller, 36 of 120 items unsure (13 of the 16 gold-S closures are unsure). The label scheme counts reframings and decisions as S, so a stricter reader would shrink S further and a looser one would grow it. Nothing here was labelled by the founder or by another model family. The V2 block shows the labeller's own evidence (the member events), which can only flatter V2.
2. Single judges, not the live panel. Live JUDGE_1 is Mixtral on Ramses and the tiebreak is Granite on Ramses; neither was called. Absolute pass rates are not comparable to the live 238 confirmations in 1869 rulings.
3. The refuted set is a join reconstruction on 23% of historic rulings (survivor-biased toward kept tensions); its thought text and similarity use final, not live, centroids.
4. V3 was not run for either judge, V1 not for gemma, V2 for gemma on 76 of 120. Hubs were shared with another chain's load; per-call seconds are not a hub benchmark.
5. Strong finding, weak instrument: the data say 'the judge does not separate settlements from restatements better than refusing everything' and 'richer input does not obviously fix it'. They do not say what would.

## Recommendation (nothing applied)
Do not change core/tension_ledger.py on this evidence: neither the prefix strip nor the event block clears noise. If the closure rate matters (each False closure drains contradiction pressure and marks member shadow events resolved), the cheaper lever is upstream of the judge, e.g. a template-thought guard (the same grounding paragraph closing unrelated tensions) or exempting reading-event labels. Both are spawned as follow-up jobs; the second labelling of this blind sheet and the full-panel/V3 completion are lab jobs.
