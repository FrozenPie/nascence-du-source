# Librarian P0-vs-P1 head-to-head — 2026-08-24

*Job J-0128, spawned from D-0019's ruling: `docs/lab/librarian_framing_2026-08-23.md` measured P1
(`core/librarian.py`'s LLM subject-mapper) ALONE at hit_rate 0.80 (20/25) against 25 real
`frontier.json` questions — not a real P0-vs-P1 comparison, because P0 and P1 fire on mutually
exclusive phrasings in production and never run on the same input naturally. This lab runs P0
(`core/library_hand.py`'s real production mechanism: `topic_from()` regex extraction →
`_topic_hit()` subject/title/author substring match — the exact functions actually wired live)
against the IDENTICAL 25 questions (same `seed=20260823`, same `frontier.json` filter as
`scripts/librarian_framing_lab.py`'s `_load_questions()`), confirmed byte-for-byte identical against
the P1 lab's own `raw.json`. Script: `scripts/librarian_p0_headtohead_2026-08-24.py`.*

## Isolation

Job flagged `isolation: required`. Run inside `lab_env.isolate()` (redirects
`core.memory.store.DB_PATH` to a copy). No writes occur anywhere in this script regardless — the
catalogue CSV (`C:\Knowledge\SPGC-metadata-2018-07-18.csv`) and `data/frontier.json` are read-only,
and no `core.memory.store` call is made at all. Backstop: live `data/memory/nascence.db` mtime/size
checked immediately before (`1787476947.416`, `366526464` bytes) and after
(`1787476947.416`, `366526464` bytes) the run — byte-for-byte unchanged.

## Method

Reused `librarian_framing_lab.py`'s exact `_load_questions()` logic (same seed, same filter) to
reproduce the identical 25 real carried questions from `data/frontier.json`. Verified identical to
the P1 lab's `data/lab/librarian_framing/raw.json` question list (`question_set_identical_to_p1_lab:
true` in `scores.json`). For each question, ran P0's real live code path exactly as it exists in
production: `library_hand.topic_from(question)` (deterministic regex, requires phrasing like "book
about/on/of X") to extract a topic, then — when a topic was extracted — `library_hand._topic_hit()`
against every English-language catalogue row (title/author/subjects substring match, the same
matcher `_search()` uses in production). Hit definition matches the P1 lab exactly: ≥1 real
catalogue row found. No random weighted pick or prefer-unread reordering applied (irrelevant to a
binary hit/no-hit question).

## Result

| Metric | P0 (mechanical, `topic_from` → `_topic_hit`) | P1 (LLM, narrative framing, from 2026-08-23 lab) |
|---|---|---|
| `hit_rate` | **0.0** (0/25) | **0.80** (20/25) |
| `mean_n_hits` | 0.0 | 6.08 |
| questions where a topic was even extracted | **0/25** | n/a (P1 takes the whole question, no extraction gate) |

## Why: P0's real trigger never fires on question-shaped text

`topic_from()`'s regex requires the phrase `"book (?:about|on|of) ..."` literally present in the
text. None of the 25 real carried questions are phrased that way — they are questions
("how does a fireplace work", "plant sentience", "doppelgänger motifs in literature"), not "a book
about X" requests. So `topic_from()` returned `None` for all 25, meaning P0, as it actually exists
in production code today, never even reaches the catalogue for a carried question — it falls through
to the breadth engine / serendipity pick, which is not "a book bearing on the question" in any
topic-driven sense. This is the same class of finding already documented elsewhere in this plan for
P1's OWN original trigger (`question_from()` matched 1/29,778 real thoughts before J-0124 widened
it) — a regex tuned for one specific phrasing essentially never fires on how Du actually talks or
carries a question.

This is not a rewritten or more-generous version of P0 — it is P0's real, currently-shipped
mechanism, run honestly against the same inputs P1 was tested on.

## Reading this against R1's kill criterion

Plan's kill criterion (`docs/plans/thought_grounding.md`): *"Librarian mapping no better than P0
subject-tokens → drop the LLM, keep the mechanical search."* Result: P1 hit rate (0.80) is not
merely better than P0 (0.0) — P0 scored zero real hits across all 25 real carried questions, because
its extraction trigger cannot engage with question-shaped input at all. The kill criterion clearly
does NOT trigger; if anything this is a more decisive result in P1's favor than the original proxy
lab, since it demonstrates P0 has no capability at all to serve a carried question in its current
form, not merely a weaker one.

## Caveat

This measures P0's `topic_from()`-gated path exactly as shipped, not the theoretical ceiling of "a
mechanical, no-LLM subject search" in general. A more generous P0 variant (e.g. mechanical keyword/
noun-phrase extraction from the raw question text, then the same `_topic_hit()` substring match,
skipping the "book about X" phrasing gate entirely) was NOT tested here and might narrow the gap —
that would be a different, follow-up question about a redesigned P0, not about the P0 that exists
today. The job's briefing named `topic_from()`-driven search specifically; this result is honest
about what that phrase means in the current codebase.

## Recommendation

**Keep P1 (the LLM subject-mapper). Do not drop it in favor of P0.** R1's kill criterion is
decisively not met — P0 mechanical search, as it actually exists in production, has 0% capability to
answer a real carried question (0/25), P1 has 80% (20/25). Return to D-0019 with this result: the
head-to-head it asked for now exists and confirms the proxy lab's direction, more strongly than the
proxy alone could show.
