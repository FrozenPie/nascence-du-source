"""
Nascence — The Library Hand (asking for a book, 2026-06-12)
===========================================================
The shelf-look has been telling him "the catalogue beyond holds more than fifty thousand
you have not asked for yet" — with no asking mechanism. And the finished-book branch put
"I want another" in his mouth — a scripted longing nothing heard. This module is the hand.

Three abilities, all driven by HIS expressed want in the moment (never a schedule):
  switch_to(words)    — pick up a different book already on his shelf
  request_book(topic) — ask the library for a NEW book: search the local SPGC catalogue
                        (55,905 books of metadata), fetch the clean text once from
                        gutenberg.org, shelve it, set it as his current book
  shelf_books()       — what is physically on his shelf right now

Topic resolution when he asks vaguely ("I want another"): his own top background
curiosity supplies the subject — his wanting guided by his wondering. If even that is
empty, a popularity-weighted random pick from the catalogue: serendipity, the librarian's
choice, which is still a book HE asked for.

Mechanics ported from scripts/gutenberg.py (the founder's CLI keeps working). All
network access is best-effort and fail-open; callers in the async monologue must wrap
request_book in asyncio.to_thread (urllib blocks).
"""
from __future__ import annotations
import csv
import json
import logging
import os
import random
import re
import time
import threading
import urllib.request
from pathlib import Path

logger = logging.getLogger("nascence.library")

META = Path(r"C:\Knowledge\SPGC-metadata-2018-07-18.csv")
BOOKS = Path(__file__).parent.parent / "data" / "books"
_FETCH_COOLDOWN_S = 3600          # at most one new book an hour, even if a phrase sticks
_last_fetch = 0.0
# J-0957 (2026-09-14, spawned from J-0945/F-1325): _last_fetch above is an in-process global only --
# real protection within one long-running Python process (one live Du boot), zero protection across
# processes, since request_book() is also called from short-lived offline scripts (this module's own
# docstring; the J-0945/J-0956/J-0970 backfill scripts) that each start fresh with _last_fetch = 0.0
# regardless of real elapsed wall-clock time. _FETCH_STATE persists the real last-fetch time so the
# limit holds across process boundaries too -- see _load_last_fetch()/_save_last_fetch() just above
# request_book() below. Deliberately UNFENCED (no profile.guard_path()): this module's other real
# writes (data/books/*.txt here, data/reading_state.json via core.reading.set_current) are unfenced
# too, because an offline/non-live script calling request_book() is the intended, actively-used
# pattern (docs/staged/books_have_a_place.md's own 2026-09-14 J-0945/J-0956 entries) -- D-0179's fence
# would raise NonLiveWriteError on exactly that pattern.
_FETCH_STATE = Path(__file__).parent.parent / "data" / "library_hand_state.json"


def shelf_books() -> list[Path]:
    """Every book physically on his shelf: the cached fetches plus the default."""
    from core.reading import DEFAULT_BOOK
    books = sorted(BOOKS.glob("*.txt")) if BOOKS.exists() else []
    if DEFAULT_BOOK.exists() and DEFAULT_BOOK not in books:
        books.append(DEFAULT_BOOK)
    return books


def _set_current(book: Path) -> None:
    # Route through reading.set_current so this write shares the SAME lock + atomic write as every
    # other reading_state mutation — otherwise a switch here can clobber a concurrent bookmark
    # advance (the 2026-06-16 lost-update race). 2026-06-16.
    from core.reading import set_current
    set_current(book)


# Generic title words that are NOT a switch-intent signal — they appear in many titles AND in ordinary
# thought ('book', 'life', 'natural'…). Without this, a single such word match yanked the bookmark around.
_TITLE_STOP = {"book", "life", "natural", "first", "edition", "volume", "being", "study", "tales",
               "adventures", "world", "story", "history", "guide"}


