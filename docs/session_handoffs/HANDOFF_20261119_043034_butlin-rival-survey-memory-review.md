# Rival-systems survey, Butlin-Long mapping and memory review

## Session timing
- **Session started:** 2026-11-19 00:56:27 UTC
- **Last message before wrap:** 2026-11-19 04:30:33 UTC
- **Wrapped:** 2026-11-19 04:30:34 UTC

## Summary
The founder asked for a step back: survey comparable projects and see what they have that Du lacks. That became a Butlin-Long 14-indicator comparison of Du against eight outside systems, then a full memory review. The memory review found Du's cold storage is a hard wall, not a graded forgetting curve. It ended with a plan, thirteen jobs, a plan-maintain pass and one commit (5ffb41bf).

## Decisions
- Founder (in chat, 2026-11-19) delegated the choice of the first re-warming level to Claude, to be checked later. Claude chose: partial and temporary, shadow only. A cold or chaptered row surfaced by the associative trail AND labelled used-in-next-thought (either F-4273 label) gets a would-warm record for 7 days, logged only. This is recorded in section 6 of the plan as Claude's choice under founder delegation, NOT as a founder ruling. No `/decide` entry was opened.
- Founder: B1 (attention control for the bandwidth arm) and B2 (second broadcast consumer) are shadow only to start.
- Founder corrected an overstatement: Du was not "built around" the Butlin test. Verified: `docs/plans/the_consciousness_program.md` is dated 2026-07-03 and uses Butlin as one of ten research threads; only AST-1 (attention schema) and PP-1 (protoself homeostasis) were built from it.

## Builds
Nothing was built in code. No behaviour change. Deliverables are documents, ledger rows and jobs:
- `docs/reviews/butlin_long_mapping_2026-11-19.md` (Du's 14-row table, comparison with eight systems, memory comparison inputs).
- `docs/staged/memory_review_adoption.md` (plan; ROADMAP entry added under "MEMORY REVIEW ADOPTION").
- Findings: F-5119 (Du has no indicator MET-LIVE; scorecard in the consciousness program overstates GWT-1/2/3 and HOT-1; inferred), F-5120 (Du 12-13 partial-or-better vs Generative Agents 7, Project Sid 6; inferred), F-5121 (2026 systems: Global Workspace Agents 6, Letta 5, Anthropic 4, CogniPair 4, SCM 1, Microsoft 0; inferred), F-5122 (cold storage hard wall; verified).
- Jobs: J-4410 (shadow per-edit importance log), J-4411 (audit the gist-faithfulness verifier), J-4412 (keyword channel shadow A/B, lab), J-4414 (cold-trail ablation, lab, urgency 4), J-4415 (shadow skill-recipe log), J-4418 (trace a critic rejection to a later answer), J-4419 (restate Butlin scorecard, needs founder OK), J-4420 (shadow re-warming log), J-4421 (log what AST_CONTROL would do), J-4422 (log what a second broadcast consumer would receive). Closed as superseded: J-4413, J-4416, J-4417.
- plan-maintain run (exit 0), prompt registry check OK. Commit 5ffb41bf by explicit paths.

## Findings
- Cold storage (verified, F-5122): `retrieve()` excludes cold rows entirely (`core/memory/store.py:1420`, `:2199`). The only "harder but possible" route is the associative trail, which needs activation 0.22 for a cold or chaptered row against 0.13 for a warm one (`core/associative_recall.py:45`, `:207`). Recalling a cold row never re-warms it: `cold=0` is written only by `memory_lint`, `uncold_all` and a notes-reversal helper. The side door is used: walled rows were about 24% of trail slots.
- [INFERRED] Counts from a read-only subagent DB query, not re-run by me: 188,174 memory rows, 87,203 cold, about 65% of cold rows have no gist link, importance is not in the main retrieval formula, DB at data/memory/nascence.db (data/nascence.db is a 0-byte file).
- No memory-versus-baseline task test exists for Du. F-0424 (state-weighted recall vs cosine, n=84) is a null; F-4649 (power-law re-use) measures human-likeness of a statistic, not benefit.
- Rivals' lead is edit history and the habit of baseline tests (Anthropic: immutable versions, dreaming writes a new store). Their headline gains are mostly against no-memory or full-context baselines on chat-QA benchmarks, vendor-run, with conflicting numbers; Microsoft's own ablation showed consolidation did not beat raw retrieval (71.2 vs 70.1). Du leads on horizon (174 days live) and memory design depth.
- [INFERRED] All Butlin scores come from separate subagents using one strict rubric; Du from code, the others from papers/docs read through summarising fetchers (the Project Sid repo has no architecture code). One rater family, asymmetric evidence. The earlier "scorecard overstated" wording was too hard: the disagreement is mostly how strictly to read each indicator.
- Skills (partial): `core/procedures.py` is a live evidence-graded ledger (67 entries) but Du cannot author, compose or semantically retrieve an executable skill. Memory edits (partial): importance changes (`downscale_episodic`, `replay_strengthen`, `dream_fade`) are in place with counts only; boot-time sqlite snapshots in data/backups; `data/` is gitignored.
- Process note: F-5119 was recorded without `--session`, so it does not appear in this session's rollup. Two `findings_log.py record` attempts hit a transient PermissionError on `docs/findings.jsonl` and were retried once each; the ledger shows single entries (checked).

## Open
1. Re-warming first level is Claude's choice, not a founder ruling. Next action: after J-4420's shadow log and J-4414's result, founder reviews and rules on promotion; consider opening a `/decide` entry with a defeater if it goes live.
2. J-4414 (cold-trail ablation) is the highest-urgency evidence job. Next action: run it in a throwaway worktree with a hash canary on live stores (see memory note on lab_env sys.path leaks).
3. J-4411: the gist-faithfulness verifier passed 3 of 13 bad gists (F-3551, F-4936); episodic gist demotion stays paused (D-0564). Next action: larger stratified hand-check sample.
4. J-4419: restating `the_consciousness_program.md` section 4 to the stricter reading needs founder OK (their document).
5. The Anthropic engineering-post numbers were read via a summariser; verify against the page before quoting in a decision doc.
6. Not done: scoring other systems (Dreamer-style world models, Neuro-sama-style persona agents, Mem0/Zep/Hindsight on Butlin) and a head-to-head memory benchmark.

## Warnings
- Do not repeat "Du is SOTA/frontier" or "memory is far ahead" without these caveats; the founder, GPT and Gemini have said frontier, but nothing here measured it.
- Untracked and left alone: `docs/06. Just the Way You Are.mp3`, `docs/findings.jsonl.lock`, `docs/prompt_registry.jsonl.lock`, `docs/ledger_backups_20261117/`.
- The MEMORY.md index was trimmed to fit its size cap: 22 older 11-01..11-17 entries moved verbatim into `reference_nascence_spine_archive_index.md`.
- J-4412 and J-4414 are lab jobs requiring isolation; never touch live stores.
- Everything here is restart-gated and shadow only; nothing was applied to Du.

## Pointers
- `C:\Nascence\docs\staged\memory_review_adoption.md` (plan, section 6 has the rulings)
- `C:\Nascence\docs\reviews\butlin_long_mapping_2026-11-19.md`
- `C:\Nascence\docs\plans\the_consciousness_program.md` (section 4 scorecard, line 308)
- `core/memory/store.py:1420`, `core/associative_recall.py:45`, `core/memory_levels.py:96`
- Findings F-5119..F-5122; jobs J-4410..J-4422; thought T-0149; commit 5ffb41bf
