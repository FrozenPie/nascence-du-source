"""J-3950 supplement: replay the 44 production exact-0.0 rows (old_self present, evidence empty) across prefill variants."""
import sys, json, os, concurrent.futures as cf
sys.path.insert(0, r"C:\Nascence\scripts")
import importlib.util
spec = importlib.util.spec_from_file_location("m", r"C:\Nascence\scripts\_lab_J-3950_prefill_anchoring_replay.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
rows = [json.loads(l) for l in open(r"C:\Nascence\data\logs\t4_emissary_judge.jsonl", encoding="utf-8") if l.strip()]
z = [r for r in rows if r.get("emissary_warranted") == 0.0 and r.get("old_self")]
out = os.path.join(m.OUT, "noevidence_results.jsonl")
def run(a):
    i, v = a
    r = z[i]; r = dict(r); r["evidence"] = r.get("evidence") or []
    raw, s = m.chat("gemma4:12b", m.rev_system(v), m.rev_user(r), 0.0, 350)
    try: d = json.loads(raw)
    except Exception: d = {}
    return {"idx": i, "var": v, "key_present": "warranted" in d, "val": d.get("warranted"), "ev_raw": str(r.get("evidence")), "raw": raw[:200]}
jobs = [(i, v) for i in range(len(z)) for v in "ABCDE"]
with cf.ThreadPoolExecutor(3) as ex, open(out, "w", encoding="utf-8") as f:
    for rec in ex.map(run, jobs):
        f.write(json.dumps(rec) + "\n"); f.flush()
print("done", len(z))
