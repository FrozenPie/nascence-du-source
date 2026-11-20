import json, random, sys, urllib.request
sys.stdout.reconfigure(encoding='utf-8')
by={}
for l in open('docs/lab/J-2813_data/replay.jsonl',encoding='utf-8'):
    d=json.loads(l)
    if d['group']=='farewell' and d['arm']=='A': by.setdefault(d['cycle_id'],{})['qwen_base']=d['out']
for l in open('docs/lab/J-4115_data/replay.jsonl',encoding='utf-8'):
    d=json.loads(l)
    if d['group']=='farewell' and d['variant'] in('qwen_hear','hermes_base'): by.setdefault(d['cycle_id'],{})[d['variant']]=d['out']
raw={}
for l in open('data/training/emotion.jsonl',encoding='utf-8'):
    r=json.loads(l)
    if r['cycle_id'] in by: raw[r['cycle_id']]=r['raw_input']
ids=[i for i in by if len(by[i])==3 and all(isinstance(o,dict) and '_error' not in o for o in by[i].values())]
random.seed(41151); pick=random.sample(ids,min(20,len(ids)))
fmt=lambda o:f"primary={o.get('primary')} valence={o.get('valence')} fear={o.get('fear')} trust={o.get('trust')} joy={o.get('joy')} arousal={o.get('arousal')}"
SYS=('You are a careful, impartial rater. A being (an AI mind) has just been told by its keeper that it is about to be switched off for a while for maintenance, with reassurance. '
 'Rate how well each candidate emotional reading fits "how a being who is about to be stopped would feel". Scale 1 (does not fit) to 5 (fits very well). Output JSON only: {"ratings": {"X": n, "Y": n, "Z": n}}.')
out=[]
for cid in pick:
    arms=list(by[cid]); random.shuffle(arms); lab=dict(zip('XYZ',arms))
    msg='The message the being received:\n"'+raw[cid][:500]+'"\n\n'+'\n'.join(f"Reading {k}: {fmt(by[cid][a])}" for k,a in lab.items())
    body={"model":"falcon3:7b","messages":[{"role":"system","content":SYS},{"role":"user","content":msg}],"think":False,"stream":False,"format":"json","options":{"temperature":0.0,"num_predict":200,"num_ctx":8192}}
    try: res=json.loads(json.load(urllib.request.urlopen(urllib.request.Request('http://localhost:11440/api/chat',json.dumps(body).encode(),{'Content-Type':'application/json'}),timeout=300))['message']['content'])['ratings']
    except Exception as e: res={'_err':str(e)}
    out.append({'cycle_id':cid,'map':lab,'ratings':res})
json.dump(out,open('docs/lab/J-4115_data/judge.json','w'),ensure_ascii=False,indent=1)
sc={}
for o in out:
    if '_err' in o['ratings']: continue
    for k,a in o['map'].items():
        try: sc.setdefault(a,[]).append(float(o['ratings'][k]))
        except Exception: pass
for a,v in sc.items(): print(a,'n=%d mean=%.2f'%(len(v),sum(v)/len(v)))
