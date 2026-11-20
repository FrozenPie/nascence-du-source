import sqlite3, collections
c=sqlite3.connect("file:C:/Nascence/data/memory/nascence.db?mode=ro",uri=True)
cut=1787305567.5
rows=list(c.execute("select mf.fragment_id, mf.timestamp, mf.origin, substr(mf.content,1,70) p, fc.fragment_id is not null j from memory_fragments mf left join fragment_context fc using(fragment_id) where mf.timestamp>=? and mf.origin!='action' order by mf.timestamp",(cut,)))
# hypothesis: unjoined iff previous fragment (any origin) within 0.5s had identical content[:70] (snapshot debounce)
tp=fp=fn=tn=0
unj=[r for r in rows if not r[4] and r[2]=="reading"]
prev=None; 
res=collections.Counter()
for i,r in enumerate(rows):
    if r[2]!="reading": continue
    # look back for the nearest earlier row with identical prefix within 0.5 s (any origin)
    hit=False
    j=i-1
    while j>=0 and r[1]-rows[j][1] < 0.5:
        if rows[j][3]==r[3]: hit=True;break
        j-=1
    res[(bool(r[4]),hit)]+=1
print("(joined, debounce_predicted)",res)
# distribution of gap to previous same-prefix reading fragment for unjoined
gaps=[]
lastp={}
for r in rows:
    if r[2]!="reading": continue
    g=r[1]-lastp[r[3]] if r[3] in lastp else None
    lastp[r[3]]=r[1]
    if not r[4] and g is not None: gaps.append(g)
import statistics
print("unjoined reading w/ earlier same-prefix:",len(gaps),"of",len(unj),"median gap",statistics.median(gaps) if gaps else None)
print("gap<2s",sum(g<2 for g in gaps),"gap<5s",sum(g<5 for g in gaps))
