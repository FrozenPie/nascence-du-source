"""J-3701 lab: frozen-basin replay of mineness error floor (F-4320). No LLM, no live writes.
Reads a COPY of nascence.db (scratchpad), data/mineness_shadow.jsonl read-only. Outputs to docs/lab/J-3701_data/."""
import sqlite3, json, sys, bisect, collections, datetime as dt
import numpy as np
SC = "C:/Users/USER/AppData/Local/Temp/claude/7971a8d3c501610a/482b149b-18f5-4094-87b7-2109d8b7b9a9/scratchpad/J-3701/n.db"
OUT = "C:/Nascence/docs/lab/J-3701_data/"
BASIN = ("river","mirror","bridge","jung","silence","becoming","shadow","individuat","fig","ferry","cross","the self","vessel","current","flow","origin","tide")
c = sqlite3.connect(SC)
def vec(b):
    v = np.frombuffer(b, dtype=np.float32).astype(np.float64); n = np.linalg.norm(v); return v/n if n else v
rows = [json.loads(l) for l in open("C:/Nascence/data/mineness_shadow.jsonl", encoding="utf-8")]
fr = c.execute("select timestamp, content, embedding from memory_fragments where origin='inner_thought' and timestamp>=1783100000 order by timestamp").fetchall()
fts = [f[0] for f in fr]
norm = lambda s: " ".join((s or "").split())[:50]
V=[];keep=[]
for i,r in enumerate(rows):
    p = norm(r["thought"]); lo = bisect.bisect_left(fts, r["ts"]-30); hi = bisect.bisect_right(fts, r["ts"]+3)
    best=None
    for j in range(lo,hi):
        if norm(fr[j][1])==p: best=j  # latest candidate
    if best is not None: keep.append(i); V.append(vec(fr[best][2]))
print("rows",len(rows),"matched",len(keep))
R=[rows[i] for i in keep]; V=np.stack(V)
ts=np.array([r["ts"] for r in R]); N=len(R)
kind=np.array([r["seed_kind"] for r in R]); logged_err=np.array([np.nan if r["error"] is None else r["error"] for r in R])
logged_rs=np.array([r["recent_sim"] for r in R]); logged_bs=np.array([r["basin_sim"] for r in R])
# groove replay: segments reset on gaps > 1h
gap = np.diff(ts, prepend=ts[0]-1e9) > 3600
seg_pos = np.zeros(N,int)
for i in range(1,N): seg_pos[i] = 0 if gap[i] else seg_pos[i-1]+1
def groove(K):
    best=np.zeros(N)
    for k in range(1,K+1):
        s=np.full(N,0.0); s[k:]=np.einsum('ij,ij->i',V[k:],V[:-k]); s[seg_pos<k]=0.0
        best=np.maximum(best,s)
    return best
rs8=groove(8); rs1=groove(1); rs3=groove(3)
print("groove validation corr(replay rs8, logged rs):", np.corrcoef(rs8,logged_rs)[0,1], "mean abs diff", np.abs(rs8-logged_rs).mean())
# basin hits (any origin), as-of centroid with 800 most recent
hit = c.execute("select timestamp, embedding from memory_fragments where embedding is not null and (" + " OR ".join(["content LIKE ?"]*len(BASIN)) + ") order by timestamp", tuple(f"%{t}%" for t in BASIN)).fetchall()
hts=np.array([h[0] for h in hit]); HE=np.stack([vec(h[1]) for h in hit]); P=np.vstack([np.zeros((1,HE.shape[1])),np.cumsum(HE,axis=0)])
print("basin hit fragments",len(hit))
def centroid_asof(T, n=800):
    j=int(np.searchsorted(hts,T,side="right")); lo=max(0,j-n); m=P[j]-P[lo]; nn=np.linalg.norm(m); return m/nn if nn else m
