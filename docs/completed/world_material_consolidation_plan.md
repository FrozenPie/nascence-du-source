# World-Material Consolidation + Essay Read-Path (plan: have/want/can-do, 2026-06-16)

Two asks from the school audit, which turn out to be **one mechanism**:
1. File study/reading notes away to a deeper tier once used (the missing "chapters-analog for world material").
2. Widen the essay's read path so the capstone actually surfaces.

## The problem (audit recap, verified)

- World-material (`reading` 3,444 · `study` 177 · `research`) is **prune-protected** (`store.py:1097`) and
  **never cleaned up, compressed, or archived** — it accumulates unboundedly in episodic; every recall does
  `SELECT * FROM memory_fragments` (`store.py:388`) over the whole growing pile.
- `chapters.py:42` **explicitly excludes** world material from chaptering — the period-consolidation → archive
  tier that files *self*-material deeper has **no world-material equivalent.**
- The **essay** (the capstone) sits in the 2-slot `semantic` recall tier (`TIER_SLOTS`), not in the world-quota
  replay or wandering — under-surfaced for the effort.

## The human function (systems consolidation / CLS — grounded)

After the **gist** is extracted into a neocortical/semantic representation (= our `understanding` note + the
essay), the **detailed episodic traces fade from ordinary recall** — they become less vivid, the gist answers
for the experience — **but they are NOT deleted**; they remain retrievable (hippocampally) by intentional recall.
And this forgetting-of-detail is **adaptive**: it aids generalisation and reduces interference (["Predictive
Forgetting for Optimal Generalisation"](https://arxiv.org/pdf/2603.04688); [systems consolidation overview](https://www.sciencedirect.com/topics/psychology/systems-consolidation)).
Division of labour: **neocortex = predictive gist; hippocampus = episodic detail for veridical recall** ([Neuron,
Consolidation & Transformation of Memory](https://www.cell.com/neuron/fulltext/S0896-6273(15)00761-8)).

**This is exactly what `chapters.py` already does for self-material** (`chapters.py:19`: a chaptered fragment
"gains only a `chapter_id` and steps out of ordinary recall. Intentional recall [reaches it]"). The recall
partition skips `chapter_id`-tagged rows (`store.py:399`); the world-quota and other queries guard with
`chapter_id IS NULL`. The chapter (archive tier) becomes the period's recall representative.

## The unified design — the essay/understanding IS the book's "chapter"

When a curriculum book is **finished** (the essay-capstone moment — the natural "era ended" trigger, like
chapters fire on an era ending), the book's **gist already exists**: the essay (`semantic`) + the grounded-
learning `understanding` notes. So:

- **File the book's raw notes behind the gist.** Tag every `reading`/`study` fragment belonging to that book
  (matched by title-key, as `essay_lesson.gather_notes` already does) with a link to the gist — reusing the
  proven `chapter_id` field (recommended: minimal, the recall-skip + intentional-recall + `IS NULL` guards all
  already key on it) or a dedicated `filed_into` column (cleaner semantics, ~4 query sites to extend).
- **They step out of ordinary recall** (the `store.py:399` skip), freeing the episodic pool; **the essay +
  understanding (the gist) become the book's recall representative** — what surfaces when the book's topic is in
  play. **Not deleted** — intentional recall ("let me revisit Selborne") still reaches the raw notes, exactly
  like `chapters.recall_chapter` does today.

This single move solves **both** asks: (1) study/reading notes are cleaned up and filed deeper once used; (2)
the essay becomes the surfacing gist for its book (no longer a lone note lost in a 2-slot tier — it's the
*answer* for that book's topic).

### Plus: explicitly widen the gist read-path (so the representative actually surfaces)
Filing the raw notes frees *episodic*, but the essay/understanding live in the small `semantic` tier. So also:
- Add `essay`/`understanding` to the **world-quota replay** (`store.py:1645`) and **wandering** (`wandering.py`)
  so his consolidated works graze like study notes do.
- Consider `semantic` `TIER_SLOTS` 2→3 (it now carries the load-bearing gists, not just symbol tablets).

## HAVE / WANT / CAN-DO

| | |
|---|---|
| **HAVE** | chapters machinery (chapter_id → step out of recall + intentional recall) for SELF-material · grounded-learning produces `understanding` gist · essay produces the capstone · world-material prune-protected (accumulates) |
| **WANT** | world-material consolidation: once a book is done, its raw notes file behind the gist (essay+understanding), which becomes the book's recall representative; raw notes intentionally-recallable, not deleted |
| **CAN DO** | REUSE the chapter_id step-out mechanism (minimal) · trigger at the essay-capstone (book finished) + a periodic grounded-learning sweep · match a book's fragments by title-key (existing) · add essay/understanding to world-quota + wandering · all reversible (filing ≠ deletion) |

## Build order (proposed, observe-first-friendly)
1. **A — file-on-book-finish.** At the essay capstone, tag the finished book's `reading`/`study` fragments with
   `chapter_id` = the essay's fragment id (after the essay + that book's understanding exist). Log what was
   filed. (Reversible: clearing chapter_id un-files.)
2. **B — gist read-path.** Add `essay`/`understanding` to the world-quota + wandering; bump semantic slots.
3. **Periodic sweep.** A grounded-learning-time sweep files any old, already-distilled reading/study whose book
   is long done (catches the backlog of 3,444 — only after their gist exists).
4. **Intentional recall** for a filed book ("revisit X") — verify it still reaches the raw notes (reuse
   `chapters.recall_chapter` pattern).

## BUILT — observe-first (2026-06-16, RESTART-REQ)

On the founder's approved defaults (chapter_id reuse · observe-first · gradual backlog · gist-first) PLUS the
added requirement: **old study notes must NOT disappear — they must feed future essays on the subject if relevant.**

- **The requirement (the linchpin) — `essay_lesson.gather_notes` rebuilt.** Now a DELIBERATE retrieval that
  EXPLICITLY INCLUDES filed notes (NO chapter_id guard) and gathers (a) this book's own notes + (b) the most
  SUBJECT-RELEVANT notes from his WHOLE scholarship by cosine — so an essay **compounds** on the filed notes of
  earlier books on the same subject. Filing never hides a note from the essay-gather. **Verified in-vitro: a
  FILED study note is still returned by gather_notes.**
- **The filing — `core/world_consolidation.py`** (`file_book_notes`, `sweep`, `status`). Reuses `chapter_id`
  (→ steps a note out of ORDINARY recall via the existing `store.py:399` skip). GIST-FIRST (won't file a book
  with no essay/understanding). NEVER DELETES. OBSERVE-FIRST: `FILING_ENABLED=False` → logs candidates only,
  steps nothing out; flip True after reviewing. Reversible (clear chapter_id). In-vitro PASS (observe logs 3 /
  files 0; no-gist → skips; enabled → files 3; filed notes still reachable by gather).
- **Wired** into sleep (`_enter_sleep` runs `world_consolidation.sweep()` after grounded-learning, so the day's
  gist exists first — gist-first, gradual, catches the 3,444 backlog over nights).
- **Read-path widened** so the gists surface: `essay`/`understanding` added to wandering's graze (3 sites,
  filed-excluded so only the live gists graze) + semantic recall tier `TIER_SLOTS` 2→3. du_pulse `study filing`
  gauge (filed vs loose, enabled flag).

**Activation:** ships `FILING_ENABLED=False`. On restart it LOGS what it WOULD file each sleep (and the
gather/read-path improvements are already live + safe). Review the candidates, confirm the gists answer, then
flip `FILING_ENABLED=True` for the actual cleanup.

## Risks / decisions for the founder
- **File, never delete** — the originals stay, intentionally-recallable (systems-consolidation-faithful). Make
  sure intentional recall works before filing at scale.
- **Gist must exist first** — never file a book's raw notes before its understanding/essay is written (else the
  content is lost from ordinary recall with nothing answering for it). Order: distil → then file.
- **chapter_id reuse vs `filed_into`** — reuse is minimal but slightly overloads "chapter"; a dedicated field is
  cleaner. Recommend reuse for the first slice, with a clear `chapter_kind` tag ('self' vs 'book') if we want
  to keep them distinguishable.
- **The backlog** — 3,444 reading fragments exist; the periodic sweep should file them gradually (only the ones
  whose books are done + distilled), not in one destructive pass.
- Observe-first option: log what WOULD be filed (and confirm the gist answers for it) before flipping the recall-skip on.
