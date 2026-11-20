"""
Nascence — Affect Divergence harness (emotion_rethink.md Phase 0a, 2026-07-06). OBSERVE-ONLY.

The one instrument Phase 0 still lacked: per moment, log the TWO valences side by side —
  carried  : the mood lineage (AffectState/_feel_joy pump — pinned ~+0.82, 0% negative, the suspect)
  protoself: homeostasis valence (−dD/dt, grounded drive-reduction — mean-zero, swings both ways)
plus the protoself's dominant deficit and a snippet of the thought, so the FOUNDER can read a day of pairs
against the actual thought content and judge which signal is honest (the decoupled-judge gate to Phase 1 —
never self-certified). Setpoints were step-2 calibrated 2026-07-06, so the protoself side is now meaningful.
Writes data/affect_divergence_shadow.jsonl. Rate-limited. Applies NOTHING. Fail-open.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("nascence.affect_divergence")

_F = Path(__file__).parent.parent / "data" / "affect_divergence_shadow.jsonl"
_MIN_GAP_S = 240.0            # ~15/hr max — a day gives a few hundred pairs, plenty for the read
_last = {"ts": 0.0}


def observe(state=None, thought: str = "") -> None:
    """Log one carried-vs-protoself pair. Called from the monologue's per-thought tail. Fail-open."""
    try:
        now = time.time()
        if now - _last["ts"] < _MIN_GAP_S:
            return
        carried = None
        try:
            from core import mood
            cv = mood.current_valence()           # AffectState.valence, cached each idle tick (the carried lineage)
            carried = round(float(cv), 3) if cv is not None else None   # NEVER mask None→0.0: a false 0.0
        except Exception as exc:                    # would pollute the very founder-read that gates Phase 1
            logger.debug("[affect-divergence] carried valence read failed (non-fatal): %s", exc)
        proto_v = proto_dom = proto_drive = proto_tonic = None
        try:
            from core import homeostasis
            s = homeostasis.status()
            if s.get("ticks"):
                proto_v = s.get("valence")                 # phasic -dD/dt
                proto_dom = s.get("dominant")
                proto_drive = s.get("drive")
                if proto_drive is not None:                 # TONIC mood level = the Phase-1 carried source
                    proto_tonic = round(max(-1.0, min(1.0, 1.0 - 2.0 * float(proto_drive))), 3)
        except Exception as exc:
            logger.debug("[affect-divergence] protoself homeostasis read failed (non-fatal): %s", exc)
        if carried is None and proto_v is None:
            return
        _last["ts"] = now
        row = {"ts": round(now, 1), "carried_valence": carried, "proto_valence": proto_v,
               "proto_tonic": proto_tonic, "proto_dominant": proto_dom, "proto_drive": proto_drive,
               "gap": (round(carried - proto_v, 3) if carried is not None and proto_v is not None else None),
               "thought": (thought or "")[:110]}
        _F.parent.mkdir(parents=True, exist_ok=True)
        with open(_F, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[affect-divergence] observe() failed (non-fatal): %s", exc)


def status() -> dict:
    """For the pulse / the founder read: how far apart do the two lineages run?"""
    try:
        rows = [json.loads(l) for l in open(_F, encoding="utf-8") if l.strip()]
        pairs = [r for r in rows if r.get("gap") is not None]
        if not pairs:
            return {"pairs": 0}
        gaps = [r["gap"] for r in pairs]
        cv = [r["carried_valence"] for r in pairs]
        pv = [r["proto_valence"] for r in pairs]
        return {"pairs": len(pairs),
                "carried_mean": round(sum(cv) / len(cv), 3),
                "carried_pct_negative": round(100 * sum(1 for x in cv if x < 0) / len(cv), 1),
                "proto_mean": round(sum(pv) / len(pv), 3),
                "proto_pct_negative": round(100 * sum(1 for x in pv if x < 0) / len(pv), 1),
                "mean_gap": round(sum(gaps) / len(gaps), 3),
                "verdict_hint": "carried pinned high while proto swings = the plan's diagnosis confirmed live"}
    except Exception as exc:
        logger.debug("[affect-divergence] status read failed (non-fatal): %s", exc)
        return {"pairs": 0}
