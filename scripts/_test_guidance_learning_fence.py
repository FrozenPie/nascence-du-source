"""
Regression: core/guidance_learning.py's seven write targets sit behind the D-0179 write fence (J-1813 / F-2428).

The gap: _LOG (guidance_shadow_log.jsonl), _INJECT_LOG (guidance_injection_log.jsonl), _CLASSIFY_LOG, _BELIEFS
(guidance_beliefs.json), _INTEG_STATE, _INTEG_LOG and _CONTRA_LOG were written with no profile.guard_path, so any
non-live harness that reached capture_shadow / log_injection / integrate_guidance wrote Du's real guidance stores.
Fix: every target resolved through guard_path before any I/O. Loggers/clock: INSIDE their existing fail-open try.
_save_beliefs: resolved BEFORE its try so the refusal is not mislabelled "integrated beliefs this cycle were lost";
integrate_guidance also refuses up front (before any LLM-driven work) and returns None.

  [1] surface  [2] leak (simulated root, CONTROL = pre-fix source verbatim from git)  [3] real paths trapped
  [4] live byte-identical incl. error paths  [5] legit redirects  [6] visibility  [7] canary

  python scripts/_test_guidance_learning_fence.py        # exit 0 = ALL OK
"""
from __future__ import annotations
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/

import asyncio
import builtins
import hashlib
import json
import logging
import shutil
import subprocess
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


_NAMES = ("guidance_shadow_log.jsonl", "guidance_injection_log.jsonl", "guidance_classify_log.jsonl",
          "guidance_beliefs.json", "guidance_integration_state.json", "guidance_integration_log.jsonl",
          "guidance_contradictions_shadow.jsonl")
_ATTRS = ("_LOG", "_INJECT_LOG", "_CLASSIFY_LOG", "_BELIEFS", "_INTEG_STATE", "_INTEG_LOG", "_CONTRA_LOG")
_LIVE_SET = tuple(Path(r"C:\Nascence") / "data" / n for n in _NAMES)
_TREE_SET = tuple(ROOT / "data" / n for n in _NAMES)
_WATCH = set(_LIVE_SET) | set(_TREE_SET)
_before = {p: _snap(p) for p in _WATCH}

import core                                      # noqa: E402  (BEFORE anything that could hijack sys.path -- F-2423)
from core import profile as P                    # noqa: E402
from core import guidance_learning as G          # noqa: E402
from core import judge_panel as _JP              # noqa: E402

# J-3233 / D-0622: the same-lesson check calls the judge panel; stub it to "no verdict" so this write-fence test calls no
# hub (and judge_panel_log.jsonl stays untouched). The control module (git HEAD~) predates the check and never calls it.


async def _no_verdict_panel(*a, **k):
    return {"verdict": None, "how": "unavailable", "v1": None, "v2": None, "hub1": None, "hub2": None, "hub3": None, "why": None}


_JP.rule_detail = _no_verdict_panel

check(Path(core.__file__).resolve().is_relative_to(ROOT), f"core imported from the tree under test ({core.__file__})")

TMP = Path(tempfile.mkdtemp(prefix="j1813_guidance_fence_"))
_orig = dict(DATA=P._DATA, CANON=P._CANONICAL_DATA, LIVE=P.LIVE, TIME=G.time,
             SEM=G._semantic_candidate, MAT=G.materialize_promoted_beliefs, PATHS={a: getattr(G, a) for a in _ATTRS})


def _git_show(rev):
    return subprocess.run(["git", "show", f"{rev}:core/guidance_learning.py"], cwd=ROOT, check=True,
                          capture_output=True).stdout.decode("utf-8")


