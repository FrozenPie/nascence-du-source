"""
Regression: core/school.py, core/nature_study.py and core/literal_will.py sit behind the D-0179 write fence (J-1801 / F-2426).

The gap: school.STATE, nature_study._STATE/_LOG and literal_will._LOG/_STATE are plain __file__-relative module-level paths and
their writers never went through profile.guard_path, so ANY process that merely imported them from the shared tree and reached a
writer wrote Du's REAL data/school.json, data/nature_study_state.json, data/nature_study_log.jsonl,
data/literal_will_shadow.jsonl and data/literal_will_state.json (same class as F-2406 satisfaction / F-2416 prediction_error).

The build: school._save and nature_study._save/_record resolve their path(s) through profile.guard_path BEFORE any I/O, outside
any swallow (a refusal raises profile.NonLiveWriteError, as the callers' existing carve-outs expect; _record resolves both
targets before its fragment store / competence side effects, so a refusal is a total no-op). literal_will._log_row/_save_state
(observe-only, fail-open) resolve inside their own try, so a refusal is logged by guard_path and swallowed. A LIVE process gets
the same paths back: byte-identical behaviour.

ISOLATED: every write goes to a temp dir or a SIMULATED data/ root, or is TRAPPED (recorded, never executed) when aimed at the
REAL C:\\Nascence\\data; the live files are hashed before and after. Safe to run from any tree, including against the pre-fix
modules (it must FAIL there).

  python scripts/_test_school_nature_literal_fence.py        # exit 0 = ALL OK
"""
from __future__ import annotations
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/

import builtins
import hashlib
import json
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402  -- BEFORE every other core import, and asserted (F-2423)
_core_file = Path(core.__file__).resolve()
assert ROOT in _core_file.parents, f"core resolves to {_core_file}, not inside {ROOT} -- refusing to run"

TMP = Path(tempfile.mkdtemp(prefix="j1801_fence_"))
print("core package:", _core_file)
print("isolated store dir:", TMP)

FAILS = 0


def check(cond: bool, label: str) -> None:
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


_LIVE_DATA = Path(r"C:\Nascence") / "data"
_NAMES = ("school.json", "nature_study_state.json", "nature_study_log.jsonl",
          "literal_will_shadow.jsonl", "literal_will_state.json")
_WATCH = {_LIVE_DATA / n for n in _NAMES} | {ROOT / "data" / n for n in _NAMES} | {
    _LIVE_DATA / "satisfaction_log.jsonl", _LIVE_DATA / "prediction_error_log.jsonl",
    _LIVE_DATA / "logs" / "shadow_integrity.jsonl", _LIVE_DATA / "buses_log.jsonl"}


def _snap(p: Path):
    if not p.exists():
        return None
    b = p.read_bytes()
    return (len(b), hashlib.sha256(b).hexdigest())


_before = {p: _snap(p) for p in _WATCH}

from core import profile as P            # noqa: E402
from core import school, nature_study, literal_will as lw  # noqa: E402
import core.memory.store as store        # noqa: E402

_orig = dict(S=school.STATE, NS=nature_study._STATE, NL=nature_study._LOG, LL=lw._LOG, LS=lw._STATE,
             DATA=P._DATA, CANON=P._CANONICAL_DATA, LIVE=P.LIVE, SF=store.store_fragment)


def restore():
    school.STATE, nature_study._STATE, nature_study._LOG = _orig["S"], _orig["NS"], _orig["NL"]
    lw._LOG, lw._STATE = _orig["LL"], _orig["LS"]
    P._DATA, P._CANONICAL_DATA, P.LIVE = _orig["DATA"], _orig["CANON"], _orig["LIVE"]
    store.store_fragment = _orig["SF"]


def aim_at(root: Path):
    """Point the three modules at `root` (a data/ dir) AND make the fence treat `root` as the data root."""
    school.STATE = root / "school.json"
    nature_study._STATE = root / "nature_study_state.json"
    nature_study._LOG = root / "nature_study_log.jsonl"
    lw._DATA = root
    lw._LOG = root / "literal_will_shadow.jsonl"
    lw._STATE = root / "literal_will_state.json"
    P._DATA = P._CANONICAL_DATA = root


def listing(root: Path):
    return sorted(str(p.relative_to(root)) for p in root.rglob("*")) if root.exists() else []


frag_calls = []


def _frag_stub(*a, **k):
    frag_calls.append(k.get("content", ""))


