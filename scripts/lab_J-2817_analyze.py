"""J-2817 analysis of arms_out.jsonl (+ judge_out.jsonl if present)."""
import json, re, sys, statistics as st, collections, importlib.util
sys.stdout.reconfigure(encoding='utf-8')
spec=importlib.util.spec_from_file_location('arms','C:/Nascence/scripts/lab_J-2817_recall_arms.py'); arms=importlib.util.module_from_spec(spec); spec.loader.exec_module(arms)
D='C:/Nascence/docs/lab/J-2817_data/'
outs={}
for l in open(D+'arms_out.jsonl',encoding='utf-8'):
    d=json.loads(l); outs[(d['i'],d['arm'])]=d
def words(s): return re.findall(r"[a-z']+",s.lower())
def shingles(w,n=5): return {tuple(w[i:i+n]) for i in range(len(w)-n+1)}
def carry(text,pshing):
    sh=shingles(words(text)); 
    return (len(sh&pshing)/len(sh)) if sh else 0.0
res={a:collections.defaultdict(list) for a in 'ABCDE'}
for (i,a),d in sorted(outs.items()):
    try: j=json.loads(d['raw'])
    except Exception: res[a]['parsefail'].append(1); continue
    t=[x for x in j.get('tensions',[]) if x]; c=j.get('confidence')
    res[a]['ntens'].append(len(t)); res[a]['conf'].append(float(c) if isinstance(c,(int,float)) else None)
    u=arms.make(arms.sample[i]['user_prompt'],a)
    k=u.find(arms.HEAD); mem=u[k:] if k>=0 else u
    ps=shingles(words(mem))
    for x in t: res[a]['carry_t'].append(carry(x,ps))
    res[a]['carry_r'].append(carry(str(j.get('reconstruction','')),ps))
    # carry from Tensions: tails (only present in A prompts)
    tails=' '.join(re.findall(r"Tensions:(.*?)(?=\n  \[|\n\n|$)",arms.sample[i]['user_prompt'],flags=re.S))
    ts=shingles(words(tails))
    for x in t: res[a]['carry_tail'].append(carry(x,ts) if ts else None)
    res[a]['has_tail'].append(1 if ts else 0)
    res[a]['type'].append(d['type'])
print("arm n parsefail empty% mean_ntens ntens_dist conf>=.8% conf_mean conf_values(top) carryT>=.5% mean_carryT carryR")
for a in 'ABCDE':
    r=res[a]; n=len(r['ntens']); nt=r['ntens']
    conf=[c for c in r['conf'] if c is not None]
    ct=r['carry_t']
    print(a,n,len(r['parsefail']),f"{100*sum(1 for x in nt if x==0)/n:.1f}%",round(st.mean(nt),2),dict(sorted(collections.Counter(nt).items())),
      f"{100*sum(1 for c in conf if c>=.8)/len(conf):.0f}%",round(st.mean(conf),3),collections.Counter(conf).most_common(5),
      f"{100*sum(1 for x in ct if x>=.5)/max(1,len(ct)):.0f}%",round(st.mean(ct),3) if ct else None,round(st.mean(r['carry_r']),3))
    for ty in ('internal','human'):
        ix=[k for k,t in enumerate(r['type']) if (t=='internal')==(ty=='internal')]
        if ix: print('   ',ty,len(ix),'empty%',round(100*sum(1 for k in ix if nt[k]==0)/len(ix),1),'conf mean',round(st.mean([r['conf'][k] for k in ix if r['conf'][k] is not None]),3))
ca=[x for x in res['A']['carry_tail'] if x is not None]
print('A: tensions that share >=50% of 5-grams with a prompt Tensions: tail:',sum(1 for x in ca if x>=.5),'/',len(ca),'; prompts with tail:',sum(res['A']['has_tail']),'/',len(res['A']['has_tail']))
# paired confidence/ntens change
pairs=collections.defaultdict(dict)
for (i,a),d in outs.items():
    try: j=json.loads(d['raw']); pairs[i][a]=(len([x for x in j.get('tensions',[]) if x]),j.get('confidence'))
    except Exception: pass
full=[p for p in pairs.values() if len(p)==3]
print('paired items',len(full),'C empty where A nonempty:',sum(1 for p in full if p['C'][0]==0 and p['A'][0]>0),'B empty where A nonempty:',sum(1 for p in full if p['B'][0]==0 and p['A'][0]>0))
try:
    jd={}
    for l in open(D+'judge_out.jsonl',encoding='utf-8'):
        d=json.loads(l)
        try: jd[(d['i'],d['arm'])]=json.loads(d['raw'])
        except Exception: pass
    print('judge n',len(jd))
    for a in 'ABCDE':
        v=[x for (i,aa),x in jd.items() if aa==a]
        if not v: continue
        g=lambda k:[float(x.get(k,0)) for x in v if isinstance(x.get(k,0),(int,float))]
        nt=sum(g('n_tensions')); 
        print(a,len(v),'quality',round(st.mean(g('quality')),2),'grounded',sum(g('grounded')),'fabricated',sum(g('fabricated')),'of',nt,'tensions;','conflict_exists',sum(1 for x in v if x.get('conflict_exists_in_memories') is True),'/',len(v),
          'empty outputs where conflict exists:',sum(1 for (i,aa),x in jd.items() if aa==a and x.get('n_tensions')==0 and x.get('conflict_exists_in_memories') is True),
          'empty outputs where none exists:',sum(1 for (i,aa),x in jd.items() if aa==a and x.get('n_tensions')==0 and x.get('conflict_exists_in_memories') is False))
except FileNotFoundError: pass
