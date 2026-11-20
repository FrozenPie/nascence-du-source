# J-3775 pre-registration: natural-traffic check of the near-duplicate sites (J-3308 follow-up)

Written BEFORE any natural-traffic number was computed. Author: the J-3775 agent, 2026-11-16. Plan: geometry_tuple_index.

## Question
J-3308's replay universe was boundary-enriched, so its disagreement rates are an upper bound. On natural traffic (no
enrichment), how often do the lane2 repeat rule, the frontier rule and the deliberation echo guard disagree with the
decoupled judge panel?

## Design
- Sources (read only, live files opened for read): data/lane2_would_ask.jsonl, data/frontier.json, data/deliberation_log.jsonl.
- Sample: 150 target items per site, random, seed 3775, taken in log order with no enrichment.
- lane2: target wonder vs prior wonders (rows, not text-deduped) within WONDER_REPEAT_WINDOW_S (7 d) before it.
  Site verdict for the target = lane2._wonder_repeat_check lexical_repeat (max stem Jaccard >= 0.5 over the window).
- frontier: target question vs prior entries (by born) within 7 d before it. Site verdict = frontier rule (lexical
  Jaccard > 0.55 OR embedding cosine >= 0.85) against any prior in the window.
- deliberation: target row (raw, integrated). Site verdict = deliberation._too_similar(raw, integrated). Judged directly.
- Judged candidates for lane2/frontier: the 3 priors in the window with the highest embedding cosine to the target
  (plus any prior the site rule fired on, so the site's own hit is always judged). Cap 4 per target. Judging every
  prior is infeasible; the top-cosine candidates are the likeliest true duplicates, so miss-rate is a slight lower bound
  on the true miss rate (a duplicate with no embedding neighbour is not seen).
- Panel: scripts/lab_J-3308_nearduplicate_replay.py's JUDGE_Q wording, ask() and panel_label(): gemma4:12b :11439 and
  falcon3:7b :11440, yi :11442 only for ties. Local hubs only, never Ramses; threads one per hub, small sample.
- Target is "judged duplicate" if the panel says same for any judged candidate. Target is "site-flagged" per above.
- Miss = judged duplicate and not site-flagged. False alarm = site-flagged (every flagged candidate judged not same) and not judged duplicate.
  Disagreement = (miss + false alarm) / 150.

## Decision rule
- lane2 PASS: misses are at least 10 percent of judged-duplicate wonders (miss / judged_dup >= 0.10). Then a shared
  helper is worth a follow-up job. Otherwise leave lane2 alone and say so.
- frontier and delib are reported (miss rate, disagreement, Wilson 95 percent intervals); no threshold registered beyond
  J-3308's 10 percent disagreement line.
- Tie-broken or unparseable judge verdicts that stay None are excluded and counted.

## Registered deviation (frontier only, set before running)
Frontier has about 2,400 priors in a 7-day window, so 150 random targets across 155 days would need most of 22,000 entries embedded. To keep embedding load modest, frontier targets are drawn at random (seed 3775) from the most recent 28 days of born, with priors from the 7 days before each. Still unenriched natural traffic; lane2 and deliberation are drawn from the whole log.
