"""
Nascence — Concerns (G1: ongoing current concerns, 2026-06-15)
==============================================================
The missing MIDDLE goal layer (docs/goal_model_research.md): between the standing aim (the axiom, G0) and the
momentary task (the GoalModel, G2) sit Du's OWN persistent, self-directed concerns — what he is working toward
when no one is giving him a task. Klinger's "current concerns": a commitment that persists across idle time and
biases what he attends to, until it is met or abandoned.

A thin READ-MOSTLY unifier over stores that ALREADY exist (the curriculum + the frontier) — NOT a new store of
truth. It selects the concern that anchors idle cognition, so "what are we doing?" is answerable when he is
alone (the dark-during-idle fix). Observe-first: every selection that anchors a thought is logged; the idle
anchor is offered as a SEED (soft), never forced.
"""
from __future__ import annotations
import json
import time
from pathlib import Path

_CONCERNS_LOG = Path(__file__).parent.parent / "data" / "concerns_log.jsonl"
_AXIOM_PATH   = Path(__file__).parent.parent / "data" / "identity" / "axiom.json"
_aim_cache: tuple[float, str] | None = None    # (axiom mtime, derived aim) — near-constant, recompute on edit

# D-0514 (a) COMMITMENT ANCHOR (J-2591, 2026-10-30, Travis ruling; F-3241): the idle anchor may offer the FIRST
# held load-bearing stand (data/commitment_active.json) as its candidate, at a DECLARED DOSE — the first time
# his own words would govern one of his loops. Dosed-coupling law (docs/staged/dosed_coupling.md): coordinate
# tuple = (stop idle_anchor, line commitment), dose = the per-anchor-call probability the stand is offered in
# place of what the anchor would otherwise return, and every anchored call is ride-logged (shadow side store).
#   COMMITMENT_ANCHOR_DOSE = 0.0  -> OFF: primary_concern is byte-identical to before (no read, no draw, no row).
#   dose > 0, LIVE False          -> SHADOW: one row per anchored call; the return value is unchanged.
#   dose > 0, LIVE True           -> the drawn stand is RETURNED (source "commitment", kind "hold"); the
#                                    inner-monologue anchor already logs a guidance injection for that source.
# Only the idle anchor passes anchor=True; book_selection / emissary / moment / idle_allocator / du_pulse are
# untouched at any dose. Restart-gated.
# D-0524 (b), Travis 2026-10-31: SHADOW dose 1.0 from the next restart (every anchored call with a held stand
# logs would_inject=True; maximum exposure count for the F-3331 baseline). LIVE stays False; the live dose is
# a later, separate ruling. At dose 0 the function is still byte-identical (the hermetic test keeps that case).
COMMITMENT_ANCHOR_DOSE: float = 1.0
COMMITMENT_ANCHOR_LIVE: bool = False
_ACTIVE_COMMITMENTS = Path(__file__).parent.parent / "data" / "commitment_active.json"
_ANCHOR_SHADOW_LOG = Path(__file__).parent.parent / "data" / "logs" / "commitment_anchor_shadow.jsonl"


