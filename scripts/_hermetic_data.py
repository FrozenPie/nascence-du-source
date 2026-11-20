"""Shared hermetic-data guard for test scripts (J-3789).

A test that exercises a module with a hard-coded log path (data/felt_preamble_log.jsonl,
data/llm_latency.jsonl, data/memory/nascence.db, ...) writes into THIS tree's data/ -- and when the
test is run from C:\\Nascence, into Du's live logs. 46 of the session's tests did exactly that
(found 2026-11-07 at the Run G/H/I merge; bisected 2026-11-15 by running each test alone and diffing data/).

Usage, one line near the top of a test script (before the code under test writes anything)::

    import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789

install() does two things:
  1. Redirects every WRITE that targets <tree>/data/** (open for write/append, os.replace/rename/remove/
     mkdir/makedirs, sqlite3.connect) into a private temp directory. Reads see the temp copy if the file was
     written there, else the real file, so a test can still read seed data. Nothing under data/ is created or
     modified by the test.
  2. Registers an atexit check: if data/ differs from the snapshot taken at install() time (file set, sizes,
     mtimes), the process prints the offending paths and exits with status 97, so a leak that gets past (1)
     (e.g. a subprocess, or a C-level writer) fails the test instead of passing silently.

It does not import core or lab_env, so "import core BEFORE lab_env" ordering in the tests is unaffected.
"""
from __future__ import annotations

import atexit
import builtins
import io
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
_installed = False
_tmp: Path | None = None


def _snapshot() -> dict:
    out = {}
    if DATA.exists():
        for r, _d, fs in os.walk(DATA):
            for f in fs:
                p = os.path.join(r, f)
                try:
                    st = os.stat(p)
                    out[p] = (st.st_size, st.st_mtime_ns)
                except OSError:
                    pass
    return out


def _map(path, for_write: bool):
    """Return the temp-dir twin of a path under data/, or the path unchanged."""
    try:
        if isinstance(path, int) or path is None:
            return path
        p = Path(os.fspath(path))
        ap = p if p.is_absolute() else Path.cwd() / p
        ap = Path(os.path.normpath(ap))
        rel = ap.relative_to(DATA)
    except (ValueError, TypeError):
        return path
    twin = _tmp / rel
    if for_write:
        twin.parent.mkdir(parents=True, exist_ok=True)
        if not twin.exists() and ap.exists() and ap.is_file():
            shutil.copy2(ap, twin)  # append / read-modify-write sees the seed content
        return str(twin)
    return str(twin) if twin.exists() else path


def install() -> Path:
    """Redirect writes under <tree>/data/ to a temp dir and arm the exit check. Idempotent."""
    global _installed, _tmp
    if _installed:
        return _tmp
    _installed = True
    _tmp = Path(tempfile.mkdtemp(prefix="hermetic_data_"))
    before = _snapshot()
    _real_open, _real_io_open = builtins.open, io.open
    _r = {n: getattr(os, n) for n in ("replace", "rename", "remove", "unlink", "mkdir", "makedirs")}
    _real_connect = sqlite3.connect

    def _open(file, mode="r", *a, **kw):
        w = any(c in mode for c in "wax+")
        return _real_open(_map(file, w), mode, *a, **kw)

    def _io_open(file, mode="r", *a, **kw):
        w = any(c in mode for c in "wax+")
        return _real_io_open(_map(file, w), mode, *a, **kw)

    def _two(name):
        def f(src, dst, *a, **kw):
            return _r[name](_map(src, True), _map(dst, True), *a, **kw)
        return f

    def _one(name):
        def f(path, *a, **kw):
            return _r[name](_map(path, True), *a, **kw)
        return f

    def _connect(database, *a, **kw):
        return _real_connect(_map(database, True) if not str(database).startswith(":") else database, *a, **kw)

    builtins.open = _open
    io.open = _io_open
    os.replace, os.rename = _two("replace"), _two("rename")
    os.remove, os.unlink = _one("remove"), _one("unlink")
    os.mkdir, os.makedirs = _one("mkdir"), _one("makedirs")
    sqlite3.connect = _connect

    def _check():
        after = _snapshot()
        bad = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
        shutil.rmtree(_tmp, ignore_errors=True)
        if bad:
            sys.stderr.write("HERMETIC GUARD (J-3789): test changed the tree's data/:\n  " + "\n  ".join(bad[:20]) + "\n")
            sys.stderr.flush()
            os._exit(97)

    atexit.register(_check)
    return _tmp
