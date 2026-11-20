"""J-1840 end-to-end: drive the EDITED core.model_client.call_node_json (worktree copy) against the real
Ramses :11441 hub (Du stopped) using the J-1829 recorded prompts. Telemetry is lab-moded (no writes).
Reads prompts from C:\\Nascence\\data\\lab\\j1829... (read only). Writes only the result file named below."""
import sys, os, json, time, re, asyncio, collections
from pathlib import Path
WT = Path(r"C:\Users\USER\AppData\Local\Temp\claude\C--Nascence\1a2654bf-c60b-4408-96f6-0524944578b1\scratchpad\wt_ramses_second_tier")
sys.path.insert(0, str(WT))
os.chdir(str(WT))
import core
assert Path(core.__file__).resolve().is_relative_to(WT), core.__file__
from core import model_client as mc, telemetry as tel
tel.enter_lab_mode()
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROMPTS = Path(r"C:\Nascence\data\lab\j1829_json_grammar_audition\prompts.jsonl")
OUT = Path(r"C:\Users\USER\AppData\Local\Temp\claude\C--Nascence\1a2654bf-c60b-4408-96f6-0524944578b1\scratchpad\e2e_J-1840_results.jsonl")
URL = "http://LAN-HOST:11441"


def schema_keys(p):
    if p.get("logged_output_keys"):
        return list(p["logged_output_keys"])
    s = p["system"]
    i = s.rfind("JSON")
    blk = s[i:] if i >= 0 else s
    j = blk.find("{")
    if j < 0:
        blk = s[s.find("{"):] if "{" in s else ""
    else:
        blk = blk[j:]
    return list(dict.fromkeys(re.findall(r'"([A-Za-z_][A-Za-z0-9_]*)"\s*:', blk)))


rows = [json.loads(l) for l in open(PROMPTS, encoding="utf-8")]
by = collections.defaultdict(list)
for r in rows:
    by[r["job"]].append(r)
pick = []
for job, lst in by.items():
    pick += lst if job == "subconscious._active_imagination" else lst[:4]

# record the grammar arm of every wire call
ARMS = []
real_post = mc.aiohttp.ClientSession.post


class Spy:
    def __init__(self):
        self.s = mc.aiohttp.ClientSession()
    async def __aenter__(self):
        await self.s.__aenter__(); return self
    async def __aexit__(self, *e):
        return await self.s.__aexit__(*e)
    def post(self, url, json=None, timeout=None):
        ARMS.append((json or {}).get("format") == "json")
        return self.s.post(url, json=json, timeout=timeout)


_orig = mc.aiohttp.ClientSession
mc.aiohttp.ClientSession = lambda *a, **k: Spy.__new__(Spy)  # placeholder, replaced below


class _Spy2:
    def __init__(self, *a, **k):
        self.s = _orig(*a, **k)
    async def __aenter__(self):
        await self.s.__aenter__(); return self
    async def __aexit__(self, *e):
        return await self.s.__aexit__(*e)
    def post(self, url, json=None, timeout=None):
        ARMS.append((json or {}).get("format") == "json")
        return self.s.post(url, json=json, timeout=timeout)


mc.aiohttp.ClientSession = _Spy2


async def main():
    out = []
    for p in pick:
        ARMS.clear()
        t0 = time.monotonic()
        try:
            v = await mc.call_node_json(URL, p["system"], p["user"], max_tokens=p["max_tokens"],
                                        temperature=p["temperature"], timeout=120)
            ok = True
            keys = schema_keys(p)
            keys_ok = all(k in v for k in keys) if isinstance(v, dict) else False
        except Exception as e:
            ok, keys_ok, v = False, False, repr(e)[:200]
        rec = {"job": p["job"], "i": p.get("i"), "arms": list(ARMS), "ok": ok, "keys_ok": keys_ok,
               "s": round(time.monotonic() - t0, 2)}
        out.append(rec)
        print(rec, flush=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")
    n = len(out)
    first_nogram = sum(1 for r in out if r["arms"] and r["arms"][0] is False)
    retried = [r for r in out if len(r["arms"]) > 1]
    print("N", n, "first attempt no-grammar", first_nogram, "retried", len(retried),
          "retry arms all grammar", all(all(r["arms"][1:]) for r in retried),
          "ok", sum(r["ok"] for r in out), "keys_ok", sum(r["keys_ok"] for r in out))
    for job in by:
        rs = [r for r in out if r["job"] == job]
        print(job, "n", len(rs), "retried", sum(len(r["arms"]) > 1 for r in rs), "ok", sum(r["ok"] for r in rs),
              "p50s", sorted(r["s"] for r in rs)[len(rs) // 2])

asyncio.run(main())
