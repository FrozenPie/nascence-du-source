"""
Offline test for J-3200 / D-0587: core.associative_recall.recall_fragments(exclude_own_works=True).

The authoring act's grounding must not return his own earlier WORKS (origin 'study', header
"[My study note: '<title>'] ...", title == first line of a data/Study/WORK_*.md file), while study notes stay
and the default call (exclude_own_works=False) is byte-identical to before.

SAFETY. Everything runs against a tempdir: core.study.STUDY_DIR and the new _OWN_WORKS_LOG are pointed there,
recall_trail/_load_rows/_embed are stubbed (no DB, no embedding model), profile.guard_path is made a pass-through.
Nothing under C:\\Nascence\\data or this tree's data/ is opened.

Run: python scripts/_test_j3200_exclude_own_works.py   (exit 0 = all passed)
"""
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import core  # noqa: E402  (BEFORE anything that could resolve a different tree)
assert str(Path(core.__file__).resolve()).lower().startswith(str(TREE).lower()), core.__file__
from core import associative_recall as ar  # noqa: E402

# J-4052: the live Du has run this feature since the 2026-11-14 boot, so the live data/ log legitimately EXISTS; what this
# test must prove is that IT did not write there. Snapshot the size of both candidate logs before anything runs.
_LIVE_LOGS = (Path(r"C:\Nascence\data") / "author_grounding_works_excluded.jsonl", TREE / "data" / "author_grounding_works_excluded.jsonl")
_LIVE_BEFORE = {str(_p): (_p.stat().st_size if _p.exists() else None) for _p in _LIVE_LOGS}
from core import study  # noqa: E402
from core import profile  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (("  " + detail) if (detail and not cond) else ""))
    if not cond:
        FAILS.append(name)


tmp = Path(tempfile.mkdtemp(prefix="J-3200_"))
sdir = tmp / "Study"
sdir.mkdir()
study.STUDY_DIR = sdir
ar._OWN_WORKS_LOG = tmp / "works_excluded.jsonl"
profile.guard_path = lambda p: p
ar._WORK_TITLES.update(stamp=None, titles=frozenset())

(sdir / "WORK_20261029_0100_Mottainai.md").write_text("# On Mottainai and the Unwasted\n\n*A study note by x*\n\nbody\n", encoding="utf-8")
(sdir / "WORK_20261029_0200_Quote.md").write_text("# It's a Matter of 'Fact'\n\nbody\n", encoding="utf-8")
(sdir / "TAB_20261029_0300_Knots.md").write_text("# How knots hold\n\nbody\n", encoding="utf-8")
(sdir / "ESSAY_20261029_0400_Water.md").write_text("# Water and Tubes\n\nbody\n", encoding="utf-8")

FR = {
    "w1": ("study", "[My study note: 'On Mottainai and the Unwasted'] The idea of not wasting..."),
    "n1": ("study", "[My study note: 'How knots hold'] A friction hitch grips because..."),
    "w2": ("study", "[My study note: 'It's a Matter of 'Fact''] fact versus method..."),
    "e1": ("study", "[My study note: 'Water and Tubes'] Water rises in a thin tube..."),
    "s1": ("study", "[My study note: 'Knots' . on 'The Ashley Book' . subject: knots] A hitch..."),
    "r1": ("reading", "[From 'Mottainai: a word'] reading text about waste"),
    # same title as a work but a NON-study origin must never be touched by the exclusion
    "x1": ("lived", "[My study note: 'On Mottainai and the Unwasted'] lived-origin lookalike"),
    "w3": ("study", "[My study note: 'On Mottainai and the Unwasted'] A second copy of the same work"),
    "n2": ("study", "[My study note: 'A note whose body quotes On Mottainai and the Unwasted'] body"),
}
ORDER = ["w1", "n1", "w2", "e1", "s1", "w3", "r1", "x1", "n2"]
ar._embed_called = []


