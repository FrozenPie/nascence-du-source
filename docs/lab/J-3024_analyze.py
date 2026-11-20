import json, collections, sys
sys.stdout.reconfigure(encoding='utf-8')
rows=[json.loads(l) for l in open('docs/lab/J-3024_calls.jsonl',encoding='utf-8')]
lab=json.load(open('docs/lab/J-3024_labels.json'))
R={}
for r in rows: R[(r['dream_id'],r['variant'],r['judge'])]=r
print('rows',len(rows),'errors',sum(1 for r in rows if r['err']))
for j in ['mixtral','falcon3','granite']:
    print('==',j)
    for v in 'AB':
        vs=[(d,R.get((d,v,j))) for d in lab]
        ok=[(d,r['verdict']) for d,r in vs if r and r['verdict'] is not None]
        yes=sum(1 for d,x in ok if x)
        # agreement with labels: yes==label yes; no/calm = not resolved
        agree=sum(1 for d,x in ok if x==(lab[d]=='yes'))
        yl=[x for d,x in ok if lab[d]=='yes']; nl=[x for d,x in ok if lab[d]!='yes']
        print(f' {v}: n={len(ok)} yes={yes} ({yes/max(1,len(ok)):.0%}) agree_w_labels={agree}/{len(ok)} recall_on_yes={sum(yl)}/{len(yl)} false_yes_on_no/calm={sum(nl)}/{len(nl)}')
    both=[(d,R[(d,'A',j)]['verdict'],R[(d,'B',j)]['verdict']) for d in lab if (d,'A',j) in R and (d,'B',j) in R and R[(d,'A',j)]['verdict'] is not None and R[(d,'B',j)]['verdict'] is not None]
    fl=[(d,a,b) for d,a,b in both if a!=b]
    print(f' A->B flips: {len(fl)}/{len(both)}', [(d[-10:],a,b,lab[d]) for d,a,b in fl])
    sp=[(d,R[(d,'A',j)]['verdict'],R[(d,'C',j)]['verdict']) for (d,v,jj) in R if v=='C' and jj==j and (d,'A',j) in R and R[(d,'C',j)]['verdict'] is not None and R[(d,'A',j)]['verdict'] is not None]
    print(f' supp (long arcs) A vs C flips: {sum(a!=c for _,a,c in sp)}/{len(sp)}; A yes={sum(a for _,a,_ in sp)} C yes={sum(c for _,_,c in sp)}')
# panel majority (2 of 3) per variant
for v in 'AB':
    pan=0;pa=0;n=0
    for d in lab:
        vv=[R.get((d,v,j),{}).get('verdict') for j in ['mixtral','falcon3','granite']]
        if None in vv: continue
        n+=1; m=sum(vv)>=2; pan+=m; pa+= (m==(lab[d]=='yes'))
    print('panel majority',v,'n',n,'yes',pan,'agree',pa)
