import json,re,sys,urllib.request,time
URL='http://localhost:11433/api/chat'; M='command-r7b:latest'
s=json.load(open('docs/lab/J-3313_sample200.json'))
P=("You rate the emotional tone EXPRESSED by a passage of first-person text. Judge only what the text itself expresses, "
"not the topic. Scale: -2 clearly negative (fear, pain, anger, despair, dread), -1 mildly negative (unease, ache, tension, grief), "
"0 neutral or mixed, +1 mildly positive (calm, warmth, trust, contentment), +2 clearly positive (joy, relief, delight). "
"Reply with ONLY JSON: {\"valence\": <integer -2..2>}.\n\nTEXT:\n")
def ask(t):
    for a in range(2):
        try:
            b=json.dumps({"model":M,"stream":False,"options":{"temperature":0,"num_predict":30},"messages":[{"role":"user","content":P+t}]}).encode()
            r=json.load(urllib.request.urlopen(urllib.request.Request(URL,b,{'Content-Type':'application/json'}),timeout=120))
            m=re.search(r'-?\d',r['message']['content'].replace('+',''))
            m=re.search(r'"valence"\s*:\s*([+-]?\d)',r['message']['content'])
            return int(m.group(1)) if m else None
        except Exception as e: err=e; time.sleep(2)
    print('fail',err); return None
for r in s:
    r['j_trunc']=ask(r['draft'][:420]); r['j_full']=ask(r['draft'][:1800])
json.dump(s,open('docs/lab/J-3313_judged200.json','w'))
print('done',sum(r['j_trunc'] is None for r in s),sum(r['j_full'] is None for r in s))
