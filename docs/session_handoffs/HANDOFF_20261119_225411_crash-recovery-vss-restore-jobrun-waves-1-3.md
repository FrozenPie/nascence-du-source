# Crash recovery (state files restored from shadow copies) and three Du-down job-run waves

## Session timing
- **Session started:** 2026-11-19 20:33:43 UTC
- **Last message before wrap:** 2026-11-19 22:54:10 UTC
- **Wrapped:** 2026-11-19 22:54:11 UTC

## Summary
The computer hard-crashed at about 09:06 NZ on 2026-11-20. Du's relaunch looked hung but was a 5-minute SQLite WAL replay; the crash had zero-filled 19 state files in `data/`, which were restored from Windows shadow copies taken at 04:51. With Du kept stopped, three job-run waves (13, 10 and 8 jobs) were run through a Workflow and all builds merged to master; Du has NOT been started on any of it yet.

## Builds
All merged to master and verified on merged HEAD in a throwaway worktree (py_compile, each job's own test, `function_size_ratchet.py check` green, `prompt_registry.py check` exit 0, live `data/` fingerprint unchanged). Every one takes effect at Du's next start; none was run against a real model because the servers were kept down.

Wave 1 (doc commit `ab702ef6`, merges `02063908`..`07fb6c06`):
- J-4426 (F-5157): `core/store_persist.py` gains `write_text_durable` (tmp, fsync, keep `<name>.prev`, `os.replace`) and `read_json_durable` (WARNING "STATE FILE DAMAGED", fall back to `.prev`, "RECOVERED" / "NOT RECOVERED"). Converted: spring_ledger, opponent_process, sensorium (room_state), life, transport_manager, garden/shore/wood life.
- J-4427 (F-5156): `scripts/backup_memory.py` STATE_FILES now includes the 16 crash-wiped files (about 30 MB more per boot snapshot); empty or all-NUL sources are skipped with a warning and the newest good copy is carried forward; each snapshot gets `_backup_manifest.json`. Four `core/telemetry` readers and `hud/server.py` now survive the NUL-filled line the crash left in four jsonl logs.
- J-4142 (F-5155): think calls get `num_predict` 6000 (never below 4096) in `core/model_client.py`.
- J-4218 (F-5152): `DEEPMEM_MEMO_BYPASS_COOLDOWN = False`. J-4154 (F-5154): `_EPOCH_RETRIEVAL_FLOOR` 0.58 to 0.66. J-4223 (F-5153): `GRAND_WORK_PLAIN_PROSE = True`.
- Doc/index jobs done: J-4439, J-4273, J-4276, J-4280, J-4291 (also closed J-4190, J-4192, J-4193), J-4262, J-4438.

Wave 2 (merges `7cb58b03`..`fa098f00`):
- J-4442 (F-5166): durable save and `.prev` for cat_state, smell_field, supply, fieldcraft, world_manifest_live, transport_cause_lines, climate_state, sound_knowledge, plus the light files through `core/light_sidecar.py`.
- J-4170 (F-5160): follow-line stop-3 prompt `_CONS_SYS_V3`, flag `CONS_PROMPT_V3 = True` in `core/follow_line.py`.
- J-4174: precision gate in `core/object_hypothesis.extract`, env flag `NASCENCE_OBJHYP_PRECISION_GATE` (on).
- J-4158: stricter tension judge, `TENSION_JUDGE_STRICT` (on) in `core/schema.py`.
- J-4157: Emotion prompt "BEFORE YOU APPRAISE" paragraph removed, `EMOTION_PRIOR_IN_PROMPT = False` in `nodes/emotion_node.py`.
- J-4151: estate symbol nodes read "now: <newest tablet>" (`core/identity_estate.py`).
- J-4156: `core/recall_arm_e.py`, `RECALL_ARM_E_PROMPT` off, `RECALL_ARM_E_SHADOW` on.
- J-4410: `core/memory/edit_log.py`, `MEMORY_EDIT_LOG_MODE = "shadow"`, writes `data/memory_edit_log.jsonl`.
- J-4428: `core/stand_deed_link.py` (shadow-only judged deed link).
- J-4227 was a duplicate of J-4363; closed with a regression test only.

Wave 3 (merges `92f2fd5c`, `adead9d6`, `37f5aff3`, `c24137d4`..`552f852d`):
- J-4153 (F-5175): `nodes/idle_thought/opener_diversity.py` (`OPENER_DIVERSITY` on) plus phrasing pools with cooldown in `core/phrasing.py` and `core/wandering.py` (`WANDER_LEAD_POOL`). Idle seed parts 45 to 46; `_think` +2 lines accepted.
- J-4155: opposite-pole candidate pass in `core/guidance_learning.py`, `OPPOSITE_POLE_PASS_ENABLED = True`, `OPPOSITE_POLE_PASS_ACT = False` (log only).
- J-4420: `core/rewarm_shadow.py` re-warm shadow log (never writes cold=0); `_think` +1 line accepted (commit `3565e064`).
- J-4222: journal felt line from the day's affect trace (`core/journal.py`).
- J-4230: hardening of the existing faded-frontier archive in `core/frontier.py` (J-4371 had already built it; `NASCENCE_FRONTIER_ARCHIVE` still off).
- J-4152: tighter rehearse / self_distance cues in `core/speech_function_gauge.py` (gauge still not wired).
- J-4448: `STAND_DEED_LINK_SHADOW = True`, P-0134 set to SHADOW.

## Fixes
- Restore applied at about 10:00 NZ with Du stopped: 16 state files put back at their 04:51 contents from `data/_crash_recovery_20261120/restore_set/` (script `restore.py` in the same folder). The post-crash versions Du wrote between 09:36 and 09:57 are parked in `data/_crash_recovery_20261120/post_crash_live/`. `frontier.light.json` and `subconscious_state.light.json` were left as Du rebuilt them.
- Wave 3 merge conflict in `docs/function_size_baseline.json` (J-4153 and J-4420 each accepted a `_think` growth): resolved by keeping master's copy, finishing the merge, then re-running `function_size_ratchet.py accept` for J-4420's one line. `_think` baseline is now 3601.

## Findings
- F-5128 (verified): the crash zero-filled every `data/` state file rewritten in its last minute (19 files, 4 jsonl logs got a NUL tail) and left a 715 MB WAL. The 09:29 relaunch spent 5 min 6 s in `init_db()` replaying it with nothing logged. Du then loaded the blank files with no warning and started them from empty (spring_ledger 16.2 MB to 174 bytes). No copy existed in the repo. F-5128 was recorded without `--session`, so it is missing from this session's rollup; its text says the second scan ran at 09:38, it was about 09:37.
- F-5129 (verified): all of them were recoverable from VSS shadow copies 6 (04:51:20) and 5 (04:51:07); the shadow path `\\?\GLOBALROOT\Device\HarddiskVolumeShadowCopyN\` is readable without elevation. Files mid-write in shadow 6 were intact in shadow 5.
- The memory database passed `PRAGMA quick_check` after the WAL replay.
- T-0155 is the session's opening thought.
- Rollup gap: the job-run agents used their job ids as `--session`, so the rollup for this session shows only T-0155 and F-5129. The per-agent results are in the three workflow journals under `C:\Users\USER\.claude\projects\C--Nascence\0a53de93-3665-4bcd-8553-36fcc9cee2cc\subagents\workflows\` (`wf_9c20782c-3a1`, `wf_d2cc7526-78d`, `wf_bb0c30f7-d57`).
- J-4291: 9 of the last 56 stand second-look rows still hit the 90 s lane timeout (now labelled, not fixed).
- J-4153's replay: 54.3% of idle thoughts share their first three words with another thought the same day; the new opener line would have named 39% of same-day reuses, so it cannot reach the 30% threshold alone.

## Open
1. Du is stopped. Next action: the founder starts him from the Control Panel, then a session reads the first boot: no "STATE FILE DAMAGED" lines, `.prev` files appearing, the `[backup-memory] state_` line and `_backup_manifest.json` (J-4441), `num_predict=6000` on think calls (J-4440), opener line in `data/idle_prompt_samples.jsonl`, and no idle-thought stalls from the memo cooldown change.
2. J-3208 is blocked: it needs J-2951 (repair of the pegged genuine judge) first. No code changed.
3. Post-boot reads spawned by the waves: J-4440, J-4441, J-4443, J-4444 to J-4460 (J-4459 is the two-week opener re-read; J-4460 fixes the pre-existing failing `scripts/_test_wandering_inner_cap.py`).
4. Not run: J-4164 (merge old branch `jobrun/J-3750`), J-3680, the UDMS jobs J-4226 and J-4325 (they live in `C:\UDMS`), about 200 other open jobs, and all 62 lab experiments.
5. [OPEN] Why the machine crashed was not investigated. Check the Windows event log if it recurs.
6. Missing plan docs: no `follow_line.md` and no `thought_cycle_as_manifest_loop.md` exist, so J-4170's and J-4223's plan notes were refused.

## Warnings
- Another Claude session was committing to master during this one (J-4194, J-4293, J-4270). Uncommitted plan-doc edits in the tree at wrap time are a mix of that session's work and this session's `plan_state` notes; they were deliberately not swept into this session's commits.
- A stale staged `docs/ROADMAP.md` entry (left by another session's `safe_commit`, F-2570 pattern) made `worktree_dispatch.py merge-back` refuse every branch in wave 1. Check `git diff --cached --name-only` before a merge-back pass.
- `data/_lab/20261120_103325` is an empty folder created when the J-4170 agent ran an existing test through `lab_env`, against the no-writes-to-data rule. Left in place.
- `wmic` does not exist on this Windows build; use `Get-CimInstance Win32_Process`.
- The first `plan_maintain.py` run this session took over ten minutes.

## Pointers
- `data/_crash_recovery_20261120/` (git-ignored): `shadow4/`, `shadow5/`, `shadow6/`, `restore_set/`, `post_crash_live/`, `restore.py`.
- `core/store_persist.py` (durable write and read helpers), `scripts/backup_memory.py`.
- Workflow script reused for all three waves: `C:\Users\USER\.claude\projects\C--Nascence\0a53de93-3665-4bcd-8553-36fcc9cee2cc\workflows\scripts\job-run-du-down-wave1-wf_9c20782c-3a1.js`.
- F-5128, F-5129; jobs J-4426, J-4427, J-4442.
