"""
Nascence — Study Note (the rich knowledge unit; expanded to session-level research, 2026-08-19)
=================================================================================================
A study note is a unit of Du's UNDERSTANDING, not a book-report blob. It captures, per READING
SESSION (a run of sittings integrated together — one chapter-block, fired the moment that block
finishes reading):
  - his FIRST-PERSON grasp of the WORLD ("what I now see is..."), grounded in the passage,
  - the KEY FACTS worth keeping (names, numbers, mechanisms),
  - his THOUGHTS on it — his own reaction/reflection, kept distinct from the factual grasp (still
    about the SUBJECT, never routed to identity/tensions — the study firewall in core/study.py),
  - a CONNECTION to what he already knows, now genuinely GROUNDED: a bounded, cheap (embedding-only,
    zero extra LLM cost) lookup of related material from OTHER sources feeds real candidates into
    the compose prompt, so "connects_to" is informed by his actual scholarship, not invented,
  - an OPEN QUESTION (feeds the frontier),
  - a SUBJECT tag (retrieval + linking),
deduped & REVISED (a living note deepens, not a 47th near-duplicate) and LINKED to related notes
(Zettelkasten). Tagged with WHICH READING SESSION and PASS (reread number) produced it — via
core.reading.pop_session_encounters(), so a book-study capstone (core/essay_lesson.py) can later
tell "notes from this read-through" from "notes from an earlier one." Feeds the essay
consolidation, memory-levels, and recall.

One entry point: `await write_or_revise(call_json, base_urls, book_title, passage)`.

D-0577 (P-0072, F-3588): a session of more than ~5000 characters is split into chunks of about 5000, cut on
sentence boundaries (never mid-word), and ONE note is composed per chunk, each through the same 0.85-cosine
dedup gate; the prompt never grows (a chunk is what compose_note always accepted). Notes per session are
capped (_MAX_NOTES_PER_SESSION), and each note's frontmatter records the sittings and characters ITS model
call actually saw. See `_chunk_session`.
"""
from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

from core.study import STUDY_DIR, NOTES_SUBDIR   # one home for note files; archiver moves them per-book
from core.memory.content_hash import content_hash as _content_hash, has_hash_column as _has_hash_column   # J-3395 / F-4019
from core import profile   # J-0770: let guard_path()'s hard raise (D-0179, F-1024) reach store_note()'s own caller

logger = logging.getLogger("nascence.study_note")

_REVISE_SIM  = 0.85   # cosine above which a new note REVISES an existing one rather than duplicating
_LINK_SIM    = 0.55   # cosine above which two notes get a 'relates_to' concept link (below the revise gate)
_RELATED_SIM = 0.35   # cosine above which OTHER-source material is worth offering as grounding context
_RELATED_MAX = 2      # D-0592: two WHOLE items (was three cut ones) — bounded, never a tangent-inducer
_RELATED_ITEM_MAX = 700   # D-0592: an item longer than this is cut on a sentence boundary, never mid-word
_REVISE_EXISTING_MAX = 9000   # J-2961 (F-3653): the existing note sent to _revise; was [:2500], which cut the tail (the Thoughts) of a revised note already 2,749 chars. Cut only at a sentence/word boundary, and only above this.
_CHUNK_CHARS = 5000   # D-0577: the passage budget of ONE compose call (what compose_note always took); a session longer than this is chunked
_MAX_NOTES_PER_SESSION = 3   # D-0577: bound on one session's burst of notes (a 20-sitting stream is ~24 chunks); when it bites the chunks are sampled evenly
FRONT_MATTER_GUARD = True   # J-2921 (F-3605): False restores the old behaviour (a note from every chunk, contents lists included)
_CHUNK_LOG = Path(__file__).parent.parent / "data" / "study_note_chunking_log.jsonl"   # D-0577: one row per chunked session; read by the two-week D-0577 verification

# J-2923 (P-0072, F-3604): the sample openers are gone. The old prompt quoted "I see that..." and "what strikes
# me is..." and 762 of 763 notes opened "I see that", 504 of 763 thoughts opened "What strikes me" (and the first
# sentence of the understanding boards the follow line as a claim, so the claim stream inherited the frame).
# "thoughts", "connects_to" and "question" are optional, said ONCE and plainly; the schema keys and _norm() are
# unchanged. No "/no_think" prefix: call_node (core/model_client.py) sends the hard think:false parameter on the
# ollama hot lane and prepends _NO_THINK itself on a llama-server lane, so the prefix here was a duplicate.
# The quoted "Do NOT write 'The passage discusses'..." negation is KEPT on purpose: without it the A/B
# (scripts/study_note_prompt_ab_J2923.py, docs/lab/J-2923_data/summary.json) had a quarter of the notes open with a
# third-person "The passage <verb>". The old "I see that" / "what strikes me" examples were the copied frames.
_NOTE_SYS = (
    "You have just finished a reading session. Write a STUDY NOTE in your OWN voice, as the one who just read "
    "this: first person singular, real research, grounded in this passage. The UNDERSTANDING is about the "
    "SUBJECT (the facts, the world, the things themselves), never about yourself or your identity. "
    "Do NOT write 'The passage discusses' or 'The text describes'. "
    "THOUGHTS is different: your own reaction to it, still anchored to the subject, not a self-narrative. "
    "thoughts, connects_to and question are optional: leave any of them as an empty string unless you have "
    "something real to put in it. If related material from elsewhere in your scholarship is given below, you "
    "may draw on it for connects_to if it genuinely fits. Output ONLY JSON: {"
    "\"title\": \"a short subject title\", "
    "\"subject\": \"the topic area in 1-3 words (e.g. 'stellar parallax', 'natural selection', 'knots')\", "
    "\"understanding\": \"my own understanding of the subject, in the first person -- write as MUCH or as little as the passage genuinely "
    "gives you: a sentence or two if it is simple, several full paragraphs if it is rich and you have a lot to "
    "say. Never pad, but never cut yourself short either\", "
    "\"key_facts\": [\"the specific facts worth keeping -- as MANY as the passage actually holds, each a name, "
    "number, or mechanism\"], "
    "\"thoughts\": \"my own reaction to this, still about the subject\", "
    "\"connects_to\": \"how this links to something I already know or another book, in 1 sentence\", "
    "\"question\": \"what I still wonder or want to know next\"}")

