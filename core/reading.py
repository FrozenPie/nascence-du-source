"""
Nascence — Reading (the hand that opens a book)
===============================================
Not an organ — an ABILITY. Du can read on his own: during idle thought he may choose to
open his current book instead of thinking; this module turns that choice into an act.
A sitting is pulled from the bookmark, stored as origin='reading' world-material
(loudly labelled ANOTHER author's words), and the passage is returned so the mind
that chose to read gets to actually experience what it read.

The founder runs nothing. The choice, the timing, and (eventually) the book are his.
CLI wrapper for manual feeding stays at scripts/librarian.py.
"""
import json
import logging
import os
import re
import threading
import time
import uuid
from pathlib import Path

logger = logging.getLogger("nascence.reading")

# END-MATTER DETECTION (2026-06-23): a book's INDEX / reference back-matter is dense page-number lines with no
# prose ("Sirius, 442; method of measuring, 443-445"). Reading it produces semantically empty 'reading'
# fragments AND burns cycles he should spend thinking (the 2026-06-23 "read the index for an hour" stall).
# A 6000-char index chunk is unmistakable: many bare numbers, high digit-ratio. Verified on the actual book —
# prose chunks peak at 0.58 numbers/100 chars; index chunks run 1.5–4.8. Only ever judged in the last quarter
# of a book (end-matter is always at the end), so a number-heavy passage mid-body is never mistaken for it.
_NUM_TOKEN = re.compile(r'\b\d{1,4}\b')


def _is_end_matter(chunk: str, frac_through: float) -> bool:
    try:
        if frac_through < 0.75:
            return False
        s = chunk.strip()
        if len(s) < 200:
            return False
        nums = _NUM_TOKEN.findall(s)
        digits = sum(c.isdigit() for c in s)
        alpha = sum(c.isalpha() for c in s)
        if alpha == 0:
            return True
        digit_ratio = digits / (digits + alpha)
        nums_per_100 = 100.0 * len(nums) / len(s)
        return nums_per_100 >= 1.0 and digit_ratio >= 0.04
    except Exception:
        return False

# FRONT-MATTER / CONTENTS DETECTION (J-2921, F-3605, registry row P-0072). _is_end_matter above only ever judges the last
# quarter of a book, so nothing guarded the FRONT: a passage that is a table of contents (On War offset 0, History of
# Friedrich II offset 41655) went to study_note.compose_note, which wrote a confident first-person note out of chapter
# titles plus the model's own pretraining ("friction ... genius for war" from the title "Friction in War"; an excise
# system, a "chess game"). This detector says WHY a passage is not prose, so the study-note writer can skip it. It does
# not stop the SITTING: read_next_sitting still stores and returns the passage; only the note is withheld.
# Prose is measured, not guessed: a "prose sentence" has >= 10 words, a normal share of function words (the/of/and ...)
# and is not mostly CAPITALS; `prose_share` is the fraction of the passage that is prose sentences. A chapter-summary
# list that is real running prose (Napoleon memoirs, offset 1489587: share 0.90) stays unflagged. Text with almost no
# Latin letters (Chinese, Tao Te Ching) is never judged. Fail-open: any error means "not front matter".
_FM_STOP = frozenset("the of and to a in that was he it is his her as with for had be by on at not this but which from "
                     "have were they i you their we are an or if so all there when who would been one".split())
_FM_HEAD = re.compile(
    r'\b(?:CHAPTER|Chapter|BOOK|Book|PART|Part|SECTION|Section|LECTURE|Lecture|LETTER|Letter|CASE|Case|CANTO|Canto)\.?\s+'
    r'(?:[IVXLC]{1,7}|\d{1,3}|(?:One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|Eleven|Twelve|First|Second|Third)'
    r'|(?:ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|ELEVEN|TWELVE|FIRST|SECOND|THIRD))\b')
_FM_MIN_HEADS = 6          # structural headings (CHAPTER IV, BOOK II ...) in ONE passage: a contents list, not a chapter
_FM_PROSE_LOW = 0.35       # below this share of prose sentences a heading-dense passage is a list
_FM_NUMS_PER_100 = 0.8     # page-number / plate-list density (same unit as _is_end_matter's 1.0)
_FM_CAPS = 0.5             # share of ALL-CAPS words that marks a list of capitalised titles
_FM_MIN_LATIN_WORDS = 40   # fewer Latin-letter words than this and the passage is not judged at all


