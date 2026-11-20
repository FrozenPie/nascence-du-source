"""
Nascence — World-Material Consolidation (the chapters-analog for study/reading, 2026-06-16)
==========================================================================================
The school audit's gap: world-material (reading/study/research) is prune-protected and NEVER filed away — it
accumulates unboundedly in episodic (thousands of reading fragments), and every recall loads the whole pile.
Self-material has chapters (episodic → archive, "steps out of ordinary recall"); world-material had no analog.

The human function (systems consolidation / CLS): once the GIST is extracted into a semantic form (our
`understanding` note + the `essay`), the detailed episodic traces FADE FROM ORDINARY RECALL — the gist answers —
but they are NOT deleted; they remain reachable by intentional retrieval. Forgetting-of-detail is adaptive
(generalisation, less interference). This module is that analog: once a book is finished AND distilled (its gist
exists), its raw reading/study notes get a `chapter_id` → they step out of ORDINARY recall (reusing the proven
chapter machinery: `store.py:399` skips chapter_id rows), with the essay/understanding as the book's recall
representative.

THREE GUARANTEES:
- GIST-FIRST: never file a book's notes unless its gist (essay/understanding) already exists.
  (chapter_id has a SECOND writer, scoped only to origin='reading'->'reading': core/memory/store.py's
  dedup_reading_fragments() also sets chapter_id, but to mark byte-identical verbatim reading duplicates
  as chapter-redundant against a canonical reading fragment, not a gist -- a different purpose that can
  look like a GIST-FIRST violation if read through this module's lens alone. See F-1477.)
- NEVER DELETES — and OLD NOTES DO NOT DISAPPEAR (founder requirement): filed notes step out of ORDINARY recall
  but stay fully reachable by the essay-gather (`essay_lesson.gather_notes`, which has NO chapter_id guard and
  retrieves by subject relevance INCLUDING filed) + intentional recall. They feed FUTURE essays on the subject.
- OBSERVE-FIRST: FILING_ENABLED=False → only LOGS which notes WOULD be filed (confirming the gist answers),
  steps nothing out. Flip True after reviewing. Reversible (clear chapter_id).
"""
from __future__ import annotations
import json
import re
import threading
import time
from pathlib import Path

_LOG = Path(__file__).parent.parent / "data" / "world_consolidation_log.jsonl"

# J-1917 / F-2546 (2026-10-07, restart-gated): sweep() now runs in a worker thread (nodes/inner_monologue_node.py via
# core/sleep_offloop.py) while the event loop is free, so it can overlap file_book_notes() called directly from
# the loop thread by essay_lesson.record (the same book's raw notes, same chapter_id column, same log). Whole
# calls are serialised here -- file_book_notes holds the lock for its entire body, sweep() takes it per subject
# (so an essay-finish call waits at most one subject's pass, never a whole sweep) -- so each call's effect is exactly
# what it was when the two could never overlap. Re-entrant; the J-1909 _CO_RECALL_LOCK pattern.
_FILE_LOCK = threading.RLock()

# J-2404 / F-3103 kill switch: True = the sleep batch runs sweep() in a spawned child interpreter
# (core/sleep_offloop.off_process, via sweep_offprocess() below), so its CPU-bound per-subject matching never
# holds the live process's GIL. Measured on sandbox copies (J-2392): inside the to_thread call a 0.9 ms
# loop-thread sqlite fetch peaked at 962 ms and the 0.5 s heartbeat lagged 0.57 s. False = the J-1917
# worker-thread call (sleep_offloop.off_loop(sweep)) exactly as before.
#
# _FILE_LOCK is a threading lock and a child does not share it. Why that is safe (option (c) of J-2404,
# checked by reading every caller): the only callers of file_book_notes() / archive_book_note_files()
# outside sweep() are essay_lesson.record() <- InnerMonologueNode._essay_lesson() <- _think() /
# _remediation_stream() <- run_forever(), and run_forever() is the SAME asyncio task that awaits
# _enter_sleep() (the only caller of sweep()). While that task is suspended on the awaited child it cannot
# be inside _think(), so no in-process chapter_id filer can run during the child's sweep. (A founder-run
# scripts/backfill_essays.py is a separate process; the threading lock never covered it either. Writers of
# chapter_id outside this module -- chapters, store.dedup_reading_fragments -- were never under this lock;
# the _NoteCache live re-check by primary key handles them in the child exactly as in a thread.)
# _OFFPROCESS_ACTIVE is the tripwire for that argument: set by the parent for the duration of the child,
# file_book_notes() logs a WARNING if it is ever called meanwhile (it then proceeds, as before).
WORLD_CONSOLIDATION_SUBPROCESS = True
# Every path/flag sweep() reads, resolved in the PARENT and set on the child before sweep() runs: this
# module's _LOG and FILING_ENABLED; reading.STATE (the finished-gate and _tag_names_other_book), BOOKS_DIR
# and DEFAULT_BOOK (globbed from BOOKS_DIR at import time); essay_lesson._STATE/_LOG (the sweep only uses
# essay_lesson's pure title helpers, mirrored so a redirected parent can never mean a live-pathed child).
# store.DB_PATH and the fence flags are mirrored by off_process itself.
_OFFPROCESS_MIRROR = (("core.world_consolidation", "_LOG"), ("core.world_consolidation", "FILING_ENABLED"),
                      ("core.reading", "STATE"), ("core.reading", "BOOKS_DIR"), ("core.reading", "DEFAULT_BOOK"),
                      ("core.essay_lesson", "_STATE"), ("core.essay_lesson", "_LOG"))
