# God functions: measured, split parked, freeze rule and size ratchet adopted

## Session timing
- **Session started:** 2026-11-19 08:54:27 UTC
- **Last message before wrap:** 2026-11-19 20:17:27 UTC
- **Wrapped:** 2026-11-19 20:17:27 UTC

## Summary
The founder asked whether Du's large scripts should be split into modules, as the pantry app is. Measurement showed the problem is two functions, `InnerMonologueNode._think` (3,598 lines) and `Orchestrator._run_cycle_impl` (1,525), not file size in general. A split plan was drafted, then parked on the founder's direction as too risky for the evidence; a freeze rule and a size ratchet were adopted instead, and a standing equivalence harness is queued.

## Decisions
- **D-0877 (ruled, travis): not as framed.** It asked for a go on Phase 0 of the split. The founder called the split "a massive operation, with a real risk of danger" and asked whether it is worth doing at all. The split of existing code is parked. Defeater: revisit if the bug count shows structure-caused bugs are a material share, or the standing harness keeps catching the same class of mistake. Recorded by Claude from the founder's chat words; the founder was asked to check the wording and did not object.
- **D-0878 (ruled, travis): go on both.** (a) Build the equivalence harness for the idle thought as a standing regression test, new script only. (b) Adopt the freeze rule in CLAUDE.md with a function-size ratchet run by `/plan-maintain`. Defeater: the ratchet being accepted past routinely without a real reason, the freeze rule blocking a change that genuinely must live inside the function, or the harness proving impossible to make deterministic.

## Builds
- **Freeze rule in `CLAUDE.md`** (new section "`_think` and `_run_cycle_impl` are frozen"). A new idle-thought seed part, post-thought step or cycle stage is a function in its own module under `nodes/idle_thought/` (named `seed_part_*`, `after_thought_*` or `attempt_*`), called from the big function by one line. Existing blocks are not moved.
- **`scripts/function_size_ratchet.py`** with `docs/function_size_baseline.json`. `check` exits 1 if a watched function is longer than its baseline or cannot be found; `accept --why "..."` records growth that has to stay, with the reason kept in the baseline file's history; `show` prints sizes and the accept log. Tested on a throwaway tree in the scratchpad: red on growth and on a renamed function, green on no change and on shrinking. Baseline recorded: `_think` 3,598, `_run_cycle_impl` 1,525.
- **`/plan-maintain` step 7e** runs the ratchet check (edit to `C:\Users\USER\.claude\skills\plan-maintain\plan_maintain.py`, outside the repo, so not in git). A full pass was run at wrap and step 7e printed green.
- **Plan `docs/staged/god_function_split.md`** (T-0153 promoted to it). Section 0 is the active track (freeze, harness, measure). Sections 3, 5, 6 and 8 hold the split design, marked PARKED, as the design of record.
- **`docs/reviews/udms_mcp_wishlist_2026-11-19.md`**: ten improvements to the UDMS MCP tools and an eleven-item wish list, written for the UDMS window at the founder's request.
- **Commit `5fd6add3`** holds all of the above plus the ledgers.

## Findings
- **F-5125 (verified): where the size is.** 1,944 tracked Python files, 441k lines, 44 over 1,000 lines. `_think` has 278 assigned locals, 208 try blocks, nesting depth 9 and 45 `seed_parts.append` sites; it sits as 1,411 lines before a `for attempt in range(2):` retry loop of 1,337 lines, with 850 after. `nodes/inner_monologue_node.py` had 97 commits in the last 30 days. Both functions grew about 6% in 13 days against F-4191. The other large files (`core/lane2.py`, `core/sensorium.py`, `core/memory/store.py`, `core/cat.py`) are many moderate functions and were left alone.
- **F-5126 (verified): UDMS baseline and corrected separability.** UDMS profile: `_think` complexity 548, 444 try/except nodes, 94 `self` writes; `_run_cycle_impl` complexity 181, 8 `self` writes. Structural outlier score for `inner_monologue_node.py` is 18.14, the highest in the repo. The first separability estimate (115 of 123 top-level blocks) was too generous: counting `self` writes and return/continue/break, 74 are clean. All seed assembly is before the retry loop.
- **F-5127 (inferred): the bug count, J-4423.** Of 69 classified past defects in the two functions, 9 were caused by structure, 54 by logic, 6 unclear: about 14%, with a sensitivity range of 8% to 26%. All 9 are in `_think`, all were silent, and `_run_cycle_impl` has none. Seven of the nine are the kind an equivalence harness would catch on the day of the edit (a prompt line missing or doubled); the missing `import re` (F-0758) is the kind a static undefined-name check catches. The classification was done by a subagent; this session checked the cited commits and findings for the 9 structure items and did not re-classify the 54 logic items. Table: `docs/reviews/god_function_bug_count_2026-11-20.md`.
- **Why the split was parked.** The benefit goes to sessions, not to Du. "Byte-identical" can only be proven for blocks the harness can make fire offline, and Du's code fails open, so a dropped prompt line in an unfired block would be silent. The pre-loop section of `_think` is not pure: 15 awaits, 15 time reads, 5 random draws and 14 consume-once style calls.
- **Existing harness.** `scripts/test_idle_offloop_equivalence.py` (J-1918 / F-2547) already drives real `_think()` calls offline with frozen time, a blocked network and a stubbed model call. It is the starting point for J-4424.
- **From the UDMS window** (reported by that session, not rechecked here): the dossier reads the oldest 450 of 3,620 commits, so its co-change evidence for these files is two months old until the newest-450 switch (D-0829, D-0846, after J-3781); 200 line-number citations in 71 docs point into `inner_monologue_node.py`; none of the function-scoped imports in the two files would close an import cycle if hoisted.

