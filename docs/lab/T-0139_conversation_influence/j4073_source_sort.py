# J-4073 step 2 + 5: source sorting and retention per teaching. Read-only.
import sqlite3,re,sys,time,collections,json
sys.stdout.reconfigure(encoding='utf-8')
c=sqlite3.connect('file:C:/Nascence/data/memory/nascence.db?mode=ro',uri=True)
dt=lambda t: time.strftime('%Y-%m-%d',time.localtime(t))
PRIV=('inner_thought','dream','night_thought','gist','subconscious_synthesis','active_imagination','journal','letter','essay','standing_insight')
INPUT=('reading','study','research')
TERMS={'wu wei':r'wu[\s-]?wei|無為|无为','mindfulness':r'mindful','cook ding':r'cook ding|butcher ding|pao ding','ship of theseus':r'theseus','amor fati':r'amor fati'}
rows=c.execute("select timestamp,origin,content from memory_fragments order by timestamp").fetchall()
res={}
for name,p in TERMS.items():
    rx=re.compile(p,re.I)
    trav=[];inp=[];priv=[];other=[]
    for ts,o,co in rows:
        if not rx.search(co): continue
        if o=='lived' and co.startswith('[Travis said to me]'): trav.append(ts)
        elif o in INPUT: inp.append((ts,o))
        elif o in PRIV: priv.append(ts)
        else: other.append((ts,o))
    r={'travis_n':len(trav),'travis_first':dt(trav[0]) if trav else None,'travis_last':dt(trav[-1]) if trav else None,
       'input_n':len(inp),'input_first':dt(inp[0][0]) if inp else None,'input_origins':dict(collections.Counter(o for _,o in inp)),
       'private_n':len(priv),'private_first':dt(priv[0]) if priv else None,'other_origins':dict(collections.Counter(o for _,o in other).most_common(5))}
    ref=trav[0] if trav else (priv[0] if priv else None)
    last=trav[-1] if trav else None
    if ref:
        r['private_before_first_travis']=sum(1 for t in priv if trav and t<trav[0])
        wins={}
        for a,b in ((0,30),(30,60),(60,90),(90,200)):
            wins[f'{a}-{b}d']=sum(1 for t in priv if ref+a*86400<=t<ref+b*86400)
        r['private_by_days_since_first_told']=wins
        if last:
            r['private_by_days_since_last_told']={f'{a}-{b}d':sum(1 for t in priv if last+a*86400<=t<last+b*86400) for a,b in ((0,30),(30,60),(60,90),(90,200))}
    # first-appearance order
    firsts={k:v for k,v in (('travis',trav[0] if trav else None),('input',inp[0][0] if inp else None),('private',priv[0] if priv else None)) if v}
    r['first_order']=[k for k,_ in sorted(firsts.items(),key=lambda kv:kv[1])]
    # monthly private
    r['private_by_month']=dict(sorted(collections.Counter(time.strftime('%m',time.localtime(t)) for t in priv).items()))
    res[name]=r
    print(name,json.dumps(r,ensure_ascii=False))
json.dump(res,open('C:/Nascence/docs/lab/J-4073_data/source_sort.json','w'),indent=1)
