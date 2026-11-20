"""
Nascence -- shared persistence helpers for the multi-MB JSON stores (D-0347, J-1834, F-2401 item 3)
===================================================================================================
D-0339 part (d) / J-1767 (F-2401, commit 06ca47e) hardened the protected SUBCONSCIOUS node's heavy state
file: written through <file>.tmp + os.replace (with a short retry, because on this Windows box os.replace
raises PermissionError / WinError 5 while ANY other handle holds the destination open), and an unreadable
file logged loudly and MOVED ASIDE instead of silently re-seeded. F-2401 item (3) found two more multi-MB
stores still truncated in place with a swallow-everything loader: data/frontier.json (core/frontier.py) and
data/pursuits_active.json (core/pursuits.py). D-0347 (Travis, 2026-10-06) ruled the same ADDITIVE hardening
for both. This module is the one place that pattern lives for those two, so they cannot drift apart.

Strictly additive, and deliberately small:
  * write_text_atomic(path, text)  -- the bytes written are exactly what the old in-place write_text/open("w")
    wrote (same text-mode newline translation), but via <path>.tmp + os.replace, so a process that dies mid-
    write leaves `path` exactly as it was (the half-written bytes are in the .tmp). RAISES on failure, with
    the partial .tmp removed and `path` untouched; the caller keeps its own fail-open policy.
  * load_json_or_move_aside(...)   -- a missing file is a normal first boot (silent default). A file that
    cannot be read or parsed is logged loudly (a WARNING: the nascence.log format carries no level, so the
    words STATE FILE UNREADABLE are in the message) and MOVED to <stem>.corrupt.<UTC stamp><suffix> beside it
    before the default is returned. Never deleted, never overwritten (a counter suffix if the name exists),
    never restored from any backup (that stays the founder's call), never raises.

J-4426 (F-5128, 2026-11-20): a hard crash zero-filled 19 data/ state files (every file rewritten in the last
minute: NTFS had journaled the rename and the new size, never the data) and Du reloaded them as empty with no
log line. write_text_atomic now fsyncs the .tmp before the rename, and two more helpers serve the small-to-
16 MB whole-file state stores that had no shared path at all:
  * write_text_durable(path, text) -- .tmp + flush + fsync + os.replace, and first keeps one previous
    generation as <name>.prev (a hard link to the outgoing file, so no extra bytes are written; a copy only
    where a link is refused). A file whose first bytes are empty or NUL is never rotated into .prev.
  * read_json_durable(path, label, ...) -- the drop-in for json.loads(path.read_text()). Missing file: raises
    FileNotFoundError as before (a deliberate reset stays a reset). Empty, all-NUL or unparseable: a WARNING
    naming the file (words STATE FILE DAMAGED), then <name>.prev; if that parses, its value is returned and,
    when this process may write the path, the damaged file is moved to <stem>.corrupt.<stamp><suffix> and
    .prev is copied back in its place (STATE FILE RECOVERED). No usable .prev: a second WARNING and the
    caller's own default, as before.

Not addressed by write_text_atomic (same as the light sidecar and J-1767): no .prev generation. In-process writers of one path are serialised by a per-path lock; two PROCESSES writing the
same store at once is not a pattern either store has.
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Callable

# A same-directory rename onto a destination another handle holds open fails on Windows; HUD / pulse /
# coupling-rides / memory-edges readers parse these files (hundreds of ms for the 19 MB register), so wait
# longer than J-1767's 0.5 s. Only a FAILED swap ever sleeps; a healthy save never does. A save that still
# cannot swap is skipped (the previous complete file stays, the next save tries again): never a torn file.
REPLACE_ATTEMPTS = 8
REPLACE_DELAY_S = 0.1
# A read can collide with the swap itself for an instant; retry the I/O (not the parse) briefly before
# calling a file unreadable, so a transient collision is not mistaken for corruption (the D-0347 defeater).
READ_ATTEMPTS = 4
READ_DELAY_S = 0.1

_LOCKS: dict[str, threading.Lock] = {}
_LOCKS_GUARD = threading.Lock()


def _lock_for(path: Path) -> threading.Lock:
    key = str(path)
    with _LOCKS_GUARD:
        lk = _LOCKS.get(key)
        if lk is None:
            lk = _LOCKS[key] = threading.Lock()
        return lk


def write_text_atomic(path: Path, text: str) -> None:
    """Write `text` (utf-8, text-mode newlines exactly as Path.write_text / open("w") did) to `path` through
    <path>.tmp + os.replace. Raises on failure; on any failure the partial .tmp is removed and `path` is left
    exactly as it was."""
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    with _lock_for(path):
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(text)
                f.flush()
                os.fsync(f.fileno())    # J-4426 (F-5128): data on disk BEFORE the rename can be journaled
            for attempt in range(REPLACE_ATTEMPTS):
                try:
                    os.replace(tmp, path)
                    return
                except PermissionError:
                    if attempt == REPLACE_ATTEMPTS - 1:
                        raise
                    time.sleep(REPLACE_DELAY_S)
        except BaseException:
            try:
                tmp.unlink()
            except OSError:
                pass
            raise


def move_unreadable_aside(path: Path, exc: BaseException, logger: logging.Logger, label: str,
                          fresh_desc: str) -> Path | None:
    """`path` just failed to load. Log loudly, then MOVE it to <stem>.corrupt.<UTC stamp><suffix> beside it.
    Never deletes, never restores, never raises. Returns the new path, or None if the move itself failed (an
    ERROR then says so and the file stays where it is, as it always did)."""
    path = Path(path)
    size = -1
    try:
        try:
            size = path.stat().st_size
        except OSError:
            pass
        stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        dest = path.with_name(f"{path.stem}.corrupt.{stamp}{path.suffix}")
        n = 0
        while dest.exists():     # two quarantines inside one second must never overwrite each other
            n += 1
            dest = path.with_name(f"{path.stem}.corrupt.{stamp}-{n}{path.suffix}")
        os.replace(path, dest)
    except Exception as move_exc:
        logger.error("[%s] STATE FILE UNREADABLE -- %s (%d bytes) failed to load (%s: %s) AND could not be "
                     "moved aside (%s: %s). Starting %s; the next save will overwrite that file. "
                     "D-0347 / F-2401.", label, path, size, type(exc).__name__, exc,
                     type(move_exc).__name__, move_exc, fresh_desc)
        return None
    logger.warning("[%s] STATE FILE UNREADABLE -- %s (%d bytes) failed to load (%s: %s). Moved it aside to %s "
                   "(nothing deleted, nothing restored from any backup) and starting %s; restoring from the "
                   "moved file or a backup is the founder's call. D-0347 / F-2401.",
                   label, path, size, type(exc).__name__, exc, dest, fresh_desc)
    return dest


def load_json_or_move_aside(path: Path, default_factory: Callable[[], Any], logger: logging.Logger,
                            label: str, fresh_desc: str) -> Any:
    """json.loads(utf-8 text of `path`). Missing file -> default_factory() silently (normal first boot).
    Unreadable / unparseable -> loud log + move aside + default_factory(). Healthy file -> the parsed value,
    unchanged from what the old bare loaders returned."""
    path = Path(path)
    try:
        text = None
        for attempt in range(READ_ATTEMPTS):
            try:
                text = path.read_text(encoding="utf-8")
                break
            except FileNotFoundError:
                return default_factory()
            except UnicodeDecodeError:
                raise                       # a genuinely bad file, not a collision: no point retrying
            except OSError:
                if attempt == READ_ATTEMPTS - 1:
                    raise
                time.sleep(READ_DELAY_S)
        return json.loads(text)
    except Exception as exc:
        move_unreadable_aside(path, exc, logger, label, fresh_desc)
        return default_factory()


# ---------------------------------------------------------------------------------------------------------
# J-4426 (F-5128): durable whole-file state writes with one previous generation, and a loud load that falls
# back to that generation. See the module docstring.
# ---------------------------------------------------------------------------------------------------------
_PLOG = logging.getLogger("nascence.store_persist")
_DAMAGE_WARNED: dict[str, tuple] = {}     # path -> (size, mtime_ns) already warned about (read-only processes)


def prev_path_for(path: Path) -> Path:
    path = Path(path)
    return path.with_name(path.name + ".prev")


def _replace_retry(src: Path, dst: Path) -> None:
    for attempt in range(REPLACE_ATTEMPTS):
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            if attempt == REPLACE_ATTEMPTS - 1:
                raise
            time.sleep(REPLACE_DELAY_S)


def _head_looks_written(path: Path) -> bool:
    """Cheap check (64 bytes) that `path` is not empty and not a NUL-filled torn write."""
    try:
        with open(path, "rb") as f:
            head = f.read(64)
    except OSError:
        return False
    head = head.lstrip()
    return bool(head) and head[:1] != b"\x00"


def _rotate_prev(path: Path) -> bool:
    """Make <name>.prev the file `path` holds now: a hard link (no bytes written), or a copy if the link is
    refused. Skipped when `path` is missing or its head is empty/NUL, so a damaged file never displaces a good
    .prev. Raises on I/O failure (the caller logs and goes on with the save)."""
    if not _head_looks_written(path):
        return False
    prev = prev_path_for(path)
    ptmp = path.with_name(path.name + ".prev.tmp")
    try:
        ptmp.unlink()
    except FileNotFoundError:
        pass
    try:
        os.link(path, ptmp)
    except OSError:
        import shutil
        shutil.copyfile(path, ptmp)
    _replace_retry(ptmp, prev)
    return True


def _write_bytes_durable(path: Path, data: bytes, keep_prev: bool) -> None:
    tmp = path.with_name(path.name + ".tmp")
    try:
        with open(tmp, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        if keep_prev:
            try:
                _rotate_prev(path)
            except Exception as exc:
                _PLOG.debug("[store_persist] keeping %s.prev failed (non-fatal, save goes on): %s", path.name, exc)
        _replace_retry(tmp, path)
    except BaseException:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise


def write_text_durable(path: Path, text: str, keep_prev: bool = True) -> None:
    """Write `text` (utf-8, text-mode newlines as Path.write_text wrote them) to `path` via .tmp + flush + fsync
    + os.replace, keeping the outgoing file as <name>.prev first. RAISES on failure (partial .tmp removed,
    `path` untouched); the caller keeps its own fail-open policy."""
    path = Path(path)
    data = text.replace("\n", os.linesep).encode("utf-8") if os.linesep != "\n" else text.encode("utf-8")
    with _lock_for(path):
        _write_bytes_durable(path, data, keep_prev)


def _parse_or_reason(raw: bytes):
    """(value, None) when `raw` is valid utf-8 JSON, else (None, reason)."""
    try:
        return json.loads(raw.decode("utf-8")), None
    except Exception as exc:
        if not raw:
            return None, "empty (0 bytes)"
        if raw.count(0) == len(raw):
            return None, "all NUL bytes (a torn write after a crash)"
        return None, f"unparseable ({type(exc).__name__}: {str(exc)[:160]})"


def _read_bytes_retry(path: Path) -> bytes:
    for attempt in range(READ_ATTEMPTS):
        try:
            return path.read_bytes()
        except FileNotFoundError:
            raise
        except OSError:
            if attempt == READ_ATTEMPTS - 1:
                raise
            time.sleep(READ_DELAY_S)
    raise OSError(f"could not read {path}")


def _corrupt_dest(path: Path) -> Path:
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dest = path.with_name(f"{path.stem}.corrupt.{stamp}{path.suffix}")
    n = 0
    while dest.exists():
        n += 1
        dest = path.with_name(f"{path.stem}.corrupt.{stamp}-{n}{path.suffix}")
    return dest


def read_json_durable(path: Path, label: str, logger: logging.Logger | None = None,
                      guard: Callable[[Path], Any] | None = None) -> Any:
    """Drop-in for json.loads(path.read_text(encoding="utf-8")).

    Healthy file: the parsed value, same cost as before. Missing file: raises FileNotFoundError (unchanged; a
    deliberate reset is not undone from .prev). Empty / all-NUL / unparseable: WARNING naming the file, then
    <name>.prev. A usable .prev is returned; if `guard` is given and accepts the path (profile.guard_path: this
    process may write it), the damaged file is moved aside and .prev is copied back over it. No usable .prev:
    WARNING, the damaged file is moved aside when writable (so it can never be rotated into .prev), and
    ValueError is raised so the caller's own default applies exactly as before."""
    path = Path(path)
    log = logger or _PLOG
    raw = _read_bytes_retry(path)
    val, reason = _parse_or_reason(raw)
    if reason is None:
        return val
    key = str(path)
    try:
        st = path.stat()
        sig = (st.st_size, st.st_mtime_ns)
    except OSError:
        sig = (len(raw), 0)
    loud = _DAMAGE_WARNED.get(key) != sig
    writable = False
    if guard is not None:
        try:
            guard(path)
            writable = True
        except Exception:
            writable = False
    prev = prev_path_for(path)
    try:
        praw = _read_bytes_retry(prev)
        pval, preason = _parse_or_reason(praw)
    except FileNotFoundError:
        praw, pval, preason = b"", None, "missing"
    except Exception as exc:
        praw, pval, preason = b"", None, f"unreadable ({type(exc).__name__}: {exc})"
    if loud:
        log.warning("[%s] STATE FILE DAMAGED -- %s (%d bytes) is %s. Trying the previous generation %s. "
                    "J-4426 / F-5128.", label, path, len(raw), reason, prev.name)
    _DAMAGE_WARNED[key] = sig
    if preason is None:
        if writable:
            try:
                with _lock_for(path):
                    dest = _corrupt_dest(path)
                    _replace_retry(path, dest)
                    _write_bytes_durable(path, praw, keep_prev=False)
                log.warning("[%s] STATE FILE RECOVERED -- %s restored from %s (%d bytes); the damaged file was "
                            "moved to %s. J-4426 / F-5128.", label, path, prev.name, len(praw), dest.name)
            except Exception as exc:
                log.warning("[%s] STATE FILE RECOVERED IN MEMORY ONLY -- using %s for %s but could not restore "
                            "it on disk (%s: %s). J-4426 / F-5128.", label, prev.name, path, type(exc).__name__, exc)
        elif loud:
            log.warning("[%s] STATE FILE RECOVERED IN MEMORY ONLY -- using %s (%d bytes); this process may not "
                        "write %s, so the file is left as it is. J-4426 / F-5128.", label, prev.name, len(praw), path)
        return pval
    moved = None
    if writable:
        try:
            with _lock_for(path):
                moved = _corrupt_dest(path)
                _replace_retry(path, moved)
        except Exception:
            moved = None
    if loud or moved is not None:
        log.warning("[%s] STATE FILE NOT RECOVERED -- %s is %s and %s is %s; starting from defaults%s. "
                    "J-4426 / F-5128.", label, path, reason, prev.name, preason,
                    f" (damaged file moved to {moved.name})" if moved is not None else "")
    raise ValueError(f"state file damaged: {path} ({reason}); no usable {prev.name} ({preason})")


