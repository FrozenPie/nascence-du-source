# Geometry Tuple Index — full design session (archaeology → SOTA research → docs-folder test)

## Session timing
- **Session started:** 2026-08-23 20:04:26 UTC
- **Last message before wrap:** 2026-08-23 23:03:25 UTC
- **Wrapped:** 2026-08-24 01:31:26 UTC

## Summary

Started from a founder+Gemini brainstorm (idea I-0023) about a "topological manifold" architecture for
Du, drawing on a predecessor project's (`C:\FreshStart`) ABF/Pinnacle compression archaeology. Two rounds
of code-reading corrected the extrapolation to what's real (F-0243–F-0250). After an early draft wired
the idea as a live child-plan of `cognitive_geometry.md`, the founder explicitly corrected course:
**this must stay outside Du's active architecture entirely** — an external tool, thought-experiment only,
several real plans already touch this territory. Resolved by writing everything to
`docs/staged/geometry_tuple_index.md`, deliberately unlinked from ROADMAP.md. The rest of the session
built that document out through: a systematic 59-plan consumer survey (F-0251, 6 real hits), three rounds
of real SOTA literature research (F-0252–F-0254, F-0258–F-0259), independent verification of two external
AI reviews (Gemini and GPT, F-0255/F-0256 — corrected as much as adopted), real read-only benchmarks
against live Nascence data (F-0261), and a real disparity-filter test over the docs folder itself that
surfaced a previously-unweighted connection to `memory_knowledge.md` (F-0260, F-0262).

## What changed

**Files created:**
- `C:\Nascence\docs\staged\geometry_tuple_index.md` — the main deliverable. Grew from a narrow single-
  field checkpoint-index idea into an 11-section staged design covering three dimensions (Time/Knowledge/
  Memory), a real indexing-technique toolkit, a cascaded/per-band compression direction (explicitly the
  most speculative section), the real 6-plan consumer baseline, a gated build order (P0→P3), 8 guards,
  full SOTA citations, 6 frontier extensions, and a real inventory/backfill audit. Deliberately still has
  zero ROADMAP.md link and no `cognitive_geometry.md` parent relationship.
- `C:\Users\USER\.claude\skills\memory-links\pattern_discovery.py` — new, real, reusable tool (not a
  one-off). Read-only disparity-filter/rarity-weighted analysis over the `memory-links` edge store;
  `--new-only` flag surfaces plan-pairs with real shared substrate but no existing recorded relationship.
- `C:\Users\USER\.claude\projects\C--FreshStart\memory\project_nascence_geometry_tuple_index.md` —
  companion memory file, kept current with the doc's growth across the session.

**Findings logged (all `--session c01d1276-...`):** F-0243 through F-0262 (20 findings) — ABF/Pinnacle
archaeology corrections, the 59-plan consumer survey, three SOTA research passes, two external-review
verifications, a citation-completeness audit, the hidden-bonuses math research (Tucker/PQ/JL/compressed
sensing/concentration-of-measure), the disparity-filter technique itself, and the real benchmark results.

**Ideas/thoughts:** T-0010 (raised) → promoted to I-0023 → promoted to `geometry_tuple_index`. T-0011
(the "might need updated ROADMAP rules / higher-level linking doc" side quest, explicitly deferred by the
founder — genuinely open, not yet actioned). I-0024 (the six frontier extensions).

**Jobs:** J-0210 spawned from F-0246 (test whether ABF's dead `fold_with_checkpoints` pattern transfers
to JSONL indexing) — filed, independently actionable, has NOT been run yet.

**No decisions ruled, no ROADMAP.md edits, no Du runtime code touched.** `/plan-maintain --session ...`
run at wrap time; confirms `geometry_tuple_index` correctly shows the `roadmap_link` gap as intentional
(J-0223 already tracks it, not a bug).

## Key findings worth remembering

- **The strongest single discovery**: `memory_knowledge.md` literally owns `core/epistemic_state.py` —
  the exact live KNOW/THINK/SUSPECT/GUESS mechanism the staged doc's §2.2 Knowledge dimension is built
  from. Found by running the new `pattern_discovery.py` tool on the real docs graph, not by manual
  review. Should be treated as the closest real sibling plan, not a passing citation.
- **Du's epistemic grade is already decoupled from self-report** — verified against a real
  `provenance_log.jsonl` row (`self_reported_confidence: 0.85` vs. assigned `grade: SUSPECT`) — matches
  the strongest, most-replicated SOTA finding (verbalized LLM confidence is unreliable; only decoupled
  signals are validated). Du already does the right thing here.
- **Real join gap**: only `provenance_log.jsonl` carries an exact `cycle_id`; `moments.jsonl` and
  `geometry_tuples.jsonl` only have `ts`. Fix identified (thread `cycle_id` through to
  `moment.record()`/`geometry_census.snapshot()`) but **not implemented** — that's a Du runtime edit,
  deliberately not made this session.
