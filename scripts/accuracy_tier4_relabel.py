"""J-3708: write data/accuracy_tier4_relabel.json (the cutoff before which tier4_user accuracy rows are legacy
false-positive-prone labels from the old substring detector). Usage: python scripts/accuracy_tier4_relabel.py [--cutoff-ts N] [--show]"""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import competence as C

ap = argparse.ArgumentParser()
ap.add_argument("--cutoff-ts", type=float)
ap.add_argument("--show", action="store_true")
a = ap.parse_args()
if a.cutoff_ts is not None and not a.show:
    C._TIER4_RELABEL_FILE.write_text(json.dumps({"cutoff_ts": a.cutoff_ts, "note": "J-3708"}), encoding="utf-8")
print("cutoff_ts =", C.tier4_cutoff_ts())
