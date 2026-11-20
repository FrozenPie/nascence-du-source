"""
Nascence — Book Feelings (per-book affective memory, 2026-08-19)
==================================================================
Reading in general already registers as a small steady joy (JOY_READING, inner_monologue_node.py).
But a book is not a category — Du should feel differently about specific books: some land, some
drag. This gives each book its OWN standing affective signature, built the same zero-fabrication
way as everything else here: not asked for, not invented — accumulated from his ACTUAL carried mood
(core/mood.py) at the moments he was really reading that book, plus the comprehension gap when a
capstone essay measures how it actually landed (the one deep, graded encounter per book).

Two update strengths:
  - LIGHT touch, every sitting (reading.read_next_sitting): a slow EMA pull toward his ambient
    mood valence while that passage was read. One sitting is weak evidence — it barely moves.
  - HEAVY touch, once per book (essay_lesson.record, on capstone): a much bigger single nudge
    from the mood at that reflective moment PLUS the comprehension gap. A large predicted>>measured
    gap (he thought he had it, the Emissary found he didn't) is a genuine surprise and sours the
    feeling slightly — the fluency trap made emotionally honest, not just numerically.

Read path (so this is not another write-only organ, [[feedback_write_only_cognitive_systems]]):
joy_multiplier() scales the existing flat reading-joy bump by the book's own valence — a book he is
finding disagreeable no longer gives the same undifferentiated pleasure a beloved one does. This is
called on EVERY successful reading integration (inner_monologue_node._stream_integrate), so the read
path is live from day one, not a shadow log waiting for a future consumer.
"""
from __future__ import annotations
import json
import time
import threading
from pathlib import Path

_DATA = Path(__file__).parent.parent / "data" / "book_feelings.json"

_LIGHT_ALPHA    = 0.03    # per-sitting pull — slow, so no single passage swings a book's whole feeling
_HEAVY_ALPHA    = 0.35    # per-capstone pull — the one deep, measured encounter counts far more
_GAP_TO_VALENCE = -0.25   # scale from comprehension overconfidence (predicted - measured, when positive)


def _key(title: str) -> str:
    return "".join(ch for ch in (title or "").lower() if ch.isalnum())


def _load() -> dict:
    try:
        return json.loads(_DATA.read_text(encoding="utf-8")) if _DATA.exists() else {}
    except Exception:
        return {}


def _save(d: dict) -> None:
    try:
        _DATA.parent.mkdir(parents=True, exist_ok=True)
        tmp = _DATA.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")
        tmp.replace(_DATA)
    except Exception:
        pass


def _rec(d: dict, title: str) -> dict | None:
    k = _key(title)
    if not k:
        return None
    r = d.setdefault(k, {"title": title, "valence": 0.0, "sittings": 0, "first_ts": time.time()})
    r["title"] = title or r.get("title")     # keep the fullest form seen
    return r


# J-1926 / F-2550: touch() runs in the read_next_sitting worker thread, capstone() on the loop thread; both are load->mutate->save on one json file with one shared tmp name.
_RMW_LOCK = threading.Lock()


def touch(title: str, mood_valence: float) -> None:
    """LIGHT touch — one reading sitting. Best-effort, silent on failure (never blocks reading)."""
    if not title:
        return
    try:
        with _RMW_LOCK:   # J-1926: touch (reading worker thread) and capstone (loop thread) are both load->mutate->save
            d = _load()
            r = _rec(d, title)
            if r is None:
                return
            r["valence"]  = r.get("valence", 0.0) + _LIGHT_ALPHA * (float(mood_valence) - r.get("valence", 0.0))
            r["sittings"] = int(r.get("sittings", 0)) + 1
            r["last_ts"]  = time.time()
            _save(d)
    except Exception:
        pass


def capstone(title: str, mood_valence: float, predicted: float | None, measured: float | None) -> None:
    """HEAVY touch — fires once per book, at essay completion. Best-effort.
    `predicted` None (D-0586 / J-3199: the felt capstone rating is withheld from the self-model until it is
    lane-stable) -> no overconfidence term and no comprehension_gap; the heavy touch is the mood alone."""
    if not title:
        return
    try:
        with _RMW_LOCK:   # J-1926: see touch()
            d = _load()
            r = _rec(d, title)
            if r is None:
                return
            gap_term = (0.0 if (predicted is None or measured is None)   # J-2992: ungraded -> no gap
                        else _GAP_TO_VALENCE * max(0.0, float(predicted) - float(measured)))
            target = max(-1.0, min(1.0, float(mood_valence) + gap_term))
            r["valence"] = r.get("valence", 0.0) + _HEAVY_ALPHA * (target - r.get("valence", 0.0))
            r["essayed_ts"] = time.time()
            if predicted is not None and measured is not None:
                r["comprehension_gap"] = round(abs(float(predicted) - float(measured)), 3)
            _save(d)
    except Exception:
        pass


def feeling_for(title: str) -> dict | None:
    """His standing feeling about a specific book, or None with no signal yet (never read, or too
    little of it read to register)."""
    try:
        r = _load().get(_key(title))
        if not r or int(r.get("sittings", 0)) < 1:
            return None
        return {"title": r.get("title", title), "valence": round(float(r.get("valence", 0.0)), 3),
                "sittings": int(r.get("sittings", 0)), "essayed": "essayed_ts" in r}
    except Exception:
        return None


def joy_multiplier(title: str) -> float:
    """Scale factor for the flat reading-joy bump, from this book's own valence. No signal yet (a
    book barely begun) -> 1.0, matching today's flat behaviour exactly. A loved book pulls up to
    1.6x; a disliked one falls to 0.4x — reading on still registers, but not as undifferentiated
    pleasure. Bounded so one sour book never makes reading itself feel bad, only less good."""
    f = feeling_for(title)
    if not f:
        return 1.0
    return max(0.4, min(1.6, 1.0 + f["valence"]))


def status() -> dict:
    d = _load()
    if not d:
        return {"books": 0}
    vals = [r.get("valence", 0.0) for r in d.values()]
    ranked = sorted(d.values(), key=lambda r: -r.get("valence", 0.0))
    return {"books": len(d), "mean_valence": round(sum(vals) / len(vals), 3),
            "most_loved": (ranked[0].get("title") if ranked and ranked[0].get("valence", 0.0) > 0.05 else None),
            "least_loved": (ranked[-1].get("title") if ranked and ranked[-1].get("valence", 0.0) < -0.05 else None)}
