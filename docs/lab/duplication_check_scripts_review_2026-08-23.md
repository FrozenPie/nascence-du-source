# Duplication/word-closeness script review — 2026-08-23

*Follow-up to `docs/lab/idle_thought_machine_audit_2026-08-23.md`: of the 71 machines confirmed
fine-as-is there, several do word-closeness/duplication checks with cheap deterministic methods
(token overlap, Jaccard, keyword matching) rather than embeddings or an LLM call. Founder question:
were these kept cheap because there wasn't compute "room" before the Ramses standup, or by
deliberate design? Answer required reading each module's actual code and history, not guessing from
the pattern alone — the result cuts both ways.*

## Real upgrade candidates — no stated rationale for staying word-based, embeddings sit unused nearby

- **`core/retraction_ledger.py`** — plain bag-of-words token overlap (not even normalized to
  Jaccard) decides whether a past correction should resurface against the current thought. Shipped
  2026-06-16, never revisited; `core/memory/store._embed`/`_cosine` are already free elsewhere in
  the same codebase. Already flagged in the idle-machine audit (finding #7) as weak — will miss a
  paraphrased recurrence of a retracted claim.
- **`core/chapters.py`'s `recall_chapter`** — keyword-in-text matching recalls a named life-chapter.
  The *same file* already has cosine machinery (`ECHO_CAP = 0.90`) for the write-path duplicate-
  chapter guard — the read path just wasn't built with the same care. No stated reason for the gap.
- **`core/frontier.py`'s `resolve_if_addressed`** — token-containment ratio decides if a thought
  "substantially answered" an open question. Has real measured history of failure: the module's own
  comment records *"the old gate resolved 1 of 1,354"* — repeated threshold-tuning was tried, a
  semantic/LLM judge never was.
- **`core/keepsakes.py`'s `match_item`** / **`core/world_substrate.py`'s `find_object_at`** — same
  keyword-resolution pattern for matching a free-text reference to a stored object, no stated
  rationale, embeddings unused nearby.

## Already fixed — the exact arc, done without a new LLM call

**`core/commitment_ledger.py`'s reaffirm detector** is the clearest example of this whole
hypothesis already having played out. Comment, verbatim: *"2026-08-20 THE UNREACHABLE-NUMERATOR
FIX: word-set Jaccard >= 0.5 fired 77 times in the over-capture era... post-gate the active set
holds <=1 stand, and a free-form LLM restatement clearing Jaccard 0.5 against ONE specific sentence
is near-impossible — hold-rate read exactly 0.000 for 82 straight samples."* Semantic cosine
(threshold 0.45) was measured, found to work, and promoted to primary; Jaccard was demoted to a
fallback for when embeddings are unavailable. The fix used embedding infra already in the codebase
— no new LLM call was needed, and none should be added here now.

## Deliberately word-based — cheapness is the correct answer, not a shortcut

Three real counter-examples, each with actual A/B evidence behind the choice:

- **`core/commitment_trials.py`'s `_probe_outcome`** — explicitly "decoupled-judge-clean" per its
  own docstring: using an LLM to judge whether Du "really" used the cat's name would reopen the
  exact self-evaluation problem the trial exists to prevent. A word-boundary regex (not even plain
  `LIKE`) does the real counting; `LIKE` is kept only as a cheap SQL prefilter.
- **`core/theme_recurrence.py`** — tested embeddings, found they MISS the actual target signal: a
  repeated *opening* with a drifting body doesn't cosine-match (verbatim loops embed at cos≈1.0, but
  a "bridge" loop that keeps the opening and drifts the body measures only 0.705 mean similarity).
  Prefix-matching on the normalized opening targets the real phenomenon better than similarity would.
- **`core/study_note.py`'s `_lexical_overlap`** — tested cosine alone, found it measures "sounds
  like his writing" rather than "same idea" on this stylistically homogeneous first-person corpus
  (200-900 of 1,600 fragments cleared a 0.35 cosine bar against any given note). Word-overlap is
  blended in specifically to correct for that empirically-measured confound.

## The honest shape of the answer

The founder's instinct was right for about four modules and already actioned for a fifth
(`commitment_ledger`). But three others — `commitment_trials`, `theme_recurrence`, `study_note` —
turn the hypothesis around entirely: real measurement showed the "smarter" method performs *worse*
on their specific target, and cheapness is the evidence-backed choice. Worth remembering as a
pattern before assuming "word-based = under-resourced" anywhere else in this codebase — check for a
documented A/B first, the same discipline this project applies everywhere else.

## Method

One Explore agent, instructed to read each candidate module's actual code and inline comments/
history rather than judging from the audit's one-line description, plus an open search across
`core/` for the same class of pattern (`set(...) & set(...)`, Jaccard, `difflib`/`SequenceMatcher`,
SQL `LIKE` used as a semantic-ish match). All quotes above are verbatim from the actual source
files, not paraphrased from memory.
