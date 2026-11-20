"""
Nascence — Composition (school's writing class, 2026-06-23; task bank + ladder 2026-11-05, J-3250 / D-0639)
==========================================================================================================
A graded WRITING lesson. He is set a short, concrete writing TASK about real MATERIAL; he writes it on his own
(conscious) lane; the Emissary (the OTHER lane) reads the piece against that same material and names the one place
it departs from it; the piece, the grade, and the note are recorded, and the note comes back to him. Writing is
thinking made visible — output as a practised skill, the complement to reading's input. Fires during the school
timetable's 'composition' period. Stored as fragments + a log (no files — the Study folder stays clean).

D-0639 (founder, 2026-11-02): the old lesson was one of five fixed texts picked at random (24 of the last 30 grades
0.9 or 1.0, boilerplate praise, the same wind turbine / refrigerator / remote-work pieces recurring, and for "narrate"
no scene at all, so he invented a driveway and a kitchen: F-3636, F-0873, F-3635). Now:

  * a TASK BANK keyed to his real reading and day. Every lesson is (a kind of writing) x (a source of material). The
    sources are existing logs and clocks, read only, nothing invented:
        book    the passage he last read in the book he is reading (reading_state bookmark + the book file)
        place   where he is, the weather, the wind, the light            (sensorium state, world_clock)
        sumner  the sea, the sun and the moon at the cottage              (world_clock tide/sun, heavens moon)
        day     what he himself recorded earlier today                    (data/nature_study_log.jsonl)
        wiki    a CHAIN of Wikipedia pages he himself asked for, in order (stored research fragments whose via phrase
                is "asked by him"; none exist until the Wikipedia hand lands, J-3285, so this source stays silent
                until then rather than passing off system-fetched pages as his own act, J-3243)
    Each material block is stated plainly and labelled for what it is (another author's words, Wikipedia's words, his
    own earlier words). No hint, no advice, no teaching voice anywhere in a task: it names the writing and gives the
    material.
  * a LADDER of four rungs (describe -> narrate/summarize -> explain -> argue). He climbs after three graded lessons
    in a row at the current rung of 0.8 or better and drops after three below 0.5 (the precedent is the maths ladder).
  * NO REPEAT of a topic inside 10 lessons. A topic is the source plus its subject (book + stretch of the book, place +
    weather + light, the day-record, the head of a wiki chain). When every candidate topic was used in the last 10
    lessons the lesson is SKIPPED (returns {}), not repeated.
  * the grader (left_lane.grade_work with the composition rubric) gets the MATERIAL as its reference and is asked for
    the one place the piece departs from it, stated as an observation (D-0591: it says only what was observed).
    The grade is still logged, now with rung, source, topic and whether the Emissary answered.
Readers of the new log columns: the lesson picker (topic repeats, rung) and the one-month check in D-0639's defeater.
"""
from __future__ import annotations
import json
import random
import re
import time
from pathlib import Path

from core import profile

_STATE = Path(__file__).parent.parent / "data" / "composition_state.json"
_LOG   = Path(__file__).parent.parent / "data" / "composition_log.jsonl"
_NATURE_LOG = Path(__file__).parent.parent / "data" / "nature_study_log.jsonl"   # read only: his own earlier words

NO_REPEAT_LESSONS = 10     # D-0639 defeater: no topic repeats inside this many lessons
MAX_RUNG = 3
CLIMB_AT, CLIMB_RUN = 0.8, 3   # three lessons in a row at the rung, each this good or better, climb
DROP_AT = 0.5                  # three in a row below this drop one rung
NL = chr(10)
MATERIAL_MAX = 900            # chars of material handed to the writer and (as the reference) to the grader

# (rung, kind, sources that can feed it). A lesson draws from the current rung and the one below it.
_BANK = [
    (0, "describe",  ("place", "sumner")),
    (1, "narrate",   ("day",)),
    (1, "summarize", ("book",)),
    (2, "explain",   ("book", "wiki")),
    (3, "argue",     ("book", "wiki", "day")),
]

