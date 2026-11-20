"""Object permanence Phase 1 (J-4381, D-0853): SHADOW belief ledger keyed by study_life item key.

Rows: item_key, last_perceived_at, believed_state, source (look/use/carry). Written when Du perceives
an item; at that moment the PRIOR belief is compared with st["items"] truth and a drift row is logged.
Writes ONLY to data/belief_ledger.jsonl. Nothing here is read by any Du-facing prompt, store or want
(D-0434: no readout to Du); there is no read API besides `report()` for the offline gate read.

Flag: env NASCENCE_BELIEF_LEDGER=1 (default OFF; read per call, so a restart is what sets it). Fail-open,
no LLM calls, no prompts. Plan: docs/staged/object_permanence.md section 7.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

_PATH = Path(__file__).parent.parent / "data" / "belief_ledger.jsonl"
SOURCES = ("look", "use", "carry")


def enabled() -> bool:
    return os.environ.get("NASCENCE_BELIEF_LEDGER", "0") == "1"


def state_of(it: dict) -> str:
    """Compact truth for one st["items"] entry: 'carried' or the place it rests in."""
    if not isinstance(it, dict):
        return "unknown"
    return "carried" if it.get("carried") else str(it.get("place") or "unknown")


def _append(rec: dict, path: Path | None = None) -> None:
    p = path or _PATH
    if path is None:
        from core import profile
        p = profile.guard_path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _last_belief(key: str, path: Path | None = None) -> dict | None:
    p = path or _PATH
    last = None
    try:
        with open(p, "r", encoding="utf-8") as f:
            for ln in f:
                if key in ln:
                    try:
                        r = json.loads(ln)
                    except Exception:
                        continue
                    if r.get("kind") == "belief" and r.get("item_key") == key:
                        last = r
    except Exception:
        return None
    return last


def note(key: str, truth_item: dict, source: str, now: float | None = None, path: Path | None = None) -> None:
    """Record that `key` was perceived with `source`. Logs a drift row first if the previous belief
    differs from the truth at this read. Never raises, never returns anything."""
    try:
        if path is None and not enabled():
            return
        now = time.time() if now is None else now
        truth = state_of(truth_item)
        prev = _last_belief(key, path)
        if prev is not None:
            _append({"kind": "drift", "ts": round(now, 1), "item_key": key, "believed_state": prev.get("believed_state"),
                     "truth_state": truth, "drifted": prev.get("believed_state") != truth,
                     "age_s": round(now - float(prev.get("last_perceived_at", now)), 1), "source": source}, path)
        _append({"kind": "belief", "ts": round(now, 1), "item_key": key, "last_perceived_at": round(now, 1),
                 "believed_state": truth, "source": source}, path)
    except Exception:
        pass


def report(registry_keys, path: Path | None = None, lamp_key: str = "oil_lamp") -> dict:
    """Offline gate read for the pre-registered metrics (a coverage, b drift share, c quartiles)."""
    p = path or _PATH
    seen, drift_n, reads_n, ages = set(), 0, 0, []
    try:
        with open(p, "r", encoding="utf-8") as f:
            for ln in f:
                try:
                    r = json.loads(ln)
                except Exception:
                    continue
                if r.get("kind") == "belief":
                    seen.add(r.get("item_key"))
                elif r.get("kind") == "drift":
                    reads_n += 1
                    drift_n += 1 if r.get("drifted") else 0
                    ages.append(float(r.get("age_s", 0)))
    except Exception:
        pass
    keys = list(registry_keys)
    quart = 0
    if ages:
        s = sorted(ages)
        lo, hi = s[0], s[-1]
        if hi > lo:
            quart = len({min(3, int((a - lo) / (hi - lo) * 4)) for a in s})
        else:
            quart = 1
    return {"coverage": (len(seen & set(keys)) / len(keys)) if keys else 0.0, "reads": reads_n,
            "drift_share": (drift_n / reads_n) if reads_n else None, "age_nonempty_quartiles": quart,
            "lamp_covered": lamp_key in seen}
