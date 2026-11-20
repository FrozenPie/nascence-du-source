"""
light_sidecar — shared helpers for Part A of docs/staged/data_store_hygiene.md (D-0154, 2026-09-05).

Two hot readers (ClimateEngine._read_subconscious, frontier.open_count) were parsing 60 MB and 4 MB JSON
files in full every 5 s tick (F-0853/F-0854/F-0857). The owners of those files now ALSO write a light
companion with every non-vector field, and the readers can read that instead. Shadow-first: the read flags
(SUBC_LIGHT_READ in core/climate_engine.py, FRONTIER_LIGHT_READ in core/frontier.py) stay False until
data/light_sidecar_shadow.jsonl shows heavy == light for the values the readers actually consume.

Additive only: the heavy file is still the store of record and is written unchanged in content.
Everything here is fail-open and never raises into a caller.
"""
from __future__ import annotations

import json
import logging
import os
import time
import threading
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.light_sidecar")

_ROOT = Path(__file__).resolve().parent.parent
_DATA = _ROOT / "data"
# J-0875 (F-1235): SHADOW_LOG is resolved at CALL time by _shadow_path() below, never at import -- a
# script that sets `light_sidecar.SHADOW_LOG = <temp path>` (exploratory_ignition_test.py does) is
# honoured as-is, and an unredirected non-live process is refused rather than allowed to append its
# own heavy-vs-light rows to Du's live J-0621 instrument.
SHADOW_LOG = _DATA / "light_sidecar_shadow.jsonl"
SHADOW_EVERY_S = 60.0
VECTOR_MIN_LEN = 16

_last_shadow: dict[str, float] = {}


def is_vector(v) -> bool:
    """A long numeric list — an embedding/centroid, never something a scalar consumer reads."""
    return (isinstance(v, list) and len(v) > VECTOR_MIN_LEN
            and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v[:8]))


def light_record(rec: dict) -> dict:
    """Every field of `rec` except vectors and private (underscore) working fields."""
    return {k: v for k, v in rec.items() if not is_vector(v) and not str(k).startswith("_")}


def light_records(recs) -> list:
    out = []
    for r in recs or []:
        if isinstance(r, dict):
            out.append(light_record(r))
    return out


def write_atomic(path: Path, obj) -> bool:
    """Compact JSON to path.tmp then os.replace onto path, so a reader never sees a torn file.
    J-4442 (F-5157): through core.store_persist.write_text_durable -- the .tmp is now fsynced before the
    replace (the 2026-11-20 crash zero-filled frontier.light.json / subconscious_state.light.json, written
    without one) and the outgoing file is kept as <name>.prev for load() below. Same bytes, same path."""
    try:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        from core import store_persist as _sp
        _sp.write_text_durable(path, json.dumps(obj, ensure_ascii=False))
        return True
    except Exception:
        return False


def load(path: Path):
    """json.load or None (never raises).
    J-4442 (F-5157): an empty / all-NUL / unparseable light file now logs a WARNING naming it and falls back
    to <name>.prev (restored on disk when this process may write it); with no usable .prev it returns None as
    before, and the caller falls back to the heavy file exactly as before."""
    try:
        from core import store_persist as _sp
        return _sp.read_json_durable(Path(path), "light_sidecar", logger, guard=profile.guard_path)
    except Exception:
        return None


def shadow_due(reader: str, every_s: float = SHADOW_EVERY_S) -> bool:
    """Rate limiter for the once-a-minute heavy-vs-light comparison, per reader."""
    now = time.time()
    if now - _last_shadow.get(reader, 0.0) < every_s:
        return False
    _last_shadow[reader] = now
    return True


def _shadow_path() -> Path | None:
    """Where this process may append its shadow rows, resolved at call time -- or None if nowhere.

    J-0875 (F-1235, world_store_write_fence): data/light_sidecar_shadow.jsonl is the INSTRUMENT the
    founder-ruled D-0154 flip (J-0621) was read from. Any non-Du process that called a shadow-comparing
    reader (frontier.open_count / ClimateEngine._read_subconscious with its read flag False) used to
    append its own temp-heavy-vs-live-light comparison here -- shadow_due() is always True on a fresh
    process's first call -- which produced the foreign heavy 0/10/1 rows of 2026-09-05/06 that F-1213
    first read as a live heavy-file rewrite.

    Same gate as the world-store fence, different failure mode: profile.guard_path() decides (live
    process -> the real path; SHADOW_LOG explicitly redirected outside data/ -> that path, as-is;
    lab_env.isolate()'s data/_lab/<dir>/ sandbox -> allowed, D-0200), but a refusal here DROPS the row
    (with guard_path's own one-per-path warning) instead of raising D-0179's NonLiveWriteError. This is
    a diagnostic row on a READ path, not a world store: a read-only caller of open_count() must never
    be refused its count because a side-instrument wanted to write, and the callers' own fail-open
    try/except would swallow the raise anyway -- so the raise would buy nothing and could only break a
    reader. D-0179's false-negative concern does not apply: no script asserts on its own shadow rows
    (a script that wants them redirects SHADOW_LOG explicitly). Recorded as a named design choice in
    docs/staged/world_store_write_fence.md (J-0875), not a silent one.
    """
    try:
        return profile.guard_path(SHADOW_LOG)
    except profile.NonLiveWriteError:
        return None
    except Exception:
        return None


# J-1926 / F-2550: shadow_log is reached from the loop thread (climate engine, pursuits.status) and from the coupling-ledgers daemon thread (frontier.open_count); serialise the append.
_APPEND_LOCK = threading.Lock()


def shadow_log(reader: str, heavy_value, light_value, heavy_ms: float | None = None,
               light_ms: float | None = None, **extra) -> None:
    """One row per comparison. The J-0621 read checks heavy_value == light_value on every row.
    Non-live processes write nothing unless SHADOW_LOG was explicitly redirected (see _shadow_path)."""
    path = _shadow_path()
    if path is None:
        return
    try:
        row = {"ts": round(time.time(), 1), "reader": reader,
               "heavy_value": heavy_value, "light_value": light_value,
               "agree": (heavy_value == light_value),
               "heavy_ms": None if heavy_ms is None else round(heavy_ms, 1),
               "light_ms": None if light_ms is None else round(light_ms, 1)}
        row.update(extra)
        path.parent.mkdir(parents=True, exist_ok=True)
        with _APPEND_LOCK, open(path, "a", encoding="utf-8") as f:
            print(json.dumps(row, ensure_ascii=False, default=str), file=f)
    except Exception:
        pass
