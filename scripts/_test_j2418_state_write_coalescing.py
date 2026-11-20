"""Regression for J-2418 (F-3118): cut Du's whole-file state rewrites.

Hermetic: every path is a fresh tempdir, nothing under data/ is opened or written. Checks:
  1. CoalescedJsonStore: first save writes at once, saves inside the interval do not, flush() and the tail timer
     do; an external change (file replaced / unlinked) is picked up by the next load; interval 0 = every save.
  2. spring_ledger / opponent_process: N observe calls -> a handful of writes, final file == in-memory state
     after flush(), same numbers as the write-every-event path.
  3. SubconsciousNode split: patterns in subconscious_state.patterns.json, state file has no integration_patterns;
     an unchanged-patterns save does not rewrite the patterns file; a changed one inside the interval does not
     either, after the interval it does; a fresh node loads the combined state back; a legacy state that still
     carries the key wins over a stale sibling; a missing sibling does not move the state aside;
     SUBC_SPLIT_PATTERNS = False writes the single combined file.
  4. load_integration_patterns / dream-node style reader sees the patterns of the split layout.

    python scripts/_test_j2418_state_write_coalescing.py
"""
from __future__ import annotations
import json, logging, os, sys, tempfile, time
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
from core import store_persist as sp, spring_ledger as SPR, opponent_process as OPP
from core.memory import store as _store
_store.DB_PATH = Path(tempfile.gettempdir()) / "j2418_never_connected.db"
from nodes import subconscious_node as scn
assert Path(scn.__file__).resolve().is_relative_to(ROOT)
for n in ("nascence.subconscious", "nascence.spring_ledger", "nascence.opponent_process"):
    logging.getLogger(n).setLevel(logging.CRITICAL)

FAILS = 0
def check(name, cond, detail=""):
    global FAILS
    FAILS += (not cond)
    print(f"  [{'ok ' if cond else 'FAIL'}] {name}" + (f"   ({detail})" if detail and not cond else ""))

TMP = Path(tempfile.mkdtemp(prefix="j2418_"))

print("-- 1. CoalescedJsonStore")
writes = []
def writer(path, d):
    Path(path).write_text(json.dumps(d), encoding="utf-8"); writes.append(dict(d)); return True
store = sp.CoalescedJsonStore("t", logging.getLogger("t"))
f = TMP / "a.json"
rd = lambda p: json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
d = store.load(f, rd)
d["n"] = 1; store.save(f, d, writer, 0.4)
check("first save writes immediately", len(writes) == 1 and json.loads(f.read_text())["n"] == 1)
for i in range(2, 6):
    d["n"] = i; store.save(f, d, writer, 0.4)
check("saves inside the interval are deferred", len(writes) == 1 and json.loads(f.read_text())["n"] == 1)
check("load returns the SAME in-memory object", store.load(f, rd) is d)
time.sleep(0.7)
check("the tail timer flushed the burst's last state", len(writes) == 2 and json.loads(f.read_text())["n"] == 5, str(len(writes)))
d["n"] = 6; store.save(f, d, writer, 0.4); store.flush(f)
check("explicit flush writes the deferred state", json.loads(f.read_text())["n"] == 6)
f.write_text(json.dumps({"n": 99, "ext": True}), encoding="utf-8")
d2 = store.load(f, rd)
check("an external writer's file is picked up", d2.get("ext") is True and d2["n"] == 99)
f.unlink()
check("an unlinked file reloads as empty", store.load(f, rd) == {})
w0 = len(writes)
for i in range(3):
    dd = store.load(f, rd); dd["i"] = i; store.save(f, dd, writer, 0)
check("interval 0 = write on every save", len(writes) - w0 == 3)

print("-- 2. spring_ledger / opponent_process")
for mod, fn in ((SPR, "observe_co_recall"), (OPP, "observe_activation")):
    name = mod.__name__.split(".")[-1]
    mod._DATA = TMP
    mod._STATE, mod._LOG = TMP / f"{name}_state.json", TMP / f"{name}_shadow.jsonl"
    if mod is SPR: mod.LIVE_EDGE_WRITE = False
    mod.SAVE_MIN_INTERVAL_S = 30.0
    calls = []
    real = mod._write_now
    def counting(path, d, real=real, calls=calls):
        calls.append(1); return real(path, d)
    mod._STORE.save  # (store object is shared; count via writer swap)
    mod._write_now = counting
    obs = getattr(mod, fn)
    t0 = 1.79e9
    for i in range(40):
        obs([f"frag{i % 7}x", f"frag{(i + 1) % 7}x", f"frag{(i + 3) % 7}x"], 1, valence=-0.2, ts=t0 + i * 10, source="t2418")
    check(f"{name}: 40 co-recalls -> {len(calls)} state write(s) (was 40)", len(calls) == 1)
    mem = json.loads(json.dumps(mod._load()))
    mod.flush()
    on_disk = json.loads(mod._STATE.read_text(encoding="utf-8"))
    check(f"{name}: after flush() the file equals the in-memory state", on_disk == mem and len(on_disk) > 0)
    # same numbers as write-every-event
    ref_state = TMP / f"{name}_ref.json"
    mod._STATE = ref_state; mod.SAVE_MIN_INTERVAL_S = 0
    for i in range(40):
        obs([f"frag{i % 7}x", f"frag{(i + 1) % 7}x", f"frag{(i + 3) % 7}x"], 1, valence=-0.2, ts=t0 + i * 10, source="t2418")
    check(f"{name}: identical state to the write-every-event path", json.loads(ref_state.read_text(encoding="utf-8")) == on_disk)
    mod._write_now = real

