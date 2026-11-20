"""J-3309 step 3: pairwise blind order-swapped judge on the DIFFERING items only. Own HTTP posts to the
judge_panel family hubs (same payload shape as core/judge_panel._ask, no telemetry writes); never the key-writer lane.
usage: judge_J-3309.py <hub:j1|j2|tb> <arms comma list>   -- resumable cache in judge_cache_<hub>_J-3309.jsonl"""
import sys, json, sqlite3, random, time, urllib.request, os
sys.path.insert(0, r"C:\Nascence")
D = r"C:\Nascence\docs\lab\J-3309"
HUBS = {"j1": "http://LAN-HOST:11438", "j2": "http://127.0.0.1:11440", "tb": "http://LAN-HOST:11437"}
hub, arms = sys.argv[1], sys.argv[2].split(",")
limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10**9
Q = {q["cycle_id"]: q for q in json.load(open(D + r"\frozen_queries_J-3309.json", encoding="utf-8"))}
A = json.load(open(D + r"\arms_J-3309.json"))
cache_f = D + rf"\judge_cache_{hub}_J-3309.jsonl"
done = set()
if os.path.exists(cache_f):
    for l in open(cache_f, encoding="utf-8"):
        r = json.loads(l); done.add((r["cycle_id"], r["arm"], r["order"]))
cn = sqlite3.connect("file:C:/Nascence/data/memory/nascence.db?mode=ro", uri=True)
def content(fid):
    r = cn.execute("SELECT content FROM memory_fragments WHERE fragment_id=?", (fid,)).fetchone()
    t = " ".join((r[0] if r else "").split())
    return t[:280] + ("..." if len(t) > 280 else "")
SYS = ("You compare two sets of memory snippets retrieved for an entity that is about to think or answer. "
       "Judge which set would help the entity more in answering or thinking about the query: relevance, "
       "specific useful substance, not mere word overlap. Output ONLY JSON: {\"x_better\": true|false}. "
       "true means set X is better, false means set Y is better. You must pick one.")
def fmt(items): return "\n".join(f"{i+1}. {t}" for i, t in enumerate(items))
def ask(user):
    payload = {"model": "judge", "stream": False, "format": "json",
               "messages": [{"role": "system", "content": SYS}, {"role": "user", "content": user}],
               "options": {"temperature": 0.0, "num_predict": 60}}
    t0 = time.time()
    for attempt in range(2):
        try:
            req = urllib.request.Request(HUBS[hub] + "/api/chat", json.dumps(payload).encode(), {"Content-Type": "application/json"})
            d = json.load(urllib.request.urlopen(req, timeout=240))
            v = json.loads(d["message"]["content"])
            if isinstance(v.get("x_better"), bool): return v["x_better"], None, round(time.time() - t0, 1)
            err = "parse"
        except Exception as e:
            err = type(e).__name__
    return None, err, round(time.time() - t0, 1)
n = 0
out = open(cache_f, "a", encoding="utf-8")
for r in A:
    for arm in arms:
        if r.get("no_keys") or arm not in r: continue
        a_ids = [x["id"] for x in r[arm]]; p_ids = [x["id"] for x in r["plain"]]
        a_only = [i for i in a_ids if i not in p_ids]; p_only = [i for i in p_ids if i not in a_ids]
        if not a_only and not p_only: continue
        q = Q[r["cycle_id"]]
        rng = random.Random(hash((r["cycle_id"], arm)) & 0xffff) if False else random.Random(r["cycle_id"] + arm)
        at = [content(i) for i in a_only]; pt = [content(i) for i in p_only]
        rng.shuffle(at); rng.shuffle(pt)
        qtxt = f"Query: {q['raw_input'][:600]}\nSummary: {q['summary'][:400]}"
        for order in (1, 2):
            if (r["cycle_id"], arm, order) in done: continue
            if n >= limit: sys.exit(0)
            X, Y = (at, pt) if order == 1 else (pt, at)
            u = f"{qtxt}\n\nSet X:\n{fmt(X)}\n\nSet Y:\n{fmt(Y)}"
            xb, err, el = ask(u)
            arm_pref = None if xb is None else (xb if order == 1 else (not xb))
            out.write(json.dumps({"cycle_id": r["cycle_id"], "arm": arm, "order": order, "hub": hub, "x_better": xb,
                                  "arm_pref": arm_pref, "err": err, "s": el, "n_a": len(at), "n_p": len(pt)}) + "\n"); out.flush()
            n += 1
