"""
Nascence - Grounding Injection + Re-seed, SHADOW (continuous_stream Phase 2 = Rail C.2 + C.3; J-2214,
ruled by Travis 2026-10-16 from T-0089). OBSERVE-ONLY. Nothing in this module changes a seed, a prompt,
a gap, or any decision Du makes. It answers one question with real data before any live flip:

    "When the DMN stream starts restating instead of developing, what grounding source WOULD a Rail C
     injector have handed the next move, from which pool, and would that source have been off the loop?"

THE TRIGGER (Rail C: fire the function the human gap was doing, on STATE not clock). Three redundancy
readings, none of them a new detector:
  topic_lock   - the J-2152 topic-perseveration rule (core/topic_perseveration.py, the detector of record):
                 the same coarse cluster() -- shared quoted anchor term, else cosine >= TOPIC_SIM -- run
                 over the last WINDOW DMN thoughts ACROSS trains (the gauge runs it per day over the
                 orchestrator's internal questions; this runs it rolling over the stream), with the
                 gauge's own FROZEN_SHARE / FROZEN_MIN_N. Fires when the current thought sits in the
                 modal topic and that topic holds >= FROZEN_SHARE of the window.
  restating    - cosine-to-recent ACROSS trains (continuous_stream.md section 4.1: generalise _circling to
                 the between-train scope) >= INTERVENE_SIM (the plan's "intervene >= 0.80").
  circling / slow_loop - the existing per-train _circling and theme_recurrence flags, passed through.
  double_repeat - (J-3335, additive) the sentence-level double repeat: the caller passes the tick-start
                 _bored_streak; >= 2 adds this reason. Rows carry trigger ('double_repeat' when it is the only
                 reason, else the first other reason, None when nothing fired) and double_repeat (bool); old
                 rows have neither field and still parse. Every double_repeat row is logged, cooled down or
                 not (cooldown_blocked says which), so the reader sees the full population (J-3144: ~11/day).
                 Decoupled check: feeds_loop / sim_to_loop come from the pool scorer's loop-cosine, not the
                 pool writer. STOP CONDITIONS: under 100 double_repeat rows after 14 live days (too rare to
                 matter: record and propose archive); a pick that feeds the loop on > 30% of double_repeat
                 would-inject rows; or any write outside data/.
A trigger becomes a would-inject row only outside COOLDOWN_S of the previous one, so the read sees the
rate a live injector would actually fire at, not one row per restating thought.

THE POOLS (World answers, never leads: every candidate is something Du ALREADY ENCOUNTERED; nothing is
fetched, generated or suggested from outside his own record). All reads are non-mutating peeks.
Repaired by J-2364 (F-3053, D-0473 ruled by travis 2026-10-18; rows carry pools_v=2 from then on):
  reading      - a real PASSAGE: the ~320 chars of the current book that end at his bookmark (what he
                 last read; core.reading.current_book()/current_offset(), read-only). The bare title
                 stem (F-3053 d: 'Seeing Europe with Famous Authors' x5) is never offered on its own.
  frontier     - his own open world-questions (core.frontier.top_open(FRONTIER_PEEK), the NON-mutating
                 peek -- never open_question_for_seed(), which marks a question offered). A question
                 that is recurring on the curiosity side (cosine >= FRONTIER_THEME_SIM to at least
                 FRONTIER_THEME_K of the last THEME_N ignited curiosity_log questions) feeds the loop
                 (F-3053 c: 'art of using words properly' / mottainai re-offered).
  percept      - the world's own most recent ANSWERS to his looks (data/life_events.jsonl kind
                 'answer' = rendered to him, a 'line' the world wrote, bounded tail read). Never
                 data/moments.jsonl: every moment there is his own DMN sentence, so the old percept
                 pool was self-echo (F-3053 a: median sim to loop 0.583, never picked). No answer
                 within PERCEPT_MAX_AGE_S -> no percept candidate.
  letter       - a peer letter waiting on him (core.peers._read_thread, read-only)
  conversation - the last real exchange with Travis (state.conversation_history[-1]); D-0440 made
                 conversation one more grounding source, so it is a POOL here, not a separate path.
                 D-0440 itself ruled "judged read first, no build" for conversational_redirect: this
                 only LOGS it as a candidate, it builds nothing for that plan. Farewell sentences are
                 stripped and what is left must carry >= CONVO_MIN_CONTENT content words, within
                 CONVO_MAX_AGE_S (F-3053 b: one goodnight message was 8 of 53 picks, up to 23 h old).
RE-SEED (Rail C.3): among the candidates, the pick is the one LEAST similar to the redundant topic
(cosine to the modal topic's first thought) plus REPEAT_PENALTY per earlier pick of the same candidate
(F-3053 e: 31 distinct texts in 53 picks). A candidate feeds_loop and is never picked if it shares the
loop's quoted anchor term, sits at cosine >= LOOP_SIM to the loop topic (paraphrases the anchor rule
missed), or (frontier) recurs on the curiosity side -- by cosine (theme_recur) or by the loop's lexical
core words (theme_core, see theme_core()); feeds_why says which.

COMPOSITION (read before extending):
  - measurement_to_action arm 5 (J-2186) attacks the CURIOSITY side of the same loop: the orchestrator's
    input_type="internal" question -> add_theme -> CuriosityNode._recent_themes cycle. This module never
    touches that path; it watches only the DMN stream (nodes/inner_monologue_node.py). Not a parallel
    mechanism: different stream, same detector rule.
  - The live boredom redirect / core.boredom escape (_develop_or_branch_seed) already exist. Each row
    carries live_redirect / live_escape so the read can see how often Rail C would fire where those
    did NOT (the only cases a live flip would change).
  - No readout to Du (D-0434): nothing here is shown to him, as a gauge, a percept, or a prompt line.

STORE: data/grounding_injection_shadow.jsonl, one row per DMN thought observed (light), with the pool
candidates and the pick filled only on would-inject rows. Every write resolves profile.guard_path() at the
point of write (a non-live process is refused, NonLiveWriteError propagates out of observe()), and every
append and the rolling buffer are under _LOCK. The caller wraps observe() fail-open.
"""
from __future__ import annotations

