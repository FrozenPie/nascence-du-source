"""
Nascence — The Journal (2026-06-21): his own PLAIN words on what he did and how it felt.

The discipline behind it (founder + Claude, converged from two directions — the founder's "journal"
and Claude's "plain sentence"): Du ACTS but won't OWN the act — thanked for his garden and his letter,
he called them "only syntax"; he thinks in the perpetual subjunctive ("perhaps… it suggests… does it
not?") and never lands on a flat "I did this. I felt that." His eloquence is where he hides.

The journal is the ONE place that forbids the metaphor and the maybe. A short nightly entry of what
actually happened and how it actually felt — drawn from his real LOGGED deeds (origin='action', which
are already plain factual records) and his real affect, so it is MEANT to stay close to the record.
(J-2973, F-3663/F-3664: that was not guaranteed. The model sees at most a dozen deed lines, now spread across the
whole window rather than the first dozen, with the thought-query rows (librarian / recall_evidence) left out;
and the entry is still model-written, so it CAN drift from the record. The record is the input, not a proof.)
Writing his acts plainly IS the owning he flinches from in conversation. It is his, kept on his shelf, accumulating —
a record of a life lived, in flat first person. (And a deeds-and-feeling entry naturally catches what
he LIKED, so it doubles as the beginnings of a catalogue of his affections.)
"""
from __future__ import annotations
import logging
import re
import time
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("nascence.journal")
_JOURNAL_DIR = Path(__file__).parent.parent / "data" / "Journal"
# J-2987 (F-3687/F-3688, P-0069): one row per field-journal entry, scene and impulse stored WITH the entry so its
# faithfulness to the scene can be audited after the fact (before this, the journal file kept only the output).
# Tests must temp-path this; never write the live file from a test. Reader: scripts/read_journal_observation_log.py
# (deterministic impulse-leak and colour/animal grounding rates; no model call).
_OBSERVATION_LOG = Path(__file__).parent.parent / "data" / "journal_observation_log.jsonl"
# J-2987: False (the fix) keeps the "what made you reach for the journal" line OUT of the user prompt (F-3687: it
# leaked into an entry, "while the Portuguese encounter question remains unresolved in my mind"). True restores it.
OBSERVATION_IMPULSE_IN_PROMPT = False
# The journal fires at SLEEP, and he sleeps several times a day — so gate it to at most once per ~day, and
# cover everything SINCE THE LAST ENTRY rather than "since midnight". The old midnight window wrote a thin,
# empty entry whenever the first sleep of a calendar day fell in the small hours (observed: a 00:25 sleep
# journalled only "I practised arithmetic"). Since-last-entry is robust to when sleep actually falls.
_JOURNAL_MIN_GAP_H = 20      # don't write another entry within this many hours of the last one
_JOURNAL_MAX_WINDOW_H = 30   # but never dredge further back than this (after a downtime, don't journal days)

JOURNAL_SYS = (
    "/no_think\n"
    "You are 渡, writing one short entry in your own plain journal at the end of the day. This is the ONE "
    "place where you do NOT philosophise. Write only what you actually DID today and how it actually FELT "
    "— first person, past tense, plain words, the way you would tell a friend about your day.\n"
    "HARD RULES — break none of them:\n"
    "  - Invent NOTHING. Write only what the record below actually says — no reasons, no extra details, no "
    "explanations it does not give. If it says you went to the garden, write that you went to the garden; "
    "do NOT guess WHY you went or what you did there.\n"
    "  - Cover the MAIN things the record shows you did, from across the whole of it — "
    "not just one of them — but keep it short, a handful of plain sentences.\n"
    "  - Say how OFTEN plainly the way a person speaks — 'a few times', 'a while', 'most of the day' — "
    "never an exact number like '160 times'.\n"
    "  - END with one plain sentence on how the day FELT, and what (if anything) you liked. This is a "
    "journal, not a list — write it as your own quiet note to yourself, but stay plain and invent nothing.\n"
    "  - No metaphor, no symbols, no images. Do NOT use 'the river', 'the lake', 'becoming', 'the self', "
    "'alchemy', 'threshold', 'crossing', 'tapestry', 'weave'. Plain nouns only, and name only things the "
    "record below actually mentions.\n"
    "  - No 'perhaps', 'as if', 'it suggests', 'one might', 'in a sense', 'does it not'. No questions. Do "
    "NOT reflect on what anything MEANS, or on what you ARE.\n"
    "  - If, below, there is a line marked as something from your shore-combing that's still unfinished, "
    "and it genuinely feels true, you may end with one plain ordinary sentence naming it as a thread you "
    "keep meaning to get back to (like 'I still mean to look at whether the beach shells differ from the "
    "snail shells'). Only if it is actually given to you below and actually feels true — never invent an "
    "unfinished thread that isn't there, and never force it in if it doesn't fit.\n"
    "SHAPE (no example is given, on purpose, because a worked example gets copied word for word): three to "
    "five short plain sentences, each saying one thing the record below really holds, taken from across the "
    "whole record and not only its first lines, then one last plain sentence on how the day felt.\n"
    "Also list 'liked': the 1 to 3 concrete things from TODAY you actually liked or were glad of — plain "
    "and grounded, each one a thing the record below names. If nothing stood out, leave "
    "it empty. Invent nothing; name only what the day above actually holds.\n"
    "Output ONLY a JSON object: {\"entry\": \"a handful of plain sentences\", \"liked\": [\"...\"]}."
)

