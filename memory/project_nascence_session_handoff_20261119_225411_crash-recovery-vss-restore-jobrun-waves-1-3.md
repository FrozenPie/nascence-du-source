---
name: project-nascence-session-handoff-20261119-225411-crash-recovery-vss-restore-jobrun-waves-1-3
description: 2026-11-20 hard crash zero-filled 19 data/ state files; restored from 04:51 Windows shadow copies (F-5128/F-5129); three Du-down job-run waves (31 jobs) merged; Du not yet restarted on them.
metadata:
  type: project
  originSessionId: 0a53de93-3665-4bcd-8553-36fcc9cee2cc
  sessionStarted: 2026-11-19 20:33:43 UTC
  modified: 2026-11-19T22:55:10.442Z
---

Handoff: `C:\Nascence\docs\session_handoffs\HANDOFF_20261119_225411_crash-recovery-vss-restore-jobrun-waves-1-3.md`.

A hard crash at about 09:06 NZ on 2026-11-20 zero-filled every `data/` state file written in its last minute; Du's slow relaunch was a WAL replay, and he then loaded the blank files silently. They were restored from VSS shadow copies (copies kept in `data/_crash_recovery_20261120/`). State saves are now durable with a `.prev` generation (J-4426, J-4442) and the per-boot backup covers those files (J-4427). Three job-run waves were merged while Du was down; the first boot on them still needs reading (J-4440, J-4441, J-4443..J-4460).

Related: [[feedback_safe_commit_stale_index]] (the stale staged ROADMAP blocked merge-back), [[feedback_jobrun_parked_jobs_and_sweep_sizing]], [[reference_windows_vss_recovery]].
