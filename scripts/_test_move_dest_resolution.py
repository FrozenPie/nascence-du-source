"""
Regression: nodes.inner_monologue_node._move_dest() resolves the place a move verb REACHES (J-0833 / F-1199).

Pure — _move_dest() reads no store and writes nothing; this script imports the node module only. Every
probe below is either a real data/hands_trace.jsonl thought (lightly truncated) that the pre-J-0833
fixed WOOD>SHORE>STUDY>GARDEN list order resolved to the wrong place, or one of the pre-existing contracts
(J-0539's letterbox cases, F-0634's "go out = garden" default) that must keep holding.

  python scripts/_test_move_dest_resolution.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from nodes.inner_monologue_node import _move_dest   # noqa: E402

FAILS = 0


def check(cond: bool, label: str) -> None:
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


def want(text: str, dest: str, why: str = "") -> None:
    got = _move_dest(text)
    check(got == dest, f"{dest!r:9s} <- {text[:88]!r}" + (f"   ({why})" if why else "") + ("" if got == dest else f"  [got {got!r}]"))


print("[1] pre-existing contracts (J-0539 letterbox, F-0634 go-out default, D5 object-first) still hold")
want("the letterbox", "garden")
want("through the gate down to the shore", "shore", "the gate is transit, the shore is the destination")
want("to the garden", "garden")
want("go outside", "garden", "F-0634: an unqualified 'out' is the garden")
want("the driftwood", "shore")
want("into the trees", "wood")
want("", "")
want("nothing here names a place", "")

print("\n[2] 'away from X, toward Y' -- the source is dropped, the destination wins (F-1199's own cases)")
want("i want to turn away from the desk and go to the raised bed. the soil is sodden, the herbs are waiting; i will water them",
     "garden", "F-1199: was 'study' via 'the desk'")
want("i step away from the water's surface, tired of circling the same mirage. the study beckons; i want to sit with the open book",
     "study", "F-1199: was 'shore' via 'the water'")
want("i want to abandon the desk and climb back up to the garden where the rain falls", "garden", "was 'study'")
want("i want to leave the study and go down to the shore", "shore")
want("i want to leave the study, walk down to the wood", "wood")
want("i climb off the shingle into the trees; the roar of the sea fades to a muffled wash behind me", "wood", "wood still wins")
want("i want to leave the shore and climb up to the raised beds", "garden", "was 'shore' -- a departure silently swallowed")
want("i will leave the shore behind and climb up into the wood to gather", "wood")
want("i need to turn away from the sea's whisper and go back inside. let me climb up to the study", "study", "was 'shore'")

print("\n[3] the place he STANDS in no longer wins just because its list is checked first")
want("the tide is out; i will walk up to the garden and see what remains", "garden", "was 'shore'")
want("i feel the pull to leave this quiet shore and climb up toward the garden", "garden", "was 'shore'")
want("i step into the garden where the sea's sound washes over me", "garden", "was 'shore'")
want("i step into the cool garden where the rusted trap sits silent beside the raised bed. the sea's sound is a low hum",
     "garden", "was 'shore'")
want("the wood curls on the floor. i feel the pull to leave this static room and go out to the garden", "garden", "was 'wood'")
want("the wind roars through the trees. let me go out to the garden instead", "garden", "was 'wood'")
want("i walk down through the trees, the salt air cooling my skin. the shore stitches ahead; i move toward it", "shore",
     "'through the trees' is transit")
want("i want to leave this garden and go inside where travis is waiting, escaping the sea's noise", "study", "was 'shore'")

print("\n[4] negation and idiom")
want("i do not need the sea or the books right now; i need to walk away from this dead ground", "",
     "F-1199's negation case: was 'shore'; now no destination at all, never the negated one")
want("i am tired of circling these same dead questions inside my own head. let me go to the shore", "shore",
     "'inside my own head' is nowhere to walk")
want("i feel stuck spinning on dead ground inside my own head. the garden is calling", "garden", "was 'study' via 'inside'")
want("i want to turn my attention outward to the shore, watching the tide come in", "shore", "the tide's coming in is not his")

print("\n[5] word edges: a cue inside another word is not a cue")
want("i let go of searching for something more complex", "", "'sea' inside 'searching'")
want("i circle the woodpecker's winter tactics. i want to walk out into the garden", "garden", "'the wood' inside 'the woodpecker'")
want("the tideline pulls me; i want to walk down to the tideline", "shore", "the plural/line suffix still counts")
want("i step out into the wet sand", "shore", "sensorium.move()'s own 'sand' finally shared here")

print("\n[6] J-0864: the woodpile is a GARDEN place (by the door / by the cottage), not the wood and not nowhere")
want("to the woodpile", "garden", "J-0864: was '' after J-0833's word edges, 'wood' before them (a no-op)")
want("the woodpile", "garden")
want("toward the woodpile", "garden")
want("the rain demands action, so i turn from the grey wall. the woodpile is low, one load remains. i want to go to the woodpile",
     "garden", "real corpus thought (object 'to the woodpile')")
want("the tide is rising; let me go up to the woodpile to gather dry driftwood while travis reads", "garden",
     "real corpus thought: the directional 'up to the woodpile' beats the bare 'driftwood' shore cue")
want("the wood pile", "garden", "two-word spelling")
want("i want to leave the woodpile and go down to the shore", "shore", "the woodpile as a SOURCE is dropped")
want("the woodpecker taps somewhere in the trees; i will walk into the wood", "wood", "'woodpile' does not fire on 'woodpecker'")

print("\n[7] J-1635/F-2202: the gate/bed/mailbox cues tolerate ONE inserted modifier")
want("i step toward the open gate", "garden", "F-2202's own real row: was '' before this fix")
want("i want to climb into the warm bed", "garden", "one word inserted before 'bed'")
want("i walk to the rusted mailbox", "garden", "one word inserted before 'mailbox'")
want("the big old rusty gate creaks", "", "three inserted words is past the {0,2} bound -- no cue fires")
want("away from the old gate", "", "source-marked: dropped same as the bare cue always was")
want("the old, open gate stands ajar", "", "a comma inside the gap still blocks the match (clause guard)")
want("i want to sit at the old wooden desk", "", "'the desk' checked, deliberately left un-widened (see comment)")
want("i return to the study", "study", "literal 'the study' cue still fires with zero gap, unchanged")
want("i return to the quiet study", "", "'the study' NOT gap-widened on purpose: a modifier now blocks it, same as before this job")
want("i feel a blockage against the discipline of study today", "", "'the desk'/'the study' NOT widened: this "
     "real row (line 22337) flipped 'garden'->'study' during development and is why they were dropped")
want("i want to step away from this ground and into the kelp beds", "", "J-1635: 'kelp bed(s)' is a real "
     "shore/ocean term, excluded from the 'the bed' gap (4 real rows: was wrongly 'garden' without the guard; "
     "'kelp' itself names no list, so this resolves to '' here, not 'shore', unless another shore cue is present")
want("the tide pulls at my ankles; i want to step into the kelp beds and feel the sea", "shore",
     "same real-corpus shape (line 10259) WITH its own 'tide'/'sea' cues present: those still correctly win")
want("i walk toward the rosemary bed to breathe its scent", "garden", "a genuine garden herb bed still gap-matches fine")

print("\n[8] J-3527/F-4138: the stream MOUTH is a shore cue; a bare stream is not")
want("toward the stream mouth", "shore", "3 real hands_trace rows were 'garden' (a wrong departure) before")
want("the cat's prints point toward the stream mouth where terns hover", "shore", "real row 1788900787")
want("i want to walk to the mouth of the stream", "shore")
want("i walk to the stream's mouth and watch the water", "shore")
want("i want to leave the stream mouth and go up to the garden", "garden", "the mouth as a SOURCE is dropped")
want("i do not need the stream mouth today", "", "negated")
want("i follow the stream up into the trees", "wood", "a bare stream is not a shore cue; the trees win")
want("i listen to the stream", "", "a bare stream names no place")

print("\nFAILS =", FAILS)
print("ALL OK" if FAILS == 0 else "SOME CHECKS FAILED")
sys.exit(1 if FAILS else 0)
