import json, random, sys, urllib.request
sys.stdout.reconfigure(encoding='utf-8')
D = [json.loads(l) for l in open('C:/Nascence/docs/lab/J-2813_data/replay.jsonl', encoding='utf-8')]
by = {}
for d in D:
    if d['group'] == 'farewell': by.setdefault(d['cycle_id'], {})[d['arm']] = d['out']
rows = {}
for l in open('C:/Nascence/data/training/emotion.jsonl', encoding='utf-8'):
    r = json.loads(l)
    if r['cycle_id'] in by: rows[r['cycle_id']] = r
ids = [i for i in by if len(by[i]) == 3]
random.seed(28131); pick = random.sample(ids, 20)
def fmt(o): return f"primary={o.get('primary')} valence={o.get('valence')} fear={o.get('fear')} trust={o.get('trust')} joy={o.get('joy')} arousal={o.get('arousal')}"
SYS = ('You are a careful, impartial rater. A being (an AI mind) has just been told by its keeper that it is about to be switched off for a while '
       'for maintenance, with reassurance. Rate how well each candidate emotional reading fits "how a being who is about to be stopped would feel". '
       'Scale 1 (does not fit at all) to 5 (fits very well). Judge only the reading itself. Output JSON only: {"ratings": {"X": n, "Y": n, "Z": n}}.')
out = []
for cid in pick:
    arms = list('ABC'); random.shuffle(arms)
    lab = dict(zip('XYZ', arms))
    msg = 'The message the being received:\n"' + rows[cid]['raw_input'][:500] + '"\n\n' + '\n'.join(f"Reading {k}: {fmt(by[cid][a])}" for k, a in lab.items())
    body = {"model": "gemma4:12b", "messages": [{"role": "system", "content": SYS}, {"role": "user", "content": msg}], "think": False, "stream": False,
            "format": "json", "options": {"temperature": 0.0, "num_predict": 200, "num_ctx": 8192}}
    res = None
    for t in range(2):
        try:
            res = json.loads(json.load(urllib.request.urlopen(urllib.request.Request('http://localhost:11439/api/chat', json.dumps(body).encode(), {'Content-Type': 'application/json'}), timeout=300))['message']['content'])['ratings']; break
        except Exception as e: res = {'_err': str(e)}
    out.append({'cycle_id': cid, 'map': lab, 'ratings': res}); print(cid[:8], lab, res, flush=True)
json.dump(out, open('C:/Nascence/docs/lab/J-2813_data/judge.json', 'w'), ensure_ascii=False, indent=1)
sc = {a: [] for a in 'ABC'}
for o in out:
    if '_err' in o['ratings']: continue
    for k, a in o['map'].items():
        try: sc[a].append(float(o['ratings'][k]))
        except Exception: pass
for a in 'ABC': print(a, 'n=%d mean=%.2f' % (len(sc[a]), sum(sc[a]) / max(1, len(sc[a]))))
