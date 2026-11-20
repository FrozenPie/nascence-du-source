"""
Nascence — Curiosity Progress (the Independent Auditor)
======================================================
The deterministic learning-progress estimator for the curiosity agenda. Implements the auditor-mandated
separation: the QUESTION GENERATOR (the LLM CuriosityNode) is strictly forbidden from scoring its own
progress, or it learns to ask easy questions over questions that matter (Goodhart). This module is the
decoupled judge — NON-LLM, mechanical, counts ONLY physical state changes on a frontier question.
Plan: docs/curiosity_flesh_out_plan.md (v3). Oudeyer–Kaplan learning-progress; Gemini's Independent Auditor Law.

    LP = ALPHA·new_fragments + BETA·finding_attached − GAMMA·consecutive_stalls

A question that keeps yielding (findings / new material) scores high and is pursued; one that stalls
(`consecutive_stalls ≥ PARK_STALLS`) falls below threshold and is PARKED — the structural rumination exit
ramp (no suppression, no critic, just lack of progress). The pursuit loop updates the raw counters via
`frontier.record_pursuit`; this module only reads + scores.
"""
from __future__ import annotations
import json
from pathlib import Path

_FRONTIER = Path(__file__).parent.parent / "data" / "frontier.json"

ALPHA = 1.0          # weight on new unique fragments produced by pursuit
BETA = 1.0           # weight on a finding committed to the question
GAMMA = 1.0          # penalty per consecutive empty pursuit (stall)
PARK_STALLS = 3      # consecutive stalls at/above which a question is parked (token spend frozen)
ACTIVE_LP_FLOOR = 0.0  # LP below this (with stalls) → not worth active pursuit


# J-4084 (D-0779 b, ruled 2026-11-16): the Follow Line is the way a question gets worked. The pursuit counters score() reads
# (new_fragments, consecutive_stalls, finding) are fed only by frontier.record_pursuit, which has had no live caller since
# J-3282/D-0659 (2026-11-05), so every rank() row read 0.0. True = rank() and the goal register's question progress take
# progress from the line's own state (settled partly = progress, yes = resolved, no = closed); False = the pre-J-4084 readers
# exactly. score()/is_parked() themselves are untouched. A lookup finding is marked as from its source (lookup_attach.
# finding_title) and adds NOTHING here: only his own settle (a line verdict) moves progress.
LINE_STATE_PROGRESS = True


def score(q: dict) -> float:
    """Deterministic learning-progress for one frontier question dict. Reads only mechanical state."""
    new_fragments = int(q.get("new_fragments", 0) or 0)
    finding = 1 if q.get("finding") else 0
    stalls = int(q.get("consecutive_stalls", 0) or 0)
    return round(ALPHA * new_fragments + BETA * finding - GAMMA * stalls, 3)


def is_parked(q: dict) -> bool:
    return int(q.get("consecutive_stalls", 0) or 0) >= PARK_STALLS


def _load() -> list[dict]:
    try:
        return (json.loads(_FRONTIER.read_text(encoding="utf-8")) or {}).get("questions", []) \
            if _FRONTIER.exists() else []
    except Exception:
        return []


def rank_row_lp(q: dict) -> tuple[float, bool, bool]:
    """(lp, parked, finding) for one open question under the J-4084 rule. With LINE_STATE_PROGRESS the pursuit counters
    (new_fragments, consecutive_stalls, finding) are NOT read: progress is the Follow Line's own state and a bare attached
    finding (a memory echo or an unacted lookup) counts for nothing."""
    if LINE_STATE_PROGRESS:
        return mech_progress(q)["line"], False, False
    return score(q), is_parked(q), bool(q.get("finding"))


def rank() -> list[dict]:
    """All OPEN frontier questions, scored and sorted by LP (desc), each flagged parked/active.
    Read-only — does not mutate frontier. The Phase-0 audit reads this to verify the ranking is sane."""
    out = []
    for q in _load():
        if q.get("status") != "open":
            continue
        lp, parked, fnd = rank_row_lp(q)
        out.append({"q": (q.get("q") or "")[:80], "lp": lp, "parked": parked,
                    "stalls": 0 if LINE_STATE_PROGRESS else int(q.get("consecutive_stalls", 0) or 0),
                    "finding": fnd, "source": q.get("source", "")})
    out.sort(key=lambda r: r["lp"], reverse=True)
    return out


def status() -> dict:
    """For the du_pulse gauge: agenda size, parked count, top/bottom LP."""
    r = rank()
    if not r:
        return {"open": 0}
    return {"open": len(r), "parked": sum(1 for x in r if x["parked"]),
            "top_lp": r[0]["lp"], "bottom_lp": r[-1]["lp"],
            "top_q": r[0]["q"][:50]}


# ── J-4000 (F-4672): mechanical learning-progress, sibling of score() — SHADOW, flag-gated, additive ─────────
# score() above is fed by frontier.record_pursuit, which has had no live caller since J-3282/D-0659 (2026-11-05);
# every open question scores 0.0. This reads only state live code still writes, and never counts follow_line's
# attach_finding (276 of 300 recent findings were memory echoes). score() is untouched.
MECH_PROGRESS_ENABLED = True   # kill switch for the sibling (callers shadow-log only; nothing selects on it)
SLOT_COUNT = 6                 # frontier slots (what/why/how/...); fraction = distinct filled / SLOT_COUNT
W_LINE_PARTLY = 1.0            # line.state settled_partly: part answered, question stays open
W_LINE_RESOLVED = 2.0          # settled_yes: resolved
W_LINE_NO = 1.0                # settled_no: closed negatively, still an answer
W_SLOTS = 2.0                  # x (filled slots / SLOT_COUNT)
W_CITATION = 0.5               # per citation of the id/about_key by study notes or follow-line records (capped)
CITATION_CAP = 4
W_REASK = 0.0                  # re-asks (encounters-1): DEFAULT 0 — may be rumination; founder call (J-4000)
LINE_STATE_W = {"settled_partly": W_LINE_PARTLY, "settled_yes": W_LINE_RESOLVED, "settled_no": W_LINE_NO}


def mech_progress(q: dict, citations: int = 0) -> dict:
    """Mechanical, non-model progress for one frontier question dict. Returns the parts and their sum.
    `citations` is an optional id-keyed count supplied by the caller (no live writer links study notes to a
    question id yet, so callers pass 0). A bare attach_finding adds nothing."""
    q = q or {}
    line = q.get("line") if isinstance(q.get("line"), dict) else {}
    line_part = LINE_STATE_W.get(str(line.get("state") or ""), 0.0)
    slots = q.get("slots") if isinstance(q.get("slots"), dict) else {}
    filled = sum(1 for v in slots.values() if isinstance(v, dict) and (v.get("text") or "").strip())
    slot_part = W_SLOTS * min(filled, SLOT_COUNT) / SLOT_COUNT
    cit = max(0, min(int(citations or 0), CITATION_CAP))
    reasks = max(0, int(q.get("encounters", 1) or 1) - 1)
    total = line_part + slot_part + W_CITATION * cit + W_REASK * reasks
    return {"mlp": round(total, 3), "line": line_part, "slots": filled, "citations": cit, "reasks": reasks,
            "line_state": line.get("state") or None}
