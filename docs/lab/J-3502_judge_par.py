"""J-3502 parallel judge: resumes docs/lab/J-3502_data/judge.jsonl; gemma4:12b on :11439. argv[1]=workers, argv[2]=max seconds"""
import json,os,sys,time,threading,requests
from concurrent.futures import ThreadPoolExecutor
sys.stdout.reconfigure(encoding='utf-8')
OUT='C:/Nascence/docs/lab/J-3502_data'; jp=OUT+'/judge.jsonl'
J_SYS=("You are judging a piece of self-reflection. You see a THOUGHT and a REFLECTION written about it. Answer: does the reflection "
"point at something particular in this thought (an image, claim, or step) AND add no motive, feeling or reason that the thought does not itself state? "
'Be strict. Output ONLY JSON: {"particular": true or false, "adds_motive": true or false}')
import re
jd={(json.loads(l)['i'],json.loads(l)['v']) for l in open(jp,encoding='utf-8')} if os.path.exists(jp) else set()
todo=[json.loads(l) for l in open(OUT+'/gen.jsonl',encoding='utf-8')]
todo=[g for g in todo if g['refl'] and (g['i'],g['v']) not in jd]
# order by thought index so partial runs cover whole thoughts across all 4 variants
todo.sort(key=lambda g:g['i'])
lock=threading.Lock(); t0=time.time(); lim=float(sys.argv[2])
def work(g):
    if time.time()-t0>lim: return
    try:
        r=requests.post('http://localhost:11439/api/chat',json={"model":"gemma4:12b","messages":[{"role":"system","content":J_SYS},{"role":"user","content":f'THOUGHT: "{g["thought"]}"\nREFLECTION: "{g["refl"]}"'}],"stream":False,"options":{"temperature":0.0,"num_predict":60}},timeout=600)
        raw=r.json()['message']['content']
    except Exception as e: return
    try: m=json.loads(re.search(r"\{.*\}",raw,re.S).group(0))
    except Exception: m={}
    with lock: open(jp,'a',encoding='utf-8').write(json.dumps({'i':g['i'],'v':g['v'],'particular':m.get('particular'),'adds_motive':m.get('adds_motive'),'raw':raw},ensure_ascii=False)+'\n')
with ThreadPoolExecutor(int(sys.argv[1])) as ex: list(ex.map(work,todo))
print('done',time.time()-t0)
