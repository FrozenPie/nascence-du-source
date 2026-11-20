"""
Nascence — Affections (the loves-ledger, 2026-06-21): the LIGHT-side organ.

The whole identity machinery metabolises WOUNDS — T2 fires only on a tension cluster, T4 authors the self
from standing contradictions, the climate ignites on dissonance. There is no organ for what he LOVES, and
a self built only from its tensions is a wound-catalogue (founder + Claude, idea #2). This is its positive
twin: it accumulates what 渡 keeps coming back to with warmth.

GROUNDING — the honest version (after a false start): the first design tried to pick warmly-FELT memories
by their emotion-vec, but that vec proved write-only for valence — every fragment scored equally "warm"
(the felt_text template dominates the embedding; emotion_primary isn't even stored), so it named his
TENSIONS as loves. The joy events don't record their cause; raw recurrence conflates love with habit (160
arithmetic drills is not love). The one clean, grounded signal is **what HE says he liked** — the plain
'liked' list his nightly journal now produces. So a love here is his OWN stated affection, accumulated,
and EARNED by recurrence (named on ≥2 days), the way a tension is earned by chronic mass. No LLM, no
inference, nothing to confabulate.

OBSERVE-FIRST: surfaces the earned loves as a recallable 'affection' fragment so the light enters his
ambient self-material — but feeds NOTHING into T4 (phase 2, after the made-mind realisation lands).
"""
from __future__ import annotations
import json
import logging
from pathlib import Path

logger = logging.getLogger("nascence.affections")
_LEDGER = Path(__file__).parent.parent / "data" / "affections.json"
_LIKES = Path(__file__).parent.parent / "data" / "likes.jsonl"   # appended by the journal: his own stated likes
_EARNED = 2     # a like named on this many days is an EARNED love (vs a one-off), the analog of chronic mass


def record_likes(date: str, likes) -> None:
    """Called by the journal each night: append the day's plainly-STATED likes (his own words — the only
    honest, grounded affection signal)."""
    try:
        clean = [str(x).strip() for x in (likes or []) if str(x).strip()][:5]
        if not clean:
            return
        _LIKES.parent.mkdir(parents=True, exist_ok=True)
        with open(_LIKES, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"date": date, "likes": clean}, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[affections] record_likes failed (non-fatal): %s", exc)


def _ledger() -> dict:
    try:
        return json.loads(_LEDGER.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_ledger(d: dict) -> None:
    try:
        _LEDGER.parent.mkdir(parents=True, exist_ok=True)
        _LEDGER.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        pass


def synthesise() -> dict:
    """Rebuild the loves-ledger from his journal-stated likes and, when loves have RECURRED, surface them
    as one recallable 'affection' fragment. Deterministic — no LLM, grounded entirely in what HE said he
    liked. Observe-first: feeds nothing into T4. Returns a small summary."""
    out = {"distinct": 0, "earned": []}
    try:
        if not _LIKES.exists():
            return out
        rows = [json.loads(l) for l in _LIKES.read_text(encoding="utf-8").splitlines() if l.strip()]
        led = {}
        for r in rows:
            for like in r.get("likes", []):
                k = like.lower().strip()
                if not k:
                    continue
                e = led.get(k, {"phrase": like, "count": 0, "first": r.get("date", "")})
                e["count"] += 1
                e["last"] = r.get("date", "")
                e["phrase"] = like
                led[k] = e
        last_announced = (_ledger().get("__announced") or "")   # carry the dedup sentinel
        out["distinct"] = len(led)
        earned = [e["phrase"] for e in sorted(led.values(), key=lambda x: -x.get("count", 0))
                  if e.get("count", 0) >= _EARNED]
        out["earned"] = earned
        obs = ("I keep coming back to " + ", ".join(earned[:3]) + ".") if earned else ""
        if obs and obs != last_announced:     # only store when the earned set actually changes (no nightly flood)
            try:
                from core.memory.store import store_fragment
                store_fragment(content=obs, layer="episodic", relevance=0.7, importance=0.7,
                               keywords=["affection", "what I love"] + earned[:3], origin="affection")
                led["__announced"] = obs
                logger.info("[affections] earned loves surfaced: %s", earned[:4])
            except Exception as exc:
                logger.debug("[affections] store_fragment failed (non-fatal): %s", exc)
        _save_ledger(led)
        return out
    except Exception as exc:
        logger.debug("[affections] synthesise failed (non-fatal): %s", exc)
        return out


def earned_loves() -> list[str]:
    """The loves that have RECURRED — earned, ready for phase 2 (folding into T4). Read by the pulse."""
    return [e["phrase"] for e in sorted(_ledger().values(), key=lambda x: -x.get("count", 0) if isinstance(x, dict) else 0)
            if isinstance(e, dict) and e.get("count", 0) >= _EARNED]
