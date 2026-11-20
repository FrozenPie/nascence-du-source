"""
Regression: core/couriers.py's writers sit behind the D-0179 write fence (J-1805, F-2427's side finding; sibling of J-1797's core/buses.py fence).

THE GAP. core/couriers.py had no profile / guard_path at all, and every path in it is __file__-relative (_ROOT = Path(__file__).parent.parent), so ANY
process that imported it and reached a writer wrote that tree's REAL data/ files: _log_delivery -> couriers_log.jsonl (a bare open(..., 'a')) and
_save_state -> couriers_state.json (a bare write_text, the route cooldown). context_echo() and sound_echo() -- the two urgent couriers, called each
tick from core/orchestrator.py inside try/except -- call both on every delivery.

THE BUILD. Both writers resolve their path through profile.guard_path() as the first statement inside their own fail-open try. The live Du boot
(profile.mark_live()), a lab_env.isolate() sandbox and any path redirected outside data/ get the same path back; every other process is refused,
nothing is touched, nothing is raised. A non-live context_echo()/sound_echo() still returns True (the return value never depended on the writes) but
the cooldown no longer advances on disk -- the by-design difference.

Every write goes to a temp dir or a SIMULATED data/ root; a BLOCKING audit hook records and aborts any write-mode open / rename / remove under a real
data/ (C:\\Nascence\\data or <root>\\data), so even the pre-fence control can never write a file there.
  [0] resolution   core / core.profile / core.couriers come from THIS root; surface and flags unchanged
  [1] static       AST ratchet: every write-mode open() / write_text() in core/couriers.py takes a guard_path() result (and the ratchet has teeth)
  [2] non-live     simulated data/ root: fenced = both files byte-identical, nothing new; the pre-fence reference rewrites them (control)
  [3] real paths   the module's own default paths, audit hook armed: fenced = zero attempts, no data/ dir; the reference attempts both real files
  [4] live         fenced == pre-fence reference byte for byte (both routes, both COURIER_TEXT_DELIVERY settings), returns identical
  [5] redirects    data/_lab/<stamp>/ and a path outside data/ still write, identically; data/_lab/<file> with no sandbox dir stays refused
  [6] visibility   one guard_path warning per path
  [7] canary       the live couriers / buses / satisfaction / prediction-error / integrity files are byte-identical to the start of the run

The pre-fence reference is the shipped functions with their guard_path(X) calls undone textually (X), exec'd into a copy of the module namespace.

  python scripts/_test_couriers_fence.py        # exit 0 = ALL OK; run it FROM the checkout it tests (a worktree)
TEETH: run it with the pre-J-1805 core/couriers.py (a throwaway `git worktree add <dir> HEAD` plus this file) -- it must exit 1.
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
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="j1805_couriers_fence_"))
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
_CANARY = [_LIVE_DATA / f for f in ("couriers_log.jsonl", "couriers_state.json", "buses_log.jsonl", "buses_state.json", "satisfaction_log.jsonl",
                                    "satisfaction_state.json", "prediction_error_log.jsonl", "prediction_error_state.json")]
_CANARY.append(_LIVE_DATA / "logs" / "shadow_integrity.jsonl")


def _snap(p: Path):
    if not p.exists():
        return None
    b = p.read_bytes()
    return (len(b), hashlib.sha256(b).hexdigest())


_before = {p: _snap(p) for p in _CANARY}

_WATCH = sorted({str(_LIVE_DATA).lower(), str(ROOT / "data").lower()})
_WRITE_EVENTS = {"os.rename", "os.remove", "os.rmdir", "os.truncate", "os.utime", "os.chmod",
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
        raise PermissionError(f"J-1805 test trap: write under a real data/ blocked: {hit}")


sys.addaudithook(_audit)


def _attempt_names() -> set:
    return {Path(a[1]).name for a in ATTEMPTS}


class _Cap(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.rows = []

    def emit(self, record):
        self.rows.append((record.name, record.levelno, record.getMessage()))


_cap = _Cap()
_lgs = {n: logging.getLogger(n) for n in ("nascence.profile", "nascence.couriers")}
_lv = {n: (l.level, l.propagate) for n, l in _lgs.items()}
for _l in _lgs.values():
    _l.addHandler(_cap)
    _l.propagate = False

import core                                                    # noqa: E402  (BEFORE anything that could aim at another tree)
from core import profile as P                                  # noqa: E402
from core import couriers                                      # noqa: E402

# -- [0] resolution + surface ---------------------------------------------------------------------------------------------
print("\n[0] module resolution + surface")
for _m in (core, P, couriers):
    if ROOT not in Path(_m.__file__).resolve().parents:
        print(f"ABORT: {_m.__name__} was imported from {_m.__file__}, not from this root {ROOT}")
        sys.exit(2)
check(True, f"core, core.profile and core.couriers are THIS root's ({Path(core.__file__).resolve().parent})")
_D = {a: getattr(couriers, a) for a in ("_DELIVERY_LOG", "_STATE", "_DB")}
_orig = dict(DATA=P._DATA, CANON=P._CANONICAL_DATA, LIVE=P.LIVE, time=time.time, TD=couriers.COURIER_TEXT_DELIVERY)
check(getattr(couriers, "profile", None) is P, "core.couriers.profile is core.profile (one module object, so mark_live() reaches it)")
check(_D["_DELIVERY_LOG"] == ROOT / "data" / "couriers_log.jsonl" and _D["_STATE"] == ROOT / "data" / "couriers_state.json",
      "the two write-path constants keep their names and __file__-relative defaults (hud/server.py, felt_recall and du_pulse read the same files)")


def _sig(fn):
    return [(n, p.default if p.default is not inspect.Parameter.empty else "<req>") for n, p in inspect.signature(fn).parameters.items()]


check([n for n, _ in _sig(couriers._log_delivery)] == ["route", "detail"] and _sig(couriers._save_state) == [("d", "<req>")]
      and _sig(couriers.context_echo) == [] and _sig(couriers.sound_echo) == [] and _sig(couriers.status) == [],
      "_log_delivery(route, **detail) / _save_state(d) / context_echo() / sound_echo() / status() signatures unchanged")
check(couriers.WORLD_COURIERS is True and couriers.COURIER_TEXT_DELIVERY is True, "the two flags (WORLD_COURIERS, COURIER_TEXT_DELIVERY) are untouched")
P.LIVE = False
for _n in ("couriers_log.jsonl", "couriers_state.json"):
    try:
        P.guard_path(_LIVE_DATA / _n)
        check(False, f"guard_path refuses the REAL data/{_n} in a non-live process")
    except P.NonLiveWriteError:
        pass
check(True, "guard_path refuses both REAL live files in a non-live process (pure check, no I/O)")

# -- [1] static ratchet ---------------------------------------------------------------------------------------------------
print("\n[1] static: every write-mode open() / write_text() in core/couriers.py takes a guard_path() result")


def _is_guard(n) -> bool:
    return (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "guard_path"
            and isinstance(n.func.value, ast.Name) and n.func.value.id == "profile")


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
            if isinstance(f, ast.Name) and f.id == "open" and node.args:
                mode = node.args[1] if len(node.args) > 1 else next((k.value for k in node.keywords if k.arg == "mode"), None)
                if isinstance(mode, ast.Constant) and isinstance(mode.value, str) and set(mode.value) & set("wax+"):
                    tgt = node.args[0]
                    if not (_is_guard(tgt) or (isinstance(tgt, ast.Name) and tgt.id in guarded)):
                        bad.append((fn.name, node.lineno, ast.unparse(tgt)))
            elif isinstance(f, ast.Attribute) and f.attr in ("write_text", "write_bytes"):
                if not (_is_guard(f.value) or (isinstance(f.value, ast.Name) and f.value.id in guarded)):
                    bad.append((fn.name, node.lineno, ast.unparse(f.value)))
    return bad


_bad = _unfenced_write_sites(Path(couriers.__file__).read_text(encoding="utf-8"))
check(not _bad, f"no unfenced write site in core/couriers.py {_bad}")
check(_unfenced_write_sites("def w(p):\n    with open(p, 'a') as f:\n        f.write('x')\n") != []
      and _unfenced_write_sites("def w():\n    _S.write_text('x')\n") != []
      and _unfenced_write_sites("def w(p):\n    q = profile.guard_path(p)\n    open(q, 'a')\n    profile.guard_path(p).write_text('x')\n    open(p)\n") == [],
      "the ratchet itself: flags a bare open(..., 'a') and a bare .write_text(), passes guard_path()-bound writers and plain reads")

# -- the pre-fence reference ------------------------------------------------------------------------------------------------
_SITE = re.compile(r"profile\.guard_path\((\w+)\)")
_FENCED = ("_log_delivery", "_save_state", "context_echo", "sound_echo")
_ref_ns = dict(vars(couriers))
_sites = {}
for _name in _FENCED:
    _src, _sites[_name] = _SITE.subn(r"\1", inspect.getsource(getattr(couriers, _name)))
    exec(compile(_src, f"<pre-J-1805 {_name}>", "exec"), _ref_ns)
check(_sites == {"_log_delivery": 1, "_save_state": 1, "context_echo": 0, "sound_echo": 0},
      f"the shipped module carries exactly the two guard_path sites the reference undoes {_sites}")
_get_new = lambda n: getattr(couriers, n)                      # noqa: E731
_get_ref = lambda n: _ref_ns[n]                                # noqa: E731

# -- fixtures --------------------------------------------------------------------------------------------------------------
T0 = 1_800_000_000.0


def _freeze():
    time.time = lambda: T0


DB = TMP / "nascence.db"
_c = sqlite3.connect(DB)
_c.execute("CREATE TABLE memory_fragments (fragment_id TEXT, content TEXT, origin TEXT)")
_c.execute("CREATE TABLE fragment_context (fragment_id TEXT, tuple_ts REAL, place TEXT, weather TEXT, sounds TEXT)")
_c.execute("INSERT INTO memory_fragments VALUES ('f1', 'a storm on the ünï shore ✓', 'lived')")
_c.execute("INSERT INTO fragment_context VALUES ('f1', ?, 'the shore', 'thunderstorm', '[\"owl_x\"]')", (T0 - 10 * 86400.0,))
_c.commit()
_c.close()

# Real core.sensorium / core.sound_knowledge / core.soundscape are used; the inputs the routes read are pinned, and wandering.perceive
# (its own writer, a separate question -- see the J-1805 finding) is neutralised.
from core import sensorium as SENS, sound_knowledge as SK, soundscape as SND, wandering as WDR       # noqa: E402
_stub_orig = dict(state=dict(SENS.state), load=SK._load, learned=SK.is_learned, perceive=WDR.perceive,
                  beds=SND._BEDS, rates=SND._EVENT_RATES)
PERCEIVED: list = []
WDR.perceive = lambda line, *a, **k: PERCEIVED.append(line)
SENS.state.clear()
SENS.state.update({"weather": "thunderstorm"})
SK._load = lambda: {"hearings": {"owl_x": {"last_ts": T0 - 5.0}}}
SK.is_learned = lambda k: True
SND._BEDS = set(SND._BEDS) - {"owl_x"}
SND._EVENT_RATES = {k: v for k, v in SND._EVENT_RATES.items() if k != "owl_x"}

fake = TMP / "fake_root" / "data"
fake.mkdir(parents=True)
_KEYS = ("delivery", "state")


def _paths(d: Path) -> dict:
    return dict(delivery=d / "couriers_log.jsonl", state=d / "couriers_state.json")


def _plant(p: dict) -> None:
    p["state"].parent.mkdir(parents=True, exist_ok=True)
    p["delivery"].write_text("".join(json.dumps({"ts": 1.0, "route": "planted", "n": i}) + "\n" for i in range(2)), encoding="utf-8")
    p["state"].write_text(json.dumps({"last_echo_ts": 5.0, "last_sound_echo_ts": 6.0}), encoding="utf-8")


def _aim(p: dict) -> None:
    for attr, val in (("_DELIVERY_LOG", p["delivery"]), ("_STATE", p["state"]), ("_DB", DB)):
        setattr(couriers, attr, val)
        _ref_ns[attr] = val


def _aim_defaults() -> None:
    _aim(dict(delivery=_D["_DELIVERY_LOG"], state=_D["_STATE"]))


def _fp(p: dict) -> dict:
    return {k: _snap(p[k]) for k in _KEYS}


def _bytes(p: dict) -> dict:
    return {k: (p[k].read_bytes() if p[k].exists() else None) for k in _KEYS}


def _rows(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines()) if path.exists() else 0


def _names(d: Path):
    return sorted(x.name for x in d.iterdir())


def _sequence(get) -> dict:
    """context_echo then sound_echo (cooldown state planted old enough to fire), plus both writers called directly."""
    PERCEIVED.clear()
    r = {}
    r["ctx"] = get("context_echo")()
    r["snd"] = get("sound_echo")()
    r["perceived"] = list(PERCEIVED)
    get("_log_delivery")("route_x", note="ünï ✓", n=3)
    get("_save_state")({"last_echo_ts": T0, "last_sound_echo_ts": T0})
    return r


_SIM = lambda: setattr(P, "_DATA", fake) or setattr(P, "_CANONICAL_DATA", fake)   # noqa: E731
_REAL = lambda: setattr(P, "_DATA", _orig["DATA"]) or setattr(P, "_CANONICAL_DATA", _orig["CANON"])   # noqa: E731

try:
    # -- [2] non-live, simulated data/ root ---------------------------------------------------------------------------------
    print("\n[2] non-live process, default-style paths under a simulated data/ root")
    _SIM()
    P.LIVE = False
    _freeze()
    ctl, new = _paths(fake / "nl_ctl"), _paths(fake / "nl_new")
    _plant(ctl)
    _aim(ctl)
    r_ctl = _sequence(_get_ref)
    check(r_ctl["ctx"] is True and r_ctl["snd"] is True and _rows(ctl["delivery"]) == 2 + 3
          and json.loads(ctl["state"].read_text()) == {"last_echo_ts": T0, "last_sound_echo_ts": T0},
          f"CONTROL: the pre-fence reference rewrites both files in a non-live process (delivery {_rows(ctl['delivery'])} rows, state advanced)")
    _plant(new)
    f0, n0 = _fp(new), _names(fake / "nl_new")
    _aim(new)
    r_new = _sequence(_get_new)
    check(_fp(new) == f0, "fenced: both files byte-identical (size + sha256) after context_echo, sound_echo and both writers called directly")
    check(_names(fake / "nl_new") == n0, f"fenced: no new file appeared next to them {_names(fake / 'nl_new')}")
    check(r_new == r_ctl and r_new["ctx"] is True and r_new["snd"] is True and len(r_new["perceived"]) == 2,
          "both routes still return True and still deliver their text (the return values never depended on the writes)")
    for fn, args in (("_log_delivery", ("route_x",)), ("_save_state", ({"zz": 1},))):
        try:
            check(_get_new(fn)(*args) is None, f"fenced {fn}() returns None and raises nothing")
        except Exception as exc:
            check(False, f"fenced {fn}() raised {exc!r}")
    check(_fp(new) == f0, "...and still touched nothing")

    # -- [3] the module's own REAL default paths ----------------------------------------------------------------------------
    print("\n[3] the module's own default (REAL data/) paths, non-live, blocking audit hook armed")
    _REAL()
    P.LIVE = False
    _freeze()
    ATTEMPTS.clear()
    _aim_defaults()
    r3 = _sequence(_get_new)
    check(not ATTEMPTS, f"fenced: the whole call sequence made ZERO write attempts under any real data/ {ATTEMPTS}")
    check((ROOT / "data").exists() == _DATA_EXISTED, "fenced: ...and created no data/ directory under this root either")
    check(r3 == r_ctl, "...and its returns are still the reference's")
    ATTEMPTS.clear()
    _aim_defaults()
    _sequence(_get_ref)
    check(_attempt_names() == {"couriers_log.jsonl", "couriers_state.json"},
          f"CONTROL: the pre-fence reference attempts both REAL files (blocked, never written): {sorted(_attempt_names())} ({len(ATTEMPTS)} attempts)")
    ATTEMPTS.clear()

    # -- [4] live, byte for byte --------------------------------------------------------------------------------------------
    print("\n[4] live process (profile.LIVE = True): fenced == pre-fence reference, byte for byte")
    _SIM()
    P.LIVE = True
    _freeze()
    for td in (True, False):
        couriers.COURIER_TEXT_DELIVERY = _ref_ns["COURIER_TEXT_DELIVERY"] = td
        ln, lo = _paths(fake / f"live_new_{td}"), _paths(fake / f"live_old_{td}")
        for p_, get_ in ((ln, _get_new), (lo, _get_ref)):
            _plant(p_)
            _aim(p_)
            p_["ret"] = _sequence(get_)
        bn, bo = _bytes(ln), _bytes(lo)
        for k in _KEYS:
            check(bn[k] is not None and bn[k] == bo[k], f"COURIER_TEXT_DELIVERY={td} {k}: bytes identical to the pre-fence reference ({len(bn[k] or b'')} B)")
        check(ln["ret"] == lo["ret"] and ln["ret"]["ctx"] is True and ln["ret"]["snd"] is True, f"COURIER_TEXT_DELIVERY={td}: every return value identical")
        check(_rows(ln["delivery"]) == 5, f"non-vacuous: delivery log grew 2 -> {_rows(ln['delivery'])} rows (two route rows + one direct)")
        if td is False:
            check(b"would_have_delivered" in bn["delivery"] and b"f1" in bn["delivery"], "the would-have row (D-0293) is written byte-identically too")
        else:
            check("ünï ✓".encode("utf-8") in bn["delivery"] and b"\\u" not in bn["delivery"], "ensure_ascii=False content survives byte-identically")
    couriers.COURIER_TEXT_DELIVERY = _ref_ns["COURIER_TEXT_DELIVERY"] = _orig["TD"]
    blocker = fake / "blocker_file"
    blocker.write_text("x")
    for tag, get_ in (("fenced", _get_new), ("pre-fence", _get_ref)):
        _aim(dict(delivery=blocker / "a.jsonl", state=blocker / "b.json"))
        r_io = _sequence(get_)
        check(r_io["ctx"] is True and r_io["snd"] is True and not (blocker / "a.jsonl").exists(),
              f"{tag}: real I/O errors (parent is a FILE) stay fail-open, routes still True")

    # -- [5] legitimate redirects -------------------------------------------------------------------------------------------
    print("\n[5] non-live process, legitimate redirects")
    P.LIVE = False
    ref_live = _bytes(_paths(fake / "live_new_True"))
    for tag, p_ in (("data/_lab/<stamp>/ (lab_env.isolate()'s sandbox)", _paths(fake / "_lab" / "20261004_000000")),
                    ("a path outside data/ (a temp redirect)", _paths(TMP / "outside"))):
        _plant(p_)
        _aim(p_)
        _sequence(_get_new)
        check(_bytes(p_) == ref_live, f"{tag}: writes and bytes identical to the live run")
    direct = _paths(fake / "_lab")
    _aim(direct)
    _sequence(_get_new)
    check(not any(direct[k].exists() for k in _KEYS), "data/_lab/<file> with no sandbox directory stays refused (no file created)")

    # -- [6] visibility -----------------------------------------------------------------------------------------------------
    print("\n[6] the swallowed refusal is not silent")
    vis = _paths(fake / "vis")
    _plant(vis)
    _aim(vis)
    P._warned.discard(str(vis["delivery"]))
    _cap.rows.clear()
    couriers._log_delivery("a")
    couriers._log_delivery("b")
    couriers._log_delivery("c")
    warn = [r for r in _cap.rows if r[0] == "nascence.profile" and r[1] == logging.WARNING and "couriers_log.jsonl" in r[2]]
    check(len(warn) == 1, f"guard_path logs ONE warning per path naming couriers_log.jsonl across 3 refused delivery writes ({len(warn)})")
finally:
    for _a, _v in _D.items():
        setattr(couriers, _a, _v)
    P._DATA, P._CANONICAL_DATA, P.LIVE = _orig["DATA"], _orig["CANON"], _orig["LIVE"]
    time.time = _orig["time"]
    couriers.COURIER_TEXT_DELIVERY = _orig["TD"]
    SENS.state.clear()
    SENS.state.update(_stub_orig["state"])
    SK._load, SK.is_learned, WDR.perceive = _stub_orig["load"], _stub_orig["learned"], _stub_orig["perceive"]
    SND._BEDS, SND._EVENT_RATES = _stub_orig["beds"], _stub_orig["rates"]
    for _n, _l in _lgs.items():
        _l.removeHandler(_cap)
        _l.setLevel(_lv[_n][0])
        _l.propagate = _lv[_n][1]

# -- [7] canary -------------------------------------------------------------------------------------------------------------
print("\n[7] canary")
_after = {p: _snap(p) for p in _CANARY}
check(_after == _before, "the live couriers / buses / satisfaction / prediction-error / integrity files are byte-identical to the start of the run "
      + "(" + ", ".join(f"{p.name} {_after[p][0] if _after[p] else 'absent'}" for p in _CANARY[:4]) + ")")
check(couriers._DELIVERY_LOG == ROOT / "data" / "couriers_log.jsonl" and (ROOT / "data").exists() == _DATA_EXISTED,
      "the module's own paths were restored and this root's data/ directory is as it was")
shutil.rmtree(TMP, ignore_errors=True)
print(f"\n{'ALL OK' if not FAILS else f'{FAILS} FAILURE(S)'} -- {CHECKS} checks")
sys.exit(1 if FAILS else 0)
