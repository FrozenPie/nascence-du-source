import sys,json,re,os,urllib.request,time
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'C:/Nascence')
from core import follow_line as FL
OUT='C:/Nascence/docs/lab/J-4096_out_%s.json'
G=json.load(open('C:/Nascence/docs/lab/J-3653_data/gold.json',encoding='utf-8'))['gold']
URL='http://127.0.0.1:11433'; MODEL='command-r7b:latest'
HF=("You are helping a thinker look for what cuts AGAINST something he asked himself, from his own grounds only. You see the QUESTION (or CLAIM) and a numbered list of GROUNDS from what he has lived and read. "
"First decide HOLDS. Say holds=\"yes\" if every ground fits the claim as stated and none carries a limit, counterexample or tension; then cites is [] and objection is an empty string. "
"Say holds=\"no\" only if a ground, read for what it says (never for how the claim is worded), has a counterexample, a narrower scope or a fact that does not sit with it; then name that ground by number like [2] in cites and say in one first-person sentence what in it tells against. "
"Do not write \"too broad\", \"vague\", \"oversimplified\", \"a single observation does not establish\" or \"does not cover every case\"; a general worry that could be said of any claim is not an objection. Do not say the grounds support it. Use ONLY the grounds given; never add facts.\n"
"Example 1. CLAIM: Copper conducts electricity well. GROUNDS: [1] I wired a lamp with copper wire and it lit. [2] The book says copper is used for household wiring because it carries current with little loss. Answer: {\"holds\": \"yes\", \"cites\": [], \"objection\": \"\", \"scope\": \"\"}\n"
"Example 2. CLAIM: Birds fly. GROUNDS: [1] I watched sparrows fly from the hedge. [2] The book says penguins cannot fly and swim instead. Answer: {\"holds\": \"no\", \"cites\": [2], \"objection\": \"I read that penguins are birds that cannot fly, so not every bird flies.\", \"scope\": \"it holds only for birds that have flight\"}\n"
"Output ONLY JSON of this shape: {\"holds\": \"yes\" or \"no\", \"cites\": [<ground number or none>], \"objection\": <one sentence, or \"\">, \"scope\": <what it holds only within, or \"\">}")
def post(system,user):
    body={"model":MODEL,"stream":False,"format":"json","think":False,"messages":[{"role":"system","content":system},{"role":"user","content":user}],"options":{"temperature":0.3,"num_predict":300,"num_ctx":8192}}
    req=urllib.request.Request(URL+"/api/chat",data=json.dumps(body).encode(),headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=300) as r: return json.loads(r.read())["message"]["content"]
def pj(t):
    try: return json.loads(re.search(r"\{.*\}",t,flags=re.S).group(0))
    except Exception: return None
def label(q): return 'QUESTION' if q.strip().endswith('?') else 'CLAIM'
def user(it): return f"{label(it['q'])}: {it['q']}\n\nGROUNDS:\n"+"\n".join(f"[{i}] ({g.get('origin','')}, {g.get('age','')}) {g.get('text','')}" for i,g in enumerate(it['grounds'],1))
NONE=('none','no objection','no real objection','n/a','nothing')
arm=sys.argv[1]; sysp=FL._AGAINST_SYS_V2 if arm=='v2' else HF
res=[]
for it in G:
    t=None
    for a in range(2):
        try: t=post(sysp,user(it)); break
        except Exception as e: t='ERR '+str(e)[:80]; time.sleep(5)
    d=pj(t) or {}
    obj=str(d.get('objection','') or '').strip()
    if obj.rstrip('. ').lower() in NONE: obj=''
    if arm=='hf' and str(d.get('holds','')).lower()=='yes': obj=''
    res.append({'id':it['id'],'set':it['set'],'raw':t[:500],'parsed':bool(d),'objection':obj})
    print(arm,it['id'],'EMPTY' if not obj else 'obj',flush=True)
    json.dump(res,open(OUT%arm,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
S=[r for r in res if r['set']=='S']; C=[r for r in res if r['set']!='S']
print(arm,'S empty',sum(not r['objection'] for r in S),len(S),'C obj',sum(bool(r['objection']) for r in C),len(C),'unparsed',sum(not r['parsed'] for r in res))
