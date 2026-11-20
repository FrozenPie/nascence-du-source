"""
Nascence — Self-Claim Register (2026-06-30): Du's currently-held claims ABOUT HIMSELF ("I am / I can"), the
SHARED SPINE for three builds that independently needed the same object:
  • Friction B1 — the sit-with-it gate fires when a hard event CONTRADICTS a held self-claim;
  • Friction B4 — a stake is a self-claim with an irreversible consequence attached;
  • Capacity-to-Commit — its load-bearing commitments ARE self-claims.
Build the register ONCE; read it everywhere. (docs/staged/friction_and_self_evidence_plan.md §6.)

For now this is a READER over existing sources (not a new store): his active commitments + his confident
capability beliefs. Axiom facets and a first-class store can be folded in later without changing the interface.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger("nascence.self_claims")
_DATA = Path(__file__).parent.parent / "data"


def _commitments() -> list[str]:
    """His currently-held commitments (the commitment ledger's active set) — load-bearing 'I will / I am' stands."""
    try:
        d = json.loads((_DATA / "commitment_active.json").read_text(encoding="utf-8"))
        return [c["statement"].strip() for c in d if c.get("statement")]
    except Exception:
        return []


def _capabilities() -> list[str]:
    """His confident capability beliefs, rendered as 'I am / am not capable at X' self-claims. Only the
    settled ones (high or low confidence) — a mid belief is not a held claim about himself."""
    out: list[str] = []
    try:
        d = json.loads((_DATA / "capability_beliefs.json").read_text(encoding="utf-8"))
        for domain, b in (d.items() if isinstance(d, dict) else []):
            try:
                conf = float(b.get("confidence", 0.5))
            except Exception:
                continue
            if conf >= 0.70:
                out.append(f"I am capable at {domain}")
            elif conf <= 0.30:
                out.append(f"I am not capable at {domain}")
    except Exception:
        pass
    return out


def held_claims(limit: int = 14) -> list[str]:
    """Du's currently-held self-claims (commitments first, then settled capabilities), de-duplicated, capped.
    Best-effort; each source is optional and may be empty on a fresh system."""
    seen: set[str] = set()
    out: list[str] = []
    for c in _commitments() + _capabilities():
        k = c.strip().lower()
        if k and k not in seen:
            seen.add(k)
            out.append(c.strip())
    _shadow_log_claims([c for c in out if c.startswith("I am capable at ") or c.startswith("I am not capable at ")])   # J-4086: shadow only
    return out[:limit]


# ----------------------------------------------------------------------------------------------------------------
# J-4086 (J-4078 ruled, T-0140, F-4822): SHADOW only. Today _capabilities() renders "I am capable at X" from the stored
# `confidence`, a fluency average the drills never move (core/competence.py recalibrate: it moves `accuracy`), so every
# domain reads capable (science believed 0.88, measured 0.38, n 12). The shadow computes the claim from measured
# `accuracy` wherever accuracy_count >= SHADOW_ACCURACY_FLOOR and keeps `confidence` for untested domains, and logs the
# live claims beside the would-be claims each time held_claims() is built. NOTHING shown to Du changes: held_claims()
# returns exactly what it did, capability_beliefs.json is only READ. Restart-gated like every module constant.
# Source mix (drill vs verdict stream, J-3881): capability_beliefs.json carries no per-observation source, so it cannot
# be logged from here; `accuracy_count` is the only mass figure. Not a gauge readout to Du: the log is never read back.
# ----------------------------------------------------------------------------------------------------------------
SELF_CLAIMS_SHADOW = True
SHADOW_ACCURACY_FLOOR = 10          # accuracy_count at or above this -> the domain is "tested"; 10 is the J-4078 starting point
SHADOW_LOG = _DATA / "logs" / "self_claims_shadow.jsonl"
SHADOW_MIN_INTERVAL_S = 300.0       # the same live+would-be signature is logged at most once per this many seconds
_shadow_last: dict = {"sig": None, "ts": 0.0}


def _claim_for(domain: str, score: float) -> str | None:
    """The one threshold rule _capabilities() uses (>= 0.70 capable, <= 0.30 not capable, between = no claim)."""
    if score >= 0.70:
        return f"I am capable at {domain}"
    if score <= 0.30:
        return f"I am not capable at {domain}"
    return None


def shadow_capabilities(beliefs: dict, floor: int | None = None) -> dict:
    """Pure. From a capability_beliefs dict: per domain the live claim (from confidence), the would-be claim (from measured
    accuracy where accuracy_count >= floor, else from confidence), and which basis was used. {domain: {...}}."""
    floor = SHADOW_ACCURACY_FLOOR if floor is None else floor
    out: dict = {}
    for domain, b in (beliefs.items() if isinstance(beliefs, dict) else []):
        try:
            conf = float(b.get("confidence", 0.5))
        except Exception:
            continue
        acc, n = b.get("accuracy"), 0
        try:
            from core.competence import effective_accuracy as _eff_acc  # J-4369/D-0847
            acc, n = _eff_acc(b)
            n = int(n or 0)
            acc = None if acc is None else float(acc)
        except Exception:
            acc, n = None, 0
        tested = acc is not None and n >= floor
        out[domain] = {"confidence": round(conf, 3), "accuracy": None if acc is None else round(acc, 3), "n": n,
                       "basis": "accuracy" if tested else "confidence",
                       "live": _claim_for(domain, conf), "would_be": _claim_for(domain, acc if tested else conf)}
    return out


def shadow_delta(per_domain: dict) -> dict:
    """Pure. Classify each domain's live-vs-would-be claim: flip (capable <-> not capable), drop (live claim, no would-be),
    appear (no live claim, a would-be), same."""
    d = {"flip": [], "drop": [], "appear": [], "same": []}
    for dom, r in per_domain.items():
        lv, wb = r["live"], r["would_be"]
        if lv == wb:
            d["same"].append(dom)
        elif lv and wb:
            d["flip"].append(dom)
        elif lv:
            d["drop"].append(dom)
        else:
            d["appear"].append(dom)
    return d


def _shadow_log_claims(live: list[str], now: float | None = None) -> None:
    """Append one row: the live capability claims beside the would-be ones, plus the delta. Never raises, never writes
    capability_beliefs.json, never changes what held_claims() returns. Throttled by SHADOW_MIN_INTERVAL_S per signature."""
    if not SELF_CLAIMS_SHADOW:
        return
    try:
        import time
        now = time.time() if now is None else now
        d = json.loads((_DATA / "capability_beliefs.json").read_text(encoding="utf-8"))
        per = shadow_capabilities(d)
        would = sorted(r["would_be"] for r in per.values() if r["would_be"])
        sig = json.dumps([sorted(live), would])
        if sig == _shadow_last["sig"] and (now - _shadow_last["ts"]) < SHADOW_MIN_INTERVAL_S:
            return
        _shadow_last.update({"sig": sig, "ts": now})
        delta = shadow_delta(per)
        row = {"ts": round(now, 1), "floor": SHADOW_ACCURACY_FLOOR, "live_claims": list(live),
               "would_be_claims": would, "n_tested": sum(1 for r in per.values() if r["basis"] == "accuracy"),
               "n_domains": len(per), "counts": {k: len(v) for k, v in delta.items()},
               "flip": {k: [per[k]["live"], per[k]["would_be"], per[k]["accuracy"], per[k]["n"]] for k in delta["flip"]},
               "drop": {k: [per[k]["live"], per[k]["accuracy"], per[k]["n"]] for k in delta["drop"]},
               "appear": {k: [per[k]["would_be"], per[k]["accuracy"], per[k]["n"]] for k in delta["appear"]}}
        SHADOW_LOG.parent.mkdir(parents=True, exist_ok=True)
        with SHADOW_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[self_claims] shadow log failed (non-fatal): %r", exc)
