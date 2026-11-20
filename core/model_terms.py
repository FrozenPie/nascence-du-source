"""
Nascence - model_terms: mark the terms of a Curiosity question that the generator brought from its own weights.

J-3350 (D-0629 part 2, design: docs/reviews/J-3240_entity_name_and_model_knowledge_tag_review.md section 5).

A term is "model supplied" when it appears in a question but (a) is not in the prompt context the generator was
given, and (b) is in no memory fragment older than the question. That is a fact about the text found by something
other than the writer (the mottainai test: the word had no earlier life anywhere in Du's world). The tag is never
placed in any prompt (law: no hint to Du; the world answers). Corroboration is computed live by the reader
(core/epistemic_state.py shadow), never stored here.

detect(question_texts, prompt_context_text, asof_ts, index=None) -> sorted list of folded terms.

The first-seen index (term -> earliest fragment timestamp) is built once from memory_fragments and refreshed
incrementally (only fragments at or after the watermark are read). It is read-only against the memory DB.
Fail-open everywhere: detect() returns [] on any error and never raises into the cycle.
"""
from __future__ import annotations

import json
import logging
import re
import sqlite3
import threading
import time
import unicodedata
from pathlib import Path

logger = logging.getLogger("nascence.model_terms")

TAG_ENABLED = True            # kill switch for the tag itself (the ledger reader has its own flag, MODEL_TERMS_LEDGER)

_ROOT = Path(__file__).parent.parent
_DEFAULT_DB = _ROOT / "data" / "memory" / "nascence.db"
_DEFAULT_CACHE = _ROOT / "data" / "model_terms_first_seen.json"

_MIN_LEN = 3
_MAX_LEN = 40

# Capitalised words the prototype flagged that are ordinary English, not model-supplied knowledge.
STOP_TERMS = frozenset({
    "war", "out", "two", "ten", "art", "mad", "son", "the", "and", "but", "for", "how", "why", "what", "who",
    "when", "where", "which", "does", "did", "can", "could", "would", "should", "are", "was", "were", "has",
    "have", "not", "one", "three", "four", "five", "six", "seven", "eight", "nine", "his", "her", "its", "our",
    "man", "men", "new", "old", "big", "end", "day", "way", "air", "sea", "sun", "law", "god", "net", "age",
    "box", "key", "red", "blue", "east", "west", "north", "south", "first", "last", "great", "world", "time",
})

_WORD = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)?", re.UNICODE)       # a letter run, optional inner apostrophe
_LETTERS = re.compile(r"[^\W\d_]{%d,%d}" % (_MIN_LEN, _MAX_LEN), re.UNICODE)
_QUOTED = (
    re.compile(r'"([^"\n]{2,60})"'),
    re.compile("“([^”\n]{2,60})”"),
    re.compile("‘([^’\n]{2,60})’"),
    re.compile(r"(?<![\w])'([^'\n]{2,60})'(?![\w])"),
)
_SENT_END = (".", "?", "!", ":", ";", "\n")


def fold(text: str) -> str:
    """Lowercase and strip accents (the prototype lost Munsterberg and Milosevic to accent stripping, so fold, never drop)."""
    nf = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in nf if not unicodedata.combining(c)).lower()


def _strip_possessive(word: str) -> str:
    for suf in ("'s", "’s", "'", "’"):
        if word.endswith(suf) and len(word) > len(suf) + 1:
            return word[: -len(suf)]
    return word


def tokens(text: str) -> set:
    """Folded letter-run tokens (len 3..40) of a text, possessives stripped. Used for the context and the index."""
    out = set()
    for w in _WORD.findall(text or ""):
        for t in _LETTERS.findall(fold(_strip_possessive(w)).replace("'", " ").replace("’", " ")):
            out.add(t)
    return out


def candidates(text: str) -> set:
    """Folded candidate terms of one question: quoted words, and capitalised words that are not sentence-initial."""
    text = text or ""
    found: set = set()
    for rx in _QUOTED:
        for m in rx.finditer(text):
            found |= tokens(m.group(1))
    for m in _WORD.finditer(text):
        w = m.group(0)
        if not w[0].isupper():
            continue
        before = text[: m.start()].rstrip(" \t\"'“‘([{")
        if not before or before.endswith(_SENT_END):
            continue                                   # sentence-initial capital: not evidence of a name
        found |= tokens(_strip_possessive(w))
    return found


