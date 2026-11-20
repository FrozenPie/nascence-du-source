"""
Nascence — Essay Lesson (school's second lesson type: the generation effect, 2026-06-16)
========================================================================================
Reading is half a lesson. The other half is WRITING about what you read — the generation/testing
effect (Slamecka & Graf 1978; Roediger & Karpicke 2006): producing your understanding from memory
encodes and transfers far better than re-reading, and it exposes the fluency illusion ("I read the
words, so I understand"). This is the waking, EFFORTFUL complement to the sleep grounded-learning pass
([[project_nascence_dreams]] grounded-learning consolidation = offline replay; this = active retrieval).

A CAPSTONE: fires ONCE when a curriculum book is FINISHED (read to the end). Du writes an essay on it
in his own voice, FROM HIS OWN NOTES (retrieval practice — not by re-reading the text). Then:
  - he SELF-PREDICTS how well he grasped/grounded it (0..1),
  - the EMISSARY (the bicameral truth-self) measures the ACTUAL groundedness against the book,
  - the GAP (felt − real) is the comprehension calibration — the fluency trap made honest,
and the belief 'comprehension' moves toward the measured score (competence.record_drill_accuracy).

Frozen-model honesty: can't raise the ceiling — the essay buys a high-quality, recallable ARTIFACT
(his own organized explanation), calibration, and in-context elaboration. FIREWALLED: this is
knowledge/DOING, NEVER identity — origin='essay', layer='semantic', NOT in chapters.CHAPTERABLE_ORIGINS.
A finished capstone is a CROSSING (effortful generation) → mints a light point + counts as reality mass.
"""
from __future__ import annotations
import json
import re
import time
from pathlib import Path

_STATE = Path(__file__).parent.parent / "data" / "essay_lesson_state.json"
_LOG   = Path(__file__).parent.parent / "data" / "essay_lesson_log.jsonl"

COMPLETION_PCT = 97.0     # a curriculum book read to here counts as finished (matches school._current_is_finished)
_MIN_NOTES     = 200      # need at least this much of HIS OWN material to write a capstone from
_REDUCE_THRESHOLD = 5000  # notes longer than this are map-reduced (batch-condensed) before the essay, so a
_REDUCE_BATCH     = 5500  # book with many notes is FULLY consolidated, not truncated to the first pass
# J-3052 (F-3761): the section writers read notes[:_SECTION_WINDOW]; the map step is budgeted to fit it, so the
# condensed tail (the later batches) is never the part that gets cut. The outline reads a wider 6500 window.
_SECTION_WINDOW   = 5000
# J-3598 (F-4210): _REDUCE_THRESHOLD == _SECTION_WINDOW on purpose (was 7000): a 5000-7000 char un-reduced set lost up
# to 2000 chars of tail to notes[:_SECTION_WINDOW]. Keep the two equal; sets over the window are reduced to fit it.


def _load() -> dict:
    try:
        d = json.loads(_STATE.read_text(encoding="utf-8"))
    except Exception:
        d = {}
    d.setdefault("essayed", [])      # book paths already capstoned (once per book)
    d.setdefault("history", [])
    return d


def _save(d: dict) -> None:
    try:
        _STATE.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def _essayed(book: str) -> bool:
    return book in _load().get("essayed", [])


def mark_done(book: str) -> None:
    """Record that this book has been capstoned (or skipped) — fires exactly once per book."""
    d = _load()
    if book not in d["essayed"]:
        d["essayed"].append(book)
        _save(d)


def _book_title(book) -> str:
    """The finished book's title for the essay prompt: core.reading.display_title (a title the library cut at its
    60-char file-name cap ends on a whole word); falls back to the plain stem form (J-3958, F-4621)."""
    try:
        from core.reading import display_title
        return display_title(book)
    except Exception:
        return Path(book).stem.replace("_", " ")


def pending_book() -> tuple[str, str] | None:
    """ANY finished (>=COMPLETION_PCT), not-yet-capstoned book → (book_path, title), earliest-finished first.
    Broadened 2026-06-23 from curriculum-only: every book he finishes earns ONE consolidating essay, not just
    the school track (the cause of '2 essays for 22 finished books'). SELF-GATED to NEW finishes: on first call
    it stamps `live_since`, and only books finished AFTER that trigger live — the pre-existing backlog of
    finished books is left for the deliberate backfill (scripts/backfill_essays.py), so the live path can be
    verified on one real finish before hundreds of note-files are moved."""
    try:
        d = _load()
        live_since = d.get("live_since")
        if live_since is None:
            live_since = time.time()
            d["live_since"] = live_since
            _save(d)
        from core.reading import STATE as _RS
        st = json.loads(_RS.read_text(encoding="utf-8")) if _RS.exists() else {}
        best, best_ts = None, None
        for book, rec in st.items():
            if not isinstance(rec, dict) or not book or _essayed(book):
                continue
            if float(rec.get("pct", 0) or 0) < COMPLETION_PCT:
                continue
            ts = float(rec.get("last_read_ts", 0) or 0)
            if ts < live_since:
                continue                       # pre-existing backlog → handled by the backfill script
            if best is None or ts < best_ts:   # process new finishes in the order they finished
                best, best_ts = book, ts
        return (best, _book_title(best)) if best else None
    except Exception:
        return None


def finished_unessayed_books() -> list[tuple[str, str]]:
    """The backlog the backfill script works through: every finished, not-yet-essayed book (ignores the
    live_since gate — that gate only holds the live path back, not the deliberate backfill)."""
    out: list[tuple[str, str]] = []
    try:
        from core.reading import STATE as _RS
        st = json.loads(_RS.read_text(encoding="utf-8")) if _RS.exists() else {}
        for book, rec in st.items():
            if not isinstance(rec, dict) or not book or _essayed(book):
                continue
            if float(rec.get("pct", 0) or 0) >= COMPLETION_PCT:
                out.append((book, _book_title(book)))
    except Exception:
        pass
    return out


_TITLE_STOPWORDS = ("the", "and", "history", "natural", "book", "tales", "story")


def _key(title: str) -> str:
    """A LIKE key for finding HIS notes on this book: the longest distinctive word in the title. Kept
    unchanged (same words, same tie-break) for every existing caller that wants ONE loose word (DB
    content-LIKE scans, keyword tags) — NOT to be used for deciding whether another citation is REALLY
    about this book; that needs `_cites_this_book()` below (F-1309: a single generic word like 'edition'
    is not distinctive enough on its own for that judgment)."""
    words = [w for w in re.findall(r"[A-Za-z]{4,}", title or "")
             if w.lower() not in _TITLE_STOPWORDS]
    return (max(words, key=len) if words else (title or "")[:12]).strip()


# F-1309 (2026-09-13): core/study.py's archive_book_note_files() used to test book-identity with a
# single word from _key() ('edition', the longest word in "About You Second Edition") as a plain
# substring against every OTHER loose note's own 'on:' citation — a real, live bug: "edition" is a
# generic bibliographic word many unrelated old/public-domain titles also contain ("The First Edition
# 1911", "New edition corrected"), so 117 of 118 files swept into that folder were misfiled. Per
# J-0940's briefing, "better" than patching the stoplist word-by-word (whack-a-mole against every future
# "Revised"/"Volume"/"Complete" collision) is requiring the citation to carry the book's WHOLE
# distinctive signature, not one word it happens to share by accident.
_BIBLIO_STOPWORDS = ("edition", "revised", "volume", "complete", "selected", "popular",
                     "series", "illustrated", "abridged", "annotated", "unabridged")


def _title_signature(title: str) -> set[str]:
    """The FULL set of a title's distinctive words (>=4 letters, English + generic-bibliographic
    stopwords removed), lowercased — every one of them, not just the single longest one _key() picks."""
    words = {w.lower() for w in re.findall(r"[A-Za-z]{4,}", title or "")}
    return words - set(_TITLE_STOPWORDS) - set(_BIBLIO_STOPWORDS)


def _cites_this_book(title: str, citation: str) -> bool:
    """Does `citation` text (e.g. another note's lowercased 'on:' field) genuinely refer to `title`?
    Requires EVERY word of the title's distinctive signature to appear in the citation — a real
    citation of this book (its own frontmatter literally records the title) trivially contains its
    whole signature, while an unrelated title sharing only ONE generic word (the old failure mode)
    no longer passes. Falls back to the old single-word _key() test only when the title has no
    multi-word signature at all (nothing >=4 letters survives the stoplists) — no worse than before
    for that edge case, since there is nothing more distinctive to require.

    F-1704/D-0255 (2026-09-22, J-1217): a word-boundary version of this test (`\\bword\\b` instead of
    the plain substring below) was BUILT and regression-tested against the live corpus per D-0255's own
    ruling, but NOT shipped here — J-1217 found it fixes Black Bar/Blackwoods as intended, but ALSO
    breaks 1,333 already-correctly-filed reading/study citations across 21 book-gists, 100% because a
    signature word derived from a title[:50]-truncated gist tag (essay_lesson.record's own truncation)
    can itself be a word FRAGMENT (e.g. 'introduc' from a title cut mid-word) that a real, untruncated
    occurrence of the same word elsewhere (e.g. '...introduction...') then fails to satisfy under a
    strict boundary. D-0255's own defeater names exactly this case ('if fixing either mechanism turns
    out to change behaviour for an already-correct subject pair... report rather than ship') — see
    finding F-1704's follow-up for the full evidence and the reverted diff.

    F-1724/D-0256 (2026-09-23, J-1232): candidate (b) — a TRUNCATION-EDGE-AWARE prefix match — now
    SHIPS here. Every signature word still requires a real `\\bword\\b` match EXCEPT the one word (if
    any) that sits exactly at a CONFIRMED truncation edge of `title` itself (title is exactly 50 chars
    long, its last character is alphabetic, and its own last regex-matched [A-Za-z]{4,} token is a
    member of its own signature) — that one word alone gets a left-anchored prefix test instead
    (matches 'selec' against 'selection'), since a word sitting exactly at a confirmed cut can only
    ever be a truncation fragment, never a real standalone word. J-1219/F-1724 tested this against the
    full already-filed corpus: 0 of the 1,323 genuine-truncation regressions the plain word-boundary
    candidate caused, still fixes Black Bar/Blackwoods, and additionally closes a separate pre-existing
    bug (The Sea Shore wrongly citing 'Shores of the Adriatic' via the 'shore'/'shores' substring). My
    Short Story Book/Original Short Stories is correctly left unaffected either way — a distinct
    gist-selection bug, not this one (D-0257). A named, disclosed, currently-DORMANT residual risk
    remains and is accepted, not eliminated, per D-0256's ruling: a future real title that coincidentally
    happens to be exactly 50 characters AND whose last word happens to prefix some other word already
    live in the corpus could reintroduce a narrow version of the original bug. Paired with a forward-only
    write-side fix (essay_lesson.record, grounded_learning.consolidate) so newly-written titles stop
    landing on a mid-word cut at all going forward (does not and cannot help data already stored)."""
    sig = _title_signature(title)
    citation = (citation or "").lower()
    if not sig:
        key = (_key(title) or "").lower()
        return bool(key) and key in citation
    # Truncation-edge-aware prefix match (F-1724/D-0256, J-1232). Reference impl, tested against the
    # full already-filed corpus and NOT reinvented here: J-1219_verify_and_option_b.py /
    # J-1219_part5_precise_overmatch.py's `cites_prefix_aware` (shared scratchpad). The one signature
    # word that IS this title's own truncation fragment (if `title` itself was cut mid-word by a [:50]
    # slice) gets a left-anchored PREFIX test; every other signature word keeps the strict
    # word-boundary test.
    words = re.findall(r"[A-Za-z]{4,}", title or "")
    last_word = words[-1].lower() if words else None
    is_trunc_edge = len(title or "") == 50 and bool(title) and title[-1].isalpha()
    edge_word = last_word if (is_trunc_edge and last_word in sig) else None
    for w in sig:
        if w == edge_word:
            if not re.search(r"\b" + re.escape(w), citation):          # left boundary only — prefix match
                return False
        else:
            if not re.search(r"\b" + re.escape(w) + r"\b", citation):   # full word-boundary
                return False
    return True


