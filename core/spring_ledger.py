"""
Nascence — THE SPRING LEDGER, P3 shadow (cognitive_geometry.md §6's P3 build-order requirement, at the
memory level via memory_multiway_linking.md §4's `co_recalled_developing`/`contradicts` edge type;
D-0051, ruled 2026-09-13). PHASE 0 = SHADOW/observe-only. Computes TWO candidate learning rules side by
side over the same real co-recall stream — naive Hebbian-with-decay (nudges on every co-occurrence) vs
progress-gated (nudges only when the ledger's own `developed==1` verdict fires) — per cognitive_geometry
.md §6's own wording: "from accrued tuples compute BOTH candidate learning rules side-by-side."

Mirrors core/opponent_process.py's own established shape exactly (same hook, same JSON-state-file +
shadow-jsonl-log pattern, same PAIR_CAP/fail-open discipline) — that module already proved this pattern
out for the sibling antagonist field `b`; this is the spring weight `w` side of the same mechanism, kept
in a SEPARATE store (§7's own required separation: `w` is slow/structural, `b` is fast/reversible).

This module IS that weight, in shadow — see the plan this was built from, the "P3 — The Spring Ledger"
design doc (metric sheet: hub concentration, weight-distribution spread, absolute magnitude, valence
asymmetry, and the calcification gate itself).

UPDATE (D-0215, ruled 2026-09-25, F-1901): the founder's own gate passed — the pre-registered ceiling
test (F-1316/F-1901) crossed n_backed>=14 (9->27) with REAL_POSITIVE evidence (mean diff +0.1312, 95%
CI [+0.0819,+0.1836], excludes 0; survives a fragment-dedup robustness check). `observe_co_recall()`
below now ALSO writes a real `(fragment)-[co_recalled_developing]->(fragment)` row into
`core.memory_edges` — via `add_edge()`, still `INSERT OR IGNORE`, so it still cannot NUDGE a stored
weight; a live edge is a snapshot fact, not a live-updated value — the FIRST time a pair's own
`w_gated` clears `LIVE_EDGE_THRESHOLD` (0.3, F-1316's own ceiling-test bar). This fires ONLY on the one
real call site that opts in (`live_edges=True`, wired from `core/memory_edges.py`'s own
`log_co_recall()`); every other caller — in particular `scripts/spring_ledger_backfill.py`'s replay,
which never passes `live_edges` — keeps the pre-D-0215 default (`live_edges=False`) and so still
"never touches memory_edges" exactly as that script's own docstring promises. The naive-vs-gated
SHADOW computation itself (below) is completely unchanged either way. See `LIVE_EDGE_WRITE` /
`LIVE_EDGE_THRESHOLD` just below the tunables for the kill-switch and the bar.

ACTIVATION = one co-recall event for a pair — the SAME unit `opponent_process.py` already uses (reuses
`memory_edges.log_co_recall()`'s own unit, wired as a sibling call from there).

PROGRESS = the ledger's own `developed` field (1 = a genuine deepen, 0.40<=restate_sim<0.82; 0 or None
otherwise) — gates `w_gated`'s nudge, never `w_naive`'s (the whole point of the comparison).

SIGN = mood valence at activation time, reusing `opponent_process._sign()`'s exact thresholds so both
mechanisms agree on what counts as aversive/positive/neutral.

DECAY = exponential, tau on the order of WEEKS (not opponent_process's hours) — `w` is meant to be
earned, structural memory, not a fast-reversible mood-adjacent antagonist (§7's own required
distinction). Growth step is IDENTICAL for both naive and gated rules, so any difference in accrued
weight isolates the effect of gating itself, not a confound from different step sizes.
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

from core.opponent_process import _sign

logger = logging.getLogger("nascence.spring_ledger")

_DATA = Path(__file__).parent.parent / "data"
_STATE = _DATA / "spring_ledger_state.json"
_LOG = _DATA / "spring_ledger_shadow.jsonl"

# ── tunables (Phase 0 exists to find the right values from real data; all cheap to change, none live) ──
GROWTH_STEP = {"aversive": 0.12, "positive": 0.07, "neutral": 0.04}   # identical for naive AND gated --
                                                                       # isolates the gating effect itself
CEILING = 1.0                        # both rules share a ceiling -- keeps weight interpretable as 0-1
DECAY_TAU_S = {"aversive": 21 * 86400.0, "positive": 10 * 86400.0, "neutral": 14 * 86400.0}  # weeks-scale,
                                                                       # slow/structural (§7), asymmetric
PAIR_CAP = 24                # same cap/spirit as opponent_process and M1's own caps
PRUNE_BELOW = 0.01
PRUNE_IDLE_S = 60 * 86400.0  # springs are meant to be long-lived; prune only genuinely abandoned pairs

# ── D-0215 (ruled 2026-09-25): shadow -> live graduation for co_recalled_developing ─────────────────
LIVE_EDGE_WRITE = True        # kill-switch -- flip False to disable the live memory_edges write
                               # entirely, without a code revert, if D-0215's own defeater fires
LIVE_EDGE_THRESHOLD = 0.3     # F-1316's own ceiling-test bar (== scripts/spring_ledger_reflective_
                               # ceiling_test.py's SPRING_THRESHOLD); do not change without a fresh /decide


# J-2418 (F-3118): the state dict stays in-process and is written at most once per SAVE_MIN_INTERVAL_S (and at
# exit), instead of re-parsed + rewritten whole on every co-recall. SAVE_MIN_INTERVAL_S = 0 restores
# write-every-event (kill switch; tests that read the file right after a call set it to 0).
SAVE_MIN_INTERVAL_S = 60.0
_STORE = _sp.CoalescedJsonStore("spring_ledger", logger)
_OBSERVE_LOCK = threading.RLock()


def _read_disk(path: Path) -> dict:
    try:
        if not path.exists():
            return {}
        from core import profile
        # J-4426 (F-5128): a damaged file is logged and falls back to <name>.prev before {}.
        return _sp.read_json_durable(path, "spring_ledger", logger, guard=profile.guard_path)
    except Exception as exc:
        logger.debug("[spring_ledger] state load failed (non-fatal): %s", exc)
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
        logger.debug("[spring_ledger] state save failed (non-fatal): %s", exc)
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
    """Every early return LOGS WHY (the reentry.py lesson, already applied once in opponent_process.py:
    a shadow log that can go silent for weeks behind a bare None is a broken instrument, not a quiet
    one)."""
    _log({"ts": round(time.time(), 1), "skip": reason, **detail})


def _write_live_edge(src_id: str, dst_id: str, weight: float, source: str) -> None:
    """D-0215 (ruled 2026-09-25, F-1901): once a pair's gated weight clears LIVE_EDGE_THRESHOLD, write
    the real `(fragment)-[co_recalled_developing]->(fragment)` edge into core.memory_edges -- the
    actual shadow-to-live graduation. Fail-open (never raises into observe_co_recall's own loop);
    `add_edge()` is `INSERT OR IGNORE` (core/memory_edges.py's own
    `UNIQUE(src_kind, src_id, dst_kind, dst_id, edge_type)` constraint), so a pair that keeps clearing
    the bar on later ticks is a harmless no-op, not a duplicate or an overwrite -- the same idempotency
    discipline `sync_resolves()` and the dream_node forward hooks in that file already rely on.
    `weight` is the rounded w_gated value at the moment this tick cleared the bar -- a snapshot, not a
    live-updated one: memory_edges rows are immutable facts, the ADAPTIVE weight keeps living here, in
    this module's own decaying state. Deferred import of core.memory_edges, matching that module's own
    deferred import of THIS module inside log_co_recall() -- avoids any import-order coupling."""
    try:
        from core import memory_edges as _edges
        _edges.add_edge("fragment", src_id, "fragment", dst_id, "co_recalled_developing",
                         weight=weight,
                         provenance=f"spring_ledger w_gated>={LIVE_EDGE_THRESHOLD} source={(source or '')[:60]}")
    except Exception as exc:
        logger.debug("[spring_ledger] live co_recalled_developing write failed (non-fatal): %s", exc)


def observe_co_recall(*args, **kwargs):
    """Serialised (J-2418): the state dict is now shared in-process, so concurrent callers must not interleave."""
    with _OBSERVE_LOCK:
        return _observe_co_recall_unlocked(*args, **kwargs)


def _observe_co_recall_unlocked(fragment_ids: list, developed, valence=None, ts: float | None = None,
                       source: str = "", live_edges: bool = False) -> list[dict]:
    """One co-recall event -> one naive+gated growth/decay tick for every pair in `fragment_ids`
    (capped). Additive, fail-open: reads/writes only this module's own state file + shadow log, plus
    (ONLY when `live_edges=True` -- see D-0215 above) a real `memory_edges` row per pair that clears
    LIVE_EDGE_THRESHOLD. `live_edges` defaults to False so every pre-existing caller (in particular
    scripts/spring_ledger_backfill.py's replay) is completely unaffected unless it explicitly opts in;
    the one real live call site is core/memory_edges.py's own log_co_recall(). Returns the event rows
    (empty on skip/error) -- useful for tests and the backfill script, ignored by the real caller."""
    try:
        ids = sorted(dict.fromkeys(str(i) for i in (fragment_ids or []) if i))
        if len(ids) < 2:
            _skip("fewer-than-2-ids", n_ids=len(fragment_ids or []))
            return []
        pairs = list(combinations(ids, 2))[:PAIR_CAP]
        now = ts if ts is not None else time.time()
        sign = _sign(valence)
        gate_open = developed == 1
        state = _load()
        out = []
        for a, b_id in pairs:
            key = f"{a[:12]}|{b_id[:12]}"
            rec = state.get(key) or {"w_naive": 0.0, "w_gated": 0.0, "n_naive": 0, "n_gated": 0,
                                      "born": now, "last_ts": now}
            gap = max(0.0, now - float(rec.get("last_ts", now)))
            decay = math.exp(-gap / DECAY_TAU_S[sign])
            wn_prev, wg_prev = float(rec.get("w_naive", 0.0)), float(rec.get("w_gated", 0.0))
            wn_decayed, wg_decayed = wn_prev * decay, wg_prev * decay
            step = GROWTH_STEP[sign]
            wn_after = min(CEILING, wn_decayed + step)                          # naive: always nudges
            wg_after = min(CEILING, wg_decayed + step) if gate_open else wg_decayed  # gated: only on developed==1
            rec.update(w_naive=round(wn_after, 5), w_gated=round(wg_after, 5),
                       n_naive=rec.get("n_naive", 0) + 1,
                       n_gated=rec.get("n_gated", 0) + (1 if gate_open else 0),
                       last_ts=now, sign_last=sign)
            state[key] = rec
            row = {"ts": round(now, 1), "key": key, "sign": sign, "developed": developed,
                   "gate_open": gate_open, "source": source[:40], "gap_s": round(gap, 1),
                   "w_naive_prev": round(wn_prev, 5), "w_naive_after": round(wn_after, 5),
                   "w_gated_prev": round(wg_prev, 5), "w_gated_after": round(wg_after, 5),
                   "n_naive": rec["n_naive"], "n_gated": rec["n_gated"]}
            _log(row)
            out.append(row)
            # D-0215: graduation write, gated on the caller opting in AND the kill-switch AND the
            # pair's own gated weight clearing the bar -- `a`/`b_id` are the FULL fragment ids (the
            # `key` string above is a lossy 12-char-prefix pair id, kept only for this module's own
            # in-process state dict; a memory_edges row needs the real ids, which are only ever in
            # scope here, inline, never recoverable from the persisted state file alone).
            if live_edges and LIVE_EDGE_WRITE and rec["w_gated"] >= LIVE_EDGE_THRESHOLD:
                _write_live_edge(a, b_id, rec["w_gated"], source)
        stale = [k for k, v in state.items()
                 if max(v.get("w_naive", 0.0), v.get("w_gated", 0.0)) < PRUNE_BELOW
                 and (now - float(v.get("last_ts", now))) > PRUNE_IDLE_S]
        for k in stale:
            state.pop(k, None)
        _save(state)
        return out
    except Exception as exc:
        logger.debug("[spring_ledger] observe_co_recall failed (non-fatal): %s", exc)
        return []


def status() -> dict:
    """For the pulse / a quick health check -- coverage + top pairs by each rule."""
    try:
        from core.shadow_log import tail_rows as _tail_rows
        rows = _tail_rows(_LOG, 4000)
    except Exception:
        return {"activations": 0}
    live = [r for r in rows if "skip" not in r]
    if not live:
        return {"activations": 0, "skips": len(rows)}
    state = _load()
    top_naive = sorted(({"key": k, "w": v.get("w_naive", 0.0), "n": v.get("n_naive", 0)}
                         for k, v in state.items()), key=lambda x: -x["w"])[:8]
    top_gated = sorted(({"key": k, "w": v.get("w_gated", 0.0), "n": v.get("n_gated", 0)}
                         for k, v in state.items()), key=lambda x: -x["w"])[:8]
    return {"activations": len(live), "skips": len(rows) - len(live), "tracked_pairs": len(state),
            "top_naive": top_naive, "top_gated": top_gated}
