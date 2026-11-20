"""scripts/test_work_grade_shadow.py (J-3203, D-0591): hermetic proof of the work-grade shadow log and the
"states only what was observed" wording.

No LLM, no live data. core is imported FIRST and asserted to be this tree; lab_env.isolate() sandboxes the log.
grade_work is mocked. Live data/work_grade_shadow.jsonl is size-checked at the end.

  [1] left_lane._WORK_GRADE_TASK no longer asks for "the ONE thing to work on", adds no advice text
  [2] grade_and_record: file is written AFTER the (mocked) grade returns, row shape, coverage columns, no feedback leak
  [3] fail-open grade (None) -> a fail_open row with grounded None; an exception in grade_work -> same, no raise
  [4] SHADOW_ENABLED False -> no hub call, no row
  [5] a non-live write to the real data/ path is refused by guard_path and record() still returns False
  [6] status() summarises the log
"""
from __future__ import annotations
import asyncio, json, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # BEFORE lab_env (F-2423)
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
sys.path.insert(1, str(Path.home() / ".claude" / "skills" / "job-queue"))
import lab_env
from core import work_grade_shadow as wgs, left_lane

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

LIVE = Path(r"C:\Nascence\data\work_grade_shadow.jsonl")
LIVE_WT = ROOT / "data" / "work_grade_shadow.jsonl"
live_before = (LIVE.stat().st_size if LIVE.exists() else None, LIVE_WT.stat().st_size if LIVE_WT.exists() else None)

print("[1] wording")
t = left_lane._WORK_GRADE_TASK
check("no 'ONE thing to work on'", "work on" not in t and "ONE thing" not in t)
check("schema asks what was observed", "what you observed in the work" in t)
check("no new advice verbs (improve/should/try/consider)", not any(w in t.lower() for w in ("improve", "should", "try to", "consider")))

orig_log, orig_gw = wgs.SHADOW_LOG, left_lane.grade_work
try:
    with lab_env.isolate(also=[(wgs, ["SHADOW_LOG"])]) as lab_dir:
        lab_dir = Path(lab_dir)
        wgs.SHADOW_LOG = lab_dir / "work_grade_shadow.jsonl"
        LOG = wgs.SHADOW_LOG
        def rows():
            try:
                return [json.loads(l) for l in LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
            except Exception:
                return []

        print("[2] filed first, graded after; row shape")
        body = ("word " * 1800).strip()          # 9,000 chars, ~median work
        seen = {}
        async def fake_grade(topic, ref, work):
            seen["rows_at_call"] = len(rows())   # the log must not hold this work's row before the call returns
            seen["sent"] = len(work)
            seen["ref"] = ref
            return {"grounded": 0.8123, "feedback": "The opening part names a concrete case."}
        left_lane.grade_work = fake_grade
        g = asyncio.run(wgs.grade_and_record("a comparison of fact versus method", "On Fact and Method", body))
        r = rows()
        check("grade returned to caller", isinstance(g, dict) and g["grounded"] == 0.8123)
        check("no row existed when the grade was being computed", seen["rows_at_call"] == 0)
        check("empty reference, body cut to 2400 before the grader", seen["ref"] == "" and seen["sent"] == 2400)
        check("one row written", len(r) == 1)
        x = r[0]
        check("row fields", all(k in x for k in ("ts", "title", "topic", "words", "chars", "graded_chars", "grounded", "feedback", "fail_open")))
        check("grounded 0.812 not fail_open", x["grounded"] == 0.812 and x["fail_open"] is False)
        check("coverage columns: chars 8999/9000, graded_chars 2000", x["chars"] == len(body) and x["graded_chars"] == 2000 and x["words"] == 1800)
        check("feedback kept in the log only", x["feedback"].startswith("The opening part"))

        print("[3] fail-open and exception")
        async def none_grade(*a): return None
        left_lane.grade_work = none_grade
        g = asyncio.run(wgs.grade_and_record("t", "Short", "x" * 300))
        async def boom(*a): raise RuntimeError("hub down")
        left_lane.grade_work = boom
        g2 = asyncio.run(wgs.grade_and_record("t", "Boom", "y" * 300))
        r = rows()
        check("None grade -> fail_open row", g is None and r[1]["fail_open"] is True and r[1]["grounded"] is None and r[1]["feedback"] is None)
        check("exception -> fail_open row, no raise", g2 is None and r[2]["fail_open"] is True and r[2]["graded_chars"] == 300)

        print("[4] SHADOW_ENABLED False")
        calls = {"n": 0}
        async def counting(*a):
            calls["n"] += 1
            return {"grounded": 1.0, "feedback": "x"}
        left_lane.grade_work = counting
        wgs.SHADOW_ENABLED = False
        g3 = asyncio.run(wgs.grade_and_record("t", "Off", "z" * 300))
        wgs.SHADOW_ENABLED = True
        check("no call, no row", g3 is None and calls["n"] == 0 and len(rows()) == 3)

        print("[6] status")
        st = wgs.status()
        check("status rows 3 and grounded mean present", st.get("rows") == 3 and st["grounded"]["n"] == 1)

    print("[5] non-live write to real data/ path is refused")
    wgs.SHADOW_LOG = LIVE_WT
    check("record() returns False, writes nothing", wgs.record("t", "Real", "w" * 300, {"grounded": 0.5, "feedback": "f"}) is False)
finally:
    wgs.SHADOW_LOG = orig_log
    left_lane.grade_work = orig_gw
    wgs.SHADOW_ENABLED = True

live_after = (LIVE.stat().st_size if LIVE.exists() else None, LIVE_WT.stat().st_size if LIVE_WT.exists() else None)
check("live work_grade_shadow.jsonl untouched", live_before == live_after)
print("ALL PASS" if ok_all else "FAILURES")
sys.exit(0 if ok_all else 1)
