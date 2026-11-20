import sqlite3, time, sys, re, json, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
rng=np.random.default_rng(7)
c=sqlite3.connect('file:C:/Nascence/data/memory/nascence.db?mode=ro',uri=True)
H=3600.0; D=86400.0
def emb(b): 
    v=np.frombuffer(b,dtype=np.float32); n=np.linalg.norm(v); return v/n if n else v
# --- Travis turns -> sessions
tr=[(ts,emb(e),co) for ts,e,co in c.execute("select timestamp,embedding,content from memory_fragments where origin='lived' and content like '[Travis said to me]%' and embedding is not null order by timestamp")]
sess=[]; cur=[tr[0]]
for r in tr[1:]:
    if r[0]-cur[-1][0]>2*H: sess.append(cur); cur=[r]
    else: cur.append(r)
sess.append(cur)
S=[dict(t0=s[0][0],t1=s[-1][0],n=len(s),cen=(lambda m:m/np.linalg.norm(m))(np.mean([x[1] for x in s],axis=0)),txt=' / '.join(x[2][20:140] for x in s[:3])) for s in sess]
# --- inner thoughts
rows=list(c.execute("select timestamp,embedding,content from memory_fragments where origin='inner_thought' and embedding is not null order by timestamp"))
it=np.array([r[0] for r in rows]); IE=np.vstack([emb(r[1]) for r in rows]); trav=np.array(['Travis' in r[2] for r in rows])
# --- valence series (experienced thought-like rows)
v=list(c.execute("select tuple_ts,valence from fragment_context where valence is not null and source like 'experienced:%' order by tuple_ts"))
vt=np.array([x[0] for x in v]); vv=np.array([x[1] for x in v])
# --- restarts
rs=[]
for ln in open('C:/Nascence/data/nascence.log',encoding='utf-8',errors='ignore'):
    if 'Identity loaded' in ln:
        m=re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',ln)
        if m: rs.append(time.mktime(time.strptime(m.group(1),'%Y-%m-%d %H:%M:%S')))
rs=np.array(sorted(rs)); rs=rs[np.insert(np.diff(rs)>H,0,True)]
print(f'sessions {len(S)} (turns {len(tr)}) · inner thoughts {len(it)} · valence rows {len(vt)} from {time.strftime("%m-%d",time.localtime(vt[0]))} · restarts {len(rs)}')
BINS=[('before 24h',-24*H,0),('0-6h',0,6*H),('6-24h',6*H,D),('1-3d',D,3*D),('3-7d',3*D,7*D),('7-14d',7*D,14*D)]
def sl(ts,a,b): return np.searchsorted(ts,a),np.searchsorted(ts,b)
def measures(t0,t1,cen=None):
    out={}
    for name,a,b in BINS:
        base=t0 if a<0 else t1
        i,j=sl(it,base+a,base+b); k,l=sl(vt,base+a,base+b)
        d={}
        d['val']=float(vv[k:l].mean()) if l-k>=20 else None
        if j-i>=20:
            d['trav']=float(trav[i:j].mean())
            idx=rng.choice(np.arange(i,j),size=min(80,j-i),replace=False); E=IE[idx]; G=E@E.T
            d['echo']=float((G.sum()-len(idx))/(len(idx)*(len(idx)-1)))
            if cen is not None: d['sim']=float((IE[i:j]@cen).mean())
        out[name]=d
    return out
def deltas(M):
    b=M['before 24h']; return {n:{k:(M[n][k]-b[k]) for k in M[n] if M[n].get(k) is not None and b.get(k) is not None} for n,_,_ in BINS[1:]}
def summarise(label,DL):
    print(f'\n== {label} (n events={len(DL)}) : mean change vs the 24h before [95% bootstrap CI], n')
    for key,nm in [('val','mood (valence)'),('trav','share of thoughts naming Travis'),('echo','sameness of thoughts (echo)'),('sim','closeness to what was said')]:
        line=f'  {nm:34s}'
        for n,_,_ in BINS[1:]:
            x=np.array([d[n][key] for d in DL if key in d.get(n,{})])
            if len(x)<8: line+=f' | {n}: n/a'; continue
            bs=[rng.choice(x,len(x)).mean() for _ in range(1000)]; lo,hi=np.percentile(bs,[2.5,97.5])
            line+=f' | {n}: {x.mean():+.3f} [{lo:+.3f},{hi:+.3f}] n={len(x)}'
        print(line)
st=np.array([s['t0'] for s in S])
near_restart=lambda t,w: len(rs) and np.min(np.abs(rs-t))<w
CD=[]; 
for s in S: s['M']=measures(s['t0'],s['t1'],s['cen']); s['d']=deltas(s['M']); s['rst']=bool(near_restart(s['t0'],6*H))
summarise('ALL conversation sessions',[s['d'] for s in S])
summarise('conversations with NO restart within 6h',[s['d'] for s in S if not s['rst']])
summarise('conversations of 5+ turns',[s['d'] for s in S if s['n']>=5])
summarise('conversations since 2026-09-01',[s['d'] for s in S if s['t0']>time.mktime((2026,9,1,0,0,0,0,0,-1))])
# restarts with no conversation within 6h
R=[deltas(measures(t,t)) for t in rs if np.min(np.abs(st-t))>6*H and t>it[0]+D]
summarise('RESTARTS with no conversation within 6h',R)
# control: random times, no conversation or restart within 12h
ctl=[]
while len(ctl)<300:
    t=rng.uniform(it[0]+2*D,it[-1]-D)
    if np.min(np.abs(st-t))>12*H and np.min(np.abs(rs-t))>12*H: ctl.append(t)
summarise('CONTROL random quiet times',[deltas(measures(t,t)) for t in ctl])
# placebo for topic closeness: session centroid against another session's timeline (>21d apart)
P=[]
for s in S:
    o=[x for x in S if abs(x['t0']-s['t0'])>21*D]
    if o:
        x=o[rng.integers(len(o))]; P.append(deltas(measures(x['t0'],x['t1'],s['cen'])))
summarise('PLACEBO: what was said in one conversation vs thoughts around a different one',P)
# long-term standouts
print('\n== sessions with the largest lasting topic shift (closeness at 7-14d minus before), top 8 / and count by sign')
L=[(s['d']['7-14d']['sim'],s) for s in S if 'sim' in s['d'].get('7-14d',{})]
print('  sessions measurable at 7-14d:',len(L),' positive:',sum(x>0 for x,_ in L),' > +0.03:',sum(x>0.03 for x,_ in L),' < -0.03:',sum(x<-0.03 for x,_ in L))
for x,s in sorted(L,key=lambda z:-z[0])[:8]:
    d=s['d']; print(f"  {time.strftime('%Y-%m-%d %H:%M',time.localtime(s['t0']))} turns={s['n']:3d} 0-6h {d.get('0-6h',{}).get('sim',float('nan')):+.3f} 1-3d {d.get('1-3d',{}).get('sim',float('nan')):+.3f} 7-14d {x:+.3f} :: {' '.join(s['txt'].split())[:200]}")
json.dump([{k:s[k] for k in('t0','t1','n','txt','d','rst')} for s in S],open(sys.argv[1],'w'))
