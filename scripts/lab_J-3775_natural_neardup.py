"""J-3775: natural-traffic check of lane2 / frontier / deliberation near-duplicate rules (follow-up to J-3308).
READ-ONLY on live data. Writes only under docs/lab/J-3775_data. Pre-registration: docs/lab/J-3775_preregistration.md.
  python scripts/lab_J-3775_natural_neardup.py build | judge | report
"""
from __future__ import annotations
import json, random, sys, threading, bisect
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
import core  # noqa: E402,F401
sys.path.insert(0, str(ROOT / "scripts"))
import importlib
J = importlib.import_module("lab_J-3308_nearduplicate_replay")

SEED = 3775
N = 150
SRC = Path("C:/Nascence/data")
OUT = ROOT / "docs" / "lab" / "J-3775_data"
W = 7 * 86400.0


def topk(t, cands, emb, k=3):
    et = emb.get(t)
    sc = []
    for c in cands:
        s = J.cos(et, emb.get(c))
        if s is not None:
            sc.append((s, c))
    sc.sort(reverse=True)
    return [c for _, c in sc[:k]]


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    rules = J.site_rules()
    from core import lane2
    items = []
    rows = []
    for r in J._jl(SRC / "lane2_would_ask.jsonl"):
        w = (r.get("wonder") or "").strip()
        if w:
            rows.append((float(r.get("ts") or 0), w))
    rows.sort()
    tg = rng.sample(range(len(rows)), N)
    tss = [x[0] for x in rows]
    need = set()
    plan = []
    for i in tg:
        lo = bisect.bisect_left(tss, rows[i][0] - W)
        pri = [rows[j][1] for j in range(lo, i)]
        plan.append((rows[i][1], pri))
        need.add(rows[i][1])
        need.update(pri)
    emb = J.embed_all(list(need))
    for t, pri in plan:
        hit = [p for p in pri if rules["lane2"](t, p, None)]
        cands = list(dict.fromkeys(topk(t, pri, emb, 3) + hit[:1]))[:4]
        items.append({"site": "L", "target": t, "n_prior": len(pri), "flag": bool(hit), "cands": cands})
    print("lane2 done", len(need), "embedded", flush=True)
    qs = [(float(q["born"]), q["q"]) for q in json.load(open(SRC / "frontier.json", encoding="utf-8"))["questions"] if q.get("q")]
    qs.sort()
    bs = [x[0] for x in qs]
    cut = bs[-1] - 28 * 86400
    pool = [i for i in range(len(qs)) if bs[i] >= cut]
    tg = rng.sample(pool, min(N, len(pool)))
    need = set()
    plan = []
    for i in tg:
        lo = bisect.bisect_left(bs, bs[i] - W)
        pri = [qs[j][1] for j in range(lo, i)]
        plan.append((qs[i][1], pri))
        need.add(qs[i][1])
        need.update(pri)
    emb = J.embed_all(list(need))
    print("frontier embedded", len(need), flush=True)
    for t, pri in plan:
        hit = [p for p in pri if rules["frontier"](t, p, J.cos(emb.get(t), emb.get(p)))]
        cands = list(dict.fromkeys(topk(t, pri, emb, 3) + hit[:1]))[:4]
        items.append({"site": "F", "target": t, "n_prior": len(pri), "flag": bool(hit), "cands": cands})
    drows = [r for r in J._jl(SRC / "deliberation_log.jsonl") if r.get("raw") and r.get("integrated")]
    for r in rng.sample(drows, min(N, len(drows))):
        items.append({"site": "D", "target": r["raw"], "n_prior": 1, "flag": bool(rules["delib"](r["raw"], r["integrated"], None)),
                      "cands": [r["integrated"]]})
    pairs = []
    for k, it in enumerate(items):
        it["id"] = f"N{k:04d}"
        for c, cand in enumerate(it["cands"]):
            pairs.append({"pid": f"{it['id']}_{c}", "iid": it["id"], "src": it["site"], "a": it["target"], "b": cand})
    json.dump(items, open(OUT / "items.json", "w", encoding="utf-8"), ensure_ascii=False)
    with open(OUT / "pairs.jsonl", "w", encoding="utf-8") as f:
        for p in pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    print("items", len(items), "pairs", len(pairs))