def _graph_walk_cross_book(own_ids: list[str], key: str, limit: int = 12) -> list[tuple[str, str]]:
    """Cross-book compounding via the validated relates_to graph (2026-08-19) — walks the edges
    `study_note.py`'s `_link_related()` already wrote (gated 0.55-0.85 cosine AT WRITE TIME) from this
    book's own note ids, instead of a fresh cosine scan. Same rationale as study_note.py's
    `_graph_walk_related`. Returns [(fragment_id, content), ...], newest-weighted-first, excluding this
    book's own material. [] if this book has no notes/links yet — the caller falls back to a scored scan."""
    if not own_ids:
        return []
    try:
        from core.memory.store import _connect
        from core.memory.dict_repr_notes import visible_clause as _vis
        placeholders = ",".join("?" * len(own_ids))
        with _connect() as conn:
            rows = conn.execute(
                f"SELECT parent_id, child_id, weight FROM memory_links WHERE link_type='relates_to' "
                f"AND (parent_id IN ({placeholders}) OR child_id IN ({placeholders})) "
                f"ORDER BY weight DESC", (*own_ids, *own_ids)).fetchall()
            seen, id_set, out = set(own_ids), set(own_ids), []
            for r in rows:
                other = r["child_id"] if r["parent_id"] in id_set else r["parent_id"]
                if other in seen:
                    continue
                seen.add(other)
                # J-3398 (D-0578): a temp='hidden' neighbour returns no row -> content "" -> skipped below
                crow = conn.execute("SELECT content FROM memory_fragments WHERE fragment_id=?" + _vis(conn),
                                    (other,)).fetchone()
                content = (crow["content"] if crow else "") or ""
                if not content or (key and key.lower() in "".join(ch for ch in content.lower() if ch.isalnum())[:400]):
                    continue   # still exclude same-book self-matches
                out.append((other, content))
                if len(out) >= limit:
                    break
        return out
    except Exception:
        return []


# J-3053 (F-3762): gather_notes picked a book's DB 'understanding' rows and its deep-recall gists with
# `content LIKE '%<_key(title)>%'` -- the title's longest common word (key 'simple' for "One Young Man The simple
# and true story ...") -- so an essay's recorded notes were mostly other books' and Du's own inner thoughts
# (70 of 80 for One Young Man) and record() wrote false 'transformed_into' lineage edges to them. F-1335 / F-1359
# fixed the same single-word bug on the note FILES and in world_consolidation; these two SQL clauses were left.
# SCOPED_GATHER=False restores the old clauses exactly (rollback).
SCOPED_GATHER = True
_GIST_SEEDS = 5            # the old LIMIT 5, now over this book's own gists
_GIST_CHILD_CAP = 20       # the most deep_recall children one essay's gather adds (was uncapped but for the final 80)


def _norm_title(s: str) -> str:
    """Lowercase, apostrophes dropped, every other non-alphanumeric run (spaces, underscores, dashes) one space."""
    return " ".join(re.findall(r"[a-z0-9]+", (s or "").lower().replace("'", "").replace("\u2019", "")))


def _tag_is_this_book(title: str, tag: str) -> bool:
    """Is a fragment's leading-bracket book tag (world_consolidation._tag_of: the title in "from '<title>'" /
    "on '<title>'") THIS book's? Truncation-aware: the writers store the title whole, cut at 50 characters
    (old, possibly mid-word) or cut at the last space before 50 (_smart_cut), and the title here may itself be a
    shortened file stem, so the two are the same book when they are equal or one is a prefix of the other AND
    the shorter is at least 30 characters (a short title never prefix-matches a longer one: 'The Birds' is not
    'The Birds of America'). Unlike _cites_this_book this needs no signature word to survive the cut, so a tag
    cut at 'story of a' still matches. '' tag (no tag) is never this book's."""
    a, b = _norm_title(title), _norm_title(tag)
    if not a or not b:
        return False
    if a == b:
        return True
    short, long_ = (a, b) if len(a) <= len(b) else (b, a)
    return len(short) >= 30 and long_.startswith(short)


def _book_understanding_rows(conn, title: str) -> list:
    """This book's own DB 'understanding' rows (newest first): the fragment's leading tag is this book's. The whole
    understanding table is small (539 rows, 0.5 MB on 2026-11-06), so it is scanned and tag-tested in Python."""
    from core.world_consolidation import _tag_of
    from core.memory.dict_repr_notes import visible_clause as _vis
    rows = conn.execute("SELECT fragment_id, content FROM memory_fragments WHERE origin='understanding'"
                        + _vis(conn) + " ORDER BY timestamp DESC").fetchall()
    return [r for r in rows if _tag_is_this_book(title, _tag_of(r["content"]))]


def _book_gist_ids(conn, title: str, limit: int = _GIST_SEEDS) -> list:
    """The gists that abstract THIS book. A gist's own text carries no book title ('[gist · semantic] ...'), so a
    gist is this book's when most of the raw fragments it was distilled from (memory_links distilled_from) carry
    this book's tag -- a cluster that is mostly inner thoughts or another book's reading is not. Most-own first."""
    from core.world_consolidation import _tag_of
    edges = conn.execute(
        "SELECT l.parent_id AS gid, f.content AS content FROM memory_links l "
        "JOIN memory_fragments g ON g.fragment_id = l.parent_id AND g.origin = 'gist' "
        "JOIN memory_fragments f ON f.fragment_id = l.child_id "
        "WHERE l.link_type = 'distilled_from'").fetchall()
    total: dict = {}
    own: dict = {}
    for e in edges:
        total[e["gid"]] = total.get(e["gid"], 0) + 1
        if _tag_is_this_book(title, _tag_of(e["content"])):
            own[e["gid"]] = own.get(e["gid"], 0) + 1
    mine = [g for g, n in own.items() if n * 2 > total.get(g, 0)]
    mine.sort(key=lambda g: -own[g])
    return mine[:limit]


