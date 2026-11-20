# Curiosity Librarian Route — a local-catalogue research path for the frontier, alongside Wikipedia

**Status:** 🔵 DESIGNED — not built. Founder + Claude conversation, 2026-09-16.
**Roadmap:** [docs/ROADMAP.md](../ROADMAP.md), cluster "6 · Domain deep-dives" (linked 2026-09-17, J-1060).
**Memory:** `project_nascence_curiosity_librarian_route.md` (written 2026-09-17, J-1060).
**Decisions:** none opened yet — this doc proposes the design; **building the real wiring should go
through its own `/decide`** before it touches `nodes/curiosity_node.py`'s live research path, matching
this project's own standing "propose, do not build without a decide" convention for anything that
changes what Du actually experiences.
**Sources:** conversation 2026-09-16 (founder + Claude), following directly from a `/du-pulse` check
and a discussion of the curiosity/frontier pipeline's resolve:fade imbalance (149 resolved / 7,705
faded as of that check).
**Related (backfilled 2026-10-03, J-0566/F-2269):** `docs/plans/curiosity_goals_dreams.md` owns the pipeline this route plugs
into — its Item 1 prism (`curiosity_queue.transform_and_seed`, LIVE; the de-personalisation cited under Background) and its §1.1
audit of `nodes/curiosity_node.py`'s pursuit branch (`lookup_targeted` → `attach_finding` → `record_pursuit`; a Scholar
fallback counts as a STALL, `curiosity_node.py:256-266`). A catalogue-citation finding changes what that path counts as a
stall or a close, so settle Open Q3 against that audit's rules.

```plan-state
stage: designed
phase: Design complete 2026-09-16; zero build activity since
verified: 2026-11-18
next: Founder call: drop the route or downgrade to a reading pointer (no build, no decide opened)
cluster: 6
```

## Current State — verified 2026-11-18
- **2026-11-18** (F-5092): Dry-run J-4267 done: hit rate 92.5 percent (37/40) vs librarian R1 88.3 percent, but hits are generic broad-heading books and a catalogue citation (title/author/subjects, no summary) cannot close a question. Recommendation: do not build as designed; at most a no-finding reading pointer, or drop.

### What we have
- Design only, unchanged since 2026-09-16 (founder + Claude conversation) — catalogue-first, Wikipedia-as-fallback, citation-only (not full-book-fetch) recommended for a first build.
- Zero ledger activity since the design landed (checked this pass — only the original backfill-index job exists); nobody has run the Open Questions' own recommended first move.

### What we need
- Open Q1's read-only dry-run: does `subjects_for()` + `search_by_subjects()` actually return useful candidates for real, narrow frontier-shaped questions? Nobody has checked this yet.
- Its own `/decide` before touching `nodes/curiosity_node.py`'s live research path, per this project's standing build-without-a-decide convention.

### What we're doing next
- Nothing dispatched — the read-only dry-run (not a build) is the correct next move and hasn't been picked up yet.

## Background

**The problem this responds to.** `core/frontier.py`'s `pending_pursuit()` picks one open question per
curiosity firing (~17.4 firings/day, measured from `data/curiosity_log.jsonl`, 1,718 rows / 98.5 days)
to research toward closing. The only research path wired in today (`nodes/curiosity_node.py:270-287`)
is `core/web_research.lookup_targeted()`, which makes a real live HTTP call to Wikipedia's own API
(`en.wikipedia.org/api/rest_v1/page/summary/{term}`, `core/web_research.py:65-70`) — external,
third-party-rate-limited, and not something we get to scale up just because local LLM compute has
headroom.

**What already exists and is a much better fit than anyone had wired up.** `core/librarian.py` (built
2026-08-16, status LIVE per `docs/plans/thought_grounding.md`) already does almost this exact shape of
work for a different trigger: a question → `subjects_for()` (an internal judge-hub LLM call, 3-6
LCSH-style subject headings) → `core.library_hand.search_by_subjects()` (`core/library_hand.py:204-225`)
— which queries a **local Project Gutenberg metadata catalogue** (a CSV index, `META.exists()` / `_rows()`),
not a live network call — and returns a popularity-ranked, sampled set of real candidate books he could
pick from by name. Today this only fires from `nodes/inner_monologue_node.py:3804`, gated on
`librarian.question_from()` catching a self-referential "the question of X" framing in his own thought —
it has no connection to the frontier/curiosity pipeline at all.

