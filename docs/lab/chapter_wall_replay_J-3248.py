"""J-3248 (D-0637): 200 real recall queries, live pool vs pool with the chapter wall removed vs both walls removed (env SELF_CUT, RECENCY_OFF).

READ-ONLY. Opens data/memory/nascence.db with mode=ro and reads data/training/recall.jsonl; writes only to $J3248_OUT
(default: the system temp dir). Never imports core, never starts Du. Run order: chapter_wall_replay_J-3248.py first
(SELF_CUT=0.95 python ...), then the other two, which read its output file. Report: docs/reviews/J-3248_chaptered_memory_recall_review.md
"""
import os, sys, json, time, random, re, sqlite3, collections
os.environ["HF_HUB_OFFLINE"]="1"
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
import tempfile
SP=os.environ.get("J3248_OUT") or tempfile.gettempdir()
DB="file:C:/Nascence/data/memory/nascence.db?mode=ro"
c=sqlite3.connect(DB,uri=True); c.row_factory=sqlite3.Row
t0=time.time()
rows=c.execute("select rowid rid,fragment_id,layer,timestamp,origin,cold,temp,chapter_id,embedding from memory_fragments where embedding is not null").fetchall()
N=len(rows); print("loaded",N,time.time()-t0)
M=np.empty((N,384),dtype=np.float32)
fid=[];layer=[];ts=np.empty(N);origin=[];cold=np.zeros(N,bool);temp=[];chap=[]
for i,r in enumerate(rows):
    M[i]=np.frombuffer(r["embedding"],dtype=np.float32)
    fid.append(r["fragment_id"]);layer.append(r["layer"]);ts[i]=r["timestamp"];origin.append(r["origin"]);cold[i]=bool(r["cold"]);temp.append(r["temp"]);chap.append(r["chapter_id"] or "")
del rows
layer=np.array(layer);origin=np.array(origin);temp=np.array(temp);chap=np.array(chap)
fid_idx={f:i for i,f in enumerate(fid)}
# parent class of each chaptered row
porigin=np.array([origin[fid_idx[ch]] if ch and ch in fid_idx else ("" if not ch else "missing") for ch in chap])
cls=np.where(chap=="","unwalled",np.where(porigin=="chapter","period_chapter",np.where(np.isin(porigin,["understanding","essay"]),"gist_filed","dedup_or_other")))
base_ok=(~cold)&(temp!="hidden")&(origin!="system_note")&(layer!="dormant")
poolA=base_ok&(chap=="")
poolB=base_ok                    # chapter wall removed, cold wall kept
poolC=(temp!="hidden")&(origin!="system_note")&(layer!="dormant")  # both walls removed (upper bound)
print("poolA",poolA.sum(),"poolB",poolB.sum(),"poolC",poolC.sum())
# queries
rec=[json.loads(l) for l in open("C:/Nascence/data/training/recall.jsonl",encoding="utf-8") if l.strip()]
def pick(sub,n,seed):
    random.Random(seed).shuffle(sub); return sub[:n]
