import json,glob,collections,sys
sys.stdout.reconfigure(encoding='utf-8')
r={}
for f in sorted(glob.glob('C:/Nascence/docs/lab/J-4122_judge_*.jsonl')):
    for l in open(f,encoding='utf-8'):
        d=json.loads(l)
        if d.get('raw'):
            try: r[(d['i'],d['arm'])]=json.loads(d['raw'])
            except Exception: pass
print('parsed',len(r))
exists={}
for (i,a),j in r.items(): exists.setdefault(i,[]).append(bool(j.get('conflict_exists_in_memories')))
for a in 'ACE':
    rows=[(i,j) for (i,x),j in r.items() if x==a]
    n=len(rows); nt=sum(j.get('n_tensions',0) for i,j in rows); g=sum(j.get('grounded',0) for i,j in rows); f=sum(j.get('fabricated',0) for i,j in rows)
    q=sum(j.get('quality',0) for i,j in rows)/n
    withT=sum(1 for i,j in rows if j.get('n_tensions',0)>0)
    fabItems=sum(1 for i,j in rows if j.get('fabricated',0)>0)
    # conflict exists per judge on this output, missed = exists & n_tensions==0
    missed=sum(1 for i,j in rows if j.get('conflict_exists_in_memories') and j.get('n_tensions',0)==0)
    ex=sum(1 for i,j in rows if j.get('conflict_exists_in_memories'))
    print(a,'n',n,'tensions',nt,'grounded',g,'fab',f,'items_with_tension',withT,'items_with_fab',fabItems,'meanQ',round(q,2),'judge_says_conflict_exists',ex,'missed(exists&empty)',missed)
