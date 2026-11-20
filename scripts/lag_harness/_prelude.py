"""scripts/lag_harness/_prelude.py (J-1892, F-2540): safety prelude for offline timing scripts (audit hook: no write under live C:/Nascence outside LAGH_SCRATCH, no subprocess but nvidia-smi/rocm-sdk, network blocked once _NET['block'] is set AFTER the event loop exists; needs env LAGH_SCRATCH, optional LAGH_WT). Originally part of the harness:
on the throwaway worktree's FULL-fidelity data copy (small+medium stores, DB backup copy). No model calls, no network, no subprocess
(audit hook), no write outside the scratchpad (audit hook). Usage: python loop_lag_harness.py <seconds> <outjson> [--no-climate] [--profile]"""
import sys, os, time, json, asyncio, pathlib, statistics as st, collections, traceback

SP = pathlib.Path(os.environ["LAGH_SCRATCH"])   # the scratch dir that holds the throwaway worktree (+ its data/ copy)
WT = SP / os.environ.get("LAGH_WT", "wt_head")
LIVE_ROOT = os.path.normcase(r"C:\Nascence")
SP_N = os.path.normcase(str(SP))

# ---------- safety net: audit hook ----------
def _norm(p):
    try:
        if isinstance(p, int): return None
        if isinstance(p, bytes): p = p.decode("utf-8", "replace")
        return os.path.normcase(os.path.abspath(os.fspath(p)))
    except Exception:
        return None

def _under_live(n):
    return n is not None and (n == LIVE_ROOT or n.startswith(LIVE_ROOT + os.sep)) and not n.startswith(SP_N)

_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC
def _hook(event, args):
    try:
        if event == "open":
            path, mode, flags = args[0], args[1], args[2]
            n = _norm(path)
            if _under_live(n):
                w = False
                if isinstance(mode, str) and any(c in mode for c in "wax+"): w = True
                if isinstance(flags, int) and (flags & _WRITE_FLAGS): w = True
                if w: raise PermissionError("lag_harness audit: write under live C:\\Nascence refused: %s" % n)
        elif event in ("os.rename", "os.replace"):
            for p in args[:2]:
                if _under_live(_norm(p)): raise PermissionError("lag_harness audit: rename under live refused")
        elif event in ("os.remove", "os.rmdir", "os.mkdir", "os.truncate", "shutil.rmtree", "os.chmod"):
            if _under_live(_norm(args[0])): raise PermissionError("lag_harness audit: %s under live refused" % event)
        elif event in ("shutil.copyfile", "shutil.copy", "shutil.move", "shutil.copytree"):
            for p in args[:2]:
                if _under_live(_norm(p)) and p is args[1]: raise PermissionError("lag_harness audit: copy into live refused")
        elif event == "sqlite3.connect":
            if _under_live(_norm(args[0])): raise PermissionError("lag_harness audit: sqlite3 connect to live refused")
        elif event == "socket.connect":
            if _NET["block"]: raise PermissionError("lag_harness audit: no network")
        elif event == "subprocess.Popen":
            exe = str(args[0]); cmd = args[1]
            _SUBP.append((exe, str(cmd)[:160]))
            if not any(w in (exe.lower()+" "+str(cmd).lower()) for w in ("nvidia-smi","rocm-sdk","hipconfig")):
                raise PermissionError("lag_harness audit: no subprocess (%s)" % str(cmd)[:80])
        elif event in ("os.system", "os.exec", "os.posix_spawn", "os.spawn"):
            raise PermissionError("lag_harness audit: no subprocess")
    except PermissionError:
        raise
    except Exception:
        pass
_NET={'block':False}; _SUBP=[]
sys.addaudithook(_hook)
try:   # asyncio on Windows connects through overlapped ConnectEx, which raises NO 'socket.connect' audit event
    import asyncio.windows_events as _we
    _orig_connect = _we.IocpProactor.connect
    def _blocked_connect(self, *a, **k):
        if _NET["block"]: raise PermissionError("lag_harness audit: no network (IocpProactor.connect)")
        return _orig_connect(self, *a, **k)
    _we.IocpProactor.connect = _blocked_connect
except Exception:
    pass

os.environ.setdefault("HF_HUB_OFFLINE", "1"); os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
sys.path.insert(0, str(WT)); os.chdir(WT)
import core
assert str(pathlib.Path(core.__file__).resolve()).lower().startswith(str(WT).lower()), core.__file__
from core import profile
assert str(profile._DATA).lower().startswith(str(WT).lower()), profile._DATA
profile.mark_live()      # the worktree's own _DATA only; the audit hook above refuses any write under live C:\Nascence
from core.memory import store
assert str(store.DB_PATH).lower().startswith(str(WT).lower()), store.DB_PATH