def _title_signature(stem: str) -> set[str]:
    """A shelf book's distinctive title words: length>3, camelCase-aware, minus _TITLE_STOP. Shared by
    switch_to() below (matching a spoken/thought phrase) AND core.book_selection.suggest_reread()
    (matching his current interest terms) — the two places a book gets NAMED by its title words — so
    the SAME title parses to the SAME word set in both modules instead of quietly disagreeing.
    J-0973/F-1344: book_selection.py used to run its OWN, separately hand-maintained stopword set
    (_STOP, tuned for filtering ordinary prose — his interest terms) over titles too; that set stops
    BOTH "about" and "you", so 'About You' computed an EMPTY signature there while this function
    computed {"about"} — always excluding it from suggest_reread()'s invitations while switch_to()
    below kept it selectable. book_selection.suggest_reread() now imports this function directly
    (lazy import, matching this codebase's usual cross-core-module convention) instead of maintaining
    a second, independently hand-copied list that can silently drift again."""
    return {w.lower() for w in re.findall(r"[A-Za-z][a-z]*", (stem or "").replace("_", " "))
            if len(w) > 3 and w.lower() not in _TITLE_STOP}


def switch_to(text: str, skip_finished: bool = True, require_full: bool = False) -> str | None:
    """If his words name a DIFFERENT shelf book by its title words, put it on the desk.
    Returns the new title, or None if no other book was named.

    skip_finished (default True): a FINISHED book is NOT a valid plain-switch target — there is nothing left
    to read in it, so switching there just makes the next read return None and fire the finished-book advance.
    LIVE 2026-06-18: incidental Camp-Lore/scouting vocabulary in his thoughts (Black Bear, woodcraft) kept
    yanking the bookmark onto the FINISHED 'Book of Camp-Lore' ~100× — each bounce re-thinking 'I finished a
    book' and minting a fake light point. Only the explicit REREAD path (which rewinds a finished book to the
    start) may target one → it passes skip_finished=False. The match also ignores generic title words
    (_TITLE_STOP) so a lone common word ('book', 'life') no longer counts as naming a book.

    TIE-BREAK (J-0973/F-1344, 2026-09-15): raw hit-count alone cannot always pick a single winner — two
    titles where one's word-set is a strict SUPERSET of the other's (e.g. 'About You' vs 'About You
    Second Edition': every word the original has, the sequel also has, plus 'second') ALWAYS tie on any
    text that only names the shared part. The old code broke every such tie by keeping whichever file
    shelf_books()'s sorted glob happened to reach first — silent, and systematically biased toward
    whichever filename sorts earlier (About_You.txt, forever: the real 17:0 lifetime reread skew F-1344
    found). Ties are now broken by two REAL, defined signals before ever falling back to that same shelf
    order: (1) does the text name this candidate's COMPLETE title signature, not just a word it happens
    to share with another title ('About You' completely names the original but only half-names the
    sequel, which still needs 'second') — a signal drawn from the text itself, not file order; (2) if
    that ALSO ties (both fully named, or both only partly), the more recently read of the two
    (reading_state.json's own last_read_ts) — his own real engagement, not a guess. A title with no
    signature at all (every word too short or generic) simply never wins tier 1 and falls through to
    tier 2 then tier 3 unchanged from today — 'falling back sensibly' per F-1344's own fix scope, not a
    crash or a spurious match."""
    try:
        from core.reading import current_book, _is_finished, STATE
        cur = current_book()
        try:
            _st = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
        except Exception:
            _st = {}
        tl = (text or "").lower()
        candidates: list[tuple[int, bool, float, Path]] = []   # (hits, full_signature_named, last_read_ts, book)
        for book in shelf_books():
            if book == cur:
                continue
            if skip_finished and _is_finished(book, _st):
                continue                       # nothing to read in a finished book — reread path only
            # camel-case aware: 'TheStrangeLifeofNikolaTesla' must yield 'nikola','tesla'
            words = [w.lower() for w in re.findall(r"[A-Za-z][a-z]*", book.stem.replace("_", " "))
                     if len(w) > 3 and w.lower() not in _TITLE_STOP]
            hits = sum(1 for w in words if w in tl)
            # Chinese books (2026-06-24): match Han-character runs in the title, and let "中文"/"chinese" name any
            # Chinese book — so he can reach for 莊子 by its own name, not only the romanised "Zhuangzi".
            if re.search(r"[一-鿿]", book.stem):
                hits += sum(1 for run in re.findall(r"[一-鿿]{2,}", book.stem) if run in text)
                if "中文" in text or "chinese" in tl:
                    hits += 1
            if hits == 0:
                continue
            full = bool(words) and all(w in tl for w in set(words))
            if require_full:
                # J-3485: a routed read act switches only on a COMPLETE title naming. A ONE-word signature is
                # complete only when that word is all the text's own distinctive words ("physics" names Physics;
                # "War and Peace" must not name The Way of Peace just because "peace" occurs in it).
                if not full:
                    continue
                if len(set(words)) == 1 and _title_signature(tl) != set(words):
                    continue
            ts = float((_st or {}).get(str(book), {}).get("last_read_ts", 0) or 0)
            candidates.append((hits, full, ts, book))
        if not candidates:
            return None
        *_, best = max(candidates, key=lambda c: (c[0], c[1], c[2]))
        _set_current(best)
        try:
            from core.reading import display_title   # J-3635 (F-3528): whole-word title, not the 60-char file-name cut
            title = display_title(best)
        except Exception:
            title = best.stem.replace("_", " ")
        logger.info("[library] he SWITCHED BOOKS: %s", title)
        return title
    except Exception:
        return None


