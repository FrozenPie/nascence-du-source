"""J-3973 / D-0751: figurative-object guard on the objtest declare gate (sensorium._strict_test_object).
Pure string test, no stores touched. Exit 0 = pass."""
import os, pathlib, sys
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import core
assert str(pathlib.Path(core.__file__).resolve()).lower().startswith(str(HERE).lower()), core.__file__
from core import sensorium as s

FAIL = []
def check(c, m):
    print(("PASS " if c else "FAIL ") + m)
    if not c: FAIL.append(m)

FIG = ["I weigh the stone evidence against the book's division",
       "weigh the stone against the other claim", "I weigh the stone evidence",
       "weigh the shell argument carefully", "weigh the pebble up against the rest"]
REAL = ["scrape the stone", "heft the pebble", "weigh the stone in my hand", "I smell the driftwood",
        "float the shell", "scratch the pumice", "weigh the piece", "sniff the old bottle"]
for t in FIG:
    clause = s._test_clause(t) or t
    check(not s._strict_test_object(clause), "guard ON refuses figurative: " + t)
for t in REAL:
    check(s._strict_test_object(s._test_clause(t) or t), "guard ON keeps real test: " + t)
# the live false positive end to end at the hand's own gate
check(s._test_clause(FIG[0]) != "" and not s._strict_test_object(s._test_clause(FIG[0])), "F-4490 replay refused")
os.environ["NASCENCE_OBJTEST_FIGURATIVE_GUARD"] = "0"
check(s._strict_test_object(s._test_clause(FIG[0])), "kill switch off: pre-guard behaviour (F-4490 clause passes again)")
for t in REAL:
    check(s._strict_test_object(s._test_clause(t) or t), "switch off keeps real: " + t)
sys.exit(1 if FAIL else 0)
