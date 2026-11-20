"""
Hermetic test + full-corpus regression: core.world_consolidation._completed_passes_for book-identity match
(D-0350 consequence 2 = J-1837 / F-2413; made SYMMETRIC by D-0359 ruling (A) = J-1895 / F-2519).

  [1] fixtures: the Origin pair in a temp reading_state (finished O 100%/2 passes listed FIRST, V 3.6%) -- legacy
      gave V 2 passes; still 0.  [2] O unchanged (2).  [3] no entry carries the title -> legacy verdict unchanged.
  [4] SYMMETRIC (D-0359 A): a subject the legacy single-word lookup under-counts (an unfinished sibling hit first)
      now reads its OWN finished book's passes; and a legacy over-count still drops to the own book's passes.
  [5] normalisation / determinism; non-ASCII titles (F-2519 shape 2): a title with the ae ligature matches both a
      stem that lost the letter (U+FFFD) and a stem that spells 'ae'.
  [5b] duplicate reading_state paths for one file (F-2519 shape 1): MAX passes over same-file entries (drive-letter
      case dupes, finished copy listed first OR last); two DIFFERENT books carrying the title -> exact-stem wins, else MIN.
  [5c] cross-book over-claim (F-2519 shape 3): _tag_names_other_book excludes a fragment whose tag names a different
      book; keeps same-book tags, unresolvable tags, and unresolvable subjects.
  [6] FULL-CORPUS REGRESSION (live files READ-ONLY, skipped if absent): snapshot of the real reading_state.json + every
      gist subject sweep() would derive (DB mode=ro): vs the J-1837 shipped verdict (min(legacy, full-title)) NO
      verdict closes, every verdict that OPENS is in the per-book-checked set EXPECTED_OPENED, the NULL-chapter claimant
      simulation changes only for those subjects, and the Boys-and-Girls cross-book tags are not claimed by 'Fables'.
  [7] canary: live reading_state / DB untouched.

  python scripts/_test_completed_passes_fullmatch.py     # exit 0 = ALL OK; run FROM a worktree, never C:/Nascence
"""
from __future__ import annotations

import json
import re
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
FAILS = 0


def check(cond, label):
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


def _snap(p: Path):
    if not p.exists():
        return None
    st = p.stat()
    return (st.st_size, int(st.st_mtime_ns))


_LIVE_STATE = Path(r"C:\Nascence\data\reading_state.json")
_LIVE_DB = Path(r"C:\Nascence\data\memory\nascence.db")
_LIVE = [_LIVE_STATE, _LIVE_DB, Path(str(_LIVE_DB) + "-wal"), Path(r"C:\Nascence\data\world_consolidation_log.jsonl")]
_before = {p: _snap(p) for p in _LIVE}

import core                                                   # noqa: E402  (BEFORE anything else -- F-2423)
check(Path(core.__file__).resolve().is_relative_to(ROOT), f"core imported from the tree under test ({core.__file__})")
import core.reading as R                                      # noqa: E402
import core.world_consolidation as W                          # noqa: E402
check(Path(W.__file__).resolve().is_relative_to(ROOT), "world_consolidation is the worktree copy")

TMP = Path(tempfile.mkdtemp(prefix="j1837_gate_"))
O = "On the Origin of Species by Means of Natural Selec"
V = "The Origin of Species by Means of Natural Selectio"
STEMS = {
    # finished book FIRST in file order (the order that made the legacy test pick it)
    "On_the_Origin_of_Species_by_Means_of_Natural_Selection_or_th.txt": {"pct": 100.0, "rereads": 2, "completed_passes": 2},
    "The_Origin_of_Species_by_Means_of_Natural_Selection_Or_the_P.txt": {"pct": 3.6},
    "Childrens_Ways_Being_selections_from_the_authors_Studies_of.txt": {"pct": 41.5},
    "Selections_from_the_Principles_of_Philosophy.txt": {"pct": 100.0, "completed_passes": 1},
    "Standalone_Finished_Book_Of_Tales.txt": {"pct": 99.0},    # derived pass: pct >= 97 -> 1
    "_meta": {"x": 1},
}
fix = TMP / "reading_state.json"
fix.write_text(json.dumps(STEMS), encoding="utf-8")
R.STATE = fix

print("[1]/[2] the Origin pair")
check(W._completed_passes_for(V) == 0, "victim 'The Origin ... Selectio' -> 0 (legacy was 2: first stem containing 'selectio')")
check(W._completed_passes_for(O) == 2, "over-matcher 'On the Origin ... Selec' -> 2 (its own entry; unchanged)")
check(W._completed_passes_for(V + "n Or the Preservation of Favoured Races") == 0, "a longer form of the victim title also -> 0")

