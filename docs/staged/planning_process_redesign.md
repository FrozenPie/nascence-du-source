# Planning Process Redesign — plans as design + one state block, history derived not written

**Status:** 🟡 BUILT (2026-09-27, I-0083) — the three tools exist and have run once over the whole plan set; the reader migration, the generated ROADMAP rows and the hand-compaction of the bullet-shaped giants are queued (see `next:` and the open jobs).

```plan-state
stage: built
phase: Tools built + first full pass done; readers not yet migrated
verified: 2026-09-28
next: Cite F-2197/F-2198 as added evidence when S-0222 is next reviewed in the skill-suggestion backlog.
cluster: 8
```

## Current State — verified 2026-09-28
- **2026-09-28** (F-2199): J-1602 (from F-2164) audited the other 9 F-2045 batch-4 plans for the same cross-plan stale-gap pattern. 2 of 9 confirmed stale: memory_knowledge (F-2197, Improvement 2 gap already closed under memory_multiway_linking) and ramses_second_tier (F-2198, D-0297 under lane2_the_witness not cross-referenced). 7 of 9 checked clean (F-2199 has the per-plan detail). S-0222 already tracks the structural plan_ledger.py fix this recurring pattern argues for.

- **2026-09-28** (F-2148): D-0315 ruled: idle_executive_plan.md's 40KB SIZE_CAP overage accepted as a permanent, generic per-plan lint exception in plan_state.py (SIZE_CAP_EXCEPTIONS dict); lint --all verified it no longer flags idle_executive_plan and all other over-cap plans are unaffected.
- **2026-09-28** (F-2096): memory-links harvests docs/plan_history now (J-1487, F-2096). Measured before building: 46% (882 of 1908) of claims_file/plan-plan-reference edges the pre-compaction plan text produced are gone from what live plan-doc text produces today, since plan-compact's folded prose sits unscanned in docs/plan_history -- not a near-zero case. Built and shipped: a history node kind (id = plan slug) in build_edges.py, with a history_of edge plus a second claims_file/references/wikilink pass sourced from each docs/plan_history/<slug>.md file, provenance naming the history file. Ran the real rebuild live: +871 new edges (797 claims_file, 39 plan-plan references, 33 history_of, 2 wikilinks), verified via query.py on both plan: and history: nodes. SKILL.md updated. D-0313 (open, a cluster-field editorial question from unrelated job J-1502) left untouched -- not sourced from this job.

- **2026-09-28** (F-2077): J-1495 (F-2042 follow-up, this finding F-2077): idle_executive_plan.md's 40 KB SIZE_CAP flag is not fixable by plan_compact.py -- it has only one, already-condensed Current State heading, so there is nothing to fold; the overage is Sections 0-12, the auditor design body, which is load-bearing design reasoning per rule 4 above, not foldable history. Opened D-0315 for Travis: accept a permanent cap exception vs hand-trim the design body. Filed two skill-manager suggestions, on plan-state's lint remedy message and job-queue's isolation default for kind=test jobs.
- **2026-09-27** (F-2050): J-1486 done: ROADMAP rows shipped as plan_index.py's new By Cluster section (mirrors ROADMAP's own numbering), not a replacement of ROADMAP's bullets -- that full-replacement idea was read closely and declined after evidence, see F-2050 and section 3. Surfaced J-1502/S-0203 (16 plans with cluster: top).

- **2026-09-27** (F-2046): J-1483 checked: fields real on 96 plans, 7 defect jobs spawned, cap count 24->13. Its --touch pass exposed my verified/evidence_read conflation: liveness UNREAD 176->1; split the field, restored 76 pre-pass dates, UNREAD back to 129 (F-2046).
- **2026-09-27** (F-2034): First post-compaction plan-maintain: liveness lost last-verified on 59 rows (kept headings say updated/bare date); fixed by making parse_last_verified prefer the plan-state block (F-2034). 136 liveness rows gone = evidence files only cited in folded history; gate: per plan (J-1483) is where they belong now.

- **Founder ruling (2026-09-27, in conversation):** the ROADMAP "and other bits are good ideas but I do not think they are sufficient. The plans are full of so much history they are hard to read and add to." Approved: derived ledger, one state block, one-time compaction, generated ROADMAP rows, an add-to-a-plan command, decisions as the pointer for open questions. **Declined:** collapsing the plan folders into one — `plans/`, `staged/`, `shelf/`, `completed/`, `archive/` stay.
- **Built today:** `/plan-ledger` (derived timeline per plan from the five ledgers), `/plan-state` (the block; `show/init/set/sync/lint/note`), `/plan-compact` (fold dated Current State sections into `docs/plan_history/<slug>.md`, dry-run default, id-audited, git-dirty-guarded).
- **Run today:** 23 plans compacted (1.4 MB of dated sections folded out, 0 unknown ids); 94 plans given a state block. `stage:` was guessed by word-match on the Status line and `next:` is blank everywhere except here — both are placeholders until a person or agent verifies each plan (J-1483). Lint after the pass: 1 regrowing (strings_and_sheets, being drafted in another window, deliberately skipped), 24 over the 40 KB cap (the bullet-shaped giants + long designs), 14 `verified: unknown` (no dated Current State heading ever).

## 1. The problem, measured (2026-09-27)

| Doc | Size | Dated `## Current State` sections | Ledger records naming it |
|---|---|---|---|
| world_store_write_fence | 459 KB | 91 | 118 findings, 93 jobs |
| lane2_the_witness | 295 KB | 1 section, 132 KB long (bullets) | 102 findings, 80 jobs, 22 decisions |
| dosed_coupling | 130 KB | 33 | 72 findings |
| actions_expansion | 224 KB | 53 | — |