def fake_trail(qv, **kw):
    return [{"fragment_id": f, "activation": 1.0 - i * 0.01} for i, f in enumerate(ORDER)]


def fake_rows(ids):
    return {f: {"content": FR[f][1], "origin": FR[f][0]} for f in ids}


import core.memory.store as _store  # noqa: E402
_store._embed = lambda q: [0.1]
ar.recall_trail = fake_trail
ar._load_rows = fake_rows

# 1 default: byte-identical, includes works, writes no log
base = ar.recall_fragments("mottainai", k=5, grounded_only=True)
check("default keeps works (unchanged behaviour)", [m["fragment_id"] for m in base] == ["w1", "n1", "w2", "e1", "s1"],
      str([m["fragment_id"] for m in base]))
check("default writes no exclusion log", not ar._OWN_WORKS_LOG.exists())

# 2 flag: works out, notes/essays/study_note-shaped/lookalike stay; k counts only what is shown
ex = ar.recall_fragments("mottainai", k=5, grounded_only=True, exclude_own_works=True)
ids = [m["fragment_id"] for m in ex]
check("works excluded, k refilled down the trail", ids == ["n1", "e1", "s1", "r1", "x1"], str(ids))
check("study notes stay (TAB, ESSAY, study_note-shaped)", {"n1", "e1", "s1"} <= set(ids))
check("title with apostrophes recognised as a work", "w2" not in ids)
check("non-study origin with a work's title is untouched", "x1" in ids)
ex_all = [m["fragment_id"] for m in ar.recall_fragments("mottainai", k=15, grounded_only=True, exclude_own_works=True)]
check("a note whose body merely quotes a work title is kept (k=15)", "n2" in ex_all and not ({"w1", "w2", "w3"} & set(ex_all)), str(ex_all))

# 3 log row
rows = [json.loads(ln) for ln in ar._OWN_WORKS_LOG.read_text(encoding="utf-8").splitlines()]
check("one row per flagged call", len(rows) == 2, str(len(rows)))
check("row counts the excluded works", rows[0]["n_excluded"] == 3 and rows[0]["excluded_ids"] == ["w1", "w2", "w3"]
      and rows[0]["n_shown"] == 5, str(rows[0]))

# 4 a work filed after the first call is picked up (dir mtime cache)
(sdir / "WORK_20261029_0500_New.md").write_text("# A Brand New Work\n\nbody\n", encoding="utf-8")
os.utime(sdir, ns=(os.stat(sdir).st_atime_ns, os.stat(sdir).st_mtime_ns + 5_000_000_000))
FR["w9"] = ("study", "[My study note: 'A Brand New Work'] text")
ORDER.insert(0, "w9")
ex2 = [m["fragment_id"] for m in ar.recall_fragments("q", k=3, grounded_only=True, exclude_own_works=True)]
check("newly filed work excluded on the next call", "w9" not in ex2, str(ex2))

# 5 fail-open: no Study dir / no titles -> nothing excluded, no raise
study.STUDY_DIR = tmp / "nope"
ar._WORK_TITLES.update(stamp=None, titles=frozenset())
ex3 = [m["fragment_id"] for m in ar.recall_fragments("q", k=3, grounded_only=True, exclude_own_works=True)]
check("missing Study dir -> fail-open (nothing excluded)", ex3 == ["w9", "w1", "n1"], str(ex3))

# 6 live data/ untouched
for root in _LIVE_LOGS:
    # a live Du appends to this file in its own process meanwhile, so the log GROWING is not this test writing; the file
    # appearing where there was none (a fresh tree), or shrinking, would be.
    _was, _now = _LIVE_BEFORE[str(root)], (root.stat().st_size if root.exists() else None)
    check("no write under " + str(root.parent), (_was is None and _now is None) or (_was is not None and _now is not None and _now >= _was))

print("\n%d failed" % len(FAILS) if FAILS else "\nall passed")
sys.exit(1 if FAILS else 0)
