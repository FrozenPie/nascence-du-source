"""
Nascence — Opponent-Process Antagonist Field ("squishy springs", cognitive_geometry.md §11, P3b —
2026-08-19). PHASE 0 = SHADOW/observe-only. Nothing here is read by any live path; this instrument
exists to gather the evidence the open decisions in §11 need (activation-unit definition, the asymmetry
ratio, per-spring vs per-node pooling) before any of it goes live.

THE MECHANISM (full derivation: docs/plans/cognitive_geometry.md §11). A spring's earned weight `w`
(memory_edges.weight) is LAW-protected — §1, never touched here. This module tracks a SEPARATE,
fully-reversible antagonist `b` per co-activating pair: felt pull would eventually be `max(0, w - b)`,
but this instrument only computes `b`'s own trajectory — pairing it against a real `w` is P3 proper
(the spring ledger itself), not yet built, and out of scope here. Solomon & Corbit 1974/1980, NOT Koob &
Le Moal's allostasis extension: `b` decays FULLY to zero given enough quiet — no permanent baseline
drift (§11 records why that version was rejected: never formalized even by its own author, and the best
2025 human test of its core prediction found the opposite result).

ACTIVATION = one co-recall event for a pair — deliberately reuses `memory_edges.log_co_recall()`'s own
unit rather than inventing a new one. Wired as a sibling call from there (see memory_edges.py), which
means every one of M1's 9 sources feeds this for free with zero new call sites.

PROGRESS = the same `developed` gate M1 already computes (restate ∈ [0.40, 0.82) = a genuine deepen, not
a near-duplicate). §7's calcification law — strengthen on co-activation × PROGRESS, not mere circling —
applies here too: a bare co-occurrence grows `b` at a fraction of what a judged deepen does.

SIGN = the mood valence at the moment of activation (aversive / positive / neutral). This is the one
place real evidence should set an asymmetric parameter rather than a guess: aversive-offset rebound is
well-documented, positive-offset mostly isn't, so aversive activation grows `b` faster, to a higher
ceiling, and decays slower than positive activation does.
"""
from __future__ import annotations

import json
import logging
import math
import threading
import time
from itertools import combinations
from pathlib import Path

from core import store_persist as _sp

logger = logging.getLogger("nascence.opponent_process")

_DATA = Path(__file__).parent.parent / "data"
_STATE = _DATA / "opponent_process_state.json"
_LOG = _DATA / "opponent_process_shadow.jsonl"

# ── tunables (Phase 0 exists to find the right values from real data; all cheap to change, none live) ──
GROWTH_STEP = {"aversive": 0.14, "positive": 0.07, "neutral": 0.03}   # per-activation step (pre-ceiling)
GROWTH_STEP_RESTATE_MULT = 0.35     # a bare co-occurrence (not a judged deepen) grows b at this fraction
CEILING = {"aversive": 1.0, "positive": 0.55, "neutral": 0.30}       # asymmetric asymptote
DECAY_TAU_S = {"aversive": 6 * 3600.0, "positive": 2 * 3600.0, "neutral": 3 * 3600.0}  # aversive lingers
VALENCE_AVERSIVE_BELOW = -0.05
VALENCE_POSITIVE_ABOVE = 0.05
PAIR_CAP = 24                # a 12-id co-recall row is 66 pairs; cap for cost (same spirit as the M1 caps)
PRUNE_BELOW = 0.01           # entries decayed under this AND quiet a long while get dropped (state hygiene)
PRUNE_IDLE_S = 14 * 86400.0


# J-2418 (F-3118): the state dict stays in-process and is written at most once per SAVE_MIN_INTERVAL_S (and at
# exit), instead of re-parsed + rewritten whole on every co-recall. SAVE_MIN_INTERVAL_S = 0 restores
# write-every-event (kill switch; tests that read the file right after a call set it to 0).
SAVE_MIN_INTERVAL_S = 60.0
_STORE = _sp.CoalescedJsonStore("opponent_process", logger)
_OBSERVE_LOCK = threading.RLock()


def _read_disk(path: Path) -> dict:
    try:
        if not path.exists():
            return {}
        from core import profile
        # J-4426 (F-5128): a damaged file is logged and falls back to <name>.prev before {}.
        return _sp.read_json_durable(path, "opponent_process", logger, guard=profile.guard_path)
    except Exception as exc:
        logger.debug("[opponent_process] state load failed (non-fatal): %s", exc)
        return {}


def _load() -> dict:
    return _STORE.load(_STATE, _read_disk)


def _write_now(path: Path, d: dict) -> bool:
    try:
        from core import profile
        state_path = profile.guard_path(path)   # J-2180/F-2883: fenced (D-0179) -- a non-live, non-isolate()d process is refused here, swallowed by the fail-open net
        state_path.parent.mkdir(parents=True, exist_ok=True)
        _sp.write_text_durable(state_path, json.dumps(d, ensure_ascii=False))   # J-4426: fsync + .prev
        return True
    except Exception as exc:
        logger.debug("[opponent_process] state save failed (non-fatal): %s", exc)
        return False


def _save(d: dict) -> None:
    _STORE.save(_STATE, d, _write_now, SAVE_MIN_INTERVAL_S)


