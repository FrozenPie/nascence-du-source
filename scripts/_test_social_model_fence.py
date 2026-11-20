"""
Regression: core/social_model.py save() sits behind the D-0179 write fence (J-1810 / F-2428, the F-2283 class).

The gap: SocialModelManager.save() wrote _SOCIAL_STATE_PATH (data/social_state.json) with no profile.guard_path, so any
non-live process that built an Orchestrator and ran a human cycle rewrote Du's real relational state (trust, delta_social,
cycles_since_spike; a correction spike on disk for the next real boot). activate_profile()'s rebase protects only a
process that CALLS it. The build: save() resolves the path through profile.guard_path before the mkdir, INSIDE its own
non-fatal try (refusal logged + swallowed, never raised into the orchestrator). Live process: byte-identical.

  [1] surface   names unchanged; module's `profile` is core.profile
  [2] leak      (simulated data/ root) CONTROL: the pre-fix save() (verbatim below) rewrites the file in a non-live process;
                the fenced save() leaves it byte-identical, creates nothing, raises nothing; in-memory state still evolves;
                __init__'s migration save is refused too
  [3] real path write TRAPPED with _SOCIAL_STATE_PATH at the REAL C:\\Nascence\\data file: pre-fix reaches it, fenced does not
  [4] live      (profile.LIVE=True) fenced == pre-fix bytes, incl. non-ASCII and the error path (parent is a file)
  [5] legit     data/_lab/<stamp>/ sandbox and a path outside data/ still write non-live; data/_lab/<file> stays refused
  [6] visible   one profile WARNING per path + a social debug line
  [7] canary    real social_state.json files byte-identical before/after

  python scripts/_test_social_model_fence.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import hashlib
import json
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


_LIVE_FILE = Path(r"C:\Nascence") / "data" / "social_state.json"
_DEFAULT_FILE = ROOT / "data" / "social_state.json"
_WATCH = {_LIVE_FILE, _DEFAULT_FILE}
_before = {p: _snap(p) for p in _WATCH}

import core                                      # noqa: E402  (BEFORE anything that could hijack sys.path -- F-2423)
from core import profile as P                    # noqa: E402
from core import social_model as SM              # noqa: E402

check(Path(core.__file__).resolve().is_relative_to(ROOT), f"core imported from the tree under test ({core.__file__})")

TMP = Path(tempfile.mkdtemp(prefix="j1810_social_fence_"))
_orig = dict(PATH=SM._SOCIAL_STATE_PATH, DATA=P._DATA, CANON=P._CANONICAL_DATA, LIVE=P.LIVE)

# The pre-J-1810 save(), verbatim -- the CONTROL.
_REF_SRC = r'''
def save(self):
    try:
        _SOCIAL_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _SOCIAL_STATE_PATH.write_text(
            json.dumps(self.state.to_json(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as exc:
        logger.debug("[social] save failed (non-fatal): %s", exc)
'''
_ref_ns = dict(vars(SM))
exec(_REF_SRC, _ref_ns)
_ref_save = _ref_ns["save"]
_new_save = SM.SocialModelManager.save


def _aim(path: Path):
    SM._SOCIAL_STATE_PATH = _ref_ns["_SOCIAL_STATE_PATH"] = path


def _mgr(path: Path, trust=0.7, tone="analytical"):
    _aim(path)
    m = SM.SocialModelManager.__new__(SM.SocialModelManager)
    m._migrated_on_load = False
    m.state = SM.SocialState(relational_trust=trust, expected_tone=tone)
    return m


SEED = {"relation_id": "travis", "expected_tone": "analytical", "relational_trust": 0.835, "user_expectations": [],
        "user_knowledge_state": {}, "interpersonal_tensions": [], "delta_social": 0.0, "cycles_since_spike": 1014,
        "state_version": 1}

try:
    print("\n[1] surface")
    check(getattr(SM, "profile", None) is P, "core.social_model.profile is core.profile (mark_live() reaches it)")
    check(hasattr(SM, "_SOCIAL_STATE_PATH") and hasattr(SM, "SocialModelManager") and hasattr(SM.SocialModelManager, "save"),
          "public names intact")

    fake = TMP / "fake_root" / "data"
    fake.mkdir(parents=True)
    P._DATA = fake
    P._CANONICAL_DATA = fake
    P.LIVE = False
    f = fake / "social_state.json"

    print("\n[2] the leak (simulated data/ root)")
    f.write_text(json.dumps(SEED, indent=2), encoding="utf-8")
    base = _snap(f)
    m = _mgr(f)
    _ref_save(m)
    check(_snap(f) != base, "CONTROL: pre-fix save() rewrites the file in a non-live process (the leak is real)")
    f.write_text(json.dumps(SEED, indent=2), encoding="utf-8")
    base = _snap(f)
    names = sorted(x.name for x in fake.iterdir())
    m = _mgr(f)
    m.state.apply_correction("That is not what I asked. Just answer the question.")
    m.state.decay_cycle()
    r = _new_save(m)
    check(r is None, "fenced save() returns None and raises nothing")
    check(_snap(f) == base, "fenced save(): file byte-identical (size + sha256)")
    check(sorted(x.name for x in fake.iterdir()) == names, "no new file appears")
    check(m.state.delta_social > 0.3, "in-memory state still evolves (only persistence refused)")
    gone = fake / "sub" / "social_state.json"
    m2 = _mgr(gone)
    _new_save(m2)
    check(not gone.exists() and not gone.parent.exists(), "absent target: neither file nor mkdir'd parent created")
    old = dict(SEED, state_version=0, delta_social=1.0)
    f.write_text(json.dumps(old, indent=2), encoding="utf-8")
    base = _snap(f)
    _aim(f)
    mm = SM.SocialModelManager()
    check(mm._migrated_on_load and _snap(f) == base, "__init__ migration save refused too (file untouched, no raise)")

    print("\n[3] real path (writes trapped)")
    P._DATA = _orig["DATA"]
    P._CANONICAL_DATA = _orig["CANON"]
    hits = []
    real_wt, real_mk = Path.write_text, Path.mkdir
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

    Path.write_text, Path.mkdir = trap_wt, trap_mk
    try:
        for tgt in (_LIVE_FILE, _DEFAULT_FILE):
            hits.clear()
            _ref_save(_mgr(tgt))
            ref_hits = list(hits)
            hits.clear()
            _new_save(_mgr(tgt))
            check(any(h[0] == "write" for h in ref_hits), f"CONTROL pre-fix reaches the real write ({tgt})")
            check(not hits, f"fenced save() reaches neither write nor mkdir ({tgt})")
    finally:
        Path.write_text, Path.mkdir = real_wt, real_mk

    print("\n[4] live (profile.LIVE = True)")
    P._DATA, P._CANONICAL_DATA, P.LIVE = fake, fake, True
    for label, trust, tone in (("ascii", 0.61, "analytical"), ("non-ascii", 0.42, "tendre \u00e9\u00e8 \u2014 \u65e5\u672c")):
        a, b = fake / f"a_{label}.json", fake / f"b_{label}.json"
        _ref_save(_mgr(a, trust, tone))
        _new_save(_mgr(b, trust, tone))
        check(a.exists() and a.read_bytes() == b.read_bytes(), f"live fenced == pre-fix bytes ({label})")
    blocker = fake / "blocker"
    blocker.write_text("x", encoding="utf-8")
    bad = blocker / "social_state.json"
    for fn, nm in ((_ref_save, "pre-fix"), (_new_save, "fenced")):
        try:
            fn(_mgr(bad))
            ok = True
        except Exception:
            ok = False
        check(ok, f"live I/O error stays fail-open ({nm})")
    check(blocker.read_text(encoding="utf-8") == "x", "error path left the blocker file intact")

    print("\n[5] legit redirects (non-live)")
    P.LIVE = False
    lab = fake / "_lab" / "20261005_000000" / "social_state.json"
    _new_save(_mgr(lab, 0.5))
    check(lab.exists(), "data/_lab/<stamp>/ sandbox still writes")
    outside = TMP / "elsewhere" / "social_state.json"
    _new_save(_mgr(outside, 0.5))
    check(outside.exists(), "a path outside data/ still writes")
    direct = fake / "_lab" / "social_state.json"
    _new_save(_mgr(direct, 0.5))
    check(not direct.exists(), "data/_lab/<file> directly stays refused")

    print("\n[6] visibility")
    P._warned.clear()

    class H(logging.Handler):
        def __init__(self):
            super().__init__(logging.DEBUG)
            self.recs = []

        def emit(self, r):
            self.recs.append(r)

    h = H()
    lg_social = logging.getLogger("nascence.social")
    old_lvl = lg_social.level
    lg_social.setLevel(logging.DEBUG)
    logging.getLogger().addHandler(h)
    lg_social.addHandler(h)
    f.write_text(json.dumps(SEED), encoding="utf-8")
    _new_save(_mgr(f))
    _new_save(_mgr(f))
    logging.getLogger().removeHandler(h)
    lg_social.removeHandler(h)
    lg_social.setLevel(old_lvl)
    warns = [r for r in h.recs if r.levelno == logging.WARNING and "refused" in r.getMessage()]
    dbg = [r for r in h.recs if r.name == "nascence.social" and "save failed" in r.getMessage()]
    check(len(warns) == 1, f"exactly one guard WARNING for the path across two refusals (got {len(warns)})")
    check(len(dbg) >= 1, "social debug line carries the refusal")
finally:
    SM._SOCIAL_STATE_PATH = _orig["PATH"]
    P._DATA, P._CANONICAL_DATA, P.LIVE = _orig["DATA"], _orig["CANON"], _orig["LIVE"]
    shutil.rmtree(TMP, ignore_errors=True)

print("\n[7] canary")
check({p: _snap(p) for p in _WATCH} == _before, "real social_state.json files byte-identical to the start of the run")
print("\nALL OK" if FAILS == 0 else f"\n{FAILS} FAILED")
sys.exit(0 if FAILS == 0 else 1)
