"""J-3284 (D-0631 review J-3243): readable_label tells the truth about research rows and names peer."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import core
sys.path.insert(1, str(Path.home() / '.claude' / 'skills' / 'job-queue'))
import lab_env
tree = Path(__file__).resolve().parent.parent
assert tree in Path(core.__file__).resolve().parents, core.__file__
from core.schema import MemoryFragment

def lab(o, c="c"): return MemoryFragment("x", c, "semantic", 0.5, 0.0, origin=o).readable_label()

OLD = "Something I looked up (external fact - Wikipedia)"
SHOCK = "Something that arrived from the world uninvited (a random Wikipedia page; not my choice)"
SYS = "Something a system fetched for one of my questions (Wikipedia, a keyword match; may be the wrong page)"
with lab_env.isolate():
    assert lab("research", "[Looked up: 'Habituation' (asked by him: habituation)] text") == OLD
    assert lab("research", "[Looked up: 'Significance' (external shock — uninvited)] text") == SHOCK
    assert lab("research", "[Looked up: 'Leiocephalus' (pursuit: what is a habit)] text") == SYS
    assert lab("research", "[Looked up: 'Habit' (curiosity: habit)] text") == SYS
    assert lab("research", "[Looked up: 'Capillary action' (twig off 'Soap Bubbles')] text") == SYS
    # a title that merely contains the words must not be mistaken for the via
    assert lab("research", "[Looked up: 'External shock' (pursuit: what is a shock)] text") == SYS
    assert lab("research", "[Looked up: \"O'Brien\" (pursuit: q (x))] text") == SYS
    # no prefix at all: unchanged legacy label (J-1735 test)
    assert lab("research") == OLD and lab("research", "plain text") == OLD
    # other origins unaffected by content
    assert lab("reading", "[Looked up: 'X' (external shock)]").startswith("A book I am reading")
    p = lab("peer", "(a letter from X) hello")
    assert p != "peer" and len(p) > 10, p
print("OK")