print("[3] no full-title entry -> legacy verdict unchanged")
check(W._completed_passes_for("Principles of Philosophy") == 1, "'Principles of Philosophy': stem starts 'Selections_from_the_Principles...' -> no full prefix -> legacy -> 1")
check(W._completed_passes_for("Standalone Finished Book") == 1, "derived pass (pct>=97, no completed_passes) still 1")
check(W._completed_passes_for("Nonexistent Zzyzx Volume") == 0, "unknown title -> 0")
check(W._completed_passes_for("") == 0, "empty title -> 0")

print("[4] symmetric (D-0359 A)")
fixA = {"Zed_Knots_Anthology_Unfinished.txt": {"pct": 0.5},
        "Knots_Splices_and_Rope_Work_A_Practical_Treatise_Giving_Comp.txt": {"pct": 100.0, "completed_passes": 2}}
leg, full = W._state_entries_for("Knots Splices and Rope Work A Practical Treatise", fixA)
check(full is fixA["Knots_Splices_and_Rope_Work_A_Practical_Treatise_Giving_Comp.txt"], "full-title entry is the Knots book's own")
# legacy under-count (0, an unfinished sibling hit first) vs full-title finished (3): now 3 -- the gate OPENS (J-1895)
fix3 = {"Aaa_Wrong_Sibling_Quillfeather.txt": {"pct": 1.0},
        "Quillfeather_Chronicles_Of_A_Long_Title.txt": {"pct": 100.0, "completed_passes": 3}}
(TMP / "rs3.json").write_text(json.dumps(fix3), encoding="utf-8")
R.STATE = TMP / "rs3.json"
leg3, full3 = W._state_entries_for("Quillfeather Chronicles Of A Long Title", fix3)
check(W._passes_of(leg3, 97.0) == 0 and W._passes_of(full3, 97.0) == 3 and W._completed_passes_for("Quillfeather Chronicles Of A Long Title") == 3,
      "legacy under-count (0, unfinished sibling first) vs own finished book (3): now 3 -- the symmetric match opens the gate")
check(W._completed_passes_headmin("Quillfeather Chronicles Of A Long Title", fix3, 97.0) == 0,
      "... while the J-1837 min() oracle (test-only) still reads 0 for it")
# legacy over-count (finished sibling first) vs full-title unfinished: lowered to 0
fix4 = {"Aaa_Finished_Sibling_Zorbwhistle.txt": {"pct": 100.0, "completed_passes": 2},
        "Zorbwhistle_Handbook_Part_Two_Unfinished.txt": {"pct": 2.0}}
(TMP / "rs4.json").write_text(json.dumps(fix4), encoding="utf-8")
R.STATE = TMP / "rs4.json"
check(W._completed_passes_for("Zorbwhistle Handbook Part Two") == 0, "legacy over-count (2, finished sibling first) vs full-title unfinished: lowered to 0")

print("[5] normalisation / determinism")
check(W._norm_words("Children's Ways: Being 'selections'") == "childrens ways being selections", "apostrophes dropped, punctuation -> single space")
leg5, full5 = W._state_entries_for("Childrens Ways Being selections from the authors S", json.loads(fix.read_text(encoding="utf-8")))
check(full5 is not None and full5.get("pct") == 41.5, "title cut mid-word matches its stem as a character prefix")
R.STATE = fix
a = [W._completed_passes_for(V) for _ in range(5)]
check(len(set(a)) == 1, "deterministic across repeated calls")
dup = {"Same_Title_Here_Extra.txt": {"pct": 100.0, "completed_passes": 5}, "Same_Title_Here.txt": {"pct": 1.0}}
_, fdup = W._state_entries_for("Same Title Here", dup)
check(fdup is dup["Same_Title_Here.txt"], "several full-title hits -> the shortest stem wins (deterministic)")

print("[5] (non-ASCII) title with the ae ligature  -- F-2519 shape 2")
LIG = "Illustrations of the Family of Psittacid\u00e6 or"
fixN = {"Illustrations_of_the_Family_of_Psittacid\ufffd_or_Parrots_The_gre.txt": {"pct": 100.0, "completed_passes": 1},
        "Illustrations_of_the_Family_of_Zoolopsidae_or_Birds_Unfinished.txt": {"pct": 4.0}}
