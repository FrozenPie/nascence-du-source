# Session handoff — built /plan-schema-audit, then extended job-filing across the planning toolchain

## Session timing
- **Session started:** 2026-08-23 09:12:13 UTC
- **Last message before wrap:** 2026-08-23 09:59:52 UTC
- **Wrapped:** 2026-08-23 09:59:55 UTC

## Summary

Started from a `/session-resume` catch-up, then a founder ask to reinforce the tuple/indexing
discipline carried over from Du's own `core/memory_edges.py`: build a skill that sweeps every
Nascence plan against a schema of known index fields and auto-queues backfill work. Built
`/plan-schema-audit` from scratch (extensible `FIELD_CHECKS` list, one job per plan with a required
gap), wired it into `/plan-maintain`, then in two follow-ups wired its `claims_a_real_file` field to
real `plan-files-audit` resolution and added two new `memory_edges`-style tuple checks read directly
from the shared edge graph. A final, broader ask ("a lot of these skills should be making jobs to
resolve problems and answer questions") led to auditing the rest of the toolchain for report-only
findings that deserved job-filing, discovering mid-session that a concurrent window had just built
`/gauge-check` for exactly the plan-liveness half of that ask — so that part was left alone, and the
gap it doesn't cover (ROADMAP/decision hygiene, stage-mismatch tracking) got filled instead.

## What changed

- **Built `~/.claude/skills/plan-schema-audit/`** (`plan_schema_audit.py` + `SKILL.md`) — sweeps all
  56 plans against an extensible field schema (`FIELD_CHECKS`, append-one-dict to extend), files a
  `category: backfill` job-queue entry per plan with a required gap. Currently 10 fields: 4
  structural (Status line, Current State section, ROADMAP link, memory file), 3 memory-frontmatter
  (`name`/`description`/`metadata.type`), 3 tuple (`claims_a_real_file`, `edge_documents_present`,
  `no_open_overlap_edge`).
- **Real-data corrections made along the way** (see Key findings): `current_state_section` demoted
  `required`→`recommended` after a live run would have filed 49/56 near-duplicate jobs;
  `claims_a_real_file` wired to `plan_files_audit.py`'s real `extract_refs`/`resolve_ref`/
  `ref_is_only_candidate` (imported, not reimplemented) instead of staying a placeholder.
- **`edge_documents_present` (required) and `no_open_overlap_edge` (recommended)** added — read
  directly from `_memory_edges.jsonl` via a new `load_edge_lookups()`. Caught 2 real stale-graph
  plans and reproduced exactly the 6 known-open overlap-audit finding-groups with 0 noise.
- **Found and fixed a real bug**: an existing open job's briefing could go stale when a NEW required
  field got added to the schema after that job was filed (dedup only checked "does a job exist," not
  "is its content current"). Fixed by refreshing an existing job's `briefing` in place when computed
  content changes — this became the seed for the shared helper below.
- **Built `common.py`'s `file_or_refresh_job(jq, rows, source, title, briefing, ...)`** — the
  create-or-refresh-by-exact-source-string mechanism, extracted out of plan-schema-audit so the next
  tool wanting this didn't reimplement it. Refactored plan-schema-audit onto it.
- **`~/.claude/skills/plan-index/plan_index.py`** — `collect_rows()` now also returns
  `doc_status`/`roadmap_snippet`/`memory_desc` (raw per-source text, additive, no existing caller
  broken — checked `gauge-check`/`plan-snapshot`, both dict-key access only). New
  `file_mismatch_job()` files ONE aggregate job (`J-0050`, source `plan-index:stage-mismatches`)
  listing all ⚠-mismatched plans — checked real volume first (23/56 plans) before deciding this
  should NOT be one-job-per-plan.
- **`~/.claude/skills/plan-maintain/plan_maintain.py`** — new `file_lint_jobs()` files one job per
  ROADMAP orphan link (`J-0051` `contradiction_rearchitecture_plan`, `J-0052`
  `evidence_review_dashboard`) and bad `decisions.jsonl` plan slug (`J-0053`, `D-0013` →
  `factory_stations`). Deliberately NOT for the two high-volume lint findings (missing Status/Current
  State) or the cosmetic ones (underscore memory names, unharvested review docs).
- **`job_queue.py`**: added the `backfill` category + `--category` filter to `list`/`next` (this
  session); a CONCURRENT session substantially reworked the same file mid-session (new
  `isolation`/`spawned_from` fields, a `spawn` command, `CATEGORIES` constant) — adapted
  plan-schema-audit to build jobs via `jq._make_record()` instead of a hand-rolled dict so it can't
  drift from that schema.
- **Memory**: new `reference_nascence_plan_schema_audit_tool.md`,
  `reference_nascence_job_filing_across_toolchain.md` (the "who files what, and the volume test that
  decides who doesn't" reference); `MEMORY.md` pointers updated (twice — once more by a concurrent
  session adding `/gauge-check`'s own entry, left as-is).
- **`docs/job_queue.jsonl`**: grew from 7 rows to 62+ over the session — 35 backfill (`J-0008`..
  `J-0042`), 1 aggregate mismatch (`J-0050`), 2 roadmap-orphan (`J-0051`/`J-0052`), 1 bad-slug
  (`J-0053`) from this session's own work; the rest (`J-0044`/`46`/`47`/`48`/`49` and others) from a
  concurrent session actively using `/gauge-check`.

## Key findings

- **The volume-before-severity lesson, learned twice this session and now written down**: a field/
  finding that LOOKS like a simple presence check can turn out to be systemic (49/56 plans missing
  Current State, 23/56 stage-mismatched) rather than a rare bug. Both times the fix was the same
  shape — demote to `recommended`/report-only, or collapse to ONE aggregate job — not tune the
  threshold. Apply this test before adding any new auto-filed job anywhere in this toolchain: run it
  for real first.
- **`/gauge-check` already exists and is the correct owner of plan-liveness→job-queue**, built by a
  concurrent session the same day, confirmed actively in use mid-session (5 real jobs appeared,
  including the exact `capacity_to_commit` "THE BIG ONE" example already in its own SKILL.md).
  Deliberately did NOT add auto-job-filing to `plan_liveness.py` itself — would have duplicated or
  raced with `gauge-check`'s judgment-in-the-loop design (`triage` reads, a session scopes+spawns
  manually). This is now documented in `reference_nascence_job_filing_across_toolchain.md` so it
  doesn't get "fixed" into a duplicate mechanism later.
- **`claims_a_real_file` validated against real ground truth**, not just unit-tested: flagged
  `transport_manager` and `world_census`, both independently confirmed against
  `plan_files_evidence_audit.md`'s own MISSING list — 0 false positives, and correctly excluded a
  genuinely proposed-only ("candidate") filename in `transport_manager`'s data-file claim.

## Open threads

- **35 backfill jobs sit open and ready** (`job_queue.py list --category backfill`) — mostly missing
  Status lines, a handful of ROADMAP links/memory-file gaps. Nobody's picked these up yet.
- **`J-0050`** (23-plan ROADMAP stage-badge sync), **`J-0051`/`J-0052`** (dead ROADMAP links),
  **`J-0053`** (bad decision slug on `D-0013`) — all open, all `category: analysis`, all
  self-contained enough to hand to a fresh window.
- **Deliberately deferred, not built**: `plan-liveness`'s `NEVER-FIRED`/`STALE` verdicts (12 and 2
  respectively, real volume checked) still have no auto-job path — left for `/gauge-check` to own if
  it proves insufficient, not duplicated here. `claims_a_real_file`-family checks don't yet cross-
  reference `plan-liveness`'s own findings (a plan could theoretically pass one and fail the other on
  the same underlying file) — no conflict observed yet, but not proven absent either.
