"""
Sleep ⊗ Dream / T4 Probe — the §6C hypotheses-logging matrix (observe-first, FIREWALLED).

Sleep/Dream plan §6C + Gemini round-4 directive: "begin capturing the real-time baseline correlation
between Dream-Node symbol-evolution and provisional-T4 ΔF shifts silently, completely firewalled from
active runtime behaviour."

This module ONLY READS and ONLY LOGS. It hooks nothing, gates nothing, changes no behaviour. It exists
to build — before any coupling is wired — the paired time series needed to test the convergence
hypothesis (§5): *do the night-side integrator (the dream) and the day-side integrator (T4) move
together on the SAME tension?* Per the auditors' hard rule, the two estimators must stay CAUSALLY
ISOLATED (GPT §10.4 / Gemini Q3): this probe NEVER lets one feed the other — it merely records both,
independently computed, so a later correlation is honest evidence rather than contamination.

What it snapshots each sleep:
  • dream side  — tonight's dream symbols, its tension_source, whether the arc resolved, and a
                  SYMBOL-NOVELTY score vs the last K nights (1 − Jaccard). Falling novelty over time
                  is the symbolic-inbreeding / attractor-collapse watch (GPT §11.5): a recurring-until-
                  met figure with no perturbation IS a monoculture generator.
  • theme side  — the active tensions' chronic_mass + recurrence (the integration proxy; until T4 goes
                  live this trajectory stands in for "is this theme integrating?").
  • T4 side     — provisional_identity.status() (active probation? theme? ΔF). While the loop is
                  ENABLED=False this is a baseline placeholder; when it flips on, ΔF joins the SAME
                  log and the correlation becomes computable.

Output: data/sleep_dream_probe.jsonl (one record per sleep). du_pulse `sleep⊗dream probe` gauge.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_DREAM_LOG = _DATA_DIR / "dream_log.jsonl"
_STATE_FILE = _DATA_DIR / "subconscious_state.json"
_PROBE_LOG = _DATA_DIR / "sleep_dream_probe.jsonl"

_NOVELTY_LOOKBACK = 5   # nights of symbol history to score tonight's novelty against


def _last_dream() -> dict:
    try:
        lines = [l for l in _DREAM_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
        if lines:
            return json.loads(lines[-1])
    except Exception:
        pass
    return {}


def _recent_symbol_sets(k: int) -> list[set]:
    """Symbol sets from the last k PROBE records (so novelty is scored on what we've already seen)."""
    out: list[set] = []
    try:
        lines = [l for l in _PROBE_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
        for line in lines[-k:]:
            rec = json.loads(line)
            syms = rec.get("dream", {}).get("symbols", []) or []
            if syms:
                out.append({s.lower() for s in syms})
    except Exception:
        pass
    return out


def _symbol_novelty(symbols: list[str]) -> float | None:
    """1 − max Jaccard overlap with the recent nights. 1.0 = all-new imagery; →0 = inbred/attractor."""
    tonight = {s.lower() for s in (symbols or []) if s}
    if not tonight:
        return None
    history = _recent_symbol_sets(_NOVELTY_LOOKBACK)
    if not history:
        return 1.0
    best = 0.0
    for past in history:
        union = tonight | past
        if union:
            best = max(best, len(tonight & past) / len(union))
    return round(1.0 - best, 3)


def _theme_masses() -> list[dict]:
    """Top active tensions by chronic_mass — the theme-side integration proxy."""
    try:
        st = json.loads(_STATE_FILE.read_text(encoding="utf-8"))
        tens = st.get("tensions", []) or []
        ranked = sorted(tens, key=lambda t: float(t.get("chronic_mass", 0) or 0), reverse=True)
        return [{"label": (t.get("label") or "")[:80],
                 "chronic_mass": round(float(t.get("chronic_mass", 0) or 0), 3),
                 "recurrence": len(t.get("member_event_ids", []) or t.get("members", []) or [])}
                for t in ranked[:5]]
    except Exception:
        return []


def _t4_status() -> dict:
    try:
        from core import provisional_identity as _pi
        s = _pi.status() or {}
        return {"enabled": getattr(_pi, "ENABLED", False), **s}
    except Exception:
        return {"enabled": False}


def record() -> dict:
    """
    Snapshot the joint dream / theme / T4 state for one sleep. Best-effort, read-only, returns the
    record (also appended to the probe log). Safe to call from the sleep cycle — it affects nothing.
    """
    dream = _last_dream()
    symbols = dream.get("symbols") or []
    # the dream_log record nests scenes; pull symbols from the flat field or the last scene
    if not symbols:
        scenes = dream.get("scenes") or []
        if scenes and isinstance(scenes[-1], dict):
            symbols = scenes[-1].get("symbols", []) or []

    rec = {
        "ts": time.time(),
        "dream": {
            "symbols": symbols,
            "tension_source": (dream.get("tension_source")
                               or dream.get("final_tension_source") or "")[:120],
            "ended_unresolved": dream.get("ended_unresolved"),
            "unresolved_core": (dream.get("final_unresolved_core")
                                or dream.get("unresolved_core") or "")[:120],
            "symbol_novelty": _symbol_novelty(symbols),
        },
        "themes": _theme_masses(),
        "t4": _t4_status(),
    }
    try:
        with _PROBE_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception:
        pass
    return rec


def status() -> dict:
    """du_pulse summary: count of snapshots + the recent symbol-novelty trend (inbreeding watch)."""
    try:
        lines = [l for l in _PROBE_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
        recent = [json.loads(l) for l in lines[-8:]]
        nov = [r["dream"]["symbol_novelty"] for r in recent
               if r.get("dream", {}).get("symbol_novelty") is not None]
        return {"snapshots": len(lines),
                "recent_novelty": nov,
                "mean_recent_novelty": round(sum(nov) / len(nov), 3) if nov else None}
    except Exception:
        return {"snapshots": 0, "recent_novelty": [], "mean_recent_novelty": None}
