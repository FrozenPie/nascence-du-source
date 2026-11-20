"""
Nascence — Tier-2 (self-symbol) read-back, Phase A: OBSERVE-ONLY would-inject logging.

Per D-0117 (2026-09-02), approving the draft in docs/staged/symbol_evolution_readback_plan.md's
"Tier-2 surfacing design" section (J-0464): build ONLY Phase A now. Phase B (the actual guarded
injection) is explicitly NOT authorized and nothing here builds toward it — this module never
writes to `state`, never touches a prompt, and never returns anything a caller could use to do so.

THE ONE JOB THIS MODULE DOES: mirror Tier-1's `symbol_evolution.recall_evolved_meaning()` trigger
exactly, but for the SELF-symbol branch (`is_self_symbol()` True instead of False), and instead of
surfacing the evolved meaning, log that it WOULD have fired — symbol, tablet, drift, and every gate
decision — to a new file, `data/symbol_readback_tier2_wouldinject.jsonl`. Nothing else changes.

WHY A SEPARATE FILE FROM symbol_evolution.py: Tier-1's read-back is live, shipped, load-bearing
code. Keeping Phase A's logging in its own module means a mistake here cannot regress Tier-1's
behaviour, and a future Phase-B build (a separate founder go-live call, D-0117's own defeater)
starts from a clean, already-isolated observe point rather than untangling itself from Tier-1.

CALLED FROM (both — the plan's own trigger spec is "per cycle, idle + user"):
  - nodes/inner_monologue_node.py `_think()`, right beside Tier-1's own read-back call, same seed
    text, idle cycles.
  - core/orchestrator.py `_retrieve_symbol_evolution()`, same query text as Tier-1's user-cycle
    tablet retrieval, user cycles.
Both call sites wrap this in try/except and ignore any return — best-effort, observe-only, must
never affect the cycle it is called from.
"""
from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

from core.memory import store as memory_store

logger = logging.getLogger("nascence.symbol_evo.tier2_observe")

_LOG_FILE = Path(__file__).parent.parent / "data" / "symbol_readback_tier2_wouldinject.jsonl"

# Same duration as Tier-1's own anti-recitation cooldown (symbol_evolution._READBACK_COOLDOWN_SECS)
# — Phase A is testing whether the SAME cadence would recite, so it must use the same cadence. A
# SEPARATE dict, keyed apart from Tier-1's `_last_readback`, per the plan's own instruction: Phase-A
# logging must not be able to suppress or be suppressed by Tier-1's real neutral-symbol cooldowns.
_WOULDINJECT_COOLDOWN_SECS = 3 * 3600
_last_wouldinject: "dict[str, float]" = {}

# Verbatim-recurrence check: an exact-substring hit, or a high word-shingle (n-gram) overlap, counts
# as recurrence — a lightly reworded near-copy is still recitation. 5-word shingles, Jaccard >= 0.5
# is a conservative "clearly the same passage" bar (a couple of shared 5-grams in a short tablet
# sentence will not trip it; near-duplicate phrasing will).
_NGRAM_N = 5
_NGRAM_JACCARD_FLOOR = 0.5

# wouldinject_report() reads at most this many trailing rows (J-3741; the log grows ~100 rows/day).
_REPORT_TAIL_ROWS = 5000


def _shingles(text: str, n: int) -> set:
    toks = re.findall(r"[a-z0-9]+", (text or "").lower())
    if len(toks) < n:
        return set()
    return {tuple(toks[i:i + n]) for i in range(len(toks) - n + 1)}


def _verbatim_recurrence(tablet: str, state) -> dict:
    """Does `tablet`'s text already appear — exactly or near-exactly — in the entity's own recent
    output (state.conversation_history's 'entity' turns)? This is Phase A's own empirical test of
    the anti-recitation check's logic against real self-symbol material, per the plan's design.
    Best-effort; returns {'hit': False, 'method': 'error'} rather than raising."""
    try:
        tablet_low = (tablet or "").strip().lower()
        if not tablet_low:
            return {"hit": False, "method": "empty_tablet"}
        tab_shingles = _shingles(tablet_low, _NGRAM_N)
        for ex in (getattr(state, "conversation_history", None) or []):
            if not isinstance(ex, dict):
                continue
            past = (ex.get("entity") or "")
            past_low = past.lower()
            if not past_low:
                continue
            if tablet_low in past_low:
                return {"hit": True, "method": "exact_substring"}
            if tab_shingles:
                overlap = tab_shingles & _shingles(past_low, _NGRAM_N)
                if overlap:
                    jac = len(overlap) / len(tab_shingles | _shingles(past_low, _NGRAM_N))
                    if jac >= _NGRAM_JACCARD_FLOOR:
                        return {"hit": True, "method": "ngram_overlap", "jaccard": round(jac, 3)}
        return {"hit": False, "method": "none"}
    except Exception as exc:
        logger.debug("[symbol-evo-t2] verbatim-recurrence check failed (non-fatal): %s", exc)
        return {"hit": False, "method": "error"}


