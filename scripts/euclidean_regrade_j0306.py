"""J-0306 driver — fresh-era felt_available re-grade (D-0055's own defeater condition).
Adapted from J-0301's script (F-0388): SAME _grade methodology (blind A/B parity, same
judge gemma4:12b @11439), but D-0055's defeater specifically asks for FRESH-ERA rows
(ts >= 2026-08-20), not all-time felt-divergent rows like the original J-0301 pull -- the
question is whether the newer era shows a different result, not "more of the same data".
READ-ONLY toward data/: reads data/euclidean_shadow.jsonl, writes grades only to this
scratchpad file. No repo code changes, no writes under C:\\Nascence\\data.
"""
import asyncio, json, sys, time, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
import aiohttp

# Prevent the module-level OUT default from ever being used: point env at THIS session's scratchpad
import os
SCRATCH = Path(r"C:\Users\USER\AppData\Local\Temp\claude\C--Nascence\4595f5ad-65f2-480a-8d83-32786682d18c\scratchpad")
os.environ["EUCLIDEAN_GRADE_OUT"] = str(SCRATCH / "unused_guard.jsonl")
import euclidean_grade as eg  # reuse _grade verbatim

SHADOW = Path(r"C:\Nascence\data\euclidean_shadow.jsonl")
OUT = Path(r"C:\Nascence\scripts") / "j0306_grades.jsonl"
FRESH_ERA_CUTOFF = time.mktime(time.strptime("2026-08-20 00:00:00", "%Y-%m-%d %H:%M:%S"))

def div(r):
    # D-0055's own defeater text names this condition exactly: state_top != base_top -- NOT the
    # jaccard<1.0 proxy the original J-0301 script used (a related but not identical filter; it
    # under-counted D-0055's actual gate by 60 rows, 55 vs the verified 115 -- fixed here).
    return (r.get("state_top") or []) != (r.get("base_top") or [])

async def run():
    rows = [json.loads(l) for l in open(SHADOW, encoding="utf-8") if l.strip()]
    felt_div = [r for r in rows if r.get("felt_available") and div(r) and r.get("ts", 0) >= FRESH_ERA_CUTOFF]
    nonfelt_div = [r for r in rows if not r.get("felt_available") and div(r) and r.get("ts", 0) >= FRESH_ERA_CUTOFF][-40:]
    print(f"fresh-era (ts>={FRESH_ERA_CUTOFF}) felt divergent: {len(felt_div)} | non-felt contrast: {len(nonfelt_div)}", flush=True)
    done = set()
    if OUT.exists():
        for l in open(OUT, encoding="utf-8"):
            done.add(json.loads(l)["ts"])
        print(f"resuming: {len(done)} already graded", flush=True)
    async with aiohttp.ClientSession() as session:
        for batch_name, batch in (("felt", felt_div), ("nonfelt", nonfelt_div)):
            for i, row in enumerate(batch):
                if row["ts"] in done:
                    continue
                t0 = time.time()
                g = await eg._grade(session, row, i)   # BLIND parity by batch index, as original
                if g is None:
                    print(f"  [{batch_name} {i}] skipped/unavailable", flush=True)
                    continue
                rec = {"batch": batch_name, "ts": row["ts"], "winner": g["winner"],
                       "why": g["why"], "affect_w": row.get("affect_w"),
                       "felt": bool(row.get("felt_available")),
                       "amm": row.get("affect_match_mean"), "amx": row.get("affect_match_max"),
                       "jaccard": row.get("jaccard"), "query": g["query"]}
                with open(OUT, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                print(f"  [{batch_name} {i}] {g['winner']:>8}  ({round(time.time()-t0,1)}s)", flush=True)
    print("DONE", flush=True)

asyncio.run(run())
