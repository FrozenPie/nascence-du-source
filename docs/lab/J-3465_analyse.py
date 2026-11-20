import sys, json, re, random, glob
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Nascence")
items = json.load(open(ROOT/"docs/lab/J-3465_control60.json", encoding="utf-8"))["items"]
byn = {i["n"]: i for i in items}
def norm(t): return re.sub(r"\s+"," ",re.sub(r"[^\w\s]"," ",str(t or "").lower())).strip()
def world(it):
    m = re.search(r"(Recently studied or read.*?)(?:\n\s*\n|\Z)", it["material"].strip(), re.S)
    return m.group(1).strip() if m else ""
STOP=set("the a an of to in and or is are was were do does did how what why which that this these those with for on as by at from be it its their his her can could would should there any specific between into than then about".split())
def toks(s): return [w for w in norm(s).split() if w not in STOP and len(w)>2]
PRES=re.compile(r"\b(reflect|reveal|shape|influence|impact|contribut|alter|represent|relate|redefine|reshape|affect|symbol|metaphor|concept|implication|significance|role)\w*", re.I)
def lex(it):
    q=toks(it["question"]); w=set(toks(world(it)))
    ov=sum(1 for t in q if t in w)/max(1,len(q))
    caps=len(re.findall(r"(?<!^)\b[A-Z][a-z]+", it["question"]))
    pres=len(PRES.findall(it["question"]))
    return ov, caps, pres
def auc(p,n):
    if not p or not n: return None
    return sum(1 if a>b else .5 if a==b else 0 for a in p for b in n)/(len(p)*len(n))
def aucs(sc, pos="good", neg=("bad",)):
    P=[s for n,s in sc.items() if byn[n]["label"]==pos and s is not None]
    N=[s for n,s in sc.items() if byn[n]["label"] in neg and s is not None]
    return auc(P,N)
def boot(sc, neg, B=2000, seed=1):
    rnd=random.Random(seed); ns=[n for n in sc if sc[n] is not None]
    g=[n for n in ns if byn[n]["label"]=="good"]; b=[n for n in ns if byn[n]["label"] in neg]
    r=[]
    for _ in range(B):
        P=[sc[rnd.choice(g)] for _ in g]; N=[sc[rnd.choice(b)] for _ in b]; r.append(auc(P,N))
    r.sort(); return r[int(.025*B)], r[int(.975*B)]
def rep(name, sc):
    if sum(v is not None for v in sc.values())<12: return
    n_ok=sum(v is not None for v in sc.values())
    a1=aucs(sc); a2=aucs(sc,neg=("bad","borderline"))
    l1=boot(sc,("bad",)); l2=boot(sc,("bad","borderline"))
    print(f"{name:34s} n={n_ok:2d} AUC(good|bad)={a1:.3f} [{l1[0]:.2f},{l1[1]:.2f}]  AUC(good|bad+bord)={a2:.3f} [{l2[0]:.2f},{l2[1]:.2f}]")
    return a1,a2
def sup_ok(r, it): s=norm((r.get("v") or {}).get("support") or r.get("quote")); return bool(s) and s in norm(world(it))
def scores(tag,var):
    f=ROOT/f"docs/lab/J-3465_raw_{tag}_{var}.jsonl"
    if not f.exists(): return None
    rows=[json.loads(l) for l in f.open(encoding="utf-8") if l.strip()]
    out={}
    for r in rows:
        it=byn[r["n"]]; v=r.get("v")
        d={}
        if var=="V0":
            if isinstance(v,dict) and isinstance(v.get("answerable"),bool) and isinstance(v.get("unsupported_link"),bool):
                ans=v["answerable"] and sup_ok(r,it)
                d={"shipped":int(ans)+int(not v["unsupported_link"]),"ans_only":int(ans),"noLink_only":int(not v["unsupported_link"]),"ans_raw":int(v["answerable"])}
        elif var=="V1":
            if isinstance(v,dict) and isinstance(v.get("score"),(int,float)):
                s=v["score"]; d={"score03":s,"score03_guard":(s if sup_ok(r,it) else min(s,1))}
        elif var=="V2":
            if r.get("quote_ok") and isinstance(v,dict) and isinstance(v.get("answerable"),bool) and isinstance(v.get("unsupported_link"),bool):
                d={"twostep":1+int(v["answerable"])+int(not v["unsupported_link"])}
            elif r.get("err") is None and "quote_ok" in r: d={"twostep":0}
        out[r["n"]]=d
    return out
if __name__=="__main__":
    print("== lexical-only (non-LLM) ==")
    L={i["n"]:lex(i) for i in items}
    rep("overlap",{n:v[0] for n,v in L.items()})
    rep("-presupposed verbs",{n:-v[2] for n,v in L.items()})
    rep("overlap - 0.1*pres",{n:v[0]-0.1*v[2] for n,v in L.items()})
    rep("caps count",{n:v[1] for n,v in L.items()})
    for tag in ("falcon","gemma","yi"):
        for var in ("V0","V1","V2"):
            S=scores(tag,var)
            if not S: continue
            keys=sorted({k for d in S.values() for k in d})
            print(f"== {tag} {var} rows={len(S)} ==")
            for k in keys:
                sc={n:d.get(k) for n,d in S.items()}
                rep(f"{tag}.{var}.{k}",sc)
                if k in("shipped","ans_only","score03_guard","twostep","ans_raw"):
                    rep(f"  +0.5*overlap",{n:(None if v is None else v+0.5*L[n][0]) for n,v in sc.items()})
                    rep(f"  -0.15*presVerbs",{n:(None if v is None else v-0.15*L[n][2]) for n,v in sc.items()})
