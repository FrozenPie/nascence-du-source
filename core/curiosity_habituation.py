"""
Nascence — Curiosity Habituation Shadow (squishy-spring discount, first READ path — J-0585, spawned
from F-0812, under docs/staged/dosed_coupling.md Phase 0 / docs/plans/cognitive_geometry.md §11).

SHADOW-ONLY. This module never changes what curiosity actually offers. `nodes/curiosity_node.py`'s
`_select_seeds` keeps sampling exactly as it always has (sqrt(count) weight, anti-relock recency
penalty, weighted-without-replacement pick) — that is the REAL choice, untouched. Alongside it, this
module computes a WOULD-CHOOSE sample using the same pool but with each tension's weight additionally
discounted by a habituation term `b`, and logs `{real_choice, would_choice, weights}` so a founder read
after a few days can ask whether the discount would have changed anything, per the founder framing
(T-0045): a strong pull for a long time is less important than a medium pull that never fires.

THE SHAPE (deliberately mirrors core/opponent_process.py's `b`, not a new formalism): `b` per tension
label GROWS when that tension is genuinely re-activated (its own `count` field increases — i.e. it
recurred somewhere in the system, the same signal core/tension_ledger.py already uses to decide whether
to bump chronic_mass) and DECAYS exponentially with quiet (real time since the tension's own `last_ts`).
Sign asymmetry (aversive > positive > neutral, same ordering as opponent_process) is approximated from
the tension's own `_last_touch_charge` (0..1, already computed by tension_ledger._touch_charge from the
tagged shadow_events.emotion_primary of its most recent member) since no per-tension valence field
exists yet — high charge (fear/anger/frustration/... per tension_ledger.CHARGE_WEIGHTS) reads as
aversive-shaped habituation (grows faster, higher ceiling, decays slower); low charge reads as
positive-shaped; anything else is neutral. This is a proxy, not a measured valence — documented as such,
not passed off as more than it is.

The discount is MULTIPLICATIVE and floored, never zeroing a tension out (this project's "not deletion"
law, dosed_coupling.md §6): discounted_weight = raw_weight * max(DISCOUNT_FLOOR, 1 - b).

State (`data/curiosity_habituation_state.json`) is keyed by tension ID (J-1172/D-0244, 2026-09-23 —
was keyed by label text; F-1630 found labels churn under a stable id and identical text can be worn by
different ids, so a label key stranded 70% of accumulated `b` on strings no tension wears any more,
F-1632). `nodes/curiosity_node.py`'s REAL pick and its anti-relock (`_recent_seeds`) still key by
label — that is live behaviour and stays untouched (this module is still shadow-only); only the pool
THIS module scores is now id-keyed, one entry per tension object, so a label shared by several tensions
no longer collapses onto a single last-wearer entry here (F-1632: about 160 of 868 tensions were
hidden this way). Persists {b, last_count, last_update_ts, sign_last} per id so decay is measured
against real elapsed time between calls, not resampled fresh each tick, and so a relabel (F-1630's
churn) no longer resets `b` to 0. The pre-existing per-label store cannot be migrated (no id was ever
recorded alongside a label, F-1632) and is moved aside as a dated backup the first time it is loaded
under this code, never deleted (see `_load_state()` below — demote, never delete, this project's
standing law). Fail-open throughout: any error here must never affect curiosity's real behaviour — the
caller wraps this whole module in a bare try/except.
"""
from __future__ import annotations

import json
import math
import random
import re
import time
from pathlib import Path

from core import profile

_DATA = Path(__file__).parent.parent / "data"
_STATE = _DATA / "curiosity_habituation_state.json"
_LOG = _DATA / "curiosity_habituation_shadow.jsonl"

# ── tunables (Phase 0 shadow — cheap to retune from the log, nothing here is live) ──
GROWTH_STEP = {"aversive": 0.12, "positive": 0.05, "neutral": 0.03}     # per genuine re-activation
GROWTH_DELTA_CAP = 5             # a count that jumped by a lot between polls still only grows b this much
CEILING = {"aversive": 0.95, "positive": 0.45, "neutral": 0.30}         # asymmetric asymptote for b
DECAY_TAU_S = {"aversive": 3 * 86400.0, "positive": 1 * 86400.0, "neutral": 2 * 86400.0}  # aversive lingers
CHARGE_AVERSIVE_AT_OR_ABOVE = 0.6     # _last_touch_charge proxy thresholds (tension_ledger's own scale)
CHARGE_POSITIVE_AT_OR_BELOW = 0.15
DISCOUNT_FLOOR = 0.05             # a habituated tension is discounted, never zeroed (dosed_coupling §6)

