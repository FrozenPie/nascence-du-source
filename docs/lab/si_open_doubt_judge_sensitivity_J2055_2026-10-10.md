# J-2055 part 1: judge sensitivity on generated-style thoughts (2026-10-10)

Question (F-2669): J-2054 scored the open-doubt cup 0/30 engaged with the J-2052 absolute panel judge (engaged = mixtral AND falcon >= 4),
and the judge had given essentially no 4-5 to any generated thought. Is that null informative, i.e. can this judge see engagement in a
GENERATED-style thought?

Method: 20 plain baseline thoughts from data/lab/J-2031/gens.jsonl (gemma4:12b, one per fire; row 3 sample 1 because sample 0 was ERR; rows 1/2 and
4/3 share a cycle id so items are keyed row.sample). The session model wrote one minimally edited variant of each (same voice, mean length 285 vs 294
chars) that explicitly takes up the fire's doubt. Third arm: the same edited text scored against ANOTHER fire's reflection (edited_mism) to check the
edit wins by taking up THIS doubt rather than by generic doubt language. J-2052 rubric imported unchanged; hubs :11438/:11440 only, one stream,
2 s pauses, temperature 0; Du was live and sharing the judge hubs. Gate written before data: edited >= 50%, plain <= 11%, edited_mism <= 11%.

Results (engaged = both judges >= 4; Wilson 95%):
- plain 0/20 (0-16.1%); mean mixtral 2.40, falcon 3.25. Both >= 3: 8/20.
- edited 18/20 = 90% (69.9-97.2%); mean mixtral 4.00, falcon 4.85. The 2 misses were mixtral 3 (rows 6.0 and 10.0).
- edited_mism 4/20 = 20% (8.1-41.6%); mean 3.05 / 3.35. The 4 (rows 9.0, 13.0, 14.0, 17.0) share avoidance/self-suspicion vocabulary with a neighbouring reflection.
- Paired: edited engaged and plain not 18; the reverse 0; edited score sum > plain 19/20; edited > edited_mism 18/20.
- Gate: edited >= 50% PASS, plain <= 11% PASS, edited_mism <= 11% FAIL (20%, but the CI contains 11%).

Reading: the judge CAN see explicit, doubt-specific engagement in generated-style text (90% sensitivity, 0% false-positive on plain), so J-2054's
cup 0/30 (Wilson upper 11.4%) is a real null for explicit engagement, not a floor effect. Limits: the edits are strong and explicit (a weak or oblique
real engagement is untested); the author of the edits also knows the rubric; the specificity floor against a wrong doubt is elevated (about 20%, n=20)
when the text carries generic self-doubt language; the cup/control texts came from gemma4:12b, not the live qwen3.5:9b.
Part 2 (live-generator replay) needs Du offline: prepared as scripts/si_open_doubt_cup_live_gen_J2055.py, not run.
Raw: data/lab/J-2055/{sens_abs.jsonl,sens_summary.json,sens_stdout.log}; script scripts/si_open_doubt_judge_sensitivity_J2055.py.
