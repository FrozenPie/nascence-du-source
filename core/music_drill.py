"""
Nascence — Music Drill + Composition Hand (school subject, 2026-07-04 · docs/staged/music_learning.md Tier 1)
============================================================================================================
Music THEORY as school: generated, DETERMINISTICALLY-GRADED drills (the proven math-drill pattern — the
grader is NEVER the LLM; parser checks: beat sums, interval arithmetic, scale/chord/key spelling tables,
ABC measure sums) + COMPOSITION as a new hand (write a melody in ABC, graded for WELL-FORMEDNESS only —
never for beauty; aesthetics is not deterministically gradable and we do not fake a judge).

Why (the design session, ratified): music is a LANGUAGE — theory/notation transfer directly to a frozen
LLM (his weights carry heavy musical knowledge; deep-memory reframe: it is HIS to reach into). A domain
with ZERO river-vocabulary overlap (the attractor has no grip on voice-leading), deterministic rightness
(more felt-vs-measured calibration ground), and a CRAFT escape (making, not only watching). Partners the
listening lane (core/listening.py): he hears structure he can also name and make. ABC PLAYBACK of his own
pieces stays OUT by law (self-reference arrives only after listening history is deep).

Adaptive ladder + accuracy-window advancement copied from math_drill (a real teacher's promotion). Daily
target starts MODEST (the math drill at 200/day bled into his dreams — start at 20, tune on evidence).
"""
from __future__ import annotations

import json
import random
import re
import time
from datetime import date
from pathlib import Path

_STATE = Path(__file__).parent.parent / "data" / "music_drill_state.json"
_LOG = Path(__file__).parent.parent / "data" / "music_drill_log.jsonl"
_COMPOSITIONS = Path(__file__).parent.parent / "data" / "compositions"
_COMP_LOG = Path(__file__).parent.parent / "data" / "compositions_log.jsonl"

DAILY_TARGET = 16        # drills/day. Was 20; a 45-min period with SESSION_INTERVAL_S 700 holds 4 sessions x BATCH 4
#                          = 16, which is what every full school day logged (founder, 2026-09-05, F-0871).
BATCH = 4                # problems per drill session
SESSION_INTERVAL_S = 700  # same pacing rhythm as maths
MAX_LEVEL = 6
ADVANCE_ACCURACY = 0.90  # music spelling is harder than arithmetic for an 8B — 90%, not 95
ADVANCE_WINDOW = 30
COMPOSE_DAILY_CAP = 1    # one piece a day is plenty — craft, not flooding

# ── the deterministic theory tables (spelled correctly — no computed enharmonics) ─────────────────────
_SEMITONE = {"c": 0, "c#": 1, "db": 1, "d": 2, "d#": 3, "eb": 3, "e": 4, "f": 5, "f#": 6, "gb": 6,
             "g": 7, "g#": 8, "ab": 8, "a": 9, "a#": 10, "bb": 10, "b": 11}
_MAJOR_SCALES = {
    "C": ["C", "D", "E", "F", "G", "A", "B"],
    "G": ["G", "A", "B", "C", "D", "E", "F#"],
    "D": ["D", "E", "F#", "G", "A", "B", "C#"],
    "A": ["A", "B", "C#", "D", "E", "F#", "G#"],
    "E": ["E", "F#", "G#", "A", "B", "C#", "D#"],
    "F": ["F", "G", "A", "Bb", "C", "D", "E"],
    "Bb": ["Bb", "C", "D", "Eb", "F", "G", "A"],
    "Eb": ["Eb", "F", "G", "Ab", "Bb", "C", "D"],
    "Ab": ["Ab", "Bb", "C", "Db", "Eb", "F", "G"],
}
_MINOR_TRIADS = {"Am": ["A", "C", "E"], "Em": ["E", "G", "B"], "Dm": ["D", "F", "A"],
                 "Bm": ["B", "D", "F#"], "F#m": ["F#", "A", "C#"], "Cm": ["C", "Eb", "G"],
                 "Gm": ["G", "Bb", "D"], "Fm": ["F", "Ab", "C"]}
