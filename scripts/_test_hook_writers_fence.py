"""
Regression: core/watershed.py, core/geometry_census.py, core/loop_probe.py, core/retrieval_probe.py and core/r_shadow.py sit
behind the D-0179 write fence (J-1815 / F-2428; the F-2406 shape for the store_fragment()/retrieve() observe-only hooks).

The gap: these five modules' write targets are plain __file__-relative module constants and their writers never went through
profile.guard_path, so ANY process that merely imported core.memory.store from the shared tree and called store_fragment()/retrieve()
(lab_env.isolate() redirects only store.DB_PATH) wrote Du's REAL data/watershed_state.json, watershed_shadow.jsonl,
geometry_tuples.jsonl, loop_probe_log.jsonl, retrieval_probe_log.jsonl and r_shadow.jsonl.

The build: every writer resolves its target through profile.guard_path BEFORE any I/O, INSIDE its existing fail-open try (all five are
observe-only hooks; store.py wraps every call site in try/except too). geometry_census.snapshot swallows the refusal locally (returns
None) instead of re-raising, because its four callers were not audited for a new raise. core/arousal.py is deliberately NOT fenced
(the non-live HUD server legitimately appends data/arousal_shadow.jsonl). A LIVE process gets the same paths back: byte-identical.

ISOLATED: every write goes to a temp dir or a SIMULATED data/ root, or is TRAPPED (recorded, never executed) when aimed at the REAL
data/ trees; live files are hashed before and after. Safe to run from any tree, including against the pre-fix modules (it must FAIL).

  python scripts/_test_hook_writers_fence.py        # exit 0 = ALL OK
"""
from __future__ import annotations
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/

import builtins
import hashlib
import importlib.util
import itertools
import json
import pathlib
import subprocess
import sys
import tempfile
import time
import types
import uuid
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402  -- BEFORE every other core import, and asserted (F-2423)
_core_file = Path(core.__file__).resolve()
assert ROOT in _core_file.parents, f"core resolves to {_core_file}, not inside {ROOT} -- refusing to run"

TMP = Path(tempfile.mkdtemp(prefix="j1815_fence_"))
BASE = "8ca9b43"   # the commit these modules were fenced on top of: pre-fix source for the live byte-identity comparison
print("core package:", _core_file)
print("isolated dir:", TMP)

FAILS = 0


def check(cond: bool, label: str) -> None:
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


_LIVE_DATA = Path(r"C:\Nascence") / "data"
_NAMES = ("watershed_state.json", "watershed_shadow.jsonl", "geometry_tuples.jsonl", "loop_probe_log.jsonl",
          "retrieval_probe_log.jsonl", "r_shadow.jsonl")
_WATCH = {_LIVE_DATA / n for n in _NAMES} | {ROOT / "data" / n for n in _NAMES} | {
    _LIVE_DATA / "satisfaction_log.jsonl", _LIVE_DATA / "prediction_error_log.jsonl",
    _LIVE_DATA / "logs" / "shadow_integrity.jsonl", _LIVE_DATA / "buses_log.jsonl"}


def _snap(p: Path):
    if not p.exists():
        return None
    b = p.read_bytes()
    return (len(b), hashlib.sha256(b).hexdigest())


_before = {p: _snap(p) for p in _WATCH}

from core import profile as P  # noqa: E402
from core import watershed as ws, geometry_census as gc, loop_probe as lp, retrieval_probe as rp, r_shadow as rs  # noqa: E402

_REAL_ROOTS = (str(_LIVE_DATA).lower(), str((ROOT / "data")).lower())
TRAPPED: list[str] = []


def _is_real(p) -> bool:
    try:
        s = str(Path(p).resolve()).lower()
    except Exception:
        s = str(p).lower()
    return any(s.startswith(r) for r in _REAL_ROOTS)


_real_open, _real_wt, _real_mkdir, _real_replace, _real_popen = builtins.open, Path.write_text, Path.mkdir, Path.replace, Path.open
_trap_on = False


def _open(f, mode="r", *a, **k):
    if _trap_on and isinstance(f, (str, Path)) and any(c in mode for c in "wax+") and _is_real(f):
        TRAPPED.append(f"open({f}, {mode})")
        raise OSError("trapped real-path write")
    return _real_open(f, mode, *a, **k)


