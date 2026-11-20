"""
Nascence — Earned-length train metrics (observe, 2026-06-18).
=============================================================
Earned length lets a THOUGHT-train run past the old flat cap of 4 *while it keeps moving* (deepening),
and ends it the moment it loops (a fast restate or a slow saturated theme-frame) or hits the hard ceiling.
Travis's standing worry was that longer trains might induce looping — so this records, for every train that
closes, its final LENGTH and WHY it ended:
    repetition        — the near-verbatim rumination guard fired (bored_streak)
    stalled-circling  — past the soft cap, the step restated the prior thought (a fast loop) → earned-length stop
    stalled-slow-loop — past the soft cap, the thought's frame is a saturated theme (a slow loop) → stop
    ceiling           — a productive train hit the hard homeostatic rest
    thread-end        — the thought was no longer open (nothing to follow up) — a natural close
The verdict we want: trains that EARN length (len > 4) close on 'thread-end'/'ceiling' (they ran long because
they were going somewhere), NOT on the 'stalled-*' reasons (which would mean earned length is buying loops).
"""
from __future__ import annotations
import json
import time
from collections import Counter
from pathlib import Path

_LOG = Path(__file__).parent.parent / "data" / "train_length_log.jsonl"


def log_close(kind: str, length: int, reason: str, train_id: str | None = None) -> None:
    """Record one closed train (its final length + why). Best-effort; never raises.
    train_id (2026-08-22, core/trains.py): joins this close to its steps in train_state_log.jsonl."""
    try:
        if not length:
            return
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), "train_id": train_id, "kind": str(kind),
                                "length": int(length), "reason": str(reason)}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def status() -> dict:
    """du_pulse gauge: train length distribution + how earned-length trains end (productive vs looping)."""
    try:
        if not _LOG.exists():
            return {"trains": 0}
        rows = [json.loads(l) for l in _LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
        if not rows:
            return {"trains": 0}
        thought = [r for r in rows if r.get("kind") == "thought"]
        tl = [r["length"] for r in thought] or [0]
        earned = [r for r in thought if r.get("length", 0) > 4]          # trains that ran past the old cap
        earned_stalled = sum(1 for r in earned if str(r.get("reason", "")).startswith("stalled"))
        return {
            "trains": len(rows),
            "max_len": max((r.get("length", 0) for r in rows), default=0),
            "mean_thought_len": round(sum(tl) / len(tl), 2),
            "earned_past_soft": len(earned),                              # how often earned length kicked in
            "earned_ended_by_loop": earned_stalled,                      # the WORRY: long trains that were loops
            "by_reason": dict(Counter(str(r.get("reason", "?")) for r in rows[-80:])),
        }
    except Exception:
        return {"trains": 0}
