import numpy as np, datetime, itertools, json, collections, sys
z=np.load('prep_J-1964.npz',allow_pickle=True)
W,ts,own,TE,DE,arc_ts=z['W'],z['ts'],z['own'],z['TE'],z['DE'],z['arc_ts']
nA=len(arc_ts)
D=lambda t: datetime.datetime.fromtimestamp(t).date().toordinal()
day=np.array([D(t) for t in ts]); end=day.max()
adays=np.array([D(t) for t in arc_ts])
# injected-text similarity per thought: max cos to dream tails of dreams with ts in [t-3d, t)
order=np.argsort(arc_ts); 
inj=np.full(len(ts),-1.0,dtype=np.float32)
SD=W@DE.T  # (nW, nArcs)
lo=np.searchsorted(arc_ts[order],ts-3*86400); hi=np.searchsorted(arc_ts[order],ts)
for i in range(len(ts)):
    if hi[i]>lo[i]: inj[i]=SD[i,order[lo[i]:hi[i]]].max()
print('thoughts with an active injected dream tail:',round(float((inj>-1).mean()),3))
# T sims: per arc, max over its T texts
ST=np.full((nA,len(ts)),-1.0,dtype=np.float32)
for k,a in enumerate(own):
    ST[a]=np.maximum(ST[a],TE[k]@W.T)
hasT=np.zeros(nA,bool); hasT[np.unique(own)]=True
# D-0233 dropped share
for th in (0.45,0.5,0.55,0.6):
    m=ST>=th; ex=m&(ST<=inj[None,:])
    print('theta',th,'raw recurrences',int(m[hasT].sum()),'dropped by D-0233 (closer to injected text)',int(ex[hasT].sum()),'share %.3f'%(ex[hasT].sum()/max(1,m[hasT].sum())))
dayidx=day-day.min(); nd=dayidx.max()+1
cntday=np.bincount(dayidx,minlength=nd)
obs=cntday>=5   # day counts as observed if >=5 waking thoughts
def recur_days(theta):
    """(nA, nd) bool: arc had a qualifying recurrence that day"""
    q=(ST>=theta)&(ST>inj[None,:])
    R=np.zeros((nA,nd),bool)
    for a in np.where(hasT)[0]:
        R[a,np.unique(dayidx[q[a]])]=True
    return R
def states(R,N,K,Rm,M,start=0):
    out=[]
    for a in range(nA):
        if not hasT[a]: out.append('noT'); continue
        d=adays[a]-day.min()
        pre=range(d-K,d); win=range(d+1,d+N+1); rel=range(d+N+1,d+N+M+1)
        if d-K<0 or any(x>=nd for x in itertools.chain(win,rel)) : out.append('pending' if d+N+M>=nd else 'noT'); continue
        pre_obs=[x for x in pre if obs[x]]
        if len(pre_obs)<max(Rm,0.6*K): out.append('unobs'); continue
        if not all(obs[x] for x in win): out.append('unobs'); continue
        base=sum(R[a,x] for x in pre_obs)
        if base<Rm: out.append('no-baseline'); continue
        if any(R[a,x] for x in win): out.append('unmet'); continue
        rel_obs=[x for x in rel if obs[x]]
        if len(rel_obs)<0.6*M: out.append('met?')   # met but relapse window unobservable
        elif any(R[a,x] for x in rel_obs): out.append('relapsed')
        else: out.append('met')
    return out
if __name__=='__main__':
    res=[]
    for th in (0.40,0.45,0.50,0.55,0.60,0.65):
        R=recur_days(th)
        for N,K,Rm,M in itertools.product((2,3,5,7,10),(14,21,30),(2,3,4,5),(3,5,7,14)):
            s=collections.Counter(states(R,N,K,Rm,M))
            b=s['unmet']+s['met']+s['relapsed']
            allb=b+s['no-baseline']
            res.append(dict(th=th,N=N,K=K,R=Rm,M=M,n=dict(s),base=b,
              met=s['met']/b if b else 0,unmet=s['unmet']/b if b else 0,rel=s['relapsed']/b if b else 0,nobase=s['no-baseline']/max(1,allb)))
    json.dump(res,open('grid_J-1964.json','w'))
    ok=[r for r in res if r['base']>=50 and all(0.02<=r[k]<=0.60 for k in ('met','unmet','rel'))]
    print('grid',len(res),'nondegenerate',len(ok))
    ok.sort(key=lambda r:-min(r['met'],r['unmet'],r['rel']))
    for r in ok[:15]: print({k:(round(v,3) if isinstance(v,float) else v) for k,v in r.items() if k!='n'}, r['n'])