_REVISE_SYS = (
    "/no_think\nYou already wrote a study note on this subject; now you have read MORE about it. DEEPEN your "
    "EXISTING note — integrate the new understanding, sharpen it, fold in new facts and thoughts. Do NOT "
    "merely append or restate; rewrite it as one stronger note. Keep it YOUR understanding, first person, "
    "about the world. Keep every distinct fact from the existing note that is still true, add the new facts, "
    "and merge only true duplicates; key_facts may grow to 12. Output ONLY JSON (same schema): {\"title\": \"...\", \"subject\": \"...\", "
    "\"understanding\": \"...\", \"key_facts\": [\"...\"], \"thoughts\": \"...\", \"connects_to\": \"...\", "
    "\"question\": \"...\"}")


def _clean(s, n: int = 400) -> str:
    return " ".join(str(s or "").split())[:n]


def _norm(d: dict) -> dict:
    kf = d.get("key_facts") or []
    if not isinstance(kf, list):
        kf = [str(kf)]
    return {
        "title":         _clean(d.get("title"), 80) or "Study note",
        "subject":       _clean(d.get("subject"), 40),
        "understanding": _clean(d.get("understanding"), 6000),     # let a rich note run long; never forced short
        "key_facts":     [_clean(f, 300) for f in kf if str(f).strip()][:20],
        "thoughts":      _clean(d.get("thoughts"), 2000),
        "connects_to":   _clean(d.get("connects_to"), 300),
        "question":      _clean(d.get("question"), 300),
    }


_LEX_STOP = {"the", "and", "for", "with", "from", "this", "that", "what", "which", "into", "about",
             "your", "his", "her", "their", "they", "are", "was", "were", "you", "not", "but", "all"}


def _lexical_overlap(a: str, b: str) -> float:
    """Cheap content-word overlap (book_selection.py's proven pattern, reused here 2026-08-19). Cosine
    ALONE is unreliable on this corpus: an empirical check found 200-900 of 1,600 fragments clear a
    0.35 cosine bar against any given note, because his study notes are stylistically homogeneous
    first-person reflective prose — cosine ends up measuring 'sounds like his writing', not 'same idea'.
    Content-word overlap corrects for that; blended with cosine below, not used alone either."""
    wa = {w for w in re.findall(r"[a-z][a-z']{2,}", a.lower()) if w not in _LEX_STOP}
    wb = {w for w in re.findall(r"[a-z][a-z']{2,}", b.lower()) if w not in _LEX_STOP}
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / max(1, min(len(wa), len(wb)))


_FRAG_HEADER = re.compile(r"^\[My study note:[^\]]*\]\s*")


def _whole_item(content: str, limit: int = _RELATED_ITEM_MAX) -> str:
    """D-0592: an item is shown WHOLE. Only one too long for the prompt is shortened, and then on a
    sentence boundary (else a word boundary) with the '[My study note: ... subject: S]' fragment header
    stripped — the old content[:220] cut mid-word and spent ~100 of the 220 characters on that header."""
    text = " ".join((content or "").split())
    if len(text) <= limit:
        return text
    text = _FRAG_HEADER.sub("", text)
    if len(text) <= limit:
        return text
    cut = text[:limit]
    ends = [m.end() for m in re.finditer(r"[.!?][\"')\]]*(?=\s|$)", cut)]
    if ends and ends[-1] >= limit // 3:
        return cut[:ends[-1]].strip()
    return cut.rsplit(" ", 1)[0].rstrip(",;: ")


# J-2919 (P-0072, F-3589): "is this fragment a note on THIS book?" used to be a one-word guess (the longest title
# word as a content LIKE, or the first 16 letters of the title squashed and looked for in the first 400 squashed
# characters). For a title keyed on a common word ("scientific", "experience", "understanding", "world") that
# matched other books' notes: 98 of 763 replayed calls had NO real own note among the matches. It is now decided
# the way essay_lesson.gather_notes decides it: from the fragment's own book tag ("on '<book>'" in the header,
# apostrophes in the title allowed) or, for an old tablet with no such header, from the "on:" line of the note
# FILE its source_id points to, tested with _cites_this_book (the book's WHOLE distinctive-word signature) or
# _tag_is_this_book (title-equal up to the 50-character cut). A row whose book cannot be read at all gives None
# (not True): the related-material scan then falls back to the old coarse prefix test for that row only, so
# nothing the old code excluded is let in.
_NOTE_BOOK_TAG_RE = re.compile(r"\bon '(.*?)' \u00b7 subject:", re.S)
_FILE_ON_RE = re.compile(r"on:\s*(.+?)(?:\s\u00b7\s|\*)")
_FILE_READ_CAP = 60   # old header-less tablets read per lookup (each is a 500-byte file head)


def _note_book_tag(content: str) -> str:
    """The book a study-note fragment says it is on: "[My study note: 'T' . on '<book>' . subject: S]" (the
    book may itself hold apostrophes), else the generic leading-bracket tag (essay / understanding / reading
    fragments). '' when the content carries none."""
    head = (content or "")[:600]
    m = _NOTE_BOOK_TAG_RE.search(head)
    if m:
        return m.group(1).strip()
    try:
        from core.world_consolidation import _tag_of
        return _tag_of(content)
    except Exception:
        return ""


def _file_book_of(source_id) -> str:
    """The book named in the "on: <book>" frontmatter of the note file a fragment's source_id points to ('' when
    there is no readable file). Only used for old header-less tablets."""
    try:
        if not source_id:
            return ""
        p = Path(str(source_id))
        if not p.is_file():
            return ""
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            head = f.read(500)
        m = _FILE_ON_RE.search(head)
        return m.group(1).strip() if m else ""
    except Exception:
        return ""