good=[r for r in rec if len((r.get("raw_input") or "").strip())>=20]
recent=[r for r in good if float(r["ts"])>=1792800000]
older=[r for r in good if float(r["ts"])<1792800000 and float(r["ts"])>=1788000000]
print("good",len(good),"recent",len(recent),"older",len(older))
def strat(pool,n):
    a=[r for r in pool if r.get("input_type")=="internal"];b=[r for r in pool if r.get("input_type")!="internal"]
    nb=min(len(b),n*3//10); return pick(b,nb,1)+pick(a,n-nb,2)
setR=strat(recent,100); setO=strat(older,100)
from sentence_transformers import SentenceTransformer
model=SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",device="cpu")
STOP=set("that this with from have what your about which their there would could should these those where when while been being into than then they them also just like more some such only over very much many how why who whom whose does did done each other will can may might".split())
def toks(s): return set(w for w in re.findall(r"[a-z]{4,}",(s or "").lower()) if w not in STOP)
# contents fetched lazily
def content(i):
    return c.execute("select content from memory_fragments where fragment_id=?",(fid[i],)).fetchone()[0] or ""
SELF_CUT=float(os.environ.get('SELF_CUT','1.0'))
TIER={"archive":2,"semantic":3,"episodic":4}
now=time.time()
age=(now-ts)/86400.0
recency=np.ones_like(age) if os.environ.get('RECENCY_OFF') else 1.0+0.2*np.maximum(0.0,1.0-age/7.0)
def select(sims,pool,limit=8):
    sc=np.where(pool,sims*recency,-9.0)
    chosen=[]
    for tier,k in TIER.items():
        m=pool&(layer==tier)
        idx=np.where(m)[0]
        if len(idx)==0: continue
        top=idx[np.argsort(-sc[idx])[:k+4]]
        chosen.append((tier,list(top)))
    sel=[];overflow=[]
    for tier,lst in chosen:
        k=TIER[tier]; sel+=lst[:k]; overflow+=lst[k:]
    if len(sel)<limit:
        overflow.sort(key=lambda i:-sc[i]); sel+=overflow[:limit-len(sel)]
    sel=sorted(sel,key=lambda i:-sc[i])[:limit]
    return sel
out=[]
def run(qset,label):
    for q in qset:
        text=q["raw_input"].strip()
        qv=model.encode(text,normalize_embeddings=True,show_progress_bar=False).astype(np.float32)
        sims=M@qv
        if SELF_CUT<1.0: sims=np.where(sims>=SELF_CUT,-1.0,sims)   # drop the query's own stored echo (self-match) from every arm
        qt=toks(text)
        rowo={"set":label,"ts":q["ts"],"input_type":q.get("input_type"),"q":text[:160]}
        for nm,pool in (("A",poolA),("B",poolB),("C",poolC)):
            sel=select(sims,pool)
            rowo[nm]={"ids":[fid[i] for i in sel],"cls":[str(cls[i]) for i in sel],"sims":[float(sims[i]) for i in sel],
                      "origin":[str(origin[i]) for i in sel]}
            # pure top-1 by cosine
            m=np.where(pool,sims,-9.0); j=int(np.argmax(m)); rowo[nm]["top1_cos_id"]=fid[j]; rowo[nm]["top1_cos"]=float(sims[j]); rowo[nm]["top1_cos_cls"]=str(cls[j])
            rowo[nm]["_sel"]=sel
        # entrants in B not in A
        a=set(rowo["A"]["_sel"]); ent=[i for i in rowo["B"]["_sel"] if i not in a]
        rowo["B_entrants"]=[{"id":fid[i],"cls":str(cls[i]),"origin":str(origin[i]),"sim":float(sims[i]),
            "max_cos_to_A":float(max(float(M[i]@M[j]) for j in rowo["A"]["_sel"])),
            "lex":len(toks(content(i))&qt)/max(1,len(qt)),"parent":chap[i]} for i in ent]
        # lexical overlap of A's items for baseline
        rowo["A_lex"]=[len(toks(content(i))&qt)/max(1,len(qt)) for i in rowo["A"]["_sel"]]
        # parent chapter surfaced in A?
        aset=set(fid[i] for i in rowo["A"]["_sel"])
        for e in rowo["B_entrants"]: e["parent_in_A"]=e["parent"] in aset
        # all chaptered rows scoring above A's 8th (any, not just those that fit slots)
        a8=min(float(sims[i]*recency[i]) for i in rowo["A"]["_sel"])
        cand=np.where(poolB&(chap!=""))[0]; sc=sims[cand]*recency[cand]
        rowo["n_chap_over_A8"]=int((sc>a8).sum())
        rowo["n_chap_over_A8_by_cls"]=dict(collections.Counter(str(cls[i]) for i in cand[sc>a8]))
        for nm in "ABC": rowo[nm].pop("_sel")
        out.append(rowo)
run(setR,"recent"); run(setO,"older")
json.dump(out,open(os.path.join(SP,"replay_J-3248_out_cut%s_rec%s.json"%(os.environ.get("SELF_CUT","1.0"),os.environ.get("RECENCY_OFF","0"))),"w",encoding="utf-8"),ensure_ascii=False)
print("done",time.time()-t0)