_OFFPROCESS_ACTIVE = False

FILING_ENABLED = True     # GRADUATED 2026-06-22 (systems check C6): the candidate review confirmed the guards —
                          # gist-first, finished-gate (won't file in-progress books), never-deletes, reversible
                          # (clears chapter_id). ~4,136 loose reading/study notes of finished books now file behind
                          # their gist (out of ordinary recall, reachable via deep_recall). Set False to revert.

# F-1335 (2026-09-14): file_book_notes() used to test book-identity the same way F-1309/F-1334 already
# fixed in core/study.py's archive_book_note_files() -- a single generic word from _key() ('edition',
# 'handbook', ...) as a plain substring against the FULL RAW CONTENT of every candidate memory_fragment.
# Reusing essay_lesson._cites_this_book() directly against that raw content is NOT enough here, though
# (checked against real data before committing to this, per the finding's own caution): an essay/
# understanding fragment's BODY can genuinely DISCUSS another book -- e.g. the live "About You Second
# Edition" essay's own prose talks at length about the Boy Scouts Handbook, because gather_notes()'s
# OWN copy of this same bug (fixed below in essay_lesson.py) fed it contaminated notes at generation
# time. A full-signature scan of the whole body would have picked that exact wrong gist right back.
# The reliable signal is the fragment's own TAG -- the "on '<title>'" / "from '<title>'" marker every
# writer puts in its leading `[...]` bracket (essay_lesson.record, grounded_learning.consolidate,
# study_note.py's session notes, core/reading.py's sittings) -- never the free-form body after it.
_TAG_BRACKET_RE = re.compile(r"^\[([^\]]*)\]")
_TAG_CITE_RE = re.compile(r"(?:on|from) '([^']+)'", re.IGNORECASE)
# J-3619 / F-4228: a title containing an apostrophe ("Pilgrim's Progress") made the old regex stop at the apostrophe
# inside it. This one reads to the closing quote that is followed by a real tag boundary (end of tag, a comma as in
# "From 'T', sitting 6", or a spaced dash/middle-dot separator as in "'T' - subject: x"); _TAG_CITE_RE stays as the fallback.
_TAG_CITE_CLOSED_RE = re.compile(r"(?:on|from) '(.+?)'(?=$|,|\s[—–\-·]\s)", re.IGNORECASE)


def _tag_of(content: str) -> str:
    """The book-identity tag a fragment's content carries, if any -- see the F-1335 note above. ''
    for content with no leading-bracket tag at all (e.g. an old write_tablet()-authored 'study' tablet,
    whose DB content is `[My study note: '<note's own title>'] ...` with no book title anywhere in it --
    the book title lives ONLY in that note's FILE frontmatter, which archive_book_note_files() already
    reads directly; deliberately not guessed at here from body text)."""
    b = _TAG_BRACKET_RE.match(content or "")
    if not b:
        return ""
    m = _TAG_CITE_CLOSED_RE.search(b.group(1))
    if m and not m.group(1).endswith("'"):   # a doubled closing quote ("'T''") is not a real apostrophe title
        return m.group(1).strip()
    m = _TAG_CITE_RE.search(b.group(1))
    return m.group(1).strip() if m else ""