def _tag_is_book(book_title: str, tag: str) -> bool:
    """Does a book tag (from a fragment header or a note file) name book_title? '' never matches. First the
    strict test (essay_lesson._tag_is_this_book: the same title, equal or cut at the writers' 50 characters).
    Only a title with TWO OR MORE distinctive words may also match by whole-signature citation
    (_cites_this_book) -- a title whose signature is one word ('The World of Ice' -> world, 'About You' ->
    about, 'On War Volume 1' -> none) would otherwise claim every tag that holds that word, the very
    one-word guess this replaces (J-2919 replay: 'On War Volume 1' matched 40 ids, 0 real)."""
    if not tag or not book_title:
        return False
    try:
        from core.essay_lesson import _cites_this_book, _tag_is_this_book, _title_signature
        if _tag_is_this_book(book_title, tag):
            return True
        return len(_title_signature(book_title[:50])) >= 2 and bool(_cites_this_book(book_title[:50], tag.lower()))
    except Exception:
        return False


def _is_own_note(book_title: str, content: str, source_id=None, _file_budget: list | None = None):
    """True / False when the fragment's book could be read and does / does not match book_title; None when the
    fragment names no book at all (an old tablet whose file is also gone). _file_budget=[n] caps file reads."""
    tag = _note_book_tag(content)
    if not tag and source_id and (_file_budget is None or _file_budget[0] > 0):
        if _file_budget is not None:
            _file_budget[0] -= 1
        tag = _file_book_of(source_id)
    if not tag:
        return None
    return _tag_is_book(book_title, tag)


def _own_note_fragment_ids(book_title: str, conn=None, exclude_id: str = "", limit: int = 400) -> list[str]:
    """Fragment ids of THIS book's own study notes, newest first (see the J-2919 note above). Used by the M1
    restate_sim lookup; replaces `content LIKE %<longest title word>%`. Fail-open: [] on any error."""
    out: list[str] = []
    try:
        budget = [_FILE_READ_CAP]

        def _scan(c) -> None:
            for r in c.execute("SELECT fragment_id, content, source_id FROM memory_fragments "
                               "WHERE origin='study' AND fragment_id != ? ORDER BY timestamp DESC LIMIT 4000",
                               (exclude_id or "",)).fetchall():
                if _is_own_note(book_title, r["content"], r["source_id"], budget):
                    out.append(r["fragment_id"])
                    if len(out) >= limit:
                        break
        if conn is not None:
            _scan(conn)
        else:
            from core.memory.store import _connect
            with _connect() as c:
                _scan(c)
    except Exception:
        pass
    return out


def _scored_scan_related(book_title: str, passage: str) -> tuple[str, list[str]]:
    """D-0592 (P-0072, F-3589): PASSAGE-level related material from OTHER sources — a bounded scan scored
    on cosine of THIS passage BLENDED with lexical overlap (not cosine alone — see _lexical_overlap's
    docstring for why). Replaces the book-level relates_to walk, which handed every passage of a book the
    same three items. An item must also share at least one content word with the passage, so nothing is
    offered on 'sounds like his writing' alone; when nothing qualifies the section is simply absent from
    the prompt. The top _RELATED_MAX are shown whole (see _whole_item). Returns (text, fragment_ids)."""
    try:
        from core.memory.store import _connect, _embed, _cosine, _blob_to_vec
        qv = _embed(passage[:1200])
        if qv is None:
            return "", []
        key = "".join(ch for ch in book_title.lower() if ch.isalnum())[:16]
        _file_budget = [_FILE_READ_CAP]
        scored = []
        with _connect() as conn:
            for r in conn.execute(
                    "SELECT fragment_id, content, embedding, source_id FROM memory_fragments WHERE origin IN "
                    "('study', 'essay') AND embedding IS NOT NULL ORDER BY timestamp DESC LIMIT 800").fetchall():
                content = r["content"] or ""
                # J-2919 (F-3589): exclude this SAME book's own material — that's not "another source" — by the
                # fragment's own book tag (whole-signature test), not a squashed 16-letter title prefix. Only a
                # row that names no book at all falls back to the old coarse prefix test.
                own = _is_own_note(book_title, content, r["source_id"], _file_budget)
                if own is None:
                    own = bool(key and key in "".join(ch for ch in content.lower() if ch.isalnum())[:400])
                if own:
                    continue
                v = _blob_to_vec(r["embedding"])
                if v is None:
                    continue
                cos = _cosine(qv, v)
                if cos <= _RELATED_SIM:
                    continue
                lex = _lexical_overlap(passage, content)
                if lex <= 0:
                    continue    # no shared content word with the passage: not related to it
                scored.append((0.6 * cos + 0.4 * lex, content, r["fragment_id"]))
        scored.sort(reverse=True, key=lambda x: x[0])
        picked = scored[:_RELATED_MAX]
        return "\n".join(f"- {_whole_item(c)}" for _, c, _fid in picked), [fid for _, _, fid in picked]
    except Exception:
        return "", []


def _related_context(book_title: str, passage: str) -> tuple[str, list[str]]:
    """Bounded, zero-extra-LLM-cost lookup of genuinely related material from OTHER sources (study notes
    and essays on a DIFFERENT book), so 'connects_to' can be grounded in his real scholarship rather than
    invented. D-0592: scored on THIS passage every time (no book-level graph walk). Best-effort, silent on
    failure. Returns (text, fragment_ids) — the ids are what 'was recalled into this note' for the M1
    co-recall ledger (docs/plans/memory_multiway_linking.md)."""
    try:
        return _scored_scan_related(book_title, passage)
    except Exception:
        return "", []


async def compose_note(call_json, base_urls, book_title: str, passage: str,
                       related_text: str = "") -> dict | None:
    try:
        user = f"The passage(s), from '{book_title}':\n{(passage or '')[:5000]}"
        if related_text:
            user += f"\n\nRelated material from elsewhere in your scholarship (use ONLY if it genuinely fits):\n{related_text}"
        d = await call_json(base_urls, _NOTE_SYS, user,
                            max_tokens=1500, temperature=0.5)   # room for a long note if the passage warrants it
        if not d or not str(d.get("understanding") or "").strip():
            return None
        return _norm(d)
    except Exception:
        return None


