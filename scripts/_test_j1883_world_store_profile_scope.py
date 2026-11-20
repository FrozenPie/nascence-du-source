"""
Regression/pin test for J-1883 (F-2489 / F-2506 follow-up): the WORLD-STORE SCOPE of a named profile.

THE QUESTION. The J-1867 audit re-runs showed guard_path() refusing core.cat's data/cat_state.json and
core.scene_extra_ledger's data/scene_extra_ledger.jsonl from a named-profile cycle with NO profiles\\<name>\\
prefix, i.e. activate_profile() does not rebase them. J-1883's own re-runs (4 more audit runs, 12 cycles,
different probes) also saw data/provisions.json refused the same way: it is not two files, it is the whole
world-store family (docs/staged/world_store_write_fence.md inventory) that activate_profile() never rebases.

THE ANSWER THIS TEST PINS. That is harmless as long as no process is BOTH live (profile.mark_live()) and
named (activate_profile(<name>)): a non-live named profile is refused by guard_path() (D-0179; it even
refuses data/profiles/<name>/ paths), and a live-and-named boot is the only case that would write Du's
real world files. Today no code path is both: scripts/run_nascence.py is the only mark_live() caller and
never calls activate_profile(); the 3 other live scripts (seed_memory, debate_harness, backfill_essays)
say in their own docstrings that live means Carl's root data/ and that a named profile would be the wrong tool; every
activate_profile() caller is non-live. So nothing is rebased (a half
rebase -- 2 of ~24 world-store modules -- would only build a half-separate world) and instead:
  1. (static)  the set of non-test files that call mark_live() is exactly the 4 known root-data scripts, and no
               such file calls activate_profile() -- this test FAILS the day someone adds a live named boot,
               and its message points at the open question (own world per profile vs shared Du world);
  2. (runtime) activate_profile(<named>) leaves cat._STATE_F / scene_extra_ledger._LEDGER on the root path and
               guard_path() refuses both for a non-live process (true before AND after any future rebase);
  3. (tripwire) core.profile logs one loud warning when a process is live AND a named profile is active, in
               either call order (mark_live() after activation, activate_profile() after mark_live()); the
               root alias never warns.

SAFETY. Every path lives under a tempdir; a sys.addaudithook installed before the first core import RAISES
on any real-tree write (same hook as scripts/_test_j1867_assoc_recall_rebase.py).
Run: python scripts/_test_j1883_world_store_profile_scope.py   (exit 0 = all passed)
"""
import ast
import logging
import os
import shutil
import sys
import tempfile
import threading
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REAL_ROOTS = [os.path.normcase(str(Path(r"C:\Nascence\data").resolve())),
              os.path.normcase(str(TREE / "data"))]
HOOK_EVENTS: list = []
_busy = threading.local()
_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC


def _norm(p):
    try:
        if isinstance(p, int):
            return None
        if isinstance(p, bytes):
            p = os.fsdecode(p)
        return os.path.normcase(os.path.abspath(os.fspath(p)))
    except Exception:
        return None


def _is_real(p):
    return bool(p) and any(p == r or p.startswith(r + os.sep) for r in REAL_ROOTS)


def _hook(event, args):
    if getattr(_busy, "on", False):
        return
    path = None
    if event == "open":
        m, fl = args[1], args[2]
        w = (isinstance(m, str) and any(c in m for c in "wax+")) or \
            (isinstance(fl, int) and bool(fl & _WRITE_FLAGS) and m != "r")
        if not w:
            return
        path = _norm(args[0])
    elif event == "sqlite3.connect":
        path = _norm(args[0])
    elif event in ("os.rename", "os.replace"):
        path = _norm(args[1]) if _is_real(_norm(args[1])) else _norm(args[0])
    elif event in ("os.remove", "os.mkdir", "os.rmdir", "shutil.copyfile"):
        path = _norm(args[-1] if event == "shutil.copyfile" else args[0])
    else:
        return
    if not _is_real(path):
        return
    _busy.on = True
    try:
        HOOK_EVENTS.append({"event": event, "path": path})
    finally:
        _busy.on = False
    raise PermissionError(f"J-1883 test hook: blocked real-data {event} {path}")


sys.addaudithook(_hook)

import core  # noqa: E402  -- BEFORE anything else from the tree (and before any lab_env)
assert str(Path(core.__file__).resolve()).lower().startswith(str(TREE).lower()), core.__file__

import core.profile as P                      # noqa: E402
import core.cat as CAT                        # noqa: E402
import core.scene_extra_ledger as SEL         # noqa: E402
import core.look_render_ledger as LRL         # noqa: E402  (J-1899: the look-target render ledger is a world store too)

results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond)))
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  -- {detail}" if (detail and not cond) else ""))


def _call_names(tree):
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name):
                yield f.id
            elif isinstance(f, ast.Attribute):
                yield f.attr


def _scan():
    """(files calling mark_live/_mark_live, files calling activate_profile) among non-test repo .py files."""
    live, named = set(), set()
    skip_dirs = {".git", "data", "public_repo", "docs_site", "graphify-out", "scratch", "__pycache__", ".claude"}
    for root, dirs, files in os.walk(TREE):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fn in files:
            if not fn.endswith(".py") or fn.startswith("_test") or fn.startswith("test_"):
                continue
            p = Path(root) / fn
            try:
                tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
            except SyntaxError:
                continue
            names = set(_call_names(tree))
            rel = p.relative_to(TREE).as_posix()
            if names & {"mark_live", "_mark_live"}:
                live.add(rel)
            if "activate_profile" in names:
                named.add(rel)
    return live, named


