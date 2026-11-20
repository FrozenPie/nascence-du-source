"""
Regression: core/competence.py's five writers sit behind the D-0179 write fence (J-1812 / F-2428).

The gap: record_drill_accuracy (data/capability_beliefs.json read-modify-write), CompetenceTracker._save (same file,
merge + tmp/replace), _save_surprise_log (capability_surprise.json), _append_accuracy_observation
(accuracy_observations.jsonl) and _append_stability_observation (stability_observations.jsonl) wrote with no
profile.guard_path, so a harness whose lesson ran record_drill_accuracy moved Du's real self-efficacy EMA (F-2420/F-2422).
Fix: every target resolved through guard_path before any I/O (before the READ of the read-modify-write), INSIDE each
writer's existing best-effort try; a refusal does nothing at all (record_drill_accuracy returns None, the others None).

  [1] surface  [2] leak (simulated root, CONTROL = verbatim pre-fix writers)  [3] real paths trapped
  [4] live byte-identical incl. error paths  [5] legit redirects  [6] visibility  [7] canary

  python scripts/_test_competence_fence.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import builtins
import hashlib
import json
import logging
import shutil
import sys
import tempfile
import types
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FAILS = 0


def check(cond, label):
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


def _snap(p: Path):
    return None if not p.exists() else (p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest())


_NAMES = ("capability_beliefs.json", "capability_surprise.json", "accuracy_observations.jsonl", "stability_observations.jsonl")
_LIVE_SET = tuple(Path(r"C:\Nascence") / "data" / n for n in _NAMES)
_TREE_SET = tuple(ROOT / "data" / n for n in _NAMES)
_BASE = set(_LIVE_SET) | set(_TREE_SET)
_WATCH = _BASE | {p.with_suffix(p.suffix + ".tmp") for p in _BASE}
_before = {p: _snap(p) for p in _WATCH}

import core                                      # noqa: E402  (BEFORE anything that could hijack sys.path -- F-2423)
from core import profile as P                    # noqa: E402
from core import competence as C                 # noqa: E402
from core import prediction_error as PE          # noqa: E402

check(Path(core.__file__).resolve().is_relative_to(ROOT), f"core imported from the tree under test ({core.__file__})")

TMP = Path(tempfile.mkdtemp(prefix="j1812_competence_fence_"))
_orig = dict(B=C._BELIEFS_FILE, S=C._SURPRISE_FILE, A=C._ACCURACY_OBS_FILE, T=C._STABILITY_OBS_FILE,
             DATA=P._DATA, CANON=P._CANONICAL_DATA, LIVE=P.LIVE, OBS=PE.observe, TIME=C.time)

# prediction_error.observe is separately fenced (J-1799) but in LIVE mode would write Du's real files: stub it, record calls.
OBS_CALLS = []
PE.observe = lambda *a, **k: OBS_CALLS.append((a, k))
C.time = types.SimpleNamespace(time=lambda: 1234.5)

# The pre-J-1812 writers, verbatim -- the CONTROL.
_REF_SRC = r'''
def record_drill_accuracy(domain, measured, lr=0.20, predicted=None):
    import json as _json
    try:
        data = _json.loads(_BELIEFS_FILE.read_text(encoding="utf-8")) if _BELIEFS_FILE.exists() else {}
        b = data.setdefault(domain, {"confidence": 0.5, "accuracy": None, "accuracy_count": 0,
                                     "calib_pairs": [], "domain_type": "knowledge"})
        conf = float(predicted) if predicted is not None else float(b.get("confidence", 0.5))
        b.setdefault("calib_pairs", []).append([round(conf, 3), round(float(measured), 3)])
        b["calib_pairs"] = b["calib_pairs"][-20:]
        old = b.get("accuracy")
        b["accuracy"] = round(measured if old is None else old + lr * (measured - old), 4)
        b["accuracy_count"] = int(b.get("accuracy_count", 0)) + 1
        b["last_tested"] = time.time()
        _BELIEFS_FILE.write_text(_json.dumps(data, indent=2), encoding="utf-8")
        try:
            from core import prediction_error as _pe
            _pe.observe(domain, predicted=conf, measured=float(measured),
                        event=f"On {domain}: I felt {conf:.2f} but measured {float(measured):.2f}")
        except Exception:
            pass
        return b
    except Exception as exc:
        logger.debug("[competence] drill recalibration failed: %s", exc)
        return None

def _save_surprise_log(surprises):
    try:
        _SURPRISE_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = _SURPRISE_FILE.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(surprises[-_SURPRISE_LOG_MAX:], f)
        tmp.replace(_SURPRISE_FILE)
    except Exception:
        pass

def _append_accuracy_observation(entry):
    try:
        _ACCURACY_OBS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_ACCURACY_OBS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass

def _append_stability_observation(entry):
    try:
        _STABILITY_OBS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_STABILITY_OBS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass

def tracker_save(self):
    try:
        _BELIEFS_FILE.parent.mkdir(parents=True, exist_ok=True)
        on_disk = {}
        if _BELIEFS_FILE.exists():
            try:
                on_disk = json.loads(_BELIEFS_FILE.read_text(encoding="utf-8"))
            except Exception:
                on_disk = {}
        merged = {**on_disk, **{k: b.as_dict() for k, b in self._beliefs.items()}}
        tmp = _BELIEFS_FILE.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2)
        tmp.replace(_BELIEFS_FILE)
    except Exception as exc:
        logger.debug("[competence] save failed (non-fatal): %s", exc)
'''
_ref = dict(vars(C))
exec(_REF_SRC, _ref)


class _Ns:
    """Uniform attribute access over the fenced module (C) or the verbatim control namespace (dict)."""
    def __init__(self, target):
        self._t = target

    def __getattr__(self, n):
        return self._t[n] if isinstance(self._t, dict) else getattr(self._t, n)


REF, NEW = _Ns(_ref), _Ns(C)
_ref_save = _ref["tracker_save"]
_new_save = C.CompetenceTracker._save


def _aim(b: Path, s: Path, a: Path, t: Path):
    for d in (C.__dict__, _ref):
        d["_BELIEFS_FILE"], d["_SURPRISE_FILE"], d["_ACCURACY_OBS_FILE"], d["_STABILITY_OBS_FILE"] = b, s, a, t


def _aim_dir(d: Path):
    _aim(*(d / n for n in _NAMES))


def _tracker():
    tr = C.CompetenceTracker.__new__(C.CompetenceTracker)
    tr._beliefs = {"mathematics": C.CapabilityBelief(confidence=0.7, evidence_count=3, domain_type="skill"),
                   "m\u00fasica \u97f3": C.CapabilityBelief(confidence=0.4, domain_type="skill")}
    return tr


_J4369_KEYS = ("accuracy_drill", "accuracy_drill_count", "accuracy_verdict", "accuracy_verdict_count")


def _strip_j4369(raw: bytes) -> bytes:
    """J-4369 (D-0847) additively splits accuracy into drill/verdict fields. Drop ONLY those keys from the NEW
    side's beliefs file so the byte comparison still pins every pre-existing field and the file layout."""
    try:
        obj = json.loads(raw.decode("utf-8"))
    except Exception:
        return raw
    if not isinstance(obj, dict):
        return raw
    for v in obj.values():
        if isinstance(v, dict):
            for k in _J4369_KEYS:
                v.pop(k, None)
    return json.dumps(obj, indent=2).encode("utf-8")