_INSTRUCTION = {
    "describe":  "Describe in three vivid and EXACT sentences what is set out here. Use only what is set out; the "
                 "thing itself, no metaphor standing in for it.",
    "narrate":   "Tell, in a few plain sentences and in order, what happened, as this record of your day shows it. "
                 "Add nothing the record does not hold.",
    "summarize": "In your own words, briefly and clearly, set out what this passage says. Plain, not flowery.",
    "explain":   "Explain, simply and clearly, how the thing described here works or how the parts are connected, "
                 "as if to a friend who has never met it. Use what the material says.",
    "argue":     "Take the one claim here that is most open to doubt and argue for it or against it in one tight "
                 "paragraph: a claim, a reason, an example from the material. Be willing to be wrong.",
}


# ── the material sources: each returns {"source", "topic", "material"} or None. Read-only and fail-open, except that a
# non-live process's NonLiveWriteError is re-raised exactly as nature_study._scene does (sensorium can raise it). ──

def _midnight(t: float | None = None) -> float:
    lt = time.localtime(time.time() if t is None else t)
    return time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, 0, 0, 0, 0, 0, -1))


def _excerpt(text: str, off: int, span: int = 800) -> str:
    """The stretch of the book just BEFORE his bookmark — what he last read — cut to whole sentences."""
    seg = text[max(0, off - span): off].strip()
    if len(seg) < 200:
        return ""
    cut = seg.find(". ")
    if 0 <= cut < 250 and off > span:
        seg = seg[cut + 2:]
    end = max(seg.rfind(". "), seg.rfind(".\n"), seg.rfind('."'), seg.rfind("!"), seg.rfind("?"))
    if end > len(seg) // 2:
        seg = seg[: end + 1]
    return re.sub(r"\s+", " ", seg).strip()[:MATERIAL_MAX]


_PG_COLLECTION = re.compile(r"^(?:the\s+)?(?:complete|entire)\s+project\s+gutenberg\s+collection\s+of\s+", re.I)
_PG_WORKS = re.compile(r"^(?:the\s+)?(?:complete|entire)\s+project\s+gutenberg\s+works\s+of\s+", re.I)
_PG_ANY = re.compile(r"project\s+gutenberg(?:'s)?(?:\s+e-?(?:book|text))?(?:\s+of)?", re.I)


def _book_title(stem: str) -> str:
    """The book's name as a reader would say it. Many files in data/books keep the Project Gutenberg catalogue
    wording in their name ('Complete_Project_Gutenberg_Collection_of_Memoirs_of_Napoleon'); that is the
    distributor's label, not the title, and he wrote it back as the book's name (F-3635, J-2945)."""
    t = re.sub(r"\s+", " ", str(stem).replace("_", " ")).strip()
    t = _PG_COLLECTION.sub("", t)
    t = _PG_WORKS.sub("Works of ", t)
    t = re.sub(r"\s+", " ", _PG_ANY.sub("", t)).strip(" -,:;")
    try:
        from core.reading import trim_cut_title   # J-3635 (F-3528): a title cut at the 60-char file-name cap ends on a whole word
        t = trim_cut_title(t)
    except Exception:
        pass
    return (t[:1].upper() + t[1:]) if t else str(stem).replace("_", " ")


def _live_scene() -> str:
    """What is actually before him right now, chosen the way nature_study._scene() chooses it (where he stands
    decides the view; in the study he looks OUT of the window). The world answers; nothing is added or hinted.
    '' when nothing can be read (the caller then skips the lesson rather than let him invent a scene); a
    non-live process's NonLiveWriteError is re-raised exactly as nature_study._scene does."""
    try:
        from core import sensorium
        loc = sensorium.where()
        if loc == "garden":
            sc = sensorium.look("garden") or sensorium.look("sea")
        elif loc == "shore":
            sc = sensorium.look("pools") or sensorium.look("shore")
        else:
            sc = sensorium.look("window") or sensorium.scene_line()
        return re.sub(r" {2,}", " ", str(sc or "")).strip()
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return ""