try:
    # ── [1] surface ────────────────────────────────────────────────────────────────────────────────────────────────────
    print("[1] surface")
    check(getattr(school, "profile", None) is P and getattr(nature_study, "profile", None) is P and getattr(lw, "profile", None) is P, "all three modules hold core.profile")
    for p in (_LIVE_DATA / "school.json", _LIVE_DATA / "nature_study_state.json", _LIVE_DATA / "nature_study_log.jsonl",
              _LIVE_DATA / "literal_will_shadow.jsonl", _LIVE_DATA / "literal_will_state.json"):
        P.LIVE = False
        try:
            P.guard_path(p)
            check(False, f"guard_path refuses {p.name}")
        except P.NonLiveWriteError:
            check(True, f"guard_path refuses {p.name}")
    for src in ("school.py", "nature_study.py", "literal_will.py"):
        check("guard_path(" in (ROOT / "core" / src).read_text(encoding="utf-8"), f"core/{src} calls guard_path")

    # ── [2] the leak, simulated data/ root, NON-LIVE ───────────────────────────────────────────────────────────────────
    print("[2] non-live refusal (simulated data/ root)")
    fake = TMP / "fake_root" / "data"
    fake.mkdir(parents=True)
    aim_at(fake)
    store.store_fragment = _frag_stub
    P.LIVE = False
    # pre-existing content must stay byte-identical
    (fake / "school.json").write_text('{"assigned_book": null, "history": []}', encoding="utf-8")
    pre = _snap(fake / "school.json")
    names0 = listing(fake)

    def refused(fn, label):
        try:
            fn()
            check(False, label + " (no exception)")
        except P.NonLiveWriteError:
            check(True, label)
        except Exception as e:
            check(False, f"{label} (wrong exception {e!r})")

    refused(lambda: school._save({"x": 1}), "school._save refused")
    refused(school.record_session, "school.record_session refused")
    refused(school.new_day, "school.new_day refused")
    check(_snap(fake / "school.json") == pre, "school.json byte-identical (size+sha256)")
    refused(lambda: nature_study._save({"history": []}), "nature_study._save refused")
    refused(lambda: nature_study._record("obs " * 20, "inf", 0.7, "fb"), "nature_study._record refused")
    check(frag_calls == [], "refused _record never reached store_fragment (no half-write)")
    check(listing(fake) == names0, "no nature_study file created")
    lw._log_row({"ts": 1, "x": "a"})
    lw._save_state({"k": 1})
    lw._skip("because", why=1)
    check(listing(fake) == names0, "literal_will._log_row/_save_state/_skip create nothing (swallowed, observe-only)")
    r = lw.observe("I will light the fire now.", "", location="study", cycle_id="c1")
    check(r is None and listing(fake) == names0, "literal_will.observe returns None, writes nothing")
    check(nature_study.status()["lessons"] == 0 and school.status()["history"] == [], "reads still work non-live")

    # ── [3] real paths: every write TRAPPED ────────────────────────────────────────────────────────────────────────────
    print("[3] real C:\\Nascence\\data paths (writes trapped)")
    trapped = []
    _real_open = builtins.open
    _real_wt = Path.write_text
    _real_mkdir = Path.mkdir
    _real_replace = Path.replace

    def _is_real(p) -> bool:
        try:
            Path(p).resolve().relative_to(_LIVE_DATA)
            return True
        except Exception:
            return False

    def t_open(f, mode="r", *a, **k):
        if _is_real(f) and any(c in str(mode) for c in "wax+"):
            trapped.append(("open", str(f)))
            raise OSError("trapped")
        return _real_open(f, mode, *a, **k)

    def t_wt(self, *a, **k):
        if _is_real(self):
            trapped.append(("write_text", str(self)))
            raise OSError("trapped")
        return _real_wt(self, *a, **k)

    def t_mkdir(self, *a, **k):
        if _is_real(self):
            trapped.append(("mkdir", str(self)))
            return None
        return _real_mkdir(self, *a, **k)

    def t_replace(self, *a, **k):
        if _is_real(self):
            trapped.append(("replace", str(self)))
            raise OSError("trapped")
        return _real_replace(self, *a, **k)

    builtins.open, Path.write_text, Path.mkdir, Path.replace = t_open, t_wt, t_mkdir, t_replace
    try:
        school.STATE = _LIVE_DATA / "school.json"
        nature_study._STATE = _LIVE_DATA / "nature_study_state.json"
        nature_study._LOG = _LIVE_DATA / "nature_study_log.jsonl"
        lw._DATA = _LIVE_DATA
        lw._LOG = _LIVE_DATA / "literal_will_shadow.jsonl"
        lw._STATE = _LIVE_DATA / "literal_will_state.json"
        P._DATA = P._CANONICAL_DATA = _LIVE_DATA
        P.LIVE = False
        for fn in (lambda: school._save({"a": 1}), lambda: nature_study._save({"history": []}),
                   lambda: nature_study._record("obs " * 20, "i", 0.5, "f"),
                   lambda: lw._log_row({"ts": 1}), lambda: lw._save_state({"k": 1}),
                   lambda: lw.observe("I will light the fire now.", "", location="study")):
            try:
                fn()
            except Exception:
                pass
        check(trapped == [], f"fenced modules reached NO real write (trapped={trapped})")
        # CONTROL: the trap itself works (a live process would write; here it is trapped, not executed)
        P.LIVE = True
        try:
            school._save({"a": 1})
        except Exception:
            pass
        check(any(k == "write_text" for k, _ in trapped), "CONTROL: a live school._save IS seen by the trap (the test can fail)")
    finally:
        builtins.open, Path.write_text, Path.mkdir, Path.replace = _real_open, _real_wt, _real_mkdir, _real_replace
    store.store_fragment = _frag_stub

    # ── [4] live parity ────────────────────────────────────────────────────────────────────────────────────────────────
    print("[4] live parity (profile.LIVE = True)")
    live = TMP / "live_root" / "data"
    live.mkdir(parents=True)
    aim_at(live)
    P.LIVE = True
    d = {"assigned_book": "b", "assigned_title": "Tïtle", "history": [{"ts": 1, "title": "x"}], "today_done": 2}
    school._save(d)
    ref = TMP / "ref_school.json"
    _real_wt(ref, json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")
    check((live / "school.json").read_bytes() == ref.read_bytes(), "school._save bytes identical to the pre-fix expression")
    school.record_session()
    check(json.loads((live / "school.json").read_text(encoding="utf-8"))["today_done"] == 3, "record_session ticks live")
    nd = {"history": [{"ts": 1, "score": 0.5, "feedback": "f"}]}
    nature_study._save(nd)
    _real_wt(ref, json.dumps(nd, indent=1, ensure_ascii=False), encoding="utf-8")
    check((live / "nature_study_state.json").read_bytes() == ref.read_bytes(), "nature_study._save bytes identical")
    nature_study._record("a" * 40 + " garden", "it tells me", 0.8, "good")
    row = json.loads((live / "nature_study_log.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    check(row["score"] == 0.8 and row["feedback"] == "good" and "garden" in row["observation"], "nature log row written live")
    check(len(frag_calls) == 1, "live _record reaches store_fragment once")
    check(len(nature_study._load()["history"]) == 2, "live _record appends to state history")
    lw._log_row({"ts": 1.0, "family": "fire", "n": "é"})
    _ref2 = TMP / "ref_lw.jsonl"   # the pre-fix expression, text-mode append (platform newline), like the writer
    with _real_open(_ref2, "a", encoding="utf-8") as _f:
        _f.write(json.dumps({"ts": 1.0, "family": "fire", "n": "é"}, ensure_ascii=False) + "\n")
    check((live / "literal_will_shadow.jsonl").read_bytes() == _ref2.read_bytes(),
          "literal_will._log_row bytes identical to the pre-fix expression")
    lw._save_state({"intents": {"a": 1}})
    check(json.loads((live / "literal_will_state.json").read_text(encoding="utf-8")) == {"intents": {"a": 1}}
          and not (live / "literal_will_state.tmp").exists(), "literal_will._save_state atomic, no .tmp left")
    lw.observe("I will light the fire now.", "", location="study", cycle_id="c1")
    check((live / "literal_will_shadow.jsonl").stat().st_size > 40, "live observe still logs rows")

    # ── [5] legit redirects still write non-live ───────────────────────────────────────────────────────────────────────
    print("[5] legit redirect (path outside data/) non-live")
    P._DATA = P._CANONICAL_DATA = _orig["DATA"]
    P.LIVE = False
    out = TMP / "elsewhere"
    out.mkdir()
    school.STATE = out / "school.json"
    school._save({"ok": 1})
    check(json.loads((out / "school.json").read_text(encoding="utf-8")) == {"ok": 1}, "redirected school._save writes non-live")
    lw._DATA = out
    lw._LOG = out / "lw.jsonl"
    lw._log_row({"ts": 2})
    check((out / "lw.jsonl").exists(), "redirected literal_will._log_row writes non-live")
finally:
    restore()

# ── [6] canary ─────────────────────────────────────────────────────────────────────────────────────────────────────────
print("[6] canary")
_after = {p: _snap(p) for p in _WATCH}
check(_after == _before, "every watched live file byte-identical to the start of the run")

print("\nALL OK" if FAILS == 0 else f"\n{FAILS} FAILURE(S)")
sys.exit(1 if FAILS else 0)
