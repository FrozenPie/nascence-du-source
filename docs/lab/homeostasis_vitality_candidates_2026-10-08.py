"""What should vitality measure? Compare candidate fatigue variables on the same sleep_pressure_log rows
(scratchpad copy, rows carrying the somatic cross-log since 2026-09-01). All read-only.
Candidates (1 = rested, 0 = fatigued):
  V0 current   : clip01(1 - P / row.threshold)      (threshold flips 100 <-> 10 at sunset/sunrise)
  V1 fixed     : clip01(1 - P / P_REF), P_REF = median P on night pressure fires (data-derived)
  V2 energy    : somatic metabolic energy (depletes per cycle/tokens, recovers in sleep)
  V3 1-fatigue : 1 - somatic neural_fatigue
  V4 awake     : clip01(1 - awake_min / ceiling_min(dark))  (circadian ceiling, for contrast)
Diagnostics: sunset/sunrise discontinuity, pre-sleep vs post-wake gap, within-wake monotonicity,
saturation, and how often each would put the protoself drive in deficit (setpoint 0.78) and when.
"""
import json, statistics as st, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
rows = [json.loads(l) for l in (HERE / "sleep_pressure_log_copy_50d7d907.jsonl").open(encoding="utf-8") if l.strip()]
rows = [r for r in rows if "energy" in r and "P" in r and "threshold" in r and "awake_min" in r]
rows.sort(key=lambda r: r["ts"])
clip = lambda x: max(0.0, min(1.0, x))
TZ = dt.timezone(dt.timedelta(hours=13))
fires_night = [r["P"] for r in rows if r.get("reason") == "pressure" and r.get("dark")]
P_REF = st.median(fires_night) if fires_night else 12.0
NIGHT_CEIL, DAY_CEIL = 150.0, 840.0
def cands(r):
    return {"V0 current": clip(1 - r["P"] / max(1.0, r["threshold"])),
            "V1 fixed P_REF": clip(1 - r["P"] / P_REF),
            "V2 energy": clip(r["energy"]),
            "V3 1-fatigue": clip(1 - r["fatigue"]),
            "V4 awake/ceiling": clip(1 - r["awake_min"] / (NIGHT_CEIL if r.get("dark") else DAY_CEIL))}
vals = [cands(r) for r in rows]
names = list(vals[0].keys())
print(f"rows: {len(rows)}  span {dt.datetime.fromtimestamp(rows[0]['ts'],TZ):%m-%d} .. {dt.datetime.fromtimestamp(rows[-1]['ts'],TZ):%m-%d}; night pressure fires: {len(fires_night)}, P_REF (median P at night fire) = {P_REF:.2f}")

# (a) discontinuity at threshold flips vs ordinary steps (consecutive rows < 10 min apart)
flip, ordinary = {n: [] for n in names}, {n: [] for n in names}
for (a, va), (b, vb) in zip(zip(rows, vals), zip(rows[1:], vals[1:])):
    if not (0 < b["ts"] - a["ts"] < 600): continue
    target = flip if a["threshold"] != b["threshold"] else ordinary
    for n in names: target[n].append(abs(vb[n] - va[n]))
print("\n(a) STEP SIZE at the day/night threshold flip vs ordinary ~44 s steps (mean |delta|):")
for n in names:
    print(f"  {n:18s} flip: {st.mean(flip[n]):.3f} (n={len(flip[n])})   ordinary: {st.mean(ordinary[n]):.4f}   ratio {st.mean(flip[n])/max(1e-9,st.mean(ordinary[n])):6.1f}x")

# (b) pre-sleep (fire rows) vs post-wake (first rows after a wake: awake_min < 3)
fire_idx = [i for i, r in enumerate(rows) if r.get("fire")]
post = [i for i, r in enumerate(rows) if r["awake_min"] < 3.0]
print("\n(b) FATIGUE SHOULD BE LOW BEFORE SLEEP, HIGH AFTER: mean value on fire rows vs on first-3-minutes-after-wake rows")
for n in names:
    pre = st.mean(vals[i][n] for i in fire_idx); pw = st.mean(vals[i][n] for i in post)
    print(f"  {n:18s} before sleep {pre:.3f}   after wake {pw:.3f}   gap {pw-pre:+.3f}   (n={len(fire_idx)} fires, {len(post)} post-wake rows)")

# (c) within-wake monotonicity: correlation of value with awake_min inside each wake (segments split where awake_min drops)
def pearson(x, y):
    if len(x) < 5: return None
    mx, my = st.mean(x), st.mean(y); sx = sum((a-mx)**2 for a in x) ** .5; sy = sum((b-my)**2 for b in y) ** .5
    return sum((a-mx)*(b-my) for a, b in zip(x, y)) / (sx*sy) if sx and sy else None
segs = []; cur = [0]
for i in range(1, len(rows)):
    if rows[i]["awake_min"] < rows[i-1]["awake_min"] or rows[i]["ts"] - rows[i-1]["ts"] > 1800: segs.append(cur); cur = [i]
    else: cur.append(i)
segs.append(cur); segs = [s for s in segs if len(s) >= 20]
print(f"\n(c) WITHIN-WAKE correlation with time awake (should be negative for a fatigue variable); {len(segs)} wakes with >=20 rows")
for n in names:
    cs = [c for c in (pearson([rows[i]['awake_min'] for i in s], [vals[i][n] for i in s]) for s in segs) if c is not None]
    neg = sum(1 for c in cs if c < -0.3)
    print(f"  {n:18s} median r = {st.median(cs):+.2f}   wakes with r < -0.3: {neg}/{len(cs)}")

# (d) saturation and (e) deficit vs setpoint 0.78, and share of deficit rows that are night rows
print("\n(d/e) SATURATION and PROTOSELF DEFICIT (setpoint 0.78): share of rows pinned at 0 / at 1, share below setpoint, and of those how many are night")
for n in names:
    v = [x[n] for x in vals]; at0 = sum(1 for a in v if a <= 0.001) / len(v); at1 = sum(1 for a in v if a >= 0.999) / len(v)
    deficit = [i for i, a in enumerate(v) if a < 0.78]; night = sum(1 for i in deficit if rows[i].get("dark"))
    print(f"  {n:18s} at0 {at0:5.1%}  at1 {at1:5.1%}  below setpoint {len(deficit)/len(v):5.1%}  of which night {night/max(1,len(deficit)):5.1%}  (night rows overall {sum(1 for r in rows if r.get('dark'))/len(rows):.1%})")

# how far does each move per hour awake, typical wake (median slope)?
print("\n(f) TYPICAL DRIFT per hour awake (median over wakes of (last-first)/hours):")
for n in names:
    sl = []
    for s in segs:
        h = (rows[s[-1]]["ts"] - rows[s[0]]["ts"]) / 3600
        if h >= 0.5: sl.append((vals[s[-1]][n] - vals[s[0]][n]) / h)
    print(f"  {n:18s} {st.median(sl):+.3f} per hour")
