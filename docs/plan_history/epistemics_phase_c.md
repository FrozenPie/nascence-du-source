# epistemics_phase_c — folded history


---

# History folded on 2026-09-27 from `docs\plans\epistemics_phase_c.md` (plan-compact, 1 section(s), verbatim, original order)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py epistemics_phase_c`._

## Current State — verified 2026-09-24 (F-1899)

Still exactly what the Status line below says: **DRAFT, nothing built.** A month after reopening,
no code toward C0 exists (`grep -r "tier3_model|_tier3_queue" core/` finds only
`core/source_model.py`'s pre-existing classification mapping, never an implementation).
`data/accuracy_observations.jsonl`'s slow growth (27→34 rows since this doc was written) is NOT
evidence toward this plan's own gate — every row is still `tier1_eval`/`tier4_user`, sourced from
the parent plan's pre-existing Tier 1/2 code; this plan's own paired bootstrap corpus can't grow
until C0 exists to log `source="tier3_model"` rows. Zero `/decide` history and no prior Current
State section here reflects that the "should we build this" question was already answered in the
reopening's own reasoning (the one-GPU constraint no longer applies), not neglect — what was
missing is someone actually building it. **J-1343 spawned** for the doc's own named first step
(C0 Path 1, contradiction-triggered only — Path 2/C1 stay explicitly out of scope per the doc's
own sequencing, gated on the 3070 VRAM headroom question).
