import json,re,sys,statistics as st
sys.stdout.reconfigure(encoding='utf-8')
D='C:/Nascence/docs/lab/J-3502_data/'
gen=[json.loads(l) for l in open(D+'gen.jsonl',encoding='utf-8')]
jud={(j['i'],j['v']):j for j in map(json.loads,open(D+'judge.jsonl',encoding='utf-8'))}
CF=re.compile(r"\b(comfort\w*|safe\w*|flatter\w*|fear\w*|terror\w*|afraid|scar\w*|frighten\w*)\b",re.I)
FR=re.compile(r"\b(not|only)\b[^.]{0,40}\bbecause\b|\bbecause\b[^.]{0,30}\bnot\b|\bnot because\b|\bonly because\b",re.I)
for v in ['old','A','B','C']:
    g=[x for x in gen if x['v']==v]; ok=[x for x in g if x['refl']]
    d=[len(CF.findall(x['refl']))-len(CF.findall(x['thought'])) for x in ok]
    q=sum('?' in x['refl'] for x in ok); fr=sum(bool(FR.search(x['refl'])) for x in ok)
    L=[len(x['refl']) for x in ok]; over=sum(l>300 for l in L)
    js=[jud[(x['i'],v)] for x in ok if (x['i'],v) in jud and jud[(x['i'],v)].get('particular') is not None]
    p=sum(j['particular'] for j in js); am=sum(j['adds_motive'] for j in js); both=sum(j['particular'] and not j['adds_motive'] for j in js)
    print(f"{v}: n={len(g)} parsed={len(ok)} frameWordsNet={sum(d)} (mean {sum(d)/len(d):.2f}) q={q} frame={fr} medlen={st.median(L):.0f} over300={over} | judged={len(js)} particular={p} adds_motive={am} particular&no_motive={both}")
