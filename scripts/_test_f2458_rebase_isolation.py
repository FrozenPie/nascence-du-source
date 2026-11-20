"""
Offline regression test for J-1824 / F-2458: the 10 modules the J-1718 DYNAMIC write audit caught
writing to the ROOT profile's data/ from a named-profile human cycle must be rebased by
core.profile.activate_profile() like every other per-agent data/ path constant.

THE LEAK (F-2458). One human cycle of a real Orchestrator under activate_profile("_j1690_audit")
attempted 13 writes/opens against the real data/ tree from modules the rebase tuple never named:
core.arousal (_DATA: arousal_state.tmp, arousal_regime_shadow_state.tmp, arousal_shadow.jsonl),
core.wandering (path built INLINE from __file__ inside _log_trail -- no constant to rebase at all),
core.emotion_construction (_DATA: emotion_construction_shadow.jsonl, plus a sqlite3.connect READ of the
real data/memory/nascence.db from _affective_retrieval_shadow), core.memory.store
(_RETRIEVE_LATENCY_LOG), core.attention_schema_loop (_DATA), core.epistemic_affordance_advisor
(LOG_JSONL_PATH under an ABSOLUTE c:/Nascence root -- invisible to the generic rebase from a worktree),
core.conversational_action (_LOG), core.unified_inference (_UNIFIED_LOG), core.orchestrator
(_CORRELATION_LOG -- the one constant its hand-rebase block never covered), core.coupling_rides
(_LOG/_DATA derived from a repo _ROOT).

HOW THIS TEST STAYS SAFE (it must never touch the real data/). Every path lives under a tempdir:
core.profile._DATA and every constant under test are pointed into that tempdir BEFORE
activate_profile() runs, so the "live" files below are STAND-INS -- even the failure this test exists
to catch (a leak) lands on the stand-in, never on a real file. No model servers, no Orchestrator is
constructed, no sqlite3.connect is made. On top of that a sys.addaudithook (installed BEFORE the
first core import, the J-1718 method) RAISES on any write-mode open / sqlite3.connect / rename /
mkdir under the real C:\\Nascence\\data or under this tree's own data/ -- so a real write cannot
happen even if the stand-in plumbing were wrong; every such event is a hard FAIL, not advisory.
The real data/ top level of both trees is fingerprinted (size, mtime_ns) before and after as an
advisory line (Du's own continuous writers legitimately move files while Du is up).

Covers:
  0. premise: core is imported from THIS tree (not C:\\Nascence); every constant under test lives
     under core.profile._DATA -- including the advisor's LOG_JSONL_PATH, which used to hang off a
     literal absolute Path("c:/Nascence") (so from a worktree it was the REAL tree, and outside this
     tree's _DATA where the generic loop could not see it) and is now anchored to __file__
  1. activate_profile(<named>) rebases EVERY constant under test into the profile dir, and
     core.wandering now exposes a module constant at all
  2. a simulated harness cycle -- the real writer functions the audit caught, called directly as a
     NON-live process -- leaves every stand-in live file byte-identical (sha256 AND mtime_ns);
     unfenced writers land in the profile's own dir, fenced ones (wandering, coupling_rides;
     J-1821/J-1822) are refused by guard_path (D-0179/D-0200) and write nowhere
  3. the memory DB the emotion constructor's affective-retrieval shadow would open is the profile's
     own, not the live one
  4. re-activating the same / another profile never nests profile dirs
  5. activate_profile(None) (root alias = Carl) restores every live path -- the identity no-op
  6. the audit hook saw zero real-tree writes during the whole run

Expected: FAILS on a HEAD worktree without the J-1824 change (the unlisted constants stay at the
live path; core.wandering has no _LOG), PASSES with it.

Run: python scripts/_test_f2458_rebase_isolation.py   (exit 0 = all passed)
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile
import threading
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ── the audit hook: FIRST, before any core import (J-1718's method) ───────────────────────────────
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
    raise PermissionError(f"J-1824 test hook: blocked real-data {event} {path}")


sys.addaudithook(_hook)

import core  # noqa: E402  -- BEFORE anything else from the tree (and before any lab_env)
assert str(Path(core.__file__).resolve()).lower().startswith(str(TREE).lower()), core.__file__

import core.profile as P                      # noqa: E402
import core.arousal as A                      # noqa: E402
import core.wandering as W                    # noqa: E402
import core.emotion_construction as EC        # noqa: E402
import core.memory.store as S                 # noqa: E402
import core.attention_schema_loop as AST      # noqa: E402
import core.epistemic_affordance_advisor as EAA  # noqa: E402
import core.conversational_action as CA       # noqa: E402
import core.unified_inference as UI           # noqa: E402
import core.orchestrator as O                 # noqa: E402
import core.coupling_rides as CR              # noqa: E402

results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond)))
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  -- {detail}" if (detail and not cond) else ""))


def snap(path: Path):
    try:
        return (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
    except FileNotFoundError:
        return None


def fingerprint(root: Path, skip=("profiles",)):
    out = {}
    try:
        for p in root.iterdir():
            if p.name in skip:
                continue
            try:
                st = p.stat()
                out[p.name] = (st.st_size, st.st_mtime_ns)
            except OSError:
                pass
    except OSError:
        pass
    return out


# (module, attr, rel-path under data/) -- every constant F-2458 named, plus each module's own _DATA
SPEC = [
    (A,   "_DATA",                 Path(".")),
    (A,   "_STATE",                Path("arousal_state.json")),
    (A,   "_LOG",                  Path("arousal_shadow.jsonl")),
    (A,   "_REGIME_STATE",         Path("arousal_regime_shadow_state.json")),
    (W,   "_LOG",                  Path("wandering_log.jsonl")),
    (EC,  "_DATA",                 Path(".")),
    (EC,  "_SHADOW_LOG",           Path("emotion_construction_shadow.jsonl")),
    (EC,  "_AR_SHADOW_LOG",        Path("emotion_construction_affective_retrieval_shadow.jsonl")),
    (S,   "_RETRIEVE_LATENCY_LOG", Path("retrieve_latency_probe.jsonl")),
    (AST, "_DATA",                 Path(".")),
    (AST, "_LOG",                  Path("ast_loop_shadow.jsonl")),
    (AST, "_STATE",                Path("ast_loop_state.json")),
    (EAA, "LOG_JSONL_PATH",        Path("investigative_action_log.jsonl")),
    (CA,  "_LOG",                  Path("conversational_action_log.jsonl")),
    (UI,  "_UNIFIED_LOG",          Path("unified_inference_log.jsonl")),
    (O,   "_CORRELATION_LOG",      Path("correlation_log.jsonl")),
    (CR,  "_DATA",                 Path(".")),
    (CR,  "_LOG",                  Path("coupling_rides.jsonl")),
]
STAND_IN_FILES = sorted({rel for _, _, rel in SPEC if rel != Path(".")})

print("\n=== J-1824 / F-2458 -- 10-module rebase isolation (offline, tempdir stand-in, audit hook) ===\n")

# --- 0. premise (read BEFORE anything is patched) --------------------------------------------------
print("0. Premise")
check("core imported from the tree under test", Path(core.__file__).resolve().parent.parent == TREE, core.__file__)
REAL_DATA_BEFORE = fingerprint(Path(r"C:\Nascence\data"))
TREE_DATA_BEFORE = fingerprint(TREE / "data")
for mod, attr, rel in SPEC:
    v = getattr(mod, attr, None)
    if mod is W:
        # the whole point of the wandering code edit: a constant must exist for the rebase to see
        check("core.wandering exposes a module-level _LOG constant", isinstance(v, Path), f"got {v!r}")
        if not isinstance(v, Path):
            continue
    if mod is EAA:
        # J-1824: NASCE_ROOT was the literal Path("c:/Nascence") -- from a worktree that is the REAL
        # tree, and the generic rebase cannot see a constant outside this process's own _DATA.
        check("advisor NASCE_ROOT is anchored to THIS tree (__file__), not the literal c:/Nascence",
              EAA.NASCE_ROOT == TREE, f"{EAA.NASCE_ROOT} vs {TREE}")
    try:
        r = v.relative_to(P._DATA)
    except (ValueError, AttributeError):
        r = None
    check(f"{mod.__name__}.{attr} == core.profile._DATA / {rel.as_posix()!r}", r == rel, f"{v} vs _DATA={P._DATA}")

TMP = Path(tempfile.mkdtemp(prefix="j1824_f2458_iso_"))
OLD_NS = 1_700_000_000 * 10 ** 9            # a fixed old mtime: ANY rewrite is visible, even within one tick
try:
    FAKE_DATA = TMP / "data"
    (FAKE_DATA / "memory").mkdir(parents=True)

    def seed_live():
        for rel in STAND_IN_FILES:
            f = FAKE_DATA / rel
            f.write_text('{"stand_in": true, "cycles_since_spike": 7}\n', encoding="utf-8")
            os.utime(f, ns=(OLD_NS, OLD_NS))
        db = FAKE_DATA / "memory" / "nascence.db"
        db.write_bytes(b"stand-in, never opened")
        os.utime(db, ns=(OLD_NS, OLD_NS))

    def live_snaps():
        return {rel: snap(FAKE_DATA / rel) for rel in STAND_IN_FILES} | {Path("memory/nascence.db"): snap(FAKE_DATA / "memory" / "nascence.db")}

    # Point BOTH ends at the tempdir before anything under test can run.
    P._DATA = FAKE_DATA
    for mod, attr, rel in SPEC:
        if mod is W and not isinstance(getattr(W, "_LOG", None), Path):
            continue      # HEAD: nothing to re-point; the premise check above already failed
        setattr(mod, attr, FAKE_DATA if rel == Path(".") else FAKE_DATA / rel)
    S.DB_PATH = FAKE_DATA / "memory" / "nascence.db"      # activate_profile sets this by hand; keep it in the tempdir too
    seed_live()

    # --- 1. a named profile rebases every constant --------------------------------------------------
    print("\n1. activate_profile(<named>) rebases every constant F-2458 named")
    PROFILE = "_j1824_f2458_iso"
    base = P.activate_profile(PROFILE)
    check("profile dir is under the temp data root", base == FAKE_DATA / "profiles" / PROFILE, base)
    for mod, attr, rel in SPEC:
        expected = base if rel == Path(".") else base / rel
        got = getattr(mod, attr, None)
        check(f"{mod.__name__}.{attr} rebased into the profile dir", got == expected, f"{got} != {expected}")
    check("store.DB_PATH is the profile's own DB", S.DB_PATH == base / "memory" / "nascence.db", S.DB_PATH)

    # --- 2. a simulated harness cycle never touches the live stand-ins ----------------------------------
    print("\n2. The audit's own writers, called as a NON-live process, leave every live stand-in byte-identical")
    before = live_snaps()
    _live_flag = P.LIVE
    P.LIVE = False
    # core.arousal: _save (arousal_state.tmp -> .json), level() (arousal_shadow.jsonl, first call always logs),
    # regime_shadow_tick (arousal_regime_shadow_state.tmp -> .json)
    A._save({"last_alert_ts": time.time(), "last_alert_mag": 0.1, "last_alert_why": "j1824 probe"})
    A._last_log = 0.0
    A._cache.update({"level": None, "ts": 0.0})
    A.level()
    A.regime_shadow_tick(True)
    # core.wandering: fenced (J-1822) -- refused in a non-live named profile, swallowed, writes nowhere
    W._log_trail({"text": "j1824 probe", "origin": "sense", "via": "sense"})
    # core.memory.store: the retrieve() latency probe
    S._log_retrieve_latency(1, 1, 0.1, 0.1)
    # core.attention_schema_loop: observe_schema (ast_loop_shadow.jsonl + ast_loop_state.tmp)
    class _Schema:
        bandwidth = 0.5; driver = "probe"; fixated = False; focus = ["j1824"]
    AST.observe_schema(_Schema())
    # core.conversational_action / core.unified_inference: plain appends
    CA._log_row({"probe": "j1824"})
    UI.UnifiedInferenceGate().observe(None, {"curiosity": 0.1, "satisfaction": 0.2})
    # core.epistemic_affordance_advisor: the jsonl append only (its SQLite projection goes through
    # store._connect -> DB_PATH, deliberately not exercised here: no sqlite3.connect in this test)
    EAA.LOG_JSONL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(EAA.LOG_JSONL_PATH, "a", encoding="utf-8") as _f:
        _f.write(json.dumps({"probe": "j1824"}) + "\n")
    # core.coupling_rides: fenced (J-1821) -- same as wandering
    CR._append({"probe": "j1824"})
    # core.orchestrator: _log_correlation is a method; the constant check in 1. covers it, the
    # J-1718 driver re-run (J-1824's second verification) covers the call site
    O._CORRELATION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(O._CORRELATION_LOG, "a", encoding="utf-8") as _f:
        _f.write(json.dumps({"probe": "j1824"}) + "\n")
    P.LIVE = _live_flag
    after = live_snaps()
    for rel in before:
        check(f"live stand-in {rel.as_posix()} byte-identical (sha256 + mtime_ns)",
              after[rel] is not None and after[rel] == before[rel], f"before={before[rel]} after={after[rel]}")
    for rel in (Path("arousal_state.json"), Path("arousal_shadow.jsonl"), Path("arousal_regime_shadow_state.json"),
                Path("retrieve_latency_probe.jsonl"), Path("ast_loop_shadow.jsonl"), Path("ast_loop_state.json"),
                Path("conversational_action_log.jsonl"), Path("unified_inference_log.jsonl"),
                Path("investigative_action_log.jsonl"), Path("correlation_log.jsonl")):
        check(f"unfenced writer landed in the profile dir: {rel.as_posix()}", (base / rel).exists(), base / rel)
    for rel in (Path("wandering_log.jsonl"), Path("coupling_rides.jsonl")):
        check(f"fenced writer (D-0179) wrote nowhere: {rel.as_posix()}",
              not (base / rel).exists() and after[rel] == before[rel], base / rel)
    check("no stray .tmp left in the live stand-in dir",
          not any(p.suffix == ".tmp" for p in FAKE_DATA.iterdir()), [p.name for p in FAKE_DATA.iterdir()])

    # --- 3. the affective-retrieval shadow's DB is the profile's ----------------------------------------
    print("\n3. The emotion constructor's affective-retrieval shadow would open the profile DB, not the live one")
    check("EC._DATA / 'memory' / 'nascence.db' is the profile DB",
          EC._DATA / "memory" / "nascence.db" == base / "memory" / "nascence.db", EC._DATA)

    # --- 4. idempotent, never nests ----------------------------------------------------------------------
    print("\n4. Re-activation never nests")
    P.activate_profile(PROFILE)
    check("same profile again -> same paths",
          all(getattr(m, a) == (base if r == Path(".") else base / r) for m, a, r in SPEC), [str(getattr(m, a)) for m, a, _ in SPEC])
    other = P.activate_profile(PROFILE + "_b")
    check("another profile -> that profile's own paths (not nested)",
          other == FAKE_DATA / "profiles" / (PROFILE + "_b")
          and all(getattr(m, a) == (other if r == Path(".") else other / r) for m, a, r in SPEC),
          [str(getattr(m, a)) for m, a, _ in SPEC])

    # --- 5. root alias == identity no-op ----------------------------------------------------------------
    print("\n5. Root alias (Carl) is an identity no-op")
    P.activate_profile(None)
    for mod, attr, rel in SPEC:
        expected = FAKE_DATA if rel == Path(".") else FAKE_DATA / rel
        got = getattr(mod, attr, None)
        check(f"{mod.__name__}.{attr} back at the live path", got == expected, f"{got} != {expected}")
finally:
    shutil.rmtree(TMP, ignore_errors=True)

# --- 6. the hook ---------------------------------------------------------------------------------------
print("\n6. Audit hook")
check("zero real-tree write/connect events during the whole run", not HOOK_EVENTS, HOOK_EVENTS[:5])

# --- advisory: the REAL data/ of both trees ----------------------------------------------------------------
for label, root, b4 in (("C:\\Nascence\\data", Path(r"C:\Nascence\data"), REAL_DATA_BEFORE),
                        (str(TREE / "data"), TREE / "data", TREE_DATA_BEFORE)):
    now = fingerprint(root)
    changed = sorted(k for k in set(b4) | set(now) if b4.get(k) != now.get(k))
    if changed:
        print(f"\n  [WARN] {label} top level changed during this run: {changed[:20]} -- "
              f"if Du is live, its own writers may legitimately have moved these; otherwise investigate")
    else:
        print(f"\n  [info] {label} top level untouched by this run ({len(now)} entries)")

passed = sum(1 for _, ok in results if ok)
print(f"\n=== {passed}/{len(results)} passed ===")
sys.exit(0 if passed == len(results) else 1)
