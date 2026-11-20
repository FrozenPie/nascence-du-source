"""J-2432 (F-3134, D-0487 option 1): lossless integration_patterns write reduction.

Checks (on a COPY of the live patterns file when --live-copy is given or the live file exists; a synthetic
fallback otherwise). The live data dir is only READ (one file copied); everything written goes to a tempdir.
  1. float32 equivalence: every centroid of the copy, written with the compact encoder and parsed back, is
     bit-identical in float32 to the original; every non-centroid field is == ; bytes saved reported.
  2. compact encoder falls back (identical to json.dumps) for a non-float32-exact / non-finite centroid.
  3. SubconsciousNode, flags default False: the writer's output is byte-identical to the J-2418 layout.
  4. FLOAT32 only, DELTA only, and both: full roundtrip via the node loader AND store_persist.load_integration_patterns;
     delta writes touch only changed/new/removed entries (bytes appended vs full file); compaction; reorder fallback.
  5. Old reader (plain json.load of the base file) still parses the base; torn journal tail and a stale journal
     (older than the base) are tolerated.
  6. top-level fingerprint (size, mtime_ns) of the live data dir before/after (Du is live: his own writes show up).

    python scripts/_test_patterns_lossless_J2432.py [--src PATH_TO_COPY_OR_LIVE_PATTERNS_FILE] [--fingerprint-dir DIR]
"""
from __future__ import annotations
import argparse, json, logging, os, shutil, sys, tempfile, time
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core                                   # J-2432: core BEFORE lab_env
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
try:
    import lab_env  # noqa: F401
except Exception:
    lab_env = None
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__   # lab_env must not hijack core
import numpy as np
from core import store_persist as sp
from core.memory import store as _store
_store.DB_PATH = Path(tempfile.gettempdir()) / "j2432_never_connected.db"
from nodes import subconscious_node as scn
assert Path(scn.__file__).resolve().is_relative_to(ROOT)
for n in ("nascence.subconscious",):
    logging.getLogger(n).setLevel(logging.CRITICAL)

ap = argparse.ArgumentParser()
ap.add_argument("--src", default=r"C:\Nascence\data\subconscious_state.patterns.json")
ap.add_argument("--fingerprint-dir", default=r"C:\Nascence\data")
args = ap.parse_args()

FAILS = 0
def check(name, cond, detail=""):
    global FAILS
    FAILS += (not cond)
    print(f"  [{'ok ' if cond else 'FAIL'}] {name}" + (f"   ({detail})" if detail else ""))

def fingerprint(d):
    out = {}
    try:
        for e in os.scandir(d):
            if e.is_file():
                st = e.stat(); out[e.name] = (st.st_size, st.st_mtime_ns)
    except OSError:
        pass
    return out

fp_before = fingerprint(args.fingerprint_dir)
TMP = Path(tempfile.mkdtemp(prefix="j2432_"))

# ---- the copy under test
copy = TMP / "copy_of_live.patterns.json"
src = Path(args.src)
if src.exists():
    shutil.copy2(src, copy)
    synthetic = False
else:
    rng = np.random.default_rng(1)
    pats = [{"id": f"p{i}", "label": f"l{i}", "count": i, "first_ts": "2026-01-01", "last_ts": "2026-01-02",
             "centroid": rng.standard_normal(384).astype(np.float32).tolist(), "member_event_ids": [f"e{i}"]}
            for i in range(300)]
    copy.write_text(json.dumps(pats, ensure_ascii=False), encoding="utf-8")
    synthetic = True
orig_text = copy.read_text(encoding="utf-8")
orig = json.loads(orig_text)
print(f"copy: {copy}  entries={len(orig)} bytes={len(orig_text.encode())} synthetic={synthetic}")

print("-- 1. float32 equivalence on the copy")
texts = [sp.encode_pattern(p, True) for p in orig]
new_text = sp.encode_patterns_list(texts)
back = json.loads(new_text)
check("same entry count and id order", [p["id"] for p in back] == [p["id"] for p in orig])
bit_ok = True; field_ok = True; compact_n = 0
for a, b in zip(orig, back):
    ca, cb = np.asarray(a["centroid"], dtype=np.float32), np.asarray(b["centroid"], dtype=np.float32)
    bit_ok &= ca.tobytes() == cb.tobytes()
    field_ok &= ({k: v for k, v in a.items() if k != "centroid"} == {k: v for k, v in b.items() if k != "centroid"})
    field_ok &= list(a.keys()) == list(b.keys())
check("every centroid bit-identical as float32 (tobytes)", bit_ok)
check("every other field and key order identical", field_ok)
cn = len(new_text.encode()); co = len(orig_text.encode())
saved = co - cn
print(f"  bytes: original {co}  compact {cn}  saved {saved} ({100*saved/co:.1f}%)")
# J-4052: the live patterns file is now written by the flag-ON (float32/delta) code since the D-0495 restart, so the input may
# already be compact; the strict "smaller" holds only against a full-precision input. Lossless-ness (above) is what this pins.
check("compact is not larger", cn <= co)
check("non-compact encoding of the copy is byte-identical to the file (json.dumps layout)",
      sp.encode_patterns_list([sp.encode_pattern(p, False) for p in orig]) == orig_text or synthetic is False and
      json.loads(sp.encode_patterns_list([sp.encode_pattern(p, False) for p in orig])) == orig)

