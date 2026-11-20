"""
core/scene_extra_ledger.py -- the SCENE-extra RENDER LEDGER: an exact, observe-only count of ambient lines
==========================================================================================================
2026-10-03 (J-1694, F-2293; cat_overhaul chain, link 2 of 2 after J-1693's wood-mapping fix).

WHY. world_detail.scene_extra() hands sensorium.scene_line() an occasional ambient line that NAMES a lookable
object (SCENE_P = 0.25 of scene builds; the record player's four study lines J-0997 added are among them).
J-1014's four read-backs (F-1466, F-1624, F-1741, F-2293) could not count how often Du was actually shown such a
line, because nothing recorded the draw. The substitutes are lossy: data/spatial_shadow.jsonl cuts the scene text
to 220 characters (the study's base scene alone is longer, so no study-place extra is ever visible there) and
data/training/voice.jsonl is only a sample. This ledger is the exact count.

WHAT. ONE ROW per world_detail.scene_extra() call that returned a non-empty line, appended from inside that call
(none for an empty draw -- about 75% of scene builds -- so a few hundred rows a day):
    {"ts": 1790968367.9,         # time of the draw (epoch s to 0.1 s: the spatial_shadow / cat ledger convention)
     "loc": "study",             # the `location` argument: which SCENE pool was asked
     "place": "study",           # where the caller says Du IS (sensorium state["location"]); "" if not passed
     "conds": ["any", "night"],  # the pool's condition keys that matched this draw, sorted (the sub-pools merged)
     "line": "...",              # the line returned
     "pool": 16}                 # lines in the merged pool at the draw (each had a 1/pool chance, given a draw)
`loc` and `place` differ only where a caller folds one place onto another's pool -- exactly the F-2290 fault J-1693
fixed (the wood asked the study's pool) -- so recording both keeps that class of fault visible in the data itself.
One row is one scene BUILD that drew an extra, not necessarily one idle tick: scene_line() has several callers
(inner_monologue_node, voice_node, executive_node, nature_study, sensorium.look), so a read-back that wants idle
ticks only joins on ts against data/spatial_shadow.jsonl (its row is written right after the scene is built).

RULES (the briefing's; each is pinned by scripts/_test_j1694_scene_extra_ledger.py).
  * Observe-only: never changes the returned line and takes no random draw -- the SCENE_P roll and the
    random.choice keep their exact sequence; this module never touches `random`.
  * Fail-open: record() swallows everything, including the D-0179 write fence's NonLiveWriteError, and
    scene_extra() wraps the call as well. No ledger problem can raise into scene_line() or change a scene.
  * World-store write fence (J-0610 / D-0179), the way core/cat_sounds.py's ledger writer does it: the path goes
    through profile.guard_path(), so only the one real live Du boot (profile.mark_live()), a lab_env.isolate()
    sandbox or a path redirected outside data/ can write. Any other process (a test, a diagnostic, an importer)
    gets False and no file. Unlike the state writers the refusal is NOT re-raised: an instrument must not take
    the scene down, and scene_line() would swallow it in the extra's own except anyway.
  * Restart-gated: Du loads this at his next start; nothing here is imported until the first non-empty draw.

Read side: read_rows() (every parsable row, optionally since a ts) and status() (row count, first/last ts, rows per
pool). Both are read-only, tolerate a torn last line and a missing file, and never raise.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.scene_extra_ledger")

_DATA = Path(__file__).parent.parent / "data"
_LEDGER = _DATA / "scene_extra_ledger.jsonl"


def record(location: str, place: str, conds, line: str, pool: int) -> bool:
    """Append one render row. True iff a row was written; False -- never an exception -- otherwise."""
    try:
        # D-0179: the real data/ only for the live Du boot; a non-live process is refused here, before any I/O.
        path = profile.guard_path(_LEDGER)
        row = {"ts": round(time.time(), 1), "loc": location, "place": place or "",
               "conds": sorted(conds), "line": line, "pool": int(pool)}
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return True
    except Exception as exc:     # incl. profile.NonLiveWriteError: a non-live process records nothing, quietly
        logger.debug("[scene_extra_ledger] row not written (non-fatal): %s", exc)
        return False


def _ts(row: dict) -> float:
    try:
        return float(row.get("ts") or 0.0)
    except Exception:
        return 0.0


def read_rows(since_ts: float = 0.0, path=None) -> list:
    """Every parsable ledger row with ts >= since_ts, oldest first. A torn or garbled line (a crash mid-append) is
    skipped, a missing ledger is []. `path` defaults to the live ledger (read-only: pass a lab copy to read another)."""
    p = Path(path) if path is not None else _LEDGER
    out: list = []
    try:
        with open(p, encoding="utf-8") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    row = json.loads(raw)
                except Exception:
                    continue
                if isinstance(row, dict) and _ts(row) >= since_ts:
                    out.append(row)
    except Exception:
        pass
    return out


def status(path=None) -> dict:
    """{path, ledger_rows, first_ts, last_ts, by_loc} -- by_loc counts rows per pool asked (study/garden/shore/wood)."""
    p = Path(path) if path is not None else _LEDGER
    rows = read_rows(0.0, p)
    by_loc: dict = {}
    for r in rows:
        k = str(r.get("loc", ""))
        by_loc[k] = by_loc.get(k, 0) + 1
    tss = [_ts(r) for r in rows]
    return {"path": str(p), "ledger_rows": len(rows), "first_ts": min(tss) if tss else None,
            "last_ts": max(tss) if tss else None, "by_loc": by_loc}