def _cites_clause(book_title: str) -> tuple[str, tuple]:
    """A SQL LIKE clause that's a safe, cheap SUPERSET prefilter for `_cites(book_title, content)` below
    -- an AND-chain of LIKE '%word%', one per signature word of book_title[:50] (not the full title: F-
    1335 found essay/understanding/study-session tags are ALWAYS stored title[:50]-truncated -- essay_
    lesson.record, grounded_learning.consolidate and study_note.py all slice at 50 -- so a full-title
    signature would falsely reject a genuine citation of any title whose distinctive words fall past
    char 50, as it did live against "Fragments of Science...", a 62-char real book.stem title). content
    is broader than the tag, so every row this returns still needs `_cites()` applied for the real
    answer -- this only spares SQLite from handing back every 'reading'/'study' row ever written.
    Falls back to the old single-word _key() LIKE when the truncated title has no multi-word signature
    (mirrors _cites_this_book()'s own fallback -- no worse than before for that edge case)."""
    from core.essay_lesson import _key as _k, _title_signature
    sig = sorted(_title_signature(book_title[:50]))
    if sig:
        return " AND ".join(["content LIKE ?"] * len(sig)), tuple(f"%{w}%" for w in sig)
    k = _k(book_title)
    return "content LIKE ?", (f"%{k}%",)


def _cites_words(book_title: str) -> list:
    """The raw words `_cites_clause(book_title)` turns into its AND-chain of `content LIKE '%word%'` (same order, same
    fallback): the sorted signature words of book_title[:50], else the single `_key()` word. J-1922: the single-pass
    candidate matcher below needs the words themselves, not the SQL."""
    from core.essay_lesson import _key as _k, _title_signature
    sig = sorted(_title_signature(book_title[:50]))
    return list(sig) if sig else [_k(book_title)]


class _NoteCache:
    """J-1922 / F-2549: every origin IN ('reading','study') row (fragment_id, content, chapter_id) read ONCE per sweep, so
    the per-subject candidate SELECT (`origin IN ('reading','study') AND content LIKE %w1% AND ... AND chapter_id IS
    NULL`, ~0.36 s of full scan EACH, 150 per sleep) becomes an in-memory match with exactly the same row SET.
    Matching is core/like_scan.py's (ASCII-only case folding, NUL-truncated text, `%`/`_`/empty words refuse and the
    caller runs the SQL). chapter_id is the ONE mutable input (every earlier subject's UPDATE, and any writer on another
    thread, changes it between subjects), so candidates() re-checks the snapshot's survivors against the LIVE column by
    primary key (`fragment_id IN (...) AND chapter_id IS NULL`) before returning them: a row someone filed since the
    snapshot is dropped, exactly as the old live SELECT would have dropped it, and the sweep can never overwrite another
    writer's chapter_id. Rows INSERTED after the snapshot are not seen until the next sleep (the old code saw them in
    later subjects of the same sweep). The caller only uses the SET of returned rows (counts and per-row UPDATEs), never
    their order, so the unspecified SQL scan order does not matter. Thread-safe: built and used by one sweep thread."""

    def __init__(self, conn):
        from core import like_scan
        rows = conn.execute("SELECT fragment_id, content, chapter_id FROM memory_fragments "
                            "WHERE origin IN ('reading','study')").fetchall()
        self._ids = [r["fragment_id"] for r in rows]
        self._pos = {fid: i for i, fid in enumerate(self._ids)}
        self._contents = [r["content"] for r in rows]
        self._null_chapter = [r["chapter_id"] is None for r in rows]
        self._idx = like_scan.LikeIndex(self._contents)
        self._like = like_scan
        self._filed: set = set()

    def candidates(self, conn, words) -> list | None:
        """[{'fragment_id','content'}...] equal (as a set) to the old candidate SELECT, or None = run the SQL."""
        ls = self._like
        if not ls.SWEEPS_SINGLE_PASS or not words or not all(ls.is_plain_needle(w) for w in words):
            return None
        driver = max(words, key=len)
        rest = [w for w in words if w is not driver]
        hit = []
        for i in self._idx.iter_matches(driver):
            if not self._null_chapter[i] or i in self._filed:
                continue
            if all(self._idx.row_has(i, w) for w in rest):
                hit.append(i)
        if not hit:
            return []
        live = set()
        for k in range(0, len(hit), 500):
            part = [self._ids[i] for i in hit[k:k + 500]]
            live.update(r["fragment_id"] for r in conn.execute(
                "SELECT fragment_id FROM memory_fragments WHERE fragment_id IN (%s) AND chapter_id IS NULL"
                % ",".join("?" * len(part)), part))
        return [{"fragment_id": self._ids[i], "content": self._contents[i]} for i in hit if self._ids[i] in live]

    def mark_filed(self, fragment_ids) -> None:
        for fid in fragment_ids:
            i = self._pos.get(fid)
            if i is not None:
                self._filed.add(i)