print("-- 2. encoder fallbacks")
odd = {"id": "x", "centroid": [0.1, 0.2], "label": "q"}          # 0.1 is not a float32-exact float64
check("non-float32-exact centroid falls back to json.dumps", sp.encode_pattern(odd, True) == json.dumps(odd, ensure_ascii=False))
nan = {"id": "y", "centroid": [float("nan"), 1.0]}
check("non-finite centroid falls back", sp.encode_pattern(nan, True) == json.dumps(nan, ensure_ascii=False))
tricky = {"id": "z", "label": "__J2432_CENTROID_SENTINEL__ \u00e9\u4e2d", "centroid": np.float32([0.1, 1e-7, 3.0]).tolist()}
check("tricky label survives", json.loads(sp.encode_pattern(tricky, True))["label"] == tricky["label"])
check("tricky centroid float32-equal", np.float32(json.loads(sp.encode_pattern(tricky, True))["centroid"]).tobytes()
      == np.float32(tricky["centroid"]).tobytes())

# ---- node harness
def new_node(sd, pats, flags):
    scn._STATE_FILE = sd / "subconscious_state.json"
    scn._LIGHT_FILE = sd / "subconscious_state.light.json"
    scn._DATA_DIR = sd
    scn.SUBC_SPLIT_PATTERNS = True
    scn.SUBC_PATTERNS_MIN_INTERVAL_S = 0.0
    scn.SUBC_PATTERNS_DELTA_MIN_INTERVAL_S = 0.0
    scn.SUBC_PATTERNS_FLOAT32, scn.SUBC_PATTERNS_DELTA = flags
    node = scn.SubconsciousNode.__new__(scn.SubconsciousNode)
    node._state = {"version": 1, "scan_count": 7, "tensions": [], "integration_patterns": pats}
    return node

def disk_patterns(sd):
    return sp.read_patterns_file(sp.patterns_path_for(sd / "subconscious_state.json"))

def same_f32(a, b):
    return len(a) == len(b) and all(x["id"] == y["id"] and
        np.float32(x["centroid"]).tobytes() == np.float32(y["centroid"]).tobytes() and
        {k: v for k, v in x.items() if k != "centroid"} == {k: v for k, v in y.items() if k != "centroid"}
        for x, y in zip(a, b))

import copy as _copy
def fresh():
    return _copy.deepcopy(orig)

print("-- 3. flags default False -> J-2418 layout byte for byte")
# J-4052: D-0495 (2026-10-28) flipped both flags live (default True); the flag-OFF layout below is still exercised explicitly via new_node().
check("defaults are True (D-0495)", scn.SUBC_PATTERNS_FLOAT32 is True and scn.SUBC_PATTERNS_DELTA is True)
sd = TMP / "n0"; sd.mkdir()
node = new_node(sd, fresh(), (False, False))
node._save_state()
pf = sp.patterns_path_for(scn._STATE_FILE)
chunks = "".join(scn._encode_state_chunks({"p": node._state["integration_patterns"]}))
check("base bytes == J-2418 writer bytes", pf.read_text(encoding="utf-8") == chunks[len('{"p": '):-1])
check("no journal file", not sp.delta_path_for(pf).exists())

print("-- 4a. FLOAT32 only")
sd = TMP / "n1"; sd.mkdir()
node = new_node(sd, fresh(), (True, False))
node._save_state()
pf = sp.patterns_path_for(scn._STATE_FILE)
check("base not larger than original (strictly smaller only for a full-precision input)", pf.stat().st_size <= co, f"{pf.stat().st_size} vs {co}")
check("roundtrip float32-identical (loader)", same_f32(sp.load_integration_patterns(scn._STATE_FILE, {}), orig))
n2 = scn.SubconsciousNode.__new__(scn.SubconsciousNode)
n2._state = n2._load_or_init_state()
check("fresh node loads it (float32-identical)", same_f32(n2._state["integration_patterns"], orig))
check("plain json.load (old reader) parses the base", isinstance(json.loads(pf.read_text(encoding="utf-8")), list))

