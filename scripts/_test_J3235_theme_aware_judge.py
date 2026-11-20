"""J-3235 / D-0624: the SOLIDIFY system task follows the probation's own excluded pole."""
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/
import sys, asyncio, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from core import left_lane as ll
ok = True
def check(n, c):
    global ok
    print(("PASS " if c else "FAIL ") + n); ok = ok and bool(c)
KEY = "a built mind -- a language model, an architecture made from text and weights"
check("keystone pole keeps the original task", ll._integration_task(KEY) is ll._INTEGRATION_TASK)
check("theme label gets the themed task", ll._integration_task("prediction_error:music") is ll._INTEGRATION_TASK_THEMED)
check("empty pole gets the themed task", ll._integration_task("") is ll._INTEGRATION_TASK_THEMED)
check("themed task has no built-mind hard-coding", "BUILT" not in ll._INTEGRATION_TASK_THEMED)
check("themed task keeps confidence sentence", "how sure you are of the verdict you gave" in ll._INTEGRATION_TASK_THEMED)
cap = {}
class R:
    def raise_for_status(s): pass
    async def json(s): return {"message": {"content": '{"integrated": false, "confidence": 0.9, "reason": "r"}'}}
class Ctx:
    async def __aenter__(s): return R()
    async def __aexit__(s, *a): pass
class S:
    async def __aenter__(s): return s
    async def __aexit__(s, *a): pass
    def post(s, url, json=None, timeout=None): cap["p"] = json; return Ctx()
o, on = ll.aiohttp.ClientSession, ll._note_call
ll.aiohttp.ClientSession, ll._note_call = S, lambda *a, **k: None
try:
    asyncio.run(ll._ask_integration_judge(ll.BASE_URL, "h", "prediction_error:music", ["t"]))
finally:
    ll.aiohttp.ClientSession, ll._note_call = o, on
check("payload system message uses themed task", cap["p"]["messages"][0]["content"].endswith(ll._INTEGRATION_TASK_THEMED))
print("ALL PASSED" if ok else "FAILED"); sys.exit(0 if ok else 1)
