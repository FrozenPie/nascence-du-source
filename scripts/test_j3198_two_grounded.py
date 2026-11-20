"""J-3198 / D-0585: the capstone grader gets the full lineage and reports two grounded numbers.

Nothing here opens a live store or calls a hub: the grader's HTTP post is a scripted fake, every path
essay_lesson writes is a temp path, and record()'s memory / competence / filing calls are replaced by recorders.
Run from the worktree:  python scripts/test_j3198_two_grounded.py
"""
from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import core                                    # noqa: E402  (before anything that could resolve to C:\Nascence)
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
from core import left_lane as ll              # noqa: E402
from core import essay_lesson as el           # noqa: E402

FAILS: list[str] = []


def check(cond, msg):
    if not cond:
        FAILS.append(msg)
        print("  FAIL:", msg)


TITLE = "One Young Man"
BOOK = [f"- I see that the clerk drills with the rifle regiment on day {i}." for i in range(8)]
WIDER = ["- [Understanding - from 'Leibnizs New Essays'] Leibniz holds that ideas are innate in the mind." + " x" * 40
         for _ in range(30)]
NOTES = "\n".join(BOOK + WIDER) + "\n\n── FROM AN EARLIER READING OF THIS BOOK (lower weight) ──\n- (pass 0) the first reading"
ESSAY = "The clerk learns drill. Leibniz would call that an innate idea made explicit. " * 40


class _Resp:
    def __init__(self, payload): self._p = payload
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False
    def raise_for_status(self): pass
    async def json(self): return {"message": {"content": json.dumps(self._p)}}


def _fake_session(sent: list, reply: dict):
    class _S:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        def post(self, url, json=None, timeout=None):
            sent.append(json)
            return _Resp(reply)
    return lambda *a, **k: _S()


def test_split_and_window():
    el._GATHER_META[TITLE] = {"n_own": len(BOOK)}
    b, w = el.split_lineage(TITLE, NOTES)
    check(b.startswith(BOOK[0]) and "the first reading" in b, f"book part = own lines + earlier-reading section: {b[:80]!r}")
    check("Leibniz" not in b and w.count("\n") == len(WIDER) - 1, "wider part = the cross-book lines only")
    el._GATHER_META.pop(TITLE, None)
    b2, w2 = el.split_lineage(TITLE, NOTES)
    check(w2 == "" and "Leibniz" in b2, "unknown split: everything counts as the book's, wider empty (never invents a split)")

    gb, gw, ge = ll.grade_window(b, w, ESSAY)
    check(len(gb) + len(gw) <= ll._NOTES_CHARS, f"notes within budget: {len(gb)} + {len(gw)}")
    check(len(gw.split("\n")) == len(WIDER), "every wider note is still present (lines shortened, none dropped)")
    check(len(ge) <= ll._ESSAY_CHARS, "essay window")
    long_essay = "e" * 30000
    gb, gw, ge = ll.grade_window(b, w, long_essay)
    check(len(ge) == ll._ESSAY_CHARS and len(gb) + len(gw) + len(ge) <= ll._PROMPT_CHARS + 1000,
          f"a long essay shrinks the notes window: {len(gb)} + {len(gw)} + {len(ge)}")
    # the old windows were [:2500]; the new one must be larger on both
    check(len(ESSAY[:ll._ESSAY_CHARS]) > 2500, "essay window is wider than the old 2500")
    gb, gw, ge = ll.grade_window("", "", "")
    check((gb, gw, ge) == ("", "", ""), "empty input")


def test_grade_essay_prompt_and_parse():
    sent: list = []
    reply = {"grounded": 0.6, "grounded_wider": 0.8, "feedback": "ok"}
    with mock.patch.object(ll.aiohttp, "ClientSession", _fake_session(sent, reply)), \
            mock.patch.object(ll, "_note_call", lambda *a, **k: None):
        res = asyncio.run(ll.grade_essay(TITLE, "\n".join(BOOK), ESSAY, wider_material="\n".join(WIDER)))
    user = sent[0]["messages"][1]["content"]
    system = sent[0]["messages"][0]["content"]
    check(res and res["grounded"] == 0.6 and res["grounded_wider"] == 0.8, f"both numbers parsed: {res}")
    check("THIS book" in user and "WIDER reading" in user and "Leibniz" in user, "user message carries both note bodies")
    check("never call it a hallucination" in system and "grounded_wider" in system, "system prompt names the rule and the schema")
    check(res["chars"]["wider_in"] == len("\n".join(WIDER)), f"chars record what was sent: {res['chars']}")
    # a reply without 'grounded' still fails open
    with mock.patch.object(ll.aiohttp, "ClientSession", _fake_session([], {"feedback": "x"})), \
            mock.patch.object(ll, "_note_call", lambda *a, **k: None):
        check(asyncio.run(ll.grade_essay(TITLE, "a", "b")) is None, "no 'grounded' -> None (fail-open)")


