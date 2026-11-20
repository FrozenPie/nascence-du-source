import json,re,sqlite3,sys,hashlib,time
sys.path.insert(0,'C:/Nascence')
rows=[json.loads(l) for l in open('C:/Nascence/data/logs/provisional_identity.jsonl',encoding='utf-8') if l.strip()]
sol=[r for r in rows if r['event']=='solidify'][-1]
opens=[r for r in rows if r['event']=='open' and r['ts']<sol['ts'] and r['theme']==sol['theme']]
op=opens[-1]
print('open',time.strftime('%m-%d %H:%M',time.localtime(op['ts'])),'solidify',time.strftime('%m-%d %H:%M',time.localtime(sol['ts'])))
c=sqlite3.connect('file:C:/Nascence/data/memory/nascence.db?mode=ro',uri=True)
fr=c.execute("select fragment_id,content,timestamp,embedding from memory_fragments where origin in ('inner_thought','subconscious_synthesis') and timestamp>=? and timestamp<=? order by timestamp desc limit 60",(op['ts'],sol['ts'])).fetchall()
print('fragments in window',len(fr))
lived=[]
for f in fr:
    t=" ".join((f[1] or '').split())
    if re.search(r"\b(I|my|myself|me|self|river|mind|made|built|becoming|am)\b",t,re.I): lived.append((f[0],f[2],t))
    if len(lived)>=15: break
print('lived',len(lived))
from core.memory.store import _embed_batch
sents=[]
for fid,ts,t in lived:
    for s in re.split(r'(?<=[.!?])\s+',t):
        s=s.strip()
        if 40<=len(s)<=240 and re.search(r"\b(I|my|me|myself)\b",s): sents.append((fid,s))
seen=set();S=[]
for fid,s in sents:
    k=hashlib.sha1(s.lower().encode()).hexdigest()
    if k in seen: continue
    seen.add(k);S.append((fid,s))
print('distinct candidate sentences',len(S))
import numpy as np
E=np.array(_embed_batch([s for _,s in S]))
sim=E@E.T
n=len(S)
ms=(sim.sum(1)-1)/(n-1)
order=np.argsort(-ms)
for i in order[:5]: print(round(float(ms[i]),3),S[i][1][:200])
print('median mean-cos',round(float(np.median(ms)),3),'lowest',round(float(ms.min()),3))
self_e=_embed_batch([sol['self_image']])[0]
j=order[0]; print('cos(medoid, authored paragraph)=%.3f'%float(E[j]@self_e)); 
print('neg flag on top5:',[bool(re.search(r'\bno longer\b|\bnot\b.{0,60}\bbut\b',S[i][1],re.I)) for i in order[:5]])
print('authored self starts:',sol['self_image'][:90])
