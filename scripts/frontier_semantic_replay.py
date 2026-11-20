"""J-2428 offline replay (read-only on data/frontier.json): embeds the open questions, writes S.npy/opens.json next to this
script's temp dir, then the threshold/cross-topic analysis. Two steps kept as the original scratch scripts; see
docs/reviews/frontier_semantic_merge_replay_2026-10-19.md for results. Run part 1 then part 2."""
# ===== part 1: embed =====
import sys, json, time, hashlib, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Nascence\.claude\worktrees\j2275-prune-retire-22d6d7')
os.environ['HF_HUB_OFFLINE']='1'
from core.memory import store
import numpy as np
d=json.load(open(r'C:\Nascence\data\frontier.json',encoding='utf-8'))
qs=d['questions']
opens=[q for q in qs if q['status']=='open']
print(len(opens))
t=time.time(); V=store._embed_batch([q['q'] for q in opens]); print('embed',time.time()-t)
M=np.stack(V); S=M@M.T
np.save(os.path.join(os.path.dirname(__file__),'S.npy'),S)
json.dump([q['q'] for q in opens],open(os.path.join(os.path.dirname(__file__),'opens.json'),'w',encoding='utf-8'))
t=time.time(); store._embed("one more question about whatever"); print('single embed',time.time()-t)

# ===== part 2: incremental greedy replay (rep-only matching) =====
import sys, json, os, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
h=os.path.dirname(__file__)
S=np.load(h+'/S.npy'); Q=json.load(open(h+'/opens.json',encoding='utf-8'))
d=json.load(open(r'C:\Nascence\data\frontier.json',encoding='utf-8'))
op=[q for q in d['questions'] if q['status']=='open']
mot=np.array(['mottainai' in q.lower() for q in Q]); n=len(Q)
print('n',n,'mot',mot.sum())
iu=np.triu_indices(n,1)
for name,mask in [('mot-mot',mot[iu[0]]&mot[iu[1]]),('other-other',~mot[iu[0]]&~mot[iu[1]]),('cross',mot[iu[0]]!=mot[iu[1]])]:
    s=S[iu][mask]; print(name,len(s),'pcts 50/90/99/max',np.percentile(s,[50,90,99,100]).round(3))
# incremental replay in born order
order=np.argsort([q['born'] for q in op])
for th in [.70,.75,.80,.85,.90]:
    reps=[];merged=0;cross=0;mm=0
    for i in order:
        best=None;bs=0
        for r in reps:
            if S[i,r]>bs: bs=S[i,r];best=r
        if best is not None and bs>=th:
            merged+=1
            if mot[i]!=mot[best]: cross+=1
        else: reps.append(i)
    print(th,'merged',merged,'entries left',len(reps),'cross-topic(mottainai vs not)',cross)
import random
random.seed(7)
for th in [.80,.85]:
    reps=[];pairs=[]
    for i in order:
        best=None;bs=0
        for r in reps:
            if S[i,r]>bs: bs=S[i,r];best=r
        if best is not None and bs>=th: pairs.append((i,best,bs))
        else: reps.append(i)
    print('\n== th',th,'mottainai entries left',sum(mot[r] for r in reps),'other left',sum(not mot[r] for r in reps),'pairs',len(pairs))
    for i,b,s in random.sample(pairs,30):
        print(f'{s:.3f} M={int(mot[i])}{int(mot[b])}\n   NEW: {Q[i][:150]}\n   REP: {Q[b][:150]}')
# ===== part 3: single-link variant (chains across topics at 0.80) =====
for th in [.80,.85,.88]:
    groups=[];cross=0
    for i in order:
        best=None;bs=0
        for gi,g in enumerate(groups):
            s=max(S[i,m] for m in g)
            if s>bs: bs=s;best=gi
        if best is not None and bs>=th:
            if mot[i]!=mot[groups[best][0]]: cross+=1
            groups[best].append(i)
        else: groups.append([i])
    mg=[g for g in groups if mot[g[0]]]
    print(th,'groups',len(groups),'mot groups',len(mg),'largest mot',max(map(len,mg)),'cross',cross)