# J-1172/D-0244: a tension id is str(uuid.uuid4()) (nodes/subconscious_node.py:647) — used to tell an
# already-id-keyed state file apart from the old per-label one below, never to validate an id otherwise.
_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)


def _looks_id_keyed(d: dict) -> bool:
    """True if `d` is empty (nothing to migrate either way) or its keys already look like tension ids.
    False only when `d` is non-empty and its keys are clearly the OLD per-label text keys."""
    if not d:
        return True
    return bool(_UUID_RE.match(next(iter(d))))


def _load_state() -> dict:
    try:
        if not _STATE.exists():
            return {}
        d = json.loads(_STATE.read_text(encoding="utf-8"))
        if d and not _looks_id_keyed(d):
            # J-1172/D-0244: this is the pre-existing per-LABEL store (F-1632: 70% orphaned, and
            # unmigratable — no id was ever recorded alongside a label). Demote, never delete: move it
            # aside as a dated backup rather than overwriting or dropping it, then treat state as empty
            # so the id-keyed store below starts fresh. One-shot per real file: once renamed,
            # `_STATE.exists()` is False on every later call and this branch does not fire again.
            # Best-effort and guarded OUTSIDE the surrounding return-empty-on-any-error net's intent —
            # a non-live process (a lab/test run, guard_path raising NonLiveWriteError) cannot touch
            # data/ at all, so it just treats the old content as absent this call without renaming
            # anything; only a genuinely live process (or one already inside a lab_env.isolate()
            # sandbox, which guard_path treats as pre-isolated) performs the real rename.
            try:
                live_path = profile.guard_path(_STATE)
                backup = live_path.with_name(
                    f"curiosity_habituation_state.pre_idkey_{time.strftime('%Y%m%d')}.json")
                if not backup.exists():
                    live_path.replace(backup)
            except Exception:
                pass
            return {}
        return d
    except Exception:
        return {}


def _save_state(d: dict) -> None:
    path = profile.guard_path(_STATE)   # J-1196/D-0250: real data/ only if this process is live;
    # raises before any I/O if not (D-0179, J-0932 precedent). Resolved OUTSIDE the fail-open try
    # below, so the refusal is never swallowed by the net meant for genuine disk errors.
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)
    except Exception:
        pass


def _log(rec: dict) -> None:
    path = profile.guard_path(_LOG)   # J-1196/D-0250: same fence as _save_state() above, resolved
    # independently since _LOG is a distinct path constant from _STATE.
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _sign(charge: float) -> str:
    if charge >= CHARGE_AVERSIVE_AT_OR_ABOVE:
        return "aversive"
    if charge <= CHARGE_POSITIVE_AT_OR_BELOW:
        return "positive"
    return "neutral"


def _discount(tension_id: str, tension: dict, now: float, state: dict) -> tuple[float, dict]:
    """Advance and return this TENSION's (keyed by id, J-1172/D-0244 — was by label text) habituation
    `b`, plus the row detail for the shadow log. Mutates `state` in place (caller persists once after
    the whole pool is processed)."""
    count = int(tension.get("count", 1) or 1)
    last_ts = float(tension.get("last_ts") or now)
    charge = float(tension.get("_last_touch_charge", 0.3) or 0.3)
    sign = _sign(charge)

    prior = state.get(tension_id) or {"b": 0.0, "last_count": count, "last_update_ts": now}
    gap = max(0.0, now - float(prior.get("last_update_ts", now)))
    b_decayed = float(prior.get("b", 0.0)) * math.exp(-gap / DECAY_TAU_S[sign])

    delta = max(0, count - int(prior.get("last_count", count)))
    if delta > 0:
        step = GROWTH_STEP[sign] * min(delta, GROWTH_DELTA_CAP)
        b_after = min(CEILING[sign], b_decayed + step)
    else:
        b_after = b_decayed

    state[tension_id] = {"b": round(b_after, 5), "last_count": count, "last_update_ts": now, "sign_last": sign}
    detail = {"count": count, "charge": round(charge, 3), "sign": sign,
              "b_prev": round(float(prior.get("b", 0.0)), 5), "b": round(b_after, 5)}
    return b_after, detail


_LABEL_CAP = 200          # J-2626: per-label char cap in the logged `labels` (live max is ~100; just a bound)
_RECENT_SEEDS_CAP = 20    # J-2626: the node's own memory is 14 (_RECENT_SEED_MEMORY); cap is only a bound


