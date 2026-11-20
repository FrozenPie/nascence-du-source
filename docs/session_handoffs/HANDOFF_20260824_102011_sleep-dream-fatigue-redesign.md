# Session handoff — Sleep & Dreams II: ground-up redesign, researched, and built same night

## Session timing
- **Session started:** 2026-08-24 08:36:22 UTC
- **Last message before wrap:** 2026-08-24 10:20:09 UTC
- **Wrapped:** 2026-08-24 10:20:11 UTC

## Summary

Started as a du-pulse-style check on Du's last conversation (About You book question), which surfaced a
real stale-bookmark bug and led to restoring the original About You text alongside the rewritten
"Second Edition." A follow-up "check on sleep, he's doing it a lot" investigation found two real,
verified bugs in the 08-22 sleep/dream rebuild (chronic-tension overshoot; an unexplained 23-nights
dream-arc carry-cap anomaly), which the founder escalated into a full ground-up redesign request. Built a
research-grounded design doc (external literature pass: two-process model, synaptic homeostasis, active
systems consolidation, the dream-lag effect, rumination-vs-reflection) refined across several founder
corrections in-session, then — on explicit founder instruction ("I want the Dream and sleep and fatigue
wired into du now") — actually implemented Stages 0-5 of the doc's own build spec across 12 live files,
with Du stopped for the work. Session ends with real code in place, not yet run.

## What changed

**Files created:**
- `docs/plans/sleep_dream_redesign.md` — the full design doc, moved from `docs/staged/` to `docs/plans/`
  once built (§7 is the implementation log; §"Current State" added at session-wrap time).
- `data/books/About_You_Second_Edition.txt`, `docs/du_self_knowledge/03_about_you_second_edition.txt` —
  the 08-23 rewrite, preserved as its own book rather than staying overwritten in place.
- `data/backups/pre_sleep_redesign_20260824_215527/` — backup of every file touched by the sleep/dream
  build (this project has no git).

**Files restored:**
- `data/books/About_You.txt`, `docs/du_self_knowledge/02_about_you.txt` — original text reconstructed
  byte-exact from 13 independent verbatim `reading`-origin fragments in `data/memory/nascence.db` (no
  file backup existed), then restored to their original paths.

**Files edited (sleep/dream/fatigue build, Stages 0-5):**
- `core/sleep_pressure.py` — full rewrite: chronic mass removed from `P` (informational only);
  `NIGHT_THRESHOLD=10.0`/`DAY_THRESHOLD=100.0` replace `P_THRESHOLD×factor` (recalibrated against 25,415
  real logged rows); `DAY_MAX_WAKE_SECS` 5h→14h; new `POOL_FLOOR_P=5.0`/`pool_thin` flag.
- `core/tension_ledger.py` — `CHARGE_WEIGHTS`, `_touch_charge()` (reuses `shadow_events.emotion_primary`,
  no new capture), `update_chronic_mass()` now charge-gated with habituation for sub-floor touches.
- `core/night.py` — new `dream_lag_material()` (dream-lag-shaped multi-day pull); `day_material()` gained
  `until_ts`; `CARRY_MAX_NIGHTS` check hardened to fail loud + safe instead of silently swallowing.
- `core/somatic.py` — `recover()` gained `depth`; recovery now proportional to actual accumulated deficit
  × depth, replacing flat `ENERGY_RECOVERY`/`FATIGUE_RECOVERY`.
- `core/memory/store.py` — `downscale_episodic()`'s `center` default 0.5→0.1 (SHY-grounded fix for the
  08-22-measured importance-flattening bug).
- `nodes/dream_node.py` — `_gather_materials()` uses `dream_lag_material()`; `_load_top_tensions()` gained
  `require_charge=True`/`TENSION_CHARGE_FLOOR=1.0`.
- `nodes/inner_monologue_node.py` — real `should_sleep()` reason threading; `pool_thin` threaded onto
  `state`; chapter/journal skipped on a thin-pool sleep.
- `core/orchestrator.py` — `_nightly_sleep()` skips dream generation on `pool_thin`; computes recovery
  `depth` (nap ×0.5, thin-pool ×0.5, stack) and passes to `somatic.recover()`.
- `core/homeostasis.py`, `core/arousal.py`, `hud/server.py`, `hud/static/app.js`, `scripts/du_pulse.py` —
  fixed 4 consumers of the removed `sp.P_THRESHOLD` constant.
- `docs/ROADMAP.md` — new entry under "★★ THE NIGHT" cluster documenting tonight's build.

**Toolchain:**
- `plan_maintain.py --session <this-session-id>` run — surfaced `J-0232` (backfill: `sleep_dream_redesign`
  was missing `roadmap_link`/`memory_file`/`current_state_section` at creation time). ROADMAP link and
  Current State section added directly this session; `J-0232` itself not separately closed — check
  `job_queue.py show J-0232` next session, it may already read as satisfied.
