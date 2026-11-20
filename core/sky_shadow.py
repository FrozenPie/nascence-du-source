"""Real-site sun and moon, SHADOW LOG (J-3292 sun; J-3293 adds the "moon" key, D-0655; docs/reviews/sumner_sky_tide_weather_design_J-3264.md section 2).

At each geometry-census moment, compute the OLD sun (world_clock.sun_legacy / daylight_legacy: the month table)
and the REAL-SITE sun (world_clock.sun_sumner / daylight_sumner) for the same instant and append one row to
data/sky_shadow.jsonl. This is the 7-day evidence the design's stop condition asks for BEFORE the founder is
asked to flip world_place.SKY_MODE to "live".

READER (the write-only law: a log nobody reads is not built): scripts/sky_shadow_read.py -- coverage, day-by-day
rise/set shift, daylight-word disagreement and the largest dusk/dawn shift, plus the "7 days seen?" gate. Run by
the founder or the job that closes J-3292; nothing else reads this file and nothing here acts on it.

Hard guarantees:
  * Writes ONLY data/sky_shadow.jsonl. No prompt line, no census field, no fragment field, no schema change.
  * Rows are numbers and phase words only: no place name, no coordinates (world_place.py's privacy rule).
  * Fail-open: record() never raises into geometry_census.snapshot() (a fence refusal is swallowed too).
  * Kill-switch: SKY_SHADOW = False -> record() is a no-op. Rate-limited to one row per _MIN_GAP_S.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path

from core import profile

logger = logging.getLogger(__name__)

SKY_SHADOW = True                                  # kill-switch: False -> record() does nothing

_DATA = Path(__file__).parent.parent / "data"
_LOG = _DATA / "sky_shadow.jsonl"                  # tests must temp-path this, never touch the live file
_MIN_GAP_S = 60.0                                  # census ticks can be seconds apart; the sun moves slowly
_MAX_LOG_BYTES = 50 * 1024 * 1024                  # runaway guard
_lock = threading.Lock()
_last_ts = 0.0


def row_for(t: float, source: str = "?") -> dict:
    """The comparison row for instant `t`: old sun vs real-site sun, both always computed (whatever SKY_MODE is)."""
    from core import world_clock as wc, world_place as wp
    old, new = wc.sun_legacy(t), wc.sun_sumner(t)
    old_rs = wc._SUN.get(time.localtime(t).tm_mon, (7.0, 18.0))
    new_rs = wc.sun_times_sumner(t)
    tz = wc.tz_check(t)

    def pick(d, *keys):
        return {k: d.get(k) for k in keys}
    # J-3293 (Phase 1b): the legacy moon beside the real moon, same instant. Fail-open: a moon error drops the
    # "moon" key, never the sun row.
    moon = None
    try:
        from core import heavens as hv
        mo, mn = hv.moon_legacy(t), hv.moon_true(t)
        mt = hv.moon_times(t)
        moon = {"old": pick(mo, "phase", "illum", "up", "az"),
                "new": {**pick(mn, "phase", "illum", "up", "az", "alt"),
                        "rise_h": None if mt["rise"] is None else round(wp.civil_hour(mt["rise"]), 2),
                        "set_h": None if mt["set"] is None else round(wp.civil_hour(mt["set"]), 2)}}
    except Exception as exc:
        logger.debug("[sky-shadow] moon compare failed (non-fatal): %s", exc)
    row = {
        "ts": round(t, 1), "source": source, "mode": wp.SKY_MODE, "live": bool(wp.sky_live(t)),
        "old": {**pick(old, "up", "phase", "az", "f"), "daylight": wc.daylight_legacy(t),
                "rise_h": round(old_rs[0], 2), "set_h": round(old_rs[1], 2)},
        "new": {**pick(new, "up", "phase", "az", "f", "alt"), "daylight": wc.daylight_sumner(t),
                "rise_h": round(new_rs[0], 2), "set_h": round(new_rs[1], 2)},
        "tz_agree": bool(tz.get("agree")),
    }
    if moon is not None:
        row["moon"] = moon
    return row


def record(source: str = "?", now: float | None = None) -> dict | None:
    """Append one comparison row. Returns the row (for tests) or None on any no-op/failure. Never raises."""
    global _last_ts
    if not SKY_SHADOW:
        return None
    try:
        _log = profile.guard_path(_LOG)             # resolve BEFORE any I/O; refusal swallowed below
    except Exception as exc:                        # NonLiveWriteError or anything else: observe-only, no row
        logger.debug("[sky-shadow] refused by the fence (non-live): %s", exc)
        return None
    try:
        t = time.time() if now is None else float(now)
        with _lock:
            if t - _last_ts < _MIN_GAP_S:
                return None
            _last_ts = t
            if _log.exists() and _log.stat().st_size > _MAX_LOG_BYTES:
                return None
            row = row_for(t, source)
            _log.parent.mkdir(parents=True, exist_ok=True)
            with open(_log, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row
    except Exception as exc:
        logger.debug("[sky-shadow] record failed (non-fatal): %s", exc)
        return None
