"""J-3972 / D-0750: residual half dropped on the four climate lines only; ledgers keep it. In-memory, no live stores."""
import sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import core  # noqa: E402
from core import coupling_rides as cr  # noqa: E402
assert Path(core.__file__).resolve().is_relative_to(ROOT.resolve()), core.__file__
ROWS = []
cr._append = lambda row: ROWS.append(row)
FAILS = 0
S = "idle thought seed"


def check(c, label):
    global FAILS
    print(("  ok   " if c else "  FAIL ") + label)
    FAILS += 0 if c else 1


def pub(loop, coords):
    cr.publish(loop, "t", coords)
    time.sleep(0.002)


check(cr.RESIDUAL_DROP_CLIMATE is True, "flag on by default")
C4 = ["completion_tension", "identity_pressure", "world_model_strain", "novelty_hunger"]
for i in range(3):
    pub("climate", {k: 0.2 + 0.2 * i for k in C4})
    cr.read(S, "climate", keys=C4, dose="cup")
    pub("ledgers", {"escalations_1h": float(i), "frontier_open": 10.0 + 5 * i})
    cr.read(S, "ledgers", keys=["escalations_1h", "frontier_open"], dose="cup")
cg = [r for r in ROWS if r.get("line") == "climate" and r.get("gates")][-1]["gates"]
check(all(cg[k]["residual"] is None and cg[k]["residual_fire"] is None and cg[k].get("residual_dropped") for k in C4),
      "climate: residual dropped on all four")
check(all("spike_fire" in cg[k] for k in C4), "climate: spike verdict still reported")
check(not any(k[1] == "climate" for k in cr._spring) and not any(k[1] == "climate" for k in cr._last_seen),
      "climate: no expectation or spring state kept")
lg = [r for r in ROWS if r.get("line") == "ledgers" and r.get("gates")][-1]["gates"]
check(all(lg[k]["residual"] is not None and lg[k].get("fresh") is True for k in lg), "ledgers: residual half kept")
cr.RESIDUAL_DROP_CLIMATE = False
g = cr._gates_for("s2", "climate", {"completion_tension": 0.1}, 1.0)
g = cr._gates_for("s2", "climate", {"completion_tension": 0.9}, 2.0)
check(g["completion_tension"]["residual"] is not None, "flag off restores residual on climate")
print("FAILED" if FAILS else "ALL OK")
sys.exit(1 if FAILS else 0)
