"""J-2675 test: call_node carries the hub's token counts onto the llm_latency row (additive); the reader works.
Runs from the worktree; asserts its own tree; stubs aiohttp (no hub is called); every telemetry/shadow path is
pointed at a temp dir; touches no live data."""
import asyncio
import json
import sys
import tempfile
from pathlib import Path

TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core  # noqa: E402,F401
try:
    import lab_env  # noqa: E402,F401
except Exception:
    pass
assert Path(core.__file__).resolve().is_relative_to(TREE), core.__file__
from core import model_client, telemetry, speech_timing_shadow  # noqa: E402
assert Path(model_client.__file__).resolve().is_relative_to(TREE)
sys.path.insert(0, str(TREE / "scripts"))
import prefill_share_report as rep  # noqa: E402

tmp = Path(tempfile.mkdtemp(prefix="j2675_"))
telemetry._LAB_MODE = False
for name in ("_DATA",):
    setattr(telemetry, name, tmp)
telemetry._CALLS = tmp / "llm_calls.jsonl"
telemetry._LAT = tmp / "llm_latency.jsonl"
telemetry._STATIONS = tmp / "thought_station_log.jsonl"
speech_timing_shadow._LOG = tmp / "sts.jsonl"

# ---- 1. _eval_counts: ns -> s, missing -> absent, junk -> absent, never raises
assert model_client._eval_counts({"prompt_eval_count": 2450, "prompt_eval_duration": 3_000_000_000,
                                  "eval_count": 120, "eval_duration": 2_500_000_000}) == \
    {"pe": 2450, "pe_s": 3.0, "ec": 120, "ec_s": 2.5}
assert model_client._eval_counts({"prompt_eval_count": 10, "eval_count": 5}) == {"pe": 10, "ec": 5}
assert model_client._eval_counts({}) == {} and model_client._eval_counts(None) == {}
assert model_client._eval_counts({"prompt_eval_count": "x", "eval_count": True, "eval_duration": -1}) == {}


# ---- 2. call_node end to end with a stubbed aiohttp session
class _Resp:
    def __init__(self, d): self.d = d
    def raise_for_status(self): pass
    async def json(self): return self.d
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False


class _Sess:
    reply = {}
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False
    def post(self, url, json=None, timeout=None): return _Resp(_Sess.reply)


model_client.aiohttp.ClientSession = _Sess


def run(reply, port="11433"):
    _Sess.reply = reply
    return asyncio.run(model_client.call_node(f"http://127.0.0.1:{port}", "sys", "user", json_mode=False))


def rows():
    p = tmp / "llm_latency.jsonl"
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


out = run({"message": {"content": "hi"}, "prompt_eval_count": 2450, "prompt_eval_duration": 3_000_000_000,
           "eval_count": 100, "eval_duration": 2_000_000_000})
assert out == "hi"
r = rows()[-1]
assert r["pe"] == 2450 and r["pe_s"] == 3.0 and r["ec"] == 100 and r["ec_s"] == 2.0, r
assert {"ts", "model", "node", "by", "s", "ok"} <= set(r), r           # every legacy key still there
# llama.cpp hub style: counts, no durations -> pe/ec present, pe_s/ec_s ABSENT (unknown, not 0)
run({"message": {"content": "yo"}, "prompt_eval_count": 800, "eval_count": 40}, port="11444")
r2 = rows()[-1]
assert r2["pe"] == 800 and r2["ec"] == 40 and "pe_s" not in r2 and "ec_s" not in r2, r2
# a reply with no counts at all -> row exactly as before
run({"message": {"content": "z"}}, port="11440")
r3 = rows()[-1]
assert not ({"pe", "pe_s", "ec", "ec_s"} & set(r3)), r3

# ---- 3. the reader
telemetry_rows = [
    {"ts": 1000.0, "model": "m", "node": "11433", "by": "a:1", "s": 5.0, "ok": 1, "pe": 2000, "pe_s": 3.0, "ec": 50, "ec_s": 1.5},
    {"ts": 1001.0, "model": "m", "node": "11433", "by": "a:1", "s": 7.0, "ok": 1, "pe": 3000, "pe_s": 4.0, "ec": 60, "ec_s": 2.0},
    {"ts": 1002.0, "model": "m", "node": "11433", "by": "b:2", "s": 2.0, "ok": 1},   # old row, no counts
    {"ts": 1003.0, "model": "m", "node": "11433", "by": "a:1", "s": 9.0, "ok": 0, "pe": 1, "pe_s": 1.0},  # failed -> ignored
]
st = telemetry.prefill_share_status(rows=telemetry_rows)["by_caller"]
assert st["a:1"]["n_total"] == 2 and st["a:1"]["med_prompt_tokens"] == 3000
assert abs(st["a:1"]["prefill_share"] - round(7.0 / 12.0, 3)) < 1e-9, st
assert st["b:2"]["n_with_pe"] == 0 and st["b:2"]["prefill_share"] is None and st["b:2"]["med_prompt_tokens"] is None
doc = rep.build(telemetry_rows, [(999.0, 1000.5)], "11433", 0.0, "test")
assert "human turn" in doc and "idle / background" in doc and "a:1" in doc and "APPROXIMATE" in doc
doc2 = rep.build(telemetry_rows, [], None, 0.0, "test")
assert "NONE supplied" in doc2
# log window parser
lg = tmp / "n.log"
lg.write_text("2026-11-07 09:00:00,123 [nascence.orchestrator] [CYCLE abcd1234] human: hello\nother line\n", encoding="utf-8")
w = rep.human_windows_from_log(lg, 120.0)
assert len(w) == 1 and w[0][1] - w[0][0] == 120.0
print("J-2675 test OK")