_KEY_SIG = {"C": (0, ""), "G": (1, "sharps"), "D": (2, "sharps"), "A": (3, "sharps"), "E": (4, "sharps"),
            "B": (5, "sharps"), "F": (1, "flats"), "Bb": (2, "flats"), "Eb": (3, "flats"),
            "Ab": (4, "flats"), "Db": (5, "flats")}
_DUR_BEATS = {"whole note": 4.0, "half note": 2.0, "quarter note": 1.0, "eighth note": 0.5}
_ORDINAL = {2: "2nd", 3: "3rd", 4: "4th", 5: "5th", 6: "6th", 7: "7th"}


def _load() -> dict:
    try:
        d = json.loads(_STATE.read_text(encoding="utf-8"))
    except Exception:
        d = {}
    d.setdefault("level", 1)
    d.setdefault("window", [])
    d.setdefault("today_done", 0)
    d.setdefault("composed_today", 0)
    d.setdefault("day", date.today().isoformat())
    if d["day"] != date.today().isoformat():
        d["day"] = date.today().isoformat()
        d["today_done"] = 0
        d["composed_today"] = 0
    return d


def _save(d: dict) -> None:
    try:
        _STATE.write_text(json.dumps(d, indent=1), encoding="utf-8")
    except Exception:
        pass


# ── note-answer normalization (deterministic grading of spelled answers) ─────────────────────────────
_NOTE_QUALITY = {"major", "minor", "maj", "min", "natural", "and", "or", "sharp", "flat"}


def _norm_notes(text: str) -> list[str]:
    """Extract normalized note names from his answer: 'F♯'/'F sharp'/'f#' → 'f#'. Order preserved.
    J-2988 (F-3685): a bare 'a'/'A' with no accidental is also the English ARTICLE, so it is read as the note A
    only when it cannot be the article: a lowercase 'a' counts only when the whole text is a note list (nothing
    but note names, 'major'/'minor', 'and'/'or' and punctuation), and a capital 'A' counts unless it is followed
    by an ordinary lowercase word ('A minor' and 'A major' are still the note A)."""
    t = (text or "").replace("♯", "#").replace("♭", "b")
    t = re.sub(r"([A-Ga-g])[ -]?sharp", r"\1#", t, flags=re.I)
    t = re.sub(r"([A-Ga-g])[ -]?flat", r"\1b", t, flags=re.I)
    words = re.findall(r"[A-Za-z#]+", t)
    note_list = bool(words) and all(
        re.fullmatch(r"[A-Ga-g](#|b)?", w) or w.lower() in _NOTE_QUALITY for w in words)
    out = []
    for m in re.finditer(r"\b([A-Ga-g])(#|b)?(?![a-z#])", t):
        letter, acc = m.group(1), m.group(2)
        if letter in "aA" and not acc:
            if letter == "a" and not note_list:
                continue                                       # lowercase bare 'a' in prose: the article
            nxt = re.match(r"\s+([a-z]+)", t[m.end():])
            if letter == "A" and nxt and nxt.group(1) not in _NOTE_QUALITY and not note_list:
                continue                                       # 'A word ...': the article at a sentence start
        out.append((letter + (acc or "")).lower())
    return out


