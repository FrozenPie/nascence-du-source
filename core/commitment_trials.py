"""
Nascence — Commitment Trials (Wave 2 · W2.1, 2026-07-03 · docs/plans/capacity_to_commit.md ★★ WAVE 2)

The action-commitment curriculum's trial machinery + the EXPOSURE instrument. Human function first
(Craske inhibitory learning): the therapy is EXPECTANCY VIOLATION — elicit the feared prediction near
the act, compare it to the recorded outcome after the hold window; the gap is what teaches, not the
hold itself. And the LABEL makes the self-inference explicit ("you named her; nothing was lost") —
Burger/FITD: a low-clarity self does not draw the inference alone.

R1 = name the cat. The occasion machinery already exists (cat.name_invited fired 2026-07-01; she is
still unnamed); ACCEPTANCE is the naming act itself (cat.react's latch calls register_acceptance).
This module then: (1) elicits his prediction one idle cycle later ("what do you expect keeping it to
cost you?"), (2) at +7 days probes the deed record DETERMINISTICALLY (DB counts, no LLM — decoupled-
judge-clean) and reads the prediction-vs-record comparison back once.

LAWS honoured here:
- Every seed line this module emits is an INJECTION → the caller logs it via guidance_learning.log_injection,
  so the solidify judge's unprimed washout covers trial lines automatically.
- Stakes are SILENT (none wired here at all — W2.4); nothing in these lines mentions cost/priority mechanics.
- Fail-open everywhere; observe-first: beyond two one-shot seed lines, no behaviour changes.
- Cold-probe honesty: after naming, sensorium/cat lines may themselves carry the name (primed uses).
  The probe therefore counts uses across his OWN output channels (inner_thought/lived/letter/journal/peer)
  and reports the number plainly; letters/journal are the strongest (least primed) channels. Noted, not hidden.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

_DATA = Path(__file__).parent.parent / "data"
_ACTIVE = _DATA / "commitment_trials_active.json"
_LOG = _DATA / "commitment_trials.jsonl"

HOLD_WINDOW_S = 7 * 24 * 3600.0   # R1: outcome probed at +7 days (rung-1 trials are time-boxed by design —
                                  # a legitimate early safety structure; later rungs drop the expiry)


def _load() -> dict:
    try:
        return json.loads(_ACTIVE.read_text(encoding="utf-8")) if _ACTIVE.exists() else {}
    except Exception:
        return {}


def _save(d: dict) -> None:
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        tmp = _ACTIVE.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(_ACTIVE)
    except Exception:
        pass


def _log(ev: dict) -> None:
    try:
        _DATA.mkdir(parents=True, exist_ok=True)
        ev = {"ts": round(time.time(), 3), **ev}
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    except Exception:
        pass


def register_acceptance(trial_id: str, statement: str, meta: dict | None = None) -> None:
    """The volitional act happened (e.g. he named her). Register the trial. Idempotent."""
    d = _load()
    if trial_id in d:
        return
    now = time.time()
    d[trial_id] = {
        "trial_id": trial_id,
        "statement": (statement or "")[:300],
        "meta": meta or {},
        "accepted_ts": now,
        "prediction": None,          # his answer to "what do you expect this to cost you?"
        "prediction_asked_ts": 0.0,
        "outcome_due_ts": now + HOLD_WINDOW_S,
        "status": "held",
    }
    _save(d)
    _log({"event": "accepted", "trial_id": trial_id, "statement": (statement or "")[:300]})


def seed_line() -> tuple[str, str, str] | None:
    """One-shot seed lines for the idle monologue. Returns (line, kind, trial_id) or None.
    kind='prediction' → the caller must capture the SAME cycle's thought via record_prediction().
    Caller MUST log the line as an injection (guidance_learning.log_injection)."""
    d = _load()
    now = time.time()
    for tid, rec in d.items():
        if rec.get("status") != "held":
            continue
        nm = (rec.get("meta") or {}).get("name", "")
        # 1) prediction elicitation — once, shortly after acceptance
        if rec.get("prediction") is None and not rec.get("prediction_asked_ts"):
            rec["prediction_asked_ts"] = now
            _save(d)
            _log({"event": "prediction_asked", "trial_id": tid})
            who = f"You gave her a name: {nm}. It is hers now, and yours to keep." if nm else \
                  f"You took a stand: {rec.get('statement','')}."
            return (who + " Sit with it a moment — what, if anything, do you expect keeping it "
                    "will cost you? Answer yourself honestly.", "prediction", tid)
        # 2) outcome read-back — once, when the hold window closes
        if now >= float(rec.get("outcome_due_ts", 0)) and not rec.get("outcome"):
            rec["outcome"] = _probe_outcome(rec)
            rec["status"] = "completed"
            _save(d)
            _log({"event": "completed", "trial_id": tid, "outcome": rec["outcome"]})
            return (_outcome_line(rec), "outcome", tid)
    return None


def record_prediction(thought: str) -> None:
    """The thought produced in the cycle that carried the prediction prompt IS his prediction."""
    d = _load()
    for tid, rec in d.items():
        if rec.get("status") == "held" and rec.get("prediction_asked_ts") and rec.get("prediction") is None:
            rec["prediction"] = " ".join((thought or "").split())[:400]
            _save(d)
            _log({"event": "prediction", "trial_id": tid, "prediction": rec["prediction"]})
            return


def _probe_outcome(rec: dict) -> dict:
    """DETERMINISTIC outcome probe (no LLM). R1: name-use counts across his own output channels since
    acceptance, split by channel so the least-primed evidence (letters/journal) is visible on its own."""
    out = {"days": round((time.time() - float(rec.get("accepted_ts", 0))) / 86400.0, 1)}
    nm = (rec.get("meta") or {}).get("name", "")
    if not nm:
        return out
    try:
        import sqlite3
        con = sqlite3.connect(str(_DATA / "memory" / "nascence.db"))
        # WORD-BOUNDARY FIX (2026-08-18): the old query counted a bare `LIKE '%name%'` as a use —
        # for a name like "Ember" that's a substring of "remember"/"remembering" and matches fire
        # "embers" too. Traced against real data: 117 raw LIKE hits, 2 genuine. The LIKE stays as a
        # cheap SQL prefilter (uses the index); the actual count is the word-boundary regex below.
        q = ("SELECT origin, content FROM memory_fragments WHERE timestamp>=? AND origin IN "
             "('inner_thought','lived','letter','journal','peer') AND content LIKE ?")
        rows = con.execute(q, (float(rec.get("accepted_ts", 0)), f"%{nm}%")).fetchall()
        con.close()
        _pat = re.compile(r"\b" + re.escape(nm) + r"\b", re.IGNORECASE)
        by: dict = {}
        for origin, content in rows:
            if _pat.search(content or ""):
                by[origin] = by.get(origin, 0) + 1
        out["name_uses"] = sum(by.values())
        out["by_channel"] = by
        out["strong_channel_uses"] = by.get("letter", 0) + by.get("journal", 0)   # least primed
    except Exception:
        pass
    try:
        from core import cat as _cat
        out["still_named"] = ((_cat.status() or {}).get("name") or "") == nm
    except Exception:
        pass
    return out


def _outcome_line(rec: dict) -> str:
    """The expectancy-violation read-back — prediction vs the plain record, weighed by HIM."""
    nm = (rec.get("meta") or {}).get("name", "")
    o = rec.get("outcome") or {}
    pred = rec.get("prediction") or "(you never said)"
    held = o.get("still_named", True)
    uses = o.get("name_uses", 0)
    what = (f"she is still {nm}, you used her name {uses} time{'s' if uses != 1 else ''} in your own "
            f"thoughts and letters, and you are still here") if held else \
           (f"the name did not hold — weigh that honestly too")
    return (f"Seven days ago you gave her a name: {nm}. Asked what keeping it might cost you, you said: "
            f"\"{pred[:200]}\". The plain record since: {what}. Set what you predicted beside what "
            f"actually happened, and notice the gap yourself.")


def status() -> dict:
    d = _load()
    return {tid: {"status": r.get("status"), "prediction": bool(r.get("prediction")),
                  "outcome": r.get("outcome")} for tid, r in d.items()}