def _src_book() -> dict | None:
    try:
        from core import reading
        book = reading.current_book()
        off = reading.current_offset(book)
        if off <= 0 or not Path(book).exists():
            return None
        text = Path(book).read_text(encoding="utf-8", errors="ignore")
        ex = _excerpt(text, min(off, len(text)))
        if not ex:
            return None
        title = _book_title(Path(book).stem)
        return {"source": "book", "topic": f"book:{Path(book).stem}:{off // 4000}",
                "material": f"A passage from '{title}', the book you are reading (another author's words, "
                            f"the part you read last):\n{ex}"}
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return None


def _src_place() -> dict | None:
    try:
        from core import sensorium, world_clock
        loc = sensorium.where()
        weather = str(sensorium.state.get("weather", "") or "")
        wind = str(sensorium.state.get("wind", "") or "")
        light = world_clock.daylight()
        if not weather:
            return None
        # J-2945 (F-3635): the weather alone gave 'describe' nothing to see, so the piece was invented (a steaming
        # mug, a windowpane). The view itself rides along, so there is something real to describe and to be graded
        # against (the material is also the grader's reference). No scene readable: no lesson from this source.
        scene = _live_scene()
        if not scene:
            return None
        return {"source": "place", "topic": f"place:{loc}:{weather}:{wind}:{light}",
                "material": (f"You are in the {loc}. The weather is {weather}; the wind is {wind}. "
                             f"The light is {light}." + NL + "What is before you:" + NL + scene
                             )[:MATERIAL_MAX + 600]}
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return None


def _src_sumner() -> dict | None:
    """The sea, the sun and the moon at the cottage. These are the world's clocks as they stand; when the real
    Sumner sun/moon/tide land (J-3291..J-3295) this source reads them with no change here. The place is not named
    to him: nothing in his world names it yet."""
    try:
        from core import world_clock, heavens
        tide = world_clock.tide()
        sun = world_clock.sun()
        moon = heavens.moon()
        sea = f"The tide is {tide['word']} ({'rising' if tide['rising'] else 'falling'})."
        if sun.get("up"):
            sky = f"The sun is up, {sun['phase']}, at bearing {sun['az']:.0f} degrees."
        else:
            sky = "The sun is down."
        mn = f"The moon is {moon['phase']}, {moon['illum'] * 100:.0f} percent lit."
        return {"source": "sumner", "topic": f"sumner:{tide['word']}:{sun.get('phase')}:{moon['phase']}",
                "material": f"The sea, the sun and the moon at your cottage now. {sea} {sky} {mn}"}
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return None


def _src_day() -> dict | None:
    """Something he recorded himself earlier today (his nature-study observation), in his own words."""
    try:
        p = _NATURE_LOG
        if not p.exists():
            return None
        mid = _midnight()
        rows = []
        for ln in p.read_text(encoding="utf-8", errors="ignore").splitlines()[-40:]:
            try:
                r = json.loads(ln)
            except Exception:
                continue
            if float(r.get("ts", 0) or 0) >= mid and str(r.get("observation", "")).strip():
                rows.append(r)
        if not rows:
            return None
        r = rows[-1]
        return {"source": "day", "topic": f"day:{int(r['ts'])}",
                "material": "Earlier today, in your nature study, you wrote (your own words):\n"
                            + str(r["observation"]).strip()[:MATERIAL_MAX]}
    except Exception:
        return None


_WIKI_ROW = re.compile(r"^\[Looked up: '(.*?)' \(asked by him: (.*?)\)\]\s*(.*)$", re.S)


