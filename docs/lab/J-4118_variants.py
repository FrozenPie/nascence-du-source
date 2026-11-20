"""J-4118: replay J-2970 follows battery with _JUDGE_B_SYS rewordings. Read-only, no core import. Resumable."""
import json, sys, time, threading, ast, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); 
import importlib.util
spec = importlib.util.spec_from_file_location("r", str(Path(__file__).parent / "J-2970_replay.py")); r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
ROOT = Path(r"C:\Nascence"); OUT = ROOT/"docs"/"lab"/"J-4118_calls.jsonl"
HUBS = {"falcon3": "http://127.0.0.1:11445", "granite": "http://LAN-HOST:11437"}
TAIL = " Answer ONLY JSON: {\"follows\": true} or {\"follows\": false}."
V = {
 "base": r.sysprompts()["_JUDGE_B_SYS"],
 "v1_observer": ("You judge whether stated CONSEQUENCES really follow from a CLAIM. Test each consequence: would an observer who only read the claim already know it, "
   "or could they get it by rewording the claim? If so it is a restatement and does NOT count. A real consequence is a NEW, specific, checkable fact that would be true if the claim is true "
   "and would likely be false if the claim is false. Vague themes and hedges ('may', 'could be seen as') do not count. Answer true only if at least one consequence passes. When uncertain, answer false." + TAIL),
 "v2_falsifier": ("You judge whether stated CONSEQUENCES really follow from a CLAIM. For each consequence ask two things: (1) Name a concrete observation, different from the claim's own words, that could show the consequence wrong. If none can be named, it is a restatement or a vague theme: reject it. "
   "(2) If the claim were false, would this consequence probably be false too? If it would be true anyway, reject it. Answer true only if at least one consequence passes both tests. When uncertain, answer false." + TAIL),
 "v3_strict_examples": ("You judge whether stated CONSEQUENCES really follow from a CLAIM. Reject a consequence that: says the claim again in other words; only adds a hedge or a general theme; or has no link to the claim. "
   "Accept one that predicts a specific further fact (a person, event, number, or case not named in the claim) which could be checked and would fail if the claim were false. "
   "Example of reject: claim 'X rested on Y' with consequence 'Y was important to X'. Example of accept: a named event that would have gone differently without Y. Answer true only if at least one consequence is accepted. When uncertain, answer false." + TAIL),
}
bat = json.loads((ROOT/"docs"/"lab"/"J-2970_battery.json").read_text(encoding="utf-8"))["follows"]
done=set()
if OUT.exists():
    for l in OUT.read_text(encoding="utf-8").splitlines():
        if l.strip():
            x=json.loads(l)
            if x["verdict"] is not None: done.add((x["hub"],x["id"],x["variant"]))
lock=threading.Lock()
def worker(hub):
    for var,sysm in V.items():
        for d in bat:
            if (hub,d["id"],var) in done: continue
            for a in (1,2):
                v,err,s=r.ask(HUBS[hub],sysm,r.user_b(d),"follows",timeout=120)
                if v is not None: break
                time.sleep(5)
            with lock, open(OUT,"a",encoding="utf-8") as f:
                f.write(json.dumps(dict(hub=hub,id=d["id"],cls=d["cls"],variant=var,verdict=v,err=err,secs=s))+"\n")
ts=[threading.Thread(target=worker,args=(h,)) for h in HUBS]
[t.start() for t in ts];[t.join() for t in ts]
rows=[json.loads(l) for l in OUT.read_text(encoding="utf-8").splitlines() if l.strip()]
rows=[x for x in rows if x["verdict"] is not None]
tab=collections.defaultdict(lambda:[0,0])
for x in rows:
    k=(x["hub"],x["variant"],x["cls"]); tab[k][0]+=x["verdict"]; tab[k][1]+=1
lines=[]
for k in sorted(tab): lines.append(f"{k[0]:8} {k[1]:20} {k[2]:15} yes {tab[k][0]}/{tab[k][1]}")
(ROOT/"docs"/"lab"/"J-4118_summary.txt").write_text("\n".join(lines),encoding="utf-8")
print("\n".join(lines)); print("errors", sum(1 for l in OUT.read_text(encoding='utf-8').splitlines() if '"verdict": null' in l))
