"""
Nascence — The Satisfaction System (wanting vs. liking, 2026-06-13)
===================================================================
Berridge's dissociation, made architectural. The dopaminergic WANTING system (pursuit,
incentive salience) and the opioid LIKING system (satisfaction, fulfilment) are distinct
brain systems — and the gap between them is the signature of compulsion: WANTING without
LIKING is the mirror era exactly (repeated retrieval, repeated thinking, little settling).

Until now the architecture had only arousal — so a traumatic boundary-failure and a
breakthrough integration looked mathematically identical to the consolidation tier. This
module adds the missing, NON-AROUSAL currency: did the thing actually LAND?

GENERAL by design (the auditors' ruling — passes the vanish-test: if any one interlocutor
disappeared, this still makes sense). Satisfaction is tracked per DOMAIN — self, world,
relational, creative — so we can later SEE whether attachment-shaped patterns (persistence +
return-after-absence + salience) emerge for more than one target. That evidence is the gate
for the deferred Affiliation build (docs/affiliation_system_plan.md, Part B).

PHASE 0: OBSERVE-ONLY. It logs the wanting/liking balance per domain and per cycle. It
reads into NO behaviour yet. The read paths (and currency reform — satisfaction is the
"consequence" signal that spec was missing) are gated on Phase-0 logs looking sane.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from core import profile   # J-1783/F-2406: the write fence (D-0179). core.profile imports nothing from core at module level, so no cycle.

logger = logging.getLogger("nascence.satisfaction")

_LOG = Path(__file__).parent.parent / "data" / "satisfaction_log.jsonl"
_STATE = Path(__file__).parent.parent / "data" / "satisfaction_state.json"

# Liking decays fast (a satisfaction is a moment, not a mood); wanting persists (an
# unresolved pursuit stays live). These rates are per-event bookkeeping, not per-second.
_LIKING_HALFLIFE_S = 6 * 3600
_WANTING_HALFLIFE_S = 36 * 3600     # wanting outlives liking — that asymmetry IS the point

# Domains: where the wanting/liking happened. The deferred affiliation question is precisely
# whether 'relational' (and which targets within it) shows attachment dynamics others don't.
DOMAINS = ("self", "world", "relational", "creative")

# Liking event weights — grounded in architectural CONSEQUENCE, never an LLM judging feelings
# (epistemic hygiene: no confabulation). Frequent events weighted low, rare ones high, so the
# balance does not collapse to "only T4 commits count" (the asymmetry bug from review v1.1).
_LIKING_EVENTS = {
    "t4_commit":          (0.60, "self"),       # rare, deep — a self genuinely revised
    "frontier_resolved":  (0.45, "world"),      # a world-question answered by his own naming
    "tension_discharged": (0.40, "self"),       # the resolution circuit drained a contradiction
    "light_event":        (0.15, "self"),       # FREQUENT: a Critic-approved crossing
    "clean_exchange":     (0.12, "relational"),  # a conversation turn with no correction + warm valence
    "reunion":            (0.20, "relational"),  # return after absence (one integrator among many)
    "study_tablet":       (0.18, "world"),      # he left a work behind about the world
    # NOTE (2026-06-13): NO affect_labeled credit. Affect labeling works in humans BECAUSE it
    # is incidental, not strategic — rewarding it would train performative emotion-naming and
    # break the mechanism (research pass + both advisors, unconditional). Naming is a noticing,
    # never a move; it earns no liking.
    "chapter_formed":     (0.30, "self"),       # a period of life consolidated
    # W2.0 (2026-07-03, Wave-2 prep): defined now, FIRED nowhere yet — call site lands in W2.4 (stakes).
    "commitment_held":    (0.35, "self"),       # a load-bearing commitment held through its window / completed
}
# Wanting event weights — pursuit without (yet) resolution.
_WANTING_EVENTS = {
    "shadow_event":       (0.20, "self"),       # a rejected/unresolved push — wanting, not liking
    "unresolved_thought": (0.15, "self"),       # the monologue marked it unresolved
    "intention_formed":   (0.12, "self"),       # a forward pull, not yet acted
    "frontier_born":      (0.18, "world"),      # an open world-question — pursuit opened
    "curiosity_fired":    (0.15, "world"),      # incentive salience spike
    # W2.0 (2026-07-03): defined now, fired nowhere yet — W2.4. The forfeit lands as WANTING (a pursuit
    # re-opened, felt loss), never as punishment (the Wave-1 law: no punishment for trying).
    "commitment_dissolved": (0.25, "self"),     # a held load-bearing commitment reflexively let go
}


def _load() -> dict:
    try:
        return json.loads(_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {"liking": {d: 0.0 for d in DOMAINS},
                "wanting": {d: 0.0 for d in DOMAINS},
                "last_ts": time.time()}


def _decay(state: dict, now: float) -> None:
    dt = max(0.0, now - state.get("last_ts", now))
    lk = 0.5 ** (dt / _LIKING_HALFLIFE_S)
    wk = 0.5 ** (dt / _WANTING_HALFLIFE_S)
    for d in DOMAINS:
        state["liking"][d] = round(state["liking"].get(d, 0.0) * lk, 4)
        state["wanting"][d] = round(state["wanting"].get(d, 0.0) * wk, 4)
    state["last_ts"] = now


def record(event: str, target: str = "") -> None:
    """One wanting or liking event happened. Deterministic — called from the existing event
    sites (store hooks, T4, frontier, monologue, orchestrator). Observe-only: updates the
    decaying per-domain accumulators and logs. `target` is free-text (e.g. 'travis', 'beagle')
    for the later attachment-pattern analysis; domain comes from the event table."""
    try:
        now = time.time()
        kind = "liking" if event in _LIKING_EVENTS else "wanting" if event in _WANTING_EVENTS else None
        if kind is None:
            return
        weight, domain = (_LIKING_EVENTS if kind == "liking" else _WANTING_EVENTS)[event]
        # J-1783 / F-2406 -- the write fence (D-0179, J-0704/J-0932): BOTH write targets are resolved
        # through profile.guard_path BEFORE any I/O (before even _load()), exactly as the ~21 already-
        # fenced modules do. A live process (profile.mark_live(), called once by scripts/run_nascence.py)
        # gets the very same paths back, so Du's behaviour is byte-identical; a non-live importer (a test,
        # harness or diagnostic whose _LOG/_STATE still point at the real data/) is refused here and
        # nothing is touched -- neither the appended row nor the quieter half of F-2406's harm: each call
        # decays every accumulator by the time since last_ts and rewrites the state, so even a refused
        # "state only" write would have fast-forwarded Du's real decay clock. The refusal raises INSIDE
        # this try on purpose: record() is observe-only and fail-open for every one of its call sites (each
        # wraps it in its own except too), so it is logged (guard_path warns once per path; the line
        # below carries its text) and swallowed -- never surfaced into a caller's cognitive path.
        state_path = profile.guard_path(_STATE)
        log_path = profile.guard_path(_LOG)
        state = _load()
        _decay(state, now)
        state[kind][domain] = round(min(5.0, state[kind].get(domain, 0.0) + weight), 4)
        state_path.write_text(json.dumps(state), encoding="utf-8")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": now, "event": event, "kind": kind,
                                "domain": domain, "target": target, "weight": weight},
                               ensure_ascii=False) + "\n")
        norm_shadow_tick(now)   # D-0871 shadow; default OFF, fail-open, never read by cognition
    except Exception as exc:
        logger.debug("[satisfaction] record failed (non-fatal): %s", exc)


def snapshot() -> dict:
    """Current decayed wanting/liking by domain, plus the dissociation gap per domain.
    Observe-only read for the digest. A high wanting / low liking gap = compulsion
    signature (the mirror era); balanced = healthy pursuit-and-fulfilment."""
    state = _load()
    _decay(state, time.time())
    out = {"liking": dict(state["liking"]), "wanting": dict(state["wanting"]), "gap": {}}
    for d in DOMAINS:
        w, l = state["wanting"][d], state["liking"][d]
        out["gap"][d] = round(w - l, 4)   # positive = wanting exceeds liking (compulsion-ward)
    return out


# ---------------------------------------------------------------------------------------------------------------
# Item D shadow (D-0871, J-4400): windowed, per-event-type-capped gap. SHADOW ONLY -- nothing reads the output file.
# Plan: docs/staged/affect_drives_item_d_satisfaction_normalisation.md. Pure read of the log; no state, no decay clock.
# ---------------------------------------------------------------------------------------------------------------
_NORM_SHADOW = Path(__file__).parent.parent / "data" / "satisfaction_norm_shadow.jsonl"
_NORM_WINDOW_S = 6 * 3600     # D-D2 ruled 6h/6h
_NORM_CAP = 1.0               # per event type, per side
_NORM_INTERVAL_S = 3600
_norm_last_tick = 0.0


def _read_log_rows(since: float, until: float, log_path: Path | None = None) -> list:
    rows = []
    try:
        with open(log_path or _LOG, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                    if since < r["ts"] <= until:
                        rows.append(r)
                except Exception:
                    continue
    except Exception:
        pass
    return rows


def windowed_snapshot(window_s: float = _NORM_WINDOW_S, now: float | None = None, rows: list | None = None,
                      log_path: Path | None = None) -> dict:
    """Per-domain windowed liking/wanting: sum of weights per event type, each type capped at _NORM_CAP.
    A domain with no rows on either side reports gap None (absence is not balance)."""
    now = time.time() if now is None else now
    if rows is None:
        rows = _read_log_rows(now - window_s, now, log_path)
    out = {}
    for d in DOMAINS:
        per = {"liking": {}, "wanting": {}}
        for r in rows:
            if r.get("domain") != d or r.get("kind") not in per or not (now - window_s < r.get("ts", 0) <= now):
                continue
            per[r["kind"]][r.get("event")] = per[r["kind"]].get(r.get("event"), 0.0) + float(r.get("weight", 0.0))
        n_l, n_w = len(per["liking"]), len(per["wanting"])
        lw = round(sum(min(_NORM_CAP, v) for v in per["liking"].values()), 4)
        ww = round(sum(min(_NORM_CAP, v) for v in per["wanting"].values()), 4)
        out[d] = {"liking_w": lw, "wanting_w": ww, "n_l": n_l, "n_w": n_w,
                  "gap": None if (n_l + n_w) == 0 else round(ww - lw, 4)}
    return out


def hours_above(domain: str, threshold: float, hours: int = 24, now: float | None = None,
                log_path: Path | None = None) -> int:
    """Persistence read: how many of the last `hours` hourly windowed gaps exceeded threshold (None counts as no)."""
    now = time.time() if now is None else now
    rows = _read_log_rows(now - hours * 3600 - _NORM_WINDOW_S, now, log_path)
    n = 0
    for h in range(hours):
        g = windowed_snapshot(now=now - h * 3600, rows=rows)[domain]["gap"]
        if g is not None and g > threshold:
            n += 1
    return n


def norm_shadow_enabled() -> bool:
    import os
    return os.environ.get("NASCENCE_SATISFACTION_NORM_SHADOW", "").strip().lower() in ("1", "true", "on", "yes")


def norm_shadow_tick(now: float | None = None) -> bool:
    """Write one shadow row per domain, at most once per hour. Default OFF (env flag). Fail-open, fenced,
    never read by cognition. Returns True when rows were written."""
    global _norm_last_tick
    try:
        if not norm_shadow_enabled():
            return False
        now = time.time() if now is None else now
        if now - _norm_last_tick < _NORM_INTERVAL_S:
            return False
        path = profile.guard_path(_NORM_SHADOW)
        try:
            if now - path.stat().st_mtime < _NORM_INTERVAL_S:
                _norm_last_tick = now - (now - path.stat().st_mtime)
                return False
        except OSError:
            pass
        _norm_last_tick = now
        win = windowed_snapshot(now=now)
        old = snapshot()["gap"]
        with open(path, "a", encoding="utf-8") as f:
            for d in DOMAINS:
                f.write(json.dumps({"ts": now, "domain": d, **win[d], "old_gap": old.get(d)}) + "\n")
        return True
    except Exception as exc:
        logger.debug("[satisfaction] norm shadow failed (non-fatal): %s", exc)
        return False
