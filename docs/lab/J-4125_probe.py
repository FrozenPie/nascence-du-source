import sys, asyncio, time, aiohttp
sys.path.insert(0, r"C:\Nascence")
from core import judge_panel as jp, ground_grade as gg
T="The cold grate holds the room's quiet weight."
G="A cold grate is a metal grille. It was installed in 1952 by a plumber named Harold, and it conducts heat away from air."
async def main():
    async with aiohttp.ClientSession() as s:
        for name, url in (("cmdr7b","http://LAN-HOST:11441"),("gemma","http://127.0.0.1:11439"),("qwen","http://127.0.0.1:11433"),("falcon","http://127.0.0.1:11440")):
            t=time.time()
            try:
                r = await jp._ask(s,url,gg.Q1_SYSTEM,gg.build_user(T,G),"adds_detail",timeout=170,num_predict=200)
            except Exception as e: r=repr(e)
            print(name,r,round(time.time()-t,1),flush=True)
asyncio.run(main())
