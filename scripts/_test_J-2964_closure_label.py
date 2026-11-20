"""J-2964 / F-3657 / P-0062: the closure composer's LLM calls carry a station label in data/llm_latency.jsonl.
Offline: aiohttp is faked, every telemetry writer is captured in memory, SHADOW_LOG is a temp file, nothing under
the repo's data/ is touched, no hub is called.

Covers:
  1. dream / line / pursuit arm composer calls reach telemetry.log_llm_latency with by == closure:compose_<arm>
     (before: the event loop's frame, asyncio.events:94(Handle)); log_llm_call and log_thought_station carry the
     same label; the parsed text still flows through (compose_how ok).
  2. A call made WITHOUT the label keeps the frame label (the default is unchanged) and the label does not leak
     out of the wrapped call (reset on exit, also on a raise).
  3. `_compose_fn` (the test seam) and a 2-argument replacement of `_compose_sync` still work (signatures kept).
  4. The module docstring no longer claims SHADOW / CLOSURE_WRITE_LIVE is False.
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core                                              # noqa: E402  (core BEFORE lab_env)
assert TREE in Path(core.__file__).resolve().parents, core.__file__
from core import closure as cl                           # noqa: E402
from core import model_client as mc                      # noqa: E402
from core import telemetry as tel                        # noqa: E402

FAILS = []


def check(name, ok):
    print(("PASS " if ok else "FAIL ") + name)
    if not ok:
        FAILS.append(name)


class _Resp:
    status = 200

    def raise_for_status(self):
        pass

    async def json(self):
        return {"message": {"content": '{"resolution": "I hold that the grounds were what I had, and I say so plainly. The old records I found agreed with each other, and my first thought matched them. Nothing came back that cut against it, so I keep it as it stands, though thinly, and I would look again if something new turned up."}'}}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


class _Session:
    def __init__(self, *a, **k):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    def post(self, *a, **k):
        return _Resp()


lat, calls, stations = [], [], []
mc.aiohttp.ClientSession = _Session
tel.log_llm_latency = lambda model, node, caller, secs, ok, **kw: lat.append((node, caller, ok))
tel.log_llm_call = lambda *a, **kw: calls.append(kw.get("caller"))
tel.log_thought_station = lambda model, url, caller, **kw: stations.append(caller)   # J-4052: model_client now passes fn=
import core.speech_timing_shadow as _sts                 # noqa: E402
_sts.log_call = lambda *a, **k: None

tmp = Path(tempfile.mkdtemp(prefix="j2964_"))
cl.SHADOW_LOG = tmp / "closure_shadow.jsonl"
cl._write_live = lambda wb: "fid-test"
assert cl._compose_fn is None

print("[1] each arm's composer call is labelled")
r = cl.compose_dream_resolution({"id": "arc1", "core": "x", "last": "y", "title": "t"})
check("dream: compose ok through the real _compose_sync", r.get("how") == "ok" and r.get("text"))
check("dream: latency by == closure:compose_dream", [c for _, c, _ in lat] == ["closure:compose_dream"])
check("dream: llm_calls + thought_station carry it too", calls == ["closure:compose_dream"] and stations == ["closure:compose_dream"])

lat.clear()
ent = {"id": "e_1", "q": "did the goldfinches change the soil?", "about_key": "k1"}
r1 = cl.record_line_settled(ent, {"grounds": [{"origin": "a book", "text": "g1"}], "status": "held"}, "yes, settled")
check("line: composed + written", r1["compose_how"] == "ok" and r1["written_live"])
check("line: latency by == closure:compose_line", [c for _, c, _ in lat] == ["closure:compose_line"])

lat.clear()
cl._record_arm("pursuit", "pursuit", "p_1", "panel", "met", "d", "sys", "user")
check("pursuit: latency by == closure:compose_pursuit", [c for _, c, _ in lat] == ["closure:compose_pursuit"])

print("[2] default unchanged, no leak")
lat.clear()
asyncio.run(mc.call_node_json("http://127.0.0.1:11433", "s", "u"))
check("unlabelled call keeps its frame label (not closure:*)", len(lat) == 1 and not lat[0][1].startswith("closure:"))
check("label var is back to None outside the call", mc._CALL_LABEL.get() is None)


async def _boom():
    raise RuntimeError("x")

try:
    asyncio.run(mc.with_call_label("closure:compose_test", _boom()))
except RuntimeError:
    pass
check("label reset after a raise", mc._CALL_LABEL.get() is None)
async def _lab():
    return mc._caller_label()


check("label is cut to the 60-char `by` width", asyncio.run(mc.with_call_label("z" * 90, _lab())) == "z" * 60)

GOOD_TEXT = "I hold that the grounds were what I had, and I say so plainly. The old records I found agreed with each other, and my first thought matched them. Nothing came back that cut against it, so I keep it as it stands, though thinly, and I would look again if something new turned up."   # J-2963: composer output is validated now (40-90 words, first person)
print("[3] seams keep their signatures")
cl._compose_fn = lambda s, u: {"resolution": GOOD_TEXT + " fn path."}
check("_compose_fn seam", cl.compose_dream_resolution({"id": "a2", "core": "x", "last": "y", "title": "t"})["text"] == GOOD_TEXT + " fn path.")
cl._compose_fn = None
orig = cl._compose_sync
cl._compose_sync = lambda system, user: {"resolution": GOOD_TEXT + " two-arg replacement."}
check("2-arg _compose_sync replacement (the J-2910 test's shape)",
      cl.compose_dream_resolution({"id": "a3", "core": "x", "last": "y", "title": "t"})["text"] == GOOD_TEXT + " two-arg replacement.")
cl._compose_sync = orig

print("[4] docstring")
doc = cl.__doc__
check("docstring no longer says SHADOW / RESTART-GATED headline or CLOSURE_WRITE_LIVE is False",
      "SHADOW / RESTART-GATED" not in doc and "CLOSURE_WRITE_LIVE is False. Every" not in doc
      and cl.CLOSURE_WRITE_LIVE is True and cl.CLOSURE_ARMS == {"line", "lookup"} and "CLOSURE_ARMS = {\"line\"}" in doc)

print("\n" + ("ALL PASS" if not FAILS else f"{len(FAILS)} FAILED: {FAILS}"))
sys.exit(1 if FAILS else 0)