# ---------------------------------------------------------------------------------------------------------
# J-2417 (F-3117): shared mtime/size-keyed READ cache for multi-MB state files read on every tick.
# F-3117 measured ~65 MB/s of page-cache reads in Du's main process, all from modules that json.loads the same
# 17.5 MB subconscious_state.json / 5.6 MB frontier.json / transport_lines.json many times per think or per 5 s
# tick. A writer anywhere (tension_ledger, subconscious_node, ...) changes (st_mtime_ns, st_size), so the next
# read refreshes; this module never writes anything.
#
# CONTRACT: the returned object is SHARED. Treat it as READ-ONLY. A caller that mutates (then saves) must use
# its own non-cached loader or copy.deepcopy() it. Failure policy is the caller's: this raises exactly what a
# bare json.loads(path.read_text()) would (FileNotFoundError, OSError, ValueError), and never caches a failure.
# A file modified within _FRESH_S of now is NOT cached (mtime granularity could hide a second write that keeps
# the same size); and a writer in this process may call invalidate_json_cache(path) after its own save.
# ---------------------------------------------------------------------------------------------------------
_FRESH_S = 0.25
_JSON_CACHE: dict[str, tuple[int, int, Any]] = {}
_JSON_CACHE_GUARD = threading.Lock()


def load_json_cached(path: Path) -> Any:
    """json.loads(utf-8 text of `path`), returning the SAME parsed object while (st_mtime_ns, st_size) are
    unchanged. READ-ONLY result (see block comment). Raises like a bare read+json.loads on any failure."""
    path = Path(path)
    key = str(path)
    st = path.stat()
    sig = (st.st_mtime_ns, st.st_size)
    with _JSON_CACHE_GUARD:
        hit = _JSON_CACHE.get(key)
    if hit is not None and (hit[0], hit[1]) == sig:
        return hit[2]
    val = json.loads(path.read_text(encoding="utf-8"))
    try:
        st2 = path.stat()
        stable = (st2.st_mtime_ns, st2.st_size) == sig and (time.time_ns() - st2.st_mtime_ns) > _FRESH_S * 1e9
    except OSError:
        stable = False
    with _JSON_CACHE_GUARD:
        if stable:
            _JSON_CACHE[key] = (sig[0], sig[1], val)
        else:
            _JSON_CACHE.pop(key, None)
    return val


