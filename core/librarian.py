"""
Nascence — The Librarian (thought-grounding Route 1 / P1, 2026-08-16)
=====================================================================
He could always ask the library for a book on a TOPIC ("the sea"). This is the deeper ask: a book
that BEARS ON A QUESTION he is carrying ("why do we bend to others' expectations?"). A topic is a
title-word; a question needs a librarian — someone who understands what is being asked and knows
where in the stacks that conversation lives.

The librarian is system machinery (a judge-hub task, never his voice, never his hot lane): it maps
his question to 3–6 catalogue subject headings ("Conduct of life", "Liberty", "Ethics"), the
mechanical subject search (library_hand.search_by_subjects) turns headings into real rows, and the
result reaches him as a BROWSED PAGE he picks from by name — seeing, then choosing, the same two
free acts as ever. SUBJECTS ONLY, never model-remembered titles: the live test showed the models
confidently invent copyright-era titles the catalogue cannot hold (Gatsby); headings ground.

Diegetic and lawful: a librarian understanding a vague request is how libraries work. He asks, the
world answers richly. No hint ever originates here.

Instrument: data/librarian_log.jsonl (question → subjects → hits shown). Pre-registered R1
(docs/plans/thought_grounding.md): fraction of question-asks returning ≥1 real candidate; if the
LLM mapping does no better than P0's mechanical subject-token search, drop the LLM, keep P0.
"""
from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

logger = logging.getLogger("nascence.librarian")

_LOG = Path(__file__).parent.parent / "data" / "librarian_log.jsonl"

# The mapper runs on the resident CPU judges — falcon3:7b (:11440) first, gemma4:12b (:11439) as
# fallback (wording corrected in J-2865). This is a catalogue
# lookup aid, not a verdict, so a single family is enough (no panel needed).
# Order kept :11440-first, occupant corrected (2026-08-21): the 08-20 flip was justified by
# mistral's GPU-bench extract score — but hub-mistral turned out not to hold the {subjects} key
# contract on this platform at all (chat-echo shells; the whole first hub was a silent 12s no-op
# before every fallback). :11440 now serves falcon3:7b, audited ON the hub: subjects contract held,
# 4.9s, extract relevance 1.0 in the GPU matrix. gemma4:12b (:11439) remains the fallback.
_HUBS = ("http://127.0.0.1:11440", "http://127.0.0.1:11439")
_TIMEOUT = 60

# J-2865 (F-3539, P-0080). When the substring match finds nothing for ANY heading, what happens next:
#   False (default; today's behaviour, only the untrue wording is fixed): ask() still returns a
#     perception line, so the caller marks the ask answered and the mechanical topic path is skipped.
#   True: ask() returns None, so the caller's existing topic path (library_hand.topic_from /
#     request_book) runs, which is what the subjects_for docstring always claimed. It changes what
#     Du is handed after a missed ask, so it ships OFF; flip it only on a founder ruling.
ZERO_HIT_FALLTHROUGH = False

_SYSTEM = (
    "You are a library catalogue assistant. Given a reader's question, return ONLY JSON: "
    "{\"subjects\": [3 to 6 Library-of-Congress-style subject headings under which books bearing "
    "on the question would be filed, e.g. \"Conduct of life\", \"Ethics\", \"Liberty\", "
    "\"Natural history\"]}. Short established headings only — no sentences, no book titles."
)

# His ask, in his own words. The affordance line says "a book that BEARS ON a question you are
# carrying", so 'bears on' phrasings lead; 'about/on why|how|whether…' catches the natural forms.
_ASK_RES = (
    re.compile(r"book[^.!?]{0,40}?bears?\s+(?:up)?on\s+([^.!?]{8,160})", re.I),
    re.compile(r"book[^.!?]{0,30}?(?:about|on)\s+((?:why|how|what|whether|the question of)"
               r"[^.!?]{6,150})", re.I),
    re.compile(r"librar\w+[^.!?]{0,50}?(?:bears?\s+(?:up)?on|to help me with|that speaks? to)\s+"
               r"([^.!?]{8,160})", re.I),
)

