"""J-3976 (D-0757): length-aware reflection best-of-2 selector. Pure-function test, no live stores."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import schema
from nodes.reflection_node import ReflectionNode
assert os.path.abspath(schema.__file__).startswith(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
n = ReflectionNode.__new__(ReflectionNode)
sc = lambda d: n._score_candidate({"draft": d})
short = " ".join(["w"] * 40) + "."
mid = " ".join(["word"] * 85) + "."
long_ = " ".join(["word"] * 120) + "."
longer = " ".join(["word"] * 140) + "."
trunc_short = " ".join(["w"] * 40)
assert sc(short) > sc(long_), "short terminal must beat over-length terminal"
assert sc(mid) > sc(short), "richer in-limit still wins"
assert sc(long_) > sc(longer) > 0, "less over-length preferred"
assert sc(long_) > sc(trunc_short), "terminal still preferred over truncated"
assert sc("") == 0.0
schema.REFLECTION_LENGTH_AWARE_SELECT = False
assert sc(long_) > sc(short), "flag off restores old behaviour"
print("OK")
