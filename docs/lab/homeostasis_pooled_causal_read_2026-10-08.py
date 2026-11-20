"""Pooled read of homeostasis's causal-substrate predictor vs naive persistence ACROSS regimes.

Read-only: copies data/homeostasis_shadow.jsonl to the scratchpad first, imports core.world_clock only
(pure function of ts). Scores every (prev -> cur) prediction step exactly as the chain's own tests do:
  naive_err  = |actual_cur - actual_prev|
  causal_err = |actual_cur - predicted_causal_prev|
  trend_err  = |actual_cur - predicted_next_prev|      (the original EMA-trend self-model, for reference)
per variable, never pooled across variables (D-0045/D-0108 methodology). Regime = a run of rows with no
gap > GAP_S (a restart or offline stretch starts a new regime). Switch row = world_clock.daylight flips
day<->night between prev and cur (the D-0279 'scoreable switch event', before stale handling).
Stale row (per variable) = actual_cur == actual_prev exactly (naive_err 0 by circularity) -- reported, and
the sign tests are given both with and without them.
"""
import json, shutil, sys, math, collections, datetime as dt
from pathlib import Path

ROOT = Path(r"C:\Nascence"); sys.path.insert(0, str(ROOT))
from core import world_clock as wc  # noqa

SRC = ROOT / "data" / "homeostasis_shadow.jsonl"
HERE = Path(__file__).resolve().parent
COPY = HERE / "homeostasis_shadow_copy_50d7d907.jsonl"
shutil.copyfile(SRC, COPY)
SINCE = 1788517496.0   # F-0810/J-0582 fix = start of the valid predicted_causal corpus (F-0986)
GAP_S = 1800.0
EPS = 1e-12
VARS = ("coherence", "novelty", "vitality")
TZ = dt.timezone(dt.timedelta(hours=13))
f = lambda ts: dt.datetime.fromtimestamp(ts, TZ).strftime("%m-%d %H:%M")

rows = []
with COPY.open(encoding="utf-8") as fh:
    for line in fh:
        try: d = json.loads(line)
        except Exception: continue
        if d.get("ts", 0) >= SINCE and isinstance(d.get("predicted_causal"), dict) and isinstance(d.get("variables"), dict):
            rows.append(d)
rows.sort(key=lambda r: r["ts"])
print(f"rows with predicted_causal since {f(SINCE)}: {len(rows)}  ({f(rows[0]['ts'])} .. {f(rows[-1]['ts'])})")

# regimes
regimes = []; cur = [rows[0]]
for r in rows[1:]:
    if r["ts"] - cur[-1]["ts"] > GAP_S: regimes.append(cur); cur = [r]
    else: cur.append(r)
regimes.append(cur)

def sign_p(w, l):
    n = w + l
    if n == 0: return float("nan")
    k = min(w, l); p = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(1.0, 2 * p)

steps = []  # one per (prev,cur) within a regime
for gi, g in enumerate(regimes):
    for prev, cur in zip(g, g[1:]):
        dark_p = wc.daylight(prev["ts"]) == "night"; dark_c = wc.daylight(cur["ts"]) == "night"
        st = {"regime": gi, "ts": cur["ts"], "switch": dark_p != dark_c, "to": "night" if dark_c else "day"}
        for v in VARS:
            a_c = cur["variables"].get(v); a_p = prev["variables"].get(v)
            pc = prev["predicted_causal"].get(v); pn = (prev.get("predicted_next") or {}).get(v)
            if a_c is None or a_p is None or pc is None: continue
            st[v] = {"naive": abs(a_c - a_p), "causal": abs(a_c - pc),
                     "trend": abs(a_c - pn) if pn is not None else None, "stale": a_c == a_p}
        steps.append(st)

print(f"\nREGIMES ({len(regimes)}): rows / hours / switch events (day<->night flips)")
for gi, g in enumerate(regimes):
    sw = sum(1 for s in steps if s["regime"] == gi and s["switch"])
    hrs = (g[-1]["ts"] - g[0]["ts"]) / 3600
    print(f"  r{gi:02d} {f(g[0]['ts'])} -> {f(g[-1]['ts'])}  rows={len(g):4d} hours={hrs:6.1f} switches={sw}")