- **Two external AI reviews were independently verified, not trusted**: Gemini's "async/multi-threaded
  jitter" diagnosis was wrong (orchestrator.py confirmed single-threaded/synchronous) but its proposed
  fix was right anyway. GPT's "wrong bottleneck" argument overstated its case, but its speed-vs-
  correctness conflation catch was real and got fixed at the root. Both reviews, independently, converged
  on the same trajectory observation: this design is drifting from "geometry index" toward "event-sourced
  temporal causal graph" — now named explicitly in the doc.
- **Real, honest math findings**: learned indexes are production-proven (shipped in Google Bigtable);
  Hilbert curves are legacy tech past 2-3 dimensions, now with a proven theorem (Pestov's concentration-
  of-measure result) backing that up, not just an empirical trend; compressed sensing was considered and
  honestly rejected as not fitting this data shape; a naive single-line-fit learned index performs poorly
  on real `geometry_tuples.jsonl` data (motivates piecewise/PGM-style fitting instead).
- **Real benchmark, not assumed**: weather-transition headroom confirmed on live data — 205/17,331 rows,
  ratio 0.0118, under the <0.05 prediction. Full scan baseline: 0.475s.
- **A real data-quality catch before it became a build mistake**: the `affect` field in
  `geometry_tuples.jsonl` is NOT uniformly shaped across rows — Product Quantization needs a fixed-length
  vector, so a canonical key-order/fill-missing scheme is a real prerequisite, not yet designed.

## Open threads

1. **J-0210 hasn't run** — test whether `fold_with_checkpoints` actually works and whether the pattern
   transfers to JSONL. First real gate before anything else in the build order proceeds.
2. **P1/P1.5 have zero code** — building either (weather-transition index, grade-transition index) means
   crossing the doc's own Activation guard; needs an explicit founder `/decide`, not just momentum.
3. **`cycle_id` threading through `moment.record()`/`geometry_census.snapshot()`** is a real Du runtime
   edit, identified but deliberately not made — needs a separate, explicit go-ahead, distinct from
   anything "design/discuss."
4. **Six real founder decisions are on hold in the other concurrent session** (D-0022, D-0025, D-0029,
   D-0033, D-0035, D-0041) plus D-0014/J-0220, all waiting on this design landing. Worth revisiting once
   the founder has read this doc — several (D-0022, D-0035) looked more justified on reflection than
   others (D-0025, D-0041), per this session's own read.
5. **J-0223 conflict unresolved** — a `plan-schema-audit` backfill job wants to add a ROADMAP.md link to
   `geometry_tuple_index.md`, directly contradicting its deliberate unlinked status. Needs a founder call
   in the other session (dismiss the job, or explicitly override the doc's own guard).
6. **T-0011's side quest** (possible need for a higher-level doc linking ideas/thoughts/plans/decisions)
   — explicitly deferred, genuinely still open, not yet scoped.
7. **`pattern_discovery.py` was only run in `--new-only` mode with default settings** — the tool is real
   and reusable; a fuller pass (different edge types beyond `shares_file`, e.g. `references`/
   `coordinates_with`) was not run this session, given token constraints late in the session.
8. **Does one `cycle_id` ever cover more than one `moment.record()` call?** Flagged as an unresolved
   residual question in the doc's guards section — worth checking directly before P1.5 is ever built.

## Warnings

- **The other concurrent session (`5008482f-de41-4dd5-9bed-63c52124f514`) has six decisions and one job
  explicitly waiting on this document** — read `docs/staged/geometry_tuple_index.md` before ruling on
  D-0022/D-0025/D-0029/D-0033/D-0035/D-0041 or executing J-0220.
- **Do not add a ROADMAP.md link or `cognitive_geometry.md` parent relationship to `geometry_tuple_index.md`
  without a real founder decision** — this was deliberately corrected once already this session; J-0223
  wanting to add exactly that link is a known, flagged, unresolved tension, not something to silently
  resolve either way.
- **`memory-links/pattern_discovery.py` is new** — any future rebuild/refactor of the memory-links skill
  should know it exists and reuses `ct.EDGES_PATH`/`ct.MEMORY_DIR` conventions from `_plan_tools_common`.

## Pointers

- `C:\Nascence\docs\staged\geometry_tuple_index.md` — the actual deliverable, read this first.
- `C:\Nascence\docs\job_queue.jsonl` J-0210 — the real next actionable step.
- `~/.claude/skills/memory-links/pattern_discovery.py` — the new tool, `--new-only` mode is the useful one.
- `docs/findings.jsonl` F-0243 through F-0262 — full citation trail for every claim in the staged doc.
- `docs/plans/memory_knowledge.md` and `docs/RESEARCH_specialists.md` — the two closest real sibling
  plans, worth reading alongside the staged doc, not instead of it.
