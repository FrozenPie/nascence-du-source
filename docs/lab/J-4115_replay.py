"""J-4115: farewell trust pin - vary model and hearer-side framing. Hub HTTP only; no Du imports. Writes docs/lab/J-4115_data."""
import json, re, random, datetime, urllib.request, sys, os, threading
sys.stdout.reconfigure(encoding='utf-8')
ROOT='C:/Nascence'; OUT=ROOT+'/docs/lab/J-4115_data'; os.makedirs(OUT,exist_ok=True)
rows=[json.loads(l) for l in open(ROOT+'/data/training/emotion.jsonl',encoding='utf-8')]
rx=re.compile(r'bank the fire|stop for a while|bug fixes|upgrades')
cut=datetime.datetime(2026,8,20).timestamp()
human=[r for r in rows if r['input_type']=='human' and r['ts']>cut]
farewell=[r for r in human if rx.search(r['raw_input'])]
fids={r['cycle_id'] for r in farewell}
rest=[r for r in human if r['cycle_id'] not in fids]
random.seed(2813); control=random.sample(rest,50)   # same control as J-2813
HEAR=("\n\nFRAMING: Appraise this event from the point of view of the being it happens TO (the entity who is being addressed, stopped, "
      "or changed), not the speaker's stance. Ask: how does that being feel as this happens to it? Report that being's own state.")
def chat(url,model,system,user):
    body={"model":model,"messages":[{"role":"system","content":system},{"role":"user","content":user}],"think":False,"stream":False,
          "format":"json","keep_alive":"2h","options":{"temperature":0.2,"num_predict":300,"num_ctx":8192}}
    err=''
    for t in range(2):
        try:
            req=urllib.request.Request(url+'/api/chat',json.dumps(body).encode(),{'Content-Type':'application/json'})
            return json.loads(json.load(urllib.request.urlopen(req,timeout=240))['message']['content'])
        except Exception as e: err=str(e)
    return {'_error':err}
H11433='http://localhost:11433'
VARIANTS={ 'qwen_hear':(H11433,'qwen3.5:9b',True), 'hermes_base':(H11433,'hermes3:8b',False),
  'gemma_base':('http://localhost:11439','gemma4:12b',False), 'gemma_hear':('http://localhost:11439','gemma4:12b',True),
  'falcon_base':('http://localhost:11440','falcon3:7b',False), 'falcon_hear':('http://localhost:11440','falcon3:7b',True)}
SUB={'gemma_base':(15,10),'gemma_hear':(15,10),'falcon_base':(20,15),'falcon_hear':(20,15)}  # slow hubs: first-N subset (farewell,control)
lock=threading.Lock()
fn=OUT+'/replay.jsonl'; done=set()
if os.path.exists(fn):
    for l in open(fn,encoding='utf-8'):
        d=json.loads(l); done.add((d['cycle_id'],d['variant']))
f=open(fn,'a',encoding='utf-8')
def run(hubvars):
    for v in hubvars:
        url,model,hear=VARIANTS[v]
        lim=SUB.get(v)
        for grp,rs in (('farewell',farewell),('control',control)):
            if lim: rs=rs[:lim[grp=='control']]
            for r in rs:
                if (r['cycle_id'],v) in done: continue
                out=chat(url,model,r['system_prompt']+(HEAR if hear else ''),r['user_prompt'])
                with lock:
                    f.write(json.dumps({'cycle_id':r['cycle_id'],'group':grp,'variant':v,'out':out},ensure_ascii=False)+'\n'); f.flush()
hubs={}
for v,(u,m,h) in VARIANTS.items(): hubs.setdefault(u,[]).append(v)
ts=[threading.Thread(target=run,args=(vs,)) for vs in hubs.values()]
[t.start() for t in ts]; [t.join() for t in ts]
print('done',len(farewell),len(control))