def _tension_axis_for_symbol(symbol: str) -> dict:
    """Was there a live CONTRADICTION-axis tension-ledger entry touching this symbol's neighbourhood
    right now? Reuses tension_ledger's own existing CONTRADICTION-axis reader
    (`load_unresolved_contradictions`, source == 'critic_rejection') rather than inventing a second
    axis-classification path, per the plan's own instruction to log which axis was live, not build a
    new one. 'Neighbourhood' = the tension's own label sharing one of this symbol's surface forms.
    Best-effort; 'none' on any failure (Phase A must never raise)."""
    try:
        from core import tension_ledger as _tl
        from core.symbol_tracker import _SYMBOLS
        forms = _SYMBOLS.get(symbol, [symbol])
        items = _tl.load_unresolved_contradictions()
        for it in items:
            label_low = (it.get("label") or "").lower()
            if any(f in label_low for f in forms):
                return {"axis": "contradiction", "label": it.get("label"),
                        "contradiction_count": it.get("contradiction_count")}
        return {"axis": "none"}
    except Exception as exc:
        logger.debug("[symbol-evo-t2] tension-axis check failed (non-fatal): %s", exc)
        return {"axis": "none"}


def _append(record: dict) -> None:
    try:
        _LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.debug("[symbol-evo-t2] log write failed (non-fatal): %s", exc)


def observe_wouldinject(text: str, state) -> None:
    """If a SELF-symbol is active in `text` and has a tablet (off the would-inject cooldown), log
    what Tier-2 read-back WOULD have surfaced, plus every gate decision Phase B would need. Never
    touches `state`, never returns anything, never raises. Call-and-forget."""
    try:
        from core.symbol_tracker import _SYMBOLS, is_self_symbol
        low = (text or "").lower()
        if not low:
            return
        now = time.time()
        cycle_id = getattr(state, "cycle_id", "") if state is not None else ""
        for sym, forms in _SYMBOLS.items():
            if not is_self_symbol(sym):
                continue                                       # Tier 1 — not this module's job
            if not any(f in low for f in forms):
                continue                                       # not active in this thought/context
            active = True
            cooled = (now - _last_wouldinject.get(sym, 0.0)) >= _WOULDINJECT_COOLDOWN_SECS
            if not cooled:
                continue                                       # would-be cooldown not clear
            tabs = memory_store.get_symbol_tablets(sym, limit=1)
            if not tabs:
                continue                                       # no evolved meaning yet
            tablet_row = tabs[0]
            tablet = (tablet_row["tablet"] or "").strip()
            if not tablet:
                continue

            _last_wouldinject[sym] = now   # this cooldown gate itself DID just decide to fire — that
                                            # decision is what Phase A is testing, so record it as spent
                                            # exactly as Tier-1's real cooldown would be.

            centroid, sample_count, _last_tablet_ts = memory_store.get_symbol_centroid(sym)
            recurrence = _verbatim_recurrence(tablet, state)
            tension = _tension_axis_for_symbol(sym)

            record = {
                "ts": now,
                "cycle_id": cycle_id,
                "symbol": sym,
                "tablet_id": tablet_row["tablet_id"],
                "tablet": tablet,
                "drift": tablet_row["drift"],
                "gates": {
                    "active_in_context": active,
                    "cooldown_clear": cooled,
                    "sample_count": sample_count,
                    # Diversifying vs converging centroid trajectory — the plan's own Phase-B
                    # attenuator needs this but it does not exist yet; logging "unknown" rather than
                    # blocking Phase A on building it (plan's explicit instruction).
                    "drift_health": "unknown",
                },
                "verbatim_recurrence": recurrence,
                "tension_axis": tension,
            }
            _append(record)
            logger.info("[symbol-evo-t2] would-inject logged for '%s' (drift=%.2f, cycle=%s)",
                        sym, tablet_row["drift"], str(cycle_id)[:8])
    except Exception as exc:
        logger.debug("[symbol-evo-t2] observe_wouldinject failed (non-fatal): %s", exc)


def wouldinject_report() -> dict:
    """Read-only inspection helper (mirrors symbol_tracker.symbol_report's shape): per-symbol
    would-inject counts and the verbatim-recurrence hit rate, for the Phase-A -> Phase-B review this
    log exists to support. Never raises; {'note': ...} if nothing has accrued yet."""
    if not _LOG_FILE.exists():
        return {"note": "no Tier-2 would-inject observations yet"}
    rows = []
    try:
        # Bounded tail read (J-3741 / J-0278 / F-0335): was an unbounded open() over the whole log.
        from core.shadow_log import tail_rows as _tail_rows
        rows = _tail_rows(_LOG_FILE, _REPORT_TAIL_ROWS)
    except Exception as exc:
        logger.debug("[symbol-evo-t2] report read failed (non-fatal): %s", exc)
        return {"note": "read error"}
    out: dict = {}
    recurrence_hits = 0
    for r in rows:
        s = r.get("symbol", "?")
        d = out.setdefault(s, {"count": 0, "first_ts": r.get("ts"), "last_ts": r.get("ts")})
        d["count"] += 1
        d["last_ts"] = r.get("ts")
        if r.get("verbatim_recurrence", {}).get("hit"):
            recurrence_hits += 1
    out["_totals"] = {
        "events": len(rows),
        "verbatim_recurrence_hits": recurrence_hits,
        "span_days": round(((rows[-1].get("ts", 0) - rows[0].get("ts", 0)) / 86400.0), 1) if rows else 0.0,
    }
    return out