def flush() -> None:
    """Write any deferred state now (also runs at interpreter exit)."""
    _STORE.flush(_STATE)


def _log(rec: dict) -> None:
    try:
        from core import profile
        log_path = profile.guard_path(_LOG)   # J-2180/F-2883: fenced (D-0179) -- a non-live, non-isolate()d process is refused here, swallowed by the fail-open net
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _skip(reason: str, **detail) -> None:
    """Every early return LOGS WHY (the reentry.py lesson: a shadow log that can go silent for weeks
    behind a bare `None` is a broken instrument, not a quiet one)."""
    _log({"ts": round(time.time(), 1), "skip": reason, **detail})


def _sign(valence) -> str:
    if valence is None:
        return "neutral"
    v = float(valence)
    if v <= VALENCE_AVERSIVE_BELOW:
        return "aversive"
    if v >= VALENCE_POSITIVE_ABOVE:
        return "positive"
    return "neutral"


def observe_activation(*args, **kwargs):
    """Serialised (J-2418): the state dict is now shared in-process, so concurrent callers must not interleave."""
    with _OBSERVE_LOCK:
        return _observe_activation_unlocked(*args, **kwargs)


def _observe_activation_unlocked(fragment_ids: list, developed, valence=None, ts: float | None = None,
                        source: str = "") -> list[dict]:
    """One co-recall event → one growth/decay tick for every pair in `fragment_ids` (capped). Additive,
    fail-open: reads/writes only this module's own state file + shadow log, touches nothing else.
    Returns the event rows (empty list on any skip/error) — useful for tests, ignored by real callers."""
    try:
        ids = sorted(dict.fromkeys(str(i) for i in (fragment_ids or []) if i))
        if len(ids) < 2:
            _skip("fewer-than-2-ids", n_ids=len(fragment_ids or []))
            return []
        pairs = list(combinations(ids, 2))[:PAIR_CAP]
        now = ts if ts is not None else time.time()
        sign = _sign(valence)
        has_progress_signal = developed is not None
        progress = bool(developed)
        state = _load()
        out = []
        for a, b_id in pairs:
            key = f"{a[:12]}|{b_id[:12]}"
            rec = state.get(key) or {"b": 0.0, "n": 0, "born": now, "last_ts": now}
            b_prev = float(rec.get("b", 0.0))
            gap = max(0.0, now - float(rec.get("last_ts", now)))
            b_decayed = b_prev * math.exp(-gap / DECAY_TAU_S[sign])
            step = GROWTH_STEP[sign] * (1.0 if (not has_progress_signal or progress)
                                         else GROWTH_STEP_RESTATE_MULT)
            b_after = min(CEILING[sign], b_decayed + step)
            rec.update(b=round(b_after, 5), n=rec.get("n", 0) + 1, last_ts=now, sign_last=sign)
            state[key] = rec
            row = {"ts": round(now, 1), "key": key, "sign": sign, "progress": progress,
                   "has_progress_signal": has_progress_signal, "source": source[:40],
                   "gap_s": round(gap, 1), "b_prev": round(b_prev, 5),
                   "b_decayed": round(b_decayed, 5), "b_after": round(b_after, 5),
                   "activation_n": rec["n"]}
            _log(row)
            out.append(row)
        stale = [k for k, v in state.items()
                 if v.get("b", 0.0) < PRUNE_BELOW and (now - float(v.get("last_ts", now))) > PRUNE_IDLE_S]
        for k in stale:
            state.pop(k, None)
        _save(state)
        return out
    except Exception as exc:
        logger.debug("[opponent_process] observe_activation failed (non-fatal): %s", exc)
        return []


def status() -> dict:
    """For the pulse: coverage + the asymmetry read — the §11 open question this shadow data answers."""
    try:
        from core.shadow_log import tail_rows as _tail_rows
        # Bounded tail read (J-0278/F-0335): was a full scan of the 2.2MB+ growing log on every ~6s
        # HUD poll. "activations"/"skips" now cap at the window; the stats use live[-3000:].
        rows = _tail_rows(_LOG, 4000)
    except Exception:
        return {"activations": 0}
    live = [r for r in rows if "skip" not in r]
    if not live:
        return {"activations": 0, "skips": len(rows)}
    recent = live[-3000:]
    by_sign: dict = {}
    for r in recent:
        s = by_sign.setdefault(r["sign"], {"n": 0, "b_sum": 0.0, "max_b": 0.0})
        s["n"] += 1
        s["b_sum"] += r["b_after"]
        s["max_b"] = max(s["max_b"], r["b_after"])
    state = _load()
    top = sorted(({"key": k, "b": v.get("b", 0.0), "n": v.get("n", 0), "sign": v.get("sign_last")}
                  for k, v in state.items()), key=lambda x: -x["b"])[:8]
    return {
        "activations": len(live), "skips": len(rows) - len(live), "tracked_pairs": len(state),
        "by_sign": {s: {"n": v["n"], "mean_b": round(v["b_sum"] / v["n"], 4), "max_b": round(v["max_b"], 4)}
                    for s, v in by_sign.items()},
        "top_b": top,
    }
