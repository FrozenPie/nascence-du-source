"""
J-2247 (D-0446, F-2925): the residual gate's expectation E updates only on a NEW publish of the line.
A re-read of the same published tuple logs fresh=False, residual None, and leaves E and the spring alone.
Fully isolated: coupling_rides._append is replaced by an in-memory list, so no file anywhere is written.
  python scripts/_test_j2247_residual_new_publish.py     # exit 0 = ALL OK
"""
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  (import core BEFORE any lab_env use)
from core import coupling_rides as cr   # noqa: E402

assert Path(core.__file__).resolve().is_relative_to(ROOT.resolve()), core.__file__
ROWS = []
cr._append = lambda row: ROWS.append(row)
FAILS = 0
S = "idle thought seed"
cr.RESIDUAL_DROP_CLIMATE = False   # D-0750: this file pins D-0446 on climate lines; drop covered by _test_j3972_*


def check(c, label):
    global FAILS
    print(("  ok   " if c else "  FAIL ") + label)
    FAILS += 0 if c else 1


def pub(loop, coords):
    cr.publish(loop, "t", coords)
    time.sleep(0.002)                 # distinct registry ts per publish


def g_of(key):
    return ROWS[-1]["gates"][key]


check(cr.RESIDUAL_E_ON_NEW_PUBLISH is True, "flag on by default (D-0446)")

# --- ledgers: one publish, many probe-cadence re-reads
for i in range(25):
    pub("ledgers", {"escalations_1h": i % 2, "frontier_open": 300})
pub("ledgers", {"escalations_1h": 1, "frontier_open": 300})
cr.read(S, "ledgers", keys=["escalations_1h"], dose="cup")
check(g_of("escalations_1h")["fresh"] is True and g_of("escalations_1h")["residual"] is None,
      "first drink of a publish: fresh=True, cold E -> residual None")
for _ in range(6):                    # 6 more idle-seed reads inside the same 10-min ledger publish
    cr.read(S, "ledgers", keys=["escalations_1h"], dose="cup")
    g = g_of("escalations_1h")
    check(g["fresh"] is False and g["residual"] is None and g["residual_fire"] is None and g["spike_fire"] is not None,
          "re-read of the same publish: fresh=False, no residual verdict, spike verdict still reported")
check(cr._last_seen[(S, "ledgers", "escalations_1h")] == 1.0, "E held at the drunk value")

pub("ledgers", {"escalations_1h": 3, "frontier_open": 300})
b0 = cr._spring.get((S, "ledgers", "escalations_1h"), cr.SPRING_B0)
cr.read(S, "ledgers", keys=["escalations_1h"], dose="cup")
g = g_of("escalations_1h")
check(g["fresh"] is True and g["expected"] == 1.0 and g["residual"] == 2.0, "new publish: residual against the PREVIOUS publish's value")
check(g["residual_fire"] is True and cr._spring[(S, "ledgers", "escalations_1h")] > b0, "jump fires; spring grows")
b1 = cr._spring[(S, "ledgers", "escalations_1h")]
for _ in range(5):
    cr.read(S, "ledgers", keys=["escalations_1h"], dose="cup")
check(cr._spring[(S, "ledgers", "escalations_1h")] == b1, "re-reads neither relax nor grow the spring")
fires = sum(1 for r in ROWS if r.get("gates", {}).get("escalations_1h", {}).get("residual_fire") is True)
check(fires == 1, "one surprise -> exactly one residual fire (not one per re-read)")

# --- a new publish whose value is unchanged is still evidence: fresh, residual 0, quiet, spring relaxes
pub("ledgers", {"escalations_1h": 3, "frontier_open": 300})
cr.read(S, "ledgers", keys=["escalations_1h"], dose="cup")
g = g_of("escalations_1h")
check(g["fresh"] is True and g["residual"] == 0.0 and g["residual_fire"] is False, "unchanged value on a new publish: fresh, residual 0, quiet")
check(cr._spring[(S, "ledgers", "escalations_1h")] < b1, "spring relaxes on a fresh quiet read")

# --- per-stop: another stop has its own E and its own freshness
cr.read("other stop", "ledgers", keys=["escalations_1h"], dose="cup")
check(g_of("escalations_1h")["fresh"] is True, "freshness is per (stop, line, key)")

# --- probe passes the publish ts too
cr._probe_last.clear()
pub("climate", {"completion_tension": 0.4, "identity_pressure": 0.2, "world_model_strain": 0.1, "novelty_hunger": 0.5})
cr.probe(S)
pr = [r for r in ROWS if r["kind"] == "probe" and r["line"] == "climate"][-1]
check(all(v.get("fresh") is True for v in pr["gates"].values()), "probe rows carry fresh=True on a new climate publish")
cr._probe_last.clear()
cr.probe(S)
pr = [r for r in ROWS if r["kind"] == "probe" and r["line"] == "climate"][-1]
check(all(v.get("fresh") is False and v["residual"] is None for v in pr["gates"].values()), "probe re-read of same climate publish: fresh=False")
check(cr.probe(S) is None, "probe still returns None (shadow only)")

# --- return values unchanged: read() returns exactly the published coordinate
check(cr.read(S, "ledgers", keys=["frontier_open"], dose="cup") == {"frontier_open": 300}, "read() return value unchanged")

# --- flag off: J-1957 per-read prior, no fresh field
cr.RESIDUAL_E_ON_NEW_PUBLISH = False
cr.read(S, "ledgers", keys=["escalations_1h"], dose="cup")
g = g_of("escalations_1h")
check("fresh" not in g and g["residual"] == 0.0 and g["residual_fire"] is False, "flag off: old per-read prior, no fresh field")
check(cr._gates_for("x", "ledgers", {"escalations_1h": 3}) and "fresh" not in cr._gates_for("y", "ledgers", {"escalations_1h": 3})["escalations_1h"],
      "no pub_ts: old behaviour")

print("ALL OK" if not FAILS else f"{FAILS} FAILED")
sys.exit(1 if FAILS else 0)
