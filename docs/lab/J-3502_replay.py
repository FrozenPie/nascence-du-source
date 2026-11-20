"""J-3502: replay P-0042 _SYSTEM old/A/B/C on 40 past thoughts. Pure HTTP to local hubs; imports no Du module,
writes only docs/lab/J-3502_data/. Resumable."""
import json, re, sys, os, time, requests
sys.stdout.reconfigure(encoding='utf-8')
ROOT='C:/Nascence'; OUT=ROOT+'/docs/lab/J-3502_data'; os.makedirs(OUT,exist_ok=True)
GEN='http://localhost:11433/api/chat'; GMODEL='qwen3.5:9b'
JUDGE='http://localhost:11439/api/chat'; JMODEL='gemma4:12b'
doc=open(ROOT+'/docs/staged/p0042_system_rewrite_draft_J-3488.md',encoding='utf-8').read()
blocks=re.findall(r"```\n(.*?)```",doc,re.S)
old,B,C=blocks[0].strip(),blocks[1].strip(),blocks[2].strip()
# variant A: old minus the sentence, plus topical-link paragraph (per doc section 4)
sent=" Am I holding this because it's true, or because it's comfortable, safe, or flattering to hold?"
assert sent in old
oldp=old.split("\n\nYou may end up")
A_p1=oldp[0].replace(sent,"")
A_p2=B.split("\n\n")[1]
A=A_p1+"\n\n"+A_p2+"\n\nYou may end up"+oldp[1]
V={'old':old,'A':A,'B':B,'C':C}
for k,v in V.items(): assert '"reflection"' in v, k
rows=[json.loads(l) for l in open(ROOT+'/data/self_interrogation_shadow.jsonl',encoding='utf-8') if '"kind": "interrogate"' in l]
rows=[r for r in rows if len(r['thought'])>=40]
step=len(rows)/40; samp=[rows[int(i*step)] for i in range(40)]
def chat(url,model,sys_,user,mt,temp):
    for a in range(2):
        try:
            r=requests.post(url,json={"model":model,"messages":[{"role":"system","content":sys_},{"role":"user","content":user}],"stream":False,"think":False,"options":{"temperature":temp,"num_predict":mt}},timeout=400)
            return r.json()['message']['content']
        except Exception as e: err=str(e); time.sleep(3)
    return "ERR "+err
def parse(t,key):
    m=re.search(r"\{.*\}",t,re.S)
    try: return json.loads(m.group(0)).get(key)
    except Exception: return None
gp=OUT+'/gen.jsonl'
done={(json.loads(l)['i'],json.loads(l)['v']) for l in open(gp,encoding='utf-8')} if os.path.exists(gp) else set()
if sys.argv[1]=='gen':
    for i,r in enumerate(samp):
        user=f'The thought: "{r["thought"][:400]}"\nTurn and look at it now.'
        for v,s in V.items():
            if (i,v) in done: continue
            raw=chat(GEN,GMODEL,s,user,180,0.7)
            refl=parse(raw,'reflection')
            open(gp,'a',encoding='utf-8').write(json.dumps({'i':i,'v':v,'thought':r['thought'],'raw':raw,'refl':refl},ensure_ascii=False)+'\n')
        print(i,flush=True)
J_SYS=("You are judging a piece of self-reflection. You see a THOUGHT and a REFLECTION written about it. Answer: does the reflection "
"point at something particular in this thought (an image, claim, or step) AND add no motive, feeling or reason that the thought does not itself state? "
'Be strict. Output ONLY JSON: {"particular": true or false, "adds_motive": true or false}')
if sys.argv[1]=='judge':
    jp=OUT+'/judge.jsonl'
    jd={(json.loads(l)['i'],json.loads(l)['v']) for l in open(jp,encoding='utf-8')} if os.path.exists(jp) else set()
    for l in open(gp,encoding='utf-8'):
        g=json.loads(l)
        if (g['i'],g['v']) in jd or not g['refl']: continue
        raw=chat(JUDGE,JMODEL,J_SYS,f'THOUGHT: "{g["thought"]}"\nREFLECTION: "{g["refl"]}"',60,0.0)
        try: m=json.loads(re.search(r"\{.*\}",raw,re.S).group(0))
        except Exception: m={}
        open(jp,'a',encoding='utf-8').write(json.dumps({'i':g['i'],'v':g['v'],'particular':m.get('particular'),'adds_motive':m.get('adds_motive'),'raw':raw},ensure_ascii=False)+'\n')
