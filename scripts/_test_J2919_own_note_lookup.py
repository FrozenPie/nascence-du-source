"""J-2919 test: study_note's "this book's own notes" lookup (F-3589). Temp DB and temp note files only; no live data.

Run from the worktree:  python scripts/_test_J2919_own_note_lookup.py
"""
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (before lab_env)
from core import study_note as sn  # noqa: E402

assert Path(sn.__file__).resolve().parent.parent == ROOT, "tested the wrong tree"


def frag(title, book, subj="x"):
    return f"[My study note: '{title}' · on '{book[:50]}' · subject: {subj}] I see something."


def main():
    # 1. the tag reader, incl. an apostrophe in the book title and a non-study leading tag
    assert sn._note_book_tag(frag("T", "Children's Ways: a study")) == "Children's Ways: a study"
    assert sn._note_book_tag("[Understanding - from 'The Birds of America'] text") in ("The Birds of America", "")

    # 2. one-word-key books must not claim each other's notes
    sci = "Popular Scientific Lectures"
    other = "Scientific Papers of Lord Rayleigh"
    assert sn._is_own_note(sci, frag("a", sci)) is True
    assert sn._is_own_note(sci, frag("a", other)) is False
    exp = "The Varieties of Religious Experience"
    assert sn._is_own_note(exp, frag("a", "Experience and Nature")) is False
    assert sn._is_own_note(exp, frag("a", exp)) is True
    assert sn._is_own_note("Children's Ways: a study", frag("a", "Children's Ways: a study")) is True
    # a title cut at 50 characters by the writer still matches the full title
    longt = "Leibniz New Essays Concerning the Human Understanding and more words"
    assert sn._is_own_note(longt, frag("a", longt)) is True
    # a one-word-signature title ('World') claims only its own tag, not every tag holding the word
    assert sn._is_own_note("The World of Ice", frag("a", "The World as Will and Idea Vol 3 of 3")) is False
    assert sn._is_own_note("The World of Ice", frag("a", "The World of Ice")) is True
    assert sn._is_own_note("On War  Volume 1", frag("a", "Some Other Volume 2")) is False
    # no tag and no file -> None (unknown), not True
    assert sn._is_own_note(sci, "[My study note: 'only a note title'] body") is None

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        # 3. an old header-less tablet: book read from the note FILE's "on:" line
        f_old = td / "TAB_old.md"
        f_old.write_text(f"# t\n\n*A study note by x · 2026-01-01 00:00 · on: {sci} · subject: s*\n\nbody\n",
                         encoding="utf-8")
        f_oth = td / "TAB_oth.md"
        f_oth.write_text(f"# t\n\n*A study note by x · 2026-01-01 00:00 · on: {other} · subject: s*\n\nbody\n",
                         encoding="utf-8")
        assert sn._is_own_note(sci, "[My study note: 'old'] b", str(f_old)) is True
        assert sn._is_own_note(sci, "[My study note: 'old'] b", str(f_oth)) is False
        # file-read budget is honoured
        assert sn._is_own_note(sci, "[My study note: 'old'] b", str(f_old), [0]) is None

        # 4. _own_note_fragment_ids over a temp DB (newest first, exclude_id honoured, other books ignored)
        db = td / "t.db"
        conn = sqlite3.connect(str(db))
        conn.row_factory = sqlite3.Row
        conn.execute("CREATE TABLE memory_fragments (fragment_id TEXT, content TEXT, source_id TEXT, origin TEXT, "
                     "timestamp REAL, embedding BLOB)")
        rows = [("a1", frag("n1", sci), "", "study", 1.0), ("a2", frag("n2", other), "", "study", 2.0),
                ("a3", frag("n3", sci), "", "study", 3.0), ("a4", "[My study note: 'old'] b", str(f_old), "study", 0.5),
                ("a5", frag("n5", other), "", "essay", 9.0)]
        for r in rows:
            conn.execute("INSERT INTO memory_fragments VALUES (?,?,?,?,?,NULL)", r)
        assert sn._own_note_fragment_ids(sci, conn) == ["a3", "a1", "a4"], sn._own_note_fragment_ids(sci, conn)
        assert sn._own_note_fragment_ids(sci, conn, exclude_id="a3", limit=1) == ["a1"]
        assert sn._own_note_fragment_ids(other, conn) == ["a2"]      # the essay row is not a study note
        # the OLD one-word LIKE would have matched the other book for the key 'scientific'
        old = [r["fragment_id"] for r in conn.execute(
            "SELECT fragment_id FROM memory_fragments WHERE origin='study' AND content LIKE '%Scientific%'")]
        assert "a2" in old
        conn.close()
    # fail-open
    assert sn._own_note_fragment_ids("anything", conn=object()) == []
    print("ok: J-2919 own-note lookup")


if __name__ == "__main__":
    main()
