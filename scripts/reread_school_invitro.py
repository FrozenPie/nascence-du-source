"""In-vitro for Move 7 (reread-when-helpful) + Move 8 (school auto-extend / spiral). Monkeypatched —
no network, no live school.json or reading_state touched."""
import sys, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import book_selection as bs, reading_history as rh
from core import school

# ---- Move 7: suggest_reread ----------------------------------------------------------------
read = rh.read_paths()
assert read, "no finished books in reading_state to test against"
target = read[0]                                   # e.g. a finished book
# J-0973/F-1344: suggest_reread() now extracts a candidate's title words via bs._title_words()
# (reconciled with core.library_hand's own title-word stoplist, _TITLE_STOP), not this module's
# prose-tuned _words()/_STOP any more (that mismatch was the actual bug — a real title like
# 'About You' computed an EMPTY word set under _STOP, since _STOP treats "about"/"you" as noise).
# Seeding pick_term via the old _words() here could pick a word (e.g. "story"/"book"/"life", all
# in _TITLE_STOP but none in _STOP) that _title_words() itself now filters as title-boilerplate —
# unfindable in ANY real title, which would spuriously fail this assertion with no real product
# regression behind it. Match the real mechanism on both sides.
tterms = bs._title_words(Path(target).stem.replace("_", " "))
pick_term = next(iter(tterms))                     # a real word from its title

_orig_interest = bs._interest_terms
bs._interest_terms = lambda: {pick_term}           # pretend his concern shares a word with this book
try:
    rr = bs.suggest_reread(min_gap_days=0.0)
    assert rr and pick_term in bs._title_words(rr["title"]), f"suggest_reread missed the relevant book: {rr}"
    print(f"[7a] suggest_reread OK — interest '{pick_term}' → returns '{rr['title'][:45]}'")
    # gate: if interest is empty, no suggestion
    bs._interest_terms = lambda: set()
    assert bs.suggest_reread() is None, "suggest_reread should be silent with no interest"
    print("[7b] gate OK — no interest → no reread invitation (reread stays the earned exception)")
finally:
    bs._interest_terms = _orig_interest

# ---- Move 8: school auto-extend (no dead-end) + spiral --------------------------------------
# protect the real school state
bak = school.STATE.read_text(encoding="utf-8") if school.STATE.exists() else None
def restore():
    if bak is not None: school.STATE.write_text(bak, encoding="utf-8")
    elif school.STATE.exists(): school.STATE.unlink()

try:
    # an EXHAUSTED curriculum: idx at the last book
    school._save({"curriculum": ["book a", "book b"], "curriculum_idx": 1,
                  "assigned_title": "book b", "assigned_book": "X", "today_done": 0,
                  "sessions_per_day": 4, "history": []})

    # (8a) advance() must NOT dead-end (old behaviour returned None) — it routes to _extend_program
    import random as _rnd
    _orig_ext = school._extend_program
    school._extend_program = lambda d: ("EXTENDED", "/path/extended")
    got = school.advance()
    assert got == ("EXTENDED", "/path/extended"), f"advance dead-ended instead of extending: {got}"
    print("[8a] no dead-end OK — exhausted curriculum advance() → breadth extension, not None")
    school._extend_program = _orig_ext

    # (8b) spiral branch: force the 20% spiral, feed a relevant read book, no-op the rewind
    school._save({"curriculum": ["book a"], "curriculum_idx": 0, "today_done": 0,
                  "sessions_per_day": 4, "history": []})
    _orig_rand = _rnd.random
    _rnd.random = lambda: 0.05                          # < 0.20 → take the spiral path
    _orig_sugg = bs.suggest_reread
    bs.suggest_reread = lambda min_gap_days=14.0: {"path": target, "title": Path(target).stem.replace("_"," ")}
    import core.reading as _rd
    _orig_reread = _rd.reread
    _rd.reread = lambda b=None: "rewound-title"
    try:
        d = school._load()
        res = school._extend_program(d)
        assert res, "spiral extend returned nothing"
        nd = school._load()
        assert nd["history"][-1]["source"] == "spiral", f"spiral not recorded: {nd['history'][-1]}"
        assert nd["assigned_title"] == res[0] and nd["curriculum"][-1] == res[0], "spiral assign incoherent"
        print(f"[8b] spiral reread OK — extended program with a rewound keystone '{res[0][:40]}' (source=spiral)")
    finally:
        _rnd.random = _orig_rand; bs.suggest_reread = _orig_sugg; _rd.reread = _orig_reread
finally:
    restore()

print("\nALL PASS — reread-when-helpful invites motivated returns; school never dead-ends (breadth + spiral).")