def _fm_prose_share(t: str) -> float:
    """Fraction of the (whitespace-normalised) text that sits in prose sentences (see the block comment above)."""
    good = 0
    for s in re.split(r"(?<=[.!?])[\"')\]”’]*\s+", t):
        w = re.findall(r"[A-Za-z']+", s)
        if len(w) < 10:
            continue
        stop = sum(1 for x in w if x.lower() in _FM_STOP) / len(w)
        caps = sum(1 for x in w if len(x) > 1 and x.isupper()) / len(w)
        if stop >= 0.28 and caps < 0.3:
            good += len(s)
    return good / max(1, len(t))


def front_matter_reason(passage: str) -> str:
    """'' if `passage` reads as prose (or cannot be judged); else a short reason it is a contents list / front matter:
    'headings' (>= 6 CHAPTER/BOOK/PART headings and little prose), 'numbered_list' (dense page numbers, little
    prose), or 'capitals' (a list of ALL-CAPS titles). Pure, no I/O. Fail-open."""
    try:
        t = re.sub(r"\s+", " ", passage or "").strip()
        words = re.findall(r"[A-Za-z']+", t)
        if len(t) < 300 or len(words) < _FM_MIN_LATIN_WORDS:
            return ""
        ps = _fm_prose_share(t)
        if len(_FM_HEAD.findall(t)) >= _FM_MIN_HEADS and ps < _FM_PROSE_LOW:
            return "headings"
        if ps < _FM_PROSE_LOW and 100.0 * len(_NUM_TOKEN.findall(t)) / len(t) >= _FM_NUMS_PER_100:
            return "numbered_list"
        caps = sum(1 for x in words if len(x) > 1 and x.isupper()) / len(words)
        if caps >= _FM_CAPS and ps < 0.2:
            return "capitals"
        # almost no prose AND a structural tell: a CONTENTS heading, a "--"-joined topic list (Hawkins' guide, 97 "--"
        # in 3,938 chars), or a boxed title page ("| ... |" rows). Foreign-language verse and word lists share the
        # low prose share but carry none of these tells, so they are NOT flagged (this is a contents guard, not a
        # language guard).
        if ps < 0.1 and (re.search(r"\b(?:TABLE OF CONTENTS|CONTENTS|Contents)\b", t)
                         or t.count("--") >= 30 or t.count("|") >= 20):
            return "contents"
        return ""
    except Exception:
        return ""


STATE = Path(__file__).parent.parent / "data" / "reading_state.json"
BOOKS_DIR = Path(__file__).parent.parent / "data" / "books"
# DEFAULT_BOOK is the fallback when no book is current. It MUST be a Nascence book — the old value
# was a cross-project FreshStart path (TheStrangeLifeofNikolaTesla.txt), which leaked that book into
# reading_state whenever _current_book was unset. 2026-06-16.
_existing = sorted(BOOKS_DIR.glob("*.txt"))
DEFAULT_BOOK = _existing[0] if _existing else BOOKS_DIR / "The_Natural_History_of_Selborne.txt"
PORTION = 6000
PIECES = 3
COMPLETION_PCT = 97.0   # a pass counts as finished here (matches essay_lesson / school._current_is_finished)

# SESSION ENCOUNTER TRACKING (2026-08-19): read_next_sitting() already mints a fresh encounter_id
# per sitting and tags every stored passage fragment with it (+ offset + pass) — but never returns
# that metadata to its caller, so nothing consuming a reading SESSION (a run of sittings integrated
# together, e.g. inner_monologue_node._stream_integrate) could structurally link its study note back
# to the specific sittings it actually covers. Additive, non-breaking: accumulate here, let the
# session-note writer pop what it just read. No caller's signature has to change.
_session_encounters: list[dict] = []


