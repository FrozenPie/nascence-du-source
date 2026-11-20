"""J-2806 read-only: do slow fast-path retrieve() calls fall inside a sleep (night-mind) interval from nascence.log?
Sleep interval = 'entering Sleep State' ... next '[night] waking:' (+ the 'scheduler turns during sleep' line)."""
import json, re, datetime as dt, bisect, statistics as st
LOG=r'C:/Nascence/data/nascence.log'; PROBE=r'C:/Nascence/data/retrieve_latency_probe.jsonl'
rows=[json.loads(l) for l in open(PROBE,encoding='utf-8')]
calls=[r for r in rows if r.get('path') in('fast','fast+delta')]
t_lo=calls[0]['timestamp']-7200
ev=[]
with open(LOG,encoding='utf-8',errors='replace') as f:
    for line in f:
        if 'entering Sleep State' in line or '[night] waking:' in line or 'wake requested' in line or 'scheduler turns during sleep' in line:
            ts=dt.datetime.strptime(line[:23],'%Y-%m-%d %H:%M:%S,%f').timestamp()
            if ts<t_lo: continue
            kind='enter' if 'entering Sleep' in line else ('wake' if 'waking:' in line else ('wakereq' if 'wake requested' in line else 'sched'))
            ev.append((ts,kind,line.strip()[24:200]))
iv=[];cur=None
for ts,k,l in ev:
    if k=='enter': cur=ts
    elif k=='wake' and cur is not None: iv.append((cur,ts)); cur=None
print('sleep intervals in probe era:',len(iv),'total hours %.1f'%(sum(b-a for a,b in iv)/3600))
starts=[a for a,b in iv]
def inside(s,e):
    k=bisect.bisect_right(starts,e)-1
    for j in (k-1,k):
        if j>=0 and iv[j][0]<=e and iv[j][1]>=s: return True
    return False
res={True:[],False:[]}
for r in calls:
    tot=r['elapsed_ms_sql']+r['elapsed_ms_score']; e=r['timestamp']; s=e-tot/1000
    res[inside(s,e)].append((tot,r['path'],e))
for k,v in res.items():
    t=sorted(x[0] for x in v)
    print('in sleep' if k else 'awake   ',len(t),'p50 %.0f p90 %.0f p99 %.0f max %.0f'%(t[len(t)//2],t[int(len(t)*.9)],t[int(len(t)*.99)],t[-1]),'>1500ms:',sum(1 for x in t if x>1500),'>700ms:',sum(1 for x in t if x>700))
for path in ('fast','fast+delta'):
    for k in (True,False):
        t=sorted(x[0] for x in res[k] if x[1]==path)
        if t: print(path,'in sleep' if k else 'awake',len(t),'p50 %.0f'%t[len(t)//2],'p90 %.0f'%t[int(len(t)*.9)],'>1500:',sum(1 for x in t if x>1500))
print('calls >1500ms and their sleep state:')
for k,v in res.items():
    for tot,p,e in v:
        if tot>1500: print(dt.datetime.fromtimestamp(e).strftime('%m-%d %H:%M:%S'),p,round(tot),'IN SLEEP' if k else 'awake')