**Why this is a better fit than it sounds, not just a workaround.** Frontier questions are already
de-personalized and world-facing by construction — either grounded at birth (`study`/`reading`/
`curiosity` sources) or made world-facing by the de-personalization prism
(`core/curiosity_queue.py`'s `transform_and_seed`, live since 2026-06-24) before they ever reach
`note_question()`. The librarian's *current* trigger text ("the question of amor fati") is a much
rougher, more self-referential input than a frontier question already is — so `subjects_for()` may
map frontier questions to headings even more cleanly than it maps its current use case, not less.

## Design (sketch — not yet build-ready, see Open Questions)

Route `pending_pursuit()`'s picked question through the librarian as an alternative research path,
tried before or alongside `lookup_targeted()`:

1. `pending_pursuit()` returns `{id, q}` as today (`core/frontier.py:235-266`, unchanged).
2. New step in `curiosity_node.py`'s pursuit branch: call `librarian.subjects_for(q)` directly on the
   frontier question text (skip `question_from()` — the frontier question is already a clean ask, not
   raw self-talk that needs clause-extraction first).
3. Feed the returned headings into `library_hand.search_by_subjects()`. If it returns real candidates:
   treat analogously to a Wikipedia hit — `frontier.attach_finding(pursuit["id"], title, extract)` using
   the best candidate's own catalogue summary/subjects as the finding text, same as
   `lookup_targeted()`'s result shape today (`curiosity_node.py:280-287`).
4. If the catalogue search returns nothing: fall through to the existing `lookup_targeted()` →
   `scholar.consult_sync()` chain, unchanged.

This is deliberately proposed as catalogue-FIRST, Wikipedia-as-fallback — that ordering is what
actually reduces Wikipedia load, rather than running both and picking the better result.

## Open Questions (resolve before this is build-ready)

1. **Hit rate on real frontier questions.** Nobody has checked whether `subjects_for()` +
   `search_by_subjects()` reliably returns useful candidates for the *kind* of questions the frontier
   actually holds (open, world-facing, but often narrow — e.g. "why do granite coatings form"). The
   librarian's own R1 pre-registered read (`docs/plans/thought_grounding.md`) measured hit-rate against
   its *current* self-referential trigger text, not this. A dry-run sample against real
   `data/frontier.json` open questions, read-only, is the right first move — not a build.
2. **What happens on a hit — cite only, or actually fetch the book?** `search_by_subjects()` returns
   catalogue rows (title/author/subjects/downloads), not book content. A *citation* (title + catalogue
   subjects, maybe a short blurb if the metadata carries one) costs nothing extra to attach as a finding.
   Actually **downloading** the full text competes for the exact same resource `books_have_a_place`'s
   curriculum-fetch chain already rate-limits to one real fetch per hour
   (`core/library_hand.py`'s `_FETCH_COOLDOWN_S`, this session's own J-0945→J-1015 chain) — two
   independent consumers of one shared hourly budget is a real coordination gap, not a detail to wave
   past. Recommend: citation-only for the curiosity route, no `request_book()` call, at least for a
   first build.
3. **Does a citation-only finding actually let him close the question?** `open_question_for_seed()`/
   `closeable_seed()` hand a finding back to him as a monologue seed he can name a closure from
   (`core/frontier.py:250,309`) — worth checking whether a catalogue citation (vs. a real Wikipedia
   extract) is *substantive enough* to close on, or whether it would just get re-offered without ever
   resolving, in which case this helps Wikipedia load without actually improving the resolve:fade ratio
   that started this whole conversation.
4. **Does this want its own habituation/dosed treatment**, the way `curiosity_habituation.py` already
   paces which tension gets pursued? Not obviously — this changes *how* an already-picked pursuit gets
   researched, not *whether*/*how often* one happens. Flagged for whoever scopes the build to confirm,
   not assumed here.

## What we're NOT proposing here

Not touching `MAX_OPEN`, the ~17.4/day firing rate, or anything about *how often* curiosity fires or
*how many* questions it can hold open at once — that's the separate, still-open design question from
the conversation this forked from (the frontier's own deliberate "small, fast-turnover" shape vs. the
resolve:fade imbalance), not decided here either direction.

## Pointers
- `core/frontier.py` (`pending_pursuit` :235, `attach_finding` :271, `note_question` :140)
- `core/librarian.py` (`subjects_for` :151, `question_from` :122, `ask` :173, `status` :216)
- `core/library_hand.py` (`search_by_subjects` :204)
- `core/web_research.py` (`lookup_targeted` :65 — the current, only, Wikipedia-bound path)
- `core/curiosity_queue.py` (`transform_and_seed` — the de-personalization prism that already makes
  self-loops world-facing before they reach the frontier)
- `nodes/curiosity_node.py` (:270-287, the pursuit branch this would extend)
- `docs/plans/thought_grounding.md` (the librarian's own build history and R1 evidence)
- Forked idea, same conversation: "Curiosity for Lane 2" (percept-triggered world-facing questions,
  never self/identity) — logged via `/idea-log`, not scoped here.