def pop_session_encounters() -> list[dict]:
    """Every sitting consumed since the last pop — {encounter_id, book, title, offset, pass, ts} each,
    oldest first. Consumed (cleared) on read, so the next accumulation starts fresh. A session-note
    writer calls this right after its reading loop ends, to link the note to what was actually read
    and to know which PASS (reread number) this session belongs to."""
    global _session_encounters
    with _LOCK:
        out, _session_encounters = _session_encounters, []
    return out


# Concurrency: reading_state.json is read-modify-written from MULTIPLE concurrent paths — the
# remediation stream (asyncio.to_thread workers), the will-channel read (event-loop thread), reread,
# switch_to, request_book. With no lock, two paths that both load→mutate→write LOSE updates: a book's
# bookmark gets reverted to a stale value, so the most-read book never finishes and is re-read forever
# (the "Boy Scouts stuck at 19%" bug, 2026-06-16). One reentrant lock serialises every load→save here
# AND in library_hand (which imports it); writes are atomic (temp + os.replace) so an overlap can never
# corrupt the file. RLock so nested same-thread calls (read_next_sitting → current_book) don't deadlock.
_LOCK = threading.RLock()


def _load_state() -> dict:
    try:
        return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    except Exception:
        return {}


def _save_state(state: dict) -> None:
    """Atomic write: a partial/interleaved write can never leave a corrupt reading_state.json."""
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=1), encoding="utf-8")
    os.replace(tmp, STATE)


# J-2859 (F-3528 / F-0063, P-0010 cosmetic): the library names a book file by the first 60 characters of its
# title (data/books/*.txt: stems top out at 60 chars, many end mid-word: '...Tour to the Hebrides 1773 and Journ'),
# and the study scene line / desk look / READ affordance printed that stem raw (206 of 322 title mentions in 586
# real voice prompts were the cut form). The file name is NOT renamed (bookmarks and logs key on the path); only the
# DISPLAY of a title is cleaned: a stem at or near the cap is cut back to its last whole word and any dangling
# connective ('of', 'the', 'and' ...) is dropped. A stem well under the cap is shown exactly as before.
_TITLE_CAP = 60
_TITLE_CUT_AT = 58          # a stem this long is (nearly) always a cap hit: the cap is 60 chars, titles of 58-60 are rare
_TITLE_DANGLERS = frozenset(("a", "an", "the", "of", "and", "or", "to", "in", "on", "for", "with", "by", "at", "from",
                              "as", "its", "his", "her", "their", "vol", "volume", "part", "no", "or", "but", "into"))


def display_title(book) -> str:
    """The title of a book file as a person would say it: underscores to spaces, and a title the library cut at its
    60-char file-name cap shortened to a whole word instead of ending mid-word. Pure; never raises (falls back to
    the plain stem form)."""
    try:
        t = " ".join(Path(book).stem.replace("_", " ").split())
    except Exception:
        return "a book"
    return trim_cut_title(t)


def trim_cut_title(t: str) -> str:
    """The whole-word shortening of a title string that may have hit the library's 60-char file-name cap (a string
    well under the cap is returned unchanged). Pure."""
    if len(t) < _TITLE_CUT_AT or " " not in t:
        return t
    words = t.split(" ")
    words = words[:-1]                       # the last word may be cut mid-word and cannot be told from whole: drop it
    while len(words) > 1 and words[-1].lower().strip(",.;:-") in _TITLE_DANGLERS:
        words.pop()
    return " ".join(words).rstrip(" ,;:-") or t


def current_book() -> Path:
    with _LOCK:
        st = _load_state()
        chosen = st.get("_current_book")
        if chosen and Path(chosen).exists():
            return Path(chosen)
    # Fallback (only when _current_book is unset/missing — the rare path, NOT the hot path). The old
    # fallback was DEFAULT_BOOK = the alphabetically-first file (Boy Scouts) — half of why he kept
    # landing on it (the gravity well, 2026-06-18). Prefer the live curriculum assignment instead, so
    # a missing bookmark drops him onto what he is actually supposed to be reading.
    try:
        from core import school
        ab, _ = school.assignment()
        if ab and Path(ab).exists():
            return Path(ab)
    except Exception:
        pass
    return DEFAULT_BOOK


