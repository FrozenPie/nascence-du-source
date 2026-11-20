"""Hermetic test for J-2873: left_lane records WHY a grounding failed (transport / timeout / empty_or_unparseable /
leak_dropped) in a skip log, the log has a reader, and nothing about the return values changed.
Model calls stubbed; every log path pointed at a temp dir; touches nothing under data/."""
import asyncio
import importlib.util
import json
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import core  # noqa: E402  -- before anything else, must be THIS checkout

assert Path(core.__file__).resolve().is_relative_to(HERE), core.__file__

import aiohttp  # noqa: E402
from core import left_lane as ll  # noqa: E402

tmp = Path(tempfile.mkdtemp(prefix="j2873_"))
SKIP = tmp / "ground_skip_log.jsonl"
ll._GROUND_SKIP_LOG = SKIP
ll._LEAK_GATE_LOG = tmp / "ground_leak_gate.jsonl"
ll.GROUND_OUTCOME_LOG = tmp / "ground_outcome.jsonl"   # J-2890 (merged after this test): keep the outcome row in the temp dir
import core.ground_grade as _gg  # noqa: E402
_gg.GROUND_GRADE_SHADOW = False                          # no shadow grade (it would call a real hub)
ll._emissary.master_context = lambda **_k: ""
import core.emissary_tension as _et  # noqa: E402
_et.note_recurrence = lambda *a, **k: None
import core.source_sight as _ss  # noqa: E402
_ss.is_self_mechanism = lambda t: False

fails = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


def run(c):
    return asyncio.run(c)


def rows():
    try:
        return [json.loads(l) for l in SKIP.read_text(encoding="utf-8").splitlines()]
    except FileNotFoundError:
        return []


def set_ask(seq):
    it = iter(seq)

    async def fake(payload):
        v = next(it)
        if isinstance(v, BaseException):
            raise v
        return v
    ll._ask_ground = fake


T = "I notice the kettle ticking as it cools and I am still."

# 1. classification
check("classify timeout", ll._classify_ground_failure(asyncio.TimeoutError()) == "timeout")
check("classify builtin TimeoutError is timeout, not transport", ll._classify_ground_failure(TimeoutError()) == "timeout")
check("classify connector error", ll._classify_ground_failure(aiohttp.ClientConnectionError()) == "transport")
check("classify OSError", ll._classify_ground_failure(ConnectionRefusedError()) == "transport")
check("classify bad JSON", ll._classify_ground_failure(json.JSONDecodeError("x", "y", 0)) == "empty_or_unparseable")
check("classify other", ll._classify_ground_failure(ValueError("x")) == "other")

# 2. each failure path writes one row and still returns (None, False)
for label, seq, want in [
    ("transport", [aiohttp.ClientConnectionError("down")], "transport"),
    ("timeout", [asyncio.TimeoutError()], "timeout"),
    ("empty", [""], "empty_or_unparseable"),
    ("unparseable", [json.JSONDecodeError("Expecting value", "", 0)], "empty_or_unparseable"),
    ("leak twice", ["The Master sees a kettle.", "The Master hears it."], "leak_dropped"),
]:
    before = len(rows())
    set_ask(seq)
    out = run(ll.ground_thought_verdict(T))
    r = rows()
    check(f"{label}: returns (None, False)", out == (None, False))
    check(f"{label}: exactly one new row", len(r) == before + 1)
    check(f"{label}: reason {want}", r[-1]["reason"] == want and "ts" in r[-1])
check("transport row carries the exception class", rows()[0]["exc"] == "ClientConnectionError")

# 3. success, null and leak-then-clean write NOTHING
before = len(rows())
set_ask(["A kettle's steel contracts as it cools, so it ticks."])
check("success: returns grounding", run(ll.ground_thought_verdict(T)) == ("A kettle's steel contracts as it cools, so it ticks.", False))
set_ask([None])
check("null: (None, True)", run(ll.ground_thought_verdict(T)) == (None, True))
set_ask(["The Master sees it.", "Steel contracts as it cools."])
check("leak then clean: returns the clean grounding", run(ll.ground_thought_verdict(T)) == ("Steel contracts as it cools.", False))
check("success / null / retry-then-clean wrote no skip row", len(rows()) == before)

# 4. log failure never raises
ll._GROUND_SKIP_LOG = tmp  # a directory: open() fails
try:
    ll._log_ground_skip("transport")
    check("unwritable log does not raise", True)
except Exception:
    check("unwritable log does not raise", False)
ll._GROUND_SKIP_LOG = SKIP

# 5. reader
s = ll.ground_skip_summary(SKIP)
check("summary counts rows", s["rows"] == 5)
check("summary by_reason", s["by_reason"] == {"transport": 1, "timeout": 1, "empty_or_unparseable": 2, "leak_dropped": 1})
check("summary since_ts filters", ll.ground_skip_summary(SKIP, since_ts=time.time() + 100)["rows"] == 0)
check("summary of a missing file is empty", ll.ground_skip_summary(tmp / "nope.jsonl")["rows"] == 0)

spec = importlib.util.spec_from_file_location("gsr", HERE / "scripts" / "ground_skip_report.py")
gsr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gsr)
(tmp / "deliberation_log.jsonl").write_text(json.dumps({"ts": time.time()}) + "\n", encoding="utf-8")
txt = gsr.report(tmp, days=1)
check("report prints a day line and the skip total", "5 rows" in txt and time.strftime("%Y-%m-%d") in txt)

# 6. the live log was not touched by this test
check("live data/ground_skip_log.jsonl not created", not (HERE / "data" / "ground_skip_log.jsonl").exists())

print(("\nFAILED: %s" % fails) if fails else "\nALL PASS")
sys.exit(1 if fails else 0)