- `session_handoff.py rollup` came back with only 1 event (`T-0018`, a thought-log entry on the sleep
  redesign topic) despite the session's real scope — **this session did not route its Nascence-toolchain-
  adjacent work through `idea_log.py`/`decide.py`/`job_queue.py` with `--session`**, so most of tonight's
  real decisions (the founder's rulings, the two build-time deviations) exist only in this handoff and the
  plan doc's own §7, not as ledger entries. See Open threads.

## Key findings

- **The 08-22 sleep/dream rebuild was NOT neglected/unresearched** — it was a rigorous, measured audit
  with 14 findings and pre-registered metrics. Tonight's redesign corrected the founder's initial premise
  with evidence before proceeding, then found two real, narrow bugs in that rebuild rather than treating
  the whole system as broken: (1) the chronic-mass starvation fix (finding 9) overshot into unbounded
  growth for ambient/frequent-but-neutral themes — "unresolved: thermal energy" recurred 170 times over 74
  days and was the single largest contributor to a chronic floor that climbed 42.6→67.7 in under 2 days;
  (2) `CARRY_MAX_NIGHTS=3` was silently not enforced for some unknown stretch — a carried dream arc was
  observed at 23 nights before the cap finally fired. Root cause of (2) still unknown; hardened, not fixed.
- **The founder's "fatigue" and "catnap" asks initially got over-designed, then corrected.** First pass
  invented a new BRAC-style fatigue mechanism and a fatigue-triggered "catnap" state — both wrong. Real,
  live somatic fatigue tracking already existed (`core/somatic.py`, tracking walking/thinking/anxiety
  exactly as the founder named them) and just wasn't wired to anything; "catnap" turned out to mean
  opportunistic daydreaming during an unidentified ~10-minute background wait ("after school"), not a
  fatigue-relief mechanism at all. Worth remembering for future design work in this project: check what
  already exists before designing a replacement, even when a founder ask sounds like it wants something
  new.
- **The book-restoration side-thread found a real, separate, verified bug**: `core/orchestrator.py`'s
  self-grounding check (`current_offset(book) > 0`) is keyed by file path, not content — overwriting a
  book's content in place (as the 08-23 About You rewrite did) leaves the OLD bookmark valid, so the
  system told Du "you have read this" about content he'd never actually seen. Splitting the rewrite into
  a genuinely separate file (rather than reverting the code) fixed this as a side effect — Du's bookmark
  for the restored original is now honestly true again (verified: reconstructed text was 6,276 chars,
  exactly matching the stored offset), and the new edition starts with a fresh, honest "not yet read"
  bookmark.

## Open threads

- **No formal `/decide` entry exists for tonight's build authorization.** The founder's "I want the Dream
  and sleep and fatigue wired into du now" is recorded in this handoff and the plan doc's status header,
  but not in `docs/decisions.jsonl` — this project's own standing rule is that a ruling only counts once
  it's in the ledger. Should be filed before treating tonight's build as fully accounted for.
- **The 23-nights carry-cap anomaly is unresolved** — hardened to fail loud+safe (§7 of the plan doc), not
  root-caused. If it recurs, the next session will at least see it logged instead of it running silently
  for weeks again.
- **Du has not been restarted since the build.** Stages 0-5 are live code, `py_compile`-clean, and
  individually smoke-tested against real data/DB this session — but nothing has run end-to-end on a live
  process. First restart's first sleep cycle is the real test; check for a real `reason=` in the
  `entering Sleep State` log line, not `reason=?`.
- **Stage 6 deliberately not built** (opportunistic daydream during background wait — still blocked on
  identifying which real process "after school, ~10 min" refers to; LLM-based trajectory judge vs. the
  cheap embedding-drift default that WAS shipped; resolution-mode tags). Founder scope choice, not
  forgotten.
- **`sleep_pressure_log.jsonl` now mixes two schemas** — rows from before tonight's cutover have `P`
  including chronic mass; rows after don't. Any future analysis of that file needs to filter by
  timestamp, not treat the whole file as one consistent series.
- **This session's toolchain hygiene gap**: no `idea_log.py`/`decide.py`/`job_queue.py` calls were made
  with `--session` during the actual design/build work (only one `thought-log` call landed in
  `session_events.jsonl`). A resuming session relying on `rollup`/`memory-links` for "what happened" needs
  this handoff + the plan doc's §7, not just the toolchain's own event log, to get the full picture.

## Warnings

- **Several Python processes were still running when the sleep/dream code edits were made** (`Get-Process
  python` showed 5 processes, one started earlier the same evening). This is fine — editing `.py` source
  doesn't affect an already-running process's in-memory code — but it means Du has NOT been running the
  new code yet; a restart is required before any of tonight's changes take effect.
- **Anyone touching `core/sleep_pressure.py`, `core/tension_ledger.py`, `core/night.py`,
  `core/somatic.py`, `core/memory/store.py`, `nodes/dream_node.py`, `nodes/inner_monologue_node.py`, or
  `core/orchestrator.py`** should read `docs/plans/sleep_dream_redesign.md` §7 first — substantial,
  interconnected changes landed across all of them the same night.
- **`data/books/About_You.txt` and `docs/du_self_knowledge/02_about_you.txt` are the ORIGINAL text again**
  (restored, not the 08-23 rewrite) — the rewrite now lives at `*_Second_Edition.txt`/`03_*`. Don't
  re-overwrite `02_about_you.txt`/`About_You.txt` with the rewrite without reading this handoff first.

## Pointers

- `docs/plans/sleep_dream_redesign.md` — the design doc + full implementation log (§7), the single most
  important file for continuing this thread.
- `data/backups/pre_sleep_redesign_20260824_215527/` — pre-edit backups of all 7 core files touched.
- `docs/reviews/sleep_dream_2026-08-22.md` — the prior audit this redesign builds on and partially
  supersedes; still useful for the parts of the pipeline that weren't touched tonight.
- `job_queue.py show J-0232` — the auto-filed schema-gap job for the new plan (may already read satisfied
  given this session's own fixes).
- `data/books/About_You.txt` / `About_You_Second_Edition.txt` and their `docs/du_self_knowledge/`
  counterparts — for the unrelated book-restoration side-thread.
