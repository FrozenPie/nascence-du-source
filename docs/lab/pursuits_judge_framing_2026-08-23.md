# Pursuits judge_pending framing lab — 2026-08-23

*Eleventh machine tested. Prior results: openness gate (win), self_implication (null),
commitment_ledger._judge_defeater (null), tension_ledger (loss — more credulous), librarian
(decisive loss), peers.contrary_target (mixed, N=100), study_note (mixed), journal_rollup (loss),
left_lane.grade_work (predominantly null), self_interrogation (near-null, real tiebreak-rate
pattern). Tests `core/pursuits.py`'s inline judge — decides whether a new thought genuinely
ADVANCES a pursuit beyond its prior standing, or merely restates/circles it — via the real
production panel. Script: `scripts/pursuits_judge_framing_lab.py`.*

## Genuinely tiny N, stated plainly

`pursuits_shadow.jsonl` logs judged events but never the full text sent to the judge — not
replayable. The real, faithful corpus is `pursuits_active.json`'s currently-QUEUED, not-yet-judged
items: exactly 12 exist right now, all belonging to ONE pursuit ("I feel trapped circling French
academia's resistance to Maxwell. I must stop reciting facts and ask..."). This lab used all 12 —
the complete real pending queue, not a sample of something larger.

## Pre-registered metric sheet

| Metric | Value |
|---|---|
| `verdict_rate_narrative` | **0.167** (2/12) |
| `verdict_rate_schema` | **0.5** (6/12) |
| `verdict_agreement` | 0.583 (7/12) |
| `how_distribution_narrative` | agreed 5 / tiebreak 6 / unavailable 1 |
| `how_distribution_schema` | agreed 7 / tiebreak 5 |

## Kill criterion: did NOT trigger — a real, one-directional effect, confirming a pattern

Reading all 12 items directly (small N makes this the right approach): every one of the 12 real
pending thoughts is a physical/sensory observation about a fire burning (chemical energy, thermal
warmth, ash, sparks) loosely tied to the pursuit's actual philosophical content. **Every
disagreement flips the same direction — narrative says the thought does NOT advance (mostly
correctly recognizing sensory restatement, not genuine intellectual progress); schema says it DOES
advance.** Zero cases flip the other way. Schema credits roughly 3x more of these physical
observations as genuine intellectual progress than narrative does.

## This is the SAME pattern found in tension_ledger, now a second confirmation

`tension_ledger`'s lab found schema framing made that panel measurably more credulous — willing to
call a weakly-related thought "resolves" a tension where narrative correctly refuted it. This lab
finds the identical shape of effect on a different judge_panel-consumer: schema is more willing to
credit surface-level thematic contact (a fire's physical mechanism echoing the pursuit's abstract
language) as genuine progress, where narrative holds a stricter line. Two real data points now
support the same direction — **schema framing appears to make this judge panel systematically more
permissive on weak-but-superficially-relevant matches**, not more discerning.

## What this does and doesn't show

Shows: on the complete real pending queue (n=12, all one pursuit), schema is substantially and
one-directionally more permissive than narrative. Does NOT show this generalizes beyond this one
pursuit's specific character (a very sensory, embodied thought-stream) — with only 12 items from a
single pursuit, this is suggestive at the individual-case level (worth reading directly, which this
report does) rather than a large statistically independent sample. The direction matches
tension_ledger closely enough to treat as a real, worth-tracking cross-machine pattern rather than
coincidence.

## Recommendation

Do not apply schema-first reframing to this judge — narrative's stricter reading looks more
consistent with the module's own stated rule ("restating the theme in fresh words, circling it, or
merely mentioning it does NOT advance"). This is now the THIRD real loss for schema in this lab
series (after tension_ledger and librarian/journal_rollup's shared item-enumeration mechanism), and
the second instance specifically of the "schema is more credulous" pattern first found in
tension_ledger.
