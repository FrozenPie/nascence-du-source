"""scripts/lag_floor_reread.py (J-1912, F-2540/F-2541): re-read the 5 s-loop lag floor of a live incarnation with J-1892's method.

READ-ONLY on data/ (text reads only; writes JSON only into LAGFLOOR_OUT, default the system temp dir).
Per 60-tick climate gap ('[climate] dominant=' lines in data/nascence.log) it joins IGNITION / sleep / human lines,
llm_latency.jsonl, monologue_log.jsonl and transport_shadow.jsonl, then prints per incarnation window:
  (1) the quietest-class floor (no ignition/sleep-line/human, <=3 LLM calls) and the typical no-ignition median,
      as excess s/tick = (gap-300)/60;  (2) the equal-period lockstep period (intervals with exactly 5
      transport_shadow rows, gap<600) = gap/60;  (3) competence-timer wake lag ([tier3]/[stability] tick after a
      skip tick, gap-120, 0<=lag<900).
Windows D..J are the 09-29..10-07 incarnations of F-2541; K is 10-08 09:03..18:50; L is the 10-09 08:36:57 boot to
the end of the log. NOTE the quietest class is almost entirely gaps INSIDE a night-mind sleep interval (60 of 62 in L):
an awake Du always makes >3 LLM calls per 5 minutes. Edit W / bK / bL below for a new incarnation.
Run: LAGFLOOR_OUT=<dir> python -I scripts/lag_floor_reread.py
"""
import tempfile
import re, json, bisect, datetime, collections, statistics, sys, os
D = r"C:\Nascence\data"
OUT = os.environ.get("LAGFLOOR_OUT", tempfile.gettempdir())
def ep(s): return datetime.datetime.fromisoformat(s).timestamp()
W = {"D": ("2026-09-29 12:36:49", "2026-09-30 10:35:01"), "E": ("2026-09-30 20:28:49", "2026-10-01 07:17:42"),
     "G": ("2026-10-03 23:25:34", "2026-10-04 06:56:02"), "H": ("2026-10-04 20:40:29", "2026-10-05 09:00:11"),
     "I": ("2026-10-06 01:11:50", "2026-10-06 07:30:49"), "J": ("2026-10-07 12:33:26", "2026-10-07 23:59:59")}
pat = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),(\d{3}) \[([\w\.]+)\] (.*)")
ev = collections.defaultdict(list)
lines = []
with open(D + r"\nascence.log", "r", encoding="utf-8", errors="replace") as f:
    for ln in f:
        if ln[:4] != "2026" or ln[:10] < "2026-09-29": continue
        m = pat.match(ln)
        if not m: continue
        t = datetime.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").timestamp() + int(m.group(2)) / 1000
        msg = m.group(4); lg = m.group(3)
        lines.append((t, lg, msg))
        if msg.startswith("[climate] dominant="): ev["climate"].append(t)
        elif msg.startswith("[climate] IGNITION"): ev["ign"].append(t)
        elif "human:" in msg and msg.startswith("[CYCLE"): ev["human"].append(t)
        elif "Sleep State" in msg or msg.startswith("[nightly-sleep]") or msg.startswith("[sleep]"): ev["sleep"].append(t)
        if "entering Sleep State" in msg: ev["sleep_in"].append(t)
        if msg.startswith("[night] waking"): ev["sleep_out"].append(t)
        if lg == "nascence.main" and msg.startswith("Identity loaded"): ev["boot"].append(t)
        if lg == "nascence.main" and msg.startswith("Affect saved"): ev["saved"].append(t)
