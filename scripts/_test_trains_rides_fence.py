"""
Regression: core/trains.py (_log -> trains_log.jsonl) and core/coupling_rides.py (_append -> coupling_rides.jsonl) sit behind the D-0179 write fence
(J-1821, F-2453 side finding 1; siblings of J-1805's core/couriers.py and J-1797's core/buses.py fences).

THE GAP. Neither module had profile / guard_path, and both paths are __file__-relative, so ANY process that imported one and called trains.open()/close() or
coupling_rides.publish()/read()/... appended to that tree's REAL data/ file (after mkdir-ing data/ itself).

THE BUILD. trains._log and coupling_rides._append resolve profile.guard_path(_LOG) as the FIRST statement inside their own fail-open try, BEFORE the mkdir. Live,
lab_env.isolate() sandbox and outside-data paths get the same path back (byte-identical); a non-live process is refused, the refusal is swallowed, data/ is not
even created. trains._active (in-memory train ids) and every return value are unchanged.

Every write goes to a temp dir or a SIMULATED data/ root; a BLOCKING audit hook records and aborts any write-mode open / mkdir / rename / remove under a real data/.
  [0] resolution   core / core.profile / both modules come from THIS root; surface unchanged
  [1] static       AST ratchet: every write-mode open()/Path.open('a') in both modules takes a guard_path() result (and the ratchet has teeth)
  [2] non-live     simulated data/ root: fenced = file byte-identical, nothing new, same returns / in-memory ids; reference rewrites it (control)
  [3] real paths   module default paths, audit hook armed: fenced = zero attempts and no data/ dir created; the reference attempts the real data/
  [4] live         fenced == pre-fence reference byte for byte
  [5] redirects    data/_lab/<stamp>/ and a path outside data/ still write identically; data/_lab/<file> with no sandbox dir stays refused
  [6] visibility   one guard_path warning per path
  [7] canary       the live trains_log / coupling_rides / buses / couriers files are unchanged (prefix hash) since the start of the run

  python scripts/_test_trains_rides_fence.py     # exit 0 = ALL OK; run it FROM the checkout it tests (a worktree)
TEETH: run it with the pre-J-1821 modules (throwaway `git worktree add <dir> HEAD` plus this file) -- it must exit 1.
"""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
import logging
import os
import re
import shutil
import sys
import tempfile
import types
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="j1821_trains_rides_fence_"))
print("isolated store dir:", TMP)
FAILS = 0
CHECKS = 0


def check(cond: bool, label: str) -> None:
    global FAILS, CHECKS
    CHECKS += 1
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


_LIVE_DATA = Path(r"C:\Nascence") / "data"
_CANARY = [_LIVE_DATA / f for f in ("trains_log.jsonl", "coupling_rides.jsonl", "buses_log.jsonl", "buses_state.json", "couriers_log.jsonl",
                                    "couriers_state.json", "satisfaction_log.jsonl", "prediction_error_log.jsonl")]
_CANARY.append(_LIVE_DATA / "logs" / "shadow_integrity.jsonl")


def _snap_hash(p: Path, n: int | None = None):
    # live logs are appended to continuously by a running Du; compare a hash of the first N bytes (append-only => the prefix is stable unless rewritten)
    if not p.exists():
        return None
    if n is None:
        n = min(p.stat().st_size, 1_000_000)
    with open(p, "rb") as f:
        b = f.read(n)
    return (len(b), hashlib.sha256(b).hexdigest())


_before = {p: _snap_hash(p) for p in _CANARY}

_WATCH = sorted({str(_LIVE_DATA).lower(), str(ROOT / "data").lower()})
_WRITE_EVENTS = {"os.rename", "os.remove", "os.rmdir", "os.mkdir", "os.truncate", "os.utime", "os.chmod",
                 "shutil.copyfile", "shutil.copymode", "shutil.copystat", "shutil.copytree", "shutil.move", "shutil.rmtree"}
ATTEMPTS: list = []
_DATA_EXISTED = (ROOT / "data").exists()


def _under_watch(p) -> bool:
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
            writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC)))
            if writing and _under_watch(path):
                hit = ("open", str(path), mode)
        elif event in _WRITE_EVENTS:
            for a in args:
                if isinstance(a, (str, bytes, os.PathLike)) and _under_watch(a):
                    hit = (event, str(a), None)
                    break
    except Exception:
        return
    if hit:
        ATTEMPTS.append(hit)
        raise PermissionError(f"J-1821 test trap: write under a real data/ blocked: {hit}")


