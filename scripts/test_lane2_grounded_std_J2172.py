"""J-2172: pure-function checks for scripts/lane2_grounded_std.py (no data/ access)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lane2_grounded_std as g

def T(place, gs, day="day", leak=None):
    r = {"kind": "tick", "place": place, "daylight": day, "grounding": {"grounded_share": gs}}
    if leak: r["metaphor_judged"] = {"verdict": leak}
    return r

ref = [T("garden", .3)] * 20 + [T("study", .4)] * 80          # long-run mix 20/80
win = [T("garden", .3)] * 60 + [T("study", .4)] * 40          # garden-heavy window
r = g.standardise(win, ref)
assert abs(r["raw"] - 0.34) < 1e-9 and abs(r["standardised"] - 0.38) < 1e-9, r   # .2*.3+.8*.4
r2 = g.standardise(win + [T("shore", .9)] * 2, ref, min_n=5)   # 2 shore ticks: dropped, not silently used
assert r2["standardised"] == 0.38 and r2["dropped_strata"] == [("shore/day", 2)], r2
assert g.standardise([], ref)["standardised"] is None
lk = g.metaphor_leak([T("study", .4, leak="metaphor")] * 3 + [T("study", .4, leak="literal")] * 97)
assert lk == {"judged_n": 100, "leak": 0.03}
assert g.defeater_check({"standardised": 0.34}, lk)["revisit"] is True
assert g.defeater_check({"standardised": 0.40}, lk)["revisit"] is False
assert g.defeater_check({"standardised": None}, {"judged_n": 5, "leak": 0.5})["revisit"] is None
print("OK")
