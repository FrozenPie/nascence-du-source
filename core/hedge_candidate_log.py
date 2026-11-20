"""
Nascence -- hedged-draft candidate log (J-2805 / F-3445, additive SHADOW instrument).

Why this exists: NodeBase.run_best_of fires N concurrent drafts (Reflection: REFLECTION_HEDGE, temps 0.35 and
0.75 plus the affect bias) and keeps the best by `_score_candidate` (Reflection: longest draft, +1000 when it
ends on terminal punctuation). Only the WINNER ever reached a log (the teacher-example row), so nobody could say
whether the second draft ever wins, how the pair differ, or whether the longest-draft selector chooses well
against a prompt that asks for roughly 60-90 words (F-3445: 16 of 79 kept drafts were over 90 words).

This module appends ONE row per hedged run to data/hedge_candidates.jsonl and gives a reader (`stats`, also
`python -m core.hedge_candidate_log`) that answers the two questions the job set:
  1. how often does the 0.75-temperature (second-index) draft win?
  2. how often is the kept draft over 90 words while a SHORTER valid draft existed?
It changes nothing about which draft is kept and adds nothing to any prompt (the row is written after the pick).

Row: {ts, cycle_id, node, input_type, n, n_valid, kept_index, kept_temp,
      kept_over_90, shorter_valid_exists, candidates: [{index, temp, valid, words, ends_terminal, score, text}]}
  text is capped at TEXT_CAP chars; an invalid (errored) candidate carries valid=false, err, and no text.

Fail-open and fenced like core/node_failure_log.py: the path is resolved through profile.guard_path BEFORE any
I/O; any error (including a NonLiveWriteError refusal in a non-live process) is swallowed -- logging must never
break a thought cycle. Toggle off with NASCENCE_HEDGE_CANDIDATE_LOG=0.

Reader: scripts/du_pulse.py -> _G["regression_alarms"]["hedge_candidates"] (stats(), since the last restart).
"""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path

from . import profile

logger = logging.getLogger("nascence.hedge_candidate_log")

_LOG = Path(__file__).parent.parent / "data" / "hedge_candidates.jsonl"
_ENABLED = os.environ.get("NASCENCE_HEDGE_CANDIDATE_LOG", "1") != "0"

TEXT_CAP = 1500          # chars of draft text kept per candidate
OVER_WORDS = 90          # the Reflection prompt asks for roughly 60-90 words
_TAIL_BYTES = 2_000_000  # stats() reads at most this much from the end of the file
_TERMINALS = '.!?"\''   # == nodes/reflection_node.py _score_candidate's "complete thought" set


def _draft_text(data: dict) -> str:
    """The prose the node produced: the `draft` field when there is one, else the whole dict as text."""
    d = data.get("draft") if isinstance(data, dict) else None
    return str(d) if d is not None else json.dumps(data, ensure_ascii=False, default=str)


def log_hedged(node_id: str, *, temps: list, results: list, best, scorer, cycle_id: str = "",
               input_type: str = "") -> None:
    """Append one row for a hedged run. `results` is the gather() output aligned with `temps`; `best` is the dict
    run_best_of kept (matched by identity). Best-effort; swallows all errors."""
    if not _ENABLED:
        return
    try:
        path = profile.guard_path(_LOG)   # fenced before any I/O (D-0179); refusal swallowed below
        path.parent.mkdir(parents=True, exist_ok=True)
        cands = []
        kept_index = None
        for i, r in enumerate(results):
            t = round(float(temps[i]), 3) if i < len(temps) else None
            if isinstance(r, dict):
                text = _draft_text(r).rstrip()
                try:
                    score = float(scorer(r))
                except Exception:
                    score = None
                cands.append({"index": i, "temp": t, "valid": True, "words": len(text.split()),
                              "ends_terminal": bool(text) and text[-1] in _TERMINALS,
                              "score": score, "text": text[:TEXT_CAP]})
                if r is best:
                    kept_index = i
            else:
                cands.append({"index": i, "temp": t, "valid": False,
                              "err": (f"{type(r).__name__}: {r}"[:200] if isinstance(r, BaseException) else "")})
        kept = next((c for c in cands if c["index"] == kept_index), None)
        kept_words = kept["words"] if kept else 0
        row = {
            "ts": time.time(),
            "cycle_id": cycle_id or "",
            "node": node_id,
            "input_type": input_type or "",
            "n": len(results),
            "n_valid": sum(1 for c in cands if c["valid"]),
            "kept_index": kept_index,
            "kept_temp": kept["temp"] if kept else None,
            "kept_over_90": kept_words > OVER_WORDS,
            "shorter_valid_exists": bool(kept) and any(
                c["valid"] and c["index"] != kept_index and 0 < c["words"] < kept_words for c in cands),
            "candidates": cands,
        }
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.debug("hedge candidate log write skipped: %s", e)


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


def stats(since_ts: float = 0.0, path: Path | None = None, node: str | None = None) -> dict:
    """Read the hedge log: rows, rows with 2+ valid drafts (only those can say who wins), wins by candidate index
    and by temperature, the second-index win rate, how many kept drafts are over 90 words and in how many of
    those a shorter valid draft existed, and kept drafts with no terminal punctuation. Read-only; returns
    {"rows": 0, ...} when the log does not exist yet. `enough` is True from 30 contested rows."""
    p = Path(path) if path is not None else _LOG
    out = {"rows": 0, "contested_rows": 0, "wins_by_index": {}, "wins_by_temp": {}, "second_index_win_rate": None,
           "kept_over_90": 0, "kept_over_90_shorter_valid": 0, "kept_not_terminal": 0, "median_words_kept": None,
           "last_ts": None, "enough": False}
    try:
        if not p.exists():
            return out
        kept_words = []
        for r in _read_rows(p):
            if float(r.get("ts") or 0) < since_ts:
                continue
            if node is not None and r.get("node") != node:
                continue
            out["rows"] += 1
            out["last_ts"] = max(out["last_ts"] or 0, float(r.get("ts") or 0))
            cands = [c for c in (r.get("candidates") or []) if isinstance(c, dict)]
            ki = r.get("kept_index")
            kept = next((c for c in cands if c.get("index") == ki), None)
            if kept is None:
                continue
            kept_words.append(int(kept.get("words") or 0))
            if not kept.get("ends_terminal"):
                out["kept_not_terminal"] += 1
            if r.get("kept_over_90"):
                out["kept_over_90"] += 1
                if r.get("shorter_valid_exists"):
                    out["kept_over_90_shorter_valid"] += 1
            if int(r.get("n_valid") or 0) >= 2:
                out["contested_rows"] += 1
                k = str(ki)
                out["wins_by_index"][k] = out["wins_by_index"].get(k, 0) + 1
                tk = str(kept.get("temp"))
                out["wins_by_temp"][tk] = out["wins_by_temp"].get(tk, 0) + 1
        if out["contested_rows"]:
            out["second_index_win_rate"] = round(out["wins_by_index"].get("1", 0) / out["contested_rows"], 3)
        if kept_words:
            kept_words.sort()
            out["median_words_kept"] = kept_words[len(kept_words) // 2]
        out["enough"] = out["contested_rows"] >= 30
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"[:120]
    return out


if __name__ == "__main__":
    print(json.dumps(stats(), indent=2))