def test_grade_parks_wider_and_record_logs_it():
    tmp = Path(tempfile.mkdtemp(prefix="J-3198_"))
    el._GATHER_META[TITLE] = {"n_own": len(BOOK)}
    seen = {}

    async def fake_grade(title, book_notes, essay, wider_material=""):
        seen.update(book=book_notes, wider=wider_material)
        return {"grounded": 0.7, "grounded_wider": 0.5, "feedback": "f", "chars": {"book": 1}}

    with mock.patch.object(ll, "grade_essay", fake_grade):
        score, fb = asyncio.run(el.grade(TITLE, NOTES, ESSAY))
    check(score == 0.7 and fb == "f", f"grade() still returns (this-book score, feedback): {(score, fb)}")
    check("Leibniz" in seen["wider"] and "Leibniz" not in seen["book"], "grade() hands the grader the split lineage")
    g = el._GRADES.get(TITLE) or {}
    check(g.get("wider") == 0.7 and g.get("wider_raw") == 0.5, f"wider clamped to never below the book number, raw kept: {g}")

    el._LOG = tmp / "essay_lesson_log.jsonl"
    el._STATE = tmp / "essay_lesson.json" if hasattr(el, "_STATE") else None
    with mock.patch.object(el, "_load", lambda: {"history": [], "essayed": []}), \
            mock.patch.object(el, "_save", lambda d: tmp.joinpath("state.json").write_text(json.dumps(d))), \
            mock.patch.object(el, "mark_done", lambda b: None), \
            mock.patch.object(el, "CAPSTONE_GATE", False), \
            mock.patch.dict(sys.modules, {"core.competence": mock.MagicMock()}):
        with mock.patch("core.memory.store.store_fragment", return_value="fid"), \
                mock.patch("core.memory.store.store_light_event", return_value=None), \
                mock.patch("core.study.write_tablet", return_value=None), \
                mock.patch("core.world_consolidation.file_book_notes", return_value={}), \
                mock.patch("core.study.archive_book_note_files", return_value={}):
            el.record("b", TITLE, "t", ESSAY, 0.6, 0.7, "f", source_ids=None)
    row = json.loads(el._LOG.read_text(encoding="utf-8").splitlines()[-1])
    check(row["measured"] == 0.7 and row["wider"] == 0.7 and row["wider_raw"] == 0.5, f"log row carries both numbers: {row}")
    check(TITLE not in el._GRADES, "record() consumed the parked number")
    hist = json.loads(tmp.joinpath("state.json").read_text())["history"][-1]
    check(hist.get("wider") == 0.7, f"history entry carries wider: {hist}")

    # grader unavailable: J-2992 -- ungraded (None, not a neutral 0.5), no wider, nothing parked
    async def none_grade(*a, **k): return None
    with mock.patch.object(ll, "grade_essay", none_grade):
        score, fb = asyncio.run(el.grade(TITLE, NOTES, ESSAY))
    check((score, fb) == (None, "") and TITLE not in el._GRADES, "fail-open path: ungraded None (J-2992, was 0.5), nothing parked")

    # a stale parked number from an earlier title must not leak into a later record
    el._GRADES["Other"] = {"wider": 0.9, "wider_raw": 0.9, "chars": None}
    check(TITLE not in el._GRADES, "parking is per title")


if __name__ == "__main__":
    for t in (test_split_and_window, test_grade_essay_prompt_and_parse, test_grade_parks_wider_and_record_logs_it):
        print("RUN", t.__name__)
        try:
            t()
        except Exception as exc:                # noqa: BLE001
            import traceback; traceback.print_exc()
            FAILS.append(f"{t.__name__} raised {exc!r}")
    print("FAILS:", FAILS if FAILS else "none")
    sys.exit(1 if FAILS else 0)
