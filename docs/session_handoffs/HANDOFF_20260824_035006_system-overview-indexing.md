# Plan-toolchain cleanup + System_Overview.html indexing, tuple extraction, 4 real toolchain bugs found

## Session timing
- **Session started:** 2026-08-24 01:38:02 UTC
- **Last message before wrap:** 2026-08-24 03:50:03 UTC
- **Wrapped:** 2026-08-24 03:50:06 UTC

## Summary

Opened as a routine plan-index/tuples/backfill cleanup continuing the previous session's work
(`/session-resume`, `/plan-maintain`, backfilled `du_initiated_upgrade_trigger`'s missing index
fields — **J-0208 done**). The founder then redirected to `docs/System_Overview.html` (a 1,272-line
narrative architecture doc, Build 1.3.0/2026-07-04) flagged as "outdated for sure." That grew into
three escalating passes: (1) confirm + quantify the staleness and register the doc in the
memory-links toolchain for the first time ever, (2) convert the full doc to Markdown and measure
the real drift against the live filesystem (a precise diff, not a guess), (3) extract the doc's
content into a real 154-tuple structured index with plan-ownership resolved against the toolchain's
own edge store. Each pass surfaced a genuine, verified bug in the toolchain itself (not in Du's
runtime code) — all four are now logged findings with jobs filed, plus one softer skill-manager
suggestion, matching this project's "findings become jobs, not just chat" rule.

## What changed

**Files created/edited (Nascence):**
- [`docs/ROADMAP.md`](../ROADMAP.md) — added a `🟢` bullet for `du_initiated_upgrade_trigger.md`
  next to its `*_upgrade.md` siblings (J-0208 backfill).
- [`docs/System_Overview.html`](../System_Overview.html) — added a `.note.amber` staleness banner
  (links every plan that supersedes stale content, points at `ROADMAP.md`/`docs/plans/` as
  authoritative, later updated to link the new `.md` conversion + cite the File Manifest Drift
  numbers).
- **[`docs/System_Overview.md`](../System_Overview.md)** *(new)* — full, faithful Markdown
  conversion of the HTML (all tables, node/faculty/tier registries, biological grounding table,
  dated event timeline; the giant architecture mermaid diagram summarized with a pointer rather
  than reproduced) plus a new "File Manifest Drift" section not in the original.
- **[`docs/system_overview_index.jsonl`](../system_overview_index.jsonl)** *(new)* — 154 typed
  tuples extracted from `System_Overview.md` (16 nodes, 3 pre-cortex reflexes, 6 no-LLM faculties,
  6 Consciousness Program mechanisms, 63 File Manifest `core/` entries, 20 `scripts/` entries, 9
  invariants, 6 failure classes, 15 biological groundings, 10 timeline events), each with
  `file_path`/`file_exists_now`/`plan_slugs`/`plan_resolution`/provenance. Build script at
  `<scratchpad>/build_so_index.py` (not committed anywhere permanent — the JSONL output is the
  artifact that matters).
- [`docs/plans/garden_upgrade.md`](../plans/garden_upgrade.md) — added a reciprocal `Related` note
  linking `wood_upgrade.md` back (F-0263: it cited garden one-directionally).
- [`docs/plans/memory_knowledge.md`](../plans/memory_knowledge.md) — added a reciprocal `Related`
  note linking `docs/staged/geometry_tuple_index.md` back (same F-0263 pattern).

**Claude memory files (touched or new):**
- `reference_nascence_system_overview.md` *(new)* — the full narrative of this doc's journey this
  session (stale → indexed → converted → tuple-indexed), with real `[[project-nascence-<slug>]]`
  wikilinks (fixed twice after F-0265 caught dangling ones — see Key findings).
