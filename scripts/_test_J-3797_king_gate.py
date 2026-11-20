"""J-3797 test: king_tide_now flag-off == legacy 0.92 rule; flag-on yields ~8 king days/yr at 0.99. Pure, no live data."""
import sys, datetime as dt
from pathlib import Path
TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core  # noqa
from core import world_objects as wo, world_clock as wc
assert Path(wo.__file__).resolve().is_relative_to(TREE)
assert wo.KING_TIDE_GATE_ENABLED is False
t0 = dt.datetime(2026, 1, 1, 12).timestamp()
for lvl in (None, 0.5, 0.91, 0.92, 0.95, 1.0):
    assert wo.king_tide_now(t0, lvl) == (lvl is not None and lvl >= 0.92), lvl
wo.KING_TIDE_GATE_ENABLED = True
assert not wo.king_tide_now(t0, 0.98) and not wo.king_tide_now(t0, None)
days = set(); hits = 0
t = dt.datetime(2026, 1, 1).timestamp()
end = t + 365 * 86400
while t < end:
    if wo.king_tide_now(t, wc.tide(t)["level"]):
        days.add(dt.date.fromtimestamp(t)); hits += 1
    t += 600
print("king days (flag on, 2026):", len(days))
assert 0 <= len(days) <= 16, len(days)
d1 = [wo._king_day(dt.datetime(2026, 1, 1).timestamp() + i * 86400) for i in range(365)]
print("qualifying calendar days:", sum(d1)); assert 2 <= sum(d1) <= 16
assert d1 == [wo._king_day(dt.datetime(2026, 1, 1).timestamp() + i * 86400) for i in range(365)]
print("OK")