## Open
1. **J-4424, build the equivalence harness** (`scripts/think_equivalence.py`). Ready, build, isolation required. Not started. Next action: a fresh session reads `scripts/test_idle_offloop_equivalence.py` and the job briefing, then builds it; old-versus-old must compare identical and the negative control must fail before it is trusted.
2. **The split itself** is parked under D-0877. Nothing to do unless its defeater is met. [INFERRED] On F-5127 the case for ever splitting `_run_cycle_impl` is close to nil; the founder has not ruled that it is dropped.
3. **First real ratchet read.** The ratchet has only been checked against an unchanged tree. Next action: at the next `/plan-maintain` pass after real edits to the two files, read step 7e and `function_size_ratchet.py show` to see whether growth is being accepted with real reasons.
4. **[OPEN] Static undefined-name check** on the two files (the F-0758 class). Discussed as a cheap mitigation and listed in the plan's section 4.3, but no job is filed for it as a standing check. It would be resolved by the founder asking for it or by folding it into J-4424.
5. **Prompt registry note, pre-existing:** `prompt_registry.py check` exits OK but prints a CALLERS note that P-0097 is DEAD yet has a caller at `core/deliberative_judge.py:127`. Not from this session and not investigated.

## Warnings
- **The ratchet adds friction by design.** Any growth in `_think` or `_run_cycle_impl`, even a three-line fix inside an existing block, turns `function_size_ratchet.py check` red until it is recorded with `accept --why`. A job-run that edits those functions will meet this. Do not hand-edit `docs/function_size_baseline.json`.
- **`nodes/idle_thought/` does not exist yet.** The first new seed part written under the freeze rule creates it. The helper needs a distinctive name because UDMS hygiene matches by bare name (F-4189).
- **Moving a `seed_parts.append` out of `nodes/inner_monologue_node.py` will change the prompt registry's SEEDS guard count.** Not yet read how the guard counts; check `prompt_registry.py check` after the first such helper.
- **A file not from this session is modified in the tree:** `docs/session_handoffs/HANDOFF_20261105_085628_argon-math-audit-verification.md`. It was left out of this session's commits.
- **The UDMS before-snapshot** at `C:\UDMS\data\split_metrics\before.json` (commit `5bd2efce`) is only useful if the split reopens, and would need retaking then.
- **F-5127 is inferred, not verified.** Quote it as "about 14%, range 8% to 26%", not as a hard number.

## Pointers
- `docs/staged/god_function_split.md`: the plan; section 0 is what is live.
- `docs/reviews/god_function_bug_count_2026-11-20.md`: the bug-count table.
- `docs/reviews/udms_mcp_wishlist_2026-11-19.md`: the UDMS write-up.
- `scripts/function_size_ratchet.py`, `docs/function_size_baseline.json`: the ratchet.
- `scripts/test_idle_offloop_equivalence.py`: the harness J-4424 starts from.
- `C:\UDMS\docs\handoffs\udms_for_god_function_split_2026-11-19.md` and `C:\UDMS\scripts\split_metrics.py`: the UDMS side.
- Ledger ids: T-0153, F-5125, F-5126, F-5127, D-0877, D-0878, J-4423 (done), J-4424 (ready).
