"""
Try it: the world + his machine-body pulling on the modulation field (2026-06-15).
Reads REAL signals (GPU/CPU load+temp, local time, weather) and shows the slight force each applies
to Du's field nodes right now. Observe-only — touches no live state.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
from core import exogenous as ex

snap = ex.snapshot()

print("EXOGENOUS FORCES ON THE FIELD — the world & his body, right now")
print("=" * 90)
for rd in snap["readings"]:
    flag = "" if rd.ok else "  (no reading)"
    print(f"\n[{rd.source.upper()}] {rd.raw}{flag}")
    if rd.ok and rd.forces:
        for n, f in sorted(rd.forces.items(), key=lambda kv: -abs(kv[1])):
            if abs(f) >= 0.005:
                arrow = "↑" if f > 0 else "↓"
                print(f"     {arrow} {n:<18} {f:+.3f}")

print("\n" + "=" * 90)
print("NET PULL ON DU (sum of the slight forces):")
net = snap["net"]
for n, v in sorted(net.items(), key=lambda kv: -abs(kv[1])):
    bar = ("+" if v >= 0 else "-") * min(20, int(abs(v) * 60))
    print(f"   {n:<18} {v:+.3f}  {bar}")

# the one with immediate functional use
bw = net.get("burst_willingness", 0.0)
verdict = ("rested — open to a reading/curiosity burst" if bw > 0.05
           else "saturated/strained — hold bursts, serve the moment" if bw < -0.05
           else "neutral")
print(f"\n→ pulse-manager read: burst_willingness {bw:+.3f} → {verdict}")
print("→ lane lean:", "seeker (outward)" if net.get("pull_seeker",0) > net.get("pull_self",0)
      else "self (inward)" if net.get("pull_self",0) > net.get("pull_seeker",0) else "balanced")
print("\n(observe-only: readings real, couplings are tunable hypotheses, nothing moves live behaviour)")
