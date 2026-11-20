"""J-4125 item 4: does ANY thought get null under C or D? Synthetic purely-abstract thoughts (no physical referent) + 2 sample book_person rows."""
import json, time, requests, sys
sys.stdout.reconfigure(encoding="utf-8")
inp=json.load(open(r"C:\Nascence\docs\lab\J-4125_data\inputs.json",encoding="utf-8"))
ctx_prompt = inp["prompts"]["0"]["D"]
head = ctx_prompt[:ctx_prompt.index("The thought to ground:")]
TH = ["I owe Travis an honest answer and I keep postponing it; the delay itself is what I am afraid of.",
      "Is a promise still a promise if nobody remembers making it? I wonder what binds me to my own word.",
      "Gratitude without an object is a strange thing to carry."]
out=open(r"C:\Nascence\data\lab\ground_contract_lab\J-4125_nullprobe.jsonl","a",encoding="utf-8")
for t in TH:
    for arm in ("D","C"):
        u = head + 'The thought to ground:\n  "' + t + '"'
        p={"model":"mixtral:8x7b","stream":False,"keep_alive":"30m","messages":[{"role":"system","content":inp["systems"][arm]},{"role":"user","content":u}],"options":{"temperature":0.1,"num_predict":350,"num_gpu":0},"format":"json"}
        t0=time.time()
        try: c=requests.post("http://LAN-HOST:11438/api/chat",json=p,timeout=400).json()["message"]["content"]
        except Exception as e: c="ERR "+repr(e)[:100]
        out.write(json.dumps({"arm":arm,"thought":t,"content":c,"secs":round(time.time()-t0,1)},ensure_ascii=False)+"\n"); out.flush()
