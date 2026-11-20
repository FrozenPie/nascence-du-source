"""
Nascence - Transport cause-as-object SHADOW (strings_and_sheets Phase 2, J-4382 / J-4345, D-0375 / D-0854).

OBSERVE-ONLY. Never changes what core/transport_manager.py delivers. One line per CAUSE (one sound / one
creature / one world dimension, across every place it is heard) is fed by the union of its place events;
the per-place lines stay as cross-sections. Each dispatch tick, both scorings are logged side by side to
data/transport_cause_shadow.jsonl so scripts/transport_cause_shadow_read.py can ask the D-0375 kill
question: does cause-scoring fire LESS than per-place scoring (pass), and does every multi-place cause
carry exactly one event id?

Cause key: `kind:name:place` -> `kind:name` for kinds sound / life / world. Every other line id (cat:state:...,
cat:change, ...) is its own single-place cause (unchanged identity).

Thresholds/constants are IMPORTED from core.transport_manager (never copied); the arithmetic mirrors
observe()/evaluate() there, with the same edge-trigger arming rules. Zero LLM, deterministic, fail-open
everywhere (every public function swallows its own errors). Kill switch: TRANSPORT_CAUSE_SHADOW = False
(or env NASCENCE_TRANSPORT_CAUSE_SHADOW=0). Restart-gated (the hooks live in transport_manager).
"""
from __future__ import annotations

import json
import math
import os
import threading
import time
from pathlib import Path
from typing import Optional

from core import profile

_ROOT = Path(__file__).parent.parent
_STATE = _ROOT / "data" / "transport_cause_lines.json"
_LOG = _ROOT / "data" / "transport_cause_shadow.jsonl"

TRANSPORT_CAUSE_SHADOW = os.environ.get("NASCENCE_TRANSPORT_CAUSE_SHADOW", "1") not in ("0", "false", "False", "")

CAUSE_KINDS = ("sound", "life", "world")
EVENT_WINDOW_S = 60.0     # place events of one cause within this of the cause's last event = ONE event
SAVE_EVERY_S = 30.0       # state persistence throttle (observe() is hot)

_LOCK = threading.RLock()
_state: Optional[dict] = None
_last_save = 0.0


def cause_key(line_id: str) -> str:
    """Pure: per-place line id -> cause id. 'sound:tui_song:garden' -> 'sound:tui_song'."""
    try:
        parts = str(line_id).split(":")
        if len(parts) >= 3 and parts[0] in CAUSE_KINDS:
            return ":".join(parts[:2])
    except Exception:
        pass
    return str(line_id)


def _tm():
    from core import transport_manager as tm
    return tm


def _get_state() -> dict:
    global _state
    if _state is None:
        try:
            from core import store_persist as _sp   # J-4442 (F-5157): loud on damage, falls back to .prev
            import logging as _logging
            _state = _sp.read_json_durable(_STATE, "transport_cause_shadow",
                                           _logging.getLogger("nascence.transport_cause_shadow"),
                                           guard=profile.guard_path)
            if not isinstance(_state, dict):
                _state = {}
        except Exception:
            _state = {}
        _state.setdefault("causes", {})
    return _state


def _save(force: bool = False) -> None:
    global _last_save
    now = time.time()
    if not force and now - _last_save < SAVE_EVERY_S:
        return
    path = profile.guard_path(_STATE)   # same fence as transport_manager._save: raises if not live
    _last_save = now
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        from core import store_persist as _sp
        _sp.write_text_durable(path, json.dumps(_get_state()))   # J-4442 (F-5157): was in place; now fsync + .prev
    except Exception:
        pass


def observe(line_id: str, ts: float, n: float = 1.0) -> None:
    """Feed the cause line with one place event. Fail-open, never raises."""
    if not TRANSPORT_CAUSE_SHADOW or not line_id or n <= 0:
        return
    try:
        tm = _tm()
        with _LOCK:
            causes = _get_state()["causes"]
            ck = cause_key(line_id)
            line = causes.get(ck)
            if line is None:
                line = causes[ck] = {
                    "first_ts": ts, "n_total": 0, "rate_ema": None, "gap_ema": None,
                    "last_instant_rate_hr": None, "novelty_pending": True, "novelty_fired": False,
                    "spike_armed": True, "drought_armed": True, "recent_ts": [], "places": {},
                    "event_id": None, "event_ts": None}
            # one event = place events of this cause inside EVENT_WINDOW_S of the event's start
            ev_ts = line.get("event_ts")
            if line.get("event_id") is None or ev_ts is None or ts - ev_ts > EVENT_WINDOW_S or ts < ev_ts:
                line["event_id"] = f"{ck}#{int(ts)}"
                line["event_ts"] = ts
                # a new event on the cause line = one more occurrence of the cause (union of places)
                _bump(tm, line, ts, n)
            line["places"][line_id] = {"last_ts": ts, "event_id": line["event_id"]}
            _save()
    except Exception:
        pass


