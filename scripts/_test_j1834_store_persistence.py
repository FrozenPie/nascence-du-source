"""
J-1834 / D-0347 / F-2401 item 3: core/frontier.py and core/pursuits.py persistence hardening.
Torn-file fixtures, save-under-reader, killed-mid-write, move-aside. ISOLATED: every store is redirected to a
fresh temp dir BEFORE any write; the live data/frontier*.json and data/pursuits_active.json are only
sha256-hashed (read-only canary) before and after.

Run:  python scripts/_test_j1834_store_persistence.py                 (new code, expect FAILS = 0)
      J1834_HEAD=1 python scripts/_test_j1834_store_persistence.py    (pre-change HEAD modules loaded from
                                                                       git; expect FAILS > 0)
"""
from __future__ import annotations
import hashlib, importlib, importlib.util, json, logging, os, subprocess, sys, tempfile, threading, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core                                                   # noqa: E402  (BEFORE anything else)
assert Path(core.__file__).resolve().is_relative_to(ROOT), f"core resolves outside the tree under test: {core.__file__}"
print("core ->", core.__file__)
HEAD = bool(os.environ.get("J1834_HEAD"))

LIVE = Path(r"C:\Nascence\data")
CANARY = [LIVE / n for n in ("frontier.json", "frontier.light.json", "pursuits_active.json")]


def _h(p):
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return None


def _snap():
    return {str(p): (_h(p), p.stat().st_mtime_ns if p.exists() else None) for p in CANARY}


before = _snap()

TMP = Path(tempfile.mkdtemp(prefix="j1834_"))
print("isolated dir:", TMP)
fails = 0


def check(cond, msg):
    global fails
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond:
        fails += 1


class Cap(logging.Handler):
    def __init__(self):
        super().__init__()
        self.recs = []

    def emit(self, r):
        self.recs.append(r)


def capture(name):
    h = Cap()
    lg = logging.getLogger(name)
    lg.addHandler(h)
    lg.setLevel(logging.DEBUG)
    lg.propagate = False
    return h


def load_mod(modname, relpath):
    if HEAD:
        src = subprocess.run(["git", "show", f"HEAD:{relpath}"], cwd=ROOT, capture_output=True, check=True).stdout
        p = TMP / f"head_{modname}.py"
        p.write_bytes(src)
        spec = importlib.util.spec_from_file_location(f"head_{modname}", p)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m
    return importlib.import_module(f"core.{modname}")


fr = load_mod("frontier", "core/frontier.py")
pu = load_mod("pursuits", "core/pursuits.py")
if not HEAD:
    sp = importlib.import_module("core.store_persist")
    assert Path(sp.__file__).resolve().is_relative_to(ROOT)


def questions(n):
    return {"questions": [{"q": f"Why does thing {i} happen? \u2014 \u00e9", "status": "open", "n": i} for i in range(n)]}


def pursuits(n):
    return [{"id": f"p{i}", "topic": f"t{i} \u2014 \u00e9", "status": "active", "thoughts": ["a", "b"]} for i in range(n)]


class Store:
    """adapter so the same scenarios run on both stores"""

    def __init__(self, name):
        self.name = name
        self.dir = TMP / name
        self.dir.mkdir()
        if name == "frontier":
            self.path = self.dir / "frontier.json"
            fr._F = self.path
            fr._F_LIGHT = self.dir / "frontier.light.json"
            self.load, self.save, self.mk = fr._load, fr._save, questions
            self.empty = {"questions": []}
            self.old_text = lambda d: json.dumps(d, ensure_ascii=False)
            self.logname = "nascence.frontier" if not HEAD else "nascence.frontier"
        else:
            self.path = self.dir / "pursuits_active.json"
            pu._DIR = self.dir
            pu._ACTIVE = self.path
            pu._SHADOW = self.dir / "s.jsonl"
            self.load, self.save, self.mk = pu._load, pu._save, pursuits
            self.empty = []
            self.old_text = lambda d: json.dumps(d, ensure_ascii=False, indent=1)
            self.logname = "nascence.pursuits"
        self.cap = capture(self.logname)

    def reset(self):
        for f in self.dir.iterdir():
            f.unlink()
        self.cap.recs.clear()

    def files(self):
        return sorted(f.name for f in self.dir.iterdir())

    def corrupt(self):
        return sorted(f for f in self.dir.iterdir() if ".corrupt." in f.name)

    def msgs(self, lvl=0):
        return [r.getMessage() for r in self.cap.recs if r.levelno >= lvl]

    def tmps(self):      # the HEAVY store's own temp file (the light sidecar's tmp is a different module)
        return [f for f in self.files() if f == self.path.name + ".tmp"]


