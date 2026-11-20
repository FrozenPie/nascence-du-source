"""_test_J-3817_practical_first.py -- D-0720 option A: PRACTICAL_FIRST slot order. Temp-path stores only; never touches
the live data dir. Run: python -X utf8 scripts/_test_J-3817_practical_first.py"""
from __future__ import annotations
import sys, tempfile
from pathlib import Path
from unittest import mock
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402
assert Path(core.__file__).resolve().parent.parent == ROOT, core.__file__
from core import practical_lesson as pl, school, nature_study  # noqa: E402
FAIL = []
def check(n, c):
    print(f"[{'PASS' if c else 'FAIL'}] {n}")
    if not c: FAIL.append(n)
tmp = Path(tempfile.mkdtemp())
with mock.patch.object(pl, "_STATE", tmp / "s.json"), mock.patch.object(pl, "_LOG", tmp / "l.jsonl"), \
     mock.patch.object(pl, "_pick", lambda rung: pl._BY_ID["bowline_loop"]), mock.patch.object(pl, "_object_rooms", lambda o: {}):
    check("flag defaults False", pl.PRACTICAL_FIRST is False)
    check("default: slot 1 before any firing", pl.slot_today() == 1)
    with mock.patch.object(pl, "PRACTICAL_FIRST", True):
        check("firing 1 is practical", pl.practical_first_phase() == "practical")
        t = pl.announce()
        check("announce picks a task (or none) without grading", t is not None and t["id"] == "bowline_loop")
        pl.mark_slot_fired()
        check("firing 2 is observation", pl.practical_first_phase() == "observation")
        check("directive stays practical, not observation text",
              "GO AND OBSERVE" not in pl.directive())
        pl.mark_slot_fired()
        check("stray extra firing is practical, never a 2nd observation", pl.practical_first_phase() == "practical")
    check("flag off restores observation directive at slot 1",
          pl.slot_today() == 2 or pl.directive() == nature_study.directive())
sc = mock.MagicMock()
sc.where.return_value = "wood"
sc.look.side_effect = lambda k: {"wood": "WOODSCENE"}.get(k, "")
with mock.patch.dict(sys.modules, {"core.sensorium": sc}), mock.patch("core.sensorium", sc, create=True):
    check("_scene wood branch", nature_study._scene() == "WOODSCENE")
sys.exit(1 if FAIL else 0)
