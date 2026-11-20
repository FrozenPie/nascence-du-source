import json,re,sys
sys.stdout.reconfigure(encoding='utf-8')
c=json.load(open('docs/lab/J-3465_candidates.json',encoding='utf-8'))
base=json.load(open('scripts/curiosity_prefire_control_set.json',encoding='utf-8'))
lab={}
for i in [8,22,27,59,64,69,72,54,30,1,63,46,62,73]: lab[i]='good'
for i in [16,34,37,38,2,17,19,24,43,36,60,58,67,35,14,45,75]: lab[i]='borderline'
for i in [5,10,20,42,47,52,55,61,79]: lab[i]='bad'
items=list(base['items'])
for i,l in lab.items():
    m=re.sub(r'^Entity:[^\n]*\n\n','',c[i]['up']); m=re.sub(r'\n\nGenerate questions and research directions.*$','',m,flags=re.S)
    items.append({'n':len(items),'label':l,'question':c[i]['question'],'cycle_id':c[i]['cycle_id'],'material':m,'src':'J-3465'})
from collections import Counter
print(Counter(x['label'] for x in items),len(items))
json.dump({'about':'J-3465: base 20 (J-3219) + 40 new, random.seed(3465) sample of the 11-01..11-16 curiosity questions; labels by ONE agent (J-3465), assigned before any judge score was seen; truncated 3-entry study view. Not independent.','items':items},open('docs/lab/J-3465_control60.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
