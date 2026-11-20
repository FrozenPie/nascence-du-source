"""J-3692 (F-4310): kind-of idiom is not a claim word; an adverb may sit inside a deontic frame.
Hermetic: pure functions of core.object_hypothesis (no store, no LLM); core imported from this tree.
python scripts/_test_J-3692_idiom_adverb.py   Exit 0 = pass."""
import os, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import core
assert Path(core.__file__).resolve().is_relative_to(HERE), core.__file__
from core import object_hypothesis as oh
FAIL = []
def check(c, n):
    print(("PASS " if c else "FAIL ") + n)
    if not c: FAIL.append(n)
def flags(i, a):
    os.environ["NASCENCE_KIND_IDIOM_GATE"] = i; os.environ["NASCENCE_DEONTIC_ADVERB"] = a
idiom = "Perhaps this dandelion is a kind of stillness"
real = "Perhaps this driftwood is a kind of beech"
flags("1", "1")
check(oh.extract(idiom, "plant", "dandelion") is None, "idiom-only claim dropped (gate on)")
check(oh.extract("I think this dandelion is a type of fresh weed", "plant", "dandelion") is None or True, "n/a sanity")
check(oh.extract(real, "driftwood", "driftwood") is not None, "real kind claim with a material noun kept")
flags("0", "1")
check(oh.extract(idiom, "plant", "dandelion") is not None, "gate off restores old behaviour")
for adv in ("just", "really", "simply", "only", "still", "now", "then", "also", "finally", "actually"):
    flags("1", "1")
    check(oh.deontic_frame_start(f"maybe i {adv} need to look at the glass") is not None, f"adverb {adv}: frame found")
flags("1", "0")
check(oh.deontic_frame_start("maybe i just need to look at the glass") is None, "adverb flag off: old pattern misses it")
flags("1", "1")
check(oh.deontic_frame_start("i really should let it dry") == 0, "i really should")
check(oh.deontic_frame_start("i think it is rotten") is None, "no false frame on a claim")
check(oh.deontic_frame_start("maybe i can tell it is rusted") is not None, "declared pattern behaviour unchanged for maybe-i-can")
check(oh.deontic_frame_start("i just want to know what it is") is None, "inquiry still not a frame")
check(oh.extract("Maybe I just need to look at the stone's wet glass again", "stone", "stone") is None,
      "adverb deontic: claim words inside the intention are not a hypothesis")
flags("0", "0")
check(oh.extract("Maybe I just need to look at the stone, it is wet", "stone", "stone") is not None or True, "flags off runs")
flags("1", "1")
print("RESULT", "FAIL " + str(FAIL) if FAIL else "PASS")
sys.exit(1 if FAIL else 0)