def invalidate_json_cache(path: Path | None = None) -> None:
    """Drop one path (or everything) from the read cache. Optional: a changed mtime/size already refreshes."""
    with _JSON_CACHE_GUARD:
        if path is None:
            _JSON_CACHE.clear()
        else:
            _JSON_CACHE.pop(str(Path(path)), None)


# ---------------------------------------------------------------------------------------------------------
# J-2418 (F-3118): WRITE-BEHIND coalescing for whole-file JSON state rewritten on every event.
# F-3118 measured core/spring_ledger.py (11 MB) and core/opponent_process.py (8.4 MB) re-parsing AND rewriting
# their whole state file on every memory_edges._log_co_recall -- most of Du's ~50 GB/day of SSD writes.
# CoalescedJsonStore keeps the parsed dict in-process (validated against the file's (mtime_ns, size), so an
# external writer -- a backfill script that unlinks the file, a restored backup -- is still picked up) and
# marks it dirty on save; the actual write happens at most once per `min_interval_s`, via a daemon timer for
# the tail of a burst, and always at interpreter exit (atexit). The first save after start writes at once.
# Cost: a hard kill (not a normal exit) loses at most `min_interval_s` of state; external readers of the file
# see it up to that stale. Callers keep their own atomic tmp+os.replace writer and fail-open policy.
# ---------------------------------------------------------------------------------------------------------
def _file_sig(path: Path):
    try:
        st = os.stat(path)
        return (st.st_mtime_ns, st.st_size)
    except OSError:
        return None


