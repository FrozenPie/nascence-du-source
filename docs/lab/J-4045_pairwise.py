import json, requests, random, re, time
S=json.load(open('docs/lab/J-4045_sample.json'))
rng=random.Random(4045); URL='http://LAN-HOST:11441/api/chat'
res=[]
for i,s in enumerate(S):
    other=S[(i+11)%len(S)]['best']['content']
    real=s['best']['content']; flip=rng.random()<0.5
    A,B=(other,real) if flip else (real,other)
    p=(f"INPUT: {s['raw_input'][:700]}\n\nDRAFT: {s['draft'][:900]}\n\nMEMORY A: {A[:600]}\n\nMEMORY B: {B[:600]}\n\n"
       "Which memory is more specifically relevant to this input and draft (shared topic or situation)? Answer with exactly one letter: A or B.")
    body={"model":"command-r7b","stream":False,"options":{"temperature":0},"messages":[{"role":"user","content":p}]}
    ans='ERR'
    for t in range(2):
        try: ans=requests.post(URL,json=body,timeout=120).json()['message']['content']; break
        except Exception as e: time.sleep(3)
    m=re.search(r'\b([AB])\b',ans.strip().upper()); pick=m.group(1) if m else None
    correct = pick is not None and ((pick=='B')==flip)
    res.append(dict(cycle_id=s['cycle_id'],flip=flip,pick=pick,correct=correct))
json.dump(res,open('docs/lab/J-4045_pairwise_results.json','w'),indent=1)
n=sum(r['correct'] for r in res); print('real preferred',n,'/',len(res),'unparsed',sum(r['pick'] is None for r in res),'pickB',sum(r['pick']=='B' for r in res))