# ── generation per level (text, answer, grade_kind) ──────────────────────────────────────────────────
def _gen(level: int) -> tuple[str, str, str]:
    r = random.choice
    if level <= 1:      # rhythm arithmetic — integer beat remainders only
        meter, total = r([("4/4", 4.0), ("3/4", 3.0), ("2/4", 2.0)])
        fills = [n for n in _DUR_BEATS if _DUR_BEATS[n] < total]
        picked = []
        while True:
            picked = [r(fills)] + ([r(fills)] if total >= 3 and random.random() < 0.6 else [])
            rem = total - sum(_DUR_BEATS[p] for p in picked)
            if rem >= 1.0 and abs(rem - round(rem)) < 1e-9:
                break
        names = " and a ".join(picked)
        return (f"In {meter} time, a measure already holds a {names}. "
                f"How many quarter-note beats are still needed to fill the measure?",
                str(int(round(rem))), "number")
    if level == 2:      # intervals in semitones (ascending)
        a, b = random.sample(["C", "D", "E", "F", "G", "A", "B"], 2)
        semis = (_SEMITONE[b.lower()] - _SEMITONE[a.lower()]) % 12
        return (f"Counting upward, how many semitones is it from {a} up to the next {b}?",
                str(semis), "number")
    if level == 3:      # scale degrees
        key = r(list(_MAJOR_SCALES))
        deg = r([2, 3, 4, 5, 6, 7])
        return (f"What is the {_ORDINAL[deg]} degree of the {key} major scale?",
                _MAJOR_SCALES[key][deg - 1], "note")
    if level == 4:      # triad spelling
        if random.random() < 0.5:
            key = r(list(_MAJOR_SCALES))
            s = _MAJOR_SCALES[key]
            return (f"Spell the {key} major triad — its three notes, from the root up.",
                    " ".join([s[0], s[2], s[4]]), "notes3")
        name = r(list(_MINOR_TRIADS))
        return (f"Spell the {name[:-1]} minor triad — its three notes, from the root up.",
                " ".join(_MINOR_TRIADS[name]), "notes3")
    if level == 5:      # key signatures
        if random.random() < 0.5:
            key = r([k for k, (n, _) in _KEY_SIG.items() if n > 0])
            n, kind = _KEY_SIG[key]
            return (f"How many {kind} are in the key signature of {key} major?", str(n), "number")
        n = random.randint(1, 4)
        kind = r(["sharps", "flats"])
        ans = next(k for k, (num, kd) in _KEY_SIG.items() if num == n and kd == kind)
        return (f"Which major key has exactly {n} {kind[:-1]}{'s' if n > 1 else ''} in its key signature?",
                ans, "note")
    # level 6: find the faulty measure in an ABC line (measure sums — the parser check made a question).
    # The faulty measure is never #1: a short opening is a legal anacrusis in composition grading, and the
    # drill must not teach the opposite rule.
    key = r(list(_MAJOR_SCALES))
    notes = "CDEFGAB"
    bad = random.randint(2, 4)
    measures = []
    for i in range(1, 5):
        m = [r(notes) + "2" for _ in range(4)]        # 4 × eighth-2 = 4 quarters = a full 4/4 measure (L:1/8)
        if i == bad:
            m = m[:-1] if random.random() < 0.5 else m + [r(notes) + "2"]   # short or long
        measures.append(" ".join(m))
    abc = f"X:1\nM:4/4\nL:1/8\nK:{key}\n|" + "|".join(measures) + "|"
    return (f"Here is a line of ABC notation:\n{abc}\nOne measure does not add up to the 4/4 meter. "
            f"Which measure is faulty — 1, 2, 3, or 4?", str(bad), "number")


def generate() -> dict:
    d = _load()
    text, ans, kind = _gen(d["level"])
    return {"text": text, "answer": ans, "kind": kind, "level": d["level"]}


# AUTHORSHIP (founder ruling D-0583, 2026-11-02, plan social_world_school): the hints and worked examples
# returned by method_hint() are the TRAVIS BRANCH of the 2026-08-14 world-answers law (teaching reaches Du
# only from a book on his shelf or from Travis). D-0583 covers the maths and music hints (one row), so
# the same rule applies here: they must NOT be generated or edited by a model; any new or changed hint is added through
# Travis. Behaviour is unchanged. Registry row: P-0024 (docs/guidelines/prompt_registry.md section 4, item 8).
def method_hint(level: int) -> str:
    """The METHOD (teach the system, don't just mark him wrong — the house pattern)."""
    if level <= 1:
        return ("Method: give each note its length in quarter-note beats — whole=4, half=2, quarter=1, "
                "eighth=½ — add up what the measure holds, and subtract from the meter's top number. "
                "Worked example: 3/4 holding a half note → 3 − 2 = 1 beat remains.")
    if level == 2:
        return ("Method: walk the keyboard upward one semitone at a time, counting each step, until you "
                "reach the target. Worked example: C→G is C-C#-D-D#-E-F-F#-G = 7 semitones.")
    if level == 3:
        return ("Method: build the major scale by the step pattern W-W-H-W-W-W-H from the key note, then "
                "count up to the asked degree. Worked example: D major = D E F# G A B C#; its 3rd is F#.")
    if level == 4:
        return ("Method: a triad stacks the 1st, 3rd and 5th degrees of the scale. Major: root + major "
                "third (4 semitones) + perfect fifth (7). Minor: root + MINOR third (3) + perfect fifth. "
                "Worked example: A minor = A + C (3 up) + E (7 up).")
    if level == 5:
        return ("Method: the circle of fifths. Sharps add in the order F C G D A E B (G major has 1, D has "
                "2, A has 3…); flats add in the order B E A D G C F (F major has 1, Bb has 2, Eb has 3…).")
    return ("Method: in ABC with L:1/8, a plain letter is an eighth; a number multiplies it (C2 = two "
            "eighths = a quarter). Add each measure's eighths: 4/4 needs 8. Count each measure between "
            "the bar lines and find the one that is over or under 8.")


