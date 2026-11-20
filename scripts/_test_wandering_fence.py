"""
Regression: core/wandering.py's _log_trail (wandering_log.jsonl) sits behind the D-0179 write fence (J-1822, F-2453 side finding 2).

THE GAP. _log_trail opened Path(__file__).parent.parent/'data'/'wandering_log.jsonl' in 'a' mode with no guard_path, and is reached from perceive()
(core/couriers.py, the sensorium) and every wander step -- so any non-live process importing core.wandering from a tree wrote that tree's REAL log.
THE BUILD. The path resolves through profile.guard_path() as the first statement in _log_trail's own fail-open try; refusal is swallowed.

Every write goes to a temp dir; a BLOCKING audit hook aborts any write-mode open under a real data/ (live or this root's).
  [0] resolution  [1] static ratchet  [2] non-live fake root: fenced untouched, reference (fence undone) writes
  [3] real path, hook armed: fenced zero attempts via _log_trail AND perceive(); reference attempts the real file
  [4] live: byte-identical to the reference  [5] lab sandbox / outside-data redirects still write  [6] one warning  [7] canary

  python scripts/_test_wandering_fence.py       # run FROM the checkout it tests; exit 0 = ALL OK
TEETH: against the pre-J-1822 core/wandering.py (throwaway HEAD worktree + this file) it must exit 1.
"""
from __future__ import annotations

import ast
import hashlib
import inspect
import logging
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
TMP = Path(tempfile.mkdtemp(prefix="j1822_wandering_fence_"))
FAILS = 0
CHECKS = 0


def check(cond, label):
    global FAILS, CHECKS
    CHECKS += 1
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


_LIVE = Path(r"C:\Nascence") / "data"
_WATCH = sorted({str(_LIVE).lower(), str(ROOT / "data").lower()})
ATTEMPTS: list = []
_DATA_EXISTED = (ROOT / "data").exists()


def _snap(p):
    if not p.exists():
        return None
    b = p.read_bytes()
    return (len(b), hashlib.sha256(b).hexdigest())


def _under(p):
    try:
        if isinstance(p, int):
            return False
        s = os.path.abspath(os.fsdecode(os.fspath(p))).lower()
    except Exception:
        return False
    return any(s == r or s.startswith(r + os.sep) for r in _WATCH)


def _audit(event, args):
    hit = None
    try:
        if event == "open":
            path, mode, flags = args[0], args[1], args[2]
            w = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC)))
            if w and _under(path):
                hit = ("open", str(path))
    except Exception:
        return
    if hit:
        ATTEMPTS.append(hit)
        raise PermissionError(f"J-1822 test trap: write under a real data/ blocked: {hit}")


sys.addaudithook(_audit)


