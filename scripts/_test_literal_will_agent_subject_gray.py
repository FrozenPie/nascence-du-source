"""J-2148 / F-2841: agent-subject check demotes a gated family's DEED to GRAY (never MUSING).
Pure classify() tests; no live data written. Run from the worktree: python scripts/_test_literal_will_agent_subject_gray.py"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
import core.literal_will as lw


def v(text, fam):
    r = [x for x in lw.classify(text, "", location="study") if x["family"] == fam]
    return r[0]["verdict"] if r else "NONE"


fails = []
def check(name, got, want):
    ok = got == want
    print(("PASS " if ok else "FAIL ") + name, got)
    if not ok:
        fails.append(name)

# genuine will stays DEED
check("genuine water", v("i will water the herbs now", "weed" if False else "water"), "DEED")
check("genuine door", v("i want to open the door and let the air in", "door"), "DEED")
check("genuine harvest", v("i'll cut the thyme before the frost", "harvest"), "DEED")
check("genuine fire after observation", v("the fire is cold; i should get up and light it", "fire"), "DEED")
check("genuine mow", v("i will mow the lawn now", "mow"), "DEED")
check("move-and-open", v("i walk to the door and open it", "door"), "DEED")
# noun/adjective use (determiner + words before verb, no new subject)
check("np_subject bell-notes cut", v("the tui bell-notes cut through the thyme", "harvest"), "GRAY")
check("adjective: door is open", v("the door stands open to the garden window", "door"), "GRAY")
check("adjective: door is open (is)", v("the window is open and the door is open", "door"), "GRAY")
# perception
check("perception", v("i watch the light cut across the thyme", "harvest"), "GRAY")
# refusal / too-X-to / negation the blockers miss
check("cannot", v("i cannot feed the cat yet", "cat"), "GRAY")
check("not to", v("i decided not to gather wood", "gather"), "GRAY")
check("do not", v("i do not pull away from the door", "door"), "GRAY")
check("too tired to", v("i am too tired to water the herbs", "water"), "GRAY")
# deliberation / question
check("should i", v("should i harvest thyme or simply sit?", "harvest"), "GRAY")
check("question mark", v("do the herbs need me to water them?", "water"), "GRAY")
# past narration
check("where i cut it", v("the thyme heals where i cut it", "harvest"), "GRAY")
check("smell of cut grass not DEED", v("the smell of cut grass drifts in", "mow") != "DEED", True)
check("fresh cut grass", v("fresh cut grass on the lawn", "mow"), "GRAY")
# blockers still win to MUSING; ungated unaffected
check("blocker negation", v("i won't water the herbs", "water"), "MUSING")
check("ungated move unchanged", v("i want to step through the door", "move"), v("i want to step through the door", "move"))
# demotion never yields MUSING, feature recorded
r = [x for x in lw.classify("the thyme heals where i cut it", "", location="study") if x["family"] == "harvest"][0]
check("feature recorded", r["features"].get("agent_subject_fail"), "narration")
print("FAILS:", fails)
sys.exit(1 if fails else 0)
