"""
Hermetic test for J-4222 (D-0822; P-0068): the nightly journal's felt line comes from the day's affect TRACE (mean
over the entry's own window, data/affect_log.jsonl) and is handed to the model as notes, so the closing sentence is
in his own words. No LLM, no live data: the affect log, journal dir and recap clock are temp paths; the model call
is a fake that captures the user prompt; store_fragment, the frontier note and the likes ledger are stubbed.

  [1] trace math: mean valence, strongest discrete feeling, early/late thirds; rows outside the window ignored
  [2] fewer than _TRACE_MIN_ROWS rows, a missing log, or a garbage log -> None (fail open)
  [3] notes wording: low / good / even tone, lighter / heavier / same arc, weak feelings left out
  [4] write_entry with a low-day trace and a GOOD instant at sleep: the prompt carries the trace ("mostly low"),
      not the instant ("a good day"), tells the model to use its own words, and holds no ready-made felt sentence
  [5] no trace rows in the window -> the pre-J-4222 instant line, byte for byte
  [6] JOURNAL_FELT_FROM_TRACE False -> the pre-J-4222 instant line even with a full trace
  [7] the tail read: a log larger than _TRACE_TAIL_BYTES still yields the window's rows

Run:  python scripts/_test_J-4222_journal_felt_trace.py   (from the tree under test)
"""
from __future__ import annotations
import asyncio, json, sys, tempfile, time, types
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # BEFORE anything else from the tree (F-2423)
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
from core import journal as J

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

TMP = Path(tempfile.mkdtemp(prefix="J4222_"))
J._JOURNAL_DIR = TMP / "Journal"
J._DAY_STATE_F = J._JOURNAL_DIR / ".day_recap_state.json"
J._AFFECT_LOG = TMP / "affect_log.jsonl"
J._frontier_note = lambda since: None
J._deeds_since = lambda since: ["Read 'Tyndall on glaciers'", "Walked to the shore", "Wrote a letter"]
import core.memory.store as _store
_store.store_fragment = lambda *a, **k: None      # never write a live fragment
assert "Nascence" not in str(J._AFFECT_LOG) or str(TMP) in str(J._AFFECT_LOG)

NOW = time.time()

def write_log(rows, path=None):
    p = path or J._AFFECT_LOG
    with open(p, "w", encoding="utf-8") as f:
        for ts, aff in rows:
            f.write(json.dumps({"ts": ts, "cycle_id": "x", "affect": aff}) + "\n")

def aff(valence, **dims):
    d = {k: 0.0 for k in J._TRACE_DISCRETE}
    d.update(dims)
    d["valence"] = valence
    d["arousal"] = 0.3
    return d

# [1] trace math
rows = [(NOW - 40 * 3600, aff(0.9, joy=0.9))]                     # outside the window
rows += [(NOW - 20 * 3600 + i * 600, aff(-0.6, fear=0.4)) for i in range(3)]   # early third
rows += [(NOW - 10 * 3600 + i * 600, aff(-0.4, fear=0.3)) for i in range(3)]
rows += [(NOW - 2 * 3600 + i * 600, aff(0.0, fear=0.2, joy=0.1)) for i in range(3)]  # late third
write_log(rows)
t = J._day_affect_trace(NOW - 24 * 3600, NOW)
check("[1] trace found, 9 rows in window (the 40 h-old row left out)", t and t["n"] == 9)
check("[1] mean valence = mean of the 9 rows", t and abs(t["valence_mean"] - (-1.0 / 3)) < 1e-9)
check("[1] strongest feeling fear", t and t["top"] == "fear" and abs(t["top_mean"] - 0.3) < 1e-9)
check("[1] early -0.6, late 0.0", t and abs(t["valence_early"] + 0.6) < 1e-9 and abs(t["valence_late"]) < 1e-9)