class FirstSeenIndex:
    """term -> earliest fragment timestamp, over memory_fragments content. Refreshed incrementally."""

    def __init__(self, db_path=None, cache_path=None):
        self.db_path = Path(db_path) if db_path else _DEFAULT_DB
        self.cache_path = Path(cache_path) if cache_path else None
        self.first: dict = {}
        self.watermark: float = 0.0
        self._last_save = 0.0
        self._load_cache()

    def _load_cache(self) -> None:
        try:
            if self.cache_path and self.cache_path.exists():
                d = json.loads(self.cache_path.read_text(encoding="utf-8"))
                self.first = {str(k): float(v) for k, v in (d.get("first") or {}).items()}
                self.watermark = float(d.get("watermark") or 0.0)
        except Exception as exc:
            logger.debug("[model_terms] cache load failed (rebuilding): %s", exc)
            self.first, self.watermark = {}, 0.0

    def save(self) -> bool:
        """Write the cache (only when a cache_path was given). Never raises."""
        try:
            if not self.cache_path:
                return False
            from core import profile as _profile
            _profile.guard_path(self.cache_path)       # a non-live process must not write the live cache (D-0179)
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.cache_path.with_suffix(self.cache_path.suffix + ".tmp")
            tmp.write_text(json.dumps({"watermark": self.watermark, "first": self.first}, ensure_ascii=False),
                           encoding="utf-8")
            tmp.replace(self.cache_path)
            self._last_save = time.time()
            return True
        except Exception as exc:
            logger.debug("[model_terms] cache save failed (non-fatal): %s", exc)
            return False

    def refresh(self) -> int:
        """Read fragments at or after the watermark (idempotent: min() per term). Returns fragments read. Read-only DB."""
        uri = "file:%s?mode=ro" % self.db_path.as_posix()
        conn = sqlite3.connect(uri, uri=True, timeout=30.0)
        n = 0
        try:
            cur = conn.execute("SELECT content, timestamp FROM memory_fragments WHERE timestamp >= ? "
                               "ORDER BY timestamp", (self.watermark,))
            first = self.first
            for content, ts in cur:
                ts = float(ts)
                for t in tokens(content or ""):
                    old = first.get(t)
                    if old is None or ts < old:
                        first[t] = ts
                if ts > self.watermark:
                    self.watermark = ts
                n += 1
        finally:
            conn.close()
        return n

    def first_seen(self, term: str):
        return self.first.get(term)


_DEFAULT: FirstSeenIndex | None = None


def default_index() -> FirstSeenIndex:
    """The process-wide live index (cache under data/). Created lazily; the caller refreshes it."""
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = FirstSeenIndex(_DEFAULT_DB, _DEFAULT_CACHE)
    return _DEFAULT


def _is_truncation_join(term: str, first: dict, asof_ts: float) -> bool:
    """A mid-word-truncated theme joined to the next word ("galileoin"): a known older term plus 2-3 letters."""
    if len(term) < 6:
        return False
    for k in (2, 3):
        base = term[:-k]
        ts = first.get(base) if len(base) >= 4 else None
        if ts is not None and ts < asof_ts:
            return True
    return False


_refresh_lock = threading.Lock()
_last_refresh = 0.0


def ready(index: FirstSeenIndex | None = None) -> bool:
    """True once the index has been loaded from its cache or built at least once."""
    idx = index if index is not None else default_index()
    return idx.watermark > 0.0


def refresh_async(min_interval: float = 120.0, index: FirstSeenIndex | None = None) -> bool:
    """Start an incremental refresh (and cache save) on a daemon thread unless one ran within min_interval seconds or is
    running. The live cycle never waits on it (a cold build reads every fragment). Returns True if a thread started."""
    global _last_refresh
    idx = index if index is not None else default_index()
    try:
        if idx.cache_path:
            from core import profile as _profile
            _profile.guard_path(idx.cache_path)        # non-live process: no background build, no cache write
    except Exception:
        return False
    now = time.time()
    if now - _last_refresh < min_interval or not _refresh_lock.acquire(blocking=False):
        return False
    _last_refresh = now

    def _run():
        try:
            idx.refresh()
            idx.save()
        except Exception as exc:
            logger.debug("[model_terms] background refresh failed (non-fatal): %s", exc)
        finally:
            _refresh_lock.release()

    threading.Thread(target=_run, name="model_terms_refresh", daemon=True).start()
    return True


def detect(question_texts, prompt_context_text: str, asof_ts: float, index: FirstSeenIndex | None = None) -> list:
    """Terms of the questions that are model supplied. Never raises; [] on any error or when TAG_ENABLED is False."""
    try:
        if not TAG_ENABLED:
            return []
        if isinstance(question_texts, str):
            question_texts = [question_texts]
        idx = index if index is not None else default_index()
        ctx = tokens(prompt_context_text or "")
        first = idx.first
        out = set()
        for q in question_texts or []:
            for t in candidates(str(q)):
                if t in STOP_TERMS or t in ctx:
                    continue
                ts = first.get(t)
                if ts is not None and ts < asof_ts:
                    continue                            # it had an earlier life in Du's memory
                if _is_truncation_join(t, first, asof_ts):
                    continue
                out.add(t)
        return sorted(out)
    except Exception as exc:
        logger.debug("[model_terms] detect failed (non-fatal): %s", exc)
        return []
