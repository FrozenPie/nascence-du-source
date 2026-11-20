"""J-3472: the D-0102 mood-cluster defeater read (scripts/analyze_j3472_mood_cluster_defeater.py).

  [1] components(): a detached gauge is its own component at |r| >= 0.6; a connected set is one.
  [2] zero_lag_table(): first-difference mode strips a shared slow trend (two series that share only a ramp correlate
      ~1 raw, ~0 on first differences).
  [3] End to end on SYNTHETIC logs in a temp dir (no live data): valence family tight, opponent independent,
      lane2.commit_threshold = clip(0.35 - 0.4 * valence); ignition LEADS valence with NEGATIVE coupling
      (val[t+1] = -0.8 * ig[t] + noise). The direction rule must name ignition the leader (the sign-of-area rule
      alone gets this wrong), ignition must be the one driver, opp must be isolated at |r| >= 0.6.
  [4] The run writes only under the temp out-dir / md path.
Run from the worktree root:  python scripts/_test_J3472_mood_cluster_defeater.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import core  # noqa: E402  (BEFORE any lab_env; this test needs none)

assert str(Path(core.__file__).resolve()).startswith(str(ROOT)), core.__file__

import numpy as np  # noqa: E402

import analyze_j3472_mood_cluster_defeater as m  # noqa: E402

fails = 0


def check(cond, msg):
    global fails
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        fails += 1


# [1] components
names = ["a", "b", "c", "d"]
tbl = {("a", "b"): {"r": 0.9}, ("a", "c"): {"r": -0.8}, ("a", "d"): {"r": 0.1}, ("b", "c"): {"r": 0.7},
       ("b", "d"): {"r": None}, ("c", "d"): {"r": 0.2}}
comps = m.components(names, tbl)
check(comps == [["a", "b", "c"], ["d"]], f"components: a-b-c connected, d detached ({comps})")

# [2] first-difference mode
n = 300
rng = np.random.default_rng(1)
ramp = np.arange(n, dtype=float)
x = {k: float(ramp[k] + rng.normal(0, 1.5)) for k in range(n)}
y = {k: float(ramp[k] * 0.5 + rng.normal(0, 1.5)) for k in range(n)}
raw_t, _ = m.zero_lag_table({"x": x, "y": y}, ["x", "y"], 0, n)
d1_t, _ = m.zero_lag_table({"x": x, "y": y}, ["x", "y"], 0, n, first_diff=True)
check(raw_t[("x", "y")]["r"] > 0.95 and abs(d1_t[("x", "y")]["r"]) < 0.25,
      f"shared ramp: raw r {raw_t[('x','y')]['r']:.3f}, first-diff r {d1_t[('x','y')]['r']:.3f}")

# [3] synthetic live-format logs
tmp = Path(tempfile.mkdtemp(prefix="J3472_"))
data = tmp / "data"
data.mkdir()
DAYS = 60
bins = DAYS * 96
t0 = m.epoch("2026-08-21") + 3600
rng = np.random.default_rng(7)
ig = np.zeros(bins)
for i in range(1, bins):
    ig[i] = 0.7 * ig[i - 1] + rng.normal(0, 1.0)
val = np.zeros(bins)
for i in range(bins - 1):
    val[i + 1] = -0.8 * ig[i] + 0.3 * rng.normal()
opp = np.zeros(bins)
for i in range(1, bins):
    opp[i] = 0.7 * opp[i - 1] + rng.normal(0, 1.0)
val_s = val / (np.abs(val).max() + 1e-9)   # keep inside [-1, 1] so the clip never bites
aw = np.zeros(bins)
for i in range(1, bins):
    aw[i] = aw[i - 1] + 15.0 if (i % 48) != 0 else 0.0   # 48-bin wake bouts, reset between


def write(fname, rows):
    with open(data / fname, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


ts = [float(t0 + i * m.QUARTER + 5) for i in range(bins)]
write("affect_divergence_shadow.jsonl", [{"ts": ts[i], "carried_valence": float(val_s[i]), "proto_tonic": float(val_s[i])} for i in range(bins)])
write("felt_preamble_log.jsonl", [{"ts": ts[i], "valence": float(val_s[i] + rng.normal(0, 0.01)), "ema_valence": float(val_s[i])} for i in range(bins)])
write("thermal_relationship.jsonl", [{"ts": ts[i], "felt_valence": float(val_s[i] + rng.normal(0, 0.01))} for i in range(bins)])
write("lane2_shadow.jsonl", [{"ts": ts[i], "gain": {"commit_threshold": float(min(1.0, max(0.0, 0.35 - 0.4 * val_s[i])))}} for i in range(bins)])
write("stream_drive_shadow.jsonl", [{"ts": ts[i], "ignition": float(ig[i])} for i in range(bins)])
write("opponent_process_shadow.jsonl", [{"ts": ts[i], "b_after": float(opp[i])} for i in range(bins)])
write("sleep_pressure_log.jsonl", [{"ts": ts[i], "awake_min": float(aw[i])} for i in range(bins)])

out_dir = tmp / "out"
md = tmp / "md" / "tables.md"
snapshot_before = sorted((p.name, p.stat().st_size) for p in data.iterdir())
m.main(["--data-dir", str(data), "--out-dir", str(out_dir), "--md", str(md), "--draws", "100", "--seed", "3"])
rep = json.loads((out_dir / "mood_cluster_defeater_read.json").read_text(encoding="utf-8"))
full = rep["windows"]["FULL"]

fam = [["affect_divergence.carried_valence", "affect_drives.valence", "lane2_weather.commit_threshold",
        "thermal_relationship.felt_valence"]]
comps_full = [sorted(g) for g in full["components_hourly"]]
check(any(set(fam[0]) <= set(g) for g in comps_full), f"valence family sits inside one component (ignition may join it): {comps_full}")
check(["opponent_process.b_after"] in comps_full, "opponent_process.b_after is isolated at |r| >= 0.6")
lag = full["lag"]
key = "affect_drives.valence x continuous_stream.ignition"
check(key in lag and lag[key].get("coupling") == "-", f"ignition x valence is negatively coupled ({lag.get(key, {}).get('coupling')})")
check(lag[key].get("leader") == "continuous_stream.ignition",
      f"negative coupling: leader is ignition (leader={lag[key].get('leader')}, det_z={lag[key].get('det_z')})")
check(abs(lag[key].get("det_z", 0)) >= 3.0, f"ignition -> valence is significant under the detrended null ({lag[key].get('det_z'):+.2f})")
check(full["lag_driver_det"]["drivers"] == ["continuous_stream.ignition"], f"ignition is the one driver: {full['lag_driver_det']['drivers']}")
check(rep["verdict"]["FULL"]["isolated_gauges"] == ["opponent_process.b_after"], f"isolated: {rep['verdict']['FULL']['isolated_gauges']}")

# [4] only the temp out paths were written; the data dir is untouched
snapshot_after = sorted((p.name, p.stat().st_size) for p in data.iterdir())
check(snapshot_before == snapshot_after, "data dir untouched")
check((out_dir / "mood_cluster_pairs.tsv").exists() and (out_dir / "mood_cluster_weekly_r.tsv").exists() and md.exists(),
      "tsv + weekly tsv + md written under the temp paths")

print(f"\n{'ALL PASS' if not fails else str(fails) + ' FAILED'}")
sys.exit(1 if fails else 0)
