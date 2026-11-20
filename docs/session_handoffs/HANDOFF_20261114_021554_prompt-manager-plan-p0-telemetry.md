# Prompt manager: plan staged and audited, P0 provenance telemetry built

## Session timing
- **Session started:** 2026-11-14 00:22:23 UTC
- **Last message before wrap:** 2026-11-14 02:15:53 UTC
- **Wrapped:** 2026-11-14 02:15:54 UTC

## Summary
The founder asked about a prompt manager (T-0131); they put the LLM-writes-prompts half on hold and asked for the scripted side. This session staged `docs/staged/prompt_manager.md`, took it through two outside audits (Gemini, GPT), ruled six decisions (D-0769 to D-0774), then built and tested the P0 observe-only telemetry and re-ran the D-0368 vocabulary table. Two commits, `44be657b` and `2d87455d`; nothing is live until Du restarts.

## Decisions
All ruled by travis in chat on 2026-11-14, each as approval of Claude's recommendation:
- D-0769 variant authorship: Claude may draft structural/factual wording; a semantic reviewer checks; Travis authors or approves anything touching affect, attention, identity or the Travis branch. The receiving model never certifies equivalence.
- D-0770 registry integration: sibling script `scripts/_test_prompt_table_orphans.py` for P0/P1, wired into `prompt_registry.py check` after the P1 golden test passes. The registry-skill extension is skill_manager suggestion S-0325.
- D-0771 run P0 now (observe-only) and re-ask pools or replacement only on its result.
- D-0772 freeze the idle wrapper head and tail until a replay shows a change safe and useful.
- D-0773 the Table is a new `core/prompt_lines.py`, referenced from the registry.
- D-0774 the offline LLM prompt proposer is a separate future plan, not a commitment of this one.
- Clarification, not a ruling: D-0368's "same-day opener reuse under 30%" is the 4-word metric (travis, in chat); recorded as F-4671. D-0368's own text is unchanged.

## Builds
- P0 telemetry, built in a throwaway worktree, re-run in the shared tree, committed in `44be657b`, restart-gated: `core/prompt_budget.py` (`_provenance` writes one compact row per idle assembly to `data/prompt_provenance.jsonl`; hashes, 48-char labels, lane, pool picks; rotates at 10 MB) and `core/phrasing.py` (a pick ring plus `drain_picks`). Test `scripts/_test_prompt_manager_p0_provenance.py` passes, as do the J-2933, J-2941 and J-3223 tests. `vary()` selection was proven identical to the old algorithm over 300 seeded draws. Overhead measured on the dev machine: +0.27 ms per assembly, about 692 bytes per row, about 2.2 MB a week.
- Baseline script `scripts/prompt_manager_p0_baseline.py` and its report `docs/lab/prompt_manager_p0_baseline_2026-11-14.md` (vocabulary-by-week table plus a change ledger of restarts and commits).
- The plan doc is v2 with P0 status in section 10b, committed in `44be657b` and `2d87455d`. The research table and the audit-round-1 table were moved out to `docs/reviews/prompt_manager_research_2026-11-14.md` and `docs/reviews/prompt_manager_audit_round1_2026-11-14.md` to stay under the 40 KB plan cap.

## Fixes
- Corrected the plan's earlier claim that no phrasing pools exist and that the /quit farewell is the only rotation. `core/phrasing.py` `vary()` (since July) has six call sites in the main tree (F-4664).

