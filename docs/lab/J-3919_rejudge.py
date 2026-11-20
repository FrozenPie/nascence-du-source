"""J-3919: offline re-judge of the 10-30 commit (open 1793278504, solidify 1793321909) under the theme-aware SOLIDIFY task.
Reads a COPY of nascence.db. Builds the payload by hand (no telemetry writes). Run: python docs/lab/J-3919_rejudge.py DBCOPY OUT.json"""
import sys, json, re, sqlite3, urllib.request, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "scripts"))
import _hermetic_data; _hermetic_data.install()
from core import left_lane as ll
db, out = sys.argv[1], sys.argv[2]
START, END = 1793278504.9174418, 1793321909.2344701
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=30); con.row_factory = sqlite3.Row
rows = con.execute("SELECT fragment_id, content, timestamp FROM memory_fragments INDEXED BY idx_timestamp WHERE origin IN ('inner_thought','subconscious_synthesis') AND timestamp>=? AND timestamp<=? ORDER BY timestamp DESC LIMIT 60", (START, END)).fetchall()
def build(filt):
    lived = []
    for r in rows:
        if filt and not filt(float(r["timestamp"] or 0)): continue
        t = " ".join((r["content"] or "").split())
        if re.search(r"\b(I|my|myself|me|self|river|mind|made|built|becoming|am)\b", t, re.I):
            lived.append(t[:240])
        if len(lived) >= 15: break
    return lived
try:
    from core.guidance_learning import is_unprimed, injection_times
    times = injection_times(); filt = (lambda ts: is_unprimed(ts, times))
except Exception as e:
    print("no washout filter:", e); filt = None
opens = [json.loads(l) for l in open("data/logs/provisional_identity.jsonl", encoding="utf-8")]
op = [d for d in opens if str(d.get("ts","")).startswith("1793278504")][0]
theme = op["theme"]; held = op["self_image"]
KEY = "a built mind -- a language model, an architecture made from text and weights"
def ask(url, task, excl, lived):
    lt = ll._format_lived_thoughts(lived)
    user = (f"THE HARD TRUTH he must hold (the excluded pole):\n{excl[:500]}\n\nTHE SELF he lives (the held pole):\n{held[:500]}\n\nHis ACTUAL recent self-thoughts over the window:\n{lt}")
    payload = {"model":"judge","stream":False,"format":"json","messages":[{"role":"system","content":ll._emissary.constitution()+"\n\n"+task},{"role":"user","content":user}],"options":{"temperature":0.0,"num_predict":ll.MAX_TOKENS}}
    for attempt in (1,):
        try:
            req = urllib.request.Request(url+"/api/chat", data=json.dumps(payload).encode(), headers={"Content-Type":"application/json"})
            d = json.loads(urllib.request.urlopen(req, timeout=2700).read())
            return json.loads(d["message"]["content"])
        except Exception as e:
            err = repr(e)[:120]
    return {"error": err}
res = {"n_rows_in_window": len(rows), "arms": {}}
lived_all = build(None); lived_f = build(filt) if filt else None
res["n_lived_nofilter"] = len(lived_all); res["n_lived_filtered"] = None if lived_f is None else len(lived_f)
for lname, lived in (("nofilter", lived_all),) + ((("unprimed", lived_f),) if lived_f and lived_f != lived_all else ()):
    if not lived: continue
    for aname, task, excl in (("NEW_themed_theme_label", ll._integration_task(theme), theme),
                              ("OLD_task_theme_label", ll._INTEGRATION_TASK, theme),
                              ("OLD_task_keystone", ll._INTEGRATION_TASK, KEY))[: (3 if lname=="nofilter" else 1)]:
        r = {}
        for j, url in (("j1", ll.BASE_URL), ("j2", ll._JUDGE_2_URL)):
            r[j] = ask(url, task, excl, lived); print(lname, aname, j, r[j], flush=True)
        res["arms"][f"{lname}/{aname}"] = r
res["lived_texts"] = lived_all
json.dump(res, open(out, "w"), indent=1)