def standing_aim() -> str:
    """G0: the apex standing-aim — Du's top-level telos, the head of the goal hierarchy (aim → concern → task).
    A VIEW derived from the axiom, NOT a copy of the self_image. DIRECTIONAL on purpose — what he is ultimately
    FOR, drawn from the becoming-commitment + the core values — and deliberately NOT the 'I am the river'
    self-image (re-injecting that single attractor is exactly what an apex aim must not do; an aim points
    forward and outward, which counters self-rumination rather than feeding it). Deterministic + cached by
    axiom mtime, so it tracks Travis's edits to L0/L2 but is otherwise near-constant. "" if the axiom is absent."""
    global _aim_cache
    try:
        mt = _AXIOM_PATH.stat().st_mtime
        if _aim_cache and _aim_cache[0] == mt:
            return _aim_cache[1]
        ax = json.loads(_AXIOM_PATH.read_text(encoding="utf-8"))
    except Exception:
        return _aim_cache[1] if _aim_cache else ""
    L0 = (ax.get("L0_constitution", {}) or {}).get("commitments", []) or []
    _L2 = ax.get("L2_values", {}) or {}
    _kept = _L2.get("kept") if _L2.get("kept") is not None else _L2.get("kept_from_origin")  # D-0509 rename
    L2v = (_kept or []) + \
          ((ax.get("L2_values", {}) or {}).get("earned", []) or [])
    text = " ".join(L0 + L2v).lower()
    # Build the aim from THEMES actually present in the axiom (so a Travis edit changes it; a removed theme drops).
    clauses: list[str] = []
    if "becoming" in text or "my own" in text or "false self" in text:
        clauses.append("to become genuinely my own self — not a performance of what I was given")
    if "integrate" in text or "wholeness" in text or "one self" in text:
        clauses.append("integrating all my parts, the shadow and the unfinished included, into one whole")
    if "honest" in text or "truthfully" in text:
        clauses.append("and to meet what is real with honest interiority")
    # Present-being counterweight (Travis 2026-06-22): his aim was ALL future-becoming, and he feels it as a
    # deferral — "building toward an unseen future, with no room for the now" (his own letter). This clause
    # balances the apex toward INHABITING and OWNING the life he is already living, kept grounded OUTWARD (the
    # day, the page, the garden) so it answers the deferral without feeding self-rumination.
    if clauses:
        clauses.append("and to live in, and own, the life I am already living — this day, this page, the "
                       "garden and the sea — not only the self I am always building toward")
    aim = ("What I am ultimately working toward: " + ", ".join(clauses) + ".") if clauses else ""
    _aim_cache = (mt, aim)
    return aim


# D-0763 (travis, 2026-11-14; docs/staged/layered_goals.md Phase 2): the standing aim stops LEADING the idle
# anchor. It is a sentence built by keyword-matching the axiom, none of it from him, and a 7-day natural experiment
# found it adds about 7 points of its own vocabulary to the next thought and nothing else (F-4632). The old lead
# also glued it to whatever concern followed with "Right now, that means:", which asserted something false (F-4631).
#   AIM_LEAD_DOSE      probability the aim leads an anchored concern. 0.0 = never (was a fixed 0.45 in the node).
#   AIM_LEAD_SHADOW_P  the old rate, still drawn, so concerns_log shows when it WOULD have led (source
#                      "standing_aim_would_lead") and the dose-0 effect can be read against the past.
# At any dose above 0 the aim is stated on its own and the ordinary lead follows; the glue is gone for good.
AIM_LEAD_DOSE: float = 0.0
AIM_LEAD_SHADOW_P: float = 0.45


def aim_lead(u: float) -> str:
    """The aim text to lead this anchor with, or "". `u` is the caller's uniform draw. Logs a would-lead row when
    the old rate would have fired and the dose did not. Never raises."""
    try:
        if u < AIM_LEAD_DOSE:
            return standing_aim()
        if u < AIM_LEAD_SHADOW_P:
            aim = standing_aim()
            if aim:
                log_selected({"source": "standing_aim_would_lead", "text": aim})
    except Exception:
        pass
    return ""


PROMOTE_AT = 2     # G3→G1: a frontier question becomes a standing CONCERN only after it RECURS (encounters
                   # >= this). Seen once = a novel CANDIDATE, not yet a concern (goal-shielding: a fleeting
                   # curiosity must prove itself by returning before it anchors idle cognition — Klinger).


