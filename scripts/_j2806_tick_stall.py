"""J-2806 read-only: is a slow retrieve() a process-wide stall?  The competence [tier3] tick is a 120 s heartbeat; a gap
well over 120 s that CONTAINS the call means the loop thread was starved/blocked around the call (not retrieve-specific)."""
import json, re, datetime as dt, bisect
LOG=r'C:/Nascence/data/nascence.log'; PROBE=r'C:/Nascence/data/retrieve_latency_probe.jsonl'
rows=[json.loads(l) for l in open(PROBE,encoding='utf-8')]
calls=[r for r in rows if r.get('path') in('fast','fast+delta')]
t_lo=calls[0]['timestamp']-3600
ticks=[]
with open(LOG,encoding='utf-8',errors='replace') as f:
    for line in f:
        if '[tier3] tick #' in line:
            ts=dt.datetime.strptime(line[:23],'%Y-%m-%d %H:%M:%S,%f').timestamp()
            if ts>=t_lo: ticks.append(ts)
print('tier3 ticks in era:',len(ticks))
gaps=[(ticks[i],ticks[i+1],ticks[i+1]-ticks[i]) for i in range(len(ticks)-1)]
LATE=150.0; DOWN=1800.0
late=[g for g in gaps if LATE<g[2]<DOWN]
print('gaps >%.0fs (excluding >%.0fs = Du down): %d of %d'%(LATE,DOWN,len(late),len(gaps)))
starts=[g[0] for g in gaps]
def gap_of(ts):
    k=bisect.bisect_right(starts,ts)-1
    return gaps[k] if 0<=k<len(gaps) and gaps[k][0]<=ts<=gaps[k][1] else None
def classify(r):
    tot=(r['elapsed_ms_sql']+r['elapsed_ms_score'])/1000; e=r['timestamp']; s=e-tot
    g=gap_of(e)
    if g is None or g[2]>=DOWN: return 'nogap'
    return 'late' if g[2]>LATE else 'ontime'
import collections
for name,cond in (('all calls',lambda r:True),('>700ms',lambda r:r['elapsed_ms_sql']+r['elapsed_ms_score']>700),
                  ('>1500ms',lambda r:r['elapsed_ms_sql']+r['elapsed_ms_score']>1500),('<=700ms',lambda r:r['elapsed_ms_sql']+r['elapsed_ms_score']<=700)):
    c=collections.Counter(classify(r) for r in calls if cond(r)); print(name,dict(c))
print('--- the >1500 ms calls, with the enclosing tick gap')
for r in calls:
    tot=(r['elapsed_ms_sql']+r['elapsed_ms_score'])
    if tot>1500:
        g=gap_of(r['timestamp'])
        print(dt.datetime.fromtimestamp(r['timestamp']).strftime('%m-%d %H:%M:%S'),round(tot),'ms; enclosing tick gap:', None if g is None else '%.0f s (%s -> %s)'%(g[2],dt.datetime.fromtimestamp(g[0]).strftime('%H:%M:%S'),dt.datetime.fromtimestamp(g[1]).strftime('%H:%M:%S')))
