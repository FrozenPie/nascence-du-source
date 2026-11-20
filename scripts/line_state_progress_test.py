"""Hermetic test for J-4084 (D-0779 b): question progress from the Follow Line state. Pure functions + a temp frontier file."""
import sys, json, tempfile
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core
assert Path(core.__file__).resolve().is_relative_to(ROOT)
from core import curiosity_progress as cp, goals, idle_allocator as ia
ok = True
def check(n, c):
    global ok; ok = ok and bool(c); print(f"  [{'PASS' if c else 'FAIL'}] {n}")
qs = [
 {"id": "a", "q": "open untouched", "status": "open"},
 {"id": "b", "q": "partly", "status": "open", "line": {"state": "settled_partly"}},
 {"id": "c", "q": "lookup echo only", "status": "open", "finding": {"title": "the Wikipedia page \"x\" (you looked it up)"}, "new_fragments": 3},
 {"id": "d", "q": "no verdict", "status": "open", "line": {"state": "settled_no"}},
 {"id": "e", "q": "old stalled", "status": "open", "consecutive_stalls": 5},
]
with tempfile.TemporaryDirectory() as t:
    f = Path(t) / "frontier.json"; f.write_text(json.dumps({"questions": qs}), encoding="utf-8")
    cp._FRONTIER = f
    cp.LINE_STATE_PROGRESS = True
    r = {x["q"]: x for x in cp.rank()}
    check("untouched open question = 0", r["open untouched"]["lp"] == 0 and not r["open untouched"]["parked"])
    check("settled partly = progress (1.0)", r["partly"]["lp"] == 1.0)
    check("settled no = 1.0 (an answer)", r["no verdict"]["lp"] == 1.0)
    check("lookup finding + new_fragments adds NOTHING until he settles", r["lookup echo only"]["lp"] == 0 and r["lookup echo only"]["finding"] is False)
    check("stall counter no longer parks", r["old stalled"]["parked"] is False)
    cp.LINE_STATE_PROGRESS = False
    r = {x["q"]: x for x in cp.rank()}
    check("flag off = pre-J-4084 readers exactly (finding+fragments=4.0; stalled parked)", r["lookup echo only"]["lp"] == 4.0 and r["old stalled"]["parked"] is True and r["partly"]["lp"] == 0)
    cp.LINE_STATE_PROGRESS = True
    # goals register
    goals._load_frontier = lambda ids: {q["id"]: q for q in qs if q["id"] in ids}
    out = goals._question_progress({"a", "b", "c", "d"})
    check("goals: untouched lp None; partly 1.0; echo-only None", out["a"]["lp"] is None and out["b"]["lp"] == 1.0 and out["c"]["lp"] is None and out["c"]["has_finding"] is False)
    check("goals: mech shadow still attached", "mech" in out["b"])
    goals.LINE_STATE_PROGRESS = False
    out = goals._question_progress({"c"})
    check("goals flag off: old pursuit read (lp 4.0)", out["c"]["lp"] == 4.0)
print("\nALL PASS" if ok else "\nFAILURES"); sys.exit(0 if ok else 1)
