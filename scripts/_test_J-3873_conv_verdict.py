"""J-3873: conv_status_verdict states a verdict for each data regime; pure function, no live reads."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.conv_status_verdict import verdict
assert verdict({"scans": 0}).startswith("NO DATA")
assert verdict({"scans": 5, "would_fire": 1}).startswith("INSUFFICIENT")
assert verdict({"scans": 40, "would_fire": 0}).startswith("SILENT")
v = verdict({"scans": 40, "would_fire": 4, "mean_directness": 0.7, "retreat_in_draft": 2, "retreat_rate": 0.5})
assert "10.0%" in v and "2/4" in v, v
print("OK")
