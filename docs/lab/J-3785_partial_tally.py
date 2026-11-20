import sys,json,collections
sys.path.insert(0,'scripts')
import importlib.util as u
s=u.spec_from_file_location('g','scripts/lab_J-3785_same_lesson_gate.py');g=u.module_from_spec(s);s.loader.exec_module(g)
pairs,lab,a=g.load()
for hub in ('falcon3','gemma4'):
    c=collections.Counter()
    for l in open(f'docs/lab/J-3785_data/stage2_{hub}_fwd.jsonl',encoding='utf-8'):
        r=json.loads(l);k='hand-same' if lab.get(r['pid'])=='S' else 'not-same(A-assimilated)'
        c[(k,r['same'])]+=1
    print(hub,dict(c))
