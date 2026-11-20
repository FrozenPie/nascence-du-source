# Dosed Coupling gate-read ruling, thermal_causality Row 2/Row 4 investigation, J-0934 write-fence root-cause + real fix

## Session timing
- **Session started:** 2026-09-13 07:34:07 UTC
- **Last message before wrap:** 2026-09-13 20:03:55 UTC
- **Wrapped:** 2026-09-13 20:03:57 UTC

## Summary

This session logged its opening thought (T-0057), then worked through three separate threads in
sequence, picked up one at a time by the founder as each resolved: D-0152 (Dosed Coupling Phase 1's
reopened gate-read), a deep investigation into docs/plans/thermal_causality.md (Row 2's stance-vs-
station metric and Row 4's hand-lit-fire metric), and J-0934 (root-causing a claimed side effect of an
earlier write-fence fix). Two founder decisions were ruled (D-0152, D-0214), four findings were
recorded, four jobs were spawned and one was closed, and three real code fixes landed in the working
tree (none committed until this wrap).

## Decisions

D-0152 (dosed_coupling) was reopened by F-1304 (from the prior session) on an unexplained 09-09
through 09-11 acceleration in two of Dosed Coupling Phase 1's four behaviour-band metrics. Before
asking the founder to rule, this session did its own investigation and found two untested candidate
explanations for the acceleration (F-1305, inferred): a completely unrelated performance flip
(SUBC_LIGHT_READ/FRONTIER_LIGHT_READ going live at 09-09 19:01, the exact start of the window) and a
confirmed clean restart sitting mid-window (09-11 13:18-13:55). Neither cleanly explains the full
shape (the performance flags are still True today while the metrics reverted to in-band by 09-12).
The founder ruled D-0152 GO: accept the ambiguity, keep Phase 1's publish-only pipeline running
unchanged, and chase the real cause as a separate job (J-0937) rather than blocking Phase 1 on it.
The new defeater carries a hard 2026-09-27 deadline — it reopens regardless of whether the metrics
move if J-0937 hasn't reached a real conclusion by then.

