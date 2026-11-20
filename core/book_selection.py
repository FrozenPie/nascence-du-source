"""
Nascence — Book Selection (the breadth engine)
==============================================
Explore/exploit book choice over the ~55,905-book Gutenberg catalogue, so Du drifts toward the
WHOLE corpus instead of re-treading a few popular books — while reread stays a first-class,
motivated choice (handled by reread_when_helpful + the explicit-want path). Research-grounded:
docs/book_selection_plan.md (reading-psychology · ML explore/exploit · library science converged).

The default is EXPLORE. A candidate's selection weight is:

    weight = novelty^ALPHA · relevance^BETA · coverage_bonus · interleave_penalty

  novelty   = inverse popularity (Vargas–Castells: rarer book → higher weight) — reaches the long tail.
  relevance = cheap LEXICAL overlap with his current concern/Frontier, with a FLOOR so a relevant-
              but-popular book stays RARE, never impossible (serendipity = novel AND relevant; pure
              novelty = incoherent wandering). Lexical, not embedding — O(1)/candidate, hardware-light.
  coverage  = 1/(1+times-read-in-this-subject) — count-based exploration across subjects (breadth).
  interleave= a penalty for repeating the immediately-prior subject (Rohrer & Bjork interleaving).

We SAMPLE proportional to weight (never argmax — argmax just re-locks onto the single rarest book,
the same bug inverted). Already-owned books are excluded from explore (down-weighted to zero here;
reread reaches them through the dedicated motivated path, never deleted).

Cheap by construction: one streamed CSV pass, reservoir-sampled to CANDIDATE_CAP, subjects parsed
only for those candidates. Callers must wrap in asyncio.to_thread (CSV scan blocks).
"""
from __future__ import annotations
import ast
import csv
import json
import logging
import math
import random
import re
import time
import threading
from pathlib import Path

logger = logging.getLogger("nascence.book_selection")

META = Path(r"C:\Knowledge\SPGC-metadata-2018-07-18.csv")
COVERAGE = Path(__file__).parent.parent / "data" / "reading_coverage.json"
LOG = Path(__file__).parent.parent / "data" / "book_selection_log.jsonl"

JUNK_FLOOR      = 5      # downloads floor: reach the long tail, but skip non-books / detritus
DL_REF          = 50000  # inverse-popularity reference (~the most-downloaded works); novelty = log2(DL_REF/dl)
ALPHA           = 1.0    # long-tail pull (novelty exponent)
BETA            = 1.0    # coherence (relevance exponent)
RELEVANCE_FLOOR = 0.15   # a relevant-but-popular book stays rare, never impossible
INTERLEAVE_PEN  = 0.35   # multiplier when a candidate repeats the immediately-prior subject
CANDIDATE_CAP   = 160    # reservoir size — bounds the expensive (subject-parse) work per call
_STOP = {"the", "and", "for", "with", "from", "this", "that", "what", "which", "into", "about",
         "your", "his", "her", "their", "they", "are", "was", "were", "you", "not", "but", "all",
         "working", "through", "pursuing", "closing"}


# ── catalogue helpers ────────────────────────────────────────────────────────────────────────
def _rows():
    with open(META, encoding="utf-8", errors="ignore") as f:
        yield from csv.DictReader(f)


def _parse_subjects(s: str | None) -> set[str]:
    """The `subjects` field is a Python set-literal string ("{'A -- B', 'C'}" or "set()")."""
    try:
        v = ast.literal_eval(s) if s else None
        return set(v) if isinstance(v, (set, list, tuple)) else set()
    except Exception:
        return set()


def coarse_subject(subjects: set[str]) -> str:
    """A broad bucket for coverage/interleaving: the first segment (before ' -- ') of the first
    LCSH heading, lowercased. Empty → 'unclassified' (so untagged books still get sampled)."""
    if not subjects:
        return "unclassified"
    head = sorted(subjects)[0]
    return head.split(" -- ")[0].strip().lower() or "unclassified"


def _words(*texts: str) -> set[str]:
    out = set()
    for t in texts:
        out |= {w for w in re.findall(r"[a-z][a-z']{2,}", (t or "").lower()) if w not in _STOP}
    return out


