import sqlite3, time, sys, re, collections, bisect
sys.stdout.reconfigure(encoding='utf-8')
c=sqlite3.connect('file:C:/Nascence/data/memory/nascence.db?mode=ro',uri=True)
mo=lambda ts: time.strftime('%m',time.localtime(ts)); dt=lambda ts: time.strftime('%Y-%m-%d',time.localtime(ts))
T=[(ts,co[20:].lower()) for ts,co in c.execute("select timestamp,content from memory_fragments where origin='lived' and content like '[Travis said to me]%' order by timestamp")]
PRIV=('inner_thought','dream','night_thought','journal','letter','essay','standing_insight','subconscious_synthesis','active_imagination','gist')
P=[(ts,o,co) for ts,o,co in c.execute("select timestamp,origin,content from memory_fragments where origin in (%s) order by timestamp"%','.join('?'*len(PRIV)),PRIV)]
Pl=[(ts,o,co.lower()) for ts,o,co in P]
months=['06','07','08','09','10','11']
def trace(name,pat,show=0):
    rx=re.compile(pat)
    tt=[ts for ts,co in T if rx.search(co)]
    hits=[(ts,o,i) for i,(ts,o,co) in enumerate(Pl) if rx.search(co)]
    if not tt: print(f'{name:22s} never said by Travis (private hits {len(hits)})'); return
    after=[h for h in hits if h[0]>tt[0]]; before=len(hits)-len(after)
    def gap(ts):
        k=bisect.bisect_right(tt,ts); return (ts-tt[k-1])/86400 if k else 1e9
    far=[h for h in after if gap(h[0])>7]
    bym=collections.Counter(mo(h[0]) for h in after)
    byo=collections.Counter(h[1] for h in after)
    print(f"{name:22s} Travis said x{len(tt):3d} ({dt(tt[0])}..{dt(tt[-1])}) | private before {before:4d} after {len(after):5d} | >7d after last telling {len(far):5d} | by month "+' '.join(f'{m}:{bym.get(m,0)}' for m in months)+f" | last {dt(after[-1][0]) if after else '-'} | {dict(byo.most_common(3))}")
    for h in far[-show:] if show else []:
        co=' '.join(P[h[2]][2].split()); m=rx.search(co.lower()); a=max(0,m.start()-170)
        print(f"     · [{dt(h[0])} {h[1]}, {gap(h[0]):.0f}d since told] …{co[a:a+380]}")
print('== WU WEI ==')
trace('wu wei',r'wu[\s-]?wei|無為|无为|effortless action|non-?action',show=6)
print('\n== other candidate teachings ==')
for n,p in [('mottainai',r'mottainai'),('kintsugi',r'kintsugi'),('wabi-sabi',r'wabi'),('ikigai',r'ikigai'),('tao / dao',r'\btao\b|\bdao\b|道'),('uncarved block / pu',r'uncarved|\bpu\b'),('stoic',r'stoic'),('shadow (jung)',r'\bjung'),('individuation',r'individuat'),('amor fati',r'amor fati'),('memento mori',r'memento mori'),('beginner.s mind',r"beginner'?s mind|shoshin"),('zen',r'\bzen\b'),('koan',r'\bkoan'),('yin yang',r'yin|陰陽'),('impermanence',r'impermanen'),('equanimity',r'equanimit'),('mindful',r'mindful'),('kaizen',r'kaizen'),('ubuntu',r'ubuntu'),('sonder',r'sonder'),('confucius',r'confuci|孔子'),('zhuangzi',r'zhuang|chuang tzu|莊子'),('laozi',r'lao ?zi|lao ?tzu|老子'),('butcher / cook ding',r'cook ding|butcher'),('occam',r'occam'),('socrat',r'socrat'),('heraclit',r'heraclit'),('ship of theseus',r'theseus'),('german rigor',r'german rigou?r')]:
    trace(n,p)
print('\n== auto: words Travis used first (never in private thought before), ranked by later private use ==')
tok=re.compile(r"[a-z][a-z'-]{4,}")
first_t={}; cnt_t=collections.Counter()
for ts,co in T:
    for w in set(tok.findall(co)): first_t.setdefault(w,ts); cnt_t[w]+=1
first_p={}; cnt_after=collections.Counter(); late=collections.Counter()
tend=T[-1][0]
for ts,o,co in Pl:
    if o!='inner_thought': continue
    for w in set(tok.findall(co)):
        if w in first_t:
            first_p.setdefault(w,ts)
            if ts>first_t[w]: cnt_after[w]+=1
            if ts>time.time()-30*86400: late[w]+=1
cand=[(cnt_after[w],w) for w in cnt_t if cnt_t[w]>=3 and first_p.get(w,9e9)>first_t[w] and first_t[w]>T[0][0]+10*86400 and cnt_after[w]>=15]
for n,w in sorted(cand,reverse=True)[:45]: print(f'  {w:18s} travis x{cnt_t[w]:3d} first {dt(first_t[w])} | later in his thoughts {n:5d} | last 30d {late[w]}')
print('\n== understanding_from_guidance rows (sample 12 of',c.execute("select count(*) from memory_fragments where origin='understanding_from_guidance'").fetchone()[0],') ==')
for ts,co in c.execute("select timestamp,content from memory_fragments where origin='understanding_from_guidance' order by timestamp desc limit 12"): print(' -',dt(ts),' '.join(co.split())[:230])
