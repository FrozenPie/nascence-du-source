"""J-3872: verdict() on stubbed status dicts (pure; touches no data/ store)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import emotion_construction as ec
assert Path(ec.__file__).resolve().is_relative_to(Path(__file__).resolve().parent.parent)
from scripts.affective_retrieval_read import verdict

assert verdict({"rows": 0})["verdict"] == "NO-DATA"
assert verdict({"rows": 50, "paired": 50, "mean_jaccard_top5": 0.99})["verdict"] == "INSUFFICIENT"
def s(j): return {"rows": 500, "paired": 500, "mean_jaccard_top5": j, "mean_affect_match_gap": 0.02}
assert verdict(s(0.979))["verdict"] == "CONSTRUCTED-MATCHES-LLM"
assert verdict(s(0.75))["verdict"] == "MIXED"
assert verdict(s(0.3))["verdict"] == "CONSTRUCTED-DIVERGES"
print("ok")
