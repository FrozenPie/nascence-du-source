"""
Nascence -- hedge-agreement shadow log (J-3314 / D-0671 / J-3171 review section 5.3 C1; additive SHADOW instrument).

Why this exists: the Reflection node's own `confidence` field carries almost no signal (397 of 417 logged lines say
'high', AUC 0.517 against first-attempt Critic rejection, n 4,374; D-0671 drops the line from the Executive prompt).
NodeBase.run_best_of already holds TWO hedged drafts at selection time (REFLECTION_HEDGE = 2). How much the two
independent samples AGREE is a candidate replacement signal: two drafts that say the same thing are probably
grounded, two that diverge probably are not. This module measures that and nothing else.

It appends ONE row per reflection hedged run that has at least two valid drafts to
data/reflection_hedge_agreement_shadow.jsonl (true append, one json object per line, the session-events convention):

    {ts, cycle_id, input_type, n_valid, agreement, conf_chosen, conf_other, chosen_len, other_len}

  agreement   cosine of the two drafts' MiniLM embeddings (core.memory.store._embed, normalised vectors, so the
              dot product); null when either embedding is unavailable (the row is still written, honestly null).
  conf_*      the drafts' own stated `confidence` (null when absent / not numeric).
  *_len       draft length in characters.
  The "other" draft is the highest-scoring valid draft that is not the kept one.

NOTHING reaches any prompt, no behaviour changes, no field is added to ReflectionOutput. The hot lane pays nothing:
run_best_of only calls `submit(...)`, which queues the work on ONE background daemon thread and returns at once;
the embedding (CPU, serialised by the embedder lock) and the file write happen on that thread. The queue is bounded
(a backlog is dropped, never grown), every error is swallowed, and the path is resolved through profile.guard_path
BEFORE any I/O like the sibling logs (a NonLiveWriteError refusal in a non-live process is swallowed too).

Flag: core.schema.REFLECTION_HEDGE_AGREEMENT_SHADOW (default True = log). Env NASCENCE_HEDGE_AGREEMENT_LOG=0 also
turns it off.

READER (so this is not write-only): `stats()` / `python -m core.hedge_agreement_log`, surfaced in
scripts/du_pulse.py -> regression_alarms.hedge_agreement. The decision read is a named job: after at least 600
cycles, AUC of LOW agreement for first-attempt Critic rejection (critic.jsonl joined by cycle_id) and for the
provenance grade; promotion bar AUC >= 0.6, stop under 0.55.
"""
from __future__ import annotations

import json
import logging
import os
import queue
import threading
import time
from pathlib import Path

from . import profile

logger = logging.getLogger("nascence.hedge_agreement_log")

_LOG = Path(__file__).parent.parent / "data" / "reflection_hedge_agreement_shadow.jsonl"
_ENV_ON = os.environ.get("NASCENCE_HEDGE_AGREEMENT_LOG", "1") != "0"

TEXT_CAP = 2000          # chars of each draft sent to the embedder
_QUEUE_MAX = 8           # a backlog beyond this is dropped, never grown
_TAIL_BYTES = 2_000_000  # stats() reads at most this much from the end of the file
ENOUGH_ROWS = 600        # the J-3314 read job's minimum

_Q: "queue.Queue" = queue.Queue(maxsize=_QUEUE_MAX)
_worker: "threading.Thread | None" = None
_worker_lock = threading.Lock()


def _enabled() -> bool:
    if not _ENV_ON:
        return False
    try:
        from . import schema
        return bool(getattr(schema, "REFLECTION_HEDGE_AGREEMENT_SHADOW", True))
    except Exception:
        return False


def _draft_text(data: dict) -> str:
    d = data.get("draft") if isinstance(data, dict) else None
    return (str(d) if d is not None else json.dumps(data, ensure_ascii=False, default=str)).strip()


def _conf(data: dict):
    try:
        v = data.get("confidence") if isinstance(data, dict) else None
        return None if v is None or isinstance(v, bool) else round(float(v), 4)
    except Exception:
        return None


def _agreement(a: str, b: str):
    """Cosine of the two texts' normalised MiniLM vectors, or None. Never raises."""
    try:
        from core.memory.store import _embed
        va, vb = _embed(a[:TEXT_CAP]), _embed(b[:TEXT_CAP])
        if va is None or vb is None:
            return None
        return round(float((va * vb).sum()), 4)
    except Exception as e:
        logger.debug("hedge agreement embed skipped: %s", e)
        return None


