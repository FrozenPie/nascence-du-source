import json, datetime as dt, collections, sys
P=r"C:\Nascence\data\transport_habituation_shadow.jsonl"
days=collections.OrderedDict()
with open(P,encoding="utf-8") as f:
    for line in f:
        try: r=json.loads(line)
        except Exception: continue
        d=dt.datetime.fromtimestamp(r["ts"]).strftime("%Y-%m-%d")
        s=days.setdefault(d,{"n":0,"real":collections.Counter(),"would":collections.Counter(),"nd":0,"nc":0,"differs":0,"realfired":0,"maxnd":0,"first":r["ts"],"last":r["ts"]})
        s["n"]+=1; s["last"]=r["ts"]
        rw=r.get("real_winner"); ww=r.get("would_winner")
        s["real"][(rw or {}).get("line_id")]+=1; s["would"][(ww or {}).get("line_id")]+=1
        nd=sum(1 for v in r["weights"].values() if v["kind"]!="novelty" and v["raw_weight"]>=1.5)
        s["nd"]+=nd; s["maxnd"]=max(s["maxnd"],nd); s["nc"]+=r["n_candidates"]; s["differs"]+=bool(r.get("differs")); s["realfired"]+=rw is not None
for d,s in days.items():
    top=s["real"].most_common(2); wt=s["would"].most_common(2)
    print(d,s["n"],"cad_s=%.0f"%((s["last"]-s["first"])/max(1,s["n"]-1)),"cands=%.1f"%(s["nc"]/s["n"]),"sd>=1.5/tick=%.2f max=%d"%(s["nd"]/s["n"],s["maxnd"]),"fired=%d differs=%d"%(s["realfired"],s["differs"]),"realdistinct=%d"%len(s["real"]),"top",[(str(k)[:34],v) for k,v in top],"would",[(str(k)[:34],v) for k,v in wt])
