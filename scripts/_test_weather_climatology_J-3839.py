"""J-3839: W1 climatology shape test. Pure (no data/ reads or writes, no sensorium import, no LLM). Run from the worktree.
Uses the EXACT stationary distribution of the walk per month (power iteration), not a noisy simulation."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from core import weather_climatology as wc
S = (-2, -1, -1, 0, 0, 0, 1, 2); W = (1, 4, 4, 5, 5, 5, 2, 1); N = 7

def stat(w):
    P = [[0.0] * N for _ in range(N)]; t = sum(w)
    for i in range(N):
        for s, x in zip(S, w):
            P[i][max(0, min(N - 1, i + s))] += x / t
    v = [1.0 / N] * N
    for _ in range(2000):
        v = [sum(v[i] * P[i][j] for i in range(N)) for j in range(N)]
    return v

base = stat(W); bw = sum(base[3:]); bs = base[6]
rows = [stat(wc.weather_weights(m, S, W)) for m in range(1, 13)]
aw = sum(sum(r[3:]) for r in rows) / 12; as_ = sum(r[6] for r in rows) / 12
print("baseline wet %.4f storm %.4f | tilted annual wet %.4f storm %.4f" % (bw, bs, aw, as_))
print("mon target_ratio got_ratio storm")
worst = 0
for m, r in enumerate(rows):
    got = sum(r[3:]) / bw; worst = max(worst, abs(got - wc._WET_RATIO[m]))
    print("%3d  %.3f  %.3f  %.4f" % (m + 1, wc._WET_RATIO[m], got, r[6]))
print("worst wet-ratio error %.3f" % worst)
assert abs(sum(wc._WET_RATIO) / 12 - 1) < 1e-9 and abs(sum(wc._WIND_RATIO) / 12 - 1) < 1e-9
assert abs(aw - bw) / bw < 0.02, "annual wet level moved"
assert as_ <= bs * 1.05, "storm share rose above the 08-18 level"
assert worst < 0.03
for m in range(1, 13):
    d, w = wc.direction_weights(m); assert len(d) == len(w) == 7
print("OK")
