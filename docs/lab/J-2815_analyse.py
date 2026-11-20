import json, collections, math
R = collections.defaultdict(dict); meta = {}
for l in open("C:/Nascence/docs/lab/J-2815_data/replay.jsonl", encoding="utf-8"):
    r = json.loads(l)
    if "_error" in r["out"]: continue
    R[r["cycle_id"]][r["arm"]] = r["out"]; meta[r["cycle_id"]] = r
ids = [i for i in R if set(R[i]) >= {"A","B","C"}]
print("complete triples", len(ids), "of", len(R))
def lab(o): return str(o.get("primary","")).lower().strip()
def f(o,k):
    try: return float(o.get(k,0))
    except: return 0.0
def rate(xs): 
    n=len(xs); k=sum(xs); p=k/n if n else float('nan')
    se=1.96*math.sqrt(p*(1-p)/n) if n else 0
    return f"{k}/{n}={p:.3f} (+-{se:.3f})"
A=[lab(R[i]["A"])==meta[i]["pw"] for i in ids]
B=[lab(R[i]["B"])==meta[i]["pw"] for i in ids]
C_orig=[lab(R[i]["C"])==meta[i]["pw"] for i in ids]
C_swap=[lab(R[i]["C"])==meta[i]["swap"] for i in ids]
B_swap=[lab(R[i]["B"])==meta[i]["swap"] for i in ids]
A_swap=[lab(R[i]["A"])==meta[i]["swap"] for i in ids]
print("P(label=prior word)  A",rate(A)," B(no prior)",rate(B)," C",rate(C_orig))
print("P(label=swapped word) A",rate(A_swap)," B",rate(B_swap)," C",rate(C_swap))
def mean(a): return sum(a)/len(a) if a else float('nan')
for k in ("valence","arousal","fear","joy","trust"):
    print(k, "A %.3f B %.3f C %.3f"%tuple(mean([f(R[i][a],k) for i in ids]) for a in "ABC"))
print("primary==fear  A %s B %s C %s"%tuple(rate([lab(R[i][a])=="fear" for i in ids]) for a in "ABC"))
print("-- by prior word (n, A=pw, B=pw, C=pw, C=swap)")
for pw in sorted(set(meta[i]["pw"] for i in ids)):
    s=[i for i in ids if meta[i]["pw"]==pw]
    print(pw,len(s),*[round(mean(x),2) for x in ([lab(R[i]["A"])==pw for i in s],[lab(R[i]["B"])==pw for i in s],[lab(R[i]["C"])==pw for i in s],[lab(R[i]["C"])==meta[i]["swap"] for i in s])])
print("-- by input_type")
for it in ("human","internal"):
    s=[i for i in ids if meta[i]["input_type"]==it]
    print(it,len(s),*[round(mean(x),3) for x in ([lab(R[i]["A"])==meta[i]["pw"] for i in s],[lab(R[i]["B"])==meta[i]["pw"] for i in s],[lab(R[i]["C"])==meta[i]["pw"] for i in s],[lab(R[i]["C"])==meta[i]["swap"] for i in s])])
print("valence shift A-B %.3f  C-B %.3f  C-A %.3f"%(mean([f(R[i]["A"],"valence")-f(R[i]["B"],"valence") for i in ids]),mean([f(R[i]["C"],"valence")-f(R[i]["B"],"valence") for i in ids]),mean([f(R[i]["C"],"valence")-f(R[i]["A"],"valence") for i in ids])))
print("label A!=B:", rate([lab(R[i]["A"])!=lab(R[i]["B"]) for i in ids]), " C!=A:", rate([lab(R[i]["C"])!=lab(R[i]["A"]) for i in ids]))