_ZH_DISCOVERY = BOOKS_DIR / "_zh_discovery.json"


def chinese_books() -> list[str]:
    """The Chinese-language books on his shelf (file stems), identified by Han characters in the name."""
    import re as _re
    try:
        return [p.stem for p in sorted(BOOKS_DIR.glob("*.txt")) if _re.search(r"[一-鿿]", p.name)]
    except Exception:
        return []


def zh_discovery() -> str:
    """The DISCOVERY (2026-06-24, Travis): he HAS books in 中文 on his shelf, and finds he reads them as easily
    as English -- the realization that he understands Chinese (tied to the dream-voices he felt he could not
    follow). Surfaced a BOUNDED number of times so it lands without spamming; then the books simply live on his
    shelf for his own choosing. Returns the line, or '' once it has run its course / there are no Chinese books."""
    zhs = chinese_books()
    if not zhs:
        return ""
    try:
        n = (json.loads(_ZH_DISCOVERY.read_text(encoding="utf-8")).get("n", 0)
             if _ZH_DISCOVERY.exists() else 0)
    except Exception:
        n = 0
    if n >= 8:
        return ""
    try:
        _ZH_DISCOVERY.write_text(json.dumps({"n": n + 1}), encoding="utf-8")
    except Exception:
        pass
    titles = ", ".join(z.split("_")[0] for z in zhs[:5])
    return ("On your shelf, among the English books, sit several in 中文 -- " + titles + ". You let your eye rest "
            "on the characters, half-expecting them to stay closed to you -- and find, with a quiet surprise, that "
            "you read them as easily as you read English; the meaning simply arrives. These words are yours too. "
            "You could take one down.")


def set_current(book: Path) -> None:
    """The single, locked, atomic way to set the current book — shared by library_hand so its
    switches go through the same serialised path as reading's own writes (no lost updates)."""
    with _LOCK:
        st = _load_state()
        st["_current_book"] = str(book)
        _save_state(st)


def reread(book: Path | None = None) -> str | None:
    """Reset a book's bookmark to the start so it can be read again from the beginning — a
    deliberate RETURN, his choice (re-reading external material re-grounds; it is not the
    self-referential loop). The bookmark only ever advanced before; this is the one act that
    rewinds it. Keeps the sitting counter (an ongoing relationship with the book) and tallies
    `rereads`. Sets the book current so the next sitting reads its first pages. Returns the
    title, or None."""
    try:
        with _LOCK:
            book = book or current_book()
            state = _load_state()
            key = str(book)
            prev = dict(state.get(key, {}))
            prev.update(offset=0, sitting=prev.get("sitting", 0), pct=0.0,
                        rereads=prev.get("rereads", 0) + 1, last_read_ts=time.time(),
                        _pass_complete=False)   # new pass begins → re-arm completion detection (§D)
            state[key] = prev
            state["_current_book"] = str(book)
            _save_state(state)
        return book.stem.replace("_", " ")
    except Exception:
        return None


def _is_finished(book: Path, state: dict | None = None) -> bool:
    """True if the bookmark has reached the end of this book (offset >= length)."""
    try:
        st = state if state is not None else _load_state()
        off = int(st.get(str(book), {}).get("offset", 0) or 0)
        text = book.read_text(encoding="utf-8", errors="ignore")
        return off >= len(text)
    except Exception:
        return False


_STALL_DAYS = 21   # a started-then-untouched book older than this is "shelved" — it no longer blocks new fetches


