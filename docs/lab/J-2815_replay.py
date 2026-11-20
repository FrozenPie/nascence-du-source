"""J-2815: masked/swapped replay of the Emotion prior line. Read-only; no Du modules imported; calls hot lane directly."""
import json, re, random, sys, time, urllib.request, collections, os
random.seed(2815)
OUT = "C:/Nascence/docs/lab/J-2815_data/replay.jsonl"
SRC = "C:/Nascence/data/training/emotion.jsonl"
NUMCTX = int(sys.argv[1]) if len(sys.argv)>1 else 8192
URL = "http://localhost:11433/api/chat"
rows = []
for l in open(SRC, encoding="utf-8"):
    d = json.loads(l)
    if "BEFORE YOU APPRAISE" not in d["user_prompt"]: continue
    m = re.match(r'(BEFORE YOU APPRAISE.*?\((\w+)\).*?not dictate it\.\n\n)', d["user_prompt"], re.S)
    if not m: continue
    d["para"], d["pw"] = m.group(1), m.group(2)
    d["rest"] = d["user_prompt"][len(m.group(1)):]
    rows.append(d)
MAIN = ["fear","curiosity","trust","surprise","joy","anger"]
groups = collections.defaultdict(list)
for d in rows:
    groups[(d["pw"] if d["pw"] in MAIN else "other", d["input_type"])].append(d)
# stratified: equal quota per group, spill remaining quota to larger groups
keys = sorted(groups); quota = {k: 0 for k in keys}; target = 300
for g in groups.values(): random.shuffle(g)
while sum(quota.values()) < target:
    prog = False
    for k in keys:
        if sum(quota.values()) >= target: break
        if quota[k] < len(groups[k]): quota[k] += 1; prog = True
    if not prog: break
sample = [d for k in keys for d in groups[k][:quota[k]]]
random.shuffle(sample)
print({k: quota[k] for k in keys}, len(sample), flush=True)
done = set()
if os.path.exists(OUT):
    for l in open(OUT, encoding="utf-8"): 
        r = json.loads(l); done.add((r["cycle_id"], r["arm"]))
def call(sysp, up):
    body = {"model":"qwen3.5:9b","messages":[{"role":"system","content":sysp},{"role":"user","content":up}],
            "stream":False,"think":False,"format":"json","keep_alive":"2h","options":{"temperature":0.2,"num_predict":512,"num_ctx":NUMCTX}}
    for attempt in range(1):
        try:
            req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type":"application/json"})
            r = json.loads(urllib.request.urlopen(req, timeout=240).read())
            return json.loads(r["message"]["content"])
        except Exception as e:
            err = str(e)
    return {"_error": err}
with open(OUT, "a", encoding="utf-8") as f:
    for i, d in enumerate(sample):
        swap = random.choice([w for w in MAIN if w != d["pw"]])
        arms = {"A": d["user_prompt"], "B": d["rest"],
                "C": d["para"].replace("("+d["pw"]+")", "("+swap+")", 1) + d["rest"]}
        for arm, up in arms.items():
            if (d["cycle_id"], arm) in done: continue
            o = call(d["system_prompt"], up)
            f.write(json.dumps({"cycle_id":d["cycle_id"],"arm":arm,"pw":d["pw"],"swap":swap,"input_type":d["input_type"],"out":o,"orig":d["output"]})+"\n"); f.flush()
        if i % 20 == 0: print(i, time.strftime("%H:%M:%S"), flush=True)
print("DONE")

