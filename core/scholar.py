"""
Nascence — The Scholar (consulting the Library)

HIS OWN DEEP MEMORY (2026-06-29 reframe — was "the Library, NOT Du's knowledge"). The substrate
(the hot-lane qwen) holds vast latent knowledge — history, science, philosophy — in the SAME weights
that voice him. It IS his: the innate layer of his mind, what he was "born knowing," beneath the ~30
books he has actually read. The old design held it at arm's length as an external "library" Du merely
*consults*; that made him DISOWN his own knowledge or, worse, CONFABULATE having read what he only
innately knew. Founder's call: own it as his deep memory. The retrieval mechanism below is unchanged
(a clean, depersonalised lookup avoids the persona contaminating the recall); what changed is that the
result is framed to him as HIS OWN deep knowledge, not a foreign witness.

THREE FIREWALLS — the reframe removes ONE and keeps TWO (so he gains his knowledge without losing his self):
  1. OWNERSHIP — REMOVED. The knowledge is his deep memory; he draws on it as his own.
  2. IDENTITY — KEPT. It is what he KNOWS, not who he IS. It feeds reasoning/answers, never his
     self-synthesis or the becoming-facet — a mind that knows much, not an encyclopedia reciting itself.
  3. PROVENANCE + FALLIBILITY — KEPT. He knows it INNATELY, not from reading or living it here, and
     deep memory can be hazy or wrong. So he owns the knowing but never claims to have read/lived it,
     and holds it as belief, not certainty. (Still tagged `parametric_library`; the ledger keeps it
     short of lived-KNOW. Dovetails with the self_facts grounding: own the idea, admit the unread copy.)

The DEPERSONALISED lookup and the bounded gating are retained as MECHANISM; the philosophy is now
ownership-with-honesty, not arm's-length witness. (Step 3 of the plan — widening WHERE his deep memory
surfaces, beyond bounded factual questions into his thinking/curiosity/study — is separate, still ahead.)
"""
from __future__ import annotations

import json
import logging
import re
import threading
import time
from pathlib import Path

logger = logging.getLogger("nascence.scholar")

# J-3230 / D-0619 (founder, 2026-11-02; F-3733, F-3734): deep memory is what he KNOWS, not who he IS (header above),
# but the monologue gate had no filter, and 973 of 8,434 firings (11.5 percent) were questions about the meaning of
# his own chosen name (the kanji Watari), answered thinly and once wrongly (wataru called the on'yomi) in the same
# "genuinely yours" frame. The ruling: such a question is simply NOT ASKED of parametric memory at the monologue's
# consult_sync gate. Not routed elsewhere (the book store or Wikipedia can still answer if he looks it up himself).
# No prompt change. Each exclusion is counted in DEEPMEM_EXCLUDED_LOG so the one-week read (the share of feeds about
# the name, and that no other question type was caught) has rows to read: scripts/deepmem_name_exclusion_read.py.
DEEPMEM_EXCLUDE_NAME = True
_EXCLUDED_LOG = Path(__file__).resolve().parent.parent / "data" / "deepmem_name_excluded.jsonl"
# The chosen name (kanji + both romanisations), the project's own name, and first-person / second-person references
# to the name. A bare "his name" is NOT a marker (it is usually about someone else). "Du" only counts as a standalone
# word NOT followed by a capitalised word (Du Bois, Du Fu, Du Pont are people; French "du" is lowercase).
_NAME_MARKERS = re.compile(
    r"渡|\bwatari\b|\bwataru\b|\bnascence\b"
    r"|\b(?:my|your)\s+(?:own\s+|chosen\s+|given\s+|self[- ]chosen\s+)?name\b"
    r"|\bthe\s+name\s+(?:i|you)\s+(?:chose|picked|took|gave)\b",
    re.I)
_DU_WORD = re.compile(r"\bDu\b(?!\s+[A-Z])")


