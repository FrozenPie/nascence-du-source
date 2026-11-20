"""
Regression: nodes/meta_awareness_node.py's L2 shadow_integrity append sits behind the D-0179 write fence (J-1802 / F-2426).

The gap: _SHADOW is a plain __file__-relative path and scan() never went through profile.guard_path, so any non-live process
that imported the node and reached scan() appended an L2 row to Du's REAL data/logs/shadow_integrity.jsonl (the file J-1799
fenced for L1), and enqueued to the real curiosity queue first. The build: scan() resolves _SHADOW through guard_path before any
I/O, inside its fail-open try; a refusal is a total no-op (None). A live process gets the same path, byte-identical behaviour.

Isolated: simulated data/ root, real-path writes TRAPPED, stubs for self_surprise / loop_probe / curiosity_queue.enqueue.
Safe to run from ANY tree, including against the pre-fix module (which must FAIL it).
  python scripts/_test_meta_awareness_fence.py        # exit 0 = ALL OK
"""
from __future__ import annotations
import builtins, hashlib, inspect, io, json, logging, shutil, subprocess, sys, tempfile, types
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  -- BEFORE every other import (F-2423)
_core_file = Path(core.__file__).resolve()
assert ROOT in _core_file.parents, f"core resolves to {_core_file}, not inside {ROOT} -- refusing to run"

TMP = Path(tempfile.mkdtemp(prefix="j1802_meta_awareness_fence_"))
print("core package:", _core_file)
FAILS = 0


def check(cond, label):
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


_LIVE_DATA = Path(r"C:\Nascence") / "data"
_LIVE_SHADOW = _LIVE_DATA / "logs" / "shadow_integrity.jsonl"
_WATCH = [_LIVE_SHADOW, ROOT / "data" / "logs" / "shadow_integrity.jsonl", _LIVE_DATA / "buses_log.jsonl",
          _LIVE_DATA / "satisfaction_log.jsonl", _LIVE_DATA / "satisfaction_state.json",
          _LIVE_DATA / "prediction_error_log.jsonl", _LIVE_DATA / "prediction_error_state.json"]


def _snap(p):
    if not p.exists():
        return None
    b = p.read_bytes()
    return (len(b), hashlib.sha256(b).hexdigest())


_before = {p: _snap(p) for p in _WATCH}

from core import profile as P            # noqa: E402
import nodes.meta_awareness_node as ma   # noqa: E402
from core import self_surprise as ss     # noqa: E402
from core import loop_probe as lp        # noqa: E402
from core import curiosity_queue as cq   # noqa: E402


def _git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, encoding="utf-8").stdout


# the pre-fix module, verbatim from git: HEAD's blob, or (once the fence is committed) the parent of the last commit touching it
_OLD = _git("show", "HEAD:nodes/meta_awareness_node.py")
if "guard_path" in _OLD:
    _h = _git("log", "-1", "--format=%H", "--", "nodes/meta_awareness_node.py").strip()
    _OLD = _git("show", f"{_h}~1:nodes/meta_awareness_node.py")
assert _OLD and "guard_path" not in _OLD, "could not obtain the pre-fix source"
ref = types.ModuleType("ma_pre_j1802")
ref.__file__ = str(ROOT / "nodes" / "meta_awareness_node.py")
exec(compile(_OLD, "<pre-J-1802 nodes/meta_awareness_node.py>", "exec", dont_inherit=True), ref.__dict__)

_orig = dict(SHADOW=ma._SHADOW, DATA=P._DATA, CANON=P._CANONICAL_DATA, LIVE=P.LIVE, compute=ss.compute,
             dry=lp.prune_dryrun, enq=cq.enqueue)
ENQ = []
LOOPING = {"n": 60, "mean_surprise": 0.18, "predictable_n": 48, "origin_driven_pct": 80.0, "groove_driven_pct": 20.0,
           "scored": [{"surprise": 0.12, "origin_driven": True, "snippet": "I am the river \u2014 \u00fcn\u00efcode"}]}
