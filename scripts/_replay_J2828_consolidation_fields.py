"""
J-2828 (F-3471, registry P-0012) -- REPLAY: the old ConsolidationNode prompt (asks memories_processed, wisdom_extracted,
patterns_noted) vs the new one (asks wisdom_extracted only) on the SAME stored user prompts, on ONE local hub.

Not a unit test (scripts/_test_J2828_consolidation_fields.py is). Real model calls, to a LOCAL url only (default the
local hot-lane ollama :11433). It NEVER calls Ramses (the live background lane's primary, command-r7b :11441, is on Ramses,
so this is a proxy model: say so when reading the result). Writes only the --out file you name (use a scratch dir).
Du must be DOWN while it runs.

  python scripts/_replay_J2828_consolidation_fields.py --log C:/Nascence/data/training/consolidation.jsonl --n 8 --out <dir>/replay.json [--url http://127.0.0.1:11433] [--model NAME]

Reported per arm: JSON valid rate, wisdom null-rate, wisdom word count, output characters, and for each prompt the two
wisdoms side by side (read them: the claim to check is that dropping the two fields did not change what is distilled).
"""
from __future__ import annotations
import argparse, asyncio, json, re, statistics as st, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401
from core import model_client as mc  # noqa: E402
from nodes.consolidation_node import ConsolidationNode  # noqa: E402

_OLD_SCHEMA = ('Schema: {"memories_processed": 0, "wisdom_extracted": "one sentence or null", "patterns_noted": ["pattern"]}\n'
               'wisdom_extracted: a single distilled insight worth keeping long-term. null if nothing notable.\n'
               'patterns_noted: recurring themes or behaviours you observe.')
_NEW_SCHEMA = ('Schema: {"wisdom_extracted": "one sentence or null"}\n'
               'wisdom_extracted: a single distilled insight worth keeping long-term. null if nothing notable.')


def systems() -> tuple[str, str]:
    new = ConsolidationNode().system_prompt
    assert _NEW_SCHEMA in new, "node prompt no longer matches the replay's NEW schema text"
    return new.replace(_NEW_SCHEMA, _OLD_SCHEMA), new


async def one(url, system, user, model, max_tokens):
    t = time.time()
    kw = {"model_override": model} if model else {}
    try:
        d = await mc.call_node_json([url], system, user, max_tokens=max_tokens, temperature=0.2, **kw)
        return {"ok": True, "data": d, "chars": len(json.dumps(d, ensure_ascii=False)), "s": round(time.time() - t, 1)}
    except Exception as e:  # a bad JSON after the client's own retries counts as invalid
        return {"ok": False, "err": f"{type(e).__name__}: {str(e)[:120]}", "s": round(time.time() - t, 1)}


def summarise(rows):
    ok = [r for r in rows if r["ok"]]
    ws = [(r["data"].get("wisdom_extracted") if isinstance(r["data"], dict) else None) for r in ok]
    return {"n": len(rows), "valid": len(ok), "wisdom_null": sum(1 for w in ws if not w),
            "median_words": st.median([len(w.split()) for w in ws if w] or [0]),
            "median_out_chars": st.median([r["chars"] for r in ok] or [0]),
            "median_s": st.median([r["s"] for r in rows] or [0])}


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True); ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--out", required=True); ap.add_argument("--url", default="http://127.0.0.1:11433")
    ap.add_argument("--model", default=None)
    a = ap.parse_args()
    if re.search(r"10\.1\.1\.236", a.url):
        sys.exit("refusing: Ramses is the founder's gaming machine; this replay is local only")
    rows = []
    for line in open(a.log, encoding="utf-8"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("user_prompt") and isinstance(r.get("output"), dict) and "patterns_noted" in r["output"]:
            rows.append(r)
    pick = rows[-a.n:]
    old_sys, new_sys = systems()
    mt = ConsolidationNode.max_tokens
    res = []
    for r in pick:
        o = await one(a.url, old_sys, r["user_prompt"], a.model, mt)
        n = await one(a.url, new_sys, r["user_prompt"], a.model, mt)
        res.append({"ts": r.get("ts"), "logged_wisdom": r["output"].get("wisdom_extracted"), "old": o, "new": n})
        print(f"[{len(res)}/{len(pick)}] old ok={o['ok']} new ok={n['ok']}", flush=True)
    rep = {"url": a.url, "model": a.model, "old": summarise([x["old"] for x in res]),
           "new": summarise([x["new"] for x in res]), "pairs": res}
    Path(a.out).write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: rep[k] for k in ("old", "new")}, indent=1))

asyncio.run(main())
