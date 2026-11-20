"""J-2676 lab step B: replay captured payloads against ollama :11433 or a standalone llama-server, record timings.

  python scripts/lab_J-2676_replay.py --cap <dir> --arm ollama|llama --base http://127.0.0.1:PORT --order b2b|inter \
        --out <file.jsonl> [--n-idle 50] [--chains 5]

Corpus: idle = real idle user prompts (data/idle_prompt_samples.jsonl: wrapper_head + parts + wrapper_tail) paired with
the rebuilt system prompt variant; human = the captured :11433 node-chain payloads (call order kept).
Order b2b: idle x N consecutively, then each human chain in order.  Order inter: idle thought, then 2 other-caller
payloads (cycled from the human chains), repeated.  Reads only; no live data/ writes; local hosts only.
"""
import argparse, asyncio, json, random, sys, time
from pathlib import Path

import aiohttp

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent


def parse_json_obj(txt):
    if not txt:
        return None
    t = txt.strip()
    try:
        d = json.loads(t)
        return d if isinstance(d, dict) else None
    except Exception:
        pass
    i, j = t.find("{"), t.rfind("}")
    if i >= 0 and j > i:
        try:
            d = json.loads(t[i:j + 1])
            return d if isinstance(d, dict) else None
        except Exception:
            return None
    return None


def build_idle(cap, n, seed=2676):
    sysv = json.load(open(cap / "idle_system_prompts.json", encoding="utf-8"))
    rows = [json.loads(l) for l in open(ROOT / "data" / "idle_prompt_samples.jsonl", encoding="utf-8") if l.strip()]
    rows = [r for r in rows if "wrapper_head" in r and r.get("parts")]
    rows = random.Random(seed).sample(rows, min(n, len(rows)))
    items = []
    for r in rows:
        user = (r["wrapper_head"] or "") + "\n".join(r["parts"]) + (r.get("wrapper_tail") or "")
        key = f"wand{int(bool(r.get('wandering')))}_mid{int(bool(r.get('mid_thread')))}"
        if key not in sysv:
            key = next(iter(sysv))
        mid = bool(r.get("mid_thread"))
        items.append({"kind": "idle", "key": key, "system": sysv[key], "user": user,
                      "max_tokens": 400 if mid else 256, "temperature": 0.8 if r.get("wandering") else 0.75})
    return items


def build_human(cap, chains):
    recs = [json.loads(l) for l in open(cap / "capture_posts.jsonl", encoding="utf-8") if l.strip()]
    out = []
    for r in recs:
        if ":11433" not in r["url"] or not r["chain"] or not r["chain"].startswith("human"):
            continue
        p = r["payload"]
        msgs = p["messages"]
        out.append({"kind": "human", "chain": r["chain"], "seq": r["seq"], "system": msgs[0]["content"],
                    "user": msgs[1]["content"], "max_tokens": p["options"]["num_predict"],
                    "temperature": p["options"]["temperature"], "json": p.get("format") == "json",
                    "ollama_pe": r["pe"], "ollama_wall_capture": r["wall"]})
    keep = sorted({x["chain"] for x in out})[:chains]
    return [x for x in out if x["chain"] in keep]


async def one(session, arm, base, it, timeout=300):
    t0 = time.monotonic()
    if arm == "ollama":
        payload = {"model": "qwen3.5:9b", "messages": [{"role": "system", "content": it["system"]},
                                                          {"role": "user", "content": it["user"]}],
                   "think": False, "stream": False,
                   "options": {"temperature": it["temperature"], "num_predict": it["max_tokens"], "num_ctx": 8192},
                   "keep_alive": "2h", "format": "json"}
        url = base + "/api/chat"
    else:
        payload = {"model": "x", "messages": [{"role": "system", "content": it["system"]},
                                              {"role": "user", "content": it["user"]}],
                   "max_tokens": it["max_tokens"], "temperature": it["temperature"], "stream": False,
                   "response_format": {"type": "json_object"},
                   "chat_template_kwargs": {"enable_thinking": False}}
        url = base + "/v1/chat/completions"
    rec = {"kind": it["kind"], "chain": it.get("chain"), "key": it.get("key"), "arm": arm}
    try:
        async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
            resp.raise_for_status()
            d = await resp.json()
    except Exception as e:
        rec.update(wall=round(time.monotonic() - t0, 3), ok=False, err=repr(e)[:150])
        return rec
    wall = time.monotonic() - t0
    if arm == "ollama":
        txt = (d.get("message") or {}).get("content") or ""
        rec.update(prompt_n=d.get("prompt_eval_count"), prompt_ms=round((d.get("prompt_eval_duration") or 0) / 1e6, 1),
                   gen_n=d.get("eval_count"), gen_ms=round((d.get("eval_duration") or 0) / 1e6, 1), cache_n=None)
    else:
        txt = ((d.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
        tm = d.get("timings") or {}
        rec.update(prompt_n=tm.get("prompt_n"), prompt_ms=round(tm.get("prompt_ms") or 0, 1), cache_n=tm.get("cache_n"),
                   gen_n=tm.get("predicted_n"), gen_ms=round(tm.get("predicted_ms") or 0, 1),
                   total_prompt_tokens=(d.get("usage") or {}).get("prompt_tokens"))
    obj = parse_json_obj(txt)
    rec.update(wall=round(wall, 3), ok=True, parsed=obj is not None, keys=sorted(obj.keys()) if obj else [],
               has_thought=bool(obj and str(obj.get("thought", "")).strip()) if it["kind"] == "idle" else None,
               out_chars=len(txt), think_leak=("<think>" in txt))
    return rec


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", required=True)
    ap.add_argument("--arm", required=True, choices=["ollama", "llama"])
    ap.add_argument("--base", required=True)
    ap.add_argument("--order", default="b2b", choices=["b2b", "inter"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-idle", type=int, default=50)
    ap.add_argument("--chains", type=int, default=5)
    a = ap.parse_args()
    assert "127.0.0.1" in a.base or "localhost" in a.base
    cap = Path(a.cap)
    idle = build_idle(cap, a.n_idle)
    human = build_human(cap, a.chains)
    if a.order == "b2b":
        seq = idle + human
    else:
        others = [h for h in human]
        seq, k = [], 0
        for it in idle:
            seq.append(it)
            for _ in range(2):
                if others:
                    seq.append(others[k % len(others)])
                    k += 1
        seq += human
    print(f"{a.arm} {a.order}: {len(idle)} idle + {len(human)} human payloads, sequence {len(seq)}")
    # warm-up so model load is not counted in the first row (not recorded, not part of the corpus)
    async with aiohttp.ClientSession() as s:
        w = dict(idle[0]); w["max_tokens"] = 8
        await one(s, a.arm, a.base, w)
        with open(a.out, "w", encoding="utf-8") as f:
            for i, it in enumerate(seq):
                r = await one(s, a.arm, a.base, it)
                r["i"] = i
                r["order"] = a.order
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
                f.flush()
                if i % 10 == 0:
                    print(i, r.get("kind"), r.get("wall"), r.get("prompt_n"), r.get("cache_n"), r.get("parsed"))


asyncio.run(main())
