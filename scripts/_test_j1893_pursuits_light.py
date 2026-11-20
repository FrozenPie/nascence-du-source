"""J-1893 (F-2522 spawn): core/pursuits.py light companion for status()/sample_series().

ISOLATED: pu._ACTIVE / _SHADOW / _SERIES / _DIR and light_sidecar.SHADOW_LOG are redirected into a fresh temp dir
BEFORE any call; the only live file touched is a READ-ONLY copy source for the optional live-size check
(--live-size), which copies data/pursuits_active.json into the temp dir first and never opens it again.
Run from a worktree:  python scripts/_test_j1893_pursuits_light.py [--live-size]
"""
from __future__ import annotations

import json
import random
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core                                                    # noqa: E402  (BEFORE anything else under test)
assert Path(core.__file__).resolve().is_relative_to(ROOT), f"core resolves outside the tree under test: {core.__file__}"
import core.pursuits as pu                                      # noqa: E402
from core import light_sidecar as ls                            # noqa: E402

LIVE = "--live-size" in sys.argv
LIVE_ACTIVE = Path(r"C:\Nascence\data\pursuits_active.json")    # only ever COPIED from below
TMP = Path(tempfile.mkdtemp(prefix="j1893_pursuits_"))
pu._ACTIVE, pu._SHADOW, pu._SERIES, pu._DIR = (TMP / "pursuits_active.json", TMP / "pursuits_shadow.jsonl",
                                                TMP / "pursuits_series.jsonl", TMP)
ls.SHADOW_LOG = TMP / "light_sidecar_shadow.jsonl"
assert pu._ACTIVE != LIVE_ACTIVE and pu._light_path().parent == TMP

fails = 0


def check(ok, label):
    global fails
    print(("PASS  " if ok else "FAIL  ") + label)
    if not ok:
        fails += 1


def mk(n, seed=1):
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        out.append({"id": f"p{i}", "question": f"question number {i} " + "x" * rnd.randint(0, 80),
                    "status": rnd.choice(["active", "dormant", "dormant", "saturated"]),
                    "heat": round(rnd.choice([0.0, 0.5, 0.5, 0.18, 0.9, rnd.random()]), 3),   # deliberate heat TIES
                    "advances": rnd.randint(0, 30), "restates": rnd.randint(0, 9),
                    "coheres": rnd.randint(0, 20), "scatters": rnd.randint(0, 20),
                    "last_touched": 1.0, "centroid": [rnd.random() for _ in range(384)]})
    return out


def dumps(d):
    return json.dumps(d, ensure_ascii=False)             # NOT sort_keys: key order must match too


# 1. _save writes the light companion; light == heavy status byte-for-byte (incl. heat ties, stable order)
items = mk(200)
pu._save(items)
check(pu._light_path().exists(), "_save writes pursuits_active.light.json beside the heavy file")
check(pu._light_status() is not None, "light companion is fresh against the heavy file stamp")
pu.PURSUITS_LIGHT_READ = False
heavy = pu.status()
check(dumps(heavy) == dumps(pu._status_from_items(items)), "status() (heavy path) == pure status over the same items")
pu.PURSUITS_LIGHT_READ = True
real_load = pu._load
def _boom():
    raise AssertionError("heavy _load called with light read ON and a fresh sidecar")
pu._load = _boom
try:
    light = pu.status()
    check(dumps(light) == dumps(heavy), "status() from the light sidecar is BYTE-IDENTICAL to the heavy one")
except AssertionError as e:
    check(False, str(e))
finally:
    pu._load = real_load

# 2. stale: heavy changed behind _save's back -> light refused, heavy answers, sidecar rebuilt
items2 = mk(200, seed=2)
pu._ACTIVE.write_text(json.dumps(items2, ensure_ascii=False, indent=1), encoding="utf-8")   # not via _save
check(pu._light_status() is None, "a heavy file changed outside _save makes the light companion STALE (refused)")
s = pu.status()
check(dumps(s) == dumps(pu._status_from_items(items2)), "stale light -> status() answers from the heavy file")
check(pu._light_status() is not None and dumps(pu._light_status()) == dumps(s), "...and the sidecar was rebuilt fresh")

# 3. missing light -> fallback + rebuild
pu._light_path().unlink()
s = pu.status()
check(dumps(s) == dumps(pu._status_from_items(items2)) and pu._light_path().exists(), "missing light -> heavy fallback, sidecar rebuilt")

# 4. torn / garbage light -> fallback
pu._light_path().write_text("{not json", encoding="utf-8")
check(pu._light_status() is None and dumps(pu.status()) == dumps(pu._status_from_items(items2)), "unparseable light -> heavy fallback")

# 5. shadow mode logs agreement
ls._last_shadow.clear()
pu.PURSUITS_LIGHT_READ = False
pu._save(items2)
pu.status()
rows = [json.loads(l) for l in ls.SHADOW_LOG.read_text(encoding="utf-8").splitlines()] if ls.SHADOW_LOG.exists() else []
rows = [r for r in rows if r.get("reader") == "pursuits.status"]
check(len(rows) >= 1 and rows[-1]["agree"] is True and rows[-1]["light_present"] is True,
      f"shadow row logged, heavy==light ({rows[-1] if rows else None})")

