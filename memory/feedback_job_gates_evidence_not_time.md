---
name: feedback-job-gates-evidence-not-time
description: "Job waits must be evidence gates that survive restarts, never calendar dates or uninterrupted-uptime clocks"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 0bdafb3f-1621-463a-92ae-61ed5f66568a
  modified: 2026-10-18T22:28:42.438Z
---

Job-queue waits should be gated on accrued evidence (rows in a log, accrued live hours), not on a calendar `not_before` date, and not on a clock that resets when Du restarts.

**Why:** Travis (2026-10-19): Du is a WIP restarted often for updates, Windows updates interrupt uptime, and he sometimes needs the hardware for other things, so long uninterrupted runs rarely happen. A date is a guess, and a "since current boot" or uptime clock would starve jobs forever.

**How to apply:** Use `job_queue.py defer <id> --gate-file F --gate-rows N [--since-boot] [--gate-match k=v] --drop-date` (since-boot pins a FIXED `since_ts` at set time, so rows keep counting across later restarts) or `--live-hours N` (Du's accrued running time, summed from sleep_pressure_log heartbeat rows at ~65 s each, across restarts). Built 2026-10-19 in `~/.claude/skills/job-queue/job_gate.py`. Only 4 jobs have no gate and ~71 still carry dates; the rest are evidence-gated. See [[reference-nascence-claude-md-rules]].
