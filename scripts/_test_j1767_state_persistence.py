"""Regression for J-1767 / D-0339 part (d) (Travis 2026-10-04; evidence F-2314): nodes/subconscious_node.py's
persistence of data/subconscious_state.json.

  save  -- _save_state() used to rewrite the heavy file IN PLACE (open "w" + json.dump: truncate, then ~5 s of
           writing on a 46 MB file). A process that died inside that window left a torn file (2026-09-28 21:54).
           Now: same bytes, written to <file>.tmp and os.replace'd, with a short bounded retry because on Windows
           os.replace raises PermissionError (WinError 5) while any reader holds the destination open.
  load  -- _load_or_init_state() swallowed ANY exception (bare `except: pass`) and returned a FRESH state (scan
           140361 -> 1), silently. Now: a loud WARNING (exception + size + new path) and the unreadable file is
           MOVED to subconscious_state.corrupt.<UTC stamp>.json, never deleted; still no restore from a backup.

Runs entirely inside lab_env.isolate(also=[(module, ["_STATE_FILE", "_LIGHT_FILE"])], db="empty") on a COPY of the
live state (data/_lab/<ts>/); the live data/subconscious_state.json and its light sidecar are sha256-hashed before
and after (nothing under data/_hold or data/backups is ever opened). The decisive case kills a child process in the
middle of a real _save_state() write -- the F-2314 failure itself, no exception handler gets to run.

    python scripts/_test_j1767_state_persistence.py
    J1767_MODULE=<path to another subconscious_node.py> python scripts/_test_j1767_state_persistence.py
        (the same assertions against e.g. HEAD's pre-J-1767 file -- the failure-injection / kill / quarantine cases
         FAIL there, which is what "fails without the change" means)
"""
from __future__ import annotations
import hashlib, importlib.util, json, logging, os, shutil, subprocess, sys, tempfile, threading, time
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
# lab_env hard-codes C:\Nascence and would insert(0, ...) it ahead of this checkout's core/ -- append it first so it doesn't
sys.path.append(r"C:\Nascence"); sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")

LIVE_DATA = Path(r"C:\Nascence\data")
LIVE_STATE, LIVE_LIGHT = LIVE_DATA / "subconscious_state.json", LIVE_DATA / "subconscious_state.light.json"
CHILD_FLAG = "J1767_child_mid_write.flag"