def _strip_ret(rets):
    """J-4369: drop only the additive drill/verdict keys from returned belief dicts before comparing."""
    return [({k: v for k, v in r.items() if k not in _J4369_KEYS} if isinstance(r, dict) else r) for r in rets]


def run_all(ns, tr_save, d: Path):
    """Drive all five writers against dir d; returns the record_drill_accuracy return values."""
    _aim_dir(d)
    rets = [ns.record_drill_accuracy("comprehension", 0.8, predicted=0.55),
            ns.record_drill_accuracy("fieldcraft", 1.0),
            ns.record_drill_accuracy("fieldcraft", 0.0)]
    tr_save(_tracker())
    ns._save_surprise_log([{"ts": 1.0, "surprise": 0.25, "domain": "x\u00e9"}])
    ns._append_accuracy_observation({"ts": 1.0, "q": "caf\u00e9 \u65e5\u672c"})
    ns._append_accuracy_observation({"ts": 2.0, "q": "two"})
    ns._append_stability_observation({"ts": 3.0, "stab": 0.5, "q": "\u00fc"})
    return rets


try:
    print("\n[1] surface")
    check(getattr(C, "profile", None) is P, "core.competence.profile is core.profile (mark_live() reaches it)")
    check(all(hasattr(C, n) for n in ("_BELIEFS_FILE", "_SURPRISE_FILE", "_ACCURACY_OBS_FILE", "_STABILITY_OBS_FILE",
                                       "record_drill_accuracy", "_save_surprise_log", "CompetenceTracker")), "public names intact")

    fake = TMP / "fake_root" / "data"
    fake.mkdir(parents=True)
    P._DATA = fake
    P._CANONICAL_DATA = fake
    P.LIVE = False

    print("\n[2] the leak (simulated data/ root, non-live)")
    OBS_CALLS.clear()
    run_all(REF, _ref_save, fake)
    check(all((fake / n).exists() for n in _NAMES), "CONTROL: pre-fix writers write all four files in a non-live process")
    check(len(OBS_CALLS) == 3, "CONTROL: pre-fix record_drill_accuracy reaches prediction_error.observe")
    for n in _NAMES:
        (fake / n).unlink()
    seeds = {n: ('{"mathematics": {"confidence": 0.5}}' if n.endswith(".json") else '{"a": 1}\n') for n in _NAMES}
    for n, v in seeds.items():
        (fake / n).write_text(v, encoding="utf-8")
    snaps = {n: _snap(fake / n) for n in _NAMES}
    listing = sorted(x.name for x in fake.iterdir())
    OBS_CALLS.clear()
    rets = run_all(NEW, _new_save, fake)
    check(rets == [None, None, None], "fenced record_drill_accuracy returns None (documented failure value), raises nothing")
    check({n: _snap(fake / n) for n in _NAMES} == snaps, "all four files byte-identical (size + sha256)")
    check(sorted(x.name for x in fake.iterdir()) == listing, "no new file appears (no .tmp leftovers)")
    check(not OBS_CALLS, "refusal precedes the read-modify-write: prediction_error.observe never reached")
    for n in _NAMES:
        (fake / n).unlink()
    run_all(NEW, _new_save, fake)
    check(not any((fake / n).exists() for n in _NAMES), "absent targets: nothing created")
    sub = fake / "sub"
    _aim_dir(sub)
    C.record_drill_accuracy("x", 0.5)
    _new_save(_tracker())
    C._save_surprise_log([])
    check(not sub.exists(), "absent parent: no mkdir")

    print("\n[3] real paths (writes trapped)")
    P._DATA, P._CANONICAL_DATA = _orig["DATA"], _orig["CANON"]
    hits = []
    real_wt, real_mk, real_open, real_rep = Path.write_text, Path.mkdir, builtins.open, Path.replace
    parents = {p.parent for p in _WATCH}

    def trap_wt(self, *a, **k):
        if Path(self) in _WATCH:
            hits.append(("write", str(self)))
            return 0
        return real_wt(self, *a, **k)

    def trap_mk(self, *a, **k):
        if Path(self) in parents:
            hits.append(("mkdir", str(self)))
            return None
        return real_mk(self, *a, **k)

    def trap_rep(self, target):
        if Path(self) in _WATCH or Path(target) in _WATCH:
            hits.append(("replace", str(target)))
            return None
        return real_rep(self, target)

    class _Null:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def write(self, *_):
            return 0

    def trap_open(f, *a, **k):
        try:
            if Path(f) in _WATCH:
                hits.append(("open", str(f)))
                return _Null()
        except TypeError:
            pass
        return real_open(f, *a, **k)

    Path.write_text, Path.mkdir, builtins.open, Path.replace = trap_wt, trap_mk, trap_open, trap_rep
    try:
        for tset in (_LIVE_SET, _TREE_SET):
            for ns, sv, bucket in ((REF, _ref_save, "ref"), (NEW, _new_save, "new")):
                _aim(*tset)
                hits.clear()
                ns.record_drill_accuracy("fieldcraft", 1.0)
                ns._save_surprise_log([])
                ns._append_accuracy_observation({})
                ns._append_stability_observation({})
                sv(_tracker())
                if bucket == "ref":
                    kinds = {h[0] for h in hits}
                    check(kinds >= {"write", "open", "mkdir", "replace"},
                          f"CONTROL pre-fix reaches real write/open/mkdir/replace ({tset[0].parent})")
                else:
                    check(not hits, f"fenced writers reach no write/mkdir/open/replace ({tset[0].parent}) {hits[:2]}")
    finally:
        Path.write_text, Path.mkdir, builtins.open, Path.replace = real_wt, real_mk, real_open, real_rep

    print("\n[4] live (profile.LIVE = True)")
    P._DATA, P._CANONICAL_DATA, P.LIVE = fake, fake, True
    seed_full = {"comprehension": {"confidence": 0.6, "accuracy": 0.9, "accuracy_count": 2,
                                   "calib_pairs": [[0.5, 0.5]], "domain_type": "knowledge"},
                 "unrelated": {"confidence": 0.1}}
    for tag, seed in (("empty", None), ("seeded", seed_full)):
        da, db = fake / f"ref_{tag}", fake / f"new_{tag}"
        for d in (da, db):
            d.mkdir()
            if seed is not None:
                (d / _NAMES[0]).write_text(json.dumps(seed), encoding="utf-8")
        OBS_CALLS.clear()
        ra = run_all(REF, _ref_save, da)
        n_ref = len(OBS_CALLS)
        OBS_CALLS.clear()
        rb = run_all(NEW, _new_save, db)
        check(_strip_ret(ra) == _strip_ret(rb), f"live return values identical ({tag})")
        check(n_ref == len(OBS_CALLS) == 3, f"live prediction_error.observe still called per drill ({tag})")
        for n in _NAMES:
            check((da / n).exists() and (_strip_j4369 if n == _NAMES[0] else (lambda b: b))((db / n).read_bytes()) == (_strip_j4369 if n == _NAMES[0] else (lambda b: b))((da / n).read_bytes()), f"live bytes identical: {n} ({tag})")
        check(sorted(x.name for x in da.iterdir()) == sorted(x.name for x in db.iterdir()), f"same file set ({tag})")
    # error paths: unparseable beliefs file, and a blocker file where a directory is needed
    for label in ("corrupt", "blocked"):
        outs = []
        for ns, sv, tag in ((REF, _ref_save, "ref"), (NEW, _new_save, "new")):
            d = fake / f"err_{label}_{tag}"
            d.mkdir()
            if label == "corrupt":
                (d / _NAMES[0]).write_text("{not json", encoding="utf-8")
                _aim_dir(d)
            else:
                (d / "blocker").write_text("x", encoding="utf-8")
                _aim_dir(d / "blocker" / "deeper")
            try:
                r = ns.record_drill_accuracy("fieldcraft", 1.0)
                sv(_tracker())
                ns._save_surprise_log([])
                ns._append_accuracy_observation({})
                ns._append_stability_observation({})
                blob = (d / _NAMES[0]).read_bytes() if label == "corrupt" else (d / "blocker").read_bytes()
                outs.append(("ok", r is None, blob))
            except Exception as exc:
                outs.append(("raised", type(exc).__name__, None))
        check(outs[0] == outs[1] and outs[0][0] == "ok", f"live {label}: fail-open, identical to pre-fix ({outs[1][:2]})")

    print("\n[5] legit redirects (non-live)")
    P.LIVE = False
    lab = fake / "_lab" / "20261005_000000"
    lab.mkdir(parents=True)
    run_all(NEW, _new_save, lab)
    check(all((lab / n).exists() for n in _NAMES), "data/_lab/<stamp>/ sandbox still writes all four files")
    out = TMP / "elsewhere"
    out.mkdir()
    run_all(NEW, _new_save, out)
    check(all((out / n).exists() for n in _NAMES), "a path outside data/ still writes all four files")
    direct = fake / "_lab"
    run_all(NEW, _new_save, direct)
    check(not any((direct / n).exists() for n in _NAMES), "data/_lab/<file> directly stays refused")

    print("\n[6] visibility")
    P._warned.clear()

    class H(logging.Handler):
        def __init__(self):
            super().__init__(logging.DEBUG)
            self.recs = []

        def emit(self, r):
            self.recs.append(r)

    h = H()
    lg = logging.getLogger("nascence.competence")
    old = lg.level
    lg.setLevel(logging.DEBUG)
    logging.getLogger().addHandler(h)
    lg.addHandler(h)
    for _ in range(2):
        run_all(NEW, _new_save, fake)
    logging.getLogger().removeHandler(h)
    lg.removeHandler(h)
    lg.setLevel(old)
    warns = [r for r in h.recs if r.levelno == logging.WARNING and "refused" in r.getMessage()]
    dbg = [r for r in h.recs if r.name == "nascence.competence" and "failed" in r.getMessage()]
    check(len(warns) == 4, f"one guard WARNING per path (4 paths) (got {len(warns)})")
    check(len(dbg) >= 14, f"competence debug lines carry the refusals (got {len(dbg)})")
finally:
    C._BELIEFS_FILE, C._SURPRISE_FILE, C._ACCURACY_OBS_FILE, C._STABILITY_OBS_FILE = _orig["B"], _orig["S"], _orig["A"], _orig["T"]
    C.time = _orig["TIME"]
    PE.observe = _orig["OBS"]
    P._DATA, P._CANONICAL_DATA, P.LIVE = _orig["DATA"], _orig["CANON"], _orig["LIVE"]
    shutil.rmtree(TMP, ignore_errors=True)

print("\n[7] canary")
check({p: _snap(p) for p in _WATCH} == _before, "real competence data files byte-identical to the start")
print("\nALL OK" if FAILS == 0 else f"\n{FAILS} FAILED")
sys.exit(0 if FAILS == 0 else 1)
