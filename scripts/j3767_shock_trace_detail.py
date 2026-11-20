# J-3767 trace, committed by J-4010 unchanged from the scratchpad original (detail pass 1).
# READ-ONLY. Imports scripts/j2916_shock_trace.py by path and reads the live data dir. Re-run for J-3764 after pursuit lookup retirement.
import sys, json, re, sqlite3, collections
sys.dont_write_bytecode = True
import importlib.util
spec = importlib.util.spec_from_file_location("j2916", r"C:\Nascence\scripts\j2916_shock_trace.py")
J = importlib.util.module_from_spec(spec); spec.loader.exec_module(J)
from pathlib import Path
class A: pass
a = A(); a.db = Path(r"C:\Nascence\data\memory\nascence.db"); a.data = Path(r"C:\Nascence\data"); a.days = 30
B = J.build(a); shocks, controls = B["shocks"], B["controls"]
df, n = J.background_df(B["streams"])
kws = {r["id"]: J.keywords(r, df, n) for r in shocks + controls}
D = a.data
def jl(p):
    o = []
    for l in open(p, encoding="utf-8", errors="replace"):
        try: o.append(json.loads(l))
        except Exception: pass
    return o
# ---- T4: per source, per field
print("=== T4 hits by source/field")
src = []
for r in jl(D/"logs"/"t4_chain_trace.jsonl"):
    for k in ("delta", "evidence", "self_concept", "arc_entry"):
        src.append(("chain."+k, float(r["ts"]), str(r.get(k) or ""), r.get("authored")))
for r in jl(D/"logs"/"t4_emissary_judge.jsonl"):
    for k in ("candidate", "evidence"):
        src.append(("judge."+k, float(r["ts"]), str(r.get(k) or ""), None))
for r in jl(D/"narrative_quality_log.jsonl"):
    if str(r.get("kind","")).startswith("t4_"):
        src.append((r["kind"], float(r["ts"]), r.get("text_head") or "", None))
c = collections.Counter(); ex = []
lens = collections.defaultdict(list)
for nm, t, tx, au in src:
    if t < a.__dict__.get("x", 0) + B["start"]: continue
    lens[nm].append(len(tx))
    tl = tx.lower(); tk = J.toks(tl)
    for r in shocks:
        if 0 <= t - r["ts"] <= 48*3600:
            v = J.cites(tl, tk, *kws[r["id"]])
            if v:
                c[(nm, v)] += 1; ex.append((nm, round((t-r["ts"])/3600,1), v, r["title"], tx[:90].replace("\n"," ")))
print(dict(c))
for e in ex[:30]: print(e)
print({k:(len(v), max(v)) for k,v in lens.items()})
# authored self_concept + arc: how many authored events, how many cite any shock in view
# ---- dream hits
print("=== dream hits")
dr = [r for r in jl(D/"dream_log.jsonl") if r["ts"] >= B["start"]-0]
for r in dr:
    tx = " ".join([str(r.get("narrative") or ""), str(r.get("final_narrative") or ""), " ".join(r.get("symbols") or []), str(r.get("tension_source") or "")]).lower()
    tk = J.toks(tx)
    for s in shocks:
        if 0 <= r["ts"] - s["ts"] <= 48*3600:
            v = J.cites(tx, tk, *kws[s["id"]])
            if v:
                print(round((r["ts"]-s["ts"])/3600,1), "tier", v, "|", s["title"], "| kw", kws[s["id"]][1][:3], "| srcs", r.get("material_sources"), "| ts", r["ts"])
# in seed fragments, does the shock's keyword appear?
c = sqlite3.connect(f"file:{a.db.as_posix()}?mode=ro&immutable=1", uri=True)
print("=== seed-fragment route check")
for r in dr:
    tx = " ".join([str(r.get("narrative") or ""), str(r.get("final_narrative") or ""), " ".join(r.get("symbols") or [])]).lower()
    tk = J.toks(tx)
    hit = [s for s in shocks if 0 <= r["ts"]-s["ts"] <= 48*3600 and J.cites(tx, tk, *kws[s["id"]])]
    if not hit: continue
    ids = (r.get("seed") or {}).get("fragment_ids") or []
    ftx = []
    for i in ids:
        row = c.execute("select origin,content from memory_fragments where fragment_id=?", (i,)).fetchone()
        if row: ftx.append((row[0], row[1].lower()))
    for s in hit:
        t_, d_, e_ = kws[s["id"]]
        inseed = [o for o, x in ftx if (t_ and t_ in x) or any(w in J.toks(x) for w in d_)]
        print(s["title"], "-> seed fragments carrying it:", inseed, "n_seed", len(ids))
