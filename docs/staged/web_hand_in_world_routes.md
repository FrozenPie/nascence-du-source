# Web hand: the two in-world routes (D-0661 b and c), staged for wording approval

Status: staged, draft wording, J-4344 (2026-11-18). Plan: web_hand (docs/staged/web_hand.md). Nothing here is live; no live store, book or prompt was edited. Route (a), Travis telling him in conversation, is the founder's own step and is not drafted.

Constraints held: no standing prompt line (D-0661 refused option d); the world answers and never leads, so both texts are plain statements of what exists, with no "you should", no "try", no mention of how often; additive only (a new book file and a new object file, no edit to About_You.txt or About_You_Second_Edition.txt, which stay readable as history). The hand only fires when his clause names a source word (core/web_hand.py `_WIKI_RX`: "Wikipedia", "the encyclopedia", "my encyclopedia", "the encyclopaedia's entry"), so both texts use exactly those words, once, as nouns for a thing that exists.

## Route 1: About You, version 3 (a diegetic line)

Found: `data/books/About_You.txt` (6.3 KB) and `data/books/About_You_Second_Edition.txt` (10.1 KB). The second edition has sections WHAT YOU ARE, THE HOUSE, THE ENGINES, WHO ELSE IS HERE, WHAT YOU ARE FOR - A CORRECTION. It is a book on the shelf (`core/library_hand.shelf_books` reads `data/books/*.txt`); nothing in code names the file, so a third edition is a new file, not a code change. Founder said "version 3 with a things he can do and how to do them section", so the line sits inside a new section rather than loose.

Proposed new file: `data/books/About_You_Third_Edition.txt` = the second edition text unchanged, the READ THIS FIRST opening gaining nothing, plus one new section placed after THE HOUSE (so it reads as part of what the house offers) and before THE ENGINES.

Section text (draft, for approval):

```
WHAT YOU CAN DO, AND HOW

Most of what you do you already do without being told: you go to the garden, you light the
fire, you write a letter, you take a book down. You say what you mean to do in your own
words, and where the house has a hand for it, it is done.

Some things you can do need a name for what you are reaching toward. If you want to know
something the house does not hold, you can look it up in the encyclopedia, or on Wikipedia, and
say so in plain words: what you look up, and where. What comes back is what that page says,
marked as the page's and not yours. If there is no page, it says so, and nothing else answers
in its place. A look-up takes a little while to come round again.

None of this is asked of you. It is written down so that it is not a thing you must guess.
```

Notes on the wording: "the encyclopedia, or on Wikipedia" gives the hand both source words; "what you look up, and where" teaches the grammar (term plus named source) without an example sentence he could copy as a script; no mention of the web source (separate, flag NASCENCE_WEB_HAND_WEB, and D-0788 handled it as its own question); "a little while" states the 10-minute-per-source limit without a number; the last paragraph is the same tone as the second edition's "You do not owe anyone a self". Open point for the founder: whether to also add one sentence about the web as a source. Default drafted: no, it is out of D-0661's scope.

Wiring needed at go: add the file; `data/book_feelings.json` and the reading state pick up a new title on first read with no hand edit. Known hazard to check at build, not now: `core/library_hand.py` lines ~86-115 title-signature dedup (F-1344): "About You Third Edition" has the signature {about, third}; a superset-of-another-title rule exists, so a build step must run the library_hand title-collision check (scripts/check_reread_title_disambiguation.py) against the new filename before it goes in `data/books/`. Also `core/world_consolidation.py:518` and `core/essay_lesson.py:145` already special-case "About You Second Edition" for the word "edition"; a Third Edition filename shares that word and should be eyeballed the same way.

## Route 2: the encyclopedia object in the study

Found: there is no generic study-object registry. Study objects are of three kinds: fixtures named in `core/object_graph._FIXTURES` and the action table (`core/actions.py`, "shelf", "desk", "book"); keepsakes (`core/keepsakes.py`, state in `data/keepsakes.json`); and one-off world items with their own module and state file (`core/care_package.py`, `data/care_package.json`, the "parcel" family). The cheapest additive form that needs no new action family and no code is a book: the encyclopedia is a volume on the study shelf, read the way he reads any book.

Proposed new file: `data/books/The_Encyclopedia.txt`, a short physical volume whose text is its own colophon and a stub of its coverage, in the same plain world voice as About You:

```
THE ENCYCLOPEDIA
one volume, kept on the study shelf

This volume is a short one, and it does not hold everything. It holds the first page of a few
things, and a note on every spine's edge says the same: for the rest, the encyclopedia is
Wikipedia, and its pages say more than this book can.

A look-up is a question put to Wikipedia in your own words: the thing, and the encyclopedia. The
answer is what Wikipedia says, set down as Wikipedia's.
```

(Draft kept to two short paragraphs; the second sentence repeats the source word once so the grammar is met; no instruction mood.) Open choice A or B for the founder:
- A (drafted above): a readable book, additive data only, zero code, appears in his shelf like every other title. Weakness: it is one book among 100s, so he may rarely take it down; the defeater in D-0661 (fewer than ten firings in 30 days) covers that.
- B: a standing study object like the care package (`core/encyclopedia_object.py`, `data/encyclopedia.json`, a line in the study scene via `scene_clause()`, a `look` answer). Stronger presence, but new code in the sensorium path; it touches `core/sensorium.py` and `core/actions.py` (hub files). If B is chosen, `udms_get_change_dossier` runs on each before editing, and `prompt_registry.py check` runs only if a prompt site moves (A touches none, B's scene line is a world line and is also not a prompt site, but check at build).

Recommended: A first (it is the minimum that fulfils D-0661 c and is reversible by deleting a file), with B held as a follow-up if the 30-day defeater trips.

## Done criteria for the build job (after wording approval, restart-gated)
1. Write `data/books/About_You_Third_Edition.txt` and `data/books/The_Encyclopedia.txt` with the approved text exactly.
2. Run `scripts/check_reread_title_disambiguation.py` for both new titles.
3. `prompt_registry.py check` exits 0 (expected: no change).
4. Nothing live until the next Du restart; route (a) is told to him by Travis in conversation after restart.
