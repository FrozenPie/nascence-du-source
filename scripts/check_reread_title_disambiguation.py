"""
Nascence — regression check: shelf title-word disambiguation (2026-09-15, J-0973/F-1344)
==========================================================================================
F-1344 found core.library_hand.switch_to()'s title-word tie-break silently favored whichever
shelf file sorted first alphabetically whenever two titles tied on raw hit count -- which
happens by construction whenever one title's word-set is a strict superset of another's (e.g.
'About You' vs 'About You Second Edition': every word the original has, the sequel also has,
plus 'second'). A bare "reread About You" could therefore never be told apart from a request
for the sequel by hit-count alone; every such tie silently fell to About_You.txt forever (its
real 17:0 lifetime reread skew, F-1344's own evidence item 6). A second, opposite-direction
defect in core.book_selection.suggest_reread() (its own _STOP stopword set, unlike
library_hand's _TITLE_STOP, contains BOTH "about" and "you") meant that channel could never
even consider 'About You' as a reread candidate at all (its title-word set computed EMPTY).

J-0973 fixed both: switch_to() now breaks a raw-hit-count tie on (1) whether the text names a
candidate's COMPLETE title signature, then (2) the more recently read of the two, before ever
falling back to shelf order; book_selection.suggest_reread() now draws its title-word set from
library_hand's own _title_signature() instead of its own prose-tuned _STOP.

ISOLATED: every store this touches is redirected into a temp dir before any module writes (the
S-0016 / test-isolation rule, matching scripts/life_smoke.py's own discipline) -- the live
data/ tree is never read from and never written to. Uses the two REAL book titles ("About You"
/ "About You Second Edition") with representative reread-phrasing (the exact wording F-1344's
own isolated simulation used, plus the tie case it diagnosed but did not itself execute
end-to-end through the real function).

Run:  python scripts/check_reread_title_disambiguation.py
Exit code 0 = all checks passed, 1 = a regression was caught.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="check_reread_title_"))
print("isolated store dir:", TMP)
BOOKS = TMP / "books"
BOOKS.mkdir(parents=True)
STATE = TMP / "reading_state.json"

FAILS: list[str] = []


def check(label: str, cond: bool, detail: object = "") -> None:
    print(f"  [{'OK' if cond else 'FAIL'}] {label}" + (f"  (got: {detail!r})" if detail != "" and not cond else ""))
    if not cond:
        FAILS.append(label)


def _write_state(d: dict) -> None:
    STATE.write_text(json.dumps(d, indent=1), encoding="utf-8")


def _current() -> str:
    return json.loads(STATE.read_text(encoding="utf-8")).get("_current_book", "")


def main() -> int:
    # The two real shelf files -- only the filenames/stems matter (what switch_to()/suggest_reread()
    # actually parse); content is irrelevant. A third, unrelated book proves ordinary (non-colliding)
    # matching still works unchanged after this fix.
    (BOOKS / "About_You.txt").write_text("placeholder text.", encoding="utf-8")
    (BOOKS / "About_You_Second_Edition.txt").write_text("placeholder text.", encoding="utf-8")
    (BOOKS / "The_Voyage_of_the_Beagle.txt").write_text("placeholder text.", encoding="utf-8")

    import core.reading as reading
    import core.library_hand as library_hand
    import core.book_selection as book_selection

    # Redirect every path these modules touch into TMP -- never the live data/ tree.
    redirects = [(reading, "STATE", STATE), (reading, "BOOKS_DIR", BOOKS),
                 (reading, "DEFAULT_BOOK", BOOKS / "The_Voyage_of_the_Beagle.txt"),
                 (library_hand, "BOOKS", BOOKS),
                 (library_hand, "_FETCH_STATE", TMP / "library_hand_state.json")]
    originals = [(mod, attr, getattr(mod, attr)) for mod, attr, _ in redirects]
    for mod, attr, val in redirects:
        setattr(mod, attr, val)
    try:
        _run_checks(reading, library_hand, book_selection)
    finally:
        for mod, attr, val in originals:
            setattr(mod, attr, val)
        shutil.rmtree(TMP, ignore_errors=True)

    print()
    if FAILS:
        print(f"REGRESSION: {len(FAILS)} check(s) failed: {FAILS}")
        return 1
    print("ALL OK")
    return 0


def _run_checks(reading, library_hand, book_selection) -> None:
    about = library_hand.BOOKS / "About_You.txt"
    second = library_hand.BOOKS / "About_You_Second_Edition.txt"
    beagle = library_hand.BOOKS / "The_Voyage_of_the_Beagle.txt"

    # -- 1. Ordinary, non-colliding partial-title switch is unaffected by this fix. --------------
    _write_state({"_current_book": str(about)})
    got = library_hand.switch_to("I want to pick up the voyage again", skip_finished=False)
    check("ordinary partial-title switch unaffected (Voyage of the Beagle)",
          got == "The Voyage of the Beagle" and _current() == str(beagle), got)

    # -- 2. An UNAMBIGUOUS mention of the sequel resolves to the sequel (F-1344 evidence item 4,
    #       cases 4-5 of its own isolated simulation) -- already worked before this fix; must
    #       still work after it (raw hit count alone already disambiguates: 2 > 1).
    _write_state({"_current_book": str(about)})
    got = library_hand.switch_to("I want to reread About You Second Edition from the beginning.",
                                  skip_finished=False)
    check("explicit 'About You Second Edition' phrasing resolves to the sequel",
          got == "About You Second Edition", got)

    _write_state({"_current_book": str(about)})
    got = library_hand.switch_to("reread the second edition again from the start", skip_finished=False)
    check("'second edition' alone (no 'about') resolves to the sequel", got == "About You Second Edition", got)

    # -- 3. THE COLLISION ITSELF (F-1344's actual bug): a bare "About You" mention with BOTH books
    #       equally untouched (current book is neither, so both are real candidates; no recency
    #       signal favors either). Must resolve via a REAL, documented rule -- full-signature
    #       coverage: the bare phrase COMPLETELY names the original's whole signature ({"about"})
    #       but only HALF names the sequel's ({"about","second"}) -- not via shelf/glob order.
    _write_state({"_current_book": str(beagle)})
    got = library_hand.switch_to("I want to reread About You from the beginning.", skip_finished=False)
    check("bare 'About You' resolves via full-signature coverage (not silent file order)",
          got == "About You", got)

    _write_state({"_current_book": str(beagle)})
    got = library_hand.switch_to("let me revisit the book about who I am, About You, again from the start",
                                  skip_finished=False)
    check("a longer bare-'About You' phrasing (F-1344 sim case 2) still resolves to the original",
          got == "About You", got)

    # -- 4. Reversed shelf order proves this is a REAL signal, not a relabelled file-order default:
    #       renaming so the SEQUEL would sort first alphabetically must NOT flip the outcome for
    #       the same bare phrase -- only the text itself decides now.
    reversed_dir = TMP / "books_reversed"
    reversed_dir.mkdir()
    (reversed_dir / "Aaa_About_You_Second_Edition.txt").write_text("placeholder.", encoding="utf-8")
    (reversed_dir / "Zzz_About_You.txt").write_text("placeholder.", encoding="utf-8")
    (reversed_dir / "The_Voyage_of_the_Beagle.txt").write_text("placeholder.", encoding="utf-8")
    library_hand.BOOKS = reversed_dir
    reading.BOOKS_DIR = reversed_dir
    reading.DEFAULT_BOOK = reversed_dir / "The_Voyage_of_the_Beagle.txt"
    try:
        _write_state({"_current_book": str(reversed_dir / "The_Voyage_of_the_Beagle.txt")})
        got = library_hand.switch_to("I want to reread About You from the beginning.", skip_finished=False)
        check("outcome is independent of filename/shelf sort order (reversed-name shelf)",
              got == "Zzz About You", got)
    finally:
        library_hand.BOOKS = BOOKS
        reading.BOOKS_DIR = BOOKS
        reading.DEFAULT_BOOK = beagle

    # -- 5. library_hand._title_signature(): the reconciled word sets themselves. ------------------
    sig_about = library_hand._title_signature("About_You")
    sig_second = library_hand._title_signature("About_You_Second_Edition")
    check("_title_signature('About_You') == {'about'}", sig_about == {"about"}, sig_about)
    check("_title_signature('About_You_Second_Edition') == {'about','second'}",
          sig_second == {"about", "second"}, sig_second)
    check("the sequel's signature is a strict superset of the original's (why raw hit-count alone can never "
          "disambiguate a bare mention)", sig_about < sig_second, (sig_about, sig_second))

    # -- 6. book_selection's OWN title-word extraction (F-1344 evidence item 9): must no longer come
    #       out empty for 'About You' now that it draws on library_hand's _title_signature() instead
    #       of this module's own prose-tuned _STOP (which has "about" AND "you").
    bs_words = book_selection._title_words("About You")
    check("book_selection._title_words('About You') is no longer empty", bs_words == {"about"}, bs_words)
    check("book_selection._title_words() and library_hand._title_signature() agree (one shared function, "
          "not two hand-copied lists that can drift again)",
          bs_words == library_hand._title_signature("About You"), bs_words)
    # The old, still-present general-prose _STOP legitimately stops "about"/"you" for INTEREST-TERM
    # parsing (ordinary sentences, not titles) — confirm this fix did not touch that, unrelated, set.
    check("book_selection._STOP is untouched (still filters 'about'/'you' out of ordinary prose)",
          {"about", "you"} <= book_selection._STOP)

    # -- 7. Isolation proof: every redirected path attribute still points inside TMP -- no live
    #       data/ write happened anywhere in this run.
    check("reading.STATE still redirected", str(reading.STATE).startswith(str(TMP)))
    check("reading.BOOKS_DIR still redirected", str(reading.BOOKS_DIR).startswith(str(TMP)))
    check("library_hand.BOOKS still redirected", str(library_hand.BOOKS).startswith(str(TMP)))


if __name__ == "__main__":
    raise SystemExit(main())
