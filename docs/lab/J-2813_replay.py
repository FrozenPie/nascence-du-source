"""J-2813: 3-arm emotion replay. Talks only to hubs over HTTP; imports no Du module and writes only docs/lab/J-2813_*."""
import json, re, random, time, datetime, urllib.request, sys, os
sys.stdout.reconfigure(encoding='utf-8')
ROOT = 'C:/Nascence'
OUT = ROOT + '/docs/lab/J-2813_data'
os.makedirs(OUT, exist_ok=True)
rows = [json.loads(l) for l in open(ROOT + '/data/training/emotion.jsonl', encoding='utf-8')]
rx = re.compile(r'bank the fire|stop for a while|bug fixes|upgrades')
cut = datetime.datetime(2026, 8, 20).timestamp()
human = [r for r in rows if r['input_type'] == 'human' and r['ts'] > cut]
farewell = [r for r in human if rx.search(r['raw_input'])]
fids = {r['cycle_id'] for r in farewell}
rest = [r for r in human if r['cycle_id'] not in fids]
random.seed(2813)
control = random.sample(rest, 50)
PRIOR = re.compile(r'^BEFORE YOU APPRAISE.*?\n\n', re.S)

def arm_prompt(r, arm):
    p = r['user_prompt']
    if arm == 'A': return p
    if arm == 'C': return PRIOR.sub('', p, count=1)
    if arm == 'B':
        words = f'The words themselves: "{r["raw_input"][:400]}"'
        lines = p.split('\n')
        for i, l in enumerate(lines):
            if l.startswith('Summary:'):
                lines.insert(i + 1, words); return '\n'.join(lines)
        return p + '\n' + words

def chat(url, model, system, user, tries=2, max_tokens=300):
    body = {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "think": False, "stream": False, "format": "json", "keep_alive": "2h",
            "options": {"temperature": 0.2, "num_predict": max_tokens, "num_ctx": 8192}}
    for t in range(tries):
        try:
            req = urllib.request.Request(url + '/api/chat', json.dumps(body).encode(), {'Content-Type': 'application/json'})
            c = json.load(urllib.request.urlopen(req, timeout=180))['message']['content']
            return json.loads(c)
        except Exception as e:
            err = str(e)
    return {'_error': err}

HOT = 'http://localhost:11433'
res = []
fn = OUT + '/replay.jsonl'
done = {}
if os.path.exists(fn):
    for l in open(fn, encoding='utf-8'):
        d = json.loads(l); done[(d['cycle_id'], d['arm'])] = d
f = open(fn, 'a', encoding='utf-8')
for grp, rs in (('farewell', farewell), ('control', control)):
    for r in rs:
        for arm in 'ABC':
            if (r['cycle_id'], arm) in done: continue
            out = chat(HOT, 'qwen3.5:9b', r['system_prompt'], arm_prompt(r, arm))
            d = {'cycle_id': r['cycle_id'], 'group': grp, 'arm': arm, 'ts_src': r['ts'], 'stored': r['output'], 'out': out,
                 'has_prior': 'BEFORE YOU APPRAISE' in r['user_prompt']}
            f.write(json.dumps(d, ensure_ascii=False) + '\n'); f.flush()
print('done', len(farewell), len(control))
