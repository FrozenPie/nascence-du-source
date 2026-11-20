"""
Modulation-field test (2026-06-15) — observe-only.
1) STABILITY: numerical proof the coupled field cannot run away.
2) PERTURBATION: a novelty spike propagates through the springs THEN decays back to baseline (no lock-in).
3) EXOGENOUS: the real world/body forces drive the field to a resting bias.
4) COMBINED: a novelty spike on top of the night-world → burst_willingness response.
Touches no live state.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
from core.modulation_field import ModulationField, stability, NODES
from core import exogenous as ex

WATCH = ["novelty", "curiosity_drive", "pull_seeker", "burst_willingness", "arousal", "pull_self"]


def row(t, f):
    return f"  t{t:<2} " + "  ".join(f"{n.split('_')[0][:5]}:{f.get(n):+.2f}" for n in WATCH)


print("1) STABILITY PROOF — A = -D + W")
s = stability()
print(f"   eigenvalues (real parts): {s['eigs']}")
print(f"   max real eigenvalue: {s['max_real_eig']}  → {'STABLE ✓ (all negative: perturbations decay)' if s['stable'] else 'UNSTABLE ✗'}")

print("\n2) PERTURBATION — spike novelty +0.8 (a novel passage 'calls'), then let it run:")
f = ModulationField()
f.perturb("novelty", 0.8)
print("   " + "  ".join(f"{n.split('_')[0][:5]}" for n in WATCH))
for t in range(0, 13):
    print(row(t, f.state()))
    f.step(dt=1.0)
st = f.state()
back = all(abs(st[n] - (0.30 if n == "arousal" else 0.0)) < 0.03 for n in ("novelty", "curiosity_drive", "burst_willingness"))
print(f"   → springs fired (novelty→curiosity→seeker+burst), then RETURNED to baseline: "
      f"{'✓ no runaway' if back else '… still settling'}")

print("\n3) EXOGENOUS — the real world/body forces drive the field to equilibrium:")
exo = ex.snapshot()["net"]
print(f"   world right now: " + ", ".join(f"{k}{v:+.2f}" for k, v in exo.items() if abs(v) > 0.01))
f = ModulationField()
for _ in range(25):
    f.step(dt=1.0, exogenous=exo)
eq = f.state()
print("   field equilibrium under the world:")
for n in WATCH:
    print(f"     {n:<18} {eq[n]:+.3f}")
bw = eq["burst_willingness"]
print(f"   → pulse-manager gate: burst_willingness {bw:+.3f} → "
      f"{'open to a burst' if bw > 0.05 else 'hold bursts' if bw < -0.05 else 'neutral'}")

print("\n4) COMBINED — a novel passage arrives on top of the current world:")
f = ModulationField()
for _ in range(10):
    f.step(dt=1.0, exogenous=exo)         # settle into the world
before = f.get("burst_willingness")
f.perturb("novelty", 0.8)                  # something genuinely new
for _ in range(4):
    f.step(dt=1.0, exogenous=exo)
after = f.get("burst_willingness")
print(f"   burst_willingness: {before:+.3f} (resting in the world) → {after:+.3f} (novelty arrived)")
print(f"   → novelty {'lifted' if after > before else 'lowered'} his willingness to pursue, "
      f"by {after-before:+.3f} — engagement, applied to the schedule.")