def judge():
    pairs = [json.loads(l) for l in open(OUT / "pairs.jsonl", encoding="utf-8")]
    path = OUT / "labels.jsonl"
    done = {}
    if path.exists():
        for l in open(path, encoding="utf-8"):
            r = json.loads(l)
            done[(r["pid"], r["model"])] = r
    f = open(path, "a", encoding="utf-8")
    lock = threading.Lock()

    def one(model, x, timeout=200):
        if (x["pid"], model) in done:
            return done[(x["pid"], model)]["same"]
        sysmsg = J.JUDGE_Q[x["src"]] + ' Answer ONLY JSON: {"same": true} or {"same": false}.'
        try:
            v, raw, s = J.ask(model, sysmsg, "A: " + x["a"] + "\nB: " + x["b"], timeout=timeout)
        except Exception as e:
            v, raw, s = None, repr(e)[:150], None
        rec = {"pid": x["pid"], "model": model, "same": v, "raw": raw, "s": s}
        with lock:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            done[(x["pid"], model)] = rec
        return v

    def worker(m):
        fails = 0
        for k, x in enumerate(pairs):
            v = one(m, x)
            fails = fails + 1 if v is None else 0
            if fails >= 8:
                print(m, "8 consecutive failures, stopping this hub", flush=True)
                return
            if k % 50 == 0:
                print(m, k, flush=True)
    ths = [threading.Thread(target=worker, args=(m,)) for m in ("gemma4:12b", "falcon3:7b")]
    [t.start() for t in ths]
    [t.join() for t in ths]
    n = 0
    for x in pairs:
        g = done.get((x["pid"], "gemma4:12b"), {}).get("same")
        fa = done.get((x["pid"], "falcon3:7b"), {}).get("same")
        if g is not None and fa is not None and g != fa and n < 120:
            n += 1
            one("yi:34b-v1.5", x, timeout=400)
    f.close()
    print("judge done; yi", n)


def report():
    items = json.load(open(OUT / "items.json", encoding="utf-8"))
    votes = {}
    for l in open(OUT / "labels.jsonl", encoding="utf-8"):
        r = json.loads(l)
        votes.setdefault(r["pid"], {})[r["model"]] = r["same"]
    pairs = {}
    for l in open(OUT / "pairs.jsonl", encoding="utf-8"):
        p = json.loads(l)
        pairs.setdefault(p["iid"], []).append(p["pid"])
    res = {}
    for site in "LFD":
        its = [i for i in items if i["site"] == site]
        dup = miss = fa = unk = flagged = 0
        for it in its:
            labs = [J.panel_label(votes.get(pid, {}))[0] for pid in pairs.get(it["id"], [])]
            jd = any(x is True for x in labs)
            if not jd and any(x is None for x in labs):
                unk += 1
                continue
            flagged += it["flag"]
            if jd:
                dup += 1
                if not it["flag"]:
                    miss += 1
            elif it["flag"]:
                fa += 1
        n = len(its) - unk
        res[site] = {"n": len(its), "excluded_unknown": unk, "judged_dup": dup, "site_flagged": flagged, "misses": miss,
                     "miss_rate_of_dup": round(miss / dup, 3) if dup else None, "miss_wilson": J.wilson(miss, dup),
                     "false_alarms": fa, "disagreement": round((miss + fa) / max(1, n), 3),
                     "disagreement_wilson": J.wilson(miss + fa, n)}
    json.dump(res, open(OUT / "summary.json", "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    {"build": build, "judge": judge, "report": report}[sys.argv[1]]()
