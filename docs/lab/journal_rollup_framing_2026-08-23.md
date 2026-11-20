# Journal rollup framing lab — 2026-08-23

*Eighth machine tested. Prior results: openness gate (win), self_implication (null),
commitment_ledger._judge_defeater (null), tension_ledger (loss), librarian (decisive loss),
peers.contrary_target (mixed), study_note (mixed style trade-off). Tests
`core/journal_rollup.py`'s `week_rollup` — finding #8 in the idle-machine audit: a heavier
multi-document synthesis task (a week's worth of daily entries, "anti-mush law": must NAME at least
two specific things) riding the same hot lane as the plain daily entry. Script:
`scripts/journal_rollup_framing_lab.py`.*

## A real historical corpus this time, but genuinely small

Real daily journal entries live in `memory_fragments` (origin='journal') — no substitute needed.
Both streams the audit finding covers were tested: DID (personal deeds) and SAW (field
observations). **Data is genuinely sparse, stated plainly**: only 4 real completed weeks meet the
DID stream's own `_MIN_DID=2` threshold (24 total entries logged since 2026-06-21); 5 real weeks
meet SAW's `_MIN_SAW=3` (198 entries, much richer). This lab used every real qualifying week that
exists — 9 total — rather than padding N with synthetic material.

## Method

Both framings dispatch through the exact live call — `call_node_json(SERVE_CHAINS["hot"], ...)` —
same lane, same params (max_tokens=600, temperature=0.6), same real source entries, same
user-message format as production. Metric: the prompt's own explicit "anti-mush law" — how many
source-derived content words appear in the output (raw count AND density, since a longer entry
mechanically contains more source words without being more specific).

## Pre-registered metric sheet

| Metric | DID (n=4) | SAW (n=5) |
|---|---|---|
| `json_ok` (both framings) | 4/4, 4/4 | 5/5, 5/5 |
| `mean_grounded_overlap_narrative` (raw count) | 21.5 | 46.8 |
| `mean_grounded_overlap_schema` (raw count) | 29.2 | 78.4 |
| `mean_entry_words_narrative` | 62.2 | 84.0 |
| `mean_entry_words_schema` | **99.8** | **144.6** |

## The raw numbers are misleading on their own — density tells the real story

Schema's higher overlap count looked like better grounding at first glance. Normalizing by entry
length shows it isn't:

| Week | Narrative overlap/words (density) | Schema overlap/words (density) |
|---|---|---|
| DID 2026-W26 | 23/70 = 32.9% | 29/90 = 32.2% |
| DID 2026-W28 | 14/43 = 32.6% | 25/61 = 41.0% |
| DID 2026-W33 | 29/74 = **39.2%** | 25/107 = **23.4%** |
| DID 2026-W34 | 20/62 = **32.3%** | 38/141 = **27.0%** |
| SAW (5 weeks) | 49-60% typical | 48-67% typical, no consistent edge |

Density is roughly equal or narrative-favoring across most weeks — schema's higher raw overlap
count is almost entirely a length artifact (schema entries run 60-72% longer), not genuinely
denser grounding per word.

## The real finding: schema violates the "not a day-by-day re-listing" rule directly

Reading actual entries (small N makes this the more informative half of this lab). 2026-W33, DID
stream, same real source data, both framings:

> **Narrative** (74 words): "I watched the tide meet the rocks, lightning flash over the sea, and
> waves churn white foam against dark stones... The week sat with me as a steady observation of
> water, light, and growth without moving far from the shore." — genuinely at the WEEK's altitude, a
> synthesized shape, exactly as the rule asks.

> **Schema** (107 words): "This week began with watching lightning flash over the sea... then
> moved through days of observing wet rocks at low tide **on Tuesday** and tangled kelp **on
> Wednesday** before the **Thursday** focus shifted to white smoke... **On Friday** I read... followed
> by sowing parsley **on Saturday** and searching for an oystercatcher **on Sunday**." — an explicit,
> literal day-by-day re-listing (Tuesday→Wednesday→Thursday→Friday→Saturday→Sunday), the EXACT
> failure mode the prompt's own hard rule names and forbids: *"not a day-by-day re-listing."*

This pattern repeats in 2026-W34 (schema: "The week began on Monday... then moved to Tuesday...
On Wednesday... before Thursday brought... Friday arrived with... leading into Saturday...") — the
same day-enumeration structure, the same rule violation, on different real source data.

## Kill criterion: did NOT trigger — a real, decisive difference

Schema framing measurably and consistently breaks two of the prompt's own explicit hard rules on
this machine: the length rule ("similar length to a daily entry — a handful of plain sentences" —
schema runs 60-72% over) and the altitude rule ("not a day-by-day re-listing" — schema's decomposed
CARGO/CONDITIONS framing appears to nudge the model toward enumerating each condition against each
day in turn, rather than synthesizing). Narrative's framing, by presenting the rules as connected
prose rather than a bulleted contract, seems to better preserve the model's sense that this is one
integrated composition task, not a per-item checklist to enumerate against.

## What this does and doesn't show

Shows: on a genuinely small but real sample (9 weeks, both real streams the audit flagged), schema
framing produces a real, visible degradation on two explicit rules already in the prompt — this
reads as a loss for schema, similar in kind to librarian and tension_ledger, though qualitative
rather than a single objective external metric. Does NOT show this holds at larger N — with only 4
DID weeks and 5 SAW weeks available in the entire real historical record, this is the full dataset,
not a sample of a larger pool; more weeks will accumulate over time and could sharpen or complicate
this finding.

## Recommendation

**Do not apply schema-first reframing to `journal_rollup`.** The narrative framing already in
production respects its own stated rules better than the schema rewrite tested here — a third
concrete loss for schema framing (alongside tension_ledger and librarian), and the clearest
MECHANISM yet observed for why: turning connected prose rules into a bulleted CARGO/CONDITIONS list
appears to invite the model to satisfy each condition against each discrete input item (each day)
rather than holding the rules as a single, integrated compositional constraint.