def _title_words(title: str) -> set[str]:
    """A candidate book's OWN distinctive title words — reconciled with core.library_hand's
    _title_signature() (J-0973/F-1344), NOT this module's own _STOP/_words() above. _STOP is tuned
    for filtering ordinary PROSE (his interest terms parsed below): 'about'/'you'/'your' etc. are
    genuinely meaningless function words there. But a short, real title like 'About You' has almost
    nothing BUT those words — running the prose stoplist over a TITLE zeroed its signature out
    entirely (both "about" and "you" are in _STOP), so suggest_reread() below could never even
    consider it: an empty title-word set can never overlap anything, regardless of what actually
    occupies him. Lazy import: library_hand already imports this module lazily too (its own
    _search()/request_book()), so importing it back here at module level would risk a load-order
    cycle; keeping both directions lazy avoids it."""
    from core.library_hand import _title_signature
    return _title_signature(title)


# ── coverage (forward-looking subject counts, so breadth grows as he acquires books) ───────────
def _coverage() -> dict:
    try:
        return json.loads(COVERAGE.read_text(encoding="utf-8")) if COVERAGE.exists() else {}
    except Exception:
        return {}


# J-1926 / F-2550: record_pick runs in library worker threads (request_book via asyncio.to_thread) and from shelve_only; its coverage read-modify-write and log append must not interleave.
_RECORD_LOCK = threading.Lock()