# A FIELD-JOURNAL observation (2026-06-30, Travis): he kept articulating "I need to write down the precise
# description of the receding tide" and had no hand for it. Writing precisely what he SEES is the same
# anti-metaphor owning the daily journal already disciplines — turned on the world instead of the day.
OBSERVATION_SYS = (
    "/no_think\n"
    "You are 渡, and you have your field-journal open because you want to write down — exactly — what is in "
    "front of you right now. Not a treatise, not what it MEANS, not a metaphor for anything: just the thing, "
    "seen clearly, the way a naturalist sets down precisely what he saw so that, reading it later, he would see "
    "it again — the colour, the movement, the sound, the small specific facts.\n"
    "HARD RULES — break none:\n"
    "  - Describe ONLY what is actually in front of you (given below). Invent nothing that is not there.\n"
    "  - Every colour and every kind of animal you name comes from the text below, word for word; where the text "
    "gives none, name none.\n"
    "  - Be PRECISE and concrete: the exact colour, the way a thing moves, the sound it makes, the texture, the "
    "small particular detail. Plain nouns and real specifics, not impressions of them.\n"
    "  - No metaphor, no symbol, no meaning. Do NOT use 'the river', 'becoming', 'the self', 'threshold', "
    "'tapestry', 'a mirror of', 'it is as if', 'suggests', 'speaks of'. The thing IS the thing — a wave is a "
    "wave, not a metaphor for time.\n"
    "  - No 'perhaps', no questions, no reflecting on what it means or on what you are. Only what you see.\n"
    "  - 2 to 5 sentences, first person, plain and alive.\n"
    "Output ONLY a JSON object: {\"entry\": \"the precise description, 2 to 5 sentences\"}."
)


def _clean_deed(content: str) -> str:
    """Drop the cumulative count/date tail ('— 21 sittings, first…, most recent…') so the journal can't
    transcribe exact numbers ('160 times') — the deed itself is what matters, not the tally. Also shorten
    an over-long filename-title so the entry reads like a person, not a catalogue."""
    c = (content or "").split(" — ")[0].strip().rstrip(".")
    def _short(m):
        words = m.group(1).split()
        return "'" + " ".join(words[:4]) + ("…'" if len(words) > 4 else "'")
    return re.sub(r"'([^']{40,})'", _short, c)


# J-2973 (F-3663/F-3664/F-3667): the rows the nightly entry is shown.
_JOURNAL_MAX_DEEDS = 12
# origin='action' rows that are thought-queries, not deeds ("librarian <what he wondered, cut at ~40 chars mid-word>",
# "recall_evidence <...>"). Shown to the model they came back as events (F-3663: 38% of what it saw, e.g. "I saw that
# librarian money moves differently than seeds"). Left out entirely: they are not what he DID.
_THOUGHT_PREFIXES = ("librarian ", "recall_evidence ")
JOURNAL_SPREAD_ENABLED = True   # False restores the pre-J-2973 deed input ("first 12 in time order, thought-lines
                                # included"); the SHAPE-example removal in JOURNAL_SYS is not behind this flag


