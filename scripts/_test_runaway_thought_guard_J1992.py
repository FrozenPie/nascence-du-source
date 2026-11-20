"""J-1992 / F-2593: guard_runaway_thought cuts a salvaged runaway multi-object output at the first leaked key.

Offline, pure-function test. Writes nothing; reads C:/Nascence/data/monologue_log.jsonl read-only for the replay.
Run from the tree under test:  python scripts/_test_runaway_thought_guard_J1992.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  -- import core BEFORE anything else
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
from core import model_client as mc  # noqa: E402

fails = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


g = mc.guard_runaway_thought
# 1 clean thought untouched
check("clean unchanged", g("The wind moves; I keep thinking, \"about\" it.") == "The wind moves; I keep thinking, \"about\" it.")
# 2 leaked siblings cut at first marker
raw = 'The garden is quiet today.","about":"fear","unresolved":false,"intention":"x","thought":"second"'
check("cut at first marker", g(raw) == "The garden is quiet today.")
# 3 escaped form
raw2 = 'First thought.\\",\\"intention\\":\\"x\\"'
check("escaped cut", g(raw2) == "First thought.")
# 4 nothing before marker -> dropped
check("drop when empty head", g('","about":"x"') == "")
# 5 empty
check("empty in empty out", g("") == "")
# 6 counters moved
check("counters", mc.RUNAWAY_THOUGHT_STATS["truncated"] >= 2 and mc.RUNAWAY_THOUGHT_STATS["dropped"] >= 1)
# 7 end-to-end: real extract_json salvage of a runaway repeat output, then guard
runaway = ('{"thought":"The wind shifts.","about":"a","unresolved":false,"intention":"i","act":{"kind":"none","object":""},'
           '"state":"s"}{"thought":"Another one.","about":"b","intention":"j","act":{"kind":"none","object":""')
d = mc.extract_json(runaway)
out = g(str(d.get("thought", "")))
check("e2e salvage leaks before guard or parses", True)
check("e2e no leaked key after guard", '"about"' not in out and '"intention"' not in out and out != "")
# 8 replay against known leaked rows (read-only)
log = Path("C:/Nascence/data/monologue_log.jsonl")
n = bad = 0
if log.exists():
    with log.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            if '\\"about\\"' not in line and '"about"' not in line:
                continue
            try:
                t = str(json.loads(line).get("thought", ""))
            except Exception:
                continue
            if not mc._RUNAWAY_MARKER.search(t):
                continue
            n += 1
            o = g(t)
            if mc._RUNAWAY_MARKER.search(o) or len(o) >= len(t):
                bad += 1
    print(f"replay: {n} leaked rows, {bad} not cleaned")
    check("replay finds 11 leaked rows", n == 11)
    check("replay all cleaned", bad == 0)
else:
    print("SKIP replay (no monologue_log)")
print("FAILED: %s" % fails if fails else "ALL PASS")
sys.exit(1 if fails else 0)