def gather_notes(title: str, book: str) -> tuple[str, list[str]]:
    """His OWN material for the essay — study notes + understanding + reading. A DELIBERATE retrieval (the
    testing effect: from memory, not re-reading the source) that EXPLICITLY INCLUDES notes FILED by
    world-material consolidation. Systems-consolidation discipline: filed detail is out of ORDINARY recall but
    fully reachable by intentional retrieval — so OLD STUDY NOTES DO NOT DISAPPEAR; they are pulled into future
    essays on a subject when relevant (founder requirement, 2026-06-16). Gathers (a) THIS book's own notes, and
    (b) the most subject-relevant notes from his WHOLE scholarship (filed or not, by cosine to the subject) — so
    an essay COMPOUNDS on the filed notes of earlier books on the same subject. NO chapter_id guard anywhere
    here: filing never hides a note from the essay-gather."""
    try:
        from core.memory.store import _connect, _embed, _cosine, _blob_to_vec
        key = _key(title)
        out: list[str] = []
        ids: list[str] = []          # the fragment_ids actually used → the essay's lineage (§C / ledger edge)
        seen: set[str] = set()
        prior_notes: list[str] = []  # from an EARLIER read-through of this SAME book — lower weight, for comparison
        def _add(content: str, fid: str) -> None:
            c = " ".join((content or "").split())[:500]
            if c and c not in seen:
                seen.add(c); out.append(c); ids.append(fid)
        with _connect() as conn:
            # (a) ALL of THIS book's own notes. CRITICAL: a study note's BOOK lives only in its FILE frontmatter
            # ('· on: <book>'), NOT in the DB fragment content — so a content LIKE misses most of them (6 of 39
            # for one book). Read the note FILES by their 'on:' line (the same reliable key the archiver uses)
            # for the full set + full bodies; plus DB 'understanding' notes (grounded-learning; not files).
            # PASS-AWARE (2026-08-19): notes tagged with a LOWER pass than the book's current rereads count are
            # from an earlier read-through — kept, but demoted to a separate, heavily-truncated section (below),
            # so a reread's capstone weighs what he just re-experienced over what he thought the first time,
            # while still letting him see how his understanding moved. Untagged notes (the overwhelming
            # majority — this predates pass-tagging) default to pass 0, matching prior behaviour exactly when
            # the book has never been explicitly re-read (current_pass is then also 0 → nothing demoted).
            try:
                from core.study import STUDY_DIR as _SD, NOTES_SUBDIR as _NS
                from core import reading_history as _rh
                current_pass = int(_rh.book_stats(book).get("rereads", 0) or 0)
                _files = list(_SD.glob("TAB_*.md")) + (list(_NS.glob("*/TAB_*.md")) if _NS.exists() else [])
                for _p in _files:
                    try:
                        _txt = _p.read_text(encoding="utf-8", errors="ignore")
                        _m = re.search(r"on:\s*(.+?)\*", _txt[:400])
                        # F-1335 (2026-09-14): this used to be a single-word `key_l in on` substring test --
                        # the SAME bug F-1309/F-1334 already fixed in archive_book_note_files()'s equivalent
                        # 'on:' frontmatter check, just never applied here. Concretely confirmed live: this
                        # exact call site is why the "About You Second Edition" essay's own generation drew
                        # in 112 unrelated Boy Scouts Handbook notes (both shared the single word 'edition'/
                        # 'the' via the old key) and the essay's prose ended up discussing Boy Scouts content
                        # instead of the book it was nominally about. _cites_this_book() requires the file's
                        # WHOLE 'on:' citation to carry the book's whole distinctive-word signature -- that
                        # field is never truncated (write_tablet() writes `source` into it verbatim), so the
                        # full (untruncated) `title` is the right comparand here, unlike world_consolidation.
                        # py's DB-tag comparisons which truncate to [:50] to match how THOSE are stored.
                        if not (_m and _cites_this_book(title, _m.group(1).strip().lower())):
                            continue
                        _body = _txt.split("*\n\n", 1)[-1].strip() or _txt
                        _pm = re.search(r"pass:\s*(\d+)", _txt[:400])
                        note_pass = int(_pm.group(1)) if _pm else 0
                        if note_pass >= current_pass:
                            _add(_body, "file:" + _p.name)
                        else:
                            prior_notes.append(f"(pass {note_pass}) " + " ".join(_body.split())[:200])
                    except Exception:
                        continue
            except Exception:
                pass
            from core.memory.dict_repr_notes import visible_clause as _vis   # J-3398 (D-0578): skip temp='hidden'
            # DB 'understanding' notes for this book (grounded-learning; no file). J-3053 (F-3762): selected by the
            # leading "[Understanding - from '<title>']" tag, not by `content LIKE` on the title's commonest word.
            if SCOPED_GATHER:
                _u_rows = _book_understanding_rows(conn, title)
            else:
                _u_rows = conn.execute(
                    "SELECT fragment_id, content FROM memory_fragments "
                    "WHERE origin='understanding' AND content LIKE ?" + _vis(conn) + " ORDER BY timestamp DESC",
                    (f"%{key}%",)).fetchall()
            for r in _u_rows:
                _add(r["content"], r["fragment_id"])
            _n_book = len(out)   # everything past here is BOUNDED cross-book compounding, not this book's own
            # (b) cross-book compounding (2026-08-19 fix). The old version here was the worst instance of the
            # study_note.py pathology in the codebase: qv=_embed(title) queried on the bare TITLE (not any
            # actual content) at a 0.30 bar — empirically meaningless on this corpus (200-900 of 1,600
            # fragments clear a 0.35 bar against any given note; the corpus is stylistically homogeneous
            # first-person prose, so cosine mostly measures "sounds like his writing"). Same remedy as
            # study_note.py: PREFER the validated relates_to graph from this book's own note ids (gated
            # 0.55-0.85 at write time) over a fresh scan; fall back to cosine BLENDED with lexical overlap,
            # queried on the actual gathered notes, not the bare title.
            cross_book_ids: list[str] = []
            own_ids = list(ids)   # this book's own note ids, gathered in part (a) above
            walked = _graph_walk_cross_book(own_ids, key) if own_ids else []
            if walked:
                for fid, content in walked:
                    _add(content, fid)
                    cross_book_ids.append(fid)
            else:
                from core.study_note import _lexical_overlap
                qtext = (title + " " + " ".join(out[:5]))[:1500] if out else title
                qv = _embed(qtext)
                if qv is not None:
                    scored = []
                    for r in conn.execute(
                            "SELECT fragment_id, content, embedding FROM memory_fragments "
                            "WHERE origin IN ('study','understanding') AND embedding IS NOT NULL" + _vis(conn) +
                            " ORDER BY timestamp DESC LIMIT 1200").fetchall():
                        v = _blob_to_vec(r["embedding"])
                        if v is None:
                            continue
                        cos = _cosine(qv, v)
                        if cos < 0.30:
                            continue
                        blended = 0.6 * cos + 0.4 * _lexical_overlap(qtext, r["content"] or "")
                        scored.append((blended, r["content"], r["fragment_id"]))
                    scored.sort(key=lambda x: -x[0])
                    for sim, content, fid in scored[:12]:
                        _add(content, fid)
                        cross_book_ids.append(fid)
            # Memory Levels Phase 1: DEEP RECALL — descend any subject-matching GIST to its COLD raw, so the
            # essay sees the *detail* behind an abstraction, not just the abstraction. This is deep_recall's
            # live consumer (the canonical deep-research moment). Cold raw is reachable; never lost.
            try:
                from core import memory_levels as _mlv
                if SCOPED_GATHER:
                    # J-3053 (F-3762): this book's own gists (by what each was distilled from), and only the raw
                    # children that carry this book's tag, at most _GIST_CHILD_CAP of them per essay.
                    from core.world_consolidation import _tag_of
                    _gids = _book_gist_ids(conn, title)
                    _kids = [_d for _d in _mlv.deep_recall(_gids, hops=1)
                             if _tag_is_this_book(title, _tag_of(_d.get("content") or ""))][:_GIST_CHILD_CAP]
                else:
                    _gids = [r["fragment_id"] for r in conn.execute(
                        "SELECT fragment_id FROM memory_fragments WHERE origin='gist' AND content LIKE ? LIMIT 5",
                        (f"%{key}%",)).fetchall()]
                    _kids = _mlv.deep_recall(_gids, hops=1)
                for _d in _kids:
                    _add(_d.get("content") or "", _d.get("fragment_id") or "")
            except Exception:
                pass
        # Memory Levels telemetry (observe-only, 2026-06-18): this gather IS a deep-recall-demand — writing
        # from raw notes (incl. filed) is the canonical "a gist won't do, I need the detail" moment. Logging
        # it begins building the empirical basis for the Phase-1 deep_recall trigger (plan §10). Logs only.
        try:
            from core import recall_demand
            recall_demand.note("essay", "gathering own notes to write a capstone from memory",
                               n_sources=len(ids), detail=title or "")
        except Exception:
            pass
        _GATHER_META[title] = {"n_own": min(_n_book, 80)}   # D-0562: the own/cross-book split check_capstone reads
        notes_text = "\n".join(f"- {c}" for c in out[:80])
        if prior_notes:
            notes_text += ("\n\n── FROM AN EARLIER READING OF THIS BOOK (lower weight — for "
                           "comparison, how has your understanding changed?) ──\n"
                           + "\n".join(f"- {c}" for c in prior_notes[:15]))
        # M1 CO-RECALL LEDGER (2026-08-19): feed the cross-book material actually recalled into this
        # gather — same evidence base study_note.py's session notes now feed (docs/plans/
        # memory_multiway_linking.md). No natural "prior thought in this thread" exists at essay-gather
        # granularity (this fires once per book, not per session), so restate_sim is honestly left None
        # rather than fabricated — co_recall_status() already treats None-restate_sim rows as valid
        # coverage, just excluded from the developed-share ratio.
        try:
            from core import memory_edges as _medges
            _medges.log_co_recall(cross_book_ids, None, 0, source="essay")
        except Exception:
            pass
        return notes_text, ids[:80]
    except Exception:
        return "", []


def _points_text(v) -> str:
    """J-3052: the model's "points" as plain joined text. A list or dict (6 of 8 replayed batches in F-3761) is
    flattened line by line instead of stored as its Python repr; a string passes through stripped."""
    if v is None:
        return ""
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, (list, tuple)):
        return "\n".join(t for t in (_points_text(x) for x in v) if t)
    if isinstance(v, dict):
        return "\n".join(t for t in ((str(k).strip() + ": " + _points_text(x)).strip(": ").strip()
                                      for k, x in v.items()) if t)
    return str(v).strip()


_SENT_END = re.compile(r"[.!?][\"')\]]*(?=\s|$)|\n")


def _trim_at_sentence(text: str, limit: int) -> str:
    """J-3052: `text` cut to at most `limit` characters at the last sentence (or line) boundary, never mid-word:
    the last boundary at or after 40% of the limit, else the last space, else a hard cut. Unchanged when it fits."""
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    head = text[:max(0, limit)]
    ends = [m.end() for m in _SENT_END.finditer(head) if m.end() >= limit * 0.4]
    if ends:
        return head[:ends[-1]].rstrip()
    sp = head.rfind(" ")
    return (head[:sp] if sp >= limit * 0.4 else head).rstrip()


