"""J-2213 regression: core/smell.py RENOTICE re-arm + both channels' DELIVER state.

Drives the REAL smell.percept_shadow() with a fake clock: he stays 24 h at one place with one dominant odorant.
RENOTICE_REARM=True  -> a renotice at most once per RENOTICE_S (docstring: "rare renotice") -> <= 4 in 24 h.
RENOTICE_REARM=False -> the pre-J-2213 behaviour: after 6 h, one every COOLDOWN_S (~15 min) -> dozens.
No live data: smell._log / at / phrasing.vary / store_fragment are stubbed; runs inside lab_env.isolate().
"""
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # BEFORE lab_env (F-2423)
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
from core import smell, light, thermal, channel_arbitration as arb, sensorium, phrasing
from core.memory import store as _store
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

def run(rearm: bool):
    smell.RENOTICE_REARM = rearm
    smell._p.clear(); smell._p.update({"place": None, "dominant": None, "since": 0.0, "last": 0.0, "seen": {}})
    arb.reset()
    clock = {"t": 1_800_000_000.0}
    logged, stored = [], []
    smell.time.time = lambda: clock["t"]
    smell.at = lambda place, now=None: [("woodsmoke", 0.4)]
    smell._log = lambda rec: logged.append(rec)
    phrasing.vary = lambda key, opts: opts[0]
    _store.store_fragment = lambda **kw: stored.append(kw)
    sensorium.state = {"location": "study"}
    lines = []
    for _ in range(int(24 * 3600 / 60)):          # a tick a minute for 24 h
        ln = smell.percept_shadow("t")
        if ln: lines.append(ln)
        clock["t"] += 60.0
    kinds = [r["would_fire"] for r in logged if r.get("would_fire")]
    rts = [r["ts"] for r in logged if r.get("would_fire") == "renotice"]
    run.gaps = [b - a for a, b in zip(rts, rts[1:])]
    return kinds, lines, stored

with isolate():
    print("DELIVER flags:", "light", light.DELIVER, "smell", smell.DELIVER, "thermal", thermal.DELIVER)
    check("light.DELIVER is True (J-2213)", light.DELIVER is True)
    check("smell.DELIVER is True (J-2213)", smell.DELIVER is True)
    check("thermal.DELIVER unchanged True (D-0047)", thermal.DELIVER is True)
    k_on, lines_on, st_on = run(True)
    gaps_on = run.gaps
    k_off, _, _ = run(False)
    print("rearm=True kinds:", k_on.count("entry"), "entry,", k_on.count("renotice"), "renotice")
    print("rearm=False kinds:", k_off.count("entry"), "entry,", k_off.count("renotice"), "renotice")
    check("rearm=True: renotice <= 4 in 24 h at one place", k_on.count("renotice") <= 4)
    check("rearm=True: renotice gaps >= RENOTICE_S", all(g >= smell.RENOTICE_S for g in gaps_on))
    check("rearm=False reproduces the old flood (> 40 renotices in 24 h)", k_off.count("renotice") > 40)
    check("delivered lines returned == fires (DELIVER path)", len(lines_on) == len(k_on))
    check("each delivered line stored once with origin=smell", len(st_on) == len(k_on) and all(s.get("origin") == "smell" for s in st_on))
    smell.RENOTICE_REARM = True
print("ALL PASS" if ok_all else "SOME FAILED")
sys.exit(0 if ok_all else 1)