def _label_fields(labels_by_id, recent_seeds, real_choice, would_choice) -> dict:
    """J-2626 / F-3356: the extra, additive row fields. `labels` = {id: label} for exactly the ids in
    real_choice + would_choice (never the whole pool, so the per-row cost stays ~1 KB, not a second
    pool copy); `recent_seeds` = the label list the node's anti-relock held AT PICK TIME. Each is
    emitted only when the caller supplied it, so an old-style call logs exactly the old row shape.
    Pure formatting; never raises into the caller (the surrounding observe_and_log net also covers it)."""
    out: dict = {}
    if labels_by_id is not None:
        wanted = list(dict.fromkeys(list(real_choice) + list(would_choice)))
        out["labels"] = {tid: str(labels_by_id[tid])[:_LABEL_CAP] for tid in wanted if tid in labels_by_id}
    if recent_seeds is not None:
        out["recent_seeds"] = [str(x)[:_LABEL_CAP] for x in list(recent_seeds)[-_RECENT_SEEDS_CAP:]]
    return out


def observe_and_log(pool: list[tuple[str, float]], tensions_by_id: dict, real_choice: list[str],
                     k: int, now: float | None = None, labels_by_id: dict | None = None,
                     recent_seeds: list | None = None) -> None:
    """Given the REAL sampling pool re-expressed `[(tension_id, raw_weight), ...]` (J-1172/D-0244 —
    was `(label, raw_weight)`; same sqrt(count)+anti-relock weights the real pick used, but one entry
    per tension OBJECT keyed by id, so a label shared by several tensions no longer collapses to one),
    the tension records keyed by id, the ids the REAL pick actually touched (every id sharing a label
    the real pick chose — see the caller, which removes them from its own pool together), and k
    itself: compute a WOULD-CHOOSE sample using habituation-discounted weights and log both. Never
    raises — the caller wraps this in try/except, but this stays self-contained defensively too.

    J-2626 / F-3356 (additive logging, restart-gated): two OPTIONAL kwargs. `labels_by_id` ({id: label},
    the caller's whole id->label map; only the ids in real_choice/would_choice are logged) and
    `recent_seeds` (the node's label-keyed anti-relock list at pick time) are written into the row as
    `labels` / `recent_seeds` so an id-era row stays readable as a label path (a tension's label churns
    under its stable id, F-1630; the real anti-relock memory is keyed by label text). They never touch
    the pick, the weights, the discount or the state file; rows from before this build lack them."""
    try:
        if not pool:
            return
        now = now if now is not None else time.time()
        state = _load_state()
        weights_detail: dict = {}
        discounted_pool: list[tuple[str, float]] = []
        for tid, raw_weight in pool:
            tension = tensions_by_id.get(tid, {})
            b, detail = _discount(tid, tension, now, state)
            discounted_weight = raw_weight * max(DISCOUNT_FLOOR, 1.0 - b)
            detail["raw_weight"] = round(raw_weight, 5)
            detail["discounted_weight"] = round(discounted_weight, 5)
            weights_detail[tid] = detail
            discounted_pool.append((tid, discounted_weight))
        _save_state(state)

        would_choice: list[str] = []
        wpool = list(discounted_pool)
        for _ in range(min(k, len(wpool))):
            ids = [p[0] for p in wpool]
            weights = [p[1] for p in wpool]
            pick = random.choices(ids, weights=weights, k=1)[0]
            would_choice.append(pick)
            wpool = [p for p in wpool if p[0] != pick]

        _log({
            "ts": round(now, 1),
            "keyed_by": "tension_id",   # J-1172/D-0244: absent on every pre-rekey row (those carry
                                          # label strings instead), present on every row from here on
            "real_choice": real_choice,
            "would_choice": would_choice,
            "differs": sorted(real_choice) != sorted(would_choice),
            "weights": weights_detail,
            **_label_fields(labels_by_id, recent_seeds, real_choice, would_choice),
        })
    except Exception:
        pass


def status() -> dict:
    """For the pulse: how much divergence the shadow has accrued so far — the pre-registered read."""
    try:
        from core.shadow_log import tail_rows as _tail_rows
        rows = _tail_rows(_LOG, 2000)
    except Exception:
        return {"rows": 0}
    if not rows:
        return {"rows": 0}
    differs = sum(1 for r in rows if r.get("differs"))
    return {
        "rows": len(rows),
        "differ_share": round(differs / len(rows), 3),
        "tracked_ids": len(_load_state()),   # J-1172/D-0244: was tracked_labels
    }
