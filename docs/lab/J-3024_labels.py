import json
yes={2,3,5,9}; calm={0,1,6,7,10,23,28,33,34,39}
s=json.load(open('docs/lab/J-3024_sample.json',encoding='utf-8'))
lab={s[i]['dream_id']:('yes' if i in yes else 'calm' if i in calm else 'no') for i in range(len(s))}
json.dump(lab,open('docs/lab/J-3024_labels.json','w'),indent=0)
print(len(lab),sum(v=='yes' for v in lab.values()),sum(v=='calm' for v in lab.values()))