for name in ("frontier", "pursuits"):
    S = Store(name)
    print(f"\n=== {name} ===")

    print("[1] healthy path unchanged")
    S.reset()
    d = S.mk(50)
    S.save(d)
    old = TMP / "old_writer.bin"
    old.write_text(S.old_text(d), encoding="utf-8")        # what the pre-change in-place writer produced
    check(S.path.read_bytes() == old.read_bytes(), "healthy save is byte-identical to the old in-place writer's output")
    check(S.load() == d, "healthy load returns the stored value")
    check(not S.tmps(), "no .tmp left behind")
    check(not S.corrupt() and not S.msgs(logging.WARNING), "healthy load: nothing moved aside, no warning")

    print("[2] missing file = normal first boot")
    S.reset()
    check(S.load() == S.empty, "missing file -> empty store")
    check(not S.files() and not S.msgs(logging.INFO), "silent, nothing created")

    print("[3] torn / unreadable file")
    for label, blob in (("truncated JSON", S.old_text(S.mk(50)).encode("utf-8")[:900]), ("zero bytes", b""),
                        ("invalid utf-8", b"\xff\xfe\x00bad")):
        S.reset()
        S.path.write_bytes(blob)
        r = S.load()
        check(r == S.empty, f"{label}: empty store returned exactly as before")
        c = S.corrupt()
        check(len(c) == 1 and c[0].read_bytes() == blob,
              f"{label}: moved (not rewritten) to <stem>.corrupt.<UTC stamp>.json, byte-identical")
        check(not S.path.exists(), f"{label}: original path is gone")
        w = [m for m in S.msgs(logging.WARNING) if "STATE FILE UNREADABLE" in m]
        check(len(w) == 1 and f"({len(blob)} bytes)" in w[0] and "Moved it aside" in w[0],
              f"{label}: exactly one loud WARNING naming the size and the move")
        check(len(S.files()) == 1, f"{label}: nothing else appeared (no automatic restore)")
        S.save(S.mk(3))
        check(len(S.corrupt()) == 1 and S.corrupt()[0].read_bytes() == blob,
              f"{label}: the next save leaves the moved file untouched")

    print("[4] move-aside itself blocked / two quarantines in one second")
    S.reset()
    S.path.write_bytes(b"{torn")
    if not HEAD:
        real = sp.os.replace
        sp.os.replace = lambda a, b: (_ for _ in ()).throw(PermissionError("blocked"))
        try:
            r = S.load()
        finally:
            sp.os.replace = real
        check(r == S.empty and S.path.exists() and any("AND could not be moved aside" in m for m in S.msgs(logging.ERROR)),
              "move blocked: no raise, empty store, file stays put, an ERROR says so")
        S.reset()
        for i in range(2):
            S.path.write_bytes(b"{torn%d" % i)
            S.load()
        names = [c.name for c in S.corrupt()]
        check(len(names) == 2 and len(set(names)) == 2, "two quarantines get distinct names and both survive")
        # a transient READ collision must not be mistaken for corruption (the D-0347 defeater)
        S.reset()
        good = S.mk(10)
        S.save(good)
        sp.READ_DELAY_S = 0.01
        real_rt = Path.read_text
        n = {"c": 0}

        def flaky_read(self, *a, **k):
            if self == S.path and n["c"] < 2:
                n["c"] += 1
                raise PermissionError("WinError 32")
            return real_rt(self, *a, **k)
        Path.read_text = flaky_read
        try:
            r = S.load()
        finally:
            Path.read_text = real_rt
        check(r == good and not S.corrupt() and n["c"] == 2, "a transient read collision is retried, NOT moved aside as 'corrupt'")
    else:
        check(False, "(HEAD has no move-aside at all)")

    print("[5] save failure paths (previous file must survive)")
    S.reset()
    base = S.mk(20)
    S.save(base)
    if not HEAD:
        sp.REPLACE_DELAY_S = 0.01
        calls = {"n": 0}
        real = sp.os.replace

        def flaky(a, b):
            if Path(b) != S.path:          # the light sidecar's own os.replace is not under test
                return real(a, b)
            calls["n"] += 1
            if calls["n"] <= 2:
                raise PermissionError("WinError 5")
            return real(a, b)
        sp.os.replace = flaky
        try:
            S.save(S.mk(21))
        finally:
            sp.os.replace = real
        check(calls["n"] == 3 and S.load() == S.mk(21) and not S.tmps(), "replace blocked twice: retried, the save landed, no .tmp left")
        S.reset()
        S.save(base)
        S.cap.recs.clear()
        def blocked(a, b):
            if Path(b) != S.path:
                return real(a, b)
            raise PermissionError("WinError 5")
        sp.os.replace = blocked
        t0 = time.time()
        try:
            S.save(S.mk(22))
        finally:
            sp.os.replace = real
        check(S.load() == base, "replace blocked for good: previous file intact")
        check(not S.tmps(), "...no .tmp left")
        check(any("save failed" in m for m in S.msgs(logging.WARNING)), "...logged at WARNING (was silent / debug)")
        check(time.time() - t0 < 3, "...bounded wait")
        # dump failure mid-write
        S.reset()
        S.save(base)
        keep = S.path.read_bytes()
        import builtins
        real_write = None

        class Boom:
            def __init__(s, f):
                s.f = f

            def __enter__(s):
                return s

            def __exit__(s, *a):
                s.f.close()

            def write(s, t):
                s.f.write(t[:50])
                raise OSError("disk full")
        real_open = sp.__dict__.get("open")
        sp.open = lambda p, *a, **k: Boom(builtins.open(p, *a, **k))
        try:
            S.save(S.mk(30))
        finally:
            del sp.open
        check(S.path.read_bytes() == keep and not S.tmps(), "write fails mid-way: previous file byte-intact, partial .tmp removed")
        # a REAL reader handle blocks os.replace on Windows
        S.reset()
        S.save(base)
        h = open(S.path, "rb")

        def closer():
            time.sleep(0.35)
            h.close()
        th = threading.Thread(target=closer)
        th.start()
        sp.REPLACE_DELAY_S = 0.1
        t0 = time.time()
        S.save(S.mk(23))
        th.join()
        check(S.load() == S.mk(23) and time.time() - t0 >= 0.3,
              "a REAL reader handle blocks os.replace on Windows: the save waited for it and landed")
    else:
        check(False, "(HEAD has no retry/atomic write)")

    print("[6] process killed in the MIDDLE of a real save")
    S.reset()
    base = S.mk(2000)
    S.save(base)
    keep = S.path.read_bytes()
    child = TMP / f"child_{name}.py"
    child.write_text(f'''
import sys, io, time, importlib, importlib.util, builtins
from pathlib import Path
sys.path.insert(0, r"{ROOT}")
import core
HEAD = {HEAD!r}
name = {name!r}
modname = "frontier" if name == "frontier" else "pursuits"
if HEAD:
    spec = importlib.util.spec_from_file_location("head_" + modname, r"{TMP}" + "/head_" + modname + ".py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
else:
    m = importlib.import_module("core." + modname)
d = Path(r"{S.dir}")
if name == "frontier":
    m._F = d / "frontier.json"; m._F_LIGHT = d / "frontier.light.json"
else:
    m._DIR = d; m._ACTIVE = d / "pursuits_active.json"
class Half:
    def __init__(s, real): s.r = real
    def __enter__(s): return s
    def __exit__(s, *a): s.r.close()
    def write(s, text):
        s.r.write(text[: len(text) // 2]); s.r.flush(); print("READY", flush=True); time.sleep(120)
    def __getattr__(s, k): return getattr(s.r, k)
_orig = io.open
def patched(file, mode="r", *a, **k):
    f = _orig(file, mode, *a, **k)
    if "w" in mode and ("frontier" in str(file) or "pursuits_active" in str(file)) and "light" not in str(file):
        return Half(f)
    return f
io.open = patched
builtins.open = patched
sp = sys.modules.get("core.store_persist")
if sp: sp.open = patched
items = ({{"questions": [{{"q": "Why does thing %d happen? x" % i, "status": "open"}} for i in range(2500)]}}
         if name == "frontier" else [{{"id": "p%d" % i, "topic": "t%d" % i, "status": "active"}} for i in range(2500)])
m._save(items)
''', encoding="utf-8")
    p = subprocess.Popen([sys.executable, str(child)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    line = p.stdout.readline().strip()
    err = ""
    if line != "READY":
        p.kill()
        err = p.stderr.read()[-300:]
    check(line == "READY", f"child reached the middle of a real _save() write (got {line!r} {err})")
    p.kill()
    p.wait()
    p.stdout.close()
    p.stderr.close()
    after = S.path.read_bytes() if S.path.exists() else b""
    check(after == keep, "killed mid-write: the store file is byte-identical to before the write began"
          + ("" if after == keep else f" (now {len(after)} bytes)"))
    S.cap.recs.clear()
    r = S.load()
    check(r == base, "next boot after the kill: the pre-kill content loads (NOT a silent empty store)")
    check(not S.corrupt(), "...nothing quarantined (the file was never torn)")
    if not HEAD:
        S.save(S.mk(5))
        check(S.load() == S.mk(5) and not S.tmps(), "the stale half-written .tmp is simply overwritten by the next save")

after = _snap()
check(after == before, "canary: live data/frontier.json, frontier.light.json, pursuits_active.json unchanged (sha256 + mtime)")
print(f"\nFAILS = {fails}  ({'HEAD pre-change modules' if HEAD else 'new modules'})")
sys.exit(1 if fails else 0)
