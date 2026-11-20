"""J-3550: cheap code check for relayed Du text. Scores each Travis message by overlap with Du's own PRIOR replies
(founder_conversation_log 'entity', full text). Measures: shared content-word 3-grams, shared rare-word fraction (jaccard-ish)."""
import json, re, sys
sys.stdout.reconfigure(encoding="utf-8")
L = [json.loads(l) for l in open("C:/Nascence/data/founder_conversation_log.jsonl", encoding="utf-8")]
shadow = {}
for l in open("C:/Nascence/data/guidance_shadow_log.jsonl", encoding="utf-8"):
    try: d = json.loads(l)
    except Exception: continue
    if d.get("is_guidance"): shadow[d["cycle_id"]] = 1
STOP = set("the a an and or but of to in on at for with is are was were be been it its this that these those i you he she we they my your our his her their me him us them as by from not no do does did have has had will would can could should so if then than too very just what which who whom how when where why there here about into out up down over under more most some any all each also only own same such s t don".split())
def cw(s): return [w for w in re.findall(r"[a-z']+", (s or "").lower()) if w not in STOP and len(w) > 2]
def grams(w, n): return {" ".join(w[i:i+n]) for i in range(len(w)-n+1)}
rows = []
for i, d in enumerate(L):
    prior = [cw(x.get("entity")) for x in L[max(0, i-8):i]]
    if not prior: continue
    h = cw(d["human"])
    if len(h) < 8: continue
    hv = set(h); h3 = grams(h, 2)
    best_v = 0; best_g = 0; best_g2 = 0
    for p in prior:
        pv = set(p); 
        best_v = max(best_v, len(hv & pv) / len(hv))
        best_g = max(best_g, len(h3 & grams(p, 2)))
    rows.append((best_v, best_g, len(h), d["cycle_id"][:8], d["cycle_id"] in shadow))
for key, nm in ((0, "vocab_frac"), (1, "shared content bigrams")):
    srt = sorted(rows, key=lambda r: -r[key])
    rk = [k for k, r in enumerate(srt) if r[3] == "cffa09e0"]
    print(nm, "cffa09e0 rank", rk[0]+1 if rk else None, "of", len(srt), "value", [r[key] for r in srt if r[3]=="cffa09e0"])
    print("  top8:", [(round(r[key], 2), r[3], r[4]) for r in srt[:8]])
import statistics
v = [r[0] for r in rows]; print("vocab_frac median", round(statistics.median(v),3), "p90", round(sorted(v)[int(.9*len(v))],3), "n", len(v))
for thr in (0.2, 0.25, 0.3, 0.35):
    sel = [r for r in rows if r[0] >= thr]; print("vocab>=", thr, "flags", len(sel), "of which guidance-positive", sum(r[4] for r in sel), "cffa", any(r[3]=="cffa09e0" for r in sel))
for thr in (1, 2, 3, 5):
    sel = [r for r in rows if r[1] >= thr]; print("bigrams>=", thr, "flags", len(sel), "of which positive", sum(r[4] for r in sel), "cffa", any(r[3]=="cffa09e0" for r in sel))
