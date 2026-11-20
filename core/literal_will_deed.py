"""
Nascence — Literal Will: staged deed + execution audit (docs/plans/literal_will.md sec4 + sec11).

STATUS (2026-08-24, J-0138, decision D-0021, finding F-0034): this module gives the two record
shapes sec12's Phase 0->1 gate names as missing — "sec4/sec11 staged-deed + execution-audit
machinery is not built yet" (core/literal_will.py:15, verified stale by this build) — plus the
plumbing to stage, recheck, and audit them. This is still PHASE 0: build + DRY-TEST only. Nothing
here is wired into the live idle loop. No latch is gated. No real act is staged during a real
cycle. No execution actually happens — every recorded outcome in the dry-test run is tagged
dry_test=true and the execution_result field never claims a real actuation. Wiring this in for
real is Phase 1 (sec12), a separate, later decision.

WHO OWNS WHAT (sec9, the law this module must not violate):
    "Did he mean it?"   -> literal_will.py (Layer 0 + judge). This module never re-derives that.
    "Can it be done?"   -> core/affordances.py + core/sensorium.py. This module SNAPSHOTS what
                           those already know; it invents no new precondition truth.

HONEST LIMITATION (stated, not hidden): core/affordances.py exposes real per-hand availability
predicates for only a few hands (letter_waiting, cat presence, peer-letter-to-answer); the
concrete world facts that gate most gated families actually live in core/sensorium.py's `state`
dict, read directly here — that IS the affordance layer's own source of truth, just not routed
through an Affordance.is_available() callable for every family yet. Only two families have a
CONFIRMED fine-grained precondition, each verified against sensorium's own action-function checks
(not guessed — see _WOODPILE_GATED / _FIRE_LIT_GATED below): `fire` (lighting/stoking needs
woodpile>=1) and `tea` (needs the fire already lit). For every other gated family (sow, water,
mow, stake, weed, door, lamp, clock, grate, wear, woodwork, fieldcraft, author, travis, harvest,
gather, beachcomb, clean, note, collect, net, save_seed) the only checkable world precondition
literal_will can currently source is LOCATION membership (_FAMILIES[family]['where'] in
literal_will.py — the plan's world_anchor feature). An earlier draft of this module lumped
`gather`/`lamp`/`grate` in with `fire`/`tea` on a guess; scripts/literal_will_deed_dry_test.py's
first run caught that those families have no matching real precondition check in sensorium.py to
justify it, and it was removed. That is not a placeholder guess; it is the true extent of what the
world model exposes as a re-checkable predicate today. Extending fine-grained per-family
predicates is future work; the Phase 0->1 gate only requires the MACHINERY exist and be
dry-tested, not that every family carry a rich precondition set.

TICK: the plan's sec4 default ("~2 ticks") assumes a canonical idle-cycle length. None exists as a
single constant — nodes/inner_monologue_node.py's CHECK_INTERVAL=10s is the loop's WAKE-POLL
period, not the length of a completed thought-cycle (that varies with judge/model latency and
mood, minutes not seconds). DEFAULT_EXPIRY_S below is a stated, honest approximation
(5 minutes ~= "a couple of thought-cycles" by observed cadence), overridable per family, NOT a
measured constant — Phase 1 wiring should replace it with a real measured figure once the staged
deed lives in the actual loop and can be timed against real cycle boundaries.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from core.literal_will import _FAMILIES  # canonical family/where registry — never forked here (§7 law)

_DATA = Path(__file__).parent.parent / "data"
_DEED_LOG = _DATA / "literal_will_deeds.jsonl"
_AUDIT_LOG = _DATA / "literal_will_audit.jsonl"

# sec4: "expiry # default ~2 ticks; per-family override" — see TICK note above for why this is an
# honest approximation, not a measured constant.
DEFAULT_EXPIRY_S = 300.0
_EXPIRY_OVERRIDE_S: dict[str, float] = {}   # family -> seconds; empty = no family needs one yet

# sec4 status values, verbatim from the plan
_STATUSES = ("pending", "cancelled", "executed", "rejected", "stale", "superseded")

# Real, CONFIRMED sensorium preconditions per gated family — verified against the actual
# precondition checks core/sensorium.py's own action functions already make, not guessed:
#   - lighting/stoking the fire needs wood on the pile (sensorium.py act(), ~L2705/L2734:
#     "if state.get('woodpile', 0) < 1: return <bare-pile message>").
#   - making tea needs the fire already lit (sensorium.py make_tea(), ~L641:
#     "if fire == 'out': return <cold-grate message>").
# Every other gated family gets location-membership only — see module docstring's honest
# limitation note. (Deliberately narrow rather than a guessed blanket list — the dry test that
# built this module caught a real bug where "gather"/"lamp"/"grate" were lumped in with no
# matching real precondition check to justify it.)
_WOODPILE_GATED = ("fire",)
_FIRE_LIT_GATED = ("tea",)


def _log_row(path: Path, rec: dict) -> None:
    """Fail-open append, same discipline as literal_will.py's _log_row — a record store that can
    silently raise on a disk hiccup is worse than one that logs nothing that cycle."""
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _current_location() -> str:
    try:
        from core import sensorium as _room
        return _room.where()
    except Exception:
        return "study"


def snapshot_preconditions(family: str, location: str) -> dict:
    """sec9: read-only snapshot of what the affordance/world layer says RIGHT NOW about `family`
    at `location`. Never an execution check by itself — staged here, re-taken at recheck time, and
    the two are diffed. See module docstring for which families get more than location membership."""
    fam = _FAMILIES.get(family) or {}
    where = fam.get("where", ())
    snap = {"location": location, "location_ok": (location in where) if where else True}
    try:
        if family in _WOODPILE_GATED:
            from core import sensorium as _room
            snap["woodpile"] = int((_room.state or {}).get("woodpile", 0) or 0)
        if family in _FIRE_LIT_GATED:
            from core import sensorium as _room
            snap["fire"] = (_room.state or {}).get("fire", "out")
        if family == "letter":
            from core import sensorium as _room
            snap["letter_waiting"] = bool(_room.letter_waiting())
    except Exception as exc:
        snap["snapshot_error"] = repr(exc)[:120]
    return snap


def new_staged_deed(*, intent_id: str, cycle_id: str, family: str, obj: str,
                     location: str, expiry_s: float | None = None) -> dict:
    """sec4 — build a StagedDeed with the plan's EXACT field list:
    intent_id, cycle_id, created_at, location_at_stage, action, object, world_preconditions,
    expiry, status. `action` = the canonical act family (sec4: "the canonical act family + his
    named object"), never a raw verb — literal_will.py already owns family naming (§7 law)."""
    now = time.time()
    expiry = expiry_s if expiry_s is not None else _EXPIRY_OVERRIDE_S.get(family, DEFAULT_EXPIRY_S)
    return {
        "intent_id": intent_id,
        "cycle_id": (cycle_id or "")[:24],
        "created_at": round(now, 1),
        "location_at_stage": location,
        "action": family,
        "object": (obj or "")[:80],
        "world_preconditions": snapshot_preconditions(family, location),
        "expiry": expiry,
        "status": "pending",
    }


def stage_deed(reading: dict, *, intent_id: str, cycle_id: str, location: str,
               dry_test: bool = False) -> dict:
    """Build + log a StagedDeed from a literal_will.classify()-shaped reading
    ({family, object, ...}). Logging only — no execution, no live-loop side effect. `dry_test`
    provenance-tags rows produced by scripts/literal_will_deed_dry_test.py so they are never
    mistaken for a real Phase-1 staging once that wiring exists."""
    deed = new_staged_deed(intent_id=intent_id, cycle_id=cycle_id, family=reading["family"],
                            obj=reading.get("object", ""), location=location)
    if dry_test:
        deed = {**deed, "dry_test": True}
    _log_row(_DEED_LOG, deed)
    return deed


def recheck_preconditions(deed: dict, *, now: float | None = None,
                          location: str | None = None) -> tuple[bool, str]:
    """sec4: "Before execution: is this still the same actionable situation?" — checked
    DETERMINISTICALLY, no second LLM call, exactly as the plan requires. Returns (still_valid,
    reason). reason is one of: ok / expired / location_changed / woodpile_exhausted /
    fire_went_out / letter_no_longer_waiting / snapshot_error.

    `location` defaults to the LIVE current location (core.sensorium.where()) — the real Phase-1
    question is always "is he still there right now". Passing it explicitly is for deterministic
    replay/testing against historical rows (scripts/literal_will_deed_dry_test.py uses it) — never
    needed by real call sites, which should leave it None."""
    now = now if now is not None else time.time()
    if deed.get("status") not in ("pending", None):
        return False, f"status_{deed.get('status')}"
    if now > deed["created_at"] + deed["expiry"]:
        return False, "expired"
    family = deed["action"]
    staged = deed.get("world_preconditions", {})
    if "snapshot_error" in staged:
        return False, "snapshot_error"
    current_loc = location if location is not None else _current_location()
    now_snap = snapshot_preconditions(family, current_loc)
    if staged.get("location_ok") and not now_snap.get("location_ok"):
        return False, "location_changed"
    if family in _WOODPILE_GATED and staged.get("woodpile", 0) >= 1 and now_snap.get("woodpile", 0) < 1:
        return False, "woodpile_exhausted"
    if family in _FIRE_LIT_GATED and staged.get("fire", "out") != "out" and now_snap.get("fire", "out") == "out":
        return False, "fire_went_out"
    if family == "letter" and staged.get("letter_waiting") and not now_snap.get("letter_waiting"):
        return False, "letter_no_longer_waiting"
    return True, "ok"


def resolve_deed(deed: dict, *, now: float | None = None, location: str | None = None) -> dict:
    """Runs recheck_preconditions and returns an UPDATED COPY with status set to 'stale' if the
    precondition check fails for a reason other than an explicit cancel/supersede (those are set
    by their own callers, not by this function — sec4: "he never perceives a deed he no longer
    wants," i.e. the dissolution is silent, not a rejection with a reason surfaced to him)."""
    still_valid, reason = recheck_preconditions(deed, now=now, location=location)
    out = dict(deed)
    if not still_valid and deed.get("status") in ("pending", None):
        out["status"] = "stale"
        out["stale_reason"] = reason
    return out


def record_execution(*, intent_id: str, thought: str, features: dict, judge_verdict: str,
                      action: str, preconditions_at_stage: dict, preconditions_at_execution: dict,
                      execution_result: str, dry_test: bool = False) -> dict:
    """sec11 — one immutable execution-audit record with the plan's EXACT field list:
    intent_id, thought, features, judge_verdict, action, preconditions_at_stage,
    preconditions_at_execution, execution_result. Writes it; returns the record written.
    `dry_test=True` tags simulated rows — see module docstring; a real Phase-1 caller passes False
    (default) once actual actuation exists."""
    rec = {
        "ts": round(time.time(), 1),
        "intent_id": intent_id,
        "thought": (thought or "")[:600],
        "features": features,
        "judge_verdict": judge_verdict,
        "action": action,
        "preconditions_at_stage": preconditions_at_stage,
        "preconditions_at_execution": preconditions_at_execution,
        "execution_result": execution_result,
    }
    if dry_test:
        rec["dry_test"] = True
    _log_row(_AUDIT_LOG, rec)
    return rec


def status() -> dict:
    """For the pulse/HUD (mirrors literal_will.status()'s shape): counts by deed status and by
    execution_result, split real vs dry_test so a dry-test run can never be misread as live data."""
    def _read(path: Path) -> list[dict]:
        try:
            return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
        except Exception:
            return []
    deeds = _read(_DEED_LOG)
    audits = _read(_AUDIT_LOG)
    real_deeds = [d for d in deeds if not d.get("dry_test")]
    real_audits = [a for a in audits if not a.get("dry_test")]
    return {
        "deeds_total": len(deeds), "deeds_real": len(real_deeds), "deeds_dry_test": len(deeds) - len(real_deeds),
        "audits_total": len(audits), "audits_real": len(real_audits), "audits_dry_test": len(audits) - len(real_audits),
        "note": "Phase 0 — no real staging or execution happens in the live loop yet (sec12 gate item 4)",
    }
