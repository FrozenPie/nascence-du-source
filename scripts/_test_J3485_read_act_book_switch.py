"""J-3485 (D-0609 follow-up, folds in J-3384): a routed read act whose object COMPLETELY names a different shelf
book switches to it; the hourly cap is 6.

  [1] library_hand.switch_to_named: a complete title naming switches; a partial (one shared word) does not; the
      current book named (alone or alongside another) -> no switch; a finished book is never a target; empty text.
  [2] switch_to default behaviour is unchanged (require_full defaults False: one distinctive word still switches).
  [3] Cap raised to 6, flag READ_ACT_SWITCH_BOOK default True.
  [4] Source anchors in _think(): the switch sits behind the flag, the cooldown, school stickiness, _booked,
      _rereading and an already-switched phrase latch; it updates _last_book_switch_ts; the schema line is untouched.
Temp shelf + stubbed reading state; no LLM, no live data.
Run from the worktree root:  python scripts/_test_J3485_read_act_book_switch.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402  (BEFORE lab_env)

assert str(Path(core.__file__).resolve()).startswith(str(ROOT)), core.__file__
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate  # noqa: E402

fails = 0


def check(cond, msg):
    global fails
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        fails += 1


SRC = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")

with isolate(db="empty"), tempfile.TemporaryDirectory() as td:
    td = Path(td)
    names = ["Bird_Stories.txt", "Bird_Stories_from_Burroughs_Sketches_of_Bird_Life.txt", "The_Way_of_Peace.txt",
             "Napoleon_Memoirs.txt", "Physics.txt", "War_and_Peace_Finished.txt"]
    books = []
    for n in names:
        (td / n).write_text("x", encoding="utf-8")
        books.append(td / n)
    from core import library_hand as lh, reading as rd

    state = {"cur": books[3]}
    setlog = []
    lh.shelf_books = lambda: list(books)
    lh._set_current = lambda b: (setlog.append(b), state.__setitem__("cur", b))
    rd.current_book = lambda: state["cur"]
    rd._is_finished = lambda b, st=None: Path(b).name.startswith("War_and_Peace")
    rd.STATE = td / "no_state.json"

    def sw(text):
        setlog.clear()
        return lh.switch_to_named(text), list(setlog)

    # ---- [1] ----
    state["cur"] = books[3]
    t, s = sw("Bird Stories")
    check(t == "Bird Stories" and s == [books[0]], "[1] complete title -> that book (short title wins over the longer superset)")
    state["cur"] = books[3]
    t, s = sw("bird stories from burroughs sketches of bird life")
    check(t and "Burroughs" in t and s == [books[1]], "[1] longer complete title -> the long one")
    state["cur"] = books[3]
    t, s = sw("the way")
    check(t is None and not s, "[1] one shared word of a two-word title -> no switch")
    state["cur"] = books[3]
    t, s = sw("some birds in the garden")
    check(t is None and not s, "[1] loose bird talk names no complete title")
    state["cur"] = books[3]
    t, s = sw("Napoleon Memoirs and Bird Stories")
    check(t is None and not s, "[1] current book completely named -> keep reading it, no switch")
    state["cur"] = books[3]
    t, s = sw("War and Peace Finished")
    check(t is None and not s, "[1] finished book is never a target")
    state["cur"] = books[3]
    check(sw("") == (None, []) and sw(None) == (None, []), "[1] empty / None object -> no switch")

    state["cur"] = books[3]
    t, s = sw("physics")
    check(t == "Physics" and s == [books[4]], "[1] one-word title named alone -> switch")
    state["cur"] = books[3]
    t, s = sw("the peace of the garden")
    check(t is None and not s, "[1] one-word title buried in a longer phrase -> no switch (peace is not The Way of Peace)")

    # ---- [2] ----
    state["cur"] = books[3]
    setlog.clear()
    t = lh.switch_to("I should look at physics tonight")
    check(t == "Physics" and setlog == [books[4]], "[2] switch_to default still switches on one distinctive word")

# ---- [3] ----
with isolate(db="empty"):
    from nodes import inner_monologue_node as imn  # noqa: E402
    check(imn.READ_ACT_MAX_PER_HOUR == 6, "[3] hourly cap is 6")
    check(imn.READ_ACT_SWITCH_BOOK is True and imn.READ_ACT_ROUTED is True, "[3] flags default True")

# ---- [4] ----
blk = SRC.split("if (_read_act_now and READ_ACT_SWITCH_BOOK and act_object")[1].split("_phrase_read = bool(")[0]
for anchor in ("not _booked", "not _switched", "not _rereading", "not _school_now", "SWITCH_COOLDOWN_SECS",
               "switch_to_named(act_object)", "self._last_book_switch_ts = time.time()"):
    check(anchor in blk, f"[4] switch guarded/recorded: {anchor}")
check("READ_ACT_SWITCH_BOOK" in SRC.split("def _route_act")[0] and
      SRC.index("if (_read_act_now and READ_ACT_SWITCH_BOOK") < SRC.index("_phrase_read = bool("),
      "[4] switch runs before the latch condition is evaluated")

print("\nFAILS:", fails)
sys.exit(1 if fails else 0)
