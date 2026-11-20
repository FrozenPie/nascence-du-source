"""Regression for J-2381 (F-3078, plan sleep_as_a_mode): SubconsciousNode._save_state fast path.

Hermetic: every path is a fresh tempfile directory, the memory DB is never connected, nothing under data/ is
opened. Checks:
  1. _encode_state_chunks == json.dumps(json.loads(json.dumps(x)), ensure_ascii=False) on awkward synthetic state
     (unicode, NaN/inf, tuples, nested non-str keys, numpy float64, empty lists, non-str top-level key fallback);
  2. fast save == legacy save, byte for byte, heavy file AND light sidecar (light_ts pinned);
  3. the merge re-read (json.load) is skipped while the file is our own last write, and runs after an external
     in-place write (core/tension_ledger.py style) and merges its resolved fields exactly as legacy does;
  4. an external write DURING the save abandons it (file left as the other writer wrote it, no .tmp), and the
     next save re-reads, merges and lands;
  5. the kill switch SUBC_SAVE_OFFLOOP = False runs the legacy code (json.load every save) with the same bytes;
  6. _t1_scan awaits the save on a worker thread when the switch is on, on the loop thread when it is off.

    python scripts/_test_j2381_subc_save_fast.py
"""
from __future__ import annotations
import asyncio, hashlib, json, logging, math, os, sys, tempfile, threading, time
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
from core.memory import store as _store
_store.DB_PATH = Path(tempfile.gettempdir()) / "j2381_never_connected.db"
import numpy as np
from nodes import subconscious_node as scn
assert Path(scn.__file__).resolve().is_relative_to(ROOT)
logging.getLogger("nascence.subconscious").setLevel(logging.CRITICAL)

FAILS = 0
def check(name, cond, detail=""):
    global FAILS
    FAILS += (not cond)
    print(f"  [{'ok ' if cond else 'FAIL'}] {name}" + (f"   ({detail})" if detail and not cond else ""))

class _T:                     # pin time.time() so the light sidecar's light_ts is comparable
    def __getattr__(self, n): return getattr(time, n)
    @staticmethod
    def time(): return 1792300000.0
scn.time = _T()
scn.SUBC_SPLIT_PATTERNS = False   # J-2418: this test pins the J-2381 single-file byte identity; the split has its own test

def synthetic_state():
    return {
        "version": 1, "scan_count": 140361, "last_scan": 1792299999.123456789, "last_synthesis": None,
        "emotional_signature": {"valence": 0.1, "arousal": float("nan"), "dominance": float("inf")},
        "baseline_drift": {"valence": -0.0, "arousal": 1e-17},
        "tensions": [{"id": f"t{i}", "label": "渡 — être «quoted» \"x\"\n\t ", "count": i,
                      "centroid": [math.sin(i + j) for j in range(48)], "member_event_ids": [i, i + 1],
                      "resolved": bool(i % 3 == 0), "resolved_ts": (1.5 * i if i % 3 == 0 else None),
                      "np": np.float64(0.1) * i, "tup": (1, 2.5, "a"), "nested": {1: "int key", 2.5: "f", True: "b", None: "n"},
                      "_private": [0.0] * 20, "resolution_attempts": []} for i in range(40)],
        "integration_patterns": [{"id": f"p{i}", "centroid": [0.001 * k for k in range(64)], "label": "ü" * (i % 5)}
                                 for i in range(60)],
        "empty_list": [], "empty_tuple": (), "tuple_top": (1, (2, 3), [4]), "s": "plain",
    }

def legacy_bytes(state) -> bytes:
    return json.dumps(json.loads(json.dumps(state)), ensure_ascii=False).encode("utf-8")

print("-- 1. encoder byte identity")
st = synthetic_state()
check("chunked encoding == old deep-copy round trip encoding",
      "".join(scn._encode_state_chunks(st)).encode("utf-8") == legacy_bytes(st))
odd = {"a": 1, 7: "int key at top level"}
check("non-str top-level key: falls back to one whole dumps, still identical",
      "".join(scn._encode_state_chunks(odd)).encode("utf-8") == legacy_bytes(odd))
check("non-dict state: identical", "".join(scn._encode_state_chunks([1, {"a": (2,)}])) == json.dumps([1, {"a": [2]}], ensure_ascii=False))
pieces = list(scn._encode_state_chunks(st))
check("big lists are split per element (longest piece < 4 KB here)", max(len(p) for p in pieces) < 4096, str(max(len(p) for p in pieces)))

