"""J-3465 lab: raw judge outputs for 3 rubric variants over the 60-item control. Resumable. Sequential per hub.
usage: python docs/lab/J-3465_run.py URL TAG V0,V1,V2"""
import sys, json, asyncio, time, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT)); sys.stdout.reconfigure(encoding="utf-8")
from core import judge_panel as jp   # import core BEFORE lab_env
sys.path.insert(0, "C:/Users/USER/.claude/skills/job-queue")
from lab_env import isolate
import aiohttp

URL, TAG, VARS = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
items = json.load(open(ROOT/"docs/lab/J-3465_control60.json", encoding="utf-8"))["items"]
import random as _r
_r.Random(3465).shuffle(items)   # interleave labels so a partial run is balanced
SYS0 = jp.CURIOSITY_PREFIRE_SYSTEM
SYS1 = ("You check ONE candidate question against the material its asker was shown. You do not answer the "
 "question and you do not improve it. STUDIED OR READ MATERIAL is the only evidence; the asker's OWN EARLIER "
 "THOUGHTS are not evidence.\nReply with JSON only: {\"support\": \"up to 12 words copied exactly from the "
 "STUDIED OR READ MATERIAL that this question is about, or empty string\", \"score\": 0, 1, 2 or 3, \"why\": "
 "\"under 15 words\"}\nScore 3 = names a specific person, place, event, text or fact that is in the studied "
 "material and asks something a further reading could answer, about one thing at a time. 2 = about something "
 "in the studied material but vague/general, or it asks the material to explain a link it does not make. "
 "1 = only loosely related to the studied material (mostly the asker's own thoughts or a general theme). "
 "0 = an abstraction, feeling, metaphor, invented scenario, or nothing in the studied material.")
SYS2A = ("Find the passage. You are given STUDIED OR READ MATERIAL and a CANDIDATE QUESTION. Reply JSON only: "
 "{\"quote\": \"up to 12 words copied exactly from the STUDIED OR READ MATERIAL that the question is about, or an "
 "empty string if no passage in it is what the question is about\"}")
SYS2B = ("You are given a QUOTE from studied material and a CANDIDATE QUESTION. Reply JSON only: "
 "{\"answerable\": true or false, \"unsupported_link\": true or false, \"why\": \"under 15 words\"}. "
 "answerable = true only if the question asks about a specific person, place, event, text or fact in the quote "
 "that further reading could answer. unsupported_link = true if the question assumes that one thing reflects, "
 "reveals, shapes, influences or represents another, or blends unrelated subjects, when the quote does not connect them.")

async def call(sess, system, user, timeout=420):
    p = {"model": "judge", "stream": False, "format": "json",
         "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
         "options": {"temperature": 0.0, "num_predict": 220}}
    t0 = time.monotonic()
    for attempt in (0,):
        try:
            async with sess.post(URL + "/api/chat", json=p, timeout=aiohttp.ClientTimeout(total=timeout)) as r:
                r.raise_for_status(); d = await r.json()
            raw = (d.get("message") or {}).get("content") or ""
            try: return json.loads(raw), None, round(time.monotonic()-t0, 1), raw
            except Exception: return None, "parse", round(time.monotonic()-t0, 1), raw
        except Exception as e:
            err = type(e).__name__
    return None, err, round(time.monotonic()-t0, 1), ""

def blocks(it):
    world, own = jp._prefire_split_material(it["material"].strip())
    return world, own

async def main():
    async with aiohttp.ClientSession() as sess:
        for var in VARS:
            out = ROOT/f"docs/lab/J-3465_raw_{TAG}_{var}.jsonl"
            done = set()
            if out.exists():
                done = {json.loads(l)["n"] for l in out.open(encoding="utf-8") if l.strip()}
            for it in items:
                if it["n"] in done: continue
                world, own = blocks(it)
                u = ("STUDIED OR READ MATERIAL (the only evidence):\n<<<\n" + (world[:2400] or "(none)")
                     + "\n>>>\n\nTHE ASKER'S OWN EARLIER THOUGHTS (not evidence):\n<<<\n" + (own[:1200] or "(none)")
                     + "\n>>>\n\nCANDIDATE QUESTION: " + it["question"] + "\n\nReply with the JSON only.")
                row = {"n": it["n"], "label": it["label"], "var": var}
                if var == "V0":
                    v, e, s, raw = await call(sess, SYS0, u); row.update(v=v, err=e, s=s)
                elif var == "V1":
                    v, e, s, raw = await call(sess, SYS1, u); row.update(v=v, err=e, s=s)
                elif var == "V2":
                    ua = ("STUDIED OR READ MATERIAL:\n<<<\n" + (world[:2400] or "(none)") + "\n>>>\n\nCANDIDATE QUESTION: "
                          + it["question"] + "\n\nReply with the JSON only.")
                    v1, e1, s1, _ = await call(sess, SYS2A, ua)
                    q = (v1 or {}).get("quote") if isinstance(v1, dict) else None
                    q = q if isinstance(q, str) else ""
                    ok = bool(q) and jp._prefire_norm(q) in jp._prefire_norm(world)
                    row.update(quote=q, quote_ok=ok, err=e1, s=s1)
                    if ok:
                        ub = "QUOTE:\n<<<\n" + q + "\n>>>\n\nCANDIDATE QUESTION: " + it["question"] + "\n\nReply with the JSON only."
                        v2, e2, s2, _ = await call(sess, SYS2B, ub); row.update(v=v2, err2=e2, s2=s2)
                with out.open("a", encoding="utf-8") as f: f.write(json.dumps(row, ensure_ascii=False) + "\n")
                print(TAG, var, it["n"], row.get("v"), row.get("err"), row.get("s"), flush=True)

with isolate(db="empty"):
    asyncio.run(main())
