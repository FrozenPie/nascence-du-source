import json, requests, time, re, random, sys
model, url, tag = sys.argv[1], sys.argv[2], sys.argv[3]
S=json.load(open('docs/lab/J-4045_sample.json'))
n=len(S)
frs=[s['best'] for s in S]
rows=[]
for i,s in enumerate(S):
    rows.append(('real',i,s,s['best']))
    rows.append(('ctrl',i,s,frs[(i+7)%n]))
random.Random(4107).shuffle(rows)
SYS="You are a strict relevance rater. Reply with only a single digit 1-5."
res=[]
def ask(p):
    body={"model":model,"stream":False,"options":{"temperature":0,"num_predict":400 if 'gemma4' in model else 20},"messages":[{"role":"system","content":SYS},{"role":"user","content":p}]}
    for t in range(2):
        try:
            return requests.post(url+'/api/chat',json=body,timeout=180).json()['message']['content']
        except Exception as e: err='ERR '+str(e)[:80]; time.sleep(3)
    return err
for k,(kind,i,s,f) in enumerate(rows):
    p=("A mind is replying to an input. Below are the INPUT, the DRAFT reply, and one MEMORY fragment retrieved.\n\n"
       f"INPUT: {s['raw_input'][:700]}\n\nDRAFT: {s['draft'][:900]}\n\nMEMORY: {f['content'][:700]}\n\n"
       "Rate how relevant and useful this memory is for grounding the reply to this input. 1 = unrelated (different topic or situation); 2 = vague shared mood only; 3 = loosely related; 4 = clearly shares the specific topic or situation; 5 = directly about the same situation. Reply with only the digit.")
    a=ask(p); m=re.search(r'[1-5]',a)
    res.append(dict(kind=kind,idx=i,cycle_id=s['cycle_id'],score=int(m.group()) if m else None,raw=a[:80]))
    print(k,kind,res[-1]['score'],flush=True)
json.dump(res,open(f'docs/lab/J-4107_{tag}.json','w'),indent=1)
def rate(kind):
    r=[x['score'] for x in res if x['kind']==kind and x['score']]
    return len(r), sum(1 for v in r if v>=4)/max(1,len(r)), sum(r)/max(1,len(r))
print('REAL',rate('real'),'CTRL',rate('ctrl'))