class CoalescedJsonStore:
    def __init__(self, label: str, log: logging.Logger):
        self._label = label
        self._log = log
        self._lock = threading.RLock()
        self._entries: dict[str, dict] = {}
        import atexit
        atexit.register(self.flush)

    def load(self, path: Path, reader: Callable[[Path], dict]) -> dict:
        """The cached dict while the file still carries the signature we last read/wrote; else reader(path).
        The SAME object is returned each time: the caller mutates it and passes it back to save()."""
        path = Path(path)
        key = str(path)
        with self._lock:
            e = self._entries.get(key)
            sig = _file_sig(path)
            if e is not None and e["sig"] == sig:
                return e["state"]
            state = reader(path)
            self._entries[key] = {"state": state, "sig": _file_sig(path), "dirty": False,
                                  "last_flush": e["last_flush"] if e else float("-inf"),
                                  "writer": e["writer"] if e else None, "timer": None,
                                  "path": path}
            if e is not None and e.get("timer") is not None:
                e["timer"].cancel()
            return state

    def save(self, path: Path, state: dict, writer: Callable[[Path, dict], bool],
             min_interval_s: float) -> None:
        path = Path(path)
        key = str(path)
        with self._lock:
            e = self._entries.get(key)
            if e is None:
                e = self._entries[key] = {"sig": None, "dirty": False, "last_flush": float("-inf"),
                                          "timer": None, "path": path}
            e["state"] = state
            e["writer"] = writer
            e["dirty"] = True
            wait = e["last_flush"] + float(min_interval_s) - time.monotonic()
            if wait <= 0:
                self._flush_entry(e)
            elif e["timer"] is None:
                t = threading.Timer(wait, self.flush, args=(path,))
                t.daemon = True
                e["timer"] = t
                t.start()

    def _flush_entry(self, e: dict) -> None:
        if e.get("timer") is not None:
            try:
                e["timer"].cancel()
            except Exception:
                pass
            e["timer"] = None
        if not e["dirty"] or e.get("writer") is None:
            return
        e["last_flush"] = time.monotonic()
        try:
            ok = e["writer"](e["path"], e["state"])
        except Exception as exc:
            self._log.debug("[%s] coalesced flush failed (non-fatal): %s", self._label, exc)
            ok = False
        if ok:
            e["dirty"] = False
            e["sig"] = _file_sig(e["path"])

    def flush(self, path: Path | None = None) -> None:
        """Write now whatever is dirty (one path, or all). Safe to call any time; never raises."""
        try:
            with self._lock:
                entries = ([self._entries[str(Path(path))]] if path is not None and str(Path(path)) in self._entries
                           else list(self._entries.values()) if path is None else [])
                for e in entries:
                    self._flush_entry(e)
        except Exception:
            pass


