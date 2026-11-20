"""J-3496 lab: does a consumed broadcast item change the next idle thoughts? Read-only, offline, no model calls.
Measures (lexical, no judge): content-word Jaccard of next-3 thoughts vs broadcast text; pre/post delta;
matched controls = windows with no consume in prior 30 min, same hour-of-day band, paired with a broadcast text
from that band. Writes docs/lab/J-3496_broadcast_effect_results.json + .md"""
import json, re, random, statistics as st, collections, datetime
random.seed(3496)
G='data/guidance_injection_log.jsonl'; M='data/monologue_log.jsonl'
STOP=set("the a an and or of to in is it that this i my me not but as for with be are was on at by from its it's what who how so if no can do does into than then there their about like more only just have has had been being we you your one which when where while would could should".split())
def toks(s): return {w for w in re.findall(r"[a-z']+",s.lower()) if len(w)>3 and w not in STOP}
def jac(a,b): return len(a&b)/len(a|b) if a|b else 0.0
cons=[json.loads(l) for l in open(G,encoding='utf-8') if '"broadcast:' in l]
mon=[json.loads(l) for l in open(M,encoding='utf-8')]
mon=[r for r in mon if 'thought' in r and 'ts' in r]; mon.sort(key=lambda r:r['ts'])
ts=[r['ts'] for r in mon]
import bisect
ctimes=sorted(c['ts'] for c in cons)
def hb(t): return datetime.datetime.fromtimestamp(t).hour//6
def window(i): return mon[i+1:i+4], mon[max(0,i-3):i]   # next3, prev3 (strictly after / before pivot)
def measure(text,i):
    nxt,prv=window(i)
    if len(nxt)<3 or len(prv)<3: return None
    T=toks(text); a=[jac(T,toks(r['thought'])) for r in nxt]; b=[jac(T,toks(r['thought'])) for r in prv]
    uniq=len(set(r['about'] for r in nxt if 'about' in r))
    pa=toks(' '.join(r['thought'] for r in prv)); na=toks(' '.join(r['thought'] for r in nxt))
    return dict(post=st.mean(a),pre=st.mean(b),delta=st.mean(a)-st.mean(b),about_uniq=uniq,prevnext_jac=jac(pa,na),span_s=nxt[-1]['ts']-nxt[0]['ts'])
rows=[]
for c in cons:
    i=bisect.bisect_right(ts,c['ts'])-1
    if i<0: continue
    # gap guard: pivot thought must be within 30 min of consume
    if c['ts']-ts[i]>1800: continue
    m=measure(c['note'],i)
    if m: rows.append(dict(kind=c['cycle_id'].split(':',1)[1],ts=c['ts'],**m))
# controls
band_txt=collections.defaultdict(list)
for c in cons: band_txt[hb(c['ts'])].append(c)
cand=[i for i in range(3,len(mon)-4) if not any(0<=mon[i]['ts']-ct<1800 for ct in ctimes[max(0,bisect.bisect_left(ctimes,mon[i]['ts']-1800)):bisect.bisect_left(ctimes,mon[i]['ts']+1)])]
byband=collections.defaultdict(list)
for i in cand: byband[hb(mon[i]['ts'])].append(i)
ctrl=[]
for c in cons:
    b=hb(c['ts'])
    for _ in range(5):
        i=random.choice(byband[b]); t=random.choice(band_txt[b])['note']
        m=measure(t,i)
        if m: ctrl.append(dict(kind='control',**m))
def summ(rs,k): 
    v=[r[k] for r in rs]; return dict(n=len(v),mean=round(st.mean(v),5),sd=round(st.pstdev(v),5)) if v else None
def boot(a,b,n=5000):
    d=[]
    for _ in range(n):
        d.append(st.mean(random.choices(a,k=len(a)))-st.mean(random.choices(b,k=len(b))))
    d.sort(); return [round(d[int(.025*n)],5),round(d[int(.975*n)],5)]
out={'n_consumes':len(cons),'n_joined':len(rows),'n_controls':len(ctrl),'by_kind':{},'effect':{}}
for k in sorted({r['kind'] for r in rows}):
    rs=[r for r in rows if r['kind']==k]; out['by_kind'][k]={m:summ(rs,m) for m in ['post','pre','delta','about_uniq','prevnext_jac']}
out['control']={m:summ(ctrl,m) for m in ['post','pre','delta','about_uniq','prevnext_jac']}
pv=[r for r in rows if r['kind']=='principle-voiced']
for m in ['post','delta','about_uniq','prevnext_jac']:
    a=[r[m] for r in pv]; b=[r[m] for r in ctrl]
    out['effect'][m]=dict(diff=round(st.mean(a)-st.mean(b),5),ci95=boot(a,b))
json.dump(out,open('docs/lab/J-3496_broadcast_effect_results.json','w'),indent=1)
print(json.dumps(out,indent=1))