def _bump(tm, line: dict, ts: float, n: float) -> None:
    """Same EMA update as transport_manager.observe(), applied to the cause line."""
    last_ts = line.get("last_ts")
    if last_ts is not None and ts > last_ts:
        gap_hours = (ts - last_ts) / 3600.0
        if gap_hours > 0:
            inst = 1.0 / gap_hours
            alpha = min(1.0, max(0.0, 1.0 - math.exp(-tm._LAMBDA * gap_hours)))
            line["rate_ema"] = inst if line.get("rate_ema") is None else line["rate_ema"] + alpha * (inst - line["rate_ema"])
            line["gap_ema"] = gap_hours if line.get("gap_ema") is None else line["gap_ema"] + alpha * (gap_hours - line["gap_ema"])
            line["last_instant_rate_hr"] = inst
    recent = line.setdefault("recent_ts", [])
    recent.append(ts)
    if len(recent) > tm._RECENT_TS_CAP:
        del recent[: len(recent) - tm._RECENT_TS_CAP]
    line["n_total"] = int(line.get("n_total", 0)) + (n if n >= 1 else 1)
    line["last_ts"] = ts
    line["drought_armed"] = True


def evaluate_cause(line: dict, now: float) -> list:
    """Candidates [(kind, weight)] for one cause line right now (mirrors transport_manager.evaluate();
    spike re-arm applied in place on the shadow's own state only)."""
    tm = _tm()
    out = []
    if line.get("novelty_pending") and not line.get("novelty_fired"):
        out.append(("novelty", 1.0))
    if tm._cold_start(line, now):
        return out
    rate_ema, gap_ema = line.get("rate_ema"), line.get("gap_ema")
    if rate_ema and rate_ema > 0:
        window_hours = max((gap_ema or 0.0) * tm.WINDOW_GAP_MULTIPLE, tm.MIN_WINDOW_HOURS)
        start = now - window_hours * 3600.0
        wn = sum(1 for t in (line.get("recent_ts") or []) if t >= start)
        ratio = (wn / window_hours) / rate_ema
        if ratio < tm.SPIKE_TRIGGER_RATIO and not line.get("spike_armed", True):
            line["spike_armed"] = True
        if ratio >= tm.SPIKE_TRIGGER_RATIO and line.get("spike_armed", True):
            out.append(("spike", ratio - 1.0))
    last_ts = line.get("last_ts")
    if gap_ema and last_ts and gap_ema > 0:
        ratio = ((now - last_ts) / 3600.0) / gap_ema
        if ratio >= tm.DROUGHT_TRIGGER_RATIO and line.get("drought_armed", True):
            out.append(("drought", ratio - 1.0))
    return out


def _fires(kind: str, weight: float, threshold: float) -> bool:
    return kind == "novelty" or weight >= threshold


def _write(rows: list) -> None:
    path = profile.guard_path(_LOG)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    except Exception:
        pass


def tick(place_candidates: list, threshold: float, now: Optional[float] = None) -> None:
    """Called once per dispatch_tick() with that tick's per-place Candidates (read-only use). Logs one
    'tick' summary row plus one 'cause' row per cause that has any candidate under either scoring.
    Cause lines that would fire are disarmed/consumed in the SHADOW state only. Fail-open."""
    if not TRANSPORT_CAUSE_SHADOW:
        return
    try:
        now = time.time() if now is None else now
        with _LOCK:
            causes = _get_state()["causes"]
            by_cause: dict = {}
            for c in place_candidates or []:
                by_cause.setdefault(cause_key(c.line_id), []).append(c)
            cause_cands: dict = {}
            for ck, line in causes.items():
                cc = evaluate_cause(line, now)
                if cc:
                    cause_cands[ck] = cc
            rows = []
            n_cause_fired = n_place_fired = 0
            for ck in set(by_cause) | set(cause_cands):
                line = causes.get(ck) or {}
                cc = cause_cands.get(ck, [])
                best = max(cc, key=lambda x: x[1], default=None)
                cause_fire = any(_fires(k, w, threshold) for k, w in cc)
                places = []
                place_fire = False
                for c in by_cause.get(ck, []):
                    pf = _fires(c.kind, c.weight, threshold)
                    place_fire = place_fire or pf
                    pl = (line.get("places") or {}).get(c.line_id) or {}
                    places.append({"line_id": c.line_id, "kind": c.kind, "place_would_fire": pf,
                                   "weight": round(c.weight, 3), "last_event_id": pl.get("event_id")})
                n_cause_fired += 1 if cause_fire else 0
                n_place_fired += sum(1 for p in places if p["place_would_fire"])
                if cause_fire and best is not None:
                    for k, w in cc:   # shadow consume/disarm so a cause fires once per edge, like per-place
                        if _fires(k, w, threshold):
                            if k == "novelty":
                                line["novelty_pending"], line["novelty_fired"] = False, True
                            else:
                                line[f"{k}_armed"] = False
                rows.append({"type": "cause", "ts": round(now, 1), "cause_id": ck,
                             "cause_would_fire": cause_fire,
                             "cause_kind": best[0] if best else None,
                             "cause_weight": round(best[1], 3) if best else 0.0,
                             "n_places": len((line.get("places") or {})),
                             "event_ids": [line.get("event_id")] if line.get("event_id") else [],
                             "places": places})
            rows.append({"type": "tick", "ts": round(now, 1), "n_causes": len(causes),
                         "cause_fired": n_cause_fired, "place_fired": n_place_fired,
                         "cause_any": n_cause_fired > 0, "place_any": n_place_fired > 0})
            _write(rows)
            _save()
    except Exception:
        pass
