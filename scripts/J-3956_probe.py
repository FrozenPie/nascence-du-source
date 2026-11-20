import sys,time,asyncio,tempfile,pathlib
sys.path.insert(0,'C:/Nascence'); sys.path.insert(0,'C:/Nascence/scripts')
from core import judge_panel as jp
import importlib; prep=importlib.import_module('J-3956_prep')
t=pathlib.Path(tempfile.mkdtemp())
jp._LOG=t/'l.jsonl'; jp._INPUTS_LOG=t/'i.jsonl'; jp._TIMEOUT=300
o=prep.build()
async def m():
    for a in o[:2]:
        s=time.time(); d=await jp.rule_detail("You are a strict judge. Output ONLY JSON: {\"advances\": true|false, \"why\": \"<clause>\"}",a['new'],"advances",context="J-3956:probe")
        print(round(time.time()-s,1),{k:d.get(k) for k in('verdict','how','s1','s2','err1','err2')},flush=True)
asyncio.run(m())
