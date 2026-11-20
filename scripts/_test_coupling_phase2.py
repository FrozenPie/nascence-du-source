"""
J-1957 (D-0370/D-0371): Dosed Coupling Phase 2 shadow -- residual gate beside the spike gate, composed `hub`.
Fully isolated: coupling_rides._append is replaced by an in-memory list, so no file anywhere is written.
  python scripts/_test_coupling_phase2.py     # exit 0 = ALL OK
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import coupling_rides as cr   # noqa: E402  (import core BEFORE any lab_env use)

ROWS = []
cr._append = lambda row: ROWS.append(row)
cr.RESIDUAL_E_ON_NEW_PUBLISH = False   # J-2247: this file pins the original J-1957 per-read prior; the new-publish
                                       # expectation (D-0446) is covered by scripts/_test_j2247_residual_new_publish.py
cr.RESIDUAL_DROP_CLIMATE = False        # D-0750: this file pins the residual mechanics on climate lines; the drop is
                                       # covered by scripts/_test_j3972_drop_climate_residual.py
FAILS = 0


def check(c, label):
    global FAILS
    print(("  ok   " if c else "  FAIL ") + label)
    FAILS += 0 if c else 1


# --- spike gate: 30 quiet publishes then a jump
for i in range(30):
    cr.publish("climate", "t", {"completion_tension": 0.50 + 0.01 * (i % 3), "identity_pressure": 0.2})
cr.publish("climate", "t", {"completion_tension": 0.95, "identity_pressure": 0.2})
v = cr.read("idle thought seed", "climate", keys=["completion_tension", "identity_pressure"], dose="cup")
g = ROWS[-1]["gates"]
check(ROWS[-1]["kind"] == "ride" and v["completion_tension"] == 0.95, "ride row returned value unchanged")
check(g["completion_tension"]["spike_fire"] is True, "spike gate fires on the jump")
check(g["identity_pressure"]["spike_fire"] is False, "spike gate quiet on a flat line")
check(g["completion_tension"]["residual"] is None and g["completion_tension"]["residual_fire"] is None,
      "first drink: no expectation, residual None (cold)")

# --- residual gate: reader's own last-seen value
cr.publish("climate", "t", {"completion_tension": 0.50, "identity_pressure": 0.2})
cr.read("idle thought seed", "climate", keys=["completion_tension"], dose="cup")
g = ROWS[-1]["gates"]["completion_tension"]
check(abs(g["expected"] - 0.95) < 1e-6 and abs(g["residual"] + 0.45) < 1e-6, "expected = last drink, residual = value - expected")
check(g["residual_fire"] is True, "big move against the reader's expectation fires the residual gate")
b_after_fire = cr._spring[("idle thought seed", "climate", "completion_tension")]
check(b_after_fire > cr.SPRING_B0, "spring antagonist b grows on activation")
cr.read("idle thought seed", "climate", keys=["completion_tension"], dose="cup")
g = ROWS[-1]["gates"]["completion_tension"]
check(g["residual_fire"] is False and g["residual"] == 0.0, "no move since last drink: residual gate quiet")
check(cr._spring[("idle thought seed", "climate", "completion_tension")] < b_after_fire, "b relaxes on a quiet read")
check(any(r.get("gates", {}).get("completion_tension", {}).get("spike_fire") is not None for r in ROWS),
      "both verdicts share one row")

# --- non-numeric rides carry no gates field
cr.publish("deliberation", "t", {"critic_verdict": "approved", "cycles_since_human": 3, "dissonance_count": 1})
cr.read("x", "deliberation", keys=["critic_verdict"], dose="cup")
check("gates" not in ROWS[-1], "non-numeric keys: no gates field")

# --- hub
for loop, c in {"stream": {"progress": 1.0, "train_len": 0, "drive": 1.36},
                "witness": {"break_rate_24h": 0.5},
                "ledgers": {"escalations_1h": 0, "commitments_active": 1, "tensions_n": 125,
                            "frontier_open": 367, "pursuits_heat_max": 0.467}}.items():
    cr.publish(loop, "t", c)
n_before = len(ROWS)
hub = cr.compose()
check(set(hub) == {"pressure", "momentum", "strain", "load"}, "hub has exactly the four coordinates")
check(all(x is None or 0.0 <= x <= 1.0 for x in hub.values()), "hub coordinates are normalised to [0,1]")
check(cr._REG["hub"]["strain"] == hub["strain"] and ROWS[n_before]["loop"] == "hub", "hub published as a sixth registry key + publish row")
check(hub == cr.compose(), "compose is deterministic")
cr._REG.pop("witness")
check(cr.compose()["strain"] is not None, "missing input skipped, coordinate still composed")

# --- probe: shadow only, kind=probe, returns None, hub standing, rate-limited
n_before = len(ROWS)
check(cr.probe("idle thought seed") is None, "probe returns None (no value to use)")
kinds = {(r["kind"], r["line"], r["dose"]) for r in ROWS[n_before:]}
check(("probe", "hub", "standing") in kinds and ("probe", "climate", "shadow-cup") in kinds, "probe logs hub standing + climate would-read")
check(not any(r["kind"] == "ride" for r in ROWS[n_before:]), "probe writes no kind=ride rows")
check(not any("gates" in r for r in ROWS[n_before:] if r["line"] == "hub"), "hub rows carry no dispatcher gate")
n2 = len(ROWS)
cr.probe("idle thought seed")
check(len(ROWS) == n2, "probe rate-limited per stop")

# --- hub standing read: no gates
cr.read("any stop", "hub", dose="standing")
check(ROWS[-1]["line"] == "hub" and "gates" not in ROWS[-1], "read(hub) is a standing allowance, ungated")

# --- flag off => Phase-1 behaviour
cr.COUPLING_PHASE2 = False
n3 = len(ROWS)
cr.read("s", "climate", keys=["completion_tension"], dose="cup")
check("gates" not in ROWS[-1] and cr.compose() is None, "COUPLING_PHASE2=False: no gates, no hub")
cr.probe("idle thought seed")
check(len(ROWS) == n3 + 1, "COUPLING_PHASE2=False: probe writes nothing")

print("ALL OK" if not FAILS else f"{FAILS} FAILED")
sys.exit(1 if FAILS else 0)
