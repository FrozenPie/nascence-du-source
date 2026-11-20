---
name: ops-claude-code-job-object-kills-servers
description: Claude Code's PowerShell tool runs inside a Windows Job object (no breakaway); Du's hubs/supervisor launched from it die when the Claude app restarts. Use scripts/start_supervisor_detached.ps1 (WMI launch).
metadata:
  type: project
---

**Verified 2026-09-03 (F-0704).** The Claude Code desktop app's PowerShell tool process is inside a
Windows Job object with breakaway disabled (`IsProcessInJob` True, `LimitFlags=0x0`). The Bash tool
was NOT in a job that day. Anything launched from the PowerShell tool — hubs via `launch_servers.ps1`
(DETACHED_PROCESS grandchildren included), `supervisor.py` — stays in the job and is killed when the
Claude app restarts. On 2026-09-03 09:18:08 the app auto-updated (Claude_1.44121.1.0) and took down
Judge1 :11439, Judge2 :11440, Dreamer :11442 and the D-0127 watchdog together; Du (started from the
standalone Control Panel) survived and logged `[left-lane] essay-grade unavailable ... port=11439`
fail-opens all morning. The port sweep of the code found nothing wrong — D-0125 keeps the local tier
live and left_lane/peers/decomposed_critic/librarian correctly point at it.

**Why:** a "transport error on 127.0.0.1:11439" is not evidence of a config bug when the tier was
launched from a Claude session — check `netstat` and `data/supervisor.log` first (see
[[ops-nascence-30day-outage]] on verifying an instrument before trusting a trend, and
[[feedback-my-failure-modes]]).

**How to apply:** bring the local tier up with
`powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start_supervisor_detached.ps1`
(WMI `Win32_Process.Create` → child of WmiPrvSE, no caller job; idempotent; the supervisor then
ensures + watches all four local servers). `launch_servers.ps1` now prints a red warning when run
inside a job. Rule recorded in Nascence `CLAUDE.md`. Related: [[project-nascence-session-handoff-20260902-041735-judge1-repoint-control-panel-bug]] (F-0684 Full-Start bug, D-0125, D-0127).
