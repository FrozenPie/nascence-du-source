import sys, os, collections, importlib, bisect, json, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
A = importlib.import_module("J-2536_audit")
frags, fc, wc, cut = A.load_frags()
T = A.load_tuples()
by = collections.defaultdict(list)
for t in T: by[t["source"]].append((t["ts"], A.norm(t["thought"])[:70]))
for s in by: by[s].sort()
res = collections.defaultdict(lambda: collections.Counter())
big = []
for fid, r in fc.items():
    if not r[0].startswith("experienced:"): continue
    f = frags.get(fid)
    if not f: continue
    o = f[0]; src = r[0].split(":",1)[1]
    d_frag = f[1] - r[1]   # fragment timestamp now vs stamped tuple_ts
    res[src]["n"] += 1
    if abs(d_frag) > 1: res[src]["frag_ts_moved_gt1s"] += 1
    if abs(d_frag) > 3600: res[src]["frag_ts_moved_gt1h"] += 1
    # real snapshot time: nearest same-source tuple with same prefix to tuple_ts
    arr = by.get(src, [])
    pr = A.norm(f[2])[:70]
    lo = bisect.bisect_left(arr, (r[1]-3600,)); hi = bisect.bisect_right(arr, (r[1]+3600,))
    cands = [a for a in arr[lo:hi] if a[1] and a[1] in f[2] or (a[1] and pr.startswith(a[1][:30]))]
    if not cands: res[src]["no_stamp_tuple_in_1h"] += 1; continue
    best = min(cands, key=lambda a: abs(a[0]-r[1]))
    dd = abs(best[0]-r[1])
    if dd > 5: res[src]["stamp_vs_tuple_ts_gt5s"] += 1
    if dd > 60: res[src]["stamp_vs_tuple_ts_gt60s"] += 1
    if dd > 3600: res[src]["stamp_vs_tuple_ts_gt1h"] += 1
tot = collections.Counter()
for s,v in sorted(res.items(), key=lambda kv: -kv[1]["n"]):
    tot.update(v)
    print(s, dict(v))
print("TOTAL", dict(tot))
json.dump({s: dict(v) for s, v in res.items()}, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "J-2536_out_drift.json"), "w"), indent=1)
