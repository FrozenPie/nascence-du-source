---
name: feedback-parallel-agents-need-locked-ledgers
description: "Before fanning out many parallel agents that write to a shared ledger, prove the writing tool is locked and fails loud. 2026-10-31: 15 agents wiped docs/findings.jsonl (3,465 findings) through findings_log.py's unlocked load-modify-save."
metadata:
  type: feedback
---

Before launching more than a few agents that write to a shared ledger, race-test the writing tool on a throwaway
copy first: N concurrent processes, then count rows and unique ids. Check that it holds `ct.locked(STORE)` across the
whole load-modify-save, that a missing or unreadable file is a hard stop, and that save refuses to shrink.

**Why:** 2026-10-31 the prompt-investigation sweep ran ~15 agents at once. `findings_log.py` (record, spawn-job) had no
lock, and `load()` went through `ct.read_text`, which returns "" on any exception. One read failed mid-replace, the
next finding became F-0001, and 3,465 findings were overwritten. Restored 2026-11-01 from git + transcripts (F-3537
records it; map in `docs/reviews/findings_wipe_2026-10-31.md`). Every other ledger tool already locked; this one did not,
and nobody had run it under real concurrency.

**How to apply:** I launched the first wave without checking the tool and found out from an agent. Check first, launch
second. Also: my own race test called the real `ct.log_event`, so it wrote 40 test rows (session TEST) into the live
`session_events.jsonl`; test tools by monkeypatching the event log path as well as the store. Related:
[[feedback-test-isolation-live-stores]], [[project-nascence-prompt-inventory-2026-10-31]].