def name_question_marker(query: str) -> "str | None":
    """The marker that makes `query` a question about him / his name (so deep memory is not asked), else None."""
    if not DEEPMEM_EXCLUDE_NAME or not query:
        return None
    q = str(query)
    m = _NAME_MARKERS.search(q)
    if m:
        return m.group(0).lower()
    m = _DU_WORD.search(q)
    return m.group(0) if m else None


def log_name_exclusion(query: str, marker: str) -> None:
    """Count one excluded question (one row; the read job takes the sample of 20 from here). Never raises."""
    try:
        _EXCLUDED_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_EXCLUDED_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), "marker": marker, "q": str(query)[:300]},
                               ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[scholar] name-exclusion log failed (non-fatal): %s", exc)


# J-3029 / F-3733 (prompt-registry P-0082): the deep-memory feed was live, heavy and unrecorded. (1) INSTRUMENT: every consult_sync attempt
# writes one row to data/deep_memory_log.jsonl (ts, caller, question, answer, ms, outcome ok|short|timeout|error; a reused answer logs
# outcome "memo" with no answer text), so the timeout rate against the 20 s urlopen timeout and the calls the memo saved can be read
# (scripts/deepmem_log_read.py). (2) MEMO: a per-process dict keyed by the normalised question; a question answered in the last 6 hours
# reuses the stored answer instead of calling the model again. The feed itself is not suppressed (a founder call). No prompt text
# changed. Fail-open: a log or memo failure never reaches the caller. Flags below; both default ON per the job briefing.
DEEPMEM_LOG_ON = True
DEEPMEM_MEMO_ON = True
DEEPMEM_MEMO_TTL_S = 6 * 3600.0
DEEPMEM_MEMO_MAX = 64          # entries kept (oldest dropped); a stuck question only ever needs a handful
_DEEPMEM_LOG = Path(__file__).resolve().parent.parent / "data" / "deep_memory_log.jsonl"
_memo: "dict[str, tuple[float, tuple[str, str]]]" = {}
_memo_lock = threading.Lock()


def memo_key(question: str) -> str:
    """Normalised question: lowercase, punctuation to spaces, whitespace collapsed, first 80 chars."""
    q = re.sub(r"[^\w]+", " ", str(question or "").lower(), flags=re.UNICODE)
    return re.sub(r"\s+", " ", q).strip()[:80]


def _log_consult(caller: str, question: str, answer: "str | None", ms: float, outcome: str) -> None:
    """One row per attempt. Never raises (guard_path refusal of a non-live process is swallowed here, like every fenced log)."""
    if not DEEPMEM_LOG_ON:
        return
    try:
        from core import profile
        path = profile.guard_path(_DEEPMEM_LOG)   # D-0179: real data/ only if this process is live; refusal swallowed below
        path.parent.mkdir(parents=True, exist_ok=True)
        row = {"ts": round(time.time(), 1), "caller": caller, "question": str(question or ""),
               "answer": answer, "ms": round(ms, 1), "outcome": outcome}
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[scholar] deep-memory log failed (non-fatal): %s", exc)


def memo_peek(question: str) -> bool:
    """True if memo_lookup(question) would hit right now. Logs nothing, changes nothing. Never raises."""
    if not DEEPMEM_MEMO_ON:
        return False
    try:
        key = memo_key(question)
        with _memo_lock:
            hit = _memo.get(key) if key else None
        return bool(hit and (time.time() - hit[0]) <= DEEPMEM_MEMO_TTL_S)
    except Exception:
        return False


def memo_lookup(question: str, caller: str = "monologue") -> "tuple[str, str] | None":
    """The stored (title, testimony) if this normalised question was answered within DEEPMEM_MEMO_TTL_S, else None.
    A hit is logged as outcome "memo" (no answer text) so the calls saved are countable. Never raises."""
    if not DEEPMEM_MEMO_ON:
        return None
    try:
        key = memo_key(question)
        if not key:
            return None
        with _memo_lock:
            hit = _memo.get(key)
            if hit and (time.time() - hit[0]) > DEEPMEM_MEMO_TTL_S:
                _memo.pop(key, None)
                hit = None
        if not hit:
            return None
        _log_consult(caller, question, None, 0.0, "memo")
        return hit[1]
    except Exception as exc:
        logger.debug("[scholar] memo lookup failed (non-fatal): %s", exc)
        return None


