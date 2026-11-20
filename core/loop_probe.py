"""
Nascence — Loop Probe (Loop Metabolism, PHASE A: INSTRUMENT-ONLY, 2026-06-14)
============================================================================
Both auditors approved this phase outright: ship the dedup DETECTOR in shadow mode and the prune
DRY-RUN, change NO behaviour. It produces the two numbers needed before any cut — the real
forward dedup rate and the real prune impact — on live data, firewalled, read into nothing.

  shadow_observe(origin, content)  — for every self-origin episodic write, log whether it WOULD be
      exact-deduped (O(1), in-memory content-hash set; no per-write table scan — Gemini's latency
      guard) and the would-be replay_count. The write still happens. Behaviour is untouched.

  prune_dryrun()                   — what prune_episodic() WOULD demote to cold this call (kind-aware,
      per-kind sub-budgets + throttle since J-0475/D-0116): count, origin breakdown, confirmation that
      protected-origin material is protected, and the age/importance range of the cut. Delegates to
      prune_episodic(dry_run=True) — the real selection logic, SELECT-only. Pure read.

Exact-hash ONLY (auditor ruling Q1): near/semantic merging is deferred to the offline harvest so
the live hot lane stays cheap and the McAdams agentic-register transitions are never erased at
write time. Reads into NO behaviour. Firewalled log: data/loop_probe_log.jsonl.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
import threading
from pathlib import Path

from core import profile   # J-1815/F-2428: the write fence (D-0179)

logger = logging.getLogger("nascence.loop_probe")

_LOG = Path(__file__).parent.parent / "data" / "loop_probe_log.jsonl"

# self-voices only — world origins (reading/study/research) and keyed `action` are never deduped
SELF_ORIGINS = ("inner_thought", "subconscious_synthesis", "active_imagination")

_seen: dict[str, int] | None = None   # content-hash -> times seen (lazy, process-lifetime)


def _h(content: str) -> str:
    return hashlib.sha1((content or "").encode("utf-8", "ignore")).hexdigest()


def _init_seen() -> None:
    """One-time load of existing self-origin content hashes, so the per-write check is O(1)."""
    global _seen
    _seen = {}
    try:
        from core.memory.store import _connect
        with _connect() as c:
            q = "SELECT content FROM memory_fragments WHERE origin IN ({})".format(
                ",".join("?" * len(SELF_ORIGINS)))
            for r in c.execute(q, SELF_ORIGINS):
                hh = _h(r["content"] if hasattr(r, "keys") else r[0])
                _seen[hh] = _seen.get(hh, 0) + 1
        logger.info("[loop_probe] shadow seen-set seeded with %d self-origin hashes", len(_seen))
    except Exception as exc:
        logger.debug("[loop_probe] seen-set seed failed (non-fatal): %s", exc)
        _seen = {}


# J-1926 / F-2550: shadow_observe() runs from store_fragment on the loop thread and from the read_next_sitting worker thread; serialise the append.
_APPEND_LOCK = threading.Lock()


def shadow_observe(origin: str, content: str) -> None:
    """Observe-only. Log whether this write WOULD be exact-deduped. NEVER blocks the insert."""
    try:
        if origin not in SELF_ORIGINS or not content:
            return
        # J-1815 / F-2428 -- write fence: resolve the log target BEFORE any I/O/state change, INSIDE the existing
        # fail-open try (store_fragment's caller also swallows). A refusal skips the whole observation, so the
        # in-process _seen counter is not advanced by writes that never land.
        _log = profile.guard_path(_LOG)
        if _seen is None:
            _init_seen()
        hh = _h(content)
        prior = _seen.get(hh, 0)
        _seen[hh] = prior + 1
        rec = {
            "ts": time.time(),
            "origin": origin,
            "would_dedup": prior > 0,                 # an identical row already exists
            "would_be_replay_count": prior + 1,       # what replay_count would become on merge
            "content_head": (content or "")[:80],
        }
        with _APPEND_LOCK, open(_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except profile.NonLiveWriteError as exc:
        logger.debug("[loop_probe] shadow_observe write refused by the fence (non-live): %s", exc)
    except Exception as exc:                          # a probe must never affect the write path
        logger.debug("[loop_probe] shadow_observe failed (non-fatal): %s", exc)


def prune_dryrun(keep: int | None = None) -> dict:
    """What prune_episodic() WOULD do (kind-aware demote-to-cold, per-kind sub-budgets + throttle),
    without touching the DB. Pure read.

    (2026-09-02, J-0478/F-0648): this used to hand-duplicate prune_episodic's selection logic as a
    second SELECT — a single shared-pool query with only a 3-origin protected list and no cold=0
    filter, already stale before J-0475 and materially wrong after it (J-0475 made the real function
    kind-aware with per-kind sub-budgets (KIND_BUDGET_WEIGHT) and a per-kind throttle
    (MAX_DEMOTED_PER_KIND_PER_RUN) this copy never reflected). It now delegates to
    prune_episodic(dry_run=True) — the real function, SELECT-only — so there is exactly one place
    the selection logic lives and this can't drift stale again the same way.
    """
    # J-2275 (D-0453, 2026-10-17): prune_episodic is RETIRED -- it demotes nothing and its dry-run dict now
    # reports would_prune/would_demote/would_delete = 0 with `retired: True`. EPISODIC_PRUNE_THRESHOLD no
    # longer exists (the row cap was replaced by store.RETRIEVE_LATENCY_BUDGET_MS); `keep` is passed through
    # and ignored. Kept delegating so this stays the one place the (now empty) selection is read from.
    from core.memory.store import prune_episodic, _connect
    out: dict = {"keep": keep}
    try:
        out = prune_episodic(keep=keep, dry_run=True)
        # informational context only; kept under the old field name for continuity.
        with _connect() as c:
            out["episodic_total"] = c.execute(
                "SELECT COUNT(*) FROM memory_fragments WHERE layer='episodic'").fetchone()[0]
    except Exception as exc:
        out["error"] = str(exc)
    logger.info("[loop_probe] prune_dryrun: %s", out)
    return out
