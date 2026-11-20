import sys, os, collections, importlib, bisect, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
A = importlib.import_module("J-2536_audit")
frags, fc, wc, cut = A.load_frags()
T = A.load_tuples()
t_first = min(t["ts"] for t in T)
print("first tuple", time.strftime("%F %T", time.localtime(t_first)), "stamp cut", time.strftime("%F %T", time.localtime(cut)))
idle_ts = sorted(t["ts"] for t in T if t["source"] in ("idle","monologue","monologue_train"))
eras = ("pre-census","census-pre-stamp","post-stamp")
def era(ts): return "pre-census" if ts < t_first else ("census-pre-stamp" if ts < cut else "post-stamp")
tab = collections.defaultdict(lambda: collections.Counter())
for fid,(o,ts,ct) in frags.items():
    e = era(ts); c = A.classify(fid, fc)
    tab[o][e+"|"+c] += 1; tab[o]["n"] += 1
    tab["ALL"][e+"|"+c] += 1; tab["ALL"]["n"] += 1
rows = sorted([k for k in tab if k!="ALL"], key=lambda k: -tab[k]["n"])
print("| origin | n | pre-census (none) | census-era pre-stamp: window / none | post-stamp: exact / window / none | post-stamp coverage |")
for k in rows+["ALL"]:
    v = tab[k]
    pe = sum(v[f"{e}|{c}"] for e in ("post-stamp",) for c in ("exact","window"))
    pn = sum(v[f"post-stamp|{c}"] for c in ("exact","window","none"))
    print(f"| {k} | {v['n']} | {v['pre-census|none']+v['pre-census|window']} | {v['census-pre-stamp|window']} / {v['census-pre-stamp|none']} | {v['post-stamp|exact']} / {v['post-stamp|window']} / {v['post-stamp|none']} | {A.pct(pe,pn) if pn else '-'}% |")
# unjoined decomposition
tot_un = sum(1 for fid in frags if A.classify(fid, fc)=="none")
print("total frags", len(frags), "joined", len(frags)-tot_un, "unjoined", tot_un)
dec = collections.Counter()
for fid,(o,ts,ct) in frags.items():
    if A.classify(fid, fc)!="none": continue
    e = era(ts)
    if e=="post-stamp":
        dec["post-stamp:"+o] += 1
    else:
        dec[e] += 1
for k,v in dec.most_common(12): print(k, v)
# size time-only potential for census-pre-stamp unjoined
for W in (30, 300):
    n=tot=0
    byo = collections.Counter(); byt = collections.Counter()
    for fid,(o,ts,ct) in frags.items():
        if A.classify(fid, fc)=="none" and era(ts)=="census-pre-stamp":
            tot+=1; byt[o]+=1
            i=bisect.bisect_left(idle_ts, ts-W)
            if i<len(idle_ts) and idle_ts[i] <= ts+W: n+=1; byo[o]+=1
    print(f"census-pre-stamp unjoined: {tot}; have an idle tuple within +-{W}s (time only): {n} ({A.pct(n,tot)}%)", dict(byo.most_common(6)))
# fc coverage of the experienced layer 'crossed' fields share for reference
