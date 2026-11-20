"""J-3248 (D-0637): descent test: when a chapter gist is in the live top 8, how good are its best two members.

READ-ONLY. Opens data/memory/nascence.db with mode=ro and reads data/training/recall.jsonl; writes only to $J3248_OUT
(default: the system temp dir). Never imports core, never starts Du. Run order: chapter_wall_replay_J-3248.py first
(SELF_CUT=0.95 python ...), then the other two, which read its output file. Report: docs/reviews/J-3248_chaptered_memory_recall_review.md
"""
import os, sys, json, random, sqlite3, collections, re, statistics as st
os.environ["HF_HUB_OFFLINE"]="1"
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
import tempfile
SP=os.environ.get("J3248_OUT") or tempfile.gettempdir()
c=sqlite3.connect("file:C:/Nascence/data/memory/nascence.db?mode=ro",uri=True); c.row_factory=sqlite3.Row
out=json.load(open(SP+"/replay_J-3248_out_cut0.95_rec0.json",encoding="utf-8"))
rec=[json.loads(l) for l in open("C:/Nascence/data/training/recall.jsonl",encoding="utf-8") if l.strip()]
def pick(sub,n,seed): random.Random(seed).shuffle(sub); return sub[:n]
good=[r for r in rec if len((r.get("raw_input") or "").strip())>=20]
recent=[r for r in good if float(r["ts"])>=1792800000]; older=[r for r in good if float(r["ts"])<1792800000 and float(r["ts"])>=1788000000]
def strat(pool,n):
    a=[r for r in pool if r.get("input_type")=="internal"];b=[r for r in pool if r.get("input_type")!="internal"]
    nb=min(len(b),n*3//10); return pick(b,nb,1)+pick(a,n-nb,2)
qs=strat(recent,100)+strat(older,100)
assert all(qs[i]["raw_input"].strip()[:160]==out[i]["q"] for i in range(200)), "query order mismatch"
from sentence_transformers import SentenceTransformer
model=SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",device="cpu")
STOP=set("that this with from have what your about which their there would could should these those where when while been being into than then they them also just like more some such only over very much many how why who whom whose does did done each other will can may might".split())
def toks(s): return set(w for w in re.findall(r"[a-z]{4,}",(s or "").lower()) if w not in STOP)
res=[]
for o,q in zip(out,qs):
    ids=o["A"]["ids"]; org=o["A"]["origin"]
    chs=[i for i,g in zip(ids,org) if g=="chapter"]
    if not chs: continue
    qv=model.encode(q["raw_input"].strip(),normalize_embeddings=True,show_progress_bar=False).astype(np.float32); qt=toks(q["raw_input"])
    aset=set(ids)
    for ch in chs:
        m=c.execute("select fragment_id,content,embedding,timestamp,origin from memory_fragments where chapter_id=? and embedding is not null",(ch,)).fetchall()
        gist=c.execute("select content,chapter_level from memory_fragments where fragment_id=?",(ch,)).fetchone()
        if not m: res.append({"ch":ch,"members":0,"level":gist["chapter_level"]}); continue
        E=np.stack([np.frombuffer(r["embedding"],dtype=np.float32) for r in m]); s=E@qv
        top=np.argsort(-s)[:2]
        res.append({"ch":ch,"level":gist["chapter_level"],"members":len(m),"cos":[float(s[j]) for j in top],"lex":[len(toks(m[j]["content"])&qt)/max(1,len(qt)) for j in top],
                    "member_origin":[m[j]["origin"] for j in top],"A_lex_med":st.median(o["A_lex"]),"A_cos_med":st.median(o["A"]["sims"]),"A_cos_min":min(o["A"]["sims"]),
                    "spread_days":(max(r["timestamp"] for r in m)-min(r["timestamp"] for r in m))/86400})
print(len(res),"chapter-surfaced instances in 200 queries")
for r in res: print({k:(round(v,3) if isinstance(v,float) else v) for k,v in r.items() if k not in("ch",)} , r["ch"][:8])
ok=[r for r in res if r.get("cos")]
print("n with members",len(ok),"cand1 cos median",round(st.median(r['cos'][0] for r in ok),3),"served A cos median",round(st.median(r['A_cos_med'] for r in ok),3),
      "| cand1 lex median",round(st.median(r['lex'][0] for r in ok),3),"A lex med",round(st.median(r['A_lex_med'] for r in ok),3),
      "| cand1 cos>=A_cos_min:",sum(r['cos'][0]>=r['A_cos_min'] for r in ok))