def sha(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def load_module():
    from core.memory import store as _store
    _store.DB_PATH = Path(tempfile.gettempdir()) / "j1767_never_connected.db"    # belt and braces: never the live DB
    alt = os.environ.get("J1767_MODULE")
    if alt:
        spec = importlib.util.spec_from_file_location("nodes.subconscious_node", alt)
        m = importlib.util.module_from_spec(spec)
        sys.modules["nodes.subconscious_node"] = m
        spec.loader.exec_module(m)
        return m
    from nodes import subconscious_node as m
    return m


def child(lab: Path):
    """Runs in a separate process: start a real _save_state(), write half the JSON, announce, and stall -- the parent
    then kills this process (TerminateProcess) in the middle of the write."""
    scn = load_module()
    scn._STATE_FILE, scn._LIGHT_FILE = lab / "subconscious_state.json", lab / "subconscious_state.light.json"
    node = scn.SubconsciousNode.__new__(scn.SubconsciousNode)
    node._state = json.loads(scn._STATE_FILE.read_text(encoding="utf-8"))
    node._state["scan_count"] += 1000
    real_dumps = json.dumps

    def stall_dump(obj, fp, *a, **k):
        s = real_dumps(obj, ensure_ascii=False)
        fp.write(s[: len(s) // 2]); fp.flush()
        (lab / CHILD_FLAG).write_text("mid-write", encoding="utf-8")
        time.sleep(120)
    json.dump = stall_dump
    if hasattr(scn, "_encode_state_chunks"):     # J-2381 fast path encodes element-wise instead of json.dump
        def stall_chunks(state):
            s = real_dumps(state, ensure_ascii=False)
            yield s[: len(s) // 2]
            (lab / CHILD_FLAG).write_text("mid-write", encoding="utf-8")
            time.sleep(120)
        scn._encode_state_chunks = stall_chunks
    node._save_state()


if len(sys.argv) >= 3 and sys.argv[1] == "--child":
    child(Path(sys.argv[2]))
    sys.exit(0)

FAILS = 0
def check(name, cond, detail=""):
    global FAILS
    FAILS += (not cond)
    print(f"  [{'ok ' if cond else 'FAIL'}] {name}" + (f"   ({detail})" if detail and not cond else ""))


class Cap(logging.Handler):
    def __init__(self): super().__init__(logging.DEBUG); self.records = []
    def emit(self, record): self.records.append(record)
    def loud(self, level=logging.WARNING): return [r for r in self.records if r.levelno >= level]


LIVE_BEFORE = (sha(LIVE_STATE), sha(LIVE_LIGHT))
scn = load_module()
print("module under test:", scn.__file__)
from lab_env import isolate

LG = logging.getLogger("nascence.subconscious")
CAP = Cap(); LG.addHandler(CAP); LG.setLevel(logging.DEBUG); LG.propagate = False
real_dump, real_replace, real_sleep, real_gmtime = json.dump, os.replace, time.sleep, time.gmtime

with isolate(also=[(scn, ["_STATE_FILE", "_LIGHT_FILE"])], db="empty") as lab:
    STATE, LIGHT = scn._STATE_FILE, scn._LIGHT_FILE
    TMP = STATE.with_name(STATE.name + ".tmp")
    if not (STATE.parent == lab and LIGHT.parent == lab and "_lab" in str(lab)):
        sys.exit(f"ABORT: the isolation redirect did not take ({STATE}) -- nothing was written")
    check("isolated: _STATE_FILE / _LIGHT_FILE point into the lab dir", True)

    # the "copied state": a real copy of the live heavy file (read-only access to the live one); synthetic if absent
    if LIVE_STATE.exists():
        shutil.copyfile(LIVE_STATE, STATE)
    else:
        STATE.write_text(json.dumps({"version": 1, "scan_count": 5000, "last_scan": None, "emotional_signature": {},
                                     "tensions": [{"id": f"t{i}", "count": 3, "centroid": [0.1 * (i % 7)] * 64}
                                                  for i in range(300)], "integration_patterns": []}), encoding="utf-8")
    print(f"  state copy: {STATE.stat().st_size:,} bytes")

    def clear_tmp():
        for p in lab.glob("*.tmp"): p.unlink()

    def mutate(node, d=1):
        node._state["scan_count"] += d
        return node._state["scan_count"]

    def disk_scan():
        try: return json.loads(STATE.read_text(encoding="utf-8")).get("scan_count")
        except Exception: return None

    # ---- 0. healthy path: load as-is, save byte-identical to the old in-place writer -----------------------------
    print("-- healthy file")
    node = scn.SubconsciousNode()                      # __init__ -> _load_or_init_state() on the copy
    orig = json.loads(STATE.read_text(encoding="utf-8"))
    check("healthy: loaded as-is (scan_count and tensions match the file)",
          node._state["scan_count"] == orig["scan_count"] and len(node._state["tensions"]) == len(orig["tensions"]))
    check("healthy: no warning logged, no .corrupt file", not CAP.loud() and not list(lab.glob("subconscious_state.corrupt.*")))
    mutate(node)
    node._save_state()
    ref = lab / "J1767_reference_old_writer.json"
    with open(ref, "w", encoding="utf-8") as f:          # the OLD writer, verbatim, on what the node holds after its save
        json.dump(json.loads(json.dumps(node._state)), f, ensure_ascii=False)
    check("healthy save: byte-identical to the old in-place writer's output", STATE.read_bytes() == ref.read_bytes(),
          f"{STATE.stat().st_size} vs {ref.stat().st_size} bytes")
    check("healthy save: no .tmp left behind; light sidecar written and parses",
          not TMP.exists() and json.loads(LIGHT.read_text(encoding="utf-8")).get("scan_count") == node._state["scan_count"])
    HEALTHY = STATE.read_bytes()

    # ---- 1. a failure INSIDE json.dump leaves the previous file intact -------------------------------------------
    print("-- save: failure inside json.dump")
    clear_tmp(); before, lb = STATE.read_bytes(), sha(LIGHT); CAP.records.clear()
    mutate(node)
    def torn_dump(obj, fp, *a, **k):
        fp.write('{"version": 1, "scan_count": 424242, "tensions": ['); fp.flush()
        raise OSError(28, "simulated: No space left on device")
    json.dump = torn_dump
    real_chunks = getattr(scn, "_encode_state_chunks", None)
    if real_chunks is not None:                  # J-2381 fast path: the same failure inside its encoder
        def torn_chunks(state):
            yield '{"version": 1, "scan_count": 424242, "tensions": ['
            raise OSError(28, "simulated: No space left on device")
        scn._encode_state_chunks = torn_chunks
    try: node._save_state()
    finally:
        json.dump = real_dump
        if real_chunks is not None: scn._encode_state_chunks = real_chunks
    check("dump fails mid-write: the previous state file is byte-for-byte intact", STATE.read_bytes() == before,
          f"now {STATE.stat().st_size} bytes, scan_count {disk_scan()}")
    check("...no half-written .tmp left behind", not list(lab.glob("*.tmp")))
    check("...light sidecar not rewritten (the heavy save failed first, as before)", sha(LIGHT) == lb)
    check("...the failure is logged ('state save failed') and nothing is raised", any("state save failed" in r.getMessage() for r in CAP.loud()))
    node._save_state()
    check("...and the next scan's save succeeds", disk_scan() == node._state["scan_count"])

    # ---- 2. os.replace blocked by a reader (Windows WinError 5) --------------------------------------------------
    print("-- save: os.replace blocked by a reader")
    def flaky(n_fail):
        calls = {"n": 0}
        def f(src, dst):
            calls["n"] += 1
            if calls["n"] <= n_fail: raise PermissionError(13, "simulated: destination held open by a reader", str(dst))
            return real_replace(src, dst)
        return f, calls
    clear_tmp(); mutate(node)
    os.replace, calls = flaky(2)
    try: node._save_state()
    finally: os.replace = real_replace
    check("replace blocked twice: retried, the save landed, no .tmp left",
          calls["n"] >= 3 and disk_scan() == node._state["scan_count"] and not list(lab.glob("*.tmp")), f"replace calls={calls['n']}")
    clear_tmp(); before, lb = STATE.read_bytes(), sha(LIGHT); CAP.records.clear(); mutate(node)
    os.replace, calls = flaky(10 ** 6)
    t0 = time.perf_counter()
    try: node._save_state()
    except BaseException as exc: print("   raised:", exc)
    finally: os.replace = real_replace
    dt = time.perf_counter() - t0
    check("replace blocked for good: previous file intact, no .tmp, light sidecar untouched, logged, bounded wait (< 5 s)",
          STATE.read_bytes() == before and not list(lab.glob("*.tmp")) and sha(LIGHT) == lb
          and any("state save failed" in r.getMessage() for r in CAP.loud()) and dt < 5.0, f"{dt:.2f}s")
    node._save_state()
    clear_tmp(); mutate(node)
    reader = open(STATE, "r", encoding="utf-8")            # a REAL handle, held the way json.load(open(path)) holds it
    slept = {"n": 0}
    def sleep_and_release(s):
        slept["n"] += 1
        if not reader.closed: reader.close()
        real_sleep(s)
    time.sleep = sleep_and_release
    try: node._save_state()
    finally: time.sleep = real_sleep; reader.close()
    check("a REAL reader handle blocks os.replace on Windows: the save waited for it and landed",
          disk_scan() == node._state["scan_count"] and (os.name != "nt" or slept["n"] >= 1), f"sleeps={slept['n']}")

    # ---- 3. the F-2314 failure itself: the process DIES in the middle of the write ------------------------------
    print("-- save: process killed mid-write")
    clear_tmp(); STATE.write_bytes(HEALTHY); BASE = json.loads(HEALTHY)["scan_count"]; before = STATE.read_bytes()
    flag = lab / CHILD_FLAG
    if flag.exists(): flag.unlink()
    proc = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--child", str(lab)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, env=os.environ.copy())
    t0 = time.time()
    while not flag.exists() and proc.poll() is None and time.time() - t0 < 120:
        real_sleep(0.1)
    reached = flag.exists()
    proc.kill(); _, err = proc.communicate(timeout=60)
    check("child reached the middle of a real _save_state() write before it was killed", reached,
          (err or b"").decode("utf-8", "replace")[-600:])
    check("killed mid-write: data/subconscious_state.json is byte-identical to before the write began", STATE.read_bytes() == before,
          f"now {STATE.stat().st_size} bytes, parses={disk_scan() is not None}")
    CAP.records.clear()
    boot = scn.SubconsciousNode.__new__(scn.SubconsciousNode)
    state = boot._load_or_init_state()                  # the next boot
    check("next boot after the kill: the pre-kill state loads (scan_count preserved, NOT a fresh re-seed), nothing quarantined",
          state.get("scan_count") == BASE and not CAP.loud() and not list(lab.glob("subconscious_state.corrupt.*")),
          f"scan_count={state.get('scan_count')} (base {BASE})")
    boot._state = state; mutate(boot)
    boot._save_state()
    check("the stale half-written .tmp from the killed process is simply overwritten by the next save",
          not TMP.exists() and disk_scan() == boot._state["scan_count"])

    # ---- 4. load: an unreadable file is moved aside, loudly, never deleted --------------------------------------
    print("-- load: unreadable state file")
    def run_load(raw: bytes):
        STATE.write_bytes(raw); CAP.records.clear(); listed = set(os.listdir(lab))
        n = scn.SubconsciousNode.__new__(scn.SubconsciousNode)
        st = n._load_or_init_state()
        new = sorted(set(os.listdir(lab)) - listed)
        return n, st, new, [x for x in new if x.startswith("subconscious_state.corrupt.") and x.endswith(".json")]
    cut = HEALTHY[: int(len(HEALTHY) * 0.513)]            # cut mid-write at ~51%, like the 23.5 MB of 45.8 MB on 2026-09-28
    n, st, new, asides = run_load(cut)
    check("torn file: a fresh state is returned exactly as before (scan_count 0, no tensions)", st.get("scan_count") == 0 and st.get("tensions") == [])
    check("torn file: moved to subconscious_state.corrupt.<UTC stamp>.json and the original path is gone",
          len(asides) == 1 and not STATE.exists() and len(asides[0]) > len("subconscious_state.corrupt..json"), f"new files: {new}")
    check("...the moved file is byte-identical to the torn file (moved, not rewritten or deleted)",
          bool(asides) and sha(lab / asides[0]) == hashlib.sha256(cut).hexdigest())
    check("...nothing else appeared (no automatic restore from any backup)", new == asides)
    loud = CAP.loud()
    msg = loud[0].getMessage() if loud else ""
    check("...exactly one WARNING, naming the exception, the byte size, the new path and the fresh start",
          len(loud) == 1 and loud[0].levelno == logging.WARNING and "JSONDecodeError" in msg and f"({len(cut)} bytes)" in msg
          and bool(asides) and asides[0] in msg and "FRESH" in msg and "UNREADABLE" in msg, msg[:300])
    n._state = st; mutate(n); n._save_state()
    check("the save after the re-seed writes a healthy file and leaves the moved file untouched",
          disk_scan() == n._state["scan_count"] and bool(asides) and sha(lab / asides[0]) == hashlib.sha256(cut).hexdigest())
    n, st, new, asides = run_load(b"")
    check("zero-byte file: moved aside + loud + fresh state", len(asides) == 1 and st.get("scan_count") == 0 and len(CAP.loud()) == 1)
    def deny(src, dst):
        raise PermissionError(13, "simulated: file locked", str(src))
    os.replace = deny
    try: n, st, new, asides = run_load(cut)
    finally: os.replace = real_replace
    check("move-aside itself blocked: nothing raised, fresh state returned, the file stays put, an ERROR says so",
          st.get("scan_count") == 0 and STATE.read_bytes() == cut and not asides
          and any(r.levelno == logging.ERROR and "could not be moved aside" in r.getMessage() for r in CAP.records))
    time.gmtime = lambda *a: real_gmtime(1_700_000_000)    # the same UTC second twice
    try:
        _, _, _, a1 = run_load(b"{ torn one")
        _, _, _, a2 = run_load(b"{ torn two")
    finally: time.gmtime = real_gmtime
    check("two quarantines in the same second get distinct names and both survive intact",
          len(a1) == 1 and len(a2) == 1 and a1 != a2 and (lab / a1[0]).read_bytes() == b"{ torn one" and (lab / a2[0]).read_bytes() == b"{ torn two")
    STATE.write_bytes(HEALTHY); CAP.records.clear()
    st = scn.SubconsciousNode.__new__(scn.SubconsciousNode)._load_or_init_state()
    check("healthy file again: loads unchanged, silently", st.get("scan_count") == json.loads(HEALTHY)["scan_count"] and not CAP.loud())

LG.removeHandler(CAP)
LIVE_AFTER = (sha(LIVE_STATE), sha(LIVE_LIGHT))
check("canary: live data/subconscious_state.json and its light sidecar are byte-identical before and after (sha256)",
      LIVE_BEFORE == LIVE_AFTER, f"{LIVE_BEFORE} -> {LIVE_AFTER}")
print("lab dir (left for inspection):", lab)
print("FAILS =", FAILS)
sys.exit(1 if FAILS else 0)
