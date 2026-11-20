"""
_test_nature_period_kind.py -- J-3251 (D-0640): the nature period's two kinds of lesson are logged as such,
and scripts/nature_period_read.py reads them.

Covers: nature_study.run() writes kind='observation' + the room ('where') on its log row, nothing about the
scene text is changed; practical_lesson's issued row and graded row carry kind='practical'; the reader counts
window-view lessons from the 'where' field when present and from F-3651's wording when not; both D-0640
defeater lines flip correctly on synthetic data. Fully isolated (lab_env.isolate, db='empty'); never touches
C:\\Nascence\\data. Run: python -X utf8 scripts/_test_nature_period_kind.py   Exit 1 on any failure.
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path
from unittest import mock

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path.home() / ".claude" / "skills" / "job-queue"))

import core  # noqa: E402  -- BEFORE lab_env, so the worktree's core wins
from lab_env import isolate  # noqa: E402
from core import nature_study, practical_lesson, sensorium  # noqa: E402
sys.path.insert(0, str(ROOT / "scripts"))
import nature_period_read as npr  # noqa: E402

FAIL: list[str] = []


def check(name: str, cond: bool, detail="") -> None:
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" -- {detail}" if detail and not cond else ""))
    if not cond:
        FAIL.append(name)


def _last(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8").strip().splitlines()[-1])


with isolate(also=[
    (nature_study, ["_STATE", "_LOG"]),
    (practical_lesson, ["_STATE", "_LOG", "_FC_LEDGER"]),
], db="empty") as lab_dir:
    print(f"isolated lab dir: {lab_dir}\n")
    check("nature log is redirected into the lab dir", str(nature_study._LOG).startswith(str(lab_dir)))
    check("practical log is redirected into the lab dir", str(practical_lesson._LOG).startswith(str(lab_dir)))

    # ── observation row ──
    async def _fake_call_json(urls, system, user, **kw):
        return {"observation": "A grey gull stands on the fence post, one foot drawn up, wind lifting its wing.",
                "inference": "the wind is from the sea"}

    async def _fake_grade(task, scene, work):
        return {"grounded": 0.9, "feedback": "specific"}

    seen_user = {}

    async def _spy_call_json(urls, system, user, **kw):
        seen_user["user"] = user
        return await _fake_call_json(urls, system, user, **kw)

    for where in ("study", "garden"):
        with mock.patch.object(nature_study, "_scene", return_value="SCENE-TEXT"), \
             mock.patch.object(sensorium, "where", return_value=where), \
             mock.patch("core.left_lane.grade_work", _fake_grade), \
             mock.patch("core.memory.store.store_fragment", lambda **k: None):
            res = asyncio.run(nature_study.run(_spy_call_json, []))
        row = _last(nature_study._LOG)
        check(f"observation row kind ({where})", row.get("kind") == "observation", row)
        check(f"observation row where ({where})", row.get("where") == where, row)
        check(f"old keys still there ({where})", {"ts", "score", "feedback", "observation"} <= set(row), row)
    check("the prompt he is given is still only the scene (nothing added)",
          seen_user.get("user") == "What is before you now:\nSCENE-TEXT", seen_user)
    check("directive wording untouched", nature_study.directive().startswith("It is your NATURE STUDY now"))

    # ── practical rows ──
    task = practical_lesson.LADDER[0]
    with mock.patch.object(practical_lesson, "_pick", return_value=task), \
         mock.patch.object(practical_lesson, "_object_rooms", return_value={}), \
         mock.patch.object(practical_lesson, "_ledger_since", return_value=[]):
        practical_lesson._current_task()
        issued = _last(practical_lesson._LOG)
        check("issued row kind", issued.get("event") == "issued" and issued.get("kind") == "practical", issued)
        practical_lesson.run(trigger="period_end")
        graded = _last(practical_lesson._LOG)
        check("graded row kind", graded.get("kind") == "practical" and graded.get("attempted") is False, graded)

    # ── reader on the isolated logs just written ──
    r = npr.read(lab_dir, days=1)
    check("reader sees 2 observation lessons", r["observation_lessons"] == 2, r)
    check("reader decides them by the where field", r["rows_with_where_field"] == 2, r)
    check("reader: 1 of 2 window view", r["window_view"] == 1 and abs(r["window_share"] - 0.5) < 1e-9, r)
    check("reader sees the issued practical and the unattempted grade",
          r["practical_issued"] == 1 and r["practical_graded"] == 1 and r["practical_attempted"] == 0, r)
    check("defeater (b) fires when no practical was attempted", r["defeater_b_practicals_not_done"] is True, r)
    check("defeater (a) holds at 50%", r["defeater_a_window_share_over_limit"] is False, r)

    # ── reader on synthetic data: legacy wording fallback, and an over-limit month ──
    syn = lab_dir / "syn"
    syn.mkdir(exist_ok=True)
    now = time.time()
    with open(syn / "nature_study_log.jsonl", "w", encoding="utf-8") as f:
        for i in range(8):     # legacy rows, no 'where': 7 window-wording, 1 garden-wording
            txt = "the garden bed, parsley and thyme" if i == 0 else "the fence and the mailbox flag"
            f.write(json.dumps({"ts": now - i * 3600, "score": 0.9, "feedback": "", "observation": txt}) + "\n")
    with open(syn / "practical_log.jsonl", "w", encoding="utf-8") as f:
        f.write(json.dumps({"ts": now - 10, "kind": "practical", "task": "x", "attempted": True, "ok": True}) + "\n")
    r2 = npr.read(syn, days=30)
    check("legacy rows fall back to wording (7 of 8)", r2["window_view"] == 7 and r2["rows_with_where_field"] == 0, r2)
    check("defeater (a) trips over 70% (87.5%)", r2["defeater_a_window_share_over_limit"] is True, r2)
    check("defeater (b) holds when a practical was done", r2["defeater_b_practicals_not_done"] is False, r2)
    check("reader main() runs", npr.main(["--data", str(syn), "--days", "30"]) == 0)

print()
print("FAILED: " + ", ".join(FAIL) if FAIL else "ALL PASS")
sys.exit(1 if FAIL else 0)
