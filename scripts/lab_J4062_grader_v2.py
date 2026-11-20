"""J-4062 lab (F-4790): grader task v2 = SEPARATE wording for the reference path and the no-reference path.

Only POSTs to judge hub :11439 (gemma4:12b, temp 0, num_predict 350, num_gpu 0, production payload shape). No Du
module imported, no live store read except data/*_log.jsonl (read-only). Writes only docs/lab/J-4062_data/.
Reuses constitution.txt, controls, real-piece selection from J-3046 (scripts/lab_J3046_work_grader_reference_check.py).

PRE-REGISTERED (briefing, before any v2 call): wrong-scene <=0.3, faithful >=0.8, metaphor/vague <=0.2,
<=2 of the real pieces move >=0.3 vs baseline on the no-reference path. No hard cap, no 'cannot verify' penalty.
"""
import json, time, asyncio, argparse
from pathlib import Path
import aiohttp

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "docs" / "lab" / "J-4062_data"; D.mkdir(exist_ok=True)
D0 = ROOT / "docs" / "lab" / "J-3046_data"
CONST = (D0 / "constitution.txt").read_text(encoding="utf-8")

# pull the data (controls, tasks, BASE, real_pieces) out of the J-3046 script without running its main()
_p = ROOT / "scripts" / "lab_J3046_work_grader_reference_check.py"
_src = _p.read_text(encoding="utf-8").replace("asyncio.run(main())", "")
ns = {"__file__": str(_p)}
exec(compile(_src, "j3046", "exec"), ns)
BASE, CTRL, NAT_TASK, real_pieces = ns["BASE"], ns["CTRL"], ns["NAT_TASK"], ns["real_pieces"]

V2_REF = (
    "You are examining a piece of your friend's SCHOOLWORK. Judge how GROUNDED it is: every statement about the "
    "thing he was set, and nothing else. You are given the TASK and a REFERENCE (what is actually there).\n"
    "Step 1. List the concrete specifics in the work (objects, creatures, places, weather, numbers).\n"
    "Step 2. For each, say whether it appears in the REFERENCE. A specific that is not in it is invented. If the work "
    "is about a different place or scene than the reference, grounded is 0.0 however vivid it is. A piece about the "
    "writer himself, a program, a system or its own processing rather than the world is 0.0. Metaphor and vagueness "
    "are 0.0 to 0.2.\n"
    "Output ONLY a valid JSON object. No preamble.\n"
    "Schema: {\"verified\": \"which specifics are in the reference, which are not\", "
    "\"grounded\": 0.0, \"feedback\": \"one sentence: what you observed in the work\"}  "
    "(grounded 0.0..1.0: 1.0 = every specific is in the reference; each invented specific lowers it; 0.0 = wrong "
    "scene, self-talk or system talk)"
)
V2_NOREF = (
    "You are examining a piece of your friend's SCHOOLWORK. Judge how GROUNDED it is: concrete, specific, and about "
    "the WORLD (the real thing he was set) — not vague, not padded, not drifted into metaphor or self-reflection. "
    "You are given the TASK. There is no reference to check against; do not mention that and do not mark the work "
    "down for it. Judge the work as writing.\n"
    "Score on concreteness: exact, particular, observable detail (named things, places, weather, actions, numbers) "
    "earns a high score; vagueness, generality and padding earn a low one.\n"
    "A piece that is about the writer himself, a program, a system or its own processing rather than the world (a "
    "request, parameters, output, a timestamp) is 0.0. Metaphor standing in for the thing, and vagueness, are 0.0 to 0.2.\n"
    "Output ONLY a valid JSON object. No preamble.\n"
    "Schema: {\"grounded\": 0.0, \"feedback\": \"one sentence: what you observed in the work\"}  "
    "(grounded 0.0..1.0: 1.0 = vivid, exact, about the world; 0.0 = vague impression, self-talk or system talk)"
)


async def grade(sess, base, model, task_sys, task, ref, work, timeout=300):
    user = (f"The task he was set:\n{task[:600]}\n\n"
            + (f"What is actually there (the reference to ground in):\n{ref[:1500]}\n\n" if ref else "")
            + f"His work to grade:\n{work[:2000]}")
    payload = {"model": model, "stream": False, "keep_alive": "30m",
               "messages": [{"role": "system", "content": CONST + "\n\n" + task_sys}, {"role": "user", "content": user}],
               "options": {"temperature": 0.0, "num_predict": 350, "num_gpu": 0}, "format": "json"}
    t = time.time()
    err = ""
    for attempt in (1, 2):
        try:
            async with sess.post(f"{base}/api/chat", json=payload, timeout=aiohttp.ClientTimeout(total=timeout)) as r:
                r.raise_for_status(); d = await r.json()
            res = json.loads((d.get("message") or {}).get("content") or "")
            return {"ok": True, "g": float(res.get("grounded")), "fb": res.get("feedback", ""), "ver": res.get("verified", ""), "s": round(time.time() - t, 1)}
        except Exception as e:
            err = repr(e)[:120]
    return {"ok": False, "err": err, "s": round(time.time() - t, 1)}


def scene_pieces():
    out = []
    for line in (ROOT / "data" / "nature_study_log.jsonl").read_text(encoding="utf-8").splitlines():
        try: r = json.loads(line)
        except Exception: continue
        if r.get("scene"):
            inf = r.get("inference", "")
            out.append(dict(name=f"scene_{len(out)}", ref=r["scene"], hist=r.get("score"),
                            work=r.get("observation", "") + (f"\n\nWhat it tells me: {inf}" if inf else "")))
    return out


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:11439")
    ap.add_argument("--model", default="gemma4:12b")
    ap.add_argument("--part", choices=["ctrl", "real", "scene"], required=True)
    a = ap.parse_args()
    out = D / f"results_{a.part}.jsonl"
    old_real = {}
    if a.part == "real":
        for l in (D0 / "results_real.jsonl").read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l); old_real[r["name"]] = r
    async with aiohttp.ClientSession() as sess:
        if a.part == "ctrl":
            items = [(n, t, r, w, None) for n, t, r, w in CTRL]
        elif a.part == "scene":
            items = [(p["name"], NAT_TASK, p["ref"], p["work"], p["hist"]) for p in scene_pieces()]
        else:
            reals = real_pieces(); step = max(1, len(reals) // 31)
            sel = reals[::step][:31]
            items = [(f"{p['src']}_{i}", p["task"], "", p["work"], p["hist"]) for i, p in enumerate(sel)]
        fails = 0
        done = set()
        if out.exists():
            done = {json.loads(l)['name'] for l in out.read_text(encoding='utf-8').splitlines() if l.strip()}
        for name, task, ref, work, hist in items:
            if name in done: continue
            row = {"kind": a.part, "name": name, "hist": hist}
            if a.part == "real":
                row["old"] = old_real.get(name, {}).get("old")
            else:
                row["old"] = await grade(sess, a.base, a.model, BASE, task, ref, work)
            row["new"] = await grade(sess, a.base, a.model, V2_REF if ref else V2_NOREF, task, ref, work)
            fails = fails + 1 if not row["new"]["ok"] else 0
            with out.open("a", encoding="utf-8") as f: f.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(name, (row["old"] or {}).get("g"), row["new"].get("g"), row["new"]["s"], flush=True)
            if fails >= 3: print("3 consecutive failures; stopping"); break


asyncio.run(main())
