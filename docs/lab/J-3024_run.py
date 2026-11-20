"""J-3024 lab: counterfactual re-judge battery for the dream resolution judge (P-0107). Offline; direct hub calls only,
no core imports, no writes under data/. Resumable: appends one row per finished call to docs/lab/J-3024_calls.jsonl."""
import json, sys, time, urllib.request, os, random
sys.stdout.reconfigure(encoding='utf-8')
HUBS = {'mixtral': 'http://LAN-HOST:11438', 'falcon3': 'http://127.0.0.1:11440', 'granite': 'http://LAN-HOST:11437'}
OUT = 'docs/lab/J-3024_calls.jsonl'
SYSTEM = ("You are an independent reader of a dream-arc narrative \u2014 you did NOT write it. Judge ONLY this: "
    "does the arc's own text show a genuine meeting, reconciliation, or resolution of its central "
    "tension by the end \u2014 or does it end without one (missed, deferred, still unfaced)? Judge the "
    "IMAGERY ITSELF, not any claim made about it. Refute-biased: if the text is ambiguous or you are "
    "not sure, answer false (unresolved).\n"
    "Output ONLY a valid JSON object. No preamble.\n"
    'Schema: {"resolved": true, "why": "one sentence citing what in the text is or is not resolved"}')
def user(arc, core, variant):
    if variant == 'A':   # as-is (pre-J-3019): head cut at 3000, self-report line present
        a = arc[:3000]; sr = True
    elif variant == 'B': # self-report line removed, head cut
        a = arc[:3000]; sr = False
    else:                # C: tail kept (J-3019 behaviour, 5000), self-report present
        a = arc[-5000:]; sr = True
    u = f"The full dream arc, scene by scene:\n{a}\n\n"
    if sr:
        u += ("(The dream's own self-report below is NOT evidence \u2014 judge the text above independently: "
              f"unresolved_core = \"{(core or '')[:200]}\")")
    return u.rstrip()
def ask(url, u):
    payload = {"model": "judge", "stream": False, "format": "json",
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": u}],
        "options": {"temperature": 0.0, "num_predict": 200}}
    t0 = time.time()
    for attempt in (1, 2):
        try:
            req = urllib.request.Request(url + '/api/chat', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
            d = json.load(urllib.request.urlopen(req, timeout=300))
            v = json.loads((d.get('message') or {}).get('content') or '')
            if isinstance(v, dict) and isinstance(v.get('resolved'), bool):
                return v['resolved'], v.get('why'), None, round(time.time() - t0, 1)
            err = 'parse'
        except Exception as e:
            err = type(e).__name__
        time.sleep(5)
    return None, None, err, round(time.time() - t0, 1)
if __name__ == '__main__':
    base = json.load(open('docs/lab/J-3024_sample.json', encoding='utf-8'))
    supp = json.load(open('docs/lab/J-3024_supp.json', encoding='utf-8'))
    units = [(o, v, 'base') for o in base for v in 'AB'] + [(o, v, 'supp') for o in supp for v in 'AC']
    done = set()
    if os.path.exists(OUT):
        for l in open(OUT, encoding='utf-8'):
            r = json.loads(l); done.add((r['dream_id'], r['variant'], r['judge']))
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for judge, url in HUBS.items():
        if only and judge != only: continue
        for o, v, grp in units:
            if (o['dream_id'], v, judge) in done: continue
            r = ask(url, user(o['arc'], o['core'], v))
            row = {'dream_id': o['dream_id'], 'variant': v, 'judge': judge, 'group': grp, 'verdict': r[0], 'why': r[1], 'err': r[2], 'sec': r[3]}
            open(OUT, 'a', encoding='utf-8').write(json.dumps(row, ensure_ascii=False) + '\n')
            print(row['dream_id'], v, judge, r[0], r[2], r[3], flush=True)
