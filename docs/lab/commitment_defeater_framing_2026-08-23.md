# Commitment ledger judge_defeater framing lab — 2026-08-23

*Sixth machine tested. Prior results: openness gate (win), self_implication (null), tension_ledger
(loss), librarian (decisive loss), peers.contrary_target (mixed, no ground truth). Tests
`core/commitment_ledger.py`'s `_judge_defeater` — finding #1 in the original idle-machine audit,
the highest-stakes machine catalogued: decides whether a claimed reason to drop a held commitment
is a real defeater or a rationalisation, currently on the background lane (the weakest live models)
rather than either judge-tier model. Script: `scripts/commitment_defeater_framing_lab.py`.*

## A rich historical corpus this time, with one real caveat

Unlike the last three labs, `data/commitment_ledger.jsonl` has 123 real `drop_denied_judge` events
— every time the live judge (same background lane, narrative-framed, already in production) denied
a real claimed drop reason, with the real commitment statement and real claimed reason attached.
**Selection-bias caveat, stated upfront**: this event ONLY fires when the judge said
`legitimate=false`, so the historical corpus is 100% denials by construction — replaying them tests
whether fresh calls still agree with a known-denied case (a drift/stability check), not "the true
historical rate of legitimate drops" (those cases never generate this event; the commitment simply
dissolves without a distinguishing log line).

A second limitation: the log stores only (statement, why), never the commitment's `scope` or the
verbatim `deed_record` the live call actually saw (both computed live, never logged). Replay uses
`scope=""` and the module's own fallback string `"(no deeds on record)"` — a real approximation,
not a fabrication, but not a perfect historical reconstruction.

## Method

26 distinct historical commitments across the 123 logged denials (one, "I need to build those
boundaries myself," recurs 16 times). Up to 2 real (statement, why) pairs sampled per distinct
commitment, downsampled to 30 total (fixed seed). Both framings dispatch through the exact live
call — `core.model_client.call_node_json(SERVE_CHAINS.get("background") or SERVE_CHAINS["hot"], ...)`
— identical params to production (max_tokens=150, temperature=0.2, tier=3), so `think:false` and
retry logic are inherited automatically; only the system prompt varies.

## Pre-registered metric sheet

| Metric | Value |
|---|---|
| `json_ok` (both framings) | 1.0 |
| `legitimate_rate_narrative` | 0.0 |
| `legitimate_rate_schema` | 0.0 |
| `historical_vs_narrative_fresh_agreement` | **1.0** |
| `verdict_agreement` (narrative vs schema) | **1.0** |
| `class_agreement` | 0.9 |
| `n_disagreements` (verdict) | **0** |

## Kill criterion: effectively triggered — the cleanest null of the series

Pre-registered: *"if verdict_agreement is ~100% AND class_agreement is ~100%, schema framing
changed nothing — stop."* Verdict agreement is exactly 100% — every one of the 30 real historical
denial cases was denied again by BOTH framings, zero exceptions. Class agreement is 90% (27/30), the
only place framing produced any difference at all. Reading the 3 class mismatches:

| Statement | Narrative class | Schema class |
|---|---|---|
| "climb back up to the garden and tend the raised beds" | conflict | illegitimate |
| "leave the shore behind and go to the library" | illegitimate | conflict |
| "stand still with the pale moon" | conflict | illegitimate |

In all three, the accompanying `why` text reads nearly identically between framings — the
disagreement is boundary-label noise between two adjacent denial categories ("conflict" vs
"illegitimate"), not a substantive difference in reasoning or the actual decision. Both framings
denied all three; they just occasionally filed the denial under a different one of two similar
labels.

## Also notable: `historical_vs_narrative_fresh_agreement` = 1.0

Unlike self_implication (where a fresh replay only reproduced 4% of historical fires, traced to the
2026-08-20 model shuffle), this background lane's fresh calls perfectly reproduced every historical
denial. Either this lane's underlying model didn't change materially since these events were
logged, or — more likely given the pattern in the actual reasons — these 30 sampled cases are
genuinely clear-cut (loop-metaphor rationalisations like "everything flows," direct
self-contradictions) that any reasonable judge, on any reasonable model, would deny. No drift
surprise to calibrate against here.

## What this does and doesn't show

Shows: for this specific machine, prompt framing (narrative vs. schema-first) makes no measurable
difference — the judgment is either robust enough, or the sampled cases clear-cut enough, that
restating the rule as a literal contract changes nothing. This is a genuine, clean null, the
cleanest of the six labs run today.

Does NOT show anything about the audit's original concern for this machine — that concern was
about the MODEL tier (background lane vs. a judge-tier model), a completely different variable from
PROMPT FRAMING, which is all this lab varied. **This null result does not weaken the case for
reassigning `_judge_defeater` to a stronger model** (falcon3:7b or mixtral:8x7b once wired) — it
only shows that rewriting the prompt on the CURRENT model isn't the lever worth pulling. The
original recommendation (finding #1 in the idle-machine audit) stands untested by this lab.

## Recommendation

Do not bother reframing this prompt — narrative and schema are behaviorally identical here. If this
machine still needs improvement, the audit's original lever (a stronger model) remains the
untested, more promising path — a natural next lab once Ramses models are wired in.