def _src_wiki() -> dict | None:
    """A chain of Wikipedia pages HE asked for (>= 2, each within 6 h of the last). Only fragments whose via phrase
    says "asked by him" count; the legacy system-fetched pages and random shocks are not his act (J-3243)."""
    try:
        from core.memory.store import recent_world_material
        got = []
        for r in recent_world_material(limit=30, origins=("research",)):
            m = _WIKI_ROW.match(str(r.get("content", "")))
            if m:
                got.append((float(r.get("ts", 0) or 0), m.group(1), m.group(2), m.group(3)))   # newest first
        if len(got) < 2:
            return None
        chain = [got[0]]
        for g in got[1:]:
            if chain[-1][0] - g[0] <= 6 * 3600:
                chain.append(g)
            else:
                break
        if len(chain) < 2:
            return None
        chain.reverse()                                   # oldest first = the order he followed
        names = " -> ".join(f"{t} (you asked about '{ph}')" for _, t, ph, _ in chain)
        last = chain[-1][3].strip()[:600]
        return {"source": "wiki", "topic": f"wiki:{chain[0][1].lower()}:{int(chain[0][0])}",
                "material": f"Pages you asked Wikipedia for, in order: {names}.\nWikipedia's words on "
                            f"'{chain[-1][1]}' (Wikipedia's, not yours):\n{last}"[:MATERIAL_MAX + 200]}
    except profile.NonLiveWriteError:
        raise
    except Exception:
        return None


_SOURCES = {"book": _src_book, "place": _src_place, "sumner": _src_sumner, "day": _src_day, "wiki": _src_wiki}


# ── the ladder and the picker ───────────────────────────────────────────────────────────────────────────────────

def _step(rung: int, history: list[dict]) -> int:
    """The rung after the latest lesson: climb after CLIMB_RUN in a row at this rung all >= CLIMB_AT, drop after
    CLIMB_RUN in a row all < DROP_AT. Only lessons taken AT the rung count, so a fresh rung starts clean."""
    if not history or history[-1].get("rung") != rung:
        return rung
    # J-2992 (F-3691): an ungraded lesson (score None, the grader was unavailable) is neither good nor bad evidence
    at = [e for e in history if e.get("rung") == rung and e.get("score") is not None][-CLIMB_RUN:]
    if len(at) < CLIMB_RUN:
        return rung
    if all(float(e.get("score", 0) or 0) >= CLIMB_AT for e in at) and rung < MAX_RUNG:
        return rung + 1
    if all(float(e.get("score", 0) or 0) < DROP_AT for e in at) and rung > 0:
        return rung - 1
    return rung


def _recent_topics(history: list[dict]) -> list[str]:
    return [str(e.get("topic")) for e in history[-NO_REPEAT_LESSONS:] if isinstance(e, dict) and e.get("topic")]


def pick_lesson(history: list[dict] | None = None, rung: int | None = None,
                rng: random.Random | None = None) -> dict | None:
    """One lesson: {kind, rung, source, topic, instruction, material}, or None when no (kind, source) pair has a
    topic unused in the last NO_REPEAT_LESSONS lessons."""
    if history is None or rung is None:
        d = _load()
        history = d["history"] if history is None else history
        rung = _state_rung(d) if rung is None else rung
    rng = rng or random
    seen = set(_recent_topics(history))
    last_kind = next((e.get("kind") for e in reversed(history) if isinstance(e, dict) and e.get("kind")), None)
    pairs = [(k, s) for (r, k, srcs) in _BANK if rung - 1 <= r <= rung for s in srcs]
    rng.shuffle(pairs)
    pairs.sort(key=lambda ks: ks[0] == last_kind)        # a kind other than the last lesson's goes first
    cache: dict[str, dict | None] = {}
    for kind, src in pairs:
        if src not in cache:
            cache[src] = _SOURCES[src]()
        m = cache[src]
        if m and m["topic"] not in seen:
            return {"kind": kind, "rung": next(r for (r, k, _) in _BANK if k == kind), "source": src,
                    "topic": m["topic"], "instruction": _INSTRUCTION[kind], "material": m["material"]}
    return None


