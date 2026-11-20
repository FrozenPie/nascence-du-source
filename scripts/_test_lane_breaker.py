"""J-1832 / F-2466: unit tests for call_node_json's per-lane circuit breaker (core/model_client.py).

ISOLATED: call_node is replaced by a fake (no network, no hub), the breaker's clock is a fake, and every
telemetry file path the code under test can reach is redirected to a temp dir. `import core` comes first
and its __file__ is asserted to lie in the tree this script lives in (live-store safety, F-1681).
Run:  python scripts/_test_lane_breaker.py
"""
import asyncio
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core                                    # noqa: E402  (BEFORE anything lab-ish)
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
import aiohttp                                 # noqa: E402
from core import model_client as mc            # noqa: E402
from core import telemetry as tel              # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="j1832_breaker_"))
tel._DATA = TMP
tel._BREAKER = TMP / "lane_breaker.jsonl"
tel._JSONFAIL = TMP / "llm_json_parse_fail.jsonl"
tel._LAT = TMP / "llm_latency.jsonl"
tel._STATIONS = TMP / "thought_station_log.jsonl"
tel._CALLS = TMP / "llm_calls.jsonl"

A, B = "http://LAN-HOST:11441", "http://127.0.0.1:11433"

CLOCK = [1000.0]
mc._breaker_now = lambda: CLOCK[0]


class Fake:
    """Scripted call_node: per base_url a list of outcomes consumed in order (last one repeats)."""
    def __init__(self, script):
        self.script, self.calls = script, []

    async def __call__(self, base_url, system_prompt, user_prompt, **kw):
        self.calls.append(base_url)
        seq = self.script[base_url]
        out = seq.pop(0) if len(seq) > 1 else seq[0]
        if callable(out):
            out = await out()
        if isinstance(out, BaseException):
            raise out
        return out


OK = '{"ok": true}'
TO = asyncio.TimeoutError()
CONN = aiohttp.ClientConnectionError("refused")


def reset(script):
    mc._BREAKER.clear()
    CLOCK[0] = 1000.0
    f = Fake(script)
    mc.call_node = f
    if tel._BREAKER.exists():
        tel._BREAKER.unlink()
    return f


def rows():
    if not tel._BREAKER.exists():
        return []
    return [json.loads(l) for l in tel._BREAKER.read_text(encoding="utf-8").splitlines() if l.strip()]


def run(chain, **kw):
    kw.setdefault("timeout", 120)
    kw.setdefault("retries", 2)
    return asyncio.run(mc.call_node_json(chain, "s", "u", **kw))


def t_trips_after_three_and_skips():
    f = reset({A: [TO], B: [OK]})
    for _ in range(3):
        assert run([A, B]) == {"ok": True}
    assert f.calls == [A, B] * 3, f.calls              # each of the first 3 still paid the A attempt
    assert mc._BREAKER[A]["state"] == "open"
    f.calls.clear()
    assert run([A, B]) == {"ok": True}
    assert f.calls == [B], f.calls                     # 4th: A skipped outright
    assert mc._BREAKER[A]["skipped"] == 1
    assert [r["event"] for r in rows()] == ["open"], rows()


def t_two_timeouts_do_not_trip_and_success_resets():
    f = reset({A: [TO, TO, OK, TO, TO], B: [OK]})
    for _ in range(2):
        run([A, B])
    run([A, B])                                        # A answers -> streak reset
    for _ in range(2):
        run([A, B])
    assert mc._BREAKER[A]["state"] == "closed" and mc._BREAKER[A]["fails"] == 2
    assert rows() == []


def t_single_endpoint_chain_never_skipped():
    f = reset({A: [TO]})
    for _ in range(5):
        try:
            run([A])
            raise AssertionError("should have raised")
        except ValueError:
            pass
    assert mc._BREAKER[A]["state"] == "open"
    assert f.calls == [A] * 5, f.calls                 # still attempted every time (fail-open)


def t_all_tripped_still_attempts():
    f = reset({A: [TO], B: [TO]})
    for _ in range(3):
        try:
            run([A, B])
        except ValueError:
            pass
    assert mc._BREAKER[A]["state"] == "open" and mc._BREAKER[B]["state"] == "open"
    f.calls.clear()
    try:
        run([A, B])
    except ValueError:
        pass
    assert f.calls == [A, B], f.calls                  # nowhere better: both tried


def t_probe_close_cycle_and_log():
    f = reset({A: [TO, TO, TO, OK], B: [OK]})
    for _ in range(3):
        run([A, B])
    CLOCK[0] += 100
    f.calls.clear()
    run([A, B])
    assert f.calls == [B]                              # still cooling off
    CLOCK[0] += 201                                    # past 300 s since opening
    f.calls.clear()
    run([A, B])
    assert f.calls == [A], f.calls                     # the probe went through to A and succeeded
    assert mc._BREAKER[A]["state"] == "closed"
    run([A, B])
    ev = rows()
    assert [r["event"] for r in ev] == ["open", "half_open", "close"], ev
    assert ev[0]["cooloff"] == 300.0
    assert ev[2]["skipped"] == 1 and abs(ev[2]["open_s"] - 301) < 1, ev[2]
    assert ev[2]["node"] == "11441" and ev[2]["url"] == A


