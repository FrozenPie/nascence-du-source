# LOD Retrieval Lab — L0/L1/L2 staged index vs baseline top-k (2026-08-29, J-0372)

**Spec:** docs/staged/antigravity_ecosystem_proposals.md A-1 spec #1 (OpenViking L0/L1/L2
progressive-detail retrieval). **Duplicate check:** docs/staged/du_recall_lens_upgrades.md read in
full first (re-confirmed on resume via keyword grep for L0/L1/L2/abstraction_level/staged-detail:
zero hits) — different technique family (spectral diffusion / anchoring / counterfactual re-rank),
not a staged-detail retrieval idea. Not a duplicate.

## Method

- Baseline arm: `core.memory.store.retrieve()` called live (against an isolated DB copy) with each
  query's real text — Du's actual current recall call, output used as-is.
- LOD arm: cosine-scored independently against the real `abstraction_level` 0/1/2 pools
  (L0=raw, L1=gist, L2=theme/chapter — Du's existing schema, no new columns), composed via a
  slot-cascade (~20% L2, ~30% L1, rest L0, unfilled coarser slots cascade to finer) sized to match
  each query's own baseline result count.
- Judge: `core.judge_panel.rule_detail` — real two-family decoupled panel (gemma4:12b / falcon3:7b)
  + granite3.1-moe:3b tiebreak, blind (Set A/B relabeled per query via an independent RNG stream, no
  ordering or method hint in the prompt).
- Queries: 120 real logged frontier questions sampled from `data/frontier.json`
  (6,430 entries; sample seeded/deduped/length-filtered >=20 chars), processed across multiple
  chunked runs (see CHUNKING NOTE in this script's own docstring) and aggregated by global pool
  index, deduped, here.

## Result

- Sampled/attempted: 120
- Actually judged (non-null verdict): 113
- LOD wins: 98 (86.7%)
- Baseline wins: 15 (13.3%)
- Margin (LOD - baseline win rate): 73.5 points

## Verdict

**PASS — clears the >=10pt / >=100-pair bar**

Kill criterion (pre-registered, from the spec): LOD-staged must beat baseline by >=10 win-rate
points over >=100 judged pairs, or archive as no-lift.

## Isolation

Run entirely inside `lab_env.isolate()` — every DB read against a lab-dir copy of `nascence.db`,
never the live file. `judge_panel._LOG` redirected into the same lab dir (own dedicated log,
`also=`-idiom) so lab rulings never touch the live `judge_panel_log.jsonl` panel ledger.
`telemetry.log_llm_call` and `retrieval_probe.observe` no-op'd for the run (same pattern as
`scripts/routing_lab.py`) since both write to live per-cycle logs unrelated to this experiment.
Live DB row-count/mtime checked before and after each chunk as a backstop.

Shadow log: `data/lod_retrieval_lab_shadow.jsonl` (120 total rows after dedupe by global
pool index, one per attempted pair — query, both arms' fragment ids, judge how/v1/v2, winner).