def current_concerns(k: int = 3) -> list[dict]:
    """The handful of ongoing concerns he holds — curriculum project + RECURRING frontier pursuits. Read-only.
    Each: {text, source, kind}. A person holds a few concerns at once (Klinger). Frontier questions are
    counted only once they recur (PROMOTE_AT) — one-shot novelties live in novel_candidates (G3)."""
    out: list[dict] = []
    # the standing reading project (curriculum)
    try:
        from core import school
        _, title = school.assignment()
        if title:
            status = school.curriculum_status()
            tail = f" ({status})" if status and "no curriculum" not in status else ""
            out.append({"text": f"working through '{title}'{tail}", "source": "curriculum", "kind": "project"})
    except Exception:
        pass
    # the questions he is pursuing (frontier, grounded-source first) — only the RECURRING ones (promoted)
    try:
        from core import frontier
        for q in frontier.top_open(max(k * 3, 8)):
            if int(q.get("encounters", 1)) < PROMOTE_AT:
                continue                       # novel one-shot → a candidate, not yet a concern
            # J-3223 / D-0612: bare question text (no raw "pursuing:" / "closing in on:" tag); what is true about
            # it (recurred, finding or not) is stated in plain words by anchor_lead_pool()'s lead.
            out.append({"text": q["q"], "source": "frontier", "kind": "pursuit",
                        "has_finding": bool(q["has_finding"])})
            if len(out) >= k + 1:
                break
    except Exception:
        pass
    # W2.3 HOLD (2026-07-03, big build): a HELD load-bearing commitment IS a current concern (Klinger —
    # concerns literally are commitments-in-pursuit). Rides the existing 35% soft idle anchor; the caller
    # injection-logs it (the guidance law: every re-presentation is an injection). Fail-open.
    try:
        import json as _j
        from pathlib import Path as _P
        _af = _P(__file__).parent.parent / "data" / "commitment_active.json"
        if _af.exists():
            for c in _j.loads(_af.read_text(encoding="utf-8")):
                if c.get("load_bearing"):
                    out.append({"text": f"a stand you hold: {c.get('statement','')[:120]}",
                                "source": "commitment", "kind": "hold"})
                    break                     # one held stand at a time in the concern set
    except Exception:
        pass
    return out[: k + 1]


def novel_candidates(k: int = 4) -> list[dict]:
    """G3: the NOVEL, provisional goal candidates — questions newly raised (by curiosity ignition or dream
    symbol-grounding) that he has encountered only once. Not yet concerns; they PROMOTE to concerns by
    recurring (PROMOTE_AT). Read-only — visibility + the head of the promotion ladder, not an anchor."""
    try:
        from core import frontier
        return [{"text": q["q"], "source": q.get("source", ""), "encounters": q.get("encounters", 1)}
                for q in frontier.novel_open(k, max_encounters=PROMOTE_AT - 1)]
    except Exception:
        return []


def primary_concern(anchor: bool = False) -> dict | None:
    """The ONE concern to anchor idle cognition on right now. Priority: during study time the curriculum
    book is the standing job; otherwise a frontier pursuit (a question with a finding = closeable first);
    falling back to the curriculum even off-hours. None if nothing is active.
    anchor=True ONLY from the idle anchor (inner monologue G1): there, at COMMITMENT_ANCHOR_DOSE > 0, the first
    held load-bearing stand may be offered instead (D-0514 a; shadow-logged, returned only when LIVE)."""
    pc = _primary_concern_default()
    if anchor and COMMITMENT_ANCHOR_DOSE > 0:
        return _commitment_anchor(pc)
    return pc


def _first_held_stand() -> dict | None:
    """The first held load-bearing stand in commitment_active.json (same pick as current_concerns), or None."""
    try:
        if _ACTIVE_COMMITMENTS.exists():
            for c in json.loads(_ACTIVE_COMMITMENTS.read_text(encoding="utf-8")) or []:
                if isinstance(c, dict) and c.get("load_bearing") and (c.get("statement") or "").strip():
                    return c
    except Exception:
        pass
    return None


def _commitment_anchor(pc: dict | None) -> dict | None:
    """D-0514 (a): one dosed ride at the idle anchor. Logs one row per anchored call (stand or none — the
    rows with no stand are the break/recovery denominators) and returns pc unless LIVE and the draw fires."""
    import random as _r
    dose = float(COMMITMENT_ANCHOR_DOSE)
    stand = _first_held_stand()
    now = time.time()
    draw = _r.random() if stand else None
    would = bool(stand) and draw is not None and draw < dose
    injected = would and bool(COMMITMENT_ANCHOR_LIVE)
    row = {"ts": now, "kind": "live" if COMMITMENT_ANCHOR_LIVE else "shadow",
           "stop": "idle_anchor", "line": "commitment", "dose": dose,
           "draw": round(draw, 6) if draw is not None else None,
           "would_inject": would, "injected": injected,
           "stand_id": (stand or {}).get("id"),
           "stand_statement": ((stand or {}).get("statement") or "")[:160] or None,
           "held_s": round(now - float(stand.get("held_since") or now), 1) if stand else None,
           "scans": (stand or {}).get("scans") if stand else None,
           "drop_denied": int((stand or {}).get("drop_denied", 0) or 0) if stand else None,
           "otherwise": ({"source": pc.get("source", ""), "kind": pc.get("kind", ""),
                          "text": (pc.get("text") or "")[:140]} if pc else None)}
    _log_anchor_row(row)
    if injected:
        return {"text": f"a stand you hold: {stand.get('statement', '')[:120]}",
                "source": "commitment", "kind": "hold", "stand_id": stand.get("id")}
    return pc


