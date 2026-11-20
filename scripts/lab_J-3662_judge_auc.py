"""J-3662: judge-vs-use AUC with strict (content-checked) 4-gram label and human stratum. Read-only on live data."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_J3311_used_label as A
units = A.read_jsonl(A.OUT / "labels.jsonl")
fin = A.load_voice_finals(); db = A.open_db()
fr = A.fetch_fragments(db, {u["fragment_id"] for u in units}); db.close()
def ok(g):
    return all(t.strip("'") for t in g) and sum(1 for t in g if len(t.strip("'")) >= 5) >= 2
for u in units:
    sh = A.grams4(fr[u["fragment_id"]][0]) & A.grams4(fin[u["cycle_id"]])
    u["u4s"] = any(ok(g) for g in sh)
types = {}
for u in units: types[u["input_type"]] = types.get(u["input_type"], 0) + 1
out = {"input_types": types, "arms": {}}
for tag in sys.argv[1:]:
    sc = {}
    for r in A.read_jsonl(A.OUT / f"judge_scores_{tag}.jsonl"):
        if r["score"] is not None: sc[(r["cycle_id"], r["fragment_id"])] = r["score"]
    rows = [u for u in units if (u["cycle_id"], u["fragment_id"]) in sc]
    d = {"n": len(rows), "cycles": len({u["cycle_id"] for u in rows})}
    for name, sub in [("all", rows), ("human", [u for u in rows if u["input_type"] == "human"]),
                      ("nonhuman", [u for u in rows if u["input_type"] != "human"])]:
        s = [sc[(u["cycle_id"], u["fragment_id"])] for u in sub]; cl = [u["cycle_id"] for u in sub]
        e = {"n": len(sub), "cycles": len(set(cl))}
        for lab in ("ue", "u4s", "u4"):
            y = [u[lab] for u in sub]; av = A.auc(s, y)
            e[lab] = {"auc": None if av is None else round(av, 4), "n_pos": int(sum(y)),
                      "ci": list(A.auc_cluster_boot(s, y, cl)) if av is not None else None}
        d[name] = e
    out["arms"][tag] = d
p = A.OUT.parent / "J-3662_auc.json"; p.write_text(json.dumps(out, indent=1))
for t, d in out["arms"].items():
    print(t, d["n"], d["cycles"])
    for k in ("all", "human", "nonhuman"):
        e = d[k]; print("  ", k, e["n"], e["cycles"], {l: (e[l]["auc"], e[l]["ci"], e[l]["n_pos"]) for l in ("ue", "u4s", "u4")})