# CONTROL: the pre-fix module, verbatim from git, executed as a module namespace.
# J-1841 (2026-10-06): the original "HEAD, else HEAD~1" lookup rotted as soon as a second commit touched this
# module after the fence landed (018e3c6) -- HEAD~1 then also carried guard_path, the control check failed and
# the unlink at [2] crashed the whole run before [3]-[7] could execute. Walk this file's own history back to
# the newest revision WITHOUT guard_path instead.
_old_src = _git_show("HEAD")
if "guard_path" in _old_src:          # HEAD already carries the fix (run after the commit): find the last pre-fix rev
    _revs = subprocess.run(["git", "rev-list", "HEAD", "--", "core/guidance_learning.py"], cwd=ROOT, check=True,
                           capture_output=True).stdout.decode().split()
    for _rev in _revs:
        _old_src = _git_show(_rev)
        if "guard_path" not in _old_src:
            break
_ref = {"__name__": "gl_control", "__file__": str(ROOT / "core" / "guidance_learning.py"), "__package__": "core"}
exec(compile(_old_src, "gl_control", "exec"), _ref)
check("guard_path" not in _old_src, "control source is the pre-fix module (no guard_path)")

_CLOCK = types.SimpleNamespace(time=lambda: 1234.5)


def _prep(target):
    for name, val in (("time", _CLOCK), ("_semantic_candidate", lambda *a, **k: (None, 0.0)),
                      ("materialize_promoted_beliefs", lambda: 0)):
        if isinstance(target, dict):
            target[name] = val
        else:
            setattr(target, name, val)


_prep(_ref)
_prep(G)


class _Ns:
    def __init__(self, t):
        self._t = t

    def __getattr__(self, n):
        return self._t[n] if isinstance(self._t, dict) else getattr(self._t, n)


REF, NEW = _Ns(_ref), _Ns(G)


def _aim(paths):
    for d in (G.__dict__, _ref):
        for a, p in zip(_ATTRS, paths):
            d[a] = p


def _aim_dir(d: Path):
    _aim([d / n for n in _NAMES])


async def _call_json(*a, **k):
    return {"relation": "assimilate"}


def run_all(ns, d: Path):
    """Drive every writer against dir d; returns the return values."""
    _aim_dir(d)
    for i, text in enumerate(("Commit fully to one direction and hold it", "Notice caf\u00e9 \u65e5\u672c patterns before acting",
                               "Hold the question open a while longer")):
        ns._log({"ts": 100.0 + i, "is_guidance": True, "principle": text, "why": "w\u00fc", "scope": "s", "confidence": 0.7})
    ns.log_injection("c1", "note one \u00e9")
    ns.log_injection("c2", "")
    ns._log_classify({"ts": 1.0, "relation": "assimilate", "x": "\u00fc"})
    ns._log_contradiction({"id": "a", "principle": "p\u00e9", "corroboration_count": 2, "entrenchment": 0.3, "domain": "self"},
                          {"id": "b", "principle": "q", "corroboration_count": 1, "entrenchment": 0.2})
    try:
        ns._save_beliefs([{"id": "z", "principle": "caf\u00e9 \u65e5\u672c"}])
    except P.NonLiveWriteError:
        pass
    ns._set_integ_last_ts(5.5)
    return [asyncio.run(ns.integrate_guidance(_call_json, []))]


def _fileset(d: Path):
    return sorted(x.name for x in d.iterdir())