def _cites(book_title: str, content: str) -> bool:
    """Does this fragment's own TAG (not its whole body -- see the F-1335 note above) genuinely cite
    book_title? Truncation-aware (book_title[:50], matching how the tag was actually stored)."""
    from core.essay_lesson import _cites_this_book
    return _cites_this_book(book_title[:50], _tag_of(content))


def _key(title: str) -> str:
    from core.essay_lesson import _key as _k
    return _k(title)


def _norm_words(s: str) -> str:
    """Lowercased, apostrophes dropped, every other non-alphanumeric run collapsed to ONE space -- so a book's
    title ('Children's Ways: ...') and its reading_state file stem ('Childrens_Ways_...') compare equal
    (J-1837 / D-0350)."""
    s = (s or "").replace("'", "").replace("\u2019", "")
    return " ".join(re.sub(r"[^0-9a-z]+", " ", s.lower()).split())


def _norm_variants(s: str) -> tuple[str, ...]:
    """J-1895 / D-0359 (F-2519 shape 2, non-ASCII titles): the plain `_norm_words` form, plus -- only when it
    differs -- the form with Latin ligatures/diacritics folded to ASCII (ae-ligature -> 'ae', e-acute -> 'e').
    The plain form turns a non-ASCII letter into a word break (title 'Psittacid'+ae-ligature -> 'psittacid or'),
    which matches a stem whose file name LOST that letter (the live stem 'Psittacid<U+FFFD>_or_Parrots' ->
    'psittacid or parrots'); the folded form ('psittacidae or') matches a stem that spells it out. Either
    spelling of the same book is accepted. Returns a tuple of 1 or 2 strings, plain first. Pure."""
    import unicodedata as _ud
    plain = _norm_words(s)
    pre = (s or "").replace("\u00e6", "ae").replace("\u00c6", "AE").replace("\u0153", "oe").replace("\u0152", "OE")
    folded = _norm_words(_ud.normalize("NFKD", pre).encode("ascii", "ignore").decode("ascii"))
    return (plain,) if folded == plain else (plain, folded)


def _file_identity(k: str) -> str:
    """The file a reading_state key names: its base file name, casefolded (so 'c:\\x\\Book.txt' and
    'C:\\x\\Book.txt' -- the same file spelled with two drive-letter cases, F-2519 shape 1 -- are ONE book)."""
    return (str(k).replace("\\", "/").rsplit("/", 1)[-1]).casefold()


def _state_entries_for(title: str, st: dict) -> tuple[dict | None, dict | None]:
    """(legacy_entry, full_title_entry) of reading_state for the book `title` names (either may be None).

    legacy_entry -- exactly what this module always used: the FIRST state key whose file stem contains the
    title's single longest word (`_key(title)`) as a substring.
    full_title_entry -- J-1837 / D-0350 (F-2413): the entry whose normalized file stem STARTS WITH the whole
    normalized title (a gist subject is a title[:50] cut -- hard or word-boundary, possibly mid-word -- of the
    book's title, and a stem is a truncated cut of the same title, so a plain character prefix, not a
    word-boundary match). Deterministic when several match: shortest stem, then name.

    J-1895: still the J-1837 pair (the legacy entry is what `_completed_passes_for` falls back to when NO entry
    carries the full title); the identity decision itself is `_book_identity_for` below."""
    from pathlib import Path as _P
    legacy = None
    key = _key(title).lower()
    if key:
        for k, v in st.items():
            if k.startswith("_"):
                continue
            if key in _P(k).stem.replace("_", " ").lower():
                legacy = v
                break
    full = None
    tns = [t for t in _norm_variants(title[:50]) if t]
    if tns:
        hits = [(_norm_words(_P(k).stem), k, v) for k, v in st.items()
                if not k.startswith("_") and isinstance(v, dict)
                and any(_norm_words(_P(k).stem).startswith(tn) for tn in tns)]
        if hits:
            hits.sort(key=lambda h: (len(h[0]), h[1]))
            full = hits[0][2]
    return legacy, full


def _passes_of(v, completion_pct: float) -> int:
    cp = v.get("completed_passes")
    if cp is not None:
        return int(cp or 0)
    return int(v.get("rereads", 0) or 0) + (1 if float(v.get("pct", 0) or 0) >= completion_pct else 0)