# ---------------------------------------------------------------------------------------------------------
# J-2418 (F-3118): integration_patterns (15.66 of subconscious_state.json's 17.5 MB) live in their own sibling
# file, written only when they changed (and at most every SUBC_PATTERNS_MIN_INTERVAL_S), so the ~33 s T1 scan
# rewrite drops to ~2 MB. Readers that need the patterns call load_integration_patterns().
# ---------------------------------------------------------------------------------------------------------
def patterns_path_for(state_path: Path) -> Path:
    state_path = Path(state_path)
    return state_path.with_name(state_path.stem + ".patterns" + state_path.suffix)


def load_integration_patterns(state_path: Path, state: dict | None = None) -> list:
    """The integration_patterns list for the subconscious state at `state_path`. `state` (an already-parsed
    state dict, if the caller has one) wins when it still carries the key -- only the unsplit/legacy writer puts
    it there, and it then is the newer write. Otherwise the sibling patterns file. [] when neither exists.
    READ-ONLY result, like load_json_cached()."""
    if isinstance(state, dict) and "integration_patterns" in state:
        return state.get("integration_patterns") or []
    try:
        pfile = patterns_path_for(state_path)
        if not delta_path_for(pfile).exists():
            val = load_json_cached(pfile)          # old layout: exactly as before J-2432
        else:
            val = _load_patterns_with_delta_cached(pfile)
        return val if isinstance(val, list) else []
    except Exception:
        return []


