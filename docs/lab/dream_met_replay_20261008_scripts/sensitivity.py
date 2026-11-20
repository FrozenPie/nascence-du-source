import collections, numpy as np, datetime
from replay_J_1964 import *
late=arc_ts>=datetime.datetime(2026,8,29).timestamp()
def line(th,N,K,Rm,M,mask=None):
    R=recur_days(th); st=np.array(states(R,N,K,Rm,M))
    if mask is not None: st=np.where(mask,st,'x')
    s=collections.Counter(st.tolist()); b=s['met']+s['unmet']+s['relapsed']; ne=s['met']+s['relapsed']; nb=s['no-baseline']
    return '| %.2f | %d | %d | %d | %d | %d | %d (%.0f%%) | %d (%.0f%%) | %d (%.0f%%) | %d (%.0f%%) | %.2f |'%(th,N,K,Rm,M,b,nb,100*nb/(nb+b),s['met'],100*s['met']/b,s['unmet'],100*s['unmet']/b,s['relapsed'],100*s['relapsed']/b,s['relapsed']/max(1,ne)), s, st
base=(0.61,3,25,2,3)
print('| theta | N | K | R | M | arcs w/ baseline | no-baseline | met | unmet | relapsed | relapsed/ever-met |')
print('|---|---|---|---|---|---|---|---|---|---|---|')
vars_=[base]+[(t,)+base[1:] for t in (0.58,0.60,0.62,0.65)]+[base[:1]+(n,)+base[2:] for n in (2,4,5,7)]+[base[:2]+(k,)+base[3:] for k in (14,21,30)]+[base[:3]+(r,)+base[4:] for r in (3,4)]+[base[:4]+(m,) for m in (5,7,14)]
for v in vars_:
    l,s,st=line(*v); print(l, '<- chosen' if v==base else '')
l,s,st=line(*base); print(dict(s))
l2,s2,_=line(*base,mask=late); print('since 08-29',l2,dict(s2))
l3,s3,_=line(*base,mask=~late); print('before 08-29',l3,dict(s3))
cr=z['cr']; print(sorted(collections.Counter((a,b) for a,b in zip(cr.tolist(),st.tolist()) if b in('met','unmet','relapsed','no-baseline')).items()))
