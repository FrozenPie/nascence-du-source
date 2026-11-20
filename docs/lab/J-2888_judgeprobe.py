import sys, asyncio, time, aiohttp
sys.path.insert(0, r"C:\Nascence")
from core import judge_panel as jp, ground_grade as gg
async def main():
    async with aiohttp.ClientSession() as s:
        for name, url in (("falcon", jp.JUDGE_2), ("granite", jp.TIEBREAK)):
            t = time.time()
            r = await jp._ask(s, url, gg.Q2_SYSTEM, gg.build_user("The cold grate holds the room's quiet weight.", "A cold grate is a metal grille; metal conducts heat away from air, which is why it feels cold."), "names_mechanism", timeout=200, num_predict=200)
            print(name, url, r, round(time.time() - t, 1), flush=True)
asyncio.run(main())