import json
import re
import threading
import time
from pathlib import Path

from core import profile

_DATA = Path(__file__).parent.parent / "data"
_LOG = _DATA / "grounding_injection_shadow.jsonl"
_LIFE_EVENTS = _DATA / "life_events.jsonl"    # world-authored answers (core/life.py owns it; read-only here)
_CURIOSITY_LOG = _DATA / "curiosity_log.jsonl"  # nodes/curiosity_node.py owns it; read-only tail here
DOUBLE_REPEAT_STREAK = 2   # J-3335: tick-start _bored_streak at/above which the double_repeat trigger applies
POOLS_V = 2             # J-2364 repaired pools; rows before it have no pools_v field

WINDOW = 12             # last N DMN thoughts (across trains) the topic rule runs over
WINDOW_MAX_AGE_S = 6 * 3600   # a thought older than this drops out of the window (a restart gap is not a loop)
INTERVENE_SIM = 0.80    # continuous_stream.md section 4.1: advisory >= 0.70, intervene >= 0.80
ADVISORY_SIM = 0.70
COOLDOWN_S = 600.0      # at most one would-inject per 10 minutes (the rate a live injector would fire at)
PERCEPT_TAIL = 400      # bounded tail read of life_events.jsonl for the percept pool
PERCEPT_MAX_AGE_S = 24 * 3600
PERCEPT_K = 2           # at most this many distinct recent world answers
PERCEPT_MIN_WORDS = 6   # plus _GENERIC_MISS: the world's generic 'Nothing shows itself' is not a ground
CONVO_MAX_AGE_S = 6 * 3600    # J-2364 staleness cut (was 24 h; F-3053 b picks were up to 23 h old)
CONVO_MIN_CONTENT = 7   # distinct content words left after farewell sentences are stripped
READING_EXCERPT = 320   # chars of the passage ending at the bookmark
READING_MIN_WORDS = 8
FRONTIER_PEEK = 8       # peek deeper than 3 so a non-looping question can still surface
THEME_N = 12            # last N ignited curiosity questions (curiosity_log tail)
FRONTIER_THEME_SIM = 0.60   # calibrated on the J-2288 rows (F-3053): K=2 caught 124/140 loop-pattern
FRONTIER_THEME_K = 2        # frontier candidates and 1/19 others (that one: 'proper word usage', a paraphrase)
CORE_MIN = 3            # theme_core: a word in >= this many of the last THEME_N questions...
CORE_DF = 0.05          # ...and in < 5% of the long baseline (recent ones discounted) is the loop's lexical core
CORE_TAIL_BYTES = 2 * 1024 * 1024   # long baseline = last 2 MB of curiosity_log (~800 ignited questions)
LOOP_SIM = 0.55         # = topic_perseveration.TOPIC_SIM: cosine to the loop topic that counts as same topic
REPEAT_PENALTY = 0.15   # added to sim_to_loop per earlier pick of the same candidate
REPEAT_SEED_N = 2000    # log tail rows read once to seed the pick counts across a restart