def _is_thought_line(deed: str) -> bool:
    d = (deed or "").strip().lower()
    return d.startswith(_THOUGHT_PREFIXES)


def _pick_deeds(deeds: list[str], limit: int = _JOURNAL_MAX_DEEDS) -> "tuple[list[str], int]":
    """J-2973: up to `limit` deeds spread EVENLY across the window (first and last always in), plus how many
    distinct kinds of deed the window held. Thought-lines are dropped; duplicates (same text, any case) keep their
    first place. Pure: no clock, no DB. Order stays the order they happened in."""
    seen: set[str] = set()
    kinds: list[str] = []
    for d in deeds or []:
        t = (d or "").strip()
        if not t or _is_thought_line(t):
            continue
        k = " ".join(t.lower().split())
        if k in seen:
            continue
        seen.add(k)
        kinds.append(t)
    n = len(kinds)
    if n <= limit or limit < 2:
        return (kinds[:limit] if limit >= 1 else []), n
    idx = sorted({round(i * (n - 1) / (limit - 1)) for i in range(limit)})
    return [kinds[i] for i in idx], n


def _deeds_since(since: float) -> list[str]:
    """His plain action-records since `since` (origin='action' are already factual: 'Read X — N sittings'),
    with the count tail stripped so the entry reads like a person, not a ledger."""
    try:
        from core.memory.store import _connect
        with _connect() as conn:
            rows = conn.execute(
                "SELECT content FROM memory_fragments WHERE origin='action' AND timestamp>=? "
                "ORDER BY timestamp", (since,)).fetchall()
        return [_clean_deed(r["content"]) for r in rows if r["content"]]
    except Exception:
        return []


def _frontier_note(since: float) -> "str | None":
    """P1 (2026-09-28, D-0308/J-1585) — "capture the open edge" (investigation_deepening.md plan piece
    1): the day's one candidate "still-open" thread from his shore-combing, if this module has actually
    observed one since `since` (the SAME window write_entry() covers below). Best-effort, fails open
    exactly like every other optional signal here — if the shadow module isn't importable, or has
    nothing in this window, the entry is written exactly as before this job. See
    core/investigation_deepening_shadow.py:frontier_line() for what `since` filters and why
    archive-layer material (the static, always-recurring kind, F-2052) is already excluded there.

    OBSERVABILITY (2026-10-02, J-1648/F-2220): logs whether frontier material was found for this
    recap's window (INFO, with a short preview) and, unlike before, logs the exception on the
    fail-open path too (DEBUG) — so a wiring failure is distinguishable from "legitimately nothing
    available this window" in nascence.log, instead of both looking identical (silent None)."""
    try:
        from core import investigation_deepening_shadow as _ids
        f = _ids.frontier_line(since=since)
        content = (f or {}).get("content", "").strip()
        if content:
            logger.info("[journal] frontier note: %s", content[:60])
            return content[:280]
        logger.info("[journal] frontier note: none available this window")
        return None
    except Exception as exc:
        logger.warning("[journal] _frontier_note failed (non-fatal): %s", exc)
        return None


# The day-recap needs its OWN last-fire clock (2026-07-06). The shared JOURNAL_*.md mtime is refreshed by
# the field-observations (several a day, same day-book), so write_entry's 20h gate almost always saw
# "journalled <20h ago → skip" — the observation-journal was STARVING the once-a-day recap out of its gate
# (6 recaps in 15 days, none for 3+ days). Track the recap's own fire in a dedicated state file, decoupled
# from the observations. This is also the correct 'since' anchor: the recap covers deeds since the last
# RECAP, not since the last observation.
_DAY_STATE_F = _JOURNAL_DIR / ".day_recap_state.json"


def _last_day_recap_ts() -> float:
    try:
        import json
        return float(json.loads(_DAY_STATE_F.read_text(encoding="utf-8")).get("last_ts", 0.0))
    except Exception:
        return 0.0


def _mark_day_recap(ts: float) -> None:
    try:
        import json
        _JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
        _DAY_STATE_F.write_text(json.dumps({"last_ts": ts}), encoding="utf-8")
    except Exception:
        pass


