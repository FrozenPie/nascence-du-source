"""J-1736/F-2366: render() tags origin=='inner_thought' honestly; others unchanged. render() only, no I/O."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import core
from core import wandering as w
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
assert os.path.abspath(core.__file__).startswith(root), core.__file__
def r(items):
    w._trail.clear(); w._trail.extend(items); return w.render()
out = r([{"text": "mine", "origin": "inner_thought", "via": "drift"}])
assert "(a thought of your own from earlier) mine" in out and "drifted through" not in out, out
out = r([{"text": "bk", "origin": "reading", "via": "drift"}])
assert "(drifted through your mind) bk" in out, out
for via, tag in [("sense","you notice"),("ambient","glimpsed"),("felt","surfaced — it feels like how you feel now")]:
    out = r([{"text": "x", "origin": "inner_thought", "via": via}])
    assert f"({tag}) x" in out, out
out = r([{"text": "x", "origin": "essay", "via": "drift"}])
assert "(drifted through your mind) x" in out
w._trail.clear()
print("OK")
