"""J-2806 read-only: does a retrieve() probe row overlap a known heavy background job (chapters seed scan)?
Reads C:/Nascence/data read-only; prints a summary. Writes nothing."""
import json, re, datetime as dt, bisect, statistics as st, sys
LOG=r'C:/Nascence/data/nascence.log'; PROBE=r'C:/Nascence/data/retrieve_latency_probe.jsonl'
rows=[json.loads(l) for l in open(PROBE,encoding='utf-8')]
t0=min(r['timestamp'] for r in rows if r.get('path'))  # first row carrying a path
pat=re.compile(r'^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d{3}) \[nascence\.chapters\] \[chapters\] seed scan (over|done)')
iv=[]; cur=None
with open(LOG,encoding='utf-8',errors='replace') as f:
    for line in f:
        if '[chapters] seed scan' not in line: continue
        m=pat.match(line)
        if not m: continue
        ts=dt.datetime.strptime(m.group(1),'%Y-%m-%d %H:%M:%S,%f').timestamp()
        if ts<t0-3600: continue
        if m.group(2)=='over': cur=ts
        elif cur is not None:
            iv.append((cur,ts)); cur=None
print('seed-scan intervals since probe path era:',len(iv), 'mean dur %.1fs'%st.mean(b-a for a,b in iv))
starts=[a for a,b in iv]
def overlaps(s,e):
    k=bisect.bisect_right(starts,e)-1
    for j in range(max(0,k-1),k+1):
        if j>=0 and iv[j][0]<=e and iv[j][1]>=s: return True
    return False
res={'ov':[], 'no':[]}
for r in rows:
    p=r.get('path')
    if p not in('fast','fast+delta'): continue
    tot=(r['elapsed_ms_sql']+r['elapsed_ms_score'])
    e=r['timestamp']; s=e-tot/1000
    res['ov' if overlaps(s,e) else 'no'].append((tot,p,r))
for k,v in res.items():
    t=sorted(x[0] for x in v)
    print(k,len(t),'p50 %.0f p90 %.0f max %.0f'%(t[len(t)//2],t[int(len(t)*.9)],t[-1]),'>700:',sum(1 for x in t if x>700))
print('overlapping calls:')
for tot,p,r in res['ov']:
    print(dt.datetime.fromtimestamp(r['timestamp']).strftime('%m-%d %H:%M:%S'),p,round(tot))
# time-share: fraction of wall time inside a scan
span=max(r['timestamp'] for r in rows)-t0
print('scan time share of probe-era wall clock: %.2f%%'%(100*sum(b-a for a,b in iv)/span))