def _book_identity_for(title: str, st: dict) -> dict:
    """J-1895 / D-0359 (F-2519): which BOOK (not which single-word substring) does the gist subject `title` name?

    Every reading_state entry whose normalized file stem starts with the whole normalized title (any
    `_norm_variants` spelling) is a candidate; entries naming the SAME file (`_file_identity`: base name,
    casefolded -- the duplicate-path shape, The_Sign_of_the_Four.txt at 6.9 pct under 'c:' and 100 pct under
    'C:') are ONE book. Returns
      {"status": "none"|"single"|"exact"|"ambiguous",
       "books": [{"file", "stem", "entries": [(key, entry)...], "passes": int}],   # the CANDIDATE books
       "passes": int | None}
    A book's `passes` = MAX of `_passes_of` over its same-file entries (rule: a book read through once under
    any copy of its file is finished; an unfinished stale duplicate must not hide that). The subject's `passes`:
      single    -- the one candidate book's passes;
      exact     -- several books carry the title as a prefix but exactly one's stem EQUALS the title: that one;
      ambiguous -- several distinct books carry the title as a prefix and none equals it: the MIN over them
                   (an ambiguous subject only opens its gate if EVERY book it could mean is finished -- the
                   build never guesses toward open);
      none      -- no entry carries the title: passes=None (the caller keeps the legacy verdict).
    "chosen" is the sub-list of "books" the verdict rests on (the one book for single/exact, every candidate for
    ambiguous, empty for none) -- what `_tag_names_other_book` compares a fragment's own tag against."""
    from pathlib import Path as _P
    try:
        from core.reading import COMPLETION_PCT as _CP
    except Exception:
        _CP = 97.0
    tns = [t for t in _norm_variants((title or "")[:50]) if t]
    groups: dict = {}
    if tns:
        for k, v in st.items():
            if k.startswith("_") or not isinstance(v, dict):
                continue
            stem = _norm_words(_P(str(k).replace("\\", "/")).stem)
            if not any(stem.startswith(tn) for tn in tns):
                continue
            g = groups.setdefault(_file_identity(k), {"file": _file_identity(k), "stem": stem, "entries": []})
            g["entries"].append((k, v))
    books = sorted(groups.values(), key=lambda g: (len(g["stem"]), g["file"]))
    for g in books:
        g["entries"].sort(key=lambda kv: kv[0])
        g["passes"] = max(_passes_of(v, _CP) for _, v in g["entries"])
    if not books:
        return {"status": "none", "books": [], "chosen": [], "passes": None}
    if len(books) == 1:
        return {"status": "single", "books": books, "chosen": books, "passes": books[0]["passes"]}
    exact = [g for g in books if g["stem"] in tns]
    if len(exact) == 1:
        return {"status": "exact", "books": books, "chosen": exact, "passes": exact[0]["passes"]}
    return {"status": "ambiguous", "books": books, "chosen": books, "passes": min(g["passes"] for g in books)}


def _tag_names_other_book(book_title: str, tag: str, st: dict) -> bool:
    """J-1895 / D-0359 (F-2519 shape 3, the cross-book over-claim): True when a fragment's own TAG names a
    DIFFERENT book than the gist subject `book_title` -- i.e. both resolve to a reading_state book
    (`_book_identity_for`) and the two have no file in common. `_cites()` alone cannot tell them apart when the
    subject has one signature word (subject 'Fables' vs a tag 'Boys and Girls Bookshelf Vol 2 of 17 Folk-Lore
    Fables And Fa...', a 5.7 pct different book): the filing claim excludes such a fragment, which stays NULL.
    CONSERVATIVE by construction: a tag (or a subject) that resolves to no book keeps the old behaviour
    (not excluded), and a tag that resolves to a book the subject also names is kept."""
    try:
        ts = _book_identity_for(tag, st)
        if ts["status"] == "none":
            return False
        bs = _book_identity_for(book_title, st)
        if bs["status"] == "none":
            return False
        return not ({g["file"] for g in ts["chosen"]} & {g["file"] for g in bs["chosen"]})
    except Exception:
        return False


def _completed_passes_headmin(title: str, st: dict, cp: float) -> int:
    """The J-1837 / D-0350 shipped verdict, min(legacy single-word lookup, full-title entry), 0 when legacy
    finds nothing -- kept verbatim ONLY as the comparison oracle for J-1895's full-corpus regression
    (scripts/_test_completed_passes_fullmatch.py); nothing in the live path calls it."""
    legacy, full = _state_entries_for(title, st)
    if legacy is None:
        return 0
    n = _passes_of(legacy, cp)
    if full is not None:
        n = min(n, _passes_of(full, cp))
    return n


