"""
Regression: core/buses.py's writers sit behind the D-0179 write fence (J-1797, F-2421's side finding).

THE GAP. core/buses.py had no profile / guard_path at all, and every path in it is __file__-relative (_ROOT = Path(__file__).parent.parent), so ANY
process that merely imported it and reached a writer wrote that tree's REAL data/ files: _log_delivery -> buses_log.jsonl, the calibration bridge ->
world_calibration.jsonl + buses_state.json (the dedupe state, rewritten on EVERY call), idle_freight's shadow row -> idle_freight_bus_shadow.jsonl.
A plain look reaches it: sensorium._shore_look's exact-match 'driftwood' branch calls buses.object_ledger_line('driftwood_17'), which calls
_log_delivery once the tracked object holds two observations -- J-1774's first test run did exactly that from a worktree (the audit hook recorded
7 open-for-append attempts at <worktree>\\data\\buses_log.jsonl). Same class as F-2406 (core/satisfaction.py, fenced by J-1783).

THE BUILD. Each of the four write paths is resolved through profile.guard_path() BEFORE any I/O, inside the writer's own fail-open net: the live Du
boot (profile.mark_live()), a lab_env.isolate() sandbox and any path redirected outside data/ get the very same path back; every other process is
refused, nothing is touched, nothing is raised (these are observe-only instruments; nodes/reflection_node.py calls idle_freight() unwrapped).
sync_investigation_calibration resolves BOTH of its targets (ledger + dedupe state) up front, so rows and state are written together or not at all.

What this proves, ISOLATED (no model, no live data: every write goes to a temp dir or a SIMULATED data/ root, and a BLOCKING audit hook records and
aborts any write-mode open / rename / remove under a real data/ -- C:\\Nascence\\data or <root>\\data -- so even the pre-fence control can never write a file there):
  [0] resolution   core / core.profile / core.buses come from THIS root; surface (names, signatures, defaults, flags) unchanged
  [1] static       every write-mode open() / write_text() in core/buses.py takes a guard_path() result (an AST ratchet: a NEW unfenced writer fails it)
  [2] non-live     (simulated data/ root) the pre-fence reference rewrites all four files; the fenced module leaves them byte-identical, creates no file,
                   raises nothing, and every return value except sync's rows-written count (0 vs N, by design) is identical to the reference
  [3] real paths   the module's own default (REAL data/) paths with the audit hook armed: the reference attempts all four real files, the fenced module none
  [4] live         (profile.LIVE = True) fenced == pre-fence reference, byte for byte (all four files) and return for return; real I/O errors stay fail-open
  [5] legit        a data/_lab/<stamp>/ sandbox and a path outside data/ still write (bytes identical to the live run); data/_lab/<file> stays refused
  [6] visibility   the swallowed refusal is not silent: one profile WARNING per path, a buses debug line carrying the refusal text
  [7] call site    the real sensorium.look('driftwood') at the shore, twice, in an isolated store: zero write attempts under any data/; the re-encounter
                   ledger line is still returned; the pre-fence _log_delivery swapped in attempts the real buses_log.jsonl (blocked)
  [8] canary       the live buses / satisfaction / prediction-error / integrity files are byte-identical to the start of the run

The pre-fence reference is the shipped function with its guard_path(X) calls undone textually (X), so it tracks future edits to the module; it is exec'd
into a copy of the module namespace. (At build time the derived sources were also diffed against `git show cc9b1b3:core/buses.py`.)

  python scripts/_test_j1797_buses_write_fence.py        # exit 0 = ALL OK; run it FROM the checkout it tests (a worktree, never C:\\Nascence for a control)
TEETH: run it with the pre-J-1797 core/buses.py (a throwaway `git worktree add <dir> cc9b1b3` plus this file) -- it must exit 1.
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
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="j1797_buses_fence_"))
print("isolated store dir:", TMP)

FAILS = 0
CHECKS = 0


def check(cond: bool, label: str) -> None:
    global FAILS, CHECKS
    CHECKS += 1
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


# data/ is gitignored and never checked out into a job-run worktree, so "live" is the one real repo, never ROOT-relative.
_LIVE_DATA = Path(r"C:\Nascence") / "data"
_CANARY = [_LIVE_DATA / f for f in ("buses_log.jsonl", "buses_state.json", "world_calibration.jsonl", "idle_freight_bus_shadow.jsonl",
                                    "satisfaction_log.jsonl", "satisfaction_state.json", "prediction_error_log.jsonl",
                                    "prediction_error_state.json", "world_objects.json", "world_substrate.json", "room_state.json")]
_CANARY.append(_LIVE_DATA / "logs" / "shadow_integrity.jsonl")


def _snap(p: Path):
    """(size, sha256) of a file, None if absent -- a byte-exact fingerprint, never mtime alone."""
    if not p.exists():
        return None
    b = p.read_bytes()
    return (len(b), hashlib.sha256(b).hexdigest())


_before = {p: _snap(p) for p in _CANARY}

# -- a BLOCKING write audit: records AND aborts any write-mode open / rename / remove under a real data/ ------------------
_WATCH = sorted({str(_LIVE_DATA).lower(), str(ROOT / "data").lower()})
_WRITE_EVENTS = {"os.rename", "os.remove", "os.rmdir", "os.truncate", "os.utime", "os.chmod",
                 "shutil.copyfile", "shutil.copymode", "shutil.copystat", "shutil.copytree", "shutil.move", "shutil.rmtree"}
ATTEMPTS: list = []
_HOOK_OFF = [False]                           # the test's own one cleanup step (removing the empty data/ the pre-fence control made) switches the trap off
_DATA_EXISTED = (ROOT / "data").exists()      # a refused writer must not even create this root's data/ directory (the old shadow write did: mkdir before open)


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
    if _HOOK_OFF[0]:
        return
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
        raise PermissionError(f"J-1797 test trap: write under a real data/ blocked: {hit}")


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
_lgs = {n: logging.getLogger(n) for n in ("nascence.profile", "nascence.buses")}
_lv = {n: (l.level, l.propagate) for n, l in _lgs.items()}
for _l in _lgs.values():
    _l.addHandler(_cap)
    _l.propagate = False                     # keep stderr clean; the capture is the record
_lgs["nascence.buses"].setLevel(logging.DEBUG)

import numpy as np                                             # noqa: E402,F401  (core.memory.store imports it; fail early and clearly if absent)
import core                                                    # noqa: E402
from core import profile as P                                  # noqa: E402
from core import buses                                         # noqa: E402
from core import cargo_types as CT                             # noqa: E402
from core import world_substrate as WS                         # noqa: E402
import core.memory.store as MS                                 # noqa: E402

# ── [0] resolution + surface ──────────────────────────────────────────────────────────────────────────────────────────────
print("\n[0] module resolution + surface")
for _m in (core, P, buses):
    if ROOT not in Path(_m.__file__).resolve().parents:
        print(f"ABORT: {_m.__name__} was imported from {_m.__file__}, not from this root {ROOT} (F-2423: a shared-tree import would aim every default path at the live data/)")
        sys.exit(2)
check(True, f"core, core.profile and core.buses are THIS root's ({Path(core.__file__).resolve().parent})")
_D = {a: getattr(buses, a) for a in ("_DELIVERY_LOG", "_CAL_LOG", "_STATE", "_IDLE_FREIGHT_SHADOW_LOG", "_ADVISOR_LOG", "_TRAINS_LOG", "_TRAIN_STATE_LOG")}
_orig = dict(DATA=P._DATA, CANON=P._CANONICAL_DATA, LIVE=P.LIVE, time=time.time, WS_get=WS.get_object, MS_embed=MS._embed, MS_cos=MS._cosine,
             log_delivery=buses._log_delivery)
check(getattr(buses, "profile", None) is P, "core.buses.profile is core.profile (one module object, so mark_live() reaches it)")
check(_D["_DELIVERY_LOG"] == ROOT / "data" / "buses_log.jsonl" and _D["_CAL_LOG"] == ROOT / "data" / "world_calibration.jsonl"
      and _D["_STATE"] == ROOT / "data" / "buses_state.json" and _D["_IDLE_FREIGHT_SHADOW_LOG"] == ROOT / "data" / "idle_freight_bus_shadow.jsonl",
      "the four write-path constants keep their names and __file__-relative defaults (hud/server.py and du_pulse read the same files)")


def _sig(fn):
    return [(n, p.default if p.default is not inspect.Parameter.empty else "<req>") for n, p in inspect.signature(fn).parameters.items()]


check(_sig(buses.idle_freight) == [("k", 2), ("query_text", ""), ("raw_window", None), ("cycle_id", "")], f"idle_freight's signature is unchanged {_sig(buses.idle_freight)}")
# J-4052: object_ledger_line later gained optional keyword parameters (branch, base_chars, show); the original two parameters
# and defaults are unchanged and every addition has a default, so every old call is still valid.
_osig = _sig(buses.object_ledger_line)
check(_osig[:2] == [("entity_id", "<req>"), ("max_facts", 4)] and all(d != "<req>" for _, d in _osig[2:]),
      f"object_ledger_line's original signature is unchanged (extras all optional): {_osig}")
check(_sig(buses.sync_investigation_calibration) == [] and _sig(buses._save_state) == [("d", "<req>")], "sync_investigation_calibration() / _save_state(d) signatures unchanged")
check([n for n, _ in _sig(buses.log_transfer)] == ["route", "detail"] and [n for n, _ in _sig(buses._log_delivery)] == ["route", "detail"],
      "log_transfer(route, **detail) / _log_delivery(route, **detail) signatures unchanged")
check(buses.WORLD_BUSES is True and buses.IDLE_FREIGHT_BUS is True, "the two flags (WORLD_BUSES, IDLE_FREIGHT_BUS) are untouched")
P.LIVE = False
for _n in ("buses_log.jsonl", "world_calibration.jsonl", "buses_state.json", "idle_freight_bus_shadow.jsonl"):
    try:
        P.guard_path(_LIVE_DATA / _n)
        check(False, f"guard_path refuses the REAL data/{_n} in a non-live process")
    except P.NonLiveWriteError:
        pass
check(True, "guard_path refuses all four REAL live files in a non-live process (pure check, no I/O)")
P.LIVE = True
check(all(P.guard_path(_LIVE_DATA / n) == _LIVE_DATA / n for n in ("buses_log.jsonl", "buses_state.json")), "...and hands them back untouched once live")
P.LIVE = False


# ── [1] static ratchet ────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[1] static: every write-mode open() / write_text() in core/buses.py takes a guard_path() result")


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


_bad = _unfenced_write_sites(Path(buses.__file__).read_text(encoding="utf-8"))
check(not _bad, f"no unfenced write site in core/buses.py {_bad}")
check(_unfenced_write_sites("def w(p):\n    with open(p, 'a') as f:\n        f.write('x')\n") != []
      and _unfenced_write_sites("def w():\n    _S.write_text('x')\n") != []
      and _unfenced_write_sites("def w(p):\n    q = profile.guard_path(p)\n    open(q, 'a')\n    profile.guard_path(p).write_text('x')\n    open(p)\n") == [],
      "the ratchet itself: flags a bare open(..., 'a') and a bare .write_text(), passes guard_path()-bound writers and plain reads")

# ── the pre-fence reference: the shipped functions with their guard_path(X) calls undone ─────────────────────────────────────
_SITE = re.compile(r"profile\.guard_path\((\w+)\)")
_FENCED = ("_log_delivery", "_save_state", "object_ledger_line", "sync_investigation_calibration", "log_transfer", "idle_freight")
_ref_ns = dict(vars(buses))
_sites = {}
for _name in _FENCED:
    _src, _sites[_name] = _SITE.subn(r"\1", inspect.getsource(getattr(buses, _name)))
    exec(compile(_src, f"<pre-J-1797 {_name}>", "exec"), _ref_ns)
check(_sites == {"_log_delivery": 1, "_save_state": 1, "object_ledger_line": 0, "sync_investigation_calibration": 2, "log_transfer": 0, "idle_freight": 1},
      f"the shipped module carries exactly the five guard_path sites (1 + 1 + 2 + 1) the reference undoes {_sites}")
_get_new = lambda n: getattr(buses, n)                         # noqa: E731
_get_ref = lambda n: _ref_ns[n]                                # noqa: E731

# ── fixtures ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
T0 = 1_800_000_000.0
_T = [T0]


def _freeze():
    _T[0] = T0
    time.time = lambda: _T[0]


def _jl(rows) -> str:
    return "".join((r if isinstance(r, str) else json.dumps(r, ensure_ascii=False)) + "\n" for r in rows)


ADV, ADV_EMPTY, TRAINS, TSTATE = TMP / "advisor.jsonl", TMP / "advisor_empty.jsonl", TMP / "trains_log.jsonl", TMP / "train_state_log.jsonl"
ADV.write_text(_jl([
    {"episode_id": "e1", "evidence_outcome": "CONFIRMED", "question": "does the log float", "discriminative_prediction": "it floats"},
    {"episode_id": "e2", "evidence_outcome": "CONFIRMED", "question": "already synced"},
    {"episode_id": "e3", "evidence_outcome": "UNTESTED", "question": "pending"},
    {"episode_id": "e4", "evidence_outcome": "INCONCLUSIVE", "question": "an honest non-pair"},
    {"episode_id": "e5", "evidence_outcome": "INCONCLUSIVE", "question": "early row"},
    {"episode_id": "e5", "evidence_outcome": "CONFIRMED", "question": "ünïcode ✓ later row"},
    "this line is not json",
    {"episode_id": "e6", "evidence_outcome": "REFUTED", "question": "x" * 200},
    {"no_episode": True},
]), encoding="utf-8")
ADV_EMPTY.write_text("", encoding="utf-8")
TRAINS.write_text(_jl([{"event": "open", "id": "tA", "product_type": CT.THOUGHT}, {"event": "open", "id": "tB", "product_type": CT.CONTEMPLATION},
                       {"event": "open", "id": "tC", "product_type": CT.LETTER}, {"event": "open", "id": "tD", "product_type": CT.THOUGHT},
                       {"event": "open", "id": "tE", "product_type": CT.THOUGHT}, {"event": "step", "id": "tA"}]), encoding="utf-8")
TSTATE.write_text(_jl([
    {"train_id": "tA", "thought": "the log has gone grey where the sea works at it", "ts": T0 - 3600, "restate_sim": 0.31},
    {"train_id": "tA", "thought": "the log has gone grey where the sea works at it, deeper now", "ts": T0 - 1800, "restate_sim": 0.2},
    {"train_id": "tB", "thought": "what the tide keeps and what it gives back", "ts": T0 - 900, "restate_sim": 0.9},
    {"train_id": "tC", "thought": "a letter to nobody", "ts": T0 - 100, "restate_sim": 0.1},
    {"train_id": "tD", "thought": "what the tide keeps and what it gives back", "ts": T0 - 5000, "restate_sim": 0.5},
    {"train_id": "tE", "thought": "", "ts": T0 - 50, "restate_sim": 0.5},
]), encoding="utf-8")


def _stub_embed(text):
    t = str(text)
    return [float(len(t) % 11 + 1), float(sum(map(ord, t)) % 13 + 1), float(t.count("t") + 1)]


def _stub_cos(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na, nb = sum(x * x for x in a) ** 0.5, sum(x * x for x in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


class _Obj:
    def __init__(self, obs):
        self.observations = obs


_OBS2 = [{"features": {"colour": "grey", "shape": "log"}, "timestamp": T0 - 3 * 86400.0},
         {"features": {"colour": "silver grey", "grain visibility": "faint"}, "timestamp": T0 - 3600.0}]
MS._embed, MS._cosine = _stub_embed, _stub_cos
WS.get_object = lambda eid: _Obj(_OBS2) if eid == "driftwood_17" else (_Obj(_OBS2[:1]) if eid == "x" else None)

fake = TMP / "fake_root" / "data"                  # a SIMULATED data/ root -- the real one is never a write target in sections [2], [4]-[6]
fake.mkdir(parents=True)
_KEYS = ("delivery", "cal", "state", "shadow")


def _paths(d: Path) -> dict:
    return dict(delivery=d / "buses_log.jsonl", cal=d / "world_calibration.jsonl", state=d / "buses_state.json", shadow=d / "idle_freight_bus_shadow.jsonl")


def _plant(p: dict) -> None:
    p["state"].parent.mkdir(parents=True, exist_ok=True)
    p["delivery"].write_text(_jl([{"ts": 1.0, "route": "planted", "n": i} for i in range(2)]), encoding="utf-8")
    p["cal"].write_text(_jl([{"ts": 2.0, "episode_id": "old1", "measured": 1.0}]), encoding="utf-8")
    p["state"].write_text(json.dumps({"cal_synced_ids": ["e2", "old1"]}), encoding="utf-8")
    p["shadow"].write_text(_jl([{"ts": 3.0, "planted": True}]), encoding="utf-8")


def _aim(p: dict, advisor: Path = ADV) -> None:
    for attr, val in (("_DELIVERY_LOG", p["delivery"]), ("_CAL_LOG", p["cal"]), ("_STATE", p["state"]), ("_IDLE_FREIGHT_SHADOW_LOG", p["shadow"]),
                      ("_ADVISOR_LOG", advisor), ("_TRAINS_LOG", TRAINS), ("_TRAIN_STATE_LOG", TSTATE)):
        setattr(buses, attr, val)
        _ref_ns[attr] = val


def _aim_defaults(advisor: Path = ADV) -> None:
    _aim(dict(delivery=_D["_DELIVERY_LOG"], cal=_D["_CAL_LOG"], state=_D["_STATE"], shadow=_D["_IDLE_FREIGHT_SHADOW_LOG"]), advisor)


def _fp(p: dict) -> dict:
    return {k: _snap(p[k]) for k in _KEYS}


def _bytes(p: dict) -> dict:
    return {k: (p[k].read_bytes() if p[k].exists() else None) for k in _KEYS}


def _rows(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines()) if path.exists() else 0


def _names(d: Path):
    return sorted(x.name for x in d.iterdir())


def _sequence(get) -> dict:
    r = {}
    get("log_transfer")("weather_garden", note="ünï ✓", n=3)
    r["ledger2"] = get("object_ledger_line")("driftwood_17")
    r["ledger1"] = get("object_ledger_line")("x")
    r["sync1"] = get("sync_investigation_calibration")()
    r["sync2"] = get("sync_investigation_calibration")()
    r["idle1"] = get("idle_freight")(k=2, query_text="the tide and the log", raw_window=[{"thought": "raw one", "ts": 1.0}, {"thought": "raw two", "ts": 2.0}], cycle_id="c-1")
    r["idle2"] = get("idle_freight")(k=2, query_text="", raw_window=[], cycle_id="")
    r["idle3"] = get("idle_freight")(k=2, query_text="the log", raw_window=None)
    r["idle0"] = get("idle_freight")(k=0)
    return r


_SIM = lambda: setattr(P, "_DATA", fake) or setattr(P, "_CANONICAL_DATA", fake)   # noqa: E731
_REAL = lambda: setattr(P, "_DATA", _orig["DATA"]) or setattr(P, "_CANONICAL_DATA", _orig["CANON"])   # noqa: E731

try:
    # ── [2] non-live, simulated data/ root ────────────────────────────────────────────────────────────────────────────────
    print("\n[2] non-live process, default-style paths under a simulated data/ root")
    _SIM()
    P.LIVE = False
    _freeze()
    ctl, new = _paths(fake / "nl_ctl"), _paths(fake / "nl_new")
    _plant(ctl)
    _aim(ctl)
    r_ctl = _sequence(_get_ref)
    check(_rows(ctl["delivery"]) == 2 + 9 and _rows(ctl["cal"]) == 1 + 3 and _rows(ctl["shadow"]) == 1 + 2
          and json.loads(ctl["state"].read_text())["cal_synced_ids"] != ["e2", "old1"],
          f"CONTROL: the pre-fence reference rewrites all four files in a non-live process (delivery {_rows(ctl['delivery'])} rows, calibration {_rows(ctl['cal'])}, "
          f"shadow {_rows(ctl['shadow'])}, state advanced)")
    _plant(new)
    f0, n0 = _fp(new), _names(fake / "nl_new")
    _aim(new)
    r_new = _sequence(_get_new)
    check(_fp(new) == f0, "fenced: all four files byte-identical (size + sha256) after the whole call sequence")
    check(_names(fake / "nl_new") == n0, f"fenced: no new file appeared next to them {_names(fake / 'nl_new')}")
    check(r_new["sync1"] == 0 and r_new["sync2"] == 0 and r_ctl["sync1"] == 3 and r_ctl["sync2"] == 0,
          f"sync_investigation_calibration: fenced returns 0 (nothing synced), the reference returned {r_ctl['sync1']} -- the one by-design difference")
    _same = {k: r_new[k] == r_ctl[k] for k in r_new if not k.startswith("sync")}
    check(all(_same.values()) and r_new["ledger2"].startswith(" You have looked at this before") and r_new["ledger1"] == ""
          and len(r_new["idle1"]) == 2 and len(r_new["idle2"]) == 2 and len(r_new["idle3"]) == 2 and r_new["idle0"] == [],
          f"object_ledger_line and idle_freight return exactly what the reference returned, in a non-live process {_same}")
    for fn, args in (("_log_delivery", ("route_x",)), ("log_transfer", ("route_y",)), ("_save_state", ({"cal_synced_ids": ["zz"]},))):
        try:
            ret = _get_new(fn)(*args)
            check(ret is None, f"fenced {fn}() returns None and raises nothing")
        except Exception as exc:
            check(False, f"fenced {fn}() raised {exc!r}")
    check(_fp(new) == f0, "...and still touched nothing")

    # ── [3] the module's own REAL default paths, audit hook armed ────────────────────────────────────────────────────────
    print("\n[3] the module's own default (REAL data/) paths, non-live, blocking audit hook armed")
    _REAL()
    P.LIVE = False
    _freeze()
    ATTEMPTS.clear()
    _aim_defaults()
    r3 = _sequence(_get_new)
    _aim_defaults(ADV_EMPTY)
    r3["sync_empty"] = buses.sync_investigation_calibration()
    check(not ATTEMPTS, f"fenced: the whole call sequence (incl. a sync with nothing to sync) made ZERO write attempts under any real data/ {ATTEMPTS}")
    check((ROOT / "data").exists() == _DATA_EXISTED, "fenced: ...and created no data/ directory under this root either (the shadow writer used to mkdir before it opened)")
    check(r3["sync1"] == 0 and r3["sync_empty"] == 0 and r3["ledger2"] == r_ctl["ledger2"] and r3["idle1"] == r_ctl["idle1"],
          "...and its returns are still the reference's (ledger line, idle_freight list) or the by-design 0")
    ATTEMPTS.clear()
    _aim_defaults()
    _sequence(_get_ref)
    _aim_defaults(ADV_EMPTY)
    _ref_ns["sync_investigation_calibration"]()
    _want = {"buses_log.jsonl", "world_calibration.jsonl", "buses_state.json", "idle_freight_bus_shadow.jsonl"}
    check(_attempt_names() == _want, f"CONTROL: the pre-fence reference attempts all four REAL files (blocked, never written): {sorted(_attempt_names())} ({len(ATTEMPTS)} attempts)")
    if not _DATA_EXISTED and (ROOT / "data").is_dir() and not any((ROOT / "data").iterdir()):
        _HOOK_OFF[0] = True
        try:
            (ROOT / "data").rmdir()              # the control's mkdir made this empty, git-ignored directory; every file write in it was blocked
        finally:
            _HOOK_OFF[0] = False
    ATTEMPTS.clear()

    # ── [4] live, byte for byte ───────────────────────────────────────────────────────────────────────────────────────────
    print("\n[4] live process (profile.LIVE = True): fenced == pre-fence reference, byte for byte")
    _SIM()
    P.LIVE = True
    _freeze()
    live_new, live_old = _paths(fake / "live_new"), _paths(fake / "live_old")
    for p_, get_ in ((live_new, _get_new), (live_old, _get_ref)):
        _plant(p_)
        _aim(p_)
        p_["ret"] = _sequence(get_)
    b_new, b_old = _bytes(live_new), _bytes(live_old)
    for k in _KEYS:
        check(b_new[k] is not None and b_new[k] == b_old[k], f"{k}: bytes identical to the pre-fence reference ({len(b_new[k] or b'')} B)")
    check(live_new["ret"] == live_old["ret"], "every return value identical (ledger line, sync counts 3 then 0, all four idle_freight results)")
    check(_rows(live_new["delivery"]) == 11 and _rows(live_new["cal"]) == 4 and _rows(live_new["shadow"]) == 3 and live_new["ret"]["sync1"] == 3,
          f"non-vacuous: delivery {_rows(live_new['delivery'])} rows, calibration {_rows(live_new['cal'])}, shadow {_rows(live_new['shadow'])}, sync1 {live_new['ret']['sync1']}")
    check("ünï ✓".encode("utf-8") in b_new["delivery"] and b"\\u" not in b_new["delivery"], "ensure_ascii=False content survives byte-identically")
    blocker = fake / "blocker_file"
    blocker.write_text("x")
    for tag, get_ in (("fenced", _get_new), ("pre-fence", _get_ref)):
        p_ = _paths(fake / f"io_{tag}")
        _plant(p_)
        p_["delivery"], p_["cal"] = blocker / "a.jsonl", blocker / "b.jsonl"          # parents are a FILE: real I/O errors
        _aim(p_)
        r_io = _sequence(get_)
        check(r_io["sync1"] == 0 and r_io["ledger2"].startswith(" You have looked") and len(r_io["idle1"]) == 2 and not (blocker / "a.jsonl").exists(),
              f"{tag}: real I/O errors (delivery / calibration parent is a FILE) stay fail-open: sync 0, ledger line and idle_freight still returned")
    _a, _b = _paths(fake / "io_fenced"), _paths(fake / "io_pre-fence")
    check(all(_a[k].read_bytes() == _b[k].read_bytes() for k in ("state", "shadow")), "...and the files that could be written (state, shadow) are identical between the two")

    # ── [5] legitimate redirects still write ──────────────────────────────────────────────────────────────────────────────
    print("\n[5] non-live process, legitimate redirects")
    P.LIVE = False
    lab = _paths(fake / "_lab" / "20261004_000000")
    out = _paths(TMP / "outside")
    for tag, p_ in (("data/_lab/<stamp>/ (lab_env.isolate()'s sandbox)", lab), ("a path outside data/ (a temp redirect)", out)):
        _plant(p_)
        _aim(p_)
        r5 = _sequence(_get_new)
        check(_bytes(p_) == b_new and r5 == live_new["ret"], f"{tag}: writes, bytes and returns identical to the live run")
    direct = _paths(fake / "_lab")
    _aim(direct)
    _sequence(_get_new)
    check(not any(direct[k].exists() for k in _KEYS), "data/_lab/<file> with no sandbox directory stays refused (no file created)")

    # ── [6] visibility ────────────────────────────────────────────────────────────────────────────────────────────────────
    print("\n[6] the swallowed refusal is not silent")
    vis = _paths(fake / "vis")
    _plant(vis)
    _aim(vis)
    P._warned.discard(str(vis["delivery"]))
    _cap.rows.clear()
    buses._log_delivery("a")
    buses._log_delivery("b")
    buses.log_transfer("c")
    buses.sync_investigation_calibration()
    warn = [r for r in _cap.rows if r[0] == "nascence.profile" and r[1] == logging.WARNING and "buses_log.jsonl" in r[2]]
    dbg = [r for r in _cap.rows if r[0] == "nascence.buses" and "calibration sync failed" in r[2] and "refused" in r[2]]
    check(len(warn) == 1, f"guard_path logs ONE warning per path naming buses_log.jsonl across 3 refused delivery writes ({len(warn)})")
    check(len(dbg) == 1, f"the calibration bridge logs a debug line carrying the refusal text ({len(dbg)})")
    time.time = _orig["time"]

    # ── [7] the real call site: sensorium.look('driftwood') at the shore ───────────────────────────────────────────────────
    print("\n[7] call site: the real sensorium.look('driftwood') twice at the shore, isolated store, buses on its own default paths")
    _REAL()
    P.LIVE = False
    _aim_defaults()
    MS._embed, MS._cosine, WS.get_object = _orig["MS_embed"], _orig["MS_cos"], _orig["WS_get"]
    from scripts._test_isolation import redirect_world_stores                 # noqa: E402
    redirect_world_stores(TMP, locomotion=True)
    from core import life, world_traces as WT, sound_knowledge as SK, procedures as PR, transport_manager as TM, boredom as BD   # noqa: E402
    from core import nest_gate_shadow as NGS, sensorium as S, wandering as WDR, activity_memory as AM                        # noqa: E402
    life._F, life._LEDGER, life._EVENTS, life._DATA, life._FLAGS_F = (TMP / "life_state.json", TMP / "life_ledger.jsonl", TMP / "life_events.jsonl", TMP,
                                                                      TMP / "life_flags.json")
    WT._TRACES_F, SK._LEDGER_F, NGS._LEDGER = TMP / "world_traces.json", TMP / "sound_knowledge.json", TMP / "nest_gate_shadow.jsonl"
    PR._F, PR._LOG, TM._STATE, TM._SHADOW_LOG, BD._STATE = (TMP / "procedures.json", TMP / "procedures_log.jsonl", TMP / "transport_lines.json",
                                                             TMP / "transport_shadow.jsonl", TMP / "boredom_state.json")
    for _mod, _attrs in (("core.garden", ("_F", "_LEDGER", "_EVENTS")), ("core.garden_life", ("_F", "_EVENTS")), ("core.shore_life", ("_F", "_EVENTS", "_LEDGER")),
                         ("core.wood_life", ("_F", "_EVENTS", "_LEDGER")), ("core.cat", ("_STATE_F", "_HUNT_LEDGER_F")),
                         ("core.cat_sounds", ("_LEDGER", "_FLAGS_F")), ("core.supply", ("_F", "_LOG")), ("core.fieldcraft", ("_F", "_LEDGER")),
                         ("core.garden_knowledge", ("_F",)), ("core.smell", ("_F",))):
        _m = __import__(_mod, fromlist=["x"])
        for _a in _attrs:
            if hasattr(_m, _a):
                setattr(_m, _a, TMP / f"{_mod.split('.')[-1]}_{_a.strip('_').lower()}.json")
            else:
                print("  (isolation note)", _mod, _a, "has no such attribute -- stale isolation-list entry?")
    WDR.perceive = lambda *a, **k: None                                      # no per-module path to redirect: neutralised, as life_smoke does
    AM.record = lambda *a, **k: None                                         # (it opens the shared sqlite DB directly)
    S.state.clear()
    S.state.update({"weather": "clear", "wind": "breeze", "fire": "out", "fire_fuel": 0.0, "last_event": 0, "location": "shore", "garden": S._fresh_garden()})
    ATTEMPTS.clear()
    try:
        t1, t2 = S.look("driftwood"), S.look("driftwood")
    except Exception as exc:
        t1 = t2 = f"RAISED {exc!r}"
    check(t1.startswith("You look at the big driftwood log") and "You have looked at this before" not in t1,
          f"look 1 (one observation, no ledger yet): {t1[:90]!r}")
    check("You have looked at this before" in t2 and "2 times" in t2,
          "look 2: the re-encounter ledger line is still returned in a non-live process (the delivery ROW is what is refused)")
    check(not ATTEMPTS, f"fenced: ZERO write attempts under any real data/ across the two looks {ATTEMPTS}")
    buses._log_delivery = _ref_ns["_log_delivery"]                           # CONTROL: the pre-fence delivery writer, on the module's own default path
    _ref_ns["_DELIVERY_LOG"] = _D["_DELIVERY_LOG"]
    try:
        t3 = S.look("driftwood")
    finally:
        buses._log_delivery = _orig["log_delivery"]
    check("3 times" in t3 and "buses_log.jsonl" in _attempt_names(),
          f"CONTROL: with the pre-fence _log_delivery swapped in, look 3 attempts the real buses_log.jsonl (blocked): {sorted(_attempt_names())}")
    ATTEMPTS.clear()
finally:
    for _a, _v in _D.items():
        setattr(buses, _a, _v)
    P._DATA, P._CANONICAL_DATA, P.LIVE = _orig["DATA"], _orig["CANON"], _orig["LIVE"]
    time.time = _orig["time"]
    MS._embed, MS._cosine, WS.get_object, buses._log_delivery = _orig["MS_embed"], _orig["MS_cos"], _orig["WS_get"], _orig["log_delivery"]
    for _n, _l in _lgs.items():
        _l.removeHandler(_cap)
        _l.setLevel(_lv[_n][0])
        _l.propagate = _lv[_n][1]

# ── [8] canary ────────────────────────────────────────────────────────────────────────────────────────────────────────────
print("\n[8] canary")
_after = {p: _snap(p) for p in _CANARY}
check(_after == _before, "the live buses / satisfaction / prediction-error / integrity / world files are byte-identical to the start of the run "
      + "(" + ", ".join(f"{p.name} {_after[p][0] if _after[p] else 'absent'}" for p in _CANARY[:4]) + ")")
check(buses._DELIVERY_LOG == ROOT / "data" / "buses_log.jsonl" and (ROOT / "data").exists() == _DATA_EXISTED, "the module's own paths were restored and this root's data/ directory is as it was")
shutil.rmtree(TMP, ignore_errors=True)
print(f"\n{'ALL OK' if not FAILS else f'{FAILS} FAILURE(S)'} -- {CHECKS} checks")
sys.exit(1 if FAILS else 0)
