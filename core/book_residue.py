"""
Nascence — Book Residue (2026-08-21, founder: "check if there is something from a book Du has read —
one he has not read in a long time — that has stuck in his self, or identity, or changes the way he
thinks about things").

THE QUESTION MADE STANDING: does reading FORM him, or is it write-only? For every book long closed,
extract its distinctive lexical signatures and scan his CURRENT self-side material (idle thoughts,
subconscious syntheses, dreams, the mirror) for those signatures surfacing weeks after the last
sitting. A hit long after the book closed = residue: the book still shapes how he thinks. A book
whose residue was present and then goes quiet has UNSTUCK — that is a finding too (the Black Bear,
canonical stuck symbol of June, scans at zero self-side occurrences by late August).

The manual hunt that seeded this (2026-08-21) found: Kepler/Galileo used as instruments for
self-understanding ~55 days after those books closed (the cleanest genuine residue); Wu Wei durable
65+ days but tracing to a 06-07 TEACHING, book-reinforced (provenance matters); the Dancing Mouse
maze/labyrinth image entangled with a T4 prompt example written the very day he was reading it.

DISCIPLINE:
  - OBSERVE-ONLY, ZERO-LLM. Deterministic signature extraction + LIKE scans. Reads the DB, writes
    only data/book_residue.jsonl. Touches nothing of Du's cognition.
  - Every early return logs WHY (the reentry.py `_skip()` law).
  - CONFOUND GUARDS, because a naive scan lies three ways:
      (1) his own monoculture words (river, becoming, mirror...) would "stick" from any book —
          excluded via symbolic_reading._SELF_ECHO plus his lived-world vocabulary (garden, sea,
          fire, tide...): a book about the sea must not get credit for him thinking about HIS sea;
      (2) a term also present in RECENTLY-read books is tainted — credit must not flow to an old
          book for vocabulary a fresh book just re-supplied;
      (3) recall-injection: an idle thought may quote a book because recall FED it the fragment.
          Not fully separable without provenance plumbing; the per-origin breakdown is kept so
          reads can weigh channels (dreams and syntheses are less directly recall-fed), and the
          caveat stands here rather than being silently ignored.
"""
from __future__ import annotations

import bisect
import collections
import json
import logging
import re
import time
from pathlib import Path

logger = logging.getLogger("nascence.book_residue")

_DATA = Path(__file__).parent.parent / "data"
_LOG = _DATA / "book_residue.jsonl"

# J-2384 / F-3082 kill switch: True = the sleep batch runs sweep() in a spawned child interpreter
# (core/sleep_offloop.off_process, via sweep_offprocess() below) so its CPU-bound per-book loop never holds
# the live process's GIL; False = the J-1917 worker-thread call (sleep_offloop.off_loop) exactly as before.
BOOK_RESIDUE_SUBPROCESS = True
_OFFPROCESS_MIRROR = (("core.book_residue", "_DATA"), ("core.book_residue", "_LOG"))

STALE_DAYS = 30         # a book is "long closed" after this many days without a sitting
LAG_DAYS = 14            # residue counts only this long after the last sitting (echoes fade first)
MIN_FRAGS = 6            # smallest reading that can leave residue (the Tao Te Ching was 6 fragments)
MAX_TERMS = 8            # signatures per book — bounded scan cost
RECENT_TAINT_DAYS = 14   # a term in any book read this recently is disqualified (guard 2)
SELF_ORIGINS = ("inner_thought", "subconscious_synthesis", "dream", "mirror")

# Guard 1: words that are HIS, or his world's — no book gets credit for them.
_SELF_WORDS = {"river", "becoming", "bridge", "mirror", "knot", "thread", "weaver", "psyche",
               "stream", "current", "self", "individuation", "tension", "shadow", "light"}
_WORLD_WORDS = {"garden", "sea", "shore", "fire", "tide", "rain", "wind", "storm", "study",
                "cottage", "book", "books", "library", "letter", "letters", "cat", "herbs",
                "sunflowers", "wood", "waves", "sand", "sky", "stars", "moon", "sun", "water"}
