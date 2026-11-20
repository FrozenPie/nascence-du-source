# graphify — project-specific notes & the enrichment pass

> How we run graphify on Nascence, and the one project-specific fix that must run after every build.
> Archived snapshots live in `graphify-out/archive/<YYYYMMDD>/` (kept for cross-time comparison; excluded
> from the scan because they sit under `graphify-out/`).

## The workflow (every rebuild)

```bash
# 1. archive the current snapshot (dated) for future comparison
cp graphify-out/{graph.json,graph.html,GRAPH_REPORT.md,manifest.json,cost.json} graphify-out/archive/<date>/

# 2. rebuild (incremental — only re-extracts changed files; code = free AST, docs = LLM)
/graphify C:\Nascence --update

# 3. ★ ENRICH — recover the edges graphify's AST misses on this project (REQUIRED)
python scripts/graphify_enrich.py

# 4. re-cluster after enriching (edges/nodes just changed), then check graph.html actually got written —
#    once this project passed 5000 nodes, `cluster-only` started silently skipping it (see below)
python -m graphify cluster-only .
python scripts/graphify_force_html.py   # only needed if the previous line printed "Skipped graph.html"

# 5. health check — read the graph for real findings, not just to look at it
python scripts/graphify_health_check.py
```

Steps 3 and 4 are not optional. Without step 3 the graph systematically under-represents how connected the
code is; without step 4's check, graph.html silently goes missing (or stale) and the only visual left is
whatever `graphify tree` last produced — a hierarchical tree, not the linked-circles community view. Step 5
is the payoff for doing 3 and 4 properly — a noisy graph makes a noisy checker.

## Why step 3 exists — the AST blind spot (found 2026-07-04)

graphify uses a **tree-sitter** AST and resolves imports at **module level only**. Nascence uses
function-**local (lazy) imports everywhere** — the fail-open discipline: `def f(): from core.x import y; ...`.
graphify cannot resolve a call to a symbol bound by an in-function import, so it **drops both the
`imports_from` and the `calls` edge**. The whole basin-centroid reuse spine
(`self_surprise._basin_centroid` ← `mineness._get_basin` ← `reentry`) was invisible until we looked;
`arousal.tonic` calling `homeostasis.status` + `sleep_pressure.status` — invisible; and so on across the
shadow organs, which all wire together through lazy imports.

## What `scripts/graphify_enrich.py` does

An **additive, idempotent post-processing pass** — it does NOT patch the graphify package (survives
upgrades). Using Python's own `ast` (precise + scope-aware, unlike generic tree-sitter for pure-Python):

- parses every `.py` under `core/`, `nodes/`, `scripts/`;
- per function/method scope, collects module-level AND function-local project-internal imports;
- resolves the calls they enable (`name()` for `from x import name`; `mod.attr()` for `from x import mod`);
- adds the missing `imports_from` (file→file) and `calls` (symbol→symbol) edges to `graph.json`.

Honesty guards (graphify's rules, kept): IDs are generated with graphify's own `graphify.ids.make_id` so
nothing becomes an orphan; an edge is added **only when both endpoints already exist as nodes**; it never
invents a node; scope-correct (does not descend into nested defs, so shadowed names can't create false
edges); fully idempotent (a second run adds 0). Each enriched edge carries `"enriched": "local_import"` so
they're distinguishable from graphify's own.

**First run (2026-07-04): +675 `calls` + 124 `imports_from` edges recovered** (6,051 → ~6,838), which merged
14 artificially-split communities (261 → 247) — the subsystems are now as connected in the graph as they are
in the code. Re-cluster after enriching (the reported build did) so communities reflect the recovered edges.

## Why step 4 exists — graph.html silently disappears past 5000 nodes (found 2026-08-18)

`cluster-only`'s CLI has an aggregated-community fallback for graphs over the 5000-node HTML viz limit
(circles = communities, still a force-directed "linked spheres" view) — but it only turns that fallback on
when graph.json trips an unrelated BYTE-SIZE cap, not the actual node-count check `to_html()` itself uses.
This project's graph.json is a few MB (well under that byte cap) but now has 5300+ nodes, so `cluster-only`
silently prints "Skipped graph.html" instead of building the view it's fully capable of — no error, easy to
miss. `scripts/graphify_force_html.py` calls the same underlying `to_html()` graphify already ships, just
without the CLI's broken gate. Default mode raises `node_limit` past the actual node count so the RAW
per-symbol graph renders (thousands of individual dots) — confirmed against the founder's side-by-side of
old vs new screenshots that this, not the coarse aggregated-community view, is the graph people actually
want to browse. `--aggregate` forces the coarser community-circle fallback instead, kept as an escape hatch
if the raw render ever gets too heavy for the browser. Re-run either mode any time `cluster-only` reports a
skip. See the script's own docstring for the full trace. (Do not confuse this with `graphify tree` — that's
a genuinely different, hierarchical D3 view, useful for browsing every raw node in a different shape, but
not what people mean by "the graph.")

## Ghost duplicate nodes + self.-call resolution (found & fixed 2026-08-18)