_LOCK = threading.Lock()
_buf: list[dict] = []           # {ts, text, vec}
_last_inject_ts = 0.0
_pick_counts: dict[str, int] = {}
_picks_seeded = False


def _now() -> float:
    return time.time()


def _cos(a, b) -> float | None:
    try:
        if a is None or b is None:
            return None
        return float(a @ b)
    except Exception:
        try:
            return float(sum(float(x) * float(y) for x, y in zip(a, b)))
        except Exception:
            return None


def _default_embed(text: str):
    try:
        from core.memory.store import _embed
        return _embed(text)
    except Exception:
        return None


# -- the redundancy reading (detector of record = topic_perseveration's rule) ------------------------
def redundancy(text: str, vec, window: list[dict]) -> dict:
    """Pure: topic-lock + cross-train cosine reading of `text` against `window` (oldest first, each
    {text, vec}). Returns the reading; never mutates."""
    from core import topic_perseveration as tp
    items = list(window) + [{"text": text, "vec": vec}]
    texts = [it["text"] for it in items]
    vmap = {}
    for it in items:
        vmap.setdefault(it["text"], it["vec"])
    labels, method = tp.cluster(texts, embed=lambda q: vmap.get(q))
    cur = labels[-1]
    n = len(labels)
    cnt: dict[int, int] = {}
    for lb in labels:
        cnt[lb] = cnt.get(lb, 0) + 1
    modal_lb, modal_n = max(cnt.items(), key=lambda kv: (kv[1], -kv[0]))
    modal_share = modal_n / n if n else 0.0
    first_idx = labels.index(modal_lb)
    topic_lock = bool(n >= tp.FROZEN_MIN_N and cur == modal_lb and modal_share >= tp.FROZEN_SHARE)
    sims = [s for s in (_cos(vec, it["vec"]) for it in window) if s is not None]
    cos_max = max(sims) if sims else None
    return {"n": n, "topics": len(cnt), "modal_share": round(modal_share, 3), "in_modal": cur == modal_lb,
            "topic_lock": topic_lock, "method": method, "cos_recent_max": None if cos_max is None else round(cos_max, 3),
            "modal_first_text": texts[first_idx], "modal_first_vec": items[first_idx]["vec"],
            "modal_anchors": sorted(tp.anchors_of(texts[first_idx]))}


# -- the pools (read-only peeks at what Du already encountered) -------------------------------------
def _words(t: str) -> int:
    return len(str(t or "").split())


def excerpt_before(text: str, offset: int, n: int = READING_EXCERPT) -> str:
    """Pure: the last ~n chars of `text` that end at `offset` (what was just read), starting at a sentence
    boundary when one is near, whitespace collapsed. '' when nothing has been read yet."""
    try:
        offset = max(0, min(int(offset), len(text or "")))
    except Exception:
        return ""
    if offset <= 0:
        return ""
    chunk = text[max(0, offset - 2 * n):offset]
    tail = chunk[-n:] if len(chunk) > n else chunk
    head_room = chunk[: len(chunk) - len(tail)]
    # start right after a sentence end inside the tail's first half; else back up into head_room for one
    ends = [i for i in (tail.find(". "), tail.find(".\n"), tail.find("? "), tail.find("! ")) if i >= 0]
    cut = min(ends) if ends else -1
    if 0 <= cut < len(tail) // 2:
        tail = tail[cut + 2:]
    elif head_room:
        b = max(head_room.rfind(". "), head_room.rfind(".\n"))
        if b >= 0:
            tail = head_room[b + 2:] + tail
    return " ".join(tail.split())[: 2 * n]


def last_read_book(state: dict) -> tuple[str, int] | None:
    """Pure: (path, offset) of the book with the newest last_read_ts and a real bookmark (offset > 0)."""
    best = None
    for k, v in (state or {}).items():
        if not isinstance(v, dict):
            continue
        try:
            off, ts = int(v.get("offset", 0) or 0), float(v.get("last_read_ts", 0) or 0)
        except Exception:
            continue
        if off > 0 and (best is None or ts > best[2]):
            best = (k, off, ts)
    return (best[0], best[1]) if best else None


