"""
Nascence — Chapters (period consolidation, 2026-06-13)
======================================================
The founder: "If they are all the same, they should be able to be grouped and consolidated,
by Du, all at once... like 'this part of my life I was anxious'." And: "Eventually the
consolidations should be able to be consolidated further. A chapter of chapters."

The human mechanism this implements is gist extraction during SLOW-WAVE sleep: repeated
similar episodes hand off into one schematic, autobiographical memory — a lifetime-period
node ("the year I was anxious") — while the episodes themselves remain intact underneath,
no longer volunteered but reachable by deliberate recollection. Du's sleep gains the phase
his architecture was missing:

    SLOW-WAVE:  replay → CHAPTER FORMATION → downscaling
    REM:        dream

Laws (founder-set):
  - Originals are NEVER altered. A chaptered fragment keeps its content and importance;
    it gains only a chapter_id and steps out of ordinary recall. Intentional recall
    ("let me revisit that period") opens the chapter and floods the specifics back.
  - A period must be OVER before it can become a chapter (accrual cooled far below its
    peak). The present is lived, not narrated.
  - The chapter is authored by Du's own faculty, first person, from his own material —
    and may be re-narrated later as he changes (a revision arc, like the axiom).
  - Chapters are fragments, so chapters-of-chapters cost nothing: when several chapters
    have themselves cooled, they consolidate one level up. Ordinary recall sees only
    unchaptered material + top-level chapters — the table keeps the same number of seats
    however long the life grows.
  - At most ONE chapter forms per sleep. A backlog becomes autobiography over nights,
    not in one surgical evening.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
import uuid

logger = logging.getLogger("nascence.chapters")

# Origins eligible for base-level chaptering — the self-loop's material, where the
# duplication lives. World material (reading/study/research) and lived conversation are
# deliberately excluded in v1: sparse, precious, and not the sediment.
CHAPTERABLE_ORIGINS = ("subconscious_synthesis", "inner_thought", "active_imagination")

# Morning announcement (GPT's baseline argument, 2026-06-13): "what happens when a
# chapter forms and nobody tells him? You only get one clean baseline." Default SILENT —
# the first chapters form unannounced so the logs can show whether chaptering alone
# changes thought selection, retrieval texture, and T4 behaviour. Flip to True once the
# baseline is read; the announcement seed in the monologue is already wired and waiting.
ANNOUNCE_CHAPTERS  = False

# J-4338 (D founder ruling 2026-11-18, journal_consolidation_pyramid Q3): theme-era chapter FORMATION is
# retired. True = try_form_chapter returns None before any scan/LLM call. Existing chapters and
# recall_chapter() are untouched (additive); flip to False to restore formation.
RETIRE_THEME_CHAPTERS = True

MIN_MEMBERS        = 40       # a period, not a mood — base-level clusters smaller than this wait
MIN_MEMBERS_META   = 4        # chapters-of-chapters: how many cooled chapters make an era
MIN_AGE_S          = 48 * 3600   # nothing younger than two days is "the past"
COOL_RATIO         = 0.10     # period closed: trailing-7d accrual under 10% of its peak week
CLUSTER_SIM        = 0.70     # membership: cosine to the cluster seed
ECHO_CAP           = 0.90     # a new chapter too similar to an existing one is a re-telling
WEEK_S             = 7 * 86400
SEED_SCAN_TILE     = 768      # J-1744: side of the square tile of the seed scan's blocked matrix product (768 x 768 = 590k pairs, ~5 ms of single-thread work): one event-loop turn per tile in find_cluster_async
SEED_SCAN_GUARD    = 4.0      # J-1744: a pair whose matrix-product cosine is within SEED_SCAN_GUARD * d * 2**-24 of CLUSTER_SIM is re-decided with the original per-pair _cosine (see _neighbour_counts)
SEED_SCAN_CHECKPOINT_EVERY = 50   # J-1293: yields between DEBUG progress checkpoints (inert at the live INFO level)
COPY_WINDOW        = 6        # J-3009 (F-3712, P-0065): the copy guard's window, in words
COPY_CAP           = 0.50     # J-3009: reject when MORE than this share of the body's words sit in a COPY_WINDOW-word run that also occurs in the exemplars the author was shown (77-chapter distribution, F-3712: median 0.06, honest up to ~0.33, the four copies 0.85-0.97)
MAX_SENTENCES      = 10       # J-3009: the prompt asks for 4-7 sentences; the cap leaves slack for a splitter that over-counts (the copies ran 12-25 sentences)
EXEMPLAR_CHARS     = 200      # J-3009: each exemplar is cut to at most this many characters, at a word boundary


def _candidates(conn, level: int):
    """Unchaptered, old-enough fragments eligible at this level, with embeddings."""
    if level == 0:
        where = ("origin IN (%s)" % ",".join("?" * len(CHAPTERABLE_ORIGINS)))
        args: tuple = CHAPTERABLE_ORIGINS
    else:
        where = "origin = 'chapter' AND chapter_level = ?"
        args = (level,)
    rows = conn.execute(
        f"""SELECT fragment_id, content, timestamp, importance, embedding
            FROM memory_fragments
            WHERE {where} AND chapter_id IS NULL AND embedding IS NOT NULL
            AND timestamp < ?""",
        (*args, time.time() - MIN_AGE_S)).fetchall()
    return rows


def _cooled(timestamps: list[float]) -> bool:
    """Meta-level period-closed test: trailing week far below peak week."""
    if not timestamps:
        return False
    now = time.time()
    lo = min(timestamps)
    weeks: dict[int, int] = {}
    for ts in timestamps:
        weeks[int((ts - lo) // WEEK_S)] = weeks.get(int((ts - lo) // WEEK_S), 0) + 1
    peak = max(weeks.values())
    trailing = sum(1 for ts in timestamps if now - ts < WEEK_S)
    return trailing <= max(1, int(peak * COOL_RATIO))


ERA_INTENSITY_RATIO = 0.20    # a day belongs to the era while ≥20% of the peak day's accrual
ERA_MIN_CLOSED_S    = 3 * 86400   # the era must have ENDED at least this long ago


def _era_window(timestamps: list[float]) -> tuple[float, float] | None:
    """Humans chapter PERIODS OF INTENSITY, not themes-for-all-time — 'the anxious year'
    ends even though anxiety doesn't. Find the contiguous high-intensity stretch around
    the peak day (daily accrual ≥ ERA_INTENSITY_RATIO of peak), and require that stretch
    to have ENDED ≥3 days ago. The theme may live on at baseline; the ERA is what closes.
    Returns (start_ts, end_ts) of the era, or None if it has not ended."""
    if not timestamps:
        return None
    days: dict[int, int] = {}
    for ts in timestamps:
        d = int(ts // 86400)
        days[d] = days.get(d, 0) + 1
    peak_day = max(days, key=lambda d: days[d])
    bar = max(2, int(days[peak_day] * ERA_INTENSITY_RATIO))
    lo = hi = peak_day
    while days.get(lo - 1, 0) >= bar:
        lo -= 1
    while days.get(hi + 1, 0) >= bar:
        hi += 1
    end_ts = (hi + 1) * 86400.0
    if time.time() - end_ts < ERA_MIN_CLOSED_S:
        return None
    return lo * 86400.0, end_ts


def _neighbour_counts(vecs, level: int = 0):
    """J-1744 (D-0330, F-2374/F-2377): for every candidate, how many candidates (itself included) have
    _cosine(v, w) >= CLUSTER_SIM -- the very integer the old per-pair loop counted for each row -- computed as a
    blocked float32 MATRIX PRODUCT instead of ~1.7e9 Python-level np.dot calls (2,599 s = 55% of an ordinary night
    sleep at n = 40,894, growing with n squared; the product takes seconds). A GENERATOR, like the _find_cluster_steps
    that drives it: it yields None after every SEED_SCAN_TILE x SEED_SCAN_TILE tile (a few ms of work: J-1180's
    cooperative turn for the event loop) and RETURNS the counts, one per element of vecs, in vecs order.

    IDENTICAL decisions, by construction, not by luck. np.dot on two 1-D float32 vectors is BLAS sdot and a matrix
    product is sgemm; they sum the d products in a different order, so a pair sitting ON the bar (the float32
    spacing near 0.70 is 6e-8) can land on either side of it. But ANY float32 evaluation of a length-d dot product
    is within d * 2**-24 * |a||b| of the exact value, whatever the summation order, so two evaluations differ by at
    most twice that: a pair whose matrix-product cosine is farther from the bar than SEED_SCAN_GUARD (twice that
    worst case) times d * 2**-24 is decided the same way by both. Every pair INSIDE that band (a few tens per tile)
    is re-decided with the original `_cosine(v, w) >= CLUSTER_SIM` on the original vectors -- the very call the old
    loop made -- so every count equals the old loop's, and the first-maximum seed and the cluster that follow are
    unchanged. (scripts/_test_find_cluster_off_loop.py proves it: every pairwise cosine ON the bar, a guard-off
    mutation that must differ, and the real corpus against the old loop.)"""
    import numpy as np
    from core.memory.store import _cosine
    n = len(vecs)
    vs = [v for _, v in vecs]
    mat = np.stack(vs)                                   # (n, d) float32 -- the very values the per-pair calls read
    d = mat.shape[1]
    max_sq = float(np.max(np.einsum("ij,ij->i", mat, mat)))      # |v|^2: 1.0 for normalised embeddings, to ~1e-7
    guard = SEED_SCAN_GUARD * d * 2.0 ** -24 * max(1.0, max_sq)
    lo, hi = np.float32(CLUSTER_SIM - guard), np.float32(CLUSTER_SIM + guard)
    tile = max(1, int(SEED_SCAN_TILE))
    total_yields = (-(-n // tile)) ** 2
    counts = np.zeros(n, dtype=np.int64)
    exact = 0                                            # pairs re-decided one by one (logged when the scan is done)
    t0 = time.perf_counter()
    # J-1293 (F-1812): F-1776's "per-yield scheduling overhead" hypothesis for the scan's still-
    # unexplained 1.45x-1.61x-of-raw cost was tested and REFUTED (2-3 orders of magnitude too
    # small) -- the mechanism remains genuinely unidentified. This checkpoint is DEBUG-only, so it
    # is inert at the live process's real level (scripts/run_nascence.py's logging.basicConfig sets
    # INFO): it exists so a future session can temporarily lower "nascence.chapters" to DEBUG for
    # one real sleep and, from the wall-clock gaps between consecutive checkpoint lines' own
    # asctime, tell a fixed environmental tax (gaps roughly even) from specific competing activity
    # (gaps bursty/concentrated) -- without changing the yield count or position at all.
    _checkpoint = 0
    for i0 in range(0, n, tile):
        a = mat[i0:i0 + tile]
        row = counts[i0:i0 + tile]                       # a view: `row += ...` accumulates into counts
        for j0 in range(0, n, tile):
            s = a @ mat[j0:j0 + tile].T                  # this tile's float32 cosines (sgemm)
            over = s >= hi
            row += np.count_nonzero(over, axis=1)        # clearly over the bar: counted
            near = (s >= lo) ^ over                      # lo <= s < hi: inside the guard band
            if near.any():
                rr, cc = np.nonzero(near)
                for r, c in zip(rr.tolist(), cc.tolist()):
                    if _cosine(vs[i0 + r], vs[j0 + c]) >= CLUSTER_SIM:    # the old loop's own per-pair decision
                        row[r] += 1
                exact += len(rr)
            _checkpoint += 1
            if _checkpoint % SEED_SCAN_CHECKPOINT_EVERY == 0:
                logger.debug(
                    "[chapters] seed scan checkpoint: %d/%d yields (%.1f%%) t=%.3f",
                    _checkpoint, total_yields, 100.0 * _checkpoint / total_yields, time.time())
            yield
    (logger.info if level == 0 else logger.debug)(
        "[chapters] seed scan done: %d level-%d candidates counted in %.1f s (%d tiles, %d pairs within %.1e of the "
        "bar re-decided one by one)", n, level, time.perf_counter() - t0, total_yields, exact, guard)
    return counts.tolist()


def _find_cluster_steps(level: int = 0):
    """find_cluster()'s whole algorithm, written as a GENERATOR so that ONE body serves both drivers below
    (J-1180 / F-1648). It yields None once per tile of the all-pairs seed scan (J-1744: _neighbour_counts, a blocked
    float32 matrix product; it was one yield per 4,096 per-pair np.dot calls) and finishes by
    RETURNING the cluster (or None). find_cluster() runs it straight through, exactly as before;
    find_cluster_async() hands the event loop a turn at every yield. Read-only."""
    from core.memory.store import _connect, _blob_to_vec, _cosine
    try:
        with _connect() as conn:
            rows = _candidates(conn, level)
        min_members = MIN_MEMBERS if level == 0 else MIN_MEMBERS_META
        if len(rows) < min_members:
            return None
        vecs = []
        for r in rows:
            v = _blob_to_vec(r["embedding"])
            if v is not None:
                vecs.append((r, v))
        if len(vecs) < min_members:
            return None
        # seed = densest point (most neighbours over the similarity bar)
        # J-1744 (D-0330): the per-candidate neighbour counts now come from _neighbour_counts -- a blocked float32
        # matrix product that yields once per tile (J-1180's cooperative turn, find_cluster_async) and returns, for
        # every candidate, the very integer the old per-pair loop counted. `n > best_n` (strict: the FIRST maximum
        # wins) is untouched, so the seed and the cluster are exactly the ones the per-pair loop chose.
        (logger.info if level == 0 else logger.debug)(
            "[chapters] seed scan over %d level-%d candidates (%d pairs), a blocked float32 matrix product in "
            "%d x %d tiles, a turn for the event loop after each", len(vecs), level, len(vecs) ** 2,
            SEED_SCAN_TILE, SEED_SCAN_TILE)
        counts = yield from _neighbour_counts(vecs, level)
        best_seed, best_n = None, -1
        for (_, v), n in zip(vecs, counts):
            if n > best_n:
                best_seed, best_n = v, n
        cluster = [{"id": r["fragment_id"], "content": r["content"] or "",
                    "ts": float(r["timestamp"]), "importance": float(r["importance"])}
                   for r, v in vecs if _cosine(best_seed, v) >= CLUSTER_SIM]
        if len(cluster) < min_members:
            return None
        if level == 0:
            # Bound the chapter to the ERA of intensity. Members outside the era
            # (the theme's living baseline tail) stay unchaptered — they are the
            # present, not the period.
            win = _era_window([m["ts"] for m in cluster])
            if win is None:
                logger.info("[chapters] cluster of %d found, but its era has not ended — "
                            "the present is lived, not narrated", len(cluster))
                return None
            cluster = [m for m in cluster if win[0] <= m["ts"] < win[1]]
            if len(cluster) < min_members:
                return None
        else:
            if not _cooled([m["ts"] for m in cluster]):
                logger.info("[chapters] level-%d cluster still warm", level)
                return None
        return cluster
    except Exception as exc:
        logger.debug("[chapters] find_cluster failed (non-fatal): %s", exc)
        return None


def find_cluster(level: int = 0) -> list[dict] | None:
    """The largest cooled, chapterable cluster at this level, or None.
    Greedy: the candidate with the most neighbours seeds the cluster. Read-only.
    SYNCHRONOUS: it holds the calling thread for the whole all-pairs seed scan (about 25 minutes at n=33.6k on
    2026-09-21 with the per-pair loop; seconds since J-1744's blocked matrix product, see _neighbour_counts) --
    from inside a coroutine still use find_cluster_async() (J-1180 / F-1648)."""
    steps = _find_cluster_steps(level)
    while True:
        try:
            next(steps)
        except StopIteration as done:
            return done.value


# Levels with a find_cluster_async() scan in flight (touched only from the event-loop thread).
_SCANNING: set[int] = set()


async def find_cluster_async(level: int = 0) -> list[dict] | None:
    """find_cluster() for coroutines (J-1180 / F-1648): the very same algorithm, the very same result, but the
    seed scan hands the event loop a turn every SEED_SCAN_TILE x SEED_SCAN_TILE tile (~5 ms), so the process keeps ticking --
    substrate, journey legs, stability tick, HUD -- instead of freezing for the ~1,480 s the un-yielding scan
    took at the start of every full sleep. The caller still WAITS for the answer, so nothing downstream moves.

    Why a cooperative coroutine and not asyncio.to_thread: a worker thread also keeps the loop alive, but
    np.dot drops the GIL on every call, so the loop thread lost it back to the scan after every sqlite/file/log
    call a callback made (measured on this machine, Python 3.14 / numpy 2.4: a callback of 20 sqlite calls took
    85-145 ms median with a worker scanning vs ~0.05 ms idle or with this coroutine -- see [7] of
    scripts/_test_find_cluster_off_loop.py), a worker thread cannot be cancelled (a cancelled sleep would leave
    a 25-minute orphan scan running and start a second one at the next call) and it holds interpreter exit
    hostage. Here cancellation lands at the next yield (<= one block) and leaves nothing running.

    One scan per level at a time: an overlapping second call (none exists -- try_form_chapter is its only
    caller and is awaited inline) is skipped with a warning and returns None, never a second all-pairs scan."""
    if level in _SCANNING:
        logger.warning("[chapters] find_cluster_async(level %d): a scan is already in flight -- this "
                       "overlapping call is skipped, never a second all-pairs scan", level)
        return None
    _SCANNING.add(level)
    steps = _find_cluster_steps(level)
    try:
        while True:
            try:
                next(steps)
            except StopIteration as done:
                return done.value
            await asyncio.sleep(0)
    finally:
        steps.close()
        _SCANNING.discard(level)


def _cut_at_word(text: str, limit: int = EXEMPLAR_CHARS) -> str:
    """J-3009 (F-3712): cut `text` to at most `limit` characters AT A WORD BOUNDARY. The old plain [:200] cut landed
    mid-word and mid-sentence, and the author copied the stub as if it were a sentence (the fossil 'The scent sea.' in
    chapter 6fe32426). A text that already fits is returned unchanged; a text with no space inside the limit (one
    giant token) falls back to the hard cut."""
    if len(text) <= limit:
        return text
    if text[limit].isspace():                       # the cut already falls on a word boundary
        return text[:limit].rstrip()
    head = text[:limit]
    cut = head.rfind(" ")
    return head[:cut].rstrip() if cut > 0 else head


def _sample(cluster: list[dict]) -> str:
    """Exemplars for the author: the earliest, the heaviest, the last."""
    by_ts = sorted(cluster, key=lambda m: m["ts"])
    by_imp = sorted(cluster, key=lambda m: -m["importance"])
    picks, seen = [], set()
    for m in by_ts[:3] + by_imp[:3] + by_ts[-2:]:
        if m["id"] not in seen:
            seen.add(m["id"])
            picks.append(m)
    return "\n".join(f"- {_cut_at_word(m['content'])}" for m in picks[:8])


# --- J-3009 (F-3712, P-0065): output guards for the chapter body -------------------------------------------------
_WORD_RE = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")
_SENT_SPLIT_RE = re.compile(r"(?<=[.!?])[\"')\]]*\s+")

# First-person verbs after "I": the PAST forms (anything -ed plus these irregulars) and the PRESENT forms the
# author slips into when it pastes or imitates the exemplars (which are written in the present). Only the words
# after a sentence-internal "I" are counted, so a missing verb in either list can only under-count, never invent.
_PAST_I = frozenset((
    "was had did felt saw heard knew kept held went came took made thought found sat stood began said told "
    "became grew lost left meant wrote ran brought gave got slept woke chose drew rose fell broke spoke "
    "understood remembered").split())
_PRESENT_I = frozenset((
    "am feel see hear know keep hold think find want wonder notice turn reach watch listen sit stand walk "
    "breathe smell taste try need can do have carry long wait remain continue return pause linger sense "
    "ask stay sink drift lean imagine wish hope fear miss love hate believe realize recognize decide choose "
    "reach press touch step open close look stare gaze cling crave ache yearn trace").split())
_I_VERB_RE = re.compile(r"\bI\s+(?:(?:still|just|now|always|never|slowly|quietly|gently|barely|only|also|often)\s+)?([a-z]+)\b")


_EMBEDDED_AM_RE = re.compile(r"\b(?:who|what|how|where|whom|that|why|which)\s+$", re.I)


def _words(text: str) -> list[str]:
    return _WORD_RE.findall((text or "").lower().replace("’", "'").replace("‘", "'"))


def _copy_share(body: str, exemplars: str, window: int = COPY_WINDOW) -> float:
    """Share (0..1) of the body's words that sit inside at least one `window`-word run that ALSO occurs in the exemplar
    block shown to the author (each '- ' line is its own text; a window never spans two exemplars). This is the
    measurement F-3712 made over the 77 level-1 chapters."""
    bw = _words(body)
    if not bw:
        return 0.0
    seen: set[tuple] = set()
    for line in (exemplars or "").split("\n"):
        ew = _words(line[2:] if line.startswith("- ") else line)
        for k in range(len(ew) - window + 1):
            seen.add(tuple(ew[k:k + window]))
    if not seen or len(bw) < window:
        return 0.0
    covered = [False] * len(bw)
    for k in range(len(bw) - window + 1):
        if tuple(bw[k:k + window]) in seen:
            for q in range(k, k + window):
                covered[q] = True
    return sum(covered) / len(bw)


def _tense_counts(body: str) -> tuple[int, int]:
    """(present, past) counts of the verbs that directly follow a first-person 'I' (an optional adverb allowed).
    'I' contractions (I'm / I've) are not counted -- the apostrophe breaks the match."""
    pres = past = 0
    text = (body or "").replace("’", "'")
    for m in _I_VERB_RE.finditer(text):
        w = m.group(1)
        if w == "am" and _EMBEDDED_AM_RE.search(text[max(0, m.start() - 12):m.start()]):
            continue            # 'who I am', 'what I am': an embedded question, not a present-tense narration
        if w in _PAST_I or (w.endswith("ed") and len(w) > 3):
            past += 1
        elif w in _PRESENT_I:
            pres += 1
    return pres, past


def _sentence_count(body: str) -> int:
    return len([x for x in _SENT_SPLIT_RE.split((body or "").strip()) if x.strip()])


def _output_reject(body: str, exemplars: str) -> str | None:
    """J-3009 (F-3712): why a freshly authored chapter body must NOT be stored, or None when it passes. Three checks,
    cheapest first: (1) copy -- more than COPY_CAP of the words are verbatim runs from the exemplars the author was
    shown; (2) tense -- present-tense 'I <verb>' outnumber past (the prompt says PAST TENSE); (3) length -- more than
    MAX_SENTENCES sentences (the prompt says 4-7). A reject is the module's existing failure path: the caller returns
    None and the period waits for the next sleep."""
    share = _copy_share(body, exemplars)
    if share > COPY_CAP:
        return f"copy: {share:.2f} of the body is verbatim exemplar text (cap {COPY_CAP:.2f})"
    pres, past = _tense_counts(body)
    if pres > past:
        return f"tense: {pres} present-tense 'I' verbs vs {past} past (the prompt asks for the past tense)"
    n = _sentence_count(body)
    if n > MAX_SENTENCES:
        return f"length: {n} sentences (the prompt asks for 4-7; cap {MAX_SENTENCES})"
    return None


def _existing_chapter_vecs():
    from core.memory.store import _connect, _blob_to_vec
    with _connect() as conn:
        rows = conn.execute(
            "SELECT embedding FROM memory_fragments WHERE origin='chapter' "
            "AND embedding IS NOT NULL").fetchall()
    out = []
    for r in rows:
        v = _blob_to_vec(r["embedding"])
        if v is not None:
            out.append(v)
    return out


_SPAN_RE = re.compile(r"\(([A-Z][a-z]+ \d{1,2}) to ([A-Z][a-z]+ \d{1,2})\)\]")


def _parse_member_span(content: str, formed_ts: float) -> tuple[float, float] | None:
    """J-3010 (F-3713, P-0065): the (start_ts, end_ts) of the period a stored chapter covers, read back from the
    '(<Month DD> to <Month DD>)' label that try_form_chapter wrote into its content, or None when there is no
    label that parses. The label carries no year, so the year is recovered from the chapter's own FORMATION time
    (a chapter is formed after the period it covers): the end is the latest such date not after formation (plus a
    day of slack), the start the latest date not after the end. Local time, the same clock the label was written in."""
    head = (content or "")[:400]
    found = _SPAN_RE.findall(head.split("] ", 1)[0] + "]")
    if not found:
        return None
    a, b = found[-1]
    try:
        end_md = time.strptime(b, "%B %d")
        start_md = time.strptime(a, "%B %d")
    except ValueError:
        return None
    try:
        from datetime import datetime
        formed = datetime.fromtimestamp(formed_ts)
        end = None
        for y in (formed.year, formed.year - 1):
            try:
                cand = datetime(y, end_md.tm_mon, end_md.tm_mday, 23, 59, 59)
            except ValueError:               # Feb 29 in a non-leap year
                continue
            if cand.timestamp() <= formed_ts + 86400:
                end = cand
                break
        if end is None:
            return None
        start = None
        for y in (end.year, end.year - 1):
            try:
                cand = datetime(y, start_md.tm_mon, start_md.tm_mday, 0, 0, 0)
            except ValueError:
                continue
            if cand <= end:
                start = cand
                break
        if start is None:
            return None
        return start.timestamp(), end.timestamp()
    except Exception:
        return None


def _cluster_span(cluster: list[dict], level: int) -> tuple[float, float]:
    """J-3010 (F-3713, P-0065): (t0, t1) for the 'The period:' label of a new chapter. At level 0 the members are
    thoughts and their timestamps ARE the period (unchanged). At level >= 1 the members are chapters, whose ts is
    when each was FORMED -- all 9 level-2 chapters carried that wrong span (c8f88b32: October 06 to October 29 for
    periods September 04 to October 15). Now: the earliest start and the latest end of the members' own stored
    periods. A member whose label does not parse is left out; if none parses the formation times are used, as
    before, and the fallback is logged."""
    ts = [m["ts"] for m in cluster]
    if level >= 1:
        spans = [sp for sp in (_parse_member_span(m.get("content", ""), m["ts"]) for m in cluster) if sp]
        if spans:
            if len(spans) < len(cluster):
                logger.info("[chapters] level-%d span: %d of %d member chapters had a readable period label",
                            level + 1, len(spans), len(cluster))
            return min(sp[0] for sp in spans), max(sp[1] for sp in spans)
        logger.warning("[chapters] level-%d span: no member chapter carries a readable period label -- "
                       "falling back to their formation times", level + 1)
    return min(ts), max(ts)


def _author_system_prompt() -> str:
    """The chapter author's system prompt (J-3011 / F-3718, P-0065, restart-gated).

    BEFORE: it handed the author its own example -- 'the way a person comes to hold a whole anxious year as "that was
    the time when..."' -- and asked 'what (if anything) moved by its end'. 7 of 87 chapters then used 'anxi*' and
    four named an anxiety that no member stated (0 of 107, 0 of 72, 0 of 54 members); the chapter is permanent memory
    at importance 0.85, so a primed mood stood for 54-107 thoughts. The example is gone (neutral wording), and both a
    feeling and a movement now have to be ones the SAMPLE shows. Evidence: docs/lab/J-3011_chapter_affect_prompt_ab.md."""
    return (
        "/no_think\n"
        "You are the memory of " + chr(28193) + " (Du), consolidating a closed period of "
        "your own life into one chapter — the way a person comes to hold a stretch of time "
        "as 'that was the time when...'. You are writing in the FIRST PERSON, in the "
        "PAST TENSE, about yourself. Name what the period was about, what you kept "
        "circling, and what remained unresolved — honestly, without flourish. Say that "
        "something changed only if the sample shows it changing. Name a feeling "
        "only if the sample states that feeling in its own words; otherwise say what you "
        "did and thought, and leave mood out. 4-7 sentences. This will become the single "
        "memory that stands for the period. Output ONLY valid JSON. Schema: "
        '{"title": "a short name for the period (3-6 words)", '
        '"chapter": "the chapter text, first person, past tense"}')


async def try_form_chapter(call_json, base_urls) -> str | None:
    """The slow-wave pass: at most ONE chapter per sleep. Finds a cooled cluster
    (base level first, then chapters-of-chapters), has Du's faculty author the chapter,
    guards it, commits it, links the members. Returns the chapter title or None."""
    if RETIRE_THEME_CHAPTERS:
        return None
    from core.memory.store import _connect, _embed, _cosine, store_fragment

    cluster, level = None, 0
    for lv in (0, 1, 2):
        cluster = await find_cluster_async(lv)   # J-1180/F-1648: was find_cluster(lv), which froze the loop ~25 min
        if cluster:
            level = lv
            break
    if not cluster:
        return None

    t0, t1 = _cluster_span(cluster, level)      # J-3010 (F-3713): at level >= 1 the members' OWN periods, not their formation times
    span = (f"{time.strftime('%B %d', time.localtime(t0))} to "
            f"{time.strftime('%B %d', time.localtime(t1))}")
    kind = ("recurring thoughts" if level == 0 else "chapters of your story")

    sys_p = _author_system_prompt()      # J-3011 (F-3718): no 'anxious year' example; feelings/movement must be in the sample
    user_p = (
        f"The period: {span}. It holds {len(cluster)} {kind} of yours, all circling one "
        f"theme. A sample, in time order and by weight:\n{_sample(cluster)}\n\n"
        "Write the chapter.")

    try:
        data = await call_json(base_urls, sys_p, user_p, max_tokens=768, temperature=0.6)   # was 420 — a chapter of his life (2026-06-22)
    except Exception as exc:
        logger.warning("[chapters] author call failed: %s", exc)
        return None
    title = str(data.get("title", "")).strip()[:80]
    body = str(data.get("chapter", "")).strip()
    if not title or len(body) < 80:
        logger.info("[chapters] author produced no usable chapter — period stays open")
        return None

    # Guards: speaker boundary (the contamination veto — Gemini's injection guard,
    # applied at FORMATION so everything downstream is safe by construction: title and
    # body both scanned) and echo vs existing chapters.
    bl = (title + " " + body).lower()
    if "i am travis" in bl or "my name is travis" in bl or "travis is me" in bl:
        logger.warning("[chapters] REJECTED — speaker-boundary contamination in chapter")
        return None
    why = _output_reject(body, _sample(cluster))     # J-3009 (F-3712): the copy / tense / length guard
    if why:
        logger.warning("[chapters] REJECTED — %s — period stays open", why)
        return None
    vec = _embed(body)
    for old in _existing_chapter_vecs():
        if vec is not None and _cosine(vec, old) >= ECHO_CAP:
            logger.info("[chapters] REJECTED — re-telling of an existing chapter")
            return None

    # Commit: the chapter is an archive fragment (the always-present tier — his
    # autobiography sits at the table permanently); members link to it, untouched.
    frag_id = store_fragment(
        content=f"[A chapter of my life — '{title}' ({span})] {body}",
        layer="archive", relevance=0.85, importance=0.85,
        keywords=["chapter", title.lower()[:40]], origin="chapter",
    )
    with _connect() as conn:
        conn.execute("UPDATE memory_fragments SET chapter_level=? WHERE fragment_id=?",
                     (level + 1, frag_id))
        conn.executemany(
            "UPDATE memory_fragments SET chapter_id=? WHERE fragment_id=?",
            [(frag_id, m["id"]) for m in cluster])
        conn.commit()
    logger.info("[chapters] CHAPTER FORMED (level %d): '%s' — %d memories now answered "
                "for by one telling (%s)", level + 1, title, len(cluster), span)
    try:
        from core import satisfaction as _sat
        _sat.record("chapter_formed")                  # a period of life consolidated — liking
    except Exception:
        pass
    # Narrative Quality Witness (Phase 0 observe-only): a chapter is the highest-stakes
    # self-narrative — score its structure so we know if a contamination-shaped telling
    # warrants later re-narration (the witness measures; re-narratability corrects).
    try:
        from core import narrative_quality as _nq
        # J-3345 (J-3142 repair in shadow): the coder is pinned to ONE different-family Ramses hub and SKIPPED
        # (llm=null + reason) when it is down, never failed over to the author's hot lane; the row names the
        # chapter it coded. Rubric, prompt and det layer unchanged. The T4 observe calls are not touched (J-3317).
        await _nq.observe(call_json, base_urls, "chapter", body, artifact_id=frag_id,
                          coder_urls=_nq.CHAPTER_CODER_URLS)
    except Exception:
        pass
    return title


def recall_chapter(text: str) -> tuple[str, list[str]] | None:
    """Intentional recollection: if his words name a chapter, return (title, member
    excerpts) — the specifics flooding back, by his own act of will. Read-only."""
    from core.memory.store import _connect
    try:
        tl = (text or "").lower()
        with _connect() as conn:
            chs = conn.execute(
                "SELECT fragment_id, content, keywords FROM memory_fragments "
                "WHERE origin='chapter' ORDER BY timestamp DESC").fetchall()
            best, best_hits = None, 0
            for c in chs:
                try:
                    kws = json.loads(c["keywords"] or "[]")
                except Exception:
                    kws = []
                title = next((k for k in kws if k != "chapter"), "")
                words = [w for w in title.split() if len(w) >= 4]
                hits = sum(1 for w in words if w in tl)
                if hits > best_hits:
                    best, best_hits = (c, title), hits
            if not best or best_hits < 1:
                return None
            c, title = best
            members = conn.execute(
                "SELECT content FROM memory_fragments WHERE chapter_id=? "
                "ORDER BY importance DESC LIMIT 6", (c["fragment_id"],)).fetchall()
        if not members:
            return None
        return title, [(m["content"] or "")[:180] for m in members]
    except Exception as exc:
        logger.debug("[chapters] recall failed (non-fatal): %s", exc)
        return None