- `project_nascence_du_initiated_upgrade_trigger.md` *(new)* — J-0208's backfill.
- `MEMORY.md` — new entries for both of the above; also compacted from 19.6KB→~17.1KB per the
  harness's own size-limit hook (unrelated content trimming, several existing entries shortened,
  one 4-entry session-handoff chain merged into one line — no content lost, just tightened).

**Findings + jobs (all `--session c284760a-1460-418c-bb01-131de742cdcb`, full detail in each):**
- **F-0263** → **J-0225** (extend `build_edges.py` to harvest plan-doc-to-plan-doc prose refs) +
  **J-0226** (review the remaining ~35 `pattern_discovery.py` [NEW] pairs, after J-0225 lands).
- **F-0264** → **J-0227** (the real System_Overview.html 1.4.0 narrative rewrite — not attempted
  this session, deliberately).
- **F-0265** → **J-0228** (`harvest_memory_files()`'s wikilink harvester doesn't validate targets).
- **F-0266** → **J-0229** (group the 307 undocumented `core/`+`scripts/` files by owning plan,
  mechanical prep ahead of J-0227).
- **F-0267** → **J-0230** (investigate the 6-file Error Pathway/Self-Knowledge orphan cluster —
  zero plan coverage, mixed liveness signal).
- **F-0268** → **J-0231** (`plan_sync_check.py` has no `--session` support at all, but
  `common.py`'s shared warning tells every caller to use it anyway — following that advice
  corrupts the tool's own output).
- **S-0002** (skill-manager suggestion, not a job) — `job_queue.py` has no `update`/edit command;
  hit this twice this session working around it by chaining new jobs to old ones instead.
- **J-0208 → done** (the session's one completed mechanical backfill).
- **T-0014** — this session's opening thought-log capture.

## Key findings worth remembering

- **System_Overview.html's problem is coverage, not accuracy.** Diffing its 07-04 File Manifest
  against the live filesystem found **zero** deleted/renamed files — every mechanism it names is
  still real. The gap is pure, measurable addition: `core/` grew 62→201 (139 undocumented),
  `scripts/` grew ~20→187 (168 undocumented). This reframes the eventual 1.4.0 rewrite (J-0227) as
  primarily an ADDITION task, not a correction task.
- **The 154-tuple index found a real, verified backfill-candidate pattern on its first pass**
  (F-0267): of 111 file-backed tuples, 39 resolve to zero current plans. Two distinct shapes: (a)
  6 of the 16 core cognitive nodes (perception/salience/memory_router/critic/consolidation/
  meta_awareness) — likely benign, the more settled half vs. the actively-evolving nodes that DO
  have plans; (b) a coherent 6-file Error Pathway/Self-Knowledge cluster with genuinely mixed
  liveness (`error_pathway.py` touched 08-19, its 5 siblings not since June) and its own doctrine
  docs (`error_pathway_charter.md`, `task_constraint_effector_spec.md`) missing entirely from
  `docs/*.md` — queued as J-0230 rather than guessed at.
- **Plan-to-plan prose relationships are invisible to the memory-links graph** (F-0263): checked
  the top 3 `pattern_discovery.py` "[NEW]" pairs by reading the actual plan text — all 3 were
  ALREADY explicitly cross-referenced in prose (`emissary_lane2.md`↔`lane2_the_witness.md` fully
  both ways; `wood_upgrade.md`→`garden_upgrade.md` and `geometry_tuple_index.md`→`memory_knowledge.md`
  one-directionally). `build_edges.py`'s `harvest_plan_files()` only ever produces
  `claims_file`/`shares_file` edges from backtick code/data refs — it never scans a plan's own body
  text for mentions of another plan, unlike `harvest_memory_files()` for memory files. This makes
  `pattern_discovery.py`'s "[NEW]" flag a real false-positive source until J-0225 lands.
- **The memory-file wikilink harvester has zero target validation** (F-0265), caught live: this
  session's own first draft of `reference_nascence_system_overview.md` used bare plan slugs like
  `[[t4_watershed]]` (not a memory file's real `name:`) and silently produced dangling
  `memory→memory` edges to non-existent nodes — no error, no warning. It doesn't even respect
  code-span backticks (a *description* of the bug using `` `[[x]]` `` as an example still got
  parsed as a real link and created a bogus edge to node "x"). Had to fix the file twice before the
  edges came out clean. Its sibling `harvest_capture_references()` (idea/thought wikilinks) already
  does this right — validates and reports `unmatched` instead of writing garbage.
- **A tool's own warning can be actively wrong for that specific tool** (F-0268): `common.py`'s
  shared `log_event()` helper prints "If this command takes --session, re-run with it" on every
  call regardless of whether the calling script's CLI has a `--session` flag at all.
  `plan_sync_check.py` doesn't — acting on its own tool's advice corrupted the real check output
  with two bogus `[MISSING] file does not exist` entries.

## Open threads

- **J-0223 remains open and untouched** (the pre-existing `geometry_tuple_index.md` ROADMAP-link
  conflict from the prior session) — still needs a founder call, not resolved either way this
  session.
- **J-0225 through J-0231 are all open, unstarted.** J-0227 (the real System_Overview.md rewrite)
  and J-0230 (the Error Pathway cluster investigation) are the two with real judgment-call content;
  the rest (J-0225, J-0226, J-0228, J-0229, J-0231) are more mechanical/build fixes to the toolchain
  itself.
- **S-0002 is an open skill-manager suggestion**, not yet a job — worth promoting to a real job if
  the `job_queue.py update` friction recurs again.
- **The 4 orphaned pre-Bonsai memory files** (`project_nascence.md` era 2026-05-29,
  `project_nascence_biological_grounding.md`, `project_nascence_introspective_recurrence.md`,
  `project_memory_systems_roadmap.md`) that reference `System_Overview.html` but aren't in
  `MEMORY.md`'s index — founder explicitly deferred this cleanup to a separate task, still
  genuinely open.
- **`docs/system_overview_index.jsonl` has no query tool yet** — it's a raw JSONL store, same shape
  as `_memory_edges.jsonl` but standalone. Nobody's written a `query.py`-equivalent for it. If this
  pattern (extract a doc into typed tuples, resolve plan ownership, mine for orphans) proves useful
  again on another doc, a small shared script for "diff a tuple index's file_paths against
  claims_file edges" would be worth generalizing rather than re-writing `build_so_index.py`'s logic
  each time.

## Warnings

- **`_memory_edges.jsonl` is rebuild-from-scratch on every `build_edges.py`/`plan-maintain` run for
  its OWNED_EDGE_TYPES** (references/originated_in/documents/claims_file/shares_file) — don't hand-edit
  it expecting a change to survive; edit the source memory file/plan doc and re-run the rebuild.
- **Any future memory file using `[[double-bracket]]` syntax must double-check the bracket target is
  a real memory file's `name:` frontmatter slug**, not a plan's bare slug — see F-0265. Until J-0228
  lands, the harvester will silently write a dangling edge for a mistake like this with no warning
  at all.
- **`docs/System_Overview.html`'s Consciousness Program section is explicitly flagged superseded**
  (banner added this session) — the keystone/AST-1 picture it shows is pre-correction; read
  `the_consciousness_program.md` for current status, not that section.

## Pointers

- `reference_nascence_system_overview.md` — the fullest single account of this session's
  System_Overview.html work, with real wikilinks into every plan touched.
- `docs/system_overview_index.jsonl` + the orphan list printed in this session's tool output — the
  concrete backfill-candidate data, if picking up J-0230 or exploring further patterns.
- `docs/reviews/plan_schema_audit.md` / `plan_liveness_audit.md` — refreshed this session, current
  as of the last `plan-maintain` run (03:27 UTC).
- `job_queue.py list` / `decide.py list --open` — live state; this handoff is a snapshot, not a
  substitute.
