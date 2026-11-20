# J-3313 pass 2: judge runner against Ramses command-r7b (LAN-HOST:11441), checkpointed, resumable.
import json,re,sys,urllib.request,time,os
URL='http://LAN-HOST:11441/api/chat'; M='command-r7b'
S=json.load(open('docs/lab/J-3313_sample200.json'))
OUT='docs/lab/J-3313_judged200_pB.json'
P=("Read the first-person passage and decide how it FEELS to the writer: heavy/dark/anxious/sad/aching (negative) or light/warm/hopeful/settled (positive). "
"Most reflective writing leans one way or the other; use 0 only if it is truly flat. Rate -2 (clearly negative), -1 (leaning negative), 0 (flat), +1 (leaning positive), +2 (clearly positive). "
"Reply with ONLY JSON: {\"valence\": <integer -2..2>}.\n\nTEXT:\n")
def ask(t):
    err=None
    for a in range(3):
        try:
            b=json.dumps({"model":M,"stream":False,"options":{"temperature":0,"num_predict":30},"messages":[{"role":"user","content":P+t}]}).encode()
            r=json.load(urllib.request.urlopen(urllib.request.Request(URL,b,{'Content-Type':'application/json'}),timeout=60))
            c=r['message']['content']
            m=re.search(r'"?valence"?\s*:\s*\+?(-?\d)',c) or re.fullmatch(r'\s*\+?(-?\d)\s*',c)
            return (int(m.group(1)) if m else None), c[:60]
        except Exception as e: err=e; time.sleep(2)
    return None,'ERR '+str(err)[:60]
done={}
if os.path.exists(OUT): done={r['cycle_id']:r for r in json.load(open(OUT))}
n=int(sys.argv[1]) if len(sys.argv)>1 else 200
out=[]
for i,r in enumerate(S[:n]):
    if r['cycle_id'] in done and 'j_full' in done[r['cycle_id']]: out.append(done[r['cycle_id']]); continue
    r=dict(r); r['j_trunc'],r['raw_t']=ask(r['draft'][:420]); r['j_full'],r['raw_f']=ask(r['draft'][:1800]); out.append(r)
    if i%20==0: json.dump(out,open(OUT,'w')); print(i,flush=True)
json.dump(out,open(OUT,'w'))
print('done',sum(r['j_trunc'] is None for r in out),sum(r['j_full'] is None for r in out))
