"""J-4085 / D-0784 B: done_when second call. Stubbed model, temp-path stores only, no live data."""
import asyncio, json, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  (core BEFORE lab_env)
assert str(core.__file__).lower().startswith(str(ROOT).lower())
from core import commitment_ledger as cl, done_when as dw  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="j4085_"))
dw.STORE = TMP / "done_when.jsonl"; dw.SHADOW_LOG = TMP / "dw_shadow.jsonl"
assert cl._dw_scan_fragment() == "" and dw.scan_fragment() == "", "scan fragment must be reverted"
assert "done_when" not in (cl._SCAN_SYS + cl._dw_scan_fragment())
assert dw.legacy_scan_fragment().strip()

calls = []
async def stub(base_urls, system, user, **kw):
    calls.append((system, user, kw))
    if system == dw.SECOND_CALL_SYS:
        return {"done_when": "when the fire has burned a full night"}
    return None

async def main():
    r = await dw.second_call(stub, ["u"], "I will tend the fire", "I will tend the fire", "abc12345", "cyc")
    assert r == "when the fire has burned a full night"
    rows = [json.loads(l) for l in dw.SHADOW_LOG.read_text().splitlines()]
    assert len(rows) == 1 and rows[0]["done_when"] == r and rows[0]["live"] is False and rows[0]["stand_id"] == "abc12345"
    assert dw.get("commitment", "abc12345") is None, "shadow must not write the side store"
    assert calls[0][2]["temperature"] == 0.0 and calls[0][2]["tier"] == 3
    dw.DONE_WHEN_SECOND_CALL_LIVE = True
    await dw.second_call(stub, ["u"], "t", "s", "live1", "cyc")
    assert dw.get("commitment", "live1")["done_when"] == r
    dw.DONE_WHEN_SECOND_CALL_LIVE = False
    async def boom(*a, **k): raise RuntimeError("x")
    assert await dw.second_call(boom, ["u"], "t", "s", "e1") == ""    # fail-open, error row logged
    assert json.loads(dw.SHADOW_LOG.read_text().splitlines()[-1])["error"] == "RuntimeError"
    # spawn: kill switch off -> no task / no call
    n = len(calls); dw.DONE_WHEN_SECOND_CALL_SHADOW = False
    cl._spawn_done_when_call(stub, ["u"], "t", {"id": "z", "statement": "s"}, "c"); await asyncio.sleep(0.05)
    assert len(calls) == n
    dw.DONE_WHEN_SECOND_CALL_SHADOW = True
    cl._spawn_done_when_call(stub, ["u"], "t", {"id": "z", "statement": "s"}, "c"); await asyncio.sleep(0.05)
    assert len(calls) == n + 1
asyncio.run(main())
assert not str(TMP).lower().startswith("c:\nascence")
print("OK J-4085 done_when second call; tmp", TMP)
