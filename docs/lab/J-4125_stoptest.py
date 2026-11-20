import json, time, requests, sys
sys.stdout.reconfigure(encoding="utf-8")
inp=json.load(open(r"C:\Nascence\docs\lab\J-4125_data\inputs.json",encoding="utf-8"))
for arm in ("D",):
    for stop in (None,["\n\n","  "]):
        p={"model":"mixtral:8x7b","stream":False,"keep_alive":"30m","messages":[{"role":"system","content":inp["systems"][arm]},{"role":"user","content":inp["prompts"]["2"][arm]}],"options":{"temperature":0.1,"num_predict":350,"num_gpu":0},"format":"json"}
        if stop: p["options"]["stop"]=stop
        t=time.time(); r=requests.post("http://LAN-HOST:11438/api/chat",json=p,timeout=300).json()
        print(arm,stop,round(time.time()-t,1),repr(r["message"]["content"][:400]),flush=True)