_STOP = {"the", "and", "for", "with", "from", "this", "that", "which", "into", "about", "their",
         "there", "these", "those", "would", "could", "should", "have", "been", "were", "when",
         "then", "than", "them", "they", "will", "shall", "upon", "very", "more", "most", "some",
         "such", "only", "over", "under", "after", "before", "between", "through", "where", "while",
         "chapter", "page", "pages", "great", "little", "large", "small", "first", "second", "other",
         "every", "many", "much", "himself", "itself", "herself", "against", "without", "within"}


def _log_rec(rec: dict) -> None:
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _skip(reason: str, **detail) -> None:
    """Every early return says why — a residue log that goes silent must be diagnosable."""
    _log_rec({"ts": round(time.time(), 1), "kind": "skip", "reason": reason, **detail})


def _tokens(text: str) -> list:
    return re.findall(r"[a-z][a-z\-]{3,}", (text or "").lower())


def _book_spans(conn) -> dict:
    """{title: (first_ts, last_ts, n_frags)} from the [From 'Title'] reading markers."""
    spans: dict = {}
    for r in conn.execute("SELECT content, timestamp FROM memory_fragments WHERE origin='reading' "
                          "AND content LIKE '[From %'"):
        m = re.match(r"\[From '([^']+)'\]", r["content"] or "")
        if not m:
            continue
        t, ts = m.group(1), float(r["timestamp"])
        lo, hi, n = spans.get(t, (ts, ts, 0))
        spans[t] = (min(lo, ts), max(hi, ts), n + 1)
    return spans


