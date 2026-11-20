"""J-2669 part 3: time-shift/block nulls, cluster (day) bootstrap, AUC by component, which arm dominates, text-overlap proxy."""
import json, sys, datetime, re
import numpy as np
from pathlib import Path
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("C:/Nascence/data/mineness_shadow.jsonl")
rows=[json.loads(l) for l in open(SRC,encoding="utf-8") if l.strip()]
S=[r for r in rows if r.get("error") is not None]
def d(ts): return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%d")
for r in S: r["d"]=d(r["ts"]); r["m"]=r["d"][:7]
months=sorted({r["m"] for r in S}); rng=np.random.default_rng(26690)
def sep_of(err,auth):
    s=err[auth==0]; o=err[auth==1]
    return o.mean()-s.mean() if len(s) and len(o) else np.nan
print("== time-shift (circular) null for sep(O-S) per month, 2000 shifts >=300 rows; plus day-cluster bootstrap 95% CI")
for mm in months:
    t=[r for r in S if r["m"]==mm and r["authorship"] in ("SELF","OTHER")]
    err=np.array([r["error"] for r in t]); au=np.array([1 if r["authorship"]=="OTHER" else 0 for r in t]); n=len(t)
    obs=sep_of(err,au); nulls=[]
    for _ in range(2000):
        k=int(rng.integers(300,n-300)); nulls.append(sep_of(err,np.roll(au,k)))
    nulls=np.array(nulls); p=(1+np.sum(nulls>=obs))/(1+len(nulls))
    days=sorted({r["d"] for r in t}); idx={dd:[i for i,r in enumerate(t) if r["d"]==dd] for dd in days}
    bs=[]
    for _ in range(2000):
        pick=rng.choice(len(days),len(days)); ii=np.concatenate([idx[days[j]] for j in pick]); bs.append(sep_of(err[ii],au[ii]))
    print(mm,"sep",round(obs,4),"timeshift-null mean/sd",round(nulls.mean(),4),round(nulls.std(),4),"p",round(p,4),"| day-cluster CI",np.round(np.nanpercentile(bs,[2.5,97.5]),4),"ndays",len(days))
def auc(pos,neg):
    # P(pos>neg) via rank, subsample for speed
    pos=np.asarray(pos); neg=np.asarray(neg)
    if len(pos)>4000: pos=rng.choice(pos,4000,replace=False)
    if len(neg)>4000: neg=rng.choice(neg,4000,replace=False)
    allv=np.concatenate([pos,neg]); order=allv.argsort().argsort()+1
    r=order[:len(pos)].sum(); return (r-len(pos)*(len(pos)+1)/2)/(len(pos)*len(neg))
print("\n== AUC(world-seeded vs spontaneous) by component per month (0.5 = no discrimination)")
for mm in months:
    sp=[r for r in S if r["m"]==mm and r["seed_kind"]=="spontaneous"]; w=[r for r in S if r["m"]==mm and r["seed_kind"]=="world"]
    if len(w)<30: print(mm,"n world",len(w)); continue
    f=lambda key,rs:[x[key] for x in rs]
    a_err=auc(f("error",w),f("error",sp)); a_rs=auc([-x["recent_sim"] for x in w],[-x["recent_sim"] for x in sp]); a_bs=auc([-x["basin_sim"] for x in w],[-x["basin_sim"] for x in sp])
    dom_sp=np.mean([x["basin_sim"]>=x["recent_sim"] for x in sp]); dom_w=np.mean([x["basin_sim"]>=x["recent_sim"] for x in w])
    print(mm,"AUC error",round(a_err,3),"recent_sim only",round(a_rs,3),"basin_sim only",round(a_bs,3),"| basin-arm dominates: spont",round(dom_sp,3),"world",round(dom_w,3),"| mean rs w/sp",round(np.mean(f('recent_sim',w)),3),round(np.mean(f('recent_sim',sp)),3),"bs w/sp",round(np.mean(f('basin_sim',w)),3),round(np.mean(f('basin_sim',sp)),3))
print("\n== AUC(any OTHER kind vs spontaneous) per kind, Sep-Nov pooled")
sp=[r for r in S if r["seed_kind"]=="spontaneous" and r["m"]>="2026-09"]
for k in ["percept","frontier","reading","letter","world"]:
    o=[r for r in S if r["seed_kind"]==k and r["m"]>="2026-09"]
    print(k,len(o),"AUC",round(auc([r["error"] for r in o],[r["error"] for r in sp]),3))
print("\n== text overlap proxy among consecutive spontaneous thoughts (word-set Jaccard on 120-char logged text), by month")
def ws(t): return set(re.findall(r"[a-z']{4,}",(t or "").lower()))
for mm in months:
    t=[r for r in S if r["m"]==mm]; js=[]
    for a,b in zip(t,t[1:]):
        A,B=ws(a["thought"]),ws(b["thought"])
        if A and B: js.append(len(A&B)/len(A|B))
    print(mm,"mean consecutive jaccard",round(float(np.mean(js)),4),"n",len(js))
print("\n== assimilated OTHER share (OTHER with error<0.45) by month and by kind")
for mm in months:
    o=[r for r in S if r["m"]==mm and r["authorship"]=="OTHER"]; 
    print(mm,"OTHER<tau",round(np.mean([r["error"]<0.45 for r in o]),3),"SELF>=tau",round(np.mean([r["error"]>=0.45 for r in S if r["m"]==mm and r["authorship"]=="SELF"]),3))
print("\n== recall/dream/trial/guidance/concern/imagination rows in log:", sum(1 for r in rows if r.get("seed_kind") in ("recall","dream","trial","guidance","concern","imagination")))
