import json,collections,datetime as dt
G=[json.loads(l) for l in open('data/deliberation_guard_log.jsonl',encoding='utf-8')]
D=[]
for l in open('data/deliberation_log.jsonl',encoding='utf-8'):
    try:D.append(json.loads(l))
    except:pass
t0=G[0]['ts']
day=lambda t:dt.datetime.fromtimestamp(t).strftime('%m-%d')
gd=collections.Counter(day(r['ts']) for r in G)
dd=collections.Counter(day(r['ts']) for r in D if r['ts']>=t0-3600)
print('days  guard  delib_kept')
for d in sorted(set(gd)|set(dd)):
    g,k=gd[d],dd[d];print(d,g,k,f'{g/(g+k):.2f}' if g+k else '')
tg=sum(gd.values());tk=sum(dd.values());print('total',tg,tk,tg/(tg+tk))
# window with fix before skip-upfront (to 11-09)
q=lambda s:('?' in s or '？' in s)
# (3) deliberation_log rows since t0 whose raw has a question and integrated has none
bad=[r for r in D if r['ts']>=t0-60 and q(r['raw']) and not q(r.get('integrated',''))]
print('question-dropped rows in deliberation_log since guard:',len(bad), [day(r['ts']) for r in bad][:10])
allq=[r for r in D if r['ts']>=t0-60 and q(r['raw'])]
print('rows w/ question raw since guard:',len(allq))
# guard rows sanity: raw has q, rejected no q
print('guard rows raw q:',sum(q(r['raw']) for r in G),'rejected has q:',sum(q(r['rejected_integrated']) for r in G))
print('arm',collections.Counter(r['arm'] for r in G))
