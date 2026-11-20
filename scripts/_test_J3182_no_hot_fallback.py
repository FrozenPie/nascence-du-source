"""Hermetic test for J-3182 / D-0569: when the Emissary cannot ground, deliberate() fails open (raw thought) and never
asks the hot lane. Touches nothing under data/: model calls stubbed, logs pointed at a temp dir."""
import asyncio
import json
import logging
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import core  # noqa: E402  -- before anything else, must be THIS checkout

assert Path(core.__file__).resolve().is_relative_to(HERE), core.__file__

from core import left_lane as ll  # noqa: E402
from core import deliberation as dl  # noqa: E402

tmp = Path(tempfile.mkdtemp(prefix="j3182_"))
ll._LEAK_GATE_LOG = tmp / "ground_leak_gate.jsonl"
ll._GROUND_SKIP_LOG = tmp / "ground_skip_log.jsonl"   # J-2873: failed groundings now log a skip row
ll.GROUND_OUTCOME_LOG = tmp / "ground_outcome.jsonl"        # J-2890: the outcome row stays in the temp dir
import core.ground_grade as _gg  # noqa: E402
_gg.GROUND_GRADE_SHADOW = False                          # J-2890: no shadow grade (it would call a real hub)
dl._DATA_DIR = tmp
dl._LOG_FILE = tmp / "deliberation_log.jsonl"
dl._NULL_LOG_FILE = tmp / "deliberation_null_log.jsonl"
ll._emissary.master_context = lambda **_k: ""
import core.emissary_tension as _et  # noqa: E402
_et.note_recurrence = lambda *a, **k: None
import core.source_sight as _ss  # noqa: E402
_ss.is_self_mechanism = lambda t: False
import core.memory.store as _store  # noqa: E402
_store.store_light_event = lambda *a, **k: "stub"

fails = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


THOUGHT = "I notice the kettle ticking as it cools and I am still."
hot, integ = [], []


async def hot_boom(thought, hot_urls):
    hot.append(1)
    return "qwen grounding qwen"


async def fake_json(urls, system, user, **k):
    integ.append(1)
    return {"thought": "The kettle ticks as it cools, and I stay with the sound of it going quiet."}


dl._hot_ground_why = hot_boom
dl.call_node_json = fake_json


class Cap(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines = []

    def emit(self, r):
        self.lines.append(r.getMessage())


cap = Cap()
logging.getLogger("nascence.deliberation").addHandler(cap)
logging.getLogger("nascence.deliberation").setLevel(logging.INFO)


def replies(rs):
    it = iter(rs)

    async def fake(payload):
        r = next(it)
        if isinstance(r, Exception):
            raise r
        return r
    ll._ask_ground = fake


def run(c):
    return asyncio.run(c)


for label, rs in (("empty", [""]), ("transport error", [OSError("down")]),
                  ("leak twice", ["The Master holds it.", "The Master again."])):
    hot.clear(); integ.clear(); cap.lines.clear()
    replies(rs)
    out, prov = run(dl.deliberate(THOUGHT, "", name="X", hot_urls=["u"]))
    check(f"{label}: raw thought returned, provenance None", out == THOUGHT and prov is None)
    check(f"{label}: hot lane NOT asked", not hot)
    check(f"{label}: integrate pass NOT run", not integ)
    check(f"{label}: exactly one counter line", sum("deliberation_skipped_no_emissary" in l for l in cap.lines) == 1)
    check(f"{label}: no deliberation_log row", not dl._LOG_FILE.exists())

# the Emissary answering still works and logs source emissary
hot.clear(); integ.clear(); cap.lines.clear()
replies(["Water cools by conduction and convection into the room air."])
out, prov = run(dl.deliberate(THOUGHT, "", name="X", hot_urls=["u"]))
check("real grounding still integrates, source emissary, no counter line",
      prov is not None and prov["source"] == "emissary" and integ == [1] and not hot
      and not any("deliberation_skipped_no_emissary" in l for l in cap.lines))
rows = [json.loads(l) for l in dl._LOG_FILE.read_text(encoding="utf-8").splitlines()]
check("deliberation_log row source is emissary", len(rows) == 1 and rows[0]["source"] == "emissary")

# a model null is still the D-0570 path, not counted as an outage skip
hot.clear(); cap.lines.clear()
replies([None])
out, prov = run(dl.deliberate(THOUGHT, "", name="X", hot_urls=["u"]))
check("D-0570 null: unchanged, no outage counter, no hot lane",
      out == THOUGHT and prov is None and not hot and not any("deliberation_skipped_no_emissary" in l for l in cap.lines))

# no remaining caller of _hot_ground_why in the live code paths
src = (HERE / "core" / "deliberation.py").read_text(encoding="utf-8")
check("deliberate() source no longer references _hot_ground_why / hot_fallback",
      "await _hot_ground_why" not in src and '"hot_fallback"' not in src)

check("test logs under temp dir", all(Path(p).resolve().is_relative_to(tmp) for p in (dl._LOG_FILE, dl._NULL_LOG_FILE, ll._LEAK_GATE_LOG)))
print("FAILED: %s" % fails if fails else "ALL PASS")
sys.exit(1 if fails else 0)