def grade(response: str, answer: str, kind: str) -> bool:
    """Deterministic — never the LLM. `response` is the model's ANSWER FIELD only (J-2988, F-3685: the callers
    no longer prepend the working text, so a matching token in the working can no longer credit a miss).
    Numbers: the LAST whole number in the field, meter fractions like '4/4' ignored, is the true number;
    note: the true note is among the normalized notes named; notes3: the notes named are EXACTLY the triad's
    notes (any order, repeats fine — spelling is what is being tested; an extra note in the field is a miss)."""
    if kind == "number":
        nums = re.findall(r"(?<!\d)-?\d+", re.sub(r"\d+\s*/\s*\d+", " ", response or ""))
        return bool(nums) and nums[-1] == str(answer)
    want = _norm_notes(answer)
    got = _norm_notes(response)
    if kind == "note":
        return bool(want) and want[0] in got
    return bool(want) and set(got) == set(want)      # notes3


def record(level: int, correct: bool) -> dict:
    d = _load()
    w = d.get("window", [])
    w.append(1 if correct else 0)
    d["window"] = w[-ADVANCE_WINDOW:]
    if (len(d["window"]) >= ADVANCE_WINDOW
            and sum(d["window"]) / len(d["window"]) >= ADVANCE_ACCURACY
            and level < MAX_LEVEL):
        d["level"] = level + 1
        d["window"] = []
    d["today_done"] = d.get("today_done", 0) + 1
    _save(d)
    return d


def log(problem: str, his_answer: str, answer: str, correct: bool, level: int,
        working: str = "", raw_answer: str | None = None, item_id: str | None = None) -> None:
    """One row per independent attempt. J-2988 (F-3685): `raw_answer` (the whole answer field, capped at 400) and
    `working_head` (the first 200 chars of the working) are kept beside the old keys so a regrade is possible;
    scripts/regrade_drill_log_j2988.py is the reader."""
    try:
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), "level": level, "problem": problem[:160],
                                "his_answer": (his_answer or "")[:60], "true": answer,
                                "correct": bool(correct),
                                "raw_answer": (raw_answer if raw_answer is not None else his_answer or "")[:400],
                                "working_head": (working or "")[:200],
                                **({"item_id": item_id} if item_id else {})}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def due() -> bool:
    return _load().get("today_done", 0) < DAILY_TARGET


# ── THE COMPOSITION HAND — write a melody in ABC, graded for WELL-FORMEDNESS only ────────────────────
def compose_due() -> bool:
    return _load().get("composed_today", 0) < COMPOSE_DAILY_CAP


def compose_task() -> dict:
    """A concrete, bounded composition brief. Sometimes a Tang-poem setting (唐詩 were songs — curriculum
    continuity); the technical frame is always the same well-formed target the parser can check."""
    key = random.choice(["C", "G", "D", "F", "Am", "Em"])
    mood = random.choice(["quiet and slow", "walking and even", "bright and quick", "wandering, a little sad"])
    poem = random.random() < 0.3
    brief = (f"Compose a short melody of your own: exactly 4 measures in ABC notation, in K:{key}, "
             f"M:4/4, L:1/8 — so every measure must add up to 8 eighth-note units. Make it {mood}.")
    if poem:
        brief += (" Let it be a setting of a line from a Tang poem you have read — name the line first, "
                  "then write the tune it suggests to you.")
    return {"key": key, "mood": mood, "brief": brief}


