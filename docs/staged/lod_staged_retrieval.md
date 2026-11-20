# LOD Staged Retrieval — L0/L1/L2 abstraction-level cascade for recall (2026-08-29)

> **Status: 🔵 DESIGNED — SHADOW-TESTED, PASSED — NOT YET WIRED LIVE (2026-08-29, J-0372/F-0545, D-0054 gate).**
> The A-1 spec #1 investigation (`docs/staged/antigravity_ecosystem_proposals.md` item 1, "OpenViking
> L0/L1/L2 progressive-detail retrieval") ran a real offline lab test (`scripts/lod_retrieval_lab.py`)
> comparing an abstraction-level-staged candidate composition against Du's live `core.memory.store.
> retrieve()` on 120 real logged frontier questions, blind-judged by the real two-family
> `judge_panel.rule_detail` panel + tiebreak. **Result: LOD wins 98/113 judged pairs (86.7%), a 73.5
> win-rate-point margin — clears the pre-registered ≥10pt/≥100-pair kill threshold by a wide margin.
> PASS.** Full result: `docs/lab/lod_retrieval_lab_2026-08-29.md`; finding: F-0545 (verified). Per
> D-0054's own promotion rule (an investigation that proves an item useful promotes it to a real plan
> doc) this is that doc. **Nothing has been wired into the live retrieval path yet** — this doc's §5
> is the build order for doing that, shadow-mode first, per this project's own discipline for every
> other retrieval-adjacent kill-switch (`PEER_REFLECTION_RECALL_LIVE`, `LANE2_LIVE`,
> `TRANSPORT_LIVE`, `REFINERY_LIVE` — all in `core/`).

```plan-state
stage: designed
phase: Lab PASSED (F-0545, 73.5pt margin); Step 1 port-into-store.py not started; Du offline since 08-31
verified: 2026-11-18
evidence_read: 2026-09-02
gate: data/lod_retrieval_shadow_live.jsonl >= 100 live judged pairs once Step 2's shadow hook is built
next: Step 1: port _lod_pools()/_lod_staged() into core/memory/store.py as a pure unwired function (XS, behavior-neutral)
cluster: 10
```


---

## 0. What this is not

This is not a new memory representation and not a schema change. `memory_fragments.abstraction_level`
already exists and is already populated (0=raw transcript, 1=gist, 2=theme/chapter, 3=identity — see
`docs/memory_levels_plan.md`, the foundational abstraction lattice, Phase 1 LIVE). LOD staged
retrieval is a **retrieval-composition** idea only: instead of scoring one flat candidate pool and
taking the top-k (currently tier-mixed, see §2), score the L0/L1/L2 pools *independently* and compose
the result set from a fixed cascade of slots across levels. No new writer, no new column, no new model
call beyond the existing embedding + judge infrastructure this test reused.

## 1. Design — what the L0/L1/L2 cascade actually does

Grounded directly in Du's real schema (not the Antigravity blueprint's fictional `cognitive_mmu.py`
integration point — re-grounded per the A-1 spec's own caveat):

- **L0 (raw, `abstraction_level=0`)** — verbatim/near-verbatim transcript-level fragments. The
  biggest pool (3,732 rows in the lab's isolated snapshot, non-cold/non-chaptered).
- **L1 (gist, `abstraction_level=1`)** — Consolidation-produced distillations. 1,303 rows.
- **L2 (theme/chapter, `abstraction_level≥2`)** — broad thematic/chapter-level summaries. 179 rows
  (levels 2 and above collapsed into one pool for this test; level 3/identity rows are rare and were
  not split out separately).

For a query where the caller wants `n` results (matched to whatever `retrieve(limit=...)` would have
returned), the cascade allocates:

- `l2_n = max(1, round(0.2 * n))` — ~20% broad thematic anchors
- `l1_n = max(1, round(0.3 * n))` — ~30% gists
- `l0_n = n - l2_n - l1_n` — the rest, specific raw detail

Each level's pool is cosine-scored independently against the query embedding (the same
`store._embed` / `store._cosine` / `store._blob_to_vec` machinery `retrieve()` already uses). Slots
are filled coarsest-first (L2 → L1 → L0); **if a level's pool doesn't have enough scored candidates to
fill its own slots, the shortfall cascades down to the next finer level** — the exact same
overflow idiom `store.py`'s own `TIER_SLOTS`/`retrieve()` loop already uses for its
archive→semantic→episodic cascade (see `_lod_staged()` in `scripts/lod_retrieval_lab.py:147-162`,
deliberately mirroring `retrieve()`'s `spare_slots` pattern at `core/memory/store.py:778-801` so the
two designs are structurally comparable, not apples-to-oranges).

**What the test actually proved:** this abstraction-level-only composition, used to build the ENTIRE
result set, beats the current tier-mixed single-level top-k on real judged relevance. It did **not**
test any hybrid that keeps the existing tier partition (archive/semantic/episodic) and adds an
abstraction-level cascade *within* each tier — see §2, this matters for the wiring design.

## 2. How this interacts with the existing `TIER_SLOTS` overflow idiom

`core/memory/store.py`'s live `retrieve()` (lines 697-857) partitions candidate rows by **tier**
(`layer` column: `archive` / `semantic` / `episodic`, plus a per-cycle `working` tier assembled
outside the DB) via the `TIER_SLOTS` constant (`archive: 2, semantic: 3, episodic: 4` — 8 slots
total, "authoritative... corrected 2026-07-02"). Within each tier it scores by cosine similarity and
lets unfilled slots cascade tier-to-tier (archive → semantic → episodic).

**Tier and abstraction level are orthogonal axes.** Tier is about *kind* of memory (identity/archive
vs. distilled understanding vs. lived episodic experience). Abstraction level is about *level of
detail* (raw transcript vs. gist vs. theme) and can appear inside any tier — an episodic fragment can
be raw or already gisted; a semantic fragment is usually already L1+ by construction (it's a
distillation); archive fragments trend L2/L3 (identity-level).

The lab test's LOD arm **replaced** the tier partition entirely — it built the whole 8-slot (or
however many the baseline call asked for) result set from the L0/L1/L2 pools directly, with no tier
concept at all, and won head-to-head against the real tier-mixed baseline. That is a strong result,
but it licenses only the claim "abstraction-level-staged composition beats tier-mixed top-k as a
whole-result-set strategy" — it does **not** by itself tell us whether:

- (a) abstraction-level staging should **replace** `TIER_SLOTS` outright (tier concept dropped,
  L0/L1/L2 cascade becomes the only axis), or
- (b) abstraction-level staging should be applied **within** each tier's existing slot allocation
  (e.g. episodic's 4 slots become "1 L2-ish / 1 L1-ish / 2 L0" instead of pure cosine-top-4), keeping
  the archive/semantic/episodic guarantee (permanent identity always present, etc.) intact.

Design (b) is the safer default for live wiring, because it preserves every guarantee the current
`retrieve()` already makes that the lab test's baseline arm also benefited from for free (the archive
tier's "always present" identity slots, the recency-guarantee insertion at lines 812-830, the
`retrieval_probe` observability hook) — none of which was re-tested independently of the tier system
in the lab. Recommendation: **build and shadow-test (a) exactly as validated first** (it's what was
actually proven), but flag design (b) as the natural follow-up experiment before any full replacement,
since a full swap risks losing the recency-guarantee and archive-always-present properties that
`retrieve()`'s callers may depend on implicitly. This is an open design question for whoever picks up
§5 Step 3 below — not resolved by this doc.

## 3. Real test methodology and result (cite: F-0545, verified)

**Method** (verbatim from F-0545 / `docs/lab/lod_retrieval_lab_2026-08-29.md`):

- **Baseline arm:** `core.memory.store.retrieve()` called live against an isolated DB copy, with each
  query's real text — Du's actual current recall call, output used as-is.
- **LOD arm:** cosine-scored independently against the real `abstraction_level` 0/1/2 pools, composed
  via the slot cascade described in §1, sized to match each query's own baseline result count.
- **Judge:** `core.judge_panel.rule_detail` — the real two-family decoupled panel (gemma4:12b /
  falcon3:7b) + granite3.1-moe:3b tiebreak, blind (Set A/B relabeled per query via an independent RNG
  stream, no ordering or method hint in the prompt — judge never told which arm is which).
- **Queries:** 120 real logged frontier questions sampled (seeded/deduped/length-filtered ≥20 chars)
  from `data/frontier.json` (6,430 entries), processed across 15 chunked runs (a mid-run worktree
  teardown forced chunking — see the script's own RESUME/CHUNKING notes) and aggregated by global pool
  index, deduped.
- **Isolation:** entirely inside `lab_env.isolate()` — every DB read against a lab-dir copy of
  `nascence.db`, never the live file; `judge_panel._LOG` redirected so lab rulings never touched the
  live panel ledger; `telemetry.log_llm_call`/`retrieval_probe.observe` no-op'd. Live DB row-count/
  mtime checked before and after every chunk — unchanged every time.

**Result:**

| Metric | Value |
|---|---|
| Sampled/attempted | 120 |
| Actually judged (non-null verdict) | 113 |
| LOD wins | 98 (86.7%) |
| Baseline wins | 15 (13.3%) |
| Margin (LOD − baseline win rate) | **73.5 points** |
| Kill criterion | ≥10 win-rate points over ≥100 judged pairs |
| Verdict | **PASS — clears the bar by a wide margin** |

Evidence: `docs/lab/lod_retrieval_lab_2026-08-29.md` (full report), `data/lod_retrieval_lab_shadow.jsonl`
(120 rows, one per attempted pair — query, both arms' fragment ids, judge how/v1/v2/winner),
`scripts/lod_retrieval_lab.py` (harness). Finding: **F-0545 (confidence: verified)**.

**What this result does NOT establish** (worth being honest about before wiring anything live):

- **Replayed queries, not live traffic.** The 120 queries came from `data/frontier.json` (Du's logged
  question backlog), not from real-time `core.associative_recall.py` calls happening during actual
  cognition. The A-1 spec itself allowed either source ("drawn from live `core.associative_recall.py`
  traffic (or replayed frontier questions/tension resolutions)") and the replayed-frontier route was
  the one actually run. A live-traffic shadow pass (§5 Step 2) is the natural way to close this gap
  before any live flip.
- **Tier-vs-abstraction-level interaction untested** — see §2.
- **No test yet of design (b)** (LOD-within-tier) — only the full-replacement composition was tested.

## Current State — verified 2026-11-18
- **2026-11-18**: J-4277: Steps 1+2 built in core/memory/store.py (_lod_pools, _lod_staged_candidates, _lod_shadow_observe; LOD_RETRIEVAL_LIVE=False, LOD_RETRIEVAL_SHADOW=False). Restart-gated; set LOD_RETRIEVAL_SHADOW True to collect. Test scripts/_test_J-4277_lod_shadow.py passes.

### What we have
- **SHADOW-TESTED, PASSED. Still not wired into `core/memory/store.py` in any form** — no ledger
  record names this plan since the 2026-09-02 read (J-0419), and a fresh grep this pass confirms
  `retrieve()` is still the pre-test tier-mixed implementation; no `LOD_RETRIEVAL_LIVE` constant exists.
- All claimed artifacts still on disk: `docs/lab/lod_retrieval_lab_2026-08-29.md`,
  `data/lod_retrieval_lab_shadow.jsonl` (122 lines), `scripts/lod_retrieval_lab.py`. Finding F-0545
  (verified) records the 98/113, 73.5pt-margin lab PASS.

### What we need
- §5 Step 1–2: the pure cascade port into `store.py` plus the observe-only shadow hook behind
  `LOD_RETRIEVAL_LIVE = False`, so live-traffic evidence can start accruing.
- §5 Step 3's tier-interaction design ruling ((a) full replacement vs (b) LOD-within-tier) once
  ≥100 live judged pairs exist — likely a `/decide` entry.

### What we're doing next
Nothing in flight — no job or finding has touched this plan since 2026-09-02. The next concrete
action is still §5 Step 1, an XS behavior-neutral refactor safe to do with Du offline.

## 5. Build order — wiring into the live retrieval path (shadow-mode first)

Per this project's own discipline (every comparable retrieval-adjacent change —
`PEER_REFLECTION_RECALL_LIVE`, `LANE2_LIVE`, `TRANSPORT_LIVE`, `NEEDLE_TRIAGE_LIVE`,
`REFINERY_LIVE` — ships behind a module-level kill-switch constant, shadow-exact by default, flipped
only after a live-traffic gate is met), the recommended order is:

**Step 1 — Port the scoring/cascade logic into `core/memory/store.py` as a pure, unwired function.**
Move `_build_pools()` / `_score()` / `_lod_staged()` (currently only in `scripts/lod_retrieval_lab.py`,
lines 124-162) into `store.py` as e.g. `_lod_pools()` / `_lod_staged_candidates(query_vec, n)`,
reusing `_embed`/`_cosine`/`_blob_to_vec` that already exist there. No call site changes yet — this
step is pure refactor-and-relocate so the logic lives next to `retrieve()` instead of only in a
standalone lab script. Cost: XS, no behavior change, testable in isolation.

**Step 2 — Wire a SHADOW (observe-only) hook inside `retrieve()`, same pattern as `retrieval_probe.py`.**
At the end of `retrieve()` (near the existing `retrieval_probe.observe()` call, `core/memory/
store.py:832-844`), compute the LOD-staged candidate set for the same query/limit, using the SAME
live rows already fetched (`all_rows`) rather than a second DB read, and log both the real returned
set (already tier-mixed) and what the LOD cascade would have returned, to a new dedicated shadow log
(e.g. `data/lod_retrieval_shadow_live.jsonl`) — mirroring `retrieval_probe.py`'s "reads into NO
behaviour" discipline exactly. This closes the live-traffic gap noted in §3: real production `retrieve()`
calls, not replayed frontier questions. Guard behind a module constant, e.g.:

```python
LOD_RETRIEVAL_LIVE = False   # shadow kill-switch: False = compute+log only, callers see the
                              # unmodified tier-mixed result (retrieve()'s current behavior)