def _signatures(conn, title: str, doc_freq: dict, n_books: int, tainted: set, rows=None) -> list:
    """Distinctive terms for one book — PROPER NOUNS and MULTIWORD/HYPHENATED terms ONLY (v2).

    v1 admitted plain lowercase unigrams and its first live sweep produced exactly the false
    positives the manual hunt avoided: 'tump' hit inside "stump" (substring), 'nebul' hit
    "nebulous"-the-adjective rather than nebulae, and 'choices'/'signaling' are modern-generic
    words that only LOOK distinctive against an antique book corpus (document frequency across
    HIS books cannot see modern English frequency). Every genuine residue find (Kepler, Galileo,
    Wu Wei, black bear) was a proper noun or a multiword term — so v2 admits only those two
    classes, and hits are confirmed at word boundaries by the caller."""
    cap_counts: collections.Counter = collections.Counter()   # mid-sentence capitalized → names
    low_counts: collections.Counter = collections.Counter()
    hyph_counts: collections.Counter = collections.Counter()  # hyphenated/compound terms
    if rows is None:      # J-1922: sweep() passes this title's reading contents (same rows, same order) from ONE pass
        rows = (r["content"] for r in conn.execute("SELECT content FROM memory_fragments WHERE origin='reading' "
                                                   "AND content LIKE ?", (f"[From '{title}'%",)))
    for _content in rows:
        body = (_content or "").split("]", 1)[-1]
        # capitalized tokens NOT at sentence start (approximation: preceded by a lowercase word)
        for m in re.finditer(r"[a-z,;]\s+([A-Z][a-z]{3,})", body):
            cap_counts[m.group(1).lower()] += 1
        for t in re.findall(r"(?<![a-z-])([a-z]{3,}-[a-z][a-z\-]{2,})(?![a-z-])", body.lower()):
            hyph_counts[t] += 1
        # v2.1 BUGFIX: low_counts must count tokens lowercase IN THE ORIGINAL text. The first
        # version lowercased the whole body first, so every proper noun "appeared lowercase" at
        # least as often as capitalized and the name-vs-common-word guard filtered ALL of them —
        # the sweep tracked 0 books. Only genuinely lowercase occurrences disqualify a name.
        low_counts.update(re.findall(r"(?<![A-Za-z])([a-z][a-z\-]{3,})", body))
    scored = []
    for term, n in cap_counts.items():
        # a real NAME is (almost) never lowercase in the same book; a capitalized common word is
        if n < 3 or low_counts.get(term, 0) > n or term in _STOP or term in _SELF_WORDS                 or term in _WORLD_WORDS or term in tainted:
            continue
        df = doc_freq.get(term, 0)
        if df > max(2, n_books // 8):
            continue
        scored.append((n / (1 + df), term))
    for term, n in hyph_counts.items():
        if n < 3 or term in tainted or doc_freq.get(term, 0) > 2:
            continue
        scored.append((n / (1 + doc_freq.get(term, 0)), term))
    scored.sort(reverse=True)
    return [t for _s, t in scored[:MAX_TERMS]]


class _ReadingGroups:
    """J-1922 / F-2549: ONE pass over origin='reading' replacing, per book, (a) the doc-frequency scan `content LIKE
    '[From 'title'%' LIMIT 120` (289 scans, ~68 s) and (b) _signatures' full read of the book's fragments (124 reads,
    ~33 s). The pass uses the SAME plan and therefore the SAME row order as those queries (`WHERE origin='reading'`,
    idx_origin = rowid order), so "the first 120 matching rows" is the same 120 rows. A row belongs to title T iff its
    text starts with `[From 'T'` under SQLite's LIKE (ASCII-only case folding, NUL-truncated): for a title with no
    `'` that is exactly "the text between `[From '` and the NEXT quote equals T, ASCII-case-insensitively", which is
    how rows are keyed here (two titles differing only in ASCII case share a row group, as LIKE makes them). A title
    containing a LIKE wildcard (`%`, `_`), a quote or a NUL is not handled: for_title()/seen_for() return None and
    sweep() runs the old SQL for that title. `keep_titles` (the stale books) get every content kept, in order."""

    def __init__(self, conn, titles, keep_titles):
        from core import like_scan
        ls = like_scan
        self._ls = ls
        self._tokens_cap = 120
        self._plain = lambda t: ls.is_plain_needle(t) and "'" not in t
        want = {ls.ascii_lower(t) for t in titles if self._plain(t)}
        keep = {ls.ascii_lower(t) for t in keep_titles if self._plain(t)}
        self._n: dict = {}
        self._seen: dict = {}
        self._rows: dict = {k: [] for k in keep}
        for r in conn.execute("SELECT content FROM memory_fragments WHERE origin='reading'"):
            c = r["content"]
            if c is None:
                continue
            if not isinstance(c, str):
                raise ls.Unsupported("non-text reading content")
            if c[:7].translate(ls._LOWER) != "[from '":
                continue
            j = c.find("'", 7)
            if j < 0:
                continue
            nul = c.find("\x00")
            if 0 <= nul <= j:          # LIKE stops at the NUL before it can see the closing quote
                continue
            key = c[7:j].translate(ls._LOWER)
            if key not in want:
                continue
            n = self._n.get(key, 0) + 1
            self._n[key] = n
            if n <= self._tokens_cap:
                self._seen.setdefault(key, set()).update(_tokens(c.split("]", 1)[-1]))
            if key in keep:
                self._rows[key].append(c)

    def seen_for(self, title: str):
        """The token set the old doc-frequency loop built for `title` (union over its first 120 rows), or None."""
        if not self._plain(title):
            return None
        return self._seen.get(self._ls.ascii_lower(title), set())

    def rows_for(self, title: str):
        """Every reading content of `title`, in table order, or None (title not kept / not plain)."""
        if not self._plain(title):
            return None
        return self._rows.get(self._ls.ascii_lower(title))


class _SelfRows:
    """J-1922 / F-2549: the self-origin rows read ONCE, replacing 842 per-term statements
    `SELECT origin, content, timestamp ... WHERE origin IN (4 self origins) AND timestamp > ? AND content LIKE %term%
    ORDER BY timestamp DESC LIMIT 6` (~195 s). Rows come from the same idx_origin scan the old statements used (so rows
    with EQUAL timestamps keep the old statements' tie order -- the sorter is stable on scan order; verified against a
    scratch SQLite in scripts/test_sleep_single_pass_unit.py) and are stably sorted newest-first; top() then returns the
    first 6 rows that contain the term (ASCII-case-insensitive substring, exactly LIKE) with timestamp > thr. The
    word-boundary regex confirmation stays with the caller, applied AFTER the LIMIT as before."""

    def __init__(self, conn):
        from core import like_scan
        ph = ",".join("?" * len(SELF_ORIGINS))
        rows = [(r["origin"], r["content"], r["timestamp"]) for r in conn.execute(
            f"SELECT origin, content, timestamp FROM memory_fragments WHERE origin IN ({ph})", SELF_ORIGINS)]
        for _o, _c, ts in rows:
            if isinstance(ts, bool) or not isinstance(ts, (int, float)):
                raise like_scan.Unsupported("non-numeric timestamp")
        rows.sort(key=lambda r: -r[2])           # stable: equal timestamps stay in scan order
        self._rows = rows
        self._negts = [-r[2] for r in rows]       # ascending
        self._idx = like_scan.LikeIndex([r[1] for r in rows])

    def top(self, term: str, thr: float) -> list:
        """The old statement's (origin, content, timestamp) rows, newest first, at most 6, for `term`, or None."""
        if not _is_plain(term):
            return None
        stop = bisect.bisect_left(self._negts, -thr)       # rows with timestamp > thr
        out = []
        for i in self._idx.iter_matches(term, stop):
            out.append(self._rows[i])
            if len(out) == 6:
                break
        return out


def _is_plain(term) -> bool:
    from core import like_scan
    return like_scan.is_plain_needle(term)


def sweep() -> dict:
    """One residue pass over every stale book. Called from the sleep batch (beside grounded_learning);
    zero LLM calls, pure DB reads + one jsonl append. Fail-open; never raises into sleep."""
    out = {"books_tracked": 0, "books_with_residue": 0, "unstuck": 0}
    try:
        from core.memory.store import _connect
        now = time.time()
        with _connect() as conn:
            spans = _book_spans(conn)
            if not spans:
                _skip("no reading spans found")
                return out
            stale = {t: s for t, s in spans.items()
                     if (now - s[1]) > STALE_DAYS * 86400 and s[2] >= MIN_FRAGS}
            if not stale:
                _skip("no stale books yet", books_total=len(spans))
                return out
            # Guard 2, v2.2: the global tainted-vocabulary set is GONE. With his reading volume,
            # the union of the last 14 days' book vocabulary covers most of English, and the first
            # v2 sweep filtered every signature of every book ("no clean signatures" x9). The
            # guard's principle survives but moved to where it is true: PER-HIT and TIME-AWARE,
            # below — a hit only loses credit if the term appeared in something he READ in the
            # 14 days before THAT thought.
            tainted: set = set()
            # document frequency across books, for distinctiveness
            doc_freq: collections.Counter = collections.Counter()
            # J-1922 / F-2549: ONE pass over the reading rows and ONE over the self-origin rows replace the per-title
            # doc-frequency scans, the per-book full reads and the per-term LIKE scans below (any failure or an
            # unreproducible title/term -> the original per-statement SQL, unchanged).
            groups = selfrows = None
            try:
                from core import like_scan
                if like_scan.SWEEPS_SINGLE_PASS:
                    groups = _ReadingGroups(conn, spans, stale)
                    selfrows = _SelfRows(conn)
            except Exception as exc:
                logger.debug("[book-residue] single-pass setup failed, using per-term SQL: %s", exc)
                groups = selfrows = None
            for t in spans:
                seen = groups.seen_for(t) if groups is not None else None
                if seen is None:
                    seen = set()
                    for r in conn.execute("SELECT content FROM memory_fragments WHERE origin='reading' "
                                          "AND content LIKE ? LIMIT 120", (f"[From '{t}'%",)):
                        seen.update(_tokens((r["content"] or "").split("]", 1)[-1]))
                doc_freq.update(seen)

            books = []
            ph = ",".join("?" * len(SELF_ORIGINS))
            for title, (lo, hi, n) in sorted(stale.items(), key=lambda kv: kv[1][1]):
                terms = _signatures(conn, title, doc_freq, len(spans), tainted,
                                    rows=groups.rows_for(title) if groups is not None else None)
                if not terms:
                    _skip("no clean signatures", book=title[:60])
                    continue
                hits = []
                for term in terms:
                    # LIKE narrows cheaply; the word-boundary regex CONFIRMS (v2 — 'tump' must
                    # never again score a hit inside "stump").
                    rx = re.compile(chr(92) + "b" + re.escape(term) + chr(92) + "b", re.I)
                    top = selfrows.top(term, hi + LAG_DAYS * 86400) if selfrows is not None else None
                    if top is not None:
                        top = [{"origin": o, "content": c, "timestamp": t} for (o, c, t) in top]
                    else:
                        top = conn.execute(
                            f"SELECT origin, content, timestamp FROM memory_fragments WHERE origin "
                            f"IN ({ph}) AND timestamp > ? AND content LIKE ? "
                            "ORDER BY timestamp DESC LIMIT 6",
                            (*SELF_ORIGINS, hi + LAG_DAYS * 86400, f"%{term}%"))
                    for r in top:
                        if not rx.search(r["content"] or ""):
                            continue
                        hits.append({"term": term, "origin": r["origin"],
                                     "ts": round(float(r["timestamp"]), 1),
                                     "text": " ".join((r["content"] or "").split())[:180]})
                hits = hits[:12]
                books.append({"book": title[:80], "last_read_days": round((now - hi) / 86400),
                              "frags": n, "signatures": terms, "residue_hits": len(hits),
                              "by_origin": dict(collections.Counter(h["origin"] for h in hits)),
                              "samples": hits[:3]})
            out["books_tracked"] = len(books)
            out["books_with_residue"] = sum(1 for b in books if b["residue_hits"])
            # UNSTUCK detection: residue in a prior sweep, zero now (the Black Bear pattern)
            prior: dict = {}
            try:
                for line in open(_LOG, encoding="utf-8"):
                    rec = json.loads(line)
                    if rec.get("kind") == "sweep" and rec.get("sig_ver") == 2:
                        for b in rec.get("books", []):
                            prior[b["book"]] = b.get("residue_hits", 0)
            except FileNotFoundError:
                pass
            for b in books:
                if prior.get(b["book"], 0) > 0 and b["residue_hits"] == 0:
                    b["unstuck"] = True
                    out["unstuck"] += 1
            # sig_ver stamps the signature scheme; unstuck-comparison must never cross schemes
            _log_rec({"ts": round(now, 1), "kind": "sweep", "sig_ver": 2, **out, "books": books})
            logger.info("[book-residue] sweep: %d stale books, %d with live residue, %d unstuck",
                        out["books_tracked"], out["books_with_residue"], out["unstuck"])
    except Exception as exc:
        logger.debug("[book-residue] sweep failed (non-fatal): %s", exc)
        _skip("sweep-error", err=repr(exc)[:120])
    return out


async def sweep_offprocess() -> dict:
    """sweep() in a spawned child (J-2384 / F-3082): same paths, same D-0353 fence state, same log lines,
    same sweep record; the caller awaits it. Fail-open: a child failure returns the zero dict sweep()
    returns on error and records a skip row here (the parent writes it after the child has exited)."""
    from core import sleep_offloop
    zero = {"books_tracked": 0, "books_with_residue": 0, "unstuck": 0}
    return await sleep_offloop.off_process(
        "core.book_residue", "sweep", zero=zero, mirror=_OFFPROCESS_MIRROR,
        on_fail=lambda why: _skip("subprocess-error", err=str(why)[:200]))


def status() -> dict:
    """HUD/pulse read — from the LOG only (no DB scans on a dashboard refresh)."""
    if not _LOG.exists():
        return {"sweeps": 0, "why": "no sweep has run yet — fires in the sleep batch"}
    try:
        from core.shadow_log import tail_rows as _tail_rows
        # Bounded tail read (J-0278/F-0335): "sweeps" now caps at the window; the panel reads sw[-1].
        sweeps = _tail_rows(_LOG, 1000)
    except Exception as e:
        return {"sweeps": 0, "why": f"log unreadable: {e!r}"}
    sw = [s for s in sweeps if s.get("kind") == "sweep"]
    if not sw:
        skips = collections.Counter(s.get("reason") for s in sweeps if s.get("kind") == "skip")
        return {"sweeps": 0, "skips": dict(skips)}
    last = sw[-1]
    top = sorted(last.get("books", []), key=lambda b: -b.get("residue_hits", 0))
    return {"sweeps": len(sw), "books_tracked": last.get("books_tracked"),
            "books_with_residue": last.get("books_with_residue"),
            "unstuck": last.get("unstuck"),
            "top_residue": [(b["book"][:44], b["residue_hits"], b["by_origin"]) for b in top[:4]
                            if b.get("residue_hits")],
            "faded": [b["book"][:44] for b in last.get("books", []) if b.get("unstuck")]}