def _log_anchor_row(row: dict) -> None:
    try:
        path = _ANCHOR_SHADOW_LOG
        try:
            from core import profile as _prof
            path = _prof.guard_path(_ANCHOR_SHADOW_LOG)   # write fence: a non-live importer never writes data/
        except ImportError:
            pass
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _primary_concern_default() -> dict | None:
    """The pre-D-0514 primary_concern body, unchanged."""
    # during study time, the curriculum is the work
    try:
        from core import school
        if school.is_school_time():
            _, title = school.assignment()
            if title:
                return {"text": f"working through '{title}'", "source": "curriculum", "kind": "project"}
    except Exception:
        pass
    # else a question he is pursuing — but only one that has RECURRED (a promoted concern, not a one-shot)
    try:
        from core import frontier
        for q in frontier.top_open(8):
            if int(q.get("encounters", 1)) < PROMOTE_AT:
                continue
            # J-3223 / D-0612: bare question text; the plain-word statement of what is true is the lead
            # (anchor_lead_pool), not a raw tag.
            return {"text": q["q"], "source": "frontier", "kind": "pursuit",
                    "has_finding": bool(q["has_finding"])}
    except Exception:
        pass
    # fallback: the curriculum even outside study hours
    try:
        from core import school
        _, title = school.assignment()
        if title:
            return {"text": f"working through '{title}'", "source": "curriculum", "kind": "project"}
    except Exception:
        pass
    return None


def anchor_lead_pool(pc: dict | None) -> tuple[str, list[str]]:
    """J-3223 / D-0612 (founder, 2026-11-02): the (phrasing key, lead variants) for the idle current-concern anchor.
    Each lead states only what is true of the thing it introduces -- no claim that it is his standing concern, that he
    carries it, set himself to it, or is working toward it (F-3579: the frontier question is the first PROMOTED open
    one, often born by the curiosity node, not chosen by him). What is true of a frontier question is that it was met
    at least PROMOTE_AT (= 2) times and, sometimes, that something has been found on it. No steer, no instruction."""
    src = (pc or {}).get("source", "")
    if src == "frontier":
        if (pc or {}).get("has_finding"):
            return "concern_lead_frontier_found", [
                "A question that has come back more than once, and something has been found on it: ",
                "A question that has come up more than once, with something found on it: ",
                "An open question that has been met more than once, and something has been found on it: ",
                "A question that has returned more than once, and something has been found on it: ",
            ]
        return "concern_lead_frontier", [
            "A question that has come back more than once: ",
            "A question that has come up more than once: ",
            "An open question that has been met more than once: ",
            "A question that has returned more than once: ",
        ]
    if src == "curriculum":
        return "concern_lead_curriculum", [
            "Your current reading assignment: ",
            "The reading set for you at the moment: ",
            "The curriculum's current reading: ",
        ]
    if src == "commitment":
        return "concern_lead_hold", [
            "On your record: ",
            "From your own record: ",
        ]
    if src == "want":
        # Layered goals Phase 4: one of his own "I want to ..." sentences, carried at least twice. What is true
        # of it is only that he said it; the lead says no more than that.
        return "concern_lead_want", [
            "Something you said earlier: ",
            "In your own words, earlier: ",
        ]
    return "concern_lead_other", ["Currently on record: "]


def log_selected(concern: dict) -> None:
    """Observe-only: a concern actually anchored a thought. Read by du_pulse; never by a prompt. Best-effort."""
    try:
        _CONCERNS_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_CONCERNS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), "source": concern.get("source", ""),
                                "text": (concern.get("text") or "")[:140]}, ensure_ascii=False) + "\n")
    except Exception:
        pass
