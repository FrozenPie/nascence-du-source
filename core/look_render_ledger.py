"""
core/look_render_ledger.py -- the LOOK-TARGET RENDER LEDGER: an exact, observe-only count of which pool line a look drew
=======================================================================================================================
2026-10-07 (J-1899, D-0360 (c) RULED option 3 "measure first"; F-2505 section 5; the J-1694 scene_extra_ledger shape).

WHY. F-2505 (J-1732) found daylight-bound and diurnal-bird lines that can render at night in the look-target pools
(world_detail.detail() = a look at a NEW target; world_detail.extra_pool() = extra lines merged into an EXISTING target's
own pool), and computed per-look odds, but could not say how often Du actually LOOKS at those targets at night:
nothing recorded which look-pool line was rendered (F-2505 section 5; nascence.log carries only legacy "he LOOKS" rows).
D-0360 (c) therefore ruled: build this ledger, run it, THEN decide whether the garden / shore / wood bird targets need
night-capable content. The scene channel already has its own ledger (core/scene_extra_ledger.py); this is the look channel.

WHAT. ONE ROW per look that actually RENDERED a pool line, appended from inside the producing call:
    {"ts": 1791400000.1,        # time of the render (epoch s to 0.1 s: the scene_extra_ledger convention)
     "src": "detail",           # "detail" (a look at a new target) | "extra_pool" (an extra line that was the line drawn)
     "loc": "garden",           # the place whose target was matched (the content module's LOCATION)
     "target": "garden:birds",  # the registry key: <place>:<target>
     "key": "any",              # the POOL KEY the line came from ("rare" for the rare tail), "" if it cannot be resolved
     "phase": "night",          # the phase argument as the caller passed it (dawn / day / dusk / night)
     "conds": ["any", "night"], # every condition key the engine emitted for this look, sorted
     "pool": 22,                # lines in the merged pool at the draw (detail: after the rare roll; extra_pool: the extras)
     "line_id": "3fa91c0d2e",   # sha1(line)[:10]: a STABLE id, so a reader can join rows to a pool line forever
     "line": "..."}             # the first 48 characters (a prefix is enough to recognise it; the id is the exact key)
detail() writes one row per non-empty return. extra_pool() only OFFERS lines (the sensorium draws among them with its
own base pool), so its row is written by sensorium's own pick -- world_detail.note_extra_pick() -- and ONLY when the line
that was drawn is one of the extras: an extra that was offered and not drawn is not a render and leaves no row.

RULES (the briefing's; each is pinned by scripts/_test_j1899_look_render_ledger.py).
  * Observe-only: never changes the returned line and takes no random draw -- every random.random() / random.choice keeps
    its exact sequence; this module never touches `random`.
  * Fail-open: record() swallows everything, including the D-0179 write fence's NonLiveWriteError, and every caller wraps
    the call as well. No ledger problem can raise into a look or change one.
  * World-store write fence (J-0610 / D-0179), the way core/scene_extra_ledger.py does it: the path goes through
    profile.guard_path(), so only the one real live Du boot (profile.mark_live()), a lab_env.isolate() sandbox or a path
    redirected outside data/ can write; a test, a diagnostic, an importer or a NAMED-PROFILE process (activate_profile()
    never rebases world stores -- J-1883) gets False and no file.
  * Capped by rotation (the store-hygiene rule: an append-only instrument must not grow without bound): when the file
    passes ROTATE_BYTES it is renamed over <name>.1 (one generation kept) and a fresh file starts, so the on-disk
    history is between ROTATE_BYTES and 2 x ROTATE_BYTES, i.e. weeks at the expected few-hundred-rows-a-day rate.
    read_rows() reads the rotated generation first, so a read-back spans the rotation.
  * Restart-gated: Du loads this at his next start; nothing here is imported until the first rendered look.

Read side: read_rows() and status() (both read-only, tolerate a torn last line and a missing file, never raise), and
night_looks() -- the exact count D-0360 (c)'s defeater asks for: night rows per target, for the garden / shore / wood bird
targets (defeater: fewer than 5 such looks in total after >= 14 nights = exposure too small to justify a content change).
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.look_render_ledger")

_DATA = Path(__file__).parent.parent / "data"
_LEDGER = _DATA / "look_render_ledger.jsonl"

ROTATE_BYTES = 4_000_000          # ~16k rows at ~250 B; one rotated generation (.1) is kept
LINE_PREFIX = 48                  # characters of the line stored beside its id
BIRD_TARGETS = ("garden:birds", "shore:birds", "wood:birds")      # D-0360 (c)'s three targets


def line_id(line: str) -> str:
    """Stable id of a pool line (sha1 prefix); the join key between a ledger row and the content modules."""
    return hashlib.sha1((line or "").encode("utf-8")).hexdigest()[:10]


def _rotate_if_needed(path: Path) -> None:
    try:
        if path.exists() and path.stat().st_size >= ROTATE_BYTES:
            os.replace(path, path.with_name(path.name + ".1"))
    except Exception as exc:                 # a failed rotation just lets the file grow one more append
        logger.debug("[look_render_ledger] rotation skipped (non-fatal): %s", exc)


def record(src: str, loc: str, target: str, key: str, phase: str, conds, line: str, pool: int) -> bool:
    """Append one render row. True iff a row was written; False -- never an exception -- otherwise."""
    try:
        # D-0179: the real data/ only for the live Du boot; a non-live process is refused here, before any I/O.
        path = profile.guard_path(_LEDGER)
        row = {"ts": round(time.time(), 1), "src": src, "loc": loc or "", "target": target or "", "key": key or "",
               "phase": phase or "", "conds": sorted(conds), "pool": int(pool),
               "line_id": line_id(line), "line": (line or "")[:LINE_PREFIX]}
        path.parent.mkdir(parents=True, exist_ok=True)
        _rotate_if_needed(path)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return True
    except Exception as exc:     # incl. profile.NonLiveWriteError: a non-live process records nothing, quietly
        logger.debug("[look_render_ledger] row not written (non-fatal): %s", exc)
        return False


def _ts(row: dict) -> float:
    try:
        return float(row.get("ts") or 0.0)
    except Exception:
        return 0.0


def _read_one(p: Path, since_ts: float) -> list:
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


def read_rows(since_ts: float = 0.0, path=None) -> list:
    """Every parsable row with ts >= since_ts, oldest first, the rotated generation (<name>.1) before the live file.
    A torn or garbled line is skipped, a missing ledger is []. `path` defaults to the live ledger (read-only)."""
    p = Path(path) if path is not None else _LEDGER
    return _read_one(p.with_name(p.name + ".1"), since_ts) + _read_one(p, since_ts)


def status(path=None) -> dict:
    """{path, ledger_rows, first_ts, last_ts, by_src, by_target} -- rows per producer and per registry target."""
    p = Path(path) if path is not None else _LEDGER
    rows = read_rows(0.0, p)
    by_src: dict = {}
    by_target: dict = {}
    for r in rows:
        by_src[str(r.get("src", ""))] = by_src.get(str(r.get("src", "")), 0) + 1
        by_target[str(r.get("target", ""))] = by_target.get(str(r.get("target", "")), 0) + 1
    tss = [_ts(r) for r in rows]
    return {"path": str(p), "ledger_rows": len(rows), "first_ts": min(tss) if tss else None,
            "last_ts": max(tss) if tss else None, "by_src": by_src, "by_target": by_target}


def night_looks(path=None, since_ts: float = 0.0, targets=BIRD_TARGETS) -> dict:
    """{target: night rows}, plus "total" over `targets` and "nights" (distinct local dates with any row): the exact
    figure D-0360 (c)'s defeater reads. A row is a night look when its phase is "night"."""
    rows = read_rows(since_ts, path)
    out = {t: 0 for t in targets}
    for r in rows:
        if r.get("phase") == "night" and r.get("target") in out:
            out[r["target"]] += 1
    out["total"] = sum(out[t] for t in targets)
    out["nights"] = len({time.strftime("%Y-%m-%d", time.localtime(_ts(r))) for r in rows if _ts(r)})
    return out
