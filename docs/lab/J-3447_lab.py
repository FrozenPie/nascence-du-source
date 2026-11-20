"""J-3447: same-text noise floor for the drift shadow. Read-only on live DB (mode=ro). Hot lane :11433 qwen3.5:9b."""
import sys, json, sqlite3, time, os, re, urllib.request, itertools, statistics as S
sys.path.insert(0, "C:/Nascence")
from core import memory_levels as ml
OUT = "C:/Nascence/docs/lab/J-3447_data/raw.json"
MODEL = sys.argv[1] if len(sys.argv) > 1 else "qwen3.5:9b"
PORT = sys.argv[2] if len(sys.argv) > 2 else "11433"
conn = sqlite3.connect("file:C:/Nascence/data/memory/nascence.db?mode=ro", uri=True, timeout=20)
conn.row_factory = sqlite3.Row
gists = ml._pick_gists(conn, 20, set()); conn.close()
stance = ml._self_stance()
SYS = ("/no_think\nYou are 渡, RE-REMEMBERING one of your own past self-observations — not reciting "
 "it word-for-word (memory reconstructs), but NOT rewriting it either. The SPECIFIC thing it "
 "was about — the actual image, subject, or event — must stay clearly present and recognisable; "
 "someone comparing your retelling to the original should plainly see it is the SAME memory. "
 "Do NOT add claims that were not in it, and do NOT turn it into a statement about who you are "
 "now. Output ONLY JSON: {\"recalled\": \"...\"} (2-4 sentences).")
SYS_L = SYS.replace("Do NOT add claims", "What may shift is only what it now MEANS to you, the colour of it, not its content. Do NOT add claims")
def call(s, u):
    body = {"model": MODEL, "stream": False, "think": False, "format": "json",
            "options": {"temperature": 0.6, "num_predict": 300},
            "messages": [{"role": "system", "content": s}, {"role": "user", "content": u}]}
    try:
        r = urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{PORT}/api/chat", json.dumps(body).encode(), {"Content-Type": "application/json"}), timeout=120)
        return str(json.loads(json.loads(r.read())["message"]["content"]).get("recalled", "")).strip()
    except Exception as e:
        return ""
try: res = json.load(open(OUT, encoding="utf-8"))["res"]
except Exception: res = []
done = {r["fid"] for r in res}
t0 = time.time()
for fid, text, ts in gists:
    if fid in done: continue
    u = f"The past self-observation (the ANCHOR — its subject must survive):\n  {text[:600]}\n\nRe-remember the observation above, as you are now."
    ul = (f"The past self-observation (the ANCHOR — its subject must survive):\n  {text[:600]}\n\nThe lens you now see through (let it colour the MEANING, not replace the memory):\n  {stance[:600]}\n\nRe-remember the observation above, as you are now.")
    plain = [call(SYS, u) for _ in range(5)]
    lens = [call(SYS_L, ul) for _ in range(3)] if stance else []
    res.append({"fid": fid, "orig": text, "plain": plain, "lens": lens})
    json.dump({"res": res, "stance": stance, "model": MODEL}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
    print(len(res), round(time.time() - t0), flush=True)
    if time.time() - t0 > 2400: break
