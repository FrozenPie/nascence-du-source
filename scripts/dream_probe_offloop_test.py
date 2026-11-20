"""J-2111: log_seed_pairs rows identical on/off thread; loop stays responsive. Uses a temp log + fake probe_pair."""
import asyncio, sys, tempfile, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import dream_probe as dp
from core.idle_offloop import off_loop
tmp = Path(tempfile.mkdtemp()); dp._PROBE_LOG = tmp / "p.jsonl"
def fake(a, b):
    time.sleep(0.05); return {"edge_exists": False, "edge_types": [], "rank_of_B_in_recall_trail_edge_aware": None, "cosine": 0.5}
dp.probe_pair = fake
ids = [f"f{i}" for i in range(6)]
def rows():
    import json
    return [{k: v for k, v in json.loads(l).items() if k != "ts"} for l in dp._PROBE_LOG.read_text().splitlines()]
n1 = dp.log_seed_pairs("d1", ids); r1 = rows(); dp._PROBE_LOG.unlink()
async def main():
    lag = []
    async def canary():
        for _ in range(20):
            t = time.perf_counter(); await asyncio.sleep(0.02); lag.append(time.perf_counter() - t - 0.02)
    c = asyncio.create_task(canary())
    n = await off_loop(dp.log_seed_pairs, "d1", ids)
    await c
    return n, max(lag)
n2, maxlag = asyncio.run(main()); r2 = rows()
assert n1 == n2 == 15 and r1 == r2, (n1, n2)
assert maxlag < 0.2, maxlag
print("OK rows", n2, "identical; max loop lag %.3fs (probe ~0.75s)" % maxlag)
