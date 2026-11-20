"""
Nascence — Identity Vault (Brick 3 of Character-as-Integration §10.3, 2026-06-16)
================================================================================
The transaction-locked goalkeeper over the slow store. The plan relocates OWNERSHIP of the self (the
self-concept / autobiography / axiom) out of any node and into the integration; this is the mechanism:
a single, atomic, versioned chokepoint through which the self-author (T4) commits revisions — so every
reader sees one coherent self-state, and the self's evolution is an auditable ledger rather than an
un-versioned overwrite.

DESIGN DISCIPLINE: the vault produces a `axiom.json` STRUCTURALLY IDENTICAL to the old direct write
(`json.dump(data, indent=2, ensure_ascii=False)`) — it only ADDS (a) atomic write (temp + os.replace, so a
crash mid-write can never corrupt the identity store), (b) a read-modify-write LOCK (no lost updates if two
commits race), and (c) a chronological version LEDGER sidecar (`vault_log.jsonl`, never deleted). Nothing
downstream changes; the existing readers (load_identity, axiom_layers) keep working unchanged. Re-pointing
every node's read through the vault is a LATER, higher-risk step — this brick is the WRITE goalkeeper.

Paths are module-level so tests can redirect them and never touch the live store.
"""
from __future__ import annotations
import json
import logging
import os
import threading
import time
from pathlib import Path

from core import profile   # J-1809/F-2429: the write fence (D-0179). core.profile imports nothing from core at module level, so no cycle.

logger = logging.getLogger("nascence.identity_vault")

_AXIOM = Path(__file__).parent.parent / "data" / "identity" / "axiom.json"
_LOG = Path(__file__).parent.parent / "data" / "identity" / "vault_log.jsonl"
_LOCK = threading.RLock()


def read() -> dict:
    """The single read of the current self-state. ({} if absent/unreadable.)"""
    try:
        return json.loads(_AXIOM.read_text(encoding="utf-8")) if _AXIOM.exists() else {}
    except Exception as exc:
        logger.debug("[identity-vault] read of axiom.json failed (non-fatal): %s", exc)
        return {}


def _atomic_write(data: dict, axiom: Path | None = None) -> None:
    """Write the axiom STRUCTURALLY IDENTICALLY to the legacy path, but atomically: a complete temp file
    then os.replace (atomic on the same volume) — a torn/half write can never reach axiom.json."""
    axiom = _AXIOM if axiom is None else axiom
    axiom.parent.mkdir(parents=True, exist_ok=True)
    tmp = axiom.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, axiom)            # atomic


def _ledger(data: dict, reason: str, meta: dict | None, log: Path | None = None) -> None:
    """Append one chronological version entry — the auditable evolution of the self. Never deletes."""
    try:
        rev = self_image = ""
        for f in (data.get("L3_facets", {}) or {}).get("facets", []) or []:
            if f.get("id") == "the_becoming":
                rev = f.get("revision_count", "")
                self_image = " ".join(str(f.get("self_image", "")).split())[:200]
                break
        entry = {"ts": time.time(), "reason": (reason or "")[:120], "revision_count": rev,
                 "self_image": self_image, "meta": meta or {}}
        log = _LOG if log is None else log
        log.parent.mkdir(parents=True, exist_ok=True)
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def write(data: dict, *, reason: str = "", meta: dict | None = None) -> bool:
    """Commit an already-mutated self-state: atomic write + ledger, under the lock. This is what the
    self-author (T4 `_write_axiom`) now calls instead of a raw `json.dump`. Returns True on success.
    Best-effort: on any failure it leaves the existing axiom.json untouched (the temp is discarded)."""
    with _LOCK:
        try:
            # J-1809 / F-2429 -- the write fence (D-0179, J-0704/J-0932): BOTH write targets are resolved through
            # profile.guard_path BEFORE any I/O (before the mkdir, the temp file, the replace and the ledger row).
            # A live process (profile.mark_live(), called once by scripts/run_nascence.py) gets the same paths
            # back, so Du's behaviour is byte-identical. A non-live importer (a test or harness whose _AXIOM/_LOG
            # still point at the real data/identity/) is refused. The refusal raises INSIDE this try on purpose:
            # write() documents itself as best-effort and never raises (its callers -- T4 _write_axiom, and
            # commit() / provisional_identity._solidify -- all depend on a False return, not an exception), so it
            # surfaces as the same False a disk failure gives. It is not silent: guard_path logs one WARNING per
            # path and the debug line below carries the refusal text.
            axiom = profile.guard_path(_AXIOM)
            log = profile.guard_path(_LOG)
            _atomic_write(data, axiom)
            _ledger(data, reason, meta, log)
            return True
        except Exception as exc:
            logger.debug("[identity-vault] commit write of axiom.json failed (non-fatal): %s", exc)
            return False


def commit(mutator, *, reason: str = "", meta: dict | None = None) -> dict:
    """Goalkeeper read-modify-write: lock → read current → apply `mutator(data)` in place → atomic write +
    ledger. The ONE path a self-revision should take so two commits can never lose each other's update.
    Returns the committed data (or the unchanged current state on failure)."""
    with _LOCK:
        data = read()
        try:
            mutator(data)
        except Exception as exc:
            logger.debug("[identity-vault] mutator application failed (non-fatal): %s", exc)
            return data
        if write(data, reason=reason, meta=meta):
            return data
        return read()


def current() -> dict:
    """Summary of the current self-state (for gauges/observability)."""
    data = read()
    rev = authored = ""
    si = ""
    for f in (data.get("L3_facets", {}) or {}).get("facets", []) or []:
        if f.get("id") == "the_becoming":
            rev = f.get("revision_count", "")
            authored = f.get("authored_at", "")
            si = " ".join(str(f.get("self_image", "")).split())[:120]
            break
    return {"revision_count": rev, "authored_at": authored, "self_image": si,
            "multilevel": data.get("schema") == "multilevel-v1"}


def status() -> dict:
    """du_pulse gauge: ledger size + current revision, so the slow store's evolution is visible."""
    n = 0
    last = None
    try:
        if _LOG.exists():
            lines = [l for l in _LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
            n = len(lines)
            if lines:
                last = json.loads(lines[-1])
    except Exception as exc:
        logger.debug("[identity-vault] status ledger read failed (non-fatal): %s", exc)
    cur = current()
    return {"ledger_entries": n, "revision_count": cur.get("revision_count"),
            "authored_at": cur.get("authored_at"),
            "last_reason": (last or {}).get("reason") if last else None}