for k in ev: ev[k].sort()
boots = ev["boot"]
print("boots", [datetime.datetime.fromtimestamp(b).strftime("%m-%d %H:%M:%S") for b in boots[-4:]])
last_t = lines[-1][0]
# K window: 10-08 09:03 boot to last 'Affect saved' before L boot
bK = [b for b in boots if datetime.datetime.fromtimestamp(b).strftime("%m-%d") == "2026-10-08"[5:]][0] if False else None
def fmt(t): return datetime.datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S")
bK = ep("2026-10-08 09:03:08"); bL = ep("2026-10-09 08:36:57")
saved_before_L = [t for t in ev["saved"] if bK < t < bL]
eK = saved_before_L[-1] if saved_before_L else bL - 60
WE = {k: (ep(a), ep(b)) for k, (a, b) in W.items()}
WE["K"] = (bK, eK)
WE["L"] = (bL, last_t)
print("K window", fmt(bK), fmt(eK), "L window", fmt(bL), fmt(last_t))
# sleep intervals
sl_in = ev["sleep_in"]; sl_out = ev["sleep_out"]
sleep_iv = []
for a in sl_in:
    b = [x for x in sl_out if x > a]
    sleep_iv.append((a, b[0] if b else a + 3600))
def in_sleep(t0, t1):
    for a, b in sleep_iv:
        if a < t1 and b > t0: return True
    return False
lo = min(a for a, b in WE.values())
def jl(fn):
    out = []
    with open(D + "\\" + fn, "rb") as f:
        for ln in f:
            m = re.search(rb'"ts": (\d+(?:\.\d+)?)', ln[:300])
            if not m: continue
            t = float(m.group(1))
            if t >= lo: out.append((t, ln))
    return out
mono = sorted(t for t, _ in jl("monologue_log.jsonl"))
llm = []
for t, ln in jl("llm_latency.jsonl"):
    m = re.search(rb'"s": ([\d.]+)', ln)
    llm.append((t, float(m.group(1)) if m else 0.0))
llm.sort(); llm_t = [t for t, _ in llm]
ts_rows = sorted(t for t, _ in jl("transport_shadow.jsonl"))
ign = ev["ign"]; hum = ev["human"]; slp = ev["sleep"]
def cnt(lst, a, b): return bisect.bisect_right(lst, b) - bisect.bisect_right(lst, a)
rows = []
for w, (a, b) in WE.items():
    cl = [t for t in ev["climate"] if a <= t <= b]
    for t0, t1 in zip(cl, cl[1:]):
        g = t1 - t0
        if g > 3000: continue
        i0 = bisect.bisect_right(llm_t, t0); i1 = bisect.bisect_right(llm_t, t1)
        rows.append(dict(w=w, t0=t0, gap=g, ign=cnt(ign, t0, t1), human=cnt(hum, t0, t1), sleep=cnt(slp, t0, t1),
                         insleep=in_sleep(t0, t1), llm_n=i1 - i0, thoughts=cnt(mono, t0, t1), disp=cnt(ts_rows, t0, t1)))
json.dump(rows, open(OUT + r"\lag_floor_rows.json", "w"))
def pt(g): return (g - 300) / 60
def med(x): return statistics.median(x) if x else float("nan")
def q(x, p):
    x = sorted(x); return x[min(len(x) - 1, int(p * len(x)))] if x else float("nan")
print("\n=== per-window floor (excess s/tick = (gap-300)/60; period = excess+5)")
print("win  n_gaps | quietest(no ign/sleep-line/human, llm<=3): n med_excess p10 | no-ign no-sleep-line: n med_excess | equal-period(5 disp rows,gap<600): n med_period")
res = {}
for w in ["D", "E", "G", "H", "I", "J", "K", "L"]:
    s = [r for r in rows if r["w"] == w]
    q0 = [r["gap"] for r in s if r["ign"] == 0 and r["sleep"] == 0 and r["human"] == 0 and r["llm_n"] <= 3]
    ni = [r["gap"] for r in s if r["ign"] == 0 and r["sleep"] == 0]
    q0b = [r["gap"] for r in s if r["ign"] == 0 and r["sleep"] == 0 and not r["insleep"] and r["human"] == 0 and r["llm_n"] <= 3]
    nib = [r["gap"] for r in s if r["ign"] == 0 and r["sleep"] == 0 and not r["insleep"]]
    ep5 = [r["gap"] / 60 for r in s if r["disp"] == 5 and r["gap"] < 600]
    ep5n = [r["gap"] / 60 for r in s if r["disp"] == 5 and r["gap"] < 600 and r["ign"] == 0 and not r["insleep"]]
    res[w] = dict(n=len(s), q0=q0, ni=ni, q0b=q0b, nib=nib, ep5=ep5, ep5n=ep5n)
    print(f"{w}  {len(s):4d} | q n={len(q0):3d} med={pt(med(q0)):.3f} p10={pt(q(q0,.1)):.3f} | ni n={len(ni):3d} med={pt(med(ni)):.3f} | ep5 n={len(ep5):3d} med={med(ep5):.3f} (ign0 & not-in-sleep: n={len(ep5n)} med={med(ep5n):.3f})"
          f" || not-in-sleep-interval: q n={len(q0b)} med={pt(med(q0b)):.3f}; ni n={len(nib)} med={pt(med(nib)):.3f}")
