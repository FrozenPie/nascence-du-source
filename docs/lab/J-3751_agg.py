import json
R=json.load(open("J-3751_data/results.json"))
print(len(R))
for arm in ("new_prompt","old_prompt"):
    ms=[r["m_"+arm] for r in R if r.get("m_"+arm)]; js=[r["judge_"+arm] for r in R if r.get("judge_"+arm)]
    n=len(ms)
    s=lambda k: round(sum(m[k] for m in ms)/n,2)
    print(arm,"n",n,{k:s(k) for k in ["old_facts","new_read_facts","rev_facts","old_retained","rev_facts_matching_new_read","union_facts","old_len","rev_len","thoughts_jac_old","thoughts_jac_new","connects_jac_new","question_jac_new"]})
    print(" judge n",len(js),{k:round(sum(j.get(k,0) or 0 for j in js)/max(1,len(js)),2) for k in ["thoughts_reflect_new","connects_reflect_new","question_reflect_new","integrates_both"]})
    print(" per-pair rev/union", [(m["rev_facts"],m["union_facts"],m["old_retained"],m["old_facts"]) for m in ms])
