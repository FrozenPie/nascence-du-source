import json,sys
sys.path.insert(0,'C:/Nascence')
ACT='C:/Nascence/data/pursuits_active.json'
J='C:/Nascence/data/pursuits_judged.jsonl'
def trunc_words(text, limit):
    text=(text or "").strip()
    if len(text)<=limit: return text
    cut=text[:limit]; sp=cut.rfind(" ")
    head=cut[:sp] if sp>limit*0.4 else cut
    return head.rstrip(" ,;:")+"…"
def dq(p):
    if p.get("question_kind") in ("question","done_when","observation") and (p.get("question_text") or "").strip(): return p["question_text"]
    return p.get("question","")
def build():
    reg={p['id']:p for p in json.load(open(ACT,encoding='utf-8'))}
    rows=[json.loads(l) for l in open(J,encoding='utf-8')]
    out=[]
    for i,r in enumerate(rows):
        p=reg.get(r['pursuit_id'])
        if not p: continue
        q=dq(p); ps=r.get('prior_standing',''); th=r.get('thought','')
        old=f"PURSUIT: {q[:200]}\n\nITS PRIOR POSITION: {ps[:280]}\n\nNEW THOUGHT: {th[:450]}\n\nDoes the thought advance the pursuit?"
        pq=trunc_words(q,250); nps=trunc_words(ps,300)
        dedupe = (not nps) or nps==pq or nps==(p.get('question') or '').strip()[:300] or (len(ps)>=150 and q.strip().startswith(ps.strip()))
        if dedupe: nps="same as the pursuit itself"
        new=f"PURSUIT: {pq}\n\nITS PRIOR POSITION: {nps}\n\nNEW THOUGHT: {th[:400]}\n\nDoes the thought advance the pursuit?"
        out.append(dict(i=i,pid=r['pursuit_id'],old=old,new=new,old_verdict=r['verdict'],old_how=r['how'],dedupe=dedupe,qlong=len(q)>200,differs=old!=new))
    return out
if __name__=='__main__':
    o=build()
    import collections
    print(len(o),collections.Counter((x['dedupe'],x['qlong'],x['differs']) for x in o))
