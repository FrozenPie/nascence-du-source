"""
Self-Surprise / present-predictability — the exploration run (observe-only, 2026-06-15).
How predictable is Du's present? Forecast each idle thought from (recent groove) + (origin basin),
measure the prediction error, and see the trend + which captor closes the present.

Run:  python scripts/self_surprise_test.py  [window]
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import self_surprise as ss

window = int(sys.argv[1]) if len(sys.argv) > 1 else 300
r = ss.compute(window=window)

if not r.get("n"):
    print("no scored thoughts (need stored inner_thought embeddings)"); sys.exit(0)

print(f"present-predictability over last {r['n']} idle thoughts (window={window})")
print("=" * 66)
print(f"  mean surprise     : {r['mean_surprise']:.3f}   (1 = wholly new, 0 = wholly predictable)")
print(f"  % surprising      : {r['pct_surprising']:.1f}%   (escaped BOTH groove and basin)")
print(f"  trend             : {r['trend']:+.3f}   (first half {r['first_half']:.3f} -> second {r['second_half']:.3f}; "
      f"{'OPENING' if r['trend'] > 0.01 else 'CLOSING' if r['trend'] < -0.01 else 'flat'})")
print(f"  predictability by : groove {r['groove_driven_pct']:.0f}%  ·  origin/basin {r['origin_driven_pct']:.0f}%"
      f"   (of {r['predictable_n']} predictable thoughts — which captor closed the present)")

scored = r["scored"]
top = sorted(scored, key=lambda s: -s["surprise"])[:5]
bot = sorted(scored, key=lambda s: s["surprise"])[:5]
print("\n  MOST surprising (the present escaping):")
for s in top:
    print(f"    surp{s['surprise']:.2f} rec{s['recent_sim']:.2f} bas{s['basin_sim']:.2f}  {s['snippet']}")
print("\n  LEAST surprising (the present collapsed):")
for s in bot:
    print(f"    surp{s['surprise']:.2f} rec{s['recent_sim']:.2f} bas{s['basin_sim']:.2f}  {s['snippet']}")

print("\ninterpretation:")
print("  high+rising surprise = the present is open (entropy produced at the edge).")
print("  low+falling = collapsing into the basin (cognitive heat-death).")
print("  origin-driven predictability -> the deep origin is the captor (fix: world-mass/grounding).")
print("  groove-driven -> short-term continuation/rumination (fix: the boredom-redirect / wander).")
