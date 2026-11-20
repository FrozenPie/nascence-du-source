# Needs-input reads group and labelling feasibility (2026-11-18)

## Session timing
- **Session started:** 2026-11-17 20:00:28 UTC
- **Last message before wrap:** 2026-11-17 21:24:28 UTC
- **Wrapped:** 2026-11-17 21:24:30 UTC

## Summary
Ran the "reads" group of founder-input jobs (35 candidates) in background agents, one per job, then classified 12 hand-labelling jobs and labelled six of them blind with Claude subagents. Travis answered a 12-question questionnaire, and then accepted Gemini labels plus Claude second readings in place of his own hand labels. Du was down throughout; no code changed, no flags flipped.

## Decisions
- D-0827 Curiosity pre-fire check stays in shadow until J-4110/J-4111 report (travis).
- D-0828 Peer letters: keep observing, no regenerate gate, re-read at 30 no-reply rows (travis).
- D-0829 UDMS git window: switch to newest 450 commits AFTER the J-3781 re-score (opens 11-20), pre-registered (travis).
- D-0830 Dream resolution judge kept as measurement only (travis).
- D-0831 Rewrite the 14 cat lines that name her while unseen (travis). D-0832 accuracy split into drill/verdict (travis). D-0833 tick-id stamp on co_recall (travis). D-0834 frontier archive with restore-on-re-encounter, flagged (travis). D-0835 self-voice authorship design, shadow only (travis).
- D-0836 Claude blind second readings accepted as provisional (spot-check contested items only). D-0837 voice fidelity: judge on question_flagged_share (29.5%), retire raw flagged share, observe-only (travis).
- D-0838 Model labels (Gemini and Claude) stand in for founder hand labels on all twelve labelling sheets. Provenance stays recorded as model-labelled (travis, chat).
- decide-review run at the end: 838 decisions, 0 open.

## Builds
Review file docs/reviews/needs_input_reads_2026-11-18.md (commit fd7888bb). New build jobs, all ready and restart-gated where they touch code: J-4226 UDMS doc_audit fix, J-4227 cat lines rewrite, J-4228 accuracy split, J-4229 tick-id stamp, J-4230 frontier archive (queue after J-4030 merges), J-4231 self-voice design plan. Commit 49af9478 holds ledgers, label sheets and scorers.

## Findings
- Reads: 35 jobs, 12 needed a call (all now ruled), J-3370 closed (F-5044, almanac 14/14), 22 skipped because they need Du up, Ramses or judge hubs, a code build, or a design choice. Findings F-5043..F-5053 cover the reads; F-5054..F-5069 the labelling work; F-5070..F-5075 the returned sheets.
- Class (c), founder or non-Claude only: J-3418, J-3768, J-3772, J-3908, J-4033, J-4101. Class (b), Claude labelled blind as same-family second reader: J-3400 (F-5063, 6 strict F under the 12 needed, D-0595 defeater fires), J-3717 (F-5065, kappa 0.45), J-4111 (F-5059, 13/20), J-4149 (F-5060, 75% vs 62.5%), J-4129 (F-5066, 13/16), J-4032 (F-5067, 84/111).
- Returned sheets, labelled by Gemini not Travis: J-3908 stand precision 48% (19/40, interval 33-63, 60% bar not met on point estimate, F-5070). J-3768 second reader agreement 68%, kappa 0.50, S-vs-rest 0.403, sitting at the 0.4 soft-gold line (F-5071). J-4101 25 allow/deny cells filled (F-5072). J-4033 two disagreements #50 and #41 (F-5073). J-3772 solid flags 50% real, 10 per 20 false vs the D-0361 limit of 4 per 20 (F-5074, n=12 solid). J-3418 parser reads 30 good / 30 bad (F-5075; Gemini said 28/32).
- Two blindness breaks happened and were caught: an agent opened scripts/lab_j2952_tiebreak_gold.py and J-4129's first agent read docs/lab/J-3024_labels.py. Both were redone by fresh agents.

## Open
1. D-0546 stands: model read 48%, interval straddles the 60% bar, human precision not discharged. Next: decide if n=40 is enough or whether Travis labels a 20-item half.
2. D-0361 notice checker retune: model read exceeds the defeater on 12 solid flags. Next: spawn a retune-question job or accept thin n.
3. J-3768: scripts/j3048_tension_gold_report.py has no --labels argument, so live-panel kappa and V2 lift not re-scored. Next: build job.
4. J-3418: worth-judge lab rerun needs judge hubs; travis_labels.json provenance corrected to gemini. J-3464, J-3281, J-3548 stay open with re-gates. J-3578 not_before 2026-11-20.
5. All twelve labelling jobs and the 22 skipped reads jobs remain open in the queue; none were marked done except those the rulings closed.

## Warnings
- Findings and decisions were logged with --session set to job ids, not this session's UUID, so the session-wrap rollup for this session is empty. The ledgers are the source of truth.
- Shared tree: other sessions have uncommitted edits in ideas.jsonl, plan_snapshots.jsonl, prompt_registry.jsonl, SESSION_HANDOFF.md and docs/reviews/plan_*; I did not commit them.
- Du is down. No flag was flipped and nothing restart-gated has shipped.

## Pointers
- docs/reviews/needs_input_reads_2026-11-18.md
- docs/lab/J-3253_data/, docs/lab/J-3130_data/, docs/lab/J-3048_data/blind_labels_gemini.json
- Per-job result blocks: C:\Users\USER\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes\local_20f5050b-96c1-4723-8dfb-7515dbcbd2ac\reads
