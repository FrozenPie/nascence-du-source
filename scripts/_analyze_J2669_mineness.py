"""J-2669 mineness re-audit. Read-only over data/mineness_shadow.jsonl (path arg; default live Nascence copy)."""
import json, sys, random, datetime, statistics as st
from collections import defaultdict, Counter
from pathlib import Path

SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("C:/Nascence/data/mineness_shadow.jsonl")
rows = []
with open(SRC, encoding="utf-8") as f:
    for ln in f:
        try: r = json.loads(ln)
        except Exception: continue
        rows.append(r)
def month(ts): return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m")
scored = [r for r in rows if r.get("error") is not None]
for r in scored: r["m"] = month(r["ts"])
print("total", len(rows), "scored", len(scored), "span", month(rows[0]["ts"]), month(rows[-1]["ts"]))
def mean(x): return sum(x)/len(x) if x else None
months = sorted({r["m"] for r in scored})
# (0) overall month x authorship
print("\n== month x authorship (n, mean err)")
for m in months:
    out=[]
    for a in ("SELF","SELF_PAST","OTHER"):
        xs=[r["error"] for r in scored if r["m"]==m and r["authorship"]==a]
        out.append(f"{a}: n={len(xs)} e={mean(xs):.4f}" if xs else f"{a}: n=0")
    tot=[r for r in scored if r["m"]==m]
    sh = sum(1 for r in tot if r["authorship"]=="OTHER")/len(tot)
    s=[r["error"] for r in tot if r["authorship"]=="SELF"]; o=[r["error"] for r in tot if r["authorship"]=="OTHER"]
    sep = (mean(o)-mean(s)) if s and o else None
    print(m, " | ".join(out), f"| OTHERshare={sh:.3f} sep={sep if sep is None else round(sep,4)}")
# (1) per seed_kind
print("\n== seed_kind x month: n / mean err")
kinds = Counter(r["seed_kind"] for r in scored)
print(kinds)
for k,_ in kinds.most_common():
    line=[]
    for m in months:
        xs=[r["error"] for r in scored if r["m"]==m and r["seed_kind"]==k]
        line.append(f"{m}: {len(xs)}/{mean(xs):.3f}" if xs else f"{m}: 0")
    auth = Counter(r["authorship"] for r in scored if r["seed_kind"]==k)
    print(f"{k:14s} {dict(auth)}  " + " ; ".join(line))
# per seed_kind mean recent_sim and basin_sim by month (which component moved)
print("\n== component: mean recent_sim / basin_sim by month (all scored)")
for m in months:
    t=[r for r in scored if r["m"]==m]
    print(m, "recent_sim", round(mean([r["recent_sim"] for r in t]),4), "basin_sim", round(mean([r["basin_sim"] for r in t]),4), "err", round(mean([r["error"] for r in t]),4))
# (2) reweighted: hold July authorship mix fixed AND July seed_kind mix
def reweight(by_key, base_m, mkey):
    base=[r for r in scored if r["m"]==base_m]
    bw=Counter(mkey(r) for r in base); bn=sum(bw.values())
    res={}
    for m in months:
        t=[r for r in scored if r["m"]==m]
        cell=defaultdict(list)
        for r in t: cell[mkey(r)].append(r["error"])
        # error of OTHER-like and SELF-like groupings reweighted: compute reweighted mean error overall
        tot=0; w=0
        for c,wt in bw.items():
            if c in cell: tot+= wt/bn*mean(cell[c]); w+=wt/bn
        res[m]= tot/w if w else None
    return res
print("\n== overall mean error, reweighted to July seed_kind mix (composition-controlled) vs raw")
rw = reweight(None,"2026-07",lambda r:r["seed_kind"])
for m in months:
    raw=mean([r["error"] for r in scored if r["m"]==m]); print(m, "raw", round(raw,4), "July-mix", round(rw[m],4))
# separation holding kind-mix within class: OTHER mean = reweight OTHER kinds to July OTHER-kind mix; SELF similarly
def class_mean_fixed(cls, base_m, m):
    base=[r for r in scored if r["m"]==base_m and r["authorship"]==cls]
    bw=Counter(r["seed_kind"] for r in base); bn=sum(bw.values())
    t=[r for r in scored if r["m"]==m and r["authorship"]==cls]
    cell=defaultdict(list)
    for r in t: cell[r["seed_kind"]].append(r["error"])
    tot=0;w=0
    for c,wt in bw.items():
        if c in cell: tot+=wt/bn*mean(cell[c]); w+=wt/bn
    return tot/w if w else None