allq = []
for w in "DEGHIJ": allq += res[w]["q0"]
print("D..J pooled quietest n", len(allq), "median gap", med(allq), "excess", pt(med(allq)))
# dispatch-count distribution for L
for w in ["J", "K", "L"]:
    c = collections.Counter(r["disp"] for r in rows if r["w"] == w and r["gap"] < 600)
    print(w, "dispatch rows per climate interval (gap<600)", dict(sorted(c.items())))
# per-day breakdown of L
print("\n=== L by day (quietest, no-ign) ")
byday = collections.defaultdict(lambda: dict(q=[], ni=[], ep=[]))
for r in rows:
    if r["w"] != "L": continue
    d = fmt(r["t0"])[:10]
    if r["ign"] == 0 and r["sleep"] == 0 and r["human"] == 0 and r["llm_n"] <= 3: byday[d]["q"].append(r["gap"])
    if r["ign"] == 0 and r["sleep"] == 0: byday[d]["ni"].append(r["gap"])
    if r["disp"] == 5 and r["gap"] < 600: byday[d]["ep"].append(r["gap"] / 60)
for d in sorted(byday):
    v = byday[d]
    print(d, f"q n={len(v['q'])} med={pt(med(v['q'])):.3f} | ni n={len(v['ni'])} med={pt(med(v['ni'])):.3f} | ep5 n={len(v['ep'])} med={med(v['ep']):.3f}")
def comp_lag(w):
    a, b = WE[w]
    out = []
    for key, pfx in (("tier3", "[tier3] tick"), ("stab", "[stability] tick")):
        v = [(t, "skip=" in msg) for t, lg, msg in lines if lg == "nascence.competence" and msg.startswith(pfx) and a <= t <= b]
        for i in range(len(v) - 1):
            gap = v[i + 1][0] - v[i][0] - 120
            if v[i][1] and 0 <= gap < 900:
                out.append((v[i + 1][0], gap))
    return out
print("\n=== competence-timer wake lag (skip tick -> next tick, gap-120, 0<=lag<900)")
cres = {}
for w in ["D", "E", "G", "H", "I", "J", "K", "L"]:
    lg = comp_lag(w)
    if not lg: continue
    x = [g for _, g in lg]
    xs = [g for t, g in lg if in_sleep(t - g - 120, t)]
    xa = [g for t, g in lg if not in_sleep(t - g - 120, t)]
    def stat(x):
        n = len(x)
        return dict(n=n, med=med(x), p75=q(x, .75), p90=q(x, .9), f05=sum(1 for g in x if g > .5) / n if n else float("nan"), f2=sum(1 for g in x if g > 2) / n if n else float("nan"), mx=max(x) if x else float("nan"))
    cres[w] = dict(all=stat(x), awake=stat(xa), sleep=stat(xs))
    for k, s in cres[w].items():
        if s["n"]:
            print(f"{w} {k:6s} n={s['n']:5d} med={s['med']:.4f} p75={s['p75']:.4f} p90={s['p90']:.3f} >0.5s={100*s['f05']:.1f}% >2s={100*s['f2']:.1f}% max={s['mx']:.1f}")
json.dump({w: {k: v for k, v in res[w].items()} for w in res}, open(OUT + r"\lag_floor_res.json", "w"))
json.dump(cres, open(OUT + r"\lag_floor_cres.json", "w"))
