"""
Resting as a legitimate dream ending (J-3177, D-0565, plans dream_overhaul + closure_law).  SHADOW / RESTART-GATED.

THE RULING (founder, 2026-11-02): "Resting is a legitimate ending. Stop reading ended-unfaced as failure; change what
the carry and met-state key on; the closure writer reads a rest as a close." The evidence behind it (F-3574, F-3719):
since 10-05, 119 of 140 arcs ended 'ended-unfaced' and 20 'stalled'; the dreamer's close note itself says "bring THIS
motion to its rest ... force no neat resolution". A dream that arrives at its ending and stops is doing what it was
asked to do; the downstream was built as if only an empty unresolved_core counted.

DESIGN PASS: every reader of the ending / unresolved state, and what a 'rest' does to each (the finding recorded by J-3177 holds
the same table). READ = who reads it today; REST = what this change makes it do (live mode); SHADOW = what is logged.

  nodes/dream_node.py _last_unresolved_arc   READ  rec.ended_unresolved -> returns the arc as tonight's carry
                                              REST  an arc that ended at rest is NOT returned (live). An arc that did not
                                                    arrive (stalled / dropped / ceiling) keeps the legacy carry.
  nodes/dream_node.py _carried_n             READ  ended_unresolved -> counter+1. Only called when the arc was returned,
                                              so a rest arc never counts; no change needed.
  nodes/dream_node.py _met_carry_check       READ  dream_met.thread_state -> computed / provisional met ends the carry.
                                              REST  unchanged: it can only end a carry; a rest arc has already ended it.
  nodes/dream_node.py _bridge_final          READ  last.unresolved_core -> shadow event (source 'unresolved_dream', feeds
                                                    tension_ledger SALIENCE and core/balance.py's shadow verdict).
                                              REST  UNCHANGED here: not in D-0565's list (carry, met-state, closure) and it
                                                    feeds tension pressure, which is a separate ruling. Follow-up job.
  nodes/dream_node.py _log_arc               READ  writes ended_unresolved / close_reason / final_unresolved_core. REST
                                                    changes nothing it writes (dream_log.jsonl keeps its shape).
  nodes/dream_node.py _judge_close_reason    READ  the panel's verdict sets the resolved / ended-unfaced LABEL. D-0580:
                                                    measurement only, wire nothing. REST classification deliberately does
                                                    NOT read that label's resolved-vs-unfaced distinction (both are
                                                    'arrived at its ending'); it reads only whether the arc arrived.
  core/night.py CARRY_MAX_NIGHTS=3           READ  the cap on how often a returned arc returns. UNCHANGED; the rest check
                                                    sits before it (a rest arc is never returned, so never counted).
  core/night.py remember_dream / stage       READ  copies close_reason into recent_dreams.json and the night ledger (a
                                                    label, read by nobody that acts). UNCHANGED.
  core/dream_met.py carry_thread_root        READ  last arc ended_unresolved -> a thread exists. REST (live): a rest arc is
                                                    not a thread, so thread_state() answers 'none' for it.
  core/dream_met.py compute_states           READ  tension texts incl. final_unresolved_core; any arc, ended or not.
                                              REST  each state row gains an additive 'ending' (rest | open | met-core) so a
                                                    'met' that follows a rest is distinguishable from one that follows a
                                                    stall. 'met' itself (the waking mind stopped returning) is unchanged.
  core/closure.py record_dream_met           READ  fires on a computed 'met' only; _dream_prompts reads
                                                    final_unresolved_core. REST: the row gains 'ending'. Unchanged gate.
  core/closure.py record_rest_close (NEW)    REST  a rest is read as a CLOSE CANDIDATE: one kind='rest_close' shadow row per
                                                    rest arc. It is CERTIFIED only by an independent judge (the resolution
                                                    panel said resolved, or dream_met says met); the rest classification
                                                    itself never certifies, and NOTHING is written to the memory DB (D-0614:
                                                    the dream arm is shadow-only and "a rest is not a certified close").
  scripts/du_pulse.py                        READ  'resolved / unresolved' counts from ended_unresolved, captioned as a
                                                    test to lift. REST: an added line counts rest / open / met-core and
                                                    what the carry would have returned.
  core/sleep_dream_probe.py                  READ  copies ended_unresolved into a probe row; a label, UNCHANGED.
  core/balance.py, core/tension_ledger.py,
  core/climate_engine.py                     READ  via _bridge_final's shadow / light event sources. UNCHANGED (above).
  idle seed (inner_monologue_node)           READ  state.recent_dreams[0].narrative only (waking_dream_seed); it never
                                                    reads the ending. NOTHING to change (and IMN is not touched).

KINDS (arc_ending): 'met-core' the dreamer's own final unresolved_core is empty; 'rest' the arc arrived at its ending
(close_reason 'resolved' or 'ended-unfaced' -- set only when the close phase or movement 'arrived' ended the loop) and
still names a core; 'open' it did not arrive (stalled / dropped / ceiling) and names a core; 'unknown' no close_reason
(pre-2026-08-22 rows). Only 'rest' changes behaviour; 'open' and 'unknown' keep the legacy carry.

MODE RESTING_ENDING: 'off' = the exact pre-J-3177 behaviour, nothing logged; 'shadow' (default, restart-gated, founder
flips it) = every carry consultation logs what the rest rule WOULD do to data/logs/dream_rest_shadow.jsonl and the carry
is unchanged; 'live' = a rest arc is not returned and carry_thread_root answers 'none' for it. The reader of the shadow
log is scripts/du_pulse.py (the 'dream endings' line) and the flip-decision job J-3177 spawned.

DEFEATER (D-0565): revisit if the carry no longer returns any unfaced arc, or if rest endings crowd out the arcs the
closure writer would certify. The shadow log's would_return rate and the rest_close certified rate are those two readings.

Fail-open everywhere: any failure here leaves the legacy behaviour.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("nascence.dream_rest")

_ROOT = Path(__file__).parent.parent
_DATA = _ROOT / "data"
DREAM_LOG = _DATA / "dream_log.jsonl"                                     # module-level so a test can temp-path them
REST_SHADOW_LOG = _DATA / "logs" / "dream_rest_shadow.jsonl"
RESOLUTION_SHADOW_LOG = _DATA / "logs" / "dream_resolution_shadow.jsonl"   # nodes/dream_node.py writes it (the panel's verdict)

RESTING_ENDING = "shadow"          # off | shadow | live   -- J-3177 / D-0565: shadow first, the founder flips it after the read
# close_reason values that exist only when the arc ARRIVED at its own ending: nodes/dream_node.py sets 'resolved' /
# 'ended-unfaced' at phase == "close" or at movement "arrived" (and the panel may swap the two, D-0580). 'stalled'
# (the arc circled), 'dropped' (a scene failed) and 'ceiling' (ran out) are not endings the dream reached.
ARRIVED_REASONS = ("resolved", "ended-unfaced")
KINDS = ("met-core", "rest", "open", "unknown")

# J-3807 (D-0708 (c), founder 2026-11-09): a rest-ended arc (arrived at its own ending, still names a core) writes a
# LIGHT unresolved_dream event instead of the full one. 'light' = source REST_EVENT_SOURCE, which tension_ledger counts
# as SALIENCE at REST_SALIENCE_WEIGHT of a full event (so some carry of unfinished business stays, D-0229, without full
# tension pressure, D-0565). 'full' = the pre-J-3807 behaviour exactly (source 'unresolved_dream'). RESTART-GATED.
REST_EVENT_MODE = "light"          # full | light
REST_EVENT_SOURCE = "unresolved_dream_rest"
REST_SALIENCE_WEIGHT = 0.3


def rest_event_source(close_reason: str | None, unresolved_core: str) -> str:
    """The shadow-event source _bridge_final should write for an arc ending with this close_reason / core. Pure.
    Only a rest (core non-empty AND the arc arrived: close_reason in ARRIVED_REASONS) goes light; stalled / dropped /
    ceiling / unknown arcs did not arrive and keep 'unresolved_dream'. Mode 'full' -> always 'unresolved_dream'."""
    if REST_EVENT_MODE == "light" and unresolved_core and close_reason in ARRIVED_REASONS:
        return REST_EVENT_SOURCE
    return "unresolved_dream"


def mode() -> str:
    m = RESTING_ENDING
    return m if m in ("shadow", "live") else "off"


def arc_ending(rec: dict) -> str:
    """Classify a dream_log arc record (see KINDS). Pure."""
    if not rec.get("ended_unresolved"):
        return "met-core"
    cr = rec.get("close_reason")
    if not cr:
        return "unknown"
    return "rest" if cr in ARRIVED_REASONS else "open"


def _append(path: Path, row: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    try:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
    except FileNotFoundError:
        pass
    return rows


def carry_returns(rec: dict, *, now: float | None = None) -> bool:
    """Should the carry return this ended-unresolved arc tonight? Called by DreamNode._last_unresolved_arc for an
    arc that the legacy rule already returns (ended_unresolved). 'off' -> True, nothing logged. 'shadow' -> True,
    one row logged saying what 'live' would do. 'live' -> False for a rest arc, True otherwise. Never raises
    (any failure -> True, the legacy carry)."""
    try:
        m = mode()
        if m == "off":
            return True
        kind = arc_ending(rec)
        would_return = kind != "rest"
        _append(REST_SHADOW_LOG, {
            "ts": round(time.time() if now is None else now, 1), "kind": "carry", "mode": m,
            "dream_id": rec.get("dream_id"), "ending": kind, "close_reason": rec.get("close_reason"),
            "carried_n_logged": rec.get("carried_n"), "legacy_returns": True, "would_return": would_return,
            "carry_changed": bool(m == "live" and not would_return)})
        return True if m == "shadow" else would_return
    except Exception as exc:
        logger.debug("[dream_rest] carry_returns failed (non-fatal, legacy carry): %r", exc)
        return True


def is_thread(rec: dict) -> bool:
    """dream_met.carry_thread_root's question: does this last arc leave a carried thread? Legacy = ended_unresolved.
    Only 'live' mode drops a rest arc; shadow / off are exactly the legacy test."""
    if not rec.get("ended_unresolved"):
        return False
    if mode() == "live" and arc_ending(rec) == "rest":
        return False
    return True


def panel_verdict(dream_id: str, path: Path | None = None) -> dict:
    """The independent resolution panel's verdict for one arc, from dream_resolution_shadow.jsonl:
    {'verdict': True|False|None, 'how': str|None} (None = no row / panel unavailable). Pure read."""
    out = {"verdict": None, "how": None}
    for r in _read_jsonl(path or RESOLUTION_SHADOW_LOG):
        if r.get("dream_id") == dream_id:
            out = {"verdict": r.get("judge_verdict"), "how": r.get("judge_how")}
    return out


def summarize(dream_log: Path | None = None, shadow_log: Path | None = None, *, since_ts: float = 0.0) -> dict:
    """For scripts/du_pulse.py: endings of arcs since `since_ts`, and the shadow log's carry consultations."""
    arcs = [r for r in _read_jsonl(dream_log or DREAM_LOG) if (r.get("scenes") or 0) >= 2 and float(r.get("ts") or 0) >= since_ts]
    kinds = {k: 0 for k in KINDS}
    for r in arcs:
        kinds[arc_ending(r)] += 1
    consult = [r for r in _read_jsonl(shadow_log or REST_SHADOW_LOG) if r.get("kind") == "carry" and float(r.get("ts") or 0) >= since_ts]
    return {"mode": mode(), "arcs": len(arcs), "endings": kinds, "consultations": len(consult),
            "would_return": sum(1 for r in consult if r.get("would_return")),
            "would_end": sum(1 for r in consult if not r.get("would_return"))}
