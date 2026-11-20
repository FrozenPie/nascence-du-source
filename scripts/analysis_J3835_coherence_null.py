import re,sqlite3,sys,time,random,hashlib
sys.path.insert(0,'C:/Nascence')
import numpy as np
c=sqlite3.connect('file:C:/Nascence/data/memory/nascence.db?mode=ro',uri=True)
now=time.time()
fr=c.execute("select fragment_id,content,timestamp from memory_fragments where origin in ('inner_thought','subconscious_synthesis') and timestamp>? order by timestamp desc limit 3000",(now-14*86400,)).fetchall()
th=[]
for f in fr:
    t=" ".join((f[1] or '').split())
    if re.search(r"\b(I|my|myself|me|self|river|mind|made|built|becoming|am)\b",t,re.I): th.append(t)
print('thoughts',len(th))
from core.memory.store import _embed_batch
# per-thought sentences, embed once
per=[]
allS=[]
for t in th:
    ss=[]
    for s in re.split(r'(?<=[.!?])\s+',t):
        s=s.strip()
        if 40<=len(s)<=240 and re.search(r"\b(I|my|me|myself)\b",s): ss.append(len(allS)); allS.append(s)
    per.append(ss)
E=np.array(_embed_batch(allS))
print('sentences',len(allS))
random.seed(7)
idx=[i for i,p in enumerate(per) if p]
def medoid(sset):
    seen=set();keep=[]
    for j in sset:
        k=hashlib.sha1(allS[j].lower().encode()).hexdigest()
        if k not in seen: seen.add(k);keep.append(j)
    M=E[keep]@E[keep].T; n=len(keep)
    ms=(M.sum(1)-1)/(n-1); return float(ms.max()),n
res=[]
for _ in range(300):
    pick=random.sample(idx,15)
    res.append(medoid([j for i in pick for j in per[i]])[0])
res=np.array(res)
print('null medoid score: p50 %.3f p90 %.3f p95 %.3f p99 %.3f max %.3f'%tuple(np.percentile(res,[50,90,95,99,100])))
# temporal-window null: 15 consecutive thoughts (like a probation's newest-15)
res2=[]
for s in range(0,len(idx)-15,5):
    pick=idx[s:s+15]; res2.append(medoid([j for i in pick for j in per[i]])[0])
res2=np.array(res2); print('consecutive-15 null: n=%d p50 %.3f p90 %.3f p95 %.3f max %.3f'%(len(res2),*np.percentile(res2,[50,90,95,100])))
print('10-30 solidify medoid 0.442 -> percentile in random null %.1f, in consecutive null %.1f'%((res<0.442).mean()*100,(res2<0.442).mean()*100))
