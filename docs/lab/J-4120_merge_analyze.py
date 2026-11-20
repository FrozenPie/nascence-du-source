import json, statistics as st
D="C:/Nascence/docs/lab/"
rows=[json.loads(l) for l in open(D+"J-2875_data/J-2875_results.jsonl",encoding="utf-8")]
rg={}
for l in open(D+"J-4120_regrade.jsonl",encoding="utf-8"):
    j=json.loads(l)
    if isinstance(j["grade"],dict): rg[(j["idx"],j["arm"])]=j
def get(r,a):
    x=r[a]; g=x.get("grade")
    if isinstance(g,dict) and g.get("faithful") is not None: return g["faithful"],x.get("commit"),x.get("genuine")
    j=rg.get((r["idx"],a))
    if j and j["grade"].get("faithful") is not None: return j["grade"]["faithful"],j["commit"],j["genuine"]
    return None,None,None
for kind in ("semantic","episodic","ALL"):
    rs=[r for r in rows if kind=="ALL" or r["kind"]==kind]
    out={}
    for a in "AB":
        v=[get(r,a) for r in rs]; gr=[x for x in v if x[0] is not None]
        out[a]=(len(gr),round(st.mean(x[0] for x in gr),3),sum(1 for x in gr if x[1]),sum(x[2] for x in gr))
    pairs=[(get(r,"A"),get(r,"B")) for r in rs]; pp=[(a[0],b[0],a[1],b[1]) for a,b in pairs if a[0] is not None and b[0] is not None]
    print(kind,len(rs),"A(n,mean,commit,genuine)",out["A"],"B",out["B"],"paired n",len(pp),"diff",round(st.mean(b-a for a,b,_,_ in pp),3),
      "commitA",sum(1 for p in pp if p[2]),"commitB",sum(1 for p in pp if p[3]),"B-only",sum(1 for p in pp if p[3] and not p[2]),"A-only",sum(1 for p in pp if p[2] and not p[3]))
for r in rows:
    if r["idx"] in (6,11,12): print("known",r["idx"],get(r,"A"),get(r,"B"))