class _Cap(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.rows = []

    def emit(self, r):
        self.rows.append((r.name, r.levelno, r.getMessage()))


_cap = _Cap()
_pl = logging.getLogger("nascence.profile")
_pl_prop = _pl.propagate
_pl.addHandler(_cap)
_pl.propagate = False

import core                                                    # noqa: E402  (BEFORE anything that could aim at another tree)
from core import profile as P                                  # noqa: E402
from core import wandering as W                                # noqa: E402

print("[0] resolution")
for _m in (core, P, W):
    if ROOT not in Path(_m.__file__).resolve().parents:
        print(f"ABORT: {_m.__name__} imported from {_m.__file__}, not {ROOT}")
        sys.exit(2)
check(True, "core, core.profile, core.wandering are THIS root's")
check(getattr(W, "profile", None) is P, "core.wandering.profile is core.profile (one module object)")
check(list(inspect.signature(W._log_trail).parameters) == ["item"] and list(inspect.signature(W.perceive).parameters) == ["text"],
      "_log_trail(item) / perceive(text) signatures unchanged")

print("\n[1] static: every write-mode open()/write_text() in core/wandering.py takes a guard_path() result")


def _is_guard(n):
    return (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "guard_path"
            and isinstance(n.func.value, ast.Name) and n.func.value.id == "profile")


def _unfenced(src):
    bad = []
    for fn in ast.walk(ast.parse(src)):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        g = {t.id for n in ast.walk(fn) if isinstance(n, ast.Assign) and _is_guard(n.value) for t in n.targets if isinstance(t, ast.Name)}
        for n in ast.walk(fn):
            if not isinstance(n, ast.Call):
                continue
            f = n.func
            if isinstance(f, ast.Name) and f.id == "open" and n.args:
                m = n.args[1] if len(n.args) > 1 else next((k.value for k in n.keywords if k.arg == "mode"), None)
                if isinstance(m, ast.Constant) and isinstance(m.value, str) and set(m.value) & set("wax+"):
                    t = n.args[0]
                    if not (_is_guard(t) or (isinstance(t, ast.Name) and t.id in g)):
                        bad.append((fn.name, n.lineno))
            elif isinstance(f, ast.Attribute) and f.attr in ("write_text", "write_bytes"):
                if not (_is_guard(f.value) or (isinstance(f.value, ast.Name) and f.value.id in g)):
                    bad.append((fn.name, n.lineno))
    return bad


_bad = _unfenced(Path(W.__file__).read_text(encoding="utf-8"))
check(not _bad, f"no unfenced write site in core/wandering.py {_bad}")
check(_unfenced("def w(p):\n    with open(p, 'a') as f:\n        f.write('x')\n") != []
      and _unfenced("def w(p):\n    q = profile.guard_path(p)\n    open(q, 'a')\n    open(p)\n") == [], "the ratchet has teeth")

# pre-fence reference: the shipped function with its guard_path(X) call undone textually
_src, _n = re.subn(r"profile\.guard_path\((.*)\)\n", lambda m: m.group(1) + "\n", inspect.getsource(W._log_trail))
_ref_ns = dict(vars(W))
exec(compile(_src, "<pre-J-1822 _log_trail>", "exec"), _ref_ns)
check(_n == 1, f"shipped _log_trail carries exactly one guard_path site the reference undoes ({_n})")
_new, _ref = W._log_trail, _ref_ns["_log_trail"]

_orig = dict(DATA=P._DATA, CANON=P._CANONICAL_DATA, LIVE=P.LIVE, file=W.__file__, time=time.time, LOG=W._LOG)
fake = TMP / "fake_root"
(fake / "data").mkdir(parents=True)
ITEM = {"via": "sense", "origin": "sense", "text": "a ünï ✓ line"}


def _aim(root: Path, sim: bool = True):
    """_log_trail derives its path from the module global __file__ -> point it at <root>/core/wandering.py."""
    f = str(root / "core" / "wandering.py")
    W.__file__ = f
    _ref_ns["__file__"] = f
    # J-1824 / J-4050: _log_trail now reads the module constant _LOG at call time (not __file__), so aim that too.
    W._LOG = _ref_ns["_LOG"] = root / "data" / "wandering_log.jsonl"
    if root != ROOT:
        (root / "data").mkdir(parents=True, exist_ok=True)
        if sim:                                   # the simulated tree's own data/ is the one the fence protects
            P._DATA = P._CANONICAL_DATA = root / "data"
    return root / "data" / "wandering_log.jsonl"


def _sim():
    pass


def _real():
    P._DATA, P._CANONICAL_DATA = _orig["DATA"], _orig["CANON"]


def _seq(fn):
    fn(dict(ITEM))
    fn({"via": "memory", "origin": "m", "text": "x" * 300})


def _rows(p):
    return len(p.read_text(encoding="utf-8").splitlines()) if p.exists() else 0


try:
    time.time = lambda: 1_800_000_000.0
    print("\n[2] non-live, simulated data/ root")
    _sim()
    P.LIVE = False
    c = _aim(fake / "ctl")
    c.write_text("planted\n", encoding="utf-8")
    _seq(_ref)
    check(_rows(c) == 3, "CONTROL: pre-fence reference appends to the log in a non-live process")
    n = _aim(fake / "new")
    n.write_text("planted\n", encoding="utf-8")
    f0, names = _snap(n), sorted(x.name for x in n.parent.iterdir())
    _seq(_new)
    check(_snap(n) == f0 and sorted(x.name for x in n.parent.iterdir()) == names, "fenced: log byte-identical, nothing new next to it")
    check(_new(dict(ITEM)) is None, "fenced _log_trail returns None and raises nothing")

    print("\n[3] real default path, non-live, blocking hook armed")
    _real()
    P.LIVE = False
    _aim(ROOT)
    ATTEMPTS.clear()
    _seq(_new)
    W.perceive("a perceived line")      # the real entry point couriers / the sensorium call
    check(not ATTEMPTS, f"fenced: _log_trail AND perceive() made ZERO write attempts under a real data/ {ATTEMPTS}")
    check((ROOT / "data").exists() == _DATA_EXISTED, "fenced: no data/ directory created under this root")
    ATTEMPTS.clear()
    _seq(_ref)
    check({Path(a[1]).name for a in ATTEMPTS} == {"wandering_log.jsonl"},
          f"CONTROL: the pre-fence reference attempts the real wandering_log.jsonl ({len(ATTEMPTS)} attempts, blocked)")
    PRE_ATTEMPTS = len(ATTEMPTS)
    ATTEMPTS.clear()

    print("\n[4] live: fenced == pre-fence reference, byte for byte")
    _sim()
    P.LIVE = True
    lo = _aim(fake / "lo")
    lo.write_text("planted\n", encoding="utf-8")
    _seq(_ref)
    ln = _aim(fake / "ln")
    ln.write_text("planted\n", encoding="utf-8")
    _seq(_new)
    check(ln.read_bytes() == lo.read_bytes() and _rows(ln) == 3, "live: bytes identical to the reference, rows appended")
    check("ünï ✓".encode("utf-8") in ln.read_bytes() and b"\\u" not in ln.read_bytes(), "ensure_ascii=False content survives")

    print("\n[5] redirects, non-live")
    P.LIVE = False
    p = _aim(fake / "data" / "_lab" / "s1", sim=False)     # a lab_env.isolate()-style sandbox dir under data/_lab/<stamp>
    P._DATA = P._CANONICAL_DATA = fake / "data"
    _seq(_new)
    check(_rows(p) == 2, "data/_lab/<stamp>/ sandbox: still writes")
    p = _aim(TMP / "outside", sim=False)
    P._DATA = P._CANONICAL_DATA = fake / "data"      # a different tree's data/: the outside path is not under it
    _seq(_new)
    check(_rows(p) == 2, "a path outside data/: still writes")

    print("\n[6] visibility")
    v = _aim(fake / "vis")
    P._warned.discard(str(v))
    _cap.rows.clear()
    for _ in range(3):
        _new(dict(ITEM))
    w = [r for r in _cap.rows if r[1] == logging.WARNING and "wandering_log.jsonl" in r[2]]
    check(len(w) == 1, f"one guard_path warning per path across 3 refused writes ({len(w)})")
finally:
    P._DATA, P._CANONICAL_DATA, P.LIVE = _orig["DATA"], _orig["CANON"], _orig["LIVE"]
    W.__file__ = _orig["file"]
    W._LOG = _orig["LOG"]
    time.time = _orig["time"]
    _pl.removeHandler(_cap)
    _pl.propagate = _pl_prop

print("\n[7] no leak")
check(not ATTEMPTS and (ROOT / "data").exists() == _DATA_EXISTED, "no write attempt reached any real data/ outside the deliberate CONTROL probes; no data/ dir created")
shutil.rmtree(TMP, ignore_errors=True)
print(f"\n{'ALL OK' if not FAILS else f'{FAILS} FAILURE(S)'} -- {CHECKS} checks")
sys.exit(1 if FAILS else 0)