Mechanism: the one `## Current State — verified DATE` section introduced 2026-08-23 was **appended per job** (job-run SKILL.md step 6: "Update the plan doc's Current State section with a dated note") because plan-liveness credits a plan by the date on its newest verified heading. Every appended section cites J-/F-/D- ids that already hold the same content in the ledgers, which carry a `plan` slug on 73% of findings, 77% of jobs, 97% of decisions. The plan doc was a hand-written second copy of a machine-readable ledger — and the copy was the one people had to read.

## 2. The design

A plan doc is **design + one ```plan-state block + one Current State section**. Nothing else accumulates in it.

| Need | Where it lives now | Tool |
|---|---|---|
| What happened on this plan | derived from findings/jobs/decisions/ideas/thoughts by slug | `plan_ledger.py <slug>` |
| What is true now | the ```plan-state block (stage, phase, verified, gate, next, open_decisions, history, cluster) | `plan_state.py show/set/sync` |
| Adding a line after a job | ONE dated bullet under the kept Current State heading + re-stamp | `plan_state.py note` (after `findings_log.py record --plan`) |
| The prose that had accumulated | `docs/plan_history/<slug>.md`, verbatim, append-only | `plan_compact.py` |
| Open questions | decide, by plan slug; the block's `open_decisions:` is derived from it | `decide.py`, `plan_state.py sync` |
| Regrowth | lint: one Current State heading, 40 KB cap, block present | `plan_state.py lint --all`; plan-schema-audit carries the same checks as recommended fields |
| ROADMAP rows | NOT a replacement for ROADMAP's own bullets (see §3 — declined after review) — instead a new "By Cluster" section in `plan_index.py`'s existing generated table (`memory/project_nascence_plan_index.md`), grouping every plan by `cluster:` and showing `stage:`/`phase:`/`next:`/`verified:`/open-decisions straight from the block, mirroring ROADMAP's own `### N ·` numbering via `roadmap_cluster_headings()` | done (J-1486) |

The fenced block inside the doc is this project's existing convention (```shadow-promotion, read by plan-shadow-read); `key: value` lines only, no YAML dependency. `open_decisions:` is the only derived field and `set` refuses to hand-edit it.

## 3. What is NOT done yet (the open jobs)

- **Real state lines.** `stage:` guessed, `next:` blank, and the kept Current State section is often the last narrow job note rather than a summary. One pass per plan with judgment — J-1483.
- **Bullet-shaped giants.** lane2_the_witness, social_world_school, train_split_merge, geometry_tuple_index, memory_multiway_linking, the_consciousness_program keep history as multi-line bullets under a single heading; plan-compact v1 cannot fold that shape — J-1484.
- **Reader migration.** plan-index, plan-liveness, plan-snapshot still regex the Status line and the verified heading; they should prefer the block when present — J-1485.
- **Generated ROADMAP rows — done, but not as originally scoped (J-1486, 2026-09-27).** The literal
  original ask (fully replace ROADMAP's own per-plan bullets with a generated one-liner, migrating any
  "non-derivable" prose into the plan's own doc or the cluster paragraph) was read closely against the
  real doc first — every cluster checked (0, 7, 8, 9, 10) turned out to be dense, specific,
  hand-written paragraphs (founder rulings, cross-plan relationships, exact numbers), not thin status
  lines; cluster 9 additionally has bullets with no corresponding plan doc at all. Raised to the
  founder before building anything; their own response ("a tuple? an index? a new higher-up document,
  leave ROADMAP just with the gaps filled? a combination?") became the shipped design: a new "By
  Cluster" section in `plan_index.py`'s own pre-existing generated table
  (`memory/project_nascence_plan_index.md`), grouping every plan by `cluster:` with `stage:`/`phase:`/
  `next:`/`verified:` straight from the block, mirroring ROADMAP's own numbering — ROADMAP.md's prose
  is untouched, not one bullet replaced or migrated. The 3 plans with no ROADMAP link at all
  (`strings_and_sheets`, `golden_spiral_recall`, `conversational_action_bridge`) are covered by
  `plan-schema-audit`'s own pre-existing Tier-1 backfill jobs (J-1480/1481/1482), not by this change.
  Full evidence: F-2050. A real data-quality gap surfaced in passing — 16 plans hold the literal string
  `cluster: top` instead of a real number — filed as J-1502 (fix) and S-0203 (validate `cluster:` in
  `plan_state.py set`, the way `stage:` already is).
- **memory-links** does not harvest `docs/plan_history/` — the folded prose's `[[links]]` and backtick refs are out of the edge graph until it does — J-1487.
- **strings_and_sheets** compaction once its author's window is done — J-1488.


> **Job-id note (2026-09-27):** the six briefs above were written naming J-1464..J-1469 but other windows added jobs first, so they landed as J-1483..J-1488 (same order). Inside the stored briefings, read J-1464→J-1483, J-1465→J-1484, J-1467→J-1486. job-queue has no `amend` (S-0199), so the ledger copies stay as written.

## 4. Rules for every session from here (supersedes job-run step 6's "dated note")

1. After a job: `findings_log.py record ... --plan <slug>`; then `plan_state.py note <slug> --text "..." --finding F-XXXX [--next "..."]`. Never add a `## Current State` heading. `verified:` means the DOC was checked; `evidence_read:` means the evidence LOGS were read (plan-liveness's UNREAD keys on it) — add `--evidence-read` to `note` only when that is literally true (F-2046).
2. Before reading a plan: `plan_ledger.py <slug> --since <its verified: date>`.
3. If `plan_state.py lint` says a plan is regrowing or over cap: `plan_compact.py <slug>` (dry-run, read it, then `--write`).
4. Design changes go in the design sections. State changes go in the block. History goes nowhere by hand.
