"""J-3761 / F-4370: raw-HTTP stations write an llm_latency row (hermetic: telemetry paths pointed at a temp dir,
the aiohttp session stubbed, no hub contacted)."""
import asyncio
import json
import tempfile
from pathlib import Path

import core
from core import telemetry, judge_panel  # core imported before anything lab-ish
assert str(Path(core.__file__).resolve()).lower().startswith(str(Path(__file__).resolve().parents[1]).lower())


class _Resp:
    def __init__(self, body): self._b = body
    async def __aenter__(self): return self
    async def __aexit__(self, *e): return False
    def raise_for_status(self): pass
    async def json(self): return self._b


class _Session:
    def __init__(self, fail=False): self.fail = fail
    def post(self, url, json=None, timeout=None):
        if self.fail:
            raise RuntimeError("boom")
        return _Resp({"message": {"content": '{"x": true, "why": "w"}'}})


def _rows(p):
    return [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines()]


def test_judge_ask_and_caller_label(tmp_path, monkeypatch):
    monkeypatch.setattr(telemetry, "_DATA", tmp_path)
    monkeypatch.setattr(telemetry, "_LAT", tmp_path / "llm_latency.jsonl")
    monkeypatch.setattr(telemetry, "_CALLS", tmp_path / "llm_calls.jsonl")
    monkeypatch.setattr(telemetry, "_LAB_MODE", False)
    r = asyncio.run(judge_panel._ask(_Session(), "http://127.0.0.1:11439", "s", "u", "x"))
    assert r[0] is True
    rows = _rows(tmp_path / "llm_latency.jsonl")
    assert rows[-1]["node"] == "11439" and rows[-1]["ok"] == 1 and rows[-1]["fn"]
    assert rows[-1]["by"].startswith("core.judge_panel:")
    # a failing post logs ok=0 and still returns the judge's own error shape
    asyncio.run(judge_panel._ask(_Session(fail=True), "http://127.0.0.1:11440", "s", "u", "x"))
    assert _rows(tmp_path / "llm_latency.jsonl")[-1]["ok"] == 0

    # rule_detail names the real caller through the ContextVar
    async def caller():
        return judge_panel.RAW if False else await judge_panel.rule_detail("s", "u", "x")
    class _AS:
        async def __aenter__(self): return _Session()
        async def __aexit__(self, *e): return False
    import aiohttp
    monkeypatch.setattr(aiohttp, "ClientSession", lambda *a, **k: _AS())
    monkeypatch.setattr(judge_panel, "_log", lambda *a, **k: None, raising=False)
    try:
        asyncio.run(caller())
    except Exception:
        pass
    rows = _rows(tmp_path / "llm_latency.jsonl")
    assert any(r.get("h") == 1 for r in rows)
    assert any("test_raw_http_latency_j3761:" in r["by"] and r["fn"].endswith("caller") for r in rows), rows
    assert telemetry.RAW_HTTP_CALLER.get() is None