def _popen(self, mode="r", *a, **k):
    if _trap_on and any(c in mode for c in "wax+") and _is_real(self):
        TRAPPED.append(f"Path.open({self}, {mode})")
        raise OSError("trapped real-path write")
    return _real_popen(self, mode, *a, **k)


def _wt(self, *a, **k):
    if _trap_on and _is_real(self):
        TRAPPED.append(f"write_text({self})")
        raise OSError("trapped real-path write")
    return _real_wt(self, *a, **k)


def _mk(self, *a, **k):
    if _trap_on and _is_real(self):
        TRAPPED.append(f"mkdir({self})")
        raise OSError("trapped real-path mkdir")
    return _real_mkdir(self, *a, **k)


def _rep(self, *a, **k):
    if _trap_on and _is_real(self):
        TRAPPED.append(f"replace({self})")
        raise OSError("trapped real-path replace")
    return _real_replace(self, *a, **k)


builtins.open, Path.write_text, Path.mkdir, Path.replace, Path.open = _open, _wt, _mk, _rep, _popen

# stubs for the sensor/arousal reads geometry_census.snapshot makes (arousal.level() would append the unfenced HUD sampler's live log)
import core.arousal as _arousal  # noqa: E402
import core.soundscape as _snd  # noqa: E402
_arousal.level = lambda *a, **k: 0.5
_snd.active_sounds = lambda *a, **k: [{"s": "rain"}]


def _stub_census(mod):
    mod._place_weather = lambda: {"place": "study", "weather": {"sky": "clear"}}
    mod._objects = lambda: {"lamp": 1}
    mod._body = lambda state=None: {"tired": 0.2}
    mod._affect = lambda state=None: {"valence": 0.1}
    mod._warmth = lambda: 0.5
    mod._cat_at = lambda: "sofa"
    mod._light_band_truth = lambda: "day"
    mod._smells_truth = lambda: ["tea"]


_stub_census(gc)


