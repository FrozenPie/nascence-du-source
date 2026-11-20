"""J-2674 step 1: READ-ONLY wall-clock/rows/memory measurement of every full-scan reader of
data/geometry_tuples.jsonl. No behaviour change; opens the live file read-only. Usage:
  python scripts/j2674_tuple_reader_measure.py [path-to-geometry_tuples.jsonl] [reps]
Prints a JSON summary (counts/timings only)."""
import json, sys, time, tracemalloc
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  (import core first)
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
from core import object_graph as og, mapping_census as mc  # noqa: E402

P = Path(sys.argv[1] if len(sys.argv) > 1 else r"C:\Nascence\data\geometry_tuples.jsonl")
REPS = int(sys.argv[2]) if len(sys.argv) > 2 else 3

def timed(fn):
    ts = []
    out = None
    for _ in range(REPS):
        t0 = time.perf_counter(); out = fn(); ts.append(time.perf_counter() - t0)
    return out, [round(x, 2) for x in ts]

def scan_sync(floor=0.0):  # the sync_fragment_context() scan loop, verbatim shape (no DB)
    n = kept = 0
    for line in open(P, encoding="utf-8"):
        if not line.strip(): continue
        try: t = json.loads(line)
        except Exception: continue
        n += 1
        if (t.get("ts") or 0) < floor: continue
        if t.get("source") not in ("idle", "monologue", "monologue_train"): continue
        th = " ".join((t.get("thought") or "").split())
        if len(th) < 30: continue
        kept += 1
    return n, kept

res = {"file": str(P), "bytes": P.stat().st_size, "reps": REPS}
rows, ts = timed(lambda: og._load_tuples(P))
res["object_graph._load_tuples"] = {"rows": len(rows), "secs": ts}
r2, ts = timed(lambda: mc.load_rows(P))
res["mapping_census.load_rows"] = {"rows": len(r2), "secs": ts}
del r2
# floor = last-hour like a steady-state sync: scan still parses every line
last = max(t["ts"] for t in rows)
(n, kept), ts = timed(lambda: scan_sync(last - 3600))
res["sync_fragment_context scan (1h floor)"] = {"rows_parsed": n, "rows_kept": kept, "secs": ts}
# memory: retained size of the proposed cache payload (ts float, sounds list, affect dict)
tracemalloc.start()
keep = og._load_tuples(P)
cur, peak = tracemalloc.get_traced_memory(); tracemalloc.stop()
res["retained_og_dicts_MB"] = round(cur / 1e6, 1); res["peak_during_load_MB"] = round(peak / 1e6, 1)
print(json.dumps(res, indent=1))
