import json,urllib.request,time,sys
for i in range(8):
    for u,m in [("http://localhost:11433","qwen3.5:9b"),("http://localhost:11439","gemma4:12b"),("http://localhost:11440","falcon3:7b")]:
        t=time.time()
        b={"model":m,"stream":False,"options":{"num_predict":10},"messages":[{"role":"user","content":'say hi'}]}
        r=urllib.request.Request(u+"/api/chat",json.dumps(b).encode(),{"Content-Type":"application/json"})
        try:
            json.load(urllib.request.urlopen(r,timeout=60)); print(i,m,"OK",round(time.time()-t,1),flush=True)
        except Exception as e: print(i,m,"FAIL",flush=True)
