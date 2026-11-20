"""
Nascence — internal-cycle human-window gate + shadow (J-2297, D-0445 (a), F-2992 / F-2918).

THE PATH THIS CLOSES (F-2992): the human conversation window (state.conversation_history, the last few
human<->Du exchanges, and state.prior_session_exchanges, the boot-seeded bridge from the previous run)
is only WRITTEN on human cycles (core/orchestrator.py, the human-only append), but it is READ, ungated,
by four prompt builders on every cycle, internal ones included:
    nodes/episodic_buffer_node.py   "Immediate exchange"          (the scene binder; scenes are stored)
    nodes/reflection_node.py        "WHERE WE LEFT OFF", "THIS SESSION"
    nodes/executive_node.py         "WHERE WE LEFT OFF", "THIS SESSION"
    nodes/recall_node.py            "CURRENT EXCHANGE (direct context)"
With zero human turns in a run nothing ever ages those exchanges out, so a stale exchange (10-08 shutdown
pause, 10-16 letters) was bound into 45 of 98 internal scenes for a week (F-2918).

WHAT THIS MODULE DOES
  keep(state, key, block_lines) -> the block to put in the prompt. Human cycles: the block, unchanged,
      always (byte-identical prompts). Internal cycles: the block when INTERNAL_HUMAN_WINDOW_GATE is
      False (today's behaviour), [] when it is True. Either way, on an internal cycle it records how many
      chars that block had (would drop / did drop) for the shadow row below.
  human_window(state) -> (conversation_history, prior_session_exchanges) as a prompt should see them:
      the real lists for human cycles or with the gate off, ([], []) for internal cycles with it on.
  log_shadow(state, output) -> ONE observe-only row per internal/timer cycle that reached voice, appended
      to data/internal_cycle_context_shadow.jsonl. Fail-open; fenced with profile.guard_path (D-0179).

KILL SWITCH: INTERNAL_HUMAN_WINDOW_GATE = False ships as SHADOW (prompts unchanged, rows logged). D-0445
says flip it only with Travis at a boot, then read 2-3 live days (address share bar 5 percent).
Nothing here reaches Du's experience (D-0434): the shadow row is read by the D-0445 follow-up read only.
Not touched (out of scope by the ruling): the voice recent-replies block (D-0442), the write side of
conversation_history, the depth gates (len(conversation_history) < 5) that other blocks use.
"""
from __future__ import annotations

import logging
import re
import time
from pathlib import Path

logger = logging.getLogger("nascence.internal_context_gate")

# False = SHADOW: internal-cycle prompts keep the human window exactly as before; rows are still logged.
# True  = the four prompt blocks are omitted on input_type != "human" cycles. Human cycles never change.
# D-0466 (travis, 2026-10-17): flipped to True for the next boot (J-2336). Revert to False at a restart
# per the D-0466 defeater (internal replies addressed to Travis > 5 percent in the first 3 live days).
INTERNAL_HUMAN_WINDOW_GATE = True

# J-3217 / D-0606 (founder, 2026-11-02, F-3454, row P-0006): on HUMAN cycles an exchange older than this many
# hours is left out of the six window blocks (BLOCK_KEYS: the four prompt builders), so a message that arrives
# days after the last session does not bind to the old turns (the 10-19 11:13 garden question became a scene
# about the 10-16/17 pause exchange). Same-day continuity is unchanged. The age comes from the entry's own
# "ts" (epoch seconds, stamped when the exchange is appended in core/orchestrator.py; legacy entries restored
# from conversation_state.json are stamped with that file's ended_at, the latest the exchange can have happened).
# An entry with no usable "ts" is KEPT (fail-open: today's behaviour). Set to None/0 to switch this off.
# D-0606 defeater: revisit if a message after a pause of more than 24 hours that was meant to continue the
# earlier exchange loses it (a read of the human turns that answer an old exchange); then lengthen N or key it
# to the session instead of the clock.
EXCHANGE_MAX_AGE_HOURS = 24

# The shadow row writer itself (independent of the gate). On by default per the J-2297 briefing.
INTERNAL_CONTEXT_SHADOW_ON = True

_LOG = Path(__file__).parent.parent / "data" / "internal_cycle_context_shadow.jsonl"

BLOCK_KEYS = (
    "episodic.immediate_exchange",
    "reflection.where_we_left_off",
    "reflection.this_session",
    "executive.where_we_left_off",
    "executive.this_session",
    "recall.current_exchange",
)

# Per-cycle notes from keep(): {cycle_id: {block_key: chars}}. Bounded so a cycle that never reaches voice
# (silence, error) cannot grow it without limit.
_NOTES: dict[str, dict[str, int]] = {}
_NOTES_MAX = 32

# F-2918's lexical address pattern (J-1873's read): an asker addressed in the first 160 chars.
_ADDRESS_RE = re.compile(
    r"\bTravis\b|\byou (?:ask|speak|offer|see|call|stand)\b|\byour (?:question|equation)\b|\bthe \w+ you\b",
    re.IGNORECASE,
)
_TRAVIS_RE = re.compile(r"\bTravis\b", re.IGNORECASE)