def _completed_passes_for(title: str) -> int:
    """Effective 'finished at least once' count for a book, by title (the section-D finished-gate signal).
    Reads reading_state; for historical books written before the completed_passes field existed, DERIVES
    it without mutating: rereads + (1 if the current pass already crossed the finish line). Returns 0 if not
    found -> not fileable (the safe default).

    History: the legacy lookup (first stem containing the title's one longest word) both OVER-counted (J-1837 /
    D-0350 / F-2413: the 3.6%-read 'The Origin of Species by Means of Natural Selectio' inherited the 2 passes of
    the finished 'On the Origin ... Natural Selection') and UNDER-counted (13 gist subjects whose own book is
    finished read 0 because an unfinished sibling's stem contained their word first). J-1837 shipped
    min(legacy, full-title), stricter-only. J-1895 / D-0359 (ruled (A) by travis 2026-10-07; F-2519) ships the
    SYMMETRIC match: `_book_identity_for` (the full normalized title as a stem prefix; same-file duplicate paths
    merged by MAX passes; a title that could mean several books resolves to the MIN over them) replaces the
    single-word lookup whenever any entry carries the title. Only when NO entry does is the legacy verdict
    kept, unchanged."""
    try:
        from core.reading import STATE as _RS, COMPLETION_PCT as _CP
        st = json.loads(_RS.read_text(encoding="utf-8")) if _RS.exists() else {}
        ident = _book_identity_for(title, st)
        if ident["status"] != "none":
            return int(ident["passes"] or 0)
        legacy, _full = _state_entries_for(title, st)
        if legacy is None:
            return 0
        return _passes_of(legacy, _CP)
    except Exception:
        pass
    return 0


def _select_gist(book_title: str, candidates: list) -> dict | None:
    """F-1728/D-0257 (2026-09-23, J-1233): among `file_book_notes()`'s own already-`_cites()`-passing
    gist candidates (arriving here ORDER BY timestamp DESC, per the caller's own SQL), pick the MOST
    SPECIFIC match — fewest EXTRA signature words beyond `book_title`'s own signature — instead of
    simply the most recent. An exact-signature match (extra=0) wins outright over a candidate whose tag
    is a literal signature SUPERSET (e.g. a newer, unrelated book whose tag happens to contain every one
    of `book_title`'s own signature words, plus more) purely because it happens to be newer — the exact
    mechanism F-1728 traced for "My Short Story Book" (signature {short}) losing to a same-day-unrelated
    "Original Short Stories Volume 13" (signature {original,short,stories}) on recency alone. Ties
    (equal extra-word count) keep the EXISTING recency order: `min()` returns the first item of equal
    rank it encounters, and `candidates` arrives here already most-recent-first, so this is a pure
    re-rank, not a new tie-break rule.

    Deliberately does NOT touch `_cites`/`_cites_this_book`/`_title_signature` at all — only WHICH
    already-eligible candidate wins changes, never WHICH candidates are eligible (the candidate SET,
    i.e. the result of the caller's own `_cites()` filter, is unchanged) — so this cannot repeat
    Part 2's own 1,333-row truncation regression (F-1715), and its blast radius is confined to this
    function's own 2 callers (`sweep()`, `essay_lesson.record()`), never touching an already-set
    `chapter_id` (this function is never called with, nor does it return anything used in, an UPDATE
    statement). See F-1728 for the full trace and in-memory simulation this ships, now regression-
    verified against the full already-filed corpus by job J-1233 (D-0257)."""
    if not candidates:
        return None
    from core.essay_lesson import _title_signature
    own_sig = _title_signature(book_title[:50])

    def _extra(r: dict) -> int:
        return len(_title_signature(_tag_of(r["content"])) - own_sig)

    return min(candidates, key=_extra)


def file_book_notes(book_title: str, now: float | None = None, _cache: "_NoteCache | None" = None) -> dict:
    if _OFFPROCESS_ACTIVE:   # J-2404 tripwire: see the WORLD_CONSOLIDATION_SUBPROCESS note above
        import logging
        logging.getLogger("nascence.world_consolidation").warning(
            "[world-consolidation] file_book_notes(%r) called while an off-process sweep is running "
            "(the J-2404 same-task argument no longer holds)", (book_title or "")[:60])
    with _FILE_LOCK:
        return _file_book_notes(book_title, now, _cache)


