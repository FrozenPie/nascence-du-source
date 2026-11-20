import json, collections
rows=[json.loads(l) for l in open('docs/lab/J-4127_judge_gemma.jsonl',encoding='utf-8')]
best={}
for r in rows:
    if 'judge' in r: best[(r['pre'],r['arm'],r['i'])]=r['judge']['unsampled_feeling']
tot=collections.defaultdict(lambda:[0,0]); pc=collections.defaultdict(lambda:collections.defaultdict(lambda:[0,0]))
for (p,a,i),v in best.items():
    tot[a][0]+=v; tot[a][1]+=1; pc[p][a][0]+=v; pc[p][a][1]+=1
for a in ('old','new'): print(a, tot[a], round(tot[a][0]/max(1,tot[a][1]),3))
for p in pc: print(p, {a:tuple(pc[p][a]) for a in pc[p]})
import math
(a,n),(b,m)=tot['old'],tot['new']
# fisher via scipy if available
try:
    from scipy.stats import fisher_exact; print('fisher', fisher_exact([[a,n-a],[b,m-b]]))
except Exception as e: print('no scipy')