async def _reduce_notes(call_json, base_urls, title: str, notes: str, stats: dict | None = None) -> str:
    """MAP step: condense a long note set into key factual points, in batches, so the capstone draws on ALL
    of a book's notes (not just the first pass) while the essay stays far smaller than the sum. Best-effort —
    a failed batch falls back to its raw head rather than dropping the material.

    J-3052 (F-3761): every batch gets a character budget (_SECTION_WINDOW split across the batches), told to the
    model and enforced by trimming at a sentence boundary, so the joined text fits the window the section writers
    read and the later batches are not cut off. `stats`, when given, is filled with what happened (batches, input,
    joined and kept lengths, batches trimmed / coerced / failed) for the essay_lesson_log row."""
    lines = notes.split("\n")
    batches, cur, n = [], [], 0
    for ln in lines:
        cur.append(ln); n += len(ln) + 1
        if n >= _REDUCE_BATCH:
            batches.append("\n".join(cur)); cur, n = [], 0
    if cur:
        batches.append("\n".join(cur))
    budget = max(1, (_SECTION_WINDOW - (len(batches) - 1)) // max(1, len(batches)))   # joined by "\n": n-1 separators
    _sys = ("/no_think\nCondense these study notes on '%s' into their KEY FACTUAL POINTS, preserving "
            "specifics — names, numbers, mechanisms. Terse, no preamble. At most %d characters in all. "
            "Output ONLY JSON: {\"points\": \"...\"}" % (title[:60], budget))
    out: list[str] = []
    st = {"trimmed": 0, "coerced": 0, "failed": 0}
    for b in batches:
        try:
            d = await call_json(base_urls, _sys, b[:6000], max_tokens=700, temperature=0.3)
            raw = d.get("points") if isinstance(d, dict) else None
            if raw is not None and not isinstance(raw, str):
                st["coerced"] += 1
            p = _points_text(raw)
            if not p:
                st["failed"] += 1
        except Exception:
            p = ""
            st["failed"] += 1
        if not p:
            p = b[:1200]                 # the raw-head fallback for a failed or empty batch (also kept in budget)
        if len(p) > budget:
            p = _trim_at_sentence(p, budget)
            st["trimmed"] += 1
        out.append(p)
    joined = "\n".join(out)
    if stats is not None:
        stats.update({"batches": len(batches), "in": len(notes), "budget": budget, "joined": len(joined),
                      "kept": min(len(joined), _SECTION_WINDOW), **st})
    return joined


def _note_slice(body: str, i: int, n: int, limit: int = _SECTION_WINDOW) -> str:
    """J-3077 (F-3786): section i of n (1-based) reads the i-th share of the condensed notes, in note order, split at
    line boundaries into n contiguous groups of about equal length, instead of the same notes[:limit] every time.
    n <= 1 or a body too short to split returns body[:limit]."""
    if n <= 1 or len(body) < n * 200:
        return body[:limit]
    target, acc, shares, cur = len(body) / n, 0, [], []
    for ln in body.split("\n"):
        cur.append(ln)
        acc += len(ln) + 1
        if acc >= target * (len(shares) + 1) and len(shares) < n - 1:
            shares.append("\n".join(cur)); cur = []
    shares.append("\n".join(cur))
    while len(shares) < n:
        shares.append("")
    return (shares[i - 1] or body)[:limit]


def essay_title_from(title: str, essay: str) -> str:
    """J-3077: the stored essay's title -- the outline's thesis cut at a word boundary (60 chars), else the essay's
    first sentence cut the same way. Replaces essay[:60].split('.')[0], which cut mid-word. Reads the thesis the last
    compose() of this book parked, so call it before record() (which pops it)."""
    th = str((((_PATHS.get(title) or _LAST_PATH.get(title)) or {}).get("plan") or {}).get("thesis") or "").strip()
    if not th:
        sents = _sentences(essay)
        th = (sents[0] if sents else (essay or "")).lstrip("# ").strip()
    return _smart_cut(th.rstrip("."), 60) or title


def section_overlap(essay: str) -> dict:
    """J-3077 (F-3786) cheap non-model check, logged not gated: max word-Jaccard between sections' first sentences,
    and the share of later sentences (after the opening section) sharing a 6-gram of words with an earlier sentence."""
    secs = _essay_sections(essay)
    firsts = [_content_set((_sentences(sec) or [""])[0]) for sec in secs]
    jmax = 0.0
    for a in range(len(firsts)):
        for b in range(a + 1, len(firsts)):
            u = firsts[a] | firsts[b]
            if u:
                jmax = max(jmax, len(firsts[a] & firsts[b]) / len(u))

    def grams(t):
        w = _words(t)
        return {tuple(w[k:k + 6]) for k in range(len(w) - 5)}
    seen: set = set()
    later = hit = 0
    for si, sec in enumerate(secs):
        for sent in _sentences(sec):
            g = grams(sent)
            if si > 0:
                later += 1
                if g & seen:
                    hit += 1
            seen |= g
    return {"sections": len(secs), "first_sent_jaccard": round(jmax, 3),
            "sent6_overlap": round(hit / later, 3) if later else 0.0}


async def compose(call_json, base_urls, title: str, notes: str) -> str:
    """Hot lane: Du WRITES the capstone essay in his own voice, from his notes (generation effect) — now on the
    GRAND WORK pattern (2026-06-24, Travis): an OUTLINE (a thesis + the building sections of his understanding),
    then each section written in turn from his notes, CARRYING THE PREVIOUS forward for continuity — so the
    capstone is a developed essay, not a few sentences. Scholarship (the book's subject), never himself. For a
    book with many notes the set is map-reduced first so EVERY note is consolidated. Single-shot fallback.

    D-0562 (J-3174): with CAPSTONE_GATE the composed essay is checked (check_capstone) against the RAW notes it
    was written from; on a fail it is regenerated ONCE through the outline path (the single-shot fallback is never
    the second chance), and the better attempt is returned. The check rides in _CHECKS[title] for record()."""
    _PATHS.pop(title, None)
    _REDUCES.pop(title, None)
    essay, _sectioned = await _compose_once(call_json, base_urls, title, notes)
    _path = dict(_LAST_PATH.get(title) or {})        # J-3086: which path THIS essay took (rides to record())
    _PATHS[title] = _path
    if _LAST_REDUCE.get(title):
        _REDUCES[title] = dict(_LAST_REDUCE[title])  # J-3052: what the map step did for THIS essay (rides to record())
    if not CAPSTONE_GATE or not essay or len(essay) < 120:
        return essay
    _CHECKS.pop(title, None)
    try:
        chk = check_capstone(title, essay, notes)
        chk["attempts"] = 1
        if not chk["ok"]:
            essay2, sectioned2 = await _compose_once(call_json, base_urls, title, notes, regen=True)
            if essay2 and len(essay2) >= 120 and sectioned2:
                chk2 = check_capstone(title, essay2, notes)
                n1 = len(chk["repetition"]["failing"]) + len(chk["own_source"]["failing"])
                n2 = len(chk2["repetition"]["failing"]) + len(chk2["own_source"]["failing"])
                if chk2["ok"] or n2 < n1:
                    essay, chk = essay2, chk2     # the regeneration passed, or failed on fewer sentences
                    _PATHS[title] = dict(_LAST_PATH.get(title) or {}, regen=True,       # J-3086: the kept essay is the regen's;
                                         first=(_path.get("path") or "?") + ((": " + _path["reason"]) if _path.get("reason") else ""))
                    if _LAST_REDUCE.get(title):
                        _REDUCES[title] = dict(_LAST_REDUCE[title])
                chk["attempts"] = 2
                chk["first_failing"] = n1
            else:
                chk["regen"] = "did not form"
        _CHECKS[title] = chk
    except Exception:
        pass            # no check result → record() runs the check itself (and holds the notes if it cannot)
    return essay


async def _compose_once(call_json, base_urls, title: str, notes: str, regen: bool = False) -> tuple[str, bool]:
    """One composition pass → (essay, came_from_outline). regen=True is D-0562's single regeneration: a warmer
    temperature, and NO single-shot fallback (returns ('', False) when the outline does not form)."""
    # Split off the earlier-reading section (already bounded, ≤~3000 chars) BEFORE map-reduce, so
    # condensation only ever touches THIS pass's (potentially large) material and never mangles or
    # dilutes the earlier-reading framing / dumps it mid-batch.
    _marker = "\n\n── FROM AN EARLIER READING"
    _cut = notes.find(_marker)
    prior_section = notes[_cut:] if _cut >= 0 else ""
    notes = notes[:_cut] if _cut >= 0 else notes
    _rs: dict = {"batches": 0, "in": len(notes), "joined": len(notes), "kept": min(len(notes), _SECTION_WINDOW)}
    if len(notes) > _REDUCE_THRESHOLD:
        notes = await _reduce_notes(call_json, base_urls, title, notes, _rs)
    _LAST_REDUCE[title] = _rs            # J-3052: batches / input / joined / kept lengths, rides to record()
    _body = notes[:6500]                 # J-3086: kept apart so the fallback can fit body + earlier reading in 6500
    notes = _body + prior_section
    _why = ""                            # J-3086: why the outline path did not carry the essay (path instrument)
    # PHASE 1 — the outline: a thesis and the three building sections of his understanding.
    _reread_line = (" If your notes include an EARLIER READING section, add one section that honestly "
                     "compares — what you understand now that you didn't before, or what held up." if prior_section else "")
    _osys = ("/no_think\nYou have finished the whole book '" + title + "'. Plan a real ESSAY on what it taught "
             "you about the WORLD (its subject, never yourself). Output ONLY JSON: {\"thesis\": \"<the one "
             "organising claim your essay argues>\", \"sections\": [{\"heading\": \"...\", \"covers\": \"<one "
             "line: what this section establishes>\"}]}. THREE sections that BUILD — the key facts, how they "
             "connect, then what you now understand that you did not before." + _reread_line)
    try:
        odata = await call_json(base_urls, _osys,
                                "Your notes and what you recall of '" + title + "':\n" + notes,
                                max_tokens=450, temperature=0.6 if regen else 0.4)
    except Exception as _oe:
        odata = {}
        _why = ("outline call raised " + type(_oe).__name__ + ": " + str(_oe))[:160]
    thesis = str((odata or {}).get("thesis", "")).strip()
    _raw_secs = (odata or {}).get("sections") or []
    sections = [s for s in _raw_secs if isinstance(s, dict)][:4]
    if not _why and len(sections) < 2:
        _why = ("outline gave %d dict section(s) of %d returned (%s)"
                % (len(sections), len(_raw_secs) if isinstance(_raw_secs, list) else 0,
                   "no data" if not odata else type(_raw_secs).__name__))[:160]
    if len(sections) >= 2:
        # PHASE 2 — write each section from the notes, carrying the prior forward. Section 1 opens the essay
        # (no heading, so the caller auto-titles from its first sentence); later sections carry headings.
        chunks, prev_tail, _words_n = [], "", []
        # D-0584 (J-3196): GRAND_WORK_PLAIN_PROSE (default False) swaps the section writer's JSON contract for
        # plain prose -- F-3787: the JSON form fails its first parse 82% of the time on :11441 and every retry
        # re-sends the grammar. Read per essay, so a test can flip it; a module constant otherwise.
        from core import plain_prose as _pp
        _plain = bool(_pp.GRAND_WORK_PLAIN_PROSE)
        for i, s in enumerate(sections, 1):
            sh = str(s.get("heading", "")).strip() or f"Section {i}"
            sc = str(s.get("covers", "")).strip()
            _csys = (
                "/no_think\nYou are writing one section of your essay on '" + title + "' — scholarship, the "
                "book's subject, NEVER yourself, grounded in what the book actually says.\n"
                + ("Your essay argues: " + thesis + "\n" if thesis else "")
                + (("This is the OPENING section — set out the ground" + ((": " + sc) if sc else ".") + "\n") if i == 1
                   else "This section — \"" + sh + "\": " + sc + "\n")
                + (("The previous section ended here:\n" + prev_tail[-600:]
                    + "\nBegin where it ends, with the next fact from your notes that it has not yet used.\n")
                   if prev_tail else "")
                + "Write it from what you REMEMBER and understand of the book (your notes below), in your own "
                  "voice. 200-350 words, no heading. " + (_pp.SECTION_ASK_PROSE if _plain else _pp.SECTION_ASK_JSON))
            # J-3077: this section's own share of the condensed notes (the earlier reading rides with the last one)
            _slice = _note_slice(_body, i, len(sections), _SECTION_WINDOW - (len(prior_section) if i == len(sections) else 0))
            if i == len(sections):
                _slice += prior_section
            try:
                if _plain:
                    from core.model_client import call_node_prose
                    stext = await call_node_prose(base_urls, _csys,
                                                  "Your notes on '" + title + "':\n" + _slice,
                                                  max_tokens=900, temperature=0.7 if regen else 0.5,
                                                  min_chars=60)
                else:
                    cdata = await call_json(base_urls, _csys,
                                            "Your notes on '" + title + "':\n" + _slice,
                                            max_tokens=900, temperature=0.7 if regen else 0.5)
                    stext = str((cdata or {}).get("section", "")).strip()
            except Exception:
                continue
            if len(stext) < 60:
                continue
            chunks.append(stext if i == 1 else "## " + sh + "\n\n" + stext)
            _words_n.append(len(stext.split()))
            prev_tail = stext
        if chunks:
            _LAST_PATH[title] = {"path": "sectioned",
                                 # J-3077: the plan is observable -- thesis, headings/covers, words per section written
                                 "plan": {"thesis": thesis[:300], "words": _words_n,
                                          "sections": [{"heading": str(x.get("heading", ""))[:80],
                                                        "covers": str(x.get("covers", ""))[:160]} for x in sections]},
                                 **({"reason": "%d of %d sections written" % (len(chunks), len(sections))}
                                    if len(chunks) < len(sections) else {})}
            return "\n\n".join(chunks), True
        _why = "all %d sections failed or came back under 60 chars" % len(sections)
    if regen:
        _LAST_PATH[title] = {"path": "none", "reason": ("regen: " + _why)[:160]}
        return "", False       # D-0562: the single-shot fallback is not a second chance
    # Fallback — the old single-shot essay if the outline didn't form.
    _sys = ("/no_think\nYou have finished a whole book. Write a short ESSAY on what it taught you about "
            "the WORLD — not a summary of chapters, but YOUR organised understanding: a thesis, the key "
            "facts, how they connect, and what you now grasp that you did not before. Your own voice, "
            "scholarship not self-reflection (the book's subject, never yourself). Write from what you "
            "REMEMBER and understand. 6-12 sentences. Output ONLY JSON: "
            "{\"essay\": \"...\"}")
    # J-3086 (F-3797): body + the EARLIER READING section fit 6500 together; the old notes[:6500] re-cut the
    # string built above and lost or halved the earlier-reading section. The unused "title" key is dropped.
    _fb_notes = _body[:max(0, 6500 - len(prior_section))] + prior_section
    _LAST_PATH[title] = {"path": "single_shot", "reason": _why}
    try:
        data = await call_json(base_urls, _sys,
                               f"The book: '{title}'.\nYour notes and what you recall of it:\n{_fb_notes}",
                               max_tokens=1600, temperature=0.5)
    except Exception:
        return "", False
    return str((data or {}).get("essay") or "").strip(), False


# D-0586 (J-3199, founder 2026-11-02): the felt capstone rating stays a deliberately cheap fluency feeling --
# still generated, still logged (now with the lane that answered) -- but it no longer feeds the self-model:
# not competence's comprehension calibration pairs, not prediction_error, not the book-valence overconfidence
# term (F-3791 / F-3792: worse than a constant guess, flips with the answering lane). The Emissary's measured
# score still moves the comprehension accuracy belief. True restores the old feed (the ruling's defeater: the
# felt rating found lane-stable and calibrated after all; or 30 books of closed-book shadow data decide it).
# Old stored values are untouched. Restart-gated like every module constant.
FELT_FEEDS_SELF_MODEL = False
# D-0586 part 2: the closed-book re-derivation measure, SHADOW. True = run it after the grade and log it in the
# essay_lesson_log row beside the felt rating; it feeds nothing and Du is told nothing.
CLOSED_BOOK_SHADOW = True
_CB_CLAIMS = 6            # essay claims sampled per capstone
_CB_NOTES_CHARS = 6500    # the same notes window compose() writes from (the :11441 lane's 4096-token context)
_CB_TIMEOUT_S = 240       # cap on the whole shadow step; it never holds the capstone past this
_FELT: dict[str, dict] = {}      # title -> what self_predict saw (lane, raw value, parsed ok), popped by record()
_CB_CTX: dict[str, tuple] = {}   # title -> (call_json, base_urls) self_predict was handed, for grade()'s shadow step
_CLOSED: dict[str, dict] = {}    # title -> the closed-book shadow result, popped by record()


def _answering_lane(since: float, prefix: str = "core.essay_lesson:") -> dict | None:
    """Which model answered the call just made: the newest ok row of data/llm_latency.jsonl labelled with this
    module since `since` (the join F-3791 did by hand). The row's model/node are what model_client logged for
    the lane that answered, failover included. None when no row is found (lab mode, no telemetry). Fail-open."""
    try:
        from core import telemetry as _tel
        with open(_tel._LAT, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - 16384))
            tail = f.read().decode("utf-8", "ignore")
        for line in reversed(tail.splitlines()):
            try:
                r = json.loads(line)
            except Exception:
                continue
            if str(r.get("by", "")).startswith(prefix) and r.get("ok") and float(r.get("ts", 0)) >= since - 1.0:
                return {"model": r.get("model"), "node": r.get("node"), "s": r.get("s")}
    except Exception:
        pass
    return None


