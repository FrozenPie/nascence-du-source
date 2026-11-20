"""J-3536: blind judge on guard-log pairs (raw vs rejected_integrated), reusing J-3150 prompts. Offline; no Du modules.
usage: J-3536_judge.py <judge_name:falcon|gemma> [limit]"""
import sys,json,time,hashlib,importlib.util,urllib.request
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
spec=importlib.util.spec_from_file_location('j3150','C:/Nascence/scripts/lab_deliberation_blind_judge_J-3150.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
J={'mixtral':('http://LAN-HOST:11438','mixtral:8x7b'),'falcon':('http://127.0.0.1:11440','falcon3:7b'),'gemma':('http://127.0.0.1:11439','gemma4:12b')}
name=sys.argv[1];lim=None
shard=int(sys.argv[2]) if len(sys.argv)>2 else 0
nsh=int(sys.argv[3]) if len(sys.argv)>3 else 1
url,model=J[name]
def post(system,user,temperature=0.0,timeout=300):
    body={"model":model,"stream":False,"format":"json","messages":[{"role":"system","content":system},{"role":"user","content":user}],"options":{"temperature":temperature,"num_predict":48}}
    req=urllib.request.Request(url+"/api/chat",data=json.dumps(body).encode(),headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=timeout) as r: return json.loads(r.read())["message"]["content"]
G=[json.loads(l) for l in open('C:/Nascence/data/deliberation_guard_log.jsonl',encoding='utf-8')]
out=Path('C:/Nascence/docs/lab/J-3536_data');out.mkdir(exist_ok=True)
path=out/(f'judgments_{name}.jsonl' if nsh==1 else f'judgments_{name}_s{shard}.jsonl')
shared=out/f'judgments_{name}.jsonl'
done=set()
for pp in [shared,path]:
  if pp.exists():
    for l in open(pp,encoding='utf-8'):
        try:
            r=json.loads(l)
            if r.get('verdict'):done.add(r['key'])
        except:pass
import random
rows=list(G);random.Random(3536).shuffle(rows)
t0=time.time();n=0
for i,g in enumerate(rows):
    if i%nsh!=shard:continue
    pid=hashlib.sha1((repr(g['ts'])+g['raw']).encode()).hexdigest()[:10]
    s={"pair_id":pid,"stratum":"guard","raw":g['raw'],"grounding":g.get('grounding',''),"integrated":g['rejected_integrated'],
       "control_text":"","order_real_a_is_rewrite":m.order_a_is_rewrite(3536,pid,'real'),"order_control_a_is_rewrite":False}
    for kind in ('blind','blindswap'):
        key=f'{pid}|real|{kind}'
        if key in done:continue
        r=m.judge_one({"key":key,"sample":s,"cond":"real","kind":kind},post=post)
        open(path,'a',encoding='utf-8').write(json.dumps(r,ensure_ascii=False)+"\n");n+=1
    if i%20==0:print(i,n,round(time.time()-t0),flush=True)
print('done',n,round(time.time()-t0))
