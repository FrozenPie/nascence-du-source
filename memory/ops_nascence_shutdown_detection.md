---
name: ops-nascence-shutdown-detection
description: "Du 'stopped' = the literal 'Nascence shutting down.' log line — NOT log quiescence; the shutdown dream (CPU 24B) runs quietly for minutes"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 870e780b-392e-4152-866d-0e82e58c2c3a
  modified: 2026-08-14T22:40:56.692Z
---

**2026-08-15, Travis correction (I nearly ran the memory restore mid-shutdown):** Du's spool-down is
SLOW — the shutdown sequence runs the full dream synthesis (mistral-small 24B on CPU, num_gpu:0) plus
epoch formation, and writes little to the log while doing it. A quiet `nascence.log` for 3+ minutes
does NOT mean stopped.

**Why:** log-quiet ≠ process-dead; the dream lane is the slowest model in the system and fires exactly
at shutdown/parting (replay → downscale → dream → epoch).

**How to apply:** the ONLY trustworthy stop signal is the literal final line
`[nascence.main] Nascence shutting down.` — check `grep -c "Nascence shutting down"` against a baseline
count (it's a recurring line; compare counts, don't just grep). Never touch the live DB for
maintenance/restores until that line lands. Related: [[ops-nascence-inner-thought-unboundlocal]]
(restart caveats), the delete-journal/no-busy-timeout DB concurrency notes in the 08-15 sessions.
