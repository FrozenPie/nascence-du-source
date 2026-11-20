# Geometry Tuple Index — multi-dimensional theory deep session (Claude, FreshStart window)

## Session timing
- **Session started:** 2026-08-24 03:57:00 UTC
- **Last message before wrap:** 2026-08-24 06:40:18 UTC
- **Wrapped:** 2026-08-24 08:33:40 UTC

## Summary

A single long session pushing `docs/staged/geometry_tuple_index.md` far past its prior state — from
"three candidate dimensions" into a real, tested multi-dimensional theory: a Keys dimension for
discovered links between dimensions, a kind-taxonomy map (22 rows), an event-face/state-face
distinction, eager vs. lazy vs. derived-on-demand capture, and nine real benchmarks run against live
Nascence data rather than argued in the abstract. Ended with a founder-pasted GPT review (verified
accurate against the real doc) and one concrete adversarial check it prompted, which found a real
world-truth-boundary risk in this session's own empirical work.

## What changed

**Primary artifact**: `C:\Nascence\docs\staged\geometry_tuple_index.md` — added §2.4 (slice+overlay
framework, still has an unconfirmed founder-mapping from early in the session), §2.5 (un-deferred
`moment.py::recall()` at the design level), §2.6 (the Keys dimension), §2.7 (kind-map, 22 rows, 5
patterns), §2.8 (event-face vs. state-face), §2.9 (eager co-located capture, unified with §2.6), §2.10
(source→observer derivation law, checked across 5 real channels). §3's toolkit corrected (HNSW→NSW
naming, Pi-pillar's false zero-storage claim, golden-angle entry added) and extended with real benchmark
results (§3.1). §4 corrected (Echo→Cipher citation) and extended (Cipher/Monolith pipeline connection,
a real gap found in Nascence's own Sound Space MEASURED/CONSTRUCTED split). §6 extended with a real
wave-fit+piecewise learned index (F-0278) and the first-ever real run of P1.5's own pre-registered
metrics (F-0279). §7 gained three new guards (sidecar crash-consistency, dimension-creep, world-truth-
source). §10 extended with a real plans/overview sweep (F-0277).

**Real code artifacts added** (all additive, dev-only, none touch production): `engine/oxibonsai/
crates/oxibonsai-runtime/examples/geometry_bench.rs`, `geometry_bench_true_hnsw.rs`,
`geometry_bench_384d.rs`; `hnsw_rs = "0.3"` added to that crate's `[dev-dependencies]` only.

**Findings logged** (see `docs/findings.jsonl`): F-0269, F-0275, F-0276, F-0277, F-0278, F-0279, F-0280,
F-0281, F-0282 — all `[verified]`, all cited with real evidence in the doc itself.

**Thought logged**: T-0015 (session-open musing, matches this session's actual arc).

**Toolchain**: `/plan-maintain` run twice (first pass without `--session`, invisible to this session's
rollup — re-run with it before wrap). `geometry_tuple_index` is now properly indexed in `plan_index.md`,
`plan_liveness_audit.md`, `plan_schema_audit.md`, `plan_snapshots.jsonl`; memory-links rebuilt (74 real
edges touching this plan).

## Key findings

- **F-0269/F-0275/F-0276** — the orphaned `embedding_index.rs` NSW candidate loses to a plain linear
  scan once tuned for usable recall; a real true-HNSW crate (`hnsw_rs`) wins decisively at both 8-D and
  384-D. The theory (HNSW as SOTA) was right; the specific orphaned implementation wasn't.
- **F-0278** — the founder's "shape data toward a wave, keep the fit as the key" idea, translated to
  transform coding (detrend + DCT-of-residual), cut a real learned-index error from 8,654 to 134 rows
  once combined with piecewise segmentation at one real, found discontinuity (the documented 30-day
  outage). Piecewise and wave-fit are independent, multiplicative wins.
- **F-0279/F-0280** — real rigor matters. F-0279's Time↔Knowledge link test got 2 of 5 predictions
  wrong (76.7% oscillation rate — GPT's earlier "transient noise" worry was real, not hypothetical).
  F-0280 then found and ran `moment.py`'s own proper shuffle-null significance test (`z=14.53`) — the
  strongest, most rigorously-validated result of the session, sitting beside a real, precisely-diagnosed
  utilization gap (`MOMENT_READBACK` still `False`, 20% recall hit rate).
- **F-0281** — closed an open design question by reading `sync_fragment_context()` directly: it does
  NOT use `cycle_id` (the fix proposed in §1 is real and still unimplemented, not superseded), and it
  revealed Nascence has **two separate real memory stores** (`moments.jsonl` vs. a SQL-backed
  `memory_fragments` table) this document had been conflating as one.
- **F-0282** — checking a pasted GPT review's abstract world-truth-leakage warning against real code
  found it concretely true: this session's own core benchmarks (F-0269/F-0275/F-0278) were built on
  `geometry_tuples.jsonl`, which is explicitly WORLD TRUTH, not the belief-filtered `fragment_context`
  layer. Not a current violation (nothing here is live), but a real guard now sits in §7 for any future
  activation.
- **Corrections made along the way** (the document's own culture — flag, don't silently fix): HNSW→NSW
  naming (the orphaned candidate is a simplified single-layer NSW, not full HNSW), Echo→Cipher (the
  real working sound-cipher pillar, not the toy Echo file), Pi-pillar's false "zero-storage" claim (it's
  a hardcoded 1000-digit string), a misattributed onset-gating quote (real source is `soundscape.py`,
  not `channels_programme.md`), `oxibonsai-runtime/TODO.md`'s wrong "done" checkbox.

## Open threads

- **§2.4's founder-mapping is still unconfirmed** — early in the session Claude mapped "3 things to
  predict about Knowledge" onto three specific metrics; flagged unconfirmed at the time and never
  corrected. Check before treating it as settled.
- **`sync_fragment_context()` is narrower than §1's `cycle_id` proposal** — it explicitly skips
  conversational/cycle-sourced rows (own code comment: "cycle rows... later"). The `cycle_id` fix
  remains real and unbuilt for that broader case.
- **Smell has no source→observer distance-falloff function** (§2.10) — Sound/Light/Thermal/Memory all
  have one, independently built each time; Smell is a real, confirmed, named gap with Thermal's own
  code as a direct template.
- **World-truth-source guard (§7, F-0282)** — before any future P1/P1.5/Keys/HNSW activation, the
  underlying data source needs to move from `geometry_tuples.jsonl`/`world_context` to
  `fragment_context`. Not yet done; a real blocker for activation, not just a note.
- **GPT's proposed adversarial pass, partially started** — one item (world-truth leakage) checked and
  confirmed real (F-0282). The rest of GPT's attack list (temporal joins, graph explosion, indexing
  overhead, stale indexes, "do some proposed operations need the system at all") is real and
  unaddressed. Founder wants to keep pulling these one at a time rather than a full ceremonial redo.
- **J-0223 still open and correctly conflicting** — a `plan-schema-audit` job wants to add a ROADMAP
  link + Current State section to this deliberately-unlinked document. Confirmed still tracked, still
  unresolved, exactly as the document itself already says. Do not resolve it by adding the link — the
  founder's ruling to keep this document unlinked stands.
- **The "221 degrees" archaeology lead was explicitly dropped** (founder's call) — not in
  `core/lib/abf/`, would need `scripts/legacy/`, `scripts/recovered/`, or the unopened
  `D:\AI stuff\Merged\` archive. Not worth picking back up unless it resurfaces on its own.
- **Two small precision notes from the toolchain pass, unfixed**: `investigative_action_log.jsonl`
  (cited in F-0277) is ambiguous between two real file locations; the ABF pillar files cited this
  session show as "missing" in `plan_files_audit` only because they live under a different project
  root (`C:\FreshStart`) than Nascence's own audit scope.

## Warnings

- This document remains **deliberately staged and unlinked from ROADMAP.md** — the founder has
  corrected this twice now (once early in its history, once implicitly via J-0223 staying open). Do
  not "fix" the missing ROADMAP link or Current State section without an explicit founder decision.
- `engine/oxibonsai` is Nascence's own from-scratch LLM inference engine (kernels/model/runtime
  crates) — unrelated to this design thread except as a benchmarking substrate. The `hnsw_rs` dev-
  dependency and three `examples/geometry_bench*.rs` files are real, harmless, dev-only additions, but
  a session unfamiliar with why they're there should read §3.1 before assuming they're stray.
- The world-truth-source guard (F-0282) is a real constraint on any future build here — a session
  picking this design back up toward activation should read it before writing implementation code.

## Pointers

- `C:\Nascence\docs\staged\geometry_tuple_index.md` — the primary artifact, read start to finish; it's
  long but every section is dated and attributed.
- `C:\Nascence\docs\findings.jsonl` — F-0269 through F-0282, real evidence for everything above.
- `C:\Nascence\core\moment.py`, `C:\Nascence\core\memory_edges.py` — the two files that turned out to
  carry the most load-bearing real detail this session; worth reading directly, not just citing.
- `C:\Users\USER\.claude\projects\C--FreshStart\memory\project_nascence_geometry_tuple_index.md` —
  Claude's own memory file for this thread, updated turn-by-turn all session; the fastest way for a
  future Claude session to re-orient without re-reading the whole design doc.
