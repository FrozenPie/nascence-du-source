import asyncio, json, sys, time
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Nascence"); sys.path.insert(0, str(ROOT))
import core
from core import episodic_buffer_judge as ebj
async def main():
    out=[]
    for c in ebj.control_cases():
        served={}
        t=time.time()
        v=await ebj.judge_scene(c["streams"],c["scene"],c["dissonance"],served)
        dt=time.time()-t
        ok = isinstance(v,dict) and v["supported"]==c["expect_supported"] and v["scene_invented"]==c["expect_scene_invented"]
        out.append({"case":c["name"],"secs":round(dt,1),"matched":ok,"verdict":v,"served":served,"user_chars":len(ebj.build_user(c["streams"],c["scene"],c["dissonance"]))})
        print(json.dumps(out[-1]),flush=True)
    Path("C:/Nascence/docs/lab/J-4106_timing.json").write_text(json.dumps(out,indent=1),encoding="utf-8")
asyncio.run(main())