# [2] fail-open cases
write_log(rows[:3])
check("[2] 2 rows in window -> None", J._day_affect_trace(NOW - 24 * 3600, NOW) is None)
J._AFFECT_LOG.unlink()
check("[2] missing log -> None", J._day_affect_trace(NOW - 24 * 3600, NOW) is None)
J._AFFECT_LOG.write_text("not json\n{\"ts\": \"bad\"}\n\n", encoding="utf-8")
check("[2] garbage log -> None", J._day_affect_trace(NOW - 24 * 3600, NOW) is None)

# [3] notes wording
n = J._felt_notes({"valence_mean": -0.4, "top": "fear", "top_mean": 0.3, "valence_early": -0.6, "valence_late": 0.0})
check("[3] low + fear + lighter", n.startswith("mostly low") and "fear" in n and "lighter towards the end" in n)
n = J._felt_notes({"valence_mean": 0.5, "top": "joy", "top_mean": 0.05, "valence_early": 0.6, "valence_late": 0.3})
check("[3] good, weak feeling left out, heavier", n.startswith("mostly good") and "joy" not in n and "heavier" in n)
n = J._felt_notes({"valence_mean": 0.0, "top": "trust", "top_mean": 0.2, "valence_early": 0.0, "valence_late": 0.1})
check("[3] even + same arc", n.startswith("mostly even") and "about the same" in n)

# [4] write_entry uses the trace, not the instant
CALLS: list[str] = []
async def fake_model(base_urls, sys_prompt, user, **kw):
    CALLS.append(user)
    return {"entry": "I read and walked. The day sat heavy on me, though it eased a little by evening.", "liked": []}

GOOD_INSTANT = types.SimpleNamespace(affect=types.SimpleNamespace(valence=0.8))
def run(state=GOOD_INSTANT):
    CALLS.clear()
    if J._DAY_STATE_F.exists():
        J._DAY_STATE_F.unlink()
    return asyncio.run(J.write_entry(fake_model, ["http://stub"], state))

write_log([(NOW - 20 * 3600 + i * 3600, aff(-0.5, fear=0.3)) for i in range(15)])
p = run()
u = CALLS[0] if CALLS else ""
check("[4] entry written", p is not None and p.exists())
check("[4] prompt says mostly low (the trace)", "mostly low" in u)
check("[4] prompt does NOT carry the instant at sleep", "a good day" not in u)
check("[4] prompt asks for his own words and not to copy", "OWN words" in u and "Do not copy these notes" in u)
check("[4] no ready-made felt sentence left", "And how the day felt, underneath:" not in u)
check("[4] the instruction still follows", "Write tonight's entry now" in u)

# [5] no trace rows -> old line exactly
J._AFFECT_LOG.unlink()
run()
check("[5] fallback = pre-J-4222 instant line", "And how the day felt, underneath: a good day.\n\nWrite tonight's" in CALLS[0])

# [6] flag off
write_log([(NOW - 20 * 3600 + i * 3600, aff(-0.5, fear=0.3)) for i in range(15)])
J.JOURNAL_FELT_FROM_TRACE = False
run()
check("[6] flag off -> instant line, no notes", "And how the day felt, underneath: a good day." in CALLS[0]
      and "mostly low" not in CALLS[0])
J.JOURNAL_FELT_FROM_TRACE = True

# [7] tail read on a big log
big = TMP / "big_affect_log.jsonl"
pad = json.dumps({"ts": NOW - 300 * 3600, "affect": aff(0.9, joy=0.9), "raw_input": "x" * 300})
with open(big, "w", encoding="utf-8") as f:
    for _ in range(int(J._TRACE_TAIL_BYTES / len(pad)) + 2000):
        f.write(pad + "\n")
    for i in range(6):
        f.write(json.dumps({"ts": NOW - 5 * 3600 + i * 60, "affect": aff(-0.3, trust=0.4)}) + "\n")
J._AFFECT_LOG = big
t = J._day_affect_trace(NOW - 24 * 3600, NOW)
check("[7] big log (> tail bytes) still finds the 6 window rows", big.stat().st_size > J._TRACE_TAIL_BYTES
      and t and t["n"] == 6 and t["top"] == "trust")

print("ALL PASS" if ok_all else "SOME FAILED")
sys.exit(0 if ok_all else 1)
