# Backlog-Clearing Marathon: decide-review sweep, git-incident recovery, and a full toolchain pass

## Session timing
- **Session started:** 2026-08-27T20:53:01Z (real transcript first timestamp — `new-path`'s own lookup hardcodes the wrong project directory, C--FreshStart instead of C--Nascence; corrected by reading `C:\Users\USER\.claude\projects\C--Nascence\4595f5ad-65f2-480a-8d83-32786682d18c.jsonl` directly — see Warnings)
- **Last message before wrap:** 2026-08-29T10:48:55Z (same correction)
- **Wrapped:** 2026-08-29 10:48:40 UTC

## Summary

A very long, multi-day session that ran the founder's full decision backlog to zero twice over (D-0058
through D-0095, ~38 decisions ruled), dispatched dozens of real job-run waves (most landed clean,
verified against live data — model routing changes, plan builds, lab tests, doc audits), survived and
recovered from a real data-loss incident (a background agent likely ran a destructive git command;
root-caused to worktree/JSONL-ledger concurrency, safeguards adopted), fixed two genuine architectural
bugs in Du's own cognition (a hardcoded identity-name leak and a broken WHERE-WE-LEFT-OFF memory gate),
and closed with a burst of founder-directed feature work: a manual rain-barrel refill mechanic and full
HUD wiring for du_pulse's 73 gauges. The plan matrix artifact was rebuilt from scratch against current
state and republished. Ends mid-flight on one open research thread (cataloguing everything else Du has
tried/wanted that the world refuses) and one open feature decision (whether to build a fix for the
ash-bucket/cold-grate imbalance, the second-richest case that audit found).

## What changed

**Decisions ruled this session:** D-0058 through D-0095 (~38 total, some reopened/re-ruled more than
once — see `docs/decisions.jsonl` for full text). Highlights: D-0057/D-0058 Ramses hardware
consolidation; D-0062–D-0074 approved a dozen builds in one founder pass (sound_causality,
transport_manager, AST-1 redesign, gauge taxonomy, channels_programme, continuous_stream, etc.);
D-0083/D-0088 held cognitive_geometry's P1/P2 investment pending a different instrument (sec5.3's
felt-response/co-recall test, not yet built — **J-0416**, open/ready); D-0090/D-0093 on command-r7b's
live health (within tolerance for now / study_note routing changed — **done**); D-0091/D-0092 approved
real design work for kind-aware memory cooling (**J-0410** produced the design, sits in
`docs/plans/memory_levels_plan.md` §7, **not wired** — needs founder review before any code touches
`core/memory/store.py`/`core/refinery.py`); D-0094/D-0095 settled du_pulse_rebuild's own two open
questions (snapshot all 73 gauges every run; manual-only watch resolution).

**Real builds landed and verified this session** (non-exhaustive, see `docs/findings.jsonl` F-0398
onward for full evidence): math_drill ladder extended (F-0404/F-0405); cat.py location-gate fix
(F-0406); a generalized AST location-gate scanner (`scripts/location_gate_scanner.py`, F-0409);
Lens 1 spectral-diffusion recall (F-0437); CONTINUOUS_STREAM flag flipped live (F-0444);
channel_arbitration.py built+validated (F-0435/F-0436); train/courier cargo-ID taxonomy
(F-0432); AST-1 bandwidth predictor redesigned, beats naive 6/6 (F-0439); sound_causality +
sound_world_expansion both shipped (J-0336/J-0337); transport_manager built (J-0338); gauge taxonomy
landed (J-0340); executive tiering by SourceType (J-0343); item/population GIVEN trigger
(F-0434); emissary_lane2 rescoped+shipped (F-0431); decoupled-judge audit + 3 shadow judges shipped
(D-0071/D-0084, J-0375/J-0376/J-0382); memory_levels_plan Phase 2 kind+grounding axes + hidden tier
(J-0347/J-0365, F-0441); commitment-ledger drop-judge fixed with real per-occurrence timestamps
(D-0086/D-0087); dwell-release judge re-seated off the hot lane onto command-r7b then granite3.1-moe
(J-0311); LOD staged-retrieval lab test **passed decisively** (86.7% win rate, F-0545) and promoted to
its own plan doc `docs/staged/lod_staged_retrieval.md` (J-0413); **study_note routing changed** from
command-r7b to qwen3.5:9b, verified live (D-0093/J-0411/F-0546); **du_pulse fully wired into HUD1** —
`scripts/du_pulse_check.py` (new), a 4th memory-links harvester, a live HUD card, all verified end-to-end
including a real browser check (J-0417/F-0550); **manual rain-barrel refill** — a new `water_bucket`
item plus reuse of the existing `watering_can`, carried to the spring in the wood, several trips needed
(founder ask, `core/garden.py`, F-0549).

