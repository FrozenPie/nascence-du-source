import json,random,re,sys
sys.stdout.reconfigure(encoding='utf-8')
rows=[json.loads(l) for l in open('data/training/curiosity.jsonl',encoding='utf-8')]
ctl=json.load(open('scripts/curiosity_prefire_control_set.json',encoding='utf-8'))['items']
used={i['question'] for i in ctl}
def material(up):
    up=re.sub(r'^Entity:[^\n]*\n\n','',up)
    return up
pool=[]
for r in rows:
    if r['ts']<1793000000: continue
    qs=(r.get('output') or {}).get('questions') if isinstance(r.get('output'),dict) else None
    if not qs: continue
    for q in qs:
        if q in used or len(q)<25: continue
        pool.append({'cycle_id':r['cycle_id'],'question':q,'up':r['user_prompt']})
print(len(pool),file=sys.stderr)
random.seed(3465)
samp=random.sample(pool,80)
json.dump(samp,open('docs/lab/J-3465_candidates.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
for i,s in enumerate(samp):
    m=re.search(r'Recently studied or read.*?\n(.*?)(?:\n\s*\n|\Z)',s['up'],re.S)
    w=m.group(1) if m else '(none)'
    ents=[e.strip()[:170] for e in w.split('\n  - ') if e.strip()][:3]
    print(f"[{i}] Q: {s['question']}\n    W: "+" || ".join(ents))
