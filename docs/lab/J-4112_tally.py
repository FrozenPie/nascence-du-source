import json, math, collections
rows=[json.loads(l) for l in open(r"C:\Nascence\docs\lab\J-3412_data\judgments_falcon3.jsonl",encoding="utf-8")]
by=collections.defaultdict(dict)
for r in rows:
    if r.get("verdict"): by[r["pair_id"]][r["kind"]]=r
def binom(k,n):
    if n==0: return 1.0
    return min(1.0,2*sum(math.comb(n,i) for i in range(0,min(k,n-k)+1))/2**n)
out={}
for dim in ("faithful","voice","question_open"):
    rw=orig=inc=0; apos=0;tot=0
    for p,d in by.items():
        if len(d)<2: continue
        w=[]
        for k in ("blind","blindswap"):
            r=d[k]; v=r["verdict"].get(dim); 
            if v not in("A","B"): w=None;break
            tot+=1; apos+= v=="A"
            w.append("rewrite" if (v=="A")==r["a_is_rewrite"] else "raw")
        if w is None: continue
        if w[0]==w[1]: 
            if w[0]=="rewrite": rw+=1
            else: orig+=1
        else: inc+=1
    out[dim]=dict(rewrite_wins=rw,raw_wins=orig,inconsistent=inc,p=binom(rw,rw+orig),A_rate=apos/max(tot,1))
print(len(by),json.dumps(out,indent=1))
json.dump(out,open(r"C:\Nascence\docs\lab\J-4112_tally.json","w"))