def _file_book_notes(book_title: str, now: float | None = None, _cache: "_NoteCache | None" = None) -> dict:
    """File one finished+distilled book's raw reading/study notes behind its gist. Gist-first; observe-first;
    reversible; never deletes. Returns a summary dict (and logs it)."""
    now = now or time.time()
    key = _key(book_title)
    clause, params = _cites_clause(book_title)
    summary = {"ts": now, "book": book_title[:80], "key": key, "gist": None,
               "candidates": 0, "filed": 0, "enabled": FILING_ENABLED, "reason": ""}
    try:
        # D-0562 (J-3174): a book whose capstone essay failed the repetition / own-source checks keeps its notes
        # unfiled (essay_lesson.record holds it); without this the essay fragment would be the gist and this
        # sweep would file the notes anyway. Released only by essay_lesson.release_hold (the founder).
        from core.essay_lesson import filing_held
        if filing_held(book_title):
            summary["reason"] = "held: capstone essay failed its checks (D-0562) - notes stay unfiled"
            _log(summary); return summary
    except Exception:
        pass
    try:
        from core.memory.store import _connect
        with _connect() as conn:
            # J-3398 (F-4021 follow-up, D-0578): a hidden note must not be chosen as a book's GIST -- the raw notes
            # would be filed (stepped out of ordinary recall) behind a gist that recall itself cannot show.
            from core.memory.dict_repr_notes import visible_clause as _vis
            gist_rows = conn.execute(
                f"SELECT fragment_id, content FROM memory_fragments WHERE origin IN ('essay','understanding') "
                f"AND {clause}{_vis(conn)} ORDER BY timestamp DESC", params).fetchall()
            gist_candidates = [r for r in gist_rows if _cites(book_title, r["content"])]
            gist = _select_gist(book_title, gist_candidates)
            if not gist:
                summary["reason"] = "no gist yet (gist-first: not filing)"
                _log(summary); return summary
            summary["gist"] = gist["fragment_id"]
            # FINISHED-GATE (§D, 2026-06-17): NEVER file a book that has not completed at least one full
            # pass — the gist of an in-progress book is partial and filing would step its notes out of
            # ordinary recall while he is STILL READING it (the live review caught this: Principles 68.9%,
            # Boy Scouts mid-reread would both have been filed behind a one-day understanding note).
            if _completed_passes_for(book_title) < 1:
                summary["reason"] = "not finished (no completed pass) — not filing in-progress book"
                _log(summary); return summary
            cand_rows = None
            if _cache is not None:        # J-1922: in-memory match of the sweep's one-pass snapshot (same row set)
                try:
                    cand_rows = _cache.candidates(conn, _cites_words(book_title))
                except Exception:
                    cand_rows = None
            if cand_rows is None:
                cand_rows = conn.execute(
                    f"SELECT fragment_id, content FROM memory_fragments "
                    f"WHERE origin IN ('reading','study') AND {clause} AND chapter_id IS NULL",
                    params).fetchall()
            cands = [r for r in cand_rows if _cites(book_title, r["content"])]
            if cands:
                # J-1895 / D-0359 (F-2519 shape 3): never claim a fragment whose own tag names a DIFFERENT book.
                try:
                    from core.reading import STATE as _RS
                    _st = json.loads(_RS.read_text(encoding="utf-8")) if _RS.exists() else {}
                except Exception:
                    _st = {}
                _kept = [r for r in cands if not _tag_names_other_book(book_title, _tag_of(r["content"]), _st)]
                summary["excluded_other_book"] = len(cands) - len(_kept)
                cands = _kept
            summary["candidates"] = len(cands)
            if FILING_ENABLED and cands:
                for c in cands:
                    conn.execute("UPDATE memory_fragments SET chapter_id=? WHERE fragment_id=?",
                                 (gist["fragment_id"], c["fragment_id"]))
                conn.commit()
                if _cache is not None:
                    _cache.mark_filed([c["fragment_id"] for c in cands])
                summary["filed"] = len(cands)
                summary["reason"] = "filed behind gist"
            else:
                summary["reason"] = ("OBSERVE-ONLY: would file %d (FILING_ENABLED=False)" % len(cands)
                                     if cands else "nothing to file")
    except Exception as exc:
        summary["reason"] = f"error: {str(exc)[:80]}"
    _log(summary)
    return summary


