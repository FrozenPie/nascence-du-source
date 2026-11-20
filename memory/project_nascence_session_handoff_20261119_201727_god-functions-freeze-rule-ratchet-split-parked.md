---
name: project-nascence-session-handoff-20261119-201727-god-functions-freeze-rule-ratchet-split-parked
description: 11-20 god functions (_think 3,598 lines, _run_cycle_impl 1,525) measured; split of existing code PARKED by founder (D-0877); freeze rule in CLAUDE.md plus size ratchet adopted (D-0878); bug count F-5127 about 14% structure-caused; equivalence harness J-4424 ready, not built.
metadata:
  type: project
  originSessionId: 8ef072cf-6c10-40e9-8c96-f0def8dfa538
  sessionStarted: 2026-11-19 08:54:27 UTC
  modified: 2026-11-19T20:26:23.576Z
---

The founder asked whether Du's large scripts should be split into modules. The problem turned out to be two functions, not file size. A split plan was drafted and then parked as too risky for the evidence (D-0877); instead new behaviour must go in helper modules under `nodes/idle_thought/` and `scripts/function_size_ratchet.py check` must stay green (D-0878, rule in the project CLAUDE.md, run by `/plan-maintain` step 7e). The bug count (F-5127, inferred) found 9 of 69 past defects structure-caused, all in `_think`, all silent.

Full detail: `C:\Nascence\docs\session_handoffs\HANDOFF_20261119_201727_god-functions-freeze-rule-ratchet-split-parked.md`. Plan: `C:\Nascence\docs\staged\god_function_split.md`. Next work is J-4424, the standing idle-thought equivalence harness.

**How to apply:** do not propose moving existing blocks out of `_think` or `_run_cycle_impl` unless D-0877's defeater is met; the founder judged it a massive operation with real danger. Related: [[feedback_erosion_of_foundations]], [[project_nascence_inner_monologue]], [[project_udms_feedback_loop]], [[project_nascence_prompt_manager]].
