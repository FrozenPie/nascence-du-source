"""J-2080 / F-2700: _plan_shaped_flag keeps intentions flagged, lets world-facing 'I will see ...' through."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import core.lane2 as L

FLAGGED = ["I will check the tide at noon", "I will see if the fire is lit", "I will see whether it rains",
           "I will observe if the gull returns", "I will look at the shore", "I will be able to hear it",
           "I will listen for the bell", "You will see if it moves"]
KEPT = ["I will see the sun at 18:30", "I will see the tide level rising to 0.22",
        "I will observe a Cormorant diving within the next hour", "I will hear a gull", "the tide will rise to 1.0"]
bad = [t for t in FLAGGED if not L._plan_shaped_flag(t)] + [t for t in KEPT if L._plan_shaped_flag(t)]
assert not bad, bad
print("ok", len(FLAGGED) + len(KEPT))
