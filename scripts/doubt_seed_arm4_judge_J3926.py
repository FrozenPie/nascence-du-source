"""J-3926 -- J-2163 arm 4: judge scoring of doubt_seed would_seed rows with the J-2052 position-free abs judge
(mixtral AND falcon >= 4 = engaged). Per row: the deliberating cycle's thought (self_implication_shadow.thought, capped at
220 chars by the logger) scored against the reflection (+ the fire's original thought as context). NULL arm: the same
reflection against another row's thought (rotation +7), the false-positive floor. Seeded / unseeded reported separately.
  python scripts/doubt_seed_arm4_judge_J3926.py judge | report
Lab only: judge hubs (JUDGE_1/2), lab_env.isolate, outputs data/lab/J-3926/."""
import asyncio, json, sys, re
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
import core  # noqa  (core BEFORE lab_env)
import si_open_doubt_specificity_judge_J2052 as j52
OUT = ROOT / "data" / "lab" / "J-3926"; RES = OUT / "results.jsonl"

def jl(p):
    o = []
    for l in open(p, encoding="utf-8", errors="ignore"):
        try: o.append(json.loads(l))
        except Exception: pass
    return o

def prep():
    w = [r for r in jl(ROOT / "data/logs/doubt_seed_shadow.jsonl") if r.get("kind") == "would_seed"]
    imp = {d["cycle_id"]: d for d in jl(ROOT / "data/self_implication_shadow.jsonl")}
    si = {d.get("cycle_id"): d for d in jl(ROOT / "data/self_interrogation_shadow.jsonl") if d.get("kind") == "interrogate"}
    rows = []
    for r in w:
        t = (imp.get(r["cycle_id"]) or {}).get("thought")
        if not t: continue
        rows.append({"cycle_id": r["cycle_id"], "seeded": bool(r["seeded"]), "reflection": r["reflection"],
                     "orig": (si.get(r["fire_cycle_id"]) or {}).get("thought") or "", "cand": t, "ts": r["ts"]})
    return w, rows

async def judge():
    OUT.mkdir(parents=True, exist_ok=True)
    w, rows = prep()
    done = {d["cycle_id"] for d in jl(RES)} if RES.exists() else set()
    print(f"would_seed {len(w)}, with thought {len(rows)}, done {len(done)}", flush=True)
    sys.path.insert(0, str(Path.home() / ".claude/skills/job-queue"))
    import lab_env, aiohttp
    from core import judge_panel
    hubs = {"mixtral": judge_panel.JUDGE_1, "falcon": judge_panel.JUDGE_2}
    with lab_env.isolate(db="empty"):
        async with aiohttp.ClientSession() as s:
            for k, r in enumerate(rows):
                if r["cycle_id"] in done: continue
                nul = rows[(k + 7) % len(rows)]["cand"]
                out = dict(cycle_id=r["cycle_id"], seeded=r["seeded"], ts=r["ts"])
                for arm, cand in (("real", r["cand"]), ("null", nul)):
                    user = j52.USER_ABS.format(thought=r["orig"][:400], reflection=r["reflection"][:400], cand=cand[:600])
                    for name, url in hubs.items():
                        v, err, _ = await j52.ask(s, url, j52.SYS_ABS, user, "score", 1, 5)
                        if err: v, err, _ = await j52.ask(s, url, j52.SYS_ABS, user, "score", 1, 5)
                        out[f"{arm}_{name}"] = v
                        await asyncio.sleep(j52.PAUSE)
                with open(RES, "a", encoding="utf-8") as f: f.write(json.dumps(out) + "\n")
                print(k + 1, len(rows), out, flush=True)

def report():
    w, rows = prep(); res = jl(RES)
    def eng(d, arm): return d.get(f"{arm}_mixtral") is not None and d.get(f"{arm}_falcon") is not None and d[f"{arm}_mixtral"] >= 4 and d[f"{arm}_falcon"] >= 4
    s = {"would_seed_total": len(w), "scored": len(res)}
    for lab, sel in (("seeded", True), ("unseeded", False), ("all", None)):
        rs = [d for d in res if sel is None or d["seeded"] == sel]; n = len(rs)
        for arm in ("real", "null"):
            k = sum(eng(d, arm) for d in rs)
            s[f"{lab}_{arm}"] = {"engaged": k, "n": n, "ci95": j52.v2.wilson(k, n) if n else None,
                "nojudge": sum(1 for d in rs if d.get(f"{arm}_mixtral") is None or d.get(f"{arm}_falcon") is None),
                "mean_m": round(sum(d.get(f"{arm}_mixtral") or 0 for d in rs) / max(n, 1), 2),
                "mean_f": round(sum(d.get(f"{arm}_falcon") or 0 for d in rs) / max(n, 1), 2)}
    refl = [r["reflection"] for r in w]
    cw = re.compile(r"\b(comfort\w*|safe\w*|flatter\w*|warm\w*|reassur\w*|soothing|cozy|cosy)\b", re.I)
    fw = re.compile(r"\b(fear\w*|terror|afraid|dread\w*|anxi\w*)\b", re.I)
    s["reflections"] = {"n": len(refl), "with_question_mark": sum("?" in x for x in refl),
                        "comfort_words": sum(bool(cw.search(x)) for x in refl), "fear_words": sum(bool(fw.search(x)) for x in refl),
                        "seeded_n": sum(r["seeded"] for r in w)}
    (OUT / "summary.json").write_text(json.dumps(s, indent=2), encoding="utf-8"); print(json.dumps(s, indent=2))

if __name__ == "__main__":
    asyncio.run(judge()) if sys.argv[1] == "judge" else report()