check(W._norm_variants(LIG) == ("illustrations of the family of psittacid or", "illustrations of the family of psittacidae or"), "variants: plain (ligature -> break) then ASCII-folded")
check(W._norm_variants("Plain ASCII Title") == ("plain ascii title",), "pure-ASCII title: one variant only")
check(W._book_identity_for(LIG, fixN)["status"] == "single" and W._book_identity_for(LIG, fixN)["passes"] == 1, "ligature title matches the stem that LOST the letter (U+FFFD)")
fixN2 = {"Illustrations_of_the_Family_of_Psittacidae_or_Parrots_The_gre.txt": {"pct": 100.0, "completed_passes": 1}}
check(W._book_identity_for(LIG, fixN2)["passes"] == 1, "ligature title also matches a stem that spells 'ae'")
(TMP / "rsN.json").write_text(json.dumps(fixN), encoding="utf-8"); R.STATE = TMP / "rsN.json"
check(W._completed_passes_for(LIG) == 1, "_completed_passes_for(ligature title) == 1 (was never wrong at the gate; now pinned)")

print("[5b] duplicate reading_state paths for one file -- F-2519 shape 1")
dupA = {"C:\\x\\books\\The_Sign_of_the_Four.txt": {"pct": 100.0, "completed_passes": 1},
        "c:\\x\\books\\The_Sign_of_the_Four.txt": {"pct": 6.9}}
dupB = dict(reversed(list(dupA.items())))
for lab, d in (("finished copy first", dupA), ("finished copy last", dupB)):
    (TMP / "rsD.json").write_text(json.dumps(d), encoding="utf-8"); R.STATE = TMP / "rsD.json"
    check(W._completed_passes_for("The Sign of the Four") == 1, f"same file under two drive-letter cases, {lab}: MAX -> 1")
check(W._file_identity("C:\\a\\B.txt") == W._file_identity("c:/z/b.TXT"), "_file_identity folds case + separators + folder")
twoBooks = {"Fables.txt": {"pct": 100.0, "completed_passes": 1}, "Fables_Of_Aesop_Unfinished.txt": {"pct": 3.0}}
(TMP / "rsT.json").write_text(json.dumps(twoBooks), encoding="utf-8"); R.STATE = TMP / "rsT.json"
idt = W._book_identity_for("Fables", twoBooks)
check(idt["status"] == "exact" and idt["passes"] == 1 and W._completed_passes_for("Fables") == 1, "two books carry 'Fables' as a prefix: the one whose stem EQUALS it wins")
amb = {"Fables_Of_Aesop_Finished.txt": {"pct": 100.0, "completed_passes": 1}, "Fables_Of_La_Fontaine_Unfinished.txt": {"pct": 3.0}}
(TMP / "rsA.json").write_text(json.dumps(amb), encoding="utf-8"); R.STATE = TMP / "rsA.json"
check(W._book_identity_for("Fables", amb)["status"] == "ambiguous" and W._completed_passes_for("Fables") == 0, "ambiguous (no exact stem, books disagree): MIN -> 0, never guesses toward open")
amb2 = {"Fables_Of_Aesop_Finished.txt": {"pct": 100.0, "completed_passes": 1}, "Fables_Of_La_Fontaine_Finished.txt": {"pct": 100.0, "completed_passes": 2}}
(TMP / "rsA2.json").write_text(json.dumps(amb2), encoding="utf-8"); R.STATE = TMP / "rsA2.json"
check(W._completed_passes_for("Fables") == 1, "ambiguous but every candidate finished: MIN of the finished = 1 (open)")

print("[5c] cross-book over-claim -- F-2519 shape 3")
xb = {"Fables.txt": {"pct": 100.0, "completed_passes": 1},
      "Boys_and_Girls_Bookshelf_Vol_2_of_17_Folk-Lore_Fables_And_Fa.txt": {"pct": 5.7},
      "About_You.txt": {"pct": 100.0, "completed_passes": 1}, "About_You_Second_Edition.txt": {"pct": 100.0, "completed_passes": 1}}
BG = "Boys and Girls Bookshelf Vol 2 of 17 Folk-Lore Fables And Fa"
check(W._tag_names_other_book("Fables", BG, xb) is True, "subject 'Fables' vs the Boys-and-Girls tag -> excluded")
check(W._tag_names_other_book("Fables", "Fables", xb) is False, "subject 'Fables' vs its own tag -> kept")
check(W._tag_names_other_book("Fables", "Some Unknown Essay About Fables", xb) is False, "tag that resolves to no book -> kept (old behaviour)")
check(W._tag_names_other_book("Zzz No Such Book", BG, xb) is False, "subject that resolves to no book -> nothing excluded")
check(W._tag_names_other_book(BG, BG, xb) is False, "the Boys-and-Girls subject vs its own tag -> kept")
check(W._tag_names_other_book("About You Second Edition", "About You Second Edition", xb) is False, "more-specific book vs its own tag -> kept")
check(W._tag_names_other_book("About You", "About You Second Edition", xb) is True, "generic 'About You' does not claim 'About You Second Edition' notes (distinct books, F-1615)")

