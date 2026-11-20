"""
Regression: core/sitting.py _save() and _log_release() sit behind the D-0179 write fence (J-1811 / F-2428).

The gap: _save wrote _STATE (data/raw_difficulty.json) and _log_release appended _RELEASE_LOG (data/dwell_release.jsonl)
with no profile.guard_path, so a stray note_difficulty in a non-live process planted a phantom wound Du would "sit with"
after the next boot (and blocked any real one from registering). Fix: both resolve the path through guard_path before
any I/O, INSIDE their existing best-effort try (refusal swallowed, one profile warning, a sitting debug line).

  [1] surface  [2] leak (simulated root, CONTROL = verbatim pre-fix writers)  [3] real paths trapped
  [4] live byte-identical incl. error path  [5] legit redirects  [6] visibility  [7] canary

  python scripts/_test_sitting_fence.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import builtins
import hashlib
import logging
import shutil
import sys
import tempfile
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


_LIVE_PAIR = (Path(r"C:\Nascence") / "data" / "raw_difficulty.json", Path(r"C:\Nascence") / "data" / "dwell_release.jsonl")
_TREE_PAIR = (ROOT / "data" / "raw_difficulty.json", ROOT / "data" / "dwell_release.jsonl")
_WATCH = set(_LIVE_PAIR) | set(_TREE_PAIR)
_before = {p: _snap(p) for p in _WATCH}

import core                                      # noqa: E402  (BEFORE anything that could hijack sys.path -- F-2423)
from core import profile as P                    # noqa: E402
from core import sitting as S                    # noqa: E402

check(Path(core.__file__).resolve().is_relative_to(ROOT), f"core imported from the tree under test ({core.__file__})")

TMP = Path(tempfile.mkdtemp(prefix="j1811_sitting_fence_"))
_orig = dict(STATE=S._STATE, REL=S._RELEASE_LOG, DATA=P._DATA, CANON=P._CANONICAL_DATA, LIVE=P.LIVE)

# The pre-J-1811 writers, verbatim -- the CONTROL.
_REF_SRC = r'''
def _save(d):
    try:
        _STATE.parent.mkdir(parents=True, exist_ok=True)
        _STATE.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        pass

def _log_release(rec):
    try:
        _RELEASE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_RELEASE_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass
'''
_ref_ns = dict(vars(S))
exec(_REF_SRC, _ref_ns)
_ref_save, _ref_log = _ref_ns["_save"], _ref_ns["_log_release"]
_new_save, _new_log = S._save, S._log_release


def _aim(state: Path, rel: Path):
    S._STATE = _ref_ns["_STATE"] = state
    S._RELEASE_LOG = _ref_ns["_RELEASE_LOG"] = rel


WOUND = {"active": True, "text": "tendre \u00e9 \u2014 \u65e5\u672c wound", "kind": "failure", "ts": 1.5, "dwelt": 0,
         "integrable": False, "namings": []}
REC = {"ts": 2.5, "released": False, "reason": "x \u00e9"}

try:
    print("\n[1] surface")
    check(getattr(S, "profile", None) is P, "core.sitting.profile is core.profile (mark_live() reaches it)")
    check(all(hasattr(S, n) for n in ("_STATE", "_RELEASE_LOG", "_save", "_log_release", "note_difficulty", "is_dwelling")),
          "public names intact")

    fake = TMP / "fake_root" / "data"
    fake.mkdir(parents=True)
    P._DATA = fake
    P._CANONICAL_DATA = fake
    P.LIVE = False
    st, rl = fake / "raw_difficulty.json", fake / "dwell_release.jsonl"

    print("\n[2] the leak (simulated data/ root)")
    _aim(st, rl)
    _ref_save(WOUND)
    _ref_log(REC)
    check(st.exists() and rl.exists(), "CONTROL: pre-fix writers plant the wound + log row in a non-live process")
    st.unlink()
    rl.unlink()
    st.write_text('{"active": false}', encoding="utf-8")
    rl.write_text('{"a": 1}\n', encoding="utf-8")
    b1, b2 = _snap(st), _snap(rl)
    names = sorted(x.name for x in fake.iterdir())
    check(_new_save(WOUND) is None and _new_log(REC) is None, "fenced writers return None, raise nothing")
    check(_snap(st) == b1 and _snap(rl) == b2, "both files byte-identical (size + sha256)")
    check(sorted(x.name for x in fake.iterdir()) == names, "no new file appears")
    st.unlink()
    rl.unlink()
    S.note_difficulty("stray", "failure")
    check(not st.exists() and not rl.exists(), "note_difficulty in a non-live process plants nothing (absent target)")
    sub = fake / "sub"
    _aim(sub / "raw_difficulty.json", sub / "dwell_release.jsonl")
    _new_save(WOUND)
    _new_log(REC)
    check(not sub.exists(), "absent target: neither file nor mkdir'd parent created")

    print("\n[3] real path (writes trapped)")
    P._DATA, P._CANONICAL_DATA = _orig["DATA"], _orig["CANON"]
    hits = []
    real_wt, real_mk, real_open = Path.write_text, Path.mkdir, builtins.open
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

    Path.write_text, Path.mkdir, builtins.open = trap_wt, trap_mk, trap_open
    try:
        for state_t, rel_t in (_LIVE_PAIR, _TREE_PAIR):
            _aim(state_t, rel_t)
            hits.clear()
            _ref_save(WOUND)
            _ref_log(REC)
            ref_hits = list(hits)
            hits.clear()
            _new_save(WOUND)
            _new_log(REC)
            new_hits = list(hits)
            check({h[0] for h in ref_hits} >= {"write", "open"}, f"CONTROL pre-fix reaches the real write+open ({state_t.parent})")
            check(not new_hits, f"fenced writers reach no write/mkdir/open ({state_t.parent})")
    finally:
        Path.write_text, Path.mkdir, builtins.open = real_wt, real_mk, real_open

    print("\n[4] live (profile.LIVE = True)")
    P._DATA, P._CANONICAL_DATA, P.LIVE = fake, fake, True
    for label, d, r in (("ascii", dict(WOUND, text="plain"), dict(REC, reason="plain")), ("non-ascii", WOUND, REC)):
        a_s, a_r, b_s, b_r = (fake / f"{n}_{label}" for n in ("as", "ar", "bs", "br"))
        _aim(a_s, a_r)
        _ref_save(d)
        _ref_log(r)
        _ref_log(r)
        _aim(b_s, b_r)
        _new_save(d)
        _new_log(r)
        _new_log(r)
        check(a_s.exists() and a_s.read_bytes() == b_s.read_bytes(), f"live _save bytes identical ({label})")
        check(a_r.exists() and a_r.read_bytes() == b_r.read_bytes() and a_r.read_text(encoding="utf-8").count("\n") == 2,
              f"live _log_release append bytes identical ({label})")
    blocker = fake / "blocker"
    blocker.write_text("x", encoding="utf-8")
    for fn, arg, nm in ((_ref_save, WOUND, "pre-fix _save"), (_new_save, WOUND, "fenced _save"),
                        (_ref_log, REC, "pre-fix _log_release"), (_new_log, REC, "fenced _log_release")):
        _aim(blocker / "a.json", blocker / "a.jsonl")
        try:
            fn(arg)
            ok = True
        except Exception:
            ok = False
        check(ok, f"live I/O error stays fail-open ({nm})")
    check(blocker.read_text(encoding="utf-8") == "x", "error path left the blocker file intact")

    print("\n[5] legit redirects (non-live)")
    P.LIVE = False
    lab = fake / "_lab" / "20261005_000000"
    _aim(lab / "raw_difficulty.json", lab / "dwell_release.jsonl")
    _new_save(WOUND)
    _new_log(REC)
    check((lab / "raw_difficulty.json").exists() and (lab / "dwell_release.jsonl").exists(),
          "data/_lab/<stamp>/ sandbox still writes")
    out = TMP / "elsewhere"
    _aim(out / "raw_difficulty.json", out / "dwell_release.jsonl")
    _new_save(WOUND)
    _new_log(REC)
    check((out / "raw_difficulty.json").exists() and (out / "dwell_release.jsonl").exists(), "a path outside data/ still writes")
    _aim(fake / "_lab" / "raw_difficulty.json", fake / "_lab" / "dwell_release.jsonl")
    _new_save(WOUND)
    _new_log(REC)
    check(not (fake / "_lab" / "raw_difficulty.json").exists() and not (fake / "_lab" / "dwell_release.jsonl").exists(),
          "data/_lab/<file> directly stays refused")

    print("\n[6] visibility")
    P._warned.clear()

    class H(logging.Handler):
        def __init__(self):
            super().__init__(logging.DEBUG)
            self.recs = []

        def emit(self, r):
            self.recs.append(r)

    h = H()
    lg = logging.getLogger("nascence.sitting")
    old = lg.level
    lg.setLevel(logging.DEBUG)
    logging.getLogger().addHandler(h)
    lg.addHandler(h)
    _aim(st, rl)
    _new_save(WOUND)
    _new_save(WOUND)
    _new_log(REC)
    _new_log(REC)
    logging.getLogger().removeHandler(h)
    lg.removeHandler(h)
    lg.setLevel(old)
    warns = [r for r in h.recs if r.levelno == logging.WARNING and "refused" in r.getMessage()]
    dbg = [r for r in h.recs if r.name == "nascence.sitting" and "failed" in r.getMessage()]
    check(len(warns) == 2, f"one guard WARNING per path (2 paths, 4 refusals) (got {len(warns)})")
    check(len(dbg) >= 4, "sitting debug lines carry the refusals")
finally:
    S._STATE, S._RELEASE_LOG = _orig["STATE"], _orig["REL"]
    P._DATA, P._CANONICAL_DATA, P.LIVE = _orig["DATA"], _orig["CANON"], _orig["LIVE"]
    shutil.rmtree(TMP, ignore_errors=True)

print("\n[7] canary")
check({p: _snap(p) for p in _WATCH} == _before, "real raw_difficulty.json / dwell_release.jsonl files byte-identical to the start")
print("\nALL OK" if FAILS == 0 else f"\n{FAILS} FAILED")
sys.exit(0 if FAILS == 0 else 1)
