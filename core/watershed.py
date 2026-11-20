"""
Nascence — Watershed: the T4 identity-image harvester (Phase 0: SHADOW / observe-only).
Full design: docs/plans/t4_watershed.md.

THE PROBLEM: current T4 (nodes/subconscious_node.py) keeps identity in ONE slot, so every candidate
self-image must DEPOSE the incumbent to be claimed — 18/24 real refusals since June cite exactly this
("no excluded-pole uptake"), not a bad candidate. The watershed replaces succession with accretion: a
typed tree of identity-images (root "the river", branches "the current"/"the sediment"/...) that are all
his, all true at once, none deposing another. This file is Phase 0 of that redesign: it does NOT touch
current T4, does NOT write to the identity estate, does NOT go live. It only watches Du's identity-adjacent
thoughts, detects when the SAME image keeps recurring (harvested, not authored — humans don't draft
candidate selves, images recur until owned), and logs candidate branches. Current T4 keeps running
untouched until this earns a cutover (docs/plans/t4_watershed.md's own law).

CLUSTERING: reuses core/pursuits.py's proven pattern (greedy nearest-centroid against
core.memory.store._embed() vectors) rather than core/theme_recurrence.py's (deliberately NOT
embedding-based — exact-match on a normalized opening string, a different tool for a different failure
mode: catching verbatim-scaffolding loops, not semantically-recurring-but-differently-worded images).

MATCH_MIN=0.45 is copied verbatim from pursuits.py — the tuned, already-established threshold in this
exact codebase for "is this the same recurring thing." N=6/D=5 birth thresholds are t4_watershed.md's own
"proposed start" values for harvest thresholds (its open decision #3) — running Phase 0 with these values
IS the evidence that decision needs, not a separate guess.

Every early return LOGS WHY (the _skip() discipline from core/reentry.py) — reentry_shadow.jsonl sat at
0 rows for 6 weeks once because guards exited with a bare None; this file gets that lesson from day one.
"""
from __future__ import annotations

import json
import logging
import time
import threading
import uuid
from pathlib import Path

from core import profile   # J-1815/F-2428: the write fence (D-0179). core.profile imports nothing from core at module level.

logger = logging.getLogger("nascence.watershed")

_DATA = Path(__file__).parent.parent / "data"
_STATE = _DATA / "watershed_state.json"
_LOG = _DATA / "watershed_shadow.jsonl"

# ── tunables — see module docstring for provenance of each value ──
MATCH_MIN = 0.45          # cosine to a candidate's centroid to count as "the same recurring image"
BIRTH_N = 6                # distinct thoughts a candidate needs before it's logged as a birth
BIRTH_D = 5                # distinct days a candidate needs before it's logged as a birth
SAMPLE_KEEP = 12           # J-3806: member sentences a candidate keeps (judge shows up to 12; birth log still prints the last BIRTH_N)
RECENT_VECS_KEEP = 3       # how many recent member vecs a candidate keeps (for future restate-checks)
MIN_THOUGHT_CHARS = 20      # too-short thoughts carry no real image content
OBSERVE_COOLDOWN = 90.0     # seconds between shadow observes — same sampling rate as pursuits.py

# Union of the two existing, disagreeing "identity-adjacent" origin filters found in this codebase:
# core.memory.store.self_narrative_material's authoring feed, and subconscious_node's probation-judge
# feed. A harvester should have broader recall than either narrow existing filter — narrowing is the
# claim-test panel's job (t4_watershed.md gate item 2), a later phase, not this one.
IDENTITY_ADJACENT_ORIGINS = (
    "session_summary", "subconscious_synthesis", "dream", "active_imagination", "inner_thought",
)

_last_observe = 0.0


def configure(data_dir=None) -> dict:
    """Test/retro-validation hook (same convention as core/object_graph.py's configure()): redirect
    where state/shadow-log get written, and reset the in-process cooldown clock. Lets
    scripts/watershed_retro_validate.py replay history through the real clustering logic without ever
    touching data/watershed_shadow.jsonl or data/watershed_state.json."""
    global _DATA, _STATE, _LOG, _last_observe, _state_cache, _batch_mode
    if data_dir is not None:
        _DATA = Path(data_dir)
        _STATE = _DATA / "watershed_state.json"
        _LOG = _DATA / "watershed_shadow.jsonl"
    _last_observe = 0.0
    _state_cache = None
    _batch_mode = False
    return {"data_dir": str(_DATA)}