- **18 `docs/reviews/*.md` still unharvested by `memory-links`** (only `plan_overlap_audit_*.md` is)
  — flagged by `plan-maintain`'s lint every run, never turned into a job (a meta-tooling extension,
  not a per-item task) — see `docs/reviews/index_coverage.md`.

## Warnings

- **Multiple concurrent windows were active on this project for this session's entire duration** —
  confirmed directly (`job_queue.py` reworked mid-session by another window; `MEMORY.md` edited
  concurrently at least twice with a `/gauge-check` entry this session didn't add). Re-read
  `job_queue.py`, `plan_maintain.py`, `MEMORY.md` fresh before editing any of them again.
- **Job-queue volume jumped from ~7 to 62+ rows this session** (combination of this session's own
  filing and concurrent `/gauge-check` activity) — if `job_queue.py list` (no filter) feels
  overwhelming now, use `--category backfill`/`--category analysis`/`next` (which still correctly
  ranks hand-curated ⭐⭐⭐+ founder work above the machine-filed ⭐⭐ jobs, confirmed this session).
- Every new job-filing addition in this session ends with a full `/plan-maintain` rerun confirming
  idempotency (0 duplicates) — if you add a new auto-filed finding anywhere, follow the same pattern:
  test standalone, then a full pipeline run, then rerun again to confirm nothing duplicates.

## Pointers

- `~/.claude/skills/plan-schema-audit/plan_schema_audit.py` + `SKILL.md` — the tool this session was
  mostly about; `FIELD_CHECKS` is the extension point for any future index-field convention.
- `~/.claude/skills/_plan_tools_common/common.py` — `file_or_refresh_job()`, the shared job-filing
  mechanism now used by 3 tools.
- `~/.claude/skills/plan-index/plan_index.py` (`file_mismatch_job`) and
  `~/.claude/skills/plan-maintain/plan_maintain.py` (`file_lint_jobs`) — the two other new job-filing
  sites.
- `~/.claude/projects/C--FreshStart/memory/reference_nascence_job_filing_across_toolchain.md` — read
  this before adding job-filing to any other tool; it has the full "who files what, and why some
  findings deliberately don't" picture plus the volume-test rule.
- `~/.claude/skills/gauge-check/` — not touched this session, but load-bearing to the reasoning above;
  read its own SKILL.md before considering any plan-liveness-driven job-filing.