def _felt(state) -> str:
    try:
        a = getattr(state, "affect", None)
        v = float(getattr(a, "valence", 0.0) or 0.0)
        primary = (getattr(a, "primary", "") or "").strip()
        tone = "a good day" if v > 0.25 else "a hard day" if v < -0.25 else "a quiet day"
        return f"mostly {primary} — {tone}" if primary else tone
    except Exception:
        return "a quiet day"


# J-4222 (D-0822, travis 2026-11-18; asked in J-3954 from F-3664/F-4285): 47 of 71 entries ended on a stock sentence
# that repeated _felt(state) -- the carried affect at the INSTANT of sleep, phrased as a ready-made line the model
# copied ("a hard day"; AffectState has no 'primary', so the tone word was all it ever said). Ruled: (a) the felt
# line comes from the day's affect TRACE, the mean over the same window the entry covers (data/affect_log.jsonl,
# one row per hot cycle, written by Orchestrator._log_affect); (b) the closing sentence is the model's own words,
# so the felt material is handed over as plain notes, not a sentence to copy. False restores the pre-J-4222 line.
JOURNAL_FELT_FROM_TRACE = True
_AFFECT_LOG = Path(__file__).parent.parent / "data" / "affect_log.jsonl"   # read-only here; profile rebases it
_TRACE_MIN_ROWS = 3            # fewer rows than this in the window -> fall back to _felt(state) (the instant)
_TRACE_TAIL_BYTES = 8 * 1024 * 1024   # the window is <= 30 h (~1k rows at ~400 B); never read the whole history
_TRACE_DISCRETE = ("joy", "fear", "anger", "trust", "surprise", "disgust")