```

Cost: S. No change to what any caller receives while `LOD_RETRIEVAL_LIVE = False`. This step alone
gives real accumulated evidence on live traffic composition (query distribution, pool sizes as they
drift, timing overhead of a second scoring pass per call) before any judge-blind re-test is even worth
running.

**Step 3 — Resolve the tier-interaction design question (§2) before touching what callers receive.**
Once Step 2 has accumulated a real sample (recommend: same ≥100-judged-pair bar the original spec
used, but this time blind-judged against **live** `retrieve()` calls rather than replayed frontier
questions, to directly test the gap named in §3) — decide (a) full replacement of `TIER_SLOTS` vs.
(b) LOD-within-tier, per §2's tradeoffs. This is a design decision, likely warranting a `/decide`
entry if it isn't obvious once the live-shadow data is in, since it changes a guarantee
(archive-always-present, recency-insertion) other code may implicitly depend on.

**Step 4 — Promotion criteria to flip `LOD_RETRIEVAL_LIVE = True` (or wire the chosen design as the
real default).** Do not flip on the original lab result alone — that result is real and verified but
was against replayed queries, not live traffic, and did not test the tier-interaction question. Flip
only once:
  1. Step 2's live-shadow log has accumulated ≥100 real judged pairs (same blind two-family panel +
     tiebreak, same kill criterion: ≥10 win-rate points), confirming the lab result holds on live
     traffic, not just frontier.json replay; AND
  2. Step 3's tier-interaction design has been chosen and built (not left as the untested full-swap);
     AND
  3. A rollback path exists — `LOD_RETRIEVAL_LIVE = False` must be an exact revert to today's
     `retrieve()` behavior, the same discipline every other kill-switch in `core/` already documents
     (`identity_projection.py:146`, `pursuits.py:115`, `refinery.py:31`).

**Kill/no-go for this build order itself:** if Step 2's live-shadow re-test does NOT reproduce a real
margin (i.e. the 73.5pt lab margin was itself an artifact of the frontier.json query distribution
rather than a real property of the technique), archive the live-wiring effort — the original F-0545
finding stays valid (it answered the question it was designed to answer), but "worth wiring live" is
a separate, not-yet-met bar.

## 6. Duplicate/overlap check (carried forward from the A-1 spec)

`docs/staged/du_recall_lens_upgrades.md` (J-0291, parked) was read in full before the lab test was
built and re-confirmed via keyword grep for L0/L1/L2/abstraction_level/staged-detail (zero hits) — it
is a different technique family entirely (spectral diffusion over the concept co-occurrence graph,
deterministic fact anchoring, counterfactual-ensemble re-ranking). Not a duplicate of this plan.
`docs/memory_levels_plan.md` is the foundational abstraction lattice this plan's L0/L1/L2 pools are
read FROM (Phase 1 LIVE, `abstraction_level` column) — this plan does not change that lattice, only
adds a new way of composing a retrieval result set from it.

## 7. Cross-references

- Spec origin: `docs/staged/antigravity_ecosystem_proposals.md` A-1 item 1 (line ~93), D-0054 gate.
- Finding: **F-0545** (verified) — `python findings_log.py show F-0545`.
- Lab report: `docs/lab/lod_retrieval_lab_2026-08-29.md`.
- Lab harness: `scripts/lod_retrieval_lab.py`.
- Shadow data: `data/lod_retrieval_lab_shadow.jsonl` (120 rows).
- Live retrieval code (unmodified as of this doc): `core/memory/store.py:697-857` (`retrieve()`),
  `core/memory/store.py:307-312` (`TIER_SLOTS`).
- Job that produced this doc: **J-0413**.
- ROADMAP: `docs/ROADMAP.md` → cluster 10 (External proposals inbox).
