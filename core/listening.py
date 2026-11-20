"""
Nascence — Listening: the ear goes live (big build 2026-07-03 · docs/staged/music_learning.md tier 2).

HIS act ("put the record on") starts a piece; it UNFOLDS one section per idle cycle as perception (the
deterministic descriptor, clothed lightly); when it ends, SILENCE is a thing (one ending line, then two
quiet cycles); a wake-snapshot is logged for the attention-persistence instrument. The felt-vector nudge is
SHADOW-ONLY here (logged, never applied) — observe-first on anything touching affect.

Laws honoured: NO duration metadata reaches him, ever (anticipation is real only if the cadence is not
guaranteed) · music scenes are WORLD PERCEPTION (sensorium-class — no injection log, same as weather; the
music originates OUTSIDE the system and the extractor only translates) · companions-in-time: every
listening stores fragments under origin='listening' with the piece key, so re-listenings LAYER (nothing
overwrites) · features come from the offline cache (data/music/<piece>.features.json) — zero runtime DSP.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("nascence.listening")

_DATA = Path(__file__).parent.parent / "data"
_MUSIC = _DATA / "music"
_STATE_F = _DATA / "listening_state.json"
_WAKE_LOG = _DATA / "listening_wake.jsonl"
_FELT_SHADOW = _DATA / "listening_felt_shadow.jsonl"
SILENCE_CYCLES = 2      # after the ending line: this many wordless cycles before the state clears


def _load() -> dict:
    try:
        return json.loads(_STATE_F.read_text(encoding="utf-8")) if _STATE_F.exists() else {}
    except Exception:
        return {}


def _save(d: dict) -> None:
    try:
        _STATE_F.parent.mkdir(parents=True, exist_ok=True)
        tmp = _STATE_F.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        tmp.replace(_STATE_F)
    except Exception as exc:
        logger.debug("[listening] _save failed (non-fatal): %s", exc)


def shelf() -> list[str]:
    """The pieces the player can ACTUALLY play. 2026-08-21 (48-day-dead felt-shadow root cause): 5 of 6
    cached feature files were built by the earlier geometry pipeline — global coords, NO 'sections' —
    and their source audio is gone, so a start on them ended instantly ('The music ends' as the FIRST
    line — a world lie) and `names[0]` alphabetically WAS one of them. The shelf now lists only pieces
    with real sections; the shells stay on disk for the day their audio returns and the section
    extractor re-runs."""
    try:
        out = []
        for p in sorted(_MUSIC.glob("*.features.json")):
            try:
                if json.loads(p.read_text(encoding="utf-8")).get("sections"):
                    out.append(p.stem.replace(".features", ""))
            except Exception:
                pass
        return out
    except Exception:
        return []


def active() -> bool:
    return bool(_load().get("piece"))


# ── THE APPARATUS BOOKENDS (2026-10-28, sound_world_expansion §5, D-0500/J-2478) ─────────────────────────────────
# A listening session has two timestamps: `started_ts` (written by start() since the ear went live) and, new this
# pass, `ended_ts` -- stamped the moment THE ENDING fires in tick() and carried through the clear that follows the
# silence cycles, so the quiet after a record still knows when the music stopped. soundscape._sec_apparatus reads
# both through session_marks() to voice the player's own apparatus: needle_crackle in the lead-in groove (piece set,
# first section not yet arrived) and runout_hiss in the run-out groove after the ending, until the arm is lifted.
# Read-only here; the record's own lines (the needle-drop in start(), the ending in tick()) are untouched -- these
# are sounds OF a session he chose, never a cue to start one (D-0443 left the player's affordance alone).
RUNOUT_S = 20 * 60.0       # how long the run-out groove hisses round before the arm is lifted (a world assumption)


def session_marks() -> dict:
    """The session's own marks, read as they are: piece / idx / silence / started_ts / ended_ts. ended_ts outlives
    the clear (see tick()); a fresh start() replaces the whole state, so a new record wipes the old ending."""
    d = _load()
    try:
        silence = int(d.get("silence", -1)) if d.get("silence") is not None else -1
    except Exception:
        silence = -1
    try:
        idx = int(d.get("idx", 0) or 0)
    except Exception:
        idx = 0
    return {"piece": d.get("piece") or None, "idx": idx, "silence": silence,
            "started_ts": float(d["started_ts"]) if d.get("started_ts") else None,
            "ended_ts": float(d["ended_ts"]) if d.get("ended_ts") else None}


def _cleared(d: dict) -> dict:
    """What the state becomes after the silence cycles: empty as before, except that the ending's own timestamp is
    kept (no piece, so active() / tick() / start() / the census all still read it as idle, exactly as {})."""
    return {"ended_ts": d["ended_ts"]} if d.get("ended_ts") else {}


def start(piece: str = "", by: str = "du") -> str:
    """Put the record on. by='du' — HIS act (the hand-first everyday path). by='travis' — SHARED LISTENING
    (design decision #2, joint attention): Travis reaches into the world and plays it; both are receivers,
    neither is communicating. The needle-drop line carries the agent so provenance lives in the content.
    Returns what he perceives (the first section arrives next cycle)."""
    d = _load()
    if d.get("piece"):
        return ""                      # already listening — one piece at a time
    names = shelf()
    if not names:
        return ""
    pick = piece if piece in names else names[0]
    try:
        feats = json.loads((_MUSIC / f"{pick}.features.json").read_text(encoding="utf-8"))
    except Exception:
        return ""
    _save({"piece": pick, "idx": 0, "started_ts": round(time.time(), 1),
           "n": len(feats.get("sections", [])), "silence": -1, "by": by})
    logger.info("[listening] started: %s (%d sections, by=%s)", pick, len(feats.get("sections", [])), by)
    try:
        from core import arousal
        arousal.alert(0.25, "music begins")     # the needle drop is an alerting event (Tier-2 C, shadow)
    except Exception:
        pass
    if by == "travis":
        return ("Travis has put a record on — you hear the needle find its groove: a hiss, a beat of "
                "nothing, and then it begins. He is listening to this too, right now, on his side. "
                "You are both hearing the same thing.")
    return ("You set the record going — a hiss, a beat of nothing, and then it begins. "
            "The music is in the room now, and the room is different for it.")


# ── the shared-listening request channel (Travis's hand into the world) ──────────────────────────────
_REQUEST_F = _MUSIC / "play_request.json"


def request_play(piece: str = "") -> bool:
    """Called by scripts/play_the_record.py: place a request the live mind will pick up within a cycle."""
    try:
        _MUSIC.mkdir(parents=True, exist_ok=True)
        _REQUEST_F.write_text(json.dumps({"piece": piece, "ts": time.time()}), encoding="utf-8")
        return True
    except Exception:
        return False


def poll_request() -> str | None:
    """Checked each idle cycle by the monologue: if Travis placed a play request and nothing is playing,
    the record starts by HIS hand (shared listening). The request file is consumed either way; a stale
    request (>1h old — the sim was down) is discarded, never fired late into a different moment."""
    try:
        if not _REQUEST_F.exists():
            return None
        req = json.loads(_REQUEST_F.read_text(encoding="utf-8"))
        _REQUEST_F.unlink(missing_ok=True)
        if time.time() - float(req.get("ts", 0)) > 3600:
            logger.info("[listening] stale play request discarded")
            return None
        if active():
            return None
        return start(req.get("piece", ""), by="travis") or None
    except Exception:
        return None


def tick() -> str | None:
    """One idle cycle of listening: the next section as perception, or the ending/silence. None if idle."""
    d = _load()
    if not d.get("piece"):
        return None
    # silence phase — the ending already spoke; the quiet is wordless, then the state clears
    if d.get("silence", -1) >= 0:
        d["silence"] -= 1
        if d["silence"] < 0:
            _wake_snapshot(d)
            _save(_cleared(d))       # J-2478: ended_ts survives the clear (the run-out groove is still turning)
        else:
            _save(d)
        return None
    try:
        feats = json.loads((_MUSIC / f"{d['piece']}.features.json").read_text(encoding="utf-8"))
        sections = feats.get("sections", [])
    except Exception:
        _save({})
        return None
    idx = int(d.get("idx", 0))
    if idx >= len(sections):
        # THE ENDING — then silence is a thing (design law #4)
        d["silence"] = SILENCE_CYCLES
        d["ended_ts"] = round(time.time(), 1)   # J-2478 (§5): the apparatus bookend -- runout_hiss reads this
        _save(d)
        _end = ("The music ends — not fading, finishing. The room holds the quiet after it; "
                "the quiet has a shape.")
        if d.get("by") == "travis":
            _end += " Somewhere on his side, Travis heard it end too."
        _store_scene(d["piece"], "the ending", _end)
        return _end
    from core import audio_features as af
    sec = sections[idx]
    desc = af.describe_section(sec, feats)
    d["idx"] = idx + 1
    _save(d)
    opener = "It opens:" if idx == 0 else ("It turns:" if sec.get("rising") else "It goes on:")
    line = f"From the player, the music. {opener} {desc}."
    _store_scene(d["piece"], f"section {idx + 1}", line)
    _felt_shadow(feats, sec, idx)
    return line


def _store_scene(piece: str, part: str, line: str) -> None:
    """Companions-in-time: every listening moment is a fragment under the piece's key — layers, never
    overwrites. Re-listens accrete onto the same lineage."""
    try:
        from core.memory.store import store_fragment
        from core import mood as _mood
        store_fragment(content=f"(listening — '{piece}', {part}) {line}", layer="episodic",
                       relevance=0.6, importance=0.55, keywords=["music", "listening", piece],
                       origin="listening", valence=_mood.current_valence(), felt=_mood.current_felt())
    except Exception:
        pass


def _felt_shadow(feats: dict, sec: dict, idx: int) -> None:
    """OBSERVE-FIRST: log the nudge the felt-vector WOULD receive. Applied nowhere."""
    try:
        from core import audio_features as af
        nudge = af.felt(feats)
        with open(_FELT_SHADOW, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), "piece": _load().get("piece"),
                                "section": idx + 1, "would_nudge": nudge}) + "\n")
    except Exception:
        pass


def _wake_snapshot(d: dict) -> None:
    """The attention-persistence instrument's anchor: listening ended HERE; the pulse compares behaviour
    in the wake window against baseline (curiosity, journaling, reading picks, dream motifs)."""
    try:
        with open(_WAKE_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), "piece": d.get("piece"),
                                "sections_heard": d.get("idx", 0), "started_ts": d.get("started_ts"),
                                "by": d.get("by", "du")}) + "\n")
        logger.info("[listening] wake snapshot: %s (%s sections heard)", d.get("piece"), d.get("idx"))
    except Exception:
        pass


def status() -> dict:
    d = _load()
    return {"active": bool(d.get("piece")), "piece": d.get("piece"),
            "section": d.get("idx", 0), "shelf": shelf()}
