"""J-2392 (sleep_as_a_mode, F-3094 follow-up): GIL-convoy harness for EVERY _sleep_off(...) sweep in
nodes/inner_monologue_node.py _enter_sleep, generalised from J-2379/J-2384's convoy_J-2384.py (book_residue only).

What it measures (per sweep, one fresh sandbox per run):
  victim    = a 2000-row sqlite fetch on the event-loop thread every 0.1 s (0.8-0.9 ms when the loop is free);
  heartbeat = lag of asyncio.sleep(0.5) on the loop;
  wall      = the awaited call itself.
modes: none   = no sweep, a 12 s idle window (baseline)
       thread = await core.sleep_offloop.off_loop(fn, *args) -- exactly the live path (asyncio.to_thread)
       inline = fn(*args) on the loop thread (the pre-J-1917 path; reference only)
       offproc = await the sweep's core.sleep_offloop.off_process wrapper (OFFPROC below; J-2403). The spawned
                 child gets a sitecustomize (via PYTHONPATH) installing the same audit guard as this parent:
                 the live data dir blocked outright, this tree's data/ blocked for writes, reads recorded; its events
                 come back in the RESULT as child_blocked / child_tree_read / child_live_touch.
  --log-tail REL: also report the last jsonl row of SBX/REL after the call (e.g. stick_test_log.jsonl).

ISOLATION (job isolation=required; never touches C:\\Nascence\\data):
  * the sandbox is a directory OUTSIDE every tree (argument --sbx), populated by copying the needed stores;
  * after importing the target, EVERY module-level pathlib.Path / absolute-path str in any loaded core.* / nodes.*
    module that points into this tree's data/ (or C:\\Nascence\\data) is rewritten to the same relative path under
    the sandbox (store.DB_PATH included), and re-applied after the call's lazy imports are known (probe mode);
  * a sys.addaudithook guard RAISES on any open / sqlite3.connect / rename / remove / mkdir that resolves into
    C:\\Nascence\\data or this tree's data/ -- reads included, so a missed redirect can only fail loudly, never
    read or write a live store; every read of a sandbox path that does not exist is recorded as `missing`
    (the probe mode prints them so the operator copies them in from the live tree, read-only);
  * profile.mark_live() is called so profile.guard_path() lets the redirected (sandbox) writes through exactly as
    in the live boot; the audit guard, not the fence, is the backstop.

Usage (from the tree under test):
  python scripts/lab_convoy_sweeps_J2392.py --sbx <dir> --sweep stick_test --mode thread [--rows 2000] [--probe]
  python scripts/lab_convoy_sweeps_J2392.py --list
Prints one RESULT line (json) per run.
"""
from __future__ import annotations

import argparse
import os as _os0
_os0.environ.setdefault("HF_HUB_OFFLINE", "1")        # no network check on the embedder load
_os0.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
import asyncio
import json
import logging
import os
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TREE_DATA = (ROOT / "data").resolve()
LIVE_DATA = Path(r"C:\Nascence\data")
_FORBIDDEN = [str(TREE_DATA).lower(), str(LIVE_DATA).lower()]   # the sandbox may lie under neither

import datetime as _dt
# the last "[night] waking:" line before the 2026-10-18 08:37 shutdown (log timestamps are local time)
LAST_WAKE_TS = _dt.datetime(2026, 10, 18, 4, 26, 56, 848000).timestamp()

