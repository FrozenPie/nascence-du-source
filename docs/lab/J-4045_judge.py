import json, requests, time, re
S=json.load(open('docs/lab/J-4045_sample.json'))
URL='http://LAN-HOST:11441/api/chat'
SYS="You are a strict relevance rater. Answer with exactly one word: YES or NO."
res=[]
for i,s in enumerate(S):
    p=("A mind is replying to an input. Below are the INPUT, the DRAFT reply so far, and one MEMORY fragment that was retrieved.\n\n"
       f"INPUT: {s['raw_input'][:700]}\n\nDRAFT: {s['draft'][:900]}\n\nMEMORY: {s['best']['content'][:700]}\n\n"
       "Would this memory be genuinely relevant and useful for improving or grounding the reply to this input (shares the specific topic or situation, not just a vague mood or generic theme)? Answer YES or NO.")
    body={"model":"command-r7b","stream":False,"options":{"temperature":0},"messages":[{"role":"system","content":SYS},{"role":"user","content":p}]}
    ans=None
    for t in range(2):
        try:
            r=requests.post(URL,json=body,timeout=120); ans=r.json()['message']['content']; break
        except Exception as e: ans='ERR '+str(e)[:80]; time.sleep(3)
    m=re.search(r'\b(YES|NO)\b',ans.upper())
    res.append(dict(cycle_id=s['cycle_id'],sim=s['best']['sim'],verdict=m.group(1) if m else 'UNPARSED',raw=ans[:200]))
    print(i,res[-1]['verdict'],round(s['best']['sim'],2),flush=True)
json.dump(res,open('docs/lab/J-4045_results.json','w'),indent=1)
from collections import Counter
c=Counter(r['verdict'] for r in res); print(c)