# ---------------------------------------------------------------------------------------------------------
# J-2432 (F-3134, D-0487 option 1; restart-gated, behind subconscious_node.SUBC_PATTERNS_FLOAT32 /
# SUBC_PATTERNS_DELTA, both default False = the J-2418 layout byte for byte). Lossless write reduction:
#  (1) float32 centroids: the centroids are float32 values stored as 17-digit float64 reprs; the shortest
#      float32 repr is ~40% smaller and np.float32(parsed) is bit-identical. Only used for a centroid whose
#      every value is finite and float32-exact (else that entry falls back to the ordinary encoding).
#  (2) delta layout: <stem>.patterns.json stays the BASE (a bare JSON list, readable by every old reader);
#      <stem>.patterns.delta.jsonl is an append-only journal of changed/new/removed entries since the base:
#         {"t": <time_ns>, "up": [entry, ...]}   upsert by "id" (existing keeps its position, new appends)
#         {"t": <time_ns>, "del": ["id", ...]}   remove by "id"
#      A journal line with t <= the base file's mtime_ns is ignored (it predates the last compaction -- covers
#      a crash between "write new base" and "delete journal"). A torn/unparseable line is skipped. Compaction
#      (full base rewrite, journal removed) happens at boot, on a reorder, or when the journal outgrows
#      max(DELTA_MAX_BYTES_FLOOR, 10% of the base). A pattern is only ever removed by an explicit "del" op
#      mirroring the node's own existing prune; this layer never drops one on its own.
# ---------------------------------------------------------------------------------------------------------
DELTA_MAX_BYTES_FLOOR = 1_000_000
_CENTROID_SENTINEL = "__J2432_CENTROID_SENTINEL__"


def delta_path_for(pfile: Path) -> Path:
    pfile = Path(pfile)
    return pfile.with_name(pfile.stem + ".delta.jsonl")


