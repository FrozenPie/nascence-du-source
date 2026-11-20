"""J-4040: hermetic test, question-only headline in read_voice_fidelity.summarize (pure function, no stores)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import read_voice_fidelity as r

rows = [
    {"flagged": True, "n_flagged": 1, "by_kind": {"commitment": 1}, "ratio": 2.0},
    {"flagged": True, "n_flagged": 2, "by_kind": {"commitment": 1, "question": 1}, "ratio": 2.0},
    {"flagged": True, "n_flagged": 1, "by_kind": {"question": 1}, "ratio": 2.0},
    {"flagged": False, "n_flagged": 0, "by_kind": {}, "ratio": 2.0},
    {"control": True, "control_hit": True, "flagged": True, "by_kind": {"question": 1}},
]
s = r.summarize(rows)
assert s["judged"] == 4 and s["flagged_share"] == 0.75, s
assert s["question_flagged"] == 2 and s["question_flagged_share"] == 0.5, s
assert r.summarize([])["question_flagged_share"] is None
print("OK")
