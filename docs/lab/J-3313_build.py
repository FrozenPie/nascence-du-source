import json,ast,random,datetime,collections
cut=datetime.datetime(2026,10,6).timestamp()
aff={}
for l in open('data/affect_log.jsonl',encoding='utf-8'):
    try:d=json.loads(l)
    except: continue
    aff[d['cycle_id']]=d
rows=[];seen=set();bad=0
for l in open('data/training/reflection.jsonl',encoding='utf-8'):
    try:d=json.loads(l)
    except: bad+=1;continue
    if float(d['ts'])<cut: continue
    cid=d['cycle_id']
    if cid in seen or cid not in aff: continue
    try: o=ast.literal_eval(d['output']) if isinstance(d['output'],str) else d['output']
    except Exception: 
        try:o=json.loads(d['output'])
        except Exception: bad+=1;continue
    dr=o.get('draft') if isinstance(o,dict) else None
    if not dr or len(dr)<40: continue
    seen.add(cid); a=aff[cid]
    rows.append(dict(cycle_id=cid,input_type=d['input_type'],draft=dr,stated=a['emotion']['valence'],carried=a['affect']['valence'],ts=d['ts']))
print(len(rows),bad,collections.Counter(r['input_type'] for r in rows))
random.seed(3313)
hum=[r for r in rows if r['input_type']=='human'];intl=[r for r in rows if r['input_type']!='human']
s=random.sample(hum,min(100,len(hum)))+random.sample(intl,200-min(100,len(hum)))
random.shuffle(s)
json.dump(s,open('docs/lab/J-3313_sample200.json','w'))
print(len(s),collections.Counter(r['input_type'] for r in s))