def _load_old(name: str):
    """The pre-fix module source (git show BASE:core/<name>.py) as a fresh module, or None if unavailable."""
    try:
        src = subprocess.run(["git", "show", f"{BASE}:core/{name}.py"], cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8")
    except Exception as exc:
        print(f"   (cannot load pre-fix {name}: {exc})")
        return None
    mod = types.ModuleType(f"_old_{name}")
    mod.__file__ = str(ROOT / "core" / f"{name}.py")
    mod.__package__ = "core"
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    return mod


def tree(root: Path):
    out = {}
    if root.exists():
        for p in sorted(root.rglob("*")):
            if p.is_file():
                out[str(p.relative_to(root))] = p.read_bytes()
    return out


# deterministic clock + uuid, restored in finally
_real_time, _real_uuid4 = time.time, uuid.uuid4


class _Clock:
    def __init__(self):
        self.t = 1_800_000_000.0

    def __call__(self):
        self.t += 7.0
        return self.t


def deterministic():
    clk = _Clock()
    cnt = itertools.count(1)
    time.time = clk
    uuid.uuid4 = lambda: uuid.UUID(int=next(cnt))


def undeterministic():
    time.time, uuid.uuid4 = _real_time, _real_uuid4


_orig = dict(ws=(ws._DATA, ws._STATE, ws._LOG), gc=gc._LOG, lp=lp._LOG, rp=rp._LOG, rs=rs._SHADOW_LOG,
             DATA=P._DATA, CANON=P._CANONICAL_DATA, LIVE=P.LIVE, seen=lp._seen)


def restore():
    ws._DATA, ws._STATE, ws._LOG = _orig["ws"]
    gc._LOG, lp._LOG, rp._LOG, rs._SHADOW_LOG = _orig["gc"], _orig["lp"], _orig["rp"], _orig["rs"]
    P._DATA, P._CANONICAL_DATA, P.LIVE = _orig["DATA"], _orig["CANON"], _orig["LIVE"]
    lp._seen = _orig["seen"]
    ws.configure()
    undeterministic()


def aim(root: Path, w=ws, g=gc, l=lp, r=rp, s=rs):
    """Point the five modules (or their pre-fix twins) at `root` and make the fence treat `root` as the data root."""
    w._DATA = root
    w._STATE = root / "watershed_state.json"
    w._LOG = root / "watershed_shadow.jsonl"
    w._state_cache, w._last_observe, w._batch_mode = None, 0.0, False
    g._LOG = root / "geometry_tuples.jsonl"
    g._last_ts, g._last_thought = 0.0, ""
    l._LOG = root / "loop_probe_log.jsonl"
    l._seen = {}
    r._LOG = root / "retrieval_probe_log.jsonl"
    s._SHADOW_LOG = root / "r_shadow.jsonl"


def drive(w=ws, g=gc, l=lp, r=rp, s=rs):
    """A fixed sequence through every writer, incl. an error-path-ish repeat; returns the observable return values."""
    rets = []
    vec1, vec2 = [1.0, 0.0, 0.0], [0.9, 0.1, 0.0]
    rets.append(w.observe("a recurring image of the lamp in the window at night", vec=vec1, _cooldown=False))
    rets.append(w.observe("the lamp in the window again tonight, same image", vec=vec2, _cooldown=False))
    rets.append(w.observe("short", vec=vec1, _cooldown=False))                       # skip row
    w.begin_batch(); w.observe("batched thought about the same lamp image here", vec=vec1, _cooldown=False); w.flush_state()
    rets.append(g.snapshot(source="inner_thought", thought="a thought", unresolved=True))
    rets.append(g.snapshot(source="inner_thought", thought="a different thought"))
    l.shadow_observe("inner_thought", "same words"); l.shadow_observe("inner_thought", "same words"); l.shadow_observe("reading", "ignored")
    pool = [(0.9, "reading", "f1"), (0.5, "lived", "f2")]
    r.observe("what is the tide today", pool, {"f2"}, [{"fragment_id": "f1", "content": "tide table"}])
    results = [(0.8, {"timestamp": _real_time() - 100}), (0.7, {"timestamp": _real_time() - 90 * 86400})]
    rets.append(s.log_observation("retrieve:recent", results, pool=[row for _, row in results], now_ts=1_800_000_500.0))
    return json.dumps(rets, sort_keys=True, default=str)


try:
    # [1] surface
    print("[1] surface")
    for m in (ws, gc, lp, rp, rs):
        check(getattr(m, "profile", None) is P or "guard_path(" in Path(m.__file__).read_text(encoding="utf-8"), f"{m.__name__} calls guard_path")
    check("guard_path(" not in (ROOT / "core" / "arousal.py").read_text(encoding="utf-8"), "core/arousal.py is deliberately NOT fenced (HUD sampler)")

    # [2] non-live, DEFAULT module constants (the real data/ trees), real-path writes trapped
    print("[2] non-live refusal: default constants -> real data/ writes trapped")
    P.LIVE = False
    deterministic()
    _trap_on = True
    for p in (_LIVE_DATA / "watershed_state.json", _LIVE_DATA / "r_shadow.jsonl"):
        try:
            P.guard_path(p); check(False, f"guard_path refuses {p.name}")
        except P.NonLiveWriteError:
            check(True, f"guard_path refuses {p.name}")
    ws.configure(); lp._seen = {}
    drive()
    _trap_on = False
    check(not TRAPPED, f"no real-path write attempted by any of the five writers (trapped: {TRAPPED[:4]})")
    undeterministic()

    # [3] non-live, simulated data/ root: nothing written, nothing created
    print("[3] non-live refusal: simulated data/ root")
    fake = TMP / "fake_root" / "data"
    fake.mkdir(parents=True)
    (fake / "r_shadow.jsonl").write_bytes(b'{"old": 1}\n')
    aim(fake)
    P._DATA = P._CANONICAL_DATA = fake
    P.LIVE = False
    pre = tree(fake)
    deterministic()
    drive()
    undeterministic()
    check(tree(fake) == pre, "non-live: every simulated-data file byte-identical, no new file")

    # [4] LIVE: byte-identical to the pre-fix writers over a fixed-clock sequence
    print("[4] LIVE=True byte-identical to the pre-fix source")
    old = {n: _load_old(n) for n in ("watershed", "geometry_census", "loop_probe", "retrieval_probe", "r_shadow")}
    if all(old.values()):
        _stub_census(old["geometry_census"])
        la, lb = TMP / "live_new" / "data", TMP / "live_old" / "data"
        la.mkdir(parents=True); lb.mkdir(parents=True)
        P.LIVE = True
        aim(la)
        deterministic(); r_new = drive(); undeterministic()
        aim(lb, old["watershed"], old["geometry_census"], old["loop_probe"], old["retrieval_probe"], old["r_shadow"])
        deterministic(); r_old = drive(old["watershed"], old["geometry_census"], old["loop_probe"], old["retrieval_probe"], old["r_shadow"]); undeterministic()
        ta, tb = tree(la), tree(lb)
        check(set(ta) == set(tb) and len(ta) >= 6, f"same file set ({sorted(ta)})")
        check(ta == tb, "all bytes identical (rows, indent, line endings)")
        check(r_new == r_old, "identical return values")
        # error path: parent of every target is a regular file -> writers swallow, same return values, nothing raised
        ea, eb = TMP / "err_new" / "data", TMP / "err_old" / "data"
        for d in (ea, eb):
            d.parent.mkdir(parents=True); d.write_bytes(b"i am a file, not a dir")
        aim(ea); deterministic(); e_new = drive(); undeterministic()
        aim(eb, old["watershed"], old["geometry_census"], old["loop_probe"], old["retrieval_probe"], old["r_shadow"])
        deterministic(); e_old = drive(old["watershed"], old["geometry_census"], old["loop_probe"], old["retrieval_probe"], old["r_shadow"]); undeterministic()
        check(e_new == e_old, "LIVE error path (blocked parent dir): identical return values, nothing raised")
    else:
        check(False, "pre-fix sources loadable for the byte-identity comparison")

    # [5] allow-list: lab sandbox and outside-data paths still write, data/_lab/<file> stays refused
    print("[5] redirect/sandbox behaviour")
    P.LIVE = False
    fake2 = TMP / "fake2" / "data"
    (fake2 / "_lab" / "20261005_000000").mkdir(parents=True)
    P._DATA = P._CANONICAL_DATA = fake2
    sb = fake2 / "_lab" / "20261005_000000"
    aim(sb)
    deterministic(); drive(); undeterministic()
    check(all((sb / n).exists() for n in _NAMES), "data/_lab/<stamp>/ sandbox: all six files written")
    outside = TMP / "outside_data"
    outside.mkdir()
    aim(outside)
    deterministic(); drive(); undeterministic()
    check(all((outside / n).exists() for n in _NAMES), "path outside data/ (configure(data_dir=tmp)): all six files written")
    aim(fake2 / "_lab")
    P._DATA = P._CANONICAL_DATA = fake2
    deterministic(); drive(); undeterministic()
    check(not any((fake2 / "_lab" / n).exists() for n in _NAMES), "data/_lab/<file> (not a sandbox dir) stays refused")

    # [6] watershed.configure(data_dir=tmp) keeps working for a non-live replay (watershed_retro_validate's contract)
    print("[6] watershed.configure redirect")
    d = TMP / "cfg"
    ws.configure(data_dir=str(d))
    P._DATA = P._CANONICAL_DATA = fake2
    deterministic()
    ws.observe("a replayed thought that is long enough to count here", vec=[1.0, 0.0], _cooldown=False)
    undeterministic()
    check((d / "watershed_state.json").exists() and (d / "watershed_shadow.jsonl").exists(), "configure(data_dir=tmp) state + log written non-live")
    src = (ROOT / "scripts" / "watershed_retro_validate.py").read_text(encoding="utf-8")
    check('"data" / "_lab" / "watershed_retro"' in src, "watershed_retro_validate LAB sits in the allow-listed data/_lab/ sandbox")
finally:
    _trap_on = False
    builtins.open, Path.write_text, Path.mkdir, Path.replace, Path.open = _real_open, _real_wt, _real_mkdir, _real_replace, _real_popen
    restore()

_after = {p: _snap(p) for p in _WATCH}
# INFORMATIONAL only: a running Du legitimately appends to these live files, so a hash diff cannot prove a leak. The proof is the
# trap in [2] (every real-path write by these writers is recorded and refused) plus the simulated-root byte-equality in [3].
_chg = sorted(p.name for p in _WATCH if _before[p] != _after[p])
print("   (info) live files whose bytes moved during this run (a running Du writes them itself):", _chg or "none")
print("ALL OK" if FAILS == 0 else f"{FAILS} FAILED")
sys.exit(1 if FAILS else 0)
