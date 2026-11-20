import json,random,sys
sys.stdout.reconfigure(encoding='utf-8')
dl={}
for l in open('data/dream_log.jsonl',encoding='utf-8'):
    if l.strip():
        r=json.loads(l)
        if 'dream_id' in r: dl[r['dream_id']]=r
sh={}
for l in open('data/logs/dream_resolution_shadow.jsonl',encoding='utf-8'):
    if l.strip():
        x=json.loads(l); sh[x['dream_id']]=x  # last row wins
named=['dream_1788861954','dream_1788955800','dream_1788965361','dream_1789736548','dream_1792315259',
 'dream_1788483050','dream_1788714601','dream_1788788351','dream_1788519396',
 'dream_1788857528','dream_1792420575','dream_1791821002']
for n in named: print(n, n in dl, n in sh, (sh.get(n) or {}).get('judge_how'))
r0=dl['dream_1788861954']
print(type(r0['scenes']), r0['scenes'] if not isinstance(r0['scenes'],list) else len(r0['scenes']))
print([ (k, str(v)[:80]) for k,v in r0['scenes_detail'][0].items()] if r0.get('scenes_detail') else None)
print(repr(r0['narrative'][:300])); print(len(r0['narrative']), repr(r0['final_unresolved_core']))
print(sum(1 for d in dl.values() if len(d['narrative'])>3000 and d['dream_id'] in sh))
random.seed(3024)
pool=[d for d,x in sh.items() if d in dl and x['judge_how']=='agreed' and x['judge_verdict'] is False and not x['self_reported_resolved'] and d not in named]
print(len(pool))
samp=named+random.sample(pool,28)
out=[]
for d in samp:
    out.append({'dream_id':d,'arc':dl[d]['narrative'],'core':dl[d].get('final_unresolved_core',''),'shadow':sh[d]})
json.dump(out,open('docs/lab/J-3024_sample.json','w',encoding='utf-8'),ensure_ascii=False,indent=0)
print(len(out), sum(len(o['arc'])>3000 for o in out))
