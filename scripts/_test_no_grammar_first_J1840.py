"""J-1840 / D-0354: no JSON grammar on the FIRST call_node_json attempt for the :11441 background lane.

Offline: aiohttp.ClientSession is replaced by a scripted fake (no network, no Ramses, no live data).
Telemetry writes are redirected to a temp dir (core.telemetry._DATA/_LAT/_JSONFAIL), never data/.

Checks:
  1. :11441 first attempt carries NO format=json; a parse failure retries WITH format=json (and succeeds).
  2. :11441 with retries=0 keeps the grammar (no second attempt to fall back on).
  3. every other lane (:11433, :11437, :11438) keeps format=json on attempt 1, unchanged.
  4. bare call_node(json_mode=True) on :11441 (no retry owner) keeps the grammar.
  5. llm_latency rows carry g=0/1 on json calls; llm_json_parse_fail.jsonl records the g=0 miss.
  6. transport failure on :11441 first attempt still fails over to the next server (unchanged).
Run from the tree under test:  python scripts/_test_no_grammar_first_J1840.py
"""
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  -- import core BEFORE anything else, then prove which tree it resolved to
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
from core import model_client as mc  # noqa: E402
from core import telemetry as tel    # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="j1840_"))
tel._DATA = TMP
tel._LAT = TMP / "llm_latency.jsonl"
tel._JSONFAIL = TMP / "llm_json_parse_fail.jsonl"
tel._STATIONS = TMP / "stations.jsonl"
tel._CALLS = TMP / "llm_calls.jsonl"

SEEN = []          # (url, had_format_json)
SCRIPT = {}        # url-substring -> list of replies (str) or Exception to raise


class _Resp:
    def __init__(self, text): self._t = text
    def raise_for_status(self): pass
    async def json(self): return {"message": {"content": self._t}}
    async def __aenter__(self): return self
    async def __aexit__(self, *e): return False


class _Sess:
    async def __aenter__(self): return self
    async def __aexit__(self, *e): return False

    def post(self, url, json=None, timeout=None):
        SEEN.append((url, (json or {}).get("format") == "json"))
        for key, q in SCRIPT.items():
            if key in url:
                item = q.pop(0)
                if isinstance(item, Exception):
                    raise item
                return _Resp(item)
        raise AssertionError("unscripted url " + url)


mc.aiohttp.ClientSession = lambda *a, **k: _Sess()
PROSE = "contemplation: a quiet thing\nwhat_spoke: nothing\nunresolved: all"
GOOD = '{"a": 1}'


def run(coro):
    return asyncio.run(coro)


def reset(**script):
    SEEN.clear(); SCRIPT.clear(); SCRIPT.update(script)


# 1. :11441 miss then retry with grammar
reset(**{":11441": [PROSE, GOOD]})
out = run(mc.call_node_json("http://LAN-HOST:11441", "s", "u"))
assert out == {"a": 1}, out
assert [g for _, g in SEEN] == [False, True], SEEN
print("OK 1: :11441 attempt1 no grammar, parse failure -> retry WITH grammar")

# 1b. clean first reply -> exactly one call, no grammar
reset(**{":11441": [GOOD]})
assert run(mc.call_node_json("http://LAN-HOST:11441", "s", "u")) == {"a": 1}
assert [g for _, g in SEEN] == [False], SEEN
print("OK 1b: clean first reply -> one call, no grammar")

# 1c. fenced reply parses without retry
reset(**{":11441": ["```json\n" + GOOD + "\n```"]})
assert run(mc.call_node_json("http://LAN-HOST:11441", "s", "u")) == {"a": 1}
assert len(SEEN) == 1
print("OK 1c: fenced reply handled by extract_json, no retry")

# 2. retries=0 keeps grammar
reset(**{":11441": [GOOD]})
run(mc.call_node_json("http://LAN-HOST:11441", "s", "u", retries=0))
assert [g for _, g in SEEN] == [True], SEEN
print("OK 2: retries=0 keeps the grammar (no fallback attempt exists)")

# 3. other lanes unchanged
for port in ("11433", "11437", "11438"):
    reset(**{":" + port: [GOOD]})
    run(mc.call_node_json("http://127.0.0.1:" + port, "s", "u"))
    assert [g for _, g in SEEN] == [True], (port, SEEN)
print("OK 3: :11433/:11437/:11438 first attempt still format=json")

# 4. bare call_node keeps grammar
reset(**{":11441": [GOOD]})
run(mc.call_node("http://LAN-HOST:11441", "s", "u", json_mode=True))
assert [g for _, g in SEEN] == [True], SEEN
reset(**{":11441": ["text"]})
run(mc.call_node("http://LAN-HOST:11441", "s", "u", json_mode=False))
assert [g for _, g in SEEN] == [False], SEEN
print("OK 4: bare call_node unchanged (json_mode=True -> grammar, json_mode=False -> none)")

# 6. transport failure on first attempt still fails over (no retry on same server, same as before)
import asyncio as _a  # noqa: E402
reset(**{":11441": [_a.TimeoutError()], ":11433": [GOOD]})
out = run(mc.call_node_json(["http://LAN-HOST:11441", "http://127.0.0.1:11433"], "s", "u"))
assert out == {"a": 1} and [g for _, g in SEEN] == [False, True], SEEN
print("OK 6: transport failure on :11441 fails over to the hot lane (grammar there, as before)")

# 5. telemetry
lat = [json.loads(l) for l in open(tel._LAT, encoding="utf-8")]
assert sum(1 for r in lat if "g" not in r) == 1, lat   # exactly the json_mode=False call has no g
assert any(r["node"] == "11441" and r["g"] == 0 for r in lat)
assert any(r["node"] == "11441" and r["g"] == 1 for r in lat)
assert all(r["g"] == 1 for r in lat if r["node"] in ("11433", "11437", "11438"))
jf = [json.loads(l) for l in open(tel._JSONFAIL, encoding="utf-8")]
assert len(jf) == 1 and jf[0]["node"] == "11441" and jf[0]["attempt"] == 0 and jf[0]["g"] == 0, jf
# a json_mode=False call must not carry g
tel.log_llm_latency("m", "http://x:11441", "c", 1.0, True, grammar=None)
last = json.loads(open(tel._LAT, encoding="utf-8").read().splitlines()[-1])
assert "g" not in last, last
# lab mode silences the new writer too
tel.enter_lab_mode()
n = len(open(tel._JSONFAIL, encoding="utf-8").read().splitlines())
tel.log_json_parse_fail("m", "n", "c", 0, 0)
assert len(open(tel._JSONFAIL, encoding="utf-8").read().splitlines()) == n
tel.exit_lab_mode()
print("OK 5: latency rows carry g; parse-fail row recorded (attempt 0, g 0); lab mode silences it")
print("ALL PASS; temp dir:", TMP)
