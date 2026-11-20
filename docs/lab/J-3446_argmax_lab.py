"""J-3446 part 2: which belief does the prefilter actually pick as candidate, and is it the opposite pole?"""
import sys, json, os, re
sys.path.insert(0, r"C:\Nascence"); sys.path.insert(0, r"C:\Users\USER\.claude\skills\job-queue")
sys.stdout.reconfigure(encoding="utf-8")
from core import guidance_learning as gl
import lab_env
D = r"C:\Nascence\data"
beliefs = json.load(open(os.path.join(D,"guidance_beliefs.json"), encoding="utf-8"))
rows = [json.loads(l) for l in open(os.path.join(D,"guidance_shadow_log.jsonl"), encoding="utf-8") if l.strip()]
rows = [r for r in rows if r.get("is_guidance") and len((r.get("principle") or "").strip()) >= 15 and gl._domain(r)=="self"]
RIV = re.compile(r"\b(river|flow|flows|flux|current|fluid|fluidity|transient|shifting|impermanen\w*)", re.I)
BLT = re.compile(r"\b(observer|constant|commit\w*|construct\w*|anchor\w*|stable|durable|single direction|chosen|choose|chooses)", re.I)
def pole(t):
    a, b = bool(RIV.search(t)), bool(BLT.search(t))
    return "fluid" if a and not b else "durable" if b and not a else "mixed" if a and b else "none"
sb = [b for b in beliefs if b.get("domain")=="self" and b.get("status")!="superseded"]
import collections
C = collections.Counter(); ex=[]
with lab_env.isolate(db="empty"):
    for r in rows:
        p=r["principle"].strip(); text=p+" "+(r.get("scope") or""); ts=float(r["ts"])
        cands=[b for b in sb if p not in (b.get("captures") or []) and b.get("principle")!=p and float(b.get("first_ts",0))<ts]
        if not cands: C["no_cands"]+=1; continue
        sc=[(gl._overlap(text,b["principle"]+" "+b.get("scope","")),b) for b in cands]
        best,cb=max(sc,key=lambda x:x[0])
        lp=pole(p); cp=pole(cb["principle"])
        path="lexical" if best>=gl._SIM_RELATED else "none"
        if path=="none":
            sbb,cos=gl._semantic_candidate(text,cands,"self")
            if cos>=gl._SIM_RELATED_EMBED: path="semantic"; cb=sbb; cp=pole(cb["principle"])
        opp = {lp,cp}=={"fluid","durable"}
        C[f"path_{path}"]+=1
        if lp in("fluid","durable"): C[f"lesson_{lp}"]+=1
        if opp: 
            C["opposed_candidate_reaches_gate"]+=1
            if len(ex)<4: ex.append((p[:80],cb["principle"][:80],round(best,2)))
        # opposed belief exists at all for this lesson, vs. chosen
        if lp in("fluid","durable"):
            want="durable" if lp=="fluid" else "fluid"
            if any(pole(b["principle"])==want for b in cands): C["lesson_has_opposite_belief_available"]+=1
print(dict(C)); print(ex)
json.dump({"counts":dict(C),"examples":ex}, open(r"C:\Nascence\docs\lab\J-3446_argmax_result.json","w",encoding="utf-8"),indent=1)
