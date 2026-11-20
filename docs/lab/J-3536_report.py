import json,glob,collections,math,sys
sys.stdout.reconfigure(encoding='utf-8')
def p2(k,n):
    if n==0:return 1
    pk=lambda i:math.comb(n,i)/2**n
    return min(1,sum(pk(i) for i in range(n+1) if pk(i)<=pk(k)+1e-12))
R={}
for f in glob.glob('J-3536_data/judgments_mixtral*.jsonl'):
    for l in open(f,encoding='utf-8'):
        r=json.loads(l)
        if r.get('verdict'):R[r['key']]=r
by=collections.defaultdict(dict)
for r in R.values():by[r['pair_id']][r['kind']]=r
def side(r,c):
    v=r['verdict'].get(c)
    if v not in('A','B'):return 'tie'
    return 'rewrite' if (v=='A')==bool(r['a_is_rewrite']) else 'raw'
print('calls',len(R),'pairs with both',sum(1 for p in by.values() if len(p)==2),'of 296')
for c in('question_open','faithful','voice'):
    for mode in('single','debiased'):
        cnt=collections.Counter()
        for p in by.values():
            if mode=='single':
                if 'blind' in p:cnt[side(p['blind'],c)]+=1
            elif len(p)==2:
                a,b=side(p['blind'],c),side(p['blindswap'],c)
                cnt[a if a==b else 'tie']+=1
        n=cnt['rewrite']+cnt['raw']
        print(c,mode,dict(cnt),'rewrite share non-tie',round(cnt['rewrite']/n,3) if n else None,'p',round(p2(cnt['rewrite'],n),4))
