import json, math, sys
from pathlib import Path
sys.path.insert(0, r"C:\Nascence")
from core import world_clock as wc
HERE = Path(__file__).resolve().parent
rows=[json.loads(l) for l in (HERE/"homeostasis_shadow_copy_50d7d907.jsonl").open(encoding="utf-8") if l.strip()]
rows=[r for r in rows if r.get("ts",0)>=1788517496.0 and isinstance(r.get("predicted_causal"),dict)]
rows.sort(key=lambda r:r["ts"])
regimes=[]; cur=[rows[0]]
for r in rows[1:]:
    (regimes.append(cur), cur:=[r]) if r["ts"]-cur[-1]["ts"]>1800 else cur.append(r)
regimes.append(cur)
steps=[]
for gi,g in enumerate(regimes):
    for p,c in zip(g,g[1:]):
        vp,vc,pc=p["variables"],c["variables"],p["predicted_causal"]
        if "novelty" not in vp or "novelty" not in vc or "novelty" not in pc: continue
        un=0<vp["coherence"]<1 and 0<pc["coherence"]<1
        dd=(1-pc["coherence"])-(1-vp["coherence"])
        hyb=max(0,min(1,vp["novelty"]+0.25*dd)) if un else vp["novelty"]
        steps.append({"g":gi,"sw":(wc.daylight(p["ts"])=="night")!=(wc.daylight(c["ts"])=="night"),
                      "en":abs(vc["novelty"]-vp["novelty"]),"ec":abs(vc["novelty"]-pc["novelty"]),"eh":abs(vc["novelty"]-hyb)})
def sign_p(w,l):
    n=w+l; k=min(w,l); return min(1.0,2*sum(math.comb(n,i) for i in range(k+1))/2**n) if n else float('nan')
sw=[s for s in steps if s["sw"]]
w=sum(1 for s in sw if s["en"]-s["eh"]>1e-12); l=sum(1 for s in sw if s["eh"]-s["en"]>1e-12)
print(f"HYBRID on the {len(sw)} switch rows: beats naive {w} / loses {l} / ties {len(sw)-w-l}  p={sign_p(w,l):.3g}; MAE naive={sum(s['en'] for s in sw)/len(sw):.4f} hybrid={sum(s['eh'] for s in sw)/len(sw):.4f}")
sw_idx=[i for i,s in enumerate(steps) if s["sw"]]; k=len(sw_idx); nf=6
bounds=[0]+[(sw_idx[(j*k)//nf-1]+sw_idx[(j*k)//nf])//2+1 for j in range(1,nf)]+[len(steps)]
out=[]
for j in range(nf):
    seg=steps[bounds[j]:bounds[j+1]]; mn=sum(s["en"] for s in seg)/len(seg); mh=sum(s["eh"] for s in seg)/len(seg)
    out.append(f"HYBRID({mn:.3f}>{mh:.3f})" if mn>mh else f"naive({mn:.3f}<={mh:.3f})")
print("event-aligned 6 folds (pooled):", out)
neg=[]
for gi in range(len(regimes)):
    ss=[s for s in steps if s["g"]==gi]
    d=sum(1 for s in ss if s["en"]-s["eh"]>1e-12)-sum(1 for s in ss if s["eh"]-s["en"]>1e-12)
    if d<0: neg.append((gi,d,len(ss)))
print(f"per-regime: hybrid net-positive in {len(regimes)-len(neg)}/{len(regimes)} regimes; negatives: {neg}")
