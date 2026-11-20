r"""J-4174 (F-5025, object_epistemic_loop): precision gate on core.object_hypothesis.extract().
Pure text test, no I/O on data/. Cases are the 9 live inferences hand-labelled in F-5025 (2 real, 7 not) plus
synthetic checks for each rule. Run: python scripts/_test_J-4174_precision_gate.py
"""
import os, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
import core
assert Path(core.__file__).resolve().is_relative_to(HERE), core.__file__
from core import object_hypothesis as oh

TRAP = ("garden_item", "a spring-jawed possum trap, rusted, its plate set with a twist of wire for bait")
HEAP = ("garden_item", "the compost heap in the corner by the wall, dark and settling under a board")
DAND = ("garden_plant", "a dandelion")
ROSE = ("garden_plant", "the rosemary bush")
DRIFT = ("driftwood", "a pale bleached log")
STONE = ("stone", "a pale porous stone")

# (object, text, real?) -- live rows from F-5025
LIVE = [
    (TRAP, "Maybe that rusted trap isn't just metal", True),
    (DAND, "salt water seeps up, perhaps stealing nitrogen from the soil right where the dandelion roots struggle", True),
    (ROSE, "The bee's persistence contrasts with the plant's endurance. perhaps my own ideas need this kind of "
           "resilience, to weather the wind without snapping", False),
    (DAND, "Maybe I should just let the dandelion float away for now", False),
    (DAND, "The dandelion sits quietly ahead, unbothered by Napoleon's court or revolutionary tensions. Perhaps "
           "history needs this kind of stillness", False),
    (DAND, "The low sun glows on the dandelion while a bee blunders past. I wonder if that heavy insect knows its "
           "hive is gone, or if it simply trusts the old landmarks will hold", False),
    (DAND, "my focus settles on the dandelion. I wonder if this landscape's scars come from the mill's smoke or "
           "the axe's blow", False),
    (HEAP, "I consider the isolation: a wall built of treaties that turned Electors into silent observers, perhaps "
           "making them more dangerous than if they had been allies", False),
    (TRAP, "Yet, the trap stands rusted by the gate. Perhaps I should leave it be, letting the seeds rest", False),
]
# synthetic: (object, text, expected with gate ON)
SYN = [
    (DRIFT, "I think this driftwood might be beech", True),           # anchor + link
    (DRIFT, "The log lies there. I think it came from the river", True),   # backref + verb claim
    (DRIFT, "The log lies there. Maybe it's rotten inside", True),      # it's + adjective
    (DRIFT, "The log lies there. Maybe it is hollow", True),            # backref + link
    (STONE, "perhaps the stone is volcanic", True),
    (("shell", "a pale fan-shaped shell"), "Perhaps the shell isn't crushed, just porous", True),  # broad-corpus near-loss
    (DAND, "I wonder if this landscape's scars come from the mill", False),
    (STONE, "The stone sits there. perhaps that heavy gull will come back", False),  # determiner backref
    (STONE, "perhaps the gull on the stone is old", False),             # (b) location anchor
    (DRIFT, "The log lies there. maybe this beach's sand came from the river", False),       # (c) noun in gap
    (("study_item", "the book 'The Time Machine'"), "perhaps it was a machine built to consume souls", False),
    (("study_item", "the book 'The Time Machine'"), "perhaps the book is damp", True),
    (("made_thing", "a hand trowel"), "The hand-sized creature stops. I wonder if it is old", False),
    (ROSE, "perhaps my plant is dying", True),
    (ROSE, "perhaps my own plant is dying", False),
    (HEAP, "maybe the wall is old", False),                             # (a) non-head name word
    (HEAP, "maybe the compost heap is rotting", True),
]

def run(flag):
    os.environ["NASCENCE_OBJHYP_PRECISION_GATE"] = flag
    return [bool(oh.extract(t, *o)) for (o, t, _r) in LIVE], [bool(oh.extract(t, *o)) for (o, t, _e) in SYN]

fails = 0
on_live, on_syn = run("1")
off_live, off_syn = run("0")
for (o, t, real), got in zip(LIVE, on_live):
    if got != real:
        fails += 1; print("FAIL live", real, got, t[:70])
tp = sum(1 for (_o, _t, r), g in zip(LIVE, on_live) if r and g)
fp = sum(1 for (_o, _t, r), g in zip(LIVE, on_live) if g and not r)
print(f"live precision gate ON: {tp}/{tp + fp}; gate OFF: "
      f"{sum(1 for (_o,_t,r),g in zip(LIVE, off_live) if r and g)}/{sum(off_live)}")
for (o, t, exp), got in zip(SYN, on_syn):
    if got != exp:
        fails += 1; print("FAIL syn", exp, got, t[:70])
# subset property: gate ON never adds a hit
for a, b in list(zip(on_live, off_live)) + list(zip(on_syn, off_syn)):
    if a and not b:
        fails += 1; print("FAIL subset")
# gate off is the previous behaviour: compost treaties row still accepted there (F-5025 replay hit)
if not off_live[7]:
    fails += 1; print("FAIL gate-off no longer reproduces the compost hit")
# object_anchors (used by intervention_test) unchanged; head_anchors cuts the locative tail
assert oh.object_anchors(*HEAP) >= {"wall", "board", "compost", "heap"}
assert oh.head_anchors(*HEAP) == {"compost", "heap"}, oh.head_anchors(*HEAP)
assert oh.head_anchors(*TRAP) == {"possum", "trap"}, oh.head_anchors(*TRAP)
print("PASS" if not fails else f"{fails} FAILURES")
sys.exit(1 if fails else 0)
