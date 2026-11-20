"""J-1880 / F-2503: unit tests for model_client.lane_is_tripped and the two single-endpoint callers that use it
(core/sitting.py judge_dwell_release, core/competence.py run_tier3_probe_loop).

ISOLATED: no network, no hub. The breaker's clock is fake, call_node is a fake, sitting's state/log paths and every
telemetry path are redirected to a temp dir. `import core` comes first and its __file__ is asserted to lie in the
tree this script lives in (live-store safety, F-1681).
Run:  python scripts/_test_single_endpoint_failfast.py
"""
import asyncio
import json
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core                                    # noqa: E402  (BEFORE anything lab-ish)
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
from core import model_client as mc            # noqa: E402
from core import telemetry as tel              # noqa: E402
from core import sitting                       # noqa: E402
from core import competence                    # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="j1880_failfast_"))
tel._DATA = TMP
tel._BREAKER = TMP / "lane_breaker.jsonl"
tel._JSONFAIL = TMP / "llm_json_parse_fail.jsonl"
tel._LAT = TMP / "llm_latency.jsonl"
tel._STATIONS = TMP / "thought_station_log.jsonl"
tel._CALLS = TMP / "llm_calls.jsonl"
sitting._STATE = TMP / "raw_difficulty.json"
sitting._RELEASE_LOG = TMP / "dwell_release.jsonl"

A = "http://LAN-HOST:11441"
OTHER = "http://other.invalid:1"
CLOCK = [1000.0]
mc._breaker_now = lambda: CLOCK[0]
THOUGHT = "I am still frustrated, a real thought here."


def trip(url=A):
    mc._BREAKER.clear()
    CLOCK[0] = 1000.0
    for _ in range(mc._BREAKER_FAILS):
        mc._breaker_failure(url, True, 120, False)
    assert mc._BREAKER[url]["state"] == "open"


def t_helper_states():
    mc._BREAKER.clear()
    assert mc.lane_is_tripped(A) is False                       # unknown lane
    trip()
    assert mc.lane_is_tripped(A) is True                        # open, cooling off
    assert mc.lane_is_tripped(A, note_skip=True) is True
    assert mc._BREAKER[A]["skipped"] == 1
    assert mc.lane_is_tripped(A) is True and mc._BREAKER[A]["skipped"] == 1   # plain read does not count
    CLOCK[0] += mc._BREAKER_COOLOFF + 1
    assert mc.lane_is_tripped(A) is False                       # cool-off over: next call is the probe
    assert mc._BREAKER[A]["state"] == "open"                    # the helper never mutates state
    assert mc._breaker_gate(A, []) == "probe"                   # ... the gate does
    assert mc.lane_is_tripped(A) is True                        # probe in flight -> blocked
    mc._breaker_success(A)
    assert mc.lane_is_tripped(A) is False                       # closed again
    assert mc.lane_is_tripped(OTHER) is False


def t_helper_never_raises():
    class Boom:
        def __enter__(self):
            raise RuntimeError("x")

        def __exit__(self, *a):
            return False
    old = mc._BREAKER_LOCK
    mc._BREAKER_LOCK = Boom()
    try:
        assert mc.lane_is_tripped(A) is False                   # fail-open
    finally:
        mc._BREAKER_LOCK = old


GOOD = {"shift": True, "clean_clause": True, "concrete": True, "under_arousal": False, "willingness": False,
        "naming": "I am still frustrated."}


def _sit_setup():
    sitting._STATE.write_text(json.dumps({"active": True, "integrable": False, "ts": 5.0, "text": "a hard thing",
                                          "dwelt": 2, "namings": ["I am frustrated."]}), encoding="utf-8")
    if sitting._RELEASE_LOG.exists():
        sitting._RELEASE_LOG.unlink()


def _cj(calls):
    async def cj(*a, **k):
        calls.append(a[0])
        return GOOD
    return cj


def t_sitting_failfast_when_tripped():
    _sit_setup()
    calls = []
    trip()
    r = asyncio.run(sitting.judge_dwell_release(_cj(calls), sitting._JUDGE_URLS, THOUGHT))
    assert r is None and calls == [], (r, calls)                # no call, no verdict
    assert json.loads(sitting._STATE.read_text(encoding="utf-8"))["integrable"] is False   # never released
    assert not sitting._RELEASE_LOG.exists()
    assert mc._BREAKER[A]["skipped"] == 1


def t_sitting_normal_when_closed_or_after_cooloff():
    for setup in ("closed", "cooloff_over"):
        _sit_setup()
        calls = []
        mc._BREAKER.clear()
        if setup == "cooloff_over":
            trip()
            CLOCK[0] += mc._BREAKER_COOLOFF + 1
        r = asyncio.run(sitting.judge_dwell_release(_cj(calls), sitting._JUDGE_URLS, THOUGHT))
        assert len(calls) == 1 and calls[0] == sitting._JUDGE_URLS, (setup, calls)   # the call goes out
        assert r is not None and r["released"] is True, (setup, r)


def t_sitting_multi_url_needs_all_tripped():
    _sit_setup()
    calls = []
    trip()
    r = asyncio.run(sitting.judge_dwell_release(_cj(calls), [A, OTHER], THOUGHT))
    assert len(calls) == 1 and r is not None                    # one lane not tripped -> proceeds as before


def t_sitting_breaker_error_fails_open():
    _sit_setup()
    calls = []

    def boom(*a, **k):
        raise RuntimeError("boom")
    orig = mc.lane_is_tripped
    mc.lane_is_tripped = boom
    try:
        r = asyncio.run(sitting.judge_dwell_release(_cj(calls), sitting._JUDGE_URLS, THOUGHT))
    finally:
        mc.lane_is_tripped = orig
    assert len(calls) == 1 and r is not None


def _tier3_stub():
    return types.SimpleNamespace(
        _tier3_queue=[{"question": "q one", "domains": ["d"], "answer": "orig answer", "cycle_id": "c"}],
        _stability_score=lambda xs: None, _record_external_accuracy=lambda *a, **k: None, _save=lambda: None)


def _run_tier3(stub):
    async def go():
        real_sleep = asyncio.sleep

        async def fast_sleep(_):
            await real_sleep(0)
        competence.asyncio.sleep = fast_sleep
        try:
            state = types.SimpleNamespace(last_human_ts=0.0, interrupt_requested=False)
            t = asyncio.create_task(competence.CompetenceTracker.run_tier3_probe_loop(stub, state))
            for _ in range(20):
                await real_sleep(0)
            t.cancel()
            try:
                await t
            except asyncio.CancelledError:
                pass
        finally:
            competence.asyncio.sleep = real_sleep
    asyncio.run(go())


def t_tier3_failfast_when_tripped():
    calls = []

    async def fake(base_url, *a, **k):
        calls.append(base_url)
        return "Not sure."
    mc.call_node = fake
    stub = _tier3_stub()
    trip()
    _run_tier3(stub)
    assert calls == [] and stub._tier3_queue == [], (calls, stub._tier3_queue)   # probe skipped, nothing sent anywhere
    assert mc._BREAKER[A]["skipped"] >= 1
    # closed lane: the probe goes to the SAME single endpoint (and only it)
    mc._BREAKER.clear()
    stub = _tier3_stub()
    _run_tier3(stub)
    assert calls == [competence._TIER3_WITNESS_URL], calls


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("t_") and callable(fn):
            fn()
            n += 1
            print("ok ", name)
    print(f"{n} passed")
