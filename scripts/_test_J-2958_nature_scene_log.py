"""J-2958 (F-3651): nature_study logs the scene + inference, and the grader gets a task string matching the lesson.
Every file is under a temp dir; model calls and memory writers are stubs. Run from the worktree:
    python scripts/_test_J-2958_nature_scene_log.py
"""
from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from pathlib import Path
from unittest import mock

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(1, str(Path.home() / ".claude" / "skills" / "job-queue"))

import core  # noqa: E402  -- BEFORE lab_env
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
import lab_env  # noqa: E402
from core import nature_study as ns, left_lane, competence, profile  # noqa: E402
sys.path.insert(0, str(ROOT / "scripts"))
import nature_copy_rate as ncr  # noqa: E402

FAILS: list[str] = []


def check(cond, msg):
    print(f"  [{'PASS' if cond else 'FAIL'}] {msg}")
    if not cond:
        FAILS.append(msg)


SCENE = "A wren sits on the fence post beside the grey mailbox; the wet lawn shines and a cold wind moves the lavender."
OBS = "A small brown wren on the fence post, the grey mailbox beside it, the wet lawn shining, lavender moving in a cold wind."
INF = "The wind is from the sea."
tmp = Path(tempfile.mkdtemp(prefix="J-2958_"))
seen = {}


async def fake_json(urls, sysmsg, user, **kw):
    return {"observation": OBS, "inference": INF}


async def fake_grade(task, reference, work, rubric=""):
    seen.update(task=task, reference=reference, rubric=rubric)
    return {"grounded": 0.7, "feedback": "ok"}


with mock.patch.object(ns, "_LOG", tmp / "nature_study_log.jsonl"), mock.patch.object(ns, "_STATE", tmp / "state.json"), \
        mock.patch.object(ns, "_scene", lambda: SCENE), mock.patch.object(ns, "_where", lambda: "study"), \
        mock.patch.object(left_lane, "grade_work", fake_grade), \
        mock.patch.object(competence, "record_drill_accuracy", lambda *a, **k: None), \
        mock.patch("core.memory.store.store_fragment", lambda **k: None):
    res = asyncio.run(ns.run(fake_json, ["http://stub"]))

print("[1] log row")
row = json.loads((tmp / "nature_study_log.jsonl").read_text(encoding="utf-8").splitlines()[0])
check(row.get("scene") == SCENE, "row carries the scene text")
check(row.get("inference") == INF, "row carries the inference")
check(row.get("obs_chars") == len(OBS), "row carries the untruncated observation length")
check(all(k in row for k in ("ts", "score", "graded", "feedback", "observation", "kind", "where")), "old keys unchanged")
check(row["observation"] == OBS[:300] and row["kind"] == "observation" and row["where"] == "study", "old key values unchanged")
check(res["score"] == 0.7, "run() return unchanged")

print("[2] grader task string")
check(seen.get("task") == ns._GRADE_TASK and seen.get("reference") == SCENE, "grader gets the aligned task + the scene as reference")
check("particulars" in seen["task"] and "inference" in seen["task"] and "one real thing" not in seen["task"],
      "task names the particulars then one inference")
check(seen.get("rubric") == "", "grade_work rubric untouched (default)")

print("[3] write fence still a total no-op when refused")
with mock.patch.object(ns, "_LOG", tmp / "refused.jsonl"), mock.patch.object(ns, "_STATE", tmp / "refused_state.json"), \
        mock.patch.object(profile, "guard_path", side_effect=profile.NonLiveWriteError("x")):
    try:
        ns._record(OBS, INF, 0.5, "f", "study", SCENE)
        check(False, "refused write raises")
    except profile.NonLiveWriteError:
        check(not (tmp / "refused.jsonl").exists(), "refused: raised, nothing written")

print("[4] copy-rate reader")
r = ncr.copy_rate(SCENE, OBS)
check(r["word_share"] is not None and r["word_share"] > 0.5, f"high-copy observation reads high: {r}")
r2 = ncr.copy_rate(SCENE, "Granite boulders and a heron stalking the tidal shallows of a distant estuary.")
check(r2["word_share"] < 0.2, f"unrelated observation reads low: {r2}")
rd = ncr.read([row, {"observation": "old row, no scene"}], n=20)
check(rd["no_scene"] == 1 and rd["measured"] == 1 and not rd["enough"], f"old rows counted no_scene, not guessed: {rd}")

print("FAIL" if FAILS else "ALL PASS", FAILS)
raise SystemExit(1 if FAILS else 0)