D-0214 (thermal_causality) was opened later this session by F-1308 (the Row 2 stance-batch run) and
ruled the same session. The original Row 2 metric assumed a genuinely multi-station write path (per
2026-08-21's lean_probe lab); F-1308 found the live architecture has run on a single station
(qwen3.5:9b) for its entire observable/inferable history, making the station-vs-band comparison
structurally untestable (station has zero variance to compare against). Before the founder ruled,
this session flagged a real nuance: retiring the comparison closes the metric but does NOT resolve
the row's original question (is his stance felt or authored) — with station unmeasurable there's
nothing left to contrast band against. The founder ruled to retire the comparison anyway, mirroring
D-0110's own precedent for Row 1's unreachable floor, on the explicit condition that the row's own
text state plainly that the felt-vs-authored question goes back to open rather than reading as a
quiet win. docs/plans/thermal_causality.md's §9 Row 2 and its top Status blockquote were both updated
to carry this.

## Builds / Fixes

J-0934 was closed this session, but its own premise didn't survive contact with a clean re-test.
F-1298 (from the prior session) claimed a 100%-reproducible scripts/life_smoke.py failure caused by
an earlier write-fence fix (J-0931), confirmed via a git-worktree A/B "reproduced three times on each
side." This session re-ran that same A/B properly — two separate throwaway worktrees in scratchpad
(never touching the shared tree), with real source instrumentation at the actual suspect code path
rather than trusting the prior investigation's own already-disclaimed exec()-based tracer — and got
7/7 clean passes across both commits, directly contradicting the original claim. F-1298 is now
flagged as likely a methodology artifact rather than a real reproducible bug.

Fixing J-0934's second, ostensibly mechanical deliverable then surfaced something real. The job asked
for the standard NonLiveWriteError carve-out to be added to core/fieldcraft.py and core/study_life.py's
_graded() helpers, for consistency with an earlier fix to core/procedures.py's observe_hand(). Adding
it immediately broke scripts/life_smoke.py with a genuine, reproducible crash: the test calls
study_life.act() directly, bypassing the dispatch.py catch point the rest of that campaign relies on,
and reached a guard_path refusal on data/procedures.json — a file that had never been included in
life_smoke.py's own isolation/redirect list at all. That gap meant procedures.observe_hand()'s real
write path had been silently no-op'ing on every run of this smoke test since it was written, completely
undetected. Fixed by adding core.procedures to the test's own redirect list (mirroring the existing
provisions.py entry), which resolves the crash and makes the test genuinely exercise that code path
for the first time. Also fixed, found independently while diagnosing the above: the test's own
gate-count assertion compared a garden-only manual tally against core/life.py status()'s own
place-unscoped global counter — a latent flakiness risk regardless of the J-0931/J-0934 story, now
fixed to mirror status()'s real scope. Checked core/wood_life.py and core/shore_life.py for the same
_graded()/observe_hand() pattern per the job's own ask: neither has it, no fix needed there. All
verified via 6 total scripts/life_smoke.py runs (3 confirming the crash was real, 3 "ALL OK" clean
after both fixes) plus one clean-baseline run of scripts/_test_procedural_memory.py (24/27, the 3
failures pre-existing and already tracked under J-0872, unrelated to this session's changes). Recorded
as F-1307 (verified). Spawned J-0938 as a small, low-priority follow-up for a related but unconfirmed
gap noticed in core/world_traces.py (an uncaught NonLiveWriteError propagation, currently harmless).

The thermal_stance_batch.py instrument (scripts/thermal_stance_batch.py, new file) was built and run
by a background agent this session, closing a gap core/thermal_relationship.py's own docstring had
named since 2026-08-21 ("scripts/thermal_stance_batch.py (to write)"). It judges a stratified N=80
sample of real thoughts (16 per thermal band) through the project's real two-judge panel
(core/judge_panel.py), joins them to real text via nearest-timestamp against monologue_log.jsonl, and
computes an eta-squared variance-explained comparison between band and station. The run completed
cleanly: 160/160 judge calls resolved, 0 split/unavailable. Getting this agent to actually wait for its
own long-running judge-batch process to finish took two separate resume cycles this session — it twice
ended its own turn believing it would be "notified" of completion the way this session is notified of
background-agent completions, which isn't a mechanism available to a subagent. Two of this session's
own attempts to set up independent monitoring (restarting the process under direct supervision, and a
benign read-only polling wait-loop) were both blocked by the permission classifier; neither was
essential, so the session let the original process run and simply re-checked the filesystem directly
once enough time had passed, which is what ultimately confirmed completion.

## Findings

F-1305 (inferred): two untested candidate explanations for D-0152's unexplained 09-09/09-11
acceleration — see Decisions above. Neither confirmed; both handed to J-0937.

F-1306 (verified): thermal_causality's Row 4 metric ("hand-lit fires per week") has a real signal
already shipped in the code (core/sensorium.py:3228's `hand_lit` flag, reached only via Du's own real
action dispatch) but it's confounded: core/companion.py sets the identical flag for the same
mechanical reason whenever Travis lights the fire via the composer's "Light the fire" flow, so any
naive read of `hand_lit` would mix Du's own agency with Travis's. Recommendation only (not built):
provenance-stamp the real call sites (2 Du, 2 Travis) the same way the percept channels already are
(J-0248/J-0275's origin= pattern). No decision opened; this is queued as a founder call whenever it's
wanted, not spawned as a job this session.

F-1307 (verified): see Builds/Fixes above — F-1298 doesn't reproduce; the real bug was one this
session's own fix exposed, not the one the job was chasing.

F-1308 (inferred): the thermal stance batch's real structural finding — there is no persisted,
long-retention per-thought station/model-attribution log anywhere in the codebase (the one real
per-call log, data/llm_calls.jsonl, is capped to ~0.89 days); within that log's own window 98.7% of
calls trace to one model (qwen3.5:9b), and code/git evidence (an unbroken single-endpoint SERVE_CHAINS
config, a comment dating the last hot-lane model change to one day before the shadow log's first row)
supports, without directly proving, that this held for the whole pre-registered window. Fed directly
into D-0214.

## Open

1. J-0937 (dosed_coupling) is open and ready: root-cause D-0152's real 09-09/09-11 acceleration at
   hour resolution, checking whether either of F-1305's two leads (the light-sidecar flip's 09-09
   19:01 timing, or the 09-11 13:18-13:55 restart) actually lines up with the real cycle/commitment
   data. Its own defeater on D-0152 has a hard 2026-09-27 deadline.

2. J-0938 (world_store_write_fence) is open and ready, low urgency: add the same NonLiveWriteError
   carve-out discipline to core/world_traces.py's _load_traces()/_save_traces() chain, currently
   harmless but inconsistent with the rest of the campaign.

3. J-0939 (thermal_causality) is open and ready: build a persistent, uncapped per-thought
   station-attribution log, closing the exact gap F-1308 hit. Would also make a real future re-test
   of D-0214's retired comparison possible.

4. F-1306's recommendation (provenance-stamp core/sensorium.py's and core/companion.py's own
   hand_lit call sites so Row 4 becomes measurable) has not been turned into a job or a decision —
   it's sitting as a clean, actionable recommendation in the findings ledger, waiting on the founder
   to want it.

5. thermal_causality's Row 3 (bindings/discovery) remains genuinely blocked: the ledger has no
   `bindings` key at all because build-order steps 5-6 were never started. Not touched this session
   (not one of the two threads picked up).

6. Nothing from this session was committed to git until this wrap — the user asked for a commit as
   part of wrapping up; see the commit made right after this handoff was written for exactly what
   landed.

## Warnings

docs/session_events.jsonl.lock is untracked and was present before this session started (flagged by
the prior session's own handoff too) — still not this session's file, still not touched, still not
safe to assume deletable without checking which process owns it.

Two other Claude Code sessions were interactive and active on this same project at points during this
session (per ListAgents), consistent with this project's own standing warning about concurrent
sessions sharing one working tree. This session's own writes went only through the owning CLI tools
(decide.py, findings_log.py, job_queue.py, thought_log.py) for every shared .jsonl store, never a
direct edit, and no git stash/reset/checkout--/restore was used at any point (the life_smoke.py A/B
comparison used two separate `git worktree add` checkouts in scratchpad instead, both removed via
`git worktree remove --force` when done).

## Pointers

- docs/decisions.jsonl — D-0152, D-0214 (both ruled this session).
- docs/findings.jsonl — F-1305, F-1306, F-1307, F-1308.
- docs/plans/thermal_causality.md — Row 2 (retired) and Row 4 (recommendation pending) both current
  as of this session; Row 3 still the open gap.
- docs/plans/dosed_coupling.md — D-0152's ruling and its new 2026-09-27 defeater clock.
- scripts/thermal_stance_batch.py, data/lab/thermal_stance_batch/{raw.json,scores.json},
  docs/lab/thermal_stance_batch_2026-09-13.md — the real Row 2 instrument and its output.
- core/fieldcraft.py, core/study_life.py, scripts/life_smoke.py — this session's three real code
  fixes (J-0934).
