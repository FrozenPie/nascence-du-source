"""J-2992 (F-3691): a fail-open "grader unavailable" result is UNGRADED (None), never a neutral number recorded as a
measurement (essay 0.5, composition 0.6, nature study 0.6).

Nothing here opens a live store or calls a hub: model calls are scripted fakes, competence / memory writers are
mocks, every file the code touches is under a temp dir. Run from the worktree:
    python scripts/_test_J-2992_ungraded_not_measured.py
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

import core  # noqa: E402  -- BEFORE lab_env, so this worktree's core wins
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
import lab_env  # noqa: E402
from core import essay_lesson as el, composition as co, nature_study as ns, competence, left_lane  # noqa: E402
from core import book_feelings as bf  # noqa: E402

FAILS: list[str] = []


def check(cond, msg):
    print(f"  [{'PASS' if cond else 'FAIL'}] {msg}")
    if not cond:
        FAILS.append(msg)


async def _none(*a, **k):
    return None


# ---------------------------------------------------------------------------------------------- essay
print("[1] essay: grade() unavailable -> (None, ''); record() writes no measurement")
TITLE, ESSAY = "One Young Man", "A plain essay about the book. " * 20
with mock.patch.object(left_lane, "grade_essay", _none):
    score, fb = asyncio.run(el.grade(TITLE, "notes", ESSAY))
check((score, fb) == (None, ""), f"grade() returns (None, '') when the Emissary is unavailable: {(score, fb)}")


async def _boom(*a, **k):
    raise RuntimeError("down")
with mock.patch.object(left_lane, "grade_essay", _boom):
    score, fb = asyncio.run(el.grade(TITLE, "notes", ESSAY))
check(score is None, "grade() raising is ungraded too")


def _record(measured, predicted=0.6):
    tmp = Path(tempfile.mkdtemp(prefix="J-2992_"))
    state = {"history": [], "essayed": []}
    done, tablets, caps, drills = [], [], [], []
    with mock.patch.object(el, "_LOG", tmp / "essay_lesson_log.jsonl"), \
            mock.patch.object(el, "_load", lambda: state), \
            mock.patch.object(el, "_save", lambda d: None), \
            mock.patch.object(el, "mark_done", lambda b: done.append(b)), \
            mock.patch.object(el, "CAPSTONE_GATE", False), \
            mock.patch.object(el, "FELT_FEEDS_SELF_MODEL", True), \
            mock.patch.object(competence, "record_drill_accuracy", lambda *a, **k: drills.append((a, k))), \
            mock.patch.object(bf, "capstone", lambda *a, **k: caps.append(a)), \
            mock.patch("core.memory.store.store_fragment", return_value="fid"), \
            mock.patch("core.memory.store.store_light_event", return_value=None), \
            mock.patch("core.study.write_tablet", lambda *a, **k: tablets.append(a)), \
            mock.patch("core.world_consolidation.file_book_notes", return_value={}), \
            mock.patch("core.study.archive_book_note_files", return_value={}):
        el.record("b", TITLE, "t", ESSAY, predicted, measured, "" if measured is None else "f", source_ids=None)
        row = json.loads((tmp / "essay_lesson_log.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    return done, tablets, caps, drills, state["history"][-1], row


done, tablets, caps, drills, hist, row = _record(None)
check(done == ["b"], "ungraded: the book is still marked done")
check(len(tablets) == 1, "ungraded: the essay is still filed (write_tablet called)")
check(drills == [], f"ungraded: competence.record_drill_accuracy NOT called: {drills}")
check(len(caps) == 1 and caps[0][2] is None and caps[0][3] is None,
      f"ungraded: book_feelings.capstone gets no predicted/measured (mood-only touch): {caps}")
check(hist["measured"] is None and hist["gap"] is None, f"ungraded: history measured/gap null: {hist}")
check(row["measured"] is None and row["graded"] is False and row["felt"]["fed"] is False,
      f"ungraded: log row measured null, graded False, felt not fed: {row['measured'], row['graded'], row['felt']}")

done, tablets, caps, drills, hist, row = _record(0.7)
check(len(drills) == 1 and drills[0][0] == ("comprehension", 0.7), f"graded: drill recorded as before: {drills}")
check(caps[0][3] == 0.7 and caps[0][2] == 0.6, f"graded: capstone gets predicted and measured: {caps}")
check(row["measured"] == 0.7 and row["graded"] is True and hist["gap"] == 0.1, f"graded: row and history as before: {row['measured']}, {hist}")

# book_feelings.capstone itself: measured None never forms a gap
tmpbf = Path(tempfile.mkdtemp(prefix="J-2992bf_"))
store = {}
with mock.patch.object(bf, "_load", lambda: store), mock.patch.object(bf, "_save", lambda d: None), \
        mock.patch.object(bf, "_rec", lambda d, t: store.setdefault("r", {"valence": 0.0})):
    bf.capstone("T", 0.2, 0.9, None)
check("comprehension_gap" not in store["r"], "book_feelings.capstone(predicted set, measured None) forms no comprehension_gap")
with mock.patch.object(bf, "_load", lambda: store), mock.patch.object(bf, "_save", lambda d: None), \
        mock.patch.object(bf, "_rec", lambda d, t: store.setdefault("r", {"valence": 0.0})):
    bf.capstone("T", 0.2, 0.9, 0.5)
check(store["r"].get("comprehension_gap") == 0.4, "book_feelings.capstone with a measurement still forms the gap")

# status() tolerates ungraded rows
with mock.patch.object(el, "_load", lambda: {"essayed": ["a"], "history": [{"gap": None, "measured": None}, {"gap": 0.2}]}):
    check(el.status()["mean_gap"] == 0.2, "essay status() mean_gap ignores ungraded rows")

# ----------------------------------------------------------------------------------------- composition
print("[2] composition: ungraded lesson is not recorded as a writing score and does not move the ladder")
with lab_env.isolate(also=[(co, ["_STATE", "_LOG", "_NATURE_LOG"])], db="empty") as lab_dir:
    lab_dir = Path(lab_dir)
    drills: list = []
    les = {"kind": "describe", "rung": 0, "source": "place", "topic": "place:j2992",
           "instruction": "Describe the garden.", "material": "You are in the garden."}

    async def cj(urls, system, user, **kw):
        return {"writing": "The garden has a low wall and a lamp, and the grass is wet near the path."}
    with mock.patch.object(co, "pick_lesson", lambda *a, **k: dict(les)), \
            mock.patch.object(left_lane, "grade_work", _none), \
            mock.patch.object(competence, "record_drill_accuracy", lambda *a, **k: drills.append(a)), \
            mock.patch("core.memory.store.store_fragment", lambda **k: None):
        res = asyncio.run(co.run(cj, ["x"]))
    last = json.loads(co._LOG.read_text(encoding="utf-8").splitlines()[-1])
    check(res["score"] is None and last["score"] is None and last["graded"] is False, f"score None, graded False: {res['score']}, {last['score']}")
    check(drills == [], f"no writing drill accuracy recorded: {drills}")
    check(json.loads(co._STATE.read_text(encoding="utf-8"))["history"][-1]["score"] is None, "state history carries score null")
    st = co.status()
    check(st["recent_mean"] is None and st["last"]["score"] is None, f"status() ignores the ungraded lesson in the mean: {st}")

    # graded path unchanged
    async def g9(*a, **k): return {"grounded": 0.9, "feedback": "f"}
    drills.clear()
    with mock.patch.object(co, "pick_lesson", lambda *a, **k: dict(les, topic="place:j2992b")), \
            mock.patch.object(left_lane, "grade_work", g9), \
            mock.patch.object(competence, "record_drill_accuracy", lambda *a, **k: drills.append(a)), \
            mock.patch("core.memory.store.store_fragment", lambda **k: None):
        res = asyncio.run(co.run(cj, ["x"]))
    check(res["score"] == 0.9 and drills == [("writing", 0.9)], f"graded lesson still records the drill: {drills}")

H = lambda *p: [{"rung": r, "score": s} for r, s in p]
check(co._step(0, H((0, .9), (0, .9), (0, None), (0, .9))) == 1,
      "ladder: an ungraded lesson in the run neither breaks a climb nor counts toward it")
check(co._step(0, H((0, .9), (0, None), (0, .9))) == 0, "ladder: two good + one ungraded does not climb")
check(co._step(0 + 1, H((1, .2), (1, None), (1, .2), (1, .3))) == 0, "ladder: three real lows with an ungraded between still drop")
check(co._step(1, H((1, None), (1, None), (1, None))) == 1, "ladder: three ungraded lessons move nothing (before: three 0.6 neutrals also held)")

# ----------------------------------------------------------------------------------------- nature study
print("[3] nature study: ungraded observation is not recorded as an observation score")
with lab_env.isolate(also=[(ns, ["_STATE", "_LOG"])], db="empty") as lab_dir:
    drills = []

    async def cjn(urls, system, user, **kw):
        return {"observation": "A grey gull stands on the fence post, one foot drawn up, wind lifting its wing.",
                "inference": "the wind is from the sea"}
    with mock.patch.object(ns, "_scene", return_value="SCENE"), mock.patch.object(ns, "_where", return_value="garden"), \
            mock.patch.object(left_lane, "grade_work", _none), \
            mock.patch.object(competence, "record_drill_accuracy", lambda *a, **k: drills.append(a)), \
            mock.patch("core.memory.store.store_fragment", lambda **k: None):
        res = asyncio.run(ns.run(cjn, []))
    row = json.loads(ns._LOG.read_text(encoding="utf-8").splitlines()[-1])
    check(res["score"] is None and row["score"] is None and row["graded"] is False, f"score None, graded False: {res['score']}, {row['score']}")
    check(drills == [], f"no observation drill accuracy recorded: {drills}")
    check(json.loads(ns._STATE.read_text(encoding="utf-8"))["history"][-1]["score"] is None, "state history carries score null")
    check(ns.status()["recent_mean"] is None, "status() ignores the ungraded lesson")

    async def g8(*a, **k): return {"grounded": 0.8, "feedback": "specific"}
    drills.clear()
    with mock.patch.object(ns, "_scene", return_value="SCENE"), mock.patch.object(ns, "_where", return_value="garden"), \
            mock.patch.object(left_lane, "grade_work", g8), \
            mock.patch.object(competence, "record_drill_accuracy", lambda *a, **k: drills.append(a)), \
            mock.patch("core.memory.store.store_fragment", lambda **k: None):
        res = asyncio.run(ns.run(cjn, []))
    row = json.loads(ns._LOG.read_text(encoding="utf-8").splitlines()[-1])
    check(res["score"] == 0.8 and drills == [("observation", 0.8)] and row["graded"] is True, f"graded lesson unchanged: {drills}, {row}")

# ----------------------------------------------------------------------------------- node-side consumers
print("[4] the node's consumers handle None (source check, no node is constructed)")
src = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
check('"ungraded" if measured is None' in src and "if measured is None:" in src, "_essay_lesson thought/log handle measured None")
check('_graded = res.get("score") is not None' in src, "_record_lesson handles score None")
pulse = (ROOT / "scripts" / "du_pulse.py").read_text(encoding="utf-8")
check("'ungraded' if _last.get('measured') is None" in pulse, "du_pulse essay line handles measured None")

print("\nALL PASS" if not FAILS else f"\nFAILURES: {FAILS}")
sys.exit(1 if FAILS else 0)