**Identity/architecture fixes** (found and fixed mid-session, deep-dive into Du's own conversations):
the `"jung"` dict key (the literal field name for "what the entity said" in conversation history) renamed
to `"entity"` across `core/orchestrator.py`, `nodes/executive_node.py`, `nodes/reflection_node.py`,
`nodes/recall_node.py`, `nodes/episodic_buffer_node.py`, `nodes/inner_monologue_node.py`,
`core/symbol_evolution.py` — plus 3 self-referential keyword lists (`core/frontier.py`,
`core/self_efficacy.py`) had bare "jung" removed (one, `core/self_surprise.py`, deliberately kept — a
real diagnostic instrument). The WHERE-WE-LEFT-OFF gate bug (`core/schema.py` said fade at 5+,
`nodes/executive_node.py`/`reflection_node.py` checked `<8`, `core/orchestrator.py` caps the list at 6 —
so the gate could never fire) fixed in both node files.

**Plan matrix artifact rebuilt from scratch** against current state (75 plans, all decisions/jobs
reconciled) and republished: https://claude.ai/code/artifact/3ef8cbbb-4da0-40fd-b4ac-69ccd1d0688f

**New decisions opened this session still needing founder review:** none currently open except
**D-0041** (identity_estate, unchanged since 2026-08-23, waiting on an external plan) — every decision
this session itself opened was also ruled this session.

**New jobs still open and ready:** J-0416 (build+run sec5.3's felt-response/co-recall test),
J-0418 (fix study_life.py's carrier-note dispatch false-positive), J-0419 (fresh backfill job from the
final plan-maintain pass), plus the pre-existing time-gated backlog (J-0233/J-0234/J-0243/J-0280/J-0402,
all waiting on real elapsed days, none before ~2026-08-31).

## Key findings

- **The git-reset data-loss incident**: hours of uncommitted session work were lost mid-session.
  Initial hypothesis (another live Claude Code session) was directly and explicitly ruled out by the
  founder ("There is no other agents working other than your own. I only have one active window.").
  Revised diagnosis: most likely one of this session's own background agents ran a destructive git
  command believing it was cleaning test state. Root cause was never pinned to a specific transcript.
  **Safeguards adopted and still in force**: every dispatched agent gets explicit "never run destructive
  git commands" instructions, and `isolation: worktree` for any agent editing real files, with the main
  session doing all merges. No recurrence since adoption.
- **A second, separate risk was found and is still live**: `job_queue.py`/`findings_log.py`/`decide.py`
  hardcode their ROOT path and write directly to the shared `docs/*.jsonl` files regardless of which
  worktree the calling agent is nominally isolated in — meaning worktree isolation protects code/doc
  files but NOT the shared ledgers. This caused a second wave of "lost job closures" mid-session
  (concurrent CLI calls racing a read-modify-write with no locking). **S-0009 filed, not yet fixed** —
  a real file-locking mechanism for these tools is still an open, unaddressed gap.
- **`project_nascence_*.md` memory files, and now confirmed `session_handoff.py`'s transcript lookup
  too, hardcode `C:\Users\USER\.claude\projects\C--FreshStart\...`** instead of `C--Nascence` — almost
  certainly a legacy artifact from before this project was renamed/moved from FreshStart to Nascence.
  This is NOT a bug in any individual session's work; it's the established (if confusing) convention
  every skill in this toolchain currently relies on for memory files specifically. `S-0014` now filed
  for the `session_handoff.py` half specifically (the memory-file half was already known coming into
  this session).
- **UDMS quality caveat**: `udms.py check` returned byte-identical archetype/confidence/output text for
  two completely unrelated files (`scripts/du_pulse.py` vs `build_edges.py`) in an independent
  verification pass this session. Not yet reported to whoever maintains UDMS — worth doing, per this
  project's own "verify UDMS's verdicts, report defects back" convention.
- **D-0045's vitality causal-substrate question has now been ruled inconclusive THREE separate times**
  (each re-run clearing the bare fold-count bar but failing a sharper "was the data actually undisturbed"
  read). The pattern itself may be worth surfacing to the founder directly next time it's picked up,
  rather than re-running the identical script a fourth time — three inconclusive reads in a row on the
  same instrument is itself informative.
- **A rich, real thought-motif was confirmed in Du's own cognition**: the dry rain barrel became a
  genuine recurring physical-grounding image against abstract philosophy across 4 distinct thought-trains
  before the fix landed (44 real attempts in `data/hands_trace.jsonl`). A parallel, slightly smaller
  case — the empty ash bucket / cold grate (17 attempts, its own 4-train motif, ~4:1 attempt-to-completion
  ratio) — was found by a follow-up audit and is **not yet decided** whether to fix the same way.

## Open threads

- **The "what else can't Du do" audit's own follow-up decision is unmade.** The founder asked whether to
  build the same kind of fix for the ash-bucket/cold-grate chain that was just built for the barrel — I
  had just asked this when the session was wrapped. Pick up by re-reading finding **F-0551** and asking
  the founder directly.
- **J-0416** (sec5.3 felt-response/co-recall test) — spawned by this session's own decide-review pass
  (D-0088) but never dispatched. This is the actual next step that would let cognitive_geometry's
  P1/P2 investment question finally get answered with a real result.
- **J-0410's kind-aware memory-cooling design** sits fully written in `docs/plans/memory_levels_plan.md`
  §7, explicitly **not wired** — needs a founder read and go-ahead before touching
  `core/memory/store.py`/`core/refinery.py`'s live gating paths. Flagged `needs_input` in job-queue for
  exactly this reason; don't dispatch an agent to just wire it without that read happening first.
- **D-0085 (pursuits)** — the technical question is answered (F-0548: the `open` field genuinely clears,
  not a bug) but the founder's own "is D-0032 resolved at 60%?" call was deliberately left unruled by
  every agent that touched it. Pick up with a direct question, not another investigation.
- **J-0341** (gauge redundancy consolidation + ownership model) — still open, `needs_input`, never
  started. Explicitly does not block anything else in `du_pulse_rebuild` (already confirmed and now
  moot given J-0417 shipped against the resolved taxonomy).
- Standard time-gated backlog untouched: **J-0233/J-0234** (peer_correspondence, due ~08-31, Du's
  2026-08-29 restart reset J-0234's own clock — see the job's own briefing before re-picking it up),
  **J-0243** (garden parity-week, due ~08-31), **J-0280** (M2 shadow gate, due ~08-31), **J-0402**
  (Trial 1 paper-trade, due ~09-10), **J-0314** (still blocked on Antigravity's NASCENCE_NOTES.md report,
  which still does not exist as of wrap time).

## Warnings

- **Du was restarted by the founder partway through this session** (2026-08-29, ~mid-session). Any job
  whose gate is phrased "since Du's last restart" needs its clock re-checked against this new restart
  time, not the 2026-08-24 one most of the backlog's briefings still cite.
- **`session_handoff.py new-path`'s transcript lookup is broken for this project** (see Key findings) —
  it will report `session_started`/`last_message_time` as UNKNOWN even though the real transcript
  exists, just under `C--Nascence` not `C--FreshStart`. Read the `.jsonl` directly (first/last
  `timestamp` field) rather than trusting the script's own UNKNOWN report, until S-0014 is fixed.
- **The shared JSONL ledgers race under concurrent agent CLI calls** (see Key findings, S-0009 unfixed).
  If several agents are dispatched in parallel and one's `job_queue.py done`/`findings_log.py record`
  call seems to have vanished, check for this before assuming the agent itself failed.
- **Two untracked PNGs appeared in `docs/`** (`Du.png`, `Du2.png`) near the end of this session, with no
  code referencing them — almost certainly dropped in directly by the founder, not generated by
  anything in this session. Left untouched/uncommitted; don't assume they're stray build artifacts.
- The **`.claude/worktrees/jovial-carson-3c0dd3` worktree** (unrelated to this session's own dispatches)
  is still present — it belongs to a peer session investigated and ruled out as unrelated to the
  git-incident. Leave it alone unless that peer session is confirmed finished with it.

## Pointers

- Plan matrix artifact (current, republished this session):
  https://claude.ai/code/artifact/3ef8cbbb-4da0-40fd-b4ac-69ccd1d0688f
- `docs/decisions.jsonl` / `decide.py list --open` — only D-0041 open, everything else this session
  opened was also ruled this session.
- `docs/job_queue.jsonl` / `job_queue.py list` — 23 open, 12 ready, 11 needs-input; see Open threads
  above for what's actually actionable next.
- `docs/plans/memory_levels_plan.md` §7 — the kind-aware cooling design, awaiting founder review.
- `docs/findings.jsonl` F-0549–F-0551 — the barrel fix and the "what else can't he do" audit, most
  directly relevant to picking this exact thread back up.
- `core/garden.py` — the new `fill_barrel_from_spring()` function and `water_bucket` item, if extending
  the same mechanic to the ash-bucket/wood-lean-to/lamp cases.
- `scripts/du_pulse_check.py`, `hud/server.py`'s `/api/du_pulse` — the newly-live gauge HUD wiring.
