import json,time,urllib.request,sys
for u in ("http://127.0.0.1:11440","http://LAN-HOST:11438"):
    p={"model":"judge","stream":False,"format":"json","messages":[{"role":"user","content":'Reply JSON {"advances": false, "why":"x"}'}],"options":{"temperature":0.0,"num_predict":40}}
    t=time.time()
    try:
        r=urllib.request.urlopen(urllib.request.Request(u+"/api/chat",json.dumps(p).encode(),{"Content-Type":"application/json"}),timeout=170)
        print(u,round(time.time()-t,1),r.read()[:150],flush=True)
    except Exception as e: print(u,round(time.time()-t,1),repr(e),flush=True)
