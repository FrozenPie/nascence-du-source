"""J-2806 read-only: per-process rank of every fast-path retrieve() call (boot = 'Loading embedding model' line)."""
import json, re, datetime as dt, bisect, statistics as st
LOG=r'C:/Nascence/data/nascence.log'
boots=[]; shut=[]
with open(LOG,encoding='utf-8',errors='replace') as f:
    for line in f:
        if 'Loading embedding model' in line:
            boots.append(dt.datetime.strptime(line[:23],'%Y-%m-%d %H:%M:%S,%f').timestamp())
        elif 'Nascence shutting down' in line:
            shut.append(dt.datetime.strptime(line[:23],'%Y-%m-%d %H:%M:%S,%f').timestamp())
rows=[json.loads(l) for l in open(r'C:/Nascence/data/retrieve_latency_probe.jsonl',encoding='utf-8')]
calls=[r for r in rows if r.get('path') in('fast','fast+delta')]
rank={}
byboot={}
for r in calls:
    b=bisect.bisect_right(boots,r['timestamp']-(r['elapsed_ms_sql']+r['elapsed_ms_score'])/1000)-1
    byboot.setdefault(b,[]).append(r)
print('boot, first-3 totals ms, then median of rest, n')
first=[];later=[]
for b,v in sorted(byboot.items()):
    tots=[x['elapsed_ms_sql']+x['elapsed_ms_score'] for x in v]
    since=(v[0]['timestamp']-boots[b])/60
    print(dt.datetime.fromtimestamp(boots[b]).strftime('%m-%d %H:%M:%S'),'first call +%.1f min'%since,[round(t) for t in tots[:3]],'rest p50 %.0f'%(st.median(tots[3:]) if len(tots)>3 else -1),len(tots), v[0]['path'])
    first.append(tots[0]); later+=tots[1:]
print('first-call-after-boot: n',len(first),'median %.0f'%st.median(first),'min %.0f max %.0f'%(min(first),max(first)))
print('all later calls: n',len(later),'median %.0f'%st.median(later))
print('boots in era:',[dt.datetime.fromtimestamp(b).strftime('%m-%d %H:%M') for b in boots if b>=calls[0]['timestamp']-3600*24])