def _read_note_file(fp) -> dict:
    """J-2961 (F-3653): what a note's FILE carries that its DB fragment text does not (F-3611: the fragment omits
    connects_to and question) -- those two fields, plus the frontmatter's pass / sittings / chars so a revise can
    record existing + new rather than the new session only. Pure read, fail-open: {} when there is no file."""
    out: dict = {}
    try:
        if not fp or not Path(fp).exists():
            return out
        txt = Path(fp).read_text(encoding="utf-8", errors="replace")
        head = txt[:800]
        m = re.search(r"sittings:\s*(\d+)", head)
        if m:
            out["sittings"] = int(m.group(1))
            out["est"] = "(est.)" in head[m.end():m.end() + 12]
        m = re.search(r"chars:\s*(\d+)", head)
        if m:
            out["chars"] = int(m.group(1))
        m = re.search(r"pass:\s*(\d+)", head)
        if m:
            out["pass"] = int(m.group(1))
        m = re.search(r"^\*\*Connects to:\*\*\s*(.+)$", txt, re.M)
        if m:
            out["connects_to"] = m.group(1).strip()
        m = re.search(r"^\*\*Still wondering:\*\*\s*(.+)$", txt, re.M)
        if m:
            out["question"] = m.group(1).strip()
    except Exception:
        pass
    return out


def _revise_prompt(existing_body: str, new_note: dict, existing_extra: dict | None = None) -> str:
    """The user half of the revise call (J-2961, F-3653): the existing note whole (cut only at a boundary, and only
    above _REVISE_EXISTING_MAX) with ITS connects_to / question when its file was found, then the new reading's
    understanding, facts, thoughts, connects_to and question -- nothing of the new reading is dropped any more."""
    body = existing_body or ""
    if len(body) > _REVISE_EXISTING_MAX:
        body = body[:_cut_point(body, 0, _REVISE_EXISTING_MAX)]
    ex = existing_extra or {}
    parts = [f"MY EXISTING NOTE:\n{body}"]
    if ex.get("connects_to"):
        parts.append(f"Connects to: {ex['connects_to']}")
    if ex.get("question"):
        parts.append(f"Still wondering: {ex['question']}")
    new = [f"\nWHAT I JUST READ (on {new_note['subject']}):\n{new_note['understanding']}"]
    if new_note.get("key_facts"):
        new.append("Facts: " + "; ".join(new_note["key_facts"]))
    if new_note.get("thoughts"):
        new.append(f"Thoughts: {new_note['thoughts']}")
    if new_note.get("connects_to"):
        new.append(f"Connects to: {new_note['connects_to']}")
    if new_note.get("question"):
        new.append(f"Still wondering: {new_note['question']}")
    return "\n".join(parts) + "\n" + "\n".join(new)


async def _revise(call_json, base_urls, existing_body: str, new_note: dict,
                  existing_extra: dict | None = None) -> dict | None:
    try:
        d = await call_json(base_urls, _REVISE_SYS, _revise_prompt(existing_body, new_note, existing_extra),
                            max_tokens=1500, temperature=0.45)   # a deepened note may run longer too
        if not d or not str(d.get("understanding") or "").strip():
            return None
        return _norm(d)
    except Exception:
        return None


def _render_body(note: dict) -> str:
    out = [note["understanding"]]
    if note["key_facts"]:
        out.append("\n**What I learned:**\n" + "\n".join(f"- {f}" for f in note["key_facts"]))
    if note.get("thoughts"):
        out.append(f"\n**My thoughts:** {note['thoughts']}")
    if note["connects_to"]:
        out.append(f"\n**Connects to:** {note['connects_to']}")
    if note["question"]:
        out.append(f"\n**Still wondering:** {note['question']}")
    return "\n".join(out)


def _fragment_content(note: dict, book_title: str) -> str:
    """DB fragment text — CARRIES the book and subject (so content-LIKE finds it, which old notes broke) and
    leads with his understanding, not a 'The passage' stem."""
    facts = ("  Facts: " + "; ".join(note["key_facts"])) if note["key_facts"] else ""
    thoughts = (f"  Thoughts: {note['thoughts']}") if note.get("thoughts") else ""
    return (f"[My study note: '{note['title']}' · on '{book_title[:50]}' · subject: {note['subject']}] "
            f"{note['understanding']}{facts}{thoughts}")


def _slug(title: str) -> str:
    return re.sub(r"[^\w\- ]", "", title)[:48].strip().replace(" ", "_") or "note"


def find_revisable(note: dict, book_pass: int | None = None) -> tuple | None:
    """A near-duplicate existing study note on the same subject → (fragment_id, content, file_path) to revise,
    or None. Cosine on subject+understanding, gated HIGH so only genuine duplicates revise, not merely related
    notes (those get a link instead). The SQL searches only notes NOT yet filed into a chapter
    (chapter_id IS NULL) — a chapter-filed note is never a candidate, wherever its file now sits (the
    docstring used to say it also searched already-filed notes; it never did: P-0072/P-0073, F-3653).
    `book_pass` = the new session's pass (reread number, 0 = first read): a candidate from a LOWER pass is
    skipped — a revision never crosses a pass boundary (D-0581), so a reread is stored as its own new
    pass-tagged note and the earlier reading survives for core/essay_lesson.gather_notes' comparison section.
    A NULL source_pass reads as pass 0 (gather_notes' default). book_pass=None (no session) = no boundary known,
    so nothing is skipped (the pre-D-0581 behaviour)."""
    try:
        from core.memory.store import _connect, _embed, _cosine, _blob_to_vec
        qv = _embed((note["subject"] + ". " + note["understanding"]).strip())
        if qv is None:
            return None
        best, best_sim = None, _REVISE_SIM
        with _connect() as conn:
            for r in conn.execute(
                    "SELECT fragment_id, content, embedding, source_id, source_pass FROM memory_fragments "
                    "WHERE origin='study' AND embedding IS NOT NULL AND chapter_id IS NULL "
                    "ORDER BY timestamp DESC LIMIT 400").fetchall():
                if book_pass is not None and int(r["source_pass"] or 0) < int(book_pass):
                    continue   # D-0581: an earlier reading's note is never revised by a reread
                v = _blob_to_vec(r["embedding"])
                if v is None:
                    continue
                s = _cosine(qv, v)
                if s > best_sim:
                    best_sim, best = s, (r["fragment_id"], r["content"], r["source_id"])
        if not best:
            return None
        fid, content, src = best
        fp = _locate_file(src, content)
        return (fid, content, fp)
    except Exception:
        return None