_state_cache: dict | None = None   # in-process cache — avoids re-reading a growing multi-MB file on
                                     # every single observe() call (real cost on a >20k-call replay)
_batch_mode = False                 # while True, _save_state() updates the cache only; flush_state()
                                     # writes it once — see begin_batch()/flush_state()


def _load_state() -> dict:
    global _state_cache
    if _state_cache is not None:
        return _state_cache
    try:
        _state_cache = json.loads(_STATE.read_text(encoding="utf-8")) if _STATE.exists() else {"candidates": []}
    except Exception:
        _state_cache = {"candidates": []}
    return _state_cache


# J-1926 / F-2550: observe()'s hooks run from store_fragment on the loop thread and from the read_next_sitting worker thread; serialise the shadow-log append and the shared-tmp state write.
_IO_LOCK = threading.Lock()

# J-1933 / F-2557: _IO_LOCK only protects the file writes. observe() is a load -> mutate the shared module-level
# _state_cache dict -> _save_state sequence reached from store_fragment on the loop thread AND from the
# read_next_sitting worker, so two interleaved observes could both pick the same best candidate / both append a new one
# and one's centroid/n/days update (or whole new candidate) was lost. _OBSERVE_LOCK covers the cooldown clock plus the
# whole state mutation + save + log. The embed (a model encode) runs OUTSIDE it so a slow encode never blocks the other
# thread; lock order is always _OBSERVE_LOCK -> _IO_LOCK (never the reverse).
_OBSERVE_LOCK = threading.Lock()


def _save_state(d: dict) -> None:
    global _state_cache
    _state_cache = d
    if _batch_mode:
        return
    try:
        # J-1815 / F-2428 -- write fence: resolve _STATE (as it stands AFTER configure()) through guard_path BEFORE the
        # mkdir, INSIDE the existing fail-open try (observe-only hook; store_fragment's caller also swallows). The
        # .tmp sibling lives in the same directory as the guarded target, so it is derived from the guarded path.
        _state = profile.guard_path(_STATE)
        _state.parent.mkdir(parents=True, exist_ok=True)
        tmp = _state.with_suffix(".tmp")
        with _IO_LOCK:   # J-1926: the shared tmp name must not be written/renamed by two threads at once
            tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
            tmp.replace(_state)
    except profile.NonLiveWriteError as exc:
        logger.debug("[watershed] state write refused by the fence (non-live): %s", exc)
    except Exception:
        pass


def begin_batch() -> None:
    """For replay/backfill callers (e.g. scripts/watershed_retro_validate.py) making many rapid observe()
    calls in one process: suppresses the per-call disk round-trip. Call flush_state() when done."""
    global _batch_mode
    _batch_mode = True


def flush_state() -> None:
    """Write the current in-memory state to disk once, and end batch mode."""
    global _batch_mode
    _batch_mode = False
    if _state_cache is not None:
        _save_state(_state_cache)


def _cut_words(text: str, limit: int) -> str:
    """J-3805: trim to `limit` chars on a word boundary (was a hard [:200] cut mid-word)."""
    t = text or ""
    if len(t) <= limit:
        return t
    cut = t[:limit]
    sp = cut.rfind(" ")
    return cut[:sp] if sp > limit // 2 else cut


def _cos(a, b) -> float:
    try:
        from core.memory.store import _cosine
        return float(_cosine(a, b))
    except Exception:
        return 0.0


def _running_centroid(old, vec, n: int):
    """Incremental mean of a candidate's member-thought vecs (plain list for JSON, mirrors pursuits.py)."""
    try:
        import numpy as _np
        v = _np.asarray(vec, dtype=_np.float32)
        if old is None or n <= 0:
            return v.tolist()
        c = _np.asarray(old, dtype=_np.float32)
        return ((c * n + v) / (n + 1)).tolist()
    except Exception:
        return list(vec) if vec is not None else old