sys.addaudithook(_audit)


class _Cap(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.rows = []

    def emit(self, record):
        self.rows.append((record.name, record.levelno, record.getMessage()))


_cap = _Cap()
_lg = logging.getLogger("nascence.profile")
_lg_state = (_lg.level, _lg.propagate)
_lg.addHandler(_cap)
_lg.propagate = False

import core                                                    # noqa: E402  (BEFORE anything that could aim at another tree)
from core import profile as P                                  # noqa: E402
from core import trains, coupling_rides as CR                  # noqa: E402

# -- [0] resolution + surface ---------------------------------------------------------------------------------------------
print("\n[0] module resolution + surface")
for _m in (core, P, trains, CR):
    if ROOT not in Path(_m.__file__).resolve().parents:
        print(f"ABORT: {_m.__name__} was imported from {_m.__file__}, not from this root {ROOT}")
        sys.exit(2)
check(True, f"core, core.profile, core.trains, core.coupling_rides are THIS root's ({Path(core.__file__).resolve().parent})")
_orig = dict(DATA=P._DATA, CANON=P._CANONICAL_DATA, LIVE=P.LIVE, time=time.time, new_id=trains.new_id,
             tD=trains._DATA, tL=trains._LOG, cD=CR._DATA, cL=CR._LOG)
check(getattr(trains, "profile", None) is P and getattr(CR, "profile", None) is P, "both modules' .profile is core.profile (one object, so mark_live() reaches them)")
check(trains._LOG == ROOT / "data" / "trains_log.jsonl" and trains._DATA == ROOT / "data"
      and CR._LOG == ROOT / "data" / "coupling_rides.jsonl" and CR._DATA == ROOT / "data",
      "the path constants keep their names and __file__-relative defaults (hud/server.py, du_pulse, buses, lane2_break_habituation read the same files)")
check(list(inspect.signature(trains._log).parameters) == ["row"] and list(inspect.signature(CR._append).parameters) == ["row"]
      and list(inspect.signature(trains.open).parameters) == ["kind", "origin", "role", "parent", "product_type"]
      and list(inspect.signature(trains.close).parameters) == ["train_id", "reason"],
      "_log(row) / _append(row) / trains.open / trains.close signatures unchanged")
check(CR.COUPLING_PUBLISH is True, "COUPLING_PUBLISH flag untouched")
P.LIVE = False
for _p in (_LIVE_DATA / "trains_log.jsonl", _LIVE_DATA / "coupling_rides.jsonl"):
    try:
        P.guard_path(_p)
        check(False, f"guard_path refuses the REAL {_p.name} in a non-live process")
    except P.NonLiveWriteError:
        pass
check(True, "guard_path refuses both REAL live files in a non-live process (pure check, no I/O)")
P.LIVE = _orig["LIVE"]

# -- [1] static ratchet ---------------------------------------------------------------------------------------------------
print("\n[1] static: every write-mode open() / Path.open('a') in both modules takes a guard_path() result")


def _is_guard(n) -> bool:
    return (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "guard_path"
            and isinstance(n.func.value, ast.Name) and n.func.value.id == "profile")


def _mode_of(node, idx):
    return node.args[idx] if len(node.args) > idx else next((k.value for k in node.keywords if k.arg == "mode"), None)


def _writes(m) -> bool:
    return isinstance(m, ast.Constant) and isinstance(m.value, str) and bool(set(m.value) & set("wax+"))


def _unfenced_write_sites(src: str) -> list:
    bad = []
    for fn in ast.walk(ast.parse(src)):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        guarded = {t.id for node in ast.walk(fn) if isinstance(node, ast.Assign) and _is_guard(node.value)
                   for t in node.targets if isinstance(t, ast.Name)}
        for node in ast.walk(fn):
            if not isinstance(node, ast.Call):
                continue
            f = node.func
            if isinstance(f, ast.Name) and f.id == "open" and node.args and _writes(_mode_of(node, 1)):
                tgt = node.args[0]
                if not (_is_guard(tgt) or (isinstance(tgt, ast.Name) and tgt.id in guarded)):
                    bad.append((fn.name, node.lineno, ast.unparse(tgt)))
            elif isinstance(f, ast.Attribute) and f.attr == "open" and _writes(_mode_of(node, 0)):
                if not (_is_guard(f.value) or (isinstance(f.value, ast.Name) and f.value.id in guarded)):
                    bad.append((fn.name, node.lineno, ast.unparse(f.value)))
            elif isinstance(f, ast.Attribute) and f.attr in ("write_text", "write_bytes"):
                if not (_is_guard(f.value) or (isinstance(f.value, ast.Name) and f.value.id in guarded)):
                    bad.append((fn.name, node.lineno, ast.unparse(f.value)))
    return bad


for _m in (trains, CR):
    _bad = _unfenced_write_sites(Path(_m.__file__).read_text(encoding="utf-8"))
    check(not _bad, f"no unfenced write site in {Path(_m.__file__).name} {_bad}")
check(_unfenced_write_sites("def w(p):\n    with open(p, 'a') as f:\n        f.write('x')\n") != []
      and _unfenced_write_sites("def w():\n    with _LOG.open('a') as f:\n        pass\n") != []
      and _unfenced_write_sites("def w():\n    _S.write_text('x')\n") != []
      and _unfenced_write_sites("def w(p):\n    q = profile.guard_path(p)\n    open(q, 'a')\n    q.open('a')\n    open(p)\n") == [],
      "the ratchet itself: flags a bare open(..., 'a'), a bare Path.open('a') and a bare .write_text(); passes guard_path()-bound writes and plain reads")

# -- the pre-fence references ----------------------------------------------------------------------------------------------
_SITE = re.compile(r"profile\.guard_path\((\w+)\)")
_refs = {}
for _mod, _fname in ((trains, "_log"), (CR, "_append")):
    _src, _n = _SITE.subn(r"\1", inspect.getsource(getattr(_mod, _fname)))
    _ns = dict(vars(_mod))
    exec(compile(_src, f"<pre-J-1821 {_mod.__name__}.{_fname}>", "exec"), _ns)
    # rebind the reference onto the LIVE module dict so it sees the same _LOG/_DATA/profile the shipped function does (the test re-aims those)
    _refs[_mod.__name__] = (_fname, types.FunctionType(_ns[_fname].__code__, vars(_mod), _fname), _n, getattr(_mod, _fname))
check({k: v[2] for k, v in _refs.items()} == {"core.trains": 1, "core.coupling_rides": 1},
      "each shipped writer carries exactly one guard_path site, which the reference undoes")


def use(mod, which):
    """Route the module's own _log/_append global to the shipped (new) or pre-fence (ref) function."""
    fname, ref, _n, new = _refs[mod.__name__]
    setattr(mod, fname, new if which == "new" else ref)


# -- fixtures --------------------------------------------------------------------------------------------------------------
T0 = 1_800_000_000.0
fake = TMP / "fake_root" / "data"
fake.mkdir(parents=True)
_SIM = lambda: setattr(P, "_DATA", fake) or setattr(P, "_CANONICAL_DATA", fake)   # noqa: E731
_REAL = lambda: setattr(P, "_DATA", _orig["DATA"]) or setattr(P, "_CANONICAL_DATA", _orig["CANON"])   # noqa: E731


def _aim(d: Path) -> dict:
    p = dict(trains=d / "trains_log.jsonl", rides=d / "coupling_rides.jsonl")
    trains._LOG, trains._DATA = p["trains"], d
    CR._LOG, CR._DATA = p["rides"], d
    return p


def _aim_defaults() -> None:
    trains._LOG, trains._DATA, CR._LOG, CR._DATA = _orig["tL"], _orig["tD"], _orig["cL"], _orig["cD"]


def _plant(p: dict) -> None:
    p["trains"].parent.mkdir(parents=True, exist_ok=True)
    for k in ("trains", "rides"):
        p[k].write_text("".join(json.dumps({"ts": 1.0, "planted": i}) + "\n" for i in range(2)), encoding="utf-8")


def _fp(p: dict) -> dict:
    return {k: (p[k].stat().st_size, hashlib.sha256(p[k].read_bytes()).hexdigest()) if p[k].exists() else None for k in p}


def _bytes(p: dict) -> dict:
    return {k: (p[k].read_bytes() if p[k].exists() else None) for k in p}


def _names(d: Path):
    return sorted(x.name for x in d.iterdir())


def _sequence(which: str) -> dict:
    """Public API: a train opened + closed (+ a child), and the coupling publish / read / _append verbs."""
    use(trains, which)
    use(CR, which)
    trains._active.clear()
    CR._REG.clear()
    counter = iter(range(100))
    trains.new_id = lambda: f"t_{next(counter):06d}"
    time.time = lambda: T0
    r = {}
    a = trains.open("thought", "ünï ✓ origin", product_type="THOUGHT")
    b = trains.open("thought", "child", role="prove", parent=a["id"])
    trains.update(a["id"], len=7)
    r["train_a"] = dict(a)
    r["active_mid"] = sorted(trains._active)
    r["closed_b"] = trains.close(b["id"], "merged")
    r["closed_a"] = trains.close(a["id"], "done ünï")
    r["active_end"] = sorted(trains._active)
    CR.publish("climate", "stop_x", {"valence": 0.123456789, "note": "ünï ✓", "n": 3})
    r["read"] = CR.read("stop_y", "climate", ["valence"])
    CR._append({"ts": 1.5, "kind": "direct", "x": "ünï ✓"})
    return r


try:
    # -- [2] non-live, simulated data/ root -------------------------------------------------------------------------------
    print("\n[2] non-live process, default-style paths under a simulated data/ root")
    _SIM()
    P.LIVE = False
    ctl = _aim(fake / "nl_ctl")
    _plant(ctl)
    r_ctl = _sequence("ref")
    n_tr, n_ri = len(ctl["trains"].read_text().splitlines()), len(ctl["rides"].read_text().splitlines())
    check(n_tr == 2 + 4 and n_ri >= 2 + 2,
          f"CONTROL: the pre-fence reference appends to both files in a non-live process (trains {n_tr} rows, rides {n_ri} rows)")
    new = _aim(fake / "nl_new")
    _plant(new)
    f0, n0 = _fp(new), _names(fake / "nl_new")
    r_new = _sequence("new")
    check(_fp(new) == f0, "fenced: both files byte-identical (size + sha256) after the whole open/close/publish/read/_append sequence")
    check(_names(fake / "nl_new") == n0, f"fenced: no new file appeared next to them {_names(fake / 'nl_new')}")
    check(r_new == r_ctl and r_new["active_mid"] == ["t_000000", "t_000001"] and r_new["active_end"] == [] and r_new["closed_a"]["close_reason"] == "done ünï",
          "returns identical to the reference; trains._active ids / close bookkeeping unchanged by the fence (in-memory state never depended on the write)")
    check(r_new["read"] is not None and "valence" in r_new["read"], f"coupling read() still returns the published tuple {r_new['read']}")
    for mod, fn, arg in ((trains, "_log", {"event": "x"}), (CR, "_append", {"kind": "x"})):
        use(mod, "new")
        try:
            check(getattr(mod, fn)(arg) is None, f"fenced {mod.__name__}.{fn}() returns None and raises nothing")
        except Exception as exc:
            check(False, f"fenced {mod.__name__}.{fn}() raised {exc!r}")
    check(_fp(new) == f0, "...and still touched nothing")

    # -- [3] REAL default paths -------------------------------------------------------------------------------------------
    print("\n[3] the modules' own default (REAL data/) paths, non-live, blocking audit hook armed")
    _REAL()
    P.LIVE = False
    ATTEMPTS.clear()
    _aim_defaults()
    r3 = _sequence("new")
    check(not ATTEMPTS, f"fenced: the whole sequence made ZERO write/mkdir attempts under any real data/ {ATTEMPTS}")
    check((ROOT / "data").exists() == _DATA_EXISTED, "fenced: ...and created no data/ directory under this root either")
    check(r3 == r_ctl, "...and its returns are still the reference's")
    ATTEMPTS.clear()
    _aim_defaults()
    _sequence("ref")
    _hit = {Path(a[1]).name for a in ATTEMPTS}
    check(len(ATTEMPTS) > 0 and (ROOT / "data").name in {Path(a[1]).name for a in ATTEMPTS} | {"data"},
          f"CONTROL: the pre-fence reference attempts the REAL data/ (blocked, never written): {sorted(_hit)} ({len(ATTEMPTS)} attempts)")
    ATTEMPTS.clear()

    # -- [4] live, byte for byte ------------------------------------------------------------------------------------------
    print("\n[4] live process (profile.LIVE = True): fenced == pre-fence reference, byte for byte")
    _SIM()
    P.LIVE = True
    ln = _aim(fake / "live_new")
    _plant(ln)
    r_ln = _sequence("new")
    lo = _aim(fake / "live_old")
    _plant(lo)
    r_lo = _sequence("ref")
    bn, bo = _bytes(ln), _bytes(lo)
    for k in ("trains", "rides"):
        check(bn[k] is not None and bn[k] == bo[k], f"{k}: bytes identical to the pre-fence reference ({len(bn[k] or b'')} B)")
    check(r_ln == r_lo, "every return value identical")
    check(len(bn["trains"].splitlines()) == 6 and len(bn["rides"].splitlines()) >= 4,
          "non-vacuous: both logs grew (trains 2 -> 6 rows; rides gained publish/ride/direct rows)")
    check("ünï ✓".encode("utf-8") in bn["trains"] and "ünï ✓".encode("utf-8") in bn["rides"] and b"\\u" not in bn["trains"],
          "ensure_ascii=False content survives byte-identically")
    blocker = fake / "blocker_file"
    blocker.write_text("x")
    for tag in ("new", "ref"):
        trains._LOG, trains._DATA = blocker / "a.jsonl", blocker
        CR._LOG, CR._DATA = blocker / "b.jsonl", blocker
        try:
            r_io = _sequence(tag)
            check(r_io["active_end"] == [] and not (blocker / "a.jsonl").exists(), f"{tag}: real I/O errors (parent is a FILE) stay fail-open, in-memory state intact")
        except Exception as exc:
            check(False, f"{tag}: I/O error escaped: {exc!r}")

    # -- [5] legitimate redirects -----------------------------------------------------------------------------------------
    print("\n[5] non-live process, legitimate redirects")
    P.LIVE = False
    for tag, d in (("data/_lab/<stamp>/ (lab_env.isolate()'s sandbox)", fake / "_lab" / "20261005_000000"),
                   ("a path outside data/ (a temp redirect)", TMP / "outside")):
        p_ = _aim(d)
        _plant(p_)
        _sequence("new")
        check(_bytes(p_) == bo, f"{tag}: writes and bytes identical to the live run")
    direct = _aim(fake / "_lab")
    _sequence("new")
    check(not any(direct[k].exists() for k in direct), "data/_lab/<file> with no sandbox directory stays refused (no file created)")

    # -- [6] visibility ---------------------------------------------------------------------------------------------------
    print("\n[6] the swallowed refusal is not silent")
    vis = _aim(fake / "vis")
    _plant(vis)
    P._warned.discard(str(vis["trains"]))
    P._warned.discard(str(vis["rides"]))
    _cap.rows.clear()
    use(trains, "new")
    use(CR, "new")
    for _ in range(3):
        trains._log({"event": "a"})
        CR._append({"kind": "a"})
    for name in ("trains_log.jsonl", "coupling_rides.jsonl"):
        w = [r for r in _cap.rows if r[0] == "nascence.profile" and r[1] == logging.WARNING and name in r[2]]
        check(len(w) == 1, f"guard_path logs ONE warning per path naming {name} across 3 refused writes ({len(w)})")
finally:
    for _mod in (trains, CR):
        _fname, _ref, _n, _new = _refs[_mod.__name__]
        setattr(_mod, _fname, _new)
    _aim_defaults()
    P._DATA, P._CANONICAL_DATA, P.LIVE = _orig["DATA"], _orig["CANON"], _orig["LIVE"]
    time.time = _orig["time"]
    trains.new_id = _orig["new_id"]
    trains._active.clear()
    CR._REG.clear()
    _lg.removeHandler(_cap)
    _lg.setLevel(_lg_state[0])
    _lg.propagate = _lg_state[1]

# -- [7] canary -------------------------------------------------------------------------------------------------------------
print("\n[7] canary")
_after = {p: (_snap_hash(p, _before[p][0]) if _before[p] else _snap_hash(p)) for p in _CANARY}
check(all((_before[p] is None and _after[p] is None) or (_before[p] is not None and _before[p] == _after[p]) for p in _CANARY),
      "the first-1MB prefix hash of every live trains/rides/buses/couriers/satisfaction/prediction-error/integrity file is unchanged since the start of the run")
check(trains._LOG == ROOT / "data" / "trains_log.jsonl" and (ROOT / "data").exists() == _DATA_EXISTED,
      "the modules' own paths were restored and this root's data/ directory is as it was")
shutil.rmtree(TMP, ignore_errors=True)
print(f"\n{'ALL OK' if not FAILS else f'{FAILS} FAILURE(S)'} -- {CHECKS} checks")
sys.exit(1 if FAILS else 0)
