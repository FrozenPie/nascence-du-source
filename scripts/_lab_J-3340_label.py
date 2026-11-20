"""J-3340 step 1b: blind labelling by falcon3:7b (:11436) and granite3.1-moe:3b (:11437) on Ramses. No Du store touched."""
import json, sys, urllib.request, concurrent.futures as cf
sys.stdout.reconfigure(encoding="utf-8")
S = json.load(open("docs/lab/J-3340_data/sample120.json", encoding="utf-8"))
SYS = ("You label one first-person sentence written by a mind about itself. Choose exactly one label:\n"
 "CLAIM = asserts something about what the speaker IS or HOLDS beyond this moment (a trait, belief, nature, enduring stance, general fact about themselves) that could in principle be checked against their past or reading.\n"
 "STATE = describes a present-moment state, feeling, perception or action (right now / here).\n"
 "OTHER = anything else (question, observation of the world that merely contains 'my', metaphor with no self-assertion, fragment).\n"
 'Answer ONLY JSON: {"label": "CLAIM"} or {"label": "STATE"} or {"label": "OTHER"}.')
def ask(host, model, s):
    body = {"model": model, "stream": False, "format": "json", "options": {"temperature": 0},
            "messages": [{"role": "system", "content": SYS}, {"role": "user", "content": "SENTENCE: " + s}]}
    req = urllib.request.Request(f"http://{host}/api/chat", json.dumps(body).encode(), {"Content-Type": "application/json"})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=180))
        t = r["message"]["content"]
        lab = json.loads(t).get("label", "?").upper()
        return lab if lab in ("CLAIM", "STATE", "OTHER") else "?"
    except Exception as e:
        return "ERR"
out = {}
for name, host, model in (("falcon", "LAN-HOST:11436", "falcon3:7b"), ("granite", "LAN-HOST:11437", "granite3.1-moe:3b")):
    with cf.ThreadPoolExecutor(2) as ex:
        labs = list(ex.map(lambda r: ask(host, model, r["s"]), S))
    out[name] = labs
    print(name, {l: labs.count(l) for l in set(labs)})
json.dump(out, open("docs/lab/J-3340_data/judge_labels.json", "w"))
