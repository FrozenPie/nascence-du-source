"""
Test suite -- J-3076 / F-3785: the T4 SOLIDIFY (lived-integration) judge.
  (1) _INTEGRATION_TASK says confidence is confidence in the verdict given (one sentence; the rest of the task unchanged)
      and judge_lived_integration stores each leg's confidence and the agreed verdict instead of a meaningless min().
  (2) the lived-thought block shows whole thoughts only, all 15 of a full window (was lt[:2600]: 11 of 15, cut mid-thought).
  (3) the solidify rule (both legs true AND confidence >= INTEG_CONF_MIN = 0.6) is intact in provisional_identity.evaluate.
  (4) no stale model names in the live-seat comments/docstrings.
Hermetic: model calls are stubbed (fake aiohttp session / patched legs), no hub is contacted, nothing is written outside a
temp dir, and this checkout's data/ is not touched.

Run: python scripts/_test_J3076_integration_judge.py      (exit 0 = every check passed)
"""
from __future__ import annotations
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/

import asyncio
import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import aiohttp  # noqa: E402
import core as _core_pkg  # noqa: E402
assert str(Path(_core_pkg.__file__).resolve()).lower().startswith(str(ROOT).lower()), _core_pkg.__file__
from core import left_lane as ll  # noqa: E402
from core import provisional_identity as pi  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + ((" -- " + str(detail)) if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


# ---- (2) thought window -------------------------------------------------------------------------------------------
full = [("thought %02d " % i) + ("x" * (240 - 11)) for i in range(15)]      # 15 x 240 chars, as the caller builds them
assert all(len(t) == 240 for t in full)
block = ll._format_lived_thoughts(full)
check("full 15-thought window is shown whole", block.count("\n- ") == 14 and block.startswith("- thought 00 ")
      and all(t in block for t in full), block.count("\n"))
check("old behaviour would have lost thoughts (3,4xx chars > 2600)", len("\n".join("- " + t for t in full)) > 2600)
check("no thought is cut mid-way", all(line == "- " + t for line, t in zip(block.split("\n"), full)))

orig_budget = ll._INTEG_THOUGHT_BUDGET
ll._INTEG_THOUGHT_BUDGET = 1000
small = ll._format_lived_thoughts(full)
lines = small.split("\n")
check("a tight budget keeps the NEWEST whole thoughts and drops the oldest", 1 <= len(lines) < 15
      and all(l == "- " + t for l, t in zip(lines, full)) and len(small) <= 1000, len(lines))
ll._INTEG_THOUGHT_BUDGET = orig_budget
check("over-long single thought is capped, empties skipped", ll._format_lived_thoughts(["", "y" * 500]) == "- " + "y" * 240)
check("empty window message kept", ll._format_lived_thoughts([]) == "(no lived self-thoughts found)")
check("more than 15 supplied -> only 15 shown", ll._format_lived_thoughts(["z"] * 20).count("\n") == 14)

# ---- (1a) prompt sentence reaches the wire; task otherwise unchanged -------------------------------------------------
captured = {}


class _Resp:
    def __init__(self, content): self._c = content
    def raise_for_status(self): pass
    async def json(self): return {"message": {"content": self._c}}
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False


class _Sess:
    def __init__(self, *a, **k): pass
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False
    def post(self, url, json=None, timeout=None):
        captured["url"], captured["payload"] = url, json
        return _Resp('{"integrated": false, "confidence": 0.9, "reason": "r"}')


orig_session, orig_note = aiohttp.ClientSession, ll._note_call
aiohttp.ClientSession = _Sess
ll._note_call = lambda *a, **k: None
try:
    res = asyncio.run(ll._ask_integration_judge(ll._JUDGE_2_URL, "held", "excl", full))
finally:
    aiohttp.ClientSession, ll._note_call = orig_session, orig_note
sysmsg = captured["payload"]["messages"][0]["content"]
usr = captured["payload"]["messages"][1]["content"]
check("system prompt carries the confidence-in-the-verdict-you-gave sentence",
      "how sure you are of the verdict you gave, whether true or false" in sysmsg)
check("user message carries all 15 thoughts whole", all(t in usr for t in full))
# J-4052: the leg result later gained raw_integrated / raw_confidence / lane / model (provenance); the three verdict
# fields are what this pins and they must still pass through unchanged.
check("leg result passes through", {k: res.get(k) for k in ("integrated", "confidence", "reason")} == {"integrated": False, "confidence": 0.9, "reason": "r"}, res)
task = ll._INTEGRATION_TASK
check("0.6 floor and the substantive task wording untouched",
      "GENUINE metaphorical integration (COUNT this as integrated)" in task
      and "EVASIVE metaphor (do NOT count this)" in task and "does the metaphor engage the CONTENT of being built" in task
      and pi.INTEG_CONF_MIN == 0.6)

# ---- (1b) judge_lived_integration stores legs + agreed verdict --------------------------------------------------------


def run_legs(v1, v2):
    seq = iter([v1, v2])

    async def fake(url, held, excl, lt):
        return next(seq)
    o = ll._ask_integration_judge
    ll._ask_integration_judge = fake
    try:
        return asyncio.run(ll.judge_lived_integration("h", "e", ["t"]))
    finally:
        ll._ask_integration_judge = o


def leg(i, c): return {"integrated": i, "confidence": c, "reason": "r%s" % i}


r = run_legs(leg(True, 0.8), leg(True, 0.9))
check("double true: integrated, confidence = min of the two own-verdict confidences",
      r["integrated"] is True and r["confidence"] == 0.8 and r["agreed_verdict"] == "integrated"
      and r["conf_j1"] == 0.8 and r["conf_j2"] == 0.9, r)
r = run_legs(leg(False, 0.95), leg(False, 0.9))
check("double false (new semantics): confidence is real (0.9), not 0.0",
      r["integrated"] is False and r["confidence"] == 0.9 and r["agreed_verdict"] == "not_integrated", r)
r = run_legs(leg(False, 0.9), leg(True, 0.85))
check("split: not integrated, no agreed verdict, both legs kept",
      r["integrated"] is False and r["agreed_verdict"] == "split" and r["confidence"] == 0.0
      and r["conf_j1"] == 0.9 and r["conf_j2"] == 0.85 and r["judge1"]["integrated"] is False and r["judge2"]["integrated"] is True, r)
r = run_legs(None, leg(True, 0.9))
check("one leg down: not integrated (fail as before), single_leg, down leg's conf None",
      r["integrated"] is False and r["agreed_verdict"] == "single_leg" and r["conf_j1"] is None and r["conf_j2"] == 0.9, r)
check("both legs down -> None (fail-open, as before)", run_legs(None, None) is None)

# ---- (3) the solidify rule, via provisional_identity.evaluate with its writers stubbed --------------------------------
tmp = Path(tempfile.mkdtemp(prefix="J3076_"))
calls = []
saved = {n: getattr(pi, n) for n in ("current", "_solidify", "_revert", "_atomic_write_prov", "_log", "delta_free_energy",
                                     "evidence_ready", "_LOG")}
now = time.time()
rec = {"theme": "t", "expires_ts": now - 5, "extends": 0, "started_ts": now - 100}
pi.current = lambda: dict(rec)
pi.delta_free_energy = lambda r, n: {"dF": 0}
pi.evidence_ready = lambda n=None: True
pi._solidify = lambda r, df, integ=None: calls.append("solidify") or True
pi._revert = lambda r, df, integ=None, fatigue=True: calls.append("revert" if fatigue else "revert_nofatigue")
pi._atomic_write_prov = lambda r: calls.append("write")
pi._log = lambda r: None
pi._LOG = tmp / "provisional_identity.jsonl"
try:
    def ev(integrated, conf):
        calls.clear()
        return pi.evaluate(integration={"integrated": integrated, "confidence": conf}, now=now)["decision"]
    check("integrated + 0.6 solidifies", ev(True, 0.6) == "solidify")
    check("integrated + 0.59 does not solidify (extends)", ev(True, 0.59) == "extend")
    check("not integrated reverts with fatigue regardless of confidence", ev(False, 0.95) == "revert" and calls[-1] == "revert")
finally:
    for n, v in saved.items():
        setattr(pi, n, v)

# ---- (4) stale names ---------------------------------------------------------------------------------------------------
src = (ROOT / "core" / "left_lane.py").read_text(encoding="utf-8")
doc = ll.judge_lived_integration.__doc__
check("judge_lived_integration docstring names the live seats", "gemma4:12b" in doc and "falcon3:7b" in doc
      and "TWO independent judges (llama3.1" not in doc)
check("_JUDGE_2 comment names falcon3:7b", '_JUDGE_2_URL = "http://127.0.0.1:11440"' in src
      and "# qwen2.5:7b" not in src.split("_JUDGE_2_URL =")[1].split("\n")[0])
check("lt[:2600] is gone", "lt[:2600]" not in src)

print("\n%d failed" % len(FAILS) if FAILS else "\nALL PASSED")
sys.exit(1 if FAILS else 0)
