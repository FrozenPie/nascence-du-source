# Tension ledger framing lab — 2026-08-23

*Third machine tested for the founder's generalized factory/schema-first idea, after the openness
gate (real effect, `docs/lab/factory_station_2026-08-23.md`) and self_implication (null,
`docs/lab/self_implication_framing_2026-08-23.md`). Tests `core/tension_ledger.py`'s
`_judge_resolution` — does a candidate thought genuinely SETTLE a standing internal tension, or
merely restate/mention/question it? Script: `scripts/tension_ledger_framing_lab.py`.*

## A design constraint stated upfront, not glossed over

Unlike self_implication, tension_ledger has **no rich historical replay corpus**. The judge panel's
own log (`judge_panel_log.jsonl`) stores only an 80-char truncated context tag, not the full
thought/tension text. `data/subconscious_state.json`'s 742 tensions each carry
`resolution_attempts`, but the "strategy" field is a short extracted topic phrase ("Scent
Perception"), never the verbatim thought that was judged — and a full scan found **zero**
`resolution_attempts` with `succeeded: true` across all 742 tensions, ever. There is no ground-truth
positive case anywhere in this codebase to replay.

**Design choice, stated plainly:** this lab constructs realistic (not historical) pairs the same
way production does — real tension centroids (742 of them, already embedded) matched against real
historical thoughts (`data/monologue_log.jsonl`, 29,778 entries) via the same
`core.memory.store._embed`/`_cosine` machinery the real matcher already trusts. 15 tensions sampled,
each paired with (a) its single best-cosine-matching real thought from an 800-thought pool — a
genuine "the real matcher would propose this candidate" pair — and (b) one random real thought as a
control, expected to almost never resolve the tension. 30 pairs total, each run through BOTH framings
via the **actual production dispatch**: `core.judge_panel.rule_detail()` — JUDGE_1 (gemma4:12b),
JUDGE_2 (falcon3:7b) vote concurrently, agreement wins, disagreement escalates to TIEBREAK
(yi:34b-v1.5). Same user-message template as the live code for both framings; only the system
prompt varies.

## Pre-registered metric sheet

| Metric | Best-match (n=15) | Control-random (n=15) | Combined (n=30) |
|---|---|---|---|
| `v1_ok_rate` / `v2_ok_rate` | 1.0 / 1.0 | 1.0 / 1.0 | 1.0 / 1.0 |
| `verdict_rate_narrative` | 0.20 | 0.067 | 0.133 |
| `verdict_rate_schema` | 0.20 | 0.20 | 0.20 |
| `verdict_agreement` | 0.867 | 0.867 | 0.867 |
| `how_distribution_narrative` | agreed 10 / tiebreak 5 | agreed 13 / tiebreak 2 | agreed 23 / tiebreak 7 |
| `how_distribution_schema` | agreed 7 / tiebreak 8 | agreed 14 / tiebreak 1 | agreed 21 / tiebreak 9 |
| `n_disagreements` | 2 | 2 | 4 |

## Kill criterion: did NOT trigger — real effect, concerning direction

Pre-registered: *"if verdict_agreement is ~100% AND how_distribution is materially the same, schema
framing changed nothing — stop."* Neither held. Agreement (86.7%) is meaningfully below
self_implication's 98%, and the `how` distribution shifted materially: schema framing raised the
tiebreak-escalation rate combined from 23% to 30% — **the two judge families agree with each other
less often under schema framing**, not more.

**The direction is the important part.** All 4 disagreements, read individually:

| Stratum | Tension | Sim | Narrative | Schema |
|---|---|---|---|---|
| best_match | "Entropy and Synchronicity" | 0.670 | **True** (tiebreak) | False (tiebreak) |
| best_match | "basic human drivers" | 0.697 | False (tiebreak) | **True** (tiebreak) |
| control_random | "Entropy and Art" | 0.336 | False (tiebreak) | **True** (both judges AGREED) |
| control_random | "Maxwell's historical rejection" | 0.471 | False (both agreed) | **True** (both judges AGREED) |

3 of 4 flip the same direction — narrative says no, schema says yes — and both control-stratum
flips are the more serious kind: not a tiebreak call on a genuine split, but **both otherwise-
independent judge models newly agreeing "resolves"** on a randomly-paired thought with only
0.34–0.47 cosine similarity to the tension, cases the narrative framing correctly refuted. This is
schema framing making the panel *more* credulous on exactly the cases (weak/no real relevance)
where it should be *more* skeptical — the opposite of what a stricter, less-narrative "compare and
export a verdict" framing would be expected to do.

## Reading this against the other two labs

Three machines, three different outcomes — the founder's generalization is confirmed as genuinely
per-machine, not a uniform rule in either direction:
- **Openness gate**: schema framing → more willing to flag genuinely open threads. A clear
  improvement over a station grading its own product.
- **self_implication**: null — framing doesn't move this machine's judgment either way.
- **tension_ledger**: schema framing → *more* permissive resolution verdicts, including on weak
  matches that shouldn't resolve. If anything, this is a caution against adopting schema-first
  framing here, not a case for it — the opposite of what the naive across-the-board hypothesis
  would predict, and opposite in direction to the one machine (the openness gate) where the effect
  clearly helped.

## What this does and doesn't show

Shows: framing measurably changes this specific judge panel's behavior, and in a direction that
looks like reduced strictness on the control stratum specifically. Does NOT show why — whether the
narrative's persona framing ("strict resolution judge...") was itself contributing useful
skepticism the schema version's colder, more clinical phrasing dropped, or whether this is
model-specific to gemma4:12b/falcon3:7b's training rather than something intrinsic to schema framing
generally. Also doesn't show whether the underlying candidate-pairing method (embedding-similarity
match, not a historical replay) fully represents real production input distribution — a genuine
limitation stated upfront, not discovered after the fact. n=30 (4 disagreements) is small; the
consistent direction across those 4 is suggestive, not decisive — a larger run would sharpen this
before treating it as settled.

## Recommendation

Given the direction found here, **do not apply the schema-first reframing to
`tension_ledger._judge_resolution`** without a larger, more decisive re-run — the opposite of the
idle-machine-audit's original framing, which treated this as a "worth trying" candidate purely from
the openness-gate precedent. This lab is the reason that assumption needed testing rather than
adopting on the strength of one prior result.