def _write_row(job: dict) -> None:
    chosen, other = job["chosen"], job["other"]
    ct, ot = _draft_text(chosen), _draft_text(other)
    row = {
        "ts": job["ts"],
        "cycle_id": job["cycle_id"],
        "input_type": job["input_type"],
        "n_valid": job["n_valid"],
        "agreement": _agreement(ct, ot),
        "conf_chosen": _conf(chosen),
        "conf_other": _conf(other),
        "chosen_len": len(ct),
        "other_len": len(ot),
    }
    path = profile.guard_path(_LOG)   # fenced before any I/O (D-0179); a refusal is swallowed by the caller
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _run() -> None:
    while True:
        job = _Q.get()
        try:
            _write_row(job)
        except Exception as e:
            logger.debug("hedge agreement row skipped: %s", e)
        finally:
            _Q.task_done()


def _ensure_worker() -> None:
    global _worker
    with _worker_lock:
        if _worker is None or not _worker.is_alive():
            _worker = threading.Thread(target=_run, name="hedge-agreement-log", daemon=True)
            _worker.start()


def submit(node_id: str, *, results: list, best, scorer, cycle_id: str = "", input_type: str = "") -> None:
    """Called by NodeBase.run_best_of after the pick. Reflection only; needs >= 2 valid drafts. Queues one job on the
    background thread and returns immediately. Best-effort; swallows all errors; changes nothing about the pick."""
    try:
        if node_id != "reflection" or not _enabled():
            return
        valid = [r for r in results if isinstance(r, dict)]
        if len(valid) < 2 or best is None:
            return
        others = [r for r in valid if r is not best]
        if not others:
            return
        try:
            other = max(others, key=scorer)
        except Exception:
            other = others[0]
        job = {"ts": time.time(), "cycle_id": cycle_id or "", "input_type": input_type or "",
               "n_valid": len(valid), "chosen": best, "other": other}
        _ensure_worker()
        _Q.put_nowait(job)
    except queue.Full:
        logger.debug("hedge agreement queue full; row dropped")
    except Exception as e:
        logger.debug("hedge agreement submit skipped: %s", e)


def drain(timeout: float = 30.0) -> bool:
    """Block until the queue is empty (tests / shutdown). True if drained within `timeout`."""
    end = time.time() + timeout
    while time.time() < end:
        if _Q.unfinished_tasks == 0:
            return True
        time.sleep(0.02)
    return _Q.unfinished_tasks == 0


def _read_rows(path: Path) -> list[dict]:
    size = path.stat().st_size
    with open(path, "rb") as f:
        if size > _TAIL_BYTES:
            f.seek(size - _TAIL_BYTES)
            f.readline()   # drop the partial first line
        raw = f.read().decode("utf-8", errors="replace")
    rows = []
    for ln in raw.splitlines():
        try:
            r = json.loads(ln)
            if isinstance(r, dict):
                rows.append(r)
        except Exception:
            continue
    return rows


def _q(sorted_vals: list, p: float):
    return round(sorted_vals[min(len(sorted_vals) - 1, int(p * len(sorted_vals)))], 4)


def stats(since_ts: float = 0.0, path: Path | None = None) -> dict:
    """Read the shadow log: rows, rows with a real agreement, agreement median / p10 / p90, share of rows whose two
    drafts stated the same confidence, last ts. `enough` is True from ENOUGH_ROWS rows (the J-3314 read job's bar).
    Read-only; {"rows": 0, ...} when the log does not exist yet."""
    p = Path(path) if path is not None else _LOG
    out = {"rows": 0, "rows_with_agreement": 0, "agreement_median": None, "agreement_p10": None,
           "agreement_p90": None, "same_confidence_share": None, "last_ts": None, "enough": False}
    try:
        if not p.exists():
            return out
        ag, same, both = [], 0, 0
        for r in _read_rows(p):
            if float(r.get("ts") or 0) < since_ts:
                continue
            out["rows"] += 1
            out["last_ts"] = max(out["last_ts"] or 0, float(r.get("ts") or 0))
            a = r.get("agreement")
            if isinstance(a, (int, float)):
                ag.append(float(a))
            cc, co = r.get("conf_chosen"), r.get("conf_other")
            if cc is not None and co is not None:
                both += 1
                same += 1 if cc == co else 0
        out["rows_with_agreement"] = len(ag)
        if ag:
            ag.sort()
            out["agreement_median"], out["agreement_p10"], out["agreement_p90"] = _q(ag, .5), _q(ag, .1), _q(ag, .9)
        if both:
            out["same_confidence_share"] = round(same / both, 3)
        out["enough"] = out["rows"] >= ENOUGH_ROWS
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"[:120]
    return out


if __name__ == "__main__":
    print(json.dumps(stats(), indent=2))
