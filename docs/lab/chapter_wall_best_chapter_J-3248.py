"""J-3248 (D-0637): best chapter by cosine per query, and whether its members beat the gist.

READ-ONLY. Opens data/memory/nascence.db with mode=ro and reads data/training/recall.jsonl; writes only to $J3248_OUT
(default: the system temp dir). Never imports core, never starts Du. Run order: chapter_wall_replay_J-3248.py first
(SELF_CUT=0.95 python ...), then the other two, which read its output file. Report: docs/reviews/J-3248_chaptered_memory_recall_review.md
"""
import os, sys, json, random, sqlite3, collections, statistics as st
os.environ["HF_HUB_OFFLINE"]="1"
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
import tempfile
SP=os.environ.get("J3248_OUT") or tempfile.gettempdir()
c=sqlite3.connect("file:C:/Nascence/data/memory/nascence.db?mode=ro",uri=True); c.row_factory=sqlite3.Row
rows=c.execute("select fragment_id,origin,cold,chapter_id,embedding from memory_fragments where embedding is not null and (origin='chapter' or (chapter_id is not null and chapter_id!=''))").fetchall()
ch=[r for r in rows if r["origin"]=="chapter"]
cidx={r["fragment_id"]:i for i,r in enumerate(ch)}
CM=np.stack([np.frombuffer(r["embedding"],dtype=np.float32) for r in ch])
toplevel=np.array([not r["chapter_id"] for r in ch])
members=collections.defaultdict(list)
for r in rows:
    if r["origin"]!="chapter" and r["chapter_id"] in cidx: members[r["chapter_id"]].append(r)
MM={k:np.stack([np.frombuffer(m["embedding"],dtype=np.float32) for m in v]) for k,v in members.items()}
print("chapters",len(ch),"toplevel (in live pool)",int(toplevel.sum()),"chapters with direct raw members",len(MM),"median members",st.median(len(v) for v in members.values()))
rec=[json.loads(l) for l in open("C:/Nascence/data/training/recall.jsonl",encoding="utf-8") if l.strip()]
def pick(sub,n,seed): random.Random(seed).shuffle(sub); return sub[:n]
good=[r for r in rec if len((r.get("raw_input") or "").strip())>=20]
recent=[r for r in good if float(r["ts"])>=1792800000]
older=[r for r in good if float(r["ts"])<1792800000 and float(r["ts"])>=1788000000]
def strat(pool,n):
    a=[r for r in pool if r.get("input_type")=="internal"];b=[r for r in pool if r.get("input_type")!="internal"]
    nb=min(len(b),n*3//10); return pick(b,nb,1)+pick(a,n-nb,2)
qs=strat(recent,100)+strat(older,100)
from sentence_transformers import SentenceTransformer
model=SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",device="cpu")
QV=model.encode([q["raw_input"].strip() for q in qs],normalize_embeddings=True,show_progress_bar=False).astype(np.float32)
S=QV@CM.T
top_i=S.argmax(1)
print("queries",len(qs))
cnt=collections.Counter(ch[i]["fragment_id"][:8] for i in top_i); print("best-chapter-by-cosine magnet distribution (top 6):",cnt.most_common(6),"distinct",len(cnt))
bs=S.max(1); print("best chapter cosine: median %.3f, p90 %.3f, share>=0.25: %.2f, >=0.40: %.2f, >=0.50: %.2f"%(np.median(bs),np.percentile(bs,90),(bs>=.25).mean(),(bs>=.4).mean(),(bs>=.5).mean()))
# toplevel only
St=np.where(toplevel[None,:],S,-9); bt=St.max(1); print("toplevel-only best cos median %.3f share>=0.40 %.2f"%(np.median(bt),(bt>=.4).mean()))
# members of best chapter: top member cosine vs gist cosine
gain=[];nm=[]
for qi in range(len(qs)):
    k=ch[top_i[qi]]["fragment_id"]
    if k in MM:
        ms=MM[k]@QV[qi]; gain.append(float(ms.max()-S[qi,top_i[qi]])); nm.append(len(ms))
print("queries whose best chapter has raw members:",len(gain),"; member best cos minus gist cos: median %.3f, share members better: %.2f, share >=+0.10: %.2f"%(np.median(gain),(np.array(gain)>0).mean(),(np.array(gain)>=.10).mean()))
# aggregate across ALL members of top-3 chapters for any member >= 0.5 cosine
hit5=0
for qi in range(len(qs)):
    for j in np.argsort(-S[qi])[:3]:
        k=ch[j]["fragment_id"]
        if k in MM and (MM[k]@QV[qi]).max()>=0.5: hit5+=1;break
print("queries where a member of a top-3 (by gist cosine) chapter has cosine>=0.5 to the query:",hit5,"/",len(qs))
# any chaptered member at all >=0.5 vs best live-pool item? from earlier out: A top1 cos
out=json.load(open(SP+"/replay_J-3248_out_cut0.95_rec0.json",encoding="utf-8"))
a1=np.array([o["A"]["top1_cos"] for o in out]); print("live-pool best cosine median %.3f; share>=0.5: %.2f"%(np.median(a1),(a1>=.5).mean()))
