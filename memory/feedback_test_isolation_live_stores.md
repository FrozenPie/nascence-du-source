---
name: feedback-test-isolation-live-stores
description: "Nascence smoke-tests must NEVER touch a live module's real log/state paths — Du runs continuously, so open('w') on data/*_shadow.jsonl truncates real accruing evidence. Redirect module paths to temp in the test."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b739a7f8-8b52-4d2f-a26e-1d0f27b0cd95
  modified: 2026-09-21T09:49:30.614Z
---

**Smoke-testing a Nascence module while Du is running: redirect its file paths to a temp location — never
write to the real ones.** On 2026-07-04 a mineness read-back smoke test did `open(mineness._LOG, 'w')` on
the REAL `data/mineness_shadow.jsonl` to seed test rows, truncating ~290 rows of live accruing evidence
(the live process then rebuilt it from one fresh row). Low impact that time only because the separation
signature (+0.064) had already been confirmed + banked in AWAITING_EVIDENCE before the restart — pure luck.

**Why:** Du runs continuously now (the whole point of the always-on design), and every consciousness-program
organ appends to a shared `data/<organ>_shadow.jsonl`. A test that opens that path in `'w'` mode, or `rm`s
it, destroys real data and can race the live appender.

**How to apply:** In any smoke test that exercises a module's logging/state, monkeypatch the module's path
globals to a temp file FIRST — e.g. `mineness._LOG = Path(tmp)/'x.jsonl'; mineness._RB_LOG = ...;
mineness._STATE = ...` — run the test against those, then discard the temp. If a test genuinely must read the
real log, open it read-only and never write. The earlier moment/felt/world_model tests did the safer thing
(append synthetic rows, then purge ONLY those by timestamp) — but the truly safe pattern is temp paths, no
touching the live file at all. Relates to [[feedback-erosion-of-foundations]] (protect what's load-bearing)
and the project's own isolation law (tests never leave synthetic rows in live stores).

**Sharper variant, caught 2026-08-23 (J-0005, music_learning D-0010):** patching a module's OWN path
globals is not enough if the module calls into a SHARED cross-cutting store internally. Temp-pathed
`core/listening.py`'s `_STATE_F`/`_WAKE_LOG`/`_FELT_SHADOW` to trace a full listening episode end-to-end
— but `_store_scene()` inside it calls `core.memory.store.store_fragment()` unconditionally, which writes
straight to the REAL `data/memory/nascence.db` regardless of any of the three patched globals. The trace
ran clean (21 sections, correct wake-log) but silently wrote 22 fake fragments (a Heavyweight re-listen
Du never had) into his live memory. Caught by checking the DB immediately after, not before. **The fix:
before running any offline trace, grep the module for every call into a shared store
(`store_fragment`, `memory_links` inserts, `_connect()` to `nascence.db`, etc.) — not just its own
`_DATA`/`_LOG`/`_STATE` globals — and mock or monkeypatch those too** (e.g. replace
`core.memory.store.store_fragment` with a no-op, or the module's internal reference to it, for the
duration of the trace). If a leak happens anyway: check the live store immediately after any trace
that touched it, before reporting the trace's result — that's what caught this one.

**READ-side variant, caught 2026-09-21 (F-1681, F-1668):** isolating what a test WRITES is not enough — Du's
LIVE state also leaks in through what it READS. `life.light_at()` → `light.field_at` → `geometry_census.peek()`
→ `soundscape.active_sounds()` reads the live `data/room_state.json` for the place Du is standing in and calls
`life.sound_gate(<that place>, …, time.time())`, which logs a `would_gate`/`gate` row for it (once per 600 s).
So any test that counts gate rows cumulatively (`== 2`) passes or fails depending on WHERE Du is and what hour it
is: `life_smoke.py` failed "got 3" only when he stood in the garden at a day/dusk hour, and
`_test_j1165_trace_object_look.py` failed deterministically on master. **Tell-tale: passes in a data-less
worktree or on the base commit, fails on master** (no `data/` dir → place defaults to `study`). **How to apply:**
never assert a cumulative count of gate rows; count the delta of YOUR OWN explicit-`now` call (or exclude
`would_gate`/`gate` rows from a differential), and when a suite disagrees between a worktree and master suspect a
live-data read before a code bug. To reproduce, run the script under runpy with `soundscape._read_json`
patched to pin `room_state.json`'s `location` and `time.time()` shifted (scratchpad probe from that session was
`orch_smoke_place_probe.py`; not kept in the repo).