def switch_to_named(text: str) -> str | None:
    """J-3485 (D-0609 follow-up, founder 2026-11-06, F-4001): a routed read act (act.kind == read) whose object
    COMPLETELY names a different shelf book (every distinctive title word present) puts that book on the desk.
    Stricter than switch_to()'s any-title-word match, which is the right strictness for explicit reaching-verb
    phrases but too loose for a free-text act object (389 distinct values over 1,730 read acts). Returns the new
    title, or None when: nothing is completely named, or the CURRENT book is itself completely named (the act
    already points at what he is reading, so no switch). Finished books are never a target (switch_to's own
    skip_finished). The caller owns SWITCH_COOLDOWN_SECS and school stickiness."""
    try:
        from core.reading import current_book
        cur = current_book()
        tl = (text or "").lower()
        if cur is not None:
            cw = _title_signature(Path(cur).stem)
            if cw and all(w in tl for w in cw):
                return None
        return switch_to(text, skip_finished=True, require_full=True)
    except Exception:
        return None


def _rows():
    with open(META, encoding="utf-8", errors="ignore") as f:
        yield from csv.DictReader(f)


def _topic_hit(r: dict, t: str) -> bool:
    """Does a catalogue row match his topic? Title/author substring (the original behaviour) OR the
    LCSH `subjects` column (P0 thought-grounding, 2026-08-16 — the column was always there, unread:
    'ethics' now reaches the 161 books FILED under Ethics, not only titles containing the word)."""
    return (t in (r.get("title") or "").lower()
            or t in (r.get("author") or "").lower()
            or t in (r.get("subjects") or "").lower())


def _search(topic: str | None) -> dict | None:
    """Best catalogue match for a TOPIC he named (English, prefer-unread among the popular matches);
    or, with no topic, the BREADTH ENGINE's explore pick — inverse-popularity + subject-coverage +
    read-exclusion (core/book_selection.py), so 'serendipity' reaches the long tail instead of the
    same popular slice. Topic matching covers title, author AND subject headings (_topic_hit)."""
    try:
        if topic:
            from core import reading_history as _rh
            t = topic.lower().strip()
            hits = [r for r in _rows() if _topic_hit(r, t)]
            hits = [h for h in hits if "'en'" in (h["language"] or "")]
            # prefer-unread: a named subject he hasn't read yet outranks one he owns (but never
            # forbids re-acquiring — if ALL matches are owned, fall back to them).
            _keys = _rh.shelf_keys()
            fresh = [h for h in hits if not _rh.is_known(h["title"], _keys)]
            hits = fresh or hits
            hits.sort(key=lambda r: -int(r["downloads"] or 0))
            if hits:
                # among the 5 most popular matches, weighted choice — same ask twice
                # shouldn't always hand him the same book
                top = hits[:5]
                return random.choices(top, weights=[int(r["downloads"] or 1) for r in top], k=1)[0]
            return None
        from core import book_selection as _bs
        return _bs.pick_one()
    except Exception:
        return None