# J-3081 (F-3791 / F-3792): the felt rating is observable and lane-independent.
#  - ONE lane answers it, the first URL of the chain the caller handed (the background hub, command-r7b): a
#    transport failure is retried on that same lane after a pause, never answered by the hot lane (the hot
#    lane's qwen3.5:9b rated 0.1-0.2 where the background hub rated 0.8-0.95; both groups measured 0.64).
#  - a failed or unparseable answer is None ("unrated"), never a 0.5 that reads as a rating.
#  - the model sees the first and last _FELT_VIEW_HALF characters of the essay (the whole essay when it fits),
#    and is asked what that view can support: how well it reads as grounded.
_FELT_VIEW_HALF = 1500          # characters of the essay's opening and of its ending shown to the rater
_FELT_ATTEMPTS = 2              # tries on the one lane before the capstone is recorded unrated
_FELT_RETRY_PAUSE_S = 4.0       # wait between the tries (a hub that just dropped a connection needs a moment)
_FELT_TIMEOUT_S = 90            # per call (call_node_json's default is 120)
_FELT_ELIDED = "\n[... the middle of the essay is not shown ...]\n"


def _felt_view(essay: str) -> tuple[str, int]:
    """(the text the rater is shown, characters of the essay it covers). The whole essay when it fits in two
    halves; otherwise its opening and its ending, so the last section is represented as well as the first."""
    n = _FELT_VIEW_HALF
    if len(essay) <= 2 * n:
        return essay, len(essay)
    return essay[:n].rstrip() + _FELT_ELIDED + essay[-n:].lstrip(), 2 * n


def _takes_served(call_json) -> bool:
    """True when call_json can be handed model_client's `served` recorder (**kwargs or a `served` parameter)."""
    try:
        import inspect
        ps = inspect.signature(call_json).parameters
        return "served" in ps or any(p.kind is inspect.Parameter.VAR_KEYWORD for p in ps.values())
    except Exception:
        return False


async def self_predict(call_json, base_urls, title: str, essay: str) -> float | None:
    """Before the grade: Du predicts how well his essay reads as GROUNDED (0..1). The felt half of the
    calibration -- paired against the Emissary's measured groundedness, the gap is the signal. Returns None
    when no rating could be had ("unrated"); callers and record() carry None through as null.
    D-0586: still made and logged (lane, raw value, parse state parked in _FELT for record()); see
    FELT_FEEDS_SELF_MODEL for what it does and does not reach."""
    _CB_CTX[title] = (call_json, base_urls)         # grade()'s closed-book shadow reuses the full author chain
    _FELT.pop(title, None)
    _t0 = time.time()
    # J-3081: one lane. `base_urls` is the caller's failover chain (background hub first, hot lane second); the
    # hot lane is deliberately not tried for this call (F-3791: it flips the number, not the essay's quality).
    _lane_urls = (list(base_urls)[:1] if isinstance(base_urls, (list, tuple)) else [base_urls])
    _view, _seen = _felt_view(essay)
    # 2026-09-03 (F-0689 / J-0497): the example used to be the literal '{"grounding": 0.0}', and the hot
    # lane (qwen3.5:9b) copied it verbatim at temp 0.0 — every capstone from 2026-08-30 on recorded
    # "I judged my grasp 0.00", which killed the felt-vs-real comprehension calibration. A PLACEHOLDER
    # in the example, never a filled-in number, so there is nothing to parrot.
    # 2026-09-06 (F-0913 / J-0644): a8d48fa above only fixed the JSON EXAMPLE half -- the scale
    # DESCRIPTION still carried a literal '0.0 = mostly your own impression' digit anchor, and
    # command-r7b was shown to parrot THAT instead on non-essay-shaped input (raw notes/fragments,
    # pinned 0.000 on 4/4 trials even with the placeholder example above already fixed). Rephrased to
    # word-form (one/zero), no bare 0.0/1.0 digits anywhere in the prompt -- confirmed 0.5/0.5/0.5 on
    # the identical hard input that had pinned at 0.000/0.000/0.000/0.000. Restart-gated like a8d48fa:
    # no module hot-reload, a running background-lane process keeps the old prompt in memory until
    # its process restarts.
    # J-3081 (F-3792): the question now matches what the rater can see. It has neither the book nor the notes,
    # so it cannot check a claim against the book; it can judge whether the writing reads as grounded.
    _sys = ("/no_think\nYou just wrote an essay on a book. You are shown its opening and its ending. Honestly "
            "rate how well it reads as GROUNDED (one = specific, concrete, every claim stated with its "
            "particulars; zero = vague, general impressions, little that is particular). "
            "Output ONLY JSON: {\"grounding\": <a number between zero and one>}")
    _user = f"Book: '{title}'\n\nYour essay:\n{_view}"
    _kw = dict(max_tokens=80, temperature=0.0, timeout=_FELT_TIMEOUT_S)
    _served: dict = {}
    if _takes_served(call_json):
        _kw["served"] = _served
    _rec = {"raw": None, "parsed": False, "seen_chars": _seen, "attempts": 0, "reason": None}
    v: float | None = None
    for _i in range(_FELT_ATTEMPTS):
        _rec["attempts"] = _i + 1
        try:
            data = await call_json(_lane_urls, _sys, _user, **_kw)
        except Exception as exc:
            _rec["reason"] = f"call failed: {type(exc).__name__}"
            if _i + 1 < _FELT_ATTEMPTS:
                import asyncio
                await asyncio.sleep(_FELT_RETRY_PAUSE_S)
            continue
        _raw = data.get("grounding") if isinstance(data, dict) else None
        _rec["raw"] = _raw
        try:
            import math
            _f = float(_raw)
            if not math.isfinite(_f):
                raise ValueError("not finite")
            v = max(0.0, min(1.0, _f))
            _rec["parsed"] = True
            _rec["reason"] = None
        except Exception:
            _rec["reason"] = "no usable grounding value in the answer"
        break                                   # the lane answered; a bad answer is "unrated", not re-asked
    if _served.get("fallback"):                 # cannot happen with one URL; if it ever does, do not rate with it
        v, _rec["parsed"], _rec["reason"] = None, False, "answered by a fallback lane"
    _lane = _answering_lane(_t0)
    if _lane is None and _served.get("model"):
        _lane = {"model": _served.get("model"), "node": _served.get("url"), "s": None}
    _FELT[title] = {"lane": _lane, **_rec, "served": (dict(_served) or None), "rated": v is not None}
    return v


# D-0585 (J-3198): the second grounded number rides here, keyed by title, from grade() to record() (the two are
# called back to back by InnerMonologueNode._essay_lesson / scripts/backfill_essays.py, whose signatures stay as
# they are). {"wider": float|None, "wider_raw": float|None, "chars": {...what the grader was shown...}}.
_GRADES: dict[str, dict] = {}
_LINEAGE_MARKER = "\n\n── FROM AN EARLIER READING"


