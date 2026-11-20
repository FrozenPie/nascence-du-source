"""Spot check v2: observed text-vs-context agreement vs a PERMUTATION NULL (context rows shuffled within origin)."""
import json, random, collections, sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
A = importlib.import_module("J-2536_audit")
frags, fc, wc, cut = A.load_frags()
RNG = random.Random(25362)
CATLOC = {"on_your_lap": re.compile(r"\b(lap)\b", re.I), "on_the_desk": re.compile(r"\b(on the desk|desk)\b", re.I),
          "by_the_fire": re.compile(r"\b(by the fire|hearth|grate|fireside)\b", re.I),
          "windowsill": re.compile(r"\b(windowsill|sill)\b", re.I), "doorstep": re.compile(r"\b(doorstep|door step)\b", re.I),
          "garden": re.compile(r"\b(garden)\b", re.I), "away_hunting": re.compile(r"\b(hunting|prowl\w*|out hunting)\b", re.I)}
CATW = A.CAT

def tests(text, row, cat_world):
    res = A.spot(None, text, row)
    # cat location test against WORLD truth (experienced cat_at is None whenever she's elsewhere)
    if CATW.search(text):
        ment = [k for k, rx in CATLOC.items() if rx.search(text)]
        if ment and cat_world:
            res["catloc"] = "agree" if cat_world in ment else "disagree"
    res.pop("cat_here", None)
    return res

def grp(k):
    return k.split("_")[0] if (k.startswith("w_") or k.startswith("s_")) else k

def score(ids, ctx):  # ctx: id -> (fcrow, cat_world)
    c = collections.Counter()
    for fid in ids:
        r = tests(frags[fid][2], ctx[fid][0], ctx[fid][1])
        for k, v in r.items():
            c[(grp(k), v)] += 1
    return c

by_o = collections.defaultdict(list)
for fid, r in fc.items():
    f = frags.get(fid)
    if not f: continue
    by_o[f[0] if r[0].startswith("experienced:") else "WINDOW(census_world:idle)"].append(fid)
out = {}
for o, ids in sorted(by_o.items(), key=lambda kv: -len(kv[1])):
    if len(ids) < 300: continue
    ctx = {fid: (fc[fid], (wc.get(fid) or (None,)*8)[3] if False else (wc.get(fid) or [None]*8)[3]) for fid in ids}
    # wc row = (source,tuple_ts,place,weather,cat_at,sounds,warmth) -> index 4 is cat_at
    ctx = {fid: (fc[fid], (wc.get(fid) or [None]*7)[4]) for fid in ids}
    obs = score(ids, ctx)
    nulls = []
    for _ in range(20):
        perm = ids[:]
        RNG.shuffle(perm)
        ctxp = {fid: ctx[p] for fid, p in zip(ids, perm)}
        nulls.append(score(ids, ctxp))
    row = {}
    for g in ("w", "place", "s", "catloc"):
        a, d = obs[(g, "agree")], obs[(g, "disagree")]
        na = [n[(g, "agree")] / max(1, n[(g, "agree")] + n[(g, "disagree")]) for n in nulls]
        mean_n = sum(na) / len(na)
        sd = (sum((x - mean_n) ** 2 for x in na) / len(na)) ** 0.5
        obs_rate = a / max(1, a + d)
        row[g] = {"applicable": a + d, "agree_obs": round(obs_rate, 3), "agree_null": round(mean_n, 3), "null_sd": round(sd, 4),
                  "lift": round(obs_rate - mean_n, 3), "mismatch_obs": round(1 - obs_rate, 3) if a + d else None}
    out[o] = {"n": len(ids), "groups": row}
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "J-2536_out_spot2.json"), "w"), indent=1)
for o, v in out.items():
    print(o, v["n"], {g: (r["applicable"], r["agree_obs"], r["agree_null"], r["lift"]) for g, r in v["groups"].items()})
