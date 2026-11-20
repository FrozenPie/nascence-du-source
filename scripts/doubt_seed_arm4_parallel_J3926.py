"""J-3926 parallel driver: one call queue (J-2052 abs controls first, then arm-4 real, then null), per-hub concurrency.
Writes data/lab/J-3926/calls.jsonl (resumable, one row per judge call). Lab only; lab_env.isolate."""
import asyncio, json, sys, time
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
import core  # noqa
import si_open_doubt_specificity_judge_J2052 as j52
import doubt_seed_arm4_judge_J3926 as a4
CALLS = a4.OUT / "calls.jsonl"; CONC = int(sys.argv[1]) if len(sys.argv) > 1 else 4
DEADLINE = time.time() + float(sys.argv[2]) * 60 if len(sys.argv) > 2 else time.time() + 3000

async def main():
    a4.OUT.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(Path.home() / ".claude/skills/job-queue"))
    import lab_env, aiohttp
    from core import judge_panel
    hubs = {"mixtral": judge_panel.JUDGE_1, "falcon": judge_panel.JUDGE_2}
    done = {d["key"] for d in a4.jl(CALLS)} if CALLS.exists() else set()
    old = {r["id"]: r for r in a4.jl(j52.OUT / "abs.jsonl")}
    jobs = []
    for iid, ctx, cand, kind in j52.items("abs"):
        user = j52.USER_ABS.format(thought=ctx["thought"][:400], reflection=ctx["reflection"][:400], cand=cand[:600])
        jobs.append(("ctl", iid, kind, user))
    w, rows = a4.prep()
    for arm in ("real", "null"):
        for k, r in enumerate(rows):
            cand = r["cand"] if arm == "real" else rows[(k + 7) % len(rows)]["cand"]
            user = j52.USER_ABS.format(thought=r["orig"][:400], reflection=r["reflection"][:400], cand=cand[:600])
            jobs.append((arm, r["cycle_id"], "seeded" if r["seeded"] else "unseeded", user))
    q = {h: asyncio.Queue() for h in hubs}
    for j in jobs:
        for h in hubs:
            key = f"{j[0]}|{j[1]}|{h}"
            if key in done: continue
            if j[0] == "ctl" and old.get(j[1], {}).get(h) is not None: continue
            q[h].put_nowait((key, j))
    async def worker(h, s):
        while time.time() < DEADLINE:
            try: key, j = q[h].get_nowait()
            except asyncio.QueueEmpty: return
            v, err, sec = await j52.ask(s, hubs[h], j52.SYS_ABS, j[3], "score", 1, 5)
            if err: v, err, sec = await j52.ask(s, hubs[h], j52.SYS_ABS, j[3], "score", 1, 5)
            with open(CALLS, "a", encoding="utf-8") as f:
                f.write(json.dumps(dict(key=key, arm=j[0], id=j[1], kind=j[2], hub=h, v=v, err=err, s=sec)) + "\n")
            print(key[:50], v, err, sec, flush=True)
    with lab_env.isolate(db="empty"):
        async with aiohttp.ClientSession() as s:
            await asyncio.gather(*[worker(h, s) for h in hubs for _ in range(CONC)])
asyncio.run(main())