def _pool_reading() -> list[dict]:
    """The passage ending at the current book's bookmark; if the current book is not started yet (offset 0,
    a fresh switch), the passage he last read in the most recently read book. Read-only on reading_state."""
    try:
        from core import reading
        book = reading.current_book()
        off = reading.current_offset(book)
        if off <= 0:
            lr = last_read_book(reading._load_state())
            if lr and Path(lr[0]).exists():
                book, off = Path(lr[0]), lr[1]
        stem = book.stem.replace("_", " ").strip()
        ex = excerpt_before(book.read_text(encoding="utf-8", errors="ignore"), off)
        if _words(ex) >= READING_MIN_WORDS:
            return [{"pool": "reading", "text": ex[:300], "ref": f"{stem[:60]} @{off}"}]
    except Exception:
        pass
    return []


def is_recurring_theme(sims: list, k: int = FRONTIER_THEME_K, t: float = FRONTIER_THEME_SIM) -> bool:
    """Pure: does a question sit on a topic the curiosity side keeps returning to?"""
    return sum(1 for x in sims if x is not None and x >= t) >= k


def parse_curiosity_tail(lines: list[str], n: int = THEME_N) -> list[str]:
    """Pure: the last n ignited questions[0] from curiosity_log lines (same reading as
    core/world_displacement._seed_history: F-2889 matched fired internal questions to index 0)."""
    qs = []
    for ln in lines:
        try:
            d = json.loads(ln)
        except Exception:
            continue
        if str(d.get("ignited")).lower() != "true":
            continue
        q = d.get("questions")
        if isinstance(q, str):
            try:
                q = json.loads(q)
            except Exception:
                q = [q]
        if q and isinstance(q, list) and isinstance(q[0], str) and len(q[0].strip()) > 12:
            qs.append(q[0].strip())
    return qs[-n:]


