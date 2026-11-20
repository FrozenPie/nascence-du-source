"""J-4381: shadow belief ledger (temp-path store only; never touches data/)."""
import sys, tempfile, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from core import belief_ledger as bl
d = pathlib.Path(tempfile.mkdtemp()) / "b.jsonl"
assert not bl.enabled()
bl.note("poker", {"place": "study"}, "look", now=100.0, path=d)
bl.note("poker", {"carried": True}, "carry", now=400.0, path=d)   # prior belief 'study' vs truth carried -> drift
bl.note("kettle", {"place": "kitchen"}, "look", now=500.0, path=d)
r = bl.report(["poker", "kettle", "oil_lamp", "rope"], path=d)
assert r["coverage"] == 0.5 and r["reads"] == 1 and r["drift_share"] == 1.0, r
bl.note("poker", {"x": 1}, "look")          # no path + flag off -> no write to live store
print("ALL OK")