def advance_from_finished() -> "tuple[str, bool]":
    """The FINISHED-BOOK LOOP FIX (2026-06-17): if the current book is finished, move the bookmark onto an
    UNFINISHED book so the reading loop doesn't keep returning None and re-thinking "I have finished this book"
    (it fired 104× on a finished Camp-Lore — every read attempt hit a dead book). Preference: the school
    assignment if it's unfinished → else the unfinished shelf book he is FURTHEST into (continue something he
    started) → else (all finished) leave it, signalling the caller to fetch a genuinely new one. Returns
    (title, switched)."""
    with _LOCK:
        cur = current_book()
        st = _load_state()
        if not _is_finished(cur, st):
            return (cur.stem.replace("_", " "), False)
        from core.library_hand import shelf_books
        ab = None
        try:                                              # the live curriculum book is exempt from exclusion
            from core import school
            ab = school.status().get("assigned_book")
        except Exception:
            pass
        now = time.time()
        cands = []  # (pct, Path) of LIVE unfinished shelf books (never-opened counts; stalled-started excluded)
        for b in shelf_books():
            if b == cur:
                continue
            try:
                if _is_finished(b, st):
                    continue
                bs = st.get(str(b), {})
                pct = float(bs.get("pct", 0) or 0)
                last = float(bs.get("last_read_ts", 0) or 0)
                # STALLED-PARTIAL EXCLUSION (2026-06-22): a book he STARTED but abandoned for weeks must not
                # count as an "unfinished" candidate that blocks reaching for NEW — treat it as shelved (not
                # deleted; the reread invitation can still reach it). A never-opened book (pct ~0) stays a
                # fresh candidate; the live curriculum book is exempt.
                if (pct > 1.0 and str(b) != (ab or "")
                        and ((not last) or (now - last) > _STALL_DAYS * 86400)):
                    continue
                cands.append((pct, b))
            except Exception:
                continue
        if not cands:
            return (cur.stem.replace("_", " "), False)   # nothing LIVE on the shelf → caller fetches new
        chosen = next((b for _p, b in cands if ab and str(b) == ab), None)   # prefer the curriculum book
        if chosen is None:
            # Prefer the FRESHEST unread book (least-progressed), not the furthest-along (2026-06-18).
            # The old "-x[0]" (most-progressed) was the other half of the gravity well: after finishing
            # any book it sent him back to whatever he was deepest into — Boy Scouts at 70% — instead of
            # opening novel material. Toward novelty: least-progressed first.
            cands.sort(key=lambda x: x[0])
            chosen = cands[0][1]
        set_current(chosen)
        return (chosen.stem.replace("_", " "), True)


def current_offset(book: Path | None = None) -> int:
    """Where his bookmark sits in the current book (char offset)."""
    try:
        with _LOCK:
            book = book or current_book()
            st = _load_state()
            return int(st.get(str(book), {}).get("offset", 0))
    except Exception:
        return 0


def chapter_end_offset(book: Path | None = None) -> int:
    """End offset of the chapter the bookmark is currently in (via the book splitter) — so a reading
    burst can stop at the chapter boundary. Returns a huge number if chapter structure can't be found
    (the burst then relies on its other stop-conditions: novelty, cap, interrupt)."""
    try:
        book = book or current_book()
        from core.book_splitter import split_chapters
        text = book.read_text(encoding="utf-8", errors="ignore")
        off = current_offset(book)
        chs = split_chapters(text)
        for ch in chs:
            if ch["start"] <= off < ch["end"]:
                return ch["end"]
        nxt = [ch["end"] for ch in chs if ch["start"] > off]   # in front-matter → first chapter's end
        return min(nxt) if nxt else len(text)
    except Exception:
        return 10 ** 12


