# Evidence recall framing lab — 2026-08-23

*Thirteenth and final machine in this batch. Prior results: openness gate (win), self_implication
(null), commitment_ledger._judge_defeater (null), tension_ledger (loss), librarian (decisive loss),
peers.contrary_target (mixed, N=100), study_note (mixed), journal_rollup (loss),
left_lane.grade_work (predominantly null), self_interrogation (near-null), pursuits.judge_pending
(loss), deliberation.ground_thought (loss, methodology lesson). Tests
`core/evidence_recall.py`'s `_JUDGE_SYSTEM` — decides whether a remembered episode is real evidence
bearing on a carried question, vs. merely thematic resemblance or a past conversation about the
question. Real production panel. This is the last of judge_panel's four named consumers
(self_interrogation, tension_ledger, pursuits, evidence — all four now tested). Script:
`scripts/evidence_recall_framing_lab.py`.*

## A real corpus recovered via DB join

`data/evidence_log.jsonl` logs 11 real historical asks with judged fragment_ids (v1/v2/how) but not
the episode text itself. Joined against `memory_fragments` — all 11 asks' fragment_ids resolved, 0
missing — recovering 66 real (question, episode content, historical JUDGE_1 vote) triples. All 66
used, no sampling.

## Pre-registered metric sheet

| Metric | Value |
|---|---|
| `verdict_rate_narrative` | 0.485 (32/66) |
| `verdict_rate_schema` | **0.591** (39/66) |
| `historical_v1_vs_narrative_fresh_v1_agreement` | 0.652 |
| `verdict_agreement` (narrative vs schema) | **0.742** (49/66) |
| `how_distribution_narrative` | agreed 40 / tiebreak 26 |
| `how_distribution_schema` | agreed 44 / tiebreak 22 |
| `n_disagreements` | 17 |

## Kill criterion: did NOT trigger — a third confirmation of the "schema is more credulous" pattern

Of 17 disagreements, **12 flip narrative=false → schema=true; only 5 flip the other way** (71%
one-directional). This is the third machine in this series showing the same shape of effect first
found in tension_ledger and confirmed sharply in pursuits: schema framing makes this judge panel
more willing to credit weak or merely-thematic connections as genuine.

A concrete example makes the mechanism visible. Question: *"my past beliefs."* Episode: a passage
Du read from *The Varieties of Religious Experience*, quoting the BOOK'S AUTHOR's own childhood
memory ("I remember, for instance, that one evening when I was a youth, my father read..."). This
is not Du's own belief history — it's a passage about someone else's past, on a thematically
related topic. **Narrative correctly said `bears=false` (both judges agreed)** — exactly the
"merely thematic" exclusion the prompt's own rule names. **Schema said `bears=true` (both judges
agreed)** — crediting topical resemblance as if it were genuine evidence about Du's own specific
past beliefs.

## One prior pattern does NOT hold here — worth correcting rather than ignoring

The earlier-named "schema raises judge-panel tiebreak rate" pattern (seen in tension_ledger and
self_interrogation) runs the OPPOSITE direction on this machine: schema's tiebreak rate (33%) is
LOWER than narrative's (39%), not higher. Stated plainly rather than cherry-picked: that pattern is
real on 2 of 4 tested judge_panel machines, not universal — worth tracking as a per-machine
question, not a blanket rule, exactly the discipline this whole lab series has been built around.

## Also notable: real temporal/model drift independent of framing

`historical_v1_vs_narrative_fresh_v1_agreement` = 65.2% — JUDGE_1 (gemma4:12b) itself, on the exact
same real (question, episode) pairs, agrees with its own historically-logged vote only about two
thirds of the time. This is a framing-independent finding (both fresh calls use the real prompt,
only comparing old vote vs. new vote on the same model) — a real instability worth someone's
attention on its own, separate from the schema question.

## What this does and doesn't show

Shows: a third, real confirmation that schema framing makes THIS panel measurably more credulous on
weak-but-topically-resembling matches — now supported across tension_ledger, pursuits, and
evidence_recall, three independent judge_panel consumers. Also shows the tiebreak-rate pattern
doesn't generalize past the two machines where it was first seen — a useful correction against
over-pattern-matching. Does not show whether JUDGE_1's own 65% self-agreement rate is a real problem
or expected noise at this sample size; flagged, not diagnosed.

## Recommendation

Do not apply schema-first reframing to evidence_recall — the credulity pattern is now the most
consistently-replicated finding in this entire lab series (3 of 3 tested judge_panel-based
comparison tasks show it), and this machine's whole purpose (deciding what counts as REAL evidence
vs. superficial resemblance) is exactly the kind of task where that failure mode matters most.