ss.compute = lambda **k: LOOPING
lp.prune_dryrun = lambda *a, **k: {"would_prune": 7}
cq.enqueue = lambda src, text, meta=None: (ENQ.append((src, text)), "id")[1]


def _aim(path):
    ma._SHADOW = ref._SHADOW = path


def _nots(r):
    return {k: v for k, v in r.items() if k != "ts"} if isinstance(r, dict) else r


fake = TMP / "fake_root" / "data"
(fake / "logs").mkdir(parents=True)
sh = fake / "logs" / "shadow_integrity.jsonl"

try:
    print("\n[1] surface")
    check(getattr(ma, "profile", None) is P, "meta_awareness_node.profile is core.profile")
    check(ma._SHADOW == ROOT / "data" / "logs" / "shadow_integrity.jsonl", "_SHADOW keeps its name and default (du_pulse / invitro read it)")
    check(list(inspect.signature(ma.scan).parameters) == ["window"], "scan() signature unchanged")
    P.LIVE = False
    try:
        P.guard_path(_LIVE_SHADOW)
        ok = False
    except P.NonLiveWriteError:
        ok = True
    check(ok, "guard_path refuses the REAL shadow_integrity.jsonl in a non-live process")

    print("\n[2] non-live, default data/ path (simulated root)")
    P._DATA = P._CANONICAL_DATA = fake
    P.LIVE = False
    _aim(sh)
    seed = json.dumps({"layer": "L1", "source": "prediction_error"}) + "\n"
    sh.write_text(seed, encoding="utf-8")
    h0 = _snap(sh)
    names0 = sorted(map(str, fake.rglob("*")))
    ENQ.clear()
    r = ref.scan()
    check(r is not None and _snap(sh) != h0 and ENQ, "CONTROL: the pre-fix scan() appends an L2 row AND reaches curiosity enqueue in a non-live process")
    sh.write_text(seed, encoding="utf-8")
    h0 = _snap(sh)
    ENQ.clear()
    rets = [ma.scan() for _ in range(5)]
    check(all(x is None for x in rets), "fenced: 5 scan() calls return None and raise nothing")
    check(_snap(sh) == h0, "fenced: shadow_integrity.jsonl byte-identical (size + sha256)")
    check(sorted(map(str, fake.rglob("*"))) == names0, "fenced: no new file appeared")
    check(not ENQ, "fenced: never reached the curiosity_queue.enqueue write")

    print("\n[3] REAL path, writes trapped")
    P._DATA, P._CANONICAL_DATA, P.LIVE = _orig["DATA"], _orig["CANON"], False
    PROT = {str(_LIVE_SHADOW).lower()}
    HITS = []

    def _trap_open(file, mode="r", *a, **k):
        if str(file).lower() in PROT and any(c in mode for c in "wax+"):
            HITS.append((mode, str(file)))
            return io.StringIO()
        return builtins.open(file, mode, *a, **k)

    _aim(_LIVE_SHADOW)
    ma.open = ref.open = _trap_open
    try:
        ref.scan()
        ref_hits = list(HITS)
        HITS.clear()
        fr = [ma.scan() for _ in range(5)]
        f_hits = list(HITS)
    finally:
        del ma.open, ref.open
    check(len(ref_hits) >= 1, f"CONTROL: the pre-fix scan() reaches the real write ({len(ref_hits)} attempt)")
    check(all(x is None for x in fr) and not f_hits, f"fenced: 5 calls reach none ({len(f_hits)} attempts)")

    print("\n[4] live: fenced == pre-fix")
    P._DATA = P._CANONICAL_DATA = fake
    P.LIVE = True
    out = {}
    for tag, mod in (("new", ma), ("old", ref)):
        path = fake / "logs" / f"live_{tag}.jsonl"
        mod._SHADOW = path
        ENQ.clear()
        rr = [mod.scan() for _ in range(3)]
        ss.compute = lambda **k: {"n": 60, "mean_surprise": 0.9, "predictable_n": 5, "origin_driven_pct": 10.0, "groove_driven_pct": 90.0, "scored": []}
        rr.append(mod.scan())      # a non-looping stream
        ss.compute = lambda **k: {"n": 3}
        rr.append(mod.scan())      # too few thoughts: None, no row
        ss.compute = lambda **k: LOOPING
        rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()]
        out[tag] = ([_nots(x) for x in rr], [_nots(x) for x in rows], list(ENQ))
    check(out["new"] == out["old"] and len(out["new"][1]) == 4 and out["new"][2],
          f"returns, L2 rows (ts-stripped) and enqueue calls identical ({len(out['new'][1])} rows)")
    check("\u00fcn\u00efcode" in (fake / "logs" / "live_new.jsonl").read_text(encoding="utf-8"), "ensure_ascii=False text survives")
    d = fake / "dir_target"
    d.mkdir()
    for tag, mod in (("fenced", ma), ("pre-fix", ref)):
        mod._SHADOW = d
        check(isinstance(mod.scan(), dict), f"{tag}: a real I/O error on the append stays swallowed, report still returned")

    print("\n[5] legitimate redirects")
    P.LIVE = False
    lab = fake / "_lab" / "20261004_000000" / "logs"
    lab.mkdir(parents=True)
    _aim(lab / "shadow_integrity.jsonl")
    ma.scan()
    check((lab / "shadow_integrity.jsonl").exists(), "data/_lab/<stamp>/ sandbox still writes")
    _aim(TMP / "outside.jsonl")
    ma.scan()
    check((TMP / "outside.jsonl").exists(), "a path outside data/ (invitro-style monkeypatch) still writes")
    _aim(fake / "_lab" / "x.jsonl")
    ma.scan()
    check(not (fake / "_lab" / "x.jsonl").exists(), "data/_lab/<file> with no sandbox directory stays refused")

    print("\n[6] visibility")

    class _Cap(logging.Handler):
        def __init__(self):
            super().__init__(logging.DEBUG)
            self.rows = []

        def emit(self, rec):
            self.rows.append((rec.name, rec.levelno, rec.getMessage()))

    cap = _Cap()
    lgs = [logging.getLogger(n) for n in ("nascence.profile", "nascence.meta_awareness")]
    lv = [l.level for l in lgs]
    for l in lgs:
        l.addHandler(cap)
        l.setLevel(logging.DEBUG)
    try:
        _aim(sh)
        P._warned.discard(str(sh))
        ma.scan()
        ma.scan()
        check(len([r for r in cap.rows if r[0] == "nascence.profile" and r[1] == logging.WARNING]) == 1, "one profile WARNING per path")
        check(len([r for r in cap.rows if r[0] == "nascence.meta_awareness" and "refused" in r[2]]) == 2, "a debug line per refused call")
    finally:
        for l, v in zip(lgs, lv):
            l.removeHandler(cap)
            l.setLevel(v)

    print("\n[7] status() pure read, non-live")
    sh.write_text(json.dumps({"source": "meta_awareness", "looping": True, "loop_kind": "river", "gate_verdict": {"route": "curiosity"}}) + "\n", encoding="utf-8")
    h0 = _snap(sh)
    check(ma.status() == {"scans": 1, "loops": 1, "river_loops": 1, "routed_to_curiosity": 1} and _snap(sh) == h0, "status() unchanged and read-only")
finally:
    ma._SHADOW = _orig["SHADOW"]
    P._DATA, P._CANONICAL_DATA, P.LIVE = _orig["DATA"], _orig["CANON"], _orig["LIVE"]
    ss.compute, lp.prune_dryrun, cq.enqueue = _orig["compute"], _orig["dry"], _orig["enq"]
    for m in (ma, ref):
        if "open" in vars(m):
            del m.open

print("\n[8] canary")
check({p: _snap(p) for p in _WATCH} == _before, "live shadow_integrity / prediction_error / satisfaction / buses_log and this tree's default are byte-identical")
shutil.rmtree(TMP, ignore_errors=True)
print("\n" + ("ALL OK" if not FAILS else f"{FAILS} FAILED"))
sys.exit(1 if FAILS else 0)