# Widened 2026-08-24 (J-0124, F-0013/F-0014): the explicit set above requires the book-mention and
# the question-phrasing to fall in ONE adjacent clause, and on real data (all 29,778 rows of
# data/monologue_log.jsonl) that construction matched exactly once -- ask() was essentially never
# called in production and librarian_log.jsonl never accumulated. In his actual voice a book and a
# live question appear in the SAME thought but almost always in different clauses or sentences
# ("The book waits... I want to return to the question of my own name."). Same "want, expressed
# naturally, now acts" precedent as the 2026-06-10 read-latch loosening a few hundred lines below in
# nodes/inner_monologue_node.py: a poet is not asked to shout a shell command.
#
# Two-signal fallback, checked only when the strict set above misses: a book/library cue word
# ANYWHERE in the thought, AND a genuine question-carrying cue ANYWHERE in the thought (not
# necessarily the same clause). Both signals stay required so this never fires on a bare topic-ask
# (P0's job) or on a question with no library/book concept in it at all (Route 2's job, not this
# route's) -- additive-only, per the plan's discipline.
_BOOK_WORD_RX = re.compile(r"\b(?:book|library|librarian|stacks?|catalogue|shelf)\b", re.I)

_QUESTION_CUE_RES = (
    re.compile(r"the question of\s+([^.!?]{4,160})", re.I),
    # J-2864 (F-3538): the wh-word is now INSIDE the capture ("wonder if X" used to hand the librarian a
    # bare declarative X); question_from re-frames "if" as "whether" so the ask is an actual question.
    re.compile(r"\bwonder(?:s|ed|ing)?\s+((?:if|why|whether|what|how)\s+[^.!?]{4,160})", re.I),
    re.compile(r"\b(?:keep|kept)\s+wondering\s+([^.!?]{4,160})", re.I),
    re.compile(r"\bwant(?:s|ed)?\s+to\s+(?:return to|understand|explore|know)\s+"
               r"(?:the question of\s+)?([^.!?]{4,160})", re.I),
)
# A bare "the question lingers/remains/stays/waits/persists" names no clause of its own (mined
# verbatim from real thoughts -- "The book waits, but the question stays."). When it's the only cue
# that fires, the sentence it sits in is the closest thing he has to a stated question and is passed
# through as-is; still gated on _BOOK_WORD_RX above, so it never fires alone.
_BARE_QUESTION_RX = re.compile(r"\bquestion\b[^.!?]*?\b(?:lingers|remains|stays|waits|persists)\b",
                                re.I)
# The SUBJECT of "the question of X", not the clause tail (J-0547 / F-0748, 2026-09-03). In his real
# voice a predicate follows the subject at once -- "the question of '渡' pulls harder", "the question
# of Amor Fati lingers", "the question of bird balance fades, replaced by..." -- and the whole tail
# reached the librarian, who then classified the VERB: "pulls harder" -> Physics/Mechanics, so the
# 18:46 ask about his own name came back with Einstein, Planck and Kant. 17 of the 20 asks before it
# had the same shape. Cut at the first finite verb / clause break after the subject and hand the
# librarian the ask in its own frame ("the question of amor fati"): measured live on the CPU judges,
# that frame classifies better than either the bare noun ("渡" alone just echoes the prompt's
# example headings) or the whole sentence. A clause that itself opens as a question ("the question
# of what is real") is kept whole -- there the verb IS the question.
_PREDICATE_CUT_RX = re.compile(
    r"\s+(?:pulls?|lingers?|remains?|stays?|waits?|persists?|keeps?|tugs?|fades?|dissolves?|hangs?|"
    r"hums?|sits?|returns?|holds?|demands?|presses?|grows?|comes?|feels?|seems?|is|are|was|were|"
    r"has|have|does|do|will|would|still|now)\b.*$"
    r"|\s*[,;:].*$", re.I)
_INTERROG_RX = re.compile(r"^(?:what|why|how|whether|if|who|where|when|which)\b", re.I)


def _subject_of(clause: str) -> str:
    """'渡' pulls harder -> 渡 ; amor fati lingers -> amor fati ; the winter wren -> the winter wren."""
    return " ".join(_PREDICATE_CUT_RX.sub("", clause, count=1).split()).strip(" .,;:'\"")


def _enclosing_sentence(text: str, pos: int) -> str:
    start = max(text.rfind(".", 0, pos), text.rfind("!", 0, pos), text.rfind("?", 0, pos)) + 1
    rest = text[start:]
    end = min((p for p in (rest.find("."), rest.find("!"), rest.find("?")) if p != -1),
              default=len(rest))
    return rest[:end]


