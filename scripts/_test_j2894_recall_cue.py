import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.night import recall_cue
H = ("What the day held \u2014 things you DID and met in the world (the dream recombines these; it does not "
     "narrate them):\n")
w = H + "  - walked the garden\n  - read a letter from Darwin\n\nLet the dream rise from these \u2014 the day's residue, transformed."
c = recall_cue(w); assert c == "walked the garden read a letter from Darwin", c
f = "What the day FELT most strongly (the charge the dream works):\n  - (warm) a cat on the sill\n\nTransform this."
assert recall_cue(f) == "(warm) a cat on the sill"
assert recall_cue("plain text no bullets") == "plain text no bullets"
assert recall_cue("") == "" and len(recall_cue(H + "  - " + "x"*500)) == 240
print("ok")
