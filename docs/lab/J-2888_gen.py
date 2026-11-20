"""J-2888 generation: replay the sample through mixtral:8x7b on :11438, sequential, resumable, interleaved by row across arms."""
import asyncio, json, sys, time, os, aiohttp
sys.stdout.reconfigure(encoding="utf-8")
D = r"C:\Nascence\docs\lab\J-2888_data"
OUT = r"C:\Nascence\data\lab\ground_contract_lab\gen.jsonl"
URL = "http://LAN-HOST:11438"
inp = json.load(open(D + r"\inputs.json", encoding="utf-8"))
rows = [json.loads(l) for l in open(D + r"\sample.jsonl", encoding="utf-8")]
ARMS = sys.argv[1].split(",") if len(sys.argv) > 1 else ["A0", "A", "B", "C", "D"]
LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else 100
# round-robin over strata so any prefix of the run is stratified (the full 100 x 4 arms needs about 22 h at ~200 s/call)
_by = {}
for r in rows: _by.setdefault(r["stratum"], []).append(r["sid"])
_ks = ["plain_sensory", "self_metaphor", "book_person"]
ORDER = []
_i = 0
while any(_by[s] for s in _ks):
    s = _ks[_i % 3]; _i += 1
    if _by[s]: ORDER.append(_by[s].pop(0))
done = set()
if os.path.exists(OUT):
    for l in open(OUT, encoding="utf-8"):
        try: r = json.loads(l); done.add((r["sid"], r["arm"]))
        except Exception: pass

async def call(sess, system, user):
    payload = {"model": "mixtral:8x7b", "stream": False, "keep_alive": "30m",
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
               "options": {"temperature": 0.1, "num_predict": 350, "num_gpu": 0}, "format": "json"}
    last = None
    for attempt in (1, 2):
        t0 = time.monotonic()
        try:
            async with sess.post(f"{URL}/api/chat", json=payload, timeout=aiohttp.ClientTimeout(total=240)) as resp:
                resp.raise_for_status(); data = await resp.json()
            return (data.get("message") or {}).get("content") or "", round(time.monotonic() - t0, 1), None
        except Exception as e:
            last = repr(e)[:120]
    return None, round(time.monotonic() - t0, 1), last

async def main():
    async with aiohttp.ClientSession() as sess:
        for k in ORDER[:LIMIT]:
            for arm in ARMS:
                if (k, arm) in done: continue
                content, secs, err = await call(sess, inp["systems"][arm], inp["prompts"][str(k)][arm])
                rec = {"sid": k, "arm": arm, "stratum": rows[k]["stratum"], "content": content, "secs": secs, "err": err, "ts": time.time()}
                with open(OUT, "a", encoding="utf-8") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                print(k, arm, secs, err or "", flush=True)
asyncio.run(main())
