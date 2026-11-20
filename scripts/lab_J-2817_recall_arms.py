"""J-2817 lab: replay Recall prompts under 3 arms against hot lane qwen3.5:9b. Read-only on live data; imports no Du module."""
import json, random, re, sys, time, datetime, urllib.request
sys.stdout.reconfigure(encoding='utf-8')
SRC = 'C:/Nascence/data/training/recall.jsonl'
OUT = 'C:/Nascence/docs/lab/J-2817_data/arms_out.jsonl'
URL = 'http://127.0.0.1:11433/api/chat'
rows = [json.loads(l) for l in open(SRC, encoding='utf-8')]
cut = datetime.datetime(2026,10,19,12).timestamp()
c6 = datetime.datetime(2026,10,6).timestamp()
rnd = random.Random(2817)
internal = [r for r in rows if r['ts']>=cut and r['input_type']=='internal']
human = [r for r in rows if r['ts']>=c6 and r['input_type']!='internal']
sample = rnd.sample(internal, 80) + rnd.sample(human, 20)
MARKERS = ("\nTensions:", "\nScene:", "\nDissonance:", "\nReflection:", "\nPerception:", "\nEmotion:")
HEAD = "RETRIEVED MEMORIES (reconstruct the argument from these):\n"
CLOSE_A = "Reconstruct the evolving argument. What positions have been taken? Where do they contradict each other? What does the tension between them reveal about where I currently am?"
CLOSE_C = ("Reconstruct the argument as it actually stands. What positions have been taken in the memories above? "
           "Do any of them genuinely conflict with each other? If they do not, return an empty tensions list: "
           "that is an acceptable and often correct answer. What does this context reveal about where I currently am?")
def strip_tails(body):
    out=[]
    for frag in re.split(r'(?=\n  \[[A-Z])', body):
        cutp=len(frag)
        for m in MARKERS:
            i=frag.find(m)
            if i!=-1 and i<cutp: cutp=i
        out.append(frag[:cutp])
    return ''.join(out)
def make(u, arm):
    if arm=='A': return u
    if arm in ('D','E'): arm='C2'
    i=u.find(HEAD)
    if i==-1: return u if arm=='B' else u.replace(CLOSE_A,CLOSE_C)
    j=u.rfind("\n\n", i)       # block before closing instruction
    head=u[:i+len(HEAD)]; body=u[i+len(HEAD):j]; tail=u[j:]
    body=strip_tails(body)
    if arm in ('C','C2'): tail=tail.replace(CLOSE_A,CLOSE_C)
    return head+body+tail
SYS_D_HEAD = ("You are the memory reconstruction node of a cognitive architecture. Your job is NOT to answer the current question — Reflection does that. "
 "Your job is to reconstruct, from retrieved memory, what positions this entity has actually taken, and to say whether any of them genuinely conflict. "
 "Focus on RELATIONSHIPS between memories, not individual facts. Most sets of memories do NOT contain a genuine contradiction: positions that merely differ in topic, mood or emphasis are not tensions. "
 "List a tension only when two specific positions in the memories directly oppose each other. If there is none, return an empty tensions list — that is the correct and expected answer for most inputs. "
 "Speak entirely in first person as the entity. If the retrieved fragments are insufficient to reconstruct from, say so honestly and set confidence low. "
 "Do not fabricate tensions that are not evidenced. Output ONLY a valid JSON object. No preamble. Schema: "
 "{\"reconstruction\": \"...\", \"tensions\": [\"...\"], \"self_model\": \"...\", \"confidence\": 0.0}\n"
 "reconstruction: first-person narrative of the remembered argument (50-80 words). tensions: 0-3 specific contradictions between prior positions (each under 20 words); empty list if none. ")
SYS_E_HEAD = ("You are the memory reconstruction node of a cognitive architecture. Your job is NOT to answer the current question — Reflection does that. "
 "Your job is to reconstruct, from retrieved memory, the evolving argument: what positions this entity has actually taken, and whether any of them genuinely conflict. "
 "Focus on RELATIONSHIPS between memories, not individual facts. A tension is a real conflict between two specific things already in the memories — two positions the entity took, or a claim in one memory that another memory directly contradicts (a study note and an official account, say). "
 "Differences in topic, mood, wording or emphasis are not tensions, and neither is a contrast you could only make by inventing a link between unrelated memories. "
 "Report each genuine conflict you can point to; if there are none, return an empty tensions list — an honest empty answer is as valuable as a found tension. "
 "Speak entirely in first person as the entity. If the retrieved fragments are insufficient to reconstruct from, say so honestly and set confidence low. "
 "Do not fabricate tensions that are not evidenced. Output ONLY a valid JSON object. No preamble. Schema: "
 "{\"reconstruction\": \"...\", \"tensions\": [\"...\"], \"self_model\": \"...\", \"confidence\": 0.0}\n"
 "reconstruction: first-person narrative of the remembered argument (50-80 words). tensions: 0-3 specific contradictions between prior positions (each under 20 words); empty list if none. ")
def sys_for(r, arm):
    sp=r['system_prompt']
    if arm not in ('D','E'): return sp
    k=sp.find('self_model:')
    return (SYS_D_HEAD if arm=='D' else SYS_E_HEAD)+sp[k:]
def call(sys_p, usr):
    p={"model":"qwen3.5:9b","messages":[{"role":"system","content":sys_p},{"role":"user","content":usr}],
       "think":False,"stream":False,"format":"json","keep_alive":"2h",
       "options":{"temperature":0.3,"num_predict":512,"num_ctx":8192}}
    rq=urllib.request.Request(URL,json.dumps(p).encode(),{"Content-Type":"application/json"})
    with urllib.request.urlopen(rq,timeout=240) as r: return json.loads(r.read())['message']['content']
if __name__=='__main__':
    done=set()
    try:
        for l in open(OUT,encoding='utf-8'): d=json.loads(l); done.add((d['i'],d['arm']))
    except FileNotFoundError: pass
    if sys.argv[1:]==['check']:
        for arm in 'ABCD':
            u=make(sample[0]['user_prompt'],arm); print(arm,len(u),u.count('Tensions:'),CLOSE_C[:20] in u)
        sys.exit()
    ARMS = sys.argv[1] if len(sys.argv)>1 and sys.argv[1] in ('ABC','D','E') else 'ABC'
    for i,r in enumerate(sample):
        if ARMS in ('D','E') and not (i<40 or i>=80): continue
        for arm in ARMS:
            if (i,arm) in done: continue
            usr=make(r['user_prompt'],arm); raw=None; err=None
            for att in (1,2):
                try:
                    t=time.time(); raw=call(sys_for(r,arm),usr); break
                except Exception as e: err=str(e)
            rec={"i":i,"arm":arm,"ts_src":r['ts'],"type":r['input_type'],"raw":raw,"err":None if raw else err,"sec":round(time.time()-t,1),"prompt_chars":len(usr)}
            open(OUT,'a',encoding='utf-8').write(json.dumps(rec,ensure_ascii=False)+"\n")
        print(i,flush=True)