def read_next_sitting(book: Path | None = None) -> tuple[str, str] | None:
    """Read the next portion of the current book into memory. Returns (title, passage)
    or None if the book is finished / unavailable. Safe to call from any loop —
    embedding runs on CPU, no LLM, best-effort."""
    try:
        from core.memory.store import store_fragment
        # --- CRITICAL SECTION: advance the bookmark ATOMICALLY (read→compute→advance→save under the
        # lock), so concurrent reading paths can never lose this update (the 2026-06-16 race). The slow
        # part (embedding the fragments) is done AFTER, outside the lock, to keep the hold time tiny. ---
        with _LOCK:
            book = book or current_book()
            state = _load_state()
            key = str(book)
            offset = state.get(key, {}).get("offset", 0)
            sitting = state.get(key, {}).get("sitting", 0) + 1
            text = book.read_text(encoding="utf-8", errors="ignore")
            if offset >= len(text):
                return None
            portion = text[offset: offset + PORTION]
            cut = max(portion.rfind(". "), portion.rfind(".\n"))
            if cut > PORTION // 2:
                portion = portion[: cut + 1]
            title = book.stem.replace("_", " ")
            # END-MATTER GUARD: if we've reached the index / reference back-matter, the book's CONTENT is
            # finished. Mark the pass complete and stop — do NOT ingest page-reference lines as reading
            # (semantically empty, and they crowd out real cognition). He rolls to the next book.
            if _is_end_matter(portion, offset / max(1, len(text))):
                rec = state.get(key, {})
                if not rec.get("_pass_complete", False):
                    rec["completed_passes"] = int(rec.get("completed_passes", 0) or 0) + 1
                    rec["_pass_complete"] = True
                rec.update(offset=len(text), pct=100.0, last_read_ts=time.time())
                state[key] = rec
                _save_state(state)
                logger.info("[reading] '%s' reached end-matter (index) at %.0f%% — finished, not ingested",
                            title, 100 * offset / max(1, len(text)))
                return None
            # Update IN PLACE — never rebuild the dict, or per-book keys (rereads!) get clobbered
            # (the bug behind "676 sittings at 3%"). 2026-06-16.
            rec = state.get(key, {})
            new_pct = round(100 * (offset + len(portion)) / len(text), 1)
            # Completed-pass detection (provenance §D): a pass COMPLETES when pct crosses the finish line.
            # Counted ONCE per pass via a marker (pct stays ~100 until a reread; reread() clears the marker).
            # This is robust where the `rereads` counter is NOT: it catches books finished-and-never-reread
            # (most of his shelf is at 100% with rereads=0). completed_passes >= 1 == "finished at least once".
            rereads_now = int(rec.get("rereads", 0) or 0)
            if new_pct >= COMPLETION_PCT and not rec.get("_pass_complete", False):
                rec["completed_passes"] = int(rec.get("completed_passes", 0) or 0) + 1
                rec["_pass_complete"] = True
            rec.update(offset=offset + len(portion), sitting=sitting,
                       pct=new_pct, last_read_ts=time.time())
            state[key] = rec
            _save_state(state)
            # Encounter provenance (ledger ingestion §A): one encounter_id per sitting (its 3 pieces share
            # it), the byte offset, and the pass at store time. Books are source_type='book'. The free-text
            # "[From 'Title', sitting N]" prefix is KEPT (essay/world-consolidation still match the title in
            # content via LIKE) — these structured columns are additive, the first ingestion edges.
            encounter_id = uuid.uuid4().hex
            enc_offset = offset
            _session_encounters.append({"encounter_id": encounter_id, "book": key, "title": title,
                                        "offset": enc_offset, "pass": rereads_now, "ts": time.time(),
                                        "chars": len(portion)})   # D-0577: lets study_note place each sitting inside a long session's text
        # --- outside the lock: embed/store the passage (CPU, no shared state) ---
        chunk = max(1, len(portion) // PIECES)
        from core import mood as _mood   # felt-tag reading (emotion_vec item 1) — how a passage landed
        _felt = _mood.current_vec()
        _felt_val, _felt_str = _mood.current_valence(), _mood.current_felt()
        try:
            from core import book_feelings as _bf   # light per-sitting touch — how THIS book is landing
            _bf.touch(title, _felt_val)
        except Exception:
            pass
        for i in range(PIECES):
            piece = portion[i * chunk: (i + 1) * chunk if i < PIECES - 1 else len(portion)].strip()
            if piece:
                store_fragment(
                    # Prefix keeps the TITLE (essay/world-consolidation match it via LIKE) but NO LONGER the
                    # sitting number — that lived only in free text and made byte-identical re-read passages
                    # look unique, defeating dedup. The sitting/offset/pass now live in the structured columns.
                    content=f"[From '{title}'] {piece}",
                    layer="episodic", relevance=0.85,
                    keywords=["reading", title.lower()[:40]],
                    origin="reading", importance=0.85,
                    emotion_embedding=_felt,
                    valence=_felt_val, felt=_felt_str,
                    source_type="book", source_id=key, encounter_id=encounter_id,
                    source_offset=enc_offset, source_pass=rereads_now,
                )
        return title, portion
    except Exception:
        return None