# name -> (module, attribute path, args builder). Order = the order _enter_sleep awaits them.
SWEEPS = {
    "sleep_enter":          ("core.sleep_pressure", "sleep_enter", lambda: (LAST_WAKE_TS,)),
    "replay_strengthen":    ("core.memory.store", "replay_strengthen", lambda: (LAST_WAKE_TS,)),
    "affections":           ("core.affections", "synthesise", lambda: ()),
    "psyche_graph":         ("core.psyche_graph", "snapshot", lambda: ()),
    "stick_test":           ("core.stick_test", "snapshot", lambda: ()),
    "stick_census":         ("core.stick_test", "census", lambda: ()),   # J-2403: full per-object rows, identity check only
    "peer_metrics":         ("core.peer_metrics", "snapshot", lambda: ()),
    "holdrate":             ("core.commitment_ledger", "holdrate_snapshot", lambda: ()),
    "world_consolidation":  ("core.world_consolidation", "sweep", lambda: ()),
    "book_residue":         ("core.book_residue", "sweep", lambda: ()),
    "memory_lint":          ("core.memory_levels", "memory_lint", lambda: ()),
    "memory_edges":         ("core.memory_edges", "harvest_all", lambda: ()),
    "world_ledger":         ("core.world_ledger_ask", "refresh_offloop", lambda: ()),
    "bus_sync":             ("core.buses", "sync_investigation_calibration", lambda: ()),
    "monoculture":          ("core.monoculture", "snapshot", lambda: ()),
    "meta_awareness":       ("nodes.meta_awareness_node", "scan", lambda: ()),
    "downscale":            ("core.memory.store", "downscale_episodic", None),     # lambda wrapper, see _target
    "read_count":           ("core.memory.store", "read_count_importance_shadow", None),
    "dream_fade":           ("core.night", "dream_fade", lambda: ()),
    "epoch":                ("core.night", "epoch", lambda: (LAST_WAKE_TS, [])),
}

# J-2403: sweep -> (module, async zero-arg off_process wrapper)
OFFPROC = {
    "stick_test":   ("core.stick_test", "snapshot_offprocess"),
    "book_residue": ("core.book_residue", "sweep_offprocess"),
    "world_consolidation": ("core.world_consolidation", "sweep_offprocess"),   # J-2404
    "stick_census": ("__census__", None),   # off_process(core.stick_test.census) with stick_test's own mirror
}

_CHILD_GUARD = r'''
import os, sys, json
_LIVE = %(live)r; _TREE = %(tree)r; _SBX = %(sbx)r; _OUT = %(out)r
_fd = os.open(_OUT, os.O_WRONLY | os.O_CREAT | os.O_APPEND)
_busy = [False]
def _rec(kind, ev, s):
    _busy[0] = True
    try:
        os.write(_fd, (json.dumps([kind, ev, s]) + "\n").encode("utf-8"))
    finally:
        _busy[0] = False
def _norm(p):
    if isinstance(p, bytes): p = p.decode("utf-8", "replace")
    if not isinstance(p, (str, os.PathLike)): return None
    s = os.fspath(p)
    if s.startswith("file:"): s = s[5:].split("?", 1)[0]
    try: return os.path.abspath(s).lower()
    except Exception: return s.lower()
def _audit(event, args):
    if _busy[0] or event not in ("open", "sqlite3.connect", "os.rename", "os.remove", "os.mkdir", "os.rmdir",
                                 "os.listdir", "os.scandir", "shutil.copyfile", "shutil.rmtree", "os.truncate"):
        return
    paths = [args[0], args[1]] if event in ("os.rename", "shutil.copyfile") else [args[0]]
    write = event in ("os.rename", "os.remove", "os.mkdir", "os.rmdir", "shutil.rmtree", "os.truncate")
    if event == "open":
        mode = args[1] if len(args) > 1 else None; flags = args[2] if len(args) > 2 else 0
        if isinstance(mode, str): write = any(c in mode for c in "wax+")
        elif isinstance(flags, int): write = bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC))
    for i, p in enumerate(paths):
        s = _norm(p)
        if not s: continue
        w = write or (event == "shutil.copyfile" and i == 1)
        if s == _LIVE or s.startswith(_LIVE + os.sep) or (w and (s == _TREE or s.startswith(_TREE + os.sep))):
            _rec("blocked", event, s)
            raise PermissionError("J-2403 child isolation guard: %%s on non-sandbox data path %%s" %% (event, s))
        if s == _TREE or s.startswith(_TREE + os.sep): _rec("tree_read", event, s)
        if s.startswith("c:\\nascence"): _rec("live_touch", event, s)
        if w and s.startswith(_SBX + os.sep): _rec("sbx_write", event, s)
sys.addaudithook(_audit)
'''


