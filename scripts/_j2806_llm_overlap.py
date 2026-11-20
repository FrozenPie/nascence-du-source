"""J-2806 read-only: how many LOCAL-box LLM calls (nodes :11433 hot lane, :11439/:11440/:11442 CPU hubs) were in flight
during each fast-path retrieve() call?  llm_latency.jsonl rows: ts = completion time, s = duration."""
import json, bisect, statistics as st, datetime as dt
LOCAL={'11433','11439','11440','11442'}
rows=[json.loads(l) for l in open(r'C:/Nascence/data/retrieve_latency_probe.jsonl',encoding='utf-8')]
calls=[r for r in rows if r.get('path') in('fast','fast+delta')]
lo=calls[0]['timestamp']-300
ll=[]
for line in open(r'C:/Nascence/data/llm_latency.jsonl',encoding='utf-8',errors='replace'):
    try: d=json.loads(line)
    except Exception: continue
    if d['ts']<lo: continue
    ll.append((d['ts']-d['s'],d['ts'],str(d['node']),d['model']))
ll.sort(); starts=[x[0] for x in ll]
print('llm rows in era',len(ll),'local share %.0f%%'%(100*sum(1 for x in ll if x[2] in LOCAL)/len(ll)))
maxdur=max(x[1]-x[0] for x in ll)
def inflight(s,e):
    out=[]
    j=bisect.bisect_right(starts,e)
    k=bisect.bisect_left(starts,s-maxdur)
    for x in ll[k:j]:
        if x[1]>=s and x[0]<=e: out.append(x)
    return out
def stat(r):
    tot=(r['elapsed_ms_sql']+r['elapsed_ms_score'])/1000; e=r['timestamp']; s=e-tot
    f=inflight(s,e); return len([x for x in f if x[2] in LOCAL]), sorted(set(x[2] for x in f))
slow=[r for r in calls if r['elapsed_ms_sql']+r['elapsed_ms_score']>700]
norm=[r for r in calls if r['elapsed_ms_sql']+r['elapsed_ms_score']<=700]
sl=[stat(r)[0] for r in slow]; nm=[stat(r)[0] for r in norm]
print('local LLM calls in flight: slow mean %.2f (share>=1: %.0f%%)  normal mean %.2f (share>=1: %.0f%%)'%(st.mean(sl),100*sum(1 for x in sl if x)/len(sl),st.mean(nm),100*sum(1 for x in nm if x)/len(nm)))
for r in slow:
    tot=r['elapsed_ms_sql']+r['elapsed_ms_score']
    if tot>1500:
        n,nodes=stat(r); print(dt.datetime.fromtimestamp(r['timestamp']).strftime('%m-%d %H:%M:%S'),round(tot),'local in flight',n,'nodes',nodes)