print(f"  total switch events across regimes: {sum(1 for s in steps if s['switch'])}; regimes with >=9: {sum(1 for gi in range(len(regimes)) if sum(1 for s in steps if s['regime']==gi and s['switch'])>=9)}")

def report(name, sel):
    print(f"\n== {name}: {len(sel)} steps")
    for v in VARS:
        ss = [s[v] for s in sel if v in s]
        if not ss: continue
        ident = sum(1 for x in ss if abs(x["causal"] - x["naive"]) <= EPS)
        stale = sum(1 for x in ss if x["stale"])
        def wl(xs):
            w = sum(1 for x in xs if x["naive"] - x["causal"] > EPS); l = sum(1 for x in xs if x["causal"] - x["naive"] > EPS)
            return w, l, len(xs) - w - l
        w, l, t = wl(ss); w2, l2, t2 = wl([x for x in ss if not x["stale"]])
        mae_n = sum(x["naive"] for x in ss) / len(ss); mae_c = sum(x["causal"] for x in ss) / len(ss)
        tr = [x["trend"] for x in ss if x["trend"] is not None]; mae_t = sum(tr) / len(tr) if tr else float("nan")
        print(f"  {v:9s} n={len(ss):5d} identical_to_naive={ident:5d} stale={stale:5d} | MAE naive={mae_n:.4f} causal={mae_c:.4f} trend={mae_t:.4f} | "
              f"sign all: causal {w}/naive {l}/tie {t} p={sign_p(w,l):.3g} | non-stale: {w2}/{l2}/{t2} p={sign_p(w2,l2):.3g}")

report("ALL STEPS pooled across regimes", steps)
report("SWITCH ROWS only (D-0279's scoreable events), pooled across regimes", [s for s in steps if s["switch"]])
report("NON-SWITCH rows pooled", [s for s in steps if not s["switch"]])

# per-regime direction on switch rows and on all rows, for consistency
print("\nPER-REGIME direction (causal wins - naive wins), non-stale steps; switch rows in brackets")
for gi in range(len(regimes)):
    line = f"  r{gi:02d}"
    for v in VARS:
        ss = [s[v] for s in steps if s["regime"] == gi and v in s and not s[v]["stale"]]
        sw = [s[v] for s in steps if s["regime"] == gi and s["switch"] and v in s and not s[v]["stale"]]
        d = sum(1 for x in ss if x["naive"] - x["causal"] > EPS) - sum(1 for x in ss if x["causal"] - x["naive"] > EPS)
        dsw = sum(1 for x in sw if x["naive"] - x["causal"] > EPS) - sum(1 for x in sw if x["causal"] - x["naive"] > EPS)
        line += f"  {v[:4]} {d:+4d}[{dsw:+d}/{len(sw)}]"
    print(line)

# event-aligned 6-fold over pooled switch events (chronological across regimes), per variable
print("\nEVENT-ALIGNED 6 FOLDS over pooled switch events (chronological, regimes concatenated), MAE verdict per fold")
sw_idx = [i for i, s in enumerate(steps) if s["switch"]]
k = len(sw_idx); nf = min(6, k)
bounds = [0] + [ (sw_idx[(j * k) // nf - 1] + sw_idx[(j * k) // nf]) // 2 + 1 for j in range(1, nf) ] + [len(steps)]
for v in VARS:
    out = []
    for j in range(nf):
        seg = [s[v] for s in steps[bounds[j]:bounds[j+1]] if v in s and not s[v]["stale"]]
        if not seg: out.append("empty"); continue
        mn = sum(x["naive"] for x in seg) / len(seg); mc = sum(x["causal"] for x in seg) / len(seg)
        out.append("CAUSAL" if mn - mc > 1e-9 else ("naive" if mc - mn > 1e-9 else "tie"))
    print(f"  {v:9s} folds={nf} events={k}: {out}  -> causal wins {out.count('CAUSAL')}/{nf}")
print("\nNOTE: folds here span regime boundaries (that is the pooling assumption under test).")