try:
    print("\n[1] surface")
    check(getattr(G, "profile", None) is P, "core.guidance_learning.profile is core.profile (mark_live() reaches it)")
    check(all(hasattr(G, n) for n in _ATTRS + ("capture_shadow", "log_injection", "integrate_guidance", "_save_beliefs")),
          "public names intact")

    fake = TMP / "fake_root" / "data"
    fake.mkdir(parents=True)
    P._DATA = fake
    P._CANONICAL_DATA = fake
    P.LIVE = False

    print("\n[2] the leak (simulated data/ root, non-live)")
    run_all(REF, fake)
    check(all((fake / n).exists() for n in _NAMES), "CONTROL: pre-fix writers write all seven files in a non-live process")
    for n in _NAMES:
        (fake / n).unlink()
    seeds = {n: ('[{"id": "old"}]' if n.endswith("beliefs.json") else '{"last_ts": 1}' if n.endswith("state.json") else '{"a": 1}\n')
             for n in _NAMES}
    for n, v in seeds.items():
        (fake / n).write_text(v, encoding="utf-8")
    snaps = {n: _snap(fake / n) for n in _NAMES}
    listing = _fileset(fake)
    rets = run_all(NEW, fake)
    check(rets == [None], "fenced integrate_guidance returns None, nothing raises")
    check({n: _snap(fake / n) for n in _NAMES} == snaps, "all seven files byte-identical (size + sha256)")
    check(_fileset(fake) == listing, "no new file appears")
    for n in _NAMES:
        (fake / n).unlink()
    run_all(NEW, fake)
    check(not any((fake / n).exists() for n in _NAMES), "absent targets: nothing created")
    sub = fake / "sub"
    _aim_dir(sub)
    G.log_injection("x", "y")
    G._log({"a": 1})
    G._log_classify({})
    G._log_contradiction({}, {})
    G._set_integ_last_ts(1.0)
    check(not sub.exists(), "absent parent: no mkdir")
    _aim_dir(fake)
    try:
        G._save_beliefs([{"id": 1}])
        check(False, "_save_beliefs non-live raises NonLiveWriteError")
    except P.NonLiveWriteError:
        check(True, "_save_beliefs non-live raises NonLiveWriteError (surfaced, not 'beliefs lost')")

    print("\n[3] real paths (writes trapped)")
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

        def __iter__(self):
            return iter(())

    def trap_open(f, mode="r", *a, **k):
        try:
            if Path(f) in _WATCH and any(c in mode for c in "wax+"):
                hits.append(("open", str(f)))
                return _Null()
        except TypeError:
            pass
        return real_open(f, mode, *a, **k)

    Path.write_text, Path.mkdir, builtins.open = trap_wt, trap_mk, trap_open
    try:
        for tset in (_LIVE_SET, _TREE_SET):
            for ns, bucket in ((REF, "ref"), (NEW, "new")):
                _aim(tset)
                hits.clear()
                ns._log({"ts": 1.0, "is_guidance": True, "principle": "x" * 30})
                ns.log_injection("c", "n")
                ns._log_classify({})
                ns._log_contradiction({}, {})
                ns._set_integ_last_ts(1.0)
                try:
                    ns._save_beliefs([])
                except P.NonLiveWriteError:
                    pass
                asyncio.run(ns.integrate_guidance(_call_json, []))
                if bucket == "ref":
                    kinds = {h[0] for h in hits}
                    check(kinds >= {"write", "open", "mkdir"}, f"CONTROL pre-fix reaches real write/open/mkdir ({tset[0].parent})")
                else:
                    check(not hits, f"fenced writers reach no write/mkdir/open ({tset[0].parent}) {hits[:2]}")
    finally:
        Path.write_text, Path.mkdir, builtins.open = real_wt, real_mk, real_open

    print("\n[4] live (profile.LIVE = True)")
    P._DATA, P._CANONICAL_DATA, P.LIVE = fake, fake, True
    for tag in ("empty", "seeded"):
        da, db = fake / f"ref_{tag}", fake / f"new_{tag}"
        for d in (da, db):
            d.mkdir()
            if tag == "seeded":
                (d / "guidance_beliefs.json").write_text(json.dumps([{"id": "old", "principle": "an old unrelated thing entirely",
                                                                       "status": "tentative", "domain": "self"}]), encoding="utf-8")
                (d / "guidance_integration_state.json").write_text('{"last_ts": 100.5}', encoding="utf-8")
        ra = run_all(REF, da)
        rb = run_all(NEW, db)
        check(ra == rb and ra[0] is not None, f"live return values identical and integrate ran ({tag})")
        for n in _NAMES:
            nb = (db / n).read_bytes() if (db / n).exists() else None
            if n == "guidance_classify_log.jsonl" and nb is not None:
                # J-2221 (F-2911): integrate_guidance now appends ONE extra post-pole-gate row
                # ({"record": "final", ...}) per classified lesson -- an intended, additive change that the
                # pre-J-1813 reference source cannot produce. Drop those rows, then the J-1637 rows must
                # still be byte-identical; and the final row must actually be there.
                lines = nb.splitlines(keepends=True)
                kept = [x for x in lines if b'"record": "final"' not in x]
                check(len(kept) < len(lines), f"J-2221 final-verdict row present in classify log ({tag})")
                # J-3060 (P-0018): the classify row also gains additive cand_score / cand_path fields the pre-J-1813
                # reference cannot produce -- strip them, then the remaining bytes must still be identical.
                def _strip_j3060(x):
                    rec = json.loads(x.decode("utf-8"))
                    rec.pop("cand_score", None)
                    rec.pop("cand_path", None)
                    return json.dumps(rec, ensure_ascii=False).encode("utf-8") + x[len(x.rstrip(b"\r\n")):]
                nb = b"".join(_strip_j3060(x) for x in kept)
            check((da / n).exists() and (da / n).read_bytes() == nb, f"live bytes identical: {n} ({tag})")
        check(_fileset(da) == _fileset(db), f"same file set ({tag})")
    for label in ("corrupt", "blocked"):
        outs = []
        for ns, tag in ((REF, "ref"), (NEW, "new")):
            d = fake / f"err_{label}_{tag}"
            d.mkdir()
            if label == "corrupt":
                (d / "guidance_beliefs.json").write_text("{not json", encoding="utf-8")
                (d / "guidance_integration_state.json").write_text("{not json", encoding="utf-8")
                target = d
                probe = d / "guidance_beliefs.json"
            else:
                (d / "blocker").write_text("x", encoding="utf-8")
                target = d / "blocker" / "deeper"
                probe = d / "blocker"
            try:
                r = run_all(ns, target)
                outs.append(("ok", r, probe.read_bytes()))
            except Exception as exc:
                outs.append(("raised", type(exc).__name__, None))
        check(outs[0] == outs[1], f"live {label}: behaviour identical to pre-fix ({str(outs[1])[:60]})")

    print("\n[5] legit redirects (non-live)")
    P.LIVE = False
    lab = fake / "_lab" / "20261005_000000"
    lab.mkdir(parents=True)
    run_all(NEW, lab)
    check(all((lab / n).exists() for n in _NAMES), "data/_lab/<stamp>/ sandbox still writes all seven files")
    out = TMP / "elsewhere"
    out.mkdir()
    run_all(NEW, out)
    check(all((out / n).exists() for n in _NAMES), "a path outside data/ still writes all seven files")
    direct = fake / "_lab"
    run_all(NEW, direct)
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
    lg = logging.getLogger("nascence.guidance")
    old = lg.level
    lg.setLevel(logging.DEBUG)
    logging.getLogger().addHandler(h)
    lg.addHandler(h)
    for _ in range(2):
        run_all(NEW, fake)
    logging.getLogger().removeHandler(h)
    lg.removeHandler(h)
    lg.setLevel(old)
    warns = [r for r in h.recs if r.levelno == logging.WARNING and "refused" in r.getMessage()]
    lost = [r for r in h.recs if r.levelno >= logging.WARNING and r.name == "nascence.guidance"]
    dbg = [r for r in h.recs if r.name == "nascence.guidance" and r.levelno == logging.DEBUG]
    check(len(warns) >= 1, f"guard WARNING logged once per path (got {len(warns)})")
    check(not lost, "no refusal is logged as a guidance WARNING ('beliefs lost' / 'write failed')")
    check(len(dbg) >= 6, f"guidance debug lines carry the refusals (got {len(dbg)})")
finally:
    for a, p in _orig["PATHS"].items():
        setattr(G, a, p)
    G.time, G._semantic_candidate, G.materialize_promoted_beliefs = _orig["TIME"], _orig["SEM"], _orig["MAT"]
    P._DATA, P._CANONICAL_DATA, P.LIVE = _orig["DATA"], _orig["CANON"], _orig["LIVE"]
    shutil.rmtree(TMP, ignore_errors=True)

print("\n[7] canary")
check({p: _snap(p) for p in _WATCH} == _before, "real guidance data files byte-identical to the start")
print("\nALL OK" if FAILS == 0 else f"\n{FAILS} FAILED")
sys.exit(0 if FAILS == 0 else 1)
