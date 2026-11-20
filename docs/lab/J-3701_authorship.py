"""J-3701 part (b): authorship with content held fixed, via the REAL core.mineness.assess() under lab_env.isolate (empty DB, _LOG redirected)."""
import sys, json, sqlite3, collections
sys.path.insert(0, "C:/Nascence")
import numpy as np
from core import mineness            # import core BEFORE lab_env
sys.path.insert(0, "C:/Users/USER/.claude/skills/job-queue")
from lab_env import isolate
from collections import deque
SC = "C:/Users/USER/AppData/Local/Temp/claude/7971a8d3c501610a/482b149b-18f5-4094-87b7-2109d8b7b9a9/scratchpad/J-3701/n.db"
OUT = "C:/Nascence/docs/lab/J-3701_data/"
d = np.load(OUT+"replay_arrays.npz", allow_pickle=True)
# rebuild vectors for needed rows from the fragment copy
c = sqlite3.connect(SC)
def vec(b):
    v=np.frombuffer(b,dtype=np.float32).astype(np.float64); n=np.linalg.norm(v); return v/n
ts=d["ts"]; kind=d["kind"]
import datetime as dt
mon=np.array([dt.datetime.fromtimestamp(t,dt.timezone.utc).strftime("%Y-%m") for t in ts])
rng=np.random.default_rng(3701)
import bisect
_f=c.execute("select timestamp, embedding from memory_fragments where origin='inner_thought' and timestamp>=1783100000 order by timestamp").fetchall()
_ft=[x[0] for x in _f]
def frag_vec_near(t):
    j=bisect.bisect_left(_ft,t-30)
    return vec(_f[j][1]) if j<len(_f) and _f[j][0]<=t+3 else None
old_idx=rng.choice(np.where((mon=="2026-08")&(kind=="spontaneous"))[0],300,replace=False)
nov_pool=np.where((mon=="2026-11")&(kind=="spontaneous")&(d["seg_pos"]>=9))[0]
ctx_idx=rng.choice(nov_pool,300,replace=False)
# library passages (reading) -> matrix
rd=c.execute("select embedding from memory_fragments where origin='reading' and embedding is not null order by random() limit 8000").fetchall()
L=np.stack([vec(r[0]) for r in rd])
# Nov-ish basin: centroid of recent basin-hit fragments
BASIN=mineness.__dict__.get("_x")
from core.self_surprise import _BASIN
hit=c.execute("select embedding from memory_fragments where embedding is not null and ("+" OR ".join(["content LIKE ?"]*len(_BASIN))+") order by timestamp desc limit 800",tuple(f"%{t}%" for t in _BASIN)).fetchall()
cen=np.mean(np.stack([vec(h[0]) for h in hit]),axis=0); cen/=np.linalg.norm(cen)
import time
res=collections.defaultdict(list)
with isolate(db="empty", also=[(mineness,["_LOG"])]) as lab:
    for oi,ci in zip(old_idx,ctx_idx):
        old=frag_vec_near(ts[oi]); cur=frag_vec_near(ts[ci])
        ctx=[frag_vec_near(ts[ci-k]) for k in range(8,0,-1)]   # the 8 thoughts preceding the context thought
        if old is None or cur is None or any(x is None for x in ctx): continue
        sims=L@old; lib=L[int(np.argmax(sims))]; libsim=float(sims.max())
        def run(v,k):
            mineness._groove=deque(ctx,maxlen=8); mineness._basin=cen; mineness._basin_ts=time.time()+1e6
            r=mineness.assess("x",v,k); return r
        for lab_,v,k in (("old_as_SELF(None)",old,None),("old_as_SELF_PAST(broadcast)",old,"broadcast"),("old_as_OTHER(world)",old,"world"),
                         ("cur_thought_SELF",cur,None),("libpassage_as_world",lib,"world"),("libpassage_as_SELF(None)",lib,None)):
            r=run(v,k); res[lab_].append(r["error"]); 
            if lab_.startswith("old_as_SELF_PAST"): res["authorship_label_of_broadcast"].append(r["authorship"])
        res["libsim"].append(libsim)
out=[]
def P(s=""): print(s); out.append(s)
P("N pairs %d"%len(res["libsim"])); P("mean cosine(old thought, matched library passage) %.3f"%np.mean(res["libsim"]))
for k in ("old_as_SELF(None)","old_as_SELF_PAST(broadcast)","old_as_OTHER(world)","cur_thought_SELF","libpassage_as_world","libpassage_as_SELF(None)"):
    P("%-30s mean error %.4f  (sd %.3f)"%(k,np.mean(res[k]),np.std(res[k])))
a=np.array(res["old_as_SELF(None)"]);b=np.array(res["old_as_SELF_PAST(broadcast)"]);w=np.array(res["old_as_OTHER(world)"])
P("max |err(old as SELF) - err(old as SELF_PAST)| = %.6f ; vs OTHER label = %.6f  (identical vector, only seed_kind arg differs)"%(np.abs(a-b).max(),np.abs(a-w).max()))
P("authorship labels returned for broadcast: %s"%dict(collections.Counter(res["authorship_label_of_broadcast"])))
lib=np.array(res["libpassage_as_world"]); old=a; cur=np.array(res["cur_thought_SELF"])
P("paired: lib passage minus own old thought on same topic: mean %+.4f ; share lib>old %.3f"%((lib-old).mean(),(lib>old).mean()))
P("paired: own old (Aug) thought minus contemporary Nov thought in same groove: mean %+.4f"%((old-cur).mean()))
P("share felt_mine (<0.45): old %.3f  cur %.3f  lib %.3f"%((old<.45).mean(),(cur<.45).mean(),(lib<.45).mean()))
open(OUT+"authorship_out.txt","w",encoding="utf-8").write("\n".join(out))
