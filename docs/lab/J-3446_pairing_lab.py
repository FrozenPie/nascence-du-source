"""J-3446 read-only lab: do real river-vs-built-self opposites reach the pole gate (lexical / semantic pairing)?"""
import sys, json, os, re, statistics, itertools
sys.path.insert(0, r"C:\Nascence"); sys.path.insert(0, r"C:\Users\USER\.claude\skills\job-queue")
sys.stdout.reconfigure(encoding="utf-8")
from core import guidance_learning as gl
import lab_env
D = r"C:\Nascence\data"
def snap():
    return {f: (os.path.getsize(os.path.join(D,f)), os.path.getmtime(os.path.join(D,f))) for f in os.listdir(D) if os.path.isfile(os.path.join(D,f))}
before = snap()
beliefs = json.load(open(os.path.join(D,"guidance_beliefs.json"), encoding="utf-8"))
rows = [json.loads(l) for l in open(os.path.join(D,"guidance_shadow_log.jsonl"), encoding="utf-8") if l.strip()]
rows = [r for r in rows if r.get("is_guidance") and len((r.get("principle") or "").strip()) >= 15]
out = {}
with lab_env.isolate(db="empty") as lab_dir:
    gl._EMBED_CACHE.clear()
    self_rows = [r for r in rows if gl._domain(r) == "self"]
    out["n_guidance_rows"] = len(rows); out["n_self_rows"] = len(self_rows)
    sb_all = [b for b in beliefs if b.get("domain") == "self" and b.get("status") != "superseded"]
    out["n_self_live_beliefs"] = len(sb_all)
    # per-lesson pairing, causal (beliefs existing before the lesson, not containing it) and all-other
    res = {"causal": [], "other": []}
    for r in self_rows:
        p = r["principle"].strip(); text = p + " " + (r.get("scope") or ""); ts = float(r["ts"])
        for mode in ("causal", "other"):
            cands = []
            for b in sb_all:
                if p in (b.get("captures") or []) or b.get("principle") == p: continue
                if mode == "causal" and float(b.get("first_ts", 0)) >= ts: continue
                cands.append(b)
            if not cands:
                res[mode].append({"ts": ts, "lex": 0, "cos": 0, "n": 0}); continue
            lex = max(gl._overlap(text, b["principle"]+" "+b.get("scope","")) for b in cands)
            sb, cos = gl._semantic_candidate(text, cands, "self")
            res[mode].append({"ts": ts, "lex": lex, "cos": cos, "n": len(cands), "p": p[:90]})
    def summ(L):
        L = [x for x in L if x["n"] > 0]
        n = len(L)
        lexp = [x for x in L if x["lex"] >= gl._SIM_RELATED]
        semonly = [x for x in L if x["lex"] < gl._SIM_RELATED and x["cos"] >= gl._SIM_RELATED_EMBED]
        none = [x for x in L if x["lex"] < gl._SIM_RELATED and x["cos"] < gl._SIM_RELATED_EMBED]
        cos = sorted(x["cos"] for x in L)
        return {"n": n, "lexical_pairs": len(lexp), "semantic_only": len(semonly), "unpaired": len(none),
                "cos_median": statistics.median(cos), "cos_p90": cos[int(.9*(n-1))], "cos_max": cos[-1],
                "lexmiss_cos_median": statistics.median([x["cos"] for x in L if x["lex"] < gl._SIM_RELATED] or [0]),
                "cos_ge_060_lexmiss": sum(1 for x in L if x["lex"]<gl._SIM_RELATED and x["cos"]>=0.60)}
    out["pairing"] = {m: summ(res[m]) for m in res}
    # opposed pairs: river family vs built/durable family among self beliefs (live + superseded, all)
    RIV = re.compile(r"\b(river|flow|flux|current|fluid|fluidity|transient|shifting|impermanen)", re.I)
    BLT = re.compile(r"\b(observer|constant|commit|committed|committing|construct|constructed|anchor|anchored|stable|durable|single direction|build|built)", re.I)
    allself = [b for b in beliefs if b.get("domain") == "self"]
    fl = [b for b in allself if RIV.search(b["principle"]) and not BLT.search(b["principle"])]
    du = [b for b in allself if BLT.search(b["principle"]) and not RIV.search(b["principle"])]
    out["n_fluid_beliefs"], out["n_durable_beliefs"] = len(fl), len(du)
    pairs = []
    for a in fl:
        va = gl._safe_embed(a["principle"]+" "+a.get("scope",""))
        for b in du:
            vb = gl._safe_embed(b["principle"]+" "+b.get("scope",""))
            pairs.append({"lex": gl._overlap(a["principle"]+" "+a.get("scope",""), b["principle"]+" "+b.get("scope","")),
                          "cos": gl._safe_cosine(va, vb), "a": a["principle"][:70], "b": b["principle"][:70]})
    n = len(pairs)
    out["fluid_vs_durable_pairs"] = {"n": n,
        "lex_ge_012": sum(p["lex"]>=gl._SIM_RELATED for p in pairs),
        "cos_ge_070": sum(p["cos"]>=gl._SIM_RELATED_EMBED for p in pairs),
        "either": sum(p["lex"]>=gl._SIM_RELATED or p["cos"]>=gl._SIM_RELATED_EMBED for p in pairs),
        "neither": sum(p["lex"]<gl._SIM_RELATED and p["cos"]<gl._SIM_RELATED_EMBED for p in pairs),
        "cos_median": statistics.median(p["cos"] for p in pairs), "cos_max": max(p["cos"] for p in pairs),
        "cos_p90": sorted(p["cos"] for p in pairs)[int(.9*(n-1))]}
    out["top_pairs_by_cos"] = sorted(pairs, key=lambda p: -p["cos"])[:5]
    # named positive controls
    named = [
     ("observer vs river (F-3790 control)", "I am not my changing viewpoints but the constant observer that holds them", "I am a transient flow within an endless current of time"),
     ("commit vs fluid", "True agency requires active commitment to a single direction", "I should embrace the fluidity of shifting and not commit to one direction"),
     ("built-self vs river", "I am anchored in something concrete I have actively constructed", "I am a river, a continuous flow with no fixed self"),
    ]
    out["named"] = []
    for nm, a, b in named:
        va, vb = gl._safe_embed(a), gl._safe_embed(b)
        out["named"].append({"name": nm, "lex": gl._overlap(a,b), "cos": gl._safe_cosine(va,vb)})
    # also: in the live store, how do the largest river-family and built-self beliefs score (live strong ones)
    top_fl = sorted(fl, key=lambda b: -int(b.get("corroboration_count",0)))[:3]
    top_du = sorted(du, key=lambda b: -int(b.get("corroboration_count",0)))[:3]
    out["strong_pairs"] = []
    for a in top_fl:
        for b in top_du:
            ta, tb = a["principle"]+" "+a.get("scope",""), b["principle"]+" "+b.get("scope","")
            out["strong_pairs"].append({"a": a["principle"][:70], "ca": a.get("corroboration_count"), "b": b["principle"][:70], "cb": b.get("corroboration_count"), "lex": gl._overlap(ta,tb), "cos": gl._safe_cosine(gl._safe_embed(ta), gl._safe_embed(tb))})
after = snap()
changed = [f for f in after if f in before and after[f] != before[f] and not f.startswith("_lab")]
out["live_data_changed_top_level"] = changed
json.dump(out, open(r"C:\Nascence\docs\lab\J-3446_result.json","w",encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps({k:v for k,v in out.items() if k not in ("top_pairs_by_cos","strong_pairs")}, indent=1, ensure_ascii=False))