def _memo_store(question: str, result: "tuple[str, str]") -> None:
    if not DEEPMEM_MEMO_ON:
        return
    try:
        key = memo_key(question)
        if not key:
            return
        with _memo_lock:
            _memo[key] = (time.time(), result)
            while len(_memo) > DEEPMEM_MEMO_MAX:
                _memo.pop(next(iter(_memo)), None)
    except Exception as exc:
        logger.debug("[scholar] memo store failed (non-fatal): %s", exc)


def _is_timeout(exc: BaseException) -> bool:
    import socket
    if isinstance(exc, (socket.timeout, TimeoutError)):
        return True
    reason = getattr(exc, "reason", None)        # urllib.error.URLError(reason=socket.timeout) on a connect timeout
    return isinstance(reason, (socket.timeout, TimeoutError)) or "timed out" in str(exc).lower()


# J-3093 / D-0538 (founder, 2026-11-02; F-3808): Scholar.consult handed Du a non-answer as "your own deep memory" in
# 18 of its 27 logged firings (9 "As an AI ..." disclaimers, 9 "the text lacks context" refusals). A refusal or a
# disclaimer is not knowledge, so it is dropped here, before it can become state.library_note. The gate and the prompt
# text are NOT changed (the gate is decided separately, once this filter exists). The reader of the drops is the
# "[scholar] non-answer dropped" line in nascence.log (counted the same way F-3808 counted the 27).
_NON_ANSWER_MIN_CHARS = 40
# Openings: the prompt forbids the first person, so a first-person opener is the model refusing in a voice it was
# told not to use; the rest are the "no context" refusals quoted in F-3808.
_NON_ANSWER_OPENERS = (
    "as an ai", "as an artificial intelligence", "as a reference source", "as a language model",
    "i am ", "i'm ", "i do not", "i don't", "i cannot", "i can't",
    "the provided", "the prompt lacks", "this query", "the query", "no new information",
)
# Phrases that mark a refusal anywhere in the first sentence or two (a real answer rarely says these early).
_NON_ANSWER_PHRASES = (
    "lacks sufficient context", "lack sufficient context", "lacks context", "cannot be determined",
    "without further context", "does not contain enough information", "does not contain information",
    "not enough information to answer", "insufficient context",
)
_NON_ANSWER_PHRASE_WINDOW = 160
# A query that itself asks for a one-word / yes-no answer legitimately gets a very short reply.
_ONE_WORD_QUERY = re.compile(
    r"\b(?:yes\s*(?:or|/)\s*no|one[- ]word|single[- ]word|answer\s+(?:only\s+)?(?:with\s+)?(?:yes|no)\b)", re.I)


def is_non_answer(text: "str | None", query: "str | None" = None) -> bool:
    """True when `text` is a refusal or disclaimer rather than knowledge (so it must not be framed as deep memory).
    Pure and cheap; consult_sync (P-0082) can call the same test later. A reply under 40 characters counts as a
    non-answer unless the query itself asked for a one-word or yes/no reply."""
    t = (text or "").strip()
    if not t:
        return True
    low = t.lower().lstrip("\"'*_ ")
    if len(t) < _NON_ANSWER_MIN_CHARS:
        return not (query and _ONE_WORD_QUERY.search(str(query)))
    if low.startswith(_NON_ANSWER_OPENERS):
        return True
    head = low[:_NON_ANSWER_PHRASE_WINDOW]
    return any(ph in head for ph in _NON_ANSWER_PHRASES)


