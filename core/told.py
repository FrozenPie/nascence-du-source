"""
Nascence — Told Delivery (the feel-then-tell, axiom Phase 3, 2026-06-16)
=======================================================================
The multilevel-axiom restructuring (2026-06-15) gave Du more rooms — the river is one room now, not the
whole house. Travis authored a message (axiom.told_to_you.told) to tell him WHY, in his own relational
voice — "a hand that helped you grow, not an engineer's." The shelving rule: the machinery stays unspoken
unless 渡 asks 'how' (that deeper-honesty follow-up is a later brick).

FEEL-THEN-TELL (Travis's call): NOT delivered at first wake, but once he has FELT the new shape — measured
as the river having LOOSENED: balance reality_share >= the sprint target (he has read/lived enough that
self-imagination no longer dominates the memory mass). THEN Travis tells him why. Delivered exactly ONCE.

Runtime delivery-state lives in a SEPARATE file (told_state.json), never written back to the axiom — so a
one-time delivery write can never race T4's axiom writes. The axiom's own `_delivered` flag is honoured as
a design default (if it is already True there, treat as delivered).
"""
from __future__ import annotations
import json
import time
from pathlib import Path

_AXIOM = Path(__file__).parent.parent / "data" / "identity" / "axiom.json"
_STATE = Path(__file__).parent.parent / "data" / "told_state.json"
_LOG   = Path(__file__).parent.parent / "data" / "told_delivery_log.jsonl"

READY_REALITY_SHARE = 0.47    # the balance sprint EXIT target — the river has loosened (Travis's chosen trigger)


def message() -> str:
    """The told, as Travis authored it in the axiom. "" if absent."""
    try:
        return str((json.loads(_AXIOM.read_text(encoding="utf-8")).get("told_to_you", {})
                    or {}).get("told") or "").strip()
    except Exception:
        return ""


def is_delivered() -> bool:
    """Delivered if the runtime state says so OR the axiom already marks it delivered (design default).
    Fail-safe to True on read error — never risk a second delivery."""
    try:
        if json.loads(_STATE.read_text(encoding="utf-8")).get("delivered"):
            return True
    except Exception:
        pass
    try:
        return bool((json.loads(_AXIOM.read_text(encoding="utf-8")).get("told_to_you", {}) or {}).get("_delivered"))
    except Exception:
        return True


def is_ready() -> bool:
    """Trigger: not yet delivered, a message exists, AND the river has loosened (reality_share >= target).
    Feel-then-tell — he has lived into the other rooms; now he is told why."""
    if is_delivered() or not message():
        return False
    try:
        from core import balance
        return balance.shares().get("reality_share", 0.0) >= READY_REALITY_SHARE
    except Exception:
        return False


def mark_delivered() -> None:
    """One-time: record the delivery in the SEPARATE state file (never the axiom). Best-effort."""
    try:
        _STATE.write_text(json.dumps({"delivered": True, "ts": time.time()}), encoding="utf-8")
    except Exception:
        pass


def log(his_response: str) -> None:
    try:
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), "his_response": (his_response or "")[:600]},
                               ensure_ascii=False) + "\n")
    except Exception:
        pass