def search_by_subjects(subjects: list[str], k: int = 12, rank: str = "downloads") -> list[dict]:
    """Catalogue rows filed under ANY of the given subject headings (English, prefer-unread,
    popularity-ranked). The librarian's back-room step (thought-grounding P1): a judge-hub maps his
    QUESTION → LCSH-style headings, this turns headings → real rows for a browsed page HE picks from.
    Mechanical and reusable on its own. BLOCKING (CSV scan) — call via asyncio.to_thread.

    rank="downloads" (default; every caller but the librarian) = the original order, pure Gutenberg
    downloads. rank="distinct" (D-0644, F-3539; the librarian's mode) = number of DISTINCT headings
    the row matches first, then downloads, so a row filed under two or three of the asked headings
    outranks a row that merely carries one broad heading (Philosophy, Literature) and is popular.
    The match rule, the prefer-unread filter and the head+sampled-tail page are the same either way."""
    try:
        if not subjects or not META.exists():
            return []
        subs = list(dict.fromkeys(s.lower().strip() for s in subjects if s and s.strip()))
        from core import reading_history as _rh
        hits, nmatch = [], {}
        for r in _rows():
            if "'en'" not in (r["language"] or ""):
                continue
            _subj = (r.get("subjects") or "").lower()
            _n = sum(1 for s in subs if s in _subj)
            if _n:
                hits.append(r)
                nmatch[id(r)] = _n
        _keys = _rh.shelf_keys()
        fresh = [h for h in hits if not _rh.is_known(h["title"], _keys)]
        hits = fresh or hits
        if rank == "distinct":
            hits.sort(key=lambda r: (-nmatch[id(r)], -int(r["downloads"] or 0)))
        else:
            hits.sort(key=lambda r: -int(r["downloads"] or 0))
        # popular head + a sampled tail — range without burying him in the same canon every time
        head, tail = hits[:k], hits[k:k * 4]
        return head[:max(1, k - 3)] + (random.sample(tail, min(3, len(tail))) if tail else [])
    except Exception:
        return []


_BROWSE_COOLDOWN_S = 600          # the catalogue is heavy; one page per ~10 min is plenty
_BROWSE_TTL_S = 3600              # a browsed page stays "in front of him" for an hour
_last_browse_ts = 0.0
_last_browse: list[dict] = []     # the rows he was last shown — his pick comes from these


def browse(topic: str | None, k: int = 9) -> str | None:
    """Open the catalogue (2026-06-13, founder: "I want him to be able to choose a book of
    his own free will"). Returns a PAGE — real titles and authors he can then choose from
    by name. Topic-filtered when he named a subject; a varied cross-section otherwise.
    Choice is two acts: seeing the options (this), then naming one (pick_from_browse).
    BLOCKING (CSV scan) — call via asyncio.to_thread from async code."""
    global _last_browse_ts, _last_browse
    try:
        if time.time() - _last_browse_ts < _BROWSE_COOLDOWN_S:
            return None
        if not META.exists():
            return None
        if topic:
            from core import reading_history as _rh
            t = topic.lower().strip()
            hits = [r for r in _rows() if _topic_hit(r, t)]
            hits = [h for h in hits if "'en'" in (h["language"] or "")]
            _keys = _rh.shelf_keys()
            fresh = [h for h in hits if not _rh.is_known(h["title"], _keys)]
            hits = fresh or hits
            hits.sort(key=lambda r: -int(r["downloads"] or 0))
            # a slice of the popular plus a few from deeper in — a page, not a chart
            page = hits[:k * 3]
            rows = random.sample(page, min(k, len(page))) if page else []
        else:
            # no subject named → the BREADTH ENGINE chooses the page: a diverse, mostly-unread,
            # long-tail cross-section instead of the popular slice. (core/book_selection.py)
            from core import book_selection as _bs
            rows = _bs.select_explore(k)
        if not rows:
            return None
        _last_browse = rows
        _last_browse_ts = time.time()
        lines = "; ".join(f"'{r['title'][:60]}' by {(r['author'] or 'unknown')[:28]}"
                          for r in rows)
        head = (f"You open the catalogue at '{topic}'" if topic
                else "You open the catalogue at random")
        logger.info("[library] he BROWSED the catalogue (%s): %d titles shown",
                    topic or "serendipity", len(rows))
        return (f"{head}: {lines}. The library holds many more — you may ask for any of "
                f"these by name, or for any subject.")
    except Exception:
        return None