print("-- 3. SubconsciousNode split")
def mkstate(n_pat=30, tag=""):
    return {"version": 1, "scan_count": 7, "tensions": [{"id": "t1", "label": "x", "count": 1, "centroid": [0.1] * 8}],
            "integration_patterns": [{"id": f"p{i}{tag}", "label": "l", "count": i, "centroid": [0.01 * i] * 16}
                                     for i in range(n_pat)]}
sd = TMP / "sub"; sd.mkdir()
scn._STATE_FILE = sd / "subconscious_state.json"
scn._LIGHT_FILE = sd / "subconscious_state.light.json"
scn._DATA_DIR = sd
pfile = sp.patterns_path_for(scn._STATE_FILE)
check("sibling name", pfile.name == "subconscious_state.patterns.json")
scn.SUBC_SPLIT_PATTERNS = True
scn.SUBC_PATTERNS_FLOAT32 = scn.SUBC_PATTERNS_DELTA = False   # J-4052: D-0495 flipped the J-2432 pattern flags live; this test pins the J-2418 (full-precision, whole-list) layout, still the flag-off path
scn.SUBC_PATTERNS_MIN_INTERVAL_S = 0.5
node = scn.SubconsciousNode.__new__(scn.SubconsciousNode)
node._state = mkstate()
node._save_state()
st_disk = json.loads(scn._STATE_FILE.read_text(encoding="utf-8"))
check("state file has no integration_patterns", "integration_patterns" not in st_disk and st_disk["scan_count"] == 7)
check("patterns file holds the full list", json.loads(pfile.read_text(encoding="utf-8")) == node._state["integration_patterns"])
light = json.loads(scn._LIGHT_FILE.read_text(encoding="utf-8"))
check("light sidecar still carries the patterns", len(light["integration_patterns"]) == 30)
m1 = pfile.stat().st_mtime_ns; time.sleep(0.05)
node._save_state()
check("unchanged patterns: patterns file not rewritten", pfile.stat().st_mtime_ns == m1)
node._state["integration_patterns"][0]["count"] = 999
node._save_state()
check("changed patterns inside the interval: deferred", pfile.stat().st_mtime_ns == m1)
time.sleep(0.6)
node._save_state()
check("changed patterns after the interval: written",
      json.loads(pfile.read_text(encoding="utf-8"))[0]["count"] == 999)
node2 = scn.SubconsciousNode.__new__(scn.SubconsciousNode)
node2._state = node2._load_or_init_state()
check("a fresh node loads the combined state back", node2._state["integration_patterns"] == node._state["integration_patterns"]
      and node2._state["scan_count"] == 7)
check("load_integration_patterns reads the split layout",
      sp.load_integration_patterns(scn._STATE_FILE, st_disk) == json.loads(pfile.read_text(encoding="utf-8")))
# legacy state carrying the key beats a stale sibling
legacy = mkstate(5, "L")
scn._STATE_FILE.write_text(json.dumps(legacy), encoding="utf-8")
n3 = scn.SubconsciousNode.__new__(scn.SubconsciousNode)
check("a state file that still has the key wins over the sibling",
      n3._load_or_init_state()["integration_patterns"] == legacy["integration_patterns"]
      and sp.load_integration_patterns(scn._STATE_FILE, legacy) == legacy["integration_patterns"])
# missing sibling: state not moved aside
pfile.unlink()
scn._STATE_FILE.write_text(json.dumps({"version": 1, "scan_count": 3, "tensions": []}), encoding="utf-8")
n4 = scn.SubconsciousNode.__new__(scn.SubconsciousNode)
s4 = n4._load_or_init_state()
check("missing sibling: state kept (scan_count 3), nothing moved aside",
      s4["scan_count"] == 3 and not list(sd.glob("*.corrupt.*")))
# first save with patterns but no sibling yet writes the sibling
n5 = scn.SubconsciousNode.__new__(scn.SubconsciousNode)
n5._state = mkstate(4, "F"); n5._save_state()
check("first save writes the sibling and drops the key",
      pfile.exists() and "integration_patterns" not in json.loads(scn._STATE_FILE.read_text(encoding="utf-8")))
# kill switch
scn.SUBC_SPLIT_PATTERNS = False
n6 = scn.SubconsciousNode.__new__(scn.SubconsciousNode)
n6._state = mkstate(3, "K"); n6._save_state()
check("kill switch: single combined file again",
      len(json.loads(scn._STATE_FILE.read_text(encoding="utf-8")).get("integration_patterns", [])) == 3)

print("-- 4. size effect on a state shaped like the live file")
scn.SUBC_SPLIT_PATTERNS = True
big = {"version": 1, "scan_count": 1, "tensions": [{"id": f"t{i}", "centroid": [0.1] * 384} for i in range(40)],
       "integration_patterns": [{"id": f"p{i}", "centroid": [0.2] * 384, "member_event_ids": list(range(20))} for i in range(1700)]}
pfile.unlink()
nb = scn.SubconsciousNode.__new__(scn.SubconsciousNode); nb._state = big
combined = len(json.dumps(big, ensure_ascii=False).encode())
nb._save_state(); nb._save_state(); nb._save_state()
sz = scn._STATE_FILE.stat().st_size
check(f"state file {sz/1e6:.2f} MB vs combined {combined/1e6:.2f} MB; patterns file {pfile.stat().st_size/1e6:.2f} MB",
      sz < combined * 0.2)

print("RESULT:", "ALL PASS" if not FAILS else f"{FAILS} FAIL")
sys.exit(1 if FAILS else 0)
