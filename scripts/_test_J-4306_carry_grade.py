"""J-4306 (F-5079): a practical announced on day N, period closed while Du was shut down across midnight,
is graded once on the first tick of day N+1 (CARRY_GRADE_ACROSS_DAYS). Temp-store, zero LLM."""
from __future__ import annotations
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()
import json, sys, time, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import practical_lesson as pl  # noqa: E402

fails = []
def check(n, c, x=""):
    print(("PASS " if c else "FAIL ") + n, x if not c else "")
    if not c: fails.append(n)

tmp = Path(tempfile.mkdtemp())
pl._STATE = tmp / "state.json"; pl._LOG = tmp / "log.jsonl"; pl._FC_LEDGER = tmp / "fc.jsonl"
task = next(t for t in pl._BY_ID.values() if t.get("craft") or t.get("deed_keys"))
tid = task["id"]
lt = time.localtime(); ann = time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, 10, 40, 0, 0, 0, -1)) - 86400
end = pl._period_end(ann)
craft = task.get("craft")
dkeys = sorted(task.get("deed_keys") or ())
row = {"ts": ann + 300, "ok": True}
if dkeys: row["deed"] = dkeys[0]
else: row["craft"] = craft
pl._FC_LEDGER.write_text(json.dumps(row) + "\n", encoding="utf-8")
yday = pl._today_key(ann)
def seed():
    pl._LOG.write_text("", encoding="utf-8")
    pl._save_state({"day": yday, "slot_fired": 1, "task_id": tid, "announced_ts": ann, "graded_day": None, "rung": 1})

# flag OFF: old behaviour, day lost
pl.CARRY_GRADE_ACROSS_DAYS = False; seed()
check("OFF: next-day tick grades nothing", pl.period_end_grade() == {})
check("OFF: no carry stashed", "carry" not in pl._load_state())
check("OFF: no graded row", pl._LOG.read_text(encoding="utf-8") == "")

# flag ON
pl.CARRY_GRADE_ACROSS_DAYS = True; seed()
res = pl.period_end_grade()
check("ON: next-day tick grades the carried practical", res.get("attempted") is True and res.get("ok") is True, res)
rows = [json.loads(l) for l in pl._LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
check("ON: one row, trigger carry_over, prior day", len(rows) == 1 and rows[0]["trigger"] == "carry_over" and rows[0]["day"] == yday, rows)
check("ON: carry cleared, never graded twice", "carry" not in pl._load_state() and pl.period_end_grade() == {})
# ungraded already (graded_day == day) must not carry
pl._save_state({"day": yday, "slot_fired": 1, "task_id": tid, "announced_ts": ann, "graded_day": yday, "rung": 1})
check("ON: already-graded day not carried", pl.period_end_grade() == {} and "carry" not in pl._load_state())
# period not yet closed -> carry kept
seed(); st = pl._load_state(); pl._roll_day(st, pl._today_key())
check("ON: carry persisted by roll", pl._load_state().get("carry", {}).get("task_id") == tid)
print("\nFAILED:" if fails else "\nALL PASS", fails or "")
sys.exit(1 if fails else 0)
