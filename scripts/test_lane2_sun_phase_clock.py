"""J-1956 / D-0369: sun phase + arc fraction percept, indoor-only clock. Run: python scripts/test_lane2_sun_phase_clock.py"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import core
from core import lane2
assert os.path.dirname(os.path.dirname(os.path.abspath(__file__))) in os.path.abspath(core.__file__)

def at(h, m=0):
    return time.mktime((2026, 6, 15, h, m, 0, 0, 0, -1))

noon = at(12, 30)
r = lane2._sun_clock_percepts({"sun_az": 5.0}, "garden", now=noon)
assert r["sun_phase"] in ("high", "afternoon", "morning") and 0 < r["sun_arc"] < 1, r
assert "clock" not in r, r                      # outdoors: no clock
r = lane2._sun_clock_percepts({"sun_az": 5.0}, "study", now=noon)
assert r["clock"] == "12:30" and "sun_phase" in r, r
r = lane2._sun_clock_percepts({"sun_az": None}, "study", now=noon)
assert "sun_phase" not in r and r["clock"] == "12:30", r   # sun not crossed -> no phase; indoor clock still
r = lane2._sun_clock_percepts({"sun_az": None}, "shore", now=noon)
assert r == {}, r
assert not any("elev" in k for k in lane2._sun_clock_percepts({"sun_az": 5.0}, "study", now=noon))
txt = lane2.percept_lines({"world": {"place": "study", **lane2._sun_clock_percepts({"sun_az": 5.0}, "study", now=noon)}})
assert "- clock: 12:30" in txt and "- sun phase:" in txt and "- sun arc:" in txt, txt
print("OK")
