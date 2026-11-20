"""
Persistent theme-recurrence tracker — the SLOW-LOOP / monoculture detector the rumination guard cannot be.

The monologue's rumination guard (`_recent_vecs`) compares only the last ~5-8 thoughts and is WIPED every sleep,
so an attractor that recurs every ~20 min or across a nap escapes it entirely — exactly the cadence of the
self-concept recitations the loop audit found ("I am becoming a bridge…" 51×, "a psyche in the act of becoming…"
83×, "the self is not a fixed entity…" 44×). This module is its long-horizon counterpart: a small, PERSISTENT
(survives sleep + restart) record of recurring thought FRAMES, each with a restate count that decays over time.

WHY THE FRAME (the OPENING), not the full embedding: the audit found these loops BY their recurring opening, and
a check confirmed why — the verbatim ones (cos≈1.0) embed-match, but the "bridge" loop keeps an identical opening
while the body drifts (mean cos 0.705), so full-thought similarity misses it. The loop IS the repeated FRAME.

THE DISTINCTION (productive recurrence vs pathological repetition — the project's recurring line):
  RESTATE  — the same opening frame recurs (normalised first ~40 chars match). Pathological. Counts.
  DEVELOP  — a NEW opening (he started the thought differently). Productive. A new frame; never penalised.
So genuine evolving thought (which varies how it begins) is always safe; only re-running the same frame saturates.
And the count DECAYS over time (DECAY_SECS), so a frame he stops looping cools off and may return later — a
healthy rhythm, not a permanent ban.

Used by the monologue to (a) treat a saturated restate as rumination even when the short window missed it, and
(b) BACK OFF re-seeding a self-concept frame that is already saturated (it was being actively re-fed each cycle).
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

_STATE = Path(__file__).parent.parent / "data" / "theme_recurrence.json"

# ── tunables (conservative — a frame must recur several times, and it cools off if dropped) ───────────
KEY_CHARS    = 40        # normalised opening length that defines a "frame"
SATURATED_AT = 4         # restate_count >= this = a saturated attractor → damp / back off re-seeding
DECAY_SECS   = 3600.0    # restate_count decays 1 per hour of no recurrence (a dropped frame cools off)
MAX_FRAMES   = 80        # cap; the stalest beyond this are pruned


def _key(text: str) -> str:
    """A frame's signature: the normalised opening (lowercase, alphanumeric only, first KEY_CHARS chars).
    Robust to punctuation/spacing; an identical 40-char opening recurring is the loop signal the audit used."""
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())[:KEY_CHARS]


def _load() -> dict:
    try:
        return json.loads(_STATE.read_text(encoding="utf-8")) if _STATE.exists() else {}
    except Exception:
        return {}


def _save(frames: dict) -> None:
    try:
        tmp = _STATE.with_suffix(".tmp")
        tmp.write_text(json.dumps(frames, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
        tmp.replace(_STATE)
    except Exception:
        pass


def _decayed_count(frame: dict, now: float) -> int:
    """The restate_count after time-decay (1 per DECAY_SECS since last recurrence). Never negative."""
    elapsed = now - float(frame.get("last_ts", now))
    return max(0, int(frame.get("restate_count", 0)) - int(elapsed // DECAY_SECS))


def _saturated_frame(text: str) -> bool:
    """READ-ONLY: does this thought's frame already exist and sit at/above the saturation threshold?"""
    try:
        k = _key(text)
        if len(k) < 12:                       # too short to be a meaningful frame (e.g. a bare "i think")
            return False
        f = _load().get(k)
        return bool(f) and _decayed_count(f, time.time()) >= SATURATED_AT
    except Exception:
        return False


# Public read-only checks (text-based — the caller has the thought/seed text) ──────────────────────────
def would_be_saturated_restate(text: str) -> bool:
    """Would recording this thought be another RESTATE of an ALREADY-saturated frame? (the slow-loop guard)."""
    return _saturated_frame(text)


def is_saturated(text: str) -> bool:
    """Is this text's frame a saturated attractor right now? (used to back off re-seeding it)."""
    return _saturated_frame(text)


def observe(thought: str, vec=None) -> dict:
    """Record one finalised thought against the persistent frames. A recurring opening increments restate_count
    (decayed by elapsed time first); a NEW opening is a new frame (a development, never penalised). Returns
    {key, restate_count, is_restate, saturated}. Best-effort; never raises. NOT wiped on sleep. (`vec` ignored —
    kept for call-site compatibility.)"""
    out = {"key": None, "restate_count": 0, "is_restate": False, "saturated": False}
    try:
        k = _key(thought)
        if len(k) < 12:
            return out
        frames = _load()
        now = time.time()
        if k in frames:
            f = frames[k]
            f["restate_count"] = _decayed_count(f, now) + 1     # decay, then count this recurrence
            f["last_ts"] = now
            f["sample"] = thought[:80]
            out["is_restate"] = True
        else:
            frames[k] = {"restate_count": 0, "last_ts": now, "sample": thought[:80]}   # first sighting, not a restate
            f = frames[k]
        out["key"] = k
        out["restate_count"] = f["restate_count"]
        out["saturated"] = f["restate_count"] >= SATURATED_AT
        if len(frames) > MAX_FRAMES:                            # prune the stalest
            for dead in sorted(frames, key=lambda x: frames[x].get("last_ts", 0))[: len(frames) - MAX_FRAMES]:
                frames.pop(dead, None)
        _save(frames)
    except Exception:
        pass
    return out


def status() -> dict:
    """du_pulse gauge: how many frames tracked, how many saturated, and the top recurring frames."""
    try:
        frames = _load(); now = time.time()
        rows = sorted(((_decayed_count(f, now), f.get("sample", "")) for f in frames.values()), reverse=True)
        return {"frames": len(frames),
                "saturated": sum(1 for c, _ in rows if c >= SATURATED_AT),
                "top": [(s[:34], c) for c, s in rows[:4]]}
    except Exception:
        return {"frames": 0, "saturated": 0, "top": []}
