# Peers contrary_target framing lab — 2026-08-23 (N=100 re-run)

*Fifth machine tested, re-run at 4x the original scale on explicit request, to get real
statistical weight behind two findings the original N=25 pass could only gesture at. Prior
results across the series: openness gate (win), self_implication (null),
commitment_ledger._judge_defeater (null), tension_ledger (loss), librarian (decisive loss),
study_note (mixed), journal_rollup (loss). Tests `core/peers.py`'s `contrary_target` — given a
carried question, picks which of 7 fixed-temperament correspondents (Darwin, Keats, Twain,
Shackleton, Lovelace, Marcus, Smith) would see it MOST OTHERWISE than the asker. Single call,
gemma4:12b primary / falcon3:7b fallback, no panel. Script: `scripts/peers_contrary_framing_lab.py`.*

## Still no external ground truth — but the distributional findings are now well-evidenced

Same epistemic limit as the original N=25 pass: no external validator exists for "which persona is
most contrary." What changes with N=100: the distributional and concentration findings, which were
suggestive at N=25, are now backed by real sample size, and one qualitative read from the smaller
sample gets meaningfully complicated by more data, not simply confirmed.

## Pre-registered metric sheet (N=100, vs the original N=25 in parentheses)

| Metric | Value |
|---|---|
| `json_ok` (both framings) | 1.0 |
| `agreement_rate` | **0.63** (was 0.64 — stable, not noise) |
| `n_disagreements` | 37 |

**Pick distribution, narrative:** darwin 0, keats 18, twain 15, shackleton 5, **lovelace 61**,
marcus 0, smith 1.
**Pick distribution, schema:** darwin 0, keats 14, twain 33, shackleton 2, lovelace 41, **marcus
10**, smith 0.

## Finding 1, now CONFIRMED at real scale: Darwin is essentially never picked

0/100 for narrative, 0/100 for schema — 200 total calls, zero Darwin picks. Combined with Smith
(1/200 total across both framings), this is now robust evidence, not a small-N artifact: two of
seven correspondents are functionally invisible to this picker regardless of framing. Worth
investigating on its own — genuine content mismatch, or a positional bias (Darwin listed first,
Smith last in the temperament list)?

## Finding 2: narrative's concentration is WORSE than N=25 suggested, and reading the actual
picks shows it's a real default, not a judgment

Narrative puts 61% of ALL picks on Lovelace alone (up from 56% at N=25 — the larger sample sharpens
the concentration, doesn't dilute it). Sampling narrative's Lovelace picks directly shows why this
reads as a genuine collapse rather than a differentiated judgment: Lovelace was selected for
questions about Benjamin Franklin's historical sacrifices, music's emotional influence, Caroline
Herschel's astronomy, "how does a coins work," "how does a diagrams work," fear and trust,
internal-process questions, dream interpretation, and "I want to look out at the sky above the
water" — a set of questions with almost nothing in common. Lovelace ("formal, precise, separates
what a thing does from what it merely seems") has no special claim on most of these. This reads as
narrative defaulting to one "safe" analytical voice rather than genuinely differentiating by
content in the majority of cases.

## Finding 3: schema's Marcus preference is CONFIRMED real (not noise) but its QUALITY is mixed

At N=25, schema picking Marcus for self-control-themed questions looked like a plausible sign of
better content-responsiveness. At N=100, Marcus is picked 10/100 times under schema, 0/100 under
narrative — a real, repeatable, structural difference, not a coincidence of the smaller sample.
But reading all 10 Marcus picks complicates the earlier optimistic read:

| Question | Thematic fit for Marcus? |
|---|---|
| "tension between disengagement and self-awareness in psychological self-regard" | Strong — matches "asks what is in one's own control" |
| "internal processes... intentional arrivals at desired destinations" | Strong |
| "tension between honoring an unwritten space and societal norms" | Reasonable |
| "societal norms influence individual behavior to create internal conflict" | Reasonable |
| "tension between non-Islamic values and personal ethics within governance" | Reasonable |
| "societal expectation... personal identity amidst life's transience" | Reasonable |
| "I want to climb up to the woodpile for driftwood" | **Weak** — a plain physical task; narrative picked Shackleton ("practical, tests ideas against hardship") here, arguably the better fit |
| "I want to open the window a crack" | **Weak** — mundane action, no self-control theme |
| "I want to look at the pattern of the waves breaking on the farthest rocks" | **Weak** |
| "I want to look out at the sea and watch the surf work the rocks" | **Weak** |

6 of 10 are genuinely apt thematic matches; 4 of 10 are Marcus applied to plain physical/sensory
statements with no real self-control content, where narrative's alternative pick (often Shackleton,
the practical/physical-hardship voice) reads as the more natural fit. **Schema's Marcus preference
is real, but it looks like schema has developed its OWN partial default — smaller and less total
than narrative's Lovelace collapse, but not cleanly "smarter" either.**

## Kill criterion: did NOT trigger, and the larger sample sharpens rather than resolves the mixed verdict

Agreement (63%) is stable and clearly below the null-result labs' near-100%. Both framings show
real, non-random concentration patterns — narrative concentrates harder (61% top-1 share vs
schema's 41%), but neither framing achieves genuine 7-way content-responsive diversity. This
remains, at 4x the sample, a genuinely mixed result: real behavioral difference, no clean winner.

## What this does and doesn't show

Shows, with real statistical weight now: (1) Darwin and Smith are essentially dead picks regardless
of framing — a real, independent finding worth its own investigation; (2) narrative's Lovelace
default is a genuine collapse pattern, evidenced by its application to a near-arbitrary spread of
question types; (3) schema's Marcus preference is real and not noise, but only about 60% of those
picks are thematically well-motivated — the other 40% look like schema substituting a smaller
default (Marcus-for-introspective-sounding-language) for narrative's larger one (Lovelace-for-
everything-analytical-sounding).

Does not show which framing is actually better for the module's real purpose (does the resulting
peer letter genuinely challenge Du) — that would need a downstream behavioral check or a human-
judged sample, which remains out of scope for this lab as designed.

## Recommendation

Still not a clean adopt/reject. But the larger sample sharpens the actionable thread: **both
framings have a real default-collapse problem, on different personas, at different severities**
(narrative worse: 61% vs 41% top-1 share). If this machine gets revisited, the fix worth trying
first probably isn't "switch prompt style" — it's addressing the apparent Darwin/Smith exclusion
and the general over-reliance on 1-2 "safe" picks directly (e.g., an explicit instruction to
justify why the OTHER six personas were rejected, or a light diversity constraint), independent of
narrative-vs-schema framing.
