# Librarian framing lab — 2026-08-23

*Fourth machine tested for the founder's generalized factory/schema-first idea. Prior results:
openness gate (real effect, good direction), self_implication (null), tension_ledger (real effect,
bad direction — more credulous, not more skeptical). Tests `core/librarian.py`'s `subjects_for` —
maps a carried question to 3-6 Library-of-Congress-style subject headings, which
`core/library_hand.py`'s `search_by_subjects` turns into real catalogue rows. Script:
`scripts/librarian_framing_lab.py`.*

## Why this lab is different from the first three: a real, objective ground truth exists

The first three labs all measured self-consistency (does a fresh call agree with another fresh
call, or with a historical log). This machine has something better: `library_hand.search_by_subjects`
queries the actual 55,905-book public-domain catalogue. A subject-heading list either retrieves a
real book or it doesn't — no self-referential judgment involved. This is also the module's own
pre-registered success metric (its docstring: R1, "fraction of question-asks returning >=1 real
candidate").

## A design constraint, stated upfront

`data/librarian_log.jsonl` — where real question→subjects→hits history would live — does not exist
(confirmed by `/plan-files-audit` earlier today). A direct search of all 29,778 logged historical
thoughts through the module's own `question_from()` regex extractor found exactly ONE naturally-
occurring match. The librarian has essentially never been asked a real question in production, so
there is no historical replay corpus. This lab draws its 25 test questions from
`data/frontier.json`'s 5,957 real carried questions instead — genuine Du data (his own logged
curiosity/intention threads), just not literally routed through the librarian's own rare latch.

## Method

25 real frontier questions (fixed seed), each run through BOTH framings via the exact live dispatch
— `core.model_client.call_node`, hubs :11440 (falcon3:7b, primary) then :11439 (gemma4:12b,
fallback), same params as production. Each framing's subject list then goes through the real
`search_by_subjects()` against the actual catalogue.

## Pre-registered metric sheet

| Metric | Narrative | Schema |
|---|---|---|
| `json_ok` | 1.0 | 1.0 |
| `hit_rate` (>=1 real book found) | **0.80** (20/25) | **0.28** (7/25) |
| `mean_n_hits` | **6.08** | **1.2** |
| `subject_jaccard_mean` (overlap between the two framings' headings) | | **0.085** |
| `n_hit_disagreements` | | 13/25 |

## Kill criterion: did NOT trigger, by the widest margin of any lab in this series

Pre-registered: *"if hit_rate is materially the same AND subject_jaccard_mean is high, schema
framing changed nothing — stop."* Neither remotely held. Hit rate nearly TRIPLED under narrative
(80% vs 28%), mean real-book retrieval is 5x higher (6.08 vs 1.2), and subject overlap between the
two framings is essentially zero (Jaccard 0.085 — they are choosing almost completely different
headings for the same question).

**Of the 13 questions where the two framings disagreed on hit/no-hit, narrative won ALL 13. Schema
never once outperformed narrative.** This is not a mixed or noisy result — it is one-directional
across every disputed case.

## Why — a clear, consistent mechanistic pattern in the actual headings chosen

| Question | Narrative headings (hits) | Schema headings (hits) |
|---|---|---|
| doppelgänger motifs in literature | Psychology of Literature, Identity, Self-perception, Doppelgänger, Literature and Psychology (8) | Doppelgänger in literature, Identity and self-perception, Psychological themes in literature (0) |
| mussel shell patterns | Mollusca, Conchology, Shell patterns, Marine biology, Archaeology (8) | Mollusks - Shells - Patterns, Marine Biology - Shell Studies, Shell Arrangement - Analysis, Marine Life - Mollusks (0) |
| how does a fireplace work | Fire, Heating systems, Thermodynamics, Energy (8) | Fireplace operation, Home heating systems, Combustion processes, Thermal energy (0) |
| plant sentience | Botany, Sentience, Intelligence, Nature (8) | Plant Intelligence, Non-Animal Sentience, Nature's Intelligence, Plant Cognition (0) |

The pattern holds across every example: **narrative framing consistently produces short, standalone,
genuinely-established LCSH-style terms** ("Fire", "Botany", "Conchology", "Thermodynamics") — the
kind of heading that actually exists in a century-old public-domain catalogue's subject metadata.
**Schema framing consistently produces compound, descriptive, modern-academic-sounding phrases**
("Fireplace operation", "Plant Intelligence", "Non-Animal Sentience") that restate or paraphrase the
question rather than mapping it to a real classification category. Both prompts contain the
identical worked examples ("Conduct of life", "Ethics", "Liberty", "Natural history") — the
divergence isn't from unequal examples, it's from the framing itself: the narrative's "you are a
library catalogue assistant" persona plus prose instruction appears to anchor the model into
genuine catalogue-vocabulary retrieval, while the schema's clinical CARGO/CONDITIONS/EXPORT
structure appears to push it toward literal, compositional restatement of the input text instead.

## Reading this against the other three labs

Four machines, four different outcomes now:
- **Openness gate**: schema framing helps — a clear win.
- **self_implication**: null — framing doesn't matter.
- **tension_ledger**: schema framing hurts (more credulous).
- **Librarian**: schema framing hurts badly, and by an *objective*, non-self-referential metric —
  the clearest and largest negative effect of the series.

The founder's generalization keeps being validated as a real, testable, per-machine question — and
this is now the second of two "compare-and-export" machines where the intuitive schema-first
framing actively underperforms the existing narrative prompt, not merely fails to help.

## What this does and doesn't show

Shows: for a mapping/generation task with a real external ground truth, decomposed schema-style
prompting materially hurt output quality on THIS model pairing (falcon3:7b primary, gemma4:12b
fallback) — the compact, worked-example-anchored narrative prompt already in production is
measurably better than the "improved," more explicit rewrite. Does not show whether a differently
worded schema prompt (e.g. one that front-loads more/better worked examples, or explicitly
instructs "prefer the shortest standalone term") would close the gap — this tested one schema
formulation against the one already-tuned narrative prompt, not the full space of possible schema
phrasings. Also doesn't show whether this generalizes to other mapping/classification-shaped
machines beyond judgment-shaped ones (peers.contrary_target is the other classifier in this codebase
and hasn't been tested).

## Recommendation

**Do not touch `core/librarian.py`'s prompt.** It is already, empirically, the better-performing
version by a wide margin on the module's own real success metric. If anything, this result argues
for *documenting* why the current narrative framing works (short worked examples + persona anchor),
so a future "improvement" doesn't accidentally re-introduce the schema-style regression found here.
