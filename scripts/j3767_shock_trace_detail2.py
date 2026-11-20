# J-3767 trace, committed by J-4010 unchanged from the scratchpad original (detail pass 2, argv[1] = days window).
# READ-ONLY. Imports scripts/j2916_shock_trace.py by path and reads the live data dir. Re-run for J-3764 after pursuit lookup retirement.
import sys, json, re, sqlite3, collections, bisect, datetime as dt
sys.dont_write_bytecode = True
import importlib.util
spec = importlib.util.spec_from_file_location("j2916", r"C:\Nascence\scripts\j2916_shock_trace.py")
J = importlib.util.module_from_spec(spec); spec.loader.exec_module(J)
from pathlib import Path
class A: pass
a = A(); a.db = Path(r"C:\Nascence\data\memory\nascence.db"); a.data = Path(r"C:\Nascence\data"); a.days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
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
c = sqlite3.connect(f"file:{a.db.as_posix()}?mode=ro&immutable=1", uri=True)
rows = c.execute("select fragment_id,timestamp,importance,origin,content from memory_fragments where timestamp>=? and origin in "
                 "('action','activity','lived','letter','peer','social_notification','research')", (B["start"] - 8 * 86400,)).fetchall()
rows.sort(key=lambda r: r[1])
ts_ = [r[1] for r in rows]
shock_ids = {r["id"] for r in shocks}; ctrl_ids = {r["id"] for r in controls}
by_id = {r["id"]: r for r in shocks + controls}
print("importance by class (median):")
import statistics
for nm, f in (("shock", lambda r: r[0] in shock_ids), ("pursuit", lambda r: r[0] in ctrl_ids),
              ("other", lambda r: r[0] not in shock_ids and r[0] not in ctrl_ids)):
    v = [r[2] for r in rows if f(r) and r[2] is not None]
    print(nm, len(v), statistics.median(v) if v else None, round(sum(1 for x in v if x >= 0.8) / max(1, len(v)), 3))
def top(lo, hi, k=6):
    i, j = bisect.bisect_right(ts_, lo), bisect.bisect_left(ts_, hi)
    sub = sorted(rows[i:j], key=lambda r: (-(r[2] or 0), -r[1]))
    return sub[:8][:k]
dr = [r for r in jl(D / "dream_log.jsonl") if r["ts"] >= B["start"]]
expo = collections.Counter(); cited = collections.Counter(); ndream_with = collections.Counter(); win = collections.Counter()
ex = []
for r in dr:
    t0 = float(str(r["dream_id"]).split("_")[-1])
    txt = " ".join([str(r.get("narrative") or ""), str(r.get("final_narrative") or ""), " ".join(r.get("symbols") or [])]).lower()
    tk = J.toks(txt)
    has = collections.Counter()
    for nm, lo, hi in (("recent", t0 - 2 * 86400, t0), ("far", t0 - 7 * 86400, t0 - 5 * 86400)):
        for fr in top(lo, hi):
            cl = "shock" if fr[0] in shock_ids else "pursuit" if fr[0] in ctrl_ids else "other"
            expo[(nm, cl)] += 1; has[(nm, cl)] += 1
            if cl != "other":
                rec = by_id[fr[0]]
                if J.cites(txt, tk, *kws[rec["id"]]):
                    cited[(nm, cl)] += 1
                    if cl == "shock": ex.append((nm, rec["title"], round((t0 - rec["ts"]) / 3600, 1)))
    for k_, v in has.items():
        if v: ndream_with[k_] += 1
print("exposure (page-views in top6 of day_material world query):", {f"{k[0]}|{k[1]}": v for k, v in expo.items()})
print("cited:", {f"{k[0]}|{k[1]}": v for k, v in cited.items()})
print("dreams with >=1:", {f"{k[0]}|{k[1]}": v for k, v in ndream_with.items()}, "of", len(dr))
print(ex[:20])
# T4 hit outcomes
print("=== T4 judge outcomes for hit events")
j = jl(D / "logs" / "t4_emissary_judge.jsonl")
for r in j:
    t = float(r["ts"])
    if t < B["start"]: continue
    tx = (str(r.get("candidate")) + " " + str(r.get("evidence"))).lower(); tk = J.toks(tx)
    for s in shocks:
        if 0 <= t - s["ts"] <= 48 * 3600 and J.cites(tx, tk, *kws[s["id"]]):
            print(dt.datetime.fromtimestamp(t).strftime("%m-%d %H:%M"), s["title"], "warranted", r.get("emissary_warranted"), "self_filter_pass", r.get("self_filter_pass"))
tot = [r for r in j if float(r["ts"]) >= B["start"]]
print("judge rows in window", len(tot), "pass", sum(1 for r in tot if str(r.get("self_filter_pass")) == "True"), "warranted>=0.5", sum(1 for r in tot if float(r.get("emissary_warranted") or 0) >= 0.5))
