import json,collections,sys
sys.stdout.reconfigure(encoding='utf-8')
base=collections.defaultdict(collections.Counter); cnt=collections.defaultdict(int)
def put(key,o):
    if not isinstance(o,dict) or '_error' in o: base[key]['ERR']+=1; return
    base[key][str(o.get('primary')).lower()]+=1
for l in open('docs/lab/J-2813_data/replay.jsonl',encoding='utf-8'):
    d=json.loads(l)
    if d['arm']=='A': put(('qwen_base(J-2813 A)',d['group']),d['out'])
fare={}
for l in open('docs/lab/J-4115_data/replay.jsonl',encoding='utf-8'):
    d=json.loads(l); put((d['variant'],d['group']),d['out'])
    o=d['out']
    if isinstance(o,dict) and '_error' not in o: fare.setdefault((d['variant'],d['group']),[]).append(o.get('trust',0))
for k in sorted(base):
    n=sum(base[k].values()); t=[x for x in fare.get(k,[]) if isinstance(x,(int,float))]
    print(k,'n=%d'%n,dict(base[k].most_common(6)),'trust_mean=%.2f'%(sum(t)/len(t)) if t else '')
