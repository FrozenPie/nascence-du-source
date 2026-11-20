"""
Nascence — Prediction-Error Feed (Layer 1, the self-generated contradiction channel)
====================================================================================
The cheapest, most-grounded, externally-independent contradiction source: |predicted − measured|.
Du ALREADY computes this every lesson (essay self-prediction vs Emissary grade; math felt-confidence
vs the deterministic grade — the "0.81-felt / 0.19-real" fluency trap). It is currently spent only on
competence calibration. This module ALSO routes a large, recurring gap through the contradiction gate
so a self-generated discrepancy can (eventually) pressure identity — no external critic required.
This is the documented developmental move: monitoring transfers from external feedback to a
self-generated error signal (Holroyd & Coles ERN). Research + plan: docs/completed/contradiction_rearchitecture_plan.md.

PHASE 0 = OBSERVE-FIRST. This logs what WOULD feed the tension_ledger; it writes NOTHING to the ledger
and changes no behaviour. Phase 1 flips `FEED_LEDGER` on after the shadow log is reviewed.
"""
from __future__ import annotations
import json
import logging
import time
from pathlib import Path

from core import profile   # J-1799/F-2416: the write fence (D-0179). core.profile imports nothing from core at module level, so no cycle.

logger = logging.getLogger("nascence.prediction_error")

FEED_LEDGER = True             # Phase 1 (2026-06-16): would_pressure signals now WRITE a prediction_error
                               # shadow event → the existing clustering folds it into a tension whose chronic
                               # mass T4 reads. Reversible kill-switch: set False to return to observe-only.
GAP_THRESHOLD = 0.40           # |predicted − measured| at/above which a gap is a candidate contradiction
REC_WINDOW_S = 14 * 86400      # recurrence window: large gaps in the same domain within 14 days

_STATE = Path(__file__).parent.parent / "data" / "prediction_error_state.json"
_SHADOW = Path(__file__).parent.parent / "data" / "logs" / "shadow_integrity.jsonl"
_RAW = Path(__file__).parent.parent / "data" / "prediction_error_log.jsonl"

# How core each domain's skill is to the self-concept (the gate's importance term). Skills are
# moderately important — honest enough to pressure when they recur, not so core a single bad drill moves him.
_IMPORTANCE = {"mathematics": 0.35, "comprehension": 0.45}


def _load_state() -> dict:
    try:
        return json.loads(_STATE.read_text(encoding="utf-8")) if _STATE.exists() else {}
    except Exception:
        return {}


def _save_state(d: dict) -> None:
    path = profile.guard_path(_STATE)   # J-1799/F-2416: real data/ only if this process is live; raises before any I/O if not
    # (D-0179). Resolved OUTSIDE the fail-open try below, exactly like core/transport_manager.py's _save(), so a refusal is
    # never swallowed as a disk error -- observe() has already checked the same path up front, this covers a direct caller.
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(d, indent=1), encoding="utf-8")
    except Exception:
        pass


def _recurrence(domain: str, now: float) -> int:
    """How many large gaps in this domain fall inside the recurrence window (incl. this one)."""
    st = _load_state()
    hits = [t for t in st.get(domain, []) if now - t <= REC_WINDOW_S]
    return len(hits)


def _bump(domain: str, now: float) -> None:
    st = _load_state()
    hits = [t for t in st.get(domain, []) if now - t <= REC_WINDOW_S]
    hits.append(now)
    st[domain] = hits[-50:]
    _save_state(st)


