"""J-3052 / F-3761 (P-0074): essay_lesson._reduce_notes budgets every batch so the joined condensed text fits the
window the section writers read (_SECTION_WINDOW), trims at a sentence boundary, flattens a list/dict "points" to
plain joined text, keeps the raw-head fallback for a failed batch, and reports batches / joined / kept lengths.

Temp paths only; the model is a scripted fake; no live store is read or written.
Run from the worktree:  python scripts/_test_J-3052_reduce_budget.py
"""
from __future__ import annotations
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/

import asyncio
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import core                                    # noqa: E402  (before anything that could resolve to C:\Nascence)
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
from core import essay_lesson as el            # noqa: E402

FAILS: list[str] = []
TMP = Path(tempfile.mkdtemp(prefix="j3052_"))
el._STATE = TMP / "essay_lesson_state.json"
el._LOG = TMP / "essay_lesson_log.jsonl"


def check(cond, msg):
    print(("  ok:   " if cond else "  FAIL: ") + msg)
    if not cond:
        FAILS.append(msg)


TITLE = "The Birds"
# ~40,000 characters of note lines -> 8 batches at _REDUCE_BATCH 5500
NOTES = "\n".join("- note %04d: the field marks of the species are set out with the range and the song %s."
                  % (i, "x" * 12) for i in range(470))
NOTES = NOTES[:40232]
assert len(NOTES) > 38000


def point_text(k: int, n: int = 1300) -> str:
    """~n chars of sentences that START with the batch marker [Bk]."""
    s, i = "[B%d] " % k, 0
    while len(s) < n:
        i += 1
        s += "Sentence %d about batch %d names a species, a number and a mechanism. " % (i, k)
    return s[:n]


class Fake:
    """reduce -> points per batch (shape per `shapes`), outline -> 3 sections, section -> text. Records every prompt."""
    def __init__(self, shapes=None, raise_on=()):
        self.k = 0
        self.shapes = shapes or {}
        self.raise_on = set(raise_on)
        self.reduce_sys = []
        self.outline_user = None
        self.section_users = []

    async def __call__(self, base_urls, system, user, max_tokens=0, temperature=0.0):
        if "Condense these study notes" in system:
            k = self.k
            self.k += 1
            self.reduce_sys.append(system)
            if k in self.raise_on:
                raise RuntimeError("hub timeout")
            t = point_text(k)
            sh = self.shapes.get(k, "str")
            if sh == "list":
                return {"points": [t[:650], t[650:]]}
            if sh == "dict":
                return {"points": {"Cowbirds": {"Behavior": t[:400], "Range": t[400:]}}}
            if sh == "empty":
                return {"points": ""}
            return {"points": t}
        if "Plan a real ESSAY" in system:
            self.outline_user = user
            return {"thesis": "t", "sections": [{"heading": "H%d" % i, "covers": "c"} for i in range(3)]}
        self.section_users.append(user)
        return {"section": "A section written from the notes. " * 12}


# ---- 1. coercion --------------------------------------------------------------------------------------------
print("coercion of points")
check(el._points_text("  plain  ") == "plain", "string passes through stripped")
check(el._points_text(["a one.", "b two.", ""]) == "a one.\nb two.", "list is joined line by line, blanks dropped")
dt = el._points_text({"Cowbirds": {"Behavior": "lay in nests", "Range": "wide"}})
check(dt == "Cowbirds: Behavior: lay in nests\nRange: wide" or ("Cowbirds" in dt and "lay in nests" in dt and "[" not in dt and "{" not in dt),
      "nested dict is flattened to text, no repr: %r" % dt)
check(el._points_text(None) == "" and el._points_text(7) == "7", "None -> empty, number -> its text")

# ---- 2. sentence trim ---------------------------------------------------------------------------------------
print("sentence-boundary trim")
t = point_text(0)
r = el._trim_at_sentence(t, 624)
check(len(r) <= 624 and r.endswith("."), "trimmed to <=624 and ends on a full stop (len %d)" % len(r))
check(len(r) >= 624 * 0.4, "does not over-trim")
check(el._trim_at_sentence("short.", 624) == "short.", "text that fits is unchanged")
check(not el._trim_at_sentence("word " * 300, 100).endswith("wor"), "no sentence stop -> cut at a space, not mid-word")

# ---- 3. the F-3761 replay: 8 batches of 1,300-char points ------------------------------------------------
print("8 batches, every one must reach the sections and the outline")
f = Fake()
st: dict = {}
out = asyncio.run(el._reduce_notes(f, ["u"], TITLE, NOTES, st))
check(st["batches"] == 8, "8 batches (got %s)" % st.get("batches"))
check(len(out) <= el._SECTION_WINDOW, "joined condensed text fits the section window (%d <= %d)" % (len(out), el._SECTION_WINDOW))
check(all("[B%d]" % k in out[:el._SECTION_WINDOW] for k in range(8)), "all 8 batch markers inside the first %d chars" % el._SECTION_WINDOW)
check(st["kept"] == st["joined"] == len(out), "kept == joined (nothing cut): %s" % st)
check(st["trimmed"] == 8, "each over-budget batch was trimmed (%s)" % st["trimmed"])
check(all(("At most %d characters" % st["budget"]) in s for s in f.reduce_sys) and st["budget"] == (5000 - 7) // 8,
      "the budget (%s) is told to the model" % st["budget"])
# what the OLD code did, to prove this test discriminates: join untrimmed 1,300-char points and cut at 5000
old_joined = "\n".join(point_text(k) for k in range(8))
check(sum(1 for k in range(8) if "[B%d]" % k in old_joined[:5000]) < 8,
      "sanity: the old untrimmed join loses batches in the first 5000 chars")

# ---- 4. through compose(): the prompts the model actually receives ---------------------------------------
print("compose(): outline and section prompts")
f = Fake()
_gate, el.CAPSTONE_GATE = el.CAPSTONE_GATE, False      # the fake sections repeat; keep the D-0562 regen out of this check
try:
    essay = asyncio.run(el.compose(f, ["u"], TITLE, NOTES))
finally:
    el.CAPSTONE_GATE = _gate
check(bool(essay) and len(f.section_users) == 3, "sectioned essay formed (%d section calls)" % len(f.section_users))
# J-3077: each section now reads its OWN share of the condensed notes, so the section prompts TOGETHER carry all 8
check(all(any("[B%d]" % k in u for u in f.section_users) for k in range(8)),
      "the section prompts together carry all 8 batches (J-3077: one slice each)")
check(all("[B%d]" % k in (f.outline_user or "") for k in range(8)), "the outline prompt carries all 8 batches")
rs = el._REDUCES.get(TITLE) or {}
check(rs.get("batches") == 8 and rs.get("kept") == rs.get("joined") and rs.get("in") == len(NOTES),
      "compose() parked the reduce stats for record(): %s" % rs)

# ---- 5. list/dict points, a failed batch, an empty batch ------------------------------------------------
print("list / dict points, failed and empty batches")
f = Fake(shapes={1: "list", 2: "list", 3: "dict", 5: "empty"}, raise_on=(4,))
st = {}
out = asyncio.run(el._reduce_notes(f, ["u"], TITLE, NOTES, st))
check(st["coerced"] == 3, "3 non-string points coerced (got %s)" % st["coerced"])
check("['" not in out and "{'" not in out, "no Python repr of a list or dict in the condensed text")
check(st["failed"] == 2, "raised batch + empty batch count as failed (got %s)" % st["failed"])
check(len(out) <= el._SECTION_WINDOW, "still inside the window (%d)" % len(out))
check(all("[B%d]" % k in out for k in (0, 1, 2, 3, 6, 7)), "the good batches are all present")
lines = out.split("\n")
check("note 0" in out and out.count("- note") >= 2, "failed/empty batches fall back to their raw head (note lines present)")

# ---- 6. few batches: no trimming of a modest set ------------------------------------------------------------
print("small note set")
small = "\n".join("- note %04d: the field marks of the species are set out clearly." % i for i in range(150))[:9000]
f = Fake()
st = {}
out = asyncio.run(el._reduce_notes(f, ["u"], TITLE, small, st))
check(st["batches"] == 2 and st["budget"] == (5000 - 1) // 2, "2 batches, budget %s" % st.get("budget"))
check("[B0]" in out and "[B1]" in out and len(out) <= 5000, "both batches present, in window")

# J-3598 (F-4210): threshold == window, so no un-reduced set loses a tail to notes[:window]
check(el._REDUCE_THRESHOLD == el._SECTION_WINDOW, "J-3598: _REDUCE_THRESHOLD == _SECTION_WINDOW")

# ---- 7. an unreduced set records batches 0, with an earlier-reading section the body is still whole -------
print("unreduced set + earlier reading")
f = Fake()
under = ("- n %03d some note. " % 0) * 100
PRIOR = "\n\n── FROM AN EARLIER READING ──\nEARLIER-MARK I once read it differently."
asyncio.run(el.compose(f, ["u"], "Small Book", under + PRIOR))
rs = el._REDUCES.get("Small Book") or {}
check(rs.get("batches") == 0 and rs.get("in") == len(under), "no reduce -> batches 0, in = body length: %s" % rs)
check("EARLIER-MARK" in (f.outline_user or ""), "the outline still sees the earlier-reading section")

# ---- 8. record() writes the reduce key (record's other side effects replaced) ------------------------------
print("record() log row")
el._REDUCES["Rec Book"] = {"batches": 8, "in": 40232, "budget": 624, "joined": 4990, "kept": 4990,
                           "trimmed": 8, "coerced": 0, "failed": 0}
from unittest import mock                                       # noqa: E402
from core import world_consolidation as wc, study, competence, mood, book_feelings, memory_edges   # noqa: E402
from core.memory import store                                   # noqa: E402
wc._LOG = TMP / "world_consolidation_log.jsonl"
_patches = [
    mock.patch.object(competence, "record_drill_accuracy", lambda *a, **k: None),
    mock.patch.object(book_feelings, "capstone", lambda *a, **k: None),
    mock.patch.object(store, "store_fragment", lambda *a, **k: "frag1"),
    mock.patch.object(store, "store_light_event", lambda *a, **k: None),
    mock.patch.object(study, "write_tablet", lambda *a, **k: None),
    mock.patch.object(memory_edges, "add_edge", lambda *a, **k: None),
    mock.patch.object(mood, "current_vec", lambda: None), mock.patch.object(mood, "current_valence", lambda: 0.0),
    mock.patch.object(mood, "current_felt", lambda: None),
    mock.patch.object(wc, "file_book_notes", lambda t, *a, **k: {"filed": 0}),
    mock.patch.object(study, "archive_book_note_files", lambda t, *a, **k: {"moved": 0, "dest": "x"}),
]
for _p in _patches:
    _p.start()
try:
    el.record("rec.txt", "Rec Book", "Rec essay", "An essay body. " * 20, 0.5, 0.5, "fb", source_ids=[])
finally:
    for _p in _patches:
        _p.stop()
rows = [json.loads(x) for x in el._LOG.read_text(encoding="utf-8").splitlines() if x.strip()] if el._LOG.exists() else []
check(bool(rows) and rows[-1].get("reduce", {}).get("batches") == 8, "the log row carries the reduce key: %s" % (rows[-1].get("reduce") if rows else "no row"))
check("Rec Book" not in el._REDUCES, "record() popped the parked stats")

print()
print("FAILED: %d" % len(FAILS) if FAILS else "ALL OK")
sys.exit(1 if FAILS else 0)