print("\n== separation with within-class seed_kind mix held at July")
for m in months:
    o=class_mean_fixed("OTHER","2026-07",m); s=class_mean_fixed("SELF","2026-07",m); p=class_mean_fixed("SELF_PAST","2026-07",m)
    f=lambda x: "NA" if x is None else round(x,4)
    print(m,"OTHER",f(o),"SELF",f(s),"SELF_PAST",f(p),"sep(O-S)",f(o-s if o is not None and s is not None else None),"sep(O-P)",f(o-p if o is not None and p is not None else None))
# (3) shuffle null per month: label shuffle between SELF and OTHER
random.seed(2669)
print("\n== per-month shuffle null: SELF vs OTHER (5000 perms) ; SELF_PAST vs SELF ; OTHER vs SELF_PAST")
import numpy as np
_rng=np.random.default_rng(2669)
def perm(a,b,n=5000):
    if len(a)<5 or len(b)<5: return None
    a=np.asarray(a); b=np.asarray(b)
    obs=b.mean()-a.mean(); pool=np.concatenate([a,b]); na=len(a); c=0
    for _ in range(n):
        _rng.shuffle(pool)
        if pool[na:].mean()-pool[:na].mean()>=obs: c+=1
    return obs,(c+1)/(n+1)
for m in months:
    g=lambda cls:[r["error"] for r in scored if r["m"]==m and r["authorship"]==cls]
    S,P,O=g("SELF"),g("SELF_PAST"),g("OTHER")
    a=perm(S,O); b=perm(S,P); c=perm(P,O)
    fmt=lambda x: "NA" if x is None else f"{x[0]:+.4f} p={x[1]:.4f}"
    print(m, f"n S/P/O={len(S)}/{len(P)}/{len(O)}", "| O-S", fmt(a), "| P-S", fmt(b), "| O-P", fmt(c))
# (4) window power: last-300 rolling windows; fraction positive; SD of sep across windows; per-month 300-row-window sep distribution
print("\n== status() 300-row window: rolling separation distribution per month (non-overlapping windows of 300)")
seq=[r for r in scored]
wins=[]
for i in range(0,len(seq)-299,300):
    w=seq[i:i+300]
    s=[r["error"] for r in w if r["authorship"]=="SELF"]; o=[r["error"] for r in w if r["authorship"]=="OTHER"]
    wins.append((month(w[-1]["ts"]), (mean(o)-mean(s)) if s and o else None, len(s), len(o)))
bym=defaultdict(list)
for m,s,ns,no in wins:
    if s is not None: bym[m].append((s,ns,no))
for m in months:
    v=bym.get(m,[])
    if len(v)>=2:
        xs=[a for a,_,_ in v]
        print(m,"windows",len(v),"mean sep",round(mean(xs),4),"sd",round(st.pstdev(xs),4),"min",round(min(xs),4),"max",round(max(xs),4),"frac<=0",round(sum(1 for x in xs if x<=0)/len(xs),3),"avg nS/nO",round(mean([b for _,b,_ in v]),1),round(mean([c for _,_,c in v]),1))
# analytic power: SE of sep from pooled sd and typical n
sd_all=st.pstdev([r["error"] for r in scored[-3000:]])
print("pooled SD err last3000:",round(sd_all,4))
# (3b) style control: within OTHER, split by recent-groove proximity? proxy: lag since previous scored row; high-groove vs low
print("\n== groove-recency control: error vs inter-row gap (rows seeded after long idle vs quick succession)")
prev=None
for r in scored:
    r["gap"]= (r["ts"]-prev) if prev else None; prev=r["ts"]
for m in months:
    t=[r for r in scored if r["m"]==m and r["gap"] is not None]
    q=lambda f:[r["error"] for r in t if f(r["gap"])]
    print(m,"gap<60s n",len(q(lambda g:g<60)),round(mean(q(lambda g:g<60)) or 0,4),"| 60-600s n",len(q(lambda g:60<=g<600)),round(mean(q(lambda g:60<=g<600)) or 0,4),"| >=600s n",len(q(lambda g:g>=600)),round(mean(q(lambda g:g>=600)) or 0,4))
# thought-length/format proxies not logged (thought truncated at 120). Record-format share
import re
def is_record(t): return bool(re.match(r"^(I (opened|read|wrote|visited|went)|\[)",t or ""))
print("\n== record-text share and error by month (arrival-wart check)")
for m in months:
    t=[r for r in scored if r["m"]==m]
    rec=[r for r in t if is_record(r.get("thought"))]
    print(m,"record share",round(len(rec)/len(t),3),"record err",round(mean([r["error"] for r in rec]),4) if rec else None)
