"""J-1735 / F-2367: every previously-raw origin renders a non-raw label; the 15 original labels unchanged."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import core
sys.path.insert(1, str(Path.home() / '.claude' / 'skills' / 'job-queue'))
import lab_env
tree = Path(__file__).resolve().parent.parent
assert tree in Path(core.__file__).resolve().parents, core.__file__
from core.schema import MemoryFragment

ORIGINAL = {
 "seed": "Core memory (inherited)", "lived": "Our conversation", "consolidation": "My own reflection",
 "subconscious_synthesis": "Self-observation (subconscious)", "active_imagination": "Private contemplation",
 "dream": "Dream", "session_summary": "Session record", "inner_thought": "My inner thought",
 "parametric_library": "Consulted reference (the library — unverified, weigh it)",
 "reading": "A book I am reading (ANOTHER author's words — not my own writing)",
 "study": "My own study note (my work, about the world)",
 "research": "Something I looked up (external fact - Wikipedia)",
 "letter": "A letter I wrote to Travis, on my own initiative",
 "chapter": "A chapter of my life (my own telling of a settled period)",
 "sound": "A sound I heard in the room (the world, heard)"}
NEW = ["understanding","understanding_from_guidance","standing_insight","gist","action","mirror","essay","affection","thermal"]

def lab(o): return MemoryFragment("x","c","semantic",0.5,0.0,origin=o).readable_label()
with lab_env.isolate():
    for o, l in ORIGINAL.items(): assert lab(o) == l, o
    for o in NEW: assert lab(o) != o and len(lab(o)) > 10, o
    assert len({lab(o) for o in NEW}) == len(NEW)
    assert lab("zzz_unknown") == "zzz_unknown"
print("OK")
