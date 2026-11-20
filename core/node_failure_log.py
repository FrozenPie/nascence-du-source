"""
Nascence -- NodeBase failure log (J-2854 / F-3525, additive).

Why this exists: NodeBase.run() catches every Exception and returns False, and the orchestrator discards
the return value for 11 of 12 nodes. So a code bug inside a node's _build_prompt/_write_output reads as
quiet silence, a failed Critic reads as approval, a failed Executive reads as a chosen silence. The only
trace was one `[node] FAILED:` line in nascence.log -- no per-node counter (the June Curiosity float()
bug logged 20 FAILED lines before anyone saw it).

This module appends ONE small row per failed node call to data/node_failures.jsonl and gives
scripts/du_pulse.py a reader (`stats`). It changes nothing about what a failure returns or does.

Row: {ts, node, cause, stage, cycle_id, input_type, hedged, err}
  cause : "transport" | "empty_content" | "parse" | "code_bug"
  stage : "build" | "call" | "write"  (where in NodeBase.run the exception was raised)

Cause classes (stage decides first: an exception raised in _build_prompt/_write_output is our code, never
the model):
  code_bug       stage build/write -- a bug in a node (or a state-shape mismatch)
  empty_content  stage call, the model answered with nothing ("No JSON object found in response: ''")
  parse          stage call, the model answered but no usable JSON came back
  transport      stage call, every server in the chain was down / timed out / breaker-skipped

Fail-open and fenced like core/training_log.py: the path is resolved through profile.guard_path BEFORE any
I/O; any error (including a NonLiveWriteError refusal in a non-live process) is swallowed -- logging must
never break a thought cycle. Toggle off with NASCENCE_NODE_FAILURE_LOG=0.

Reader: scripts/du_pulse.py -> _G["regression_alarms"]["node_failures"] (stats()).
"""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path

from . import profile

logger = logging.getLogger("nascence.node_failure_log")

_LOG = Path(__file__).parent.parent / "data" / "node_failures.jsonl"
_ENABLED = os.environ.get("NASCENCE_NODE_FAILURE_LOG", "1") != "0"

CAUSES = ("transport", "empty_content", "parse", "code_bug")
_TAIL_BYTES = 2_000_000   # stats() reads at most this much from the end of the file


def classify(exc: BaseException | None, stage: str = "call") -> str:
    """Map a swallowed exception to one of CAUSES. Pure; never raises."""
    try:
        if stage in ("build", "write"):
            return "code_bug"
        low = f"{type(exc).__name__} {exc}".lower()
        if "no json object found in response: ''" in low or 'no json object found in response: ""' in low:
            return "empty_content"
        if ("no json object" in low or "jsondecodeerror" in low or "expecting" in low
                or "extra data" in low or "unterminated" in low):
            return "parse"
        if "all servers exhausted" in low:
            # call_node_json wraps its last_error; a parse/empty last_error was matched above, anything
            # else (timeout, connect refused, breaker-skipped lane -> last_error None) is the transport.
            return "transport"
        if any(k in low for k in ("timeout", "clienterror", "clientconnector", "serverdisconnected",
                                  "connection", "oserror")):
            return "transport"
        return "code_bug"
    except Exception:
        return "code_bug"


def log_failure(node_id: str, exc: BaseException | None, *, stage: str = "call", cycle_id: str = "",
                input_type: str = "", hedged: bool = False) -> None:
    """Append one failure row. Best-effort; swallows all errors."""
    if not _ENABLED:
        return
    try:
        path = profile.guard_path(_LOG)   # fenced before any I/O (D-0179); refusal swallowed below
        path.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "ts": time.time(),
            "node": node_id,
            "cause": classify(exc, stage),
            "stage": stage,
            "cycle_id": cycle_id or "",
            "input_type": input_type or "",
            "hedged": bool(hedged),
            "err": f"{type(exc).__name__}: {exc}"[:300] if exc is not None else "",
        }
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.debug("node failure log write skipped: %s", e)


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


def stats(since_ts: float = 0.0, path: Path | None = None) -> dict:
    """Counts of failed node calls since `since_ts`: total, by node, by cause, and the code-bug subset by node.
    A code_bug row is the alarm (a node raising in OUR code reads as silence); transport/empty/parse are the
    model or the wire. Read-only; returns {"total": 0, ...} when the log does not exist yet."""
    p = Path(path) if path is not None else _LOG
    out = {"total": 0, "by_node": {}, "by_cause": {}, "code_bug_by_node": {}, "last_ts": None,
           "code_bug_alarm": False}
    try:
        if not p.exists():
            return out
        for r in _read_rows(p):
            if float(r.get("ts") or 0) < since_ts:
                continue
            n, c = str(r.get("node") or "?"), str(r.get("cause") or "?")
            out["total"] += 1
            out["by_node"][n] = out["by_node"].get(n, 0) + 1
            out["by_cause"][c] = out["by_cause"].get(c, 0) + 1
            if c == "code_bug":
                out["code_bug_by_node"][n] = out["code_bug_by_node"].get(n, 0) + 1
            out["last_ts"] = max(out["last_ts"] or 0, float(r.get("ts") or 0))
        out["code_bug_alarm"] = bool(out["code_bug_by_node"])
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"[:120]
    return out
