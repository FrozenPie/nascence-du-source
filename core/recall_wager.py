"""
Nascence — the recall-confidence WAGER (measurement_to_action arm 2; J-2158, 2026-10-15; SHADOW, flag off).

THE GAP. Every responded cycle already gets an epistemic grade (core/epistemic_state.ProvenanceLedger.assess:
KNOW/THINK/SUSPECT/GUESS/NO_BASIS, with `justification = GRADE_SCORE[grade]` and `confabulation_signal =
self_reported_confidence - justification`). Since the 2026-10-09 boot: 95 graded cycles, 94 SUSPECT, and the narrated
recall confidence on those is 0.85/0.92/0.95/0.90 on 87 of 94 — population variance 0.0029 (J-2157). It is a constant,
not a measurement, because nothing happens when it is wrong: the grade is logged to data/provenance_log.jsonl for the
founder and never comes back to Du. The one confidence Du HAS calibrated is maths (prediction gap 0.44 -> 0.21,
F-2853), and the only difference is that the drill's result goes through competence.record_drill_accuracy ->
prediction_error.observe, where a large felt-vs-real gap costs him something.

THE WAGER. This module puts the narrated confidence on the same path the drill uses, with the SAME two calls: when a
cycle's grade is gated (SUSPECT / GUESS / NO_BASIS, the grades the monitor already treats as "cannot back it yet") and
the narrated confidence is at or above CONF_BAR, the pair (predicted = narrated confidence, measured = justification)
is folded into the `factual_recall` belief (data/capability_beliefs.json -- a domain the tracker already owns, with
calib_pairs) and observed by prediction_error (gap >= GAP_THRESHOLD 0.40 -> the contradiction gate -> the chronic-mass
feed when it would pressure). Nothing downstream is new: whatever the drill's large gaps already do, this does.

D-0434 (travis, 2026-10-15): nothing here reaches a prompt, a percept or a preamble. Du is never told the grade; he
can only LOSE the wager, through the same machinery a wrong drill answer already moves. The named risk (plan §2.2): he
may learn a new constant at 0.6. The read-back is the VARIANCE of narrated confidence across grades, not its mean.

SHADOW (RECALL_CONFIDENCE_WAGER = False): every would-be wager is logged to data/logs/recall_wager_shadow.jsonl with
the pair and the gap, and the two calls are NOT made. True: the calls are made and the row says fed=True. The flag
reverts to the exact pre-J-2158 path (assess() already ran; this is one extra call after it, fail-open).
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.recall_wager")

RECALL_CONFIDENCE_WAGER = True    # D-0495 (travis, 2026-10-28, the October restart batch): flipped live, read LIVE by its own read job (90 shadow rows: every one would feed, narrated 0.85-0.95 vs measured 0.5). Plan §2.2 read runs on live rows
CONF_BAR = 0.85                   # the narrated-confidence floor at which an ungrounded claim is a wager, not a guess
# J-4180 (D-0803, 2026-11-17): THE FREE EDGE. measured is the constant 0.5 (GRADE_SCORE[SUSPECT]) and prediction_error loses
# only at gap >= 0.40, so narrating exactly 0.85 (gap 0.35) can NEVER lose: 278/278 wagers at 0.85 cost nothing while
# 176/176 at 0.90-0.95 were lost -- Du found the cheapest "high" and sat on it (274/450 exactly 0.85). The stronger
# channel is the SAME machinery with a lower loss bar for this domain only: a wager at or above CONF_BAR is lost at
# gap >= WAGER_LOSS_GAP (0.30), so 0.85 now costs what 0.92 did. No readout (D-0434): he is never told; the only way
# to stop losing is to state a confidence he can back. False = the exact pre-J-4180 path (threshold 0.40).
WAGER_LOSS_GAP = 0.30
GRADED_LOSS = True
DOMAIN = "factual_recall"         # the existing belief domain (core/competence._DOMAIN_ANCHORS); never a new one
# J-2666 (F-3413): measured = the grade's GRADE_SCORE is a constant (0.5 on all 131 live rows), so the wager cannot be
# won or lost on correctness. With REAL_OUTCOME True the measured side is a correctness outcome in {0,1} from a
# decoupled check (an accuracy_observations row for the SAME cycle_id with source tier3_model / tier4_user, i.e. the
# Phase C witness or the human verdict, never Du's own grade); with none available the wager is NOT fed and the row
# says scorable=False. SHADOW-FIRST: False = the exact pre-J-2666 path (measured = justification, byte-identical).
REAL_OUTCOME = False
OUTCOME_SOURCES = frozenset({"tier3_model", "tier4_user"})
_OBS = Path(__file__).parent.parent / "data" / "accuracy_observations.jsonl"
GATED_GRADES = frozenset({"SUSPECT", "GUESS", "NO_BASIS"})   # mirrors epistemic_state._GATED_GRADES

_SHADOW = Path(__file__).parent.parent / "data" / "logs" / "recall_wager_shadow.jsonl"
# J-4087 (J-3899 ruled 2026-11-16): the outcome also comes from a decoupled per-cycle check of the reply against the
# memory STORE (core/recall_check.py, outcome_source "memcheck_store"), and a SETTLE step feeds a verdict that arrives
# after the wager (a later tier3_model / tier4_user observation for the same cycle_id). Both stay SHADOW while REAL_OUTCOME
# is False: rows carry shadow_* fields and the legacy measured/feed is byte-identical. REAL_OUTCOME stays False until 100
# scored rows exist (J-3613 re-runs the thick-introspection test); the flip to live is a founder call.
# the settle log sits beside the shadow log: data/logs/recall_wager_settle.jsonl
SETTLE_MIN_INTERVAL_S = 120.0
SETTLE_SCAN_ROWS = 600
_last_settle = 0.0


def correctness_outcome(cycle_id: str, obs_path: Path | None = None) -> tuple[float | None, str]:
    """Read-only: the correctness outcome ({0.0,1.0}) a decoupled source logged for this cycle, plus its source tag.
    (None, "") when no external observation for the cycle exists. Latest matching row wins. Never raises."""
    try:
        if not cycle_id:
            return None, ""
        path = Path(obs_path) if obs_path is not None else _OBS
        if not path.exists():
            return None, ""
        found = (None, "")
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if cycle_id not in line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if r.get("cycle_id") == cycle_id and r.get("source") in OUTCOME_SOURCES and r.get("measured") is not None:
                    found = (1.0 if float(r["measured"]) >= 0.5 else 0.0, str(r["source"]))
        return found
    except Exception:
        return None, ""


def _decoupled_outcome(cycle_id: str, output: str, raw_input: str, context_text: str,
                       outcome: float | None, outcome_source: str) -> tuple[float | None, str]:
    """Caller outcome > tier3_model/tier4_user observation for this cycle > memory-store check. (None, "") if none."""
    if outcome is not None:
        return float(outcome), outcome_source or "caller"
    o, src = correctness_outcome(cycle_id)
    if o is not None:
        return o, src
    if output:
        try:
            from core import recall_check as _rc
            res = _rc.check(output, raw_input, context_text)
            if res.get("outcome") is not None:
                return float(res["outcome"]), str(res.get("source") or _rc.SOURCE_TAG)
        except Exception:
            pass
    return None, ""


def place(assessment, *, cycle_id: str = "", input_type: str = "", raw_input: str = "",
          outcome: float | None = None, outcome_source: str = "", output: str = "",
          context_text: str = "") -> dict | None:
    """One call per responded cycle, right after ProvenanceLedger.assess(). Returns the shadow row when the cycle
    was a wager (gated grade AND confidence >= CONF_BAR), else None. Never raises into the cycle."""
    try:
        if assessment is None:
            return None
        grade = str(getattr(assessment, "grade", "") or "")
        conf = float(getattr(assessment, "self_reported_confidence", 0.0) or 0.0)
        just = float(getattr(assessment, "justification", 0.0) or 0.0)
        if grade not in GATED_GRADES or conf < CONF_BAR:
            return None
        scorable = True
        sh_o, sh_src = (None, "")
        if not REAL_OUTCOME:
            sh_o, sh_src = _decoupled_outcome(cycle_id, output, raw_input, context_text, outcome, outcome_source)
        if REAL_OUTCOME:
            outcome, outcome_source = _decoupled_outcome(cycle_id, output, raw_input, context_text, outcome, outcome_source)
            if outcome is None:
                scorable = False
            else:
                just = 1.0 if float(outcome) >= 0.5 else 0.0
        gap = round(abs(conf - just), 3) if scorable else None
        row = {"ts": round(time.time(), 1), "cycle_id": cycle_id, "input_type": input_type, "grade": grade,
               "domain": DOMAIN, "predicted": round(conf, 3), "measured": round(just, 3) if scorable else None,
               "gap": gap, "would_feed": scorable, "fed": False}
        if REAL_OUTCOME:
            row["outcome_source"] = outcome_source if scorable else "none"
            row["scorable"] = scorable
        else:
            # shadow: what the real path WOULD have scored (measured above is still the legacy constant, and fed)
            row["shadow_scorable"] = sh_o is not None
            row["shadow_measured"] = sh_o
            row["shadow_outcome_source"] = sh_src or "none"
            row["shadow_gap"] = round(abs(conf - sh_o), 3) if sh_o is not None else None
        if RECALL_CONFIDENCE_WAGER and scorable:
            # The drill's own path, verbatim: record_drill_accuracy folds the calibration pair into the belief file
            # and calls prediction_error.observe(domain, predicted, measured, event) itself (core/competence.py L89-94).
            from core import competence as _comp
            b = _comp.record_drill_accuracy(DOMAIN, measured=just, predicted=conf,
                                            gap_threshold=WAGER_LOSS_GAP if GRADED_LOSS else None)
            row["graded_loss"] = bool(GRADED_LOSS) and gap is not None and WAGER_LOSS_GAP <= gap < 0.40
            row["fed"] = b is not None
            if b is not None:
                row["accuracy_after"] = b.get("accuracy")
                row["accuracy_count"] = b.get("accuracy_count")
        shadow = profile.guard_path(_SHADOW)
        shadow.parent.mkdir(parents=True, exist_ok=True)
        with open(shadow, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        # J-2527 (measurement_to_action sec.9, I-0105): a LOST wager may become one frontier question (a cup). Own
        # module, own flag (core.wager_curiosity.WAGER_CURIOSITY, shadow False), own log; fail-open, never changes
        # this row or the drill feed above.
        try:
            from core import wager_curiosity as _wc
            if scorable:
                _wc.feed(row, assessment, raw_input)
        except Exception as exc:
            logger.debug("[recall_wager] wager_curiosity failed (non-fatal): %s", exc)
        try:
            settle()                      # J-4087: throttled; logs/feeds verdicts that arrived after their wager
        except Exception as exc:
            logger.debug("[recall_wager] settle failed (non-fatal): %s", exc)
        return row
    except profile.NonLiveWriteError as exc:
        logger.debug("[recall_wager] refused (non-fatal): %s", exc)
        return None
    except Exception as exc:
        logger.debug("[recall_wager] place failed (non-fatal): %s", exc)
        return None


def _obs_verdicts(obs_path: Path) -> dict:
    """cycle_id -> (outcome, source) for tier3_model / tier4_user rows, latest wins. One pass over the file."""
    out: dict = {}
    if not obs_path.exists():
        return out
    with open(obs_path, encoding="utf-8") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except Exception:
                continue
            cid = r.get("cycle_id")
            if cid and r.get("source") in OUTCOME_SOURCES and r.get("measured") is not None:
                out[cid] = (1.0 if float(r["measured"]) >= 0.5 else 0.0, str(r["source"]))
    return out


def settle(*, obs_path: Path | None = None, shadow_path: Path | None = None, settle_path: Path | None = None,
           now: float | None = None, force: bool = False) -> list[dict]:
    """The settle step (J-4087). For wager rows with no external verdict at placement (outcome source not tier3_model /
    tier4_user), look for a verdict that has arrived since for the same cycle_id; write one row per cycle to the settle
    log (idempotent) and, only when REAL_OUTCOME and RECALL_CONFIDENCE_WAGER are on and the wager was not already fed
    with a real outcome, feed it through the same record_drill_accuracy call. Throttled. Never raises."""
    global _last_settle
    try:
        now = time.time() if now is None else now
        if not force and now - _last_settle < SETTLE_MIN_INTERVAL_S:
            return []
        _last_settle = now
        obs = Path(obs_path) if obs_path is not None else _OBS
        shadow = Path(shadow_path) if shadow_path is not None else _SHADOW
        sp = Path(settle_path) if settle_path is not None else shadow.with_name("recall_wager_settle.jsonl")
        verdicts = _obs_verdicts(obs)
        if not verdicts or not shadow.exists():
            return []
        from core.shadow_log import tail_rows as _tail
        rows = _tail(shadow, SETTLE_SCAN_ROWS)
        done: set = set()
        if sp.exists():
            with open(sp, encoding="utf-8") as fh:
                for line in fh:
                    try:
                        done.add(json.loads(line).get("cycle_id"))
                    except Exception:
                        continue
        written: list[dict] = []
        for r in rows:
            cid = r.get("cycle_id")
            if not cid or cid in done or cid not in verdicts:
                continue
            if r.get("outcome_source") in OUTCOME_SOURCES or r.get("shadow_outcome_source") in OUTCOME_SOURCES:
                continue                  # already scored by an external verdict at placement
            o, src = verdicts[cid]
            conf = float(r.get("predicted") or 0.0)
            srow = {"ts": round(now, 1), "cycle_id": cid, "domain": DOMAIN, "predicted": round(conf, 3),
                    "measured": o, "gap": round(abs(conf - o), 3), "outcome_source": src, "settled_late": True,
                    "placed_ts": r.get("ts"),
                    "placed_outcome_source": r.get("outcome_source") or r.get("shadow_outcome_source") or "none",
                    "fed": False}
            if REAL_OUTCOME and RECALL_CONFIDENCE_WAGER:
                if r.get("fed") and r.get("scorable"):
                    srow["superseded_fed"] = True      # already fed with a memcheck outcome: logged, not double-fed
                else:
                    from core import competence as _comp
                    b = _comp.record_drill_accuracy(DOMAIN, measured=o, predicted=conf)
                    srow["fed"] = b is not None
            guarded = profile.guard_path(sp)
            guarded.parent.mkdir(parents=True, exist_ok=True)
            with open(guarded, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(srow, ensure_ascii=False) + "\n")
            done.add(cid)
            written.append(srow)
        return written
    except profile.NonLiveWriteError as exc:
        logger.debug("[recall_wager] settle refused (non-fatal): %s", exc)
        return []
    except Exception as exc:
        logger.debug("[recall_wager] settle failed (non-fatal): %s", exc)
        return []


def status() -> dict:
    """For the pulse/HUD: counts over the last 2000 shadow rows."""
    try:
        from core.shadow_log import tail_rows as _tail
        rows = _tail(_SHADOW, 2000)
    except Exception:
        rows = []
    large = [r for r in rows if (r.get("gap") or 0) >= 0.40]
    return {"flag": RECALL_CONFIDENCE_WAGER, "wagers": len(rows), "fed": sum(1 for r in rows if r.get("fed")),
            "large_gap": len(large),
            "unscorable": sum(1 for r in rows if r.get("scorable") is False),
            "shadow_scored": sum(1 for r in rows if r.get("shadow_scorable")),   # J-4087: need 100 before J-3613
            "last_ts": rows[-1]["ts"] if rows else None}
