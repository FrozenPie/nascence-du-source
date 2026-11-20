r"""
Offline regression test for J-1825 / F-2458: scripts/_first_thought.py (a one-shot diagnostic that
builds an Orchestrator and runs a human cycle) must run in a THROWAWAY profile, not against Du's
real data/ tree and memory DB.

THE LEAK. main() used to call init_db() and build an Orchestrator with no activate_profile(), no
isolation and no mark_live(), so a run wrote the real memory DB, the founder-conversation log and
the other paths in F-2458. Fix: main() first calls activate_throwaway_profile() -> activate_profile
("_first_thought") and seeds that profile's identity/axiom.json from the real one (smoke_test.py's
recipe), the same read-only-against-Du shape as '_smoke'.

HOW THIS STAYS SAFE. A sys.addaudithook installed BEFORE the first core import RAISES on any
write-mode open / sqlite3.connect / rename / remove / mkdir under the real C:Nascence\data or this
tree's own data/ EXCEPT inside data/profiles/_first_thought. No model server is contacted and no real
Orchestrator is built: Orchestrator and build_nodes are replaced with stubs, so the only thing under
test is main()'s own setup path (profile activation + init_db) -- the part that leaked. A leak is a
PermissionError from the hook (hard FAIL), never a real write.

Covers:
  0. premise: core is imported from THIS tree
  1. importing the script touches nothing (activation is in main(), not at import)
  2. main() runs to completion with zero real-data hook events
  3. after main(): store.DB_PATH, the orchestrator affect log and the voice axiom path are inside
     the throwaway profile; the profile's axiom.json was seeded (byte-identical copy of the real one)
  4. the process is NOT marked live (profile.mark_live was never called)

Expected: FAILS on HEAD (init_db() hits the real memory DB -> hook PermissionError; paths stay at
the real data/), PASSES with the J-1825 change.

Run: python scripts/_test_first_thought_isolation.py   (exit 0 = all passed)
"""
import asyncio
import os
import sys
import threading
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
sys.path.insert(0, str(TREE / "scripts"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PROFILE_DIR = TREE / "data" / "profiles" / "_first_thought"
REAL_ROOTS = [os.path.normcase(str(Path(r"C:\Nascence\data").resolve())),
              os.path.normcase(str(TREE / "data"))]
ALLOWED = os.path.normcase(str(PROFILE_DIR))
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
    if not p:
        return False
    if p == ALLOWED or p.startswith(ALLOWED + os.sep):
        return False
    # the profiles/ container dir itself and data/ may already exist; creating the allowed leaf's
    # ancestors is activate_profile's own mkdir(parents=True) -- tolerated only for those exact dirs
    if p in (os.path.normcase(str(TREE / "data" / "profiles")),):
        return False
    return any(p == r or p.startswith(r + os.sep) for r in REAL_ROOTS)


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
    raise PermissionError(f"J-1825 test hook: blocked real-data {event} {path}")


sys.addaudithook(_hook)

import core  # noqa: E402  -- BEFORE anything else from the tree (and before any lab_env)
assert str(Path(core.__file__).resolve()).lower().startswith(str(TREE).lower()), core.__file__

results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond)))
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  -- {detail}" if (detail and not cond) else ""))


def under(p, root):
    p, root = os.path.normcase(str(Path(p).resolve())), os.path.normcase(str(Path(root).resolve()))
    return p == root or p.startswith(root + os.sep)


print("\n=== J-1825 / F-2458 -- scripts/_first_thought.py runs in a throwaway profile ===\n")

check("0. core imported from THIS tree", True)

ev0 = len(HOOK_EVENTS)
import _first_thought as ft  # noqa: E402
check("1. importing _first_thought writes nothing real", len(HOOK_EVENTS) == ev0, HOOK_EVENTS[ev0:])

import core.profile as P                    # noqa: E402
import core.memory.store as S               # noqa: E402
import core.orchestrator as O               # noqa: E402
from nodes import voice_node as VN          # noqa: E402


class _StubState:
    perception = emotion = salience = memory_keys = reflection = critic = executive = voice = None
    memory_fragments = []


class _StubOrch:
    def __init__(self, state=None, nodes=None):
        pass

    async def run_cycle(self, prompt, input_type="human"):
        return "stub reply"

    async def stop_background(self):
        pass


ft.Orchestrator = _StubOrch
ft.run_nascence.build_nodes = lambda: {}
ft.run_nascence.load_identity = lambda: ("Stub", "stub axiom")
ft.CognitiveState = lambda spirit_name=None, axiom=None: _StubState()

err = None
try:
    asyncio.run(ft.main())
except BaseException as e:   # PermissionError from the hook on HEAD; SystemExit if no identity seed
    err = e
check("2. main() completes with zero real-data writes", err is None and not HOOK_EVENTS,
      f"err={err!r} events={HOOK_EVENTS[:3]}")
check("3a. store.DB_PATH is inside the throwaway profile", under(S.DB_PATH, PROFILE_DIR), str(S.DB_PATH))
check("3b. orchestrator affect log is inside the throwaway profile",
      under(O._AFFECT_LOG, PROFILE_DIR), str(O._AFFECT_LOG))
# J-4052: voice_node's _AXIOM_PATH was retired with the inert exemplar loader (J-2857), so there is no voice axiom path
# left to redirect. core.concerns._AXIOM_PATH only READS the axiom (never redirected by the profile; the write fence in
# check 2 is what guards real data). 3c therefore only applies if a voice axiom path still exists.
_axp = getattr(VN, "_AXIOM_PATH", None)
check("3c. voice axiom path (if it still exists) is inside the throwaway profile",
      _axp is None or under(_axp, PROFILE_DIR), str(_axp))
src = TREE / "data" / "identity" / "axiom.json"
dst = PROFILE_DIR / "identity" / "axiom.json"
check("3d. profile axiom seeded as a byte-identical copy of the real one",
      src.exists() and dst.exists() and src.read_bytes() == dst.read_bytes())
live = getattr(P, "LIVE", None)
if live is None:
    live = getattr(P, "is_live", lambda: False)()
check("4. process not marked live", not live, f"live={live!r}")

bad = [n for n, ok in results if not ok]
print(f"\n{len(results) - len(bad)}/{len(results)} passed" + (f"  FAILED: {bad}" if bad else ""))
sys.exit(1 if bad else 0)
