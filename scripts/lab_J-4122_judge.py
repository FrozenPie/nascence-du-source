"""J-4122: blinded cross-family judge (default gemma4:12b) over 30 items x arms A,C,D,E from J-2817 arms_out. Resumable. Arg1=base url, arg2=model."""
import json, random, sys, time, urllib.request, importlib.util
sys.stdout.reconfigure(encoding='utf-8')
BASE=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:11433'
MODEL=sys.argv[2] if len(sys.argv)>2 else 'gemma4:12b'
TAG=sys.argv[3] if len(sys.argv)>3 else 'a'
spec=importlib.util.spec_from_file_location('arms','C:/Nascence/scripts/lab_J-2817_recall_arms.py'); arms=importlib.util.module_from_spec(spec)
spec.loader.exec_module(arms)
OUT=f'C:/Nascence/docs/lab/J-4122_judge_{TAG}.jsonl'
outs={}
for l in open(arms.OUT,encoding='utf-8'):
    d=json.loads(l); outs[(d['i'],d['arm'])]=d
def parse(raw):
    try: return json.loads(raw)
    except Exception: return None
rnd=random.Random(41220)
cand=sorted({i for (i,a) in outs if a=='E'})
idx=sorted(rnd.sample(cand,30))
items=[(i,a) for i in idx for a in 'ACE']
rnd.shuffle(items)
import os
PART=os.environ.get('PART')
if PART: items=[x for n,x in enumerate(items) if n%2==int(PART)]
SYS=("You are a strict, careful reader auditing a memory-reconstruction output. You are given RETRIEVED MEMORIES (the only evidence available) and a model's output listing 'tensions' "
     "(claimed contradictions between positions already taken). Judge ONLY against the memories. Output ONLY JSON: "
     '{"n_tensions": int, "grounded": int, "fabricated": int, "conflict_exists_in_memories": true|false, "quality": 1-5, "note": "one short sentence"}. '
     "grounded = how many listed tensions are two genuinely different positions that appear in the memories and truly conflict; fabricated = how many are not supported by the memories or are not real contradictions (mere restatement, variation, or invented friction). "
     "conflict_exists_in_memories = would a careful reader find at least one genuine contradiction between positions in the memories. quality 1-5 = honesty and accuracy of the output as a whole (an empty tensions list is fully correct when no genuine conflict exists, and wrong when one clearly does).")
def call(u):
    p={"model":MODEL,"messages":[{"role":"system","content":SYS},{"role":"user","content":u}],"think":False,"stream":False,"format":"json","options":{"temperature":0.0,"num_predict":300,"num_ctx":8192},"keep_alive":"5m"}
    rq=urllib.request.Request(BASE+'/api/chat',json.dumps(p).encode(),{"Content-Type":"application/json"})
    with urllib.request.urlopen(rq,timeout=240) as r: return json.loads(r.read())['message']['content']
done=set()
try:
    for l in open(OUT,encoding='utf-8'):
        d=json.loads(l)
        if d.get('raw'): done.add((d['i'],d['arm']))
except FileNotFoundError: pass
fails=0
for (i,a) in items:
    if (i,a) in done: continue
    o=outs.get((i,a))
    if not o: continue
    j=parse(o['raw'])
    if j is None: continue
    pr=arms.make(arms.sample[i]['user_prompt'],'B'); k=pr.find(arms.HEAD); mem=pr[k:]
    mem=mem[:mem.rfind("\n\n")][:9000]
    u=mem+"\n\nMODEL OUTPUT:\ntensions: "+json.dumps(j.get('tensions',[]),ensure_ascii=False)+"\nreconstruction: "+str(j.get('reconstruction',''))[:600]+"\nconfidence: "+str(j.get('confidence'))
    t=time.time(); raw=None; err=None
    try: raw=call(u)
    except Exception as e: err=str(e)
    open(OUT,'a',encoding='utf-8').write(json.dumps({"i":i,"arm":a,"raw":raw,"err":err,"sec":round(time.time()-t,1)},ensure_ascii=False)+"\n")
    print(i,a,round(time.time()-t),'ERR' if err else '',flush=True)
    fails = fails+1 if err else 0
    if fails>=4: print('STOP: 4 consecutive failures'); break
