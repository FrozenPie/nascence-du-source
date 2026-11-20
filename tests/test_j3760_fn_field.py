"""J-3760 / F-4371: telemetry rows carry `fn` (frame co_qualname) beside `by`; `by` is unchanged. Temp dir only."""
import asyncio, json, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from core import telemetry as tel          # import core BEFORE anything lab-ish
from core import model_client as mc


class _Holder:
    def work(self):
        return mc._caller_label(), mc._caller_fn()

    def nested(self):
        def inner():
            return mc._caller_fn()
        return inner()


def test_fn_matches_label_frame():
    lbl, fn = _Holder().work()
    assert lbl.startswith(__name__ + ":") and lbl.endswith("(_Holder)")
    assert fn == "_Holder.work"
    assert "<locals>" in _Holder().nested()


def test_explicit_label_gives_empty_fn():
    async def go():
        async def inner():
            return mc._caller_label(), mc._caller_fn()
        return await mc.with_call_label("closure:compose_line", inner())
    lbl, fn = asyncio.run(go())
    assert lbl == "closure:compose_line" and fn == ""


def test_rows_additive(monkeypatch=None):
    d = Path(tempfile.mkdtemp(prefix="j3760_"))
    saved = (tel._DATA, tel._LAT, tel._STATIONS, tel._JSONFAIL, tel._CALLS, tel._LAB_MODE)
    try:
        tel._DATA, tel._LAB_MODE = d, False
        tel._LAT, tel._STATIONS, tel._JSONFAIL, tel._CALLS = (d / "l.jsonl", d / "s.jsonl", d / "j.jsonl", d / "c.jsonl")
        tel.log_llm_latency("m", "http://x:11433", "mod:1(C)", 1.0, True, fn="C.f")
        tel.log_llm_latency("m", "http://x:11433", "mod:1(C)", 1.0, True)
        tel.log_thought_station("m", "http://x:11433", "mod:1(C)", fn="C.f")
        tel.log_json_parse_fail("m", "http://x:11433", "mod:1(C)", 0, 0, fn="C.f")
        tel.log_llm_call("m", "http://x:11433", caller="mod:1(C)", fn="C.f")
        for f in (tel._LAT, tel._STATIONS, tel._JSONFAIL, tel._CALLS):
            rows = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines()]
            assert rows[0]["by"].startswith("mod:1") and rows[0]["fn"] == "C.f", f
            if f == tel._LAT:
                assert "fn" not in rows[1] and rows[1]["by"] == "mod:1(C)"
    finally:
        tel._DATA, tel._LAT, tel._STATIONS, tel._JSONFAIL, tel._CALLS, tel._LAB_MODE = saved


def test_rejoin_prefers_logged_fn():
    import rejoin_appendix_a_j2977 as rj
    assert rj.logged_fn({"fn": "A.b.<locals>.c"}) == "A.b.c"
    assert rj.logged_fn({"by": "x:1"}) is None