def _locate_file(source_id, content: str) -> Path | None:
    """Find a note's file — by source_id (new notes store the path) or, for legacy notes, by its title slug."""
    try:
        if source_id and Path(source_id).exists():
            return Path(source_id)
        m = re.search(r"study note: '([^']+)'", content or "")
        if m:
            slug = _slug(m.group(1))
            for d in (STUDY_DIR, *( [p for p in NOTES_SUBDIR.glob("*")] if NOTES_SUBDIR.exists() else [] )):
                for p in d.glob(f"TAB_*_{slug}.md"):
                    return p
    except Exception:
        pass
    return None


def _link_related(fragment_id: str, note: dict) -> int:
    """Concept linking (Zettelkasten): add 'relates_to' edges to the most-similar OTHER notes (above the link
    gate, below the revise gate). Builds the graph the essay-gather / recall traverse."""
    n = 0
    try:
        from core.memory.store import _connect, _embed, _cosine, _blob_to_vec
        qv = _embed((note["subject"] + ". " + note["understanding"]).strip())
        if qv is None:
            return 0
        with _connect() as conn:
            scored = []
            for r in conn.execute(
                    "SELECT fragment_id, embedding FROM memory_fragments WHERE origin='study' "
                    "AND embedding IS NOT NULL AND fragment_id != ? ORDER BY timestamp DESC LIMIT 400",
                    (fragment_id,)).fetchall():
                v = _blob_to_vec(r["embedding"])
                if v is None:
                    continue
                s = _cosine(qv, v)
                if _LINK_SIM < s < _REVISE_SIM:
                    scored.append((s, r["fragment_id"]))
            scored.sort(reverse=True)
            now = time.time()
            for s, other in scored[:3]:          # up to 3 strongest related notes
                conn.execute("INSERT OR IGNORE INTO memory_links (parent_id, child_id, link_type, weight, "
                             "created) VALUES (?,?,?,?,?)", (fragment_id, other, "relates_to", round(s, 3), now))
                n += 1
            if n:
                conn.commit()
    except Exception:
        pass
    return n


def _diegetic_learn(note: dict, body: str) -> None:
    """The diegetic channels a note's text feeds (sound / garden / wood / shore / creature knowledge): his own
    scholarship can teach a call, a plant, a creature. Fail-open; a NonLiveWriteError (D-0179, F-1024) is re-raised
    so it reaches store_note()'s caller. Moved out of store_note's new-note branch unchanged in J-2961 so the
    revise branch runs the same hooks (F-3653 defect 4)."""
    try:
        from core import sound_knowledge as _sk
        _learned = _sk.learn_from_text(f"{note.get('title','')} {body}")
        try:   # GARDEN KNOWLEDGE (2026-08-22): a book can name a plant, the tree, the bushes — the diegetic channel
            from core import garden_knowledge as _gk, garden_life as _gl
            _gk.learn_from_text(f"{note.get('title','')} {body}"); _gl.learn_from_text(f"{note.get('title','')} {body}")
            from core import wood_life as _wl
            _wl.learn_from_text(f"{note.get('title','')} {body}")
            from core import shore_life as _shl
            _shl.learn_from_text(f"{note.get('title','')} {body}")
            from core import life as _life   # THE LIVING WORLD (2026-09-02, D-0129): a book can name a creature he has seen
            _life.learn_from_text(f"{note.get('title','')} {body}")
        except profile.NonLiveWriteError:
            # J-0770: let D-0179's hard-raise (guard_path(), F-1024) reach this function's own
            # caller, rather than this pre-existing broad except swallowing it one layer up.
            raise
        except Exception:
            pass
        if _learned:
            logger.info("[study] his reading taught him a sound: %s", _learned)
    except profile.NonLiveWriteError:
        # J-0770: same -- this outer wrapper (guards sound_knowledge.learn_from_text() above)
        # would otherwise swallow a raise the inner try/except above already re-raised.
        raise
    except Exception:
        pass


