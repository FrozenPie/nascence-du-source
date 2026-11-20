# Built /job-run (batch job-queue execution) + ran + fixed a real concurrency bug found while verifying

## Session timing
- **Session started:** 2026-08-23 10:41:35 UTC
- **Last message before wrap:** 2026-08-23 11:53:57 UTC
- **Wrapped:** 2026-08-23 11:53:59 UTC

## Summary

Travis asked for a new sub-skill of `/job-queue` that batch-works the open backlog via agents instead
of `next`'s one-job-at-a-time handoff: mechanical jobs first, then real plan-domain work, letting the
real-work tier spawn jobs/rule decisions/edit plans as it goes. Built `/job-run`, tested its tiering
logic against the live 72-job backlog, then ran a real pilot (Tier 1+2 only, Travis's explicit scope
choice) via the `Workflow` tool. The pilot mostly worked — but running ~23 agents in parallel, each
individually rerunning the full `plan_maintain.py` per its own job briefing's literal text, raced on a
shared full-rebuild file and produced ~28 spurious re-filed jobs. Caught this by actually verifying
results rather than trusting the agents' self-reported "done," root-caused it with a live repro (one
clean rebuild instantly fixed the "missing" edges), and fixed it in the skill itself.

**Rollup note:** `session_handoff.py rollup` returned zero rows for this session id — none of this
session's `job_queue.py`/`build_edges.py`/`plan_maintain.py` calls were run with a `--session` flag
(those CLIs don't currently expose one at the call sites used here). This handoff is built from the
actual conversation record and direct verification, not the session_events log — flagging the gap
rather than silently treating "no rows" as "nothing happened."

## What changed

- **Built** `~/.claude/skills/job-run/job_run.py` and `SKILL.md` — new sub-skill of `job-queue`.
  Tiers the open+ready backlog: Tier 1 = `category: backfill` (mechanical), Tier 2 = `category: doc`
  or a `source` naming a meta-tooling audit (`plan-index:`/`plan-maintain:`/`skill-manager:`/
  `gauge-check:`), Tier 3 = everything else (`build`/`analysis`/`test`/`lab_experiment` sourced from
  `plan:`/`decision:`), grouped by `plan` slug so same-plan jobs serialize instead of racing (caught
  a real example live: `the_consciousness_program` had two open jobs, J-0003 and J-0069).
- **Cross-linked**: `job-queue`'s own `SKILL.md` now points to `/job-run` under a new "Batch-working
  the backlog" section.
- **Memory**: new `memory/reference_nascence_job_run_tool.md`; `MEMORY.md`'s toolchain index line
  updated to list `/job-run` and link the new reference file.
- **Ran the pilot** (Workflow run id `wf_6b477918-b21`, 34 agents, 33 real jobs dispatched: 27 Tier 1
  + 6 Tier 2 after refresh dropped jobs another concurrent window had already closed) — **31 done, 2
  correctly declined**:
  - Jobs closed: J-0015, J-0016, J-0017, J-0019, J-0020, J-0021, J-0022, J-0024, J-0025, J-0028,
    J-0029, J-0030, J-0031, J-0032, J-0033, J-0034, J-0035, J-0037, J-0038, J-0039, J-0040, J-0042
    (Tier 1), J-0067, J-0051, J-0052, J-0063 (Tier 2). (J-0008–J-0014, J-0018, J-0023, J-0026, J-0027,
    J-0036, J-0077–J-0080 were closed by a **different, concurrently-active window** during this same
    window — see Warnings.)
  - Blocked (left `in_progress`, real findings, not guesses): **J-0053** (D-0013's plan slug
    `factory_stations` has no real plan doc — ROADMAP explicitly says that research cluster isn't
    tracked as a plan by design; needs a founder call on where it belongs) and **J-0050** (29-plan
    ROADMAP sync — found most "disagreements" are a `plan_index.py` parser artifact, nearest section
    header vs. each plan's own bullet badge, not real staleness; fixed the 2 genuine ones, recommends
    a parser fix over hand-editing the rest).
  - Real memory-file renames (fixed genuine slug/filename mismatches build_edges.py needs to match on):
    `project_nascence_lane2_witness.md` → `project_nascence_lane2_the_witness.md` (+ 4 other files'
    wikilinks + `MEMORY.md`), `project_nascence_consciousness_program.md` →
    `project_nascence_the_consciousness_program.md` (+ `MEMORY.md` link).
  - New decisions: **D-0014** open (sound_causality vs. sound_world_expansion content overlap),
    **D-0015** open (does shore_upgrade.md supersede generative_world_sedimentation's Module A),
    **D-0016** open (social_world_school belief-injection vs. G6-G9 guardrails), **D-0017** ruled GO
    (social_world_school latch-loosening gate, heeded_rate=0.342, defeater: re-measure after latch
    loosens).
- **Found and fixed a real toolchain bug** (not hypothetical — reproduced live): ~23 Tier-1 agents ran
  in parallel, each individually rerunning the full `plan_maintain.py` per its job briefing's literal
  text (written for `next`'s one-at-a-time use). `plan_maintain.py` includes `build_edges.py` doing a
  **full rebuild-from-scratch** of the shared `_memory_edges.jsonl`. ~23 concurrent rebuilds (plus a
  second window doing the same) raced on that one file's atomic write — whichever landed last silently
  dropped edges another had just added. Next `plan-schema-audit` sweep saw `edge_documents_present`
  (REQUIRED) missing for ~15 plans that were actually fine — including several this same run had just
  fixed a *different* gap on — and re-filed ~28 fresh backfill jobs (J-0081–J-0119 range). **Confirmed
  the mechanism directly**: ran one clean, non-concurrent `build_edges.py`, and every "missing" edge
  for `capacity_to_commit`/`executive_world_grounding`/`wood_upgrade` was instantly restored. Fixed in
  `job-run/SKILL.md`: Tier 1/2 agents now verify with `plan_sync_check.py` only (single plan, no
  shared-file rewrite), never call `plan_maintain.py` themselves; the orchestrator runs it exactly
  once, after the tier finishes. Documented in `reference_nascence_job_run_tool.md` alongside
  `[[feedback-test-isolation-live-stores]]` (same shared-store-race class of lesson as `lab_env.py`).
- Ran one clean `plan_maintain.py` pass myself after the pilot to settle the edges file and get an
  honest current count before reporting back.

## Key findings

- **Real, reproduced bug, not speculation**: parallel agents each independently doing a "full rebuild
  from scratch" of a shared file is unsafe even when each individual agent's own work looks isolated
  (same shape of lesson as the J-0005 DB-leak incident that produced `lab_env.py`, just at the
  toolchain-orchestration layer instead of inside Du's own code).
- `file_or_refresh_job` (the shared job-filing mechanism) doesn't proactively re-verify a gap on an
  *existing* open job when a fresh sweep runs — it only refreshes if new content differs from stale
  content, and doesn't re-check "is this gap even still real" for jobs already sitting open. That
  means some of J-0081–J-0119 are already stale (their real gap was fixed by my post-pilot clean
  rebuild) but still show the old, now-wrong briefing. Not fixed this session — noted as a possible
  follow-up (see Open threads).
- `plan_index.py`'s ROADMAP-vs-plan stage matching reads the *nearest section header*, not each plan's
  own inline bullet badge — J-0050's finding, not yet turned into its own job.

## Open threads

- **J-0081–J-0119 (~28 jobs) need a fresh, honest triage before any more agents touch them** — most
  are likely already resolved by the clean rebuild I ran, but their briefings weren't proactively
  refreshed. Re-run `plan-maintain` once cleanly, then check `job_run.py plan` again before trusting
  the count. ~12 of the 39 in that range are genuinely new discoveries (plans not in the original
  35-job Tier-1 list: `epistemics_phase_c`, `hud2_visual`, `investigation_deepening`,
  `item_and_population_factories`, `ramses_second_tier`, `social_world_school`, `t4_watershed`,
  `train_courier_cargo_ids`, `transport_manager`, `world_census`, `idle_executive_plan`,
  `du_pulse_rebuild`) and those ARE real.
- **Tier 3 untouched by design** — Travis explicitly chose "Tier 1+2 only (pilot)" over running any of
  the 31 real-work jobs across 30 plan-groups. Ready to go (`job_run.py plan --json` still resolves
  it) whenever he wants to scope a batch.
- **J-0053 and J-0050** need a founder call / a `plan_index.py` parser fix respectively — not more
  agent-dispatch as currently scoped.
- **D-0014, D-0015, D-0016** are open, waiting on Travis's read (`/decide-review` will surface them).
- Possible future fix, not built: have `plan-schema-audit` proactively re-verify an already-open job's
  gap on every sweep (not just file new ones when the exact `source` has no open row) — would close
  the "stale open job" gap noted above more directly than the "agents don't call plan_maintain
  themselves" fix alone.

## Warnings

- **A second Claude Code window was actively working this same project/store concurrently during this
  session** (confirmed via that window's own handoff note visible in `MEMORY.md`'s recent additions).
  No data corruption observed in `job_queue.jsonl` itself (JSONL appends/rewrites survived), but this
  is exactly the collision risk that produced the edge-rebuild bug above. Check current
  `job_queue.py list` state before assuming any job id's status matches what this handoff says.
- Don't dispatch a fresh Tier 1 batch against the J-0081–J-0119 range without re-running
  `plan-maintain` once (cleanly, non-concurrently) first — several are already stale.

## Pointers

- `~/.claude/skills/job-run/SKILL.md`, `job_run.py` — the new skill, including the concurrency-bug
  writeup in its own "Known limitations"-adjacent section.
- `~/.claude/skills/job-queue/SKILL.md` — "Batch-working the backlog" cross-link.
- `memory/reference_nascence_job_run_tool.md` — full incident writeup, linked from `MEMORY.md`.
- `C:\Nascence\docs\job_queue.jsonl` — the store; `C:\Nascence\docs\reviews\plan_schema_audit.md` and
  `plan_maintain_run.md` — latest reports from the post-pilot clean rebuild.
- Workflow run `wf_6b477918-b21` — full per-agent journal for the pilot dispatch.
