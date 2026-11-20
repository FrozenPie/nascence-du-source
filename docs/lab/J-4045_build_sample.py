import json, random
out=json.load(open('docs/reviews/J-3312_data/J-3312_out.json'))
rows=[json.loads(l) for l in open('data/training/reflection.jsonl',encoding='utf-8') if l.strip()][-500:]
byc={}
for r in rows: byc[r['cycle_id']]=r
elig=[]
for c in out:
    new=[f for f in c['new'] if f['sim']>=0.6 and f['ts']<=c['ts']]
    if not new or c['cycle_id'] not in byc: continue
    best=max(new,key=lambda f:f['sim'])
    r=byc[c['cycle_id']]
    o=r['output']; draft=o.get('draft') if isinstance(o,dict) else str(o)
    elig.append(dict(cycle_id=c['cycle_id'],raw_input=r['raw_input'],draft=draft,best=best,n_new=len(new)))
print('eligible',len(elig))
random.Random(3312).shuffle(elig)
s=elig[:40]
json.dump(s,open('docs/lab/J-4045_sample.json','w'),indent=1)
print(len(s)); print(json.dumps(s[0])[:900])
