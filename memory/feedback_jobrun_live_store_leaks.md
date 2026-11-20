---
name: feedback-jobrun-live-store-leaks
description: 10-04: two test-script leaks into Du's REAL data/ files (satisfaction, prediction_error, shadow_integrity) while Du was down; lab_env.py put C:/Nascence at sys.path[0] so worktree runs loaded the shared tree's core (fixed); verify with a before/after hash canary from a throwaway worktree; repair = truncate + replay-validated state rebuild
metadata:
  node_type: memory
  type: feedback
  originSessionId: 2315a7b3-9526-4ef6-b6e9-5b57b923a07f
  modified: 2026-10-04T04:30:38.263Z
---

**What happened (F-2406, F-2422, F-2423):** (1) My own post-merge verification ran `scripts/exploratory_ignition_test.py` from the shared
C:\Nascence tree; `core/satisfaction.py` had unfenced `__file__`-relative paths, so 30 `frontier_born` rows + a 9.5 h decay fast-forward hit
Du's live satisfaction files. (2) At 16:49:37 a build agent's loop of tests, launched from ITS WORKTREE, wrote five more live files
(satisfaction_{log,state}, prediction_error_{log,state}, logs/shadow_integrity.jsonl) with a fake 2026-09-08 clock: `~/.claude/skills/job-queue/lab_env.py`
did `sys.path.insert(0, "C:\Nascence")` on import, so a test that imports lab_env before core loads the SHARED tree's core (live paths, and master's code
instead of the branch's). Both repaired by me with Du down. lab_env.py now APPENDS (backup `.bak_F-2423_orchestrator_20261004`;
`scripts/_test_lab_env_core_resolution.py`); `core/satisfaction.py` fenced (J-1783); prediction_error fence J-1799, buses fence J-1797, audit J-1786.

**Why it matters:** "run the tests from your worktree" was NOT leak-proof, and an isolate()-using test from a worktree verified master, not the branch.
Any module with `__file__`-relative `data/` paths and no `profile.guard_path` writes the live file from any process that merely imports it from the
shared tree; `activate_profile`'s rebase tuple protects only a process that calls it (F-2412).

**How to apply:** (a) After every merge/verification, fingerprint the LIVE data/ top level (size + mtime_ns) before and after (scratchpad `jr_verify_generic.py`,
`jr_canary.py` hash baseline): only the HUD's `arousal_shadow.jsonl`/`hud.err.log` may change; that canary caught both leaks. (b) Run verification from a
throwaway worktree of merged HEAD (`git worktree add --detach`), never the shared tree. (c) In any test script import `core` BEFORE `lab_env` and assert
`core.__file__` is inside the tree under test. (d) Repair recipe: append-only logs → truncate to the pre-leak byte length after checking the tail and the
prefix hash; derived state (satisfaction: decay half-lives 6 h/36 h, cap 5.0) → replay the pre-leak log through the module's own rule, then replay the leaked
rows on top and require the polluted file to be reproduced EXACTLY before writing; keep backups of the polluted files; JSON state files keep their byte format
(prediction_error_state.json is indent=1 with CRLF). (e) Never write live stores from dispatched agents; leave the repair to the orchestrator.
Related: [[feedback_test_isolation_live_stores]], [[feedback_jobrun_parked_jobs_and_sweep_sizing]], [[project_nascence_20261004_jobrun_waves]].