print("\n=== J-1883 -- world-store scope of a named profile (offline, tempdir, audit hook) ===\n")
print("0. Premise")
check("core imported from the tree under test", Path(core.__file__).resolve().parent.parent == TREE, core.__file__)
check("cat._STATE_F is _DATA/cat_state.json", CAT._STATE_F.relative_to(P._DATA) == Path("cat_state.json"), CAT._STATE_F)
check("scene_extra_ledger._LEDGER is _DATA/scene_extra_ledger.jsonl",
      SEL._LEDGER.relative_to(P._DATA) == Path("scene_extra_ledger.jsonl"), SEL._LEDGER)
check("look_render_ledger._LEDGER is _DATA/look_render_ledger.jsonl (J-1899)",
      LRL._LEDGER.relative_to(P._DATA) == Path("look_render_ledger.jsonl"), LRL._LEDGER)

print("\n1. Static: no code path is both LIVE and NAMED")
LIVE_FILES, NAMED_FILES = _scan()
KNOWN_LIVE = {"scripts/run_nascence.py", "scripts/seed_memory.py", "scripts/debate_harness.py",
              "scripts/backfill_essays.py"}     # each declares live == Carl's root data/, never a named profile
check("the non-test mark_live() callers are exactly the 4 known root-data scripts", LIVE_FILES == KNOWN_LIVE,
      f"{sorted(LIVE_FILES ^ KNOWN_LIVE)} -- a new live process appeared (or one went away): decide whether it may run a named profile "
      f"(world-store modules are NOT rebased; see core/profile.py _warn_if_live_named_profile)")
both = LIVE_FILES & NAMED_FILES
check("no mark_live() caller also calls activate_profile()", not both,
      f"{sorted(both)} is live AND named: it would write Du's own world files (cat_state.json, "
      f"scene_extra_ledger.jsonl, provisions.json, ...). Rebase the world-store family or rule against it first.")
check("activate_profile() has callers (the scan is not vacuous)", len(NAMED_FILES) >= 3, sorted(NAMED_FILES))

TMP = Path(tempfile.mkdtemp(prefix="j1883_scope_"))
saved = (P._DATA, P.ACTIVE_BASE, P.LIVE, CAT._STATE_F, SEL._LEDGER, LRL._LEDGER)
records = []


class _H(logging.Handler):
    def emit(self, record):
        records.append(record.getMessage())


handler = _H(level=logging.WARNING)
plog = logging.getLogger("nascence.profile")
plog.addHandler(handler)
try:
    FAKE = TMP / "data"
    (FAKE / "memory").mkdir(parents=True)
    P._DATA = FAKE
    P.ACTIVE_BASE = FAKE
    P.LIVE = False
    CAT._STATE_F = FAKE / "cat_state.json"
    SEL._LEDGER = FAKE / "scene_extra_ledger.jsonl"
    LRL._LEDGER = FAKE / "look_render_ledger.jsonl"
    import core.memory.store as S             # noqa: E402
    S.DB_PATH = FAKE / "memory" / "nascence.db"

    print("\n2. Runtime (non-live): a named profile leaves the world-store constants alone and guard_path refuses them")
    base = P.activate_profile("_j1883_scope")
    check("profile dir is under the fake data root", base == FAKE / "profiles" / "_j1883_scope", base)
    check("cat._STATE_F NOT rebased (still the root world file)", CAT._STATE_F == FAKE / "cat_state.json", CAT._STATE_F)
    check("scene_extra_ledger._LEDGER NOT rebased", SEL._LEDGER == FAKE / "scene_extra_ledger.jsonl", SEL._LEDGER)
    check("look_render_ledger._LEDGER NOT rebased", LRL._LEDGER == FAKE / "look_render_ledger.jsonl", LRL._LEDGER)
    for label, path in (("cat_state.json", CAT._STATE_F), ("scene_extra_ledger.jsonl", SEL._LEDGER),
                        ("look_render_ledger.jsonl", LRL._LEDGER)):
        try:
            P.guard_path(path)
            check(f"guard_path refuses {label} for a non-live named profile", False, "returned a path")
        except P.NonLiveWriteError:
            check(f"guard_path refuses {label} for a non-live named profile", True)
    check("no tripwire warning for a NON-live named profile", not [r for r in records if "LIVE and a NAMED" in r], records)

    print("\n3. Tripwire (live AND named, either order)")
    records.clear()
    P.LIVE = True                      # order 1: live first, then a named activation
    P.activate_profile("_j1883_scope")
    hits = [r for r in records if "LIVE and a NAMED" in r and "activate_profile()" in r]
    check("activate_profile(<named>) in a live process warns once", len(hits) == 1, records)
    records.clear()
    P.activate_profile(None)           # root alias in a live process: the normal Du boot
    check("root alias in a live process does NOT warn", not records, records)
    P.LIVE = False                     # order 2: named active, then mark_live()
    P.activate_profile("_j1883_scope")
    records.clear()
    P.mark_live()
    hits = [r for r in records if "LIVE and a NAMED" in r and "mark_live()" in r]
    check("mark_live() with a named profile already active warns once", len(hits) == 1, records)
    P.LIVE = False
    P.activate_profile(None)
    records.clear()
    P.mark_live()
    check("mark_live() with the root profile does NOT warn", not records, records)
finally:
    plog.removeHandler(handler)
    P._DATA, P.ACTIVE_BASE, P.LIVE, CAT._STATE_F, SEL._LEDGER, LRL._LEDGER = saved
    shutil.rmtree(TMP, ignore_errors=True)

print("\n4. Audit hook")
check("zero real-tree write/connect events during the whole run", not HOOK_EVENTS, HOOK_EVENTS[:5])

passed = sum(1 for _, ok in results if ok)
print(f"\n=== {passed}/{len(results)} passed ===")
sys.exit(0 if passed == len(results) else 1)