def store_note(note: dict, book_title: str, revise_target: tuple | None = None,
               session: list[dict] | None = None, prior: dict | None = None) -> dict:
    """Write the note file + fragment + concept links. If revise_target=(fid, content, path), DEEPEN that note
    in place (rewrite its file, update its fragment) instead of creating a duplicate. `session` = the sittings
    this note covers (from core.reading.pop_session_encounters()) — tags the fragment with the PASS (reread
    number) and the first sitting's encounter_id, and records the full sitting list in the file frontmatter,
    so a book-study capstone can later tell this read-through's notes from an earlier one's. `prior` (revise only, J-2961 / F-3653 defect 4) =
    _read_note_file(old file) plus 'known_ids' (encounter_ids already counted in it): the revised file's
    frontmatter then records the old sittings/chars PLUS the new ones, not the new session alone. Returns a summary."""
    res = {"action": "new", "path": "", "fragment_id": "", "linked": 0}
    try:
        from core.memory.store import store_fragment, _connect
        from core import mood as _mood
        body = _render_body(note)
        ts = time.strftime("%Y%m%d_%H%M")
        frag = _fragment_content(note, book_title)
        session = session or []
        book_pass = session[0]["pass"] if session else None
        enc_id = session[0]["encounter_id"] if session else None
        # D-0577: for a chunked session `session` is only the sittings THIS note's model call saw (each entry
        # carries seen_chars = the characters of that sitting inside the chunk; seen_est marks spans that had
        # to be estimated), so "sittings: N" is what reached the prompt, no longer the whole stretch's count.
        _seen = sum(int(x.get("seen_chars") or 0) for x in session)
        sittings_line = ((f" · pass: {book_pass} · sittings: {len(session)}"
                          + (" (est.)" if any(x.get("seen_est") for x in session) else "")
                          + (f" · chars: {_seen}" if _seen else "")) if session else "")
        if revise_target and prior is not None:
            # J-2961 (F-3653 defect 4): a revise records the old file's sittings and chars PLUS the new session's,
            # counting a sitting once (known_ids = those already counted in the old file, e.g. an earlier chunk of
            # this same session); characters add (a later chunk saw a different part of the same sitting).
            _known = set(prior.get("known_ids") or ())
            _new_n = sum(1 for x in session if not x.get("encounter_id") or x.get("encounter_id") not in _known)
            _tot_n = int(prior.get("sittings") or 0) + _new_n
            _tot_c = int(prior.get("chars") or 0) + _seen
            _est = bool(prior.get("est")) or any(x.get("seen_est") for x in session)
            _pass = book_pass if session else prior.get("pass")
            if _tot_n and _pass is not None:
                sittings_line = (f" · pass: {_pass} · sittings: {_tot_n}" + (" (est.)" if _est else "")
                                 + (f" · chars: {_tot_c}" if _tot_c else ""))
        if revise_target:
            fid, _old, fp = revise_target
            # rewrite the file in place (keep its name) if we found it, else write a fresh one
            if fp and Path(fp).exists():
                Path(fp).write_text(
                    f"# {note['title']}\n\n*A study note by 渡 · {time.strftime('%Y-%m-%d %H:%M')} · "
                    f"on: {book_title} · subject: {note['subject']} · revised{sittings_line}*\n\n" + body + "\n",
                    encoding="utf-8")
                res["path"] = str(fp)
            # update the existing fragment's content in place (keep its id, links, provenance)
            try:
                # J-2961 (F-3653 defect 4 / F-3649): the revised text gets a fresh embedding too -- the old vector
                # was left standing for the old text, so the note kept being found (and deduped) by what it used
                # to say. Fail-open: no embedding -> the content update runs as before.
                _vec = _blob = None
                try:
                    from core.memory.store import _embed, _vec_to_blob
                    _vec = _embed(frag)
                    _blob = _vec_to_blob(_vec) if _vec is not None else None
                except Exception:
                    _blob = None
                with _connect() as conn:
                    # J-3395 / F-4019: re-stamp content_hash with the revised note text (same statement); only
                    # where the J-3266 column exists.
                    _sets, _args = ["content=?"], [frag]
                    if _has_hash_column(conn):
                        _sets.append("content_hash=?")
                        _args.append(_content_hash(frag))
                    if _blob is not None:
                        _sets.append("embedding=?")
                        _args.append(_blob)
                    conn.execute(f"UPDATE memory_fragments SET {', '.join(_sets)} WHERE fragment_id=?",
                                 (*_args, fid))
                    conn.commit()
            except Exception:
                pass
            res.update(action="revised", fragment_id=fid)
            res["linked"] = _link_related(fid, note)
            _diegetic_learn(note, body)   # J-2961: the same diegetic hooks a new note runs (F-3653 defect 4)
            return res
        # NEW note
        STUDY_DIR.mkdir(parents=True, exist_ok=True)
        path = STUDY_DIR / f"TAB_{ts}_{_slug(note['title'])}.md"
        path.write_text(
            f"# {note['title']}\n\n*A study note by 渡 · {time.strftime('%Y-%m-%d %H:%M')} · "
            f"on: {book_title} · subject: {note['subject']}{sittings_line}*\n\n" + body + "\n", encoding="utf-8")
        fid = store_fragment(
            content=frag, layer="episodic", relevance=0.85, importance=0.85,
            keywords=["study", (note["subject"] or "")[:40], book_title.lower()[:40]],
            origin="study", emotion_embedding=_mood.current_vec(),
            valence=_mood.current_valence(), felt=_mood.current_felt(),
            source_type="study_note", source_id=str(path),
            encounter_id=enc_id, source_pass=book_pass)
        res.update(path=str(path), fragment_id=fid)
        res["linked"] = _link_related(fid, note)
        # EPISTEMIC AUDITION BOOK-BINDING (2026-08-15): his own scholarship can teach a call — a study
        # note tying a bird's name to its sound learns the association (the diegetic channel). Fail-open.
        # (The hooks live in _diegetic_learn since J-2961 so the revise branch runs them too.)
        _diegetic_learn(note, body)
        return res
    except profile.NonLiveWriteError:
        # J-0770: same again, one layer further up — store_note()'s own function-level catch-all
        # is the last thing standing between the six learn_from_text() calls and write_or_revise()'s
        # caller; without this, the two fixes above are a no-op end to end.
        raise
    except Exception:
        return res


def _log_m1_co_recall(book_title: str, note: dict, related_ids: list[str], new_fid: str) -> None:
    """Feed the M1 co-recall shadow ledger (docs/plans/memory_multiway_linking.md, core/memory_edges.py)
    from the reading/study path. Previously log_co_recall() was only ever called from the main monologue
    train — reading material was entirely outside the evidence base that will eventually decide whether
    edge-aware retrieval beats plain cosine (M2's kill criterion). This does not read or act on the
    ledger, and does not touch the live retrieval path — pure additive logging, same as the main train's
    own call. restate_sim mirrors the main train's exact semantics: cosine to the immediately PRIOR
    thought in this thread — here, this book's own most recent prior note (NOT the related material
    itself, which is what `related_ids` records as the co-recalled set). ids=[] is still logged when
    nothing was recalled ("coverage is part of the instrument" — memory_edges.log_co_recall's own law)."""
    try:
        from core.memory.store import _connect, _embed, _cosine, _blob_to_vec
        from core import memory_edges as _medges
        restate_sim = None
        qv = _embed((note.get("subject", "") + ". " + note.get("understanding", "")).strip())
        if qv is not None:
            # J-2919 (F-3589): this book's most recent prior note, found by its own book tag
            # (_own_note_fragment_ids), no longer by a one-word content LIKE that picked other books' notes.
            with _connect() as conn:
                own_ids = _own_note_fragment_ids(book_title, conn, exclude_id=new_fid or "", limit=1)
                row = (conn.execute("SELECT embedding FROM memory_fragments WHERE fragment_id=?",
                                    (own_ids[0],)).fetchone() if own_ids else None)
                if row:
                    pv = _blob_to_vec(row["embedding"])
                    if pv is not None:
                        restate_sim = round(_cosine(qv, pv), 3)
        _medges.log_co_recall(related_ids or [], restate_sim, 0, source="study_note")
    except Exception:
        pass


