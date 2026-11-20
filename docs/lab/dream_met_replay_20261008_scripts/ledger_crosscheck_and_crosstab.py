import collections, numpy as np, json, datetime
from replay_J_1964 import *
R=recur_days(0.60)
def rep(N,K,Rm,M,mask=None,label=''):
    st=np.array(states(R,N,K,Rm,M))
    if mask is not None: st=np.where(mask,st,'x')
    s=collections.Counter(st.tolist()); b=s['met']+s['unmet']+s['relapsed']; ne=s['met']+s['relapsed']; nb=s['no-baseline']
    print(label,(N,K,Rm,M),dict(s),'| base',b,'nobase %.1f%% met %.1f%% unmet %.1f%% relapsed %.1f%% | relapsed/ever-met %.2f ever-met %.1f%%'%(100*nb/(nb+b),100*s['met']/b,100*s['unmet']/b,100*s['relapsed']/b,s['relapsed']/max(1,ne),100*ne/b))
    return st
for p in [(3,21,2,4),(3,21,2,3),(4,21,2,4),(3,21,2,5)]: rep(*p,label='all arcs')
st=rep(3,21,2,4,label='CHOSEN')
late=arc_ts>=datetime.datetime(2026,8,29).timestamp()
rep(3,21,2,4,mask=late,label='since 08-29')
rep(3,21,2,4,mask=~late,label='before 08-29')
# close_reason crosstab
cr=z['cr']; ct=collections.Counter(zip(cr.tolist(),st.tolist())); 
for k in sorted(ct): 
    if k[1] in('met','unmet','relapsed','no-baseline'): print(k,ct[k])
# ledger cross-check: nearest archive tension centroid to each arc T; was it re-bumped after arc+N?
ar=[json.loads(l) for l in open('C:/Nascence/data/tensions_archive.jsonl',encoding='utf-8') if l.strip()]
C=np.array([a['centroid'] for a in ar],dtype=np.float32); C/=np.linalg.norm(C,axis=1,keepdims=True)+1e-9
bump=np.array([max(a.get('_chronic_last_ts',0) or 0,a.get('last_ts',0) or 0) for a in ar])
agree=collections.Counter()
for k,a in enumerate(own):
    pass
best={}
for k,a in enumerate(own):
    sims=C@TE[k]; j=int(sims.argmax())
    if sims[j]>=0.6 and (a not in best or sims[j]>best[a][0]): best[a]=(float(sims[j]),j)
print('arcs with ledger tension cos>=0.6:',len(best),'of',int(hasT.sum()))
for state in ('met','unmet','relapsed'):
    idx=[a for a in best if st[a]==state]
    rebump=[bump[best[a][1]]>arc_ts[a]+3*86400 for a in idx]
    print(state,'matched',len(idx),'ledger tension last-bumped after arc+3d (still live in ledger):',sum(rebump))
print('arcs total',nA,'hasT',int(hasT.sum()))