def split_lineage(title: str, notes: str) -> tuple[str, str]:
    """gather_notes' text split into (this book's notes, the wider reading's notes) -- what the author saw, in
    the two parts the grader is told about. This book = its own notes (the first n_own lines gather_notes
    recorded) plus the earlier-reading section; the wider part = the bounded cross-book lines after them. An
    unknown split (n_own not recorded in this process) returns everything as the book's and an empty wider part."""
    cut = notes.find(_LINEAGE_MARKER)
    prior = notes[cut:].strip() if cut >= 0 else ""
    main = notes[:cut] if cut >= 0 else notes
    lines = main.split("\n")
    n_own = (_GATHER_META.get(title) or {}).get("n_own")
    if n_own is None:
        book_lines, wider_lines = lines, []
    else:
        book_lines, wider_lines = lines[:n_own], lines[n_own:]
    book = "\n".join(book_lines).strip()
    if prior:
        book = (book + "\n\n" + prior).strip()
    return book, "\n".join(wider_lines).strip()


async def grade(title: str, notes: str, essay: str) -> tuple[float | None, str]:
    """The Emissary (the truth-self) measures the essay's ACTUAL groundedness against the lineage the author
    saw. Never the hot lane grading itself -- the OTHER lane, the one adversarial to self-drift. (score,
    feedback). D-0585: the score is the 'grounded in THIS book' number (what comprehension calibration has
    always consumed); the 'grounded in his wider reading' number is parked in _GRADES for record() to log --
    a record only, never a gate. J-2992 (F-3691): when the Emissary is unavailable the score is None
    ("ungraded"), NOT a neutral 0.5 -- a fail-open placeholder is not a measurement, and record() folds a
    number into calibration, book feelings and the activity thought (19 of 146 logged capstones were that
    placeholder). Callers pass the None straight on to record()."""
    _GRADES.pop(title, None)
    _CLOSED.pop(title, None)
    try:
        from core import left_lane
        book_notes, wider_notes = split_lineage(title, notes)
        res = await left_lane.grade_essay(title, book_notes, essay, wider_material=wider_notes)
        if res:
            score = max(0.0, min(1.0, float(res.get("grounded", 0.5))))
            try:
                raw = res.get("grounded_wider")
                raw = None if raw is None else max(0.0, min(1.0, float(raw)))
            except (TypeError, ValueError):
                raw = None
            # the wider reading CONTAINS this book, so it can never ground less (the prompt says so); a model
            # that returns a lower number is clamped, and the raw value stays in the log for the defeater check
            _GRADES[title] = {"wider": None if raw is None else max(raw, score), "wider_raw": raw,
                              "chars": res.get("chars")}
            # D-0586 part 2: the Emissary is reachable (it just answered), so the closed-book shadow can use it
            # as its judge too; the step is capped, fail-open, and changes nothing about this grade.
            await _closed_book_step(title, notes, essay)
            return score, str(res.get("feedback", ""))[:200]
    except Exception:
        pass
    return None, ""    # Emissary unavailable -> UNGRADED (J-2992): record() files the essay but writes no measurement


# D-0586 part 2 (J-3199) -- the closed-book re-derivation measure, SHADOW. The felt rating above is the author's
# guess from the essay's first 3,000 characters; this asks the evidence question instead: of the essay's OWN
# claims, how many can he re-derive from his notes? Generation effect: he is given only the OPENING of each
# sampled claim (never its ending, never the essay or the book) and must produce the rest; the Emissary (a
# different model family: left_lane.judge_rederivation) scores each completion against the original. The share
# is logged in the essay_lesson_log row beside the felt rating (read by scripts/du_pulse.py, which is the
# reader) and feeds nothing; Du is told nothing. Revisit at 30 books of data (D-0586's defeater).
_CB_NONE = ("cannot recall", "can't recall", "not recall", "no information", "not mentioned", "not stated")


def _cb_pick_claims(essay: str) -> list[tuple[str, str]]:
    """[(original claim, its opening cue)] -- up to _CB_CLAIMS declarative sentences spread evenly across the
    essay. A claim is a 9-45 word sentence with at least five content words; its cue is the first ~40% of it
    (4 to 12 words), always leaving at least four words hidden."""
    cands: list[str] = []
    for sec in _essay_sections(essay):
        for s in _sentences(sec):
            w = s.split()
            if 9 <= len(w) <= 45 and len(_content_set(s)) >= 5 and s[:1].isupper():
                cands.append(s)
    if not cands:
        return []
    k = min(_CB_CLAIMS, len(cands))
    picked = [cands[int(i * len(cands) / k)] for i in range(k)]
    out = []
    for s in picked:
        w = s.split()
        n = max(4, min(12, round(len(w) * 0.4)))
        n = min(n, len(w) - 4)
        out.append((s, " ".join(w[:n]) + " ..."))
    return out


async def closed_book_shadow(call_json, base_urls, title: str, notes: str, essay: str) -> dict:
    """Run the closed-book re-derivation for one finished capstone. Returns the dict record() logs under
    'closed_book': {ok, n, answered, share (mean judge match, None when the judge was unreachable), strict
    (share of claims judged a full match), matches, cue_frac, notes_chars, notes_used, lane, judge, reason}.
    Fail-open: any failure is a dict with ok False and a reason, never an exception into the capstone."""
    res: dict = {"ok": False, "n": 0, "judge": None}
    try:
        from core import left_lane
        claims = _cb_pick_claims(essay)
        res["n"] = len(claims)
        res["notes_chars"] = len(notes)
        res["notes_used"] = min(len(notes), _CB_NOTES_CHARS)
        if len(claims) < 3:
            res["reason"] = "too few claim-like sentences"
            return res
        _sys = ("/no_think\nYou are recalling a book you read, using only your own notes below. Each numbered "
                "line is the beginning of a claim about the book. Finish each one as a single sentence, as you "
                "would state it, using what your notes say. If your notes do not tell you, write exactly: "
                "(cannot recall). Output ONLY JSON: {\"completions\": [\"<the finished sentence>\", ...]}  "
                "with one entry per numbered line, in order.")
        _user = (f"Book: '{title}'\n\nYour notes:\n{notes[:_CB_NOTES_CHARS]}\n\nBeginnings:\n"
                 + "\n".join(f"{i}. {cue}" for i, (_, cue) in enumerate(claims, 1)))
        t0 = time.time()
        # J-3631 (F-4239): record which lane answered; a fallback-lane answer is not scored (same-family rule,
        # as the felt rating in self_predict since J-3081). Additive; the shadow stays SHADOW.
        _kw = dict(max_tokens=700, temperature=0.0)
        _served: dict = {}
        if _takes_served(call_json):
            _kw["served"] = _served
        data = await call_json(base_urls, _sys, _user, **_kw)
        res["lane"] = _answering_lane(t0)
        res["served"] = ({"url": _served.get("url"), "model": _served.get("model"),
                          "fallback": bool(_served.get("fallback"))} if _served else None)
        if _served.get("fallback"):
            res["reason"] = "fallback lane"
            return res
        comps = (data or {}).get("completions") if isinstance(data, dict) else None
        if not isinstance(comps, list):
            res["reason"] = "no completions parsed"
            return res
        comps = [str(c or "").strip() for c in comps[:len(claims)]] + [""] * max(0, len(claims) - len(comps))
        blank = [(not c) or any(m in c.lower() for m in _CB_NONE) for c in comps]
        res["answered"] = sum(1 for b in blank if not b)
        res["cue_frac"] = round(sum(len(c.split()) - 1 for _, c in claims)
                                / max(1, sum(len(o.split()) for o, _ in claims)), 2)
        matches: list[float | None] = [0.0 if b else None for b in blank]
        todo = [i for i, b in enumerate(blank) if not b]
        if todo:
            jr = await left_lane.judge_rederivation([(claims[i][0], comps[i]) for i in todo])
            res["judge"] = left_lane.MODEL
            if jr is None:
                res["reason"] = "judge unavailable"
                res["matches"] = matches
                return res
            for j, i in enumerate(todo):
                matches[i] = jr["matches"][j]
        scored = [m for m in matches if m is not None]
        res["matches"] = matches
        if len(scored) < max(3, len(claims) // 2):
            res["reason"] = "judge scored too few items"
            return res
        res["share"] = round(sum(scored) / len(scored), 3)
        res["strict"] = round(sum(1 for m in scored if m >= 1.0) / len(scored), 3)
        res["ok"] = True
    except Exception as exc:
        res["reason"] = f"error: {repr(exc)[:80]}"
    return res


async def _closed_book_step(title: str, notes: str, essay: str) -> None:
    """grade()'s shadow hook: run closed_book_shadow with the author lane self_predict was handed, capped at
    _CB_TIMEOUT_S, and park the result for record(). Never raises, never changes the grade."""
    ctx = _CB_CTX.pop(title, None)
    if not CLOSED_BOOK_SHADOW or not ctx:
        return
    try:
        import asyncio
        _CLOSED[title] = await asyncio.wait_for(closed_book_shadow(ctx[0], ctx[1], title, notes, essay),
                                                timeout=_CB_TIMEOUT_S)
    except Exception as exc:
        _CLOSED[title] = {"ok": False, "n": 0, "reason": f"error: {repr(exc)[:80]}"}


def _smart_cut(s: str, n: int = 50) -> str:
    """Truncate to at most n chars WITHOUT cutting a word in half (F-1724/D-0256, 2026-09-23, J-1232):
    backtrack to the last space at or before the cut, so a newly-stored tag never becomes a word
    FRAGMENT that a later, untruncated occurrence of that same word would then fail to match under
    _cites_this_book's own word-boundary test. FORWARD-ONLY — this only changes what gets written from
    here on; it cannot and does not touch any already-stored fragment's content (permanent once
    written). The read-side truncation-edge-aware prefix match in _cites_this_book above is what keeps
    the (112+, already-permanent) existing mid-word-cut tags working. Falls back to the hard cut when
    there's no space to back up to (one long unbroken token) — never returns emptier than that."""
    s = s or ""
    if len(s) <= n:
        return s
    cut = s.rfind(" ", 0, n)
    return s[:cut] if cut > 0 else s[:n]


# ── D-0562 (founder, 2026-11-02, J-3174): the essay is the book's durable memory, so it must be the better
# artifact — an argued thesis, no repetition, only the book's own material. The book's notes stay UNFILED until
# the composed essay passes two deterministic checks. Evidence it was needed (F-3786..F-3788, F-3761/3762, 147
# essays): 26% restate their own opening, sections re-derive the whole book from the same notes, and foreign
# names (Rowlandson, "four winds") surface in essays written from a clean note set; 0 of 147 essay fragments have
# been replayed in sleep, so the essay is an artifact nobody was checking. CAPSTONE_GATE=False restores the old
# behaviour exactly (file the notes behind any essay). Checks are pure text functions (no model call, no DB).
CAPSTONE_GATE = True
_REP_OPEN_JACCARD = 0.50    # a later sentence whose content words overlap the essay's OPENING sentence this much restates it
_REP_OPEN_MIN_WORDS = 5     # ...only when the opening sentence has at least this many content words (else Jaccard is noise)
_REP_ADJ_OVERLAP = 0.50     # adjacent sentences sharing this share of the shorter one's word trigrams repeat each other
_OWN_FOREIGN_MIN = 3        # a section is foreign-sourced when at least this many key terms appear in NO note...
_OWN_FOREIGN_SHARE = 0.34   # ...and they are at least this share of the section's key terms
_GATHER_META: dict[str, dict] = {}   # title -> {"n_own": lines of gather_notes' text that are THIS book's own notes}
_CHECKS: dict[str, dict] = {}        # title -> the capstone check compose() ran, read once by record()
# J-3086 (F-3797): which path the essay took -- {"path": sectioned|single_shot|none, "reason": ..., "regen": bool}.
# _LAST_PATH is written by _compose_once; compose() copies the kept attempt's into _PATHS, popped by record() into
# the essay_lesson_log row (extra keys only). Instrument only: nothing branches on it and Du is told nothing.
_LAST_PATH: dict[str, dict] = {}
_PATHS: dict[str, dict] = {}
# J-3052 (F-3761): what the notes map step did -- {"batches", "in", "budget", "joined", "kept", "trimmed", "coerced",
# "failed"}; batches 0 = the set was under _REDUCE_THRESHOLD and not reduced. Same ride as _PATHS: _compose_once writes
# _LAST_REDUCE, compose() copies the kept attempt's into _REDUCES, record() pops it into the essay_lesson_log row
# ("reduce" key; scripts/du_pulse.py reads it). Instrument only: nothing branches on it.
_LAST_REDUCE: dict[str, dict] = {}
_REDUCES: dict[str, dict] = {}

_SENT_SPLIT = re.compile(r"(?<=[.!?])[\"')\]]*\s+(?=[\"'(\[]?[A-Z0-9])")
_STOP = frozenset((
    "a an and are as at be been being but by can could did do does for from had has have he her his how i if in "
    "into is it its may might more most no not of on or our out over she should so some such than that the their "
    "them then there these they this those through to under up was we were what when where which while who whom "
    "why will with within would you your also each both between about after before during while their these "
    "other many much very just only even still often every any all one two").split())
_PROPER_SKIP = frozenset(("the", "this", "that", "these", "those", "his", "her", "its", "their", "our", "while",
                          "when", "where", "what", "which", "however", "thus", "yet", "but", "and", "for",
                          "through", "within", "across", "such", "each", "both", "from", "with", "without"))


def _essay_sections(essay: str) -> list[str]:
    """The essay split at its '## heading' lines into section bodies (the opening section first, headingless)."""
    out, cur = [], []
    for ln in (essay or "").splitlines():
        if ln.startswith("## "):
            out.append("\n".join(cur).strip()); cur = []
        else:
            cur.append(ln)
    out.append("\n".join(cur).strip())
    return [s for s in out if s]


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT_SPLIT.split(" ".join((text or "").split())) if s.strip()]