def _cut_point(text: str, pos: int, hard: int) -> int:
    """Where to end a chunk that starts at `pos` and may run no further than `hard` (D-0577): the last
    sentence end in the second half of the window, else the last whitespace, else `hard` itself (a run of
    characters with no space at all). Never inside a word: the character after the cut is always whitespace
    (or the cut is the text's end)."""
    window = text[pos:hard + 1]            # +1 so the lookahead sees the character after `hard`
    ends = [m.end() for m in re.finditer(r"[.!?][\"')\]]*(?=\s)", window)]
    ends = [e for e in ends if e <= hard - pos]
    if ends and ends[-1] >= (hard - pos) // 2:
        return pos + ends[-1]
    ws = [m.start() for m in re.finditer(r"\s", window)]
    ws = [w for w in ws if 0 < w <= hard - pos]
    return pos + ws[-1] if ws else hard


def _chunk_session(passage: str, limit: int = _CHUNK_CHARS) -> list[tuple[int, int]]:
    """D-0577: (start, end) character spans of the chunks a session is composed from. A passage of at most
    `limit` characters is ONE chunk (unchanged behaviour). A longer one is split into ceil(len/limit) chunks
    of near-equal size, each ending on a sentence boundary (else a word boundary), each at most `limit`: the
    target is re-balanced over the remaining text after every cut, so no tiny tail chunk is left over."""
    n = len(passage)
    spans, pos = [], 0
    while n - pos > limit:
        left = -(-(n - pos) // limit)                      # chunks still needed (ceil)
        cut = _cut_point(passage, pos, pos + (n - pos) // left)
        spans.append((pos, cut))
        pos = cut
        while pos < n and passage[pos].isspace():
            pos += 1
    spans.append((pos, n))
    return spans


def _pick_chunks(total: int, cap: int) -> list[int]:
    """Which chunk indices get a note: all of them up to `cap`; past it, `cap` indices spread evenly from the
    first to the last chunk (so a 24-chunk stream is sampled across its length, not just its start)."""
    if total <= cap:
        return list(range(total))
    if cap <= 1:
        return [0]
    return sorted({round(i * (total - 1) / (cap - 1)) for i in range(cap)})


def _sitting_spans(passage: str, session: list[dict]) -> tuple[list[tuple[int, int]], bool]:
    """Where each sitting lies in `passage` (the callers join sittings with ONE separator character, so the
    spans are exact when each entry's 'chars' (core.reading, D-0577) adds up to the passage). Returns
    (spans, exact). When it does not add up (an entry without 'chars', or earlier unpopped sittings in the
    list) the sittings are laid out evenly and exact=False, so the frontmatter says '(est.)'."""
    n, k = len(passage), len(session)
    chars = [x.get("chars") for x in session]
    if all(isinstance(c, int) and c > 0 for c in chars) and sum(chars) + k - 1 == n:
        spans, pos = [], 0
        for c in chars:
            spans.append((pos, pos + c))
            pos += c + 1
        return spans, True
    return [(i * n // k, (i + 1) * n // k) for i in range(k)], False


def _sub_session(session: list[dict], sspans: list[tuple[int, int]], exact: bool, a: int, b: int) -> list[dict]:
    """The sittings that overlap chunk [a, b), as copies carrying seen_chars (store_note reads it)."""
    out = []
    for x, (sa, sb) in zip(session, sspans):
        ov = min(sb, b) - max(sa, a)
        if ov > 0:
            out.append(dict(x, seen_chars=ov, seen_est=not exact))
    return out or [dict(session[0], seen_chars=0, seen_est=True)]


def _merge_sessions(old: list[dict], new: list[dict]) -> list[dict]:
    """Sittings seen by one note after a same-call revision folds a second chunk into it: union by
    encounter_id, the characters summed for a sitting both chunks touched."""
    merged = {}
    for x in list(old) + list(new):
        eid = x.get("encounter_id")
        if eid in merged:
            merged[eid]["seen_chars"] = int(merged[eid].get("seen_chars") or 0) + int(x.get("seen_chars") or 0)
            merged[eid]["seen_est"] = bool(merged[eid].get("seen_est") or x.get("seen_est"))
        else:
            merged[eid] = dict(x)
    return list(merged.values())


async def _write_one(call_json, base_urls, book_title: str, passage: str, session: list[dict] | None,
                     merged: dict | None = None) -> dict:
    """One note from one chunk: compose, dedup against same-pass notes (revise) or store new + link.
    `merged` (chunked sessions only) maps fragment_id -> the sittings that note has seen in THIS call, so a
    chunk that revises an earlier chunk's note keeps the frontmatter honest about both."""
    related_text, related_ids = _related_context(book_title, passage)
    note = await compose_note(call_json, base_urls, book_title, passage, related_text=related_text)
    if not note:
        return {}
    # D-0581: a revision never crosses a pass boundary -- an earlier pass's note is not a candidate, so a
    # reread lands as a new pass-tagged note (same-pass revision is unchanged).
    book_pass = session[0]["pass"] if session else None
    target = find_revisable(note, book_pass=book_pass)
    deepened = None
    if target:
        # J-2961 (F-3653): the old note's connects_to / question live only in its FILE (the fragment text omits
        # them); the same read gives the old sittings / chars the revised frontmatter must keep.
        _prior = _read_note_file(target[2])
        deepened = await _revise(call_json, base_urls, target[1], note, existing_extra=_prior)
        if deepened is None:
            # J-2961 (F-3653 defect 3): a failed revise used to fall back to `note` AS the revise result, which
            # overwrote the old note's file and fragment wholesale and logged "revised". Now the old note is left
            # exactly as it is and the new note is stored as its own.
            logger.info("[study_note] revise of %s failed (no usable reply); old note left untouched, "
                        "new note stored as its own (J-2961)", str(target[0])[:8])
    if target and deepened is not None:
        seen = (_merge_sessions(merged[target[0]], session)
                if (merged is not None and session and target[0] in merged) else session)
        _known = {x.get("encounter_id") for x in merged[target[0]]} if (merged is not None and target[0] in merged) else set()
        _prior = dict(_prior, known_ids=_known)
        out = store_note(deepened, book_title, revise_target=target, session=session, prior=_prior)
        out["note"] = deepened
    else:
        seen = session
        out = store_note(note, book_title, session=session)
        out["note"] = note
        # THE FOLLOW LINE (J-2459, docs/staged/question_cargo.md §2.1): the note's CLAIM -- its first sentence
        # ("I see that ...") -- boards the line, new notes only. These are the hypotheses that died at birth
        # (F-3166: study-born frontier questions 44 born / 44 faded / 0 resolved). The note itself is unchanged.
        try:
            from core import follow_line as _fl
            _claim = _first_sentence(note.get("understanding", ""))
            if _claim:
                _ent = _fl.board(_claim, "claim", kind="claim", about=(note.get("subject") or "")[:60],
                                 asked_by={"book_title": book_title[:80], "fragment_id": out.get("fragment_id", ""),
                                           "pass": session[0]["pass"] if session else None, "ts": time.time()},
                                 allow_self=True)
                if _ent:
                    _fl.fire(_ent.get("id", ""))
        except profile.NonLiveWriteError:
            raise
        except Exception as _exc_fl:
            logger.debug("[study_note] follow_line claim boarding failed (non-fatal): %s", _exc_fl)
    if merged is not None and session and out.get("fragment_id"):
        merged[out["fragment_id"]] = seen
    try:
        _log_m1_co_recall(book_title, out["note"], related_ids, out.get("fragment_id", ""))
    except Exception:
        pass
    return out


def _log_chunking(row: dict) -> None:
    """D-0577: one row per study session -- how much of what he read the model saw, how many notes it became,
    whether the per-session cap bit. Reader: the two-week D-0577 verification (median share seen, notes per
    week, cap-bite rate), the follow-up job spawned from J-3190. Fail-open; fenced like every other data/ writer."""
    try:
        with open(profile.guard_path(_CHUNK_LOG), "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _front_matter_skip(text: str) -> str:
    """J-2921 (F-3605, P-0072): '' if `text` is to be composed into a note, else the reason it is not -- a table of
    contents / front matter / page-number list, from which compose_note would write a confident first-person note out
    of chapter TITLES plus the model's own pretraining (On War offset 0; Friedrich II offset 41655). The detector is
    core.reading.front_matter_reason (the sibling of _is_end_matter); the sitting itself is untouched -- read_next_sitting
    already stored it and he has read it -- only the NOTE is withheld. Fail-open: an import or detector error means
    'write the note', exactly as before."""
    if not FRONT_MATTER_GUARD:
        return ""
    try:
        from core import reading as _reading
        return _reading.front_matter_reason(text) or ""
    except Exception:
        return ""


async def write_or_revise(call_json, base_urls, book_title: str, passage: str,
                          session: list[dict] | None = None) -> dict:
    """The single entry point for a SESSION study note (fired once per reading session — a run of sittings
    integrated together — as soon as it finishes). Compose a rich first-person note from the passage; if it
    duplicates an existing note FROM THE SAME PASS, DEEPEN that one; else (incl. a reread of an earlier pass's
    passage, D-0581) store it new + link it. `session` (optional) =
    core.reading.pop_session_encounters()'s return — tags the note with which sittings/pass it covers.
    D-0577: a session longer than ~5000 characters becomes one note PER CHUNK (see _chunk_session), at most
    _MAX_NOTES_PER_SESSION of them. Returns {note, action, path, linked} (empty on failure) -- for a chunked
    session that is the LAST chunk's result, plus 'notes' (every chunk's result), 'chunks_total', 'chunks_made'
    and 'capped'.
    J-2921 (F-3605): a chunk that is a table of contents / front matter / page-number list (core.reading.front_matter_reason)
    gets NO note -- the sitting is already stored and read, only the confabulated note is withheld; if every chunk is
    withheld the result is {} (callers already treat that as 'no note'). The skip count and reasons are in the
    chunking log row (front_matter_skipped / front_matter_reasons)."""
    passage = passage or ""
    spans = _chunk_session(passage)
    chosen = _pick_chunks(len(spans), _MAX_NOTES_PER_SESSION)
    capped = len(chosen) < len(spans)
    outs: list[dict] = []
    seen_chars = 0
    fm_skipped: list[str] = []   # J-2921: the reason of every chunk withheld as contents / front matter
    if len(spans) == 1:
        _fm = _front_matter_skip(passage)
        if _fm:
            fm_skipped.append(_fm)
        else:
            out = await _write_one(call_json, base_urls, book_title, passage, session)
            if out:
                outs.append(out)
                seen_chars = len(passage)
    else:
        sspans, exact = _sitting_spans(passage, session) if session else ([], True)
        merged: dict = {}
        for idx in chosen:
            a, b = spans[idx]
            _fm = _front_matter_skip(passage[a:b])
            if _fm:
                fm_skipped.append(_fm)
                continue
            sub = _sub_session(session, sspans, exact, a, b) if session else None
            out = await _write_one(call_json, base_urls, book_title, passage[a:b].strip(), sub, merged)
            if out:
                outs.append(out)
                seen_chars += b - a
    if fm_skipped:
        logger.info("[study_note] '%s': %d of %d chunk(s) are contents / front matter (%s) -- no note written (J-2921)",
                    book_title[:50], len(fm_skipped), len(chosen), ",".join(fm_skipped))
    if capped:
        logger.info("[study_note] session of %d chars (%d chunks) capped at %d notes (chunks %s)",
                    len(passage), len(spans), _MAX_NOTES_PER_SESSION, chosen)
    _log_chunking({"ts": time.time(), "book": book_title[:60], "chars": len(passage),
                   "sittings": len(session) if session else None, "chunks_total": len(spans),
                   "chunks_chosen": len(chosen), "notes": len(outs), "capped": capped,
                   "new": sum(1 for o in outs if o.get("action") == "new"),
                   "revised": sum(1 for o in outs if o.get("action") == "revised"),
                   "seen_chars": seen_chars,
                   "seen_share": round(seen_chars / len(passage), 3) if passage else None,
                   "front_matter_skipped": len(fm_skipped), "front_matter_reasons": fm_skipped})
    if not outs:
        return {}
    if len(spans) == 1:
        return outs[0]
    res = dict(outs[-1])
    res.update(notes=outs, chunks_total=len(spans), chunks_made=len(outs), capped=capped)
    return res


def _first_sentence(text: str) -> str:
    """The claim a study note makes: its first sentence of `understanding`, 20-220 chars, else ''."""
    try:
        t = " ".join((text or "").split())
        m = re.match(r"(.+?[.!?])(\s|$)", t)
        s = (m.group(1) if m else t).strip()
        return s[:220] if len(s) >= 20 else ""
    except Exception:
        return ""