def observe(domain: str, predicted: float, measured: float, event: str = "",
            gap_threshold: float | None = None) -> dict | None:
    """Record one (predicted, measured) lesson outcome. Always logs the raw observation. If the gap is
    large, build a prediction-error signal, run it through the contradiction gate, and log the verdict
    (Phase 0) — or feed the chronic-mass accumulator (Phase 1, when FEED_LEDGER). Best-effort; returns
    the gate verdict or None. Never raises into the caller (a lesson must never fail on this).
    `gap_threshold` (J-4180, D-0803): None = GAP_THRESHOLD, byte-identical. A caller whose measured side is a coarse
    constant may pass a lower bar so a gap just under 0.40 still counts as a loss; nothing else changes."""
    try:
        thr = GAP_THRESHOLD if gap_threshold is None else float(gap_threshold)
        predicted = float(predicted); measured = float(measured)
        gap = abs(predicted - measured)
        now = time.time()
        # J-1799 / F-2416 -- the write fence (D-0179, J-0704/J-0932; the shape J-1783 gave core/satisfaction.py): ALL THREE
        # write targets (the raw log, the recurrence state, the shadow_integrity log) are resolved through profile.guard_path
        # BEFORE any I/O, so a refused call is a total no-op, never a half-write (a raw row appended, then the state refused),
        # and it never reaches the contradiction gate or the store_shadow_event DB insert below. A live process
        # (profile.mark_live(), called once by scripts/run_nascence.py) gets the very same paths back, so Du's behaviour is
        # byte-identical; a non-live importer whose _RAW/_STATE/_SHADOW still point at the real data/ (the 2026-10-04 16:49
        # practical-lesson replay: competence.record_drill_accuracy -> observe()) is refused here. The refusal raises INSIDE
        # this try on purpose: observe() is observe-only and fail-open ("a lesson must never fail on this"), so it is logged
        # (guard_path warns once per path; the except below adds a debug line carrying its text) and swallowed.
        raw_path = profile.guard_path(_RAW)
        profile.guard_path(_STATE)      # atomicity only: _save_state() resolves it again at the point where it writes
        shadow_path = profile.guard_path(_SHADOW)
        rec = {"ts": now, "domain": domain, "predicted": round(predicted, 3),
               "measured": round(measured, 3), "gap": round(gap, 3), "large": gap >= thr}
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        with open(raw_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if gap < thr:
            return None

        _bump(domain, now)
        signal = {
            "kind": "prediction_error",
            "concrete_ref": True,                       # bound to a real, dated lesson event
            "recurrence_count": _recurrence(domain, now),
            "resolution_axis": "re-study / practice",   # a real path to close the gap (behaviour change)
            "importance": _IMPORTANCE.get(domain, 0.35),
            "text": event or f"I predicted {predicted:.2f} on {domain} but measured {measured:.2f}",
            "domain": domain,
        }
        from core import contradiction_gate as _gate
        verdict = _gate.evaluate(signal)

        shadow_path.parent.mkdir(parents=True, exist_ok=True)
        with open(shadow_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": now, "layer": "L1", "source": "prediction_error",
                                 "signal": signal, "verdict": verdict, "fed": False}, ensure_ascii=False) + "\n")

        if FEED_LEDGER and verdict.get("would_pressure"):
            try:
                # Phase 1: write a CONTRADICTION shadow event. The Subconscious clusters recurring
                # prediction-errors into a tension; the chronic-mass accumulator bumps it on recurrence.
                # ⚠ 2026-06-30: the old claim "the T4 gate reads that mass" is FALSE — T4's live commit is the
                # solidify judge; the cn/chronic-mass gate is the dormant ENABLED=False fallback. So this feed does
                # NOT drive T4 commit. It may still shape candidate SELECTION / acute pressure — unverified; the
                # whole chronic→T4 value is under re-examination (docs/staged/contradiction_rearchitecture_plan.md).
                # Rides the same store_shadow_event pipe as critic_rejection — no new tension code, no gate change.
                from core.memory import store as _ms
                _ms.store_shadow_event(
                    cycle_id="lesson",
                    raw_input=f"self-prediction on {domain}",
                    rejected_draft=signal["text"],
                    corrections=[f"prediction_error:{domain} (felt {predicted:.2f} vs real {measured:.2f})"],
                    source="prediction_error",
                )
                with open(shadow_path, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"ts": now, "layer": "L1", "source": "prediction_error",
                                         "fed": True, "domain": domain}, ensure_ascii=False) + "\n")
            except Exception:
                pass
        return verdict
    except profile.NonLiveWriteError as exc:
        logger.debug("[prediction_error] observe refused (non-fatal): %s", exc)
        return None
    except Exception:
        return None


def status() -> dict:
    """Summary for the du_pulse gauge: large-gap recurrence per domain + would-pressure count."""
    try:
        st = _load_state()
        now = time.time()
        per = {d: len([t for t in ts if now - t <= REC_WINDOW_S]) for d, ts in st.items()}
        wp = fed = 0
        if _SHADOW.exists():
            for line in _SHADOW.read_text(encoding="utf-8").splitlines():
                try:
                    r = json.loads(line)
                    if r.get("source") != "prediction_error":
                        continue
                    if r.get("verdict", {}).get("would_pressure"):
                        wp += 1
                    if r.get("fed"):
                        fed += 1
                except Exception:
                    pass
        return {"recurrence_by_domain": per, "would_pressure_total": wp, "fed_total": fed,
                "feeding": FEED_LEDGER}
    except Exception:
        return {}