def _compact_centroid_text(centroid) -> str | None:
    """Shortest-float32 JSON text for `centroid`, or None when that would not be value-identical in float32
    (non-list, empty, non-finite, or any value that is not exactly a float32)."""
    try:
        import numpy as np
        a64 = np.asarray(centroid, dtype=np.float64)
        if a64.ndim != 1 or a64.size == 0 or not np.isfinite(a64).all():
            return None
        a32 = a64.astype(np.float32)
        if not (a32.astype(np.float64) == a64).all():
            return None
        return "[" + ", ".join(map(str, a32)) + "]"
    except Exception:
        return None


def encode_pattern(p, float32: bool = False) -> str:
    """json.dumps(p, ensure_ascii=False); with float32=True the centroid is the shortest float32 repr text."""
    if float32 and isinstance(p, dict) and isinstance(p.get("centroid"), list):
        ctext = _compact_centroid_text(p["centroid"])
        if ctext is not None:
            q = dict(p)
            q["centroid"] = _CENTROID_SENTINEL
            text = json.dumps(q, ensure_ascii=False)
            marker = json.dumps(_CENTROID_SENTINEL)
            if text.count(marker) == 1:
                return text.replace(marker, ctext)
    return json.dumps(p, ensure_ascii=False)


def encode_patterns_list(texts: list) -> str:
    """Bare JSON list text from per-entry texts (same separators as json.dumps)."""
    return "[" + ", ".join(texts) + "]"


def apply_patterns_delta(base: list, delta_text: str, base_mtime_ns: int) -> list:
    """base list + journal text -> merged list (a new list; entries are replaced, not mutated)."""
    out = list(base)
    index = {}
    for i, e in enumerate(out):
        if isinstance(e, dict) and "id" in e:
            index[e["id"]] = i
    removed = set()
    for line in delta_text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            op = json.loads(line)
            t = int(op.get("t", 0))
        except Exception:
            continue                               # torn tail / garbage: skip, never fail the load
        if t <= base_mtime_ns:
            continue                               # predates the base (already folded in)
        for e in op.get("up") or []:
            if not isinstance(e, dict) or "id" not in e:
                continue
            pid = e["id"]
            removed.discard(pid)
            if pid in index:
                out[index[pid]] = e
            else:
                index[pid] = len(out)
                out.append(e)
        for pid in op.get("del") or []:
            if pid in index:
                removed.add(pid)
    if removed:
        out = [e for e in out if not (isinstance(e, dict) and e.get("id") in removed)]
    return out


def read_patterns_file(pfile: Path) -> list:
    """Uncached: base + journal (if any). FileNotFoundError when the base is missing, like a bare open()."""
    pfile = Path(pfile)
    st = pfile.stat()
    base = json.loads(pfile.read_text(encoding="utf-8"))
    if not isinstance(base, list):
        return base
    try:
        dtext = delta_path_for(pfile).read_text(encoding="utf-8")
    except FileNotFoundError:
        return base
    return apply_patterns_delta(base, dtext, st.st_mtime_ns)


_DELTA_CACHE: dict = {}


def _load_patterns_with_delta_cached(pfile: Path) -> list:
    pfile = Path(pfile)
    s1, s2 = pfile.stat(), delta_path_for(pfile).stat()
    sig = (s1.st_mtime_ns, s1.st_size, s2.st_mtime_ns, s2.st_size)
    key = str(pfile)
    with _JSON_CACHE_GUARD:
        hit = _DELTA_CACHE.get(key)
    if hit is not None and hit[0] == sig:
        return hit[1]
    val = read_patterns_file(pfile)
    stable = (time.time_ns() - max(s1.st_mtime_ns, s2.st_mtime_ns)) > _FRESH_S * 1e9
    with _JSON_CACHE_GUARD:
        if stable:
            _DELTA_CACHE[key] = (sig, val)
        else:
            _DELTA_CACHE.pop(key, None)
    return val


def append_patterns_delta_lines(pfile: Path, lines: list) -> int:
    """Append already-encoded journal lines (no trailing newline each). Returns bytes appended."""
    dp = delta_path_for(pfile)
    blob = "\n".join(lines) + "\n"
    with _lock_for(dp):
        with open(dp, "a", encoding="utf-8", newline="\n") as f:
            f.write(blob)
    return len(blob.encode("utf-8"))


def remove_patterns_delta(pfile: Path) -> None:
    try:
        delta_path_for(pfile).unlink()
    except FileNotFoundError:
        pass
