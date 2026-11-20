"""J-3619 / F-4228: _tag_of must keep an apostrophe inside a book title.  Pure, hermetic (no DB, no files).
Run FROM a worktree: python scripts/_test_J3619_tag_of_apostrophe.py   (exit 0 = ALL OK)"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # core BEFORE anything else
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
from core import world_consolidation as wc

CASES = [
    ("[From 'Pilgrim's Progress', sitting 6] text", "Pilgrim's Progress"),
    ("[From 'Gulliver's Travels'] text", "Gulliver's Travels"),
    ("[Understanding — from 'Stoicism's Wisdom for Modern Times'] x", "Stoicism's Wisdom for Modern Times"),
    ("[Essay — on 'Children's Ways: A Book'] x", "Children's Ways: A Book"),
    ("[My study note: 'Dreams' — on 'King Arthur's Tales' — subject: bird behavior] x", "King Arthur's Tales"),
    # unchanged behaviour for apostrophe-free titles
    ("[From 'The Mad King', sitting 2] x", "The Mad King"),
    ("[From 'The Mad King'] x", "The Mad King"),
    ("[My study note: 'N' — on 'The Mad King' — subject: s] x", "The Mad King"),
    ("no bracket From 'X'", ""),
    ("[no cite here] x", ""),
]
bad = [(c, w, wc._tag_of(c)) for c, w in CASES if wc._tag_of(c) != w]
for b in bad:
    print("FAIL", b)
assert wc._cites("Pilgrim's Progress", "[From 'Pilgrim's Progress', sitting 6] x")
print("ALL OK" if not bad else "FAILED")
sys.exit(1 if bad else 0)