## Findings
- F-4664 (verified): phrasing pools already exist and are live; F-1927's "no pools" counted `random.choice` inside the node file only. Picks were not logged anywhere before P0.
- F-4665 (verified): D-0368 re-measure. The reconstructed regex families match F-1927's published weeks 1-2 within about 1-2 points. A+E has been live since the 2026-10-09 08:36:57 boot. Frustration is under 15% only in the last two weeks (17.6% and 17.1% in the weeks of 10-24 and 10-31). 4-word opener reuse is 27-29% now but was 32% and 34% in the weeks of 10-10 and 10-17; the 3-word figure is 45-58% throughout.
- F-4666 (verified): circling vocabulary vanished on 09-29 (21% to 1%), ten days before A+E, so A+E cannot be credited. Which of the two 09-28 restarts did it is not isolated.
- F-4667 (guessing): the "anchor" idiom fell from about 25% to about 6% after the 11-07 20:33 boot, which made J-3223/D-0612's pooled concern-lead rewording live. Timing only; J-2887/F-4375 found no prompt text seeds "anchor". Spawned J-3992 as a hot-lane replay test.
- F-4671 (verified): the 30% threshold is the 4-word metric.
- The idle wrapper tail "What moves in you now? One quiet thought." is load-bearing for output schema (the condensed-twin replay in `core/condensed_thought.py`: 26 of 60 replies followed the live schema with it, 0 of 40 without), which is why D-0772 freezes it.
- Both auditors approved P0, approved P1 conditionally, and held pools. Disagreement: Gemini said n-gram proxies resist Goodharting; the plan follows GPT, who called them diagnostics only. Outside reviews are inputs, not rulings.
- The web research behind the plan came mostly through search summaries, not the primary papers. It is a lead list, not a verified review (plan section 5, and the research review doc).

## Open
1. Arm the P0 telemetry: it takes effect at Du's next restart. After about a week, read `data/prompt_provenance.jsonl` and check the rows are well-formed and pool picks appear. Not blocked; next action is the restart itself.
2. P1 (`core/prompt_lines.py`, byte-identical refactor, golden test over the complete request payload). Blocked on D-0633 (the condensed-twin prompt fix settling, with its exact bytes recorded). The execution fingerprint (model digest, sampling parameters) belongs here because those are set at the call site in `nodes/inner_monologue_node.py`.
3. J-3992 (open lab job): did the J-3223 concern-lead rewording cause the 11-07 anchor drop? Next action: pick it up in a throwaway worktree with a hash canary.
4. J-2933 and J-2941 (full-prompt capture) are still `in_progress`; P2a replay wants their full prompts.
5. Telemetry scope (a seventh question in plan section 11, not filed as a decision): Level 1 on the idle station only until overhead is measured on the real lanes. Next action: a founder call, or file it with `/decide open`.
6. S-0325 (skill-manager suggestion): add a Table-consistency section to the registry `check` once P1 is verified.

## Warnings
- The telemetry is committed but not live; it will only write once Du restarts. The shared tree's `nodes/inner_monologue_node.py` is edited by other (layered goals) work; P1 must be built in a throwaway worktree, never with `git stash`/`reset`/`checkout`/`restore` in the shared tree.
- Left uncommitted on purpose because they belong to other sessions: `docs/ideas.jsonl`, `docs/reviews/plan_files_evidence_audit.md`, `docs/staged/maths_of_mind_atlas.md`, `docs/reviews/affect_chain_2026-11-14.md`, its handoff, the mp3 and the two `.lock` files. The ledger files committed in `44be657b` and `2d87455d` are shared and may contain other sessions' appended rows.
- The session-events rollup missed S-0325 because the skill suggestion was logged without `--session`.
- Gap: the P0 overhead number is from this dev machine, not the Ramses or Threadripper lanes. [INFERRED] the telemetry cost is negligible against multi-second model calls, but it has not been measured in the live process.

## Pointers
- Plan: `docs/staged/prompt_manager.md` (sections 6 to 8 for the design, 10b for P0 status, 11 for the decision table).
- Reviews: `docs/reviews/prompt_manager_audit_round1_2026-11-14.md`, `docs/reviews/prompt_manager_research_2026-11-14.md`; GPT's full audit is at `C:\AISaves\# Prompt Manager — independent crit.txt`.
- Baseline: `docs/lab/prompt_manager_p0_baseline_2026-11-14.md` via `scripts/prompt_manager_p0_baseline.py`.
- Code: `core/phrasing.py`, `core/prompt_budget.py`, `core/concerns.py:276` (`anchor_lead_pool`), `nodes/inner_monologue_node.py:4071`; test `scripts/_test_prompt_manager_p0_provenance.py`.
- Ledgers: D-0769 to D-0774, D-0368, F-4664 to F-4667, F-4671, F-1927, J-3992, S-0325, T-0131, I-0073.
