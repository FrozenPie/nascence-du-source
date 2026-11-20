"""J-3802 / D-0696 hermetic test: the order-counterbalance SHADOW arm changes no verdict and logs both orders.
No network (hubs stubbed), live data/ log redirected to a temp path, hash canary on the live log."""
import asyncio, hashlib, json, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import judge_panel as jp
assert Path(jp.__file__).resolve().parent.parent == ROOT
live = ROOT / "data" / "judge_panel_log.jsonl"
h0 = hashlib.sha256(live.read_bytes()).hexdigest() if live.exists() else None
tmp = Path(tempfile.mkdtemp()) / "log.jsonl"
jp._LOG = tmp; jp._DATA = tmp.parent
calls = []
async def fake_ask(session, url, system, user, key, timeout=90, num_predict=200):
    calls.append((url, system))
    if url == jp.JUDGE_2 and jp.first_listed_option(system) is False:
        return False, "rev", None, 0.1          # reversed order flips JUDGE_2
    return True, "w", None, 0.1
jp._ask = fake_ask
class _S:
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False
import types, aiohttp
aiohttp.ClientSession = _S
SYS = 'Judge it. Reply {"genuine": true} or {"genuine": false}.'
def run(): return asyncio.run(jp.rule_detail(SYS, "u", "genuine"))
r_off = run(); n_off = len(calls); calls.clear()
jp.JUDGE_ORDER_SHADOW_ON = True
r_on = run(); n_on = len(calls)
assert n_off == 2 and n_on == 3, (n_off, n_on)
assert r_off == r_on and r_on["verdict"] is True and r_on["how"] == "agreed", (r_off, r_on)
rows = [json.loads(l) for l in tmp.read_text().splitlines()]
assert "v2_rev" not in rows[0] and rows[1]["v2_rev"] is False and rows[1]["order_first"] is True and rows[1]["v2"] is True
calls.clear(); jp.rule_detail  # no-form prompt: no extra call, no extra fields
asyncio.run(jp.rule_detail("no schema here", "u", "genuine")); assert len(calls) == 2
assert "v2_rev" not in json.loads(tmp.read_text().splitlines()[-1])
jp.JUDGE_ORDER_SHADOW_KEYS = frozenset({"other"}); calls.clear(); run(); assert len(calls) == 2
assert jp.reverse_option_order("true|false") == "false|true"
h1 = hashlib.sha256(live.read_bytes()).hexdigest() if live.exists() else None
assert h0 == h1, "live judge_panel_log.jsonl changed"
print("OK")