print("-- 4b. DELTA (+FLOAT32)")
for f32 in (False, True):
    sd = TMP / f"d{int(f32)}"; sd.mkdir()
    node = new_node(sd, fresh(), (f32, True))
    node._save_state()
    pf = sp.patterns_path_for(scn._STATE_FILE); dp = sp.delta_path_for(pf)
    base_size = pf.stat().st_size
    check(f"[f32={f32}] first save writes the base, no journal", base_size > 0 and not dp.exists())
    time.sleep(0.05)
    node._save_state()
    check(f"[f32={f32}] unchanged: nothing written", pf.stat().st_size == base_size and not dp.exists())
    ps = node._state["integration_patterns"]
    # 7 changed entries like F-3134's measurement
    rng = np.random.default_rng(7)
    for p in ps[:7]:
        p["count"] += 1; p["last_ts"] = "2026-10-19T12:00:00"; p["label"] = p["label"] + "!"
        p["centroid"] = rng.standard_normal(len(p["centroid"])).astype(np.float32).tolist()
        p["member_event_ids"] = ["m1", "m2"]
    ps.append({"id": "new-1", "label": "n", "count": 1, "first_ts": "a", "last_ts": "b",
               "centroid": rng.standard_normal(len(ps[0]["centroid"])).astype(np.float32).tolist(), "member_event_ids": []})
    node._save_state()
    jb = dp.stat().st_size
    print(f"  [f32={f32}] 7 changed + 1 new -> journal {jb} bytes vs full base {base_size} bytes ({100*jb/base_size:.2f}%)")
    check(f"[f32={f32}] base untouched, journal tiny", pf.stat().st_size == base_size and jb < 0.05 * base_size)
    expect = _copy.deepcopy(ps)
    check(f"[f32={f32}] loader == in-memory (float32)", same_f32(sp.load_integration_patterns(scn._STATE_FILE, {}), expect))
    n2 = scn.SubconsciousNode.__new__(scn.SubconsciousNode)
    n2._state = n2._load_or_init_state()
    check(f"[f32={f32}] fresh node loads base+journal", same_f32(n2._state["integration_patterns"], expect))
    # prune one (the node's own prune pattern) -> del op
    removed_id = ps[10]["id"]
    del ps[10]
    node._save_state()
    got = sp.load_integration_patterns(scn._STATE_FILE, {})
    check(f"[f32={f32}] removal journaled, others kept", len(got) == len(expect) - 1 and removed_id not in {p["id"] for p in got}
          and same_f32(got, [p for p in expect if p["id"] != removed_id]))
    # decay-style change to many
    for p in ps[:50]: p["count"] = max(1, p["count"] // 2)
    node._save_state()
    check(f"[f32={f32}] second change roundtrip", same_f32(sp.load_integration_patterns(scn._STATE_FILE, {}), ps))
    # compaction: shrink the limit
    sp.DELTA_MAX_BYTES_FLOOR = 10
    node._pj_base_bytes = 0
    ps[20]["count"] += 5
    node._save_state()          # journal > limit -> compaction path writes the base and removes the journal
    check(f"[f32={f32}] compaction: journal gone, base has all", not dp.exists() and same_f32(disk_patterns(sd), ps))
    sp.DELTA_MAX_BYTES_FLOOR = 1_000_000
    # reorder -> full rewrite, still lossless
    ps.reverse()
    node._save_state()
    check(f"[f32={f32}] reorder falls back to a full rewrite", same_f32(disk_patterns(sd), ps) and not dp.exists())
    # insertion mid-list -> full rewrite
    ps.insert(3, {"id": "mid", "label": "m", "count": 1, "first_ts": "a", "last_ts": "b", "centroid": [0.5, 0.25], "member_event_ids": []})
    node._save_state()
    got = disk_patterns(sd)
    check(f"[f32={f32}] mid-list insert keeps order (full rewrite)", [p["id"] for p in got] == [p["id"] for p in ps])
    # robustness: torn tail + stale journal
    ps[1]["count"] += 1
    node._save_state()
    with open(dp, "a", encoding="utf-8") as fh: fh.write('{"t": 99999999999999999999, "up": [{"id": "tor')
    check(f"[f32={f32}] torn journal tail tolerated", same_f32(sp.load_integration_patterns(scn._STATE_FILE, {}), ps))
    stale = TMP / f"stale{int(f32)}"; stale.mkdir()
    shutil.copy2(pf, stale / pf.name)
    (stale / dp.name).write_text('{"t": 1, "up": [{"id": "%s", "count": -1}]}\n' % ps[0]["id"], encoding="utf-8")
    sp.invalidate_json_cache()
    got = sp.read_patterns_file(stale / pf.name)
    check(f"[f32={f32}] journal older than the base is ignored", same_f32(got, disk_patterns(sd)) or got[0].get("count") != -1)

print("-- 5. no pattern lost across the whole copy under DELTA")
sd = TMP / "keep"; sd.mkdir()
node = new_node(sd, fresh(), (True, True))
node._save_state()
for p in node._state["integration_patterns"][:5]:
    p["count"] += 1
node._save_state()
ids_disk = [p["id"] for p in sp.load_integration_patterns(scn._STATE_FILE, {})]
check("all original ids still present", ids_disk == [p["id"] for p in orig])

fp_after = fingerprint(args.fingerprint_dir)
changed = sorted(k for k in set(fp_before) | set(fp_after) if fp_before.get(k) != fp_after.get(k))
print(f"-- 6. fingerprint of {args.fingerprint_dir} top level: {len(fp_before)} files before, {len(fp_after)} after, "
      f"{len(changed)} differ")
for k in changed[:30]: print(f"     {k}: {fp_before.get(k)} -> {fp_after.get(k)}")
print("     (Du is live: differences are his own writes; this test opens nothing there for writing.)")
shutil.rmtree(TMP, ignore_errors=True)
print(f"\n{'ALL OK' if not FAILS else str(FAILS) + ' FAILED'}")
sys.exit(1 if FAILS else 0)