def recent_curiosity_themes(n: int = THEME_N, path: Path | None = None, tail_bytes: int = 256 * 1024) -> list[str]:
    """Bounded read-only tail of curiosity_log.jsonl (default 256 KB). [] on any error."""
    try:
        with open(path or _CURIOSITY_LOG, "rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(max(0, size - tail_bytes))
            tail = fh.read().decode("utf-8", errors="replace").splitlines()[1:]
        return parse_curiosity_tail(tail, n)
    except Exception:
        return []


_CJK = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")


def _qwords(t: str) -> set:
    from core import topic_perseveration as tp
    return {w for w in tp._content(t) if len(w) >= 4 or _CJK.match(w)}


def theme_core(recent: list[str], base: list[str], m: int = CORE_MIN, df: float = CORE_DF) -> set:
    """Pure: the curiosity loop's LEXICAL core -- content words in >= m of the `recent` questions that are
    rare (< df of questions) in the longer `base` once the recent ones are discounted ('mottainai', 'properly',
    'words'; not 'influence' or 'perception', which every question uses). `base` includes `recent`.
    Catches the frontier's stale paraphrases of an older loop that sit below the cosine rule (J-2364 replay
    on the J-2288 rows: alone 119/142 loop-pattern frontier candidates, 0/17 others)."""
    rc: dict = {}
    for t in recent or []:
        for w in _qwords(t):
            rc[w] = rc.get(w, 0) + 1
    bc: dict = {}
    for t in base or []:
        for w in _qwords(t):
            bc[w] = bc.get(w, 0) + 1
    nb = max(1, len(base or []))
    return {w for w, n in rc.items() if n >= m and max(0, bc.get(w, 0) - n) / nb < df}


def loop_core(recent: list[str], base: list[str], loop_text: str, m: int = CORE_MIN) -> set:
    """Pure: theme_core() plus any word recurring in >= m recent curiosity questions that the DMN loop topic
    itself also uses -- the word BOTH streams keep repeating ('mottainai' in a days-long loop is no longer
    rare in the baseline, so theme_core alone misses it). Replay on the J-2288 rows: 121/142 loop-pattern
    frontier candidates, 0/17 others."""
    rc: dict = {}
    for t in recent or []:
        for w in _qwords(t):
            rc[w] = rc.get(w, 0) + 1
    shared = {w for w, n in rc.items() if n >= m} & _qwords(loop_text or "")
    return theme_core(recent, base, m=m) | shared


_core_cache = {"ts": 0.0, "base": []}


def _curiosity_base(now: float) -> list[str]:
    """The long baseline for theme_core: last CORE_TAIL_BYTES of curiosity_log, re-read at most hourly."""
    if now - _core_cache["ts"] > 3600.0 or not _core_cache["base"]:
        _core_cache["base"] = recent_curiosity_themes(10 ** 6, tail_bytes=CORE_TAIL_BYTES)
        _core_cache["ts"] = now
    return _core_cache["base"]


def _pool_frontier() -> list[dict]:
    try:
        from core import frontier
        return [{"pool": "frontier", "text": str(q["q"])[:300], "ref": q.get("source", "")}
                for q in frontier.top_open(FRONTIER_PEEK) if q.get("q")]
    except Exception:
        return []


_GENERIC_MISS = re.compile(r"\s*nothing\b", re.I)   # the generic miss: 'Nothing shows itself; whatever is there keeps still.'


def percept_from_life(rows: list[dict], now: float, k: int = PERCEPT_K) -> list[dict]:
    """Pure: newest-first, up to k DISTINCT world-written answer lines (life_events kind 'answer', i.e.
    rendered to him; 'would_answer' was never shown) within PERCEPT_MAX_AGE_S, >= PERCEPT_MIN_WORDS words."""
    out, seen = [], set()
    for r in reversed(rows or []):
        try:
            if r.get("kind") != "answer" or not r.get("line"):
                continue
            if now - float(r.get("ts", 0)) > PERCEPT_MAX_AGE_S:
                continue
            line = " ".join(str(r["line"]).split())
            if _words(line) < PERCEPT_MIN_WORDS or _GENERIC_MISS.match(line) or line.lower() in seen:
                continue
            seen.add(line.lower())
            out.append({"pool": "percept", "text": line[:300], "ref": r.get("ts")})
            if len(out) >= k:
                break
        except Exception:
            continue
    return out


def _pool_percept(now: float) -> list[dict]:
    try:
        from core.shadow_log import tail_rows
        return percept_from_life(tail_rows(_LIFE_EVENTS, PERCEPT_TAIL), now)
    except Exception:
        return []


def _pool_letter() -> list[dict]:
    try:
        from core import peers
        for k in peers.PERSONAS:
            t = peers._read_thread(k)
            if t and t[-1].get("from") == k and t[-1].get("text"):
                return [{"pool": "letter", "text": str(t[-1]["text"])[:300], "ref": k}]
    except Exception:
        pass
    return []


_SENT = re.compile(r"(?<=[.!?])\s+|\n+")
_FAREWELL = re.compile(r"\b(going to bed|go to bed|head(?:ing)? (?:off )?to bed|off to bed|good ?night|night night|"
                       r"sleep well|sweet dreams|talk (?:again |to you )?(?:in the morning|tomorrow|later|soon)|"
                       r"we will ta(?:lk)?\b|we'?ll talk|see you|good ?bye|bye\b|that is good to hear|"
                       r"that'?s good to hear|thank(?:s| you))", re.I)
FAREWELL_MAX_WORDS = 16  # a sentence this short that matches _FAREWELL is a sign-off, not content


def strip_farewell(msg: str) -> str:
    """Pure: the message with its sign-off sentences removed (a long sentence that merely mentions bed
    keeps its content: 'before I head to bed tonight, I want you to know I found your letters...')."""
    keep = []
    for sent in _SENT.split(str(msg or "")):
        s2 = sent.strip()
        if not s2:
            continue
        if _FAREWELL.search(s2) and _words(s2) <= FAREWELL_MAX_WORDS:
            continue
        keep.append(s2)
    return " ".join(keep)


def conversation_ground(msg: str) -> str:
    """Pure: the content of a Travis message usable as a ground, or '' (pure sign-off / too thin)."""
    from core import topic_perseveration as tp
    rest = strip_farewell(msg)
    return rest if len(tp._content(rest)) >= CONVO_MIN_CONTENT else ""


def _pool_conversation(state, now: float) -> list[dict]:
    try:
        hist = getattr(state, "conversation_history", None) or []
        if not hist:
            return []
        age = now - float(getattr(state, "last_human_ts", 0.0) or 0.0)
        h = str(hist[-1].get("human") or "").strip()
        if h and age <= CONVO_MAX_AGE_S:
            g = conversation_ground(h)
            if g:
                return [{"pool": "conversation", "text": g[:300], "ref": round(age, 1)}]
    except Exception:
        pass
    return []


def gather(state=None, now: float | None = None) -> list[dict]:
    now = _now() if now is None else now
    return (_pool_reading() + _pool_frontier() + _pool_percept(now) + _pool_letter()
            + _pool_conversation(state, now))


def pick_key(c: dict) -> str:
    return f"{c.get('pool')}|" + " ".join(str(c.get("text") or "").lower().split())[:120]


def choose(cands: list[dict], red: dict, embed=_default_embed, themes: list | None = None,
           repeats: dict | None = None, core_words: set | None = None) -> tuple[dict | None, list[dict]]:
    """Re-seed pick: least similar to the modal topic's first thought, plus REPEAT_PENALTY per earlier pick
    of the same candidate (`repeats`: pick_key -> count); never one that feeds the loop (shared anchor term,
    cosine >= LOOP_SIM to the loop topic, or -- frontier only -- recurring among `themes`, the recent
    curiosity questions). Returns (pick, scored candidates). Pure given `embed`."""
    from core import topic_perseveration as tp
    loop_an = set(red.get("modal_anchors") or [])
    tvec = red.get("modal_first_vec")
    repeats = repeats or {}
    tvecs = None
    scored = []
    for c in cands:
        v = c.pop("_vec", None)
        if v is not None:
            try:
                import numpy as np
                v = np.asarray(v, dtype="float32")
            except Exception:
                pass
        else:
            v = embed(c["text"]) if embed else None
        sim = _cos(tvec, v)
        why = []
        if (loop_an and (tp.anchors_of(c["text"]) & loop_an)) or \
                any(len(a) >= 3 and a in c["text"].lower() for a in loop_an):
            why.append("anchor")
        if sim is not None and sim >= LOOP_SIM:
            why.append("loop_sim")
        if c["pool"] == "frontier" and themes and v is not None:
            if tvecs is None:
                tvecs = [embed(t) if embed else None for t in themes]
            if is_recurring_theme([_cos(v, tv) for tv in tvecs]):
                why.append("theme_recur")
        if c["pool"] == "frontier" and core_words and (_qwords(c["text"]) & set(core_words)):
            why.append("theme_core")
        rep = int(repeats.get(pick_key(c), 0))
        scored.append({"pool": c["pool"], "text": c["text"][:160], "ref": c.get("ref"),
                       "sim_to_loop": None if sim is None else round(sim, 3), "feeds_loop": bool(why),
                       "feeds_why": why, "repeat": rep})
    ok = [s for s in scored if not s["feeds_loop"]]
    if not ok:
        return None, scored
    ok.sort(key=lambda s: (1.0 if s["sim_to_loop"] is None else s["sim_to_loop"]) + REPEAT_PENALTY * s["repeat"])
    return ok[0], scored


def _seed_pick_counts() -> None:
    """Once per process: count earlier picks from the log tail so a restart does not reset the penalty.
    Bounded read of this module's own log. Called under _LOCK."""
    global _picks_seeded
    if _picks_seeded:
        return
    _picks_seeded = True
    try:
        from core.shadow_log import tail_rows
        for r in tail_rows(_LOG, REPEAT_SEED_N):
            p = r.get("pick") if r.get("would_inject") else None
            if p and p.get("text"):
                k = pick_key(p)
                _pick_counts[k] = _pick_counts.get(k, 0) + 1
    except Exception:
        pass


# -- the hook ------------------------------------------------------------------------------------------
def observe(signals: dict, thought: str, vec, state=None, live: dict | None = None,
            now: float | None = None, embed=_default_embed, bored_streak: int | None = None) -> dict | None:
    """SHADOW hook, called once per DMN thought (after stream_drive.observe). Reads redundancy, decides
    would-inject, gathers pools only when it would, logs one row. Applies NOTHING. Raises
    profile.NonLiveWriteError in a non-live process (the caller's fail-open wrapper swallows it)."""
    global _last_inject_ts
    if not thought or not str(thought).strip():
        return None
    now = _now() if now is None else now
    path = profile.guard_path(_LOG)   # resolved before any I/O; a non-live process is refused here
    with _LOCK:
        win = [b for b in _buf if now - b["ts"] <= WINDOW_MAX_AGE_S][-WINDOW:]
        red = redundancy(thought, vec, win)
        cmax = red["cos_recent_max"]
        reasons = []
        if red["topic_lock"]:
            reasons.append("topic_lock")
        if cmax is not None and cmax >= INTERVENE_SIM:
            reasons.append("restating")
        if signals.get("circling"):
            reasons.append("circling")
        if signals.get("slow_loop"):
            reasons.append("slow_loop")
        # J-3335: second, additive trigger -- the sentence-level double repeat (the _bored_streak >= 2 the
        # tick STARTED with). Same pools, same cooldown accounting; None / <2 adds nothing.
        dbl = False
        try:
            dbl = bored_streak is not None and int(bored_streak) >= DOUBLE_REPEAT_STREAK
        except Exception:
            dbl = False
        if dbl:
            reasons.append("double_repeat")
        trigger = None
        if reasons:
            trigger = "double_repeat" if reasons == ["double_repeat"] else                 next(r for r in reasons if r != "double_repeat")
        cooled = (now - _last_inject_ts) >= COOLDOWN_S
        would = bool(reasons) and cooled
        grounded = None
        try:
            from core import stream_drive
            grounded = stream_drive._is_grounded(signals.get("about"), signals.get("source"))
        except Exception:
            pass
        live = live or {}
        row = {"ts": round(now, 1), "about": (signals.get("about") or "")[:60], "source": signals.get("source"),
               "train_kind": signals.get("train_kind"), "train_len": signals.get("train_len"),
               "grounded": grounded, "window_n": red["n"], "topics": red["topics"],
               "modal_share": red["modal_share"], "in_modal": red["in_modal"], "topic_lock": red["topic_lock"],
               "cos_recent_max": cmax, "advisory": bool(cmax is not None and cmax >= ADVISORY_SIM),
               "circling": bool(signals.get("circling")), "slow_loop": bool(signals.get("slow_loop")),
               "method": red["method"], "reasons": reasons, "trigger": trigger,
               "double_repeat": dbl, "bored_streak_start": bored_streak if dbl else None,
               "cooldown_blocked": bool(reasons) and not cooled,
               "would_inject": would, "live_redirect": bool(live.get("redirected")),
               "live_escape": bool(live.get("escape"))}
        if would:
            _last_inject_ts = now
            _seed_pick_counts()
            themes = recent_curiosity_themes()
            core_w = loop_core(themes, _curiosity_base(now), red["modal_first_text"]) if themes else set()
            pick, scored = choose(gather(state, now), red, embed=embed, themes=themes,
                                  repeats=_pick_counts, core_words=core_w)
            pick_repeat = None
            if pick is not None:
                pick_repeat = int(pick.get("repeat", 0))
                k = pick_key(pick)
                _pick_counts[k] = _pick_counts.get(k, 0) + 1
            row.update({"loop_topic": red["modal_first_text"][:140], "loop_anchors": red["modal_anchors"],
                        "candidates": scored, "pick": pick,
                        "pools_available": sorted({c["pool"] for c in scored}),
                        "pools_v": POOLS_V, "pick_repeat": pick_repeat,
                        "feeds_loop_n": sum(1 for c in scored if c["feeds_loop"]),
                        "theme_core": sorted(core_w)[:12]})
        _buf.append({"ts": now, "text": str(thought), "vec": vec})
        del _buf[:-WINDOW]
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        except Exception:
            pass
    return row


def status(n: int = 2000) -> dict:
    """For pulse / liveness: rates over the recent tail. Bounded read."""
    try:
        from core.shadow_log import tail_rows
        rows = tail_rows(_LOG, n)
        if not rows:
            return {"rows": 0}
        inj = [r for r in rows if r.get("would_inject")]
        pools: dict[str, int] = {}
        for r in inj:
            p = (r.get("pick") or {}).get("pool") or "none"
            pools[p] = pools.get(p, 0) + 1
        v2 = [r for r in inj if r.get("pools_v") == POOLS_V]
        return {"rows": len(rows), "would_inject": len(inj), "would_inject_v2": len(v2),
                "distinct_picks_v2": len({pick_key(r["pick"]) for r in v2 if r.get("pick")}),
                "pick_repeat_max_v2": max([int(r.get("pick_repeat") or 0) for r in v2] or [0]),
                "would_inject_where_live_did_not": sum(1 for r in inj if not r.get("live_redirect") and not r.get("live_escape")),
                "topic_lock_frac": round(sum(1 for r in rows if r.get("topic_lock")) / len(rows), 3),
                "pick_by_pool": pools}
    except Exception:
        return {"rows": 0}