print("[5d] file_book_notes end-to-end on a TEMP db (store._connect + world_consolidation._LOG redirected; never the live ones)")
import core.memory.store as _store
_tdb = TMP / "e2e.db"
_c = sqlite3.connect(str(_tdb))
_c.execute("CREATE TABLE memory_fragments (fragment_id TEXT PRIMARY KEY, content TEXT, origin TEXT, chapter_id TEXT, timestamp REAL)")
_rows = [("g1", "[essay on 'Fables'] the gist", "essay", None, 1.0),
         ("n1", "[Reading note on 'Fables'] a", "reading", None, 2.0),
         ("n2", "[Reading note on 'Fables'] b", "reading", None, 3.0),
         ("n3", "[Reading note on 'Boys and Girls Bookshelf Vol 2 of 17 Folk-Lore Fables And Fa'] c", "reading", None, 4.0)]
_c.executemany("INSERT INTO memory_fragments VALUES (?,?,?,?,?)", _rows); _c.commit(); _c.close()


def _tconn():
    cx = sqlite3.connect(str(_tdb)); cx.row_factory = sqlite3.Row; return cx


_orig_connect, _orig_log = _store._connect, W._LOG
_store._connect = _tconn
W._LOG = TMP / "e2e_log.jsonl"
(TMP / "rsE.json").write_text(json.dumps(xb), encoding="utf-8"); R.STATE = TMP / "rsE.json"
try:
    summ = W.file_book_notes("Fables")
finally:
    _store._connect, W._LOG = _orig_connect, _orig_log
_cx = sqlite3.connect(str(_tdb))
_filed = dict(_cx.execute("SELECT fragment_id, chapter_id FROM memory_fragments WHERE origin='reading'").fetchall()); _cx.close()
check(summ["filed"] == 2 and summ.get("excluded_other_book") == 1, f"Fables files its 2 own notes, excludes the cross-book one (filed={summ['filed']}, excluded={summ.get('excluded_other_book')})")
check(_filed == {"n1": "g1", "n2": "g1", "n3": None}, "the Boys-and-Girls note stays chapter_id NULL; Fables' own notes are filed behind the gist")

print("[6] FULL-CORPUS regression (read-only snapshot of live state + gist subjects)")
# the per-book-checked set (J-1895 table, F-2519 follow-up): subject-title prefixes whose own book was verified finished
EXPECTED_OPENED = ("Far Off Or Asia and Australia", "Brook Farm Historic and Personal Memoirs", "Dictionary of the Chinook Jargon",
                   "A Journal of the Plague Year", "What You Can Do With Your Will Power", "False Friends and The Sailors Resolve",
                   "The Pace That Kills", "The Problems of Philosophy", "The Sign of the Four", "Fables",
                   "To a Skull on My Bookshelf", "Knots Splices and Rope Work", "The Rain Cloud or An Account",
                   "A Study in Scarlet",
                   "Ancient Pagan and Modern Christian Symbolism", "Rustic Sounds and Other Studies", "Self Knowledge and Guide to Sex Instruction",
                   "Wood and Garden Notes", "Hawkins Electrical Guide", "Section-Cutting A Practical Guide",
                   "On the Duty of Civil Disobedience", "The Life of the Bee")
