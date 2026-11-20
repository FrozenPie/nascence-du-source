import json, pickle, sys, collections, time
KEEP=("ts","source","thought","place","weather","cat_at","sounds","warmth","fire","tide_level","standpoint")
rows=[]; bad=0
with open("C:/Nascence/data/geometry_tuples.jsonl",encoding="utf-8") as f:
    for line in f:
        line=line.strip()
        if not line: continue
        try: t=json.loads(line)
        except Exception: bad+=1; continue
        rows.append({k:t.get(k) for k in KEEP})
print(len(rows),"bad",bad)
pickle.dump(rows,open("J-2536_tuples.pkl","wb"))
cnt=collections.Counter(r["source"] for r in rows)
print(cnt.most_common(50))
print(time.strftime("%F",time.localtime(rows[0]["ts"])),time.strftime("%F",time.localtime(rows[-1]["ts"])))
