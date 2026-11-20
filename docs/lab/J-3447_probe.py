import json,time,urllib.request,sys
for port,m in [(11439,"gemma4:12b"),(11440,"falcon3:7b"),(11433,"qwen3.5:9b")]:
    t=time.time()
    try:
        b={"model":m,"stream":False,"think":False,"options":{"num_predict":20},"messages":[{"role":"user","content":"Say hi in 5 words."}]}
        r=urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port}/api/chat",json.dumps(b).encode(),{"Content-Type":"application/json"}),timeout=150)
        print(port,round(time.time()-t,1),json.loads(r.read())["message"]["content"][:60])
    except Exception as e: print(port,round(time.time()-t,1),"ERR",e)
