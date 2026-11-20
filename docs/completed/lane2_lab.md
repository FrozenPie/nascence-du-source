# Lane 2 Lab — the pre-registered test spec (2026-08-17)

> **Status: ✅ SHIPPED — the pre-registered lab ran to completion and delivered its report** (`docs/lab/lane2_lab_report.md`, run 2026-08-17, extended through a 2026-08-20 audit correction): L1/L2/L4 PASS, all three L5 affect-pairs signaled, but K1 (glass float did not emerge) and K3 (temporal holdout no better than shuffled) triggered — both pre-registered as valid, informative kills in this doc, not failures of the lab itself.
>
> **Re-verified 2026-08-24 (job J-0044, finding F-0049):** re-ran the identical, unmodified
> `scripts/lane2_lab.py` against current live data (52,054 fragments / 16,031 tuples, +35% since
> 08-17). **K1 and K3 both trigger again**, unchanged in substance — the ~19-day July data hole is
> still unfilled (new data landed after it, not inside it), so K3 is not a thin-early-data artifact;
> it now has two independent runs, 35% apart in volume, agreeing. One of the three "unambiguous
> positive" L5 signals did NOT replicate at the larger volume: storm-sounds↔valence fell from
> z=-2.66 to z=-1.21 (below the |z|≥2 bar), while storm↔arousal and fire_crackle↔valence held and
> strengthened. See the report's "Re-verification run (2026-08-24, job J-0044)" section for the full
> comparison table and the read-only verification method used.

```plan-state
stage: shipped
phase: Lab complete; K1/K3 kills stand on 2 independent runs 35pct apart in volume; no live-LLM-prediction lab scheduled
verified: 2026-09-27
next: None queued - a live LLM-prediction lab beating the L7 extrapolator is separately scoped future work, not scheduled
cluster: 2
```