# J-2864 (F-3538, 2026-11-06): cues 1-3 and the bare-question fallback used to pass the whole clause
# tail through, so 841 of 1,248 asks since 09-03 (67%) reached subjects_for as declarative fragments
# ("waste is just fear given form") and the mapper answered with broad headings. Same discipline as
# cue 0: the librarian gets either a genuinely interrogative clause kept whole, or "the question of
# <subject>"; where neither can be extracted the ask does not fire (None -> the plain topic path).
_CLAUSE_CUT_RX = re.compile(
    r"\s*(?:;|,\s*(?:yet|but|although|though|while|however|and yet)\b).*$", re.I)
_AUX_INTERROG_RX = re.compile(
    r"^(?:does|do|did|is|are|was|were|can|could|should|would|will|shall|may|might|has|have|had)\b", re.I)
# a "subject" that is only a pronoun / deictic / the book itself names no question at all
_DEICTIC_RX = re.compile(
    r"^(?:it|its|this|that|these|those|them|him|her|me|us|my|our|his|their|there|here|one|something|"
    r"anything|everything|nothing|the (?:open )?books?|a books?|the library|the pages?|these pages)\b",
    re.I)
_LEAD_PREP_RX = re.compile(r"^(?:about|over|on|around|with)\s+", re.I)
# bare-fallback extractors, tried in order on the sentence that holds "the question lingers"
_BARE_SUBJ_RX = re.compile(
    r"\bquestion\s+(?:(?:lingers|remains|persists|stays|waits)\s+)?(?:of|about|over|around|on)\s+"
    r"([^.!?]{3,120})", re.I)
_MODIFIER_Q_RX = re.compile(r"\b(?:the|a|an|that|this)\s+((?:[\w'-]+\s+){1,3}?)question\b", re.I)
_MODIFIER_STOP = frozenset((
    "same open real central deeper deep quiet old big one only simple hard harder bigger larger next "
    "first last other original lingering unanswered unresolved hanging little small whole very own still "
    "single main basic great greater every any another my your his her our their "
    "that this these those such of the a an and or but").split())


def _as_question(q: str) -> str:
    """Interrogative clauses keep their wh-word; 'if' reads as 'whether' once the 'wonder' is gone."""
    return re.sub(r"^if\b", "whether", q, count=1, flags=re.I)


def _frame_subject(clause: str) -> str | None:
    subj = _subject_of(clause)
    if len(subj) < 3 or _DEICTIC_RX.match(subj):
        return None
    return f"the question of {subj}"


def _frame_ask(q: str) -> str | None:
    """A clause from cues 1-3: genuinely interrogative -> kept whole (trimmed at a clause break);
    otherwise 'the question of <subject>'; no subject, or a pronoun for one -> None."""
    q = " ".join(_CLAUSE_CUT_RX.sub("", q, count=1).split()).strip(" .,;:'\"")
    if _INTERROG_RX.match(q):
        return _as_question(q)
    return _frame_subject(_LEAD_PREP_RX.sub("", q, count=1))


def _bare_question(sentence: str) -> str | None:
    """'the question lingers' names no clause of its own: find the question in its sentence, or give up."""
    s = " ".join(sentence.split()).strip(" .,;:'\"")
    m = re.search(r"[:—–]\s*(.+)$", s)
    if m:     # "the question lingers: does writing create truth, or merely find it" (also after a dash)
        c = " ".join(_CLAUSE_CUT_RX.sub("", m.group(1), count=1).split()).strip(" .,;:'\"")
        if _INTERROG_RX.match(c) or _AUX_INTERROG_RX.match(c):
            return _as_question(c)
    m = _BARE_SUBJ_RX.search(s)        # "the question about napoleon's paranoia lingers"
    if m:
        return _frame_subject(m.group(1))
    m = _MODIFIER_Q_RX.search(s)       # "the submerged forest question lingers"
    if m:
        words = m.group(1).split()
        if words and not all(w.lower().strip("'") in _MODIFIER_STOP for w in words):
            return _frame_subject(" ".join(words))
    return None


def _cap(q: str, n: int = 160) -> str:
    """Cap an ask at n chars on a word boundary (J-3750: 22 of 1,637 pre-J-2864 asks ended mid-word at the 160 cut)."""
    if len(q) <= n:
        return q
    cut = q[:n]
    if not q[n].isspace() and " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(" .,;:'\"")