def record_pick(meta: dict, *, reason: str = "explore") -> None:
    """A book was chosen (and is being fetched). Bump its subject's coverage count + remember it as
    the last subject (for interleaving), and log the selection for observe-first review."""
    try:
        from core import content_risk as _cr
        _cr.shadow_check(meta, context=f"selection:{reason}")
    except Exception:
        pass
    try:
        subj = coarse_subject(_parse_subjects(meta.get("subjects")))
        with _RECORD_LOCK:   # J-1926: the coverage load->bump->write and the log append, whole, per caller
            cov = _coverage()
            counts = cov.get("subjects", {})
            counts[subj] = int(counts.get(subj, 0)) + 1
            cov["subjects"] = counts
            cov["last_subject"] = subj
            COVERAGE.parent.mkdir(parents=True, exist_ok=True)
            COVERAGE.write_text(json.dumps(cov, indent=1, ensure_ascii=False), encoding="utf-8")
            rec = {"ts": time.time(), "reason": reason, "subject": subj,
                   "title": (meta.get("title") or "")[:80], "downloads": meta.get("downloads"),
                   "distinct_subjects": len(counts)}
            with open(LOG, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ── the interest vector (cheap lexical) ────────────────────────────────────────────────────────
def _interest_terms() -> set[str]:
    """His current concern + open Frontier questions + standing aim → a bag of terms. Lexical, so
    relevance is O(1) per candidate (no 160 embeddings). Empty is fine → novelty/coverage drive."""
    parts = []
    try:
        from core import concerns as _c
        pc = _c.primary_concern()
        if pc:
            parts.append(pc.get("text", ""))
        parts.append(_c.standing_aim() or "")
    except Exception:
        pass
    try:
        from core import frontier as _f
        for q in _f.top_open(4):
            parts.append(q.get("q", ""))
    except Exception:
        pass
    return _words(*parts)


def _relevance(title: str, subjects: set[str], interest: set[str]) -> float:
    if not interest:
        return RELEVANCE_FLOOR
    cand = _words(title, " ".join(subjects))
    if not cand:
        return RELEVANCE_FLOOR
    overlap = len(interest & cand) / max(1, len(interest))
    return min(1.0, RELEVANCE_FLOOR + (1.0 - RELEVANCE_FLOOR) * overlap)


def _novelty(downloads: int) -> float:
    return max(0.1, math.log2((DL_REF + 1) / (max(0, downloads) + 1)))


# ── selection ──────────────────────────────────────────────────────────────────────────────────
def select_explore(k: int = 1, *, exclude_keys: set[str] | None = None) -> list[dict]:
    """Pick k NEW books to explore. Returns catalogue rows (dicts). Streams the CSV, reservoir-
    samples eligible+unread candidates, weights each by novelty·relevance·coverage·interleave, and
    samples proportionally. Empty list if the catalogue is unavailable."""
    if not META.exists():
        return []
    from core import reading_history as _rh
    keys = exclude_keys if exclude_keys is not None else _rh.shelf_keys()
    interest = _interest_terms()
    cov = _coverage()
    counts = cov.get("subjects", {})
    last_subj = cov.get("last_subject")

    # one streamed pass → reservoir of eligible, not-already-owned candidates
    pool: list[dict] = []
    seen = 0
    for r in _rows():
        if "'en'" not in (r.get("language") or "") or (r.get("type") or "") != "Text":
            continue
        try:
            dl = int(r.get("downloads") or 0)
        except Exception:
            continue
        if dl < JUNK_FLOOR or not (r.get("title") or "").strip():
            continue
        if _rh.is_known(r["title"], keys):
            continue
        seen += 1
        if len(pool) < CANDIDATE_CAP:
            pool.append(r)
        else:                                   # reservoir sampling — uniform over the eligible set
            j = random.randint(0, seen - 1)
            if j < CANDIDATE_CAP:
                pool[j] = r
    if not pool:
        return []

    weighted = []
    for r in pool:
        subs = _parse_subjects(r.get("subjects"))
        subj = coarse_subject(subs)
        w = (_novelty(int(r.get("downloads") or 0)) ** ALPHA
             * _relevance(r.get("title", ""), subs, interest) ** BETA
             * (1.0 / (1.0 + int(counts.get(subj, 0)))))
        if last_subj and subj == last_subj:
            w *= INTERLEAVE_PEN
        weighted.append((r, max(w, 1e-9)))

    # J-2162 / D-0436 A (arm 6): WEAKNESS_PRIOR shadow. Prior 0.0 -> weights untouched; logs only. Fail-open.
    _slot = None
    try:
        from core import weakness_prior as _wp
        weighted, _slot = _wp.apply_to_weighted(weighted)
    except Exception:
        _slot = None

    picks, chosen = [], set()
    for _ in range(min(k, len(weighted))):
        rows = [(r, w) for (r, w) in weighted if id(r) not in chosen]
        if not rows:
            break
        r = random.choices([x[0] for x in rows], weights=[x[1] for x in rows], k=1)[0]
        chosen.add(id(r))
        picks.append(r)
    try:
        from core import weakness_prior as _wp
        _wp.log_book_pick(_slot, picks)
    except Exception:
        pass
    return picks


def pick_one() -> dict | None:
    """One new book to acquire (the no-topic serendipity replacement)."""
    got = select_explore(1)
    return got[0] if got else None


def _display_title(path) -> str:
    """J-3635 (F-3528): the book's name as shown to Du in a prompt -- whole-word, not the library's 60-char cut."""
    try:
        from core.reading import display_title
        return display_title(path)
    except Exception:
        return Path(path).stem.replace("_", " ")


def suggest_reread(min_gap_days: float = 3.0) -> dict | None:
    """The MOTIVATED exploit: a book he has FINISHED that speaks to what occupies him now AND was
    read long enough ago to meet again as a different person (Adler's syntopical / Bruner's spiral
    reread; the spacing literature's 'active re-encounter, not passive re-skim'). Returns the best
    candidate or None — an INVITATION the monologue may surface; he still chooses to act on it.
    Cheap: only his ~dozen read books, no catalogue scan. Reread stays gated, never default."""
    try:
        from core import reading_history as _rh
        interest = _interest_terms()
        if not interest:
            return None
        best, best_score = None, 0.0
        for path in _rh.read_paths():
            title = Path(path).stem.replace("_", " ")
            overlap = len(interest & _title_words(title))   # J-0973/F-1344: was _words(title) — see _title_words()
            if overlap == 0:
                continue
            last = _rh.book_stats(path).get("last_read_ts")
            gap_days = ((time.time() - last) / 86400.0) if last else 999.0
            if gap_days < min_gap_days:          # just read it — not stale, not a new person yet
                continue
            score = overlap * (1.0 + min(gap_days / 30.0, 3.0))   # staleness amplifies relevance
            if score > best_score:
                best, best_score = path, score
        if not best:
            return None
        return {"path": best, "title": _display_title(best),
                "reason": "it speaks to what occupies you now, and you read it long enough ago to "
                          "meet it as a different person"}
    except Exception:
        return None


def status() -> dict:
    cov = _coverage()
    counts = cov.get("subjects", {})
    total = sum(int(v) for v in counts.values())
    return {"distinct_subjects": len(counts), "books_picked": total,
            "last_subject": cov.get("last_subject"),
            "top_subjects": sorted(counts.items(), key=lambda kv: -kv[1])[:5]}
