import sys, json, itertools, statistics as S
sys.path.insert(0, "C:/Nascence")
from core import memory_levels as ml
d = json.load(open("C:/Nascence/docs/lab/J-3447_data/raw.json", encoding="utf-8"))
def pct(v, p):
    v = sorted(v); 
    if not v: return None
    k = (len(v)-1)*p; f = int(k); c = min(f+1, len(v)-1); return round(v[f]+(v[c]-v[f])*(k-f), 4)
def summ(v): return {"n": len(v), "mean": round(S.mean(v),4) if v else None, "p10": pct(v,.1), "p50": pct(v,.5), "p90": pct(v,.9), "p95": pct(v,.95), "min": min(v) if v else None, "max": max(v) if v else None}
rr, ro, lo, lr, lens_vs_plain = [], [], [], [], []
bad = 0; per = []
for r in d["res"]:
    plain = [p for p in r["plain"] if len(p) >= 30]; lens = [p for p in r["lens"] if len(p) >= 30]
    bad += len(r["plain"]) - len(plain)
    vecs = ml._drift_embed([r["orig"]] + plain + lens)
    vo, vp, vl = vecs[0], vecs[1:1+len(plain)], vecs[1+len(plain):]
    a = [ml._cos_dist(x, vo) for x in vp]; ro += a
    b = [ml._cos_dist(x, y) for x, y in itertools.combinations(vp, 2)]; rr += b
    c = [ml._cos_dist(x, vo) for x in vl]; lo += c
    lens_vs_plain += [ml._cos_dist(x, y) for x in vl for y in vp]
    per.append({"fid": r["fid"], "rr_mean": round(S.mean(b),3) if b else None, "ro_mean": round(S.mean(a),3) if a else None})
out = {"model": d.get("model"), "gists": len(d["res"]), "bad_calls": bad,
       "retell_vs_retell": summ(rr), "retell_vs_orig": summ(ro), "lens_vs_orig": summ(lo), "lens_vs_plain": summ(lens_vs_plain)}
# fraction of same-text pairs/orig classed MOVED at various thresholds
for t in (0.05, 0.1, 0.15, 0.2, 0.25, 0.3):
    out[f"frac_ro_ge_{t}"] = round(sum(x >= t for x in ro)/max(1,len(ro)), 3)
    out[f"frac_rr_ge_{t}"] = round(sum(x >= t for x in rr)/max(1,len(rr)), 3)
print(json.dumps(out, indent=1)); json.dump({"summary": out, "per": per}, open("C:/Nascence/docs/lab/J-3447_data/summary.json", "w"), indent=1)