def t_probe_fail_reopens():
    f = reset({A: [TO], B: [OK]})
    for _ in range(3):
        run([A, B])
    CLOCK[0] += 301
    f.calls.clear()
    run([A, B])
    assert f.calls == [A, B], f.calls                  # probe tried A (timed out), then fell to B
    assert mc._BREAKER[A]["state"] == "open"
    f.calls.clear()
    run([A, B])
    assert f.calls == [B]                              # a fresh cool-off began at the probe failure
    assert [r["event"] for r in rows()] == ["open", "half_open", "reopen"]


def t_only_one_probe_at_a_time():
    async def go():
        gate = asyncio.Event()

        async def slow_ok():
            await gate.wait()
            return OK
        f = Fake({A: [slow_ok], B: [OK]})
        mc._BREAKER.clear()
        mc._BREAKER[A] = {"state": "open", "fails": 3, "opened_at": CLOCK[0] - 400, "since": CLOCK[0] - 400,
                          "skipped": 0, "probe": False}
        mc.call_node = f
        t1 = asyncio.create_task(mc.call_node_json([A, B], "s", "u"))
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        assert mc._BREAKER[A]["state"] == "half_open" and mc._BREAKER[A]["probe"]
        r2 = await mc.call_node_json([A, B], "s", "u")      # second caller while the probe is out
        assert r2 == {"ok": True} and f.calls == [A, B], f.calls
        gate.set()
        assert await t1 == {"ok": True}
        assert mc._BREAKER[A]["state"] == "closed"
    if tel._BREAKER.exists():
        tel._BREAKER.unlink()
    asyncio.run(go())


def t_cancelled_probe_is_released():
    async def go():
        async def hang():
            await asyncio.sleep(3600)
        mc._BREAKER.clear()
        mc._BREAKER[A] = {"state": "open", "fails": 3, "opened_at": CLOCK[0] - 400, "since": CLOCK[0] - 400,
                          "skipped": 0, "probe": False}
        mc.call_node = Fake({A: [hang], B: [OK]})
        t = asyncio.create_task(mc.call_node_json([A, B], "s", "u"))
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        assert mc._BREAKER[A]["state"] == "half_open"
        t.cancel()
        try:
            await t
        except asyncio.CancelledError:
            pass
        st = mc._BREAKER[A]
        assert st["state"] == "open" and not st["probe"], st      # handed back, not stuck half-open
        assert mc._breaker_gate(A, [B]) == "probe"                # next caller can probe at once
    asyncio.run(go())


def t_short_timeout_and_fast_errors_do_not_count():
    f = reset({A: [TO], B: [OK]})
    for _ in range(5):
        run([A, B], timeout=10)                        # below _BREAKER_MIN_TIMEOUT
    assert mc._BREAKER[A]["fails"] == 0 and mc._BREAKER[A]["state"] == "closed"
    f = reset({A: [CONN], B: [OK]})
    for _ in range(5):
        run([A, B])                                    # connection refused: fast, not counted
    assert mc._BREAKER[A]["fails"] == 0 and mc._BREAKER[A]["state"] == "closed"
    assert f.calls == [A, B] * 5


def t_parse_failure_counts_as_alive():
    f = reset({A: [TO, TO, "not json at all", "not json", "not json", OK], B: [OK]})
    run([A, B]); run([A, B])                           # fails == 2
    run([A, B], retries=2)                             # A answers junk x3 -> content failure, lane alive
    assert mc._BREAKER[A]["fails"] == 0, mc._BREAKER[A]


def t_breaker_bug_fails_open():
    class Boom(dict):
        def get(self, *a, **k):
            raise RuntimeError("boom")
        def setdefault(self, *a, **k):
            raise RuntimeError("boom")
    f = reset({A: [TO], B: [OK]})
    orig = mc._BREAKER
    mc._BREAKER = Boom()
    try:
        for _ in range(4):
            assert run([A, B]) == {"ok": True}
        assert f.calls == [A, B] * 4                   # prior behaviour exactly
    finally:
        mc._BREAKER = orig


def t_lab_mode_no_log():
    reset({A: [TO], B: [OK]})
    tel.enter_lab_mode()
    try:
        for _ in range(3):
            run([A, B])
    finally:
        tel.exit_lab_mode()
    assert mc._BREAKER[A]["state"] == "open" and rows() == []


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for t in tests:
        t()
        print("PASS", t.__name__)
    print(f"{len(tests)} passed; temp dir {TMP}")


if __name__ == "__main__":
    main()
