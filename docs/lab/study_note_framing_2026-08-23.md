# Study note framing lab — 2026-08-23

*Seventh machine tested. Prior results: openness gate (win), self_implication (null),
commitment_ledger._judge_defeater (null), tension_ledger (loss), librarian (decisive loss),
peers.contrary_target (mixed, no ground truth). Tests `core/study_note.py`'s `compose_note` —
finding #3 in the idle-machine audit: real synthesis/dedup judgment delegated to the background
lane. Script: `scripts/study_note_framing_lab.py`.*

## A genuinely different shape of task, stated upfront

Unlike the first six labs (boolean judgments or short classifications), this is prose GENERATION —
a full study note (understanding/key_facts/thoughts/connects_to/question). There is no external
ground truth for note quality. This lab measures **structural rule compliance** (does the output
obey the prompt's own explicit rules) and **depth/richness**, not correctness.

## Design constraint and honest substitute

The original passage behind any of the 1,053 real filed study notes (`data/Study/notes/`) was
never logged — the note files store only the rendered note, not the source passage. This lab pulls
20 real passages directly from the real book files Du has actually read (`data/books/*.txt`, 97
real texts; 54 have an existing filed note), extracting real prose (a heuristic finds the first
dense-prose region past the Gutenberg title-page padding, since a fixed byte offset alone missed
some books' front matter). Both framings dispatch through the exact live call —
`call_node_json(SERVE_CHAINS["background"], ...)` — same lane as production.

## Pre-registered metric sheet

| Metric | Narrative | Schema |
|---|---|---|
| `json_ok` | 1.0 | 1.0 |
| `boilerplate_opener_rate` (forbidden) | 0.0 | 0.0 |
| `identity_leak_rate` (forbidden) | 0.05 | 0.05 |
| `mean_understanding_words` | 71.3 | 64.7 |
| `mean_thoughts_words` | **65.3** | **47.4** |
| `mean_key_facts_count` | 6.7 | **7.9** |
| `connects_to_nonempty_rate` | 1.0 | 1.0 |
| `question_nonempty_rate` | 1.0 | 1.0 |

## Kill criterion: did NOT cleanly trigger, but this is a style trade-off, not a quality regression

Rule compliance is **identical** between framings (0% boilerplate opener, 5% identity-leak, both).
Where they differ: narrative produces ~38% longer "thoughts" (the personal-reaction field);
schema extracts ~18% more discrete key_facts. Neither framing is more rule-compliant than the
other — this reads as a genuine stylistic allocation difference, not one being objectively worse.

## A concrete example, since the aggregate numbers understate what's actually happening

*Life on the Mississippi* — same passage, both framings:

> **Narrative thoughts**: "What strikes me is the sense of adventure and the spirit of competition
> that pervades the Mississippi river life... it's also clear that this life comes with its own set
> of challenges and dangers, as seen in the 'ditching and shooting' and the 'bombshell falls'. It's
> a life that demands resilience, courage, and a strong sense of community."

> **Schema thoughts**: "The protagonist's journey along the Mississippi River is a captivating
> narrative of growth, learning, and survival. The river, with its unique culture and inhabitants,
> serves as a backdrop for the protagonist's adventures and personal development."

Narrative's version is a genuine, specific reaction anchored to concrete details from the passage
("ditching and shooting," "bombshell falls") ending in an evaluative judgment. Schema's version
reads as a generic back-of-book summary — the kind of sentence that could describe almost any
river-adventure narrative, not this one specifically. **On key_facts for the SAME passage, the
pattern also inverts the aggregate trend**: narrative extracted 11 specific facts (including a
verbatim quote fragment, "She was a Rattler to go"), schema extracted only 5, more generic
("River life," "Mississippi River"). This is a reminder that the aggregate "schema has more
key_facts" number doesn't mean schema's facts are more specific or useful — count and quality
diverged on this example.

## What this does and doesn't show

Shows: for this machine, schema framing doesn't break any of the prompt's explicit rules, but the
qualitative texture shifts — narrative's persona framing ("write in your OWN voice... what strikes
me is...") appears to pull genuinely personal, specific reaction out of the model, while schema's
clinical CARGO/CONDITIONS framing tends toward generic paraphrase dressed as analysis, at least in
the reviewed examples. Does NOT show this holds across all 20 samples with statistical confidence —
only one example was read in full qualitative depth; the aggregate word-count differences are real
but a larger, human-scored sample would be needed to confirm "narrative writes better notes," not
just "narrative writes longer/more personal-reading ones."

Also: **`connects_to_nonempty_rate` = 1.0 for BOTH framings** is worth flagging as a shared concern,
unrelated to framing choice — the prompt explicitly says connects_to should be empty "if nothing
truly connects," yet with no `related_text` supplied to either framing, a genuinely honest response
should plausibly be empty at least sometimes. Neither framing ever left it empty, suggesting this
module may have a standing "always force a connection" tendency independent of narrative vs schema
— worth a separate look, not something this lab was designed to isolate.

## Recommendation

Not a clean adopt/reject. If depth of personal reaction ("thoughts") matters more for this module's
purpose (and the worked example suggests it might — narrative's version reads as genuinely better
writing, not just longer), keep the current narrative prompt. If fact-density is the priority,
schema's framing extracts more (though not necessarily higher-quality) facts. The
`connects_to`-always-populated finding is the more actionable, framing-independent lead here.