A graphify audit (chasing "orphan" nodes to check what's actually dead in Du) found two more gaps, both now
fixed inside `scripts/graphify_enrich.py` — step 3 above still covers both, nothing changed in the workflow:

1. **`self.method()` / `self.attr.method()` were invisible too**, not just lazy imports. Every
   `orchestrator.py` method checked (`run_cycle`, `_thalamic_gate`, `_introspection_budget`, ...) showed as
   a zero-edge orphan despite being genuinely called — same for `self.unified_gate.observe()` and
   `self.symbol_tracker.observe()`. `graphify_enrich.py` now also resolves same-class same-file self-calls,
   and instance-attribute calls by tracking `self.X = ProjectClass(...)` assignments.
2. **125 ghost duplicate nodes**, found while verifying #1: graphify's semantic-extraction merge step can
   fail to match a doc/rationale mention of a symbol back to its existing AST node, minting a second,
   disconnected node with a cruder ID instead (same bug class as `graphify.ids`' own documented "#550
   same-name collisions", just at symbol grain — e.g. `core/stick_test.py` had both `core_stick_test`
   [real, connected] and a bare `stick_test` ghost [isolated, its own singleton community]). These ghosts
   inflated the apparent orphan count without representing anything real. `graphify_enrich.py` now also runs
   `dedupe_ghosts()`: merges any non-AST node sharing (source_file, symbol name) with a real AST node,
   rewriting its edges onto the real node and dropping the duplicate. Idempotent, like the rest of the pass.

Net effect on this run: core/`nodes/` singleton count went from 24 → 4, and the 4 remaining are legitimate
(two blank `__init__.py`, one confirmed-retired block in `curator.py`, one constant that's read, not called).
Two known-real remaining islands the fix does NOT reach: `scripts/gutenberg.py` and `scripts/supervisor.py`
are invoked via subprocess/non-standard import paths, not `from x import y` — genuinely outside what an
AST call-graph can represent, not a bug.

## Why step 5 exists — `scripts/graphify_health_check.py` (built 2026-08-18)

The ghost-node hunt above wasn't just cleanup — tracing one of the graph's own AMBIGUOUS semantic edges by
hand (`weather_conditions.py` ↔ `world_traces.py`) caught a real bug: `world_traces.py` was silently
re-deriving its own copy of weather logic that `weather_conditions.py` already owned as the canonical
source. The founder asked to turn that manual process into a repeatable tool. `graphify_health_check.py`
runs three checks, matching `world_grounding_audit.py`'s house style (standalone, advisory not gating,
hardcoded allowlists, one function per check):

1. **Dead/orphaned code** — core/nodes symbols with zero graph edges. Never trusted on graph signal alone:
   every candidate is grep-verified against every `.py` file in the repo first. That discipline is load-
   bearing, not decoration — while building this check, a THIRD residual gap turned up: `core/schema.py`'s
   `SERVE_CHAINS` still has an unmerged ghost node (`schema_servechains`, 0 edges) even after the dedup pass
   above, because graphify's AST extractor doesn't tag simple module-level constant assignments with
   `_origin: "ast"` the way it tags functions/classes — so neither `SERVE_CHAINS` node looked "more real"
   than the other to `dedupe_ghosts()`'s matching logic, and neither got merged. Left as-is rather than
   loosening that filter (real risk of new false merges) — the checker's mandatory grep pass already
   neutralizes it correctly (SERVE_CHAINS is used in 22 files, so it never gets reported).
2. **Canonical-module drift** — generalizes the weather_conditions/world_traces catch: for each of 8 modules
   that self-declare "single source of truth" status in their own docstrings (`weather_conditions.py`,
   `affordances.py`, `mood.py`, `schema.py`, `world_objects.py`, `contradiction_gate.py`, `listening.py`,
   `epistemic_state.py`), flags any file with an AMBIGUOUS/INFERRED graph edge to it that doesn't actually
   import it. Self-resolving by construction — fix the drift and the real edge silences the flag. Read every
   hit before acting: the first real run found 2, and both turned out to be false positives on inspection
   (thematic-but-not-functional similarity, e.g. `world_clock.py`'s own docstring says weather explicitly
   lives elsewhere) — exactly the judgment call this check is built to hand off, not resolve automatically.
3. **Architecture rules** — deliberately empty scaffold. No project-wide rules document exists anywhere in
   this repo (checked 2026-08-18). The one candidate found, `world_objects.py`'s own "Architectural Contract
   v1.4" (3 named invariants), is narrative rather than a checkable condition yet — add rules to the `RULES`
   list in the script once a specific check's exact semantics are pinned down, rather than guessing.

## Other ideas (not built — pick if a future need arises)

- **Rationale-node volume:** ~1,187 `*_rationale_NNNN` nodes (one per docstring/comment block) bloat
  communities. They carry the "why" (useful for GraphRAG), so we keep them — but a report view that hides
  them would make the structural skeleton clearer. Low priority.
- **Shadow/live tagging:** tag each organ node with its flag state (shadow vs live) from AWAITING_EVIDENCE
  so the graph can be filtered to "what actually runs." Genuinely project-specific; build if we want a
  live-only structural view.