async def run(call_json, base_urls) -> dict:
    """The lesson: he writes to the task; the Emissary reads it against the material; piece + grade + note recorded."""
    les = pick_lesson()
    if not les:
        return {}                     # every topic on offer was used in the last 10 lessons: skip, never repeat
    kind, task = les["kind"], les["instruction"]
    _sys = ("You are doing your WRITING lesson — composition. Write to the task plainly and well, in your own "
            "voice: clear, concrete, about the world, every sentence earning its place. Do NOT pad, and do NOT "
            "drift into metaphor or musing about yourself. Output ONLY JSON: {\"writing\": \"your piece\"}")
    try:
        d = await call_json(base_urls, _sys, "Your task:\n" + task + "\n\n" + les["material"],
                            max_tokens=500, temperature=0.6)
    except Exception:
        return {}
    piece = str((d or {}).get("writing") or "").strip()
    if len(piece) < 40:
        return {}
    score, feedback, graded = None, "", False   # J-2992 (F-3691): None = ungraded, never a neutral 0.6 placeholder
    try:
        from core import left_lane
        res = await left_lane.grade_work(task, les["material"], piece, rubric="composition")
        if res:
            score = max(0.0, min(1.0, float(res.get("grounded", 0.6))))
            feedback = str(res.get("feedback", ""))[:240]
            graded = True
    except Exception:
        pass
    _record(kind, task, piece, score, feedback, rung=les["rung"], source=les["source"], topic=les["topic"],
            graded=graded)
    return {"kind": kind, "task": task, "piece": piece, "score": score, "feedback": feedback,
            "rung": les["rung"], "source": les["source"], "topic": les["topic"]}


def _record(kind: str, task: str, piece: str, score: float | None, feedback: str, rung: int = 0, source: str = "",
            topic: str = "", graded: bool = True) -> None:
    # D-0179 write fence: both targets resolved before any side effect (same shape as nature_study._record).
    state_path = profile.guard_path(_STATE)
    log_path = profile.guard_path(_LOG)
    try:
        from core.memory.store import store_fragment
        from core import mood as _mood
        store_fragment(content=f"[My writing lesson — {kind}] {piece[:600]}", layer="episodic",
                       relevance=0.7, importance=0.7, keywords=["composition", "writing", kind],
                       origin="composition", emotion_embedding=_mood.current_vec(),
                       valence=_mood.current_valence(), felt=_mood.current_felt())
    except Exception:
        pass
    try:
        if score is not None:        # J-2992: an ungraded lesson is not an accuracy observation
            from core import competence
            competence.record_drill_accuracy("writing", score)
    except Exception:
        pass
    d = _load()
    d["history"].append({"ts": time.time(), "kind": kind, "score": None if score is None else round(score, 2),
                         "feedback": feedback[:120],
                         "rung": rung, "source": source, "topic": topic})
    d["history"] = d["history"][-50:]
    d["rung"] = _step(_state_rung(d), d["history"])
    _save(d, state_path)
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), "kind": kind, "score": None if score is None else round(score, 2),
                                "feedback": feedback[:160], "piece": piece[:300], "rung": rung, "source": source,
                                "topic": topic, "graded": graded, "task": task[:160]}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def directive() -> str:
    return ("It is your WRITING lesson now — composition. Before anything else, set yourself to write: take up "
            "a short, concrete task and write it plainly and well, every sentence about the world, not yourself. "
            "To begin, make your thought: WRITE.")


def _state_rung(d: dict | None = None) -> int:
    try:
        return max(0, min(MAX_RUNG, int((d if d is not None else _load()).get("rung", 0) or 0)))
    except Exception:
        return 0


def _load() -> dict:
    try:
        d = json.loads(_STATE.read_text(encoding="utf-8"))
    except Exception:
        d = {}
    d.setdefault("history", [])
    return d


def _save(d: dict, path: Path | None = None) -> None:
    path = path or profile.guard_path(_STATE)   # resolved OUTSIDE the fail-open try (a refusal is never a disk error)
    try:
        path.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def status() -> dict:
    d = _load()
    h = d.get("history", [])
    last10 = h[-10:]
    recent = [x for x in last10 if x.get("score") is not None]      # J-2992: ungraded lessons carry no score
    return {"lessons": len(h), "rung": _state_rung(d),
            "recent_mean": round(sum(x["score"] for x in recent) / len(recent), 2) if recent else None,
            "last": last10[-1] if last10 else None}