def make_node(d: Path, state: dict, flag: bool):
    scn._STATE_FILE, scn._LIGHT_FILE = d / "subconscious_state.json", d / "subconscious_state.light.json"
    scn._STATE_FILE.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    scn.SUBC_SAVE_OFFLOOP = flag
    return scn.SubconsciousNode()

real_load = json.load
loads_seen = {"n": 0}
def counting_load(*a, **k):
    loads_seen["n"] += 1
    return real_load(*a, **k)
json.load = counting_load

with tempfile.TemporaryDirectory(prefix="j2381_") as tmpd:
    T = Path(tmpd)
    (T / "fast").mkdir(); (T / "legacy").mkdir()

    print("-- 2. fast save == legacy save (heavy + light)")
    base = json.loads(json.dumps(synthetic_state()))       # what a booted node holds: plain JSON types
    nl = make_node(T / "legacy", base, False); nl._state["scan_count"] += 1; nl._state["tensions"][1]["resolved"] = True
    nl._save_state(); L_heavy, L_light = scn._STATE_FILE.read_bytes(), scn._LIGHT_FILE.read_bytes()
    nf = make_node(T / "fast", base, True); nf._state["scan_count"] += 1; nf._state["tensions"][1]["resolved"] = True
    loads_seen["n"] = 0
    nf._save_state(); F_heavy, F_light = scn._STATE_FILE.read_bytes(), scn._LIGHT_FILE.read_bytes()
    check("heavy file byte-identical", F_heavy == L_heavy, f"{len(F_heavy)} vs {len(L_heavy)}")
    check("light sidecar byte-identical", F_light == L_light)
    check("first fast save after load skipped the merge re-read (file is what we loaded)", loads_seen["n"] == 0, str(loads_seen))
    check("no .tmp left", not (T / "fast" / "subconscious_state.json.tmp").exists())
    same = []
    for rnd, idx in enumerate((5, 7, None, 8)):          # the node resolves a tension, then saves again (and again)
        for node, d, flag in ((nl, T / "legacy", False), (nf, T / "fast", True)):
            scn._STATE_FILE, scn._LIGHT_FILE = d / "subconscious_state.json", d / "subconscious_state.light.json"
            scn.SUBC_SAVE_OFFLOOP = flag
            node._state["scan_count"] += 1
            if idx is not None:
                node._state["tensions"][idx]["resolved"] = True
                node._state["tensions"][idx]["resolved_ts"] = 100.0 + rnd
            node._save_state()
        same.append((T / "legacy" / "subconscious_state.json").read_bytes() == (T / "fast" / "subconscious_state.json").read_bytes()
                    and (T / "legacy" / "subconscious_state.light.json").read_bytes() == (T / "fast" / "subconscious_state.light.json").read_bytes())
    check("4 more save rounds with node-side resolutions: heavy + light identical after every round", all(same), str(same))
    scn._STATE_FILE, scn._LIGHT_FILE = T / "fast" / "subconscious_state.json", T / "fast" / "subconscious_state.light.json"
    scn.SUBC_SAVE_OFFLOOP = True

    print("-- 3. merge gate")
    loads_seen["n"] = 0; nf._state["scan_count"] += 1; nf._save_state()
    check("steady state: second save does not re-read the file", loads_seen["n"] == 0)
    disk = json.loads(scn._STATE_FILE.read_text(encoding="utf-8"))
    tid = disk["tensions"][2]["id"]
    disk["tensions"][2].update(resolved=True, resolved_ts=1234.5, resolving_thought_id="cyc-9",
                               resolution_thought="settled", resolution_sim=0.91)
    time.sleep(0.01)
    with open(scn._STATE_FILE, "w", encoding="utf-8") as f:          # tension_ledger writes in place
        json.dump(disk, f, ensure_ascii=False)
    loads_seen["n"] = 0; nf._state["scan_count"] += 1; nf._save_state()
    after = json.loads(scn._STATE_FILE.read_text(encoding="utf-8"))
    t2 = [t for t in after["tensions"] if t["id"] == tid][0]
    check("external write detected: merge re-read ran once", loads_seen["n"] == 1, str(loads_seen))
    check("external resolution merged into memory and file",
          t2["resolved"] is True and t2["resolved_ts"] == 1234.5 and t2["resolving_thought_id"] == "cyc-9"
          and t2["resolution_thought"] == "settled" and t2["resolution_sim"] == 0.91 and after["scan_count"] == nf._state["scan_count"])
    # same scenario through legacy -> same bytes
    nl._state = json.loads(json.dumps(nf._state)); scn._STATE_FILE = T / "legacy" / "subconscious_state.json"
    scn._LIGHT_FILE = T / "legacy" / "subconscious_state.light.json"
    scn.SUBC_SAVE_OFFLOOP = False; nl._save_state()
    check("legacy writes the same bytes for the merged state",
          (T / "legacy" / "subconscious_state.json").read_bytes() == (T / "fast" / "subconscious_state.json").read_bytes())

    print("-- 4. external write DURING the save")
    scn._STATE_FILE, scn._LIGHT_FILE = T / "fast" / "subconscious_state.json", T / "fast" / "subconscious_state.light.json"
    scn.SUBC_SAVE_OFFLOOP = True
    real_chunks = scn._encode_state_chunks
    other = json.loads(scn._STATE_FILE.read_text(encoding="utf-8"))
    tid3 = other["tensions"][4]["id"]
    other["tensions"][4].update(resolved=True, resolved_ts=777.0, resolving_thought_id="cyc-mid",
                                resolution_thought="mid-save", resolution_sim=0.5)
    def racing_chunks(state):
        for i, p in enumerate(real_chunks(state)):
            if i == 3:
                time.sleep(0.01)
                with open(scn._STATE_FILE, "w", encoding="utf-8") as f:
                    json.dump(other, f, ensure_ascii=False)
            yield p
    scn._encode_state_chunks = racing_chunks
    nf._state["scan_count"] += 1
    try: nf._save_state()
    finally: scn._encode_state_chunks = real_chunks
    on_disk = json.loads(scn._STATE_FILE.read_text(encoding="utf-8"))
    check("save abandoned: the other writer's file is intact, no .tmp",
          on_disk == other and not (T / "fast" / "subconscious_state.json.tmp").exists())
    loads_seen["n"] = 0; nf._save_state()
    on_disk = json.loads(scn._STATE_FILE.read_text(encoding="utf-8"))
    t4 = [t for t in on_disk["tensions"] if t["id"] == tid3][0]
    check("next save re-read, merged the mid-save resolution and landed our state",
          loads_seen["n"] == 1 and t4["resolution_thought"] == "mid-save" and on_disk["scan_count"] == nf._state["scan_count"])

    print("-- 5. kill switch")
    scn.SUBC_SAVE_OFFLOOP = False
    loads_seen["n"] = 0; nf._save_state(); nf._save_state()
    check("switch off: legacy path re-reads the file on every save", loads_seen["n"] == 2, str(loads_seen))
    check("switch off: same bytes as the fast path writes",
          scn._STATE_FILE.read_bytes() == "".join(real_chunks(nf._state)).encode("utf-8"))

    print("-- 6. _t1_scan call site")
    async def _none(*a, **k): return None
    scn.get_shadow_events = lambda **k: []
    scn.get_light_events = lambda **k: []
    for m in ("_apply_decay", "_apply_pattern_decay", "_update_emotional_signature"):
        setattr(nf, m, lambda *a, **k: None)
    nf._find_ai_trigger = lambda *a, **k: None
    nf._find_t2_trigger = lambda *a, **k: None
    seen = []
    real_save = scn.SubconsciousNode._save_state
    nf._save_state = lambda: (seen.append(threading.get_ident()), real_save(nf))
    async def run():
        loop_tid = threading.get_ident()
        scn.SUBC_SAVE_OFFLOOP = True; await nf._t1_scan(None)
        scn.SUBC_SAVE_OFFLOOP = False; await nf._t1_scan(None)
        return loop_tid
    loop_tid = asyncio.run(run())
    check("switch on: save ran on a worker thread; switch off: on the loop thread",
          len(seen) == 2 and seen[0] != loop_tid and seen[1] == loop_tid, f"{seen} loop={loop_tid}")
    scn.SUBC_SAVE_OFFLOOP = True

json.load = real_load
print("RESULT:", "ALL PASS" if FAILS == 0 else f"{FAILS} FAIL")
sys.exit(1 if FAILS else 0)