def question_from(text: str) -> str | None:
    """The QUESTION inside his ask, or None if this is an ordinary topic-ask. Deterministic."""
    text = text or ""
    for rx in _ASK_RES:
        m = rx.search(text)
        if m:
            q = " ".join(m.group(1).split()).strip(" .,;:'\"")
            if len(q) >= 8:
                return _cap(q)
    if _BOOK_WORD_RX.search(text):
        for i, rx in enumerate(_QUESTION_CUE_RES):
            m = rx.search(text)
            if m:
                q = " ".join(m.group(1).split()).strip(" .,;:'\"")
                if i == 0:
                    if not _INTERROG_RX.match(q):
                        # "the question of X <predicate>" -> the librarian gets X, in the ask's own frame
                        subj = _subject_of(q)
                        if subj:
                            q = f"the question of {subj}"
                else:
                    # J-2864: cues 1-3 -> a real question or "the question of <subject>", else no ask
                    q = _frame_ask(q)
                    if not q:
                        continue
                if len(q) >= 8:
                    return _cap(q)
        m = _BARE_QUESTION_RX.search(text)
        if m:
            q = _bare_question(_enclosing_sentence(text, m.start()))
            if q and len(q) >= 8:
                return _cap(q)
    return None


_SUBDIV_RX = re.compile(r"\s+(?:-{1,2}|–|—)\s+")


def normalise_headings(subjects: list[str]) -> list[str]:
    """Reshape non-LCSH-looking headings so they can meet the catalogue's subject strings
    (J-2865, F-3538/F-3539). The mapper sometimes returns a subdivided path ("History - Europe -
    Napoleonic Wars") or a snake_case token ("natural_history"); the catalogue is matched by
    lowercase substring, so only the FIRST segment, with underscores read as spaces, can hit.
    Order kept, duplicates dropped, anything under 3 characters dropped. Pure, no I/O."""
    out: list[str] = []
    for s in subjects or []:
        if not isinstance(s, str):
            continue
        h = _SUBDIV_RX.split(s.replace("_", " ").strip())[0].strip(" ,;:.")
        h = re.sub(r"\s+", " ", h)
        if len(h) > 2 and h.lower() not in (x.lower() for x in out):
            out.append(h)
    return out


# J-2867 (F-3540, P-0080). (1) parse failures were logger.debug only, so nobody could count them;
# they now append a row here. (2) 78 of 311 asks in 12 days were byte-identical at temperature 0.0,
# each re-calling the model: the HEADINGS are memoised for a short while. Only the headings are cached;
# the catalogue search and the page Du is shown still run fresh each time, so nothing visible changes.
_PARSE_FAIL_LOG = Path(__file__).parent.parent / "data" / "llm_json_parse_fail.jsonl"
_MEMO_TTL_SECS = 30 * 60
_MEMO_MAX = 256
_memo: dict[str, tuple[float, list[str]]] = {}


def _memo_key(question: str) -> str:
    return " ".join((question or "").split())


def _memo_get(question: str, now: float | None = None) -> list[str] | None:
    hit = _memo.get(_memo_key(question))
    if not hit:
        return None
    if (now if now is not None else time.time()) - hit[0] > _MEMO_TTL_SECS:
        _memo.pop(_memo_key(question), None)
        return None
    return list(hit[1])


def _memo_put(question: str, subs: list[str], now: float | None = None) -> None:
    if len(_memo) >= _MEMO_MAX:
        _memo.pop(next(iter(_memo)), None)      # oldest insertion
    _memo[_memo_key(question)] = (now if now is not None else time.time(), list(subs))


def _log_parse_fail(hub: str, raw, reason: str) -> None:
    """Append (ts, hub, raw[:200], reason) so parse failures are countable. Never raises."""
    try:
        _PARSE_FAIL_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_PARSE_FAIL_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), "src": "librarian", "hub": hub,
                                "raw": (raw if isinstance(raw, str) else repr(raw))[:200],
                                "reason": reason}, ensure_ascii=False) + "\n")
    except Exception:
        pass