def _install_child_guard(sbx: Path) -> Path:
    gdir = sbx.parent / (sbx.name + "_childguard_J2403")
    gdir.mkdir(exist_ok=True)
    out = gdir / "events.jsonl"
    out.write_text("", encoding="utf-8")
    (gdir / "sitecustomize.py").write_text(_CHILD_GUARD % {"live": str(LIVE_DATA).lower(), "tree": str(TREE_DATA).lower(),
                                                           "sbx": str(sbx).lower(), "out": str(out)}, encoding="utf-8")
    os.environ["PYTHONPATH"] = str(gdir) + (os.pathsep + os.environ["PYTHONPATH"] if os.environ.get("PYTHONPATH") else "")
    return out


GUARD = {"blocked": [], "missing": set(), "live_touch": [], "tree_read": []}
SBX: Path | None = None
_TR0 = [0]


def _norm(p) -> str | None:
    if isinstance(p, bytes):
        p = p.decode("utf-8", "replace")
    if not isinstance(p, (str, os.PathLike)):
        return None
    s = os.fspath(p)
    if s.startswith("file:"):
        s = s[5:].split("?", 1)[0]
    try:
        return os.path.abspath(s).lower()
    except Exception:
        return s.lower()


def _audit(event, args):
    if event not in ("open", "sqlite3.connect", "os.rename", "os.remove", "os.mkdir", "os.rmdir",
                     "os.listdir", "os.scandir", "shutil.copyfile", "shutil.rmtree", "os.truncate"):
        return
    paths = [args[0]] if event != "os.rename" else [args[0], args[1]]
    if event == "shutil.copyfile":
        paths = [args[0], args[1]]
    write = event in ("os.rename", "os.remove", "os.mkdir", "os.rmdir", "shutil.rmtree", "os.truncate",
                      "sqlite3.connect")
    if event == "open":
        mode = args[1] if len(args) > 1 else None
        flags = args[2] if len(args) > 2 else 0
        if isinstance(mode, str):
            write = any(c in mode for c in "wax+")
        elif isinstance(flags, int):
            write = bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC))
    live = str(LIVE_DATA).lower()
    tree = str(TREE_DATA).lower()
    for i, p in enumerate(paths):
        s = _norm(p)
        if not s:
            continue
        w = write or (event == "shutil.copyfile" and i == 1)
        # C:\Nascence\data: nothing at all (reads too). This tree's data/: no writes; reads recorded.
        if s == live or s.startswith(live + os.sep) or (w and (s == tree or s.startswith(tree + os.sep))):
            GUARD["blocked"].append((event, s))
            raise PermissionError(f"J-2392 isolation guard: {event} on non-sandbox data path {s}")
        if s == tree or s.startswith(tree + os.sep):
            fr = sys._getframe(1); where = ""
            while fr is not None:
                fn_ = fr.f_code.co_filename.lower()
                if (os.sep + "core" + os.sep) in fn_ or (os.sep + "nodes" + os.sep) in fn_:
                    where += f"{os.path.basename(fn_)}:{fr.f_lineno}:{fr.f_code.co_name} < "
                    if where.count("<") >= 3: break
                fr = fr.f_back
            GUARD["tree_read"].append((event, s, where))
        if s.startswith(r"c:\nascence"):
            GUARD["live_touch"].append((event, s))
        if SBX is not None and event in ("open", "os.listdir", "os.scandir", "sqlite3.connect"):
            sb = str(SBX).lower()
            if s.startswith(sb + os.sep) and not os.path.exists(s):
                mode = args[1] if event == "open" and len(args) > 1 else "r"
                if event != "open" or (isinstance(mode, str) and "r" in mode and "+" not in mode) or mode is None:
                    GUARD["missing"].add(os.path.relpath(s, sb))