def is_internal(state) -> bool:
    return (getattr(state, "input_type", "human") or "human") != "human"


def gate_drops(state) -> bool:
    """True when the human window must be left out of this cycle's prompts."""
    return bool(INTERNAL_HUMAN_WINDOW_GATE) and is_internal(state)


def fresh(state, entries, now: float | None = None) -> list:
    """J-3217 / D-0606: `entries` (conversation_history or prior_session_exchanges) as a HUMAN cycle's prompt
    should see them: exchanges older than EXCHANGE_MAX_AGE_HOURS left out. Internal cycles, a disabled constant,
    and entries with no usable "ts" are returned unchanged (the same entries, in order). Never raises."""
    try:
        lst = list(entries or [])
        if not EXCHANGE_MAX_AGE_HOURS or is_internal(state) or not lst:
            return lst
        cutoff = (time.time() if now is None else float(now)) - float(EXCHANGE_MAX_AGE_HOURS) * 3600.0
        out = []
        for ex in lst:
            try:
                ts = ex.get("ts") if isinstance(ex, dict) else None
                ts = float(ts) if ts is not None else None
            except Exception:
                ts = None
            if ts is not None and ts < cutoff:
                continue
            out.append(ex)
        return out
    except Exception:
        return list(entries or [])


def human_window(state) -> tuple[list, list]:
    """(conversation_history, prior_session_exchanges) as a prompt builder should see them this cycle."""
    if gate_drops(state):
        return [], []
    return (list(getattr(state, "conversation_history", None) or []),
            list(getattr(state, "prior_session_exchanges", None) or []))


def keep(state, key: str, block: list) -> list:
    """Return `block` (unchanged) or [] when the gate drops it. Records its size on internal cycles.
    Never raises: any failure returns `block` unchanged (today's behaviour)."""
    try:
        if not is_internal(state):
            return block
        try:
            cid = str(getattr(state, "cycle_id", "") or "")
            notes = _NOTES.setdefault(cid, {})
            notes[key] = sum(len(str(l)) + 1 for l in block) if block else 0
            while len(_NOTES) > _NOTES_MAX:
                _NOTES.pop(next(iter(_NOTES)))
        except Exception:
            pass
        return [] if INTERNAL_HUMAN_WINDOW_GATE else block
    except Exception:
        return block


def _flags(text) -> dict:
    t = str(text or "")
    head = t[:160]
    return {"travis": bool(_TRAVIS_RE.search(t)), "address160": bool(_ADDRESS_RE.search(head))}


def build_row(state, output) -> dict:
    """The shadow row for this cycle (pure: reads state and _NOTES, writes nothing)."""
    cid = str(getattr(state, "cycle_id", "") or "")
    notes = _NOTES.get(cid, {})
    blocks = {}
    for k in BLOCK_KEYS:
        if k in notes:
            blocks[k] = {"present": notes[k] > 0, "chars": notes[k]}
        else:
            blocks[k] = None          # that node did not build a prompt this cycle
    refl = getattr(state, "reflection", None)
    exe = getattr(state, "executive", None)
    scene_o = getattr(state, "episodic_scene", None)
    draft = (getattr(refl, "draft", "") or "") if refl is not None else ""
    synth = (getattr(exe, "synthesis", "") or "") if exe is not None else ""
    rtype = getattr(exe, "response_type", None) if exe is not None else None
    scene = (getattr(scene_o, "scene", "") or "") if scene_o is not None else ""
    out = str(output or "")
    return {
        "ts":               round(time.time(), 3),
        "cycle_id":         cid,
        "input_type":       getattr(state, "input_type", None),
        "gate_on":          bool(INTERNAL_HUMAN_WINDOW_GATE),
        "conv_hist_len":    len(getattr(state, "conversation_history", None) or []),
        "prior_session_len": len(getattr(state, "prior_session_exchanges", None) or []),
        "blocks":           blocks,
        "draft":            draft[:300],
        "synthesis":        synth[:400],
        "response_type":    rtype,
        "output":           out[:300],
        "scene":            scene[:300],
        "flags": {
            "draft":     _flags(draft),
            "synthesis": _flags(synth),
            "output":    _flags(out),
            "scene":     _flags(scene),
        },
    }


def log_shadow(state, output) -> None:
    """Append one row for an internal cycle. Human cycles: nothing. Never raises."""
    try:
        if not INTERNAL_CONTEXT_SHADOW_ON or not is_internal(state):
            return
        row = build_row(state, output)
        _NOTES.pop(row["cycle_id"], None)
        from core import profile, shadow_log
        shadow_log.append(profile.guard_path(_LOG), row)
    except Exception as exc:
        logger.debug("[internal-context] shadow row failed (non-fatal): %s", exc)