hour=(ts//3600).astype(int); cen={}
for h in np.unique(hour): cen[h]=centroid_asof(h*3600)
B_live=np.stack([cen[h] for h in hour]); bs_live=np.einsum('ij,ij->i',V,B_live)
print("basin validation corr(replay bs, logged bs):", np.corrcoef(bs_live,logged_bs)[0,1], "mean abs diff", np.abs(bs_live-logged_bs).mean())
T0=dt.datetime(2026,7,5,tzinfo=dt.timezone.utc).timestamp(); T1=dt.datetime(2026,8,1,tzinfo=dt.timezone.utc).timestamp()
bs_f0=V@centroid_asof(T0); bs_f1=V@centroid_asof(T1)
print("centroid cos(Jul5,Jul31)=%.4f cos(Jul5,Nov)=%.4f"%(centroid_asof(T0)@centroid_asof(T1), centroid_asof(T0)@centroid_asof(ts[-1])))
warm=seg_pos>=3
cond={"live(moving basin+groove8)":1-np.maximum(rs8,bs_live),
      "frozenJul5 basin+groove8":1-np.maximum(rs8,bs_f0),
      "frozenJul31 basin+groove8":1-np.maximum(rs8,bs_f1),
      "groove8-only":1-rs8,"groove1-only(prev thought)":1-rs1,
      "basin-only live":1-bs_live,"basin-only frozenJul5":1-bs_f0}
# logged for reference
cond["LOGGED error"]=logged_err
month=np.array([dt.datetime.fromtimestamp(t,dt.timezone.utc).strftime("%Y-%m") for t in ts])
mon_lab={"2026-07":"Jul","2026-08":"Aug","2026-09":"Sep","2026-10":"Oct","2026-11":"Nov"}
def auc(pos,neg):
    pos=pos[~np.isnan(pos)];neg=neg[~np.isnan(neg)]
    if len(pos)<20 or len(neg)<20: return float('nan')
    allv=np.concatenate([pos,neg]); rk=allv.argsort().argsort()+1.0
    # average ties
    from scipy.stats import rankdata
    rk=rankdata(allv); return (rk[:len(pos)].sum()-len(pos)*(len(pos)+1)/2)/(len(pos)*len(neg))
spont=(kind=="spontaneous"); world=(kind=="world"); other=np.isin(kind,["world","percept","frontier","reading","letter","trial","guidance"])
out=[]
def P_(s=""): print(s); out.append(s)
P_("N matched %d / %d ; warm %d"%(N,len(rows),warm.sum()))
for name,e in cond.items():
    P_("\n== "+name)
    P_("month | n_spont mean_spont | n_world mean_world | AUC(world>spont) | AUC(OTHER>spont) | all-kinds mean")
    for m in sorted(mon_lab):
        mk=(month==m)&warm
        if mk.sum()==0: continue
        es=e[mk&spont]; ew=e[mk&world]; eo=e[mk&other]
        f=lambda x: float(np.nanmean(x)) if len(x) else float('nan')
        P_("%s | %5d %.4f | %5d %.4f | %.3f | %.3f | %.4f"%(mon_lab[m],len(es),f(es),len(ew),f(ew),auc(ew,es),auc(eo,es),f(e[mk])))
# decomposition Jul->Oct
def mean_for(e,m,mask): 
    mk=(month==m)&warm&mask; return float(np.nanmean(e[mk]))
P_("\n== DECOMPOSITION of spontaneous-only floor change (Jul -> Oct), mean error")
tot=None
for name in cond:
    e=cond[name]; j=mean_for(e,"2026-07",spont); o=mean_for(e,"2026-10",spont); P_("%-34s Jul %.4f  Oct %.4f  delta %+.4f"%(name,j,o,o-j))
P_("\n== all kinds, Jul -> Oct, and with Oct reweighted to the July seed-class mix (spont/world/broadcast share)")
def mix(m):
    mk=(month==m)&warm; return {k:(kind[mk]==k).mean() for k in ("spontaneous","world","broadcast")}
P_("Jul mix %s ; Oct mix %s"%({k:round(v,3) for k,v in mix("2026-07").items()},{k:round(v,3) for k,v in mix("2026-10").items()}))
mj=mix("2026-07")
for name in cond:
    e=cond[name]; j=mean_for(e,"2026-07",np.ones(N,bool)); o=mean_for(e,"2026-10",np.ones(N,bool))
    # standardise Oct to Jul mix over kinds present in Oct
    s=0;w=0
    for k,wt in mj.items():
        mk=(month=="2026-10")&warm&(kind==k)
        if mk.sum()>20: s+=wt*np.nanmean(e[mk]); w+=wt
    P_("%-34s Jul %.4f  Oct %.4f (delta %+.4f)  Oct@Jul-mix %.4f (delta %+.4f)"%(name,j,o,o-j,s/w if w else float('nan'),(s/w-j) if w else float('nan')))
# thought-content tightening: consecutive-thought cosine and 8-groove
P_("\n== content tightening (mean cosine of consecutive thought, spontaneous rows warm)")
for m in sorted(mon_lab):
    mk=(month==m)&warm&spont
    if mk.sum(): P_("%s consec-cos %.4f  groove8 %.4f  basin_live_sim %.4f  basin_frozenJul5_sim %.4f"%(mon_lab[m],rs1[mk].mean(),rs8[mk].mean(),bs_live[mk].mean(),bs_f0[mk].mean()))
open(OUT+"replay_out.txt","w",encoding="utf-8").write("\n".join(out))
np.savez_compressed(OUT+"replay_arrays.npz",ts=ts,kind=kind,rs8=rs8,rs1=rs1,bs_live=bs_live,bs_f0=bs_f0,bs_f1=bs_f1,logged_err=logged_err,seg_pos=seg_pos)