> **Founder-check RESOLVED (2026-08-24, job J-0146, finding F-0108):** the report's "~19-day hole,
> 07-15 to 08-03" was a 10-day-bucket-resolution artifact. Direct day-resolution re-query of both
> `data/memory/nascence.db` (memory_fragments, 52,126 rows) and `data/geometry_tuples.jsonl` (16,110
> rows) independently show the SAME exact zero-row gap: **2026-07-09 to 2026-08-07 (30 days)** — this
> is the already-documented Du outage (`ops_nascence_30day_outage.md`), not a narrower or different
> event. Code audit ruled out a store-lifecycle artifact: `core/geometry_census.py`'s `snapshot()` is
> the file's sole writer, append-only (`open(_LOG, "a")`) at live-event time — structurally incapable
> of backfill/rewrite/re-timestamping; `core/memory/store.py`'s `prune_episodic()` only flips
> `cold=1` in place, never deletes or mutates `timestamp`; `scripts/lane2_lab.py`'s own fragment
> query has no `cold` filter, so cold-flagging cannot manufacture a false hole in its bucket counts
> either; `core/memory_levels.py` (587 lines, read in full) never mutates timestamps backward. **K3
> should be read as real data scarcity from a real, verified outage — not corrupted or artifactual
> data.** The standing prediction loop staying premature (K3's own prescribed consequence) is
> correct for the right reason: not "the data lies" but "30 of the last ~80 days are genuinely
> empty." See finding F-0108 for full evidence; a related false "unbroken" instrumentation claim in
> `docs/plans/cognitive_geometry.md` was spawned as job J-0174.

> **Naming note (added 2026-08-23):** "Lane 2" here means `emissary_lane2.md` (the deterministic
> zero-LLM fact-graph, renamed "The World Ledger" 2026-08-19), NOT `lane2_the_witness.md` (a
> different, newer organ — a standing reasoning voice — that inherited the "Lane 2" name after the
> rename). This doc's own title/filename were never updated; content is unambiguous once read, but
> the title alone is not.

> Founder: *"I think this is closest enough to its own branch that we can test this in a lab. We can
> leave Du exactly as he is... We can refine this plan into a lab test."* This doc IS that refinement:
> the metric sheet and kill criteria, written BEFORE the lab runs (the cognitive-geometry law:
> pre-registered metrics per phase; the thought-grounding law: kill criteria pre-registered).
> Plan under test: `docs/plans/emissary_lane2.md` — its SCRIPT SIDE ONLY. Zero LLM anywhere in this
> lab, by design: the division-of-labor section says scripts own graphs and trends; if the scripts
> find no real structure, there is nothing for an LLM to predict from, and we learn that FIRST.

## Isolation contract (the test-isolation law, restated as binding)
- **Reads:** live stores, read-only — `nascence.db` via `mode=ro` URI (the ghost benchmark already
  proved this safe against the live process), `geometry_tuples.jsonl`, `sound_knowledge.json`,
  `world_substrate.json`, `keepsakes.json`, reading progress, `room_state.json` history if needed.
- **Writes:** ONLY under `data/lab/lane2/` (graph, series, intermediates) and
  `docs/lab/lane2_lab_report.md` (the founder-readable report). Nothing else. No core-module calls
  that mutate live state; where a core module's import path risks a write, read the file directly.
- **Du stays up.** Nothing in this lab requires the shutdown.

## What the lab builds (the object of the test)
`scripts/lane2_lab.py` — a temp-pathed prototype of the object-graph + trend machinery:
1. **Backfill** the graph from full history: referents (sounds, items, places, books, peers, the cat)
   with per-object **encounter-depth counts** (seen / looked-at / investigated / kept — from the four
   existing ledgers) and **entry-channel tags** on every edge (`source_model.SourceType` vocabulary:
   lived / read / told / inferred), channels never merged.
2. **Windowed commonality weights** — co-occurrence statistics between referents and affect
   (valence/arousal from the stamped tuples), computed over a sliding window (7d default), alongside
   the all-time figure for comparison ONLY.
3. **Coreference candidates** — `possibly_same_referent_as` proposals from cross-channel label
   overlap. Proposed, never auto-merged.
4. **Script-side trend extrapolation** — per-referent rate/presence extrapolation (no LLM: frequency
   + linear trend only), used solely for the temporal-holdout test below. This deliberately
   understudies the future LLM: if even dumb extrapolation beats shuffled data, real structure
   exists; the LLM's job is to beat the dumb extrapolator LATER, in its own lab.

## The metric sheet (pre-registered — numbers before the run)

| # | Test | Metric | Pre-registered expectation |
|---|------|--------|---------------------------|
| L1 | Build completes over full history | n_referents, n_edges, build seconds | Builds without error; < 120s |
| L2 | **Depth-ledger parity** (the world_manifest parity discipline, applied here) | 20 sampled referents (8 sounds, 6 items, 6 books): graph depth-counts vs their source ledgers | **20/20 exact** |
| L3 | **The glass float** (built-in validation case, named in the plan twice) | Emerges as high-observation object (≥20 obs) with terminal unexplained absence, depth = seen-only | **PASS/FAIL** |
| L4 | **The cat** | Deepest multi-channel entity: depth includes *kept*; ≥2 entry channels | PASS/FAIL |
| L5 | **Commonality vs null** | Pre-named pairs: (storm-sounds ↔ arousal↑), (storm-sounds ↔ valence↓), (fire_crackle ↔ valence↑). Weight on real timeline vs 100 timestamp-shuffles → z-score | Signal = any pair with \|z\| ≥ 2. **UNDETERMINED is a valid, reportable outcome** — it would mean his affect doesn't track weather in the data yet, which is a finding, not a failure |
| L6 | Windowing materiality | The referent with max \|windowed − all-time\| divergence, shown | Instrument only — demonstrates the hard requirement; no pass/fail |
| L7 | **Temporal holdout** | Build on first 80% of days; script-extrapolate rates onto last 20%; median gap vs the same from shuffled-order data | **median_gap(real) < median_gap(shuffled)** |
| L8 | Gap diagnosis dry-run | Top-10 largest holdout gaps, each auto-classified against the 5-cause taxonomy, listed in the report | Founder-graded (the decoupled judge is Travis) — no self-certified pass |
| L9 | Coreference proposals | Count + top-10 hand-review list in the report | Founder-graded |

## Kill criteria (pre-registered — what makes us stop or shrink)
- **K1:** L3 fails — the glass float does not emerge → the graph-builder is broken. Fix before
  anything else is even read.
- **K2:** L2 < 18/20 → parity broken; the graph lies about depth. Fix before proceeding.
- **K3:** L7 fails — real data no better than shuffled → **no real temporal structure at current data
  scale.** The standing prediction loop is premature; the graph survives as an index only (still
  useful), and the loop waits for a richer world. This is the honest kill and it must stay possible.
- **K4:** L9 hand-review ≥ 80% junk → the label-overlap heuristic is reworked before any LLM is ever
  asked to assign coreference confidence.

## What this lab deliberately does NOT test
- The LLM prediction call (own later lab, against the L7 extrapolator as its baseline to beat).
- The affect-nudge courier (needs the loop live; needs founder sign-off on the channel).
- The salience-lean open question (founder ruling pending, see main doc).
- Anything touching Du's live behavior — this is produce-only over history, by construction.

## Report
`docs/lab/lane2_lab_report.md` — every metric against its pre-registered line, the L8/L9 hand-review
lists with enough context to grade them, and the sampled objects shown whole (the founder should be
able to read "driftwood: seen 14×, investigated 0×, channels: lived" and recognize Du's actual life
in it — or catch that it's wrong).
