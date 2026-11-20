---
name: ops-nascence-30day-outage
description: "Du was DOWN 2026-07-09 to 2026-08-07 (30 days, zero memory_fragments) — any July-to-August trend read across that hole is wrong."
metadata: 
  node_type: memory
  type: project
  originSessionId: 12d3f00a-7b77-4df3-9adf-e2e877f8664f
  modified: 2026-08-20T05:47:38.490Z
---

**Du had a 30-day outage: 2026-07-09 → 2026-08-07 inclusive, zero rows in `memory_fragments`.**
(35 empty days total across the store's life; longest run 30. Verified directly against
`C:\Nascence\data\memory\nascence.db` on 2026-08-20.)

**Why this matters and keeps biting:** every plan doc that says "six weeks of evidence" is describing
roughly **13–17 days of actual runtime**. Three independent audits hit this on 2026-08-20 and it had
silently corrupted at least two recorded conclusions:

- The **`r(time, valence) = −0.677` "six-week decline"** does not exist. It is a −0.73 *instrument step*
  the day after `AFFECT_SOURCE_PROTOSELF` went live (2026-07-07), then the hole, then a dead-flat
  post-cutover window: **r = +0.012**. It was written into `AWAITING_EVIDENCE.md` as a founder-must-see.
- **K3** (World Ledger kill criterion) "fails, substrate too thin, needs months" — its predictor's
  14-day training window falls *entirely inside the hole*, so it predicts zero for everything.

**Standing rule earned:** any time-series claim must first verify the series was produced by ONE
unchanged instrument end-to-end, and must plot n-per-day before trusting a correlation.

Also note: the live DB is `data\memory\nascence.db`. `C:\Nascence\nascence.db` does not exist and
`data\nascence.db` is 0 bytes — decoys.

See [[feedback-my-failure-modes]], [[project-nascence-transit-map]].
