"""D-0409 A (J-2097): felt recall Phase 1 gate = own edge + cooldown; dispatcher verdict never gates.
All I/O is patched to a temp dir / stubs (no live data, no DB). Run: python scripts/felt_recall_gate_test.py"""
import sys, tempfile, pathlib, json, types
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core
assert str(pathlib.Path(core.__file__).resolve()).startswith(str(ROOT)), core.__file__
from core import felt_recall as fr

tmp = pathlib.Path(tempfile.mkdtemp())
fr._SHADOW_LOG = tmp / "felt_recall_shadow.jsonl"

class Prior:
    valence, arousal, primary = 0.2, 0.1, "calm"
class Affect:
    def __init__(self): self.n = 0
    def apply_prior(self, p): self.n += 1

fr._build_prior = lambda dim, v, t: (Prior(), 7, 0.5, [1, 2, 3])
fr._affect_now = lambda a: {}
fr._get_baseline_valence = lambda: 0.0
fr._courier_would_have_fired = lambda now, dim: (False, None)
tm_calls = []
fr._register_dispatcher_line = lambda dim, place, now: (tm_calls.append(dim) or {"verdict": "none", "cold_start": False, "weight": 0.0})

def run(live):
    fr.FELT_RECALL_LIVE = live
    fr._last_fired.clear()
    a = Affect()
    r1 = fr._handle_edge("weather", "a", "b", {}, a, 1000.0)
    r2 = fr._handle_edge("weather", "b", "c", {}, a, 1100.0)   # inside 600 s cooldown
    r3 = fr._handle_edge("weather", "c", "d", {}, a, 1700.0)   # cooldown elapsed
    return a, r1, r2, r3

a, r1, r2, r3 = run(True)
assert r1["fired"] and r1["applied"] and r1["gate_used"] == "edge_cooldown"   # verdict none still tugs
assert not r2["fired"] and not r2["applied"]                                   # cooldown suppresses
assert r3["fired"] and r3["applied"] and a.n == 2
a, r1, r2, r3 = run(False)
assert a.n == 0 and not any(r["applied"] for r in (r1, r2, r3))                # flag False: inert
# on_substrate_tick still registers with the dispatcher on every edge and logs verdict
fr._current_tuple = lambda: {"weather": "x", "place": "p"}
fr._prev_tuple = {"weather": "y", "place": "p"}
fr._dim_edges = lambda p, c: [("weather", "y", "x")]
fr._last_fired.clear(); tm_calls.clear()
fr.on_substrate_tick(None)
row = json.loads(fr._SHADOW_LOG.read_text().splitlines()[-1])
assert tm_calls == ["weather"] and row["dispatcher_verdict"] == "none" and row["gate_used"] == "edge_cooldown"
print("OK felt_recall gate tests passed")