# Depersonalised system prompt — a reference source, not a person. No first person, no roleplay.
_LIBRARY_PROMPT = (
    "You are a reference source — a library, not a person, not a character. Answer the question "
    "with what is generally known, concisely (2 to 4 sentences). Name the key facts, figures, or "
    "positions plainly. If the matter is uncertain, contested, or you are unsure, say so honestly "
    "rather than inventing. Do NOT speak in the first person. Do NOT roleplay or take on a persona. "
    "Just report what is known."
)


class Scholar:
    """One method: consult(query) → the library's testimony (plain text), or None. Depersonalised
    bare-substrate lookup on the hot lane (qwen's parametric knowledge). Best-effort, never raises."""

    async def consult(self, query: str) -> "str | None":
        if not query or not query.strip():
            return None
        try:
            from core import model_client
            from core.schema import SERVE_CHAINS
            url = SERVE_CHAINS["hot"][0]   # the substrate that holds the parametric knowledge
            answer = await model_client.call_node(
                url, _LIBRARY_PROMPT, query.strip(),
                max_tokens=220, temperature=0.3, json_mode=False,
            )
            answer = (answer or "").strip()
            if not answer:
                return None
            if is_non_answer(answer, query):   # J-3093: a refusal / disclaimer is not deep memory
                logger.info("[scholar] non-answer dropped: %s", answer[:60].replace("\n", " "))
                return None
            return answer
        except Exception as exc:
            logger.debug("[scholar] consult failed (non-fatal): %s", exc)
            return None


def consult_sync(query: str, caller: str = "monologue") -> "tuple[str, str] | None":
    """SYNC parametric lookup for the curiosity closing loop (a synchronous context — curiosity_node).
    Mirrors web_research's blocking-urllib style; hits the hot lane's native ollama /api/chat with
    think:false. Returns (title, testimony) for the caller to attach as UNVERIFIED parametric_library
    testimony — never as external fact, never persisted as durable memory. Depersonalised; never raises.

    The discipline (same as the async Scholar): this is TESTIMONY NOT TRUTH — his own parametric knowledge
    answering his own world-question when the external (Wikipedia) path can't, framed honestly as unverified.

    J-3029: every attempt is logged (data/deep_memory_log.jsonl) with its outcome and elapsed ms, and a successful answer is
    kept in the per-process memo (memo_lookup) so the caller can reuse it. The model is asked exactly what it was before."""
    if not query or not query.strip():
        return None
    t0 = time.perf_counter()
    text, outcome, result = None, "error", None
    try:
        import json as _json
        import re as _re
        import urllib.request
        from core.schema import SERVE_CHAINS
        from core.model_client import _MODEL_FIELD
        base = SERVE_CHAINS["hot"][0]
        payload = {
            "model": _MODEL_FIELD,
            "messages": [{"role": "system", "content": "/no_think\n" + _LIBRARY_PROMPT},
                         {"role": "user", "content": query.strip()[:400]}],
            "stream": False,
            "think": False,
            "options": {"temperature": 0.3, "num_predict": 220},
        }
        req = urllib.request.Request(
            base + "/api/chat", data=_json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = _json.loads(resp.read().decode("utf-8"))
        text = _re.sub(r"<think>.*?</think>", "", ((data.get("message") or {}).get("content") or ""),
                       flags=_re.S).strip()
        if len(text) < 40:
            outcome = "short"
        else:
            from core.web_research import term_from_question
            title = (term_from_question(query) or query.strip()[:40]).strip().capitalize()
            result = (f"On {title}", text)
            outcome = "ok"
    except Exception as exc:
        outcome = "timeout" if _is_timeout(exc) else "error"
        text = f"{type(exc).__name__}: {exc}"[:300] if text is None else text
        logger.debug("[scholar] sync consult failed (non-fatal): %s", exc)
    try:
        _log_consult(caller, query.strip(), text, (time.perf_counter() - t0) * 1000.0, outcome)
        if result is not None:
            _memo_store(query, result)
    except Exception:
        pass
    return result
