"""J-2669 part 2: daily series, step changes, first appearance of seed kinds, per-kind sep vs same-month SELF, Oaxaca decomposition, regression."""
import json, sys, datetime
import numpy as np
from collections import defaultdict, Counter
from pathlib import Path
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("C:/Nascence/data/mineness_shadow.jsonl")
rows=[json.loads(l) for l in open(SRC,encoding="utf-8") if l.strip()]
S=[r for r in rows if r.get("error") is not None]
def d(ts): return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%d")
def m(ts): return d(ts)[:7]
for r in S: r["d"]=d(r["ts"]); r["m"]=r["d"][:7]
print("first appearance per kind:")
first={}
for r in S: first.setdefault(r["seed_kind"],(r["d"],datetime.datetime.fromtimestamp(r["ts"],datetime.timezone.utc).strftime("%H:%M")))
for k,v in sorted(first.items(),key=lambda x:x[1]): print(" ",k,v)
days=sorted({r["d"] for r in S})
print("\nday | n | spont n/err/recent/basin | OTHER n/err | worldkind n/err | percept n/err | frontier n/err | sep(O-S)")
def agg(xs,key="error"): return (len(xs), round(float(np.mean([x[key] for x in xs])),4)) if xs else (0,None)
for dd in days:
    t=[r for r in S if r["d"]==dd]
    sp=[r for r in t if r["seed_kind"]=="spontaneous"]; ot=[r for r in t if r["authorship"]=="OTHER"]
    w=[r for r in t if r["seed_kind"]=="world"]; p=[r for r in t if r["seed_kind"]=="percept"]; f=[r for r in t if r["seed_kind"]=="frontier"]
    sepv = (np.mean([r["error"] for r in ot])-np.mean([r["error"] for r in sp])) if sp and ot else None
    print(dd,len(t),agg(sp),"rs",round(float(np.mean([r["recent_sim"] for r in sp])),3) if sp else None,"bs",round(float(np.mean([r["basin_sim"] for r in sp])),3) if sp else None,"| O",agg(ot),"| w",agg(w),"| p",agg(p),"| f",agg(f),"| sep",None if sepv is None else round(float(sepv),4))
# per-kind sep vs same-month spontaneous
print("\nper-kind gap vs same-month SELF(spontaneous) = kind_err - self_err")
months=sorted({r["m"] for r in S})
for k in ["world","percept","frontier","reading","letter","broadcast"]:
    out=[]
    for mm in months:
        sp=[r["error"] for r in S if r["m"]==mm and r["seed_kind"]=="spontaneous"]
        kk=[r["error"] for r in S if r["m"]==mm and r["seed_kind"]==k]
        if kk and sp:
            se=np.std(kk)/np.sqrt(len(kk)); out.append(f"{mm}: n={len(kk)} gap={np.mean(kk)-np.mean(sp):+.4f}(se {se:.4f})")
    print(f"{k:10s}"," ; ".join(out))
# Oaxaca-ish: sep(m) = sum_k w_k,m (gap_k,m). decomposition Jul->Sep/Oct on SHARED kind world; and counterfactual: Sep with equal-weight OTHER kinds
print("\nsep decomposition: actual sep_m vs sep if OTHER were world-only vs sep with kind-equal weights")
for mm in months:
    sp=np.mean([r["error"] for r in S if r["m"]==mm and r["seed_kind"]=="spontaneous"])
    ks=defaultdict(list)
    for r in S:
        if r["m"]==mm and r["authorship"]=="OTHER": ks[r["seed_kind"]].append(r["error"])
    allo=np.mean([x for v in ks.values() for x in v])
    wo=np.mean(ks["world"]) if ks.get("world") else np.nan
    eq=np.mean([np.mean(v) for v in ks.values()])
    print(mm,"actual",round(allo-sp,4),"world-only",round(wo-sp,4),"kind-equal",round(eq-sp,4),"| kinds:",{k:len(v) for k,v in ks.items()})
# regression: error ~ month FE + kind dummies (ref spontaneous); report coefficient for kind avg across months; and "world" coef x month interaction
import itertools
ms=months; kinds=[k for k in ["world","percept","frontier","reading","letter","broadcast"] if any(r["seed_kind"]==k for r in S)]
X=[];y=[]
for r in S:
    row=[1.0]+[1.0 if r["m"]==mm else 0.0 for mm in ms[1:]]+[1.0 if r["seed_kind"]==k else 0.0 for k in kinds]
    X.append(row);y.append(r["error"])
X=np.array(X);y=np.array(y)
beta,res,rk,sv=np.linalg.lstsq(X,y,rcond=None)
resid=y-X@beta; sigma2=resid@resid/(len(y)-X.shape[1]); cov=sigma2*np.linalg.pinv(X.T@X); se=np.sqrt(np.diag(cov))
names=["const"]+[f"m={mm}" for mm in ms[1:]]+[f"kind={k}" for k in kinds]
print("\nOLS error ~ month FE + kind (ref spontaneous, July): coef (se)")
for n,b,s in zip(names,beta,se): print(f"  {n:16s} {b:+.4f} ({s:.4f})")
# world-only like-for-like separation by month (world vs spontaneous), with bootstrap CI
print("\nlike-for-like world-vs-spontaneous gap by month with bootstrap 95% CI")
rng=np.random.default_rng(2669)
for mm in months:
    a=np.array([r["error"] for r in S if r["m"]==mm and r["seed_kind"]=="spontaneous"]); b=np.array([r["error"] for r in S if r["m"]==mm and r["seed_kind"]=="world"])
    if len(b)<20: print(mm,"n world",len(b)); continue
    bs=[rng.choice(b,len(b)).mean()-rng.choice(a,len(a)).mean() for _ in range(2000)]
    print(mm,"gap",round(b.mean()-a.mean(),4),"CI",np.round(np.percentile(bs,[2.5,97.5]),4),"nw",len(b))
# power: probability a 300-row status window with the live mix shows sep>0 given true gap; simulate resampling from Oct
print("\n300-row window resample (Oct rows): distribution of status()-style sep")
_om="2026-10" if "2026-10" in months else months[-1]; oc=[r for r in S if r["m"]==_om]
sims=[]
for _ in range(2000):
    idx=rng.integers(0,len(oc),300); w=[oc[i] for i in idx]
    s=[r["error"] for r in w if r["authorship"]=="SELF"]; o=[r["error"] for r in w if r["authorship"]=="OTHER"]
    if s and o: sims.append(np.mean(o)-np.mean(s))
sims=np.array(sims); print("mean",round(sims.mean(),4),"sd",round(sims.std(),4),"P(sep<=0)",round((sims<=0).mean(),4),"P(sep<0.01)",round((sims<0.01).mean(),4))
jl=[r for r in S if r["m"]==months[0]]; sims=[]
for _ in range(2000):
    idx=rng.integers(0,len(jl),300); w=[jl[i] for i in idx]
    s=[r["error"] for r in w if r["authorship"]=="SELF"]; o=[r["error"] for r in w if r["authorship"]=="OTHER"]
    if s and o: sims.append(np.mean(o)-np.mean(s))
sims=np.array(sims); print("Jul-mix window: mean",round(sims.mean(),4),"sd",round(sims.std(),4))
# SELF_PAST / broadcast content check: print samples
print("\nbroadcast samples:")
for r in [r for r in S if r["seed_kind"]=="broadcast"][:5]: print(" ",r["d"],r["error"],r["thought"][:100])