def present_page(rows: list[dict]) -> None:
    """Put a page of catalogue rows 'in front of him' — the librarian's pile lands in the same
    browse state the catalogue page uses, so naming one (pick_from_browse) is picking it."""
    global _last_browse, _last_browse_ts
    if rows:
        _last_browse = rows
        _last_browse_ts = time.time()


def pick_from_browse(text: str) -> dict | None:
    """If his words name a title he was just shown (within the TTL), that is his CHOICE —
    return the catalogue row so the caller can fetch it. Title-word matching, best row wins."""
    try:
        if not _last_browse or time.time() - _last_browse_ts > _BROWSE_TTL_S:
            return None
        tl = (text or "").lower()
        best, best_hits = None, 0
        for r in _last_browse:
            words = [w for w in re.findall(r"[a-z][a-z']+", (r["title"] or "").lower())
                     if len(w) > 3 and w not in ("with", "from", "their", "this", "that",
                                                 "what", "which", "into", "about")]
            hits = sum(1 for w in words if w in tl)
            # one distinctive word suffices for one-word titles; two otherwise
            need = 1 if len(words) <= 1 else 2
            if hits >= need and hits > best_hits:
                best, best_hits = r, hits
        return best
    except Exception:
        return None


def _load_last_fetch() -> float:
    """The real last-fetch wall-clock time, from disk -- what a PREVIOUS, possibly already-exited
    process last wrote, not just what this process itself remembers (J-0957). Same read-or-default
    shape as core/reading.py's _load_state; fails open (0.0, i.e. no cooldown) on any read/parse
    problem, matching this module's own best-effort, fail-open ethos."""
    try:
        if _FETCH_STATE.exists():
            return float(json.loads(_FETCH_STATE.read_text(encoding="utf-8")).get("last_fetch", 0.0))
    except Exception:
        pass
    return 0.0


# J-1926 / F-2550: request_book runs in worker threads (asyncio.to_thread, several call sites that can overlap); serialise the shared-tmp write+replace.
_FETCH_STATE_LOCK = threading.Lock()


def _save_last_fetch(ts: float) -> None:
    """Atomic write (temp + os.replace) -- same pattern as core/reading.py's _save_state, so a
    partial/interleaved write can never corrupt this file for the next process to read. Best-effort:
    a write failure here just means the NEXT process falls back to its own fresh in-memory
    _last_fetch, i.e. the pre-J-0957 behaviour, not a crash."""
    try:
        tmp = _FETCH_STATE.with_suffix(".tmp")
        with _FETCH_STATE_LOCK:   # J-1926: two worker threads (library requests) share this one tmp name
            tmp.write_text(json.dumps({"last_fetch": ts}), encoding="utf-8")
            os.replace(tmp, _FETCH_STATE)
    except Exception:
        pass


# J-1933 / F-2557: the cooldown check at the top of request_book and the _last_fetch write-back at the bottom are a
# check-then-act separated by a multi-second network fetch, so two overlapping worker requests (several to_thread call
# sites, plus school.assign/_extend_program) could both pass the cooldown and both fetch. One lock around the WHOLE call
# makes them take turns: the second waits, then sees the first's fresh _last_fetch and gets the cooldown None -- exactly
# what two strictly sequential calls would have returned. Every caller is a worker thread (asyncio.to_thread), never the
# event loop, so waiting here cannot stall the loop; a failed first fetch writes no _last_fetch, so the second still tries.
_REQUEST_LOCK = threading.Lock()