def grade_abc(text: str, expect_key: str) -> dict:
    """DETERMINISTIC well-formedness: header fields present (M, L, K), notes parse, and each measure's
    durations sum to the meter (first and last measure may run short — anacrusis and final are legal).
    Returns {ok, measures, faults[]}. Never grades beauty — that is not a thing a parser may pretend to know."""
    try:
        t = (text or "").strip()
        faults = []
        m_meter = re.search(r"^M:\s*(\d+)/(\d+)", t, re.M)
        m_len = re.search(r"^L:\s*1/(\d+)", t, re.M)
        m_key = re.search(r"^K:\s*([A-G][b#]?m?)", t, re.M)
        if not m_meter:
            faults.append("missing M: meter header")
        if not m_len:
            faults.append("missing L: unit-length header")
        if not m_key:
            faults.append("missing K: key header")
        elif expect_key and m_key.group(1) != expect_key:
            faults.append(f"key is {m_key.group(1)}, the brief asked K:{expect_key}")
        if faults:
            return {"ok": False, "measures": 0, "faults": faults}
        num, den = int(m_meter.group(1)), int(m_meter.group(2))
        unit = int(m_len.group(1))
        expected_units = num * unit / den                      # e.g. 4/4 at L:1/8 → 8
        body = t[m_key.end():]
        body = re.sub(r"%.*", "", body)
        bars = [b for b in re.split(r"\|+", body.replace("\n", " ")) if b.strip()]
        if len(bars) < 2:
            return {"ok": False, "measures": len(bars), "faults": ["fewer than 2 measures"]}
        note_re = re.compile(r"([_^=]?)([A-Ga-gz])([,']*)(\d+)?(/(\d+)?)?")
        for i, bar in enumerate(bars):
            units = 0.0
            for m in note_re.finditer(bar):
                mult = float(m.group(4)) if m.group(4) else 1.0
                if m.group(5):                                  # /n or bare /
                    mult /= float(m.group(6)) if m.group(6) else 2.0
                units += mult
            short_ok = i in (0, len(bars) - 1)                  # anacrusis / final may run short
            if abs(units - expected_units) > 1e-6 and not (short_ok and units < expected_units):
                faults.append(f"measure {i + 1} holds {units:g} units, the meter needs {expected_units:g}")
        return {"ok": not faults, "measures": len(bars), "faults": faults}
    except Exception as exc:
        return {"ok": False, "measures": 0, "faults": [f"unparseable: {exc}"]}


def save_composition(text: str, task: dict, result: dict) -> None:
    """The artifact is kept (data/compositions/) — his pieces accumulate. ABC playback of them stays OUT
    by law until listening history is deep (self-reference arrives late)."""
    try:
        _COMPOSITIONS.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        (_COMPOSITIONS / f"{stamp}.abc").write_text(text or "", encoding="utf-8")
        with open(_COMP_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), "file": f"{stamp}.abc", "key": task.get("key"),
                                "mood": task.get("mood"), "ok": result.get("ok"),
                                "measures": result.get("measures"),
                                "faults": result.get("faults", [])[:4]}, ensure_ascii=False) + "\n")
        d = _load()
        d["composed_today"] = d.get("composed_today", 0) + 1
        _save(d)
    except Exception:
        pass


def status() -> dict:
    d = _load()
    w = d.get("window", [])
    acc = round(sum(w) / len(w), 2) if w else 0.0
    comps = 0
    try:
        comps = sum(1 for _ in open(_COMP_LOG, encoding="utf-8"))
    except Exception:
        pass
    return {"level": d["level"], "today_done": d["today_done"], "target": DAILY_TARGET,
            "window_acc": acc, "window_n": len(w), "compositions": comps,
            "composed_today": d.get("composed_today", 0)}
