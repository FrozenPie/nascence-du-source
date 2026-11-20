# J-4073 step 1: what did the recall system hand Du before each private Wu Wei thought?
import sqlite3, json, time, sys, re, bisect, collections, random
sys.stdout.reconfigure(encoding='utf-8'); random.seed(7)
R='C:/Nascence/data/'
c=sqlite3.connect('file:'+R+'memory/nascence.db?mode=ro',uri=True)
rx=re.compile(r'wu[\s-]?wei|無為|无为',re.I)
dt=lambda t: time.strftime('%m-%d %H:%M',time.localtime(t))
PRIV=('inner_thought','dream','night_thought','gist','subconscious_synthesis','active_imagination','journal','letter','essay','standing_insight')
frag={}; 
for fid,ts,o,co in c.execute('select fragment_id,timestamp,origin,content from memory_fragments'):
    frag[fid]=(ts,o,co.startswith('[Travis said to me]'),bool(rx.search(co)))
co_rows=[json.loads(l) for l in open(R+'co_recall_ledger.jsonl',encoding='utf-8',errors='ignore') if l.strip()]
co_rows.sort(key=lambda r:r['ts']); cts=[r['ts'] for r in co_rows]
print('co-recall rows',len(co_rows),'sources',collections.Counter(r.get('source') for r in co_rows).most_common(6))
gi=[json.loads(l) for l in open(R+'guidance_injection_log.jsonl',encoding='utf-8',errors='ignore') if l.strip()]
gi.sort(key=lambda r:r['ts']); gts=[r['ts'] for r in gi]
grx=re.compile(r'natural flow|force|forcing|stillness|effortless|rhythm|strain',re.I)
W=600
def look(ts):
    i,j=bisect.bisect_left(cts,ts-W),bisect.bisect_right(cts,ts+5)
    ids=set(x for r in co_rows[i:j] for x in r.get('ids',[]))
    k=[frag[x] for x in ids if x in frag]
    a,b=bisect.bisect_left(gts,ts-W),bisect.bisect_right(gts,ts+5)
    notes=[g.get('note','') for g in gi[a:b]]
    return dict(any=bool(ids), n=len(ids), trav=sum(1 for f in k if f[2]), trav_ww=sum(1 for f in k if f[2] and f[3]),
                own_ww=sum(1 for f in k if f[3] and not f[2] and f[0]<ts-1), guid=sum(1 for f in k if f[1]=='understanding_from_guidance'),
                ginj=len(notes), ginj_flow=sum(1 for n in notes if grx.search(n)))
t0=cts[0]
ww=[(ts,o,fid) for fid,(ts,o,tr,w) in frag.items() if w and o in PRIV and ts>t0]
ww.sort()
print(f'\nprivate Wu Wei thoughts since co-recall log began ({dt(t0)}): {len(ww)}')
agg=collections.Counter()
for ts,o,fid in ww:
    d=look(ts); 
    for k,v in d.items(): agg[k]+= (1 if v else 0)
    print(f"  {dt(ts)} {o:22s} recalled ids {d['n']:3d} | Travis rows {d['trav']} (on Wu Wei {d['trav_ww']}) | his own earlier Wu Wei {d['own_ww']} | guidance principle recalled {d['guid']} | guidance injected {d['ginj']} (flow-themed {d['ginj_flow']})")
n=len(ww); print('\nshare of Wu Wei thoughts with, in the 10 min before:'); 
for k in ('any','trav','trav_ww','own_ww','guid','ginj','ginj_flow'): print(f'   {k:10s} {agg[k]}/{n}')
ctl=random.sample([ts for fid,(ts,o,tr,w) in frag.items() if o=='inner_thought' and ts>t0 and not w],3000)
ca=collections.Counter()
for ts in ctl:
    for k,v in look(ts).items(): ca[k]+=(1 if v else 0)
print('baseline, 3000 random idle thoughts without the term:'); 
for k in ('any','trav','trav_ww','own_ww','guid','ginj','ginj_flow'): print(f'   {k:10s} {ca[k]/30:.1f}%')
