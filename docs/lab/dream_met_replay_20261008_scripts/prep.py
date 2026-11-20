# J-1964 prep: read-only. Loads waking embeddings from a BACKUP db copy (immutable ro), embeds arc tension texts + dream tails.
import sqlite3, json, numpy as np, datetime, time, sys
from sentence_transformers import SentenceTransformer
OUT='.'
c=sqlite3.connect('file:C:/Nascence/data/backups/nascence_20261008_090235.db?mode=ro&immutable=1',uri=True)
rows=c.execute("select fragment_id,origin,timestamp,embedding,substr(content,1,200) from memory_fragments where origin in ('inner_thought','study') and embedding is not null order by timestamp").fetchall()
ids=[r[0] for r in rows]; org=np.array([r[1] for r in rows]); ts=np.array([r[2] for r in rows])
W=np.stack([np.frombuffer(r[3],dtype=np.float32) for r in rows])
print('waking',W.shape, np.linalg.norm(W,axis=1).mean())
m=SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",device='cpu')
# verification: re-embed 40 stored thoughts from full content; cosine to stored blob
rng=np.random.default_rng(0); idx=rng.choice(len(rows),40,replace=False)
full=[c.execute("select content from memory_fragments where fragment_id=?",(ids[i],)).fetchone()[0] for i in idx]
E=m.encode(full,normalize_embeddings=True,show_progress_bar=False)
cs=(E*W[idx]).sum(1); print('stored-vs-reembed cos: min %.4f mean %.4f'%(cs.min(),cs.mean()))
dl=[json.loads(l) for l in open('C:/Nascence/data/dream_log.jsonl',encoding='utf-8') if l.strip()]
arcs=[r for r in dl if 'close_reason' in r]
def ttexts(r):
    t=[]
    for x in (r.get('seed',{}) or {}).get('tension_labels',[]) or []: t.append(str(x))
    if r.get('final_unresolved_core'): t.append(r['final_unresolved_core'])
    return t
texts=[];own=[]
for i,r in enumerate(arcs):
    for t in ttexts(r): texts.append(t); own.append(i)
TE=m.encode(texts,normalize_embeddings=True,show_progress_bar=False,batch_size=64)
tails=[" ".join((r.get('final_narrative') or r.get('narrative') or '').split())[-260:] for r in arcs]
DE=m.encode(tails,normalize_embeddings=True,show_progress_bar=False,batch_size=64)
np.savez('prep_J-1964.npz',W=W,ts=ts,org=org,ids=np.array(ids),TE=TE,own=np.array(own),DE=DE,arc_ts=np.array([r['ts'] for r in arcs]),
  cr=np.array([r['close_reason'] for r in arcs]),texts=np.array(texts,dtype=object),tails=np.array(tails,dtype=object))
print('arcs',len(arcs),'arcs with T text',len(set(own)),'texts',len(texts))