def _redirect_value(v):
    if isinstance(v, Path):
        s = str(v.resolve() if not v.is_absolute() else v).lower()
    elif isinstance(v, str) and len(v) > 3 and (v[1:3] == ":\\" or v[1:3] == ":/"):
        s = os.path.abspath(v).lower()
    else:
        return None
    for base in (str(TREE_DATA).lower(), str(LIVE_DATA).lower()):
        if s == base or s.startswith(base + os.sep):
            rel = s[len(base):].lstrip("\\/")
            # keep the original casing of the relative part
            orig = str(v)
            tail = orig[len(orig) - len(rel):] if rel else ""
            new = SBX / tail if tail else SBX
            return new if isinstance(v, Path) else str(new)
    return None


def redirect_all() -> int:
    n = 0
    for name, mod in list(sys.modules.items()):
        if not (name == "core" or name.startswith("core.") or name == "nodes" or name.startswith("nodes.")):
            continue
        f = getattr(mod, "__file__", "") or ""
        if not f.lower().startswith(str(ROOT).lower()):
            raise RuntimeError(f"{name} imported from {f}, not the tree under test {ROOT}")
        for attr, v in list(vars(mod).items()):
            # function default arguments are bound at def time (def load_rows(path=_TUPLES)): rewrite them too
            fobjs = [v] if callable(v) and hasattr(v, "__defaults__") else []
            if isinstance(v, type) and getattr(v, "__module__", None) == name:
                fobjs += [m for m in vars(v).values() if hasattr(m, "__defaults__")]
            for fo in fobjs:
                if getattr(fo, "__module__", None) != name:
                    continue
                d = getattr(fo, "__defaults__", None)
                if d:
                    nd = tuple(_redirect_value(x) or x for x in d)
                    if nd != d:
                        fo.__defaults__ = nd; n += 1
                kd = getattr(fo, "__kwdefaults__", None)
                if kd:
                    nk = {k: (_redirect_value(x) or x) for k, x in kd.items()}
                    if nk != kd:
                        fo.__kwdefaults__ = nk; n += 1
            nv = _redirect_value(v)
            if nv is not None and nv != v:
                setattr(mod, attr, nv)
                n += 1
            if nv is not None:
                try:
                    _REDIR.add(os.path.relpath(str(nv), str(SBX)))
                except ValueError:
                    pass
    return n


_SEEN_MODS: set = set()


def install_import_redirect():
    """Redirect every core.*/nodes.* module imported LATER (a sweep's function-level lazy imports) the moment its
    import returns, before the caller can use its path constants."""
    import builtins
    orig = builtins.__import__
    _SEEN_MODS.update(sys.modules)

    def _imp(name, globals=None, locals=None, fromlist=(), level=0):
        m = orig(name, globals, locals, fromlist, level)
        if len(sys.modules) != len(_SEEN_MODS):
            # a module still executing its body (nested import) is skipped until its own import returns
            new = [k for k, mm in list(sys.modules.items()) if k not in _SEEN_MODS
                   and not getattr(getattr(mm, "__spec__", None), "_initializing", False)]
            _SEEN_MODS.update(new)
            if any(k == "core" or k.startswith(("core.", "nodes.")) for k in new):
                _LAZY[0] += redirect_all()
        return m
    builtins.__import__ = _imp
    import importlib
    orig_im = importlib.import_module

    def _im(name, package=None):   # importlib.import_module does not go through builtins.__import__
        m = orig_im(name, package)
        _imp("sys")
        return m
    importlib.import_module = _im


_LAZY = [0]
_REDIR: set = set()


def _target(name):
    import importlib
    modname, attr, argsb = SWEEPS[name]
    mod = importlib.import_module(modname)
    fn = getattr(mod, attr)
    if name == "downscale":
        return (lambda: fn(since_ts=LAST_WAKE_TS)), ()
    if name == "read_count":
        return (lambda: fn(since_ts=LAST_WAKE_TS)), ()
    return fn, argsb()


