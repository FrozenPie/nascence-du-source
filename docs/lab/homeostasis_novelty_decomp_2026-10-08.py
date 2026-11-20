"""Novelty thread (F-2609 follow-up): WHY does the causal novelty predictor lose to persistence, and
would a cheap fix beat it? Offline, read-only, on the scratchpad copy of homeostasis_shadow.jsonl.

Identities used (core/climate_engine.py:706-707, core/homeostasis.py _read_coherence, homeostasis_causal):
  coherence_actual   = clip01(1 - diss)                      -> diss_prev = 1 - coh_prev   (valid when 0 < coh < 1)
  novelty_actual     = clip01(0.5*(1 - sa) + 0.25*diss + surprise_addend)
  causal_novelty     = clip01(0.5*(1 - sa_prev) + 0.25*proj)  with proj = 1 - causal_coherence (valid when 0 < pc_coh < 1)
So on an unclipped step the causal predictor differs from persistence by exactly
  causal - naive = 0.25*(proj - diss_prev) - surprise_prev       (it carries the dissonance forecast, drops the addend)
Predictors compared per step (per variable novelty):
  P0 naive      = nov_prev
  P1 causal     = logged predicted_causal.novelty
  P2 hybrid     = nov_prev + 0.25*(proj - diss_prev)   (persistence for quietness+surprise, causal for dissonance)
  P3 half-hybrid= nov_prev + 0.125*(proj - diss_prev)  (shrunk dissonance term, in case proj overshoots)
Also: variance decomposition of actual novelty steps into the dissonance part and the rest.
"""
import json, math, collections, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
COPY = HERE / "homeostasis_shadow_copy_50d7d907.jsonl"
SINCE = 1788517496.0; GAP_S = 1800.0; EPS = 1e-12
rows = []
for line in COPY.open(encoding="utf-8"):
    try: d = json.loads(line)
    except Exception: continue
    if d.get("ts", 0) >= SINCE and isinstance(d.get("predicted_causal"), dict): rows.append(d)
rows.sort(key=lambda r: r["ts"])

def sign_p(w, l):
    n = w + l
    if n == 0: return float("nan")
    k = min(w, l); return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)

steps = []
for prev, cur in zip(rows, rows[1:]):
    if cur["ts"] - prev["ts"] > GAP_S: continue
    vp, vc, pc = prev["variables"], cur["variables"], prev["predicted_causal"]
    if any(k not in vp or k not in vc or k not in pc for k in ("novelty", "coherence")): continue
    unclipped = 0.0 < vp["coherence"] < 1.0 and 0.0 < pc["coherence"] < 1.0
    diss_prev = 1 - vp["coherence"]; proj = 1 - pc["coherence"]
    dd = proj - diss_prev
    a = vc["novelty"]
    preds = {"P0 naive": vp["novelty"], "P1 causal": pc["novelty"],
             "P2 hybrid": max(0, min(1, vp["novelty"] + 0.25 * dd)) if unclipped else vp["novelty"],
             "P3 half-hybrid": max(0, min(1, vp["novelty"] + 0.125 * dd)) if unclipped else vp["novelty"]}
    steps.append({"ts": cur["ts"], "actual": a, "preds": preds, "unclipped": unclipped,
                  "d_nov": a - vp["novelty"], "d_diss_term": 0.25 * ((1 - vc["coherence"]) - diss_prev) if (0 < vc["coherence"] < 1 and 0 < vp["coherence"] < 1) else None,
                  "causal_minus_naive": pc["novelty"] - vp["novelty"]})
print(f"steps: {len(steps)}  unclipped (coherence strictly inside (0,1) at prev and in the forecast): {sum(s['unclipped'] for s in steps)}")

print("\nPREDICTOR LEAGUE (MAE, and sign test vs naive; ties = |diff|<=1e-12)")
for name in steps[0]["preds"]:
    errs = [abs(s["actual"] - s["preds"][name]) for s in steps]
    mae = sum(errs) / len(errs)
    w = l = 0
    for s in steps:
        e0 = abs(s["actual"] - s["preds"]["P0 naive"]); e = abs(s["actual"] - s["preds"][name])
        if e0 - e > EPS: w += 1
        elif e - e0 > EPS: l += 1
    print(f"  {name:15s} MAE={mae:.4f}  beats naive on {w} / loses {l} / ties {len(steps)-w-l}  p={sign_p(w,l):.3g}")

# bias: is the causal predictor systematically low (missing addend) or is its dissonance forecast wrong?
cm = [s["causal_minus_naive"] for s in steps]
signed = [s["actual"] - s["preds"]["P1 causal"] for s in steps]
print(f"\nBIAS: mean(actual - causal) = {sum(signed)/len(signed):+.4f}   median = {sorted(signed)[len(signed)//2]:+.4f}")
print(f"      mean(causal - naive) = {sum(cm)/len(cm):+.4f}; share of steps where causal < naive: {sum(1 for x in cm if x < -EPS)/len(cm):.2%}")
# is the direction of the causal adjustment right? (when causal says novelty will rise vs fall, does it?)
agree = sum(1 for s in steps if abs(s["causal_minus_naive"]) > 1e-4 and abs(s["d_nov"]) > 1e-4 and (s["causal_minus_naive"] > 0) == (s["d_nov"] > 0))
tot = sum(1 for s in steps if abs(s["causal_minus_naive"]) > 1e-4 and abs(s["d_nov"]) > 1e-4)
print(f"      direction agreement (sign of causal adjustment vs sign of actual change, both > 1e-4): {agree}/{tot} = {agree/max(1,tot):.1%}")

# variance decomposition of actual novelty changes
dn = [s["d_nov"] for s in steps if s["d_diss_term"] is not None]
dterm = [s["d_diss_term"] for s in steps if s["d_diss_term"] is not None]
rest = [a - b for a, b in zip(dn, dterm)]
var = lambda xs: sum((x - sum(xs)/len(xs))**2 for x in xs) / len(xs)
print(f"\nVARIANCE of per-step novelty change (n={len(dn)}): total {var(dn):.5f}; dissonance term {var(dterm):.5f}; rest (quietness+surprise) {var(rest):.5f}")
big = sorted(steps, key=lambda s: -abs(s["d_nov"]))[:8]
TZ = dt.timezone(dt.timedelta(hours=13))
print("\nLARGEST actual novelty jumps (ts, d_nov, dissonance-term part, causal adj):")
for s in big:
    print(f"  {dt.datetime.fromtimestamp(s['ts'],TZ):%m-%d %H:%M}  d_nov={s['d_nov']:+.3f}  diss_part={s['d_diss_term'] if s['d_diss_term'] is None else round(s['d_diss_term'],3)}  causal_adj={s['causal_minus_naive']:+.3f}")
# distribution of step sizes
small = sum(1 for s in steps if abs(s["d_nov"]) < 0.01)
print(f"\nSTEP SIZE: |d_nov| < 0.01 on {small}/{len(steps)} steps ({small/len(steps):.1%}); |causal adj| > 0.05 on {sum(1 for s in steps if abs(s['causal_minus_naive'])>0.05)} steps")
