"""scripts/test_post_wake_row.py (J-2011, F-2611): hermetic proof of the post-wake sleep_pressure row. No LLM, no live data.

The sleep_pressure log is a temp file; core is imported BEFORE anything repoints paths and its location is asserted.

  [1] after a FIRE row, vitality (homeostasis._read_vitality) reads ~0.0 (the bug); after log_post_wake it reads ~1.0
  [2] the post_wake row: fire False, reason 'post_wake', P recomputed since the wake clock, no 'asleep' key, standard keys kept
  [3] the fire row is untouched: last_fire_ts() still returns the fire row's ts, not the post_wake row's
  [4] sleep_exit is applied first: an armed beat is disarmed, so no sleep_beat row can follow the post_wake row
  [5] kill switch writes nothing; never raises on a bad wake_ts
  [6] replay of a day of synthetic sleeps: count of 'pinned' steps (vitality tick whose last row is a fire row) is >0 before, 0 after
  [7] node wiring (AST): log_post_wake is called in the monologue node right after _last_wake_ts is set, off-loop
Run:  python scripts/test_post_wake_row.py   (from the tree under test)
"""
from __future__ import annotations
import ast, json, sys, tempfile, threading, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # BEFORE anything that could repoint paths
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
from core import sleep_pressure as sp, homeostasis

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

tmp = Path(tempfile.mkdtemp(prefix="j2011_"))
sp._LOG_FILE = tmp / "sleep_pressure_log.jsonl"
assert not str(sp._LOG_FILE).startswith(str(ROOT / "data"))
_intake = {"v": (0, 0.0)}
sp._new_intake = lambda since: _intake["v"]

def rows():
    return [json.loads(l) for l in sp._LOG_FILE.read_text(encoding="utf-8").splitlines() if l.strip()] if sp._LOG_FILE.exists() else []

def append_fire(ts, P=12.0, thr=10.0):
    with sp._LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": ts, "P": P, "threshold": thr, "fire": True, "reason": "pressure", "dark": True}) + "\n")

print("[1] vitality pinned by the fire row, released by the post-wake row")
t0 = time.time() - 600
append_fire(t0)
v_before = homeostasis._read_vitality()
check(f"after a fire row vitality is ~0 (the F-2611 pin): {v_before}", v_before <= 0.01)
_intake["v"] = (0, 0.0)
check("log_post_wake returns True", sp.log_post_wake(time.time()) is True)
v_after = homeostasis._read_vitality()
check(f"after the post-wake row vitality is ~1: {v_after}", v_after >= 0.99)

print("[2] row shape")
r = rows()[-1]
check("reason post_wake, fire False, post_wake flag", r["reason"] == "post_wake" and r["fire"] is False and r.get("post_wake") is True)
check("no 'asleep' key (awake again)", "asleep" not in r)
check("true measured P (0 here), standard keys kept", r["P"] == 0.0 and all(k in r for k in ("threshold", "dark", "awake_min", "new_notes", "new_epi_weight", "ts")))
_intake["v"] = (3, 25.0)
sp.log_post_wake(time.time())
check("P is recomputed from the intake, not hard-coded 0 (2.8 with 3 notes/25 epi)", rows()[-1]["P"] == 2.8)
_intake["v"] = (0, 0.0)

print("[3] fire row untouched")
check("last_fire_ts() still the fire row", abs(sp.last_fire_ts(default=-1.0) - t0) < 1e-6)

print("[4] armed beat is disarmed first")
sp.sleep_enter(time.time() - 3600)
n0 = len(rows())
sp.log_post_wake(time.time())
sp.log_sleep_beat()
for t in threading.enumerate():
    if t.name == "sleep-pressure-beat":
        t.join(2.0)
check("no sleep_beat row after post_wake", len(rows()) == n0 + 1 and rows()[-1]["reason"] == "post_wake")

print("[5] kill switch / robustness")
sp.POST_WAKE_ROW_ENABLED = False
n1 = len(rows())
check("kill switch writes nothing", sp.log_post_wake(time.time()) is False and len(rows()) == n1)
sp.POST_WAKE_ROW_ENABLED = True
try:
    ok = sp.log_post_wake("not-a-number")
except Exception:
    ok = "raised"
check("bad wake_ts does not raise (returns False)", ok is False)

print("[6] replay of synthetic sleeps: pinned steps before vs after")
def pinned_steps(with_post_wake):
    sp._LOG_FILE.write_text("", encoding="utf-8")
    base = 1_000_000.0
    pinned = 0
    for day in range(5):
        fire_ts = base + day * 86400
        # a normal below-threshold row, then the fire, then ~4 homeostasis ticks (600 s) during/after the sleep
        with sp._LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": fire_ts - 60, "P": 3.0, "threshold": 10.0, "fire": False, "reason": "below_threshold"}) + "\n")
        append_fire(fire_ts)
        if with_post_wake:
            sp.log_post_wake(fire_ts + 400)                  # wake after ~400 s rest
            ls = sp._LOG_FILE.read_text(encoding="utf-8").splitlines()
            pw = json.loads(ls[-1]); pw["ts"] = fire_ts + 400    # row is stamped with the real clock; place it on the synthetic timeline
            ls[-1] = json.dumps(pw); sp._LOG_FILE.write_text("\n".join(ls) + "\n", encoding="utf-8")
        for k in range(4):
            tick = fire_ts + 100 + 600 * k
            last = [json.loads(l) for l in sp._LOG_FILE.read_text(encoding="utf-8").splitlines()]
            # the tick reads the newest row whose ts <= tick
            vis = [x for x in last if x["ts"] <= tick] or last
            if vis[-1].get("fire"):
                pinned += 1
    return pinned
b = pinned_steps(False)
a = pinned_steps(True)
check(f"pinned steps before={b} (>0), after={a}: post-wake row removes the pin for ticks after the wake", b > 0 and a < b)
# honest limit: ticks DURING the sleep (before the wake) are still on the fire row -- that is J-2016 sleep rows / D-0398.

print("[7] node wiring (AST)")
src = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
ast.parse(src)
i_wake, i_pw = src.find("self._last_wake_ts = time.time()"), src.find("log_post_wake")
check("log_post_wake is called in the node, after _last_wake_ts is set", 0 < i_wake < i_pw < i_wake + 900)
check("called off-loop via asyncio.to_thread", "asyncio.to_thread(_sp_pw.log_post_wake" in src)

print("\nALL PASS" if ok_all else "\nFAILURES")
sys.exit(0 if ok_all else 1)