class _Cap(logging.Handler):
    def __init__(self):
        super().__init__(); self.lines = []
    def emit(self, r):
        try:
            self.lines.append(f"{r.levelname} {r.name} | {r.getMessage()[:240]}")
        except Exception:
            pass


def _summ(x):
    if x is None:
        return None
    try:
        s = json.dumps(x, default=str)
    except Exception:
        s = repr(x)
    return s[:300]


async def run(name, mode, nrows, probe, idle_s, log_tail=None):
    global SBX
    sys.addaudithook(_audit)
    cap = _Cap(); logging.getLogger().addHandler(cap); logging.getLogger().setLevel(logging.INFO)
    sys.path.insert(0, str(ROOT)); os.chdir(ROOT)
    import core
    assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
    from core import profile
    from core.memory import store
    from core import sleep_offloop
    profile.mark_live()
    child_events = None
    if mode == "offproc":
        child_events = _install_child_guard(SBX)   # before any child can spawn
    if name != "none":
        fn, args = _target(name)
    else:
        fn, args = None, ()
    nred = redirect_all()
    _TR0[0] = len(GUARD["tree_read"])
    install_import_redirect()
    # the live boot has the sentence-transformers embedder loaded long before any sleep: load it here, outside the
    # measured window, so a sweep's first _embed() is not a cold model load (measured 70 s on the first epoch probe)
    t_w = time.perf_counter()
    try:
        store._embed("warm up the embedder")
    except Exception:
        pass
    warm_s = time.perf_counter() - t_w
    assert str(store.DB_PATH).lower().startswith(str(SBX).lower()), store.DB_PATH
    db = str(store.DB_PATH)
    vconn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    q_sql = f"SELECT timestamp FROM memory_fragments LIMIT {nrows}"
    vconn.execute(q_sql).fetchall()
    stop = False; vict = []; hb = []; vict_t = []

    async def victim():
        while not stop:
            t = time.perf_counter(); vconn.execute(q_sql).fetchall(); vict.append(time.perf_counter() - t); vict_t.append(t)
            await asyncio.sleep(0.1)

    async def heartbeat():
        while not stop:
            due = time.perf_counter() + 0.5; await asyncio.sleep(0.5); hb.append(time.perf_counter() - due)

    tv = asyncio.create_task(victim()); th = asyncio.create_task(heartbeat())
    await asyncio.sleep(1.0)
    n0v, n0h = len(vict), len(hb)
    err = None; out = None
    T0 = time.perf_counter()
    try:
        if mode == "none" or fn is None:
            await asyncio.sleep(idle_s)
        elif mode == "thread":
            assert sleep_offloop.SLEEP_SWEEPS_OFFLOOP
            out = await sleep_offloop.off_loop(fn, *args)
        elif mode == "inline":
            out = fn(*args)
        elif mode == "offproc":
            import importlib
            omod, oattr = OFFPROC[name]
            if omod == "__census__":
                from core import stick_test as _stk
                out = await sleep_offloop.off_process("core.stick_test", "census", zero={},
                                                      mirror=_stk._OFFPROCESS_MIRROR)
            else:
                out = await getattr(importlib.import_module(omod), oattr)()
    except Exception as exc:
        err = f"{type(exc).__name__}: {exc}"[:300]
    T1 = time.perf_counter()
    # keep the probes running a little past the call so a lag that ends with it is still sampled
    await asyncio.sleep(0.6)
    stop = True; await tv; await th
    v = sorted(vict[n0v:]) or [0.0]; h = hb[n0h:] or [0.0]
    # J-2403: when (relative to the call's start) the slowest victim fetches began, and the >50 ms count
    _vw = [(d, t - T0) for d, t in zip(vict[n0v:], vict_t[n0v:])]
    _slow = sorted(_vw, reverse=True)[:3]
    late_lazy = redirect_all()   # modules the call imported lazily: any non-zero count = a path that was live-pathed
    res = {"sweep": name, "mode": mode, "rows": nrows, "wall_s": round(T1 - T0, 3),
           "victim_n": len(vict) - n0v, "victim_median_ms": round(v[len(v) // 2] * 1000, 1),
           "victim_max_ms": round(v[-1] * 1000, 1), "hb_n": len(hb) - n0h, "victim_gt50ms": sum(1 for d, _ in _vw if d > 0.05),
           "victim_slowest_at_s": [[round(d * 1000, 1), round(t, 2)] for d, t in _slow], "hb_max_lag_s": round(max(h), 3),
           "stalls_gt2s": sum(1 for x in h if x > 2), "error": err, "out": _summ(out),
           "embedder_warm_s": round(warm_s, 2), "redirected": nred, "lazy_redirected": _LAZY[0], "late_redirect_needed": late_lazy,
           "guard_blocked": GUARD["blocked"][:10], "live_touch": sorted(set(GUARD["live_touch"]))[:10],
           "tree_read_after_redirect": sorted(set(GUARD["tree_read"][_TR0[0]:]))[:20],
           "missing": sorted(GUARD["missing"])[:60],
           # path constants (any loaded module) whose live counterpart exists but the sandbox copy does not --
           # Path.exists() emits no audit event, so a module that checks before reading would silently see nothing
           "unpopulated": sorted(r for r in _REDIR if r not in (".", "") and not (SBX / r).exists()
                                 and (LIVE_DATA / r).exists())}
    if child_events is not None:
        ev = [json.loads(l) for l in open(child_events, encoding="utf-8") if l.strip()]
        res["child_blocked"] = [e for e in ev if e[0] == "blocked"][:10]
        res["child_live_touch"] = sorted({e[2] for e in ev if e[0] == "live_touch"})[:10]
        res["child_tree_read"] = sorted({e[2] for e in ev if e[0] == "tree_read"})[:20]
        res["child_sbx_writes"] = sorted({os.path.relpath(e[2], str(SBX).lower()) for e in ev if e[0] == "sbx_write"})[:20]
        res["child_events_n"] = len(ev)
    if out is not None:
        try:
            res["out_full"] = json.loads(json.dumps(out, default=str))
        except Exception:
            pass
    if log_tail:
        lp = SBX / log_tail
        try:
            lines = [l for l in open(lp, encoding="utf-8") if l.strip()]
            res["log_rows"] = len(lines); res["log_tail"] = json.loads(lines[-1]) if lines else None
        except Exception as exc:
            res["log_tail_error"] = repr(exc)[:200]
    res["log_lines"] = [l for l in cap.lines if "stick-test" in l or "off_process" in l or "fence" in l][:20]
    print("RESULT " + json.dumps(res), flush=True)
    if probe:
        for l in cap.lines[-40:]:
            print("   log:", l)


def main():
    global SBX
    ap = argparse.ArgumentParser()
    ap.add_argument("--sbx"); ap.add_argument("--sweep", default="none")
    ap.add_argument("--mode", default="thread", choices=["none", "thread", "inline", "offproc"])
    ap.add_argument("--rows", type=int, default=2000); ap.add_argument("--probe", action="store_true")
    ap.add_argument("--idle", type=float, default=12.0); ap.add_argument("--list", action="store_true")
    ap.add_argument("--log-tail", default=None)
    a = ap.parse_args()
    if a.list:
        print("\n".join(SWEEPS)); return
    SBX = Path(a.sbx).resolve()
    for f in _FORBIDDEN:
        assert not str(SBX).lower().startswith(f), SBX
    assert (SBX / "memory" / "nascence.db").exists(), "sandbox has no memory/nascence.db copy"
    asyncio.run(run(a.sweep, a.mode, a.rows, a.probe, a.idle, a.log_tail))


if __name__ == "__main__":
    main()
