# J-2996: does the pursuits 'advances' judge separate progress from recombined imagery? (from F-3692, P-0100)

Status: measured on a single local judge, NOT on the live three-model panel. Read-only toward Du; core/pursuits.py and core/judge_panel.py unchanged.
Data: docs/lab/J-2996_data/ (gold_pairs.jsonl, gold_labels.json, blind_sheet.txt, replay_single.shard0-2.jsonl). Scripts: scripts/j2996_pursuit_gold_build.py, _replay.py, _report.py. Test: scripts/_test_J2996_pursuit_gold.py.

## What was built
1. Gold set, 81 consecutive (prior confirmed thought -> next thought) pairs from data/pursuits_active.json, across 20+ pursuits: 60 panel-CONFIRMED pairs (the judge's exact input: pursuit question, previous confirmed thought, new thought) plus 21 not-yet-judged 'pending' items. The briefing's ~30 judge-REFUTED pairs do not survive in the file (refuted items are dropped); the 21 pending items are the nearest substitute and have no panel verdict, so they are unlabelled-by-panel by construction.
2. Blind labels (A advance / R restate-or-re-image / T tour), written from blind_sheet.txt before any replay, blind to panel verdict and source. Gold: 20 A, 35 R, 26 T. 12 of 81 flagged unsure by the labeller (10 of the 20 A are unsure).
3. Replay of all 81 pairs through four prompts, 324 rulings (infra errors retried then excluded; 5 rulings have no verdict, 4 in V0 and 1 in V1, and are left out of the rates):
   - V0 live: exact core/pursuits.py judge_pending prompt.
   - V1 no_image: V0 + 'a new image, example, object or sensory detail on the same theme is NOT an advance'.
   - V2 last3: judge sees the pursuit's last 3 confirmed thoughts, not only the previous one.
   - V3 both.

## Results (one judge, gemma4:12b at :11439, called through judge_panel._ask; numbers are k/n with Wilson 95%)
| variant | pass rate | agree w/ gold | kappa | false-keep (gold non-advance passed) | false-reject (gold advance refused) | keep rate on the 60 confirmed pairs |
|---|---|---|---|---|---|---|
| V0 live | 65% (50/77) | 53% (41/77) [42-64] | 0.18 | 58% (33/57); restate 50%, tour 68% | 15% (3/20) | 54% (30/56) |
| V1 no_image | 39% (31/80) | 69% (55/80) [58-78] | 0.30 | 30% (18/60); restate 29%, tour 31% | 35% (7/20) | 27% (16/59) |
| V2 last3 | 60% (49/81) | 52% (42/81) [41-62] | 0.13 | 56% (34/61); restate 40%, tour 77% | 25% (5/20) | 48% (29/60) |
| V3 both | 44% (36/81) | 63% (51/81) [52-73] | 0.22 | 38% (23/61); restate 26%, tour 54% | 35% (7/20) | 32% (19/60) |

Paired change vs V0: V1 flips 20 pass->fail (16 correct, 4 wrong), 0 fail->pass; V2 flips 9 (7/2) and 5 fail->pass; V3 flips 16 (12/4).

## Reading
- The live prompt does NOT separate progress from recombined imagery on this gold set. V0 agreement with the gold is 53% (kappa 0.18), and it passes 58% of gold non-advances, including 68% of 'tour' pairs and 50% of 'restate' pairs. It does refuse 15% of gold advances, so it is not blind, just close to indifferent. 95% of the 21 pending items pass it.
- The image rule (V1) is the one variant that moves things: agreement 53% -> 69%, false-keeps halved (58% -> 30%). Price: false-rejects 15% -> 35% (7/20; 4 of the 7 are labeller-unsure) and it would keep only 27% of the currently confirmed advances. Among the 10 labeller-SURE gold advances V0 keeps 9, V1 7, V2 7, V3 6.
- Last-3 comparison (V2) alone does nothing useful: agreement 52%, tour false-keeps rise to 77%. It adds cost without discrimination on this model.
- Blind labels classify only 15 of the 60 panel-confirmed pairs (25%) as genuine advances; 26 are restatements and 19 tours. That is one labeller's reading, but it agrees in direction with F-3692 (the confirmed trains are largely recombined imagery).

## Caveats (read before acting on any number)
1. Single judge, not the panel. The live panel (mixtral :11438 + falcon3 + granite :11437 tiebreak) could not be used: Ramses is off limits and falcon3/yi were saturated at ~220 s per call, so a panel ruling cost ~7 min. gemma4:12b alone passes only 54% of the 60 pairs the live panel CONFIRMED, so it is a stricter and different judge; absolute pass rates must not be compared to the live 82%. Variant differences on one fixed judge are the valid comparison.
2. Circularity in V1: the labeller's own R criterion includes 'a new image/example/sensory detail with no new claim', which is exactly the sentence V1 adds. V1's agreement lead is partly the labels and the prompt sharing a definition. A labeller who did not write that criterion is needed before V1 is promoted.
3. Single labeller (Claude), 12 unsure items, only 20 gold advances: the false-reject rates have wide intervals (V1 7/20 = 35%, CI 18-57%). The founder or a second session has not yet labelled.
4. The extra unlabelled confirmed sample (--extra) was not run; the keep rate rests on the 60 labelled confirmed pairs.

## Recommendation (nothing applied)
Do not change the prompt on this evidence alone. If a stricter advances judge is wanted, V1's sentence is the only candidate worth the live panel test, but only after (a) an independent second labelling of the 81 pairs and (b) the panel-mode replay on the same pairs. Spawned as follow-up jobs (see the ledger).