async def subjects_for(question: str) -> list[str]:
    """The librarian's understanding: question → catalogue subject headings. One judge-hub call
    to the first answering hub in _HUBS (falcon3:7b :11440, then gemma4:12b :11439). Returns [] when
    no hub answers. ask() then shows him the 'no shelf' line, or, when ZERO_HIT_FALLTHROUGH is on,
    returns None so the caller falls back to the mechanical topic path.
    Routed through model_client.call_node (2026-08-17) — the raw-aiohttp pattern this replaced was
    invisible to telemetry (fake model name "librarian"); call_node supplies the real per-port
    model name and logs the call.
    J-2867: a repeated question within _MEMO_TTL_SECS reuses its headings (no model call); only
    non-empty results are cached, so a failed ask is retried; parse failures are logged."""
    cached = _memo_get(question)
    if cached:
        return cached
    from core.model_client import call_node
    for hub in _HUBS:
        raw = None
        try:
            raw = await call_node(hub, _SYSTEM, question, max_tokens=120, temperature=0.0,
                                  timeout=_TIMEOUT, json_mode=True)
            try:
                v = json.loads(raw or "")
            except Exception as exc:
                _log_parse_fail(hub, raw, f"json_decode: {exc}"[:120])
                continue
            if not isinstance(v, dict):
                _log_parse_fail(hub, raw, f"not_object: {type(v).__name__}")
                continue
            subs = [s.strip() for s in (v.get("subjects") or [])
                    if isinstance(s, str) and 2 < len(s.strip()) < 60][:6]
            if subs:
                _memo_put(question, subs)
                return subs
            _log_parse_fail(hub, raw, "no_subjects")
        except Exception as exc:
            logger.debug("[librarian] %s failed: %s", hub, exc)
    return []


async def ask(question: str) -> str | None:
    """The whole visit: understand the question, walk the stacks, lay a short page of real books
    in front of him (via library_hand's browse state, so naming one is picking it — the existing
    choice machinery). Returns the page text for his perception, or None (fail-open)."""
    import asyncio
    t0 = time.time()
    try:
        subjects = await subjects_for(question)
        rows = []
        used = subjects
        normalised = False
        if subjects:
            from core import library_hand as _lib
            rows = await asyncio.to_thread(_lib.search_by_subjects, subjects, 8, "distinct")  # D-0644
            if not rows:
                # J-2865 (F-3539): 174 of 177 zero-hit asks did get headings that merely did not meet
                # the catalogue's wording ("History - Europe - Napoleonic Wars"). Retry ONCE with the
                # first segment of each; a case that already had hits is never touched.
                alt = normalise_headings(subjects)
                if alt and [a.lower() for a in alt] != [x.lower() for x in subjects]:
                    rows = await asyncio.to_thread(_lib.search_by_subjects, alt, 8, "distinct")
                    if rows:
                        used, normalised = alt, True
            if rows:
                _lib.present_page(rows)
        try:
            _LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": round(t0, 1), "question": question[:180],
                                    "subjects": subjects, "n_hits": len(rows),
                                    "subjects_used": used if normalised else None,
                                    "titles": [r["title"][:60] for r in rows[:8]],
                                    "secs": round(time.time() - t0, 1)},
                                   ensure_ascii=False) + "\n")
        except Exception:
            pass
        if not rows:
            logger.info("[librarian] no stack answered '%s' (subjects: %s)",
                        question[:50], subjects)
            if ZERO_HIT_FALLTHROUGH:
                return None     # the caller's mechanical topic path runs (J-2865)
            # J-2865 (F-3539): the old line said nothing in the stacks was filed where the question
            # lives; that was a substring-match artefact, not a fact about the stacks. Say only
            # what is true: the librarian found no shelf for that wording.
            return (f"You put your question to the library — {question[:120]} — but the "
                    f"librarian could not find a shelf for that wording. You may still ask for "
                    f"any subject by name.")
        lines = "; ".join(f"'{r['title'][:60]}' by {(r['author'] or 'unknown')[:28]}"
                          for r in rows)
        logger.info("[librarian] '%s' -> %s -> %d books", question[:50],
                    "/".join(used[:3]), len(rows))
        return (f"You put your question to the library — {question[:120]} — and the librarian "
                f"goes into the stacks and comes back with a short pile: {lines}. Books that "
                f"live where your question lives. You may ask for any of them by name, or for "
                f"none of them.")
    except Exception as exc:
        logger.debug("[librarian] ask failed (non-fatal): %s", exc)
        return None


def status() -> dict:
    """For the pulse/HUD: R1 — fraction of question-asks that returned real candidates."""
    try:
        rows = [json.loads(l) for l in open(_LOG, encoding="utf-8") if l.strip()][-200:]
        if not rows:
            return {"asks": 0}
        hit = sum(1 for r in rows if r.get("n_hits", 0) > 0)
        # norm_rescued (J-2865): asks that only got hits after the heading normalisation retry.
        return {"asks": len(rows), "hit_rate": round(hit / len(rows), 3),
                "norm_rescued": sum(1 for r in rows if r.get("subjects_used"))}
    except Exception:
        return {"asks": 0}