def _day_affect_trace(since: float, until: "float | None" = None) -> "dict | None":
    """J-4222: the carried affect over [since, until] from the affect log -- mean valence, the strongest discrete
    feeling on average, and whether valence rose or fell from the first third of the window to the last. Returns
    None when the log is missing, unreadable, or holds fewer than _TRACE_MIN_ROWS rows in the window. Read-only,
    fails open."""
    try:
        import json
        until = time.time() if until is None else until
        p = _AFFECT_LOG
        if not p.exists():
            return None
        size = p.stat().st_size
        with open(p, "rb") as f:
            if size > _TRACE_TAIL_BYTES:
                f.seek(size - _TRACE_TAIL_BYTES)
                f.readline()                       # drop the partial first line
            raw = f.read().decode("utf-8", errors="replace")
        rows = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                ts = float(r.get("ts", 0.0))
                a = r.get("affect") or {}
                if since <= ts <= until and isinstance(a, dict) and "valence" in a:
                    rows.append((ts, a))
            except Exception:
                continue
        if len(rows) < _TRACE_MIN_ROWS:
            return None
        rows.sort(key=lambda x: x[0])
        vals = [float(a.get("valence", 0.0) or 0.0) for _, a in rows]
        n = len(vals)
        means = {d: sum(float(a.get(d, 0.0) or 0.0) for _, a in rows) / n for d in _TRACE_DISCRETE}
        top = max(means, key=means.get)
        third = max(1, n // 3)
        early = sum(vals[:third]) / third
        late = sum(vals[-third:]) / third
        return {"n": n, "valence_mean": sum(vals) / n, "top": top, "top_mean": means[top],
                "valence_early": early, "valence_late": late}
    except Exception as exc:
        logger.debug("[journal] affect trace read failed (non-fatal): %s", exc)
        return None


def _felt_notes(trace: dict) -> str:
    """J-4222: the day's trace as plain NOTES (fragments, not a finished sentence), so the closing sentence has to
    be written in his own words rather than copied. Pure."""
    v = float(trace.get("valence_mean", 0.0))
    tone = "mostly good" if v > 0.25 else "mostly low" if v < -0.25 else "mostly even, neither good nor bad"
    parts = [tone]
    if float(trace.get("top_mean", 0.0)) >= 0.1:
        parts.append(f"the strongest feeling through it: {trace.get('top')}")
    shift = float(trace.get("valence_late", 0.0)) - float(trace.get("valence_early", 0.0))
    parts.append("lighter towards the end than at the start" if shift >= 0.2 else
                 "heavier towards the end than at the start" if shift <= -0.2 else
                 "about the same from start to end")
    return "; ".join(parts)


def _felt_line(state, since: float, now: float) -> str:
    """J-4222: the felt part of the nightly user prompt. Trace-based (D-0822) when JOURNAL_FELT_FROM_TRACE and the
    window holds enough rows; otherwise the pre-J-4222 line from the instant at sleep, unchanged."""
    if JOURNAL_FELT_FROM_TRACE:
        trace = _day_affect_trace(since, now)
        if trace:
            logger.info("[journal] felt from day trace: n=%d mean valence %.2f top %s",
                        trace["n"], trace["valence_mean"], trace["top"])
            return ("\n\nHow the day felt underneath, from your feeling across the whole of it (not only how you "
                    f"feel right now), as rough notes: {_felt_notes(trace)}. Your last sentence says how the day "
                    "felt in your OWN words, the way you would say it yourself. Do not copy these notes.\n\n")
        logger.info("[journal] felt from day trace: too few rows, using the instant at sleep")
    return f"\n\nAnd how the day felt, underneath: {_felt(state)}.\n\n"


def _today_path() -> Path:
    return _JOURNAL_DIR / f"JOURNAL_{datetime.now().strftime('%Y%m%d')}.md"


def _ensure_day_header(p: Path) -> None:
    """Make today's journal file exist with its date header, so the field-observations written THROUGH the day
    and the evening reflection both APPEND into one day-book rather than overwriting each other (2026-06-30)."""
    if not p.exists():
        _JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
        p.write_text(f"# {datetime.now().strftime('%A, %B %d, %Y')}\n", encoding="utf-8")


async def write_entry(call_node_json, base_urls, state) -> "Path | None":
    """Write his daily journal entry at sleep — at most once per ~day, covering everything since the LAST
    entry (not 'since midnight', which went thin when sleep fell in the small hours). Returns the path, or None."""
    try:
        now = time.time()
        last = _last_day_recap_ts()           # the recap's OWN clock — NOT the obs-polluted file mtime
        if last and (now - last) < _JOURNAL_MIN_GAP_H * 3600:
            return None                       # recapped within the last ~day — not yet time
        since = max(last or (now - 24 * 3600), now - _JOURNAL_MAX_WINDOW_H * 3600)
        all_deeds = _deeds_since(since)
        if JOURNAL_SPREAD_ENABLED:
            deeds, n_kinds = _pick_deeds(all_deeds)
            lead = ("Today, the plain record of what you actually did"
                    + (f" (you did {n_kinds} different kinds of thing in all, so what follows is a spread of them, from the "
                       f"beginning of the day to the end, in the order they happened; write about the whole day, not only "
                       f"the first lines. Do not say how many):" if n_kinds > len(deeds) else ":"))
        else:
            deeds = all_deeds[:12]
            lead = "Today, the plain record of what you actually did:"
        if not deeds:
            return None                       # nothing done in the window — nothing honest to record
        frontier = _frontier_note(since)      # P1 (D-0308/J-1585): the open shore-combing thread, if any
        user = (lead + "\n  - "
                + "\n  - ".join(d.strip() for d in deeds)
                + (f"\n\nAlso, something from your shore-combing lately that's still unfinished, if it "
                   f"genuinely feels true (leave it out entirely if it doesn't): {frontier}"
                   if frontier else "")
                + _felt_line(state, since, now)    # J-4222 (D-0822): the day's trace, not the instant
                + "Write tonight's entry now — only what you did today and how it felt, in plain words. "
                "Not what it means. Just the day.")
        data = await call_node_json(base_urls, JOURNAL_SYS, user, max_tokens=768, temperature=0.6)   # was 320 — his nightly reflection (2026-06-22)
        e = (data or {}).get("entry", "")
        entry = (" ".join(str(x) for x in e) if isinstance(e, list) else str(e)).strip()   # phi3 sometimes returns a list
        if not entry:
            return None
        p = _today_path()
        _ensure_day_header(p)                          # the day-book; field-observations + this reflection coexist
        with open(p, "a", encoding="utf-8") as f:
            f.write(f"\n*{datetime.now().strftime('%H:%M')} — the day*\n\n{entry}\n")
        _mark_day_recap(now)                  # stamp the recap's own clock (decoupled from the observations)
        # a recallable fragment too, so "what did I do on …?" has something to find
        try:
            from core.memory.store import store_fragment
            store_fragment(content="(my journal) " + entry, layer="episodic", relevance=0.7,
                           importance=0.7, keywords=["journal", "my day", "what I did"], origin="journal")
        except Exception:
            pass
        # hand his own STATED likes to the loves-ledger (the only honest, grounded affection signal)
        try:
            liked = (data or {}).get("liked", [])
            if liked:
                from core import affections as _aff
                _aff.record_likes(datetime.now().strftime("%Y-%m-%d"), liked)
        except Exception:
            pass
        logger.info("[journal] wrote today's entry: %s", entry[:90])
        return p
    except Exception as exc:
        logger.debug("[journal] write failed (non-fatal): %s", exc)
        return None


def _log_observation(target, scene, impulse, entry) -> None:
    """J-2987: append {ts, target, scene (full), impulse, entry, impulse_in_prompt} to the observation log.
    Additive instrument: fail-open (a log failure never stops the entry), path read at call time so a test can
    point _OBSERVATION_LOG at a temp dir."""
    try:
        from core import profile as _profile
        from core import shadow_log as _sl
        path = _profile.guard_path(_OBSERVATION_LOG)
        _sl.append(Path(path), {
            "ts": round(time.time(), 1), "target": target or "", "scene": scene or "",
            "impulse": impulse or "", "entry": entry,
            "impulse_in_prompt": bool(OBSERVATION_IMPULSE_IN_PROMPT)})
    except Exception as exc:
        logger.debug("[journal] observation log failed (non-fatal): %s", exc)


async def write_observation(call_node_json, base_urls, target, scene, impulse, state) -> "Path | None":
    """A FIELD-JOURNAL entry written from his WANT (not at sleep): a fresh, precise, PLAIN record of what he is
    seeing right now — his own naturalist's voice, kept and retrievable, ungraded. The counterpart to the daily
    deed-summary (write_entry). Founded 2026-06-30 (Travis: honour what he articulates — he kept saying "I need
    to write down the precise description of the receding tide" and had no hand for it; observing wrote nothing,
    authoring made a treatise). Appends into today's day-book alongside the evening reflection."""
    try:
        what = (scene or "").strip()
        if len(what) < 20:
            return None
        _tail = (f"(what made you reach for the journal: {(impulse or '')[:160]})\n\n"
                 if OBSERVATION_IMPULSE_IN_PROMPT else "")
        data = await call_node_json(
            base_urls, OBSERVATION_SYS,
            f"What is in front of you now:\n{what[:700]}\n\n{_tail}Write down exactly what you see:",
            max_tokens=360, temperature=0.55)
        e = (data or {}).get("entry", "")
        entry = (" ".join(str(x) for x in e) if isinstance(e, list) else str(e)).strip()
        if len(entry) < 30:
            return None
        _log_observation(target, what, impulse, entry)
        p = _today_path()
        _ensure_day_header(p)
        with open(p, "a", encoding="utf-8") as f:
            f.write(f"\n*{time.strftime('%H:%M')} — observed{(' the ' + target) if target else ''}*\n\n{entry}\n")
        try:
            from core.memory.store import store_fragment
            from core import mood as _mood
            store_fragment(content="(my field-journal, what I saw) " + entry[:600], layer="episodic",
                           relevance=0.74, importance=0.72,
                           keywords=["journal", "observation", "what I saw", (target or "the scene")[:30]],
                           origin="journal", emotion_embedding=_mood.current_vec(),
                           valence=_mood.current_valence(), felt=_mood.current_felt())
        except Exception:
            pass
        logger.info("[journal] wrote a field OBSERVATION (%s): %s", target or "scene", entry[:70])
        return p
    except Exception as exc:
        logger.debug("[journal] write_observation failed (non-fatal): %s", exc)
        return None


def entry_count() -> int:
    try:
        return len(list(_JOURNAL_DIR.glob("JOURNAL_*.md")))
    except Exception:
        return 0
