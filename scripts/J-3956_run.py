import sys, json, time, asyncio, random, os
sys.path.insert(0,'C:/Nascence'); sys.path.insert(0,'C:/Nascence/scripts')
from core import judge_panel as jp
sys.path.insert(0,'C:/Users/USER/.claude/skills/job-queue')
from lab_env import isolate
import importlib; prep=importlib.import_module('J-3956_prep')
SYS=("You are a strict judge of intellectual progress. A thought ADVANCES a "
     "pursuit only if it adds something genuinely new beyond the pursuit's prior "
     "position: a further step, a consequence, a distinction, evidence, or a "
     "development. Restating the theme in fresh words, circling it, or merely "
     "mentioning it does NOT advance. When uncertain, answer false. Output ONLY "
     'JSON: {"advances": true|false, "why": "<one short clause>"}')
def snap():
    return {f:(os.path.getsize('data/'+f),os.path.getmtime('data/'+f)) for f in os.listdir('data') if os.path.isfile('data/'+f)}
async def main():
    before=snap()
    o=prep.build(); random.seed(3956)
    aff=[a for a in o if a['dedupe'] or a['qlong']]
    ctl=[a for a in o if not a['dedupe'] and not a['qlong']]
    ctl=random.sample([a for a in ctl if a['differs']],12)+random.sample([a for a in ctl if not a['differs']],12)
    sample=aff+ctl
    out=open('docs/lab/J-3956_results.jsonl','w',encoding='utf-8')
    with isolate(also=[(jp,["_LOG","_INPUTS_LOG"])],db="empty") as lab:
        for k,a in enumerate(sample):
            res={}
            for arm in ('old','new'):
                for attempt in range(2):
                    d=await jp.rule_detail(SYS,a[arm],"advances",context=f"J-3956:{a['pid']}")
                    if d.get('verdict') is not None: break
                res[arm]=(d.get('verdict'),d.get('how'))
            rec=dict(i=a['i'],pid=a['pid'],dedupe=a['dedupe'],qlong=a['qlong'],differs=a['differs'],logged=a['old_verdict'],old=res['old'],new=res['new'])
            out.write(json.dumps(rec)+'\n'); out.flush()
            print(k,rec['old'],rec['new'],flush=True)
    after=snap()
    ch=[f for f in after if f not in before or after[f]!=before[f]]
    print("TOPLEVEL_CHANGED",ch)
asyncio.run(main())