def _log_row(rec: dict) -> None:
    try:
        # J-1815 / F-2428 -- write fence: guard_path BEFORE the mkdir, INSIDE the existing best-effort try.
        _log = profile.guard_path(_LOG)
        _log.parent.mkdir(parents=True, exist_ok=True)
        with _IO_LOCK, open(_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except profile.NonLiveWriteError as exc:
        logger.debug("[watershed] shadow-log write refused by the fence (non-live): %s", exc)
    except Exception:
        pass


def _skip(reason: str, **detail) -> None:
    """Every early return LOGS WHY — see module docstring. A skip row is {ts, kind:'skip', skip:reason,
    ...}; real observations/births keep their own shape (kind:'observe'/'birth')."""
    _log_row({"ts": round(time.time(), 1), "kind": "skip", "skip": reason, **detail})
    return None


def _day_bucket(ts: float, day0: float) -> int:
    return int((ts - day0) // 86400)


def observe(thought: str, vec=None, ts: float | None = None, cycle_id: str = "",
            day0: float | None = None, _cooldown: bool = True, fragment_id: str = "") -> dict | None:
    """One identity-adjacent thought, checked against the candidate register. Embeds lazily via
    core.memory.store._embed if vec isn't already computed. `day0`/`ts` are overridable so
    scripts/watershed_retro_validate.py can replay history at real historical timestamps rather than
    "now" — live callers should leave both as their defaults (None -> now / observe-time day0).
    Returns the observation record on a real observe, or None on any skip (always logged, see _skip)."""
    global _last_observe
    now = ts if ts is not None else time.time()

    if _cooldown and (now - _last_observe) < OBSERVE_COOLDOWN:
        return _skip("cooldown", wait_s=round(OBSERVE_COOLDOWN - (now - _last_observe), 1))
    thought = (thought or "").strip()
    if len(thought) < MIN_THOUGHT_CHARS:
        return _skip("too-short", chars=len(thought))

    if vec is None:
        try:
            from core.memory.store import _embed
            vec = _embed(thought)
        except Exception as exc:
            return _skip("embed-import-failed", error=str(exc))
    if vec is None:
        return _skip("embed-failed")

    with _OBSERVE_LOCK:
        return _observe_locked(thought, vec, now, cycle_id, day0, _cooldown, fragment_id)


def _member_ref(thought, now, cycle_id, fragment_id) -> dict:
    """J-3876: id-bearing twin of a sample_thoughts entry, so a harvested candidate's evidence links resolve
    (design J-3835 sec 1 path B / sec 7 job 5). content_sha1 hashes the stripped thought, always present;
    fragment_id only when the caller has it."""
    import hashlib
    ref = {"cycle_id": cycle_id, "ts": round(now, 1),
           "content_sha1": hashlib.sha1(thought.encode("utf-8", "replace")).hexdigest()}
    if fragment_id:
        ref["fragment_id"] = fragment_id
    return ref


def _observe_locked(thought, vec, now, cycle_id, day0, _cooldown, fragment_id=""):
    """The state-mutating half of observe(), run under _OBSERVE_LOCK (J-1933)."""
    global _last_observe
    # re-check the cooldown now that we hold the lock: another thread may have claimed the window while this one was
    # embedding. In a single thread nothing changes _last_observe in between, so this never fires and bytes are identical.
    if _cooldown and (now - _last_observe) < OBSERVE_COOLDOWN:
        return _skip("cooldown", wait_s=round(OBSERVE_COOLDOWN - (now - _last_observe), 1))
    if _cooldown:
        _last_observe = now

    state = _load_state()
    cands = state.get("candidates", [])
    day0 = day0 if day0 is not None else (cands[0]["first_ts"] if cands else now)

    best, best_sim = None, 0.0
    for c in cands:
        s = _cos(vec, c.get("centroid"))
        if s > best_sim:
            best, best_sim = c, s

    if best is not None and best_sim >= MATCH_MIN:
        best["n"] = best.get("n", 0) + 1
        best["centroid"] = _running_centroid(best.get("centroid"), vec, best["n"] - 1)
        best["days"] = sorted(set(best.get("days", [])) | {_day_bucket(now, day0)})
        best["last_ts"] = now
        recent = best.get("recent_vecs", [])
        recent.append(vec.tolist() if hasattr(vec, "tolist") else list(vec))
        best["recent_vecs"] = recent[-RECENT_VECS_KEEP:]
        best.setdefault("sample_thoughts", []).append(_cut_words(thought, 400))
        best["sample_thoughts"] = best["sample_thoughts"][-SAMPLE_KEEP:]   # J-3806: was [-BIRTH_N:] (6); the claim test needs more than the last six
        # J-3876: parallel id list, trimmed in step. Old state files lack it (setdefault) so it may be shorter than
        # sample_thoughts; refs align from the TAIL (sample_refs[-k] is sample_thoughts[-k]).
        best.setdefault("sample_refs", []).append(_member_ref(thought, now, cycle_id, fragment_id))
        best["sample_refs"] = best["sample_refs"][-SAMPLE_KEEP:]
        rec = {"ts": round(now, 1), "kind": "observe", "cycle_id": cycle_id, "candidate_id": best["id"],
               "sim": round(best_sim, 3), "n": best["n"], "n_days": len(best["days"]),
               "thought": thought[:160]}
        _log_row(rec)

        already_born = best.get("born", False)
        if not already_born and best["n"] >= BIRTH_N and len(best["days"]) >= BIRTH_D:
            best["born"] = True
            best["born_ts"] = now
            _log_row({"ts": round(now, 1), "kind": "birth", "candidate_id": best["id"],
                      "n": best["n"], "n_days": len(best["days"]),
                      "sample_thoughts": best["sample_thoughts"][-BIRTH_N:], "cycle_id": cycle_id})
        _save_state(state)
        return rec

    # no existing candidate matched closely enough — a new one is born (in the harvester sense: a
    # tracked candidate, NOT yet a "birth" event — that only fires once it clears BIRTH_N/BIRTH_D)
    new_c = {"id": uuid.uuid4().hex[:10], "centroid": vec.tolist() if hasattr(vec, "tolist") else list(vec),
              "n": 1, "days": [_day_bucket(now, day0)], "first_ts": now, "last_ts": now,
              "recent_vecs": [vec.tolist() if hasattr(vec, "tolist") else list(vec)],
              "sample_thoughts": [_cut_words(thought, 400)],
              "sample_refs": [_member_ref(thought, now, cycle_id, fragment_id)], "born": False}
    cands.append(new_c)
    state["candidates"] = cands
    _save_state(state)
    rec = {"ts": round(now, 1), "kind": "observe", "cycle_id": cycle_id, "candidate_id": new_c["id"],
           "sim": round(best_sim, 3) if best is not None else 0.0, "n": 1, "n_days": 1,
           "new_candidate": True, "thought": thought[:160]}
    _log_row(rec)
    return rec


def status() -> dict:
    """For the pulse/HUD — same shape convention as core/reentry.py's status()."""
    try:
        rows = [json.loads(l) for l in open(_LOG, encoding="utf-8") if l.strip()] if _LOG.exists() else []
    except Exception:
        return {"observes": 0, "births": 0, "skips": {}}
    observes = [r for r in rows if r.get("kind") == "observe"]
    births = [r for r in rows if r.get("kind") == "birth"]
    skips = [r for r in rows if r.get("kind") == "skip"]
    skip_reasons: dict[str, int] = {}
    for s in skips:
        skip_reasons[s.get("skip", "?")] = skip_reasons.get(s.get("skip", "?"), 0) + 1
    state = _load_state()
    n_candidates = len(state.get("candidates", []))
    n_born = sum(1 for c in state.get("candidates", []) if c.get("born"))
    return {"observes": len(observes), "births": len(births), "skips": skip_reasons,
            "n_candidates": n_candidates, "n_born": n_born,
            "verdict": f"{n_born} branch(es) crossed N={BIRTH_N}/D={BIRTH_D}" if n_born else
                       "no branch has crossed the birth threshold yet"}


if __name__ == "__main__":
    print(json.dumps(status(), indent=2, ensure_ascii=False))