# 6. D-0347 behaviour intact: torn heavy is moved aside, status() is the empty register, no exception
pu._ACTIVE.write_text("[{broken", encoding="utf-8")
e = pu.status()
check(e["active"] == 0 and e["pursuits"] == [] and not pu._ACTIVE.exists()
      and any(TMP.glob("pursuits_active.corrupt.*.json")), "D-0347: torn heavy file moved aside, empty status, no crash")
check(pu._light_status() is None, "...and the orphaned light companion is not trusted (heavy gone)")
pu._save(mk(5, seed=3))
check(pu._light_status() is not None and pu.status()["active"] == pu._status_from_items(mk(5, seed=3))["active"],
      "save after move-aside works, light fresh")

# 7. sample_series still appends through the light path
pu.PURSUITS_LIGHT_READ = True
pu.sample_series(force=True)
check(pu._SERIES.exists() and json.loads(pu._SERIES.read_text(encoding="utf-8").splitlines()[-1])["active"] == pu.status()["active"],
      "sample_series(force) appends a row consistent with status()")

# 8. observe() path: a real observe() through the save path keeps the light companion fresh
pu._save(mk(30, seed=4))
r = pu.observe("What is the shape of the thing I keep circling back to?", about="", vec=[0.1] * 384, cycle_id="t")
check(pu._light_status() is not None and dumps(pu._light_status()) ==
      dumps(pu._status_from_items(json.loads(pu._ACTIVE.read_text(encoding="utf-8")))),
      f"after observe() (ev={None if r is None else r.get('event')}) the light companion matches the heavy file")

# 9. optional live-size: a 19 MB copy of the live register, N>=12 before/after timing
if LIVE:
    import statistics as st
    pu._ACTIVE = TMP / "pursuits_active.json"
    shutil.copyfile(LIVE_ACTIVE, pu._ACTIVE)
    items = json.loads(pu._ACTIVE.read_text(encoding="utf-8"))
    print(f"live-size copy: {pu._ACTIVE.stat().st_size/1e6:.2f} MB, {len(items)} items")
    pu._write_light(items)
    pu.PURSUITS_LIGHT_READ = False
    ls._last_shadow.clear()
    th, tl = [], []
    for _ in range(12):
        t = time.perf_counter(); h = pu.status(); th.append((time.perf_counter() - t) * 1000)
    pu.PURSUITS_LIGHT_READ = True
    for _ in range(12):
        t = time.perf_counter(); l = pu.status(); tl.append((time.perf_counter() - t) * 1000)
    check(dumps(h) == dumps(l), "LIVE-SIZE: status() byte-identical heavy vs light")
    check(dumps(h) == dumps(pu._status_from_items(items)), "LIVE-SIZE: status() equals the pure status over the parsed copy")
    print(f"status() heavy median {st.median(th):.1f} ms (min {min(th):.1f} max {max(th):.1f}) | "
          f"light median {st.median(tl):.2f} ms (min {min(tl):.2f} max {max(tl):.2f}) N=12")
    pu.PURSUITS_LIGHT_READ = False
    th2 = []
    for _ in range(12):
        pu._last_series = 0.0
        t = time.perf_counter(); pu.sample_series(force=True); th2.append((time.perf_counter() - t) * 1000)
    pu.PURSUITS_LIGHT_READ = True
    tl2 = []
    for _ in range(12):
        t = time.perf_counter(); pu.sample_series(force=True); tl2.append((time.perf_counter() - t) * 1000)
    print(f"sample_series() heavy median {st.median(th2):.1f} ms | light median {st.median(tl2):.2f} ms N=12")
    sv = []
    for _ in range(4):
        t = time.perf_counter(); pu._save(items); sv.append((time.perf_counter() - t) * 1000)
    print(f"_save (incl. light write) median {st.median(sv):.0f} ms (F-2522 measured 425 ms before this change)")
    lw = []
    for _ in range(12):
        t = time.perf_counter(); pu._write_light(items); lw.append((time.perf_counter() - t) * 1000)
    print(f"_write_light alone median {st.median(lw):.1f} ms; light file {pu._light_path().stat().st_size} bytes")

# 10. part (b) static check: the single should_sleep call site is off the event loop, contract unchanged
src = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
check("_fire, _info = await asyncio.to_thread(_sp.should_sleep, self._last_wake_ts)" in src
      and "_fire, _info = _sp.should_sleep(" not in src, "inner_monologue_node: should_sleep runs via asyncio.to_thread at its single call site")

assert pu._ACTIVE != LIVE_ACTIVE
shutil.rmtree(TMP, ignore_errors=True)
print("RESULT:", "ALL PASS" if not fails else f"{fails} FAIL")
sys.exit(1 if fails else 0)
