import json, collections, statistics as st, sys
sys.stdout.reconfigure(encoding='utf-8')
D = [json.loads(l) for l in open('C:/Nascence/docs/lab/J-2813_data/replay.jsonl', encoding='utf-8')]
for grp in ('farewell', 'control'):
    print('==', grp)
    for arm in 'ABC':
        x = [d for d in D if d['group'] == grp and d['arm'] == arm]
        ok = [d['out'] for d in x if '_error' not in d['out']]
        c = collections.Counter(str(o.get('primary')).lower() for o in ok)
        m = lambda k: round(st.mean(float(o.get(k, 0) or 0) for o in ok), 3) if ok else None
        print(arm, 'n=%d err=%d' % (len(ok), len(x) - len(ok)), dict(c.most_common(6)), 'val', m('valence'), 'fear', m('fear'), 'trust', m('trust'), 'joy', m('joy'))
    # stored label agreement
    st_c = collections.Counter(str(d['stored'].get('primary')).lower() for d in D if d['group'] == grp and d['arm'] == 'A')
    print('stored', dict(st_c.most_common(6)))