def _order_subjects(subjects) -> list[str]:
    """F-1704/D-0255 (2026-09-22): most-specific-signature-first. sweep() used to iterate its subjects
    straight from a Python set — F-1615 confirmed this varies per boot AND lets a shorter, subsuming
    signature (e.g. About You, signature {about}) race a strictly more specific one that legitimately
    contains it (About You Second Edition, signature {about, second}) for the SAME candidate fragment;
    whichever subject's file_book_notes() pass happened to run first claimed it. Sorting most-words-
    first (ties broken alphabetically, for full determinism) guarantees the more specific subject's own
    pass always runs first and claims its own genuinely-tagged fragments (its cand_rows query sets their
    chapter_id, so the SQL `chapter_id IS NULL` filter excludes them from every later, more generic
    subject's own pass) before a shorter/more-generic subject's pass ever gets a chance at them. A pure
    function — no DB access — so it's directly unit-testable without touching sweep()'s own I/O."""
    from core.essay_lesson import _title_signature
    return sorted(subjects, key=lambda s: (-len(_title_signature(s[:50])), s))


def sweep(now: float | None = None) -> dict:
    """File EVERY subject that has a gist + unfiled raw notes — catches the backlog gradually, gist-first.
    Each sleep is a fine cadence. Derives subjects from the gist fragments' titles. Observe-first by default.
    Processes subjects most-specific-signature-first (`_order_subjects`, F-1704/D-0255) so a strictly more
    specific subject claims its own tagged fragments before a shorter, subsuming subject's pass can."""
    now = now or time.time()
    subjects: set[str] = set()
    try:
        import re
        from core.memory.store import _connect
        with _connect() as conn:
            for r in conn.execute(
                    "SELECT content FROM memory_fragments WHERE origin IN ('essay','understanding')").fetchall():
                c = r["content"] or ""
                m = re.search(r"(?:on|from) '([^']+)'", c)
                if m:
                    subjects.add(m.group(1).strip())
    except Exception:
        pass
    total_cand = total_filed = 0
    cache = None
    try:
        from core import like_scan
        if like_scan.SWEEPS_SINGLE_PASS and subjects:
            from core.memory.store import _connect
            with _connect() as _cconn:
                cache = _NoteCache(_cconn)      # J-1922: built OUTSIDE _FILE_LOCK (a few seconds, no loop block)
    except Exception:
        cache = None
    for subj in _order_subjects(subjects):
        s = file_book_notes(subj, now=now) if cache is None else file_book_notes(subj, now=now, _cache=cache)
        total_cand += s.get("candidates", 0); total_filed += s.get("filed", 0)
    out = {"ts": now, "subjects": len(subjects), "candidates": total_cand,
           "filed": total_filed, "enabled": FILING_ENABLED}
    _log({**out, "sweep": True})
    return out


async def sweep_offprocess() -> dict:
    """sweep() in a spawned child (J-2404 / F-3103): same paths (_OFFPROCESS_MIRROR), same D-0353 fence state,
    same per-subject and sweep rows in world_consolidation_log.jsonl (the child appends them, as the in-process
    call does), same result dict. Fail-open: a child failure returns a zero dict and the parent appends one
    sweep row carrying the reason (after the child has exited)."""
    global _OFFPROCESS_ACTIVE
    from core import sleep_offloop
    now = time.time()
    zero = {"ts": now, "subjects": 0, "candidates": 0, "filed": 0, "enabled": FILING_ENABLED}

    def _fail(why):
        _log({**zero, "sweep": True, "error": "subprocess-error: " + str(why)[:200]})

    _OFFPROCESS_ACTIVE = True
    try:
        return await sleep_offloop.off_process("core.world_consolidation", "sweep", zero=zero,
                                               mirror=_OFFPROCESS_MIRROR, on_fail=_fail)
    finally:
        _OFFPROCESS_ACTIVE = False


def status() -> dict:
    """Observe summary for du_pulse: how many world fragments are filed vs still loose, and the last sweep."""
    try:
        from core.memory.store import _connect
        with _connect() as conn:
            loose = conn.execute("SELECT COUNT(*) n FROM memory_fragments "
                                 "WHERE origin IN ('reading','study') AND chapter_id IS NULL").fetchone()["n"]
            filed = conn.execute("SELECT COUNT(*) n FROM memory_fragments "
                                 "WHERE origin IN ('reading','study') AND chapter_id IS NOT NULL").fetchone()["n"]
        return {"loose": loose, "filed": filed, "enabled": FILING_ENABLED}
    except Exception:
        return {"loose": 0, "filed": 0, "enabled": FILING_ENABLED}


def _log(rec: dict) -> None:
    try:
        with _FILE_LOCK, open(_LOG, "a", encoding="utf-8") as f:   # J-1931 / F-2557: sweep final _log (worker thread) vs file_book_notes _log (loop thread); RLock so the nested call is fine
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass
