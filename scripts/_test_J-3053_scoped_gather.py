"""J-3053 / F-3762: essay_lesson.gather_notes selects a book's DB 'understanding' rows and its deep-recall gists
by the book's TAG (and by what a gist was distilled from), not by `content LIKE '%<commonest title word>%'`.

Temp sqlite DB + temp study dirs only; no model, no live data. Run from the worktree:
    python scripts/_test_J-3053_scoped_gather.py
"""
from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import core                                    # noqa: E402  (before anything that could resolve to C:\Nascence)
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
from core import essay_lesson as el            # noqa: E402
import core.memory.store as store              # noqa: E402

FAILS: list[str] = []


def check(cond, msg):
    print(("  ok:   " if cond else "  FAIL: ") + msg)
    if not cond:
        FAILS.append(msg)


TITLE = "One Young Man The simple and true story of a clerk who enlis"      # a 60-char file stem, as in live
OTHER = "The Brothers Karamazov"
DASH = "\u2014"

# ── the tag test ────────────────────────────────────────────────────────────────────────────────────────────
print("tag test")
check(el._tag_is_this_book(TITLE, TITLE), "whole title matches")
check(el._tag_is_this_book(TITLE, "One Young Man The simple and true story of a clerk"), "tag cut at 50 matches")
check(el._tag_is_this_book(TITLE, "One Young Man The simple and true story of a"), "tag smart-cut earlier (drops 'clerk') matches")
check(el._tag_is_this_book(TITLE, "One Young Man The simple and true story of a cle"), "tag cut mid-word matches")
check(not el._tag_is_this_book(TITLE, "The Simple Life"), "another title sharing the key word 'simple' does not")
check(not el._tag_is_this_book(TITLE, ""), "no tag is never this book's")
check(not el._tag_is_this_book("The Birds", "The Birds of America"), "a short title does not prefix-match a longer one")
check(el._tag_is_this_book("The Birds", "The Birds"), "a short title matches itself")
check(el._tag_is_this_book("Childrens Ways Their Growth And Education Of The Young Mind", "Children"+chr(0x2019)+"s Ways Their Growth And Education Of The Young Mind"), "an apostrophe in the tag still matches the file-stem form")

# ── a temp DB shaped like the live one ──────────────────────────────────────────────────────────────────────
tmp = Path(tempfile.mkdtemp(prefix="J-3053_"))
DB = tmp / "n.db"
conn0 = sqlite3.connect(str(DB))
conn0.executescript("""
CREATE TABLE memory_fragments (fragment_id TEXT PRIMARY KEY, content TEXT, origin TEXT, timestamp REAL, temp TEXT, embedding BLOB);
CREATE TABLE memory_links (parent_id TEXT, child_id TEXT, link_type TEXT, weight REAL);
""")
_ts = [0.0]


def frag(fid, origin, content, temp="warm"):
    _ts[0] += 1.0
    conn0.execute("INSERT INTO memory_fragments VALUES (?,?,?,?,?,NULL)", (fid, content, origin, _ts[0], temp))


def link(p, c):
    conn0.execute("INSERT INTO memory_links VALUES (?,?,?,0.5)", (p, c, "distilled_from"))


# understanding rows: two of this book (one smart-cut tag, one hidden), foreign ones that merely say 'simple'
frag("u-own1", "understanding", "[Understanding %s from 'One Young Man The simple and true story of a'] OWN-U1 the clerk enlists." % DASH)
frag("u-own2", "understanding", "[Understanding %s from 'One Young Man The simple and true story of a clerk'] OWN-U2 trench life." % DASH)
frag("u-hid", "understanding", "[Understanding %s from 'One Young Man The simple and true story of a clerk'] HIDDEN dict repr" % DASH, temp="hidden")
frag("u-for1", "understanding", "[Understanding %s from '%s'] FOREIGN-U1 a simple faith." % (DASH, OTHER))
frag("u-for2", "understanding", "[Understanding %s from 'The Simple Life'] FOREIGN-U2 simple living." % DASH)
frag("u-for3", "understanding", "[Understanding %s a principle I hold] FOREIGN-U3 simple rules." % DASH)
# gists: g-own (children mostly this book's reading), g-mixed (mostly inner thoughts), g-foreign (another book's)
frag("g-own", "gist", "[gist %s semantic] the clerk's enlistment in brief." % DASH)
frag("g-mixed", "gist", "[gist %s self] a simple pattern of days." % DASH)
frag("g-for", "gist", "[gist %s semantic] a simple faith." % DASH)
N_OWN_KIDS = 30
for i in range(N_OWN_KIDS):
    frag("r-own%02d" % i, "reading", "[From '%s'] OWN-R%02d passage text." % (TITLE, i))
    link("g-own", "r-own%02d" % i)
frag("t-in", "inner_thought", "FOREIGN-IT thought without a tag.")
link("g-own", "t-in")                                     # 30 own of 31 -> still this book's gist
frag("r-m1", "reading", "[From '%s'] OWN-RM1 one own child." % TITLE)
link("g-mixed", "r-m1")
for i in range(4):
    frag("t-m%d" % i, "inner_thought", "FOREIGN-IT-M%d untagged." % i)
    link("g-mixed", "t-m%d" % i)                          # 1 own of 5 -> not this book's gist
for i in range(3):
    frag("r-for%d" % i, "reading", "[From '%s'] FOREIGN-R%d." % (OTHER, i))
    link("g-for", "r-for%d" % i)
conn0.commit()
conn0.close()


def _connect():
    c = sqlite3.connect(str(DB), check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


empty = tmp / "study"
empty.mkdir()
fake_rh = mock.Mock()
fake_rh.book_stats = lambda b: {"rereads": 0}


def gather(scoped: bool):
    el.SCOPED_GATHER = scoped
    with mock.patch.object(store, "_connect", _connect), mock.patch.object(store, "_embed", lambda *a, **k: None), \
            mock.patch("core.study.STUDY_DIR", empty), mock.patch("core.study.NOTES_SUBDIR", tmp / "none"), \
            mock.patch("core.reading_history.book_stats", fake_rh.book_stats), \
            mock.patch("core.recall_demand.note", lambda *a, **k: None), \
            mock.patch("core.memory_edges.log_co_recall", lambda *a, **k: None):
        return el.gather_notes(TITLE, "C:/x/One_Young_Man.txt")


print("understanding + gist scoping (SCOPED_GATHER on)")
txt, ids = gather(True)
check("OWN-U1" in txt and "OWN-U2" in txt, "both of the book's own understanding rows are in")
check("HIDDEN" not in txt, "a temp='hidden' understanding row is still skipped")
check("FOREIGN-U1" not in txt and "FOREIGN-U2" not in txt and "FOREIGN-U3" not in txt, "no foreign understanding row")
check("FOREIGN-IT" not in txt and "FOREIGN-R" not in txt, "no foreign gist child (inner thought / other book)")
check("g-mixed" not in ids and "g-for" not in ids, "gist ids are never the lineage themselves")
kids = [i for i in ids if i.startswith("r-own")]
check(len(kids) == el._GIST_CHILD_CAP, "own gist children are capped at _GIST_CHILD_CAP (%d of %d)" % (len(kids), N_OWN_KIDS))
check("r-m1" not in ids, "the child of a mostly-inner-thought gist is not pulled in")
check(len(ids) == 2 + el._GIST_CHILD_CAP, "the whole lineage is own-book: %d ids" % len(ids))

print("rollback (SCOPED_GATHER off) restores the old LIKE-on-key clauses")
txt0, ids0 = gather(False)
check("FOREIGN-U1" in txt0 and "FOREIGN-U2" in txt0, "old path picks the foreign understanding rows on the word 'simple'")
check("g-for" not in ids0 and any(i.startswith("r-for") for i in ids0), "old path descends the foreign gist")
el.SCOPED_GATHER = True

print("helper: gist ids")
with _connect() as c:
    gids = el._book_gist_ids(c, TITLE)
check(gids == ["g-own"], "only the gist distilled mostly from this book's reading: %s" % gids)

print("py_compile-level: constants")
check(el.SCOPED_GATHER is True, "default is on")

print("\nFAILS: %d" % len(FAILS))
for f in FAILS:
    print(" -", f)
sys.exit(1 if FAILS else 0)