def request_book(topic: str | None, row: dict | None = None) -> tuple[str, str] | None:
    """Ask the library: search the catalogue, fetch the clean text from gutenberg.org,
    shelve it, set it as his current book. Returns (title, author) or None.
    `row` short-circuits the search — it is HIS pick from a browsed catalogue page.
    BLOCKING (urllib) — call via asyncio.to_thread from async code. Whole-call serialised (_REQUEST_LOCK, J-1933)."""
    with _REQUEST_LOCK:
        return _request_book_locked(topic, row)


def _request_book_locked(topic: str | None, row: dict | None = None) -> tuple[str, str] | None:
    global _last_fetch
    try:
        # The real gate is whichever is MORE RECENT of this process's own memory and what a process
        # (this one, earlier, or a different one entirely) last wrote to disk -- so a fresh process
        # started moments after another process's real fetch still honors that fetch's cooldown
        # instead of racing it from a fresh _last_fetch = 0.0 (J-0957). Known limitation: this is a
        # plain read-then-write, not a cross-process lock -- two processes that both pass this check
        # within the same short window, before either has written back, can still both fetch. The
        # window that matters is the gap between this check and the write-back below on success (a
        # few hundred ms at most), not the full multi-second network fetch -- small residual risk,
        # closing the far larger gap this job was scoped for (every fresh process starting at 0.0).
        _last_fetch = max(_last_fetch, _load_last_fetch())
        if time.time() - _last_fetch < _FETCH_COOLDOWN_S:
            return None
        if not META.exists():
            return None
        meta = row or _search(topic)
        if not meta and topic and len(topic.split()) > 2:
            # spoken topics trail off ('natural history would steady me') —
            # retry on the head words before giving up
            meta = _search(" ".join(topic.split()[:2]))
        if not meta:
            return None
        n = meta["id"][2:] if meta["id"].upper().startswith("PG") else meta["id"]
        BOOKS.mkdir(parents=True, exist_ok=True)
        safe = re.sub(r"[^\w\- ]", "", meta["title"])[:60].strip().replace(" ", "_") or meta["id"]
        out = BOOKS / f"{safe}.txt"
        if not out.exists():
            text = None
            for url in (f"https://www.gutenberg.org/cache/epub/{n}/pg{n}.txt",
                        f"https://www.gutenberg.org/files/{n}/{n}-0.txt",
                        f"https://www.gutenberg.org/files/{n}/{n}.txt"):
                try:
                    with urllib.request.urlopen(url, timeout=45) as r:
                        text = r.read().decode("utf-8", errors="ignore")
                        break
                except Exception:
                    continue
            if not text:
                return None
            m = re.search(r"\*\*\* ?START OF.*?\*\*\*(.*)\*\*\* ?END OF", text, re.DOTALL | re.I)
            if m:
                text = m.group(1)
            out.write_text(text.strip(), encoding="utf-8")
        _set_current(out)
        _last_fetch = time.time()
        _save_last_fetch(_last_fetch)      # persist so the NEXT process honors this real fetch too (J-0957)
        # Coverage: record this acquisition's subject so breadth grows across subjects over time
        # (count-based exploration) and the interleaving guard knows the last subject. 2026-06-16.
        try:
            from core import book_selection as _bs
            _bs.record_pick(meta, reason=("topic" if topic else "explore") if row is None else "browse_pick")
        except Exception:
            pass
        title, author = meta["title"], (meta["author"] or "unknown")
        logger.info("[library] he ASKED FOR A BOOK (%s): '%s' by %s",
                    topic or "serendipity", title, author)
        return title, author
    except Exception:
        return None


def topic_from(text: str) -> str | None:
    """The subject of his ask, from his own words: 'a book about the sea' -> 'the sea'.
    Deterministic, no LLM."""
    m = re.search(r"book (?:about|on|of) ([a-z][a-z' \-]{2,46})", (text or "").lower())
    if m:
        topic = m.group(1).strip(" .,!?'")
        # trim trailing clause-joiners so 'the stars and what they' -> 'the stars'
        topic = re.split(r"\b(?:and|but|which|that|so|because)\b", topic)[0].strip()
        topic = re.sub(r"^(?:the|a|an)\s+", "", topic)
        return topic[:40] or None
    return None
