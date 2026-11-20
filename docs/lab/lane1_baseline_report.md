# Lane 1 self-correction baseline — the pre-Lane-2 counterfactual

*Run 2026-08-20 08:04 · 0.3s · zero LLM · DB read-only · window 14d · rolling series: `data/lab/lane1_baseline/baseline_series.jsonl`*

**Pre-registered PRIMARY endpoint:** `self_interrogation.genuine_per_1k_thoughts`  
*The most direct operationalisation of spontaneous self-doubt that names something real, and already graded by a DECOUPLED judge panel rather than self-scored. Chosen despite having the thinnest data of the five channels, because the alternatives measure architecture-driven correction (resolution_events) or something only loosely related to self-correction at all (train movement).*

All other channels are SECONDARY/exploratory. Reporting a secondary channel as the result because it happened to move is the failure this split exists to prevent.

**Denominator:** 9004 `inner_thought` fragments across 12 days.

## PRIMARY — self-interrogation

- fires: **14** · skips (not sampled): 111
- judge reached a verdict on: **7** of 14 (**50% decidable**)
- genuine: **5**
- **primary rate: 0.555 genuine per 1k thoughts** (daily SD 2.442)

## SECONDARY channels

- **resolution_events:** 528 in window → 58.641 per 1k thoughts
- **T4 provisional identity:** {'revert': 17, 'open': 21, 'solidify': 4}
- **train movement:** 6527 scored steps → circling 9 · deepening 4879 · jumping 1639 · 0.1% circling
- **contradiction pressure:** 30 readings, 28 distinct values, mean 21.251

## How to use this

1. Re-run this script unchanged before Phase 1 wires any Lane 2 read path, and again after. Changing
   the endpoint, thresholds, or channels between runs **voids the comparison**.
2. The kill threshold is deliberately NOT set yet. Set it from this baseline's own natural
   week-to-week variance once several snapshots exist — setting a number before knowing the noise
   floor would be calibrating a gauge nothing has passed through.
3. Run it periodically regardless; the rolling series is the point.

*Raw: `data/lab/lane1_baseline/latest_detail.json`*