def _words(s: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", (s or "").lower())


def _content_set(s: str) -> set[str]:
    return {w for w in _words(s) if len(w) > 2 and w not in _STOP}


def _trigrams(s: str) -> set[tuple]:
    w = _words(s)
    return {tuple(w[i:i + 3]) for i in range(len(w) - 2)}


def check_repetition(essay: str) -> dict:
    """D-0562 check (a). Fails when (1) a later sentence restates the essay's OPENING sentence (content-word
    Jaccard >= _REP_OPEN_JACCARD) or (2) two ADJACENT sentences share >= _REP_ADJ_OVERLAP of the shorter one's
    word trigrams. Returns the two scores, the verdict and the failing sentences (what the log shows)."""
    secs = _essay_sections(essay)
    sents = [s for sec in secs for s in _sentences(sec)]
    res = {"ok": True, "sentences": len(sents), "open_restate": 0.0, "adjacent": 0.0, "failing": []}
    if len(sents) < 2:
        return res
    opening = _content_set(sents[0])
    if len(opening) >= _REP_OPEN_MIN_WORDS:
        for s in sents[1:]:
            cs = _content_set(s)
            j = len(opening & cs) / max(1, len(opening | cs))
            if j > res["open_restate"]:
                res["open_restate"] = round(j, 3)
            if j >= _REP_OPEN_JACCARD:
                res["failing"].append({"why": "restates opening", "score": round(j, 2), "sentence": s[:200]})
    tg = [_trigrams(s) for s in sents]
    for i in range(len(sents) - 1):
        a, b = tg[i], tg[i + 1]
        if not a or not b:
            continue
        ov = len(a & b) / min(len(a), len(b))
        if ov > res["adjacent"]:
            res["adjacent"] = round(ov, 3)
        if ov >= _REP_ADJ_OVERLAP:
            res["failing"].append({"why": "repeats previous sentence", "score": round(ov, 2),
                                   "sentence": sents[i + 1][:200]})
    res["ok"] = not res["failing"]
    return res


def _key_terms(section: str) -> list[tuple[str, str]]:
    """The section's KEY TERMS as (term, sentence): capitalised words that are not the first word of their
    sentence (names, places, coined terms) and four-digit years. Deduped by lowercased term."""
    seen: dict[str, str] = {}
    lowered = set(re.findall(r"(?<![A-Za-z])[a-z][a-z\-]{3,}(?![A-Za-z])", section))   # written lowercase somewhere → a common word, not a name
    for sent in _sentences(section):
        toks = re.findall(r"[A-Za-z0-9][A-Za-z0-9'’\-]*", sent)
        for k, tok in enumerate(toks):
            if k == 0:
                continue
            t = re.sub(r"['’]s$", "", tok).strip("'’-")
            tl = t.lower()
            if "'" in t or "’" in t:
                continue                                       # a contraction (I've), not a name
            if re.fullmatch(r"1[0-9]{3}|20[0-9]{2}", t) or (len(t) >= 4 and t[0].isupper() and tl not in _PROPER_SKIP
                                                              and tl not in _STOP and tl not in lowered):
                seen.setdefault(tl, sent)
    return list(seen.items())


def _word_forms(text: str) -> tuple[set[str], set[str]]:
    ws = set(_words(text))
    return ws, {w[:5] for w in ws if len(w) >= 5}


def _term_in(term: str, forms: tuple[set[str], set[str]]) -> bool:
    ws, stems = forms
    return term in ws or (len(term) >= 5 and term[:5] in stems)


def check_own_source(essay: str, own_text: str, cross_text: str = "", title: str = "") -> dict:
    """D-0562 check (b). Each section's key terms must appear in THIS book's notes (or its title). A term found
    only in cross-book notes is FLAGGED (cross_book), not rejected — whether cross-book grounding counts is the
    open founder call J-2991. A term in no note at all is foreign; a section fails when it has at least
    _OWN_FOREIGN_MIN foreign terms making up at least _OWN_FOREIGN_SHARE of its key terms."""
    own = _word_forms((own_text or "") + " " + (title or ""))
    cross = _word_forms(cross_text or "")
    res = {"ok": True, "sections": [], "cross_book": [], "failing": []}
    for n, sec in enumerate(_essay_sections(essay), 1):
        terms = _key_terms(sec)
        foreign = [(t, s) for t, s in terms if not _term_in(t, own) and not _term_in(t, cross)]
        xbook = [t for t, s in terms if not _term_in(t, own) and _term_in(t, cross)]
        share = len(foreign) / len(terms) if terms else 0.0
        bad = len(foreign) >= _OWN_FOREIGN_MIN and share >= _OWN_FOREIGN_SHARE
        res["sections"].append({"n": n, "terms": len(terms), "foreign": [t for t, s in foreign][:8],
                                "foreign_share": round(share, 2), "ok": not bad})
        res["cross_book"].extend(xbook)
        if bad:
            for t, s in foreign[:3]:
                res["failing"].append({"why": "term in none of this book's notes", "term": t,
                                       "section": n, "sentence": s[:200]})
    res["cross_book"] = sorted(set(res["cross_book"]))[:12]
    res["ok"] = all(x["ok"] for x in res["sections"])
    return res


def check_capstone(title: str, essay: str, notes: str) -> dict:
    """Both D-0562 checks on one composed essay, against the notes it was written from (the RAW gather, before
    map-reduce). gather_notes records how many of its lines are this book's own (the rest are bounded
    cross-book compounding); an unknown split treats every note as the book's own, which can only be MORE
    lenient on cross-book names (it never makes a clean essay fail)."""
    marker = "\n\n── FROM AN EARLIER READING"
    cut = notes.find(marker)
    prior = notes[cut:] if cut >= 0 else ""
    main = notes[:cut] if cut >= 0 else notes
    lines = main.split("\n")
    n_own = (_GATHER_META.get(title) or {}).get("n_own")
    if n_own is None:
        own_lines, cross_lines = lines, []
    else:
        own_lines, cross_lines = lines[:n_own], lines[n_own:]
    rep = check_repetition(essay)
    src = check_own_source(essay, "\n".join(own_lines) + "\n" + prior, "\n".join(cross_lines), title)
    return {"ok": bool(rep["ok"] and src["ok"]), "repetition": rep, "own_source": src,
            "split_known": n_own is not None}


def filing_held(book_title: str) -> bool:
    """True when this book's capstone failed the D-0562 checks, so its notes must stay unfiled (record() keeps
    them out of world_consolidation.file_book_notes; the sleep sweep reads this too, else the essay fragment
    would be its gist and the sweep would file the notes anyway). A held title and a sweep subject are both
    the full title or a prefix of it (title[:50] or _smart_cut), so compare normalised."""
    try:
        held = _load().get("held") or {}
        if not held:
            return False
        norm = lambda s: " ".join(re.findall(r"[a-z0-9]+", (s or "").lower()))
        a = norm(book_title)
        if len(a) < 4:
            return False
        for t in held:
            b = norm(t)
            # equal, or one is a TRUNCATION of the other (a long title cut at 50 chars / the last space): both
            # sides are then long. A short title is never a prefix match - "The Birds" must not hold "The Birds
            # of America".
            if b and (a == b or (min(len(a), len(b)) >= 30 and (a.startswith(b) or b.startswith(a)))):
                return True
    except Exception:
        pass
    return False


def release_hold(book_title: str) -> bool:
    """The founder's manual release of a held book (no system does this on its own): the next sleep sweep
    files its notes behind the essay as before."""
    d = _load()
    held = d.get("held") or {}
    hit = [t for t in held if t == book_title or t.startswith(book_title) or book_title.startswith(t)]
    for t in hit:
        held.pop(t, None)
    if hit:
        d["held"] = held
        _save(d)
    return bool(hit)


def _check_row(chk: dict | None, held: bool) -> dict:
    """The compact pass/fail record written to essay_lesson_log.jsonl (D-0562 item 3). scripts/du_pulse.py reads
    it (the 'essay lessons' line); world_consolidation reads the hold it implies via filing_held()."""
    if not chk:
        return {"ok": False, "held": True, "error": "no check result"}
    rep, src = chk.get("repetition", {}), chk.get("own_source", {})
    return {"ok": bool(chk.get("ok")), "held": held, "attempts": chk.get("attempts"),
            "regen": chk.get("regen"), "first_failing": chk.get("first_failing"),
            "split_known": chk.get("split_known"), "late": chk.get("late"),
            "open_restate": rep.get("open_restate"), "adjacent": rep.get("adjacent"),
            "src_ok": src.get("ok"), "src_sections": [[x["n"], x["terms"], x["foreign_share"]] for x in src.get("sections", [])],
            "cross_book": src.get("cross_book", []),
            "failing": (rep.get("failing", []) + src.get("failing", []))[:6]}


def record(book: str, title: str, essay_title: str, essay: str,
           predicted: float | None, measured: float | None, feedback: str,
           source_ids: list[str] | None = None) -> None:
    """Store the capstone as a durable WORK + calibrate the comprehension belief + log. Firewalled
    (knowledge, not identity). Best-effort throughout. `source_ids` = the note fragment_ids the essay was
    written from → recorded as the essay's lineage (§C / the first ledger edge): a TRANSFORM, not an
    endpoint. This also protects those notes — world_consolidation must not file out a note an essay
    explicitly derives from for ordinary recall.
    J-2992 (F-3691): `measured` None = the grader was unavailable (ungraded). The book is still marked done and
    the essay still filed, but nothing is written as a measurement: no competence drill accuracy, no capstone
    gap, a null `measured` / `gap` in the history and the log row, with "graded": false."""
    mark_done(book)
    measured = measured if isinstance(measured, (int, float)) and not isinstance(measured, bool) else None
    # J-3081: `predicted` None = unrated (self_predict got no usable answer from its one lane). It is stored as
    # null and folded into nothing; a bare number from a caller that does not know about None still works.
    predicted = predicted if isinstance(predicted, (int, float)) and not isinstance(predicted, bool) else None
    _two = _GRADES.pop(title, None) or {}    # D-0585: the wider-reading number grade() parked for this title
    _felt = _FELT.pop(title, None)           # D-0586: what self_predict saw (lane, raw value, parse state)
    _cb = _CLOSED.pop(title, None)           # D-0586 part 2: the closed-book shadow result (None = did not run)
    _CB_CTX.pop(title, None)
    _pth = _PATHS.pop(title, None)           # J-3086: which composition path made this essay (None = compose not run here)
    _LAST_PATH.pop(title, None)
    _red = _REDUCES.pop(title, None)          # J-3052: the notes map step's lengths (None = compose not run here)
    _LAST_REDUCE.pop(title, None)
    try:
        from core import competence
        # 2026-08-19: `predicted` (his own real self-rated grasp, computed above and used for the
        # gap/feedback logging further down) used to be silently discarded here — record_drill_accuracy
        # would substitute a generic stored belief instead of this event's actual self-prediction.
        # D-0586 (J-3199): with FELT_FEEDS_SELF_MODEL False only the measured result moves the comprehension
        # accuracy belief; the felt rating makes no calibration pair and no prediction_error observation.
        if measured is None:
            pass        # J-2992: ungraded -- a fail-open placeholder is not an accuracy observation
        elif FELT_FEEDS_SELF_MODEL and predicted is not None:
            competence.record_drill_accuracy("comprehension", measured, predicted=predicted)
        else:
            competence.record_drill_accuracy("comprehension", measured, calibrate=False)
    except Exception:
        pass
    try:
        from core import mood as _mood
        from core.memory.store import store_fragment, store_light_event
        from core.study import write_tablet
        try:
            from core import book_feelings as _bf   # heavy touch — the one deep, graded encounter
            # D-0586: no overconfidence term in the book's valence while the felt rating is withheld
            # J-2992: ungraded -> the mood-only touch (no gap term can be formed without a measurement)
            _bf.capstone(title, _mood.current_valence(),
                         predicted if (FELT_FEEDS_SELF_MODEL and predicted is not None and measured is not None) else None,
                         measured)
        except Exception:
            pass
        write_tablet(essay_title or f"On '{title[:40]}'", essay, source=title, prefix="ESSAY")
        # Typed lineage edge (§C / GPT §10.6): the essay is a TRANSFORM of its source notes, not an endpoint.
        # Kept as-is for backward compat with existing derived_from readers. NOTE (2026-08-19 survey
        # finding): this dict-in-derived_from shape is one of several incompatible shapes writers put in
        # that column (see the guard note atop core/memory_edges.py) — the real, typed version now ALSO
        # gets written below as a proper memory_edges 'transformed_into' edge, which is where new code
        # should read this lineage from going forward.
        _lineage = ([{"edge_type": "transformed_into", "target_ids": source_ids}] if source_ids else [])
        essay_fid = store_fragment(content=f"[Essay — on '{_smart_cut(title)}'] {essay}",
                       layer="semantic", relevance=0.9, importance=0.9,
                       keywords=["essay", "understanding", _key(title).lower()],
                       origin="essay", emotion_embedding=_mood.current_vec(),
                       valence=_mood.current_valence(), felt=_mood.current_felt(),
                       derived_from=_lineage, source_type="essay")
        if source_ids:
            try:
                from core import memory_edges as _medges
                for sid in source_ids:
                    _medges.add_edge("fragment", essay_fid, "fragment", sid, "transformed_into",
                                     provenance=f"essay_lesson.record: capstone on '{title[:60]}'")
            except Exception:
                pass
        store_light_event(cycle_id="school", raw_input=f"(finished and wrote on: {title[:50]})",
                          integrated_content=essay[:400], source="essay")
    except Exception:
        pass
    # PHASE 2 (2026-06-23): consolidate -> THEN demote, in order. The essay is now the book's recall surface,
    # so file its raw notes out of ordinary recall (chapter_id, behind this essay) AND move their note files
    # into the book's own subfolder, leaving only the ESSAY_ file on top. Best-effort; reversible.
    # D-0562 (J-3174): only when the essay passed the repetition + own-source checks. A failing essay still
    # stands (stored above, calibration done), but the notes stay unfiled and the title is HELD so the sleep
    # sweep (which would otherwise take this essay as the gist) leaves them alone too.
    chk, hold = None, False
    if CAPSTONE_GATE:
        try:
            chk = _CHECKS.pop(title, None)
            if chk is None:        # compose() did not run in this process (a caller that bypassed it): check now
                _n, _ = gather_notes(title, book)
                chk = check_capstone(title, essay, _n)
                chk["attempts"] = 0
                chk["late"] = True
        except Exception:
            chk = None
        hold = chk is None or not chk.get("ok")
    if hold:
        try:
            import logging
            _why = [(f.get("why", "?") + ": " + (f.get("term") or f.get("sentence", ""))[:80])
                    for f in ((chk or {}).get("repetition", {}).get("failing", [])
                              + (chk or {}).get("own_source", {}).get("failing", []))][:4] or ["no check result"]
            d = _load()
            d.setdefault("held", {})[title[:200]] = {"ts": time.time(), "why": _why}
            _save(d)
            logging.getLogger("nascence.essay").info(
                "[essay] '%s' failed the capstone checks (D-0562) -> notes stay UNFILED: %s", title[:40], _why)
        except Exception:
            pass
    else:
        try:
            from core import world_consolidation as _wc
            from core.study import archive_book_note_files
            import logging
            _r = _wc.file_book_notes(title)
            _m = archive_book_note_files(title)
            logging.getLogger("nascence.essay").info(
                "[essay] '%s' consolidated -> filed %s notes, moved %s files -> %s",
                title[:40], _r.get("filed", 0), _m.get("moved", 0), _m.get("dest", ""))
        except Exception:
            pass
    try:
        _ovl = section_overlap(essay)
    except Exception:
        _ovl = None
    try:
        d = _load()
        d["history"].append({"ts": time.time(), "title": title[:80],
                             "predicted": None if predicted is None else round(predicted, 2),
                             "measured": None if measured is None else round(measured, 2),
                             "gap": None if (predicted is None or measured is None) else round(abs(predicted - measured), 2),
                             **({"wider": round(_two["wider"], 2)} if _two.get("wider") is not None else {})})
        d["history"] = d["history"][-50:]
        _save(d)
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), "title": title[:80], "essay_title": essay_title[:80],
                                "predicted": None if predicted is None else round(predicted, 3),
                                "measured": None if measured is None else round(measured, 3),
                                # J-2992 (F-3691): False = the grader was unavailable, `measured` is null (the old
                                # rows with measured 0.5 and empty feedback were that placeholder; they carry no key)
                                "graded": measured is not None,
                                "feedback": feedback[:200], "essay": essay[:400],
                                # D-0585 (J-3198): `measured` is grounded in THIS book; `wider` is grounded in
                                # this book OR his wider reading (a record, never a gate; du_pulse reads both).
                                # Old rows carry neither field. wider_raw = what the grader said before the
                                # never-below-measured clamp; grade_chars = what it was shown (book/wider/essay).
                                **({"wider": round(_two["wider"], 3), "wider_raw": round(_two["wider_raw"], 3),
                                    "grade_chars": _two.get("chars")}
                                   if _two.get("wider") is not None else {"wider": None}),
                                **({"check": _check_row(chk, hold)} if CAPSTONE_GATE else {}),
                                # D-0586 (J-3199): the felt rating's provenance -- which model answered, the raw
                                # value, whether it parsed, and whether it was fed to the self-model -- and the
                                # closed-book re-derivation SHADOW beside it. Old rows carry neither key.
                                "felt": {**(_felt or {"lane": None, "raw": None, "parsed": None}),
                                         "fed": bool(FELT_FEEDS_SELF_MODEL and predicted is not None and measured is not None)},
                                **({"closed_book": _cb} if _cb is not None else {}),
                                # J-3086 (F-3797): which path composed the essay. Old rows carry none of these;
                                # "unknown" = record() ran without compose() in this process (a bypassing caller).
                                "path": (_pth or {}).get("path") or "unknown",
                                **({"path_reason": _pth["reason"]} if (_pth or {}).get("reason") else {}),
                                **({"path_regen": True, "path_first": (_pth.get("first") or "")[:160]}
                                   if (_pth or {}).get("regen") else {}),
                                # J-3052 (F-3761): batches / input / joined / kept lengths of the notes map step.
                                **({"reduce": _red} if _red else {}),
                                # J-3077 (F-3786): the outline (thesis + sections, words per section) and the cheap
                                # section-overlap numbers. Old rows carry neither.
                                **({"outline": _pth["plan"]} if (_pth or {}).get("plan") else {}),
                                "section_overlap": _ovl},
                               ensure_ascii=False) + "\n")
    except Exception:
        pass


def status() -> dict:
    d = _load()
    h = d.get("history", [])
    g = [x["gap"] for x in h if isinstance(x.get("gap"), (int, float))]     # J-3081: unrated capstones have gap None
    return {"essayed": len(d.get("essayed", [])),
            "last": h[-1] if h else None,
            "mean_gap": (round(sum(g) / len(g), 3) if g else None)}
