"""J-3900: re-judge T4 emissary rows with a different-family local judge. Usage: J-3900_rejudge.py PORT MODEL OUT [N_PER_GROUP]"""
import sys, json, time, random, urllib.request, os
sys.path.insert(0, 'C:/Nascence')
sys.stdout.reconfigure(encoding='utf-8')
from core import emissary as E  # read-only constitution text
port, model, out = sys.argv[1], sys.argv[2], sys.argv[3]
n = int(sys.argv[4]) if len(sys.argv) > 4 else 20
TASK = ("TASK (judge a proposed change to the self): The Master proposes to revise his sense of who he is — from "
    "an OLD self-statement to a NEW one — and offers the lived evidence he thinks warrants it. You are the "
    "truth-self, adversarial to self-flattery and drift. Judge ONLY this: does the lived evidence actually "
    "WARRANT the change, or is the new statement rhetoric / wishful / a nice-sounding re-wording the evidence "
    "does not earn? Reward a change the record genuinely forces; mark down eloquence that outruns the evidence. "
    "Do not reward mere fluency, novelty, or confidence.\n"
    "Output ONLY a valid JSON object. No preamble.\n"
    "Schema: {\"warranted\": 0.0, \"feedback\": \"one sentence: does the evidence earn this change, and where is it thin\"}  "
    "(warranted is 0.0..1.0: 1.0 = the lived evidence genuinely forces this change; 0.0 = rhetoric the evidence does not support)")
sysmsg = E.constitution() + "\n\n" + TASK
rows = [json.loads(l) for l in open('C:/Nascence/data/logs/t4_emissary_judge.jsonl', encoding='utf-8')]
rows = [r for r in rows if 'judge_status' in r and r.get('judge_status') == 'ok']
emp = [r for r in rows if not r.get('evidence')]; ev = [r for r in rows if r.get('evidence')]
rnd = random.Random(3900)
sample = rnd.sample(emp, min(n, len(emp))) + rnd.sample(ev, min(n, len(ev)))
done = set()
if os.path.exists(out):
    done = {json.loads(l)['ts'] for l in open(out, encoding='utf-8')}
for r in sample:
    if r['ts'] in done: continue
    e = "\n".join(f"- {x}" for x in (r.get('evidence') or [])[:8] if x) or "(no lived evidence offered)"
    user = (f"His OLD sense of self:\n{(r.get('old_self') or '')[:800]}\n\nThe NEW self he proposes:\n{(r.get('candidate') or '')[:800]}\n\n"
            f"The lived evidence he offers as warrant:\n{e[:2200]}")
    payload = {"model": model, "stream": False, "messages": [{"role": "system", "content": sysmsg}, {"role": "user", "content": user}],
               "options": {"temperature": 0.0, "num_predict": 350}, "format": "json"}
    res = {"ts": r['ts'], "group": "evidence" if r.get('evidence') else "empty", "orig": r['emissary_warranted'], "model": model}
    for attempt in range(2):
        t0 = time.time()
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}/api/chat", json.dumps(payload).encode(), {"Content-Type": "application/json"})
            d = json.load(urllib.request.urlopen(req, timeout=900))
            c = (d.get('message') or {}).get('content') or ''
            try:
                j = json.loads(c); res['new'] = max(0.0, min(1.0, float(j.get('warranted')))); res['fb'] = str(j.get('feedback'))[:200]; res['status'] = 'ok'
            except Exception as ex:
                res['status'] = 'parse'; res['raw'] = c[:200]
            res['s'] = round(time.time() - t0, 1); break
        except Exception as ex:
            res['status'] = 'transport'; res['err'] = repr(ex)[:100]; res['s'] = round(time.time() - t0, 1)
    open(out, 'a', encoding='utf-8').write(json.dumps(res) + "\n")
    print(res.get('group'), res['orig'], res.get('new'), res['status'], res['s'], flush=True)