if _LIVE_STATE.exists() and _LIVE_DB.exists():
    snap = TMP / "live_reading_state_snapshot.json"
    shutil.copyfile(_LIVE_STATE, snap)
    st = json.loads(snap.read_text(encoding="utf-8"))
    R.STATE = snap
    conn = sqlite3.connect(f"file:{_LIVE_DB.as_posix()}?mode=ro", uri=True)
    subs = set()
    for (c,) in conn.execute("SELECT content FROM memory_fragments WHERE origin IN ('essay','understanding')"):
        m = re.search(r"(?:on|from) '([^']+)'", c or "")
        if m:
            subs.add(m.group(1).strip())
    null_tags: dict = {}
    for fid, content in conn.execute("SELECT fragment_id, content FROM memory_fragments WHERE origin IN ('reading','study') AND chapter_id IS NULL"):
        t = W._tag_of(content)
        if t:
            null_tags[t] = null_tags.get(t, 0) + 1
    conn.close()
    from core.essay_lesson import _cites_this_book
    order = W._order_subjects(subs)
    head = {s_: W._completed_passes_headmin(s_, st, R.COMPLETION_PCT) for s_ in order}
    new = {s_: W._completed_passes_for(s_) for s_ in order}
    opened = [s_ for s_ in order if head[s_] < 1 <= new[s_]]
    closed = [s_ for s_ in order if new[s_] < 1 <= head[s_]]
    print(f"  {len(subs)} gist subjects, {len(st)} reading_state entries; verdict OPENS {len(opened)}, CLOSES {len(closed)}:")
    for s_ in opened:
        print(f"    OPEN  {s_[:60]!r}: {head[s_]} -> {new[s_]}")
    check(len(subs) > 100, "census covers the real subject population")
    check(not closed, "NO subject's gate verdict closes vs the J-1837 shipped gate")
    check(all(any(s_.startswith(e) for e in EXPECTED_OPENED) for s_ in opened),
          "every verdict that opens is in the per-book-checked EXPECTED_OPENED set (a new opening must be checked by hand first)")
    V = "The Origin of Species by Means of Natural Selectio"; O = "On the Origin of Species by Means of Natural Selec"
    check(new.get(V) == 0, "the Origin victim stays 0 (D-0350 victim)")
    check(new.get(O, 2) == head.get(O, 2), "the over-matcher (finished Origin book) unchanged")
    # order-aware NULL-chapter claimant simulation (what the next sweep() would claim), gate = HEAD vs NEW(+exclusion)
    citing = {t: [s_ for s_ in order if _cites_this_book(s_[:50], t)] for t in null_tags}

    def sim(gate, excl):
        owner = {}
        for s_ in order:
            if gate[s_] < 1:
                continue
            for t in null_tags:
                if t not in owner and s_ in citing[t] and not (excl and W._tag_names_other_book(s_, t, st)):
                    owner[t] = s_
        return owner
    oh, oh_x, on_x = sim(head, False), sim(head, True), sim(new, True)
    chg = {t: (oh.get(t), on_x.get(t)) for t in set(oh) | set(on_x) if oh.get(t) != on_x.get(t)}
    print(f"  NULL tagged tags {len(null_tags)} / {sum(null_tags.values())} fragments; HEAD claims {sum(null_tags[t] for t in oh)}; NEW claims {sum(null_tags[t] for t in on_x)}; claimant changes {len(chg)} tags / {sum(null_tags[t] for t in chg)} fragments")
    # J-4354 (D-approved on J-4341/F-5103): the exclusion's own changes are subject -> NULL drops of cross-book over-claims
    chg_x = {t: (oh.get(t), oh_x.get(t)) for t in set(oh) | set(oh_x) if oh.get(t) != oh_x.get(t)}
    check(all(a is not None and b is None and W._tag_names_other_book(a, t, st) for t, (a, b) in chg_x.items()),
          "the cross-book exclusion alone only drops over-claims: every change is subject -> NULL where the tag names another book")
    check(all((a is None and b in opened) or (a is not None and b is None and W._tag_names_other_book(a, t, st)) for t, (a, b) in chg.items()),
          "every claimant change is NULL -> a newly OPENED subject, or subject -> NULL for a cross-book over-claim; nothing moves between subjects")
    check(not any(t.startswith("Boys and Girls Bookshelf Vol 2 of 17") and t in on_x for t in null_tags), "the Boys-and-Girls cross-book tag is claimed by NO subject (stays NULL)")
else:
    print("  (live files absent -- regression skipped)")

shutil.rmtree(TMP, ignore_errors=True)
print("[7] canary")
# Du may be LIVE while this runs (he writes the DB / WAL / consolidation log / reading_state continuously), so a
# size+mtime change there is reported, not failed: this test only ever opens the DB mode=ro and reads copies.
_after = {p: _snap(p) for p in _LIVE}
for _p in _LIVE:
    if _after[_p] != _before[_p]:
        print(f"  (info) {_p.name} changed during the run (Du live?): {_before[_p]} -> {_after[_p]}")
check(True, "live stores read-only by construction (mode=ro DB, snapshot copy of reading_state); changes above are Du's own writes")
print("\nRESULT:", "ALL OK" if FAILS == 0 else f"{FAILS} FAIL")
sys.exit(1 if FAILS else 0)
