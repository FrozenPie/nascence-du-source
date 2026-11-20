import json, re, sys, urllib.request, collections
rows = [json.loads(l) for l in open("docs/lab/J-3794_data/sample.jsonl", encoding="utf-8")]
extra = "--closures" in sys.argv
if extra:
    cut = []
    for l in open("data/logs/follow_line_shadow.jsonl", encoding="utf-8"):
        if '"settled"' in l:
            try: r = json.loads(l)
            except Exception: continue
            if r.get("kind") == "settled" and r["verdict"] == "yes" and r["resolved"] and r.get("closure_how") == "ok":
                cut.append(r)
    rows = [{"sid": "c%d" % i, **r} for i, r in enumerate(cut)]
P = ("QUESTION: {q}\n\nTHOUGHT: {t}\n\nDoes THOUGHT answer or directly engage QUESTION? "
     "Answer with one word: yes, partly, or no.")
def ask(port, model, prompt):
    req = urllib.request.Request("http://127.0.0.1:%d/api/chat" % port, headers={"Content-Type": "application/json"},
        data=json.dumps({"model": model, "stream": False, "options": {"temperature": 0},
                         "messages": [{"role": "user", "content": prompt}]}).encode())
    return json.load(urllib.request.urlopen(req, timeout=180))["message"]["content"]
def parse(s):
    m = re.search(r"\b(yes|partly|no)\b", (s or "").lower()); return m.group(1) if m else "invalid"
out = open("docs/lab/J-3794_data/" + ("closures_graded.jsonl" if extra else "graded.jsonl"), "w", encoding="utf-8")
for r in rows:
    p = P.format(q=r["q"], t=r["thought"]); g = {}
    for name, port, model in (("gemma", 11439, "gemma4:12b"), ("falcon", 11440, "falcon3:7b")):
        try: raw = ask(port, model, p)
        except Exception as e: raw = "ERR " + str(e)[:80]
        g[name] = parse(raw); g[name + "_raw"] = raw[:80]
    out.write(json.dumps({"sid": r["sid"], "logged": r["verdict"], "resolved": r["resolved"], **g}) + "\n"); out.flush()
print("done", len(rows))
